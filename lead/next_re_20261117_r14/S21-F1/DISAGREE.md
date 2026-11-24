# S21-F1 DISAGREE — 与旧文档/台账冲突

| # | 旧来源（节号/行） | 旧表述 | 本卡实测 | 裁定 |
|---|---|---|---|---|
| D1 | coverage.tsv 行 `0046CCD0`（classification_trace.tsv） | `CampaignClass::slot25 … 槽语义未证`，grade `[静态推断]` | `0x46CCD0` 是战役段读取函数（读 CD/FinalMovie/Scenario/DebugOnly/Description），调用点 0x46CF65 `[vptr+0x64]`；本卡判 `[已证]` | 升级，见 coverage_delta.tsv；旧级来自「槽语义未证」，现由控制流+键名实证闭合 |
| D2 | coverage.tsv 行 `0046D070` | `CampaignClass::slot12 … 槽语义未证` `[静态推断]` | `0x46D070 = mov eax,0x3a0; ret` = GetSize；与 new(0x3a0)@0x46CE97 双证 | 升级 `[已证]`；本卡反复用「槽语义未证」旧级不应再沿用 |
| D3 | coverage.tsv 行 `0052CB90` | `调用图邻居 1 票 … （弱信号）` `[未证]` | 实测 BATTLEMD*.INI 通配枚举函数，4 个调用点，IAT 实证 | 升级 `[已证]` |
| D4 | coverage.tsv 行 `0046D330`（当时归 S22 / sub_） | `无可用静态信号；S22 兜底桶` `[未证]`，subsystem S22 | 实测写 vptr `0x7e4aac`（CampaignScoreClass vtable）+ 初始化全局；RTTI TD 0x81B2C8 | S22→S21 并升 `[已证]`；S22 是「未定类」桶不得参与覆盖结论（R14_COMMON §9） |
| D5 | R14_COMMON §3「键冲突判据=战役名 `_stricmp(obj+0x24, [Battles] 值)`」 | 已证事实 | 本卡复现一致（0x46CE73/0x46CCAC），并补出对象是 CampaignClass（RTTI 实测） | **一致**，无冲突；记此以证本卡未推翻 §3 |
| D6 | a3_campaign_map_spec.md §5.1 行 156-158 | BATTLEMD 注册机制条目 | 完全一致（0x52CBA0 FindFirstFileA / 0x52CCCD 回退 / 0x46CE10 按名归并） | **一致**，仅作线索核对，本卡结论独立重取证 |
| D7 | kb/30_ini_subsystem.md §6.4 | CCINIClass 尺寸 0x58 双路实证（new(0x58)@0x52CBFB） | 本卡在 0x52CBFB 复现 `push 0x58; call 0x7c8e17`，且 0x52CC0B..0x52CC36 构造链一致 | **一致**，无冲突 |
| D8 | kb/10_map_triggers.md §3 | TEventClass+0x2C 事件 ID，合法下界 0x0D，两级表派发 | 本卡未重做（S15 已入账），仅引用其结论 | **一致**（复用），本卡不产出 S15 新结论 |

## 声明
- 本卡未改台账、未改 PANEL、未改 `coverage.tsv`，只交 `coverage_delta.tsv`（append 由 M 卡串行执行）。
- D1–D4 为 grade/subsystem 升级建议，不是对旧卡事实的否定——旧级出自「槽语义未证」的保守默认，本卡补了实证。
