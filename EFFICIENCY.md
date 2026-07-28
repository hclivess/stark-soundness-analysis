# Where the cost actually is

`THEOREM.md` and `HORIZONS.md` are about *soundness*. This file is about *cost*,
and it opens with an uncomfortable observation about the rest of the repo.

---

## 0. The reflexive point

Everything in Parts I–IV optimises **bits of security per query**. Query count
governs proof size and verifier work. It has almost **no effect on prover
time** — NADO's own `fri.py` comment states this correctly:

> The prover's dominant cost (the LDE + Merkle tree) is UNCHANGED by query
> count; only the opening set grows.

That is right. So the finding that 247 of NADO's 320 queries buy zero security
is a **proof-size** finding, not a prover finding. Soundness parameters are
close to free on the prover side. If the goal is "better and more efficient
systems," the soundness analysis is necessary — you have to know what you're
allowed to spend — but it is not where efficiency lives.

Efficiency lives in the cost decomposition below.

---

## 1. The decomposition

```
T_total  =  T_witness        trace / witness generation (front end)
          + T_encode         encode the trace into a codeword  (NTT / FFT, or linear code)
          + T_commit         Merkle tree over the codeword     (hashing)
          + T_constraint     check the constraints             (quotient poly, or sumcheck)
          + T_open           query openings                    (~free; scales with s)
```

Measured today, on GPU-accelerated backends:

- **NTT is 90–91% of proof generation latency** ([ZKProphet, arXiv 2509.22684](https://arxiv.org/abs/2509.22684)); paired with optimised MSM, NTT accounts for up to 90% of latency.
  > **Scope correction, iteration 52** (`ntt_share_scope.py`): ZKProphet measures
  > systems "paired with optimized MSM implementations" — pairing/discrete-log
  > provers. **A hash-based STARK has no MSM**; its second dominant kernel is
  > Merkle hashing, which has no counterpart in that measurement. So this
  > citation does not support 90% *for STARKs*. The defensible claim is the
  > **ordering** — `T_encode` and `T_commit` dominate, `T_open` is small — which
  > is all this document's argument uses. Where a specific share is needed, quote
  > the sweep in `ntt_share_scope.py`, not a point estimate.
- **Front-end trace generation is rapidly becoming the bottleneck** ([ZK-Tracer, arXiv 2605.25493](https://arxiv.org/abs/2605.25493)), which states verbatim: *"current hardware acceleration research has exclusively focused on backend proving, [but] we identify that the frontend execution and trace generation phase is rapidly emerging as the new system bottleneck."*
  > **Sourcing correction, iteration 53** (`efficiency_sources.py`): earlier revisions of this line quoted "20–30% of end-to-end time" and *"to over 90%"*. **Neither figure is locatable in the cited paper** — it extracts cleanly at 5,612 words and contains no percent sign at all — and the abstract's own speedups (1829× trace-gen, 963× end-to-end) cannot reconstruct them, being consistent with any front-end fraction from 50% up. The qualitative claim above is verified; the percentages are withdrawn.
- Hashing and MSM are minimal *after* optimisation.

So the honest picture is: **`T_encode` dominates now, and `T_witness` is about
to.** `T_open` — the thing soundness parameters control — is noise.

---

## 2. What each technique actually attacks

| technique | attacks | mechanism | what it costs |
|---|---|---|---|
| **small fields** (M31, BabyBear, KoalaBear, Goldilocks) | *all* terms | machine-word arithmetic, cheaper reduction | soundness — the entire subject of `THEOREM.md`; needs degree-4/5 extensions to claw back |
| **sumcheck instead of quotient polys** (Jolt, SP1 Hypercube, WHIR, SWIRL) | `T_constraint` | linear-time, no polynomial division, no FFT in the constraint check | a different, less mature soundness analysis (mutual correlated agreement — refuted at capacity in 2025) |
| **linear-time codes** (Brakedown, Blaze/RAA, BaseFold) | **`T_encode`** | encode in O(n) instead of O(n log n); Blaze uses no FFT at all | worse rate ⇒ more queries ⇒ larger proofs |
| **binary towers** (Binius) | `T_encode`, `T_witness` | a 1-bit witness value costs 1 bit, not 31 | a different code class and proximity analysis |
| **lookups** (Lasso / Jolt) | `T_witness`, `T_constraint` | replace constraint evaluation with table lookups | table structure must be exploitable |
| **accumulation / folding** (LatticeFold+, Nova) | amortises *everything* | defer the expensive proof; fold instances | M-SIS, if you want it post-quantum |
| **GPU / ASIC** | `T_encode`, `T_commit` | parallel NTT and hashing | capex; and it is what *caused* the front-end to become the bottleneck |
| **jagged commitments** (SP1) | verifier & recursion | one commitment for the whole trace; verifier circuit sized by trace *area* | — |

Two things fall out of this table.

**They compose, mostly.** Small fields × sumcheck × lookups × linear-time codes
attack four different terms. Binius + Justin Thaler's small-field sumcheck was
projected to give Jolt another 5–10× on top of Lasso's own 10–40× over halo2's
lookup argument. Jolt already proves at roughly the speed of a 100 kHz
processor and was ~2× the state of the art at publication.

**Only one of them trades against soundness in the way this repo has been
measuring** — the small-field turn. That is why the small-field penalty keeps
reappearing in every part of `THEOREM.md`: it is the one efficiency lever whose
price is denominated in bits.

---

## 3. The lookup singularity

Jolt ([eprint 2023/1217](https://eprint.iacr.org/2023/1217)) is the most
philosophically different item on the list. The goal — Barry Whitehat's "lookup
singularity" — is circuits that do **nothing but lookups** into predetermined
tables.

Jolt's tables are larger than `2^128`, far too big to materialise, but they are
**structured**: they depend only on the ISA, so the cost never grows linearly in
table size. Instead of arithmetising what an instruction *computes*, you
arithmetise the claim that its (input, output) pair *appears in the ISA's table*.

This is a genuine change of altitude. It doesn't make a proof system faster by
improving a bound; it removes most of the constraint system.

---

## 4. The bottleneck is leaving cryptography

This is the finding I'd flag hardest, because it reframes the whole field.

Backend acceleration has been so successful that **the front end is becoming
dominant**. Trace/witness generation is rising toward dominance (see the
sourcing correction in section 1; the specific percentages are withdrawn).

Witness generation is **not a cryptography problem**. It is emulation,
memory layout, and data movement — closer to a JIT or a database engine than to
a proximity test. The next order of magnitude in zkVM performance looks likely
to come from systems engineering, not from a better low-degree test.

Which means: a project optimising its FRI parameters for prover speed is
optimising a term that is already ~0% of the budget, and will be less.

---

## 5. What this implies for a project like NADO

NADO's constants are `NUM_QUERIES = 320`, `FRI_BLOWUP = 2`, `GRIND_BITS = 18`,
Goldilocks base field, Python prover with Rust hot paths.

- **`FRI_BLOWUP = 2` is the right prover choice** and for the right reason: rate
  1/2 means the LDE is only 2× the trace, so `T_encode` is as small as FRI
  allows. Every other system paying blowup 4–16 is spending 2–8× more NTT.
- **320 queries cost the prover essentially nothing** — the comment is correct.
  They cost proof size and verifier time, and ~247 of them buy no security
  (`soundness.py`).
- **The real prover lever is `T_encode`**: Goldilocks NTT over a 2× LDE. Moving
  to GF(p²) for folding challenges — the soundness fix — raises fold arithmetic
  cost but leaves the layer-0 LDE, the dominant term, untouched. **The soundness
  fix is close to free on the prover.**
- **The real efficiency lever is the front end**, per §4 — a Python-hosted trace
  builder is exactly the term that dominates once the backend is fast.

So the efficiency and soundness recommendations do not conflict here, which is
worth stating plainly: fixing the 47-bit ceiling costs almost nothing in prover
time, and the thing that would actually speed NADO up is unrelated to FRI.

---

## 6. Limits — what cannot be improved

- **Query complexity** of an IOPP for a rate-ρ code has an information-theoretic
  floor near `λ/log(1/ρ)` in the correlated-agreement framework. Beating it
  requires changing the *code* or the *test*, never tuning FRI (`frontier.py`).
- **Commit-phase soundness** is bounded by field size and cannot be bought with
  queries or grinding at any price (`THEOREM.md` Thm 2). This is the one that
  bit NADO.
- **Encoding** is `Ω(n)`; linear-time codes already achieve it, so `T_encode`
  has a constant-factor future, not an asymptotic one.
- **Witness generation** is `Ω(execution length)` — you cannot prove a
  computation without, in some form, running it. This is the floor the field is
  now approaching, and it is not a cryptographic one.

---

## Sources

- [ZKProphet: Understanding Performance of Zero-Knowledge Proofs on GPUs, arXiv 2509.22684](https://arxiv.org/abs/2509.22684) (IEEE IISWC 2025)
- [ZK-Tracer: A High-Performance Heterogeneous Accelerator for zkVM Trace Generation, arXiv 2605.25493](https://arxiv.org/abs/2605.25493)
- [Jolt: SNARKs for Virtual Machines via Lookups, eprint 2023/1217](https://eprint.iacr.org/2023/1217)
- [a16z, "The lookup singularity: Introducing Lasso & Jolt"](https://a16zcrypto.com/posts/article/introducing-lasso-and-jolt/)
- [ZKPOG: Accelerating WitGen-Incorporated End-to-End ZKP on GPU, eprint 2025/765](https://eprint.iacr.org/2025/765)
