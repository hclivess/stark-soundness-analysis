"""
Anatomy of the provable-soundness ceiling -- and a correction to iteration 6.

Iteration 6 concluded there are "exactly three ways to move the ceiling":
multilinear (doesn't), lattice (escapes), extension degree (lifts). Trying to
FALSIFY that claim by writing the ceiling in full generality shows it was
incomplete. There are five levers, and two of them have moved within the last
two years without anyone changing field size.

THE GENERAL FORM
----------------
Every commit-phase bound this repo has touched -- BCIKS20, BCHKS25, UDR,
threshold halving, action-orbit, and WHIR's per-round terms -- has the shape

    eps_commit  =  C(params) * n^a / |F|  *  2^(-g_commit)

for a domain size n = 2^nu, a constant-ish factor C depending on the proximity
parameter and rate, an EXPONENT a on the domain size, and optional commit-phase
proof-of-work. Taking logs:

    ceiling  =  E  -  a*nu  -  log2 C  +  g_commit

That is the whole object. Five levers, not three:

  1. E          extension field size          additive, unbounded, costs proof size
  2. a          exponent on the domain size   INTEGER, has moved 2 -> 1 -> 0
  3. nu         evaluation domain size        bounded below by the computation
  4. log2 C     the bound's constant factor   improved by better proofs
  5. g_commit   commit-phase grinding         additive, costs 2^g prover work

Iteration 6 collapsed 2, 4 and 5 into "the bound" and treated it as fixed. It is
not fixed: `a` alone has gone 2 -> 1 -> 0 in the literature since 2020, and each
step is worth nu bits -- about 22 at a 2^20 trace. That is larger than anything
extension degree buys per unit of proof size.

HISTORICAL MOVEMENT OF a
------------------------
  a = 2   BCIKS20                (m+1/2)^7 n^2 / (3 rho^{3/2} |F|)
  a = 1   BCHKS25, UDR           (2m'^5 + ...) n / (3 rho^{3/2} |F|),  (gamma n + 1)/|F|
  a = 1   threshold halving      n*r/|F|                      [2026/858]
  a = 0   action-orbit           O(1)/|F|, above Johnson      [2026/861, conditional on Q2]

Each decrement is worth nu bits at no cost in proof size, prover time, or
assumption strength -- it is pure proof engineering on the same protocol.
"""

import math


def ceiling(E, nu, a, log2C, g_commit=0):
    """ceiling = E - a*nu - log2 C + g_commit."""
    return E - a * nu - log2C + g_commit


# (label, a, log2C at m=16 / typical, source)
BOUNDS = [
    ("BCIKS20 (2020)",        2, 7 * math.log2(16.5) - math.log2(3) + 1.5, "eprint 2020/654"),
    ("BCHKS25 JBR (2025)",    1, 5 * math.log2(16.5) + 1 - math.log2(3) + 1.5, "eprint 2025/2055"),
    # UDR's constant is log2(gamma), gamma=(1-rho)/2, so it depends on the RATE:
    # -2.0 at rho=1/2, -1.415 at rho=1/4. The table below is at rho=1/4 (blowup 4)
    # to match the E=124, nu=22 instance used throughout.
    ("UDR (BCHKS25 Cor 1.4)", 1, math.log2((1 - 0.25) / 2), "gamma=(1-rho)/2 at rho=1/4"),
    ("threshold halving",     1, math.log2(20), "eprint 2026/858, r rounds"),
    ("action-orbit",          0, 0.0, "eprint 2026/861, conditional on Q2"),
]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    E, nu = 124, 22          # 31-bit^4, 2^20 trace, blowup 4

    sec("1. THE CEILING IS FIVE TERMS, NOT ONE")
    print("      ceiling = E - a*nu - log2(C) + g_commit\n")
    print(f"  at E={E}, nu={nu} (31-bit^4, 2^20 trace):\n")
    print(f"  {'bound':<24} {'a':>2} {'log2 C':>8} {'ceiling':>9} {'PQ':>7}  source")
    print("  " + "-" * 78)
    for lbl, a, c, src in BOUNDS:
        v = ceiling(E, nu, a, c)
        print(f"  {lbl:<24} {a:>2} {c:>8.1f} {v:>9.1f} {v/2:>7.1f}  {src}")
    print("""
  The exponent `a` is worth nu bits per decrement -- 22 here. Going from
  BCIKS20 to BCHKS25 bought more than doubling the extension degree would have,
  and cost nothing: same protocol, same proof size, same assumption.""")

    sec("2. WHAT EACH LEVER COSTS")
    print(f"""  {'lever':<22} {'moves ceiling by':<20} {'cost'}
  {'-'*76}
  {'E (extension deg)':<22} {'+1 per bit':<20} proof size; deg 4->10 is ~800 KiB at 128 PQ
  {'a (domain exponent)':<22} {'+nu per decrement':<20} NOTHING -- pure proof engineering
  {'nu (domain size)':<22} {'+a per halving':<20} bounded below by the computation itself
  {'log2 C (constant)':<22} {'+1 per bit':<20} NOTHING -- pure proof engineering
  {'g_commit (grinding)':<22} {'+1 per bit':<20} 2^g prover work, per folding round

  Two of the five are FREE. They are the ones the literature has actually been
  moving, and the ones no deployed system can act on unilaterally -- you get them
  by someone proving a better theorem, not by changing a config.""")

    sec("3. CORRECTING ITERATION 6")
    print("""
  Iteration 6 said: multilinear leaves the ceiling alone, lattices escape it,
  extension degree lifts it -- "exactly three ways". That collapsed `a`, `C` and
  g_commit into "the bound" and treated the bound as a constant.

  It is not a constant. Since 2020, on the SAME protocol and SAME assumption:
      a: 2 -> 1        (BCIKS20 -> BCHKS25)   worth ~22 bits at nu=22
      C: (m+1/2)^7 -> 2(m+1/2)^5               worth ~2*log2(m+1/2) ~ 8 bits
  and 2026/861 claims a = 0 conditionally, worth another ~22.

  So the corrected statement is: FIVE levers, of which
      - extension degree and grinding are yours to set,
      - domain size is set by the computation,
      - the exponent and the constant are set by whoever last proved a theorem,
        and they have moved more in five years than any config change.

  A system deployed in 2020 at 31-bit^4 had a ceiling of {b0:.0f} classical bits.
  The identical system today, with no change whatsoever, has {b1:.0f} -- because
  the analysis improved underneath it.""".format(
        b0=ceiling(E, nu, 2, BOUNDS[0][2]), b1=ceiling(E, nu, 1, BOUNDS[2][2])))

    sec("4. WHAT a = 0 WOULD MEAN")
    print(f"  {'system':<26} {'E':>4} {'nu':>4} {'a=1 now':>9} {'a=0':>7} {'a=0 PQ':>8}")
    print("  " + "-" * 64)
    for nm, Ex, nux in (("NADO today", 64, 18), ("NADO + GF(p^2)", 128, 18),
                        ("31-bit^4 deployed", 124, 22), ("Goldilocks^3", 192, 22)):
        a1 = ceiling(Ex, nux, 1, -1.415)
        a0 = ceiling(Ex, nux, 0, 0.0)
        print(f"  {nm:<26} {Ex:>4} {nux:>4} {a1:>9.1f} {a0:>7.1f} {a0/2:>8.1f}")
    print("""
  If the action-orbit line (2026/861) holds up -- it rests on an unproven
  sparse-dominance conjecture Q2 -- then NADO with a degree-2 extension would
  reach 128 classical / 64 PQ, and a 31-bit^4 system 124 / 62, with no parameter
  change at all. That is the single largest unclaimed win in this whole
  repository, and it is not ours to claim: it depends on someone settling Q2.""")


def scope_and_open_questions():
    sec("5. SCOPE OF THE a-CLASSIFICATION -- AND ONE UNRESOLVED CASE")
    print("""
  VERIFIED, by reading the formula in each case:

    a = 0   Jagged / sumcheck / zerocheck / RLC   soundcalc/circuits/jagged.py
            numerators are log2(width), 2*log_trace, num_constraints -- all
            logarithmic or constraint-counted, none polynomial in n
    a = 1   UDR                                   (gamma*n + 1)/|F|
    a = 1   BCHKS25 JBR                           (2m'^5 + ...)*n/(3 rho^{3/2}|F|)
    a = 1   threshold halving                     n*r/|F|            [2026/858]
    a = 2   BCIKS20                               (m+1/2)^7 n^2/(3 rho^{3/2}|F|)
    a = 0   action-orbit, CONDITIONAL on Q2       O(1)/|F|           [2026/861]

  So on everything whose formula I have actually read, the split holds: the
  sumcheck family is a = 0, the RS-proximity family is a >= 1, and the only
  a = 0 code test is conditional.

  UNRESOLVED -- Brakedown / Ligero interleaved codes.

  This is the case that could break the classification, and I could not settle
  it. Ligero-style proximity testing takes a random linear combination of m rows
  and applies a proximity test to the combination. The classic interleaved
  lemma (Ames-Hazay-Ishai-Venkitasubramaniam) is frequently quoted with a
  soundness term of O(1)/|F|, independent of n. If that is the operative bound
  for Brakedown at its deployed radius, then Brakedown is an UNCONDITIONAL
  a = 0 CODE test, and the claim "code-proximity layers have a >= 1" is false
  as stated -- it would instead be a statement about REED-SOLOMON proximity in
  the list-decoding regime specifically.

  Evidence pulling the other way: soundcalc's UDR bound for RS is
  (gamma*n + 1)/|F|, i.e. a = 1, and that IS a unique-decoding-radius bound. So
  an n-dependence survives at unique-decoding radius for RS. Whether the
  gamma*n term comes from the bare proximity gap or from the multi-point
  quotient structure layered on top of it is exactly what I could not determine.

  WHAT WOULD SETTLE IT: the explicit soundness statement in
    - Diamond, "Proximity Testing with Logarithmic Randomness", eprint 2023/630
    - "Proximity Gaps in Interleaved Codes"
    - the Brakedown paper's proximity lemma
  read directly rather than from abstracts. eprint PDFs return HTTP 403 to this
  session's fetcher, so this is a tooling limit, not a reasoning one.

  UNTIL THEN the classification should be read as scoped:
      "for the Reed-Solomon proximity bounds whose formulas are recorded above,
       code layers carry a >= 1 unconditionally, and the sumcheck family carries
       a = 0"
  and NOT as a claim about every possible code-based commitment.""")


if __name__ == "__main__":
    report()
    scope_and_open_questions()
