# PROGRESS — CONFLICT_CLASS2

CONFLICTS.tsv 列结构(4列): entry | field | source_a(card:value) | source_b(card:value)
前3行(列以 | 分隔):
  00410410 | subsystem | C01_census:S17 | S18-F1:S18
  00410410 | name | C01_census:AbstractClass::Save | S18-F1:AbstractClass::CalculateChecksum
  00438BF0 | name | C01_census:BombListClass::Update | W174_dirty80:fn_00438BF0

CONFLICTS.tsv: 数据行 463 (≈463 ✓), distinct entries 262, field=subsystem 179/name 273/grade 11。
coverage.tsv: 列 entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict; 数据行 18431; conflict=1 行 250 (≈250 ✓), distinct entries 250。

两个量纲不同的原因:
- 463 是【字段级行数】：同 entry 拆多行(subsystem/name/grade), 262 entry→463 行。
- 250 是【entry级标志行数】：coverage 每 entry 仅 1 行, conflict=1 即该 entry 有冲突。
- 250 个 coverage 冲突 entry 全部 ⊂ 262 个 CONFLICTS entry; 余 12 个为 CONFLICTS-only 的 grade-only 记录
  (W177-C(delta) ↔ PENDING_CORRECTIONS(M5)), 不在 coverage conflict=1 集合, 故不进分类。
- 均为盘上实测值, 未为对齐 463/250 调数。

冲突侧取值: 默认 CONFLICTS.source_a(card/prior); 若 coverage 的 name+subsystem 与 source_a 全吻合则取 source_b。
多行 entry 冲突侧 name/subsystem 以 `;` 连接, 每 entry 一行。未做 RTTI/裁决。
