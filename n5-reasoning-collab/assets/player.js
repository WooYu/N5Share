/* Deck navigation is deliberately independent of any build tool or server. */
(() => {
  'use strict';
  const N = window.N5;
  const $ = (s) => document.querySelector(s);
  const escape = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const duration = seconds => seconds % 60 ? `${Math.floor(seconds / 60)}分${seconds % 60}秒` : `${seconds / 60}分钟`;
  const slides = N.chapters.flatMap(ch => ch.slides.map(s => ({...s, chapter:ch.title, chapterId:ch.id})));
  const stage = $('#stage');
  let current = 0;
  let core = false;
  const route = () => slides.map((s,i) => ({s,i})).filter(({s}) => !core || s.coreSeconds > 0).map(({i}) => i);

  if (slides.length !== 51 || slides.reduce((n,s) => n+s.seconds,0) !== 8880 || slides.reduce((n,s) => n+s.coreSeconds,0) !== 7200) {
    stage.innerHTML = '<section class="slide active"><h2>课程文件不完整</h2><p>请完整解压培训包，再打开 index.html。</p></section>';
    throw new Error('N5: expected 51 slides, 148 minutes and 120-minute core route.');
  }
  slides.forEach((s,i) => {
    const section = document.createElement('section');
    section.id = s.id;
    section.className = `slide${i === 0 ? ' cover' : ''}${s.demo ? ' demo-slide' : ''}`;
    section.setAttribute('aria-label', `${s.id} ${s.title}`);
    section.setAttribute('aria-hidden', 'true');
    section.inert = true;
    const trim = s.coreSeconds === 0 ? '核心路线可跳过' : s.coreSeconds < s.seconds ? `核心路线 ${duration(s.coreSeconds)}` : '核心页';
    section.innerHTML = `<div class="slide-eyebrow"><b>N5 / ${String(Number(s.chapterId)).padStart(2,'0')} · ${escape(s.chapter)}</b><span class="trim-note">${duration(s.seconds)} · ${trim}</span></div><h2>${escape(s.title)}</h2><div class="slide-content">${s.html}</div><footer class="slide-footer"><span>高级推理框架与多 Agent 协作 · 同一任务，逐层升级</span><span>${String(i+1).padStart(2,'0')} / 51</span></footer>`;
    const body = section.querySelector('.slide-content');
    if (s.quiz) {
      const q = s.quiz;
      const quiz = document.createElement('div');
      quiz.className = 'quiz';
      quiz.innerHTML = `<div class="quiz-question">${escape(q.question)}</div><div class="quiz-options">${q.options.map((o,j) => `<button type="button" data-answer="${j}">${String.fromCharCode(65+j)}. ${escape(o)}</button>`).join('')}</div><div class="quiz-feedback" role="status"></div>`;
      quiz.addEventListener('click', e => {
        const button = e.target.closest('[data-answer]');
        if (!button) return;
        quiz.querySelectorAll('button').forEach(b => b.classList.remove('correct','incorrect'));
        const correct = Number(button.dataset.answer) === q.answer;
        button.classList.add(correct ? 'correct' : 'incorrect');
        quiz.querySelector('.quiz-feedback').textContent = `${correct ? '正确。' : '再想一想。'}${q.explanation}`;
      });
      body.append(quiz);
      const printed = document.createElement('div');
      printed.className = 'quiz-print';
      printed.hidden = true;
      printed.innerHTML = `<p>${escape(q.question)}</p><ol type="A">${q.options.map(o => `<li>${escape(o)}</li>`).join('')}</ol><p class="small">参考答案：${String.fromCharCode(65+q.answer)} · ${escape(q.explanation)}</p>`;
      body.append(printed);
    }
    if (s.demo) {
      const host = document.createElement('div');
      host.className = 'demo';
      host.dataset.scenario = s.demo;
      host.setAttribute('aria-label', `${s.title} 互动演示`);
      body.append(host);
      const printed = document.createElement('div');
      printed.className = 'print-demo';
      printed.innerHTML = `<b>互动演示 · ${escape(N.scenarios[s.demo]?.title || s.title)}</b><p>在 HTML 中逐步执行、回看角色交接和共享状态。</p><p>${escape(({react:'天气观察 → 筛选场馆 → 计算完整费用 → 核对预算 → 验收。',plan:'先执行计划 v1；雨天的失败揭示天气与场馆选择之间的前置依赖。',supervisor:'主管接收执行角色的回报，再决定下一位执行者。',hierarchical:'信息组与财务组局部汇总，总管根据两份组报告验收。',swarm:'对等角色按观察交接控制权，宿主核对终止条件。',dual:'计划 v1 → 雨天失败 → 回传观察 → 规划方修订 v2 → 重新执行。',review:'四维审查 → 汇总 → 真实冲突仲裁 → 驳回未证实顾虑 → 修订 → 复审。'})[s.demo])}</p><p class="small">离线运行的是预设教学剧本，工具数据均为课程合成样本。</p>`;
      body.append(printed);
    }
    stage.append(section);
  });
  const nodes = [...stage.children];
  function fit() {
    const box = $('#viewport');
    document.documentElement.style.setProperty('--stage-scale', Math.min(box.clientWidth / 1440, box.clientHeight / 810));
  }
  function populateOutline() {
    $('#outlineList').innerHTML = N.chapters.map(ch => `<section class="outline-chapter"><h3>${escape(ch.title)} <span class="small">/ ${duration(ch.slides.reduce((n,s) => n+(core?s.coreSeconds:s.seconds),0))}</span></h3>${ch.slides.map(s => `<button type="button" data-page="${s.id}" class="${slides[current].id===s.id?'current ':''}${core&&!s.coreSeconds?'skipped':''}"><span>${s.id} · ${escape(s.title)}</span><span>${core && !s.coreSeconds ? '跳过' : duration(core?s.coreSeconds:s.seconds)}</span></button>`).join('')}</section>`).join('');
  }
  function show(index, updateHash = true) {
    const list = route();
    index = Math.max(0,Math.min(slides.length-1,index));
    if (!list.includes(index)) index = list.find(i => i >= index) ?? list[list.length-1];
    nodes[current]?.classList.remove('active');
    if(nodes[current]) { nodes[current].inert = true; nodes[current].setAttribute('aria-hidden','true'); }
    current = index;
    const s = slides[index];
    const serviceLink = $('#serviceEdition');
    serviceLink.hidden = location.protocol !== 'file:';
    serviceLink.href = `http://127.0.0.1:8775/#${s.id}`;
    serviceLink.title = '先双击 start-demo.cmd 启动本地服务，再打开此链接使用真实模型。';
    nodes[index].classList.add('active');
    nodes[index].inert = false;
    nodes[index].setAttribute('aria-hidden','false');
    $('#chapterLabel').textContent = `${s.chapter} · ${core?'核心路线':'完整路线'}`;
    $('#pageCounter').textContent = `${String(index+1).padStart(2,'0')} / 51`;
    const before = list.filter(i=>i<index).reduce((n,i)=>n+(core?slides[i].coreSeconds:slides[i].seconds),0);
    $('#durationLabel').textContent = `本页 ${duration(core?s.coreSeconds:s.seconds)} · ${Math.floor(before/60)} / ${core?120:148} 分钟`;
    $('#previous').disabled = index === list[0];
    $('#next').disabled = index === list[list.length-1];
    $('#progress').setAttribute('aria-valuenow',index+1);
    $('#progress i').style.width = `${(list.indexOf(index)+1)/list.length*100}%`;
    if (updateHash) history.replaceState(null,'',`#${s.id}`);
    $('#notesContent').innerHTML = `<h3>${escape(s.id+' · '+s.title)}</h3>${escape(s.notes)}`;
    document.title = `${s.id} · ${s.title} | N5`;
    if(s.demo) N.DemoPlayer.mount(nodes[index].querySelector('.demo'));
    document.dispatchEvent(new CustomEvent('n5:slidechange',{detail:{id:s.id}}));
  }
  function move(delta) {
    const list = route();
    show(list[Math.max(0,Math.min(list.length-1,list.indexOf(current)+delta))]);
  }
  function openDialog(id) {
    if(id==='outlineDialog') populateOutline();
    const dialog = document.getElementById(id);
    if(!dialog.open) dialog.showModal();
  }
  async function fullscreen() {
    try { if(document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { $('#durationLabel').textContent = '浏览器未允许全屏，可使用 F11'; }
  }
  document.querySelectorAll('[data-open]').forEach(b => b.addEventListener('click',()=>openDialog(b.dataset.open)));
  document.addEventListener('click', e => {
    const button = e.target.closest('[data-handout]');
    if (!button) return;
    const handout = N.handouts?.[button.dataset.handout];
    if (!handout) return;
    $('#handoutTitle').textContent = handout.title;
    $('#handoutContent').innerHTML = handout.html;
    openDialog('handoutDialog');
    $('#handoutDialog').scrollTop = 0;
  });
  document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click',()=>b.closest('dialog').close()));
  document.querySelectorAll('dialog').forEach(d => d.addEventListener('click',e => { if(e.target===d) { const r=d.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close(); } }));
  $('#outlineList').addEventListener('click',e => { const b=e.target.closest('[data-page]'); if(!b)return; const i=slides.findIndex(s=>s.id===b.dataset.page); if(core && !slides[i].coreSeconds){core=false;$('#coreRoute').checked=false;} show(i);$('#outlineDialog').close(); });
  $('#coreRoute').addEventListener('change',e=>{core=e.target.checked;show(current);});
  $('#previous').addEventListener('click',()=>move(-1));
  $('#next').addEventListener('click',()=>move(1));
  $('#fullscreen').addEventListener('click',fullscreen);
  document.addEventListener('keydown',e => {
    if(e.ctrlKey||e.metaKey||e.altKey||document.querySelector('dialog[open]'))return;
    if(e.target.closest('input,select,textarea,[contenteditable=true]'))return;
    if((e.key===' '||e.key==='Enter')&&e.target.closest('button,a'))return;
    const key=e.key.toLowerCase();
    const actions={arrowright:()=>move(1),pagedown:()=>move(1),' ':()=>move(1),arrowleft:()=>move(-1),pageup:()=>move(-1),home:()=>show(0),end:()=>show(50),o:()=>openDialog('outlineDialog'),n:()=>openDialog('notesDialog'),f:fullscreen,'?':()=>openDialog('helpDialog')};
    if(actions[key]){e.preventDefault();actions[key]();}
  });
  addEventListener('hashchange',()=>{const i=slides.findIndex(s=>s.id===location.hash.slice(1));if(i>=0)show(i,false);});
  addEventListener('resize',fit);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)N.DemoPlayer.pauseAll();});
  addEventListener('beforeprint',()=>N.DemoPlayer.pauseAll());
  N.deck = {slides,show,get current(){return current;}};
  fit();
  show(Math.max(0,slides.findIndex(s=>s.id===location.hash.slice(1))));
})();
