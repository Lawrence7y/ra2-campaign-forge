import { randomUUID } from 'node:crypto';
import { DesktopConnection } from './cdp.mjs';

const capabilities = {
  'qoder-cn': ['probe', 'sessions', 'agents', 'models', 'dispatch', 'prompt', 'status', 'read', 'model', 'cancel'],
  zcode: ['probe', 'status'],
};
function required(p, key) {
  const value = p[key];
  if (typeof value !== 'string' || !value.trim()) throw new Error(`缺少 ${key}`);
  return value.trim();
}
function page(p, max = 100) {
  const limit = p.limit ?? 20, offset = p.offset ?? 0;
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > max || !Number.isSafeInteger(offset) || offset < 0 || offset > 10000) throw new Error('分页参数无效');
  return { limit, offset };
}
export class DesktopHarnessService {
  constructor(config, connect = async conf => { const c = new DesktopConnection(conf); try { await c.connect(); return c; } catch(e) { c.close(); throw e; } }) {
    this.config = config; this.connect = connect;
  }
  list() {
    return Object.entries(this.config.harnesses || {}).map(([name, cfg]) => ({ name, transport: cfg.kind === 'pending' ? 'not-implemented' : 'existing-desktop-ipc', endpoint: cfg.endpoint, actions: cfg.kind === 'pending' ? [] : capabilities[name] || [], limitation: cfg.limitation }));
  }
  async run(p) {
    if (p.action === 'list') return this.list();
    const name = required(p, 'harness'), cfg = this.config.harnesses?.[name];
    if (!cfg) throw new Error(`未配置桌面 harness: ${name}`);
    if (cfg.kind === 'pending' || !capabilities[name]?.includes(p.action)) throw new Error(`${name} 桌面端尚不支持 ${p.action}；不会改用 CLI。${cfg.limitation || ''}`);
    if (p.thinking !== undefined) throw new Error('该桌面 adapter 尚不支持会话级 thinking；不会修改全局模型偏好冒充成功');
    const c = await this.connect({ ...cfg, api: name === 'qoder-cn' ? 'qoderDesktop' : 'zcode' });
    try {
      if (name === 'zcode') return { harness: name, transport: 'existing-desktop-ipc', connected: true, targetId: c.targetId, activity: await c.call('getDesktopSessionActivity'), actions: capabilities[name] };
      if (p.action === 'probe') {
        const sessions = await c.call('listChatSessions', [1, 0, false]);
        return { harness: name, transport: 'existing-desktop-ipc', connected: true, targetId: c.targetId, sessionsAccessible: Array.isArray(sessions), modelTasksInvoked: 0, actions: capabilities[name] };
      }
      if (p.action === 'sessions') { const { limit, offset } = page(p); return { sessions: await c.call('listChatSessions', [limit, offset, false]), nextOffset: offset + limit }; }
      if (p.action === 'agents') {
        const r = await c.call('queryData', [{ type: 'agent-configurations.list' }]);
        if (r?.error) throw new Error(r.error.message || r.error.code);
        // Do not return agent instructions, MCP config, executable paths, or credentials.
        return { agents: (r?.data || []).map(a => ({ id: a.id, name: a.name, runtimeId: a.runtimeId, enabled: a.enabled, archived: a.archived })) };
      }
      if (p.action === 'models') return { models: await c.call('listChatModels', [{ workspaceDirectories: cfg.workspaceDirectories || [], forceRefresh: false, ...(p.runtimeProfileId ? { runtimeProfileId: p.runtimeProfileId } : {}) }]) };
      if (p.action === 'dispatch') {
        const agentId = required(p, 'agentId'), prompt = required(p, 'prompt');
        if (prompt.length > 32000) throw new Error('prompt 超过桌面端 32000 字符限制');
        const sessionId = randomUUID(), inputId = randomUUID();
        // Creates a real, persisted GUI session through the desktop's send use case.
        // Does not launch a parallel SDK worker or grant tools extra permissions.
        const acceptance = await this.send(c, { sessionId, inputId, agentId, prompt, clientSubmittedAt: Date.now(), dispatchMode: 'start', permissionMode: 'default', planMode: true, ...(p.cwd ? { cwd: p.cwd } : {}), ...(p.modelId ? { model: p.modelId } : {}) });
        return { sessionId, inputId, acceptance, completed: false, message: '仅表示桌面 IPC 返回了受理结果；请检查 acceptance，再用 status/read 跟踪。不自动重发。' };
      }
      const sessionId = required(p, 'sessionId');
      if (p.action === 'status') return await this.status(c, sessionId);
      if (p.action === 'read') {
        if (p.beforeMessageId) {
          const { limit } = page(p, 20);
          return await c.call('loadChatHistoryBefore', [sessionId, required(p, 'agentId'), p.beforeMessageId, limit]);
        }
        // Desktop history/open use case; may attach its own existing runtime but never sends a prompt.
        return await c.call('openChatSession', [sessionId]);
      }
      if (p.action === 'cancel') return { sessionId, result: await c.call('interruptChatSession', [sessionId]), scope: 'foreground-turn-only' };
      const state = await this.status(c, sessionId);
      if (state?.activeTurn || state?.runtimeState === 'running' || state?.queuedTurns?.length || state?.pendingInteractions?.length) throw new Error('桌面会话正在运行/排队/等待交互，拒绝改模型或追加 start；不会打断用户任务');
      if (p.action === 'model') {
        const modelId = required(p, 'modelId');
        const summary = await c.call('setChatSessionModel', [sessionId, modelId]);
        return { sessionId, requested: modelId, summary, verified: summary?.model === modelId, effective: 'next-turn' };
      }
      if (p.action === 'prompt') {
        const prompt = required(p, 'prompt'); if (prompt.length > 32000) throw new Error('prompt 超过桌面端 32000 字符限制');
        // openChatSession resolves the persisted agent identity, not an arbitrary replacement agent.
        const opened = await c.call('openChatSession', [sessionId]);
        const agentId = opened?.summary?.agentId;
        if (!agentId) throw new Error('桌面端未返回原会话 agentId，拒绝向其他 agent 投递');
        const inputId = randomUUID();
        const acceptance = await this.send(c, { sessionId, inputId, agentId, prompt, clientSubmittedAt: Date.now(), dispatchMode: 'start' });
        return { sessionId, inputId, acceptance, completed: false, permissionPolicy: 'inherit-existing-session' };
      }
      throw new Error('未知桌面操作');
    } finally { c.close(); }
  }
  async send(c, input) {
    try { return await c.call('sendChatMessage', [input]); }
    catch(e) { throw new Error(`桌面发送失败或结果不确定；sessionId=${input.sessionId}, inputId=${input.inputId}。先查询状态，不自动重发。${e.message}`); }
  }
  async status(c, sessionId) {
    // Snapshot through a short-lived unique observer. No permanent renderer hooks.
    const watchId = `pi-desktop-${randomUUID()}`;
    try {
      const r = await c.call('watchChatSessionControl', [sessionId, watchId]);
      if (!r?.state || r.state.sessionId !== sessionId || typeof r.state.runtimeState !== 'string') throw new Error('桌面控制状态无效，拒绝猜测空闲/完成');
      return r.state;
    }
    finally { await c.call('unwatchChatSessionControl', [sessionId, watchId]); }
  }
}
