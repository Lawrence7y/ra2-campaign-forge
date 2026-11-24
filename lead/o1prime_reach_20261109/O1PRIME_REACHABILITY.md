# O1PRIME_REACHABILITY.md — O1′ 子格可达性与影响报告

任务写域：lead/o1prime_reach_20261109/。零真机（未启动任何游戏进程、未读活进程内存）、零采样代码（无 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析）。本报告只查 **可达性与影响**，不判矩阵该不该改（该裁决已由 lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md 处理）。

---

## 1 目的与边界

**目的**：核实 A/B 裁决登记的 O1′ 缺陷——「STATE_MATRIX.json 第 6 行文本把 absent_confirmed × exists=True × read_error 子格（即 O1′ 输入格）字面错盖为 new_first_appearance / high」——在真实运行流中 (i) 输入格是否真的能出现，(ii) 若出现是否会把环境故障虚报成 high 置信并造成下游误处置。

**边界（如实声明）**：
- 本报告**不下**「该不该改矩阵」的结论；只对 A/B 裁决对 O1′ 的「活性 / 理论」归类做实证评估。
- 零真机约束：真机趟流（launch 游戏本体→崩溃→finalize）**未做端到端实跑**；本文所有实跑都是把被核件的**真函数**（make_pre_freshness_snapshot、copy_post_except_evidence、classify_except_freshness、真 Recorder）在本任务写域 _o1_tmp / _o1v_tmp 内、以真实文件系统故障输入驱动。该边界在 §3 与 §5 未验项中如实区分。
- 触发条件评级为概率性工程判断（引用到的只有代码事实与实跑结果）；「日常概率低」是定性结论，未做量化统计（未验）。

---

## 2 上游指纹（十件）与两条路径读解

### 2.1 十件指纹（本会话实跑复核）

实跑命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\o1prime_reach_20261109\_o1_fp.py`（hashlib 实算，与编排方基线逐件比对）。输出（_o1_fp_out.txt，末行 ALL_MATCH）：

| 文件 | sha256 | 字节数 | 结果 |
|:--|:--|:--|:--|
| lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py | ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 | 412759 | MATCH |
| lead/b2b_design_20261106/STATE_MATRIX.json | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3558 | MATCH |
| lead/b2b_design_20261106/B2B_DESIGN.md | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66735 | MATCH |
| lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md | 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31 | 36851 | MATCH |
| lead/matrix_ab_ruling_20261109/_ab_RULING_MATRIX_AB_20261109.md | a7211b32b1f8b06e9ec34da06257ab9e86b7d0259d9ef8d9d3697a8d79096935 | 25984 | MATCH |
| lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md | 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8 | 29818 | MATCH |
| lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md | c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801 | 28897 | MATCH |
| out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py（母本） | 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 | 399508 | MATCH |
| lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | MATCH |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | MATCH |

复核件同基线：_o1v_fp_out.txt 末行 ALL_MATCH（独立脚本 _o1v_fp.py）。十件全 MATCH，下文所有「文件：行」引用均基于这些字节。

### 2.2 路径读解一：copy_post_except_evidence 的 write_bytes 控制流（实读被核件）

lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py（下称被核件）：

- :4720-4722 `post_observed` 初始化为 `{"exists": None, "size": None, "sha256": None, "mtime_post": None, "captured_at_iso": None, "read_error": None}`。
- :4756-4764 源件不存在分支：exists=False，早退（与本格无关——本格要求 exists=True）。
- **:4766-4769** 读源件成功：`blob = src.read_bytes()` → `st = src.stat()` → `h = hashlib.sha256(blob).hexdigest()` → **:4769** `post_observed.update({"exists": True, "size": len(blob), "sha256": h, "mtime_post": float(st.st_mtime)})`。**exists 在此被置 True**。
- :4771 `dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"`（微秒时间戳，名字全新唯一）。
- **:4772 `dst.write_bytes(blob)`** ← 失败注入点。
- :4773 `except Exception as exc:` → **:4777-4785** 三条 `rec.add("ERROR", …)`：freshness_copy_failed / freshness_copy_stage="read_bytes/stat/write_bytes" / freshness_copy_traceback。
- **:4786 `post_observed["read_error"] = f"{type(exc).__name__}: {exc}"`** ← **只新增 read_error 键，不触 exists**（exists 保持 :4769 置入的 True——该点经复核探针实证，见 §3.3）。
- :4788-4789 `_emit_f(classify_except_freshness(pre_freshness_snapshot, post_observed), "copy_failed")` → **:4790 `raise`** 原样上抛。
- 上抛后：run_guarded_steps :4526-4553（out_dir 缺省 WORKDIR :4537-4538；逐项 except 记账 :4540-4545；把每个失败落盘 finalize_errors.txt :4547-4552；:4553 `raise errors[0][1]` 原样重抛）；再由 write_finalize_error :4556-4577 落 error.txt（:4571-4577）。
- 真实流调用链：finalize 收尾项 `_except_evidence_copy`（:6166-6168）调 copy_post_except_evidence，pre 快照来自 :6623-6624 `make_pre_freshness_snapshot(carrier_dir / "except.txt")`（backup 后、launch 前拍）。

### 2.3 路径读解二：classify_except_freshness 分支序（实读被核件）

classify_except_freshness（:4616-4698）：
- 初始四元组恒 `usable_as_crash_evidence=False`（:4624-4626），`_finish` 再次强制 False（:4628-4632）——任何 verdict 都不给崩溃证据资格（docstring :4621「恒 False」；常量区注释 :217-220「F 结论恒 usable_as_crash_evidence=False（:677 口径）」）。
- **:4643-4646 read_error 是第一个判定分支**（注释 :4642「★ N1：错误独立出口，优先于一切状态折叠」）：`if post.get("read_error"): return _finish("post_read_error", "none", None, …)` —— 先于 unknown 分支（:4648）、先于 exists 分支（:4656-4664）、先于 absent_confirmed 的 NFA/high 分支（:4666-4669）。取真值判断（truthiness），空串不触发（该边界的实流可达性见 §5 未验项）。
- 因此 O1′ 格（pre=absent_confirmed × exists=True × read_error 非空）的**运行期真实返回恒为四元组 (post_read_error, none, None, usable_as_crash_evidence=False)**，:4666-4669 的 new_first_appearance/high 分支根本走不到。

### 2.4 矩阵 :6 的声称（实读 STATE_MATRIX.json）

lead/b2b_design_20261106/STATE_MATRIX.json 共 14 行数据行：
- **第 5 行**（post_read_error 行）：`{"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口",…}` —— preState **只写 "present"**，不覆盖 absent_confirmed/unknown pre 态。
- **第 6 行**（NFA 行）：`{"state":"absent_confirmed","preState":"absent_confirmed","condition":"跑前确认无件 + 跑后在场（存在性硬证）⇒ 本趟新出现；是否新崩溃仍只由集合差裁定","verdict":"new_first_appearance","confidence":"high","usableAsCrashEvidence":false}` —— condition **无任何 read_error 例外句**。
- 故按「preState + condition」字面键匹配（耦合件 :67 口径），O1′ 格的唯一 claimant 是第 6 行 ⇒ **矩阵文本声称 new_first_appearance/high，实码给 post_read_error/none**。冲突为真，但它是**矩阵文本层 vs 实码**的错配（claimant 错配），不是运行期谎报——与裁决 :55 原文自洽：「O1′ 的『虚报 high』指**矩阵格声称** high，非运行时输出 high」。

---

## 3 实证方法与实跑输出

**方法总述**（方法 A+B 为撰写人，C+A′ 为复核人独立异法，四者结论一致）：静态 import 被核模块（importlib 标准导入；import 安全性先由 _o1_astcheck.py 静态 AST 证明——顶层仅常量/定义/__main__ 守卫，副作用调用仅 :182 `SetProcessDPIAware()` 与 :3337 纯计算两处良性调用，_o1_astcheck_out.txt）；在被核模块上调用**真函数**（真 make_pre_freshness_snapshot 产出 pre 快照 → 模拟本趟在载体目录写出 except.txt → copy_post_except_evidence 真实执行读源+写 dst），写失败注入全部落在唯一写域 _o1_tmp / _o1v_tmp；spy 包装 classify 只捕获实参后转调原函数，故 post_observed 与返回值均为**实流产物而非手工构造**。icacls 拒写事毕 `/remove:d` 还原。

### 3.1 撰写人实跑（_o1_harness2.py → _o1_harness2_out.txt，python 3.12.10 / Windows 11 10.0.26200）

| CASE | 构造 | 实跑结果（摘自输出原文） |
|:--|:--|:--|
| success_control | out_dir 正常（合法对照） | copy 成功 ⇒ `{"verdict": "new_first_appearance", "confidence": "high", "is_new": true, … "usable_as_crash_evidence": false, "pre_snapshot_state": "absent_confirmed"}`（:6 行**合法**形态，证明正常流确实产出 high——错配不是常态误报） |
| **B1** out_dir 父目录缺失 | 先建后删真实目录 | `raised = FileNotFoundError: [Errno 2] No such file or directory: '…_o1_tmp\vanished_out_B1_outdir_missing\except_post_20261109T034020170844.txt'`；classify **实收** post_observed = `{exists: True, size: 56, sha256: 14f8168b…, mtime_post: 1794166820.1698177, captured_at_iso: 2026-11-09T03:40:20+08:00, read_error: FileNotFoundError…}`；classify **实际返回** = `{"verdict": "post_read_error", "confidence": "none", "is_new": null, …, "usable_as_crash_evidence": false, "pre_snapshot_state": "absent_confirmed"}`；rec 留痕含 `[ERROR] freshness_copy_failed`、`[FRESHNESS] freshness_verdict = post_read_error`、`[FRESHNESS] usable_as_crash_evidence = False` |
| **B2** out_dir 为普通文件 | 真实文件占位目录位 | `raised = FileNotFoundError: [Errno 2] …plainfile_B2_outdir_is_file.txt\except_post_…txt`；classify 实收 `exists=True` + read_error=FileNotFoundError ⇒ 返回 post_read_error/none/None/False |
| B3 超长路径（~370 字符） | 深层长目录链 | **写入成功**（本机长路径已放行）⇒ new_first_appearance/high（合法形态）。**该失败形态本机未复现，如实记（未验）** |
| **B4** ACL 拒写 | icacls deny *S-1-1-0:(WD)（事毕 /remove:d 还原，[B4 前置] icacls deny rc = 0） | `raised = PermissionError: [Errno 13] Permission denied: '…denied_B4_acl_denied\except_post_20261109T034020287723.txt'`；classify 实收 `exists=True` + read_error=PermissionError ⇒ 返回 post_read_error/none/None/False |
| C 构造字典对照 | 四组构造 post_observed 直喂真 classify | `exists=True × read_error × pre=absent_confirmed` ⇒ post_read_error/none；`× pre=present` ⇒ 同；`exists=None × read_error`（O1 主子格）⇒ 同；`exists=True 无 read_error × absent_confirmed` ⇒ new_first_appearance/high |

**traceback 绑定（_o1_dump_rows.py → _o1_dump_rows_out.txt，B1 与 B4 同形）**：

```
Traceback (most recent call last):
  File "D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py", line 4772, in copy_post_except_evidence
    dst.write_bytes(blob)
  File "…\pathlib.py", line 1036, in write_bytes
    with self.open(mode='wb') as f:
         ^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '…\dump_vanished_out\except_post_20261109T034202567659.txt'
```

即异常逐帧绑定被核件 **:4772 dst.write_bytes(blob)** 本体——不是 harness 自身代码抛的。全量 rows+traceback 落盘 _o1_rows_dump.json。

### 3.2 复核人实跑（_o1v_harness.py → _o1v_harness_out.txt）

- 方法 C 五组构造字典直喂真 classify：C1 O1′ 格 ⇒ post_read_error/none/None/False；C2 合法对照 ⇒ new_first_appearance/high；C3 pre=unknown × read_error ⇒ post_read_error（实证分支序）；C4 pre=present × read_error ⇒ 同；**C5 空串 read_error ⇒ 落 new_first_appearance/high（truthiness 边界；实流不可达，因 :4786 恒写非空 f-string——见 §5 未验项）**。
- 方法 A′（撰写人未用过的两种真实失败根因）：A′-1 out_dir 含非法字符 `?` ⇒ `OSError: [Errno 22] Invalid argument`；A′-2 out_dir 本身为普通文件 ⇒ `FileNotFoundError: [Errno 2]`。均走真序列（真 make_pre_freshness_snapshot 得 pre=absent_confirmed → 载体写出 → copy_post 读源成功 → dst 写失败），`traceback frames bound to candidate = [('qc151_trip.candidate_lf.py', 4772, 'copy_post_except_evidence')]`，F = (post_read_error, none, None, False)，与撰写人 B1/B2/B4 一致。

### 3.3 关键分歧点实证：write_bytes 失败后 exists 未被重置

复核探针 spy 捕获 :4788 classify **实收**的 post_observed（_o1v_harness_out.txt 原文）：

```
spy.post_observed_at_classify = {"pre_state": "absent_confirmed", "post": {"exists": true, "size": 274, …, "read_error": "OSError: [Errno 22] Invalid argument: …"}}
[A' badchar] >>> KEY POINT4: post_observed['exists'] after write_bytes failure = True (None reset would show None)
```

两种真实失败下均见 `exists: true` 与 `read_error` 并存（代码层对应：:4769 先置 True、:4773-4790 except 块只在 :4786 新增 read_error 键）。**O1′ 输入格（exists=True × read_error）真实存在**——若不存在，本格会落入 exists=None 的 O1 主子格（孤儿「不答」），错配性质完全不同。此点实证落定。

---

## 4 触发条件现实性评估与「虚报 high」的实际后果

### 4.1 dst 指向何处、写入量

- dst = `out_dir/except_post_<微秒时间戳>.txt`（:4771）；out_dir = WORKDIR（finalize 缺省 :6160-6161）；WORKDIR 来源 = `--out-dir` / 环境变量 QC151_OUT_DIR / DEFAULT_OUT_DIR 三选一（:6423-6431，模块级 :199/:200/:207），main 早期 `WORKDIR.mkdir(parents=True, exist_ok=True)`（:6450，且有批准域校验 :6433-6449）。⇒ **父目录在正常流中必然刚由同进程建好，目标名微秒级全新唯一**。
- 写入量 = 载体 except.txt 大小，母本量级 26515 字节（:244-245 `EXCEPT_MASTER_SIZE = 26515`），即约几十 KB。

### 4.2 六类失败条件逐项评级（评级为工程判断；每条引用的代码事实均已实读）

| 失败条件 | 评级 | 依据 |
|:--|:--|:--|
| 磁盘满 | 【罕见】 | 自身仅 ~26KB；且磁盘满时更早的写帧 / manifest / Recorder 落盘已先失败，轮不到 :4772 |
| 权限不足 / AV 拦截 | 【罕见，环境级】 | out_dir 是同进程刚建的运行期写域，正常权限模型下必然可写；仅企业端点 AV/勒索防护拦项目目录写入可能命中。**该形态 B4 已实证**——即便发生，分类仍正确（post_read_error/none） |
| 目标被占用 | 【近乎不可能】 | 目标名含微秒时间戳、全新唯一（:4771），不存在被占用的常态 |
| 路径过长 | 【罕见】 | 仅当操作者传极端 --out-dir；本机实测长路径放行（B3 ~370 字符写入成功）；且 WORKDIR 启动即建（:6450），过长在趟前已败 |
| 只读介质 | 【近乎不可能】 | 运行期写域不可能落在只读介质上完成前面所有步骤 |
| out_dir 中途被删 / 被换成文件 | 【近乎不可能】 | 需外部并发干扰同进程刚建的目录；B1/B2 已实证即便发生，分类仍正确 |

**总评**：无任何由 trip 自身逻辑产生的触发路径（trip 逻辑自己只会让 dst 可写）；全部条件为环境级故障，日常概率低（定性；未做量化，未验）。**一旦发生是响亮失败**：ERROR×3（:4777-4785）→ raise（:4790）→ finalize_errors.txt 落盘并原样重抛（:4547-4553）→ error.txt（:4571-4577），无成功假象。

### 4.3 虚报 high 的实际后果（下游是否因此改变处置）

- **矩阵文本若被当真**：会把一次证据副本的环境失败读成「跑前确认无件 + 跑后在场（存在性硬证）⇒ 本趟新出现·高置信」——环境故障被误读成崩溃征兆。这是错配的**名义**后果。
- **实测后果链三层兜死**（每层均有实证或实读）：
  1. **运行期无任何逻辑消费 confidence/new_first_appearance 做分支**。本会话实跑 `grep -c "freshness_confidence\|freshness_verdict"`（被核件）= **4**，且全部是 F 字段组装进 info/rec（:4798-4806、:4730-4753），E/退出码口径独立（:217-220 门禁注释、docstring :4619-4620）；实跑 `grep -c "STATE_MATRIX"`（被核件）= **0**——候选件根本不读矩阵。
  2. **该格 usable_as_crash_evidence 恒 False**：classify :4624-4626 初始即 False、_finish :4628-4632 再次强制，落盘 note 明写「★★ 恒 False：F 结论不得作为本趟崩溃证据（:677）」（:4747-4750）。B1/B2/B4/A′-1/A′-2/C1-C5 全部实跑返回 usable=False；即便合法 high 对照（success_control/C2）也是 False。运行期账本四元组 = (post_read_error, none, None, False)，**high 被 confidence=none + usable=False 双重兜住**。
  3. **同一账本并存 freshness_copy_failed ERROR 行 + finalize_errors.txt**：若有人按矩阵 :6 文本把该格读成 high，账内 ERROR 留痕与之自相矛盾，冲突自明、易被审计识破。
- **下游 grep（本会话实跑）**：`grep -rl --include="*.py" "STATE_MATRIX" lead/`（排除本写域）= **34 件**；过滤掉审计/探针/测试/指纹目录后残余 11 件全为 `_fp`/`_cv`/`_rw`/`_pv` 类指纹与结构核对脚本（ledger_appendix_20261108、n4_yi_final_20261108、v2_precision_fix_20261108、w2_samecause_20261109 下）。freshness_confidence/verdict 的其余下游是测试断言——b2b_candidate_20261106/tests/test_candidate.py:244-263 `test_b4_post_copy_exception_records_error_and_reraises` **恰断言 copy 写异常 ⇒ freshness_verdict=post_read_error、freshness_confidence=none**（实读确认），即设计意图、实码、旧测试三者一致，矩阵 :6 措辞滞后。计数口径残差（撰写人 33 vs 复核人/本会话 34）见 §5。

---

## 5 复核回件 + 结论 + 声明与未验项

### 5.1 复核回件

复核 verdict：**confirmed**（七步复核全过，无推翻项；复核回件原文见工作流【复核】栏，产物 _o1v_fp.py/.txt、_o1v_astcheck.py/.txt、_o1v_harness.py/.txt、_o1v_tmp/ 均在本写域）。复核人独立重算被核件指纹、逐行核对全部码径引用、以异法（C+A′）复现实证、并以探针捕获 classify 实参落定 exists 未重置分歧点——与本报告 §2-§4 全部一致。

被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759

（绑定对象 = lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py；本会话实跑 _o1_fp.py 重算同值。）

### 5.2 结论：理论错配（矩阵/文档文本层），严重度 low

- **输入格实流可达——已实证，非码序推理**：三种撰写人失败形态（B1 父目录缺失 FileNotFoundError [Errno 2]、B2 父为普通文件 FileNotFoundError、B4 ACL 拒写 PermissionError [Errno 13]）+ 两种复核人新根因（A′-1 非法字符 OSError [Errno 22]、A′-2 out_dir 为文件）共五种真实 write_bytes 失败，均以被核件真函数触发、traceback 逐帧绑定被核件 ：4772，post_observed 实流呈现 exists=True × read_error 并存（_o1v_harness_out.txt KEY POINT4）。裁决的码序链 ：4769→:4772→:4786 正确。
- **但「虚报 high」不出现在运行期**：真 classify 对该格恒回 (post_read_error, none, None, usable_as_crash_evidence=False)——五种真实失败 + 四组构造字典 + 复核五组全部同值；read_error 是 classify 第一分支（:4643-4646），:6 行的 NFA/high 分支（:4666-4669）对该格不可达。运行期**零错误输出**。
- **按本任务定义（真实流出现且造成后果）**：O1′ 归**理论错配**——触发条件全部环境级罕见、无 trip 自身逻辑路径、发生时趟响亮失败且账内 ERROR 与矩阵文本自相矛盾、运行期无分支消费该四元组、usable 恒 False。「活性错配」标签（如裁决 ：60 对 W2 的用法——错的是 verdict 标签且有机器可读消费场景）不适用于 O1′：O1′ 的错不在实码任何输出，只在矩阵文档对同一输入的预期标签（裁决 ：55 原句「错的只是矩阵文档对同一输入的预期标签」）。
- **对 A/B 裁决分类的评估**：裁决把 O1′ 列为三处缺陷中「后果最重的一格」（:61）且 STRICT 下残留 1 格 MISLABEL（:89）——就**输入格可达**而言，本实证支持该登记（且把裁决 ：243 自认的「实际文件系统故障形态未验」在零真机约束内补上）；但就**造成后果**而言，实测后果被 confidence=none + usable=False + 无消费方 + 账内 ERROR 自明四层兜死，high 只存在于矩阵 ：6 的文本层。裁决 ：55 本身已澄清「虚报 high 指矩阵格声称、非运行时输出」，与本实证一致，无活性/理论错标。**本报告不判矩阵该不该改**。

### 5.3 未改任何文件声明

本任务（撰写+复核+交付全程）**未修改、未追加、未覆盖**任何被核件/母本/两件台账/只读目录内的文件；所有写入仅发生在唯一写域 lead/o1prime_reach_20261109/（撰写阶段 _o1_*、复核阶段 _o1v_*、本文件）。B4 的 icacls deny 已以 `/remove:d` 还原（_o1_harness2_out.txt `CLEANUP icacls remove-deny rc = 0`）。**未 commit、未 push**。零真机、零采样。

### 5.4 未验项（如实登记，不补造）

1. **B3 超长路径失败形态未复现**：本机长路径已放行，~370 字符 dst 写入成功（_o1_harness2_out.txt B3）。该形态下 write_bytes 是否失败、失败后分类是否仍正确，本机未验。
2. **真机端到端实流未跑**（零真机约束）：make_pre_freshness_snapshot → copy_post_except_evidence 的实流调用链中，两函数本体与真实故障输入已实跑，但「真实趟内 finalize 现场调到 _except_evidence_copy 并遇环境故障」未做端到端复现；:6166-6168 调用点为实读非实跑。
3. **C5 truthiness 边界实流不可达性为推理+复核实证，非撰写人实跑**：classify 对 read_error 取真值（:4643），空串会落 new_first_appearance/high（_o1v_harness_out.txt C5 行）——但 :4786 恒写非空 f-string（`f"{type(exc).__name__}: {exc}"`，类型名不可能为空），实流不可达；撰写人未单独实跑此组。
4. **T1/T2/T5 门禁未跑**（沿裁决 ：240 如实登记；本任务亦未跑）。
5. **触发条件概率未量化**：§4.2 评级为定性工程判断。
6. **计数口径残差不翻案**：读矩阵的 lead/*.py 计数撰写人报 33、复核人与本会话 grep 实跑均得 34（口径差），两数下结论不变——全为审计/探针/测试/指纹脚本，候选件 0 引用矩阵（grep -c=0，本会话实跑）。
7. **AST 顶层调用计数口径**：撰写人摘要「两处良性调用」为副作用口径（:182 SetProcessDPIAware、:3337 纯计算）；复核人全量扫描 12 处顶层调用全良性（含 __main__ 守卫内 ：7533 `sys.exit(_entry())`，import 不执行）。两口径均支持「import 被核件安全」。
