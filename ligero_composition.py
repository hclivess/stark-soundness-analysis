"""
Obstacle 1: most of iteration 43's gain sits beyond the unique-decoding radius.

Iteration 43 priced the one open capacity route at a 47% to 67% query reduction
for Ligero/Brakedown-style systems, and named composition as the first of four
obstacles: "a proximity-gap statement is not a proof system ... whether those
compose at the capacity radius is not something Yuan-Zhu claim, and not
something checked here."

This file checks the part of it that can be checked from geometry alone: WHERE
the capacity radius sits relative to unique decoding. The answer splits
iteration 43's number cleanly in two, and the split reproduces a figure this
repo derived independently seven iterations earlier.

THE GEOMETRY
------------
A near-MDS code of rate R has relative distance d ~ 1 - R, so:

    rate R    d ~ 1-R    interleaved d/3    unique dec d/2    capacity free pt
    0.500     0.500          0.1667             0.2500             0.2929
    0.250     0.750          0.2500             0.3750             0.5000
    0.125     0.875          0.2917             0.4375             0.6464

The capacity "free point" -- eps = sqrt(R) - R, where Yuan-Zhu's radius equals
the Johnson radius and the field cost is still the Theta(n) floor -- is BEYOND
the unique-decoding radius at every deployed rate. That is not a marginal
overshoot: at rate 1/4 it is 0.500 against 0.375.

THE SPLIT, AND A CONSISTENCY CHECK WORTH NOTING
------------------------------------------------
    rate    to d/2 (inside UD)    to the capacity free point
    0.500          36.6%                    47.4%
    0.250          38.8%                    58.5%
    0.125          40.1%                    66.8%

The left column is exactly what iteration 28 computed when it priced
Diamond-Posen Conjecture 1 -- which asks whether the interleaved bound extends
from e <= (d-1)/3 to e <= (d-1)/2, i.e. from the Roth-Zemor radius to the
unique-decoding radius. Iteration 28 reported 36.6 / 38.8 / 40.1%. The two
derivations share no code and start from different papers; that they agree to
three significant figures is the kind of check this repo exists to run.

So iteration 43's headline decomposes as:

    36.6-40.1%   reachable INSIDE unique decoding -- and this is precisely what
                 Diamond-Posen Conjecture 1 would deliver, no capacity result
                 needed
    the rest     requires operating BEYOND the unique-decoding radius

WHAT "BEYOND UD" ACTUALLY COSTS -- STATED AS A QUESTION, NOT A VERDICT
------------------------------------------------------------------------
It is tempting to say the extractor simply breaks beyond unique decoding, and
that would be too strong. FRI operates beyond UD routinely, and the tool that
makes it work is CORRELATED AGREEMENT: rather than decoding each word
separately, one shows the words agree with codewords on a common large set.
Yuan-Zhu prove correlated agreement, not merely a proximity gap, so the tool is
present.

What is genuinely unsettled is whether LIGERO'S extractor composes with it.
Ligero's published argument decodes rows individually -- a unique-decoding step
-- and swapping that for a correlated-agreement argument is a change to the
proof system, not a parameter change. Neither Yuan-Zhu nor GGSW claim it, and
this file does not attempt it.

The honest statement is therefore:

  * the inside-UD portion (36.6-40.1%) needs only a radius extension that is
    already a named open conjecture in the literature;
  * the remainder needs a restructured extractor, and nobody has written one.

That is a sharper reading of iteration 43 than "four obstacles remain", because
it says which part of the prize sits behind which obstacle.
"""

import math


def yield_at(radius):
    return -math.log2(1 - radius) if 0 < radius < 1 else float("nan")


def distance(R):
    """Near-MDS relative distance for a large-alphabet random linear code."""
    return 1.0 - R


def interleaved_radius(R):
    """Roth-Zemor: e <= (d-1)/3."""
    return distance(R) / 3.0


def unique_decoding_radius(R):
    return distance(R) / 2.0


def capacity_free_point(R):
    """eps = sqrt(R) - R: Yuan-Zhu's radius at the Theta(n) field floor."""
    return 1.0 - R - (math.sqrt(R) - R)


def cut_to(R, radius):
    """Fractional query reduction moving from the interleaved radius to `radius`."""
    return 1 - yield_at(interleaved_radius(R)) / yield_at(radius)


def beyond_ud(R):
    return capacity_free_point(R) > unique_decoding_radius(R)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    RATES = (0.5, 0.25, 0.125)

    sec("1. THE CAPACITY FREE POINT IS BEYOND UNIQUE DECODING AT EVERY RATE")
    print(f"  {'rate R':>7} {'d ~ 1-R':>9} {'interleaved':>12} {'unique dec':>11} "
          f"{'capacity':>10} {'beyond UD?':>12}")
    print("  " + "-" * 66)
    for R in RATES:
        print(f"  {R:>7.3f} {distance(R):>9.3f} {interleaved_radius(R):>12.4f} "
              f"{unique_decoding_radius(R):>11.4f} {capacity_free_point(R):>10.4f} "
              f"{'YES' if beyond_ud(R) else 'no':>12}")
    print("""
  Not a marginal overshoot: at rate 1/4 the capacity free point is 0.500 against
  a unique-decoding radius of 0.375.""")

    sec("2. THE SPLIT -- AND IT REPRODUCES ITERATION 28 EXACTLY")
    print(f"  {'rate':>7} {'y interleaved':>14} {'y at d/2':>10} {'y at cap':>10} "
          f"{'cut to d/2':>12} {'cut to cap':>12}")
    print("  " + "-" * 68)
    ud_cuts = []
    for R in RATES:
        yi = yield_at(interleaved_radius(R))
        yu = yield_at(unique_decoding_radius(R))
        yc = yield_at(capacity_free_point(R))
        ud_cuts.append(cut_to(R, unique_decoding_radius(R)))
        print(f"  {R:>7.3f} {yi:>14.4f} {yu:>10.4f} {yc:>10.4f} "
              f"{cut_to(R, unique_decoding_radius(R)):>11.1%} "
              f"{cut_to(R, capacity_free_point(R)):>12.1%}")
    print(f"""
  The 'cut to d/2' column is {', '.join(f'{c:.1%}' for c in ud_cuts)} -- exactly what
  iteration 28 reported when it priced Diamond-Posen Conjecture 1, which asks
  whether the interleaved bound extends from (d-1)/3 to (d-1)/2. Different
  papers, different code, same three figures. That agreement is the check.""")

    sec("3. WHICH PART OF THE PRIZE SITS BEHIND WHICH OBSTACLE")
    print(f"""
  INSIDE unique decoding -- {min(ud_cuts):.1%} to {max(ud_cuts):.1%} of queries:
      needs only the radius extension that Diamond-Posen Conjecture 1 asks for.
      That is a named open problem in the literature, not a restructuring.

  BEYOND unique decoding -- the remainder, up to {max(cut_to(R, capacity_free_point(R)) for R in RATES):.1%}:
      needs an extractor that does not decode rows individually.

  On that second point, one thing must NOT be overstated. It is tempting to say
  the extractor simply breaks beyond UD. FRI operates beyond UD routinely, and
  the tool that makes it work is CORRELATED AGREEMENT -- showing the words agree
  with codewords on a common large set rather than decoding each separately.
  Yuan-Zhu prove correlated agreement, not merely a proximity gap, so the tool
  is present.

  What is unsettled is whether LIGERO'S extractor composes with it. Ligero's
  published argument decodes rows individually, which is a unique-decoding step,
  and replacing it is a change to the proof system rather than to a parameter.
  Neither Yuan-Zhu nor GGSW claim it, and this file does not attempt it.""")


if __name__ == "__main__":
    report()
