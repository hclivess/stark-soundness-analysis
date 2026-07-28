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
binds**. That single fact explains the rest of this repo. (Strictly the BCS
theorem composes by *sum*; the min-model overstates by at most `log₂(#terms)`,
measured at ≤0.34 bits on every deployed config — `bcs_composition.py`.)

Run `python3 adversarial.py` — 202 checks written to falsify these claims, not
confirm them. It has caught two real errors in my own work.

---

## The five findings that matter

**1. Extension degree 4 is a universal default, and it caps every deployed
system near 50 post-quantum bits.** RISC Zero, SP1, OpenVM, OpenVM2, Pico,
Airbender all use it. Degree 9–10 over a 31-bit base reaches 128 PQ bits for
~800 KiB *(at `c = 2`; see finding 2 — at `c = 3` it needs degree 14)*, resting
on collision resistance plus the random oracle — no conjecture, no lattice. It
is a configuration choice nobody has revisited. **It also needs a 386-bit Merkle
digest**: quantum collision finding costs `2^{λ/3}`, so the ubiquitous 256-bit
default caps the design at 85 PQ bits however large the extension degree is.
(13 field elements over a 31-bit base = 403 bits clears it.)
→ `pq_design.py`, `quantum.py`

**2. Under a quantum adversary, everything halves — not just grinding, and
`classical/2` is the *ceiling*, not the conservative floor.** Fiat–Shamir hands
the adversary transcript control, so finding a favourable challenge is Grover-able.
Grinding nonces is unstructured search of density `2^−k`: Grover achieves `2^{k/2}`
and BBBV forbids better, so the provable range is

```
k/c ≤ PQ ≤ k/2,   c ≥ 2   (c = the QROM reduction's query-loss exponent)
```

`c` is **term-dependent**, not one constant: `c = 2` for challenge search
(Grover achieves, BBBV forbids better) but `c = 3` for the hash chain (BHT
achieves, Zhandry forbids better).

`classical/2` bounds **provable** PQ soundness from *above* and **true** PQ
security from *below* — the two coincide only where the classical bound is
attained. Chiesa–Yogev prove that Fiat–Shamir's grinding bound *is* attained,
two-sided, with a matching universal attack, and exact amplitude amplification
puts Grover 1.35 bits below the modelled `2^{k/2}`. That splits the PQ claims
in two: **no deployed system reaches 100 provable PQ bits** is *unconditional* —
the query phase binds for all seven verified zkVMs and its bound is *attained*,
so its halving is exact, and the largest deployed query term (ZisK, 128) caps the
whole field at **64 PQ bits**. The *design target* (finding 1) is the conditional
one: it is a commit-phase ceiling, and the commit bound is not known attained.
→ `qrom_bracket.py`, `quantum.py`

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
interleaved linear-code test (Ligero, and hence Brakedown), Roth–Zémor's
Theorem 1 gives false-witness probability `(e+1)/q` for `e ≤ (d−1)/3`. Since
`d = Θ(n)`, the numerator is `Θ(n)` — **`a = 1`, not the `O(1)` of folklore**,
which conflates independence of the *interleaving width* (true, and the point of
the lemma) with independence of the *block length* (false). Diamond–Posen
Remark 2 records it as sharp via an explicit Ben-Sasson et al. construction
attaining `(e+1)/q` exactly. So the `2 → 1` improvement was real proof
engineering; `1 → 0` is not available for this class of test. The only `a = 0`
code route known is conditional on an unproven conjecture.
→ `interleaved_proximity.py`, `THEOREM.md`

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
| `adversarial.py` | **202 falsification checks + 26 forgery attacks.** Start here. |
| `ceiling_anatomy.py` | the five-term ceiling; historical movement of `a` |
| `quantum.py` | the PQ halving; no system clears 100 provable PQ bits |
| `qrom_bracket.py` | `k/c ≤ PQ ≤ k/2`; which PQ claims survive the unpinned constant |
| `capacity_frs.py` | capacity moved to folded RS — and buys ~0%, not 50% |
| `open_zone.py` | evidence tiers of the BOUNDS table; what room is left above Johnson |
| `capacity_routes.py` | all three capacity routes; each closed, for two different reasons |
| `interleaved_proximity.py` | the interleaved/Ligero case resolved: `a = 1`, sharp |
| `merkle_extraction.py` | ε_MT expanded; the 3.5 constant derived; 256 bits ≠ 128 |
| `bcs_composition.py` | BCS composes by sum; the hash term's QROM loss is 3, not 2 |
| `fs_tightness.py` | Chiesa–Yogev's two-sided FS bound; Grover checked against exact amplitude amplification |
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
   *Refined iteration 29:* the disproof is specific to **plain RS over prime
   fields** (and Kambiré 2026 sharpens it to `O(1/log n)` *below* capacity).
   Capacity-radius gaps are **proved** for folded RS, subspace-design codes and
   random-evaluation RS. But *(iteration 30)* **every one of those routes is
   closed at deployed parameters**: folded RS pays `m ≥ c/η²` in payload, and the
   unfolded random ensembles need fields of `exp(Ω(1/η⁴))` to `exp(Ω(1/η⁷))` —
   thousands to millions of bits. Folding is exactly what trades payload for a
   polynomial field. (`capacity_frs.py`, `capacity_routes.py`)
2. **BCIKS20's `(m+½)⁷n²` bound is superseded by BCHKS25's `(2m'⁵+…)n`** —
   exponent 7→5 and `n²→n`, worth +29 bits. Parts I and II were built on the
   older bound.
3. **Lattices escape the ceiling.** `HORIZONS.md` originally implied they only
   trade resilience for speed.
4. **"Exactly three levers" was wrong** — there are five, and two of them have
   moved in the literature without anyone changing a config.
5. **Per-system parameters were recalled, not read**, until `SOURCES.md`. Only
   RISC Zero shipped a production config; Plonky3 and Stwo ship none.
6. **Iteration 23 hedged the wrong PQ claim.** It called the halving a
   "conservative lower bound" and warned the headline could invert if the QROM
   loss were negligible. Grover on Fiat–Shamir is an *attack*, so a negligible
   loss is impossible: `classical/2` is the best case. The negative headline is
   unconditional; the *design recommendation* is what depends on the constant.
7. **A 256-bit digest gives 127.1 classical bits, not 128**, and iteration 26's
   "384-bit digest for 128 PQ" was 0.6 bits short — the real requirement is 386.
   BCS's additive error carries a leading constant of 3.5, worth `log₂(3.5)/2`
   ≈ 0.90 classical bits and 0.60 PQ bits. Round numbers hid it.
8. **The hash term loses a factor 3, not 2.** `PQ = classical/2` is not
   universal: BCS's additive error is `t²/2^λ`, a birthday bound, so classical
   security is `λ/2` and quantum is `λ/3` (BHT above, Zhandry's `Ω(N^{1/3})`
   below). `pq_design.py` set its hash floor with the *classical* exponent in a
   function that reports post-quantum bits.
9. **…and iteration 24 then overcorrected.** "Conservative lower bound" and
   "optimistic upper bound" are *both* right — of different quantities.
   `classical/2` bounds **provable** PQ soundness from above and **true** PQ
   security from below; the two coincide only on attained terms. Neither
   iteration said which it meant.

The adversarial suite additionally caught two numerical errors in my own math —
a catastrophic-cancellation instability in Theorem 4's closed form, and a
rate-dependent constant used at the wrong rate — neither of which re-reading the
derivations would have found.

---

## Open, and not closeable from here

- **Q2** (action-orbit, eprint 2026/861) would give `a = 0` on a code layer,
  worth ~22 bits. Conditional on an unproven sparse-dominance conjecture — *and*
  on the open zone above Johnson being non-empty, which Kambiré 2026 squeezes
  from above at an unpinned rate (`open_zone.py`). **Two** unknowns, not one.
  This is the repo's largest claimed win and rests on its weakest source: an
  unreviewed preprint, abstract verified but PDF unreachable, uncited by the
  subsequent literature. Capacity-radius FRS gaps do **not** deliver it either —
  they keep `a = 1`.
- **Diamond–Posen Conjecture 1**: does the interleaved test reach the
  unique-decoding radius `(d−1)/2` while keeping the sharp `(e+1)/q`, instead of
  stopping at `(d−1)/3`? Worth a **37–40%** query cut, rising with blowup
  (36.6% at rate ½, 40.1% at rate ⅛). Open in the literature.

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
