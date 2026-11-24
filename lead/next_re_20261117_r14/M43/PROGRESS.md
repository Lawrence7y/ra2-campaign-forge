# M43 · PROGRESS

合并员 M43；开工 2026-11-19T15:44:05+08:00。写域仅 COVERAGE\coverage.tsv、COVERAGE\PANEL.md、M43\、_hygiene\coverage.M43.bak 与 PANEL.M43.bak。未改 CONFLICTS.tsv / PENDING_CORRECTIONS.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\；未 git commit、未建 venv、未 pip install。
输入只读：S03_C6\coverage_delta.tsv（7 行）+ `_audit\VERDICT.md`（有条件 PASS，应并入 6 行）；S10_KPROVED3\coverage_delta.tsv（8 行）+ `_audit\VERDICT.md`（部分成立，应并入 7 行，004DDDE0 降 ③a 不并入）。

## 13 行白名单 entry 清单（不得增删；S03 6 行按 VERDICT 逐行白名单，S10 7 行 = delta 8 行除 004DDDE0）
1 004322A0 S03 CDFileClass::vslot9 — 并入；col4=`[静态推断] FileSystem/MIX member (rtti-vftable)`，无自陈未证
2 0047AE10 S03 — 未并入；col4 含「槽语义未证」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
3 0065CDD0 S03 — 未并入；col4 含「槽语义未证」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
4 0065D0D0 S03 — 未并入；col4 含「槽语义未证」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
5 0065D190 S03 — 未并入；col4 含「槽语义未证」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
6 00431F70 S03 — 并入；col4=`[静态推断] FileSystem/MIX member (rtti-vftable)`，无自陈未证（审计「改两处语义」指 delta 写值错，非盘上 col4）
7 004D82B0 S10 — 未并入；col4 含「槽语义未证[未证]」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
8 004D5690 S10 — 未并入；同上
9 004DB260 S10 — 未并入；同上
10 00702D40 S10 — 未并入；col4 含「槽语义未证」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`
11 00706640 S10 — 未并入；同上
12 00708C30 S10 — 未并入；同上
13 004D94B0 S10 — 未并入；col4 含「槽语义未证[未证]」⇒语义自陈未证，需先补语义；grade 保持 `[静态推断]`

## 被剔行说明（不在白名单，整行不动）
S03 `00432050`：S03_C6 VERDICT line20/25/37 判语义反向（实为缓冲写非缓冲读）退回重写 ⇒ 不并入、grade 保持 `[静态推断]`、整行不动。
S10 `004DDDE0`：S10_KPROVED3 VERDICT line4/26/28 判 ③b①′（D-42 细则#1 守卫链）不成立、降 ③a ⇒ 不并入、grade 保持 `[静态推断]`、整行不动。

## 必做自检（全部通过）
(a) 行数：改前 18,431 → 改后 18,431 数据行（8 列合法）；entry 增删 0、无重复；仅 2 行变化且只动第 5/6 列。
(b) grade 直方图：改前 [已证] 1,422 / [静态推断] 5,985 / [未证] 11,024；改后 [已证] 1,424（+N，N=2）/ [静态推断] 5,983（−2）/ [未证] 11,024 不变；和 18,431。
(c) conflict==1：254 → 254，不变。
(d) 并入 2 行逐行：grade 全 `[已证]`（2/2）；name 逐字节不变（00431F70=BufferIOFileClass::vslot7、004322A0=CDFileClass::vslot9）；subsystem/one_line_semantics 亦逐字节不变；evidence_path 均指 `S03_C6/_audit/VERDICT.md#19`。
(e) 全表复查 `[已证]` ∧ 语义栏含「槽语义未证」 ∧ subsystem≠S22：改前 0 → 改后 **0**（S22 豁免 10 行不变）。
(f) coverage.tsv SHA-256：改前 `ABDD594DD0DAC330B306D859ECEB99D42CD13DC17AA5DC451D24544110C06A0C` → 改后 `6441686A8205B236315BAEDB4CD1477A5C7B2C87E49077DA532AC186DA2BA0E2`；备份 `_hygiene\coverage.M43.bak` SHA 与改前逐字一致。

## 交付
M43\PROGRESS.md、M43\MERGE_LOG.tsv（1 表头 + 13 白名单行 + 2 被剔行 = 16 行）；PANEL.md 标题/量纲/三分母/S03/S10/TOTAL 按重算值更新并新增 M43 段（置于 M41 段前；PANEL 原无 M42 段）。
改后 coverage SHA-256 前 8 位：`6441686a`。
