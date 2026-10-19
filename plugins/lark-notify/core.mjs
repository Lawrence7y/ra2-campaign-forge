/**
 * lark-notify core —— 与 harness 无关的飞书投递层。
 *
 * 设计约束（沿用 plugins/pi-feishu-notify/core.mjs 的安全模型）：
 *  - 只允许「用户事先确认过的固定收件人」，配置里的 approvedRecipient 必须与 recipient 完全一致；
 *  - 只允许 bot 身份发送，绝不回退到 user 身份；
 *  - 同一个 idempotency key 只发一次，且串行排队，避免并发刷屏；
 *  - 超时不重试（结果不确定时重试会重复发送）；
 *  - 本地台账只记录元数据，不落消息正文、不落 CLI stdout、不落凭据。
 */
import { spawn } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { basename, join } from 'node:path';
import { createHash } from 'node:crypto';

/** 抹掉可能混进通知正文的凭据形态文本。 */
export function redact(text) {
  return String(text ?? '')
    .replace(/\bBearer\s+\S+/gi, 'Bearer [REDACTED]')
    .replace(/\bsk-[A-Za-z0-9_-]{12,}/g, '[REDACTED]')
    .replace(/((?:appSecret|accessToken|refreshToken|api[_-]?key|password)\s*[=:]\s*)[^\s,;]+/gi, '$1[REDACTED]')
    .slice(0, 1400);
}

/** 稳定短 id：用作幂等键，避开 50 字符上限。 */
export function shortKey(prefix, seed) {
  return `${prefix}-${createHash('sha1').update(String(seed)).digest('hex').slice(0, 16)}`;
}

/** 运行一次 CLI，捕获 stdout/stderr，带超时与输出上限。 */
export function capture(command, args, cwd, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    let child;
    try {
      child = spawn(command, args, {
        shell: false,
        windowsHide: true,
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: {
          ...process.env,
          LARKSUITE_CLI_NO_UPDATE_NOTIFIER: '1',
          LARKSUITE_CLI_NO_SKILLS_NOTIFIER: '1',
        },
      });
    } catch (error) {
      reject(new Error(`无法启动飞书 CLI：${String(error?.message ?? error)}`));
      return;
    }
    let stdout = '';
    let stderr = '';
    let bytes = 0;
    let done = false;
    const finish = (err, result) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      if (err) reject(err);
      else resolve(result);
    };
    const timer = setTimeout(() => {
      try { child.kill(); } catch { /* 已退出 */ }
      finish(new Error('飞书 CLI 超时，发送结果不确定；不自动重试'));
    }, timeoutMs);
    for (const [stream, dest] of [[child.stdout, 'stdout'], [child.stderr, 'stderr']]) {
      stream.setEncoding('utf8').on('data', (data) => {
        bytes += Buffer.byteLength(data);
        if (bytes > 512000) {
          try { child.kill(); } catch { /* 已退出 */ }
          finish(new Error('飞书 CLI 输出超限；不自动重试'));
          return;
        }
        if (dest === 'stdout') stdout += data;
        else stderr += data;
      });
    }
    child.on('error', (error) => finish(new Error(`无法启动飞书 CLI：${String(error?.message ?? error)}`)));
    child.on('close', (code) => finish(null, { code, stdout, stderr }));
  });
}

/** 解析 lark-cli 的 JSON 信封：成功在 stdout，失败在 stderr。 */
function parseEnvelope(result) {
  const raw = result.code === 0 ? result.stdout : result.stderr;
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`飞书 CLI 返回非 JSON（exit=${result.code}）；不自动重试`);
  }
}

/**
 * 解析 lark-cli 可执行文件。只认显式配置/环境变量与本机已知安装位，
 * 找不到就报错而不是猜——猜错会静默发不出去。
 */
export function resolveCommand(configured) {
  if (typeof configured === 'string' && configured.trim() !== '') {
    if (!existsSync(configured)) throw new Error(`配置的飞书 CLI 不存在：${configured}`);
    return configured;
  }
  if (process.env.LARK_CLI && existsSync(process.env.LARK_CLI)) return process.env.LARK_CLI;

  const home = homedir();
  const candidates = [];
  const versionsRoot = join(home, '.workbuddy', 'binaries', 'node', 'versions');
  try {
    for (const version of readdirSync(versionsRoot)) {
      candidates.push(join(versionsRoot, version, 'node_modules', '@larksuite', 'cli', 'bin', 'lark-cli.exe'));
    }
  } catch { /* 该前缀不存在 */ }
  candidates.push(
    join(home, 'AppData', 'Roaming', 'npm', 'lark-cli.exe'),
    join(home, 'AppData', 'Local', 'pnpm', 'lark-cli.exe'),
    join(home, '.dsh', 'bin', 'lark-cli.exe'),
  );
  for (const candidate of candidates) if (existsSync(candidate)) return candidate;
  throw new Error('找不到 lark-cli 可执行文件；请在配置里显式写 command（或设置环境变量 LARK_CLI）');
}

/** 校验配置：任何一项不满足都拒绝发送，而不是降级发送。 */
export function validateConfig(config) {
  if (!config || typeof config !== 'object') throw new Error('缺少飞书通知配置');
  if (!/^cli_[a-zA-Z0-9]+$/.test(config.expectedAppId || '')) {
    throw new Error('缺少 expectedAppId，拒绝使用未知发送应用');
  }
  if (!['user', 'chat'].includes(config.recipient?.type)) throw new Error('recipient.type 必须为 user 或 chat');
  const pattern = config.recipient.type === 'user' ? /^ou_[a-zA-Z0-9]+$/ : /^oc_[a-zA-Z0-9]+$/;
  if (!pattern.test(config.recipient?.id || '')) throw new Error('收件人 ID 无效');
  if (config.enabled && config.approvedRecipient !== `${config.recipient.type}:${config.recipient.id}`) {
    throw new Error('收件人尚未确认，禁止自动发送');
  }
}

const DONE_STATUS = {
  completed: '已完成',
  'max-tokens': '达到输出上限后结束',
  blocked: '被策略阻断',
  aborted: '已取消',
  error: '出错',
};

/** 把一轮结束的 reason 归一成一句人话。 */
export function describeTurnEnd(reason) {
  const kind = typeof reason === 'string' ? reason : reason?.kind;
  if (kind && DONE_STATUS[kind]) return DONE_STATUS[kind];
  return kind ? String(kind) : '已结束';
}

export function nowText(timeZone = 'Asia/Shanghai') {
  try {
    return new Date().toLocaleString('zh-CN', { timeZone, hour12: false });
  } catch {
    return new Date().toISOString();
  }
}

export class FeishuSender {
  constructor(config, cwd, run = capture) {
    validateConfig(config);
    this.config = config;
    this.cwd = cwd;
    this.run = run;
    this.command = resolveCommand(config.command);
    this.chain = Promise.resolve();
    this.pending = 0;
    this.keys = new Set();
    this.identity = null;
    this.identityAt = 0;
    this.logFile = join(config.stateDir || join(homedir(), '.dsh', 'plugins', 'lark-notify'), 'notifications.jsonl');
  }

  /**
   * 确认发送身份：必须是配置里那个应用，且 bot 身份可用。
   *
   * 结果按 identityCacheMs 缓存：这条只是「发送前再确认一次」，真正的身份保证在
   * send() 里——固定 `--as bot` 且校验返回信封的 `identity === 'bot'`，
   * 所以缓存不会带来「以个人账号发出」的风险，只是省掉一次 CLI 往返。
   */
  async checkIdentity(force = false) {
    const ttl = Number.isFinite(this.config.identityCacheMs) ? this.config.identityCacheMs : 600000;
    const now = Date.now();
    if (!force && this.identity !== null && ttl > 0 && now - this.identityAt < ttl) return this.identity;
    const result = await this.run(this.command, ['auth', 'status', '--json'], this.cwd, this.config.timeoutMs);
    const envelope = parseEnvelope(result);
    if (result.code !== 0 || envelope.appId !== this.config.expectedAppId || !envelope.identities?.bot?.available) {
      this.identity = null;
      throw new Error('飞书应用身份不可用或 appId 已变化；不会切到个人身份');
    }
    this.identity = { appId: envelope.appId, appName: envelope.identities.bot.appName, identity: 'bot', available: true };
    this.identityAt = now;
    return this.identity;
  }

  /** 组装状态通知正文：只含状态、项目、时间；ask 另带被截断的事项摘要。 */
  buildText(kind, info = {}) {
    const project = info.project || basename(String(this.cwd).replace(/[\\/]+$/, ''));
    const head = kind === 'ask' ? '需要你回答 / 确认' : '本轮处理已结束';
    const lines = [
      `[DSH 通知] ${head}`,
      `项目：${project}`,
      `时间：${nowText(this.config.timeZone)}`,
    ];
    if (kind === 'ask') {
      if (info.title) lines.push(`事项：${redact(info.title).slice(0, 200)}`);
      if (this.config.includeQuestions && info.detail) lines.push(redact(info.detail).slice(0, 200));
      lines.push('请回到 DeepSeek Harness 会话处理。飞书回复不会自动回传。');
    } else {
      lines.push(`状态：${describeTurnEnd(info.reason)}`);
      if (this.config.includeCompletionSummary && info.summary) lines.push(`摘要：${redact(info.summary)}`);
    }
    return lines.join('\n');
  }

  /**
   * 发送一条通知。串行排队 + 幂等键去重 + 先验身份。
   * @param kind - 'ask' | 'done'
   * @param info - { project, title, detail, reason, summary }
   * @param key - 幂等键；同键只发一次
   */
  send(kind, info = {}, key = shortKey('dsh', `${kind}:${Date.now()}:${Math.random()}`), { dryRun = false } = {}) {
    if (!dryRun && !this.config.enabled) return Promise.resolve({ disabled: true });
    if (this.keys.has(key)) return Promise.resolve({ duplicate: true });
    if (this.pending >= 20) return Promise.reject(new Error('飞书通知队列已满'));
    this.keys.add(key);
    this.pending += 1;

    const job = this.chain.then(async () => {
      try {
        if (!dryRun && !this.config.enabled) return { disabled: true };
        await this.checkIdentity();
        if (!dryRun && !this.config.enabled) return { disabled: true };

        const text = this.buildText(kind, info);
        const args = [
          'im', '+messages-send',
          '--as', 'bot',
          '--format', 'json',
          this.config.recipient.type === 'user' ? '--user-id' : '--chat-id', this.config.recipient.id,
          '--text', text,
          '--idempotency-key', key,
        ];
        if (dryRun) args.push('--dry-run');

        const result = await this.run(this.command, args, this.cwd, this.config.timeoutMs);
        const envelope = parseEnvelope(result);
        if (result.code !== 0 || envelope.ok !== true || envelope.identity !== 'bot') {
          throw new Error(`飞书通知失败（exit=${result.code}, code=${envelope.error?.code ?? 'unknown'}）；不自动切身份或重试`);
        }
        if (!dryRun) this.log({ key, kind, status: 'sent', messageId: envelope.data?.message_id });
        return { sent: !dryRun, dryRun, messageId: envelope.data?.message_id, text };
      } catch (error) {
        if (!dryRun) this.log({ key, kind, status: 'failed-or-unknown', error: String(error?.message ?? error) });
        throw error;
      }
    });

    this.chain = job.catch(() => {});
    return job.finally(() => {
      this.pending -= 1;
      if (this.keys.size > 2048) this.keys.delete(this.keys.values().next().value);
    });
  }

  /** 只记元数据：不写消息正文、CLI 输出与凭据。 */
  log(record) {
    try {
      mkdirSync(join(this.logFile, '..'), { recursive: true });
      appendFileSync(this.logFile, `${JSON.stringify({ timestamp: Date.now(), ...record })}\n`);
    } catch { /* 本地台账写失败不影响投递结论 */ }
  }

  async drain() {
    await this.chain;
  }
}

/** 首次运行时落一份配置，方便用户直接编辑。 */
export function ensureConfigFile(file, defaults) {
  if (existsSync(file)) return false;
  mkdirSync(join(file, '..'), { recursive: true });
  writeFileSync(file, `${JSON.stringify(defaults, null, 2)}\n`);
  return true;
}
