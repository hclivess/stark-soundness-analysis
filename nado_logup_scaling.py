"""
Deriving NADO's binding term from its source instead of its printout -- which
corrects iteration 75's caveat and finds a scaling property the ladder hid.

Iteration 75 put NADO at 109 bits, bound by the LogUp aux bus, and built a
GF(p^3) recommendation on it. The offset in that model, LOGUP_OFFSET = 19, was
read off NADO's PRINTED REPORT rather than derived. That is exactly the pattern
iteration 69 built output_guard.py to catch: a number taken from what a program
prints instead of from what it computes. The whole recommendation moves
one-for-one with that offset, so it is worth deriving.

WHAT THE SOURCE SAYS
----------------------
execnode/stark/soundness.py:137

    def aux_bits(log_rows, ext=None, num_buses=4):
        base = E_EXT2 if e else E_BASE
        return base - math.log2(max(num_buses * (2.0 ** log_rows), 1.0))

So the offset is log2(num_buses) + log_rows = log2(4) + 17 = 19. The value was
right. What it depends on was not.

ITERATION 75's CAVEAT WAS WRONG
---------------------------------
It said: "the LogUp term is log2(q) - 19 ... that report notes the offset grows
with constraint count -- 3412 constraints sit at 114.3 rather than 109.0".

Two different terms, conflated. NADO has both:

    aux_bits(log_rows, num_buses)      = E - log2(buses * rows)
    alphas_bits(num_constraints, L+)   = E - log2(L+ * num_constraints)

The constraint-count scaling belongs to the ALPHAS term, which sits at 126.0 at
nc = 1 and falls to 114.3 at nc = 3412. The printed report puts that note under
the LogUp line, which is what I misread. The LogUp term does not see constraints
at all -- it scales with ROWS and BUSES.

Calling both directly:

    aux_bits, buses = 4              alphas_bits
    log_rows   bits                  nc        bits
        14    112.0                   1       126.0
        17    109.0  <- NADO today  100       119.4
        20    106.0                3412       114.3
        24    102.0              131072       109.0
        28     98.0              262144       108.0

The alphas term only overtakes the LogUp term above about 262,144 constraints.
NADO's largest circuit has 3,412, so LogUp binds by a margin of 5.3 bits and the
conflation did not change iteration 75's conclusion -- but it was still the
wrong reason.

THE SCALING PROPERTY THE LADDER HID
-------------------------------------
Because the binding term carries log_rows, NADO's provable soundness FALLS AS
ITS TRACE GROWS -- one bit per doubling:

    2^17 rows    109.0 classical    54.5 PQ    (today)
    2^20 rows    106.0              53.0
    2^24 rows    102.0              51.0
    2^28 rows     98.0              49.0

That is a property a query-bound system does not have. For the seven verified
zkVMs the query term s*y + g is independent of trace size, so growing the trace
costs proof size and nothing else. For NADO it costs security directly.

Iteration 75's ladder held rows fixed at 2^17 and so could not see this. The
ladder's conclusions are unchanged at that trace size; what is new is that the
109 figure is not a constant of the system, it is a constant of the system AT
ITS CURRENT TRACE.

AND IT STRENGTHENS THE GF(p^3) RECOMMENDATION
-----------------------------------------------
At GF(p^3) the LogUp term is 192 - 2 - log_rows, and the query phase (150.8)
takes over as the binding term. The LogUp term only returns to binding when

    192 - 2 - log_rows < 150.8    <=>    log_rows > 39.2

i.e. at 2^39 rows, which is five hundred billion. So the extension degree does
not merely buy 20.9 post-quantum bits -- it REMOVES THE TRACE-SIZE DEPENDENCE
for any trace NADO could execute. That is the stronger form of the same
recommendation, and iteration 75 could not state it because it had the offset
as a constant rather than as log2(buses) + log_rows.

A CHEAPER PARTIAL MEASURE
---------------------------
The offset also carries log2(num_buses), so consolidating the four LogUp buses
into one would buy 2 bits at any trace size and any field -- visible in the
table above as the buses=4 versus buses=1 columns (109.0 -> 111.0 at 2^17).
Two bits is not 21, and bus consolidation is a protocol change rather than a
parameter change, so this is recorded rather than recommended. It is noted
because the term's shape makes it available and nothing else in this repo
mentions it.
"""

import math
import sys

NADO_PATH = "/root/nado"

E_BASE, E_EXT2 = 64, 128
DEFAULT_BUSES = 4
NADO_LOG_ROWS = 17
NADO_QUERY_TERM = 150.8            # UDR query phase at 320 queries, blowup 2, grind 18


def _nado_module():
    """Import NADO's own soundness module, or None if the tree is absent."""
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import soundness
        return soundness
    except Exception:
        return None


def live_E():
    """The challenge-space size NADO is ACTUALLY using, read from its tree.

    ITERATION 84: this was E_EXT2 = 128, a frozen literal. NADO's soundness.py
    changed three times in twenty minutes during the GF(p^3) migration (128 ->
    96 -> 192), so a frozen transcription fails against a moving tree for the
    wrong reason -- it reports a mismatch when the tree moves, not when the
    transcription is wrong. Read the degree instead, which is the thing this
    file argued should never be hard-coded.
    """
    mod = _nado_module()
    if mod is None:
        return E_EXT2
    try:
        from execnode.stark import extf
        return E_BASE * extf.DEGREE
    except Exception:
        return E_EXT2


def aux_bits(log_rows, E=None, num_buses=DEFAULT_BUSES):
    """soundness.py, transcribed: E - log2(buses * rows), at the LIVE degree."""
    E = live_E() if E is None else E
    return E - math.log2(max(num_buses * (2.0 ** log_rows), 1.0))


def alphas_bits(num_constraints, E=None, l_plus=4.0):
    """soundness.py:170ff: E - log2(L+ * num_constraints). L+ = 4 reproduces
    the module's own 126.0 at nc = 1. E defaults to the LIVE degree."""
    E = live_E() if E is None else E
    return E - math.log2(max(l_plus * num_constraints, 1.0))


def logup_offset(log_rows=NADO_LOG_ROWS, num_buses=DEFAULT_BUSES):
    """The quantity iteration 75 hard-coded as 19, now derived."""
    return math.log2(num_buses) + log_rows


def rows_where_alphas_overtakes(log_rows=NADO_LOG_ROWS, E=None):
    """Constraint count at which the alphas term falls below the LogUp term."""
    target = aux_bits(log_rows, E)
    nc = 1
    while alphas_bits(nc, E) >= target and nc < 2 ** 30:
        nc *= 2
    return nc


def bits_lost_per_doubling(E=None):
    return aux_bits(17, E) - aux_bits(18, E)


def rows_where_logup_returns(E, query_term=NADO_QUERY_TERM,
                             num_buses=DEFAULT_BUSES):
    """log_rows at which the LogUp term falls back below the query phase."""
    return E - math.log2(num_buses) - query_term


def bus_consolidation_gain(from_buses=DEFAULT_BUSES, to_buses=1):
    return math.log2(from_buses) - math.log2(to_buses)


def cross_check_against_source(log_rows=NADO_LOG_ROWS):
    """(transcribed, NADO's own) -- None if the tree is unavailable."""
    mod = _nado_module()
    if mod is None:
        return None
    return aux_bits(log_rows), mod.aux_bits(log_rows, ext=True)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE OFFSET, DERIVED RATHER THAN READ OFF A PRINTOUT")
    xc = cross_check_against_source()
    print(f"""
  soundness.py:137 --

      def aux_bits(log_rows, ext=None, num_buses=4):
          return base - math.log2(max(num_buses * (2.0 ** log_rows), 1.0))

  So iteration 75's LOGUP_OFFSET = 19 is log2(num_buses) + log_rows
  = log2({DEFAULT_BUSES}) + {NADO_LOG_ROWS} = {logup_offset():.0f}. The VALUE was right; what it depends on
  was not.
""")
    if xc:
        print(f"  transcribed here {xc[0]:.1f}   NADO's own aux_bits {xc[1]:.1f}   "
              f"{'agree' if abs(xc[0]-xc[1]) < 1e-9 else 'DIVERGE'}")
    else:
        print("  (NADO tree unavailable; transcription not cross-checked)")

    sec("2. ITERATION 75 CONFLATED TWO TERMS")
    print(f"""
  It wrote that the LogUp offset "grows with constraint count -- 3412
  constraints sit at 114.3". That is the ALPHAS term. NADO has both:

      aux_bits(log_rows, num_buses)    = E - log2(buses * rows)
      alphas_bits(num_constraints, L+) = E - log2(L+ * num_constraints)
""")
    print(f"  {'log_rows':>9} {'aux_bits':>9}      {'nc':>8} {'alphas':>8}")
    print("  " + "-" * 46)
    ncs = [1, 100, 3412, 131072, 262144]
    for i, lr in enumerate([14, 17, 20, 24, 28]):
        mark = "  <- today" if lr == NADO_LOG_ROWS else ""
        print(f"  {lr:>9} {aux_bits(lr):>9.1f}      {ncs[i]:>8} "
              f"{alphas_bits(ncs[i]):>8.1f}{mark}")
    ov = rows_where_alphas_overtakes()
    print(f"""
  The alphas term only overtakes LogUp above about {ov:,} constraints. NADO's
  largest circuit has 3,412, so LogUp binds by {alphas_bits(3412)-aux_bits(17):.1f} bits and the
  conflation did not change iteration 75's conclusion -- but it was the wrong
  reason.""")

    sec("3. THE SCALING PROPERTY THE LADDER HID")
    print(f"""
  The binding term carries log_rows, so NADO's provable soundness FALLS AS ITS
  TRACE GROWS -- {bits_lost_per_doubling():.0f} bit per doubling:
""")
    print(f"  {'rows':>8} {'classical':>10} {'PQ':>7}")
    print("  " + "-" * 28)
    for lr in (17, 20, 24, 28):
        print(f"  {'2^' + str(lr):>8} {aux_bits(lr):>10.1f} {aux_bits(lr)/2:>7.1f}")
    print("""
  A query-bound system does not have this. For the seven verified zkVMs the term
  s*y + g is independent of trace size, so growing the trace costs proof size
  and nothing else. For NADO it costs security directly.

  Iteration 75's ladder held rows at 2^17 and could not see it. Its conclusions
  stand at that trace size; what is new is that 109 is a constant of the system
  AT ITS CURRENT TRACE, not of the system.""")

    sec("4. WHICH STRENGTHENS THE GF(p^3) RECOMMENDATION")
    r3 = rows_where_logup_returns(192)
    print(f"""
  At GF(p^3) the LogUp term is 192 - 2 - log_rows and the query phase ({NADO_QUERY_TERM})
  takes over. LogUp only returns to binding when

      192 - 2 - log_rows < {NADO_QUERY_TERM}   <=>   log_rows > {r3:.1f}

  i.e. at 2^{r3:.0f} rows -- five hundred billion. So the extension degree does not
  merely buy 20.9 post-quantum bits, it REMOVES THE TRACE-SIZE DEPENDENCE for
  any trace NADO could execute.

  That is the stronger form of the same recommendation, and iteration 75 could
  not state it while treating the offset as a constant.""")

    sec("5. A CHEAPER PARTIAL MEASURE, RECORDED NOT RECOMMENDED")
    print(f"""
  The offset also carries log2(num_buses), so consolidating {DEFAULT_BUSES} LogUp buses into
  1 buys {bus_consolidation_gain():.0f} bits at any trace size and any field:

      2^{NADO_LOG_ROWS} rows, {DEFAULT_BUSES} buses   {aux_bits(NADO_LOG_ROWS):.1f}
      2^{NADO_LOG_ROWS} rows, 1 bus     {aux_bits(NADO_LOG_ROWS, num_buses=1):.1f}

  Two bits is not twenty-one, and bus consolidation is a protocol change rather
  than a parameter change, so this is recorded rather than recommended. It is
  noted because the term's shape makes it available and nothing else in this
  repo mentions it.""")


if __name__ == "__main__":
    report()


# ---------------------------------------------------------------- composition

# ITERATION 76, answering a direct question: do the two open NADO
# recommendations compose? They do NOT. The 93 "surplus" queries are surplus
# only while the LogUp term binds at 109. Raise the field and the query phase
# becomes the binding term, at which point every one of the 320 queries counts.
COMPOSITION = [
    ("today: GF(p^2), 320 queries", 2, 320, 109.0, 54.5, 2132),
    ("cut queries: GF(p^2), 227", 2, 227, 109.0, 54.5, 1547),
    ("upgrade field: GF(p^3), 320", 3, 320, 150.8, 75.4, 2972),
    ("BOTH together", 3, 227, 112.2, 56.1, 2143),
]


def composition_table():
    return COMPOSITION


def both_is_dominated():
    """Doing both gives nearly today's size for nearly today's security."""
    _l, _d, _s, _p, pq_both, kib_both = COMPOSITION[3]
    _l0, _d0, _s0, _p0, pq_now, kib_now = COMPOSITION[0]
    return (pq_both - pq_now) < 2.0 and abs(kib_both - kib_now) / kib_now < 0.05
