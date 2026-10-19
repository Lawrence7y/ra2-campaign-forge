# W3-DOC2 派工单 · execution_runbook 档位补条款 + 门禁词汇注记（RPT1C 测绘"现在可做"半区）

> 派发：2026-10-02 21:0x（Lead）· 依据：**RPT1C_SCOPING.md**（§四条裁定表，已验收 RPT1 会话出品）
> 执行：Qoder CN（CS3 会话续办）· 预估 30–50 分钟 · **不碰任何已验收验证器、不碰两份 ATLAS、不碰补丁件**

## 背景

RPT1C 测绘结论：RPT1 的四条建议里，**"成文/注记"半区现在就能做**，落点在 `execution_runbook.md` 与门禁词汇文档；正文半（补丁/claims）被 verify_m35p 的 17,571 B 钉死 + APP2 唯一写者锁 ⇒ 排队（CS4/APP3 之后做）。

## 任务（逐条，先读 RPT1C_SCOPING.md 对应行的 file:line）

1. **G0-4 LAA 条款**（RPT1C 条④）：`execution_runbook.md` 的 G0-4 基准现写 `.ra2opt/orig/gamemd.exe`（gamemd 侧）—— 补充 game 侧真判据的准确表述：判据代码 `ra2opt/pe.py:107,289`、`cli.py:269`、`audit.py:263`、`verify_anchors.py:244-252`（行号以现读为准，禁止照抄本卡行号）。
2. **G0-5 .rsrc 红线**（条②的 runbook 半区）：G0-5 现仅 `.detour` —— 按 RPT1C 建议补 `.rsrc` 段头红线成文（判据出处引 RPT1 §… idx35 的 4B 实证 + audit_bytes 相关行，现读为准）。
3. **门禁词汇注记**（条③的文档半区）：`or 0x200` 回退在两工具源码各 1 命中（`tools/audit_bytes.py:51`、`tools/verify_bss_claims.py:80`，现读为准）—— 在门禁词汇/注记文档处成文：SizeOfHeaders 的回退语义 + "00001000h 只是记录值不是判据"（引正文 L98 现读）。
4. **RPT1 勘误并入**：RPT1C §5 登记的前件勘误（RPT1_REPORT §4 "三档零邻判"多算一档）按 append 方式追加到 RPT1 报告尾部（append-only，标注 `【RPT1C 勘误追加】`，原行一字不动）—— 或若你判 RPT1 报告属只读，则在 DOC2 报告里单列并说明。

## 铁律

- **写域**：`execution_runbook.md`（按实际路径现读定位）+ 门禁词汇文档（若不存在则在 `docs/re/` 下新建 `GATE_VOCABULARY.md`，报告里写明新建理由）+ `out/re_work/qc/W3_20261002/doc2_runbook_terms/`（报告/留证）。
- **只读**：两份 ATLAS、补丁件 M35_ch13_atlas_patch.md、claims*.txt、全部 verify_*.py、tools/*.py、coverage_ledger、dispatch 台账、manifest。
- 全部引文**现读现抄带 file:line**；改前后 sha 快照；空扫描 = INSTRUMENT_FAILED。
- 自写 `verify_doc2.py`：正控=每个条款落位断言 + 负控 ≥2（引文行号错/文件名错 ⇒ 必须 FAIL）。

## 交付

`out/re_work/qc/W3_20261002/doc2_runbook_terms/`：`DOC2_REPORT.md` + `verify_doc2.py` + 快照。完成后回报 `[0]`：四条逐条落位（文件:行）+ verdict tally 原文。
