# S10-K7 · UNKNOWNS

| # | 项 | 状态 | 处置/下一步 |
|---|---|---|---|
| U1 | 同组四虚表写回的“第3条” | [未证] 不进 delta | 006B6C90、006B6EA0、006B6FA0、006B7F10 均写 007F3650/3634/362C/3624 同序；006B6C90/006B6EA0 有 new-then-call 构造证据，006B7F10 是 vtable slot 5（非构造器）。按窄卡只记 UNKNOWNS，不加行。 |
| U2 | S10_K5 U6 的“均无 RTTI/vtable anchor” | [已证] 分歧 | 至少本两条有 RTTI/vptr 写锚，见 DISAGREE D1；不据此推断 K4 另 63 字符串命中/15 个 sub_ 也可升。 |
| U3 | 004E0E80 字段语义（buffer/capacity/flags） | [静态推断] | [+4]/[+8]/[+0xC]/[+0xD] 的角色来自分支与 call 007C8E17 的字节解释；本卡只用 RTTI 定类、ctor 字节形态定角色，不把字段语义当独立第二命名源。 |
| U4 | 基线口径差 93 vs 92 | [已证] 已解释 | 第5列全部 S10 行 [已证]=93；S10∩atlas=92；差为表外 005B3740 已 [已证]。按审计卡面统一用 ∩atlas 92。 |
| U5 | 006B8140 盘上名 | [已证] 沿用 | 盘上已是 SpawnManagerClass::scalar_deleting_destructor；本卡只改 dtor body 006B7010，不重复写 006B8140。 |

## 复算入口
- work/baseline_recompute.py → EVIDENCE/baseline_recompute.json
- work/verify_closeout.py → EVIDENCE/CLOSEOUT_CHECKS.txt
- work/dump_targets.py、work/probe_rtti.py（失败布局探针保留）、work/probe_imm_hits.py、work/probe_ctor_candidates.py、work/probe_callers.py
