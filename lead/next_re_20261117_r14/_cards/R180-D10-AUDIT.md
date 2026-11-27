# R180 跨家族审计卡（只读复核，本卡禁用反引号）

## 待审主张（主会话 R180 交付）
主张 A：补丁前，_r160/facts_floors.py、_r161/gate_runner.py、lead/next_re_20261117_r14/check_disc.py 三者对文件名 FACT_INDEX_CURRENT 的读取次数各为 0，故该指针静默漂移时三门全绿。
主张 B：本轮给 facts_floors.py 新增 D10，判据是三条相等：(1) 指针 sha256 == 本文件 CUR_SHA256；(2) 指针字节数 == 本文件 TOTAL_BYTES；(3) 指针 sha256 == CUR 文件现盘实测 sha256。文件缺失亦 FAIL。
主张 C：D10 不引入新 pin 常量，故 D9 的 MASTER_SHA256 不应变化。
主张 D：篡改工况下 D10 会 FAIL，且日志里能用 sha 末位分辨（首版只打前16位，末位篡改在日志中与基线逐字相同，已改为打全文）。
主张 E：D10 受 --ignore-pin 约束，与 D0 同族，可在自测中隔离。

## 要求：一条命令取证（禁止拆单点）
cd /home/t628/projects/ra2-campaign-forge 后一次完成：
1) for f in _r160/facts_floors.py _r161/gate_runner.py lead/next_re_20261117_r14/check_disc.py; do echo $f $(grep -c FACT_INDEX_CURRENT $f) ; done
2) grep -n "D10\|^CUR_SHA256\|^TOTAL_BYTES\|^MASTER_SHA256" _r160/facts_floors.py
3) sha256sum _r160/facts_floors.py lead/next_re_20261117_r14/FACT_INDEX_CURRENT.md lead/next_re_20261117_r14/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv
4) timeout 300 python3 _r160/facts_floors.py | tail -6 ; echo EXIT=$?
5) ls -la lead/next_re_20261117_r14/R17_LEAD_BASELINE/facts_floors.py.before_r180_D10_*.bak

## 必须逐条裁定（成立 / 部分成立 / 不成立，并给实测数字）
Q1 主张 A 是否成立？三者计数实测各为几？
Q2 主张 B 的三条判据是否都在源码里真实存在且各自能 FAIL？指出它们的具体行号。
Q3 主张 C：MASTER_SHA256 实测值是否仍是 eab67034 开头？D10 是否真的没有进入 D9 的 payload 拼接？
Q4 主张 D：日志现在打的是全文还是前16位？请从实际输出判断。
Q5 主张 E：--ignore-pin 下 D10 是否真的被关掉？如何从源码判断（给行号）？
Q6 独立指出你认为 D10 仍然存在的漏洞或错误判据（至少一条，若确无则明确写无）。特别注意：D10 是否会被「同时改指针与常量」绕过？这是不是所有指纹类门禁的共同上限？
Q7 本轮是否有任何一处主张属于「把应然数当实测」？逐条给出你判断依据。

## 纪律
只读。不修改任何文件。不确定即写不确定。禁止推测性结论。
