/**
 * 独立冒烟测试：直接驱动 core.mjs，验证 lark-cli 投递链路。
 * 用法：node smoke.mjs            → 真实发送
 *       node smoke.mjs --dry-run  → 只预演
 */
import { FeishuSender, ensureConfigFile, resolveCommand, describeTurnEnd } from './core.mjs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const configPath = join(homedir(), '.dsh', 'plugins', 'lark-notify', 'config.json');
ensureConfigFile(configPath, {
  enabled: true,
  command: '',
  expectedAppId: 'cli_YOUR_APP_ID',
  recipient: { type: 'user', id: 'ou_YOUR_OPEN_ID', label: '待填写收件人' },
  approvedRecipient: 'user:ou_YOUR_OPEN_ID',
  includeQuestions: true,
  includeCompletionSummary: false,
  settleDelayMs: 1500,
  timeoutMs: 15000,
  timeZone: 'Asia/Shanghai',
  notifyTurnEnd: true,
  notifyApprovals: true,
  notifyUserQuestions: true,
});

const { readFileSync } = await import('node:fs');
const config = JSON.parse(readFileSync(configPath, 'utf8'));
console.log('command =', resolveCommand(config.command));
console.log('describeTurnEnd =', describeTurnEnd({ kind: 'completed' }), '/', describeTurnEnd({ kind: 'error' }));

const sender = new FeishuSender(config, homedir());
const identity = await sender.checkIdentity();
console.log('identity =', identity);

const dryRun = process.argv.includes('--dry-run');
const result = await sender.send('done', { project: 'ra2-campaign-forge', reason: { kind: 'completed' } }, undefined, { dryRun });
console.log('send result =', JSON.stringify(result, null, 2));
await sender.drain();
