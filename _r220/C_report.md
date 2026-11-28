# R220-C 取证报告：check_disc.py 现态复测 + 12 个永不 FAIL id 的判据来历

执行员：hy4（只读，家族 hy4 / provider magpie-anthropic / model work/cn:hy4flash-free）
工作目录：`/home/t628/projects/ra2-campaign-forge`
输出：`_r220/C_report.md`、`_r220/C_result.json`（仅写 `_r220/`，未改项目任何文件）

---

## T1 现态复测（全部实测）

命令：`python3 lead/next_re_20261117_r14/check_disc.py`

- 退出码：**0**（`[exit 0]`）
- stdout 行数：**32**（≤200，已全量输出）；stderr 行数：**0**
- 总检查项：**31** 项 live-checks（C7 通过 31 / none-skipped 0）
- PASS：**31**；FAIL：**0**；SKIP：**0**
- FAIL id 与文字：**无**（exit 0，无 FAIL 行）

stdout 全量：

```
--- check_disc.py (R166) ---
discipline defs 31 ; DISC_RECHECK rows 31
  NOTE  C6 cross-namespace refs (compound-aware, outside 2.14+) = 9
  NOTE  C6 threshold ok: 9 <= 120
  NOTE  C6 map INCLUDE rows cover all 9 refs (10 total rows, 1 excluded)
  NOTE  C7c vacuity pre-filter: 27 regex rows tested against empty string, 0 nullable (pinned 0)
  NOTE  C7d product/expression fingerprint ok: 31 rows, sha256=b07f46981eb34a22
  NOTE  C7b shape census: bytes==0, exists=0, grep==24, grepcount==3, none=0, rows==4 ; three of six shapes have ZERO rows (exists/bytes=/none are live code with no data behind them -- 31/31 passed MUST NOT be read as all shapes exercised)
  NOTE  C11b loadable-registry: declared=12 rows, gap(claims-none, can never FAIL)=12 ids=[3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]
  NOTE  C11 frozen-class registry loaded: 12 ids [1, 2, 5, 6, 7, 8, 9, 10, 18, 20, 24, 25] ; sha256=5fc21cfece52f1e4 OK
  NOTE  C11 col7 machine-check: ok=0 fail=0 frozen-unverifiable=12 claims-none=19
  NOTE  C12 frozen-anchor live-check: 12 frozen rows, 12 anchors hit
  NOTE  C12b frozen registry mirrors the live table: 12/12 rows identical on (sec, product, expr)
  NOTE  C13 section-correspondence: 31/31 rows match their definition section
  NOTE  C14 free-text table fingerprint ok: 31 rows, sha256=a740bcc9add4e607
  NOTE  C15 content floor: 2.x sections 219 (pinned 100), last 227 (pinned 106), bytes 1943574 (floor 831406)
  NOTE  C16d floor-table pin: 2a0bb774b3068dda (OK)
  NOTE  C16 per-section floors: 219 sections measured (pinned 219), hollow/deficient 0, missing 0, unpinned 0, min margin 0
  NOTE  C18 vacuity: C17 checked=0, C11 ok=0 pinned (claims-有==frozen==12, claims-none=19) -- zero is STRUCTURAL, not incidental
  NOTE  C17 self-produced-line anachrony: checked=0 impossible=0 (pinned 0), reused-at={}, pin=e3b0c44298fc1c14
  NOTE  C19 fact-layer link (pointer-driven): 'lead/next_re_20261117_r14/R17_R131_FACTINDEX_V601/FACT_INDEX.tsv' sha 54ff0419 bytes 284839 ; facts_floors EXPECT_CUR/CUR_SHA256/TOTAL_BYTES all agree
  NOTE  C20 three-way ledger path (runner/facts/pointer): all three resolve to '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R131_FACTINDEX_V601/FACT_INDEX.tsv' ; C19 pointer state='ok'
C7 live-checks passed 31 ; none-skipped 0 ; shape census bytes==0, exists=0, grep==24, grepcount==3, none=0, rows==4
C8 section-exists passed 31
C10 self-check: ok(R166)
C19 fact-layer link: ok(54ff0419/284839/R17_R131_FACTINDEX_V601)
C20 three-way ledger path: ok(R17_R131_FACTINDEX_V601)
  PASS  structure/paths/sections/self all ok ; live checks 31
  BOUNDARY: C7 verifies product file exists AND its recorded byte count ;
            it does NOT verify that the product content supports the discipline.
            PASS != all 28 disciplines proven.  Row-7 truth is NOT machine-verified.
[exit 0]
```

---

## T2 12 个「永不 FAIL」id 的来历

### 登记机制

`check_disc.py` 没有 CHECKS 列表/装饰器；检查项是脚本顶层顺序执行的代码块，检查对象来自
`DISC_RECHECK.tsv`（31 行 = 纪律定义 31 条）。「永不 FAIL」的判据来源在 `check_disc.py:357`：

```python
C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
```

这是 C11 检查里「声称可回跑」的 id 集合（行 357）。C11b（行 361–372）把该集合与
`C11B_PIN_GAP` 对照，只钉住「哪些 id 宣称无、永不 FAIL」这个**集合本身**是否漂移——
即判据是「缺口名单不许悄悄变化」，**不是**「这些纪律真的被回跑过」。
C18（行 1042–1069）进一步把 claims-有集合 == 冻结档集合这一恒等关系钉住，
使 C11 ok=0 / C17 checked=0 成为「显式登记的结构性空转」。

### 被登记的 id 全集（排序）

`[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,31,32,33]` —— 共 **31** 个（注意缺 29、30，直接跳到 31–33）。

### 恒 PASS id 完整清单（12 个）

判据定义：行 405 `if not later.startswith('有')` 分支（claims-none 通道）→ 走 R128/R129 两道可失败判据（行 410–440），之后 `c11_unver += 1; continue`（行 441–442）——即**只要产物不出现自述行且校验式仍成立，就计入 unverifiable，绝不产生 FAIL**。

| id | 函数名/检查块 | 行号 | 判据为空的具体行 | 为什么恒 PASS |
|----|--------------|------|-----------------|--------------|
| 3 | C11 col7 机检 | 405,441-442 | DISC_RECHECK.tsv 行 id=3 col7=`无（R129 裁定：自述行时间上不可能，已撤回声称）` | col7 以「无」开头 ⇒ 行 405 分支；R128/R129 两道判据可拦「偷偷写回自述行」或「校验式失效」，但**拦不住产物内容本身不支持纪律 3**——校验式 `grep=池未加载\(未核验\)\s+0` 恒在锚文件命中，C7 只证锚存在、不证断言语义 |
| 4 | C11 col7 机检 | 405,441-442 | id=4 col7=`无（R129 裁定…）` | 同上；`grep=节号体例通过\s+15` 在锚文件恒命中 |
| 11 | C11 col7 机检 | 405,441-442 | id=11 col7=`无（仅立条当轮自带）` | claims-none 通道；校验式 `grep=控制组总判定：\*\*PASS` 在产物恒命中；无「本轮真回跑」要求 |
| 12 | C11 col7 机检 | 405,441-442 | id=12 col7=`无（仅立条当轮自带）` | 同上 |
| 13 | C11 col7 机检 | 405,441-442 | id=13 col7=`无（仅立条当轮自带）` | 同上 |
| 14 | C11 col7 机检 | 405,441-442 | id=14 col7=`无（仅立条当轮自带）` | 同上 |
| 15 | C11 col7 机检 | 405,441-442 | id=15 col7=`无（仅立条当轮自带）` | 同上 |
| 17 | C11 col7 机检 | 405,441-442 | id=17 col7=`无（仅立条当轮自带）` | 同上 |
| 22 | C11 col7 机检 | 405,441-442 | id=22 col7=`无（R129 裁定…）` | claims-none 通道；`rows=1468` 在产物恒成立；内容可任意改写（只要行数不变） |
| 26 | C11 col7 机检 | 405,441-442 | id=26 col7=`无（仅立条当轮自带）` | 同上；`rows=18712` |
| 27 | C11 col7 机检 | 405,441-442 | id=27 col7=`无（R129 裁定…）` | 同上；`rows=1242` |
| 28 | C11 col7 机检 | 405,441-442 | id=28 col7=`无（R129 裁定…）` | 同上；`rows=4518` |

**关键澄清**：这 12 个 id 并非严格「任何输入下都不可 FAIL」——R128（行 423-427）与 R129（行 434-439）给了两道可失败判据（产物里不得有自述行 / 校验式必须仍成立），C14/C7d 的 sha256 指纹也会因改 col2/3/4/5/6 而 FAIL。但**它们对「纪律内容是否真的成立」这一核心问题恒 PASS**：门禁从不检查这 12 条纪律是否真的被执行、只检查锚文件还在、行数没变。这正是调度卡所指的「永不 FAIL」实质。C11b 自己承认它们是 `gap(claims-none, can never FAIL)=12`。

### 五个「窗口表问题」id 的现态（逐个核实）

| id | 现态 | C7 判据 | 产物存在 | C7 实测结果 |
|----|------|---------|---------|------------|
| 3 | **PASS** | `grep=池未加载\(未核验\)\s+0` | 是（`R17_R61_FACTINDEX_V58/anchor_check.txt`） | grep 命中 ⇒ True |
| 4 | **PASS** | `grep=节号体例通过\s+15` | 是（同上） | grep 命中 ⇒ True |
| 22 | **PASS** | `rows=1468 ✓(rows 1468 vs 1468)` | 是（`R17_R84_T1_NARRATIVE/should_exclude.tsv`） | rows=1468 ⇒ True |
| 27 | **PASS** | `rows=1242 ✓(rows 1242 vs 1242)` | 是（`R17_R81_T2_EVID/_verdicts.tsv`） | rows=1242 ⇒ True |
| 28 | **PASS** | `rows=4518 ✓(rows 4518 vs 4518)` | 是（`R17_R88_T1_SEMDEF/tier_final.tsv`） | rows=4518 ⇒ True |

五个全部 PASS，无 FAIL。第 7 列均已降级为「无（R129 裁定：自述行时间上不可能，已撤回声称）」。

---

## T3 自然真实行：改造为真正判据的现成数据源

对每个 id，给出「若要把判据改成真判据，应断言的现成数据来自哪里」。只允许引用仓库已有事实文件。

| id | 现成数据源文件 | 行号/键名 | 建议断言的现成事实 |
|----|--------------|----------|------------------|
| 3 | `lead/next_re_20261117_r14/R17_R61_FACTINDEX_V58/anchor_check.txt` | `grep=池未加载\(未核验\)\s+0` 命中行 | 断言「未核验」计数 == 0 且退出码非零分支存在（现仅断言字符串存在） |
| 4 | `lead/next_re_20261117_r14/R17_R61_FACTINDEX_V58/anchor_check.txt` | `grep=节号体例通过\s+15` 命中行 | 断言节号体例通过数 == 15（现仅断言数字出现） |
| 11 | `lead/next_re_20261117_r14/_r38/checkC3_report.md` | `控制组总判定：**PASS` 行 | 断言四个子检查各有正/反控记录（C3 纪律要求） |
| 12 | `lead/next_re_20261117_r14/_r38/checkC3_report.md` | `闭集合声明（纪律 12①）` 行 | 断言闭集合声明存在且值域恰为允许集合 |
| 13 | `lead/next_re_20261117_r14/_r38/checkC3.py` | `控制组（四个子检查全都要）` 行 | 断言控制组覆盖 4 个子检查（每个各一正一反） |
| 14 | `lead/next_re_20261117_r14/_r38/checkC3.py` | `checkC3_report_FAIL\.md` 命中行 | 断言 FAIL 报告确实落盘且非空 |
| 15 | `lead/next_re_20261117_r14/_r38/settle_iat.py` | `所在节分布=3` 行 | 断言三方混用量 `339/339` 与节分布 3 一致 |
| 17 | `lead/next_re_20261117_r14/R16_MEASURE_EVID675/mev675.py` | `out_excl=2` 行 | 断言 `stage_scale` 排除了自身产物目录与自身产物文件名两项 |
| 22 | `lead/next_re_20261117_r14/R17_R84_T1_NARRATIVE/should_exclude.tsv` | `rows=1468` | 断言备份副本数 == 1468 且全部落在被测根之外（现只数行数） |
| 26 | `lead/next_re_20261117_r14/R17_R78_T1_RECLASS/files_tier_Cprime.tsv` | `rows=18712` | 断言 why 分布中兜底占比 == 77.7%（现只数行数） |
| 27 | `lead/next_re_20261117_r14/R17_R81_T2_EVID/_verdicts.tsv` | `rows=1242` | 断言 verdict 列存在且分布被实际统计（现只数行数） |
| 28 | `lead/next_re_20261117_r14/R17_R88_T1_SEMDEF/tier_final.tsv` | `rows=4518` | 断言 snap 表与当轮盘上内容同 sha256（现只数行数） |

补充：事实层 `FACT_INDEX.tsv`（`lead/next_re_20261117_r14/R17_R131_FACTINDEX_V601/FACT_INDEX.tsv`）中 F03/F04/F11/F12/F13/F14/F15/F17/F22/F26/F27/F28 十二行均存在且带 `[已证]`/`[流程]` 分级、evidence_paths、limitations 字段——这些是**跨纪律的事实锚**，但 check_disc.py 从不读它们（C19 只读指针 sha/字节数，不读 F 行内容）。对外级判据若要引用「已证」事实，这里是最直接的数据源。

---

## T4 C7 三死分支 + C20 realpath/inode 一致性

### C7 三死分支（if 后 return，无 else）

`run_expr()`（行 150–204）里三个单行 if-return，逐个给上下文：

1. **行 152**（FILE_MISSING，实际可 FAIL）：
```python
150| def run_expr(path, expr):
151|     ap = os.path.join(ROOT, path.replace('\\', '/'))
152|     if not os.path.isfile(ap): return False, 'FILE_MISSING'
153|     head = expr.split(' ')[0]
```
   返回 False（FAIL），不是 PASS；但无 else，后续流程靠 fall-through。

2. **行 172**（BAD_GREPCOUNT，实际可 FAIL）：
```python
170|     rest = expr[len('grepcount='):].strip()
171|     m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
172|     if not m0: return False, 'BAD_GREPCOUNT'
173|     pat, want = m0.group(1), int(m0.group(2))
```

3. **行 203**（none → SKIP，永不 FAIL）：
```python
202|         return (n == int(m3.group(1))), 'rows=%d' % n
203|     if head == 'none': return None, 'none'
204|     return False, 'BAD_EXPR:' + head
```
   返回 `None` ⇒ 行 212 `if ok is None: c7_none += 1`（计为 SKIP）。当前 31 行里 `none=0`，即该分支**从未被触发**。

补充（更接近「死分支」语义的发现）：`exists` / `bytes=` / `none` 三个**形态**在 `run_expr` 里是活代码，但在 31 行 DISC_RECHECK 表中出现次数均为 0（T1 NOTE: `bytes==0, exists==0, none==0`）。`C7_SHAPE_PIN`（行 288–289）把这三个零计数钉住：

```python
288| C7_SHAPE_PIN = {'grep=': 24, 'grepcount=': 3, 'rows=': 4,
289|                 'exists': 0, 'bytes=': 0, 'none': 0}
```

即「三种死分支」真正 dead 的是**数据覆盖**，不是代码本身；C7b 已把「零覆盖」显式钉为不变量（改动即 FAIL）。

### C20 realpath/inode 一致性

实现行：`check_disc.py:1256–1357`（核心比较在 1336、1344）：

```python
1336|         elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ff):
1337|             fails.append('C20 gate_runner.LEDGER=%r vs facts_floors.EXPECT_CUR=%r ...')
1344|         elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ptr):
1345|             fails.append('C20 gate_runner.LEDGER=%r vs pointer=%r ...')
```

- 比较对象：**`os.path.normpath` 后的字符串绝对路径**（C20 块内 `normpath` 出现 4 次）。
- **不是** realpath（C20 块内 0 次）、**不是** inode（`inode`/`st_ino` 0 次）、**不是** sha256（C20 块内 0 次；sha 比对是 C19 行 1172–1176 的职责）。
- 含义：只做词法级路径同一性，符号链接/硬链接换指无法被 C20 发现（边界已在源码行 1249–1255 自述）。

---

## T5 正反控（沙箱实测）

沙箱构造：`/tmp/C_tamper_root/` 下按项目结构软链所有文件，`check_disc.py` 与 `FACT_INDEX_CURRENT.md` 用真实副本（项目目录零改动）。

### 反控（未篡改）

- 退出码 **0**，stdout 32 行，stderr 0 行
- PASS/FAIL 与 T1 **完全一致**（31 PASS / 0 FAIL）；唯一差异是 C20 NOTE 中路径前缀 `/tmp/C_tamper_root/...` vs `/home/t628/projects/ra2-campaign-forge/...`——预期差异，不影响判定。

### 正控（把指针 `V601` → `V999`）

- 退出码 **1**，stdout 28 行，stderr 0 行
- 新增 FAIL **2 个**：
  1. `C19 pointer relative path does not exist: 'lead/.../R17_R131_FACTINDEX_V999/FACT_INDEX.tsv' -> '/tmp/.../V999/FACT_INDEX.tsv' (pointer names a version that is not on disk)`
  2. `C20 gate_runner.LEDGER='/tmp/.../V601/FACT_INDEX.tsv' vs pointer='/tmp/.../V999/FACT_INDEX.tsv' (the runner drives both gates against a version the pointer no longer declares)`
- C19/C20 从 `ok(...)` 变为 `not-run`/`FAIL`。
- 证明 **C19 与 C20 判据是活的**（指针被破坏即 FAIL）。

### 恢复

`/tmp/C_tamper_root/`、`/tmp/C_T1_*.txt`、`/tmp/C_T5*.txt` 均为临时文件，改完即弃；项目目录零改动（sha256 前后一致：`ee8454f7...`）。

---

## 一句话结论

**现态门禁不能真正拦住「纪律断言层面」的回归**：31 项全 PASS 中，12 个 id（3/4/11/12/13/14/15/17/22/26/27/28）的「纪律是否真被回跑」判据恒 PASS（C11b 自己承认 gap=12，C18 承认 claims-有==frozen⇒结构性空转），且 C7 只检查产物存在和字节/行数、不检查内容真假；C20 仅做 normpath 字符串相等、不做 realpath/inode 校验。但门禁**能**拦住「锚文件被删、行数变化、版本指针漂移、free-text 表被改」这类结构性回归（正控实测 C19/C20 FAIL）。**最小可行修补点**：`check_disc.py:405-442`（claims-none 通道）——当前 `if not later.startswith('有')` 直接 `c11_unver += 1; continue`，应在此处对这 12 个 id 增加一条「断言对象内容」的判据（例如对 id 22 断言 `should_exclude.tsv` 的路径列全部在被测根之外、对 id 26 断言 `why` 列兜底占比 == 77.7%），数据源见 T3 表格；仅改一行不够，需要在 405–442 块内为每个 id 接入 T3 列出的现成事实文件。
