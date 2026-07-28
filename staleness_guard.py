"""
A guard against the repository's characteristic failure mode: stale claims.

This repo has overturned itself about ten times in thirty-five iterations, and
the correction rate is the main reason to trust what survived. But every
overturn has left the retracted statement sitting in OTHER files, asserted as
current, because nothing checked. Iteration 35 found two such spots in
ceiling_anatomy.py two iterations after the claim was retracted -- and only
because I went looking by hand.

The README check-count guard has caught drift four times by being mechanical.
This applies the same idea to CLAIMS: a table of retracted statements, and a
scan that fails the adversarial suite if any file asserts one.

THE ASSERTION-vs-QUOTATION PROBLEM
-----------------------------------
The difficulty is that the files documenting a retraction necessarily QUOTE the
retracted claim. radius_staircase.py has to say "the repo's table said
'code proximity: a >= 1'" in order to correct it. A naive substring scan would
flag exactly the files doing the right thing.

The rule used here: an occurrence of a retracted phrase is allowed only if a
retraction marker appears WITHIN A WINDOW around it -- one of RETRACT,
SUPERSEDED, WRONG, CORRECTED, "no longer", or an explicit iteration reference.

The window matters. The first version of this guard checked whether the marker
appeared ANYWHERE in the file, and a teeth-test immediately showed that is
useless: a synthetic file whose only content was a bare stale assertion went
undetected, because its own header contained the word "retracted". Any file
long enough to discuss retraction at all would have exempted itself. Proximity
matching is what gives the guard teeth, and the teeth are re-tested on every
run by self_test() below.

WHAT IS REGISTERED
------------------
Only claims this repository ITSELF asserted and then retracted, with the
iteration that overturned them. Not general falsehoods -- the point is internal
consistency, not fact-checking the literature.
"""

import os
import re

# (retracted phrase, what replaced it, iteration that overturned it)
RETRACTED = [
    ("the RS-proximity family is a >= 1",
     "a is a staircase in the radius: 0 at UDR, 1 at Johnson, unbounded above",
     33),
    ("the only\n  a = 0 code test is conditional",
     "BCHKS25 result 1 gives an UNCONDITIONAL a = 0 at the unique-decoding radius",
     33),
    ("nothing known forbids a = 0",
     "BCHKS25 results 3-4 forbid it above Johnson for some RS codes",
     33),
    ("highest-leverage open problem",
     "the RS capacity conjecture was disproved in late 2025",
     9),
    ("exactly three levers",
     "there are five levers",
     7),
    ("conservative LOWER bound",
     "classical/2 bounds provable PQ from ABOVE; it is a ceiling",
     24),
    ("floor binds for exactly one deployed system",
     "it costs zero -- m is Johnson-regime and SP1 is reported in UDR",
     39),
    ("headroom exceeds nu everywhere",
     "it fails for the two UDR systems once the right regime is used",
     40),
    ("blocked by field size",
     "Yuan-Zhu give 22-135 bits; they are blocked by structure, not field size",
     42),
    ("no known efficient certificate",
     "not needed: the sampling failure probability is q^{-Omega(n)} <= 2^-360",
     46),
    ("their unconstrained optimum already exceeds 3",
     "soundcalc derives m by formula; its raw value is 10-50, so the floor is dead code",
     47),
]

# Extended in iteration 35 after its own first run produced a FALSE POSITIVE:
# qrom_bracket.py quotes "conservative LOWER bound" and immediately corrects it
# with the word "Backwards", which was not in the list. A guard whose marker
# vocabulary is too narrow flags the files doing the right thing.
MARKERS = ("RETRACT", "SUPERSEDED", "WRONG", "CORRECTED", "no longer",
           "used to", "iteration 33", "iteration 24", "overturn", "false",
           "backwards", "was not", "it is not", "instead")

SCAN_EXT = (".py", ".md")
SKIP = {"staleness_guard.py"}


def _norm(s):
    """Collapse whitespace so line-wrapped phrases still match."""
    return re.sub(r"\s+", " ", s)


WINDOW = 700          # characters either side of an occurrence


def _marked_near(flat_lower, pos, length):
    """Is a retraction marker within WINDOW characters of this occurrence?"""
    lo = max(0, pos - WINDOW)
    hi = min(len(flat_lower), pos + length + WINDOW)
    ctx = flat_lower[lo:hi]
    return any(m.lower() in ctx for m in MARKERS)


def scan_text(text):
    """Return [(phrase, replacement, iteration)] asserted without a nearby marker."""
    flat = _norm(text)
    low = flat.lower()
    out = []
    for phrase, replacement, it in RETRACTED:
        p = _norm(phrase).lower()
        start = 0
        while True:
            pos = low.find(p, start)
            if pos < 0:
                break
            if not _marked_near(low, pos, len(p)):
                out.append((phrase, replacement, it))
                break
            start = pos + len(p)
    return out


def scan(root="."):
    """Return [(file, phrase, replacement, iteration)] for unmarked assertions."""
    hits = []
    for name in sorted(os.listdir(root)):
        if name in SKIP or not name.endswith(SCAN_EXT):
            continue
        try:
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        for phrase, replacement, it in scan_text(text):
            hits.append((name, phrase, replacement, it))
    return hits


def self_test():
    """The guard must flag a bare stale assertion and clear a marked one.

    Run on every invocation. A guard that cannot fail is not a guard, and the
    first version of this one could not -- see the module docstring.
    """
    bare = "The sumcheck family is a = 0 and the RS-proximity family is a >= 1."
    marked = ("SUPERSEDED IN ITERATION 33: this file used to say that "
              "the RS-proximity family is a >= 1, which is wrong.")
    return bool(scan_text(bare)) and not scan_text(marked)


def report():
    print("=" * 92)
    print("STALENESS GUARD -- retracted claims asserted without a retraction marker")
    print("=" * 92)
    print(f"\n  {len(RETRACTED)} retracted claims registered, "
          f"scanning {', '.join(SCAN_EXT)} files\n")
    print(f"  {'iteration':>9}  {'retracted claim':<44} replaced by")
    print("  " + "-" * 88)
    for phrase, replacement, it in RETRACTED:
        p = _norm(phrase)
        print(f"  {it:>9}  {p[:44]:<44} {replacement[:38]}")

    print(f"\n  self-test (does the guard actually fail?): "
          f"{'PASS' if self_test() else 'BROKEN -- guard cannot fail'}")

    hits = scan()
    print()
    if hits:
        print(f"  *** {len(hits)} STALE ASSERTION(S) ***")
        for name, phrase, replacement, it in hits:
            print(f"    {name}: asserts \"{_norm(phrase)[:50]}\" "
                  f"(retracted in iteration {it})")
    else:
        print("  no stale assertions: every occurrence sits in a file that also "
              "carries\n  a retraction marker, which is the documenting case.")
    print()
    return hits


if __name__ == "__main__":
    raise SystemExit(1 if report() else 0)
