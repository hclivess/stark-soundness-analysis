"""
A transient halving bug, caught within minutes by a check built for something
else -- and already fixed before this file was finished.

*** READ THIS FIRST: THE BUG DESCRIBED BELOW IS NO LONGER PRESENT. ***
It existed in NADO's WORKING TREE (uncommitted) for a few minutes during the
GF(p^3) migration and was corrected while this file was being written. The
sequence is recorded because the DETECTION is the finding, not the defect.

    state 1   E_EXT2 = 128 hard-coded                  iteration 79 reported it
    state 2   base = _D * E_BASE // 2 if _D != 2 ...   halved the field: 96
    state 3   base = E_FIELD() if e else E_BASE        correct: 192

aux_bits(2^17) read 109.0, then 77.0, then 173.0. This repo measured state 2;
by the time the write-up was done the tree was at state 3.

WHAT STATE 2 WAS, AND WHY IT WAS WRONG

Iteration 79 reported that soundness.py hard-coded E_EXT2 = 128 while the
transcript emitted GF(p^3), under-reporting by 64 bits of challenge space. The
recommended patch was to make the constant follow extf.DEGREE.

An intermediate fix read:

    e = _ext_challenges() if ext is None else bool(ext)
    from execnode.stark.extf import DEGREE as _D
    base = (_D * E_BASE // 2 if _D != 2 else E_EXT2) if e else E_BASE

At _D = 3 and E_BASE = 64 that is 3 * 64 // 2 = 96. The challenge space of
GF(p^D) is D * log2(p) = 192. The `// 2` halves it.

THE FILE CONTRADICTS ITSELF TWO LINES APART
---------------------------------------------
soundness.py:77 already says so:

    E_EXT3 = 192                # log2 |GF(p^3)|, for reference

So the module states GF(p^3) is 192 bits at line 77 and computes 96 for the same
field at line 149. The D = 2 branch is right -- E_EXT2 = 128 = 2 * 64 -- which
is what makes the D != 2 branch's `// 2` visible as a slip rather than a
convention: the two branches disagree about what D * E_BASE means.

WHAT IT COSTS
---------------
    aux_bits(2^17 rows) reported     77.0
    aux_bits(2^17 rows) correct     173.0
    under-report                     96 bits

Iteration 79 measured the under-report at 64 bits of challenge space. It is now
96. The fix moved the number in the wrong direction and further than before,
because 96 < 128: the module now prices the challenge space BELOW the GF(p^2)
value it was using before the migration.

Everything else iteration 79 established is unaffected -- the transcript still
emits 3 limbs, ext_challenges_active is still unconditional, and the live system
is still at 150.8 classical / 75.4 post-quantum. Only the accounting moved, and
it moved down.

HOW IT WAS RESOLVED
---------------------
NADO's own fix went further than the patch this file was going to propose. It
now reads

    base = E_FIELD() if e else E_BASE

routing the whole question through one function rather than a branch on the
degree, so E_EXT2/E_EXT3 and the live value cannot drift apart again. That is
the better fix; the patch drafted here (`(_D * E_BASE) if e else E_BASE`) would
have removed the halving but kept the shape that allowed it.

HOW IT WAS CAUGHT
-------------------
By a check written in iteration 76 that pins this repo's transcription of
aux_bits against NADO's own function:

    check("the transcribed aux_bits matches NADO's own function exactly", ...)

It failed on the first suite run after the change, reporting
"transcribed 109.0000 vs NADO's 77.0000". The check exists because iteration 76
had derived the LogUp offset from NADO's printed report rather than its source,
and pinning the two together was the fix. It has now caught a live regression in
the tree it pins against, which is more than it was built for.
"""

import sys

NADO_PATH = "/root/nado"
LOG_ROWS, BUSES = 17, 4


def _s():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import extf, soundness
        return soundness, extf
    except Exception:
        return None


def degree():
    n = _s()
    return None if n is None else n[1].DEGREE


def nado_base_bits():
    """What soundness.py prices the challenge space at, via aux_bits."""
    n = _s()
    if n is None:
        return None
    import math
    S = n[0]
    return S.aux_bits(LOG_ROWS, ext=True) + math.log2(BUSES * 2 ** LOG_ROWS)


def correct_base_bits():
    """D * log2(p) -- and E_EXT3 in the same file agrees."""
    n = _s()
    return None if n is None else n[1].DEGREE * n[0].E_BASE


def file_states_correct_value():
    """soundness.py:77 defines E_EXT3 = 192, contradicting its own aux_bits."""
    n = _s()
    if n is None:
        return None
    return getattr(n[0], "E_EXT3", None) == correct_base_bits()


def degree2_branch_is_right():
    """E_EXT2 == 2 * E_BASE, which is why the other branch reads as a slip."""
    n = _s()
    return None if n is None else n[0].E_EXT2 == 2 * n[0].E_BASE


def under_report():
    """Bits by which aux_bits now understates. Was 64 at iteration 79."""
    c, b = correct_base_bits(), nado_base_bits()
    return None if c is None or b is None else c - b


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    if degree() is None:
        print("\n  (NADO tree unavailable -- nothing to check)")
        return
    S = _s()[0]
    sec("1. THREE STATES IN ABOUT TWENTY MINUTES")
    print(f"""
  NADO's soundness.py was edited in its WORKING TREE (uncommitted) three times
  while iterations 79-83 were running:

      state 1   E_EXT2 = 128 hard-coded                 aux_bits(2^17) = 109.0
      state 2   base = _D * E_BASE // 2 if _D != 2 ...  aux_bits(2^17) =  77.0
      state 3   base = E_FIELD() if e else E_BASE       aux_bits(2^17) = 173.0

  Iteration 79 reported state 1 -- the constant did not follow extf.DEGREE, so
  the module priced GF(p^2) while the transcript emitted GF(p^3). State 2 was an
  intermediate fix that HALVED the field: at _D = {degree()} and E_BASE = {S.E_BASE},
  {degree()} * {S.E_BASE} // 2 = {degree()*S.E_BASE//2}, where the challenge space of GF(p^D) is D * log2(p) = {correct_base_bits()}.

  State 2 was self-contradicting on its face: soundness.py:77 already defined
  E_EXT3 = {getattr(S, 'E_EXT3', '?')} for the same field, and the D = 2 branch was right
  (E_EXT2 = {S.E_EXT2} = 2 * {S.E_BASE}: {degree2_branch_is_right()}), so the two branches disagreed about
  what D * E_BASE meant.""")

    sec("2. THE CURRENT STATE IS CORRECT")
    print(f"""
      aux_bits(2^{LOG_ROWS} rows) now      {S.aux_bits(LOG_ROWS, ext=True):>7.1f}
      D * log2(p) - log2(buses*rows)  {correct_base_bits() - 19:>7.1f}
      discrepancy                     {under_report():>7.0f} bits

  NADO's own fix went further than the patch this file was drafting. It reads

      base = E_FIELD() if e else E_BASE

  routing the question through one function rather than a branch on the degree,
  so E_EXT2/E_EXT3 and the live value cannot drift apart again. Better than the
  `(_D * E_BASE)` this file would have proposed, which removes the halving but
  keeps the shape that allowed it.""")

    sec("3. THE FINDING IS THE DETECTION, NOT THE DEFECT")
    print("""
  State 2 existed for minutes and is gone. What is worth recording is that it
  was caught at all, by a check written in iteration 76 for a different purpose:

      check("the transcribed aux_bits matches NADO's own function exactly", ...)

  It failed on the first suite run after the edit -- "transcribed 109.0000 vs
  NADO's 77.0000". That check exists because iteration 76 had derived the LogUp
  offset from NADO's printed REPORT rather than its SOURCE, and pinning the two
  together was the correction. Pinning a transcription against a live tree turns
  out to detect regressions in that tree, which is more than it was built for.

  It also means this repo's NADO figures have a freshness problem no guard
  addresses: three different answers to the same call in twenty minutes. Any
  number quoted here about NADO is a number about NADO AT A MOMENT.""")


if __name__ == "__main__":
    report()
