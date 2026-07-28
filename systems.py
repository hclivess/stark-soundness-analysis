"""
One canonical system table with the regime baked in.

WHY THIS EXISTS
---------------
Iterations 38 and 40 made the same mistake in different files, eight iterations
apart: applying the Johnson-regime model to a system reported in UDR.

    it 38  m_star.py       m-optimisation applied to SP1  -> phantom 3.46 bits
    it 40  a_floor_scope.py commit_jbr + list size 2m+1 applied to SP1 and
                            OpenVM -> headroom overstated by 9 and 15 bits

Neither was a reasoning error. Both were structural: every file re-declares its
own copy of the seven-system table and then re-derives the commit bound ad hoc,
so getting the regime right is a thing each file has to remember separately.
Two of seven files forgot.

The parameter tables themselves have NOT drifted -- checked mechanically across
all five files that carry one, and they are identical. The drift was entirely in
what each file did with them.

So this module holds the table once, with the reported regime as a field, and
exposes accessors that cannot be called without it. A file that imports
`commit_bound(sys)` gets the right formula by construction rather than by
remembering.

WHAT "REGIME-CORRECT" MEANS HERE
---------------------------------
  UDR  commit bound (gamma*n + 1)/|F|, gamma = (1-rho)/2  -- no proximity
       parameter m, and list size 1 (unique decoding admits at most one
       codeword within the radius)
  JBR  commit bound BCHKS25 Thm 1.5, evaluated at m; list size
       (m + 0.5)/sqrt(rho)  -- corrected in iteration 68 from 2m+1, which is
       that expression only at rho = 1/4

The regime field is what soundcalc REPORTS each system in, cross-checked by
Theorem 7's crossover, which predicts all seven correctly.
"""

import math

# (name, E, R, T_trace, queries, grinding, reported_bits, reported_regime)
# Verified configs -- see SOURCES.md. Venus excluded as a ZisK duplicate.
SYSTEMS = [
    ("SP1 6.1.0",    124, 2, 21, 124, 16, 100, "UDR"),
    ("OpenVM 1.5.0", 124, 1, 23, 193, 20, 100, "UDR"),
    ("Airbender",    124, 1, 24,  87, 28,  67, "JBR"),
    ("Pico",         124, 1, 22,  84, 16,  53, "JBR"),
    ("ZisK 0.16.1",  192, 1, 21, 229, 16, 128, "JBR"),
    ("RISC Zero",    124, 2, 21,  50,  0,  48, "JBR"),
    ("Miden",        128, 3, 18,  27, 16,  55, "JBR"),
]

FIELDS = ("name", "E", "R", "T", "s", "g", "reported", "regime")


def as_dict(row):
    return dict(zip(FIELDS, row))


def nu(row):
    d = as_dict(row)
    return d["T"] + d["R"]


def rho(row):
    return 2.0 ** -as_dict(row)["R"]


def yield_udr(R):
    return -math.log2((1 + 2.0 ** -R) / 2)


def yield_jbr(R, m):
    a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
    return -math.log2(a) if a < 1 else float("-inf")


def commit_udr(R, nu_, E):
    """(gamma*n + 1)/|F|, gamma = (1-rho)/2. No proximity parameter."""
    gamma = (1 - 2.0 ** -R) / 2
    return E - math.log2(gamma * 2.0 ** nu_ + 1)


def commit_bound(row, m=None):
    """The commit bound in the system's OWN regime. m is ignored for UDR."""
    from regime_crossover import commit_jbr, m_eq
    d = as_dict(row)
    if d["regime"] == "UDR":
        return commit_udr(d["R"], nu(row), d["E"])
    return commit_jbr(d["R"], nu(row), d["E"], m if m is not None else m_eq(d["R"]))


def list_size(row, m=None):
    """Codewords within the radius: 1 for unique decoding, (m+0.5)/sqrt(rho)
    for Johnson.

    CORRECTED IN ITERATION 68. This returned 2m+1, dropping the 1/sqrt(rho)
    that this repo's OWN commit_jbr carries: regime_crossover.py:95 computes
    `mm / sqrt_rho` = (m+0.5)/sqrt(rho), and :98 carries
    `- log2(2m+1) + 0.5*log2(rho)` = -log2((2m+1)/sqrt(rho)). The commit bound
    was always right; only this accessor's attribution of which factor is the
    LIST was wrong, and 2m+1 is that expression's value at rho = 1/4.
    soundcalc states the same thing directly (johnson_bound.py:91-105).
    """
    from regime_crossover import m_eq
    d = as_dict(row)
    if d["regime"] == "UDR":
        return 1.0
    mm = (m if m is not None else m_eq(d["R"])) + 0.5
    return mm / math.sqrt(2.0 ** -d["R"])


def query_term(row, m=1000.0):
    """s * (bits per query) + g, in the system's own regime."""
    d = as_dict(row)
    y = yield_udr(d["R"]) if d["regime"] == "UDR" else yield_jbr(d["R"], m)
    return d["s"] * y + d["g"]


def by_regime(regime):
    return [r for r in SYSTEMS if as_dict(r)["regime"] == regime]


# --------------------------------------------------------- drift detection

import glob
import re

_ROW = re.compile(
    r'\("(SP1[^"]*|OpenVM[^"]*|Airbender|Pico|ZisK[^"]*|RISC Zero|Miden)",\s*'
    r'(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)')


def local_tables(root="."):
    """Every file carrying its own copy of the table, as {file: {name: params}}."""
    out = {}
    for path in sorted(glob.glob(root + "/*.py")):
        name = path.split("/")[-1]
        if name == "systems.py":
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        rows = {}
        for m in _ROW.finditer(text):
            key = m.group(1)
            if key not in rows:
                rows[key] = tuple(int(m.group(i)) for i in range(2, 7))
        if len(rows) >= 5:
            out[name] = rows
    return out


def drift(root="."):
    """Files whose local table disagrees with the canonical one."""
    canon = {as_dict(r)["name"]: (as_dict(r)["E"], as_dict(r)["R"], as_dict(r)["T"],
                                  as_dict(r)["s"], as_dict(r)["g"])
             for r in SYSTEMS}
    bad = []
    for fname, rows in local_tables(root).items():
        for k, v in rows.items():
            if k in canon and v != canon[k]:
                bad.append((fname, k, v, canon[k]))
    return bad


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    from regime_crossover import m_eq

    sec("1. THE CANONICAL TABLE, WITH REGIME AS A FIELD")
    print(f"  {'system':<15} {'E':>5} {'R':>3} {'T':>3} {'nu':>4} {'s':>5} "
          f"{'g':>4} {'reported':>9} {'regime':>7}")
    print("  " + "-" * 62)
    for r in SYSTEMS:
        d = as_dict(r)
        print(f"  {d['name']:<15} {d['E']:>5} {d['R']:>3} {d['T']:>3} "
              f"{nu(r):>4} {d['s']:>5} {d['g']:>4} {d['reported']:>9} "
              f"{d['regime']:>7}")

    sec("2. REGIME-CORRECT ACCESSORS vs THE WRONG-REGIME VALUES")
    from regime_crossover import commit_jbr
    print(f"  {'system':<15} {'regime':>7} {'commit (correct)':>17} "
          f"{'if JBR forced':>14} {'delta':>8} {'L':>6}")
    print("  " + "-" * 72)
    for r in SYSTEMS:
        d = as_dict(r)
        cc = commit_bound(r)
        forced = commit_jbr(d["R"], nu(r), d["E"], m_eq(d["R"]))
        print(f"  {d['name']:<15} {d['regime']:>7} {cc:>17.1f} {forced:>14.1f} "
              f"{cc-forced:>+8.1f} {list_size(r):>6.2f}")
    print("""
  The two UDR rows are where iterations 38 and 40 went wrong. Forcing the JBR
  bound on them understates their commit ceiling by 10 and 19 bits, and inflates
  their list size from 1 to 5 and 17.5.""")

    sec("3. DRIFT CHECK ACROSS EVERY FILE CARRYING ITS OWN COPY")
    tabs = local_tables()
    for fname, rows in tabs.items():
        print(f"  {fname:<24} {len(rows)} systems")
    bad = drift()
    print()
    if bad:
        print(f"  *** {len(bad)} DRIFTED ROW(S) ***")
        for f, k, v, c in bad:
            print(f"    {f}: {k} has {v}, canonical is {c}")
    else:
        print(f"  no drift: all {len(tabs)} local tables agree with the canonical one.")
        print("  (parameters never drifted -- the regime HANDLING did, which is")
        print("   what the accessors above are for.)")


if __name__ == "__main__":
    report()
    raise SystemExit(1 if drift() else 0)
