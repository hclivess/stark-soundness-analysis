"""
Theorem 4 needed the same correction Part III applied to Theorems 3', 5 and 6 --
and III.3 explicitly exempted it. The exemption was wrong.

WHAT PART III ALREADY DID (checked first, so this does not re-discover it)
---------------------------------------------------------------------------
Before writing anything, I checked what Part III had already audited, because
this iteration's first draft was about to re-derive a result the repo already
held. It does:

  III.2  applies the deployed `m >= 3` convention to Theorems 3' and 5, and
         collapses Theorem 5's dichotomy: under m >= 3 both regimes prefer the
         smallest blowup, and "the opposition in Part II was an artifact of
         letting m reach m_min in regime J".
  III.3  recomputes Theorem 6 under BCHKS25 and finds its +19..+22 bit margin
         shrinks to +5.7..+8.7, because "BCHKS25 already gives the Johnson
         regime the O(n) commit term".

Both are correct and neither is re-derived here. One refinement is added below
(the margin does not merely shrink -- at the theoretical supremum it REVERSES).

THE EXEMPTION THAT WAS WRONG
-----------------------------
III.3 ends: "it still costs kappa(R) in queries (Theorem 4, unaffected)."

Theorem 4 is not unaffected. Its query multiplier is

    kappa(R) := yield_J(R) / yield_T(R)

and Part II's definition block states plainly `yield_J(R) = R/2  (sup over m)`.
That supremum is attained only as m -> m_min -- exactly the condition III.2 says
deployment does not meet. So Theorem 4 rests on the same unavailable limit that
III.2 removed from Theorems 3' and 5, and III.3 exempted it anyway.

Recomputed at the deployed m = 3, where yield_J = -log2(sqrt(rho)(1 + 1/2m)):

    blowup      2      4      8     16     32     64
    Thm 4    1.205  1.475  1.807  2.192  2.616  3.069
    m = 3    0.669  1.147  1.539  1.948  2.383  2.841

Theorem 4 overstates the query penalty by 0.23 to 0.54 throughout.

AND THE SIGN FLIPS
------------------
At blowup 2 the deployed multiplier is 0.669 -- BELOW ONE. Threshold halving
does not cost queries there; it SAVES them. The crossover is at blowup 3.12 for
m = 3, and it moves with m:

    m = 3   -> kappa = 1 at blowup 3.12
    m = 5   -> 2.43
    m = 10  -> 1.88
    m = 20  -> 1.56

Theorem 4's stated reading -- "the cost of going unconditional above Johnson
*vanishes* as the blowup approaches 1" -- is right in direction and wrong at the
boundary. Under the deployed convention the cost does not vanish asymptotically;
it becomes negative below blowup ~3.

WHAT THAT DOES TO III.3's CONCLUSION
-------------------------------------
III.3 concluded "the case for adopting it is materially weaker than Part II
concluded". At deployed m and low blowup the opposite holds: III.3's own table
leaves threshold halving +5.7 bits of ceiling at blowup 2, and the corrected
kappa says it also needs ~33% FEWER queries there. On both axes at once.

That conclusion is conditional on eprint 2026/858 being correct, which iteration
31 graded tier 3 -- unreviewed, one group, PDF unreachable. Nothing here raises
that grade. It says only that IF the bound holds, the deployed-parameter case
for it is stronger than the repo last concluded, not weaker.

REFINEMENT TO III.3
-------------------
III.3 reports Theorem 6's margin at m >= 3 only. At the theoretical supremum
m -> m_min the margin does not shrink -- it reverses: the BCHKS25 Johnson ceiling
EXCEEDS threshold halving's by 1.9 to 2.3 bits at blowup 4 and above. So the two
regimes' ranking depends on which m is available, which is the same hinge III.2
identified for the blowup question.
"""

import math


def yield_J_sup(R):
    """Part II's yield_J: R/2, the supremum over m (needs m -> m_min)."""
    return R / 2.0


def yield_J_at_m(R, m):
    """Achievable Johnson yield at a given proximity parameter."""
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("nan")


def yield_T(R):
    """Threshold halving: 1 - log2(1 + 2^-R), the unique-decoding yield."""
    return 1 - math.log2(1 + 2.0 ** -R)


def kappa(R, m=None):
    """Query multiplier for J -> T. m=None uses Part II's supremum."""
    yj = yield_J_sup(R) if m is None else yield_J_at_m(R, m)
    return yj / yield_T(R)


def kappa_crossover(m, lo=0.05, hi=10.0):
    """Blowup exponent at which kappa = 1; below it, T needs fewer queries."""
    if yield_J_at_m(lo, m) - yield_T(lo) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if yield_J_at_m(mid, m) - yield_T(mid) < 0:
            lo = mid
        else:
            hi = mid
    return hi


def ceiling_J_bchks(R, T_len, E, m):
    rho = 2.0 ** -R
    sr = math.sqrt(rho)
    mm = m + 0.5
    gam = 1 - sr * (1 + 0.5 / m)
    if gam <= 0:
        return float("-inf")
    n = 2.0 ** (T_len + R)
    return E - math.log2((2 * mm ** 5 + 3 * mm * gam * rho) * n / (3 * rho * sr)
                         + mm / sr)


def ceiling_J_sup(R, T_len, E):
    """m -> m_min supremum, from Theorem 8's closed form."""
    u = 2 ** (R / 2.0)
    if u <= 1:
        return float("-inf")
    return (E - T_len) + (-5 * R + 5 * math.log2(u - 1) + 4 + math.log2(3))


def ceiling_T(R, T_len, E, rounds=20):
    return E - T_len - R - math.log2(rounds)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THEOREM 4's kappa USES A SUPREMUM DEPLOYMENT CANNOT REACH")
    print(f"  {'blowup':>7} {'yield_J sup':>12} {'yield_J m=3':>12} {'yield_T':>9} "
          f"{'kappa Thm4':>11} {'kappa m=3':>10} {'overstated':>11}")
    print("  " + "-" * 78)
    for R in (1, 2, 3, 4, 5, 6):
        k1, k3 = kappa(R), kappa(R, 3.0)
        print(f"  {2**R:>7} {yield_J_sup(R):>12.3f} {yield_J_at_m(R,3.0):>12.3f} "
              f"{yield_T(R):>9.3f} {k1:>11.3f} {k3:>10.3f} {k1-k3:>+11.3f}")
    print("""
  III.2 removed the m -> m_min supremum from Theorems 3' and 5 as unavailable in
  deployment. Theorem 4 uses the same supremum, and III.3 exempted it: "it still
  costs kappa(R) in queries (Theorem 4, unaffected)". It is affected.""")

    sec("2. AND BELOW BLOWUP ~3 THE PENALTY IS NEGATIVE")
    print(f"  {'m':>6} {'kappa = 1 at blowup':>22} {'reading':>34}")
    print("  " + "-" * 66)
    for m in (3.0, 5.0, 10.0, 20.0):
        c = kappa_crossover(m)
        print(f"  {m:>6.0f} {2**c:>22.3f} {'below this, T needs FEWER queries':>34}")
    print(f"""
  At blowup 2 with m = 3, kappa = {kappa(1,3.0):.3f}: threshold halving needs about
  {(1-kappa(1,3.0))*100:.0f}% FEWER queries than the Johnson regime, not more. Theorem 4's
  reading -- "the cost vanishes as the blowup approaches 1" -- is right in
  direction and wrong at the boundary: under the deployed convention it does not
  vanish, it changes sign.""")

    sec("3. WHAT THAT DOES TO III.3's CONCLUSION")
    E, T_len = 124, 20
    print(f"  {'blowup':>7} {'ceil_J m=3':>12} {'ceil_T':>9} {'T - J':>8} "
          f"{'kappa m=3':>10} {'T better on':>14}")
    print("  " + "-" * 66)
    for R in (1, 2, 3, 4):
        cJ, cT = ceiling_J_bchks(R, T_len, E, 3.0), ceiling_T(R, T_len, E)
        k = kappa(R, 3.0)
        both = ("both axes" if (cT > cJ and k < 1)
                else "ceiling only" if cT > cJ else "neither")
        print(f"  {2**R:>7} {cJ:>12.2f} {cT:>9.2f} {cT-cJ:>+8.2f} {k:>10.3f} "
              f"{both:>14}")
    print("""
  III.3 concluded "the case for adopting it is materially weaker than Part II
  concluded". At blowup 2 with deployed m the opposite holds: higher ceiling AND
  fewer queries. Conditional, of course, on eprint 2026/858 being correct --
  iteration 31 graded it tier 3 and nothing here raises that grade.""")

    sec("4. REFINEMENT TO III.3: AT THE SUPREMUM THE MARGIN REVERSES")
    print(f"  {'blowup':>7} {'ceil_J sup':>12} {'ceil_J m=3':>12} {'ceil_T':>9} "
          f"{'T-J sup':>9} {'T-J m=3':>9}")
    print("  " + "-" * 64)
    for R in (1, 2, 3, 4, 5):
        cs, c3 = ceiling_J_sup(R, T_len, E), ceiling_J_bchks(R, T_len, E, 3.0)
        cT = ceiling_T(R, T_len, E)
        print(f"  {2**R:>7} {cs:>12.2f} {c3:>12.2f} {cT:>9.2f} {cT-cs:>+9.2f} "
              f"{cT-c3:>+9.2f}")
    print("""
  III.3 reports the m >= 3 column only. At the supremum the margin does not
  shrink from +19..+22 to +5.7..+8.7 -- it goes NEGATIVE at blowup 4 and above,
  where the BCHKS25 Johnson ceiling beats threshold halving outright. Which
  regime wins on ceiling depends on which m is available, the same hinge III.2
  identified for the blowup question.""")


if __name__ == "__main__":
    report()
