# Antigravity handoff

## Result

已完成离线对抗性复核卡 **W89_adversarial**（唯一写域 `lead/next_re_20261112_r04/W89_adversarial/`，其余路径未作修改、未启动或修改游戏/注入调试器）。

### 核心裁决（见 [ADVERSARIAL.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/ADVERSARIAL.md) §1）
- **对 R03 原结论打分**：**部分支持**（8 组配置实测停机与 300 s 对照差异事实存在，但「"重战斗/交战"引发崩溃」与「静态对照已排除非交战因子」的因果结论**不成立**）。
- **逐项核查结果（§2.1–§2.7）**：
  1. **坐标越界 / 单位堆叠（否决疑点）**：`[本次实测]` 全量解析 JSON 与各 trip `.MAP`，无论 `(row, col)` 还是等距投影 `iso` 菱形边界，越界数均为 `0`（`Arabs col=82..97` 最大 `x+y=198 <= 201`）；`Unit-Unit` 同格重复格均为 `0`（最大单格堆叠 `1`，最高密度 `0.938`）。同时查明 `W85_pressure/work/w85_design_*.json` 在磁盘上实为**终版 P4**（19 建筑、90 单位），并非正文主表 `dose1500`（[check_1_2_3_4_geom.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_1_2_3_4_geom.stdout.txt)）。
  2. **建筑底座物理重叠（新发现混杂因子 #2）**：`[本次实测]` `Struct-Unit Overlap = 0`，但 6 座 `NAPOWR`（`Foundation=3x2`）以步长 `2` 摆放于 `iso=(90..100, 57)`，造成 **10 格（无 `NACNST` 的 P4）至 14 格（含 `NACNST` `4x4` 的其余 9 组）底座相互重叠**。`CellClass::AddObject`（`0x0047E8A0`）将 `BuildingClass` 串入单一共享链表指针 `[ebp+0x30]`（`NextObject`），拆链 `RemoveObject`（`0x0047EA90`）按足迹逐格摘除并清零 `[esi+0x30]` 时存在多格断链/悬空风险（[check_6_part4_cell_unlink_and_270.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part4_cell_unlink_and_270.stdout.txt)）。
  3. **崩溃点与 `Crewed` 步兵生成（新发现混杂因子 #1）**：`[本次实测]` `0x0051C2D3`（`call [eax+0x1D4]`）所属函数 `0x0051BF90` 在 `.rdata/.text` 中**唯一**挂在 `.?AVInfantryClass@@` 主虚表 `0x007EB058[+0x1AC]`（即 **`InfantryClass::IsCellOccupied`**；坦克 `UnitClass` 走 `0x0073F0A0`）。W85 全图声明 `infantry=0`，却在所有崩溃组均配置至少 6 座 `Crewed=yes` 的 `NAPOWR`（以及部分含 `NACNST`/`GAPOWR`，`Crewed=yes`），而稳定先例 `W84 df` 实为 `1 × TESLA`（`w84_design_df.json` 写作 `TESLA` 非 `ATESLA`，两者均 `1x1, Crewed=no`）且无电厂/无重叠。`0x0051C2CF` 遍历 `[pCell+0xE4]` / `[pCell+0xE8]`，全合法衍生类的 `+0x1D4` 槽均非空（`0x0070C5B0` 或 `0x004264E0`），若转述 `eax=0` 为真（**原件已丢失**），指向节点 `esi` 首 dword vptr 为 `0` 的悬空/已清零指针（[check_6_deep_disasm.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_deep_disasm.stdout.txt)）。
  4. **`0xA8ED50` 与 Guard 静态对照批判**：`[本次实测]` 遍历 `run.ndjson` 见：静态 Guard 对照的 `0x0087E8E0`（`PathFinder::GenerationStamp`）在 300 s 内恒为 `4294967295`（`dx=0`），完全未触及寻路、摧毁拆链与乘员产生；而全部 Hunt 压测在 `A8ED50` 首非零**之前** `0x0087E8E0` 已先飙升 `+226..+9357`（如 `notesla400` 达 `+9357`），且 `A8ED50` 多次跌回 0、停帧实际窗口跨度为 `3.37–12.32 s`（如 `P3`/`P4`/`P4rerun` 精准在首弹后 `105–111` 帧即首波建筑/单位被毁窗口停帧）（[check_5_7_ndjson_and_crewed.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt)）。
  5. **原件丢失与栈帧疑点**：W85 当次 `except.txt` 未随沙箱归档保留；此外转述调用栈中的 `0x42A595` 在镜像中对应 `0x0042A590 call 0x4cac40`（`fadd dword ptr [esi+4]`）而非 `IsCellOccupied` 直接调点。报告 §4.2 已给出最小崩溃取证整改规范（[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/UNKNOWNS.md)）。

### 交付文件清单
- 主报告：[ADVERSARIAL.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/ADVERSARIAL.md)（§1–§5 完整结构，含混杂因素排序、最小三臂消融、最小取证整改规范与 `PRESSURE.md` 逐句改写表）
- 分歧与未知项：[DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/DISAGREE.md)、[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/UNKNOWNS.md)、[PROGRESS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/PROGRESS.md)
- 复现脚本与 stdout 证据（全部 exit code `0`）：
  - [check_1_2_3_4_geom.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_1_2_3_4_geom.py) / [check_1_2_3_4_geom.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_1_2_3_4_geom.stdout.txt)
  - [check_5_7_ndjson_and_crewed.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_5_7_ndjson_and_crewed.py) / [check_5_7_ndjson_and_crewed.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt)
  - [disasm_51C2D3.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/disasm_51C2D3.py) / [disasm_51C2D3.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/disasm_51C2D3.stdout.txt)
  - [check_vtables_and_slot1D4.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_vtables_and_slot1D4.py) / [check_vtables_and_slot1D4.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_vtables_and_slot1D4.stdout.txt)
  - [check_6_deep_disasm.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_deep_disasm.py) / [check_6_deep_disasm.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_deep_disasm.stdout.txt)
  - [check_6_part2_ctors_and_celllist.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part2_ctors_and_celllist.py) / [check_6_part2_ctors_and_celllist.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part2_ctors_and_celllist.stdout.txt)
  - [check_6_part3_unittype_crewed_and_270.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part3_unittype_crewed_and_270.py) / [check_6_part3_unittype_crewed_and_270.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part3_unittype_crewed_and_270.stdout.txt)
  - [check_6_part4_cell_unlink_and_270.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part4_cell_unlink_and_270.py) / [check_6_part4_cell_unlink_and_270.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/EVIDENCE/check_6_part4_cell_unlink_and_270.stdout.txt)

### 已知局限与阻塞项
- 受本卡离线只读约束且 W85 原始 `except.txt` 已在收尾还原中丢失：无法实机验证「去 `NAPOWR` 重叠」与「去 `Crewed=yes` 乘员生成」二者何为充分/必要条件，亦无法核实 8 次停止中除转述外其余各趟的实时 EIP（参见 [UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r04/W89_adversarial/UNKNOWNS.md) `U-W89-1`~`U-W89-4`）。
- 末次枚举 `git status --short` 因环境读取 `C:/Users/Administrator/.gitconfig` 权限被拒退出码 `1`，已由目录全量列举确认所有新建/修改文件均位于 `lead/next_re_20261112_r04/W89_adversarial/` 内。

## Prompt sent to Antigravity

```text
# W89 · 提示词（交给 agy / Gemini-4-hydrogen-high）· 对抗性复核

你要执行 RA2 Campaign Forge 项目的**离线对抗性复核卡 W89**。工作目录 `D:\Project\ra2-campaign-forge`。
**只允许写 `lead\next_re_20261112_r04\W89_adversarial\` 目录下的文件**；其余路径只读。

## 你的角色
上一轮（R03）得出一个**很强的负结论**，你的任务是**攻击它**。不要客气，但每一条反对意见都必须有**字节/结构级的证据**，不能只是"我觉得可能有别的解释"。

## 被攻击的结论（原文摘录，来自 `lead\next_re_20261112_r03\W85_pressure\PRESSURE.md`）
> 「在 vanilla YR 1.001 上，"更重战斗"（Hunt 大兵团强制交战）在 8 个配置（400–1500 units、1–3 敌 house、TESLA 12/0、玩家坦克 300/100/0、NACNST 有/无）下**全部在 `0xA8ED50` 首非零后 2.5–9 s 触发引擎崩溃/内部错误**（AV @ `0x51C2D3`：`call [eax+0x1D4]` 且 `eax=0`，空 this 虚调用）；而**同图同布局同对象数的静态对照（1522 对象全 Guard）300 s 全绿**。⇒ 本卡未造出可持续观测的加压臂」
>
> 报告把"驱动因素"归为**未证**，并列剩余候选 = {敌方 `GAPOWR`、玩家 `NAPOWR`、100×100 图、Hunt 规模}。

## 你要回答的唯一问题
**这个崩溃，真的是"交战"引起的吗？还是存在一个与交战共变的非交战混杂因素（设计/地图/坐标/对象堆叠），它才是真因？**

## 必须逐项检查的技术角度（每条都要给证据，不能只看散文报告）
1. **坐标越界**：`work\w85_design_pressure.json`（17 KB）与 `work\w85_design_control.json` 里的单位/建筑坐标，是否**全部落在**地图声明的尺寸内。报告称 `Map Size=0,0,100,100`、玩家建筑 rows 54–63、玩家 MTNK 网格 rows 66–95、敌 3 house 网格 rows 12–41 / cols 2–17 / 42–57 / **82–97**。请把**实际 JSON 里的坐标**全部解析出来，统计 min/max、**是否存在超出地图边界的坐标**、每个 house 的实际格子占用。**若敌 3 号 house 的 col 上界 97 与每格多单位叠加导致越界或堆叠，这可能是真因。**
2. **同格堆叠**：同一个 cell 上是否被放了多个对象（尤其 300–400 个 MTNK 放在 16 列 × 30 行的网格里）。计算每个 house 的"对象数 / 可用格数"密度。若密度 >1，说明有堆叠——堆叠在引擎里是否合法、会不会在首次寻路/移动时炸。
3. **建筑与单位重叠**：玩家建筑（NACNST/NAPOWR/TESLA）占的格子是否与玩家 MTNK 网格重叠；敌方 `GAPOWR` 是否压在敌方 MTNK 网格上。
4. **与稳定先例的结构对照**（关键）：r02 的 **W84 df** 配置是"30 Hunt vs 1 `ATESLA`，60×60 图，32 对象，无基建"，**分钟级稳定**。请把 W84 df 的 design json（在 `lead\next_re_20261112_r02\W84_defeat_dialog\work\w84_design_df.json`）与 W85 的 design json **逐字段结构对照**：地图尺寸、坐标分布、密度、对象总数、有无基建、`SkipMapSelect`/`EndOfGame`/胜利条件等。**找出两者最小差集**。
5. **`0xA8ED50` 的语义是否被误用**：报告用"`0xA8ED50` 首次非零"作为"开火"的时刻锚。请核这个推断：项目既有登记说它是"注册 Bullet 对象 Count"的**候选**（`[本次实测-行为相容]`，非符号级证明）。如果它其实不是弹数，那么"开火后 2.5–9 s 崩"这个时序锚就站不住。给出你认为更强的替代时序锚（例如某单位的 target 指针、或爆炸特效计数），并说明怎么取。
6. **崩溃点语义**：`gamemd.exe 0x0051C2D3 = FF 90 D4 01 00 00`（`call dword ptr [eax+0x1D4]`）。请**反汇编它所属的完整函数**，判断这个虚调用属于哪个类（找函数入口、看它引用的全局/字符串/RTTI），以及 `+0x1D4` 这个虚表槽在什么类型的对象上才有效。**这能直接告诉你"哪个对象为空"**——比如是不是某种"目标/攻击者/弹道"对象。
   - 提示：栈返回地址（报告转述）含 `0x42A595 / 0x429F5A / 0x4DBE6B / 0x42CC07` 与全局 `0x0087E8B8`。**注意这些是报告的转述，原始 `except.txt` 已丢失**（见下），所以请以**静态反汇编**为准，不要把它们当既有事实。
7. **静态对照是否真的等价**：报告的"对照臂"是同图同布局全 Guard、1522 对象、300 s 全绿。但 **Guard 单位不会移动**，因此它**没有走到**"单位移动 + 寻路 + 目标获取"这些代码路径。请指出：**"静态稳定"不能排除"移动/寻路路径上的缺陷"**，也就是说崩溃可能是"移动"而不是"开火"引起的——报告把 `0xA8ED50`（弹）当锚，可能**误把"移动开始"当成"开火"**。给出能区分"移动 vs 开火"的判据与最小实验。

## 重要：原始崩溃证据已丢失（不要假装能核它）
W85 崩溃时引擎重写的 `except.txt`（26,236 B @12:31:32）**没有被归档**，沙箱收尾时被清理（`W85_pressure\out\sandbox_game` 已不存在）。所以：
- **任何关于 EAX=0 / 访问地址 0x1D4 / 调用栈的说法，都只能算"转述"，不是可复核证据**；
- 你的批判里若用到它们，必须标注"（转述，原件已丢失）"；
- 同时请**建议**一张最小取证卡需要保存什么（这条会进整改单）。

## 交付（写入 `lead\next_re_20261112_r04\W89_adversarial\`）
1. `ADVERSARIAL.md` 主报告，结构：
   - §1 结论摘要（**对原结论的支持度打分**：支持 / 部分支持 / 不成立，并给一句话）；
   - §2 逐条技术检查（上面 1–7 每项一节，每节给"我查了什么 / 证据 / 判决"）；
   - §3 **混杂因素排序表**（按"能同时解释 8 个崩溃与静态稳定"的能力排序，每条给最小否证实验）；
   - §4 对 `0x0051C2D3` 所属函数的反汇编解读（哪个类、哪个虚槽、什么对象可能为空）；
   - §5 若你是对的，原报告哪几句必须改写（逐句给"改前/改后"）。
2. `EVIDENCE\`：你写的全部脚本 + stdout（坐标统计、密度统计、W84 vs W85 结构对照、反汇编清单）。
3. `UNKNOWNS.md`、`DISAGREE.md`、`PROGRESS.md`。

## 硬纪律
- **只读**：不改 `gamemd.exe` / `ddraw.dll` / `ra2youli`；不启动游戏、不注入、不附加调试器。
- 需要分析的文件先**复制**到本卡再处理。
- 结论分级：`[本次实测]`（你自己跑出的解析/反汇编）/ `[静态读码]` / `[静态推断]` / `[未证]`。
- 搜索"没找到"要写清范围（扫了哪些文件/多少字节/哪些编码）。
- **小步落盘**：先写 `PROGRESS.md` 骨架，每完成一条就写一次盘（本机 agy 长任务曾多次 `print timeout` 且无最终答复）。
- 时间预算 60–90 分钟；证据不足就标 `[未证]` 并写下一步最小证据，**不要编**。



Workspace: D:\Project\ra2-campaign-forge
- For a text-only or connectivity task, reply directly without inspecting files or running tools.
- Report changed workspace paths relative to this workspace.
- Treat additional accessible directories as context unless the task explicitly targets one; report an explicit external target by absolute path.
- Perform the task and create or edit its deliverables in this workspace.
- Use file editing tools for substantive file contents. Keep shell commands concise and use them for build, test, lint, or inspection steps.

At the end, return a concise handoff covering: outcome, files changed (if any), verification performed, and any blockers or remaining risks.
Keep inspection proportional to the task: avoid unbounded recursive enumeration, and if remaining time is limited, stop exploring and deliver the evidence already gathered.
```

## Run

- status: `SUCCESS`
- wrapper_status: `SUCCESS_WITH_POST_RESULT_CLEANUP`
- process_exit_code: `0`
- conversation_id: `c794ba40-5b96-41b9-ab3c-e327d6389e4f`
- model: `gemini-4-hydrogen-high`
- effort: `high`
- mode: `accept-edits`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261114-052909-3700-86bbc908a12e449a-receipt.md`
- wrapper_watchdog: `5430.0s`
- agy_total_timeout: `90m`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `1152.6s`
- agy_cumulative_duration_seconds: `1137.9132671`
- agy_cumulative_num_turns: `1`

## Tools used

- `edit_file` ×9
- `manage_task` ×1
- `read_file` ×83
- `run_command` ×35
- `write_file` ×12

## Attempt history

- attempt 1: native_status=SUCCESS, exit=0, elapsed=1152.64s, conversation_id=c794ba40-5b96-41b9-ab3c-e327d6389e4f, final_wrapper_status=SUCCESS_WITH_POST_RESULT_CLEANUP, tools={'run_command': 35, 'read_file': 83, 'write_file': 12, 'manage_task': 1, 'edit_file': 9}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `532019`
- output_tokens: `118994`
- thinking_tokens: `48998`
- cache_read_tokens: `9913912`
- total_tokens: `651013`

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
