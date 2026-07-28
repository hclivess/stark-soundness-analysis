"""
Every published proof size, reconstructed exactly -- and three corrections it
forces, one of them to iteration 60.

Iterations 48 and 56 verified SOUNDNESS figures term by term against soundcalc.
The proof-size model was never verified against anything: iteration 60 compared
one ratio for one system and inferred the rest. soundcalc's reports publish a
per-circuit expected and worst-case size for every circuit of every zkVM, and
the tomls carry every input the formula needs. So the whole thing is checkable.

THE RESULT: 110 FIGURES, ZERO DEVIATION
-----------------------------------------
Reimplementing get_FRI_proof_size_bits (soundcalc/pcs/fri.py:13) from the tomls
alone reproduces all 55 FRI circuits across six systems, both columns, exactly:

    Pico        5 circuits    riscv 2225/2583 ... embed 232/281
    Airbender   1 circuit     1836/1951
    RISC0       1 circuit     331/380
    Miden       1 circuit     112/149
    OpenVM      3 circuits    app 234635/235651 ... internal 7687/8231
    ZisK       44 circuits    Dma 748/1142 ... Final_Compressed 269/313

Not one KiB out of 110. Every input -- hash_size_bits, field, batch_size,
num_queries, trace_length, rho, fri_folding_factors -- comes from the toml; the
only thing supplied here is the formula. This is a stronger validation than the
soundness side has, because proof size has no regime ambiguity and no derived
`m`: it is arithmetic on declared parameters.

CORRECTION 1 (to iteration 60): THE SUMMARY REPORTS THE FINAL CIRCUIT
-----------------------------------------------------------------------
Iteration 60 found that SP1's summary ratio (40.4%) exceeds its single-circuit
dedup saving, which is impossible if both proofs carry identical leaf data, and
inferred the summary figure "aggregates 3 circuits".

That inference was wrong. The summary reports the LAST circuit, not a sum:

    Pico     summary 232/281   = embed             (last of 5)
    OpenVM   summary 7687/8231 = internal          (last of 3)
    ZisK     summary 269/313   = Final_Compressed  (last of 44)
    SP1      summary 529/887   = shrink            (last of 3)

SP1's core circuit is 918/1479 -- which is exactly the figure iteration 48 read
out of soundcalc-lean's sp1CoreJagged, from a completely different source. The
ratio anomaly is not aggregation: it is that systems.py records SP1's CORE
parameters while the summary quotes its SHRINK circuit, and the two have
different query counts and depths. A per-circuit comparison is the only valid
one.

CORRECTION 2 (also to iteration 60): THE TREE IS OVER THE LDE DOMAIN
----------------------------------------------------------------------
merkle_exact.CONFIGS said "(name, queries, log2 domain size) -- from systems.py,
T + R" and then listed the TRACE length T. The Merkle tree is built over the
low-degree extension, of size 2^(T+R). Every depth was short by R, confirmed
directly against the tomls: Pico's riscv has trace_length 2^22 and rho 0.5, so
D = 2^23 and the initial tree has depth 23, not 22.

Correcting it moves the deployed dedup band DOWN, because the extra levels are
below saturation and each query needs its own sibling there:

    system      at T     at nu    shift
    SP1        36.9%    33.7%     -3.2
    OpenVM     36.6%    35.1%     -1.5
    Airbender  30.1%    28.9%     -1.2
    Pico       32.5%    31.1%     -1.4
    ZisK       41.3%    39.5%     -1.9
    RISC Zero  30.1%    27.5%     -2.6
    Miden      29.8%    25.6%     -4.3

So the band is 26-40%, not the 30-41% iteration 60 put in README. The shift is
largest exactly where R is largest -- Miden's blowup 8 costs it 4.3 points --
which is the signature of the error and not a coincidence. Iteration 60's
direction was right (README's old 33-52% was too high) and its numbers were not.

CORRECTION 3: VENUS IS NOT PARAMETER-IDENTICAL TO ZisK
---------------------------------------------------------
README excludes Venus from the seven-system test set as "a parameter-identical
duplicate of ZisK". Diffing the two tomls:

    40 of 44 circuits         byte-identical
    3 circuits                differ only in a `group` label (helper vs basic)
    1 circuit -- Final        genuinely differs

Venus's Final is wider: 135 columns against 114, batch_size 158 against 139,
161 constraints against 154, and its own toml records 335.21 KB against ZisK's
327.71 KB. They are the same codebase at different versions (Venus 0.1.6, ZisK
0.16.1), so EXCLUDING Venus remains right -- it is not an independent design
decision, which is what Theorem 7's 7/7 test needs. But "parameter-identical" is
false, and the justification is now stated as what it is.

A SMALL ASYMMETRY INSIDE soundcalc
------------------------------------
utils.py:42 charges the worst case min(tuple_size*elem, hash_size) for the leaf's
sibling -- if a leaf is smaller than a digest, send it raw. The expected-case
function (utils.py:59-67) has no such term and charges a full hash at every
level including the leaf. So the two are not quite the same accounting.

It bites only where a folded tuple is smaller than the digest, which across all
deployed configs means folding factor 2 with a 124-bit element and a 256-bit
hash -- OpenVM alone. Worth 8 bits per query per round: 193 * 23 * 8 = 4.3 KiB
against a 235,651 KiB proof, or 0.002%. Iteration 60's identification of the
worst case with `naive_auth_nodes = s*depth` is therefore exact in NODE COUNT,
which is what merkle_dedup measures, and off by at most 8 bits per query per
round in BITS. Recorded rather than corrected: nothing rests on it.
"""

import math

# base field primes, for element sizing (fields.py: ceil(log2 p) * ext degree)
PRIMES = {"KoalaBear": 2 ** 31 - 2 ** 24 + 1, "BabyBear": 15 * 2 ** 27 + 1,
          "M31": 2 ** 31 - 1, "Goldilocks": 2 ** 64 - 2 ** 32 + 1}

F864, F8888 = [8, 8, 8, 8, 8, 4], [8, 8, 8, 8, 8, 8]   # ZisK folding schedules

# (system, hash_size_bits, field) then per circuit:
# (name, rho, log2 trace_length, batch_size, num_queries, folding_factors)
_SYSTEM_ROWS = [
    ("Pico", 248, "KoalaBear^4", [
        ("riscv", 0.5, 22, 1435, 84, [2] * 22), ("convert", 0.5, 20, 485, 84, [2] * 20),
        ("combine", 0.5, 18, 485, 84, [2] * 18), ("compress", 0.0625, 17, 485, 21, [2] * 17),
        ("embed", 0.0625, 15, 485, 21, [2] * 15)]),
    ("Airbender", 256, "M31^4", [
        ("generalized", 0.5, 24, 1225, 87, [16, 16, 16, 8, 8])]),
    ("RISC0", 256, "BabyBear^4", [("main", 0.25, 21, 283, 50, [16] * 4)]),
    ("Miden", 256, "Goldilocks^2", [("main", 0.125, 18, 100, 27, [4] * 7)]),
    ("OpenVM", 256, "BabyBear^4", [
        ("app", 0.5, 23, 80000, 193, [2] * 23), ("leaf", 0.5, 23, 80000, 193, [2] * 23),
        ("internal", 0.25, 21, 4000, 118, [2] * 21)]),
    ("ZisK", 256, "Goldilocks^3", [
        ("Dma", 0.5, 21, 46, 229, F864), ("DmaMemCpy", 0.5, 21, 33, 229, F864),
        ("DmaInputCpy", 0.5, 21, 27, 229, F864), ("Dma64Aligned", 0.5, 21, 62, 230, F864),
        ("Dma64AlignedInputCpy", 0.5, 21, 44, 229, F864), ("Dma64AlignedMemSet", 0.5, 21, 30, 229, F864),
        ("Dma64AlignedMem", 0.5, 21, 46, 229, F864), ("Dma64AlignedMemCpy", 0.5, 21, 52, 229, F864),
        ("DmaUnaligned", 0.5, 21, 52, 229, F864), ("DmaPrePost", 0.5, 21, 83, 230, F864),
        ("DmaPrePostMemCpy", 0.5, 21, 70, 230, F864), ("DmaPrePostInputCpy", 0.5, 21, 44, 229, F864),
        ("Main", 0.5, 22, 61, 230, F8888), ("Rom", 0.5, 22, 18, 221, F8888),
        ("Mem", 0.5, 22, 29, 230, F8888), ("RomData", 0.5, 21, 19, 229, F864),
        ("InputData", 0.5, 21, 27, 229, F864), ("MemAlign", 0.5, 21, 59, 230, F864),
        ("MemAlignByte", 0.5, 22, 25, 229, F8888), ("MemAlignReadByte", 0.5, 22, 18, 229, F8888),
        ("MemAlignWriteByte", 0.5, 22, 23, 229, F8888), ("Arith", 0.5, 21, 64, 230, F864),
        ("Binary", 0.5, 22, 49, 230, F8888), ("BinaryAdd", 0.5, 22, 18, 229, F8888),
        ("BinaryExtension", 0.5, 22, 40, 230, F8888), ("Add256", 0.5, 20, 69, 229, [8]*5),
        ("ArithEq", 0.5, 20, 470, 231, [8]*5), ("ArithEq384", 0.5, 20, 536, 232, [8]*5),
        ("Keccakf", 0.5, 17, 4065, 217, [8]*4), ("Sha256f", 0.5, 18, 1265, 231, [8,8,8,8,4]),
        ("Poseidon2", 0.25, 17, 182, 114, [8,8,8,8,4]), ("Blake2br", 0.5, 18, 651, 230, [8,8,8,8,4]),
        ("SpecifiedRanges", 0.5, 20, 107, 229, [8]*5), ("VirtualTable0", 0.5, 21, 69, 230, F864),
        ("VirtualTable1", 0.5, 21, 90, 230, F864), ("DmaPrePost-compressor", 0.25, 18, 198, 110, [8]*5),
        ("ArithEq-compressor", 0.25, 18, 198, 110, [8]*5), ("ArithEq384-compressor", 0.25, 18, 198, 110, [8]*5),
        ("Keccakf-compressor", 0.25, 20, 198, 110, F864), ("Sha256f-compressor", 0.25, 19, 198, 110, [8]*5),
        ("Blake2br-compressor", 0.25, 18, 198, 110, [8]*5), ("Recursive2", 0.125, 17, 145, 73, [8]*5),
        ("Final", 0.03125, 16, 139, 43, [16]*4), ("Final_Compressed", 0.0625, 15, 145, 54, [8]*3)]),
]

SYSTEMS = {n: (h, f, c) for n, h, f, c in _SYSTEM_ROWS}

# soundcalc reports/<vm>.md, "**Proof Size:** X KiB (expected) / Y KiB (worst case)"
PUBLISHED = {
    "Pico": [(2225, 2583), (934, 1255), (861, 1146), (253, 308), (232, 281)],
    "Airbender": [(1836, 1951)], "RISC0": [(331, 380)], "Miden": [(112, 149)],
    "OpenVM": [(234635, 235651), (234635, 235651), (7687, 8231)],
    "ZisK": [
        (748, 1142), (679, 1072), (646, 1040), (838, 1233), (738, 1131), (662, 1056),
        (748, 1142), (781, 1174), (781, 1174), (951, 1346), (881, 1276), (738, 1131),
        (890, 1292), (635, 1019), (718, 1120), (603, 997), (646, 1040), (821, 1217),
        (694, 1093), (656, 1056), (683, 1082), (848, 1244), (826, 1227), (656, 1056),
        (777, 1179), (816, 1165), (2994, 3346), (3366, 3720), (20975, 21244), (7215, 7549),
        (682, 832), (3874, 4207), (1020, 1369), (875, 1270), (989, 1384), (726, 871),
        (726, 871), (726, 871), (771, 940), (743, 892), (726, 871), (398, 487),
        (253, 292), (269, 313)],
}

# summary.md system figure vs the LAST circuit's figure -- correction 1
SUMMARY_IS_LAST = {"Pico": (232, 281), "OpenVM": (7687, 8231),
                   "ZisK": (269, 313), "SP1": (529, 887)}
SP1_CIRCUITS = [(918, 1479), (735, 1267), (529, 887)]  # core, compress, shrink

# Venus vs ZisK, from the toml diff -- correction 3
VENUS_ZISK_DIFF = {"identical": 40, "group_label_only": 3, "genuine": 1,
                   "Final": {"num_columns": (135, 114), "batch_size": (158, 139),
                             "num_constraints": (161, 154),
                             "proof_size_kb": (335.21, 327.71)}}


def elem_bits(field):
    base, _, deg = field.partition("^")
    return math.ceil(math.log2(PRIMES[base])) * int(deg or 1)


def multi_proof_bits(num_leafs, k, tuple_size, eb, hb, expected):
    """soundcalc/common/utils.py:30-77, both branches."""
    depth = math.ceil(math.log2(num_leafs))
    if expected:
        nh = 0
        for d in range(1, depth + 1):
            nh += math.ceil(2 ** d * ((1 - 2.0 ** -d) ** k - (1 - 2.0 ** (1 - d)) ** k))
        return k * tuple_size * eb + nh * hb
    return k * (tuple_size * eb + min(tuple_size * eb, hb) + (depth - 1) * hb)


def fri_proof_bits(hb, eb, batch_size, q, D, folding, rho, expected):
    """soundcalc/pcs/fri.py:13-72."""
    n = D
    total = hb + multi_proof_bits(n, q, batch_size, eb, hb, expected)
    for f in folding:
        total += hb + multi_proof_bits(n // f, q, f, eb, hb, expected)
        n //= f
    return total + int(rho * n * eb)


def reconstruct(system):
    """Returns [(name, expected_kib, worst_kib)] for one system, from its toml."""
    hb, field, circuits = SYSTEMS[system]
    eb, out = elem_bits(field), []
    for name, rho, logT, bs, q, ff in circuits:
        D = int(2 ** logT / rho)
        out.append((name,
                    fri_proof_bits(hb, eb, bs, q, D, ff, rho, True) // (8 * 1024),
                    fri_proof_bits(hb, eb, bs, q, D, ff, rho, False) // (8 * 1024)))
    return out


def all_deviations():
    """Every (system, circuit, column) deviation from the published figure."""
    devs = []
    for sysname in SYSTEMS:
        for (nm, e, w), (pe, pw) in zip(reconstruct(sysname), PUBLISHED[sysname]):
            devs.append((sysname, nm, "expected", e - pe))
            devs.append((sysname, nm, "worst", w - pw))
    return devs


def leaf_asymmetry_bits(tuple_size, eb, hb):
    """Bits by which expected over-charges the leaf sibling vs the worst case."""
    return hb - min(tuple_size * eb, hb)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. 110 PUBLISHED FIGURES, RECONSTRUCTED FROM THE TOMLS ALONE")
    print(f"\n  {'system':<11} {'circuit':<14} {'exp':>8} {'pub':>8} {'d':>3} "
          f"{'worst':>8} {'pub':>8} {'d':>3}")
    print("  " + "-" * 68)
    for sysname in SYSTEMS:
        for (nm, e, w), (pe, pw) in zip(reconstruct(sysname), PUBLISHED[sysname]):
            print(f"  {sysname:<11} {nm[:13]:<14} {e:>8} {pe:>8} {e-pe:>+3} "
                  f"{w:>8} {pw:>8} {w-pw:>+3}")
    n_bad = sum(1 for *_, d in all_deviations() if d != 0)
    print(f"""
  Across all 55 FRI circuits and both columns: {n_bad} deviations out of {len(all_deviations())}.

  Every input comes from the toml. Only the formula is supplied here. This is a
  stronger check than the soundness side has -- no regime ambiguity, no derived
  `m`, just arithmetic on declared parameters.""")

    sec("2. CORRECTION TO ITERATION 60: THE SUMMARY IS THE LAST CIRCUIT")
    print("""
  Iteration 60 saw SP1's summary ratio exceed its single-circuit dedup saving --
  impossible if both proofs carry identical leaf data -- and inferred the figure
  "aggregates 3 circuits". It does not. The summary reports the LAST circuit:\n""")
    print(f"  {'system':<9} {'summary':>14} {'last circuit':>14}")
    print("  " + "-" * 40)
    for s, (e, w) in SUMMARY_IS_LAST.items():
        last = reconstruct(s)[-1][1:] if s in SYSTEMS else (e, w)
        print(f"  {s:<9} {f'{e}/{w}':>14} {f'{last[0]}/{last[1]}':>14}")
    print(f"""
  SP1's core circuit is {SP1_CIRCUITS[0][0]}/{SP1_CIRCUITS[0][1]} -- exactly the sp1CoreJagged figure
  iteration 48 read from soundcalc-lean, an unrelated source. So the anomaly is
  that systems.py records SP1's CORE parameters while the summary quotes its
  SHRINK circuit. Different query counts, different depths. Per-circuit is the
  only valid comparison.""")

    sec("3. CORRECTION TO ITERATION 60: DEPTH IS log2 OF THE LDE DOMAIN")
    from merkle_exact import soundcalc_auth_nodes
    rows = [("SP1", 124, 21, 2), ("OpenVM", 193, 23, 1), ("Airbender", 87, 24, 1),
            ("Pico", 84, 22, 1), ("ZisK", 229, 21, 1), ("RISC Zero", 50, 21, 2),
            ("Miden", 27, 18, 3)]
    print("""
  merkle_exact.CONFIGS said "T + R" and listed T. The tree is over the LDE, of
  size 2^(T+R) -- confirmed against the tomls: Pico's riscv is trace_length 2^22
  at rho 0.5, so D = 2^23 and the initial tree has depth 23.\n""")
    print(f"  {'system':<11} {'s':>5} {'T':>4} {'R':>3} {'at T':>8} {'at nu':>8} {'shift':>8}")
    print("  " + "-" * 50)
    band = []
    for nm, s, T, R in rows:
        a = 1 - soundcalc_auth_nodes(s, T) / (s * T)
        b = 1 - soundcalc_auth_nodes(s, T + R) / (s * (T + R))
        band.append(b)
        print(f"  {nm:<11} {s:>5} {T:>4} {R:>3} {a:>7.1%} {b:>7.1%} {b-a:>+8.1%}")
    print(f"""
  Deployed band {min(band):.0%}-{max(band):.0%}, not the {30}-41% iteration 60 wrote into README.
  The shift is largest where R is largest -- Miden's blowup 8 costs it 4.3
  points -- which is the signature of the error rather than a coincidence.
  Iteration 60's direction was right; its numbers were not.""")

    sec("4. VENUS IS NOT PARAMETER-IDENTICAL TO ZisK")
    d = VENUS_ZISK_DIFF
    print(f"""
  README excludes Venus as "a parameter-identical duplicate of ZisK". Diffing:

      {d['identical']} of 44 circuits    byte-identical
      {d['group_label_only']} circuits           differ only in a `group` label (helper vs basic)
      {d['genuine']} circuit -- Final   genuinely differs\n""")
    print(f"  {'field':<18} {'Venus':>10} {'ZisK':>10}")
    print("  " + "-" * 40)
    for k, (v, z) in d["Final"].items():
        print(f"  {k:<18} {v:>10} {z:>10}")
    print("""
  Same codebase at different versions (Venus 0.1.6, ZisK 0.16.1), so EXCLUDING
  Venus stays right -- it is not an independent design decision, which is what
  Theorem 7's 7/7 test needs. But "parameter-identical" is false.""")

    sec("5. A SMALL ASYMMETRY INSIDE soundcalc")
    print("""
  utils.py:42 charges the worst case min(tuple*elem, hash) for the leaf's
  sibling -- send a leaf raw if it is smaller than a digest. The expected-case
  function has no such term and charges a full hash at every level.

  It bites only where a folded tuple is smaller than the digest:\n""")
    print(f"  {'config':<26} {'ff':>3} {'tuple':>7} {'hash':>6} {'over-charge':>12}")
    print("  " + "-" * 58)
    for nm, eb, hb in (("Pico/SP1 KoalaBear^4", 124, 248),
                       ("OpenVM BabyBear^4", 124, 256),
                       ("ZisK Goldilocks^3", 192, 256),
                       ("Miden Goldilocks^2", 128, 256)):
        for ff in (2, 4):
            print(f"  {nm:<26} {ff:>3} {ff*eb:>7} {hb:>6} "
                  f"{leaf_asymmetry_bits(ff, eb, hb):>+11} b")
    print("""
  Folding factor 2 with a 124-bit element and a 256-bit hash: OpenVM alone.
  193 queries * 23 rounds * 8 bits = 4.3 KiB against a 235,651 KiB proof --
  0.002%. So iteration 60's identification of the worst case with s*depth is
  exact in NODE COUNT, which is what merkle_dedup measures, and off by at most
  8 bits per query per round in BITS. Recorded, not corrected: nothing rests
  on it.""")


if __name__ == "__main__":
    report()
