"""
Most of the a-floor gap is not a target. It is the domain-size factor the two
bounds treat differently, and no theorem can close it.

This repo has quoted "20.6-45.0 bits nobody has closed" as its headline unclosed
quantity since iteration 40, refined at iterations 57, 67 and 68. The number is
right. The implication usually drawn from it -- that a better proximity-gaps
theorem could recover that much -- is not, and this file separates the part that
is a genuine target from the part that is a category difference.

THE TWO BOUNDS DO NOT BOUND THE SAME THING
--------------------------------------------
The MCA floor (Gao-Yang-Xu-Kan) lower-bounds err_MCA, a per-instance quantity
depending on the LIST SIZE:

    err_MCA >= (L+1)/q          L = (m+0.5)/sqrt(rho)

BCHKS25's commit bound upper-bounds the commit-phase error, which unions over
the evaluation domain and therefore carries an explicit factor n:

    K_nq = E - log2(fold) - log2(n+1) - log2(2m+1) + (1/2)log2(rho)

Subtracting exactly:

    F - K_nq = nu + log2(fold) + 1 + log2(1 + 2^-nu)
                                   - log2(1 + sqrt(rho)/(m+0.5))   (Prop 9)

verified to 1e-9 over every admissible (E, R, nu, m). The leading term carries
no m, no rho and no E; the two correction terms are bounded by 2^-nu and by
sqrt(rho)/(m+0.5), so at any deployed parameter the gap is

    nu + log2(folding) + 1   to within 0.07 bits

My first draft of this file asserted the m dependence cancels EXACTLY, dropping
the +1 in log2(L+1). The adversarial suite caught it on the first run: from
m = 2 to m = 500 the gap moves 0.357 bits, not 0. The cancellation is asymptotic
in m, and the residual is exactly log2(1 + sqrt(rho)/(m+0.5)).

The leading term is a property of the two bounds' SHAPES, not of any constant
either of them carries. Verified against the deployed set: 23.0, 24.0, 24.9,
25.0, 26.9 bits against nu + 2 of 23, 24, 25, 25, 27.

No improvement to the proximity-gaps constant closes any of it. To close it one
would need a lower bound on the commit error itself -- a quantity that unions
over the domain -- not on the MCA error.

SO THE GAP SPLITS IN TWO
--------------------------
    total headroom  =  (nu + log2(fold) + 1)  +  (K_nq - K_linear)
                        ^ structural             ^ the linear branch's slack

At soundcalc's derived m, across the five Johnson-regime systems:

    system      nu    K_lin   K_nq    floor   headroom  structural   slack
    Airbender   25     78.3   92.5    119.5       41.2        26.9    14.2
    Pico        23     80.3   94.5    119.5       39.2        24.9    14.2
    ZisK        22    140.8  161.8    185.8       45.0        24.0    21.0
    RISC Zero   23     76.8   93.6    118.6       41.8        25.0    16.8
    Miden       21     78.7   98.6    121.6       42.9        23.0    19.9

    structural   23.0-26.9 bits    59% of the total
    slack        14.2-21.0 bits    41% of the total

Only the slack is a target for a better theorem, and it is a third to a half of
what the headline number suggests.

    CORRECTED IN ITERATION 71. The first clause is wrong. The slack is slack in
    the COMMIT bound, and the commit bound does not bind at any deployed
    parameter -- the query phase does, for all seven verified zkVMs. Collapsing
    the m-exponent from 5 to 2, far beyond any plausible theorem, is worth at
    most 1.3 bits and nothing at all for three of the five systems, because the
    optimum sits at the query/commit crossover and the query yield saturates at
    R/2. See gap_closed_form.py, Propositions 10 and 11. Essentially none of the
    20.6-45.0 bits is recoverable soundness.

WHY THE SLACK EXISTS: THE WEAKER BRANCH ALWAYS BINDS
------------------------------------------------------
commit_jbr returns min(K_linear, K_nq). Sweeping 700 parameter points across
E in {64,124,128,192,256}, R in 1..4, nu in 14..30 and m in 0.6..1000, the n/q
branch binds at 25 of them -- all at m = 0.6, where the two agree to within
0.005 bits. At every m any system would choose, K_linear is the smaller and
therefore the operative bound.

That is where the 14-21 bits live: the linear branch is looser than the n/q
branch by exactly that much, and it is the one doing the work. A sharper linear
term would move the ceiling; a sharper constant in the n/q term would not,
because that branch is already slack.

WHAT THIS DOES NOT CHANGE
---------------------------
The headline number itself: 20.6-45.0 bits between the two published bounds is
still what those two bounds say, and a_floor_scope's arithmetic stands. What
changes is what a reader should conclude from it. "20.6-45.0 bits nobody has
closed" invites the reading that a theorem could recover 45 bits of soundness.
At most 14-21 of them are available even in principle, and only to an
improvement in the linear proximity-gaps term specifically.

It also does not touch finding 5's actual claim, which is about whether a = 0 is
FORBIDDEN at the Johnson radius. That question is about the exponent on n, and
this is about the constant relating two different error quantities.
"""

import math

from regime_crossover import gamma_jbr
from soundcalc_lean import jbr_m

# (name, E, R, T) -- the five systems reported in the Johnson regime
JBR_SYSTEMS = [("Airbender", 124, 1, 24), ("Pico", 124, 1, 22),
               ("ZisK", 192, 1, 21), ("RISC Zero", 124, 2, 21),
               ("Miden", 128, 3, 18)]


def commit_branches(R, nu, E, m, folding=2):
    """(K_linear, K_n_over_q) -- the two arms of commit_jbr's min."""
    rho = 2.0 ** -R
    sq = math.sqrt(rho)
    mm = m + 0.5
    pp = gamma_jbr(R, m)
    if pp <= 0.0:
        return float("-inf"), float("-inf")
    n = 2.0 ** nu
    lin = E - math.log2(max(((2 * mm ** 5 + 3 * mm * pp * rho) * n / (3 * rho * sq)
                             + mm / sq) * max(folding - 1.0, 1.0), 1.0))
    nq = (E - math.log2(folding) - math.log2(n + 1.0)
          - math.log2(2.0 * m + 1.0) + 0.5 * math.log2(rho))
    return lin, nq


def mca_floor(E, R, m):
    """Gao et al.: no proof can show err_MCA below (L+1)/q."""
    return E - math.log2((m + 0.5) / math.sqrt(2.0 ** -R) + 1.0)


def structural_gap(E, R, nu, m, folding=2):
    """F - K_nq. Proposition 9: nu + log2(folding) + 1, to within 0.07 bits."""
    return mca_floor(E, R, m) - commit_branches(R, nu, E, m, folding)[1]


def predicted_structural(nu, folding=2):
    """Proposition 9's LEADING term. Carries no m, no rho and no E."""
    return nu + math.log2(folding) + 1.0


def predicted_structural_exact(R, nu, m, folding=2):
    """Proposition 9 in full, exact to 1e-9 at every admissible parameter."""
    L = (m + 0.5) / math.sqrt(2.0 ** -R)
    return (nu + math.log2(folding) + 1.0
            + math.log2(1.0 + 2.0 ** -nu) - math.log2(1.0 + 1.0 / L))


def structural_residual(R, nu, m):
    """How far the leading term sits from the exact value. Bounded by
    log2(1 + sqrt(rho)/(m+0.5)), which is 0.07 bits at deployed m."""
    return abs(predicted_structural_exact(R, nu, m)
               - predicted_structural(nu))


def linear_slack(E, R, nu, m, folding=2):
    """K_nq - K_linear: how much looser the branch that actually binds is."""
    lin, nq = commit_branches(R, nu, E, m, folding)
    return nq - lin


def split(name, E, R, T, folding=2):
    """(m, K_lin, K_nq, floor, headroom, structural, slack) at soundcalc's m."""
    nu = T + R
    m = float(jbr_m(2.0 ** -R, E))
    lin, nq = commit_branches(R, nu, E, m, folding)
    f = mca_floor(E, R, m)
    return m, lin, nq, f, f - lin, f - nq, nq - lin


def nq_binding_points(folding=2):
    """Parameter points, out of the swept grid, where the n/q branch binds."""
    out = []
    for E in (64, 124, 128, 192, 256):
        for R in (1, 2, 3, 4):
            for nu in (14, 18, 21, 25, 30):
                for m in (0.6, 1, 2, 5, 20, 100, 1000):
                    lin, nq = commit_branches(R, nu, E, m, folding)
                    if nq == float("-inf"):
                        continue
                    if nq < lin:
                        out.append((E, R, nu, m, lin, nq))
    return out


def sweep_size():
    return 5 * 4 * 5 * 7


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. PROPOSITION 9: THE GAP HAS AN IRREDUCIBLE FLOOR OF nu + log2(fold) + 1")
    print("""
  The two bounds do not bound the same quantity. The MCA floor is per-instance
  and scales in the LIST SIZE; BCHKS25's commit bound unions over the evaluation
  domain and carries an explicit factor n. Subtracting:

      F - K_nq = log2(fold) + nu + log2( 2(m+0.5) / ((m+0.5)/sqrt(rho)) )
                 - (1/2)log2(rho)
               = nu + log2(fold) + 1

  The leading term carries no m, no rho and no E. The floor on the gap is a
  property of the two bounds' SHAPES, not of any constant either carries.

  The correction terms are bounded by 2^-nu and sqrt(rho)/(m+0.5). My first
  draft claimed the m dependence cancels EXACTLY; the adversarial suite caught
  that on the first run -- from m=2 to m=500 the gap moves 0.357 bits.\n""")
    print(f"  {'system':<11} {'nu':>4} {'m':>6} {'F - K_nq':>10} "
          f"{'nu+log2(fold)+1':>17} {'diff':>7}")
    print("  " + "-" * 60)
    for nm, E, R, T in JBR_SYSTEMS:
        nu = T + R
        m = float(jbr_m(2.0 ** -R, E))
        g, p = structural_gap(E, R, nu, m), predicted_structural(nu)
        print(f"  {nm:<11} {nu:>4} {m:>6.0f} {g:>10.2f} {p:>17.0f} {g-p:>+7.2f}")
    print("""
  No improvement to the proximity-gaps constant closes any of this. Closing it
  needs a lower bound on the COMMIT error -- a quantity that unions over the
  domain -- not on the MCA error.""")

    sec("2. SO THE HEADLINE GAP SPLITS, AND MOST OF IT IS NOT A TARGET")
    print(f"\n  {'system':<11} {'nu':>4} {'K_lin':>8} {'K_nq':>8} {'floor':>8} "
          f"{'headroom':>9} {'structural':>11} {'slack':>8}")
    print("  " + "-" * 74)
    tot, st, sl = [], [], []
    for nm, E, R, T in JBR_SYSTEMS:
        m, lin, nq, f, h, s_, l_ = split(nm, E, R, T)
        tot.append(h)
        st.append(s_)
        sl.append(l_)
        print(f"  {nm:<11} {T+R:>4} {lin:>8.1f} {nq:>8.1f} {f:>8.1f} "
              f"{h:>9.1f} {s_:>11.1f} {l_:>8.1f}")
    print(f"""
      total headroom   {min(tot):.1f} - {max(tot):.1f} bits
      structural       {min(st):.1f} - {max(st):.1f} bits    {100*sum(st)/sum(tot):.0f}% of the total
      linear slack     {min(sl):.1f} - {max(sl):.1f} bits    {100*sum(sl)/sum(tot):.0f}% of the total

  Only the slack is a target for a better theorem, and it is a third to a half
  of what the headline number suggests.

  CORRECTED IN ITERATION 71: it is not a target either. The slack is in the
  COMMIT bound, which does not bind at any deployed parameter. Collapsing the
  m-exponent 5 -> 2 is worth at most 1.3 bits. See gap_closed_form.py.""")

    sec("3. WHY THE SLACK EXISTS: THE WEAKER BRANCH ALWAYS BINDS")
    pts = nq_binding_points()
    ms = sorted({p[3] for p in pts})
    worst = max((abs(l - q) for _E, _R, _nu, _m, l, q in pts), default=0.0)
    print(f"""
  commit_jbr returns min(K_linear, K_nq). Over {sweep_size()} parameter points --
  E in (64,124,128,192,256), R in 1..4, nu in 14..30, m in 0.6..1000 --
  the n/q branch binds at {len(pts)}, all of them at m in {ms}, where the two
  branches agree to within {worst:.4f} bits.

  At every m a system would actually choose, K_linear is smaller and therefore
  operative. That is where the {min(sl):.0f}-{max(sl):.0f} bits live: the linear branch is looser
  than the n/q branch by exactly that much, and it is the one doing the work.

  A sharper LINEAR term would move the ceiling. A sharper constant in the n/q
  term would not, because that branch is already slack.""")

    sec("4. WHAT THIS DOES AND DOES NOT CHANGE")
    print("""
  DOES NOT change the headline arithmetic. 20.6-45.0 bits between the two
  published bounds is what those bounds say, and a_floor_scope stands.

  DOES change what to conclude from it. "20.6-45.0 bits nobody has closed"
  invites the reading that a theorem could recover 45 bits of soundness. At most
  14-21 are available even in principle, and only to an improvement in the
  linear proximity-gaps term specifically.

  DOES NOT touch finding 5's actual claim, which is whether a = 0 is FORBIDDEN
  at the Johnson radius. That is about the exponent on n; this is about the
  constant relating two different error quantities.""")


if __name__ == "__main__":
    report()
