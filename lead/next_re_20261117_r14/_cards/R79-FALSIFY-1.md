# R79-FALSIFY-1 — 对「34/36 是 mtime 口径的数」这条结论的异族反审

## 你是谁

R17 子代理，家族 hy4，角色审计员。只写 _r79/audit/ 下两个文件：falsify_r79.py 与 FALSIFY.md。不得修改任何既有文件。卡面与本产物都不要出现反引号。

## 被审的主张（主会话 R79 本轮给出，共四条）

1. R74 写下的跨源旁证 34/36（无旁证 0x47C432 / 0x47C440）只在 mtime 当时钟时成立；用 btime 当时钟会得到 36/36。
2. 把五个「报告过这件事」的文件整体移出语料后，仍是 34/36，那两个候选值的独立旁证数为 0。
3. 恢复后的 R14_COMMON 副本里，0x47C432 与 0x47C440 各出现 4 处；其中 3 处落在 §2.79 段内、1 处在段外（段外那处是原始缺陷站点，由 0x00 重建）。
4. btime 不能当内容时钟：存在文件 btime 早于时钟 A 而 mtime 晚于时钟 A（就地改写），COMPACT_STATE.md 是其中之一且正文确实含 R78 段。

## 你要做的四件事（每件只给 HOLDS 或 BROKEN，不许「基本成立」）

A. 自己写命中函数，复算主张 1。时钟 A 取 lead/next_re_20261117_r14/_r74/forensic_nul_r74.log 的 mtime。候选值从 live R14_COMMON.md 的 0x00 站点重建，规则与 R74 相同：0x00 后紧跟的字母数字串前补字符 0，去重，应得 36 个。btime 口径直接按 btime <= A 筛。mtime 口径按 mtime <= A 筛，四个受约束文件用 R17_LEAD_BASELINE 下以 R74.before 开头、以 004604.md 结尾的备份顶替（R14_COMMON / LEAD_LOCK / GOAL_THREE_TARGETS / STATUS_BOARD 各一份，其中 GOAL_THREE_TARGETS 的备份文件名里写的是 LEDGER，自己按内容前缀对齐）。报两个口径各得几几。
B. 复算主张 2：在 mtime 口径的语料里移除这五个文件后重算。五个文件是 R14_COMMON.md、lead/LEAD_LOCK、lead/GOAL_THREE_TARGETS_20261018.md、STATUS_BOARD.md、COMPACT_STATE.md。
C. 复算主张 3：把 live R14_COMMON.md 里的 0x00 全替换成字符 0 得到恢复副本，数那两个 token 各出现几次；再数其中多少个落在 §2.79 三级标题之后（用字节偏移比大小即可，标题串是 井号 井号 空格 2 点 79）。另外报出：4 处里有几处的原字节在 live 里是被 0x00 覆盖的（即 live 里该位置不是这个 token 的首字符）。
D. 复算主张 4：找出 mtime 偏口径语料里所有 btime <= 时钟 A 但 mtime > 时钟 A 的文件，报个数与名字；再核 COMPACT_STATE.md 正文里是否真的含 R78 段标记（字符串 井号 井号 井号 空格 R78）。

## 反审的硬要求（这一条最重要）

如果你四条全部给 HOLDS，你必须再回答一句：**这四条里哪一条最容易被一个改动过的判据造出假 HOLDS？** 给出那个判据的具体位置与它会怎样骗过你。给不出就写「给不出」，不许编。

## 输出

- _r79/audit/falsify_r79.py —— 可复跑，最后一行打印自测项数与 FAIL 数，且每个主张单独打印 HOLDS 或 BROKEN。
- _r79/audit/FALSIFY.md —— 一节对一条主张，给实测数字与你自己的命令/路径；末尾写那一条硬要求的答案。

## 纪律

- 不许读 _r79/ 下除你自己写的文件以外的任何文件，尤其不许读 _r79/clock_r79.py 与 _r79/exec/ 下任何文件。你必须自己从字节算。
- 不许引用任何既有报告里的数字当结论。
- 没跑过的数一律写「未测」。
- 步骤就五步：建语料、重建候选值、跑 A 与 B、跑 C 与 D、写两个文件。
