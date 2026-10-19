import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { HarnessBridge } from '../core.mjs';
const mock = fileURLToPath(new URL('./mock-harness.mjs', import.meta.url));
function setup(t, options = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'harness-test-'));
  const notifications = [];
  const b = new HarnessBridge({ harnesses: { mock: { adapter: 'jsonl', command: process.execPath, args: [mock] } }, ...options }, dir, s => notifications.push(s));
  t.after(async () => { await b.shutdown(); rmSync(dir, { recursive: true, force: true }); });
  return { b, notifications };
}
async function settled(b, id) {
  for (let i = 0; i < 100; i++) { if (['completed', 'failed', 'cancelled'].includes(b.get(id).status)) return; await new Promise(r => setTimeout(r, 10)); }
  throw new Error('test settle timeout');
}
test('dispatch, Unicode framing, pagination, model and continued session', async t => {
  const { b, notifications } = setup(t);
  const task = await b.dispatch('mock', '你好');
  await settled(b, task.taskId);
  assert.equal(b.get(task.taskId).status, 'completed');
  assert.equal(notifications.length, 1);
  const first = b.read(task.taskId, 0, 1); assert.equal(first.events.length, 1); assert.ok(first.hasMore);
  assert.match(JSON.stringify(b.read(task.taskId)), /结果：你好/);
  assert.match(JSON.stringify(b.read(task.taskId)), /完整/);
  await b.model(task.taskId, 'mock', 'large', 'high');
  assert.equal((await b.status(task.taskId)).remote.model.id, 'large');
  assert.ok((await b.models(task.taskId)).models.length);
  await b.prompt(task.taskId, '继续'); await settled(b, task.taskId);
  assert.equal(notifications.length, 2);
});
test('cancel and process limit', async t => {
  const { b } = setup(t, { maxProcesses: 1 });
  const a = await b.dispatch('mock', 'wait');
  await assert.rejects(b.dispatch('mock', 'another'), /进程上限/);
  await b.cancel(a.taskId); assert.equal(b.get(a.taskId).status, 'cancelled');
  await b.close(a.taskId);
});
test('provider failure is not marked complete', async t => {
  const { b } = setup(t); const a = await b.dispatch('mock', 'error'); await settled(b, a.taskId);
  assert.equal(b.get(a.taskId).status, 'failed');
});
test('oversized event still advances cursor', async t => {
  const { b } = setup(t); const a = await b.dispatch('mock', 'large'); await settled(b, a.taskId);
  const page = b.read(a.taskId); assert.ok(page.events.some(e => e.truncated)); assert.equal(page.hasMore, false);
});
test('timeouts, malformed stdout and exits fail cleanly', async t => {
  for (const prompt of ['hang', 'invalid', 'exit']) {
    const { b } = setup(t, { requestTimeoutMs: 300 });
    await assert.rejects(b.dispatch('mock', prompt));
    assert.equal([...b.tasks.values()][0].status, 'failed');
  }
});
test('unknown harness and task are rejected', async t => {
  const { b } = setup(t);
  await assert.rejects(b.dispatch('unknown', 'hi'), /未配置/);
  assert.throws(() => b.get('bad'), /未知/);
});
