# DELIVERY_SUMMARY D-53 裁决同步报告

## 1. 改动清单

### 1.1 §3 表第 1 行（②-b 收口方式）

before：

```text
| 1 | **②-b 收口方式** | **D-53 待裁**：二选一 —— (A) 永久挂 `[静态推断]` ／ (B) 撤销 D-36(A)「不写线程上下文」单条。**用户未裁前，②-b 不得表述为已证** | 照录 `PENDING_DECISIONS.md` D-53 |
```

after：

```text
| 1 | **②-b 收口方式** | **D-53 已裁 (A)**：②-b 永久以 `[静态推断]` 收口，不再投卡；不得表述为「已证」。凡引 ②-b 必须写 `[静态推断]` 并同引 `R14_COMMON §2.9`；书面限制 a–e 是不可拆的引用单元。**未选 (B)**（撤销 `D-36(A)`「不写线程上下文」单条）⇒ 真机授权范围不变。 | `R14_COMMON §2.9` + `PENDING_DECISIONS.md` 已裁决记录首条 |
```

落地点：`DELIVERY_SUMMARY.md:45`。口径已改为 D-53 已裁 (A)，写明 ②-b 永久以 `[静态推断]` 收口、不再投卡、不得表述为已证；引用须写 `[静态推断]` 并同引 `R14_COMMON §2.9`；书面限制 a–e 为不可拆引用单元；未选 (B) 故真机授权范围不变；出处改为 `R14_COMMON §2.9` + `PENDING_DECISIONS.md` 已裁决记录首条。

### 1.2 §3 表第 3 行（D-48 作取证路径）

before：

```text
| 3 | **D-48 作取证路径** | **已判死，净收益 = 0**（调试器身份 ≠ 写内存/写线程上下文的权利；10 通道中「能证明具体指令被执行过」= 0）。**不得再把 D-48 当作 ②-b 的取证路径** | 照录 `PENDING_DECISIONS.md` D-53 实测结论段 |
```

after：

```text
| 3 | **D-48 作取证路径** | **已判死，净收益 = 0**（调试器身份 ≠ 写内存/写线程上下文的权利；10 通道中「能证明具体指令被执行过」= 0）。**不得再把 D-48 当作 ②-b 的取证路径** | 照录 `R14_COMMON §2.9` + `PENDING_DECISIONS.md` D-53 已裁决条 |
```

落地点：`DELIVERY_SUMMARY.md:47`。仅改出处指针：由失效的「D-53 实测结论段」改指 `R14_COMMON §2.9` + `PENDING_DECISIONS.md` D-53 已裁决条。

## 2. 硬约束核对

- §1 三项限定同框结构：第 1–40 行逐字未变；第 13–16 行（1,654 / L1 / L2 / L3）未动。
- 非目标行：第 45、47 行之外的所有行逐字未变。
- 行数：before 65 行 → after 65 行（上限 110）。
- 全文扫描：未发现指向 D-53 / ②-b 的「待裁」「未裁」字样。全文其余「待裁」命中：无。
- 未改 `coverage.tsv`、`R14_COMMON.md`、台账、看板；`SELFCHECK.md` 无需同步。

## 3. 字节与哈希

| 项 | before | after |
|---|---|---|
| 字节数 | 7261 B | 7466 B |
| SHA-256 | `fed9b6db5f4b5e8d87c45102f1aef445d6f14d680e5c64d90357bf06cd17065b` | `b1e4f82087d59a8f8d32e81d031176aa12f2810e64c99ed3223e56d249039865` |
| 行数 | 65 | 65 |

行数口径与卡面一致：按 `split(/\r?\n/)` 计，末尾换行计 1 行。

## 4. 备份

- 路径：`R17_DELIVERY_D53/DELIVERY_SUMMARY.before_D53.md`
- 写入前已校验目标不存在；使用独占写入标记 `wx` 创建，冲突会报错退出，无静默跳过。
- 落盘：成功；备份 SHA-256 `fed9b6db5f4b5e8d87c45102f1aef445d6f14d680e5c64d90357bf06cd17065b`（与 before 一致）。

## 5. verify.py

- 命令：`python -X utf8 verify.py`（cwd: `R17_DELIVERY`）
- 结果：**PASS**（exit=0）
- `numbers.tsv` SHA-256：before `4e4c1476d14251977db31fdf702aa4e1b53e370d20e06f71c83e740c5ee6ecba` → after `4e4c1476d14251977db31fdf702aa4e1b53e370d20e06f71c83e740c5ee6ecba`（未变）

stdout：

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

stderr：

```text

```
