"""
FRI / STARK concrete soundness model -- landscape pass.

Model follows ethSTARK Documentation v1.2 (Ben-Sasson, Goldberg, Kopparty,
Saraf), Sections 5-6, which instantiates BCIKS20 "Proximity Gaps for
Reed-Solomon Codes" (Ben-Sasson, Carmon, Ishai, Kopparty, Saraf).

Three proximity regimes, in increasing order of aggressiveness:

  unique       theta = (1-rho)/2            per-query err (1+rho)/2          [unconditional]
  johnson      theta = 1-sqrt(rho)(1+1/2m)  per-query err sqrt(rho)(1+1/2m)  [proven, BCIKS20]
  conjectured  theta = 1-rho                per-query err rho               [ethSTARK Conj. 1]

Two soundness terms compete:

  QUERY  phase: scales with the number of queries s and grinding g. Cheap to buy.
  COMMIT phase: bounded by extension field size E. CANNOT be bought with queries.

The central finding of this model is that for every 31-bit-field system the
binding constraint under the *proven* bound is COMMIT, not QUERY -- so those
systems' advertised 96-100 bits are conjecture-dependent by construction, not
by parameter choice.
"""

import math

# ============================================================ soundness terms

def bits_per_query(R, regime, m=16):
    """Security bits contributed by one FRI query. R = log2(blowup factor)."""
    rho = 2.0 ** (-R)
    if regime == "conjectured":
        return R
    if regime == "johnson":
        return -math.log2(math.sqrt(rho) * (1 + 1 / (2 * m)))
    if regime == "unique":
        return -math.log2((1 + rho) / 2)
    raise ValueError(regime)


def query_bits(R, s, g, regime, m=16):
    """s FRI queries plus g bits of proof-of-work grinding."""
    return s * bits_per_query(R, regime, m) + g


def queries_needed(R, lam, g, regime, m=16):
    per = bits_per_query(R, regime, m)
    return math.ceil(max(lam - g, 0) / per)


def commit_bits(R, nu, E, regime, m=16):
    """
    FRI commit-phase soundness -- the term bounded by extension field size.
    nu = log2(|D_0|) (evaluation domain), E = log2(|F_ext|).

      proven (BCIKS20):  eps_C <= (m+1/2)^7 / (3 rho^{3/2}) * |D_0|^2 / |F|
      conjectured:       eps_C ~= |D_0| / (rho * |F|)   (ethSTARK Conj. 1, c1=c2=1)
    """
    if regime == "conjectured":
        return E - nu - R
    return E + math.log2(3) - 7 * math.log2(m + 0.5) - 1.5 * R - 2 * nu


def deep_bits(nu, E, n_constraints=1, deg=2):
    """DEEP / out-of-domain sampling: ~ (deg * |D_0|) / |F_ext| per sampled point."""
    return E - nu - math.log2(max(deg * n_constraints, 1))


def total_bits(R, nu, E, s, g, regime, m=16):
    """Overall soundness = min over the competing terms. Returns (bits, binder)."""
    terms = [
        (query_bits(R, s, g, regime, m), "query"),
        (commit_bits(R, nu, E, regime, m), "commit"),
        (deep_bits(nu, E), "deep"),
    ]
    return min(terms)

# ================================================================= cost model

def fri_rounds(nu, R, arity_log=1, last_layer_log_deg=0):
    return max(0, math.ceil((nu - R - last_layer_log_deg) / arity_log))


def proof_bytes(nu, R, s, arity_log=1, hash_bytes=32, n_base_trees=2):
    """Dominant term: Merkle authentication paths, uncompressed."""
    base = n_base_trees * s * nu * hash_bytes
    fri = sum(s * max(nu - i * arity_log, 1) * hash_bytes
              for i in range(fri_rounds(nu, R, arity_log)))
    return base + fri


def verifier_hashes(nu, R, s, arity_log=1, n_base_trees=2):
    return (n_base_trees * s * nu
            + sum(s * max(nu - i * arity_log, 1)
                  for i in range(fri_rounds(nu, R, arity_log))))

# ================================================================== optimizer

def best_m(R, nu, E, s, g, regime, m_range=range(1, 129)):
    """
    The Johnson parameter m is a free knob nobody tunes: larger m buys per-query
    yield (-> sqrt(rho)) but costs commit-phase bits at rate 7*log2(m+1/2).
    Pick the m maximising overall soundness.
    """
    return max(((total_bits(R, nu, E, s, g, regime, m)[0], m) for m in m_range))


def max_provable_bits(R, nu, E, regime="johnson", s_cap=100000, g=0):
    """Ceiling on achievable soundness even with unlimited queries."""
    return max(min(commit_bits(R, nu, E, regime, m), deep_bits(nu, E))
               for m in range(1, 129))


def required_ext_bits(R, nu, lam, regime="johnson"):
    """Smallest extension field size E that admits lam bits under this regime."""
    for E in range(32, 1025):
        if max_provable_bits(R, nu, E, regime) >= lam:
            return E
    return None

# ================================================================== instances
# Field parameters are exact. Blowup / query / grinding columns are
# REPRESENTATIVE DEFAULTS FROM RECOLLECTION, not read from source -- these are
# the entries to verify before anyone leans on the per-system conclusions.

Instance = lambda name, family, p, ext, logn, R, s, g, note: dict(
    name=name, family=family, p=p, ext=ext, logn=logn, R=R, s=s, g=g, note=note)

INSTANCES = [
    Instance("Stwo (StarkWare)", "M31 / Circle STARK", 31, 4, 20, 1, 70, 20,
             "Mersenne31 = 2^31-1, QM31 degree-4 secure field"),
    Instance("Plonky3 (KoalaBear)", "KoalaBear", 31, 4, 20, 1, 80, 16,
             "2^31-2^24+1, degree-4 ext"),
    Instance("Plonky3 (BabyBear)", "BabyBear", 31, 4, 20, 2, 42, 16,
             "2^31-2^27+1, degree-4 ext"),
    Instance("RISC Zero", "BabyBear", 31, 4, 20, 2, 50, 0,
             "2^31-2^27+1, degree-4 ext"),
    Instance("Plonky2", "Goldilocks", 64, 2, 20, 3, 28, 16,
             "2^64-2^32+1, degree-2 ext"),
    Instance("Winterfell / Miden", "Goldilocks", 64, 3, 20, 3, 27, 16,
             "2^64-2^32+1, degree-3 ext"),
    Instance("Boojum (zkSync)", "Goldilocks", 64, 2, 20, 3, 28, 20,
             "2^64-2^32+1, degree-2 ext"),
    Instance("ethSTARK doc params", "~62-bit prime", 62, 1, 20, 4, 30, 0,
             "no extension; the paper that defines Conjecture 1"),
    Instance("Cairo / StarkNet", "251-bit prime", 251, 1, 20, 4, 30, 0,
             "2^251+17*2^192+1, no extension needed"),
]

OUT_OF_SCOPE = [
    ("Binius", "binary tower fields GF(2^k)",
     "Uses small-field binary towers with a different proximity analysis "
     "(Reed-Solomon over towers + packing). The RS-over-prime-field model here "
     "does not apply directly."),
    ("STIR / WHIR", "improved FRI successors",
     "Achieve better query complexity per bit by reducing rate each round "
     "(STIR) or via super-efficient sumcheck-based proximity (WHIR). Would "
     "shift the query-phase column, not the commit-phase ceiling."),
]

# ==================================================================== report

def sec(title):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def report():
    sec("1. PER-QUERY YIELD  (bits of security per FRI query, m=16 for Johnson)")
    print(f"{'blowup':>8} {'R':>4} {'unique':>10} {'johnson':>10} "
          f"{'conjectured':>13} {'conj/john':>11}")
    for R in (1, 2, 3, 4, 5):
        u, j, c = (bits_per_query(R, r) for r in ("unique", "johnson", "conjectured"))
        print(f"{2**R:>8} {R:>4} {u:>10.3f} {j:>10.3f} {c:>13.3f} {c/j:>10.2f}x")
    print("\n  The conjecture is worth a consistent ~2x in query count. That is the")
    print("  entire headline benefit, and it is uniform across blowup factors.")

    sec("2. QUERIES NEEDED FOR 100-BIT QUERY-PHASE SECURITY")
    print(f"{'blowup':>8} {'grind':>6} {'unique':>10} {'johnson':>10} "
          f"{'conjectured':>13} {'j-c saved':>11}")
    for R in (1, 2, 3, 4):
        for g in (0, 20):
            u, j, c = (queries_needed(R, 100, g, r)
                       for r in ("unique", "johnson", "conjectured"))
            print(f"{2**R:>8} {g:>6} {u:>10} {j:>10} {c:>13} {j-c:>11}")

    sec("3. LANDSCAPE  (trace 2^20, 32-byte hashes, arity 2)")
    print("Representative params per system; 'binder' = which term limits security.\n")
    hdr = (f"{'system':<24} {'E':>5} {'blowup':>7} {'s':>4} {'g':>4} "
           f"{'unique':>8} {'johnson':>9} {'conj':>8}  binder(john/conj)")
    print(hdr)
    print("-" * len(hdr))
    for i in INSTANCES:
        E, nu = i["p"] * i["ext"], i["logn"] + i["R"]
        res = {}
        for regime in ("unique", "johnson", "conjectured"):
            if regime == "johnson":
                b, m = best_m(i["R"], nu, E, i["s"], i["g"], regime)
                res[regime] = (b, total_bits(i["R"], nu, E, i["s"], i["g"], regime, m)[1])
            else:
                res[regime] = total_bits(i["R"], nu, E, i["s"], i["g"], regime)
        print(f"{i['name']:<24} {E:>5} {2**i['R']:>7} {i['s']:>4} {i['g']:>4} "
              f"{res['unique'][0]:>8.1f} {res['johnson'][0]:>9.1f} "
              f"{res['conjectured'][0]:>8.1f}  {res['johnson'][1]}/{res['conjectured'][1]}")

    sec("4. THE CEILING: max provable bits, unlimited queries")
    print("Even with s -> infinity, the commit-phase term caps proven soundness.\n")
    print(f"{'system':<24} {'E':>5} {'proven ceiling':>15} {'conj ceiling':>14} "
          f"{'E needed for 100':>17}")
    print("-" * 80)
    for i in INSTANCES:
        E, nu = i["p"] * i["ext"], i["logn"] + i["R"]
        pc = max_provable_bits(i["R"], nu, E, "johnson")
        cc = max_provable_bits(i["R"], nu, E, "conjectured")
        need = required_ext_bits(i["R"], nu, 100, "johnson")
        print(f"{i['name']:<24} {E:>5} {pc:>15.1f} {cc:>14.1f} {str(need):>17}")
    print("\n  Every 31-bit-field system sits far below 100 provable bits. Reaching")
    print("  100 unconditionally needs a substantially larger extension -- i.e. the")
    print("  small-field performance win is paid for in assumption strength.")

    sec("5. THE UNTUNED KNOB: Johnson parameter m")
    print("m trades per-query yield against commit-phase bits (penalty 7*log2(m+1/2)).")
    print("Almost no implementation exposes it. Optimal m for each system:\n")
    print(f"{'system':<24} {'m*':>4} {'bits at m*':>11} {'bits at m=16':>13} {'delta':>7}")
    print("-" * 64)
    for i in INSTANCES:
        E, nu = i["p"] * i["ext"], i["logn"] + i["R"]
        b_star, m_star = best_m(i["R"], nu, E, i["s"], i["g"], "johnson")
        b16 = total_bits(i["R"], nu, E, i["s"], i["g"], "johnson", 16)[0]
        print(f"{i['name']:<24} {m_star:>4} {b_star:>11.1f} {b16:>13.1f} "
              f"{b_star-b16:>+7.1f}")

    sec("6. OPTIMIZATION: cheapest 100-bit config, trace 2^20, E = 2^124")
    for regime in ("conjectured", "johnson"):
        print(f"\n  regime = {regime}")
        print(f"    {'blowup':>7} {'g':>4} {'s':>5} {'proof KiB':>10} "
              f"{'v-hashes':>10} {'prover FFT cost':>16}")
        best, any_row = None, False
        for R in (1, 2, 3, 4, 5):
            for g in (0, 16, 20, 24):
                nu = 20 + R
                if max_provable_bits(R, nu, 124, regime) < 100:
                    continue
                any_row = True
                s = queries_needed(R, 100, g, regime)
                pb = proof_bytes(nu, R, s) / 1024
                print(f"    {2**R:>7} {g:>4} {s:>5} {pb:>10.1f} "
                      f"{verifier_hashes(nu, R, s):>10,} {2**R:>15}x")
                if best is None or pb < best[0]:
                    best = (pb, R, g, s)
        if not any_row:
            ceil_ = max(max_provable_bits(R, 20 + R, 124, regime) for R in range(1, 6))
            print(f"    NO FEASIBLE CONFIG -- ceiling is {ceil_:.1f} bits at E=2^124.")
            print(f"    100-bit {regime} security is unreachable at this field size,")
            print(f"    at any query count or grinding level.")
        else:
            print(f"    -> min proof: blowup {2**best[1]}, g={best[2]}, "
                  f"s={best[3]}, {best[0]:.1f} KiB")

    sec("7. OUT OF MODEL SCOPE")
    for name, family, note in OUT_OF_SCOPE:
        print(f"\n  {name}  [{family}]")
        print(f"    {note}")


if __name__ == "__main__":
    report()
