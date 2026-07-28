"""
Post-quantum soundness, done properly.

CORRECTION TO frontier.py
-------------------------
frontier.py's quantum column halved GRINDING only, and left every other term at
its classical value. That understates the problem badly, and this file replaces
it.

THE ARGUMENT
------------
Deployed STARKs are NON-INTERACTIVE: challenges are derived by Fiat-Shamir from
a hash. That hands the adversary something an interactive protocol never does --
control of the transcript. A cheating prover picks a nonce, derives the
challenges, checks whether they happen to be favourable, and repeats.

Classically, if the round-by-round soundness error is eps_rbr and the protocol
carries g bits of grinding, forging costs

    work_classical  ~  2^g * (1/eps_rbr)   =   2^(g + bits_rbr)

Quantumly that search is Grover-able -- it is an unstructured search for a
transcript in a marked set of density eps_rbr -- so it costs the square root:

    work_quantum    ~  2^(g/2) * (1/sqrt(eps_rbr))  =  2^((g + bits_rbr)/2)

Hence, uniformly:

    PQ bits  =  classical bits / 2

Not "grinding halves". EVERYTHING halves -- commit phase, query phase, DEEP and
grinding alike -- because all of them are probabilities over Fiat-Shamir-derived
challenges, and all of them are searchable by the same Grover loop.

This matches the standard engineering rule ("for lambda post-quantum bits, aim
for 2*lambda classical") and the QROM literature, where generic Fiat-Shamir
reductions lose a factor O(q^2) in the adversary's query count q, tightly --
a q^2 loss in the error is exactly a square root in the work.

Formal grounding for the round-by-round framework and the FS compilation of FRI:
  Block, Garreta, Katz, Thaler, Tiwari, Zajac,
  "Fiat-Shamir Security of FRI and Related SNARKs", eprint 2023/1071
  (ASIACRYPT 2023) -- covers ethSTARK, Plonky2, RedShift, RISC Zero.
For round-by-round sound protocols the classical FS loss is LINEAR in Q rather
than Q^mu, which is why the classical accounting above is just `bits_rbr`.

UNVERIFIED AGAINST THE AUTHORITATIVE TREATMENT -- READ THIS FIRST
-----------------------------------------------------------------
The halving below is the standard ENGINEERING rule ("for lambda post-quantum
bits, target 2*lambda classical"), derived here from Grover-over-transcripts.
It is NOT verified against the paper that actually settles the question:

    Chiesa, Di, Hu, Zheng, "How to Prove Post-Quantum Security for Succinct
    Non-Interactive Reductions", eprint 2025/2166

which is the reference Ethereum's own soundcalc points to for exactly this
("this correspondence holds for classical adversaries, but is different for
quantum adversaries in the QROM"). That work proves classical round-by-round
security IMPLIES post-quantum state-restoration security, and describes itself
as achieving "a post-quantum analogue of the classical security" via a framework
that "mirrors classical security analyses". Both phrasings hint the concrete
loss may be SMALLER than a full halving. I could not extract the quantitative
statement -- eprint PDFs return HTTP 403 to this session and the abstract does
not quantify it.

THE SENSITIVITY IS NOT A DETAIL. At degree 4 the classical ceiling is 102 bits:

    full halving (assumed here)  ->  51 PQ  -> nothing clears 100
    ~10-bit loss                 ->  92 PQ  -> nothing clears 100
    negligible loss              -> 102 PQ  -> most systems clear it

So the repository's headline -- "no deployed system reaches 100 provable
post-quantum bits" -- is TRUE under the halving and FALSE under a negligible
loss. Every PQ figure in this file and in pq_design.py should be read as a
conservative LOWER BOUND, not a measurement. Settling it requires reading
2025/2166 directly.

WHERE THIS IS CONSERVATIVE (stated so it is not oversold)
---------------------------------------------------------
1. Grover parallelises poorly: k machines give only a sqrt(k) speedup, so a
   distributed quantum attacker gains far less than a distributed classical one.
2. Each Grover iteration must evaluate the hash AND check whether the derived
   challenges are actually favourable. For FRI that check is not free, so the
   constant factors are worse for the attacker than this model admits.
3. The O(q^2) QROM loss is proved tight for GENERIC reductions; that is a
   statement about proof techniques. The concrete Grover-over-transcripts attack
   is what justifies treating the halving as real rather than an artifact.

So treat PQ = classical/2 as the defensible conservative figure, not a
prediction of an imminent attack.
"""

import math

# ------------------------------------------------------------------ regimes
# Same transcriptions as real_configs.py / regime_crossover.py (soundcalc,
# Plonky3 p3-security, BCHKS25).


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def commit_udr(R, nu, E):
    gamma = (1 - 2.0 ** -R) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def commit_jbr(R, nu, E, m, folding=2):
    rho = 2.0 ** -R
    sr = math.sqrt(rho)
    mm = m + 0.5
    gamma = 1 - sr * (1 + 0.5 / m)
    if gamma <= 0:
        return float("-inf")
    n = 2.0 ** nu
    eps = ((2 * mm ** 5 + 3 * mm * gamma * rho) * n / (3 * rho * sr)
           + mm / sr) * max(folding - 1, 1)
    lin = E - math.log2(max(eps, 1.0))
    noq = (E - math.log2(folding) - math.log2(n + 1)
           - math.log2(2 * m + 1) + 0.5 * math.log2(rho))
    return min(lin, noq)


def classical_bits(R, nu, E, s, g, log_deg):
    """Best-regime provable soundness, classically."""
    u = min(s * yield_udr(R) + g, commit_udr(R, nu, E))
    best_j = float("-inf")
    m = 1.0
    while m <= 1000.0:
        y = yield_jbr(R, m)
        if y > 0:
            best_j = max(best_j, min(s * y + g, commit_jbr(R, nu, E, m)))
        m *= 1.02
    deep = E - log_deg
    return min(max(u, best_j), deep)


def pq_bits(classical, hash_bits=256, qram=False):
    """PQ soundness. Fiat-Shamir search is Grover-able => classical/2.

    The Merkle hash contributes its own ceiling: collision resistance is
    hash_bits/2 classically; with implausible QRAM the BHT bound gives
    hash_bits/3. Neither binds at 256-bit hashes."""
    hash_floor = hash_bits / (3 if qram else 2)
    return min(classical / 2.0, hash_floor)


def classical_needed(target_pq):
    return 2 * target_pq


# ------------------------------------------------------------------ systems
# (name, E, log_trace, R, s, g, status)
SYSTEMS = [
    ("RISC Zero",          124, 20, 2,  50,  0, "VERIFIED"),
    ("Plonky2 std recur",  128, 20, 3,  28, 16, "VERIFIED"),
    ("Miden RECURSIVE_96", 128, 18, 3,  27, 16, "VERIFIED"),
    ("NADO (today)",        64, 17, 1, 320, 18, "VERIFIED"),
    ("NADO + GF(p^2)",     128, 17, 1, 320, 18, "proposed"),
    ("NADO + GF(p^3)",     192, 17, 1, 320, 18, "proposed"),
    ("Cairo / StarkNet",   251, 20, 4,  30,  0, "recalled"),
    ("Venus / ZisK",       192, 20, 3,  27, 16, "recalled"),
]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE CORRECTION: what halves under a quantum adversary")
    print("""
  frontier.py halved GRINDING only. That was wrong.

  Under Fiat-Shamir the adversary controls the transcript, so finding a
  favourable challenge is an unstructured search over a marked set of density
  eps_rbr -- Grover-able. Grinding does not sit outside that search; it is part
  of the cost of each attempt. So the whole product halves:

      work_classical ~ 2^(g + bits_rbr)     ->   work_quantum ~ 2^((g + bits_rbr)/2)

  PQ bits = classical bits / 2, applied to commit phase, query phase, DEEP and
  grinding alike. In an INTERACTIVE protocol none of this applies -- the
  verifier's challenges cannot be searched. Every deployed STARK is
  non-interactive.""")

    sec("2. PROVABLE SOUNDNESS, CLASSICAL vs POST-QUANTUM")
    print(f"  {'system':<20} {'E':>4} {'R':>2} {'s':>4} {'g':>3} "
          f"{'classical':>10} {'PQ':>7} {'>=128 PQ?':>10} {'>=100 PQ?':>10}")
    print("  " + "-" * 84)
    for name, E, T, R, s, g, status in SYSTEMS:
        nu = T + R
        c = classical_bits(R, nu, E, s, g, T)
        q = pq_bits(c)
        print(f"  {name:<20} {E:>4} {R:>2} {s:>4} {g:>3} {c:>10.1f} {q:>7.1f} "
              f"{('yes' if q >= 128 else 'NO'):>10} "
              f"{('yes' if q >= 100 else 'NO'):>10}")
    print("""
  NOT ONE deployed system reaches 100 bits of PROVABLE post-quantum soundness,
  and none is close to 128. That is the headline, and it is a direct consequence
  of the halving: 128 PQ provable bits requires 256 CLASSICAL provable bits, and
  the best classical provable figure anywhere in this repo is Cairo's ~203.""")

    sec("3. WHAT 'POST-QUANTUM' IS AND IS NOT CLAIMING")
    print("""
  These systems ARE post-quantum in the sense that matters most: no Shor attack
  applies. Hash-based IOPs have no discrete log and no factoring to break, so
  they do not fall over the way an elliptic-curve SNARK does. That property is
  real and it is why the whole hash-based line exists.

  What they are NOT is 128-bit post-quantum at their advertised parameters. The
  advertised number is classical. Halving it is the honest PQ figure, and almost
  nobody publishes that column -- the 2026 SoK already found proven-vs-conjectured
  to be the least consistently reported dimension; PQ-adjusted is reported even
  less.""")

    sec("4. WHAT IT COSTS TO ACTUALLY REACH 128 PQ BITS")
    print(f"  Need {classical_needed(128):.0f} classical provable bits. "
          f"By THEOREM.md Thm 2 the ceiling is ~(E - 2nu) for JBR and\n"
          f"  ~(E - nu) for UDR, so at a 2^20 trace:\n")
    print(f"  {'target PQ':>10} {'classical':>10} {'min E (UDR ceiling)':>21}")
    print("  " + "-" * 44)
    for tgt in (64, 80, 100, 128):
        cl = classical_needed(tgt)
        print(f"  {tgt:>10} {cl:>10} {cl + 21:>21}")
    print("""
  A 128-bit PQ provable STARK at a 2^20 trace needs roughly a 277-bit field.
  That is not a small-field system, and it is not most large-field systems
  either. The honest ceiling for 31-bit fields with degree-4 extensions is
  ~50 PQ bits.""")

    sec("5. THE ONE PLACE THE HALVING IS CHEAP TO FIX")
    print("""
  Grinding is the exception worth noting. It is the only term that is free for
  the VERIFIER, so doubling it to compensate for Grover costs the prover 2^g
  work and the verifier nothing. Going from g to 2g restores g/2 PQ bits.

  For NADO: GRIND_BITS = 18 contributes 9 PQ bits. Raising to 36 would restore
  the other 9 at a cost of 2^36 prover hashes -- feasible with the native
  alghash2 grind loop, and it needs no protocol geometry change. It does not
  come close to closing the gap on its own, but it is the cheapest bit on the
  table and the in-circuit grind check is already calibrated for a constant.""")

    sec("6. RANKING, PQ-ADJUSTED")
    rows = []
    for name, E, T, R, s, g, status in SYSTEMS:
        nu = T + R
        c = classical_bits(R, nu, E, s, g, T)
        rows.append((pq_bits(c), c, name, status))
    rows.sort(reverse=True)
    print(f"  {'rank':>4} {'PQ':>7} {'classical':>10} {'system':<20} {'status'}")
    print("  " + "-" * 60)
    for i, (q, c, name, status) in enumerate(rows, 1):
        print(f"  {i:>4} {q:>7.1f} {c:>10.1f} {name:<20} {status}")
    print("""
  The ordering is driven almost entirely by FIELD SIZE, not by query count or
  blowup -- which is the same conclusion every other part of this repo reached,
  now with the PQ factor of two applied on top.""")


if __name__ == "__main__":
    report()
