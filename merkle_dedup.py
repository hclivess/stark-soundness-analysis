"""
Merkle path deduplication: the proof-size model in pq_design.py overcounts.

THE OVERSIGHT
-------------
Every proof-size estimate in this repo has charged `s * depth` authentication
hashes for s queries into a depth-d tree. That is the cost of s INDEPENDENT
openings. Real openings share structure: two queries whose leaves land in the
same subtree share every authentication node above the point where their paths
merge, and a node that is itself on another query's path never needs to be sent
at all.

At the query counts this repo now cares about -- 113 to 450 for 128-bit PQ
provable soundness -- s is a large fraction of the tree's width near the top,
so the sharing is not a rounding error.

THE MODEL
---------
Open s leaves of a depth-d binary tree. Let O_i be the set of occupied nodes at
level i (i = 0 at the leaves), O_0 being the queried leaves themselves and
O_{i+1} the parents of O_i. To recompute the root the verifier needs, for every
occupied node, its SIBLING -- except where the sibling is itself occupied, in
which case it is already known. So

    auth(i)  =  #{ v in O_i : sibling(v) not in O_i }
    total    =  sum over i of auth(i)

With s leaves uniform among m_i = 2^(d-i) nodes at level i,

    E|O_i|  =  m_i * (1 - (1 - 1/m_i)^s)

and near the top of the tree m_i << s, so O_i saturates: every node is occupied,
every sibling is occupied, and auth(i) collapses to ZERO. The naive model keeps
charging s hashes per level all the way to the root.

Asymptotically, distinct auth nodes ~ s*(d - log2 s) + O(s): the tree is
saturated for the top log2(s) levels and behaves independently below that.

This file derives the exact expectation, validates it by Monte Carlo, and
re-prices the pq_design.py configurations.
"""

import math
import random


# ------------------------------------------------------------------ exact model

def expected_occupied(s, level_size):
    """E|O_i| for s uniform leaves: m*(1 - (1 - 1/m)^s)."""
    m = level_size
    if m <= 0:
        return 0.0
    return m * (1.0 - (1.0 - 1.0 / m) ** s)


def expected_auth_nodes(s, d):
    """
    Expected distinct authentication nodes, treating each level's occupancy as
    independent uniform (an approximation -- validated against simulation below).

    At level i with m = 2^(d-i) nodes and expected occupancy q = E|O_i|/m, a node
    is occupied w.p. q and its sibling unoccupied w.p. (1-q), so
        auth(i) ~ m * q * (1 - q) * 2   ... (both orderings counted once each)
    which simplifies to  2 * m * q * (1-q)  -- but each unordered pair contributes
    at most one needed sibling, so we count occupied-with-unoccupied-sibling:
        auth(i) = m * q * (1 - q)  * 2 / 1
    Use the pair formulation directly: of m/2 sibling pairs, a pair needs one
    auth node iff exactly one of its two members is occupied.
    """
    total = 0.0
    for i in range(d):
        m = 2 ** (d - i)
        q = expected_occupied(s, m) / m
        pairs = m / 2.0
        # exactly one of the pair occupied -> one auth node needed
        total += pairs * 2.0 * q * (1.0 - q)
    return total


def naive_auth_nodes(s, d):
    return s * d


def asymptotic_auth_nodes(s, d):
    """s*(d - log2 s) + s, valid while s << 2^d."""
    if s <= 0:
        return 0.0
    return max(0.0, s * (d - math.log2(s)) + s)


# ------------------------------------------------------------------ simulation

def simulate_auth_nodes(s, d, trials=40, seed=0):
    """Ground truth: build the occupied sets and count needed siblings."""
    rng = random.Random(seed)
    n = 1 << d
    acc = 0
    for _ in range(trials):
        occ = set(rng.randrange(n) for _ in range(s))
        need = 0
        cur = occ
        for _ in range(d):
            nxt = set()
            for v in cur:
                if (v ^ 1) not in cur:
                    need += 1
                nxt.add(v >> 1)
            cur = nxt
        acc += need
    return acc / trials


# ------------------------------------------------------------------ reporting

def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. VALIDATION: model vs Monte Carlo")
    print(f"  {'s':>5} {'depth':>6} {'naive':>9} {'model':>10} {'simulated':>11} "
          f"{'err %':>7} {'saving':>8}")
    print("  " + "-" * 62)
    worst = 0.0
    for s, d in ((32, 18), (64, 18), (113, 21), (200, 21), (320, 18),
                 (450, 21), (450, 24), (1000, 21)):
        nai = naive_auth_nodes(s, d)
        mod = expected_auth_nodes(s, d)
        sim = simulate_auth_nodes(s, d, trials=25)
        err = abs(mod - sim) / sim * 100
        worst = max(worst, err)
        print(f"  {s:>5} {d:>6} {nai:>9} {mod:>10.0f} {sim:>11.0f} {err:>6.1f}% "
              f"{100*(1-sim/nai):>7.1f}%")
    print(f"\n  worst model error vs simulation: {worst:.1f}%  "
          f"{'PASS' if worst < 5 else 'CHECK'}")
    print("""
  The saving is real and it GROWS with query count: at 450 queries into a 2^21
  tree the naive model overcharges by more than a third.""")

    sec("2. WHY: the top of the tree saturates")
    d, s = 21, 450
    print(f"  s = {s}, depth = {d}. Occupancy and auth nodes by level:\n")
    print(f"  {'level':>6} {'nodes':>10} {'E|O_i|':>10} {'occupancy':>10} {'auth':>8}")
    print("  " + "-" * 50)
    for i in range(d):
        m = 2 ** (d - i)
        q = expected_occupied(s, m) / m
        pairs = m / 2.0
        auth = pairs * 2.0 * q * (1.0 - q)
        if i < 6 or i > d - 8:
            print(f"  {i:>6} {m:>10} {q*m:>10.0f} {q:>9.1%} {auth:>8.0f}")
        elif i == 6:
            print(f"  {'...':>6}")
    print("""
  Above the saturation level every sibling is already occupied, so auth(i) -> 0.
  The naive model keeps charging s hashes per level all the way to the root; the
  top log2(s) levels are free.""")

    sec("3. RE-PRICING THE 128-BIT PQ CONFIGURATIONS")
    HASH = 32
    print("  From pq_design.py, at 128 PQ provable bits (trace 2^20):\n")
    print(f"  {'config':<26} {'s':>5} {'naive KiB':>10} {'dedup KiB':>10} {'saving':>8}")
    print("  " + "-" * 64)
    rows = [("Goldilocks^5 blowup 16", 113, 4, 5, 8),
            ("M31^10 blowup 16", 114, 4, 10, 4),
            ("Goldilocks^5 blowup 2", 450, 1, 5, 8)]
    out = {}
    for name, s, R, deg, w in rows:
        nu = 20 + R
        rounds = max(0, nu - R)
        # base trees at depth nu, then one FRI tree per fold layer at shrinking depth
        nai = 2 * naive_auth_nodes(s, nu) + sum(naive_auth_nodes(s, max(nu - i, 1))
                                                for i in range(rounds))
        ded = 2 * expected_auth_nodes(s, nu) + sum(expected_auth_nodes(s, max(nu - i, 1))
                                                   for i in range(rounds))
        vals = s * (2 * w + rounds * 2 * deg * w)
        kn = (nai * HASH + vals) / 1024
        kd = (ded * HASH + vals) / 1024
        out[name] = (kn, kd)
        print(f"  {name:<26} {s:>5} {kn:>10.0f} {kd:>10.0f} "
              f"{100*(1-kd/kn):>7.1f}%")
    print("""
  The saving is LARGER for the high-query configuration, which is exactly the
  low-blowup, prover-optimal one. Deduplication therefore narrows the gap
  between the two endpoints that pq_design.py presented as a hard tradeoff.""")

    a = out["Goldilocks^5 blowup 16"]
    b = out["Goldilocks^5 blowup 2"]
    print(f"  proof-size ratio (blowup 2 : blowup 16)")
    print(f"      naive  {b[0]/a[0]:.2f}x   ->   dedup  {b[1]/a[1]:.2f}x")
    print("""
  So the prover-optimal configuration is meaningfully less expensive in
  bandwidth than the naive model implied, while still running the LDE at 1.00x
  instead of 9.14x. For anything prover-bound, blowup 2 with deduplicated paths
  is the better system.""")

    sec("4. WHAT ELSE IS STILL OVERCHARGED")
    print("""
  Three further reductions this repo has not modelled, all standard:

  * MERKLE CAPS. Plonky2 ships cap_height = 4: stop the tree 4 levels early and
    publish the 2^4 cap. Saves min(cap_height, remaining) hashes on every path,
    and composes with deduplication (it removes exactly the levels that
    deduplication has already made cheap, so the two overlap -- the joint saving
    is less than the sum).

  * BATCHED OPENINGS ACROSS TREES. The trace and composition commitments are
    opened at the SAME query positions. Their paths are independent trees, so
    they do not share nodes, but a single combined tree over interleaved leaves
    would let them share -- at the cost of coupling the commitment schedule.

  * FINAL-LAYER TRUNCATION. `final` is sent in the clear and is 2^(nu - rounds)
    elements. Folding fewer times leaves a larger final layer but fewer Merkle
    layers; there is an optimum, and NADO fixes it at blowup with
    log_last_layer_degree_bound rather than optimising it.

  None of these change SOUNDNESS -- they are all pure encoding wins, which is
  what makes them the right place to look once the soundness parameters are
  pinned by Theorem 2 and the PQ halving.""")


if __name__ == "__main__":
    report()
