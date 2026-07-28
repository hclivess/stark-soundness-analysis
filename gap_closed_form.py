"""
The a-floor gap in closed form -- and then the finding that none of it is
recoverable soundness, which corrects iteration 70 one iteration later.

Iteration 70 split the 39-45 bit headroom into a structural part
(nu + log2(fold) + 1, Proposition 9) that no theorem can close, and a "linear
slack" part it called the genuine target. This iteration closes the slack in
closed form too, and then shows the target is not one.

PROPOSITION 10 -- THE SLACK IS THE m-EXPONENT DIFFERENCE
----------------------------------------------------------
BCHKS25's two branches differ in how they carry m. Writing m' = m + 0.5:

    K_linear  dominant factor   2 m'^5 n / (3 rho sqrt(rho))
    K_n/q     factor            2 m'

so the linear branch pays m'^5 where the other pays m'^1. Subtracting, at
folding 2 and large n:

    slack = K_nq - K_linear = 4 log2(m + 0.5) + R - log2(3) - 1

Exact to 0.000 bits on all five Johnson-regime systems. The 4 is 5 - 1.

Combining with Proposition 9, the ENTIRE gap is closed-form:

    headroom = nu + log2(fold) + 4 log2(m + 0.5) + R - log2(3)

within 0.064 bits at every deployed system -- the residual being Proposition 9's
log2(1 + sqrt(rho)/(m+0.5)) correction. There is no unexplained component. A
quantity this repo has carried as an open empirical range since iteration 40 is
an identity in nu, R and m.

PROPOSITION 11 -- AND THE GAP IS SLACK IN A TERM THAT DOES NOT BIND
---------------------------------------------------------------------
The obvious next move is to ask what a sharper linear term would buy. Replacing
m'^5 by m'^k and re-optimising max_m min(query, commit):

    system       k=5 (today)     k=4      k=3      k=2
    Airbender          70.2    +0.8     +1.2     +1.3
    Pico               57.8    +0.1     +0.2     +0.2
    ZisK              129.8    +0.5     +0.7     +0.7
    RISC Zero          50.0    +0.0     +0.0     +0.0
    Miden              56.5    +0.0     +0.0     +0.0

Collapsing the exponent from 5 to 2 -- far beyond any plausible theorem -- is
worth at most 1.3 bits, and nothing at all for three of the five.

The reason is that the optimum sits exactly at the query/commit crossover, where
an increasing function meets a decreasing one. Improving the commit bound moves
the crossover to larger m, and the query yield SATURATES there:

    -log2( sqrt(rho) (1 + 1/2m) )  ->  -log2 sqrt(rho)  =  R/2

so the query term is capped at

    s * R / 2 + g                                          (Proposition 11)

    system       s    R   g     cap    achieved   shortfall
    Airbender   87    1  28    71.5        70.2        1.30
    Pico        84    1  16    58.0        57.8        0.20
    ZisK       229    1  16   130.5       129.8        0.70
    RISC Zero   50    2   0    50.0        50.0        0.00
    Miden       27    3  16    56.5        56.5        0.00

Every deployed system is already within 1.3 bits of a cap that no commit-side
theorem can lift.

WHAT THIS CORRECTS
--------------------
Iteration 70 concluded: "only the slack is a target for a better theorem, and it
is a third to a half of what the headline number suggests." The first clause is
wrong. The slack is slack in the COMMIT bound, and the commit bound is not the
binding term at any deployed parameter -- this repo's own finding 2 says the
query phase binds for all seven verified zkVMs. Slack in a non-binding term is
not recoverable soundness.

So the honest final reading of the 20.6-45.0 bits is: essentially none of it is
available. 23-27 bits are a category difference between two bounds on different
quantities (Prop 9), and the remaining 14-21 sit in a term that is 14-21 bits
away from mattering (Props 10 and 11).

WHAT IS ACTUALLY LEFT
-----------------------
Proposition 11 says the only levers on Johnson-regime soundness are s, R and g:
queries, rate and grinding. All three are proof-size levers, which is exactly
EFFICIENCY.md section 0's claim arrived at from the opposite direction -- it
argued query count governs proof size rather than prover time; this says query
count also governs the SOUNDNESS ceiling, because nothing on the commit side
can.

That is a sharper statement of what this repo has been circling: the commit-side
theory improvements it has tracked since iteration 1 (a: 2 -> 1, better
constants) are worth under 1.3 bits at deployed parameters. The 2020-to-today
gain of 52 -> 103 bits in ceiling_anatomy.py is real, but it is a gain in a
bound that does not bind.
"""

import math

from regime_crossover import gamma_jbr
from regimes import m_min
from soundcalc_lean import jbr_m

# (name, E, R, T, s, g)
SYSTEMS = [("Airbender", 124, 1, 24, 87, 28), ("Pico", 124, 1, 22, 84, 16),
           ("ZisK", 192, 1, 21, 229, 16), ("RISC Zero", 124, 2, 21, 50, 0),
           ("Miden", 128, 3, 18, 27, 16)]

EXPONENTS = (5, 4, 3, 2)      # 5 is BCHKS25's; the rest are counterfactual


def commit_linear(R, nu, E, m, k=5, folding=2):
    """BCHKS25's linear branch with the m-exponent made a parameter."""
    rho = 2.0 ** -R
    sq = math.sqrt(rho)
    mm = m + 0.5
    pp = gamma_jbr(R, m)
    if pp <= 0.0:
        return float("-inf")
    n = 2.0 ** nu
    return E - math.log2(max(((2 * mm ** k + 3 * mm * pp * rho) * n / (3 * rho * sq)
                              + mm / sq) * max(folding - 1.0, 1.0), 1.0))


def commit_nq(R, nu, E, m, folding=2):
    return (E - math.log2(folding) - math.log2(2.0 ** nu + 1.0)
            - math.log2(2.0 * m + 1.0) + 0.5 * math.log2(2.0 ** -R))


def query_term(R, s, g, m):
    a = math.sqrt(2.0 ** -R) * (1.0 + 0.5 / m)
    return s * (-math.log2(a)) + g if a < 1.0 else float("-inf")


def slack_closed_form(R, m):
    """PROPOSITION 10: 4 log2(m+0.5) + R - log2(3) - 1, at folding 2."""
    return 4.0 * math.log2(m + 0.5) + R - math.log2(3.0) - 1.0


def headroom_closed_form(R, nu, m, folding=2):
    """Props 9 + 10: the whole gap, nu + log2(fold) + 4log2(m+.5) + R - log2 3."""
    return (nu + math.log2(folding) + 4.0 * math.log2(m + 0.5)
            + R - math.log2(3.0))


def query_cap(R, s, g):
    """PROPOSITION 11: the query yield saturates at R/2, capping the term."""
    return s * R / 2.0 + g


def best_m(R, nu, E, s, g, k=5, steps=4000):
    """argmax_m min(query, linear commit), and the value attained."""
    lo, hi = m_min(R) * 1.0001, 5000.0
    best = (None, float("-inf"))
    for i in range(steps):
        m = lo * (hi / lo) ** (i / (steps - 1))
        v = min(query_term(R, s, g, m), commit_linear(R, nu, E, m, k))
        if v > best[1]:
            best = (m, v)
    return best


def exponent_table():
    """[(name, [(k, m*, value)])] -- what a sharper m-exponent would buy."""
    out = []
    for nm, E, R, T, s, g in SYSTEMS:
        out.append((nm, [(k,) + best_m(R, T + R, E, s, g, k) for k in EXPONENTS]))
    return out


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. PROPOSITION 10: THE SLACK IS THE m-EXPONENT DIFFERENCE, 5 - 1 = 4")
    print("""
  The two branches differ only in how they carry m' = m + 0.5:

      K_linear   dominant factor   2 m'^5 n / (3 rho sqrt(rho))
      K_n/q      factor            2 m'

  Subtracting, at folding 2 and large n:

      slack = 4 log2(m + 0.5) + R - log2(3) - 1\n""")
    print(f"  {'system':<11} {'R':>3} {'m':>5} {'measured':>10} {'closed form':>13} "
          f"{'diff':>7}")
    print("  " + "-" * 54)
    for nm, E, R, T, _s, _g in SYSTEMS:
        nu, m = T + R, float(jbr_m(2.0 ** -R, E))
        meas = commit_nq(R, nu, E, m) - commit_linear(R, nu, E, m)
        cf = slack_closed_form(R, m)
        print(f"  {nm:<11} {R:>3} {m:>5.0f} {meas:>10.3f} {cf:>13.3f} {meas-cf:>+7.3f}")
    print("\n  With Proposition 9 the WHOLE gap is closed-form:\n")
    print(f"  {'system':<11} {'nu':>4} {'headroom':>10} "
          f"{'nu+log2(f)+4log2(m+.5)+R-log2(3)':>34} {'diff':>7}")
    print("  " + "-" * 70)
    from headroom_split import mca_floor
    for nm, E, R, T, _s, _g in SYSTEMS:
        nu, m = T + R, float(jbr_m(2.0 ** -R, E))
        h = mca_floor(E, R, m) - commit_linear(R, nu, E, m)
        cf = headroom_closed_form(R, nu, m)
        print(f"  {nm:<11} {nu:>4} {h:>10.3f} {cf:>34.3f} {h-cf:>+7.3f}")
    print("""
  No unexplained component. A quantity this repo has carried as an open
  empirical range since iteration 40 is an identity in nu, R and m.""")

    sec("2. PROPOSITION 11: BUT IT IS SLACK IN A TERM THAT DOES NOT BIND")
    print("\n  Replacing m'^5 by m'^k and re-optimising max_m min(query, commit):\n")
    print(f"  {'system':<11} {'k=5 (today)':>14} {'k=4':>10} {'k=3':>10} {'k=2':>10}")
    print("  " + "-" * 60)
    for nm, rows in exponent_table():
        base = rows[0][2]
        cells = "".join(f"{v:>14.1f}" if i == 0 else f"{v-base:>+10.1f}"
                        for i, (_k, _m, v) in enumerate(rows))
        print(f"  {nm:<11}{cells}")
    print("""
  Collapsing the exponent from 5 to 2 -- far beyond any plausible theorem -- is
  worth at most 1.3 bits, and nothing for three of five.

  The optimum sits exactly at the query/commit crossover. Improving the commit
  bound moves it to larger m, where the query yield SATURATES:

      -log2( sqrt(rho)(1 + 1/2m) )  ->  R/2

  so the query term is capped at s*R/2 + g, whatever the commit side does:\n""")
    print(f"  {'system':<11} {'s':>5} {'R':>3} {'g':>4} {'cap':>8} {'achieved':>10} "
          f"{'shortfall':>11}")
    print("  " + "-" * 56)
    for nm, E, R, T, s, g in SYSTEMS:
        _m, v = best_m(R, T + R, E, s, g, 5)
        cap = query_cap(R, s, g)
        print(f"  {nm:<11} {s:>5} {R:>3} {g:>4} {cap:>8.1f} {v:>10.1f} "
              f"{cap-v:>11.2f}")

    sec("3. WHAT THIS CORRECTS, AND WHAT IS LEFT")
    print("""
  Iteration 70 concluded "only the slack is a target for a better theorem". The
  first clause is wrong. The slack is slack in the COMMIT bound, and the commit
  bound does not bind at any deployed parameter -- finding 2 of this repo says
  the query phase binds for all seven verified zkVMs. Slack in a non-binding
  term is not recoverable soundness.

  So the honest reading of 20.6-45.0 bits is that essentially none is available:
  23-27 bits are a category difference between bounds on different quantities
  (Prop 9), and the remaining 14-21 sit in a term that is itself 14-21 bits away
  from mattering (Props 10, 11).

  WHAT IS LEFT. Proposition 11 says the only levers are s, R and g -- queries,
  rate, grinding. All three are proof-size levers. EFFICIENCY.md section 0
  reached the neighbouring claim from the opposite direction, that query count
  governs proof size rather than prover time; this says query count also governs
  the SOUNDNESS ceiling, because nothing on the commit side can.

  The commit-side improvements this repo has tracked since iteration 1 --
  a: 2 -> 1, better constants, the 52 -> 103 bit gain in ceiling_anatomy.py --
  are real gains in a bound that does not bind, worth under 1.3 bits where it
  counts.""")


if __name__ == "__main__":
    report()
