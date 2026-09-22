/* Optional authoring utility; the deck itself never needs a build step. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const N5 = {chapters: [], scenarios: {}};
const context = vm.createContext({window: {N5}, N5});
for (const file of ['assets/content-kit.js', ...fs.readdirSync(path.join(root,'slides')).filter(x=>x.endsWith('.js')).sort().map(x=>'slides/'+x)]) {
  vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
}
const seconds = n => n%60 ? `${Math.floor(n/60)} 分 ${n%60} 秒` : `${n/60} 分钟`;
const slides=N5.chapters.flatMap(ch=>ch.slides);
if(slides.length!==51 || slides.reduce((s,p)=>s+p.seconds,0)!==8880 || slides.reduce((s,p)=>s+p.coreSeconds,0)!==7200)throw Error('页数或时长不符，未写入讲义。');
const outline=['# N5 · 高级推理框架与多 Agent 协作 · 大纲\n\n51 页 · 完整路线 148 分钟 · 核心路线 120 分钟\n\n学习目标：按任务选择推理策略；设计角色、工具、消息、共享状态和结束条件。\n'];
const notes=['# N5 · 高级推理框架与多 Agent 协作 · 逐页讲师稿\n\n51 页 · 完整路线 148 分钟 · 核心路线 120 分钟。离线演示为预设教学剧本，工具读取课程合成资料。\n\n快捷键 O：目录；N：共屏讲稿；← →：翻页。私下备课请使用本文件。\n'];
for(const ch of N5.chapters){
  const full=ch.slides.reduce((n,s)=>n+s.seconds,0),core=ch.slides.reduce((n,s)=>n+s.coreSeconds,0);
  outline.push(`\n## ${ch.title}｜完整 ${seconds(full)} · 核心 ${core?seconds(core):'跳过'}\n\n`);
  for(const s of ch.slides){
    const trim=!s.coreSeconds?'核心路线跳过':s.coreSeconds<s.seconds?`核心 ${seconds(s.coreSeconds)}`:'核心页';
    outline.push(`- ${s.id} ${s.title}（${seconds(s.seconds)}；${trim}）${s.demo?' · 互动演示':''}\n`);
    notes.push(`\n## ${s.id} · ${s.title}\n\n${ch.title}｜${seconds(s.seconds)}｜${trim}\n\n${s.notes}\n`);
    if(s.quiz)notes.push(`\n判断题：${s.quiz.question}\n\n${s.quiz.options.map((x,i)=>`${String.fromCharCode(65+i)}. ${x}`).join('\n')}\n\n答案：${String.fromCharCode(65+s.quiz.answer)}。${s.quiz.explanation}\n`);
  }
}
fs.mkdirSync(path.join(root,'notes'),{recursive:true});
fs.writeFileSync(path.join(root,'notes/outline.md'),outline.join(''));
fs.writeFileSync(path.join(root,'notes/speaker-notes.md'),notes.join(''));
console.log('Exported 51 slides: outline + speaker notes (148 / 120 minutes).');
