"""
Resolving the repository's longest-open gap: interleaved codes are a = 1.

ceiling_anatomy.py section 5 has carried an UNRESOLVED case since iteration 6.
It said, correctly, that the a-classification could be FALSE as stated:

    "The classic interleaved lemma is frequently quoted with a soundness term of
     O(1)/|F|, independent of n. If that is the operative bound for Brakedown at
     its deployed radius, then Brakedown is an UNCONDITIONAL a = 0 CODE test,
     and the claim 'code-proximity layers have a >= 1' is false as stated."

It also named exactly what would settle it, and noted that eprint's 403s made
this a tooling limit rather than a reasoning one. The paper turns out to be open
access at IACR Communications in Cryptology, which is not behind the eprint
Cloudflare challenge.

SOURCE
------
Benjamin E. Diamond and Jim Posen, "Proximity Testing with Logarithmic
Randomness", IACR Communications in Cryptology, vol. 1 no. 1 (2024).
https://cic.iacr.org/p/1/1/2/pdf  -- fetched and read directly.

    Theorem 1 (Roth-Zemor [AHIV23, section A]). Fix an arbitrary [n,k,d]-code
    C in F_q^n, and a proximity parameter e in {0, ..., (d-1)/3}. If given
    elements u_0 and u_1 of F_q^n satisfy
        Pr_{r in F_q} [ d((1-r)*u_0 + r*u_1, C) <= e ]  >  (e+1)/q
    then [the interleaved conclusion holds].

THE RESOLUTION: a = 1, AND THE FOLKLORE IS A MISREADING
--------------------------------------------------------
The false-witness probability is (e+1)/q with e <= (d-1)/3. For any code of
constant relative distance -- which is every code anyone deploys -- d = Theta(n),
hence e = Theta(n) and the numerator is Theta(n). So

    interleaved / Ligero / Brakedown proximity testing has a = 1.

The classification survives, and the "O(1)/|F|" folklore that worried iteration 6
is a conflation of two different independences:

    the bound IS independent of the interleaving width m  (the number of rows)
    the bound is NOT independent of the block length n     (through e)

Quoting it as O(1) drops the second. That is the precise diagnosis of the
concern, not merely a refutation of it.

SHARPNESS: a = 0 IS NOT AVAILABLE FOR THIS TEST
------------------------------------------------
    Remark 2. "Theorem 1 is sharp, in the sense that its false witness
    probability (e+1)/q cannot be decreased. This fact is demonstrated by the
    following example of Ben-Sasson et al. [BSCI+23, Rem. 1.1]."

with an explicit construction (u_0 := (x_0,...,x_e,0,...,0),
u_1 := (x_0 - 1,...,x_e - 1,0,...,0)) for which R* = {x_0,...,x_e} exactly, so
the probability equals (e+1)/q on the nose. The a = 1 floor for this family is
therefore proved tight, not a proof artifact.

ATTRIBUTION CORRECTION
----------------------
README finding 5 said "Diamond-Posen Remark 2 proves it cannot be decreased,
with an explicit counterexample attaining it." Remark 2 RECORDS the sharpness;
the counterexample is credited by Diamond and Posen themselves to Ben-Sasson et
al. [BSCI+23, Rem. 1.1]. The Roth-Zemor attribution of Theorem 1 was correct
(the paper labels it that way verbatim).

THE SECOND OPEN QUESTION IN SECTION 5, ALSO RESOLVED
------------------------------------------------------
Section 5 asked whether the gamma*n in soundcalc's UDR bound "comes from the
bare proximity gap or from the multi-point quotient structure layered on top of
it". The same paper answers it in passing (page 10):

    "In the Reed-Solomon setting, Ben-Sasson et al. [BSCI+23, Thm. 1.4] achieve
    an analogue of Theorem 1 for e as high as the unique decoding radius, albeit
    with an upper bound n/q on the false witness probability somewhat worse than
    that of (e+1)/q attained by Theorem 1."

n/q is the BARE proximity gap for Reed-Solomon at the unique-decoding radius. So
the n-dependence is intrinsic to the gap itself, not imported from quotienting.
Both of section 5's open questions are now closed, in the direction that
preserves the classification.

WHAT CONJECTURE 1 IS WORTH
--------------------------
    Conjecture 1. "We wonder whether Theorem 1 holds even for proximity
    parameters e in {0, ..., (d-1)/2}."

i.e. whether the sharp (e+1)/q survives all the way to the unique-decoding
radius, instead of stopping at a THIRD of the minimum distance. Section 4 below
prices it: 37-40% of queries depending on rate.
"""

import math


def e_max_third(rho):
    """Relative proximity parameter at Theorem 1's radius, (d-1)/3, for RS."""
    return (1.0 - rho) / 3.0


def e_max_half(rho):
    """Relative proximity parameter at the unique-decoding radius, (d-1)/2."""
    return (1.0 - rho) / 2.0


def bits_per_query(delta):
    """A query detects with probability delta, so it buys -log2(1-delta) bits."""
    return -math.log2(1.0 - delta)


def numerator_exponent(n, rho):
    """The `a` in numerator = O(n^a). e+1 with e = (d-1)/3 and d = (1-rho)n + 1."""
    return (1.0 - rho) * n / 3.0 + 1.0


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE NUMERATOR SCALES WITH n, SO a = 1")
    print(f"  false-witness probability is (e+1)/q with e <= (d-1)/3, "
          f"d = (1-rho)n + 1\n")
    print(f"  {'n':>10} {'rho=1/2':>12} {'rho=1/4':>12} {'rho=1/8':>12}")
    print("  " + "-" * 50)
    for n in (2 ** 16, 2 ** 20, 2 ** 24):
        row = "  ".join(f"{numerator_exponent(n, r):>10.3g}"
                        for r in (0.5, 0.25, 0.125))
        print(f"  {n:>10}   {row}")
    print("""
  Each 16x increase in n multiplies the numerator by 16. That is a = 1 by
  definition, and it settles the case ceiling_anatomy.py section 5 left open:
  interleaved codes do NOT give a = 0, so the classification
  "code proximity layers carry a >= 1" holds unconditionally for this family.""")

    sec("2. WHERE THE 'O(1)/|F|' FOLKLORE COMES FROM")
    print("""
  The interleaved lemma's bound is genuinely independent of the INTERLEAVING
  WIDTH m -- testing a random combination of m rows costs the same as testing
  two. That is the striking part of the result, and it is what gets quoted.

  But it is not independent of the BLOCK LENGTH n, because e <= (d-1)/3 and
  d = Theta(n). Quoting the bound as O(1)/|F| silently drops the second
  dependence. Both statements below are true, and only the first is what the
  lemma says:

      independent of m (rows interleaved)   -> TRUE,  and the point of the lemma
      independent of n (block length)       -> FALSE, the numerator is Theta(n)""")

    sec("3. SHARPNESS: a = 0 IS PROVABLY UNAVAILABLE HERE")
    print("""
  Remark 2 gives an explicit pair attaining the bound exactly:

      u_0 = (x_0, ..., x_e, 0, ..., 0)
      u_1 = (x_0 - 1, ..., x_e - 1, 0, ..., 0)

  for distinct x_0, ..., x_e in F_q. Then R* = {x_0, ..., x_e} precisely, so
  Pr_r[d(...) <= e] = (e+1)/q on the nose, while the interleaved conclusion
  fails. So (e+1)/q "cannot be decreased" -- the a = 1 floor for this family is
  proved, not an artifact of a lossy analysis.""")

    sec("4. WHAT CONJECTURE 1 IS WORTH, PRICED")
    print("  Theorem 1 stops at e = (d-1)/3. Conjecture 1 asks for e = (d-1)/2.\n")
    print(f"  {'rate':>7} {'delta at /3':>12} {'delta at /2':>12} "
          f"{'bits/query':>11} {'-> ':>4} {'bits/query':>10} {'query cut':>11}")
    print("  " + "-" * 74)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        d3, d2 = e_max_third(rho), e_max_half(rho)
        y3, y2 = bits_per_query(d3), bits_per_query(d2)
        print(f"  {'1/%d' % 2**R:>7} {d3:>12.4f} {d2:>12.4f} "
              f"{y3:>11.4f} {'':>4} {y2:>10.4f} {100*(1-y3/y2):>10.1f}%")
    print("""
  So Conjecture 1 is worth a 37-40% reduction in query count, rising with
  blowup. README quoted "~37%", which is the figure at rate 1/2; at rate 1/8 it
  is 40.1%. It remains open in the literature -- this file prices it, it does
  not settle it.""")


if __name__ == "__main__":
    report()
