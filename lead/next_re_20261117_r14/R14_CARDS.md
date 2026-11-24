# R14 卡包（可直接派发｜v2：全面逆向）

> Lead 派卡时：把「通用前缀」（真机卡再加「L 卡前缀」）+「卡正文」+「通用尾部（纪律）」拼成一段提示词发给子代理。
> 模型：执行卡 → `work/cn:hy4flash-free`（失败 → `work/cn:hy4flash` → `work/cn:deepseek-v4.1-flash` high）；审计卡 → 与执行员异族；Hy4 只传 high 或不传。
> 卡类：W17x（原三线收尾）· C01–C10（P0 普查）· M（合并）· S{xx}-{K/N/F/Q/V/D}（子系统轨道）· A/S/H/P（审计/书记/卫生/规划）。

---

## 通用前缀（每张执行卡开头）

```
你是 RA2 逆向执行员，卡号 {卡号}。项目根 D:\Project\ra2-campaign-forge。
目标文件 ra2youli\gamemd.exe（SHA-256 73201CC0…F67476，ImageBase 0x400000），只读。
开工前必读：lead\next_re_20261116_r13\R13_COMMON.md（§1 作废索引、§6 纪律、§7 环境）；
若 lead\next_re_20261117_r14\R14_COMMON.md 已存在，以它为准。
写域：只允许写 lead\next_re_20261117_r14\{卡目录}\ 及 _ghidra\{卡号}\。其他位置一律只读。
工具：Python 3.12 + capstone 5.0.7（必须 skipdata=True）+ pefile；审计库 lead\next_re_20261116_r12\_lead_audit\audit_lib.py 可 import。
Ghidra 若需要：复制 lead\next_re_20261116_r11\_ghidra\W150 到 _ghidra\{卡号}，analyzeHeadless 必须 -noanalysis。
交付（全部放卡目录）：
  PROGRESS.md   ≤60 行：结论表（每条带 [已证]/[静态推断]/[未证] + 证据文件路径）+ 给审计员的 1–3 个「核心数字」及其复算方法
  UNKNOWNS.md   未解决项
  DISAGREE.md   与台账/R13_COMMON 冲突之处（引用节号）
  EVIDENCE\     原始输出（不截断；过长就分文件）
  work\         全部脚本（可复跑）
  coverage_delta.tsv  本卡涉及的每个函数一行：entry(hex8)\tsubsystem(Sxx)\tname\tone_line_semantics\tgrade([已证]/[静态推断]/[未证])\tevidence_path
                      （不得直接改 COVERAGE\coverage.tsv；由合并员统一合入）
旧文档 docs\re\*.md 只能作线索，结论必须本卡重新取证。
完成后只回复：卡号 + PROGRESS.md 路径 + 一句话结论。
```

## 通用尾部（每张执行卡结尾，纪律原文压缩）

```
纪律（每条都是翻车换来的，违反即审计 FAIL）：
1 寄存器语义判断必须回溯该寄存器全部写入点；thiscall 必须追 ecx 来源。
2 「某分支什么都不做」必须把入口到 ret 逐条打完；输出被截断≠代码不存在。
3 「某门控覆盖 X」必须给出跳转目标并证明 X 在其后/前。
4 穷举性结论双通道，至少一条不依赖 function_atlas.tsv 的 entry+size；字节命中先验指令边界。
5 站点归属用「函数区间包含」，不用 entry_at_or_before（0x482000..0x483400 是 atlas 空洞）。
6 「不存在 X」须查调用链上下各一层，并查 X 的等价形式。
7 写值逐字符核对；EIP 权重≠调用频率；「栈参数」判断须给 [esp+N] 取值集合。
8 不用「最近 E8/E9 目标」「最大函数=热点」「无调用者=死代码」等启发式。
9 写「新发现」前 grep lead\GOAL_THREE_TARGETS_20261018.md；不写台账；不改游戏文件；不 git commit。
```

---

## W173 · `LayerClass::Add` 调用点穷举 + `[obj+0x94]` 层号写点（① · 静态）

卡目录 `W173_layer_add`。背景：台账 §928-5 `[未证]`——`0x5519B0`（`VectorClass<T>::Add`，`LayerClass` vftable `0x7E6060` 槽 `+0x1C`）只有 2 个直接调用者（`0x4A9720`、`0x55BAA0`），经虚表派发的调用点未穷举。
任务：
1. 通道 A：全 `.text` 扫 `call [reg+0x1C]`，回溯 `reg` 的 vptr 来源，筛出 this ∈ `0x8A0360..0x8A03D8`（`[5]LayerClass`）的站点。
2. 通道 B（不依赖 atlas）：全 `.text` 扫对 `0x8A0360+k*0x18`（k=0..4）的立即数/位移引用，列出所在函数（区间包含判归属）。
3. 全镜像 `mov dword [reg+0x94], imm/reg` 写点：按写入值（-1/0..4/寄存器）分类，并对寄存器写入回溯来源。
4. 产出「层号 0..4 ↔ 对象类别/场景」对照表（能证多少写多少，余下标 `[未证]`）。
核心数字（给审计）：A/B 两通道站点数与交集数；`[+0x94]` 写点总数。

## W174 · `[+0x80]` 脏标记 179 写点全量分类（① · 静态）

卡目录 `W174_dirty80`。背景：§925-2 断言 `[+0x80]` 是脏标记（状态真变才置 1、绘制时消费清 0），只抽样了 6 个写点。
任务：全镜像 `mov byte [reg+0x80], *` 写点（预期 179 处 / 83 函数，先复核此数）逐个分类：写 0（消费）/ 写 1 且前有新旧比较（条件置位）/ 写 1 无比较（无条件置位）/ 写寄存器值；对每个写点确认 `reg` 指向 ObjectClass 族（追 this 来源），排除同偏移的其他类。
核心数字：写点总数、函数数、四类各自计数；「无条件置位」类全部列出地址。

## W175 · `[0x8871E0]` 类身份 + 阈值/开关来源（①②-a · 静态）

卡目录 `W175_global8871`。背景：`0x8871E0` 为运行时堆对象指针，3 个写入点 `0x52BAD8`/`0x52BAFA`/`0x6BEABD`；`+0x1808`=帧节流 N（=16）、`+0x172C`=距离阈值、`+0x250` 在 `0x6CD8CD` 无 NULL 判据；全局开关 `[0xA8ED6B]`、`[0xB73550]` 可整段绕过状态剔除（§924）。
任务：
1. 从 3 个写点回溯被写入的对象来自哪个构造器 → vftable → RTTI 类名。
2. 找 `+0x172C`、`+0x1808` 的写点，判断是否来自 INI 读取（追 INI 键字符串）。
3. `[0xA8ED6B]`、`[0xB73550]` 全部写点与写入值，给出语义候选（标明分级）。
核心数字：类名（RTTI 字符串地址）；两个字段各自写点数；两开关各自写点数。

## W176 · ②-b 放置失败分支与 `[+0x81]` 全读写（②-b · 静态，真机卡前置）

卡目录 `W176_place81`。背景：`0x43F180`（Building slot 73）mode 0=摘链、1/3=挂链、2=附属子对象刷新；挂链路径有 can-place `[+0x1AC]`（`0x43F218`/`0x43F678`）与逐格校验 `call 0x47C620`；`0x7014A0`=`TechnoClass::SetOwner`：`push 0;call[+0x124]` → `call 0x70D4A0` → `push 3;call[+0x124]`；`0x5F4D30` Limbo 写 `[+0x81]=1`。注意 §914：`0x43F658 cmp ebp,3` 不是 mode 门控。
任务：
1. 全镜像 `[reg+0x81]` 读/写点（区分 byte/dword），标出在 `0x43F180`、`0x7014A0`、`0x5F4D30`、Unlimbo 路径上的那些。
2. 把 `[+0x1AC]` 两处与 `0x47C620` 的**失败分支**从入口到 ret 逐条打完：失败后是返回失败、还是继续挂链？
3. 列出「10 格重叠」候选成因（每条给可被真机证伪的观测量）。
4. 产出真机探针表 `PROBE_TABLE.md`：地址、读宽度、触发时机、期望值（供 W177 只读轮询）。
核心数字：`[+0x81]` 读/写点数；失败分支的最终去向地址。

## W177 · 真机：NAPOWR 连续放置观测（②-b · **真机，进 LIVE_QUEUE 串行**）

卡目录 `W177_live_place`。前置：W176 入账（需要它的 `PROBE_TABLE.md`）。用 L 卡前缀派发（常设授权见 PLAN §6）。
任务：复用 `lead\next_re_20261116_r13\W172_live\` 与 `r12\W165_live\w165_probe2.py` 的探针框架；进局路径与像素定位见 R13_COMMON §5；连续放置 NAPOWR，每次放置前后只读快照 `[+0x81]`、格 `+0xE4/+0xE8` 链表与 W176 探针表所列地址。
核心数字：每次放置前后 `[+0x81]` 取值序列；重叠复现次数。

## W178 · ②-a 剩余缺口风险分级（②-a · 静态，只记录）

卡目录 `W178_guards`。对 `0x724730` 周边 30 个无守卫虚调用点与 `0x6CD8CD` 逐一判断：this 来源、可为 NULL 的路径是否可达、崩溃地址预测。D-13=C 允许写候选守卫件与离线单测（放卡目录，不落游戏目录、不注入）。
核心数字：30 个点中「存在可达 NULL 路径」的个数。

## W179 · `R14_COMMON.md` 事实底座（卫生 · 书记员）

卡目录直接写 `lead\next_re_20261117_r14\R14_COMMON.md`。输入：`R13_COMMON.md` + 台账 §923–§928 原文。
任务：沿用 R13_COMMON 结构；把 §923–§928 的已证事实并入；作废索引新增至少：§927-6（「多个不同布局容器」→ §928-2 同一 `[5]LayerClass` 数组）、§927-1「标准布局」措辞（→ §928-1）、§924-3（→ §925-2）、§918-6「可缓存优化」（→ §923）；纪律清单保持 18 条原文。不得新增台账外结论。

---

## A 卡 · 独立审计（模型：与执行员异族，默认 `work/cn:deepseek-v4.1-flash` high）

```
你是独立审计员，审计卡 {卡号}。只读执行员交付：lead\next_re_20261117_r14\{卡目录}\（PROGRESS.md、EVIDENCE\）。
写域：仅 {卡目录}\_audit\。
任务：对 PROGRESS.md 列出的 1–3 个核心数字，自己写脚本从 gamemd.exe 原始字节独立复算；
禁止 import 或复制 {卡目录}\work\ 下任何代码；至少一条通道不依赖 function_atlas.tsv 的 entry+size。
同时抽查 2 条结论是否违反纪律 1–8（附通用尾部全文）。
交付 _audit\VERDICT.md（≤40 行）：每个核心数字「执行员值 / 审计值 / 一致?」；裁决 PASS / PARTIAL（列出哪些结论降级）/ FAIL（列出理由）。
完成后只回复：卡号 + 裁决 + VERDICT.md 路径。
```

## S 卡 · 书记员起草台账节（模型：`work/cn:hy4flash-free`）

```
你是书记员。输入：{卡目录}\PROGRESS.md、UNKNOWNS.md、DISAGREE.md、_audit\VERDICT.md。
写域：仅 lead\next_re_20261117_r14\_drafts\。
先读 lead\GOAL_THREE_TARGETS_20261018.md 末尾确认当前最大节号 N，起草 _drafts\§{N+1}.md：
标题格式「## §{N+1} · {一句话结论}（2026-11-xx，R14 第 k 轮，执行 {模型} / 审计 {模型}）」；
正文只包含审计 PASS 的结论（PARTIAL 的按审计降级后的分级写）；每条带 [已证]/[静态推断]/[未证] 与证据路径；
若推翻旧节，标题加【更正 §xxx】并在文末列「作废索引增补」。不得加入任何输入以外的结论。
完成后只回复草稿路径与节号。
```

## H 卡 · 卫生门禁（模型：`work/cn:hy4flash-free`）

```
你是卫生检查员，只读。检查并输出 lead\next_re_20261117_r14\_hygiene\R{k}.md（≤20 行，每项 OK/FAIL）：
1 ra2youli\gamemd.exe SHA-256 前缀 73201CC0、后缀 F67476；ra2youli\ddraw.dll 前缀 85E0F7D5、后缀 3B03A9
2 ra2youli\except.txt 长度 26272 且 mtime 2026-11-13 06:29:17（真机卡后若变化，报告新增内容）
3 git log -1 --format=%h 等于 STATUS_BOARD 记录的 HEAD；git status 中 ra2youli\ 无变更
4 本轮新增/修改文件（按 mtime ≥ 本轮开始时间）全部位于 STATUS_BOARD 登记的写域内
5 lead\GOAL_THREE_TARGETS_20261018.md 行数只增不减，且旧内容哈希（前 L 行，L 取看板记录）未变
6 系统中是否有残留 gamemd.exe 进程；LIVE_LOCK 是否与看板记录一致
完成后只回复：全部 OK 或 FAIL 项列表。
```

## P 卡 · 规划员补卡（模型：`work/cn:deepseek-v4.1-flash` high）

```
你是规划员，只读（Lead 会指定你负责的子系统列表，如 S09,S13,S16）。
输入：STATUS_BOARD.md、PLAN_R14_SUSTAINED.md §1（DoD）、COVERAGE\PANEL.md 与 coverage.tsv（若已存在）、R14_COMMON.md（或 R13_COMMON.md）、
台账最近 20 节、相关 re_atlas\kb\* 与 docs\re\* 线索文档。
为每个负责的子系统挑出最能缩小 DoD 差距的 2–4 张卡，按本文件「T 卡模板」写（卡号顺延，K/N/F/Q/V/D 类型），
写入 lead\next_re_20261117_r14\_backlog\P-{你的子系统列表}-{日期时间}.md（写域仅此文件；多个规划员可并行，各写各的文件）。
每张卡必须给：背景（引用节号或文件）、任务、核心数字、是否真机（V 类）、预计涉及的函数地址范围（避免与在途卡重叠）。
不得写已在台账闭合的问题；猜测性假设必须标「猜测」。完成后只回复新卡号列表。
```

---

## L 卡前缀 · 真机卡（全局串行，一次只派一张）

```
你是 RA2 真机执行员，卡号 {卡号}。先用通用前缀的全部规则（写域、交付物、纪律同样适用）。
真机授权（用户 2026-11-17 常设授权，逐字）：可启动/关闭 ra2youli\gamemd.exe（只关闭你启动的进程）；
只读读取进程内存与线程上下文（ReadProcessMemory / Wow64GetThreadContext / GetProcessTimes / StackWalk / MiniDump）；
合成鼠标键盘输入；读游戏目录日志与 except.txt。
禁止：写进程内存、DLL 注入/Hook、修改 ra2youli\ 下任何文件、联网对战。遇到需要越界的步骤，停下并在 PROGRESS.md 写明需求。
开工前：确认 lead\next_re_20261117_r14\LIVE_LOCK 内容是你的卡号（Lead 已写入），并确认系统中没有残留 gamemd.exe。
开工前后各记录：ra2youli\except.txt 长度与 mtime、gamemd.exe 与 ddraw.dll 的 SHA-256。
可复用框架：lead\next_re_20261116_r13\W172_live\（EIP 分桶）、lead\next_re_20261116_r12\W165_live\w165_probe2.py（探针字段）、
R13_COMMON §5（探针字段表、进局路径、800×600 左上绘制区、按钮须像素分析定位）。
CPU 计时：GetProcessTimes 有 15.625 ms 量化，必须聚合到 ≥10 s 窗。
结束时：关闭你启动的游戏进程，确认无残留进程，在 PROGRESS.md 写「真机收尾：进程已关闭 / except.txt 未变（或变化内容）」。
```

---

## P0 普查卡 · C01–C10（并行 10 张，首轮立即派）

卡目录 `C{nn}_census`。把 `lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv`（12,916 行）按行号切 10 片：C01 = 第 1–1292 行，C02 = 1293–2584 …… C10 = 11629–12916（行号不含表头）。
任务（只处理本片函数）：
1. 为每个函数收集自动证据：所属虚表（若是某 vftable 的槽，给类 RTTI 名与槽号）；引用的字符串（含源文件名字串如 `*.CPP`）；导入 API；直接调用者/被调用者里已知名函数（参考 `re_atlas\kb\*`、`YRpp\` 头文件中的地址注释、台账已证名字）。
2. 按 PLAN §1 的 S01–S22 给出子系统候选与置信度（high/med/low），并给一行语义猜测（猜测标 `[未证]`）。
3. 交付 `coverage_delta.tsv`（本片全部函数，一行一个，grade 一律按证据给，不得把猜测写成 `[已证]`）+ `PROGRESS.md`（各子系统计数、high 置信占比、无法归类数）。
4. 另交 `atlas_gaps.tsv`：本片地址范围内通过「全 .text 扫 call/jmp rel32 目标」发现但 atlas 没有的函数入口（已知例：`0x4824D4`）。
核心数字：本片函数数（应与切片行数一致）；high 置信计数；atlas 空洞入口数。

## M 卡 · 合并员（串行；P0 十片全部 PASS 后派，之后每当有 ≥5 份新 delta 时派）

```
你是合并员，写域仅 lead\next_re_20261117_r14\COVERAGE\。
输入：所有状态为 PASS/PARTIAL 的卡目录下 coverage_delta.tsv 与 atlas_gaps.tsv（列表由 Lead 给出）。
规则：同一 entry 多来源时，grade 高者优先（[已证] > [静态推断] > [未证]）；同 grade 子系统/名字不一致 → 写入 CONFLICTS.tsv，coverage.tsv 保留旧值并标 conflict=1；不得自行裁决。
产出：coverage.tsv（全量，含 atlas 空洞新增入口）、CONFLICTS.tsv、PANEL.md（每子系统：函数数 / 有名字 % / [已证] % / DoD 差距）。
完成后只回复：合入 delta 数、冲突数、PANEL.md 路径。
```

---

## T 卡模板 · 子系统轨道卡（P1，规划员按此模板为各子系统量产）

每个子系统 Sxx 按以下四类切卡，卡号 `S{xx}-{类型}{序号}`，卡目录同名：

| 类型 | 目标 | 交付重点 | 核心数字示例 |
|---|---|---|---|
| **K 类布局** | 子系统核心类的完整字段表（偏移/宽度/类型/读者/写者）、虚表槽语义、构造/析构/`GetSize` | `LAYOUT.md` | 字段数；与 `GetSize` 是否吻合；写者站点数 |
| **N 函数命名** | 对 coverage.tsv 中本子系统 `[未证]`/无名函数批量命名（每卡 ≤150 个） | `coverage_delta.tsv` | 本卡升到 `[已证]` 的函数数 |
| **F 数据流** | 入口 → 每帧更新 → 销毁/存档 的调用链；与其他子系统接口 | `FLOW.md`（mermaid 调用图） | 链上每一跳的调用点地址 |
| **Q 专题** | 具体机制/疑点（如 ②-b、Verses 表、校验和算法） | 按题 | 按题 |
| **V 真机验证**（L 卡前缀） | 用运行时数据验证本子系统 2+ 条关键事实 | `LIVE.md` | 实测值 vs 静态预测 |
| **D 结题文档** | 汇总已入账结论写 `KB\Sxx_<名称>.md`（本子系统 KB 的唯一写者） | KB 文档 | DoD 六项逐项勾选 |

---

## 首批子系统卡（P1 起步，P0 进行中即可并行派发——它们不依赖普查）

| 卡号 | 子系统 | 类型 | 任务一句话 |
|---|---|---|---|
| S13-K1 | 战斗 | K | `WeaponTypeClass`/`WarheadTypeClass`/`BulletClass`/`BulletTypeClass` 字段布局（从 INI loader 写点反推，参考 `re_atlas\kb\30` 键表） |
| S13-F1 | 战斗 | F | 开火 → 子弹生成 → 飞行 → 命中 → 伤害结算（Verses）→ 死亡 的调用链 |
| S16-K1 | 超级武器 | K | `SuperClass`/`SuperWeaponTypeClass` 布局、充能状态机字段 |
| S17-F1 | 存档 | F | 存档/读档总入口、各类 `Save`/`Load` 顺序清单与 Swizzle 流程 |
| S18-F1 | 网络 | F | 事件队列（`EventClass`）入队/执行/校验和计算链（只读分析） |
| S09-F1 | UI | F | 输入消息 → 命令派发 → 侧栏点击 → 生产请求 链 |
| S14-F1 | House/AI | F | `HouseClass::AI` 每帧更新结构、AITrigger 评估、Team 创建 |
| S21-F1 | 战役 | F | 战役选择 → 关卡载入 → 胜负判定 → 得分界面 链 |
| S10-K1 | Mission | K | Mission 枚举、`MissionClass` 字段、各类 `Mission_*` 虚槽表 |
| S11-K1 | Locomotor | K | 各 Locomotor 类（COM 接口）vtable 与 CLSID 表 |
| S01-F1 | 主循环 | F | WinMain → 主循环 → 每帧调用顺序（Logic/Map/UI/渲染/音频）总图 |
| S03-K1 | 文件系统 | K | `CCFileClass`/`MixFileClass` 布局与 MIX 查找链 |
| S19-F1 | 音频 | F | 音效/EVA/音乐/VQA 的调度链 |
| S20-K1 | 粒子/Anim | K | `AnimClass`/`ParticleSystemClass` 布局与更新入口 |

真机卡首批（进 LIVE_QUEUE，按序）：**W177**（②-b）→ **S01-V1**（主循环每帧调用顺序的 EIP/栈采样验证）→ **S13-V1**（一场交战中 Bullet/Anim 数与命中链的运行时读数）→ **S17-V1**（存档文件块结构与静态清单对照：游戏内存档后读取存档文件，只读）。

---

## Backlog

规划员产出放在 `_backlog\*.md`（每个规划员一个文件）。Lead 只把卡号、子系统、类型、文件路径登记进 STATUS_BOARD 队列；派发时把对应卡正文从 `_backlog\` 文件中原样取出拼进提示词。
