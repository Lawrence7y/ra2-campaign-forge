# r181a 取证卡：主门禁 check_disc.py 对事实层（facts_floors / FACT_INDEX_CURRENT）的覆盖计量

## 上下文（已由主会话实测，勿重复推翻，但必须独立复算）

磁盘路径 root = /home/t628/projects/ra2-campaign-forge

- 主门禁 lead/next_re_20261117_r14/check_disc.py 现 1059 行 / 57837 B
- 事实层门禁 _r160/facts_floors.py 现 478 行 / 26147 B
- 串门 _r161/gate_runner.py 现 398 行 / 20268 B
- 当前版指针 lead/next_re_20261117_r14/FACT_INDEX_CURRENT.md
- 当前台账 lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv 133310 B

R180 登记的事实：check_disc.py 对 facts_floors 与 FACT_INDEX 的引用次数各 0。

## 你要做的事（一条命令输出全部证据）

用一条 bash 命令（可内含一个 python heredoc）完成下列 Q1..Q6，输出表格化文本。
禁止分成多次单点命令；禁止修改任何生产文件（只读）。禁止写 __pycache__。

Q1 计数：在 check_disc.py 源码中分别统计下列子串出现次数（区分大小写）：
    facts_floors / FACT_INDEX / FACT_INDEX_CURRENT / _r160 / _r161 / gate_runner
    同时统计「任何以 .py 结尾的字符串字面量路径」被 open()/read()/subprocess 读取的条数。

Q2 反向正控：同样六个子串在 _r161/gate_runner.py 与 _r160/facts_floors.py 中各自的出现次数。
    正控必须为正（否则说明计数方法本身坏了），并明确指出哪个文件充当正控。

Q3 现盘 sha256 与字节数（全部给全文 64 位 hex）：
    check_disc.py / facts_floors.py / gate_runner.py / FACT_INDEX_CURRENT.md / V563/FACT_INDEX.tsv

Q4 三门的当前退出码：分别运行
    python3 check_disc.py            （cwd = lead/next_re_20261117_r14）
    python3 _r160/facts_floors.py    （cwd = root）
    python3 _r161/gate_runner.py     （cwd = root）
    给出各自 exit code、输出中行首为 FAIL 的行数、最后一行内容。每条附 timeout。

Q5 覆盖语义：读 check_disc.py，回答「它的 18 个检查项（C1..C18）里，有哪一项会因 FACT_INDEX.tsv
    内容缩水/改 grade 而 FAIL？」给出 0 项或若干项，并指出依据行号。

Q6 分辨力反证：把 FACT_INDEX.tsv 复制到 /tmp，用 sed 把 FACT_INDEX.tsv 里 F24 那一行的 grade
    由 [已证] 改成 [流程]（只改副本），然后以副本路径作为 argv 跑 facts_floors.py，
    记录 exit code 与 FAIL 行数；再以同样副本路径跑 check_disc.py（不改生产），记录 exit code。
    结论只允许写「哪一门看得见、哪一门看不见」。

## 交付格式

- 全部证据原文贴进 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/_r181/r181a_exec.txt
- 报告正文 12 行以内，只给结论 + 关键数字；不得使用「大概/应该/估计」。
- 若任何一项与你预期不符，如实写出实测值，不要为迎合卡面而改数。
- 禁止任何写入生产树的操作（/tmp 除外）。
