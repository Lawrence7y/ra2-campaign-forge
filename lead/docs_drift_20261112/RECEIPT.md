# 收尾回执 · docs/ 脱节最小修订提案（2026-11-12）

> 本回执证明：本任务**只出提案、未执行任何 `docs/` 改动**，且写域外全程只读。
> 主交付：[DOCS_DRIFT_PROPOSAL.md](DOCS_DRIFT_PROPOSAL.md)

## 1. 任务与结论速记

- 任务：STEP 1 现况取证 → STEP 2 逐条坐实（两边引用）→ STEP 3 最小修订提案 → STEP 4 结论 → 边界与未验。
- STEP 4 结论：**严重度 中**；最该先改 1 条 = **P-1**：在 `docs/PROJECT_DIRECTION.md` **文件末尾纯尾部追加一行**，指向 `lead/GOAL_THREE_TARGETS_20261018.md` 最新落账节 **§609**（并注明本文最高仅 §483）。
- 改动量（若全部批准）：**2 个文件 / 追加 10 行 / 触碰既有行 0 / 行号漂移 0**。若只批 P-1：**1 个文件 / 3 行**。
- **上述改动一行未写入。** 本目录内所有文件均为「证据 / 提案 / 回执」，不是 `docs/` 修订。

## 2. 六条脱节：两处引用齐备性自检

| # | 脱结点 | docs 侧引用 | 事实侧引用 | grep 落盘 | 判定 |
|:--|:--|:--|:--|:--|:--|
| D1 | 台账节号 | `docs/PROJECT_DIRECTION.md:3`；`docs/re/dispatch/W3_20261002_AUD2_app2_audit.md:3`（§483）；`G1` §60x=0 | `lead/GOAL_THREE_TARGETS_20261018.md:9832`（§609）、`:9760/:9775/:9787/:9802`；`RE_PROGRESS_20261111.md:85` | `_grep/G1_section_numbers.txt` | 坐实 |
| D2 | D-31 裁决 | `G2`：D-31 / direction_ruling / RULING_DIRECTION / 方向裁决 全 0；`docs/WORK_CHAIN.md:64–76` | `lead/direction_ruling_20261108/RULING_DIRECTION.md:5,21,38,77`（16,514 B）；`RE_PROGRESS_20261111.md:64` | `_grep/G2_d31.txt` | 坐实 |
| D3 | 11-10/11-11 静态线 | `G3`：0x54A56E / 0x54A4F0 / 0x54A630 / 预置槽位 / PercentBuilt / 6 个轮次目录名 全 0 | `RE_PROGRESS_20261111.md:11,67–72,74,94`；`_sf_scan_out.txt:2,18,19`；`_cw_disasm_out.txt:2,66`；`_md_parse_out.txt:2,16`；`_ps_disasm_out.txt:11,115`；`_oo_map_out.txt:2,75,150` | `_grep/G3_static_line.txt` | 坐实（限定） |
| D4 | RE-ATLAS 停摆 | `docs/REWRITE_ROADMAP.md:22,26,28,54,79`；`docs/REWRITE_RESEARCH.md:3,11–13`；`G4` RE-ATLAS/R-064/4.07%/12,792 全 0 | `re_atlas/STATUS.md:1,6,57,453,477`（89,528 B，mtime 10-30）；`RE_PROGRESS_20261111.md:14,24,83` | `_grep/G4_atlas_numbers.txt` | 坐实（数字 988/954 **一致**，脱节在缺状态锚点/快照标题） |
| D5 | 交付线 C 进度 | `docs/PROJECT_DIRECTION.md:48,50,59`；`docs/DESIGN.md:3`；`docs/REWRITE_RESEARCH.md:312,319` | `ra2forge/cli.py:25–27`、`builder.py:59–119`；实测 `build_probe/BUILD_PROBE_RESULT.md`（exit 0 / 6 产物） | `_grep/G5_ra2forge.txt` | 坐实（**部分**过时；最小贯通样例未验） |
| D6 | P0/P1 队列口径 | `docs/PROJECT_DIRECTION.md:69–83`；`docs/NEXT_RE_AND_MODERNIZATION.md:3`；`WORK_CHAIN.md:3`；`REWRITE_ROADMAP.md:3`；`AGENT_TASK_TEMPLATE.md:4` | `RE_PROGRESS_20261111.md:15,39–41,85,91`；台账 §600–§609 | `_grep/G6_queue.txt` | 坐实（口径层；表格文字不改） |

辅助 grep：`G0_SUMMARY.md/json`（精确计数汇总）、`G7_fact_side.txt`（事实侧逐行输出）、`G8_quotes.txt`（STEP 3 拟注解处逐字原文）、`G9_line_pins.txt`（行号钉位反查 3,856 件）。

## 3. `docs/` 零改动指纹证明

见 [\_evidence/02_docs_zero_change_proof.md](_evidence/02_docs_zero_change_proof.md) 与 `.json`。

| 项 | 起点（STEP 1） | 收尾 | 判定 |
|:--|:--|:--|:--|
| 文件数 | 416 | 416 | 一致 |
| `docs_tree_sha256` | `70247ef54170dd6d06e6f328124a8d34d7e17721c32356acdec921c06a2bf787` | 同左 | **EQUAL** |
| 逐件差异 `{rel,bytes,sha256,mtime_ns}` | — | **0 项** | 零差异 |

关键两件收尾实算：

| 文件 | bytes | sha256 |
|:--|--:|:--|
| `docs/PROJECT_DIRECTION.md` | 10,194 | `1b1f56ce022694c9aabb2f58e3d3809b689e977720e3176424d82b251763949b` |
| `docs/WORK_CHAIN.md` | 23,507 | `740910625f1685beacc9d5fa9f8d58ad1d74fdb53098fad0ed6474da39f257f5` |

⇒ **`docs_zero_change = True`**。指纹全部由 `hashlib.sha256` 实算，未转抄、未推算。

## 4. 铁律自查

| 铁律 | 执行情况 |
|:--|:--|
| 1 零真机 | ✅ 未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 attach、未读活进程内存。唯一程序执行是纯 Python 的 `ra2forge` CLI（`example` + `build`，`--install` 未传） |
| 2 只读边界 | ✅ `docs/` 零改动（上节指纹）；未改任何其它非写域文件；**未执行** git commit / push / reset / checkout |
| 2b 禁改 `docs/` 下任何文件 | ✅ 逐件指纹 0 差异；STEP 3 只出提案文本 |
| 3 python 口径 | ✅ 全部 `python -I -X utf8 <绝对路径脚本>`（5 支脚本，命令见第 5 节） |
| 4 指纹 hashlib 实算 | ✅ 全部 `hashlib.sha256`，1 MiB 分块读；全树聚合指纹亦有定义与复算 |
| 5 只用材料直接支持的话 | ✅ 每条结论给 `文件:行`；拿不到的一律写入「边界与未验」13 条，未补造 |
| 6 报告须有「边界与未验」 | ✅ 主交付文末专章（A 铁律自查 + B 未验 13 条） |

补充自证：`ra2forge/__pycache__` 内 11 个 `.pyc` mtime 均为 **2026-11-12 00:23:05**，早于本轮开工 **00:42:14**，属既存文件、非本轮写入；按只读边界未删除。各脚本均置 `sys.dont_write_bytecode=True` 于 import 之前。

## 5. 本轮全部命令（可复核）

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_step1.py
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_grep.py
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_build_probe.py
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_linepins.py
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_verify_docs.py
```

只读 PowerShell 辅助命令（建写域、列目录、查 `__pycache__` mtime、列 `re_atlas/` 顶层 mtime）：均为 `New-Item`/`Get-ChildItem`/`Get-Date`，无删除、无移动、无改写。

> 一条 repo 全树行号反查因 73 MB 证据文件耗时过长被主动取消（后台 job `pwsh-0b5aab6fcacb4c1f`），改为有界扫描 `_fd_linepins.py`，跳过 4 件 >5 MB 文件并在 `G9_line_pins.txt` 中登记为未验。取消的是**读取作业**，非写操作。

## 6. 写域清单（本目录全部新建文件）

```
lead/docs_drift_20261112/
  DOCS_DRIFT_PROPOSAL.md             主交付（STEP1→STEP2→STEP3→STEP4→边界与未验）
  STEP1_DOCS_INVENTORY.md            416 件 mtime 升序全量指纹表 + 按日聚合
  STEP1_SECTION_HEADERS.md           两份文档的逐节标题行号
  RECEIPT.md                         本回执
  _fd_step1.py / _fd_grep.py / _fd_build_probe.py / _fd_linepins.py / _fd_verify_docs.py
  _evidence/
    00_docs_manifest_start.json      起点快照（416 件 + tree_sha256）
    00_docs_tree_sha256.txt
    01_fact_side_fingerprints.md/.json   42 件事实侧引用件指纹
    02_docs_zero_change_proof.md/.json   收尾零改动证明
  _grep/
    G0_SUMMARY.md / G0_SUMMARY.json
    G1_section_numbers.txt  G2_d31.txt  G3_static_line.txt  G4_atlas_numbers.txt
    G5_ra2forge.txt  G6_queue.txt  G7_fact_side.txt  G8_quotes.txt  G9_line_pins.txt
  build_probe/
    BUILD_PROBE_RESULT.md / BUILD_PROBE_RESULT.json
    demo_campaign.json
    out/Example Operation/{BATTLEMD98.INI, BUILD_REPORT.txt, EX01.MAP,
                           expandmd98.mix, INSTALL.txt, story.md}
```

## 7. 明确未执行

- STEP 3 的 P-1…P-6 共 10 行追加文本：**一条也未写入 `docs/`**。
- 未重写任何 docs 文件；未改 `docs/re/**` 任何一件；未改台账、未改 `PENDING_DECISIONS.md`、未 commit、未 push、未派新任务。
- 本回执与主交付是**提案与证据**，不构成修订授权；实施需另获批准，并按 `docs/WORK_CHAIN.md:172` 的机检三件套（锚窗逐字节不变 + 同物名称集合不变 + 纯尾部 append）复核。
