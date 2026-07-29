"""
NADO's soundness module reports 109 bits. Its prover has been drawing GF(p^3)
challenges. The live system is at 150.8, and its own accounting does not know.

Iteration 75 recommended GF(p^2) -> GF(p^3), worth +20.9 post-quantum bits.
Iteration 76 added that the D=2 ceiling decays a bit per trace doubling and
that D=3 removes the dependence until ~2^39 rows. Iteration 78 noticed that
fri.py had begun importing `extf as ext2`.

The switch has been thrown. The accounting has not followed.

THE EVIDENCE
--------------
    extf.DEGREE                    3
    Transcript.challenge_ext()     returns 3 limbs
    soundness.E_EXT2               128        <- hard-coded, degree 2
    soundness.aux_bits(17)         109.0      <- computed from that constant

soundness.py contains no reference to `extf` or `DEGREE` at all. Its E_EXT2 is
written as a literal at line 76 and consumed at :88 and :148. So every term the
module prints is evaluated in a field the system stopped using.

Transcript.challenge_ext, by contrast, reads the degree from the module:

    D INDEPENDENT base-field draws, with D read from extf.DEGREE rather than
    written here. This is the SINGLE ORIGIN of every extension challenge -- the
    FRI folding alpha, the DEEP point, the constraint alphas and the LogUp bus
    challenges all come through it -- so a hardcoded arity here is uniquely
    dangerous: prover and verifier would still agree with EACH OTHER while
    sampling a smaller space than the soundness analysis claims, and nothing
    would fail. It would simply be weaker.

That is exactly the failure this file reports, in mirror image. The docstring
guards against a hardcoded arity in the CHALLENGE understating what the analysis
claims. Here the hardcoded constant is in the ANALYSIS, and it understates what
the challenge actually samples. The direction is safe -- the system is stronger
than it says -- but the figure is wrong and it conceals a gain already paid for.

WHAT NADO ACTUALLY ACHIEVES
-----------------------------
At E = 64 * 3 = 192, with everything else unchanged:

    term        reported (E=128)    actual (E=192)
    LogUp bus              109.0             173.0
    commit                 112.0             176.0
    constraint alphas      126.0             190.0
    query phase            150.8             150.8    <- independent of E
    ----------------------------------------------
    PROVABLE               109.0             150.8
    post-quantum            54.5              75.4

Understated by 41.8 classical and 20.9 post-quantum bits. And the binding term
has moved: at E=128 it was the LogUp bus, at E=192 it is the query phase, which
is exactly the transition iteration 75 predicted and iteration 76 showed
removes the trace-size decay.

So NADO is no longer the exception to this repo's finding 2. It is now
query-bound like the seven verified zkVMs, and Proposition 11's cap
(s*R/2 + g = 178 classical at the current schedule) applies to it.

THE FIX IS ONE LINE, AND THE MODULE IS ALREADY SHAPED FOR IT
--------------------------------------------------------------
soundness.py:296 already defines and uses an E_EXT3 constant for a comparison
table, so degree 3 is contemplated in the file. What is missing is that the LIVE
constant does not follow the module that decides the degree. The patch is below
in section 3; it is offered as text, not applied -- this repo does not write to
the NADO tree.

WHAT THIS DOES NOT CLAIM
--------------------------
That the whole prover is at degree 3. fri.py:52 still carries "NOT yet ported --
both must pass ext=False until they are: native/starkprove sp_fold, and the
in-circuit fri_verify.py recursion AIRs", so some paths may still run ext=False
and sit at E_BASE = 64. What is established here is narrower and sufficient to
make the reported figure wrong: the single origin of every extension challenge
now emits 3 limbs, and the module that prices those challenges thinks it emits
2.

Anyone reconciling this should check which backends actually pass ext=True
before quoting 150.8 as the system-wide figure. The 109.0 is wrong either way,
because it is computed from a constant rather than from the degree in force.
"""

import sys

NADO_PATH = "/root/nado"

REPORTED = dict(E=128, logup=109.0, commit=112.0, alphas=126.0, query=150.8,
                provable=109.0)
BASE_BITS = 64
LOG_ROWS = 17
BUSES = 4
NU = 18                      # trace 2^17 at blowup 2


def _nado():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import extf, soundness
        from execnode.stark.transcript import Transcript
        return extf, soundness, Transcript
    except Exception:
        return None


def live_degree():
    """The degree the transcript actually emits, or None if NADO is absent."""
    n = _nado()
    if n is None:
        return None
    _extf, _s, Transcript = n
    c = Transcript(b"probe").challenge_ext()
    return len(c) if hasattr(c, "__len__") else 1


def declared_degree():
    n = _nado()
    return None if n is None else n[0].DEGREE


def accounting_E():
    """The E soundness.py prices challenges at -- a literal, not a lookup."""
    n = _nado()
    return None if n is None else n[1].E_EXT2


def accounting_follows_degree():
    """Does soundness.py's constant track extf.DEGREE? It does not."""
    d, E = declared_degree(), accounting_E()
    if d is None or E is None:
        return None
    return E == BASE_BITS * d


def terms_at(E, log_rows=LOG_ROWS, nu=NU, buses=BUSES, query=REPORTED["query"]):
    """The four algebraic terms, at a given challenge-space size."""
    import math
    return dict(logup=E - math.log2(buses * 2 ** log_rows),
                commit=E - nu + 2,
                alphas=E - 2.0,
                query=query)


def provable_at(E):
    return min(terms_at(E).values())


def understatement():
    """(classical bits, post-quantum bits) by which the report is low."""
    d = declared_degree()
    if d is None:
        return None
    actual = provable_at(BASE_BITS * d)
    return actual - REPORTED["provable"], (actual - REPORTED["provable"]) / 2


def binding_term(E):
    t = terms_at(E)
    return min(t, key=t.get)


PATCH = '''--- a/execnode/stark/soundness.py
+++ b/execnode/stark/soundness.py
@@
-E_EXT2 = 128                # log2 |GF(p^2)|
+# The challenge space is whatever extf is compiled for, not a constant written
+# here. Transcript.challenge_ext already reads extf.DEGREE and warns that a
+# hardcoded arity there would let prover and verifier "sample a smaller space
+# than the soundness analysis claims". The mirror of that is this line: with
+# extf.DEGREE = 3 the analysis priced GF(p^2) while the transcript emitted
+# GF(p^3), reporting 109.0 bits for a system at 150.8.
+from execnode.stark.extf import DEGREE as _EXT_DEGREE
+E_EXT2 = E_BASE * _EXT_DEGREE      # keep the name; the value follows the module
'''


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE SWITCH WAS THROWN; THE ACCOUNTING DID NOT FOLLOW")
    ld, dd, E = live_degree(), declared_degree(), accounting_E()
    if ld is None:
        print("\n  (NADO tree unavailable -- nothing to check)")
        return
    print(f"""
      extf.DEGREE                  {dd}
      challenge_ext() limbs        {ld}
      soundness.E_EXT2             {E}        <- hard-coded, degree 2
      soundness.aux_bits(2^17)     {REPORTED['logup']}      <- computed from it

  soundness.py contains no reference to extf or DEGREE. E_EXT2 is a literal at
  line 76, consumed at :88 and :148, so every term it prints is evaluated in a
  field the system stopped using.

  accounting follows the live degree? {accounting_follows_degree()}""")

    sec("2. WHAT NADO ACTUALLY ACHIEVES")
    act = BASE_BITS * dd
    tr, ta = terms_at(REPORTED["E"]), terms_at(act)
    print(f"\n  {'term':<20} {'reported (E=' + str(REPORTED['E']) + ')':>18} "
          f"{'actual (E=' + str(act) + ')':>18}")
    print("  " + "-" * 58)
    for k in ("logup", "commit", "alphas", "query"):
        tail = "   <- independent of E" if k == "query" else ""
        print(f"  {k:<20} {tr[k]:>18.1f} {ta[k]:>18.1f}{tail}")
    print("  " + "-" * 58)
    print(f"  {'PROVABLE':<20} {provable_at(REPORTED['E']):>18.1f} "
          f"{provable_at(act):>18.1f}")
    print(f"  {'post-quantum':<20} {provable_at(REPORTED['E'])/2:>18.1f} "
          f"{provable_at(act)/2:>18.1f}")
    c, q = understatement()
    print(f"""
  Understated by {c:.1f} classical and {q:.1f} post-quantum bits.

  And the binding term has MOVED: {binding_term(REPORTED['E'])} at E={REPORTED['E']},
  {binding_term(act)} at E={act}. That is the transition iteration 75 predicted and
  iteration 76 showed removes the trace-size decay -- so NADO is no longer the
  exception to finding 2. It is query-bound like the seven verified zkVMs, and
  Proposition 11's cap applies to it.""")

    sec("3. THE PATCH, AS TEXT")
    print("\n" + PATCH)
    print("""  soundness.py:296 already defines E_EXT3 for a comparison table, so degree 3
  is contemplated in the file. What is missing is that the LIVE constant does
  not follow the module that decides the degree.

  NOT CLAIMED: that the whole prover is at degree 3. fri.py:52 still says "NOT
  yet ported ... native/starkprove sp_fold, and the in-circuit fri_verify.py
  recursion AIRs", so some paths may run ext=False at E_BASE = 64. What is
  established is narrower and enough to make the printed figure wrong: the
  single origin of every extension challenge emits 3 limbs, and the module
  pricing them thinks it emits 2.""")


if __name__ == "__main__":
    report()
