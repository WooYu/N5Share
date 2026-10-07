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

test('all seven diagrams play, step back and replay across all weather/budget scenarios', async () => {
  const page = await browser.newPage({viewport: {width: 1280, height: 720}, reducedMotion: 'reduce'});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(base + '#6');
    for (let arch = 1; arch <= 7; arch++) {
      await page.evaluate(n => showSlide(n + 4), arch);
      const panel = page.locator('.slide.active .architecture-walkthrough');
      assert.equal(await page.locator('.slide.active .walk-tradeoffs').count(), 1);
      assert.ok(await panel.locator('[data-vis-limitation="node"] .walk-limit-pin').count() > 0);
      assert.equal(await panel.locator('[data-vis-limit-note]').count(), 0);
      for (const pin of await panel.locator('.walk-limit-pin').all()) {
        await pin.hover();
        assert.match(await pin.locator('title').textContent(), /^局限位置：.+/);
        assert.equal(await pin.evaluate(el => getComputedStyle(el).cursor), 'help');
      }
      for (const weather of ['rain', 'sun']) for (const budget of ['100', '200', '300']) {
        await panel.locator('[data-outing-more]').click();
        await panel.locator('[data-outing-weather]').selectOption(weather);
        await panel.locator('[data-outing-budget]').selectOption(budget);
        await panel.locator('[data-outing-close]').click();
        const expected = await page.evaluate(([a, w, b]) => makeArchitecturePresentation(a, w, Number(b)), [arch, weather, budget]);
        for (const step of expected) {
          await panel.locator('[data-outing-next]').click();
          for (const id of step.nodes) assert.equal(await panel.locator(`[data-vis-node="${id}"].is-current`).count(), 1, `arch ${arch} node ${id}`);
          for (const id of step.edges) assert.equal(await panel.locator(`[data-vis-edge="${id}"].is-current`).count(), 1, `arch ${arch} edge ${id}`);
          assert.equal(await panel.locator('[data-outing-output] strong').innerText(), step.caption);
          assert.equal(await panel.locator('[data-outing-output]').evaluate(el => el.scrollHeight <= el.clientHeight + 1), true, `caption must fit: ${step.caption}`);
        }
        assert.equal(await panel.locator('[data-outing-next]').isDisabled(), true);
        await panel.locator('[data-outing-prev]').click();
        assert.equal(await panel.locator('[data-outing-next]').isDisabled(), false);
        assert.equal(await panel.locator('[data-outing-output] strong').innerText(), expected.at(-2).caption);
        await panel.locator('[data-outing-reset]').click();
        assert.equal(await panel.locator('.is-current').count(), 0);
        assert.equal(await panel.locator('[data-outing-prev]').isDisabled(), true);
      }
    }
    assert.deepEqual(errors, []);
  } finally {await page.close();}
});

test('cost and unknown intents select the correct visual exits', async () => {
  const page = await browser.newPage({viewport: {width: 1280, height: 720}});
  try {
    await page.goto(base + '#10');
    const panel = page.locator('.slide.active .architecture-walkthrough');
    for (const intent of ['budget', 'unclear', 'outing']) {
      await panel.locator('[data-outing-more]').click();
      await panel.locator('[data-outing-intent]').selectOption(intent);
      await panel.locator('[data-outing-close]').click();
      while (!await panel.locator('[data-outing-next]').isDisabled()) await panel.locator('[data-outing-next]').click();
      assert.match(await panel.locator('[data-outing-output] strong').innerText(), intent === 'unclear' ? /先澄清/ : /只交付完整费用/);
    }
  } finally {await page.close();}
});

test('key events update the visible scenario and rewind it without changing live parameters', async () => {
  const page = await browser.newPage({viewport: {width: 1280, height: 720}});
  try {
    await page.goto(base + '#8');
    const plan = page.locator('.slide.active .architecture-walkthrough');
    for (let i = 0; i < 6; i++) await plan.locator('[data-outing-next]').click();
    assert.match(await plan.locator('[data-outing-scenario]').innerText(), /300 → 200/);
    assert.equal(await plan.locator('[data-outing-budget]').inputValue(), '300');
    await plan.locator('[data-outing-prev]').click();
    assert.doesNotMatch(await plan.locator('[data-outing-scenario]').innerText(), /→/);
    await plan.locator('[data-outing-next]').click();
    while (!await plan.locator('[data-outing-next]').isDisabled()) await plan.locator('[data-outing-next]').click();
    assert.match(await plan.locator('[data-outing-output] strong').innerText(), /200 元预算/);
    await plan.locator('[data-outing-reset]').click();
    assert.doesNotMatch(await plan.locator('[data-outing-scenario]').innerText(), /→/);
    await page.evaluate(() => showSlide(9));
    const router = page.locator('.slide.active .architecture-walkthrough');
    for (let i = 0; i < 5; i++) await router.locator('[data-outing-next]').click();
    assert.match(await router.locator('[data-outing-scenario]').innerText(), /只核算费用/);
    assert.equal(await router.locator('[data-outing-intent]').inputValue(), 'outing');
    await router.locator('[data-outing-prev]').click();
    assert.match(await router.locator('[data-outing-scenario]').innerText(), /安排出游/);
    await page.evaluate(() => showSlide(11));
    const graph = page.locator('.slide.active .architecture-walkthrough');
    assert.equal(await graph.locator('[data-outing-budget]').inputValue(), '200');
    while (!await graph.locator('[data-outing-next]').isDisabled()) await graph.locator('[data-outing-next]').click();
    assert.equal(await graph.locator('[data-vis-node="END"].is-current').count(), 1);
    assert.equal(await graph.locator('[data-vis-edge="validate-no_solution"].is-visited').count(), 1);
  } finally {await page.close();}
});

test('slide content stays inside its fixed stage at desktop and phone sizes', async () => {
  const page = await browser.newPage({reducedMotion: 'reduce'});
  try {
    await page.goto(base + '#6');
    fs.mkdirSync(path.join(__dirname, '../test-results/walkthrough'), {recursive: true});
    for (const viewport of [{width: 1280, height: 720}, {width: 390, height: 844}]) {
      await page.setViewportSize(viewport);
      for (let n = 6; n <= 12; n++) {
        await page.evaluate(n => showSlide(n - 1), n);
        await page.locator('.slide.active [data-outing-reset]').click();
        const issues = await page.evaluate(() => {
          const slide = document.querySelector('.slide.active');
          const content = slide.querySelector('.slide-content').getBoundingClientRect();
          const footer = slide.querySelector('.slide-footer').getBoundingClientRect();
          const bad = [];
          for (const el of slide.querySelectorAll('.walk-lead, .walk-context, .architecture-canvas, .walk-step, .walk-toolbar, .walk-tradeoffs')) {
            const r = el.getBoundingClientRect();
            if (r.bottom > content.bottom + 1 || r.right > content.right + 1 || r.left < content.left - 1) bad.push(el.className);
            if (r.bottom > footer.top - 2) bad.push('footer overlap: ' + el.className);
          }
          for (const el of slide.querySelectorAll('.walk-step, .walk-tradeoffs>div')) {
            if (el.scrollHeight > el.clientHeight + 1) bad.push('text overflow: ' + el.className);
          }
          return bad;
        });
        assert.deepEqual(issues, [], `slide ${n} at ${viewport.width}`);
        const stage = await page.locator('#stage').boundingBox();
        assert.ok(Math.abs(stage.width / stage.height - 16 / 9) < .01);
        if (viewport.width === 1280) {
          await page.screenshot({path: path.join(__dirname, `../test-results/walkthrough/page-${n}.png`)});
          await page.evaluate(() => {
            const panel = document.querySelector('.slide.active .architecture-walkthrough');
            const count = {1: 8, 2: 12, 3: 6, 4: 5, 5: 6, 6: 2, 7: 7}[Number(panel.dataset.outingArchitecture)];
            for (let i = 0; i < count; i++) panel.querySelector('[data-outing-next]').click();
          });
          await page.screenshot({path: path.join(__dirname, `../test-results/walkthrough/page-${n}-active.png`)});
        } else if (n === 6) await page.screenshot({path: path.join(__dirname, '../test-results/walkthrough/phone.png')});
      }
    }
  } finally {await page.close();}
});
