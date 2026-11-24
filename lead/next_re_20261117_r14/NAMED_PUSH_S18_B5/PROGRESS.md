# PROGRESS — NAMED_PUSH_S18_B5

批次：S18 B5（S18 named=True 非伪名候选，减去 B1/B2/B3/B4 已核 72 行，剩余全部 10 行，entry 升序；B5 为收尾批）。
输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B5`

执行纪律：先建目录、先写骨架；逐行核、每核完一行立刻落盘 EVIDENCE；每 5 行追加本文件。

## 进度

- [x] 目录与骨架（REPORT.md / delta.tsv 表头 / base_rate.tsv 表头 / PROGRESS.md）已建立
- [x] 筛选：`work/filter_b5.py` → `work/b5_filter.txt`（all=82, checked=72, remaining=10, selected=10）
- [x] 工具链自校验：gamemd.exe SHA-256=73201CC0...476（复核一致）；Python 3.12.10 / capstone 5.0.7(skipdata=True) / pefile 2024.8.26
- [x] 逐行核（每行独立 ①入口 / ②RTTI / ③b② / ④构造安装+派发 / 三陷阱 / ㉓析构锚 / 小成员表）并逐行落盘 EVIDENCE ×10
- [x] 独立复核：构造/析构写点分类（`work/verify_independent.py` + `work/classify_funcs.py`）、构造器活性、IAT thunk→Winsock API（`work/iat_b5.txt`）
- [x] 汇总（REPORT 整体重写 / delta 9 行 / base_rate / 本文件）

## 逐行落盘记录

| 序 | entry | ① | ② | ③③b | ④ | 四环齐全 | 产出 | EVIDENCE |
|---:|---|---|---|---|---|---|---|---|
| 1 | 007B13D0 | PASS | PASS | PASS(③b② sendto/recvfrom -1) | PASS | 是 | delta | ROW_007B13D0.txt |
| 2 | 007B1BC0 | PASS | PASS | PASS(③b② WSAAsyncSelect -1) | PASS | 是 | delta | ROW_007B1BC0.txt |
| 3 | 007B2630 | PASS | PASS | PASS(③b② setsockopt -1) | PASS | 是 | delta | ROW_007B2630.txt |
| 4 | 007B26D0 | PASS | PASS | PASS(③b② gethostname -1) | PASS | 是 | delta | ROW_007B26D0.txt |
| 5 | 007B30B0 | PASS | PASS | PASS(③b② socket/bind -1) | PASS | 是 | delta | ROW_007B30B0.txt |
| 6 | 007B31E0 | PASS | PASS | PASS(③b② bind -1) | PASS | 是 | delta | ROW_007B31E0.txt |
| 7 | 007B3450 | PASS | PASS | PASS(③b② socket/bind -1) | PASS | 是 | delta | ROW_007B3450.txt |
| 8 | 007B36C0 | PASS | PASS | FAIL({0,1} 布尔，非可伪证) | PASS | 否 | 无 | ROW_007B36C0.txt |
| 9 | 007B3890 | PASS | PASS | PASS(③b② WSAAsyncSelect -1) | PASS | 是 | delta | ROW_007B3890.txt |
| 10 | 007B3AA0 | PASS | PASS | PASS(③b② sendto -1) | PASS | 是 | delta | ROW_007B3AA0.txt |

> 前 5 行落盘后追加一次；后 5 行核完后再追加本表（本表为最终全量，含全部 10 行）。

## 计数（以 base_rate.tsv 为准）

rows_checked=10，ring2_ok=10，ring3b_ok=9，ring4_ok=10，all_four=9，rate=0.9000。
delta 9 行（007B36C0 因 ③ 为 {0,1} 布尔不成立，不入 delta）。
