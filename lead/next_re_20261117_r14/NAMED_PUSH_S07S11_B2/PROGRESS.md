# PROGRESS — NAMED_PUSH_S07S11_B2

候选：S07 4 行 + S11 11 行 = 15 行。每 5 行追加。

## 骨架（0 行）
- 目录已建、骨架已写、candidates.json 已落盘
- 候选筛选已复算：S07 named 22 / 伪名 0 / B1 18 / 剩 4；S11 named 29 / 伪名 0 / B1 18 / 剩 11
- 二进制 SHA-256 现场复核一致；core.py（PE+capstone skipdata+RTTI/虚表库）自检通过

## 5 行（S07 全 4 + S11 第 1 行）
已核：006DBE00 / 007BA8C0 / 007BBB90 / 007BBCF0 / 0069ED20
- 006DBE00 Tactical::slot6 → **四环齐全 [已证]**（主表 slot6 + 流写出 E_POINTER + 行外 ctor）
- 007BA8C0 BSurface::slot18 → 否（③ 全间接调用无可伪证站点）
- 007BBB90 / 007BBCF0 BSurface::slot2/slot3 → 否（③ 被调仅 {1,0} 布尔）
- 0069ED20 Ship::slot6 → 否（② 副表 off=0x18 thunk）
- EVIDENCE/ROW_*.txt 已逐行落盘

## 10 行（S11 第 2–6 行）
已核：0069EE30 / 0069FC10 / 00718100 / 007192F0 / 00719E30
- 0069EE30 Ship::slot0 → **四环齐全 [已证]**（主表 slot0 真 QI + 多值 HRESULT + ctor 0069EC50）
- 0069FC10 Ship::slot16 → 否（② 副表 off=4 thunk）
- 00718100 Teleport::slot17 → 否（② 副表 off=4 thunk）
- 007192F0 Teleport::slot16 → 否（② 副表 off=4 thunk）
- 00719E30 Teleport::slot0 → **四环齐全 [已证]**（主表 slot0 真 QI + ctor 00718000）
- EVIDENCE/ROW_*.txt 已逐行落盘

## 15 行（S11 第 7–11 行，收口）
已核：00719F80 / 00728AF0 / 0072A1C0 / 0075C7F0 / 0075C920
- 00719F80 Teleport::slot6 → 否（② 副表 off=0x18 thunk）
- 00728AF0 Tunnel::slot17 → 否（② 副表 off=4 thunk）
- 0072A1C0 Tunnel::slot35 → 否（② 副表 off=4 thunk；③ 单值 0）
- 0075C7F0 Walk::slot0 → **四环齐全 [已证]**（主表 slot0 真 QI + ctor 0075AA90）
- 0075C920 Walk::slot6 → 否（② 副表 off=0x18 thunk）

## 汇总（完成）
- rows_checked=15  ring2_ok=7  ring3b_ok=4  ring4_ok=15  all_four=4  rate=0.2667
- 产出 4 行 `[已证]`：006DBE00 / 0069EE30 / 00719E30 / 0075C7F0
- 两池耗尽：S07 22-18-4=0、S11 29-18-11=0
- delta.tsv / base_rate.tsv / 15×EVIDENCE / REPORT.md 全部落盘
