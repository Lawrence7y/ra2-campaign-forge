# W3-DOC1 派工单 · **YR 侧 ATLAS 待传播勘误落地（第一批）**（ZCode 客户端 · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：交接件 `out/re_work/W3_20261002_RESUME_AFTER_REBOOT.md` §7 待办 5 至今未执行：
> > **待传播进 ATLAS：`E-W3-23/25/27/28/34` · R56 更正（插入位 `{42,43,44}`，"唯一 idx 43" 已作废）· `CNetUtilEventSink` 更名 · 移除 35 个非 `.text` VA 的登记**
> **目标文件 = YR 侧 `docs/re/ARCHITECTURE_ATLAS.md`（455,987 B 级，与原版侧 ATLAS 是两个文件；原版侧归 APP1 会话，本卡禁碰）。**
> **勘误依据件**：`out/re_work/_lead_baseline/W3/LEAD_DISCIPLINE_INDEX.md`（自错清单）· `LEAD_ERRATUM_*.md` 系列 · 台账 R56 更正节（§180）· `docs/re/` 内既有 `【W3 勘误】` 注记体例（M11/DOCFIX 先例）

## 🔴 铁律（先读）
1. **严格 append-only / 就地加注**：原句零删除零改写；注记体例照既有 `> 【W3 勘误 E-W3-XX】改前：… / 改后：… / 依据：… / 分级：…`。
2. **改前全量快照**（文件 + 逐文件 sha）存 `out/re_work/zcode_live/W3_20261002/doc1_yr_atlas/snapshots/`；**收工做零删除证明**（旧内容 = 现内容的逐字节前缀，或有序子序列 + 每处只加不删）。
3. **每条勘误先回依据件核原文**（不许凭本卡转述改字）；**依据件里找不到的条目 ⇒ 标 `SOURCE_NOT_FOUND` 跳过并列出**，不许猜。
4. **`tools\verify_anchors.py` 改前改后各跑（须 323/323 ×2，原文落 `runs/`）**；若 `docs/re/ARCHITECTURE_ATLAS.md` 另有专属门禁脚本，同跑两次。
5. **⚠️ 35 个非 `.text` VA 的"移除"不是删行**：按台账原决议是**登记/降级**处置 —— 逐条先查当年决议原文（`_lead_baseline/` 或台账），**拿不准的条目归 `NEEDS_LEAD` 清单单列**，不执行。
6. **只读红线**：原版侧 `qc/.../scope/atlas_game/**`、`coverage_ledger/**`（CS2 在写）、`ra2youli/**`、`tools/**`、他人交付目录。
7. **写域**：`docs/re/ARCHITECTURE_ATLAS.md`（加注式）+ `out/re_work/zcode_live/W3_20261002/doc1_yr_atlas/`

## 做什么（四件）
1. **逐条落地** `E-W3-23/25/27/28/34` + R56 更正 + `CNetUtilEventSink` 更名（每条：找到出现点 → 加注 → 记 file:line/sha）。
2. **35 非 `.text` VA 按铁律 5 处置**（执行 / NEEDS_LEAD 分列）。
3. **零删除证明 + 门禁两跑**。
4. **反向验证**：抽 2 条已加注的，回依据件核"注记里的改前原文"逐字存在；抽 1 处**不应被改**的同名区域证明没动。

## 交付
`DOC1_REPORT.md`（§A 十节骨架；`[0]` 直答：落地几条/跳过几条+原因/NEEDS_LEAD 几条）· `landing_ledger.json` · `snapshots/` + `runs/` · `verify_doc1.py`（**EXIT=0 + `verdict tally` 行**）

## 回报 `[0]`
① 各条落地情况 ② 35 VA 分类 ③ 门禁两跑 ④ 反向验证 ⑤ `verdict tally` 原文

## 底线
> **宁可交"7 条落 5 条、2 条 SOURCE_NOT_FOUND、8 条 NEEDS_LEAD"，也不要交"全部落地"但依据件对不上。**
