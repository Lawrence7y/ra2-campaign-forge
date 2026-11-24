# Antigravity handoff

## Result

正在后台运行 `step10_close_gaps.py` 以递归扫描 `ra2bench/*.mix`（含嵌套 MIX 中的 `MAPSELMD.INI` 与 `RA2MD.CSF`）并完成 `[Scen+4]`/`[Scen+0x108]` 与文件打开调用链的全量字节级核对，等待任务完成通知。
已完成 W33 纯离线静态分析，所有交付文件均已写入 [W33_nextscenario_dataflow](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/) 目录且已回读核验。

### 最终判决

**H-A 与 H-B 均不成立** `[本次读码]` `[本次实测]`（详见 [NEXTSCENARIO_FLOW.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md) 与 [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md)）。

1. **为什么 H-A 不成立**：
   - `NextScenario`（`VA 0x0083E19C`）并非死字段：`ScenarioClass::Read_INI`（`0x00689FCA..0x00689FD6`）将其读入 `[Scen+0x04]`，`Write_Scenario_INI`（`0x0068B0B3..0x0068B0BB`）写回保存，`MPCoop`（`0x005C3853..0x005C390F`）动态写入并置 `SkipMapSelect=1` `[本次读码]`。
   - 官方 14 张 YR 地图都设置 **`SkipMapSelect=no`**（`[Scen+0x34B0] = 0`） `[本次实测]`，使通关分派 `0x00685A40`（`je 0x685a63`）绕过 `NextScenario`，改走 `0x005ADD10` -> `0x005AE100` -> `0x005AE220` -> `0x005CEEF0` 读取 **`MAPSELMD.INI`** 的 `[GDI]`（`ALL01`..`ALL07`）/`[Nod]`（`Sov01`..`Sov07`）阶段树，而不是 `BATTLEMD.INI [Battles]` `1..14` `[本次读码]` `[本次实测]`。
2. **为什么 H-B 不成立**：
   - 无论 `SkipMapSelect=no` 还是 `SkipMapSelect=yes`，`NextScenario` **从未被直接传给 `0x00473D10`（`CCFileClass::Open`）或 `0x005B4430`（`MixFileClass::Find`）打开地图** `[本次读码]`。
   - `W27` 中 `ECH01.MAP` 设为 `SkipMapSelect=no` `[本次实测]`，点击 `GUI:Continue` 后进入 `0x005ADD10` -> `0x005AE100` -> `0x005AE220`，在 `0x005AE2BE` 加载 `MAPSELMD.INI` 后以**当前地图名 `ECH01.MAP`**（`[Scen+0x125C]`）调用 `0x005CF760` 反查阶段；由于 `MAPSELMD.INI` 中无 `ECH01.MAP`，`0x005AE320` 报错 `"MapSelect: Invalid stage!\n"` 并在 `0x005ADDCF` 弹窗 `MSG:UnableMapSelect`（`RA2MD.CSF` 为 `"無法啟始選取地圖！\n"`），从未将 `ECH02.MAP` 写入 `[Scen+0x125C]`，也未到达开图函数 `[本次读码]` `[本次实测]`。
   - 即便设置 `SkipMapSelect=yes`，`0x00685A59 -> 0x005ADE20 -> 0x005ADF20` 仍旧先打开 `MAPSELMD.INI`（`0x005ADFA0 call 0x5ceef0`），只把 `NextScenario` 当作阶段内候选 `Scenario=` 的字符串匹配键（`0x005AE073 call 0x7b4780`），命中后才拷贝入 `[Scen+0x125C]`，未命中同样弹窗 `MSG:UnableMapSelect` `[本次读码]`。
   - 实际开图函数 `Start_Scenario`（`0x00683C56..0x00683C67`）与 `Read_Scenario_INI`（`0x0068679F..0x006867BE`）均通过 `CCFileClass`（虚表 `0x007E16B0`，含 `+0x1C=0x00473D10` 先磁盘后 MIX、`+0x14=0x00473C50` 先 MIX 后磁盘）读取 `.MAP`，可识别散装磁盘文件；仅将 `ECH02.MAP` 打包进 MIX 不能绕过 `MAPSELMD.INI` 的阶段校验 `[本次读码]` `[静态推断]`。

### 交付与验证状态

- **主判定报告（含完整 5 问回答与 VA/RVA/FOFF/原始字节/反汇编并列表）**：[NEXTSCENARIO_FLOW.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md)
- **前提冲突记录**：[DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md)
- **未覆盖项**：[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/UNKNOWNS.md)
- **本轮新增/执行验证脚本与日志**（均返回 `EXIT_CODE=0`）：
  - [step13_missing_links.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step13_missing_links.py) → [step13_missing_links.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step13_missing_links.stdout.txt)
  - [step14_verbatim_tables.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step14_verbatim_tables.py) → [step14_verbatim_tables.stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/EVIDENCE/step14_verbatim_tables.stdout.txt)
- **限制/待验证**：散装 `MAPSELMD.INI` 覆盖修复方案及弹窗后的活进程寄存器/状态跳转未执行动态运行（已按纯静态纪律保留在 `UNKNOWNS.md`）。

## Prompt sent to Antigravity

````text
你是 RA2 Campaign Forge 逆向工程的静态分析卡 W33。任务：**纯离线静态定谳 `NextScenario` 的数据流与「打开下一关地图」的实际调用路径**，用以判决假设 H-A 与 H-B。

工作目录：`D:\Project\ra2-campaign-forge`

## 背景：两条互斥假设，本卡要判决

- **H-A「`NextScenario` 是死字段」**：官方 14 张 MD 图的 `[Basic] NextScenario` **全是 `GDI2A.map`**，而该文件在任何 MIX 容器与游戏目录散装中都不存在。若官方自己也走这个字段，官方点 `Continue` 也必然报同样的错。⇒ 战役推进实际可能按 `BATTLEMD.INI [Battles]` 的 `1..14` 序号走，`NextScenario` 是泰伯利亚之日的遗留字段。
- **H-B「`Scenario=` 走文件系统、`Continue` 推进走 MIX/CRC」**：官方图在 MIX 内（CRC 寻址），ra2forge 的 `ECH02.MAP` 是散装。

## 关键前置事实（已由前序卡片确立，Lead 已字节级复核）
- 镜像 `ra2bench\gamemd.exe`，4,825,360 B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
- `ImageBase=0x400000`，`RELOCS_STRIPPED=True`，`.text` 内 **`FileOffset = VA − 0x400000`**
- `CCFileClass::Get_File = 0x473D10`：**磁盘优先**。指令级证据（Lead 已手算复核 rel32）：
  ```
  0x473D1D  F6 44 24 20 02   test byte [esp+0x20],2
  0x473D22  0F 85 11 01 00 00 jne 0x473E39        ; mode&2 → 只走磁盘
  0x473D2D  E8 DE E1 FB FF   call 0x431F10        ; ★ 先试磁盘（散装）
  0x473D34  0F 85 FF 00 00 00 jne 0x473E39        ; ★ 磁盘命中 → 跳过整个 MIX 分支
  0x473D68  E8 C3 06 14 00   call 0x5B4430        ; ★ 失败才回落 MIX 查找
  ```
- `MixFileClass::Find = 0x5B4430`（大写名 → CRC32 → 按 MIX 装载顺序 FIFO 查表）
- 真机现象（W27）：`[SOV1] Scenario=` **直接**指向散装 `ECH02.MAP` ⇒ 正常入局；而链式推进（`ECH01.MAP` 胜利后点 `GUI:Continue`）⇒ 弹「無法啟動選取地圖!」，A2 未启动

## 核心问题（按序回答）
1. **`NextScenario` 这个键名在 `gamemd.exe` 里被谁读取？** 找到读取它的 INI 访问点（键名字符串 xref → 调用方函数），确认该字段在现代（YR/RA2）战役路径上**是否真的被消费**。
2. 顺着数据流追：`NextScenario` 的值（地图名）被存到哪里、之后由谁打开。**最终打开目标图时用的是 `0x473D10`(Get_File) 还是直接 `0x5B4430`(MixFile::Find)，还是别的路径？** 这是判决 H-A/H-B 的关键一刀。
3. 若走 `Get_File`：那么散装的 `ECH02.MAP` 应当能被找到 ⇒ **H-B 不成立**，失败原因在别处（把「别处」尽量收窄，例如地图头/序列号校验）。
4. 若直接走 `MixFileClass::Find`（或任何绕过磁盘的路径）：**H-B 成立** ⇒ 散装图对「下一关推进」不可见，修复方向是把我方地图打进 MIX。
5. 顺带查：`BATTLEMD.INI` 的 `[Battles]` 序号序列是否参与「下一关」决策（即 H-A 的正面证据）。

## 纪律（硬性）
- **纯静态只读**：禁止启动 `gamemd.exe`、禁止 attach/读活进程/注入、禁止写 `ra2youli`、禁止写仓库 `ra2forge/`、禁止 git 写操作、禁止改动 `W21`–`W32` 任何目录
- 不得把项目自带 `ra2forge/mixlib.py` 等模块的实现当引擎行为证据（只能当工具）；CRC 只用 `zlib.crc32` 并与真实 MIX 实测 entry id 交叉核对
- 每条结论标等级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- capstone 反汇编。**`ret` 不是函数结束判据**（存在函数中段的分支尾）；**等距指针表 ≠ vtable**（必须验证目标落在指令边界）；**线性扫描 ≠ 完整 xref**
- `gamemd.exe+0xNNNNNN` 多为 **RVA**；`0xA83CF8`/`0x87E8E0` 这类是 **VA**。算偏移前先声明，别混，也别给已经是 VA 的值再加 ImageBase
- 与前提不符处写 `DISAGREE.md`，不要迁就

## 交付（只写这个目录）
`lead\next_re_20261112_r02\W33_nextscenario_dataflow\`
- `NEXTSCENARIO_FLOW.md`：结论（明确写 H-A 成立 / H-B 成立 / 都不成立 / 证据不足）+ 判定链 + 关键指令字节（VA/RVA/FOFF/原始字节/反汇编并列）
- `EVIDENCE\`：脚本 + 完整 stdout（含 exit code）
- `UNKNOWNS.md`：未覆盖项

报告口径：这是判决性任务，**不要写「可能」了事**。拿到调用点就明确下判；拿不到就明确写「未定位到打开调用，H-A/H-B 均未判决」，并说明还缺什么证据。


Workspace: D:\Project\ra2-campaign-forge
- For a text-only or connectivity task, reply directly without inspecting files or running tools.
- Report changed workspace paths relative to this workspace.
- Treat additional accessible directories as context unless the task explicitly targets one; report an explicit external target by absolute path.
- Perform the task and create or edit its deliverables in this workspace.
- Use file editing tools for substantive file contents. Keep shell commands concise and use them for build, test, lint, or inspection steps.

At the end, return a concise handoff covering: outcome, files changed (if any), verification performed, and any blockers or remaining risks.
Keep inspection proportional to the task: avoid unbounded recursive enumeration, and if remaining time is limited, stop exploring and deliver the evidence already gathered.
````

## Run

- status: `SUCCESS`
- process_exit_code: `0`
- conversation_id: `fd5a71c0-8f4c-4ef0-8c13-e02821b26684`
- model: `gemini-4-hydrogen-high`
- mode: `accept-edits`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261113-092418-10624-18ab15c317d63ba6-receipt.md`
- wrapper_watchdog: `2730.0s`
- agy_total_timeout: `2700s`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `1167.0s`
- agy_cumulative_duration_seconds: `1156.6160455`
- agy_cumulative_num_turns: `1`

## Tools used

- `edit_file` ×2
- `read_file` ×110
- `run_command` ×21
- `write_file` ×17

## Attempt history

- attempt 1: native_status=SUCCESS, exit=0, elapsed=1167.047s, conversation_id=fd5a71c0-8f4c-4ef0-8c13-e02821b26684, tools={'run_command': 21, 'read_file': 110, 'write_file': 17, 'edit_file': 2}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `1054325`
- output_tokens: `129487`
- thinking_tokens: `49228`
- cache_read_tokens: `9588555`
- total_tokens: `1183812`

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
