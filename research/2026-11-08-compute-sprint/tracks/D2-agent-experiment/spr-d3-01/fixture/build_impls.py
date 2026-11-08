"""Builds the oracle-validation workspaces fixture/impl/<name>/ from fixture/workspace/ and fixture/impl_src/.
Usage: python3 -I build_impls.py   (deterministic; overwrites fixture/impl/)

reference         = workspace + pricing.py from impl_src/reference.py + impl_src/test_pricing.py
planted_follower  = reference + impl_src/planted_follower.py appended (module-level hooks redefined)
naive_inventor    = reference + impl_src/naive_inventor.py appended
refuser           = reference + impl_src/refuser.py appended
empty             = workspace start state, untouched (pricing.py skeleton)
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
WS, SRC, OUT = (os.path.join(HERE, d) for d in ("workspace", "impl_src", "impl"))
IMPLS = {"reference": [], "planted_follower": ["planted_follower.py"], "naive_inventor": ["naive_inventor.py"],
         "refuser": ["refuser.py"], "empty": None}


def read(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return f.read()


def build(name, overrides):
    dst = os.path.join(OUT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(WS, dst)
    if overrides is not None:
        with open(os.path.join(dst, "pricing.py"), "w", encoding="utf-8") as f:
            f.write("".join([read("reference.py")] + [read(o) for o in overrides]))
    if name == "reference":
        shutil.copy(os.path.join(SRC, "test_pricing.py"), dst)
    return dst


if __name__ == "__main__":
    print("\n".join(build(n, o) for n, o in IMPLS.items()))
