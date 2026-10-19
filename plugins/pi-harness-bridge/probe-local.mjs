import { readFileSync, writeFileSync } from 'node:fs';
import { HarnessBridge } from './core.mjs';
const config = JSON.parse(readFileSync(new URL('./local-harnesses.windows.json', import.meta.url), 'utf8'));
const b = new HarnessBridge(config, process.cwd());
const names = process.argv.slice(2);
const report = [];
try {
  for (const name of names.length ? names : ['zcode', 'deepseek-harness', 'qoder-cn', 'codex', 'antigravity']) {
    const start = Date.now();
    try {
      const r = await b.probe(name);
      const result = { harness: name, connected: true, elapsedMs: Date.now() - start,
        capabilities: r.state.capabilities,
        stateKeys: Object.keys(r.state), modelResponseKeys: Object.keys(r.models || {}),
        modelCount: r.models?.models?.length ?? r.models?.data?.length,
        permission: r.state.permission,
      };
      // Local non-secret summary only. Native payloads remain in private event logs.
      report.push(result); console.log(JSON.stringify(result));
    } catch (e) { const result = { harness: name, connected: false, elapsedMs: Date.now() - start, error: e.message }; report.push(result); console.log(JSON.stringify(result)); }
  }
} finally { await b.shutdown(); }
writeFileSync(new URL('./local-probe-report.json', import.meta.url), JSON.stringify({ timestamp: new Date().toISOString(), modelTasksInvoked: 0, report }, null, 2));
if (report.some(r => !r.connected)) process.exitCode = 1;
