# S09-KPROVED · DISAGREE（与盘面 / 他卡口径的分歧与处置）

## D1 · RTTI 读出的类 vs coverage 既有 name（多虚表条目）
4 行在 `classification.rtti_classes` 含 2 个类，且本卡所读 vt 的类与盘面 name 前缀不一致：
- 004AAE90：读 vt7E1964[46]→`.?AVMouseClass@@`；盘面 `TabClass::slot46`。
- 004AB9B0：读 vt7E1964[48]→`.?AVMouseClass@@`；盘面 `DisplayClass::LMBUp`。
- 004ACE70：读 vt7E1964[32]→`.?AVMouseClass@@`；盘面 `TabClass::slot32`。
- 006ABD30：读 vt7E1964[34]→`.?AVMouseClass@@`；盘面 `SidebarClass::Tooltip`。
**处置**：同一 entry 出现在多张类虚表（错源 ⑯），单一 vt 不足以定「唯一类属」。② 环只需「某张 RTTI 可解表槽值＝entry」即成立，本卡已证；但不据单一 vt 改名（会引入错源 ④「类名挂错」）。delta 保留 coverage 既有 name；差异记录于此，交由命名卡/审计按多表全集裁定。

## D2 · 004AB9B0 的 ③b 档位（守卫链 vs 跳表/循环）
本卡将 004AB9B0 判 ③b①（多路守卫链，D-42 操作化细则#1）。严格字节探测器（`baseline.py` 的 P1/P2/P4）对该行返回 0（无跳表/循环/-1 哨兵），仅 P3 多常量模式（`baseline_p3.py`）命中。若审计坚持 ③b① 必须为真跳表、不接受「多路守卫链」，则本行不成立 ⇒ 出 delta、四环齐全数 8→7。已在 UNKNOWNS U2 标注为最弱一环。

## D3 · A 集合计数口径（103 与 129）
SURVEY-RING24 MATRIX 报 S09 A=103。本卡独立复算：S09 `has4_strict=1` 原始 **129**，其中 **26** 行 `has2_rtti=0`（无 ②），故 A=②∧④=**103**。与 SURVEY 一致，但明确区分「strict4 原始 129」与「A 集 103」两个量纲，避免把 129 误当 A。脚本 `work/count_A.py`。

## D4 · 随机基线数值随 ③b 操作化浮动
正文主报 0.587（含 P3 多路守卫档，与 8 行人工口径一致）；严格档 0.549。两档均给出，不单报一个「精确值」冒充唯一口径。均用行采样（seed 20261119, 2000 次, 池 N=629），未用「随机 VA 命中 target」地址算术口径（§8.6 条4）。

## D5 · grade 升 [已证] 的边界
8 行均四环齐全（D-40 最小环集），故 grade 由 `[静态推断]` 升 `[已证]`。但依错源 ⑬「入口已证≠语义已证」，本卡不据 ②/④ 背书 docs 语义名（LMBUp/Tooltip）；one_line_semantics 只写字节可核的 ② vt:slot / ③b 现场 / ④ 站点。
