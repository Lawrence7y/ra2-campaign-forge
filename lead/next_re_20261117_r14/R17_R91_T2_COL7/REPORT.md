Q1 | 可机检痕迹: 有 0/28 ; 形态=<逐条扫描 28 个产物：无任何一条含「自描述回跑行」(selfLine 命中仅纪律 1/2/9/20，且均为文档正文在讨论门禁本身，不是回跑证据)；零散痕迹(日期/轮次 token/纪律号/回跑词)在「有」「无」两侧都出现、无判别力；mtime 全部被批量重置为 2026-11-22 且多文件同秒，不可信；lead/ 全树 git 未跟踪(末提交 2026-11-12)，无外部可信时钟；独立回跑执行日志 未取得> ; 有/无 逐条见明细
Q2 | 自描述行格式=DISC_RECHECK discipline=<N> round=<Rxx> at=<ISO8601> anchors=<sha256:HEX64> conclusion=<PASS|FAIL|UNKNOWN>（逐字：字段顺序固定、单空格分隔、行首顶格、每产物仅一条） ; 校验 4 条=<①产物内含且仅含一条前缀匹配行 ②discipline==该 TSV 行号 ③at>该纪律立条落盘时刻(取自 DISC_ESTABLISH.tsv，缺则 FAIL) ④round 序号>立条轮且 at 落在该 round 的 [start,end] 窗口(取自 DISC_ROUNDS.tsv，缺则 FAIL)；另建议 ⑤anchors==sha256(TSV 第4列) ⑥conclusion∈闭集合> ; 接口=<交付独立模块 recheck_verify.py::verify_recheck_line(root,row)->(ok,detail)；Lead 在 check_disc.py 增 C11：col7 以「有」开头者调用之，FAIL 进 fails，并打印 unverifiable 计数；C1–C10 不动>
Q3 | 能落地 12/28 ; 不能落地 16/28 ; 不能落地原因: <类A 叙述/他人报告、无自产出机制=7条(16,18,19,21,23,24,25；21 与 24 同文件却分别标「无」「有」)> <类B 手编或一次性产物、无可重跑生成器=5条(5,6,7,8,10)> <类C 底座/门禁文档自指或本卡禁改=4条(1,2,9,20)> ; 能落地=3,4,11,12,13,14,15,17,22,26,27,28
Q4 | 建议=部分落地+显式计数 ; 理由=<维持现状=col7 纯自述、已实测「无→有」仍 exit 0，零改进；部分落地把 12 条从不可见自述改成结构化、跨字段一致性校验的失败闭门(C11 FAIL 进退出码)，16 条显式标 unverifiable 并计数，使 PASS 不再隐含「28 条回跑全证」——正是 §2.41/§2.42 已承认的错误读法；12 条均有现成可重跑生成器/校验器可在产物内自写该行，不需编造时间戳；但立条落盘时刻 未取得(§2.14–§2.37 只标日期无时分秒)，须 Lead 补 DISC_ESTABLISH.tsv，缺此则 ③ 退化为弱校验并须如实标注>
FALSIFY | 该方案什么情况下会误判为真: <①协同伪造：行为者把 col7「无→有」同时在产物手写一条格式全合法的 DISC_RECHECK 行(discipline 对、at 晚于立条、round 与 at 同窗口)，①–④ 全过而从未回跑——因所有时间戳与两张注册表皆同一行为者自写、无外部可信时钟；②把 DISC_ESTABLISH 落盘时刻前移或放宽 DISC_ROUNDS 窗口，任意 at 过 ③④；③产物在立条当轮已含全部 grep 目标串，事后仅追加行并把 at 写成回跑时刻(「事后补」冒充「产物自写」)，校验器只读行+命中、不核内容写入时刻，仍 PASS；④同日粒度：立条与回跑同为 2026-11-22 且表只记日期，任意当日 at 过 ③；⑤误用 mtime 作 at(实测全被批量重置同日)，把拷贝/恢复时间当回跑时间；⑥行只证明「声称跑过」，不证明 ran 了该纪律的判据(anchors 哈希可被同一个自写者重算)>
OVERALL | 该空洞能从「col7 纯自述、已证无→有仍 PASS」收窄到「12/28 条有结构化且跨字段一致性校验的回跑自述 + 16/28 显式 unverifiable 计数、PASS 不再隐含全证」；但因 lead/ 全树 git 未跟踪、无独立可信时钟/执行日志，协同伪造仍可绕过 ①–④，只能关到「自述一致性+显式不可验证」，关不到「回跑事实已证」

---

# R51-T2-COL7 · 设计+实现报告（t2-col7）

> 写目标仅本目录；`check_disc.py` 与 `DISC_RECHECK.tsv` 一个字节未改。
> 所有结论来自对 `lead\next_re_20261117_r14\` 的只读实测；取不到者写「未取得」。

## 证据基线（实测）

- `DISC_RECHECK.tsv`：28 行 + 表头，7 列；第 7 列「有（后续轮回跑）」17 条、「无（仅立条当轮自带）」11 条。
- `check_disc.py`（R49）：C3 只核第 7 列以「有/无」开头；C4 以「有」为触发条件核产物路径与校验式非空；C7 真跑校验式。**无任何一处读产物内容去核「回跑真伪」**；stdout 末行自承 `Row-7 truth is NOT machine-verified`（L231）。
- `R14_COMMON.md` §2.42 反控 H：第 7 列「无→有」造假 → PASS exit 0；硬化后仍未关（§2.42 四.1）。
- 28 个产物路径全部存在；mtime 27 条为 2026-11-22、1 条为 2026-11-21，多文件同秒 → 批量重置特征，不可作回跑时刻。
- git：仓库根存在，末提交 `3872ef6` 于 2026-11-12；`lead/.../DISC_RECHECK.tsv`、`R14_COMMON.md` 均为 `??`（未跟踪）→ 无外部可信时间戳。
- 先验工作 `R17_R90_T2_DISCUP/REPORT.md`：已把 24 条 `exists` 中 20 条升级为内容级 `grep/grepcount`（即现表状态），但那是「产物含某断言行」，与「第 7 列所述回跑真的发生过」是两个问题，不解决本空洞。

## Q1 明细 · 28 条纪律的痕迹分类

列：`纪律号 | 现有产物 | 有无可识别痕迹 | 痕迹形态 | 能否机检`

判据：可机检痕迹 = 产物内有一条由产物自己在回跑时写出、能唯一指认「回跑这次动作」的记录。四类候选痕迹（时间戳晚于立条 / 纪律编号字样 / 回跑词+数字 / 独立执行日志）逐条核对如下。

| 纪律号 | 现有产物 | 有无可识别痕迹 | 痕迹形态 | 能否机检 |
|---|---|---|---|---|
| 1 | R14_COMMON.md | 无 | 有 ISO 日期/R 轮/回跑词/「纪律 1」字样，但均为规则正文在叙述门禁；`DISC_RECHECK` 命中是 §2.40 讨论本身 | 否 |
| 2 | R14_COMMON.md | 无 | 同上；「纪律 2」在正文；无独立回跑量（先验 DISCUP 实测 notgrep 4 命中含自述、无判别力） | 否 |
| 3 | anchor_check.txt | 无 | 仅结果数字「未核验 0 / 节号体例 15」(L15–16)；无日期、无轮次、无回跑词、无纪律号 | 否 |
| 4 | anchor_check.txt | 无 | 同上 | 否 |
| 5 | lead_recheck2.tsv | 无 | 含「纪律 5」「纪律 6」逐字引用，无日期/轮次/回跑词；手编表 | 否 |
| 6 | lead_recheck2.tsv | 无 | 同上，且无本纪律号 | 否 |
| 7 | lead_recheck.tsv | 无 | 含 `REFUTED-OVERSTRICT` 与 R 轮 token，无日期/回跑词；手编表 | 否 |
| 8 | CHANGES.md | 无 | 含回跑词/R 轮/时刻，为叙述性变更日志；无自产出回跑行 | 否 |
| 9 | R14_COMMON.md | 无 | 同 1；「纪律 9」在正文 | 否 |
| 10 | CHANGES.md | 无 | 同 8 | 否 |
| 11 | _r38/checkC3_report.md | 无 | 含 R 轮/纪律 11·12 字样，无日期/回跑词；且 col7=「无」（当轮自带），正说明该格式产物不等于回跑 | 否 |
| 12 | _r38/checkC3_report.md | 无 | 同上 | 否 |
| 13 | _r38/checkC3.py | 无 | 含回跑词/R 轮，无日期；脚本本身是检查器、非回跑记录 | 否 |
| 14 | _r38/checkC3.py | 无 | 同上 | 否 |
| 15 | _r38/settle_iat.py | 无 | 四类标记全无 | 否 |
| 16 | R17_R72_T1_CLEANSCALE/REPORT.md | 无 | 含 ISO 日期/回跑词/R 轮/时刻，却标「无」→ 反证这些标记无判别力 | 否 |
| 17 | R16_MEASURE_EVID675/mev675.py | 无 | 含回跑词/R 轮，无日期；脚本 | 否 |
| 18 | R17_R70_T1_REPRO/REPORT.md | 无 | 含 ISO 日期/回跑词/R 轮及 `12:07` 时刻（校验式即 grep 它），为当日复现叙述 | 否 |
| 19 | R17_R75_T2_DRIFT/REPORT.md | 无 | 含 ISO 日期/回跑词/R 轮，却标「无」 | 否 |
| 20 | check_disc.py | 无 | `DISC_RECHECK` 命中是脚本名/注释；无回跑自述行；门自身 | 否 |
| 21 | R17_R78_T4_AUDIT30/REPORT.md | 无 | 与纪律 24 **同一文件**，此处标「无」→ 直接证明第 7 列不是文件属性 | 否 |
| 22 | R17_R84_T1_NARRATIVE/should_exclude.tsv | 无 | 四类标记全无；纯数据表 | 否 |
| 23 | R17_R78_T1_RECLASS/REPORT.md | 无 | 含日期/回跑词/纪律号，却标「无」 | 否 |
| 24 | R17_R78_T4_AUDIT30/REPORT.md | 无 | 与纪律 21 同一文件却标「有」→ 同上 | 否 |
| 25 | R17_R78_T2_REGEXDIFF/REPORT.md | 无 | 含回跑词/时刻，无日期 | 否 |
| 26 | R17_R78_T1_RECLASS/files_tier_Cprime.tsv | 无 | 含回跑词/R 轮，却标「无」；纯数据表 | 否 |
| 27 | R17_R81_T2_EVID/_verdicts.tsv | 无 | 四类标记全无；纯数据表 | 否 |
| 28 | R17_R88_T1_SEMDEF/tier_final.tsv | 无 | 含回跑词，无日期；纯数据表 | 否 |

结论：现有产物中**不存在**能区分「有」与「无」的机械痕迹。纪律 21/24 共用一文件却取值相反，是最干净的反例——第 7 列是人为断言，不是可从产物推导的事实。

## Q2 详细设计

### 2.1 自描述行格式（逐字）

```
DISC_RECHECK discipline=<N> round=<Rxx> at=<ISO8601> anchors=<sha256:HEX64> conclusion=<PASS|FAIL|UNKNOWN>
```

字段规范：

| 字段 | 取值 | 说明 |
|---|---|---|
| 前缀 | `DISC_RECHECK` | 行首顶格，单空格分隔；每产物恰好一条 |
| `discipline` | 十进制整数 1..28，无前导零 | 必须等于所在 TSV 行的纪律号 |
| `round` | `R` + 2–3 位数字，如 `R61` | 执行本次回跑的轮次编号 |
| `at` | `YYYY-MM-DDTHH:MM:SS+HH:MM` | 执行时刻，带显式时区偏移；取自执行时钟，非 mtime |
| `anchors` | `sha256:` + 64 位小写十六进制 | = SHA256(UTF-8(TSV 第 4 列「必查的现有数据锚」逐字串))，把该行绑到本纪律的锚 |
| `conclusion` | `PASS` / `FAIL` / `UNKNOWN` | 本次回跑的结论；闭集合，禁止「无/空/xxx」 |

示例（纪律 3；哈希为实测值，锚串 `v5.8 基线：人工核验类 0`）：

```
DISC_RECHECK discipline=3 round=R61 at=2026-11-22T10:23:01+08:00 anchors=sha256:22395a6103650a4840fe208f6a00fd2ae02f14dce68fd37d9098e5917b616ffa conclusion=PASS
```

「由产物自己写出」的落地方式：由生成该产物的**可重跑检查器**在其输出末尾追加该行（脚本自写或 stdout 重定向落盘），不在事后由人手工粘贴。校验器只核该行的存在与一致性；**「是否事后补」无法由文本判定**（见 FALSIFY ③）。

### 2.2 立条时刻与轮次窗口（必需外部输入，当前 未取得）

- `DISC_ESTABLISH.tsv`（建议新增，Lead 拥有）：`纪律号 | 立条节 | 立条轮 | 落盘时刻ISO8601`。§2.14–§2.37 现只写「2026-11-22」无时分秒 → **逐条落盘时刻 未取得**，须由 Lead 补；缺行/缺文件 → C11 FAIL（fail-closed）。
- `DISC_ROUNDS.tsv`（建议新增）：`轮次 | start | end`，给出每轮时间窗口；用于校 `round` 与 `at` 不矛盾。缺失 → FAIL。
- 独立回跑执行日志：**未取得**；若存在，可作为 `at` 的第二来源以削弱 FALSIFY ①。

### 2.3 校验器伪代码

```
verify_recheck_line(root, row):
    N    = int(row[0]); path = row[4]; anchor4 = row[3]
    txt  = read_utf8_with_replace(join(root, path))

    # ① 行存在且唯一
    hits = [l for l in txt.splitlines()
            if l.startswith("DISC_RECHECK ")]
    if len(hits) != 1: return (False, "R1 line_count=%d" % len(hits))

    toks = hits[0].split(" ")          # 单空格；6 个 token
    if len(toks) != 6: return (False, "R1 token_count")
    f = {}
    for t in toks[1:]:
        k, _, v = t.partition("=")
        if k in f or not v: return (False, "R1 bad_token")
        f[k] = v
    if set(f) != {discipline, round, at, anchors, conclusion}:
        return (False, "R1 field_set")

    # ② discipline 与行号一致
    if not f["discipline"].isdigit() or int(f["discipline"]) != N:
        return (False, "R2 discipline %s != %d" % (f["discipline"], N))

    # ③ at 晚于立条落盘时刻
    est = ESTABLISH.get(N)
    if est is None: return (False, "R3 no establish row (unverifiable)")
    at = parse_iso8601_strict(f["at"])     # 严格格式+时区；失败即 False
    if at is None: return (False, "R3 bad ISO8601")
    if at <= est.landing_at: return (False, "R3 at<=establish")

    # ④ round 与 at 不矛盾
    if not re.fullmatch(r"R\d{2,3}", f["round"]): return (False, "R4 bad round")
    if int(f["round"][1:]) <= est.round_no: return (False, "R4 round<=establish")
    win = ROUNDS.get(f["round"])
    if win is None: return (False, "R4 no round window")
    if not (win.start <= at <= win.end): return (False, "R4 at outside round window")

    # ⑤ anchors 绑定（建议，非卡面 4 条之一）
    if f["anchors"] != "sha256:" + sha256_hex(anchor4):
        return (False, "R5 anchors mismatch")

    # ⑥ conclusion 闭集合
    if f["conclusion"] not in {"PASS", "FAIL", "UNKNOWN"}:
        return (False, "R6 conclusion not closed set")

    return (True, "ok")
```

### 2.4 与 check_disc.py 的接口（不改本体，交付模块由 Lead 接入）

交付模块：`R17_R91_T2_COL7\recheck_verify.py`（本卡只交方案与伪代码；实现文件随方案给出接口，不写 `check_disc.py`）。

```python
# recheck_verify.py
def verify_recheck_line(root, row):
    """row = DISC_RECHECK.tsv 的一行 split('\\t') 结果
       return (ok: bool|None, detail: str)
       None = unverifiable（立条时刻/轮次窗口未登记），不进 fails 但进显式计数"""
    ...
```

Lead 在 `check_disc.py` 的接入点（描述，不实施）：

1. `import recheck_verify`；在现有 C3/C4 循环后新增 **C11** 循环：
   ```python
   unverifiable = []
   for r in rows:
       if len(r) != 7: continue
       if not r[6].strip().startswith('\u6709'):      # 第 7 列以「有」开头
           continue
       ok, detail = recheck_verify.verify_recheck_line(ROOT, r)
       if ok is False:  fails.append('C11 id %s %s' % (r[0], detail))
       elif ok is None: unverifiable.append(r[0])
   ```
2. stdout 增两行：`C11 recheck-line verified <n> ; unverifiable <k>` 与 `unverifiable ids: ...`；`k>0` 时打印边界声明。
3. 退出码语义不变：`fails` 非空 → 1，否则 0。**unverifiable 不计入 fails，但必须计数**——否则又造一个「看起来在查、实则 PASS」的口子。
4. 反控（给 Lead 的自证清单）：把某「有」行 col7 保持、产物删掉自述行 → C11 必须 FAIL；把自述行 discipline 改成别的号 → FAIL；把 at 改成立条之前 → FAIL；把 round 改成小于立条轮 → FAIL；对「无」行补一行合法自述但不改 col7 → C11 不报（col7 仍「无」），说明方向单一，符合设计。

## Q3 明细 · 能落地 12 / 不能落地 16

「能落地」= 存在可重跑的检查器/生成器，运行它即可在产物内自写该行，不需人手编造时间戳。

| 类 | 纪律号 | 条数 | 判据 / 依据 |
|---|---|---|---|
| 能落地 | 3,4 | 2 | `R17_R61_FACTINDEX_V58/verify_anchors.ts` 明确标「可复跑」（node --experimental-strip-types），其 stdout 即 `anchor_check.txt`，可在输出末尾追加自述行 |
| 能落地 | 11,12 | 2 | `_r38/checkC3.py` 可复跑，产出 `checkC3_report.md`，自写该行 |
| 能落地 | 13,14 | 2 | `_r38/checkC3.py` 自身为检查器，可在运行时写自身注释行 |
| 能落地 | 15 | 1 | `_r38/settle_iat.py` 可复跑，脚本自报 |
| 能落地 | 17 | 1 | `R16_MEASURE_EVID675/mev675.py` 可复跑，脚本自报 |
| 能落地 | 22 | 1 | `R17_R84_T1_NARRATIVE/q1_narrative.py`/`q4_sample.py` 生成 `should_exclude.tsv` |
| 能落地 | 26 | 1 | `R17_R78_T1_RECLASS/decide_cprime.py` 生成 `files_tier_Cprime.tsv` |
| 能落地 | 27 | 1 | `R17_R81_T2_EVID/judge_q4.py`/`judge_q4_v2.py` 生成 `_verdicts.tsv` |
| 能落地 | 28 | 1 | `R17_R88_T1_SEMDEF/decide_semdef.py`/`closure.py` 生成 `tier_final.tsv` |
| **小计** | | **12** | |
| 不能·类A 叙述/他人报告、无自产出机制 | 16,18,19,21,23,24,25 | 7 | 产物为 T1/T2/T4 的执行员 `REPORT.md`，由叙述写出、无重跑生成器；在其内追加行即「事后补」，违格式硬要求。21/24 同文件不同 col7 尤证 |
| 不能·类B 手编/一次性产物、无可重跑生成器 | 5,6,7,8,10 | 5 | `lead_recheck2.tsv`/`lead_recheck.tsv` 为 Lead 手编复核表（目录内无生成器，仅 build_disc.py 引用路径）；`CHANGES.md` 为叙述变更日志。`未取得`任何可重跑生成器 |
| 不能·类C 底座/门禁文档自指或本卡禁改 | 1,2,9,20 | 4 | 1/2/9 产物是 `R14_COMMON.md` 自身（纪律定义正文），写入自述行=自我引用且无独立回跑量；20 是 `check_disc.py`（门自身，本卡禁改，且「禁不可见字符断言」在产物中 未取得，见先验 DISCUP Q1） |
| **小计** | | **16** | |

注：12 条中有 5 条（22/26/27/28 及 3/4 之一）原 col7 为「无」或产物为数据表；能否落地取决于生成器是否存在，与当前 col7 取值无关。类 B/C 的「未取得」是可复核的缺口，不是编造。

## Q4 详细建议

**建议：部分落地 + 显式计数，不维持现状。**

理由：

1. 维持现状已被实测否证：§2.42 反控 H（无→有）PASS exit 0，且硬化后 C3 仍只核闭集合。零成本、零改进。
2. 部分落地有真实判别力：C11 使「col7 写有但产物没自述行 / 行号不符 / 时刻矛盾」从静默 PASS 变为 FAIL 并影响退出码——这是目前唯一能让「无→有」造假不再免费的机检增量。
3. 显式计数防止新伪通过：16 条不可落地者标 `unverifiable` 并打印计数，PASS 的语义变为「12 条自述一致 + 16 条不可验证」，而非 §2.41 已警告的「28 条全证」。若不计数，等于新造一个口子。
4. 不编造：12 条均由现成可重跑机制写出，无需伪造时间戳；立条落盘时刻当前 未取得，必须由 Lead 补 `DISC_ESTABLISH.tsv` 才能让 ③ 生效——这是方案的前置依赖，不是可跳过的细节。
5. 代价与边界：银行的是「自述一致性」，不是「回跑事实」。必须把 FALSIFY 六条随门禁输出一起打印，否则PASS 又会被误读。

## FALSIFY 详细（硬要求，未跳过）

该方案在以下情形会把「假回跑」误判为真：

1. **协同伪造**：行为者同时改 col7「无→有」并在产物手写一条格式全合法的自述行（discipline 对、at 晚于立条、round 与 at 同窗口、anchors 哈希按第 4 列重算），①–⑥ 全过而从未回跑。根因：`at`、`DISC_ESTABLISH`、`DISC_ROUNDS` 皆同一行为者自写，无外部可信时钟（git 未跟踪、无独立日志）。这是**无法靠本方案关闭**的主误判。
2. **注册表回填**：把立条落盘时刻前移、或把轮次窗口放宽到全天，任意 `at` 过 ③④。
3. **事后补冒充自写**：产物在立条当轮已含全部 grep 目标串（纪律 5/8/10/11 等确为当轮自带），事后仅追加自述行、把 `at` 写成回跑时刻；校验器只读行+命中，不核内容写入时刻 → PASS。
4. **同日粒度**：立条与回跑同为 2026-11-22 且 `DISC_ESTABLISH` 只记日期（现状），任意当日 `at` 过 ③。
5. **误用 mtime**：实测 mtime 被批量重置为同日；若把 mtime 当 `at` 来源，拷贝/恢复时间会被当回跑时间。
6. **只证声称、不证判据**：自述行证明「某时刻声称跑过」，不证明「真按该纪律判据 ran」；`anchors` 哈希可被同一自写者重算，故 ⑤ 也不是独立证据。

任何使用方必须同时看到上述六条与 C11 的 `unverifiable` 计数，否则不得把 PASS 读作「回跑已证」。

## OVERALL

收窄到「结构化自述一致性 + 显式不可验证」，收不到「回跑事实已证」——缺的是外部可信时钟与独立执行日志（均未取得），不是字段设计。

## 未取得清单（供 Lead 决策）

- 各纪律立条的逐条 ISO8601 落盘时刻（§2.14–§2.37 仅记 2026-11-22）。
- 轮次 `Rxx` 的 start/end 时间窗口表。
- 跨轮、独立的纪律回跑执行日志。
- 类 B 纪律 5/6/7/8/10 的可重跑生成器（目录内未见）。
- 纪律 20 所称「禁不可见字符断言」在产物中的实际存在（先验 DISCUP 已判 未取得）。
