// Runs probe.html cases in headless Chromium and prints JSON observations.
// Usage: node run_probe.mjs BASE_URL   (BASE_URL serves probe.html next to limen/ = the package's dist/)
import { createRequire } from "node:module";

export const CASES = ["two-root-if", "two-root-each", "nested-list"];

/** What the DOM shows for each case (pure over the observed snapshot). */
export const verdict = (kase, obs) => {
  const reported = obs.diagnostics.some((d) => d.kind === "BridgeError");
  switch (kase) {
    case "two-root-if": return { secondRootRendered: obs.dom.twoB, firstRootRendered: obs.dom.twoA, reported };
    case "two-root-each": return { rowsRendered: obs.dom.rows, extraRootsRendered: obs.dom.extras, reported };
    case "nested-list": return { innerItemsRendered: obs.dom.inner, groupsRendered: obs.dom.groups, reported };
    default: throw new Error(kase);
  }
};

const main = async () => {
  const base = process.argv[2];
  const { chromium } = createRequire(import.meta.url)("playwright");
  const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const out = [];
  for (const kase of CASES) {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`${base}/probe.html?case=${kase}`);
    await page.waitForFunction(() => window.__probe?.done, null, { timeout: 10000 }).catch(() => {});
    const obs = await page.evaluate(() => ({
      status: window.__probe?.status, diagnostics: window.__probe?.diagnostics ?? [],
      dom: { twoA: !!document.getElementById("two-a"), twoB: !!document.getElementById("two-b"),
        rows: document.querySelectorAll("#list .row").length, extras: document.querySelectorAll("#list .row-extra").length,
        groups: document.querySelectorAll("#nested .group").length, inner: document.querySelectorAll("#nested .inner-item").length },
    }));
    out.push({ case: kase, status: obs.status, pageErrors: errors, diagnostics: obs.diagnostics.slice(0, 5), verdict: verdict(kase, obs) });
    await page.close();
  }
  await browser.close();
  console.log(JSON.stringify(out, null, 1));
};

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e); process.exit(1); });
