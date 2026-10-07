const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const context = vm.createContext({document: {querySelectorAll: () => []}});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/outing.js'), 'utf8'), context);
const trace = (architecture, weather = 'rain', budget = 300, intent = 'outing') =>
  vm.runInContext(`makeArchitectureTrace(${architecture}, ${JSON.stringify(weather)}, ${budget}, ${JSON.stringify(intent)})`, context);

test('single agent retrieves relevant documents and pairs tool requests with actual returns', () => {
  const events = trace(1);
  const retrieved = events.find(e => e.retrieved_documents);
  assert.ok(retrieved, 'RAG must return documents from the query');
  assert.deepEqual(Array.from(retrieved.retrieved_documents, d => d.id), ['D01', 'D02']);
  assert.ok(!retrieved.retrieved_documents.some(d => d.id === 'D03'));
  const requests = events.filter(e => e.request);
  assert.ok(requests.some(e => e.request.name === 'read_weather'));
  assert.ok(requests.some(e => e.request.name === 'read_catalog'));
  const cost = requests.find(e => e.request.name === 'calculate_cost' && e.request.arguments.place_id === 'P03');
  assert.ok(cost);
  for (const request of requests) {
    const requestIndex = events.indexOf(request);
    const response = events.find((e, index) => index > requestIndex && e.observation?.call_id === request.request.call_id);
    assert.ok(response, request.request.name);
  }
  assert.equal(events.find(e => e.observation?.call_id === cost.request.call_id).observation.total, 210);
  assert.ok(events.at(-1).result.citations.includes('D01'));
  assert.ok(events.at(-1).result.citations.includes('D02'));
});

test('budget intent loads only the cost skill; unclear intent stops before execution', () => {
  const budget = trace(5, 'rain', 200, 'budget');
  assert.ok(budget.some(e => e.skill === 'budget_check'));
  assert.ok(!budget.some(e => e.tool === 'read_weather'));
  assert.equal(budget.at(-1).result.status, 'cost_checked');
  const unclear = trace(5, 'rain', 300, 'unclear');
  assert.equal(unclear.at(-1).result.status, 'needs_clarification');
  assert.ok(!unclear.some(e => e.tool));
});

test('blackboard wakes dependent roles only after their required evidence is posted', () => {
  const events = trace(6);
  const updates = events.filter(e => e.board);
  assert.ok(updates.length >= 4);
  const pricing = events.findIndex(e => e.actor === 'cost' && e.phase.startsWith('发布'));
  const catalog = events.findIndex(e => e.board?.catalog);
  assert.ok(catalog >= 0 && pricing > catalog);
  assert.equal(events.filter(e => e.actor === 'cost' && e.phase.startsWith('发布')).length, 1);
  assert.equal(events.at(-1).result.place_id, 'P03');
});

test('planning follows one failed execution through feedback and re-execution before its only result', () => {
  const events = trace(3);
  const failure = events.findIndex(e => e.phase === '验收 v1');
  const reflection = events.findIndex(e => e.phase === '反思 Reflection');
  const executeV2 = events.findIndex(e => e.phase === '执行 v2');
  assert.ok(failure >= 0 && reflection > failure && executeV2 > reflection);
  assert.equal(events.filter(e => e.result).length, 1);
  assert.ok(!events.slice(0, failure).some(e => /通过/.test(e.title)));
});

test('ReAct review reports only the costs queried before stopping', () => {
  const sunny = trace(2, 'sun', 200).find(e => e.phase === '机制复盘').detail;
  assert.match(sunny, /湖畔公园/);
  assert.doesNotMatch(sunny, /自然馆|城市博物馆/);
  const rainy = trace(2, 'rain', 300).find(e => e.phase === '机制复盘').detail;
  assert.match(rainy, /自然馆/);
  assert.match(rainy, /城市博物馆/);
  assert.doesNotMatch(rainy, /湖畔公园/);
});

test('graph takes weather branches before pricing and validation', () => {
  for (const [weather, budget, status, place] of [
    ['rain', 300, 'recommended', 'P03'], ['rain', 200, 'no_solution', ''],
    ['sun', 200, 'recommended', 'P01'], ['sun', 100, 'no_solution', '']
  ]) {
    const events = trace(7, weather, budget);
    const nodes = events.filter(e => e.node).map(e => e.node);
    assert.ok(nodes.indexOf(weather === 'rain' ? 'indoor_filter' : 'all_places') > nodes.indexOf('weather'));
    assert.ok(nodes.indexOf('cost') > nodes.indexOf('catalog'));
    assert.ok(nodes.indexOf('validate') > nodes.indexOf('cost'));
    assert.equal(events.at(-1).result.status, status);
    assert.equal(events.at(-1).result.place_id, place);
  }
});

test('each architecture respects the same weather and full-cost budget constraints', () => {
  for (let architecture = 1; architecture <= 7; architecture++) {
    for (const [weather, budget, status, place] of [
      ['rain', 300, 'recommended', 'P03'], ['rain', 200, 'no_solution', ''], ['rain', 100, 'no_solution', ''],
      ['sun', 300, 'recommended', 'P01'], ['sun', 200, 'recommended', 'P01'], ['sun', 100, 'no_solution', '']
    ]) {
      const result = trace(architecture, weather, budget).at(-1).result;
      assert.equal(result.status, status, `architecture ${architecture}, ${weather}/${budget}`);
      assert.equal(result.place_id, place);
      if (place) assert.equal(result.total, place === 'P03' ? 210 : 180);
    }
  }
});

const teachingTrace = (arch, weather = 'rain', budget = 300) =>
  vm.runInContext(`makeArchitectureTrace(${arch}, ${JSON.stringify(weather)}, ${budget}, 'outing', true)`, context);

test('teaching planner responds to a changed budget and reuses collected facts', () => {
  const events = teachingTrace(3);
  const change = events.findIndex(e => e.budget_change);
  assert.ok(change > 0, 'user must change the budget during execution');
  assert.equal(events[change].budget_change.from, 300);
  assert.equal(events[change].budget_change.to, 200);
  assert.equal(events.find(e => e.phase === '执行 v1').proposed_place, 'P03');
  assert.ok(events.findIndex(e => e.phase === '计划 v2') > change);
  assert.equal(events.filter(e => e.tool === 'read_weather').length, 1);
  assert.equal(events.filter(e => e.tool === 'read_catalog').length, 1);
  assert.equal(events.at(-1).result.status, 'no_solution');
  assert.equal(events.at(-1).result.budget, 200);
});

test('teaching router switches skills before any weather query when user changes request', () => {
  const events = teachingTrace(5);
  const change = events.findIndex(e => e.intent_change);
  assert.ok(change > events.findIndex(e => e.skill === 'outing_plan'));
  assert.ok(events.findIndex(e => e.skill === 'budget_check') > change);
  assert.ok(!events.some(e => e.tool === 'read_weather'));
  assert.equal(events.at(-1).result.status, 'cost_checked');
});

test('teaching supervisor resolves partial recommendations using both weather and cost', () => {
  const events = teachingTrace(4);
  const weather = events.find(e => e.actor === 'weather');
  const cost = events.find(e => e.actor === 'cost');
  assert.equal(weather.proposed_place, 'P02');
  assert.equal(cost.proposed_place, 'P01');
  assert.equal(events.at(-1).result.place_id, 'P03');
});

test('blackboard shows the cost role waiting without publishing or changing the board', () => {
  const events = teachingTrace(6);
  const waiting = events.findIndex(e => e.waiting === 'catalog');
  const catalog = events.findIndex(e => e.actor === 'catalog' && e.phase.startsWith('发布'));
  const cost = events.findIndex(e => e.actor === 'cost' && e.phase.startsWith('触发'));
  assert.ok(waiting >= 0 && catalog > waiting && cost > catalog);
  assert.equal(events[waiting].board.version, 0);
  assert.equal(events[waiting].board.costs, null);
});
