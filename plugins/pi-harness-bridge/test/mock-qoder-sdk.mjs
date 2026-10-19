export const WorkerTransport = { default: {} };
export const qodercliAuth = () => ({ type: 'qodercli' });
export const hasResolvableQoderWorkerRuntime = () => true;
export function query({ prompt, options }) {
  if (options.planMode !== true || options.permissionMode !== 'default') throw new Error('unsafe mode');
  let ended = false; let resolve; const events = [];
  const emit = e => { events.push(e); resolve?.(); resolve = undefined; };
  let model = 'small';
  (async () => {
    for await (const m of prompt) {
      if (ended) break;
      emit({ type: 'assistant', session_id: 'qoder_mock', message: { content: [{ type: 'text', text: 'Qoder: ' + m.message.content[0].text }] } });
      emit({ type: 'result', subtype: 'success', session_id: 'qoder_mock', result: 'Qoder: ' + m.message.content[0].text });
    }
  })();
  return {
    initializationResult: async () => ({}),
    getAvailableModels: async () => [{ id: model }], setModel: async m => { model = m; },
    interrupt: async () => emit({ type: 'result', subtype: 'success' }), close: () => { ended = true; resolve?.(); },
    async *[Symbol.asyncIterator]() {
      while (!ended) { if (!events.length) await new Promise(r => { resolve = r; }); while (events.length) yield events.shift(); }
    },
  };
}
