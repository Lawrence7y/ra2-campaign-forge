# PROGRESS · M26 合并员（S13_K12 白名单 3 行补账）

## 结果摘要
- 并入行数：**3**（0040F870 / 0054E890 / 0054EA70）
- 整行不动：**14**（S13_K12/coverage_delta.tsv 其余 14 行黑名单；未并入 coverage.tsv）
- 只改 grade [静态推断]→[已证] 与 evidence_path（补 #entry 锚点，取 delta 原文）；name / one_line_semantics 逐字取 delta（与盘上原值相同，故零差异）；subsystem / n_sources / conflict 逐列不动；entry 增删 0。
- 卡表列出的新名（VectorClass<WarheadTypeClass*>::FindItemIndex / VectorClass<KamikazeControl*>::Clear / VectorClass<KamikazeControl*>::SetCapacity）与 S13_K12/coverage_delta.tsv 实际行不一致：delta 为占位名，按卡面「以 delta 为准」处理，差异见 M26/MERGE_LOG.tsv。

## 前后 grade 直方图（全表 18,431 行）
| grade | 前 | 后 | 变化 |
|---|---:|---:|---:|
| [已证] | 1,449 | 1,452 | +3 |
| [静态推断] | 5,951 | 5,948 | −3 |
| [未证] | 11,031 | 11,031 | 0 |
| 合计 | 18,431 | 18,431 | 0 |

- conflict=1 前 254 → 后 254（不变）。
- 差异行逐列核对：恰好 3 行，仅第 5 列（grade）与第 6 列（evidence_path）变更，其余 6 列与备份逐字等。

## S13（atlas 分母 240）
- proved: 86 → **89/240 = 37.08%**（门槛 120，差 31）
- named(L/S-R14) 216 不变（90.00%）；strict 108 不变（45.00%）
- 3 行全在 atlas 内；atlas 内 [已证] 1,444 → 1,447。

## coverage SHA-256 与行数
| 项 | 前 | 后 |
|---|---|---|
| SHA-256 | 502A56FE261108225B1EE975CB26C86ECDF900A5727069A82B67A35A9C27BAF6 | DC471354E15E5A92F470A37EA7FA69C41FF2660639C2803EC2CB15EE9DFCA80F |
| 数据行数 | 18,431 | 18,431 |
| 文件字节 | 3671509 | 3671335 |

备份：D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/_hygiene/coverage.M26.bak

## 逐行改动
- 0040F870: grade [静态推断]→[已证]；evidence_path `EVIDENCE/analysis_full.json;EVIDENCE/bodies_audit18.txt;EVIDENCE/entry_vt_slots.tsv` → `EVIDENCE/four_rings.md#0040F870`；name/semantics 保持 delta 原文 `?$DynamicVectorClass::PAVWar::vslot4` / `[静态推断] 占位名(slot/vslot/sub),缺具名语义`
- 0054E890: grade [静态推断]→[已证]；evidence_path `EVIDENCE/analysis_full.json;EVIDENCE/bodies_audit18.txt;EVIDENCE/entry_vt_slots.tsv` → `EVIDENCE/four_rings.md#0054E890`；name/semantics 保持 delta 原文 `T_DynamicVectorClass_PAUKamikazeControl__::slot3` / `[静态推断] 占位名(slot/vslot/sub),缺具名语义`
- 0054EA70: grade [静态推断]→[已证]；evidence_path `EVIDENCE/analysis_full.json;EVIDENCE/bodies_audit18.txt;EVIDENCE/entry_vt_slots.tsv` → `EVIDENCE/four_rings.md#0054EA70`；name/semantics 保持 delta 原文 `T_DynamicVectorClass_PAUKamikazeControl__::slot2` / `[静态推断] 占位名(slot/vslot/sub),缺具名语义`

## PANEL 确认
D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/PANEL.md 已更新：标题条加 M26 并表说明；全表 [已证] 1,449→1,452、atlas 内 1,444→1,447；S13 proved 86→89/240=37.08%；三分母 A/B/C 不变；conflict=1 254 不变。
