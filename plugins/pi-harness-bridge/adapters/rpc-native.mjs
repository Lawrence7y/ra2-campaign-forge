import { RpcPipe, textOf } from './transport.mjs';
import { randomUUID } from 'node:crypto';

export class CodexAdapter {
  constructor(config, emit, finish) {
    this.config = config; this.emit = emit; this.finish = finish; this.sessionId = undefined; this.running = false; this.model = undefined;
    this.rpc = new RpcPipe(config, ['app-server'], r => this.event(r), r => {
      if (/approval/i.test(r.method)) return { decision: 'decline' };
      throw new Error(`Unsupported interactive request: ${r.method}`);
    }, e => { if (this.running) { this.running = false; this.finish('', e.message); } });
    this.ready = this.rpc.request('initialize', { clientInfo: { name: 'pi-harness-bridge', version: '0.2.0' }, capabilities: {} }).then(r => {
      this.rpc.send({ method: 'initialized', params: {} }); return r;
    });
  }
  event(r) {
    this.emit({ type: 'native_event', adapter: 'codex', event: r });
    const p = r.params || {};
    if (r.method === 'item/agentMessage/delta') this.emit({ type: 'message_update', assistantMessageEvent: { type: 'text_delta', contentIndex: 0, delta: p.delta } });
    if (r.method === 'item/completed' && p.item?.type === 'agentMessage') this.text = p.item.text;
    if (r.method === 'turn/completed' && this.running) {
      this.running = false;
      const turn = p.turn || {};
      this.finish(this.text || '', turn.status === 'failed' ? turn.error?.message || 'Codex turn failed' : undefined, turn.status === 'interrupted');
    }
  }
  async state() { await this.ready; return { adapter: 'codex', sessionId: this.sessionId, isStreaming: this.running, model: this.model, capabilities: { resume: true, model: true, thinking: true, models: true }, permission: 'read-only / never approve' }; }
  async models() { await this.ready; return this.rpc.request('model/list', { limit: 100 }); }
  async setModel(provider, modelId) {
    if (this.running) throw new Error('Session busy');
    if (this.sessionId && provider !== (this.threadProvider || 'default')) throw new Error('Codex 活跃 thread 不支持通过 turn/start 更换供应商，请另建会话');
    this.model = { provider, modelId }; return { ...this.model, effective: 'next-turn', verified: false };
  }
  async thinking(level) { if (!['minimal', 'low', 'medium', 'high', 'xhigh'].includes(level)) throw new Error('Codex effort 不支持此值'); this.effort = level; return { effective: 'next-turn', level }; }
  async prompt(message) {
    await this.ready; if (this.running) throw new Error('Session busy');
    if (!this.sessionId) {
      const r = await this.rpc.request('thread/start', { cwd: process.cwd(), approvalPolicy: 'never', sandbox: 'read-only', ...(this.model ? { model: this.model.modelId, modelProvider: this.model.provider === 'default' ? undefined : this.model.provider } : {}) });
      this.sessionId = r.thread.id; this.threadProvider = this.model?.provider || 'default';
    }
    this.running = true; this.text = '';
    try {
      const r = await this.rpc.request('turn/start', { threadId: this.sessionId, input: [{ type: 'text', text: message }], approvalPolicy: 'never', sandboxPolicy: { type: 'readOnly' }, ...(this.model ? { model: this.model.modelId } : {}), ...(this.effort ? { effort: this.effort } : {}) });
      this.turnId = r.turn.id;
      return { disposition: 'started' };
    } catch (e) { this.running = false; throw e; }
  }
  async cancel() { if (this.running && this.turnId) await this.rpc.request('turn/interrupt', { threadId: this.sessionId, turnId: this.turnId }); }
  async close() { await this.cancel().catch(() => {}); await this.rpc.close(); }
}

export class ZcodeAdapter {
  constructor(config, emit, finish) {
    this.config = config; this.emit = emit; this.finish = finish; this.running = false;
    this.rpc = new RpcPipe(config, ['app-server'], r => this.emit({ type: 'native_event', adapter: 'zcode', event: r }), r => {
      if (r.method === 'session/requestRuntimePreferences') return { nativeSearchEnhancementsEnabled: true, memoryEnabled: false, askUserQuestionAutoResolutionEnabled: false, modelContextBudgetStrategy: 'preflight-v1' };
      throw new Error(`Interactive request denied: ${r.method}`);
    }, e => { if (this.running) { this.running = false; this.finish('', e.message); } });
    this.ready = this.rpc.request('runtime/capabilities', {});
  }
  async ensure() {
    await this.ready;
    if (!this.sessionId) {
      const cwd = process.cwd();
      this.snapshot = await this.rpc.request('session/create', { workspace: { workspacePath: cwd, workspaceKey: cwd }, mode: 'plan', titleGenerationEnabled: false, offPeakToolEnabled: false, dynamicWorkflowEnabled: false });
      this.sessionId = this.snapshot.session.sessionId;
    }
    return this.sessionId;
  }
  async state() {
    await this.ensure(); this.snapshot = await this.rpc.request('session/read', { sessionId: this.sessionId, messageLimit: 10 });
    return { adapter: 'zcode', sessionId: this.sessionId, isStreaming: this.running, model: this.snapshot.session.model, remote: this.snapshot, capabilities: { resume: true, model: true, thinking: true, models: true }, permission: 'plan; interactive requests denied' };
  }
  async models() {
    await this.state();
    // Expose the native settings object, including provider-qualified availability. Do not invent a catalog.
    return { source: 'session/read.settings.model.available', models: this.snapshot.settings?.model?.available || [], current: this.snapshot.session.model, thinking: this.snapshot.settings?.thoughtLevel };
  }
  async setModel(provider, modelId) {
    await this.ensure();
    this.snapshot = await this.rpc.request('session/setModel', { sessionId: this.sessionId, model: { providerId: provider, modelId }, persistAsWorkspaceLastUsed: false });
    return { verified: true, current: this.snapshot.session.model };
  }
  async thinking(level) { await this.ensure(); return this.rpc.request('session/setThoughtLevel', { sessionId: this.sessionId, thoughtLevel: level, persistAsWorkspaceLastUsed: false }); }
  async prompt(message) {
    await this.ensure(); if (this.running) throw new Error('Session busy');
    this.running = true;
    try { await this.rpc.request('session/send', { sessionId: this.sessionId, content: message, inputId: randomUUID() }); }
    catch (e) { this.running = false; throw e; }
    this.pollTimer = setTimeout(() => void this.poll(), 500);
    return { disposition: 'started' };
  }
  async poll() {
    if (!this.running) return;
    try {
      const s = await this.rpc.request('session/read', { sessionId: this.sessionId, messageLimit: 10 }); this.snapshot = s;
      if (!s.runtime.activeTurnId && !['running', 'waiting'].includes(s.projection.status)) {
        this.running = false;
        this.emit({ type: 'native_snapshot', adapter: 'zcode', snapshot: s });
        const messages = (s.messages || []).filter(m => (m.info?.role || m.role) === 'assistant');
        const last = messages.at(-1);
        const text = textOf(last?.parts || last?.content);
        this.finish(text, s.projection.status === 'error' ? String(s.projection.lastError || 'ZCode failed') : undefined);
      } else this.pollTimer = setTimeout(() => void this.poll(), 1000);
    } catch (e) { this.running = false; this.finish('', e.message); }
  }
  async cancel() {
    clearTimeout(this.pollTimer);
    if (this.running) {
      await this.rpc.request('session/stop', { sessionId: this.sessionId });
      for (let i = 0; i < 40; i++) {
        const s = await this.rpc.request('session/read', { sessionId: this.sessionId, messageLimit: 1 });
        if (!s.runtime.activeTurnId && !['running', 'waiting'].includes(s.projection.status)) { this.running = false; break; }
        await new Promise(r => setTimeout(r, 250));
      }
      if (this.running) { this.pollTimer = setTimeout(() => void this.poll(), 1000); throw new Error('ZCode stop not yet confirmed'); }
    }
    this.finish('', undefined, true);
  }
  async close() { clearTimeout(this.pollTimer); await this.cancel().catch(() => {}); if (this.sessionId) await this.rpc.request('session/close', { sessionId: this.sessionId }).catch(() => {}); await this.rpc.close(); }
}
