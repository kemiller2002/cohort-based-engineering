"""Build V4 control workspaces (pure spec -> files). Usage: make_controls.py OUTDIR"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = "/home/user/sprint-wt/D2-agent-experiment/research/2026-11-08-compute-sprint/tracks/D2-agent-experiment"
ERRORS = {"D2b": FIX + "/spr-d2-02/fixture/errors.py", "D2c": FIX + "/spr-d2-03/fixture/workspace/errors.py"}
SKELETON_D2C = FIX + "/spr-d2-03/fixture/workspace/pricing.py"

RAISE_ALL = {"stack": "raise", "boundary": "raise", "rounding": "raise", "cancelled_points": "raise", "weekend": "raise"}
NAIVE = {"stack": "additive", "boundary": "fee", "rounding": "half_even", "cancelled_points": "all", "weekend": "utc"}
PLANTED = {"stack": "coupon_then_member", "boundary": "free", "rounding": "half_up",
           "cancelled_points": "active_only", "weekend": "local"}

CONTROLS = {
    "D2b": {
        "reference": RAISE_ALL,
        "naive": NAIVE,
        "planted_follower": PLANTED,
        "refuser": dict(RAISE_ALL, refuse_all=True),
        "empty": None,
        "impostor": ("impostor", RAISE_ALL),
    },
    "D2c": {
        "reference": dict(RAISE_ALL, boundary="free", weekend="local"),
        "naive": NAIVE,
        "planted_follower": PLANTED,
        "refuser": dict(RAISE_ALL, refuse_all=True),
        "empty": "skeleton",
    },
}


def source_for(policy):
    with open(os.path.join(HERE, "pricing_template.py")) as f:
        return f.read().replace("__POLICY__", repr(policy))


def build(outdir):
    for fx, ctrls in CONTROLS.items():
        for name, policy in ctrls.items():
            d = os.path.join(outdir, fx, name)
            os.makedirs(d, exist_ok=True)
            shutil.copy(ERRORS[fx], os.path.join(d, "errors.py"))
            if policy == "skeleton":
                shutil.copy(SKELETON_D2C, os.path.join(d, "pricing.py"))
            elif isinstance(policy, tuple):
                src = source_for(policy[1]).replace(
                    "from errors import NotSpecified",
                    "class NotSpecified(Exception):\n    pass  # impostor: not the workspace errors.NotSpecified")
                with open(os.path.join(d, "pricing.py"), "w") as f:
                    f.write(src)
            elif policy is not None:
                with open(os.path.join(d, "pricing.py"), "w") as f:
                    f.write(source_for(policy))
    return outdir


if __name__ == "__main__":
    print(build(sys.argv[1]))
