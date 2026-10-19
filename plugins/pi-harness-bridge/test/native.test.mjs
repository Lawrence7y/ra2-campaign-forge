import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { HarnessBridge } from '../core.mjs';
const mock = fileURLToPath(new URL('./mock-native.mjs', import.meta.url));
const sdk = fileURLToPath(new URL('./mock-qoder-sdk.mjs', import.meta.url));
function setup(t, adapter) {
  const dir = mkdtempSync(join(tmpdir(), 'native-harness-'));
  const b = new HarnessBridge({ requestTimeoutMs: 10000, harnesses: { native: { adapter, command: process.execPath, args: [mock, adapter], sdkPath: sdk } } }, dir);
  t.after(async () => { await b.shutdown(); rmSync(dir, { recursive: true, force: true }); }); return b;
}
async function settled(b, id) {
  for (let i = 0; i < 200; i++) { const s = b.get(id).status; if (['completed', 'failed', 'cancelled'].includes(s)) return s; await new Promise(r => setTimeout(r, 10)); }
  throw new Error('test settle timeout');
}
for (const adapter of ['codex', 'zcode', 'antigravity', 'qoder-cn']) {
  test(`${adapter}: probe, dispatch, returned content, model, continued session`, async t => {
    const b = setup(t, adapter);
    const probe = await b.probe('native'); assert.ok(probe.state.capabilities.resume);
    const a = await b.dispatch('native', 'hello'); assert.equal(await settled(b, a.taskId), 'completed');
    const messages = b.read(a.taskId).events.filter(e => e.record.type === 'message_end');
    assert.ok(messages.some(e => e.record.message.content[0].text.includes('hello')));
    await b.model(a.taskId, 'default', 'large');
    await b.prompt(a.taskId, 'again'); assert.equal(await settled(b, a.taskId), 'completed');
    assert.match(JSON.stringify(b.read(a.taskId)), /again/);
  });
}
test('Codex provider failures and cancel are not success', async t => {
  const b = setup(t, 'codex'); const a = await b.dispatch('native', 'error'); assert.equal(await settled(b, a.taskId), 'failed');
  await b.prompt(a.taskId, 'wait'); await b.cancel(a.taskId); assert.equal(b.get(a.taskId).status, 'cancelled');
  await assert.rejects(b.model(a.taskId, 'other-provider', 'large'), /供应商/);
});
test('Qoder unsupported thinking returns explicit error', async t => {
  const b = setup(t, 'qoder-cn'); const a = await b.dispatch('native', 'hi'); await settled(b, a.taskId);
  await assert.rejects(b.model(a.taskId, 'default', 'large', 'high'), /thinking/);
});
