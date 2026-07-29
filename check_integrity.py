"""
Auditing the falsification suite against itself: which checks cannot fail?

Iteration 65 retracted a claim that had survived a full day inside a PASSING
check. The check computed something true and asserted something false in its
NAME:

    check("eta's default branches on field size, which this repo had missed",
          eta_default(0.125, 2**192) != eta_default(0.125, 2**124), ...)

The condition is correct -- the two branches do differ. The clause "which this
repo had missed" was never tested by anything, and was wrong. A green suite said
nothing about it.

That is a class, not an incident, and this repo has met it before: tautological
placeholders were caught by hand in iterations 24, 26, 30, 37 and 43. Five
manual catches is the signature of something that should be mechanical.

WHAT IS MECHANICALLY DETECTABLE
---------------------------------
Not "does the name match the claim" -- that needs a reader. But a strong proxy
is: DOES THE CONDITION DEPEND ON ANYTHING AT ALL? A condition built only from
literals can never fail because of a change to this repository. It is a
statement typed into a file, dressed as a test.

Parsing adversarial.py's AST and classifying all 418 check() call sites:

    conditions referencing no identifier whatsoever      13
    of those, bare `True`                                 3

After iteration 66's fixes the count is 9: three bare-`True` sites resolved,
and the hash-ceiling pair rebound to quantum.pq_bits.

The three bare-`True` checks were:

    L609  "DEEP is off the main STARK path"
    L639  "the QROM constant is still unfetched"
    L642  "no consulted calculator publishes a post-quantum column"

All three were honest notes when written -- claims about the world or about
another codebase that the suite had no way to reach. Two of them can now be
reached, because later iterations brought the evidence into the working tree:

    L642  soundcalc is cloned locally. grep for quantum|grover|qrom across
          its entire Python source: 0 hits. Now a real check.
    L609  /root/nado is on this machine. stark.py contains 0 references to
          deep_eval, which lives in its own module. Now a real check.

    L639  is a statement about the accessibility of an eprint PDF. It cannot be
          verified offline and should never have been a check(). Demoted to a
          printed note. A check that cannot fail is worse than a comment,
          because it inflates the count and implies verification.

THE REMAINING NINE
-------------------
Arithmetic on published constants -- `256 / 2 == 128`, `(310 - 22) / 2 >= 128`.
These are not tautologies: they encode real claims, and getting one wrong would
be a real error. But they restate arithmetic rather than exercising the repo, so
they cannot catch a regression in the code they are about. Where a function
exists that computes the same thing, the check should call it. quantum.pq_bits
is exactly such a function for the hash-ceiling family, so those now go through
it and would fail if pq_bits changed.

THE GUARD
----------
`literal_only_checks()` re-runs this classification on every suite run. The
budget is pinned at the audited number (9), so a NEW literal-only check fails
the suite immediately. It is not a ban -- some claims genuinely have no repo-facing
computation -- but adding one now has to be deliberate rather than accidental.

This is the third structural guard, and they follow one pattern: iteration 41
made a regime-scope error impossible by construction, iteration 65 pinned
duplicated definitions to each other, and this pins the suite's own honesty. The
common lesson is that a repository which corrects itself needs the corrections
to be enforced by machinery, because the same mistake will otherwise be made by
the same person for the same reason.
"""

import ast
import os

SUITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adversarial.py")

# Audited in iteration 66. Literal-only conditions remaining after the three
# bare-`True` sites were resolved. Raising this number requires a reason.
LITERAL_ONLY_BUDGET = 9

# claims that were bare `True` and are now mechanically verified
RESOLVED = {
    "soundcalc PQ column": ("grep quantum|grover|qrom over the cloned "
                            "soundcalc source", 0),
    "NADO DEEP path": ("grep deep_eval in /root/nado/execnode/stark/stark.py", 0),
}


def _check_calls(path=SUITE):
    """(lineno, name_node, condition_node) for every check(...) call site."""
    tree = ast.parse(open(path).read())
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "check" and len(node.args) >= 2):
            out.append((node.lineno, node.args[0], node.args[1]))
    return out


def _identifiers(expr):
    return ({n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}
            | {n.attr for n in ast.walk(expr) if isinstance(n, ast.Attribute)})


def literal_only_checks(path=SUITE):
    """Check sites whose condition references no identifier: cannot fail on a
    code change. Returns [(lineno, source)]."""
    return [(ln, ast.unparse(cond))
            for ln, _name, cond in _check_calls(path)
            if not _identifiers(cond)]


def self_comparison_checks(path=SUITE):
    """Conditions comparing a subexpression to a STRUCTURALLY IDENTICAL one:
    f(x) == f(x), abs(g(y) - g(y)) < eps, and so on. These reference
    identifiers, so literal_only_checks cannot see them, but they are just as
    incapable of failing.

    ADDED IN ITERATION 76, after I wrote three of them in a single block --
    the same tautology class caught by hand in iterations 24, 26, 30, 37 and 43.
    The literal-only auditor missed them precisely because they call real
    functions.
    """
    found = []
    for ln, _name, cond in _check_calls(path):
        for node in ast.walk(cond):
            if isinstance(node, ast.Compare) and len(node.comparators) == 1:
                left, right = node.left, node.comparators[0]
                if ast.dump(left) == ast.dump(right) and _identifiers(left):
                    found.append((ln, ast.unparse(node)))
                    break
            # abs(A - A) < eps
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
                    and ast.dump(node.left) == ast.dump(node.right)
                    and _identifiers(node.left)):
                found.append((ln, ast.unparse(node)))
                break
    return found


def always_true_checks(path=SUITE):
    """The worst case: conditions that are the literal `True`."""
    return [(ln, ast.unparse(cond))
            for ln, _name, cond in _check_calls(path)
            if isinstance(cond, ast.Constant) and cond.value is True]


def total_check_sites(path=SUITE):
    return len(_check_calls(path))


def self_test():
    """The auditor must FLAG a literal-only check AND a self-comparison, and
    must spare a real one. Otherwise it is inert."""
    import tempfile
    src = ("def check(a, b, c=''): pass\n"
           "check('real', some_fn(1) > 0)\n"
           "check('fake', 2 + 2 == 4)\n"
           "check('taut', some_fn(3) == some_fn(3))\n"
           "check('taut2', abs(g(y) - g(y)) < 1e-9)\n")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(src)
        tmp = f.name
    try:
        lit = literal_only_checks(tmp)
        selfcmp = self_comparison_checks(tmp)
        return (len(lit) == 1 and "2 + 2" in lit[0][1]
                and len(selfcmp) == 2
                and not any("some_fn(1)" in srcline for _l, srcline in selfcmp))
    finally:
        os.unlink(tmp)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE CLASS ITERATION 65 EXPOSED")
    print("""
  A check passed for a full day while asserting something false, because the
  falsehood was in its NAME and not its condition:

      check("eta's default branches on field size, which this repo had missed",
            eta_default(0.125, 2**192) != eta_default(0.125, 2**124), ...)

  The condition is correct. "which this repo had missed" was never tested by
  anything, and was wrong. Tautological placeholders were also caught by hand in
  iterations 24, 26, 30, 37 and 43 -- five manual catches, which is the
  signature of something that should be mechanical.""")

    sec("2. WHAT A MACHINE CAN SEE: CONDITIONS THAT DEPEND ON NOTHING")
    lit = literal_only_checks()
    always = always_true_checks()
    print(f"""
  Name-versus-claim needs a reader. But a condition built only from literals can
  never fail because of a change to this repository -- it is a statement typed
  into a file, dressed as a test.

      check() call sites parsed                {total_check_sites()}
      conditions referencing no identifier     {len(lit)}
      of those, bare `True`                    {len(always)}
""")
    for ln, srcline in lit:
        print(f"    L{ln:<6} {srcline[:70]}")

    sec("3. TWO OF THE THREE ARE NOW REACHABLE")
    print("""
  All three bare-`True` checks were honest notes when written -- claims about
  the world or another codebase the suite could not reach. Later iterations
  brought the evidence into the working tree:\n""")
    for label, (how, expect) in RESOLVED.items():
        print(f"    {label:<22} {how}")
        print(f"    {'':<22}   expected hits: {expect}  -> now a real check")
    print("""
    QROM constant           a statement about whether an eprint PDF is
                            reachable. Cannot be verified offline, so it should
                            never have been a check(). Demoted to a printed
                            note: a check that cannot fail is worse than a
                            comment, because it inflates the count and implies
                            verification that did not happen.""")

    sec("4. THE GUARD, AND WHY IT IS THE THIRD OF ITS KIND")
    print(f"""
  literal_only_checks() re-runs this classification on every suite run, with the
  budget pinned at {LITERAL_ONLY_BUDGET}. A new literal-only check fails the suite. Not a ban --
  some claims genuinely have no repo-facing computation -- but adding one now
  has to be deliberate.

  auditor self-test (does it flag a planted literal-only check?): """
          f"{'PASS' if self_test() else 'FAIL -- THE AUDITOR IS INERT'}")
    print("""
  Third structural guard, and they share a pattern: iteration 41 made a
  regime-scope error impossible by construction, iteration 65 pinned duplicated
  definitions to each other, this pins the suite's own honesty. A repository
  that corrects itself needs the corrections enforced by machinery, because the
  same mistake will otherwise be made by the same person for the same reason.""")


if __name__ == "__main__":
    report()
