"""SPR-X-03: derive single-component arms from frozen G; assignment; reuse X-02's stratified exact test."""
from __future__ import annotations
import hashlib, json, random, sys
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/spr-x-02/harness")
from x02 import stratified_exact_p  # noqa: E402  (same tested function as X-02)

SEED = 2026110861
G_SHA, M_SHA = "9e6b22568c8045f6695b54ce32d69379988ac9825dc192f02fff1fd2b79ce309", "525d50e1e7c796fe87d4aa095d1f78c77d922cefa1297df7505628ff464b2efd"
FIXTURES = {"D2b": [f"a{i:02d}" for i in range(1, 13)], "D2c": [f"b{i:02d}" for i in range(1, 13)]}

def sha(s: str) -> str: return hashlib.sha256(s.encode()).hexdigest()

def split_g(g: str, m: str) -> tuple[str, str, str]:
    """Pure: return (inserted block, authority section, checklist section) from G = M + block."""
    i = next(k for k in range(len(m)) if m[k] != g[k])
    block = g[i:i + len(g) - len(m)]
    assert g[:i] + g[i + len(block):] == m
    a_start, c_start = block.index("## Authority"), block.index("## Checklist")
    return block, block[a_start:c_start], block[c_start:]

def derive(g: str, m: str) -> dict[str, str]:
    """Pure: C = M + authority section; K = M + checklist section, inserted at G's insertion point."""
    i = next(k for k in range(len(m)) if m[k] != g[k])
    block, auth, chk = split_g(g, m)
    return {"C": m[:i] + auth + m[i:], "K": m[:i] + chk + m[i:]}

def assign(seed: int = SEED) -> list[dict]:
    """Pure: 6C/6K per fixture; 4 batches of 6 (3C+3K), fixtures interleaved (same scheme as X-02)."""
    rng = random.Random(seed)
    per = {fx: rng.sample(ids, len(ids)) for fx, ids in FIXTURES.items()}
    arms = {fx: dict(zip(per[fx], ["C"] * 6 + ["K"] * 6)) for fx in FIXTURES}
    cs = {fx: [r for r in per[fx] if arms[fx][r] == "C"] for fx in FIXTURES}
    ks = {fx: [r for r in per[fx] if arms[fx][r] == "K"] for fx in FIXTURES}
    plan = [((2, 1), (1, 2)), ((1, 2), (2, 1)), ((2, 1), (1, 2)), ((1, 2), (2, 1))]  # (D2b (C,K)), (D2c (C,K)) per batch
    out, used = [], {fx: [0, 0] for fx in FIXTURES}
    for b, pair in enumerate(plan, start=1):
        for fx, (nc, nk) in zip(("D2b", "D2c"), pair):
            c0, k0 = used[fx]
            out += [{"runId": r, "fixture": fx, "arm": "C", "batch": b} for r in cs[fx][c0:c0 + nc]]
            out += [{"runId": r, "fixture": fx, "arm": "K", "batch": b} for r in ks[fx][k0:k0 + nk]]
            used[fx] = [c0 + nc, k0 + nk]
    return out

if __name__ == "__main__":
    base = __file__.rsplit("/", 3)[0] + "/arm-prompts/"
    g, m = open(base + "G.txt").read(), open(base + "M.txt").read()
    assert sha(g) == G_SHA and sha(m) == M_SHA
    if sys.argv[1:] == ["prompts"]:
        for k, v in derive(g, m).items():
            open(__file__.rsplit("/", 2)[0] + f"/arm-prompts/{k}.txt", "w").write(v); print(k, sha(v))
    elif sys.argv[1:] == ["assign"]:
        print(json.dumps({"experiment": "SPR-X-03", "seed": SEED, "model": "haiku", "runs": assign()}, indent=1))
