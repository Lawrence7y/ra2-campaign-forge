# W174 · `[+0x80]` 写点全量分类 — PROGRESS

卡号 W174｜结论：台账 179 写点/83 函数数值成立，但「全是 ObjectClass 脏标记」被否证——111 处实为 TeamClass `StepCompleted`。

## 结论表

| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | 全镜像 `mov byte [reg+0x80],src` 写点 **179** 处，双通道一致（通道A线性反汇编 skipdata / 通道B原始字节 `C6/88 + mod10 + disp32=80 00 00 00`），差集 0 | [已证] | `EVIDENCE/w174_scan_summary.txt`, `w174_channelB_writes.tsv` |
| 2 | 涉及 **83** 函数；M3（atlas∪call-target 区间包含）与 M2（entry_at_or_before）均得 83 且函数集全等 | [已证] | `EVIDENCE/w174_attrib_M3.txt`, `w174_attrib_analysis.txt` |
| 3 | 原始 atlas 区间包含仅得 79 函数+38 未归属——因 atlas 对 `0x6ECA70`/`0x454CE0` 等 size 低估（如 `0x6ECA70` size=213 但写点延至 `0x6ECCC8`）；**不可用原始 atlas size 判归属**（纪律14） | [已证] | `EVIDENCE/w174_attrib_M1.txt`, `w174_fn_signature.txt` |
| 4 | 写值分布：`1`=147, `0`=14, `al`=8, `bl`=7, `dl`=2, `cl`=1（逐字节核对，非凭印象） | [已证] | `EVIDENCE/w174_writes.tsv`, `w174_scan_summary.txt` |
| 5 | 类属：YRpp `ObjectClass.h:281` `+0x80=NeedsRedraw`（脏标记）；`TeamClass.h:88` `+0x80=StepCompleted`（脚本步骤完成）。原始 vtable `0x7F4730+0x5C`=`0x6E9140`（TeamClass slot23），故 `0x6E9140` 的 38 写为 TeamClass，**非** ObjectClass | [已证] | `EVIDENCE/w174_vtable_raw_verify.txt`, `w174_this_origin_probe.txt` |
| 6 | 按函数类属：OBJ 41 函数/52 写；TEAM 31 函数/111 写（`0x6E8000..0x6F1000` 全段，特征 `[this+0x54]`=FirstUnit + 该段为 TeamClass 代码）；UNKNOWN 11 函数/16 写 | [静态推断] | `EVIDENCE/w174_class_decision.txt`, `w174_fn_signature.txt` |
| 7 | TEAM 区非 ecx 传递的栈参函数（`ret 8`，`mov reg,[esp+N]`）其 `this` 来自栈参，仍属 TeamClass；例 `0x6ECF8C`/`0x6EFCD5` | [静态推断] | `EVIDENCE/w174_classify_context.txt` |
| 8 | 消费/清0 站点集合与台账 §925-2 一致：`0x43CEFD`,`0x5438E2`,`0x543A7D`,`0x543B72`,`0x5F4B56`,`0x5F4EA5`,`0x5F4F55`,`0x6D98EF`,`0x6D9A27`,`0x6D9B1A`,`0x6EEBA3`,`0x71CCAD`,`0x75F919`,`0x75F9D3` (14) | [已证] | `EVIDENCE/w174_classify_results.tsv` (cls=a) |

## 四类计数（179 全量；CFG 为主口径）

| 类 | 定义 | CFG 口径 | 邻近比较口径 | 分级 |
|---|---|---|---|---|
| a | 写 0 | **14** | 14 | [已证] |
| b | 写 1 且分支门控/前有比较 | **104** | 112 | [静态推断] |
| c | 写 1 无门控（无条件置位） | **43** | 35 | [静态推断] |
| d | 写寄存器值 | **18** | 18 | [已证] |

b/c 口径敏感（窗口 4→16 时 b=73..116, c=74..31，见 `w174_classify_literal.py`）。CFG 定义：写点仅能从某条件分支的一侧到达 ⇒ b；两侧皆可达 ⇒ c（`w174_classify_cfg.py`）。**d 类 18 处源码寄存器已逐条回溯，见 `w174_site_origin_backward.tsv`。**

## 「无条件置位」(c 类 CFG 口径) 全部地址（43）

`006E9521 006E9574 006E9674 006E96AE 006E98BA 006E98D6 006E98F2 006E9912 006E992F 006E9949 006E99D3 006E99EF 006E9B5C 006E9B77 006E9B92 006E9BAF 006E9BCC 006E9CE1`（以上 fn=006E9140 TEAM）
`006ECF38 006EDAA8 006EDAD8 006EDB08 006EDB38 006EDC8F 006EDD7F 006EDDAF 006EDE26 006EDE50 006EDE70 006EDE80 006EDEAB 006EDED8 006EDF05 006EDF74 006EDFBD 006EE03A 006EE0CC 006EE0F1 006EE196 006EE1BF 006EE1DF 006EE28C 006EE2FC`
分级 [静态推断]；全表 `EVIDENCE/w174_classify_cfg.tsv`（`cls=c` 行）。注意：43 处中 **32 处属 TEAM（StepCompleted），0 处属 OBJ**；OBJ 侧无条件置位 0 处——支持台账「ObjectClass 脏标记只在状态变更时置 1」。

## 给审计员的核心数字 + 复算方法

1. **179 写点**：通道A `capstone(skipdata=True)` 解全 `.text`，取 `op0.type==MEM && op0.mem.disp==0x80 && op0.size==1 && mnemonic=='mov'`；通道B 扫原始字节 `80 00 00 00` 反推 C6/88 mod=10 编码并逐点验指令边界。脚本 `work/w174_scan.py`。
2. **83 函数**：对 179 写点用 M3 区间包含（函数入口集 = atlas entry ∪ 全 .text `call rel32` 目标，共 12945 个），脚本 `work/w174_attrib_analysis.py`。
3. **写值分布 147/14/18**：对 179 写点读 `op1`（imm→值 / reg→寄存器名），脚本 `work/w174_scan.py` → `w174_writes.tsv`。

## 与台账关系

否证 §924-3/§925-2「179 处写点全为 ObjectClass 脏标记」的外延；`[+0x80]=脏标记` 本身在 ObjectClass 侧仍成立（§925-2 两处上下文已复核）。详见 `DISAGREE.md`。
