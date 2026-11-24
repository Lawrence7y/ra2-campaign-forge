> 卡号：R16-D1-WIDE-B1
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_D1_WIDE_B<n>\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-21（R16 第 22 轮起）
> **本卡是参数化卡面：批次号由派发 prompt 指定。**

# 任务：给 D1 宽读集合里「盘上尚无 ④」的行补 ④

## 0. 批次定义

清单权威来源：`lead\next_re_20261117_r14\R16_SIEVE_D1_WIDE\sieve_all.tsv`（**81 行**，判据 S1–S7 在 `sieve.py` 里）

| 批次 | 行范围（按 entry 升序，仅「盘上尚无 ④」的行） |
|---|---|
| **B1** | 第 **1–18** 行 |
| **B2** | 第 19–36 行 |
| **B3** | 第 37–54 行 |
| **B4** | 第 55–65 行 |

**注意**：`sieve_all.tsv` 共 81 行，其中 **16 行盘上已有 `④ 活表槽位见证`**（`has_ring4_on_disk == 是`），应**跳过不重做**。⇒ 待做 **65 行**，按上表切 4 批（18/18/18/11）。

## 1. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**（只有合并员能改）。只产出 delta。
2. 只写你 prompt 指定的目录。不改任何共享控制文件与卡目录（`R16_SIEVE_D1_WIDE/` 只读）。
3. 可以跑**只读**反汇编/扫描；不得改 `ra2youli\` 下任何文件。
4. **不许编造**：地址取不到写 `未取得`；关键地址缺就记 `SKIP` 并说明缺哪个。
5. 每行 ④ 必须带 **D-47 披露指针且指向 `§12.6`**。

## 2. 用户已裁的三条口径（照此执行）

- **D-50**：`mov [abs], vt` **算**合格活表装配方式，但 ④ 文本**必须写清**装配方式（不得含糊成「构造器装表」）。
- **D-51 + D-52**：只收「② 有独立审计链」的行；**宽读**——任何**独立于 ② 与 ④ 产出方**的审计产物都算（`*_audit/VERDICT.md` 与 `NAMED_PUSH_AUDIT*/verdict.tsv` 等值）。这条**筛手已经在 `sieve_all.tsv` 里落实**，你直接用它的清单即可，**不要自己重筛**（但若你发现清单里某行明显不该在，报出来、别默默跳过）。

## 3. 要做的事

1. 从 `sieve_all.tsv` 取 `has_ring4_on_disk == 否` 的行，按 entry 升序，取你批次的范围。
2. **并先复核一次盘上现值**：这些行在**当前** `coverage.tsv` 里是否真的仍无 `④ 活表槽位见证`？（并发并表可能已经覆盖了某几行；若已含则记 `SKIP-ALREADY` 并说明，不要重复追加。）
3. 逐行写 ④（槽位见证形态）：必备字段 `vt` / `slot` / `slot 值` / `COL` / `offset` / `RTTI`→`mangled` / `装表点` / `宿主` / 「entry 体外」。
   - **装配方式必须写**：从装表指令判它是 `ctor_body`（构造器体内）、`mov_abs`（`mov [abs], vt`）、还是 `reg` 形态，并把结论写进 ④ 文本（D-50 要求）。
   - 骨架照既有先例：`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`，取 `00464AC0`/`004DE630`/`004F42F0`，以及已并表的 `R16_F1_OTHER14`/`R16_D1_FINAL` 各行。
4. **若某行在 `sieve_all.tsv` 里记的 `vt` 与行名类不符**（像 `0070B570` 那次），按「类一致优先」另取该行名类自己的活表，并在 `fields.tsv` 标 `CLASS_FIX` 逐字披露理由。

## 4. 产物（你 prompt 指定的目录）

### 4.1 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 同构
表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`
- 取盘上整行原值，**只改第 4 列**：原文 + `；` + ④ 文本（**原第 4 列必须是结果的严格前缀**）。
- 第 1/2/3/5/6/7/8 列与盘上逐字节相同。记下你读到的 `coverage.tsv` 字节数与 sha256。
- 只放成功行（`SKIP-ALREADY` / `SKIP` 不进 delta）。

### 4.2 `fields.tsv`
列：`entry	subsystem	name	sieve_audit_file	sieve_audit_line	vt	slot	install_site	install_form(ctor_body|mov_abs|reg|other)	install_host	pre_has_ring4(是/否)	status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)	note`

### 4.3 `REPORT.md`
含：本批派生（sieve_all 81 → 去已含 ④ 的 16 → 待做 65 → 本批取第 N–M 行）；盘上现值复核结果（有无 `SKIP-ALREADY`）；安装形态分类计数；6 项字节复核结果；行行不同自检（entry 归一后）；`coverage.tsv` 与 `gamemd.exe` 的 sha256（证明未改）；一句明示「只补 ④ 成文、未改 grade/判定、未并表」。

## 5. 回复里给什么

只给：本批行数、OK/SKIP-ALREADY/SKIP/CLASS_FIX 各几行、安装形态分类计数、vt 取得行数、行行不同自检、你读到的 `coverage.tsv` sha（前 8 位）、三份产物路径、样例 ④ 两条（不同安装形态）。**不要贴全表**。
