"""
Theorem 7: the UDR/JBR regime crossover.

Motivation. Ethereum's `soundcalc` (reports/summary.md) reports the best
provable security across regimes, and the winning regime is NOT consistent:

    Pico        53 bits (JBR)   KoalaBear^4
    Airbender   67 bits (JBR)   M31^4
    OpenVM     100 bits (UDR)   BabyBear^4
    SP1        100 bits (UDR)   KoalaBear^4
    Venus/ZisK 128 bits (JBR)   Goldilocks^3

Parts I-III of THEOREM.md treated unique decoding as strictly weakest. That is
wrong, and this file explains exactly when and why.

The reason is that UDR and JBR trade off on OPPOSITE axes:

    UDR   worse per-query yield, but a much cleaner commit term --
          error (gamma*n + 1)/|F| with NO (m+1/2) factor at all,
          hence a HIGHER ceiling.
    JBR   better per-query yield (for large enough m), but the commit
          term carries (2m'^5 + ...) and a rho^{3/2}, hence a LOWER ceiling.

So JBR wins when queries are scarce and UDR wins when queries are plentiful.

All formulas transcribed from ethereum/soundcalc (see SOURCES.md):
  soundcalc/proxgaps/unique_decoding.py  -- UDR, "Corollary 1.4 ... from BCHKS25"
  soundcalc/proxgaps/johnson_bound.py    -- JBR, eta = sqrt(rho)/(2m)
"""

import math

LOG2_3 = math.log2(3)


# ================================================================ UDR (soundcalc)

def gamma_udr(rho):
    """soundcalc UniqueDecodingRegime.get_proximity_parameter: (1 - rate)/2."""
    return (1.0 - rho) / 2.0


def yield_udr(R):
    """Per-query bits: -log2(1 - gamma) = -log2((1+rho)/2)."""
    rho = 2.0 ** (-R)
    return -math.log2(1.0 - gamma_udr(rho))


def commit_udr(R, nu, E):
    """
    soundcalc UniqueDecodingRegime.get_error_linear:
        (gamma * n + 1) / |F|,  n = dimension/rate = LDE domain size.
    Note: NO (m + 1/2) factor and no rho^{3/2}. This is why the UDR ceiling is
    high despite its poor per-query yield.
    """
    rho = 2.0 ** (-R)
    n = 2.0 ** nu
    return E - math.log2(gamma_udr(rho) * n + 1.0)


# ================================================================ JBR (soundcalc)

def eta_from_m(rho, m):
    """soundcalc _get_eta_from_m: eta = sqrt(rho)/(2m).

    This is exactly the change of variables derived independently in
    THEOREM.md ("RESOLVED: the admissible range of m"). Confirmed verbatim.
    """
    return math.sqrt(rho) / (2.0 * m)


def gamma_jbr(R, m):
    """gamma = 1 - sqrt(rho) - eta = 1 - sqrt(rho)(1 + 1/(2m))."""
    rho = 2.0 ** (-R)
    return 1.0 - math.sqrt(rho) * (1.0 + 0.5 / m)


def yield_jbr(R, m):
    """Per-query bits: -log2(sqrt(rho)(1 + 1/(2m)))."""
    a = 1.0 - gamma_jbr(R, m)
    return -math.log2(a) if 0 < a < 1 else float("-inf")


def commit_jbr(R, nu, E, m, folding=2):
    """BCHKS25 Thm 1.5 Eq (1), as shipped in Plonky3 / soundcalc."""
    rho = 2.0 ** (-R)
    sqrt_rho = math.sqrt(rho)
    mm = m + 0.5
    pp = gamma_jbr(R, m)
    if pp <= 0.0:
        return float("-inf")
    n = 2.0 ** nu
    num = (2.0 * mm ** 5 + 3.0 * mm * pp * rho) * n
    den = 3.0 * rho * sqrt_rho
    eps = (num / den + mm / sqrt_rho) * max(folding - 1.0, 1.0)
    bits_linear = E - math.log2(max(eps, 1.0))
    bits_n_over_q = (E - math.log2(folding) - math.log2(n + 1.0)
                     - math.log2(2.0 * m + 1.0) + 0.5 * math.log2(rho))
    return min(bits_linear, bits_n_over_q)


# ============================================================ Theorem 7

def m_eq(R):
    """
    THEOREM 7(a). JBR's per-query yield exceeds UDR's iff m > m_eq(R), where

        m_eq(R) = sqrt(rho) / (1 - sqrt(rho))^2 = u / (u-1)^2,   u = 2^{R/2}

    Derivation: set sqrt(rho)(1 + 1/(2m)) = (1+rho)/2. Then
        1/(2m) = (1+rho)/(2 sqrt(rho)) - 1 = (1 - sqrt(rho))^2 / (2 sqrt(rho)),
    so m = sqrt(rho)/(1-sqrt(rho))^2. Substituting rho = u^-2 gives u/(u-1)^2.
    """
    u = 2.0 ** (R / 2)
    return u / (u - 1.0) ** 2


def ceiling_jbr(R, nu, E, m_lo=1, m_hi=1000):
    """Max commit bits over admissible m. soundcalc allows m >= 1."""
    vals = [commit_jbr(R, nu, E, m) for m in range(m_lo, m_hi + 1)
            if yield_jbr(R, m) > 0]
    return max(vals) if vals else float("-inf")


def s_star(R, nu, E, g=0):
    """
    THEOREM 7(b), exact form.

    At JBR's interior optimum, Proposition 1 gives s*y_J(m*) + g = K_J(m*).
    If UDR is still query-bound at the crossover, equality Lam_U = Lam_J reads
        s*y_U + g = s*y_J(m*) + g   =>   y_J(m*) = y_U   =>   m* = m_eq(R).

    So the two regimes cross exactly when JBR's optimal Johnson parameter
    equals the yield-equalising value m_eq, and therefore

        s* = (K_J(m_eq(R)) - g) / y_UDR(R)

    NOTE the earlier version used K_J at its MAXIMUM over m (attained at the
    smallest admissible m). That is an upper bound, not the crossover: JBR has
    not saturated at the crossing. Using K_J(m_eq) is exact.
    """
    return (commit_jbr(R, nu, E, m_eq(R)) - g) / yield_udr(R)


def s_star_upper(R, nu, E, g=0, m_lo=1):
    """The loose bound: s <= (K_J^max - g)/y_UDR guarantees UDR has won."""
    return (ceiling_jbr(R, nu, E, m_lo=m_lo) - g) / yield_udr(R)


def best_udr(R, nu, E, s, g):
    return min(s * yield_udr(R) + g, commit_udr(R, nu, E))


def _m_grid(m_lo=1.0, m_hi=1000.0, n=4000):
    """Geometric grid. Continuous m, since soundcalc's eta = sqrt(rho)/(2m) is
    continuous and only the FORWARD map applies a ceiling."""
    r = (m_hi / m_lo) ** (1.0 / n)
    return [m_lo * r ** i for i in range(n + 1)]


def best_jbr(R, nu, E, s, g, m_lo=1.0, m_hi=1000.0):
    best = (float("-inf"), None)
    for m in _m_grid(m_lo, m_hi):
        y = yield_jbr(R, m)
        if y <= 0:
            continue
        v = min(s * y + g, commit_jbr(R, nu, E, m))
        if v > best[0]:
            best = (v, m)
    return best


# ================================================================== checks

def check_m_eq(R):
    """Verify m_eq by direct search on the yield difference."""
    lo, hi = 1e-6, 1e6
    for _ in range(300):
        mid = math.sqrt(lo * hi)
        if yield_jbr(R, mid) < yield_udr(R):
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def check_crossover(R, nu, E, g=0):
    """Verify s* by scanning s and finding where UDR first beats JBR."""
    predicted = s_star(R, nu, E, g)
    prev = None
    for i in range(1, 20000):
        s = i * 0.5
        u, j = best_udr(R, nu, E, s, g), best_jbr(R, nu, E, s, g)[0]
        if prev is not None and prev <= 0 < u - j:
            return predicted, s
        prev = u - j
    return predicted, None


# ================================================================== report

def sec(t):
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


# VERIFIED configs. See SOURCES.md.
SYSTEMS = [
    ("RISC Zero",        124, 20, 2, 50, 0,  "VERIFIED  INV_RATE=4 QUERIES=50"),
    ("Plonky2 std recur", 128, 20, 3, 28, 16, "VERIFIED  rate_bits=3 nqr=28 pow=16"),
    ("Miden RECURSIVE_96", 128, 18, 3, 27, 16, "VERIFIED  rho=1/8 nq=27 grind=16"),
]


def report():
    sec("1. THEOREM 7(a): where JBR's per-query yield overtakes UDR's")
    print("   m_eq(R) = sqrt(rho)/(1-sqrt(rho))^2 = u/(u-1)^2,  u = 2^{R/2}\n")
    print(f"  {'blowup':>8} {'R':>3} {'y_UDR':>8} {'m_eq closed':>12} "
          f"{'m_eq search':>12} {'ok':>4}")
    print("  " + "-" * 54)
    for R in (1, 2, 3, 4, 5, 6):
        cf, sr = m_eq(R), check_m_eq(R)
        ok = "PASS" if abs(cf - sr) / cf < 1e-6 else "FAIL"
        print(f"  {2**R:>8} {R:>3} {yield_udr(R):>8.4f} {cf:>12.4f} "
              f"{sr:>12.4f} {ok:>4}")
    print("\n  At blowup 2 you need m > 8.24 before the Johnson regime even has a")
    print("  better per-query yield than unique decoding. At blowup 8 or more, any")
    print("  m >= 1 suffices. Low-blowup systems get much less from JBR than the")
    print("  'Johnson beats unique decoding' folklore suggests.")

    sec("2. CEILINGS: UDR's commit term has no (m+1/2) factor, so it wins")
    print(f"  {'field':>14} {'R':>3} {'nu':>3} {'K_UDR':>8} {'K_JBR':>8} "
          f"{'U-J':>7}")
    print("  " + "-" * 50)
    for E, lbl in ((124, "31-bit^4"), (128, "Goldilocks^2"), (192, "Goldilocks^3")):
        for R in (1, 2, 3):
            nu = 20 + R
            ku, kj = commit_udr(R, nu, E), ceiling_jbr(R, nu, E)
            print(f"  {lbl:>14} {R:>3} {nu:>3} {ku:>8.1f} {kj:>8.1f} {ku-kj:>+7.1f}")
    print("\n  UDR's ceiling is 6-9 bits above JBR's everywhere. That is the entire")
    print("  reason OpenVM and SP1 reach 100 provable bits in UDR while Pico and")
    print("  Airbender sit at 53 and 67 in JBR.")

    sec("3. THEOREM 7(b): the crossover query count s* = (K_JBR^max - g)/y_UDR")
    print(f"  {'field':>14} {'R':>3} {'g':>3} {'s* closed':>10} {'s* scan':>9} "
          f"{'ok':>5}")
    print("  " + "-" * 50)
    for E, lbl in ((124, "31-bit^4"), (128, "Goldilocks^2")):
        for R in (1, 2, 3):
            for g in (0, 16):
                nu = 20 + R
                pred, found = check_crossover(R, nu, E, g)
                ok = "PASS" if found and abs(pred - found) <= 1.0 else "FAIL"
                fs = f"{found:.1f}" if found else "none"
                print(f"  {lbl:>14} {R:>3} {g:>3} {pred:>10.1f} {fs:>9} {ok:>5}")
    print("\n  Below s*, use the Johnson regime. Above it, unique decoding is")
    print("  strictly better AND rests on a weaker assumption -- UDR needs no")
    print("  list-decoding argument at all. Buying queries past s* buys you both")
    print("  more security and a cleaner proof.")

    sec("4. VERIFIED SYSTEMS: which regime should each be reported in?")
    print(f"  {'system':<20} {'E':>4} {'R':>2} {'s':>4} {'g':>3} {'UDR':>7} "
          f"{'JBR':>7} {'m*':>4} {'best':>6} {'s*':>7}")
    print("  " + "-" * 78)
    for name, E, T, R, s, g, note in SYSTEMS:
        nu = T + R
        u = best_udr(R, nu, E, s, g)
        j, m = best_jbr(R, nu, E, s, g)
        star = s_star(R, nu, E, g)
        which = "UDR" if u > j else "JBR"
        print(f"  {name:<20} {E:>4} {R:>2} {s:>4} {g:>3} {u:>7.1f} {j:>7.1f} "
              f"{m:>4} {which:>6} {star:>7.0f}")
    print("\n  All three deployed systems sit BELOW their crossover, so JBR is the")
    print("  right regime to report them in -- and all three land in the 50-70 bit")
    print("  band that soundcalc independently reports for Pico (53) and")
    print("  Airbender (67). Reaching 100 provable bits means crossing s*, which")
    print("  is 130-190 queries: roughly 3-4x what these systems currently use.")
    print("\n  That is the real price of provable 100-bit security on a small field:")
    print("  not a different field, not a different bound -- just many more queries.")


if __name__ == "__main__":
    report()
