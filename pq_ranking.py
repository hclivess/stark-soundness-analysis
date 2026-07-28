"""
HORIZONS thread 3, the "most under-analysed item in the repo": no reorder.

Thread 3 read: "The quantum column, redone. frontier.py's Grover adjustment
predates the UDR/JBR/T regime split. Grinding is still halved, but the *binding
term* differs per regime, so the post-quantum ranking may reorder. This is
directly on the stated brief and is the most under-analysed item in the repo."

It was right to flag it, and the tools to answer it did not exist when it was
written. They do now:

  iteration 24  PQ = classical/2 is a CEILING, and the loss is term-dependent
  iteration 26  hash terms lose a factor 3 (BHT above, Zhandry below), not 2
  iteration 27  the BCS additive constant costs 0.90 classical / 0.60 PQ bits
  iteration 48  SP1's binding components, machine-verified

THE HYPOTHESIS IS FALSIFIED, AND THE REASON IS STRUCTURAL
-----------------------------------------------------------
A reorder needs different systems to take different losses. That requires their
binding terms to come from different families. They do not:

    system      classical   lambda   hash PQ   search PQ   PQ total   binds
    ZisK              128      256      84.7        64.0       64.0   search
    SP1               100      248      82.1        50.0       50.0   search
    OpenVM            100      256      84.7        50.0       50.0   search
    Airbender          67      256      84.7        33.5       33.5   search
    Miden              55      256      84.7        27.5       27.5   search
    Pico               53      256      84.7        26.5       26.5   search
    RISC Zero          48      256      84.7        24.0       24.0   search

Every one is bound by its QUERY phase (iteration 24, confirmed for SP1 by
machine-checked `queryErr = 100` in iteration 48), and the query phase is a
search term. Search terms all lose exactly a factor 2. A uniform factor preserves
order, so:

    naive classical/2:  ZisK, SP1, OpenVM, Airbender, Miden, Pico, RISC Zero
    term-dependent   :  ZisK, SP1, OpenVM, Airbender, Miden, Pico, RISC Zero

Identical. The post-quantum ranking is exactly the classical ranking, and the
regime split that thread 3 worried about does not touch it -- because the regime
determines which FIELD term binds, and every field term is a search term.

WHAT WOULD CAUSE A REORDER, AND HOW FAR AWAY IT IS
----------------------------------------------------
The hash term is the only one with a different exponent. It binds when

    lambda/3 - log2(3.5)/3  <  classical/2      i.e.  lambda < 3*(classical/2 + 0.6)

Margins at deployed digest sizes:

    system      needs lambda >=    has    margin
    ZisK               193.8        256      62.2
    SP1                151.8        248      96.2
    OpenVM             151.8        256     104.2
    Airbender          102.3        256     153.7
    Miden               84.3        256     171.7
    Pico                81.3        256     174.7
    RISC Zero           73.8        256     182.2

ZisK has the thinnest margin precisely because it has the most classical bits.
Nobody is close: a reorder needs a system with more than

    2 * (256/3 - 0.6)  =  169 classical bits at a 256-bit digest

and the highest deployed figure is ZisK's 128.

A CONSISTENCY CHECK THAT WAS NOT PLANNED
------------------------------------------
Read as a design rule rather than an audit, the same threshold says: to reach a
target of T post-quantum bits from search terms, the digest must satisfy
lambda >= 3*(T + log2(3.5)/3). At T = 128 that is 385.8 bits.

Iteration 27 derived the 128-PQ digest requirement independently, from the BCS
additive error's birthday shape, and got 386. Two routes, three significant
figures. It also explains the earlier result in one line: a system built to 128
PQ bits would be the first to cross the reorder threshold, which is exactly why
iteration 27 found that a 256-bit digest caps such a design at 85 PQ bits.
"""

import math

LOG2_C = math.log2(3.5)          # BCS additive constant, iteration 27

# (name, classical bits reported, digest bits). SP1's 248 and Airbender's 256
# are read from soundcalc-lean; the rest default to the 256-bit norm.
SYSTEMS = [("ZisK 0.16.1", 128, 256), ("SP1 6.1.0", 100, 248),
           ("OpenVM 1.5.0", 100, 256), ("Airbender", 67, 256),
           ("Miden", 55, 256), ("Pico", 53, 256), ("RISC Zero", 48, 256)]


def hash_pq(lam):
    """Quantum collision: Theta(2^(lambda/3)), carrying the BCS constant."""
    return lam / 3.0 - LOG2_C / 3.0


def hash_classical(lam):
    """Birthday: 2^(lambda/2), same constant."""
    return lam / 2.0 - LOG2_C / 2.0


def search_pq(classical):
    """Grover on a Fiat-Shamir search term: exactly half, iteration 24."""
    return classical / 2.0


def pq_total(classical, lam):
    return min(search_pq(classical), hash_pq(lam))


def binding_family(classical, lam):
    return "search" if search_pq(classical) <= hash_pq(lam) else "HASH"


def min_digest_for(classical):
    """Smallest lambda at which the hash term stops binding."""
    return 3.0 * (classical / 2.0 + LOG2_C / 3.0)


def reorder_threshold(lam=256):
    """Classical bits above which the hash term would bind at digest `lam`."""
    return 2.0 * (lam / 3.0 - LOG2_C / 3.0)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. EVERY DEPLOYED SYSTEM IS BOUND BY A SEARCH TERM")
    print(f"  {'system':<15} {'classical':>10} {'lambda':>7} {'hash PQ':>9} "
          f"{'search PQ':>10} {'PQ total':>9} {'binds':>8}")
    print("  " + "-" * 72)
    for nm, cl, lam in SYSTEMS:
        print(f"  {nm:<15} {cl:>10} {lam:>7} {hash_pq(lam):>9.1f} "
              f"{search_pq(cl):>10.1f} {pq_total(cl, lam):>9.1f} "
              f"{binding_family(cl, lam):>8}")
    print("""
  The regime split thread 3 worried about decides which FIELD term binds -- and
  every field term is a search term, losing exactly a factor 2 (Grover achieves,
  BBBV forbids better). The hash term is the only one with a different exponent,
  and it binds nowhere.""")

    sec("2. SO THE RANKING DOES NOT REORDER")
    naive = [nm for nm, cl, lam in sorted(SYSTEMS, key=lambda z: -z[1] / 2)]
    term = [nm for nm, cl, lam in sorted(SYSTEMS,
                                         key=lambda z: -pq_total(z[1], z[2]))]
    print(f"  naive classical/2 : {', '.join(naive)}")
    print(f"  term-dependent    : {', '.join(term)}")
    print(f"\n  {'IDENTICAL -- no reorder' if naive == term else 'REORDERED'}."
          f" A uniform factor preserves order, and the factor is uniform because")
    print("  the binding family is uniform.")

    sec("3. WHAT WOULD CAUSE ONE, AND HOW FAR AWAY IT IS")
    print(f"  the hash term binds when lambda < 3*(classical/2 + {LOG2_C/3:.2f})\n")
    print(f"  {'system':<15} {'needs lambda >=':>16} {'has':>6} {'margin':>9}")
    print("  " + "-" * 50)
    for nm, cl, lam in SYSTEMS:
        need = min_digest_for(cl)
        print(f"  {nm:<15} {need:>16.1f} {lam:>6} {lam - need:>9.1f}")
    thr = reorder_threshold(256)
    print(f"""
  ZisK has the thinnest margin precisely because it has the most classical bits.
  A reorder needs a system above {thr:.0f} classical bits at a 256-bit digest, and the
  highest deployed figure is ZisK's 128.""")

    sec("4. AN UNPLANNED CONSISTENCY CHECK WITH ITERATION 27")
    t128 = 3.0 * (128 + LOG2_C / 3.0)
    print(f"""
  Read as a design rule: to reach T post-quantum bits from search terms, the
  digest must satisfy lambda >= 3*(T + log2(3.5)/3). At T = 128 that is {t128:.1f}.

  Iteration 27 derived the 128-PQ digest requirement independently, from the BCS
  additive error's birthday shape, and got 386. Two routes, three significant
  figures.

  It also explains that earlier result in one line: a system built to 128 PQ
  bits would be the first to cross the reorder threshold of {thr:.0f} classical bits,
  which is exactly why iteration 27 found a 256-bit digest caps such a design at
  {hash_pq(256):.0f} PQ bits.""")


if __name__ == "__main__":
    report()
