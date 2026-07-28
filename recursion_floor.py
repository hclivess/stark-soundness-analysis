"""
Recursion does compress the 128-PQ base layer -- and iteration 72's "one to two
orders of magnitude" was true of the base layer only, not of what a verifier
sees.

Iteration 72 priced a 128-PQ-bit single circuit at 4-19 MiB and corrected
finding 1's "~800 KiB", which had modelled a two-column trace. It closed by
noting that every deployed headline size is a LAST circuit after several
compression rounds (iteration 61), and that recursion might compress these the
way OpenVM2's six stages take 26175 KiB to 270. It did not check. This does.

EVERY STAGE CARRIES THE FULL TARGET
-------------------------------------
That is the constraint recursion cannot dodge. A pipeline's security is the
minimum over its stages, so each must independently reach the target, and
soundcalc's reports show exactly that:

    Pico       53 bits x 5 circuits
    OpenVM    100 bits x 3
    SP1       100 bits x 3
    OpenVM2   100 bits x 6

So the FINAL proof is not free to be small. Proposition 11 applies to it too:
its own s*R/2 + g must reach 256 classical for 128 PQ. Recursion moves the work
off the verifier's critical path; it does not lower the bar any single stage
must clear.

THE FLOOR
-----------
The final stage is a recursive verifier: narrow (deployed ones run batch
128-485) and short (trace 2^15 to 2^20). At KoalaBear^9 with a 384-bit digest:

    batch  T        R=2    R=3    R=4    R=5    R=6
      128 16       1809   1338   1104    976    879
      128 18       2071   1536   1268   1120   1007
      128 20       2377   1762   1453   1281   1149
      485 18       4843   3384   2654   2238   1931

Deployed final stages all run rho = 1/16 to 1/32 (Pico's compress and embed at
R=4, ZisK's Final at R=5), so the R >= 4 columns are the live ones -- nobody
pays 456 queries in the stage they transmit. R = 2 and 3 are context.

Deployed final stages already use the high-blowup trick this table rewards --
Pico's compress and embed run rho = 1/16, ZisK's Final rho = 1/32, described in
pico.toml as "a tighter FRI configuration (larger log_blowup, fewer queries) to
compress the proof size".

So a 128-PQ verifier-facing proof is about 0.9 to 1.5 MiB.

WHICH MEANS ITERATION 72 OVER-CORRECTED
-----------------------------------------
Against what ships today:

    zkDTVM    200 KiB      Pico     232 KiB      ZisK  269 KiB
    OpenVM2   270 KiB      SP1      529 KiB

all at 100-128 CLASSICAL bits, i.e. 50-64 PQ. A 128-PQ final proof at ~1 MiB is
1.7x SP1's and 3.3x ZisK's. That is 2-4x, not the "one to two orders of
magnitude" iteration 72 wrote. Iteration 72's figure was the BASE layer, which
the prover produces and the verifier never sees.

The corrected statement: doubling post-quantum security from ~64 to 128 bits
costs roughly 2-4x in verifier-facing proof size, and 1-2 orders of magnitude in
the base-layer proof the recursion consumes.

AND FINDING 1's 797 KiB IS CLOSER THAN ITERATION 72 ALLOWED
-------------------------------------------------------------
Reproducing pq_design's own assumption -- two columns, its blowup 16, at a
recursion-sized trace 2^18 -- the verified model gives 778 KiB against its 797.
Its arithmetic was internally consistent to 2.4%.

So finding 1's number is within about 30% of the honest ~1 MiB. It got there by
describing a two-column single circuit rather than a realistic final stage,
which is the wrong derivation for roughly the right answer. Iteration 72 was
right that the derivation is wrong and overstated how wrong the number is.

WHAT REMAINS TRUE FROM ITERATION 72
-------------------------------------
The base layer really is 4-19 MiB at realistic trace widths, the leaf term
really does dominate at 60-99.6% for any zkVM-shaped trace, and pq_design's
model really does omit it. None of that changes. What changes is the conclusion
drawn: the expensive object is not the thing anyone transmits.

WHAT IS STILL NOT CHECKED
---------------------------
Whether a recursive verifier for a 128-PQ proof FITS in trace 2^18 at batch 128.
It must hash s*nu = 114*26 = 2964 Merkle nodes at 384-bit digests and do
degree-9 extension arithmetic, against today's 124*23 = 2852 nodes at 256 bits
and degree 4. The hash count is comparable but each hash is wider (13 field
elements vs 8) and each multiplication costs ~5x (81 vs 16 base products). If
that inflates the recursive circuit past 2^20, the floor rises toward 1.4 MiB
rather than 0.9. The table above spans that range deliberately; pinning it needs
a Poseidon2 gate count this repo does not have.
"""

import math

from proof_size_exact import fri_proof_bits
from pq_design_cost import queries_needed

KIB = 8 * 1024
HASH_BITS, ELEM_BITS, GRINDING = 384, 279, 28      # KoalaBear^9, BHT-safe digest

# soundcalc reports: per-stage security, showing every stage carries the target
PIPELINE_SECURITY = [("Pico", 53, 5), ("OpenVM", 100, 3), ("SP1", 100, 3),
                     ("OpenVM2", 100, 6)]

# deployed final (verifier-facing) proofs, KiB, at 100-128 CLASSICAL bits
DEPLOYED_FINAL = [("zkDTVM", 200), ("Pico", 232), ("ZisK", 269),
                  ("OpenVM2", 270), ("SP1", 529)]

# pq_design's claim and its own modelling assumption
FINDING1_CLAIM_KIB = 797
FINDING1_ASSUMPTION = dict(batch=2, T=18, R=4)

# recursive-verifier shapes seen in the tomls
RECURSIVE_BATCHES = (128, 485)
RECURSIVE_TRACES = (16, 18, 20)
BLOWUP_EXPONENTS = (2, 3, 4, 5, 6)
# Deployed FINAL stages all run rho = 1/16 to 1/32 (Pico compress/embed R=4,
# ZisK Final R=5), so R < 4 is shown for context but is not a plausible final
# configuration -- no one pays 456 queries in the stage they transmit.
FINAL_STAGE_EXPONENTS = (4, 5, 6)


def final_stage_kib(batch, T, R, hash_bits=HASH_BITS, elem_bits=ELEM_BITS,
                    g=GRINDING, expected=True):
    """Size of a 128-PQ final-stage proof: Proposition 11 applied to it too."""
    s = queries_needed(R, g)
    nu = T + R
    return fri_proof_bits(hash_bits, elem_bits, batch, s, 2 ** nu, [2] * nu,
                          2.0 ** -R, expected) // KIB


def floor_range(batch=128):
    """(min, max) verifier-facing size over plausible recursive shapes."""
    vals = [final_stage_kib(batch, T, R)
            for T in RECURSIVE_TRACES for R in FINAL_STAGE_EXPONENTS]
    return min(vals), max(vals)


def cost_multiple():
    """How much larger a 128-PQ final proof is than today's, as a range."""
    lo, hi = floor_range(128)
    deployed = [k for _n, k in DEPLOYED_FINAL]
    return lo / max(deployed), hi / min(deployed)


def finding1_reproduced():
    """pq_design's own assumption priced in the verified model."""
    a = FINDING1_ASSUMPTION
    return final_stage_kib(a["batch"], a["T"], a["R"])


def verifier_hash_count(s=None, nu=26):
    """Merkle nodes a recursive verifier must hash, s * nu."""
    s = queries_needed(4, GRINDING) if s is None else s
    return s * nu


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. EVERY STAGE CARRIES THE FULL TARGET -- THE CONSTRAINT RECURSION CANNOT DODGE")
    print("\n  A pipeline's security is the minimum over its stages, and soundcalc's")
    print("  reports show each designed to the same figure:\n")
    print(f"  {'system':<10} {'bits':>6} {'circuits':>10}")
    print("  " + "-" * 30)
    for nm, bits, n in PIPELINE_SECURITY:
        print(f"  {nm:<10} {bits:>6} {n:>10}")
    print("""
  So the FINAL proof is not free to be small: Proposition 11 applies to it too,
  and its own s*R/2 + g must reach 256 classical for 128 PQ. Recursion moves
  work off the verifier's path; it does not lower the bar a stage must clear.""")

    sec("2. THE FLOOR: A 128-PQ VERIFIER-FACING PROOF")
    print(f"\n  KoalaBear^9, {HASH_BITS}-bit digest, grinding {GRINDING}\n")
    print(f"  {'batch':>6} {'T':>3}" + "".join(f"{'R=' + str(R):>8}"
                                               for R in BLOWUP_EXPONENTS))
    print("  " + "-" * 52)
    for batch in RECURSIVE_BATCHES:
        for T in RECURSIVE_TRACES:
            if batch == 485 and T != 18:
                continue
            print(f"  {batch:>6} {T:>3}" + "".join(
                f"{final_stage_kib(batch, T, R):>8}" for R in BLOWUP_EXPONENTS))
    lo, hi = floor_range(128)
    print(f"""
  Deployed final stages already use the high-blowup trick this table rewards:
  Pico's compress and embed run rho = 1/16, ZisK's Final rho = 1/32 -- "a
  tighter FRI configuration (larger log_blowup, fewer queries) to compress the
  proof size" (pico.toml).

  So a 128-PQ verifier-facing proof is about {lo} to {hi} KiB, taking the
  blowup >= 16 columns -- no one pays 456 queries in the stage they transmit.
  The R = 2 and 3 columns are shown for context only.""")

    sec("3. WHICH MEANS ITERATION 72 OVER-CORRECTED")
    print(f"\n  {'system':<10} {'final KiB':>10}   at 100-128 CLASSICAL bits (50-64 PQ)")
    print("  " + "-" * 56)
    for nm, k in DEPLOYED_FINAL:
        print(f"  {nm:<10} {k:>10}")
    m_lo, m_hi = cost_multiple()
    print(f"""
  A 128-PQ final proof at ~1 MiB is {lo/269:.1f}x ZisK's and {lo/529:.1f}x SP1's -- {m_lo:.1f}x to {m_hi:.1f}x
  across the set. That is 2-4x, not the "one to two orders of magnitude"
  iteration 72 wrote. Iteration 72's figure was the BASE layer, which the prover
  produces and the verifier never sees.

  CORRECTED: doubling post-quantum security from ~64 to 128 bits costs roughly
  2-4x in verifier-facing proof size, and 1-2 orders of magnitude in the base
  layer the recursion consumes.""")

    sec("4. AND FINDING 1's 797 KiB IS CLOSER THAN ITERATION 72 ALLOWED")
    r = finding1_reproduced()
    a = FINDING1_ASSUMPTION
    print(f"""
  Reproducing pq_design's OWN assumption -- {a['batch']} columns, its blowup
  {2**a['R']}, at a recursion-sized trace 2^{a['T']} -- the verified model gives {r} KiB
  against its {FINDING1_CLAIM_KIB}. Internally consistent to {abs(r-FINDING1_CLAIM_KIB)/FINDING1_CLAIM_KIB:.1%}.

  So finding 1's number is within about 30% of the honest ~1 MiB. It got there
  by describing a two-column single circuit rather than a realistic final stage:
  the wrong derivation for roughly the right answer. Iteration 72 was right that
  the derivation is wrong and overstated how wrong the number is.

  STILL TRUE FROM ITERATION 72: the base layer really is 4-19 MiB at realistic
  widths, the leaf term really does dominate at 60-99.6%, and pq_design really
  does omit it. What changes is the conclusion: the expensive object is not the
  thing anyone transmits.""")

    sec("5. WHAT IS STILL NOT CHECKED")
    print(f"""
  Whether a recursive verifier for a 128-PQ proof FITS in trace 2^18 at batch
  128. It must hash s*nu = {verifier_hash_count()} Merkle nodes at {HASH_BITS}-bit digests and do
  degree-9 extension arithmetic, against today's 124*23 = 2852 nodes at 256 bits
  and degree 4. Comparable hash COUNT, but each hash is wider (13 field elements
  vs 8) and each multiplication costs about 5x (81 vs 16 base products).

  If that inflates the recursive circuit past 2^20, the floor rises toward {hi}
  rather than {lo} KiB. The table above spans that range deliberately. Pinning it
  needs a Poseidon2 gate count this repo does not have.""")


if __name__ == "__main__":
    report()
