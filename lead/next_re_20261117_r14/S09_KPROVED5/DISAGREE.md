# S09-KPROVED5 DISAGREE

## D1 · 「已并入 22 行」与 4 张 prior delta 的 27 entry
**分歧**：任务给定已并入 22 行；4 张 prior coverage_delta.tsv 合计 27 entry。
**裁定**：非矛盾——27 是「提交过的 delta 行」，22 是其中真正落盘为 `[已证]` 的行。以 `COVERAGE\coverage.tsv` 现态 grade 逐项交叉：22 个 `[已证]`、5 个 `[静态推断]`（见 UNKNOWNS U1）。
**影响**：本卡取更严口径，剔除全部 27 个 prior-delta entry（超集），故不会与任何 prior 提交重复。无异议残留。

## D2 · `004F4480` / `004F4320` 的 ② 共同基类判为 GScreenClass
**分歧**：prior S09 卡（KPROVED3/4）对多表同 slot 行归 DisplayClass / MapClass / TabClass 等，本卡对这两行归 **GScreenClass**。
**裁定**：按 MSVC `RTTIClassHierarchyDescriptor.BaseClassArray` 实测（index 0 为类自身，index 1+ 为全部基类，逐字读 TD+8）：
- `004F4480` slot15 命中 9 张表（Display/GScreen/Map/Mouse/Power/Radar/Scroll/Sidebar/Tab）， deepest common ancestor = **GScreenClass**；
- `004F4320` slot9 同样 9 张表，deepest common = **GScreenClass**。
按错源⑯/M1（2+ 表同 slot 归基类级）应取 GScreenClass；name 栏同步写 `GScreenClass::slotN`（M2 合规）。
证据：`work/fix_attrib.py`、`EVIDENCE/CLASS_ATTRIB8.tsv`、`EVIDENCE/VTABLES_ALL8.tsv`。**无异议残留**；如审计坚持须按某 prior 命名习惯改用 DisplayClass，属命名口径非四环事实。

## D3 · `0063F730` PowerClass::slot7 的 ③b 档
**分歧**：检测器 S4（≥10 字段写）将其标 strict③b。
**裁定**：人工复核反汇编（`EVIDENCE/DISASM_0063F730.txt`）：该函数无分支、纯字段清 0/置 -1（D-42 ③a「清零+置默认值」），无 ≥2 vt 写、无对象大小断言、无可证伪闸。故判 **③a、不成立**，不进 delta。检测器假阳性已记录于 UNKNOWNS U3。**无异议残留**。

## D4 · 细则#1 的边际判定（`006A5BF0` / `0069DE00`）
**分歧**：两行 S6 检测器标 strict，但人工复核后不取。
**裁定**：`006A5BF0` 全 24 闸汇入同一 free 调用 0x7c8b3d（仅参数不同）；`0069DE00` 与已黑名单 `0069DEB0` 同型（五模式汇入 call 0x4aed70）。均违 D-42 细则#1「各闸动作不同」与 §8.7 判据6，判 ③a。**无异议残留**。

## D5 · S4「内存形状断言」与构造器薄壳的分界
**说明**：本卡 8 行中无构造器，③b 档位为 ③b①（互斥闸链/switch 状）与 ③b④（完整有界 I/O 循环），均不含构造器形状断言，规避 §8.6 条3「构造器薄壳算 ③a」与 D-42 细则#2 的争议。
