"""
NADO is a fifth case for the folding finding -- and the one where the two
objectives disagree. Iteration 83's "they agree" was true, and not general.

Iteration 82 found four of seven deployed zkVMs Pareto-dominated, the whole gap
being fold arity. Iteration 83 answered the obvious objection -- that a wider
fold costs recursion -- by showing the recursion circuit gets 11-41% SMALLER,
and that proof size and verifier work are minimised by the SAME arity, 8.

NADO now qualifies for that analysis. Iteration 85 established it is query-bound
after the GF(p^3) migration, so Proposition 11 applies to it, and it ships
folding 2 -- the configuration every dominated system shipped.

IT IS DOMINATED, AND BY MORE THAN THE ZKVMS WERE
--------------------------------------------------
At DEGREE = 3 (E = 192), trace 2^17, blowup 2, 320 queries:

    batch      f=2      f=4      f=8     f=16    saving
       50     1082      864      857     1004       21%
      100     1457     1239     1232     1379       15%
      300     2957     2739     2732     2879        8%
     1000     8207     7989     7982     8129        3%

The saving falls with trace width because leaf data is width-proportional and
fold-independent, so it dilutes the effect -- the same dilution iteration 60
found in the expected/worst ratios.

BUT THE VERIFIER WANTS 4, NOT 8
---------------------------------
    f     rounds   auth nodes   leaf elems     total
    2         17        14463        10880     25343
    4          8         7976        10240     18216   <- argmin
    8          5         5832        12800     18632
   16          4         4780        20480     25260

For the four zkVMs both objectives chose 8. For NADO the verifier chooses 4.
Iteration 83 said "the two objectives agree rather than trading" -- true of
every system it examined, and not a general fact.

WHAT ACTUALLY DRIVES IT IS nu, NOT s
--------------------------------------
The first guess was the query count: leaf cost is s*f per round, so a high s
should penalise wide folds, and NADO's 320 is far above the zkVMs' 82-193. But
sweeping both:

    nu    s=100   s=200   s=320   s=500
    16        4       4       4       4
    18        8       4       4       4
    21        8       8       8       8
    24        8       8       8       8
    27        8       8       8       8

    (verifier-work argmin; the proof-size argmin is 8 throughout)

The domain size decides it. Above nu = 21 the argmin is 8 for every query count
tried; at nu = 18 it depends on s; at nu = 16 it is 4 regardless. Fewer rounds
means the per-round leaf term carries more of the total, and a small domain has
few rounds to begin with.

Every dominated zkVM runs nu = 21 to 24. NADO runs nu = 18 -- the smallest in
the set -- which is why it is the one case where the objectives separate.
Iteration 83's claim holds for the systems it checked, verified at their own
(nu, s), and generalises only above nu = 21.

SO THE RECOMMENDATION FOR NADO IS 4, NOT 8
--------------------------------------------
f = 4 gives 864 KiB against f = 8's 857 at batch 50 -- 0.8% apart, inside any
reasonable modelling error -- while being the clear verifier-work optimum
(18216 against 18632). Taking 8 would buy a rounding error in proof size and
pay 2% more verifier work.

That is a smaller change than the zkVMs need, and it lands on the arity Miden
already ships. NADO's fri.py objects to changing the fold shape at all:

    FRI_BLOWUP stays 2 for the SAME reason: a lower rate gives more bits/query
    but changes the fold shape, which would ripple into every recursion AIR.

The objection stands as an estimate of WORK. It does not describe the result:
the recursion circuit at f = 4 is 28% smaller than at f = 2 (18216 against
25343), so the ripple ends somewhere better than it started.
"""

import math
import sys

from folding_recursion_cost import verifier_work, best_fold, total_work
from proof_size_exact import fri_proof_bits

KIB = 8 * 1024
NADO_PATH = "/root/nado"

NADO_T, NADO_R, NADO_S, NADO_HASH = 17, 1, 320, 256
NADO_NU = NADO_T + NADO_R
FOLDS = (2, 4, 8, 16)
BATCHES = (50, 100, 300, 1000)

# the four zkVMs iteration 82 found dominated, at their own (nu, s)
ZKVMS = [("SP1", 23, 124), ("OpenVM", 24, 193), ("Pico", 23, 82),
         ("Miden", 21, 27)]


def live_E():
    if NADO_PATH not in sys.path:
        sys.path.insert(0, NADO_PATH)
    try:
        from execnode.stark import extf
        return 64 * extf.DEGREE
    except Exception:
        return 192


def schedule(nu, f):
    out, n, k = [], nu, int(math.log2(f))
    while n > k:
        out.append(f)
        n -= k
    return out or [2]


def nado_size(batch, f, E=None):
    E = live_E() if E is None else E
    return fri_proof_bits(NADO_HASH, E, batch, NADO_S, 2 ** NADO_NU,
                          schedule(NADO_NU, f), 2.0 ** -NADO_R, True) // KIB


def size_saving(batch):
    row = [nado_size(batch, f) for f in FOLDS]
    return 1 - min(row) / row[0]


def best_size_fold(batch):
    row = {f: nado_size(batch, f) for f in FOLDS}
    return min(row, key=row.get)


def objectives_agree(nu, s):
    """Do proof size and verifier work choose the same arity? (size argmin is 8
    across the whole region swept, so this is the verifier's choice.)"""
    return best_fold(nu, s) == 8


def divergence_sweep(nus=(16, 18, 21, 24, 27), ss=(100, 200, 320, 500)):
    return {(nu, s): best_fold(nu, s) for nu in nus for s in ss}


def nu_threshold(ss=(100, 200, 320, 500)):
    """Smallest nu at which the argmin is 8 for every query count tried."""
    for nu in range(14, 32):
        if all(best_fold(nu, s) == 8 for s in ss):
            return nu
    return None


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    E = live_E()
    sec("1. NADO IS DOMINATED TOO, AND BY MORE THAN THE ZKVMS WERE")
    print(f"\n  DEGREE-derived E = {E}, trace 2^{NADO_T}, blowup {2**NADO_R}, "
          f"{NADO_S} queries\n")
    print(f"  {'batch':>6}" + "".join(f"{'f=' + str(f):>8}" for f in FOLDS)
          + f"{'saving':>9}")
    print("  " + "-" * 50)
    for b in BATCHES:
        print(f"  {b:>6}" + "".join(f"{nado_size(b, f):>8}" for f in FOLDS)
              + f"{size_saving(b):>8.0%}")
    print("""
  The saving falls with trace width: leaf data is width-proportional and
  fold-independent, so it dilutes the effect -- the same dilution iteration 60
  found in the expected/worst ratios.""")

    sec("2. BUT THE VERIFIER WANTS 4, NOT 8")
    print(f"\n  {'f':>3} {'rounds':>8} {'auth nodes':>12} {'leaf elems':>12} "
          f"{'total':>10}")
    print("  " + "-" * 48)
    for f in FOLDS:
        r, n, l, t = verifier_work(NADO_NU, NADO_S, f)
        mark = "  <- argmin" if f == best_fold(NADO_NU, NADO_S) else ""
        print(f"  {f:>3} {r:>8} {n:>12.0f} {l:>12} {t:>10.0f}{mark}")
    print(f"""
  For the four zkVMs both objectives chose 8. For NADO the verifier chooses
  {best_fold(NADO_NU, NADO_S)}. Iteration 83 said "the two objectives agree rather than trading" --
  true of every system it examined, and not a general fact.""")

    sec("3. WHAT DRIVES IT IS nu, NOT s")
    print("""
  The first guess was the query count -- leaf cost is s*f per round, and NADO's
  320 is far above the zkVMs' 82-193. Sweeping both says otherwise:\n""")
    ss = (100, 200, 320, 500)
    print(f"  {'nu':>4}" + "".join(f"{'s=' + str(s):>8}" for s in ss))
    print("  " + "-" * 36)
    for nu in (16, 18, 21, 24, 27):
        print(f"  {nu:>4}" + "".join(f"{best_fold(nu, s):>8}" for s in ss))
    print(f"""
  (verifier-work argmin; the proof-size argmin is 8 throughout)

  The DOMAIN SIZE decides it. Above nu = {nu_threshold()} the argmin is 8 for every query
  count tried; at nu = 18 it depends on s; at nu = 16 it is 4 regardless. Fewer
  rounds means the per-round leaf term carries more of the total.

  Every dominated zkVM runs nu = 21 to 24:\n""")
    for nm, nu, s in ZKVMS:
        print(f"      {nm:<8} nu={nu:<3} s={s:<4} argmin {best_fold(nu, s)}   "
              f"{'agrees' if objectives_agree(nu, s) else 'DISAGREES'}")
    print(f"      {'NADO':<8} nu={NADO_NU:<3} s={NADO_S:<4} argmin "
          f"{best_fold(NADO_NU, NADO_S)}   "
          f"{'agrees' if objectives_agree(NADO_NU, NADO_S) else 'DISAGREES'}")
    print("""
  NADO runs the smallest domain in the set, which is why it is the one case
  where the objectives separate. Iteration 83's claim holds for the systems it
  checked and generalises only above nu = 21.""")

    sec("4. SO THE RECOMMENDATION IS 4, NOT 8")
    s4, s8 = nado_size(50, 4), nado_size(50, 8)
    w4, w8 = total_work(NADO_NU, NADO_S, 4), total_work(NADO_NU, NADO_S, 8)
    w2 = total_work(NADO_NU, NADO_S, 2)
    print(f"""
  f = 4 gives {s4} KiB against f = 8's {s8} at batch 50 -- {abs(s4-s8)/s8:.1%} apart, inside any
  reasonable modelling error -- while being the clear verifier-work optimum
  ({w4:.0f} against {w8:.0f}). Taking 8 would buy a rounding error in proof size and
  pay {w8/w4-1:.0%} more verifier work.

  A smaller change than the zkVMs need, landing on the arity Miden already
  ships. NADO's fri.py objects to changing the fold shape at all:

      FRI_BLOWUP stays 2 for the SAME reason ... changes the fold shape, which
      would ripple into every recursion AIR.

  That stands as an estimate of WORK. It does not describe the RESULT: the
  recursion circuit at f = 4 is {1-w4/w2:.0%} smaller than at f = 2 ({w4:.0f} against
  {w2:.0f}), so the ripple ends somewhere better than it started.""")


if __name__ == "__main__":
    report()
