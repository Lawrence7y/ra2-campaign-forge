# W3-S1 派工单 · **九章审计 FALSIFIED 汇总 → 原卡回填清单**（ZCode 客户端 · 续会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：**九章审计已收口**（M28R/M32R/M30R/M31R/M33R/M36R/M37R/M39R/M41R），合计产出 **FALSIFIED 约 70+ 条**，分散在九份报告里。**原卡（M25/M29/M30/M31/M33/M36/M37/M39/M41，均归 Antigravity）尚未回填** —— 而 Antigravity 额度刚恢复。
> **本卡 = 把九份审计报告的裁决汇成一张机器可读的回填清单**，让后续回填卡（或 Antigravity）可以逐条执行，不必重读九份报告。
> **本卡纯读 + 单一写域，不改任何原卡、不改任何审计件。**

## 🔴 铁律（先读）
1. **九份审计件与九份原卡全部只读**（`minimax/W3_20261002/**`、`zcode_live/W3_20261002/**`、`workbuddy/W3_20261002/**`、`qc/W3_20261002/**`、`agy/W3_20261001/m*/**`）。
2. **只汇总裁决，不重新审计**：每条 FALSIFIED **逐字引用审计件的证据**（给 `source_report + 行号/节号`），**不许自己改判**。若两份审计对同一 VA 有冲突 ⇒ 标 `CONFLICT` 并列两侧原文（不许取一）。
3. **空扫描报 `INSTRUMENT_FAILED`**（例：找不到某审计件 ⇒ 明说，不许静默跳过）。
4. **写域仅此一处**：`out/re_work/zcode_live/W3_20261002/s1_falsified_consolidation/`

## 已收审计件清单（**逐份核对存在性，缺的标 NOT_FOUND**）
```
minimax/W3_20261002/m28r_ch4_rework/M28R_REPORT.md        (§4,  4 FALSIFIED + HOLDS 30→19)
workbuddy/W3_20261002/m32r_rtti_bca/                     (§6,  CLAIM_WRONG=7 — 报告可能未写，以 verify_m32r.py 与 m32r_recheck.json 为准)
zcode_live/W3_20261002/m30r_ch7_audit/                   (§7,  5 FALSIFIED/316)
zcode_live/W3_20261002/m31r_ch8_audit/M31R_REPORT.md     (§8,  3 FALSIFIED/261)
minimax/W3_20261002/m33r_ch11_audit/M33R_REPORT.md       (§11, 15 FALSIFIED/60 — 含槽索引算术 21/22 行同病)
minimax/W3_20261002/m36r_ch14_audit/M36R_REPORT.md       (§14, 25 FALSIFIED/1371 全在[推演])
zcode_live/W3_20261002/m37r_ch15_audit/M37R_REPORT.md    (§15, 8 FALSIFIED/662)
minimax/W3_20261002/m39r_ch20_audit/M39R_REPORT.md       (§20, 4 FALSIFIED/300)
zcode_live/W3_20261002/m41r_ch22_audit/M41R_REPORT.md    (§22, 4 FALSIFIED/525)
```

## 做什么（四件）
1. **逐份抽取 FALSIFIED**：每条 = `{chapter, source_card, va_or_id, claim, corrected_value, evidence_quote, source_ref}`。
   - **M33R 的 21/22 行槽索引同病**要展开成逐行（或给出"同病模式 + 例外行"的结构化表达，让回填者能机械执行）。
   - **M36R 的 25 条**全是 `[推演]` 层入口偏移 —— 单独分组（回填时是"降级或重定位"二选一）。
2. **按回填动作分桶**：
   - `FIX_ADDRESS`（给正确值的）· `DOWNGRADE_TO_INFERRED`（[实证]→[推演]）· `FIX_SLOT_INDEX` · `REMOVE_CLAIM` · `RELOCATE_ENTRY`（入口偏移，需重找函数起点）· `CONFLICT`（两审计打架）。
   - **每桶给计数与逐条清单**。
3. **去重与交叉**：同一 VA/同一 claim 出现在多份审计的 ⇒ 合并成一条并标 `multi_source`（例：M33R 与 M41R 都查过槽索引的类是否重叠）。
4. **反向验证**：构造"应当失败"对照 —— **抽 3 条你汇入的 FALSIFIED，回原审计件核逐字引用是否真的存在**（防你自己抄错）；再**抽 1 条 HOLDS 混入清单，证明它没进来**。

## 交付
`S1_REPORT.md`（§A 十节骨架；`[0]` 直答：九件各收到几条 / 桶分布计数 / CONFLICT 数）· `falsified_consolidated.json`（全量逐条）· `bucket_summary.json` · `verify_s1.py`（**EXIT=0 + `verdict tally` 行**）· `raw/stepNN_*.txt` + `raw/progress.log`（**每收完一份审计件先落盘一次**）

## 回报 `[0]`
① 九件各自收到几条（缺件标 NOT_FOUND）② 桶分布计数 ③ CONFLICT 数（有则逐条）④ 交叉去重结果 ⑤ 反向验证（3 条逐字核 + 1 条 HOLDS 未混入）⑥ `verdict tally` 原文

## 底线
> **宁可交"九件收到 8 件、M32R 因缺报告只从 JSON 提取、共 N 条且 2 条 CONFLICT"，也不要交"九件齐全共 70 条无冲突"。**
> **本卡的价值是"可机械执行" —— 回填者拿着 JSON 就能逐条改，不需要再读九份报告。**
