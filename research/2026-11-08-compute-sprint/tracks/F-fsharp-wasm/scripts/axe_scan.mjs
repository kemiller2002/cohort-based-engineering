// axe-core WCAG 2.1 A/AA scan of a started WASM app, per hash route and viewport.
// Usage: node axe_scan.mjs OUT.json LABEL BASE_URL MARKER_ATTR AXE_JS ROUTE[,ROUTE...]
//   ROUTE is a hash such as "#/settings" or "" for the landing view. Scans desktop (1280x800) and phone (390x844).
import { writeFileSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";

export const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];
export const VIEWPORTS = { desktop: { width: 1280, height: 800 }, phone: { width: 390, height: 844 } };

/** Compact an axe result to rule-level counts (pure). */
export const summarise = (axe) => ({
  violations: axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help,
    targets: v.nodes.slice(0, 3).map((n) => n.target.join(" ")) })),
  passes: axe.passes.length, incomplete: axe.incomplete.map((v) => v.id), inapplicable: axe.inapplicable.length,
});

/** Distinct violated rule ids across scans with total node counts (pure). */
export const ruleTotals = (scans) => {
  const t = {};
  for (const s of scans) for (const v of s.violations) t[v.id] = (t[v.id] ?? 0) + v.nodes;
  return t;
};

const main = async () => {
  const [out, label, base, marker, axePath, routesArg] = process.argv.slice(2);
  const routes = (routesArg ?? "").split(",");
  const axeSource = readFileSync(axePath, "utf8");
  const { chromium } = createRequire(import.meta.url)("playwright");
  const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const scans = [];
  try {
    for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
      for (const route of routes) {
        const page = await browser.newPage({ viewport });
        await page.goto(base + route);
        let started = true;
        try { await page.waitForFunction((m) => document.documentElement.hasAttribute(m), marker, { timeout: 60000 }); }
        catch { started = false; }
        await page.waitForTimeout(500);
        await page.addScriptTag({ content: axeSource });
        const result = await page.evaluate((tags) => window.axe.run(document, { runOnly: { type: "tag", values: tags } }), TAGS);
        const axeVersion = await page.evaluate(() => window.axe.version);
        scans.push({ route: route || "(landing)", viewport: vpName, started, axeVersion, url: page.url(), ...summarise(result) });
        console.log(label, vpName, route || "(landing)", "violations", result.violations.map((v) => `${v.id}:${v.nodes.length}`).join(" ") || "none");
        await page.close();
      }
    }
  } finally { await browser.close(); }
  writeFileSync(out, JSON.stringify({ label, base, marker, tags: TAGS, measuredAt: new Date().toISOString(), ruleTotals: ruleTotals(scans), scans }, null, 1));
};

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e); process.exit(1); });
