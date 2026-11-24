# W81 DISAGREE

与任务书无实质分歧——任务 prescribed 的"恢复全包 rglob + expected_added 显式加 docs"正是被采用并实测通过的方案。记录两处技术裁量（均非路线分歧）：

1. **未采纳"可选增强"（再加一条包根白名单 check）**。理由：恢复全包后，`S4_8e` 的 `added == expected_added`（列表精确相等）已经是"包根下除白名单外无其它新文件"的显式断言——白名单即 `expected_added` 本身（现在含 docs 条目）。再写一条语义重复的 check 只会：① 断言数 844→845，偏离 Lead 要求对齐的 W77 基线口径；② 在 STRAY 场景下与 S4_8e 同时报同一事实。最小正确改法 = 只动收集器与期望集合。
2. **S4_8e desc 文本保留 "(3 changed + 2 added)" 旧计数**。任务红线"三条原有 check 文本逐字不动"优先于描述新鲜度；计数语义（源码面 added）已在收集器上方注释说明。若归属方要更新 desc，属一行文本改动，不触判定。
3. （顺带记录）首次 S4_8 单跑 FAIL 过一次：`expected_added` 初版未按 `sorted()` 字典序排（docs 放了末尾），列表精确相等如实 FAIL——这不是守护误报，是白名单书写顺序错误，已修正。过程留存于 PROGRESS.md。
