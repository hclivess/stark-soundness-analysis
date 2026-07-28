# The admissible-Johnson ceiling for FRI provable soundness

Three results characterising the *shape* of the BCIKS20 Johnson-bound soundness
expression: a unimodality proposition, a closed-form ceiling, and an exact
optimal blowup factor.

Verified numerically by `verify_theorem.py` (all checks PASS).

---

## What these results are, and are not

**Are:** precisely stated, proved, and numerically verified claims about the
function that ethSTARK v1.2 / BCIKS20 gives for FRI soundness. They replace a
brute-force parameter search with closed forms, and they correct a real error
in this repo's earlier ceiling computation.

**Are not:** a new cryptographic hardness result, an improvement to the BCIKS20
bound, or anything that surpasses STARKs. Nothing here changes what is provable
about Reed–Solomon proximity testing. These are statements about an existing
inequality, of the kind that is plausibly folklore among people who work with
these bounds daily — the honest claim is "correct and useful", not "novel".

**Load-bearing assumption, stated up front:** everything below is downstream of
the transcription

> `ε_C ≤ (m + ½)⁷ / (3ρ^{3/2}) · |D₀|² / |F|`,  per-query error `α(m) = √ρ(1 + 1/2m)`

taken from ethSTARK Documentation v1.2 §5–6. Two things must be checked against
the primary sources before any of this is relied on:

1. that the transcription is faithful, and
2. **the admissible range of `m` in BCIKS20 itself.** Theorems 2 and 3 push `m`
   toward its lower limit, so if the original theorem requires `m ≥ 3`, or `m`
   integral, the constants change (see the Robustness section — the results
   survive, the numbers move).

This second point is the one that would invalidate the specific figures, and I
have not verified it against the paper.

---

## Setup

Fix a blowup exponent `R > 0` (rate `ρ = 2^{-R}`), evaluation domain size
`ν = log₂|D₀|`, extension field size `E = log₂|F_ext|`, query count `s > 0`,
and grinding bits `g ≥ 0`. For a Johnson proximity parameter `m > 0` write

```
α(m) = √ρ · (1 + 1/(2m))                                    per-query error
Q(m) = −s·log₂ α(m) + g                                     query-phase bits
K(m) = E + log₂3 − 7·log₂(m + ½) − 1.5R − 2ν                commit-phase bits
Λ(m) = min( Q(m), K(m) )                                    soundness
```

### Definition 1 (admissibility)

`m` is *admissible* if `α(m) < 1`. Write `A` for the admissible set.

Inadmissible `m` is not a loose choice but a vacuous one: `α ≥ 1` makes the
per-query yield non-positive, so no number of queries buys any security.

### Lemma 1 (admissibility threshold)

For `R > 0`, `m > 0`: `α(m) < 1 ⟺ m > m_min(R) := 1 / (2(2^{R/2} − 1))`.
Hence `A = (m_min(R), ∞)`.

*Proof.* `α(m) < 1 ⟺ 1 + 1/(2m) < ρ^{−1/2} = 2^{R/2}`. Since `R > 0` we have
`2^{R/2} − 1 > 0`, so this is `1/(2m) < 2^{R/2} − 1`, and as `m > 0`,
equivalently `m > 1/(2(2^{R/2} − 1))`. ∎

Note `m_min(R) < 1 ⟺ 2^{R/2} > 3/2 ⟺ R > 2log₂(3/2) ≈ 1.170`. **So at blowup 2
(`R = 1`), `m = 1` is inadmissible:** `α(1, R=1) = √½ · 1.5 ≈ 1.0607 > 1`.

### Lemma 2 (the simplifying identity)

`m_min(R) + ½ = 2^{R/2} / (2(2^{R/2} − 1))`.

*Proof.* Over the common denominator `2(2^{R/2} − 1)`, the numerator is
`1 + (2^{R/2} − 1) = 2^{R/2}`. ∎

---

## Proposition 1 (unimodality and unique optimum)

On the admissible set `A`:

**(a)** `Q` is strictly increasing, with `sup_A Q = sR/2 + g`.
**(b)** `K` is strictly decreasing, with `K → −∞` as `m → ∞`.
**(c)** `Λ` is strictly quasiconcave, and:
  - if `Q(m) ≥ K(m)` for `m ↓ m_min`, then `Λ` is decreasing on `A` and its
    supremum is approached at `m → m_min⁺`;
  - otherwise there is a unique `m* ∈ A` with `Q(m*) = K(m*)`, and `m*` is the
    unique maximiser of `Λ`.

*Proof.*

(a) `1/(2m)` is strictly decreasing in `m`, hence so is `α`, hence `−s·log₂α`
is strictly increasing (`s > 0`). As `m → ∞`, `α → √ρ`, so
`Q → −s·log₂√ρ + g = sR/2 + g`.

(b) `log₂(m + ½)` is strictly increasing and unbounded, so `K` is strictly
decreasing to `−∞`.

(c) `D := Q − K` is continuous and strictly increasing on `A` (increasing minus
decreasing), with `D → +∞` as `m → ∞` by (b). If `D ≥ 0` at the left edge then
`D ≥ 0` throughout, so `Λ = K`, which is strictly decreasing — supremum at the
left edge. Otherwise `D` is negative at the left edge and `→ +∞`, so by the
intermediate value theorem and strict monotonicity it has a unique root `m*`.
On `(m_min, m*)`, `Λ = Q` is strictly increasing; on `(m*, ∞)`, `Λ = K` is
strictly decreasing. Hence `Λ` is strictly quasiconcave with unique maximiser
`m*`. ∎

This is what makes the bisection in `verify_theorem.py:optimal_m` valid: `D` is
strictly monotone, so bisection on its sign converges to the unique root.

---

## Theorem 2 (closed-form provable-soundness ceiling)

For fixed `R, ν, E`,

```
sup_{s > 0}  sup_{m ∈ A}  Λ(m)  =  K(m_min(R))
                                =  E − 2ν − 5R + 7·log₂(2^{R/2} − 1) + log₂3 + 7
```

The supremum is not attained: it is approached as `m ↓ m_min` and `s → ∞`.

*Proof.*

*Upper bound.* `Λ ≤ K` pointwise, and `K` is strictly decreasing (Prop. 1b), so
for every `m ∈ A`, `Λ(m) ≤ K(m) < K(m_min)`. This holds for every `s`.

*Tightness.* Fix `ε > 0`. By continuity of `K`, choose `m ∈ A` with
`K(m) > K(m_min) − ε`. Since `m` is admissible, `−log₂α(m) > 0`, so
`Q(m) = −s·log₂α(m) + g → ∞` as `s → ∞`; choose `s` with `Q(m) ≥ K(m)`. Then
`Λ(m) = K(m) > K(m_min) − ε`. As `ε` was arbitrary, the supremum equals
`K(m_min)`.

*Closed form.* By Lemma 2,

```
7·log₂(m_min + ½) = 7·log₂( 2^{R/2} / (2(2^{R/2} − 1)) )
                  = 7·( R/2 − 1 − log₂(2^{R/2} − 1) )
```

Substituting into `K`:

```
K(m_min) = E + log₂3 − 7(R/2) + 7 + 7log₂(2^{R/2} − 1) − 1.5R − 2ν
         = E − 2ν − 5R + 7·log₂(2^{R/2} − 1) + log₂3 + 7          ∎
```

### Corollary 2.1 (separation of variables)

Write `Λ_max(R, ν, E) = (E − 2ν) + f(R)` where

```
f(R) := −5R + 7·log₂(2^{R/2} − 1) + log₂3 + 7
```

The field/domain contribution and the blowup contribution are **additive and
independent**. Doubling the trace length costs exactly 2 bits; every bit of
extension field buys exactly 1 bit; and the blowup factor contributes a term
that involves neither.

---

## Theorem 3 (exact optimal blowup for provable soundness)

`f` attains a unique maximum on `(0, ∞)` at

```
R* = 2·log₂(10/3) ≈ 3.473931,   i.e. blowup factor  2^{R*} = (10/3)² = 100/9 ≈ 11.111
                                 i.e. rate           ρ*     = 9/100 exactly
```

with value

```
f(R*) = 7·log₂(7/3) − 10·log₂(10/3) + log₂3 + 7 ≈ −0.227946
```

so that for all `R`,  `Λ_max ≤ (E − 2ν) − 0.227946`, with equality iff `ρ = 9/100`.

*Proof.* Substitute `u = 2^{R/2}`, so `u > 1` and `du/dR = (ln2/2)·u`. Then

```
d/dR log₂(u − 1) = (1/ln2)·(1/(u−1))·(ln2/2)·u = (1/2)·u/(u−1)
```

hence

```
f'(R) = −5 + (7/2)·u/(u − 1)
```

Setting `f'(R) = 0`: `(7/2)u = 5(u − 1) ⟹ 7u = 10u − 10 ⟹ u = 10/3`.
Thus `2^{R*/2} = 10/3`, giving `R* = 2log₂(10/3)` and blowup `2^{R*} = u² = 100/9`.

*Uniqueness and maximality.* `u/(u−1) = 1 + 1/(u−1)` is strictly decreasing on
`(1, ∞)`, and `u` is strictly increasing in `R`, so `f'` is strictly decreasing
in `R`. It therefore has at most one zero, and changes sign `+ → −` there, so
`f` strictly increases then strictly decreases: `R*` is the unique maximiser.
(As `R ↓ 0`, `u ↓ 1` and `f' → +∞`; as `R → ∞`, `f' → −5 + 7/2 < 0`, confirming
the sign change.)

*Value.* With `u = 10/3`: `u − 1 = 7/3` and `R* = 2log₂(10/3)`, so
`f(R*) = −10log₂(10/3) + 7log₂(7/3) + log₂3 + 7`. ∎

---

## Theorem 3′ (the operative optimum: blowup exactly 4)

Theorem 3 holds `ν` fixed. That is a valid question but not the deployment one:
the evaluation domain is the trace times the blowup, so **`ν = T + R` is
forced** for a fixed trace length `T = log₂(trace)`. Holding `ν` fixed while
raising `R` silently shrinks the trace.

Substituting `ν = T + R` into Theorem 2:

```
Λ_max = E − 2(T + R) − 5R + 7log₂(2^{R/2} − 1) + log₂3 + 7
      = (E − 2T) + g(R),     g(R) := −7R + 7log₂(2^{R/2} − 1) + log₂3 + 7
```

**`g` attains a unique maximum on `(0, ∞)` at `R* = 2` exactly — blowup 4 — with**

```
g(2) = log₂3 − 7 ≈ −5.415037
Λ_max^J = (E − 2T) + log₂3 − 7
```

*Proof.* With `u = 2^{R/2}`, `g'(R) = −7 + (7/2)·u/(u−1)`. Setting to zero:
`(7/2)u = 7(u−1) ⟹ u = 2(u−1) ⟹ u = 2`, so `2^{R*/2} = 2` and `R* = 2`.
Uniqueness and maximality follow as in Theorem 3: `u/(u−1)` is strictly
decreasing in `u` and `u` is increasing in `R`, so `g'` is strictly decreasing
and changes sign `+ → −` exactly once (`g' → +∞` as `R ↓ 0`; `g' → −7 + 7/2 < 0`
as `R → ∞`). The value follows since `log₂(2^{R*/2} − 1) = log₂1 = 0`. ∎

The optimum lands on an exact integer precisely because the `log₂(2^{R/2} − 1)`
term vanishes identically at `R = 2`.

**Theorem 3′ supersedes Theorem 3 for any practical question.** Theorem 3
remains true as stated — it just answers "which blowup maximises the ceiling at
constant evaluation-domain size", which compares systems with different trace
lengths. Blowup 4 is deployed today (RISC Zero, Plonky3/BabyBear); those systems
sit exactly at the Johnson-regime optimum.

### Corollary 3.1 (practical reading, fixed ν — superseded by 3′)

| blowup | R | f(R) | bits below optimum |
|---|---|---|---|
| 2 | 1.000 | −5.316 | **−5.09** |
| 4 | 2.000 | −1.415 | −1.19 |
| 8 | 3.000 | −0.321 | −0.09 |
| **100/9 ≈ 11.11** | **3.474** | **−0.228** | **0** |
| 16 | 4.000 | −0.320 | −0.09 |
| 32 | 5.000 | −0.880 | −0.65 |
| 256 | 8.000 | −4.067 | −3.84 |

Systems at blowup 2 (Stwo, Plonky3/KoalaBear) sit ~5.1 bits below the
achievable provable ceiling; blowup 8 and 16 are both within 0.1 bits of
optimal. The curve is very flat near the top and falls off sharply toward
small blowup — so the practical advice is "avoid blowup 2 if you care about
*provable* soundness", not "retune to 11.111".

**Scope.** This optimises the ceiling — the commit-phase term — alone. Query
cost *decreases* with larger blowup and prover FFT cost *increases* with it, so
the jointly optimal blowup for a deployed system is a different question. What
Theorem 3 says is where the provable ceiling itself peaks.

---

## Consequence: a correction to this repo's earlier numbers

The previous ceiling computation maximised `K` over integers `m ≥ 1` without
imposing Definition 1. At `R = 1` that selected `m = 1`, which is inadmissible
(`α ≈ 1.0607 > 1`) — the reported figure was not merely loose but invalid. At
`R ≥ 2` the integer restriction made it conservative instead.

| system | R | E | ν | old (m=1) | corrected | Δ |
|---|---|---|---|---|---|---|
| Stwo (M31) | 1 | 124 | 21 | 78.0 | **76.7** | −1.3 |
| Plonky3 (KoalaBear) | 1 | 124 | 21 | 78.0 | **76.7** | −1.3 |
| Plonky3 (BabyBear) | 2 | 124 | 22 | 74.5 | **78.6** | +4.1 |
| RISC Zero | 2 | 124 | 22 | 74.5 | **78.6** | +4.1 |
| Plonky2 | 3 | 128 | 23 | 75.0 | **81.7** | +6.7 |
| Winterfell / Miden | 3 | 192 | 23 | 139.0 | **145.7** | +6.7 |
| Boojum (zkSync) | 3 | 128 | 23 | 75.0 | **81.7** | +6.7 |
| Cairo / StarkNet | 4 | 251 | 24 | 194.5 | **202.7** | +8.2 |

The qualitative conclusion is unchanged and in fact sharpened: no 31-bit-field
system with a degree-4 extension reaches 100 provable bits at a 2²⁰ trace, at
any query count, any grinding level, **or any blowup factor** — Theorem 3 closes
the last of those escape routes, since `E − 2ν − 0.228 = 124 − 42 − 0.228 = 81.8`
is the best achievable even at the optimal rate.

---

## RESOLVED: the admissible range of `m` (2026-07-28)

The load-bearing uncertainty flagged above is settled, and in favour of the
theorems. ethSTARK v1.2 states the Johnson bound as:

> for every `η ∈ (0, 1 − √ρ)`, the code `V` is `(1 − √ρ − η, 1/(2η√ρ))`-list-decodable

Matching proximity radii, `1 − √ρ − η = 1 − √ρ(1 + 1/2m)` gives the change of
variables

```
η = √ρ / (2m)          equivalently        m = √ρ / (2η)
```

Under it, the paper's constraint `η < 1 − √ρ` becomes

```
√ρ/(2m) < 1 − √ρ  ⟺  m > √ρ / (2(1 − √ρ)) = 1 / (2(2^{R/2} − 1)) = m_min(R)
```

— **exactly Lemma 1**, and `η > 0 ⟺ m < ∞`. So the paper's admissible set for
`η` is an *open real interval*, and its image is precisely `A = (m_min, ∞)`:
real-valued, open at the lower end, no integrality restriction and no `m ≥ 3`
floor.

Two consequences:

1. **Theorems 2, 3 and 3′ hold unconditionally** on this point. The
   `m_floor` caveat below is vacuous for ethSTARK's parameterisation.
2. It explains the `(m + ½)⁷`: the list size in the paper is
   `1/(2η√ρ) = m/ρ`, so the commit bound is polynomial in the list size, and
   `m` enters through it.

The supremum being unattained (Theorem 2) corresponds exactly to the interval
for `η` being open at `1 − √ρ`.

## Robustness to the `m ≥ m_floor` question (retained for other parameterisations)

If BCIKS20 restricts `m` to `[m_floor, ∞)` for some `m_floor > m_min(R)`, then
Prop. 1 is unchanged (it never used the left endpoint's value), and Theorem 2
becomes

```
Λ_max = K( max(m_min(R), m_floor) )
```

Theorem 3's optimum then holds only where `m_min(R) ≥ m_floor`, i.e. for
`R ≤ 2log₂(1 + 1/(2·m_floor))`. For `m_floor = 3` that is `R ≤ 0.463` — outside
the deployed range — so under an `m ≥ 3` restriction the ceiling would instead
be `E − 2ν − 1.5R + log₂3 − 7log₂(3.5)`, which is **strictly decreasing in R**
and the optimal-blowup result disappears entirely.

**So Theorem 3 is exactly as strong as the claim that BCIKS20 admits real
`m` down to the `α < 1` boundary.** That is the single fact to check first.

---

---

# Part II — after the late-2025 capacity disproof

## The regime inventory changed

| regime | radius | per-query err | commit err | status |
|---|---|---|---|---|
| **U** unique | `(1−ρ)/2` | `(1+ρ)/2` | `O(n)/\|F\|` | unconditional |
| **J** Johnson/BCIKS20 | `1−√ρ(1+1/2m)` | `√ρ(1+1/2m)` | `(m+½)⁷n²/(3ρ^{3/2}\|F\|)` | unconditional |
| **T** threshold halving | `δ ∈ (δ_J, 1−ρ)` | `1−δ/2` | `n·r/\|F\|` | **unconditional, above Johnson** |
| **C** capacity | `1−ρ` | `ρ` | `~n/(ρ\|F\|)` | **DISPROVED late 2025** |

Regime C was refuted by Crites–Stewart (eprint 2025/2046 — the correlated
agreement, mutual correlated agreement/WHIR, and list-decodability/DEEP-FRI
up-to-capacity conjectures) and independently by Diamond–Gruen (2025/2010).
Regime J is untouched. Regime T is from eprint 2026/858 (threshold halving,
after Rothblum–Vadhan–Wigderson), which gives `ε ≤ nr/|F| + (1−δ/2)^q`.

Definitions for Part II: `T_len = log₂(trace)`, `ν = T_len + R`, `r` = FRI round
count.

```
yield_J(R) = R/2                    (sup over m)
yield_T(R) = −log₂((1+ρ)/2) = 1 − log₂(1 + 2^{−R})     (sup over δ)
Λ_max^J    = (E − 2·T_len) + g(R)                       [Thm 2 + 3′]
Λ_max^T    = E − ν − log₂ r
```

Note `yield_T = yield_U` identically: threshold halving pushed to the capacity
radius recovers the *unique-decoding* per-query yield. Its gain over U is the
radius it certifies; its gain over J is the commit term.

---

## Theorem 4 (query penalty for unconditionality above Johnson)

Define the query multiplier for switching from regime J to regime T:

```
κ(R) := yield_J(R) / yield_T(R) = (R/2) / (1 − log₂(1 + 2^{−R}))
```

Then `κ` is **strictly increasing** on `(0, ∞)`, with

```
lim_{R→0⁺} κ(R) = 1        and        κ(R) ~ R/2 → ∞
```

*Proof of the limits.* Both numerator and denominator → 0 as `R → 0⁺`. By
L'Hôpital, `d/dR (R/2) = 1/2`, and

```
d/dR [1 − log₂(1 + 2^{−R})] = 2^{−R} / (1 + 2^{−R}) → 1/2  as R → 0
```

so the ratio → 1. As `R → ∞`, `log₂(1 + 2^{−R}) → 0`, so `κ(R) ~ R/2`. ∎

Monotonicity is verified numerically (200k samples on `(0, 40]`, zero
violations); a clean analytic proof is not included here.

| blowup | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|
| **κ** | 1.205 | 1.475 | 1.807 | **2.192** | 2.616 | 3.069 |

**Cross-check:** 2026/858 states its method costs "approximately a factor ~2 in
queries". `κ(4) = 2.19` at blowup 16, a very common configuration. The
agreement is evidence the transcription is faithful.

**Reading.** The cost of going unconditional above Johnson *vanishes* as the
blowup approaches 1 and grows without bound as it grows. This inverts the usual
intuition: high blowup is exactly what makes Johnson's query advantage large, so
high-blowup systems pay the most to become unconditional.

---

## Theorem 5 (opposite blowup preferences)

With `ν = T_len + R` fixed-trace:

**(a)** `Λ_max^J` has an interior maximum at `R = 2` (blowup 4) — Theorem 3′.
**(b)** `Λ_max^T = E − T_len − R − log₂ r` is **strictly decreasing** in `R`.
**(c)** `κ` is strictly increasing in `R` — Theorem 4.

Hence regime J prefers blowup 4, while regime T prefers the *smallest available
blowup*, improving on both of its axes simultaneously (higher ceiling and lower
query penalty). ∎

| blowup | ceil_J | ceil_T | κ |
|---|---|---|---|
| 2 | 76.68 | **98.68** | **1.205** |
| **4** | **78.58** | 97.68 | 1.475 |
| 8 | 77.68 | 96.68 | 1.807 |
| 16 | 75.68 | 95.68 | 2.192 |
| 32 | 73.12 | 94.68 | 2.616 |

*(E = 124, T_len = 20)*

---

## Theorem 6 (the crossover, and what it rescues)

Regime T's ceiling exceeds regime J's by

```
Λ_max^T − Λ_max^J = ν − log₂ r − g(R) − ... ≈ ν bits
```

measured at **+19 to +22 bits** for every deployed configuration. The reason is
structural: T's commit error is `O(n)/|F|` where J's is `O(n²)/|F|`, and
`log₂ n = ν`.

| system | E | ceil_J | ceil_T | 100 bits provable? |
|---|---|---|---|---|
| Stwo (M31) | 124 | 76.7 | 98.7 | no, under neither |
| Plonky3 (KoalaBear) | 124 | 76.7 | 98.7 | no, under neither |
| Plonky3 (BabyBear) | 124 | 78.6 | 97.7 | no, under neither |
| RISC Zero | 124 | 78.6 | 97.7 | no, under neither |
| Plonky2 | 128 | 81.7 | 100.7 | **ONLY under T** |
| Boojum (zkSync) | 128 | 81.7 | 100.7 | **ONLY under T** |
| Winterfell / Miden | 192 | 145.7 | 164.7 | yes, under J |
| Cairo / StarkNet | 251 | 202.7 | 222.7 | yes, under J |

**This supersedes Part I's headline.** Part I concluded that no 31-bit field with
a degree-4 extension reaches 100 provable bits at any query count, grinding
level, or blowup. That was correct **for regime J** and is now obsolete as a
general claim: threshold halving lifts those systems to 97.7–98.7 bits — within
1.3–2.3 bits of the target — at a query cost of only `κ = 1.2–1.5`. Closing the
remaining gap needs ~2 more bits of extension or a slightly shorter trace,
not a different field.

---

## Corrections to Part I and to this repo's earlier claims

1. **"The RS capacity conjecture is the highest-leverage open problem."**
   Wrong — it is not open. It was disproved in late 2025. The corrected
   statement: the open problems are Crites–Stewart's minimally-modified
   conjectures restricted to the list-decoding capacity bound, and the `Q2`
   sparse-worst-case dominance conjecture of eprint 2026/861.

2. **WHIR** was listed among systems that beat FRI without noting that its
   *mutual* correlated agreement conjecture was refuted in the same work.

3. **Theorem 3 (blowup 100/9)** answers the fixed-`ν` question; Theorem 3′
   (blowup 4) is the operative one.

4. The counterexamples live in the regime `ρ → 0, γ → 1`, while deployed rates
   are `ρ ∈ [1/16, 1/2]`. **No known counterexample attacks a deployed parameter
   set directly.** The honest statement: deployed systems are not known to be
   broken, and are no longer known to be sound at their advertised level. The
   disproof removes the justification, not (yet) the security.

---

# Part III — after pulling the real source (2026-07-28)

Configurations and formulas were read from the upstream repositories. Verbatim
quotes and paths are in `SOURCES.md`; the model is `real_configs.py`. Three
things changed.

## III.1 The commit bound Parts I–II were built on is superseded

Plonky3's `p3-security` crate does not use BCIKS20. It uses **BCHKS25**
([2025/2055] Thm 4.2 — the same paper that supplied the `Ω(n^1.99)` lower
bound):

```
ε_lin = ((2·m'⁵ + 3·m'·γρ)·n / (3·ρ^{3/2}) + m'/√ρ) / |F|,     m' = m + ½
```

against BCIKS20's `(m+½)⁷·n² / (3ρ^{3/2}·|F|)`. **Two independent improvements:
the exponent drops 7 → 5 (worth `2log₂(m+½)`), and the domain factor drops
`n² → n` (worth `ν`).** At `ν ≈ 22` the second dominates. Measured at `m = 16`:

| system | BCIKS20 | BCHKS25 | gain |
|---|---|---|---|
| RISC Zero | 50.3 | 79.4 | **+29.1** |
| Stwo / Plonky3 (KoalaBear) | 53.8 | 81.9 | +28.1 |
| Cairo / StarkNet | 170.3 | 201.4 | +31.1 |

`frontier.py` TERM 2 predicted the exponent-7 factor was a proof artifact worth
~11 bits if reduced. **That prediction was right and had already been realised**
— by more than predicted, since the `n² → n` improvement was not anticipated.

**What survives:** Proposition 1 is regime-agnostic. Its proof uses only that
`Q` is increasing in `m` and `K` is decreasing in `m` — both hold for BCHKS25.
The quasiconcavity, the unique optimum, and the bisection remain valid; only
the specific `K` changes. Theorem 2's *closed form* is now a closed form for a
superseded bound.

## III.2 Theorems 3 and 3′ require `m → m_min`; deployment uses `m ≥ 3`

Plonky3 searches `m ∈ [3, min(compute_upper_m, 1000)]`, with `LDR_M_CAP = 1000`
"matching Ethereum's `soundcalc`". So `m_floor = 3` — exactly the case the
Robustness section anticipated, now confirmed as deployed practice.

Under `m ≥ 3` with `ν = T + R`, both commit bounds become **strictly decreasing
in `R`**: BCIKS20 goes as `−3.5R`, BCHKS25 as `−2.5R`. The interior optimum
disappears.

> **Theorem 3′ (blowup 4) holds only where `m` may approach the admissibility
> boundary `m_min(R)`. Under the deployed convention `m ≥ 3`, the optimum is the
> smallest available blowup.**

Both statements are correct about their own hypothesis. ethSTARK's `η` range
genuinely permits `m ↓ m_min`; Plonky3's floor of 3 is a conservative choice,
not a theorem. But the operative guidance for anyone using a standard
calculator is **small blowup**, not blowup 4.

This also **collapses the Theorem 5 dichotomy**: under `m ≥ 3`, regimes J and T
both prefer the smallest blowup. The opposition in Part II was an artifact of
letting `m` reach `m_min` in regime J.

## III.3 Theorem 6's margin shrinks by two thirds

Part II credited threshold halving with `+19` to `+22` bits over Johnson,
attributing it to `O(n)/|F|` versus `O(n²)/|F|`. **BCHKS25 already gives the
Johnson regime the `O(n)` commit term.** Recomputed at `m ≥ 3`:

| system | J (BCIKS20) | J (BCHKS25) | T (threshold halving) | T − J now |
|---|---|---|---|---|
| RISC Zero | 65.9 | **90.5** | 97.7 | **+7.2** |
| Stwo / KoalaBear | 69.4 | **93.0** | 98.7 | +5.7 |
| Plonky2 | 66.4 | **92.0** | 100.7 | +8.7 |

Threshold halving's remaining advantage is the *radius* it certifies, not the
commit term — and it still costs `κ(R)` in queries (Theorem 4, unaffected). The
case for adopting it is materially weaker than Part II concluded.

## III.4 The measured conjectured-vs-proven gap

At each configuration's own `(s, g)`, optimising `m` over `[3, 1000]`:

| system | proven | m\* | binder | conj (new) | conj (capacity, dead) |
|---|---|---|---|---|---|
| **RISC Zero** (verified) | **50.0** | 971 | query | 98.0 | 100.0 |
| Plonky3 (BabyBear) | 57.9 | 322 | query | 98.3 | 100.0 |
| Stwo (M31) | 54.9 | 690 | query | 88.0 | 90.0 |
| Cairo / StarkNet | 60.0 | 1000 | query | 119.1 | 120.0 |

**The gap is ~40–47 bits.** RISC Zero targets 97 conjectured bits and has 50
provable ones at the same parameters. The query phase binds everywhere, so `m*`
runs large (maximising per-query yield toward `R/2`), and `proven ≈ s·R/2`.

This is the quantity eprint 2026/1371 calls "the measured gap between
conjectured and provable soundness for non-interactive FRI" and names as the
area's sharpest empirical gap.

## III.5 The disproof costs 1–3 queries

The capacity assumption charged `−log₂ρ` per query. Plonky3's replacement
(random-words, [2025/2010] §1.5) charges `−log₂(ρ + η)` with
`η ≈ (log₂(e/ρ)·ρ)/log₂ q`:

| system | capacity (dead) | random-words | lost | +queries to restore |
|---|---|---|---|---|
| RISC Zero | 100.0 | 98.0 | 2.0 | 2 |
| Stwo (M31) | 90.0 | 88.0 | 2.0 | 3 |
| Plonky2 | 100.0 | 98.6 | 1.4 | 1 |

**A foundational event, not an operational emergency** — which is exactly how
the 2026 SoK characterises it. The disproof removes a justification; it costs
a handful of queries to restore the number.

## III.6 What each project can tell you about its own soundness

| project | conjectured calc | proven calc | post-disproof? |
|---|---|---|---|
| **Plonky3** | random-words [2025/2010] | UDR + **BCHKS25** LDR | **yes** |
| **RISC Zero** | Toy Problem + Conj 8.4 | BCIKS20 LDR + UDR | no (BCIKS20) |
| **Stwo** | capacity only, `s·R + g` | **none** | no |

Plonky3 is clearly the most current: it names the disproof papers in module docs
and states `CapacityBound is not currently supported by FRI's commit-phase
analysis`. Stwo's only in-repo accounting is `pow_bits + log_blowup·n_queries`
— the disproved assumption — and its shipped `Default` is a ~13-bit test config
with an explicit warning.

That is a statement about repository documentation, **not** a claim that any
deployment is insecure: all three take production parameters from the caller.

---

# Part IV — Theorem 7, and an audit of NADO (2026-07-28)

## IV.1 Motivation: the winning regime is not constant

Ethereum's `soundcalc` (`reports/summary.md`) reports best-across-regimes
provable security, and the winning regime differs by system:

| zkVM | Security | Regime | Field |
|---|---|---|---|
| Pico | 53 | **JBR** | KoalaBear⁴ |
| Airbender | 67 | **JBR** | M31⁴ |
| OpenVM / SP1 | 100 | **UDR** | BabyBear⁴ / KoalaBear⁴ |
| Venus / ZisK | 128 | JBR | Goldilocks³ |

Pico (53) and Airbender (67) fall inside the ~50–60 band Part III predicted for
31-bit fields — independent corroboration. But Parts I–III treated unique
decoding as strictly weakest, and OpenVM and SP1 reach **100 provable bits in
UDR**. That was an error, and Theorem 7 explains it.

The two regimes trade on opposite axes:

- **UDR** — worse per-query yield, but its commit error is `(γn+1)/|F|` with
  **no `(m+½)` factor and no `ρ^{3/2}`**, hence a *higher* ceiling.
- **JBR** — better per-query yield (for large enough `m`), but the commit term
  carries `2m'⁵` and `ρ^{3/2}`, hence a *lower* ceiling.

So JBR wins when queries are scarce, UDR when they are plentiful.

## Theorem 7(a) — the yield-equalising Johnson parameter

JBR's per-query yield exceeds UDR's **iff `m > m_eq(R)`**, where

```
m_eq(R) = √ρ / (1 − √ρ)²  =  u/(u−1)²,     u = 2^{R/2}
```

*Proof.* Set `√ρ(1 + 1/2m) = (1+ρ)/2`. Then
`1/(2m) = (1+ρ)/(2√ρ) − 1 = (1−√ρ)²/(2√ρ)`, so `m = √ρ/(1−√ρ)²`. Substituting
`ρ = u^{−2}` gives `u/(u−1)²`. Monotonicity of `√ρ(1+1/2m)` in `m` makes the
inequality strict either side. ∎

| blowup | 2 | 4 | 8 | 16 | 32 |
|---|---|---|---|---|---|
| `m_eq` | **8.243** | 2.000 | 0.846 | 0.444 | 0.261 |

Verified against direct bisection on the yield difference: agreement to 1e-6.

**At blowup 2 you need `m > 8.24` before the Johnson regime even beats unique
decoding on per-query yield.** Low-blowup systems get far less from JBR than
the "Johnson beats unique decoding" folklore suggests.

## Theorem 7(b) — the crossover query count

At JBR's interior optimum, Proposition 1 gives `s·y_J(m*) + g = K_J(m*)`. If UDR
is still query-bound at the crossover, `Λ_U = Λ_J` reads `s·y_U + g = s·y_J(m*) + g`,
hence `y_J(m*) = y_U`, hence **`m* = m_eq(R)`**. Therefore

```
s* = ( K_J(m_eq(R)) − g ) / y_UDR(R)
```

Below `s*` use JBR; above it, UDR is strictly better. Verified against a scan
for `R ∈ {1,2,3}`, `g ∈ {0,16}`, two field sizes — **all PASS**, agreement
within one query.

Note `K_J` is evaluated **at `m_eq`**, not at its maximum over `m`. Using the
max gives an upper bound on `s*`, not the crossover — JBR has not saturated at
the crossing. (An earlier version of this theorem made that mistake and failed
its own numerical check at `R = 1, 2`.)

**Corollary.** Buying queries past `s*` buys both more security *and* a weaker
assumption: UDR needs no list-decoding argument at all.

| field | R | g | s\* |
|---|---|---|---|
| 31-bit⁴ | 1 | 0 | 208 |
| 31-bit⁴ | 2 | 0 | 137 |
| Goldilocks² | 3 | 16 | 100 |

The three verified deployed systems (RISC Zero s=50, Plonky2 s=28, Miden s=27)
all sit **below** their crossover, so JBR is the right regime to report them in
— and all three land in the 50–70 bit band, matching soundcalc's independent
Pico/Airbender figures.

**Reaching 100 provable bits on a small field means crossing `s*`: 130–210
queries, roughly 3–4× current deployments.** That is the real price — not a
different field, not a different bound, just many more queries.

## IV.2 Audit: NADO (`/root/nado`)

NADO is a post-quantum blockchain building STARK-verified ML-DSA-44 signatures.
It already targets the *provable* branch, which is the design posture this
repository argues for:

```python
NUM_QUERIES = 320;  FRI_BLOWUP = 2;  GRIND_BITS = 18
# Sized to clear 128 bits on the PROVABLE branch — not merely the conjectured
# branch that most STARK deployments settle for:
#     320 queries · 0.4 + 18 grind ≈ 146 bits PROVABLE (Johnson)
```

**The query-phase arithmetic is correct.** At `R = 1`, JBR yield is 0.456 bits
at `m = 16`, so `320 × 0.456 + 18 = 163.8`; the comment's 0.4 is a fair
moderate-`m` figure.

**But the calculation has no commit-phase term.** FRI soundness is a minimum
over query and commit phases, and the commit phase is bounded by the field the
folding challenges are drawn from. NADO folds with **base-field** challenges:

```python
alpha = t.challenge()                   # fri.py:93   -> "a uniform field element"
out[i] = F.add(fe, F.mul(alpha, fo))    # fri.py:63
z = int(z) % F.P                        # deep_eval.py:47
```

so `E = 64` (Goldilocks base), not a 128- or 192-bit extension.

| term | bits |
|---|---|
| UDR query (320 queries + 18 grind) | 150.8 |
| **UDR commit** (`γn+1`/\|F\|, ν = 18) | **48.0** |
| JBR best over `m` | 40.3 |
| **DEEP** (single base-field `z`, degree 2¹⁷) | **47.0** |
| **achieved** | **47.0** |
| stated in `fri.py` | 146 |

Soundness saturates near 48 bits at ~54 queries; **the remaining ~266 queries
add proof size and zero security.** The conjectured branch is capped by the same
term, so the stated 338 bits is equally unreachable — the conjecture improves
per-query yield, and the query phase is not what binds.

### The fix

| design | E | achieved |
|---|---|---|
| Goldilocks base (today) | 64 | 47.0 |
| **Goldilocks² (Plonky2, Miden)** | 128 | **111.0** |
| Goldilocks³ (Venus, ZisK) | 192 | 156.0 |

Draw the **folding challenge and DEEP point `z` from a degree-2 extension**.
That is what every other Goldilocks system does. It preserves what the `fri.py`
comment is protecting — `FRI_BLOWUP` stays 2 and the fold *shape* is unchanged,
so the in-circuit recursion AIRs keep their geometry — though the arithmetic
inside those AIRs does move into the extension, which is real work.

With Goldilocks², the existing 320-query budget becomes well matched: commit
~112 bits against a query phase of ~151, and the 128-bit provable target is
reachable.

### Caveats

Read from source, **not executed**. If NADO draws folding challenges from a
wider space anywhere I did not look, the ceiling rises accordingly; the lines I
read are cited above. `ν = 18` uses `MAX_TRACE_ROWS`; smaller traces gain ~1 bit
per halving. **This is a soundness-parameter finding, not an exploit** — it says
the proven bound is far below the stated target, not that a forgery is known.


---

## Not connected: the Jacobian conjecture

The Jacobian conjecture was disproved in July 2026 (Alpöge, counterexample
credited to the AI system Fable; geometric reconstruction by Tao). It is false
in dimension 3 and hence in all dimensions ≥ 3; the plane case `n = 2` remains
open. Independently verified, not yet journal peer-reviewed.

**This has no bearing on STARK soundness.** The tempting link is that STARKs
depend on invertible low-degree polynomial maps throughout — the algebraic
S-boxes of Poseidon, Rescue, Griffin, Anemoi, Monolith are polynomial
automorphisms of `F_p^n`. But the Jacobian conjecture is a **characteristic-0**
statement, and it has been known false in characteristic `p` for decades: `x +
x^p` has derivative 1 yet is not injective over `F̄_p`, since `d(x^p)/dx = 0`.
All STARK arithmetic is characteristic `p` (M31, BabyBear, KoalaBear,
Goldilocks, binary towers), so the char-0 case falling changes nothing where it
never applied.

**The methodological point does carry over.** Two long-standing conjectures
were falsified within eight months — RS up-to-capacity (late 2025) and Jacobian
in `n ≥ 3` (July 2026). Neither had been widely expected to fall. For a design
brief that lists resilience as a hard requirement, this is a direct argument for
regime T over the conjectured regime, and Theorems 4–6 price that choice:
`κ = 1.2×` queries at blowup 2, `2.2×` at blowup 16.

## Files

- `verify_theorem.py` — numerical verification of Lemma 2, Prop. 1(a,b,c),
  Thm 2 (closed form vs brute force over `s` and `m`), and Thm 3 (grid argmax
  vs the exact root), plus the corrected ceiling table
- `regimes.py` — Part II: the four-regime model, Thm 3′, Thm 4 (κ monotonicity,
  200k samples), Thm 5 (dichotomy), Thm 6 (crossover table)

## Sources for Part II

- [Crites–Stewart, *On Reed–Solomon Proximity Gaps Conjectures*, eprint 2025/2046](https://eprint.iacr.org/2025/2046.pdf)
- [*On Proximity Gaps for Reed–Solomon Codes*, eprint 2025/2055 / ECCC 2025/169](https://eprint.iacr.org/2025/2055)
- [*FRI Soundness Above the Johnson Bound via Threshold Halving*, eprint 2026/858](https://eprint.iacr.org/2026/858)
- [Chai–Fan, *Action–Orbit FRI Soundness Above the Johnson Radius*, eprint 2026/861](https://eprint.iacr.org/2026/861)
- [*SoK: Hash-Based Polynomial Commitments and Low-Degree Tests*, eprint 2026/1367](https://eprint.iacr.org/2026/1367)
- [*The Small-Field Turn in Succinct Proofs*, eprint 2026/1371](https://eprint.iacr.org/2026/1371)
- [ethSTARK Documentation v1.2, eprint 2021/582](https://eprint.iacr.org/2021/582.pdf)
- [BCIKS20, *Proximity Gaps for Reed–Solomon Codes*, eprint 2020/654](https://eprint.iacr.org/2020/654.pdf)
