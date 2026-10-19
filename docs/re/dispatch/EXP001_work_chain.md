# EXP001 · 三层工作链首轮实验（DSH 调度入口）

> **恢复时最新规则**：外部仅 Antigravity、ZCode、Qoder CN（各自全部可用模型）；内部允许 MiMo V2.6 Flash、Step 3.7 Flash、Step 5 Preview 执行子代理。用户授权恢复原暂停派送会话，覆盖本卡旧的“禁止 DSH 内部执行模型”描述；先核对既有任务和交付再续办。

> **2026-10-03 最新执行池纠正**：之后执行任务只使用 Antigravity、ZCode、Qoder CN 三个外部 harness，三者全部实际可用模型均可选择；覆盖下文早期固定模型分配及 DSH 原生执行池授权。旧交付保留证据与真实身份；DSH 继续负责调度/复核，不冒充外部执行者。

> 授权：2026-10-02 用户要求写入工作链并开始实验，允许多会话/subagent 并行。
> 规划者：Codex。调度与验收者：**DSH 中的 DeepSeek V4.1 Flash**。模型不可验证时禁止冒充执行。
> 工作目录：`D:\Project\ra2-campaign-forge`。
> 必读：`docs/PROJECT_DIRECTION.md`、`docs/WORK_CHAIN.md`、`docs/re/AGENT_TASK_TEMPLATE.md`、`docs/re/AGENT_DELIVERY_FORMAT.md`。

## 1. 实验目标与边界

**2026-10-03 用户更新优先于下文初始模型分配**：ZCode 的 GLM 5.3 Flash 额度用尽后，按难度选 Step 3.7 Flash / Step 5 Preview；DSH 中除 `deepseek-official`、`deepseek-account` 外的供应商/模型全部可用；Antigravity 的 Gemini 3.8 Flash 可作为 DSH 子代理，优先尝试边界清晰的快速任务。允许调度层按实际可用性在授权池转派，但必须记录真实模型身份、原因、依赖和写域，不能伪造原分支已由指定模型执行。调度者仍为 OpenCode Go / DeepSeek V4.1 Flash。

验证派发、依赖、写域隔离、文件交付、独立验收、负控和返工机制是否可运行，同时产出 P1 三线的小范围基础材料。不是模型排名或性能优化验收；本轮不启动游戏、不注入、不部署、不改 exe/DLL/INI，不改已有图谱与验收件。

调度者仅写 `out/re_work/work_chain/EXP001/control/**` 和本轮 `STATUS.md`；执行者分别独占下述目录。所有人只读其他目录。你不是唯一工作者，不得回滚或覆盖别人变更。

每个任务预算 20～30 分钟；单条命令超时原则上不超过 60 秒。工具缺失、模型不可用或边界不明确时停止相应分支并报告。纯文档任务不强跑无关二进制门禁；适用性及替代证据须在回报 [6] 明示，遵循用户当前任务范围。

## 2. 开工预检（先调度者，后执行者）

用户追加限定：DeepSeek 只用 OpenCode Go 路由 `opencode-go/deepseek-v4.1-flash`；禁止 `deepseek-official` 和 `deepseek-account`。新建 DSH Bridge 已在该路由上完成通信测试，续跑仍须核对会话模型。DSH Bridge 替代原 Harness Pilot 作为 Codex→DSH 入口；下游是否可派发须由 DSH 实际探测。

1. 验证自身确为 DSH DeepSeek V4.1 Flash，保存产品模型标签/ID与会话身份。预检实际可用工具和调度方式。
2. 发现、探测 Qoder CN、DSH、ZCode，查询并核实指定模型的真实选择结果。不能根据名字猜 API ID，不能静默替换。
3. 确认回执/结果通道；保存 task_id、会话/subagent ID、负责目录和依赖；只对能验证身份及回显的通道派发一次。
4. 初始化 `control/dispatch.json`：每分支包含模型、harness、身份验证证据、状态、依赖、写域、task_id、结果路径、耗时及可获得的用量。无用量则写 unknown。
5. 检查输出目录是否已有他人产物；已有活动任务时停手升级，不覆盖。读取最新项目记录，不用旧进度替代当前状态。

## 3. 四个执行分支

### A · 性能基线差距盘点（Qoder CN / Qwen3.8 Flash）

- 写域：`out/re_work/work_chain/EXP001/qwen_perf/**`。
- 范围：只读 `docs/re/bench_map_rework.md`、`out/loadbench/H1_REMEASURE_RUNBOOK.md`、`docs/REWRITE_ROADMAP.md` 中 H1 勘误及直接引用的证据；不做全库扫描。
- 必答：旧 U0200/U0800 为什么不能算真实高负载；H1 地图和实际单位数确认步骤；当前有哪些已测/未测事实；提出下一张可执行基线卡的场景、指标、重复次数与停止条件。
- 交付：`REPORT.md`（规范 [META]+[0]～[9]）及 `inventory.json`（最多 12 项，含 claim、status、source_path、source_line、scope、next_action）。文件缺失列为 gap，不猜路径或结果。
- 验收：逐条文件/行锚可查；不把名义单位数写成实测；不承诺未经测试的性能收益。

### B · 小型 PE 只读取证工具（DSH / Step 3.7 Flash）

- 写域：`out/re_work/work_chain/EXP001/step37_pe/**`。
- 交付 `pe_probe.py`：仅标准库，读取指定 PE32 文件，报告 sha256、ImageBase、段表；接受重复 `--va`，按段映射返回文件偏移与最多 16 字节原字节。
- 判据：`PointerToRawData + (VA - (ImageBase + VirtualAddress))`；超出 raw 范围的 BSS 地址报告 `NO_FILE_BYTES`，越界、畸形或非 PE32 输入明确拒绝；不得将 `VA-0x400000` 当通用映射。禁止写入输入文件。
- 数据：`ra2youli/game.exe`、`ra2youli/gamemd.exe` 分开取证。每个镜像选择 4 个地址，覆盖代码段、资源/其他段与 BSS（不存在相应可测区则如实标明）；选择方法和镜像身份必须记录，不宣称地址语义已还原。
- 交付：脚本、`samples.json`、`REPORT.md`、原始命令/退出码。带小型合成 PE fixture 的有意义测试：不同段偏移、BSS、raw 边界、畸形文件；不修改项目工具或新增依赖。
- 验收：输入前后哈希一致、8 个取证项可重算（不足则标 PARTIAL）、fixture 正负例与实际样本分开登记。

### C · DLC 最小贯通能力盘点（ZCode / GLM 5.3 Flash）

- 写域：`out/re_work/work_chain/EXP001/glm_dlc/**`。
- 范围：只读 `ra2forge` 的 CLI、设计校验、构建和安装/卸载入口、`examples/demo_campaign.json`、README 的相关说明。
- 必答：已有制作→校验→构建→安装→卸载能力及源代码锚点；包清单、依赖/冲突、升级、存档兼容分别属于“代码已有/缺少/需运行验证”；建议一个最小战役贯通实验及可执行命令，但本轮不实际安装或启动游戏。
- 交付 `REPORT.md` 和 `capabilities.json`（最多 12 项，含 capability、status、source_path、source_line、evidence、gap、next_test）。文档宣称与代码实现分别标注，不能把没有运行写成通过。
- 验收：源代码锚点准确，建议命令与实际 CLI 接口一致，建议与事实分开。

### D · 上游工具独立审计（DSH / Step 5 Preview；依赖 B）

- 写域：`out/re_work/work_chain/EXP001/step5_review/**`；只读 B 目录。
- B 交付后，独立用标准库实现/执行一次段表和原字节复算，不直接调用 B 的转换函数当独立证据。复核两个镜像的输入指纹、8 项输出、BSS 与 raw 边界。
- 在自身目录制作一个错误映射输出或脚本副本，验证审计会报错；原件不修改。报告负控命令、差异和退出码。
- 交付 `REPORT.md`、`review.json`、审计脚本和 raw 输出。每项判 `HOLDS/FALSIFIED/INSUFFICIENT`；指出具体字段/地址和证据，不直接修 B。
- 验收：能区分正确原件和错误副本；若 B 有错，交调度层返工 B，D 在新交付上复核，最多两轮。

## 4. DSH 独立验收

A/B/C 可并行，D 依赖 B。各产品不得向同一 GUI 输入框并发派发；会话/subagent 必须具名且写域互斥。不能派发的分支记 BLOCKED，不用调度者包办来冒充整个链通过。

调度者必须自行复算：

- A 与 C 的每条记录检查实际文件和行锚，抽读内容与状态一致性，并核对待测命令。
- B 独立实读每镜像至少 2 项（合计至少 4），覆盖不同段；其余结合 D 全量审计；复跑相关测试并保存真实退出码。
- D 审计器在原件与故意错误副本上的判别结果；不能把 D 的 PASS 原封不动转成调度层 PASS。
- 各执行者输入文件前后指纹与写域清单；工作区可能有其他活动，只对明确任务归属的变更作判断，不把所有并发 mtime 归咎本轮。
- 不完整、错误、无证据的交付给具体返工单。两轮仍失败或重大争议提交 Codex，不削弱验收条件。

汇总到 `control/EXPERIMENT_REPORT.md` 与 `control/acceptance.json`，列每分支的 DISPATCHED/DELIVERED/ACCEPTED/REWORK/BLOCKED、原始命令、负控、身份证据、资源用量和剩余缺口；保持进程终态与验收状态独立。

## 5. 成功判据与回执

全部满足才可标 WORK_CHAIN_PASS：DSH 身份/模型核实、四分支身份与任务关联可追溯、至少 A/B/C 实际独立会话或 subagent 并行、D 的依赖得到遵守、四分支交付及独立验收通过、负控有效、无未授权写入。仅部分通道可用记 PARTIAL。

真实返工只在出现错误时触发；若全部首轮通过，调度层利用故意错误副本生成一份模拟拒收记录，标 SIMULATED，验证返工规则而不伪造真实失败。

最后向来源会话提交回执与文件路径，重大争议交 Codex。不得对未获明确授权的其他聊天发送消息。Codex 审阅实际材料后决定扩大实验范围。
