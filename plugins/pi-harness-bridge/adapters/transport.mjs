import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

export function jsonLines(stream, onRecord, onError) {
  let buffer = ''; stream.setEncoding('utf8');
  stream.on('data', chunk => {
    try {
      buffer += chunk; let i;
      while ((i = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, i).replace(/\r$/, ''); buffer = buffer.slice(i + 1);
        if (line.length > 8 * 1024 * 1024) throw new Error('Native record exceeds 8MiB');
        if (line.trim()) onRecord(JSON.parse(line));
      }
      if (buffer.length > 8 * 1024 * 1024) throw new Error('Native buffer exceeds 8MiB');
    } catch (e) { onError(e); }
  });
  stream.on('end', () => { if (buffer.trim()) { try { onRecord(JSON.parse(buffer)); } catch (e) { onError(e); } } });
}
export function start(config, args = []) {
  const child = spawn(config.command, [...(config.args || []), ...args], {
    cwd: process.cwd(), env: { ...process.env, ...config.env }, shell: false, windowsHide: true,
    detached: process.platform !== 'win32', stdio: ['pipe', 'pipe', 'pipe'],
  });
  child.stderr.on('data', b => process.stderr.write(b));
  child.stdin.on('error', () => {});
  return child;
}
export async function stop(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  if (process.platform === 'win32' && child.pid) {
    await new Promise(resolve => {
      const killer = spawn('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
      killer.once('error', () => { child.kill(); resolve(); }); killer.once('close', resolve);
    });
  } else { try { process.kill(-child.pid, 'SIGTERM'); } catch { child.kill(); } }
}
export class RpcPipe {
  constructor(config, args, onEvent = () => {}, onRequest, onFailure = () => {}) {
    this.config = config; this.child = start(config, args); this.pending = new Map(); this.dead = false;
    jsonLines(this.child.stdout, r => {
      if (r.id !== undefined && !r.method) {
        const p = this.pending.get(String(r.id)); if (!p) return;
        this.pending.delete(String(r.id)); clearTimeout(p.timer);
        r.error ? p.reject(new Error(r.error.message || JSON.stringify(r.error))) : p.resolve(r.result);
      } else if (r.method && r.id !== undefined) {
        Promise.resolve(onRequest?.(r)).then(result => this.send({ jsonrpc: '2.0', id: r.id, result: result ?? {} }))
          .catch(e => this.send({ jsonrpc: '2.0', id: r.id, error: { code: -32601, message: e.message } }));
      } else onEvent(r);
    }, e => this.fail(e));
    this.child.on('error', e => this.fail(e));
    this.child.on('close', (code, signal) => this.fail(new Error(`Native RPC exited: ${code ?? signal}`)));
    this.onFailure = onFailure;
  }
  send(record) {
    // ZCode Protocol is strict {id, method, params}, not JSON-RPC 2.0 envelopes.
    if (this.config.adapter === 'zcode') { const { jsonrpc, ...native } = record; record = native; }
    if (!this.dead) this.child.stdin.write(JSON.stringify(record) + '\n');
  }
  request(method, params = {}) {
    if (this.dead) return Promise.reject(new Error('Native RPC closed'));
    const id = randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`Native RPC timeout: ${method}`)); }, 25000);
      this.pending.set(id, { resolve, reject, timer }); this.send({ jsonrpc: '2.0', id, method, params });
    });
  }
  fail(error) {
    if (this.dead) return; this.dead = true;
    for (const p of this.pending.values()) { clearTimeout(p.timer); p.reject(error); } this.pending.clear();
    this.onFailure?.(error); void stop(this.child);
  }
  async close() { this.onFailure = undefined; await stop(this.child); }
}
export async function capture(config, args) {
  return await new Promise((resolve, reject) => {
    const child = start(config, args); let text = ''; let done = false;
    const finish = (e, value) => { if (done) return; done = true; clearTimeout(timer); e ? reject(e) : resolve(value); };
    const timer = setTimeout(() => { void stop(child); finish(new Error('Native discovery timeout')); }, 20000);
    child.stdout.setEncoding('utf8'); child.stdout.on('data', b => { text += b; if (text.length > 1024 * 1024) { void stop(child); finish(new Error('Native discovery output too large')); } });
    child.once('error', e => finish(e)); child.once('close', code => finish(code === 0 ? null : new Error(`Native discovery exit ${code}`), text)); child.stdin.end();
  });
}
export const textOf = content => typeof content === 'string' ? content : (content || []).filter(p => p.type === 'text').map(p => p.text || '').join('\n');
