# IMPL001 · 独立 DSH 调度会话并行实施

> **恢复时最新规则**：外部仅 Antigravity、ZCode、Qoder CN，各自模型全部可用；DSH 内部另允许 MiMo V2.6 Flash、Step 3.7 Flash、Step 5 Preview 子代理。覆盖下方旧的“禁止内部执行子代理”限制。用户授权恢复原暂停会话，先核验历史交付与失败/中断记录再续办，不重复整轮实施。

> **最新执行池覆盖规则**：用户要求执行只使用 Antigravity、ZCode、Qoder CN 三个外部 harness，三者内部全部实际可用模型都可选择。覆盖旧任务卡/会话提示词中允许其他 harness 或 DSH 原生执行模型作为替代的描述。DSH 普通会话仍负责调度与复核。

> 2026-10-03 用户澄清：多开的是“各自能派外部 harness 子代理的独立 DSH 调度会话”，不是一个主会话加三个队友。
> Codex 负责本卡规划与验收边界；普通 DSH 调度会话使用 opencode-go/deepseek-v4.1-flash，挂到 ra2-campaign-forge 工作区。
> 本轮从基础盘点转入两项可隔离的工具原型实现，不改引擎、现网补丁和安装目录。全局目标依 docs/PROJECT_DIRECTION.md、docs/WORK_CHAIN.md。

## 1. 所有权

- 原 EXP001 调度会话：继续收口原任务、独立审计与返工，不迁移或重复派发原包；公共 EXP001 索引仍由它唯一维护。
- 新普通会话 PERF：唯一负责 `out/re_work/work_chain/IMPL001/perf/**` 的调度索引与下游任务。
- 新普通会话 DLC：唯一负责 `out/re_work/work_chain/IMPL001/dlc/**` 的调度索引与下游任务。
- Codex：维护 `out/re_work/work_chain/IMPL001/coordinators.json`，记录普通会话 ID、工作区与模型读回；其他调度者不改该件。

每个调度者只写自身 `control/**`，执行者分别独占 `worker/**`、`fixtures/**`、`review/**`。禁止互改，禁止调度者代写执行者产物。不得同时改 tools/、ra2forge/、ra2render/ 或旧图谱与验收件。此轮原型通过后由 Codex 决定集成卡。

## 2. PERF 工具原型

实现 `perf/worker/validate_measurement.py`（Python 标准库、独立 CLI，JSON 输入），为真实负载记录提供最小元数据验收：

- 顶层 `schema_version=1`、`target_exe`（game.exe/gamemd.exe）、`exe_sha256`、`config_sha256`、`map_sha256`（64 位十六进制）、`hardware` 非空说明、`scenario` 非空说明、`runs` 至少三组。
- 每组需要 `actual_units` 正整数、`count_source.kind=runtime`、`count_source.evidence` 非空定位说明、`tick_ms` 非空数组（有限、正数）。布尔值不当整数；NaN、Infinity、缺失/错误类型均拒绝。
- 可选 `declared_units` 仅作地图名义负载信息，不能替代 actual_units，不能生成实际单位数。元数据通过也不证明输入数据真伪，输出明确注明这一限制。
- 输出逐组 actual_units、样本数、耗时中位数及按 nearest-rank 算 P95/P99（说明方法）；保留各组差异，不把不同负载混成一条曲线或自动宣称收益。
- 有效输入退出 0，无效输入非 0，给出字段路径；不执行输入文件中的命令，不改输入文件。

并行包 P-FIX：独立模型负责 fixtures/ 下的有效/无效 JSON 与期望结果说明，直接依据本卡生成，不调用待实现工具；覆盖三组缺失、无运行计数证据、错误哈希、布尔单位数、非有限耗时、名义/实际不一致但如实记录等。

P-IMPL 与 P-FIX 可并行。二者交付后 P-AUD 独立模型只写 review/，运行工具与 fixtures、做额外负控，调度者独立核验真实退出码和关键统计。输出原始命令、报告、模型/task_id 与结果路径。没有真机数据时只验合成 fixture，不伪称高负载重测完成。

## 3. DLC 清单原型

实现 `dlc/worker/validate_package_manifest.py`（Python 标准库、独立 CLI，JSON 输入），先实现内容包清单验证，不实现安装/发布：

- 顶层 `schema_version=1`、`package_id`（小写字母/数字起始，可含连字符，最长 64）、`version`（三段非负整数版本，禁止无意义前导零）、`target_exe`（game.exe/gamemd.exe）、`target_sha256`（64 位十六进制）、`files` 非空。
- 每条文件有 `path`（包内相对路径）、`sha256`（64 位十六进制）。拒绝绝对/驱动器/UNC 路径、NUL、空路径、`.`/`..` 组件；Windows 路径分隔符等价处理，大小写不敏感检测重复路径。
- 禁止清单声明覆盖 game.exe、gamemd.exe、ra2.exe、ra2md.exe 和官方 BATTLEMD.INI（任意大小写）。战役追加的 BATTLEMD98.INI 等可以声明，后续安装仍须独立验证。
- 可选 `dependencies`、`conflicts` 为包 ID 数组；拒绝重复、自引用与同一 ID 同时依赖/冲突。本轮不解析外部依赖图，不声称多个 DLC 任意组合兼容。
- 有效输入退出 0，输出规范化清单；无效输入非 0，给出字段路径；不读取/安装目标资产、不写游戏目录、不下载内容、不执行清单里的命令。

并行包 C-FIX：独立模型负责 fixtures/ 的战役包示例与无效清单，直接依据本卡，覆盖路径穿越、Windows 驱动器/UNC、大小写碰撞、哈希错误、保留文件、自依赖及依赖/冲突重叠。

C-IMPL 与 C-FIX 可并行。二者交付后 C-AUD 独立模型运行并复核，只写 review/，提供负控和真实命令/退出码；调度者检查合规与拒绝路径。该原型不表示 DLC 框架已贯通，不做真机验收或资产分发。

## 4. 独立调度会话执行要求

先读本卡和 WORK_CHAIN。各调度会话分别探测可用的外部 harness，按实际能力、难度和额度选模型。Qoder/ZCode 仅在独立聊天身份明确时可同时操作，否则使用可并行的 Antigravity/CLI 后台任务；不得多个调度者争抢同一 GUI 输入框。外部任务需指定自己会话为回执接收方，不把结果都发给 EXP001 总协调者。

外部执行子代理仅使用 Antigravity、ZCode、Qoder CN；另可使用 DSH 内部 MiMo V2.6 Flash、Step 3.7 Flash、Step 5 Preview。按难度与实际能力选择；需要命令实跑而内部 shell 不可用时选择有有效 shell 的获准外部通道。所有通道都不可用则如实报告，不扩大模型/产品池。DSH 调度的两个官方 DeepSeek 供应商仍禁用；新调度者本身必须是独立普通会话，不把执行子代理当调度会话。

先启动 IMPL+FIX 两个互斥执行包，再进行 AUD。每个执行包建议预算 20～30 分钟，失败不自动重复同一投递；返工给具体问题，最多两轮后交 Codex。调度者 shell 已知可能有 0xC0000142，不反复重试/放宽审批，运行验证选择已有可用的外部通道。

在自己的 control/dispatch.json 记录身份、task_id、状态、写域与依赖，在 control/REPORT.md 汇报交付、真实命令、负控、独立复算与未闭合项。相关结论用项目回报规范；不用不相关的 323 条引擎锚点充当 JSON 工具行为验证。全局并行执行数争取 3～6，避免重复派发。
