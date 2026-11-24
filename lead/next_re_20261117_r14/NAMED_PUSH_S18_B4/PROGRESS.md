# PROGRESS — NAMED_PUSH_S18_B4

批次：S18 B4（S18 named=True 非伪名候选，减去 B1/B2/B3 已核 54 行，剩下前 18 行，entry 升序）。
输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B4`

执行纪律：先建目录、先写 REPORT 骨架；每核完一行立刻落盘 EVIDENCE；每 5 行追加本文件。

## 进度

- [x] 目录与骨架（REPORT.md / delta.tsv 表头 / base_rate.tsv 表头 / PROGRESS.md）已建立
- [x] 筛选：82 named 非伪名 - 54 已核 = 28，本批取前 18，剩余池 10（见 work/filter_b4.py）
- [x] 核 1-5 行（007A9110 / 007A9200 / 007A9550 / 007A9800 / 007A9970）——②PASS×5 ③FAIL×5(bool/null) ④PASS×5
- [x] 核 6-10 行（007AA6D0 / 007AA870 / 007AAFB0 / 007AB0A0 / 007AB170）——②PASS×5 ③FAIL×5(bool/null) ④PASS×5
- [x] 核 11-15 行（007AB260 / 007AB440 / 007AB8E0 / 007AC220 / 007AC700）——②PASS×5 ③FAIL×5(bool/null / p3=0 / ATL QI 模板) ④PASS×5
- [x] 核 16-18 行（007AC870 / 007AD690 / 007B10C0）——②PASS×3 ③FAIL×2(ATL QI) + **PASS×1(007B10C0 ③b②)** ④PASS×3
- [x] 汇总（REPORT / delta 1 行 / base_rate）

## 逐行落盘记录

每核完一行即落盘 `EVIDENCE/ROW_<entry>.txt`（18 份，每份含本行自身地址与字节）。

| 序 | entry | ① | ② | ③③b | ④ | 四环齐全 | 产出 |
|---:|---|---|---|---|---|---|---|
| 1 | 007A9110 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 2 | 007A9200 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 3 | 007A9550 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 4 | 007A9800 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 5 | 007A9970 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 6 | 007AA6D0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 7 | 007AA870 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 8 | 007AAFB0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 9 | 007AB0A0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 10 | 007AB170 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 11 | 007AB260 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 12 | 007AB440 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 13 | 007AB8E0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 14 | 007AC220 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 15 | 007AC700 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 16 | 007AC870 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 17 | 007AD690 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 18 | 007B10C0 | PASS | PASS | **PASS** | PASS | **是** | **delta 1 行** |

## 三陷阱与额外排查

- eax 覆写：0 行触发；唯一 PASS 行 007B10C0 的 cmp eax,-1→jne 之间仅 mov[mem],eax / pop edi，不写 eax。
- 多路同一 call：相关行本就 ③ FAIL，不改变裁定。
- 模板假句：slot0 三行（007AC700/870/690）ATL QueryInterface 判空模板，判 FAIL。
- ㉓ 析构器陷阱：所有 ④ 构造安装点 atexit=False，无落析构器者。
- 小成员表 vtable：相关 vtable 均 80+ 槽且 vtable[-4] 为合法 COL 指针，是主虚表。

## 汇总

rows_checked=18 / ②=18 / ③b=1 / ④=18 / all_four=1 / rate=0.0556。delta 1 行（007B10C0）。如实交 1 行。
