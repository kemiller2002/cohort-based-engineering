// Static file server that gzips responses (level 6, cached) when the client accepts gzip, approximating a CDN such
// as GitHub Pages. Usage: node static_gzip_server.mjs DIR PORT
import { createServer } from "node:http";
import { readFileSync, statSync } from "node:fs";
import { join, normalize, extname } from "node:path";
import { gzipSync } from "node:zlib";

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".wasm": "application/wasm", ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".dat": "application/octet-stream" };

/** MIME type for a path (pure). */
export const mimeOf = (path) => TYPES[extname(path).toLowerCase()] ?? "application/octet-stream";

/** Resolve a request URL to a file under root, refusing traversal (pure). */
export const resolvePath = (root, url) => {
  const clean = decodeURIComponent(new URL(url, "http://x").pathname);
  const rel = normalize(clean.endsWith("/") ? clean + "index.html" : clean).replace(/^([/\\])+/, "");
  if (rel.startsWith("..")) return null;
  return join(root, rel);
};

const main = () => {
  const [root, port] = process.argv.slice(2);
  const cache = new Map();
  createServer((req, res) => {
    const file = resolvePath(root, req.url);
    try {
      if (!file || !statSync(file).isFile()) throw new Error("nf");
      const accepts = /\bgzip\b/.test(req.headers["accept-encoding"] ?? "");
      const raw = readFileSync(file);
      const body = accepts ? (cache.get(file) ?? cache.set(file, gzipSync(raw, { level: 6 })).get(file)) : raw;
      res.writeHead(200, { "Content-Type": mimeOf(file), "Content-Length": body.length, "Cache-Control": "max-age=600", ...(accepts ? { "Content-Encoding": "gzip" } : {}) });
      res.end(body);
    } catch { res.writeHead(404); res.end("not found"); }
  }).listen(Number(port), "127.0.0.1");
};

if (import.meta.url === `file://${process.argv[1]}`) main();
