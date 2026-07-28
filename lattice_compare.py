"""
Pricing the lattice path: does M-SIS actually escape Theorem 2's ceiling?

HORIZONS.md assessed the lattice direction qualitatively -- "buys scaling, spends
resilience" -- and recommended against it for a project that declines the FRI
capacity conjecture on resilience grounds. This file prices it, and finds a
structural asymmetry the qualitative read missed.

TWO DIFFERENT KINDS OF SECURITY DEGRADE DIFFERENTLY UNDER A QUANTUM ADVERSARY.

  Fiat-Shamir soundness (BOTH families have it). The adversary controls the
  transcript and Grover-searches it. quantum.py: PQ bits = classical / 2.
  A FULL halving. This hits FRI and lattice folding alike -- LatticeFold+ is
  still FS-compiled.

  The COMMITMENT BINDING assumption. Here the families diverge sharply:

    hash-based   collision resistance. 256-bit hash -> 128 classical,
                 and 128 quantum under the defensible bound (BHT's 256/3 = 85
                 needs implausible QRAM). Barely moves, and never binds.

    lattice      M-SIS, broken by lattice sieving. Classical sieving costs
                 2^(0.292*beta); the best known quantum sieve (Laarhoven)
                 2^(0.265*beta). So the exponent shrinks by a factor
                 0.265/0.292 = 0.9075 -- about a 9% loss, NOT a halving.

THE ASYMMETRY THAT MATTERS FOR THEOREM 2. FRI's commit-phase soundness is
bounded by the size of the CHALLENGE FIELD: Thm 2 gives a ceiling ~E - 2nu (JBR)
or ~E - nu (UDR), unbuyable with queries. That is the ceiling that pins NADO at
47 bits and every 31-bit^4 system near 50 PQ bits.

Lattice folding has no such term. Its challenges live in R_q with q a 64-bit
prime and ring dimension 2d, so the challenge space is astronomically larger
than any single field element, and the binding is M-SIS hardness at the chosen
(d, q, beta) -- a parameter you buy with dimension, not with field width.

So the lattice path DOES escape Theorem 2's ceiling. That is a real structural
advantage HORIZONS.md did not credit it with, and it is worth stating plainly
even though the recommendation does not change.

WHY THE RECOMMENDATION STILL DOES NOT CHANGE. Escaping the ceiling is not the
same as being more secure. Three costs remain:
  1. FS soundness still halves, so the folding scheme must itself be sized for
     2*lambda classical -- the same discipline PQ design demands of FRI.
  2. M-SIS parameter estimates have moved historically as sieving improved;
     collision resistance has not.
  3. The 0.9075 sieving exponent is a MODEL, and quantum sieving speedups are
     an active area. A 9% loss is today's estimate, not a theorem.
"""

import math

# lattice sieving exponents (heuristic, BKZ-beta core-SVP model)
CLASSICAL_SIEVE = 0.292          # Becker-Ducas-Gama-Laarhoven
QUANTUM_SIEVE = 0.265            # Laarhoven quantum sieve
SIEVE_RATIO = QUANTUM_SIEVE / CLASSICAL_SIEVE


def msis_quantum_bits(classical_bits):
    """Core-SVP: security bits scale linearly in the BKZ block size beta, so a
    quantum sieve shrinks the exponent by 0.265/0.292."""
    return classical_bits * SIEVE_RATIO


def msis_beta_for(classical_bits):
    return classical_bits / CLASSICAL_SIEVE


def fs_quantum_bits(classical_bits):
    """Fiat-Shamir transcript search is Grover-able: full halving (quantum.py)."""
    return classical_bits / 2.0


def hash_quantum_bits(hash_bits, qram=False):
    return hash_bits / (3.0 if qram else 2.0)


def sec(t):
    print("\n" + "=" * 90)
    print(t)
    print("=" * 90)


def report():
    sec("1. HOW EACH SECURITY COMPONENT DEGRADES UNDER A QUANTUM ADVERSARY")
    print(f"  {'component':<34} {'classical':>10} {'quantum':>9} {'retained':>9}")
    print("  " + "-" * 66)
    rows = [("Fiat-Shamir soundness (both)", 256, fs_quantum_bits(256)),
            ("hash collision resistance", 128, hash_quantum_bits(256)),
            ("M-SIS via lattice sieving", 128, msis_quantum_bits(128)),
            ("M-SIS via lattice sieving", 256, msis_quantum_bits(256))]
    for name, c, q in rows:
        print(f"  {name:<34} {c:>10.0f} {q:>9.1f} {100*q/c:>8.1f}%")
    print(f"""
  Fiat-Shamir loses HALF. M-SIS loses about {100*(1-SIEVE_RATIO):.0f}%. Collision resistance
  loses nothing that binds. So the assumption a scheme rests on degrades far
  less than the Fiat-Shamir layer wrapped around it -- for BOTH families.""")

    sec("2. THE CEILING THAT LATTICES ESCAPE")
    print("""  FRI (Thm 2): commit-phase soundness <= ~E - nu, where E is the size of the
  CHALLENGE FIELD. Unbuyable with queries or grinding at any price.
""")
    print(f"  {'system':<28} {'E':>5} {'nu':>4} {'FRI ceiling':>12} {'PQ ceiling':>11}")
    print("  " + "-" * 64)
    for nm, E, nu in (("NADO today (Goldilocks)", 64, 18),
                      ("31-bit^4 (deployed norm)", 124, 22),
                      ("Goldilocks^3 (ZisK)", 192, 22),
                      ("31-bit^10 (PQ design)", 310, 22)):
        ceil_ = E - nu
        print(f"  {nm:<28} {E:>5} {nu:>4} {ceil_:>12.0f} {ceil_/2:>11.1f}")
    print(f"""
  Lattice folding has NO analogous term. Challenges live in R_q = Z_q[X]/(X^2d+1)
  with q a 64-bit prime, so the challenge space is q^(2d), not q. Binding is
  M-SIS at (d, q, beta), bought with DIMENSION rather than field width.

  So the lattice path genuinely escapes Thm 2. HORIZONS.md did not credit it
  with that, and should have.""")

    sec("3. WHAT 128 PQ BITS COSTS EACH WAY")
    print(f"  {'path':<30} {'needs classically':>19} {'mechanism':>26}")
    print("  " + "-" * 78)
    print(f"  {'hash-based FRI':<30} {'256 (FS halving)':>19} {'extension degree ~9-10':>26}")
    print(f"  {'lattice, FS layer':<30} {'256 (FS halving)':>19} {'challenge set size':>26}")
    print(f"  {'lattice, M-SIS binding':<30} "
          f"{f'{128/SIEVE_RATIO:.0f} (sieving)':>19} "
          f"{f'BKZ beta ~ {msis_beta_for(128/SIEVE_RATIO):.0f}':>26}")
    print(f"""
  Both families need 256 classical bits of Fiat-Shamir soundness for 128 PQ
  bits -- that requirement is universal and is the finding of quantum.py. Where
  they differ is the second term: FRI must buy it with extension degree, running
  into Thm 2; lattices buy it with BKZ block size, which has no such ceiling.""")

    sec("4. THE RECOMMENDATION, REVISITED HONESTLY")
    print(f"""
  HORIZONS.md recommended the hash-based multilinear path (a) over the lattice
  path (b) for NADO, on the grounds that a project declining the FRI capacity
  conjecture on resilience grounds should not adopt M-SIS to go faster.

  That recommendation STANDS, but one premise was wrong. I implied lattices only
  trade resilience for speed. They also escape Thm 2's ceiling, which is a real
  capability the hash-based path does not have at small field width. The correct
  statement of the trade is:

     lattice   escapes the field-size ceiling; pays a structured assumption
               whose parameters have MOVED historically, and whose quantum
               estimate ({SIEVE_RATIO:.4f} exponent ratio) is a model, not a theorem
     hash      keeps the weakest assumption known; pays extension degree ~9-10
               and ~800 KiB proofs to reach the same 128 PQ bits

  For NADO specifically the hash path remains right, because degree-10 over a
  31-bit base is a KNOWN, bounded cost with no cryptanalytic risk, whereas the
  M-SIS route trades a cost you can compute for a risk you cannot. But that is a
  judgement about risk appetite, not a claim that lattices are weaker.
""")


if __name__ == "__main__":
    report()
