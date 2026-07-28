"""
`a` is not one number. It is a staircase in the proximity radius -- and both the
README's table and iteration 32's conclusion are wrong about different steps.

The repository has carried "code proximity layers have a >= 1" since iteration 6,
and iteration 32 softened it to "proved for interleaved codes, merely observed
for FRI/WHIR, and nothing known forbids a = 0 for RS at the Johnson radius".

Reading the abstract of the paper the whole model is built on -- BCHKS25, which
this repo has cited in every iteration without ever reading its result list --
shows the truth is a staircase, and that BOTH statements are wrong:

  * a = 0 is PROVED at the unique-decoding radius. Not open, not conjectural.
  * a is UNBOUNDED above the Johnson radius. Iteration 32's "nothing forbids
    a = 0 there" is false; BCHKS25 forbids it for some codes and some delta.

SOURCE (eprint 2025/2055, abstract page fetched -- the PDF is Cloudflare-walled)
--------------------------------------------------------------------------------
Ben-Sasson, Carmon, Habock, Kopparty, Saraf, "On Proximity Gaps for Reed-Solomon
Codes". Its five results, quoted:

 1. "For proximity gaps up to the unique decoding radius delta/2, we show that
    arbitrarily small proximity loss eps* > 0 can be achieved with only
    O_{eps*}(1) exceptional z's (improving the previous bound of O(n))."

 2. "For proximity gaps up to the Johnson radius J(delta), we show that
    proximity loss eps* = 0 can be achieved with only O(n) exceptional z's
    (improving the previous bound of O(n^2))."

 3. "In the other direction, we show that for some Reed-Solomon codes and some
    delta, proximity gaps at or beyond the Johnson radius J(delta) with
    arbitrarily small proximity loss eps* needs to have at least Omega(n^1.99)
    exceptional z's."

 4. "More generally, for all constants tau, we show that for some Reed-Solomon
    codes and some delta = delta(tau), proximity gaps at radius
    delta - Omega_tau(1) with arbitrarily small proximity loss eps* needs to
    have n^tau exceptional z's."

 5. "Finally, for all Reed-Solomon codes, we show that improved proximity gaps
    imply improved bounds for their list-decodability. This shows that improved
    bounds on the list-decoding radius of Reed-Solomon codes is a prerequisite
    for any new proximity gaps results beyond the Johnson radius."

The number of exceptional z's IS the numerator of the commit error (eps =
#exceptions / q), so each result reads directly as a value of `a`.

THE STAIRCASE
-------------
    radius                       exceptions      a          proximity loss
    ------------------------------------------------------------------------
    unique decoding, delta/2     O_{eps*}(1)     0          eps* > 0
    Johnson, J(delta)            O(n)            1          eps* = 0
    at/beyond Johnson            Omega(n^1.99)   >= 1.99    eps* -> 0, some codes
    delta - Omega_tau(1)         n^tau           tau        eps* -> 0, some codes

CORRECTION 1 -- a = 0 IS ALREADY PROVED, AT THE UNIQUE-DECODING RADIUS
------------------------------------------------------------------------
The repo has treated a = 0 as the prize: ceiling_anatomy.py calls it "the single
largest unclaimed win", conditional on Q2 via eprint 2026/861. But BCHKS25 gives
it unconditionally at the unique-decoding radius, at the cost of an arbitrarily
small proximity loss eps* > 0.

And the UDR regime is not hypothetical: this repo's own Theorem 7 finds SP1 and
OpenVM deployed there, with SP1's config declaring udr_only = true. soundcalc,
which this repo transcribed, implements the OLD UDR bound -- (gamma*n + 1)/|F|,
i.e. O(n) exceptions, a = 1. Section 2 prices the difference.

CORRECTION 2 -- ITERATION 32 OVERSTATED THE ROOM ABOVE JOHNSON
----------------------------------------------------------------
Iteration 32 concluded "the strongest known lower bound does not forbid a = 0
for RS at the Johnson radius. It never did." That was reasoned from a mutual-
correlated-agreement floor whose numerator is the list size. It missed BCHKS25
results 3 and 4, which are proximity-gap lower bounds directly: at or beyond
Johnson, some RS codes need Omega(n^1.99) exceptions, and for any constant tau
some code needs n^tau. So above Johnson, a is not merely un-forbidden at 0 -- it
is provably unbounded for the worst families.

Two things survive from iteration 32: the MCA floor is real and correctly scoped
to WHIR, and the a >= 1 floor for interleaved codes is still the only sharp one.
What does not survive is the inference that a = 0 above Johnson is unobstructed.

CONSEQUENCE FOR eprint 2026/861
--------------------------------
Its claim is O(1)/|F| for plain Reed-Solomon ABOVE the Johnson radius. BCHKS25
result 5 says any such result requires improved RS list-decoding bounds first --
a famously hard and well-studied problem -- and result 3 exhibits families where
Omega(n^1.99) is necessary. So the claim is not merely unverified (iteration 31)
nor merely "structurally consistent" (iteration 32): it must thread between
proved counterexamples, which is what its sparse-input restriction and Q2 are
presumably for. That is a much sharper characterisation than either earlier
iteration reached, and it is the honest one.
"""

import math

# (label, radius, exceptions-exponent a, proximity loss, scope)
STAIRCASE = [
    ("unique decoding delta/2", "delta/2", 0.0, "eps* > 0", "all RS codes"),
    ("Johnson J(delta)", "J(delta)", 1.0, "eps* = 0", "all RS codes"),
    ("at/beyond Johnson", ">= J(delta)", 1.99, "eps* -> 0", "some RS codes"),
    ("delta - Omega_tau(1)", "delta-Om(1)", float("inf"), "eps* -> 0", "some RS codes"),
]


def ceiling(E, nu, a, log2C=0.0, g=0.0):
    return E - a * nu - log2C + g


def udr_yield(rho):
    """Per-query bits at the unique-decoding radius: -log2((1+rho)/2)."""
    return -math.log2((1 + rho) / 2.0)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE STAIRCASE: `a` IS A FUNCTION OF THE RADIUS")
    print(f"  {'radius':<16} {'exceptions':<16} {'a':>6}  {'proximity loss':<12} scope")
    print("  " + "-" * 78)
    rows = [("delta/2 (UDR)", "O_{eps*}(1)", "0", "eps* > 0", "ALL RS codes"),
            ("J(delta)", "O(n)", "1", "eps* = 0", "ALL RS codes"),
            (">= J(delta)", "Omega(n^1.99)", ">=1.99", "eps* -> 0", "some RS codes"),
            ("delta - Om_t(1)", "n^tau", "tau", "eps* -> 0", "some RS codes")]
    for r in rows:
        print(f"  {r[0]:<16} {r[1]:<16} {r[2]:>6}  {r[3]:<12} {r[4]}")
    print("""
  The repo's table said "code proximity: a >= 1" flat. That is wrong at the
  bottom step (a = 0 is proved at UDR) and wrong at the top (a is unbounded
  above Johnson, not merely >= 1).""")

    sec("2. WHAT a = 0 AT THE UNIQUE-DECODING RADIUS IS WORTH")
    print("  soundcalc implements the OLD UDR bound, (gamma*n+1)/|F|, i.e. a = 1.\n")
    print(f"  {'system':<15} {'E':>5} {'nu':>4} {'a=1 ceiling':>12} "
          f"{'a=0 ceiling':>12} {'gain':>7} {'query term':>11} {'binds?':>8}")
    print("  " + "-" * 80)
    UDR_SYS = [("SP1 6.1.0", 124, 2, 21, 124, 16, 100),
               ("OpenVM 1.5.0", 124, 1, 23, 193, 20, 100)]
    for nm, E, R, T, s, g, rep in UDR_SYS:
        nu = T + R
        rho = 2.0 ** -R
        c1 = ceiling(E, nu, 1.0, math.log2((1 - rho) / 2))
        c0 = ceiling(E, nu, 0.0, 0.0)
        q = s * udr_yield(rho) + g
        binds = "query" if q < c1 else "commit"
        print(f"  {nm:<15} {E:>5} {nu:>4} {c1:>12.1f} {c0:>12.1f} "
              f"{c0-c1:>7.1f} {q:>11.1f} {binds:>8}")
    print("""
  The ceiling rises by about nu bits -- but for both deployed UDR systems the
  QUERY phase binds first, at ~100 bits. So a = 0 at UDR does not shrink proofs
  at today's targets; it raises the reachable maximum. It matters for a system
  that wants more than ~102 bits, or one that is commit-bound.

  It is also not free: the O_{eps*}(1) constant depends on the proximity loss
  eps*, and a positive eps* shrinks the radius, costing query-phase yield. The
  abstract does not give the dependence, so the trade cannot be priced here.""")

    sec("3. WHAT THIS DOES TO THE CLAIMED a = 0 PRIZE ABOVE JOHNSON")
    print("""
  ceiling_anatomy.py calls a = 0 above Johnson "the single largest unclaimed
  win in this whole repository", worth ~nu bits, conditional on Q2. Three
  corrections stack up:

  (a) a = 0 is ALREADY unconditional at the unique-decoding radius. The prize is
      not a = 0; it is a = 0 at a LARGER radius, which buys query-phase yield on
      top of the ceiling.

  (b) BCHKS25 result 3 proves some RS codes need Omega(n^1.99) exceptions at or
      beyond Johnson. An unqualified O(1) bound there would contradict it.

  (c) BCHKS25 result 5: "improved bounds on the list-decoding radius of
      Reed-Solomon codes is a prerequisite for any new proximity gaps results
      beyond the Johnson radius." So the 2026/861 route implies progress on RS
      list decoding -- a much stronger claim than its abstract advertises.

  Iteration 31 graded that paper down on provenance. Iteration 32 said nothing
  known forbade it. This is the accurate statement: something known constrains
  it sharply, and any correct version of it must thread between published
  counterexamples.""")

    sec("4. WHERE THE DEPLOYED SYSTEMS SIT ON THE STAIRCASE")
    print(f"  {'system':<15} {'regime':>7} {'step':>18} {'a in force':>11}")
    print("  " + "-" * 56)
    SYS = [("SP1 6.1.0", "UDR"), ("OpenVM 1.5.0", "UDR"), ("Airbender", "JBR"),
           ("Pico", "JBR"), ("ZisK 0.16.1", "JBR"), ("RISC Zero", "JBR"),
           ("Miden", "JBR")]
    for nm, reg in SYS:
        step = "delta/2" if reg == "UDR" else "J(delta)"
        a_now = "1 (soundcalc)" if reg == "UDR" else "1"
        print(f"  {nm:<15} {reg:>7} {step:>18} {a_now:>11}")
    print("""
  Every deployed system sits at or below the Johnson radius, where BCHKS25's
  POSITIVE results apply and the negative ones do not. The n^1.99 and n^tau
  counterexamples live at or beyond Johnson, for adversarially chosen code
  families. Nothing here threatens a deployed parameter set -- the same
  conclusion this repo reached about the capacity disproof, for the same reason.""")


if __name__ == "__main__":
    report()
