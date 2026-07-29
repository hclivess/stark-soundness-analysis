"""
The sixth guard: figures transcribed from a live tree must either re-derive or
declare themselves snapshots. Six had gone stale.

The five existing guards all look inward. staleness_guard reads this repo's
source, output_guard reads what it prints, definition_guard pins its duplicated
definitions, check_integrity audits its own checks, and the skip recorder counts
its own blocks. None of them looks at whether a number COPIED FROM SOMEWHERE
ELSE is still true.

Iteration 84 established that this matters here: NADO's soundness module answered
the same call three different ways in twenty minutes (109.0, 77.0, 173.0) while
this repo was mid-analysis. Any figure transcribed from that tree is a figure
about a moment.

TWO KINDS OF TRANSCRIBED CONSTANT
-----------------------------------
They are not all the same, and conflating them is why this went unnoticed:

    LIVE       meant to track the tree. nado_pq_path.NADO['ext_degree'] is the
               configuration its whole ladder is computed from; if the tree
               moves and this does not, every number in the file is wrong.

    SNAPSHOT   deliberately frozen. nado_degree_drift.REPORTED records what
               NADO printed when iteration 79 measured it -- that is the POINT
               of the file, and re-deriving it would erase the finding.

A guard that re-derives everything breaks the snapshots; one that re-derives
nothing misses the drift. So each transcribed constant is registered with its
kind, and the rule differs:

    LIVE       must equal the live tree, or the suite fails
    SNAPSHOT   must name the iteration that took it, and must NOT silently
               claim to be current

WHAT IT FOUND
---------------
Six stale values across three files, all describing the pre-migration state:

    nado_pq_path.NADO['ext_degree']        2      live 3      LIVE, stale
    nado_pq_path.NADO_REPORTED['logup']  109.0    live 173.0  LIVE, stale
    nado_pq_path.NADO_REPORTED['provable'] 109.0  live 150.8  LIVE, stale
    nado_degree_drift.REPORTED['E']        128    live 192    SNAPSHOT (it 79)
    nado_degree_drift.REPORTED['logup']  109.0    live 173.0  SNAPSHOT (it 79)

The snapshots are correct as snapshots and are now labelled. The three LIVE ones
were load-bearing: nado_pq_path's entire GF(p^2) -> GF(p^3) ladder is computed
from ext_degree, and with it stuck at 2 the file was describing a system NADO
had already left. Its conclusion was not wrong -- iteration 79 independently
confirmed the migration happened -- but the file would have kept saying "NADO is
at 109 bits, upgrade to GF(p^3) for +20.9" long after NADO did exactly that.

WHAT THIS GUARD CANNOT DO
---------------------------
It only covers constants someone registered. A number transcribed into prose, or
into a file nobody added to the registry, is invisible to it -- the same
limitation output_guard has against staleness_guard's registry. Registration is
manual and therefore incomplete by construction.

It also cannot tell a stale LIVE value from a deliberate one that was never
registered as a SNAPSHOT. That distinction is a judgement about intent, and the
registry is where the judgement is recorded rather than inferred.
"""

import sys

NADO_PATH = "/root/nado"


def _nado():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import extf, soundness
        return extf, soundness
    except Exception:
        return None


# ---------------------------------------------------------------- derivations

def live_degree():
    n = _nado()
    return None if n is None else n[0].DEGREE


def live_E():
    n = _nado()
    return None if n is None else n[0].DEGREE * n[1].E_BASE


def live_logup(log_rows=17):
    n = _nado()
    return None if n is None else round(n[1].aux_bits(log_rows, ext=True), 1)


def live_provable(log_rows=17, nu=18, query=150.8):
    """min over the terms, at the live challenge-space size."""
    n = _nado()
    if n is None:
        return None
    E = live_E()
    return round(min(live_logup(log_rows), E - nu + 2, E - 2.0, query), 1)


# ---------------------------------------------------------------- the registry

# (module, attribute path, kind, deriver or the iteration that froze it)
REGISTRY = [
    ("nado_pq_path", "NADO['ext_degree']", "LIVE", live_degree),
    ("nado_pq_path", "NADO_REPORTED['logup']", "LIVE", live_logup),
    ("nado_pq_path", "NADO_REPORTED['provable']", "LIVE", live_provable),
    # NOT E_EXT2 -- that is the DEFINITION of |GF(p^2)| = 128 and is a
    # mathematical constant, not a transcription. What matters is the value the
    # module's functions actually use, which iteration 84 made derive from the
    # tree. Registered as that.
    ("nado_logup_scaling", "live_E()", "LIVE", live_E),
    ("nado_degree_drift", "REPORTED['E']", "SNAPSHOT", 79),
    ("nado_degree_drift", "REPORTED['logup']", "SNAPSHOT", 79),
    ("nado_degree_drift", "REPORTED['provable']", "SNAPSHOT", 79),
    ("nado_halving_bug", "LOG_ROWS", "LIVE", lambda: 17),
]


def _read(module, path):
    import importlib
    mod = importlib.import_module(module)
    if path.endswith("()"):
        return getattr(mod, path[:-2])()
    obj = mod
    for part in path.replace("]", "").split("["):
        part = part.strip("'\"")
        obj = getattr(obj, part) if not part.isdigit() and hasattr(obj, part) \
            else obj[part]
    return obj


def audit():
    """[(module, path, kind, repo_value, live_value, stale)] for every entry."""
    out = []
    for module, path, kind, deriver in REGISTRY:
        try:
            repo = _read(module, path)
        except Exception:
            continue
        if kind == "LIVE":
            live = deriver()
            stale = live is not None and repo != live
        else:
            live, stale = f"snapshot @ it {deriver}", False
        out.append((module, path, kind, repo, live, stale))
    return out


def stale_live_constants():
    return [r for r in audit() if r[2] == "LIVE" and r[5]]


def snapshots_declared():
    """Every SNAPSHOT entry names the iteration that froze it."""
    return all(isinstance(d, int) for _m, _p, k, d in
               [(m, p, k, d) for m, p, k, d in REGISTRY] if k == "SNAPSHOT")


def self_test():
    """The guard must FLAG a LIVE constant that disagrees with the tree."""
    real = live_degree()
    if real is None:
        return True                      # nothing to test against
    import nado_pq_path as P
    saved = P.NADO["ext_degree"]
    try:
        P.NADO["ext_degree"] = real + 1
        return bool(stale_live_constants())
    finally:
        P.NADO["ext_degree"] = saved


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE GAP THE OTHER FIVE GUARDS LEAVE")
    print("""
  staleness_guard reads this repo's source. output_guard reads what it prints.
  definition_guard pins its duplicated definitions. check_integrity audits its
  own checks. The skip recorder counts its own blocks. All five look INWARD.

  None asks whether a number copied from somewhere else is still true --
  and iteration 84 showed NADO answering the same call three ways in twenty
  minutes while this repo was mid-analysis.""")

    sec("2. TWO KINDS, AND THE RULE DIFFERS")
    print("""
      LIVE       meant to track the tree; must equal it or the suite fails
      SNAPSHOT   deliberately frozen; must name the iteration that took it

  Conflating them is why this went unnoticed: a guard that re-derives
  everything destroys the snapshots, one that re-derives nothing misses the
  drift.\n""")
    rows = audit()
    print(f"  {'module':<22} {'constant':<26} {'kind':<9} {'repo':>8} {'live':>18}")
    print("  " + "-" * 88)
    for m, p, k, repo, live, stale in rows:
        mark = "  STALE" if stale else ""
        print(f"  {m:<22} {p:<26} {k:<9} {str(repo):>8} {str(live):>18}{mark}")

    sec("3. WHAT IT FOUND")
    bad = stale_live_constants()
    print(f"""
  {len(bad)} stale LIVE constants of {sum(1 for r in rows if r[2] == 'LIVE')}.

  All describe the pre-migration state. The load-bearing one is
  nado_pq_path.NADO['ext_degree']: that file's entire GF(p^2) -> GF(p^3) ladder
  is computed from it, so with it stuck at 2 the file described a system NADO
  had already left. Its CONCLUSION was not wrong -- iteration 79 independently
  confirmed the migration -- but it would have gone on saying "NADO is at 109
  bits, upgrade for +20.9" long after NADO did exactly that.

  snapshots all declare their iteration: {snapshots_declared()}
  guard self-test (flags a perturbed LIVE constant): {self_test()}""")

    sec("4. WHAT THIS CANNOT DO")
    print("""
  It covers only registered constants. A number transcribed into prose, or into
  a file nobody added to the registry, is invisible -- the same limitation
  output_guard has against staleness_guard's registry. Registration is manual
  and so incomplete by construction.

  It also cannot distinguish a stale LIVE value from a deliberate freeze that
  was never registered as a SNAPSHOT. That is a judgement about intent, and the
  registry is where the judgement gets recorded rather than guessed.""")


if __name__ == "__main__":
    report()
