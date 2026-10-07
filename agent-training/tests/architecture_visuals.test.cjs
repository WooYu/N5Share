const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = vm.createContext({document: {querySelectorAll: () => []}});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/outing.js'), 'utf8'), context);
const steps = (arch, weather = 'rain', budget = 300, intent = 'outing') => {
  assert.equal(vm.runInContext('typeof makeArchitecturePresentation', context), 'function', 'architecture playback must expose visual steps');
  return vm.runInContext(`makeArchitecturePresentation(${arch}, ${JSON.stringify(weather)}, ${budget}, ${JSON.stringify(intent)})`, context);
};

test('ReAct shows the observation returning to decision before changing the candidate', () => {
  const run = steps(2);
  const costly = run.findIndex(s => /310/.test(s.caption));
  assert.ok(costly >= 0);
  assert.ok(run[costly].edges.includes('tool-observation'));
  assert.ok(run[costly + 1].edges.includes('observation-decision'));
  assert.match(run[costly + 1].caption, /城市博物馆/);
  assert.match(run.at(-1).caption, /210/);
});

test('graph highlights the actual rain/sun and success/failure branches', () => {
  for (const [weather, budget, filter, exit] of [
    ['rain', 300, 'indoor_filter', 'recommend'], ['sun', 100, 'all_places', 'no_solution']
  ]) {
    const run = steps(7, weather, budget);
    const edges = run.flatMap(s => Array.from(s.edges));
    assert.ok(edges.includes(`catalog-${filter}`));
    assert.ok(edges.includes(`validate-${exit}`));
    assert.ok(!edges.includes(`catalog-${filter === 'all_places' ? 'indoor_filter' : 'all_places'}`));
    assert.ok(!edges.includes(`validate-${exit === 'recommend' ? 'no_solution' : 'recommend'}`));
  }
});

test('router selects only the cost skill or exits for clarification', () => {
  const cost = steps(5, 'rain', 200, 'budget');
  assert.ok(cost.some(s => s.edges.includes('router-budget_check')));
  assert.ok(!cost.some(s => s.nodes.includes('outing_plan')));
  const unclear = steps(5, 'rain', 300, 'unclear');
  assert.ok(unclear.at(-1).nodes.includes('clarify'));
  assert.ok(!unclear.some(s => s.nodes.includes('execute')));
});

test('blackboard distinguishes state-triggered reads from evidence writes', () => {
  const run = steps(6);
  const catalog = run.findIndex(s => s.edges.includes('catalog-board'));
  const trigger = run.findIndex(s => s.edges.includes('board-cost'));
  assert.ok(catalog >= 0 && trigger > catalog);
  assert.ok(run.some(s => s.edges.includes('cost-board')));
  assert.ok(run.some(s => s.edges.includes('board-summary')));
});

test('every architecture ends with the trace result and uses concise captions', () => {
  for (let arch = 1; arch <= 7; arch++) {
    for (const weather of ['rain', 'sun']) for (const budget of [100, 200, 300]) {
      const run = steps(arch, weather, budget);
      assert.ok(run.length > 2);
      assert.ok(run.at(-1).result);
      assert.ok(run.every(s => s.nodes.length && s.caption.length < 95));
    }
  }
});

test('single agent shows its unsupported park suggestion before weather corrects it', () => {
  const run = steps(1);
  const suggestion = run.findIndex(s => /先想到.*公园/.test(s.caption));
  const correction = run.findIndex(s => /有雨.*公园/.test(s.caption));
  assert.ok(suggestion >= 0 && correction > suggestion);
  assert.match(run.at(-1).caption, /博物馆/);
});

test('teaching playback exposes budget change and both routing decisions', () => {
  const plan = steps(3);
  assert.ok(plan.some(s => s.budget_change && /300.*200/.test(s.caption)));
  assert.match(plan.at(-1).caption, /200 元预算/);
  const router = steps(5);
  assert.ok(router.some(s => s.edges.includes('router-outing_plan')));
  assert.ok(router.some(s => s.edges.includes('router-budget_check')));
  assert.equal(router.at(-1).result.status, 'cost_checked');
});
