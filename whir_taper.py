"""
Why WHIR's proofs are smaller, quantified -- and a correction to my own summary
of iteration 62.

OpenVM and OpenVM2 are the same team, the same field (BabyBear^4), the same
reported security (100 bits), and different proof systems: DEEP-ALI + FRI
against SWIRL + WHIR. That is as close to a controlled experiment as this field
offers, and it is the most direct evidence available on what the newer
protocols actually buy.

FIRST, A CORRECTION
--------------------
Closing iteration 62 I wrote that SWIRL+WHIR "gets OpenVM2 to 270 KiB against
OpenVM's 7,687 -- a 28x reduction at the same 100 bits". The 28x is arithmetic
on real published numbers, but it compares different pipeline ROLES. Per
iteration 61, each system's headline figure is its LAST circuit -- and the two
pipelines are not the same length:

    OpenVM    app -> leaf -> internal                                  (3)
    OpenVM2   app -> leaf -> internal_for_leaf -> internal_recursive
                                              -> hook -> root         (6)

Comparing like with like:

    role                       OpenVM      OpenVM2      ratio
    app                        234635        26175       9.0x
    leaf                       234635        15509      15.1x
    internal                     7687         2393       3.2x
    headline (last circuit)      7687          270      28.5x

So the 28.5x factors as

    3.2x   WHIR vs FRI at equal recursion depth
    8.9x   OpenVM2 running three more recursion stages
    -----
    28.5x  (3.2 * 8.9 = 28.5, and 7687/270 = 28.5)

Most of the headline gain is recursion depth, which OpenVM could also do. The
protocol change is worth 3.2x at matched depth, not 28x. That is still a large
number and it is the honest one.

THE MECHANISM: WHIR'S RATE IMPROVES EVERY ROUND, SO ITS QUERIES TAPER
-----------------------------------------------------------------------
FRI folds at a constant rate. Its query count is therefore the same in every
round -- OpenVM's app circuit opens 193 queries in each of 24 rounds. WHIR does
not (soundcalc/pcs/whir.py:371-373):

    for k in self.folding_factors:
        self.log_degrees.append(self.log_degrees[-1] - k)
        self.log_inv_rates.append(self.log_inv_rates[-1] + (k - 1))

The inverse rate GROWS by k-1 bits per round. A better rate means each query is
worth more, so fewer are needed. OpenVM2's app declares
whir_num_queries = [193, 88, 81, 81] -- a taper FRI cannot express.

    query openings, app circuit
        FRI   193 x 24 rounds  = 4632
        WHIR  193+88+81+81     =  443      10.5x fewer
        proof size                          9.0x smaller

The 10.5x reduction in openings and the 9.0x reduction in proof size agree to
about 15%, which is the non-query part of the proof.

THE TAPER IS EXACTLY AN EQUAL-YIELD SCHEDULE
----------------------------------------------
If the counts are chosen so every round contributes the same security, then
s_i * y(rho_i) should be constant, with y this repo's UDR per-query yield
-log2((1+rho)/2). Taking rho_i from log_blowup and k = 4, with nothing fitted:

    app   rates [1, 4, 7, 10]    80.1  80.3  80.1  80.9     spread 0.80 bits
    leaf  rates [2, 5, 8]        80.0  80.3  80.5           spread 0.53 bits

Seven rounds across two circuits, all within 0.8 bits of 80. The taper is an
equal-yield schedule, and this repo's own yield formula reproduces it.

Adding each circuit's declared query-phase grinding closes it to soundcalc's
published figure exactly:

    circuit   min_i(s_i * y_i)   + query_phase_pow   published whir_query
    app                  80.1          + 20 = 100.1                  100
    leaf                 80.0          + 20 = 100.0                  100

WHERE THIS MODEL DOES NOT REACH
---------------------------------
Only app and leaf. The four recursion circuits are reported in JBR, not UDR,
and the same arithmetic gives 56.4 / 29.3 / 19.9 for internal_for_leaf against
a published whir_query of 100.

The gap is not a tuning issue. UDR yield is bounded above by 1 bit per query
(y -> 1 as rho -> 0), so 20 queries can buy at most 20 bits in that regime, and
no choice of rate closes a 100-bit target. Those circuits must be carried by the
Johnson-regime yield -- where y = -log2(sqrt(rho)(1+1/2m)) exceeds 1 -- plus
their much heavier grinding (folding PoW 18 bits against app's 5). Reproducing
them needs the JBR path and the derived m, and is left open rather than forced:
a model that fits two circuits and is honestly reported as not fitting four is
worth more than one tuned until everything matches.

WHAT THIS SAYS FOR THE PROGRAMME
----------------------------------
The repo's ceiling equation is about the COMMIT phase. WHIR does not touch it --
the ceiling is still E - a*nu - log2 C + g_commit, and OpenVM2 still reports 100
bits, the same as OpenVM. What WHIR changes is the QUERY phase's cost per bit,
by improving the rate as it folds instead of holding it fixed.

That matters for the query-phase bound this repo keeps hitting. Finding 2 says
the largest deployed query term caps the field at 64 PQ bits, and that the query
phase binds for every verified system. WHIR does not raise the query term -- it
buys the same 100 bits with 10x fewer openings. So it is a proof-SIZE result,
not a soundness one, and the PQ ceiling is untouched. Consistent with
EFFICIENCY.md section 0: query count governs proof size, not security headroom.
"""

import math

# (circuit, log_blowup, whir_num_queries, query_phase_pow, published whir_query)
# from soundcalc/zkvms/openvm2/openvm2.toml and reports/openvm2.md
UDR_CIRCUITS = [("app", 1, [193, 88, 81, 81], 20, 100),
                ("leaf", 2, [118, 84, 81], 20, 100)]
JBR_CIRCUITS = [("internal_for_leaf", 3, [68, 30, 20], 20, 100),
                ("internal_recursive", 3, [68, 30, 20], 20, 100),
                ("hook", 2, [193, 42, 24], 20, 100),
                ("root", 4, [57, 28, 19], 20, 100)]

K_FOLD = 4   # WHIR folding factor 2^k; inverse rate gains k-1 bits per round

# per-role proof sizes, KiB (reports/openvm.md, reports/openvm2.md)
ROLES = [("app", 234635, 26175), ("leaf", 234635, 15509),
         ("internal", 7687, 2393), ("headline (last)", 7687, 270)]

FRI_APP_QUERIES, FRI_APP_ROUNDS = 193, 24


def yield_udr(log_inv_rate):
    """This repo's UDR per-query yield: -log2((1+rho)/2). Bounded above by 1."""
    return -math.log2((1 + 2.0 ** -log_inv_rate) / 2)


def inv_rates(log_blowup, n_rounds, k=K_FOLD):
    """whir.py:373 -- the inverse rate gains k-1 bits every round."""
    return [log_blowup + i * (k - 1) for i in range(n_rounds)]


def round_yields(log_blowup, queries, k=K_FOLD):
    """s_i * y(rho_i) for each WHIR round."""
    return [s * yield_udr(r)
            for s, r in zip(queries, inv_rates(log_blowup, len(queries), k))]


def whir_query_bits(log_blowup, queries, grinding, k=K_FOLD):
    """Weakest round plus declared query-phase grinding."""
    return min(round_yields(log_blowup, queries, k)) + grinding


def taper_spread(log_blowup, queries, k=K_FOLD):
    """Max-min of the per-round yields. Zero would be a perfect equal-yield schedule."""
    ys = round_yields(log_blowup, queries, k)
    return max(ys) - min(ys)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. CORRECTING THE 28x: MOST OF IT IS RECURSION DEPTH, NOT THE PROTOCOL")
    print("""
  Closing iteration 62 I called SWIRL+WHIR "a 28x reduction at the same 100
  bits". The arithmetic is right and the comparison is not like-for-like: each
  headline figure is the LAST circuit (iteration 61), and the pipelines differ
  in length -- OpenVM has 3 stages, OpenVM2 has 6.\n""")
    print(f"  {'role':<18} {'OpenVM':>9} {'OpenVM2':>9} {'ratio':>8}")
    print("  " + "-" * 48)
    for nm, a, b in ROLES:
        print(f"  {nm:<18} {a:>9} {b:>9} {a/b:>7.1f}x")
    print(f"""
  So 28.5x factors as {7687/2393:.1f}x (WHIR vs FRI at equal depth) times {2393/270:.1f}x (three
  extra recursion stages OpenVM simply does not run). The protocol change is
  worth {7687/2393:.1f}x at matched depth. Still large; also honest.""")

    sec("2. THE MECHANISM: RATE IMPROVES EACH ROUND, SO QUERIES TAPER")
    n_whir = sum(UDR_CIRCUITS[0][2])
    n_fri = FRI_APP_QUERIES * FRI_APP_ROUNDS
    print(f"""
  whir.py:373 --  log_inv_rates.append(log_inv_rates[-1] + (k - 1))

  The inverse rate GROWS every round, so each query is worth more and fewer are
  needed. FRI holds the rate fixed and must open the same count every round.

      FRI  app   {FRI_APP_QUERIES} x {FRI_APP_ROUNDS} rounds = {n_fri}
      WHIR app   {'+'.join(str(q) for q in UDR_CIRCUITS[0][2])}     =  {n_whir}      {n_fri/n_whir:.1f}x fewer
      proof size {ROLES[0][1]} -> {ROLES[0][2]}         {ROLES[0][1]/ROLES[0][2]:.1f}x smaller

  The {n_fri/n_whir:.1f}x drop in openings and the {ROLES[0][1]/ROLES[0][2]:.1f}x drop in proof size agree to about
  15%, which is the part of the proof that is not query openings.""")

    sec("3. THE TAPER IS AN EQUAL-YIELD SCHEDULE, AND THE REPO'S FORMULA FINDS IT")
    print(f"\n  {'circuit':<8} {'inv rates':>16} {'per-round s_i * y_i':>30} {'spread':>8}")
    print("  " + "-" * 66)
    for nm, lb, q, g, pub in UDR_CIRCUITS:
        ys = round_yields(lb, q)
        print(f"  {nm:<8} {str(inv_rates(lb, len(q))):>16} "
              f"{'  '.join(f'{v:.1f}' for v in ys):>30} {taper_spread(lb, q):>7.2f}")
    print(f"""
  Seven rounds across two circuits, every one within 0.8 bits of 80. Nothing is
  fitted: rho comes from log_blowup, k = {K_FOLD}, y is this repo's UDR yield.

  Adding the declared query-phase grinding reproduces soundcalc exactly:\n""")
    print(f"  {'circuit':<8} {'min_i':>8} {'grind':>7} {'model':>8} {'published':>11} {'d':>6}")
    print("  " + "-" * 52)
    for nm, lb, q, g, pub in UDR_CIRCUITS:
        m = whir_query_bits(lb, q, g)
        print(f"  {nm:<8} {min(round_yields(lb, q)):>8.1f} {g:>7} {m:>8.1f} "
              f"{pub:>11} {m-pub:>+6.1f}")

    sec("4. WHERE THE MODEL DOES NOT REACH, AND WHY NOT")
    print(f"\n  {'circuit':<20} {'per-round s_i * y_i':>26} {'model':>8} {'published':>11}")
    print("  " + "-" * 68)
    for nm, lb, q, g, pub in JBR_CIRCUITS:
        ys = round_yields(lb, q)
        print(f"  {nm:<20} {'  '.join(f'{v:.1f}' for v in ys):>26} "
              f"{whir_query_bits(lb, q, g):>8.1f} {pub:>11}")
    print("""
  These four are reported in JBR, not UDR, and the UDR model misses badly. That
  is not a tuning gap: UDR yield is bounded above by 1 bit per query, so 20
  queries buy at most 20 bits at ANY rate, and no schedule reaches 100. They
  must run on Johnson-regime yield -- where -log2(sqrt(rho)(1+1/2m)) exceeds 1 --
  plus much heavier grinding (folding PoW 18 bits against app's 5).

  Left open rather than forced. A model that fits two circuits and says plainly
  that it does not fit four is worth more than one tuned until everything
  matches.""")

    sec("5. WHAT IT MEANS FOR THIS REPO'S CEILING")
    print("""
  The ceiling equation is about the COMMIT phase, and WHIR does not touch it.
  OpenVM2 reports the same 100 bits as OpenVM. What WHIR changes is the QUERY
  phase's cost per bit, by improving the rate as it folds instead of holding it
  fixed.

  So this is a proof-SIZE result, not a soundness one. Finding 2's PQ ceiling --
  the query term caps the field at 64 PQ bits -- is untouched: WHIR buys the
  same 100 bits with 10x fewer openings, it does not buy more bits. That is
  exactly EFFICIENCY.md section 0's point, now with a second protocol family
  confirming it.""")


if __name__ == "__main__":
    report()
