# N-4 验收矩阵与 API 基线规格（草案）· B2b 候选 qc151_trip.candidate_lf.py

- 件名：`lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md`
- 日期：2026-11-08　作者：验收规格员·GLM（动态工作流子代理）
- 性质：**规格草案 + 静态调用边审查，不是放行**（见 §11）。
- 铁律遵守：零真机、零采样代码；本轮未运行两份 qc 脚本、未 import 它们（仅 `ast.parse` 只读解析）；不 commit、不 push；唯一写域 = `lead/bexec_n4_20261108/`。

---

## 0 一句话结论

N-4 原文（`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:45-51`）固定的 7 分支矩阵来自 **B2 设计**（`lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md:133-154`，本轮实读核实）；但 R3 判 PASS 的候选实际实现并绑定的是 **B2b 设计**（`lead/b2b_design_20261106/B2B_DESIGN.md` + 同目录 `STATE_MATRIX.json` 14 行矩阵），两套矩阵在 **4 处分支上取值不同**（absent_both 置信、vanished 置信、空快照语义、mtime_pre 缺失），且 B2b 改动面为 **H01–H09 九 hunk**（替代 B2 的 A—D 四处与更旧 TASK 的「三处」）。本草案把两套矩阵**都**逐分支固定到文件:行，把绑定选择列为**签发人决断点**（N-4:47「若与设计冲突退 N-2，不由测试者临时决定」）；静态调用边审查结论：**禁止 API 集合两版逐符号零差异、零新增**。

---

## 1 对象与指纹（本轮实跑：`python -I -X utf8 lead\bexec_n4_20261108\_n4_fingerprint.py`，hashlib 实算）

| 对象 | SHA256 | 字节数 |
|---|---|---|
| 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 |
| 候选 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412759 |
| B2 设计 `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11638 |
| N-4 原文 `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27225 |
| D-24 裁决 `lead/re_line_20261105/D24_RULING/RULING_D24.md` | `56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5` | 15301 |

五者与任务书上游指纹清单**逐一相符**；母本指纹与 R3 绑定记录一致（`lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md:13`）。

**被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508**（母本）；
**被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759**（候选）。

---

## 2 上游链路与两套设计的关系（本轮实读）

1. **B2**（B2_FIX_DESIGN.md）：六条修正的设计，:198 明写「本文件只是设计。应用前必须重新走一遍 B1 的预审硬门」。
2. **B2b**（B2B_DESIGN.md）：B2 的修订版设计。`lead/b2b_preaudit_20261106/B2B_PREAUDIT.md:13` `verdict: YES`（:16 限定「可以拿去编写候选；不等于可以应用到母本」）；D-25 裁决约束「立即可安排范围止于新指定写域内的 B2b 设计和独立设计预审」（B2B_DESIGN.md:43 转引 `RULING_D25.md:21,34-37`）。
3. **候选**：R3 复审判 `verdict: PASS`（CANDIDATE_SEMANTIC_REVIEW_R3.md:21），其**对照设计即 B2B_DESIGN.md + STATE_MATRIX.json**（R3:5），并实跑证明「候选 = 母本 + 设计 §4 九 hunk，一字节不多、一字节不少」（R3:31-34，决定性①②）。R3:23 明写 **PASS ≠ 可应用到母本**。
4. **N-4 原文**（NEXT_STEPS:47-48）自述「矩阵正常分支来自本轮实际读到的设计」——该设计是 B2（写于 2026-11-06 11:25，早于 B2B_DESIGN.md 的 2026-11-06 15:58 文件时间，时间戳为 ls 实见）。故 N-4 的矩阵文本**未被 B2b 修订同步**。

## 3 改动面（替代旧 TASK「三处」限制的条款）

- **旧限制**：旧 TASK §3.3 只列两处调用点、§6.2 要求「只改三处」，与合法接线死锁（B2_FIX_DESIGN.md:103-107）。
- **B2 中间版 A—D 四处**（B2_FIX_DESIGN.md:113-116、:118「四处改动是可论证的最小集」、:179-192 预计净增≈31 行删除 0 行）：
  - A `backup_carrier`（:4457-4461）补 `exists`/`mtime_pre`/`captured_at_epoch`；:88-90 限定 `exists: True` 只在成功备份分支写；
  - B `copy_post_except_evidence`（:4561-4562 签名 + :4573 前插判定 + :4583-4586 info）；
  - C `finalize_trip` 签名（:5900-5909）加 `pre_freshness_snapshot=None`；
  - D `_except_evidence_copy`（:5939）+ `finalize_trip` 调用点（:7117-7125）+ main 基线（:6387 后）接线。
- **B2b 现行版 H01–H09 九 hunk**（B2B_DESIGN.md §7 :656-668，`-`侧覆盖区间见 :635）：
  | H | 母本锚点 | 内容 |
  |---|---|---|
  | H01 | :214 后 | F 命名空间 5 常量（候选 :217-228） |
  | H02 | :4460 后 | `RESTORE.backup_mtime_pre:{name}` 留痕；**不改** `bak[name]` 三键（B2 修正 2 由此被取代） |
  | H03 | :4561 前 | 新增 `make_pre_freshness_snapshot` + `classify_except_freshness`；copy 签名加形参 |
  | H04 | :4574-4599 | copy 函数体重写：三态判别 + 正常/错误双落盘 + 3 条 ERROR 留痕 + raise + info 扩 12 键 |
  | H05 | :5909 | `finalize_trip` 签名加形参（候选 :6137） |
  | H06 | :5939 | 唯一调用点关键字传参（候选 :6166-6168） |
  | H07 | :6296 后 | 预初始化 `_pre_freshness_snapshot = None` |
  | H08 | :6388 后 | 构造跑前快照 + `FRESHNESS.captured_at_iso_pre`（候选 :6623-6629） |
  | H09 | :7125 后 | 把绑定名字传入 `:7117 finalize_trip`（候选 :7367） |
- R3 已实证候选与九 hunk 逐字节一致（R3:31-34）；本轮 AST 差集（§10）与之相容。

---

## 4 矩阵甲 · N-4 原文口径（B2_FIX_DESIGN.md:133-154 实码；N-4:47 逐项对应）

输入语义：`_pre = dict(pre_snapshot or {})`（:133）⇒ **空快照 {} 与显式 `exists=False` 与 None 三者等价**（N-4:47 明文）；`_pre_exists = bool(_pre.get("exists"))`（:134）。

| # | 场景 | verdict | confidence | 实码行 |
|---|---|---|---|---|
| 1 | 跑前无 + 跑后无 | absent_both | n/a | :137-138 |
| 2 | 跑前有 + 跑后无 | vanished | high | :137-138 |
| 3 | 跑前无 + 跑后有 | new_first_appearance | high | :141-142 |
| 4 | 两者有且 SHA 不同 | new_write | high | :148-149 |
| 5 | SHA 同 mtime 增 | rewritten_same_content | medium | :150-152 |
| 6 | SHA 同 mtime 减 | rewritten_same_content | low（「同分类,low」） | :150-152 |
| 7 | SHA 与 mtime 均同 | leftover_unchanged | high | :154 |

早退分支带结论：跑后无件时 note 附新鲜性判定，并 `rec.add("EXCEPT","evidence_freshness",...)`，note「不做 crash 归因（:677）」（:155-161）；修正动因即「absent_both 与 vanished 两个分支永远输出不了」（:123）。
合成字典单测输入：`{}` 与 `{"exists": True, "sha256": X, "mtime_pre": T}`（:202）；早退期望 `pre={"exists": False}`+跑后无件→absent_both、`pre={"exists": True}`+跑后无件→vanished（:203-204）。
甲的输出落盘仅 2 条记录（早退 note + evidence_freshness），无独立 F 命名空间、无 is_new/state 字段。

## 5 矩阵乙 · B2b 现行设计口径（STATE_MATRIX.json 14 行 + 候选 :4616-4698 实码）

判别口：`state` 字段唯一判别（候选 :4583-4585、:4636-4639）；`None`/`{}`/缺 `state`/脏值一律 `unknown`，**绝不等于「跑前确认无件」**（B2B_DESIGN.md:100-106：`{"exists": False}`（无 state）不再是「确认无件」，确认无件必须显式 `state="absent_confirmed"`）。
值域（候选 :221-228）：`FRESHNESS_VERDICTS` 9 值 = unknown/absent_both/new_first_appearance/vanished/leftover_unchanged/new_write/rewritten_same_content/error_pre_snapshot/post_read_error；`FRESHNESS_CONFIDENCES` = high/medium/low/none（**无 n/a**）；`FRESHNESS_SNAPSHOT_STATES` = unknown/absent_confirmed/present/error；`usable_as_crash_evidence` 恒 False（:4624-4631）。

| # | state（跑前） | 场景 | verdict | confidence | is_new | 候选实码 | 矩阵行 |
|---|---|---|---|---|---|---|---|
| 1 | unknown | pre=None/{}/缺state/脏值，跑后任意 | unknown | none | None | :4648-4651 | STATE_MATRIX.json:2-3 |
| 2 | error | 跑前采集抛异常 | error_pre_snapshot | none | None | :4652-4654 | :4 |
| 3 | present | 跑后读/写/统计异常（read_error 非空） | post_read_error | none | None | :4643-4646 | :5 |
| 4 | absent_confirmed | 跑前确认无件 + 跑后在场 | new_first_appearance | high | True | :4666-4669 | :6 |
| 5 | absent_confirmed | 跑前确认无件 + 跑后无件 | absent_both | **low** | False | :4657-4661 | :7 |
| 6 | present | sha 同 + mtime 未变（双侧齐全） | leftover_unchanged | high | False | :4690-4692 | :8 |
| 7 | present | sha 同 + mtime 侧缺失 | leftover_unchanged | **medium** | False | :4685-4689 | :9 |
| 8 | present | sha 不同 | new_write | high | True | :4681-4683 | :10 |
| 9 | present | sha 同 + mtime 变大 | rewritten_same_content | medium | True | :4697-4698 | :11 |
| 10 | present | sha 同 + mtime 回拨 | rewritten_same_content | low | True | :4693-4696 | :12 |
| 11 | present | 跑前在场但缺 pre.sha256 | error_pre_snapshot | none | None | :4672-4676 | :13 |
| 12 | present | 跑后缺 post.sha256 | post_read_error | none | None | :4677-4680 | :14 |
| 13 | present | 跑前在 + 跑后无件 | vanished | **none**（异常旗标，须人工复核，is_new=null） | None | :4662-4664 | :15 |

R3 已用 14 组 fixture 对候选真实函数逐行 exec 实跑，`verdict+confidence+is_new+usable_as_crash_evidence` 四元组 14/14 match（R3:42-44）；13 处 `_finish(` 出口与矩阵行映射齐全（R3:43）。

## 6 甲↔乙差异对照与处置（签发人决断点）

| 分支 | 甲（N-4:47/B2） | 乙（B2b/候选/R3 PASS 口径） | 差异 |
|---|---|---|---|
| absent_both | confidence **n/a** | **low**（「不能证无崩溃」） | 值不同 |
| vanished | confidence **high** | **none**（不给 high、is_new=null、人工复核） | 值相反 |
| 空快照 {} | ≡ exists=False（→absent_both/new_first_appearance） | → **unknown/none**（未知≠不存在） | 语义相反 |
| mtime_pre 缺失 | 未单独定义（:150 守卫跳过 → 依 sha 定 verdict） | leftover_unchanged/**medium**（盲区未覆盖标注） | 乙新增显式行 |
| 读写异常/缺省 None | 未定义 | error_pre_snapshot / post_read_error / unknown（均 none） | 乙新增出口 |
| confidence 值域 | 含 n/a | high/medium/low/none（无 n/a） | 值域不同 |
| 字段 | verdict+confidence | verdict/confidence/is_new/note/usable_as_crash_evidence/pre_snapshot_state | 乙超集 |

**处置（本草案不改验收口径，只登记）**：两套矩阵不能同时绑定为通过判据。按 N-4:47「若与设计冲突退 N-2，不由测试者临时决定」与 N-4:49「身份、任一规则或版本缺失则任务书不生效」，**由 N-4 任务书签发人在签署时显式声明绑定哪一套**。事实面：候选是按乙实现并经 R3 以乙对照判 PASS（R3:5,42-44）；若绑甲，该候选在 #1/#5/#13 及空快照/None 各场景必判 FAIL（N-5:57「矩阵任何预期不符…均 FAIL」）。**本草案建议（仅建议，非裁决）绑乙**，理由：乙是 N-2 复审链（B2B_PREAUDIT YES → D-25 → R3 PASS）的现行批准设计，且乙对 N-4 要求的四类异常契约覆盖更严（§7）。

## 7 空快照、复制失败、四类异常契约（按乙逐项固定；甲对应行为见 §4/§6）

每项固定：输入 → 返回值 → 落盘记录 → 错误预期（均为候选实码行）。

1. **空快照 `{}`（及 None / 缺 state / 脏值）**：`classify_except_freshness({}, post)` → `{"verdict":"unknown","confidence":"none","is_new":None,"pre_snapshot_state":"unknown"}`（:4634-4651）；落盘 `_emit_f` 7 键（:4730-4753）；**不作**「本趟新出现」归因，R3 穷举 36 组无 unknown→high 泄漏（R3:44）。
2. **复制失败（须记 error 且不签复制成功）**：copy 内 `try` 捕获读/写异常 → `rec.add("ERROR","freshness_copy_failed"/"freshness_copy_stage"/"freshness_copy_traceback",...)` 三条留痕（:4773-4785）→ `post_observed["read_error"]` 置错（:4786）→ `_emit_f(...,"copy_failed")` 落 F 字段（:4787-4789）→ **`raise` 原异常**（:4790）；成功路径 info/`EXCEPT.evidence_copy` 记录**不写**（info 仅 :4813 成功路径可达）⇒ 不签复制成功。早退（跑后无件）路径：`rec.add("EXCEPT","evidence_copy",None,...)` + `_emit_f(...,"src_missing")` + `return None`（:4756-4764）。
3. **mtime_pre 缺失**：state=present 且 sha 同但 mtime 侧缺失 → `leftover_unchanged`/`medium`/`is_new=False`，note「A 旁证不可用，同内容重写盲区此趟未覆盖（如实标注，不虚报 high）」（:4685-4689）；不作新崩溃归因（usable_as_crash_evidence=False）。
4. **读写异常（跑前侧）**：`make_pre_freshness_snapshot` 采集抛异常 → `state="error"` + `error`/`traceback` 字段填充（:4594-4613，N1：独立出口，不降级、不静默、不给 high）→ classify 走 `error_pre_snapshot`/none（:4652-4654）。
5. **初始化前收尾**：`try` 内 :6313..7029 任一点抛出时，抛出早于 :6389 则快照为 H07 预初始化的 `None` → classify 得 `unknown`/none；原异常由 :7037 `raise` 保留，收尾失败不写 verdict 局部量（B2B_DESIGN.md:184 P6 契约；候选 :6154-6158 CLEANUP_FAILURES 口径）。
6. **缺省调用路径**：`finalize_trip(pre_freshness_snapshot=None)`（:6137 默认）与 `copy_post_except_evidence(pre_freshness_snapshot=None)`（:4703 默认）→ 非 dict 归一 `{}` → `unknown`/none（:4634-4651）。**与 N-4「报告未验或错误、不作新崩溃归因」相符；与 B2 甲的 `{}→new_first_appearance(high)` 冲突，冲突登记于 §6。**
7. **F/E 边界（:677 不侵犯）**：F 恒写 `FRESHNESS` 组（H01 常量 :221-222），E 的集合差判据块 :5984-5990 逐字未改，9 个 hunk 覆盖区间均不含该块（B2B_DESIGN.md:635 实算；候选 :4619-4621 N9 声明）。

## 8 输出字段契约（固定键名）

- 快照 dict（:4589-4593）：`state/exists/size/sha256/mtime_pre/captured_at_epoch/captured_at_iso/error/traceback/source`（10 键；N10：双时刻缺一即契约失败，:4586）。
- classify 返回（:4624-4626）：`verdict/confidence/is_new/note/usable_as_crash_evidence/pre_snapshot_state`（6 键）。
- `_emit_f` 落盘（FRESHNESS 组，:4730-4753）：`freshness_verdict/freshness_confidence/freshness_is_new/freshness_note/pre_snapshot_state/usable_as_crash_evidence/captured_at_iso`（7 键；`is_new=None` 未测写 null，不得写 False 冒充已知，:4736-4739）。
- 成功路径 info（12 键，:4792-4812）：`source/evidence_path/size/sha256/note/mtime_post/freshness_verdict/freshness_confidence/freshness_note/captured_at_iso/pre_snapshot_state/pre_freshness_snapshot`；以 `rec.add("EXCEPT","evidence_copy",info,...)` 落盘（:4813-4814）后 `_emit_f(...,"copied")`（:4815）。
- 错误路径 ERROR 三键（:4777-4785）：`freshness_copy_failed/freshness_copy_stage/freshness_copy_traceback`。
- 跑前落盘（H08）：`rec.add(FRESHNESS_GROUP,"captured_at_iso_pre",...)`（:6625-6629）。
- `post_observed`（:4720-4722）：`exists/size/sha256/mtime_post/captured_at_iso/read_error`。

## 9 测试命令与预期（签发人绑定后即为 N-5 通过判据）

| # | 命令（绝对路径，python -I -X utf8） | 预期 | 本轮状态 |
|---|---|---|---|
| T1 | `python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_candidate_20261106\tests\test_candidate.py` | stdout `PASS=29 FAIL=0`、exit 0（29 个 `def test_`，grep 实数；R3 实跑先例 R3:23） | **本轮未跑**（禁令：不执行/不 import 候选） |
| T2 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py verify` | `VERIFY_ALL = PASS`（专项检查 A/B/C，B2B_DESIGN.md:646 实跑先例） | 本轮未跑（设计侧静态件） |
| T3 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_ast_scan.py` | 逐符号表全 UNCHANGED、候选新增禁止边=无（本轮实跑，输出 `_n4_ast_scan_out.txt`） | **已跑，通过** |
| T4 | `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\bexec_n4_20261108\_n4_fingerprint.py` | §1 五指纹逐项相符 | **已跑，通过** |
| T5 | 矩阵单测（若绑乙）：14 组 fixture 按 STATE_MATRIX.json 逐行断言四元组（R3:42 同法） | 14/14 match | 本轮未跑（同 T1 禁令） |

N-5 集成时 T1–T5 须对**应用后副本**重跑（NEXT_STEPS:55：仅离线 AST 核验、N-4 全矩阵、API 与改动面检查，不启动完整 harness）。

## 10 API 基线与静态调用边审查（本轮实跑：`_n4_ast_scan.py` → `_n4_ast_scan_out.txt`）

方法：`ast.parse` 分别解析母本与候选（未 import、未执行）；对禁止集合逐符号统计 实际调用边(call)/名字与属性引用(load)/动态查找字符串(dyn)/别名赋值(alias)；另扫 subprocess/os.system/进程创建边、ctypes 属性链、getattr/__import__/eval/exec/compile/importlib 动态解析、包装函数、字符串实参。

- **禁止集合逐符号**（11 符号 call/load/dyn/alias）：MiniDumpWriteDump 1/3/0/0；SuspendThread、StackWalk、StackWalk64、WriteProcessMemory、VirtualAllocEx、CreateRemoteThread、SetWindowsHookEx、TerminateProcess 全 0；ReadProcessMemory 1/3/0/0；OpenProcess 5/15/0/0 —— **两版逐符号全部 UNCHANGED，候选新增禁止边符号 = 无**（`_n4_ast_scan_out.txt:620-635`）。这些存量调用是母本既有的采样机器（`get_process_creation_time`/`s4_enum_modules`/`_rpm_open`/`_rpm_u32`/`_qc151p3_frozen_dump`/`_pid_alive_check`，6 个包装函数两版同名同位，候选 :781/:836/:2897/:2920/:3620/:4359），属 D-13 暂停语境下的母本既有面，非本候选新增。
- **动态解析**：getattr 13、importlib.util.spec_from_file_location 2、module_from_spec 2，两版一致；getattr 字符串实参均为 `fullscreen/evid_diff/spot_select/sg_*/measure/trip_id/filename` 等 UI/记录键，**无一命中禁止名**（dyn_forbidden 两版均 0）。
- **subprocess / os.system / 游戏发射与 taskkill**：`subprocess.Popen` 1→1（母本 :1099 → 候选 :1114，纯行移）；`os.system` 0→0；无 taskkill 调用边；进程创建边的字符串实参无 gamemd/ra2loader/yuri/taskkill 标记（`CARRIER_FILES` 的 "gamemd.exe" 等是数据常量，非发射边，两版一致）。**未新增游戏发射与 taskkill 路径**（N-4:49 该项通过）。
- **ctypes**：import 目标集合完全一致（`import ctypes`/`ctypes.wintypes as wt` 等 23 语句→25 语句，目标集合不变）；ctypes.* 属性链 220→220 逐类计数一致（`_n4_ast_scan_out.txt:640-664`）。
- **非禁止集合的实际新增调用边（10 种，共 34 处）**：`_finish x13、classify_except_freshness x3、make_pre_freshness_snapshot x1、_emit_f x3、pre.get x4、post.get x4、post_observed.get x2、post_observed.update x1、out.update x1、src.stat x2` —— 全部落在 §5/§8 的 B2b 新鲜性逻辑与错误出口内；另有 **2 条新增函数内 `import traceback`**（候选 :4609/:4775，即 H03/H04 错误分支）。**候选消失边 0 种**。按 N-4:49，FAIL 判据限于禁止集合（含 subprocess/os.system/ctypes 与动态解析），以上新增均在集合外，且与 R3「候选=母本+H01–H09 逐字节」实证（R3:31-34）相容，属已批准 hunk 范围内变动。
- **门禁规则（签发人绑定后生效）**：对禁止集合逐符号及调用边计数，候选新增调用/导入/包装/动态解析均 FAIL；删除也须解释且只许批准 hunk 内变动；字符串计数不得代替调用边审阅（本轮为 ast 调用边审阅）。

## 11 放行边界（重申任务书第 3 条）

本轮交付 = **规格草案 + 静态审查**。不签 `APPROVE_SCOPE`（签署属来源会话任务签发人，N-4:49）；不代签候选 YES（签署属独立审阅者；现有 R3:21 PASS 不因本轮升级为「可应用」）；N-5 正式集成须**持 N-4 有效新任务书另派**执行者，应用前重核母本指纹（RULING_D24.md:52 第 5 条；NEXT_STEPS:55）。母本在本轮前后未被改动（§1 指纹本轮实算仍为绑定值）。

## 12 未验项（单列，不补造）

1. 两份 qc 脚本本轮未执行、未 import；T1/T5（29 用例套件与 14 fixture 矩阵单测）未复跑——R3:23 的 `PASS=29 FAIL=0` 为转引，本轮未独立复现。
2. 矩阵甲/乙的**绑定选择未决**——N-4 签发人决断点（§6），本草案不代决。
3. `lead/b2b_isolated_20261107/INTEGRATION_REPORT.md` 存在（ls 实见）但本轮未审阅其内容——隔离副本集成当前状态**未验**。
4. `RULING_D25.md` 原文未直接实读，D-25 约束经 B2B_DESIGN.md:43 与 R3:23 转引。
5. 候选对母本的正式应用未做（N-5 未发生）；「观测集成、根因定位、修复有效性和真实数百单位验证」仍按 NEXT_STEPS:5 未验。
6. T2 设计侧 verify 脚本本轮未重跑（B2B_DESIGN.md:646 为历史实跑记录）。

## 13 引用与命令清单（本轮实跑）

- 实跑命令：①`mkdir`+`ls` 五上游件；②`python -I -X utf8 …\_n4_fingerprint.py`（§1）；③`python -I -X utf8 …\_n4_ast_scan.py > …\_n4_ast_scan_out.txt`（§10，exit=0）；④grep 候选/母本 A–D 与 H 锚点、FRESHNESS 常量、B2b 矩阵与 hunk、PREAUDIT/REVIEW verdict、测试套件计数；⑤Read：B2_FIX_DESIGN 全文、NEXT_STEPS:1-80、RULING_D24:45-79、候选 :215-232/:4580-4859/:6127-6176/:6615-6634、STATE_MATRIX.json 全文、R3:1-45、B2B_DESIGN:97-110。
- 判定依据行号均为本轮实读/实跑所得，未采信记忆。
