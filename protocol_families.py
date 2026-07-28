"""
The other three protocol families -- and a bound that iterations 60 AND 61 both
reasoned from, which is false.

Iteration 61 reconstructed every plain-FRI proof size exactly (110 figures). It
left three families untouched: JAGGED (SP1, zkDTVM), SWIRL (OpenVM2, zkDTVM's
last circuit) and WHIR (DummyWHIR). Those are exactly the systems whose
expected/worst ratio reads 0.0%, so they were the obvious next target.

FINDING 1: SWIRL's EXPECTED PROOF SIZE IS A STUB
--------------------------------------------------
soundcalc/circuits/swirl/circuit.py:132 --

    def get_expected_proof_size_bits(self) -> int:
        return self.get_proof_size_bits()

It returns the worst case verbatim. There is no expected-size model for SWIRL.

Iteration 60 explained OpenVM2's and zkDTVM's 0.0% ratios as a property of the
protocol: "WHIR/SWIRL proofs are dominated by components that do not scale with
the query set". That is wrong, and checkably so -- WHIR has a real expected
model (whir.py:860 dispatches to _get_proof_size_bits(expected=True)) and so
does JAGGED (jagged.py:92 adds the dense PCS's expected size to a deterministic
reduction term). SWIRL alone does not.

Both 0.0% systems have a SWIRL LAST circuit -- OpenVM2 throughout, zkDTVM's
root_shrink -- which is why the stub surfaces in exactly those two rows and
nowhere else. That is iteration 61's "the summary reports the last circuit"
doing useful work: it predicts which systems the stub can affect.

FINDING 2: JAGGED RECONSTRUCTS EXACTLY TOO
--------------------------------------------
JAGGED is the dense FRI PCS plus two sumchecks (jagged.py:67-83), where a
sumcheck of degree d over v variables costs (v(d+2)+2) field elements:

    log_trace = ceil(log2 dense_length) + ceil(log2 dense_batch)
    reduction = sumcheck(2, log_trace) + sumcheck(2, 2*log_trace + 2)

With that, all six JAGGED circuits land exactly:

    SP1     core      918/1479     compress  735/1267    shrink 529/887
    zkDTVM  core 311725/312976     compress 1022/1736    shrink 856/1422

122 figures now, over 61 circuits and eight systems, still zero deviation.

SP1's core at 918/1479 is worth singling out. Iteration 48 read that pair out of
soundcalc-lean's `sp1CoreJagged` -- a Lean development, a different artifact
entirely. It is now derived from sp1.toml's raw parameters through a formula
transcribed from the Python. Two independent routes to the same two numbers.

FINDING 3: THE RATIO BOUND WAS NEVER VALID
--------------------------------------------
Iteration 60 observed that SP1's published ratio (40.4%) exceeds its
single-circuit Merkle dedup saving, argued this was impossible because both
proofs carry identical leaf data, and concluded the summary figure "aggregates 3
circuits". Iteration 61 showed the summary reports the LAST circuit, not a sum,
and re-explained the violation as systems.py recording SP1's core while the
summary quotes its shrink.

Both were explaining a violation of a bound that does not hold.

A FRI proof does not contain one Merkle tree. It contains one per round --
nu + 1 of them, each shallower than the last. Deduplication improves sharply as
trees get shallower, because a fixed query count saturates a smaller tree:

    SP1 shrink, 94 queries, D = 2^21, folding [2]*18

        round  depth   exact   naive   saving
            0     21    1285    1974    34.9%
            1     20    1191    1880    36.6%
            3     18    1003    1692    40.7%
           17      4       4     376    98.9%
           18      3       3     282    98.9%

        initial tree alone      34.9%
        aggregate, all 19       55.2%
        published ratio         40.4%

34.9% < 40.4% < 55.2%. The published ratio sits between the initial tree's
saving and the all-rounds aggregate, which is exactly where it must sit: the
aggregate hash saving is 55.2%, and the proof's leaf data and final polynomial
dilute it down to 40.4%.

So the correct statement is

    ratio  <=  aggregate hash saving over ALL FRI rounds

and the initial tree's saving is neither an upper nor a lower bound. Checked
across all seven systems, every ratio respects the aggregate bound, and SP1 is
the only one that exceeds the single-tree figure -- which is why it alone looked
anomalous:

    circuit             ratio   1-tree   all-tree
    Pico embed          17.4%    25.8%     41.3%
    OpenVM internal      6.6%    33.4%     53.9%
    ZisK Final_Comp     14.1%    34.2%     44.7%
    SP1 shrink          40.4%    34.9%     55.2%   <- exceeds 1-tree
    Airbender            5.9%    28.9%     45.6%
    RISC0               12.9%    27.5%     41.5%
    Miden               24.8%    25.6%     38.2%

Two iterations spent explaining an anomaly that was an artifact of the bound
used to detect it. The lesson is narrow and worth keeping: the "overcount" band
this repo quotes (26-40%, merkle_exact) is a per-tree figure for the INITIAL
commitment, and it is not what a whole-proof ratio should be compared against.
Iteration 61's finding that the summary reports the last circuit stands on its
own evidence -- it was verified directly against Pico, OpenVM and ZisK -- and is
unaffected.
"""

import math
from proof_size_exact import fri_proof_bits, elem_bits
from merkle_exact import soundcalc_auth_nodes

KIB = 8 * 1024

# (system, field, hash_bits, [(name, rho, log2 dense_length, dense_batch,
#                              num_queries, n_folds)], [(exp, worst)])
JAGGED_SYSTEMS = [
    ("SP1", "KoalaBear^4", 248,
     [("core", 0.25, 21, 193, 124, 21), ("compress", 0.25, 20, 128, 124, 20),
      ("shrink", 0.125, 18, 128, 94, 18)],
     [(918, 1479), (735, 1267), (529, 887)]),
    ("zkDTVM", "KoalaBear^5", 248,
     [("core", 0.5, 21, 62928, 261, 21), ("compress", 0.25, 20, 128, 160, 20),
      ("shrink", 0.125, 19, 128, 131, 20)],
     [(311725, 312976), (1022, 1736), (856, 1422)]),
]

# last circuit of each system -- what the summary reports (iteration 61)
# (label, num_queries, domain size, folding factors, published expected/worst)
LAST_CIRCUITS = [
    ("Pico embed", 21, 2 ** 19, [2] * 15, 232, 281),
    ("OpenVM internal", 118, 2 ** 23, [2] * 21, 7687, 8231),
    ("ZisK Final_Comp", 54, 2 ** 19, [8] * 3, 269, 313),
    ("SP1 shrink", 94, 2 ** 21, [2] * 18, 529, 887),
    ("Airbender", 87, 2 ** 25, [16, 16, 16, 8, 8], 1836, 1951),
    ("RISC0", 50, 2 ** 23, [16] * 4, 331, 380),
    ("Miden", 27, 2 ** 21, [4] * 7, 112, 149),
]

# families and whether soundcalc models expected size, or stubs it to the worst
FAMILY_EXPECTED_MODEL = {"FRI": True, "JAGGED": True, "WHIR": True, "SWIRL": False}


def sumcheck_size_bits(degree, num_variables, field_size_bits):
    """soundcalc/circuits/jagged.py:16-21."""
    return (num_variables * (degree + 2) + 2) * field_size_bits


def jagged_proof_bits(hb, eb, dense_length, dense_batch, q, rho, folding, expected):
    """soundcalc/circuits/jagged.py:86-94. Dense FRI PCS plus two sumchecks."""
    log_trace = (math.ceil(math.log2(dense_length))
                 + math.ceil(math.log2(dense_batch)))
    reduction = (sumcheck_size_bits(2, log_trace, eb)
                 + sumcheck_size_bits(2, 2 * log_trace + 2, eb))
    dense = fri_proof_bits(hb, eb, dense_batch, q, int(dense_length / rho),
                           folding, rho, expected)
    return dense + reduction


def reconstruct_jagged():
    """[(system, circuit, expected_kib, worst_kib, pub_exp, pub_worst)]."""
    out = []
    for sysname, field, hb, circuits, published in JAGGED_SYSTEMS:
        eb = elem_bits(field)
        for (nm, rho, dl, db, q, nf), (pe, pw) in zip(circuits, published):
            out.append((sysname, nm,
                        jagged_proof_bits(hb, eb, 2 ** dl, db, q, rho, [2] * nf,
                                          True) // KIB,
                        jagged_proof_bits(hb, eb, 2 ** dl, db, q, rho, [2] * nf,
                                          False) // KIB, pe, pw))
    return out


def round_savings(q, D, folding):
    """Per-round (depth, exact auth nodes, naive) for every FRI Merkle tree."""
    n, out = D, []
    for f in [None] + list(folding):
        d = int(math.log2(n if f is None else n // f))
        out.append((d, soundcalc_auth_nodes(q, d), q * d))
        if f:
            n //= f
    return out


def aggregate_saving(q, D, folding):
    """Hash saving over ALL FRI rounds -- the valid upper bound on the ratio."""
    rs = round_savings(q, D, folding)
    return 1 - sum(e for _, e, _ in rs) / sum(n for _, _, n in rs)


def initial_tree_saving(q, D):
    """Saving for the initial commitment alone -- NOT a bound on the ratio."""
    d = int(math.log2(D))
    return 1 - soundcalc_auth_nodes(q, d) / (q * d)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. SWIRL's EXPECTED PROOF SIZE IS A STUB")
    print("""
  soundcalc/circuits/swirl/circuit.py:132 --

      def get_expected_proof_size_bits(self) -> int:
          return self.get_proof_size_bits()

  It returns the worst case verbatim. Iteration 60 read OpenVM2's and zkDTVM's
  0.0% ratios as a property of the protocol -- "WHIR/SWIRL proofs are dominated
  by components that do not scale with the query set". They are not:\n""")
    print(f"  {'family':<10} {'models expected size?':>22}")
    print("  " + "-" * 34)
    for fam, has in FAMILY_EXPECTED_MODEL.items():
        print(f"  {fam:<10} {'yes' if has else 'NO -- returns worst':>22}")
    print("""
  WHIR dispatches to _get_proof_size_bits(expected=True) and JAGGED adds the
  dense PCS's expected size to a deterministic reduction term. SWIRL alone
  stubs it. Both 0.0% systems have a SWIRL LAST circuit -- OpenVM2 throughout,
  zkDTVM's root_shrink -- so the stub surfaces in exactly those two rows.""")

    sec("2. JAGGED RECONSTRUCTS EXACTLY: 12 MORE FIGURES, 2 MORE SYSTEMS")
    print(f"\n  {'system':<9} {'circuit':<10} {'exp':>8} {'pub':>8} {'d':>3} "
          f"{'worst':>8} {'pub':>8} {'d':>3}")
    print("  " + "-" * 60)
    rows = reconstruct_jagged()
    for s, nm, e, w, pe, pw in rows:
        print(f"  {s:<9} {nm:<10} {e:>8} {pe:>8} {e-pe:>+3} {w:>8} {pw:>8} {w-pw:>+3}")
    bad = sum((e != pe) + (w != pw) for _, _, e, w, pe, pw in rows)
    print(f"""
  {bad} deviations across {2*len(rows)} figures. With iteration 61's 110, that is 122 figures
  over 61 circuits and eight systems, all exact.

  SP1's core at 918/1479 is worth singling out: iteration 48 read that pair out
  of soundcalc-lean's sp1CoreJagged, a Lean development. It is now derived from
  sp1.toml through a formula transcribed from the Python. Two independent
  routes, same two numbers.""")

    sec("3. THE RATIO BOUND ITERATIONS 60 AND 61 BOTH USED IS FALSE")
    print("""
  A FRI proof contains one Merkle tree PER ROUND, each shallower than the last,
  and dedup improves sharply as trees shrink -- a fixed query count saturates a
  smaller tree. SP1's shrink circuit, 94 queries, D = 2^21:\n""")
    print(f"  {'round':>6} {'depth':>7} {'exact':>9} {'naive':>8} {'saving':>9}")
    print("  " + "-" * 42)
    rs = round_savings(94, 2 ** 21, [2] * 18)
    for i, (d, e, nv) in enumerate(rs):
        if i < 4 or i > len(rs) - 3:
            print(f"  {i:>6} {d:>7} {e:>9.0f} {nv:>8} {1-e/nv:>8.1%}")
        elif i == 4:
            print(f"  {'...':>6}")
    agg = aggregate_saving(94, 2 ** 21, [2] * 18)
    one = initial_tree_saving(94, 2 ** 21)
    print(f"""
      initial tree alone   {one:.1%}
      aggregate, all {len(rs)}    {agg:.1%}
      published ratio      {1-529/887:.1%}

  {one:.1%} < {1-529/887:.1%} < {agg:.1%}. The ratio sits between the initial tree's saving and
  the all-rounds aggregate, exactly where it must: leaf data and the final
  polynomial dilute {agg:.1%} down to {1-529/887:.1%}. The valid bound is the AGGREGATE; the
  initial tree's saving is neither an upper nor a lower bound.\n""")
    print(f"  {'circuit':<18} {'ratio':>8} {'1-tree':>9} {'all-tree':>10} {'ok?':>6}")
    print("  " + "-" * 54)
    for nm, q, D, ff, pe, pw in LAST_CIRCUITS:
        r, a, o = 1 - pe / pw, aggregate_saving(q, D, ff), initial_tree_saving(q, D)
        print(f"  {nm:<18} {r:>7.1%} {o:>9.1%} {a:>10.1%} "
              f"{'OK' if r <= a else 'VIOL':>6}"
              + ("   <- exceeds 1-tree" if r > o else ""))
    print("""
  Every ratio respects the aggregate bound. SP1 is the only one exceeding the
  single-tree figure, which is why it alone looked anomalous. Two iterations
  went into explaining an artifact of the bound used to detect it.

  Iteration 61's finding that the summary reports the LAST circuit is unaffected
  -- it was verified directly against Pico, OpenVM and ZisK, not inferred from
  this bound.""")


if __name__ == "__main__":
    report()
