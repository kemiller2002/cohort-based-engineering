// Headless-Chromium startup timing for static WASM app builds.
// Usage: node startup.mjs OUT.jsonl LABEL URL MARKER_ATTR [--reps 5] [--warm] [--throttle 4g]
//   MARKER_ATTR: the <html> data attribute the app sets when its engine is ready (e.g. data-causa-ready).
// Each repetition launches a fresh browser context (empty HTTP cache) unless --warm, in which case a context is
// primed with one untimed load and each timed run is a reload in that context (HTTP cache warm).
import { appendFileSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";

export const THROTTLES = {
  // Chrome DevTools "Fast 4G"-like profile: 9 Mbit/s down, 1.5 Mbit/s up, 60 ms RTT added (bytes/s).
  "4g": { offline: false, latency: 60, downloadThroughput: (9 * 1024 * 1024) / 8, uploadThroughput: (1.5 * 1024 * 1024) / 8 },
};

export const parseArgs = (argv) => {
  const [out, label, url, marker, ...rest] = argv;
  if (!out || !label || !url || !marker) throw new Error("usage: OUT LABEL URL MARKER_ATTR [--reps N] [--warm] [--throttle 4g]");
  const flag = (name) => rest.includes(name);
  const value = (name, dflt) => (rest.includes(name) ? rest[rest.indexOf(name) + 1] : dflt);
  const throttle = value("--throttle", null);
  if (throttle && !THROTTLES[throttle]) throw new Error(`unknown throttle ${throttle}`);
  return { out, label, url, marker, server: value("--server", "python-http"), reps: Number(value("--reps", 5)), warm: flag("--warm"), throttle, timeoutMs: Number(value("--timeout", 60000)) };
};

/** Split "attr" or "attr=value" (pure). */
export const parseMarker = (marker) => {
  const i = marker.indexOf("=");
  return i < 0 ? { attr: marker, value: null } : { attr: marker.slice(0, i), value: marker.slice(i + 1) };
};

// Injected before any page script: records performance.now() when the marker attribute first appears on <html>
// (with the expected value, when one is given).
export const markerInitScript = (marker) => {
  const { attr, value } = parseMarker(marker);
  return `(() => {
  const attr = ${JSON.stringify(attr)}, want = ${JSON.stringify(value)};
  const record = () => { const el = document.documentElement; if (!el || window.__sprintReady || !el.hasAttribute(attr)) return;
    const v = el.getAttribute(attr); if (want === null || v === want) window.__sprintReady = { t: performance.now(), value: v }; };
  new MutationObserver(record).observe(document, { attributes: true, subtree: true, attributeFilter: [attr] });
})();`;
};

/** Reduce raw browser metrics to the row we persist (pure). */
export const toRow = ({ label, rep, mode, throttle, nav, paints, ready, resources, errors }) => {
  const byType = {};
  for (const r of resources) {
    const ext = (new URL(r.name).pathname.match(/\.([a-z0-9]+)$/i)?.[1] ?? "none").toLowerCase();
    byType[ext] = (byType[ext] ?? 0) + (r.encodedBodySize || 0);
  }
  return {
    label, rep, mode, throttle: throttle ?? "none",
    domContentLoadedMs: Math.round(nav.domContentLoadedEventEnd),
    loadMs: Math.round(nav.loadEventEnd),
    firstContentfulPaintMs: paints["first-contentful-paint"] != null ? Math.round(paints["first-contentful-paint"]) : null,
    readyMs: ready ? Math.round(ready.t) : null,
    readyValue: ready ? ready.value : null,
    requests: resources.length + 1,
    transferBytes: resources.reduce((s, r) => s + (r.transferSize || 0), 0) + (nav.transferSize || 0),
    encodedBytesByType: byType,
    pageErrors: errors,
  };
};

const measureOnce = async (context, args, rep, navigate) => {
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e.message).slice(0, 200)));
  if (args.throttle) {
    const cdp = await context.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", THROTTLES[args.throttle]);
  }
  await navigate(page);
  let ready = null;
  try {
    await page.waitForFunction(() => window.__sprintReady, null, { timeout: args.timeoutMs, polling: 50 });
    ready = await page.evaluate(() => window.__sprintReady);
  } catch { errors.push("ready marker timeout"); }
  await page.waitForLoadState("load");
  const metrics = await page.evaluate(() => ({
    nav: performance.getEntriesByType("navigation")[0].toJSON(),
    paints: Object.fromEntries(performance.getEntriesByType("paint").map((p) => [p.name, p.startTime])),
    resources: performance.getEntriesByType("resource").map((r) => ({ name: r.name, transferSize: r.transferSize, encodedBodySize: r.encodedBodySize })),
  }));
  await page.close();
  return toRow({ label: args.label, rep, mode: args.warm ? "warm" : "cold", throttle: args.throttle, ready, errors, ...metrics });
};

const main = async () => {
  const args = parseArgs(process.argv.slice(2));
  const { chromium } = createRequire(import.meta.url)("playwright"); // resolves via NODE_PATH
  const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium", headless: true });
  const version = browser.version();
  const init = markerInitScript(args.marker);
  try {
    let warmContext = null;
    if (args.warm) {
      warmContext = await browser.newContext();
      await warmContext.addInitScript(init);
      const p = await warmContext.newPage(); await p.goto(args.url); await p.waitForTimeout(3000); await p.close();
    }
    for (let rep = 1; rep <= args.reps; rep++) {
      const context = warmContext ?? (await browser.newContext());
      if (!warmContext) await context.addInitScript(init);
      const row = await measureOnce(context, args, rep, (page) => page.goto(args.url));
      const full = { server: args.server, timestampUtc: new Date().toISOString(), loadavg1: Number(readFileSync("/proc/loadavg", "utf8").split(" ")[0]), chromium: version, url: args.url, marker: args.marker, ...row };
      appendFileSync(args.out, JSON.stringify(full) + "\n");
      console.log(args.label, row.mode, row.throttle, rep, "DCL", row.domContentLoadedMs, "ready", row.readyMs, row.readyValue, "errors", row.pageErrors.length);
      if (!warmContext) await context.close();
    }
  } finally { await browser.close(); }
};

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e); process.exit(1); });
