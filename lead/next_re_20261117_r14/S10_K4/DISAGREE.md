# S10-K4 · DISAGREE

| # | 对象 | 本卡结果与处置 | 依据 |
|---|---|---|---|
| D1 | K3 PROGRESS/19 行 “Mission default no-op handler” | **语义栏错**。19 行均返回 0x1C2=450；dispatch 把返回值写为 UpdateTimer.TimeLeft，实际是 450 帧轮询间隔，不是调用无效果。本卡 delta 全部改对，grade 仍 [已证]。 | `EVIDENCE/mission_rows_corrected.txt`；`EVIDENCE/probe_timer_dispatch.txt`；审计 `S10_K3/_audit/VERDICT.md` |
| D2 | K3 “10×NOP” | 物理连续 0x90 确为 10B，但审计按“到本 19 集合下一行”的 padding 口径实测 4 行不同：005B2E50=26B、005B2E90=58B、005B2EF0=26B、005B2F50=42B。本卡两种值都写入语义栏并列明口径，不再写单一 10×NOP。 | `EVIDENCE/mission_rows_corrected.txt`；`EVIDENCE/validate_delta.txt` |
| D3 | K3 U8 “0x1C2 含义未证” | **自设假否定，作废**。005B3086 已给 `esi=edi+0xC8`，005B30E2/store 写 `[esi+8]`；本卡标为 [已证]。 | `EVIDENCE/probe_timer_dispatch.txt` |
| D4 | K3 占位名 `Mission_DefaultHandler_XXXX` | 占位描述，不是真方法名。改用镜像内 mission 名表 + dispatch/vslot 双通道定名；共享槽按 S10-K1 约定取 Capture/Guard 为主要方法名。 | `EVIDENCE/probe_mission_strings.txt`；`EVIDENCE/dispatch_table.txt`；`EVIDENCE/vtable_mission.txt` |
| D5 | K3 23 行 delta vs 本卡 19 行 | 本卡只重交需更正语义/名称的 19 行；4 行 GetSize/WhatAmI 字节与语义无误、未重复入本 delta。合并员应同时保留 K3 那 4 行，避免 proved 少算 4。 | `EVIDENCE/validate_delta.txt`；K3 审计 VERDICT |
| D6 | 卡面 88/513 与门槛 257 | 现场读盘为 88/526 与 263；按纪律 9 用盘上值，不沿用卡面。 | `EVIDENCE/baseline_recompute.txt` |
| D7 | named 口径 | 严格 named(S) 排除 slotN 后为 29，L/宽松口径为 511；本卡验证用严格口径 29→48，不改 PANEL。 | `EVIDENCE/validate_delta.txt` |
| D8 | 仅凭 vtable 归属升级 | 未使用。每行都有 body 入口到 ret、dispatch 结果写回、mission id/name 双通道或 RTTI 第三锚；B8 形态不是升级理由。 | `EVIDENCE/task3_exhaustive.txt` |

## 纪律自检
- 写域仅本卡；未写台账、未改游戏文件、未 git commit、未用 Ghidra。
- 双通道至少一条不依赖 atlas entry+size：原始 PE 字节 + capstone + RTTI + dispatch/name 表。
