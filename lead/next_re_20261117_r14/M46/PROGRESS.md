# M46 PROGRESS — S03_C7 3 行 + S09_KPROVED6 7 行共 10 行 [静态推断]→[已证]

卡号 M46｜合并员 agent-49｜2026-11-19。写域仅 COVERAGE\coverage.tsv、COVERAGE\PANEL.md、M46\、_hygiene\ M46 备份；其余只读，未 git commit / 未建 venv / 未 pip install。

## 并入结果
实际并入 N=10（S03 3 + S09 7），白名单严格 10 行。S09 审计 `S09_KPROVED6/_audit/VERDICT.md` 裁 FAIL：delta 8 行中 7 行成立可并入；006A5030 ③b 不成立（唯一回边是无边界 cmp 的 dec ebp/jne、体内无「读-判-写」，实质 ③a），黑名单整行不动。S03 3 行尚未经异族审计，仅核交付契约（语义无「未证」、含 ③b 档位与入口相对锚）3/3 满足后并入，evidence_path 指向 `S03_C7/PROGRESS.md`，MERGE_LOG 注明「待审计」，异族审计下一轮补。

## 10 行 entry 清单
S03 3：004325C0 / 0065CCA0 / 0065D1F0
S09 7：004F4240 / 004E25A0 / 0056BBE0 / 00656AC0 / 0069DE00 / 005BDC80 / 005576A0
黑名单 006A5030 整行不动（保持 `[静态推断]`、原 name/语义/evidence 不变）。

## 改列口径
三列同时改：第 4 列 = delta 原文（逐字节复制，含 ③b 整体合同、入口相对锚，全文无「未证」）；第 5 列 `[静态推断]`→`[已证]`；第 6 列 evidence_path = `S09_KPROVED6/_audit/VERDICT.md`（S09 7 行）/ `S03_C7/PROGRESS.md`（S03 3 行，待审计）。subsystem 全同（S03/S09）。name：3 行按 delta 写并登记（004F4240 `MouseClass::slot0`→`GScreenClass::slot0`、0056BBE0 `MouseClass::slot27`→`MapClass::slot27`、00656AC0 `PowerClass::slot31`→`RadarClass::slot31`，均为 ② 归基类级名）；其余 7 行 name 与 delta/改前逐字节相同。n_sources/conflict 不动。

## 必做自检 (a)-(f)
(a) 行数：改前 18,431 / 改后 18,431；entry 序列逐字节相同、增删 0；恰好 10 行变动，只动第 3/4/5/6 列（3 行含 name）。
(b) grade 直方图（第 5 列，盘上重算改前，未照抄）：改前 `[已证]` 1,450 / `[静态推断]` 5,957 / `[未证]` 11,024（和 18,431）；改后 `[已证]` 1,460 (+10) / `[静态推断]` 5,947 (−10) / `[未证]` 11,024（不变），和 1,460+5,947+11,024=18,431。
(c) conflict==1：改前 254 / 改后 254。
(d) 10 行逐行验证：grade=[已证] 10/10；新语义无「未证」10/10；含 ③b 与入口相对锚 10/10；sem 与 delta 逐字节同 10/10；evidence_path 指向上述两路径 10/10。
(e) 全表复查「[已证] 且语义含槽语义未证 且 subsystem 非 S22」：改前 0 / 改后 0（必须为 0，符合）。
(f) SHA-256：coverage.tsv 改前 `11b324d408b014444e11f67677f883c8924d55d4257c0a977f81e1b681239ae3` → 改后 `e397af8695895c7dce7160c7dfc6cc251a96277babb4929378427bc8090ad48b`；PANEL.md 改前 `281c9e768063fba466bd3c89e766d43776ddde61912aa330c9637389c0db093f` → 改后 `9cadf21e5a20bae64297612dcd61d47b769e193bb394a4273d9bfbfbb8598351`。备份 `_hygiene\coverage.M46.bak`、`_hygiene\PANEL.M46.bak`（SHA 同改前）。

## PANEL 与备份
PANEL.md：第 1 行流水追加 M46；量纲行 M46 后全表 `[已证]` 1,460；三分母「全表/atlas 内 `[已证]`」1,460/1,455（10 行全在 atlas，atlas 外 5 行不变）；面板表 S03 35→38/194=19.59%、S09 按盘上重算 99→106/1051=10.09%、TOTAL 1,445→1,455/12,916=11.27%；M45 段前新增「M46 并表说明」；其余行一字不动（346 行逐行校验字节相同）。
注：M45 面板 S09=95 / S05=157 系沿用 M44 陈旧值，盘上改前实为 99 / 165（经 `_hygiene\coverage.M45.bak` 复核，M45 实际 +7/+8 正确）；本卡按「其余行一字不动」仅重算并更正 S09 行，S05 行未动，留后续卡核。
未改 CONFLICTS.tsv、PENDING_CORRECTIONS.tsv、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli。
