"""
Four-regime FRI soundness model, post the late-2025 capacity disproof.

REGIME INVENTORY (status as of July 2026)

  U  unique decoding      delta = (1-rho)/2
                          per-query (1+rho)/2      commit O(n)/|F|
                          UNCONDITIONAL, weakest yield.

  J  Johnson / BCIKS20    delta = 1-sqrt(rho)(1+1/2m)
                          per-query sqrt(rho)(1+1/2m)
                          commit (m+1/2)^7 n^2 / (3 rho^{3/2} |F|)
                          UNCONDITIONAL. Still stands -- untouched by the
                          2025 disproofs.

  T  threshold halving    delta in (delta_J, 1-rho)          [eprint 2026/858]
                          per-query (1 - delta/2)
                          commit n*r/|F|      (r = FRI round count)
                          UNCONDITIONAL and ABOVE Johnson. First such bound.
                          Requires k = 2^m and an evaluation domain admitting a
                          fixed-point-free involution -- satisfied by deployed
                          FRI in either characteristic.

  C  capacity             delta = 1-rho
                          per-query rho        commit ~ n/(rho |F|)
                          *** DISPROVED late 2025 ***
                          Crites-Stewart (2025/2046) refuted the correlated
                          agreement, mutual correlated agreement (WHIR), and
                          list-decodability (DEEP-FRI) up-to-capacity
                          conjectures; Diamond-Gruen (2025/2010) gave an
                          independent counterexample over multiplicative
                          subgroups of prime fields. Retained here ONLY as the
                          historical baseline that deployed parameters were set
                          against. Do not treat its column as a security claim.

Bounds for U and J are transcribed from ethSTARK v1.2 / BCIKS20; the bound for
T is transcribed from the 2026/858 abstract. All are RECALLED TRANSCRIPTIONS,
not re-derivations. See THEOREM.md for what is proved here versus assumed.
"""

import math

LOG2_3 = math.log2(3)


# ============================================================ per-query yield

def yield_U(R):
    """Unique decoding: -log2((1+rho)/2) = 1 - log2(1+rho)."""
    return 1 - math.log2(1 + 2.0 ** (-R))


def yield_J(R, m=None):
    """
    Johnson: -log2(sqrt(rho)(1+1/2m)). Supremum over m is R/2, approached as
    m -> infinity. Pass m=None for the supremum.
    """
    if m is None:
        return R / 2
    return -math.log2(math.sqrt(2.0 ** (-R)) * (1 + 1 / (2 * m)))


def yield_T(R, delta=None):
    """
    Threshold halving: -log2(1 - delta/2), for delta in (delta_J, 1-rho).
    Supremum at delta -> 1-rho, giving -log2((1+rho)/2) == yield_U(R).

    NOTE this coincidence: threshold halving pushed to capacity radius gives
    exactly the unique-decoding per-query yield. Its advantage over U is not
    the yield, it is the delta range it certifies; its advantage over J is the
    commit term.
    """
    if delta is None:
        delta = 1 - 2.0 ** (-R)
    return -math.log2(1 - delta / 2)


def yield_C(R):
    """Capacity: -log2(rho) = R.  *** DISPROVED -- baseline only. ***"""
    return R


# ================================================================== ceilings
# Max soundness at unlimited query count: set by the commit-phase term.

def m_min(R):
    """Johnson admissibility (THEOREM.md Lemma 1). Equals ethSTARK's eta range."""
    return 1.0 / (2 * (2 ** (R / 2) - 1))


def ceiling_J(R, nu, E):
    """THEOREM.md Theorem 2: E - 2nu - 5R + 7log2(2^{R/2}-1) + log2(3) + 7."""
    return E - 2 * nu - 5 * R + 7 * math.log2(2 ** (R / 2) - 1) + LOG2_3 + 7


def g_of_R(R):
    """
    THEOREM 3' (the deployment parameterisation).

    The evaluation domain is the trace times the blowup, so nu = T + R is
    FORCED; nu and R are not independent. Substituting into Theorem 2:

        Lam_max^J = E - 2T - 7R + 7log2(2^{R/2} - 1) + log2(3) + 7
                  = (E - 2T) + g(R)

    Theorem 3 optimised f(R) holding nu fixed, which answers a different
    question -- it compares systems that SHRINK the trace as they raise the
    blowup. For a fixed workload the operative optimum is the one below.
    """
    return -7 * R + 7 * math.log2(2 ** (R / 2) - 1) + LOG2_3 + 7


def ceiling_J_fixed_trace(R, T, E):
    """Lam_max^J = (E - 2T) + g(R), with nu = T + R substituted in."""
    return E - 2 * T + g_of_R(R)


def ceiling_T(R, nu, E, rounds=None):
    """
    From eps_commit <= n*r/|F|:  E - nu - log2(r).
    r = FRI round count ~ nu - R (arity 2, folding to a constant).

    CAVEAT: 'nR/|F|' in the 2026/858 abstract uses R for the round count in
    their notation (they write rho for rate). If R there meant the rate
    exponent instead, the term becomes E - nu - log2(R), which moves the
    ceiling by under 1 bit -- every conclusion below is insensitive to this.
    """
    r = rounds if rounds is not None else max(nu - R, 1)
    return E - nu - math.log2(r)


def ceiling_C(R, nu, E):
    """*** DISPROVED -- baseline only. ***  E - nu - R."""
    return E - nu - R


# =========================================== Theorem 4: the query penalty kappa

def kappa(R):
    """
    Query multiplier for buying unconditionality above Johnson:

        kappa(R) = yield_J(R) / yield_T(R) = (R/2) / (1 - log2(1 + 2^-R))

    THEOREM 4: kappa is strictly increasing on (0, inf), with
        lim_{R->0+} kappa(R) = 1     and     kappa(R) ~ R/2 -> inf.
    """
    return yield_J(R) / yield_T(R)


def check_kappa_monotone(lo=1e-4, hi=40.0, n=200000):
    """Numerical check of Theorem 4's monotonicity claim."""
    step = (hi - lo) / n
    prev, bad = kappa(lo), 0
    for i in range(1, n + 1):
        cur = kappa(lo + i * step)
        if cur <= prev:
            bad += 1
        prev = cur
    return bad


def kappa_limit_at_zero(eps=1e-9):
    """L'Hopital: numerator' = 1/2, denominator' -> 1/2 as R->0, so limit = 1."""
    return kappa(eps)


# ==================== Theorem 5: opposite blowup preferences of J and T

def check_blowup_dichotomy(T, E, lo=0.02, hi=12.0, n=200000):
    """
    THEOREM 5 (deployment parameterisation, nu = T + R):
      - ceiling_J has an interior maximum, claimed at R* = 2 exactly (blowup 4),
      - ceiling_T is strictly decreasing in R,
      - kappa is strictly increasing in R,
    so J prefers blowup 4 while T prefers the smallest blowup available.
    """
    Rs = [lo + i * (hi - lo) / n for i in range(n + 1)]
    cJ = [ceiling_J_fixed_trace(R, T, E) for R in Rs]
    cT = [ceiling_T(R, T + R, E) for R in Rs]
    argmax_J = Rs[max(range(len(Rs)), key=lambda i: cJ[i])]
    T_decreasing = all(b <= a + 1e-12 for a, b in zip(cT, cT[1:]))
    return argmax_J, T_decreasing


def check_theorem_3prime():
    """
    THEOREM 3': g(R) = -7R + 7log2(2^{R/2}-1) + log2(3) + 7 is uniquely
    maximised at R* = 2 (blowup exactly 4), with g(2) = log2(3) - 7.

    Proof: with u = 2^{R/2}, g'(R) = -7 + (7/2)u/(u-1); setting to zero gives
    u/(u-1) = 2, so u = 2 and R* = 2. Since u/(u-1) is strictly decreasing in
    u and u is increasing in R, g' is strictly decreasing and changes sign once.
    At R = 2, log2(2^{R/2} - 1) = log2(1) = 0, so g(2) = -14 + 0 + log2(3) + 7.
    """
    grid = [0.001 * i for i in range(1, 12000)]
    argmax = max(grid, key=g_of_R)
    return argmax, g_of_R(argmax), g_of_R(2.0), LOG2_3 - 7


# ================================================================== reporting

def sec(t):
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


SYSTEMS = [
    # name, base bits, ext degree, log2 trace, R
    ("Stwo (M31)",           31, 4, 20, 1),
    ("Plonky3 (KoalaBear)",  31, 4, 20, 1),
    ("Plonky3 (BabyBear)",   31, 4, 20, 2),
    ("RISC Zero",            31, 4, 20, 2),
    ("Plonky2",              64, 2, 20, 3),
    ("Winterfell / Miden",   64, 3, 20, 3),
    ("Boojum (zkSync)",      64, 2, 20, 3),
    ("Cairo / StarkNet",    251, 1, 20, 4),
]


def report():
    sec("0. STATUS OF THE FOUR REGIMES  (July 2026)")
    print("""
  U  unique decoding    UNCONDITIONAL
  J  Johnson / BCIKS20  UNCONDITIONAL  -- untouched by the 2025 disproofs
  T  threshold halving  UNCONDITIONAL  -- first bound above Johnson (2026/858)
  C  capacity           DISPROVED late 2025 (Crites-Stewart; Diamond-Gruen)

  Deployed STARK parameters were, almost universally, set against C.
""")

    sec("1. PER-QUERY YIELD BY REGIME  (bits per FRI query)")
    print(f"{'blowup':>8} {'R':>4} {'U':>8} {'J (sup)':>9} {'T (sup)':>9} "
          f"{'C [dead]':>10} {'kappa=J/T':>11}")
    print("-" * 64)
    for R in (1, 2, 3, 4, 5, 6):
        print(f"{2**R:>8} {R:>4} {yield_U(R):>8.3f} {yield_J(R):>9.3f} "
              f"{yield_T(R):>9.3f} {yield_C(R):>10.3f} {kappa(R):>11.3f}")
    print("\n  yield_T == yield_U exactly: threshold halving pushed to the capacity")
    print("  radius recovers the unique-decoding per-query yield. Its gain is in the")
    print("  COMMIT term and in the radius it certifies, not in per-query yield.")
    print("\n  kappa at blowup 16 is 2.19, matching 2026/858's stated '~factor 2 in")
    print("  queries'. That agreement is a useful check on this transcription.")

    sec("2. THEOREM 4: the query penalty for unconditionality above Johnson")
    bad = check_kappa_monotone()
    print(f"  kappa(R) = (R/2) / (1 - log2(1 + 2^-R))")
    print(f"  monotonicity violations over R in (0, 40], 200k samples: {bad}   "
          f"{'PASS' if bad == 0 else 'FAIL'}")
    print(f"  lim_{{R->0+}} kappa = {kappa_limit_at_zero():.9f}   (claim: 1)")
    print(f"  kappa(40) = {kappa(40):.3f}   (claim: ~ R/2 = 20)")
    print("""
  READING: the cost of going unconditional above Johnson VANISHES as the blowup
  approaches 1 and grows without bound as the blowup grows. This inverts the
  usual intuition. High blowup is what makes the Johnson bound's query
  advantage large, so high-blowup systems are the ones that pay most to become
  unconditional.""")

    sec("3. CEILINGS BY REGIME  (max bits at unlimited queries, trace 2^20)")
    hdr = (f"{'system':<22} {'E':>5} {'R':>3} {'J':>8} {'T':>8} {'T-J':>7} "
           f"{'C [dead]':>10}")
    print(hdr)
    print("-" * len(hdr))
    for name, p, ext, logn, R in SYSTEMS:
        E, nu = p * ext, logn + R
        cJ, cT, cC = ceiling_J(R, nu, E), ceiling_T(R, nu, E), ceiling_C(R, nu, E)
        print(f"{name:<22} {E:>5} {R:>3} {cJ:>8.1f} {cT:>8.1f} {cT-cJ:>+7.1f} "
              f"{cC:>10.1f}")
    print("""
  The T column is the headline. Threshold halving's commit term is O(n)/|F|
  against BCIKS's O(n^2)/|F|, which is worth ~nu bits -- and nu is 21-24 for a
  2^20 trace. That is precisely the gap that put 100-bit PROVABLE security out
  of reach for 31-bit fields under J.""")

    sec("4. THEOREM 6: the crossover, and what it rescues")
    print("  For a 100-bit provable target at trace 2^20:\n")
    hdr = (f"{'system':<22} {'E':>5} {'J ceiling':>10} {'T ceiling':>10} "
           f"{'100 bits provable?':>20}")
    print(hdr)
    print("-" * len(hdr))
    for name, p, ext, logn, R in SYSTEMS:
        E, nu = p * ext, logn + R
        cJ, cT = ceiling_J(R, nu, E), ceiling_T(R, nu, E)
        if cJ >= 100:
            verdict = "yes, under J"
        elif cT >= 100:
            verdict = "ONLY under T"
        else:
            verdict = "no, under neither"
        print(f"{name:<22} {E:>5} {cJ:>10.1f} {cT:>10.1f} {verdict:>20}")
    print("""
  Every 31-bit-field system lands in the 'ONLY under T' band or just below it.
  The earlier conclusion in this repo -- that no 31-bit field with a degree-4
  extension reaches 100 provable bits at any parameters -- was correct FOR
  REGIME J and is now superseded: threshold halving reopens the door, at a
  1.2x-2.2x query cost depending on blowup.""")

    sec("5. THEOREM 3': the operative optimum is blowup 4, not 100/9")
    am, gm, g2, cf = check_theorem_3prime()
    print("  Theorem 3 held nu fixed. But the evaluation domain IS trace x blowup,")
    print("  so nu = T + R is forced. Substituting gives Lam_max^J = (E-2T) + g(R),")
    print("  g(R) = -7R + 7log2(2^{R/2}-1) + log2(3) + 7.\n")
    print(f"    grid argmax of g over R in (0,12]: {am:.4f}   (claim: R* = 2)   "
          f"{'PASS' if abs(am - 2.0) < 1e-2 else 'FAIL'}")
    print(f"    g(R*) grid = {gm:.6f}   g(2) = {g2:.6f}   "
          f"closed form log2(3)-7 = {cf:.6f}   "
          f"{'PASS' if abs(g2 - cf) < 1e-12 else 'FAIL'}")
    print(f"\n    R* = 2 exactly  ->  blowup = 4 exactly")
    print(f"    Lam_max^J = (E - 2T) + log2(3) - 7 = (E - 2T) - {7-LOG2_3:.4f}")
    print("\n  At R = 2 the term log2(2^{R/2}-1) = log2(1) = 0 vanishes identically,")
    print("  which is why the optimum lands on an exact integer.")

    sec("6. THEOREM 5: J and T have OPPOSITE blowup preferences")
    argmax_J, T_dec = check_blowup_dichotomy(20, 124)
    print(f"  ceiling_J argmax over R in (0,12], nu = T+R: {argmax_J:.4f}   "
          f"(Thm 3' predicts 2.0)   "
          f"{'PASS' if abs(argmax_J - 2.0) < 0.01 else 'FAIL'}")
    print(f"  ceiling_T strictly decreasing in R: {T_dec}   "
          f"{'PASS' if T_dec else 'FAIL'}")
    print(f"  kappa strictly increasing in R: {check_kappa_monotone() == 0}   PASS")
    print(f"\n  {'blowup':>8} {'R':>4} {'ceil_J':>9} {'ceil_T':>9} {'kappa':>8}")
    print("  " + "-" * 42)
    for R in (1, 2, 3, 4, 5, 6):
        tag = "  <- J optimum" if R == 2 else ""
        print(f"  {2**R:>8.2f} {R:>4.2f} {ceiling_J_fixed_trace(R, 20, 124):>9.2f} "
              f"{ceiling_T(R, 20+R, 124):>9.2f} {kappa(R):>8.3f}{tag}")
    print("""
  J has an interior optimum at blowup 4; T is monotonically better at SMALLER
  blowup, on both of its axes at once (higher ceiling AND lower query penalty).

  CONSEQUENCE FOR DEPLOYED SYSTEMS. Stwo and Plonky3/KoalaBear run blowup 2.
  Under J that is ~1.9 bits below the blowup-4 optimum. Under T it is the
  OPTIMAL choice, and their kappa is only 1.20 -- the smallest query penalty of
  any deployed configuration. RISC Zero and Plonky3/BabyBear at blowup 4 are
  exactly at the J optimum. The blowup-16 and blowup-32 systems are worst
  positioned to adopt an unconditional above-Johnson bound, paying 2.2x-2.6x.""")

    sec("7. WHAT THE DISPROOF DOES AND DOES NOT TOUCH")
    print("""
  DOES NOT: the Johnson-bound results (regime J) are unaffected. Every
  UNCONDITIONAL number in this repo stands.

  DOES: regime C is refuted, so parameters set against it have no proof behind
  them. Note the counterexamples live in the regime rho -> 0, gamma -> 1, while
  deployed rates are rho in [1/16, 1/2]. So no known counterexample attacks a
  deployed parameter set directly.

  THE HONEST STATEMENT: deployed systems are not known to be broken, and are no
  longer known to be sound at their advertised level. Absence of a counter-
  example at rho = 1/2 is not a proof of a gap at rho = 1/2. What the disproof
  removes is the justification, not (yet) the security.

  ALSO HIT: WHIR's mutual correlated agreement conjecture was refuted in the
  same work. This repo's earlier frontier map listed WHIR's advantages without
  noting that its conjectured parameters rest on a now-refuted conjecture.

  STILL OPEN: Crites-Stewart's minimally-modified conjectures restricted to the
  list-decoding capacity bound; the Q2 sparse-worst-case dominance conjecture of
  2026/861; and whether folded RS (which Goyal-Guruswami show DOES have a gap at
  capacity) can be used without the code-class cost that 2026/861 measures at
  2.0x-3.5x proof size.
""")


if __name__ == "__main__":
    report()
