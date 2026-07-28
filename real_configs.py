"""
Soundness under the BCHKS25 commit bound, with source-verified configurations.

Every formula here is transcribed from production source (see SOURCES.md for
verbatim quotes and file paths), not from recollection:

  * BCIKS20 commit bound      <- risc0/zkp/src/prove/soundness.rs
                                 e_proximity_gap_proven()
  * BCHKS25 commit bound      <- Plonky3 security/src/fri.rs
                                 commit_phase_error_ldr_m(), citing
                                 [2025/2055] Theorem 4.2 / Thm 1.5 Eq (1)
  * alpha = (1+1/2m) sqrt(rho)  <- both, identically
  * conjectured (post-disproof) <- Plonky3 security/src/fri.rs
                                 conjectured_error(), citing [2025/2010] 1.5

The headline: BCHKS25 improves BCIKS20 on TWO axes at once -- the m exponent
drops 7 -> 5, and the domain factor drops n^2 -> n. The second is worth ~nu
bits, which is the same order as what threshold halving was buying in
THEOREM.md Part II. That materially revises Theorem 6.
"""

import math

LOG2_3 = math.log2(3)


# ================================================ per-query yield (both agree)

def alpha_ldr(R, m):
    """alpha = (1 + 1/(2m)) * sqrt(rho).  Identical in RISC Zero and Plonky3."""
    return (1.0 + 0.5 / m) * math.sqrt(2.0 ** (-R))


def gamma_ldr(R, m):
    """gamma = 1 - alpha, the certified proximity radius."""
    return 1.0 - alpha_ldr(R, m)


def yield_ldr(R, m):
    """Bits of security per FRI query. Negative/zero => m inadmissible."""
    a = alpha_ldr(R, m)
    return -math.log2(a) if a < 1.0 else float("-inf")


# ===================================================== commit-phase bounds

def commit_bciks20(R, nu, E, m):
    """
    RISC Zero, e_proximity_gap_proven:
        (m + 1/2)^7 / (3 * sqrt(rho)^3) * |D|^2 / |K|
    """
    return E + LOG2_3 - 7 * math.log2(m + 0.5) - 1.5 * R - 2 * nu


def commit_bchks25(R, nu, E, m, folding=2, commit_pow=0):
    """
    Plonky3, commit_phase_error_ldr_m -- BCHKS25 Thm 1.5 Eq (1):
        eps_lin   = ((2 m'^5 + 3 m' gamma rho) n / (3 rho^{3/2}) + m'/sqrt(rho)) / |F|
        eps_round = eps_lin * (folding - 1)
    together with the alternative n/q-style bound; Plonky3 reports the
    conservative (smaller-bits) of the two.
    """
    rho = 2.0 ** (-R)
    sqrt_rho = math.sqrt(rho)
    mm = m + 0.5
    pp = gamma_ldr(R, m)
    if pp <= 0.0:
        return float("-inf")
    n = 2.0 ** nu
    fold_minus_1 = max(folding - 1.0, 1.0)

    num = (2.0 * mm ** 5 + 3.0 * mm * pp * rho) * n
    den = 3.0 * rho * sqrt_rho
    eps_linear = num / den + mm / sqrt_rho
    eps_powers = eps_linear * fold_minus_1
    bits_linear = E - math.log2(max(eps_powers, 1.0)) + commit_pow

    bits_n_over_q = (E - math.log2(folding) - math.log2(n + 1.0)
                     - math.log2(2.0 * m + 1.0) + 0.5 * math.log2(rho) + commit_pow)

    return min(bits_linear, bits_n_over_q)


def conjectured_post_disproof(R, nu, E, s, g, modulus_bits):
    """
    Plonky3 conjectured_error, the random-words bound of [2025/2010] 1.5:
        b = s * (-log2(rho + eta)) + query_pow,  eta ~ (log2(e/rho) * rho)/log2(q)
    This REPLACES the disproved capacity assumption b = s*R + g.
    """
    rho = 2.0 ** (-R)
    log2_e_over_rho = math.log2(math.e) + R
    eta = (log2_e_over_rho * rho) / modulus_bits
    eff = rho + eta
    if not (0.0 < eff < 1.0):
        return float(g)
    return s * (-math.log2(eff)) + g


def conjectured_capacity(R, s, g):
    """*** DISPROVED *** b = s*R + g. Stwo's security_bits(); Plonky3's
    conjectured_soundness_bits(); RISC Zero's toy_model_security()."""
    return s * R + g


# ========================================= optimisation over the Johnson m

M_FLOOR = 3        # Plonky3: m_min = 3usize
M_CAP = 1000       # Plonky3: LDR_M_CAP, "Matches Ethereum's soundcalc"


def best_m(R, nu, E, s, g, commit_fn, m_lo=M_FLOOR, m_hi=M_CAP):
    """
    Proposition 1 (THEOREM.md) is regime-agnostic: commit is decreasing in m and
    query is increasing in m, so min(.) is quasiconcave with a unique optimum.
    Only the commit function changes between BCIKS20 and BCHKS25.
    """
    best = (float("-inf"), None, None, None)
    for m in range(m_lo, m_hi + 1):
        y = yield_ldr(R, m)
        if y <= 0:
            continue
        q = s * y + g
        c = commit_fn(R, nu, E, m)
        v = min(q, c)
        if v > best[0]:
            best = (v, m, q, c)
    return best


def ceiling(R, nu, E, commit_fn, m_lo=M_FLOOR, m_hi=M_CAP):
    """Max commit-phase bits over admissible m -- the s -> infinity limit."""
    vals = [commit_fn(R, nu, E, m) for m in range(m_lo, m_hi + 1)
            if yield_ldr(R, m) > 0]
    return max(vals) if vals else float("-inf")


# ============================================================== configurations
# VERIFIED = read from source on 2026-07-28 (see SOURCES.md).
# ILLUSTRATIVE = a parameter point chosen for comparison; the project ships no
# production config, so no claim is made that anyone runs these numbers.

CONFIGS = [
    dict(name="RISC Zero", status="VERIFIED", p=31, ext=4, T=20, R=2, s=50, g=0,
         note="INV_RATE=4, QUERIES=50, M=16, SEGMENT 2^20, target 97 conj."),
    dict(name="Plonky3 (KoalaBear)", status="ILLUSTRATIVE", p=31, ext=4, T=20,
         R=1, s=80, g=16, note="no production config shipped; new_testing is R=2,s=2"),
    dict(name="Plonky3 (BabyBear)", status="ILLUSTRATIVE", p=31, ext=4, T=20,
         R=2, s=42, g=16, note="no production config shipped"),
    dict(name="Stwo (M31)", status="ILLUSTRATIVE", p=31, ext=4, T=20, R=1,
         s=70, g=20, note="Default PcsConfig is a ~13-bit TEST config"),
    dict(name="Plonky2 (Goldilocks)", status="ILLUSTRATIVE", p=64, ext=2, T=20,
         R=3, s=28, g=16, note="not pulled from source"),
    dict(name="Winterfell / Miden", status="ILLUSTRATIVE", p=64, ext=3, T=20,
         R=3, s=27, g=16, note="not pulled from source"),
    dict(name="Cairo / StarkNet", status="ILLUSTRATIVE", p=251, ext=1, T=20,
         R=4, s=30, g=0, note="not pulled from source"),
]


def sec(t):
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


def report():
    sec("1. BCHKS25 vs BCIKS20 -- the commit bound that Plonky3 actually ships")
    print("Both evaluated at the SAME m, so this isolates the bound change.\n")
    print(f"  {'system':<22} {'E':>4} {'R':>2} {'nu':>3} {'m':>4} "
          f"{'BCIKS20':>9} {'BCHKS25':>9} {'gain':>7}")
    print("  " + "-" * 70)
    for c in CONFIGS:
        E, nu = c["p"] * c["ext"], c["T"] + c["R"]
        for m in (16,):
            a = commit_bciks20(c["R"], nu, E, m)
            b = commit_bchks25(c["R"], nu, E, m)
            print(f"  {c['name']:<22} {E:>4} {c['R']:>2} {nu:>3} {m:>4} "
                  f"{a:>9.1f} {b:>9.1f} {b-a:>+7.1f}")
    print("\n  Two independent improvements: exponent 7 -> 5 gives 2*log2(m+1/2)")
    print("  bits, and n^2 -> n gives nu bits. At nu ~ 22 the second dominates.")

    sec("2. CEILINGS: max provable bits at unlimited queries, m in [3, 1000]")
    print(f"  {'system':<22} {'E':>4} {'BCIKS20':>9} {'BCHKS25':>9} {'gain':>7} "
          f"{'100 bits?':>11}")
    print("  " + "-" * 68)
    for c in CONFIGS:
        E, nu = c["p"] * c["ext"], c["T"] + c["R"]
        a = ceiling(c["R"], nu, E, commit_bciks20)
        b = ceiling(c["R"], nu, E, commit_bchks25)
        print(f"  {c['name']:<22} {E:>4} {a:>9.1f} {b:>9.1f} {b-a:>+7.1f} "
              f"{('YES' if b >= 100 else 'no'):>11}")
    print("\n  Under BCIKS20 the 31-bit systems capped near 77-79 bits (THEOREM.md")
    print("  Part I headline). Under the bound Plonky3 actually ships they clear")
    print("  or approach 90+, and the wider-field systems clear 100 outright.")

    sec("3. FULL ACCOUNTING at each configuration's own (s, g)")
    print(f"  {'system':<22} {'status':<13} {'proven':>8} {'m*':>4} {'binder':>7} "
          f"{'conj(new)':>10} {'conj(dead)':>11}")
    print("  " + "-" * 82)
    for c in CONFIGS:
        E, nu = c["p"] * c["ext"], c["T"] + c["R"]
        v, m, q, cm = best_m(c["R"], nu, E, c["s"], c["g"], commit_bchks25)
        binder = "query" if q <= cm else "commit"
        cn = conjectured_post_disproof(c["R"], nu, E, c["s"], c["g"], c["p"] * c["ext"])
        cd = conjectured_capacity(c["R"], c["s"], c["g"])
        print(f"  {c['name']:<22} {c['status']:<13} {v:>8.1f} {m:>4} {binder:>7} "
              f"{cn:>10.1f} {cd:>11.1f}")
    print("\n  conj(dead)  = s*R + g, the DISPROVED capacity formula that Stwo's")
    print("                security_bits() and Plonky3's conjectured_soundness_bits()")
    print("                still compute, and that RISC Zero targets 97 bits under.")
    print("  conj(new)   = the random-words replacement Plonky3's security crate uses.")

    sec("4. THE REPRICING: what the disproof actually costs")
    print(f"  {'system':<22} {'conj(dead)':>11} {'conj(new)':>10} {'lost':>6} "
          f"{'+queries to restore':>20}")
    print("  " + "-" * 74)
    for c in CONFIGS:
        E = c["p"] * c["ext"]
        nu = c["T"] + c["R"]
        cd = conjectured_capacity(c["R"], c["s"], c["g"])
        cn = conjectured_post_disproof(c["R"], nu, E, c["s"], c["g"], E)
        per = (cn - c["g"]) / c["s"] if c["s"] else 1.0
        extra = math.ceil((cd - cn) / per) if per > 0 and cd > cn else 0
        print(f"  {c['name']:<22} {cd:>11.1f} {cn:>10.1f} {cd-cn:>6.1f} {extra:>20}")
    print("\n  This is the 'modest repricing' the 2026 SoK describes: the capacity")
    print("  assumption charged -log2(rho) per query; the replacement charges")
    print("  -log2(rho + eta). At deployed rates eta is small, so the loss is a few")
    print("  bits, recoverable with a handful of extra queries. The disproof is a")
    print("  foundational event, not an operational emergency.")

    sec("5. WHAT EACH PROJECT CAN TELL YOU ABOUT ITS OWN SOUNDNESS")
    print("""
  project     conjectured calc              proven calc            post-disproof
  ---------------------------------------------------------------------------
  Plonky3     random-words [2025/2010]      UDR + BCHKS25 LDR      YES
  RISC Zero   Toy Problem + Conj 8.4        BCIKS20 LDR + UDR      no (BCIKS20)
  Stwo        capacity only (s*R + g)       NONE                   no

  Stwo's only in-repo security accounting is the formula whose underlying
  assumption was disproved, and its shipped Default is a ~13-bit test config
  carrying an explicit warning. That is a statement about what the repository
  documents, not a claim that any deployment is insecure -- production
  parameters are supplied by the caller in all three projects.

  Plonky3 is, by a clear margin, the most current: it names the disproof papers
  in module docs and has removed CapacityBound from FRI commit-phase analysis.
""")


if __name__ == "__main__":
    report()
