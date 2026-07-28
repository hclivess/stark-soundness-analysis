"""
Capacity is not dead -- it moved to folded RS. And it buys almost nothing.

README correction 1 says the up-to-capacity conjecture "is not open -- it was
disproved in late 2025", and frontier.py treats the capacity route as closed.
That is right about PLAIN Reed-Solomon and wrong as a statement about capacity
proximity gaps in general. A 2026 literature this repo had not touched
establishes capacity-radius gaps for OTHER code families, with proofs.

This file reads the primary source, works out what capacity would actually buy a
deployed system, and finds that the answer is roughly nothing -- for a reason
that is not visible from the radius alone.

THE 2026 PICTURE (arXiv, all fetched and read)
-----------------------------------------------
  2604.09724  Kambire, "Proximity Gaps Conjecture Fails Near Capacity over
              Prime Fields" -- sharpens the disproof: gaps fail at radii
              O(1/log n) BELOW capacity, not merely at it. Prime fields are
              exactly what every deployed zkVM uses.
  2601.10047  Jeronimo, Liu, Rajpal, "Optimal Proximity Gap for Folded
              Reed-Solomon Codes via Subspace Designs" -- capacity-radius gaps
              for FRS. PROVED, not conjectured.
  2607.08516  Goyal, Guruswami, Sun, Wootters, "Locality of Curve-Decoding and
              Improved Proximity Gaps" (2026-07-09) -- extends near-optimal gaps
              to random linear codes, random-evaluation-point RS, and Gallager
              LDPC, matching the subspace-design parameters.
  2605.07595  Yuan, Zhu, syndrome-space route to the same for random linear and
              random RS codes.

So the correct statement is not "capacity was disproved" but:

    capacity gaps FAIL for plain Reed-Solomon over prime fields,
    and HOLD for folded RS, subspace-design codes, and random-evaluation RS.

The route is open. It just requires changing the code.

THE THEOREM, VERBATIM (2601.10047, Theorem 5.12)
-------------------------------------------------
    Let C = FRS^m_{n,k} be an m-folded Reed-Solomon code of block length n and
    rate R := k/(nm). Fix eta in (0, 1-R) and set the target radius
    delta* := 1 - R - eta. Assume that m >= c/eta^2 and that q is at least a
    fixed polynomial in n and 1/eta, where c > 0 is a sufficiently large
    absolute constant. Then there exists an absolute constant C1 > 0 such that
    C has a line proximity gap with parameters

        eps <= (C1/q) * ( n/eta + 1/eta^3 ),      kappa = 1.

FINDING 1 -- THE CEILING EQUATION SURVIVES CAPACITY INTACT
-----------------------------------------------------------
The error is (C1/q)(n/eta + 1/eta^3). The n-term dominates whenever
eta > 1/sqrt(n), which every practical eta satisfies by orders of magnitude
(1/sqrt(n) = 2^-11 at n = 2^22). So

    eps_commit  =  (C1/eta) * n / |F|      ->    a = 1,  log2 C = log2(C1/eta)

The exponent a is UNCHANGED at capacity. This repo's central equation

    ceiling = E - a*nu - log2 C + g_commit

holds verbatim, with a = 1 and the constant now carrying a log2(1/eta) penalty.
Capacity does NOT raise the ceiling -- it LOWERS it slightly, by log2(1/eta).
Everything capacity buys is in the query phase, through the radius.

FINDING 2 -- THE RADIUS DOUBLES THE YIELD, AND THE FOLDING TAKES IT BACK
-------------------------------------------------------------------------
Per-query yield goes from Johnson's -log2(sqrt(rho)) to -log2(rho + eta): at
rho = 1/4 that is 1.00 -> up to 2.00 bits per query as eta -> 0, so up to half
the queries. That is the number the radius suggests, and it is misleading.

The theorem also requires m >= c/eta^2, and an m-folded symbol IS m field
elements. Each query returns m elements instead of one. So approaching capacity
costs quadratically in payload what it earns logarithmically in yield, and the
product has an interior optimum that is barely better than Johnson:

    proof bytes ~ s * (m * elem_bytes + depth * hash_bytes),  s = k / yield

Section 3 optimises it. At c = 1, 4-byte elements, depth 22, 32-byte hashes,
the best case is a 0.5% to 6% proof-size REDUCTION -- against the ~50% the
doubled yield implies. And c is specified in the theorem only as "a sufficiently
large absolute constant"; at c >= 2 the optimum is a net LOSS.

HONEST LIMITS
-------------
1. c and C1 are unspecified constants. Section 4 gives the sensitivity, which is
   the only defensible way to report a result that depends on them.
2. The Merkle model here is s * depth paths, undeduplicated. merkle_dedup.py
   shows real path cost is 33-52% lower, which makes the FIELD bytes a larger
   share -- so deduplication makes folding look WORSE, not better. The figures
   below are therefore generous to capacity.
3. Folding changes prover structure (the FFT is over folded cosets) and leaf
   hashing cost. Not modelled; the comparison is proof size only.
4. Theorem 5.12 is a LINE proximity gap. Deployed FRI needs the affine-subspace
   or correlated-agreement form. The paper's Theorem 6.2 extends it; this file
   assumes the extension carries the same parameters, which is the direction the
   paper claims but which I did not verify line by line.
"""

import math

ELEM_BYTES = 4          # a 31-bit field element
HASH_BYTES = 32
DEPTH = 22


def yield_johnson(rho):
    """Johnson radius 1 - sqrt(rho): a query passes with probability sqrt(rho)."""
    return -math.log2(math.sqrt(rho))


def yield_capacity(rho, eta):
    """Capacity radius 1 - rho - eta: a query passes with probability rho + eta."""
    return -math.log2(rho + eta)


def folding_required(eta, c=1.0):
    """Theorem 5.12: m >= c/eta^2, and m >= 2 by definition of folding."""
    return max(2.0, c / (eta * eta))


def eta_ceiling(rho):
    """Above this, the capacity radius is no better than Johnson's."""
    return math.sqrt(rho) - rho


def bytes_ratio(rho, eta, c=1.0, depth=DEPTH):
    """Proof bytes at capacity, relative to Johnson at the same security."""
    m = folding_required(eta, c)
    q_ratio = yield_johnson(rho) / yield_capacity(rho, eta)
    per_q_cap = m * ELEM_BYTES + depth * HASH_BYTES
    per_q_john = 1 * ELEM_BYTES + depth * HASH_BYTES
    return q_ratio * per_q_cap / per_q_john


def best_eta(rho, c=1.0, steps=4000):
    """Minimise proof size over the admissible slack."""
    hi = eta_ceiling(rho)
    best = (float("inf"), None)
    for i in range(1, steps):
        eta = hi * i / steps
        r = bytes_ratio(rho, eta, c)
        if r < best[0]:
            best = (r, eta)
    return best


def commit_constant_penalty(eta, C1=1.0):
    """log2 C = log2(C1/eta): the ceiling drops by this as eta shrinks."""
    return math.log2(C1 / eta)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. AT CAPACITY THE EXPONENT IS STILL a = 1")
    print(f"  eps = (C1/q)(n/eta + 1/eta^3). Which term dominates?\n")
    print(f"  {'n':>10} {'1/sqrt(n)':>11} {'n/eta at eta=.15':>18} "
          f"{'1/eta^3':>10} {'n-term dominates':>18}")
    print("  " + "-" * 72)
    for n in (2 ** 16, 2 ** 20, 2 ** 24):
        eta = 0.15
        a_, b_ = n / eta, 1 / eta ** 3
        print(f"  {n:>10} {1/math.sqrt(n):>11.5f} {a_:>18.3g} {b_:>10.1f} "
              f"{'yes' if a_ > b_ else 'no':>18}")
    print("""
  The n-term dominates by four to seven orders of magnitude, so the bound is
  (C1/eta) * n / |F| and a = 1 exactly as in the Johnson-regime bound this repo
  already models. The ceiling equation is unchanged in form and in exponent.
  The only difference is log2 C, which now carries a log2(1/eta) penalty --
  so capacity slightly LOWERS the ceiling rather than raising it.""")
    print(f"\n  {'eta':>8} {'log2 C penalty':>16} {'ceiling change':>16}")
    print("  " + "-" * 42)
    for eta in (0.30, 0.20, 0.15, 0.10, 0.05):
        p = commit_constant_penalty(eta)
        print(f"  {eta:>8.2f} {p:>16.2f} {-p:>+16.2f}")

    sec("2. THE RADIUS PROMISES HALF THE QUERIES")
    print(f"  {'rate':>7} {'y Johnson':>11} {'y capacity':>12} "
          f"{'query ratio':>13}  (eta -> 0)")
    print("  " + "-" * 52)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        yj, yc = yield_johnson(rho), yield_capacity(rho, 1e-9)
        print(f"  {'1/%d' % 2**R:>7} {yj:>11.3f} {yc:>12.3f} {yj/yc:>13.3f}")
    print("""
  Exactly a factor two, at every rate: Johnson's sqrt(rho) versus capacity's
  rho. If the radius were the whole story, capacity would halve every deployed
  system's query count and proof size.""")

    sec("3. THE FOLDING REQUIREMENT TAKES IT BACK")
    print("  m >= c/eta^2, and an m-folded symbol is m field elements per query.\n")
    print(f"  {'rate':>7} {'best eta':>9} {'m needed':>9} {'query ratio':>12} "
          f"{'BYTES ratio':>12} {'verdict':>10}")
    print("  " + "-" * 66)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        r, eta = best_eta(rho)
        m = folding_required(eta)
        qr = yield_johnson(rho) / yield_capacity(rho, eta)
        verdict = "%.1f%%" % ((r - 1) * 100)
        print(f"  {'1/%d' % 2**R:>7} {eta:>9.4f} {m:>9.1f} {qr:>12.3f} "
              f"{r:>12.3f} {verdict:>10}")
    print("""
  The query count does fall -- to about 76-80% of Johnson's -- but each query
  now carries ~45-55 field elements instead of one. The two nearly cancel. At
  c = 1 the best case is a 0.5% to 6% size reduction, against the 50% the radius
  suggested.""")

    sec("4. AND c IS ONLY 'A SUFFICIENTLY LARGE ABSOLUTE CONSTANT'")
    print(f"  {'c':>6} " + " ".join(f"{'rate 1/%d' % 2**R:>10}" for R in (1, 2, 3)))
    print("  " + "-" * 40)
    for c in (0.5, 1.0, 2.0, 4.0, 8.0):
        row = " ".join(f"{best_eta(2.0**-R, c)[0]:>10.3f}" for R in (1, 2, 3))
        print(f"  {c:>6.1f} {row}")
    print("""
  Ratios above 1.000 are net losses. The result flips at c between 1 and 2, and
  the theorem does not pin c down. So the honest reading is: capacity-radius
  proximity gaps for FRS are a real theorem and a genuine advance in the
  literature, but they are NOT a proof-size win for deployed systems at any
  constant we can defend, and they may be a loss.

  Two effects make the table above GENEROUS to capacity:
    - Merkle path deduplication (merkle_dedup.py: paths cost 33-52% less than
      modelled here) shrinks the term that folding is being amortised against.
    - The ceiling drops by log2(1/eta) ~ 2.7 bits at the optimal eta, which has
      to be bought back with more queries.""")


if __name__ == "__main__":
    report()
