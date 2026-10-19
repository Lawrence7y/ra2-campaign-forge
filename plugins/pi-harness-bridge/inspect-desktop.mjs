// Read-only inspection of already-enabled localhost CDP endpoints. No prompts or app mutations.
for (const port of [9333, 9344]) {
  try {
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(3000) })).json();
    for (const target of targets.filter(t => t.type === 'page')) {
      const ws = new WebSocket(target.webSocketDebuggerUrl);
      try {
      await new Promise((resolve, reject) => { ws.addEventListener('open', resolve, { once: true }); ws.addEventListener('error', reject, { once: true }); });
      const id = 1;
      const result = new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('CDP timeout')), 5000);
        ws.addEventListener('message', e => { const r = JSON.parse(e.data); if (r.id === id) { clearTimeout(timer); resolve(r); } });
      });
      ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: `JSON.stringify(Object.fromEntries(Object.keys(window).filter(k => /electron|bridge|api|zcode|qoder/i.test(k)).map(k => [k, typeof window[k] === 'object' && window[k] !== null ? Object.fromEntries(Object.keys(window[k]).filter(n=>/session|model|agent|project|command|rpc|workspace|task|auth|client/i.test(n)).map(n=>[n,typeof window[k][n]==='object'&&window[k][n]!==null?Object.keys(window[k][n]):typeof window[k][n]])) : typeof window[k]])))`, returnByValue: true } }));
      const r = await result;
      console.log(JSON.stringify({ port, targetId: target.id, type: target.type, globals: r.result?.result?.value, error: r.error }));
      } finally { ws.close(); }
    }
  } catch (e) { console.log(JSON.stringify({ port, error: e.message })); }
}
