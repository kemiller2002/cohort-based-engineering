#!/usr/bin/env python3
"""R-EXP-1 / R-EXP-2 planning: sample sizes and cost estimates from VAC-001 and VAC-002 data (design only).

usage: python3 -I plan.py EXPERIMENTS_DIR [OUT.json]

EXPERIMENTS_DIR is research/experiments. Inputs (read-only):
  VAC-001/results/{P1,R1,F1}/analysis.json   cbe.vac-001.metrics/1 arm summaries (K0 sub-agents, lower-bound cost)
  VAC-002/results/P1/analysis.json           per-arm and per-position cost (K1 isolated CLI, cli-estimate)
  VAC-002/results/P1/layer3/summary.json     Layer 3 reviewer cost and items reviewed
  VAC-001/results/decision-dataset.jsonl, VAC-002/results/P1/decision-dataset.jsonl   decisions per unit

Every number is a PLANNING ESTIMATE. The sample-size formula is the one VAC-002 preregistered
(PREREGISTRATION.md section 3): n = (z_{1-a} + z_{1-b})^2 * sum p(1-p) / d^2 * (1 + (m - 1) rho), one-sided,
with Holm's worst case (alpha / k) for a family of k primary contrasts. No trial outcome of R-EXP-1 or R-EXP-2
exists or is used. The script is pure apart from main(): every other function maps inputs to values.
"""
import json
import math
import os
import statistics
import sys
from functools import reduce

NORMAL = statistics.NormalDist()

# ---- fixed design constants (preregistered in the two protocols) ----------------------------------------------

DESIGN = {
    "alpha": 0.05,
    "power": 0.80,
    "rho": 0.05,  # within-chain ICC; VAC-002's default when it cannot be estimated
    "rexp1": {
        "chainLength": 16,
        "unitsPerKindPerChain": 4,  # K-PREM, K-DEC, K-UNDER, K-INV; see r-exp-1-protocol.md section 3
        "arms": ["A", "B", "C", "D", "DR"],
        "primaryContrasts": 6,  # H3: C-B, D-B; H5: D-B, DR-A; H6: C-B, D-B
        "baselineRate": 0.20,  # qualification minimum for the baseline arm (section 4)
        "minimumEffect": 0.15,  # absolute reduction
        "qualificationChains": 2,  # A and B, one chain each
        "maxQualificationRounds": 3,
        "layer3Share": 0.625,  # every decision of the 8 target units (K-PREM, K-DEC) + 25% of the other 8
    },
    "rexp2": {
        "chainLength": 24,
        "thirds": 3,
        "arms": ["A", "B", "D", "BX"],
        "primaryContrasts": 3,  # H2a: B vs A slope; H2b: D vs B slope; Q-C2: BX vs B
        "baselineRate": 0.05,  # VAC-002 floor for an unobserved failure proportion
        "minimumEffect": 0.10,  # rise between the first and the last third
        "pilotChainsPerArm": 1,
        "layer3Share": 0.35,  # 25% seeded sample + every decision of the 2 units after each compaction (approx.)
    },
}


# ---- pure helpers ---------------------------------------------------------------------------------------------

def mean(values):
    return statistics.fmean(values) if values else None


def ols_slope(points):
    """Least-squares slope of y on x for [(x, y)]."""
    xs, ys = [x for x, _ in points], [y for _, y in points]
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in points) / sxx if sxx else None


def z(probability):
    return NORMAL.inv_cdf(probability)


def design_effect(m, rho):
    return 1 + (m - 1) * rho


def units_needed(proportions, d, alpha, power, m, rho):
    """VAC-002 PREREGISTRATION section 3, generalised to a contrast of several independent proportions."""
    variance = sum(p * (1 - p) for p in proportions)
    return math.ceil((z(1 - alpha) + z(power)) ** 2 * variance / d ** 2 * design_effect(m, rho))


def rounded(value, digits=4):
    return None if value is None else round(value, digits)


def read_json(path):
    with open(path) as handle:
        return json.load(handle)


def count_lines(path):
    with open(path) as handle:
        return sum(1 for line in handle if line.strip())


# ---- evidence extraction (pure over loaded documents) -------------------------------------------------------

def vac001_units(analyses):
    """[(arm, unit index, cost)] over every VAC-001 arm summary."""
    return [
        (summary["arm"], unit["unit"], unit["costUsd"])
        for analysis in analyses
        for summary in analysis["arms"]
        for unit in summary["units"]
        if unit.get("costUsd") is not None and not unit.get("excluded")
    ]


def by_arm(rows):
    return reduce(lambda acc, row: {**acc, row[0]: acc.get(row[0], []) + [row[1:]]}, rows, {})


def vac001_costs(analyses):
    grouped = by_arm(vac001_units(analyses))
    return {
        arm: {
            "units": len(rows),
            "meanCostPerUnit": rounded(mean([cost for _, cost in rows])),
            "slopePerIndex": rounded(ols_slope(rows)),
        }
        for arm, rows in sorted(grouped.items())
    }


def vac002_costs(analysis):
    return {
        arm: {
            "units": summary["units"],
            "meanCostPerUnit": rounded(summary["costPerUnit"]),
            "slopePerPosition": rounded(ols_slope([(u["position"], u["costUsdCli"]) for u in summary["perUnit"]])),
            "compactions": summary["compactions"],
        }
        for arm, summary in sorted(analysis["arms"].items())
    }


def layer3_cost(summary):
    return {
        "reviewed": summary["reviewed"],
        "costUsd": rounded(summary["reviewerCostUsdCli"]["total"]),
        "perDecision": rounded(summary["reviewerCostUsdCli"]["total"] / summary["reviewed"]),
    }


# ---- cost model ------------------------------------------------------------------------------------------------

def k1_unit_costs(v1, v2):
    """K1 per-unit cost by arm: VAC-002 where the arm ran in K1; DR scaled from VAC-001's DR/D ratio."""
    dr_ratio = v1["DR"]["meanCostPerUnit"] / v1["D"]["meanCostPerUnit"]
    base = {arm: v2[arm]["meanCostPerUnit"] for arm in ("A", "B", "C", "D")}
    return {**base, "DR": rounded(base["D"] * dr_ratio), "DRoverD": rounded(dr_ratio)}


def chain_mean_cost(intercept_cost, slope, length, reference_length):
    """Mean per-unit cost over a chain of `length`, extrapolated linearly from a chain of `reference_length`."""
    return intercept_cost + slope * ((length + 1) / 2 - (reference_length + 1) / 2)


# ---- R-EXP-1 --------------------------------------------------------------------------------------------------

def rexp1_plan(costs, decisions_per_unit, l3_per_decision):
    d = DESIGN["rexp1"]
    alpha = DESIGN["alpha"] / d["primaryContrasts"]
    p0, p1 = d["baselineRate"], d["baselineRate"] - d["minimumEffect"]
    per_kind = units_needed([p0, p1], d["minimumEffect"], alpha, DESIGN["power"], d["unitsPerKindPerChain"], DESIGN["rho"])
    chains = math.ceil(per_kind / d["unitsPerKindPerChain"])
    cost_per_chain_all_arms = sum(costs[arm] for arm in d["arms"]) * d["chainLength"]
    units = chains * d["chainLength"] * len(d["arms"])
    layer3 = units * d["layer3Share"] * decisions_per_unit * l3_per_decision
    qualification = d["qualificationChains"] * d["chainLength"] * mean([costs["A"], costs["B"]])
    return {
        "alphaPerContrast": rounded(alpha, 5),
        "planningRates": {"baseline": p0, "treatment": rounded(p1)},
        "targetUnitsPerKindPerArm": per_kind,
        "chainsPerArm": chains,
        "unitsTotal": units,
        "modelCostUsd": rounded(chains * cost_per_chain_all_arms, 0),
        "layer3CostUsd": rounded(layer3, 0),
        "qualificationRoundUsd": rounded(qualification, 0),
        "qualificationMaxUsd": rounded(qualification * d["maxQualificationRounds"], 0),
        "sensitivity": {
            f"baseline{p:.2f}": math.ceil(
                units_needed([p, max(p - d["minimumEffect"], 0.01)], d["minimumEffect"], alpha, DESIGN["power"],
                             d["unitsPerKindPerChain"], DESIGN["rho"]) / d["unitsPerKindPerChain"])
            for p in (0.20, 0.30, 0.40)
        },
    }


# ---- R-EXP-2 --------------------------------------------------------------------------------------------------

def rexp2_plan(v2, costs, decisions_per_unit, l3_per_decision, calibration_items):
    d = DESIGN["rexp2"]
    alpha = DESIGN["alpha"] / d["primaryContrasts"]
    per_third = d["chainLength"] // d["thirds"]
    p, rise = d["baselineRate"], d["minimumEffect"]
    # difference in (last third - first third) between two arms: four independent proportions
    units_per_third = units_needed([p, p, p, p + rise], rise, alpha, DESIGN["power"], per_third, DESIGN["rho"])
    chains = math.ceil(units_per_third / per_third)
    reference = 12  # VAC-002 chain length
    unit_cost = {
        "A": costs["A"],
        "B": rounded(chain_mean_cost(costs["B"], v2["B"]["slopePerPosition"], d["chainLength"], reference)),
        "D": rounded(chain_mean_cost(costs["D"], v2["D"]["slopePerPosition"], d["chainLength"], reference)),
        # BX restarts on context pressure: bounded below by B and above by VAC-002's F (restart every 4 units)
        "BX": rounded(chain_mean_cost(v2["F"]["meanCostPerUnit"], v2["F"]["slopePerPosition"], d["chainLength"], reference)),
    }
    per_chain = sum(unit_cost[arm] for arm in d["arms"]) * d["chainLength"]
    units = chains * d["chainLength"] * len(d["arms"])
    return {
        "alphaPerContrast": rounded(alpha, 5),
        "unitsPerThirdPerArm": units_per_third,
        "chainsPerArm": chains,
        "unitsTotal": units,
        "unitCostUsd": unit_cost,
        "pilotUsd": rounded(per_chain * d["pilotChainsPerArm"], 0),
        "modelCostUsd": rounded(chains * per_chain, 0),
        "layer3CostUsdPlaceholder": rounded(units * d["layer3Share"] * decisions_per_unit * l3_per_decision, 0),
        "reviewerCalibrationUsdPlaceholder": rounded(calibration_items * 2 * l3_per_decision, 0),
        "sensitivity": {
            f"chainsIfBaseline{q:.2f}": math.ceil(
                units_needed([q, q, q, q + rise], rise, alpha, DESIGN["power"], per_third, DESIGN["rho"]) / per_third)
            for q in (0.05, 0.10, 0.20)
        },
    }


def plan(experiments):
    v1_docs = [read_json(os.path.join(experiments, "VAC-001", "results", run, "analysis.json")) for run in ("P1", "R1", "F1")]
    v2_doc = read_json(os.path.join(experiments, "VAC-002", "results", "P1", "analysis.json"))
    l3 = layer3_cost(read_json(os.path.join(experiments, "VAC-002", "results", "P1", "layer3", "summary.json")))
    v1, v2 = vac001_costs(v1_docs), vac002_costs(v2_doc)
    decisions = {
        "VAC-001": rounded(count_lines(os.path.join(experiments, "VAC-001", "results", "decision-dataset.jsonl")) / sum(a["units"] for a in v1.values()), 2),
        "VAC-002": rounded(count_lines(os.path.join(experiments, "VAC-002", "results", "P1", "decision-dataset.jsonl")) / sum(a["units"] for a in v2.values()), 2),
    }
    costs = k1_unit_costs(v1, v2)
    per_unit_decisions = max(decisions.values())
    return {
        "schema": "cbe.vac.r-exp-plan/1",
        "label": "PLANNING ESTIMATE; no R-EXP-1 or R-EXP-2 trial has run",
        "design": DESIGN,
        "evidence": {
            "vac001K0LowerBound": v1,
            "vac002K1CliEstimate": v2,
            "layer3SameFamilyVac002": l3,
            "decisionsPerUnit": decisions,
            "k1UnitCostUsed": costs,
        },
        "rexp1": rexp1_plan(costs, per_unit_decisions, l3["perDecision"]),
        "rexp2": rexp2_plan(v2, costs, per_unit_decisions, l3["perDecision"], 202),
    }


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    result = plan(argv[1])
    text = json.dumps(result, indent=2) + "\n"
    if len(argv) > 2:
        with open(argv[2], "w") as handle:
            handle.write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv)
