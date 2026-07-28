"""
The BCS error is a SUM, and its hash term pins a QROM loss exponent of 3, not 2.

Two things fall out of reading the actual theorem, and the second one sharpens
iteration 24's bracket into something with no unknown constant in it.

SOURCE
------
Chiesa-Yogev, "Building Cryptographic Proofs from Hash Functions", LaTeX source
at github.com/hash-based-snargs-book commit 305fa3d (2026-03-25), Theorem
[bcs-soundness] (line 17834), expanded from the macros at lines 1077-1090:

    eps_ARG(lambda, n, t)
        <=  eps_IOP-SR(lambda + salt, n, t)      <- the IOP's own error
          + eps_MT(lambda, proof_lengths, t, t+1) <- Merkle commitment extraction
          + t^2 / 2^lambda                        <- the Fiat-Shamir hash chain

and "the additive error <= 3.5 * t^2 / 2^lambda if t >= 2(log l + 1) * l",
where l is the proof length -- a condition every deployed system satisfies.

FINDING 1 -- THE min-MODEL IS AN APPROXIMATION, AND ITS ERROR IS BOUNDED
------------------------------------------------------------------------
This repo computes total soundness as a MINIMUM over terms. The theorem composes
by SUM. In bits those differ:

    bits(sum)  =  min_i k_i  -  log2( sum_i 2^(min_k - k_i) )
               >=  min_i k_i  -  log2(#terms)

so the min-model OVERSTATES by between 0 and log2(#terms) bits -- up to 2.3 bits
for a five-term model. That is an assumption the repo has relied on for 26
iterations without checking.

Measured on the seven verified zkVMs (section 1), the actual bias is 0.00 to
0.34 bits: the terms are far enough apart that the sum is dominated by its
smallest. The worst cases are SP1 and OpenVM, whose query and commit terms sit
~2 bits apart. So the min-model is sound to about a third of a bit here -- but
the bound is log2(#terms), and a system whose terms happen to coincide would pay
the full penalty.

FINDING 2 -- THE QROM LOSS IS TERM-DEPENDENT, AND BOTH FAMILIES ARE PINNED
---------------------------------------------------------------------------
Iteration 24 wrote the bracket k/c <= PQ <= k/2 with c >= 2 unknown. Reading the
additive term shows c is not one constant. It depends on which search problem
the term reduces to, and for the two dominant families the exponent is TIGHT in
both directions:

    term family        classical   quantum   loss   both bounds tight because
    ---------------------------------------------------------------------
    challenge search   1/eps       1/sqrt(eps)  2   Grover achieves; BBBV forbids better
    hash chain / MT    2^(lambda/2) 2^(lambda/3) 3  BHT achieves; Zhandry proves Omega

The t^2/2^lambda shape IS the birthday bound: classical security is lambda/2,
not lambda. Quantumly, generic collision finding in a random function costs
Theta(2^(lambda/3)) -- BHT's algorithm above, Zhandry's Omega(N^(1/3)) lower
bound below. So the hash family loses a factor 3, MORE than the halving.

That is a concrete counterexample to reading `PQ = classical/2` as universal,
and it is the first place in this repo where c > 2 is established rather than
feared.

FINDING 3 -- MY OWN 128-PQ RECOMMENDATION USES THE WRONG HASH EXPONENT
-----------------------------------------------------------------------
pq_design.py does model a hash floor, at line 83:

    def pq(c):
        return min(c / 2.0, 128.0)   # 256-bit hash floor never binds below 128

So the term is not missing -- but the exponent is the classical one. A 256-bit
digest gives 128 bits against a CLASSICAL collision finder (lambda/2); against a
quantum one it gives lambda/3 = 85. The comment "never binds below 128" is
therefore true classically and false post-quantum, in a function whose entire
job is to report post-quantum bits.

Under the conservative reading a 256-bit digest caps the design at 85 PQ bits,
below the 128 the extension degree was chosen to reach. The complete
recommendation is degree 10 AND a 384-bit digest (13 field elements over a
31-bit base). Extension degree alone does not buy 128 PQ bits.

The memory-bounded reading rescues the original number: if quantum collision
finding is held to 2^(lambda/2) -- because BHT's 2^(lambda/3) requires
2^(lambda/3) quantum-accessible memory, widely considered unrealistic -- then
256 bits suffices and pq_design.py's figure stands. That assumption was never
stated in the file; it was carried silently in a one-line comment.

CAVEAT ON SCOPE
---------------
Digest sizes were NOT read from each project's source, unlike every parameter in
SOURCES.md. Section 3 is therefore a REQUIREMENTS table -- what each reported
security level demands of lambda -- not an audit of what each system ships. The
repo does not claim any specific system is under-sized.
"""

import math

ZKVMS = [("SP1 6.1.0",    124, 2, 21, 124, 16, 100, "UDR"),
         ("OpenVM 1.5.0", 124, 1, 23, 193, 20, 100, "UDR"),
         ("Airbender",    124, 1, 24,  87, 28,  67, "JBR"),
         ("Pico",         124, 1, 22,  84, 16,  53, "JBR"),
         ("ZisK 0.16.1",  192, 1, 21, 229, 16, 128, "JBR"),
         ("RISC Zero",    124, 2, 21,  50,  0,  48, "JBR"),
         ("Miden",        128, 3, 18,  27, 16,  55, "JBR")]


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def commit_udr(R, nu, E):
    gamma = (1 - 2.0 ** -R) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def bits_of_sum(*ks):
    """Compose error terms the way the theorem does: add them, then take bits."""
    kmin = min(ks)
    return kmin - math.log2(sum(2.0 ** (kmin - k) for k in ks))


def composition_bias(*ks):
    """How much the min-model overstates: min(k) - bits(sum). In [0, log2(#terms)]."""
    return min(ks) - bits_of_sum(*ks)


def hash_bits_classical(lam):
    """Birthday: t^2/2^lambda reaches 1 at t = 2^(lambda/2)."""
    return lam / 2.0


def hash_bits_quantum(lam, memory_bounded=False):
    """BHT/Zhandry: Theta(2^(lambda/3)); lambda/2 if quantum memory is limited."""
    return lam / 2.0 if memory_bounded else lam / 3.0


def digest_needed(target_bits, quantum=True, memory_bounded=False):
    """Digest size lambda required to support `target_bits` of security."""
    if not quantum:
        return 2 * target_bits
    return 2 * target_bits if memory_bounded else 3 * target_bits


def sec(t):
    print("\n" + "=" * 94)
    print(t)
    print("=" * 94)


def report():
    from regime_crossover import commit_jbr, m_eq

    sec("1. SUM vs MIN: the composition bias the repo has been carrying")
    print(f"  {'system':<15} {'k_query':>8} {'k_commit':>9} {'min':>7} "
          f"{'bits(sum)':>10} {'bias':>6}")
    print("  " + "-" * 60)
    biases = []
    for nm, E, R, T, s, g, rep, reg in ZKVMS:
        nu = T + R
        kq = s * (yield_udr(R) if reg == "UDR" else yield_jbr(R, 1000.0)) + g
        kc = commit_udr(R, nu, E) if reg == "UDR" else commit_jbr(R, nu, E, m_eq(R))
        b = composition_bias(kq, kc)
        biases.append(b)
        print(f"  {nm:<15} {kq:>8.1f} {kc:>9.1f} {min(kq,kc):>7.1f} "
              f"{bits_of_sum(kq,kc):>10.1f} {b:>6.2f}")
    print(f"""
  Worst bias {max(biases):.2f} bits, against a theoretical worst case of
  log2(2) = 1.00 for two terms and log2(5) = 2.32 for a five-term model. The
  terms in deployed configs are far enough apart that the sum is dominated by
  its smallest, so the min-model holds to a third of a bit. That is a
  VALIDATION of an assumption, not a correction -- but the assumption was
  untested until now, and it is not free in general.""")

    sec("2. THE OMITTED TERM: t^2/2^lambda is the birthday bound")
    print("""
  The BCS theorem's additive error is 3.5*t^2/2^lambda. This repo models the
  IOP's own error only, so this term has never appeared in any figure here.
  Its shape is exactly collision finding, which fixes both columns:\n""")
    print(f"  {'digest lambda':>13} {'classical':>10} {'PQ (BHT)':>9} "
          f"{'PQ (mem-bounded)':>17}")
    print("  " + "-" * 54)
    for lam in (128, 160, 248, 256, 384, 512):
        print(f"  {lam:>13} {hash_bits_classical(lam):>10.0f} "
              f"{hash_bits_quantum(lam):>9.0f} "
              f"{hash_bits_quantum(lam, True):>17.0f}")
    print("""
  Classical security is lambda/2, never lambda. Quantum is lambda/3 by BHT's
  algorithm, and Zhandry's Omega(N^(1/3)) says no better -- so this term loses a
  factor THREE, not two. Iteration 24 could only bracket c >= 2; here c = 3
  exactly, which is the first established case of c > 2 in this repository.""")

    sec("3. REQUIREMENTS: what each reported level demands of the digest")
    print("  (a requirements table, NOT an audit -- digest sizes were not read"
          "\n   from source, unlike every parameter in SOURCES.md)\n")
    print(f"  {'target bits':>12} {'classical needs':>16} {'PQ needs (BHT)':>15} "
          f"{'31-bit elements':>16}")
    print("  " + "-" * 64)
    for tgt in (48, 64, 100, 128):
        c_, q_ = digest_needed(tgt, quantum=False), digest_needed(tgt)
        print(f"  {tgt:>12} {c_:>16} {q_:>15} {math.ceil(q_/31):>16}")
    print("""
  A 256-bit digest -- the ubiquitous default -- supports 128 classical bits but
  only 85 post-quantum bits under the conservative reading.""")

    sec("4. CORRECTION TO pq_design.py's RECOMMENDATION")
    tgt = 128
    print(f"""
  pq_design.py DOES model a hash floor -- line 83:

      def pq(c):
          return min(c / 2.0, 128.0)   # 256-bit hash floor never binds below 128

  but lambda/2 is the CLASSICAL collision exponent. Against a quantum collision
  finder a 256-bit digest gives lambda/3 = {hash_bits_quantum(256):.0f}, so in a function whose whole
  job is post-quantum bits, the floor is set with the wrong exponent and the
  comment is false in exactly the column it is used for.

      extension:  E - nu >= 2*{tgt} = {2*tgt}   ->  degree 10 gives 310 - 22 = 288  OK
      digest:     lambda >= 3*{tgt} = {3*tgt}   ->  256-bit default gives  {hash_bits_quantum(256):.0f}  FAILS

  With a 256-bit digest the design is capped at {hash_bits_quantum(256):.0f} PQ bits whatever the
  extension degree is. The complete recommendation is degree 10 AND a {3*tgt}-bit
  digest ({math.ceil(3*tgt/31)} field elements over a 31-bit base).

  The memory-bounded reading rescues the original figure: if quantum collision
  finding is held to 2^(lambda/2) -- BHT's 2^(lambda/3) needs 2^(lambda/3)
  quantum-accessible memory, widely thought unrealistic -- then {2*tgt} bits
  suffice and pq_design.py's number stands. Both readings are defensible. The
  point is that the file silently assumed one of them in a comment.""")


if __name__ == "__main__":
    report()
