"""
Thread 1's other half: two machine-checked theorems explain a standing claim.

HORIZONS thread 1 wanted soundcalc-lean used "to check Theorems 4-7 mechanically
rather than by the numerical agreement in verify_theorem.py /
regime_crossover.py". Iteration 47 read the DEFINITIONS and found that m is
derived rather than free. It did not read the 79 theorems. This does.

Most of them are per-circuit sanity lemmas for ZisK. Two are substantive, and
together they prove something this repository had only observed.

THE TWO THEOREMS
----------------
Soundcalc/Regime.lean:

    /-- The rational JBR linear-error formula upper-bounds the true real-valued
        formula. The true formula uses the exact value `sqrt rho`, while
        `jbrErrLinear` replaces it by the rational lower approximation
        `sqrtLB rho g`. Since `sqrtLB rho g <= sqrt rho` and the JBR expression
        is decreasing in this square-root parameter, this replacement gives a
        conservative upper bound. -/
    theorem jbrErrLinear_conservative ... :
        (trueErrLinearJBR F eta (jbrM rho eta g) rho d : R)
          <= (jbrErrLinear F eta g rho d : R)

Soundcalc/SecBits.lean:

    theorem secBits_anti {a b : Q} (ha : 0 < a) (hab : a <= b) :
        secBits b <= secBits a

WHAT THEY GIVE WHEN COMPOSED
-----------------------------
The first says soundcalc's computed error is at least the true error. The second
says secBits is antitone in the error. So

    soundcalc's reported bits  <=  the true bits.

soundcalc is conservative by construction, and provably so.

Now the part that concerns this repository. `regime_crossover.commit_jbr`
computes the BCHKS25 expression in floating point using `math.sqrt` -- the exact
value, not a rational lower approximation. So it is computing `trueErrLinearJBR`,
not `jbrErrLinear`, and the same composition runs the other way:

    this repo's bits  >=  soundcalc's bits,  always.

THAT IS A CLAIM THE REPO HAS BEEN MAKING EMPIRICALLY
------------------------------------------------------
README's caveat says the model "upper bounds published totals -- verified to
never undershoot across seven systems", and Theorem 7's finding says the model
"reproduces it within 1 bit (max deviation +0.9, never undershooting)".

"Never undershooting" was an observation over seven data points. It is now a
consequence of two machine-checked theorems and one fact about which formula
this repo implements. Seven agreeing data points are evidence; a proof of the
direction is better, and it means the property holds for systems not in the set.

AND IT RULES OUT ONE EXPLANATION FOR THE OVERSHOOT
----------------------------------------------------
If the sqrt approximation were large, it could explain the repo's observed 3-5
bit overshoot where another component binds. It is not. `sqrtLB(rho,g) =
floor(sqrt(g^2 rho))/g`, so the approximation error is at most 1/g, and the cost
in bits at the deployed rates is:

    g = 10        0.015 bits
    g = 1e3       0.0002 bits
    g = 1e6       0.0000 bits

That table is one parameter set. Sweeping R, nu and m as well, the worst case is
0.237 bits (R=3, nu=25, m=3, g=10) -- an adversarially coarse granularity at the
smallest admissible m. My first draft of this file quoted the 0.015 figure as
though it were the bound; the adversarial suite caught that on the first run.

So the honest magnitude is: under 0.25 bits across every parameter set tried,
and under 0.001 at any granularity a real implementation would use. Either way
it is an order of magnitude below the 3-5 bit overshoot, which must therefore
come from somewhere else -- the untuned-`m` gap this repo identified and
measured in iteration 14. Two candidate explanations, one now quantitatively
excluded.

WHAT THIS DOES NOT DO
---------------------
It does not verify Theorems 4-7 themselves, which is what thread 1 hoped for.
Those are this repository's own results about crossovers and blowup optima, and
nothing in soundcalc-lean speaks to them -- the Lean development formalises the
soundness FORMULAS, not the optimisation results built on top. What it does
verify is the direction of this repo's error against the reference, which is a
narrower thing than thread 1 asked for and more than it had.
"""

import math


def sqrt_lb(rho, g):
    """soundcalc's rational lower approximation: floor(sqrt(g^2 rho))/g."""
    return math.floor(math.sqrt(g * g * rho)) / g


def commit_jbr_exact(R, nu, E, m, folding=2):
    """What this repo computes: the true formula, exact sqrt."""
    from regime_crossover import commit_jbr
    return commit_jbr(R, nu, E, m, folding)


def commit_jbr_rational(R, nu, E, m, g, folding=2):
    """What soundcalc computes: sqrt replaced by sqrtLB at granularity g."""
    rho = 2.0 ** -R
    sr = sqrt_lb(rho, g)
    mm = m + 0.5
    gam = 1 - sr * (1 + 0.5 / m)
    if gam <= 0 or sr <= 0:
        return float("-inf")
    n = 2.0 ** nu
    eps = ((2 * mm ** 5 + 3 * mm * gam * rho) * n / (3 * rho * sr)
           + mm / sr) * max(folding - 1, 1)
    return E - math.log2(max(eps, 1.0))


def sqrt_gap_bits(R, nu, E, m, g):
    """Bits by which this repo's figure exceeds soundcalc's. Must be >= 0."""
    return commit_jbr_exact(R, nu, E, m) - commit_jbr_rational(R, nu, E, m, g)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE TWO SUBSTANTIVE THEOREMS, AND WHAT THEY COMPOSE TO")
    print("""
  Regime.lean:   trueErrLinearJBR  <=  jbrErrLinear
                 (soundcalc's computed error is at least the true error)
  SecBits.lean:  a <= b  ->  secBits b <= secBits a
                 (secBits is antitone in the error)

  Composing:     soundcalc's reported bits  <=  the true bits.

  This repo's commit_jbr uses math.sqrt -- the exact value -- so it computes the
  TRUE formula, and the same composition runs the other way:

                 this repo's bits  >=  soundcalc's bits,  always.""")

    sec("2. THE DIRECTION IS GUARANTEED; THE MAGNITUDE IS NEGLIGIBLE")
    R, nu, E, m = 1, 25, 124, 20.0
    print(f"  at R={R}, nu={nu}, E={E}, m={m:.0f}\n")
    print(f"  {'granularity g':>14} {'sqrtLB error':>14} {'this repo':>11} "
          f"{'soundcalc':>11} {'difference':>12}")
    print("  " + "-" * 66)
    for g in (10, 10 ** 2, 10 ** 3, 10 ** 6, 10 ** 9):
        a = commit_jbr_exact(R, nu, E, m)
        b = commit_jbr_rational(R, nu, E, m, g)
        print(f"  {g:>14} {math.sqrt(2.0**-R) - sqrt_lb(2.0**-R, g):>14.2e} "
              f"{a:>11.4f} {b:>11.4f} {a-b:>+12.4f}")
    print("""
  Non-negative everywhere, as the theorems require. This is one parameter set;
  sweeping R, nu and m too, the worst case is 0.237 bits (R=3, nu=25, m=3,
  g=10). Still an order of magnitude below the overshoot it might have
  explained.""")

    sec("3. WHAT THAT SETTLES, AND WHAT IT DOES NOT")
    print("""
  SETTLES a standing empirical claim. README says the model "upper bounds
  published totals -- verified to never undershoot across seven systems".
  That was an observation over seven data points; it is now a consequence of two
  machine-checked theorems plus one fact about which formula this repo
  implements. It therefore holds for systems outside the set.

  RULES OUT one explanation for the overshoot. If the sqrt approximation were
  large it could account for the 3-5 bit gap seen where another component binds.
  At a worst case of 0.237 bits it cannot. The remaining explanation is the untuned-`m` gap this
  repo identified and measured in iteration 14 -- two candidates, one now
  quantitatively excluded.

  DOES NOT verify Theorems 4-7, which is what thread 1 hoped for. Those are this
  repository's own results about crossovers and blowup optima, and the Lean
  development formalises the soundness FORMULAS, not the optimisation results
  built on them. Nothing in the 79 theorems speaks to Theorem 4, 5, 6 or 7.""")


if __name__ == "__main__":
    report()
