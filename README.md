# STARK soundness analysis — where the slack actually is

Concrete soundness modelling for FRI-based proof systems, a map of the
post-quantum argument-system frontier, and an honest accounting of which
parts of the security budget are improvable, which are conjecture-bound, and
which are information-theoretically floored.

```
python3 real_configs.py       # START HERE -- source-verified configs, BCHKS25 bound
python3 regimes.py            # four-regime model post the 2025 capacity disproof
python3 verify_theorem.py     # numerical checks for THEOREM.md Parts I-II
python3 stark_soundness.py    # original BCIKS20 model + landscape (superseded)
python3 frontier.py           # quantum adjustment + frontier map + slack decomposition
```

No dependencies beyond the standard library.

## Read this first

The analysis was revised twice as better information arrived, and the later
revisions overturn earlier headlines. In order of authority:

1. **`SOURCES.md`** — configurations and formulas read from upstream source on
   2026-07-28, with verbatim quotes. Supersedes all recalled parameters.
2. **`THEOREM.md` Part III** — what the real source changed.
3. **`THEOREM.md` Part II** — the post-disproof regime model.
4. **`THEOREM.md` Part I** and the findings below — built on BCIKS20, now
   superseded by BCHKS25 in several numbers.

Three headline corrections, in short:

- **The RS up-to-capacity conjecture is not open — it was disproved in late
  2025** (Crites–Stewart 2025/2046; Diamond–Gruen 2025/2010). An earlier
  revision called proving it "the highest-leverage open problem in the field".
  Johnson-bound soundness is untouched, and the repricing costs 1–3 queries.
- **BCIKS20's `(m+½)⁷·n²` commit bound is superseded by BCHKS25's
  `(2m'⁵+…)·n`** — exponent 7→5 and `n²→n`, worth ~+29 bits. Plonky3 ships this
  today. Ceilings below that cite ~77 bits should read ~90+.
- **Per-system blowup/query/grinding values were recalled, and mostly were not
  real configs.** Only RISC Zero ships one (blowup 4, 50 queries, no grinding,
  trace 2²⁰, 97-bit conjectured target — my recollection was right). Plonky3 and
  Stwo take parameters from the caller.

The most durable single number: **at their own deployed query counts these
systems have ~50–60 bits of provable soundness against ~97–100 conjectured.**

## Scope, honestly stated

This repo does **not** contain a new proof system that surpasses STARKs. That
is a multi-year research programme ending in a security proof, and anyone who
tells you otherwise is selling something. What it contains is the work that
has to come first: a quantitative account of where the exploitable slack in
the current constructions is, so that effort aimed at surpassing them is
aimed at the right term.

The model follows **ethSTARK Documentation v1.2** (Ben-Sasson, Goldberg,
Kopparty, Saraf), Sections 5–6, which instantiates **BCIKS20**, "Proximity
Gaps for Reed–Solomon Codes" (Ben-Sasson, Carmon, Ishai, Kopparty, Saraf).

## Findings

### 1. The conjecture is worth exactly 2×, uniformly

Per-query security yield, `R = log2(blowup)`:

| regime | per-query yield | status |
|---|---|---|
| unique decoding | `-log2((1+ρ)/2)` | unconditional |
| Johnson (BCIKS20) | `≈ R/2` | proven |
| capacity (ethSTARK Conj. 1) | `R` | conjectured |

The ratio is 2.19× at blowup 2 and converges to 2.05× at blowup 16. Every
deployed STARK's headline security number depends on this conjecture, and the
dependence is worth a factor of two in query count — no more, no less.

### 2. Every 31-bit-field system is conjecture-bound *by construction*

The FRI commit phase contributes `E + log2(3) − 7·log2(m+½) − 1.5R − 2ν` bits,
where `E = log2|F_ext|`. This term cannot be bought with queries. At a
degree-4 extension of a 31-bit field (`E = 124`) and a 2²⁰ trace:

| system | E | proven ceiling | conjectured ceiling | E needed for 100 proven |
|---|---|---|---|---|
| Stwo (M31) | 124 | **78.0** | 102.0 | 147 |
| Plonky3 (KoalaBear) | 124 | **78.0** | 102.0 | 147 |
| RISC Zero (BabyBear) | 124 | **74.5** | 100.0 | 150 |
| Plonky2 (Goldilocks) | 128 | **75.0** | 102.0 | 154 |
| Winterfell / Miden | 192 | 139.0 | 166.0 | 154 |
| Cairo / StarkNet | 251 | 194.5 | 223.0 | 157 |

Those ceilings hold at *unlimited* query count. 100 bits of unconditional
security is unreachable at `E = 124` — not at any query count, not at any
grinding level, not at any blowup factor. The small-field performance win is
paid for in assumption strength, and that is a design decision rather than a
tuning oversight.

### 3. The Johnson parameter `m` is a free knob nobody exposes

`m` trades per-query yield against the commit term at rate `7·log2(m+½)`.
Optimising it is free — it changes no protocol, only the analysis:

| system | m\* | bits at m\* | bits at m=16 | Δ |
|---|---|---|---|---|
| Boojum (zkSync) | 6 | 58.8 | 50.8 | **+8.0** |
| Plonky2 | 9 | 55.8 | 50.8 | **+5.0** |
| Plonky3 (BabyBear) | 10 | 54.8 | 50.3 | **+4.6** |
| ethSTARK doc params | 1 | 5.5 | −18.7 | **+24.2** |

### 4. Grinding is half-price against a quantum adversary

Proof-of-work grinding costs the verifier nothing, which is why deployed
systems lean on 16–24 bits of it. Grover gives a quadratic speedup on nonce
search, so `g` bits of grinding are worth `g/2` post-quantum. Stwo's
representative parameters lose 10 bits this way; recovering them costs 10 more
FRI queries, which the verifier *does* pay for.

A system advertising 100 post-quantum bits while leaning on 20 bits of
grinding is advertising ~90.

### 5. Where the slack is, ranked by impact-to-difficulty

- **Commit-phase constant — best ratio on the list.** The `(m+½)⁷` factor in
  BCIKS20 is an artifact of proof technique, not a lower bound. Nobody
  believes exponent 7 is tight. Reducing it to 3 hands every small-field
  system ~11 free bits. This is proof engineering on an existing theorem, not
  a new assumption.
- **The RS capacity conjecture — highest absolute impact.** Proving
  Reed–Solomon codes list-decodable to capacity with polynomial list size
  upgrades every deployed STARK by 2× simultaneously. Precise, known
  statement; pure mathematics.
- **Query count — already solved, adoption lag.** STIR shrinks the rate each
  round rather than holding it fixed: `O(log d + λ log log d)` queries versus
  FRI's `O(λ log d / log(1/ρ))`, worth 1.25–2.4× in practice. Anyone still on
  vanilla FRI is leaving that on the table today.
- **Arithmetization — widest open space.** Everyone optimises the polynomial
  commitment; the encoding of computation into constraints is where Binius
  (bit-level witnesses) and WHIR (native multilinear queries) found their
  wins. More slack here than in FRI itself.

**Not slack:** an IOPP for a rate-ρ code has an information-theoretic floor
around `λ/log(1/ρ)` queries in the correlated-agreement framework. You beat it
by changing the *code* (Binius, Blaze, BaseFold) or the *proximity test*
(STIR, WHIR) — never by tuning FRI. That is a cheap filter for anyone pitching
you a scheme.

## The three requirements do not jointly maximise

Post-quantum + scaling + resilient is a Pareto frontier, not a checklist:

- **Resilient** — hash-based IOPs rest on collision resistance plus the ROM,
  the weakest assumption anyone knows how to build succinct arguments from.
  FRI/STIR/WHIR are already at that floor. Nothing is *more* resilient.
- **Scaling** — lattice systems (LaBRADOR ~50KB, Greyhound √n verifier)
  produce far smaller proofs, paying with M-SIS: post-quantum, but a
  structured assumption with a live cryptanalytic literature whose parameter
  estimates have moved before.

So "surpass STARKs, post-quantum, scaling, resilient" resolves to one of:
take STIR/WHIR's query win and stay hash-based; move to lattices and accept a
structured assumption; or attack the conjecture gap itself.

## Caveats

- Field and extension-degree parameters are exact. **Blowup, query count, and
  grinding values per system are representative defaults from recollection,
  not read from source.** They are the entries to verify before leaning on any
  per-system conclusion.
- Frontier asymptotics are transcribed from the cited literature, not
  re-derived here.
- The proof-size model counts Merkle authentication paths only, uncompressed —
  no path sharing, no Merkle caps, no batching. Absolute sizes are therefore
  overestimates; relative comparisons hold.
- The 85.3-bit quantum hash cap is `256/3` (BHT), which requires implausible
  quantum RAM. The defensible figure is `256/2 = 128`, which binds nothing in
  these tables.

## Files

- `stark_soundness.py` — soundness terms, cost model, `m` optimiser, landscape
  table, ceiling analysis, minimum-proof-size parameter search
- `frontier.py` — quantum adjustment, frontier map (FRI → DEEP-FRI → Proximity
  Gaps → STIR → WHIR → BaseFold → Binius → Blaze → lattices), slack decomposition
