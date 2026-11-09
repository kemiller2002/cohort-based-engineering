import { test } from "node:test";
import assert from "node:assert/strict";
import { summarise, ruleTotals } from "../scripts/axe_scan.mjs";

test("summarise and ruleTotals", () => {
  const axe = { violations: [{ id: "color-contrast", impact: "serious", help: "h", nodes: [{ target: ["a"] }, { target: ["b"] }] }], passes: [1, 2], incomplete: [{ id: "x" }], inapplicable: [] };
  const s = summarise(axe);
  assert.equal(s.violations[0].nodes, 2); assert.equal(s.passes, 2); assert.deepEqual(s.incomplete, ["x"]);
  assert.deepEqual(ruleTotals([s, s]), { "color-contrast": 4 });
});
