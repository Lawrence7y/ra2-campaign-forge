# 子代理模型路由：机制与用法（R11，2026-11-16）

> 结论先行：**白名单是"会话级、写入事件流、只认第一次"的**。改配置文件对**已存在的会话无效**，
> 必须**新开一个顶层会话**（或重启 DSH）才生效。本会话（`session-f1326fd1…`）已固化，无法补救。

## 1. 生效机制（读代码所得，`[已证]`）

来源：asar 内 `dsh/node_modules/@deepseek-ai/dsh-tool-subagent/lib/model-selection-settings.js`
（我用 `work\asarfind.cjs` + `work\asarex.cjs` 从 `app.asar` 解出来的，脚本在同目录）。

```js
// model-selection-settings.js:86-101
ctx.on("agent/created", async ({ agent }) => {
  if (子代理会话已有策略) return;                       // 不覆盖
  if (会话是子代理) allowedModels = 父会话的策略;        // ⇒ 子代理一律继承父会话
  else if (firstLiveSeq === 0) allowedModels = 当前配置; // ⇒ 只有"全新顶层会话"才记录
  if (allowedModels !== undefined) append("subagent/model-selection-policy", ...);
});

// 投影 apply（同文件 :52-58）—— **一次性**
apply: (policy, event) => (policy !== null || event.type !== "…policy") ? policy : allowedModels;
```

派发时的判定（`dsh-tool-subagent/lib/index.js:86`）：

```js
policy === undefined
  ? (只有与父路由完全相同才放行)
  : policy.routes.some(r => r.provider === provider && r.model === model)   // 不在表里 ⇒ 抛错
```

⇒ 三条推论：
1. **配置热加载对"发号子代理"不起作用**（`harness_route_check` 读实时配置、说可用；派发读会话事件流、仍拒）。**两者不一致是正常现象，不是工具 bug。**
2. **子代理不能"自带"更多模型**：它的策略来自父会话。
3. 只有 `firstLiveSeq === 0` 的**全新顶层会话**才拿最新配置。

本会话的固化内容来自启动那一刻的配置，即当时还写着拼错的 `work/cn:hy4free`（不存在该模型）
⇒ 本会话里 `hy4flash-free` / `hy4flash` 都不可派。`[静态推断]`（会话日志是 zstd，未解压核对内容）

## 2. 当前配置（已就绪，待新会话生效）

`C:\Users\Administrator\.dsh\profiles\desktop\cordis.patch.yml` →
`subagent-model-selection-settings.allowedModels`，现为 **5 条**（`harness_route_check` revision=3）：

| provider | model | 说明 |
|---|---|---|
| `magpie-anthropic` | `work/cn:hy4flash-free` | **免费 HY 4 flash —— 优先** |
| `magpie-anthropic` | `work/cn:hy4flash` | 付费/另一只在飞通道（用户说"繁忙"时用另一只） |
| `magpie-anthropic` | `work/cn:deepseek-v4.1-flash` | 补充（设置页显示"拥堵"时降级用它） |
| `magpie-anthropic` | `zcode/GLM-5.3-Flash` | 保留 |
| `magpie-responses` | `codex/gpt-6.1-sol` | 裁决通道，保留 |

## 3. 派发时的硬约束

- **`hy4flash-free` / `hy4flash` 只支持 `reasoningEfforts: high`**（`cordis.patch.yml` 里只有 `high: high`）。
  ⇒ 派发时**不要**传 `low`/`max`/`off`，要么省略、要么传 `high`，否则会被服务端拒绝。
- `deepseek-v4.1-flash` 支持 `off/low/high/max`（本项目默认用 `high`）。
- 空跑测试一个最小卡（只让它回一行）是确认路由最快的方式；失败信息形如
  `child LLM route "…" is not allowed for this Session` ⇒ 就是本会话策略固化，不是模型不可用。

## 4. 下个会话怎么"多用这两个"

1. 新开顶层会话（或重启 DSH）→ 策略自动记录当前 5 条。
2. 派卡时显式指定：`provider=magpie-anthropic, model=work/cn:hy4flash-free`（不带 effort）。
3. 免费那只报错/限流时换 `work/cn:hy4flash`；两只都不稳再落 `work/cn:deepseek-v4.1-flash`（effort=high）。
4. 每轮先跑一次最小空跑卡确认实际落到的模型；**不要**用 `harness_route_check` 的结果代替实际派发验证
   （它读实时配置，会给出假阳性）。

### 4.1 可选：把免费 HY 4 设为子代理**默认**模型

`subagent` 工具支持 `agentOptions`（`dsh-tool-subagent/lib/index.js:295-302` 的 Config schema），
把它加到 `cordis.patch.yml` 的 `- id: subagent` 块即可，**默认值对显式 `model=` 仍会被覆盖**：

```yaml
- id: subagent
  name: "@deepseek-ai/dsh-subagent"
  config:
    maxDepth: 2
    agentOptions:
      provider: magpie-anthropic
      model: work/cn:hy4flash-free     # 只支持 high，故不写 reasoningEffort
```

⚠️ **两个坑（我本轮刻意没有替你打开）**：
1. **默认值在派发时校验**（`index.js:441-450` `preflightChildLlmRoute`）。
   若当前会话的固化策略里没有该路由，**所有不带 `model=` 的子代理派发都会直接失败**。
   ⇒ 只在**新会话**里加这行（该会话策略已含 hy4flash-free）。
2. 若免费通道临时不可用，默认值会让"忘了写 model"的派发全部失败；显式 `model=` 可绕过。
   所以这行是**便利项**，不是必需项。

## 5. 本轮的实际处置

- 配置文件：`allowedModels` 已含 **两个 hy4flash**（并删掉了一条重复的 `work/cn:hy4flash`——重复会让
  `assertAllowedModelRoutes` 抛错，可能让整条白名单失效）。
- **未**设置 `agentOptions` 默认值（见 §4.1 的坑 1：会让本会话派发全失败）。
- 本会话剩余工作如仍需派发，只能用 `deepseek-v4.1-flash`；要立刻用 hy4flash，请**新开会话**。
