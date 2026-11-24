> 卡号：R16-D1-FINAL
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_D1_FINAL\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-21（R16 第 19 轮）· 预期 **17 行**（静态 ④ 线的收官批）

# 任务：补完静态 ④ 线最后一批 —— D1 里「② 有独立审计链」的行

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**（只有合并员能改）。只产出 delta。
2. 只写 `R16_D1_FINAL\`。不改任何共享控制文件与卡目录。
3. 可以跑**只读**反汇编/扫描；不得改 `ra2youli\` 下任何文件。
4. **不许编造**：地址取不到写 `未取得`；关键地址缺就记 `SKIP` 并说明缺哪个。
5. 每行 ④ 必须自带 **D-47 披露指针且指向 `§12.6`**。

## 1. 用户已裁的两条口径（**照此执行，不许自行放宽或收紧**）

**口径一（活表装法）**：`mov [abs], vt`（直接写绝对地址装表）**算**合格的「活 vtable 槽位」装配方式，**不要求**必须是构造器体内装。理由：与盘上已并表的 151 行同形态保持口径一致。

**口径二（② 的证据要求）**：**只收「②（类身份）有独立审计链」的行**。即：该行的 ② 必须来自**既有审计记录**（`NAMED_PUSH_AUDIT*/` 下的 `verdict.tsv` / `VERDICT.md` 等），**不接受**仅靠 YRpp 知识库代理的 ②。

⇒ 按 `R16_PROBE_4FINAL` 测算，本批应为 **F1 12 行 + F2 5 行 = 17 行**；且探针明言：**做完这一批，静态 ④ 线即整线收口**。

## 2. 你要自己派生这份清单（不许照抄我的数）

**第一步：取 D1 集合**
- 输入：`R16_PROBE_4FINAL\final.tsv`（1,280 行含表头；列 `entry	subsystem	name	grade	has_ring4	vt	slot	install_site	direct_sites	note`）
- 筛 `has_ring4 == D1` ⇒ 应得 **317 行**（先报你实测的数）。

**第二步：与「来源类别」join**
- 输入：`R16_PROBE_4GAP\scan_F1_audit.tsv`（122 行：F1 缺口）与 `R16_PROBE_4GAP\matrix.tsv`（来源类别矩阵）
- 目的：给 D1 的 317 行各贴一个**来源类别**（F1 / F2 / F3 / F4 各子类）。

**第三步：按口径二筛**
- 只保留 ② **有独立审计链**的行：即该 entry 能在 `NAMED_PUSH_AUDIT*/verdict.tsv`（全部 20 个目录、约 163 条记录）里找到、且其类身份判定有审计记录。
- 探针说结果应是 **F1 12 + F2 5 = 17 行**。**报你实测的数**；若与 17 不符，**以你的实测为准并说明差异来源**（例如某行在多个 audit 目录里重复、或某行 ② 的审计记录只是转述）。

**第四步：取行范围**
- 17 行 **全做**（≤18 行/卡，合规）。

## 3. ④ 的写法

- 形态：**槽位见证**（这 17 行都是 D1 = 被活表槽持有）。
- 骨架照既有先例（`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`，取 `00464AC0`/`004DE630`/`004F42F0` 三条，以及已并表的 `R16_SLOTN_B1`/`B3`/`F1_B1` 各行）。
- 必备字段：`vt` / `slot` / `slot 值` / `COL` / `offset` / `RTTI` → `mangled` / `装表点` / `宿主函数` / 「entry 体外」。
- **若装配方式是 `mov [abs], vt`**：④ 文本里要**写清这一点**（例如「装表指令为 `mov [abs], vt`，位于 <宿主> 体内」），因为用户已把它定为合格形态、但引用者应当知道它弱于构造器体内装。
- `④升级句`：`<Class>::slot<N>（④ 表属类与行名类一致，均为 <Class>；该槽即其 vt=<VTADDR> 表 slot<N>，无归属歧义）`
- 末尾必须带：`（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`

## 4. 产物（`R16_D1_FINAL\`）

### 4.1 `derive.txt`（派生过程的中间产物）
逐阶段计数：D1 实测多少行 → join 后各类多少行 → 按口径二筛后多少行 → 最终清单（逐 entry）。

### 4.2 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 同构
表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`
- 取盘上整行原值，**只改第 4 列**：原文 + `；` + ④ 文本（**原第 4 列必须是结果的严格前缀**）。
- 第 1/2/3/5/6/7/8 列与盘上逐字节相同。记下你读到的 `coverage.tsv` 字节数与 sha256。
- 只放成功行。

### 4.3 `fields.tsv`
列：`entry	subsystem	name	source_class	audit_record(文件:行号)	ring2_independent(是)	vt	slot	install_site	install_form(ctor_body|mov_abs|reg|other)	install_host	pre_has_ring4(是/否)	status(OK|SKIP)	note`

### 4.4 `REPORT.md`
含：四阶段派生计数（含与 17 的差异说明）；每行 `②` 的审计记录出处；每行装配形态（ctor_body / mov_abs / reg / other）分类计数；6 项字节复核结果；行行不同自检（entry 归一后）；`coverage.tsv` 与 `gamemd.exe` 的 sha256（证明未改）；一句明示「只补 ④ 成文、未改 grade/判定、未并表」；**并在末尾写明：本批是静态 ④ 线收官批**。

## 5. 回复里给什么

只给：四阶段派生计数（D1 实测数 → 筛后数，与 17 是否一致）、成功/SKIP、装配形态分类计数、vt 取得行数、行行不同自检、你读到的 `coverage.tsv` sha（前 8 位）、四份产物路径、样例 ④ 两条（ctor_body 与 mov_abs 各一）。**不要贴全表**。
