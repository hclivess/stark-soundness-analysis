"""
Pricing the one capacity route that is actually open.

Iteration 42 established that the field-size objection to the unfolded capacity
routes was overstated by two to five orders of magnitude, and that what really
blocks them is structural: random linear codes have no x -> x^2 folding map, so
FRI cannot use them. But that is a statement about FRI. The systems built ON
random linear codes -- Ligero, Brakedown, and the newer Blaze and Bolt, which
Yuan-Zhu and GGSW both cite as motivation -- have no such obstruction.

So the route is open to them, and nobody in this repo had asked what it is worth.

THE COMPARISON
--------------
A linear-code system's proximity test today runs at the interleaved radius.
Iteration 28 established that bound from primary sources:

    Roth-Zemor (Diamond-Posen CiC 1(1) 2024, Thm 1): for a proximity parameter
    e in {0, ..., (d-1)/3}, the false-witness probability is (e+1)/q

so the operative relative radius is (1-R)/3 for a near-MDS code of rate R. Over
a large alphabet a random linear code is near-MDS, so its relative distance is
approximately 1-R.

Yuan-Zhu Thm 1.1.1 offers instead

    radius 1 - R - eps,   requiring   q = Theta(n) and q >= (2/eps)^(1/eps)

and correlated agreement at that radius. The per-query yield is -log2(1-radius)
in both cases, so the whole question is how much larger the radius gets and what
the field costs.

THE FRONTIER (rate 1/4, n = 2^22)
----------------------------------
    eps    radius   yield   vs interleaved   query cut   field bits
    0.25   0.5000  1.0000        2.41x         58.5%        22.0
    0.20   0.5500  1.1520        2.78x         64.0%        22.0
    0.15   0.6000  1.3219        3.19x         68.6%        24.9
    0.10   0.6500  1.5146        3.65x         72.6%        43.2
    0.05   0.7000  1.7370        4.19x         76.1%       106.4
    0.02   0.7300  1.8890        4.55x         78.0%       332.2

The interleaved radius at this rate is 0.25 and its yield 0.415. So the capacity
result is worth a 2.4x to 4.6x improvement in per-query yield -- a 59% to 78%
reduction in query count -- and the first 2.8x of that is free, in the sense that
the Theta(n) term dominates and the field requirement is 22 bits either way.

Diminishing returns set in hard: going from eps = 0.20 to eps = 0.02 buys 14
more percentage points of query reduction for 15x the field size.

WHERE THE JOHNSON RADIUS SITS
-----------------------------
At eps = sqrt(R) - R the capacity radius equals the Johnson radius exactly
(1 - R - eps = 1 - sqrt(R)). That is eps = 0.25 at rate 1/4 -- the first row.
So the first 2.41x is "reach the Johnson radius", which is not news; the rows
below it are genuinely beyond-Johnson territory, and those need 25 to 332 bits.

HONEST LIMITS -- THIS IS A PRICE, NOT A PROTOCOL
-------------------------------------------------
1. It assumes the rest of the protocol composes at the larger radius. A
   proximity-gap/correlated-agreement statement is not by itself a proof system;
   Ligero-style soundness also involves the interleaved structure, the linear
   check, and the opening argument. I have not verified those compose at the
   capacity radius, and Yuan-Zhu do not claim it.
2. The near-MDS assumption (relative distance ~ 1-R) needs a large alphabet,
   which q = Theta(n) supplies -- but Ligero and Brakedown are often deployed
   over SMALL fields precisely to make encoding cheap. Moving to a 22-bit
   alphabet is a real change to those systems, and its encoding cost is not
   modelled here.
3. The guarantee holds "with high probability over the choice of C". A deployed
   system samples one code and publishes it, and there is no known efficient
   certificate that a particular sample has the property (noted in iteration 30,
   still unresolved).
4. Query count is not proof size for these systems: Ligero/Brakedown proofs are
   dominated by the O(sqrt(n)) column openings, so a 60% query cut is not a 60%
   proof-size cut. Pricing that needs their proof-size model, which this repo
   does not carry.
"""

import math


def yield_at(radius):
    """Per-query bits: a query detects with probability `radius`."""
    return -math.log2(1 - radius) if 0 < radius < 1 else float("nan")


def interleaved_radius(R):
    """Roth-Zemor: e <= (d-1)/3, and d ~ (1-R)n for a near-MDS code."""
    return (1 - R) / 3.0


def capacity_radius(R, eps):
    """Yuan-Zhu Thm 1.1.1: rho < 1 - R - eps."""
    return 1 - R - eps


def johnson_radius(R):
    return 1 - math.sqrt(R)


def eps_at_johnson(R):
    """The eps at which the capacity radius exactly equals Johnson's."""
    return math.sqrt(R) - R


def field_bits(eps, n=2 ** 22):
    """q = Theta(n) AND q >= (2/eps)^(1/eps)."""
    return max(math.log2(n), (1.0 / eps) * math.log2(2.0 / eps))


def query_cut(R, eps):
    """Fractional reduction in query count vs the interleaved radius."""
    yi = yield_at(interleaved_radius(R))
    yc = yield_at(capacity_radius(R, eps))
    return 1 - yi / yc


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE FRONTIER: RADIUS BOUGHT vs FIELD PAID (rate 1/4)")
    R = 0.25
    yi = yield_at(interleaved_radius(R))
    print(f"  Interleaved radius {interleaved_radius(R):.4f}, yield {yi:.4f}. "
          f"Johnson radius {johnson_radius(R):.4f}.\n")
    print(f"  {'eps':>7} {'radius':>9} {'yield':>8} {'vs interleaved':>15} "
          f"{'query cut':>11} {'field bits':>11} {'beyond Johnson?':>16}")
    print("  " + "-" * 82)
    for eps in (0.25, 0.20, 0.15, 0.10, 0.05, 0.02):
        rad = capacity_radius(R, eps)
        y = yield_at(rad)
        print(f"  {eps:>7.2f} {rad:>9.4f} {y:>8.4f} {y/yi:>14.2f}x "
              f"{query_cut(R, eps):>10.1%} {field_bits(eps):>11.1f} "
              f"{'yes' if rad > johnson_radius(R) else 'no (= J)':>16}")
    print("""
  The first row is exactly the Johnson radius -- at eps = sqrt(R) - R the two
  coincide -- so the 2.41x there is "reach Johnson", not news. The rows below it
  are beyond-Johnson, and cost 25 to 332 bits.

  Note where the cost lives: the first 2.78x is free, because q = Theta(n)
  dominates and 22 bits is required either way. After that the (2/eps)^(1/eps)
  term takes over and returns diminish hard -- eps 0.20 -> 0.02 buys 14 more
  percentage points for 15x the field.""")

    sec("2. ACROSS RATES, AT THE FREE POINT")
    print(f"  {'rate':>7} {'distance':>9} {'interleaved':>12} {'capacity':>10} "
          f"{'query cut':>11} {'field bits':>11}")
    print("  " + "-" * 66)
    for R in (0.5, 0.25, 0.125):
        eps = eps_at_johnson(R)
        print(f"  {R:>7.3f} {1-R:>9.3f} {interleaved_radius(R):>12.4f} "
              f"{capacity_radius(R, eps):>10.4f} {query_cut(R, eps):>10.1%} "
              f"{field_bits(eps):>11.1f}")
    print("""
  47% to 67% fewer queries at 22 bits of field, across the deployed rate range,
  purely from testing at the Johnson radius instead of the interleaved (1-R)/3.""")

    sec("3. WHY THIS IS A PRICE AND NOT A PROTOCOL")
    print("""
  Four things stand between this table and a deployable change, and none of them
  is field size:

  1. COMPOSITION. A proximity-gap statement is not a proof system. Ligero-style
     soundness also involves the interleaved structure, the linear check and the
     opening argument. Whether those compose at the capacity radius is not
     something Yuan-Zhu claim, and not something checked here.

  2. ALPHABET. The near-MDS assumption needs a large alphabet, and q = Theta(n)
     supplies it -- but Ligero and Brakedown are often deployed over SMALL fields
     precisely to make encoding cheap. A 22-bit alphabet is a real change whose
     encoding cost this file does not model.

  3. CERTIFICATION. The guarantee holds with high probability over the choice of
     C. A deployed system samples one code and publishes it, and no efficient
     certificate for a particular sample is known. Flagged in iteration 30 and
     still unresolved.

  4. QUERIES ARE NOT PROOF SIZE for these systems. Ligero/Brakedown proofs are
     dominated by O(sqrt(n)) column openings, so a 60% query cut is not a 60%
     proof-size cut. Pricing that needs a proof-size model this repo lacks.

  So: the one open capacity route is worth 2.4x to 4.6x in per-query yield, the
  first 2.8x of it at no extra field cost, and four unmodelled obstacles stand
  between that and a deployment.""")


if __name__ == "__main__":
    report()
