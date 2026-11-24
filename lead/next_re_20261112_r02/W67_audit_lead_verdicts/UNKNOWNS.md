# UNKNOWNS · W67 审计卡（2026-11-14 01:02 收盒）

1. **"71 s" 口径** [未核-口径]：`LEAD_VERIFY_W63.md:22` / `RUNLOG.md:617` 的「冻结在 M3（47 samples / 71 s）」——47 个冻结样本**精确实测吻合**；冻结期 t=0→69.8 s（末样本 69.8 s），"71 s" 疑为含收尾拆除的窗口时长，口径未在文中定义。
2. **指令级计数未复算** [未核]：W57 的 1,394,120 条指令边界 / 99.9984% / 135,330 写操作数 / 3,268 批量写点 / 37 条门控页绝对写 / 4,005,210 anchored 解码；W58 的 `0x6EB` 立即数 8 次（0x6EA 7 / 0x6EC 7）、STATIC 9 个 / SS_BLACKFRAME 3 个、`0x622650 → FindResource(RT_DIALOG,5,148)` 链；W60 的 835 断言分组、145 CRLF / 0 bare LF、"仅第 55 行变"。均需 capstone/解析器级复算，本轮（字节级手段）未做。相关结论有互相独立的双实现支撑，风险低。
3. **CFB_COMPARE_TABLE.md 行数 vs 「逐 15 个 stream」** [未核]：数据行粗计 17 行，可能含 CONTENTS/汇总行；未逐行归类，未判「15」是否精确。
4. **锁历史** [未核]：W55B 的「23:13:18 归还锁」无法从盘面复核（`.game_instance.lock` 只反映最后一次 23:39:42.496，见 FINALIZE.lock_final；**本卡未读未取该锁**）。锁文件路径已定位：`next_re_20261112_r02\.game_instance.lock`。
5. **ts_crc_hash** [未核]：`ts_crc_hash("LOCAL.MIX")=0xA8548FD9`、`ts_crc_hash("BATTLE.INI")=0x889C5B31` 未独立复算（依赖 W64b EVIDENCE\S6_id_resolution_stdout.txt 自述）。
6. **W55B 的 A2 侧 CONTENTS 长度** [部分核]：1,381,318（A1）已由 CFB 表佐证；1,377,434（A2）未直读。
7. **W60「与 W27 D2 逐字节一致」** [未核]：SHA `369592f0…` 有 W60 产物佐证，但与 W27 当年诊断变体的比对未复核（依赖 INPLACE2 PASS + W27 历史）。
8. **W61 repoint 更省法** [未核]：THIRD_BADGE_ROUTE.md 提及的替代补丁法未复核。
9. **W63「原始件已另存」位置** [未核]：241 B 孤儿 .bak 的"另存"位置未追（还原后 sha 9f804531… 与 pristine 吻合，无实际影响）。
10. **0x6041FD 语义** [已解释，非缺陷]：RULING_C §5 引「tooltip STT:CampaignAnimTutorial（0x6041FD）」——串本体 VA=0x83567C（恰 1 次）；0x6041FD 是返回该指针的函数内地址（0x604206 `mov eax,0x83567C`）。措辞可更精确，不计缺陷。
11. **审计期间盘面在动** [环境事实]：RUNLOG 00:12→00:53 从 650 行增至 783 行（新增 §18–§23：GLM 并发限额更正、W65/W68b/W70 增量、W68 双写归属、W69 污染处置）；新 REVIEW 件（LEAD_VERIFY_W65/W68B/W70、CRITERIA_SPEC_V2）不在本卡范围。RUNLOG §19.4 提到的「W67 前一 GLM 实例」即**本卡**（其看到的 w67_verify1.py/_w67_verify1_out.txt 是本卡 00:20–00:25 的产物；"没写结论文件"系 Lead 在我收盒前查看）。后续审计者请以本 FINDINGS.md 为准，避免与 zcode-runner 的并行 W67 重复登记。
12. **W70 §20 的 battle_cnt 14/15 解释** [未核]：14+1=15（BATTLEMD98.INI 旧包 1 条）逻辑自洽但未独立复核，且不在本卡范围。
13. **W55b CONTENTS 块结构 10 次遍历全败** [未核]：引用自 W54 §4.4 与 analysis.json `structure_parsed=False`，未独立重放。
