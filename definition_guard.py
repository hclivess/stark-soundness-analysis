"""
A consistency guard for duplicated definitions -- and a retraction of a claim
iteration 64 made about this repository yesterday.

THE RETRACTION FIRST
----------------------
Iteration 64 read soundcalc's Johnson regime and reported, correctly, that eta's
default branches on field size: sqrt(rho)/100 above 2^150, max(rho/20,
sqrt(rho)/100) below. It then claimed:

    "This repo only ever had the second branch."

That is false. soundcalc_lean.py:99-103 has had both branches since iteration 47:

    def eta_soundcalc(rho, field_card_bits=124):
        if field_card_bits > 150:
            return math.sqrt(rho) / 100.0
        return max(rho / 20.0, math.sqrt(rho) / 100.0)

What iteration 64 actually did was write a SECOND implementation of the same
function in whir_jbr.py and then mistake its own novelty for the repo's gap.

The claim was not harmless, because the branch is load-bearing. ZisK is
Goldilocks^3 = 2^192 and sits above the switch:

    branch taken       m     model    reported    error
    sqrt(rho)/100     50     127.2         128     -0.8      <- what the repo does
    max(rho/20, ...)  15     119.7         128     -8.3      <- the alleged bug

Had iteration 64's claim been true, the published ZisK figure would have been
off by 8.3 bits rather than 0.8, and the "within 1 bit across seven systems"
result would have failed on that system. It did not fail, which was already
evidence the branch was present -- evidence I had in the repo and did not check
before asserting otherwise.

WHAT THE EPISODE ACTUALLY EXPOSED
-----------------------------------
Not a missing branch. A DUPLICATE. The repo now computes soundcalc's eta in two
places, and eta_from_m in two places, and m_min in five:

    eta          soundcalc_lean.eta_soundcalc     whir_jbr.eta_default
    eta_from_m   regime_crossover.eta_from_m      whir_jbr.eta_from_m
    m_min        verify_theorem, stark_soundness, blowup_theorem,
                 m_star, regimes                  (five copies)

Every one of them agrees today, checked across rates 1/2 to 1/16 and field sizes
on both sides of the 2^150 switch. That is the good news and also the reason the
risk is invisible: nothing is broken, so nothing draws attention to it. A repo
that has already suffered a regime-scope error (iteration 38, corrected twice
before iteration 41 made it impossible by construction) should not rely on five
copies of a formula staying in step by luck.

So this file is the numerical analogue of staleness_guard.py: it does not
consolidate the duplicates, it PINS them to each other, so that any future edit
which changes one and not the others fails the suite immediately.

WHY PIN RATHER THAN CONSOLIDATE
---------------------------------
Consolidating would be the better engineering answer in a codebase. Here each
file is meant to be readable on its own -- they are written as arguments, and a
reader following m_star.py should not have to chase an import to learn what
m_min is. Pinning keeps that property and removes the drift risk, at the cost of
one guard file. Iteration 41 made the same trade for systems.py.
"""

import importlib
import math

# families of duplicated definitions: (label, [(module, function)], sample args)
FAMILIES = [
    ("eta (soundcalc's default)",
     [("soundcalc_lean", "eta_soundcalc"), ("whir_jbr", "eta_default")],
     "eta"),
    ("eta_from_m",
     [("regime_crossover", "eta_from_m"), ("whir_jbr", "eta_from_m")],
     "eta_from_m"),
    ("m_min",
     [("verify_theorem", "m_min"), ("stark_soundness", "m_min"),
      ("blowup_theorem", "m_min"), ("m_star", "m_min"), ("regimes", "m_min")],
     "m_min"),
]

RATES = (0.5, 0.25, 0.125, 0.0625, 0.03125)
FIELD_BITS = (124, 128, 150, 151, 192)      # straddles soundcalc's 2^150 switch
MS = (1, 2, 3, 15, 29, 50)
RS = (1, 2, 3, 4, 5)

# the stake: what the eta branch is worth on the one system that sits above it
ZISK_CORRECT_M, ZISK_CORRECT = 50, 127.2
ZISK_WRONG_BRANCH_M, ZISK_WRONG_BRANCH = 15, 119.7
ZISK_REPORTED = 128


def _fn(module, name):
    return getattr(importlib.import_module(module), name)


def eta_calls():
    """(args, [values]) for every eta implementation. Field bits vs field size."""
    out = []
    for rho in RATES:
        for fb in FIELD_BITS:
            vals = [_fn("soundcalc_lean", "eta_soundcalc")(rho, fb),
                    _fn("whir_jbr", "eta_default")(rho, 2 ** fb)]
            out.append(((rho, fb), vals))
    return out


def eta_from_m_calls():
    return [((rho, m), [_fn("regime_crossover", "eta_from_m")(rho, m),
                        _fn("whir_jbr", "eta_from_m")(rho, m)])
            for rho in RATES for m in MS]


def m_min_calls():
    mods = [m for m, _ in FAMILIES[2][1]]
    return [((R,), [_fn(mod, "m_min")(R) for mod in mods]) for R in RS]


def disagreements(tol=1e-12):
    """Every (family, args, values) where the duplicates do not agree."""
    bad = []
    for label, calls in (("eta (soundcalc's default)", eta_calls()),
                         ("eta_from_m", eta_from_m_calls()),
                         ("m_min", m_min_calls())):
        for args, vals in calls:
            if max(vals) - min(vals) > tol:
                bad.append((label, args, vals))
    return bad


def branch_is_load_bearing():
    """Bits by which the wrong eta branch would move ZisK's published figure."""
    return abs(ZISK_WRONG_BRANCH - ZISK_REPORTED) - abs(ZISK_CORRECT - ZISK_REPORTED)


def self_test():
    """The guard must FAIL when a duplicate diverges. Otherwise it proves nothing."""
    real = _fn("whir_jbr", "eta_default")
    import whir_jbr
    try:
        whir_jbr.eta_default = lambda rho, field_size=2 ** 124: real(rho, field_size) * 1.01
        return len(disagreements()) > 0
    finally:
        whir_jbr.eta_default = real


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. RETRACTING ITERATION 64's CLAIM ABOUT THIS REPOSITORY")
    print(f"""
  Iteration 64 said of soundcalc's field-size branch on eta: "this repo only
  ever had the second branch." False. soundcalc_lean.py:99-103 has had both
  since iteration 47. Iteration 64 wrote a SECOND copy in whir_jbr.py and
  mistook its own novelty for a gap.

  The claim was not harmless, because the branch is load-bearing. ZisK is
  Goldilocks^3 = 2^192, above the switch:\n""")
    print(f"  {'branch taken':<22} {'m':>4} {'model':>8} {'reported':>10} {'error':>8}")
    print("  " + "-" * 56)
    print(f"  {'sqrt(rho)/100':<22} {ZISK_CORRECT_M:>4} {ZISK_CORRECT:>8.1f} "
          f"{ZISK_REPORTED:>10} {ZISK_CORRECT-ZISK_REPORTED:>+8.1f}   <- what the repo does")
    print(f"  {'max(rho/20, ...)':<22} {ZISK_WRONG_BRANCH_M:>4} {ZISK_WRONG_BRANCH:>8.1f} "
          f"{ZISK_REPORTED:>10} {ZISK_WRONG_BRANCH-ZISK_REPORTED:>+8.1f}   <- the alleged bug")
    print(f"""
  Worth {branch_is_load_bearing():.1f} bits. Had the claim been true, README's "within 1 bit across
  seven systems" would have failed on ZisK. It did not fail -- which was already
  evidence in the repo that the branch was present, and I asserted otherwise
  without looking.""")

    sec("2. WHAT THE EPISODE ACTUALLY EXPOSED: DUPLICATES, NOT A GAP")
    print()
    for label, members, _ in FAMILIES:
        print(f"  {label:<28} {len(members)} copies")
        for mod, fn in members:
            print(f"  {'':<28}   {mod}.{fn}")
    n = sum(len(v) for _, v, _ in FAMILIES)
    print(f"""
  {n} implementations of 3 quantities. Every one agrees today, over rates 1/2 to
  1/32 and field sizes straddling the 2^150 switch. That is exactly why the risk
  is invisible: nothing is broken, so nothing draws attention.

  A repo that already suffered a regime-scope error twice (iterations 38-40,
  until iteration 41 made it impossible by construction) should not depend on
  five copies of a formula staying in step by luck.""")

    sec("3. THE GUARD")
    bad = disagreements()
    print(f"""
  This file PINS the duplicates to each other rather than consolidating them.
  Each file here is written to be read on its own -- a reader following
  m_star.py should not chase an import to learn what m_min is -- so the trade is
  one guard file against the drift risk. Iteration 41 made the same trade.

  disagreements found: {len(bad)}""")
    for label, args, vals in bad:
        print(f"    {label} at {args}: {vals}")
    print(f"  guard self-test (does it fail when a copy diverges?): "
          f"{'PASS' if self_test() else 'FAIL -- THE GUARD IS INERT'}")


if __name__ == "__main__":
    report()
