"""
staleness_guard reads source. This runs the code and reads what it PRINTS --
which is where two retracted claims were still living.

Iteration 68 found a_floor_scope's headroom table printing SP1 at 29.4 bits
while its own docstring, four hundred lines above, said iteration 40 had
corrected that to 20.6. The correction had been documentation-only for 28
iterations. staleness_guard did not catch it, and could not: it opens files and
scans TEXT, so a docstring carrying the retraction marker satisfies its
proximity rule while the code below quietly computes the old thing.

That is a distinct failure mode from the one staleness_guard was built for.
Its registry catches a retracted claim ASSERTED IN PROSE. This catches a
retracted claim PRODUCED BY EXECUTION, where no docstring can shield it,
because printed output has no docstring.

WHAT IT FOUND
---------------
Importing all 49 modules that expose a report() (excluding this one, which
would recurse), capturing stdout, normalising
whitespace, and running staleness_guard's own registry over the OUTPUT:

    m_star: "the m >= 3 floor binds for exactly one deployed system"

printed as a SECTION HEADING, with the table below it attributing +3.46 bits to
SP1 and concluding "Binding for 1 of 7: SP1 6.1.0 (3.46 bits)".

That is the exact phantom iteration 39 retracted. SP1 is reported in UDR, whose
bound (gamma*n + 1)/|F| contains no proximity parameter, so there is no m for a
floor to bind. The docstring at the top of m_star.py has said so since iteration
39 -- in capitals, as the first thing in the file. Anyone who ran the module saw
the retracted figure presented as a result, for thirty iterations.

Corrected: the section now routes through systems.py's regime field, prints
"n/a (UDR)" for the two systems that have no m, and reports the floor binding
for ZERO of the five that do. That is a stronger version of iteration 39's
finding, not a weaker one -- the m >= 3 floor costs nothing anywhere.

WHY LINE WRAPPING MATTERS HERE
--------------------------------
The claim did not appear in the output as a greppable string: it was wrapped
across a line break inside a banner. `grep` found nothing. Normalising
whitespace before matching found it immediately -- the same lesson iterations 35
and 54 learned about the source-text guard, now applying to the output guard on
its first run. Any guard that matches phrases must normalise first.

SCOPE, HONESTLY
-----------------
This catches only claims already in staleness_guard's registry -- it inherits
that registry rather than discovering new retractions. A claim nobody has
recorded as retracted passes both guards. What it adds is that recording a
retraction now constrains the CODE as well as the prose, which is exactly the
gap iterations 68 and 69 each walked into.

It also cannot see claims that are true of the printed numbers but false of the
world; nothing mechanical can. It closes one specific hole: prose saying
"corrected" above code that still prints the uncorrected thing.
"""

import contextlib
import glob
import importlib
import io
import os

from staleness_guard import RETRACTED, _marked_near, _norm

# adversarial: the suite runs the guards, not the reverse.
# output_guard: scanning itself recurses -- report() -> coverage() ->
#   modules_with_report() -> capture(output_guard) -> report(). The stack
#   exhausts and the RecursionError surfaces on whichever modules follow this
#   one alphabetically, which is why staleness_guard and systems appeared to
#   fail while running fine standalone. A guard must not scan itself.
SKIP = {"adversarial", "output_guard"}


_CAPTURE_CACHE = {}


def modules_with_report(root="."):
    """Every module in the repo exposing a report() entry point."""
    out = []
    for path in sorted(glob.glob(os.path.join(root, "*.py"))):
        name = os.path.basename(path)[:-3]
        if name in SKIP:
            continue
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        if hasattr(mod, "report"):
            out.append((name, mod))
    return out


def capture(mod):
    """Run report() and return its stdout, or None if it raised.

    Cached: report() is deterministic, and several of these modules do heavy
    numerical work (Monte Carlo, optimiser sweeps). Running each twice made the
    guard slower than the entire adversarial suite.
    """
    key = mod.__name__
    if key not in _CAPTURE_CACHE:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                mod.report()
            _CAPTURE_CACHE[key] = buf.getvalue()
        except Exception:
            _CAPTURE_CACHE[key] = None
    return _CAPTURE_CACHE[key]


def scan_output(text):
    """Retracted claims present in `text` with no retraction marker nearby.

    Whitespace is normalised first: the m_star instance was wrapped across a
    line break inside a banner and was invisible to a literal search.
    """
    flat = _norm(text).lower()
    found = []
    for old, new, it in RETRACTED:
        needle = _norm(old).lower()
        start = 0
        while True:
            pos = flat.find(needle, start)
            if pos < 0:
                break
            if not _marked_near(flat, pos, len(needle)):
                found.append((old, new, it))
            start = pos + 1
    return found


def scan(root="."):
    """[(module, old_claim, replacement, iteration)] over every report()."""
    hits = []
    for name, mod in modules_with_report(root):
        text = capture(mod)
        if text is None:
            continue
        for old, new, it in scan_output(text):
            hits.append((name, old, new, it))
    return hits


def coverage(root="."):
    """(modules with report(), modules whose report() ran cleanly)."""
    mods = modules_with_report(root)
    return len(mods), sum(1 for _n, m in mods if capture(m) is not None)


def self_test():
    """The guard must FLAG a retracted claim planted in output, and must NOT
    flag the same claim when a retraction marker sits beside it."""
    old = RETRACTED[0][0]
    bare = f"section heading: {old} and then some numbers"
    marked = f"RETRACTED in iteration 39: {old} was wrong, corrected below"
    return bool(scan_output(bare)) and not scan_output(marked)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE HOLE staleness_guard CANNOT SEE")
    print("""
  staleness_guard opens files and scans TEXT. So a docstring carrying a
  retraction marker satisfies its proximity rule while the code below computes
  the old thing -- which is exactly what iteration 68 found in a_floor_scope,
  printing SP1 at 29.4 bits while its own docstring said iteration 40 had
  corrected that to 20.6.

  Its registry catches a retracted claim ASSERTED IN PROSE. This guard catches
  one PRODUCED BY EXECUTION, where no docstring can shield it, because printed
  output has no docstring.""")

    sec("2. WHAT IT FOUND")
    total, ok = coverage()
    hits = scan()
    print(f"""
  modules exposing report()      {total}
  report() ran cleanly           {ok}
  retracted claims in output     {len(hits)}
""")
    for name, old, new, it in hits:
        print(f"    {name}: \"{old}\"")
        print(f"    {'':<{len(name)}}  retracted in iteration {it}; correct: {new}")
    if not hits:
        print("    none -- m_star's section 2 was the one instance, fixed in "
              "iteration 69")
    print("""
  The instance it found was m_star's section 2, printed as a HEADING with a
  table attributing +3.46 bits to SP1 and concluding "Binding for 1 of 7".
  That is the phantom iteration 39 retracted: SP1 is UDR, whose bound has no
  proximity parameter, so there is no m for a floor to bind. The file's own
  docstring has said so, in capitals, since iteration 39 -- and anyone running
  the module saw the retracted number presented as a result for thirty
  iterations.""")

    sec("3. THE CLAIM WAS NOT GREPPABLE")
    print("""
  It did not appear in the output as a searchable string -- it was wrapped
  across a line break inside a banner, and grep found nothing. Normalising
  whitespace first found it immediately.

  That is the lesson iterations 35 and 54 learned about the source-text guard,
  reappearing on this guard's first run. Any guard that matches phrases must
  normalise before matching.""")

    sec("4. SCOPE")
    print(f"""
  This inherits staleness_guard's registry rather than discovering retractions:
  a claim nobody has recorded passes both guards. What it adds is that recording
  a retraction now constrains the CODE as well as the prose -- the gap
  iterations 68 and 69 each walked into.

  guard self-test (flags a planted claim, ignores a marked one): """
          f"{'PASS' if self_test() else 'FAIL -- THE GUARD IS INERT'}")


if __name__ == "__main__":
    report()
