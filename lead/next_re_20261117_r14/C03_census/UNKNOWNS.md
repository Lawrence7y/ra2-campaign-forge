# C03 · UNKNOWNS（无法归类 / 低置信）

> 卡号 C03｜片：function_atlas.tsv 逻辑行 2585–3876（1292 函数）
> 全部行级细节见 `EVIDENCE/classification_trace.tsv`（source/conf/grade/name/sem/vt/strings/imp/vote 列）

## 1. 无法归类统计

- **source=none 共 151**：无任何 vtable 槽、无 YRpp/kb 名、无台账名、无源文件模块、无字符串、无亲戚投票、无导入 API。
- **其中真零证据 137**：连 `imp`/`strings`/`vote`/`self_strong`/`self_ledger`/`module`/`vt` 全空（verify_core.py 复算口径）。
- 其余 14 个 source=none 有弱信号（导入/字符串/亲戚投票）但未命中任何 Sxx 规则，仍归 S22 兜底。
- 另有 4 个 `vtable-unmapped`：有 vtable 槽但类名无法映射到 S01-S22（多为新模板/COM 接口）。

## 2. high 置信占比偏低的原因（33.1% vs C02 的 65.0%）

本片 S22 = 745（57.7%），其中 **589 个是 `T_VectorClass_*`/`T_DynamicVectorClass_*` 模板容器虚表槽**
（每个约 6–7 槽，均为 VectorClass/DynamicVectorClass 通用方法 Add/Remove/GetItem 等）。
按 C02 同款约定「容器 → S22，core=False」，这些既不计 high、语义也无法细分，
是 high 占比被摊薄的主因。剔除 S22 后，其余 547 个函数中 high = 427（78.1%），与 C02 同量级。

## 3. 待人工/后续 P1 主攻的缺口

| 子系统 | 缺口 | 建议 |
|---|---|---|
| S13 战斗 | 仅 4 个且全为 relay_vote（无 vtable/名证据） | 本片几乎不含 Weapon/Warhead/Bullet 本体（多在 C02 片），属地址分布所致，非遗漏 |
| S14 House/AI | 11 个全为 relay_vote（HouseClass/TeamClass 等仅以容器元素形式出现） | P1 主攻 S14 时按 HouseClass vtable 直接命名 |
| S15/S16/S17/S19/S21 | 各 1–2 个，证据弱 | 本片非这些子系统的主体区，无需本卡深挖 |
| S02/S04 | 各 1 个 | 异常守卫/INI 主体不在此片 |
| atlas 空洞 41 个 | 7 个 high(call) 目标（0x4B5630/0x4B56E0/0x4B5780/0x4B5830/0x4C2FC0/0x4E1340/0x4E2500） | 见 `atlas_gaps.tsv`；建议 P1 补建函数边界 |

## 4. 方法边界（ honesty notes ）

- 所有「一行语义」均为静态猜测并标 `[未证]`；本卡未做运行时验证，未升级任何语义为 [已证]。
- 置信度 high/med/low 只反映「归属 Sxx 的证据强度」，不代表语义正确。
- 容器模板元素类型（如 `T_VectorClass_PAVHouseClass__`）**不等于**槽所属子系统；本卡一律优先归 S22，避免误配。
- atlas 空洞用「函数区间包含」`owner()==None` 判据（纪律 17），未用 entry_at_or_before。
