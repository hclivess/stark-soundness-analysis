"""
The objection I raised against iteration 82's own finding was backwards: folding
by 8 makes the recursion circuit SMALLER, not larger, and by the same margin.

Iteration 82 found four of seven deployed configurations Pareto-dominated at
equal security and equal prover cost, with the entire gap being the folding
factor. It then qualified the finding:

    Fold arity is not free in a system with recursion: the in-circuit FRI
    verifier's AIR is shaped by it, so changing the arity rewrites the recursion
    circuits.

That is true about the WORK of changing it. It carries an implicit claim about
the RESULT -- that a wider fold buys proof size at the recursion circuit's
expense -- and that claim is wrong. Iteration 74 measured the recursive-verifier
cost constant from deployed pipelines, so the question is arithmetic.

WHAT THE VERIFIER ACTUALLY DOES
---------------------------------
Per FRI round it hashes authentication paths and the revealed leaf. Folding by
f = 2^k changes both, in opposite directions:

    rounds        nu / k              falls as k grows
    auth nodes    sum over rounds     falls with fewer rounds
    leaf elements s * f per round     RISES, f siblings revealed per query

So there is an interior optimum, exactly as for proof size. At SP1's
configuration (nu = 23, s = 124):

    f   rounds   auth nodes   leaf elems   total   vs f=2
    2       22        15574         5456   21030    1.00x
    4       11         8275         5456   13731    0.65x
    8        7         5848         6944   12792    0.61x
   16        5         4636         9920   14556    0.69x

Leaves grow 27% from f=2 to f=8; auth nodes fall 62%. Net: the verifier does
39% LESS work.

AND IT HOLDS FOR EVERY DOMINATED SYSTEM
-----------------------------------------
    system     ships f   work@ship   work@f=8   change   best f
    SP1              2       21030      12792     -39%        8
    OpenVM           2       34143      20272     -41%        8
    Pico             2       14749       8757     -41%        8
    Miden            4        2967       2626     -11%        8

Four for four, and the argmin is 8 in every case -- the SAME arity that
minimises proof size in iteration 82. The two objectives do not trade against
each other here; they agree.

Through iteration 74's measured constant (1.2e4 to 4.7e4 trace cells per Merkle
node), SP1's recursive verifier goes from 2.6e8-9.9e8 cells at f=2 to
1.6e8-6.0e8 at f=8.

SO THE CAVEAT SHOULD HAVE BEEN NARROWER
-----------------------------------------
What survives: changing fold arity is real work. The AIR that checks a fold-8
round is structurally different from one that checks fold-2 -- it verifies eight
siblings per query rather than two -- so the recursion circuits must be
rewritten, and that is a project, not a constant change.

What does not survive: the suggestion that the resulting circuit is bigger.
It is 11-41% smaller, and the arity that minimises proof size also minimises
verifier work. Iteration 82 said "whether that is worth 30% is an engineering
judgement this repo cannot make". The judgement is easier than that made it
sound: the 30% is not paid for with recursion cost, it comes with a further
39% off the recursion circuit.

WHAT IS STILL NOT MODELLED
----------------------------
The AIR's per-row structure, as opposed to its size. A fold-8 verifier checks
eight siblings in one row where a fold-2 verifier checks two, so the row is
wider and the constraint degree may differ. This file counts hash work, which
iteration 74's constant converts to trace cells; it does not model constraint
degree, and a higher degree would raise the blowup the recursion circuit itself
needs. That is the remaining way the trade could turn out worse than it looks,
and nothing here rules it out.
"""

import math

from merkle_exact import soundcalc_auth_nodes

# iteration 74: trace cells per Merkle node, measured across Pico and SP1
CELLS_LO, CELLS_HI = 1.23e4, 4.71e4

# the four systems iteration 82 found dominated: (name, nu, s, shipped fold)
DOMINATED = [("SP1", 23, 124, 2), ("OpenVM", 24, 193, 2),
             ("Pico", 23, 82, 2), ("Miden", 21, 27, 4)]

FOLD_CHOICES = (2, 4, 8, 16)


def verifier_work(nu, s, f):
    """(rounds, auth nodes, leaf elements, total) hashed by an in-circuit FRI
    verifier over a domain 2^nu with s queries, folding by f each round."""
    k = int(math.log2(f))
    n, nodes, leaves, rounds = nu, 0.0, 0, 0
    while n > k:
        nodes += soundcalc_auth_nodes(s, n)
        leaves += s * f
        n -= k
        rounds += 1
    return rounds, nodes, leaves, nodes + leaves


def total_work(nu, s, f):
    return verifier_work(nu, s, f)[3]


def best_fold(nu, s, choices=FOLD_CHOICES):
    return min(choices, key=lambda f: total_work(nu, s, f))


def work_change(nu, s, f_from, f_to):
    """Fractional change in verifier work. Negative means cheaper."""
    return total_work(nu, s, f_to) / total_work(nu, s, f_from) - 1.0


def cells(nu, s, f):
    w = total_work(nu, s, f)
    return w * CELLS_LO, w * CELLS_HI


def leaves_rise_nodes_fall(nu, s, f_from=2, f_to=8):
    """(leaf growth, auth-node fall) -- the two halves of the trade."""
    _r1, n1, l1, _t1 = verifier_work(nu, s, f_from)
    _r2, n2, l2, _t2 = verifier_work(nu, s, f_to)
    return l2 / l1 - 1.0, n2 / n1 - 1.0


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE VERIFIER'S TRADE, WHICH RUNS THE SAME WAY AS THE PROOF'S")
    print("""
  Per FRI round the in-circuit verifier hashes authentication paths and the
  revealed leaf. Folding by f = 2^k moves them oppositely:

      rounds         nu / k            falls as k grows
      auth nodes     sum over rounds   falls with fewer rounds
      leaf elements  s * f per round   RISES, f siblings per query

  So there is an interior optimum. At SP1's configuration (nu = 23, s = 124):
""")
    print(f"  {'f':>3} {'rounds':>7} {'auth nodes':>11} {'leaf elems':>11} "
          f"{'total':>9} {'vs f=2':>8}")
    print("  " + "-" * 54)
    base = total_work(23, 124, 2)
    for f in FOLD_CHOICES:
        r, n, l, t = verifier_work(23, 124, f)
        print(f"  {f:>3} {r:>7} {n:>11.0f} {l:>11} {t:>9.0f} {t/base:>7.2f}x")
    dl, dn = leaves_rise_nodes_fall(23, 124)
    print(f"""
  Leaves grow {dl:+.0%} from f=2 to f=8; auth nodes fall {dn:+.0%}. Net: the verifier
  does {abs(work_change(23,124,2,8)):.0%} LESS work.""")

    sec("2. FOUR FOR FOUR, AND THE ARGMIN IS THE SAME 8")
    print(f"\n  {'system':<9} {'ships f':>8} {'work@ship':>11} {'work@f=8':>10} "
          f"{'change':>8} {'best f':>7}")
    print("  " + "-" * 58)
    for nm, nu, s, fs in DOMINATED:
        print(f"  {nm:<9} {fs:>8} {total_work(nu, s, fs):>11.0f} "
              f"{total_work(nu, s, 8):>10.0f} {work_change(nu, s, fs, 8):>+7.0%} "
              f"{best_fold(nu, s):>7}")
    lo1, hi1 = cells(23, 124, 2)
    lo2, hi2 = cells(23, 124, 8)
    print(f"""
  The same arity that minimises PROOF SIZE (iteration 82) minimises VERIFIER
  WORK. The two objectives agree rather than trading.

  Through iteration 74's measured constant, SP1's recursive verifier goes from
  {lo1:.1e}-{hi1:.1e} trace cells at f=2 to {lo2:.1e}-{hi2:.1e} at f=8.""")

    sec("3. SO ITERATION 82's CAVEAT WAS TOO STRONG")
    print(f"""
  SURVIVES: changing fold arity is real work. A fold-8 AIR verifies eight
  siblings per query where a fold-2 AIR verifies two, so the recursion circuits
  must be rewritten. That is a project.

  DOES NOT SURVIVE: the implication that the resulting circuit is bigger. It is
  {abs(work_change(23,124,2,8)):.0%} smaller for SP1 and 11-41% across the four. Iteration 82 wrote
  "whether that is worth 30% is an engineering judgement this repo cannot make".
  The judgement is easier than that: the 30% off the proof is not paid for in
  recursion cost -- it arrives with {abs(work_change(23,124,2,8)):.0%} off the recursion circuit as well.

  STILL NOT MODELLED: the AIR's per-row structure. A fold-8 verifier checks
  eight siblings in one row, so the row is wider and the constraint degree may
  differ. This counts HASH WORK, which iteration 74's constant converts to trace
  cells; it does not model constraint degree, and a higher degree would raise
  the blowup the recursion circuit itself needs. That is the remaining way the
  trade could be worse than it looks, and nothing here rules it out.""")


if __name__ == "__main__":
    report()
