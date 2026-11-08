"""SPR-X-02 assignment and stratified exact permutation analysis. Functional core; tiny I/O shell."""
from __future__ import annotations
import itertools, json, random, sys
from typing import Sequence, Mapping

SEED = 2026110851
FIXTURES = {"D2b": [f"s{i:02d}" for i in range(3, 15)], "D2c": [f"t{i:02d}" for i in range(3, 15)]}  # 12 each

def assign(seed: int = SEED) -> list[dict]:
    """Pure: 6G/6M per fixture; 4 batches of 6 runs each (3G+3M), interleaving fixtures."""
    rng = random.Random(seed)
    per_fx = {fx: list(zip(rng.sample(ids, len(ids)), ["G"] * 6 + ["M"] * 6)) for fx, ids in FIXTURES.items()}
    # balance: each batch takes 3 runs from each fixture with arms 2/1 alternating to total 3G+3M
    def batch_rows(b: int) -> list[dict]:
        rows = []
        for fx in ("D2b", "D2c"):
            g = [r for r in per_fx[fx] if r[1] == "G"]
            m = [r for r in per_fx[fx] if r[1] == "M"]
            ng, nm = ((2, 1) if (b + (fx == "D2c")) % 2 == 0 else (1, 2))
            gi = sum(((2, 1) if (k + (fx == "D2c")) % 2 == 0 else (1, 2))[0] for k in range(b))
            mi = sum(((2, 1) if (k + (fx == "D2c")) % 2 == 0 else (1, 2))[1] for k in range(b))
            rows += [{"runId": r, "fixture": fx, "arm": a, "batch": b + 1} for r, a in g[gi:gi + ng] + m[mi:mi + nm]]
        return rows
    return [row for b in range(4) for row in batch_rows(b)]

def stratified_exact_p(values: Mapping[str, Sequence[tuple[str, float]]]) -> tuple[float, float]:
    """Pure: values[fixture] = [(arm, y)]. Statistic = sum over fixtures of (mean_M - mean_G).
    Exact two-sided p by enumerating all within-fixture relabelings."""
    def stat(lbl: Mapping[str, Sequence[tuple[str, float]]]) -> float:
        def d(rows):
            g = [y for a, y in rows if a == "G"]; m = [y for a, y in rows if a == "M"]
            return sum(m) / len(m) - sum(g) / len(g)
        return sum(d(rows) for rows in lbl.values())
    obs = stat(values)
    per_fx = []
    for fx, rows in values.items():
        ys = [y for _, y in rows]; ng = sum(1 for a, _ in rows if a == "G")
        per_fx.append([[("G" if i in idx else "M", y) for i, y in enumerate(ys)] for idx in map(set, itertools.combinations(range(len(ys)), ng))])
    keys = list(values.keys())
    stats = [stat(dict(zip(keys, combo))) for combo in itertools.product(*per_fx)]
    p = sum(1 for s in stats if abs(s) >= abs(obs) - 1e-12) / len(stats)
    return obs, p

if __name__ == "__main__":
    if sys.argv[1:] == ["assign"]:
        print(json.dumps({"experiment": "SPR-X-02", "seed": SEED, "model": "haiku", "runs": assign()}, indent=1))
