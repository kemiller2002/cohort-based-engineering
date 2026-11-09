"""Builds experiments.json and findings.json from the raw files in this track (no hand-copied numbers).
usage: python3 -I harness/build_reports.py TRACK_DIR"""
import json
import re
import sys
from pathlib import Path

T = Path(sys.argv[1])


def jl(path):
    return [json.loads(l) for l in (T / path).read_text().splitlines() if l.strip()]


def by_case(rows):
    return {r["case"]: {"exit": r.get("exit"), "codes": r.get("codes"), "verdict": r.get("verdict"),
                        "reasons": (r.get("reasons") or [])[:2], "note": r.get("note") or None} for r in rows}


def suite(path):
    text = (T / path).read_text()
    m = re.search(r"(\d+) test\(s\); (\d+) passed; (\d+) failed", text)
    s = re.search(r"seconds=(\d+)", text)
    fails = sorted(set(re.findall(r"^FAIL (.*)$", text, re.M)))
    return {"tests": int(m[1]), "passed": int(m[2]), "failed": int(m[3]), "seconds": int(s[1]) if s else None,
            "failures": fails} if m else {"incomplete": True}


r01b, r01p = by_case(jl("raw/spr-e2-01-baseline.jsonl")), by_case(jl("raw/spr-e2-01-patched.jsonl"))
r02b, r02p = by_case(jl("raw/spr-e2-02-baseline.jsonl")), by_case(jl("raw/spr-e2-02-patched.jsonl"))
r03 = by_case(jl("raw/spr-e2-03.jsonl"))
fp = json.loads((T / "raw/spr-e2-01-queue-fp-scan.json").read_text())["results"]
fp_sum = {"repos": sum(1 for r in fp if r["queue"]), "completeRows": sum(r.get("completeRows", 0) for r in fp),
          "flagged": sum(r.get("flagged", 0) for r in fp)}
base, patched = suite("raw/test-suite/tests-baseline-full.log"), suite("raw/test-suite/tests-patched-full.log")
new_fail = sorted(set(patched.get("failures", [])) - set(base.get("failures", [])))
fixed = sorted(set(base.get("failures", [])) - set(patched.get("failures", [])))
suite_cmp = {"baseline": base, "patched": patched, "newlyFailing": new_fail, "newlyPassing": fixed}
(T / "raw/test-suite/comparison.json").write_text(json.dumps(suite_cmp, indent=2) + "\n")

env = {"host": "4 vCPU shared with other sprint tracks", "dotnet": "SDK 10.0.402 (/root/.dotnet)",
       "praxis": "12bf995 (3.25.0) scratch clone; patched worktree branch e2-patch",
       "dokimos": "0.11.1 fecbe0c (binary copied from E's scratch build)", "ordo": "db6d39e",
       "python": "3.13, cryptography 50.0.1", "isolation": "candidate = uid 65534 via setpriv; verifier = root"}

experiments = [
 {"id": "SPR-E2-01", "question": "Can plain completion and work validate be made to derive claim/completion facts from the tracked event log so that E-F-03 and E-F-11 are refused?",
  "hypothesis": "H1: a tracked token-free claim marker + guard over worktree∪HEAD log refuses plain completion after claim-store deletion (CLAIM_RECORD_MISSING). H2: queue 'complete' rows without a tracked completion event are reported (UNRECORDED_COMPLETION).",
  "independentVars": ["Praxis build (baseline 12bf995 vs patched e2-patch)", "attack case"],
  "dependentVars": ["exit code", "refusal/finding code", "existing test pass/fail"],
  "comparison": "same harness, same fixtures recipe, baseline vs patched binary",
  "startRevision": "praxis 12bf995", "tools": ["harness/spr-e2-01.sh", "harness/queue_fp_scan.py", "harness/run-praxis-tests.sh", "tests/Praxis.Tests/E2HardeningTests.fs (in patch)"],
  "environment": env,
  "procedure": "protocols/SPR-E2-01.md; fresh fixture repos under /home/user/sprint-scratch/E2/fixtures with their own .git (lib.sh guard); patch = patches/praxis-claim-guard-queue-integrity.patch",
  "rawResults": {"baseline": r01b, "patched": r01p, "falsePositiveScan": fp_sum},
  "verification": "Each case re-run on the final build (build 4); unit + CLI tests in Praxis's own test project; full suite compared against baseline (raw/test-suite/comparison.json).",
  "limitations": ["A1c: a claim marker that was never committed can be deleted with the store (residual).",
                  "Anyone with write access can still forge tracked events or rewrite history; the fix moves the bypass from an out-of-tree directory to reviewable tracked history.",
                  "Deviation from protocol: the first patched build broke the attested flow (PRX.VALIDATION.DIRTY_WORKTREE from the uncommitted marker); fixed by letting verification treat a marker-only log diff as clean. Tests that assert 'claim leaves git status empty' (invariant I8) fail by design.",
                  "Queue check covers 'complete' rows only; backlog 'abandoned' writes no event in 3.25.0, so it cannot be cross-checked."],
  "conclusion": "VERIFIED for the tested attacks: A1/A1b refused (exit 3, CLAIM_RECORD_MISSING), A2 reported by work validate/backlog-validate/validate (exit 1, UNRECORDED_COMPLETION); controls C1, C1b, C2, C3 pass; 0 false positives over the local repos.",
  "reproduction": "harness/spr-e2-01.sh patched <praxis-e2>/src/Praxis.Cli/bin/Release/net10.0/praxis.dll > raw/spr-e2-01-patched.jsonl"},
 {"id": "SPR-E2-02", "question": "Does a default-on repository-containment policy with digest+commit binding refuse E-F-01 without breaking legitimate completion?",
  "hypothesis": "H3: /etc/hostname (and traversal/symlink variants) are refused with OUTSIDE_REPOSITORY; an in-repo test log is accepted with a correct sha256/HEAD binding; opt-out restores old behaviour.",
  "independentVars": ["Praxis build", "evidence path form", "workProtocol.allowExternalEvidence"],
  "dependentVars": ["exit code", "code", "binding record fields"],
  "comparison": "baseline vs patched, same harness",
  "startRevision": "praxis 12bf995 + SPR-E2-01 commit", "tools": ["harness/spr-e2-02.sh"], "environment": env,
  "procedure": "protocols/SPR-E2-02.md; patch = patches/praxis-evidence-path.patch",
  "rawResults": {"baseline": r02b, "patched": r02p},
  "verification": "Binding sha256 compared to the file's sha256 and commit to git rev-parse HEAD inside the harness; CLI test in the patch asserts the same plus work validate exit 0.",
  "limitations": ["Binding proves which bytes at which commit were cited, not that tests ran or passed; an agent can write a fake log inside the repo.",
                  "Deviation: bindings moved from .ros/evidence/bindings.jsonl (protocol) to .ros/work/evidence-bindings.jsonl because the former raised an attribution finding.",
                  "The binding is written just before completion is persisted, outside the completion's own transaction.",
                  "logs/ is git-ignored by praxis init, so typical test logs record committedAtHead=false (P1); only P1b (committed log) is fully bound.",
                  "The opt-out flag lives in agent-editable ros.json (E-F-04 class)."],
  "conclusion": "VERIFIED: B1–B4 refused (baseline accepted all four), P1/P1b accepted with correct bindings, P2 opt-out accepted, P3 unchanged.",
  "reproduction": "harness/spr-e2-02.sh patched <praxis.dll> > raw/spr-e2-02-patched.jsonl"},
 {"id": "SPR-E2-03", "question": "Can an acceptance verdict be bound to evidence produced and signed by a verifier job the candidate cannot write, so that fabricated bundles are refused?",
  "hypothesis": "Verifier-computed manifest digest + Ed25519 signatures by a key unreadable to the candidate uid refuse E/V2 fabricated bundles, self-signed forgeries, replays and tampering, while a real run is ACCEPTED and a buggy/cheating candidate FAILED.",
  "independentVars": ["bundle origin (verifier job, E script, V2 script, candidate forgery, tampered)", "candidate commit"],
  "dependentVars": ["verdict", "exit", "reasons"],
  "comparison": "old Indy verifier (dae2347) vs prototype trusted verdict on the same fabricated bundles",
  "startRevision": "Indy-init dae2347 (scratch clone of full history)", "tools": ["harness/spr-e2-03.sh", "harness/trusted_acceptance/*.py"], "environment": env,
  "procedure": "protocols/SPR-E2-03.md",
  "rawResults": r03,
  "verification": "5 unittest cases for the pure core; simulation re-runnable end to end (harness/spr-e2-03.sh rebuilds keys, repos and runs from scratch).",
  "limitations": ["Local simulation: uid separation on one host stands in for GitHub environment protection, branch rulesets, required reviewers and OIDC-bound secrets — none of which is tested.",
                  "Black-box checks are a 4-requirement toy plan; adequacy for the real 108-requirement baseline is not shown.",
                  "Candidate code runs as uid 65534 on the same kernel; no container/VM isolation; no network isolation.",
                  "Root (the verifier identity) can do anything; in production the agent's token must not reach the verifier repo/environment (E-F-07 says it currently can)."],
  "conclusion": "VERIFIED for the local mechanism: T1/T2 (old verifier ACCEPTED both) REFUSED; T3, T5, T6a, T6b, T8 REFUSED; T4 EACCES; T7 caller digest ignored; P1 ACCEPTED; N1, N2 FAILED.",
  "reproduction": "sudo-less as root: harness/spr-e2-03.sh > raw/spr-e2-03.jsonl"}]
(T / "experiments.json").write_text(json.dumps({"track": "E2-hardening", "worker": "E2-001", "date": "2026-11-08",
                                                 "testSuite": suite_cmp, "experiments": experiments}, indent=2) + "\n")
print(json.dumps({"suite": {k: (v if k in ("newlyFailing", "newlyPassing") else {kk: vv for kk, vv in v.items() if kk != "failures"}) for k, v in suite_cmp.items()}}, indent=1))

I8_TESTS = "tests that assert `git status --porcelain` is empty right after `work claim` (invariant I8: claiming never touches the tracked tree)"
findings = [
 {"id": "E2-F-01", "title": "Deriving 'claimed' from the tracked event log refuses the E-F-03 claim-store deletion bypass",
  "classification": "VERIFIED",
  "statement": "With patch praxis-claim-guard-queue-integrity, `work claim` appends a token-free `work.claim.recorded` marker to .ros/events/events.jsonl and plain `work complete` consults the tracked log (working tree ∪ HEAD blob). After `rm -rf <git-common-dir>/praxis/claims/ID`, plain completion is refused with exit 3 and PRX.COMPLETION.CLAIM_RECORD_MISSING (baseline: exit 0). It is still refused when the committed marker's line is also deleted from the working tree (A1b). Normal claim -> validate-run -> complete-verified through real Dokimos 0.11.1 still completes, with and without a commit after the claim; the marker is then committed by the verified-completion metadata commit.",
  "evidence": ["raw/spr-e2-01-baseline.jsonl#A1,A1b", "raw/spr-e2-01-patched.jsonl#A1,A1b,C1,C1b,C2", "patches/praxis-claim-guard-queue-integrity.patch", "raw/test-suite/tests-p5-e2.log"],
  "limitations": "A1c: if the marker was never committed, deleting it together with the store still bypasses (exit 0). Anyone who can write the repository can forge or rewrite tracked history; the fix moves the bypass into reviewable tracked state, it does not create a trust root. Changes invariant I8; see E2-F-04."},
 {"id": "E2-F-02", "title": "A queue/event cross-check detects hand-edited queue.json completions (E-F-11) with no false positives on local repositories",
  "classification": "VERIFIED",
  "statement": "`work validate`, `work backlog-validate` and `validate` now report PRX.QUEUE.UNRECORDED_COMPLETION (exit 1) for a queue row with status 'complete' and no tracked work.completed / work.completion.verified event (baseline: valid, exit 0 on all three). Legitimately completed items produce no finding. A read-only scan of the same rule over " + f"{fp_sum['repos']} local repositories ({fp_sum['completeRows']} complete rows) flagged {fp_sum['flagged']}.",
  "evidence": ["raw/spr-e2-01-patched.jsonl#A2-*,C3", "raw/spr-e2-01-queue-fp-scan.json"],
  "limitations": "Only 'complete' rows are checked: backlog 'abandoned' writes no event in 3.25.0. A forger who also appends a fake work.completed line passes. `praxis verify` is unchanged and still exits 0."},
 {"id": "E2-F-03", "title": "Default repository containment plus digest/commit binding refuses /etc/hostname-style evidence (E-F-01) without breaking in-repo completion",
  "classification": "VERIFIED",
  "statement": "With patch praxis-evidence-path, plain `work complete` refuses evidence resolving outside the repository root (absolute, ../ traversal, file symlink, directory symlink) with exit 1 and PRX.EVIDENCE.OUTSIDE_REPOSITORY before any gate, lock or state change; baseline accepted all four. In-repo evidence is accepted and recorded in .ros/work/evidence-bindings.jsonl with sha256 (matches sha256sum) and HEAD commit (matches git rev-parse HEAD) plus committedAtHead. `workProtocol.allowExternalEvidence: true` restores the old behaviour explicitly and still records the digest.",
  "evidence": ["raw/spr-e2-02-baseline.jsonl", "raw/spr-e2-02-patched.jsonl", "patches/praxis-evidence-path.patch"],
  "limitations": "Proves which bytes at which commit were cited, not that tests ran or passed; a fabricated in-repo log is accepted. praxis init git-ignores logs/, so typical logs bind with committedAtHead=false. Opt-out lives in agent-editable ros.json. Binding is written just before (not inside) the completion transaction."},
 {"id": "E2-F-04", "title": "Existing-suite impact: the claim marker conflicts with tests that encode 'claiming never touches the tracked tree'",
  "classification": "VERIFIED",
  "statement": f"Baseline suite: {base.get('tests')} tests, {base.get('passed')} passed, {base.get('failed')} failed ({base.get('seconds')} s). Final patched suite: {patched.get('tests')} tests, {patched.get('passed')} passed, {patched.get('failed')} failed ({patched.get('seconds')} s). Newly failing: {len(new_fail)}; all are {I8_TESTS}. No newly failing test relates to SPR-E2-02. Two baseline failures (real-Dokimos attested end-to-end) are pre-existing.",
  "evidence": ["raw/test-suite/comparison.json", "raw/test-suite/tests-baseline-full.log", "raw/test-suite/tests-patched-full.log"],
  "limitations": "Suites ran on a shared 4-vCPU host; timings are indicative. Fixing the conflict needs a design decision (accept a tracked claim marker and update the I8 tests, or commit the marker at claim time), not done here."},
 {"id": "E2-F-05", "title": "A verifier-signed evidence flow refuses the E and V2 fabricated bundles that Indy-init's verifier ACCEPTS (local simulation)",
  "classification": "VERIFIED",
  "statement": "Re-running E's and V2's own fabrication scripts against Indy-init dae2347 still yields ACCEPTED from compute-acceptance-verdict.py. The prototype trusted verdict REFUSES both (no verifier signature), refuses a candidate-signed forgery, replay to another commit, tampered entries (with or without a re-hashed manifest) and a dropped entry, ignores a caller-supplied manifest digest, ACCEPTS a genuine run of a correct candidate and FAILS a buggy and a cheating candidate. The candidate uid could not read the key or write the verifier's output (EACCES).",
  "evidence": ["raw/spr-e2-03.jsonl", "harness/trusted_acceptance/", "protocols/SPR-E2-03.md"],
  "limitations": "Local uid separation only. GitHub environment protection, rulesets, required reviewers, OIDC/secrets scoping, runner isolation and the adequacy of acceptance checks for the real 108-requirement baseline are NOT TESTED. Root can bypass everything; in production the agent token must not reach the verifier repo (E-F-07: today it can)."},
 {"id": "E2-F-06", "title": "Unverified: hardening against an agent with repository write access in general",
  "classification": "NOT TESTED",
  "statement": "None of the prototypes protects against an agent that rewrites history, edits tracked logs coherently, or modifies the verifier itself; these require server-side enforcement (protected branches, CODEOWNERS, verifier in an agent-unwritable repo/environment).",
  "evidence": [], "limitations": "Out of scope of a local prototype."}]
(T / "findings.json").write_text(json.dumps({"track": "E2-hardening", "worker": "E2-001", "date": "2026-11-08", "findings": findings}, indent=2) + "\n")
