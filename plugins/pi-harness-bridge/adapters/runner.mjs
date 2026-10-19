import { fileURLToPath } from 'node:url';
import { CodexAdapter, ZcodeAdapter } from './rpc-native.mjs';
import { AgyAdapter } from './agy.mjs';
import { QoderAdapter } from './qoder.mjs';
import { RpcPipe, jsonLines } from './transport.mjs';

const config = JSON.parse(process.env.HARNESS_NATIVE_CONFIG || '{}');
let active = false; let closing = false;
const emit = value => { if (!closing) process.stdout.write(JSON.stringify(value) + '\n'); };
const finish = (text = '', error, cancelled = false) => {
  if (!active || closing) return;
  active = false;
  emit({ type: 'message_end', message: { role: 'assistant', content: [{ type: 'text', text }], stopReason: cancelled ? 'aborted' : error ? 'error' : 'stop', errorMessage: error } });
  emit({ type: 'agent_settled' });
};
class DshAdapter {
  constructor(config, emit, finish) {
    this.running = false;
    this.rpc = new RpcPipe(config, [fileURLToPath(new URL('./dsh_server.py', import.meta.url))], r => {
      if (r.method !== 'bridge/event') return;
      if (r.params.type === 'bridge_finished') { this.running = false; finish(r.params.text, r.params.error, r.params.cancelled); }
      else emit(r.params);
    }, undefined, e => { if (this.running) { this.running = false; finish('', e.message); } });
  }
  state() { return this.rpc.request('get_state'); }
  models() { return this.rpc.request('get_available_models'); }
  setModel(provider, modelId) { return this.rpc.request('set_model', { provider, modelId }); }
  thinking(level) { return this.rpc.request('set_thinking_level', { level }); }
  async prompt(message) { this.running = true; try { return await this.rpc.request('prompt', { message }); } catch (e) { this.running = false; throw e; } }
  async cancel() { await this.rpc.request('abort'); this.running = false; }
  async close() { await this.cancel().catch(() => {}); await this.rpc.close(); }
}
const classes = { codex: CodexAdapter, zcode: ZcodeAdapter, antigravity: AgyAdapter, 'qoder-cn': QoderAdapter, dsh: DshAdapter };
const Adapter = classes[config.adapter];
if (!Adapter) throw new Error(`未实现 native adapter: ${config.adapter}`);
const adapter = new Adapter(config, emit, finish);
// Initialization may reject before the first stdin command. Keep it observable rather than an unhandled rejection.
adapter.ready?.catch(() => {});
let control = Promise.resolve();
async function handle(q) {
  try {
    let data;
    switch (q.type) {
      case 'get_state': data = await adapter.state(); break;
      case 'get_available_models': data = await adapter.models(); break;
      case 'set_model': if (active) throw new Error('Session busy'); data = await adapter.setModel(q.provider, q.modelId); break;
      case 'set_thinking_level': if (active) throw new Error('Session busy'); data = await adapter.thinking(q.level); break;
      case 'prompt':
        if (active) throw new Error('Session busy'); active = true;
        try { data = await adapter.prompt(q.message); } catch (e) { active = false; throw e; }
        break;
      case 'abort':
        await adapter.cancel();
        for (let i = 0; adapter.running && i < 75; i++) await new Promise(r => setTimeout(r, 200));
        if (adapter.running) throw new Error('Native cancellation not yet confirmed');
        finish('', undefined, true); data = {}; break;
      default: throw new Error(`Unsupported command: ${q.type}`);
    }
    emit({ type: 'response', id: q.id, success: true, data });
  } catch (e) { emit({ type: 'response', id: q.id, success: false, error: e.message }); }
}
jsonLines(process.stdin, q => {
  // Serialize configuration changes/prompts. Cancellation and observation must stay responsive while a command waits.
  if (['abort', 'get_state', 'get_available_models'].includes(q.type)) void handle(q);
  else control = control.then(() => handle(q));
}, e => { process.stderr.write(e.message + '\n'); void shutdown(); });
async function shutdown() {
  if (closing) return; closing = true;
  const timeout = setTimeout(() => process.exit(1), 10000);
  try { await adapter.close(); } finally { clearTimeout(timeout); process.exit(0); }
}
process.stdin.on('end', () => void shutdown());
process.on('SIGTERM', () => void shutdown());
process.on('SIGINT', () => void shutdown());
