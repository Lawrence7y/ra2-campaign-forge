/**
 * 宿主无关的自检：用 mock ctx 跑一遍 apply()，确认插件能挂载、
 * 监听器与工具都注册成功、且 apply() 不抛异常。
 * 用法：node selftest.mjs
 */
import { apply, name, inject } from './index.js';

const handlers = new Map();
const registeredTools = [];
const effects = [];

const ctx = {
  logger: { info: (m) => console.log('INFO ', m), warn: (m) => console.log('WARN ', m) },
  on(event, fn) {
    if (!handlers.has(event)) handlers.set(event, []);
    handlers.get(event).push(fn);
  },
  get(service) {
    if (service === 'tools') return { register: (tool) => { registeredTools.push(tool.name); return () => {}; } };
    return undefined;
  },
  effect(callback, label) {
    const disposer = callback();
    effects.push({ label, disposer });
    return disposer;
  },
};

console.log('plugin name =', name);
console.log('inject =', inject);
apply(ctx);

console.log('listeners =', [...handlers.keys()].sort().join(', '));
console.log('tools =', registeredTools.join(', ') || '(none)');
console.log('effects =', effects.length);

// 模拟三种触发，确认处理函数不会抛异常（通知会真的发出去）
const WATERFALLS = new Set(['approval/request', 'tools/pre-execute']);
const fire = (event, ...args) => {
  for (const fn of handlers.get(event) ?? []) {
    const result = fn(...args, () => 'NEXT');
    if (WATERFALLS.has(event) && result !== 'NEXT') {
      throw new Error(`${event} 没有放行 waterfall：${String(result)}`);
    }
  }
};

fire('tools/pre-execute', { name: 'ask_user_question', callId: 'selftest-1', arguments: { questions: [{ id: 'q1', header: '自检', question: '插件自检：这条来自 tools/pre-execute 触发点。' }] } });
fire('approval/request', { toolName: 'pwsh', reason: '自检', id: 'selftest-approval' });

const session = { header: { id: 'selftest-session', cwd: 'D:\\Project\\ra2-campaign-forge' } };
fire('session/event', session, { type: 'turn/end', seq: 7, data: { reason: { kind: 'completed' } } });
console.log('触发完成，等待静默窗口后发送 turn/end 通知…');

// 给 settle 定时器 + 发送队列留出时间
await new Promise((resolve) => setTimeout(resolve, 6000));
console.log('OK：apply() 与三个触发点均未抛异常');
