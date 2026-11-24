# S13-K4 UNKNOWNS

## U1 — DoD 120/240 (50%) 不可达（按允许证明类型穷举）
本卡穷举 193 个非已证 S13 行，只有 13 行能在 4 类允许证明下升为 `[已证]`（6 B8 桩 + 7 行为级）。
其余 172 行为占位名（104 Class::slotN / 40 vslotN / 27 sub_ / 1 other），按 R14_COMMON §8.1 ⑬（S11-K4 整卡 FAIL 教训）**禁止**以 `Class::slotN`/vslotN 当语义升级。
证据：EVIDENCE/exhaustive_survey.tsv（逐行分类 + first4_insns，纯 jmp thunk=0）；脚本 work/exhaustive_survey.py。
即使并入 S13-K2 的 8 行，全 S13 proved 上限 = 47+8+13 = 68/240 = 28.33%，距 120 差 52。如实报，不凑数。

## U2 — 卡面 55 与 coverage.tsv 47 的差 8（S13-K2 未并入）
盘上 coverage.tsv 实测 `[已证]`=47；卡面 55 含 S13-K2 未并入的 8 行 delta（实测这 8 行在 coverage.tsv 仍 [未证]）。
本卡以 47 为 disk 真值，不重取 K2 的 8 行（避免双算）。合并员并入 K2 后应为 55，再并入本卡 13 → 68。

## U3 — 104 Class::slotN / 40 vslotN 的语义
这些行的 name 是占位槽号（如 `WeaponTypeClass::slot13`、`?$DynamicVectorClass::PAVBom::vslot3`），函数体为真实代码但需逐个方法级行为判定才能定名；
本卡未在允许证明类型下取得其语义的字节证据，保持原级。此类不是「没测=0」，而是按 ⑬ 明确禁止的升级路径。

## U4 — 27 sub_ 无名字
`sub_XXXXXXXX` 既非真名也无语义，不计 named(S)；本卡未取得可定名的字节证据（弱语义调用图信号不足），保持原级。

## U5 — 7 行为级行的字段偏移细节依赖 S13-K1 证据
本卡 behavioral7.txt 独立复算键串/调用/vptr 写；字段偏移表（+0x22F..+0x2F7 等）引用 S13-K1/ini_fields.tsv 与 ctor_candidates_detail.txt（同名卡已证）。
本卡未重新逐键核对 width/offset（非本卡证明点），故结论表的「结论」列只写本卡自证的键串/调用事实。
