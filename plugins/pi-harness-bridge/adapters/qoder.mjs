import { pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';
import { textOf } from './transport.mjs';

export class QoderAdapter {
  constructor(config, emit, finish) {
    this.config = config; this.emit = emit; this.finish = finish; this.running = false; this.closed = false; this.queue = []; this.wake = undefined;
    this.ready = this.initialize();
  }
  async initialize() {
    if (!this.config.sdkPath) throw new Error('Qoder CN 配置缺少 sdkPath');
    const sdk = await import(pathToFileURL(this.config.sdkPath).href);
    if (!sdk.hasResolvableQoderWorkerRuntime()) throw new Error('Qoder CN worker runtime 缺失');
    const self = this;
    const input = (async function* () {
      while (!self.closed) {
        if (!self.queue.length) await new Promise(resolve => { self.wake = resolve; });
        while (self.queue.length) yield self.queue.shift();
      }
    })();
    this.query = sdk.query({ prompt: input, options: {
      cwd: process.cwd(), transport: sdk.WorkerTransport.default,
      auth: this.config.authTokenEnv ? sdk.accessTokenFromEnv(this.config.authTokenEnv) : sdk.qodercliAuth(),
      permissionMode: 'default', planMode: true,
      canUseTool: async () => ({ behavior: 'deny', message: 'Pi Harness Bridge 不自动授权额外工具权限' }),
      stderr: text => process.stderr.write(text),
    } });
    this.consumePromise = this.consume();
    try { await this.query.initializationResult(); } catch (e) { throw new Error(this.error || e.message); }
  }
  async consume() {
    try {
      for await (const event of this.query) {
        this.emit({ type: 'native_event', adapter: 'qoder-cn', event });
        if (event.session_id) this.sessionId = event.session_id;
        if (event.type === 'assistant') this.text = textOf(event.message?.content);
        if (event.type === 'stream_event' && event.event?.type === 'content_block_delta' && event.event.delta?.type === 'text_delta') {
          this.emit({ type: 'message_update', assistantMessageEvent: { type: 'text_delta', contentIndex: event.event.index || 0, delta: event.event.delta.text } });
        }
        if (event.type === 'result' && event.is_error && !this.running) this.error = (event.errors || [event.terminal_reason || 'Qoder runtime failed']).join('; ');
        if (event.type === 'result' && this.running) {
          this.running = false;
          const failed = event.is_error || (event.subtype && event.subtype !== 'success');
          this.finish(event.result || this.text || '', failed ? JSON.stringify(event.errors || event.result || event.subtype) : undefined, this.cancelling);
        }
      }
      if (this.running) { this.running = false; this.finish('', 'Qoder SDK ended without a terminal result'); }
    } catch (e) { this.error = e.message; if (this.running) { this.running = false; this.finish('', e.message); } }
  }
  async state() { await this.ready; if (this.error) throw new Error(this.error); return { adapter: 'qoder-cn', sessionId: this.sessionId, model: this.model, isStreaming: this.running, capabilities: { resume: true, models: true, model: true, thinking: false }, permission: 'planMode=true; extra tool approvals denied' }; }
  async models() { await this.ready; return { models: await this.query.getAvailableModels() }; }
  async setModel(provider, modelId) {
    await this.ready;
    if (provider !== 'default') throw new Error('Qoder CN 模型使用原生模型 ID，provider 请填写 default');
    await this.query.setModel(modelId); this.model = modelId; return { modelId, acknowledged: true };
  }
  async thinking() { throw new Error('Qoder CN SDK 未适配独立 thinking 参数；可选原生模型规格'); }
  async prompt(message) {
    await this.ready; if (this.error || this.closed) throw new Error(this.error || 'Session closed');
    if (this.running) throw new Error('Session busy');
    this.running = true; this.text = ''; this.cancelling = false;
    this.queue.push({ type: 'user', uuid: randomUUID(), message: { role: 'user', content: [{ type: 'text', text: message }] }, parent_tool_use_id: null });
    this.wake?.(); this.wake = undefined;
    return { disposition: 'started' };
  }
  async cancel() { await this.ready; if (this.running) { this.cancelling = true; await this.query.interrupt(); } }
  async close() { this.closed = true; this.wake?.(); this.query?.close(); await this.consumePromise?.catch(() => {}); }
}
