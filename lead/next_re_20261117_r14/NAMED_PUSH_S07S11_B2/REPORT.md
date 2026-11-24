# NAMED_PUSH_S07S11_B2 — REPORT（最终）

> 状态：**完成**。先建目录 → 先写 REPORT 骨架 → 逐行核完即落 `EVIDENCE/`。具名通道最后一批。

## 批次信息
- 子系统：**S07 剩余 4 行 + S11 剩余 11 行 = 15 行**（两池各只跑过 B1 18 行，池 22 / 29 行）
- 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S07S11_B2`
- 目标：`ra2youli\gamemd.exe`，SHA-256 现场复算 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面期望逐字相符）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（pefile VirtualSize 口径，与卡面一致；15 个 entry 全在其内）
- 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；无 venv、未 pip install
- 只写本批目录：`REPORT.md / PROGRESS.md / delta.tsv / base_rate.tsv / EVIDENCE/ / work/`；未改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`

## 候选筛选命令（可复算）
见 `work/filter_candidates.py`：
```bash
python work/filter_candidates.py
```
逻辑（与 S07_B1/S11_B1 的 filter_b1.py 一致）：从 `SURVEY_3B2/hits_detail.tsv` 取 `subsystem∈{S07,S11}` 且 `p3b2_named==True`；排除地址式伪名 `^(fn_|sub_)[0-9A-Fa-f]{8}$`（整名与 `::` 末段都判）；按 `entry` 升序；减去 `NAMED_PUSH_S07_B1/work/b1_rows.json`、`NAMED_PUSH_S11_B1/work/b1_rows.json` 各 18 行。

- S07：`named=True` **22**，伪名 **0** → 减 B1 18 → **4**：`006DBE00 007BA8C0 007BBB90 007BBCF0`
- S11：`named=True` **29**，伪名 **0** → 减 B1 18 → **11**：`0069ED20 0069EE30 0069FC10 00718100 007192F0 00719E30 00719F80 00728AF0 0072A1C0 0075C7F0 0075C920`

**两池耗尽**：22-18-4=0，29-18-11=0。

## D-40 四环口径（严格，卡面 + 本批简报三陷阱）
1. **① 入口**：`.text` 内、atlas 边界自洽、入口即指令边界、单一 ret 收尾
2. **② 类身份**：4B 槽==entry → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD`（绝对 VA）→ `TD+8` 装饰名内联串；`Class::` 仅线索；**强制判主表**：`COL.offset==0`、槽所在表 slot0 是真函数而非 this 调整 thunk（`83 6C 24 xx E9`）、装到 `[this+0]`。小成员/子对象接口表不算。②④ 不同源。
3. **③ 整体合同**：只认 ③b②，三条同时满足：(A) `call`→`test/cmp eax`→`jcc`，两指令间无 eax 覆写；(B) 被调返回约定可伪证（≥2 出口且含具名错误码/哨兵；`{0,1}` 布尔不算；(本题技术条：`Find` -1、流 I/O `E_POINTER`、QI `E_NOINTERFACE/E_POINTER/S_OK` 均算）；(C) 两路动作实质不同——一路立即 epilogue 原样上抛，另一路继续主流程。
4. **④ 使用见证**：活虚表派发——构造器把该表装进 `[this+off]`、`push size; call 0x7C8E17(new); call ctor` 实例化；entry direct caller=0（非 direct-only）；**㉓ 锚点不得落在析构器**（须枚举全部写点，逐一标 CTOR/DTOR）。

本批三陷阱（简报）逐行落实：**读写方向**（流 I/O 行逐字节核定 `[eax+0xC]`=Read / `[eax+0x10]`=Write，未写反）；**㉓**（4 行产出行的主表全部写点已枚举，④ 只锚行外 ctor）；**小成员表非主表**（S11 Locomotion 副表 slot0 thunk 全排除）。

## 逐行总表（15 行逐行核完）

| # | entry | name（原样） | ① | ② 类身份 | ③b② | ④ 见证 | 四环 | 产出 |
|---:|---|---|---|---|---|---|---|---|
| 1 | **006DBE00** | Tactical::slot6 | ✓ | ✓ 主表 007F4348 slot6 off=0 | ✓ 流写出 E_POINTER | ✓ ctor 006D1C20@006D1D54 | **是** | **[已证]** |
| 2 | 007BA8C0 | BSurface::slot18 | ✓ | ✓ 主表 007E2070 slot18 off=0 | ✗ 全间接调用，无可伪证站点 | ✓ | 否 | 否 |
| 3 | 007BBB90 | BSurface::slot2 | ✓ | ✓ 主表 007E2070 slot2 off=0 | ✗ 被调仅 {1,0} 布尔 | ✓ | 否 | 否 |
| 4 | 007BBCF0 | BSurface::slot3 | ✓ | ✓ 主表 007E2070 slot3 off=0 | ✗ 被调仅 {1,0} 布尔 | ✓ | 否 | 否 |
| 5 | 0069ED20 | ShipLocomotionClass::slot6 | ✓ | ✗ 副表 off=0x18 thunk | ✗ | ✓ | 否 | 否 |
| 6 | **0069EE30** | ShipLocomotionClass::slot0 | ✓ | ✓ 主表 007F2E58 slot0 off=0 | ✓ QI 多值 | ✓ ctor 0069EC50@0069ECD2 | **是** | **[已证]** |
| 7 | 0069FC10 | ShipLocomotionClass::slot16 | ✓ | ✗ 副表 off=4 thunk | ✗ | ✓ | 否 | 否 |
| 8 | 00718100 | TeleportLocomotionClass::slot17 | ✓ | ✗ 副表 off=4 thunk | ✗ | ✓ | 否 | 否 |
| 9 | 007192F0 | TeleportLocomotionClass::slot16 | ✓ | ✗ 副表 off=4 thunk | ✗ | ✓ | 否 | 否 |
| 10 | **00719E30** | TeleportLocomotionClass::slot0 | ✓ | ✓ 主表 007F50CC slot0 off=0 | ✓ QI 多值 | ✓ ctor 00718000@0071805E | **是** | **[已证]** |
| 11 | 00719F80 | TeleportLocomotionClass::slot6 | ✓ | ✗ 副表 off=0x18 thunk | ✗ | ✓ | 否 | 否 |
| 12 | 00728AF0 | TunnelLocomotionClass::slot17 | ✓ | ✗ 副表 off=4 thunk | ✗ | ✓ | 否 | 否 |
| 13 | 0072A1C0 | TunnelLocomotionClass::slot35 | ✓ | ✗ 副表 off=4 thunk | ✗ 单值 0 | ✓ | 否 | 否 |
| 14 | **0075C7F0** | WalkLocomotionClass::slot0 | ✓ | ✓ 主表 007F6AC4 slot0 off=0 | ✓ QI 多值 | ✓ ctor 0075AA90@0075AADF | **是** | **[已证]** |
| 15 | 0075C920 | WalkLocomotionClass::slot6 | ✓ | ✗ 副表 off=0x18 thunk | ✗ | ✓ | 否 | 否 |

`base_rate`：`rows_checked=15  ring2_ok=7  ring3b_ok=4  ring4_ok=15  all_four=4  rate=0.2667`

## 逐环裁定依据

### ① 入口 —— 15/15 PASS
每个 entry 都是 atlas 的函数起点，入口首条即指令边界，收尾单一 `ret`/`ret 0xc`/`ret 8`。size 29–2302。

### ② 类身份 —— 7/15（**决定性环之一**）
15/15 的 RTTI 都能解析出与线索一致的类名（TD 绝对 VA、TD+8 内联串，逐行见 EVIDENCE），但强制主表判定后只剩 7 行：
- **S07 4/4**：全部 `COL.offset==0`、slot0 是真函数（Tactical vt[0]=00410260；BSurface vt[0]=00411650）、装到 `[this+0]`，主表成立。（BSurface 三行同时出现在 XSurface/DSurface 表同槽是继承复用，主表 007E2070 仍钉死。）
- **S11 3/11**：仅 3 行 slot0 落在主表（Ship 007F2E58 / Teleport 007F50CC / Walk 007F6AC4，均 `COL.offset==0`、slot0 字节 `53 8B 5C 24 08 55 8B 6C` 真 QI 函数、装到 `[esi+0]`）。**其余 8 行**全部落在子对象副表：`COL.offset=4` 或 `0x18`，slot0 字节 `83 6C 24 04/18 E9 …`=`sub [esp+4],N; jmp` this 调整 thunk，安装偏移 `[this+4]`/`[this+0x18]` ⇒ 按陷阱③判 ② FAIL。与 S11_B1（4/18）完全同型：这是 Locomotion 多继承族的固有 ② 缺口，不是"没名字"。

### ③ 整体合同 —— 4/15（全部 ③b②），两类站点
产出 4 行的 ③b② 与 B1 已证行字节级同模板：
1. **一行流写出**（006DBE00 Tactical::slot6）：`call 0x410320@006DBE0F`（被调 `[eax+0x10]`=IStream::Write，方向逐字节核定为写出未写反）→ 零间隔 `test eax,eax@006DBE14`→`jl@006DBE16`；失败原样上抛负 HRESULT（`mov eax,0x80004003`@0041032B E_POINTER 伪证），成功 `xor eax,eax@006DBE18` 返 0，两路真不同。与 S07_B1 的 00555110 LightSourceClass::slot6（流写出）同判据。
2. **三行 QueryInterface 实现**（0069EE30 / 00719E30 / 0075C7F0，字节级同模板、地址各异）：`call 0x55A9B0`→零间隔 `cmp eax,0x80004002`→`jne`；被调多值约定 `0x80004003 E_POINTER@0055A9B8` / `0x80004002 E_NOINTERFACE@0055AA41` / `0 S_OK@0055AA4F`；taken 路 `pop/pop/pop/ret 0xc` 不碰 eax（基类 HRESULT 原样上抛），fall 路 `repe cmpsd` 比 IID → `lea eax,[ebx+0x18]`/`mov [ebp],eax`/`call [ecx+4]`(AddRef)/`xor eax,eax`。与 S11_B1 的 004AF720/004B6470/0054DC60 同判据。

**未成立 11 行逐行理由**（各自独立地址，非整批共用 reason；详见各行 EVIDENCE）：
- `007BA8C0`：621B/230 指令，全部 call 为间接虚调用（`[edx+0x70]`/`[eax+0x5c]`/`[eax+0x74]`/`[eax+0x60]`），callee 不可由字节定位 ⇒ B 失败。
- `007BBB90`/`007BBCF0`：唯一直接 `call 0x7BBE20`→`test al,al`→`je`；被调 007BBE20 出口仅 `{1,0}`（`mov eax,1@007BBFD8`/`xor eax,eax@007BBFE6`）=布尔不算；其余站点为间接 call→`cmp eax,1`。
- `0069ED20`/`00719F80`/`0075C920`（slot6）：`call 0x45AEA0`(nullable 流 QI)→`test/jge` 汇合、`call 0x7DC720`(清理包装)、间接 call ⇒ 无 early-return 分离，同 S11_B1 判例。
- `0069FC10`/`00718100`/`007192F0`/`00728AF0`（slot16/17）：站点全是间接虚调用（`[edx+0x2c]`/`[eax+0x1b8]`/`[eax+0x37c]`/`[edx+0x380]`/…）或 operator new 空判/小枚举，callee 不可伪证。
- `0072A1C0`（slot35）：唯一 `call 0x55AD00@0072A1C6`→`test eax,eax`→`jne`；被调出口仅 `xor eax,eax`=0（单值）不可伪证。

**三陷阱排查**：4 行成立行的 `test/cmp` 与 `jcc` 均相邻（无 eax 覆写，见 EVIDENCE 字节）；每个站点 call 目标唯一（非多路同一 call）；语义均由字节支撑，无"初始化/清零"模板句。

### ④ 使用见证 —— 15/15 PASS（但只有 4 行能与 ② 同时成立）
- 产出 4 行的主表由行外构造器装到 `[this+0]`（C7 06 `<vt>`），构造器开头先调基类 ctor `0x55A6C0`、尾 `mov eax,esi; ret` 返 this，并由唯一 `push size; call 0x7C8E17; call ctor` 实例化：
  - Tactical ctor `006D1C20@006D1D54`，`push 0xE18; new`，调用者 0052C694/00599D80/006853B4/00687617/006BF84F
  - Ship ctor `0069EC50@0069ECD2`，`push 0x70; new@006C4F3E`，调用者 006C4F4C
  - Teleport ctor `00718000@0071805E`，`push 0x4C; new@006C4C3E`，调用者 006C4C4C
  - Walk ctor `0075AA90@0075AADF`，`push 0x3C; new@006C47BE`，调用者 006C47CC
- 4 行 entry 的 direct caller = **0**，只能经活虚表派发（非 direct-only）。
- **㉓ 写点全枚举**：逐行列出同表所有写点并标 CTOR/DTOR（见各行 EVIDENCE ④ 节）。4 行主表均存在删除式析构器重装点（Tactical 006DC470@006DC473、Ship 0069ECF0@0069ECF3/006A42B0@006A42B3、Teleport/Walk 同型），**④ 一律不取这些点**，锚行外 ctor。
- **②④ 不同源**：② 锚 `.rdata` 槽 dword + COL + TD 名串字节；④ 锚 `.text` 的 `C7 06 <vt>` 安装指令 + operator new 实例化链。段、地址、指令类型都不同。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）
- **S04**：73 个 ③b② 机械命中 `named=0`，entry 作 4B VA 全镜像 0 引用、无虚表槽、无 RTTI 链 ⇒ ② 物理不可得，36 行实测全败。
- **本批**：15/15 全为 `Class::slotN` 真名（0 伪名），15/15 在 `.rdata` 有虚表槽、RTTI 全解析出与线索一致的类名 ⇒ "有名字"确实解开了 S04 的 ② 硬约束（② 从 0/73 变成 15/15 有 RTTI 链）。
- 但本批复现了 S11_B1 的**第二个更细的 ② 缺口**：S11 Locomotion 多继承族每类 1 主表 + 1~2 子对象接口表，**8 行的槽落在副表**（`COL.offset=4`/`0x18`，slot0 this 调整 thunk、安装 `[this+4]`/`[this+0x18]`），按陷阱③不算类身份。严格口径下 **② = 7/15**（4 S07 + 3 S11 slot0）。
- 宽窄口径敏感性同 S11_B1：若 Lead 采"副表 RTTI 也认类身份"的宽口径，② 会变 15/15，但 **all_four 仍为 4**（③ 只有 4 行成立），`rate` 仍 0.2667。请 Lead 定标；本卡按严格口径报数。
- 最终 **② 真的钉住 7 行**（严格）/ 15 行（宽）；四环齐全产出 4 行。

## 产出清单
- `REPORT.md`（本文件）/ `PROGRESS.md`
- `delta.tsv`：**4 数据行**，全 `[已证]`，`entry` 大写无 `0x`，`name`/`subsystem` 原样，`evidence_path` 指本目录 `EVIDENCE/ROW_<entry>.txt`
- `base_rate.tsv`：`NAMED_PUSH_S07S11_B2	15	7	4	15	4	0.2667`
- `EVIDENCE/ROW_<entry>.txt` × **15**：每行四环地址 + 机器码字节 + 逐环裁定（含 RTTI 链、主/副表 thunk 字节、③ 站点与返回常量、④ 写点全枚举与实例化链）
- `work/`：filter_candidates.py / core.py / dump_entries.py / compact.py / verify_candidates.py / verify_inst.py / verdicts.py / gen_evidence.py 及中间 JSON/TXT —— 全部只读 gamemd.exe，写域仅本批目录，可复算。
