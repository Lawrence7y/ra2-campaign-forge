import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { mkdirSync, appendFileSync, readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const terminal = new Set(['completed', 'failed', 'cancelled']);
export class HarnessBridge {
  constructor(config, cwd, onComplete = () => {}) {
    if (!config || !config.harnesses || typeof config.harnesses !== 'object') throw new Error('配置缺少 harnesses');
    for (const [name, h] of Object.entries(config.harnesses)) {
      if (!h || !['pi-rpc', 'jsonl', 'codex', 'antigravity', 'zcode', 'qoder-cn', 'dsh'].includes(h.adapter) || typeof h.command !== 'string' || !h.command ||
          (h.args && (!Array.isArray(h.args) || h.args.some(a => typeof a !== 'string')))) throw new Error(`无效 harness 配置: ${name}`);
    }
    this.config = config; this.cwd = cwd; this.onComplete = onComplete; this.tasks = new Map(); this.closed = false;
    this.logDir = resolve(cwd, config.logDir || '.pi/harness-runs');
  }
  list() { return Object.entries(this.config.harnesses).map(([name, h]) => ({ name, adapter: h.adapter, cwd: resolve(this.cwd, h.cwd || '.') })); }
  get(id) { const t = this.tasks.get(id); if (!t) throw new Error(`未知 taskId: ${id}`); return t; }
  snapshot(t) { return { taskId: t.id, harness: t.harness, status: t.status, createdAt: t.createdAt, updatedAt: t.updatedAt, error: t.error, eventCount: t.seq, logPath: t.logPath, stderrPath: t.stderrPath, pid: t.child.pid }; }
  finish(t, status, error) {
    if (terminal.has(t.status)) return;
    t.status = status; t.error = error; t.updatedAt = new Date().toISOString();
    try { this.onComplete(this.snapshot(t)); } catch { /* observer must not break transport */ }
  }
  record(t, record) {
    const entry = { seq: ++t.seq, timestamp: new Date().toISOString(), record };
    appendFileSync(t.logPath, JSON.stringify(entry) + '\n', { mode: 0o600 });
    t.updatedAt = entry.timestamp;
    if (record.type === 'response') {
      const p = t.pending.get(record.id);
      if (p) { t.pending.delete(record.id); clearTimeout(p.timer); record.success ? p.resolve(record.data) : p.reject(new Error(record.error || 'RPC command failed')); }
    }
    if (record.type === 'message_end' && record.message?.role === 'assistant') {
      t.lastStop = record.message.stopReason; t.lastError = record.message.errorMessage;
    }
    if (record.type === 'agent_settled') {
      this.finish(t, t.cancelling || t.lastStop === 'aborted' ? 'cancelled' : t.lastStop === 'error' ? 'failed' : 'completed', t.lastError);
    }
    if (record.type === 'extension_ui_request' && ['confirm', 'select', 'input', 'editor'].includes(record.method)) {
      // Never silently approve an external agent's permission requests.
      this.write(t, { type: 'extension_ui_response', id: record.id, cancelled: true }).catch(e => this.fail(t, e));
    }
  }
  fail(t, error) {
    if (t.failing) return; t.failing = true;
    this.finish(t, 'failed', String(error.message || error));
    for (const p of t.pending.values()) { clearTimeout(p.timer); p.reject(error); }
    t.pending.clear();
    // EOF lets native wrappers cancel their owned agents before exiting (Windows signals do not run JS handlers).
    if (!t.child.stdin.destroyed) t.child.stdin.end();
    const timer = setTimeout(() => { if (!t.exited) t.child.kill(); }, 10000);
    timer.unref(); t.child.once('close', () => clearTimeout(timer));
  }
  async write(t, value) {
    if (t.exited || t.child.stdin.destroyed) throw new Error('外部进程已退出');
    await new Promise((resolve, reject) => t.child.stdin.write(JSON.stringify(value) + '\n', e => e ? reject(e) : resolve()));
  }
  request(t, type, fields = {}) {
    const id = randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        t.pending.delete(id);
        const error = new Error(`RPC 超时: ${type}; 结果不确定，进程已终止`);
        reject(error); this.fail(t, error);
      }, this.config.requestTimeoutMs || 30000);
      t.pending.set(id, { resolve, reject, timer });
      this.write(t, { ...fields, type, id }).catch(e => this.fail(t, e));
    });
  }
  open(harness) {
    if (this.closed) throw new Error('Bridge 已关闭');
    const h = this.config.harnesses[harness]; if (!h) throw new Error(`未配置 harness: ${harness}`);
    const live = [...this.tasks.values()].filter(t => !t.exited).length;
    if (live >= (this.config.maxProcesses || 4)) throw new Error('已达到进程上限，请先关闭旧会话');
    mkdirSync(this.logDir, { recursive: true });
    const id = randomUUID();
    const native = !['pi-rpc', 'jsonl'].includes(h.adapter);
    const args = native ? [fileURLToPath(new URL('./adapters/runner.mjs', import.meta.url))] : [...(h.args || [])];
    if (h.adapter === 'pi-rpc') args.push('--mode', 'rpc', '--no-extensions', '--no-session');
    const host = h.adapter === 'qoder-cn' ? h.command : process.execPath;
    const child = spawn(native ? host : h.command, args, { cwd: resolve(this.cwd, h.cwd || '.'), env: { ...process.env, ...h.env, PI_HARNESS_BRIDGE_CHILD: '1', ...(native ? { HARNESS_NATIVE_CONFIG: JSON.stringify(h) } : {}) }, shell: false, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    const t = { id, harness, child, status: 'starting', pending: new Map(), seq: 0, buffer: '', createdAt: new Date().toISOString(), logPath: join(this.logDir, id + '.jsonl'), stderrPath: join(this.logDir, id + '.stderr.log') };
    t.updatedAt = t.createdAt; this.tasks.set(id, t);
    appendFileSync(t.logPath, '', { mode: 0o600 });
    child.stdout.setEncoding('utf8'); child.stderr.setEncoding('utf8');
    child.stdout.on('data', chunk => {
      try {
        t.buffer += chunk;
        let i;
        while ((i = t.buffer.indexOf('\n')) >= 0) {
          const line = t.buffer.slice(0, i).replace(/\r$/, ''); t.buffer = t.buffer.slice(i + 1);
          if (line.length > 8 * 1024 * 1024) throw new Error('JSONL record 超过 8MiB');
          if (line) { const r = JSON.parse(line); if (!r || typeof r.type !== 'string') throw new Error('无效协议 record'); this.record(t, r); }
        }
        if (t.buffer.length > 8 * 1024 * 1024) throw new Error('JSONL buffer 超限');
      } catch (e) { this.fail(t, e); }
    });
    child.stderr.on('data', chunk => { try { appendFileSync(t.stderrPath, chunk, { mode: 0o600 }); } catch (e) { this.fail(t, e); } });
    child.stdin.on('error', e => this.fail(t, e));
    child.on('error', e => this.fail(t, e));
    child.on('close', (code, signal) => {
      t.exited = true;
      const e = new Error(`外部进程退出: code=${code}, signal=${signal}`);
      if (!terminal.has(t.status)) this.finish(t, t.cancelling ? 'cancelled' : 'failed', e.message);
      for (const p of t.pending.values()) { clearTimeout(p.timer); p.reject(e); } t.pending.clear();
    });
    return t;
  }
  async probe(harness) {
    const t = this.open(harness);
    try { return { harness, state: await this.request(t, 'get_state'), models: await this.request(t, 'get_available_models') }; }
    finally { t.status = 'completed'; await this.close(t.id); }
  }
  async dispatch(harness, prompt, model) {
    const t = this.open(harness);
    try {
      if (model) await this.request(t, 'set_model', { provider: model.provider, modelId: model.modelId });
      t.status = 'running';
      const result = await this.request(t, 'prompt', { message: prompt });
      if (result?.disposition === 'handled') this.finish(t, 'completed');
      return this.snapshot(t);
    } catch (e) { this.fail(t, e); throw new Error(`${e.message}; taskId=${t.id}; 日志=${t.logPath}`); }
  }
  async status(id) { const t = this.get(id); return { ...this.snapshot(t), remote: t.exited ? null : await this.request(t, 'get_state') }; }
  async models(id) { return this.request(this.get(id), 'get_available_models'); }
  async model(id, provider, modelId, thinking) {
    const t = this.get(id);
    if (!terminal.has(t.status)) throw new Error('请等待任务完成后切换模型，避免影响正在运行的请求');
    const result = await this.request(t, 'set_model', { provider, modelId });
    if (thinking) await this.request(t, 'set_thinking_level', { level: thinking });
    return result;
  }
  async prompt(id, message) {
    const t = this.get(id);
    if (!terminal.has(t.status)) throw new Error('会话忙，请等待完成或取消');
    t.status = 'running'; t.lastStop = undefined; t.lastError = undefined; t.cancelling = false;
    try { const result = await this.request(t, 'prompt', { message }); if (result?.disposition === 'handled') this.finish(t, 'completed'); return this.snapshot(t); }
    catch (e) { this.finish(t, 'failed', e.message); throw e; }
  }
  async cancel(id) {
    const t = this.get(id); if (terminal.has(t.status)) return this.snapshot(t);
    t.cancelling = true; await this.request(t, 'abort'); this.finish(t, 'cancelled'); return this.snapshot(t);
  }
  read(id, after = 0, limit = 30) {
    const t = this.get(id); const events = []; let bytes = 0;
    // Logs are local and durable; pagination limits model context, not total log storage.
    for (const line of readFileSync(t.logPath, 'utf8').split('\n')) {
      if (!line) continue; const e = JSON.parse(line); if (e.seq <= after) continue;
      if (events.length >= Math.min(limit, 100)) break;
      if (line.length > 20000) {
        const summary = { seq: e.seq, timestamp: e.timestamp, record: { type: e.record.type }, truncated: true, fullOutputPath: t.logPath };
        if (bytes + JSON.stringify(summary).length > 24000) break;
        events.push(summary); bytes += JSON.stringify(summary).length;
      } else {
        if (bytes + line.length > 24000) break;
        events.push(e); bytes += line.length;
      }
    }
    const next = events.at(-1)?.seq ?? after;
    return { ...this.snapshot(t), events, nextCursor: next, hasMore: next < t.seq, fullOutputPath: t.logPath };
  }
  async close(id) {
    const t = this.get(id); t.cancelling = true;
    if (!terminal.has(t.status)) this.finish(t, 'cancelled');
    t.child.stdin.end();
    if (!t.exited) await new Promise(resolve => {
      const timer = setTimeout(() => { t.child.kill(); resolve(); }, 10000);
      t.child.once('close', () => { clearTimeout(timer); resolve(); });
    });
    return this.snapshot(t);
  }
  async shutdown() { this.closed = true; await Promise.all([...this.tasks.keys()].map(id => this.close(id))); }
}
