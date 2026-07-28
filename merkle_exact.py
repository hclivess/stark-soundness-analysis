"""
An exact auth-node formula from soundcalc validates one approximation and
exposes a small systematic bias in soundcalc itself. And it corrects README.

Iteration 48 compared this repo's Merkle deduplication saving (37.4%) against
SP1's published expected/worst-case proof-size ratio (38.1%) and called it a
validation. Iteration 60 read soundcalc's `reports/summary.md`, which publishes
BOTH figures for every system, and the ratios looked alarming:

    Airbender  5.9%     OpenVM  6.6%     Pico 17.4%
    SP1       40.4%     ZisK   14.1%     OpenVM2/zkDTVM 0.0%

A 0-40% spread against a model claiming 33-52% reads like a refutation, and the
first hypothesis was that iteration 48 had compared two different quantities:
expected-vs-NAIVE (this repo) against expected-vs-WORST-CASE (soundcalc). Those
are not the same thing -- worst case with sharing is strictly below s*depth,
because the top levels of the tree cannot hold more nodes than they have.

THAT HYPOTHESIS WAS WRONG, AND THE SOURCE SETTLES IT
------------------------------------------------------
soundcalc/common/utils.py:77 --

    else:
        return num_openings * get_size_of_merkle_proof_bits(...)

soundcalc's "worst case" is num_openings independent full paths: NO sharing at
all. That is exactly `naive_auth_nodes(s, d) = s*d`. The two quantities are the
same, and iteration 48's comparison was well-posed.

The 0-40% spread across systems is therefore not about Merkle sharing at all --
it is the fixed, query-independent part of each proof (field elements, OOD
samples, per-circuit overhead) diluting the varying part by different amounts.
OpenVM2 and zkDTVM show 0.0% because WHIR/SWIRL proofs are dominated by
components that do not scale with the query set. A system-level exp/worst ratio
is not a measurement of Merkle dedup, and should not be read as one.

THE EXACT FORMULA, AND WHAT IT SAYS ABOUT THIS REPO'S APPROXIMATION
--------------------------------------------------------------------
soundcalc/common/utils.py:65 computes, per level d,

    2^d * [ (1 - 2^-d)^k  -  (1 - 2^(1-d))^k ]

which is exact: P(v unoccupied) - P(v and its sibling both unoccupied) is
P(v unoccupied AND sibling occupied), the condition for v being an auth node.

`merkle_dedup.expected_auth_nodes` instead uses m*q*(1-q) with q the marginal
occupancy -- it treats a node's occupancy as INDEPENDENT of its sibling's, and
says so in its docstring. Siblings are negatively correlated (a query landing on
v cannot land on its sibling), so the independent form should underestimate.

It does, and the effect is negligible:

    s=124 d=21     mine 1631.3     exact 1632.0     gap 0.7 nodes  (0.04%)
    s=193 d=23     mine 2801.9     exact 2802.6     gap 0.7 nodes  (0.03%)
    s=27  d=18     mine  333.6     exact  334.3     gap 0.7 nodes  (0.21%)

The bias is bounded because the two forms agree at both ends: where m >> k the
occupancy is rare and both reduce to k(1 - ...), and where m << k both saturate
to zero. The gap lives only in the narrow band around q = 1/2 and is worth under
one node per tree. The docstring's flagged approximation is now validated
against an independently derived exact formula, not only against simulation.

AND A SMALL SYSTEMATIC BIAS IN SOUNDCALC
------------------------------------------
utils.py:66 wraps each level in math.ceil:

    num_hashes += math.ceil(2**d * prob_sibling_in_proof)

Rounding up per level, over `depth` levels, adds up to `depth` phantom hashes
per Merkle tree. Against Monte Carlo:

    system        soundcalc   simulation    bias
    SP1  s=124        1642        1635.8    +0.38%
    ZisK s=229        2821        2812.4    +0.31%
    R0   s=50          734         724.5    +1.32%
    Miden s=27         341         333.4    +2.27%

Always positive, so it overstates proof size -- the safe direction, and
consistent with everything else soundcalc does. But it is systematic rather than
random, and it is largest exactly where the query count is smallest, because
`depth` phantom hashes is a bigger share of a smaller proof. Miden pays 2.27%.
Removing the ceil (or applying it once to the total) would remove it.

THE CORRECTION TO README
-------------------------
README said charging s*depth "overcounts by 33-52% at the query counts 128-bit
PQ requires". That band is real but it is a HYPOTHETICAL sweep -- merkle_dedup's
own table runs s = 32..1000, and 51.7% is attained at s=1000, a query count no
deployed system uses.

Across the seven configurations that actually ship, the overcount is:

    Airbender  30.1%     Miden      29.8%     RISC Zero  30.1%
    Pico       32.5%     OpenVM     36.6%     SP1        36.9%
    ZisK       41.3%

30-44% including NADO's 320 queries (43.7%), and 30-41% for the seven zkVMs.
The old band's floor was too high -- three deployed systems fall below 33% --
and its ceiling is unreachable in deployment. README now states the deployed
range and marks the wider one as a sweep.
"""

import math
from merkle_dedup import expected_auth_nodes, naive_auth_nodes, simulate_auth_nodes

# (name, queries, log2 domain size) -- from systems.py, T + R
CONFIGS = [("SP1", 124, 21), ("OpenVM", 193, 23), ("Airbender", 87, 24),
           ("Pico", 84, 22), ("ZisK", 229, 21), ("RISC Zero", 50, 21),
           ("Miden", 27, 18), ("NADO", 320, 21)]

# soundcalc reports/summary.md, expected / worst-case proof size in KiB
SUMMARY_KIB = [("Airbender", 1836, 1951), ("OpenVM", 7687, 8231),
               ("OpenVM2", 270, 270), ("Pico", 232, 281), ("SP1", 529, 887),
               ("ZisK", 269, 313), ("zkDTVM", 200, 200)]


def soundcalc_auth_nodes(k, depth, ceil=True):
    """soundcalc/common/utils.py:63-66. Exact expectation, ceil'd per level."""
    total = 0.0
    for d in range(1, depth + 1):
        p = (1 - 2.0 ** -d) ** k - (1 - 2.0 ** (1 - d)) ** k
        total += math.ceil(2.0 ** d * p) if ceil else 2.0 ** d * p
    return total


def ceil_bias_nodes(k, depth):
    """Phantom hashes introduced by soundcalc's per-level ceil. In [0, depth]."""
    return soundcalc_auth_nodes(k, depth) - soundcalc_auth_nodes(k, depth, False)


def independence_gap(k, depth):
    """How far this repo's independent-sibling form falls below the exact one."""
    return soundcalc_auth_nodes(k, depth, False) - expected_auth_nodes(k, depth)


def deployed_saving_range():
    """Overcount of s*depth across the seven shipping zkVMs, by the exact formula."""
    vals = [1 - soundcalc_auth_nodes(s, d) / naive_auth_nodes(s, d)
            for n, s, d in CONFIGS if n != "NADO"]
    return min(vals), max(vals)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. soundcalc's 'WORST CASE' IS THE NO-SHARING BASELINE")
    print("""
  soundcalc/common/utils.py:77 --

      else:
          return num_openings * get_size_of_merkle_proof_bits(...)

  num_openings independent full paths, no sharing. That is exactly this repo's
  naive_auth_nodes(s, d) = s*d, so iteration 48's comparison of a dedup saving
  against an expected/worst-case ratio was comparing the same quantity.

  Which means the spread in reports/summary.md is NOT about Merkle sharing:\n""")
    print(f"  {'system':<12} {'expected':>9} {'worst':>7} {'ratio':>8}")
    print("  " + "-" * 40)
    for n, e, w in SUMMARY_KIB:
        print(f"  {n:<12} {e:>9} {w:>7} {1 - e / w:>7.1%}")
    print("""
  0.0% for OpenVM2 and zkDTVM (WHIR/SWIRL: proof dominated by components that
  do not scale with the query set), 40.4% for SP1. The variation is the fixed
  part of each proof diluting the varying part by different amounts. A
  system-level exp/worst ratio is not a measurement of Merkle dedup.""")

    sec("2. THE EXACT FORMULA VALIDATES THIS REPO'S INDEPENDENCE APPROXIMATION")
    print("""
  soundcalc/common/utils.py:65, per level d:  2^d * [(1-2^-d)^k - (1-2^(1-d))^k]
  exact:  P(v unoccupied) - P(v and sibling both unoccupied)

  merkle_dedup uses m*q*(1-q), treating siblings as independent. They are
  negatively correlated, so it should underestimate. It does, by under a node:\n""")
    print(f"  {'system':<11} {'s':>5} {'d':>4} {'this repo':>11} {'exact':>10} "
          f"{'gap':>7} {'gap %':>8}")
    print("  " + "-" * 60)
    for n, s, d in CONFIGS:
        mine, ex = expected_auth_nodes(s, d), soundcalc_auth_nodes(s, d, False)
        print(f"  {n:<11} {s:>5} {d:>4} {mine:>11.1f} {ex:>10.1f} "
              f"{ex - mine:>7.2f} {(ex - mine) / ex:>7.3%}")
    print("""
  The forms agree at both ends -- where m >> k occupancy is rare and both reduce
  to k(1 - ...), where m << k both saturate to zero -- so the gap lives only
  around q = 1/2 and is worth under one node per tree.""")

    sec("3. A SYSTEMATIC BIAS IN SOUNDCALC: THE PER-LEVEL ceil")
    print("""
  utils.py:66 wraps each level in math.ceil, so up to `depth` phantom hashes
  accumulate per tree. Against Monte Carlo ground truth:\n""")
    print(f"  {'system':<11} {'s':>5} {'d':>4} {'soundcalc':>10} {'sim':>9} "
          f"{'bias':>8} {'of depth':>10}")
    print("  " + "-" * 62)
    for n, s, d in CONFIGS:
        sc = soundcalc_auth_nodes(s, d)
        sim = simulate_auth_nodes(s, d, trials=60, seed=7)
        print(f"  {n:<11} {s:>5} {d:>4} {sc:>10.0f} {sim:>9.1f} "
              f"{(sc - sim) / sim:>+7.2%} {ceil_bias_nodes(s, d):>9.1f}/{d}")
    print("""
  Always positive: it overstates proof size, the safe direction. But it is
  systematic, not random, and largest where the query count is smallest --
  `depth` phantom hashes is a bigger share of a smaller proof. Miden pays 2.27%.""")

    sec("4. CORRECTING README'S 33-52%")
    lo, hi = deployed_saving_range()
    print(f"""
  README said s*depth "overcounts by 33-52% at the query counts 128-bit PQ
  requires". That band comes from merkle_dedup's sweep over s = 32..1000; 51.7%
  is attained at s=1000, which nothing deploys. Across shipping configurations:\n""")
    print(f"  {'system':<11} {'s':>5} {'d':>4} {'s*depth':>9} {'exact':>9} "
          f"{'overcount':>11}")
    print("  " + "-" * 54)
    for n, s, d in CONFIGS:
        nv = naive_auth_nodes(s, d)
        sc = soundcalc_auth_nodes(s, d)
        print(f"  {n:<11} {s:>5} {d:>4} {nv:>9} {sc:>9.0f} {1 - sc / nv:>10.1%}")
    print(f"""
  {lo:.0%}-{hi:.0%} across the seven zkVMs, {lo:.0%}-44% including NADO. The old band's
  floor was too high -- Miden, RISC Zero and Airbender all fall below 33% -- and
  its ceiling is unreachable in deployment. README now gives the deployed range
  and marks the wider one as a sweep.""")


if __name__ == "__main__":
    report()
