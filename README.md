# The provable-soundness ceiling of hash-based proof systems

Everything in this repository reduces to one equation and one classification.

```
ceiling = E − a·ν − log₂C + g_commit
```

`E` = log₂ of the challenge field, `ν` = log₂ of the evaluation domain, `a` = the
exponent on the domain size in the commit-phase error, `C` = the bound's constant
factor, `g_commit` = commit-phase proof-of-work.

| layer / radius | exponent `a` | numerator | status |
|---|---|---|---|
| sumcheck / zerocheck / RLC / Jagged | **0** | `O(log n)` or `O(constraints)` | read off the formulas |
| RS proximity, **unique-decoding** `δ/2` | **0** | `O_{ε*}(1)` | **proved**, all RS (ε\* > 0) |
| RS proximity, **Johnson** `J(δ)` | **1** | `O(n)` | **proved**, all RS (ε\* = 0) |
| RS proximity, **beyond Johnson** | **≥ 1.99, unbounded** | `Ω(n^1.99)`, `n^τ` ∀τ | **proved** floor, some RS codes |
| Ligero / Brakedown (interleaved) | **≥ 1** | `e+1 = Θ(n)` | **proved** floor, sharp |

`a` is a **staircase in the proximity radius**, not one number — see
`radius_staircase.py`. All five rows are from BCHKS25's own result list, which
this repo cited for 32 iterations without reading.

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

Run `python3 adversarial.py` — 651 checks written to falsify these claims, not
confirm them. It has caught two real errors in my own work.

---

## The five findings that matter

**1. Extension degree 4 is a universal default, and it caps every deployed
system near 50 post-quantum bits.** RISC Zero, SP1, OpenVM, OpenVM2, Pico,
Airbender all use it. Degree 9–10 over a 31-bit base reaches 128 PQ bits *(at
`c = 2`; see finding 2 — at `c = 3` it needs degree 14)*, resting
on collision resistance plus the random oracle — no conjecture, no lattice. It
is a configuration choice nobody has revisited. **It also needs a 386-bit Merkle
digest**: quantum collision finding costs `2^{λ/3}`, so the ubiquitous 256-bit
default caps the design at 85 PQ bits however large the extension degree is.
(13 field elements over a 31-bit base = 403 bits clears it.)

*(Iteration 72: this said "for ~800 KiB". That figure charges two base field
elements per query — **a two-column trace**. Real zkVM traces are 18–80,000
columns, where leaf data is 60–99.6% of the proof. Priced in the model verified
against all 122 published figures, the same configuration is **1,188 KiB at one
column and 6,591 KiB at Airbender's width**; a realistic 128-PQ single circuit
is **4–19 MiB** depending on blowup.)*

*(Iteration 73 refines that: recursion **does** compress it. Every stage of a
real pipeline carries the full target — Pico 53×5, OpenVM 100×3, SP1 100×3,
OpenVM2 100×6 — so Proposition 11 applies to the final stage too and sets a
floor of **~0.9–1.5 MiB** for a 128-PQ verifier-facing proof, against 200–529
KiB shipping today. That is **2–4×**, not the orders of magnitude iteration 72
implied — that figure was the base layer, which the verifier never sees. And
reproducing pq_design's own two-column assumption gives 778 KiB against its 797,
so finding 1's number is within ~30% of the honest floor: **wrong derivation,
roughly right answer**.)*

*(Iteration 74 pins it. Every deployed recursion stage **is** a measurement of
the missing constant — its trace area against the verification work it does.
Five stages across Pico and SP1 give **1.2×10⁴–4.7×10⁴ cells per Merkle node**,
which reproduces the assumed T = 18–20 but, once the 384-bit digest's 1.62×
widening is applied, removes the 879 KiB low end. Optimising the aspect ratio —
narrow wins, since leaf data scales with batch but paths only logarithmically —
the floor is **977–1140 KiB**. So 128 PQ bits costs **1.8×–5.7×** the proof
anyone transmits, and finding 1's 797 KiB is within **18%** of the low end.
"No conjecture, no lattice" stands.)*
→ `pq_design.py`, `quantum.py`, `pq_design_cost.py`

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

**3. The regime crossover predicts real engineering decisions, 7/7 — and is
invariant to the UDR ceiling.** When iteration 33 found soundcalc's UDR bound
superseded (`a = 0` is proved there), the obvious worry was that 7/7 was an
artifact of the stale bound. It is not: `s*` contains no `K_UDR` term, so
recomputing with the corrected ceiling leaves every `s*` bit-identical
(`udr_a0.py`).
Unique decoding beats the Johnson bound above `s* = (K_J(m_eq) − g)/y_UDR`, where
`m_eq(R) = 2^{R/2}/(2^{R/2}−1)²`. Tested against seven production zkVMs whose
teams chose independently — two above the crossover in UDR, five below in JBR —
the theorem calls every one. SP1's config literally declares `udr_only = true`
at `s = 124` against a predicted `s* = 112`. Where soundcalc publishes the UDR
figure too — all seven — the model reproduces it within 1 bit (max deviation
+0.9, never undershooting). Venus is excluded as the **same codebase at a
different version** (0.1.6 vs ZisK 0.16.1) — not an independent design decision,
which is what the test needs. *(Iteration 61: this said "parameter-identical",
which is false — 40 of 44 circuits are byte-identical, 3 differ only in a
`group` label, and Venus's `Final` circuit is genuinely wider: 135 columns and
batch 158 against ZisK's 114 and 139.)*
→ `regime_crossover.py`, `THEOREM.md` Thm 7

**4. Two of the five levers are free, and belong to whoever last proved a
theorem.** A system deployed in 2020 at 31-bit⁴ had a ceiling of 52 classical
bits. The identical system today has 103 — no config change, no protocol change.
The exponent went `a: 2 → 1` (BCIKS20 → BCHKS25) and the constant improved.
Each decrement of `a` is worth `ν` bits, more than doubling the extension degree
buys per unit of proof size.
→ `ceiling_anatomy.py`

**5. The `a ≥ 1` floor is provably tight *for interleaved codes* — and only
there.** The strongest known lower bound for RS (mutual correlated agreement,
`err ≥ (L+1)/q`, Gao et al. 2026) has `L = 2m+1`, **independent of `n`**, so it
permits `a = 0` at the Johnson radius. Between BCHKS25's bound and that floor sit
**20.6–45.0 bits nobody has closed** (`a_floor_scope.py`). Measured on the one
deployed system whose soundness actually *rests* on mutual correlated
agreement — OpenVM2, which **declares** its list parameter — the headroom is
**18.2–22.0 bits, the narrowest of any shipping system**: WHIR extracts more of
the provably available room than FRI, and has correspondingly less left to gain
(`mca_headroom.py`).

**But most of that gap is not a target.** The MCA floor bounds a *per-instance*
list quantity; BCHKS25's commit bound unions over the evaluation domain and
carries an explicit factor `n`. Subtracting gives **Proposition 9**:
`F − K_nq = ν + log₂(fold) + 1` (exact, to within 0.07 bits at deployed `m`).
The leading term carries no `m`, no `ρ` and no `E` — it is a property of the two
bounds' *shapes*, and no proximity-gaps theorem can close it. So the gap splits
**59% structural / 41% slack**: of 39–45 bits, only **14–21** are available even
in principle, and only to a sharper *linear* term — the `n/q` branch is already
slack, binding at just 25 of 700 swept points, all at `m < 1`.
→ `headroom_split.py` For the
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
generation latency** *(that share is measured on MSM-paired systems — see
`ntt_share_scope.py`; the ordering holds, the percentage does not transfer)*, and
front-end trace generation is rapidly becoming the bottleneck
*(`efficiency_sources.py` — the qualitative claim is sourced, earlier
percentages were not locatable and are withdrawn)*. Query count governs proof size and verifier
work, not prover time. The next order of magnitude in zkVM performance looks
like systems engineering, not a better low-degree test.
→ `EFFICIENCY.md`

Merkle authentication paths share prefixes, and the top `log₂ s` levels of the
tree saturate entirely. Charging `s·depth` overcounts by **26–40% across the
seven deployed zkVMs** (42% at NADO's 320 queries). *(Iteration 60: this said
33–52%, the range of a hypothetical `s = 32…1000` sweep — 51.7% needs 1000
queries, and five shipping systems fall below 33%. Iteration 60's own
replacement, 30–41%, was also wrong: it used the trace length as the tree depth
when the tree is over the LDE domain, `2^{T+R}`.)* The model's
independent-sibling approximation is validated to <1 node per tree against
soundcalc's exact formula, and to 0.3% against Monte Carlo.
→ `merkle_dedup.py`, `merkle_exact.py`

**The whole proof-size model is exact.** Reconstructing
`get_FRI_proof_size_bits` from the tomls alone reproduces all **122 published
figures** — 55 FRI circuits across six systems, expected and worst case — with
zero deviation. This also shows each system's headline size is its *last*
circuit, not an aggregate, and that Venus differs from ZisK in one circuit.
→ `proof_size_exact.py`

---

## Files

| file | what |
|---|---|
| `adversarial.py` | **651 falsification checks, 26 of them forgery attacks against a live prover.** Start here. |
| `ceiling_anatomy.py` | the five-term ceiling; historical movement of `a` |
| `quantum.py` | the PQ halving; no system clears 100 provable PQ bits |
| `qrom_bracket.py` | `k/c ≤ PQ ≤ k/2`; which PQ claims survive the unpinned constant |
| `capacity_frs.py` | capacity moved to folded RS — and buys ~0%, not 50% |
| `pq_ranking.py` | HORIZONS thread 3: the PQ ranking does **not** reorder, and the threshold |
| `airbender_verified.py` | Airbender's full table; `jbrM` vs `m_eq` cuts JBR error 52.7→3.3 bits |
| `sp1_verified.py` | SP1's components, machine-checked: the 100 is set by FRI query **and** lookup |
| `lean_theorems.py` | two Lean theorems prove the repo never undershoots soundcalc |
| `soundcalc_lean.py` | the Lean formalization: `m` is derived, not free; Thm 7 robust to it |
| `m_star.py` | the `m` hinge is the query budget; the `m≥3` floor costs **zero** (it 39 corrects it 38) |
| `theorem4_scope.py` | Thm 4 needed the `m ≥ 3` correction III.3 exempted it from |
| `blowup_theorem.py` | Theorem 8: blowup 4 is optimal iff `c = 2(a+b)`; scope of Thm 3′ |
| `provenance_grades.py` | all 7 systems × 5 params verified against `ethereum/soundcalc` — 35/35 |
| `systems.py` | the canonical system table, regime baked in; drift detector |
| `staleness_guard.py` | mechanical guard against this repo's own retracted claims |
| `udr_a0.py` | what BCHKS25's proved `a=0` at UDR is worth, and the constant that decides it |
| `radius_staircase.py` | `a` is a staircase in the radius: 0 at UDR, 1 at Johnson, unbounded above |
| `a_floor_scope.py` | what `a ≥ 1` is *proved* for; 20.6–45.0 bits of unclosed headroom (regime-, m- and list-corrected, it 40/57/68) |
| `open_zone.py` | evidence tiers of the BOUNDS table; what room is left above Johnson |
| `ligero_obstacles.py` | two of the four obstacles dissolve: alphabet already met, sampling `2^-360` |
| `ligero_composition.py` | where the capacity gain sits vs unique decoding; splits the prize |
| `ligero_proof_size.py` | Ligero/Brakedown size model: the field term scales as `√t` |
| `linear_code_capacity.py` | pricing the one open capacity route: 2.4–4.6× yield for linear-code systems |
| `capacity_routes.py` | all three capacity routes; closed by **structure**, not field size (it 42 corrects it 30) |
| `interleaved_proximity.py` | the interleaved/Ligero case resolved: `a = 1`, sharp |
| `merkle_extraction.py` | ε_MT expanded; the 3.5 constant derived; 256 bits ≠ 128 |
| `bcs_composition.py` | BCS composes by sum; the hash term's QROM loss is 3, not 2 |
| `fs_tightness.py` | Chiesa–Yogev's two-sided FS bound; Grover checked against exact amplitude amplification |
| `pq_design.py` | what 128 PQ bits actually costs to build |
| `regime_crossover.py` | Thm 7, the UDR/JBR crossover, 5/5 prediction |
| `real_configs.py` | source-verified configs; BCHKS25 vs BCIKS20 |
| `efficiency_sources.py` | audit of EFFICIENCY.md's cited figures; two of three had sourcing problems |
| `ntt_share_scope.py` | EFFICIENCY.md's NTT share is from MSM-paired systems; the sweep that survives it |
| `merkle_dedup.py` | path deduplication, validated by simulation |
| `lattice_field_escape.py` | HORIZONS thread 4: the field-size escape quantified (4.4× at 128 PQ) |
| `lattice_compare.py` | why lattices escape the ceiling and what it costs |
| `nado_backport.py` | what to backport to NADO after it 24–50; a remaining base-field challenge |
| `nado_audit.py` | audit of a live chain: 47 provable bits vs 146 claimed (**fix landed 2026-07-28; migration is PARTIAL, true figure 63**) |
| `nado_ext_fri_prototype.py` | GF(p²) FRI fold, 10/10 against real modules |
| `THEOREM.md` | proofs, Parts I–IV |
| `SOURCES.md` | upstream quotes for formulas and totals; **all 35 system parameters verified against soundcalc's own `.toml`** (`provenance_grades.py`) |
| `EFFICIENCY.md` | the prover cost decomposition |
| `HORIZONS.md` | multilinear vs lattice, and what each costs |

Superseded but retained for the record: `stark_soundness.py`, `regimes.py`,
`frontier.py`, `post_johnson.py`, `verify_theorem.py`.

---

## Corrections made along the way

This repo overturned itself repeatedly. Recording it, because the correction
rate is the main reason to trust what survived. Since iteration 35 the
retractions are also **machine-enforced**: `staleness_guard.py` registers each
one and fails the suite if any file asserts a retracted claim without a nearby
retraction marker. It caught a stale assertion in `adversarial.py` on its first
run. Since iteration 41 `systems.py` holds the seven-system table **once**, with
each system's reported regime as a field, so the regime-mixing that produced two
separate errors (iterations 38 and 40) is impossible by construction rather than
caught after the fact.

1. **The RS up-to-capacity conjecture is not open — it was disproved in late
   2025** (Crites–Stewart 2025/2046; Diamond–Gruen 2025/2010). An early revision
   called proving it "the highest-leverage open problem in the field."
   *Refined iteration 29:* the disproof is specific to **plain RS over prime
   fields** (and Kambiré 2026 sharpens it to `O(1/log n)` *below* capacity).
   Capacity-radius gaps are **proved** for folded RS, subspace-design codes and
   random-evaluation RS. But *(iteration 30)* **every one of those routes is
   closed to FRI-based STARKs** — but for *structural* reasons, not field size.
   Folded RS pays `m ≥ c/η²` in payload; the unfolded routes are field-feasible
   (Yuan–Zhu: **22 bits** for random linear, 86–135 for random RS) but random
   linear codes have no `x → x²` folding map and random evaluation points cost
   ~20× prover. The random-linear route is genuinely **open** to
   Ligero/Brakedown-style systems. (`capacity_frs.py`, `capacity_routes.py`)
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
  (36.6% at rate ½, 40.1% at rate ⅛). Open in the literature. *(Iteration 45:
  this is exactly the portion of the capacity prize reachable inside unique
  decoding — two independent derivations agree to three significant figures.)*

Both are genuinely open problems, not gaps in this analysis.

---

## Caveats

The model is FRI/code-layer only; soundcalc composes DEEP-ALI and LogUp terms
this repo does not. It therefore **upper bounds** published totals — verified to
never undershoot across seven systems — and since iteration 55 that direction is
a consequence of two machine-checked theorems, not just seven data points
(`lean_theorems.py`). Where FRI binds it matches to 0.1 bits;
where another component binds it runs 3–5 high, and that residual is the
untuned-`m` gap, measured.

Asymptotics for systems outside the verified set are transcribed from cited
literature, not re-derived. The NADO audit was read from source, not executed.
