/**
 * @dsh-external/lark-notify —— DeepSeek Harness 的飞书通知 hook。
 *
 * DSH 没有 Claude Code 那种 settings 里的 hooks 段；等价机制是 Cordis 插件 +
 * `ctx.on(event)`。本插件挂三个真实触发点：
 *
 *   1. 每一轮对话结束（`session/event` 的 `turn/end`，且只认根会话，不含子代理）；
 *      turn/end 之后再等 settleDelayMs，若期间同一会话又 `turn/start`（目标自动续跑、
 *      被 steer 等），就取消这次通知 —— 避免一轮任务被拆成多条消息。
 *   2. 需要用户批准（`approval/request` waterfall）。
 *   3. 需要用户回答（`tools/pre-execute` 命中 `ask_user_question`）。
 *
 * 另注册一个模型工具 `feishu_notify_waiting`，覆盖「用普通文本追问」的场景。
 *
 * 设计原则：通知是旁路，任何失败都只记日志，绝不影响 agent 主流程。
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { basename, dirname, join } from 'node:path';
import { FeishuSender, ensureConfigFile, shortKey, validateConfig } from './core.mjs';

export const name = '@dsh-external/lark-notify';

/** 插件版本；写进加载心跳，便于确认线上跑的是哪一份。 */
const VERSION = '0.1.0';

/** 依赖 tools 服务：注册 feishu_notify_waiting 需要它。 */
export const inject = ['tools'];

/** 首次运行写入磁盘的默认配置；改这里不会影响已生成的配置文件。 */
const DEFAULTS = {
  enabled: true,
  command: '',
  expectedAppId: 'cli_YOUR_APP_ID',
  recipient: {
    type: 'user',
    id: 'ou_YOUR_OPEN_ID',
    label: '待填写收件人',
  },
  approvedRecipient: 'user:ou_YOUR_OPEN_ID',
  includeQuestions: true,
  includeCompletionSummary: false,
  settleDelayMs: 1500,
  timeoutMs: 30000,
  identityCacheMs: 600000,
  timeZone: 'Asia/Shanghai',
  notifyTurnEnd: true,
  notifyApprovals: true,
  notifyUserQuestions: true,
  // 只对这些项目名（会话 header.cwd 的目录名）发通知；空数组 = 所有项目。
  onlyProjects: [],
};

const CONFIG_PATH = () =>
  process.env.DSH_LARK_NOTIFY_CONFIG || join(homedir(), '.dsh', 'plugins', 'lark-notify', 'config.json');

export function apply(ctx) {
  const configPath = CONFIG_PATH();
  const log = (level, message) => {
    const text = `[lark-notify] ${message}`;
    try {
      const logger = ctx.logger;
      if (logger && typeof logger[level] === 'function') logger[level](text);
      else if (level === 'warn' || level === 'error') console.warn(text);
      else console.log(text);
    } catch { /* 日志失败不影响主流程 */ }
  };

  try {
    if (ensureConfigFile(configPath, DEFAULTS)) log('info', `已生成默认配置：${configPath}`);
  } catch (error) {
    log('warn', `无法写入默认配置：${String(error?.message ?? error)}`);
  }

  // ── 加载心跳：证明插件确实进了宿主进程（只写元数据，便于排障） ──
  try {
    const stateDir = dirname(configPath);
    mkdirSync(stateDir, { recursive: true });
    writeFileSync(join(stateDir, 'loaded.json'), `${JSON.stringify({
      version: VERSION,
      pid: process.pid,
      loadedAt: new Date().toISOString(),
      configPath,
    }, null, 2)}\n`);
  } catch { /* 心跳写失败不影响通知功能 */ }
  log('info', `已挂载 v${VERSION}（配置：${configPath}）`);

  // ── 配置读取：缓存 5s，方便改 enabled / 收件人后无需重启 ──
  let cached = null;
  let cachedAt = 0;
  const readConfig = (force = false) => {
    const now = Date.now();
    if (!force && cached !== null && now - cachedAt < 5000) return cached;
    try {
      cached = { ...DEFAULTS, ...JSON.parse(readFileSync(configPath, 'utf8')) };
    } catch (error) {
      log('warn', `配置读取失败，已停用飞书通知：${String(error?.message ?? error)}`);
      cached = { ...DEFAULTS, enabled: false };
    }
    cachedAt = now;
    return cached;
  };

  // ── 发送器：懒加载，配置非法就停用而不是降级发送 ──
  let sender = null;
  const getSender = () => {
    if (sender !== null) return sender;
    const config = readConfig();
    validateConfig(config);
    sender = new FeishuSender(config, homedir());
    log('info', `飞书通知已装载：bot(${config.expectedAppId}) → ${config.recipient.type}:${config.recipient.id}`);
    return sender;
  };

  const deliver = (kind, info, key) => {
    let config;
    try {
      config = readConfig();
    } catch (error) {
      return Promise.resolve({ failed: String(error?.message ?? error) });
    }
    if (!config.enabled) return Promise.resolve({ disabled: true });
    let active;
    try {
      active = getSender();
    } catch (error) {
      const message = String(error?.message ?? error);
      log('warn', `飞书通知未发送：${message}`);
      return Promise.resolve({ failed: message });
    }
    return active.send(kind, info, key).then(
      (result) => {
        log('info', `飞书通知已发送（${kind}）${result?.messageId ? ` message_id=${result.messageId}` : ''}`);
        return result;
      },
      (error) => {
        const message = String(error?.message ?? error);
        log('warn', `飞书通知未发送/结果不确定：${message}`);
        return { failed: message };
      },
    );
  };

  const projectOf = (agent) => {
    try {
      const cwd = agent?.header?.cwd ?? agent?.session?.header?.cwd;
      if (typeof cwd === 'string' && cwd !== '') return basename(cwd.replace(/[\\/]+$/, ''));
    } catch { /* 取不到就用兜底 */ }
    return basename(process.cwd());
  };

  /** onlyProjects 为空表示所有项目都通知。 */
  const allowedProject = (config, project) => {
    const only = Array.isArray(config.onlyProjects) ? config.onlyProjects.filter((item) => typeof item === 'string' && item !== '') : [];
    return only.length === 0 || only.includes(project);
  };

  // ── 触发点 1：每轮对话结束 ──
  const settle = new Map();
  const cancelSettle = (sessionId) => {
    const entry = settle.get(sessionId);
    if (entry === undefined) return;
    clearTimeout(entry.timer);
    settle.delete(sessionId);
  };

  ctx.on('session/event', (session, event) => {
    try {
      if (!event || typeof event.type !== 'string') return;
      const header = session?.header ?? {};
      // 只认根会话：子代理会话带 origin/parentSession，通知它们只会刷屏。
      if (header.origin === 'subagent' || header.parentSession !== undefined) return;
      const sessionId = String(header.id ?? session?.id ?? '');
      if (sessionId === '') return;

      if (event.type === 'turn/start') {
        cancelSettle(sessionId);
        return;
      }
      if (event.type !== 'turn/end') return;

      const config = readConfig();
      if (!config.notifyTurnEnd) return;

      cancelSettle(sessionId);
      const key = shortKey('dsh-t', `${sessionId}:${event.seq}`);
      const project = typeof header.cwd === 'string' && header.cwd !== ''
        ? basename(header.cwd.replace(/[\\/]+$/, ''))
        : basename(process.cwd());
      if (!allowedProject(config, project)) return;
      const info = { project, reason: event.data?.reason };
      const delay = Number.isFinite(config.settleDelayMs) && config.settleDelayMs >= 0 ? config.settleDelayMs : 1500;
      const timer = setTimeout(() => {
        settle.delete(sessionId);
        void deliver('done', info, key);
      }, delay);
      if (typeof timer.unref === 'function') timer.unref();
      settle.set(sessionId, { timer, key });
    } catch (error) {
      log('warn', `turn/end 通知失败：${String(error?.message ?? error)}`);
    }
  });

  // 插件卸载时清掉待发定时器，避免卸载后仍发消息。
  ctx.effect(() => () => {
    for (const entry of settle.values()) clearTimeout(entry.timer);
    settle.clear();
  }, 'lark-notify: pending turn notifications');

  // ── 触发点 2：需要用户批准（waterfall，必须放行） ──
  ctx.on('approval/request', (request, next) => {
    try {
      const config = readConfig();
      const project = projectOf(request?.agent);
      if (config.notifyApprovals && allowedProject(config, project)) {
        const tool = request?.toolName ? String(request.toolName) : '某项操作';
        const reason = request?.reason ? `：${String(request.reason)}` : '（程序正在等待你的批准）';
        const seed = request?.id ?? `${tool}:${Date.now()}`;
        void deliver(
          'ask',
          { project, title: '需要你的批准', detail: `${tool}${reason}` },
          shortKey('dsh-a', `approval:${seed}`),
        );
      }
    } catch (error) {
      log('warn', `批准通知失败：${String(error?.message ?? error)}`);
    }
    return next();
  });

  // ── 触发点 3：需要用户回答（waterfall，必须放行） ──
  ctx.on('tools/pre-execute', (exec, next) => {
    try {
      const toolName = exec?.name ?? exec?.tool?.name;
      const config = readConfig();
      const project = projectOf(exec?.agent);
      if (toolName === 'ask_user_question' && config.notifyUserQuestions && allowedProject(config, project)) {
        // 0.1.7 的 exec 把参数放在 arguments；老形态是 input，两者都兼容。
        const input = exec?.arguments ?? exec?.input ?? {};
        const questions = Array.isArray(input.questions) ? input.questions : [];
        const first = questions[0] ?? {};
        const detail = [first.header, first.question].filter((part) => typeof part === 'string' && part !== '').join('：');
        const title = questions.length > 1 ? `需要你的判断（${questions.length} 个问题）` : '需要你的判断';
        const seed = exec?.callId ?? `${toolName}:${Date.now()}`;
        void deliver(
          'ask',
          { project, title, detail: detail || '程序正在等待你的回答' },
          shortKey('dsh-a', `ask:${seed}`),
        );
      }
    } catch (error) {
      log('warn', `提问通知失败：${String(error?.message ?? error)}`);
    }
    return next();
  });

  // ── 可选：普通文本追问也能触发提醒的模型工具 ──
  const tools = ctx.get('tools');
  if (tools !== undefined && typeof tools.register === 'function') {
    const waitingTool = {
      name: 'feishu_notify_waiting',
      description:
        '飞书提醒：当你要用普通文本向用户提出必须由用户回答的问题、请求补充信息或等待确认时，在回复之前调用一次，让用户即使不在电脑前也能收到飞书通知。'
        + '已完成的工作不要调用它（每轮结束的通知由 hook 自动发送）。'
        + 'question 只写必要的问题摘要，禁止包含密码、密钥、token 或完整日志。'
        + '未启用飞书通知时返回 ok=false 与原因，不要重试。',
      parameters: {
        type: 'object',
        properties: {
          question: { type: 'string', description: '要提醒用户的问题摘要，一句话即可，不要包含敏感信息。' },
        },
        required: ['question'],
        additionalProperties: false,
      },
      output: {
        schema: {
          type: 'object',
          properties: { ok: { type: 'boolean' }, status: { type: 'string' } },
          required: ['ok', 'status'],
          additionalProperties: false,
        },
        render: (_args, value) => [{
          type: 'text',
          text: value?.ok === true ? `飞书提醒已发送（${value.status}）` : `飞书提醒未发送：${value?.status ?? 'unknown'}`,
        }],
      },
      execute: async (args, exec) => {
        const question = String(args?.question ?? '').slice(0, 400);
        const result = await deliver(
          'ask',
          { project: projectOf(exec?.agent), title: '需要你的回答', detail: question },
          shortKey('dsh-a', `tool:${Date.now()}:${Math.random()}`),
        );
        if (result?.disabled === true) return { ok: false, status: '飞书通知已关闭' };
        if (result?.failed !== undefined) return { ok: false, status: result.failed };
        return { ok: true, status: 'sent' };
      },
    };
    try {
      ctx.effect(() => tools.register(waitingTool), 'lark-notify: feishu_notify_waiting tool');
    } catch (error) {
      log('warn', `feishu_notify_waiting 工具注册失败（通知功能不受影响）：${String(error?.message ?? error)}`);
    }
  }
}
