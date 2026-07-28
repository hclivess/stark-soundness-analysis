# The provable-soundness ceiling of hash-based proof systems

Everything in this repository reduces to one equation and one classification.

```
ceiling = E − a·ν − log₂C + g_commit
```

`E` = log₂ of the challenge field, `ν` = log₂ of the evaluation domain, `a` = the
exponent on the domain size in the commit-phase error, `C` = the bound's constant
factor, `g_commit` = commit-phase proof-of-work.

| layer | exponent `a` | numerator |
|---|---|---|
| sumcheck / zerocheck / RLC / Jagged | **0** | `O(log n)` or `O(constraints)` |
| code proximity (FRI, WHIR, Ligero/Brakedown) | **≥ 1** | `O(n^a)` |

The whole formula is reproduced **exactly** on published data. UDR has no
proximity parameter, so its constant is fixed outright at `log₂C = −2`, leaving
every term read from each system's own config with nothing fitted:
Pico `124 − 23 + 2 + 0 = 103` (reported 103), Airbender
`124 − 25 + 2 + 5 = 106` (reported 106). Their +3 gap decomposes as
−2 (domain, `a=1`) + 5 (Airbender's declared commit grinding).

`a` is separately observable: soundcalc publishes per-round commit values, and
each fold drops `ν` by `log₂(folding factor)`, so the step between rounds *is*
`a·log₂(f)`. Measured across four systems with four different schedules —
Pico and OpenVM (fold 2, step 1), Miden (fold 4, step 2), Airbender
(mixed `[16,16,16,8,8]`, steps `{4,3}`) — it reads exactly **1**, with no
fitting. `a = 2` would double every step.

Total soundness is a **minimum** over all terms, so **the code layer always
binds**. That single fact explains the rest of this repo.

Run `python3 adversarial.py` — 121 checks written to falsify these claims, not
confirm them. It has caught two real errors in my own work.

---

## The five findings that matter

**1. Extension degree 4 is a universal default, and it caps every deployed
system near 50 post-quantum bits.** RISC Zero, SP1, OpenVM, OpenVM2, Pico,
Airbender all use it. Degree 9–10 over a 31-bit base reaches 128 PQ bits for
~800 KiB, resting on collision resistance plus the random oracle — no conjecture,
no lattice. It is a configuration choice nobody has revisited.
→ `pq_design.py`, `quantum.py`

**2. Under a quantum adversary, everything halves — not just grinding.**
*(Caveat added iteration 23: the halving is the standard engineering rule, not
verified against [eprint 2025/2166](https://eprint.iacr.org/2025/2166), the
treatment soundcalc itself defers to. If the real QROM loss is small rather than
a square root, degree-4 systems sit at ~102 PQ bits and this finding inverts.
Treat every PQ number here as a conservative lower bound.)*
Fiat–Shamir hands the adversary transcript control, so finding a favourable
challenge is Grover-able. `PQ bits = classical / 2`, applied to commit phase,
query phase, DEEP and grinding alike. **No deployed system reaches 100 bits of
provable post-quantum soundness.** The quantum weakness of a hash-based STARK is
not the hash — it is Fiat–Shamir.
→ `quantum.py`

**3. The regime crossover predicts real engineering decisions, 7/7.**
Unique decoding beats the Johnson bound above `s* = (K_J(m_eq) − g)/y_UDR`, where
`m_eq(R) = 2^{R/2}/(2^{R/2}−1)²`. Tested against seven production zkVMs whose
teams chose independently — two above the crossover in UDR, five below in JBR —
the theorem calls every one. SP1's config literally declares `udr_only = true`
at `s = 124` against a predicted `s* = 112`. Where soundcalc publishes the UDR
figure too — all seven — the model reproduces it within 1 bit (max deviation
+0.9, never undershooting). Venus is excluded as a parameter-identical
duplicate of ZisK.
→ `regime_crossover.py`, `THEOREM.md` Thm 7

**4. Two of the five levers are free, and belong to whoever last proved a
theorem.** A system deployed in 2020 at 31-bit⁴ had a ceiling of 52 classical
bits. The identical system today has 103 — no config change, no protocol change.
The exponent went `a: 2 → 1` (BCIKS20 → BCHKS25) and the constant improved.
Each decrement of `a` is worth `ν` bits, more than doubling the extension degree
buys per unit of proof size.
→ `ceiling_anatomy.py`

**5. The `a ≥ 1` floor is provably tight, not a proof artifact.** For the
interleaved linear-code test (Ligero, and hence Brakedown), Roth–Zémor give
false-witness probability `(e+1)/q`, and Diamond–Posen Remark 2 proves it
**cannot be decreased**, with an explicit counterexample attaining it. So the
`2 → 1` improvement was real proof engineering; `1 → 0` is not available for this
class of test. The only `a = 0` code route known is conditional on an unproven
conjecture.
→ `THEOREM.md`, `adversarial.py`

---

## Where the cost actually is

Soundness parameters are nearly free on the prover. **NTT is 90–91% of proof
generation latency**, and front-end trace generation is 20–30% today and would
exceed 90% at a 5× backend speedup. Query count governs proof size and verifier
work, not prover time. The next order of magnitude in zkVM performance looks
like systems engineering, not a better low-degree test.
→ `EFFICIENCY.md`

Merkle authentication paths share prefixes, and the top `log₂ s` levels of the
tree saturate entirely. Charging `s·depth` overcounts by 33–52% at the query
counts 128-bit PQ requires. Model validated against Monte Carlo to 0.3%.
→ `merkle_dedup.py`

---

## Files

| file | what |
|---|---|
| `adversarial.py` | **121 falsification checks + 26 forgery attacks.** Start here. |
| `ceiling_anatomy.py` | the five-term ceiling; historical movement of `a` |
| `quantum.py` | the PQ halving; no system clears 100 provable PQ bits |
| `pq_design.py` | what 128 PQ bits actually costs to build |
| `regime_crossover.py` | Thm 7, the UDR/JBR crossover, 5/5 prediction |
| `real_configs.py` | source-verified configs; BCHKS25 vs BCIKS20 |
| `merkle_dedup.py` | path deduplication, validated by simulation |
| `lattice_compare.py` | why lattices escape the ceiling and what it costs |
| `nado_audit.py` | audit of a live chain: 47 provable bits vs 146 claimed (**fix landed 2026-07-28; migration is PARTIAL, true figure 63**) |
| `nado_ext_fri_prototype.py` | GF(p²) FRI fold, 10/10 against real modules |
| `THEOREM.md` | proofs, Parts I–IV |
| `SOURCES.md` | verbatim upstream quotes for every parameter |
| `EFFICIENCY.md` | the prover cost decomposition |
| `HORIZONS.md` | multilinear vs lattice, and what each costs |

Superseded but retained for the record: `stark_soundness.py`, `regimes.py`,
`frontier.py`, `post_johnson.py`, `verify_theorem.py`.

---

## Corrections made along the way

This repo overturned itself repeatedly. Recording it, because the correction
rate is the main reason to trust what survived.

1. **The RS up-to-capacity conjecture is not open — it was disproved in late
   2025** (Crites–Stewart 2025/2046; Diamond–Gruen 2025/2010). An early revision
   called proving it "the highest-leverage open problem in the field."
2. **BCIKS20's `(m+½)⁷n²` bound is superseded by BCHKS25's `(2m'⁵+…)n`** —
   exponent 7→5 and `n²→n`, worth +29 bits. Parts I and II were built on the
   older bound.
3. **Lattices escape the ceiling.** `HORIZONS.md` originally implied they only
   trade resilience for speed.
4. **"Exactly three levers" was wrong** — there are five, and two of them have
   moved in the literature without anyone changing a config.
5. **Per-system parameters were recalled, not read**, until `SOURCES.md`. Only
   RISC Zero shipped a production config; Plonky3 and Stwo ship none.

The adversarial suite additionally caught two numerical errors in my own math —
a catastrophic-cancellation instability in Theorem 4's closed form, and a
rate-dependent constant used at the wrong rate — neither of which re-reading the
derivations would have found.

---

## Open, and not closeable from here

- **Q2** (action-orbit, eprint 2026/861) would give `a = 0` on a code layer,
  worth ~22 bits. Conditional on an unproven sparse-dominance conjecture.
- **Diamond–Posen Conjecture 1**: does the interleaved test reach the
  unique-decoding radius while keeping the sharp `(e+1)/q`? Worth ~37% of
  queries. Open in the literature.

Both are genuinely open problems, not gaps in this analysis.

---

## Caveats

The model is FRI/code-layer only; soundcalc composes DEEP-ALI and LogUp terms
this repo does not. It therefore **upper bounds** published totals — verified to
never undershoot across seven systems. Where FRI binds it matches to 0.1 bits;
where another component binds it runs 3–5 high, and that residual is the
untuned-`m` gap, measured.

Asymptotics for systems outside the verified set are transcribed from cited
literature, not re-derived. The NADO audit was read from source, not executed.
