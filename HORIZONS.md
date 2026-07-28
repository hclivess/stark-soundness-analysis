# New horizons — what's replacing univariate FRI (survey, 2026-07-28)

Parts I–IV of `THEOREM.md` mined FRI thoroughly: the regimes, the ceilings, the
crossovers, the post-disproof repricing. This file is about the fact that **the
leading systems are leaving FRI**, and in two different directions that trade
against each other along exactly the axis this repo has been tracking.

---

## The bifurcation

| direction | assumption | what changes | who ships it |
|---|---|---|---|
| **multilinear / sumcheck** | CRHF + ROM (unchanged) | the *arithmetization* and the committed object | SP1 Hypercube, OpenVM2, zkDTVM |
| **lattice** | **M-SIS** (new) | recursion replaced by *accumulation* | LatticeFold+, Greyhound, Grand Danois, Hachi |

Both attack the same bottleneck — **the cost of verifying a proof inside a
circuit** — and that bottleneck is precisely what blocks NADO's ext2 migration.

---

## 1. The multilinear turn (hash-only, so resilience is preserved)

**SP1 Hypercube (mainnet 2026) abandoned AIR+FRI.** It runs sumcheck +
LogUp-GKR with a multilinear **Jagged** polynomial commitment over KoalaBear.
That is the single most significant deployment fact I found this session: the
system Ethereum's own `soundcalc` reports at 100 provable bits (UDR) got there
by leaving the univariate construction behind.

**Jagged Polynomial Commitments** — Hemo, Jue, Rabinovich, Roh, Rothblum,
[eprint 2025/917](https://eprint.iacr.org/2025/917), EUROCRYPT 2026.

The problem: zkVMs commit the trace as many separate table/column polynomials,
and that creates "large overhead in verification costs, especially in hash-based
systems." A jagged matrix is one whose columns have different heights — the
natural shape of a real execution trace.

What it does: commit the **entire trace as a single polynomial**, and let the
verifier *emulate* access to the individual column polynomials, so the
arithmetization proceeds normally.

Costs, from the abstract:
- no additional oracle commitments
- prover dominated by **~5 field multiplications per trace element**
- **verifier is an arithmetic circuit depending only on total trace area**

That last property is the important one. A recursion verifier whose size depends
only on trace *area* — not on column count, table count, or FRI fold geometry —
is what kills the "combinatorial explosion in zkVM recursion."

Related, already mapped in `frontier.py`: WHIR (native multilinear queries),
BaseFold (field-agnostic foldable codes), SWIRL (matrix-stacking over the WHIR
PCS, used by OpenVM2 — an arithmetization layer, not a new low-degree test).

---

## 2. The lattice turn (M-SIS, so resilience is traded away)

**LatticeFold+** — [eprint 2025/247](https://eprint.iacr.org/2025/247), CRYPTO 2025.
Successor to LatticeFold (ASIACRYPT 2025).

- prover **5–10× faster** than LatticeFold
- **simpler verification circuit**, shorter folding proofs
- two new techniques: an algebraic range proof replacing LatticeFold's
  bit-decomposition, and a sumcheck-based transform for folding
  double-commitment statements
- **operates over small (64-bit) fields**

That last line is the one that matters here. Discrete-log folding (Nova,
ProtoStar) needs a ~256-bit field *and* isn't post-quantum. LatticeFold+ is
plausibly post-quantum **and** runs at 64 bits — which is Goldilocks, NADO's
actual field.

And the structural point: **accumulation gives IVC/PCD without recursive
SNARKs.** You never verify a proof inside a circuit; you fold instances.

Companion lattice PCS work: Greyhound (√n verifier), Grand Danois
([2026/1196](https://eprint.iacr.org/2026/1196)), Hachi
([2026/156](https://eprint.iacr.org/2026/156)) — succinct multilinear polynomial
commitments over lattices. Note both lattice and hash camps are converging on
**multilinear** as the committed object.

---

## 3. Why this bears directly on NADO

NADO's blocking problem is not `fri.py`. It is `fri_verify.py` — 458 lines
arithmetizing the FRI fold geometry in-circuit, plus the Rust `sp_fold`. That
subsystem is what gates the GF(p²) migration: moving the folding challenge to
the extension changes the fold arithmetic every recursion AIR must perform.

Both horizons above are escapes from that, and they cost different things:

**(a) Jagged / multilinear — keeps the assumption, restructures the commitment.**
A verifier circuit sized by trace area alone replaces one sized by fold geometry.
The in-circuit FRI verifier stops being the thing you maintain. Stays hash-only,
so the minimal-assumption property this repo keeps defending survives intact.
This is the path SP1 took.

**(b) LatticeFold+ — changes the assumption, deletes recursion.**
Fold instances instead of verifying proofs in-circuit. At 64 bits, so Goldilocks
is already the right field, and NADO's heterogeneous-recursion work for ML-DSA-44
is exactly the workload accumulation is built for. The price is M-SIS: a
structured assumption with a live cryptanalytic literature, in place of
collision-resistance plus the ROM.

That price is the same Pareto trade identified in Part I and never escaped
since: **post-quantum + scaling + resilient does not jointly maximise.** Path (a)
buys scaling and keeps resilience. Path (b) buys more scaling and spends
resilience.

Given NADO's stated posture — sizing for the *provable* branch rather than the
conjectured one, which is a deliberately conservative choice — **(a) is the
consistent direction and (b) is not.** A project that declines the FRI capacity
conjecture on resilience grounds should not then adopt M-SIS to go faster.

---

## 4. What did not pan out

- **Regime M** (post-Johnson MCA, [2026/1432](https://eprint.iacr.org/2026/1432)):
  proven, but the `K⁶/q` commit term needs ~248-bit fields at a 2²⁰ trace. See
  `post_johnson.py`. Unusable by every small-field system.
- **2026/1479** (Chojecki, RS-MCA conjectures and barriers): four adjacent
  conjectures, no deployable bound.
- **arxiv 2607.08516** (locality of curve-decoding): matches Goyal–Guruswami for
  random ensembles; no concrete RS improvement over BCHKS25 extractable from the
  abstract.
- **Jacobian conjecture** (disproved July 2026, `n ≥ 3`): unrelated —
  characteristic 0, and already false in characteristic `p` where all STARK
  arithmetic lives. See `THEOREM.md`.

---

## 5. Open threads worth pulling next

1. ~~**`symbolicsoft/soundcalc-lean`**~~ — **PULLED, iteration 47.** Cloned and
   read: a real formalization (79 theorem/lemma declarations, one `sorry`). It
   settles a modelling question this repo had open — `m` is **derived**, not
   free: `η = max(ρ/20, √ρ/100)` and `m = max(⌈√ρ/(2η)⌉, 3)`, with the source
   stating "η is no longer a free rational parameter". Consequences in
   `soundcalc_lean.py`: the `m ≥ 3` floor is dead code (raw `m` is 10–50), the
   commit ceilings computed at `m_eq` are 4–22 bits optimistic, the reported
   totals are unmoved because the query phase still binds, and **Theorem 7 still
   predicts 7/7** with every `s*` shifted by 10–27.
2. ~~**Jagged's concrete soundness**~~ — **PULLED, iteration 48.** Answered from
   soundcalc-lean's `native_decide`-checked breakdown: **both**. SP1's
   `queryErr` (PCS) and `lookup.errUB` (arithmetization) are *each* exactly 100,
   while every other component sits at 103–116. Neither alone explains the
   figure. Three validations fell out (`sp1_verified.py`): the ceiling equation
   matches the verified round-0 commit term to 0.58 bits; `a = 1` is confirmed
   round-by-round across 21 verified rounds; and `merkle_dedup.py` predicts
   37.4% against a verified 38.1%, understating in the conservative direction.
3. **The quantum column, redone.** `frontier.py`'s Grover adjustment predates
   the UDR/JBR/T regime split. Grinding is still halved, but the *binding term*
   differs per regime, so the post-quantum ranking may reorder. This is directly
   on the stated brief and is the most under-analysed item in the repo.
4. **LatticeFold+ concrete parameters** — M-SIS dimensions and proof sizes at
   64-bit fields, to price path (b) properly rather than qualitatively.

## Sources

- [Jagged Polynomial Commitments, eprint 2025/917](https://eprint.iacr.org/2025/917) (EUROCRYPT 2026)
- [LatticeFold+, eprint 2025/247](https://eprint.iacr.org/2025/247) (CRYPTO 2025)
- [LatticeFold, eprint 2024/257](https://eprint.iacr.org/2024/257) (ASIACRYPT 2025)
- [Grand Danois, eprint 2026/1196](https://eprint.iacr.org/2026/1196)
- [Hachi, eprint 2026/156](https://eprint.iacr.org/2026/156)
- [SoK: Hash-Based Polynomial Commitments and Low-Degree Tests, eprint 2026/1367](https://eprint.iacr.org/2026/1367)
- [Lambdaclass, "Our succinct explanation of jagged polynomial commitments"](https://blog.lambdaclass.com/our-succinct-explanation-of-jagged-polynomial-commitments/)
