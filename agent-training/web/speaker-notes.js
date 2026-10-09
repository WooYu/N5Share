/* English pronunciation in the notes dialog; no audio plays without a click. */
const speakerNotes = (() => {
  const byId = id => document.getElementById(id);
  const dialog = byId('notesDialog');
  const status = byId('notesSpeechStatus');
  const stopButton = byId('notesStopSpeech');
  const list = byId('notesTerms');
  const search = byId('notesTermSearch');
  const allTerms = byId('notesAllTerms');
  const supported = Boolean(window.speechSynthesis && typeof window.SpeechSynthesisUtterance === 'function');
  const synth = supported ? window.speechSynthesis : null;
  let pageTerms = [];
  let active = null;
  let startTimer = null;

  function englishVoice() {
    const voices = synth ? synth.getVoices().filter(voice => /^en(?:[-_]|$)/i.test(voice.lang)) : [];
    return voices.find(voice => /^en[-_]US$/i.test(voice.lang) && voice.localService)
      || voices.find(voice => /^en[-_]US$/i.test(voice.lang))
      || voices.find(voice => voice.localService) || voices[0] || null;
  }

  function readyMessage() {
    if (!supported) return '此浏览器不支持语音朗读，请使用支持语音的 Chrome 或 Edge；音标和释义仍可阅读。';
    const voice = englishVoice();
    if (voice) return '点击术语旁的按钮听英文。当前英语语音：' + voice.name
      + (voice.localService ? '（本机语音，可离线使用）。' : '（此语音可能需要联网）。');
    return '点击按钮听英文。若无法发音，请检查系统是否安装英语语音；音标和释义仍可阅读。';
  }

  function resetButtons() {
    list.querySelectorAll('[data-pronounce]').forEach(button => button.setAttribute('aria-pressed', 'false'));
    stopButton.disabled = true;
  }

  function stop(message) {
    const wasActive = Boolean(active);
    active = null; // Cancel callbacks from an older request must not affect the new one.
    clearTimeout(startTimer);
    startTimer = null;
    if (synth && wasActive) synth.cancel();
    resetButtons();
    if (message) status.textContent = message;
    else if (wasActive) status.textContent = readyMessage();
  }

  function speak(term, rate, button) {
    stop();
    if (!supported) {
      status.textContent = readyMessage();
      return;
    }
    const voice = englishVoice();
    if (!voice && synth.getVoices().length) {
      status.textContent = '没有可用的英语语音。请在系统语音设置中安装英语语音后重试；可先参考音标。';
      return;
    }
    const utterance = new SpeechSynthesisUtterance(term.spoken || term.label);
    utterance.lang = voice ? voice.lang : 'en-US';
    if (voice) utterance.voice = voice;
    utterance.rate = rate;
    utterance.pitch = 1;
    utterance.volume = 1;
    active = utterance; // Retain a reference until end/error/stop.
    stopButton.disabled = false;
    button.setAttribute('aria-pressed', 'true');
    status.textContent = '准备朗读 ' + term.label + (rate < 1 ? '（慢速）…' : '（正常语速）…');
    utterance.onstart = () => {
      if (active !== utterance) return;
      clearTimeout(startTimer);
      startTimer = null;
      status.textContent = '正在朗读 ' + term.label + (rate < 1 ? '（慢速）。' : '（正常语速）。');
    };
    utterance.onend = () => {
      if (active !== utterance) return;
      active = null;
      clearTimeout(startTimer);
      startTimer = null;
      resetButtons();
      status.textContent = term.label + ' 朗读结束，可再次点击。';
    };
    utterance.onerror = event => {
      if (active !== utterance) return;
      const unavailable = ['voice-unavailable', 'language-unavailable'].includes(event.error);
      stop(unavailable
        ? '英语语音不可用，请安装系统英语语音后重试；音标和释义仍可阅读。'
        : '朗读未能完成，请检查声音输出和英语语音设置后重试；部分语音需要联网。');
    };
    // Some engines fail silently when voice data is unavailable.
    startTimer = setTimeout(() => {
      if (active === utterance) stop('未能开始朗读，请检查声音输出和系统英语语音后重试。');
    }, 8000);
    try {
      synth.speak(utterance);
    } catch {
      stop('无法启动朗读，请检查浏览器和系统英语语音设置后重试。');
    }
  }

  function renderTerms() {
    stop();
    list.replaceChildren();
    const query = search.value.trim().toLocaleLowerCase();
    const pool = allTerms.checked ? GLOSSARY : pageTerms;
    const filtered = pool.filter(term =>
      [term.label, term.meaning, term.explanation].join(' ').toLocaleLowerCase().includes(query));
    byId('notesTermCount').textContent = (allTerms.checked ? '全课' : '本页') + ' · ' + filtered.length + ' 个';
    for (const term of filtered) {
      const card = document.createElement('article');
      card.className = 'notes-term';
      card.dataset.term = term.id;
      const heading = document.createElement('h4');
      const name = document.createElement('span');
      name.lang = 'en';
      name.textContent = term.label;
      const ipa = document.createElement('span');
      ipa.lang = 'en';
      ipa.className = 'notes-term-ipa';
      ipa.textContent = term.ipa;
      heading.append(name, ipa, document.createTextNode('（' + term.meaning + '）'));
      const definition = document.createElement('p');
      definition.textContent = term.explanation;
      const buttons = document.createElement('div');
      buttons.className = 'notes-term-buttons';
      for (const [rate, label, accessible] of [[1, '听发音', '正常语速'], [.65, '慢速', '慢速']]) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        button.dataset.pronounce = String(rate);
        button.setAttribute('aria-label', accessible + '朗读 ' + term.label);
        button.setAttribute('aria-pressed', 'false');
        button.disabled = !supported;
        button.addEventListener('click', () => speak(term, rate, button));
        buttons.append(button);
      }
      card.append(heading, definition, buttons);
      list.append(card);
    }
    if (!filtered.length) {
      const empty = document.createElement('p');
      empty.textContent = allTerms.checked ? '没有匹配的术语，请换一个关键词。' : '本页没有匹配项，可勾选“全课词库”继续查找。';
      list.append(empty);
    }
  }

  function render(slide) {
    stop();
    byId('notesText').textContent = slide.speaker_script || slide.notes;
    byId('notesSupplement').textContent = slide.speaker_supplement || '';
    byId('notesSupplementPanel').open = false;
    pageTerms = slide.terms || [];
    search.value = '';
    allTerms.checked = false;
    renderTerms();
    status.textContent = readyMessage();
    dialog.scrollTop = 0;
  }

  search.addEventListener('input', renderTerms);
  allTerms.addEventListener('change', renderTerms);
  stopButton.addEventListener('click', () => stop('已停止朗读。'));
  dialog.addEventListener('close', () => stop());
  dialog.addEventListener('cancel', () => stop());
  window.addEventListener('pagehide', () => stop());
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
  if (synth) synth.addEventListener('voiceschanged', () => {
    if (!active) status.textContent = readyMessage();
  });
  return {render, stop};
})();
