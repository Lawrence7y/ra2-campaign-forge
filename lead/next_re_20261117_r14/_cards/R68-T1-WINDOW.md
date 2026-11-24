# R68-T1 · 轮次窗口表的独立复算（只读，不改任何盘上文件）

## 背景（一句话）
check_disc.py 的 C11 有 5 条 FAIL，原因串是「R4 at outside R055 window」。窗口表在 recheck_verify.py 的 _ROUND_ROWS 里，硬编码 HHMMSS。

## 你的任务（只读，严禁写/改/删任何文件）
1. 读 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/recheck_verify.py 里的 _ROUND_ROWS。
2. 读目录 R17_LEAD_BASELINE 下所有文件名形如 STATUS_BOARD*.before_rNN_HHMMSS.md 的快照（含 add 变体与 .bak）。
3. 逐轮列出「该轮的所有快照时刻」，并回答两个只能用数据回答的问题：
   Q1 快照 before_rNN 的内容里，最后一个 ## 段是第几轮？（用 grep 抓 ^## .*R17 第 N 轮 自己数，至少抽样 r54 r55 r56 r57 r66 五个文件）
   Q2 由此判断：第 N 轮的「工作时段」应定义为
       甲 [before_rN, before_r(N+1))   还是
       乙 [before_r(N-1), before_rN)   还是
       丙 [close(N-1), close(N))，其中 close(N) = 第 N 轮全部快照时刻的最大值
   用 Q1 的实测内容判据给结论，不要凭直觉。
4. 用你选的判据，把 r35 到 r67 的窗口逐条算出来，写成一张表（轮次 / 起点 HH:MM:SS / 终点 HH:MM:SS / 依据文件名）。r41 无快照要显式写 NO-SNAPSHOT。
5. 用你算出的表去验这 5 条自述行的 at 是否落在窗口内：
   discipline=3 at=2026-11-22T17:39:19+08:00
   discipline=4 at=2026-11-22T17:40:02+08:00
   discipline=22 at=2026-11-22T17:39:19+08:00
   discipline=27 at=2026-11-22T17:39:19+08:00
   discipline=28 at=2026-11-22T17:39:19+08:00
6. 指出当前盘上 _ROUND_ROWS 与「按你判据应有的表」逐条差在哪：只列差项，给行号。

## 反控（必须做，不做视为未完成）
- 反控 A：把你算的 r55 窗口起点人为推后 1 小时，重新验那 5 条，必须全部落到窗口外。若仍全部在内，说明你的验证代码没在真判。
- 反控 B：把所有窗口都放大成 [00:00:00, 23:59:59]，5 条必全过 —— 这是「放水」方向，用来证明你的验证代码确实会区分。

## 交付
REPORT 末尾必须给：Q1 抽样结果表、Q2 结论与依据、完整窗口表、5 条验算结果、与盘上表的差项清单、反控 A/B 的实际输出。
禁止：改任何文件、写任何 .md 到工作目录以外、使用 re-tool。全部结论必须带「盘上读到什么」的原文引用（file:line）。
