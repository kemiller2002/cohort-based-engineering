import { test } from "node:test";
import assert from "node:assert/strict";
import { category, aggregate } from "../scripts/bundle_sizes.mjs";

test("category", () => {
  assert.equal(category("_framework/de/FSharp.Core.resources.wasm"), "satellite-resources");
  assert.equal(category("_framework/zh-Hans/FSharp.Core.resources.wasm"), "satellite-resources");
  assert.equal(category("_framework/dotnet.native.abc.wasm"), "runtime-native-wasm");
  assert.equal(category("_framework/dotnet.native.wasm"), "runtime-native-wasm");
  assert.equal(category("_framework/FSharp.Core.x.wasm"), "fsharp-core");
  assert.equal(category("_framework/System.Text.Json.x.wasm"), "bcl-assemblies");
  assert.equal(category("_framework/Causa.App.x.wasm"), "app-assemblies");
  assert.equal(category("_framework/dotnet.runtime.x.js"), "runtime-js");
  assert.equal(category("limen/index.js"), "js");
  assert.equal(category("forma/all.css"), "css");
  assert.equal(category("README"), "other-none");
});

test("aggregate", () => {
  const a = aggregate([{ category: "css", raw: 10, gzip: 3, brotli: 2 }, { category: "css", raw: 5, gzip: 2, brotli: 1 }, { category: "js", raw: 1, gzip: 1, brotli: 1 }]);
  assert.deepEqual(a.byCategory.css, { files: 2, raw: 15, gzip: 5, brotli: 3 });
  assert.deepEqual(a.total, { files: 3, raw: 16, gzip: 6, brotli: 4 });
});
