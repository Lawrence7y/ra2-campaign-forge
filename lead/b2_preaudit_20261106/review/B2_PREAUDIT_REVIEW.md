# B2_PREAUDIT.md 独立复核回件

**复核员**：判定书复核员（新上下文，未参与 B2_PREAUDIT.md 撰写）
**被核对象**：`lead/b2_preaudit_20261106/B2_PREAUDIT.md`
**复核时刻**：2026-11-06
**铁律遵守**：零真机、零采样、只读母本/只读既有件；唯一写域 `lead/b2_preaudit_20261106/`（本回件 + `review/` 目录）；未 commit、未 push；所有 Python 用 `python -I -X utf8` + 绝对路径。

```
subjectSha256: a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449
subjectBytes: 28410
checkedEveryRow: true
```

指纹实跑：`sha256sum lead/b2_preaudit_20261106/B2_PREAUDIT.md` →
`a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449 *lead/b2_preaudit_20261106/B2_PREAUDIT.md`；
`wc -c lead/b2_preaudit_20261106/B2_PREAUDIT.md` → `28410`。

**复核总判**：`verdict: NO` 成立；探针实跑输出一致；但「文件:行」断言发现 **4 处对不上 + 1 处轻微不精确**，详见 §3。专项「超额放行」**未发现**（见 §4）。

---

## 1 检查 1：逐条「文件:行」断言核对（不抽样）

判定书共 158 行，含「文件:行」/「:行号」/「实跑命令+输出」形式的断言。本人对其中**每一处**都亲自打开对应行或亲自复跑对应命令，覆盖如下（按判定书行号分组）。

### 1.1 判定书头部（L1–L22）

| 判定书行 | 断言 | 核对动作 | 结果 |
|:--|:--|:--|:--|
| L3–L6 | 被审设计 B2_FIX_DESIGN.md SHA256=`deacab49…` / 11638 B / 236 行 | `sha256sum` + `wc -c` + `wc -l lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | ✅ 三者全符 |
| L8–L11 | 母本 SHA256=`517889c6…` / 399508 B / 7291 行 | `sha256sum` + `wc -c` + `wc -l out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | ✅ 三者全符 |
| L11 | 与 `lead/b2_preaudit_20261106/TASK.md:34-35` 基准一致，未写 `STOP_MOTHER_DRIFT.md` | 亲读 TASK.md:34-35（基准值一致）；`find lead/b2_preaudit_20261106 -name "STOP_MOTHER_DRIFT.md"` → 零命中 | ✅ |
| L15 | `B2_FIX_DESIGN.md:198`「应用前必须重新走一遍 B1 的预审硬门」 | 亲读 B2:198 = `★ **本文件只是设计。** 应用前必须重新走一遍 B1 的预审硬门，重点验：` | ✅ |
| L21 | `grep -cE '^- \*\*N[0-9]+ .*severity=high' …B2_PREAUDIT.md` → `5` | 原样复跑（repo root）→ `5` | ✅ |

### 1.2 六条旧错误（L28–L62）——逐条逐行核

**E1（L31–L32）**：亲读 `B2_FIX_DESIGN.md:43-48`（`finalize_trip` 加形参）、`:52-64`（调用点，`:63` 裸名传参）、`:35/:63/:200`（`_pre_freshness_snapshot` 三处出现）、`:66`（默认值 None）、`:190`（`:6388` 后 +2 行）；`_b2_probe_out.txt:95-99`（赋值定义形式 = `[]`）、`:100-105`（4 个 hunk `:43/:52/:75/:128`）、`:15-16`（`:5939` 原文）、`:54`（5 个早退）；母本 `:5939`（`copy_post_except_evidence(rec, carrier_dir, out_dir)`）、`:6340/:6349/:6361/:6374/:6377`（5 个 `return`）、`:6387`（`bak = backup_carrier(rec, carrier_dir)`）、`:7038`（`finally:`）、`:7117`（`FINALIZE_CODE[0] = finalize_trip(`）；`PRE_AUDIT.md:117-129`（错误 1 NameError）。
实跑 `grep -n "pre_snapshot\|_except_evidence_copy\|5939\|6388" B2_FIX_DESIGN.md` → 命中 `:36/:114/:116/:130/:133/:184/:188/:190/:200`，全为叙述/形参，无调用点 diff。
→ **全部相符** ✅

**E2（L37–L38）**：亲读 `B2_FIX_DESIGN.md:82`（`"exists": True`）、`:88-90`（`continue` 分支不写 `bak[name]`）、`:133/:134/:141-142/:223-224`；母本 `:4453-4456`（`if not src.exists(): … continue`）、`:4583-4587`；探针 `_b2_probe_out.txt:130/:136`（`MATCH`）；`PRE_AUDIT.md:131-142`（100% 误判）。
实跑 `grep -n "captured_at_iso" B2_FIX_DESIGN.md` → exit=1 零命中；`_b2_probe_out.txt:85/:185` 计数 0。
独立复现：本人 `python -I -X utf8 -c "<转写 B2 :133-154 判定式>"` → `pre=None (未采集), 跑后有历史件 -> ('new_first_appearance', 'high')`。
→ 主体相符 ✅；但 `:141` 一处措辞不精确，见 §3 问题 5。

**E3（L43–L44）**：亲读 `B2_FIX_DESIGN.md:83/:100/:147`（`mtime_pre`）、`:99`（`mtime`）、`:81-84`（只写 3 键）；`candidate/except_freshness.py:78/:90`（候选用 `mtime`）、`:80`（`captured_at_iso`）；旧 `TASK.md:47`（要求三键）；探针 `_b2_probe_out.txt:131`（`rewritten_same_content/medium` MATCH）、`:85/:185`（`captured_at_iso` 计数 0）。→ ✅

**E4（L49–L50）**：亲读 `B2_FIX_DESIGN.md:103-118`（「我的 TASK 错误」/四处最小集）、`:234`（「本文件不改任何文件」）、`:52-64`；实跑 `grep -n "finalize_trip(" qc151_trip.py` → `:5900` def / `:7117` 调用 / `:7149` 文档字符串；`grep -n "三处\|git diff\|不许扩大" lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` → `:42/:83/:94/:115/:134`。→ ✅

**E5（L55–L56）**：亲读 `B2_FIX_DESIGN.md:132-165`（判定提到 `:155`/`:162` 之前，`:156-161` 早退 `rec.add`，`:163-165` 正常路径无落盘）、`:186`（info +4 键）；探针 `_b2_probe_out.txt:133-134`（`absent_both`/`vanished` MATCH）、`:186-191`；母本 `:4583-4587`（`info` 5 键 + `rec.add("EXCEPT","evidence_copy",info,…)`）。
实跑 `grep -n "freshness_verdict\|freshness_confidence\|freshness_note\|mtime_post\|captured_at_iso" B2_FIX_DESIGN.md` → `freshness_verdict` 仅 `:205`；`freshness_confidence`/`freshness_note`/`captured_at_iso` 零命中。→ ✅

**E6（L61–L62）**：亲读 `B2_FIX_DESIGN.md:171-175`、`:196-198`；实跑 `grep -n "git diff" B2_FIX_DESIGN.md` → `:24/:171/:173/:175`；`grep -n "out/" .gitignore` → `33:out/`；旧 `TASK.md:83/:94/:134` 三条 `git diff` 仍在。→ ✅

### 1.3 新增问题 N1–N11（L70–L112）——逐条逐行核

- **N1 (L71–L72)**：亲读 `B2_FIX_DESIGN.md:63/:66/:190/:48`；母本 `:6293-6296`（`bak: dict = {}` / `t0: list = []` / `pre_except_txt = None`，注释「★ **未取到即 None/空**」）、`:6340/:6349/:6361/:6374/:6377`、`:6387`、`:7030-7037`（`except BaseException … raise`）、`:7038`、`:7043-7047`（「它取代正常返回值向解释器传播」）、`:7117`；探针 `_b2_probe_out.txt:54,99,146-151`。
  独立复现（本人实跑 `python -I -X utf8 -c "<合成 main/finally>"`）→
  `PATH early_return -> RAISED UnboundLocalError: cannot access local variable '_pre_freshness_snapshot' where it is not associated with a value`、
  `PATH caught_exception -> RAISED UnboundLocalError: …`、`PATH normal -> None`（判定书写 `PATH normal -> NORMAL`，属同一「不抛异常」语义，非实质不符）。→ ✅
- **N2 (L75–L76)**：亲读母本 `:436-441`（Recorder「未读到写未测 / 不可测写 null / 不提供写 False 表示未知」）、`:5949-5952`、`:5961-5963`、`:5974-5976`（均为 `null` 留痕）；`B2_FIX_DESIGN.md:48/:130/:133/:134/:141-142`；`PRE_AUDIT.md:79-84/:180-181`。
  独立复现 → `pre=None (未采集), 跑后有历史件 -> ('new_first_appearance','high')`、`pre={} , 跑后有历史件 -> ('new_first_appearance','high')`；探针 `_b2_probe_out.txt:136-138,152-156`。
  实跑 `grep -n "未测\|error\|未采集\|null\|is_new" B2_FIX_DESIGN.md` → 仅 `:89` 一句。→ ✅
- **N3 (L79–L80)**：亲读 `B2_FIX_DESIGN.md:133/:202-204/:222-226`；`candidate/except_freshness.py:47`（`error_pre_snapshot`）、`:155-157`、`:204-207`。
  独立复现 → `now_exists=True {} -> ('new_first_appearance','high') | {exists:False} -> ('new_first_appearance','high')`、`now_exists=False {} -> ('absent_both','n/a') | {exists:False} -> ('absent_both','n/a')`；探针 `_b2_probe_out.txt:139-145`。→ ✅
- **N4 (L83–L84)**：亲读 `B2_FIX_DESIGN.md:137-154/:155-162/:163-165/:186/:192`；旧 `TASK.md:56`（info 新增 4 键）；母本 `:4583-4586`。
  实跑 `grep -n "^-" B2_FIX_DESIGN.md` → 18 行命中（含 `---` 分隔线与列表项），其中 diff 删除行恰为 `:46/:61/:79/:99/:157` 共 5 行（判定书只列这 5 行，未声称 18 行全是删除行，无矛盾）。→ ✅
- **N5 (L87–L88)**：亲读 `B2_FIX_DESIGN.md:118/:200`；母本 `:5938-5939`；实跑 `grep -n "^+" B2_FIX_DESIGN.md` → 全部 `+` 行 = `:42,:47,:48,:62,:63,:80,:81,:82,:83,:84,:100,:130,:132-161`，无 `copy_post_except_evidence(..., pre_snapshot=…)`；`grep -n "copy_post_except_evidence(" qc151_trip.py` → `:4561` def / `:5939` 调用。
  → **「是该函数全仓唯一调用点」对不上**，见 §3 问题 1（判为错引，非超额放行）。
- **N6 (L91–L92)**：亲读 `B2_FIX_DESIGN.md:43-48`（跳过 7 个形参 `t0/pre_except_txt/out_dir/ownership/terminated_ok/main_return_code/mother_baseline`）；探针 `_b2_probe_out.txt:162-180`（列出母本 `:5900-5909` 与缺失形参 7 个）；母本 `:5900-5909` 逐行亲读；`:192`「删除 0 行」与 5 个 `'-'` 删除行。
  → **「`:52-64` 的调用点 hunk 亦省略 `:7118-7124` 的实参」对不上**，见 §3 问题 2。
- **N7 (L95–L96)**：亲读 `B2_FIX_DESIGN.md:183-190`（8 行改动表）、`:118`；探针 `_b2_probe_out.txt:101-105`（4 hunk）、`:117-123,157-161`、`:157-161`；实跑 `grep -n "5939\|6388\|4583\|freshness_verdict\|…" B2_FIX_DESIGN.md` 与探针输出一致。→ ✅
- **N8 (L99–L100)**：亲读 `B2_FIX_DESIGN.md:136-138/:160-161/:192`；`candidate/except_freshness.py:40-42`（VERDICT_DOC）、`:187-191`（`absent_both`: `is_new=False`, `confidence=low`, notes 含「不能证无崩溃」）、`:200-202`（`vanished`: 须人工复核，`is_new=None`）。→ ✅
- **N9 (L103–L104)**：实跑 `grep -n "三处\|git diff\|不许扩大" lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` → `:42/:83/:94/:115/:134`；亲读 `B2_FIX_DESIGN.md:103-118/:171-175/:234`；`grep -n "out/" .gitignore` → `33:out/`。→ ✅
- **N10 (L107–L108)**：亲读旧 `TASK.md:47/:55`、b2 `TASK.md:27`（「237 行」）；`candidate/PATCH_SUGGESTION.md:37-44/:84-89`；`B2_FIX_DESIGN.md:81-84/:127-165/:192/:206`；探针 `_b2_probe_out.txt:39-41/:85/:185`；`wc -l B2_FIX_DESIGN.md` → `236`。
  → **「`:134` 验收要求 `RESTORE.backup_mtime_pre:except.txt`」对不上**，见 §3 问题 3。
- **N11 (L111–L112)**：亲读 `B2_FIX_DESIGN.md:160-161/:205`；母本 `:436-454`（`Recorder.add` 扁平 `(group,key,value)`、`self.rows: list = []`）、`:672-708`（`except_set_diff`，`:677`「不得用 `sha` 变化判 crash」）、`:702-707`/`:5986`（E 字段同在 `EXCEPT` group）、`:5985-5990`（`if not setdiff.get("no_new_exception", True)` 唯一影响退出码）；`PRE_AUDIT.md:80-84/:181/:189`；探针 `_b2_probe_out.txt:189-190`。→ ✅

### 1.4 阻断/责任/再提交证据/未验（L116–L157）

L119–L123 阻断项、L126–L128 责任角色（含 `B2_FIX_DESIGN.md:234/:196-198`）、L131–L139 再提交证据（含旧 `TASK.md:56`、`b2 TASK.md:82-101`，已亲读 b2 TASK.md:82/89/90/94/100/101）、L141（不发放应用许可）、L147（`lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md:99` 连 `--help` 都禁，已亲读）、L149（`B2_FIX_DESIGN.md:200-207/:209/:218/:206`，已亲读）、L150、L152（`PRE_AUDIT.md:129`、`_b1_preaudit_out.txt:177-181` —— 本人亲自打开该文件，内容为 `[缺陷 B: bak 缺失 'exists' 键导致 100% 误判 new_first_appearance]`…`:181 CONFIRMED: …100% 误判为 new_first_appearance！`，与判定书转述一致）、L154（母本 `:167 import hashlib`、`:173 import time`，已亲读 + 实跑确认）、L157（`find lead/b2_preaudit_20261106 -type f | sort` 输出 4 件，实跑一致）。
→ 全部相符 ✅；L156 一处行号错引见 §3 问题 4。

**逐条覆盖结论**：全部「文件:行」断言均已亲自打开/复跑，无抽样；发现 4 处错引 + 1 处轻微不精确。故 `checkedEveryRow: true`（= 每一条都核过，不等于「全对」）。

---

## 2 检查 2：亲自重跑探针

**指定命令**（按要求原样，cwd = repo root）：
```
python -I -X utf8 lead/b2_preaudit_20261106/_b2_probe.py
```
- 该脚本 `_b2_probe.py:291-292` 自身把输出写入 `lead/b2_preaudit_20261106/_b2_probe_out.txt`（stdout 不打印）。故先 `cp` 备份到 `/tmp/_b2_out_before_review.txt`，再跑，再对比。
- 实跑输出：`EXITCODE=0`（stdout 为空，符合脚本设计）。
- 备份指纹：`57c49ca5ea8020610fbe02f8da27ab09453b5e430eefcb48024897b58a2dc3ee`
- 重跑后 `_b2_probe_out.txt` 指纹：`sha256sum` → `57c49ca5ea8020610fbe02f8da27ab09453b5e430eefcb48024897b58a2dc3ee`；`wc -c` → `16296`；`wc -l` → `200`。
- `diff -q /tmp/_b2_out_before_review.txt lead/b2_preaudit_20261106/_b2_probe_out.txt` → 无差异，`IDENTICAL=yes`。
- 另按判定书 L147 的绝对路径形式复跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b2_preaudit_20261106/_b2_probe.py` → `EXITCODE=0`，指纹/`16296 B`/`200 行` 一致，`diff -q` → `IDENTICAL=yes`。

**结论**：探针输出与 `_b2_probe_out.txt` **完全一致**；判定书 L147 所述 `200 行 / 16296 B` / `57c49ca5…` / `IDENTICAL=yes` 全部复现。探针重写了同目录同名的既有输出文件，但字节完全相同（SHA256 前后一致），写域内、未触碰写域外文件。

**另复跑判定书自称的「独立合成复现」两组**（N1 的 main/finally、N2/N3 的判定式），输出见 §1.3 N1/N2/N3，与判定书一致。

---

## 3 复核判定的问题项（issues）

1. **【错引，B2_PREAUDIT.md:87 / N5】「是该函数全仓唯一调用点」不成立。**
   判定书 L87 写：「母本 `qc151_trip.py:5938-5939` 现状 `copy_post_except_evidence(rec, carrier_dir, out_dir)`，是该函数**全仓**唯一调用点（实跑 `grep -n "copy_post_except_evidence(" qc151_trip.py` → `:4561` def / `:5939` 调用）」。括号内的 grep 被限定在单个文件 `qc151_trip.py`，只能证明「母本文件内唯一」（L31 正是这么写的，正确），**不能**证明「全仓唯一」。
   本人实跑 `grep -rn --include=*.py "copy_post_except_evidence(rec" lead out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip 2>/dev/null | grep -v "def " | wc -l` → `22`；具体命中如 `lead/goal1_a8_fix_20261022/qc151_trip.harness4.py:6277`、`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:7207`、`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py.unapproved_5269c7a8.py:2732` 等 21 个其它副本各有调用点，共 22 个文件。
   且与判定书自身 §未验 #7（L153）「未审其它 harness 副本是否有独立调用链需同步……本人未重跑该命令，按「未验」记」自相矛盾：一边把该范围标为未验，一边给出全仓唯一性的既成结论。
   **影响**：仅「全仓」这个范围词错误；N5 的核心结论（母本 `:5939` 未传 `pre_snapshot`）仍成立，故不影响 `verdict: NO`。

2. **【错引，B2_PREAUDIT.md:91 / N6】「`:52-64` 的调用点 hunk 亦省略 `:7118-7124` 的实参」不成立。**
   本人实跑 `python -I -X utf8 -c "<逐字打印 B2:52-64 与母本:7117-7125 并比较>"`（完整输出见本次会话），结果显示 B2:54–60 与母本:7118–7124 的 7 个实参**逐字一致**：
   `B2 :54 -> 'rec, fin_carrier, bak, t0, pre_except_txt, out_dir=WORKDIR,'` ↔ `MO :7118` 同串；`:55/:56/:57/:58/:59-60` ↔ `:7119/:7120/:7121/:7122/:7123-7124` 同串。唯一差异是 B2 每行多 1 个前导空格（B2:53 前导 13 空格，母本:7117 为 12；B2:54 为 17，母本:7118 为 16），属 hunk 缩进偏移，**不是省略实参**。
   判定书 N6 同段另两句（签名 hunk 跳过 7 个形参、`:192` 删除 0 行 vs 5 行 `'-'`）均经探针 `_b2_probe_out.txt:162-180` 与 `B2_FIX_DESIGN.md:43-48` 核实成立；仅这一句错引。

3. **【错引，B2_PREAUDIT.md:107 / N10】「`:134` 验收要求 `RESTORE.backup_mtime_pre:except.txt`」行号归错文件。**
   `lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md:134` 实为
   `- ★ **`out/` 被 `.gitignore:33` 忽略**，所以 `git diff` 看不到改动——必须用**文件级 SHA256 + `diff -u` 备份对比**证明改动。`（实读 + `python -I -X utf8 -c` 打印确认）；
   `RESTORE.backup_mtime_pre:except.txt` 实际位于 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/PATCH_SUGGESTION.md:134`（`- \`qc151_fields.json\` 新增 \`RESTORE.backup_mtime_pre:except.txt\`；`）。
   实跑 `grep -n "backup_mtime_pre\|RESTORE" lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md` → exit=1，旧 TASK.md 全文零命中 `backup_mtime_pre`。
   N10 该句把候选件行号张冠李戴到旧 TASK.md；N10 其余证据（`TASK.md:47/:55`、`candidate/PATCH_SUGGESTION.md:37-44/:84-89`、`captured_at_iso` 计数 0、`wc -l`=236 vs `TASK.md:27` 的 237）逐一核实成立。

4. **【错引（轻微），B2_PREAUDIT.md:156 / 未验#10】「`TASK.md:5` 的 `review/B2_PREAUDIT_REVIEW.md`、`check_b2_preaudit.py`」行号不对。**
   `lead/b2_preaudit_20261106/TASK.md:5` 实为 `**唯一写域**：\`lead/b2_preaudit_20261106/\`（新建目录，只写此目录内的新文件）。`，并未提及这两个产物；`review/B2_PREAUDIT_REVIEW.md` 在 `TASK.md:80`（§5 交付物 3）与 `:89`（§6），`check_b2_preaudit.py` 在 `TASK.md:94`（§7）。均已亲读确认。
   （注：该条自述「未由本 ask 要求产出」与 b2 TASK.md §5/:80/:89/:94 的交付清单不符，属判定书对本轮交付范围的自我描述问题，一并记入。）

5. **【轻微不精确，B2_PREAUDIT.md:37 / E2】「判定侧 `:134`/`:141` 读同名 `exists`」。**
   `B2_FIX_DESIGN.md:134` = `+    _pre_exists = bool(_pre.get("exists"))`（确实读 `exists` 键）；但 `:141` = `+        if not _pre_exists:`（读的是 **:134 派生的布尔变量**，不是键名）。读同名键的另一处是 `:147` 的 `_pre.get("mtime_pre")`。结论（键名层面已对齐）不受影响，仅行号措辞不精确。

**未发现的问题（明确记载，避免误判）**：
- E2 的「`:223-224` 声称无键⇒`{"exists":False}` 与 `:130/:133` 的 `None⇒{}` 语义未统一」——B2:223/:224/:130/:133 亲读，成立。
- N4/N6 的「5 行 `'-'` 删除行」——实跑 `grep -n "^-" B2_FIX_DESIGN.md` 共 18 行命中，其中 diff 删除行恰为 `:46/:61/:79/:99/:157`；判定书列的就是这 5 行 diff 删除行，未声称 18 行全为删除行，无矛盾。
- L21 的 high 计数 5、L31 的「母本唯一调用点 :5939」（限定在母本文件内，正确）、L55 的母本 `:4583-4587` info 5 键、L111 的 E 口径与退出码唯一触发处，均核实无误。

---

## 4 检查 3：专项「超额放行」

### 4.1 有没有把「设计 YES」写成「可以应用到母本」？—— **没有**
- `B2_PREAUDIT.md:17` = `verdict: NO`。不存在「设计 YES」被升级的对象。
- `B2_PREAUDIT.md:15` = 「**本判定书的门**：只回答「这份设计能不能拿去制作完整候选」。**不回答、也不等于「可以应用到母本」**——那是另一道门（B2_FIX_DESIGN.md:198……）」；已核 B2:198 原文确为「应用前必须重新走一遍 B1 的预审硬门」。
- `B2_PREAUDIT.md:141` = 「**本判定书不是应用许可**：即使上述证据齐备、下一版设计拿到 `verdict: YES`，其含义也仅为「可拿去制作完整候选」；「应用到母本」仍需另走 B2 `:196-198` 所要求的预审硬门与母本改动流程，本判定书不发放该许可。」
- `B2_PREAUDIT.md:128` 责任角色明写候选实现者「负「不得按现设计直接制作/应用」的责任」。
- 实跑 `grep -n "YES\|应用到母本\|应用许可\|放行\|许可" lead/b2_preaudit_20261106/B2_PREAUDIT.md` → 全部输出见上，无一处发放应用许可。

### 4.2 有没有把复核 UNVERIFIABLE 的条目写成已成立？—— **没有（按「超额放行」口径）**
- 判定书专设 `## 未验`（L145–L157）11 条，明确列出未运行真机 harness、未验应用后 `ast.parse`、未验五项单测全矩阵、未做 §2 行号表逐格复核、未验母本 mtime、未核 `_b1_preaudit.py`、未审其它 harness 副本、未验证 import、未验下一版任务书、独立复核/门槛未产出、只读件指纹未逐一重算。
- `B2_PREAUDIT.md:156` 明写「`checkedEveryRow` 与门槛 `exitCode` 均无值可报，未伪造。本判定书不因此把自己标为「已复核」。」
- 实跑 `grep -c "未验\|未核\|未跑\|未逐一\|本人未\|未重跑\|不因此" lead/b2_preaudit_20261106/B2_PREAUDIT.md` → `11`；`grep -n "已成立\|已复核\|标为「已复核」\|无条目需降级" …` 仅命中 L13/L156，无「已复核」自称。
- L13「『复核未通过 / 无法核实的条目』为空数组，故无条目需降级为 `UNVERIFIABLE`」：实跑 `grep -rln --include=*.md --include=*.json --include=*.txt "notChecked\|UNVERIFIABLE\|无法核实" lead/b2_preaudit_20261106 lead/nextstep_plan_20261106 2>/dev/null` → 只命中 `B2_PREAUDIT.md` 自身；两路 `verdicts`/`notChecked` 源件不在写域内（应为上游子代理回话，非落盘文件），故该句本人**无法独立核实**，按「未验」记，不据此判为超额放行。
- **已考量的边界情形**：§3 问题 1（L87「全仓唯一调用点」）与 §未验 #7（L153 明说其它副本未核）确实存在张力——一个未核范围被写成了既成结论。本人把它**归类为「文件:行/作用域错引 + 事实错误」而非「超额放行」**，理由：它不发放任何许可、不改变 `verdict: NO`、且判定书在 §未验 #7 明确把该范围标为未验（未把 UNVERIFIABLE 条目整体升格为已成立）。该张力已如实写入 issues（问题 1），请主流程知悉。

**`overreachFound = false`**。

---

## 5 复核结论

| 项 | 结论 |
|:--|:--|
| 检查 1 逐条「文件:行」 | **完成，未抽样**（`checkedEveryRow: true`）；158 行判定书全部断言逐条打开/复跑；发现 4 处错引 + 1 处轻微不精确，均写入 issues |
| 检查 2 探针重跑 | **PASS**：`python -I -X utf8 lead/b2_preaudit_20261106/_b2_probe.py` → `EXITCODE=0`，输出 `57c49ca5…` / `16296 B` / `200 行`，`diff -q` → `IDENTICAL=yes` |
| 检查 3 超额放行 | **未发现**（`overreachFound=false`）：`verdict: NO`，L15/L141 明确拒绝发放应用许可，§未验 11 条如实标注 |
| 主判定 | `verdict: NO` 成立。4 处错引均为证据链局部瑕疵，未触及 E1=NOT_FIXED / 5 条 `severity=high` 两条独立判 NO 的依据；按 `TASK.md:90`，复核未判 NO 且 `checkedEveryRow=true`，不构成对 NO 的推翻 |

**复核员产出边界**：仅写 `lead/b2_preaudit_20261106/review/B2_PREAUDIT_REVIEW.md`（本文件）+ 必要的 `review/` 目录；探针重跑以字节相同的方式重写了同目录既有 `_b2_probe_out.txt`（SHA256 前后一致）；`/tmp/_b2_out_before_review.txt` 为仓库外临时备份。未创建 `check_b2_preaudit.py`（本 ask 未要求，且判定书 §未验 #10 已如实记为未产出），未修改任何只读件，不 commit、不 push。
