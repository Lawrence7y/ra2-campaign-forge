# R180 执行卡：复核 facts_floors.py 新增 D10（本卡禁用反引号，凡命令一律单行）

## 背景（全部已实测，不要重做取证，只做逐值复核）
主会话本轮给 _r160/facts_floors.py 增加检查项 D10：当前版指针文件 FACT_INDEX_CURRENT.md 必须与本文件 CUR_SHA256 / TOTAL_BYTES 及 CUR 实物 sha 一致。补丁前该指针被 check_disc.py / gate_runner.py / facts_floors.py 三者读取次数各为 0。

## 要求：用一条命令输出全部证据（禁止拆成多次单点命令）
在 /home/t628/projects/ra2-campaign-forge 下执行，一次完成：
1) 统计三个门禁文件各自含 FACT_INDEX_CURRENT 的次数与字节数与 sha256 前16位：
   python3 -c "import hashlib;fs=['_r160/facts_floors.py','_r161/gate_runner.py','lead/next_re_20261117_r14/check_disc.py'];[print(f,open(f,'rb').read().count(b'FACT_INDEX_CURRENT'),len(open(f,'rb').read()),hashlib.sha256(open(f,'rb').read()).hexdigest()[:16]) for f in fs]"
2) 打印 facts_floors.py 里 D10 块的全文行号范围与 CUR_SHA256 / TOTAL_BYTES / MASTER_SHA256 三行：
   grep -n "D10\|^CUR_SHA256\|^TOTAL_BYTES\|^MASTER_SHA256\|^EXPECT_CUR" _r160/facts_floors.py
3) 打印指针文件四个字段：grep -n "版本目录\|相对路径\|sha256\|字节数\|行数" lead/next_re_20261117_r14/FACT_INDEX_CURRENT.md
4) 实跑事实层门禁并把 D10 相关行与 exit code 一起打出：
   timeout 300 python3 _r160/facts_floors.py; echo EXIT=$?
5) 实跑 gate_runner 只取 SUMMARY：timeout 500 python3 _r161/gate_runner.py | tail -8

## 必须逐条回答（数字须来自上面那条命令的实测输出，不得引用本卡）
Q1 三个门禁对 FACT_INDEX_CURRENT 的读取次数各是多少？与「三者皆 0」是否逐值相符？
Q2 facts_floors.py 当前字节数与 sha256 前16位是多少？
Q3 D10 块出现在哪个行号区间？它是否位于 if fails 汇总语句之前？
Q4 指针四字段（版本目录/相对路径/sha256/字节数）实测值，与 facts_floors.py 的 CUR_SHA256 / TOTAL_BYTES 是否逐字相等？
Q5 facts_floors.py 实跑 exit code 与 D10 打印行内容？
Q6 gate_runner 的 G1/G2/G3 汇总行逐字？
Q7 你做一条反控：把指针文件复制到 /tmp 并在副本上改 sha 最后一位，用 --ignore-pin 之外的方式证明 D10 会 FAIL（可先把生产指针临时改坏再恢复，但必须保证恢复后 sha256 回到 ad5c1db9 开头，并在回答里给出恢复后的实测 sha256）。
Q8 是否存在「D10 能被静默绕过」的路径？只答你实测到的，不要推测。

## 纪律
- 只读 + /tmp 副本。不要修改 _r160、_r161、check_disc.py、FACT_INDEX.tsv、FACT_INDEX_CURRENT.md 的最终状态。
- 若你临时改了生产指针，必须在回答前恢复并给出恢复后实测 sha256。
- 全部数字标出处（哪个命令的第几行）。不确定就写不确定。
