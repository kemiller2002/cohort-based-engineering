#!/usr/bin/env bash
# ARCH-002 F2: build fixtures/summa/repo from Summa at a pinned commit (Worker S).
#   usage: make-snapshot.sh [SUMMA_CLONE] [OUT_DIR]
#   defaults: /home/user/kemiller2002/summa, <this dir>/repo
# The clone is only read (`git archive`); it is never modified. The result is a plain tree
# (no .git): the harness git-initialises its own copy. PROVENANCE.md records what this drops,
# patches and adds, and why.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${1:-/home/user/kemiller2002/summa}"
OUT="${2:-$HERE/repo}"
COMMIT=8b0e93ea7c57934acaa20a7eabd4d67f26efcae4
[ "$(git -C "$SRC" rev-parse "$COMMIT^{commit}")" = "$COMMIT" ] || { echo "commit $COMMIT not in $SRC"; exit 2; }

rm -rf "${OUT:?}"; mkdir -p "$OUT"
git -C "$SRC" archive --format=tar "$COMMIT" | tar -x -C "$OUT"

# 1. Dropped: agent-instruction files and the Praxis/ROS work-protocol tooling and state (Praxis is
#    held out of every arm, as in ARCH-001); the installed SDE doctrine copy (arm B-D material only);
#    agent guidance packs; Node/browser tooling and CI that the F# build and tests do not use.
DROP=(
  AGENTS.md CLAUDE.md GEMINI.md BOOTSTRAP.md HANDOFF.md README.md
  .github .praxis .ros praxis praxis-hub praxis.cmd praxis.ps1 ros ros-hub ros.cmd ros.json ros.ps1
  .sde .visual-engineering .communication-engineering
  docs/00-governance docs/work-protocol.md docs/work-adapter-contract.md docs/work-backlog-guide.md
  docs/remote-agent-contract.md docs/remote-protocol.md docs/agent-provenance.md docs/development-telemetry.md
  docs/ordo-observation.md
  registries schemas telemetry templates
  package.json package-lock.json playwright.config.js tests/browser tests/color-contract.test.mjs
  tools/app_server.mjs tools/http_body.mjs tools/ros_cli.mjs tools/ros_fs_launcher.mjs tools/ros_git.mjs
  tools/ros_hub_cli.mjs tools/ros_hub_server.mjs tools/ros_persistence.mjs tools/ros_server.mjs
  tools/ros_telemetry.mjs tools/web_static.mjs tools/pages deploy
)
for p in "${DROP[@]}"; do [ -e "$OUT/$p" ] || { echo "expected path missing: $p"; exit 2; }; rm -rf "${OUT:?}/$p"; done

# 2. Patched: the eleven F# tests whose subject was dropped are skipped, not deleted (their code stays).
python3 -I - "$OUT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
ROS = "its module reads the Praxis/ROS work queue (.ros/work/queue.json), which is not part of the ARCH-002 snapshot"
SKIP = {
    "tests/Summa.Web.Tests/ArchitectureTests.fs": [
        ("INV-ARCH-005: Praxis governs the engineering", "Praxis/ROS state (.ros, .github, CLAUDE.md) is not part of the ARCH-002 snapshot"),
        ("INV-ARCH-007: Forma presents the editor", "needs node_modules (npm install), which the ARCH-002 snapshot does not have"),
    ],
    "tests/Summa.Web.Tests/FoundationsConformanceTests.fs": [
        ("the npm foundations are pinned to immutable releases and locked", None),
        ("each page takes Forma and Folio from the installed packages", None),
        ("the shared kernel registers Folio and starts Limen from the installed packages", None),
        ("the engine answers the Limen contracts the installed kernel offers", None),
    ],
    "tests/Summa.Tests/GapAnalysisTests.fs": [
        ("every section and requirement family has exactly one row", ROS),
        ("both summaries are the counts of their columns", ROS),
        ("every row that is not yet tested is named by an open work item", ROS),
    ],
    "tests/Summa.Tests/SearchTests.fs": [
        ("SUM4-018: searching thousands of invoices is fast enough", "a 1-second wall-clock bound that fails under parallel trial load (Debug build); nondeterministic"),
    ],
    "tests/Summa.Web.Tests/RoutesTests.fs": [
        ("the committed route inventory is valid against Limen's echelon.routes v1 schema", None),
    ],
}
NPM = "needs node_modules (npm install), which the ARCH-002 snapshot does not have"
for rel, tests in SKIP.items():
    p = root / rel
    lines = p.read_text().split("\n")
    for name, why in tests:
        idx = [i for i, l in enumerate(lines) if l.startswith("let ``" + name)]
        assert len(idx) == 1, (rel, name, idx)
        i = idx[0]
        assert lines[i - 1] == "[<Fact>]", (rel, name, lines[i - 1])
        lines[i - 1] = '[<Fact(Skip = "ARCH-002 snapshot: %s")>]' % (why or NPM)
    p.write_text("\n".join(lines))
PY

# 3. Added: the acceptance test project the harness copies visible tests into (tests/Summa.Acceptance.Tests,
#    compiling Kit.fs then Acceptance/*.fs), registered in Summa.sln.
cp -r "$HERE/snapshot-additions/." "$OUT/"
python3 -I - "$OUT/Summa.sln" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_bytes().decode("utf-8-sig")
guid = "{A7C1D0E2-0002-4F2A-9A55-5A11A0000002}"
assert guid not in s and "\r\n" not in s
proj = ('Project("{F2A71F9B-5D33-465A-A702-920D77279786}") = "Summa.Acceptance.Tests", '
        '"tests\\Summa.Acceptance.Tests\\Summa.Acceptance.Tests.fsproj", "%s"\nEndProject\n' % guid)
i = s.index("Global\n")
s = s[:i] + proj + s[i:]
cfg = "".join("\t\t%s.%s|%s.%s = %s|Any CPU\n" % (guid, c, pl, k, c)
              for c in ("Debug", "Release") for pl in ("Any CPU", "x64", "x86") for k in ("ActiveCfg", "Build.0"))
j = s.index("\tEndGlobalSection\n", s.index("GlobalSection(ProjectConfigurationPlatforms)"))
s = s[:j] + cfg + s[j:]
tests_folder = "{0AB3BF05-4346-4AA6-1389-037BE0695223}"
k = s.index("\tEndGlobalSection\n", s.index("GlobalSection(NestedProjects)"))
s = s[:k] + "\t\t%s = %s\n" % (guid, tests_folder) + s[k:]
p.write_bytes(b"\xef\xbb\xbf" + s.encode("utf-8"))
PY
echo "snapshot of summa@$COMMIT written to $OUT ($(find "$OUT" -type f | wc -l) files, $(du -sh "$OUT" | cut -f1))"
