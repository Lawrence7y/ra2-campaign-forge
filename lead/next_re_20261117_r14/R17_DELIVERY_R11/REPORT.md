# R17_DELIVERY_R11 · 改动报告

## 1 · 改动逐处
| 文件 | 位置 | before → after 摘要 |
|---|---|---|
| `R17_DELIVERY/DELIVERY_SUMMARY.md` | §2 后、§3 前 | 新增 `## 2.5 · 本轮新增结构事实（供引用）`（4 条）：定名链 + 限制；槽定位；0x43F180 调用方字节链 + 边界；覆写关系 + 语义未取得。 |
| 同上 | §3 表尾 | 追加行 7/8：三版三数带口径（含「只写数字不写口径 ＝ 不可引用」）；433 只地址锚定、不得升级用（含「不构成 ② 支持、不支持任何改判」）。 |
| `R17_DELIVERY/SELFCHECK.md` | 抬头注记后 | 仅加 R11 增补注记：新行数 74、§1 行号与间距不变、1,654 出现行仍仅第 9/13 行；原判据表未动。 |

**结构不变量**：§1 第 9/13/14/15/16 行逐字未变；2.5 起于 L41，§3 起于 L49；§3 行 7/8 在 L59/L60；1,654 出现行 = 9/13。新增内容全部为插入，既有行零改动。

## 2 · before / after 字节、行数、sha256
| 文件 | before bytes | after bytes | before lines | after lines | before sha256 | after sha256 |
|---|---:|---:|---:|---:|---|---|
| `DELIVERY_SUMMARY.md` | 7466 | 10214 | 64 | 74 | `b1e4f82087d59a8f8d32e81d031176aa12f2810e64c99ed3223e56d249039865` | `1e98971ae0e36739fdbcc729c0362c67519e1e269a80561d96a2078fda9aa2da` |
| `SELFCHECK.md` | 3395 | 3585 | 54 | 56 | `b8f402fc2a6dd04ae8fcffa457d9fb78388448c392e1a1ae74911f5e7eec5ab1` | `093d15516b330d5f559cb21ba426854d12a79b2583e6395747590b50e92eab27` |

行数上限：74 ≤ 110 ✔

## 3 · verify.py
命令：`cd lead/next_re_20261117_r14/R17_DELIVERY && python -X utf8 verify.py`

结果：**PASS**（exit=0；关键值复核 全部一致）
关键值：`data_rows=18498`、`[已证]=1654`、`[静态推断]=5875`、`[未证]=10969`、`TOTAL_strict=1331`、`A/B/宽/无④=458/291/293/1196`、`§12.6=323`、`R_OK=863`、`R_TRACE_ONLY=791`、`名义=3/22`、`严格=1/22`。
`numbers.tsv` 校验：before/after 字节一致（无净变化）。

```text
== R17-DELIVERY verify ==
[in ] D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv
[in ] D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEAD_BASELINE\coverage.before_hyg.tsv
[in ] D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv
[out] D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_DELIVERY\numbers.tsv  (47 项)

coverage  : 4147334 B / sha256 c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a
data rows : 18498  cols 8  bad 0
grade     : [已证] 1654  [静态推断] 5875  [未证] 10969
proved    : atlas 内 1648  atlas 外 6   TOTAL strict 1331
ring4     : A 458 (27.69%)  B 291 (17.59%)  wide 293 (17.71%)  无④ 1196
literal   : ④>=2 raw 375 / ④空格>=2 308 （BEFORE_A1: 373 / 306）
hygiene   : §12.6 323  §12.4 0  CLSID None 0  A1 0  A2 0
evidence  : R_OK 863  R_MISSING 0  R_TRACE_ONLY 791  R_EMPTY 0
DoD       : 名义 3/22 (S15/S16/S17)  严格 1/22 (S17)
```

## 4 · 备份
- 路径：`R17_DELIVERY_R11/DELIVERY_SUMMARY.before_R11.md`
- 创建方式：`fs.writeFileSync(..., { flag: 'wx' })`；目标不存在才创建，存在即报错退出（无 if-not-exists 静默跳过）。
- 结果：**成功**；bytes=7466；sha256=`b1e4f82087d59a8f8d32e81d031176aa12f2810e64c99ed3223e56d249039865`（与 before 一致）。

## 5 · 禁改集合
`coverage.tsv` / `COVERAGE/PANEL.md` / `R14_COMMON.md` / `_cards/R17-DELIVERY-R11.md` / `R17_LEDGER_*/SELFCHECK.md` 共 11 个文件，聚合 sha256 before=`972e96c828402f14c4d83780e63cdb0db855b241341d6ecad305560426e00058`、after=`972e96c828402f14c4d83780e63cdb0db855b241341d6ecad305560426e00058`，一致，未改动。

## 6 · 产物
`REPORT.md`、`diff.txt`、`DELIVERY_SUMMARY.before_R11.md` 均写入 `R17_DELIVERY_R11/`；源文件仅 `DELIVERY_SUMMARY.md` 与 `SELFCHECK.md` 有净改动。
