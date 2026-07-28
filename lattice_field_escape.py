"""
HORIZONS thread 4, priced on the one axis both literatures state.

Thread 4 read: "LatticeFold+ concrete parameters -- M-SIS dimensions and proof
sizes at 64-bit fields, to price path (b) properly rather than qualitatively."

The M-SIS dimension tables and proof sizes live in PDF bodies, and eprint's PDFs
sit behind a Cloudflare challenge this session cannot solve (established over
five earlier iterations; abstract pages and, as of iteration 50, the SEARCH
endpoint do serve). So the thread cannot be closed as written.

What CAN be closed is the axis both literatures state in prose, and it happens
to be the axis this repo's central equation predicts: FIELD SIZE.

THE TWO CLAIMS
--------------
Boneh-Chen, "LatticeFold+", eprint 2025/247 (abstract, fetched):

    "Many existing folding protocols rely on the discrete-log based Pedersen
     commitment scheme, and are therefore not post-quantum secure and require a
     large (256-bit) field. Recently, Boneh and Chen constructed LatticeFold, a
     folding protocol using lattice-based commitments which is plausibly
     post-quantum secure and can operate with small (64-bit) fields."

This repo's ceiling equation, for a hash-based system in the unique-decoding
regime: classical bits <= E - nu - log2((1-rho)/2). Solving for the field:

    E  >=  target + nu - log2((1-rho)/2)

WHAT THE EQUATION DEMANDS, AGAINST WHAT LATTICES STATE (nu = 22, rho = 1/4)
----------------------------------------------------------------------------
    target             E needed (hash)   deg over 31b   deg over 64b   lattice
    100 classical                  123              4              2    64-bit
    128 classical                  151              5              3    64-bit
     64 PQ                         151              5              3    64-bit
    128 PQ                         279             10              5    64-bit

At the 128-post-quantum-bit target a hash-based system needs a 279-bit challenge
field; LatticeFold+ states 64. That is the escape, quantified: a factor of 4.4
in field size, and it compounds, because every query opening carries field
elements -- 35 bytes each against 8.

WHY THE ESCAPE IS STRUCTURAL AND NOT A BETTER CONSTANT
-------------------------------------------------------
The ceiling equation has E in it because a hash-based system's soundness comes
from a random challenge landing outside a bad set, and the bad set is measured
against the challenge SPACE. Security therefore scales 1:1 with field bits, and
there is no way to buy it elsewhere.

M-SIS security is not sourced from the field. It comes from the lattice
DIMENSION: the ring is R_q with q a 64-bit prime, and the hardness parameter is
beta, the dimension. So the field can stay small while security grows, and
Theorem 2's ceiling simply does not apply -- which is what lattice_compare.py
already concluded qualitatively, now with the number attached.

The post-quantum column compounds it further. Hash-based systems lose exactly
half (Grover on Fiat-Shamir; iterations 24 and 49). Lattices lose the ratio of
sieving exponents, 0.265/0.292 = 0.9075 -- about 9%, not 50%. So reaching 128
post-quantum bits costs a hash-based system 256 classical bits and a lattice
system about 141.

AN UNPLANNED CROSS-CHECK
------------------------
pq_design.py recommends extension degree 9-10 over a 31-bit base for 128
post-quantum bits, derived from its own cost model. The ceiling equation
independently gives E >= 279, which over a 31-bit base is degree 10. Two
derivations, same answer.

WHAT REMAINS UNPRICED, AND IT IS THE LARGER HALF
--------------------------------------------------
1. M-SIS dimensions. The beta a 64-bit LatticeFold+ instance needs for 128 bits
   is in a table this session cannot reach. Without it, "64-bit field" is a
   field-size claim, not a full parameter set -- a lattice system with a small
   field and a huge dimension may pay in prover time what it saves in field.
2. Proof sizes. LatticeFold+'s abstract claims "the prover is five to ten times
   faster, the verification circuit is simpler, and the folding proofs are
   shorter" than LatticeFold, all relative to its predecessor rather than to a
   hash-based baseline. No absolute figure is quoted in the abstract.
3. The 2026 line has moved past it -- Cyclo (2026/359), an l2-norm variant
   (2026/721), and ProtogaLattice (2026/1317) all improve on LatticeFold+, and
   all state their gains relative to it rather than absolutely.

So thread 4 is HALF closed: the field-size escape is now a number, and the cost
side is not. That asymmetry is worth stating plainly rather than letting the
priced half stand in for the whole.
"""

import math

CLASSICAL_SIEVE, QUANTUM_SIEVE = 0.292, 0.265      # BDGL / Laarhoven
LATTICE_RETENTION = QUANTUM_SIEVE / CLASSICAL_SIEVE
HASH_RETENTION = 0.5                                # Grover, iterations 24/49
LATTICEFOLD_FIELD_BITS = 64                         # eprint 2025/247, abstract


def field_needed(target_classical, nu=22, rho=0.25):
    """Invert the UDR ceiling: E >= target + nu - log2((1-rho)/2)."""
    return target_classical + nu - math.log2((1 - rho) / 2)


def degree_over(base_bits, E):
    return math.ceil(E / base_bits)


def classical_for_pq(pq_bits, retention):
    return pq_bits / retention


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    NU = 22

    sec("1. WHAT THE CEILING EQUATION DEMANDS OF A HASH-BASED FIELD")
    print(f"  {'target':>16} {'E needed':>10} {'deg over 31b':>13} "
          f"{'deg over 64b':>13} {'lattice':>9}")
    print("  " + "-" * 66)
    for tgt in (100, 128):
        E = field_needed(tgt, NU)
        print(f"  {'%d classical' % tgt:>16} {E:>10.0f} "
              f"{degree_over(31, E):>13} {degree_over(64, E):>13} "
              f"{'64-bit':>9}")
    for pq in (64, 128):
        E = field_needed(classical_for_pq(pq, HASH_RETENTION), NU)
        print(f"  {'%d PQ' % pq:>16} {E:>10.0f} "
              f"{degree_over(31, E):>13} {degree_over(64, E):>13} "
              f"{'64-bit':>9}")
    E128 = field_needed(classical_for_pq(128, HASH_RETENTION), NU)
    print(f"""
  At 128 post-quantum bits a hash-based system needs a {E128:.0f}-bit challenge field;
  LatticeFold+ states 64. A factor of {E128/LATTICEFOLD_FIELD_BITS:.1f}, and it compounds -- every query
  opening carries field elements, {E128/8:.0f} bytes each against 8.""")

    sec("2. WHY THE ESCAPE IS STRUCTURAL")
    print(f"""
  The ceiling equation contains E because a hash-based system's soundness comes
  from a challenge landing outside a bad set, measured against the challenge
  SPACE. Security scales 1:1 with field bits and cannot be bought elsewhere.

  M-SIS security is sourced from the lattice DIMENSION, not the field: the ring
  is R_q with q a 64-bit prime and the hardness parameter is beta. So the field
  stays small while security grows, and Theorem 2's ceiling does not apply.

  The post-quantum column compounds it:

      hash-based retains  {HASH_RETENTION:.4f}   (Grover on Fiat-Shamir)
      M-SIS      retains  {LATTICE_RETENTION:.4f}   (sieving exponents {QUANTUM_SIEVE}/{CLASSICAL_SIEVE})

  so 128 post-quantum bits costs a hash-based system {classical_for_pq(128, HASH_RETENTION):.0f} classical bits
  and a lattice system about {classical_for_pq(128, LATTICE_RETENTION):.0f}.""")

    sec("3. AN UNPLANNED CROSS-CHECK WITH pq_design.py")
    print(f"""
  pq_design.py recommends extension degree 9-10 over a 31-bit base for 128
  post-quantum bits, from its own cost model. The ceiling equation independently
  gives E >= {E128:.0f}, which over a 31-bit base is degree {degree_over(31, E128)}. Two derivations,
  same answer.""")

    sec("4. WHAT REMAINS UNPRICED -- THE LARGER HALF")
    print("""
  1. M-SIS DIMENSIONS. The beta a 64-bit LatticeFold+ instance needs for 128
     bits sits in a table behind a walled PDF. Without it, "64-bit field" is a
     field-size claim and not a parameter set: a small field with a huge
     dimension may pay in prover time what it saves in field.

  2. PROOF SIZES. LatticeFold+'s abstract claims its prover is "five to ten
     times faster" and its proofs "shorter" -- all relative to LatticeFold, not
     to a hash-based baseline. No absolute figure is quoted.

  3. THE LINE HAS MOVED PAST IT. Cyclo (2026/359), an l2-norm variant
     (2026/721) and ProtogaLattice (2026/1317) all improve on LatticeFold+, and
     all state gains relative to it rather than absolutely.

  So thread 4 is HALF closed. The field-size escape is a number now; the cost
  side is not. Saying so plainly is better than letting the priced half stand in
  for the whole.""")


if __name__ == "__main__":
    report()
