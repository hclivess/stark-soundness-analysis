# Verified configurations — pulled from source, 2026-07-28

Everything here was fetched from the upstream repositories via the GitHub API on
2026-07-28. Quotes are verbatim. This file replaces the "representative defaults
from recollection" caveat that applied to earlier revisions of this repo.

**Summary of what changed:** my recalled RISC Zero parameters were exactly
right. My recalled Stwo and Plonky3 parameters were not *wrong* so much as
**not real** — neither project ships a production FRI config; both take it from
the caller. And the single most consequential discovery is that Plonky3's
soundness crate uses **BCHKS25**, not BCIKS20, whose commit bound is
dramatically better than the one this repo's Part I and Part II were built on.

---

## RISC Zero — `risc0/risc0`

Fully verified. Ships a four-scenario soundness calculator.

### `risc0/zkp/src/lib.rs`

```rust
/// 50 FRI queries are sufficient to achieve our security target of 97 bits (conjectured security)
pub const QUERIES: usize = 50;

/// Inverse of Reed-Solomon Expansion Rate
pub const INV_RATE: usize = 4;

pub const MIN_CYCLES_PO2: usize = 13;
pub const MAX_CYCLES_PO2: usize = 24;
```

### `risc0/zkp/src/prove/soundness.rs`

Module doc:

> Soundness for STARK protocols can be analyzed under a number of different
> cryptographic assumptions.
> 1. Conjectured soundness using the Toy Problem Conjecture from ethSTARK
> 2. Conjectured soundness using Conjecture 8.4 from [Proximity Gaps] and Conjecture 2.3 from [DEEP-FRI]
> 3. Proven soundness in the list-decoding regime
> 4. Proven soundness in the unique-decoding regime
>
> RISC Zero's on-chain verifier contracts target 97 bits of conjectured
> soundness, using the Toy Problem Conjecture.
> This target assumes a SEGMENT_SIZE of 2^20 cycles. Increasing SEGMENT_SIZE to
> the maximum of 2^24 cycles reduces the result to 95 bits.

Constants and the commit-phase term:

```rust
/// Johnson parameter. See https://eprint.iacr.org/2022/1216
const M: f32 = 16.0;
const RHO: f32 = 1.0 / INV_RATE as f32;
/// η in Conjecture 8.4 of the Proximity Gaps paper
const ETA: f32 = 0.05;

/// (m + 1/2)^7 / (3 * sqrt(ρ)^3) * |D|^2 / |K|
fn e_proximity_gap_proven(&self) -> f32 {
    (M + 0.5).powi(7) / (3.0 * RHO.sqrt().powi(3))
        * (self.lde_domain_size.powi(2) / self.ext_field_size)
}

// α = (1 + 1/2m) * sqrt(ρ)
let alpha = (1.0 + 1.0 / (2.0 * M)) * RHO.sqrt();
let theta = 1.0 - alpha;

/// (1 - θ)^QUERIES
fn e_fri_queries(theta: f32) -> f32 { (1.0 - theta).powi(crate::QUERIES as i32) }
```

**This validates this repo's Part I model exactly.** `commit_bits = E + log₂3 −
7log₂(m+½) − 1.5R − 2ν` is `e_proximity_gap_proven` verbatim, and
`α = √ρ(1+1/2m)` matches. `M = 16.0` is also this repo's default.

There is a second, subdominant commit term this repo did not model:

```rust
// (2m + 1) * (|D| + 1) * FRI_FOLD * num_folding_rounds / (sqrt(ρ) * |K|)
```

At RISC Zero's parameters it contributes ≈ 89.6 bits of error against the
`(m+½)⁷` term's ≈ 49.5, so it does not bind. Omitting it was safe.

### Verified RISC Zero parameters

| quantity | value | source |
|---|---|---|
| field | BabyBear `2³¹−2²⁷+1` | `risc0_core::field::baby_bear` |
| extension degree | 4 → `E = 124` | `H::ExtElem::EXT_SIZE` |
| blowup | **4** (`R = 2`) | `INV_RATE = 4` |
| queries | **50** | `QUERIES = 50` |
| grinding | **0** | no PoW term in the FRI query phase |
| trace | **2²⁰** | stated `SEGMENT_SIZE` assumption |
| Johnson `m` | **16** | `const M: f32 = 16.0` |
| target | **97 bits, conjectured** | module doc |

My earlier recalled values (blowup 4, 50 queries, g = 0, trace 2²⁰) were
correct. The one correction: the target is **97** bits, not the 100 I assumed.

---

## Plonky3 — `Plonky3/Plonky3`

Has a dedicated `p3-security` crate, and it is **already post-disproof**.

### `security/src/fri.rs` — module doc

> Conjectured regime: random-words bound, [2025/2010] §1.5.
> Proven regime: round-by-round, [2024/1553] Theorems 2 & 3, with the
> **BCHKS25 LDR commit bound ([2025/2055] Theorem 4.2)**. Cross-checked against
> Ethereum's `soundcalc`.
> - [`proven_error_ldr_m`] / [`best_ldr_m`] is the FRI counterpart of
>   `JohnsonBound`, but searches `m ∈ [3, LDR_M_CAP]` rather than fixing
>   `m = 10` as WHIR does.
> - **`CapacityBound` is not currently supported by FRI's commit-phase analysis.**

That last line is the disproof showing up in shipped code.

### The BCHKS25 commit bound — `commit_phase_error_ldr_m`

> BCHKS25 Theorem 1.5 (Equation (1)):
> `ε_lin = ((2·m'⁵ + 3·m'·γρ)·n / (3·ρ^{3/2}) + m'/√ρ) / |F|`,
> `ε_round = ε_lin · (folding − 1)`

```rust
let num = (2.0 * pow(m_shifted, 5.0) + 3.0 * m_shifted * pp * rho) * n;
let den = 3.0 * rho * sqrt_rho;
let eps_linear = num / den + m_shifted / sqrt_rho;
let eps_powers = eps_linear * folding_minus_one;
let bits_linear = shape.modulus_bits as f64 - log2(eps_powers.max(1.0)) + regime.commit_pow_bits as f64;

let bits_n_over_q = shape.modulus_bits as f64
    - log2(regime.folding_factor()) - log2(n + 1.0) - log2(2.0 * m as f64 + 1.0)
    + 0.5 * log2(rho) + regime.commit_pow_bits as f64;

ErrorBits::from_log2(bits_linear.min(bits_n_over_q).max(0.0))
```

**Exponent 5, not 7. And `n`, not `n²`.** Both improvements over BCIKS20. See
`THEOREM.md` Part III for what this does to Theorems 2, 3′ and 6.

Note they take `min` of the two bit-counts, i.e. the *conservative* of two valid
upper bounds.

### Conjectured regime — the post-disproof replacement

> `b = num_queries · (−log2(ρ + η)) + query_pow`, with `η ≈ (log2(e/ρ) · ρ) / log2(q)`

The old capacity assumption was `−log2(ρ)` per query. The replacement charges
`−log2(ρ + η)`. This is the "modest repricing" the 2026 SoK refers to.

### Proximity parameters — `security/src/proximity.rs`

```rust
pub const LDR_M_CAP: usize = 1000;                          // "Matches Ethereum's soundcalc"

/// LDR agreement parameter α = (1 + 1/(2m))·√ρ. BCHKS25 §4.2.
pub fn alpha_ldr_m(log_blowup: usize, m: usize) -> f64 { (1.0 + 0.5 / m as f64) * sqrt(rho) }

/// LDR list size: L⁺ = (m + 1/2)/√ρ.
/// Largest proximity parameter `m` such that the η > 0 precondition of
/// Theorem 1 in [2021/582] holds.
pub fn compute_upper_m(trace_length: usize) -> usize {
    let ratio = (h + 2.0) / h;
    ceil(1.0 / (2.0 * (sqrt(ratio) - 1.0))) as usize
}
```

`compute_upper_m` has the **identical functional form** to this repo's Lemma 1,
`1/(2(√ratio − 1))`, derived from the same ethSTARK Theorem 1 precondition —
independent confirmation of the `η = √ρ/(2m)` change of variables in
`THEOREM.md`. (Theirs bounds `m` above via `ratio = (h+2)/h`; Lemma 1 bounds it
below via `ratio = 1/ρ`.)

The deployed search range is `m ∈ [3, min(compute_upper_m, 1000)]`, so
**`m_floor = 3`** — the case `THEOREM.md`'s Robustness section anticipated.

### `fri/src/config.rs`

```rust
pub struct FriParameters<M> {
    pub log_blowup: usize,
    pub log_final_poly_len: usize,
    pub max_log_arity: usize,          // 1 = binary folding
    pub num_queries: usize,
    pub commit_proof_of_work_bits: usize,
    pub query_proof_of_work_bits: usize,
    pub mmcs: M,
}

/// Returns the soundness bits of this FRI instance based on the ethSTARK conjecture.
/// Certain users may instead want to look at proven soundness, a more complex
/// calculation which isn't currently supported by this crate.
pub const fn conjectured_soundness_bits(&self) -> usize {
    self.log_blowup * self.num_queries + self.query_proof_of_work_bits
}
```

**There is no production default.** The only constructor with concrete values is
`new_testing` (`log_blowup: 2, num_queries: 2`). Real parameters are
caller-supplied.

---

## Stwo — `starkware-libs/stwo`

### `crates/stwo/src/core/fri.rs` and `core/pcs/mod.rs`

```rust
pub struct FriConfig {
    pub log_blowup_factor: u32,
    pub n_queries: usize,
    // log_last_layer_degree_bound, fold_step
}
const LOG_MIN_BLOWUP_FACTOR: u32 = 1;
const LOG_MAX_BLOWUP_FACTOR: u32 = 16;

pub const fn security_bits(&self) -> u32 { self.log_blowup_factor * self.n_queries as u32 }

pub struct PcsConfig { pub pow_bits: u32, pub fri_config: FriConfig, .. }
pub const fn security_bits(&self) -> u32 { self.pow_bits + self.fri_config.security_bits() }

impl Default for PcsConfig {
    fn default() -> Self {
        Self { pow_bits: 10, fri_config: FriConfig::new(0, 1, 3, 1), min_lifting_log_size: 0 }
    }
}
```

From the repo's own `.claude/skills/zk-stark-foundations.md`:

> | Total security | - | `pcs_config.security_bits()` | = pow_bits + log_blowup_factor * n_queries |
>
> **WARNING**: Default PcsConfig has only ~13 bits of security (test config).

### The notable finding

Stwo's **only** in-repo security accounting is
`pow_bits + log_blowup_factor · n_queries` — the pure capacity/conjectured
formula, which is the assumption disproved in late 2025. There is no
proven-soundness calculator in the repository, and no shipped production
config: `Default` is a 13-bit test configuration carrying an explicit warning.

This is not a claim that Stwo is insecure — deployments supply their own
parameters. It is a claim about what the repository itself can tell you, and
the comparison across the three projects is stark:

| project | conjectured calc | proven calc | post-disproof? | ships prod config |
|---|---|---|---|---|
| **Plonky3** | yes (random-words, 2025/2010) | yes (UDR + BCHKS25 LDR) | **yes** | no |
| **RISC Zero** | yes (Toy Problem + Conj 8.4) | yes (BCIKS20 LDR + UDR) | no (BCIKS20) | yes |
| **Stwo** | yes (capacity only) | **no** | **no** | no (13-bit test default) |

---

## Corrections to earlier revisions of this repo

1. **RISC Zero's target is 97 bits conjectured, not 100.** Everything else I
   recalled for it was exactly right.
2. **"Stwo uses blowup 2, 70 queries, 20 grinding bits" was not a real config.**
   Stwo ships no production config. The same applies to my Plonky3 rows. Those
   rows are now labelled as illustrative parameter points, not as what any
   project runs.
3. **The BCIKS20 `(m+½)⁷·n²` commit bound is superseded by BCHKS25's
   `(2m'⁵+…)·n`.** Part I and Part II of `THEOREM.md` were built on the older
   bound. See Part III.
4. `frontier.py` TERM 2 predicted that the exponent-7 factor was loose and worth
   ~11 bits if reduced. That prediction was correct and **has already been
   realised** — by BCHKS25, in the same paper (2025/2055) that supplied the
   `Ω(n^1.99)` lower bound. The realised gain is larger than predicted, because
   the `n² → n` improvement was not anticipated.

## Fetch method

```bash
gh api -H "Accept: application/vnd.github.raw" repos/OWNER/REPO/contents/PATH
```

eprint.iacr.org PDFs return HTTP 403 to WebFetch; the abstract pages
(`eprint.iacr.org/YYYY/NNN`, no `.pdf`) work.

---

# Round 2 — remaining configs and soundcalc (2026-07-28)

## Plonky2 — `0xPolygonZero/plonky2`

`plonky2/src/plonk/circuit_data.rs`, `standard_recursion_config()`:

```rust
security_bits: 100,
zero_knowledge: false,
fri_config: FriConfig {
    rate_bits: 3,            // blowup 8
    cap_height: 4,
    proof_of_work_bits: 16,
    num_query_rounds: 28,
}
```

**VERIFIED, and my recalled values were exactly right** (R=3, s=28, g=16).
Conjectured: `3·28 + 16 = 100`, matching the declared `security_bits`.

## Winterfell — `facebook/winterfell`

`air/src/options.rs`: `MIN_BLOWUP_FACTOR = 2`, `MAX_BLOWUP_FACTOR = 128`,
`MAX_NUM_QUERIES = 255`, `MAX_GRINDING_FACTOR = 32`. Doc comment:

> conjectured proof soundness is bounded by `num_queries * log2(blowup_factor) + grinding_factor`

Again the capacity formula. `air/src/proof/security.rs` holds the proven-side
computation. No single production preset; `ProofOptions::new` is caller-driven.

## Miden — via `ethereum/soundcalc` `soundcalc/zkvms/miden/miden.toml`

Parameters for Miden's `RECURSIVE_96_BITS`:

```toml
field = "Goldilocks^2"
rho = 0.125                  # blowup 8
trace_length = 262144        # 2^18
num_queries = 27
grinding_query_phase = 16
fri_folding_factors = [4, 4, 4, 4, 4, 4, 4]
air_max_degree = 9
power_batching = true        # algebraic batching
```

**VERIFIED.** My recalled R=3, s=27, g=16 were right. Two corrections: the
field is **Goldilocks², not Goldilocks³** (E = 128, not 192), and the trace is
2¹⁸, not 2²⁰.

## Ethereum soundcalc — `ethereum/soundcalc`

> A universal soundness calculator across hash-based zkEVMs and security regimes

Also `symbolicsoft/soundcalc-lean` — the same, proven in Lean.

### `reports/summary.md` — provable security by regime

| zkVM | Security | Proof system | Field |
|---|---|---|---|
| Airbender | **67** bits (JBR) | DEEP-ALI + FRI | M31⁴ |
| OpenVM 1.5.0 | **100** bits (**UDR**) | DEEP-ALI + FRI | BabyBear⁴ |
| OpenVM2 2.0.0 | 100 bits (mixed) | **SWIRL + WHIR** | BabyBear⁴ |
| Pico | **53** bits (JBR) | DEEP-ALI + FRI | KoalaBear⁴ |
| SP1 6.1.0 | **100** bits (**UDR**) | **Jagged + FRI** | KoalaBear⁴ |
| Venus 0.1.6 / ZisK 0.16.1 | 128 bits (JBR) | DEEP-ALI + FRI | Goldilocks³ |
| zkDTVM 0.8.0 | 128 bits (mixed) | Jagged+FRI / SWIRL+WHIR | KoalaBear⁵ |

Pico (53) and Airbender (67) land inside the ~50–60 band this repo predicted
for 31-bit fields at deployed query counts — independent corroboration.

**The regime column is not constant**, which is what motivated Theorem 7.

### `soundcalc/proxgaps/unique_decoding.py`

```python
def get_proximity_parameter(self, rate, dimension): return (1 - rate) / 2
def get_max_list_size(self, rate, dimension): return 1
def get_error_linear(self, rate, dimension):
    # Using Corollary 1.4 (which points to Theorem 1.3) from BCHKS25
    gamma = (1 - rate) / 2
    n = dimension / rate
    return (gamma * n + 1) / self.field.F
```

**No `(m + ½)` factor and no `ρ^{3/2}`** — this is why the UDR ceiling sits 6–9
bits above JBR's, and why OpenVM and SP1 report 100 provable bits in UDR.

### `soundcalc/proxgaps/johnson_bound.py`

```python
def _get_m_from_eta(sqrt_rate, eta):
    """m := max(⌈√ρ / (2η)⌉, 3) per BCHKS25 Theorem 1.5 / Theorem 4.2.
    The factor of 2 in the denominator is missing from the statement of
    BCHKS25 Theorem 4.2, which is a typo confirmed by the paper authors."""

def _get_eta_from_m(sqrt_rate, m):
    """Inverse: η = √ρ / (2m)."""
```

**`η = √ρ/(2m)` is verbatim the change of variables derived independently in
`THEOREM.md`** ("RESOLVED: the admissible range of m"). Third independent
confirmation, after ethSTARK Thm 1 and Plonky3's `compute_upper_m`.

Also, on the `m ≥ 3` floor:

> We allow m ≥ 1 (not just the m ≥ 3 from Thm 4.2): the lower bound of 3 can be
> relaxed to 1, as noted in the optimization remark right after Lemma 3.1 of BCHKS25.

So `m_floor` is 1, not 3 — partially restoring the range Theorems 3/3′ assumed,
though still not the continuous `m → m_min`.

## NADO — `/root/nado` (local)

| quantity | value | source |
|---|---|---|
| field | Goldilocks `2⁶⁴−2³²+1`, **no extension** | `execnode/stark/field.py:13` |
| FRI blowup | **2** (R = 1) | `execnode/stark/fri.py:41` |
| queries | **320** | `execnode/stark/fri.py:40` |
| grinding | **18** | `execnode/stark/fri.py:42` |
| max trace | **2¹⁷** | `execnode/stark/stark.py:31` |
| fold challenge | base-field element | `fri.py:93`, `transcript.py:28` |
| DEEP point z | `int(z) % F.P` | `deep_eval.py:47` |

Stated target, `fri.py` comment block:

> Sized to clear 128 bits on the PROVABLE (unconditional-modulo-collision-
> resistance) branch — not merely the conjectured branch that most STARK
> deployments settle for:
> `320 queries · 0.4 + 18 grind ≈ 146 bits PROVABLE (Johnson)`

See `nado_audit.py`. The query-phase arithmetic is correct; the calculation has
no commit-phase term, and the commit term binds at ~48 bits because challenges
are drawn from the 64-bit base field.

---

## Fiat–Shamir grinding tightness (iteration 25)

**Alessandro Chiesa and Eylon Yogev, "Building Cryptographic Proofs from Hash
Functions."** Free book; LaTeX source at
`github.com/hash-based-snargs-book/hash-based-snargs-book`, commit `305fa3d`
(2026-03-25). Quoted from `snargs-book.tex`.

Lemma `sp-srs-to-soundness` (line 9159) — **two-sided**:

> If SP has soundness error `eps` then it has state-restoration soundness error
> `eps_SR(salt, n, t) <= (t+1) * eps(n)` … Moreover
> `eps_SR(salt, n, t) >= min{t,2^salt} * eps(n) - C(min{t,2^salt},2) * eps(n)^2`.

Accompanying text (line 9157), verbatim:

> "this upper bound is essentially tight because, in common parameter regimes,
> the SP state restoration soundness error is at least Ω(t) times the SP
> soundness error. We prove this next."

The lower bound is proved by an explicit **"universal state-restoration attack"**
(line 9340): rerun a cheating prover with a fresh salt each time. That is the
nonce-grinding strategy this repo's PQ accounting assumes.

Lemma `fs-for-sigma-protocol-adaptive-soundness` (line 9103) transfers it to
Fiat–Shamir: `eps_ARG <= eps_SR`, and

> "In fact, if `eps_SR` is a tight upper bound then `eps_ARG >= eps_SR`."

On the quantum side the book does **not** give a theorem — post-quantum security
is explicitly out of scope (line 27224, "While not discussed in this book…"), and
it points to `ChiesaMS19` for both the Micali and BCS transformations. It does
state (line 2731):

> "The error bounds typically incur predictable changes due to known speedups of
> quantum algorithms. This is the case for the succinct arguments in this book."

That is consistent with `c = 2` but is not a quantitative statement, so the
QROM loss exponent remains unpinned. See `qrom_bracket.py`.

## BCS soundness composition (iteration 26)

Same source, Theorem `bcs-soundness` (`snargs-book.tex` line 17834), with macros
expanded from lines 1077–1090:

```
eps_ARG(lambda, n, t)  <=  eps_IOP-SR(lambda + salt, n, t)
                         + eps_MT(lambda, proof_lengths, t, t+1)
                         + t^2 / 2^lambda
```

> "Above `eps_MT` is the Merkle commitment multi-extraction error … and the
> additive error `<= 3.5 * t^2 / 2^lambda` if `t >= 2(log l + 1) * l`."

Two consequences: the composition is a **sum**, not a minimum (this repo's
min-model overstates by ≤ `log₂(#terms)`, measured ≤0.34 bits on deployed
configs); and the `t²/2^λ` shape is a **birthday** bound, so the hash family's
classical security is `λ/2` and its quantum security is `λ/3` — BHT's algorithm
above, Zhandry's `Ω(N^{1/3})` below. That is a QROM loss exponent of 3, strictly
worse than the halving that applies to challenge search.

## Merkle multi-extraction error (iteration 27)

Same source, Lemma `mt-multi-configuration-multi-extractability`
(`snargs-book.tex` line 13874), bound at line 13924, macro at line 1020:

```
eps_MT(lambda, lengths, t, n_c)
    <=  (3/2) * t(t-1)/2^lambda              collisions among oracle queries
      + (d_max + 1) * 2 * sum_l / 2^lambda   one pass over every tree node
      + (n_c - 1) * t / 2^lambda             distinct commitments colliding
```

simplifying (line 1031) to `(3/2)t²/2^λ + (n_c−1)t/2^λ` under the condition
(line 1030) `t >= 2(d_max+1)·sum_l`.

BCS instantiates `n_c = t+1` (macro `BCSMTError`, line 1077), so
`eps_MT <= 2.5 t²/2^λ`; adding the hash chain's `t²/2^λ` gives **3.5**, exactly
the constant stated independently at line 1084 (`BCSSimplifiedLeadingConstant`).
Three separately-read macros reproducing a fourth is the check that these terms
were read correctly.

## Interleaved-code proximity (iteration 28)

**Benjamin E. Diamond and Jim Posen, "Proximity Testing with Logarithmic
Randomness."** IACR Communications in Cryptology 1(1), 2024 —
<https://cic.iacr.org/p/1/1/2/pdf>, open access and **not** behind the eprint
Cloudflare challenge. Fetched and read directly.

> **Theorem 1 (Roth–Zémor [AHIV23, § A]).** Fix an arbitrary `[n,k,d]`-code
> `C ⊂ F_q^n`, and a proximity parameter `e ∈ {0, …, (d−1)/3}`. If given elements
> `u_0` and `u_1` of `F_q^n` satisfy
> `Pr_{r ∈ F_q}[d((1−r)·u_0 + r·u_1, C) ≤ e] > (e+1)/q` …

> **Remark 2.** "Theorem 1 is sharp, in the sense that its false witness
> probability `(e+1)/q` cannot be decreased. This fact is demonstrated by the
> following example of Ben-Sasson et al. [BSCI+23, Rem. 1.1]."

> (page 10) "In the Reed–Solomon setting, Ben-Sasson et al. [BSCI+23, Thm. 1.4]
> achieve an analogue of Theorem 1 for `e` as high as the unique decoding
> radius, albeit with an upper bound `n/q` on the false witness probability
> somewhat worse than that of `(e+1)/q` attained by Theorem 1."

> **Conjecture 1.** "We wonder whether Theorem 1 holds even for proximity
> parameters `e ∈ {0, …, (d−1)/2}`."

`e ≤ (d−1)/3` with `d = Θ(n)` makes the numerator `Θ(n)`, so **interleaved codes
carry `a = 1`** — closing the case `ceiling_anatomy.py §5` had held open since
iteration 6. The `n/q` quote also settles that Reed–Solomon's `n`-dependence at
the unique-decoding radius is intrinsic to the **bare proximity gap**, not
imported from the multi-point quotient structure.

## Capacity-radius proximity gaps (iteration 29)

The 2026 arXiv literature, all fetched and read directly (arXiv is not behind
the eprint Cloudflare challenge):

**Jeronimo, Liu, Rajpal, "Optimal Proximity Gap for Folded Reed–Solomon Codes
via Subspace Designs"** — arXiv:2601.10047v1, Theorem 5.12 verbatim:

> Let `C = FRS^m_{n,k}` be an m-folded Reed–Solomon code of block length `n` and
> rate `R := k/(nm)`. Fix `η ∈ (0, 1−R)` and set the target radius
> `δ* := 1 − R − η`. Assume that **`m ≥ c/η²`** and that `q` is at least a fixed
> polynomial in `n` and `1/η`, where `c > 0` is a sufficiently large absolute
> constant. Then there exists an absolute constant `C1 > 0` such that `C` has a
> line proximity gap with parameters `ε ≤ (C1/q)(n/η + 1/η³)`, `κ = 1`.

**Kambiré, "Proximity Gaps Conjecture Fails Near Capacity over Prime Fields"** —
arXiv:2604.09724: gaps fail "at radii that are `O(1/log n)` below the capacity
rate of the code."

**Goyal, Guruswami, Sun, Wootters, "Locality of Curve-Decoding and Improved
Proximity Gaps"** — arXiv:2607.08516 (2026-07-09): extends near-optimal gaps to
random linear codes, random-evaluation-point RS and Gallager LDPC, matching the
subspace-design parameters.

**Yuan, Zhu** — arXiv:2605.07595: syndrome-space route to the same families.

Consequences for this repo: the `n/η` term dominates `1/η³` at every practical
`η`, so **`a = 1` is unchanged at capacity** and the ceiling equation survives
verbatim with `log₂C = log₂(C1/η)` — a penalty, so capacity *lowers* the ceiling.
The `m ≥ c/η²` folding requirement means each query returns `m` field elements,
which cancels the doubled per-query yield.

## The unfolded capacity routes (iteration 30)

**Goyal, Guruswami, Sun, Wootters, "Locality of Curve-Decoding and Improved
Proximity Gaps"** — arXiv:2607.08516v1 (2026-07-09). Fetched and read.

Bounds, both **linear in `n`** (so `a = 1`, independently confirming iteration 29
from a different group and a different code family):

```
(1.1) subspace design / FRS [GG25]:  eps*q >= n*l/eta       + O(l^2/eta^3)
(1.3) this paper, random ensembles:  eps*q >= n*l(1-R)/eta  + O(l^2/eta^3)
```

The field requirements are what close these routes:

> **Theorem 5.3 (random linear codes).** "If `q ≥ exp(Ω(ℓ²/η⁴))` and
> `n ≥ Ω(ℓ⁴/η⁷)`, then with high probability …"

> **Theorem 5.6 (random Reed–Solomon codes).** "If `q ≥ n·exp(Ω(ℓ⁴/η⁷))` and
> `n ≥ Ω(ℓ⁴/η⁷)`, then with high probability …"

against Jeronimo–Liu–Rajpal Thm 5.12 for FRS, where "`q` is at least a fixed
**polynomial** in `n` and `1/η`". So folding buys a polynomial field; removing it
makes the field exponential in `1/η`.

## The two Chai–Fan preprints (iteration 31)

Abstract pages fetched directly (eprint abstract pages serve fine; only PDFs are
behind Cloudflare). Both had been carried in `ceiling_anatomy.py`'s BOUNDS table
from memory, with no entry here.

**eprint 2026/858** — Raullen Chai, Xinxin Fan (IoTeX Network), "FRI Soundness
Above the Johnson Bound via Threshold Halving":

> "For `RS[F, L, k]` … for every `δ ∈ (δ_J, 1−ρ)`:
> `ε_FRI ≤ nR/|F| + (1 − δ/2)^q`."
> "(B) The ~2× query overhead is optimal within the correlated-agreement (CA)
> framework."

**eprint 2026/861** — same authors, "Action–Orbit FRI Soundness Above the Johnson
Radius: A Rigorous `O(1)/|F|` Bound on Plain Reed–Solomon…":

> "the first rigorous `O(1)/|F|` FRI commit-phase soundness bound for plain
> Reed–Solomon above the Johnson radius … The construction is unconditional for
> sparse adversary inputs; for general inputs it reduces to a single
> sparse-worst-case dominance conjecture (Q2)."

Both match the table's `a = 1` (C = rounds) and `a = 0` (conditional) entries —
**the numbers were recorded correctly.** The provenance was not: these are
unreviewed preprints by one group, cited by neither the ABF 2026 survey nor
Goyal–Guruswami–Sun–Wootters (arXiv 2607.08516, 2026-07-09, 37 refs on this exact
topic), and unindexed in OpenAlex. Both signals are weak individually. See
`open_zone.py` for the tier grading and for how much radius is left above Johnson
once Kambiré's counterexamples are accounted for.
