"""
Design study: what actually reaches 128 bits of PROVABLE POST-QUANTUM soundness?

quantum.py established that no deployed system clears 100 PQ provable bits, and
that 128 needs 256 classical. This file asks the constructive question: given the
whole parameter space, what is the cheapest configuration that gets there?

It composes every result in the repo:
  * THEOREM.md Thm 2   -- the commit ceiling cannot be bought with queries
  * THEOREM.md Thm 7   -- UDR beats JBR past the crossover s*, and 256 classical
                          bits is deep past every crossover, so UDR is forced
  * quantum.py         -- PQ = classical/2 under Fiat-Shamir + Grover
  * EFFICIENCY.md      -- prover cost is dominated by the LDE, i.e. by 2^R and
                          trace length; query count is nearly free for the prover
                          and paid for entirely in proof size

THE KEY STRUCTURAL POINT, which falls out rather than being assumed:

The extension field is used for CHALLENGES, the DEEP point, and post-fold layer
values. The trace, the constraint evaluation and the layer-0 LDE -- i.e. the
prover's dominant cost -- stay in the BASE field. So a large extension degree
over a small base field buys soundness at close to small-field prover speed.
That is a materially different trade from adopting a large prime field.
"""

import math

# base fields, (name, log2 of base prime)
BASES = [("M31", 31), ("BabyBear", 31), ("KoalaBear", 31), ("Goldilocks", 64)]

HASH_BYTES = 32


# ------------------------------------------------------------------ soundness

def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def commit_udr(R, nu, E):
    gamma = (1 - 2.0 ** -R) / 2
    return E - math.log2(gamma * 2.0 ** nu + 1)


def commit_jbr(R, nu, E, m, folding=2):
    rho = 2.0 ** -R
    sr = math.sqrt(rho)
    mm = m + 0.5
    gamma = 1 - sr * (1 + 0.5 / m)
    if gamma <= 0:
        return float("-inf")
    n = 2.0 ** nu
    eps = ((2 * mm ** 5 + 3 * mm * gamma * rho) * n / (3 * rho * sr)
           + mm / sr) * max(folding - 1, 1)
    return min(E - math.log2(max(eps, 1.0)),
               E - math.log2(folding) - math.log2(n + 1)
               - math.log2(2 * m + 1) + 0.5 * math.log2(rho))


def best_jbr(R, nu, E, s, g):
    best = float("-inf")
    m = 1.0
    while m <= 1000.0:
        y = yield_jbr(R, m)
        if y > 0:
            best = max(best, min(s * y + g, commit_jbr(R, nu, E, m)))
        m *= 1.05
    return best


def classical_bits(R, nu, E, s, g, log_deg):
    u = min(s * yield_udr(R) + g, commit_udr(R, nu, E))
    j = best_jbr(R, nu, E, s, g)
    return min(max(u, j), E - log_deg)


def pq(c):
    return min(c / 2.0, 128.0)          # 256-bit hash floor never binds below 128


# ------------------------------------------------------------------ cost model

def queries_for(R, nu, E, g, target_classical, log_deg, cap=4000):
    """Smallest s meeting the classical target, or None if the ceiling forbids it."""
    if min(commit_udr(R, nu, E), E - log_deg) < target_classical:
        return None
    lo, hi = 1, cap
    if classical_bits(R, nu, E, cap, g, log_deg) < target_classical:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if classical_bits(R, nu, E, mid, g, log_deg) >= target_classical:
            hi = mid
        else:
            lo = mid + 1
    return lo


def base_bytes(bbits):
    """Serialised width of ONE base-field element. A 31-bit element is 4 bytes,
    a 64-bit Goldilocks element is 8. Charging 8 for both (an earlier bug here)
    penalises small bases and made Goldilocks look artificially cheaper."""
    return 4 if bbits <= 32 else 8


def _auth_nodes(s, d):
    """Expected DISTINCT authentication nodes for s queries in a depth-d tree.

    Paths share prefixes, and the top log2(s) levels saturate entirely. Charging
    s*d (as an earlier version of this file did) overcounts by 33-52% at the
    query counts required here. Model derived and validated against Monte Carlo
    to within 0.3% in merkle_dedup.py."""
    total = 0.0
    for i in range(d):
        m = 2 ** (d - i)
        q = 1.0 - (1.0 - 1.0 / m) ** s
        total += (m / 2.0) * 2.0 * q * (1.0 - q)
    return total


def proof_kib(nu, R, s, ext_words, bbits, n_base_trees=2):
    """Merkle paths dominate, deduplicated across queries."""
    rounds = max(0, nu - R)
    path_hashes = (n_base_trees * _auth_nodes(s, nu)
                   + sum(_auth_nodes(s, max(nu - i, 1)) for i in range(rounds)))
    w = base_bytes(bbits)
    value_bytes = s * (n_base_trees * w + rounds * 2 * ext_words * w)
    return (path_hashes * HASH_BYTES + value_bytes) / 1024


def prover_relative(R, T):
    """LDE work ~ 2^R * 2^T * (T + R), normalised to blowup 2 at the same trace."""
    return (2 ** R * 2 ** T * (T + R)) / (2 ** 1 * 2 ** T * (T + 1))


# ------------------------------------------------------------------- search

def search(target_pq, T, g, max_deg=12, verbose_rows=None):
    target_classical = 2 * target_pq
    out = []
    for bname, bbits in BASES:
        for d in range(1, max_deg + 1):
            E = bbits * d
            for R in (1, 2, 3, 4):
                nu = T + R
                s = queries_for(R, nu, E, g, target_classical, T)
                if s is None:
                    continue
                c = classical_bits(R, nu, E, s, g, T)
                out.append(dict(base=bname, bbits=bbits, deg=d, E=E, R=R, s=s,
                                classical=c, pq=pq(c), nu=nu,
                                kib=proof_kib(nu, R, s, d, bbits),
                                prover=prover_relative(R, T)))
    return out


def sec(t):
    print("\n" + "=" * 96)
    print(t)
    print("=" * 96)


def report():
    T, G = 20, 32

    sec("1. IS 128-BIT PQ PROVABLE REACHABLE AT ALL? (trace 2^20, grind 32)")
    res = search(128, T, G)
    if not res:
        print("  No configuration in the search space reaches it.")
    else:
        res.sort(key=lambda r: r["kib"])
        print(f"  {'base':<11} {'deg':>4} {'E':>5} {'blowup':>7} {'s':>5} "
              f"{'classical':>10} {'PQ':>6} {'proof KiB':>10} {'prover x':>9}")
        print("  " + "-" * 82)
        for r in res[:12]:
            print(f"  {r['base']:<11} {r['deg']:>4} {r['E']:>5} {2**r['R']:>7} "
                  f"{r['s']:>5} {r['classical']:>10.1f} {r['pq']:>6.1f} "
                  f"{r['kib']:>10.1f} {r['prover']:>8.2f}x")
        b = res[0]
        print(f"\n  CHEAPEST BY PROOF SIZE: {b['base']}^{b['deg']} (E={b['E']}), "
              f"blowup {2**b['R']}, {b['s']} queries -> {b['kib']:.0f} KiB")

    sec("2. THE STRUCTURAL POINT: extension degree is cheap, base field is not")
    print("""
  The extension carries CHALLENGES, the DEEP point, and post-fold layer values.
  The trace, the constraint evaluation and the layer-0 LDE -- the prover's
  dominant cost per EFFICIENCY.md -- stay in the BASE field.

  So M31^9 (E=279) is NOT the same thing as a 279-bit prime field. The former
  keeps 31-bit machine-word arithmetic everywhere it matters and pays extension
  cost only on the fold and the openings. The latter pays 279-bit arithmetic on
  every trace element.

  This is why the small-field turn is not actually in tension with high provable
  soundness -- the tension was only ever with SMALL EXTENSION DEGREE. Degree 4
  was the wrong default, not the small base field.""")

    sec("3. WHAT EXTENSION DEGREE EACH PQ TARGET NEEDS (31-bit base, trace 2^20)")
    print(f"  {'target PQ':>10} {'classical':>10} {'min E':>7} {'min deg (31-bit)':>18} "
          f"{'deployed today':>16}")
    print("  " + "-" * 66)
    for tgt in (32, 50, 64, 80, 100, 128):
        best = None
        for d in range(1, 13):
            E = 31 * d
            for R in (1, 2, 3, 4):
                s = queries_for(R, T + R, E, G, 2 * tgt, T)
                if s is not None:
                    best = d
                    break
            if best:
                break
        print(f"  {tgt:>10} {2*tgt:>10} {31*(best or 0):>7} {str(best):>18} "
              f"{'4 (=124 bits)':>16}")

    sec("4. THE COST OF THE LAST BITS -- AND THE REAL TRADEOFF")
    print("""  Two objectives pull in OPPOSITE directions, which the first table in this
  file obscured by ranking on proof size alone:

    minimise PROOF SIZE  -> raise blowup (better yield/query -> fewer queries)
    minimise PROVER TIME -> lower blowup (the LDE is 2^R x the trace)

  So there is no single "cheapest" configuration. Both endpoints:\n""")
    print(f"  {'target':>7} | {'--- smallest proof ---':^34} | {'--- fastest prover ---':^34}")
    print(f"  {'PQ':>7} | {'config':<20}{'s':>5}{'KiB':>9} | {'config':<20}{'s':>5}{'KiB':>9}")
    print("  " + "-" * 88)
    for tgt in (32, 50, 64, 80, 100, 128):
        r = search(tgt, T, G)
        if not r:
            print(f"  {tgt:>7} | {'unreachable':<34} |")
            continue
        small = min(r, key=lambda x: x["kib"])
        fast = min(r, key=lambda x: (x["prover"], x["kib"]))
        def fmt(b):
            return (f"{b['base']}^{b['deg']} bl{2**b['R']:<3}", b["s"], b["kib"])
        cs, ss, ks = fmt(small)
        cf, sf, kf = fmt(fast)
        print(f"  {tgt:>7} | {cs:<20}{ss:>5}{ks:>9.0f} | {cf:<20}{sf:>5}{kf:>9.0f}")
    print("""
  The prover-optimal column runs blowup 2 (1.00x, the EFFICIENCY.md choice) and
  pays for it in queries and proof size. The proof-optimal column runs blowup 16
  and pays 9.1x on the LDE. Query count grows roughly linearly in the target in
  both, because every query is Merkle paths and nothing else buys query-phase
  bits.""")

    sec("5. WHY UDR, NOT JOHNSON")
    print("""
  At 256 classical bits every configuration sits far past the Theorem 7 crossover
  s* = (K_J(m_eq) - g)/y_UDR, so unique decoding wins on both axes at once: it
  has the higher ceiling AND it needs no list-decoding argument.

  That is a pleasant outcome for the resilience requirement. The most demanding
  soundness target lands on the WEAKEST assumption available -- no Johnson bound,
  no proximity gaps conjecture, no capacity conjecture (disproved in 2025 anyway),
  no MSIS. Just collision resistance and the random oracle.

  A 128-bit PQ provable STARK is, in assumption terms, the most conservative
  object in this entire repository. It is only expensive in queries.""")

    sec("6. THE RECOMMENDATION")
    r = search(128, T, G)
    if r:
        small = min(r, key=lambda x: x["kib"])
        fast = min(r, key=lambda x: (x["prover"], x["kib"]))
        small31 = min([x for x in r if x["bbits"] <= 32] or r, key=lambda x: x["kib"])
        print(f"""
  There is no single answer -- pick the endpoint that matches the constraint.

  PROVER-BOUND (a phone, a light client, anything where proving time dominates):
      {fast['base']}^{fast['deg']}  (E = {fast['E']}), blowup {2**fast['R']}, {fast['s']} queries, grind {G}
      -> {fast['classical']:.0f} classical / {fast['pq']:.0f} PQ bits, {fast['kib']:.0f} KiB proof, {fast['prover']:.2f}x LDE

  BANDWIDTH-BOUND (on-chain verification, where every byte is paid for):
      {small['base']}^{small['deg']}  (E = {small['E']}), blowup {2**small['R']}, {small['s']} queries, grind {G}
      -> {small['classical']:.0f} classical / {small['pq']:.0f} PQ bits, {small['kib']:.0f} KiB proof, {small['prover']:.2f}x LDE

  BEST 31-BIT OPTION (keeps machine-word arithmetic in the base field):
      {small31['base']}^{small31['deg']}  (E = {small31['E']}), blowup {2**small31['R']}, {small31['s']} queries
      -> {small31['classical']:.0f} classical / {small31['pq']:.0f} PQ bits, {small31['kib']:.0f} KiB proof

  In every case the extension degree is the load-bearing choice, and in every
  case it is far above the degree 4 that is deployed everywhere today.

  The whole cost of going from "post-quantum in the Shor sense" to "128 bits of
  provable post-quantum soundness" is: a larger extension degree, more queries,
  and a bigger proof. It does NOT require abandoning small fields, adopting a
  lattice assumption, or believing any conjecture. Proofs in the 1-2 MiB range
  are the honest price, which is why nobody currently pays it.""")


if __name__ == "__main__":
    report()
