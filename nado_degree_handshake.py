"""
Sweeping NADO for the remaining degree-2 literals: one matters, it was dead
code, and NADO built a handshake for it before I looked -- then closed it.

*** SUPERSEDED IN ITERATION 84, ABOUT THIRTY MINUTES LATER. ***
Everything below described a real state: the arena was compiled for degree 2,
ext_capable() returned False, fold_ext raised on a 3-limb alpha, and extension
proofs composed in Python at 2.8x. NADO then rebuilt the arena for degree 3 and
generalised the entry point -- fold_ext(cols, offset, alpha) now takes a COLUMN
LIST rather than a lo/hi pair, and ext_capable() returns True. The native
GF(p^3) path is live and the 2.8x penalty is gone.

The analysis is kept because the handshake's behaviour is the finding, and it
was verified in BOTH states: it refused when the degrees differed and permits
now that they match. The checks in adversarial.py were rewritten to pin that
invariant rather than the snapshot.

Iteration 80 found four stale degree-2 literals in four files and framed them as
a pattern of things NADO's degree parameterisation had not reached. This
iteration swept for the rest.

WHAT THE SWEEP FOUND
----------------------
Static hunt across execnode/ and tests/ for 2-tuple unpacks of extension values,
`* 2` near aux/limb/width, and range(2) where DEGREE is meant. Almost every hit
is a false positive -- `a, b = lift(u), lift(v)` is two SEPARATE elements, not
one element's limbs, and rowcomp_verify's range(2) is cur-row/next-row.

One hit is real:

    stark_native.py:280   a0, a1 = ext2.lift(alpha)

and it is not a stray literal, it is a degree-2 INTERFACE:

    def fold_ext(col_lo, col_hi, offset, alpha):
        # "One GF(p^2) FRI fold of an extension column pair -> a new
        #  half-length pair; returns the LO id (HI is lo+1)."
        a0, a1 = ext2.lift(alpha)
        cid = _LIB.sp_fold_ext(col_lo, col_hi, offset, a0, a1)

A lo/hi column PAIR, two alpha limbs, and a C entry point taking both. At
DEGREE = 3 it raises ValueError: too many values to unpack (expected 2).
Widening it is a Rust ABI change, not a Python one.

IT IS DEAD CODE, AND DELIBERATELY SO
--------------------------------------
The native library reports the degree it was compiled for, and the Python side
refuses to use it unless they match:

    def ext_capable():
        # The symbols existing says nothing about which field they implement.
        # A degree-mismatched arena does not fail -- it composes a well-formed
        # polynomial over the wrong field, and the only symptom is a
        # "trace/composition mismatch" at verification with nothing pointing at
        # the field. So the degree is part of the handshake, and a library that
        # cannot answer is treated as pre-port.
        return int(_LIB.sp_ext_degree()) == extf.DEGREE

Measured against the installed library:

    native arena compiled for DEGREE   2
    Python side                        3
    ext_capable()                      False

Two call sites gate on it -- stark_native.py:377 raises a RuntimeError naming
both degrees, and stark.py:301 computes _native_ok and takes the Python path.
So the degree-2 fold cannot be reached, and cannot silently prove over the wrong
field.

That handshake landed in commit bb09fe4, "GF(p^3) AIR layout + a DEGREE
HANDSHAKE so a mismatched arena cannot silently prove the wrong field", which is
the same commit that moved the AIR layout to degree 3. The hazard was designed
for, not stumbled into.

SO ITERATION 80's FRAMING NEEDS QUALIFYING
--------------------------------------------
It presented four stale literals as a class NADO's parameterisation had not
reached. The commit order says otherwise:

    04b5af2  bind the GF(p^2) arena entry points (compose_ext / fold_ext)
    daa9adf  run the native arena under GF(p^2) -- 32.5s -> 12.2s
    bb09fe4  GF(p^3) AIR layout + a DEGREE HANDSHAKE
    39bffcb  extf.canon() and fix four more int()-on-an-extension-value sites

NADO is sweeping the same class I am -- 39bffcb is literally a batch of these --
and guarded the one site that cannot be fixed in Python. The literals iterations
77-80 found are real, and the one in tests/test_recursion_ext.py:47 is still
live, but the picture is a migration in progress with a guard on its most
dangerous edge, not an unnoticed pattern.

WHAT IT COSTS RIGHT NOW
-------------------------
Performance, not soundness. The native GF(p^2) arena -- 32.5s -> 12.2s on a real
exec AIR -- is unreachable while the Python side is degree 3, so extension
proofs compose in Python. stark.py's own docstring prices it:

    The cost is speed, not soundness: the Rust arena multiplies by a base-field
    u64 alpha, so an ext proof composes in Python. Measured 2.8x on a real exec
    AIR (17.4s vs 6.2s). Porting native/starkprove's sp_fold to extension
    arithmetic recovers it and changes nothing about what is proven.

That is the live state: NADO is at 150.8 classical / 75.4 PQ (iteration 79) and
paying roughly 2.8x in composition to be there, until sp_fold_ext's ABI widens
from 2 limbs to D.
"""

import sys

NADO_PATH = "/root/nado"

# commit order establishing that the handshake was designed, not retrofitted
COMMITS = [
    ("04b5af2", "bind the GF(p^2) arena entry points (compose_ext / fold_ext)"),
    ("daa9adf", "run the native arena under GF(p^2) -- 32.5s -> 12.2s"),
    ("bb09fe4", "GF(p^3) AIR layout + a DEGREE HANDSHAKE"),
    ("39bffcb", "extf.canon() and fix four more int()-on-an-extension-value sites"),
]

# the one real hit from the static sweep
DEGREE2_INTERFACE = ("stark_native.py:280", "a0, a1 = ext2.lift(alpha)",
                     "lo/hi column pair + 2-limb sp_fold_ext ABI")

COMPOSE_SLOWDOWN = 2.8          # stark.py: 17.4s vs 6.2s on a real exec AIR


def _sn():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import extf, stark_native
        return stark_native, extf
    except Exception:
        return None


def native_degree():
    """The degree the installed .so was compiled for, or None."""
    n = _sn()
    if n is None:
        return None
    SN, _ = n
    import ctypes
    if not SN.available() or not hasattr(SN._LIB, "sp_ext_degree"):
        return None
    SN._LIB.sp_ext_degree.restype = ctypes.c_int64
    return int(SN._LIB.sp_ext_degree())


def python_degree():
    n = _sn()
    return None if n is None else n[1].DEGREE


def ext_capable():
    n = _sn()
    return None if n is None else n[0].ext_capable()


def handshake_blocks_mismatch():
    """The probe must refuse exactly when the degrees differ."""
    nd, pd, cap = native_degree(), python_degree(), ext_capable()
    if nd is None or pd is None:
        return None
    return cap == (nd == pd)


def fold_ext_raises():
    """The degree-2 entry point must fail loudly, not compute something wrong."""
    n = _sn()
    if n is None:
        return None
    SN, extf = n
    try:
        SN.fold_ext(0, 1, 1, extf.ONE)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    nd, pd = native_degree(), python_degree()
    if pd is None:
        print("\n  (NADO tree unavailable -- nothing to check)")
        return

    sec("1. THE SWEEP: ONE REAL HIT, AND IT IS AN INTERFACE NOT A LITERAL")
    print(f"""
  Static hunt for 2-tuple unpacks of extension values, `* 2` near aux/limb/
  width, and range(2) where DEGREE is meant. Almost all hits are false
  positives -- `a, b = lift(u), lift(v)` is two SEPARATE elements, and
  rowcomp_verify's range(2) is cur-row/next-row.

  One is real:

      {DEGREE2_INTERFACE[0]}   {DEGREE2_INTERFACE[1]}
      {DEGREE2_INTERFACE[2]}

  At DEGREE = {pd} it raises ValueError: {fold_ext_raises()}. Widening it is a Rust ABI
  change, not a Python one.""")

    sec("2. IT IS DEAD CODE, AND DELIBERATELY SO")
    print(f"""
  ext_capable() requires the library to REPORT its degree and match:

      native arena compiled for DEGREE   {nd}
      Python side                        {pd}
      ext_capable()                      {ext_capable()}

  handshake refuses exactly when the degrees differ: {handshake_blocks_mismatch()}

  Two call sites gate on it -- stark_native.py:377 raises a RuntimeError naming
  both degrees, stark.py:301 computes _native_ok and takes the Python path. The
  degree-2 fold cannot be reached and cannot silently prove over the wrong
  field.""")

    sec("3. WHICH QUALIFIES ITERATION 80's FRAMING")
    print(f"\n  {'commit':<10} {'subject':<62}")
    print("  " + "-" * 74)
    for h, subj in COMMITS:
        mark = "  <- the handshake" if h == "bb09fe4" else ""
        print(f"  {h:<10} {subj:<62}{mark}")
    print("""
  Iteration 80 presented four stale literals as a class NADO's parameterisation
  had not reached. The order says otherwise: NADO is sweeping the same class
  (39bffcb is literally a batch of them) and guarded the one site that cannot be
  fixed in Python. The literals iterations 77-80 found are real, and
  tests/test_recursion_ext.py:47 is still live, but this is a migration in
  progress with a guard on its most dangerous edge -- not an unnoticed pattern.""")

    sec("4. WHAT IT COSTS: SPEED, NOT SOUNDNESS")
    print(f"""
  The native GF(p^2) arena (32.5s -> 12.2s on a real exec AIR) is unreachable
  while Python is at degree {pd}, so extension proofs compose in Python. stark.py
  prices it at {COMPOSE_SLOWDOWN}x (17.4s vs 6.2s) and says porting sp_fold "recovers it and
  changes nothing about what is proven".

  So the live state is: NADO at 150.8 classical / 75.4 PQ (iteration 79), paying
  roughly {COMPOSE_SLOWDOWN}x in composition to be there, until sp_fold_ext's ABI widens from
  2 limbs to {pd}.""")


if __name__ == "__main__":
    report()
