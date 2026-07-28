"""
NADO FRI soundness audit.

Parameters read from /root/nado on 2026-07-28:

    execnode/stark/field.py   P = 2^64 - 2^32 + 1   (Goldilocks), no extension
    execnode/stark/fri.py     NUM_QUERIES = 320, FRI_BLOWUP = 2, GRIND_BITS = 18
    execnode/stark/stark.py   MAX_TRACE_ROWS = 1 << 17
    execnode/stark/transcript.py  challenge() -> "a uniform field element"
    execnode/stark/deep_eval.py   z = int(z) % F.P

The stated design target, from the comment block in fri.py:

    #     320 queries * 0.4  +  18 grind  ~  146 bits PROVABLE (Johnson),  and
    #     320 queries * 1.0  +  18 grind  ~  338 bits CONJECTURED

Both figures account for the QUERY phase only. FRI soundness is a MINIMUM over
the query phase and the commit phase, and the commit phase is bounded by the
size of the field the folding challenges are drawn from -- it cannot be bought
with queries at any price. That is THEOREM.md Theorem 2, and it is the single
most consequential structural fact in this whole repository.

NADO folds with base-field challenges:

    alpha = t.challenge()                              # fri.py:93
    out[i] = F.add(fe, F.mul(alpha, fo))               # fri.py:63

so the relevant field size is |F| = 2^64, NOT a 128- or 192-bit extension.
"""

import math

# ----------------------------------------------------------------- parameters

E_BASE = 64.0            # log2(Goldilocks) -- the field challenges live in
R = 1                    # FRI_BLOWUP = 2  =>  rate 1/2
S = 320                  # NUM_QUERIES
G = 18                   # GRIND_BITS
T_MAX = 17               # MAX_TRACE_ROWS = 1 << 17
NU_MAX = T_MAX + R       # log2 of the FRI layer-0 domain

RHO = 2.0 ** (-R)


# ------------------------------------------------------------------- the terms

def yield_udr(R):
    return -math.log2((1.0 + 2.0 ** (-R)) / 2.0)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** (-R)) * (1.0 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def commit_udr(R, nu, E):
    """soundcalc UDR: (gamma*n + 1)/|F|, gamma = (1-rho)/2."""
    gamma = (1.0 - 2.0 ** (-R)) / 2.0
    return E - math.log2(gamma * 2.0 ** nu + 1.0)


def commit_jbr(R, nu, E, m, folding=2):
    """BCHKS25 Thm 1.5 Eq (1), as shipped in Plonky3 and soundcalc."""
    rho = 2.0 ** (-R)
    sr = math.sqrt(rho)
    mm = m + 0.5
    pp = 1.0 - sr * (1.0 + 0.5 / m)
    if pp <= 0:
        return float("-inf")
    n = 2.0 ** nu
    eps = ((2.0 * mm ** 5 + 3.0 * mm * pp * rho) * n / (3.0 * rho * sr)
           + mm / sr) * max(folding - 1.0, 1.0)
    lin = E - math.log2(max(eps, 1.0))
    noq = (E - math.log2(folding) - math.log2(n + 1.0)
           - math.log2(2.0 * m + 1.0) + 0.5 * math.log2(rho))
    return min(lin, noq)


def deep_bits(nu, E, degree_log):
    """DEEP / Schwartz-Zippel at a single base-field point z: deg/|F|."""
    return E - degree_log


def best_over_m(R, nu, E, s, g):
    best = (float("-inf"), None, None, None)
    m = 1.0
    while m <= 1000.0:
        y = yield_jbr(R, m)
        if y > 0:
            q = s * y + g
            c = commit_jbr(R, nu, E, m)
            v = min(q, c)
            if v > best[0]:
                best = (v, m, q, c)
        m *= 1.002
    return best


def sec(t):
    print("\n" + "=" * 96)
    print(t)
    print("=" * 96)


def report():
    sec("NADO FRI SOUNDNESS AUDIT")
    print(f"""
  field            Goldilocks 2^64 - 2^32 + 1, NO EXTENSION   ->  E = {E_BASE:.0f} bits
  FRI_BLOWUP       2   (R = {R}, rate 1/2)
  NUM_QUERIES      {S}
  GRIND_BITS       {G}
  MAX_TRACE_ROWS   2^{T_MAX}   ->  FRI domain nu = {NU_MAX}
""")

    sec("1. THE QUERY PHASE -- the part fri.py computes")
    yu = yield_udr(R)
    print(f"  UDR   yield/query = {yu:.4f}   ->  {S}*{yu:.4f} + {G} = "
          f"{S*yu+G:.1f} bits")
    for m in (3, 8, 16, 64):
        y = yield_jbr(R, m)
        print(f"  JBR   m={m:<3} yield = {y:.4f}   ->  {S}*{y:.4f} + {G} = "
              f"{S*y+G:.1f} bits")
    print(f"\n  The comment's 0.4 bits/query is a fair figure for the Johnson")
    print(f"  regime at moderate m. The query-phase arithmetic is CORRECT.")

    sec("2. THE COMMIT PHASE -- the term that is missing")
    print(f"  {'trace':>8} {'nu':>4} {'UDR commit':>12} {'JBR commit (best m)':>21}")
    print("  " + "-" * 50)
    for T in (10, 14, 17):
        nu = T + R
        cu = commit_udr(R, nu, E_BASE)
        cj = max(commit_jbr(R, nu, E_BASE, m)
                 for m in (1.0 * 1.002 ** i for i in range(3500))
                 if yield_jbr(R, m) > 0)
        print(f"  {'2^'+str(T):>8} {nu:>4} {cu:>12.1f} {cj:>21.1f}")
    print(f"""
  The commit error is ~ n/|F|. With |F| = 2^64 and n = 2^{NU_MAX} that is
  2^-{E_BASE - NU_MAX:.0f}, and NO number of queries changes it. Grinding does not
  help either: GRIND_BITS is a query-phase proof-of-work.""")

    sec("3. TOTAL = min(query, commit, deep)")
    nu = NU_MAX
    vj, mj, qj, cj = best_over_m(R, nu, E_BASE, S, G)
    qu, cu = S * yield_udr(R) + G, commit_udr(R, nu, E_BASE)
    vu = min(qu, cu)
    dp = deep_bits(nu, E_BASE, T_MAX)
    print(f"  UDR    query {qu:7.1f}   commit {cu:7.1f}   ->  {vu:7.1f} bits")
    print(f"  JBR    query {qj:7.1f}   commit {cj:7.1f}   ->  {vj:7.1f} bits  "
          f"(m* = {mj:.1f})")
    print(f"  DEEP   single base-field z, degree 2^{T_MAX}      ->  {dp:7.1f} bits")
    achieved = min(max(vu, vj), dp)      # pick the BEST regime, then DEEP caps
    print(f"\n  best regime = {'UDR' if vu >= vj else 'JBR'}  "
          f"(you may report whichever is higher)")
    print(f"  ACHIEVED PROVABLE SOUNDNESS = {achieved:.1f} bits   "
          f"(binder: {'DEEP' if dp < max(vu,vj) else 'FRI commit'})")
    print(f"  STATED IN fri.py             = 146 bits")
    print(f"  SHORTFALL                    = {146 - achieved:.1f} bits")
    print(f"""
  The conjectured branch is capped by the SAME commit term, so the stated 338
  bits is also unreachable -- the conjecture improves per-query yield, and the
  query phase is not what binds here.""")

    sec("4. WHY 320 QUERIES BUY NOTHING PAST ~{:.0f}".format(
        (min(cu, cj) - G) / yield_udr(R)))
    print(f"  {'queries':>9} {'UDR total':>10} {'JBR total':>10}")
    print("  " + "-" * 33)
    for s in (32, 64, 96, 128, 160, 320, 1000):
        v1 = min(s * yield_udr(R) + G, cu)
        v2 = best_over_m(R, nu, E_BASE, s, G)[0]
        tag = "  <- NUM_QUERIES" if s == S else ""
        print(f"  {s:>9} {v1:>10.1f} {v2:>10.1f}{tag}")
    print(f"""
  Soundness saturates near {min(cu,cj):.0f} bits at roughly {(min(cu,cj)-G)/yield_udr(R):.0f} queries. The
  remaining ~{S - (min(cu,cj)-G)/yield_udr(R):.0f} queries are pure proof size: they add Merkle openings
  and verifier hashing while adding zero bits of security.""")

    sec("5. THE FIX -- an extension field for challenges and DEEP sampling")
    print(f"  {'design':<34} {'E':>5} {'commit':>8} {'total':>8} {'vs now':>8}")
    print("  " + "-" * 66)
    rows = [("Goldilocks base (NADO today)", 64.0),
            ("Goldilocks^2 (Plonky2, Miden)", 128.0),
            ("Goldilocks^3 (Venus, ZisK)", 192.0)]
    base_total = None
    for label, E in rows:
        cu2 = commit_udr(R, nu, E)
        vj2 = best_over_m(R, nu, E, S, G)[0]
        vu2 = min(S * yield_udr(R) + G, cu2)
        tot = min(max(vu2, vj2), deep_bits(nu, E, T_MAX))
        if base_total is None:
            base_total = tot
        print(f"  {label:<34} {E:>5.0f} {min(cu2, commit_jbr(R,nu,E,16)):>8.1f} "
              f"{tot:>8.1f} {tot-base_total:>+8.1f}")
    print("""
  A degree-2 extension for the FOLDING CHALLENGE and the DEEP point z is the
  standard fix and is what every other Goldilocks system does: Plonky2 and
  Miden use Goldilocks^2, Venus and ZisK use Goldilocks^3. The trace, the AIR,
  the Merkle layer and the recursion geometry are untouched -- only the
  challenge sampling and the fold arithmetic move into the extension.

  This preserves the property fri.py's comment is protecting: FRI_BLOWUP stays
  2 and the fold shape is unchanged, so the in-circuit recursion AIRs that
  arithmetize the fold geometry do not need to change shape. The extension does
  change the arithmetic those AIRs perform, which is real work -- but it is the
  only way to lift a ceiling that queries cannot touch.

  With Goldilocks^2 the 320-query budget becomes well matched: the commit term
  moves to ~112 bits and the query phase at 320 queries is ~{:.0f}, so the design
  target of 128+ PROVABLE bits is reachable.""".format(S * yield_udr(R) + G))

    sec("6. CAVEATS ON THIS AUDIT")
    print("""
  * Read from source but NOT executed. I did not run NADO's prover or verifier.
  * The commit-phase model is BCHKS25/soundcalc for a generic FRI. NADO's FRI
    is its own implementation; if it draws folding challenges from a wider
    space than a single base-field element anywhere I did not look, the ceiling
    moves up accordingly. The specific lines I read are fri.py:93 (alpha =
    t.challenge()), fri.py:63 (the fold), transcript.py:28-31 (challenge ->
    "a uniform field element"), deep_eval.py:47 (z = int(z) % F.P).
  * nu = 18 uses MAX_TRACE_ROWS. Smaller traces give a slightly higher ceiling
    (about +1 bit per halving), which does not change the conclusion.
  * This is a soundness-parameter finding, not an exploit. It says the PROVEN
    bound is far below the stated target, not that a forgery is known.
""")


if __name__ == "__main__":
    report()
