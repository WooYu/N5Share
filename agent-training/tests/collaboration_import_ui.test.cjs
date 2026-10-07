const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.join(__dirname, '..');
const python = process.env.PYTHON_COMMAND || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const listingsById = JSON.parse(execFileSync(python, ['-c',
  'import sys; sys.path.insert(0, "course"); import json; from collaboration_import import course_sections, code_text; print(json.dumps({f"{sid}:{i}": code_text(b) for sid,s in course_sections().items() for i,b in enumerate(s["blocks"]) if code_text(b) is not None}))'], {cwd:root, encoding:'utf8'}));
const original = JSON.parse(fs.readFileSync(path.join(root, 'archive/2026-10-07-before-collaboration-import/slides.json'), 'utf8'));
let browser, server, base;
before(async () => {
  server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(fs.readFileSync(path.join(root, 'index.html')));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({channel: 'chrome', headless: true});
});
after(async () => {
  await browser?.close();
  await new Promise(resolve => server?.close(resolve));
});

async function assertFits(page, label) {
  const issues = await page.evaluate(() => {
    const slide = document.querySelector('.slide.active');
    const bounds = slide.querySelector('.slide-content').getBoundingClientRect();
    const footer = slide.querySelector('.slide-footer').getBoundingClientRect();
    const bad = [];
    for (const element of slide.querySelectorAll('.import-body, .import-body h3, .import-body pre, .import-body table, .import-body .card-grid, .import-body .highlight-box, .accordion-body, .faq-a')) {
      if (!element.getClientRects().length) continue;
      const rect = element.getBoundingClientRect();
      if (rect.bottom > bounds.bottom + 1) bad.push(`${element.className || element.tagName}: content overflow ${Math.round(rect.bottom - bounds.bottom)}`);
      if (rect.right > bounds.right + 1 || rect.left < bounds.left - 1) bad.push(`${element.className || element.tagName}: horizontal overflow`);
      if (rect.bottom > footer.top - 2) bad.push(`${element.className || element.tagName}: footer overlap`);
      if (element.tagName === 'PRE' && element.scrollWidth > element.clientWidth + 1) bad.push('code requires horizontal scrolling');
    }
    const number = slide.querySelector('.slide-num').getBoundingClientRect();
    for (const link of slide.querySelectorAll('.slide-footer a')) {
      const rect = link.getBoundingClientRect();
      if (rect.right > number.left - 2 || rect.bottom > footer.bottom + 1) bad.push('footer link overflow');
    }
    return bad;
  });
  assert.deepEqual(issues, [], label);
}

test('the source overview follows the architecture demos and the final page is reachable', async () => {
  const page = await browser.newPage({viewport: {width:1280, height:720}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(base + '#12');
    await page.locator('#nextBtn').click();
    assert.equal(await page.locator('.slide.active h2').textContent(), '五种协作模式总览');
    assert.match(page.url(), /#13$/);
    const course = await page.evaluate(() => COURSE.map(slide => ({title:slide.title, section:slide.source_section})));
    assert.deepEqual([course[0], ...course.slice(2, 12)].map(slide => slide.title), original.slice(0,11).map(slide => slide.title));
    assert.equal(course.length, 39);
    assert.equal(course.at(-1).title, '关键挑战与决策矩阵 · 性能目标示例');
    assert.ok(original.slice(34).every(removed => !course.some(slide => slide.title === removed.title)));
    assert.equal(await page.locator('#tocList button').count(), course.length);
    await page.locator('#tocBtn').click();
    await page.locator('#tocList button').last().click();
    assert.match(await page.locator('.slide.active h2').textContent(), /性能目标示例/);
    assert.equal(await page.locator('#nextBtn').isDisabled(), true);
    await page.keyboard.press('ArrowRight');
    assert.match(page.url(), /#39$/);
    assert.equal(await page.locator('#pageNumber').textContent(), '39 / 39');
    await page.locator('#notesBtn').click();
    assert.ok((await page.locator('#notesText').textContent()).length > 50);
    assert.deepEqual(errors, []);
  } finally {await page.close();}
});

test('the overview compares all five modes and imported footers match the notes', async () => {
  const page = await browser.newPage();
  try {
    await page.goto(base + '#13');
    assert.deepEqual(await page.locator('.slide.active .comparison-pattern h4').allTextContents(),
      ['Supervisor', 'Hierarchical', 'Swarm', 'Sequential Chain', 'Network']);
    assert.equal(await page.locator('.slide.active svg[role="img"]').count(), 5);
    assert.equal(await page.locator('.slide.active table').count(), 0);
    await assertFits(page, 'visual comparison');
    const pages = await page.evaluate(() => COURSE.flatMap((slide, index) => {
      if (!slide.source_section) return [];
      const links = [...document.querySelectorAll('.slide')[index].querySelectorAll('.slide-footer a')];
      return [{number:index+1, references:slide.sources.map(source => source[1]),
        links:links.map(link => link.getAttribute('href')), labels:links.map(link => link.textContent)}];
    }));
    assert.deepEqual(pages.map(page => page.number), [
      ...Array.from({length:9}, (_, index) => index+13),
      ...Array.from({length:15}, (_, index) => index+25),
    ]);
    for (const page of pages) {
      assert.deepEqual(page.links, page.references, `slide ${page.number}`);
      assert.ok(page.links.length > 0 && page.links.every(url => url.startsWith('https://')));
      assert.ok(page.labels.every(label => !label.includes('导入文档')));
    }
  } finally {await page.close();}
});

test('all imported pages fit the projection stage on desktop and phone', async () => {
  const page = await browser.newPage({reducedMotion:'reduce'});
  try {
    await page.goto(base + '#13');
    const indexes = await page.evaluate(() => COURSE.flatMap((slide,index) => slide.source_section ? [index] : []));
    for (const viewport of [{width:1280,height:720}, {width:390,height:844}]) {
      await page.setViewportSize(viewport);
      for (const index of indexes) {
        await page.evaluate(index => showSlide(index), index);
        await assertFits(page, `slide ${index+1} at ${viewport.width}`);
      }
    }
  } finally {await page.close();}
});

test('copying a paginated code example includes the complete original listing', async (t) => {
  const page = await browser.newPage();
  try {
    await page.goto(base + '#12');
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', {configurable:true, value:{writeText:async text => {window.importCopied = text;}}});
    });
    const listings = await page.evaluate(listingsById => {
      const ids = [...new Set([...document.querySelectorAll('[data-import-copy]')].map(button => button.closest('[data-import-block]').dataset.importBlock))];
      return ids.map(id => {
        return {id, text:listingsById[id]};
      });
    }, listingsById);
    if (!listings.length) {
      t.skip('Current course shows live source excerpts; imported code listings stay in the source snapshot.');
      return;
    }
    for (const listing of listings) {
      const index = await page.locator(`[data-import-block="${listing.id}"]`).first().evaluate(el => [...document.querySelectorAll('.slide')].indexOf(el.closest('.slide')));
      await page.evaluate(index => showSlide(index), index);
      await page.locator(`.slide.active [data-import-block="${listing.id}"] [data-import-copy]`).click();
      assert.equal(await page.evaluate(() => window.importCopied), listing.text, listing.id);
      assert.equal(await page.locator('.slide.active [data-import-copy]').first().textContent(), '已复制');
    }
  } finally {await page.close();}
});

test('engineering challenges open, close and support keyboard interaction', async () => {
  const page = await browser.newPage({viewport:{width:1280,height:720}});
  try {
    await page.goto(base + '#12');
    const indexes = await page.evaluate(() => COURSE.flatMap((slide,index) => /data-import-(faq|accordion)/.test(slide.body) ? [index] : []));
    for (const index of indexes) {
      await page.evaluate(index => showSlide(index), index);
      const triggers = page.locator('.slide.active [data-import-faq], .slide.active [data-import-accordion]');
      for (const trigger of await triggers.all()) {
        await trigger.click();
        assert.equal(await trigger.getAttribute('aria-expanded'), 'true');
        assert.equal(await page.locator('.slide.active .faq-item.open, .slide.active .accordion-item.open').count(), 1);
        await assertFits(page, `expanded answer on slide ${index+1}`);
        await trigger.press('Space');
        assert.equal(await trigger.getAttribute('aria-expanded'), 'false');
        assert.match(page.url(), new RegExp(`#${index+1}$`));
      }
    }
  } finally {await page.close();}
});

test('removed diagnosis controls do not break navigation or old slide links', async () => {
  const page = await browser.newPage({viewport:{width:1280,height:720}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(base + '#48');
    assert.equal(await page.evaluate(() => labIndex), -1);
    assert.equal(await page.locator('#playDemo').count(), 0);
    assert.equal(await page.locator('#pageNumber').textContent(), '39 / 39');
    await page.keyboard.press('Home');
    assert.equal(await page.locator('#pageNumber').textContent(), '1 / 39');
    await page.keyboard.press('End');
    assert.equal(await page.locator('#pageNumber').textContent(), '39 / 39');
    assert.deepEqual(errors, []);
  } finally {await page.close();}
});
