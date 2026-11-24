# Antigravity handoff

## Result

已完成静态逆向卡 **W87**（仅写入 `lead\next_re_20261112_r03\W87_third_badge_noexe\`，未修改或启动任何原始二进制）。

### 核心结论
**在严格保持 `gamemd.exe` SHA-256（`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）不变的前提下，四条候选路线中仅 R1 可行：**

1. **R1（运行时改对话框模板，经 `ddraw.dll` 进程内拦截）→ A · 保持 exe 哈希可行**（附前提与风险） `[本次实测]` + `[静态读码]`
   - **创建链与 IAT 槽**：`0x0052DF48..0x0052DF65`（`dlgId=0x94`, `lpDialogFunc=0x0052EC00`）→ `0x00622650` → `0x004A3B40`（`FindResourceA`/`LoadResource`/`LockResource`）→ `0x006226CB call dword ptr [0x7e1450]`（`USER32.dll!CreateDialogIndirectParamA`）。
   - **进程内拦截方案**：`gamemd.exe` 仅在 `0x007E1048` 导入 `DDRAW.dll!DirectDrawCreate`（跳板 `0x007C89D4`），且不自检 `ddraw.dll`（`VERSION.dll` 唯一调用链 `0x0074FDE8..0x0074FE99` 查询的是 `[0xb732f0]` 即 exe 自身 `ProductVersion`）。首选 **R1-a（自写代理 `ddraw.dll` 转发到 `cnc_orig.dll`）**：改写 `0x007E1450`，当 `lpDialogFunc == 0x0052EC00` 时分配 **696 B** 可写缓冲区，复制 `664 B` `RT_DIALOG 148`，将 `cDlgItems` 从 `13` 改为 `14` 并在末尾追加 32 B `id=1771` (`STATIC`, `style=0x50000007`, `exStyle=0x00000020`)。
   - **版本守卫与工程代价**：`version_guard.py` (`L1_FIELDS`) 不包含 `ddraw.dll`（可通过 L1 exe 守卫）；但 `ddraw.dll` SHA-256 (`85e0f7d5...`) 登记于 L2 `C07`、`BASELINE.json` 与 `TRACK_B_gates.json` G5，且 `ra2opt\cddraw.py` 运行时会覆盖 `ddraw.dll`。
   - **「可见」前提**：由于内置 `CAMPAIGN.PCX` 与 MIX/`.rsrc` 没有第 3 枚徽章图像 `[静态读码]`，R1 仅提供可点热区，需配套外部/Mod `CAMPAIGN.PCX` 或在热区自绘文字/边框方能真正"可见"。
2. **R2（改用 `BUTTON` 等非 STATIC 类第三控件）→ C · 不可行** `[本次实测]`
   - 虽然 `0x52EC00`（`0x52ED60`/`0x52EEFA`/`0x52F1CF`）及 `0x622CCB` 的 `ChildWindowFromPointEx` 仅传 `uFlags=1`（`CWP_SKIPINVISIBLE`）且无类过滤，但：(a) `RT_DIALOG 148` 中本就无 `1771`，仍需 R1 或改 exe；(b) 标准 `BUTTON` 对 `WM_NCHITTEST` 返回 `HTCLIENT` 并吞掉鼠标点击转而向父窗发送 `WM_COMMAND (0x111)`（如 `0x61678B`）；(c) `0x52EC00` 的 `WM_COMMAND` 分支（`0x52ECB1`）只处理 `0x40E` 与 `0x686`，直接丢弃 `0x6EB`；(d) `0x497` 初始化发给 `0x6EB` 的 `0x4D5`/`0x4D4` 仅在 `Static` 处理器 `0x6153E0` 实现。
3. **R3（复用 `1820` / `1959` / `1960` 或配置重映射）→ C · 不可行** `[本次实测]`
   - `1820 (0x71C)` 在 `0x0046DF98`、`0x00602F4F`、`0x0060356F` 有独立用途且与 `(dlg=0x94, id=0x6EB)` 明确并列；`1959`/`1960` 分别是 `all1`/`sov1` 字幕槽并在 `0x0060866C`/`0x0060869E` 硬编码坐标布局。56 处 `SetWindowLongA` 中 `0` 处传 `GWL_ID (-12)`；`.rdata`+`.data`+`.detour`（`655,360 B`）扫描 `ControlID`/`DialogID`/`BadgeID` 均为 `0` 命中。
4. **R4（对话框模板外部化机制）→ C · 不可行** `[本次实测]`
   - 全部 `FindResourceA`/`LoadResource`/`LockResource` 收敛于唯一函数 `0x004A3B40`（3 个调用点），全部 4 个 dialog 创建 API 共 8 个调用点（`.detour` 0 引用）；上述 `655,360 B` ASCII/UTF-16LE 扫描 `DLGTEMPLATE`/`.DLG`/`DIALOG.INI`/`UI.INI`/`MENU.INI`/`DialogTemplate` 全为 `0` 命中（正例 `DIALOG.PAL`=1、`BATTLEMD`=2、`BootCamp`=1）。

### 交付文件
- 主报告：[THIRD_BADGE_NOEXE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/THIRD_BADGE_NOEXE.md)
- 既有事实交叉核对（无实质冲突，附 2 项精化补充）：[DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/DISAGREE.md)
- 未证项（`0x52F191` 跳过 `0x4D7` 运行时效果、美术与坐标布局、Wine/Detours 动态加载兼容性等）：[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/UNKNOWNS.md)
- 进度日志与证据文件：[PROGRESS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/PROGRESS.md)、[file_hashes.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/file_hashes.txt)、[r2_r3_final_check_stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_r3_final_check_stdout.txt)、[r2_r3_final_disasm.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_r3_final_disasm.txt)、[tiny_strings_check.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/tiny_strings_check.txt) 等（及 `work\` 下全部副本与脚本）。

### 校验与未尽风险
- **只读二进制复核**：完成写入后再次校验 `ra2youli\gamemd.exe`（`4,825,360` B, SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）与 `ra2youli\ddraw.dll`（`411,648` B, SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`），均与基线完全一致。
- **沙盒说明**：`git status` 因沙盒内无权访问用户全局 `.gitconfig` 退出码为 1，已通过枚举 `lead\next_re_20261112_r03\W87_third_badge_noexe` 全目录文件确认写域合规；动态行为相关项均已按规范在 [UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/UNKNOWNS.md) 标为 `[未证]`。

## Prompt sent to Antigravity

```text
# W87 · 提示词（交给 agy / Gemini-4-hydrogen-high 的原文，留档）

你要执行 RA2 Campaign Forge 项目的静态逆向卡 **W87**。工作目录 `D:\Project\ra2-campaign-forge`。
**只允许写 `lead\next_re_20261112_r03\W87_third_badge_noexe\` 目录下的文件**；其余路径只读。

## 唯一问题
**能否在不修改 `gamemd.exe`（必须保持 SHA-256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）的前提下，让"第三个战役徽章"在战役菜单里真正可见、可点、可进（进而让追加式 DLC 战役在产品层面可见）？**

## 已签发的既有事实（直接采用，不必重验；若你反汇编发现与此矛盾，**停下来写 DISAGREE**）
目标镜像 `ra2youli\gamemd.exe`（4,825,360 B，ImageBase `0x400000`）。

1. 战役菜单窗口过程在 **`0x52EC00–0x52F3E8`**，逐条反汇编 658 条指令后确认它**认得三个徽章控件 id**：
   - `0x6EA`(1770) 出现 7 次、**`0x6EB`(1771) 出现 8 次**、`0x6EC`(1772) 出现 7 次。
   - 比较三元组：`0x52EE04/0x52EE3F/0x52EE78`、`0x52EF39/40/47`、`0x52F232/242/252`、`0x52F307/30F/317`。
   - `0x52EE78 cmp ebx,0x6eb` 之后 `0x52EE9D push 0x6eb`、`0x52EEA8 mov dword ptr [0xa8f7a8],0x6eb`（把 1771 记为"当前选择"）。
   - `SendDlgItemMessageA` 的 id 推送 6 处：`0x52F134/145`(0x6ea)、`0x52F156/167`(0x6ec)、`0x52F178/189`(**0x6eb**)。
2. 三个槽→三个 battle 名：`0x52F23A/24A/25A` 分别从 `[0x825C68]/[0x825C6C]/[0x825C70]` 取指针送入 `0x46CC90`（battle 表按名查表）：
   - `[0x825C68]=0x00825CA0` → `all1`（对应 1770）
   - `[0x825C6C]=0x00825C98` → `sov1`（对应 1772）
   - `[0x825C70]=0x00825C90` → **`tut1`**（对应 **1771**）
   - `0x825C74/78/7C` 三个指针初值均 `0xFFFFFFFF`；`0x825C20`（当前选择）初值 `0xFFFFFFFF`。
3. `RT_DIALOG 148` 模板（664 B）解开：`dlgVer=0x0001`、`signature=0xFFFF`、`style=0x40000040`、**`cDlgItems=13`**、`533×369`、字体 `MS Sans Serif 8pt`，解析到末尾 `trailing=0`。
   - 徽章 Static（class `#130`=STATIC，style `0x50000007`）：`id=1770` @ `(125,34)` `174×87`；`id=1772` @ `(125,216)` `173×86`。
   - **`id=1771` 不存在**（`has1770=True has1771=False has1772=True`）。
   - 同屏另有 `id=1820`(61×33 @449,29)、`1959`、`1960` 等 Static。
4. 命中检测走 **`ChildWindowFromPointEx` + `GetDlgCtrlID`**，**不靠坐标常量**；两个已存在的徽章 STATIC 是**透明、无文字、`WS_EX_TRANSPARENT`** 的点击热区（真正看到的徽章美术画在背景 `CAMPAIGN.PCX` 640×480 上）。
5. **第三徽章的像素资源不存在**：全 MIX 递归 5,630 个容器 / 1,168,759 个 CRC id 里，唯一带 campaign 名的美术是 `CAMPAIGN.PCX`，没有任何 `TUT*`/`BOOT*`/`BADGE*`/`EMBLEM*`；`.rsrc` 113 个资源叶全是 DIALOG/CURSOR/ICON/MENU/VERSION（无 `RT_BITMAP`/`RT_RCDATA`）。
6. 第三槽的**元数据齐全**：控件 id `1771`、battle 名 `tut1`、音效 `BootCampSelect`（SOUND.INI #534）、tooltip `STT:CampaignAnimTutorial`（`0x6041FD`）、描述 `DESC:TUT1`（`ra2md.csf` 内实存）。⇒ 这是**零售版被砍掉的官方 Boot Camp 入口**。
7. 已否决的路线：改 `RT_DIALOG 148` 补 `id=1771` 的**资源补丁**（路线 (c)）技术上可行（副本上已打通：`cDlgItems` 13→14、插 32 B 项、61/113 资源数据入口平移、回读 14 项 `trailing=0`），**但它会改变 `gamemd.exe` 的字节与哈希**，与"原版基线 + 版本守卫拒绝未知构建"直接冲突。本卡要的正是不走这条。
8. 游戏目录里的 `ddraw.dll` 是 **cnc-ddraw**（第三方，SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`），**不是官方件**，运行时被加载进游戏进程。

## 要求你逐条给判决的四条候选路线（每条都要有反汇编/字节级证据，不许只写"可行"或"可能"）
- **R1 运行时改对话框模板**：定位 `gamemd.exe` 创建 `RT_DIALOG 148` 的实际调用（是 `DialogBoxParamA/W`、`CreateDialogIndirectParamA/W`、还是自写 creation？给出 IAT 槽地址与调用点 VA/字节）。判断能否在模板进入 user32 之前被**进程内**拦截并在 13 项后追加第 14 项（`id=1771`）。**关键子问题**：谁来拦截？`gamemd.exe` 本身不能改，但 `ddraw.dll` 是进程内的第三方 DLL——评估"用自己写的 `ddraw.dll` 转发/包一层 cnc-ddraw"或"改 cnc-ddraw"两条子路，各自的可行性、被守卫对象是否包含 `ddraw.dll`（去仓库里查版本守卫/基线清单实际守哪些文件）、以及代价。
- **R2 非 STATIC 类的第三控件**：把第 3 个控件做成 `BUTTON`（有 caption 文字，就不需要徽章美术）。需要**反汇编确认** `0x52EC00` 里 `ChildWindowFromPointEx` 调用点的**过滤条件**：是只认 STATIC/`WS_EX_TRANSPARENT`，还是只按 `GetDlgCtrlID`？给出具体指令与结论。另外确认 `WM_COMMAND`/`BN_CLICKED` 路径是否需要该控件是特定类。
- **R3 复用既有控件**：`id=1820/1959/1960` 这些既有 Static 能否改 id（**不改 exe 就不可能**——请核实是否真的没有外部化机制），或引擎是否支持"控件 id 重映射"的 INI/配置。
- **R4 外部化机制**：确认引擎是否存在任何"对话框外部化"（从 INI/MIX/散装文件读 dialog 模板）的通道。若不存在，给出否证证据（字符串/导入/资源类型穷举范围）。

## 交付（写入 `lead\next_re_20261112_r03\W87_third_badge_noexe\`）
1. `THIRD_BADGE_NOEXE.md`：每条路线一节，**判决三档**「A 保持 exe 哈希可行（给最小落地方案 + 预计工作量 + 风险）／B 必须改 exe（给完整代价）／C 不可行（给否证证据）」，最后给总结论。
2. `EVIDENCE\`：反汇编清单（VA/RVA/文件偏移/字节/助记符）、PE 导入表与 IAT 槽、你写的所有脚本与其 stdout、文件哈希。
3. `UNKNOWNS.md`、`DISAGREE.md`（若与上面第 1–8 条任何一条冲突，必须单列）、`PROGRESS.md`。
4. 每条结论标证据分级：`[本次实测]`（你自己跑出的字节/反汇编）/ `[静态读码]` / `[静态推断]` / `[未证]`。

## 硬纪律
- **只读二进制**：禁止修改 `gamemd.exe`、`ddraw.dll`、`ra2youli` 下任何文件；禁止启动游戏、禁止注入、禁止附加调试器。
- 需要的二进制先**复制**到本卡目录再分析。
- 仓库里已有大量前序分析（`lead\next_re_20261112_r02\W61_third_badge_route\`、`REVIEW\LEAD_CHECK_menu_3slot.md`、`REVIEW\LEAD_RULING_C_line_route_a_first.md`、`docs\re\ARCHITECTURE_ATLAS.md` 等）。**先读再动手**，不要重复别人已经做完的工作；引用时要标明是转引还是你自己的实测。
- 结论"没找到"要写清搜索范围（扫了哪些节/多少字节/哪些编码/哪些反例校验），不许用"未发现"含混带过。
- **小步落盘**：先写 `PROGRESS.md` 骨架，每完成一条路线就写一次盘；不要憋到最后（本机 agy 长任务曾多次 `print timeout` 且无最终答复）。
- 时间预算约 60–90 分钟。若某条路线证据不足，**如实标 `[未证]` 并写清下一步最小证据**，不要编。



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
- process_exit_code: `0`
- conversation_id: `7a4bcd26-6671-4465-b06c-0bf4c716c3eb`
- model: `gemini-4-hydrogen-high`
- effort: `high`
- mode: `accept-edits`
- permission_mode: `always-proceed`
- receipt_path: `C:\Users\Administrator\AppData\Local\Temp\call-agy\.staging\20261114-035323-6212-4a5ee2fbec8a51d7-receipt.md`
- wrapper_watchdog: `5430.0s`
- agy_total_timeout: `90m`
- idle_warning: `10m`
- idle_grace: `5m`
- elapsed: `827.6s`
- agy_cumulative_duration_seconds: `817.247514`
- agy_cumulative_num_turns: `1`

## Tools used

- `edit_file` ×8
- `read_file` ×92
- `run_command` ×28
- `write_file` ×14

## Attempt history

- attempt 1: native_status=SUCCESS, exit=0, elapsed=827.578s, conversation_id=7a4bcd26-6671-4465-b06c-0bf4c716c3eb, tools={'run_command': 28, 'read_file': 92, 'write_file': 14, 'edit_file': 8}

## Usage reported by AGY

_These are native AGY counters. On resumed conversations they may be cumulative; do not add cache_read_tokens to total_tokens or infer billing without provider evidence._

- input_tokens: `1029506`
- output_tokens: `112871`
- thinking_tokens: `37669`
- cache_read_tokens: `6882111`
- total_tokens: `1142377`

---
Generated by `call-agy` via the official local `agy` CLI. Raw tool arguments/outputs are omitted by default.
