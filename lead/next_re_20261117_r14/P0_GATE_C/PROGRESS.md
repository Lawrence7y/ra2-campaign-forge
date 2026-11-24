# P0-GATE-C · PROGRESS.md（完整版）
> 纯静态；gamemd.exe SHA-256 73201CC0…F67476。证据相对本卡目录（EVIDENCE/ work/）。
> 停机核验：卡面「直接写 0 11 处」逐字节核对为 11 处 bit0=0，其中字面 0 **仅 5**（见 UNKNOWNS U3）。[0xA8E9A0] 按 op.access = 23W/100R（§994 更正见 DISAGREE.md）。

## 结论表
| 结论 | 等级 | 证据路径 |
|------|------|----------|
| 路径条件：四标志全 0 + M=1 + E7=0 时 0x47C620→0x47C648→0x47C6DD→0x47C6EB→0x47C6F9→0x47C701→0x47C72F→0x47C738（查 head A），**不走** 0x47C6A0 不查占用支 | **[已证]**（字节级） | EVIDENCE/p1_gate_dis.txt；work/p1_gate_dis.py；FINAL_PATH.txt |
| 0x47C3D0 的 0x47C427 `and al,1` 对 head A 每个对象过滤 bit0 | **[已证]** | EVIDENCE/p3_focused.txt；work/p3_focused.py |
| 工厂构造 Infantry/Unit：slot 0x6C3890/0x6C3410→0x517A50/0x7353C0→0x4D31E0→0x6F2B40；0x6F322F `or al,1`→0x6F3237 写回；ret@0x6F3266 前无绕过分支 ⇒ bit0 恒 1 | **[已证]**（该构造路径） | EVIDENCE/t3_u3_noskip.txt, t3_u3_inffactory.txt, FINAL_BIT0_SUMMARY.txt |
| 11 处 bit0=0 写点全部不可能命中「已放置、待判步兵」（5 栈槽 + 2 VQMovieHandle 构造 + 1 0x40B 小对象 + 1 IPX/Winsock 拷贝构造 + 1 小状态块 + 1 out-holder） | 10/11 **[已证]**（字节级），#1 out-holder 结构分离为 [静态推断]（U7）；全域恒 1 亦 [静态推断] | BIT0_ZERO11.md；EVIDENCE/p2_classify11.txt, p3_focused.txt, p5_vtables.txt, p6_verify.txt, p11_direct.txt；UNKNOWNS U7 |
| 四标志写/读：0x16BF 2/31、0x16BE 2/30、0x16B7 2/24、0xE58 9/11；绝对寻址 0、reg+off 111、base+idx 0 ⇒ 只扫绝对漏全部 15 写 | **[已证]**（计数） | EVIDENCE/t1_field_scan.txt；work/t1_field_scan.py |
| [0xA8E9A0] 23 写 / 100 读；a10 的 36 = 23 + 13 cmp 误记 | **[已证]**（计数） | EVIDENCE/p6_verify.txt；work/p6_verify.py；DISAGREE.md |
| arg2 类 = `.?AVBuildingTypeClass@@`（COL 0x7FC618→TD 0x8193A8→TD+8） | **[已证]** | EVIDENCE/t_final_verify.txt；work/t_final_verify.py |
| 场景综合：mode 1/3 挂链 + 目标格有步兵 ⇒ 0x47C738 走到，bit0=1 使 0x47C427 不跳过 ⇒ 拒绝放置（al=0） | **[静态推断]**（非真机；受 U1/U2/U4/U7 限制） | FINAL_PATH.txt；UNKNOWNS.md U1/U2/U4/U7 |
| 「引擎是否允许建筑与步兵同格」总判断 = 不允许（上述场景） | **[静态推断]** —— **不抬 [已证]** | 同上；未做真机观测 |

## 未闭环（摘要）
arg1 [esp+0x1c] 未定论；0xE58 的 8 个非 INI 写点中 #6/#8 语义未证；26 处 register-derived bit0 写点未逐一追值；gate this 类名 fail-closed；bit0 #1 的 ebx 精确类未定（U7）。逐条见 UNKNOWNS.md。

## 审计员核心数字（3 个）
1. **23 / 100**：[0xA8E9A0] 写 / 读（capstone op.access），§994 的 36 = 23 + 13 cmp。复算 `work/p6_verify.py`。
2. **11 → 5**：bit0=0 直接写点 11，其中字面 imm=0 仅 5；11/11 分类为不可达在册步兵。复算 `work/t3_u3_bit0_counts.py` + `work/p6_verify.py`，分类 `BIT0_ZERO11.md`。
3. **0x47C738**：实测四标志全 0 + M=1 的落点（查 head A）；0x47C427 的 `and al,1` 是步兵恒命中的判定点。复算 `work/p1_gate_dis.py` + `work/p3_focused.py`。

## 真机观测
**本结论仍需要真机观测**：字节级部分（路径条件、构造 bit0、写读计数）可独立复算，但总判断为 [静态推断]。
D-36 请裁的硬件断点（对 [infantry+0x14] 写 0 / 对 0x47C738 命中）**不应撤销**，正是为闭环 U1/U2/U4/U7。
