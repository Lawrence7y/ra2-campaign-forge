# W3-S4B 派工单 · **M43R 的 10 条 FALSIFIED 回填 §17 原卡**（ZCode 客户端 · 新会话 · 第二批回填）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：S3 已回填 S1 的 108 行九张 agy 原卡（Lead 验收）。**S1 早于 M43R** ⇒ 第二批：
> - **M43R 对 §17 判 `212 → 10 FALSIFIED / 202 HOLDS`**（明细在 `qc/W3_20261002/m43r_ch17_audit/{M43R_REPORT.md, m43r_full_population.json}`）
> - **对象 = ZCode 自己的 §17 原卡**：`out/re_work/zcode_live/W3_20261001/m43_ch17_expand/`（**本卡写域之一，Lead 授权追加**）

## 🔴 铁律（先读）
1. **追加式勘误**：对 `M43_REPORT.md` 与（如涉及）`M43_ch17_atlas_patch.md` 追加勘误块，**原句零删除**；块形态：
   `> 【W3-S4B 回填】<VA/id>：<原声称> → <正确值>｜依据：M43R_REPORT §② + m43r_full_population.json｜分级：<实证/推演>`
   - **10 条逐条落**；manifest/claims 数据字段不改（修正只出副本标未入册）。
2. **改前快照** 存 `out/re_work/zcode_live/W3_20261002/s4b_backfill/snapshots/`。
3. **`verify_M43.py` 与 `verify_m43r.py` 改前改后各跑**（四跑原文落 `runs/`；须全绿 EXIT=0）。
   - ⚠️ **已知**：`verify_m43r.py` 的 `T18`（protected trees）此前因 **Lead 派卡并发** FAIL（台账 §467 已裁为环境因素）⇒ 若 T18 再红，**核对 touched 清单**：只要不出现新文件即判同因，**报告注明即可，不算本卡红灯**；其余 19 条必须全绿。
4. **只读红线**：ATLAS、coverage_ledger、`ra2youli/**`、`tools/**`、qc 目录不碰。
5. **写域**：`zcode_live/W3_20261001/m43_ch17_expand/`（追加式）+ `zcode_live/W3_20261002/s4b_backfill/`

## 交付
`S4B_REPORT.md`（§A 十节骨架；`[0]` 直答）· `s4b_backfill_ledger.json`（10 条逐条）· `snapshots/` · `runs/`（四跑原文）· `verify_s4b.py`（**EXIT=0 + `verdict tally` 行**；断言：10/10 落、零删除前缀相等、四跑结果如实记录、claims/manifest 未改）

## 回报 `[0]`
① 10 条落了几 ② 四跑 EXIT（T18 按铁律 3 处置）③ 反向验证 ④ `verdict tally` 原文

## 底线
> **宁可交"10 条落 8 条、2 条冲突列出"，也不要交一个把 T18 静默跳过的全绿。**
