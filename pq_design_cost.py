"""
What a 128-PQ-bit STARK actually costs -- and a correction to finding 1's
"~800 KiB", which omits the term that dominates every real proof.

Proposition 11 (iteration 71) reduced Johnson-regime soundness to s*R/2 + g,
with the commit side irrelevant at the optimum. Iteration 61 verified a
proof-size model against all 122 published figures. Together they let this repo
answer, for the first time with both sides checked, what a 128-PQ-bit design
costs.

THE THREE CONSTRAINTS
-----------------------
128 PQ bits needs 256 classical, since finding 2's halving is exact for the
query phase (its bound is attained, Chiesa-Yogev).

    1. QUERY     s*R/2 + g = 256                    (Proposition 11)
    2. COMMIT    E >= 256 + nu - 2 - g_commit       (ceiling equation, a = 1)
    3. MERKLE    digest >= 3 * 128 = 384 bits       (BHT, finding 1)

Constraint 2 gives E >= 274-280 at deployed nu, so KoalaBear^9 (279 bits) or
^10 (310) -- which reproduces finding 1's "degree 9-10" independently, from
Proposition 11 rather than from the commit optimisation it was derived by.

Constraint 1 is a one-parameter family. At g = 28:

    blowup       2     4     8    16    32
    queries    456   228   152   114    91

THE COST, AT KoalaBear^9 WITH A 384-BIT DIGEST
------------------------------------------------
Trace 2^22, batch 1000 columns, folding 2:

    R  blowup    s   nu   LDE     expected      vs R=1
    1       2  456   23    2x    18319 KiB       1.00x
    2       4  228   24    4x     9496 KiB       0.52x
    3       8  152   25    8x     6531 KiB       0.36x
    4      16  114   26   16x     5045 KiB       0.28x
    5      32   92   27   32x     4191 KiB       0.23x

Queries fall as 1/R, but the domain grows as 2^R and the LDE with it, so proof
size falls sublinearly while prover cost rises geometrically. Blowup 16 is the
knee: 3.6x smaller proofs than blowup 2 for 8x the encoding.

THE CORRECTION: "~800 KiB" IS A TWO-COLUMN TRACE
--------------------------------------------------
README's finding 1 says degree 9-10 "reaches 128 PQ bits for ~800 KiB". That
comes from pq_design.py, whose cheapest configuration is Goldilocks^5, blowup
16, 113 queries -> 797 KiB. Its size model is

    value_bytes = s * (n_base_trees * w + rounds * 2 * ext_words * w)

with n_base_trees = 2 and w one BASE field element. That charges two base
elements per query at the initial commitment -- a trace TWO COLUMNS WIDE. The
function's docstring says "Merkle paths dominate", which is true there and only
there.

Every real zkVM is three to four orders of magnitude wider. From the tomls:
ZisK's Rom is 18, its Dma 46, Pico's convert 485, Airbender 1225, ZisK's
Keccakf 4065, OpenVM's app 80000. At those widths the leaf data is 60-99.6% of
the proof:

    batch      exact KiB    leaf share
        2           1170          0.7%
       46           1341         13.3%
      485           3045         61.8%
     1225           5918         80.4%
     4065          16945         93.1%
    80000         311768         99.6%

Reproducing pq_design's own winning configuration in the verified model gives
1188 KiB at a ONE-column trace -- already 1.5x its 797 -- and 3324 KiB at
Pico's width, 6591 at Airbender's.

So the honest statement is: 797 KiB is the Merkle-path cost of proving a
two-column trace at 128 PQ bits. It is not a zkVM proof size, and finding 1
should not be read as one. A realistic 128-PQ zkVM proof is MEGABYTES: 5 MiB at
Airbender's width and blowup 16, 4 MiB at blowup 32.

WHY THIS MATTERS RATHER THAN BEING A QUIBBLE
----------------------------------------------
The 800 KiB figure is finding 1's entire case that 128 PQ bits is affordable
today. At 5-19 MiB the conclusion changes: post-quantum security at this
security level is reachable with existing primitives, and it costs one to two
orders of magnitude in proof size over what deployed systems ship (OpenVM's
final proof is 7687 KiB at 100 CLASSICAL bits; this is 5045 KiB at 128 PQ but
for a single circuit at 1000 columns, not a whole pipeline).

The claim "no conjecture, no lattice" stands. The claim that it is nearly free
does not.

WHAT IS NOT CHECKED HERE
--------------------------
Recursion. Every deployed system's headline size is its LAST circuit after
several compression rounds (iteration 61), and the figures above are single
circuits. A recursive pipeline over a 128-PQ base could compress these the way
OpenVM2's six stages take 26175 KiB down to 270. That is the obvious next
question and this file does not answer it -- it prices the base layer only.
"""

import math

from proof_size_exact import fri_proof_bits

KIB = 8 * 1024

TARGET_PQ = 128
TARGET_CLASSICAL = 2 * TARGET_PQ          # finding 2: the halving is exact here

# a 128-PQ design point: KoalaBear^9, BHT-safe digest
DESIGN = dict(hash_bits=384, elem_bits=279, trace_log=22, grinding=28)

# pq_design.py's own cheapest configuration, for the comparison
PQ_DESIGN_BEST = dict(field="Goldilocks^5", elem_bits=320, R=4, s=113,
                      claimed_kib=797)

# batch sizes from the zkvm tomls (iteration 61)
REAL_BATCHES = [(2, "pq_design assumes this"), (18, "ZisK Rom"),
                (46, "ZisK Dma"), (485, "Pico convert"), (1225, "Airbender"),
                (4065, "ZisK Keccakf"), (80000, "OpenVM app")]


def queries_needed(R, g=28, target=TARGET_CLASSICAL):
    """Proposition 11 inverted: s such that s*R/2 + g = target."""
    return math.ceil(2 * (target - g) / R)


def field_needed(nu, g_commit=0, target=TARGET_CLASSICAL):
    """Ceiling equation at a = 1, log2 C = -2."""
    return target + nu - 2 - g_commit


def extension_degree(E_needed, base_bits=31):
    return math.ceil(E_needed / base_bits)


def digest_needed(target_pq=TARGET_PQ, exponent=3):
    """BHT quantum collision finding costs 2^(lambda/3)."""
    return exponent * target_pq


def design_size_kib(R, batch, hash_bits=None, elem_bits=None, trace_log=None,
                    g=None, expected=True):
    """Proof size for a 128-PQ single circuit at blowup 2^R and given width."""
    hb = DESIGN["hash_bits"] if hash_bits is None else hash_bits
    eb = DESIGN["elem_bits"] if elem_bits is None else elem_bits
    T = DESIGN["trace_log"] if trace_log is None else trace_log
    gg = DESIGN["grinding"] if g is None else g
    s = queries_needed(R, gg)
    nu = T + R
    return fri_proof_bits(hb, eb, batch, s, 2 ** nu, [2] * nu,
                          2.0 ** -R, expected) // KIB


def leaf_share(R, batch):
    """Fraction of the proof that is leaf data rather than Merkle paths."""
    s = queries_needed(R, DESIGN["grinding"])
    nu = DESIGN["trace_log"] + R
    total = fri_proof_bits(DESIGN["hash_bits"], DESIGN["elem_bits"], batch, s,
                           2 ** nu, [2] * nu, 2.0 ** -R, True)
    return s * batch * DESIGN["elem_bits"] / total


def pq_design_reproduced(batch):
    """pq_design's winning config, priced in the verified model."""
    d = PQ_DESIGN_BEST
    nu = DESIGN["trace_log"] + d["R"]
    return fri_proof_bits(DESIGN["hash_bits"], d["elem_bits"], batch, d["s"],
                          2 ** nu, [2] * nu, 2.0 ** -d["R"], True) // KIB


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE THREE CONSTRAINTS FOR 128 PQ BITS")
    print(f"""
  128 PQ needs {TARGET_CLASSICAL} classical -- the halving is exact for the query phase,
  whose bound is attained (Chiesa-Yogev, finding 2).

      1. QUERY    s*R/2 + g = {TARGET_CLASSICAL}                 (Proposition 11)
      2. COMMIT   E >= {TARGET_CLASSICAL} + nu - 2 - g_commit     (ceiling equation, a=1)
      3. MERKLE   digest >= 3 * {TARGET_PQ} = {digest_needed()} bits        (BHT, finding 1)
""")
    print(f"  {'nu':>4} {'E needed':>10} {'KoalaBear degree':>18} {'bits':>6}")
    print("  " + "-" * 42)
    for nu in (20, 23, 26):
        E = field_needed(nu)
        d = extension_degree(E)
        print(f"  {nu:>4} {E:>10} {d:>18} {31*d:>6}")
    print(f"""
  Degree 9-10, reproducing finding 1 independently -- from Proposition 11
  rather than from the commit optimisation finding 1 was derived by.

  Constraint 1 is a one-parameter family. At g = {DESIGN['grinding']}:\n""")
    print("  " + "".join(f"{'blowup ' + str(2**R):>12}" for R in (1, 2, 3, 4, 5)))
    print("  " + "".join(f"{queries_needed(R):>12}" for R in (1, 2, 3, 4, 5))
          + "   queries")

    sec("2. THE COST, AT KoalaBear^9 WITH A 384-BIT DIGEST")
    print(f"\n  trace 2^{DESIGN['trace_log']}, batch 1000 columns, folding 2\n")
    print(f"  {'R':>3} {'blowup':>7} {'s':>5} {'nu':>4} {'LDE':>6} "
          f"{'expected':>11} {'worst':>10} {'vs R=1':>8}")
    print("  " + "-" * 62)
    base = design_size_kib(1, 1000)
    for R in (1, 2, 3, 4, 5):
        e, w = design_size_kib(R, 1000), design_size_kib(R, 1000, expected=False)
        print(f"  {R:>3} {2**R:>7} {queries_needed(R):>5} "
              f"{DESIGN['trace_log']+R:>4} {str(2**R)+'x':>6} {e:>11} {w:>10} "
              f"{e/base:>7.2f}x")
    print("""
  Queries fall as 1/R, the domain grows as 2^R, so size falls sublinearly while
  prover cost rises geometrically. Blowup 16 is the knee.""")

    sec("3. THE CORRECTION: \"~800 KiB\" IS A TWO-COLUMN TRACE")
    print(f"""
  pq_design.proof_kib charges

      value_bytes = s * (n_base_trees * w + rounds * 2 * ext_words * w)

  with n_base_trees = 2 and w one BASE element -- two base elements per query at
  the initial commitment, i.e. a trace TWO COLUMNS WIDE. Its docstring says
  "Merkle paths dominate", true there and only there.\n""")
    print(f"  {'batch':>8} {'exact KiB':>11} {'leaf share':>12}   from the tomls")
    print("  " + "-" * 60)
    for b, who in REAL_BATCHES:
        print(f"  {b:>8} {design_size_kib(4, b):>11} {leaf_share(4, b):>11.1%}   {who}")
    print(f"""
  Reproducing pq_design's own winning configuration ({PQ_DESIGN_BEST['field']},
  blowup {2**PQ_DESIGN_BEST['R']}, {PQ_DESIGN_BEST['s']} queries) in the verified model:\n""")
    print(f"  {'batch':>8} {'exact KiB':>11} {'vs its ' + str(PQ_DESIGN_BEST['claimed_kib']):>12}")
    print("  " + "-" * 34)
    for b in (1, 2, 485, 1225):
        k = pq_design_reproduced(b)
        print(f"  {b:>8} {k:>11} {k/PQ_DESIGN_BEST['claimed_kib']:>11.1f}x")
    print("""
  1.5x even at ONE column. So 797 KiB is the Merkle-path cost of proving a
  two-column trace at 128 PQ bits. It is not a zkVM proof size, and finding 1
  should not be read as one.""")

    sec("4. WHAT CHANGES, AND WHAT DOES NOT")
    print("""
  The 800 KiB figure is finding 1's entire case that 128 PQ bits is affordable
  today. At 5-19 MiB the conclusion shifts: post-quantum security at this level
  is REACHABLE with existing primitives -- collision resistance plus the random
  oracle, no conjecture, no lattice -- and it costs one to two orders of
  magnitude in proof size over what ships now.

  "No conjecture, no lattice" stands. "Nearly free" does not.

  NOT CHECKED HERE: recursion. Every deployed system's headline size is its LAST
  circuit after several compression rounds (iteration 61), and these are single
  circuits. A recursive pipeline over a 128-PQ base could compress them the way
  OpenVM2's six stages take 26175 KiB to 270. That is the next question; this
  file prices the base layer only.""")


if __name__ == "__main__":
    report()
