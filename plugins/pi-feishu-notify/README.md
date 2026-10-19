# Pi → 飞书机器人通知 hook

通过本机官方 `lark-cli im +messages-send --as bot` 发送，不提取或复制 appSecret/token，不使用个人身份。

## 触发规则

- **本轮完全结束**：监听 `agent_settled`，不使用会被重试/排队续接提前触发的 `agent_end`。区分正常结束、失败、取消。本轮结束不等于所有需求全部完成。
- **Pi 交互弹窗**：`ui_prompt_start` 自动提醒，包括 confirm/select/input/editor/custom 等；事件只有标题，通知不包含完整选项/弹窗正文。网络发送不阻塞弹窗，不自动批准。
- **普通文本追问**：模型需调用 `feishu_notify_waiting({question})`，工具附有 prompt guideline 要求在必须回答的追问前调用。这样避免靠标点/关键词误判，但模型漏调用时不能保证捕获所有追问。等待回答的本轮不再额外发送“完成”通知。
- 这里只监听父 Pi，会话外独立桌面任务的结束、终端程序内部输入、第三方未接入 Pi UI 的授权窗口不在自动捕获范围内。
- 本版**只发通知**，飞书回复不会自动送回 Pi；需回 Pi 回答。

## 安装

本项目已在 `.pi/settings.json` 注册本插件。`/reload` 或重新启动 Pi 后生效，范围仅本项目。
配置路径：`PI_FEISHU_NOTIFY_CONFIG` 或项目 `.pi/feishu-notify.json`。配置含固定可执行文件、expectedAppId、固定收件人，不含密钥；具体格式参见 `config.example.json`。

本机配置预填了历史登录用户作为候选收件人，**enabled=false，尚未实际发送消息**。机器人身份验证通过不代表发送权限/收件人关系已验证。

命令：

- `/feishu-notify status`：查看是否启用、应用及固定收件人。
- `/feishu-notify preview`：CLI dry-run 预览流程，不发送。
- `/feishu-notify on`：显示应用、收件人及内容范围，用户本人确认后启用并保存。
- `/feishu-notify test`：启用后发送一条真实测试通知。
- `/feishu-notify off`：关闭，跳过尚未提交的队列；已经发送的消息不会撤回。

也可以在与助手确认收件人/内容/身份后，由助手更新配置中的 `approvedRecipient` 为 `user:ou_xxx` 或 `chat:oc_xxx` 并设置 enabled=true，再进行真实测试。不要在未经用户确认时启用。更换收件人后需要重新确认。

个人账号 token 过期不妨碍 bot 身份发送；若 bot scope 缺失，应在飞书开发者后台开通，不用 `auth login` 绕过。不会自动切换身份、添加 `--yes`、改登录或开权限。

## 内容与可靠性

默认只发送项目名、时间、结束状态或待回答问题；完成回复正文默认不发送（可明确授权后设 `includeCompletionSummary=true`）。不附工具日志、完整对话、思考块。问题也不能填密码/密钥；内置模式脱敏不是完备 DLP。

每次调用校验本机 CLI 的 appId 和 bot 可用性，防止发送应用变更；以参数数组、shell:false 调用固定 exe，不拼接 shell。每条通知使用 UUID 幂等键，队列串行且有上限。超时或失败只警告，不自动重试，避免不确定发送造成重复。

审计文件 `.pi/feishu-notify/notifications.jsonl` 只记录发送元数据（时间、类别、messageId、错误状态），不记录问题正文、CLI stdout 或登录状态。配置和审计目录已加入 `.pi/.gitignore`。

重载/退出时跳过队列中尚未发送的消息，并等待正在进行的有限时长 CLI 操作。没有跨重启补发；通知失败或退出过程中未提交的消息可能丢失。

验证：`cd plugins/pi-feishu-notify && npm test`。自动测试只用 mock，不发送真实消息。真实测试必须收件人/内容/身份确认后执行。
