"""
Closing iteration 63's open gap: all six OpenVM2 circuits, both regimes -- and
a shipping system tuning `m` by hand, which is Theorem 7's tradeoff as a knob.

Iteration 63 reproduced OpenVM2's whir_query figure for `app` and `leaf` (UDR)
and reported plainly that the same model missed the four recursion circuits by
60+ bits. It guessed the cause: "they must run on Johnson yield plus much
heavier grinding (folding PoW 18 bits against app's 5)".

Half right. Johnson yield, yes. The grinding guess was wrong -- the query-phase
grinding is 20 bits for ALL SIX circuits, and the folding PoW that differs feeds
a different term (whir_fold_rbr), not the query term. The actual cause was in
the toml all along:

    internal_for_leaf   explicit_regime = "list"   explicit_m = 2
    internal_recursive  explicit_regime = "list"   explicit_m = 2
    hook                explicit_regime = "list"   explicit_m = 1
    root                explicit_regime = "list"   explicit_m = 1

WHAT THE SOURCE ACTUALLY SAYS
-------------------------------
Two corrections to what this repo had been carrying from recall.

whir.py:597-611 -- the query term is (1 - delta_i)^{t_i} with grinding, where
delta_i is the MINIMUM over all k_i + 1 sub-codes of the iteration. Within an
iteration the rate is constant (whir.py:511-515), so for UDR this collapses to
exactly iteration 63's model. That model is now derived from source rather than
inferred from a fit.

johnson_bound.py:70-89 -- the Johnson proximity parameter is

    delta = 1 - sqrt(rho) - eta

not the `1 - sqrt(rho)(1 + 1/2m)` form this repo uses. The two agree, because
_get_eta_from_m is eta = sqrt(rho)/(2m) (johnson_bound.py:29), so
sqrt(rho) + eta = sqrt(rho)(1 + 1/2m). Same object, and worth recording in the
form the source uses.

Also: eta's default switches on FIELD SIZE. Above 2^150 it is sqrt(rho)/100;
below, max(rho/20, sqrt(rho)/100). OpenVM2 is BabyBear^4 = 2^124, so the second
branch applies; the first matters for Goldilocks^3 (2^192) systems like ZisK.

    RETRACTED IN ITERATION 65. This paragraph originally added "This repo only
    ever had the second branch." That is false -- soundcalc_lean.py:99-103 has
    had both since iteration 47, and ZisK's published figure depends on it: on
    the wrong branch its model value would be 119.7 against a reported 128
    (error -8.3) instead of 127.2 (error -0.8). What iteration 64 actually did
    was write a SECOND copy of the function here and mistake its own novelty for
    a gap in the repo. See definition_guard.py.

ALL SIX CIRCUITS, ONE SCHEDULE
--------------------------------
With m read from the toml, per-round yield s_i * y(rho_i, m_i):

    circuit             regime   m        per-round products      min   +20   pub
    app                 unique   -    80.1  80.3  80.1  80.9     80.1  100.1  100
    leaf                unique   -    80.0  80.3  80.5           80.0  100.0  100
    internal_for_leaf   list     2    80.1  80.3  83.6           80.1  100.1  100
    internal_recursive  list     2    80.1  80.3  83.6           80.1  100.1  100
    hook                list     1    80.1  80.4  82.0           80.1  100.1  100
    root                list     1    80.7  81.6  83.9           80.7  100.7  100

Nineteen rounds across six circuits and two regimes, every one between 80.0 and
83.9, and every circuit's minimum plus its declared 20 bits of query grinding
landing on the published 100. Iteration 63's equal-yield finding was not a
property of the UDR circuits -- it is how the whole system is designed.

THE INTERESTING PART: m = 1 IS A DELIBERATE SACRIFICE
--------------------------------------------------------
soundcalc's default m, at these rates, is 28-50. OpenVM2 pins 1 or 2. That is
not a small deviation, and it goes the "wrong" way for the query phase: smaller
m means larger eta, so a LOWER per-query yield and MORE queries for the same
bits.

The reason is list size. johnson_bound.py:91-105 gives (m + 0.5)/sqrt(rho) when
m is pinned, so:

    rate    m_default   yield cost of m=2    list size gain
    2^-3         28.3           1.25x                11.5x
    2^-6         50.0           1.11x                20.2x
    2^-9         50.0           1.07x                20.2x

They pay 7-25% more queries to shrink the decoding list by 11-20x. Every
round-by-round term -- whir_fold_rbr, whir_ood_rbr, whir_shift_rbr -- scales in
the list size, and the report shows all three sitting at 100-104 bits for these
circuits, i.e. binding or nearly so. Buying list size with queries is the only
move that helps them.

This is exactly the tradeoff Theorem 7 formalises, appearing as an explicit
engineering knob in a shipping system. The repo has been treating `m` as
something soundcalc derives (iteration 47) or that a theorem picks (m_eq). Here
a production team overrides it per circuit, and the override is the difference
between reproducing their numbers and missing by 60 bits.

WHAT THIS DOES NOT CHANGE
---------------------------
Nothing about the ceiling. This is the query phase, and OpenVM2 still reports
100 bits like OpenVM. Iteration 63's scope note stands: WHIR is a proof-size
result. What is new is that the query phase of a second protocol family, in both
proximity regimes, is now reproduced from declared parameters with nothing
fitted.
"""

import math

# (circuit, regime, log_blowup, whir_num_queries, explicit_m, query_pow, published)
# soundcalc/zkvms/openvm2/openvm2.toml and reports/openvm2.md
CIRCUITS = [
    ("app", "unique", 1, [193, 88, 81, 81], None, 20, 100),
    ("leaf", "unique", 2, [118, 84, 81], None, 20, 100),
    ("internal_for_leaf", "list", 3, [68, 30, 20], 2, 20, 100),
    ("internal_recursive", "list", 3, [68, 30, 20], 2, 20, 100),
    ("hook", "list", 2, [193, 42, 24], 1, 20, 100),
    ("root", "list", 4, [57, 28, 19], 1, 20, 100),
]

K_FOLD = 4          # inverse rate gains k-1 = 3 bits per round
FIELD_ETA_SWITCH = 2 ** 150   # johnson_bound.py:84


def eta_default(rho, field_size=2 ** 124):
    """johnson_bound.py:82-87. Duplicates soundcalc_lean.eta_soundcalc, which has
    had both branches since iteration 47; definition_guard.py pins them together."""
    return (math.sqrt(rho) / 100 if field_size > FIELD_ETA_SWITCH
            else max(rho / 20, math.sqrt(rho) / 100))


def eta_from_m(rho, m):
    """johnson_bound.py:22-29. eta = sqrt(rho)/(2m)."""
    return math.sqrt(rho) / (2 * m)


def m_default(rho, field_size=2 ** 124):
    """The m implied by the default eta."""
    return math.sqrt(rho) / (2 * eta_default(rho, field_size))


def delta_johnson(rho, m=None, field_size=2 ** 124):
    """johnson_bound.py:70-89. delta = 1 - sqrt(rho) - eta."""
    eta = eta_from_m(rho, m) if m else eta_default(rho, field_size)
    return 1 - math.sqrt(rho) - eta


def list_size(rho, m):
    """johnson_bound.py:91-105, pinned-m branch: (m + 0.5)/sqrt(rho)."""
    return (m + 0.5) / math.sqrt(rho)


def per_query_yield(log_inv_rate, regime, m=None):
    """-log2(1 - delta). UDR: delta = (1-rho)/2. JBR: Johnson."""
    rho = 2.0 ** -log_inv_rate
    d = (1 - rho) / 2 if regime == "unique" else delta_johnson(rho, m)
    return -math.log2(1 - d)


def round_products(log_blowup, queries, regime, m=None, k=K_FOLD):
    """s_i * y(rho_i) for each WHIR round, rho improving by k-1 bits per round."""
    return [s * per_query_yield(log_blowup + i * (k - 1), regime, m)
            for i, s in enumerate(queries)]


def whir_query_bits(log_blowup, queries, regime, m, grinding, k=K_FOLD):
    """Weakest round plus declared query-phase grinding."""
    return min(round_products(log_blowup, queries, regime, m, k)) + grinding


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. TWO CORRECTIONS TO WHAT THIS REPO CARRIED FROM RECALL")
    rho = 0.125
    print(f"""
  whir.py:597-611  the query term is (1 - delta_i)^t_i with grinding, delta_i
                   the MINIMUM over the iteration's k_i + 1 sub-codes. The rate
                   is constant within an iteration, so for UDR this collapses to
                   iteration 63's model -- now derived, not fitted.

  johnson_bound.py:70-89   delta = 1 - sqrt(rho) - eta, NOT 1 - sqrt(rho)(1+1/2m).
                   The two agree because eta = sqrt(rho)/(2m):

                       rho = {rho}: sqrt = {math.sqrt(rho):.5f}
                       sqrt + eta(m=2)      = {math.sqrt(rho)+eta_from_m(rho,2):.5f}
                       sqrt * (1 + 1/(2*2)) = {math.sqrt(rho)*1.25:.5f}

  johnson_bound.py:84   eta's default BRANCHES ON FIELD SIZE -- sqrt(rho)/100
                   above 2^150, max(rho/20, sqrt(rho)/100) below. This repo only
                   RETRACTED it 65: the repo HAS had both since it 47
                   (soundcalc_lean.py:99). OpenVM2 is 2^124 so the second
                   applies; Goldilocks^3 systems (2^192) take the first:

                       eta at rho=1/8, F=2^124: {eta_default(rho, 2**124):.6f}  (m = {m_default(rho, 2**124):.1f})
                       eta at rho=1/8, F=2^192: {eta_default(rho, 2**192):.6f}  (m = {m_default(rho, 2**192):.1f})""")

    sec("2. ALL SIX CIRCUITS, BOTH REGIMES, ONE EQUAL-YIELD SCHEDULE")
    print(f"\n  {'circuit':<20} {'regime':>7} {'m':>3} {'per-round s_i * y_i':>28} "
          f"{'min':>6} {'+grind':>7} {'pub':>5} {'d':>5}")
    print("  " + "-" * 84)
    for nm, reg, lb, q, m, g, pub in CIRCUITS:
        ps = round_products(lb, q, reg, m)
        mod = whir_query_bits(lb, q, reg, m, g)
        print(f"  {nm:<20} {reg:>7} {str(m or '-'):>3} "
              f"{'  '.join(f'{v:.1f}' for v in ps):>28} {min(ps):>6.1f} "
              f"{mod:>7.1f} {pub:>5} {mod-pub:>+5.1f}")
    allp = [v for nm, reg, lb, q, m, g, pub in CIRCUITS
            for v in round_products(lb, q, reg, m)]
    print(f"""
  {len(allp)} rounds, six circuits, two regimes. Every product in [{min(allp):.1f}, {max(allp):.1f}], and
  every circuit's minimum plus its declared 20 bits of query grinding landing on
  the published 100. Iteration 63's equal-yield finding was not a property of
  the UDR circuits -- it is how the whole system is designed.

  Iteration 63 also guessed the recursion circuits differed by "much heavier
  grinding". They do not: query-phase grinding is 20 bits for all six. The
  folding PoW that does differ (18 vs 5) feeds whir_fold_rbr, a different term.""")

    sec("3. m = 1 IS A DELIBERATE SACRIFICE, AND IT IS THEOREM 7's TRADEOFF")
    print("""
  soundcalc's default m at these rates is 28-50. OpenVM2 pins 1 or 2 -- which
  LOWERS per-query yield, costing queries. The reason is list size:\n""")
    print(f"  {'rate':>7} {'m_default':>11} {'yield cost of m=2':>19} {'list size gain':>16}")
    print("  " + "-" * 58)
    for r in (3, 6, 9):
        rho_r, md = 2.0 ** -r, m_default(2.0 ** -r)
        yc = per_query_yield(r, "list", md) / per_query_yield(r, "list", 2)
        lg = list_size(rho_r, md) / list_size(rho_r, 2)
        print(f"  {'2^-' + str(r):>7} {md:>11.1f} {yc:>18.2f}x {lg:>15.1f}x")
    print("""
  They pay 7-25% more queries to shrink the decoding list by 11-20x. Every
  round-by-round term -- whir_fold_rbr, whir_ood_rbr, whir_shift_rbr -- scales
  in the list size, and the report has all three at 100-104 bits for these
  circuits, binding or nearly so. Buying list size with queries is the only move
  that helps.

  This is the tradeoff Theorem 7 formalises, showing up as an engineering knob.
  The repo has treated m as something soundcalc derives (iteration 47) or a
  theorem picks (m_eq). Here a production team overrides it per circuit, and the
  override is the difference between reproducing their figures and missing by
  60 bits.""")


if __name__ == "__main__":
    report()
