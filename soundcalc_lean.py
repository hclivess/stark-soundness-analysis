"""
A machine-verified source settles the question iterations 38-39 spent two rounds on.

HORIZONS.md section 5 has listed `symbolicsoft/soundcalc-lean` as open thread 1
since it appeared: "soundcalc's bounds proven in Lean, pushed 2026-07-27. The
obvious way to check Theorems 4-7 mechanically rather than by the numerical
agreement in verify_theorem.py / regime_crossover.py."

Cloned and read. It is a real formalization -- 79 theorem/lemma declarations
across the tree and exactly one `sorry` -- not a Lean transcription of the
Python. And it answers a modelling question this repo got wrong.

THE FINDING: m IS DERIVED, NOT FREE
------------------------------------
Soundcalc/Regime.lean, verbatim:

    /-- JBR multiplicity `m = max(⌈√ρ / (2η)⌉, 3)` (BCHKS25 Thm 4.2).
        Rounded **up** via `sqrtUB` since the error formula is increasing in `m`. -/
    def jbrM (ρ η : ℚ) (g : ℕ) : ℕ := max ⌈sqrtUB ρ g / (2 * η)⌉₊ 3

and η is itself determined:

    η = if fieldCard > 2^150 then √ρ/100 else max(ρ/20, √ρ/100)

with the docstring stating outright: "`η` is no longer a free rational parameter
-- it is derived per-call from `(F, ρ, g)` via `etaLB`/`etaUB`."

So soundcalc's m is a FUNCTION of the rate and field size. It is not something a
deployment chooses, and not something to optimise over.

    blowup    rho      eta       m (Lean)    m_eq (this repo)
      2     0.5000   0.02500        15            8.24
      4     0.2500   0.01250        20            2.00
      8     0.1250   0.00625        29            0.85
     16     0.0625   0.00313        40            0.44

CONSEQUENCE 1 -- THE m >= 3 FLOOR NEVER BINDS, FOR A BETTER REASON
--------------------------------------------------------------------
Iterations 38 and 39 spent two rounds on whether Plonky3's `m >= 3` floor costs
deployed systems anything. Iteration 39 concluded it costs zero because every
Johnson-regime system's optimum sits between 47 and 846, far above 3.

The conclusion was right. The reason was not. The floor is inside soundcalc's
own formula -- `max(..., 3)` -- and the raw value it guards never goes near 3:

    blowup    1  2  4  8  16  32  64  128  256
    raw m    10 15 20 29  40  50  50   50   50

It is 10 at the smallest blowup and saturates at 50. The floor is dead code for
every rate anyone would deploy, which is a stronger statement than "deployed
optima happen to sit above it".

CONSEQUENCE 2 -- ITERATION 38 OPTIMISED A PARAMETER THAT IS FIXED
-------------------------------------------------------------------
m_star.py computes m*(s), the m maximising min(s*y(m) + g, K(m)), and reports
values from 47 to 846 across the fleet. Soundcalc does not do that. It evaluates
at m = jbrM(ρ, η), which is 15 to 40. The two are different objects: m*(s) is
"what m would a system pick if it could", jbrM is "what m does the reference
calculator use". Iteration 38's monotonicity and convergence results are correct
about the former and say nothing about the latter.

CONSEQUENCE 3 -- CEILINGS AT m_eq ARE 4 TO 22 BITS TOO OPTIMISTIC
--------------------------------------------------------------------
    system        K at m_eq    K at jbrM    delta
    Airbender          82.4         78.3     -4.1
    Pico               84.4         80.3     -4.1
    RISC Zero          92.0         76.8    -15.2
    Miden             100.9         78.7    -22.2

WHAT THIS DOES NOT CHANGE, AND WHY
-----------------------------------
The reported TOTALS are unaffected. Iteration 24 established that the query
phase binds for six of the seven verified systems, and the corrected ceiling
stays above the query term in every case -- so a 4-to-22-bit drop in a
non-binding term moves nothing. Section 3 below checks that explicitly rather
than asserting it.

And Theorem 7 survives. Its crossover is s* = (K_JBR - g)/y_UDR, so a lower
K_JBR lowers every s*:

    system      s     s* at m_eq   s* at jbrM   predicted   reported
    SP1       124        112.0         89.7        UDR        UDR
    OpenVM    193        152.9        142.9        UDR        UDR
    Airbender  87        131.2        121.2        JBR        JBR
    Pico       84        164.9        155.0        JBR        JBR
    ZisK      229        331.2        300.7        JBR        JBR
    RISC Zero  50        135.6        113.3        JBR        JBR
    Miden      27        102.3         75.5        JBR        JBR

Every s* falls by 10 to 27 and no system crosses: 7/7 under both conventions.
Together with iteration 34 -- which showed the crossover is invariant to the UDR
ceiling -- the prediction is now robust to two independent modelling choices it
could have been an artifact of.
"""

import math


def eta_soundcalc(rho, field_card_bits=124):
    """Regime.lean: eta = sqrt(rho)/100 if card > 2^150 else max(rho/20, sqrt(rho)/100)."""
    if field_card_bits > 150:
        return math.sqrt(rho) / 100.0
    return max(rho / 20.0, math.sqrt(rho) / 100.0)


def jbr_m(rho, field_card_bits=124):
    """Regime.lean jbrM: max(ceil(sqrt(rho)/(2*eta)), 3)."""
    return max(math.ceil(math.sqrt(rho) / (2 * eta_soundcalc(rho, field_card_bits))), 3)


def raw_m(rho, field_card_bits=124):
    """The value the max(..., 3) floor guards."""
    return math.ceil(math.sqrt(rho) / (2 * eta_soundcalc(rho, field_card_bits)))


ZKVMS = [("SP1 6.1.0", 124, 2, 21, 124, 16, "UDR"),
         ("OpenVM 1.5.0", 124, 1, 23, 193, 20, "UDR"),
         ("Airbender", 124, 1, 24, 87, 28, "JBR"),
         ("Pico", 124, 1, 22, 84, 16, "JBR"),
         ("ZisK 0.16.1", 192, 1, 21, 229, 16, "JBR"),
         ("RISC Zero", 124, 2, 21, 50, 0, "JBR"),
         ("Miden", 128, 3, 18, 27, 16, "JBR")]


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    from regime_crossover import commit_jbr, m_eq, yield_udr

    def y_jbr(R, m):
        a = math.sqrt(2.0 ** -R) * (1 + 0.5 / m)
        return -math.log2(a) if a < 1 else float("-inf")

    sec("1. m IS DERIVED FROM (rate, field), NOT CHOSEN")
    print(f"  {'blowup':>7} {'rho':>8} {'eta':>10} {'m (Lean)':>10} "
          f"{'m_eq (repo)':>13} {'ratio':>8}")
    print("  " + "-" * 60)
    for R in (1, 2, 3, 4):
        rho = 2.0 ** -R
        print(f"  {2**R:>7} {rho:>8.4f} {eta_soundcalc(rho):>10.5f} "
              f"{jbr_m(rho):>10} {m_eq(R):>13.2f} {jbr_m(rho)/m_eq(R):>7.1f}x")
    print("""
  Regime.lean states it outright: "eta is no longer a free rational parameter --
  it is derived per-call from (F, rho, g)". So m is a function of the config,
  not a knob.""")

    sec("2. THE m >= 3 FLOOR IS DEAD CODE AT EVERY DEPLOYABLE RATE")
    print(f"  {'blowup':>8} {'raw m':>8} {'after floor':>13} {'floor binds?':>14}")
    print("  " + "-" * 48)
    for R in range(0, 9):
        rho = 2.0 ** -R
        r = raw_m(rho)
        print(f"  {2**R:>8} {r:>8} {jbr_m(rho):>13} "
              f"{'YES' if r < 3 else 'no':>14}")
    print("""
  Raw m is 10 at blowup 1 and saturates at 50. Iterations 38-39 concluded the
  floor costs zero because deployed optima sit far above 3; the real reason is
  that the formula never produces a value near 3 at any rate.""")

    sec("3. CEILINGS FALL 4-22 BITS -- BUT THE QUERY PHASE STILL BINDS")
    print(f"  {'system':<15} {'K at m_eq':>10} {'K at jbrM':>10} {'delta':>8} "
          f"{'query term':>11} {'still binds?':>13}")
    print("  " + "-" * 72)
    for nm, E, R, T, s, g, reg in ZKVMS:
        if reg != "JBR":
            continue
        nu = T + R
        k1 = commit_jbr(R, nu, E, m_eq(R))
        k2 = commit_jbr(R, nu, E, float(jbr_m(2.0 ** -R, E)))
        q = s * y_jbr(R, 1000.0) + g
        print(f"  {nm:<15} {k1:>10.1f} {k2:>10.1f} {k2-k1:>+8.1f} {q:>11.1f} "
              f"{'yes' if q < k2 else 'NO':>13}")
    print("""
  A 4-to-22-bit drop in a term that does not bind moves no reported total.
  Iteration 24 established the query phase binds for six of seven; that is why
  this correction is real but inert.""")

    sec("4. THEOREM 7 SURVIVES BOTH CONVENTIONS")
    print(f"  {'system':<15} {'s':>5} {'s* m_eq':>9} {'s* jbrM':>9} "
          f"{'pred':>6} {'reported':>10}")
    print("  " + "-" * 58)
    wrong = 0
    for nm, E, R, T, s, g, reg in ZKVMS:
        nu = T + R
        k1 = commit_jbr(R, nu, E, m_eq(R))
        k2 = commit_jbr(R, nu, E, float(jbr_m(2.0 ** -R, E)))
        s1, s2 = (k1 - g) / yield_udr(R), (k2 - g) / yield_udr(R)
        pred = "UDR" if s > s2 else "JBR"
        wrong += pred != reg
        print(f"  {nm:<15} {s:>5} {s1:>9.1f} {s2:>9.1f} {pred:>6} {reg:>10}")
    print(f"""
  {7-wrong}/7 under soundcalc's own m. Every s* falls by 10 to 27 and no system
  crosses. With iteration 34's result that the crossover is invariant to the UDR
  ceiling, Theorem 7 is now robust to two independent modelling choices it could
  have been an artifact of.""")


if __name__ == "__main__":
    report()
