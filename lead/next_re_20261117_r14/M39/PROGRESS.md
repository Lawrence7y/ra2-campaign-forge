# M39 PROGRESS — 合并员 M39（S03_C4 + S09_KPROVED 共 15 行提级）

- 时点：2026-11-19（Asia/Shanghai）。写域仅 COVERAGE\{coverage.tsv,CONFLICTS.tsv,PANEL.md}、M39\、_hygiene\ 下 M39 备份；未动台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\，未 git commit，未建 venv / pip install。
- 输入（只读）：`S03_C4/coverage_delta.tsv` 7 行 + `_audit/VERDICT.md`（PASS，7 行全白名单）；`S09_KPROVED/coverage_delta.tsv` 8 行 + `_audit/VERDICT.md`（PARTIAL，黑名单空、8 行四环全成立）。
- 规则执行：15 行仅改第 5 列 grade `[静态推断]`→`[已证]` 与第 6 列 evidence_path（指向各自 _audit/VERDICT.md 逐行裁决 #行号）；name / subsystem / one_line_semantics 三列逐字节不动；CONFLICTS 追加 4 行只登记不裁决、不设 conflict=1；PANEL 只动指定行 + 新增 M39 节。
- 规则 3 核盘：15 行改前 grade 全为 `[静态推断]`，逐行唯一命中，无一例外 ⇒ 未触发停止条件。

## 必做自检
(a) coverage.tsv 行数：改前 18,431 数据行（含表头物理 18,432）→ 改后 18,431（物理 18,432）；entry 增删 0。PASS
(b) 第 5 列 grade 直方图（TAB 切列，只读第 5 列）：改前 [已证] 1,372 / [静态推断] 6,035 / [未证] 11,024 → 改后 [已证] 1,387 / [静态推断] 6,020 / [未证] 11,024；和均 18,431。PASS
(c) conflict==1 计数（第 8 列）：改前 254 → 改后 254（CONFLICTS 4 行不改 coverage 的 conflict 列）。PASS
(d) 15 行改后逐行 grep（第 5 列=[已证] 且 name/subsystem/semantics 与改前逐字节相同）：15/15 命中，0 差异。PASS
(e) SHA-256：
    coverage.tsv  改前 8b501ae84a68ed6daf0d3407bf8ea67d635ec106596d151de45af950e421af22
                  改后 fc7c6eb6f6d0931e117c1bec5b8e37af387d8ec43c7573eb1ca3166db87d3dc5
    CONFLICTS.tsv 改前 d8acd8d12927596b569c9fcaa9e01e7653de8b5ff34ebd693313da78a4071d85
                  改后 9a8ca7b9e1805a9d7444f2b4fcca7c376b39b6b9093c216254e366ffaf1adb49
    备份：_hygiene\coverage.M39.bak（SHA=8b501ae84a68ed6daf0d3407bf8ea67d635ec106596d151de45af950e421af22）、_hygiene\CONFLICTS.M39.bak（SHA=d8acd8d12927596b569c9fcaa9e01e7653de8b5ff34ebd693313da78a4071d85），与改前逐字节一致。

## 其他核算
- 15 行全在 atlas（function_atlas.tsv 逐 entry 各命中 1 次）⇒ atlas 内 [已证] 1,367→1,382；atlas 外 5 行不变（1,387−5=1,382）。
- S03 proved 17→24/194=12.37%（门槛 97，差 73）；S09 proved 69→77/1051=7.33%（门槛 526，差 449）；atlas 内 proved 1,367→1,382/12,916=10.70%；named 各列不变，其余 19 个子系统行一字不动。
- CONFLICTS.tsv 数据行 472→476（物理 473→477）；4 行 field=name、status=OPEN:疑似类归属错误，来源 S09_KPROVED\_audit\VERDICT.md §3；不改 coverage subsystem/name，conflict=1 仍 254。
- PANEL.md：第 1 行流水追加 M39 段；「两个量纲」全表 [已证] 改 1,387；「三分母」全表/atlas 内 [已证] 改 1,387/1,382；S03 行 proved 24/12.37%、S09 行 77/7.33%、TOTAL 行 1,382/10.70% 及差距说明按重算值写；M37 段前新增「M39 并表说明」。
- 格式铁规：表头逗号 8 列、数据行 TAB 8 列（18,431 行宽度全部为 8）；grade 只读第 5 列；表格未用逗号切分。
- 交付：M39\PROGRESS.md、M39\MERGE_LOG.tsv（15 行 coverage + 4 行 CONFLICTS + PANEL 改动逐行）。
