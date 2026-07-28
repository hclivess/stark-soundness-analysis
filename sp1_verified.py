"""
HORIZONS thread 2, answered against machine-checked numbers.

Thread 2 read: "Jagged's concrete soundness -- worth running against SP1's real
parameters to see whether the 100-bit UDR figure comes from the PCS or the
arithmetization."

soundcalc-lean (cloned in iteration 47) carries SP1's full component breakdown
as `native_decide`-checked statements. Every figure below is machine-verified,
not read off a report.

THE ANSWER: BOTH, AND THEY COINCIDE
------------------------------------
From SoundcalcIO/ZkVM/SP1.lean, verbatim:

    example : secBits (SP1_core_jagged.totalErr)                = 100
    example : secBits (SP1_core_lookup_lookup.errUB)            = 100
    example : secBits (SP1_core_FRI.queryErr (UDR koalaBear4))  = 100
    example : secBits (SP1_core_FRI.batchingErr (UDR ...))      = 104
    example : secBits (SP1_core_FRI.commitErr (UDR ...) 0)      = 103
    example : secBits SP1_core_jagged.zerocheckErr              = 112
    example : secBits SP1_core_jagged.reduceErr                 = 116

So the 100 is set by TWO components at once -- the FRI query phase and the LogUp
lookup -- which sit at exactly 100 while every other term is 103 to 122. The
thread posed it as PCS-or-arithmetization; the answer is that neither alone
explains it and both are tight.

That also settles what this repo's model does and does not see. Iteration 24
established the query phase binds for SP1, and `queryErr = 100` confirms it. But
a FRI-only model cannot see the lookup, which is equally tight -- so the repo's
standing caveat ("the model is FRI/code-layer only ... it therefore upper bounds
published totals") is exactly right here, and for a reason now visible: the
invisible term happens to coincide with the visible one.

THREE INDEPENDENT VALIDATIONS FALL OUT
---------------------------------------
1. THE CEILING EQUATION, on SP1's round-0 commit term.
   SP1 core has denseLen 2^21 and rho = 1/4, so nu = 23, and koalaBear4 gives
   E = 124. This repo's UDR ceiling is E - nu - log2(gamma), gamma = (1-rho)/2:

       124 - 23 + 1.42  =  102.42      vs machine-verified 103

   0.58 bits apart, consistent with `secBits` rounding to an integer. The
   equation was derived here from soundcalc's Python; this is the first time it
   has been checked against a formal statement.

2. a = 1, THE PER-ROUND STEP, machine-verified over 21 rounds.
   The Lean file asserts commitErr at every round 0..20 individually:

       103 104 105 106 107 108 109 110 111 112 113
       114 115 116 117 118 119 120 121 121 122

   Steps are {0, 1} with mean 0.950 over 20 fold-2 rounds -- exactly a = 1 with
   one flat spot from integer rounding. This repo measured that step from
   soundcalc's published per-round column and called it "separately observable";
   here it is formally checked, round by round.

3. MERKLE DEDUPLICATION, against a verified proof size.
   The file asserts both an expected and a worst-case proof size:

       sp1CoreFRI.proofSizeExp   / KIB = 913
       sp1CoreFRI.proofSizeWorst / KIB = 1474

   The two differ only in authentication-path sharing, so their ratio is the
   deduplication saving: 1 - 913/1474 = 38.1%.

   merkle_dedup.py, at SP1's parameters (s = 124 queries, depth 21), predicts
   37.4%. The comparison is not quite like-for-like and the direction matters:
   the 38.1% is a saving on the TOTAL proof, which includes size-invariant field
   elements, so the true Merkle-only saving in their model is at least 38.1%.
   This repo's model therefore UNDERSTATES the saving by at least 0.7 points --
   a small error in the conservative direction, validated against a number no
   part of this repo had seen.

WHAT THIS DOES NOT SHOW
-----------------------
Only SP1 and Airbender have reference configs in the tree, so this is a
two-system check, not a seven-system one. And `native_decide` verifies that the
Lean definitions evaluate to those integers; it does not verify that the Lean
definitions faithfully model BCHKS25. That second gap is exactly what the
repository's 79 theorems are for, and reading them is a separate exercise.
"""

import math

# All figures below are `native_decide`-checked in SoundcalcIO/ZkVM/SP1.lean.
SP1_VERIFIED = {
    "total": 100,
    "lookup": 100,
    "fri_query": 100,
    "fri_batching": 104,
    "fri_commit_round0": 103,
    "zerocheck": 112,
    "reduce": 116,
}

SP1_COMMIT_ROUNDS = [103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
                     114, 115, 116, 117, 118, 119, 120, 121, 121, 122]

SP1_PROOF_KIB = {"expected": 913, "worst": 1474}

# SP1 core config, from the same file
SP1_E, SP1_NU, SP1_RHO, SP1_QUERIES = 124, 23, 0.25, 124


def udr_ceiling(E, nu, rho):
    """This repo's UDR commit ceiling: E - log2(gamma*n + 1), gamma = (1-rho)/2."""
    gamma = (1 - rho) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def binding_components(verified, tol=0):
    """Which components sit at the total."""
    total = verified["total"]
    return sorted(k for k, v in verified.items()
                  if k != "total" and abs(v - total) <= tol)


def dedup_saving_from_sizes(sizes):
    return 1 - sizes["expected"] / sizes["worst"]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. WHAT SETS SP1's 100 BITS -- BOTH THE PCS AND THE LOOKUP")
    print(f"  {'component':<22} {'secBits (verified)':>19} {'at the total?':>15}")
    print("  " + "-" * 60)
    for k in ("total", "lookup", "fri_query", "fri_commit_round0",
              "fri_batching", "zerocheck", "reduce"):
        v = SP1_VERIFIED[k]
        mark = "TOTAL" if k == "total" else ("YES" if v == 100 else "")
        print(f"  {k:<22} {v:>19} {mark:>15}")
    binders = binding_components(SP1_VERIFIED)
    print(f"""
  Binding at 100: {', '.join(binders)}.

  The thread asked whether the figure comes from the PCS or the arithmetization.
  Neither alone: the FRI query phase and the LogUp lookup are both exactly 100,
  while everything else sits 3 to 22 bits above. A FRI-only model sees one of
  them and not the other -- which is why this repo's standing caveat about
  upper-bounding published totals is right, and why it happens to be tight here.""")

    sec("2. THE CEILING EQUATION AGAINST A FORMAL STATEMENT")
    mine = udr_ceiling(SP1_E, SP1_NU, SP1_RHO)
    print(f"""
  SP1 core: denseLen 2^21, rho = 1/4 so nu = {SP1_NU}; koalaBear4 gives E = {SP1_E}.

      this repo:  E - log2(gamma * 2^nu + 1)  =  {mine:.2f}
      verified :  commitErr (UDR) round 0      =  {SP1_VERIFIED['fri_commit_round0']}
      apart    :  {abs(mine - SP1_VERIFIED['fri_commit_round0']):.2f} bits, consistent with secBits rounding to an integer

  The equation was derived here from soundcalc's Python. This is the first time
  it has been checked against a machine-verified statement.""")

    sec("3. a = 1, ROUND BY ROUND, OVER 21 VERIFIED ROUNDS")
    steps = [SP1_COMMIT_ROUNDS[i + 1] - SP1_COMMIT_ROUNDS[i]
             for i in range(len(SP1_COMMIT_ROUNDS) - 1)]
    print(f"  rounds 0..20: {' '.join(str(v) for v in SP1_COMMIT_ROUNDS)}")
    print(f"\n  steps taken: {sorted(set(steps))}   mean {sum(steps)/len(steps):.3f} "
          f"over {len(steps)} fold-2 rounds")
    print("""
  Exactly a = 1 with one flat spot from integer rounding. This repo measured the
  step from soundcalc's published per-round column and called `a` "separately
  observable"; here every round is asserted individually and checked.""")

    sec("4. MERKLE DEDUPLICATION AGAINST A VERIFIED PROOF SIZE")
    import merkle_dedup as md
    ver = dedup_saving_from_sizes(SP1_PROOF_KIB)
    mine_d = 1 - (md.expected_auth_nodes(SP1_QUERIES, 21)
                  / md.naive_auth_nodes(SP1_QUERIES, 21))
    print(f"""
      proofSizeExp   = {SP1_PROOF_KIB['expected']} KiB      (paths deduplicated)
      proofSizeWorst = {SP1_PROOF_KIB['worst']} KiB      (paths not shared)
      verified saving on the TOTAL proof = {ver:.1%}

      merkle_dedup.py at s = {SP1_QUERIES}, depth 21   = {mine_d:.1%}

  Not quite like-for-like, and the direction matters: {ver:.1%} is a saving on the
  whole proof, which includes size-invariant field elements, so their Merkle-only
  saving is at least that. This repo's model therefore UNDERSTATES by at least
  {ver - mine_d:.1%} -- a small error in the conservative direction, against a number no
  part of this repo had seen.""")

    sec("5. WHAT THIS DOES NOT SHOW")
    print("""
  Only SP1 and Airbender have reference configs in the tree, so this is a
  two-system check rather than a seven-system one.

  And `native_decide` verifies that the Lean DEFINITIONS evaluate to those
  integers. It does not verify that those definitions faithfully model BCHKS25 --
  that is what the repository's 79 theorems address, and reading them is a
  separate exercise this file does not attempt.""")


if __name__ == "__main__":
    report()
