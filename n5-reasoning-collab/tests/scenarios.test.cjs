const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function load() {
  const context = vm.createContext({ window: { N5: { chapters: [], scenarios: {} } } });
  for (const name of ['outing-scripts.js', 'dual-agent-script.js', 'code-review-script.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'data', name), 'utf8'), context, { filename: name });
  }
  return context.window.N5;
}
const plain = value => JSON.parse(JSON.stringify(value));

test('registers seven independent offline scenarios and the four correct venue totals', () => {
  const n5 = load();
  assert.deepEqual(Object.keys(n5.scenarios).sort(), ['dual', 'hierarchical', 'plan', 'react', 'review', 'supervisor', 'swarm']);
  assert.deepEqual(plain(n5.outingData.venues.map(v => [v.id, v.total])), [['P01', 120], ['P02', 270], ['P03', 210], ['P04', 200]]);
});

for (const scenario of ['react', 'plan', 'supervisor', 'hierarchical', 'swarm', 'dual']) {
  for (const weather of ['sun', 'rain']) {
    for (const budget of [300, 200, 100]) {
      test(`${scenario}: ${weather} / ${budget} preserves facts, snapshots, ownership and acceptance`, () => {
        const definition = load().scenarios[scenario];
        const result = definition.create({ weather, budget });
        const ids = new Set();
        const actors = new Set(definition.roles.map(role => role.id));
        let lastVersion = 0;
        let actions = 0;
        let observations = 0;
        for (const event of result.events) {
          assert.ok(!ids.has(event.id));
          ids.add(event.id);
          assert.ok(actors.has(event.actor), `unknown actor ${event.actor}`);
          for (const actor of event.highlight) assert.ok(actors.has(actor));
          assert.ok(event.state_after.version > lastVersion);
          lastVersion = event.state_after.version;
          for (const field of Object.keys(event.state_after)) assert.ok(actors.has(event.writers[field]), `writer for ${field}`);
          assert.ok(Object.isFrozen(event));
          assert.ok(Object.isFrozen(event.state_after));
          if (event.kind === 'action') actions += 1;
          if (event.kind === 'observation') {
            observations += 1;
            assert.equal(event.actor, 'host');
            assert.equal(event.payload.source, 'synthetic_tool');
            assert.ok(event.payload.request_id);
            assert.ok(observations <= actions);
          }
          if (event.kind === 'done') assert.equal(event.actor, 'host');
        }
        assert.equal(actions, observations);
        assert.equal(result.events.filter(e => e.kind === 'done').length, 1);
        const final = result.events.at(-1);
        const expectedFailure = budget === 100 || (scenario === 'plan' && weather === 'rain');
        assert.equal(final.payload.status, expectedFailure ? 'needs_human' : 'completed');
        assert.equal(final.state_after.status, final.payload.status);
        if (expectedFailure) {
          assert.equal(final.state_after.itinerary, null);
          assert.ok(result.events.every(e => e.payload.status !== 'completed'));
        } else {
          assert.ok(final.state_after.budget_used <= budget);
          assert.equal(final.state_after.weather.condition, weather);
          if (weather === 'rain') {
            assert.equal(final.state_after.selected.type, 'indoor');
            assert.equal(final.state_after.selected.id, budget === 300 ? 'P03' : 'P04');
            assert.equal(final.state_after.budget_used, budget === 300 ? 210 : 200);
          }
          assert.equal(final.payload.acceptance.cost_matches, true);
          assert.equal(final.payload.acceptance.weather_compatible, true);
          assert.equal(final.payload.acceptance.within_budget, true);
        }
        const original = JSON.stringify(result.events[0]);
        definition.create({ weather: weather === 'rain' ? 'sun' : 'rain', budget: 100 });
        assert.equal(JSON.stringify(result.events[0]), original);
        assert.equal(result.initialState.status, 'running');
        assert.equal(result.initialState.weather, null);
        assert.equal(result.initialState.itinerary, null);
      });
    }
  }
}

test('dual executor returns failure to planner before version 2 and never invents a sunny failure', () => {
  const dual = load().scenarios.dual;
  const events = dual.create({ weather: 'rain', budget: 300 }).events;
  const report = events.findIndex(e => e.kind === 'report' && e.payload.code === 'OUTDOOR_IN_RAIN');
  const reflection = events.findIndex(e => e.kind === 'reflection');
  const revision = events.findIndex(e => e.kind === 'revision');
  assert.ok(report > 0 && reflection > report && revision > reflection);
  assert.equal(events[report].actor, 'executor');
  assert.equal(events[report].payload.to, 'planner');
  assert.equal(events[revision].actor, 'planner');
  assert.equal(events[revision].state_after.plan_version, 2);
  const sunny = dual.create({ weather: 'sun', budget: 300 }).events;
  assert.ok(sunny.every(e => e.kind !== 'reflection' && e.kind !== 'revision'));
});

test('hierarchy has two isolated group reports and swarm really transfers peer control', () => {
  const scenarios = load().scenarios;
  const hierarchy = scenarios.hierarchical.create({ weather: 'rain', budget: 200 }).events;
  assert.ok(hierarchy.some(e => e.actor === 'info_lead' && e.kind === 'report'));
  assert.ok(hierarchy.some(e => e.actor === 'finance_lead' && e.kind === 'report'));
  assert.ok(hierarchy.some(e => e.actor === 'ticket' && e.kind === 'report'));
  const swarm = scenarios.swarm.create({ weather: 'rain', budget: 200 }).events;
  const handoffs = swarm.filter(e => e.kind === 'dispatch' && e.payload.intent === 'handoff');
  assert.ok(handoffs.length >= 2);
  for (const event of handoffs) {
    assert.notEqual(event.payload.from, event.payload.to);
    assert.equal(event.state_after.control, event.payload.to);
  }
  assert.equal(swarm.at(-1).actor, 'host');
});

test('review uses four-way fan-out, fact-based arbitration, revision and explicitly scripted re-review', () => {
  const n5 = load();
  const result = n5.scenarios.review.create({});
  const events = result.events;
  const start = events.find(e => e.kind === 'dispatch' && e.payload.intent === 'fan_out');
  assert.equal(start.payload.to.length, 4);
  assert.equal(start.highlight.length, 4);
  const fanIn = events.findIndex(e => e.kind === 'report' && e.payload.intent === 'fan_in');
  assert.ok(events.slice(0, fanIn).filter(e => e.kind === 'finding').length >= 4);
  const arbitrations = events.filter(e => e.kind === 'arbitration');
  assert.equal(arbitrations.length, 2);
  assert.equal(arbitrations[0].payload.decision.audit, 'async_durable_fallback');
  assert.equal(arbitrations[0].state_after.business_facts.sensitive_order_amounts, true);
  assert.equal(arbitrations[0].state_after.business_facts.audit_required, true);
  assert.equal(arbitrations[1].payload.decision, 'reject_unmeasured_objection');
  assert.ok(!JSON.stringify(events).includes('百万倍'));
  assert.ok(!JSON.stringify(events).includes('六个数量级'));
  const revision = events.findIndex(e => e.kind === 'revision');
  const secondReviews = events.filter((e, i) => i > revision && e.kind === 'review');
  assert.equal(secondReviews.length, 4);
  assert.ok(secondReviews.every(e => e.payload.scripted === true && e.payload.tests_executed === false));
  assert.equal(events.at(-1).payload.status, 'completed');
  assert.equal(events.at(-1).state_after.tests_executed, false);
  assert.equal(result.initialState.findings.length, 0);
  assert.ok(events.every(e => Object.isFrozen(e.state_after) && Object.isFrozen(e.writers)));
  assert.ok(n5.reviewData.originalDiff.includes('selectByAmountRange'));
  assert.ok(n5.reviewData.revisedDiff.includes('AmountRange'));
  assert.ok(n5.reviewData.permissions && n5.reviewData.schema && n5.reviewData.testCases);
});

test('invalid outing conditions reject explicitly', () => {
  const scenarios = load().scenarios;
  for (const id of ['react', 'plan', 'supervisor', 'hierarchical', 'swarm', 'dual']) {
    assert.throws(() => scenarios[id].create({ weather: 'snow', budget: 300 }), /weather/);
    assert.throws(() => scenarios[id].create({ weather: 'rain', budget: 0 }), /budget/);
  }
});

test('supervisor retains control on delegation and all scenario events use the documented kinds', () => {
  const scenarios = load().scenarios;
  const allowed = new Set(['thought', 'action', 'observation', 'plan', 'reflection', 'dispatch', 'finding', 'conflict', 'arbitration', 'revision', 'review', 'report', 'done']);
  for (const [id, definition] of Object.entries(scenarios)) {
    const result = definition.create({ weather: 'rain', budget: 300 });
    const actors = new Set(definition.roles.map(role => role.id));
    for (const event of result.events) {
      assert.ok(allowed.has(event.kind), `${id}: ${event.kind}`);
      assert.ok(actors.has(event.state_after.control), `${id}: control owner`);
      for (const field of Object.keys(event.state_after)) assert.ok(actors.has(event.writers[field]));
      if (id === 'supervisor' && event.kind !== 'done') assert.equal(event.state_after.control, 'supervisor');
    }
  }
});

test('supervisor receives each candidate budget result before deciding and dispatching the next one', () => {
  for (const weather of ['sun', 'rain']) {
    for (const budget of [300, 200, 100]) {
      const events = load().scenarios.supervisor.create({ weather, budget }).events;
      let assignment = null;
      let costRequests = 0;
      let completedAssignments = 0;
      for (const event of events) {
        if (event.kind === 'dispatch' && event.payload.to === 'budget') {
          assert.equal(assignment, null, 'a new assignment must follow the previous budget report');
          assert.equal(event.payload.from, 'supervisor');
          assignment = event.state_after.selected && event.state_after.selected.id;
          assert.ok(assignment, 'the supervisor must select the candidate before delegation');
          costRequests = 0;
        }
        if (event.actor === 'budget' && event.kind === 'action' && event.payload.tool === 'calculate_cost') {
          assert.equal(event.payload.args.venue, assignment, 'budget role may only evaluate the assigned candidate');
          costRequests += 1;
          assert.equal(costRequests, 1, 'changing candidate requires another supervisor assignment');
        }
        if (event.actor === 'budget' && event.kind === 'report') {
          assert.equal(event.payload.to, 'supervisor');
          assert.equal(costRequests, 1);
          assert.equal(event.payload.data.selected, assignment);
          assignment = null;
          completedAssignments += 1;
        }
      }
      assert.equal(assignment, null);
      assert.ok(completedAssignments >= 1);
      if (weather === 'rain' && budget === 200) {
        const reports = events.filter(e => e.actor === 'budget' && e.kind === 'report');
        assert.deepEqual(plain(reports.map(e => [e.payload.data.selected, e.payload.data.feasible])), [['P03', false], ['P04', true]]);
      }
    }
  }
});

test('swarm hands rejected candidates back to the venue role before selecting a replacement', () => {
  for (const weather of ['sun', 'rain']) {
    for (const budget of [300, 200, 100]) {
      const events = load().scenarios.swarm.create({ weather, budget }).events;
      for (let i = 1; i < events.length; i += 1) {
        const event = events[i];
        if (event.state_after.selected?.id && event.state_after.selected.id !== events[i - 1].state_after.selected?.id) {
          assert.equal(event.actor, 'venue', 'only the venue role chooses replacements');
          assert.equal(event.state_after.control, 'venue');
        }
        if (event.kind === 'observation' && event.payload.tool === 'check_budget' && !event.payload.result.ok) {
          const nextChoice = events.findIndex((e, index) => index > i && e.state_after.selected?.id && e.state_after.selected.id !== event.state_after.selected?.id);
          const until = nextChoice < 0 ? events.length : nextChoice;
          assert.ok(events.slice(i + 1, until).some(e => e.kind === 'dispatch' && e.payload.from === 'budget' && e.payload.to === 'venue' && e.state_after.control === 'venue'), 'failed budget must transfer control back to venue');
        }
      }
      if (weather === 'rain' && budget === 200) {
        const handoffs = events.filter(e => e.kind === 'dispatch' && e.payload.intent === 'handoff');
        assert.deepEqual(plain(handoffs.map(e => [e.payload.from, e.payload.to])), [['weather', 'venue'], ['venue', 'budget'], ['budget', 'venue'], ['venue', 'budget']]);
      }
    }
  }
});

test('deep snapshots cannot be overwritten, and host refuses mismatched costs or weather evidence', () => {
  const n5 = load();
  const result = n5.scenarios.react.create({ weather: 'rain', budget: 300 });
  const observed = result.events.find(e => e.kind === 'observation' && e.state_after.weather);
  assert.equal(Reflect.set(observed.state_after.weather, 'condition', 'sun'), false);
  assert.equal(observed.state_after.weather.condition, 'rain');
  assert.equal(result.initialState.weather, null);
  const u = n5.scriptUtils;
  const tape = u.outingTape({ weather: 'rain', budget: 300 }, 'executor');
  tape.state.selected = { ...plain(n5.outingData.venues[1]) };
  tape.state.weather = { condition: 'sun' };
  tape.state.costs = { venue: 'P02', total: 190 };
  tape.state.budget_used = 190;
  tape.state.budget_check = { ok: true };
  assert.equal(u.accept(tape, { weather: 'rain', budget: 300 }), false);
  const final = tape.events.at(-1);
  assert.equal(final.payload.status, 'needs_human');
  assert.equal(final.payload.acceptance.cost_matches, false);
  assert.equal(final.payload.acceptance.weather_compatible, false);
  assert.equal(final.state_after.itinerary, null);
});
