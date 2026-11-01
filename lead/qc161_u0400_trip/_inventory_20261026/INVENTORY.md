# 整仓告警盘点（standing inventory）——2026-10-26，D-07 定谳执行

- 扫描件：Mimosa deep，scanId `scan-2026-10-25T16-26-38.667Z-266177a1e9f9`，
  seal `sha256:b60452c7aa90…`，jobId `scan-job-mvo1i40h-5d0d7b492be21fc9`。
- 全量 39 条 = 38 high + 1 low；本目录 `findings_full.json` 为逐条台账（含 findingId/occurrenceId）。
- 性质：**只读盘点**（定谳「保留整仓告警记录」义务）。本报告不改变任何门禁行为。

## 一、冻结件豁免清单（wontfix，6 条——破冻结才可消，须用户单独授权）

| # | 位置 | 类别 | advisory |
|---|---|---|---|
| 1 | lead/goal1_harness6_20261022/qc151_trip.harness6.py:796 | 路径穿越 | no |
| 2 | lead/goal1_harness6_20261022/qc151_trip.harness6.py:7380 | create_isolated_carrier 1 跳 path-traversal | 自标 advisory |
| 3 | lead/goal1_harness6_20261022/qc151_trip.harness6.py:8309 | finalize_trip 1 跳 path-traversal | 自标 advisory |
| 4 | lead/goal1_harness7_20261023/qc151_trip.harness7.py:796 | 路径穿越 | no |
| 5 | lead/goal1_harness7_20261023/qc151_trip.harness7.py:7468 | create_isolated_carrier 1 跳 path-traversal | 自标 advisory |
| 6 | lead/goal1_harness7_20261023/qc151_trip.harness7.py:8433 | finalize_trip 1 跳 path-traversal | 自标 advisory |

冻结件哈希：harness6 `ff8245d27b3db22a` / harness7 `d019e8beecfb5fd8`（裁决原文）。
豁免依据：定谳 2026-10-25 23:38「母本零改动铁律优先于扫描器告警」。

## 二、非冻结件（33 条 high + 1 low）——归属线修复或迁出，不设死线

- **tools/ ×17**（全部路径穿越）：atlas_apply_patches ×2、atlas_audit ×3、atlas_toc ×2、
  atlas_va_crosscheck ×2、audit_bytes ×1、bench_map_install ×1、extract_hook_tables ×1、
  validate_package_manifest ×1、verify_anchors ×1、verify_bss_claims ×2、verify_kit/_vk_io ×1
  ——归属=GOAL-3T/审计工具线。
- **lead/ ×14**：goal1_a8_fix（VERIFY_A8 代码注入 ×2 + harness4/5 advisory 污点链 ×4 +
  直接穿越 ×2）、dropped611/cont01_scan ×2、boot_fingerprint ×1、goal3_p1sbh_merge/mkdiff ×1、
  **qc161_u0400_trip 本线现役 `_disc_armG.py:75`、`_disc_stdio.py:47` 各 1（路径穿越）**
  ——归属=GOAL-3T 线；其中两条为本线现役探针，可直接修。
- **ra2forge/ ×2**：builder.py:570 high（路径穿越）、maplib.py:161 low——归属待定（ra2forge 线）。

## 三、与拦截消息的对账

- git-gate 拦截消息只显示前 12 条且恒为同一批（tools/atlas_* + VERIFY_A8），
  与本盘点 39 条同源（同一扫描底座）。
- **实证结论（阳性对照 2026-10-26，§436）**：gate 实为**整树扫描**，
  `scan-profiles.json` 宣称的 `gate.scope=diff-only` 在本版本**未被实现**
  （5 行植入件在 pathspec diff 内、远低于 maxDiffLines=500，归因零命中）。
