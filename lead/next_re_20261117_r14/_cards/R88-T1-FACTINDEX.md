# 卡 · R88-T1 · 跨家族执行员（hy4 家族）：独立复算 FACT_INDEX 四条的可核验性

## 〇 · 你是谁，写哪里
你是执行员，只读 live 数据，唯一写目标是 lead/next_re_20261117_r14/R17_R88_T1_FACTINDEX/（已存在）。
禁止改 FACT_INDEX.tsv、R14_COMMON.md、LEAD_LOCK、GOAL_THREE_TARGETS_20261018.md、STATUS_BOARD.md、
BOARD_ARCHIVE.md、以及任何 live 文件。

## 〇之二 · 磁盘纪律（上一轮出过两次事故，必须遵守）
禁止复制 live 树。若某个检查确实需要临时工作区，只能建在 /tmp/r88t1_ 下，
并且复制时显式排除以下目录：_r87、_r88、R17_LEAD_BASELINE、.git、ra2bench、re_atlas。
你的产物目录 R17_R88_T1_FACTINDEX 本身绝不可作为复制源被递归复制。
产出总量不得超过 20 MB。超出即为失败。

## 一 · 背景
项目根 /home/t628/projects/ra2-campaign-forge。
表文件：lead/next_re_20261117_r14/R17_R103_FACTINDEX_V531/FACT_INDEX.tsv
它是 5 列 TSV，表头为 fact_id statement grade evidence_paths limitations，共 54 条数据行。
evidence_paths 列用分号分隔多条路径，每条形如
  lead\next_re_20261117_r14\COVERAGE\PANEL.md(M86 / M93)
即路径后可能跟一个括号，括号里是段号或锚点。路径分隔符是反斜杠。

本库是部署在 t628 的精简库，不是完整树。已知有一批路径在盘上不存在。

## 二 · 四条要你独立复算的命题

请自己写脚本，不要抄我的结论，不要 import 我的脚本。

命题 A（可核验率）：把 evidence_paths 全部拆开，去掉括号部分，反斜杠转正斜杠，
逐条判断文件是否存在。预期：引用总数 171 条、存在 128 条、缺失 43 条、
缺失路径去重后 16 条、涉及的 fact 去重后 34 条。
请你独立算出这四个数，并核对 128 加 43 是否等于 171。

命题 B（哪些 fact 零可核验证据）：找出所有 evidence_paths 里每一条都不存在的 fact。
我预期是 F23 和 F35 两条。请独立确认，并额外报告：是否存在 evidence_paths 为空
或只含空格的 fact。

命题 C（F24 语料清单闭合）：下面五个清单文件，各自算出数据行数与 bytes 列求和：
  R17_R88_T1_SEMDEF/tier_final.tsv
  R17_R96_TIER_FINAL_4413/tier_final_4413.tsv
  R17_R97_TIER_FINAL_4413B/tier_final_4413b.tsv
  R17_R99_TIER_FINAL_4416/tier_final_4416.tsv
  R17_R101_TIER_FINAL_4417/tier_final_4417.tsv
都在 lead/next_re_20261117_r14/ 下。把它们与你读到的 F24 正文里声明的
件数与字节数逐个对照，报告哪些对得上、哪些对不上。注意第一个文件的表头可能不同，
请先打印表头再决定怎么取列，不要假设列位置。

命题 D（F29 的字节断言）：用 python3 直接读 ra2bench/gamemd.exe 的原始字节，
ImageBase 为 0x400000，节表如下：
  .text   VA 0x1000   raw 0x3e0000 @ 0x1000
  .rdata  VA 0x3e1000 raw 0x31000  @ 0x3e1000
  .data   VA 0x412000 raw 0x6c000  @ 0x412000
  .detour VA 0x793000 raw 0x3000   @ 0x497000
请自行读 PE 头核对这张表是否正确（可用 python3-pefile），不要直接相信我给的。
然后：
  D1 读出 VA 0x7E11C8 处的 16 字节，按 4 字节小端解出 4 个 dword。
  D2 读出 VA 0x6C2AC0 处的 16 字节。
  D3 读出 VA 0x7F3D98 处的 16 字节，同样解 dword。
  D4 把 D1 的第 1 个 dword 当地址，读那里的 8 字节，报告字节。
  D5 判断：VA 0x6C2AC0 处是否为 call [0x7E11C8] 形态（即 FF 15 后跟 4 字节地址 0x7E11C8）。
请把每条读到的原始十六进制都打印出来，不要只给结论。

## 三 · 你要额外找的反例
挑上面任一条，试着自己构造一个能推翻它的情形。找不到就明说找不到。

## 四 · 输出
写 REPORT.md 到 R17_R88_T1_FACTINDEX/，包含：
- 四条逐条判定（成立 / 不成立 / 部分成立），附你自己算出的数字
- 你打印的原始字节
- 你找到的反例，或明说没有
- 你无法判定的项
不要客套话。数字必须自己跑。卡面不得出现反引号，你的报告里可以用。
