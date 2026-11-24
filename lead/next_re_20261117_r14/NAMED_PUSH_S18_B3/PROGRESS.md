# PROGRESS — NAMED_PUSH_S18_B3

批次：S18 B3（S18 named=True 非伪名候选第 37..54 个，entry 升序，共 18 行）。
输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B3`

执行纪律：先建目录、先写 REPORT 骨架；每核完一行立刻落盘 EVIDENCE；每 5 行追加本文件。

## 进度

- [x] 筛选与骨架（18 行确定，0 个伪名需排除）
- [x] 核 1-5 行（00774CD0 / 00774F50 / 00775110 / 007A3100 / 007A3D90）——②PASS×5 ③FAIL×5 ④PASS×5
- [x] 核 6-10 行（007A4070 / 007A41C0 / 007A4C10 / 007A5290 / 007A55F0）——②PASS×5 ③FAIL×5 ④PASS×5
- [x] 核 11-15 行（007A5690 / 007A5890 / 007A7110 / 007A7EA0 / 007A8260）——②PASS×5 ③FAIL×5 ④PASS×5
- [x] 核 16-18 行（007A8DA0 / 007A8ED0 / 007A8FC0）——②PASS×3 ③FAIL×3 ④PASS×3
- [x] 汇总（delta.tsv 0 行 / REPORT.md / base_rate.tsv）

## 逐行落盘记录

每核完一行即落盘 `EVIDENCE/ROW_<entry>.txt`（18 份，每份含本行自身地址与字节）。

| 序 | entry | ① | ② | ③③b | ④ | 四环齐全 | 产出 |
|---:|---|---|---|---|---|---|---|
| 37 | 00774CD0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 38 | 00774F50 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 39 | 00775110 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 40 | 007A3100 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 41 | 007A3D90 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 42 | 007A4070 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 43 | 007A41C0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 44 | 007A4C10 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 45 | 007A5290 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 46 | 007A55F0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 47 | 007A5690 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 48 | 007A5890 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 49 | 007A7110 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 50 | 007A7EA0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 51 | 007A8260 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 52 | 007A8DA0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 53 | 007A8ED0 | PASS | PASS | FAIL | PASS | 否 | 否 |
| 54 | 007A8FC0 | PASS | PASS | FAIL | PASS | 否 | 否 |

## 汇总

rows_checked=18 / ②=18 / ③b=0 / ④=18 / all_four=0 / rate=0.0000。③ 为决定性瓶颈；按「宁严不宽、虚报不可接受」如实交 0 行。
