"""
Expanding the last unquantified term -- and the leading constant costs a bit.

Iteration 26 read the BCS soundness theorem and left one term unexpanded: the
Merkle commitment multi-extraction error eps_MT. If its shape were worse than
birthday it would bind below everything else in this repo and invalidate the
lambda/2 and lambda/3 figures. It is not. This file expands it, DERIVES the
book's stated leading constant from its components as a check on the reading,
and then corrects iteration 26's own digest recommendation by 0.6 bits.

SOURCE
------
Chiesa-Yogev, "Building Cryptographic Proofs from Hash Functions", LaTeX source
at github.com/hash-based-snargs-book commit 305fa3d (2026-03-25).
Lemma [mt-multi-configuration-multi-extractability] (line 13874), with the bound
at line 13924 expanded from the macro at line 1020:

    eps_MT(lambda, lengths, t, n_c)
        <=  (3/2) * t(t-1)/2^lambda            <- collisions among oracle queries
          + (d_max + 1) * 2 * sum_l / 2^lambda <- one pass over every tree node
          + (n_c - 1) * t / 2^lambda           <- distinct commitments colliding

  simplifying (line 1031) to  (3/2)*t^2/2^lambda + (n_c - 1)*t/2^lambda
  under the condition (line 1030)  t >= 2*(d_max + 1)*sum_l.

CHECKING THE READING: DERIVING 3.5
-----------------------------------
BCS instantiates this with n_c = t+1 (macro BCSMTError, line 1077: the adversary
may produce one commitment per query, plus the final one). So the third term
becomes t^2/2^lambda and

    eps_MT       <=  (3/2 + 1) * t^2/2^lambda   =  2.5 * t^2/2^lambda
    hash chain    =            1 * t^2/2^lambda
    ------------------------------------------------------------
    additive      <=          3.5 * t^2/2^lambda

which is exactly the constant the book states independently
(BCSSimplifiedLeadingConstant = 3.5, line 1084). Three separately-read macros
reproduce a fourth. That is the check that I read the terms correctly rather
than plausibly.

FINDING 1 -- NOTHING IN THE ADDITIVE ERROR IS WORSE THAN BIRTHDAY
------------------------------------------------------------------
All three components are t^2/2^lambda or smaller, and the one length-dependent
term is INDEPENDENT of t (a fixed cost, ~2^-227 at lambda=256 with a 2^24 proof).
So iteration 26's conclusion -- classical lambda/2, quantum lambda/3 -- covers
the entire additive error, with no hidden term of a worse shape. This closes the
composition question opened in iteration 26.

FINDING 2 -- THE CONSTANT IS NOT FREE, AND 256 BITS DOES NOT BUY 128
---------------------------------------------------------------------
Security from this term is where 3.5*t^2/2^lambda reaches 1:

    t = 2^(lambda/2) / sqrt(3.5)   =>   bits = lambda/2 - log2(3.5)/2
                                             = lambda/2 - 0.90

So a 256-bit digest -- the ubiquitous default -- delivers 127.10 classical bits,
not 128. A system claiming exactly 128 classical bits with a 256-bit hash is
0.9 bits short by the book's own constant. Reaching a true 128 needs
lambda >= 258.

FINDING 3 -- CORRECTING ITERATION 26 BY 0.6 BITS
-------------------------------------------------
Iteration 26 concluded that 128 post-quantum bits needs "a 384-bit digest",
from lambda/3 >= 128. With the constant carried through,

    PQ bits = lambda/3 - log2(3.5)/3 = lambda/3 - 0.60

so lambda = 384 delivers 127.40 PQ bits and misses 128 by 0.6. The requirement
is lambda >= 386. The "13 field elements over a 31-bit base" figure from
iteration 26 survives unchanged (13 * 31 = 403 >= 386); it was the round
384 that was wrong, and only just.
"""

import math

LOG2_C = math.log2(3.5)          # the book's leading constant


def mt_error_full(lam, t, sum_len, d_max, n_c):
    """The unsimplified three-term bound, as a probability."""
    return ((1.5 * t * (t - 1)) / 2.0 ** lam
            + ((d_max + 1) * 2 * sum_len) / 2.0 ** lam
            + ((n_c - 1) * t) / 2.0 ** lam)


def mt_error_simplified(lam, t, n_c):
    """(3/2)t^2/2^lambda + (n_c-1)t/2^lambda, valid when the condition holds."""
    return (1.5 * t * t + (n_c - 1) * t) / 2.0 ** lam


def simplified_condition_threshold(sum_len, d_max):
    """t must exceed this for the simplified bound: t >= 2(d_max+1)*sum_len."""
    return 2 * (d_max + 1) * sum_len


def additive_constant():
    """Derive BCS's 3.5 from its parts: 1.5 (MT birthday) + 1 (n_c=t+1) + 1 (FS)."""
    return 1.5 + 1.0 + 1.0


def hash_bits_classical(lam):
    """Where 3.5*t^2/2^lambda reaches 1: lambda/2 - log2(3.5)/2."""
    return lam / 2.0 - LOG2_C / 2.0


def hash_bits_quantum(lam, memory_bounded=False):
    """BHT/Zhandry Theta(2^(lambda/3)), carrying the same constant."""
    if memory_bounded:
        return lam / 2.0 - LOG2_C / 2.0
    return lam / 3.0 - LOG2_C / 3.0


def digest_needed(target, quantum=True, memory_bounded=False):
    """Smallest integer lambda delivering `target` bits, constant included."""
    f = 3.0 if (quantum and not memory_bounded) else 2.0
    return math.ceil(f * target + LOG2_C)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. DERIVING THE BOOK'S 3.5 FROM ITS COMPONENTS (a check on the reading)")
    print(f"""
  eps_MT   (3/2) t^2 / 2^lambda            collisions among oracle queries   1.5
           (n_c - 1) t / 2^lambda,  n_c=t+1  distinct commitments colliding   1.0
  FS chain  t^2 / 2^lambda                  hash-chain of verifier randomness 1.0
  {'-'*70}
  total                                                                      {additive_constant()}

  The book states 3.5 independently at line 1084. Three separately-read macros
  reproduce a fourth, so the terms are read correctly and not merely plausibly.""")

    sec("2. IS THE SIMPLIFIED BOUND VALID AT DEPLOYED PARAMETERS?")
    print(f"  {'proof len':>11} {'depth':>6} {'condition t >=':>16} "
          f"{'t at 100 bits':>14} {'holds':>7}")
    print("  " + "-" * 58)
    for logsum, d in ((20, 18), (24, 24), (25, 25), (26, 26)):
        thr = simplified_condition_threshold(2 ** logsum, d)
        holds = 2.0 ** 100 >= thr
        print(f"  {'2^%d' % logsum:>11} {d:>6} {'2^%.1f' % math.log2(thr):>16} "
              f"{'2^100':>14} {'yes' if holds else 'NO':>7}")
    print("""
  The condition binds at ~2^30 while any adversary worth bounding runs to 2^100
  or beyond, so the simplified form is the operative one everywhere. The
  length-dependent term it drops is INDEPENDENT of t -- a fixed cost of about
  2^-227 at lambda = 256 with a 2^24 proof -- so nothing of a worse shape than
  birthday survives anywhere in the additive error.""")

    sec("3. THE CONSTANT COSTS 0.90 CLASSICAL BITS AND 0.60 PQ BITS")
    print(f"  {'lambda':>7} {'classical':>10} {'vs lambda/2':>12} "
          f"{'PQ (BHT)':>9} {'vs lambda/3':>12}")
    print("  " + "-" * 54)
    for lam in (128, 192, 248, 256, 384, 386, 512):
        print(f"  {lam:>7} {hash_bits_classical(lam):>10.2f} "
              f"{hash_bits_classical(lam) - lam/2:>+12.2f} "
              f"{hash_bits_quantum(lam):>9.2f} "
              f"{hash_bits_quantum(lam) - lam/3:>+12.2f}")
    print(f"""
  A 256-bit digest delivers {hash_bits_classical(256):.2f} classical bits, not 128. Any system
  claiming exactly 128 classical bits with a 256-bit hash is {128 - hash_bits_classical(256):.1f} bits short
  by the book's own constant.""")

    sec("4. CORRECTING ITERATION 26'S DIGEST REQUIREMENT")
    print(f"""
  Iteration 26 said 128 PQ bits needs "a 384-bit digest", from lambda/3 >= 128.
  Carrying the constant:

      lambda = 384  ->  {hash_bits_quantum(384):.2f} PQ bits   (misses 128 by {128 - hash_bits_quantum(384):.2f})
      lambda = {digest_needed(128):>3}  ->  {hash_bits_quantum(digest_needed(128)):.2f} PQ bits   (clears it)

  So the requirement is lambda >= {digest_needed(128)}, not 384. The "13 field elements over a
  31-bit base" figure survives unchanged -- 13 * 31 = 403 >= {digest_needed(128)} -- it was the
  round number 384 that was wrong, and only just.""")
    print(f"\n  {'target':>7} {'classical needs':>16} {'PQ needs':>10} "
          f"{'31-bit elements':>16}")
    print("  " + "-" * 54)
    for tgt in (64, 100, 128, 192):
        q = digest_needed(tgt)
        print(f"  {tgt:>7} {digest_needed(tgt, quantum=False):>16} {q:>10} "
              f"{math.ceil(q / 31):>16}")


if __name__ == "__main__":
    report()
