"""
Two of iteration 43's four obstacles dissolve on inspection.

Iteration 43 priced the one open capacity route and listed four obstacles
standing between it and a deployment. Iteration 44 priced the fourth (queries are
not proof size: a 58.5% query cut is a 40-50% size cut). Iteration 45 split the
first (most of the prize sits beyond the unique-decoding radius). This file
takes the remaining two, and both turn out to be weaker than stated -- one of
them by an enormous margin.

OBSTACLE 3 -- CERTIFICATION. DISSOLVED.
----------------------------------------
As stated in iterations 30, 43 and 45:

    "The guarantee holds with high probability over the choice of C. A deployed
     system samples one code and publishes it, and there is no known efficient
     certificate that a particular sample has the property."

That framing is RETRACTED here: the certificate is not needed. See below.

The stated worry traces to GGSW's Theorem 1.2, which says "with probability at
least 2/3 over the choice of C". A 1/3 chance of a permanently unsound system
would indeed be fatal, since the failure is a ONE-TIME setup event rather than a
per-proof one, and no amplification is available without the missing
certificate.

But 2/3 is a convenience figure in an informal statement, not the operative
bound. Yuan-Zhu's formal theorems (arXiv 2605.07595, lines 869 and 995) read:

    "Then, with probability at least 1 - q^{-Omega(n)}, a random linear code C
     of rate R and length n has minimum distance at least floor(delta*n) and
     satisfies the (E, E+, K/q)-line proximity-gap property."

GGSW's own body carries bounds of the same shape (1 - q^{r - eta*n}), so its
2/3 is likewise a simplification.

q^{-Omega(n)} at Ligero parameters is not a security-relevant quantity. With
q = 2^22 and code length 2^14, even reading the hidden constant as pessimistically
as Omega(n) = n/1000:

    Omega(n) = n        failure <= 2^-360,448
    Omega(n) = n/100    failure <= 2^-3,604
    Omega(n) = n/1000   failure <= 2^-360

A one-time public sample is safe by a margin larger than every other parameter
in the system. The certificate is not needed because the event it would certify
essentially cannot happen.

ONE RESIDUAL REQUIREMENT, and it is cheap: the code must be sampled HONESTLY --
from a public randomness beacon, or by hashing a public string. No probability
bound survives an adversarially chosen code. That is a standard transparent-setup
requirement, not a new one.

OBSTACLE 2 -- ALPHABET. LARGELY DISSOLVED.
-------------------------------------------
As stated: "near-MDS needs a large alphabet, and Ligero/Brakedown are often
deployed over SMALL fields precisely to make encoding cheap. A 22-bit alphabet
is a real change whose encoding cost is not modelled."

Iteration 44 already noticed that q = Theta(n) refers to the CODE LENGTH, not
the witness size. At its parameters (N = 2^20, t = 200) the code length is
n_enc = 27842 = 2^14.8, so the requirement is q >~ 2^15: a 16-bit field.

Every field these systems already use for constraint arithmetic covers it:

    BabyBear / KoalaBear    31 bits
    M31                     31 bits
    Goldilocks              64 bits
    BN254 scalar           254 bits

So the alphabet requirement is met by construction. It is not a change to the
field; it is a constraint that the field already satisfies with 16 bits to
spare.

What does NOT dissolve is the element-width sensitivity of the size result --
but it runs the other way from the worry. A WIDER element makes the reduction
SMALLER, because it inflates the sqrt-scaling field term relative to the
linear-scaling Merkle term:

    F = 2 bytes   205.4 -> 109.6 KiB    46.7% reduction
    F = 4 bytes   318.7 -> 182.5 KiB    42.7%
    F = 8 bytes   545.1 -> 328.3 KiB    39.8%

Iteration 44 quoted 42.7% at F = 4, which is the honest middle. A 64-bit system
gets 39.8%, not less than 39%.

WHERE THAT LEAVES THE PRIZE
---------------------------
    obstacle 1  composition beyond unique decoding   OPEN, and it is the gate
    obstacle 2  alphabet                             dissolved (16 bits, already met)
    obstacle 3  certification                        dissolved (2^-360 or better)
    obstacle 4  queries are not proof size           priced: 40-50%, not 58.5%

So the route is gated by ONE thing: whether a Ligero-style extractor composes
with correlated agreement beyond the unique-decoding radius. Iteration 45 showed
the portion reachable INSIDE unique decoding is 36.6-40.1% of queries, needs no
capacity result at all, and is exactly what Diamond-Posen Conjecture 1 would
deliver.
"""

import math

# code length at iteration 44's reference parameters
N_REF, R_REF, T_REF = 2 ** 20, 0.25, 200

DEPLOYED_FIELDS = [("BabyBear / KoalaBear", 31), ("M31", 31),
                   ("Goldilocks", 64), ("BN254 scalar", 254)]


def code_length(N=N_REF, R=R_REF, t=T_REF):
    from ligero_proof_size import best_m_numeric
    _, m = best_m_numeric(N, R, t)
    return N / (m * R)


def alphabet_bits_required(N=N_REF, R=R_REF, t=T_REF):
    """Yuan-Zhu needs q = Theta(code length), so log2 of that, rounded up."""
    return math.ceil(math.log2(code_length(N, R, t)))


def sampling_failure_bits(q_bits, n_code, constant=1.0):
    """-log2 of q^{-Omega(n)} = q_bits * constant * n_code."""
    return q_bits * constant * n_code


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. OBSTACLE 3 (CERTIFICATION): THE 2/3 WAS A CONVENIENCE FIGURE")
    print("""
  GGSW Thm 1.2 (informal):  "with probability at least 2/3 over the choice of C"
  Yuan-Zhu, formal (l.869): "with probability at least 1 - q^{-Omega(n)}"

  GGSW's body carries bounds of the same shape (1 - q^{r-eta*n}), so its 2/3 is
  likewise a simplification of an exponentially small failure probability.\n""")
    print(f"  {'reading of Omega(n)':<22} {'n_code = 2^14':>16} {'n_code = 2^15':>16}")
    print("  " + "-" * 58)
    for c, lbl in ((1.0, "Omega(n) = n"), (0.01, "n/100"), (0.001, "n/1000")):
        row = "  ".join(f"2^-{sampling_failure_bits(22, 2**lg, c):>12,.0f}"
                        for lg in (14, 15))
        print(f"  {lbl:<22} {row}")
    print("""
  Even reading the hidden constant as n/1000, a one-time public sample fails
  with probability at most 2^-360 -- below every other parameter in the system.
  The certificate is not needed because the event it would certify essentially
  cannot happen.

  RESIDUAL, and it is cheap: the code must be sampled HONESTLY, from a public
  beacon or by hashing a public string. No probability bound survives an
  adversarially chosen code. That is a standard transparent-setup requirement.""")

    sec("2. OBSTACLE 2 (ALPHABET): THE REQUIREMENT IS ON THE CODE LENGTH")
    n_c = code_length()
    req = alphabet_bits_required()
    print(f"  At N = 2^20, t = 200: code length n_enc = {n_c:,.0f} = 2^{math.log2(n_c):.1f}")
    print(f"  Yuan-Zhu needs q = Theta(n_enc), i.e. about {req} bits.\n")
    print(f"  {'field already in use':<24} {'bits':>6} {'covers it?':>12}")
    print("  " + "-" * 46)
    for nm, b in DEPLOYED_FIELDS:
        print(f"  {nm:<24} {b:>6} {'yes' if b >= req else 'NO':>12}")
    print("""
  Met by construction, with 16 bits to spare on the smallest of them. This is
  not a change to the field; it is a constraint the field already satisfies.""")

    sec("3. THE ELEMENT-WIDTH SENSITIVITY RUNS THE OTHER WAY")
    import ligero_proof_size as lps
    saved = lps.F_BYTES
    print(f"  {'element width':>14} {'before KiB':>12} {'after KiB':>11} "
          f"{'reduction':>11}")
    print("  " + "-" * 52)
    try:
        for F in (2, 4, 8):
            lps.F_BYTES = F
            a, _ = lps.best_m_numeric(N_REF, R_REF, 200)
            b, _ = lps.best_m_numeric(N_REF, R_REF, 83)
            print(f"  {'%d bytes' % F:>14} {a/1024:>12.1f} {b/1024:>11.1f} "
                  f"{1-b/a:>10.1%}")
    finally:
        lps.F_BYTES = saved
    print("""
  A WIDER element makes the reduction smaller, because it inflates the
  sqrt-scaling field term against the linear-scaling Merkle term. Iteration 44
  quoted 42.7% at 4 bytes; a 64-bit system gets 39.8%. The worry was that a
  larger alphabet would be costly -- the alphabet is free, and the width effect
  is a couple of percentage points.""")

    sec("4. WHERE THAT LEAVES THE PRIZE")
    print("""
    obstacle 1  composition beyond unique decoding   OPEN -- and it is the gate
    obstacle 2  alphabet                             dissolved: 15 bits, already met
    obstacle 3  certification                        dissolved: 2^-360 or better
    obstacle 4  queries are not proof size           priced: 40-50%, not 58.5%

  One gate remains: whether a Ligero-style extractor composes with correlated
  agreement beyond the unique-decoding radius. Iteration 45 showed the portion
  reachable INSIDE unique decoding is 36.6-40.1% of queries, needs no capacity
  result at all, and is exactly what Diamond-Posen Conjecture 1 would deliver.""")


if __name__ == "__main__":
    report()
