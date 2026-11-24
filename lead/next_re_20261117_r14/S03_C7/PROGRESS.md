# S03-C7 PROGRESS（最终）

- 卡号 S03-C7｜开工 2026-11-19T16:59+08｜目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（前缀 73201CC0/后缀 F67476，现场复算）。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未建 venv / 未 pip install / 未改游戏文件 / 未改 COVERAGE/台账/COMMON/其它卡目录 / 未真机。骨架已于开工首步落盘（≥5 行）。
- 已读：R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条/§8.7 九条；D-40/41/42（含细则#1/2/3）；SURVEY_RING24\PROGRESS.md；C4/C5/C6 delta + M43/M44 MERGE_LOG + SEMFIX_SLOTS2。
- 写域：`S03_C7\`（本目录）+ `_ghidra\S03_C7\`（未用，-noanalysis）。

## 1. 行源与排除（可复算）
- S03 A 集合总行数 = **31**（SURVEY_RING24 MATRIX；`classification.tsv` has4_strict=1 实测 31）。
- 排除 23 = C4(7) ∪ C5(5) ∪ C6(7) ∪ 黑名单 4（00431F10/00473AE0/0047AF10/0065D240）；M43 的 2 行（00431F70/004322A0）+ SEMFIX 的 4 行（0047AE10/0065CDD0/0065D0D0/0065D190）均在 C6 内，无额外扣减。31−23=**8 行作业面**：004325C0 / 00473C00 / 00473CE0 / 00473FC0 / 0047AAB0 / 00631D30 / 0065CCA0 / 0065D1F0。
- 00432050 在 C6 排除集内（被审计退回），另作独立复核，不占 8 行、不进 delta。

## 2. 四环逐行（明细见 EVIDENCE/THREE_B_DETERMINATION.md）
- ② 全持有表 + ⑯：全部 8 行 RTTI 链读通、fail-closed 无命中失败；全表枚举见 `EVIDENCE/rtti_all_holders.json`。016 归基类级三行：004325C0→BufferIOFileClass、0065D1F0→RawFileClass、00631D30→Pipe；其余各行单表/最基已逐行声明。
- ③b：3 行成立（004325C0=①四路互斥闸、0065CCA0=②Close 句柄失效约定、0065D1F0=②DOS 时间打包返回）；5 行判 ③a（00473C00/00473CE0/00473FC0/0047AAB0/00631D30），理由进 UNKNOWNS U2–U6。
- ④：8/8 站点骨架成立（全 `.text` 1,392,592 指令 / 68,253 E8 边界扫描，site+5+rel32==entry、体外、非自环）；逐行见 `EVIDENCE/direct_sites.json`。
- 偏移：delta 第 4 列所有 `+0xNN` 均为入口相对，且逐字与 `EVIDENCE/dis_*.txt`、`ANCHOR_*.txt` 同一个数（判据5）。

## 3. 00432050 独立复核（任务专项）
- 审计判「实为缓冲写非缓冲读」；本卡三条独立字节证据复核**成立**（+0x228 call 0x65CDD0→WriteFile 体内 +0x052 call [7E11A0]；+0x125 memmove dst=内部缓冲；+0x04F mode=1 报错码 13 + 脏标）。正确 ③b④ 写语义已落 `EVIDENCE/REPROCESS_00432050.md`；不入本卡 delta（守 8 行）。见 DISAGREE D1。

## 4. 核心数字
- **8 行中四环齐全数 = 3**（004325C0 / 0065CCA0 / 0065D1F0）。
- **S03 A 集合总行数 = 31**。
- **③b 基率**（池=盘上 S03 `[静态推断]` ∩ 有 CFG extent = 91 行；seed 20261119，2000 次取 8，不放回）：**strict** K=18/91=19.78%、E[8]=1.5824、MC=1.5910；**loose** K=32/91=35.16%、E[8]=2.8132、MC=2.8345。操作化：`strict` ③b①只认跳表；`loose` ③b①加 D-42 细则#1（≥3 互斥闸）；两档共用 ③b②③④ 检测器。`K=8×p` 为恒等式，不作校验（判据3）。
- direct 站点逐行：27/26/42/14/2/6/9/1；delta 行数=3=自报可并入行数（判据7）。

## 5. 交付物
`PROGRESS.md`(≤60行) / `UNKNOWNS.md`(U1–U9) / `DISAGREE.md`(D1–D4) / `coverage_delta.tsv`(3 行) / `EVIDENCE\`(rtti_all_holders.json、rtti_inherit_extents.json、direct_sites.json、baselines.json、dis_*.txt×9、ANCHOR_*.txt×3、THREE_B_DETERMINATION.md、REPROCESS_00432050.md) / `work\`(common/scan_rtti/dump_rtti_chain/dump_funcs/scan_sites/baselines/dump_callees/resolve_iat/dbg.py + 中间 json)。

## 6. 自核（§8.7 九条 + M1–M8）
判据1 全表枚举 ✓ / 判据2 ②栏类名与 name 类一致 ✓ / 判据3 恒等式未冒用 ✓ / 判据4 报 ③b 基率未用②∧④ ✓ / 判据5 偏移与 EVIDENCE 同源 ✓ / 判据6 004325C0 四路动作各异 ✓ / 判据7 自报 3=delta 3 ✓ / 判据8 语义栏 3 行全文无「未证/未定/弱信号/线索」✓ / 判据9 不适用。M1–M8 逐条满足。
