"""
Numerical verification of Proposition 1 and Theorem 2 (see THEOREM.md).

Everything here is a check, not a derivation: brute-force the quantity over a
fine grid and compare against the claimed closed form. If the closed form is
wrong, this prints the discrepancy.
"""

import math

LOG2_3 = math.log2(3)


# ------------------------------------------------------------ the two terms

def alpha(R, m):
    """Per-query soundness error under the Johnson bound: sqrt(rho)(1+1/2m)."""
    return math.sqrt(2.0 ** (-R)) * (1 + 1 / (2 * m))


def Q(R, s, g, m):
    """Query-phase bits. Strictly increasing in m; sup = s*R/2 + g."""
    a = alpha(R, m)
    if a >= 1:
        return -math.inf          # inadmissible: queries buy nothing
    return -s * math.log2(a) + g


def K(R, nu, E, m):
    """Commit-phase bits. Strictly decreasing in m."""
    return E + LOG2_3 - 7 * math.log2(m + 0.5) - 1.5 * R - 2 * nu


def Lam(R, nu, E, s, g, m):
    return min(Q(R, s, g, m), K(R, nu, E, m))


# ------------------------------------------------------- the claimed results

def m_min(R):
    """Admissibility threshold: alpha(R,m) < 1  <=>  m > 1/(2(2^{R/2}-1))."""
    return 1.0 / (2 * (2 ** (R / 2) - 1))


def ceiling_closed_form(R, nu, E, m_floor=0.0):
    """
    Theorem 2.  sup over s and admissible m of Lam  =  K(m_eff), where
    m_eff = max(m_min(R), m_floor).

    With m_floor = 0 this simplifies to
        E - 2nu - 5R + 7*log2(2^{R/2} - 1) + log2(3) + 7
    """
    m_eff = max(m_min(R), m_floor)
    return K(R, nu, E, m_eff)


def ceiling_simplified(R, nu, E):
    """The simplified algebraic form, valid only when m_floor <= m_min(R)."""
    return (E - 2 * nu - 5 * R + 7 * math.log2(2 ** (R / 2) - 1) + LOG2_3 + 7)


def optimal_m(R, nu, E, s, g, lo=None, hi=1e6, iters=200):
    """Proposition 1: bisect on Q - K, which is strictly increasing."""
    lo = (lo if lo is not None else m_min(R)) * (1 + 1e-12)
    if Q(R, s, g, lo) >= K(R, nu, E, lo):
        return lo                                   # boundary case
    for _ in range(iters):
        mid = math.sqrt(lo * hi)                    # geometric bisection
        if Q(R, s, g, mid) - K(R, nu, E, mid) < 0:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


# ------------------------------------------------------------------- checks

def check_monotonicity(trials=2000):
    """Proposition 1(a),(b): Q strictly increasing, K strictly decreasing."""
    bad = 0
    for R in (1, 2, 3, 4, 5):
        ms = [m_min(R) * (1 + 1e-9) * (1.01 ** i) for i in range(trials)]
        qs = [Q(R, 50, 16, m) for m in ms]
        ks = [K(R, 21, 124, m) for m in ms]
        if any(b <= a for a, b in zip(qs, qs[1:])):
            bad += 1
        if any(b >= a for a, b in zip(ks, ks[1:])):
            bad += 1
    return bad


def check_unimodality():
    """Proposition 1(c): the grid argmax matches the bisection root."""
    worst = 0.0
    for R in (1, 2, 3, 4):
        for s in (20, 50, 100, 400):
            for g in (0, 16, 24):
                for E, nu in ((124, 21), (128, 23), (192, 23), (251, 24)):
                    grid = [m_min(R) * (1 + 1e-9) * (1.002 ** i)
                            for i in range(6000)]
                    vals = [Lam(R, nu, E, s, g, m) for m in grid]
                    best_grid = max(vals)
                    m_star = optimal_m(R, nu, E, s, g)
                    best_cf = Lam(R, nu, E, s, g, m_star)
                    worst = max(worst, best_grid - best_cf)
    return worst


def check_ceiling():
    """Theorem 2: sup over s and m equals the closed form."""
    rows = []
    for R in (1, 2, 3, 4):
        for E, nu in ((124, 21), (128, 23), (192, 23), (251, 24)):
            brute = -math.inf
            for s_exp in range(4, 22):                 # s up to ~2M queries
                s = 2 ** s_exp
                grid = [m_min(R) * (1 + 1e-9) * (1.002 ** i)
                        for i in range(6000)]
                brute = max(brute, max(Lam(R, nu, E, s, 0, m) for m in grid))
            cf = ceiling_closed_form(R, nu, E)
            simp = ceiling_simplified(R, nu, E)
            rows.append((R, E, nu, brute, cf, simp, cf - brute, abs(cf - simp)))
    return rows


def check_algebraic_identity():
    """m_min(R) + 1/2 == 2^{R/2} / (2(2^{R/2}-1)), the key simplification."""
    worst = 0.0
    for R in [x / 4 for x in range(1, 41)]:
        lhs = m_min(R) + 0.5
        rhs = 2 ** (R / 2) / (2 * (2 ** (R / 2) - 1))
        worst = max(worst, abs(lhs - rhs))
    return worst


def f_of_R(R):
    """The R-dependent part of the ceiling: Lam_max = (E - 2nu) + f(R)."""
    return -5 * R + 7 * math.log2(2 ** (R / 2) - 1) + LOG2_3 + 7


R_STAR = 2 * math.log2(10 / 3)


def f_at_optimum():
    """Theorem 3 closed form: f(R*) = 7log2(7/3) - 10log2(10/3) + log2(3) + 7."""
    return 7 * math.log2(7 / 3) - 10 * math.log2(10 / 3) + LOG2_3 + 7


def check_optimal_blowup():
    """Theorem 3: f is maximised at R* = 2*log2(10/3), blowup 2^R* ~ 11.1."""
    grid = [0.05 * i for i in range(1, 400)]
    best_R = max(grid, key=f_of_R)
    return best_R, f_of_R(best_R), R_STAR, f_of_R(R_STAR), f_at_optimum()


if __name__ == "__main__":
    print("=" * 96)
    print("VERIFICATION OF PROPOSITION 1 AND THEOREM 2")
    print("=" * 96)

    print(f"\n[1] Algebraic identity  m_min+1/2 = 2^(R/2)/(2(2^(R/2)-1))")
    err = check_algebraic_identity()
    print(f"    max abs error over R in [0.25, 10]: {err:.3e}   "
          f"{'PASS' if err < 1e-12 else 'FAIL'}")

    print(f"\n[2] Proposition 1(a,b): monotonicity of Q (up) and K (down)")
    bad = check_monotonicity()
    print(f"    violations: {bad}   {'PASS' if bad == 0 else 'FAIL'}")

    print(f"\n[3] Proposition 1(c): grid argmax vs bisection root")
    gap = check_unimodality()
    print(f"    worst (grid_best - closed_form_best): {gap:+.6f} bits   "
          f"{'PASS' if gap < 1e-3 else 'FAIL'}")

    print(f"\n[4] Theorem 2: ceiling closed form vs brute force over (s, m)")
    print(f"\n    {'R':>2} {'E':>5} {'nu':>4} {'brute sup':>11} {'closed form':>12} "
          f"{'simplified':>11} {'gap':>9}")
    print("    " + "-" * 62)
    ok = True
    for R, E, nu, brute, cf, simp, gap, ident in check_ceiling():
        flag = "" if (gap >= -1e-6 and gap < 0.05 and ident < 1e-9) else "  <-- FAIL"
        if flag:
            ok = False
        print(f"    {R:>2} {E:>5} {nu:>4} {brute:>11.4f} {cf:>12.4f} "
              f"{simp:>11.4f} {gap:>+9.5f}{flag}")
    print(f"\n    {'PASS' if ok else 'FAIL'}  (gap >= 0 means the closed form is a "
          f"true upper bound; gap ~ 0 means it is tight)")

    print("\n" + "=" * 96)
    print("CONSEQUENCE: corrected provable ceilings")
    print("=" * 96)
    print("The earlier ceiling computation maximised K over integer m >= 1 without")
    print("checking admissibility, so at blowup 2 it used m = 1, where the per-query")
    print("yield is NEGATIVE (alpha > 1) and unlimited queries buy nothing.\n")
    print(f"    {'system':<24} {'R':>2} {'E':>5} {'nu':>4} {'old (m=1)':>10} "
          f"{'corrected':>10} {'delta':>7}")
    print("    " + "-" * 68)
    SYS = [("Stwo (M31)", 1, 124, 21), ("Plonky3 (KoalaBear)", 1, 124, 21),
           ("Plonky3 (BabyBear)", 2, 124, 22), ("RISC Zero", 2, 124, 22),
           ("Plonky2", 3, 128, 23), ("Winterfell / Miden", 3, 192, 23),
           ("Boojum (zkSync)", 3, 128, 23), ("Cairo / StarkNet", 4, 251, 24)]
    for name, R, E, nu in SYS:
        old = K(R, nu, E, 1.0)
        new = ceiling_closed_form(R, nu, E)
        print(f"    {name:<24} {R:>2} {E:>5} {nu:>4} {old:>10.1f} {new:>10.1f} "
              f"{new-old:>+7.1f}")
    print("\n    At R=1 the old figure was not merely loose, it was INVALID:")
    print(f"    alpha(R=1, m=1) = {alpha(1,1):.4f} > 1.")
    print(f"    Admissibility requires m > {m_min(1):.4f} at blowup 2.")

    print("\n" + "=" * 96)
    print("THEOREM 3: the ceiling is NON-MONOTONIC in blowup, with an interior optimum")
    print("=" * 96)
    gR, gV, sR, sV, cf = check_optimal_blowup()
    print(f"\n    grid argmax        R = {gR:.4f}   f = {gV:.6f}")
    print(f"    claimed optimum    R* = 2*log2(10/3) = {sR:.6f}   f = {sV:.6f}")
    print(f"    closed form f(R*)                       = {cf:.6f}")
    print(f"    |grid - claimed| = {abs(gR-sR):.4f} (grid step 0.05)   "
          f"{'PASS' if abs(gR-sR) < 0.05 else 'FAIL'}")
    print(f"    |f(R*) - closed form| = {abs(sV-cf):.2e}   "
          f"{'PASS' if abs(sV-cf) < 1e-12 else 'FAIL'}")
    print(f"\n    Optimal blowup factor = 2^R* = {2**sR:.3f}")
    print(f"    Ceiling there         = (E - 2nu) {cf:+.4f} bits\n")
    print(f"    {'blowup':>8} {'R':>7} {'f(R)':>10} {'loss vs optimum':>17}")
    print("    " + "-" * 46)
    for R in (1, 2, 3, R_STAR, 4, 5, 6, 8):
        tag = "  <-- optimum" if abs(R - R_STAR) < 1e-9 else ""
        print(f"    {2**R:>8.2f} {R:>7.3f} {f_of_R(R):>10.3f} "
              f"{f_of_R(R)-cf:>17.3f}{tag}")
    print("\n    Deployed systems at blowup 2 (Stwo, Plonky3/KoalaBear) sit ~5.1 bits")
    print("    below the achievable provable ceiling. Blowup 16 sits ~0.6 below.")
    print("    NOTE: this optimises the CEILING (commit term) only. Query cost falls")
    print("    with larger blowup and prover cost rises, so the joint optimum differs;")
    print("    this says where the provable ceiling itself peaks.")
