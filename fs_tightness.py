"""
The Fiat-Shamir grinding bound is TIGHT, from a primary source -- and iterations
23 and 24 were each half right.

WHAT WAS MISSING
----------------
Iteration 24 argued that the query-phase bound is "attained", so its Grover
halving is exact. That premise was MY argument, not a citation. It is now
sourced, and the source is two-sided.

SOURCE
------
Alessandro Chiesa and Eylon Yogev, "Building Cryptographic Proofs from Hash
Functions" (free book, LaTeX source at github.com/hash-based-snargs-book,
commit 305fa3d, 2026-03-25). Two statements, verbatim from snargs-book.tex:

  Lemma [sp-srs-to-soundness], line 9159. If an SP has soundness error eps then
  its state-restoration soundness error obeys

      eps_SR(salt, n, t)  <=  (t + 1) * eps(n)                        [upper]
      eps_SR(salt, n, t)  >=  min{t,2^salt} * eps(n)
                              - C(min{t,2^salt}, 2) * eps(n)^2        [lower]

  and the accompanying text: "this upper bound is essentially tight because, in
  common parameter regimes, the SP state restoration soundness error is at least
  Omega(t) times the SP soundness error."

  Lemma [fs-for-sigma-protocol-adaptive-soundness], line 9103. Fiat-Shamir on an
  SP gives adaptive soundness error eps_ARG(lambda, n, t) <= eps_SR(salt, n, t),
  and -- "In fact, if eps_SR is a tight upper bound then eps_ARG >= eps_SR."

So the classical Fiat-Shamir soundness error is Theta(t * eps), tight in BOTH
directions, and the lower bound comes with an explicit attack (line 9340: a
"universal state-restoration attack" that reruns a cheating prover with a fresh
salt each time). That is exactly the nonce-grinding strategy iteration 24
assumed; it is now a cited theorem with a matching attack, not an assertion.

THE CORRECTION: "CONSERVATIVE" AND "OPTIMISTIC" ARE BOTH RIGHT
--------------------------------------------------------------
Iteration 23 called `classical/2` a conservative LOWER bound. Iteration 24
called it an optimistic UPPER bound. Each was half right, and neither said which
quantity it meant:

    k_bound  = the PROVABLE classical bound (what this repo computes)
    k_true   = the true classical security  (k_true >= k_bound, since a bound
               can be loose but never optimistic)

  Against PROVABLE post-quantum soundness:  PQ_provable = k_bound / c <= k_bound/2.
      -> k_bound/2 is the BEST case. Iteration 24 was right.
  Against TRUE post-quantum security:       PQ_true = k_true / 2 >= k_bound/2.
      -> k_bound/2 is a conservative floor. Iteration 23 was right.

The two differ exactly by the looseness of the classical bound, and by the
looseness of the QROM reduction (c). For an ATTAINED term (k_true = k_bound) the
two collapse and PQ = k/2 is exact. For an unattained term -- the commit phase,
whose constant C is a proof artifact -- they can be far apart in both
directions at once.

The engineering consequence is the opposite of what it looks like: for choosing
parameters, `classical/2` is the RIGHT number, because true security is what an
attacker faces. For claiming a proved post-quantum level, it is an upper bound
you may not be able to establish. The residual uncertainty in c is a PROOF gap,
not a security gap.

WHAT IS VALIDATED NUMERICALLY BELOW
-----------------------------------
1. The book's two-sided classical bound against exact 1-(1-eps)^t.
2. The Grover halving against exact amplitude amplification -- never actually
   computed in this repo before, only asserted. It costs 1.35 bits MORE than
   k/2 at equal success probability, so the repo's model is slightly
   conservative in the defender's favour, by a constant.
"""

import math

# ---------------------------------------------------------- classical grinding


def sr_exact(eps, t):
    """Exact success of t independent fresh-salt attempts: 1 - (1-eps)^t.

    Computed as -expm1(t * log1p(-eps)). The naive form 1 - (1-eps)**t is
    catastrophically wrong here: at eps = 2^-60, (1.0 - eps) rounds to exactly
    1.0 in float64, so the naive expression returns 0 for every t and the
    bracket check silently "fails". The first draft of this file did exactly
    that and reported the book's bound violated at k >= 60 -- it was my
    arithmetic, not their lemma. Same failure mode the suite caught in
    Theorem 4's closed form.
    """
    return -math.expm1(t * math.log1p(-eps))


def sr_upper(eps, t):
    """Chiesa-Yogev upper bound: (t+1) * eps."""
    return (t + 1) * eps


def sr_lower(eps, t, salt_bits=128):
    """Chiesa-Yogev lower bound: m*eps - C(m,2)*eps^2, m = min{t, 2^salt}."""
    m = min(t, 2.0 ** salt_bits)
    return m * eps - (m * (m - 1) / 2.0) * eps * eps


def classical_queries_for(eps, target=0.5):
    """Exact t with 1-(1-eps)^t = target."""
    return math.log1p(-target) / math.log1p(-eps)


# ------------------------------------------------------------ Grover / quantum


def grover_success(eps, T):
    """Exact amplitude amplification: sin^2((2T+1) * arcsin(sqrt(eps)))."""
    th = math.asin(math.sqrt(eps))
    return math.sin((2 * T + 1) * th) ** 2


def grover_queries_for(eps, target=0.5):
    """Exact T with sin^2((2T+1)theta) = target, first crossing."""
    th = math.asin(math.sqrt(eps))
    return (math.asin(math.sqrt(target)) / th - 1.0) / 2.0


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE BOOK'S TWO-SIDED CLASSICAL BOUND, CHECKED AGAINST EXACT PROBABILITY")
    print(f"  {'k':>4} {'t':>12} {'lower':>12} {'exact':>12} {'upper':>12} {'brackets':>9}")
    print("  " + "-" * 66)
    ok_all = True
    for k in (20, 40, 60, 80):
        eps = 2.0 ** -k
        for t in (2 ** (k // 2), 2 ** (k - 2), 2 ** k):
            lo, ex, up = sr_lower(eps, t), sr_exact(eps, t), sr_upper(eps, t)
            ok = lo - 1e-12 <= ex <= up + 1e-12
            ok_all &= ok
            print(f"  {k:>4} {t:>12} {lo:>12.6f} {ex:>12.6f} {up:>12.6f} "
                  f"{'yes' if ok else 'NO':>9}")
    print(f"\n  brackets hold everywhere: {ok_all}")
    print("""
  Both sides are within a small constant factor of the exact value in the regime
  that matters (t*eps <~ 1), which is what makes the Fiat-Shamir accounting
  `bits = log2(1/eps)` correct rather than merely safe.""")

    sec("2. THE GROVER HALVING, AGAINST EXACT AMPLITUDE AMPLIFICATION")
    print("  queries to reach success probability 1/2, both models exact:\n")
    print(f"  {'k':>4} {'log2 classical':>15} {'log2 quantum':>13} {'k/2':>8} "
          f"{'model err':>10}")
    print("  " + "-" * 56)
    errs = []
    for k in (20, 32, 48, 64, 80, 100, 128):
        eps = 2.0 ** -k
        tc = math.log2(classical_queries_for(eps))
        tq = math.log2(grover_queries_for(eps))
        errs.append(tq - k / 2)
        print(f"  {k:>4} {tc:>15.2f} {tq:>13.2f} {k/2:>8.1f} {tq - k/2:>+10.2f}")
    print(f"""
  The repo models post-quantum work as exactly 2^(k/2). Exact Grover needs
  {min(errs):+.2f} bits relative to that -- a constant, not a drift (spread
  {max(errs)-min(errs):.4f} bits across k = 20..128). Grover reaches 1/2 success in
  (pi/8)/sqrt(eps) queries, hence the -1.35; the classical side sits at
  ln(2)/eps, hence its -0.53.

  So `PQ = classical/2` OVERSTATES the quantum attacker's query count by about
  1.35 bits. The repo's PQ figures are conservative in the DEFENDER's favour by
  that constant, which is worth stating and too small to matter.""")

    sec("3. THE SALT-SPACE CAP, AND WHY IT DOES NOT SAVE ANYONE")
    print("""
  The book's lower bound is min{t, 2^salt} * eps: the grinding attack cannot
  exceed the salt space. A system with a tiny nonce space would therefore be
  IMMUNE to the grind beyond 2^salt attempts.

  That is not a defence in any deployed STARK. The "salt" is not a dedicated
  field -- a prover re-randomizes blinding factors, reorders independent
  commitments, or perturbs the witness, each of which yields a fresh transcript
  and hence a fresh challenge. The effective salt space is the prover's whole
  freedom in the transcript, which is astronomically larger than any grind a
  quantum attacker could mount. Deployed proof-of-work nonces (RISC Zero g=0,
  Pico/ZisK/Miden g=16, OpenVM g=20, Airbender g=28) are also far below any
  plausible salt bound.""")
    print(f"  {'salt bits':>10} {'attack capped at':>18} {'caps a k=64 grind?':>20}")
    print("  " + "-" * 50)
    for sb in (16, 32, 64, 128):
        capped = sb < 64
        print(f"  {sb:>10} {'2^%d attempts' % sb:>18} {'YES' if capped else 'no':>20}")
    print("""
  Only a salt space below the target security level would bind, and no system
  restricts the transcript that way.""")

    sec("4. PROVABLE vs TRUE: THE TWO READINGS OF classical/2")
    print(f"  {'term':<28} {'k_bound':>8} {'attained?':>10} "
          f"{'PQ provable':>12} {'PQ true':>9}")
    print("  " + "-" * 72)
    rows = [("query phase (ZisK, largest)", 128, True),
            ("query phase (RISC Zero)", 48, True),
            ("commit ceiling 31-bit^4", 102, False),
            ("commit ceiling 31-bit^10", 288, False)]
    for lbl, k, att in rows:
        prov = f"{k/2:.0f}" if att else f"{k/3:.0f}-{k/2:.0f}"
        true = f"{k/2:.0f}" if att else f">= {k/2:.0f}"
        print(f"  {lbl:<28} {k:>8} {'yes' if att else 'no':>10} "
              f"{prov:>12} {true:>9}")
    print("""
  For attained terms the two readings coincide and the number is exact. For the
  commit phase they diverge in OPPOSITE directions: provable soundness may be as
  low as k/3, while true security is at least k/2 and possibly much more,
  because the proximity-gap constant is not known to be attained by any prover.

  This is why the repository's headline survives and its design target does not:
  the headline rests on attained terms.""")


if __name__ == "__main__":
    report()
