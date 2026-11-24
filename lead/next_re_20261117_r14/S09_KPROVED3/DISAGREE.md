# S09-KPROVED3 · DISAGREE.md

卡号 S09-KPROVED3。记录与既有 coverage.tsv / 上一张卡口径的差异及裁决依据。

## D1 · 既有 `name` 多写为派生类，本卡按 L1/⑯ 改归基类
- S09 coverage/A 表把这 6 行记为 `TabClass::slot42/41/38/39`、`TabClass::slot44`、`TabClass::slot49`；但全 1214 张 RTTI 可解表枚举显示同一 entry 被多张派生类表以**同一 slot** 持有（004A8960/9840/9DD0/A050 各 7 张，004AAD20/AD30 各 5 张），trace 见 `EVIDENCE\VTABLES_ALL8.tsv`；类层次链见 `EVIDENCE\CLASS_ATTRIB.tsv`。
- 按 R14_COMMON §8.1 错源⑯ 与 L1，归属提升到最派生共同基类 `DisplayClass`；0048E620 同理从 `ControlClass`/`ToggleClass`/`SelectClass` 三表归 `ControlClass`。delta 的 `name` 列已同步改为 `DisplayClass::slotNN` / `ControlClass::slotNN`，保证 ② 栏类名与 name 栏一致（L2）。

## D2 · 基线口径：本卡报 ③b 基率，不报 ②∧④ 入选率
- 上一张 S09 卡把 103/629=16.375% 的 A 率当“基线”；按 L3 那是挑选谓词本身，不是 ③b 基率。
- 本卡 seed 20261119、2000 次、同 S09 内随机取 8 行：strict 39/629=6.2003%，loose 40/629=6.3593%；K=0.5035/0.5175，mean=0.0629375/0.0646875。K=8×mean 只是恒等式，不作校验。

## D3 · 004A8960 的自动 detector 曾误报，已人工全量反汇编覆盖
- 早期过宽 error-return 规则因 `call 0x7C8E17` 后的 NULL 检查将其标 strict；逐条打完 176 条指令后确认是两次「free 旧对象→new 0x30→复制坐标」的机械模式，非 D-42③b②，也非细则#1 的互斥多模闸。收紧 detector 后该行 strict/loose 均归 0；本卡不并入。

## D4 · 004AAD30 为细则#1 级边际
- 该行有 7 道互斥闸且 helper 调用各异，满足 D-42 细则#1；但它没有物理跳表、完整循环、错误码或形状断言。若审计收紧为只认四档硬条件，应首先回退此行。delta 语义栏已标「细则#1级」。

## D5 · 指令总数与上一张卡不同，E8 边界数一致
- 本卡全 `.text` VirtualSize capstone skipdata 得 1,392,592 条指令 / 68,253 个 E8@边界，与 SURVEY_RING24 一致；上一张 S09 卡自报 1,394,186 条指令，但 E8@边界同为 68,253。差异来自 skipdata 切分粒度，不影响任何交付站点；所有站点都落在 100% `.text` 扫描覆盖内。

## D6 · 命名冲突检查
- 开工前已 grep `lead\GOAL_THREE_TARGETS_20261018.md` 中 8 个候选 entry，0 命中；本卡未声称新发现，只按 RTTI/类层次修正归属名，未写台账、未改 coverage.tsv。
