let buffer = ''; let timer; let model = { provider: 'mock', id: 'small' };
const send = r => process.stdout.write(JSON.stringify(r) + '\n');
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buffer += chunk;
  let i;
  while ((i = buffer.indexOf('\n')) >= 0) {
    const q = JSON.parse(buffer.slice(0, i)); buffer = buffer.slice(i + 1);
    let data;
    switch (q.type) {
      case 'prompt':
        if (q.message === 'hang') continue;
        if (q.message === 'invalid') { process.stdout.write('bad json\n'); continue; }
        if (q.message === 'exit') { process.exit(2); }
        data = { disposition: 'started' };
        send({ type: 'agent_start' });
        timer = setTimeout(() => {
          send({ type: 'message_end', message: { role: 'assistant', content: [{ type: 'text', text: q.message === 'large' ? 'a'.repeat(30000) : '结果：' + q.message + '\u2028完整' }], stopReason: q.message === 'error' ? 'error' : 'stop', errorMessage: q.message === 'error' ? 'provider failed' : undefined } });
          send({ type: 'agent_end', willRetry: false });
          send({ type: 'agent_settled' });
        }, 50); break;
      case 'abort': clearTimeout(timer); send({ type: 'agent_settled' }); break;
      case 'get_state': data = { model, isStreaming: !!timer }; break;
      case 'get_available_models': data = { models: [model] }; break;
      case 'set_model': model = { provider: q.provider, id: q.modelId }; data = model; break;
    }
    send({ type: 'response', id: q.id, success: true, data });
  }
});
process.stdin.on('end', () => { clearTimeout(timer); process.exit(0); });
