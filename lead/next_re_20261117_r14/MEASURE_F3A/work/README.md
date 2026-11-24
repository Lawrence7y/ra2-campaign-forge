# MEASURE-F3A · work/ 脚本索引（哪个产出是权威的）

按执行顺序。**打 ★ 的是权威产出**；标 `SUPERSEDED` 的脚本保留了「判据被打回→重写」的证据链，
其终端数字**不再有效**，不要引用。

| 脚本 | 作用 | 状态 |
|---|---|---|
| `pelib.py` | 自写 PE32 解析 + 有界体内反汇编（capstone 5.0.7）；随机 8 例与 atlas `n_instr` 8/8 吻合 | 权威 |
| `thirdb.py` | ③b 检测（D-42 ①②③④ 的操作化） | **权威（含两次修正后版本）** |
| `s1_domain.py` | 行域清点：317 / S22 43 / 非 S22 **274** | 权威 → `s1_counts.json` |
| `s2_wording.py` | 措辞类与 `[未证]` 尾部形态 | 权威（探查）→ `s2_domain_raw.txt` |
| `s3_split.py` | 首版模板/锚点粗分（按 `）[未证]$` 判模板，误把 65 行标成 ANCHORED） | SUPERSEDED（探查记录） |
| `s4_canon.py` | 正确归一化模板：**272/274 是同一模板**，仅 2 行非模板 | 权威 |
| `s5_evidence.py` | `evidence_path` 指向统计（272/274 → `classification_trace.tsv`） | 权威 |
| `s6_baseline.py` | 复算 n / named_S / proved / 门槛，与台账逐一吻合 | 权威 → `s6_baseline.json` |
| `s7_bytes.py` | 首版 ③b 普查（**旧判据**：③b① 只认跳表、③b② 认布尔返回） | SUPERSEDED（数字作废） |
| `s8_calib.py` | 首版校准（把 甲/乙 判据与 ③b 判据混在一张表，导致两处 MISMATCH） | SUPERSEDED（记录了判据错误） |
| `s9_calib.py` | **两仪器分开计分**的正式校准：A 5/5、B 7/7 | **权威** → `s9_calib.json` |
| `s10_census.py` | 普查 + 降级表（用旧 ③b 判据） | SUPERSEDED（数字作废） |
| `s11_jia_verify.py` | 甲行锚点复核；出 `EVIDENCE\00522340__JIA_rowproved.txt`、`004C93D0__JIA_rowproved.txt` | **权威** |
| `s13_sample.py` | **甲乙判定定稿** + 乙 20 抽样 + 出 **`F3A_CLASS.tsv`** | **权威** → `s13_sample.json` |
| `s14_table.py` | 三情景逐子系统表（现状 / §8.6 严格 / 最宽救回） | **权威** → `s14_table.json` |
| `s15_reconcile.py` | 317 = 213 + 65 + 39 拆分复算；子系统分布对卡面 | **权威** |

## 重跑顺序（全部只读，约 1 分钟）
```
cd lead\next_re_20261117_r14\MEASURE_F3A
python work\s1_domain.py      # 274
python work\s6_baseline.py    # 复算 proved/门槛
python work\s9_calib.py       # 必须先过：A 5/5 B 7/7（exit 0）
python work\s13_sample.py     # 甲乙定稿 + F3A_CLASS.tsv
python work\s14_table.py      # 三情景表
python work\s15_reconcile.py  # 317 拆分
```

## 关键提醒
- `s12_final.py` 已删除：它是「锚点必须在本体内命中」的过粗复核，会把 `00522340`
  文本里**明确归属于被调 `005B3A00`** 的 `+0xAC` 判成缺失，从而得出 甲 0 / 乙 274 的错误结论。
  正确做法（甲=1 / 乙=273）见 `s13_sample.py` 与 `EVIDENCE\ANCHOR_RECHECK_2rows.md`。
- `__pycache__\` 是 Python 字节码残留，可删。
