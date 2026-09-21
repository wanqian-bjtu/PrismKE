/* Offline UI lifecycle test. Never submit decisions to the real document workspace. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function dropdown(page, label, index = 0) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      await page.getByRole('combobox', { name: label, exact: true }).click();
      const option = page.getByRole('option').nth(index);
      await option.waitFor({ state: 'visible' });
      await option.click({ force: true });
      return;
    } catch (error) {
      if (attempt === 2) throw error;
      await page.waitForTimeout(250);
    }
  }
}

async function main() {
  const url = process.env.PRISMKE_REVIEW_BROWSER_URL || 'http://127.0.0.1:8002/ui';
  const readonly = process.env.PRISMKE_REVIEW_BROWSER_READONLY === '1';
  const output = process.env.PRISMKE_REVIEW_BROWSER_OUTPUT || 'runtime/browser-review-qa';
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true, channel: process.env.PRISMKE_REVIEW_BROWSER_CHANNEL || undefined,
  });
  try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.getByRole('radio', { name: '实体审核', exact: true }).click();
  await dropdown(page, '运行');
  await page.getByRole('textbox', { name: '审核进度', exact: true }).waitFor();
  await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
    .some(e => e.value.includes('实体待审核')));
  await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
    .some(e => e.value.includes('候选差距')));
  await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
    .some(e => e.value.includes('页码：')));
  await page.screenshot({ path: path.join(output, 'entity-desktop.png'), fullPage: true });
  assert(await page.getByRole('textbox', { name: '提及与关联事实', exact: true }).inputValue());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(output, 'entity-mobile.png'), fullPage: true });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
  assert.equal(overflow, false, 'mobile page must not overflow horizontally');
  await page.setViewportSize({ width: 1440, height: 1000 });
  if (!readonly) {
    await page.getByRole('textbox', { name: '审核人', exact: true }).fill('browser-mock-reviewer');
    await page.getByText('创建新实体', { exact: true }).click();
    await page.getByRole('button', { name: '提交当前审核', exact: true }).click();
    await page.getByRole('button', { name: '继续处理', exact: true }).waitFor({ state: 'visible' });
    await page.getByRole('button', { name: '继续处理', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.includes('事实待审核 2')));
    if (process.env.PRISMKE_REVIEW_BROWSER_VALIDATION === '1') {
      await page.getByRole('radio', { name: '校验问题', exact: true }).click();
      await dropdown(page, '校验运行');
      await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
        .some(e => e.value.includes('阻断问题 1')));
      await page.getByRole('button', { name: '排除候选', exact: true }).waitFor();
      await page.waitForFunction(() => [...document.querySelectorAll('button')]
        .some(e => e.textContent.trim() === '排除候选' && !e.disabled));
      await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
        .some(e => e.value.includes('页码：') && e.value.includes('PrismKE')));
      await page.screenshot({ path: path.join(output, 'validation-desktop.png'), fullPage: true });
      await page.setViewportSize({ width: 390, height: 844 });
      await page.screenshot({ path: path.join(output, 'validation-mobile.png'), fullPage: true });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.getByRole('textbox', { name: '校验审核人', exact: true }).fill('browser-mock-reviewer');
      await page.getByRole('checkbox', { name: '确认排除此候选，保留原始问题及审计', exact: true }).check();
      await page.getByRole('button', { name: '排除候选', exact: true }).click();
      await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
        .some(e => e.value.includes('阻断问题 0')));
    }
    await page.getByRole('radio', { name: '事实审核', exact: true }).click();
    await dropdown(page, '运行');
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.includes('OpenAI') && e.value.includes('developed_by')));
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .filter(e => e.value.includes('页码：')).length >= 2);
    await page.screenshot({ path: path.join(output, 'conflict-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(output, 'conflict-mobile.png'), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.getByRole('textbox', { name: '审核人', exact: true }).fill('browser-mock-reviewer');
    await page.getByText('批准事实', { exact: true }).click();
    await page.getByRole('button', { name: '提交当前审核', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.includes('事实待审核 1')));
    await page.getByText('拒绝事实', { exact: true }).click();
    await page.getByRole('textbox', { name: '审核意见', exact: true }).fill('synthetic conflict rejected');
    await page.getByRole('button', { name: '提交当前审核', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.includes('事实待审核 0')));
    await page.getByRole('button', { name: '继续处理', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.includes('prepare_graph_commit'))
      && [...document.querySelectorAll('button')].some(e =>
        e.textContent.trim() === '确认写入隔离图谱' && !e.disabled));
    await page.getByRole('checkbox', { name: '确认将预览内容写入隔离图谱', exact: true }).check();
    await page.getByRole('button', { name: '确认写入隔离图谱', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value === '已写入隔离图谱。'));
    const runs = await (await page.request.get(new URL('/api/v1/runs', url).href)).json();
    let revision = runs[0].submission.revision_id;
    let expectedRevisions = 2;
    if (process.env.PRISMKE_REVIEW_BROWSER_CORRECTIONS === '1') {
      const runId = runs[0].run_id;
      await page.getByRole('radio', { name: '审核历史与纠正', exact: true }).click();
      await dropdown(page, '纠正运行');
      await dropdown(page, '历史任务', 1);
      await dropdown(page, '原审核事件');
      await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
        .some(e => e.value.includes('页码：') && e.value.includes('PrismKE')));
      assert((await page.getByRole('textbox', { name: '纠正证据原文', exact: true }).inputValue()).includes('PrismKE'));
      await page.getByRole('radio', { name: '拒绝事实', exact: true }).check();
      await page.getByRole('textbox', { name: '纠正审核人', exact: true }).fill('browser-mock-reviewer');
      await page.getByRole('textbox', { name: '纠正原因', exact: true }).fill('synthetic fact correction');
      await page.getByRole('button', { name: '预览纠正影响', exact: true }).click();
      await page.waitForFunction(() => document.body.innerText.includes('重新审核受影响事实'));
      await page.screenshot({ path: path.join(output, 'correction-desktop.png'), fullPage: true });
      await page.setViewportSize({ width: 390, height: 844 });
      await page.screenshot({ path: path.join(output, 'correction-mobile.png'), fullPage: true });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false);
      await page.setViewportSize({ width: 1440, height: 1000 });
      const beforeEvents = await (await page.request.get(new URL(`/api/v1/runs/${runId}/review-events`, url).href)).json();
      await page.getByRole('button', { name: '确认应用纠正', exact: true }).click();
      await page.waitForFunction(() => document.body.innerText.includes('explicit confirmation required'));
      const unchangedEvents = await (await page.request.get(new URL(`/api/v1/runs/${runId}/review-events`, url).href)).json();
      assert.equal(unchangedEvents.length, beforeEvents.length, 'unchecked correction cannot write an event');
      await page.getByRole('checkbox', { name: '确认应用纠正并保留历史', exact: true }).check();
      await page.getByRole('button', { name: '确认应用纠正', exact: true }).click();
      await page.waitForFunction(async rid => (await (await fetch(`/api/v1/runs/${rid}`)).json()).pending_correction_id !== null, runId);
      await page.getByRole('radio', { name: '事实审核', exact: true }).click();
      await page.getByRole('button', { name: '刷新', exact: true }).click();
      await page.getByRole('button', { name: '继续处理', exact: true }).click();
      await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
        .some(e => e.value.includes('prepare_graph_commit')));
      await page.getByRole('checkbox', { name: '确认将预览内容写入隔离图谱', exact: true }).check();
      await page.getByRole('button', { name: '确认写入隔离图谱', exact: true }).click();
      await page.waitForFunction(async rid => (await (await fetch(`/api/v1/runs/${rid}`)).json()).status === 'completed', runId);
      const corrected = await (await page.request.get(new URL('/api/v1/runs', url).href)).json();
      revision = corrected[0].submission.revision_id;
      assert.notEqual(revision, runs[0].submission.revision_id);
      expectedRevisions = 3;
    }
    await page.getByRole('radio', { name: '版本管理', exact: true }).click();
    await page.getByRole('textbox', { name: '要回滚的 Revision', exact: true }).fill(revision);
    await page.getByRole('checkbox', { name: '我确认创建补偿 Revision', exact: true }).check();
    await page.getByRole('button', { name: '执行回滚', exact: true }).click();
    await page.waitForFunction(() => document.body.textContent.includes('rollback'));
    const revisions = await (await page.request.get(new URL('/api/v1/revisions', url).href)).json();
    assert.equal(revisions.length, expectedRevisions, 'compensating rollback must preserve history');
  } else {
    await dropdown(page, '选择任务', 1);
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.startsWith('Jintian Zhang')));
    await dropdown(page, '选择任务', 2);
    await page.waitForFunction(() => [...document.querySelectorAll('textarea')]
      .some(e => e.value.startsWith('Shumin Deng')));
    const runs = await (await page.request.get(new URL('/api/v1/runs', url).href)).json();
    assert.equal(runs[0].entity_pending, 3, 'real review tasks must remain unapproved');
  }
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'browser-result.json'), JSON.stringify({
    readonly, url, pageErrors: errors, mobileOverflow: overflow, passed: true,
  }, null, 2));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
