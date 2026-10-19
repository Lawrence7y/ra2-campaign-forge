import { jsonLines } from '../adapters/transport.mjs';
const flavor = process.argv[2];
let timer; let model = { providerId: 'default', modelId: 'small' }; let running = false; let text = ''; let turn = 0;
const send = v => process.stdout.write(JSON.stringify(v) + '\n');
const snapshot = () => ({ session: { sessionId: 'sess_mock', model }, runtime: { activeTurnId: running ? 'turn_mock' : undefined }, projection: { status: running ? 'running' : 'idle' }, settings: { model: { available: [{ ref: model, label: 'Mock' }] }, thoughtLevel: { available: ['high'] } }, messages: [{ info: { role: 'assistant' }, parts: [{ type: 'text', text }] }] });
if (flavor === 'antigravity' && process.argv.includes('models')) { console.log('small\nlarge'); process.exit(0); }
jsonLines(process.stdin, async q => {
  if (flavor === 'antigravity') {
    send({ event: 'init', conversation_id: 'conversation_mock', init: {} });
    send({ event: 'step_update', step_update: { step_type: 'agent_response', text_delta: '结果' } });
    send({ event: 'result', result: { status: 'SUCCESS', conversation_id: 'conversation_mock', response: 'AGY: ' + q.message.content } });
    setTimeout(() => process.exit(0), 20); return;
  }
  if (q.method === 'initialized') return;
  let result;
  if (flavor === 'zcode' && q.jsonrpc) { send({ id: q.id, error: { message: 'ZCode rejects jsonrpc field' } }); return; }
  switch (q.method) {
    case 'initialize': result = { userAgent: 'mock' }; break;
    case 'model/list': result = { data: [{ id: 'small' }, { id: 'large' }] }; break;
    case 'thread/start': result = { thread: { id: 'thread_mock' } }; break;
    case 'turn/start':
      running = true; turn++; result = { turn: { id: 'turn_' + turn } };
      timer = setTimeout(() => {
        running = false;
        send({ method: 'item/agentMessage/delta', params: { delta: '返回\u2028文本' } });
        send({ method: 'item/completed', params: { item: { type: 'agentMessage', text: 'Codex: ' + q.params.input[0].text } } });
        send({ method: 'turn/completed', params: { turn: { id: result.turn.id, status: q.params.input[0].text === 'error' ? 'failed' : 'completed', error: { message: 'mock failed' } } } });
      }, 40); break;
    case 'turn/interrupt': clearTimeout(timer); running = false; send({ method: 'turn/completed', params: { turn: { status: 'interrupted' } } }); result = {}; break;
    case 'runtime/capabilities': result = { independentPlanState: true }; break;
    case 'session/create': result = snapshot(); break;
    case 'session/read': result = snapshot(); break;
    case 'session/setModel': model = q.params.model; result = snapshot(); break;
    case 'session/setThoughtLevel': result = snapshot(); break;
    case 'session/send':
      running = true; result = { accepted: true }; timer = setTimeout(() => { running = false; text = 'ZCode: ' + q.params.content; }, 30); break;
    case 'session/stop': clearTimeout(timer); running = false; result = {}; break;
    case 'session/close': result = { closed: true }; break;
    default: send({ id: q.id, error: { message: 'Unknown method ' + q.method } }); return;
  }
  send({ id: q.id, result });
}, e => { console.error(e); process.exit(1); });
process.stdin.on('end', () => { clearTimeout(timer); process.exit(0); });
