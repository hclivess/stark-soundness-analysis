"""
The already-published free lever: what BCHKS25 Result 1 is worth, and what it costs.

Iteration 33 found that a = 0 is PROVED at the unique-decoding radius (BCHKS25
result 1: O_{eps*}(1) exceptional z's, all RS codes, arbitrarily small proximity
loss eps* > 0), while Ethereum's soundcalc -- which this repo transcribed -- still
implements the superseded O(n) bound. This file works out three things iteration
33 asserted but did not check:

  1. whether Theorem 7's 7/7 regime prediction survives the corrected ceiling;
  2. what the correction is actually worth to a deployed system;
  3. whether it is worth anything at all, given that the O_{eps*}(1) constant is
     unspecified and the proximity loss costs query-phase yield.

FINDING 1 -- THEOREM 7 IS INVARIANT TO THE UDR CEILING
--------------------------------------------------------
This was the real risk. Theorem 7 predicts which regime a system should be
reported in, and it called all seven correctly using the a = 1 UDR ceiling. If
raising that ceiling by nu bits moved the crossover, the 7/7 result would have
been an artifact of a superseded bound.

It does not move. The crossover is

    s* = (K_JBR(m_eq) - g) / y_UDR

and K_UDR does not appear in it. The crossover is where the UDR query term
reaches the JBR CEILING -- past that point JBR is capped and UDR keeps climbing.
How high UDR can eventually climb is irrelevant to where it overtakes.

Recomputed with K_UDR = E (a = 0) instead of E - nu + 2 (a = 1): every s* is
bit-identical and the prediction stays 7/7. That is a structural invariance, not
a numerical coincidence, and it is worth stating because it means the repo's
headline prediction never depended on the bound that turned out to be stale.

FINDING 2 -- THE VALUE IS A NEW CEILING, NOT SMALLER PROOFS
-------------------------------------------------------------
For both deployed UDR systems the query phase binds at ~100 bits, below even the
old ceiling of ~102. So at today's targets the correction changes nothing: you
cannot spend a ceiling you were not touching.

What it changes is what is REACHABLE. At E = 124, nu = 23, the a = 1 ceiling caps
SP1 at 102.4 bits no matter how many queries it makes. Under a = 0 the cap is
124.0, and targets that were previously unreachable at ANY query count become
reachable:

    target 110  ->  unreachable at a=1;  139 queries at a=0
    target 120  ->  unreachable at a=1;  153 queries at a=0
    target 124  ->  unreachable at a=1;  159 queries at a=0

against SP1's current 124. So +25% queries buys +20 bits that no query count
could previously buy. That is the concrete shape of this repo's "two free
levers" thesis: a bound improvement, already published, that no calculator
implements and no config change could substitute for.

FINDING 3 -- BUT THE CONSTANT DECIDES IT, AND IT IS UNSPECIFIED
-----------------------------------------------------------------
The abstract says O_{eps*}(1): a constant depending on the proximity loss, with
no stated dependence. Two costs follow, and only the first is obvious.

(a) Proximity loss shrinks the certified radius, so it costs query yield:
    y = -log2((1+rho)/2 + eps*). Section 3 tabulates the query inflation.

(b) a = 0 only beats a = 1 if log2 C(eps*) < nu + log2(1/gamma) -- about 24.4
    bits at nu = 23, rho = 1/4. If C grows like 1/eps* or 1/eps*^2 that is
    satisfied comfortably at every useful eps*. If C grows like exp(1/eps*), it
    FAILS for eps* below about 0.07, and the useful range of the theorem is
    bounded BELOW rather than above -- the opposite of the usual intuition that
    smaller proximity loss is strictly better.

So the honest summary: the lever is real, it is already proved, it is worth up
to nu bits of previously-unreachable ceiling, and whether it is worth anything
at a given eps* cannot be settled without the constant. The PDF is
Cloudflare-walled; the abstract does not give it.
"""

import math


def y_udr(rho, eps_star=0.0):
    """Per-query bits at the UDR radius, degraded by proximity loss eps*."""
    return -math.log2((1 + rho) / 2.0 + eps_star)


def ceiling_a1(E, nu, rho):
    """soundcalc's UDR bound: (gamma*n + 1)/|F|, gamma = (1-rho)/2."""
    gamma = (1 - rho) / 2.0
    return E - math.log2(gamma * 2.0 ** nu + 1)


def ceiling_a0(E, log2C=0.0):
    """BCHKS25 result 1: O_{eps*}(1) exceptions, so the ceiling is E - log2 C."""
    return E - log2C


def queries_for(target, g, rho, eps_star=0.0):
    y = y_udr(rho, eps_star)
    return float("inf") if y <= 0 else (target - g) / y


def a0_beats_a1_threshold(nu, rho):
    """log2 C must stay below this for a = 0 to be the better bound."""
    return nu + math.log2(1.0 / ((1 - rho) / 2.0))


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    from regime_crossover import commit_jbr, m_eq, yield_udr

    ZK = [("SP1 6.1.0", 124, 2, 21, 124, 16, "UDR"),
          ("OpenVM 1.5.0", 124, 1, 23, 193, 20, "UDR"),
          ("Airbender", 124, 1, 24, 87, 28, "JBR"),
          ("Pico", 124, 1, 22, 84, 16, "JBR"),
          ("ZisK 0.16.1", 192, 1, 21, 229, 16, "JBR"),
          ("RISC Zero", 124, 2, 21, 50, 0, "JBR"),
          ("Miden", 128, 3, 18, 27, 16, "JBR")]

    sec("1. THEOREM 7 IS INVARIANT TO THE UDR CEILING (the real risk, checked)")
    print(f"  {'system':<15} {'K_UDR a=1':>10} {'K_UDR a=0':>10} {'K_JBR':>8} "
          f"{'s*':>8} {'s':>6} {'pred':>6} {'reported':>9}")
    print("  " + "-" * 78)
    wrong = 0
    for nm, E, R, T, s, g, reg in ZK:
        nu, rho = T + R, 2.0 ** -R
        k1, k0 = ceiling_a1(E, nu, rho), ceiling_a0(E)
        kJ = commit_jbr(R, nu, E, m_eq(R))
        star = (kJ - g) / yield_udr(R)
        pred = "UDR" if s > star else "JBR"
        wrong += (pred != reg)
        print(f"  {nm:<15} {k1:>10.1f} {k0:>10.1f} {kJ:>8.1f} {star:>8.1f} "
              f"{s:>6} {pred:>6} {reg:>9}")
    print(f"""
  {7-wrong}/7 correct, unchanged. s* = (K_JBR - g)/y_UDR contains no K_UDR term,
  so raising the UDR ceiling cannot move the crossover -- it only extends how
  far UDR can be pushed afterwards. The 7/7 result never rested on the stale
  bound.""")

    sec("2. WHAT IT IS WORTH: TARGETS THAT WERE UNREACHABLE AT ANY QUERY COUNT")
    E, R, T, g = 124, 2, 21, 16
    nu, rho = T + R, 2.0 ** -R
    cap1 = ceiling_a1(E, nu, rho)
    print(f"  SP1: E={E}, nu={nu}, rho=1/4, g={g}. "
          f"a=1 ceiling {cap1:.1f}, a=0 ceiling {ceiling_a0(E):.1f}\n")
    print(f"  {'target':>7} {'a=1':>16} {'a=0 queries':>13} {'vs current 124':>15}")
    print("  " + "-" * 56)
    for tgt in (100, 110, 120, 124):
        q = queries_for(tgt, g, rho)
        reach = "reachable" if tgt <= cap1 else "UNREACHABLE"
        print(f"  {tgt:>7} {reach:>16} {q:>13.0f} {q/124 - 1:>+14.0%}")
    print("""
  At today's ~100-bit target nothing changes: the query phase binds first. The
  correction converts previously-impossible targets into merely expensive ones.""")

    sec("3. THE PROXIMITY LOSS COSTS QUERIES")
    print(f"  {'target':>7} " + " ".join(f"{'eps*=%.2f' % e:>11}"
                                         for e in (0.0, 0.02, 0.05, 0.10)))
    print("  " + "-" * 56)
    for tgt in (100, 110, 120):
        row = " ".join(f"{queries_for(tgt, g, rho, e):>11.0f}"
                       for e in (0.0, 0.02, 0.05, 0.10))
        print(f"  {tgt:>7} {row}")
    print("""
  A proximity loss of 0.10 costs about 45% more queries at every target. So eps*
  wants to be small -- which is exactly where the unspecified constant bites.""")

    sec("4. WHETHER a = 0 WINS AT ALL DEPENDS ON THE UNSPECIFIED CONSTANT")
    thr = a0_beats_a1_threshold(nu, rho)
    print(f"  a = 0 beats a = 1 iff log2 C(eps*) < nu + log2(1/gamma) = {thr:.1f}"
          f"  (C < {2**thr:.3g})\n")
    print(f"  {'eps*':>7} {'C = 1/eps*':>14} {'C = 1/eps*^2':>15} "
          f"{'C = exp(1/eps*)':>18}")
    print("  " + "-" * 60)
    for e in (0.02, 0.05, 0.10, 0.20):
        cells = []
        for C in (1 / e, 1 / e ** 2, math.exp(1 / e)):
            v = math.log2(C)
            cells.append(f"{v:>7.1f} {'ok' if v < thr else 'FAILS':>6}")
        print(f"  {e:>7.2f} {cells[0]:>14} {cells[1]:>15} {cells[2]:>18}")
    print("""
  Polynomial dependence is harmless. An exponential one -- exp(1/eps*) -- fails
  below eps* ~ 0.07, which would mean the theorem's useful range is bounded
  BELOW, not above: you would need a LARGE proximity loss for a = 0 to pay, and
  a large proximity loss is what section 3 shows is expensive.

  That is the whole uncertainty, and it sits in one unstated constant.""")


if __name__ == "__main__":
    report()
