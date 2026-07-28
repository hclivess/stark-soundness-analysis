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

### Corollary 3.1 (practical reading)

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

## Robustness to the `m ≥ m_floor` question

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

## Files

- `verify_theorem.py` — numerical verification of Lemma 2, Prop. 1(a,b,c),
  Thm 2 (closed form vs brute force over `s` and `m`), and Thm 3 (grid argmax
  vs the exact root), plus the corrected ceiling table
