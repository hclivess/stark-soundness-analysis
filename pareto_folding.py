"""
Four of seven deployed configurations are Pareto-dominated, and the whole gap is
the folding factor -- not the blowup, not the query count.

Proposition 11 (iteration 71) reduced Johnson-regime soundness to s*R/2 + g and
showed the commit side is irrelevant at the optimum. That makes "is anyone
leaving anything on the table" a computable question: hold the security target
fixed, hold prover cost fixed, and ask whether a smaller proof exists.

WHY THE FIRST ANSWER WAS WRONG
--------------------------------
Minimising proof size alone drives the blowup to the search boundary -- every
system's optimum came out at R = 8, i.e. an LDE 256x the trace. That is not a
frontier, it is an objective missing a term. Proof size falls sublinearly in
blowup while prover cost rises geometrically (iteration 72), so a single-
objective search always says "crank the rate".

The meaningful test is two-objective: at the SAME security and the SAME OR LOWER
LDE multiplier, does a smaller proof exist? That is Pareto domination, and it
cannot be answered by cranking anything.

THE RESULT
------------
    system      ships KiB   blowup   dominated by
    SP1               920        4   R=2 s=124 f=8  ->    644   -30%
    OpenVM         234641        2   R=1 s=193 f=8  -> 234170   -0.2%
    Airbender        1836        2   NOT DOMINATED
    Pico             2227        2   R=1 s=82  f=8  ->   1977   -11%
    ZisK              748        2   NOT DOMINATED
    RISC Zero         331        4   NOT DOMINATED
    Miden             112        8   R=3 s=27  f=8  ->    104   -7%

Every dominating configuration holds R and s essentially fixed -- SP1's is
IDENTICAL in both, Miden's too. The entire improvement is the folding factor.

AND THE SPLIT IS EXACTLY THE FOLDING FACTOR
---------------------------------------------
    ships folding <= 4:   4 of 4 dominated   SP1, OpenVM, Pico, Miden
    ships folding >= 8:   0 of 3 dominated   Airbender, ZisK, RISC Zero

A clean separation with no exceptions. The three systems already folding 8 or 16
are on the frontier; the four folding 2 or 4 are not.

WHY FOLDING BUYS PROOF SIZE
-----------------------------
A larger folding factor means fewer FRI rounds, so fewer Merkle roots and fewer
authentication paths -- at the cost of a larger leaf, since a round folding by
2^k commits 2^k siblings per leaf. Round count falls as nu/k while leaf size
grows as 2^k, so the total has an interior optimum. At the deployed query counts
that optimum is at 8, not 2.

WHAT THIS DOES NOT ESTABLISH
------------------------------
That the four should change. The folding factor is not a free parameter in a
system with recursion: the in-circuit FRI verifier's AIR is shaped by the fold
arity, so changing it rewrites the recursion circuits. NADO's fri.py says this
about its own blowup and it applies verbatim to folding:

    FRI_BLOWUP stays 2 for the SAME reason: a lower rate gives more bits/query
    but changes the fold shape, which would ripple into every recursion AIR.

So the honest claim is narrower than "four systems are misconfigured". It is:
at equal security and equal prover cost, a 7-30% smaller proof exists for four
of seven, reachable only by a change that also rewrites their recursion AIRs.
Whether that is worth 30% is an engineering judgement this repo cannot make.
What it can say is that the cost is not soundness -- Proposition 11 fixes the
security at s*y(R) + g, which the dominating configurations hold constant by
construction.

The three undominated systems are evidence the trade is real and someone has
already made it: Airbender folds [16,16,16,8,8], ZisK [8,8,8,8,8,4], RISC Zero
[16,16,16,16].
"""

import math

from proof_size_exact import fri_proof_bits, elem_bits
from soundcalc_lean import jbr_m

KIB = 8 * 1024

# (name, field, E, hash, batch, T, R, s, g, folding, reported, regime)
SYSTEMS = [
    ("SP1", "KoalaBear^4", 124, 248, 193, 21, 2, 124, 16, [2] * 23, 100, "UDR"),
    ("OpenVM", "BabyBear^4", 124, 256, 80000, 23, 1, 193, 20, [2] * 24, 100, "UDR"),
    ("Airbender", "M31^4", 124, 256, 1225, 24, 1, 87, 28, [16, 16, 16, 8, 8], 67, "JBR"),
    ("Pico", "KoalaBear^4", 124, 248, 1435, 22, 1, 84, 16, [2] * 23, 53, "JBR"),
    ("ZisK", "Goldilocks^3", 192, 256, 46, 21, 1, 229, 16, [8, 8, 8, 8, 8, 4], 128, "JBR"),
    ("RISC Zero", "BabyBear^4", 124, 256, 283, 21, 2, 50, 0, [16] * 4, 48, "JBR"),
    ("Miden", "Goldilocks^2", 128, 256, 100, 18, 3, 27, 16, [4] * 7, 55, "JBR"),
]

FOLD_CHOICES = (2, 4, 8, 16)


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, E):
    m = float(jbr_m(2.0 ** -R, E))
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("nan")


def schedule(nu, f):
    """A uniform fold schedule of arity f down to the final layer."""
    out, n, k = [], nu, int(math.log2(f))
    while n > k:
        out.append(f)
        n -= k
    return out or [2]


def size_kib(row, R, s, folding):
    _n, fld, _E, hb, b, T, *_ = row
    nu = T + R
    return fri_proof_bits(hb, elem_bits(fld), b, s, 2 ** nu, folding,
                          2.0 ** -R, True) // KIB


def shipped_kib(row):
    _n, _f, _E, _h, _b, T, R, s, _g, ff, *_ = row
    return size_kib(row, R, s, ff)


def queries_for(row, R):
    """Queries needed to hold this system's reported security at rate 2^-R."""
    _n, _f, E, _h, _b, _T, _R, _s, g, _ff, rep, reg = row
    y = yield_udr(R) if reg == "UDR" else yield_jbr(R, E)
    if not (y > 0):
        return None
    s = math.ceil((rep - g) / y)
    return s if s >= 1 else None


def dominating(row):
    """A config at the SAME security and SAME-OR-LOWER blowup with a smaller
    proof, or None. This is the Pareto test."""
    R_ship = row[6]
    ship = shipped_kib(row)
    best = None
    for R in range(1, 9):
        if 2 ** R > 2 ** R_ship:            # must not cost the prover more
            continue
        s = queries_for(row, R)
        if s is None:
            continue
        for f in FOLD_CHOICES:
            k = size_kib(row, R, s, schedule(row[5] + R, f))
            if k < ship and (best is None or k < best[3]):
                best = (R, s, f, k)
    return best


def shipped_fold(row):
    return row[9][0]


def dominated_by_fold():
    """{fold_bucket: (n_dominated, n_total)} -- the correlation."""
    lo = [r for r in SYSTEMS if shipped_fold(r) <= 4]
    hi = [r for r in SYSTEMS if shipped_fold(r) >= 8]
    return {"<=4": (sum(1 for r in lo if dominating(r)), len(lo)),
            ">=8": (sum(1 for r in hi if dominating(r)), len(hi))}


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE OBJECTIVE HAS TO BE TWO-DIMENSIONAL")
    print("""
  Minimising proof size alone drives the blowup to the search boundary -- every
  system's optimum comes out at R = 8, an LDE 256x the trace. That is not a
  frontier, it is a missing term: proof size falls sublinearly in blowup while
  prover cost rises geometrically (iteration 72).

  The meaningful test is: at the SAME security and the SAME OR LOWER LDE
  multiplier, does a smaller proof exist? That is Pareto domination, and it
  cannot be answered by cranking anything.""")

    sec("2. FOUR OF SEVEN ARE DOMINATED")
    print(f"\n  {'system':<11} {'ships KiB':>10} {'blowup':>7} {'dominated by':>30}")
    print("  " + "-" * 62)
    n_dom = 0
    for row in SYSTEMS:
        ship, dom = shipped_kib(row), dominating(row)
        if dom:
            n_dom += 1
            tail = f"R={dom[0]} s={dom[1]} f={dom[2]} -> {dom[3]}  {dom[3]/ship-1:+.0%}"
        else:
            tail = "NOT DOMINATED"
        print(f"  {row[0]:<11} {ship:>10} {2**row[6]:>7} {tail:>30}")
    print(f"""
  {n_dom} of {len(SYSTEMS)}. Every dominating configuration holds R and s essentially fixed --
  SP1's is IDENTICAL in both, Miden's too. The entire improvement is the folding
  factor.""")

    sec("3. AND THE SPLIT IS EXACTLY THE FOLDING FACTOR")
    d = dominated_by_fold()
    print(f"\n  {'system':<11} {'ships fold':>11} {'dominated?':>12}")
    print("  " + "-" * 36)
    for row in SYSTEMS:
        print(f"  {row[0]:<11} {shipped_fold(row):>11} "
              f"{str(bool(dominating(row))):>12}")
    print(f"""
      folding <= 4:   {d['<=4'][0]} of {d['<=4'][1]} dominated
      folding >= 8:   {d['>=8'][0]} of {d['>=8'][1]} dominated

  A clean separation with no exceptions. Larger folding means fewer FRI rounds,
  so fewer Merkle roots and fewer authentication paths, at the cost of a larger
  leaf -- a round folding by 2^k commits 2^k siblings. Round count falls as
  nu/k while leaf size grows as 2^k, so there is an interior optimum, and at the
  deployed query counts it sits at 8 rather than 2.""")

    sec("4. WHAT THIS DOES NOT ESTABLISH")
    print("""
  That the four should change. Folding arity is not free in a system with
  recursion: the in-circuit FRI verifier's AIR is shaped by it, so changing the
  arity rewrites the recursion circuits. NADO's fri.py says exactly this about
  its own blowup and it applies verbatim to folding:

      FRI_BLOWUP stays 2 for the SAME reason: a lower rate gives more bits/query
      but changes the fold shape, which would ripple into every recursion AIR.

  So the claim is narrower than "four systems are misconfigured": at equal
  security and equal prover cost a 7-30% smaller proof exists for four of seven,
  reachable only by a change that also rewrites their recursion AIRs. Whether
  that is worth it is an engineering judgement this repo cannot make.

  What it can say is that the cost is not SOUNDNESS. Proposition 11 fixes
  security at s*y(R) + g, which every dominating configuration holds constant by
  construction. And the three undominated systems are evidence the trade is real
  and already taken: Airbender folds [16,16,16,8,8], ZisK [8,8,8,8,8,4], RISC
  Zero [16,16,16,16].""")


if __name__ == "__main__":
    report()
