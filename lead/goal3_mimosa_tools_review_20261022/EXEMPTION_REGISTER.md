# Mimosa 豁免登记 · `tools/` 路径穿越告警

**扫描**：`scan-2026-10-22T04-33-44.241Z-23b228f990d6`
**seal**：`sha256:bccfadd22dc88456586faf6a3e4e96039d0fc8a61fcf96c614042573f80994b0`
**规则**：`路径穿越`（high）
**判定书**：`MIMOSA_TOOLS_VERDICT.md`
**复核人**：GOAL-3T 节拍驱动器（`tools/` 负责方）
**复核日期**：2026-10-22

---

## 豁免条目（17 处）

| # | 位置 | 路径来源 | 理由 |
|--:|:--|:--|:--|
| 1 | `tools/atlas_apply_patches.py:211` | `args.atlas` | CLI 输出路径，调用者自负 |
| 2 | `tools/atlas_apply_patches.py:228` | `args.ledger` | 同上 |
| 3 | `tools/atlas_audit.py:189` | `args.va_out` | 同上 |
| 4 | `tools/atlas_audit.py:193` | `args.json_out` | 同上 |
| 5 | `tools/atlas_audit.py:230` | `args.md_out` | 同上 |
| 6 | `tools/atlas_toc.py:137` | `args.report` | 同上 |
| 7 | `tools/atlas_toc.py:144` | `args.report` | 同上（第二写点） |
| 8 | `tools/atlas_va_crosscheck.py:153` | `args.*` | 同上 |
| 9 | `tools/atlas_va_crosscheck.py:191` | `args.*` | 同上 |
| 10 | `tools/audit_bytes.py:638` | `a.json_out` | 同上（argparse 命名空间） |
| 11 | `tools/bench_map_install.py:149` | `LOG_DIR` 常量 + 时间戳 | 无外部输入进入路径 |
| 12 | `tools/extract_hook_tables.py:390` | `out_file` 模块常量 | 无外部输入进入路径 |
| 13 | `tools/validate_package_manifest.py:422` | `args.*` | CLI 输出路径 |
| 14 | `tools/verify_anchors.py:1073` | `args.*` | 同上 |
| 15 | `tools/verify_bss_claims.py:311` | `emit_claims` | 同上 |
| 16 | `tools/verify_bss_claims.py:333` | `json_out` | 同上 |
| 17 | `tools/verify_kit/_vk_io.py:23` | — | **假阳性**：该函数体内紧跟 `raise ValueError("path must not traverse upward")`，`write_bytes` 在 `open` 前必经此校验 |

---

## 豁免失效条件

以下任一发生时，本登记**自动失效**，须重新审视：

1. `tools/` 下新增**非 CLI 来源**（被测文件内容 / 网络 / 目录遍历结果）进入写路径的代码；
2. 上表任一站点的路径来源被改为来自被测文件内容；
3. 新增 `tools/` 子目录下的可写文件。

## 未豁免（范围外，移交对应责任方）

| 位置 | 归属 |
|:--|:--|
| `lead/dropped611/scripts/cont01_scan.py:410` | lead 侧，未判 |
| `lead/dropped611/scripts/cont01_scan.py:441` | lead 侧，未判 |
| `lead/goal3_p1sbh_merge_20261020/_work/mkdiff.py:88` | lead 侧，未判 |
| `ra2forge/builder.py:570` | ra2forge 侧，未判 |
| `lead/goal1_a8_fix_20261022/qc151_trip.harness4.py:768` | **本线自查**：路径为本趟自建载体目录，误报（见 A8 判定书） |
| `lead/goal1_boot_fingerprint_20261022/boot_session_fingerprint.py:1568` | **本线自查**：CLI 输出路径，误报 |

## 使用纪律

- 本登记**不构成**「`tools/` 已安全」的一般性结论，只针对上表 17 个具体站点。
- 不得据此使用 `--no-verify`。
