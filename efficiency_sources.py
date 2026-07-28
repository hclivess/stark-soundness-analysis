"""
Auditing EFFICIENCY.md's remaining cited figures. Two of three had problems.

Iteration 52 found EFFICIENCY.md's NTT share was measured on MSM-paired systems,
which STARKs are not. That audit was productive enough to run on the rest, and
iteration 52 also asserted -- without checking -- that the OTHER source was
"on-target". This checks that assertion.

THE CLAIM
---------
EFFICIENCY.md section 1:

    "Front-end trace generation is already 20-30% of end-to-end time, and if the
     backend gets even 5x faster, front-end overhead rises 'to over 90%'
     (ZK-Tracer, arXiv 2605.25493)."

The inner quotation marks present "to over 90%" as a direct quote.

WHAT THE SOURCE ACTUALLY SUPPORTS
----------------------------------
VERIFIED, verbatim from the abstract:

    "While current hardware acceleration research has exclusively focused on
     backend proving, we identify that the frontend execution and trace
     generation phase is rapidly emerging as the new system bottleneck."

That is the qualitative claim, and it is exactly what EFFICIENCY.md's argument
uses. It stands.

NOT VERIFIED: the two numbers. The PDF extracts cleanly -- 5,612 words of clean
text -- and contains NO PERCENT SIGN ANYWHERE. Neither "20-30%" nor "over 90%"
appears in the extractable text. They may live in figures or tables, which do not
extract; that is plausible for a hardware paper. But a figure presented in
quotation marks should be locatable, and this one is not.

CAN THEY BE RECONSTRUCTED FROM THE ABSTRACT? NO.
--------------------------------------------------
The abstract gives two speedups: 1829x on trace generation, and 963x end-to-end
"when integrated with existing backend proving accelerators". Amdahl's law on
those looks like it should pin the front-end fraction p, and it does not.

If the front end alone accounted for the 963x:

    p = (1 - 1/963) / (1 - 1/1829) = 99.95%

But the abstract says the backend was ALSO accelerated, so part of the 963x came
from there and the true p is lower -- 99.95% is only an upper bound. Solving for
the backend acceleration each p would require:

    p = 50%  needs a 654x backend accelerator
    p = 70%  needs 458x
    p = 90%  needs 183x
    p = 95%  needs  96x
    p = 99%  needs  20x

Every one of those is a plausible ASIC figure, so the abstract's numbers are
consistent with essentially any front-end fraction from 50% up. They neither
confirm nor refute "20-30% today, over 90% after a 5x backend speedup".

WHAT IT COSTS: NOTHING COMPUTES WITH THEM
-------------------------------------------
Unlike iteration 52's NTT share -- which fed a 20x prover penalty and a
capacity-route verdict -- these two numbers appear only in prose, in three
places (README.md:133, EFFICIENCY.md:48, EFFICIENCY.md:106). No code reads them.
So the correction is presentational: the qualitative claim is verified and
stands, and the percentages should not be stated as though they were.

THE PATTERN, SHARPENED IN ITERATION 54
----------------------------------------
The sweep is now complete -- all three of EFFICIENCY.md's cited claims audited:

    NTT share 90-91%        MIS-SCOPED: measured on MSM-paired systems (it 52)
    front-end 20-30% / 90%  UNLOCATABLE in the cited paper           (it 53)
    lookup singularity      CLEAN: every clause verbatim in Jolt's abstract

Iteration 53 called this "unflattering about the citation discipline". With the
third audited that is too broad, and the accurate diagnosis is narrower and more
useful: THE QUALITATIVE CLAIM WAS SOURCED PRECISELY; BOTH QUANTITATIVE ONES WERE
NOT.

Section 3's every clause tracks Jolt's abstract word for word -- "circuits that
only perform lookups into pre-determined lookup tables", "of size more than
2^128, that depends only on the ISA", "structured, avoiding costs that grow
linearly with the table size". Nothing there is loose.

So the failure mode was specific: prose was quoted carefully and numbers were
not. Both numeric claims survived anyway because the arguments they support rest
on ORDERINGS rather than magnitudes -- T_encode and T_commit dominate, T_open is
small, the front end is rising -- which is why the document's conclusions held
while two of its three figures did not.

The fix is to give EFFICIENCY.md's numbers the treatment SOURCES.md gives every
parameter: a verbatim quote next to each. Iteration 54 adds that block.
"""

import math

TRACE_SPEEDUP = 1829.0        # ZK-Tracer abstract
END_TO_END = 963.0            # ZK-Tracer abstract, backend also accelerated


def frontend_fraction_if_alone(s_front=TRACE_SPEEDUP, s_total=END_TO_END):
    """Amdahl, assuming ONLY the front end was accelerated. An upper bound."""
    return (1 - 1 / s_total) / (1 - 1 / s_front)


def backend_speedup_needed(p, s_front=TRACE_SPEEDUP, s_total=END_TO_END):
    """Given a front-end fraction p, the backend acceleration the totals imply."""
    rhs = 1 / s_total - p / s_front
    return (1 - p) / rhs if rhs > 0 else float("inf")


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. WHAT THE SOURCE SUPPORTS, AND WHAT IT DOES NOT")
    print("""
  VERIFIED, verbatim from the abstract:

    "While current hardware acceleration research has exclusively focused on
     backend proving, we identify that the frontend execution and trace
     generation phase is rapidly emerging as the new system bottleneck."

  That is the qualitative claim EFFICIENCY.md's argument uses. It stands.

  NOT VERIFIED: "20-30% of end-to-end time" and "to over 90%". The PDF extracts
  cleanly -- 5,612 words -- and contains NO PERCENT SIGN ANYWHERE. They may live
  in figures or tables, which do not extract. But EFFICIENCY.md presents "to over
  90%" in quotation marks, and a direct quote should be locatable.""")

    sec("2. THE ABSTRACT'S OWN NUMBERS CANNOT RECONSTRUCT THEM")
    p_upper = frontend_fraction_if_alone()
    print(f"""
  The abstract gives {TRACE_SPEEDUP:.0f}x on trace generation and {END_TO_END:.0f}x end-to-end "when
  integrated with existing backend proving accelerators".

  If the front end ALONE accounted for the end-to-end figure, Amdahl gives

      p = (1 - 1/{END_TO_END:.0f}) / (1 - 1/{TRACE_SPEEDUP:.0f}) = {p_upper:.2%}

  But the backend was also accelerated, so part of that came from there and the
  true p is lower. {p_upper:.2%} is only an upper bound. Solving for the backend
  acceleration each candidate p would require:\n""")
    print(f"  {'front-end p':>12} {'backend accel needed':>22}")
    print("  " + "-" * 38)
    for p in (0.50, 0.70, 0.90, 0.95, 0.99):
        print(f"  {p:>11.0%} {backend_speedup_needed(p):>21.0f}x")
    print("""
  Every one is a plausible ASIC figure, so the abstract is consistent with
  essentially any front-end fraction from 50% up. It neither confirms nor
  refutes the quoted percentages.""")

    sec("3. WHAT IT COSTS, AND THE PATTERN")
    print("""
  Nothing computes with these two numbers. They appear only in prose, at
  README.md:133, EFFICIENCY.md:48 and EFFICIENCY.md:106. That is unlike
  iteration 52's NTT share, which fed a 20x prover penalty and a capacity-route
  verdict. So this correction is presentational.

  The pattern is the finding. Two of EFFICIENCY.md's three headline figures now
  have sourcing problems:

      NTT share 90-91%         measured on MSM-paired systems  (iteration 52)
      front-end 20-30% / 90%   not locatable in the cited paper (this one)
      lookup singularity       Jolt/Lasso, not audited here

  Both survived because the arguments they support rest on ORDERINGS rather than
  magnitudes -- T_encode and T_commit dominate, T_open is small, the front end is
  rising. Reassuring about the argument; unflattering about the citation
  discipline, which was looser in EFFICIENCY.md than in SOURCES.md, where every
  parameter carries a verbatim quote.""")


if __name__ == "__main__":
    report()
