"""Build claims-ledger.json for Track H. Pure data + light joins against track findings and V1/V2 verdicts.

Usage: python3 -I build_ledger.py <tracks_dir> <out_path>
"""
import json
import os
import sys

TRACKS = sys.argv[1]
OUT = sys.argv[2]

# claimId -> (consequence rank, consequence if wrong, cross-track support ids, publication-use flag)
C = {
    # A economics
    "A-F-01": ("high", "Every cost figure in the sprint and any external cost claim inherits this total.", ["V1:A-F-01"], "cost baseline"),
    "A-F-03": ("high", "Coordinator-context ADR (ADR-S05) and the largest estimated saving rest on it.", ["V1:A-F-03"], "ADR-S05"),
    "A-F-04": ("medium", "Caching strategy and cost-structure statements would be wrong.", [], "outline-2"),
    "A-F-05": ("medium", "Fixed-prefix ~30% share drives the 'governance overhead' narrative; carry model is an ESTIMATE.", ["D:VAC-001 controls", "A:CONSTRUCT-008"], "outline-2"),
    "A-F-06": ("medium", "Rework share is cited for review/fix policy; categories are judgement.", ["B-F-11"], "outline-2"),
    "A-F-07": ("high", "ADR-S02 (.ros out of merge path) scope; the 'no app-code conflicts' half is already contradicted.", ["B-F-09", "V1:A-F-07", "A2:SPR-A2-01"], "ADR-S02"),
    "A-F-08": ("medium", "Dispatch/parallelism investment decisions.", ["V1:A-F-08"], "outline-2"),
    "A-F-09": ("low", "Reread-reduction tooling priority.", [], None),
    "A-F-10": ("medium", "Any duration metric built on Praxis wall_ms.", ["X-22"], "datasets"),
    "A-F-11": ("medium", "Runner capacity decisions.", ["B-F-08"], None),
    "A-F-12": ("high", "Headline '67% of CI minutes wasted' is the most quotable number in the sprint.", ["B-F-08"], "outline-2"),
    "A-F-13": ("high", "A2 CI-cache prototype and the 8% saving estimate.", ["A2 (pending)"], "outline-2"),
    "A-F-14": ("medium", "CI latency statements.", [], None),
    "A-F-16": ("high", "'Process instructions cost more than they save' would change guidance policy; n=3 pilots.", ["G-F-08", "D:VAC-001 controls"], "outline-2"),
    # B forensics
    "B-F-01": ("high", "'No run reached acceptance' is the sprint's top-line readiness statement.", ["G-F-11"], "outline-1"),
    "B-F-02": ("high", "R2 INVALID recomputation underpins the overclaim narrative.", ["G-F-11"], "outline-1"),
    "B-F-03": ("high", "ADR-S04 (mandatory dry run) depends on it; prevalence counts are one analyst's curation.", ["A-F-13", "C-F-12", "B2 (pending)"], "ADR-S04"),
    "B-F-04": ("high", "Overclaim narrative; attribution to computed verdict not established (see X-05).", ["E-F-02", "B-F-16"], "outline-1"),
    "B-F-05": ("medium", "Persistence-as-component recommendation.", [], None),
    "B-F-06": ("medium", "Live-checks-early recommendation; observational.", ["B-F-14"], None),
    "B-F-07": ("high", "Invalidates R5/R6 comparisons; also reproduces an audit verdict of DEVIATION.", [], "outline-1"),
    "B-F-08": ("medium", "Hardened CI template recommendation.", ["A-F-12", "A-F-11"], "outline-2"),
    "B-F-09": ("high", "ADR-002 evidence; conflict counts differ from A2's pre-scan (X-03).", ["A-F-07", "V1:A-F-07"], "ADR-S02"),
    "B-F-11": ("medium", "Review timing policy; no controlled comparison.", ["A-F-06"], None),
    "B-F-12": ("medium", "Owner-readiness preflight recommendation.", ["E-F-07", "E-F-08"], None),
    "B-F-13": ("medium", "Upstream-closure tracking recommendation.", ["C-F-09", "C-F-03"], None),
    "B-F-14": ("medium", "Contradicts the R10 report's own statement; branch metadata only.", ["E-F-16"], None),
    "B-F-16": ("high", "Actions-confirmed R1 overclaim; publishable example if verified.", ["G-F-11"], "outline-1"),
    # C architecture
    "C-F-01": ("high", "35-version skew drives CR-02 and the ecosystem catch-up wave.", ["C-F-02", "E-F-01"], "ADR-S01"),
    "C-F-02": ("high", "Explains why verified completion cannot run in most repos; mapping not re-executed.", ["E-F-01", "G-F-07"], "outline-1"),
    "C-F-03": ("high", "ADR-S01 (signed Registry sets) rests on the dual-catalog/lockstep claim.", ["C-F-18", "B-F-13"], "ADR-S01"),
    "C-F-04": ("high", "ADR-001 assumes the range-qualification path works once a key is trusted; not executed.", [], "ADR-S01"),
    "C-F-05": ("medium", "CR-04 deletion of 1,043 lines; behavioural equivalence not tested.", [], None),
    "C-F-07": ("medium", "'required' components not enforced.", [], None),
    "C-F-08": ("low", "Aegis 2.0.0 unreleased; NuGet not queried directly.", [], None),
    "C-F-09": ("medium", "Corroborates B-F-13 forma-workflow defect.", ["B-F-13"], "ADR-S01"),
    "C-F-12": ("medium", "CR-07 (move Indy-init tooling behind Praxis/Dokimos).", ["E-F-02"], "ADR-S03"),
    "C-F-13": ("high", "Security posture statement; org-level settings invisible.", ["E-F-13", "E-F-10"], None),
    "C-F-14": ("low", "README accuracy.", ["G-F-10"], None),
    "C-F-18": ("medium", "Approval-churn cost argument for ADR-001; owner time not measured.", ["C-F-03"], "ADR-S01"),
    # E security
    "E-F-01": ("high", "'Every complete state is self-declared' is the strongest governance claim in the sprint.", ["G-F-07", "C-F-02"], "outline-1"),
    "E-F-02": ("high", "ADR-S03 (trusted acceptance job) and the 'computed verdict is not independent' conclusion.", ["B-F-04", "C-F-12"], "ADR-S03"),
    "E-F-03": ("medium", "Claim-guard fix.", [], None),
    "E-F-04": ("medium", "Documented limit; server-side verification recommendation.", [], None),
    "E-F-05": ("medium", "'verified' label semantics.", [], None),
    "E-F-06": ("high", "Positive control: attested mode works on 3.25.0. If wrong, ADR-S03 fallback (Dokimos attested) fails.", [], "ADR-S03"),
    "E-F-07": ("high", "If branch protection actually exists via rulesets, several E findings drop in severity; rulesets unreadable.", ["B-F-12"], "ADR-S03"),
    "E-F-08": ("medium", "Owner attestation by review login; not executed.", ["E-F-07"], None),
    "E-F-09": ("medium", "Release attestation scope; not executed (dispatch prohibited).", [], None),
    "E-F-13": ("medium", "No lock files; supply-chain posture.", ["C-F-13"], None),
    "E-F-14": ("high", "'No live credential found' would be dangerous if wrong; heuristic scan; ext/full unscanned.", [], None),
    "E-F-15": ("medium", "'No prompt injection found'; keyword scan only.", [], None),
    "E-F-16": ("low", "causa-acceptance-r10 role.", ["B-F-14"], None),
    # G market
    "G-F-01": ("high", "Rules out a standalone governed-agent-platform product.", [], "outline-3"),
    "G-F-02": ("high", "Defines the narrow defensible claim; Kiro absence from one docs page.", ["E-F-06"], "outline-3"),
    "G-F-03": ("medium", "Cost telemetry is not a wedge.", [], "outline-3"),
    "G-F-04": ("medium", "Problem existence (trust gap); surveys self-selected.", [], "outline-3"),
    "G-F-05": ("medium", "Executive-evidence gap; McKinsey via secondary coverage.", [], "outline-3"),
    "G-F-06": ("high", "Regulatory timing; legal applicability needs counsel; OJ text not fetched.", [], "outline-3"),
    "G-F-07": ("high", "Flagship differentiator not in use; status data as of 2026-10-23.", ["E-F-01", "C-F-02"], "outline-1"),
    "G-F-08": ("high", "'Overhead without measured quality gain'; fixture ceiling effects.", ["A-F-16", "D:VAC-001"], "outline-2"),
    "G-F-12": ("medium", "Platform-dependency positioning; SO 2026 editorial highlights only.", [], "outline-3"),
    "G-F-13": ("low", "Context only; no SAM derived.", [], None),
}

# H-001 notes where a verifier's verdict covers only part of the claim
SCOPE_NOTES = {
    "E-F-07": "V2 verified the VERIFIED parts (protected=false, no rulesets via rules/branches endpoint, no CODEOWNERS). The SUPPORTED part (agent token admin, agent holds signing key) was not re-verified.",
    "E-F-02": "Ledger verifier only. requirements-compiler verify-plan untested by E and V2 (FX-03).",
    "B-F-01": "True but vacuous for 6 of 11 runs that never produced a computed verdict (V2 note). Cite as 'no run reached computed acceptance; 5 produced a non-accepting computed verdict, 6 produced none'.",
    "B-F-02": "Not acceptable is robust; the specific label INVALID is anachronistic (77 of 83 reasons are later-schema absences). Substantive reason ADRP-016 NOT_RUN alone gives INCOMPLETE.",
    "B-F-03": "Holds as 'first refusal that ended the governed verdict'; does NOT hold as 'dominant blocker' for R8 and is doubtful for R9, R10: product and verification incompleteness would independently have prevented acceptance.",
}

# Which verification track is assigned to each source track
ASSIGNED = {"A": "V1", "G": "V1", "B": "V2", "C": "V2", "E": "V2"}


def load_findings(track_dir):
    p = os.path.join(TRACKS, track_dir, "findings.json")
    d = json.load(open(p))
    items = d if isinstance(d, list) else d["findings"]
    return {f["id"]: f for f in items}


def load_verdicts(name):
    for base in (
        f"/home/user/sprint-wt/{name}/research/2026-11-08-compute-sprint/tracks/{name}/verdicts.json",
        os.path.join(TRACKS, name, "verdicts.json"),
    ):
        if os.path.exists(base):
            try:
                d = json.load(open(base))
            except json.JSONDecodeError:
                return {}, base + " (unparseable at read time)"
            items = d if isinstance(d, list) else d.get("verdicts", d.get("claims", []))
            return {v.get("claimId") or v.get("id"): v for v in items}, base
    return {}, None


def load_v1_pending():
    p = "/home/user/sprint-wt/V1-verification/research/2026-11-08-compute-sprint/tracks/V1-verification/CHECKPOINT.md"
    pend = set()
    if os.path.exists(p):
        for line in open(p):
            parts = [x.strip() for x in line.split("|")]
            if len(parts) > 3 and parts[1][:2] in ("A-", "G-", "B-", "C-", "E-") and parts[2] == "pending":
                pend.add(parts[1])
    return pend


findings = {}
for t in ["A-economics", "B-forensics", "C-architecture", "E-security", "G-market"]:
    findings.update(load_findings(t))

v1, v1src = load_verdicts("V1-verification")
v2, v2src = load_verdicts("V2-verification")
v1_pending = load_v1_pending()

entries = []
for cid, (rank, cons, support, use) in C.items():
    f = findings[cid]
    cls = f.get("classification")
    if cls not in ("VERIFIED", "SUPPORTED"):
        raise SystemExit(f"{cid} is {cls}, not VERIFIED/SUPPORTED")
    vt = ASSIGNED[cid[0]]
    vmap = v1 if vt == "V1" else v2
    if cid in vmap:
        v = vmap[cid]
        iv = {"by": vt, "status": "done", "verdict": v.get("verdict"),
              "independence": v.get("independence"),
              "discrepancies": v.get("discrepancies", []),
              "verifierNotes": v.get("notes")}
        if cid in SCOPE_NOTES:
            iv["scopeNote"] = SCOPE_NOTES[cid]
    elif vt == "V1" and cid in v1_pending:
        iv = {"by": vt, "status": "queued", "verdict": None}
    else:
        iv = {"by": None, "status": "not yet independently verified", "verdict": None,
              "assignedTrack": vt, "note": f"not in {vt} verdicts.json or queue at time of build"}
    flags = []
    if iv["status"] != "done":
        flags.append("NOT_YET_INDEPENDENTLY_VERIFIED")
    elif iv["verdict"] not in ("VERIFIED",):
        flags.append("VERIFICATION_FOUND_DISCREPANCY")
    if cls == "SUPPORTED":
        flags.append("SUPPORTED_ONLY")
    meas = f.get("measuredOrEstimate") or f.get("documentedOrInferred") or ""
    if "ESTIMATE" in meas or "inferred" in meas:
        flags.append("CONTAINS_ESTIMATE_OR_INFERENCE")
    if rank == "high" and "NOT_YET_INDEPENDENTLY_VERIFIED" in flags:
        flags.append("PRIORITY_FOR_VERIFICATION")
    entries.append({
        "claimId": cid,
        "track": {"A": "A-economics", "B": "B-forensics", "C": "C-architecture", "E": "E-security", "G": "G-market"}[cid[0]],
        "classification": cls,
        "severity": f.get("severity"),
        "title": f["title"],
        "measuredOrEstimate": meas or None,
        "consequence": rank,
        "consequenceIfWrong": cons,
        "trackLimitations": f.get("limitations"),
        "crossTrackSupport": support,
        "independentVerification": iv,
        "usedIn": use,
        "flags": flags,
        "evidence": f"research/2026-11-08-compute-sprint/tracks/{ {'A':'A-economics','B':'B-forensics','C':'C-architecture','E':'E-security','G':'G-market'}[cid[0]] }/findings.json#{cid}",
    })

omitted = sorted(
    k for k, f in findings.items()
    if f.get("classification") in ("VERIFIED", "SUPPORTED") and k not in C
)

summary = {
    "claims": len(entries),
    "highConsequence": sum(e["consequence"] == "high" for e in entries),
    "independentlyVerifiedDone": sum(e["independentVerification"]["status"] == "done" for e in entries),
    "verifiedClean": sum(e["independentVerification"].get("verdict") == "VERIFIED" for e in entries),
    "verificationDiscrepancy": sum("VERIFICATION_FOUND_DISCREPANCY" in e["flags"] for e in entries),
    "queued": sum(e["independentVerification"]["status"] == "queued" for e in entries),
    "notYetIndependentlyVerified": sum("NOT_YET_INDEPENDENTLY_VERIFIED" in e["flags"] for e in entries),
    "priorityForVerification": [e["claimId"] for e in entries if "PRIORITY_FOR_VERIFICATION" in e["flags"]],
}

other = []
for src, vm in (("V1", v1), ("V2", v2)):
    for k, v in vm.items():
        if k not in C:
            other.append({"id": k, "by": src, "verdict": v.get("verdict"),
                          "trackClassification": findings.get(k, {}).get("classification"),
                          "claimedValue": v.get("claimedValue"),
                          "discrepancies": v.get("discrepancies", []),
                          "verifierNotes": v.get("notes")})

out = {
    "schema": "track-h.claims-ledger/1",
    "track": "H-synthesis",
    "status": "EXPERIMENTAL. A ledger of track claims, not new claims.",
    "asOf": sys.argv[3] if len(sys.argv) > 3 else None,
    "selection": "Every VERIFIED or SUPPORTED finding in A, B, C, E, G whose being wrong would change an ADR, a recommendation, a security posture statement or a candidate public statement. Lower-consequence VERIFIED/SUPPORTED findings are listed under 'omittedLowConsequence'.",
    "verificationSources": {"V1": v1src, "V2": v2src},
    "summary": summary,
    "claims": entries,
    "omittedLowConsequence": omitted,
    "verificationsOutsideLedger": other,
    "notes": [
        "consequence is H-001's judgement of decision impact, not a confidence rating.",
        "A V1/V2 verdict of PARTIALLY VERIFIED means the core number reproduced but part of the statement or its inference did not; read discrepancies before citing.",
        "Track E's VERIFIED means reproduced by Track E in local fixtures; V2 independence is still required for E-F-01/E-F-02 before any external use.",
    ],
}
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1))
print("omitted:", omitted)
