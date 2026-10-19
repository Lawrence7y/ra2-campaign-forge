// CDP is used solely as transport into the existing Electron preload API.
// No arbitrary evaluate tool, DOM typing, app launch, process kill, or credential extraction.
export class DesktopConnection {
  constructor(config) {
    const url = new URL(config.endpoint);
    if (url.protocol !== 'http:' || !['127.0.0.1', '[::1]', 'localhost'].includes(url.hostname) || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error('Desktop endpoint 必须是本机 HTTP 根地址');
    this.config = config; this.url = url; this.pending = new Map(); this.counter = 0;
  }
  async connect() {
    const targets = await (await fetch(new URL('json/list', this.url), { signal: AbortSignal.timeout(3000), redirect: 'error' })).json();
    for (const target of targets.filter(t => t.type === 'page' && (!this.config.targetId || t.id === this.config.targetId))) {
      const address = new URL(target.webSocketDebuggerUrl);
      if (address.protocol !== 'ws:' || address.hostname !== this.url.hostname || address.port !== this.url.port) throw new Error('CDP target 地址不是配置的本机端点');
      this.ws = new WebSocket(address);
      try {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('CDP connect timeout')), 3000);
          this.ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
          this.ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error('CDP socket failed')); }, { once: true });
        });
        const socket = this.ws;
        socket.addEventListener('message', e => {
          if (this.ws !== socket) return;
          let r; try { r = JSON.parse(e.data); } catch { return; }
          const p = this.pending.get(r.id); if (!p) return;
          this.pending.delete(r.id); clearTimeout(p.timer); r.error ? p.reject(new Error(r.error.message)) : p.resolve(r.result);
        });
        socket.addEventListener('close', () => { if (this.ws === socket) this.rejectPending(); });
        const present = await this.evaluate(`typeof window[${JSON.stringify(this.config.api)}] === 'object'`, 2500);
        if (present) { this.targetId = target.id; return; }
      } catch { /* Try only other renderer targets, never retry a mutation. */ }
      this.ws.close(); this.rejectPending();
    }
    throw new Error(`未找到 ${this.config.api} 桌面 renderer；不会回退到 CLI 或误投到其他窗口`);
  }
  request(method, params, timeout = 20000) {
    const id = ++this.counter;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('Desktop IPC 超时，写操作结果可能不确定，禁止自动重发')); }, timeout);
      this.pending.set(id, { resolve, reject, timer });
      try { this.ws.send(JSON.stringify({ id, method, params })); }
      catch(e) { clearTimeout(timer); this.pending.delete(id); reject(e); }
    });
  }
  async evaluate(expression, timeout) {
    const r = await this.request('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, timeout);
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text || 'Desktop IPC failed');
    return r.result?.value;
  }
  async call(method, args = []) {
    return await this.evaluate(`(async()=>{const api=window[${JSON.stringify(this.config.api)}];const fn=api[${JSON.stringify(method)}];if(typeof fn!=='function')throw new Error('Desktop API not available');return await fn(...${JSON.stringify(args)})})()`);
  }
  rejectPending() { for (const p of this.pending.values()) { clearTimeout(p.timer); p.reject(new Error('Desktop connection closed')); } this.pending.clear(); }
  close() { this.rejectPending(); this.ws?.close(); }
}
