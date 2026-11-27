# R172-EXEC — 只做五次机械测量并原样回报（不许改任何文件）

对象：/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R123_FACTINDEX_V551/FACT_INDEX.tsv
（TSV，五列表头，54 数据行，LF only，自校验 120540 字节、sha256 前 8 位 5d4981c8）

纪律：只读。每条任务用一条 python3 -c 或 python3 脚本命令一次输出该条全部数字。共 5 条命令，不许拆成多次单点命令。
回报格式：T1..T5 各一行，写实测数字；与下面给的期望值不符的，直接写不符并给实测值。末尾列 conflicts。

## T1 F35 两列的四个计数与长度
期望：statement 里「有一手代码权威」出现 1 次；limitations 里「定义有代码权威」出现 1 次、「都过强」出现 1 次、「无外部规范权威」出现 1 次；statement 字符数 1054、字节数 1751；limitations 字符数 3276、字节数 6020。
另报：statement 字段自身的 sha256 前 16 位。

## T2 F35 的撤回语境
期望：statement 里「缺一手权威」出现 1 次，且该处前后各 80 字符内含「已撤回」与「不得再写」两个串。
另报：该处出现位置的字符下标。

## T3 strict_panel.py 的判据位置
文件：/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py
期望：全文含方括号字面 token（左方括号 未证 右方括号）共 2 次，分别在第 14 行与第 78 行；第 76 行是 grade 等于 左方括号 已证 右方括号 的判断；第 78 行是 not in sem 形式。
另报：该文件字节数与 sha256 前 16 位。

## T4 F35 五项 evidence 的存活
期望：五项中只有含 COVERAGE 与 PANEL.md 的那一项不存在，其余四项在盘。
另报：四项各自字节数。

## T5 F24 的 4,417 计数
期望：statement 里字面 4,417 出现 6 次；limitations 里出现 4 次；两列合计 10 次。
另报：statement 里 4,416 出现次数（期望 1）与 737,517,286 出现次数（期望 6）。

## 收尾
每条给数字即可，不要给建议、不要写文件、不要引用我这边的结论。
