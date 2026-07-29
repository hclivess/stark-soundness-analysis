"""
nu has driven three separate findings and was never treated as a variable. It is
free for soundness -- until a wall, and SP1 and OpenVM are 2-3 bits from it.

nu = log2 of the evaluation domain has appeared as the decisive quantity three
times: Proposition 9's structural gap is nu + log2(fold) + 1, iteration 76 found
NADO's ceiling falling one bit per trace doubling, and iteration 86 found the
fold-arity optimum switching at nu >= 21. Every time it was read off a config as
given. This asks whether there is slack in it.

FIRST, IT IS FREE
-------------------
Proposition 11 fixes achievable soundness at s*y(R) + g for a query-bound
system, and that expression contains no nu. So growing the domain costs proof
size and prover work and buys nothing, but it also COSTS nothing in security:

    nu    query term   commit bound (a=1, E=124)   binds
    18         100.1                       108.0   query
    21         100.1                       105.0   query
    24         100.1                       102.0   query
    27         100.1                        99.0   COMMIT
    30         100.1                        96.0   COMMIT

THEN THERE IS A WALL
----------------------
The commit bound is E - nu + 2 and falls one bit per doubling. It overtakes the
query term at

    nu_max = E + 2 - (s*y(R) + g)                            (Proposition 12)

Past that the system is commit-bound, and every further doubling costs a bit of
security outright. Measured across the deployed set:

    system      reg  nu   query  nu_max  headroom   trace x
    SP1         UDR  23   100.1    25.9       2.9        8x
    OpenVM      UDR  24   100.1    25.9       1.9        4x
    Airbender   JBR  25    67.4    58.6      33.6     2^34x
    Pico        JBR  23    54.0    72.0      49.0     2^49x
    ZisK        JBR  22   127.2    66.8      44.8     2^45x
    RISC Zero   JBR  23    48.2    77.8      54.8     2^55x
    Miden       JBR  21    55.8    74.2      53.2     2^53x
    NADO        UDR  18   150.8    43.2      25.2     2^25x

A sharp split. SP1 can grow its trace 8x before the commit bound takes over;
OpenVM 4x. Every other system has 25 to 55 bits of headroom -- no practical
limit at all.

WHY THE TWO UDR SYSTEMS ARE THE TIGHT ONES
--------------------------------------------
The headroom is E + 2 - query - nu, so it is squeezed from both sides by a high
query term. SP1 and OpenVM report 100.1 against E = 124, leaving 25.9 for a
domain already at 23-24. The JBR systems report 48-67 against the same or
larger E, leaving 59-78.

That is the cost of the unique-decoding regime showing up somewhere new. UDR
buys a clean commit bound with no proximity parameter (iteration 33's a = 0),
and this repo has treated the choice as free where the query phase binds. It is
free for SOUNDNESS. It is not free for SCALE: a system that spends its field on
a high query term has little left for domain size.

WHAT THIS DOES AND DOES NOT MEAN
----------------------------------
DOES NOT mean SP1 or OpenVM are misconfigured. Both prove chunks, not whole
executions -- SP1's core is trace 2^21, and a longer computation is handled by
more chunks and recursion, not a longer trace. Chunking sidesteps the wall
entirely, which is presumably part of why it is universal.

DOES mean the chunk size is bounded above by something other than memory. The
usual reason to cap a chunk is prover RAM; this says there is a SOUNDNESS cap
too, at 4-8x their current size, and it arrives without warning -- the system
does not degrade gradually, it flips from query-bound to commit-bound and then
loses a bit per doubling.

DOES also mean the fold-arity result from iteration 86 has a boundary. That
found the proof-size and verifier-work optima agreeing above nu = 21. Combined
with this: nu is free to grow to nu_max, and the fold optimum is stable in
[21, nu_max]. For SP1 and OpenVM that window is [21, 25.9] -- they are inside
it. For NADO, nu = 18 is BELOW it, which is why iteration 86 found its optima
disagreeing.

WHAT IS NOT MODELLED
----------------------
Recursion cost as a function of chunk count. Halving the chunk size doubles the
number of proofs to aggregate, and iteration 74's constant prices the aggregation
but not the tree of it. The trade "one long trace versus many short ones" needs
that, and this file does not do it -- it establishes only that the long-trace
direction has a hard stop, and where.
"""

import math

from soundcalc_lean import jbr_m

# (name, E, R, T, s, g, regime) -- T is the TRACE length, matching systems.py's
# canonical column order exactly. This first stored nu in the third slot, which
# systems.drift() caught: same tuple shape, different column meaning, which is
# precisely the hazard that detector exists for. nu is derived below.
SYSTEMS = [
    ("SP1", 124, 2, 21, 124, 16, "UDR"),
    ("OpenVM", 124, 1, 23, 193, 20, "UDR"),
    ("Airbender", 124, 1, 24, 87, 28, "JBR"),
    ("Pico", 124, 1, 22, 84, 16, "JBR"),
    ("ZisK", 192, 1, 21, 229, 16, "JBR"),
    ("RISC Zero", 124, 2, 21, 50, 0, "JBR"),
    ("Miden", 128, 3, 18, 27, 16, "JBR"),
    ("NADO", None, 1, 17, 320, 18, "UDR"),      # E derived: see _nado_E()
]


def _nado_E():
    """NADO's challenge space, read live. Its extension module has alternated
    between `extf` (parameterised, degree 3) and `ext2` (degree 2) across
    checkouts, so freezing this guarantees it is wrong half the time."""
    import sys as _s
    if "/root/nado" not in _s.path:
        _s.path.insert(0, "/root/nado")
    for name in ("extf", "ext2"):
        try:
            m = __import__(f"execnode.stark.{name}", fromlist=[name])
            return 64 * getattr(m, "DEGREE", 2)
        except Exception:
            continue
    return 128


SYSTEMS = [r if r[1] is not None else (r[0], _nado_E()) + r[2:]
           for r in SYSTEMS]


def nu(row):
    """nu = T + R, derived rather than stored -- see the note above."""
    return row[3] + row[2]

FOLD_STABLE_FROM = 21           # iteration 86: the arity optima agree above this


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, E):
    m = float(jbr_m(2.0 ** -R, E))
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("nan")


def query_term(row):
    _n, E, R, _T, s, g, reg = row
    return s * (yield_udr(R) if reg == "UDR" else yield_jbr(R, E)) + g


def commit_bound(E, nu):
    """BCHKS25 at a = 1, log2 C = -2. Falls one bit per doubling."""
    return E - nu + 2


def nu_max(row):
    """PROPOSITION 12: E + 2 - (s*y(R) + g). Past this the commit bound binds."""
    _n, E, _R, _T, _s, _g, _reg = row
    return E + 2 - query_term(row)


def headroom(row):
    """Doublings of domain still available. NEGATIVE means the system is
    already commit-bound -- its query term is not achievable at this nu, so
    the wall is behind it rather than ahead. NADO at E = 128 is the example:
    commit 112 against a query term of 150.8."""
    return nu_max(row) - nu(row)


def already_past_wall(row):
    return headroom(row) < 0


def binds_at(row, at_nu):
    _n, E, _R, _T, _s, _g, _reg = row
    return "query" if query_term(row) < commit_bound(E, at_nu) else "commit"


def fold_window(row):
    """[21, nu_max] -- where iteration 86's arity result is stable."""
    return FOLD_STABLE_FROM, nu_max(row)


def in_fold_window(row):
    lo, hi = fold_window(row)
    return lo <= nu(row) <= hi


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. nu IS FREE FOR SOUNDNESS -- THE QUERY TERM DOES NOT CONTAIN IT")
    row = SYSTEMS[0]
    print(f"\n  SP1's parameters, varying only the domain:\n")
    print(f"  {'nu':>4} {'query term':>12} {'commit bound':>14} {'binds':>8}")
    print("  " + "-" * 42)
    for _nu in (18, 21, 24, 27, 30):
        print(f"  {_nu:>4} {query_term(row):>12.1f} "
              f"{commit_bound(row[1], _nu):>14.1f} {binds_at(row, _nu):>8}")
    print("""
  Proposition 11 fixes achievable soundness at s*y(R) + g, which carries no nu.
  So growing the domain costs size and prover work and buys nothing -- but it
  costs nothing in security either, until the commit bound catches up.""")

    sec("2. PROPOSITION 12: THE WALL, AND WHO IS NEAR IT")
    print(f"""
      nu_max = E + 2 - (s*y(R) + g)

  Past it the system is commit-bound and every further doubling costs a bit
  outright.\n""")
    print(f"  {'system':<11} {'reg':>4} {'nu':>4} {'query':>8} {'nu_max':>8} "
          f"{'headroom':>10} {'trace x':>10}")
    print("  " + "-" * 60)
    for r in SYSTEMS:
        h = headroom(r)
        tx = f"{2**h:.0f}x" if h < 30 else f"2^{h:.0f}x"
        print(f"  {r[0]:<11} {r[6]:>4} {nu(r):>4} {query_term(r):>8.1f} "
              f"{nu_max(r):>8.1f} {h:>10.1f} {tx:>10}")
    tight = [r[0] for r in SYSTEMS if 0 <= headroom(r) < 5]
    past = [r[0] for r in SYSTEMS if already_past_wall(r)]
    print(f"""
  A sharp split. {', '.join(tight)} sit under 5 bits of headroom. Everything else
  has 25 to 55, which is no practical limit.
""" + (f"  {', '.join(past)} shows NEGATIVE headroom: its commit bound is already\n"
       f"  below its query term, so the wall is behind it, not ahead. That is the\n"
       f"  signature of a commit-bound system." if past else ""))

    sec("3. WHY THE TIGHT ONES ARE THE UDR SYSTEMS")
    print("""
  Headroom is E + 2 - query - nu, squeezed from both sides by a high query term.
  SP1 and OpenVM report 100.1 against E = 124, leaving 25.9 for a domain already
  at 23-24. The JBR systems report 48-67 against the same or larger E.

  That is the unique-decoding choice showing up somewhere new. UDR buys a clean
  commit bound with no proximity parameter, and this repo has treated the choice
  as free where the query phase binds. It is free for SOUNDNESS. It is not free
  for SCALE -- a system that spends its field on a high query term has little
  left for domain size.""")

    sec("4. WHAT IT MEANS, AND THE BOUNDARY IT PUTS ON ITERATION 86")
    print(f"\n  {'system':<11} {'nu':>4} {'fold window':>16} {'inside?':>9}")
    print("  " + "-" * 44)
    for r in SYSTEMS:
        lo, hi = fold_window(r)
        print(f"  {r[0]:<11} {nu(r):>4} {f'[{lo}, {hi:.0f}]':>16} "
              f"{str(in_fold_window(r)):>9}")
    print("""
  Iteration 86 found the proof-size and verifier-work optima agreeing above
  nu = 21. Combined with the wall, the arity result is stable exactly on
  [21, nu_max]. NADO at nu = 18 is BELOW that window, which is why its optima
  disagreed.

  DOES NOT mean SP1 or OpenVM are misconfigured -- both prove CHUNKS, and a
  longer computation means more chunks plus recursion, not a longer trace.
  Chunking sidesteps the wall, which is presumably part of why it is universal.

  DOES mean chunk size has a soundness cap, not just a memory one, at 4-8x
  their current size -- and it arrives without warning: the system does not
  degrade gradually, it flips regime and then loses a bit per doubling.

  NOT MODELLED: recursion cost as a function of chunk count. Halving the chunk
  doubles the proofs to aggregate; iteration 74's constant prices one
  aggregation but not the tree. "One long trace versus many short ones" needs
  that. This establishes only that the long-trace direction has a hard stop,
  and where it is.""")


if __name__ == "__main__":
    report()
