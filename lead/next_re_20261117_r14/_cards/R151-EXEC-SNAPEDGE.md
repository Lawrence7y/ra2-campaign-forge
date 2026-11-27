# R151-EXEC-SNAPEDGE · 快照边界与 F23 第二源的四点独立取证（exec）

## 角色与预算
执行员。只读，不改任何文件。预算 8 分钟，回合尽量少：**每条命令一次输出全部证据**，禁止把一个事实拆成多次单点命令。

## 背景（只给必要上下文，勿扩展到别处）
仓库根：/home/t628/projects/ra2-campaign-forge
主会话 R151 已用 _r151/r151a_recompute_snap.py（48 断言 0 FAIL）确认：FACT_INDEX v5.40 的 F23 两个证据项（COVERAGE/PANEL.md、R17_DELIVERY/DELIVERY_SUMMARY.md）现盘全失联，而二者在 11-22 快照 files_tier_A_snap2.tsv 里均有记录。
同时台账 lead/GOAL_THREE_TARGETS_20261018.md 第 40805/40818/40825/40845 行（事项 2 · R41）载明 R17_R41_RECOMPUTE/REPORT.md 正是 F23 四口径 458/291/293/1,196 的「第二源」，而该目录现盘已不存在、快照中仍有 3 件记录（REPORT.md 11,824 B / crosscheck.json 1,864 B / numbers.tsv 2,289 B）。

## 你要独立取证的四点（每点都要给命令与原始输出片段）
1. 快照清单里 R17_R41_RECOMPUTE 目录的全部成员及其字节数、mtime_ns，并回答：这批 mtime 是否落在 2026-11-21，即 R41 那一轮之后、11-22 快照之前。
2. 现盘全仓库（含 lead/ 与所有 _rNN 目录，排除 .git）是否还存在任何名为 REPORT.md 且字节数恰为 11824 的文件；用 find 或 python os.walk 给出命中数。若为 0，请明确说「0 件」，不要含糊。
3. 现盘是否还存在任何名为 coverage.tsv 或含 coverage 字样的 .tsv 文件（排除 .git）。给出完整命中清单。
4. 台账 lead/GOAL_THREE_TARGETS_20261018.md 里，字符串 R17_R41_RECOMPUTE 出现在哪些行号；字符串 R41_RECOMPUTE（不带 R17_ 前缀）又出现在哪些行号；两者差集是哪几行，并抄出这些差集行的原文前 120 字。

## 输出格式（严格）
在最终回复里给出四节，编号 1..4，每节包含：
- 命令（一行，可直接复制的 bash 或 python3 -c）
- 原始输出（截断到每节 20 行以内）
- 一句结论

最后给一行汇总：四点各自是「已确认 / 有出入 / 无法取证」。

## 纪律
- 卡面与回复中不要使用反引号。
- 不要修改任何文件。
- 不要调查 harness / server.py / re_guardian.py / re-tool 的源码。
- 不要重复我已给的数字当结论，你必须自己跑出证据。
