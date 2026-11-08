import { test } from "node:test";
import assert from "node:assert/strict";
import { mimeOf, resolvePath } from "../scripts/static_gzip_server.mjs";

test("mime and path resolution", () => {
  assert.equal(mimeOf("a/b.wasm"), "application/wasm");
  assert.equal(mimeOf("x.unknown"), "application/octet-stream");
  assert.equal(resolvePath("/r", "/"), "/r/index.html");
  assert.equal(resolvePath("/r", "/_framework/a.js?v=1"), "/r/_framework/a.js");
  assert.equal(resolvePath("/r", "/../etc/passwd"), "/r/etc/passwd");
});
