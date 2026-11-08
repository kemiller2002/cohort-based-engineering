import { test } from "node:test";
import assert from "node:assert/strict";
import { verdict } from "../scripts/limen-probe/run_probe.mjs";

test("verdict reads the DOM snapshot", () => {
  const obs = { diagnostics: [{ kind: "BridgeError" }], dom: { twoA: true, twoB: false, rows: 2, extras: 0, groups: 1, inner: 0 } };
  assert.deepEqual(verdict("two-root-if", obs), { secondRootRendered: false, firstRootRendered: true, reported: true });
  assert.deepEqual(verdict("nested-list", { ...obs, diagnostics: [] }), { innerItemsRendered: 0, groupsRendered: 1, reported: false });
  assert.throws(() => verdict("x", obs));
});
