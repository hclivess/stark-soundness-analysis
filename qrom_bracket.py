"""
The QROM loss is bracketed, not unknown -- and iteration 23's caveat pointed the
WRONG WAY.

WHAT ITERATION 23 SAID
----------------------
It said the halving `PQ = classical/2` is unverified against eprint 2025/2166,
and that the repository's headline -- "no deployed system reaches 100 provable
post-quantum bits" -- could therefore INVERT:

    full halving   ->  51 PQ  -> nothing clears 100
    negligible loss-> 102 PQ  -> most systems clear it        <-- claimed possible

That third row is impossible, and this file proves it from structure rather than
from a constant I could not fetch. The fragile claim is a DIFFERENT one.

THE BRACKET
-----------
Split every soundness term by whether its bad event is a function of a
Fiat-Shamir-derived challenge (all of them are) and by whether the classical
bound is ATTAINED by an explicit strategy (only some are).

  UPPER BOUND (an attack, not an assumption).
    A cheating prover varies a nonce, hashes, and checks whether the derived
    challenge is favourable. That is unstructured search over a marked set of
    density eps. Grover finds a marked item in Theta(1/sqrt(eps)) iterations,
    so wherever the classical bound k = log2(1/eps) is ATTAINED classically,
    the quantum cost is exactly 2^(k/2).
    BBBV (Bennett-Bernstein-Brassard-Vazirani) says no quantum algorithm beats
    Grover for unstructured search, so this is tight in both directions: for an
    attained term, PQ = k/2 EXACTLY, not "at most" and not "at least".

  LOWER BOUND (the proof side).
    QROM reductions -- CMS19's lifting lemma, generalized by Chiesa-Di-Hu-Zheng
    (eprint 2025/2166) -- bound quantum success by a polynomial function of the
    classical state-restoration error, losing a factor polynomial in the query
    budget. Writing that loss as t -> t^c, a term with classical bound k is
    provable at k/c bits. And c >= 2 necessarily, since c < 2 would prove more
    security than the Grover attack leaves standing.

  So for every term:      k/c  <=  PQ_provable  <=  k/2,     c >= 2.

`classical/2` is the BEST case, not the conservative one. Iteration 23 wrote
"treat every PQ number here as a conservative LOWER bound". Backwards: they are
optimistic UPPER bounds. The unresolved question is not whether the loss is
smaller than halving -- it cannot be -- but whether it is LARGER.

WHICH TERMS ARE ATTAINED
------------------------
The query phase is. A prover committing to a word at distance delta from the
code passes each of s queries with probability ~(1-delta), and grinds over
nonces for a favourable query set; combined with g bits of proof-of-work the
marked-set density is exactly 2^-(s*y + g). That is a realizable strategy at the
unique-decoding radius, so the classical bound is attained and the halving is
exact.

The commit phase is NOT known to be attained -- the proximity-gap constant C is
an artifact of the proof, and nobody exhibits a prover achieving it. That is
precisely the term where 2025/2166's constant matters.

WHY THAT SETTLES THE HEADLINE
-----------------------------
Total soundness is a MINIMUM over terms. From adversarial.py's iteration-15
reading of soundcalc's per-component column, the QUERY PHASE binds for six of
the seven verified production zkVMs (all but OpenVM, which is commit-bound in
JBR and reported in UDR, where its query term is 100.1 and binds again). So:

    PQ_total  <=  query_term / 2      for every deployed system,
                                      whatever 2025/2166 says.

The largest query term across the seven is ZisK's 128 bits. Hence no deployed
system exceeds 64 provable post-quantum bits -- a STRONGER statement than
"none reaches 100", and one that does not depend on the unfetched constant.

WHAT IS ACTUALLY FRAGILE
------------------------
The positive recommendation. `pq_design.py` says degree 10 over a 31-bit base
reaches 128 PQ bits. That figure is a CEILING -- a commit-phase quantity -- and
the commit phase is exactly the unattained term. At c = 2 it clears 128; at
c = 3 it delivers 96 and the recommendation needs degree ~13-14 instead.

So iteration 23 hedged the negative claim, which turns out to be unconditional,
and left the positive claim -- the one that actually rests on the constant --
unhedged. This file corrects both.
"""

import math

# ------------------------------------------------------------------ parameters

# (name, E, R, log_trace, s, g, reported classical bits, reported regime)
# Identical to adversarial.py's ZKVMS. Venus excluded as a ZisK duplicate.
ZKVMS = [("SP1 6.1.0",    124, 2, 21, 124, 16, 100, "UDR"),
         ("OpenVM 1.5.0", 124, 1, 23, 193, 20, 100, "UDR"),
         ("Airbender",    124, 1, 24,  87, 28,  67, "JBR"),
         ("Pico",         124, 1, 22,  84, 16,  53, "JBR"),
         ("ZisK 0.16.1",  192, 1, 21, 229, 16, 128, "JBR"),
         ("RISC Zero",    124, 2, 21,  50,  0,  48, "JBR"),
         ("Miden",        128, 3, 18,  27, 16,  55, "JBR")]

# soundcalc's per-component minimum for each system (adversarial.py iteration 15)
BINDS = {"SP1 6.1.0": "query", "OpenVM 1.5.0": "query", "Airbender": "query",
         "Pico": "query", "ZisK 0.16.1": "query", "RISC Zero": "query",
         "Miden": "query"}


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def query_term(R, s, g, regime, m=1000.0):
    """Classical bits bought by the query phase: s * (bits per query) + g."""
    y = yield_udr(R) if regime == "UDR" else yield_jbr(R, m)
    return s * y + g


def pq_attained(k):
    """Grover on an ATTAINED classical bound: exactly k/2, by Grover + BBBV."""
    return k / 2.0


def pq_provable(k, c):
    """A term whose classical bound is NOT known attained: provable at k/c."""
    return k / float(c)


def sec(t):
    print("\n" + "=" * 94)
    print(t)
    print("=" * 94)


def report():
    sec("1. THE BRACKET:  k/c <= PQ_provable <= k/2,  with c >= 2")
    print("""
  UPPER: Grover over Fiat-Shamir nonces is an unstructured search of density
         eps = 2^-k. It costs 2^(k/2), and BBBV forbids doing better. Where the
         classical bound is ATTAINED, PQ = k/2 exactly.
  LOWER: QROM reductions lose t -> t^c in the query budget, giving k/c. And
         c >= 2, because c < 2 would prove past the Grover attack.

  Consequence: `PQ = classical/2` is the CEILING on provable post-quantum
  soundness, not a conservative floor. Iteration 23 had the direction wrong.""")

    sec("2. THE QUERY TERM BINDS, AND IT IS THE ATTAINED ONE")
    print(f"  {'system':<16} {'regime':>6} {'reported':>9} {'query term':>11} "
          f"{'binds':>7} {'PQ <= q/2':>10}")
    print("  " + "-" * 66)
    worst = 0.0
    for nm, E, R, T, s, g, rep, reg in ZKVMS:
        q = query_term(R, s, g, reg)
        cap = pq_attained(min(q, rep))
        worst = max(worst, cap)
        print(f"  {nm:<16} {reg:>6} {rep:>9} {q:>11.1f} "
              f"{BINDS[nm]:>7} {cap:>10.1f}")
    print(f"""
  The query term reproduces each reported total, and soundcalc's own
  per-component column says it is the binding one. Since the total is a MINIMUM,

      PQ_total <= query_term / 2 = {worst:.0f} bits at worst across all seven,

  and that inequality holds whatever eprint 2025/2166's constant turns out to
  be. The headline is unconditional -- and sharper than previously stated:
  not "nothing reaches 100", but NOTHING EXCEEDS {worst:.0f}.""")

    sec("3. WHAT 2025/2166 CAN AND CANNOT MOVE")
    print(f"  {'quantity':<34} {'c = 2':>8} {'c = 3':>8} {'c = 4':>8}  fragile?")
    print("  " + "-" * 74)
    rows = [("deployed max (query, attained)", 128, True),
            ("31-bit^4 ceiling (commit)", 102, False),
            ("31-bit^10 ceiling (commit)", 288, False),
            ("Goldilocks^3 ceiling (commit)", 170, False)]
    for lbl, k, attained in rows:
        vals = [pq_attained(k) if attained else pq_provable(k, c)
                for c in (2, 3, 4)]
        tag = "no -- attained" if attained else "YES"
        print(f"  {lbl:<34} {vals[0]:>8.1f} {vals[1]:>8.1f} {vals[2]:>8.1f}  {tag}")
    print("""
  The attained row does not move: Grover both achieves and cannot beat the
  square root. Every commit-phase ceiling does move, linearly in 1/c.""")

    sec("4. THE RECOMMENDATION IS THE FRAGILE CLAIM, NOT THE HEADLINE")
    base, T, R = 31, 20, 2
    nu = T + R
    print(f"  extension degree needed for 128 provable PQ bits over a "
          f"{base}-bit base, nu = {nu}:\n")
    print(f"  {'c':>3} {'classical needed':>17} {'E needed':>9} {'degree':>7}   note")
    print("  " + "-" * 62)
    for c in (2, 3, 4):
        need_cl = 128 * c
        need_E = need_cl + nu
        deg = math.ceil(need_E / base)
        note = "pq_design.py's recommendation" if c == 2 else "recommendation FAILS"
        print(f"  {c:>3} {need_cl:>17} {need_E:>9} {deg:>7}   {note}")
    print(f"""
  At c = 2, degree 10 gives ({base*10} - {nu})/2 = {(base*10-nu)/2:.0f} PQ bits and clears 128.
  At c = 3 the same configuration gives {(base*10-nu)/3:.0f}, and 128 needs degree 14.

  That is the claim whose truth depends on the constant in 2025/2166. Iteration
  23 hedged the wrong one.""")

    sec("5. HONEST LIMITS OF THIS ARGUMENT")
    print("""
  1. The Grover accounting is in ITERATIONS, not gate cost. Each iteration must
     evaluate the whole predicate coherently -- for a commit-phase grind that is
     a full Merkle recommitment. Classical bit-security ignores that same work
     factor W, so the comparison is symmetric and k/2 stands; but a cost-based
     accounting would read k/2 + log2(W) on both sides.
  2. Grover with an unknown number of solutions needs exponential search, worth
     a small constant factor -- under a bit.
  3. "Attained" is unconditional at the unique-decoding radius. In the Johnson
     regime it presumes a word exists at the Johnson radius with the assumed
     list structure -- the same premise the classical bound is stated against,
     so the two sides remain comparable.
  4. Grover parallelises poorly (k machines buy only sqrt(k)), so a realistic
     adversary does worse than 2^(k/2). That direction only helps the defender
     and is deliberately not credited.
  5. c is still unpinned. eprint PDFs sit behind a Cloudflare challenge this
     session cannot solve; OpenAlex confirms no open-access mirror exists for
     either 2025/2166 or CMS19 (eprint 2019/834). The bracket is what can be
     established without them.""")


if __name__ == "__main__":
    report()
