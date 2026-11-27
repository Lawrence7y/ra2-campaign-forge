# CARD R166-EXEC-1 · 独立复算 FACT_INDEX V545 的证据项存活普查（不得看主会话脚本）

## 你的角色
执行员（独立实现）。目标不是复核主会话的结论，而是**用你自己的实现**数出下面这组量，
让主会话能拿两套实现比对。**不要读 _r166/ 目录下的任何文件**（那是主会话的实现）。

## 只读输入（除这些外不要读别的）
1. FACT_INDEX 现版：lead/next_re_20261117_r14/R17_R117_FACTINDEX_V545/FACT_INDEX.tsv
   （TSV，5 列，表头 fact_id / statement / grade / evidence_paths / limitations，54 条事实）
2. 仓库根目录：/home/t628/projects/ra2-campaign-forge
   （evidence_paths 里的路径是 **Windows 反斜杠相对路径**，须 replace 成 / 后再相对仓库根拼绝对路径）

## 要生成的数（一条命令一次输出，别拆成多次试探）
A. 事实条数、grade 分布（逐档计数）。
B. evidence_paths 的**证据项总数**（按分号切，每项去掉末尾括号定位符，括号定位符里可能有
   中文与斜杠，注意取**最后一个左括号**之前的部分作为路径）。
C. 其中**现存**（os.path.isfile 为真）与**不存在**的项数。
D. **整行证据链全失联**的事实 id 列表（该项数 > 0 且全部不存在），并给出它们各自的 grade。
E. 有 ≥1 项失联的事实**条数**（不是项数）。
F. 失联项的 basename 频次表（前 8 名）。

## 交付格式（严格）
1. 一条命令（可写成 python3 - <<EOF ... EOF 或单文件脚本再跑）输出 A–F 全部数值，不写中间文件到
   _r166/。脚本本体可放 /tmp/r166_exec1.py。
2. 最后打印一行：RESULT fact_rows=<A 条数> grades=<按字典序的 档=数> items=<B> live=<C 现> missing=<C 缺>
   all_dead=<D 的 id 列表> all_dead_grades=<对应 grade> facts_with_missing=<E> top_basename=<F 前三>。
3. 报告正文只用纯文本/表格/路径，**禁止反引号**，禁止写结论性推断（例如「这说明 X 不可靠」），
   只报数与 id。
4. 如果你发现 evidence_paths 的切分有歧义（例如某段里含分号但不是分隔符），**如实列出那几段原文**
   并给出两种口径下的不同计数，不要二选一。

## 禁止
- 不读 _r166/、不读 _r165/、不读 R14_COMMON.md、不读 LEAD_LOCK（避免被主会话口径污染）。
- 不修改任何文件；只在 /tmp 下写自己的脚本。
- 不做跨家族审计式评价，只报数。
