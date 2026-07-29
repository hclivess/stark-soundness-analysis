"""
The test that certifies NADO's folded proofs are as strong as any other does not
run -- and iteration 79's caveat is resolved, in the direction that matters.

Iteration 79 found NADO's transcript emitting GF(p^3) while soundness.py priced
GF(p^2), and closed with a caveat: fri.py:52 says the recursion AIRs are "NOT
yet ported", so some backends might run ext=False at E_BASE = 64, in which case
150.8 would be one path's figure rather than the system's.

TWO ANSWERS, AND THEY POINT OPPOSITE WAYS
-------------------------------------------
FIRST, THE CAVEAT DISSOLVES. stark.ext_challenges_active(backend) reads:

    `backend` is now unread -- every backend answers the same. It stays in the
    signature ON PURPOSE: every caller asks this question ABOUT a backend, and
    the day a base-field one is reintroduced the answer becomes
    backend-dependent again without a single call site changing.

and returns fri.EXT_CHALLENGES unconditionally. There is no ext=False backend.
Its docstring also records that the recursion exclusion is gone:

    The RECURSION backend used to be excluded ... That exclusion is GONE --
    fri_verify, rowcomp_verify and recursive_verify all carry extension
    arithmetic now (test_recursion_ext), so a folded proof is as strong as any
    other.

So 150.8 is the system-wide figure, not one path's. tests/test_challenge_field_
policy.py passes and pins it.

SECOND, THE EVIDENCE FOR THAT CLAIM DOES NOT EXECUTE. test_recursion_ext -- the
test named in the sentence above as establishing that folded proofs are as
strong as any other -- ERRORS ON COLLECTION:

    tests/test_recursion_ext.py:47
        prog_ext = air_ir.build_program(LB._transitions(True), 12, 0, 2, ...)
    -> logup_bind.py:46  row[_aux(k, i)] for i in range(ext2.DEGREE)
    -> IndexError: list index out of range

THE CAUSE IS A DEGREE-2 LITERAL
---------------------------------
Trace width 12 is W_MAIN(6) + NUM_AUX_BASE(3) x 2. The 2 is the extension
degree, written as a literal. At DEGREE = 3 an extension-valued aux column is
carried as a TRIPLE of base columns, so the width must be

    W_MAIN + NUM_AUX_BASE * extf.DEGREE  =  6 + 9  =  15

Verified directly: build_program at width 12 raises IndexError, at width 15 it
builds. logup_bind itself is correct and already degree-parameterised --
NUM_AUX_EXT = NUM_AUX_BASE * ext2.DEGREE evaluates to 9 -- so the module follows
the degree and the TEST does not.

stark.py:47 anticipated this exact hazard and, in doing so, shows the same
degree-2 assumption in prose:

    an extension-valued aux column is carried as a PAIR of base columns, so
    num_aux DOUBLES under ext and the AIR must declare the width the prover
    will actually build.

Pair and doubles are degree-2 words. At degree 3 it is a triple and it triples.

THE PATTERN, NOW FOUR INSTANCES
---------------------------------
NADO parameterised the degree in one place, extf.DEGREE, and made the modules
that matter follow it -- transcript.challenge_ext reads it, logup_bind computes
its width from it. What has not followed are literals scattered outside those
modules:

    it 77  nado_ext_fri_prototype  a0, a1 = lift(v)          2-tuple unpack
    it 78  adversarial.py          final[0] = (1, 2, 3)      "wrong arity"
                                                             is now valid
    it 79  soundness.py:76         E_EXT2 = 128              degree-2 constant
    it 80  test_recursion_ext:47   width 12                  6 + 3 x 2

Each was silent in its own way: the first two disabled 26 forgery attacks, the
third under-reported security by 21 post-quantum bits, and this one turns a
certifying test into a collection error that pytest reports separately from
failures.

WHAT THIS DOES AND DOES NOT MEAN
----------------------------------
It does NOT mean folded proofs are weak. logup_bind's arithmetic is
degree-correct; nothing here suggests the prover is wrong. What is established
is narrower: the claim "a folded proof is as strong as any other" currently
rests on a test that does not run, so it is unverified rather than false.

The repair is one line in the test, and it should be computed rather than
written:

    -prog_ext = air_ir.build_program(LB._transitions(True), 12, 0, 2, ext_chal=True)
    +W_EXT = LB.W_MAIN + LB.NUM_AUX_BASE * extf.DEGREE
    +prog_ext = air_ir.build_program(LB._transitions(True), W_EXT, 0, 2, ext_chal=True)

Offered as text; this repo does not write to the NADO tree.
"""

import sys

NADO_PATH = "/root/nado"

# the literal in tests/test_recursion_ext.py:47, and its degree-2 provenance
TEST_LITERAL_WIDTH = 12
BASE_WIDTH_LITERAL = 9          # line 48, correct: W_MAIN + NUM_AUX_BASE
ASSUMED_DEGREE = 2

# the four instances of the same class found so far
DEGREE_LITERALS = [
    (77, "nado_ext_fri_prototype", "a0, a1 = lift(v)", "2-tuple unpack"),
    (78, "adversarial.py", "final[0] = (1, 2, 3)", "'wrong arity' now valid"),
    (79, "soundness.py:76", "E_EXT2 = 128", "degree-2 constant"),
    (80, "test_recursion_ext:47", "width 12", "W_MAIN + NUM_AUX_BASE * 2"),
]

PATCH = '''--- a/tests/test_recursion_ext.py
+++ b/tests/test_recursion_ext.py
@@
-prog_ext = air_ir.build_program(LB._transitions(True), 12, 0, 2, ext_chal=True)
+# 12 was W_MAIN(6) + NUM_AUX_BASE(3) * 2, with the 2 being the extension degree
+# written as a literal. logup_bind already computes its own width as
+# NUM_AUX_BASE * ext2.DEGREE, so at DEGREE = 3 an aux column is a TRIPLE and the
+# trace is 15 wide; the literal made build_program read past the end of a row.
+W_EXT = LB.W_MAIN + LB.NUM_AUX_BASE * extf.DEGREE
+prog_ext = air_ir.build_program(LB._transitions(True), W_EXT, 0, 2, ext_chal=True)
'''


def _nado():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import air_ir, extf, logup_bind
        return air_ir, extf, logup_bind
    except Exception:
        return None


def degree():
    n = _nado()
    return None if n is None else n[1].DEGREE


def correct_ext_width():
    """W_MAIN + NUM_AUX_BASE * DEGREE -- what the test literal should compute."""
    n = _nado()
    if n is None:
        return None
    _air, extf, LB = n
    return LB.W_MAIN + LB.NUM_AUX_BASE * extf.DEGREE


def literal_implied_degree():
    """The degree the hard-coded 12 was written for."""
    n = _nado()
    if n is None:
        return None
    _air, _extf, LB = n
    return (TEST_LITERAL_WIDTH - LB.W_MAIN) // LB.NUM_AUX_BASE


def builds_at(width):
    """Does build_program succeed at this trace width? (None if NADO absent.)"""
    n = _nado()
    if n is None:
        return None
    air_ir, _extf, LB = n
    try:
        air_ir.build_program(LB._transitions(True), width, 0, 2, ext_chal=True)
        return True
    except Exception:
        return False


def module_width_follows_degree():
    """logup_bind's own NUM_AUX_EXT tracks the degree -- the module is correct."""
    n = _nado()
    if n is None:
        return None
    _air, extf, LB = n
    return LB.NUM_AUX_EXT == LB.NUM_AUX_BASE * extf.DEGREE


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    d = degree()
    if d is None:
        print("\n  (NADO tree unavailable -- nothing to check)")
        return

    sec("1. ITERATION 79's CAVEAT DISSOLVES: THERE IS NO ext=False BACKEND")
    print("""
  stark.ext_challenges_active(backend) returns fri.EXT_CHALLENGES
  unconditionally, and says so:

      `backend` is now unread -- every backend answers the same. It stays in the
      signature ON PURPOSE ... the day a base-field one is reintroduced the
      answer becomes backend-dependent again without a single call site
      changing.

  So iteration 79's 150.8 is the SYSTEM-WIDE figure, not one path's.
  tests/test_challenge_field_policy.py passes and pins it.""")

    sec("2. BUT THE TEST THAT CERTIFIES FOLDED PROOFS DOES NOT RUN")
    print(f"""
  stark.py's docstring says the recursion exclusion is "GONE -- fri_verify,
  rowcomp_verify and recursive_verify all carry extension arithmetic now
  (test_recursion_ext)". That test ERRORS ON COLLECTION:

      tests/test_recursion_ext.py:47
          build_program(LB._transitions(True), {TEST_LITERAL_WIDTH}, 0, 2, ext_chal=True)
      -> logup_bind.py:46  row[_aux(k, i)] for i in range(ext2.DEGREE)
      -> IndexError: list index out of range

  Width {TEST_LITERAL_WIDTH} is W_MAIN + NUM_AUX_BASE * {literal_implied_degree()} -- the extension degree
  written as a literal. At DEGREE = {d} an aux column is a TRIPLE, so the width is
  {correct_ext_width()}.
""")
    print(f"  {'width':>7} {'build_program':>15}")
    print("  " + "-" * 26)
    for w in (TEST_LITERAL_WIDTH, correct_ext_width()):
        print(f"  {w:>7} {'OK' if builds_at(w) else 'IndexError':>15}")
    print(f"""
  logup_bind itself is CORRECT and already degree-parameterised:
  NUM_AUX_EXT == NUM_AUX_BASE * DEGREE is {module_width_follows_degree()}. The module follows the
  degree; the test does not.

  stark.py:47 anticipated this hazard and shows the same assumption in prose --
  "carried as a PAIR of base columns, so num_aux DOUBLES under ext". Pair and
  doubles are degree-2 words; at degree {d} it is a triple and it triples.""")

    sec("3. THE PATTERN: FOUR INSTANCES OF ONE CLASS")
    print(f"\n  {'it':>4} {'site':<26} {'literal':<24} {'was':<24}")
    print("  " + "-" * 80)
    for it, site, lit, was in DEGREE_LITERALS:
        print(f"  {it:>4} {site:<26} {lit:<24} {was:<24}")
    print("""
  NADO parameterised the degree in ONE place and made the modules that matter
  follow it -- challenge_ext reads extf.DEGREE, logup_bind computes its width
  from it. What has not followed are literals outside those modules. Each was
  silent differently: two disabled 26 forgery attacks, one under-reported
  security by 21 post-quantum bits, and this one turns a certifying test into a
  collection error, which pytest reports separately from failures and is easy to
  read past.""")

    sec("4. WHAT THIS DOES NOT MEAN, AND THE REPAIR")
    print("""
  It does NOT mean folded proofs are weak. logup_bind's arithmetic is
  degree-correct and nothing here suggests the prover is wrong. What is
  established is narrower: the claim "a folded proof is as strong as any other"
  rests on a test that does not run, so it is UNVERIFIED rather than false.
""")
    print(PATCH)
    print("  Offered as text; this repo does not write to the NADO tree.")


if __name__ == "__main__":
    report()
