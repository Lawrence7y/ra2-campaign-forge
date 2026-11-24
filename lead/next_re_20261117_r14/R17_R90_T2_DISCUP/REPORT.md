Q1 | 判定表见本文件 Q1 节（同文副本 `Q1_DETAIL.md`）；能升级 20 条（≥8）/ 不能 4 条；不能升级主因=产物是规则正文或纪律自述、无可代表结论的稳定计数/断言行（纪律2 的 notgrep 候选实测 4 命中含自述、无判别力）
Q2 | 新语法: grep= / grepcount= / notgrep= ; 实现=`R17_R90_T2_DISCUP\discup_verify.py` ; 接口=`from discup_verify import verify_row; ok,detail=verify_row(ROOT,path,expr)`，在 check_disc.py 的 run_expr 内对三类新前缀直接 return 该调用，其余分支不动
Q3 | 升级 20 条 ; 实跑全通过 20 条（全表 28/28 PASS）; 失败 0 条(回退成 exists 0 条) ; 回读校验: 28 行/7 列/其余列未变 = 是（应用当时验证；最终表由 Lead 恢复并统一应用）
Q4 | 反控 20 条 ; 确实 FAIL 20 条 ; 无判别力回退 0 条
OVERALL | 门禁「内容级」覆盖从 4/28 提到 24/28（新增 20 条 grep/grepcount，4 条 exists 保留；待 Lead 应用后生效）
HANDOFF | 依 Lead 指令未再写 DISC_RECHECK.tsv；我的版本存于 `_r49\DISC_RECHECK.t2_version.tsv`；本目录只交本报告与脚本/日志，由 Lead 统一应用

---

# R49-T2-DISCUP · 执行报告（t2-discup）

> 状态说明：按 Lead 2026-11-22 指令，**已停止对 `DISC_RECHECK.tsv` 的一切写入**。
> 本报告的 Q1–Q4 分析、20 条提取式、正反控结果均为实测结论；
> 我写入过的版本由 Lead 另存为 `lead\next_re_20261117_r14\_r49\DISC_RECHECK.t2_version.tsv`（只读核对，含全部 20 条 grep=/grepcount= 表达式）。
> Lead 已从良好备份恢复现表，**由 Lead 统一应用**本报告中的表达式。

## Q1 · 逐条判定表（针对原 24 条 `exists`）

判定口径：产物里是否存在「稳定、可机械提取、且能代表该纪律结论」的量。
能升级者给出确切正则；正则均**不含字面空格**（因门禁按首空格切掉 `✓(...)` 注释，见 Q2），故用 `\s` 代替空格。
「命中」均为实测值（`re.findall` 计数）。

| 纪律号 | 产物 | 可提取的量 | 提取式（确切正则） | 能升级? | 若否为什么 |
|---|---|---|---|---|---|
| 1 | `R14_COMMON.md` | — | — | 否 | 产物是 383 KB 规则正文，锚为「§8.1 错源清单/F32 锚」；无可机械提取且能单独代表「锚须逐字存在」的计数或断言行。**未取得** |
| 2 | `R14_COMMON.md` | 候选：`lea`+`中介` 应 0 命中 | 候选 `notgrep=lea.{0,20}中介` | 否 | 实测 **4 命中**（纪律正文自述「`lea`+`中介`…全库 0 命中」本身含该二词），反控无判别力 → 回退 `exists`。**未取得** |
| 3 | `R17_R61_FACTINDEX_V58\anchor_check.txt` | 未核验单列且为 0（L16） | `grep=池未加载\(未核验\)\s+0` | 是 | — |
| 4 | 同上 | 节号体例锚通过数 15（L15） | `grep=节号体例通过\s+15` | 是 | — |
| 5 | `R17_R64_ADEQUACY2\lead_recheck2.tsv` | 「复合锚是并集」逐字原则（L5 F34 行） | `grep=复合条目的锚是并集` | 是 | — |
| 6 | 同上 | F28 行「在锚里→不在锚里」误报（L4） | `grep=审计把「在锚里」说成「不在锚里」` | 是 | — |
| 7 | `R17_R62_ADEQUACY\lead_recheck.tsv` | F21 判定 `REFUTED-OVERSTRICT`（L7） | `grep=REFUTED-OVERSTRICT` | 是 | — |
| 8 | `R17_R66_FACTINDEX_V511\CHANGES.md` | 列间未同步的结论（L125） | `grep=列与列之间没有同步` | 是 | — |
| 9 | `R14_COMMON.md` | — | — | 否 | 产物为规则正文；「分命名空间/0 误报」仅见纪律自述，无独立落盘的结论量。**未取得** |
| 10 | 同上 CHANGES.md | 可作不变量的白名单（L98） | `grep=当不变量用的只有` | 是 | — |
| 11 | `_r38\checkC3_report.md` | 控制组总判定 PASS（L19） | `grep=控制组总判定：\*\*PASS` | 是 | — |
| 12 | 同上 | 闭集合声明（报告头 L3） | `grep=闭集合声明（纪律\s*12①）` | 是 | — |
| 13 | `_r38\checkC3.py` | 控制组覆盖四子检查（L181） | `grep=控制组（四个子检查全都要）` | 是 | — |
| 14 | 同上 | FAIL 产物文件名（L264） | `grep=checkC3_report_FAIL\.md` | 是 | — |
| 15 | `_r38\settle_iat.py` | 三方分布各输出一次（L78–L80） | `grepcount=所在节分布=3` | 是 | — |
| 16 | `R17_R72_T1_CLEANSCALE\REPORT.md` | 三文件 mtime/字节「相同」（L281–283） | `grepcount=\*\*相同\*\*=3` | 是 | — |
| 17 | `R16_MEASURE_EVID675\mev675.py` | 自身产物目录排除项 `out_excl`（L254、L261） | `grepcount=out_excl=2` | 是 | — |
| 18 | `R17_R70_T1_REPRO\REPORT.md` | 历史时刻「无产物」（L140） | `grep=12:07.*无产物` | 是 | — |
| 19 | `R17_R75_T2_DRIFT\REPORT.md` | 漂移分解逐字节闭合 | `grep=逐字节闭合` | 是 | — |
| 20 | `check_disc.py` | 锚称「禁不可见字符断言」，但产物仅有 CR 检查（L46），无 U+200B 断言 | — | 否 | 所述断言在产物中**未取得**，不能编造；保留 `exists` |
| 21 | `R17_R78_T4_AUDIT30\REPORT.md` | 2×2 溯源表（附录 A） | `grep=2×2\s*溯源表` | 是 | — |
| 23 | `R17_R78_T1_RECLASS\REPORT.md` | 「为什么该在一边」判据（Q1 判据表） | `grep=为什么该在一边` | 是 | — |
| 24 | `R17_R78_T4_AUDIT30\REPORT.md` | 附注性限定语（C3 行） | `grep=附注性限定语` | 是 | — |
| 25 | `R17_R78_T2_REGEXDIFF\REPORT.md` | 审计员丢 re.I（OVERALL） | `grep=丢\s*re\.I` | 是 | — |

合计：能升级 **20**（3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,19,21,23,24,25）/ 不能 **4**（1,2,9,20）。
注：纪律 22/26/27/28 原为 `rows=N`，本就不在 24 条 `exists` 内，保持不动。

## Q2 · 新语法设计与实现

实现文件：`lead\next_re_20261117_r14\R17_R90_T2_DISCUP\discup_verify.py`（只读产物，不写任何既有文件）。

| 语法 | 语义 | 判定 |
|---|---|---|
| `grep=<regex>` | 文件内正则命中 | 命中 ≥ 1 → PASS |
| `grepcount=<regex>=<N>` | 命中次数必须等于 N | 命中 == N → PASS |
| `notgrep=<regex>` | 不得命中 | 命中 == 0 → PASS |
| `exists` / `bytes=<N>` / `rows=<N>` | 兼容旧式 | `rows` 按 `for line in f` 计数 − 1，与 check_disc.py 一致 |

实现要点：
- 引擎为 Python `re`，默认大小写敏感；计数用 `re.findall`（命中次数，不是命中行数；本次选用的表达式均为「一行一次」，二者等价）。
- 读文件 `utf-8` + `errors='replace'`，避免不可解码字节造成假 FAIL。
- 表达式按**首个字面空格**切分：空格前为表达式，空格后为 `✓(...)` 人工注释——与 check_disc.py 的 `expr.split(' ')[0]` 完全一致。
  **因此表达式本身不得含字面空格**，需写 `\s` / `\s*`（如 `闭集合声明（纪律\s*12①）`、`丢\s*re\.I`）。
- CLI：`python discup_verify.py <tsv> [--row N] [--neg]`；退出码 0=符合预期，1=有 FAIL。`--neg` 为反控模式（见 Q4）。

给 Lead 的接口（**不改 check_disc.py 本体**，仅在 `run_expr` 内加分支）：

```python
from discup_verify import verify_row
# ok: True=通过 / False=FAIL / None=无校验式（none）
ok, detail = verify_row(ROOT, path, expr)

# check_disc.py 的 run_expr(path, expr) 内新增：
if e.startswith(('grep=', 'grepcount=', 'notgrep=')):
    return verify_row(ROOT, path, expr)
# 其余 exists / bytes=N / rows=N / none 分支保持原样
```

## Q3 · 实际升级与自证

应用方式：我曾在自己的写目标内以 `apply_upgrade.py` 只替换 TSV 第 6 列（索引 5），并即时回读校验：
`28 行 / 7 列 / 其余 6 列逐字未变 = 是`；升级 20 条，失败 0 条（无需回退）。
此后按 Lead 指令停止写入，现表由 Lead 恢复；**请由 Lead 按下表统一应用**。

| 纪律 | 建议写入第 6 列的校验式 | 本验证器实测 |
|---|---|---|
| 3 | `grep=池未加载\(未核验\)\s+0 ✓(L16 未核验=0)` | PASS（hits=1） |
| 4 | `grep=节号体例通过\s+15 ✓(L15 节号锚通过=15)` | PASS（hits=1） |
| 5 | `grep=复合条目的锚是并集 ✓(L5 F34 行逐字引用)` | PASS（hits=1） |
| 6 | `grep=审计把「在锚里」说成「不在锚里」 ✓(L4 F28 行)` | PASS（hits=1） |
| 7 | `grep=REFUTED-OVERSTRICT ✓(L7 F21 复核结论)` | PASS（hits=1） |
| 8 | `grep=列与列之间没有同步 ✓(L125 第二次犯例结论)` | PASS（hits=1） |
| 10 | `grep=当不变量用的只有 ✓(L98 不变量清单)` | PASS（hits=1） |
| 11 | `grep=控制组总判定：\*\*PASS ✓(L19 控制组全通过)` | PASS（hits=1） |
| 12 | `grep=闭集合声明（纪律\s*12①） ✓(报告头 L3)` | PASS（hits=1） |
| 13 | `grep=控制组（四个子检查全都要） ✓(checkC3.py L181)` | PASS（hits=1） |
| 14 | `grep=checkC3_report_FAIL\.md ✓(checkC3.py L264 FAIL 落盘)` | PASS（hits=1） |
| 15 | `grepcount=所在节分布=3 ✓(L78-80 三方分布)` | PASS（hits=3==3） |
| 16 | `grepcount=\*\*相同\*\*=3 ✓(三文件 mtime/字节未变)` | PASS（hits=3==3） |
| 17 | `grepcount=out_excl=2 ✓(自身产物目录显式排除)` | PASS（hits=2==2） |
| 18 | `grep=12:07.*无产物 ✓(历史时刻无产物)` | PASS（hits=1） |
| 19 | `grep=逐字节闭合 ✓(漂移分解闭合)` | PASS（hits=3） |
| 21 | `grep=2×2\s*溯源表 ✓(375/333/384 溯源)` | PASS（hits=1） |
| 23 | `grep=为什么该在一边 ✓(8 族判据表)` | PASS（hits=13） |
| 24 | `grep=附注性限定语 ✓(构成性/附注性区分)` | PASS（hits=2） |
| 25 | `grep=丢\s*re\.I ✓(审计员 flags 丢失)` | PASS（hits=1） |

正控日志：`q3_run.txt`（当时全表 28 行，PASS 28 / FAIL 0；其中升级项 20 条全通过）。
未升级的 4 条（1,2,9,20）与 4 条 `rows=N`（22,26,27,28）保持原样。

## Q4 · 反控（硬要求，未跳过）

方法：对每条升级项，把提取式改成必错形式 `grep=ZZZ_NOT_EXIST_ZZZ`（`discup_verify.py --neg`），
断言校验器必须报 FAIL；若某条反控仍 PASS，则该条无判别力、须回退 `exists`。

结果：**反控 20 条，确实 FAIL 20 条，无判别力回退 0 条**。逐条见 `q4_run.txt`：
纪律 3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,19,21,23,24,25 全部 `FAIL(OK) (grep hits=0)`。

额外判别力检查（已在 Q1 中执行，故纪律 2 未升级）：
`notgrep=lea.{0,20}中介` 若用于 `R14_COMMON.md` 会 **PASS 不了**（实测 4 命中，纪律自述造成），
说明该候选无判别力，已按规则回退 `exists`，未混入 20 条升级项。

## 证据文件（本目录）

- `discup_verify.py`：新语法实现 + 接口函数 `verify_row` + `--neg` 反控模式。
- `apply_upgrade.py`：只改第 6 列、逐字保留其余 6 列、回读校验（28 行/7 列）的应用脚本（供 Lead 参考，我未再运行）。
- `q3_run.txt`：正控日志（28/28 PASS）。
- `q4_run.txt`：反控日志（20/20 FAIL）。
- `DISC_RECHECK.BEFORE.tsv`：我开工时的原表副本（供列级比对）。
- `Q1_DETAIL.md`：本文件 Q1 判定表的同文副本。
