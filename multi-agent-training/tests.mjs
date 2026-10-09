import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
function run(args) {
  const result = spawnSync(process.execPath, [join(root, 'run.mjs'), ...args], {
    encoding: 'utf8', timeout: 15000,
    env: { ...process.env, DEEPSEEK_API_KEY: '' },
  });
  assert.equal(result.error, undefined);
  return result;
}

for (const mode of ['sequential', 'supervisor', 'hierarchical', 'swarm', 'network']) {
  test(`${mode} completes offline and saves a usable report`, () => {
    const output = mkdtempSync(join(tmpdir(), 'agent-training-'));
    try {
      const result = run(['--mode', mode, '--output', output]);
      assert.equal(result.status, 0, result.stderr);
      const report = JSON.parse(readFileSync(join(output, `${mode}.json`), 'utf8'));
      assert.equal(report.status, 'completed');
      assert.equal(report.backend, 'offline-simulation');
      assert.equal(report.modelCalls, 0);
      assert.ok(report.content.length > 30);
      assert.ok(report.events.some(event => event.agent === 'researcher'));
      assert.ok(report.events.some(event => event.agent === 'writer'));
    } finally { rmSync(output, { recursive: true, force: true }); }
  });
}

test('product entry rejects missing requirements and approval of future output', () => {
  const result = run(['--mode', 'devteam']);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /requirements/);
  const approval = run(['--mode', 'devteam', '--approve']);
  assert.equal(approval.status, 1);
  assert.match(approval.stderr, /revision/);
});

test('a handoff cycle is stopped by an enforced step limit', () => {
  const output = mkdtempSync(join(tmpdir(), 'agent-training-'));
  try {
    const result = run(['--mode', 'network', '--force-cycle', '--max-steps', '4', '--output', output]);
    assert.equal(result.status, 2, result.stderr);
    const report = JSON.parse(readFileSync(join(output, 'network.json'), 'utf8'));
    assert.equal(report.status, 'step_limit');
    assert.ok(!existsSync(join(output, 'network.md')));
  } finally { rmSync(output, { recursive: true, force: true }); }
});

test('live mode requires a key before any API call', () => {
  const result = run(['--live', '--mode', 'sequential']);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /DEEPSEEK_API_KEY/);
});

test('invalid options are rejected clearly', () => {
  for (const args of [['--mode', 'unknown'], ['--max-steps', '0'], ['--typo'], ['--mode']]) {
    const result = run(args);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /ERROR/);
  }
});

test('security exercise rejects unauthorized tools and over-budget requests', () => {
  const output = mkdtempSync(join(tmpdir(), 'agent-training-'));
  try {
    const result = run(['--mode', 'security', '--output', output]);
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(readFileSync(join(output, 'security.json'), 'utf8'));
    assert.equal(report.checks.allowedTool, true);
    assert.equal(report.checks.unauthorizedToolBlocked, true);
    assert.equal(report.checks.budgetExceededBlocked, true);
  } finally { rmSync(output, { recursive: true, force: true }); }
});
