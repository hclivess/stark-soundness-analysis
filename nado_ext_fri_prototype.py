"""
Validated prototype of the GF(p²) FRI fold for NADO.

WHY A PROTOTYPE. The permission classifier denies edits to
/root/nado/execnode/stark/fri.py, and denies configuring that permission. Rather
than route around the denial by shell-writing the file, this implements the same
change as standalone functions against NADO's real modules (field, merkle,
transcript, ext2 -- all already on main), so the design is TESTED before anyone
applies the patch in nado_ext_fri.patch.

Every function below mirrors, line for line, what the patch puts in fri.py.
"""

import sys
sys.path.insert(0, "/root/nado")

# ITERATION 77: NADO removed `ext2` in favour of `extf`, a degree-parameterised
# extension field whose docstring is titled "WHY IT IS DEGREE-PARAMETERISED, NOT
# ext2 + ext3". The rename silently disabled all 26 forgery attacks in
# adversarial.py's PART B for an unknown number of iterations -- the suite kept
# printing "N/N PASS" with the whole block absent. Aliased rather than renamed
# throughout because the API surface is identical (lift/add/sub/mul/scalar_mul);
# the two places that assumed a 2-tuple are now degree-agnostic.
from execnode.stark import field as F, merkle                 # noqa: E402
try:                                                          # noqa: E402
    from execnode.stark import extf as ext2                   # noqa: E402
except ImportError:                                           # pragma: no cover
    from execnode.stark import ext2                           # noqa: E402
from execnode.stark.transcript import Transcript             # noqa: E402
from execnode.stark import backend as _backend               # noqa: E402

INV2 = F.inv(2)


# ------------------------------------------------- the change, as free functions

def fold_ext(evals, dom, alpha):
    """One FRI fold with a GF(p²) challenge.

    Same identity as fri._fold: g(x²) = (f(x)+f(-x))/2 + a*(f(x)-f(-x))/(2x).
    `evals` may be base ints (layer 0) or ext pairs; `dom` is always base-field;
    `alpha` is an ext pair. fe/fo scale by BASE constants (cheap), so only the
    single alpha*fo is a full extension multiply.
    """
    half = len(evals) // 2
    out = [None] * half
    for i in range(half):
        fx, fmx, x = ext2.lift(evals[i]), ext2.lift(evals[i + half]), dom[i]
        fe = ext2.scalar_mul(ext2.add(fx, fmx), INV2)
        fo = ext2.scalar_mul(ext2.sub(fx, fmx), F.mul(INV2, F.inv(x)))
        out[i] = ext2.add(fe, ext2.mul(alpha, fo))
    return out


def ext_leaf(b, v):
    """Leaf digest for a GF(p²) value: node(leaf(a), leaf(b)).

    Uses only existing backend primitives, so BLAKE2b / alghash2 / recursion all
    support ext layers with no new hash opcode.
    """
    limbs = ext2.lift(v)
    h = b.leaf(limbs[0])
    for _x in limbs[1:]:
        h = b.node(h, b.leaf(_x))
    return h


def commit_ext(values, b):
    return merkle.commit_digests([ext_leaf(b, v) for v in values], b)


def coset_interpolate(evals, offset):
    """Base-field coset interpolation (copy of fri._coset_interpolate)."""
    g = F.interpolate(evals)
    inv_off = F.inv(offset)
    scale, coeffs = 1, []
    for gj in g:
        coeffs.append(F.mul(gj, scale))
        scale = F.mul(scale, inv_off)
    return coeffs


def coset_interpolate_ext(evals, offset):
    """Interpolation is F_p-LINEAR and GF(p²) is a rank-2 F_p-module, so the two
    components interpolate separately and re-pair exactly. No extension NTT."""
    a = coset_interpolate([ext2.lift(v)[0] for v in evals], offset)
    c = coset_interpolate([ext2.lift(v)[1] for v in evals], offset)
    return [(a[i], c[i]) for i in range(len(a))]


def expected_layers(N, blowup):
    layers, n = 0, N
    while n > blowup:
        n //= 2
        layers += 1
    return layers


def prove_ext(evals, offset, blowup, num_queries, grind_bits, transcript=None,
              backend=None):
    b = backend or _backend.DEFAULT
    t = transcript or Transcript("fri", backend=b)
    N = len(evals)
    layers, roots = [], []
    cur, off = list(evals), offset
    dom = F.domain(N, off)
    depth = 0
    while len(cur) > blowup:
        is_ext = depth > 0
        root, mlayers = (commit_ext(cur, b) if is_ext else merkle.commit(cur, b))
        roots.append(root); t.absorb(root)
        layers.append({"evals": cur, "mlayers": mlayers, "off": off, "ext": is_ext})
        alpha = t.challenge_ext()
        cur = fold_ext(cur, dom, alpha)
        off = F.mul(off, off)
        dom = F.domain(len(cur), off)
        depth += 1
    final = cur
    t.absorb("final", *ext2.flatten(final))
    pow_nonce = t.grind(grind_bits)

    queries = []
    for _ in range(num_queries):
        idx = t.challenge_index(N)
        steps, a = [], idx
        for L in layers:
            n = len(L["evals"]); half = n // 2
            a %= n
            lo = a % half
            steps.append({"lo": L["evals"][lo],
                          "lo_path": merkle.open_at(L["mlayers"], lo),
                          "hi": L["evals"][lo + half],
                          "hi_path": merkle.open_at(L["mlayers"], lo + half)})
            a = lo
        queries.append({"idx": idx, "steps": steps})

    return {"N": N, "offset": offset, "blowup": blowup, "roots": roots,
            "final": final, "pow": pow_nonce, "queries": queries, "ext": True}


def verify_ext(proof, num_queries, expected_blowup, grind_bits,
               transcript=None, backend=None):
    try:
        N, offset, blowup = proof["N"], proof["offset"], proof["blowup"]
        roots, final, queries = proof["roots"], proof["final"], proof["queries"]
        if not proof.get("ext", False):
            return False, "unexpected FRI challenge field"
        if blowup != expected_blowup:
            return False, "unexpected FRI blowup"
        exp = expected_layers(N, blowup)
        if len(roots) != exp:
            return False, "wrong FRI layer count"
        if len(final) != (N >> exp):
            return False, "wrong FRI final-layer size"
        if len(queries) != num_queries:
            return False, "wrong FRI query count"

        b = backend or _backend.DEFAULT
        t = transcript or Transcript("fri", backend=b)

        alphas, offs, sizes = [], [], []
        off, n = offset, N
        for r in roots:
            t.absorb(r)
            alphas.append(t.challenge_ext())
            offs.append(off); sizes.append(n)
            off = F.mul(off, off); n //= 2
        t.absorb("final", *ext2.flatten(final))
        if not t.check_grind(proof.get("pow"), grind_bits):
            return False, "insufficient proof-of-work (grinding)"

        coeffs = coset_interpolate_ext(final, off)
        deg_bound = max(1, len(final) // blowup)
        if any(c != (0, 0) for c in coeffs[deg_bound:]):
            return False, "final layer is not low-degree"

        for q in queries:
            idx = t.challenge_index(N)
            if idx != q["idx"]:
                return False, "query index does not match transcript"
            a = idx
            for L, (root, alpha, step) in enumerate(zip(roots, alphas, q["steps"])):
                n = sizes[L]; half = n // 2
                a %= n
                lo = a % half
                if L > 0:
                    if not merkle.verify_digest(root, lo, ext_leaf(b, step["lo"]),
                                                step["lo_path"], b):
                        return False, f"bad Merkle opening (lo) at layer {L}"
                    if not merkle.verify_digest(root, lo + half,
                                                ext_leaf(b, step["hi"]),
                                                step["hi_path"], b):
                        return False, f"bad Merkle opening (hi) at layer {L}"
                else:
                    if not merkle.verify(root, lo, step["lo"], step["lo_path"], b):
                        return False, f"bad Merkle opening (lo) at layer {L}"
                    if not merkle.verify(root, lo + half, step["hi"],
                                         step["hi_path"], b):
                        return False, f"bad Merkle opening (hi) at layer {L}"
                x = F.mul(offs[L], F.pw(F.primitive_root_of_unity(n), lo))
                flo, fhi = ext2.lift(step["lo"]), ext2.lift(step["hi"])
                fe = ext2.scalar_mul(ext2.add(flo, fhi), INV2)
                fo = ext2.scalar_mul(ext2.sub(flo, fhi), F.mul(INV2, F.inv(x)))
                folded = ext2.add(fe, ext2.mul(alpha, fo))
                if L + 1 < len(roots):
                    nxt = q["steps"][L + 1]
                    nhalf = sizes[L + 1] // 2
                    expected_v = nxt["lo"] if lo < nhalf else nxt["hi"]
                    if ext2.lift(expected_v) != folded:
                        return False, f"fold inconsistency at layer {L}"
                else:
                    if ext2.lift(final[lo]) != folded:
                        return False, f"fold does not match final layer at layer {L}"
                a = lo
        return True, "ok"
    except Exception as e:
        return False, f"malformed proof: {e}"


# ------------------------------------------------------------------- tests

def _lde(coeffs, N, offset):
    """Evaluate a base-field polynomial on the size-N coset."""
    dom = F.domain(N, offset)
    return [F.poly_eval(coeffs, x) for x in dom]


def run():
    import random
    random.seed(11)
    B, NQ, G = 2, 12, 4           # small blowup/query/grind so the test is quick
    N, OFF = 64, F.GENERATOR
    deg = N // B
    ok_all = True

    def check(name, cond):
        nonlocal ok_all
        ok_all = ok_all and cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    print("=" * 74)
    print("EXT-FRI PROTOTYPE  (GF(p^2) folding challenge, NADO modules)")
    print("=" * 74)

    coeffs = [random.randrange(F.P) for _ in range(deg)]
    evals = _lde(coeffs, N, OFF)

    pr = prove_ext(evals, OFF, B, NQ, G)
    ok, why = verify_ext(pr, NQ, B, G)
    check(f"honest low-degree proof verifies ({why})", ok)

    check("layers past 0 are GF(p^2)-valued",
          all(type(v) is tuple for v in pr["final"]))
    check("proof declares ext=True", pr["ext"] is True)

    # a HIGH-degree polynomial must be rejected
    hi = [random.randrange(F.P) for _ in range(N)]
    pr2 = prove_ext(_lde(hi, N, OFF), OFF, B, NQ, G)
    ok2, why2 = verify_ext(pr2, NQ, B, G)
    check(f"high-degree input rejected ({why2})", not ok2)

    # tamper with an opened value
    import copy
    bad = copy.deepcopy(pr)
    bad["queries"][0]["steps"][0]["lo"] = (bad["queries"][0]["steps"][0]["lo"] + 1) % F.P
    ok3, why3 = verify_ext(bad, NQ, B, G)
    check(f"tampered opening rejected ({why3})", not ok3)

    # tamper with the final layer
    bad2 = copy.deepcopy(pr)
    _lim = list(bad2["final"][0])
    _lim[0] = (_lim[0] + 1) % F.P
    bad2["final"][0] = tuple(_lim)
    ok4, why4 = verify_ext(bad2, NQ, B, G)
    check(f"tampered final layer rejected ({why4})", not ok4)

    # a proof that declares base-field must be refused (the pinning check)
    bad3 = copy.deepcopy(pr); bad3["ext"] = False
    ok5, why5 = verify_ext(bad3, NQ, B, G)
    check(f"base-field declaration refused ({why5})", not ok5)

    # dropped queries
    bad4 = copy.deepcopy(pr); bad4["queries"] = bad4["queries"][:3]
    ok6, why6 = verify_ext(bad4, NQ, B, G)
    check(f"dropped queries rejected ({why6})", not ok6)

    # componentwise interpolation identity
    vals = [(random.randrange(F.P), random.randrange(F.P)) for _ in range(16)]
    ce = coset_interpolate_ext(vals, OFF)
    ca = coset_interpolate([v[0] for v in vals], OFF)
    cb = coset_interpolate([v[1] for v in vals], OFF)
    check("ext coset interpolation == componentwise base interpolation",
          ce == [(ca[i], cb[i]) for i in range(len(ca))])

    # the fold is F_p-linear in the evaluations, so a base-field alpha embedded in
    # GF(p^2) must reproduce the ORIGINAL base fold exactly
    from execnode.stark import fri as nado_fri
    dom = F.domain(N, OFF)
    al = random.randrange(F.P)
    base_fold = nado_fri._fold(evals, dom, al)
    ext_fold = fold_ext(evals, dom, (al, 0))
    check("fold_ext with a base alpha reproduces fri._fold",
          [ext2.lift(v) for v in ext_fold] == [(v, 0) for v in base_fold])

    print("=" * 74)
    print("ALL PASS" if ok_all else "FAILURES ABOVE")
    print("=" * 74)
    return ok_all


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
