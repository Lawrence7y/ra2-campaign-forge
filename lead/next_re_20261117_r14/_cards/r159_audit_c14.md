ROLE: audit （跨家族只读复核 · 禁止执行类工作）

任务：对下列五条待裁结论做只读复核，逐条判「成立 / 不成立 / 表述需改」，并给出你自己的复算数字。
只读，禁止写入任何文件。禁止调用 re-tool 派发子代理。仓库根 /home/t628/projects/ra2-campaign-forge。

被检对象文件：
F1 = lead/next_re_20261117_r14/check_disc.py
F2 = lead/next_re_20261117_r14/DISC_RECHECK.tsv （表头 1 行 + 31 数据行，每行 7 列）
F3 = lead/next_re_20261117_r14/DISC_UNVERIFIABLE.tsv
F4 = lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv （表头 fact_id statement grade evidence_paths limitations）

待裁结论：

C1 关于 F1 的 C14_ROW_SHA（31 条 id 到 sha256）：
   口径定义：C14 口径 = sha256(第1列 制表符 第2列 制表符 第3列 制表符 第4列)；C7 口径 = sha256(第1列 制表符 第5列 去空白 制表符 第6列 去空白)。
   命题：这 31 条里有 30 条是真正的 C14 口径哈希，只有 id 20 那条既不是 C14 口径也不是 C7 口径，
   而是「第 20 行在第 6 列写成 GATE_VER = 'R157' 时的 C7 口径哈希」。请复算并判。

C2 关于 C14_ROW_SHA 的后果：
   命题：F1 里 C14 漂移诊断分支只在 C14_TEXT_SHA256 不匹配时才跑；因为那唯一错误的一条钉在 id 20 上，
   所以一旦 C14_TEXT 真的漂移，诊断会把 id 20 报成漂移，而 id 20 其实一个字没改。
   请复算「用当前 F2 与当前钉，在不改动任何行的前提下走一遍 C14 漂移诊断」会列出哪些 id，并判。

C3 关于 C7 形态死分支：
   命题：F2 的 31 行里，第 6 列断言形态按首前缀统计为 grep= 24 行、grepcount= 3 行、rows= 4 行，
   而 exists / bytes= / none 三种形态各 0 行。请复算并判。注意需要一个正控说明统计器本身在工作。

C4 关于 F4 的 F08：
   命题：F08 第 4 列有两项证据路径，第一项在盘，第二项指向 R17_LEDGER_1064 目录，而盘上
   lead/next_re_20261117_r14/ 下只存在 R17_LEDGER_1063，故第二项必然失联。请复算并判。

C5 关于门禁对 F4 的覆盖：
   命题：F1 全文不含字符串 FACT_INDEX，即门禁完全不读 F4，所以 F4 的任何字段改动都不被门禁看见，
   这是一个结构性缺口，不是漏配置。请复算并判。

输出要求：C1 到 C5 逐条给出「判定 + 你的复算数字」，最后一行打印 VERDICT_DONE。
