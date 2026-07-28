"""
Regime M: proven mutual correlated agreement just past the Johnson radius.

SOURCE
------
Sunghyeon Jo, "Reed-Solomon Mutual Correlated Agreement Beyond the Johnson
Radius", eprint 2026/1432. At a fixed rate 1/r, for any fixed integer number of
steps h >= 1 beyond the Johnson budget:

    error budget   E = floor(n - sqrt(n(K-1))) + h
    MCA error      O_{r,h}( K^6 / q )

where K is the code dimension (= trace length), n the block length, q = |F|.
The paper reports the first post-Johnson budget has MCA error below 2^-128 at
rates 1/2, 1/4, 1/8 and 1/16.

WHY THIS MATTERS
----------------
Mutual correlated agreement is exactly what WHIR needs, and it is one of the
three up-to-capacity conjectures Crites-Stewart refuted in 2025 (eprint
2025/2046). So this is a partial rescue: MCA is UNCONDITIONALLY true just past
Johnson, with an explicit polynomial error.

WHAT THIS FILE SHOWS
--------------------
Two things, and the second is the interesting one.

1. The RADIUS gain is one integer step of the error budget, i.e. delta grows by
   h/n. At n = 2^21 that is a change of ~5e-7 in delta, so the per-query yield
   is indistinguishable from the Johnson yield. The value of the theorem is NOT
   more bits per query.

2. The value is the COMMIT term -- but K^6/q is expensive. Needing K^6/q < 2^-lam
   means

       log2|F|  >  6*log2(K) + lam

   which at a 2^20 trace and lam = 128 demands a ~248-bit field. Every
   small-field system (31-bit^4 = 124 bits, Goldilocks^3 = 192) is far short.
   Regime M is usable only at Cairo/StarkNet-class field sizes.

So the one new unconditional above-Johnson MCA result is, at present, unusable
by exactly the systems that need above-Johnson soundness most.

CAVEAT: O_{r,h}(.) hides constants depending on the rate 1/r and the step count
h. This file uses the bare K^6/q and therefore reports the OPTIMISTIC case; real
constants only push the required field size up.
"""

import math


def required_field_bits(log_K, lam, exponent=6):
    """log2|F| needed for K^exponent/q < 2^-lam."""
    return exponent * log_K + lam


def achievable_lambda(E, log_K, exponent=6):
    """Bits of MCA soundness available in a field of E bits at dimension 2^log_K."""
    return E - exponent * log_K


def johnson_budget(n, K):
    """E_J = floor(n - sqrt(n(K-1)))."""
    return math.floor(n - math.sqrt(n * (K - 1)))


def delta_of_budget(E, n):
    return E / n


FIELDS = [
    ("M31^4 / BabyBear^4 / KoalaBear^4", 124),
    ("Goldilocks^2 (Plonky2, Miden)", 128),
    ("Goldilocks^3 (Venus, ZisK)", 192),
    ("Cairo / StarkNet 251-bit", 251),
    ("BN254-class 254-bit", 254),
]


def sec(t):
    print("\n" + "=" * 96)
    print(t)
    print("=" * 96)


def report():
    sec("1. THE RADIUS GAIN IS NEGLIGIBLE (one integer step of the error budget)")
    print(f"  {'rate':>8} {'log2 n':>7} {'delta_J':>10} {'delta_J+1step':>14} "
          f"{'yield_J':>9} {'yield_M':>9} {'gain':>10}")
    print("  " + "-" * 74)
    for R in (1, 2, 3, 4):
        log_n = 21
        n = 2 ** log_n
        K = n >> R                       # dimension = rho * n
        EJ = johnson_budget(n, K)
        dJ, dM = delta_of_budget(EJ, n), delta_of_budget(EJ + 1, n)
        yJ, yM = -math.log2(1 - dJ), -math.log2(1 - dM)
        print(f"  {'1/'+str(2**R):>8} {log_n:>7} {dJ:>10.6f} {dM:>14.6f} "
              f"{yJ:>9.5f} {yM:>9.5f} {yM-yJ:>10.2e}")
    print("""
  One step moves delta by 1/n. The per-query yield changes in the 7th decimal
  place. Whatever this theorem is worth, it is not worth it per query.""")

    sec("2. THE COMMIT TERM K^6/q IS THE BINDING COST")
    print("  Field size needed for MCA error < 2^-lambda, by trace length:\n")
    print(f"  {'trace':>8} {'lam=100':>9} {'lam=128':>9} {'lam=160':>9}")
    print("  " + "-" * 40)
    for log_K in (14, 17, 20, 22, 24):
        row = [required_field_bits(log_K, L) for L in (100, 128, 160)]
        print(f"  {'2^'+str(log_K):>8} {row[0]:>9} {row[1]:>9} {row[2]:>9}")

    sec("3. WHAT EACH DEPLOYED FIELD CAN ACTUALLY GET (trace 2^20)")
    log_K = 20
    print(f"  {'field':<36} {'E':>5} {'MCA bits':>9} {'>=100?':>8} {'>=128?':>8}")
    print("  " + "-" * 70)
    for name, E in FIELDS:
        lam = achievable_lambda(E, log_K)
        print(f"  {name:<36} {E:>5} {lam:>9} "
              f"{('yes' if lam >= 100 else 'NO'):>8} "
              f"{('yes' if lam >= 128 else 'NO'):>8}")
    print("""
  Every small-field system is deeply negative or near zero: at a 2^20 trace,
  K^6 alone is 2^120, which exhausts a 124-bit extension before any security
  budget is allocated. Only 250-bit-class fields clear 128 bits.

  Shortening the trace helps at rate 6 bits of field per bit of log-trace, so a
  2^14 trace leaves 124 - 84 = 40 bits at E=124 -- still far short.""")

    sec("4. WHERE REGIME M SITS IN THE INVENTORY")
    print("""
  U  unique decoding      unconditional. Best CEILING of the classical regimes
                          (no (m+1/2) factor). THEOREM.md Thm 7.
  J  Johnson / BCHKS25    unconditional. Best per-query YIELD for m > m_eq(R).
  T  threshold halving    unconditional ABOVE Johnson (2026/858). Costs
                          kappa(R) in queries; commit term O(n)/|F|.
  M  post-Johnson MCA     unconditional, h integer steps past Johnson
                          (2026/1432). Yield ~ Johnson. Commit K^6/|F|.
                          USABLE ONLY AT ~250-BIT FIELDS.
  C  capacity             DISPROVED late 2025.

  For a small-field system wanting above-Johnson soundness, T remains the only
  practical option: its commit term is O(n)/|F| (~nu bits) against M's
  O(K^6)/|F| (~6*log2 K bits). At a 2^20 trace that is 21 bits versus 120.

  The pattern across this whole repository holds again: small fields buy prover
  speed and pay for it in every soundness bound, and each new result tends to
  widen rather than narrow that gap.""")

    sec("5. NOT A PROXIMITY REGIME: SWIRL")
    print("""
  SWIRL (OpenVM2, zkDTVM) is a matrix-stacking proof system that reduces trace
  evaluations to a stacked polynomial evaluation, opened via the WHIR PCS. It is
  an ARITHMETIZATION layer, not a new low-degree test, so it does not change the
  regime inventory above -- its soundness bottoms out in WHIR's proximity
  analysis, which is where BCHKS25 and the MCA question apply.

  Source: soundcalc math_companion/swirl.tex; SWIRL paper openvm.dev/swirl.pdf;
  canonical calculator openvm-org/stark-backend soundness.rs.""")


if __name__ == "__main__":
    report()
