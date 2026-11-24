# 第三轮语义复审判定书 · B2b 候选 LF 重物化版（D-25 第 5 步）

**日期**：2026-11-07　**作者**：R3 语义复审员（独立复审，新上下文）
**复审对象**：`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（只读，未改动一字）
**对照设计**：`lead/b2b_design_20261106/B2B_DESIGN.md` + 同目录 `STATE_MATRIX.json`（只读）
**方法**：全部数字取自本次会话亲自实跑（`python -I -B -X utf8` + 绝对路径，指纹 `hashlib`）或本次实读的「文件:行」。候选一律 `ast.parse` 静态解析，**未 import**；语义执行用 `importlib` + `patch("ctypes.windll.user32.SetProcessDPIAware")` 隔离加载（与 `tests/test_candidate.py:40-57` 同法，任务书许可路径；模块名 `qc151_candidate_mod_r3`，未触发 `__main__` 入口）。零真机、零采样代码、不 commit / push。**唯一写域** = `lead/b2b_candidate_review3_20261107/` 下本判定书 + 探针 + 三份重跑输出 + 测试/门禁路径副本。
**验收口径**：`lead/b2b_candidate_review2_20261106/TASK.md:183-221` 裁定附录（裁定一 / 裁定二，**现行口径**）+ 本轮 ask 的九条硬性判定规则。R2 唯一阻断项 N-1（行尾 CRLF）已由 `lead/b2b_n1_binding_20261107/N1_BINDING.md` 重新物化 + 重新绑定关闭，本轮独立实算复核。

## 头部 · 五件实算指纹（Python hashlib，实跑输出 `_review_probe_r3_out.txt:3-7`）

| 对象 | 路径 | SHA256（64 hex） | 字节数 | LF/CR | 与绑定记录一致 |
|:--|:--|:--|--:|:--|:--|
| 母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 | 7291/0 | True |
| 候选（LF） | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 | 7533/0 | True |
| 候选 diff | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` | `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` | 18,454 | 339/0 | True（N1_BINDING §6） |
| 批准设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 | 693/0 | True（R2 `:13`） |
| N-1 绑定 | `lead/b2b_n1_binding_20261107/N1_BINDING.md` | `00ea6fe87ee5508b84332447b23951d4db86a1682ee36aaa48a3bd9cf774d310` | 8,493 | 133/0 | 本轮实算 |
| R2 判定书（旁证） | `lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md` | `126e18954d77d989bf7c036de676c3d3566f0d4feaa2afb2099ac5f671d76546` | 27,593 | — | 本轮实算 |
| R2 TASK（旁证） | `lead/b2b_candidate_review2_20261106/TASK.md` | `63336d058952fc360c82f0341d85963ee88fe47adc458000724abcffe8533eca` | 13,763 | — | True（N1_BINDING §1） |

verdict: PASS

**一句话总括**：R2 的唯一阻断项 N-1（整篇行尾 LF→CRLF）经本轮独立实算确认已关闭——候选与母本**双方 CR=0**，且「母本 + 设计 §4 九 hunk」与「母本 + CANDIDATE_LF.diff」两条独立重建路径都**逐字节**等于候选（`_review_probe_r3_out.txt:124,126`），字节层与行文本层均无 H1–H9 之外的改动；R2 已排除的七项硬性条件本轮**全部逐条重验未触发**；九条硬性阻断规则逐条核对**零触发**；本人亲自重跑测试 `PASS=29 FAIL=0`、门禁 9/9（门禁只记档 1）。按修正后口径，候选**语义上实现了批准设计**。**PASS ≠ 可应用到母本**（D-25 第 6 步隔离副本集成未做，`N1_BINDING.md:110`）。

---

## 0 本轮范围 · N-1 关闭的独立确认

R2 `verdict: BLOCKED` 的**唯一成因**是 N-1（候选整篇行尾被改 CRLF，属设计 §4 未声明的字节级改动，触发硬性规则「diff 有超出 H1–H9 的改动 ⇒ BLOCKED」，见 R2 `:20,84-97,119-131`）。N-1 的关闭路径 2（按母本 LF 重新物化 + 总控重新绑定）由 `N1_BINDING.md` 执行，其 `:108` 明文「R2 对候选语义的各项裁定不变，候选仍需重新送语义复审」——本轮即该重审。本轮独立实算（非转抄绑定记录）：

- 候选 `CR=0 / LF=7533`，母本 `CR=0 / LF=7291`（`_review_probe_r3_out.txt:10-11`）——**字节级 keepends diff 与行文本 diff 完全一致**（变更块均 12、+255/-13，`:122-123`），R2 `:87` 描述的「整篇退化为替换」不再存在。
- **决定性①**：解析 `B2B_DESIGN.md` 的 9 个 ```diff 块（标准 unified diff 应用，上下文/`-` 行逐行断言母本原文、消费行数与 hunk 头声明逐个断言），重建文本 == 候选（逐字节，SHA 前 16 位同为 `ca23c116064b25a6`，`:124`）。
- **决定性②**：`CANDIDATE_LF.diff`（9 个 `@@` 头）同样从母本逐字节重建出候选（`:125-126`）。
- 二者共同构成：候选 = 母本 + 设计 §4 九 hunk，**一字节不多、一字节不少**。

---

## 1 状态矩阵对照

对照 `lead/b2b_design_20261106/STATE_MATRIX.json`（14 行）与候选 `classify_except_freshness`（`qc151_trip.candidate_lf.py:4616-4698`）：

- **14/14 逐行 match**：本人以 14 组 fixture 逐一 exec 实跑（隔离加载模块的真实函数），比对 `verdict + confidence + is_new + usable_as_crash_evidence` 四元组，14 行全 `match=True`（`_review_probe_r3_out.txt:135-149`）。例：行1 `unknown/none/None/False`、行5 `new_first_appearance/high/True`、行7 `leftover_unchanged/high/False`、行10 `rewritten_same_content/medium/True`、行12 `error_pre_snapshot/none`、行14 `vanished/none`。
- **分支静态覆盖**：`_finish(` 在候选全文 14 处（1 处 `def` @`:4628` + **13 处调用**：`:4644/:4649/:4653/:4659/:4662/:4667/:4674/:4679/:4682/:4687/:4691/:4694/:4697`），与 R2 `:51` 的 13 处一致；14 行矩阵到分支的映射：行1-2→`:4649`（unknown 出口，`None`/`{}`/缺`state`/脏值/显式`unknown` 都经 `:4637-4638` 归一后到达）、行3→`:4653`、行4/13→`:4644`/`:4679`（post_read_error 两入口）、行5→`:4667`、行6→`:4659`、行7/8→`:4691`/`:4687`、行9→`:4682`、行10/11→`:4697`/`:4694`、行12→`:4674`、行14→`:4662`。**无任何状态找不到对应分支**。
- **unknown 恒 none**：`high` 置信仅 `:4667/:4682/:4691` 三处，均非 unknown 出口；穷举 9 种未采集/脏值 pre × 4 种 post = 36 组，`unknown+非none` 与 `crash_ev≠False` 泄漏 = **0**（`_review_probe_r3_out.txt:157-159`）。
- **三态可分（裁定一口径，`TASK.md:193-199`）**：同一 `post` 下 `unknown→unknown/none`、`absent_confirmed→new_first_appearance/high`、`present→new_write/high`，三 verdict 两两不等；**裁定一验收点「`{"state":"absent_confirmed","exists":False}` 与 unknown 输出不同」= True**（`_review_probe_r3_out.txt:150-156`）。原始输入 `None`/`{}`/`{"exists":False}` 输出相同 = 设计归一意图（`B2B_DESIGN.md:100-106`），**不算阻断**。
- **快照采集器行为**（`make_pre_freshness_snapshot`，候选 `:4580-4613`）：在场文件（以候选自身文件为只读输入）→ `state=present`、sha256 与实算指纹一致、`captured_at_epoch/iso` 双时刻齐；不存在路径 → `state=absent_confirmed`（`_review_probe_r3_out.txt:160-164`）。`FRESHNESS_SNAPSHOT_STATES` 4 态、`FRESHNESS_VERDICTS` 9 值、`FRESHNESS_CONFIDENCES` 4 值与设计 H01 逐字一致（`:130-132`）。
- **保留登记（沿用 R2 `:53,107`，非候选缺陷）**：`STATE_MATRIX.json:2` 行 1 的 condition「跑后任意文件状态」措辞过宽——实测 `pre=None + post.read_error` → `post_read_error/none`（行 4 fixture 同理），因 `:4643-4646` 的 read_error 独立出口按设计 `B2B_DESIGN.md:310-311`（N1 错误优先于折叠）排在 unknown 之前。矩阵文档精度事项，无 high / 崩溃证据泄漏，不构成阻断。

**小结：硬性规则 1（状态缺分支）、2（unknown 给 high）、3（状态值层面不可分）均未触发。**

## 2 调用传参核对

- **`copy_post_except_evidence` 全量 AST 扫描**：调用点**恰 1 处** `:6167-6168`（在 `finalize_trip._except_evidence_copy` 内），位置实参 `['rec','carrier_dir','out_dir']` + 关键字 `pre_freshness_snapshot=pre_freshness_snapshot`（`_review_probe_r3_out.txt:19-22`）。**不存在第二个未传参的调用点**。def 签名 `:4701-4704` 第 4 参 `pre_freshness_snapshot: dict | None = None`（`:23-24`），与设计 H03/H06（`B2B_DESIGN.md:664,667`、§4 #3/#6）一致。
- **`finalize_trip` 兼容性**：def `:6127-6137` 共 14 参，末参 `pre_freshness_snapshot` 带默认 `None`（9 个默认值）；调用点全文件**恰 1 处** `:7358-7367`（`main` 的 `finally` 内），5 位置实参 + 9 关键字（含 `pre_freshness_snapshot`）。本人按 CPython 传参规则做**静态绑定模拟**：无缺参、无重复绑定、无未知关键字 ⇒ **不会抛 TypeError**（`_review_probe_r3_out.txt:26-32`）。H05/H09（`B2B_DESIGN.md:666,670`）落地属实。
- **`main` 内生命周期（H07/H08/H09）**：`:6528` 预初始化 `_pre_freshness_snapshot: dict | None = None`（实读确认：预初始化在 `:6545` 的 `try:` 之前、五个早退均晚于此点，`:6526-6529` 原文含「try 之前预初始化」注释与 `budget = TripBudget(rec)` 先例行）→ `:6623-6624` 赋值 `make_pre_freshness_snapshot(carrier_dir / "except.txt")`（载体备份完成后、launch 前，`:6618-6621` 实读）→ `:7367` 传入 `finalize_trip`。三件齐备（`_review_probe_r3_out.txt:50-56`），与设计 E1 根治链（`B2B_DESIGN.md:60-64`）一致。测试套件 A1–A4 / E3（早退快照 None 不崩、生命周期）独立佐证（`_test_rerun_out.txt:6-14,36-38`）。

**小结：硬性规则 4（另一调用点未传参）、5（finalize_trip TypeError）均未触发。**

## 3 输出字段核对

按裁定二口径（`TASK.md:201-210`）：**7 个 FRESHNESS 字段须三路径全落盘；12 键 `info` 只在「正常路径」与「`src_missing` 分支」落盘即可；`copy_failed` 路径没有 `evidence_copy` 行符合设计**。

- **`_emit_f` 固定 7 个 `rec.add`，全部写 `FRESHNESS_GROUP`**（候选 `:4724-4753`；设计 `B2B_DESIGN.md:83`）：实数 7 处 `:4730/:4733/:4736/:4740/:4743/:4747/:4751`；其中 **4 键**由 `FRESHNESS_KEY_PREFIX` 拼出（`freshness_verdict/confidence/is_new/note`）、**3 键**同 group 独立名（`pre_snapshot_state/usable_as_crash_evidence/captured_at_iso`），与设计 §5 精确口径（`B2B_DESIGN.md:621`）一致；全文件 `rec.add(FRESHNESS_GROUP,...)` 共 8 处 = 7 处 `_emit_f` + 1 处 H08 `captured_at_iso_pre`（`:6625`）（`_review_probe_r3_out.txt:57-80`）。
- **三路径离线合成**（全内存 `FakePath`/`Recorder` stub，零磁盘写；仅对母本既有基础设施 `sha256_file`（母本 `:416-422`，非 H1–H9 改动、用内建 `open()` 读真盘）按 R2 先例做等价 stub，已在探针内注明）：
  - **正常路径**：7 个 F 键序 = `[freshness_verdict, freshness_confidence, freshness_is_new, freshness_note, pre_snapshot_state, usable_as_crash_evidence, captured_at_iso]`（与设计 `:597-603` 逐名一致）；`EXCEPT.evidence_copy` 1 行、value 为 **12 键 dict**（原 5 键 + `mtime_post/freshness_verdict/freshness_confidence/freshness_note/captured_at_iso/pre_snapshot_state/pre_freshness_snapshot`）；0 条 ERROR、不抛（`_review_probe_r3_out.txt:167-173`）。
  - **`src_missing` 分支**：7 个 F 落盘（stage=`src_missing`）；`evidence_copy` 1 行、value=`None`（设计 `:434-435` 与 `:605` `dict|None` 口径）；0 ERROR、不抛（`:174-177`）。
  - **`copy_failed` 分支**：7 个 F 落盘（stage=`copy_failed`，verdict=`post_read_error`/conf=`none`）；**3 条 ERROR** `freshness_copy_failed/freshness_copy_stage/freshness_copy_traceback`；无 `evidence_copy` 行；原异常（OSError）**重抛**（`:178-181`）——与设计 H04「先留痕再上抛、不许静默」（`B2B_DESIGN.md:81,130`）一致。
  - **汇总**：7F 三路径 = `[True,True,True]`；info 12 键 dict = `[正常=True, src_missing=False, copy_failed=False]`；`evidence_copy` 行落点 = `[有,有,无]`、次数 `[1,1,0]`（`:182-185`）——与裁定附录 `TASK.md:209-210` 登记的候选实测逐项吻合。
- **字段名逐个核对**：7 F + 12 info + `captured_at_iso_pre`（H08 `:6625`，第 8 个 F 字段，属 `B2B_DESIGN.md:604` 单独写入点）与设计 §5 表（`:574-619`）逐名一致；测试套件 D1/D2/D3 独立佐证（`_test_rerun_out.txt:28-34`）。

**小结：硬性规则 6（7 F 字段任一路径缺失）未触发。**

## 4 F/E 分离核对

- **退出码判据逐字未改**：候选唯一含 `no_new_exception` 的 `If` 判据 `:6214-6219`，与母本 `:5985-5990` **逐字相等 = True**（`_review_probe_r3_out.txt:34-38`）；判据整块（含子树）`freshness`（不分大小写）出现 **0 次**。
- **退出码相关函数体零 freshness**：`note_cleanup_failure`（`:403-408`）、`merge_cleanup_code`（`:411-425`）、`except_set_diff`（`:687-723`）、`run_guarded_steps`（`:4526-4553`）、`_main_wrapper`（`:7381-7444`）五函数体 `freshness` 计数全 **0**（`:39-48`）。
- **`main` 体内的 7 处 freshness 行**全部为 H07/H08/H09 的**数据传递**（`_pre_freshness_snapshot` 预初始化/赋值/传参 + H08 `captured_at_iso_pre` 落盘），不在判据块内（`:49-56`）——与设计 H07/H08/H09「只传数据、不碰判据」（`B2B_DESIGN.md:136`）一致。
- **F 结论恒不可作崩溃证据**：`_finish`（`:4628-4632`）每次硬编码 `usable_as_crash_evidence=False`；14 行矩阵 + 36 组穷举中 crash_ev 全 False（§1）；测试套件 F12 独立佐证（`_test_rerun_out.txt:60-62`）。
- **命名/group 隔离**：F 全部进 `FRESHNESS` group（8 处，见 §3）；E 侧 `EXCEPT.evidence_copy` 正常路径 value 仍为 dict 且原 5 键保留（12 键为扩键），group/key/source 未改名（设计 §6②，探针 `:168-172`）。设计已登记的 H01 内联注释不精确（`:218`「唯一判据恒在 :5985-5990」vs 母本 `:5944/:7075/:7130` 等另有收尾失败点）沿用 `B2B_DESIGN.md:639`（取舍 E）原登记，属 diff 内注释文字，非可执行语义，不构成阻断。

**小结：硬性规则 7（freshness_* 被退出码判据读取）未触发。** 限缩声明：以上为静态 AST + 行文本/字节级逐字比对 + 隔离函数级实跑的结构性结论；**整趟运行时退出码行为未做真机复现**（见「未验」）。

## 5 范围限制核对

- **全量 diff（difflib，行文本口径）**：母本 7291 行 vs 候选 7533 行，变更 opcode 块 12、`+`行 **255**、`-`行 **13**；设计 §4 九个 ```diff 块 `+`255/`-`13；**候选±行多重集与设计±行多重集完全相等**（候选独有 0 / 设计独有 0）（`_review_probe_r3_out.txt:83-97`）。
- **逐 hunk 归因**：12 个变更块按母本区间全部归入设计 hunk 头自解析的 9 个母本区间（212-217 / 4458-4463 / 4558-4565 / 4572-4591 / 5906-5912 / 5936-5942 / 6294-6299 / 6386-6391 / 7122-7128），**未归入块数 = 0**（`:98-121`）——H03/H04 各被 difflib 拆成多个相邻 opcode（`:109-115`），属对齐粒度，不是设计外改动。
- **字节级 keepends 口径**：与行文本口径完全一致（12 块 / +255 / -13，`:122-123`）——**N-1 不复发**（R2 `:84-88` 的整篇替换已消失）。
- **决定性重建（两条独立路径）**：母本 + 设计 §4 九 hunk == 候选（逐字节）；母本 + `CANDIDATE_LF.diff` == 候选（逐字节）（`:124-126`）。⇒ **候选相对母本的每一字节差异都可归属到 H1–H9**，无夹带。
- **九个锚点落点实读**（候选行号）：H01 `:217-228`（5 常量）、H02 `:4476-4478`（`RESTORE.backup_mtime_pre:{name}`，`bak[name]` 三键未改，`:4475`/`:4480` 原样）、H03 `:4580-4698` + def `:4701-4704`、H04 `:4716-4826`、H05 `:6137`、H06 `:6167-6168`、H07 `:6528`、H08 `:6623-6629`、H09 `:7367`。门禁 [9] 9/9 锚点定位（`_gate_rerun_out.txt`）。
- **新增顶层函数溯源**：候选新增 `make_pre_freshness_snapshot` / `classify_except_freshness`（含嵌套 `_finish`/`_emit_f`）全部出自设计 hunk3/hunk4 的 `+` 行（多重集相等 + 逐字节重建已证），与 `N1_BINDING.md:82` 复核结论一致，**非夹带**。

**小结：硬性规则 8（diff 超出 H1–H9）未触发——N-1 已关闭且本轮独立复核。**

---

## 阻断项

**无。** 九条硬性阻断规则逐条核对结果：

| # | 硬性规则 | 结果 | 证据 |
|:--|:--|:--|:--|
| 1 | 14 状态有缺分支 | 未触发 | §1：14/14 match + 13 `_finish` 调用点映射 |
| 2 | unknown 给 high | 未触发 | §1：36 组穷举零泄漏；high 仅 `:4667/:4682/:4691` |
| 3 | 状态值层面不可分 | 未触发 | §1：三 verdict 两两不等；absent_confirmed ≠ unknown |
| 4 | 另有调用点未传 `pre_freshness_snapshot` | 未触发 | §2：调用点全文件恰 1 处且已传 |
| 5 | `finalize_trip` 调用点 TypeError | 未触发 | §2：静态绑定模拟 OK |
| 6 | 7 F 字段任一路径缺失 | 未触发 | §3：`[True,True,True]` |
| 7 | `freshness_*` 进退出码判据 | 未触发 | §4：判据块逐字未改且零 freshness |
| 8 | diff 超出 H1–H9 | 未触发 | §5：逐字节重建 == 候选；CR=0 双方 |
| 9 | 亲自重跑的测试有 FAIL | 未触发 | `PASS=29 FAIL=0`（`_test_rerun_out.txt`）；门禁 9/9 仅记档 1 |

## 未验

- **真机 / 运行时整趟**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 taskkill、未读活进程内存、未写采样代码（铁律 1/2）。全部结论为静态 + 隔离函数级 + 测试套件级的结构性结论。
- **运行时退出码实测**：F/E 分离结论（§4）来自静态 AST + 逐字比对 + 函数级实跑，非整趟运行实测；`B2B_DESIGN.md:652` 亦自认静态 ≠ 运行时。
- **`qc151_fields.json` 真实磁盘落盘**：本轮三路径为内存 Recorder stub 合成，`rec.dump` 写盘链未做磁盘复现。
- **P7a/P7b（`finally` 内先于 `:7117` 失败时 F 是否落盘）**：结构性推断沿用设计 §3 P7a/P7b（「无 F 字段落盘、异常外传」），本轮未单独构造 finally 失败场景实测。
- **`make_pre_freshness_snapshot` 的 `error` 分支实跑**：本轮探针只实跑了 present / absent_confirmed 两态（error 态需使 `exists()`/`stat()` 抛异常的真实输入）；该分支由测试套件 B1（目录输入 → state=error）独立覆盖（`_test_rerun_out.txt:14`），本人未另跑。
- **camelCase ↔ snake_case 正式字段映射全库穷尽**：未做全库扫描，沿用 R2 `:108` 的登记原状（有界扫描「无」非全库否定）。
- **R2 遗留引用精度瑕疵 1/2**（R1 判定书 `:26`/`:140` 的行号与清单呈现）：属上一轮判定书的呈现卫生事项，本轮未复核原件，沿用 R2 `:105-106` 登记原状。
- **门禁 [6][7][8] 读的 report/review 属旧交付件**：`TESTS_REPORT.md` / `review/CANDIDATE_REVIEW.md` 无 LF 版重物化件，本轮门禁副本仍指向 `lead/b2b_candidate_20261106/` 原件（见下方副本说明）；其声明内容属实性未逐字复核（档 2 只记「声明为 true」）。
- **D-25 第 6 步隔离副本离线集成**：未做。**本判定书不构成「候选可应用到母本」**（`TASK.md:219`、`N1_BINDING.md:110`）。
- **STATE_MATRIX #1 condition 措辞偏差**（§1 末条）：保持「文档精度事项」登记，未修改矩阵（只读域）。

## 证据等级说明

严格区分三档（承 `TASK.md:30-45`、D-28），不混用：

| 档 | 含义 | 本判定书里对应什么 | 能否作 verdict 依据 |
|:--|:--|:--|:--|
| **档 1 · 机械门禁通过** | `check_candidate.py` 9/9 PASS | 本人重跑门禁副本 `ALL 9 GATES PASSED! EXIT=0`（`_gate_rerun_out.txt`） | **否**。只记「门禁通过」 |
| **档 2 · 报告字段为 true** | `CANDIDATE_REVIEW.md` 等五字段为 true | 仅门禁 [8] 确认字面量存在；内容属实性未逐字复核 | **否**。只记「报告字段声明为 true」 |
| **档 3 · 语义已独立复核** | 本人逐项亲自实跑 / 实读「文件:行」 | §0–§5 全部：五件指纹、双决定性逐字节重建、14/14 矩阵 exec、36 组穷举、三路径合成、全量 AST 调用点 / F/E、`_emit_f` 计数、测试/门禁本人重跑 | **是**。本判定书属此档；`verdict: PASS` 由档 3 推出，档 1/2 仅作旁证 |

- **本判定书属于档 3（语义已独立复核）**，且是**独立复审**：所有结论出自本人本次实跑，未转抄 R1/R2 或绑定记录的数字（指纹、diff、矩阵、三路径均重算）。
- **未因门禁 9/9 判 PASS**：门禁只验格式与锚点存在；PASS 由 §1–§5 的语义核验推出。
- **`verdict: PASS` 的准确含义** = 候选**语义上**实现了批准设计（含裁定附录修正口径）。它**不等于**：可应用到母本（D-25 第 6 步未做）、运行时已验证（零真机）、集成已演练。此边界对下游引用有约束力。
- **执行者 ≠ 核验者**：本判定书撰写人（R3 复审员）未签任何独立复核；按 `TASK.md:157-165` 惯例，本件仍需另起新上下文的独立复核（`checkedEveryRow` / `noOverreach` / `blockedCount`），该复核**尚未发生**，不在本件声明范围内。

## 附 1 · 实跑命令清单（均为本次会话亲自执行，cwd = `D:/Project/ra2-campaign-forge`）

| 命令 | 输出文件 | 关键结论 | 退出码 |
|:--|:--|:--|--:|
| `python -I -B -X utf8 lead/b2b_candidate_review3_20261107/_review_probe_r3.py > lead/b2b_candidate_review3_20261107/_review_probe_r3_out.txt 2>&1` | `_review_probe_r3_out.txt` | `PASS=55 FAIL=0` + `PROBE_DONE`（五件指纹 / AST 调用点 / 退出码 / diff 归因 / `_emit_f` 计数 / 14 矩阵 / 三态 / 三路径） | 0 |
| `python -I -B -X utf8 lead/b2b_candidate_review3_20261107/_test_candidate_lf.py > lead/b2b_candidate_review3_20261107/_test_rerun_out.txt 2>&1` | `_test_rerun_out.txt` | `Ran 29 tests` / `OK` / `PASS=29 FAIL=0` | 0 |
| `python -I -B -X utf8 lead/b2b_candidate_review3_20261107/_check_candidate_r3.py > lead/b2b_candidate_review3_20261107/_gate_rerun_out.txt 2>&1` | `_gate_rerun_out.txt` | 9/9 PASS（**仅档 1**） | 0 |

## 附 2 · 测试与门禁副本的路径改绑声明（只改路径，逻辑零改动）

原脚本均指向旧候选 `lead/b2b_candidate_20261106/qc151_trip.candidate.py`（R2 绑定对象，已被 N-1 绑定替换），按任务规则不改原件，副本置于本写域：

1. **`_test_candidate_lf.py`** ← `lead/b2b_candidate_20261106/tests/test_candidate.py` 逐字节复制，**唯一改动 = 第 37 行**：
   `CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_candidate_20261106/qc151_trip.candidate.py"` → `PROJECT_ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"`。
   （`diff` 实证：仅 `37c37` 一处，见本判定书撰写会话的 diff 输出。）
2. **`_check_candidate_r3.py`** ← `lead/b2b_candidate_20261106/check_candidate.py` 逐字节复制，**全部改动均为路径解析**（`diff` 实证）：`56-60`（BASE 指向 LF 目录）、`60-64`（4 个 `*_REL` 常量：候选/diff→LF 目录，测试副本/测试输出→review3，report/review→原交付件位置）、`70-75`（DELIVERY_FILES 改为 `ROOT / *_REL` 显式路径）、`79`（TESTS_DIR→原 tests 目录，扫描原测试脚本）、`139`（cand_path）、`192`（test_out_path，指向本人**本轮新鲜**重跑输出而非旧 `_test_out.txt`）、`213`（report_path）、`225`（review_path）。九项检查的**判定逻辑一字未改**。
3. 被审候选、原测试、原门禁、设计、母本、R2 件、绑定件：本轮**零改动**（指纹见头部表；母本指纹与开工前一致）。

## 附 3 · 探针诚实记录

- 首版探针（含 `exec(compile(...))` 的 AST 提取方案）被 Mimosa 安全钩子拦截写入（与 R2 `:181` 同因），改用任务书许可的 **importlib + DPI patch** 隔离加载方案后落盘成功；结论只取实跑输出。
- 探针迭代 3 次：前两次的 3 个 FAIL 均为**探针自身缺陷**（① 键名解析漏剥单引号；② 母本基础设施 `sha256_file` 用内建 `open()` 读内存 FakeFile 抛 FileNotFoundError，发生在正常路径尾部的载体快照循环——非候选 H1–H9 代码；③ info2 判据把「src_missing 落一行 value=None」误写成「落 12 键 dict」），修正后终版 55 PASS / 0 FAIL。候选、测试、门禁在迭代中零改动。
