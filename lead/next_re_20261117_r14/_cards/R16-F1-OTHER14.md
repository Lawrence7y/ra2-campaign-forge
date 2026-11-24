> 卡号：R16-F1-OTHER14
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_F1_OTHER14\`（产物）——**严禁写 `coverage.tsv`**
> 日期：2026-11-21（R16 第 17 轮）· **14 行**

# 任务：给 14 行「真·无 ④」的行补 ④ 使用见证

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**。只产出 delta。
2. 只写 `R16_F1_OTHER14\`。不改任何共享控制文件与卡目录。
3. 可以跑**只读**反汇编/扫描；不得改 `ra2youli\` 下任何文件。
4. **不许编造**：地址取不到写 `未取得`；关键地址缺就记 `SKIP` 并说明缺哪个。
5. 每行 ④ 必须自带 **D-47 披露指针且指向 `§12.6`**（不是 §12.4）。

## 1. 背景（探针实测，照录）

`R16-PROBE-F1-PIVOT` 查明：`PROBE_4GAP` 的「F1 缺口 122 行」里，**80 行在 pin 截面时就已含 ④**，真正没有 ④ 的只有 **42 行**：

| 类别 | 行数 | 状态 |
|---|---:|---|
| `audit_ring4_ctor_install` | 28 | **已由 F1 B1–B5 补完并表** |
| **`sem_virtual_witness_only`** | **12** | ← **本卡对象（之一）** |
| **`sem_live_table_install`** | **2** | ← **本卡对象（之二）** |
| `audit_ring4_alloc_reg_pivot` | 32 | **已有 ④、不是缺口**（另一张卡只修其正文错值） |

**这 14 行 `same_source` 与 `audit_verdict` 都是 `-`（无审计记录）**，探针查明原因：它们属于 `surface.py` 的**路由 2（纯语义正则分支）**，不是「漏检」；在全部 20 个 `NAMED_PUSH_AUDIT*/verdict.tsv`（163 条）里命中 **0** 次（对照：32 行 pivot 命中 32 次）。

## 2. 这 14 行的已有线索（探针给出，你须逐行复核）

- **2 行 `sem_live_table_install`（locomotion ctor）**：探针实测持有**形态 1 的 direct call**——
  `006C404C → 004AF540`、`006C494C → 004B5AB0`。
  ⇒ 这 2 行的 ④ 是 **direct call 形态**（比槽位见证更强，因为它独立于 ②）。
- **12 行 `sem_virtual_witness_only`（多为 dtor）**：探针实测**全部解出槽位**——9 行 slot0、`RadSiteClass`/`WarheadTypeClass` slot8、`AnimClass::Draw` slot69（与语义 `v[69]` 逐值吻合）。

## 3. 要做的事

1. **自己从 `R16_PROBE_F1_PIVOT\other14.tsv` 取清单**，逐行复核上表的线索在字节上成立（不要照抄）。
2. 按**形态**写 ④：
   - **direct call 形态**（那 2 行）：④ 要写清 **调用站点地址** 与 **被调 entry**，格式参照 `R14_COMMON` 里 §8.6 条 1 关于「direct call」的口径；不得写成槽位见证。
   - **槽位见证形态**（那 12 行）：照既有先例（`coverage.tsv` 第 4 列搜 `④ 活表槽位见证`，取 `00464AC0`/`004DE630`/`004F42F0` 三条）的骨架，字段逐个填实（vt / slot / COL / RTTI / 装表点 / 宿主）。
3. **`same_source` 必须自证**：这 14 行原本 `same_source=-`（无记录），你要在 `fields.tsv` 里**自己判一次**并给出依据——④ 的证据是否独立于 ② 的类身份证据。若某行判下来是 `same_source=yes`（即 ④ 与 ② 同一条证据），**该行不得补**，记 `SKIP` 并说明（D-47(A) 虽让位 §12.3，但本批的补写前提仍要求证据链独立；这一点与 F1 前几批一致）。
4. 逐行在 `fields.tsv` 记：改前第 4 列**是否已含字符 `④`**（供并表算净增，不许假设）。

## 4. 产物（`R16_F1_OTHER14\`）

### 4.1 `delta.tsv` —— TAB 分隔，8 列，与 `coverage.tsv` 同构
表头：`entry	subsystem	name	one_line_semantics	grade	evidence_path	n_sources	conflict`
- 取盘上整行原值，**只改第 4 列**：原文 + `；` + ④ 文本（**原第 4 列必须是结果的严格前缀**，原文一字不删）。
- 第 1/2/3/5/6/7/8 列与盘上逐字节相同。记下你读到的 `coverage.tsv` 字节数与 sha256（该文件会被并发改写，若期间变化要重新校验并留痕）。
- 只放成功行。

### 4.2 `fields.tsv`
列：`entry	subsystem	name	category(sem_virtual_witness_only|sem_live_table_install)	form(direct_call|slot_witness)	key_addrs	evidence_src	same_source_judged(yes|no)	same_source_basis	pre_has_ring4(是/否)	status(OK|SKIP)	note`

### 4.3 `REPORT.md`
含：14 行清单与逐行结论；成功/SKIP 与 SKIP 原因；6 项字节复核（槽位见证行）；direct call 行给出「站点指令字节 + 目标 entry」的实证；行行不同自检（entry 归一后）；`coverage.tsv` 与 `gamemd.exe` 的 sha256（证明未改）；一句明示「只补 ④ 成文、未改 grade/判定、未并表」。

## 5. 回复里给什么

只给：14 行里 OK/SKIP 各几行、几行判成 `same_source=yes`（若有）、2 行 direct call 形态是否成立、12 行槽位是否 12/12 解出、行行不同自检、你读到的 `coverage.tsv` sha（前 8 位）、三份产物路径、样例 ④ 两条（两种形态各一）。**不要贴全表**。
