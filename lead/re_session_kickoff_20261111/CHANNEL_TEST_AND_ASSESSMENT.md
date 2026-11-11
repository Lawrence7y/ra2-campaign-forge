# 本轮开局：通道连通性实测 + 项目状态评估（2026-11-11 24:1x / 2026-11-12 00:2x Asia/Shanghai）

> 记录人：调度方（DSH 会话，Lead）。用途：本轮派发依据的实测底账。
> 纪律：**零真机**（未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存）；本次只新增本目录，其余只读；未 commit、未 push。

---

## 1 · 通道连通性实测（三条，全部实跑）

用户指定优先级：**magpie 的 hy4 与 glm5.3flash（优先）**，**call-agy 调 Antigravity Gemini 3.8 Flash（次优先）**。

### 1.1 路由白名单核对（派发前判定）

`list_subagent_models` / `harness_route_check` 实测：

| 项 | 结果 |
|:--|:--|
| 子代理模型白名单 | `enabled=true revision=1`，**共 4 条路由**，全部在 `magpie-anthropic` 下 |
| 可用模型 | `work/cn:hy4free`（Hy4·work）、`work/cn:deepseek-v4.1-flash`、`zcode/GLM-5.3-Flash`、`zcode/GLM-5.3-Flash-Trial` |
| `magpie-anthropic/work/cn:hy4free` | ✅ **在白名单里，子代理派发可用** |
| `magpie-anthropic/zcode/GLM-5.3-Flash` | ✅ **在白名单里，子代理派发可用** |

注：provider 的正确 id 是 **`magpie-anthropic`**，不是 `magpie`——直传 `magpie` 会被拒（实测报错 `LLM provider "magpie" is not allowed for this Session`）。

### 1.2 冒烟实测结果

| 通道 | 派发方式 | 结果 | 耗时 | 实测回执 |
|:--|:--|:--|--:|:--|
| **hy4free** | 原生 subagent，`provider=magpie-anthropic` + `model=work/cn:hy4free` | ✅ **CHANNEL_OK**，回 `MODEL_TAG: hy4free / ANSWER: 4` | 秒级 | subagent id `80b59123` |
| **GLM-5.3-Flash** | 原生 subagent，`provider=magpie-anthropic` + `model=zcode/GLM-5.3-Flash` | ✅ **CHANNEL_OK**，回 `MODEL_TAG: glm53flash / ANSWER: 4` | 秒级 | subagent id `f595692e` |
| **agy / Gemini 3.8 Flash** | `call_agy.ps1` 冒烟（"Reply exactly: Antigravity is connected"） | ✅ **status=SUCCESS** | **28.5 s** | `conversation_id=f105c8a7-0a56-4d3f-a206-6dc1d939e682`；`agy_cumulative_duration=11.9s` / 1 turn；tokens in=**12,161** out=**279** thinking=**269** total=**12,440** |

**agy 回复正文亲验**：handoff 文件 L5 = `Antigravity is connected.`（`grep` 2 命中：L5 为回复体、L10 为原 prompt 回显）。

### 1.3 一条必须登记的障碍（agy 首次失败，非空转）

第一次调用 agy **在模型调用前即失败**，`elapsed=0.0s`、`status=ERROR`，**零 token 消耗**：

```
HOST_SANDBOX_BLOCKED: call-agy cannot write Antigravity's required local state directory:
C:\Users\Administrator\.gemini\antigravity-cli
([Errno 13] Permission denied: ...\.call-agy-write-probe-16052-...)
```

原因是当时 DSH 文件策略为 `workspace-write`，而 agy 的状态目录在会话工作区之外。**策略切到 `danger-full-access` 后即通（28.5s SUCCESS）**。
⇒ 结论：**agy 通道要求宿主对 `~/.gemini/antigravity-cli` 有写权限**；`workspace-write` 下不可用。这是 `call-agy` skill 自述并预设的边界，不是配置错误。

### 1.4 与上一轮 STATUS_BOARD 判定的差异（重要更正）

上一轮（同日 21:1x）的 `lead/re_dispatch_20261111/STATUS_BOARD.md` §2 结论是：

> 「显式传 `provider/model` 一律被拒……该工具实例禁用『按调用指定模型』⇒ **要子代理用 hy4，须新开会话或在会话内选择一次**」

**本轮实测推翻该判定的适用性**：本会话**可以**按调用显式指定 `provider` + `model`，两条 magpie 路由均派发成功并回传了模型自报 tag。
⇒ 该判定的成立条件是**那个工具实例/会话状态**，不是全局配置。`cordis.patch.yml` 的 `subagent-model-selection-settings.enabled: true` + 三条 `allowedModels` **配置本身是对的**（与上轮结论一致），只是在旧会话里没生效。

### 1.5 通道可用性小结

| 通道 | 本轮判定 | 备注 |
|:--|:--|:--|
| magpie-anthropic / **hy4free** | ✅ 可用（原生 subagent） | 上轮经 pi CLI 的两趟「零落盘」**不构成对原生 subagent 通道的证据**——那是另一条传输层 |
| magpie-anthropic / **GLM-5.3-Flash** | ✅ 可用（原生 subagent） | 4 条路由中额度可用 |
| **call-agy → Gemini 3.8 Flash** | ✅ 可用，**但须 `danger-full-access`** | 上轮实测为「唯一稳定可靠的重活通道」（27s / 464s / 1089s / 1081s 全 SUCCESS）；**注意长任务会卡死，须 `--timeout` 硬上限 + 分段** |

---

## 2 · 项目状态评估（实测项标「实算」，转引项标「转引」）

### 2.1 三个硬指纹（本节实算）

| 项 | 实测值 | 与既有记录对照 |
|:--|:--|:--|
| 主台账 `lead/GOAL_THREE_TARGETS_20261018.md` | **788,030 B** / sha256 `a2579798976f00b4dc09edc85c0b2efa0255289411819297047e2362ba3bffda` / **9,845 行** | ✅ 与 STATUS_BOARD §9.1「759,518 → 788,030 B，10/10 自检 PASS」一致 |
| 靶件 `ra2bench/gamemd.exe` | **4,825,360 B** / sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | ✅ 与派工书期望值**逐字一致** |
| Python | 3.12.10 | — |

台账节次计数（实算，按行计）：`§604`=12 行（含引用）、**`§605`=1、`§606`=1、`§607`=2、`§608`=1、`§609`=1**。

**§607 出现 2 次的歧义已当场核清（不要遗留为开口）**：按 `^##+ *§6\d\d` 抓标题行，`§600…§609` **各恰好 1 个标题**，无重复节：
- `L9787` = `## §607 · ★★ 订正登记：N-8 质疑 + R3 第二方复算 + 第三方复核……`
- `L9841` = 正文里对**第三笔草案**的交叉引用（`…暂编 §607…`），在 `§609` 节内。

⇒ **判据定谳**：入账自检的「§605–§609 各出现 1 次」应读作 **「节标题唯一」**，不是「字符串全文字符串出现 1 次」（后者必然被交叉引用打破）。
按此口径，**§605–§609 五笔均正确入账、无重复、无遗漏**；`§604` 的 12 次均为他节对其数值的引用，属正常。

### 2.2 工具链健康度（实算，全部本轮真跑）

| 组件 | 命令 | 结果 |
|:--|:--|:--|
| `ra2re` 自检 | `python -X utf8 -m ra2re selftest`（`PYTHONPATH=<repo>`） | ✅ **EXIT=0，全部通过 20 项**（含 988 类描述符、vtable ≥900、blit 族 ≥40 实现、两次解析确定性一致） |
| `ra2forge` 校验 | `python -X utf8 -m ra2forge validate examples/demo_campaign.json` | ✅ **EXIT=0，`OK: 3 mission(s)`** |
| `ra2opt` 体检（只读） | `python -X utf8 -m ra2opt audit` | ✅ **EXIT=0，严重 0 / 警告 0 / 建议 4 / 已达标 4** |

**一条操作性发现**：本项目惯例写法 `python -I -X utf8 <绝对路径>` 用于**按绝对路径跑脚本**；
用 `-I -m <包名>` 会因隔离模式不把 cwd 放进 `sys.path` 而报 `No module named ra2re/ra2forge`（实测 EXIT=1）。
⇒ 跑包入口须 `python -X utf8 -m <pkg>` + `PYTHONPATH`，或改用绝对脚本路径。**这不影响既有探针**（它们都是绝对路径脚本）。

### 2.3 逆向本体状态（转引 `lead/re_progress_check_20261111/RE_PROGRESS_20261111.md`，含其 §8 自查与 §9 异族核验）

- **量很大但在跑**：2026-11-06 起新增 **182 个轮次目录**、**153 份带结论 md**（正确分解 **182 = 153 报告 + 18 无报告 + 11 空**，该分解已由异族核验修正过一轮）。
- **账面落后盘面**：台账最后落 §604（11-06）；11-07~11-11 五笔草案 §605–§609 上轮已并入（本节点已实算确认 788,030 B）。
- **方向已切回静态逆向**（11-10/11-11）：6 个探针全指同一族对象——`0x54A4F0`/`0x54A630` 虚表 slot2 调用面、`0x54A56E` 数据依赖链、HouseClass owner 归属、地图预置槽位解码、PlayerControl/PercentBuilt 语义。**但只有 `_out.txt/_out.json`，无 md 结论、无入账。**
- **两条独立线的状态**：**RE-ATLAS 停摆 12 天**（R-064 / 10-30 后零轮）；**GOAL-3T 在跑**。
- **三目标：无一闭合**。① 机制未闭合（「为什么慢」仍缺运行期采集通道）；② 正常退出硬门槛未达成（RC-4 不收口）；③ 保持态（每个新补丁仍需独立核验）。
- **唯一硬阻塞 = D-13**（E3 栈采样三选一 A/C/暂停），需用户一句话；PAUSE + BLOCKED 自 10-26 维持至今。

### 2.4 复现性风险（本项目当前最大隐忧，转引 + 本轮侧证）

**10 天零提交**：HEAD 停在 2026-11-01（`2657458`），工作树 **13 项已跟踪改动 + 约 263 项未跟踪**全部未入库。
⇒ 182 个轮次的证据件**只存在于本机磁盘**，不具可移交性；一旦磁盘出事不可恢复。
这与项目自身「台账 append-only + 指纹绑定」纪律**反差明显**——证据链做得极严，入库环节却是断的。

---

## 3 · 本轮派发（按通道与写域互斥切分）

| 包 | 内容 | 通道 | 写域 |
|:--|:--|:--|:--|
| WP-E | WP-B′ 两点保留质疑的**定级勘误**（CFG 推断降级全表普查 + `_ps_disasm` 复现门口径）+ 出 `LEDGER_SECTION_DRAFT_v2.md` | magpie / **GLM-5.3-Flash** | `lead/re_chain_synth_v2_20261111/` |
| WP-F | WP-D Top-10 的**批次一（5 个静态逆向轮）**固化成可入账 md | magpie / **hy4free** | `lead/re_round_batch1_20261111/` |
| WP-G | 对 WP-E 产出的 v2 草案做**异族独立核验** | call-agy / **Gemini 3.8 Flash** | 待定（依赖 WP-E 收线） |

派发原则依据：`docs/PROJECT_DIRECTION.md` §4（执行组织）+ 铁律五条（零真机 / 只读边界 / `-I -X utf8` 绝对路径 / 只用材料直接支持的话 / 边界与未验必写）。

---

## 4 · 边界与未验（本节如实）

1. 本次**未重跑**任何 `lead/` 下的逆向探针脚本；§2.3/§2.4 的数字均**转引**既有报告，未独立复算。
2. 本次**未启动游戏**、未 attach、未读活进程内存、未写任何采样代码。
3. **agy 的真实长任务承载力本轮未测**——只测了 28.5 s 冒烟。上轮记录的长任务均为**卡死风险**（1089s/1081s 完成，但另有 1125s/1139s 零落盘），故本轮对 agy 派发必须带 `--timeout` 硬上限。
4. `origin/main` 本地引用停在 2026-10-24 且**未 fetch**，故「远端是否有更新」「ahead/behind」**无法判定**。
5. §2.1 的 §607 双次出现**已当场核清并定谳口径**（见该节），不再是开口项。
6. 本目录为本次唯一新增件；**未改台账、未改 PENDING_DECISIONS、未 commit、未 push**。
