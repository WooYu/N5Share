/* The event contract is shared by authored offline scripts and live runs. */
(() => {
  'use strict';
  const N = window.N5;
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clone = value => JSON.parse(JSON.stringify(value));
  const kinds = {thought:'决策摘要',action:'工具请求',observation:'事实回填',plan:'制定计划',reflection:'反思结论',dispatch:'派发 / 交接',finding:'审查发现',conflict:'检测冲突',arbitration:'基于事实仲裁',revision:'修订',review:'验收 / 复审',report:'提交报告',done:'运行结束'};
  const statuses = {running:'运行中',completed:'验收通过',needs_human:'需要人工介入',failed:'运行失败',cancelled:'已取消',stopped:'受控停止'};
  const players = new Map();
  let healthPromise;
  const isLocalHttp = () => location.protocol === 'http:' && location.hostname === '127.0.0.1';
  async function api(path,options={}) {
    const response = await fetch(path,{...options,signal:AbortSignal.timeout(7000),headers:{'Content-Type':'application/json',...(options.headers||{})}});
    let body;
    try { body = await response.json(); } catch { throw new Error('服务返回了非 JSON 响应；请使用本课件的 Python 服务。'); }
    if(!response.ok)throw new Error(body.error || `本地服务返回 HTTP ${response.status}`);
    return body;
  }
  function health(force=false) {
    if(force)healthPromise=null;
    if(!healthPromise) healthPromise = isLocalHttp() ? api('/api/health').catch(()=>({available:false,reason:'本地真实模型服务未就绪，请运行 start-demo.cmd。'})) : Promise.resolve({available:false,reason:'真实运行：运行 start-demo.cmd 后，用 127.0.0.1 地址打开课件。'});
    return healthPromise;
  }
  class Demo {
    constructor(root) {
      this.root=root;
      this.scenario=root.dataset.scenario;
      this.definition=N.scenarios[this.scenario];
      this.events=[];this.cursor=-1;this.timer=null;this.poll=null;this.runId=null;this.running=false;this.mode='offline';this.generation=0;this.ready=false;this.cancelPending=false;
      if(!this.definition){root.textContent='剧本文件缺失，请完整解压课件。';return;}
      const review=this.scenario==='review';
      root.innerHTML=`<div class="demo-toolbar"><span class="mode-badge">预设教学剧本</span><label ${review?'hidden':''}>天气 <select data-weather aria-label="仿真天气"><option value="rain">雨天</option><option value="sun">晴天</option></select></label><label ${review?'hidden':''}>预算 <select data-budget aria-label="出游预算"><option value="300">300 元</option><option value="200">200 元</option><option value="100">100 元</option></select></label><button type="button" class="primary" data-step>下一步</button><button type="button" data-auto>自动播放</button><button type="button" data-reset>重置</button><button type="button" data-live disabled>真实运行</button><button type="button" data-cancel hidden>取消运行</button><span data-count>0 / 0</span></div><div class="demo-connection"><span data-connection role="status">正在检查真实模型服务…</span><a data-service-link>打开服务版 ↗</a><button type="button" data-recheck>重新检测</button></div><div class="demo-status"><span data-status role="status" aria-live="polite">准备就绪</span><span data-metrics></span></div><div class="role-map" aria-label="角色与控制权"></div><div class="control-route"></div><div class="event-layout"><div class="event-list" aria-label="事件列表"></div><div class="event-detail" aria-live="polite"></div></div><div class="shared-state"><h4><span>共享状态 · 当前事件快照</span><span>绿色标出本步变化 · 字段旁标写入者</span></h4><div class="state-grid"></div></div>`;
      this.$=s=>root.querySelector(s);
      this.$('[data-step]').addEventListener('click',()=>this.next());
      this.$('[data-auto]').addEventListener('click',()=>this.toggleAuto());
      this.$('[data-reset]').addEventListener('click',()=>this.reset());
      this.$('[data-weather]').addEventListener('change',()=>this.reset());
      this.$('[data-budget]').addEventListener('change',()=>this.reset());
      this.$('[data-live]').addEventListener('click',()=>this.startLive());
      this.$('[data-cancel]').addEventListener('click',()=>this.cancel());
      this.$('[data-recheck]').addEventListener('click',()=>this.checkConnection(true));
      this.$('.event-list').addEventListener('click',e=>{const b=e.target.closest('[data-event]');if(!b)return;this.pause();this.cursor=Number(b.dataset.event);this.render();const item=this.events[this.cursor];this.setStatus(`历史快照 ${item.id} · ${item.kind==='done'?this.outcome(item):'此时正在'+(kinds[item.kind]||item.kind)}${this.running?' · 真实运行仍在后台继续':''}`);});
      this.reset();
      this.checkConnection();
    }
    async checkConnection(force=false){
      if(this.checking)return;
      this.checking=true;this.$('[data-recheck]').disabled=true;
      try{const result=await health(force);players.forEach(p=>p.applyConnection(result));this.applyConnection(result);}
      finally{this.checking=false;this.$('[data-recheck]').disabled=false;}
    }
    applyConnection(result){
      this.ready=!!result.available;this.healthReason=result.reason||'DeepSeek 已就绪；工具仍读取课程合成资料。';
      const local=isLocalHttp();
      this.$('[data-live]').title=this.healthReason;
      this.$('.demo-connection').hidden=this.ready;
      this.root.classList.toggle('unavailable',!this.ready);
      this.$('[data-connection]').textContent=!local?'当前为离线版：先双击 start-demo.cmd 启动本地服务，再打开服务版。':/未配置/.test(this.healthReason)?'未配置 DeepSeek 凭据：双击 configure-deepseek.cmd 在本机输入密钥，然后重新检测。':this.healthReason;
      this.$('[data-service-link]').hidden=local;
      this.$('[data-service-link]').href=`http://127.0.0.1:8775/#${this.root.closest('.slide').id}`;
      this.$('[data-recheck]').hidden=!local;
      this.updateControls();
      if(this.cursor<0&&!this.running)this.setStatus(this.ready?'可单步演示，也可真实运行。':this.healthReason);
    }
    label(actor){return this.definition.roles.find(r=>r.id===actor)?.label || ({host:'宿主程序',executor:'执行 Agent',planner:'规划 Agent'})[actor] || actor || '待开始';}
    outcome(event){return ['offline_teaching_workflow','synthetic_review_workflow'].includes(event.payload?.scope)?'教学规则审查完成（未测试真实代码）':statuses[event.payload?.status]||'剧本结束';}
    options(){return {weather:this.$('[data-weather]').value,budget:Number(this.$('[data-budget]').value)};}
    setStatus(message,error=false){this.$('[data-status]').textContent=message;this.$('.demo-status').classList.toggle('error',error);}
    pause(){if(this.timer)clearInterval(this.timer);this.timer=null;this.$('[data-auto]').textContent='自动播放';}
    async reset(){
      if(this.running){await this.cancel();if(this.running)return;}
      this.generation++;this.pause();clearTimeout(this.poll);this.poll=null;
      this.mode='offline';this.runId=null;this.cursor=-1;
      const script=this.definition.create(this.options());
      this.events=script.events;this.initial=clone(script.initialState||{});
      this.$('[data-metrics]').textContent='';
      this.setStatus('预设教学剧本 · 点击下一步，或选择任意事件回看。');
      this.render();
    }
    updateControls(){
      this.$('[data-step]').disabled=this.running||this.cursor>=this.events.length-1;
      this.$('[data-auto]').disabled=this.running||!this.events.length;
      this.$('[data-live]').disabled=this.running||!this.ready;
      this.$('[data-cancel]').hidden=!this.running;
      this.$('[data-weather]').disabled=this.running;
      this.$('[data-budget]').disabled=this.running;
      this.$('[data-count]').textContent=`${this.cursor+1} / ${this.events.length}`;
      const badge=this.$('.mode-badge');badge.classList.toggle('live',this.mode==='live');badge.textContent=this.mode==='live'?'真实模型 · DeepSeek':'预设教学剧本';
    }
    next(){
      if(this.running||this.cursor>=this.events.length-1){this.pause();return;}
      this.cursor++;this.render();
      const event=this.events[this.cursor];
      if(this.mode==='offline')this.setStatus(event.kind==='done'?`${this.outcome(event)} · 预设教学剧本`:'预设教学剧本 · 事实来自课程合成资料。');
      if(this.cursor>=this.events.length-1)this.pause();
    }
    toggleAuto(){if(this.timer){this.pause();return;}if(this.cursor>=this.events.length-1)this.cursor=-1;this.next();if(this.cursor<this.events.length-1){this.$('[data-auto]').textContent='暂停播放';this.timer=setInterval(()=>this.next(),1300);}}
    render(){
      const e=this.events[this.cursor];
      const prior=this.cursor>0?this.events[this.cursor-1]:null;
      this.$('.role-map').innerHTML=this.definition.roles.map(r=>`<div class="${e&&(e.highlight||[e.actor]).includes(r.id)?'current':''}">${escape(r.label)}<small>${escape(r.id)}</small></div>`).join('');
      const state=e?.state_after||this.initial||{};
      const control=state.control||state.control_owner||state.current_actor;
      this.$('.control-route').textContent=e?`${prior&&prior.actor!==e.actor?this.label(prior.actor)+' → ':''}${this.label(e.actor)} · ${kinds[e.kind]||e.kind}${control?' · 控制权：'+this.label(control):''}`:'观察重点：谁在行动 → 交给谁 → 哪些状态发生变化';
      this.$('.event-list').innerHTML=this.events.map((item,i)=>`<button type="button" data-event="${i}" class="${i===this.cursor?'selected':i>this.cursor?'future':''}" ${i===this.cursor?'aria-current="step"':''}><small>${escape(item.id)}</small>${escape(item.title)}</button>`).join('');
      const list=this.$('.event-list'),selected=list.querySelector('.selected');
      if(selected){if(selected.offsetTop<list.scrollTop)list.scrollTop=selected.offsetTop;else if(selected.offsetTop+selected.offsetHeight>list.scrollTop+list.clientHeight)list.scrollTop=selected.offsetTop+selected.offsetHeight-list.clientHeight;}
      this.$('.event-detail').innerHTML=e?`<div class="event-kind">${escape(kinds[e.kind]||e.kind)} / ${escape(this.label(e.actor))}</div><h3>${escape(e.title)}</h3><p>${escape(e.detail||'')}</p><details><summary>查看结构化事件</summary><pre>${escape(JSON.stringify(e,null,2))}</pre></details>`:'<div class="event-kind">READY / 准备开始</div><h3>先看谁拿着控制权</h3><p>每走一步，核对工具事实、角色交接和状态变化。点击左侧事件可回到该时刻。</p>';
      const previous=prior?.state_after||this.initial||{};
      const writers=e?.writers||{};
      this.$('.state-grid').innerHTML=Object.entries(state).map(([key,value])=>{
        const changed=!!e&&JSON.stringify(previous[key])!==JSON.stringify(value);
        const text=typeof value==='string'?value:JSON.stringify(value);
        return `<div class="state-field${changed?' changed':''}"><strong>${escape(key)}</strong>${writers[key]?`<em>← ${escape(this.label(writers[key]))}</em>`:''}<span>${escape(text??'—')}</span></div>`;
      }).join('')||'<span class="small">还没有共享状态。</span>';
      this.updateControls();
    }
    async startLive(){
      if(this.running||!this.ready)return;
      this.pause();clearTimeout(this.poll);const generation=++this.generation;
      this.mode='live';this.running=true;this.cancelPending=false;this.events=[];this.cursor=-1;this.initial={constraints:this.options()};this.runId=null;this.render();
      this.setStatus('正在启动 DeepSeek 运行；不会回退到离线剧本。');
      try{
        const result=await api('/api/runs',{method:'POST',body:JSON.stringify({scenario:this.scenario,...this.options()})});
        if(!result.run_id)throw new Error('服务未返回运行编号。');
        this.runId=result.run_id;
        if(generation!==this.generation){await api(`/api/runs/${encodeURIComponent(result.run_id)}/cancel`,{method:'POST',body:'{}'});return;}
        if(this.cancelPending){this.cancelPending=false;await this.cancel();return;}
        await this.refresh(generation);
      }catch(error){if(generation===this.generation){this.running=false;this.setStatus(error.message,true);this.updateControls();}}
    }
    async refresh(generation){
      if(generation!==this.generation||!this.runId)return;
      try{
        const result=await api(`/api/runs/${encodeURIComponent(this.runId)}`);
        if(generation!==this.generation)return;
        const follow=this.cursor===this.events.length-1;
        this.events=Array.isArray(result.events)?result.events:[];
        if(follow||this.cursor<0)this.cursor=this.events.length-1;
        this.running=result.status==='running';
        const m=result.metrics||{};
        this.$('[data-metrics]').textContent=`模型 ${m.model_calls||0}/12 · 工具 ${m.tool_calls||0}/20 · ${Math.round(m.elapsed_seconds||0)} 秒 · token ${(m.input_tokens||0)+(m.output_tokens||0)}`;
        const last=this.events.at(-1);
        const outcome=result.status==='completed'&&last?.kind==='done'?this.outcome(last):statuses[result.status]||result.status;
        this.setStatus(result.error||`${outcome} · 真实模型输出，工具使用合成资料。`,!!result.error);
        this.render();
        if(this.running)this.poll=setTimeout(()=>this.refresh(generation),850);
      }catch(error){
        if(generation!==this.generation)return;
        this.setStatus(`读取运行失败：${error.message} 正在请求取消。`,true);
        await this.cancel(true);
      }
    }
    async cancel(preserveError=false){
      if(!this.running)return;
      if(!this.runId){this.cancelPending=true;this.setStatus('已记录取消请求；取得运行编号后立即停止。');return;}
      clearTimeout(this.poll);this.pause();
      const generation=++this.generation;
      const priorError=preserveError?this.$('[data-status]').textContent:'';
      let confirmed=false;
      this.$('[data-cancel]').disabled=true;
      try{
        const result=await api(`/api/runs/${encodeURIComponent(this.runId)}/cancel`,{method:'POST',body:'{}'});
        if(generation!==this.generation)return;
        this.running=result.status==='running';
        if(this.running){this.setStatus('已请求取消，等待当前调用停止。');this.poll=setTimeout(()=>this.refresh(generation),500);}
        else {
          confirmed=true;
          const snapshot=await api(`/api/runs/${encodeURIComponent(this.runId)}`);
          if(generation!==this.generation)return;
          this.events=Array.isArray(snapshot.events)?snapshot.events:this.events;this.cursor=this.events.length-1;this.render();
          this.setStatus(priorError?`${priorError} 已确认结束。`:result.status==='cancelled'?'已取消真实运行；终止快照已保留。':`运行已结束：${statuses[result.status]||result.status}`,!!priorError);
        }
      }catch(error){
        if(generation!==this.generation)return;
        if(confirmed){this.running=false;this.setStatus(`运行已确认结束，终止快照未能读取：${error.message}`,true);}
        else{this.setStatus(`取消尚未确认：${error.message}；可再次取消。`,true);this.poll=setTimeout(()=>this.refresh(generation),2500);}
      }
      finally{this.$('[data-cancel]').disabled=false;this.updateControls();}
    }
  }
  N.DemoPlayer={mount(root){if(!players.has(root))players.set(root,new Demo(root));return players.get(root);},pauseAll(){players.forEach(p=>p.pause());}};
  document.addEventListener('n5:slidechange',()=>N.DemoPlayer.pauseAll());
})();
