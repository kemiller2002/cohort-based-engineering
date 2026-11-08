"""Hand-curated UI/WASM/F# defects from rehearsal history, each mapped to the contract that would have caught it.

Run: python3 curated_defects.py OUT.jsonl   (writes the dataset; validation is in validate()).
Every row cites a primary source (git commit or evidence file). 'pattern' groups recurring defect classes.
'contract' names the narrowest mechanism that would have rejected the defect before review, and 'contractExists'
says whether that mechanism already exists in the Echelon stack at the version the rehearsal used.
"""
from __future__ import annotations

import json
import sys

D = [
    # pattern: limen-template-multi-root
    ("R7", "git:indy-init-rehearsal-007 evidence/defects.md D-05", "Evidence template had two root elements; second root (the relate form) silently not rendered",
     "limen-template-multi-root", "Limen binding check: reject a data-if/data-each template whose content has >1 element root (docs/11 already promises a BridgeError; 0.9.0/0.9.1 only check firstElementChild)", "partial-documented-not-enforced"),
    ("causa(R10+)", "git:causa@fda2056", "Details summary: second root inside a data-if template dropped; fixed by one root element",
     "limen-template-multi-root", "same as above", "partial-documented-not-enforced"),
    # pattern: wasm-interpreter-limits
    ("R5", "git:indy-init-rehearsal-005@a0e7d4a; Indy-init docs/engineering-improvement/investigations/wasm.md", "View.project exceeded Mono interpreter 'locals size too big' (12,683 IL locals); page could not start for ~90 min, unit tests on CoreCLR stayed green",
     "wasm-interpreter-limits", "Static IL frame check (tier-0 frame < 65,535 B) as a build/Limen-guest gate + mandatory WASM start smoke", "no"),
    ("R4", "git:indy-init-rehearsal-004@0712465 (D-HIST-WASM)", "Interpreter tier-up trap on Release+debug-info F# IL for Causa.Replay; nine diagnostic iterations",
     "wasm-interpreter-limits", "WASM start+replay smoke on the shipped build; build refuses debug-flavoured assemblies (adopted in R4)", "no"),
    # pattern: wasm-build-flavour-staleness
    ("R4", "git:indy-init-rehearsal-004@5060bc6", "Site publish reused a stale debug-flavoured Causa.Core; CI tested a different engine than deployed",
     "build-provenance", "Build records engine by content digest; deploy asserts tested == shipped (adopted R4)", "no"),
    ("R6", "git:indy-init-rehearsal-006 'Fix the Release build race'", "Release build race between test and site variants sharing bin/obj",
     "build-provenance", "Separate bin/obj per variant; build-info digests", "no"),
    # pattern: state-presentation-not-derived
    ("R3", "git:indy-init-rehearsal-003@d54785c", "State lozenges used a fixed data-state in markup, so different domain states looked identical",
     "state-presentation-not-derived", "Typed view contract: lozenge state is a projected enum bound via data-bind-data-state, never a literal (Percepta state projection + Limen view contract kind check)", "partial-percepta-unreleased"),
    ("R7", "git:indy-init-rehearsal-007 evidence/defects.md D-07", "Loading or refused sessions showed Save and raised the leave guard",
     "state-presentation-not-derived", "Percepta state projection: Save capability visible only in Loaded state; engine-derived 'offered' flags", "partial-percepta-unreleased"),
    # pattern: contrast-and-theme
    ("R4", "git:indy-init-rehearsal-004@e7a0a8e", "Save bar status text: general paragraph colour on navy failed WCAG contrast (found by axe)",
     "contrast-and-theme", "axe color-contrast gate in CI on every screen x viewport; Forma brand compiler contrast gate for custom surfaces", "yes-axe-available"),
    ("R9", "git:indy-init-rehearsal-009@f1e0be7", "a11y fixes: contrast and aria-controls", "contrast-and-theme", "axe gate (color-contrast, aria-valid-attr-value)", "yes-axe-available"),
    ("R10", "git:indy-init-rehearsal-010@e1eb083", "Low-contrast placeholder used as the only branch hint", "contrast-and-theme",
     "Forma text-field contract: hint text is a described-by element, not a placeholder; axe color-contrast", "partial"),
    ("R10", "git:indy-init-rehearsal-010@2370c4e", "OS dark mode switched Forma tokens to dark palette while app painted fixed light surfaces: unreadable labels on deployed site",
     "contrast-and-theme", "Forma theme contract: app must declare data-ef-theme or support both; Playwright emulated dark-scheme contrast check", "no"),
    ("causa(R10+)", "git:causa@0ea1d05", "Badge contrast fix during J1 wiring", "contrast-and-theme", "axe color-contrast gate", "yes-axe-available"),
    ("R1", "git:indy-init-rehearsal-001@433eafc", "Contrast and keyboard fixes for the demo list", "contrast-and-theme", "axe gate + keyboard walk spec", "yes-axe-available"),
    # pattern: focus-management
    ("R2", "indy-init-rehearsal-002/src/kernel/main.js:55", "App hand-wrote focus move/restore for form panels believing Limen cannot manage focus (focus capability pack existed in Limen 0.9.0)",
     "focus-management", "Limen focus capability (data-focus-target) + Percepta focus obligation per transition", "yes-limen-focus-capability"),
    ("causa(R10+)", "git:causa@85ba0ed", "Focus did not move to main region after route change; skip link always visible", "focus-management",
     "Route-change focus obligation (Limen focus capability) + Playwright keyboard spec", "yes-limen-focus-capability"),
    ("causa(R10+)", "git:causa@3ae3ac9", "Choice-card radio focus ring invisible (opacity 0); WebKit ring failed 3:1", "focus-management",
     "Forma choice-card contract: focus ring painted by the input in --ef-color-focus-ring; non-text contrast check (WCAG 1.4.11)", "partial"),
    ("causa(R10+)", "git:causa@56470a8", "WebKit native focus ring on Settings preference control measured 1.04:1", "focus-management",
     "Forma: all interactive controls use Forma focus-ring token; cross-engine focus-visible contrast spec", "partial"),
    # pattern: responsive-target-size
    ("causa(R10+)", "git:causa@7d5527d", "390 px audit: section links and card titles below 44 px targets", "responsive-target-size",
     "Forma target-size contract (44 px) asserted by a Playwright bounding-box check at 390 px", "partial-forma-button-only"),
    ("R10", "git:indy-init-rehearsal-010@7db8be4", "Compact menu lost its summary at phone width (keyboard order the layout kit expects)", "responsive-target-size",
     "Forma navigation-shell contract: compact <details> must keep <summary>; structural lint", "no"),
    ("R3", "git:indy-init-rehearsal-003@96c8175", "Headings took Forma's 14ch/18ch headline measure, wrapping to 2-3 words per line on desktop", "responsive-target-size",
     "Forma component contract: headline measure only inside marketing shell; screenshot/line-count regression test", "no"),
    # pattern: duplicate-or-wrong-structure
    ("R10", "git:indy-init-rehearsal-010@fddd120", "Duplicate 'Investigation sections' navigation in frame and shell", "duplicate-or-wrong-structure",
     "Percepta screen contract: one SecondaryNavigation region per screen; axe landmark-unique", "partial-percepta-unreleased"),
    ("R7", "git:indy-init-rehearsal-007 evidence/defects.md D-06", "MutationObserver loop froze Administration page", "duplicate-or-wrong-structure",
     "Boundary rule: no app-side DOM observers over Limen-bound regions (mechanism-only boundary.js lint)", "no"),
    # pattern: folio-not-integrated
    ("R8", "indy-init-rehearsal-008/evidence/reviews/T30-pre-rc.md", "Folio referenced only by bootstrap print.html; Views/Report.fs was 2 lines at T30", "folio-not-integrated",
     "Folio integration contract: report screen must render inside ef-print-document; build fails if declared capability unused", "no"),
    ("R10", "indy-init-rehearsal-010/web/screens/workspace-report.css; dist/ (sprint build)", "Folio declared and locked but not shipped in dist; report print uses hand-written @media print", "folio-not-integrated",
     "Same as above (declared-capability-used check)", "no"),
    # pattern: test-harness-timing
    ("R3", "git:indy-init-rehearsal-003@2790a6a", "Live suite set token before fieldset was enabled; first projection cleared it (S-4 regression)", "test-harness-timing",
     "App-ready/enabled-state contract exposed to tests (data-*-ready marker + role-based waits)", "partial"),
    ("R5", "git:indy-init-rehearsal-005 'ux.spec.js: default test-site port matches playwright.config.js'", "Spec hard-coded a port different from playwright.config.js", "test-harness-timing",
     "Single source for test origin (baseURL only); pipeline test AR-028 adopted", "no"),
    # pattern: fsharp-build-config
    ("R3", "git:indy-init-rehearsal-003 'Percepta gate: stop Directory.Build.props leaking'", "Repo Directory.Build.props (Nullable, TreatWarningsAsErrors) leaked into nested Percepta build: 36 FS3261 errors; first misdiagnosed as SDK roll-forward",
     "fsharp-build-config", "Nested-tool builds isolated with a stop Directory.Build.props; SDK pin with rollForward disable", "no"),
    ("R10", "CI run 42255415320 (exit 155 sdk-not-found)", "CI job ran before the pinned SDK 10.0.402 was installed", "fsharp-build-config",
     "CI template installs global.json SDK first (adopted in R9/R10)", "no"),
]

FIELDS = ("rehearsal", "source", "defect", "pattern", "contract", "contractExists")


def rows() -> list[dict]:
    return [dict(zip(FIELDS, d), id=f"UD-{i:02d}") for i, d in enumerate(D, 1)]


def validate(rs: list[dict]) -> list[str]:
    problems = [f"{r['id']} missing {k}" for r in rs for k in FIELDS if not r.get(k)]
    problems += [f"{r['id']} source has no locator" for r in rs if not any(t in r["source"] for t in ("git:", "/", "CI run"))]
    return problems


if __name__ == "__main__":
    rs = rows()
    bad = validate(rs)
    if bad:
        raise SystemExit("\n".join(bad))
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rs)
    from collections import Counter
    print(len(rs), "defects;", Counter(r["pattern"] for r in rs).most_common())
