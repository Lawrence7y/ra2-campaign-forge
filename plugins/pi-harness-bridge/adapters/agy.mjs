import { start, stop, jsonLines, capture } from './transport.mjs';

export class AgyAdapter {
  constructor(config, emit, finish) { this.config = config; this.emit = emit; this.finish = finish; this.running = false; }
  async state() { return { adapter: 'antigravity', sessionId: this.sessionId, isStreaming: this.running, model: this.model, capabilities: { resume: true, model: true, thinking: true, models: true }, permission: 'plan + sandbox; no auto-approval flag' }; }
  async models() { return { source: 'agy models', nativeOutput: await capture(this.config, ['models']) }; }
  async setModel(provider, modelId) {
    if (provider !== 'default') throw new Error('Antigravity provider 请填写 default，modelId 使用 agy models 返回的 slug');
    const catalog = await this.models();
    if (!catalog.nativeOutput.includes(modelId)) throw new Error('指定模型不在 agy models 输出中');
    this.model = modelId; return { modelId, effective: 'next-turn', verified: false };
  }
  async thinking(level) { if (!['low', 'medium', 'high', 'xhigh', 'max'].includes(level)) throw new Error('Antigravity 不支持该 effort'); this.effort = level; return { effective: 'next-turn', level }; }
  async prompt(message) {
    if (this.running) throw new Error('Session busy');
    const args = ['--print=', '--input-format', 'stream-json', '--output-format', 'stream-json', '--mode', 'plan', '--sandbox', '--disable-slash-commands', '--print-timeout', this.config.taskTimeout || '2h'];
    if (this.sessionId) args.push('--conversation', this.sessionId);
    if (this.model) args.push('--model', this.model);
    if (this.effort) args.push('--effort', this.effort);
    const child = this.child = start(this.config, args);
    this.running = true; this.cancelling = false; this.text = ''; this.result = undefined; this.parseError = undefined;
    jsonLines(child.stdout, event => {
      this.emit({ type: 'native_event', adapter: 'antigravity', event });
      if (event.event === 'init') this.sessionId = event.init?.conversation_id || event.conversation_id || this.sessionId;
      if (event.event === 'step_update' && event.step_update?.step_type === 'agent_response') {
        const delta = event.step_update.text_delta || ''; this.text += delta;
        this.emit({ type: 'message_update', assistantMessageEvent: { type: 'text_delta', contentIndex: 0, delta } });
      }
      if (event.event === 'result') {
        this.result = event.result;
        this.sessionId = event.result?.conversation_id || this.sessionId;
        // Native terminal result may precede process exit; give it a bounded grace.
        this.exitTimer = setTimeout(() => void stop(child), 5000);
      }
    }, e => { this.parseError = e.message; void stop(child); });
    child.once('error', e => { this.parseError = e.message; });
    child.once('close', code => {
      clearTimeout(this.exitTimer); this.running = false;
      const response = this.result?.response || this.text;
      const error = this.cancelling ? undefined : this.parseError || (this.result?.status !== 'SUCCESS' ? this.result?.error || `AGY ended without SUCCESS (exit=${code})` : !response ? 'AGY returned empty content' : undefined);
      this.finish(response, error, this.cancelling);
    });
    child.stdin.end(JSON.stringify({ event: 'user', message: { content: message } }) + '\n');
    return { disposition: 'started' };
  }
  async cancel() { this.cancelling = true; await stop(this.child); }
  async close() { clearTimeout(this.exitTimer); await this.cancel(); }
}
