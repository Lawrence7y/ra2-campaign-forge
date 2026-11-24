# S15S16-3B2 — ③b② 通道攻 S15/S16 proved 缺口

## 材料自校验
- `gamemd.exe` SHA-256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡片期望一致）
- Python 3.12.10 / capstone 5.0.7（skipdata=True）/ pefile 2024.8.26；ImageBase 0x400000，.text=[0x401000,0x7E038D)
- 池 = coverage.tsv 中 subsystem∈{S15,S16} 且 grade==[静态推断]：S15 44、S16 38、合计 82（atlas entry 大小写归一）
- 复算脚本在 `work/`：`extract_pool.py`→`analyze.py`→`witness.py`→`generate_outputs.py`。中途修两处真 bug 后重跑：① capstone 5.0.7 无条件跳转常量名是 `X86_INS_JE/JNE/...`（不是 JZ/JNZ），旧集合漏 `je/jne` 造成假阴性；② P3 原实现只认“被调体内 mov eax,imm”，漏掉调用点直接 `cmp eax,-1`/`test eax,eax;je` 的可伪证哨兵——两者均为卡片 P3 明列形态。

## 第 1 步 · 机械预筛（只筛，不下结论）

判据（机械、可复算）：
- P1：函数体内 `call` 后 ≤3 条内出现 `test eax,eax` / `or eax,eax` / `cmp eax,imm`，其后 ≤2 条内紧跟 jcc（capstone 5.0.7 全部 J* 常量）。
- P2：jcc 的 taken 与 fallthrough 路径“动作签名”（直接 call 目标集 / 返回常量集 / 是否 ret / 末端 eax 常量）不同；仅同一 call 参数不同不算。
- P3：可伪证具体返回约定且调用方分支——(a) 调用点 `cmp eax,-1` / `test eax,eax;je` 直接比对哨兵（卡片明列 -1/0）；或 (b) 静态可解析被调（.text、atlas 边界）有 falsifiable 失败常量 ret 与另一 ret 原点（HRESULT 约定）。

报数（分母 = 池大小）：

| subsystem | pool | P1 | P1∧P2 | P1∧P2∧P3 | base rate (P1P2P3/pool) |
|---|---:|---:|---:|---:|---:|
| S15 | 44 | 22 | 20 | 20 | 0.4545 |
| S16 | 38 | 6 | 6 | 3 | 0.0789 |
| ALL | 82 | 28 | 26 | 23 | 0.2805 |

诚实基础率：本通道总命中率 28.05%（S15 45.45%，S16 7.8947%）。P1 共 28 行，P2 砍掉 2 行，P3 砍掉 3 行；P1P2P3 命中 23 行。

## 第 2 步 · 抽样人工核（P1∧P2∧P3 命中最高的 12 个）

排序规则：按每 entry 的 P1P2P3 命中点个数降序，同数按 entry 地址升序；取前 12 个。逐行四环如下：

| # | entry | sub | ① 入口/边界 | ② 类身份(RTTI/vt) | ③ ③b② (形态/哨兵或HRESULT/检查点/消费点) | ④ 使用见证 |
|---|---|---|---|---|---|---|
| 1 | 00727240 | S15 | 0x00727240 size=897 | .?AVTriggerTypeClass@@ / vt 007F5904+0x64 | call 0x00528A10@0x00727274→TEST_EAX(sentinel 0x0)→je@0x0072727B→fail@0x007275B4; call 0x007C8D20@0x007272E4→TEST_EAX(sentinel 0x0)→je@0x007272EE→fail@0x00727374; call 0x007C8D20@0x007272FA→TEST_EAX(sentinel 0x0)→je@0x00727304→fail@0x0072736C (+9 more) | ✔ vslot 0x007F5968, ctor 00726CD2,00726E06 |
| 2 | 006CE800 | S16 | 0x006CE800 size=200 | .?AVSuperWeaponTypeClass@@ / vt 007F4090+0x14 | call 0x00410380@0x006CE814→TEST_EAX@0x006CE819→jl@0x006CE81B→fail@0x006CE8BE(callee falsy 0x80004003); call 0x005B40B0@0x006CE89B→TEST_EAX@0x006CE8A0→jne@0x006CE8A8→fail@0x006CE8BC(callee falsy 0x0) | ✔ vslot 0x007F40A4, ctor 006CE717,006CE74D |
| 3 | 007276A0 | S15 | 0x007276A0 size=477 | .?AVTriggerTypeClass@@ / vt 007F5904+0x68 | call 0x00528660@0x0072774B→TEST_EAX(sentinel 0x0)→je@0x0072775A→fail@0x00727764; call 0x00528660@0x007277DA→TEST_EAX(sentinel 0x0)→je@0x007277E9→fail@0x007277F3 | ✔ vslot 0x007F596C, ctor 00726CD2,00726E06 |
| 4 | 0053AE50 | S16 | 0x0053AE50 size=227 | 未取得（无 vt 槽） | call 0x007C8E17@0x0053AEC4→TEST_EAX(sentinel 0x0)→je@0x0053AECE→fail@0x0053AEF1 | ✘ 仅 direct caller ['006CCDE2']（direct-only → ④ 不合格） |
| 5 | 006E3DB0 | S15 | 0x006E3DB0 size=125 | .?AVTActionClass@@ / vt 007F443C+0x14 | call 0x00410380@0x006E3DBB→TEST_EAX@0x006E3DC0→jl@0x006E3DC2→fail@0x006E3E29(callee falsy 0x80004003) | ✔ vslot 0x007F4450, ctor 006DD036,006DD18D |
| 6 | 006E3E30 | S15 | 0x006E3E30 size=29 | .?AVTActionClass@@ / vt 007F443C+0x18 | call 0x00410320@0x006E3E3F→TEST_EAX@0x006E3E44→jl@0x006E3E46→fail@0x006E3E4A(callee falsy 0x80004003) | ✔ vslot 0x007F4454, ctor 006DD036,006DD18D |
| 7 | 006E4660 | S15 | 0x006E4660 size=291 | .?AVTActionClass@@ / vt 007F443C+0x20 | call None@0x006E472C→CMP_IMM(sentinel 0xffffffff)→je@0x006E4732→fail@0x006E4761 | ✔ vslot 0x007F445C, ctor 006DD036,006DD18D |
| 8 | 006E56E0 | S15 | 0x006E56E0 size=75 | .?AVTagClass@@ / vt 007F44E0+0x34 | call 0x004A1D50@0x006E56FD→TEST_EAX(sentinel 0x0)→je@0x006E5707→fail@0x006E571B | ✔ vslot 0x007F4514, ctor 006E4E07,006E4F69 |
| 9 | 006E5730 | S15 | 0x006E5730 size=97 | .?AVTagClass@@ / vt 007F44E0+0x14 | call 0x00410380@0x006E573B→TEST_EAX@0x006E5740→jl@0x006E5742→fail@0x006E578D(callee falsy 0x80004003) | ✔ vslot 0x007F44F4, ctor 006E4E07,006E4F69 |
| 10 | 006E57A0 | S15 | 0x006E57A0 size=29 | .?AVTagClass@@ / vt 007F44E0+0x18 | call 0x00410320@0x006E57AF→TEST_EAX@0x006E57B4→jl@0x006E57B6→fail@0x006E57BA(callee falsy 0x80004003) | ✔ vslot 0x007F44F8, ctor 006E4E07,006E4F69 |
| 11 | 006E6080 | S15 | 0x006E6080 size=None | .?AVTagTypeClass@@ / vt 007F45C4+0x64 | call 0x00528A10@0x006E60B4→TEST_EAX(sentinel 0x0)→je@0x006E60BB→fail@0x006E6150 | ✔ vslot 0x007F4628, ctor 006E5CA7,006E6434 |
| 12 | 006E6410 | S15 | 0x006E6410 size=86 | .?AVTagTypeClass@@ / vt 007F45C4+0x14 | call 0x00410380@0x006E641B→TEST_EAX@0x006E6420→jl@0x006E6422→fail@0x006E6462(callee falsy 0x80004003) | ✔ vslot 0x007F45D8, ctor 006E5CA7,006E6434 |

12 个样本中 11 个四环齐全进入 delta；`0053AE50`(PsyDom::Start) 只有 1 个 direct caller、无 vtable 槽，按“direct-only 不足 / D-40 不得据 direct call 单独升 [已证]”判环④不合格，**不进 delta**（其 ③b② 本体形态仍成立，但缺活使用见证）。

## 第 3 步 · 产出 delta（只放四环齐全的行）

- `S15_delta.tsv`：10 行；`S16_delta.tsv`：1 行；entry 一律大写十六进制、无 0x 前缀；grade [静态推断]→[已证]；name/subsystem 原样。
- 第 4 列写明 ③b② 形态 + 地址锚，不含“循环内非栈写”、不自陈未证。每行一份 `EVIDENCE/ROW_<entry>.txt`。

## 明确回答：按此通道，S15 / S16 还能达标吗？

现状（卡片给定、不再核）：S15 proved_strict=48、门槛 ceil(0.5n)=79、差 31；S16 proved_strict=20、门槛 45、差 25。
proved_strict 只统计 atlas 内 [已证] 且语义无 [未证]，故下面“可并 strict”只数 atlas 内 delta 行（006E6080 四环齐全、入 delta，但不在 atlas，不计入 strict）。
本卡四环齐全的 delta 行：S15 10 行、S16 1 行；其中 atlas 内、可并入 strict：S15 +9，S16 +1。

| 子系统 | 现有 strict | 本卡可并 | 并入后 | 门槛 | 达标? | 仍缺 |
|---|---:|---:|---:|---:|---|---:|
| S15 | 48 | +9 | 57 | 79 | 否 | 22 |
| S16 | 20 | +1 | 21 | 45 | 否 | 24 |

**结论：S15、S16 都不能靠本通道达标。** 即便把本卡 atlas 内可并的 10 行全部计入 strict，S15 48→57 仍差 22（门槛 79），S16 20→21 仍差 24（门槛 45）。基础率 28.05%（S16 仅 7.89%），且命中多集中于同一批 COM-HRESULT / FindIndex 哨兵模板族，扩域有限。

## 缺口该从哪类通道补

- 本卡 ③b② 命中虽增至 23 行，但四环齐全且可并入的仅 12 样本中的 11 行，不能作为补缺主力。
- 剩余缺口（S15 22 行、S16 24 行）须换通道：③b① 模式域多分支分派、③b④ 有界循环带非栈写，以及 ② 类身份（RTTI/构造链/虚表归属）与 ③a 语义直接证据补强；不得放宽 ③b②（常量返回值但调用方不检查的不算可伪证）。
- 另：本次未进入 top12 的 11 个 ③b② 命中行（多为 slot6/slot8/slot13 同模板）若后续补做环④活派发见证，可再提供有限增量，但数量级仍不足以填平 S15/S16 缺口。

