import { test } from "node:test";
import assert from "node:assert/strict";
import { parseArgs, toRow, markerInitScript } from "../scripts/startup.mjs";

test("parseArgs defaults and flags", () => {
  const a = parseArgs(["o.jsonl", "r10", "http://x/", "data-ready"]);
  assert.equal(a.reps, 5); assert.equal(a.warm, false); assert.equal(a.throttle, null);
  const b = parseArgs(["o", "l", "u", "m", "--reps", "7", "--warm", "--throttle", "4g"]);
  assert.equal(b.reps, 7); assert.equal(b.warm, true); assert.equal(b.throttle, "4g");
  assert.throws(() => parseArgs(["o", "l"]));
  assert.throws(() => parseArgs(["o", "l", "u", "m", "--throttle", "3g"]));
});

test("toRow aggregates bytes by extension", () => {
  const row = toRow({
    label: "x", rep: 1, mode: "cold", throttle: null,
    nav: { domContentLoadedEventEnd: 10.4, loadEventEnd: 20.6, transferSize: 100 },
    paints: { "first-contentful-paint": 12.2 }, ready: { t: 99.5, value: "running" },
    resources: [{ name: "http://h/a.wasm", transferSize: 50, encodedBodySize: 40 }, { name: "http://h/b.wasm?v=1", transferSize: 5, encodedBodySize: 4 }, { name: "http://h/x", transferSize: 1, encodedBodySize: 1 }],
    errors: [],
  });
  assert.equal(row.domContentLoadedMs, 10); assert.equal(row.loadMs, 21); assert.equal(row.readyMs, 100);
  assert.deepEqual(row.encodedBytesByType, { wasm: 44, none: 1 });
  assert.equal(row.transferBytes, 156); assert.equal(row.requests, 4); assert.equal(row.throttle, "none");
});

test("marker script mentions the attribute", () => {
  assert.match(markerInitScript("data-causa-ready"), /data-causa-ready/);
});
