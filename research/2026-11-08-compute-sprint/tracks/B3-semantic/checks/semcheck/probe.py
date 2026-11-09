"""POST HOC (D2): C2 out-of-sample probe. Runs the unchanged C2 rule over every .fs file (bin/obj excluded) of other
Echelon F# source trees, one type environment per tree, and writes ../raw/c2-probe.json. Alarms are listed for manual
adjudication; this is not a false-positive rate on frozen packages."""
import json
import subprocess
import time
from pathlib import Path

from . import carrier

TREES = ("/home/user/ext/causa/src", "/home/user/time-entry-state-machine/f-sharp/src",
         "/home/user/ext/vigila/src", "/home/user/ext/signal/src", "/home/user/ext/strata/src",
         "/home/user/ext/ordo/src")


def head(path):
    try:
        return subprocess.run(["git", "-C", path, "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return None


def main():
    out = []
    for tree in TREES:
        p = Path(tree)
        if not p.is_dir():
            out.append({"tree": tree, "missing": True})
            continue
        t = time.perf_counter()
        files = sorted(f for f in p.rglob("*.fs") if not ({"bin", "obj"} & set(f.parts)))
        defs = tuple(d for f in files for d in carrier.parse_types(f.read_text(errors="replace"), str(f.relative_to(p))))
        alarms, examined = carrier.check(defs)
        out.append({"tree": tree, "head": head(tree), "files": len(files), "types": len(defs),
                    "candidates": len(examined), "alarms": alarms, "seconds": round(time.perf_counter() - t, 3)})
        print(tree, head(tree), "files", len(files), "types", len(defs), "candidates", len(examined), "alarms", len(alarms))
        for a in alarms:
            print("   ", a["candidate"], "|", a["file"], "|", a["reason"][60:220])
    (Path(__file__).resolve().parents[2] / "raw" / "c2-probe.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
