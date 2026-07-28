"""
EFFICIENCY.md's headline number is measured on systems STARKs are not.

EFFICIENCY.md section 1 states:

    "NTT is 90-91% of proof generation latency (ZKProphet, arXiv 2509.22684);
     paired with optimised MSM, NTT accounts for up to 90% of latency."

That figure has since become load-bearing. Iteration 42 used it to price the
random-evaluation-point capacity route at a ~20x prover penalty, which is the
reason that route was ruled out on structural rather than field-size grounds.

So it was worth checking against the source. arXiv serves, unlike eprint's PDFs.

THE SCOPE ERROR
---------------
ZKProphet's abstract, verbatim:

    "Prior work has accelerated ZKPs on GPUs by leveraging the inherent
     parallelism in core computation kernels like Multi-Scalar Multiplication
     (MSM). ... Following massive speedups of MSM, we find that ZKPs are
     bottlenecked by kernels like Number-Theoretic Transform (NTT), as they
     account for up to 90% of the proof generation latency on GPUs WHEN PAIRED
     WITH OPTIMIZED MSM IMPLEMENTATIONS."

MSM is an elliptic-curve operation. It belongs to pairing- and discrete-log-based
systems -- Groth16, PLONK, and their kin. A hash-based STARK has no MSM at all.

So the 90% is measured in a setting where the other dominant kernel is MSM. In a
STARK the other dominant kernel is MERKLE HASHING, which has a completely
different cost profile and no counterpart in ZKProphet's measurement. The
sentence "NTT is 90-91% of proof generation latency" is true of the systems
ZKProphet measured and is not supported, by that citation, for the systems this
repository is about.

EFFICIENCY.md's own wording contains the tell -- "paired with optimised MSM" --
and the number was quoted anyway.

WHAT IT COSTS, WHICH IS LESS THAN IT LOOKS
--------------------------------------------
Iteration 42's penalty is (1 - share) + share * log2(n), from replacing an
O(n log n) NTT with O(n log^2 n) multipoint evaluation. Sweeping the share:

    NTT share    penalty     verdict against a 2x query gain
        90%       20.0x      still a loss
        70%       15.7x      still a loss
        50%       11.5x      still a loss
        30%        7.3x      still a loss
        20%        5.2x      still a loss

The trade flips only when

    (1 - s) + s * log2(n) = 2   =>   s = 1/(log2 n - 1) = 4.8%   at n = 2^22

An FFT-based prover whose FFT is under 5% of its latency does not exist. So
iteration 42's conclusion -- that the random-evaluation route is blocked by
prover cost rather than field size -- survives the whole plausible range, and
survives it by a wide margin.

That is the useful shape of this correction: the CITATION does not support the
number for STARKs, and the CONCLUSION that rested on it does not depend on the
number being right.

WHAT THE HONEST STATEMENT IS
----------------------------
For a hash-based STARK the defensible claim is the ordering, not the percentage:
T_encode (NTT) and T_commit (Merkle hashing) are the two dominant kernels, and
T_open -- the term soundness parameters control -- is small. That ordering is
what EFFICIENCY.md's argument actually uses, and it does not need 90%.

Anywhere a specific NTT share is needed, this file's sweep should be quoted
instead of a point estimate, until someone measures a hash-based STARK prover
directly. ZK-Tracer (arXiv 2605.25493) is about zkVM trace generation and so is
on-target for the front-end claim; it is the NTT share specifically that is
imported from the wrong system class.
"""

import math

ZKPROPHET_SHARE = 0.905      # what EFFICIENCY.md quotes, from an MSM-paired study
LOG2_N = 22


def prover_penalty(ntt_share, log2n=LOG2_N):
    """Replacing O(n log n) NTT with O(n log^2 n) multipoint evaluation."""
    return (1 - ntt_share) + ntt_share * log2n


def flip_share(gain=2.0, log2n=LOG2_N):
    """NTT share at which the penalty equals the query gain."""
    return (gain - 1.0) / (log2n - 1.0)


def sec(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def report():
    sec("1. THE SOURCE MEASURES MSM-PAIRED SYSTEMS; STARKs HAVE NO MSM")
    print("""
  ZKProphet (arXiv 2509.22684), abstract:

    "Following massive speedups of MSM, we find that ZKPs are bottlenecked by
     kernels like Number-Theoretic Transform (NTT), as they account for up to
     90% of the proof generation latency on GPUs WHEN PAIRED WITH OPTIMIZED MSM
     IMPLEMENTATIONS."

  MSM is an elliptic-curve operation belonging to pairing and discrete-log
  systems. A hash-based STARK has none. In a STARK the other dominant kernel is
  MERKLE HASHING, which has no counterpart in that measurement.

  EFFICIENCY.md's own wording carries the tell -- "paired with optimised MSM" --
  and quoted the number anyway.""")

    sec("2. WHAT IT COSTS: THE SWEEP THAT SHOULD HAVE BEEN THERE")
    print(f"  penalty = (1 - share) + share * log2(n),  n = 2^{LOG2_N}\n")
    print(f"  {'NTT share':>11} {'penalty':>9}   verdict against a 2x query gain")
    print("  " + "-" * 60)
    for s in (0.905, 0.70, 0.50, 0.30, 0.20, 0.10):
        p = prover_penalty(s)
        print(f"  {s:>10.0%} {p:>8.1f}x   "
              f"{'still a loss' if p > 2 else 'WOULD FLIP'}")
    fs = flip_share()
    print(f"""
  The trade flips only at share = (2-1)/(log2 n - 1) = {fs:.1%}. An FFT-based
  prover whose FFT is under 5% of its latency does not exist.

  So iteration 42's conclusion -- the random-evaluation capacity route is blocked
  by prover cost, not field size -- survives the entire plausible range by a wide
  margin. The citation does not support the number for STARKs; the conclusion
  that rested on it does not need the number.""")

    sec("3. THE DEFENSIBLE STATEMENT")
    print("""
  For a hash-based STARK the supportable claim is the ORDERING, not a
  percentage: T_encode (NTT) and T_commit (Merkle hashing) are the two dominant
  kernels, and T_open -- the term soundness parameters control -- is small.
  That ordering is what EFFICIENCY.md's argument actually uses, and it does not
  need 90%.

  Where a specific share is required, quote the sweep above rather than a point
  estimate, until someone measures a hash-based STARK prover directly.

  ZK-Tracer (arXiv 2605.25493) is about zkVM trace generation and is on-target
  for the front-end claim. It is the NTT share specifically that was imported
  from the wrong system class.""")


if __name__ == "__main__":
    report()
