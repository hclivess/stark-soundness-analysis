"""
All three routes to capacity, and why each one is closed at deployed parameters.

*** CORRECTED IN ITERATION 42 -- THE FIELD-SIZE OBJECTION WAS OVERSTATED ***
This file concludes that the unfolded routes need fields of 5,909 bits (random
linear) to 3,026,000 bits (random RS), and that every capacity route is
therefore closed. Those figures come from Goyal-Guruswami-Sun-Wootters Thms 5.3
and 5.6. But Yuan-Zhu (arXiv 2605.07595, syndrome-space approach) give much
better alphabet-size dependence for exactly these families -- and iteration 29
had already listed that paper in capacity_frs.py's source table. I used the
weaker bound anyway.

Yuan-Zhu Theorem 1.1.1, random LINEAR codes, large-alphabet setting:
    radius rho < 1 - R - eps  requires  q = Theta(n) and q >= (2/eps)^(1/eps)
Yuan-Zhu Theorem 6.6, random RS:  q >= n * 2^{O(eps^-3)}

At the break-even eps that beats the Johnson radius (see section 5, added in
iteration 42):

    route                 this file said        corrected
    random linear            5,909 bits          22 bits
    random RS            3,026,000 bits       86-135 bits

So the field-size objection collapses by two to five orders of magnitude, and
random linear codes at capacity are comfortably feasible. Section 4's verdict
"blocked by field size" is WRONG for both unfolded routes.

What survives is a DIFFERENT objection, which this file noted but did not model:
random linear codes are not Reed-Solomon, so FRI's x -> x^2 folding map does not
exist for them; and random-evaluation-point RS destroys the FFT structure that
makes a STARK prover O(n log n). Section 5 prices that. The corrected conclusion
is that the capacity routes are closed to FRI for STRUCTURAL reasons, not for
field-size reasons, and are genuinely open to Ligero/Brakedown/Blaze/Bolt-style
systems built on random linear codes.

Iteration 29 priced the folded-RS route and found it worth ~0% because the
theorem needs folding m >= c/eta^2, so each query returns m field elements. That
conclusion had an obvious hole: RANDOM-evaluation-point RS also achieves
capacity-radius gaps and is NOT folded -- one field element per symbol. If its
parameters were comparable, capacity would be a genuine ~2x proof-size win and
iteration 29's verdict would reverse.

It does not reverse. The folding is not an accident of the FRS proof; it is what
buys a polynomially-sized field. The unfolded routes pay for that in field size
instead, and they pay exponentially.

SOURCE
------
Goyal, Guruswami, Sun, Wootters, "Locality of Curve-Decoding and Improved
Proximity Gaps", arXiv:2607.08516v1 (2026-07-09). Fetched and read.

  bound (1.1), subspace-design/FRS [GG25]:   eps*q >= n*l/eta + O(l^2/eta^3)
  bound (1.3), this paper's improvement:     eps*q >= n*l(1-R)/eta + O(l^2/eta^3)

  Theorem 5.3 (random linear codes):
      "If q >= exp(Omega(l^2/eta^4)) and n >= Omega(l^4/eta^7), then with high
       probability ..."
  Theorem 5.6 (random Reed-Solomon codes):
      "If q >= n * exp(Omega(l^4/eta^7)) and n >= Omega(l^4/eta^7), then with
       high probability ..."

and from iteration 29, Jeronimo-Liu-Rajpal arXiv:2601.10047 Theorem 5.12 for
FRS: "Assume that m >= c/eta^2 and that q is at least a fixed POLYNOMIAL in n
and 1/eta."

FINDING 1 -- a = 1 AT CAPACITY, CONFIRMED BY A SECOND INDEPENDENT PAPER
------------------------------------------------------------------------
Both (1.1) and (1.3) are linear in n. Iteration 29 derived a = 1 at capacity
from the FRS paper alone; this is an independent confirmation from a different
group, for a different code family. The ceiling equation

    ceiling = E - a*nu - log2 C + g_commit

holds at capacity with a = 1 for every family anyone has proved a capacity gap
for. Capacity is a query-phase phenomenon, not a ceiling phenomenon. This is now
the best-supported structural claim in the repository.

FINDING 2 -- THE UNFOLDED ROUTES NEED EXPONENTIALLY LARGE FIELDS
------------------------------------------------------------------
Random ensembles skip the folding penalty entirely -- one field element per
symbol. But their field requirement is exp(Omega(1/eta^4)) for random linear
codes and n*exp(Omega(1/eta^7)) for random RS. To be any use, the capacity
radius 1 - R - 2*eta must beat the Johnson radius 1 - sqrt(R), which forces

    eta  <  (sqrt(R) - R) / 2

and at rate 1/4 that is eta < 0.125. Section 2 evaluates the field requirement
there: about 5,900 bits for random linear codes and about 3.0 MILLION bits for
random RS -- against the 31 to 192 bits actually deployed.

FINDING 3 -- THE COSTS ARE COMPLEMENTARY, AND THAT IS THE POINT
-----------------------------------------------------------------
    family                folding        field size          blocked by
    ---------------------------------------------------------------------
    FRS / subspace design m >= c/eta^2   polynomial          payload
    random linear         none           exp(O(l^2/eta^4))   field size
    random RS             none           exp(O(l^4/eta^7))   field size

Folding is precisely the device that trades payload for a polynomial field.
Remove it and the field requirement explodes. So "capacity without folding"
is not an unexplored option -- it is a proved theorem whose price is a field
nobody can build.

Every route to capacity known as of 2026-07 is therefore closed for deployed
parameters, and closed for two structurally different reasons.

SECONDARY OBSTACLE
------------------
The random-ensemble results hold "with high probability over the choice of C"
(Theorem 1.2 states 2/3, amplified in the body). A deployed system samples one
code and publishes it. There is no known efficient certificate that a PARTICULAR
sampled code has the property, so the guarantee does not transfer to a fixed
deployed instance the way an explicit-family theorem does. This matters less
than the field size, and is noted rather than modelled.

*** RETRACTED IN ITERATION 46. *** The 2/3 is a convenience figure in an
informal statement. Yuan-Zhu's formal theorems give 1 - q^{-Omega(n)}, which at
Ligero parameters is at most 2^-360 even reading the hidden constant as n/1000.
No certificate is needed, because the event it would certify essentially cannot
happen. The one residual requirement is that the code be sampled HONESTLY --
from a public beacon or by hashing a public string -- which is a standard
transparent-setup condition. See ligero_obstacles.py.

HONEST LIMITS
-------------
1. Omega and O hide constants. Every figure below takes the hidden constant to
   be 1, which is the most generous possible reading; real requirements are
   larger, so the conclusions are lower bounds on infeasibility.
2. l = 1 (lines) throughout. WHIR uses larger curve degree l, and the field
   requirement grows as exp(l^2) or exp(l^4), so larger l is strictly worse.
3. The Johnson comparison uses the deployed-rate radii; no claim is made about
   asymptotic regimes.
"""

import math

LN2 = math.log(2)


def johnson_radius(rho):
    return 1.0 - math.sqrt(rho)


def capacity_radius(rho, eta):
    """GGSW state the radius as 1 - R - 2*eta (note the factor 2)."""
    return 1.0 - rho - 2.0 * eta


def eta_to_beat_johnson(rho):
    """Largest eta for which the capacity radius still beats Johnson's."""
    return (math.sqrt(rho) - rho) / 2.0


def field_bits_random_linear(eta, ell=1, c=1.0):
    """Theorem 5.3: q >= exp(Omega(l^2/eta^4))."""
    return c * (ell ** 2) / (eta ** 4) / LN2


def field_bits_random_rs(eta, n, ell=1, c=1.0):
    """Theorem 5.6: q >= n * exp(Omega(l^4/eta^7))."""
    return math.log2(n) + c * (ell ** 4) / (eta ** 7) / LN2


def min_n_random(eta, ell=1, c=1.0):
    """Both theorems also need n >= Omega(l^4/eta^7)."""
    return c * (ell ** 4) / (eta ** 7)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    n = 2 ** 22

    sec("1. a = 1 AT CAPACITY, NOW FROM TWO INDEPENDENT PAPERS")
    print("""
  Jeronimo-Liu-Rajpal (2601.10047) Thm 5.12, folded RS:
      eps <= (C1/q) * ( n/eta + 1/eta^3 )
  Goyal-Guruswami-Sun-Wootters (2607.08516) bounds (1.1) and (1.3):
      eps*q >= n*l/eta + O(l^2/eta^3)          [subspace design]
      eps*q >= n*l(1-R)/eta + O(l^2/eta^3)     [random ensembles]

  All linear in n. Different groups, different code families, same exponent.
  Capacity does not move the ceiling -- it moves the radius.""")

    sec("2. HOW CLOSE TO CAPACITY DO YOU HAVE TO GET TO BEAT JOHNSON?")
    print(f"  {'rate':>7} {'Johnson radius':>15} {'eta needed':>12} "
          f"{'capacity radius there':>22}")
    print("  " + "-" * 60)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        e = eta_to_beat_johnson(rho)
        print(f"  {'1/%d' % 2**R:>7} {johnson_radius(rho):>15.4f} {e:>12.4f} "
              f"{capacity_radius(rho, e):>22.4f}")
    print("""
  At the break-even eta the two radii coincide exactly, so any real gain needs
  eta strictly below these -- and the field requirements below blow up as eta
  shrinks.""")

    sec("3. THE FIELD REQUIREMENT OF THE UNFOLDED ROUTES")
    print(f"  {'eta':>7} {'random linear (bits)':>22} {'random RS (bits)':>20} "
          f"{'min n':>12}")
    print("  " + "-" * 66)
    for eta in (0.40, 0.30, 0.25, 0.20, 0.15, 0.125):
        print(f"  {eta:>7.3f} {field_bits_random_linear(eta):>22.4g} "
              f"{field_bits_random_rs(eta, n):>20.4g} "
              f"{min_n_random(eta):>12.4g}")
    print("\n  at the eta each rate actually requires:\n")
    print(f"  {'rate':>7} {'eta':>9} {'random linear':>16} {'random RS':>16} "
          f"{'deployed E':>12}")
    print("  " + "-" * 66)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        e = eta_to_beat_johnson(rho)
        print(f"  {'1/%d' % 2**R:>7} {e:>9.4f} {field_bits_random_linear(e):>16.4g} "
              f"{field_bits_random_rs(e, n):>16.4g} {'31-192':>12}")
    print("""
  Deployed challenge fields are 124 to 192 bits. The unfolded routes need
  thousands of bits (random linear) to millions (random RS), at the most
  generous possible reading of the hidden constants. This is not a close call.""")

    sec("4. THE THREE ROUTES, AND WHY EACH IS CLOSED")
    print(f"""
  {'family':<24} {'folding':<16} {'field size':<22} blocked by
  {'-'*82}
  {'FRS / subspace design':<24} {'m >= c/eta^2':<16} {'polynomial':<22} payload (it. 29)
  {'random linear':<24} {'none':<16} {'exp(O(l^2/eta^4))':<22} field size
  {'random RS':<24} {'none':<16} {'exp(O(l^4/eta^7))':<22} field size

  Folding is exactly the device that trades payload for a polynomial field.
  Removing it does not remove the cost -- it relocates the cost into the field
  size, where it is worse. So "capacity without the folding penalty" is not an
  unexplored option: it is a proved theorem with a price nobody can pay.

  Conclusion: as of 2026-07 every known route to capacity-radius proximity gaps
  is closed at deployed parameters, for two structurally different reasons, and
  none of them would have moved the ceiling even if open.""")


# ---------------------------------------------- iteration 42: Yuan-Zhu bounds

def yz_linear_bits(eps, n=2 ** 22):
    """Yuan-Zhu Thm 1.1.1: q = Theta(n) AND q >= (2/eps)^(1/eps)."""
    return max(math.log2(n), (1.0 / eps) * math.log2(2.0 / eps))


def yz_rs_bits(eps, n=2 ** 22, c=1.0):
    """Yuan-Zhu Thm 6.6, random RS: q >= n * 2^{O(eps^-3)}."""
    return math.log2(n) + c / eps ** 3


def eps_to_beat_johnson(rho):
    """Yuan-Zhu parameterise the radius as 1-R-eps (no factor 2)."""
    return math.sqrt(rho) - rho


def ntt_penalty(log2n=22.0, ntt_share=0.905):
    """Replacing an O(n log n) NTT with O(n log^2 n) multipoint evaluation.

    EFFICIENCY.md measures NTT at 90-91% of prover latency. The asymptotic
    ratio is log n; this is generous to the random-evaluation route, since real
    multipoint-evaluation constants are far worse than NTT constants.
    """
    return (1 - ntt_share) + ntt_share * log2n


def report_corrected():
    sec("5. CORRECTED: THE FIELD-SIZE OBJECTION COLLAPSES")
    print("  Yuan-Zhu (arXiv 2605.07595) vs the GGSW bounds used above.\n")
    print(f"  {'eps':>7} {'YZ linear':>11} {'GGSW linear':>13} "
          f"{'YZ rand-RS':>12} {'GGSW rand-RS':>14}")
    print("  " + "-" * 62)
    for e in (0.30, 0.25, 0.20, 0.15, 0.10):
        eta = e / 2.0
        print(f"  {e:>7.2f} {yz_linear_bits(e):>11.1f} "
              f"{field_bits_random_linear(eta):>13.4g} {yz_rs_bits(e):>12.1f} "
              f"{field_bits_random_rs(eta, 2**22):>14.4g}")
    print(f"\n  {'rate':>7} {'eps break-even':>15} {'YZ linear':>11} "
          f"{'YZ rand-RS':>12} {'deployed E':>12} {'feasible?':>11}")
    print("  " + "-" * 74)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        e = eps_to_beat_johnson(rho)
        lin, rs = yz_linear_bits(e), yz_rs_bits(e)
        print(f"  {'1/%d' % 2**R:>7} {e:>15.4f} {lin:>11.1f} {rs:>12.1f} "
              f"{'124-192':>12} {'YES':>11}")
    print("""
  Random linear codes need about 22 bits -- the Theta(n) term dominates, and the
  (2/eps)^(1/eps) term is only 12 to 17 bits at these radii. Random RS needs 86
  to 135 bits, inside a deployed extension field. Section 4's "blocked by field
  size" is wrong for both.""")

    sec("6. WHAT ACTUALLY BLOCKS THEM: STRUCTURE, NOT FIELD SIZE")
    pen = ntt_penalty()
    print(f"""
  Random LINEAR codes are not Reed-Solomon. FRI folds by x -> x^2 on a
  multiplicative coset; a random linear code has no such map, so there is no FRI
  to run. This route is open to Ligero/Brakedown/Blaze/Bolt-style systems -- and
  those are exactly the systems the Yuan-Zhu and GGSW papers cite as motivation
  -- but it is not a change a FRI-based STARK can make.

  Random-EVALUATION-POINT RS keeps the polynomial structure but destroys the
  evaluation domain's group structure. The low-degree extension stops being an
  NTT (O(n log n)) and becomes general multipoint evaluation (O(n log^2 n)).
  EFFICIENCY.md measures NTT at 90.5% of prover latency, so the asymptotic
  prover cost multiplies by

      (1 - 0.905) + 0.905 * log2(n)  =  {pen:.1f}x   at n = 2^22

  and that is the generous reading: it credits multipoint evaluation with NTT's
  constants, which it does not have. Trading a ~20x slower prover for at most a
  2x query reduction is not a trade any deployed system would take.

  So the corrected verdict is:

    FRS / subspace design   folding m >= c/eta^2      blocked: payload (it 29)
    random linear           field ~22 bits, FEASIBLE  blocked: no FRI folding map
    random RS               field 86-135, FEASIBLE    blocked: ~{pen:.0f}x prover

  Every route is still closed to a FRI-based STARK, but for structural reasons,
  and the random-linear route is genuinely OPEN to linear-code systems.""")


if __name__ == "__main__":
    report()
    report_corrected()
