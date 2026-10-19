import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, basename, resolve } from 'node:path';
import { TaskManager } from 'file:///D:/Project/dsh-harness-pilot/lib/tasks.js';
import { normalizeSettings } from 'file:///D:/Project/dsh-harness-pilot/lib/settings.js';
import { patchTaskManager } from './patch.js';

function manager(limit) {
  const directory = mkdtempSync(join(tmpdir(), 'hp-unlimited-'));
  const instance = new TaskManager({ directory, maxConcurrent: limit,
    dispatch: spec => new Promise(resolve => spec.signal.addEventListener('abort', () => resolve({stopReason:'aborted',text:'stopped',transport:'headless'}), {once:true})) });
  const input = { target:{name:'test'}, prompt:'test', cwd:directory, timeoutMs:60000,
    callback:{notify:false,sessionId:'test',instruction:''} };
  return { instance, input, async clean(){await instance.shutdown();
    assert.equal(resolve(dirname(directory)),resolve(tmpdir()));assert.ok(basename(directory).startsWith('hp-unlimited-'));
    rmSync(directory,{recursive:true,force:true});} };
}

test('zero remains unlimited; positive limits above 16 remain valid; invalid negatives do not disable limits', () => {
  assert.equal(normalizeSettings({maxConcurrent:0}).maxConcurrent,0);
  assert.equal(normalizeSettings({maxConcurrent:100}).maxConcurrent,100);
  assert.equal(normalizeSettings({maxConcurrent:-1}).maxConcurrent,4);
});
test('unlimited accepts 20 simultaneously pending tasks', async () => {
  const m=manager(0);
  try { for(let i=0;i<20;i++) m.instance.start(m.input); assert.equal(m.instance.list(30).length,20); }
  finally { await m.clean(); }
});
test('finite limits still reject excess tasks', async () => {
  const m=manager(1);
  try { m.instance.start(m.input); assert.throws(()=>m.instance.start(m.input),/concurrency limit/); }
  finally { await m.clean(); }
});
test('hot patch allows fifth task and preserves first four; restoring finite setting works', async () => {
  const m=manager(4);let value=0;let restore;
  try {
    const ids=[];for(let i=0;i<4;i++)ids.push(m.instance.start(m.input).task_id);
    restore=patchTaskManager(TaskManager,()=>value);
    m.instance.start(m.input);
    for(const id of ids)assert.equal(m.instance.status(id).status,'running');
    value=1;assert.throws(()=>m.instance.start(m.input),/concurrency limit/);
  } finally {restore?.();await m.clean();}
});
