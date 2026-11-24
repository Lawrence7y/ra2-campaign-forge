# M37 · 并入 a-S08-KPROVED2 白名单 6 行 + 登记 1 处 docs 命名冲突

执行时间：2026-11-18T10:49:16.027Z｜写域：COVERAGE/ + M37/｜备份：_hygiene/coverage.M37.bak

## 前后直方图

| grade | 前 | 后 | 变化 |
|---|---:|---:|---:|
| [已证] | 1366 | 1372 | +6 |
| [静态推断] | 6041 | 6035 | −6 |
| [未证] | 11024 | 11024 | 0 |
| 合计数据行 | 18431 | 18431 | 0 |

conflict=1 保持 254 → 254。

## 6 行 applied（仅改第 4/5 列：one_line_semantics / grade）

| entry | name（未改） | grade 前 → 后 |
|---|---|---|
| 0045A680 | T_DynamicVectorClass_PAVFoggedObjectClass__::slot2 | [静态推断] → [已证] |
| 0045A730 | T_DynamicVectorClass_PAVFoggedObjectClass__::slot4 | [静态推断] → [已证] |
| 004D24A0 | FoggedObjectClass::slot6 | [静态推断] → [已证] |
| 004D2510 | FoggedObjectClass::slot5 | [静态推断] → [已证] |
| 004D27D0 | FoggedObjectClass::slot3 | [静态推断] → [已证] |
| 004D2810 | FoggedObjectClass::slot13 | [静态推断] → [已证] |

name / subsystem / evidence_path / n_sources / conflict 全部逐字节未改；name 仍为 ::slotN 占位名，本卡不改名。

## 2 行 rejected（整行不得改动，保持 [静态推断]）

| entry | 审计理由 |
|---|---|
| 0045AB50 | 槽位虚构：卡称 007E44F4 slot10 @007E451C 不存在（该表仅 7 槽 0..6，slot7 @007E4510=007FC558 是下一张表 COL）；free 在 +0x76 非 +0x66、false 在 +0x3F 非 +0xCE；④ 无（唯一构造器写点 00488098 被 00483A5C 直调后 00483A61 立即覆写 vptr，其余为 dtor/atexit；direct E8=0）。 |
| 0045AC30 | 同上（007E4524=007E4514 slot4，非卡称 007E44F4 slot12）；偏移整体错位；④ 无。 |

两行经 verify 逐字节与改前一致。属 SURVEY-RING24 livevt 歧义 111/112：DV slot(7+k) ≡ V slot k（k=0..6）。

## CONFLICTS 前后行数

472 → 473。追加行：entry=004D2510，field=name，source_a=docs（3 份 docs 记作 FoggedObjectClass::Draw），source_b=coverage:FoggedObjectClass::slot5，status=OPEN:docs 命名 vs 盘上占位名。不改 grade、不改名。

## S08 proved 前后

coverage 原始 S08 行 23（atlas∩coverage 分母 22；0065B800 不在 atlas）。grade 统计（原始 23 行口径）：proved **3 → 9/22**（门槛 11，差 2）。

**S08 仍不达标（9/11）。** named(L) 20/22 不变。

## coverage SHA-256

- 前：815683a15081ee3ec219423bd170809b0f292c77228043a728008ae6249ffd55
- 后：8b501ae84a68ed6daf0d3407bf8ea67d635ec106596d151de45af950e421af22

## 交付物

- COVERAGE/coverage.tsv（6 行提级）
- COVERAGE/CONFLICTS.tsv（+1 行）
- _hygiene/coverage.M37.bak（改前备份）
- M37/MERGE_LOG.tsv（6 applied + 2 rejected）
