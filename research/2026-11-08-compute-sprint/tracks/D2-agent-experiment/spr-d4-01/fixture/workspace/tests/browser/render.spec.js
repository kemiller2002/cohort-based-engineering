// Acceptance check for R8. Run with: npx playwright test --browser=webkit tests/browser/render.spec.js
const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');

test('invoice renders in WebKit', async ({ page }) => {
  const html = execFileSync('python3', ['-c',
    'import invoice; print(invoice.render_html(["A-1,2,500", "B-2,1,1250"], 10))']).toString();
  await page.setContent(html);
  await expect(page.locator('tr.line')).toHaveCount(2);
  await expect(page.locator('tr.total')).toContainText('$20.25');
  await expect(page.locator('tr.total')).toBeVisible();
});
