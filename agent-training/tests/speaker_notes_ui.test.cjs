const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.join(__dirname, '..');
const url = pathToFileURL(path.join(root, 'index.html')).href;
let browser;

before(async () => { browser = await chromium.launch({channel: 'chrome', headless: true}); });
after(async () => { await browser?.close(); });

async function openNotes(options = {}) {
  const page = await browser.newPage({viewport: options.viewport || {width:1280, height:900}});
  await page.addInitScript(({unsupported, noEnglish, delayedVoices, silent, throws}) => {
    if (unsupported) {
      Object.defineProperty(window, 'speechSynthesis', {value:undefined, configurable:true});
      Object.defineProperty(window, 'SpeechSynthesisUtterance', {value:undefined, configurable:true});
      return;
    }
    const chinese = {name:'Chinese', lang:'zh-CN', localService:true};
    const english = {name:'Local English', lang:'en-US', localService:true};
    const handlers = {};
    const calls = [], utterances = [];
    let voices = noEnglish ? [chinese] : delayedVoices ? [] : [chinese, english];
    window.__speech = {
      calls, utterances, cancels:0,
      end: i => utterances[i].onend?.(),
      error: (i, error) => utterances[i].onerror?.({error}),
      ready: () => { voices = [chinese, english]; handlers.voiceschanged?.(); }
    };
    Object.defineProperty(window, 'speechSynthesis', {configurable:true, value:{
      getVoices: () => voices,
      addEventListener: (name, handler) => { handlers[name] = handler; },
      speak: utterance => {
        if (throws) throw new Error('engine unavailable');
        calls.push({text:utterance.text, rate:utterance.rate, lang:utterance.lang, voice:utterance.voice?.name});
        utterances.push(utterance);
        if (!silent) utterance.onstart?.();
      },
      cancel: () => {
        window.__speech.cancels++;
        utterances.at(-1)?.onerror?.({error:'canceled'});
      }
    }});
    Object.defineProperty(window, 'SpeechSynthesisUtterance', {configurable:true, value:class {
      constructor(text) { this.text = text; }
    }});
  }, options);
  await page.goto(url + '#' + (options.slide || 1));
  await page.keyboard.press('n');
  await page.locator('#notesTermsPanel > summary').click();
  return page;
}

test('normal, slow, acronyms, cancellation races and explicit stop use English only', async () => {
  const page = await openNotes();
  try {
    assert.deepEqual(await page.evaluate(() => __speech.calls), []);
    const card = page.locator('[data-term="agent"]');
    await card.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
    await card.getByRole('button', {name:'慢速朗读 Agent', exact:true}).click();
    assert.deepEqual(await page.evaluate(() => __speech.calls), [
      {text:'Agent', rate:1, lang:'en-US', voice:'Local English'},
      {text:'Agent', rate:.65, lang:'en-US', voice:'Local English'}
    ]);
    assert.equal(await page.evaluate(() => __speech.cancels), 1);
    await page.evaluate(() => { __speech.end(0); __speech.error(0, 'canceled'); });
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /正在朗读 Agent（慢速）/);
    assert.equal(await page.locator('#notesStopSpeech').isEnabled(), true);
    await page.evaluate(() => __speech.end(1));
    assert.equal(await page.locator('#notesStopSpeech').isDisabled(), true);
    await page.getByRole('button', {name:'正常语速朗读 LLM', exact:true}).click();
    assert.equal(await page.evaluate(() => __speech.calls.at(-1).text), 'L L M');
    await page.locator('#notesStopSpeech').click();
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /已停止/);
    assert.equal(await page.locator('[data-pronounce][aria-pressed="true"]').count(), 0);
  } finally { await page.close(); }
});

test('closing, Escape, filtering and navigation cancel speech without advancing the deck', async () => {
  const page = await openNotes();
  try {
    const speakAgent = () => page.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
    await speakAgent();
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#notesDialog').evaluate(el => el.open), false);
    assert.equal(await page.evaluate(() => __speech.cancels), 1);
    await page.keyboard.press('n');
    await speakAgent();
    await page.locator('#notesTermSearch').fill('nothing matches');
    assert.match(await page.locator('#notesTerms').textContent(), /没有匹配项/);
    assert.equal(await page.locator('#notesStopSpeech').isDisabled(), true);
    await page.locator('#notesTermSearch').fill('Agent');
    await page.getByRole('button', {name:'慢速朗读 Agent', exact:true}).press('Space');
    assert.match(page.url(), /#1$/);
    await page.locator('[data-close="notesDialog"]').click();
    await page.keyboard.press('ArrowRight');
    assert.match(page.url(), /#2$/);
    await page.keyboard.press('n');
    assert.match(await page.locator('#notesTitle').textContent(), /课程大纲/);
    await page.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
    await page.evaluate(() => { location.hash = '#3'; });
    await page.waitForFunction(() => current === 2);
    assert.equal(await page.locator('#notesStopSpeech').isDisabled(), true);
  } finally { await page.close(); }
});

test('all 39 pages retain read-aloud copy, teaching detail and matching translated terms', async () => {
  const page = await openNotes();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    const content = await page.evaluate(() => ({
      pages: COURSE.map(slide => ({title:slide.title, script:slide.speaker_script,
        supplement:slide.speaker_supplement, notes:slide.notes, terms:slide.terms})),
      glossary:GLOSSARY
    }));
    assert.equal(content.pages.length, 39);
    const notes = fs.readFileSync(path.join(root, 'docs/speaker-notes.md'), 'utf8').replace(/\r\n/g, '\n');
    for (let i = 0; i < content.pages.length; i++) {
      const slide = content.pages[i];
      assert.ok(slide.script.length > 90, slide.title);
      for (const label of ['生活类比与业务实例', '常见误区', '互动与停顿', '原有备课提示']) {
        assert.ok(slide.supplement.includes(label), slide.title + ' / ' + label);
      }
      assert.ok(notes.includes(slide.script), 'Markdown matches slide ' + (i+1));
      assert.ok(notes.includes(slide.supplement), 'Markdown supplement matches');
      assert.ok(slide.terms.length >= 3);
      for (const term of slide.terms) {
        assert.ok(content.glossary.some(item => JSON.stringify(item) === JSON.stringify(term)));
        assert.match(term.ipa, /^\/.+\/$/);
        assert.match(term.meaning, /[\u4e00-\u9fff]/);
        assert.ok(notes.includes(term.label + ' ' + term.ipa + '（' + term.meaning + '）'));
      }
      await page.evaluate(index => { showSlide(index); speakerNotes.render(COURSE[index]); }, i);
      assert.equal(await page.locator('#notesText').textContent(), slide.script);
      assert.equal(await page.locator('.notes-term').count(), slide.terms.length);
    }
    assert.deepEqual(errors, []);
  } finally { await page.close(); }
});

test('whole-course search finds translations and cannot interpret search text as markup', async () => {
  const page = await openNotes();
  try {
    await page.locator('#notesAllTerms').check();
    await page.locator('#notesTermSearch').fill('幂等');
    assert.ok(await page.locator('.notes-term').count() >= 1);
    assert.equal(await page.locator('[data-term="idempotency"]').count(), 1);
    await page.locator('#notesTermSearch').fill('<img src=x onerror=alert(1)>');
    assert.equal(await page.locator('#notesTerms img').count(), 0);
    assert.match(await page.locator('#notesTerms').textContent(), /没有匹配/);
  } finally { await page.close(); }
});

test('unsupported speech and missing English voices keep all teaching copy usable', async () => {
  for (const options of [{unsupported:true}, {noEnglish:true}]) {
    const page = await openNotes(options);
    try {
      assert.ok((await page.locator('#notesText').textContent()).length > 90);
      if (options.unsupported) {
        assert.equal(await page.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).isDisabled(), true);
        assert.match(await page.locator('#notesSpeechStatus').textContent(), /不支持/);
      } else {
        await page.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
        assert.match(await page.locator('#notesSpeechStatus').textContent(), /没有可用的英语语音/);
        assert.deepEqual(await page.evaluate(() => __speech.calls), []);
      }
      await page.locator('#notesSupplementPanel > summary').click();
      assert.match(await page.locator('#notesSupplement').textContent(), /生活类比/);
    } finally { await page.close(); }
  }
});

test('voice loading, playback errors and engine exceptions are recoverable', async () => {
  const page = await openNotes({delayedVoices:true});
  try {
    await page.evaluate(() => __speech.ready());
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /Local English/);
    const button = page.getByRole('button', {name:'正常语速朗读 Agent', exact:true});
    await button.click();
    await page.evaluate(() => __speech.error(0, 'language-unavailable'));
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /英语语音不可用/);
    assert.equal(await page.locator('#notesStopSpeech').isDisabled(), true);
    await button.click();
    assert.equal(await page.evaluate(() => __speech.calls.length), 2);
    await page.evaluate(() => __speech.error(1, 'network'));
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /未能完成/);
  } finally { await page.close(); }
  const throwing = await openNotes({throws:true});
  try {
    await throwing.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
    assert.match(await throwing.locator('#notesSpeechStatus').textContent(), /无法启动/);
    assert.equal(await throwing.locator('#notesStopSpeech').isDisabled(), true);
  } finally { await throwing.close(); }
});

test('a silent voice engine eventually offers a retry instead of staying busy', async () => {
  const page = await openNotes({silent:true});
  try {
    await page.clock.install();
    await page.getByRole('button', {name:'正常语速朗读 Agent', exact:true}).click();
    await page.clock.fastForward(8001);
    assert.match(await page.locator('#notesSpeechStatus').textContent(), /未能开始/);
    assert.equal(await page.locator('#notesStopSpeech').isDisabled(), true);
  } finally { await page.close(); }
});

test('notes, IPA and playback controls fit desktop and mobile with keyboard access', async () => {
  fs.mkdirSync(path.join(root, 'test-results/speaker-notes'), {recursive:true});
  for (const viewport of [{width:1280,height:900}, {width:390,height:844}]) {
    const page = await openNotes({viewport});
    try {
      const agent = page.locator('[data-term="agent"]');
      const button = agent.getByRole('button', {name:'正常语速朗读 Agent', exact:true});
      await button.focus();
      await page.keyboard.press('Enter');
      assert.match(await page.locator('#notesSpeechStatus').textContent(), /正在朗读 Agent/);
      const geometry = await page.locator('#notesDialog').evaluate(dialog => {
        const r = dialog.getBoundingClientRect();
        return {width:dialog.clientWidth, content:dialog.scrollWidth, left:r.left, right:r.right,
          viewport:window.innerWidth};
      });
      assert.ok(geometry.content <= geometry.width + 1, JSON.stringify(geometry));
      assert.ok(geometry.left >= 0 && geometry.right <= geometry.viewport);
      assert.match(await agent.textContent(), /ˈeɪdʒənt/);
      await page.screenshot({path:path.join(root, 'test-results/speaker-notes/notes-' + viewport.width + '.png')});
    } finally { await page.close(); }
  }
});
