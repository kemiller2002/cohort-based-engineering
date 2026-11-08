"""Synthetic fixtures only (no Indy-init data): the checks' behaviour on toy machines, invariants and F# types."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from semcheck import carrier, model, partition, rate, slices  # noqa: E402

INV = {"id": "INV-X", "machines": ["SM-T"],
       "statement": "Per job at most two retries; under outage at most three pings in 30 seconds; nothing else."}


def machine(transitions, initial="Idle"):
    return model.load_machines({"machines": [{"id": "SM-T", "initial": initial, "transitions": transitions}]})


def tr(i, s, e, d, g="true", eff=()):
    return {"id": i, "from": s, "event": e, "to": d, "guard": g, "effects": list(eff)}


class Bounds(unittest.TestCase):
    def test_parses_count_and_rate_bounds(self):
        bs = model.parse_bounds(INV)
        self.assertEqual([(b.count, b.head, b.window_s) for b in bs], [(2, "retries", None), (3, "pings", 30.0)])

    def test_conjoined_items_share_window(self):
        bs = model.parse_bounds({"id": "I", "statement": "at most four writes and four reads in 60 seconds"})
        self.assertEqual([(b.count, b.head, b.window_s) for b in bs], [(4, "writes", 60.0), (4, "reads", 60.0)])

    def test_no_at_most_no_bound(self):
        self.assertEqual(model.parse_bounds({"id": "I", "statement": "four pings in 30 seconds happen"}), ())

    def test_pair_table_loader(self):
        ms = model.load_machines({"machines": [{"id": "M", "initial": "A", "pairs": [
            {"state": "A", "event": "e", "outcome": "legal",
             "transitions": [{"id": "T1", "guard": "g", "next": "B", "effects": ["x"]}]},
            {"state": "B", "event": "e", "outcome": "illegal"}]}]})
        self.assertEqual(ms[0].transitions, (model.Transition("T1", "A", "e", "B", "g", ("x",)),))


class Rate(unittest.TestCase):
    def bounds(self):
        return model.parse_bounds(INV)

    def test_unguarded_self_loop_ping_alarms(self):
        m = machine([tr("T1", "Idle", "Fail", "Down"), tr("T2", "Down", "Poke", "Down", "true", ["send one ping"])])
        a = rate.check(m, self.bounds(), ("loop", False))
        self.assertEqual([(x["invariant"], x["transition"]) for x in a], [("INV-X", "T2")])
        self.assertEqual(a[0]["witness"]["prefix"], ["Fail"])
        self.assertEqual(a[0]["witness"]["times"], 4)

    def test_counted_guard_is_bounded(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "fewer than three pings sent in the 30 s before now", ["send one ping"])])
        self.assertEqual(rate.check(m, self.bounds(), ("loop", False)), [])

    def test_budget_guard_not_repeatable(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "pings left", ["schedule the next ping"])])
        self.assertEqual(rate.check(m, self.bounds(), ("loop", False)), [])

    def test_exhausted_guard_still_repeatable(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "automatic pings spent", ["one ping"])])
        self.assertEqual(len(rate.check(m, self.bounds(), ("loop", False))), 1)

    def test_negated_or_cue_less_effect_does_not_emit(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "true", ["send no ping"]),
                     tr("T3", "Idle", "Off", "Idle", "true", ["automatic pings pause"])])
        self.assertEqual(rate.check(m, self.bounds(), ("loop", False)), [])

    def test_slow_loop_respects_window(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "true", ["send one ping after at least 20 s"])])
        self.assertEqual(rate.check(m, self.bounds(), ("loop", False)), [])  # 3 x 20 s >= 30 s

    def test_delegation_variant_accepts_window_in_effects(self):
        m = machine([tr("T2", "Idle", "Poke", "Idle", "true", ["send one ping; the sender keeps the 30 s window"])])
        strict = rate.check(m, self.bounds(), ("loop", False))
        deleg = rate.check(m, self.bounds(), ("loop", True))
        self.assertTrue(strict)
        self.assertEqual([x for x in deleg if x["bound"].endswith("30 s")], [])

    def test_cycle_variant_finds_two_step_loop(self):
        m = machine([tr("T1", "Idle", "Go", "Busy", "true", ["send one ping"]), tr("T2", "Busy", "Back", "Idle")])
        self.assertEqual(rate.check(m, self.bounds(), ("loop", False)), [])
        self.assertEqual({x["cycle"][0] for x in rate.check(m, self.bounds(), ("cycle", False))}, {"T1"})

    def test_machine_scope(self):
        other = model.load_machines({"machines": [{"id": "SM-OTHER", "initial": "A",
                                                   "transitions": [tr("T", "A", "P", "A", "true", ["one ping"])]}]})
        self.assertEqual(rate.check(other, self.bounds(), ("loop", False)), [])


FS_BAD = """namespace X
type ItemId = ItemId of System.Guid
type Version = Version of int64
/// doc comment
type OrderCommand = { CommandId: Guid; Item: ItemId; Expected: Version option }
type Msg =
    | Tick
    | DoCommand of OrderCommand
type Api =
    { Handle: OrderCommand -> Result<unit, string> }
"""
FS_GOOD = FS_BAD.replace("type OrderCommand = { CommandId: Guid; Item: ItemId; Expected: Version option }",
                         "type Body = class end\ntype Cmd =\n    | Create of Body\n    | Cancel of ItemId\n"
                         "type OrderCommand = { CommandId: Guid; Item: ItemId; Expected: Version option; Command: Cmd }")


class Carrier(unittest.TestCase):
    def test_parser(self):
        d = {x.name: x for x in carrier.parse_types(FS_BAD)}
        self.assertEqual(d["OrderCommand"].kind, "record")
        self.assertEqual(d["Msg"].kind, "union")
        self.assertEqual([c for c, _ in d["Msg"].parts], ["Tick", "DoCommand"])
        self.assertEqual(d["ItemId"].kind, "union")

    def test_metadata_only_command_alarms(self):
        alarms, _ = carrier.check(carrier.parse_types(FS_BAD))
        self.assertEqual({a["candidate"] for a in alarms}, {"type OrderCommand", "case Msg.DoCommand"})

    def test_command_with_union_body_passes(self):
        alarms, examined = carrier.check(carrier.parse_types(FS_GOOD))
        self.assertEqual(alarms, [])
        self.assertIn("field OrderCommand.Command", {e["candidate"] for e in examined})

    def test_string_payload_has_no_body(self):
        alarms, _ = carrier.check(carrier.parse_types("type EventPayload = EventPayload of kind: string\n"),
                                  "payload", "C2b")
        self.assertEqual(len(alarms), 1)

    def test_function_and_containers(self):
        env = {}
        self.assertFalse(carrier.has_body("int -> string", env)[0])
        self.assertFalse(carrier.has_body("Guid list", env)[0])
        self.assertTrue(carrier.has_body("Map<string, Foreign>", env)[0])


class Partition(unittest.TestCase):
    def test_missing_exhausted_branch(self):
        m = machine([tr("T1", "Wait", "Fail", "Wait", "fewer than three tries made", ["retry"])])
        self.assertEqual(len(partition.check(m)), 1)

    def test_complete_partition(self):
        m = machine([tr("T1", "Wait", "Fail", "Wait", "limit not reached"),
                     tr("T2", "Wait", "Fail", "Gone", "limit reached")])
        self.assertEqual(partition.check(m), [])


class Slices(unittest.TestCase):
    def test_invariant_source_edge_closes_cycle(self):
        sl = [{"id": "A", "requirements": ["R1"], "dependsOn": [], "acceptanceTests": ["playwright:inv.spec"]},
              {"id": "B", "requirements": ["R2"], "dependsOn": ["A"], "acceptanceTests": []}]
        inv = [{"id": "I1", "sources": ["R2"], "tests": [{"id": "playwright:inv.spec"}]}]
        r = slices.check(sl, inv, True)
        self.assertEqual([c["slices"] for c in r["cycles"]], [["A", "B"]])
        self.assertEqual(r["edgeEvidence"]["A->B"][0]["invariant"], "I1")

    def test_declared_only_acyclic(self):
        sl = [{"id": "A", "dependsOn": []}, {"id": "B", "dependsOn": ["A"]}]
        self.assertEqual(slices.check(sl, [], False)["cycles"], [])


if __name__ == "__main__":
    unittest.main()
