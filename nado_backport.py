"""
What to backport to NADO after iterations 24-50.

The NADO audit was iteration 23. Twenty-seven iterations have happened since,
and the user asked what of it should go back. This re-audits the live tree
(/root/nado, read 2026-07-28) and prices each item.

WHAT ALREADY LANDED
-------------------
    fri.py:54    EXT_CHALLENGES = True            GF(p^2) FRI folding
    stark.py:323 alphas -> t.challenge_ext()      the iteration-22 fix
    stark.py:448 same, verifier side

NADO's own calculator now reports 111 bits provable, against 47 when the audit
started and 63 after the partial migration. Both recommended migrations are in.

FINDING 1 -- A REMAINING BASE-FIELD CHALLENGE, AND IT IS THE WORST ONE
------------------------------------------------------------------------
stark.py:305 (prover) and :441 (verifier):

    challenges = [t.challenge() for _ in range(aux_spec["num_challenges"])]

`t.challenge()` is BASE field: 64 bits. The alphas two lines below were migrated
to `challenge_ext()`; these were not.

This is not a minor term. stark.py's own docstring says what aux_spec is:

    "`aux_spec` enables the TWO-PHASE protocol that lookup/permutation arguments
     (LogUp -- the memory-checking machinery the VM execution circuit needs)
     require"

So these are the LogUp challenges. A LogUp/permutation argument's soundness
error is (number of lookups + rows)/|challenge field|, so drawing them from the
base field caps that term at

    64 - log2(rows * lookups)

At NADO's 2^17 rows and a modest column count that is roughly 44 bits -- against
the 111 the FRI layer now provides, and against 121 for the alphas. Every other
term in the system is more than twice as strong.

The exact figure depends on NADO's real lookup count, which this file does not
know; the STRUCTURAL point does not. It is the same failure mode as the original
47-bit finding and the same fix, one term over.

    FIX: at stark.py:305 and :441, use the guard already present two lines below

        challenges = [(t.challenge_ext() if _ext_a else t.challenge())
                      for _ in range(aux_spec["num_challenges"])]

    with `_ext_a` computed exactly as it already is for the alphas. Worth +64
    bits on the term, and `nc` cancels the same way it does there.

FINDING 2 -- 93 QUERIES BUY NOTHING (known since iteration 23, still unapplied)
--------------------------------------------------------------------------------
NUM_QUERIES = 320 against a saturation point of 227. The query term is 150.8
bits against a ceiling of 112, so 93 queries add proof size and no security.
Cutting to 227 is a 29% proof-size reduction with zero soundness cost.

FINDING 3 -- NEW: NADO IS UNUSUALLY WELL PLACED TO USE BCHKS25 RESULT 1
-------------------------------------------------------------------------
Iteration 33 found that a = 0 is PROVED at the unique-decoding radius (BCHKS25
result 1: O_{eps*}(1) exceptional z's, all RS codes, arbitrarily small proximity
loss eps* > 0). NADO's calculator -- like Ethereum's soundcalc -- implements the
superseded O(n) UDR bound, and NADO's best regime IS unique decoding.

    ceiling today (a = 1)        112.0
    ceiling at a = 0, log2C = 2  126.0     +14.0
    ceiling at a = 0, log2C = 8  120.0      +8.0

a = 0 beats a = 1 while log2 C(eps*) < nu + log2(1/gamma) = 20, which is a wide
margin (iteration 34).

What makes NADO the good case: iteration 34 found the correction is usually
inert, because the query phase binds below the raised ceiling. NADO is the
opposite -- its query term is 150.8, far ABOVE the ceiling, so it has 93 spare
queries with which to pay the proximity loss that a = 0 costs. It is the one
configuration in this repo's whole survey where the trade is clearly favourable.

Realistic gain: the alphas term (121.4 at nc = 100) becomes binding, so
111 -> ~119, about +8 bits. Applying finding 1 first is a precondition, since
the aux term would otherwise bind at 44 and none of this would matter.

FINDING 4 -- DIGEST SIZE, AND A CHECK NADO SHOULD RUN
-------------------------------------------------------
Iterations 26-27: the BCS additive error is a birthday bound, so a lambda-bit
digest gives lambda/2 classical and lambda/3 post-quantum bits. NADO at 111
classical is 56 PQ (search-bound; iteration 49 confirms no reordering), which
needs

    lambda >= 3 * (56 + 0.6) = 170 bits

A 256-bit digest clears it with 86 bits to spare. This file could not determine
NADO's Merkle hash from the tree and is NOT asserting a problem -- it is naming
a number to check against.

FINDING 5 -- A BUG IN THE CALCULATOR I WROTE FOR THEM
-------------------------------------------------------
execnode/stark/soundness.py's `deep_bits` carries this docstring:

    "NOTE: stark.prove does NOT run a DEEP/out-of-domain step. deep_eval.py is a
     separate subsystem ... For the MAIN STARK the analogous algebraic term is
     the constraint-combination alphas"

and then `achieved()` includes that term in the minimum anyway:

    total = min(max(u, j), d, a)

`d` is 111.0 and the commit term is 112.0, so the DEEP term is what the report
prints as the headline. By its own docstring it should not be in the min for the
main STARK. Removing it changes the reported figure from 111.0 to 112.0.

Small, and mine.

PRIORITY
--------
    1. finding 1   aux/LogUp challenges -> challenge_ext()     largest, and a cap
    2. finding 2   NUM_QUERIES 320 -> 227                      29% proof size, free
    3. finding 5   drop `d` from the min in achieved()         reporting accuracy
    4. finding 4   confirm the Merkle digest is >= 170 bits    a check, not a fix
    5. finding 3   BCHKS25 result 1                            +8 bits, needs 1 first
"""

import math

# Live NADO parameters, read from /root/nado on 2026-07-28
E_BASE, E_EXT = 64.0, 128.0
R, S, G, T_LOG = 1, 320, 18, 17
NU = T_LOG + R


def y_udr(R_):
    return -math.log2((1 + 2.0 ** -R_) / 2)


def commit_udr(R_, nu_, E_):
    gamma = (1 - 2.0 ** -R_) / 2
    return E_ - math.log2(gamma * 2.0 ** nu_ + 1)


def saturation_queries(K, g, R_):
    return math.ceil((K - g) / y_udr(R_))


def aux_term(E_, rows_log=17, cols=8):
    """LogUp-style error ~ (rows*lookups)/|F|, so the term is E - log2(rows*cols)."""
    return E_ - math.log2(2.0 ** rows_log * cols)


def ceiling_a0(E_, log2C):
    """BCHKS25 result 1: O_{eps*}(1) exceptions, so the ceiling loses no nu."""
    return E_ - log2C


def digest_needed(pq_bits):
    return 3.0 * (pq_bits + math.log2(3.5) / 3.0)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    K = commit_udr(R, NU, E_EXT)
    q = S * y_udr(R) + G
    sat = saturation_queries(K, G, R)

    sec("1. WHERE NADO STANDS (live tree, 2026-07-28)")
    print(f"  E = {E_EXT:.0f} (GF(p^2)), nu = {NU}, queries = {S}, grind = {G}\n")
    print(f"  {'term':<26} {'bits':>8}")
    print("  " + "-" * 36)
    print(f"  {'commit phase (UDR)':<26} {K:>8.1f}")
    print(f"  {'query phase':<26} {q:>8.1f}")
    print(f"  {'alphas, GF(p^2), nc=100':<26} {E_EXT - math.log2(100):>8.1f}")
    print(f"  {'aux / LogUp, BASE field':<26} {aux_term(E_BASE):>8.1f}   <-- caps the VM circuit")
    print(f"""
  Both recommended migrations landed (EXT_CHALLENGES, and the alphas at
  stark.py:323/448), taking NADO from 47 to 111 bits. The aux/LogUp challenges
  at stark.py:305/441 were not migrated, and they are now the weakest term by a
  factor of more than two.""")

    sec("2. FINDING 1 -- THE AUX/LogUp CHALLENGES ARE STILL BASE FIELD")
    print(f"  {'':<28} {'base (today)':>13} {'GF(p^2) (fix)':>15} {'gain':>7}")
    print("  " + "-" * 66)
    print(f"  {'aux / LogUp term':<28} {aux_term(E_BASE):>13.1f} "
          f"{aux_term(E_EXT):>15.1f} {aux_term(E_EXT)-aux_term(E_BASE):>+7.1f}")
    print("""
  The fix is the guard already present two lines below, at stark.py:305 and 441:

      challenges = [(t.challenge_ext() if _ext_a else t.challenge())
                    for _ in range(aux_spec["num_challenges"])]

  The exact figure depends on NADO's real lookup count, which this file does not
  know. The structural point does not: it is a 64-bit challenge in a system
  whose other terms are 111 to 121.""")

    sec("3. FINDING 2 -- 93 QUERIES BUY NOTHING")
    print(f"  query term {q:.1f} against a ceiling of {K:.1f}; saturation at {sat} queries.")
    print(f"  {S} - {sat} = {S-sat} queries are proof size with no security "
          f"({(S-sat)/S:.0%} of the total).")

    sec("4. FINDING 3 -- NADO IS THE GOOD CASE FOR BCHKS25 RESULT 1")
    print(f"  {'log2 C(eps*)':>13} {'ceiling at a=0':>16} {'vs today':>10}")
    print("  " + "-" * 42)
    for lc in (0, 2, 4, 8):
        print(f"  {lc:>13} {ceiling_a0(E_EXT, lc):>16.1f} "
              f"{ceiling_a0(E_EXT, lc)-K:>+10.1f}")
    print(f"""
  a = 0 beats a = 1 while log2 C < nu + log2(1/gamma) = {NU + 2}, a wide margin.

  Iteration 34 found this correction usually inert, because the query phase
  binds below the raised ceiling. NADO is the opposite: its query term is {q:.1f},
  far above the ceiling, so it has {S-sat} spare queries to pay the proximity loss
  with. It is the one configuration in this repo's survey where the trade is
  clearly favourable -- but finding 1 must land first, or the aux term binds at
  {aux_term(E_BASE):.0f} and none of it matters.""")

    sec("5. FINDING 4 -- THE DIGEST NUMBER TO CHECK AGAINST")
    pq = min(K, q) / 2
    print(f"""
  NADO is search-bound (iteration 49: no PQ reordering), so PQ = {pq:.1f} bits.
  The BCS additive error is a birthday bound, giving lambda/3 post-quantum, so

      lambda >= 3 * ({pq:.1f} + 0.6) = {digest_needed(pq):.0f} bits

  A 256-bit digest clears it with {256 - digest_needed(pq):.0f} bits to spare. This file could not
  determine NADO's Merkle hash from the tree, so this is a number to check
  against, not an assertion that anything is wrong.""")


if __name__ == "__main__":
    report()
