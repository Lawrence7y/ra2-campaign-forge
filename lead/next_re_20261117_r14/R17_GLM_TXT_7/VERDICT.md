自报 provider 与 model 原始串：`bigmodel-api`｜`GLM-5.3-Flash`（原始串 `bigmodel-api/GLM-5.3-Flash`）

# 卡 R17-GLM-TXT-7 · 判定（8/8，只做文字一致性 + 表内算术）

#1 AGREE — `R17_R41_RECOMPUTE/REPORT.md` L48–51：汇总表报 `[已证] 1,654`/`[静态推断] 5,875`/`[未证] 10,969`、`2d 三档和 18,498`；加和校验 1654+5875+10969=18498 成立。

#2 AGREE — 同报告 L55–58：`4a ④口径A 458`/`4b ④口径B 291`/`4c 宽口径W 293`/`4d 完全无④ 1,196`；加和校验 458+1,196=1,654 成立（L77「458 + 1,196 = 1,654 闭合」亦同）。

#3 AGREE — 同报告 L61–63：`5a R_OK 863`/`5b R_MISSING 0`/`5c R_TRACE_ONLY 791`；加和校验 863+791=1,654 成立（L78「R_TRACE_ONLY(791) + R_OK(863) = 1,654」亦同）。

#4 AGREE — 同报告 L66：「6b｜权威 `strict_panel.py` 实跑｜**1,331**（TOTAL `proved_strict_n` 列）｜✅ 两实现一致」，与 strict 1,331 相符（L79「完全一致」）。

#5 AGREE — 同报告 L79：「`strict_panel.py` 的 `named_strict=1372` 是**另一列**（命名口径），不是 strict 已证数，引用时不得混淆」，L107 再次重申；已明确提醒 1372 ≠ 1331。

#6 AGREE — `R17_R40_FACTINDEX_V3/FACT_INDEX.tsv` 实读 27 行 = 1 表头 + 26 数据行，`fact_id` 自 `F01` 至 `F26` 逐行连续、无缺号无重复。

#7 AGREE — 同文件 F22–F25 的 `limitations` 列四行均非 `—`：F22「三项限定不可拆；引 1,654 必须同引①②③。」、F23「口径必须写明；宽松正则 /direct call/ 会多计 10 行…」、F24「R_OK 863 是『至少一个路径解析到真实文件』…」、F25「界向不可省；对外声明按 D-44…」。

#8 AGREE — `lead/LEAD_LOCK` L1123（AH1，AH 段）：「⚠️ 口径提醒：archive 的「213,523」是字符串长度（字符数），不是字节数；字节是 344,755。」

额外只读检查（不计入 8 项）：侧效**已披露** — 同报告 §4.2 L99：「实跑 `strict_panel.py` 会在**它自己的目录** `RULING_R15_20261119/work/` 重写 `strict_panel.tsv` 与 `strict_panel.json`」。

OVERALL: CONSISTENT
