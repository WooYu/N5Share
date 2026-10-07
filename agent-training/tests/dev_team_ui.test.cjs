const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
test('MetaGPT review design and VS Code walkthrough fit desktop and phone', async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const page = await browser.newPage({reducedMotion:'reduce'});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(pathToFileURL(path.join(__dirname,'..','index.html')).href);
    const indexes = await page.evaluate(() => COURSE.flatMap((s,i) => s.chapter === '智能开发团队实战' ? [i] : []));
    assert.equal(indexes.length, 8);
    for (const viewport of [{width:1280,height:720},{width:390,height:844}]) {
      await page.setViewportSize(viewport);
      for (const index of indexes) {
        await page.evaluate(i => showSlide(i), index);
        const issues = await page.evaluate(() => {
          const slide = document.querySelector('.slide.active');
          const bounds = slide.querySelector('.slide-content').getBoundingClientRect();
          const footer = slide.querySelector('.slide-footer').getBoundingClientRect();
          return [...slide.querySelectorAll('.dev-lead,.dev-flow,.dev-grid,.dev-table,.dev-takeaway')].flatMap(el => {
            const r = el.getBoundingClientRect();
            return r.bottom > bounds.bottom+1 || r.bottom > footer.top-2 || r.right > bounds.right+1 || r.left < bounds.left-1
              ? [el.className + ' exceeds content bounds'] : [];
          });
        });
        assert.deepEqual(issues, [], `slide ${index+1} width ${viewport.width}`);
        assert.equal(await page.locator('.slide.active pre').count(),0);
      }
    }
    await page.evaluate(() => showSlide(COURSE.findIndex(s => s.title === '修复、复审与人工门禁怎样落到代码')));
    assert.match(await page.locator('.slide.active').innerText(), /旧结果失效/);
    await page.evaluate(() => showSlide(COURSE.findIndex(s => s.title === '切换 VS Code：运行评审、修复与复审')));
    assert.equal(await page.locator('.slide.active a[href="docs/dev-team-demo-guide.md"]').count(),1);
    await page.locator('#notesBtn').click();
    assert.match(await page.locator('#notesText').innerText(), /review-1/);
    assert.deepEqual(errors,[]);
    await page.keyboard.press('Escape');
    await page.setViewportSize({width:1280,height:720});
    await page.screenshot({path:path.join(__dirname,'..','test-results','dev-team-slide.png')});
  } finally {await page.close();await browser.close();}
});
