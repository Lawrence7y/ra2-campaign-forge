R102 执行卡 · 门禁 C11 三处「永远通过」的行为级取证（与主会话独立实现）

## 你的任务

在本机（t628，Linux）对 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py
的「C11 是否真回跑」判据做**独立行为级取证**。要求：自己写脚本、自己造沙箱、自己数，不要读
主会话 _r102 目录下任何文件（那里已有主会话的答案；读了就失去独立性）。

## 已知背景（都是已实测的事实，可作前提）

1. DISC_RECHECK.tsv 有 31 行数据 + 1 行表头，7 列。第 7 列「立条之后是否回跑过」取值只有两类：
   以「有」开头 17 行、以「无」开头 14 行。
2. DISC_UNVERIFIABLE.tsv 有 12 行数据（冻结档），第 1 列是纪律号。
3. check_disc.py 的 C11 逻辑大意：第 7 列以「无」开头者直接计入 claims-none 并 continue；
   以「有」开头者调 recheck_verify.verify_recheck_line()，失败才 FAIL，但若该 id 在冻结档里则
   计入 frozen-unverifiable 而不 FAIL。
4. 门禁改动文件是 check_disc.py 与 DISC_RECHECK.tsv 两处，都是被 C7/C10 真跑校验的。

## 要你回答的四个问题（每个都要有可复跑的脚本与数字）

Q1 分桶：31 行精确分成哪三桶（真可 FAIL / 冻结豁免 / 写无豁免）？给三桶的 id 列表与规模。
   并回答：究竟多少行的 C11 判定**在结构上不可能变成 FAIL**？

Q2 洞 A「冻结摘帽」：把 DISC_UNVERIFIABLE.tsv 清空（只留表头），并同步把 check_disc.py 里的
   FREEZE_SHA256 常量改成清空后那份文件的 sha256（模拟 Lead 显式改常量的合法路径），
   门禁是否立刻 FAIL？FAIL 的 C11 行集合是否**恰好**等于原先冻结的 12 个 id？

Q3 洞 B「写无即免检」：取一行原本声称「有」且能 FAIL 的行（例如 id 3），把它第 7 列改成
   以「无」开头，其余一个字不动，门禁是否立刻从 FAIL 变 PASS？关键：必须让这次变异**只**
   打到 C11 —— 如果你同时把产物路径改坏，C7 也会 FAIL，那就不是唯一对应，结论无效。
   （提示：id 3 的产物 R17_R61_FACTINDEX_V58/anchor_check.txt 里有一条 discipline=3 的
   自述行；你可以复制该产物、只删掉这一行、把第 5 列路径指到副本，这样 C7 的 grep 锚还在。）

Q4 恒量 C11_LANDABLE：check_disc.py 第 240 行左右有 C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17,
   22, 26, 27, 28}。请用 AST 统计这个常量在脚本里被 Load 了几次；再回答：它与 Q1 的三桶
   是否一致？具体说，LANDABLE 里有多少个 id 落在「写无豁免」桶里（即永远不可能 FAIL）？

## 硬要求

- 沙箱：不要在真树上做变异。做法建议：在 /tmp 下建沙箱根，把真树的每个顶层条目 symlink 过去，
  只对 check_disc.py / DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv 三个文件用真实副本覆盖。
  注意：产物路径是相对 ROOT 的，顶层条目（例如 _r94/）也必须链上，否则 C7 会 FILE_MISSING。
- 必须自带正反控，并显式写出「正控先绿、反控才携带信息」的理由。至少要有：
  原样沙箱必须 exit 0；每个变异必须给出「有判据」与「无判据」两个方向的对照。
- 所有断言要有名字，末尾打印 n_checks 与 n_fail，并把结果写成 json。
- 严禁修改真树任何文件。只读真树，只写 /tmp 与你的产物目录。
- 产物写到 lead/next_re_20261117_r14/_r102_exec/ 下（新建），命名 VERDICT102.md + 脚本 + json。
- VERDICT102.md 里给一张表：Q1 三桶 id 列表 / Q2 FAIL 集合 / Q3 翻转前后 exit 码 / Q4 AST Load 次数。
- 最后写一节「我不确定的部分」，如实列出。

## 边界

- 不要碰 LEAD_LOCK / R14_COMMON / GOAL_THREE_TARGETS / STATUS_BOARD（那是主会话的写入区）。
- 不要分析 harness / server.py / re_guardian / re-tool 的源码。
- 不要读 _r102 目录（主会话产物），保持独立。
