"""
The m -> m_min vs m >= 3 hinge is not a convention. It is the query budget.

*** CORRECTED IN ITERATION 39 -- READ BEFORE THE NUMBERS BELOW ***
Finding 2 below reports that the m >= 3 floor "binds for exactly one deployed
system, SP1, costing it 3.46 bits". That is wrong, and the error is a scope one:
m is the JOHNSON-regime proximity parameter, and SP1 is reported in UDR, whose
bound (gamma*n + 1)/|F| contains no m at all. The 3.46 bits was computed by
applying the JBR model to a system that does not use it.

Restricted to the five systems that actually operate in the Johnson regime
(Airbender, Pico, ZisK, RISC Zero, Miden), every m* lies between 47 and 846, so:

    the m >= 3 floor costs ZERO bits to every deployed system.

The residual finding is a margin rather than a cost: the floor would begin to
bind at 2x to 3x each system's deployed query count. See section 4, added in
iteration 39, for the corrected table.

Finding 1 (m*(s) monotone decreasing, converging to m_min) is unaffected -- it is
a property of the JBR objective, not of any system's regime. Finding 3's
conclusion survives and strengthens, but its "more than two orders of magnitude"
span used SP1's 1.666; across the five actual JBR systems the span is 47 to 846,
about 18x.

Five results in THEOREM.md now flip on which value of the proximity parameter
you assume -- Theorem 3' (blowup 4), Theorem 4 (the query multiplier kappa),
Theorem 5 (opposite blowup preferences), Theorem 6 (threshold halving's margin)
and Theorem 8. Part II evaluates at the supremum m -> m_min; Part III.2 replaces
that with the deployed floor m >= 3 and calls Plonky3's floor "a conservative
choice, not a theorem".

Neither is a convention, and neither describes deployment. Theorem 2 already
says why, in a clause the repo never followed up:

    "The supremum is not attained: it is approached as m -> m_min AND s -> oo."

The two limits are tied. As m falls toward m_min the per-query yield
-log2(sqrt(rho)(1 + 1/2m)) falls to ZERO, so reaching the m_min ceiling needs an
unbounded query budget. At any finite s there is a unique interior optimum
m*(s), and that -- not m_min, not 3 -- is what a deployed system runs at.

FINDING 1 -- m*(s) IS MONOTONE DECREASING AND CONVERGES TO m_min
------------------------------------------------------------------
Computed by maximising min(s*y(m) + g, K(m)) over m, at SP1's parameters:

    s        50     100     124     200     400    1000    4000   20000
    m*    95.86    2.582   1.666   0.967   0.679   0.563   0.515   0.503

with m_min = 0.500. So Part II's supremum is the s -> oo limit, reached to three
decimal places only past s ~ 20000 -- two orders of magnitude beyond any
deployed query count. Theorem 2's "not attained" is quantitative, and this is
the quantity.

FINDING 2 -- THE m >= 3 FLOOR BINDS FOR EXACTLY ONE DEPLOYED SYSTEM
---------------------------------------------------------------------
Maximising with m free versus m >= 3, across the seven verified zkVMs:

    system      s     m* free   floor costs
    SP1       124       1.666      3.46 bits
    OpenVM    193       4.541      0
    Airbender  87      47.327      0
    Pico       84     349.376      0
    ZisK      229     231.629      0
    RISC Zero  50     846.014      0
    Miden      27     639.456      0

Only SP1's optimum lies below 3, and the floor costs it 3.46 bits. For the other
six the unconstrained optimum is 4.5 to 846 -- so far above the floor that it is
not a constraint at all.

FINDING 3 -- SO NEITHER OF THE REPO'S TWO CONVENTIONS DESCRIBES DEPLOYMENT
----------------------------------------------------------------------------
Part II evaluates at m_min: that is the s -> oo limit, and no deployed system is
within two orders of magnitude of it.

Part III evaluates at m = 3: that is a floor which binds once in seven, and for
the other six the operative m is one to three orders of magnitude ABOVE it.

The honest framing is that m is not a convention to be chosen but a function of
the query budget, and the seven deployed systems span m* from 1.7 to 846. Any
statement of the form "at m >= 3, regime X beats regime Y" is a statement about
a point most of the fleet is nowhere near.

WHAT THIS DOES NOT OVERTURN
---------------------------
III.2's specific conclusion -- that Theorem 3's blowup-4 optimum requires
m -> m_min and is unavailable under a floor -- stands, because it is a statement
about the CEILING K(m), which is monotone decreasing in m, so its maximum over
any admissible set is at the smallest available m. Likewise III.3's ceiling
comparison at m = 3 is the right comparison for "which bound permits the higher
ceiling".

What changes is the reading of the TOTAL. Ceilings are maximised at small m;
totals are maximised at m*(s); and for six of seven deployed systems those are
very different places.
"""

import math


def y_of(R, m):
    """Per-query yield at proximity parameter m."""
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else -1.0


def m_min(R):
    """Admissibility threshold (Lemma 1): alpha(m) < 1."""
    u = 2 ** (R / 2.0)
    return 1.0 / (2 * (u - 1))


def best_m(R, nu, E, s, g, lo=None, hi=1000.0, steps=6000):
    """argmax over m of the total min(s*y + g, K(m)). Returns (m*, total)."""
    from regime_crossover import commit_jbr
    lo = lo if lo is not None else m_min(R) * 1.0000001
    best = (-1e18, None)
    ratio = (hi / lo) ** (1.0 / steps)
    m = lo
    for _ in range(steps + 1):
        yy = y_of(R, m)
        if yy > 0:
            v = min(s * yy + g, commit_jbr(R, nu, E, m))
            if v > best[0]:
                best = (v, m)
        m *= ratio
    return best[1], best[0]


ZKVMS = [("SP1 6.1.0", 124, 2, 21, 124, 16),
         ("OpenVM 1.5.0", 124, 1, 23, 193, 20),
         ("Airbender", 124, 1, 24, 87, 28),
         ("Pico", 124, 1, 22, 84, 16),
         ("ZisK 0.16.1", 192, 1, 21, 229, 16),
         ("RISC Zero", 124, 2, 21, 50, 0),
         ("Miden", 128, 3, 18, 27, 16)]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. m*(s) IS MONOTONE DECREASING AND CONVERGES TO m_min")
    print(f"  SP1 parameters: R=2, nu=23, E=124, g=16, m_min = {m_min(2):.3f}\n")
    print(f"  {'s':>8} {'m*(s)':>10} {'total':>9} {'m* / m_min':>12}")
    print("  " + "-" * 44)
    prev = None
    mono = True
    for s in (50, 100, 124, 200, 400, 1000, 4000, 20000):
        m, v = best_m(2, 23, 124, s, 16)
        if prev is not None and m > prev + 1e-9:
            mono = False
        prev = m
        print(f"  {s:>8} {m:>10.3f} {v:>9.1f} {m/m_min(2):>12.3f}")
    print(f"""
  Monotone decreasing: {mono}. Theorem 2 says the supremum "is approached as
  m -> m_min AND s -> oo" -- the two limits are tied, because the yield
  -log2(sqrt(rho)(1+1/2m)) vanishes as m -> m_min, so an unbounded query budget
  is exactly what reaching that ceiling costs. Part II's supremum is reached to
  three decimals only past s ~ 20000.""")

    sec("2. THE m >= 3 FLOOR BINDS FOR EXACTLY ONE DEPLOYED SYSTEM")
    print(f"  {'system':<15} {'s':>5} {'m_min':>8} {'m* free':>10} {'total':>8} "
          f"{'m* >= 3':>9} {'total':>8} {'floor costs':>12}")
    print("  " + "-" * 82)
    binds = []
    for nm, E, R, T, s, g in ZKVMS:
        nu = T + R
        mf, vf = best_m(R, nu, E, s, g)
        m3, v3 = best_m(R, nu, E, s, g, lo=3.0)
        cost = vf - v3
        if cost > 0.01:
            binds.append((nm, cost))
        print(f"  {nm:<15} {s:>5} {m_min(R):>8.3f} {mf:>10.3f} {vf:>8.1f} "
              f"{m3:>9.3f} {v3:>8.1f} {cost:>+12.2f}")
    print(f"""
  Binding for {len(binds)} of 7: {', '.join(f'{n} ({c:.2f} bits)' for n, c in binds)}.
  For the other six the unconstrained optimum is 4.5 to 846 -- one to three
  orders of magnitude above the floor, so it is not a constraint at all.""")

    sec("3. NEITHER CONVENTION DESCRIBES DEPLOYMENT")
    print(f"  {'system':<15} {'m_min (Part II)':>16} {'3 (Part III)':>14} "
          f"{'m*(s) (actual)':>15} {'ratio to 3':>12}")
    print("  " + "-" * 76)
    for nm, E, R, T, s, g in ZKVMS:
        nu = T + R
        mf, _ = best_m(R, nu, E, s, g)
        print(f"  {nm:<15} {m_min(R):>16.3f} {3.0:>14.1f} {mf:>15.3f} "
              f"{mf/3.0:>12.2f}x")
    print("""
  Part II's m_min is the s -> oo limit; Part III's 3 is a floor that binds once.
  The fleet spans m* from 1.7 to 846. Any claim of the form "at m >= 3, regime X
  beats regime Y" describes a point most deployed systems are nowhere near.

  This does NOT overturn III.2 or III.3, which are statements about the CEILING
  K(m) -- monotone decreasing in m, hence maximised at the smallest available m,
  so evaluating at the floor is correct for them. It changes the reading of the
  TOTAL: ceilings are maximised at small m, totals at m*(s), and for six of the
  seven those are very different places.""")


JBR_ONLY = [("Airbender", 124, 1, 24, 87, 28),
            ("Pico", 124, 1, 22, 84, 16),
            ("ZisK 0.16.1", 192, 1, 21, 229, 16),
            ("RISC Zero", 124, 2, 21, 50, 0),
            ("Miden", 128, 3, 18, 27, 16)]

UDR_ONLY = [("SP1 6.1.0", 124, 2, 21, 124, 16),
            ("OpenVM 1.5.0", 124, 1, 23, 193, 20)]


def s_where_m_star_hits(target, R, nu, E, g, hi=200000):
    """Query count at which m*(s) falls to `target`. Bisection on s."""
    lo = 1
    for _ in range(60):
        mid = (lo + hi) // 2
        if best_m(R, nu, E, mid, g, steps=1200)[0] > target:
            lo = mid
        else:
            hi = mid
    return hi


def report_regimes():
    """Iteration 39: the floor question, restricted to the right regime."""
    sec("4. CORRECTED: THE FLOOR COSTS NOTHING TO ANY DEPLOYED SYSTEM")
    print("  m is the JOHNSON-regime proximity parameter. The UDR bound")
    print("  (gamma*n + 1)/|F| has no m, so it cannot bind a UDR-reported system.\n")
    print(f"  {'system':<15} {'regime':>7} {'s':>5} {'m* free':>10} "
          f"{'floor binds?':>13} {'cost':>7}")
    print("  " + "-" * 62)
    total = 0.0
    for nm, E, R, T, s, g in JBR_ONLY:
        nu = T + R
        mf, vf = best_m(R, nu, E, s, g)
        _, v3 = best_m(R, nu, E, s, g, lo=3.0)
        total += max(0.0, vf - v3)
        print(f"  {nm:<15} {'JBR':>7} {s:>5} {mf:>10.2f} "
              f"{'YES' if mf < 3 else 'no':>13} {vf-v3:>7.2f}")
    for nm, E, R, T, s, g in UDR_ONLY:
        print(f"  {nm:<15} {'UDR':>7} {s:>5} {'n/a':>10} "
              f"{'n/a -- no m':>13} {'0.00':>7}")
    print(f"""
  Total cost across every deployed system: {total:.2f} bits. Iteration 38's
  "3.46 bits to SP1" applied the JBR model to a UDR-reported system.""")

    sec("5. THE RESIDUAL: HOW MUCH HEADROOM BEFORE THE FLOOR WOULD BIND")
    print(f"  {'system':<15} {'deployed s':>11} {'s where m* = 3':>15} "
          f"{'headroom':>10}")
    print("  " + "-" * 56)
    for nm, E, R, T, s, g in JBR_ONLY:
        thr = s_where_m_star_hits(3.0, R, T + R, E, g)
        print(f"  {nm:<15} {s:>11} {thr:>15} {thr/s:>9.1f}x")
    print("""
  Every Johnson-regime system sits a factor of 2 to 3 below the query count at
  which Plonky3's floor would start costing it bits. That is a real margin and a
  concrete prediction: a JBR system that doubled or tripled its queries would
  begin paying for a floor that is, as III.2 says, a conservative choice rather
  than a theorem.""")


if __name__ == "__main__":
    report()
    report_regimes()
