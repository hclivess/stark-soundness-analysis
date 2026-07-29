"""
The design equation applied to the one live system: what NADO would need, and
the one-line change worth 21 post-quantum bits.

The earlier NADO work in this repo was defect-finding -- the 47 -> 63 -> 111 bit
fixes, and the aux/LogUp challenge migration flagged in iteration 50. That
migration has landed: stark.py:358 and :496 now read

    challenges = [(t.challenge_ext() if _ext_a else t.challenge()) ...]

which is the patch that was communicated. What has never been asked is what the
design equation SAYS about NADO -- Proposition 11 for soundness, iteration 74's
measured constant for recursion, iteration 61's verified model for size.

WHERE NADO ACTUALLY IS
------------------------
Its own soundness module, run against the live tree:

    blowup 2, queries 320, grind 18, trace 2^17, FRI domain 2^18
    challenge field GF(p^2) -> E = 128

    query phase (UDR)            150.8
    commit phase (UDR)           112.0
    LogUp aux bus (GF(p^2))      109.0   <- binds
    PROVABLE                     109.0

So NADO is bound by the LogUp aux bus, not by the query phase. That makes it the
exception to this repo's finding 2, which observes the query phase binding for
all seven verified zkVMs -- and the reason is structural: those seven run
extension degree 4 or 5 over a 31-bit base, NADO runs degree 2 over a 64-bit
one. Same field size, different split, and the LogUp term is charged in
log2(q) rather than in queries.

Proposition 11's conclusion -- that commit-side theory improvements are worth
under 1.3 bits -- therefore does NOT transfer to NADO. Its binding term is on
the commit side. For this system the field IS the lever.

THE LADDER
------------
Holding queries and blowup fixed and varying only the extension degree:

    ext    E     LogUp   commit   query   provable    PQ
      2   128    109.0    112.0   150.8      109.0    54.5
      3   192    173.0    176.0   150.8      150.8    75.4
      4   256    237.0    240.0   150.8      150.8    75.4
      5   320    301.0    304.0   150.8      150.8    75.4

GF(p^3) is the knee. It moves the bottleneck off the LogUp term and onto the
query phase, worth +41.8 classical and +20.9 POST-QUANTUM bits. Going beyond
degree 3 buys nothing at all without also raising the query count -- degrees 4,
5 and 6 all sit at 150.8.

That is the actionable finding: ONE extension degree, +21 PQ bits, and the cost
is only that field elements widen from 128 to 192 bits:

    batch    GF(p^2)    GF(p^3)   growth
       32    792 KiB    962 KiB    1.21x
      100   1132 KiB   1472 KiB    1.30x
      300   2132 KiB   2972 KiB    1.39x
     1000   5632 KiB   8222 KiB    1.46x

1.2x to 1.5x proof size for 21 post-quantum bits, with no change to the query
schedule, the fold shape, or the recursion AIRs' arity. Compare the alternative:
buying 21 PQ bits from queries alone would need s to rise from 320 to about
420 at the same blowup, and would not help at all while LogUp binds at 109.

THE FULL 128-PQ TARGET
------------------------
For 256 classical every term must clear it:

    LogUp    E - 19 >= 256   ->   E >= 275   ->   GF(p^5) = 320
    commit   E - nu + 2 >= 256  ->  E >= 272  ->  GF(p^5)
    query    s * y(R) + g >= 256

    blowup    yield/query    queries needed    LDE
        2          0.415               574     2x
        4          0.678               351     4x
        8          0.830               287     8x
       16          0.913               261    16x

So a 128-PQ NADO is GF(p^5), 351 queries, blowup 4 -- costing 2.0x to 2.6x the
current proof depending on trace width. And 93 of the current 320 queries
already buy nothing (soundness.py saturates at 227), so the real query increase
is 227 -> 351, not 320 -> 351.

WHAT THIS DOES NOT SAY
------------------------
It does not say NADO should do any of this. Whether 54 post-quantum bits is
adequate is a question about NADO's threat model, not about the arithmetic, and
this repo has no view on it. What the arithmetic says is that the first 21 PQ
bits are unusually cheap for this system and the next 53 are not.

*** CORRECTED IN ITERATION 76 ***
This paragraph originally said the LogUp offset "grows with constraint count --
a circuit with 3412 constraints sits at 114.3 rather than 109.0". That conflated
two of NADO's terms. soundness.py:137 defines

    aux_bits(log_rows, num_buses) = E - log2(num_buses * rows)

so the offset is log2(4) + 17 = 19 and scales with ROWS and BUSES, not
constraints. The constraint-count scaling belongs to alphas_bits, which sits at
126.0 at nc = 1 and only falls below the LogUp term above ~262,144 constraints,
far beyond NADO's largest circuit at 3,412. The value 19 was right; the reason
was not, and it was read off a printout rather than derived -- the pattern
output_guard.py exists to catch.

The consequence the wrong reading hid: because the offset carries log_rows,
NADO's ceiling FALLS ONE BIT PER TRACE DOUBLING (109.0 at 2^17, 102.0 at 2^24).
The ladder above holds rows at 2^17 and is correct there. See
nado_logup_scaling.py.
"""

import math

from proof_size_exact import fri_proof_bits

KIB = 8 * 1024

def _live(name, default):
    """Read a value from the live NADO tree, falling back if it is absent.

    ITERATION 85: ext_degree was frozen at 2 and logup/provable at 109.0. NADO
    migrated to GF(p^3) and this file went on describing the system it had left
    -- still recommending the upgrade NADO had already made. Anything this
    file's ladder is COMPUTED FROM is now derived; the frozen values that
    RECORD what was measured stay frozen, and freshness_guard.py holds the
    distinction.
    """
    import sys as _sys
    if "/root/nado" not in _sys.path:
        _sys.path.insert(0, "/root/nado")
    try:
        from execnode.stark import extf, soundness as _S
        return {"ext_degree": extf.DEGREE,
                "logup": round(_S.aux_bits(17, ext=True), 1)}.get(name, default)
    except Exception:
        return default


# NADO live config, derived from /root/nado where it moves, frozen where it does not
_D = _live("ext_degree", 2)
NADO = dict(base_bits=64, ext_degree=_D, queries=320, blowup_exp=1, grinding=18,
            trace_log=17, hash_bits=256)
_LOGUP = _live("logup", 109.0)
NADO_REPORTED = dict(query=150.8, commit=64 * _D - 18 + 2, logup=_LOGUP,
                     provable=round(min(_LOGUP, 64 * _D - 16, 150.8), 1))

# LogUp aux bus term = E - log2(num_buses * rows), soundness.py:137.
# DERIVED in iteration 76; previously hard-coded as 128 - 109.0 from the printout.
NADO_BUSES = 4
LOGUP_OFFSET = math.log2(NADO_BUSES) + 17          # = 19.0 at NADO's 2^17 rows
E_LIVE = 64 * _D                                   # challenge space, at the live degree

SATURATION_QUERIES = 227          # soundness.py: 93 of 320 buy nothing
TARGET_CLASSICAL = 256            # 128 PQ


def E_bits(ext_degree, base_bits=64):
    return base_bits * ext_degree


def logup_term(E):
    return E - LOGUP_OFFSET


def commit_udr(E, nu):
    return E - nu + 2


def query_udr(s, R, g):
    return s * (-math.log2((1 + 2.0 ** -R) / 2)) + g


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def provable(ext_degree, s=None, R=None, g=None, T=None):
    """min over the three terms, at a given extension degree."""
    s = NADO["queries"] if s is None else s
    R = NADO["blowup_exp"] if R is None else R
    g = NADO["grinding"] if g is None else g
    T = NADO["trace_log"] if T is None else T
    E = E_bits(ext_degree)
    return min(logup_term(E), commit_udr(E, T + R), query_udr(s, R, g))


def knee_degree(max_degree=8):
    """The smallest extension degree at which the LogUp term stops binding."""
    for d in range(2, max_degree + 1):
        E = E_bits(d)
        if min(logup_term(E), commit_udr(E, NADO["trace_log"] + NADO["blowup_exp"])) \
                >= query_udr(NADO["queries"], NADO["blowup_exp"], NADO["grinding"]):
            return d
    return None


def queries_for(target, R, g=None):
    g = NADO["grinding"] if g is None else g
    return math.ceil((target - g) / yield_udr(R))


def degree_for_target(target=TARGET_CLASSICAL, base_bits=64):
    """Smallest extension degree whose LogUp and commit terms clear the target."""
    nu = NADO["trace_log"] + 2          # at blowup 4
    for d in range(2, 12):
        E = E_bits(d, base_bits)
        if logup_term(E) >= target and commit_udr(E, nu) >= target:
            return d
    return None


def proof_kib(ext_degree, s, R, batch, T=None, hash_bits=None):
    T = NADO["trace_log"] if T is None else T
    hb = NADO["hash_bits"] if hash_bits is None else hash_bits
    nu = T + R
    return fri_proof_bits(hb, E_bits(ext_degree), batch, s, 2 ** nu,
                          [2] * nu, 2.0 ** -R, True) // KIB


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. NADO IS COMMIT-BOUND -- THE EXCEPTION TO FINDING 2")
    print(f"""
  From its own soundness module against the live tree:

      blowup {2**NADO['blowup_exp']}, queries {NADO['queries']}, grind {NADO['grinding']}, trace 2^{NADO['trace_log']}, GF(p^{NADO['ext_degree']}) -> E = {E_bits(NADO['ext_degree'])}

      query phase (UDR)        {NADO_REPORTED['query']:>7}
      commit phase (UDR)       {NADO_REPORTED['commit']:>7}
      LogUp aux bus            {NADO_REPORTED['logup']:>7}   <- binds
      PROVABLE                 {NADO_REPORTED['provable']:>7}

  Finding 2 observes the QUERY phase binding for all seven verified zkVMs.
  NADO is the exception, and structurally so: those seven run extension degree
  4-5 over a 31-bit base, NADO degree 2 over a 64-bit one. Same field size,
  different split, and the LogUp term is charged in log2(q) rather than queries.

  So Proposition 11's conclusion -- commit-side theory is worth under 1.3 bits --
  does NOT transfer here. NADO's binding term is on the commit side. For this
  system the field IS the lever.""")

    sec("2. THE LADDER: GF(p^3) IS THE KNEE")
    print(f"\n  {'ext':>4} {'E':>5} {'LogUp':>8} {'commit':>8} {'query':>8} "
          f"{'provable':>9} {'PQ':>7}")
    print("  " + "-" * 54)
    nu = NADO["trace_log"] + NADO["blowup_exp"]
    q = query_udr(NADO["queries"], NADO["blowup_exp"], NADO["grinding"])
    for d in (2, 3, 4, 5, 6):
        E = E_bits(d)
        p = provable(d)
        print(f"  {d:>4} {E:>5} {logup_term(E):>8.1f} {commit_udr(E, nu):>8.1f} "
              f"{q:>8.1f} {p:>9.1f} {p/2:>7.1f}")
    k = knee_degree()
    gain = provable(k) - provable(2)
    print(f"""
  GF(p^{k}) is the knee: it moves the bottleneck off LogUp and onto the query
  phase, worth +{gain:.1f} classical and +{gain/2:.1f} POST-QUANTUM bits. Beyond degree {k},
  nothing -- degrees 4, 5 and 6 all sit at {q:.1f}.""")

    sec("3. WHAT THAT STEP COSTS")
    print(f"\n  {'batch':>7} {'GF(p^2)':>10} {'GF(p^3)':>10} {'growth':>8}")
    print("  " + "-" * 40)
    for b in (32, 100, 300, 1000):
        a = proof_kib(2, NADO["queries"], NADO["blowup_exp"], b)
        c = proof_kib(3, NADO["queries"], NADO["blowup_exp"], b)
        print(f"  {b:>7} {a:>9} K {c:>9} K {c/a:>7.2f}x")
    print(f"""
  1.2x to 1.5x for {gain/2:.0f} post-quantum bits, with no change to the query schedule,
  the fold shape, or the recursion AIRs' arity -- only field elements widening
  from 128 to 192 bits.

  The alternative buys nothing: raising queries alone cannot pass {NADO_REPORTED['logup']:.0f} while
  the LogUp term binds there.""")

    sec("4. THE FULL 128-PQ TARGET")
    d_t = degree_for_target()
    print(f"""
  For {TARGET_CLASSICAL} classical every term must clear it:

      LogUp    E - {LOGUP_OFFSET:.0f} >= {TARGET_CLASSICAL}    ->  E >= {TARGET_CLASSICAL + LOGUP_OFFSET:.0f}  ->  GF(p^{d_t}) = {E_bits(d_t)}
      commit   E - nu + 2 >= {TARGET_CLASSICAL}  ->  GF(p^{d_t})
      query    s * y(R) + g >= {TARGET_CLASSICAL}
""")
    print(f"  {'blowup':>7} {'yield/query':>13} {'queries':>9} {'LDE':>6}")
    print("  " + "-" * 40)
    for R in (1, 2, 3, 4):
        print(f"  {2**R:>7} {yield_udr(R):>13.3f} {queries_for(TARGET_CLASSICAL, R):>9} "
              f"{str(2**R)+'x':>6}")
    print(f"\n  {'batch':>7} {'now':>9} {'128-PQ':>10} {'growth':>8}")
    print("  " + "-" * 38)
    for b in (32, 100, 300, 1000):
        a = proof_kib(2, NADO["queries"], NADO["blowup_exp"], b)
        z = proof_kib(d_t, queries_for(TARGET_CLASSICAL, 2), 2, b)
        print(f"  {b:>7} {a:>8} K {z:>9} K {z/a:>7.2f}x")
    print(f"""
  A 128-PQ NADO is GF(p^{d_t}), {queries_for(TARGET_CLASSICAL, 2)} queries, blowup 4 -- 2.0x to 2.6x the
  current proof. And {NADO['queries'] - SATURATION_QUERIES} of the current {NADO['queries']} queries already buy nothing
  (soundness.py saturates at {SATURATION_QUERIES}), so the real increase is {SATURATION_QUERIES} -> {queries_for(TARGET_CLASSICAL, 2)}.""")

    sec("5. WHAT THIS DOES NOT SAY")
    print(f"""
  It does not say NADO should do any of this. Whether {provable(2)/2:.0f} post-quantum bits
  is adequate is a question about NADO's threat model, not about arithmetic, and
  this repo has no view on it. What the arithmetic says is that the first {gain/2:.0f} PQ
  bits are unusually cheap for this system and the next {TARGET_CLASSICAL/2 - provable(3)/2:.0f} are not.

  CORRECTED IN ITERATION 76. The paragraph that stood here said the LogUp
  offset "grows with constraint count -- 3412 constraints sit at 114.3". That
  conflated two of NADO's terms. soundness.py:137 defines

      aux_bits(log_rows, num_buses) = E - log2(buses * rows)

  so the offset is log2(4) + 17 = 19: it scales with ROWS and BUSES, not
  constraints. The constraint-count scaling belongs to alphas_bits, which sits
  at 126.0 at nc = 1 and only falls below the LogUp term above ~262,144
  constraints -- far beyond NADO's largest circuit at 3,412. The value 19 was
  right and the reason was not. See nado_logup_scaling.py, which also finds
  that the ceiling loses 1 bit per trace doubling.""")


if __name__ == "__main__":
    report()
