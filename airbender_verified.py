"""
Airbender's full component table, and a 16x accuracy improvement it exposed.

Iteration 48 verified SP1 against soundcalc-lean's machine-checked figures --
one system, UDR regime. Airbender's reference table covers a different regime
(JBR), a mixed folding schedule, and commit-phase grinding, so it tests parts of
the model SP1 could not. It also has BOTH regime rows, which SP1's does not.

    | regime | total | ... | ALI | DEEP | batching | commit r1..r5      | query |
    | UDR    |    64 | ... | 114 |  110 |       90 | 106 110 114 118 121|    64 |
    | JBR    |    67 | ... | 109 |  105 |       68 |  83  87  91  95  98|    67 |

    hash 256 bits, grind_query 28, grind_commit 5, folding [16,16,16,8,8]

WHAT MATCHES EXACTLY
--------------------
All five UDR commit rounds. This repo's ceiling equation, with nu dropping by
log2(folding factor) each round and the declared +5 commit grinding added:

    reference   106  110  114  118  121
    this repo   106  110  114  118  121

The nu sequence is 25, 21, 17, 13, 10 -- steps of 4, 4, 4, 3, which is exactly
log2 of the mixed schedule [16,16,16,8,8]. README claims `a` "reads exactly 1"
on this schedule; here every round of it is reproduced, not just the step sizes.

The UDR query phase matches too: 64.1 against a reported 64.

BOTH ROWS CONFIRM TWO EARLIER FINDINGS
----------------------------------------
The QUERY PHASE binds in both regimes -- 64 = 64 in UDR, 67 = 67 in JBR -- which
is iteration 24's result for Airbender, now visible in the reference table rather
than inferred.

And JBR (67) beats UDR (64), so Airbender is correctly reported in JBR. Theorem 7
predicts JBR for it. Confirmed against a table that publishes both.

WHAT DID NOT MATCH, AND WHY IT MATTERS
----------------------------------------
The JBR query phase. This repo evaluates it at `m_eq(R)` -- Theorem 7(a)'s
yield-equalising parameter -- and gets 64.1 against a reported 67.

That is not a small error, and it is not random. `m_eq` is DEFINED as the m at
which JBR's per-query yield equals UDR's. So evaluating a system's JBR figure at
m_eq necessarily reproduces its UDR figure: 64.1 is the UDR number, arrived at by
construction. It is the right tool for locating the crossover and the wrong one
for computing what a system actually achieves in JBR.

Iteration 47 found that soundcalc derives m by formula -- jbrM = max(ceil(sqrt(rho)
/(2 eta)), 3) -- rather than treating it as free. Substituting that:

    system      reported    at m_eq   error    at jbrM   error
    Airbender         67       64.1    -2.9       67.4    +0.4
    Pico              53       50.9    -2.1       54.0    +1.0
    ZisK             128      111.0   -17.0      127.2    -0.8
    RISC Zero         48       33.9   -14.1       48.2    +0.2
    Miden             55       38.4   -16.6       55.8    +0.8

    total |error|    52.7 bits  ->  3.3 bits

Every system lands within about one bit, and the total error falls by a factor of
sixteen.

WHAT THIS DOES AND DOES NOT CHANGE
------------------------------------
It does NOT invalidate the repo's headline validation. That claim is about the
UDR figures -- "where soundcalc publishes the UDR figure too, the model
reproduces it within 1 bit" -- and the UDR side matches here to 0.1 bits across
five commit rounds and the query term.

It DOES mean that wherever this repo computed a JBR figure at m_eq, the number
was off by up to 17 bits for a reason that is now understood and fixable. The
correct usage is:

    m_eq   for Theorem 7's crossover, where the yield-equalising point IS the
           quantity of interest
    jbrM   for reproducing what a system achieves in the Johnson regime

Theorem 7's 7/7 prediction is unaffected -- iteration 47 already verified it
holds under both conventions, with every s* shifted but no system crossing.

And it closes a loop opened in iteration 55, which excluded the sqrt
approximation as the source of the model's overshoot (worth at most 0.24 bits)
and left the untuned-m gap as the remaining account. This is that gap, measured:
52.7 bits of it across five systems, and it is not "untuned" so much as the wrong
m for the question.
"""

import math

# Airbender reference table, SoundcalcIO/ZkVM/Ref/airbender.md
AIRBENDER = {
    "E": 124, "T": 24, "R": 1, "queries": 87,
    "grind_query": 28, "grind_commit": 5, "hash_bits": 256,
    "folding": [16, 16, 16, 8, 8],
    "udr": {"total": 64, "query": 64, "batching": 90, "ALI": 114, "DEEP": 110,
            "commit": [106, 110, 114, 118, 121]},
    "jbr": {"total": 67, "query": 67, "batching": 68, "ALI": 109, "DEEP": 105,
            "commit": [83, 87, 91, 95, 98]},
}

# (name, E, R, T, queries, grind, reported JBR query figure)
JBR_SYSTEMS = [("Airbender", 124, 1, 24, 87, 28, 67), ("Pico", 124, 1, 22, 84, 16, 53),
               ("ZisK", 192, 1, 21, 229, 16, 128), ("RISC Zero", 124, 2, 21, 50, 0, 48),
               ("Miden", 128, 3, 18, 27, 16, 55)]


def commit_udr(nu, E, rho):
    gamma = (1 - rho) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def commit_rounds_udr(cfg):
    """Ceiling per round: nu drops by log2(folding factor), plus commit grinding."""
    E, rho = cfg["E"], 2.0 ** -cfg["R"]
    nu = cfg["T"] + cfg["R"]
    out = []
    for f in [1] + cfg["folding"][:-1]:
        nu -= int(math.log2(f))
        out.append(commit_udr(nu, E, rho) + cfg["grind_commit"])
    return out


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def query_term(s, g, R, m=None):
    return s * (yield_udr(R) if m is None else yield_jbr(R, m)) + g


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    from regime_crossover import m_eq
    from soundcalc_lean import jbr_m

    sec("1. ALL FIVE UDR COMMIT ROUNDS MATCH EXACTLY")
    mine = commit_rounds_udr(AIRBENDER)
    ref = AIRBENDER["udr"]["commit"]
    print(f"  folding {AIRBENDER['folding']}, grind_commit "
          f"{AIRBENDER['grind_commit']}\n")
    print(f"  {'round':>7} {'reference':>10} {'this repo':>10} {'diff':>7}")
    print("  " + "-" * 38)
    for i, (r, m) in enumerate(zip(ref, mine), 1):
        print(f"  {i:>7} {r:>10} {m:>10.0f} {m-r:>+7.1f}")
    print(f"""
  The nu sequence is 25, 21, 17, 13, 10 -- steps 4, 4, 4, 3, exactly log2 of the
  mixed schedule. README claims `a` "reads exactly 1" on this schedule; here
  every round is reproduced, not just the step sizes.""")

    sec("2. BOTH REGIME ROWS CONFIRM EARLIER FINDINGS")
    u, j = AIRBENDER["udr"], AIRBENDER["jbr"]
    print(f"  {'regime':>7} {'total':>7} {'query':>7} {'binds?':>9} "
          f"{'batching':>10} {'ALI':>6} {'DEEP':>6}")
    print("  " + "-" * 58)
    for nm, row in (("UDR", u), ("JBR", j)):
        print(f"  {nm:>7} {row['total']:>7} {row['query']:>7} "
              f"{'query' if row['query'] == row['total'] else 'other':>9} "
              f"{row['batching']:>10} {row['ALI']:>6} {row['DEEP']:>6}")
    print(f"""
  The query phase binds in BOTH regimes -- iteration 24's result for Airbender,
  now visible rather than inferred. And JBR (67) beats UDR (64), so Airbender is
  correctly reported in JBR, which is what Theorem 7 predicts for it.

  UDR query phase: this repo gives {query_term(87, 28, 1):.1f} against a reported {u['query']}.""")

    sec("3. THE JBR QUERY TERM: m_eq IS THE WRONG PARAMETER FOR THIS QUESTION")
    print(f"""
  m_eq is DEFINED as the m at which JBR's yield equals UDR's, so evaluating a
  system's JBR figure at m_eq necessarily reproduces its UDR figure. For
  Airbender that is {query_term(87, 28, 1, m_eq(1)):.1f} -- the UDR number, arrived at by construction.

  Iteration 47 found soundcalc derives m by formula instead. Substituting it:\n""")
    print(f"  {'system':<12} {'reported':>9} {'at m_eq':>9} {'err':>7} "
          f"{'at jbrM':>9} {'err':>7}")
    print("  " + "-" * 58)
    te = tj = 0.0
    for nm, E, R, T, s, g, rep in JBR_SYSTEMS:
        a = query_term(s, g, R, m_eq(R))
        b = query_term(s, g, R, float(jbr_m(2.0 ** -R, E)))
        te += abs(a - rep)
        tj += abs(b - rep)
        print(f"  {nm:<12} {rep:>9} {a:>9.1f} {a-rep:>+7.1f} {b:>9.1f} "
              f"{b-rep:>+7.1f}")
    print(f"""
  total |error|:   {te:.1f} bits at m_eq   ->   {tj:.1f} bits at jbrM

  Every system within about a bit, and the total error falls {te/tj:.0f}-fold.

  This does NOT touch the repo's headline validation, which is about the UDR
  figures and matches here to 0.1 bits across five commit rounds and the query
  term. It does mean m_eq belongs to Theorem 7's crossover, where the
  yield-equalising point IS the quantity of interest, and jbrM belongs anywhere
  a system's achieved Johnson-regime figure is wanted.

  It also closes a loop from iteration 55, which excluded the sqrt approximation
  as the source of the model's overshoot and left the untuned-m gap. This is
  that gap, measured: it is not so much untuned as the wrong m for the question.""")


if __name__ == "__main__":
    report()
