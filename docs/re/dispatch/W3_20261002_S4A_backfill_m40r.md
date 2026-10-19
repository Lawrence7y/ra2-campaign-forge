# W3-S4A 派工单 · **M40R 的 48 条 FALSIFIED 回填 §21 原卡**（Qoder CN · 新会话 · 第二批回填）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：S3 已把 S1 的 108 行回填九张 agy 原卡（Lead 验收 `verify_s3.py` EXIT=0）。**但 S1 汇总早于 M40R/M43R** ⇒ **第二批未回填**：
> - **M40R 对 §21 判 `48 FALSIFIED`**（全在 callgraph 层：24 helper + 24 BSS；19 条物理不可能 + 29 条数值虚高 —— 明细在 `zcode_live/W3_20261002/m40r_ch21_audit/{callgraph_check.json, M40R_REPORT.md}`）
> - **对象 = 任务 E 的 §21 原卡**：`out/re_work/qc/W3_20261001/m40_ch21_expand/`（**你的同门写域，Lead 授权追加**）

## 🔴 铁律（先读）
1. **追加式勘误**：对 `M40_REPORT.md` 与（如涉及）`M40_ch21_atlas_patch.md` 追加勘误块，**原句零删除**；块形态：
   `> 【W3-S4A 回填】<VA>：<原声称调用者/访问者数> → <实测数>｜根因：<物理不可能/数值虚高>｜依据：M40R_REPORT §② + callgraph_check.json｜分级：[推演]（callgraph 层）`
   - 48 条**逐条落**（`manifest/claims 数据字段不改`；若 M40R 建议改 manifest ⇒ 只出修正副本标未入册）。
2. **改前快照**（`M40_REPORT.md`、`M40_ch21_atlas_patch.md` 等目标件）存 `out/re_work/qc/W3_20261002/s4a_backfill/snapshots/`。
3. **`verify_M40.py` 与 `verify_m40r.py` 改前改后各跑一次**（四跑原文落 `runs/`；**须全绿 EXIT=0**；改后红灯 ⇒ 回滚该文件并报告；**不许改验证器**）。
4. **只读红线**：ATLAS、coverage_ledger、`ra2youli/**`、`tools/**`、zcode_live 目录不碰。
5. **写域**：`qc/W3_20261001/m40_ch21_expand/`（追加式）+ `qc/W3_20261002/s4a_backfill/`

## 交付
`S4A_REPORT.md`（§A 十节骨架；`[0]` 直答）· `s4a_backfill_ledger.json`（48 条逐条：VA / before-sha / after-sha / 根因桶）· `snapshots/` · `runs/`（四跑原文）· `verify_s4a.py`（**EXIT=0 + `verdict tally` 行**；断言：48/48 落、零删除前缀相等、四跑全绿、claims/manifest 未被改）

## 回报 `[0]`
① 48 条落了几/跳过几 ② 四跑 EXIT ③ 反向验证（抽 2 条核块 + 抽 1 条 HOLDS 未被回填）④ `verdict tally` 原文

## 底线
> **宁可交"48 条落 40 条、8 条因与 M40 报告结构冲突列出"，也不要交"全落但 verify_M40 红灯"。**
