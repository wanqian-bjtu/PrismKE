/* Synthetic loopback fixture only. No real providers or production decisions. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
  const base = process.env.PRISMKE_CASE_BROWSER_URL || 'http://127.0.0.1:8007';
  const output = process.env.PRISMKE_CASE_BROWSER_OUTPUT || 'runtime/browser-case-reflection-qa';
  assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname));
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    channel: process.env.PRISMKE_REVIEW_BROWSER_CHANNEL || undefined,
  });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    page.on('pageerror', error => errors.push(error.message));
    const schema = Buffer.from(JSON.stringify({
      schema_id: 'case-browser', version: '1',
      entity_types: [{ id: 'Software' }, { id: 'Organization' }],
      relations: [{ id: 'developed_by', domain: ['Software'], range: ['Organization'] }],
    }));
    const created = await page.request.post(`${base}/api/v1/runs`, { multipart: {
      document: { name: 'synthetic.md', mimeType: 'text/markdown', buffer: Buffer.from(
        'PrismKE | unknown_relation | Example Lab | Software | Organization | 0.91\n'),
      },
      schema: { name: 'schema.json', mimeType: 'application/json', buffer: schema },
      provider: 'mock', case_mode: 'good_bad', reflection_enabled: 'true',
      reflection_provider: 'mock', reflection_max_attempts: '2',
      reflection_token_budget: '20000', reflection_time_budget_seconds: '180',
    } });
    assert.equal(created.status(), 202);
    const runId = (await created.json()).run_id;
    for (let i = 0; i < 300; i++) {
      const response = await page.request.get(`${base}/api/v1/runs/${encodeURIComponent(runId)}`);
      const state = await response.json();
      if (state.reflection_attempts?.length) break;
      await new Promise(resolve => setTimeout(resolve, 100));
      if (i === 299) throw new Error('Reflection fixture did not complete');
    }
    await page.goto(`${base}/ui/`, { waitUntil: 'domcontentloaded' });

    await page.getByRole('radio', { name: '案例库', exact: true }).click();
    await page.getByRole('button', { name: '刷新案例', exact: true }).click();
    await page.getByTestId('cell-0-0').getByText('case:browser-good', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, 'cases-desktop.png'), fullPage: true });
    const caseBody = await page.locator('body').innerText();
    assert(!caseBody.includes('vector'), 'case page must not expose embeddings');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Toggle Sidebar', exact: true }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(output, 'cases-mobile.png'), fullPage: true });
    const caseMobileOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth + 2);
    assert.equal(caseMobileOverflow, false, 'mobile case page must not overflow');

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole('button', { name: 'Toggle Sidebar', exact: true }).click();
    await page.waitForTimeout(500);
    await page.getByRole('radio', { name: 'Reflection', exact: true }).click();
    await page.getByLabel('运行', { exact: true }).click();
    await page.getByRole('option').first().click();
    await page.getByRole('button', { name: '查看检索与修复记录', exact: true }).click();
    await page.getByText('rejected_by_validation', { exact: false }).first().waitFor();
    await page.screenshot({ path: path.join(output, 'reflection-desktop.png'), fullPage: true });
    const reflectionBody = await page.locator('body').innerText();
    for (const forbidden of ['Authorization', 'api_key', 'data:image/']) {
      assert(!reflectionBody.includes(forbidden), `Reflection page exposed ${forbidden}`);
    }

    await page.setViewportSize({ width: 820, height: 1180 });
    await page.screenshot({ path: path.join(output, 'reflection-tablet.png'), fullPage: true });
    const tabletOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth + 2);
    assert.equal(tabletOverflow, false, 'tablet Reflection page must not overflow');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Toggle Sidebar', exact: true }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(output, 'reflection-mobile.png'), fullPage: true });
    const reflectionMobileOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth + 2);
    assert.equal(reflectionMobileOverflow, false, 'mobile Reflection page must not overflow');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'browser-result.json'), JSON.stringify({
      passed: true, runId, pageErrors: errors, caseMobileOverflow,
      tabletOverflow, reflectionMobileOverflow,
    }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
