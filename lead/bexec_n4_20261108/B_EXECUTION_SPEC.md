# B_EXECUTION_SPEC · N-4 正式应用任务书（草案 · 未生效 · 非放行）

- 件名：`lead/bexec_n4_20261108/B_EXECUTION_SPEC.md`
- 日期：2026-11-08　撰写：任务书撰写员·GLM（动态工作流子代理，新上下文）
- 输入：①规格草案 `lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md`（本轮实算 `cb4f3011…` / 22,136 B）；②独立复核回件（34 条命令，**verdict = partial**）；③本轮撰写员对关键论断的独立再证实（§5.2，不复述不采信）。
- 性质：本文件占 N-4:47 要求的「来源会话任务签发人在本目录 B_EXECUTION_SPEC.md 固定正式目标、候选 SHA256、A—D 允许范围、替代旧 TASK 三处限制的条款、合成测试命令与 API 基线」槽位，当前状态 = **规格草案（SPEC_DRAFT），未生效**。N-4:49「身份、任一规则或版本缺失则任务书不生效」；矩阵甲/乙绑定与 T1 修正均待签发人显式确认（§3.6、§3.7、§5.4）。
- 铁律：零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码；母本与既有件一律只读；唯一写域 = `lead/bexec_n4_20261108/`；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 Python `hashlib`（本机无 sha256sum / wc）。
- 本轮边界：只固定规格与静态审查；**不运行完整 harness、不改母本、不实施集成**；不签 `APPROVE_SCOPE`。

---

## 1 目的与授权边界（★ 规格草案，非放行）

### 1.1 正式目标
- NEXT_STEPS_20261106.md:46（本轮实读）：「②崩溃 / ③安全改动」。
- 对象：正式母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` 与唯一正式候选 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（指纹见 §2.1）。

### 1.2 授权链（本轮实读）
- `lead/re_line_20261105/D24_RULING/RULING_D24.md:52` 第 5 条：B 执行任务「应用前重核正式母本是否仍为 V2 的完整 SHA256，变化则停止套用旧版本候选；……做隔离合成测试与独立静态复核……禁止完整 harness 发射，只签离线集成状态」。
- `RULING_D24.md:61`（B/G4）：有权来源会话可直接安排执行，无须重复索取一般授权；执行代理须有任务书明确的正式 harness 写域。
- `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:45-51`（N-4 节全文实读：矩阵原文 :47、签署与 API 门禁规则 :49）、`:53-58`（N-5 节：:55 离线集成动作、:57 验收与 STOP）。
- `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md:13` `verdict: YES`；`:16` 效力边界「可以拿去编写候选；不等于可以应用到母本」。
- D-25 裁决约束：`lead/b2b_design_20261106/B2B_DESIGN.md:43`（本轮实读）转引 `RULING_D25.md:21,34-37`「立即可安排范围止于新指定写域内的 B2b 设计和独立设计预审」——**RULING_D25 原文本轮未实读**（§5.5 未验 5）。

### 1.3 放行边界（本草案不代签任何东西）
- **不签 `APPROVE_SCOPE`**：签署属来源会话任务签发人（N-4:49「独立审阅者签候选 YES、来源会话签发人签 APPROVE_SCOPE」）。
- **不代签候选 YES**：R3:21 `verdict: PASS` 属独立审阅者（`lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md:21`，本轮实读）；R3:23 明写「**PASS ≠ 可应用到母本**」——该 PASS 不因本轮升级为「可应用」。
- 不签真机验收 / 崩溃修复完成：RULING_D24:52 只签离线集成状态；NEXT_STEPS:57「不签真机验收或崩溃修复完成」。
- 母本本轮前后未被改动：§2.1 指纹为本轮收尾实算，仍与 R3:13 绑定值一致。

---

## 2 上游设计明文与 A—D 范围（替代旧 TASK「三处」限制条款）

### 2.1 对象与指纹（本轮实算：`python -I -X utf8 -c` + hashlib，18 件一次性打印）

| 对象 | 路径 | SHA256（64 hex） | 字节数 |
|---|---|---|---|
| 母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 |
| 正式候选 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412759 |
| B2 设计（甲，被否） | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11638 |
| N-4 原文 | `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27225 |
| D-24 裁决 | `lead/re_line_20261105/D24_RULING/RULING_D24.md` | `56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5` | 15301 |
| 规格草案（被核对象） | `lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md` | `cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306` | 22136 |
| 旧候选（已替换，禁绑） | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` | 420292 |
| 旧测试套件（T1 错版，见 §3.7） | `lead/b2b_candidate_20261106/tests/test_candidate.py` | `33b0c5105c4f287056590340fd7bd801c0766dfff9da451e406e32ad77d95790` | 34105 |
| R3 改绑测试副本（T1 修正对象） | `lead/b2b_candidate_review3_20261107/_test_candidate_lf.py` | `1a1335d6d4dd472e4def5e739d54f6e229f83d0b5d8a178cb5b641c491fe8d11` | 34111 |

五上游件与任务书【上游指纹】清单逐一相符；母本/候选与 R3:13-14 绑定记录一致（本轮实读）。

**被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508**（母本，收尾复核未变）；
**被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759**（正式候选）；
**被核对象 SHA256 = cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306，字节数 = 22136**（规格草案，即独立复核回件的主要被核对象，本轮实算与复核 sha256Line 一致）。

### 2.2 B2 设计明文（矩阵甲来源；已被否）
本轮实读 `B2_FIX_DESIGN.md:108-207`：
- A—D 四处（:113-116 表）：A `backup_carrier`（:4457-4461）补 `exists`/`mtime_pre`/`captured_at_epoch`；B `copy_post_except_evidence`（:4561-4562 签名 + :4573 前插判定 + :4583-4586 info）；C `finalize_trip` 签名（:5900-5909）加 `pre_freshness_snapshot=None`；D `_except_evidence_copy`（:5939）+ `finalize_trip` 调用点（:7117-7125）+ main 基线（:6387 后）接线。:118「**四处改动是可论证的最小集**」。
- 修正动因（:122-123）：判定写在早退之后 ⇒「`absent_both` 与 `vanished` 两个分支永远输出不了」。
- :198「**本文件只是设计。** 应用前必须重新走一遍 B1 的预审硬门」；合成字典单测输入与早退期望 :202-204。
- **B2 已被否**：B2B_PREAUDIT.md:8-9（本轮实读）把 B2B_DESIGN.md 标「独立预审目标版本」、把 B2_FIX_DESIGN.md 标「**历史被否参照件**」。

### 2.3 B2b 现行批准设计（矩阵乙来源；R3 PASS 对照设计）
- `B2B_DESIGN.md` §7 :662-670（本轮实读）：H01–H09 九 hunk 表，母本锚点 = :214 / :4460 / :4561 / :4574-4599 / :5909 / :5939 / :6296 / :6388 / :7125 后；:635 实算 9 个 hunk 的 `-` 侧覆盖区间均不含 E 判据块 5984-5990。
- `lead/b2b_design_20261106/STATE_MATRIX.json` :2-15（本轮全文实读）：14 数据行。
- R3:5 对照设计 = B2B_DESIGN.md + STATE_MATRIX.json；R3:31-34 决定性①②「候选 = 母本 + 设计 §4 九 hunk，一字节不多、一字节不少」；R3:42 14 组 fixture 四元组 14/14 match；R3:43 13 处 `_finish` 出口与矩阵行映射齐全（本轮实读）。

### 2.4 允许范围条款（替代旧 TASK「三处」限制）
- 若签发人**绑乙**：允许范围 = H01–H09 九 hunk（与候选逐字节对应，R3:31-34），删除 0 行。
- 若签发人**绑甲**：允许范围 = A—D 四处；但现行候选按乙实现，绑甲则在 §3.4 的 4 处差异必 FAIL，须退 N-2 重制候选（N-4:47「若与设计冲突退 N-2，不由测试者临时决定」）。
- 门禁总则（N-4:49）：新增调用、导入、包装或动态解析均 FAIL；删除也须解释且只许批准范围内变动。

### 2.5 版本纪律
- 正式候选仅 `qc151_trip.candidate_lf.py`（`ca23c116…`/412759）。
- 旧候选 `lead/b2b_candidate_20261106/qc151_trip.candidate.py`（`9656e432…`/420292，本轮实算）已被 N-1 绑定替换（R3:150，本轮实读）——**禁止**作为 N-5 对象；N-5:57「版本不符立即 STOP」。

---

## 3 合成矩阵 7 分支 + 空快照 + 复制失败 + 4 类异常契约

### 3.1 判别口与值域（候选实码，本轮实读）
- `state` 唯一判别：候选 :4583-4586（docstring 硬约束）+ :4636-4639（归一实现）——`None` / `{}` / 缺 `state` / 脏值一律 `unknown`，「绝不等于跑前确认无件」；确认无件必须显式 `state="absent_confirmed"`（B2B_DESIGN.md:100-106 本轮实读）。
- 值域（候选 :221-228 实读）：`FRESHNESS_VERDICTS` 9 值 = unknown / absent_both / new_first_appearance / vanished / leftover_unchanged / new_write / rewritten_same_content / error_pre_snapshot / post_read_error；`FRESHNESS_CONFIDENCES` = high / medium / low / none（**无 n/a**）；`FRESHNESS_SNAPSHOT_STATES` = unknown / absent_confirmed / present / error；`usable_as_crash_evidence` 恒 False（:4628-4631 `_finish` 实读）。

### 3.2 矩阵甲 · N-4:47 原文口径（= B2_FIX_DESIGN.md:133-154 实码，本轮实读）

| # | 场景 | verdict | confidence | 实码行 |
|---|---|---|---|---|
| 1 | 跑前无 + 跑后无 | absent_both | n/a | :137-138 |
| 2 | 跑前有 + 跑后无 | vanished | high | :137-138 |
| 3 | 跑前无 + 跑后有 | new_first_appearance | high | :141-142 |
| 4 | 两者有且 SHA 不同 | new_write | high | :148-149 |
| 5 | SHA 同 mtime 增 | rewritten_same_content | medium | :150-152 |
| 6 | SHA 同 mtime 减 | rewritten_same_content | low | :150-152 |
| 7 | SHA 与 mtime 均同 | leftover_unchanged | high | :154 |

输入语义：`_pre = dict(pre_snapshot or {})`（:133）⇒ 空快照 `{}` ≡ 显式 `exists=False` ≡ None；早退分支带 `evidence_freshness` 记录且 note「不做 crash 归因（:677）」（:155-161）。

### 3.3 矩阵乙 · B2b 现行口径（= STATE_MATRIX.json:2-15 + 候选 :4616-4698 实码，逐行本轮实读）

| 矩阵行 | state（跑前） | 场景 | verdict | confidence | is_new | 候选实码 |
|---|---|---|---|---|---|---|
| :2 | unknown | pre=None/{}/缺state/脏值，跑后任意 | unknown | none | None | :4648-4651 |
| :3 | unknown | pre 显式 unknown + 跑后无件 | unknown | none | None | :4648-4651 |
| :4 | error | 跑前采集抛异常 | error_pre_snapshot | none | None | :4652-4654 |
| :5 | present | 跑后 read_bytes/stat/write_bytes 抛异常 | post_read_error | none | None | :4643-4646 |
| :6 | absent_confirmed | 跑前确认无件 + 跑后在场 | new_first_appearance | high | True | :4666-4669 |
| :7 | absent_confirmed | 跑前确认无件 + 跑后无件 | absent_both | **low** | False | :4657-4661 |
| :8 | present | sha 同 + mtime 双侧齐全未变 | leftover_unchanged | high | False | :4690-4692 |
| :9 | present | sha 同 + mtime 侧缺失 | leftover_unchanged | **medium** | False | :4685-4689 |
| :10 | present | sha 不同 | new_write | high | True | :4681-4683 |
| :11 | present | sha 同 + mtime 变大 | rewritten_same_content | medium | True | :4697-4698 |
| :12 | present | sha 同 + mtime 回拨 | rewritten_same_content | low | True | :4693-4696 |
| :13 | present | 跑前在但缺 pre.sha256 | error_pre_snapshot | none | None | :4672-4676 |
| :14 | present | 跑后缺 post.sha256 | post_read_error | none | None | :4677-4680 |
| :15 | present | 跑前在 + 跑后无件 | vanished | **none**（旗标，人工复核） | None | :4662-4664 |

R3 保留登记（R3:47，本轮实读，非候选缺陷）：:2 行 condition「跑后任意文件状态」措辞过宽——实测 pre=None + post.read_error → post_read_error（:4643-4646 错误优先于折叠）。

### 3.4 甲↔乙差异（4 处分支取值不同 + 值域/字段差）

| 分支 | 甲（N-4:47 / B2） | 乙（B2b / 候选 / R3 PASS 口径） |
|---|---|---|
| absent_both 置信 | n/a | **low** |
| vanished 置信 | high | **none**（不给 high、is_new=null、人工复核） |
| 空快照 `{}` | ≡ exists=False → absent_both / new_first_appearance | → **unknown / none**（未知 ≠ 不存在） |
| mtime_pre 缺失 | 未单独定义（:150 守卫跳过） | leftover_unchanged / **medium**（盲区如实标注） |
| confidence 值域 | 含 n/a | high/medium/low/none（无 n/a） |
| 字段 | verdict + confidence | verdict / confidence / is_new / note / usable_as_crash_evidence / pre_snapshot_state（乙超集） |

### 3.5 空快照、复制失败、4 类异常契约（逐项固定：输入 → 返回值 → 落盘 → 错误预期；均候选实码行，本轮实读）

1. **空快照 `{}`（含 None / 缺 state / 脏值）**：`classify_except_freshness({}, post)` → `{"verdict":"unknown","confidence":"none","is_new":None,"note":"…未知 ≠ 不存在…","usable_as_crash_evidence":False,"pre_snapshot_state":"unknown"}`（:4634-4651）；落盘走 `_emit_f` 7 键（:4730-4753）；**不作**「本趟新出现」归因；R3:44 穷举 36 组 unknown→high 泄漏 = 0（历史转引）。
2. **复制失败（须记 error 且不签复制成功）**：copy 内 `except`（:4773-4790）→ 三条 `rec.add("ERROR", …)`：`freshness_copy_failed`（:4777-4779）/ `freshness_copy_stage`（:4780-4783）/ `freshness_copy_traceback`（:4784-4785）→ `post_observed["read_error"]` 置错（:4786）→ `_emit_f(classify(...), "copy_failed")`（:4787-4789）→ **`raise` 原异常**（:4790）。成功路径 info 与 `EXCEPT.evidence_copy` 记录仅 :4813-4814 可达 ⇒ 错误路径不签复制成功。早退（跑后无件）路径：`EXCEPT.evidence_copy=None` + `_emit_f(...,"src_missing")` + `return None`（:4756-4764）。
3. **mtime_pre 缺失**：state=present 且 sha 同但 mtime 侧缺失 → `leftover_unchanged` / `medium` / `is_new=False`，note「A 旁证不可用，同内容重写盲区此趟未覆盖（如实标注，不虚报 high）」（:4685-4689）；不作新崩溃归因（usable_as_crash_evidence 恒 False）。
4. **读写异常（跑前侧）**：`make_pre_freshness_snapshot` 采集抛异常 → `state="error"` + `error` + `traceback` 三字段（:4608-4612，内含函数内 `import traceback` :4609）→ classify 走 `error_pre_snapshot` / `none`（:4652-4654），独立出口、不降级、不静默、不给 high。
5. **初始化前收尾**：H07 预初始化 `_pre_freshness_snapshot: dict | None = None`（候选 :6528，本轮 grep 实位）；早于 :6623（H08 构造）抛出 ⇒ 快照为 None → classify 得 `unknown` / `none`；原异常保留、收尾失败进 `CLEANUP_FAILURES` 不写 verdict 局部量（B2B_DESIGN.md:184 P6 契约本轮实读；候选 :6154-6158 docstring 口径）。
6. **缺省调用路径**：`copy_post_except_evidence(pre_freshness_snapshot=None)`（:4701-4704 默认）与 `finalize_trip(pre_freshness_snapshot=None)`（:6137 默认）→ 非 dict 归一 `{}` → `unknown` / `none`（:4634-4638）。与 N-4:47「报告未验或错误、不作新崩溃归因」相符；与甲的 `{}→new_first_appearance(high)` 冲突登记于 §3.4。
7. **F/E 边界（:677 不侵犯）**：E 唯一口径恒为母本 `except_set_diff`（B2B_DESIGN.md:628-629 实读）；九 hunk 区间均不含 E 判据块 5984-5990（B2B_DESIGN.md:635）；候选 :4619-4621 N9 声明（docstring 实读）。

### 3.6 绑定决断点（签发人显式声明，本草案不代决）
两套矩阵不能同时绑定为通过判据。事实面：候选按乙实现并经 R3 以乙对照判 PASS（R3:5,42-44）；若绑甲，候选在 absent_both（low vs n/a）、vanished（none vs high）、空快照/None（unknown vs 折叠）各场景必 FAIL。**本草案建议（仅建议，非裁决）绑乙**，理由：乙是 N-2 复审链（B2B_PREAUDIT YES → D-25 → R3 PASS）的现行批准设计，且对 N-4:47 四类异常契约覆盖更严。签发人签署时必须显式声明绑定（N-4:47「不由测试者临时决定」）。

### 3.7 测试命令 T1–T5（签发人绑定后即为 N-5 通过判据；T1 已按复核缺陷修正）

| # | 命令（绝对路径） | 预期 | 状态（撰写员轮） |
|---|---|---|---|
| T1 | `python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_candidate_review3_20261107\_test_candidate_lf.py` | stdout `Ran 29 tests` / `OK` / `PASS=29 FAIL=0`、exit 0 | **本轮未跑**（禁执行 / 禁 import 候选）；先例 R3:145 + `_test_rerun_out.txt:1-3`（历史实跑，本轮实读：候选路径 = candidate_lf.py、用例总数 29） |
| T2 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py verify` | `VERIFY_ALL = PASS`（:618 打印行本轮实读） | **本轮未跑**；:646 为设计会话历史实跑记录 |
| T3 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_ast_scan.py` | 逐符号表全 UNCHANGED、候选新增禁止边 = 无 | 输出件本轮实读核验（§4）；规格员轮实跑 exit=0（转引）、复核员轮重跑输出逐字节一致（复核回件转述）；撰写员轮未重跑 |
| T4 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_fingerprint.py` | §2.1 五指纹逐项相符 | 撰写员轮以独立 hashlib 实算等价完成（18 件，五上游逐项相符）；未另跑该脚本 |
| T5 | 绑乙时：14 组 fixture 按 STATE_MATRIX.json 逐行断言 verdict/confidence/is_new/usable_as_crash_evidence 四元组（R3:42 同法） | 14/14 match | **本轮未跑**（同 T1 禁令）；R3:42 为历史转引 |

> **★ T1 错版绑定缺陷（复核确证，本草案已修正，修正本身 unconfirmed 待签发人确认）**
> - 规格草案 §9 原 T1 绑 `lead\b2b_candidate_20261106\tests\test_candidate.py`——该件 :37 `CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_candidate_20261106/qc151_trip.candidate.py"`（本轮实读），指向已被 N-1 绑定替换的**旧候选**（`9656e432…`/420292，本轮实算），**非本任务书正式候选**（`ca23c116…`/412759）。
> - R3:145 的 `PASS=29 FAIL=0` 实跑命令是改绑副本 `_test_candidate_lf.py`（R3:150-153：唯一改动 = 第 37 行重定向；本轮 `diff` 实证仅 `37c37` 一处，两件 `def test_` 各 29 个，grep 实数）。
> - 后果：若按原 T1 执行，测的是旧候选 → 触发 N-5:57 / N-4:49「版本不符立即 STOP」「任务书不生效」。
> - 处置：本草案 T1 改绑 `_test_candidate_lf.py`（`1a1335d6…`/34111，本轮实算）；替代方案 = 签发人另做等价副本（唯一改动 = 第 37 行重定向到正式候选）。**此修正未经签发人确认前，标 unconfirmed。**

N-5 集成时 T1–T5 须对**应用后副本**重跑（NEXT_STEPS:55：仅离线 AST 语法核验、N-4 全矩阵、API 与改动面检查，不启动完整 harness）。

### 3.8 输出键名契约（候选实码，本轮实读）
- 快照 dict（:4589-4593）：`state/exists/size/sha256/mtime_pre/captured_at_epoch/captured_at_iso/error/traceback/source`（10 键；N10 双时刻缺一即契约失败）。
- classify 返回（:4624-4626）：`verdict/confidence/is_new/note/usable_as_crash_evidence/pre_snapshot_state`（6 键）。
- `_emit_f` 落盘（FRESHNESS 组，:4730-4753）：`freshness_verdict/freshness_confidence/freshness_is_new/freshness_note/pre_snapshot_state/usable_as_crash_evidence/captured_at_iso`（7 键；`is_new=None` 未测写 null，不得写 False 冒充已知，:4736-4739）。
- 成功路径 info（12 键，:4792-4812）经 `rec.add("EXCEPT","evidence_copy",info,…)` 落盘（:4813-4814）后 `_emit_f(...,"copied")`（:4815）。
- 错误路径 ERROR 三键（:4777-4785）：`freshness_copy_failed/freshness_copy_stage/freshness_copy_traceback`。
- 跑前落盘（H08）：`rec.add(FRESHNESS_GROUP,"captured_at_iso_pre",…)`（:6625-6629）。
- `post_observed`（:4720-4722）：`exists/size/sha256/mtime_post/captured_at_iso/read_error`（6 键）。
- 接线四点：H05 `finalize_trip` 形参（:6137）、H06 唯一调用点关键字传参（:6166-6168）、H08 构造跑前快照（:6623-6629）、H09 绑定名传入（:7367）——本轮逐行实读。

---

## 4 禁止 API 集合的 ast 调用边静态审查（基线 vs 候选逐符号对照）

### 4.1 方法与门禁清单
- 门禁清单（N-4:49 原文列举，**仅作为禁止集合规格清单**，非实现建议）：MiniDumpWriteDump、SuspendThread、StackWalk／StackWalk64、ReadProcessMemory、WriteProcessMemory、VirtualAllocEx、CreateRemoteThread、SetWindowsHookEx、OpenProcess、TerminateProcess 及其包装／动态查找；另核 subprocess、os.system、ctypes 相关调用边；禁止新增游戏发射与 taskkill 路径。
- 方法 = `ast.parse` 分别解析母本与候选（未 import、未执行），逐符号统计 实际调用边(call) / 名字与属性引用(load) / 动态查找字符串(dyn) / 别名赋值(alias)。**字符串计数不得代替调用边审阅**（N-4:49）；门禁**不做全文禁词反扫**——字面量命中仅旁证（两版均为 0，`_verify_ast_edges_out.txt:44-45` 本轮实读）。
- 两份独立实现交叉：规格员轮 `_n4_ast_scan.py`（输出 `_n4_ast_scan_out.txt`，本轮实算 `9986fc2e…`/22510）与复核员轮 `_verify_ast_edges.py`（输出 `_verify_ast_edges_out.txt`，本轮实算 `25cabb03…`/3364）。两份输出件本轮全文实读，逐符号结论一致。

### 4.2 逐符号对照（独立复核口径 call/load/attr/dyn/alias；`_verify_ast_edges_out.txt:5-18`）

| 符号 | 母本 call/load/attr/dyn/alias | 候选 | delta |
|---|---|---|---|
| MiniDumpWriteDump | 1/0/3/0/0 | 1/0/3/0/0 | UNCHANGED |
| SuspendThread | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| StackWalk | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| StackWalk64 | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| ReadProcessMemory | 1/0/3/0/0 | 1/0/3/0/0 | UNCHANGED |
| WriteProcessMemory | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| VirtualAllocEx | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| CreateRemoteThread | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| SetWindowsHookEx | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |
| OpenProcess | 5/0/15/0/0 | 5/0/15/0/0 | UNCHANGED |
| TerminateProcess | 0/0/0/0/0 | 0/0/0/0/0 | UNCHANGED |

规格员轮四列口径（load 含 Name-load + Attribute-ref）下 OpenProcess = 5/15/0/0、MiniDumpWriteDump = 1/3/0/0、ReadProcessMemory = 1/3/0/0（`_n4_ast_scan_out.txt:623-633`），与独立口径逐符号一致（差异仅 load/attr 两列拆分定义）。**候选新增禁止边符号 = 无**（`_n4_ast_scan_out.txt:635`；`_verify_ast_edges_out.txt:18,59`）。
- 禁止集合调用边明细（`_verify_ast_edges_out.txt:20-42`）：OpenProcess 母本 :782/:859/:2896/:3640/:4353 → 候选 :797/:874/:2911/:3655/:4368（纯行移 +15，计数不变）；ReadProcessMemory :2917→:2932；MiniDumpWriteDump :3658→:3673。

### 4.3 存量面（非本候选引入）
6 个包装函数两版同名同位（`_n4_ast_scan_out.txt:612-618` 本轮实读）：`get_process_creation_time` :781→:797、`s4_enum_modules` :836→:874、`_rpm_open` :2897→:2911、`_rpm_u32` :2920→:2932、`_qc151p3_frozen_dump` :3620→:3655+:3673、`_pid_alive_check` :4359→:4368。属母本既有采样机器（D-13 暂停语境的既有面），非本候选新增；其运行时行为未验（§5.5 未验 8）。

### 4.4 subprocess / os.system / ctypes / 动态解析 / import
- 进程创建边：`subprocess.Popen` 1→1（母本 :1099 → 候选 :1114，纯行移；args 无 gamemd/ra2loader/yuri/taskkill 标记——复核回件）。本轮旁证 grep：`os\.system` 母本/候选均 **0**；`taskkill` 仅出现在注释文本（母本 :47/:1173、候选 :47/:1188，两版同文），无调用边。**未新增游戏发射与 taskkill 路径**（N-4:49 该项通过）。
- ctypes：属性链 220→220、24 种逐类计数一致（`_n4_ast_scan_out.txt:640-664`）。
- 动态解析：getattr 13/13、importlib.util.spec_from_file_location 2/2、module_from_spec 2/2（合计 17/17，`_verify_ast_edges_out.txt:665-668`）；getattr 字符串实参零命中禁止名（dyn_forbidden 两版 0）。
- import：目标集合差 NEW=[] GONE=[]；名称级目标 23→25、**语句数** 22→24（`_verify_ast_edges_out.txt:52`）；新增 2 条函数内 `import traceback` 落在 H03/H04 错误分支（候选 :4609/:4775，本轮实读）。规格草案 §10「import 语句 23→25」表述不准（23/25 为名称级目标数）——更正登记于 §5.4。

### 4.5 调用边差集与门禁判定
- 非禁止集合新增调用边 10 种共 34 处（`_verify_ast_edges_out.txt:55-57`；`_n4_ast_scan_out.txt:673-684`）：`_finish`×13、`classify_except_freshness`×3、`make_pre_freshness_snapshot`×1、`_emit_f`×3、`pre.get`×4、`post.get`×4、`post_observed.get`×2、`post_observed.update`×1、`out.update`×1、`src.stat`×2；**消失边 0**。全部落在批准九 hunk 的新鲜性逻辑与错误出口内，与 R3:31-34「候选 = 母本 + H01–H09 逐字节」相容。
- 按 N-4:49 判据：FAIL 条件（禁止集合新增调用/导入/包装/动态解析）**未触发**；删除边 0 无需解释。**该项静态判定 PASS。**

---

## 5 独立复核回件（verdict = partial）+ 未验项单独节

### 5.1 复核回件结论（34 条命令，回件原文要点）
- **verdict = partial**。五项复核要求 ①指纹实算 ②B2 明文核对（无写错无漏项）③无字符串计数冒充 / 无已签署放行 / 无代签 APPROVE_SCOPE ④未把 R3 PASS 当可应用到母本 ⑤写域 / 未跑两份 qc 脚本——**本体均通过**。
- 确证缺陷 1 项：T1 测试命令绑错候选版本（详见 §3.7 登记框）——足以让「按原规格签署后交给 N-5」失败；标注不精确 1 项：import 语句计数（§5.4 更正）。
- 复核对规格员 AST 输出件做了重跑比对（逐字节一致）并自写 `_verify_ast_edges.py` 独立重扫——两份输出件本轮均实读核验；复核员重跑动作本身为回件内容，本轮未重复。

### 5.2 撰写员轮再证实（本轮实跑 / 实读，不采信记忆）
- 实跑命令：①`ls` 写域与三个证据目录；②`python -I -X utf8 -c`（hashlib 实算 18 件指纹，§2.1）；③`grep -c "def test_"` 两测试件 = 29/29 + `diff` 两测试件（仅 `37c37`）；④`grep -n` `_draft_semantics_check.py` 行数/VERIFY_ALL/argv（:599 `assert len(mat) >= 8`、:602 打印行数、:618 `VERIFY_ALL = PASS`、:623 argv 分发）；⑤`grep -n "_pre_freshness_snapshot"` 候选（H07 :6528 实位）；⑥`grep -c "os\.system"` 两版（0/0）+ `grep -n taskkill` 两版（仅注释）；⑦`git status --porcelain` 写域与五上游（写域仅 `??` 新目录，无既有文件改动记录）。
- 实读件：B2_FIX_DESIGN.md:108-207；NEXT_STEPS_20261106.md:41-60；STATE_MATRIX.json 全文；B2B_DESIGN.md:38-47 / 97-114 / 180-188 / 628-672；B2B_PREAUDIT.md:8-19；RULING_D24.md:48-65；R3:1-50 / 145-161；候选 :215-228 / 4580-4826 / 6131-6170 / 6619-6632 / 7362-7371；两份 AST 输出件；test_candidate.py / _test_candidate_lf.py :30-69；_test_rerun_out.txt:1-10。
- T1 缺陷独立成立（§3.7 登记框全部证据均为本轮实跑/实读）；五上游指纹逐一相符；母本/候选指纹与 R3 绑定一致。

### 5.3 被核对象（本轮实算）
被核对象 SHA256 = cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306，字节数 = 22136（规格草案 `_n4_SPEC_N4_B2B_MATRIX.md`——独立复核的主要被核对象）。
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508（母本，收尾复核未变）。
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759（正式候选）。

### 5.4 verdict = partial 的处置
- **T1 绑定缺陷**：本草案 §3.7 已把 T1 改绑 R3 改绑副本并登记缺陷——该修正本身**未经签发人确认，标 unconfirmed**；签发人确认（或改绑等价副本）是任务书生效条件之一（§6）。
- **import 计数更正**：规格草案 §10「import 语句 23→25」→ 更正为「名称级 import 目标 23→25、import 语句 22→24」（`_verify_ast_edges_out.txt:52`；+2 条函数内 `import traceback` 结论不变，候选 :4609/:4775）。
- 复核通过的各项内容（指纹、B2 明文、AST 数字、无代签、写域）已直接采编进 §2–§4，并经 §5.2 独立再证实。

### 5.5 未验项（单独节，如实登记，不补造）
1. T1 / T5 本轮未跑（禁令：不执行、不 import 候选）——`PASS=29 FAIL=0`（R3:145）与 14/14 match（R3:42）均为**历史转引**，本轮未独立复现。
2. T2 本轮未跑：`VERIFY_ALL = PASS` 的 :646 记录为设计会话历史实跑；且该记录打印「STATE_MATRIX.json 行数 = 12」，现行文件为 14 数据行（本轮实读 :2-15）——记录时点差异未追溯；重跑预期打印 14（`_draft_semantics_check.py:599` 仅断言 `>=8`、:602 打印 len），判据本体不受影响，**此为实读推演，以实际输出为准**。
3. 矩阵甲/乙**绑定未决**——签发人决断点（§3.6），本草案不代决。
4. §3.7 的 T1 改绑修正 **unconfirmed**——待签发人确认。
5. `RULING_D25.md` 原文未直接实读（经 B2B_DESIGN.md:43 与 R3:23 转引）。
6. `lead/b2b_isolated_20261107/INTEGRATION_REPORT.md` 存在（目录 ls 实见）但本轮未审阅内容——隔离副本集成当前状态**未验**。
7. 候选对母本的正式应用未做（N-5 未发生）。
8. 母本既有采样机器（6 个包装函数，§4.3）本轮仅静态审阅调用边，其运行时行为**未验**。
9. 运行时退出码语义未复现（B2B_DESIGN.md:652 自我声明未验；本轮同样未做，零真机）。

---

## 6 结论

- **grade = SPEC_DRAFT（规格草案，未生效，非放行）**。本文件把 N-4 要求的 7 分支矩阵（absent_both / vanished / new_first_appearance / new_write / rewritten_same_content / leftover_unchanged 七值）、空快照、复制失败与 4 类异常契约逐项固定到文件:行，并附基线 vs 候选的逐符号调用边静态审查；全部数字来自本轮实跑/实读，未验项单列 §5.5。
- **独立复核 verdict = partial**：五项本体通过；T1 绑定缺陷已在本草案修正但 unconfirmed（§5.4）；import 计数已更正。规格草案在本修正确认前**不得**据以签署生效。
- **签署主体与生效条件**：候选 YES 由独立审阅者签（已有 R3:21，不因本轮升级为可应用，R3:23）；`APPROVE_SCOPE` 由来源会话任务签发人签（N-4:49），签署时须同时：①显式声明矩阵甲/乙绑定（N-4:47）；②确认 §3.7 修正后的 T1 绑定（或另做等价副本）；③以 N-1 记录格式绑定本任务书签署时点哈希与基线/候选哈希。身份、任一规则或版本缺失则任务书不生效（N-4:49）。
- **N-5 另派要求**：持 N-4 有效新任务书另派执行者（RULING_D24:61；NEXT_STEPS:55）；应用前重核母本指纹，变化则 STOP（RULING_D24:52；NEXT_STEPS:57）；仅离线做 AST 语法核验、N-4 全矩阵、API 与改动面检查（T1–T5 对应用后副本重跑）；由独立静态复核者验收；**不启动完整 harness**；不签真机验收或崩溃修复完成。
- **本轮承诺兑现**：未运行完整 harness、未实施集成、未 import / 未执行母本与候选（仅 `ast.parse` 只读解析与 hashlib 实算）；母本轮前轮后指纹均为绑定值（§2.1 收尾实算）；母本与既有件零改动（git status 实查）；不 commit、不 push。
