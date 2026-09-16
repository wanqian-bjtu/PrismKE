/* Synthetic loopback fixture only. No real providers or document decisions. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function main() {
  const base = process.env.PRISMKE_EXECUTION_BROWSER_URL || 'http://127.0.0.1:8006';
  const output = process.env.PRISMKE_EXECUTION_BROWSER_OUTPUT || 'runtime/browser-execution-qa';
  assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname));
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true,
    channel: process.env.PRISMKE_REVIEW_BROWSER_CHANNEL || undefined });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const schema = Buffer.from(JSON.stringify({ schema_id: 'execution-browser', version: '1',
      entity_types: [{ id: 'Software' }, { id: 'Organization' }],
      relations: [{ id: 'developed_by', domain: ['Software'], range: ['Organization'] }] }));
    const created = await page.request.post(`${base}/api/v1/runs`, { multipart: {
      document: { name: 'synthetic.md', mimeType: 'text/markdown',
        buffer: Buffer.from('ExecutionBrowser | developed_by | BrowserOrg | Software | Organization | 0.92\n') },
      schema: { name: 'schema.json', mimeType: 'application/json', buffer: schema }, provider: 'mock',
    } });
    assert.equal(created.status(), 202);
    const runId = (await created.json()).run_id;
    async function execution() {
      return (await page.request.get(`${base}/api/v1/runs/${encodeURIComponent(runId)}/execution`)).json();
    }
    async function settle(predicate) {
      for (let i = 0; i < 300; i++) {
        const value = await execution();
        if (predicate(value)) return value;
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      throw new Error('execution did not reach expected state');
    }
    await settle(value => value.status === 'running');
    assert.equal((await (await page.request.get(`${base}/offline-test/calls`)).json()).calls, 1);
    await page.goto(`${base}/ui/`, { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: '执行任务', exact: true }).click();
    await page.getByRole('button', { name: '刷新任务', exact: true }).click();
    await page.getByRole('button', { name: '安全取消', exact: true }).waitFor();
    await page.waitForFunction(() => [...document.querySelectorAll('button')]
      .some(b => b.textContent.trim() === '安全取消' && !b.disabled));
    await page.screenshot({ path: path.join(output, 'execution-running-desktop.png'), fullPage: true });
    await page.getByRole('textbox', { name: '取消操作者', exact: true }).fill('browser-mock-reviewer');
    await page.getByRole('textbox', { name: '取消原因', exact: true }).fill('synthetic cancellation');
    await page.getByRole('button', { name: '安全取消', exact: true }).click();
    await settle(value => value.status === 'cancelling');
    await page.request.post(`${base}/offline-test/release`);
    await settle(value => value.status === 'cancelled' && value.can_resume);
    await page.getByRole('button', { name: '刷新任务', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('button')]
      .some(b => b.textContent.trim() === '恢复运行' && !b.disabled));
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(output, 'execution-cancelled-mobile.png'), fullPage: true });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
    assert.equal(overflow, false, 'mobile execution page must not overflow');
    await page.getByRole('button', { name: '恢复运行', exact: true }).click();
    const finished = await settle(value => value.status === 'completed');
    assert.equal(finished.attempt, 2);
    assert.equal((await (await page.request.get(`${base}/offline-test/calls`)).json()).calls, 1);
    await page.getByRole('button', { name: '刷新任务', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('button')]
      .some(b => b.textContent.trim() === '安全取消' && b.disabled)
      && [...document.querySelectorAll('button')]
        .some(b => b.textContent.trim() === '恢复运行' && b.disabled));
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.screenshot({ path: path.join(output, 'execution-completed-desktop.png'), fullPage: true });
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'browser-result.json'), JSON.stringify({ passed: true,
      runId, status: finished.status, attempt: finished.attempt, providerCalls: 1,
      pageErrors: errors, mobileOverflow: overflow }, null, 2));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
