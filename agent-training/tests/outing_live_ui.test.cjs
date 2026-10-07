// Controlled HTTP responses exercise the real dialog; no model calls are made.
const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
let browser, server, base;
before(async () => {
  server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(fs.readFileSync(path.join(__dirname, '../index.html')));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({channel: 'chrome', headless: true});
});
after(async () => {
  await browser?.close();
  await new Promise(resolve => server?.close(resolve));
});

async function setup() {
  const page = await browser.newPage({viewport: {width: 1600, height: 1000}});
  const jobs = new Map();
  const starts = [];
  let holdPoll = false, releasePoll;
  await page.route('**/api/outing/**', async route => {
    const url = new URL(route.request().url());
    let body;
    if (url.pathname.endsWith('/config')) body = {configured: true, provider: 'Test', model: 'test-model', transport: 'test'};
    else if (url.pathname.endsWith('/start')) {
      const config = route.request().postDataJSON();
      starts.push(config);
      const id = `run-${starts.length}`;
      body = {id, config, status: 'running', mode: 'live', verified: false,
        events: [{phase: 'test', title: `stage-${config.stage}-${config.pattern}`, detail: id, actor: 'test'}], metrics: {model_calls: 1}};
      jobs.set(id, body);
    } else if (url.pathname.endsWith('/cancel')) {
      jobs.get(route.request().postDataJSON().id).status = 'cancelled';
      body = {ok: true};
    } else {
      const id = url.pathname.split('/').at(-1);
      if (holdPoll) await new Promise(resolve => {releasePoll = resolve;});
      body = jobs.get(id);
    }
    await route.fulfill({json: JSON.parse(JSON.stringify(body))});
  });
  const open = async number => {
    await page.goto(base + '#' + number);
    await page.locator('.slide.active [data-outing-more]').click();
    await page.locator('.slide.active [data-outing-live]').click();
    await page.locator('[data-live-connection]').filter({hasText: 'test-model'}).waitFor();
  };
  const close = () => page.locator('[data-close="outingLiveDialog"]').click();
  const start = async () => {
    await page.locator('[data-live-run]').click();
    await page.locator('[data-live-events] button').first().waitFor();
  };
  return {page, jobs, starts, open, close, start,
    hold: () => {holdPoll = true;}, release: () => {holdPoll = false; releasePoll?.();}};
}

test('opening another architecture shows its own empty view while the first run continues', async () => {
  const env = await setup();
  try {
    await env.open(5);
    await env.start();
    await env.close();
    await env.open(6);
    assert.match(await env.page.locator('[data-live-title]').innerText(), /② ReAct/);
    assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
    assert.equal(await env.page.locator('[data-live-run]').isDisabled(), true);
    await env.page.locator('[data-live-cancel]').click();
    await env.page.locator('[data-live-run]').waitFor({state: 'visible'});
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.start();
    assert.deepEqual(env.starts.map(c => c.stage), [3, 4]);
    assert.match(await env.page.locator('[data-live-events]').innerText(), /stage-4/);
    assert.doesNotMatch(await env.page.locator('[data-live-events]').innerText(), /stage-3/);
  } finally {env.release(); await env.page.close();}
});

test('late poll responses update only the originating architecture', async () => {
  const env = await setup();
  try {
    env.hold();
    await env.open(5);
    await env.start();
    await env.close();
    await env.open(7);
    env.jobs.get('run-1').status = 'completed';
    env.release();
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    assert.match(await env.page.locator('[data-live-title]').innerText(), /③ Plan/);
    assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
    assert.equal(await env.page.locator('[data-live-export]').isDisabled(), true);
    await env.close();
    await env.open(5);
    assert.match(await env.page.locator('[data-live-events]').innerText(), /stage-3/);
  } finally {env.release(); await env.page.close();}
});

test('collaboration patterns and reruns keep configuration and event history separate', async () => {
  const env = await setup();
  try {
    await env.open(8);
    env.jobs.clear();
    await env.start();
    env.jobs.get('run-1').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.page.locator('[data-live-pattern]').selectOption('hierarchical');
    assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
    await env.start();
    assert.deepEqual(env.starts.map(c => c.pattern), ['supervisor', 'hierarchical']);
    env.jobs.get('run-2').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.page.locator('[data-live-pattern]').selectOption('supervisor');
    assert.match(await env.page.locator('[data-live-events]').innerText(), /stage-7-supervisor/);
    await env.start();
    assert.equal(await env.page.locator('[data-live-events] button').count(), 1);
    assert.match(await env.page.locator('[data-live-detail]').innerText(), /run-3/);
  } finally {env.release(); await env.page.close();}
});

test('weather and budget changes open an empty scenario and preserve only its own history', async () => {
  const env = await setup();
  try {
    await env.open(5);
    await env.start();
    env.jobs.get('run-1').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.close();
    await env.page.locator('.slide.active [data-outing-more]').click();
    await env.page.locator('.slide.active [data-outing-weather]').selectOption('sun');
    await env.page.locator('.slide.active [data-outing-budget]').selectOption('200');
    await env.page.locator('.slide.active [data-outing-close]').click();
    await env.open(5);
    assert.match(await env.page.locator('[data-live-task]').innerText(), /晴天.*200 元/);
    assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
    assert.equal(await env.page.locator('[data-live-export]').isDisabled(), true);
    await env.start();
    assert.equal(env.starts[1].weather, 'sun');
    assert.equal(env.starts[1].budget, 200);
    env.jobs.get('run-2').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.close();
    await env.page.locator('.slide.active [data-outing-more]').click();
    await env.page.locator('.slide.active [data-outing-weather]').selectOption('rain');
    await env.page.locator('.slide.active [data-outing-budget]').selectOption('300');
    await env.page.locator('.slide.active [data-outing-close]').click();
    await env.open(5);
    assert.match(await env.page.locator('[data-live-detail]').innerText(), /run-1/);
  } finally {env.release(); await env.page.close();}
});

test('a response for another configuration is not accepted into the current trace', async () => {
  const env = await setup();
  try {
    env.hold();
    await env.open(5);
    await env.start();
    env.jobs.get('run-1').config.stage = 4;
    env.jobs.get('run-1').events = [{phase: 'test', title: 'WRONG-DEMO', actor: 'test', detail: 'wrong configuration'}];
    env.release();
    await env.page.locator('[data-live-status]').filter({hasText: '不一致'}).waitFor();
    assert.doesNotMatch(await env.page.locator('[data-live-events]').innerText(), /WRONG-DEMO/);
    assert.match(await env.page.locator('[data-live-title]').innerText(), /① 单 Agent/);
  } finally {env.release(); await env.page.close();}
});

test('a late failed cancel request cannot overwrite the status of a rerun', async () => {
  const env = await setup();
  let releaseCancel;
  try {
    await env.page.route('**/api/outing/cancel', async route => {
      env.jobs.get(route.request().postDataJSON().id).status = 'cancelled';
      await new Promise(resolve => {releaseCancel = resolve;});
      await route.fulfill({status: 500, json: {error: 'OLD-CANCEL-ERROR'}});
    });
    await env.open(5);
    await env.start();
    await env.page.locator('[data-live-cancel]').click();
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.start();
    releaseCancel();
    await env.page.waitForResponse(response => response.url().endsWith('/cancel') && response.status() === 500);
    assert.doesNotMatch(await env.page.locator('[data-live-status]').innerText(), /OLD-CANCEL-ERROR|停止请求未送达/);
    assert.match(await env.page.locator('[data-live-detail]').innerText(), /run-2/);
  } finally {releaseCancel?.(); env.release(); await env.page.close();}
});

test('new architectures start with their own stage, title and tradeoffs', async () => {
  const env = await setup();
  try {
    for (const [page, stage, title] of [[9, 8, 'Router'], [10, 9, 'Blackboard'], [11, 10, 'Graph']]) {
      await env.open(page);
      assert.ok((await env.page.locator('[data-live-title]').innerText()).includes(title));
      assert.ok((await env.page.locator('[data-live-tradeoffs]').innerText()).includes(title));
      assert.equal(await env.page.locator('[data-live-pattern-row]').isVisible(), false);
      assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
      await env.start();
      assert.equal(env.starts.at(-1).stage, stage);
      env.jobs.get(`run-${env.starts.length}`).status = 'completed';
      await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
      await env.close();
    }
  } finally {env.release(); await env.page.close();}
});

test('router intent is sent to the backend and owns a separate session', async () => {
  const env = await setup();
  try {
    await env.open(9);
    await env.start();
    assert.equal(env.starts[0].intent, 'outing');
    env.jobs.get('run-1').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.close();
    await env.page.locator('.slide.active [data-outing-more]').click();
    await env.page.locator('.slide.active [data-outing-intent]').selectOption('budget');
    await env.page.locator('.slide.active [data-outing-live]').click();
    await env.page.locator('[data-live-connection]').filter({hasText: 'test-model'}).waitFor();
    assert.match(await env.page.locator('[data-live-task]').innerText(), /只核算费用/);
    assert.equal(await env.page.locator('[data-live-events] button').count(), 0);
    await env.start();
    assert.equal(env.starts[1].intent, 'budget');
    env.jobs.get('run-2').status = 'completed';
    await env.page.waitForFunction(() => !document.querySelector('[data-live-run]').disabled);
    await env.close();
    await env.page.locator('.slide.active [data-outing-more]').click();
    await env.page.locator('.slide.active [data-outing-intent]').selectOption('outing');
    await env.page.locator('.slide.active [data-outing-live]').click();
    await env.page.locator('[data-live-connection]').filter({hasText: 'test-model'}).waitFor();
    assert.match(await env.page.locator('[data-live-detail]').innerText(), /run-1/);
  } finally {env.release(); await env.page.close();}
});
