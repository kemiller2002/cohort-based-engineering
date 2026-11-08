// Bundle size breakdown of a static site directory: raw, gzip -9 and brotli q11 bytes, per file category.
// Usage: node bundle_sizes.mjs LABEL DIR > out.json
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { createHash } from "node:crypto";
import { gzipSync, brotliCompressSync, constants } from "node:zlib";

/** Category of a published file (pure). Satellite resource folders (cs/, de/, ...) are their own category. */
export const category = (rel) => {
  const parts = rel.split("/");
  if (parts[0] === "_framework" && parts.length === 3 && /^[a-z]{2}(-[A-Za-z]+)?$/.test(parts[1])) return "satellite-resources";
  if (/^_framework\/dotnet\.native\..*\.wasm$/.test(rel)) return "runtime-native-wasm";
  if (/^_framework\/(FSharp\.Core)\./.test(rel)) return "fsharp-core";
  if (/^_framework\/(System\.|Microsoft\.|netstandard|mscorlib)/.test(rel)) return "bcl-assemblies";
  if (/^_framework\/.*\.wasm$/.test(rel)) return "app-assemblies";
  if (/^_framework\/.*\.js$/.test(rel)) return "runtime-js";
  const ext = rel.match(/\.([a-z0-9]+)$/i)?.[1]?.toLowerCase() ?? "none";
  return { css: "css", js: "js", mjs: "js", html: "html", svg: "image", png: "image", json: "json", woff2: "font", woff: "font" }[ext] ?? `other-${ext}`;
};

/** Sum rows of {category, raw, gzip, brotli} into per-category totals plus a grand total (pure). */
export const aggregate = (rows) => {
  const by = {};
  for (const r of rows) {
    const c = (by[r.category] ??= { files: 0, raw: 0, gzip: 0, brotli: 0 });
    c.files += 1; c.raw += r.raw; c.gzip += r.gzip; c.brotli += r.brotli;
  }
  const total = Object.values(by).reduce((t, c) => ({ files: t.files + c.files, raw: t.raw + c.raw, gzip: t.gzip + c.gzip, brotli: t.brotli + c.brotli }), { files: 0, raw: 0, gzip: 0, brotli: 0 });
  return { byCategory: by, total };
};

const walk = (dir) => readdirSync(dir).flatMap((n) => { const p = join(dir, n); return statSync(p).isDirectory() ? walk(p) : [p]; });

const main = () => {
  const [label, dir] = process.argv.slice(2);
  const files = walk(dir).filter((p) => !/\.(br|gz)$/.test(p));
  const rows = files.map((p) => {
    const buf = readFileSync(p); const rel = relative(dir, p).split("\\").join("/");
    return { file: rel, category: category(rel), raw: buf.length, gzip: gzipSync(buf, { level: 9 }).length,
      brotli: brotliCompressSync(buf, { params: { [constants.BROTLI_PARAM_QUALITY]: 11 } }).length,
      sha256: createHash("sha256").update(buf).digest("hex").slice(0, 16) };
  });
  console.log(JSON.stringify({ label, dir, measuredAt: new Date().toISOString(), ...aggregate(rows), files: rows.sort((a, b) => b.raw - a.raw) }, null, 1));
};

if (import.meta.url === `file://${process.argv[1]}`) main();
