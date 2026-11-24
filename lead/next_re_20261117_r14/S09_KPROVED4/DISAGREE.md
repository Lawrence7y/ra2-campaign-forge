# S09-KPROVED4 · DISAGREE

## D1 · `006A7D70` 主台账占位名（非语义冲突，不改名）
开工 grep `lead\GOAL_THREE_TARGETS_20261018.md` 命中 1 处：`:17364 | 0x006a8056 | FUN_006a7d70 | 783`，是 Ghidra 自动生成的 `FUN_006a7d70` 占位名（与 `sub_XXXXXXXX` 同类），并非语义命名。本卡 delta 用 RTTI 归属名 `SidebarClass::slot54`（全 1214 表枚举命中 1 张 `.?AVSidebarClass@@` slot54，CHD 归 SidebarClass），不构成命名冲突，无需按错源⑱改它名。已记录，未写台账。

## D2 · ③b 基率与 K3 卡口径差异（见 UNKNOWNS U1）
K3 卡（S09_KPROVED3）自报 strict 6.20%/loose 6.36%，本卡 19.55%/22.89%。差异源于检测器覆盖面（本卡实现 S2 循环与 S4 形状，K3 审计自陈这两档全池 0）。两卡均报基率而非 ②∧④ 入选率，符合 M3；本卡数值逐行可复算（`BASELINE_3B_FEATURES.tsv`）。不判为矛盾，口径并列。

## D3 · 细则#1 行保留意见（见 UNKNOWNS U2）
`00557830`、`00723EC0` 按 D-42 细则#1 归 ③b①；若审计只认四硬档（跳表/错误码/形状/循环），这两行应剔除。与 K3 审计对其 `004AAD30`（同类细则#1）所标保留意见一致。本卡按细则#1 明示并逐条给各闸异动作证据（M4），留待 Lead 裁定。

## D4 · 类名覆盖原盘面占位名（预期变更，非冲突）
8 行原 coverage 名为占位式 `ControlClass/ListClass/MapClass/...::slotNN`。本卡 delta 的 name 栏按 M1/错源⑯归共同基类（如 `00565B00` 原 `MouseClass::slot23` → `MapClass::slot23`，8 表同槽归 MapClass；`00557830` 原 `ColorListClass::slot31` → `ListClass::slot31`）。属合并员预期并入的改名，非与既有语义名冲突（开工 grep 主台账除 D1 占位名外 0 命中）。
