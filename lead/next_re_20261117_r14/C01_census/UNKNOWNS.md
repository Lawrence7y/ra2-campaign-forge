# C01 · UNKNOWNS（未决项）— FIX round

引用节号：R13_COMMON.md §1/§6/§7；PLAN_R14_SUSTAINED.md §1/§2；
本卡 `_audit\VERDICT.md` §二/§四/§六。

## U1 · 493 个 `[未证]` 函数无独立证据（原 503，↓10）
- 本片 1292 函数中 493 个（38.2%）仅有地址段弱先验，无 YRpp/KB/RTTI/字符串/导入/已知邻接证据。
- 减少 10 的原因：FIX round 修复 YRpp 解析器前向声明泄漏后，10 个原 `[未证]` 行获得正确具名 → 升 `[已证]`/`[静态推断]`。
- 级别严格保持 `[未证]`（R13 §6-9），未把弱先验写成 `[已证]`。
- 建议 P1：对 S02/S22 段用 YRpp 全量地址表二次配对；对容器段用调用者类上下文回填。

## U2 · YRpp 解析器前向声明泄漏（已修复）
- 根因：原 `CLASS_RE` 只匹配 `class X;` / `class X :`，不匹配 `class X {` 或 `class X` 单独一行（下一行 `{`），
  导致 `class VocClass;` / `class TechnoClass;` / `class HouseClass;` 等前向声明残留进 cur_class，
  后续真类定义（AudioIDXData / AudioController / AudioStream / Audio / BombListClass / BounceClass / BaseClass）未覆盖。
- 影响 24 行 name（详见 FIX_REPORT.md 必改 2），另 6 行 `sub_XXXXXX` 占位名降级。
- 修复：`work/extract_yrpp_names.py` 的 CLASS_RE 加 `\{|$` 分支、跳过 `enum class`、find_decl 跳过 `:` 开头的初始化列表行；
  0x40E320 加显式 override（GenericNode 优先于模板 Node）。
- 验证：`work/verify_name_fixes.py` 30/30 OK；`work/verify_coverage_fix.py` 24/24 OK（EVIDENCE/verify_name_fixes.txt、verify_coverage_fix.txt）。
- 残留：模板类 RTTI 名可读性差（`?$VectorClass::PAVBombClass::::`），仅字面，归属正确。

## U3 · KB 名称抽取器 — 仅 1 个 KB-only `[已证]` 成立（更正）
- 原 UNKNOWNS 写「余 3 个 KB-only 保留 `[已证]`」**错**。
- 审计实测（`_audit\VERDICT.md` §六必改 3）：KB-only 具名函数仅 **1 个**成立：`0x00410B90 WriteINI`（KB11:799 已核）。
- 另 2 个裸类名（0x0040E4A0 CCINIClass、0x00410380 AbstractClass）已降 `[静态推断]`；
  0x00410A60 Name 亦降（其 YRpp 名 AbsType.cpp 证据不足以独立定名）。
- `work/extract_kb_names.py` 可能抓到偶然 token，所有 KB-only `[已证]` 建议 P1 逐条人工复核。

## U4 · 已知例 0x4824D4 的跳转类型是短跳（EB 0A），非 rel32（保留）
- `work/verify_gaps.py`：0x4824C8 处 `EB 0A` → 0x4824D4，是 jmp rel8；E8/E9 字节扫无命中，capstone 命中。
- 该地址在本片范围外，未入本卡 atlas_gaps.tsv。
- FIX round 后本卡 atlas_gaps 分双通道：`call-jmp`(2) + `orphan`(7)，均不依赖 0x4824D4。

## U5 · atlas 空洞为函数簇，非单点（FIX 后扩展）
- 0x42E1C0 的调用点 0x42E13E 自身在空洞 (0x42E085,0x42E410) 内。
- FIX round 加建前向通道（`work/orphan_forward.py`），在片内又找到 5 个零引用孤儿入口
  （0x4093C0 / 0x412280 / 0x427850 / 0x42E990 / 0x435B50，全 16B 对齐 + 序言 + 前驱 ret），
  另独立复核 0x433060（med，ret+nop padding 后 sub-esp 序言）与 0x432BF0（low，naked helper）。
- atlas_gaps.tsv 现在为 9 行：下界 7（高置信：2 call-jmp + 5 orphan），上界 9（含 2 候选）。
- 建议 P1 对这些整段重新建函数边界（不依赖 atlas）。

## U6 · high 置信占比 7.43%（原 7.89%，已更正）
- 96/1292 达 `[已证]`，703 `[静态推断]`，493 `[未证]`。
- 下降原因：6 行 `sub_XXXXXX` 占位名由 `[已证]` 降 `[静态推断]`（R13 §6-9 / 审计 §四）。
- 这是保守分级的结果：KB22(19) + YRpp 具名(排除占位) + KB 具名方法(1) 之外一律不写 `[已证]`。
- 提高占比需 P1 逐函数人工取证，非本 P0 普查卡职责。
