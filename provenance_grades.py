"""
Auditing SOURCES.md's own claim, the way EFFICIENCY.md's claims were audited.

*** SECTIONS 1-3 ARE ITERATION 58; SECTION 4 SUPERSEDES THEIR GRADING. ***
Iteration 58 found the provenance non-uniform and graded three systems "total
only". Iteration 59 cloned ethereum/soundcalc itself, which ships a .toml for
EVERY system, and verified all 35 parameters. The gap below is closed -- read
section 4 for the current state. The iteration-58 analysis is retained because
the reasoning about WHY the exposure was narrow still holds, and because the
correction rate is the point.

README describes SOURCES.md as carrying "verbatim upstream quotes for every
parameter". Iterations 52-54 audited EFFICIENCY.md's three cited claims and found
two mis-sourced, so the file this repo holds up as its rigorous one deserves the
same treatment. It has been wrong before: iteration 28 found SOURCES.md carried
NO entry for Diamond-Posen or Roth-Zemor despite README finding 5 citing them.

WHAT SOURCES.md ACTUALLY CARRIES
---------------------------------
106 block quotes across 715 lines. Specifically:

  * soundcalc's Python, quoted as code -- the FORMULAS. Thorough.
  * a summary table of each system's reported bits, regime and field.
  * detailed sections for Miden (with its .toml path) and RISC Zero.

What it does NOT carry, for most systems, is a verbatim quote for the individual
parameters this repo's canonical table holds -- queries, grinding, trace length,
blowup. Mention counts: RISC Zero 7, OpenVM 3, SP1 2, Airbender 2, Pico 2,
Miden 2, ZisK 1, against seven fields per system in `systems.py`.

So "verbatim upstream quotes for every parameter" is an overstatement of the same
kind found in EFFICIENCY.md: true of what the file does well (formulas, totals),
not true as stated.

BUT TWO SYSTEMS NOW HAVE SOMETHING STRONGER THAN A QUOTE
----------------------------------------------------------
soundcalc-lean ships machine-readable configs for SP1 and Airbender. Checking
`systems.py` against them, field by field:

  SP1, from SoundcalcIO/ZkVM/SP1.lean (a native_decide-checked file):
      rho = 1/4          -> R = 2          matches
      field koalaBear4   -> E = 4*31 = 124 matches
      denseLen 2^21      -> T = 21         matches
      numQueries 124     -> s = 124        matches
      grindQuery 16      -> g = 16         matches

  Airbender, from SoundcalcIO/ZkVM/Ref/airbender.toml:
      field "M31^4"          -> E = 124    matches
      trace_length 2^24      -> T = 24     matches
      num_queries 87         -> s = 87     matches
      grinding_query_phase 28 -> g = 28    matches

Ten of ten checkable parameters agree exactly. Airbender's blowup is not a named
field in the toml, but iteration 56 reproduced all five of its commit rounds
exactly at R = 1, which pins it as firmly as a quote would.

THE HONEST GRADING
------------------
    system      parameter provenance
    SP1         MACHINE-CHECKED  -- SP1.lean, all 5 fields verified
    Airbender   MACHINE-READABLE -- airbender.toml, 4 fields + R confirmed
    Miden       QUOTED           -- SOURCES.md cites miden.toml with parameters
    RISC Zero   QUOTED           -- 7 mentions, the best-documented of the rest
    OpenVM      TOTAL ONLY       -- reported bits recorded, parameters not quoted
    Pico        TOTAL ONLY
    ZisK        TOTAL ONLY

That is a real spread, and README flattened it. The same fix applied to the
BOUNDS table in iteration 31 applies here: state the grade rather than implying
uniformity.

WHY THIS MATTERS LESS THAN IT COULD
-------------------------------------
Every system's REPORTED TOTAL is recorded and is what the repo validates against,
and iteration 56 showed the model reproduces all five JBR totals within about a
bit at soundcalc's own m. So the conclusions do not rest on the unquoted
parameters being right -- they rest on the totals, which are recorded, and on the
formulas, which are quoted thoroughly.

The exposure is narrower: if OpenVM's, Pico's or ZisK's queries or grinding were
transcribed wrongly, the per-system term breakdowns computed from them would be
wrong while the totals stayed right. Nothing has flagged that, and the two
systems that CAN be checked came out exact, which is weak positive evidence for
the transcription generally.
"""

import math

# systems.py's canonical values, and the machine-readable sources for two of them
SP1_LEAN = {"rho": 0.25, "field_bits": 124, "denseLen_log": 21,
            "numQueries": 124, "grindQuery": 16}
AIRBENDER_TOML = {"field_bits": 124, "trace_log": 24,
                  "num_queries": 87, "grinding_query_phase": 28}

# UPGRADED IN ITERATION 59. Cloning ethereum/soundcalc itself gives a .toml for
# every system, not just the two soundcalc-lean ships. All seven are now
# machine-readable and all 35 fields verified.
PROVENANCE = [
    ("SP1 6.1.0", "MACHINE-CHECKED", "SP1.lean + sp1.toml, 5/5 fields"),
    ("Airbender", "MACHINE-READABLE", "airbender.toml, 5/5 (R = 1 from rho 0.5)"),
    ("Miden", "MACHINE-READABLE", "miden.toml, 5/5 (blowup_factor 8)"),
    ("RISC Zero", "MACHINE-READABLE", "risc0.toml, 5/5 (rho 0.25)"),
    ("OpenVM 1.5.0", "MACHINE-READABLE", "openvm.toml, 5/5 (blowup_factor 2)"),
    ("Pico", "MACHINE-READABLE", "pico.toml, 5/5 (blowup_factor 2)"),
    ("ZisK 0.16.1", "MACHINE-READABLE", "zisk.toml, 5/5 (rho 0.5)"),
]

# (E, R, T, s, g) as read from ethereum/soundcalc soundcalc/zkvms/*/*.toml
SOUNDCALC_TOML = {
    "SP1 6.1.0":    (124, 2, 21, 124, 16),   # KoalaBear^4, blowup 4, 2^21
    "OpenVM 1.5.0": (124, 1, 23, 193, 20),   # BabyBear^4,  blowup 2, 2^23
    "Airbender":    (124, 1, 24,  87, 28),   # M31^4,       rho 0.5,  2^24
    "Pico":         (124, 1, 22,  84, 16),   # KoalaBear^4, blowup 2, 2^22
    "ZisK 0.16.1":  (192, 1, 21, 229, 16),   # Goldilocks^3,rho 0.5,  2^21
    "RISC Zero":    (124, 2, 21,  50,  0),   # BabyBear^4,  rho 0.25, 2^21
    "Miden":        (128, 3, 18,  27, 16),   # Goldilocks^2,blowup 8, 2^18
}


def check_all_systems():
    """Every field of every system against its soundcalc .toml. [(sys, field, a, b)]"""
    import systems
    out = []
    for row in systems.SYSTEMS:
        d = systems.as_dict(row)
        src = SOUNDCALC_TOML[d["name"]]
        for i, f in enumerate(("E", "R", "T", "s", "g")):
            out.append((d["name"], f, d[f], src[i]))
    return out


def check_sp1():
    """systems.py's SP1 row against SP1.lean. Returns [(field, canonical, source)]."""
    import systems
    row = next(r for r in systems.SYSTEMS if r[0] == "SP1 6.1.0")
    d = systems.as_dict(row)
    return [("R", d["R"], int(-math.log2(SP1_LEAN["rho"]))),
            ("E", d["E"], SP1_LEAN["field_bits"]),
            ("T", d["T"], SP1_LEAN["denseLen_log"]),
            ("s", d["s"], SP1_LEAN["numQueries"]),
            ("g", d["g"], SP1_LEAN["grindQuery"])]


def check_airbender():
    import systems
    row = next(r for r in systems.SYSTEMS if r[0] == "Airbender")
    d = systems.as_dict(row)
    return [("E", d["E"], AIRBENDER_TOML["field_bits"]),
            ("T", d["T"], AIRBENDER_TOML["trace_log"]),
            ("s", d["s"], AIRBENDER_TOML["num_queries"]),
            ("g", d["g"], AIRBENDER_TOML["grinding_query_phase"])]


def grade_counts():
    out = {}
    for _, grade, _ in PROVENANCE:
        out[grade] = out.get(grade, 0) + 1
    return out


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. TWO SYSTEMS CHECK EXACTLY AGAINST MACHINE-READABLE SOURCES")
    for nm, rows in (("SP1 (SP1.lean)", check_sp1()),
                     ("Airbender (airbender.toml)", check_airbender())):
        print(f"\n  {nm}")
        print(f"  {'field':>8} {'systems.py':>12} {'source':>10} {'match':>8}")
        print("  " + "-" * 42)
        for f, a, b in rows:
            print(f"  {f:>8} {a:>12} {b:>10} {'yes' if a == b else 'NO':>8}")
    total = len(check_sp1()) + len(check_airbender())
    agree = sum(1 for _, a, b in check_sp1() + check_airbender() if a == b)
    print(f"""
  {agree}/{total} checkable parameters agree exactly. Airbender's blowup is not a named
  field in its toml, but iteration 56 reproduced all five of its commit rounds
  exactly at R = 1, which pins it as firmly as a quote would.""")

    sec("2. BUT THE PROVENANCE IS NOT UNIFORM, AND README SAID IT WAS")
    print(f"  {'system':<15} {'grade':<18} basis")
    print("  " + "-" * 76)
    for nm, grade, basis in PROVENANCE:
        print(f"  {nm:<15} {grade:<18} {basis}")
    counts = grade_counts()
    print(f"""
  {counts}

  README describes SOURCES.md as carrying "verbatim upstream quotes for every
  parameter". It carries them for the FORMULAS -- soundcalc's Python, quoted
  thoroughly -- and for each system's reported total. It does not carry them for
  most systems' queries, grinding, trace length and blowup. That is the same
  shape of overstatement iterations 52-54 found in EFFICIENCY.md, in the file
  this repo holds up as its rigorous one.""")

    sec("3. WHY THE EXPOSURE IS NARROWER THAN IT LOOKS")
    print("""
  Every system's REPORTED TOTAL is recorded, and that is what the repo validates
  against. Iteration 56 showed the model reproduces all five JBR totals within
  about a bit at soundcalc's own m. So the conclusions rest on the totals, which
  are recorded, and on the formulas, which are quoted.

  The exposure is specific: if OpenVM's, Pico's or ZisK's queries or grinding
  were transcribed wrongly, the per-system TERM BREAKDOWNS computed from them
  would be wrong while the totals stayed right. Nothing has flagged that, and the
  two systems that can be checked came out exact -- weak positive evidence for
  the transcription generally, not proof of it.""")


def report_all_seven():
    """Iteration 59: cloning soundcalc itself upgrades all seven systems."""
    sec("4. ALL SEVEN SYSTEMS, ALL 35 FIELDS, AGAINST soundcalc's OWN .toml")
    rows = check_all_systems()
    bad = [r for r in rows if r[2] != r[3]]
    print(f"  cloned ethereum/soundcalc; every zkVM ships soundcalc/zkvms/<v>/<v>.toml\n")
    print(f"  {'system':<15} {'E':>5} {'R':>3} {'T':>4} {'s':>5} {'g':>4}   source")
    print("  " + "-" * 74)
    for nm, (E, R, T, s, g) in SOUNDCALC_TOML.items():
        note = {"SP1 6.1.0": "KoalaBear^4, blowup 4",
                "OpenVM 1.5.0": "BabyBear^4, blowup 2",
                "Airbender": "M31^4, rho 0.5",
                "Pico": "KoalaBear^4, blowup 2",
                "ZisK 0.16.1": "Goldilocks^3, rho 0.5",
                "RISC Zero": "BabyBear^4, rho 0.25",
                "Miden": "Goldilocks^2, blowup 8"}[nm]
        print(f"  {nm:<15} {E:>5} {R:>3} {T:>4} {s:>5} {g:>4}   {note}")
    print(f"""
  {len(rows) - len(bad)}/{len(rows)} fields agree with systems.py. {'No mismatches.' if not bad else bad}

  This closes iteration 58's finding rather than merely grading it. Every system
  is now machine-readable, and the three that were "total only" -- OpenVM, Pico,
  ZisK -- verify 5/5 like the rest.

  One inference is also now direct rather than indirect: iteration 56 pinned
  Airbender's blowup at R = 1 by reproducing all five of its commit rounds
  exactly. airbender.toml states rho = 0.5, confirming it outright. The
  reproduction was sound, and it is better to have the field than the inference.""")


if __name__ == "__main__":
    report()
    report_all_seven()
