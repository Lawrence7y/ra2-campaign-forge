import { spawn } from 'node:child_process';
import { appendFileSync, mkdirSync } from 'node:fs';
import { join, basename } from 'node:path';
import { randomUUID } from 'node:crypto';

export function redact(text) {
  return String(text || '').replace(/\bBearer\s+\S+/gi, 'Bearer [REDACTED]').replace(/\bsk-[A-Za-z0-9_-]{12,}/g, '[REDACTED]').replace(/((?:appSecret|accessToken|refreshToken|api[_-]?key|password)\s*[=:]\s*)[^\s,;]+/gi, '$1[REDACTED]').slice(0, 1400);
}
export function capture(command, args, cwd, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { shell: false, windowsHide: true, cwd, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: '1', LARKSUITE_CLI_NO_SKILLS_NOTIFIER: '1' } });
    let stdout = '', stderr = '', bytes = 0, done = false;
    const finish = (err, result) => { if (done) return; done = true; clearTimeout(timer); err ? reject(err) : resolve(result); };
    const timer = setTimeout(() => { child.kill(); finish(new Error('CLI 超时，发送结果不确定；不自动重试')); }, timeoutMs);
    for (const [stream, dest] of [[child.stdout, 'stdout'], [child.stderr, 'stderr']]) stream.setEncoding('utf8').on('data', data => {
      bytes += Buffer.byteLength(data); if (bytes > 512000) { child.kill(); finish(new Error('CLI 输出超限；不自动重试')); return; }
      if (dest === 'stdout') stdout += data.toString(); else stderr += data.toString();
    });
    child.on('error', () => finish(new Error('无法启动配置的飞书 CLI')));
    child.on('close', code => finish(null, { code, stdout, stderr }));
  });
}
function parse(result) {
  try { return JSON.parse(result.code === 0 ? result.stdout : result.stderr); } catch { throw new Error(`飞书 CLI 返回非 JSON（exit=${result.code}）；不自动重试`); }
}
export function validateConfig(config) {
  if (!config.command || typeof config.command !== 'string') throw new Error('缺少本地 CLI command');
  if (!/^cli_[a-zA-Z0-9]+$/.test(config.expectedAppId || '')) throw new Error('缺少 expectedAppId，拒绝使用未知发送应用');
  if (!['user', 'chat'].includes(config.recipient?.type)) throw new Error('recipient.type 必须为 user 或 chat');
  if (!(config.recipient.type === 'user' ? /^ou_[a-zA-Z0-9]+$/ : /^oc_[a-zA-Z0-9]+$/).test(config.recipient.id || '')) throw new Error('收件人 ID 无效');
  if (config.enabled && config.approvedRecipient !== `${config.recipient.type}:${config.recipient.id}`) throw new Error('收件人尚未确认，禁止自动发送');
}
export class FeishuSender {
  constructor(config, cwd, run = capture) { validateConfig(config); this.config = config; this.cwd = cwd; this.run = run; this.chain = Promise.resolve(); this.pending = 0; this.keys = new Set(); }
  async checkIdentity() {
    const result = await this.run(this.config.command, ['auth', 'status', '--json'], this.cwd);
    const r = parse(result);
    if (result.code !== 0 || r.appId !== this.config.expectedAppId || !r.identities?.bot?.available) throw new Error('飞书应用身份不可用或 appId 已变化；不会切到个人身份');
    return { appId: r.appId, appName: r.identities.bot.appName, identity: 'bot', available: true };
  }
  send(kind, info = {}, key = randomUUID(), { dryRun = false } = {}) {
    if (!dryRun && !this.config.enabled) return Promise.resolve({ disabled: true });
    if (this.keys.has(key)) return Promise.resolve({ duplicate: true });
    if (this.pending >= 20) return Promise.reject(new Error('飞书通知队列已满'));
    this.keys.add(key); this.pending++;
    const job = this.chain.then(async () => {
      try {
        if (!dryRun && !this.config.enabled) return { disabled: true };
        await this.checkIdentity();
        if (!dryRun && !this.config.enabled) return { disabled: true };
        const project = basename(this.cwd.replace(/\\/g, '/'));
        const status = kind === 'waiting' ? '需要你回答 / 确认' : info.outcome === 'error' ? '本轮处理失败' : info.outcome === 'aborted' ? '本轮已取消' : '本轮处理已结束';
        let text = `[Pi 通知] ${status}\n项目：${project}\n时间：${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`;
        if (kind === 'waiting') {
          if (this.config.includeQuestions && info.question) text += `\n问题：${redact(info.question)}`;
          text += '\n请回到 Pi 会话回答。飞书回复暂不会自动回传。';
        } else {
          if (this.config.includeCompletionSummary && info.summary) text += `\n回复摘要：${redact(info.summary)}`;
          text += '\n这是本轮运行结束通知，不保证全部需求已经完成。';
        }
        const args = ['im', '+messages-send', '--as', 'bot', '--format', 'json', this.config.recipient.type === 'user' ? '--user-id' : '--chat-id', this.config.recipient.id, '--text', text, '--idempotency-key', key];
        if (dryRun) args.push('--dry-run');
        const result = await this.run(this.config.command, args, this.cwd);
        const r = parse(result);
        if (result.code !== 0 || r.ok !== true || r.identity !== 'bot') throw new Error(`飞书通知失败（exit=${result.code}, code=${r.error?.code ?? 'unknown'}）；不自动切身份或重试`);
        if (!dryRun) this.log({ key, kind, status: 'sent', messageId: r.data?.message_id });
        return { sent: !dryRun, dryRun, messageId: r.data?.message_id };
      } catch(e) {
        if (!dryRun) this.log({ key, kind, status: 'failed-or-unknown', error: e.message });
        throw e;
      }
    });
    this.chain = job.catch(() => {});
    return job.finally(() => { this.pending--; if (this.keys.size > 2048) this.keys.delete(this.keys.values().next().value); });
  }
  log(record) {
    // Metadata only: never persist message text, CLI stdout, auth status, or credentials.
    try { const dir = join(this.cwd, '.pi', 'feishu-notify'); mkdirSync(dir, { recursive: true }); appendFileSync(join(dir, 'notifications.jsonl'), JSON.stringify({ timestamp: Date.now(), ...record }) + '\n'); } catch { /* Delivery is not retried if the local ledger fails. */ }
  }
  async drain() { await this.chain; }
}
export class NotifyLifecycle {
  constructor(deliver) { this.deliver = deliver; this.active = false; this.waitIndex = 0; }
  start() { if (!this.active) { this.active = true; this.runId = randomUUID(); this.outcome = 'completed'; this.summary = ''; this.awaiting = false; this.waitIndex = 0; } }
  finalMessage(message) {
    if (message?.role !== 'assistant') return;
    this.summary = (message.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n');
  }
  waiting(question, explicit = false) {
    if (explicit) { this.start(); this.awaiting = true; }
    const key = `${this.active ? this.runId : randomUUID()}:${++this.waitIndex}`;
    return this.deliver('waiting', { question }, key);
  }
  async settled() {
    if (!this.active) return;
    this.active = false;
    if (!this.awaiting) return await this.deliver('completed', { outcome: this.outcome, summary: this.summary }, this.runId);
  }
}
