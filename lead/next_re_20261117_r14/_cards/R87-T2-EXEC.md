# 卡 · R87-T2 · 执行员（hy4 家族）：独立重算 R87 的门禁实验数字

## 〇 · 你是谁
你是执行员。只读 live 树。唯一写目标是 lead/next_re_20261117_r14/R17_R87_T2_EXEC/（不存在就建）。
严禁修改 check_disc.py、DISC_RECHECK.tsv、DISC_UNVERIFIABLE.tsv、recheck_verify.py 及任何 live 文件。
严禁在 live 树上追加任何自述行 —— 所有实验必须在你自己复制出来的副本里做。

## 一 · 任务：从零重做一遍下面的实验，报你自己算出的数字

项目根 = /home/t628/projects/ra2-campaign-forge
基线（不改造时跑 live 门禁）应得到：exit 1，C11 计数 ok=0 fail=5 frozen-unverifiable=12 claims-none=13。
先确认这个基线，若你跑出来不同，如实报不同值，并说明为什么。

实验 A（摘帽）：把 lead/ 下门禁所需的子树复制到临时目录（可参考 _r87/decap2_r87.py 的 build 函数，
但请自己写，不要 import 它）。在副本里挑 DISC_UNVERIFIABLE.tsv 里登记的任意一条冻结纪律，
往它 DISC_RECHECK.tsv 第 5 列指定的产物追加一条格式合规的自描述行，
格式：DISC_RECHECK discipline=<N> round=R55 at=2026-11-22T17:45:00+08:00 anchors=sha256:<64位小写hex> conclusion=UNKNOWN
其中 anchors 必须是该纪律 DISC_RECHECK.tsv 第 4 列逐字串的 sha256。
然后跑副本门禁，报 C11 四个计数。

实验 B（只改时刻）：另建一份副本，不改任何内容，只把纪律 3、4、22、27、28 这五条
已有自述行里的 at 值改成 2026-11-22T17:45:00+08:00，跑门禁，报 exit 与 C11 四个计数。

实验 C（反控）：在实验 B 的副本基础上，把某一条的 at 改回 2026-11-22T18:45:00+08:00（窗外），
再跑一次，报 exit 与 C11 计数。预期该条重新 FAIL。

## 二 · 硬要求
- 每个实验都要有「不改造的副本」作正控，证明复制本身无损（正控跑出的计数必须与 live 一致）。
- 收尾用 sha256 证明 live 目录下所有文件未被你改动（自己写校验，前后各算一次）。
- 数字必须是脚本跑出来的，不许手填。

## 三 · 输出
写入 lead/next_re_20261117_r14/R17_R87_T2_EXEC/REPORT.md：三个实验的原始计数、正控结果、
live 未被改动的 sha256 前后值、以及任何你跑出来与我描述不一致的地方。
