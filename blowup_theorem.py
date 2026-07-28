"""
Theorem 8: why blowup 4 survived the bound update -- and where it does not hold.

THE QUESTION NOBODY ASKED
-------------------------
THEOREM.md Theorem 3' proves that blowup 4 uniquely maximises the provable-
soundness ceiling, and notes that RISC Zero and Plonky3/BabyBear "sit exactly at
the Johnson-regime optimum". That proof runs on BCIKS20:

    Lambda = (E - 2T) + g(R),   g(R) = -7R + 7*log2(2^{R/2} - 1) + log2(3) + 7

Part III.1 then records that BCIKS20 is superseded by BCHKS25 and says plainly:
"Theorem 2's closed form is now a closed form for a superseded bound." It does
NOT ask whether Theorem 3's conclusion -- R* = 2 -- survives. Three parts and
twenty-odd iterations later, nobody had checked. The headline "blowup 4 is
optimal" has been resting on a bound the repo itself retired.

It survives. And the reason is not luck in the arithmetic.

THEOREM 8 (the condition for blowup 4)
---------------------------------------
Let a commit-phase bound have the shape

    eps * |F|  =  const * (m + 1/2)^c * n^a / rho^b

covering BCIKS20 (a=2, c=7, b=3/2) and BCHKS25 (a=1, c=5, b=3/2). Deployment
forces nu = T + R, and the ceiling is approached as m -> m_min, where Lemma 2
gives log2(m_min + 1/2) = R/2 - 1 - log2(2^{R/2} - 1). Substituting:

    Lambda(R) = (E - a*T) - A*R + c*log2(2^{R/2} - 1) + const,
                A := a + c/2 + b

Writing u = 2^{R/2}, Lambda'(R) = -A + (c/2)*u/(u-1), which vanishes at
u = 2A/(2A - c). Hence the unique maximiser is

    R* = 2*log2( 2A / (2A - c) ),

and in particular

    R* = 2  (blowup 4)   <==>   A = c   <==>   c = 2(a + b).

  BCIKS20:  c = 7,  2(a+b) = 2(2 + 3/2) = 7   OK
  BCHKS25:  c = 5,  2(a+b) = 2(1 + 3/2) = 5   OK

Both bounds sit exactly on the line c = 2(a+b). The 2020 -> 2025 improvement
moved a from 2 to 1 and c from 7 to 5 -- two independent-looking changes that
happen to travel along that line together, which is precisely why the optimum
did not move. Theorem 3' survived its own foundation being replaced.

Verified numerically against the FULL non-asymptotic BCHKS25 expression (not the
m -> m_min asymptotic): sweeping R continuously at E=124, T=20 puts the argmax at
R = 2.0000.

WHERE IT DOES NOT HOLD
----------------------
Theorem 8 is a statement about bounds of the shape above -- ones with a
proximity parameter m to optimise. The unique-decoding bound has none:

    eps * |F|  =  gamma * n + 1,     gamma = (1 - rho)/2

There is no m, so c = 0 and the trade-off Theorem 8 balances does not exist.
With nu = T + R,

    Lambda(R) = (E - T) - R - log2(1 - 2^{-R}) + 1

whose derivative is -1 - 2^{-R}/(1 - 2^{-R}) < 0 for all R > 0: strictly
decreasing. The ceiling-optimal blowup in the UDR regime is as SMALL as
possible, not 4. Numerically the argmax sits at the bottom of any sweep range.

And under BCHKS25 result 1 (a = 0 at the unique-decoding radius, iteration 33)
the ceiling loses its nu-dependence entirely, so it is independent of R and the
blowup is irrelevant to the ceiling.

SO THE CORRECTED STATEMENT
--------------------------
"Blowup 4 maximises the provable-soundness ceiling" is a JOHNSON-REGIME result.
It holds for BCIKS20 and BCHKS25 because both satisfy c = 2(a+b), and it fails
in the unique-decoding regime, where the ceiling prefers minimal blowup or does
not depend on blowup at all. THEOREM.md states Theorem 3' without that scope.

This does not change any deployed recommendation: the five JBR systems sit in
the regime where blowup 4 is optimal, and the two UDR systems (SP1 at blowup 4,
OpenVM at blowup 2) are query-bound rather than ceiling-bound, so the
ceiling-optimal blowup is not what selected their parameters anyway.
"""

import math


def A_of(a, c, b=1.5):
    """The coefficient on R in Lambda(R) = ... - A*R + c*log2(2^{R/2}-1)."""
    return a + c / 2.0 + b


def r_star(a, c, b=1.5):
    """Unique ceiling-maximising blowup exponent, R* = 2 log2(2A/(2A-c))."""
    A = A_of(a, c, b)
    if c <= 0 or 2 * A - c <= 0:
        return None
    u = 2 * A / (2 * A - c)
    return 2 * math.log2(u) if u > 1 else None


def blowup4_condition(a, b=1.5):
    """R* = 2 exactly when c = 2(a+b)."""
    return 2 * (a + b)


def m_min(R):
    u = 2 ** (R / 2.0)
    return 1.0 / (2 * (u - 1)) if u > 1 else float("inf")


def ceiling_bchks_full(R, T, E, slack=1e-9):
    """The full BCHKS25 expression, m -> m_min, nu = T + R."""
    m = m_min(R) * (1 + slack) + slack
    rho = 2.0 ** -R
    sr = math.sqrt(rho)
    mm = m + 0.5
    gam = 1 - sr * (1 + 0.5 / m)
    n = 2.0 ** (T + R)
    val = (2 * mm ** 5 + 3 * mm * gam * rho) * n / (3 * rho * sr) + mm / sr
    return E - math.log2(val)


def ceiling_udr_full(R, T, E):
    """The UDR bound (gamma*n + 1)/|F|, nu = T + R. No proximity parameter."""
    rho = 2.0 ** -R
    return E - math.log2(((1 - rho) / 2.0) * 2.0 ** (T + R) + 1)


def argmax_R(fn, lo=0.05, hi=8.0, step=0.001, *args):
    best = (-1e18, None)
    R = lo
    while R < hi:
        v = fn(R, *args)
        if v > best[0]:
            best = (v, R)
        R += step
    return best[1], best[0]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THEOREM 8: R* = 2 log2(2A/(2A-c)),  A = a + c/2 + b")
    print(f"  {'bound':<26} {'a':>3} {'c':>3} {'b':>5} {'A':>6} {'R*':>8} "
          f"{'blowup':>8} {'c = 2(a+b)?':>13}")
    print("  " + "-" * 80)
    for nm, a, c, b in (("BCIKS20 (2020)", 2, 7, 1.5),
                        ("BCHKS25 Johnson (2025)", 1, 5, 1.5),
                        ("hypothetical a=1, c=4", 1, 4, 1.5),
                        ("hypothetical a=1, c=6", 1, 6, 1.5),
                        ("hypothetical a=0, c=3", 0, 3, 1.5)):
        r = r_star(a, c, b)
        need = blowup4_condition(a, b)
        print(f"  {nm:<26} {a:>3} {c:>3} {b:>5.1f} {A_of(a,c,b):>6.1f} "
              f"{r:>8.4f} {2**r:>8.3f} {'yes' if abs(c-need)<1e-9 else 'no (%g)' % need:>13}")
    print("""
  Both deployed-relevant bounds sit exactly on c = 2(a+b). The 2020 -> 2025
  improvement moved a: 2 -> 1 and c: 7 -> 5 together along that line, which is
  why Theorem 3's optimum did not move when its foundation was replaced.""")

    sec("2. VERIFIED AGAINST THE FULL NON-ASYMPTOTIC BOUND")
    for T, E in ((20, 124), (22, 124), (20, 192)):
        R, v = argmax_R(ceiling_bchks_full, 0.05, 8.0, 0.001, T, E)
        print(f"  T={T}, E={E}:  numeric argmax R* = {R:.4f} "
              f"(blowup {2**R:.4f}), ceiling {v:.2f}")
    print("""
  The asymptotic derivation assumes m -> m_min; the sweep above uses the full
  expression including the 3m'*gamma*rho and m'/sqrt(rho) terms. It lands on
  2.0000 regardless of trace length or field size, as Corollary 2.1's separation
  of variables predicts.""")

    sec("3. WHERE IT FAILS: THE UNIQUE-DECODING REGIME HAS NO m")
    print(f"  UDR bound is (gamma*n + 1)/|F| -- no proximity parameter, so c = 0\n")
    print(f"  {'R':>5} {'blowup':>8} {'Lambda - (E-T)':>16}")
    print("  " + "-" * 34)
    for R in (0.5, 1, 2, 3, 4, 5):
        print(f"  {R:>5.1f} {2**R:>8.2f} "
              f"{-R - math.log2(1 - 2.0**-R) + 1:>16.4f}")
    R, _ = argmax_R(ceiling_udr_full, 0.05, 8.0, 0.001, 20, 124)
    print(f"""
  Strictly decreasing: d/dR = -1 - 2^-R/(1 - 2^-R) < 0 for all R > 0. The sweep
  bottoms out at the low end of its range (R = {R:.2f}), i.e. the ceiling-optimal
  blowup under UDR is as small as possible -- not 4.

  And under BCHKS25 result 1 (a = 0 at the unique-decoding radius) the ceiling
  is E - log2(C), with no nu term at all, so it does not depend on blowup in
  either direction.""")

    sec("4. WHAT THIS CHANGES, AND WHAT IT DOES NOT")
    print("""
  THEOREM.md states Theorem 3' -- "blowup exactly 4" -- without scoping it to
  the Johnson regime. That scope is now explicit: it holds for bounds satisfying
  c = 2(a+b), which BCIKS20 and BCHKS25 both do, and fails where there is no
  proximity parameter to trade against the domain.

  No deployed recommendation changes. The five JBR systems sit in the regime
  where blowup 4 is optimal. The two UDR systems are QUERY-bound, not
  ceiling-bound (iteration 24), so the ceiling-optimal blowup was never what
  selected their parameters -- SP1 uses blowup 4 and OpenVM blowup 2, and
  neither choice is explained or contradicted by this theorem.""")


if __name__ == "__main__":
    report()
