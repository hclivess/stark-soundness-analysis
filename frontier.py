"""
Post-quantum argument-system frontier: what "surpassing FRI" would actually require.

Three parts:

  A. QUANTUM ADJUSTMENT -- the security these systems actually have against a
     quantum adversary, which is not the number in their docs. Grinding is
     Grover-able and loses HALF its bits. Nobody advertises this.

  B. THE FRONTIER -- systems that already beat FRI on some axis, with their
     query/prover/verifier asymptotics and, critically, what assumption each
     one pays with.

  C. WHERE THE SLACK IS -- the decomposition of FRI's cost into terms, marked
     by whether each is improvable, conjecture-bound, or information-
     theoretically floored.

Asymptotics are transcribed from the cited literature. They are recalled, not
re-derived here; verify against the papers before building on them.
"""

import math
from stark_soundness import (INSTANCES, total_bits, best_m, bits_per_query,
                             queries_needed, proof_bytes)

# ===================================================== A. QUANTUM ADJUSTMENT

def quantum_bits(R, nu, E, s, g, regime, hash_bits=256):
    """
    Quantum-adjusted soundness.

      - Grinding / proof-of-work: Grover gives a quadratic speedup on the
        nonce search, so g bits of grinding are worth only g/2 bits.
      - Merkle collision resistance: h/2 classically (birthday); BHT gives
        h/3 quantum, though it needs implausible QRAM, so h/2 is the
        defensible conservative figure and h/3 the paranoid one.
      - The query-phase soundness itself is NOT known to admit a quantum
        speedup beyond Grover on the Fiat-Shamir transcript search, which is
        already what the grinding term models.
    """
    if regime == "johnson":
        classical, m_use = best_m(R, nu, E, s, g, regime)
    else:
        classical, m_use = total_bits(R, nu, E, s, g, regime)[0], 16

    # Grinding re-priced at half value under Grover.
    quantum_soundness = min(classical - g / 2, classical) if g else classical
    hash_cap = hash_bits / 3            # BHT collision search (needs large QRAM)

    quantum = min(quantum_soundness, hash_cap)
    binder = "grinding" if quantum_soundness <= hash_cap else "hash cap"
    return classical, quantum, binder


def section_a():
    print("=" * 100)
    print("A. QUANTUM ADJUSTMENT  (Grover halves grinding; BHT caps hash security)")
    print("=" * 100)
    print("Under the ethSTARK conjecture, 256-bit Merkle hashes.\n")
    hdr = (f"{'system':<24} {'g':>4} {'classical':>10} {'quantum':>9} "
           f"{'lost':>6} {'binder':>10}  {'fix':>22}")
    print(hdr)
    print("-" * len(hdr))
    for i in INSTANCES:
        E, nu, R = i["p"] * i["ext"], i["logn"] + i["R"], i["R"]
        c, q, binder = quantum_bits(R, nu, E, i["s"], i["g"], "conjectured")
        if binder == "grinding":
            extra = math.ceil((c - q) / bits_per_query(R, "conjectured"))
            fix = f"+{extra} queries" if extra else "none needed"
        else:
            fix = "wider hash (512-bit)"
        print(f"{i['name']:<24} {i['g']:>4} {c:>10.1f} {q:>9.1f} "
              f"{c-q:>6.1f} {binder:>10}  {fix:>22}")
    print("\n  CAVEAT: the 85.3-bit hash cap is 256/3, the BHT bound, which requires")
    print("  quantum RAM at a scale most cryptographers consider implausible. The")
    print("  defensible figure is 256/2 = 128, which binds nothing here. It is in")
    print("  the table because if you are designing for a 30-year horizon you should")
    print("  see which systems it would bite first -- not because it bites today.")
    print("\n  Grinding is the cheapest classical security in the whole design --")
    print("  it costs the verifier nothing. Against a quantum adversary it is the")
    print("  most expensive: half of it evaporates, and the only way to buy it")
    print("  back is queries, which the verifier does pay for.")
    print("\n  A system claiming 100 post-quantum bits while leaning on 20+ bits of")
    print("  grinding is claiming ~90. This is the single most common overstatement")
    print("  in deployed STARK parameter sets.")


# ========================================================== B. THE FRONTIER

FRONTIER = [
    dict(name="FRI (baseline)", year=2018,
         cite="Ben-Sasson, Bentov, Horesh, Riabzev",
         queries="O(lambda * log d / log(1/rho))",
         prover="O(n log n)", verifier="O(lambda log d)",
         assumption="CRHF + ROM", pq="yes",
         beats="baseline"),
    dict(name="DEEP-FRI", year=2019,
         cite="Ben-Sasson, Goldberg, Kopparty, Saraf",
         queries="O(lambda * log d / log(1/rho))",
         prover="O(n log n)", verifier="O(lambda log d)",
         assumption="CRHF + ROM", pq="yes",
         beats="soundness up to the Johnson bound, not just unique decoding"),
    dict(name="Proximity Gaps", year=2020,
         cite="Ben-Sasson, Carmon, Ishai, Kopparty, Saraf",
         queries="O(lambda * log d / log(1/rho))",
         prover="O(n log n)", verifier="O(lambda log d)",
         assumption="CRHF + ROM", pq="yes",
         beats="batching many polys at the cost of one; the modern soundness bound"),
    dict(name="STIR", year=2024,
         cite="Arnon, Chiesa, Fenzi, Yogev",
         queries="O(log d + lambda * log log d)",
         prover="O(n log n)", verifier="O(lambda log log d)",
         assumption="CRHF + ROM", pq="yes",
         beats="FRI on query count -- shrinks the RATE each round instead of "
               "holding it fixed; ~1.25-2.4x smaller proofs in practice"),
    dict(name="WHIR", year=2024,
         cite="Arnon, Chiesa, Fenzi, Yogev",
         queries="O(log d + lambda * log log d)",
         prover="O(n log n)", verifier="~100 microseconds concrete",
         assumption="CRHF + ROM", pq="yes",
         beats="verifier time by orders of magnitude; native multilinear "
               "(sumcheck) queries, so it drops the univariate encoding tax. "
               "CAVEAT: its mutual correlated agreement up-to-capacity "
               "conjecture was among those refuted by Crites-Stewart in 2025, "
               "so its CONJECTURED parameters need repricing; the verifier-time "
               "and query-complexity wins are unaffected"),
    dict(name="BaseFold", year=2024,
         cite="Zeilberger, Chen, Fisch",
         queries="O(lambda log d)", prover="O(n log n)",
         verifier="O(log^2 d)",
         assumption="CRHF + ROM", pq="yes",
         beats="field-agnostic -- works over ANY sufficiently large field, no "
               "FFT-friendly structure needed; foldable linear codes"),
    dict(name="Binius", year=2023,
         cite="Diamond, Posen",
         queries="O(lambda log d)", prover="O(n) field ops in GF(2^k)",
         verifier="O(lambda log d)",
         assumption="CRHF + ROM", pq="yes",
         beats="prover cost on bit-level witnesses -- binary tower fields mean "
               "a 1-bit value costs 1 bit, not 31"),
    dict(name="Blaze", year=2024,
         cite="Branco, Chiesa, Fenzi, et al.",
         queries="O(lambda)", prover="O(n) LINEAR",
         verifier="polylog",
         assumption="CRHF + ROM", pq="yes",
         beats="linear-time prover via interleaved RAA codes; no FFT at all"),
    dict(name="LaBRADOR", year=2023,
         cite="Beullens, Seiler",
         queries="n/a (not an IOP)", prover="O(n)",
         verifier="O(n) -- NOT succinct",
         assumption="M-SIS (lattice)", pq="yes",
         beats="proof SIZE massively -- ~50KB for huge R1CS, vs 100s of KB; "
               "but verification is linear, so it does not scale as a rollup"),
    dict(name="Greyhound", year=2024,
         cite="Nguyen, Seiler",
         queries="n/a", prover="O(n)", verifier="O(sqrt(n))",
         assumption="M-SIS (lattice)", pq="yes",
         beats="sqrt verifier lattice PCS, ~50KB proofs; first practical "
               "lattice PCS competitive with hash-based on size"),
    dict(name="Threshold halving", year=2026,
         cite="eprint 2026/858",
         queries="kappa(R) x FRI, kappa = (R/2)/(1-log2(1+2^-R))",
         prover="unchanged", verifier="unchanged (only q recalibrated)",
         assumption="CRHF + ROM", pq="yes",
         beats="the DISPROVED capacity conjecture -- first UNCONDITIONAL "
               "soundness above the Johnson bound. commit term O(n)/|F| vs "
               "BCIKS's O(n^2)/|F|, worth ~nu bits of ceiling. Needs k=2^m and "
               "a fixed-point-free involution on the domain (standard for "
               "deployed FRI). See regimes.py Thms 4-6"),
    dict(name="Action-Orbit", year=2026,
         cite="Chai, Fan (eprint 2026/861)",
         queries="n/a", prover="unchanged", verifier="unchanged",
         assumption="CRHF + ROM + conjecture Q2", pq="yes",
         beats="O(1)/|F| commit bound above Johnson on PLAIN RS; 79.8 KiB vs "
               "161.4 KiB (interleaved RS) and 281.2 KiB (folded RS) at 128-bit. "
               "Conditional on a sparse-worst-case dominance conjecture"),
]


def section_b():
    print("\n" + "=" * 100)
    print("B. THE FRONTIER -- who already beats FRI, on what axis, paying with what")
    print("=" * 100)
    for f in FRONTIER:
        print(f"\n  {f['name']}  ({f['year']}) -- {f['cite']}")
        print(f"    queries   : {f['queries']}")
        print(f"    prover    : {f['prover']}")
        print(f"    verifier  : {f['verifier']}")
        print(f"    assumption: {f['assumption']}   post-quantum: {f['pq']}")
        print(f"    beats FRI : {f['beats']}")

    print("\n" + "-" * 100)
    print("  READ THIS AS A PARETO FRONTIER, NOT A RANKING.")
    print("-" * 100)
    print("""
  Your three requirements -- post-quantum, scaling, resilient -- cannot be
  jointly maximised. They trade against each other:

    RESILIENT (minimal assumptions)
        Hash-based IOPs rest on collision resistance + the random oracle model.
        That is the weakest assumption anyone knows how to build succinct
        arguments from. Nothing on this list is MORE resilient than FRI/STIR/
        WHIR; they are already at the floor.

    SCALING (proof size / verifier cost)
        Lattice systems (LaBRADOR, Greyhound) produce dramatically smaller
        proofs. They pay with M-SIS -- a structured assumption with a live
        cryptanalytic literature and parameter estimates that have moved
        before. Post-quantum, yes. As resilient as a hash? No.

    So "surpass STARKs, post-quantum, scaling, resilient" resolves to one of:
      (a) stay hash-based and take STIR/WHIR's query-complexity win  <- free lunch, take it
      (b) move to lattices and accept a structured assumption        <- size win, resilience loss
      (c) attack the conjecture gap itself                           <- see section C
""")


# ====================================================== C. WHERE THE SLACK IS

def section_c():
    print("=" * 100)
    print("C. WHERE THE SLACK IS -- decomposition of the FRI security budget")
    print("=" * 100)
    print("""
  Any claim to "surpass" has to name which of these terms it improves.

  TERM 1: per-query yield -- log2(1/rho) conjectured vs (1/2)log2(1/rho) proven
      STATUS: *** THE CONJECTURE WAS DISPROVED IN LATE 2025. ***

      CORRECTION. An earlier version of this file called proving the RS capacity
      conjecture "the single highest-leverage open problem in the entire field."
      That was wrong: it is not open. Crites-Stewart (eprint 2025/2046) refuted
      the correlated agreement, mutual correlated agreement (WHIR) and
      list-decodability (DEEP-FRI) up-to-capacity conjectures, and Diamond-Gruen
      (2025/2010) gave an independent counterexample over multiplicative
      subgroups of prime fields. The mechanism: correlated agreement with small
      enough error implies list decoding, so a gap beyond capacity would imply
      impossibly good list-decoding bounds.

      WHAT SURVIVES. Johnson-bound soundness is untouched. The counterexamples
      live in the regime rho -> 0, gamma -> 1, whereas deployed rates are
      rho in [1/16, 1/2], so no known counterexample attacks a deployed
      parameter set directly. Deployed systems are not known to be broken --
      they are no longer known to be sound at their advertised level.

      WHAT IS NOW OPEN: Crites-Stewart's minimally-modified conjectures
      restricted to the list-decoding capacity bound; the Q2 sparse-worst-case
      dominance conjecture of eprint 2026/861; and whether folded RS (which
      Goyal-Guruswami show DOES admit a gap at capacity) can be deployed
      without the 2.0x-3.5x proof-size cost of the code-class change.

      THE REPLACEMENT LEVER: threshold halving (eprint 2026/858) gives the first
      UNCONDITIONAL bound above the Johnson radius, at a query multiplier
      kappa(R) = (R/2)/(1 - log2(1+2^-R)) -- see regimes.py, Theorem 4.

  TERM 2: commit-phase / field-size term -- E - 2*nu - 7*log2(m+1/2) - 1.5R
      STATUS: IMPROVABLE, and demonstrably loose.
      The (m+1/2)^7 factor in BCIKS20 is an artifact of the proof technique,
      not a lower bound. Nobody believes the exponent 7 is tight. Shaving it
      to, say, (m+1/2)^3 would hand every 31-bit-field system ~11 free bits
      (see stark_soundness.py section 5) and is a proof-engineering exercise
      on an existing theorem, not a new assumption.
      HIGHEST RATIO OF (impact) TO (difficulty) ON THIS LIST.

  TERM 3: number of queries s
      STATUS: FLOORED for FRI, IMPROVED by STIR/WHIR.
      Fixed-rate folding forces s = lambda/log(1/rho). STIR escapes by
      shrinking rho each round. This is already solved -- it is adoption lag,
      not an open problem. Any deployed system still on vanilla FRI is
      leaving 1.25-2.4x on the table today.

  TERM 4: grinding g
      STATUS: HALVED BY GROVER. See section A.
      Free classically, half-price quantum. Systems that lean on it are
      overstating post-quantum security.

  TERM 5: the arithmetization (AIR/PLONKish -> polynomial)
      STATUS: WIDE OPEN, and underexplored relative to the proximity test.
      Everyone optimises the PCS; the encoding of computation into constraints
      is where Binius found its win (bit-level witnesses) and where WHIR found
      its (skip the univariate detour entirely). More slack here than in FRI.

  WHAT IS *NOT* SLACK:
      Query complexity of an IOPP for a rate-rho code has an information-
      theoretic floor of ~lambda/log(1/rho) queries in the correlated-agreement
      framework. You do not beat that by tuning FRI. You beat it by changing
      the CODE (Binius, Blaze, BaseFold) or the PROXIMITY TEST (STIR, WHIR).
      Any proposal that claims to beat it while still testing proximity to a
      rate-rho RS code by sampling is wrong, and that is a cheap filter to
      apply to anyone pitching you one.
""")


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
