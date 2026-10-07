const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.join(__dirname, '..');
let browser;
before(async () => { browser = await chromium.launch({channel:'chrome', headless:true}); });
after(async () => { await browser?.close(); });
const modes = ['sequential', 'supervisor', 'hierarchical', 'swarm', 'network'];

async function fit(page, label) {
  const problems = await page.evaluate(() => {
    const slide = document.querySelector('.slide.active');
    const bounds = slide.querySelector('.slide-content').getBoundingClientRect();
    const footer = slide.querySelector('.slide-footer').getBoundingClientRect();
    const nodes = slide.querySelectorAll('.ct-vscode-layout, .ct-vscode-diagram, .ct-vscode-observe, .ct-vscode-observe li, .ct-vscode-source, .ct-vscode-source code, .ct-vscode-run, .ct-vscode-run pre, .ct-vscode-bottom, .ct-table, .ct-prompt, .ct-footnote, .ct-answer, .ct-role-strip');
    return [...nodes].filter(el => el.getClientRects().length).flatMap(el => {
      const box = el.getBoundingClientRect();
      const issues = [];
      if (box.bottom > bounds.bottom + 1 || box.bottom > footer.top - 2) issues.push(`${el.className}: bottom overflow`);
      if (box.left < bounds.left - 1 || box.right > bounds.right + 1) issues.push(`${el.className}: horizontal overflow`);
      if (el.matches('pre') && el.scrollWidth > el.clientWidth + 2) issues.push('code horizontal scroll');
      if (el.matches('.ct-vscode-source code') && getComputedStyle(el).color !== 'rgb(237, 244, 255)') issues.push('code contrast');
      if (el.matches('.ct-vscode-observe li') && box.bottom > el.closest('.ct-vscode-layout').getBoundingClientRect().bottom + 1) issues.push('observation overlaps source link');
      return issues;
    });
  });
  assert.deepEqual(problems, [], label);
}

test('five mode pages link complete live source and show its real orchestration excerpt', async () => {
  const page = await browser.newPage({viewport:{width:1280,height:720}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href + '#14');
    for (const [offset, pattern] of modes.entries()) {
      await page.evaluate(number => showSlide(number - 1), 17 + offset);
      assert.equal(await page.locator('.slide.active svg').count(), 0);
      assert.equal(await page.locator('.slide.active a[href="demo/collaboration_live/' + pattern + '.py"]').count(), 1);
      await fit(page, `structure ${pattern}`);

      const excerpt = await page.locator('.slide.active .ct-vscode-source code').textContent();
      const source = fs.readFileSync(path.join(root, 'demo/collaboration_live', pattern + '.py'), 'utf8');
      assert.ok(source.includes(excerpt), pattern);
      await page.locator('#notesBtn').click();
      const command = await page.locator('#notesText').textContent();
      await page.keyboard.press('Escape');
      assert.match(command, new RegExp(`run_collaboration.py --pattern ${pattern} --scenario missing --step`));
      assert.equal(await page.locator('.slide.active [data-ct-action]').count(), 0);
      await fit(page, `code ${pattern}`);
    }
    assert.deepEqual(errors, []);
  } finally { await page.close(); }
});

test('all VS Code guide slides and exercise answer fit desktop and mobile projection', async () => {
  const page = await browser.newPage({reducedMotion:'reduce'});
  try {
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href + '#14');
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      await page.setViewportSize(viewport);
      for (let number = 14; number <= 21; number++) {
        await page.evaluate(number => showSlide(number - 1), number);
        await fit(page, `slide ${number} at ${viewport.width}`);
      }
    }
    await page.setViewportSize({width:1440,height:900});
    for (const [index, name] of [[16,'code'],[19,'swarm'],[14,'comparison'],[15,'playground']]) {
      await page.evaluate(index => showSlide(index), index);
      await page.screenshot({path:path.join(process.env.TEMP, 'collaboration-training-' + name + '.png')});
    }
  } finally { await page.close(); }
});
