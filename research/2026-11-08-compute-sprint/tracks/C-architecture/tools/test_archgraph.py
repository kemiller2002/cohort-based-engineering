"""Unit tests for archgraph.py (run: python3 -I -m unittest test_archgraph -v from tools/)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import archgraph as ag  # noqa: E402

PROPS = """<Project><ItemGroup>
<PackageVersion Include="FSharp.Core" Version="10.1.401" />
<PackageVersion Include="EchelonFoundry.Aegis.Core" Version="1.0.0" />
<PackageVersion Include="EchelonFoundry.Limen.Store" Version="0.9.0" />
</ItemGroup></Project>"""

NUGET = """<?xml version="1.0"?><configuration><packageSources>
<add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
<add key="echelon-vendor" value="vendor/nuget" /></packageSources></configuration>"""

WORKFLOW = """
# `conditor ci-policy check` enforces these shapes
jobs:
  x:
    steps:
      - name: praxis validate
      - run: ./praxis registry check
      - run: dokimos verification probe --spec x
      - uses: kemiller2002/praxis/.github/actions/setup@v3.25.0
      - run: echo "praxis is the tool"
      - run: for t in conditor praxis ordo dokimos; do audit $t; done
      - run: grep "praxis v3.25.0" notes
"""


class Mapping(unittest.TestCase):
    def test_nuget_system(self):
        self.assertEqual(ag.nuget_package_system("EchelonFoundry.Arca.GitHub"), "arca")
        self.assertIsNone(ag.nuget_package_system("FSharp.Core"))

    def test_npm_system(self):
        self.assertEqual(ag.npm_package_system("@echelon-foundry/print-components"), "folio")
        self.assertIsNone(ag.npm_package_system("ajv"))

    def test_registry_ids(self):
        self.assertEqual(ag.registry_id_system("limen-fsharp"), "limen")
        self.assertEqual(ag.registry_id_system("praxis"), "praxis")

    def test_schema_system(self):
        self.assertEqual(ag.schema_system("echelon.release/v2"), "echelon-registry")
        self.assertEqual(ag.schema_system("dokimos.completion-verification/1"), "dokimos")
        self.assertEqual(ag.schema_system("aegis/boundaries/v1"), "aegis")
        self.assertIsNone(ag.schema_system("echelon.toolchain/1"))


class Parsers(unittest.TestCase):
    def test_props(self):
        items = ag.parse_msbuild_items(PROPS, "PackageVersion")
        self.assertIn(("EchelonFoundry.Aegis.Core", "1.0.0"), items)
        self.assertEqual(len(items), 3)

    def test_props_malformed_falls_back_to_regex(self):
        bad = PROPS.replace("</Project>", "")
        self.assertIn(("EchelonFoundry.Limen.Store", "0.9.0"), ag.parse_msbuild_items(bad, "PackageVersion"))

    def test_conditor(self):
        c = ag.parse_conditor('{"registryAuthority":{"kind":"resolved-release-set","sha256":"ab","path":"x"},'
                              '"components":[{"id":"praxis","version":"3.7.2"}]}')
        self.assertEqual(c["components"], (("praxis", "3.7.2"),))
        self.assertEqual(c["authoritySha256"], "ab")

    def test_conditor_garbage(self):
        self.assertEqual(ag.parse_conditor("not json")["components"], ())

    def test_ros(self):
        self.assertEqual(ag.parse_ros_installed('{"installedVersion":"3.7.2"}'), "3.7.2")
        self.assertIsNone(ag.parse_ros_installed("[]"))

    def test_nuget_sources(self):
        self.assertEqual(ag.parse_nuget_sources(NUGET)[1], ("echelon-vendor", "vendor/nuget"))

    def test_npm_version(self):
        self.assertEqual(ag.version_from_npm_spec(
            "https://github.com/kemiller2002/folio/releases/download/v0.4.1/echelon-foundry-print-components-0.4.1.tgz"),
            "0.4.1")
        self.assertEqual(ag.version_from_npm_spec("^0.9.1"), "0.9.1")
        self.assertIsNone(ag.version_from_npm_spec("workspace:*"))

    def test_cli(self):
        calls = ag.parse_cli_invocations(WORKFLOW)
        self.assertIn(("praxis", "registry"), calls)
        self.assertIn(("dokimos", "verification"), calls)
        self.assertNotIn(("conditor", "ci-policy"), calls, "comment lines are not invocations")
        self.assertNotIn(("praxis", "validate"), calls, "name: lines are not invocations")
        self.assertNotIn(("praxis", "is"), calls)
        self.assertNotIn(("conditor", "praxis"), calls, "tool-name lists are not invocations")
        self.assertFalse(any(sub.startswith("v3") for _, sub in calls), "version strings are not subcommands")

    def test_uses(self):
        self.assertEqual(ag.parse_uses(WORKFLOW), (("praxis", ".github/actions/setup", "v3.25.0"),))

    def test_readme_mentions_word_boundary(self):
        self.assertEqual(ag.readme_mentions("Uses Limen and Forma; formality", ["limen", "forma", "folio"]),
                         ("forma", "limen"))


class PathFilter(unittest.TestCase):
    def test_keep_path(self):
        self.assertTrue(ag.keep_path("src/App/App.fsproj"))
        self.assertFalse(ag.keep_path("tools/x/tests/fixtures/scaffold/package.json"))
        self.assertFalse(ag.keep_path("web/node_modules/a/package.json"))
        self.assertFalse(ag.keep_path("research/experiments/a/package.json"))


class Semver(unittest.TestCase):
    def test_order(self):
        self.assertGreater(ag.semver_key("3.25.0"), ag.semver_key("3.7.2"))
        self.assertGreater(ag.semver_key("0.1.0"), ag.semver_key("0.1.0-preview.1"))

    def test_latest(self):
        self.assertEqual(ag.latest_version(["v3.9.0", "v3.25.0", "baseline-x"]), "3.25.0")
        self.assertEqual(ag.latest_version(["dokimos-v0.9.0", "dokimos-v0.11.1"], "dokimos-v"), "0.11.1")
        self.assertIsNone(ag.latest_version([]))

    def test_skew(self):
        self.assertEqual(ag.skew_class("3.7.2", "3.25.0"), "minor-behind")
        self.assertEqual(ag.skew_class("1.0.0", "1.0.0"), "current")
        self.assertEqual(ag.skew_class("2.0.0", "1.0.0"), "ahead-of-approved-set")
        self.assertEqual(ag.skew_class("0.9.0", "0.9.1"), "patch-behind")
        self.assertEqual(ag.skew_class(None, "1"), "unknown")


class Edges(unittest.TestCase):
    FACTS = {
        "nugetRefs": (("Directory.Packages.props", "EchelonFoundry.Aegis.Core", "1.0.0"),
                      ("Directory.Packages.props", "FSharp.Core", "10.1.401"),
                      ("x.fsproj", "EchelonFoundry.Chrona.Integration", None)),
        "npmRefs": (("package.json", "@echelon-foundry/limen", "0.9.0"),),
        "projectRefs": (("a.fsproj", "../../arca/src/Arca.Core/Arca.Core.fsproj"),),
        "conditor": {"components": (("praxis", "3.7.2"), ("limen-fsharp", "0.9.0")), "authoritySha256": "ab"},
        "authoritySet": "1.2.0",
        "rosInstalled": "3.7.2", "limenConfig": True, "aegisBoundaries": False,
        "schemaRefs": (("x.json", "dokimos.completion-verification/1"),),
        "cliCalls": ((".github/workflows/v.yml", "praxis", "validate"),),
        "usesRefs": (),
        "readmeMentions": ("aegis", "tutela", "chrona"),
    }

    def edges(self):
        return ag.edges_from_facts("chrona", self.FACTS, frozenset({"chrona", "arca", "aegis", "tutela"}))

    def test_types_and_no_self_edges(self):
        es = self.edges()
        self.assertTrue(all(e["type"] in ag.EDGE_TYPES for e in es))
        self.assertFalse(any(e["to"] == "chrona" for e in es))
        self.assertFalse(any(e["to"] is None for e in es))

    def test_third_party_dropped(self):
        self.assertFalse(any("FSharp.Core" in e["via"] for e in self.edges()))

    def test_doc_only_only_when_no_concrete_edge(self):
        doc = {e["to"] for e in self.edges() if e["type"] == "doc-only-claim"}
        self.assertEqual(doc, {"tutela"})

    def test_project_ref(self):
        self.assertIn(("arca", "package-ref"), {(e["to"], e["type"]) for e in self.edges()})

    def test_collapse(self):
        c = ag.collapse_edges(self.edges())
        keys = [(e["from"], e["to"], e["type"]) for e in c]
        self.assertEqual(len(keys), len(set(keys)))
        limen = [e for e in c if e["to"] == "limen" and e["type"] == "contract/schema"][0]
        self.assertEqual(limen["versions"], ["0.9.0"])

    def test_pin_skew(self):
        rows = ag.pin_skew(self.edges(), {"praxis": "3.25.0", "aegis": "1.0.0", "limen": "0.9.1",
                                          "limen-fsharp": "0.9.0"})
        by = {(r["component"], r["via"]): r["skew"] for r in rows}
        self.assertEqual(by[("praxis", "conditor-pin:praxis")], "minor-behind")
        self.assertEqual(by[("aegis", "nuget:EchelonFoundry.Aegis.Core")], "current")
        self.assertEqual(by[("limen", "npm:@echelon-foundry/limen")], "patch-behind")
        self.assertEqual(by[("limen-fsharp", "conditor-pin:limen-fsharp")], "current")

    def test_dot(self):
        dot = ag.to_dot([{"id": "a", "release": "1.0.0"}],
                        [{"from": "a", "to": "b", "type": "package-ref", "versions": ["1.0.0"]}])
        self.assertTrue(dot.startswith("digraph echelon {"))
        self.assertIn('"a" -> "b"', dot)


if __name__ == "__main__":
    unittest.main()
