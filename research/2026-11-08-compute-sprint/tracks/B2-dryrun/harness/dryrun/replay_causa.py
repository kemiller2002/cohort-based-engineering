"""Causa replays: CAUSA-CYCLE (D4) and CAUSA-RULES (D5), on Indy-init at the competition's governing commit."""
import time

from . import checks as c
from . import core

T0 = "2026-11-07T16:10:50Z"
PRE = "dae2347d26d0fb7dccc36484033515bbbaa31675"   # .echelon/r9-governance.json indyInitCommit in causa
LOCK = "kickoff/competition/toolchain.lock.json"
CAUSA = "/home/user/ext/causa"
BOOTSTRAP = "c706816"                                # T0 bootstrap commit in causa (ros.json project id)
FIXED_RULES_REV = "8d63637"                          # proposed ODR-COMP-P17 rules (repository causa-t0)


def _requirement_of(obligation):
    return obligation.rsplit("-O", 1)[0]


def cycle_check(rev):
    t = time.monotonic()
    lock = core.show_json(core.INDY_FULL, rev, LOCK)
    manifest_path = lock["scope"]["manifest"].replace("scope-manifest.json", "slice-execution-manifest.json")
    slices = core.show_json(core.INDY_FULL, rev, manifest_path)["slices"]
    plan_path = f"requirements-compiled/{lock['requirementsPackage'].get('version', 'v4.1.6')}/verification-execution-plan.json" \
        if isinstance(lock.get("requirementsPackage"), dict) and lock["requirementsPackage"].get("version") else \
        "requirements-compiled/v4.1.6/verification-execution-plan.json"
    plan = core.show_json(core.INDY_FULL, rev, plan_path)
    test_obl = {t["id"]: t.get("obligations", []) for s in plan["suites"] for t in s.get("tests", [])}
    obl_req = {o: _requirement_of(o) for os_ in test_obl.values() for o in os_}
    needs = core.show_json(core.INDY_FULL, rev, lock["assertionMergeNeeds"]["path"])["rules"]
    v1 = c.declared_edges(slices)
    v2 = c.merge_edges(v1, c.test_owner_edges(slices, test_obl, obl_req))
    v3 = c.merge_edges(v2, c.assertion_need_edges(slices, needs))
    # Post-hoc diagnostic: V2 restricted to executable tests (praxis:/verifier: record tests bind cross-cutting obligations).
    exec_obl = {k: v for k, v in test_obl.items() if not k.startswith(("praxis:", "verifier:"))}
    v2x = c.merge_edges(v1, c.test_owner_edges(slices, exec_obl, obl_req))
    v3x = c.merge_edges(v2x, c.assertion_need_edges(slices, needs))
    variants = {}
    for name, g in (("V1-declared", v1), ("V2-test-owner", v2), ("V3-assertion-needs", v3),
                    ("V2x-executable-tests-only (post hoc)", v2x), ("V3x-executable-plus-needs (post hoc)", v3x)):
        cycles = c.strongly_connected(g)
        variants[name] = {"edges": sum(len(v) for v in g.values()), "cycles": cycles,
                          "largestCycle": max([len(x) for x in cycles] or [0]),
                          "cycleWithT18andT20": c.cycle_containing(cycles, ["SL-T18", "SL-T20"]),
                          "T18outEdges": sorted(g.get("SL-T18", set())),
                          "T18reachesT20directly": "SL-T20" in g.get("SL-T18", set())}
    t18 = next(s for s in slices if s["id"] == "SL-T18")
    return {"inputs": {"lock": LOCK, "sliceManifest": manifest_path, "plan": plan_path,
                       "assertionNeeds": lock["assertionMergeNeeds"]["path"]},
            "slices": len(slices), "variants": variants,
            "T18": {"dependsOn": t18["dependsOn"],
                    "nonDotnetAcceptanceTests": [a for a in t18["acceptanceTests"] if not a.startswith("dotnet:")],
                    "testOwnerEdges": sorted(v2.get("SL-T18", set()) - v1.get("SL-T18", set()))},
            "seconds": round(time.monotonic() - t, 2)}


def rules_check(indy_rev, rules_path, identities):
    t = time.monotonic()
    rules = core.show_json(core.INDY_FULL, indy_rev, rules_path)
    probs = c.rules_binding_problems(rules.get("repository"), identities)
    return {"rulesPath": rules_path, "rulesRepository": rules.get("repository"), "targetIdentities": identities,
            "problems": probs, "seconds": round(time.monotonic() - t, 3)}


def replay():
    pre = core.commit_info(core.INDY_FULL, PRE)
    lock = core.show_json(core.INDY_FULL, PRE, LOCK)
    repo_name = lock["competitionRepository"]["repo"]
    project_id = core.show_json(CAUSA, BOOTSTRAP, "ros.json")["repository"]["id"]

    cyc = cycle_check(PRE)
    v2r = cyc["variants"]["V2-test-owner"]
    # Mechanism match (protocol: the error must name the historical mechanism): a cycle holding T18 and T20 in which
    # T18 itself has an edge to T20 (T18's acceptance spec needs T20's Connect). A large SCC formed by cross-cutting
    # record tests, with no T18->T20 edge, is recorded as an unrelated alarm, not a catch.
    primary = v2r["cycleWithT18andT20"] if v2r["T18reachesT20directly"] else []
    cycle_rec = {
        "key": "CAUSA-CYCLE", "rehearsal": "Causa", "blocker": "T18<->T20 dependency cycle in the frozen slice plan",
        "trackBEvent": "B-E-124", "t0": T0, "preT0": pre, "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], T0),
        "toolsRun": ["harness D4 cycle check (Tarjan SCC) on slice-execution-manifest + plan + assertion-merge-needs"],
        "check": cyc, "outcome": c.outcome(True, bool(primary)),
        "matchEvidence": ("V2 cycle " + str(primary)) if primary else
        "no variant has an SL-T18->SL-T20 edge (T18's only non-dotnet acceptance test, INV-21.spec.js, binds "
        "obligations of slices other than T20, and its dependence on T20's Connect is not in any pre-T0 artefact); " + "; ".join(
            f"{k}: largest cycle {v['largestCycle']} slices, T18 out-edges {v['T18outEdges']}" for k, v in cyc["variants"].items()),
        "dryRunSeconds": cyc["seconds"]}

    # D5 as preregistered: rules' repository vs the lock's competition repository.
    pre_rules = lock["processEvidence"]["rules"]
    d5 = rules_check(PRE, pre_rules, [repo_name])
    # Post-hoc D5': also accept the Praxis project id the bootstrap records (what verify-process compares).
    d5b = rules_check(PRE, pre_rules, [repo_name, project_id])
    fixed_lock = core.show_json(core.INDY_FULL, FIXED_RULES_REV, "kickoff/competition/toolchain.lock.proposed.json")
    fx = rules_check(FIXED_RULES_REV, fixed_lock["processEvidence"]["rules"], [repo_name])
    fxb = rules_check(FIXED_RULES_REV, fixed_lock["processEvidence"]["rules"], [repo_name, project_id])
    # Negative control: Rehearsal 010's own rules against Rehearsal 010.
    r10 = rules_check("89f5840", "kickoff/rehearsal-010/process-evidence-rules.json", ["indy-init-rehearsal-010"])
    matched = any("indy-init-rehearsal-010" in p for p in d5["problems"])
    rules_rec = {
        "key": "CAUSA-RULES", "rehearsal": "Causa", "blocker": "process-evidence rules bound to indy-init-rehearsal-010",
        "trackBEvent": "B-E-125", "t0": T0, "preT0": pre, "preT0IsBeforeT0": c.is_pre_t0(pre["committerTime"], T0),
        "toolsRun": ["harness D5 rules-binding check on the lock-pinned process-evidence rules"],
        "check": {"preregistered": d5, "postHocWithProjectId": d5b},
        "falsePositiveCheck": {"fixedRev": core.commit_info(core.INDY_FULL, FIXED_RULES_REV),
                               "preregistered": fx, "postHocWithProjectId": fxb, "negativeControlR10": r10},
        "outcome": c.outcome(True, matched),
        "matchEvidence": "; ".join(d5["problems"]),
        "dryRunSeconds": round(d5["seconds"] + d5b["seconds"], 3)}
    return [cycle_rec, rules_rec]
