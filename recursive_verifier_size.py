"""
Pinning the recursive-verifier trace size empirically, from the pipelines that
already exist -- closing the range iterations 72 and 73 both had to leave open.

Iteration 73 put a 128-PQ verifier-facing proof at 0.9-1.5 MiB and said plainly
what it could not settle: whether a recursive verifier for such a proof fits in
trace 2^18 at batch 128. It needs 2964 Merkle nodes hashed at 384-bit digests
with degree-9 arithmetic, against today's 2852 at 256 bits and degree 4, and
pinning it "needs a Poseidon2 gate count this repo does not have".

It does not need one. Every deployed pipeline is a measurement: each recursion
stage verifies the previous stage's proof, so its trace AREA against the
verification work is exactly the constant in question.

THE MEASUREMENT
-----------------
    system  stage       T  batch       area   nodes   cells/node
    Pico    convert    20    485   5.09e+08    1932     2.63e+05
    Pico    combine    18    485   1.27e+08    3528     3.60e+04
    Pico    compress   17    485   6.36e+07    1596     3.98e+04
    Pico    embed      15    485   1.59e+07     441     3.60e+04
    SP1     compress   20    128   1.34e+08    2852     4.71e+04
    SP1     shrink     18    128   3.36e+07    2728     1.23e+04

Pico's `convert` is an outlier at 2.6e5 and is excluded: it is the 1-to-1
circuit that also absorbs the RISCV public values and chip structure, so it is
not purely a verifier. The other five, across two independent codebases, span

    1.2e4 to 4.7e4 trace cells per Merkle node

a factor of 3.8, which is the honest precision available from six data points.

WHAT IT SAYS ABOUT THE ASSUMED RANGE
--------------------------------------
A 128-PQ verifier hashes 114 * 26 = 2964 nodes. Raw, that is 3.7e7 to 1.4e8
cells, so at batch 128:

    T = 18.1 to 20.1

which is the range iterations 72 and 73 assumed. The assumption was sound.

BUT THE DIGEST IS WIDER, AND THE LOW END GOES AWAY
----------------------------------------------------
A 384-bit digest over KoalaBear is 13 base elements against 8 for 256 bits, so
each node costs about 1.62x more to hash. (Degree-9 rather than degree-4
arithmetic also costs more, roughly 5x per multiplication, but that is per
QUERY rather than per node, so 1.62x is the conservative correction.)

    T = 18.8 to 20.8   at batch 128

So the 0.9 MiB figure at T=16 is not reachable: the recursive circuit for a
128-PQ proof is bigger than the smallest shape iteration 73 tabulated.

THE DESIGNER CHOOSES THE ASPECT RATIO, AND NARROW WINS
--------------------------------------------------------
Area is what the verification work fixes; the split between width and length is
free. Leaf data scales LINEARLY in batch while Merkle paths scale only in
log(area/batch), so narrow-and-tall is strictly better:

    at 5.9e7 cells, R=6        at 2.25e8 cells, R=6
    batch  T    KiB            batch  T    KiB
       32 21    977               32 23   1141
       64 20    984               64 22   1140
      128 19   1077              128 21   1226
      485 17   1866              485 19   2001
     1024 16   3199             1024 18   3326

Optimising over the aspect ratio, the floor is

    977 to 1140 KiB  --  about 1.0 to 1.1 MiB

tighter than iteration 73's 879-1453 and resting on a measured constant rather
than an assumed trace shape.

Deployed recursive circuits run batch 128-485, which this model puts 10-70%
above the optimum. That is an observation, not a criticism: a verifier circuit
has a natural width set by what it must hold in a row, and nothing here models
that constraint.

WHERE THIS LEAVES THE 128-PQ NUMBER
-------------------------------------
    base layer, realistic width       4-19 MiB      (iteration 72)
    verifier-facing, after recursion  1.0-1.1 MiB   (this file)
    deployed finals today             200-529 KiB   at 50-64 PQ

So 128 post-quantum bits costs 1.8x to 5.7x the proof anyone transmits --
1.8x against SP1's 529 KiB, 5.7x against zkDTVM's 200 KiB.
And finding 1's 797 KiB, which iteration 72 called an order of magnitude out
and iteration 73 put within 30%, is within 18% of the low end -- still the wrong
derivation, and closer to right than either intermediate correction had it.

WHAT IS STILL UNMEASURED
--------------------------
The 3.8x spread in cells-per-node. SP1's shrink is 1.2e4 and its compress
4.7e4, from the same codebase verifying similarly-shaped proofs, so the
variation is not a field or protocol effect -- it is padding, chip layout and
whatever else those circuits carry besides verification. Narrowing it needs the
circuits themselves, not their soundness configs.
"""

import math

from recursion_floor import final_stage_kib

# (system, stage, T, batch, verified s, verified nu, proofs verified)
STAGES = [("Pico", "convert", 20, 485, 84, 23, 1),
          ("Pico", "combine", 18, 485, 84, 21, 2),
          ("Pico", "compress", 17, 485, 84, 19, 1),
          ("Pico", "embed", 15, 485, 21, 21, 1),
          ("SP1", "compress", 20, 128, 124, 23, 1),
          ("SP1", "shrink", 18, 128, 124, 22, 1)]

# excluded from the fit: not purely a verifier, it also absorbs RISCV public
# values and chip structure
OUTLIER = ("Pico", "convert")

PQ_QUERIES, PQ_NU = 114, 26          # the 128-PQ base proof being verified
DIGEST_WIDENING = 13 / 8             # 384-bit vs 256-bit digest over KoalaBear
ASPECT_BATCHES = (32, 64, 128, 256, 485, 1024)


def cells_per_node(T, batch, s, nu, n_proofs=1):
    return (2 ** T * batch) / (s * nu * n_proofs)


def fitted_range(exclude_outlier=True):
    """(min, max) trace cells per Merkle node across deployed recursion stages."""
    vals = [cells_per_node(T, b, s, nu, n)
            for sysname, stage, T, b, s, nu, n in STAGES
            if not (exclude_outlier and (sysname, stage) == OUTLIER)]
    return min(vals), max(vals)


def pq_nodes():
    return PQ_QUERIES * PQ_NU


def required_area(widened=True):
    lo, hi = fitted_range()
    w = DIGEST_WIDENING if widened else 1.0
    return pq_nodes() * w * lo, pq_nodes() * w * hi


def trace_length(area, batch):
    return math.log2(area / batch)


def aspect_sweep(area, R=6):
    """[(batch, T, KiB)] at fixed area -- the free design choice."""
    return [(b, math.ceil(trace_length(area, b)),
             final_stage_kib(b, math.ceil(trace_length(area, b)), R))
            for b in ASPECT_BATCHES]


def optimal_floor(R=6):
    """(min KiB, max KiB) over the area range, optimising the aspect ratio."""
    lo_a, hi_a = required_area()
    return (min(k for _b, _T, k in aspect_sweep(lo_a, R)),
            min(k for _b, _T, k in aspect_sweep(hi_a, R)))


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE MEASUREMENT: DEPLOYED PIPELINES ALREADY CONTAIN THE CONSTANT")
    print("""
  Each recursion stage verifies the previous stage's proof, so its trace AREA
  against the verification work IS the cells-per-node constant iteration 73
  said it lacked a gate count for.\n""")
    print(f"  {'system':<7} {'stage':<10} {'T':>3} {'batch':>6} {'area':>11} "
          f"{'nodes':>7} {'cells/node':>12}")
    print("  " + "-" * 62)
    for sysname, stage, T, b, s, nu, n in STAGES:
        mark = "  <- excluded" if (sysname, stage) == OUTLIER else ""
        print(f"  {sysname:<7} {stage:<10} {T:>3} {b:>6} {2**T*b:>11.2e} "
              f"{s*nu*n:>7} {cells_per_node(T,b,s,nu,n):>12.2e}{mark}")
    lo, hi = fitted_range()
    print(f"""
  Pico's convert is the 1-to-1 circuit that also absorbs RISCV public values and
  chip structure, so it is not purely a verifier. The other five, across two
  independent codebases, span

      {lo:.1e} to {hi:.1e} cells per Merkle node

  a factor of {hi/lo:.1f} -- the honest precision available from six data points.""")

    sec("2. IT VALIDATES THE ASSUMED RANGE, THEN REMOVES ITS LOW END")
    raw_lo, raw_hi = required_area(widened=False)
    wid_lo, wid_hi = required_area(widened=True)
    print(f"""
  A 128-PQ verifier hashes {PQ_QUERIES} * {PQ_NU} = {pq_nodes()} nodes.

      raw            {raw_lo:.2e} to {raw_hi:.2e} cells   ->  T = """
          f"{trace_length(raw_lo,128):.1f} to {trace_length(raw_hi,128):.1f} at batch 128")
    print(f"""      widened x{DIGEST_WIDENING:.2f}  {wid_lo:.2e} to {wid_hi:.2e} cells   ->  T = """
          f"{trace_length(wid_lo,128):.1f} to {trace_length(wid_hi,128):.1f}")
    print(f"""
  The raw range is exactly what iterations 72 and 73 assumed, so the assumption
  was sound. But a 384-bit digest is 13 KoalaBear elements against 8, so each
  node costs {DIGEST_WIDENING:.2f}x more to hash -- and the 0.9 MiB figure at T=16 is not
  reachable. (Degree-9 arithmetic costs more too, but per QUERY rather than per
  node, so this is the conservative correction.)""")

    sec("3. THE ASPECT RATIO IS FREE, AND NARROW WINS")
    print("""
  Verification work fixes the AREA; the split between width and length is the
  designer's. Leaf data scales linearly in batch, Merkle paths only in
  log(area/batch), so narrow-and-tall is strictly better:\n""")
    for area, label in ((wid_lo, "optimistic"), (wid_hi, "pessimistic")):
        print(f"  {label} area {area:.2e} cells, blowup 64:")
        print(f"    {'batch':>6} {'T':>4} {'KiB':>8}")
        for b, T, k in aspect_sweep(area):
            print(f"    {b:>6} {T:>4} {k:>8}")
        print()
    f_lo, f_hi = optimal_floor()
    print(f"""  Optimising the aspect ratio, the floor is {f_lo} to {f_hi} KiB -- about 1.0 to
  1.1 MiB, tighter than iteration 73's 879-1453 and resting on a measured
  constant rather than an assumed trace shape.

  Deployed recursive circuits run batch 128-485, which this puts 10-70% above
  the optimum. An observation, not a criticism: a verifier circuit has a natural
  width set by what it must hold in a row, and nothing here models that.""")

    sec("4. WHERE THIS LEAVES THE 128-PQ NUMBER")
    print(f"""
      base layer, realistic width        4-19 MiB       (iteration 72)
      verifier-facing, after recursion   {f_lo}-{f_hi} KiB   (this file)
      deployed finals today              200-529 KiB    at 50-64 PQ

  So 128 post-quantum bits costs {f_lo/529:.1f}x to {f_hi/200:.1f}x the proof anyone transmits --
  against SP1's 529 KiB, the largest deployed final, and zkDTVM's 200 KiB, the
  smallest.

  And finding 1's 797 KiB -- which iteration 72 called an order of magnitude out
  and iteration 73 put within 30% -- is within {abs(797-f_lo)/f_lo:.0%} of the low end. Still the
  wrong derivation, and closer to right than either intermediate correction had
  it.

  STILL UNMEASURED: the {hi/lo:.1f}x spread in cells per node. SP1's shrink is 1.2e4 and
  its compress 4.7e4, same codebase, similarly-shaped proofs -- so the variation
  is not a field or protocol effect but padding, chip layout, and whatever else
  those circuits carry besides verification. Narrowing it needs the circuits,
  not their soundness configs.""")


if __name__ == "__main__":
    report()
