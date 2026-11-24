# S01-K2 · PROGRESS（主循环骨架 + 帧时钟；纯静态，未跑真机）

卡号 S01-K2｜目标 gamemd.exe SHA256 73201CC0…F67476（ImageBase 0x400000，只读）｜
写域仅本卡目录 + `_ghidra\S01-K2\`｜工具 Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26。
基线：已读 `R14_COMMON.md`(454行)、`STATUS_BOARD.md`、前序 `S01-V1\PROGRESS.md`+`_audit\VERDICT.md`（未读其 EVIDENCE）、
`COVERAGE\PANEL.md`+`coverage_README.md`。未改台账/游戏文件，未 git commit，未跑真机。

## 结论表（三级分级 + 证据路径）

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | 主循环 `0x48CCC0`(780B) 内层帧循环 `[0x48CE8A,0x48CEA8]`，回边 `0x48CEA8→0x48CE8A`；4 个顶层 call site 有序：#1 `0x48CE8A`→`0x55D360` PerFrameUpdate（必调）、#2 `0x48CE93`→`0x55CFD0` FramePredicate（条件）、#3 `0x48CE9C`→`0x48C8B0` FrameDraw（常态）、#4 `0x48CEA1`→`0x55CFD0`（必调）。每 tick 不同 callee = **3**（`0x55D360/0x48C8B0/0x55CFD0`） | [静态推断]+3边[已证] | `EVIDENCE/mainloop_disasm.txt`；栈边沿用 S01-V1 `stack_dense.ndjson`（94739/3/2） |
| 2 | N=16 门控逐字节：`idiv [ecx+0x1808]@0x4DA560` → `test edx@0x4DA566` → `jne 0x4DA63B@0x4DA568`；跳过区间 `[0x4DA56E,0x4DA63B)`（应答/声音/矿石价值），**门控后每帧都跑**；loco 派发点 `0x4DA877 call [ecx+0x40]` 在其后 | [已证] | `EVIDENCE/gate_4DA560_disasm.txt`、`loco_4DA820_disasm.txt` |
| 3 | 帧时钟：Sleep=IAT `0x7E11F0`(52 引用)、timeGetTime=IAT `0x7E1530`(106 引用)；帧计数 `0xA8ED84`(1007引用/10写) 在 `0x55DE7E inc`/`0x55DE81` 写回；时间戳存 `0xA8B55C`(`call timeGetTime@0x55D3D4`)；目标 FPS `0xA8B558`，`0x55D51C: 1000/idiv` | [已证]（IAT+字节） | `EVIDENCE/iat_full_map.txt`、`timer_iat_sites.txt`、`xref_all.txt`、`perframe_55D360_disasm.txt` |
| 4 | 帧限速机制 = `0x55E160` 内 `timeGetTime` 环 + `push remaining; call Sleep`（S16 归 MainLogicFrame::UpdateHouses）；另有 `0x55D360` 的 `Sleep(500)/Sleep(10)` 等待态循环。32ms 地板 ↔ 31.25fps 与真机 31.247 一致（量纲） | [静态推断]（机制）+真机[已证]（31.247） | `EVIDENCE/fn_55E160_disasm.txt`、`perframe_55D360_disasm.txt`；真机引用 S01-V1 PROGRESS |
| 5 | `0x6D9A50` 切片遍历器：读 `[+0x80]` 门控(`0x6D9A88`) + 几何裁剪 + 直接 `call 0x6D2790`(`0x6D9B15`) + 清脏(`0x6D9B1A`)；**无 `call [edx+0x104]`** ⇒ §4.7 更正成立 | [已证] | `EVIDENCE/iter_6D9A50_disasm.txt`（93 行全量） |
| 6 | LogicClass（RTTI TD `0x816B30`/COL `0x7FA970`/vt `0x7E1900`）是容器类：v[11]=数据 `0x7FA9A0`、v[12]=构造链 `0x40CF30`；30 槽内 **0 个 `B8 imm32 C3`**；无堆分配双点 ⇒ GetSize **不可定**，槽 12 惯例不适用 | [已证]（RTTI 链+穷举） | `EVIDENCE/getsize_candidates_v2.txt`、`rtti_targets.txt`；方法见 LAYOUT.md |
| 7 | mode=0/3/4/5 写点并存（written immediates ∈{0,3,4,5}），mode==5 覆盖遭遇战设置/局内/暂停三态 ⇒ 静态**不能**单凭 mode 判"局内" | [已证]（写点）/[未证]（局内判据） | `EVIDENCE/mode_writes.txt`、`xref_all.txt` |

## 给审计员的 3 个核心数字 + 复算方法

1. **主循环每 tick 不同 callee = 3**（4 call site，其中 0x55CFD0 占 2 个）。
   复算：`capstone.disasm(read(0x48CCC0,0x320))`，取 mnemonic=='call' 且 target∈{0x55D360,0x55CFD0,0x48C8B0} 的 site，得 0x48CE8A/93/9C/A1；按 `test al; je/jne` 走向判 #2 条件、#4 必调。对照 `EVIDENCE/mainloop_disasm.txt`。
2. **N=16 门控跳过的区间长度**：`0x4DA63B − 0x4DA56E = 0xCD = 205 B`（约 40 条指令，非"60 条"字面）；loco 派发 `0x4DA877` 在此之后。
   复算：`read(0x4DA554,0x1A0)` 反汇编，定位 `idiv [ecx+0x1808]` 的下一条 `jne` 目标 = 0x4DA63B；再定位 `0x4DA877 call [ecx+0x40]`。对照 `gate_4DA560_disasm.txt`/`loco_4DA820_disasm.txt`。
3. **S01 覆盖数字（盘面现值，统一大小写后）**：atlas_n=**53**、named(L=**10**, S=**10**,18.87%)、proved=**6**(11.32%)、static=8、unproved=39。
   复算：`python work/t1_targets.py` → `EVIDENCE/t1_report.txt`；atlas hex 小写、coverage 大写，**不统一大小写交集仅 11**（§990 坑实证）。到 50% 门槛 27/53 差 **21**；到 named 90% 门槛 48/53 差 **38**。
   ⚠️ 派卡 §2 写"proved 5(9.43%)"是 M2 前旧截面；盘面 PANEL 为 6/11.32%（M4 后），已按纪律 9 登记 DISAGREE D1，**未凑数**。

## S01 计数变化与 delta

- **proved 6 → 6**（本卡未新增 S01 [已证] 行；核实的核心 4 函数均已在 coverage [已证]）。
- **named 10 → 10**（L=S，S01 无 `Class::sub_` 占位）。
- **coverage_delta.tsv = 0 数据行**：无新 S01 入口、无可辩护的 grade 升级；跨写域发现（0x55E160=S16、0x6D9A50=S07）记入 DISAGREE/MAINLOOP 供主卡转交。
- 停机核验：31.247fps / N=16 / 0x4DA877 三项均一致（DISAGREE 表末），未触发停机。
