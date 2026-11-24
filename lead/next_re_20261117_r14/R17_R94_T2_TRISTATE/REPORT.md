Q1 | 三态定义=有·可核(产物是脚本/可重跑产物,能写出合规自描述行⇒C11强制校验)/有·无自产出机制(确实回跑过,但产物为叙述·他人报告·手编一次性·底座自指,结构上不可能自产出凭证⇒不FAIL但显式计数)/无(仅立条当轮自带,col7原样保留) ; 判别式=<col7以「无」开头→无 ; 否则(col7以「有」开头) expr=col6按首个空格截断(同run_expr去✓注释),若expr匹配 ^(rows|bytes)=\d+$ 或 ^grep=.*\\s\+\d+$ →有·可核,否则→有·无自产出机制> ; 逐行结果见明细(28行实测:可核5=3/4/22/27/28, 无自产出机制12=1/2/5/6/7/8/9/10/18/20/24/25, 无11)
Q2 | 迁移表: 有→有·可核 5 行(3,4,22,27,28) ; 有→有·无自产出机制 12 行(1,2,5,6,7,8,9,10,18,20,24,25;逐行理由见明细) ; 无→无 11 行(11,12,13,14,15,16,17,19,21,23,26 ; 原样保留「无（仅立条当轮自带）」)
Q3 | migrate_tristate.py 已交付(写目标目录,写新文件DISC_RECHECK.tristate.tsv不覆盖原表,按卡未执行) ; 幂等=是(classify对已迁移值原样返回; build_output恒从SRC重算,重跑字节一致) ; 自校验(28×7、其余列未变)=是(内存实跑PASS: 29行/7列/前6列逐字未变/0条有→无/新值闭集合5-12-11)
Q4 | C11 补丁片段=<见明细: 按col7前缀三路分派——有·可核→强制recheck_verify,无合规自描述行即FAIL; 有·无自产出机制→unverifiable++不FAIL; 无→none++; 每次运行打印unverifiable/none计数与id> ; 「不算删记录消告警」的理由=<0行从有改无,17行有全保留「有」前缀、11行无原样;12行仍声明"确实回跑过",仅把结构上不可能满足的凭证要求改成显式unverifiable计数;构造 无→有·可核 实测仍被C11抓(R1 line_count=0→FAIL);门禁未变绿,5条可核仍FAIL>
OVERALL | 只剩少数真 FAIL——按当前产物快照投影,迁移+补丁后门禁从20 FAIL降到8 FAIL(3条C7 rows=N因R55-T1追加自述行+1、5条C11全落在唯一可核的3/4/22/27/28:3/4同产物双自述行冲突、22/27/28的R55不在ROUND_WINDOWS),12条无自产出机制改显式unverifiable计数不再假FAIL;不绿也不掩盖
HANDOFF | migrate_tristate.py 与 REPORT.md 已写入 R17_R94_T2_TRISTATE\ ; 未改 check_disc.py / DISC_RECHECK.tsv,未落盘 DISC_RECHECK.tristate.tsv ; _probe_tristate.py / _verify_tristate.py 为只读证据脚本

---

# R55-T2-TRISTATE · 设计+实现报告（t2-tristate）

> 只读 `lead\`，唯一写目标 `lead\next_re_20261117_r14\R17_R94_T2_TRISTATE\`。
> 禁止改 `check_disc.py` / `DISC_RECHECK.tsv` —— 本报告只交方案 + 迁移脚本 + C11 补丁片段。
> 事实来源：`DISC_RECHECK.tsv`（28 行 7 列）、`DISC_ESTABLISH.tsv`、`check_disc.py`、`recheck_verify.py`、R17_R91/R92/R53 报告、R55-T1/T4 卡。取不到的均标「未取得」。

## 基线对账（先立事实）

- `DISC_RECHECK.tsv` 第 7 列实测只有两值：`有（后续轮回跑）` 17 行、`无（仅立条当轮自带）` 11 行（pwsh 逐行计数）。
- 17 个「有」= {1,2,3,4,5,6,7,8,9,10,18,20,22,24,25,27,28}；其中 5 条可落地 = {3,4,22,27,28}（与 R55-T1 卡、R17_R91/R92「能落地」表一致），另 12 条 = {1,2,5,6,7,8,9,10,18,20,24,25}。
- 当前门禁实跑 `python check_disc.py`（只读）：`[exit 1] 20 FAIL` = 17 条 C11（全部「有」行无合规自述行）+ 3 条 C7（22/27/28 的 `rows=N` 因 R55-T1 追加自述行多算 1）。

## Q1 · 三态定义、判别式、逐行结果

**三态定义**
1. **有·可核**：产物是脚本 + 可重跑产物（机器生成的结构化数据 / 带数值结果行的 check 日志），能写出合规自描述行 ⇒ C11 强制校验。
2. **有·无自产出机制**：确实回跑过，但产物形态（叙述 / 他人报告 / 手编一次性产物 / 底座自指）结构上不可能自产出凭证 ⇒ 不 FAIL，但必须计入 `unverifiable` 并在输出显式打印。
3. **无**：仅立条当轮自带 ⇒ 计入另一计数；col7 原样保留 `无（仅立条当轮自带）`。

**判别式（逐字、可机械执行）**
```
col7 = r[6].strip()
若 col7 以「无」开头                         -> 无（col7 原样不动）
否则（col7 以「有」开头）:
    expr = r[5].strip().split(' ')[0]        # 同 check_disc.run_expr：按首空格去 ✓(...) 注释
    若 re.match(r'^(rows|bytes)=\d+$', expr)
       或 re.match(r'^grep=.*\\s\+\d+$', expr) -> 有·可核
    否则                                     -> 有·无自产出机制
```
- 语义依据：可核行的校验式是**数值可重算式**——`rows=N`/`bytes=N`（机器生成的定长/计数产物）或 `grep=<正则>` 且正则以 `\s+<整数>` 收尾（命中一行机器重算出的结果数字，如「未核验 0」「节号体例通过 15」）。非可核行的校验式是 `grep=<叙述字面>`（匹配正文中一句文字），没有任何机器可重算的数值。
- 判别式只读 col5/col6/col7，不依赖文件是否存在，故 28 行全部可判；对「无」行优先短路，绝不动它们。

**逐行结果（判别式实跑 28 行，与 `_verify_tristate.py` 输出一致）**

| 纪律 | 旧 col7 | 新 col7 | 纪律 | 旧 col7 | 新 col7 |
|---|---|---|---|---|---|
| 1 | 有 | 有·无自产出机制 | 15 | 无 | 无 |
| 2 | 有 | 有·无自产出机制 | 16 | 无 | 无 |
| 3 | 有 | **有·可核** | 17 | 无 | 无 |
| 4 | 有 | **有·可核** | 18 | 有 | 有·无自产出机制 |
| 5 | 有 | 有·无自产出机制 | 19 | 无 | 无 |
| 6 | 有 | 有·无自产出机制 | 20 | 有 | 有·无自产出机制 |
| 7 | 有 | 有·无自产出机制 | 21 | 无 | 无 |
| 8 | 有 | 有·无自产出机制 | 22 | 有 | **有·可核** |
| 9 | 有 | 有·无自产出机制 | 23 | 无 | 无 |
| 10 | 有 | 有·无自产出机制 | 24 | 有 | 有·无自产出机制 |
| 11 | 无 | 无 | 25 | 有 | 有·无自产出机制 |
| 12 | 无 | 无 | 26 | 无 | 无 |
| 13 | 无 | 无 | 27 | 有 | **有·可核** |
| 14 | 无 | 无 | 28 | 有 | **有·可核** |

计数：有·可核 **5**、有·无自产出机制 **12**、无 **11**；col7 变更 17 行，全部是「有→有·X」，0 行「有→无」。

## Q2 · 28 行迁移表与逐行理由

**有→有·可核（5 行）** —— 产物是脚本 + 可重跑产物，校验式为数值可重算：
| 纪律 | 产物 | 校验式 | 为什么可核 |
|---|---|---|---|
| 3 | `R17_R61_FACTINDEX_V58\anchor_check.txt` | `grep=池未加载\(未核验\)\s+0` | verify_anchors 脚本生成的 check 日志；命中一行「未核验 0」数值结果 |
| 4 | 同上 | `grep=节号体例通过\s+15` | 同一 check 日志；命中「节号体例通过 15」数值结果 |
| 22 | `R17_R84_T1_NARRATIVE\should_exclude.tsv` | `rows=1468 ✓(...)` | 机器生成 TSV；行数可重算 |
| 27 | `R17_R81_T2_EVID\_verdicts.tsv` | `rows=1242 ✓(...)` | 机器生成 TSV；行数可重算 |
| 28 | `R17_R88_T1_SEMDEF\tier_final.tsv` | `rows=4518 ✓(...)` | 机器生成 TSV；行数可重算 |

**有→有·无自产出机制（12 行）** —— 逐行给「产物是什么形态」：
| 纪律 | 产物 | 形态 | 逐行理由 |
|---|---|---|---|
| 1 | `R14_COMMON.md` | 底座规则正文 / 自指 | 产物即规则正文本身，锚是「纪律 1 ·」标题自指；无脚本可重跑并自写凭证 |
| 2 | `R14_COMMON.md` | 底座规则正文 / 自指 | 同 1；锚「纪律 2 ·」为正文自指 |
| 5 | `R17_R64_ADEQUACY2\lead_recheck2.tsv` | 他人（审计 T2）报告 | 别人手编的复算表，非本方脚本产物；grep 命中一句叙述 |
| 6 | `R17_R64_ADEQUACY2\lead_recheck2.tsv` | 他人报告 | 同 5 |
| 7 | `R17_R62_ADEQUACY\lead_recheck.tsv` | 他人报告 | 审计复算表，手编一次性 |
| 8 | `R17_R66_FACTINDEX_V511\CHANGES.md` | 叙述 changelog | 手编变更记录，grep 命中一句文字 |
| 9 | `R14_COMMON.md` | 底座规则正文 / 自指 | 锚「⇒纪律 9 ·」为正文自指 |
| 10 | `R17_R66_FACTINDEX_V511\CHANGES.md` | 叙述 changelog | 手编变更记录 |
| 18 | `R17_R70_T1_REPRO\REPORT.md` | 叙述报告 | 执行员手编 REPORT，grep 命中「12:07 无产物」叙述 |
| 20 | `check_disc.py` | 底座自指 | 产物是门禁自身；改它需同步 C10 自登记，不能自写回跑凭证 |
| 24 | `R17_R78_T4_AUDIT30\REPORT.md` | 叙述报告 | 手编审计 REPORT |
| 25 | `R17_R78_T2_REGEXDIFF\REPORT.md` | 叙述报告 | 手编审计 REPORT |

（与 R17_R91/R92 分类完全对齐：类A 叙述/他人报告＝16/18/19/21/23/24/25，其中「有」者 18/24/25；类B 手编一次性＝5/6/7/8/10；类C 底座自指＝1/2/9/20，其中「有」者 1/2/9/20。）

**无→无（11 行）**：11,12,13,14,15,16,17,19,21,23,26 —— col7 原样保留 `无（仅立条当轮自带）`，不参与 C11 强制校验。

## Q3 · 迁移脚本（已交付，未执行）

`R17_R94_T2_TRISTATE\migrate_tristate.py`：
- 读 `DISC_RECHECK.tsv`（SRC）→ 只改 col7 → 写新文件 `DISC_RECHECK.tristate.tsv`（DST，**不覆盖原表**；`SRC==DST` 直接抛错）。
- 幂等：`classify()` 对已是新值的 col7 原样返回；`build_output()` 每次都从 SRC 重算，重复执行产出字节一致。
- 保留其余 6 列逐字不变：`out.append('\t'.join(row[:6] + [new7]))`，前 6 列直接切片原样拼接。
- 写后自校验 `selfcheck()`：29 行（表头+28）、每行 7 列、前 6 列逐字未变、0 条「有→无」、新 col7 属闭集合 {有·可核, 有·无自产出机制, 无...}，并打印三态计数。
- 实跑（内存、不落盘，`python _verify_tristate.py`）：`selfcheck: PASS`，计数 `{'有·可核':5, '有·无自产出机制':12, '无（仅立条当轮自带）':11}`。按卡要求**未调用 `migrate()`**，故 DST 未生成。

## Q4 · check_disc.py 的 C11 补丁片段（仅片段，不改原文件）

替换 `check_disc.py` 第 220–256 行的 C11 段（注释 + `C11_LANDABLE` + 循环 + notes），改为下列三路分派（保留原文件全 ASCII 打印风格，中文用 `\u` 转义）：

```python
# ---- C11 【R55-T2】第 7 列三态机检 ----
# 有·可核          -> 强制走 recheck_verify，无合规自描述行即 FAIL
# 有·无自产出机制  -> 不 FAIL，计入 unverifiable 并显式打印
# 无                -> 计入 none 计数（另一计数）
S_V = '\u6709\u00b7\u53ef\u6838'                      # 有·可核
S_N = '\u6709\u00b7\u65e0\u81ea\u4ea7\u51fa\u673a\u5236'   # 有·无自产出机制
c11_ok = c11_fail = c11_unver = c11_none = 0
unver_ids, none_ids = [], []
_vmod = None
try:
    sys.path.insert(0, R14)
    import recheck_verify as _vmod
except Exception as _e:
    notes.append('C11 verifier import FAILED: %s' % _e)

for r in rows:
    if len(r) != 7:
        continue
    later = r[6].strip()
    if later.startswith(S_N):
        c11_unver += 1; unver_ids.append(r[0])       # 不 FAIL，但显式计数
        continue
    if not later.startswith(S_V):                    # 「无（仅立条当轮自带）」及一切非「有·可核」
        c11_none += 1; none_ids.append(r[0])         # 另一计数
        continue
    # ---- 到这里只剩「有·可核」：强制机检 ----
    if _vmod is None:
        fails.append('C11 id %s verifiable but verifier unavailable' % r[0])
        c11_fail += 1
        continue
    try:
        ok, detail = _vmod.verify_recheck_line(ROOT, r)
    except Exception as e:
        ok, detail = False, 'verifier-error:%s' % e
    if ok:
        c11_ok += 1
    else:
        c11_fail += 1
        fails.append('C11 id %s verifiable but no valid self-description line (%s)'
                     % (r[0], str(detail)[:70]))
notes.append('C11 three-state: ok=%d fail=%d unverifiable=%d none=%d ; unver_ids=%s'
             % (c11_ok, c11_fail, c11_unver, c11_none, ','.join(unver_ids) or '-'))
```

在末尾打印区（原第 269 行附近）追加两行，使计数显式可见：
```python
print('C11 three-state: ok=%d fail=%d unverifiable(no-mechanism)=%d none=%d'
      % (c11_ok, c11_fail, c11_unver, c11_none))
print('C11 unverifiable ids: %s' % (','.join(unver_ids) or '(none)'))
```

**兼容性说明**：C3/C4/C9/C10 完全不动。C3 只要求 col7 以「有」或「无」开头——三态值 `有·可核`/`有·无自产出机制` 均以「有」开头、`无（...）` 以「无」开头，闭集合仍成立；C4 对「有·可核」继续要求产物路径与校验式非空。

### 为什么这不算「删记录消告警」

1. **没有一条记录被降级或删除**：迁移表 17 个「有」全部保留「有」前缀（5 个 `有·可核` + 12 个 `有·无自产出机制`），11 个「无」原样。C11 原样会把 17 行当「有」全查；补丁后仍把 17 行当「有」处理，只是按产物形态分派。纪律条数（28）、C1/C2 的号集都不变。
2. **12 行的声称被保留且更强**：它们仍声明「确实回跑过」，只是把不可能满足的凭证要求（`recheck_verify`）改为显式 `unverifiable` 计数。原先这 12 行产生的是**永远无法通过的假 FAIL**（产物是叙述/他人报告，不可能含自述行）——去掉假 FAIL 是修正判据，不是消真实告警。
3. **造假路径仍被堵死（实测构造）**：`_verify_tristate.py` 把纪律 11 从「无」改写成「有·可核」（伪造回跑），`verify_recheck_line` 返回 `ok=False :: R1 line_count=0 (must be 1)` ⇒ C11 仍 FAIL。所以「无→有造假」在新逻辑下依旧被抓；补丁没有制造「无→有仍 PASS」的新口子。
4. **门禁没有变绿来掩盖**：按当前产物快照，应用迁移+补丁后仍有 8 条真 FAIL（5 条 C11 落在唯一可核的 3/4/22/27/28 + 3 条 C7）。"绿的来源"没有被制造；PASS 语义从「28 条自称回跑」收紧为「5 条可核经机检 + 12 条显式不可验证 + 11 条仅当轮自带」。

## 证据文件（本目录）
- `migrate_tristate.py`：迁移脚本（已交付，未执行）。
- `REPORT.md`：本报告。
- `_verify_tristate.py`：只读探针——判别式逐行结果 + 内存自校验 + 无→有造假构造。
- `_probe_tristate.py`：只读探针——对 5 个可核行实跑 `verify_recheck_line`。

## 未取得 / 边界
- 未取得：5 条可核行的自述行目前**均不合规**——3/4 因 `anchor_check.txt` 被 R55-T1 追加了 2 条自述行（R1 line_count=2），22/27/28 因自述行写 `round=R55` 而 `ROUND_WINDOWS` 只覆盖 r35–r53（R4 no round window）。这些属于 R55-T1 / 门禁轮窗表的职责，本卡不改产品、不改轮窗，仅如实上报。
- 迁移脚本**按卡未执行**，`DISC_RECHECK.tristate.tsv` 未生成；自校验在内存中完成并 PASS。
- 本任务不改 `check_disc.py` / `DISC_RECHECK.tsv`；Q4 仅为 diff 片段，落地由 Lead 决定。
