"""
The a >= 1 floor is proved for interleaved codes and NOT for FRI -- and there
are 25-37 bits of room between what is proved possible and proved impossible.

*** CORRECTED THREE TIMES -- READ ALL NOTES BEFORE THE NUMBERS ***

*** ITERATION 67: THE LIST-SIZE CONVENTION IS RATE-1/4-ONLY ***
This file computes the MCA floor with L = 2m+1. soundcalc's pinned-m branch
(johnson_bound.py:91-105) uses (m+0.5)/sqrt(rho), and the two agree ONLY at
rho = 1/4 -- the ratio is 2*sqrt(rho), independent of m. Effect on the headroom
figures below:

    Airbender, Pico, ZisK   rho = 1/2    understated by 0.50 bits (conservative)
    RISC Zero               rho = 1/4    exact
    Miden                   rho = 1/8    OVERSTATED by 0.50 bits
    SP1, OpenVM             UDR, L = 1   unaffected

So Miden's headroom is 0.5 bits too generous and the rest are conservative or
exact. Small, and the direction is what makes it worth recording: everywhere
else this convention errs toward understating the repo's own claims. See
mca_headroom.py, which also measures the floor on the one deployed system whose
soundness actually rests on mutual correlated agreement.

*** ITERATION 40: THE HEADROOM TABLE MIXES REGIMES ***
Section 3 computes headroom for all seven zkVMs using commit_jbr and the
Johnson list size 2m+1. Two of the seven -- SP1 and OpenVM -- are reported in
UDR, whose bound (gamma*n+1)/|F| is a different formula and whose list size is
1 by the definition of unique decoding. Corrected:

    system     headroom as published    corrected    nu
    SP1                        29.4         20.6    23
    OpenVM                     36.3         21.0    24
    (the five JBR systems are unchanged)

So the range is 20.6 to 37.3 bits, not 25.2 to 37.3 -- and FINDING 3's claim
that headroom "exceeds nu at every system" is FALSE for the two UDR systems.
It holds for the five that actually run the Johnson regime. This is the same
regime-scope error iteration 39 found in m_star.py, in a file written eight
iterations earlier; iteration 40 audited the repo for it after finding the
first instance.

*** PARTIALLY RETRACTED IN ITERATION 33 -- READ THIS TOO ***
This file concludes below that "nothing known forbids a = 0 for RS at the
Johnson radius". That is correct about the MCA floor and WRONG as a general
statement: BCHKS25's own result list (eprint 2025/2055, read for the first time
in iteration 33) proves that at or beyond the Johnson radius some RS codes need
Omega(n^1.99) exceptional z's, and n^tau for every constant tau. So a = 0 above
Johnson IS obstructed by published counterexamples -- the MCA floor simply is
not the binding constraint. Everything below about mutual correlated agreement,
the list-size numerator, and the headroom AT the Johnson radius stands.
See radius_staircase.py for the corrected picture.

Iteration 31 graded eprint 2026/861's O(1)/|F| claim (a = 0 above the Johnson
radius, conditional on Q2) down to tier 3 on PROVENANCE: unreviewed, one group,
uncited by the subsequent literature. That grading stands. But provenance is not
the same as plausibility, and this iteration checks the separate question of
whether anything KNOWN forbids the result. Nothing does, and the repository was
close to implying otherwise.

THE NEWEST LOWER BOUND (arXiv 2607.10572, 2026-07-12, fetched and read)
------------------------------------------------------------------------
Gao, Yang, Xu, Kan, "List-Decoding Counterexamples Yield Lower Bounds on Mutual
Correlated Agreement Error":

    "Given an explicit counterexample to the (p,L)-list-decodability of a linear
    code over F_q, we construct a related code C' of the same length and
    dimension such that
        err_MCA(C', p)  >=  (1/q) * ceil( (L+1)q / (q+L) )
    while decreasing its minimum distance by at most one."

Mutual correlated agreement is the property WHIR's soundness rests on, so this
is a proved FLOOR on a quantity deployed systems depend on. At every realistic
parameter the ceiling evaluates exactly:

    err_MCA  >=  (L+1)/q        for all q >> L

FINDING 1 -- THE FLOOR IS SET BY LIST SIZE, NOT BY DOMAIN SIZE
----------------------------------------------------------------
The numerator is L+1, where L is the LIST SIZE at the radius in question -- not
the domain size n. That distinction decides the whole a-classification, and this
repository's own code already records the answer:

    regime_crossover.py, commit_jbr():
        bits_n_over_q = E - log2(folding) - log2(n+1) - log2(2m+1) + ...
                                            ^^^^^^^^^   ^^^^^^^^^^^^
                                            domain      LIST SIZE

BCHKS25's Johnson-regime bound carries log2(n+1) and log2(2m+1) as SEPARATE
factors. The list size is 2m+1 -- a function of the proximity parameter only,
INDEPENDENT OF n. At the optimal m for deployed rates that is L = 2 to 18.

So in the Johnson regime the MCA floor is (L+1)/q with L = O(m): that is
O(1)/|F|, i.e. a = 0. The strongest known lower bound does not forbid a = 0 for
Reed-Solomon at the Johnson radius. It never did.

FINDING 2 -- SO WHAT IS THE a >= 1 FLOOR ACTUALLY PROVED FOR?
---------------------------------------------------------------
For the INTERLEAVED test, and there only. Roth-Zemor's false-witness probability
is (e+1)/q where e is the PROXIMITY PARAMETER, e <= (d-1)/3 = Theta(n), and
Diamond-Posen Remark 2 exhibits a pair attaining it (iteration 28). Numerator
Theta(n), sharp, a = 1 unavoidable.

That is a statement about interleaved codes. README finding 5 says so correctly.
But the a-table at the top of the README reads

    code proximity (FRI, WHIR, Ligero/Brakedown)   a >= 1

and that row is an EMPIRICAL observation about every bound anyone has proved --
not a proved floor for FRI or WHIR. The distinction was never stated. For
Ligero/Brakedown it is a theorem; for FRI and WHIR it is a track record.

FINDING 3 -- THE HEADROOM IS 25 TO 37 BITS
--------------------------------------------
Between the best proved UPPER bound on commit-phase soundness (BCHKS25, what
this repo models) and the best proved LOWER bound (the MCA floor, E - log2(L+1))
there is a gap that no theorem has closed in either direction. Section 3
measures it across the seven verified zkVMs: 25.2 to 37.3 bits.

That gap is slightly LARGER than nu (21-25 bits at deployed sizes), which is
exactly what an a: 1 -> 0 improvement would deliver. So the lower bound leaves
precisely enough room for the action-orbit claim, plus its constant. The claim
is structurally consistent with everything proved, and iteration 31's tier-3
grading should be read as "unverified provenance", never as "implausible".

CORRECTION TO ITERATION 31'S SOURCE
------------------------------------
Iteration 31 built the open-zone analysis on Kambire (arXiv 2604.09724). That
note says up front it "flesh[es] out a sketch by Krachun and Kazanin"; the
primary source is

    Krachun, Kazanin, Habock, "Failure of proximity gaps close to capacity",
    eprint 2026/782 -- cited as [KKH26] by Goyal-Guruswami-Sun-Wootters.

whose abstract states the failure at "eta = Theta_rho(1/log n)". The subscript
matters: the constant is RATE-DEPENDENT. Iteration 31's open_zone.py sweeps a
single rate-independent c across all three rates, which is the wrong shape --
the emptying threshold is c(rho), not c. The qualitative conclusion (the zone
can be empty at deployed n, so Q2's value rests on two unknowns) is unaffected;
the per-rate comparison in that table is not meaningful as drawn.
"""

import math


def mca_floor_prob(q, L):
    """Gao-Yang-Xu-Kan: err_MCA >= (1/q) * ceil((L+1)q/(q+L))."""
    return math.ceil((L + 1) * q / (q + L)) / q


def mca_floor_bits(E, L):
    """The floor expressed as bits of soundness: E - log2(L+1)."""
    return E - math.log2(L + 1)


def johnson_list_size(m):
    """BCHKS25's Johnson-regime list size, as used in commit_jbr: 2m+1."""
    return 2.0 * m + 1.0


def interleaved_numerator(n, rho):
    """Roth-Zemor: e+1 with e <= (d-1)/3, d = (1-rho)n+1. Theta(n)."""
    return (1.0 - rho) * n / 3.0 + 1.0


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    from regime_crossover import commit_jbr, m_eq

    sec("1. THE MCA FLOOR IS EXACTLY (L+1)/q AT EVERY DEPLOYED PARAMETER")
    print(f"  {'q':>10} {'L':>10} {'floor':>14} {'as bits':>10} "
          f"{'(L+1)/q bits':>14} {'match':>7}")
    print("  " + "-" * 70)
    for q_log in (31, 124, 192):
        q = 2 ** q_log
        for L in (5, 33, 2 ** 11):
            f = mca_floor_prob(q, L)
            a_, b_ = math.log2(f), math.log2((L + 1) / q)
            print(f"  2^{q_log:<8} {L:>10} {f:>14.3e} {a_:>10.2f} {b_:>14.2f} "
                  f"{'yes' if abs(a_-b_) < 1e-9 else 'NO':>7}")

    sec("2. THE NUMERATOR IS THE LIST SIZE, AND IT DOES NOT SCALE WITH n")
    print("""  BCHKS25's bound, as this repo already implements it, keeps the two
  apart:

      bits = E - log2(folding) - log2(n+1) - log2(2m+1) + (1/2)log2(rho)
                                 ^ domain      ^ LIST SIZE

  The list size is 2m+1. Doubling n does not change it.\n""")
    print(f"  {'m':>8} {'list size 2m+1':>16} {'floor bits at E=124':>22}")
    print("  " + "-" * 50)
    for m in (0.85, 2.0, 8.24, 16.0, 100.0):
        L = johnson_list_size(m)
        print(f"  {m:>8.2f} {L:>16.2f} {mca_floor_bits(124, L):>22.2f}")
    print("""
  Compare the interleaved case, where the numerator IS the domain size:""")
    print(f"\n  {'n':>10} {'interleaved numerator (rho=1/4)':>34} {'ratio to n':>12}")
    print("  " + "-" * 60)
    for n in (2 ** 16, 2 ** 20, 2 ** 24):
        v = interleaved_numerator(n, 0.25)
        print(f"  {n:>10} {v:>34.4g} {v/n:>12.4f}")
    print("""
  Theta(n) for interleaved, Theta(1) for the RS Johnson regime. The a >= 1
  floor is PROVED for the first and merely OBSERVED for the second.""")

    sec("3. HEADROOM: WHAT NO THEOREM HAS CLOSED")
    ZK = [("SP1 6.1.0", 124, 2, 21), ("OpenVM 1.5.0", 124, 1, 23),
          ("Airbender", 124, 1, 24), ("Pico", 124, 1, 22),
          ("ZisK 0.16.1", 192, 1, 21), ("RISC Zero", 124, 2, 21),
          ("Miden", 128, 3, 18)]
    print(f"  {'system':<15} {'E':>5} {'nu':>4} {'m_eq':>7} {'BCHKS25 K':>11} "
          f"{'MCA floor':>11} {'headroom':>9} {'nu':>5}")
    print("  " + "-" * 74)
    gaps = []
    for nm, E, R, T in ZK:
        nu = T + R
        m = m_eq(R)
        K = commit_jbr(R, nu, E, m)
        F = mca_floor_bits(E, johnson_list_size(m))
        gaps.append(F - K)
        print(f"  {nm:<15} {E:>5} {nu:>4} {m:>7.2f} {K:>11.1f} {F:>11.1f} "
              f"{F-K:>9.1f} {nu:>5}")
    print(f"""
  Headroom {min(gaps):.1f} to {max(gaps):.1f} bits: the distance between the best proved upper
  bound and the best proved lower bound. Nobody has closed it from either side.

  Note it exceeds nu at every system. An a: 1 -> 0 improvement is worth exactly
  nu bits, so the strongest known lower bound leaves room for it AND for the
  constant. The action-orbit claim is not in tension with anything proved -- the
  objection to it is provenance (iteration 31), not impossibility.

  RETRACTED IN PART, ITERATION 33. The sentence above is right about the MCA
  floor and WRONG as a general statement. BCHKS25's own result list (never read
  until iteration 33) proves that at or beyond the Johnson radius some RS codes
  need Omega(n^1.99) exceptional z's, and n^tau for every constant tau. So a = 0
  above Johnson IS obstructed by published counterexamples; the MCA floor simply
  is not the binding constraint. This file's headroom figures remain correct as
  a statement about mutual correlated agreement at the Johnson radius.
  See radius_staircase.py.""")


REGIMES = {"SP1 6.1.0": "UDR", "OpenVM 1.5.0": "UDR", "Airbender": "JBR",
           "Pico": "JBR", "ZisK 0.16.1": "JBR", "RISC Zero": "JBR",
           "Miden": "JBR"}


def commit_udr(R, nu, E):
    """The UDR bound (gamma*n + 1)/|F|, gamma = (1-rho)/2. No m, no list size."""
    gamma = (1 - 2.0 ** -R) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def headroom_regime_correct(nm, E, R, T):
    """(commit bound, list size, headroom) under the system's REPORTED regime."""
    from regime_crossover import commit_jbr, m_eq
    nu = T + R
    if REGIMES[nm] == "UDR":
        # unique decoding: at most one codeword within the radius, so L = 1
        return commit_udr(R, nu, E), 1.0, mca_floor_bits(E, 1.0) - commit_udr(R, nu, E)
    m = m_eq(R)
    K = commit_jbr(R, nu, E, m)
    L = johnson_list_size(m)
    return K, L, mca_floor_bits(E, L) - K


def report_regime_corrected():
    """Iteration 40: section 3 recomputed in each system's own regime."""
    from regime_crossover import commit_jbr, m_eq
    sec("4. CORRECTED: SECTION 3 APPLIED THE JBR MODEL TO TWO UDR SYSTEMS")
    ZK = [("SP1 6.1.0", 124, 2, 21), ("OpenVM 1.5.0", 124, 1, 23),
          ("Airbender", 124, 1, 24), ("Pico", 124, 1, 22),
          ("ZisK 0.16.1", 192, 1, 21), ("RISC Zero", 124, 2, 21),
          ("Miden", 128, 3, 18)]
    print(f"  {'system':<15} {'regime':>7} {'K published':>12} {'K correct':>10} "
          f"{'head pub':>9} {'head corr':>10} {'nu':>4} {'> nu?':>6}")
    print("  " + "-" * 78)
    corrected = []
    for nm, E, R, T in ZK:
        nu = T + R
        m = m_eq(R)
        Kj = commit_jbr(R, nu, E, m)
        pub = mca_floor_bits(E, johnson_list_size(m)) - Kj
        Kc, Lc, hc = headroom_regime_correct(nm, E, R, T)
        corrected.append((nm, hc, nu))
        print(f"  {nm:<15} {REGIMES[nm]:>7} {Kj:>12.1f} {Kc:>10.1f} "
              f"{pub:>9.1f} {hc:>10.1f} {nu:>4} "
              f"{'yes' if hc > nu else 'NO':>6}")
    fails = [(n, h, v) for n, h, v in corrected if h <= v]
    print(f"""
  Headroom is {min(h for _, h, _ in corrected):.1f} to {max(h for _, h, _ in corrected):.1f} bits, not 25.2 to 37.3. And FINDING 3's
  claim that headroom exceeds nu at EVERY system fails for {len(fails)} of them
  ({', '.join(n for n, _, _ in fails)}) -- exactly the two reported in UDR.
  It holds for the five that actually run the Johnson regime.

  Note the UDR list size is 1: unique decoding means at most one codeword lies
  within the radius, so the MCA floor there is E - log2(2) = E - 1, and the
  headroom is the gap between the UDR commit bound and that.""")


def headroom_at_jbrM(nm, E, R, T):
    """Iteration 57: the same headroom, at soundcalc's DERIVED m rather than m_eq."""
    from regime_crossover import commit_jbr
    from soundcalc_lean import jbr_m
    nu = T + R
    if REGIMES[nm] == "UDR":
        # UDR has no proximity parameter, so nothing moves
        return headroom_regime_correct(nm, E, R, T)
    m = float(jbr_m(2.0 ** -R, E))
    K = commit_jbr(R, nu, E, m)
    L = 2.0 * m + 1.0
    return K, L, mca_floor_bits(E, L) - K


def report_jbrM():
    """Iteration 57: propagating the m_eq -> jbrM correction from iteration 56."""
    sec("5. AT SOUNDCALC'S DERIVED m, THE HEADROOM IS LARGER STILL")
    ZK = [("SP1 6.1.0", 124, 2, 21), ("OpenVM 1.5.0", 124, 1, 23),
          ("Airbender", 124, 1, 24), ("Pico", 124, 1, 22),
          ("ZisK 0.16.1", 192, 1, 21), ("RISC Zero", 124, 2, 21),
          ("Miden", 128, 3, 18)]
    print("""  Iteration 56 established that m_eq is the crossover parameter and jbrM is
  what soundcalc actually evaluates at. Sections 3-4 used m_eq. Redone:\n""")
    print(f"  {'system':<15} {'regime':>7} {'head @m_eq':>11} {'head @jbrM':>11} "
          f"{'nu':>4} {'> nu?':>7}")
    print("  " + "-" * 62)
    hs = []
    for nm, E, R, T in ZK:
        nu = T + R
        _, _, a = headroom_regime_correct(nm, E, R, T)
        _, _, b = headroom_at_jbrM(nm, E, R, T)
        hs.append((nm, b, nu))
        print(f"  {nm:<15} {REGIMES[nm]:>7} {a:>11.1f} {b:>11.1f} {nu:>4} "
              f"{'yes' if b > nu else 'NO':>7}")
    jbr = [(n, h, v) for n, h, v in hs if REGIMES[n] == "JBR"]
    print(f"""
  The two UDR rows do not move -- the UDR bound has no proximity parameter. The
  five JBR rows rise from 25.2-37.3 to {min(h for _, h, _ in jbr):.1f}-{max(h for _, h, _ in jbr):.1f}, so the full range is
  {min(h for _, h, _ in hs):.1f}-{max(h for _, h, _ in hs):.1f} bits rather than 20.6-37.3.

  FINDING 3's conclusion is unaffected in structure and stronger in degree: the
  headroom still exceeds nu for every Johnson-regime system, now by 14-22 bits
  rather than 10-14, and still fails for the two UDR systems (iteration 40).""")


if __name__ == "__main__":
    report()
    report_regime_corrected()
    report_jbrM()
