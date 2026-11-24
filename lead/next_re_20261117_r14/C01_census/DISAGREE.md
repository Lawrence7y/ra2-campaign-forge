# C01 · DISAGREE（分歧与不一致）

引用节号：R13_COMMON.md §1（作废索引）/§2；PLAN_R14_SUSTAINED.md §1；台账 `lead\GOAL_THREE_TARGETS_20261018.md` §675/§911。

## D1 · 与台账 §675 的关系（0x0043BCF0）
- 台账 §675 曾称 0x0043BCF0 是「BuildingClass 构造函数」，R13 §1 作废索引已判错，由台账 §911 覆盖。
- 本卡未引用 §675 结论。coverage_delta.tsv 中 0x0043BCF0 = `sub_0043BCF0` / S19 / `[静态推断]`
  （依据：callees 0x406060、0x405c00 为 YRpp 具名音频方法，调用图传播；证据 EVIDENCE/evidence_raw.json#0043BCF0）。
- 本卡分级为 `[静态推断]` 而非 `[已证]`，未把「构造函数」猜测写成任何级别。
- 需 P1 用台账 §911 的五条功能性证据（两次 DVC::Delete / 两次 CRT free / vptr 回退 / 无返回值 / n_callers=1）
  复核本卡的 S19 归属——「§675 错」不等于「S19 对」，两者是不同命题（R13 §6-18：等价形式也要查）。

## D2 · 与 R13 §2 的关系（0x0043F180）
- R13 §2 已证 0x0043F180 = BuildingClass 主表 slot 73（`+0x124`），mode 0=摘链 / 1&3=挂链 / 2=`[未证]`。
- 本卡 coverage_delta.tsv 给 `BuildingClass::vslot73` / S12 / `[静态推断]`（RTTI 虚表归属通道）。
- **不冲突**：S12（生产/经济/建造放置）与 slot 73 的 grid Limbo/Unlimbo 语义同向；
  本卡按 P0 自动证据保守记 `[静态推断]`，未擅自升级为 `[已证]`（R13 §6-9）。
- 建议书记员/合并员：R13 §2 的 `[已证]` 语义由 P1 专卡回填台账时再覆盖本行，不在 P0 delta 内改判。

## D3 · 与「jmp rel32」口径的字面差异（0x4824D4）
- 卡正文将 0x4824D4 列为「扫 call/jmp rel32 目标」的已知例。
- 本卡实测（EVIDENCE/gap_verification.txt）：该入口由 0x4824C8 的 `EB 0A`（jmp rel8 短跳）命中，
  E8/E9 字节扫无命中；capstone 的 `jmp 0x...` 目标扫命中。
- 这不是结论分歧，而是「rel32」字面过窄；本卡判定以 capstone 目标扫为准，并在 UNKNOWNS.md U4 记录。

## D4 · 无其他与作废索引的冲突
- 已逐条核对 R13 §1 的 20 条作废项：落在本片地址范围的只有 §675（→D1）与 §2 相关项（→D2）。
  其余（0x55B8F0 / 0x617641 / 0x61CC5C / 0x67D300 / 0x485020 / 0x482854 等）均在 0x00456DFC 之外，
  本卡未引用、未归类，不构成分歧。
- 未使用「最近 E8/E9 目标」「最大函数=热点」「无调用者=死代码」等被禁启发式（R13 §6-7/8）。
