"""
The a-floor gap, measured on the one system whose soundness actually rests on
mutual correlated agreement -- and a list-size convention this repo got right
only at rate 1/4.

a_floor_scope.py established the gap: BCHKS25's proximity-gaps bound sits
20.6-37.3 bits above the best proved lower bound, the mutual-correlated-agreement
floor err >= (L+1)/q of Gao-Yang-Xu-Kan (arXiv 2607.10572). Every one of those
seven measurements is on a FRI system. But MCA is not FRI's assumption -- it is
WHIR's. a_floor_scope says so itself: "Mutual correlated agreement is the
property WHIR's soundness rests on."

Iterations 63-65 brought a WHIR system into reach, with a property no FRI system
has: OpenVM2 DECLARES its list-decoding parameter. Four of its six circuits pin
explicit_m = 1 or 2 in the toml, so their list sizes are stated rather than
derived, and the floor can be evaluated with nothing assumed.

FINDING 1 -- WHIR SITS CLOSEST TO ITS OWN PROVED FLOOR
--------------------------------------------------------
The floor gives a ceiling on what any proof can establish:

    err_MCA >= (L+1)/q    =>    provable bits <= log2(q) - log2(L+1)

At OpenVM2's declared list sizes, q = |BabyBear^4| = 2^124:

    circuit              m    rate      L    MCA ceiling   achieved   headroom
    internal_for_leaf    2    2^-3    7.1          121.0        100       21.0
                              2^-6   20.0          119.6                  19.6
                              2^-9   56.6          118.2                  18.2
    hook                 1    2^-2    3.0          122.0        100       22.0
    root                 1    2^-4    6.0          121.2        100       21.2
                             2^-10   48.0          118.4                  18.4

18.2 to 22.0 bits. The seven FRI systems run 20.6 to 37.3. So OpenVM2 has the
NARROWEST headroom of any deployed system, and it is the only one for which this
particular floor is the relevant obstruction rather than a bound on a
neighbouring quantity.

That is what one would hope to find and it is worth saying plainly: the newest
protocol extracts more of the provably available room than the older one does.
It also means WHIR has the least left to gain from future improvements to the
proximity-gaps constant -- 18 bits rather than 37.

FINDING 2 -- SMALL m HAS A THIRD BENEFIT, AND IT IS THIS ONE
--------------------------------------------------------------
Iteration 64 found OpenVM2 pinning m = 1 or 2 against a default of 28-50, and
identified the tradeoff: 7-25% more queries bought an 11-20x smaller list, which
helps every round-by-round term. There is a third consequence it did not
identify. The MCA floor scales in L, so a smaller list raises the ceiling the
floor imposes:

    rate    m_default   L_default   ceiling    L(m=2)   ceiling   gain
    2^-3         28.3        81.4     117.6       7.1     121.0   +3.4
    2^-6         50.0       404.0     115.3      20.0     119.6   +4.3
    2^-9         50.0      1142.7     113.8      56.6     118.2   +4.3

Pinning m small buys 3.4-4.3 bits of provable ceiling on top of everything
iteration 64 counted. Stated as an observation, not a claim about intent: there
is no evidence the OpenVM2 team chose m with the MCA floor in mind, and the
round-by-round terms alone justify the choice. But it means the choice is better
motivated than iteration 64 concluded, and it is the direction a designer who
DID have the floor in mind would move.

FINDING 3 -- `2m+1` IS THE RATE-1/4 SPECIAL CASE
--------------------------------------------------
This repo has used L = 2m+1 for the Johnson list size throughout (systems.py,
a_floor_scope.py). soundcalc's pinned-m branch (johnson_bound.py:91-105) uses
(m + 0.5)/sqrt(rho). These are the same formula only at rho = 1/4:

    (m + 0.5)/sqrt(rho)  =  2m + 1   <=>   sqrt(rho) = 1/2

and the general ratio is (2m+1) / [(m+0.5)/sqrt(rho)] = 2*sqrt(rho) = sqrt(4*rho).

    rho     ratio    repo's list is       cost in floor bits
    1/2     1.414    41% too LARGE        conservative by 0.50
    1/4     1.000    exact                0
    1/8     0.707    29% too SMALL        overclaims by 0.50
    1/16    0.500    50% too SMALL        overclaims by 1.00

Across the deployed set this matters in one place. Airbender, Pico and ZisK run
rho = 1/2, where the repo is conservative. RISC Zero runs rho = 1/4, where it is
exact. Miden runs rho = 1/8, where the repo's list is too small and its headroom
is therefore 0.5 bits too generous. SP1 and OpenVM are UDR, list size 1, and
unaffected.

Half a bit on one system out of seven. Small, and worth fixing because the
direction is the bad one: everywhere else the repo's convention errs toward
understating its own claims, and on Miden it does the opposite.

FINDING 4 -- soundcalc CARRIES TWO LIST-SIZE FORMULAS
-------------------------------------------------------
johnson_bound.py:91-105 returns (m + 0.5)/sqrt(rho) when m is pinned, and
1/(2*eta*sqrt(rho)) otherwise -- which with eta = sqrt(rho)/(2m) is m/rho. Those
differ by a factor of about 1/sqrt(rho):

    rho = 1/2,  m = 15:   pinned 21.9    default 30.0
    rho = 1/8,  m = 15:   pinned 43.8    default 120.0

Both are valid upper bounds on the list; the pinned-m expression is the tighter
one, by a factor growing as the rate falls. This is not a bug -- they come from
different theorems, and a code path that has not been told m cannot use the
sharper form. But it does mean a system that declares m gets a materially better
list bound than one that does not, independently of the m value itself, which
compounds the effect measured in Finding 2.
"""

import math

Q_BITS = 124            # BabyBear^4, OpenVM2's field
FRI_HEADROOM_RANGE = (20.6, 37.3)     # a_floor_scope.py, seven FRI systems

# OpenVM2, from openvm2.toml: (circuit, log_blowup, explicit_m, achieved bits)
WHIR_CIRCUITS = [("internal_for_leaf", 3, 2, 100), ("internal_recursive", 3, 2, 100),
                 ("hook", 2, 1, 100), ("root", 4, 1, 100)]
K_FOLD = 4

# deployed JBR systems and their rates, for the convention audit
JBR_RATES = [("Airbender", 0.5), ("Pico", 0.5), ("ZisK", 0.5),
             ("RISC Zero", 0.25), ("Miden", 0.125)]


def list_pinned(rho, m):
    """johnson_bound.py:91-105, explicit_m branch. The tighter bound."""
    return (m + 0.5) / math.sqrt(rho)


def list_default(rho, m):
    """johnson_bound.py:99-105, Johnson branch: 1/(2*eta*sqrt(rho)) = m/rho."""
    return 1.0 / (2 * (math.sqrt(rho) / (2 * m)) * math.sqrt(rho))


def list_repo(m):
    """This repo's convention throughout: 2m + 1."""
    return 2 * m + 1


def convention_ratio(rho):
    """(2m+1) / ((m+0.5)/sqrt(rho)) = 2*sqrt(rho), independent of m."""
    return 2 * math.sqrt(rho)


def mca_ceiling(L, q_bits=Q_BITS):
    """Gao et al.: err >= (L+1)/q, so no proof can exceed log2(q) - log2(L+1)."""
    return q_bits - math.log2(L + 1)


def m_default(rho):
    """soundcalc's derived m for a sub-2^150 field."""
    return math.sqrt(rho) / (2 * max(rho / 20, math.sqrt(rho) / 100))


def circuit_headroom(log_blowup, m, achieved, k=K_FOLD, rounds=3):
    """[(rate, L, ceiling, headroom)] per WHIR round."""
    out = []
    for i in range(rounds):
        rho = 2.0 ** -(log_blowup + i * (k - 1))
        L = list_pinned(rho, m)
        out.append((rho, L, mca_ceiling(L), mca_ceiling(L) - achieved))
    return out


def whir_headroom_range():
    vals = [h for _n, lb, m, a in WHIR_CIRCUITS
            for _r, _L, _c, h in circuit_headroom(lb, m, a)]
    return min(vals), max(vals)


def small_m_gain(rho, m=2):
    """Bits of provable ceiling bought by pinning m instead of taking the default."""
    return mca_ceiling(list_pinned(rho, m)) - mca_ceiling(list_pinned(rho, m_default(rho)))


def convention_error_bits(rho):
    """Bits by which this repo's 2m+1 misstates the floor. Positive = overclaim."""
    return math.log2(1.0 / convention_ratio(rho))


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. WHIR SITS CLOSEST TO ITS OWN PROVED FLOOR")
    print(f"""
  a_floor_scope measured the gap on seven FRI systems. But mutual correlated
  agreement is WHIR's assumption, not FRI's -- that file says so itself. OpenVM2
  is the first WHIR system in reach, and four of its circuits DECLARE m, so the
  floor evaluates with nothing assumed.

      err_MCA >= (L+1)/q   =>   provable bits <= {Q_BITS} - log2(L+1)
""")
    print(f"  {'circuit':<20} {'m':>3} {'rate':>7} {'L':>7} {'ceiling':>9} "
          f"{'achieved':>9} {'headroom':>9}")
    print("  " + "-" * 70)
    for nm, lb, m, ach in WHIR_CIRCUITS:
        for i, (rho, L, c, h) in enumerate(circuit_headroom(lb, m, ach)):
            r = int(round(-math.log2(rho)))
            print(f"  {nm if i == 0 else '':<20} {m if i == 0 else '':>3} "
                  f"{'2^-' + str(r):>7} {L:>7.1f} {c:>9.1f} "
                  f"{ach if i == 0 else '':>9} {h:>9.1f}")
    lo, hi = whir_headroom_range()
    print(f"""
  {lo:.1f} to {hi:.1f} bits, against {FRI_HEADROOM_RANGE[0]}-{FRI_HEADROOM_RANGE[1]} for the seven FRI systems. OpenVM2
  has the NARROWEST headroom of any deployed system, and is the only one where
  this floor is the relevant obstruction rather than a bound on a neighbouring
  quantity.

  The newest protocol extracts more of the provably available room. It also has
  the least left to gain from future improvements to the constant -- {lo:.0f} bits
  rather than {FRI_HEADROOM_RANGE[1]:.0f}.""")

    sec("2. A THIRD BENEFIT OF SMALL m THAT ITERATION 64 MISSED")
    print(f"\n  {'rate':>7} {'m_default':>11} {'L_default':>11} {'ceiling':>9} "
          f"{'L(m=2)':>8} {'ceiling':>9} {'gain':>7}")
    print("  " + "-" * 66)
    for r in (3, 6, 9):
        rho = 2.0 ** -r
        md = m_default(rho)
        print(f"  {'2^-' + str(r):>7} {md:>11.1f} {list_pinned(rho, md):>11.1f} "
              f"{mca_ceiling(list_pinned(rho, md)):>9.1f} {list_pinned(rho, 2):>8.1f} "
              f"{mca_ceiling(list_pinned(rho, 2)):>9.1f} {small_m_gain(rho):>+7.1f}")
    print("""
  Iteration 64 counted two effects of pinning m small: more queries, smaller
  list helping the round-by-round terms. The MCA floor scales in L too, so the
  same choice buys 3.4-4.3 bits of provable ceiling.

  An observation, not a claim about intent -- there is no evidence the team
  chose m with this floor in mind, and the RBR terms alone justify it. But the
  choice is better motivated than iteration 64 concluded.""")

    sec("3. THIS REPO'S `2m+1` IS THE RATE-1/4 SPECIAL CASE")
    print("""
  systems.py and a_floor_scope.py use L = 2m+1. soundcalc's pinned-m branch uses
  (m+0.5)/sqrt(rho). They coincide only at rho = 1/4, and the ratio is
  2*sqrt(rho) -- independent of m:\n""")
    print(f"  {'rho':>7} {'ratio':>8} {'repo list is':>18} {'floor bits':>12}")
    print("  " + "-" * 50)
    for rho in (0.5, 0.25, 0.125, 0.0625):
        rt = convention_ratio(rho)
        desc = ("exact" if abs(rt - 1) < 1e-12
                else f"{abs(rt-1)*100:.0f}% too " + ("LARGE" if rt > 1 else "SMALL"))
        eb = convention_error_bits(rho)
        print(f"  {rho:>7} {rt:>8.3f} {desc:>18} "
              f"{('conservative ' + f'{-eb:.2f}') if eb < 0 else ('overclaims ' + f'{eb:.2f}'):>12}")
    print(f"\n  {'system':<12} {'rho':>7} {'effect on its headroom':>26}")
    print("  " + "-" * 48)
    for nm, rho in JBR_RATES:
        eb = convention_error_bits(rho)
        note = ("exact" if abs(eb) < 1e-12
                else f"{'overstated by' if eb > 0 else 'understated by'} {abs(eb):.2f} bits")
        print(f"  {nm:<12} {rho:>7} {note:>26}")
    print("""
  Half a bit, on one system out of seven. Worth fixing because the direction is
  the bad one: everywhere else this convention errs toward understating the
  repo's own claims, and on Miden it does the opposite.""")

    sec("4. soundcalc CARRIES TWO LIST-SIZE FORMULAS")
    print(f"\n  {'rho':>7} {'m':>5} {'pinned (m+.5)/sqrt':>20} {'default m/rho':>15} {'ratio':>8}")
    print("  " + "-" * 58)
    for rho in (0.5, 0.125):
        for m in (2, 15):
            print(f"  {rho:>7} {m:>5} {list_pinned(rho, m):>20.1f} "
                  f"{list_default(rho, m):>15.1f} {list_default(rho, m)/list_pinned(rho, m):>8.2f}x")
    print("""
  Both are valid upper bounds; the pinned-m form is tighter by roughly
  1/sqrt(rho), and the advantage grows as the rate falls. Not a bug -- they come
  from different theorems, and a path not told m cannot use the sharper one. But
  a system that DECLARES m gets a materially better list bound independently of
  the m value, which compounds Finding 2.""")


if __name__ == "__main__":
    report()
