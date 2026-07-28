"""
Obstacle 4, priced: a 58.5% query cut is a 40-50% proof-size cut, not 58.5%.

Iteration 43 priced the one open capacity route -- Yuan-Zhu's capacity-radius
correlated agreement, available to Ligero/Brakedown-style systems because they
have no x -> x^2 folding obstruction -- and found it worth a 47% to 67%
reduction in QUERY COUNT. It then listed four obstacles standing between that
and a deployment, the fourth being:

    "QUERIES ARE NOT PROOF SIZE for these systems. Ligero/Brakedown proofs are
     dominated by O(sqrt(n)) column openings, so a 60% query cut is not a 60%
     proof-size cut. Pricing that needs a proof-size model this repo lacks."

This file builds that model. The answer is that the query cut translates
SUB-LINEARLY, because the dominant term scales as sqrt(t) rather than t.

THE MODEL
---------
A Ligero-style prover arranges an N-element witness as m rows of k = N/m, and
Reed-Solomon-encodes each row to length n = k/R. The proof carries

    one combined row            n elements
    t column openings           m elements each
    t Merkle authentication paths, depth log2(n)

so with F bytes per field element and H bytes per hash,

    size(m) = (N/(mR))*F  +  t*m*F  +  t*log2(N/(mR))*H

The first two terms trade against each other in m. Ignoring the log term's
m-dependence, d/dm = 0 gives

    m* = sqrt(N/(tR))      and      size* = 2F*sqrt(N t / R)  +  t*log2(n)*H

THE POINT: THE FIELD TERM SCALES AS sqrt(t)
---------------------------------------------
Because m* itself moves with t, the two field terms are each F*sqrt(Nt/R), so
the field part of the proof grows as sqrt(t), not t. Only the Merkle part is
linear in t. Cutting queries by a factor alpha therefore scales

    field part   by  sqrt(alpha)
    Merkle part  by  alpha

At iteration 43's rate-1/4 figure (58.5% cut, alpha = 0.415): sqrt(alpha) =
0.644 and alpha = 0.415, and the blend lands at a 42.7% size reduction for
N = 2^20.

    t     m*     n_enc   size KiB   field KiB   Merkle KiB
    200  150.6   27842      318.7       226.5         92.3
    150  173.0   24238      264.3       196.1         68.3
    120  192.7   21769      229.4       175.4         54.0
    100  210.8   19893      204.7       160.1         44.6
     83  230.7   18179      182.5       145.8         36.7
     60  270.6   15500      150.1       124.0         26.1

Note m* RISES as t falls -- the optimiser rebalances toward fewer, taller
columns -- which is why the field term does not fall linearly.

SENSITIVITY
-----------
Merkle deduplication makes it WORSE, not better. merkle_dedup.py measures real
path cost at 33-52% below t*depth; that shrinks the only term which scales
linearly in t, leaving the sqrt-scaling field term more dominant:

    no dedup     318.7 -> 182.5 KiB    42.7% reduction
    dedup -33%   288.3 -> 170.4 KiB    40.9%
    dedup -52%   270.7 -> 163.4 KiB    39.6%

And larger witnesses make it worse too, for the same reason -- the field term
grows with N while the Merkle term grows only logarithmically:

    N = 2^16  50.1%      N = 2^20  42.7%
    N = 2^18  46.3%      N = 2^22  40.0%

So the honest range is a 40% to 50% proof-size reduction across realistic
witness sizes, against the 58.5% the query count alone suggests.

HONEST LIMITS
-------------
1. Ligero carries SEVERAL combined rows (row-check, linear check, quadratic
   check), not one. Each adds n*F, which shifts the optimum toward larger m and
   makes the field term more dominant still -- so this file's figures are an
   UPPER bound on the achievable reduction.
2. The closed form m* = sqrt(N/(tR)) drops the log term's m-dependence. Checked
   against the numeric argmin: they differ by 2.3% to 4.0%, and every figure
   above uses the numeric one.
3. F = 4 bytes and H = 32 bytes. Iteration 43 noted Yuan-Zhu needs an alphabet
   of q = Theta(n); at these parameters n_enc is 2^14 to 2^15, so a 4-byte
   element covers it comfortably -- the alphabet requirement does not force a
   larger F here, which is worth recording because iteration 43 flagged it as an
   open cost.
4. This prices SIZE only. Encoding cost, prover time and the composition
   question from iteration 43 obstacle 1 are untouched.
"""

import math

F_BYTES = 4
H_BYTES = 32


def proof_size(N, R, t, m, dedup=1.0, n_rows=1):
    """Bytes: n_rows combined rows + t columns + t Merkle paths."""
    n = N / (m * R)
    return (n_rows * n * F_BYTES
            + t * m * F_BYTES
            + dedup * t * math.log2(max(n, 2)) * H_BYTES)


def best_m_numeric(N, R, t, dedup=1.0, n_rows=1, steps=4000):
    """argmin over m of the proof size. Geometric sweep."""
    lo, hi = 1.0, float(N)
    best = (float("inf"), None)
    for i in range(1, steps):
        m = lo * (hi / lo) ** (i / float(steps))
        s = proof_size(N, R, t, m, dedup, n_rows)
        if s < best[0]:
            best = (s, m)
    return best


def m_star_closed(N, R, t):
    """sqrt(N/(tR)) -- drops the log term's m-dependence."""
    return math.sqrt(N / (t * R))


def size_reduction(N, R, t0, t1, dedup=1.0, n_rows=1):
    s0, _ = best_m_numeric(N, R, t0, dedup, n_rows)
    s1, _ = best_m_numeric(N, R, t1, dedup, n_rows)
    return 1 - s1 / s0


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    N, R = 2 ** 20, 0.25

    sec("1. THE FIELD TERM SCALES AS sqrt(t), WHICH IS THE WHOLE POINT")
    print(f"  N = 2^20 witness, rate 1/4, {F_BYTES}B elements, {H_BYTES}B hashes\n")
    print(f"  {'t':>6} {'m*':>9} {'n_enc':>10} {'size KiB':>10} "
          f"{'field KiB':>10} {'Merkle KiB':>11}")
    print("  " + "-" * 60)
    for t in (200, 150, 120, 100, 83, 60):
        s, m = best_m_numeric(N, R, t)
        n = N / (m * R)
        fld = (n * F_BYTES + t * m * F_BYTES) / 1024
        mk = t * math.log2(n) * H_BYTES / 1024
        print(f"  {t:>6} {m:>9.1f} {n:>10.0f} {s/1024:>10.1f} {fld:>10.1f} "
              f"{mk:>11.1f}")
    print("""
  m* RISES as t falls -- the optimiser rebalances toward fewer, taller columns.
  That is why the field part goes as sqrt(t): both field terms equal
  F*sqrt(N t/R) at the optimum, so they move together with sqrt(t).""")

    sec("2. CLOSED FORM vs NUMERIC ARGMIN (the log term is dropped, so check it)")
    print(f"  {'t':>6} {'m* closed':>11} {'m* numeric':>12} {'difference':>12}")
    print("  " + "-" * 44)
    for t in (200, 100, 60):
        cf = m_star_closed(N, R, t)
        _, num = best_m_numeric(N, R, t)
        print(f"  {t:>6} {cf:>11.1f} {num:>12.1f} {abs(num/cf - 1):>11.1%}")
    print("""
  2.3% to 4.0% apart. Every figure in this file uses the numeric argmin.""")

    sec("3. CONVERTING ITERATION 43's QUERY CUT INTO BYTES")
    alpha = 0.415
    s0, _ = best_m_numeric(N, R, 200)
    s1, _ = best_m_numeric(N, R, 83)
    print(f"""
  Iteration 43, rate 1/4: 58.5% fewer queries (alpha = {alpha:.3f}).

      field part scales by sqrt(alpha) = {math.sqrt(alpha):.3f}
      Merkle part scales by      alpha = {alpha:.3f}

      {s0/1024:.1f} KiB  ->  {s1/1024:.1f} KiB   =   {1 - s1/s0:.1%} smaller

  not the 58.5% the query count alone suggests.""")

    sec("4. SENSITIVITY -- BOTH KNOBS MAKE IT WORSE")
    print(f"  {'Merkle model':<14} {'before KiB':>11} {'after KiB':>10} "
          f"{'reduction':>11}")
    print("  " + "-" * 50)
    for d, lbl in ((1.0, "no dedup"), (0.67, "dedup -33%"), (0.48, "dedup -52%")):
        a, _ = best_m_numeric(N, R, 200, d)
        b, _ = best_m_numeric(N, R, 83, d)
        print(f"  {lbl:<14} {a/1024:>11.1f} {b/1024:>10.1f} {1-b/a:>10.1%}")
    print(f"\n  {'witness N':<14} {'reduction':>11}")
    print("  " + "-" * 28)
    for lg in (16, 18, 20, 22):
        print(f"  {'2^%d' % lg:<14} {size_reduction(2**lg, R, 200, 83):>10.1%}")
    print("""
  Deduplication shrinks the only term that scales linearly in t, so it leaves
  the sqrt-scaling field term more dominant and the reduction SMALLER. Larger
  witnesses do the same, for the same reason. And Ligero's several combined rows
  (not modelled) push further in that direction -- so 40-50% is an upper bound,
  not a midpoint.""")


if __name__ == "__main__":
    report()
