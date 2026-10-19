import { Type } from '@earendil-works/pi-ai';
import { defineTool, type ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { FeishuSender, NotifyLifecycle } from './core.mjs';

export default function(pi: ExtensionAPI) {
  if (process.env.PI_HARNESS_BRIDGE_CHILD === '1' || process.env.PI_FEISHU_NOTIFY_CHILD === '1') return;
  let sender: FeishuSender | undefined;
  function configPath(cwd: string) { return process.env.PI_FEISHU_NOTIFY_CONFIG || join(cwd, '.pi/feishu-notify.json'); }
  function get(cwd: string) {
    if (!sender) {
      const file = configPath(cwd);
      if (!existsSync(file)) throw new Error(`缺少飞书通知配置: ${file}`);
      sender = new FeishuSender(JSON.parse(readFileSync(file, 'utf8')), cwd);
    }
    return sender;
  }
  const warning = (ctx: any, e: unknown) => ctx.ui.notify(`飞书通知未发送/结果不确定：${String(e)}`, 'warning');
  let currentCwd = '';
  const life = new NotifyLifecycle((kind: string, info: any, key: string) => get(currentCwd).send(kind, info, key));
  pi.on('agent_start', (_e, ctx) => { currentCwd = ctx.cwd; life.start(); });
  pi.on('message_end', (e) => { life.finalMessage(e.message); });
  pi.on('agent_before_settle', (e) => { life.outcome = e.outcome; });
  pi.on('agent_settled', async (_e, ctx) => {
    currentCwd = ctx.cwd;
    try { await life.settled(); } catch(e) { warning(ctx, e); }
  });
  pi.on('ui_prompt_start', (e, ctx) => {
    currentCwd = ctx.cwd;
    // Never block the UI opening on network delivery; no auto-answer or approval.
    void life.waiting(e.title || `Pi ${e.kind} 交互需要你处理`).catch(error => warning(ctx, error));
  });
  pi.registerTool(defineTool({
    name: 'feishu_notify_waiting', label: 'Feishu Needs Your Input',
    description: '已启用飞书通知时，在用普通文本向用户提出必须回答的问题、请求补充信息或等待确认之前调用。仅向用户本地确认过的固定收件人以飞书 bot 身份发送提醒。不能选择其他收件人、开启通知、代表用户批准权限或接收飞书回复。只填写必要问题，禁止密码/密钥/完整日志。配置未启用会明确返回 disabled。',
    promptGuidelines: ['启用飞书通知后，任何需要用户回答、补充信息或确认的普通文本追问，先调用 feishu_notify_waiting，随后在正常回复中展示问题并等待用户。不要为已完成的工作调用该工具；完成通知由 agent_settled hook 自动发送。不要把密钥、账号密码、完整对话或工具日志放进 question。'],
    parameters: Type.Object({ question: Type.String({ minLength: 1, maxLength: 1400 }) }),
    async execute(_id, p, signal, _update, ctx) {
      if (signal?.aborted) throw new Error('已取消');
      currentCwd = ctx.cwd;
      const result = await life.waiting(p.question, true);
      return { content: [{ type: 'text', text: JSON.stringify(result) }], details: result };
    },
  }));
  pi.registerCommand('feishu-notify', {
    description: '飞书通知 status / on（用户确认后启用）/ off / test（启用后真实测试）/ preview（不发送）',
    handler: async (args, ctx) => {
      currentCwd = ctx.cwd;
      try {
        const s = get(ctx.cwd), c = s.config, action = args.trim() || 'status';
        if (action === 'status') {
          const identity = await s.checkIdentity();
          ctx.ui.notify(JSON.stringify({ enabled: c.enabled, sender: identity, recipient: c.recipient, includeQuestions: c.includeQuestions, includeCompletionSummary: c.includeCompletionSummary, pending: s.pending }, null, 2), 'info');
        } else if (action === 'on') {
          if (!ctx.hasUI) throw new Error('启用需用户本人确认；请在 Pi 交互界面运行 /feishu-notify on');
          const identity = await s.checkIdentity();
          const approved = await ctx.ui.confirm('确认启用飞书自动通知', `发送应用：${identity.appName || identity.appId}（bot，不是你的个人账号）\n收件人：${c.recipient.label || c.recipient.id}（${c.recipient.id}）\n内容：项目名 + 本轮状态${c.includeQuestions ? ' + 必须回答的问题/弹窗标题' : ''}${c.includeCompletionSummary ? ' + 最后回复摘要' : '；不附完成回复正文'}\n每次本轮结束和需要回答时自动发送；不转发工具日志，不自动读取飞书回复。是否允许？`);
          if (!approved) return;
          c.approvedRecipient = `${c.recipient.type}:${c.recipient.id}`; c.enabled = true;
          writeFileSync(configPath(ctx.cwd), JSON.stringify(c, null, 2) + '\n');
          ctx.ui.notify('飞书通知已启用。/feishu-notify test 可发送真实测试消息。', 'info');
        } else if (action === 'off') {
          c.enabled = false; writeFileSync(configPath(ctx.cwd), JSON.stringify(c, null, 2) + '\n');
          ctx.ui.notify('飞书通知已关闭；已提交的发送可能无法撤回。', 'info');
        } else if (action === 'test' || action === 'preview') {
          if (action === 'test' && !c.enabled) throw new Error('收件人/内容尚未确认；请先 /feishu-notify on');
          const r = await s.send('waiting', { question: '通知 hook 测试：请回到 Pi 回答；本条不要求你做任何操作。' }, undefined, { dryRun: action === 'preview' });
          ctx.ui.notify(JSON.stringify(r), 'info');
        } else throw new Error('用法：/feishu-notify status|on|off|test|preview');
      } catch(e) { warning(ctx, e); }
    },
  });
  pi.on('session_shutdown', async () => {
    // Skip queued messages at shutdown; settle delivery itself is awaited above.
    if (sender) { sender.config.enabled = false; await sender.drain(); }
    sender = undefined; life.active = false;
  });
}
