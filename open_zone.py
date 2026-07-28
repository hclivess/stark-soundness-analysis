"""
Two audits the repository owed itself: the evidence tier of its own table, and
how much room is actually left between Johnson and the counterexamples.

WHY THIS FILE
-------------
ceiling_anatomy.py section 4 says the action-orbit line is "the single largest
unclaimed win in this whole repository" -- 22 bits, from a = 0. That claim, and
the threshold-halving row next to it, entered the BOUNDS table from remembered
eprint IDs. SOURCES.md had no entry for either. Given that this repo has already
been burned once by a remembered citation (the RS capacity conjecture, README
correction 1), both were overdue for verification.

PART A -- THE CITATIONS ARE ACCURATE
-------------------------------------
Fetched both abstract pages directly (eprint abstract pages serve fine; only the
PDFs sit behind Cloudflare).

  eprint 2026/858, Chai & Fan (IoTeX Network), "FRI Soundness Above the Johnson
  Bound via Threshold Halving":
      "eps_FRI <= nR/|F| + (1 - delta/2)^q"
  and "(B) The ~2x query overhead is optimal within the correlated-agreement
  framework".

  eprint 2026/861, Chai & Fan, "Action-Orbit FRI Soundness Above the Johnson
  Radius: A Rigorous O(1)/|F| Bound on Plain Reed-Solomon...":
      "the first rigorous O(1)/|F| FRI commit-phase soundness bound for plain
      Reed-Solomon above the Johnson radius ... unconditional for sparse
      adversary inputs; for general inputs it reduces to a single
      sparse-worst-case dominance conjecture (Q2)".

Both match what the BOUNDS table records: a = 1 with C = r (rounds) for 858, and
a = 0 conditional on Q2 for 861. No correction needed to the numbers.

PART B -- BUT THE TABLE MIXES EVIDENCE TIERS SILENTLY
------------------------------------------------------
What the verification did surface is a provenance asymmetry the table never
declared. Its rows are not equally supported:

  TIER 1 -- implemented in Ethereum's soundcalc, cross-validated against seven
     deployed zkVMs, and reproduced by this repo's model to 0.1 bits where FRI
     binds:                                    BCIKS20, BCHKS25, UDR
  TIER 2 -- peer-reviewed or established-group preprint, fetched and read from
     source in this repo:                      Roth-Zemor/Diamond-Posen (CiC
     2024), Jeronimo-Liu-Rajpal, Goyal-Guruswami-Sun-Wootters
  TIER 3 -- unreviewed preprint, single group, "first ever" claim on a central
     open problem:                             Chai-Fan 2026/858, 2026/861

Two observations about tier 3, both weak individually and neither a refutation:
  - Goyal-Guruswami-Sun-Wootters (arXiv 2607.08516, 2026-07-09) surveys this
    exact literature in 37 references, lists the limitation results
    [DG25, CS25, BSCH+25, KKH26] and cites the ABF 2026 survey -- and cites
    neither Chai-Fan paper, though 861 claims to have settled "the central open
    question in the proximity-gap line" three months earlier.
  - Neither paper is indexed in OpenAlex at all. That is genuinely weak evidence:
    eprint preprints are often unindexed, and Diamond-Posen appears only because
    CiC published it.

The point is not that the results are wrong -- I have not read either proof, and
the PDFs are unreachable from here. The point is that this repository's single
largest claimed win rests on its weakest-supported source, and never said so.
The BOUNDS table now carries a tier column.

PART C -- HOW MUCH ROOM IS LEFT ABOVE JOHNSON?
------------------------------------------------
Any O(1)/|F| bound above the Johnson radius has to live in the zone between the
Johnson radius (where BCHKS25 already works) and the radius where the known
counterexamples start biting. That zone is being squeezed from above:

  Kambire, arXiv 2604.09724 (2026): proximity gaps "fail at radii that are
  O(1/log n) below the capacity rate of the code, where n is the length of
  the code."

So the surviving open zone at deployed parameters is

    [ 1 - sqrt(rho),  1 - rho - c/log n ]     width = sqrt(rho) - rho - c/log n

and it is EMPTY once c >= (sqrt(rho) - rho) * log n. At n = 2^22 that threshold
is c = 4.6 to 5.5 depending on rate. Section 3 tabulates it.

This is the honest bound on what Q2 could ever be worth: if Kambire's hidden
constant is around 5 or more, there is no open zone left at deployed sizes and
the action-orbit result would have nothing to apply to. Nobody has pinned that
constant, so the 22-bit figure the repo quotes should be read as conditional on
BOTH Q2 and on the open zone being non-empty -- two independent unknowns, where
the repo previously flagged one.

CORRECTED IN ITERATION 32 -- SOURCE AND SHAPE
----------------------------------------------
This file cites Kambire (arXiv 2604.09724) for the near-capacity failure. That
note says up front it "flesh[es] out a sketch by Krachun and Kazanin"; the
PRIMARY source is Krachun-Kazanin-Habock, "Failure of proximity gaps close to
capacity", eprint 2026/782, cited as [KKH26] by Goyal-Guruswami-Sun-Wootters.
Its abstract puts the failure at

    eta = Theta_rho(1/log n)

-- note the SUBSCRIPT. The constant is RATE-DEPENDENT. Section 3 sweeps a single
rate-independent c across all three rates, which is the wrong shape: the
emptying threshold is c(rho), not c, so the per-rate columns are not comparable
as drawn. The qualitative conclusion is unaffected -- the zone can be empty at
deployed n, so Q2's value rests on two unknowns rather than one -- but each rate
column should be read on its own, not across.
"""

import math

LOG2_N = 22.0        # deployed trace+blowup domain, n = 2^22


def johnson_radius(rho):
    return 1.0 - math.sqrt(rho)


def capacity_radius(rho):
    return 1.0 - rho


def zone_width(rho, c=1.0, log2n=LOG2_N):
    """Surviving open zone between Johnson and Kambire's failure radius."""
    return max(0.0, (math.sqrt(rho) - rho) - c / log2n)


def c_empties_zone(rho, log2n=LOG2_N):
    """The hidden constant at which nothing is left above Johnson."""
    return (math.sqrt(rho) - rho) * log2n


TIERS = [
    ("BCIKS20",              1, "soundcalc + 7 zkVMs, model reproduces to 0.1b"),
    ("BCHKS25 JBR",          1, "soundcalc + 7 zkVMs, model reproduces to 0.1b"),
    ("UDR (BCHKS25 Cor 1.4)", 1, "soundcalc + 7 zkVMs, constant fixed at -2"),
    ("Roth-Zemor / D-P",     2, "IACR CiC 1(1) 2024, fetched and read"),
    ("Jeronimo-Liu-Rajpal",  2, "arXiv 2601.10047, fetched and read"),
    ("Goyal-Guruswami+",     2, "arXiv 2607.08516, fetched and read"),
    ("Kambire",              2, "arXiv 2604.09724, abstract read"),
    ("threshold halving",    3, "eprint 2026/858, abstract only, unreviewed"),
    ("action-orbit (Q2)",    3, "eprint 2026/861, abstract only, unreviewed"),
]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE TWO REMEMBERED CITATIONS CHECK OUT")
    print("""
  2026/858  "eps_FRI <= nR/|F| + (1 - delta/2)^q"        -> a = 1, C = rounds
  2026/861  "first rigorous O(1)/|F| ... above the Johnson radius ...
             reduces to a single sparse-worst-case dominance conjecture (Q2)"
                                                          -> a = 0, conditional

  Both match the BOUNDS table in ceiling_anatomy.py. No numbers change. This is
  the first time either has been checked against its source rather than recalled.""")

    sec("2. BUT THE TABLE MIXES EVIDENCE TIERS")
    print(f"  {'bound':<24} {'tier':>5}  support")
    print("  " + "-" * 84)
    for name, tier, note in TIERS:
        print(f"  {name:<24} {tier:>5}  {note}")
    print("""
  The repository's single largest claimed win -- 22 bits from a = 0 -- sits in
  tier 3, and the table never said so. Neither Chai-Fan paper is cited by
  Goyal-Guruswami-Sun-Wootters (2026-07-09), a 37-reference treatment of this
  exact literature that does cite the limitation results and the ABF survey;
  neither is indexed in OpenAlex. Both signals are weak. The conclusion is not
  that the results are wrong -- it is that they should not be quoted with the
  same confidence as a bound Ethereum ships in its reference calculator.""")

    sec("3. HOW MUCH ROOM IS LEFT ABOVE JOHNSON, AND FOR HOW LONG")
    print(f"  open zone = [1-sqrt(rho), 1-rho-c/log n],  n = 2^{LOG2_N:.0f}\n")
    print(f"  {'rate':>6} {'Johnson':>9} {'capacity':>9} {'full gap':>9} "
          + " ".join(f"{'c=%g' % c:>8}" for c in (1, 2, 5, 10)))
    print("  " + "-" * 74)
    for R in (1, 2, 3):
        rho = 2.0 ** -R
        row = " ".join(f"{zone_width(rho, c):>8.4f}" for c in (1, 2, 5, 10))
        print(f"  {'1/%d' % 2**R:>6} {johnson_radius(rho):>9.4f} "
              f"{capacity_radius(rho):>9.4f} "
              f"{capacity_radius(rho)-johnson_radius(rho):>9.4f} {row}")
    print(f"\n  {'rate':>6} {'c that empties the zone':>26}")
    print("  " + "-" * 34)
    for R in (1, 2, 3):
        print(f"  {'1/%d' % 2**R:>6} {c_empties_zone(2.0**-R):>26.2f}")
    print("""
  Kambire's constant is unspecified. At c around 5 there is nothing left above
  the Johnson radius at n = 2^22, and an O(1)/|F| bound in that zone would have
  no radius to apply to. So the 22-bit action-orbit figure is conditional on TWO
  unknowns -- Q2, and a non-empty open zone -- where this repo previously
  flagged only the first.

  Note the zone WIDENS with n: c/log n falls as n grows, so the zone is widest
  for large traces and empty for small ones. At c = 5 and rate 1/4 it opens up
  only past n = 2^22. That direction favours the claim at Ethereum scale, which
  is where 2026/861 pitches it.""")
    print(f"\n  {'log2 n':>8} {'zone width at rate 1/4, c=5':>30}")
    print("  " + "-" * 40)
    for l2 in (16, 20, 22, 24, 28):
        print(f"  {l2:>8} {zone_width(0.25, 5.0, l2):>30.4f}")


if __name__ == "__main__":
    report()
