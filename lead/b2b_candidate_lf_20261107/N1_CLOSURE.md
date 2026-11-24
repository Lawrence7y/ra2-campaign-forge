# N1_CLOSURE.md — N-1 关闭说明（R2 关闭路径 2：候选按母本 LF 重新物化）

- 撰写角色：说明撰写员（工作流子代理）。本件唯一写域 = 本文件；本件撰写者未参与新候选物化（铁律 8：执行者≠核验者）。
- 日期：2026-11-07。零真机、零采样代码（铁律 1、2）；未 commit、未 push（铁律 4）。
- 本件所有指纹与字节数均为本会话 `python -I -X utf8`（绝对路径，hashlib）实跑实算（铁律 5、6），不是转抄值；引证一律「文件:行」或「命令+输出」。
- 本件是 N-1 的**关闭记录**，不是通过判定书；越界声明见 §6。

---

## 1. 问题

**N-1 是什么**：R2 语义审查登记的新阻断项——候选整篇行尾被从母本 LF 改为 CRLF，是设计 §4 九个 hunk 从未声明、且落在 H1–H9 范围之外的字节级改动（`lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md:119-126`）。R2 实测：母本 `CRLF=0 / LF=7291`，候选 `CRLF=7533 / LF=7533`（`CANDIDATE_SEMANTIC_REVIEW_R2.md:122`，对应其 `_r2_part1_out.txt:8-9`）；母本第 1 行不在任何 hunk 区间内，行尾仍由 `b'3\n'` 变 `b'\r\n'`（`CANDIDATE_SEMANTIC_REVIEW_R2.md:123`）。本会话独立复算同值（§3 实跑输出）。

**R2 判了什么**：触发硬性规则「diff 有超出 H1–H9 的改动 ⇒ verdict 必须 BLOCKED」（`CANDIDATE_SEMANTIC_REVIEW_R2.md:125`，其内引 `TASK.md:151`），`verdict: BLOCKED`，登记阻断项 N-1，给出三条关闭路径（`CANDIDATE_SEMANTIC_REVIEW_R2.md:127-130`）；关闭前维持 BLOCKED（`CANDIDATE_SEMANTIC_REVIEW_R2.md:131`）。R2 同时如实两面：这是行尾字节转换、非夹带代码，ast.parse 仍成功、Python 语义层等价，但规则无「仅行尾不计」豁免（`CANDIDATE_SEMANTIC_REVIEW_R2.md:126`）。

**根因在哪一行**：`D:/Project/ra2-campaign-forge/lead/b2b_candidate_20261106/_implement_candidate.py:165-166`（本会话实读）：

```python
165	    candidate_text = "\n".join(candidate_lines) + "\n"
166	    CANDIDATE_PATH.write_text(candidate_text, encoding="utf-8")
```

`:165` 以 LF 拼出行文本；`:166` 的 `Path.write_text` 以默认 `newline=None` 打开文本写模式，Windows 上把每个 `\n` 翻译为 `os.linesep`（`'\r\n'`）落盘，9 hunk 之外的整篇被加 CR。因果复现证据：R2 会话实跑写 `'alpha\nbeta\n'` 落盘 `b'alpha\r\nbeta\r\n'`（`lead/b2b_candidate_review2_20261106/_r2_causal_out.txt:2-7`，本会话实读；该复现属 R2 会话实跑件，本件未重复落盘实验——按铁律 9 本件无临时写域）。

---

## 2. 处置

走 R2 三条关闭路径（`CANDIDATE_SEMANTIC_REVIEW_R2.md:128-130`）中的**第 2 条**。`CANDIDATE_SEMANTIC_REVIEW_R2.md:129` 原文：

> 2. 候选按母本 LF **重新物化**（H1–H9 之外逐字节与母本相同），四件指纹中「候选」一项随之更新并由总控重新绑定；或

处置产物（本会话 `ls -la lead/b2b_candidate_lf_20261107/` 实测，mtime 2026-11-07 14:09）：

| 件 | 路径 |
|---|---|
| 新候选（LF 版） | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` |
| 配套 diff | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` |

- 旧候选 `lead/b2b_candidate_20261106/qc151_trip.candidate.py` 保持原样未改：门禁 U4 指纹零漂移 PASS（§5），其 SHA256 与 R2 会话实算一致（`_r2_part1_out.txt:3`）与本会话实算一致（§3）。
- 「H1–H9 之外逐字节与母本相同」由 §4 侧 B 逐字节重建对比与门禁 N11/N12 实跑证明。
- 总控门禁脚本对路径 2 的预测值与产物一致（`lead/control_20261106/gate_n1_lf_20261107.py:47-51`，实跑 N2/N3/N16/N17 PASS，§5）。
- 路径 2 后半句「四件指纹中『候选』一项随之更新并由总控重新绑定」**未在本件完成、本件不签**（见 §6 第 6 条）。
- 新候选物化的执行过程本件未持、不述；本件只对产物做只读核验与记账。

---

## 3. 字节账

实跑命令：`python -I -X utf8 - <<'PY' … PY`（内联脚本：`hashlib.sha256` + `bytes.count`，只读母本/旧候选/新候选/设计件四路径，不写任何文件）。关键输出：

```
mother bytes=399508 LF=7291 CR=0 CRLF=0 sha256=517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636
old_cand(CRLF) bytes=420292 LF=7533 CR=7533 CRLF=7533 sha256=9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc
new_cand(LF) bytes=412759 LF=7533 CR=0 CRLF=0 sha256=ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2
derived: nominal_gain=old-mother=20784  real_gain=new-mother=13251  eol_only=nominal-real=7533
cross: eol_only == old_CRLF_count ? True
new_cand: CR=0 BOM=False tail=b'))\n'
new_LF - mother_LF = 242
```

| 件 | 路径 | 字节数 | LF | CR | SHA256（64 hex，本会话实算） |
|---|---|---:|---:|---:|---|
| 母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | 399,508 | 7,291 | 0 | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` |
| 旧候选（CRLF 版，N-1 客体） | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | 420,292 | 7,533 | 7,533 | `9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc` |
| 新候选（LF 版，路径 2 产物） | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | 412,759 | 7,533 | 0 | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` |

设计件 `lead/b2b_design_20261106/B2B_DESIGN.md`（66,735 B）指纹零漂移由门禁 U2 实跑核过（§5：`66735 B 565771d8b31c516d`）。

**「名义净增 20,784 B」的拆解**（全部本会话实算）：

- 名义净增 = 旧候选 − 母本 = 420,292 − 399,508 = **20,784 B**；
- 其中 **7,533 B 是纯行尾字节**：旧候选 7,533 行每行一个 CR，交叉核验 `eol_only == old_CRLF_count ? True`（上方输出）；
- **真实净增 = 13,251 B** = 新候选 − 母本 = 412,759 − 399,508，即设计 9 hunk 的行文本净变化：新候选 LF 7,533 − 母本 LF 7,291 = 242 行（= +255/−13，与 R2 的设计块统计 `+行=255 -行=13` 同值，`_r2_part1_out.txt:13`）；
- 门禁 N16「真实净增 == 13251 B」、N17「名义净增 − 真实净增 == 7533（纯行尾字节）」均 PASS（§5）。

---

## 4. 等价性双侧证明

同一内联实跑（`python -I -X utf8 - <<'PY'`，只读四个文件，不落盘）覆盖两侧；**两条都成立，缺一不构成证明**。

**侧 A：新候选 == 旧候选 CRLF→LF（独立来源交叉）**

代码：`as_lf = ob.replace(CRLF, b'\n')` 后与 `nb` 逐字节 `==`。输出：

```
== 侧A: 新候选 == 旧候选 CRLF->LF ==
equal_bytes = True   (412759 vs 412759 B)
old_len - as_lf_len == old_CRLF_count ? True (7533)
```

**侧 B：新候选 == 母本+9hunk 重建（设计 §4 语义重建）**

代码：从 `lead/b2b_design_20261106/B2B_DESIGN.md` 围栏块解析 diff 块（共 9 块），按 `@@` 头取 `(o_start, o_count, n_start, n_count)`，切 `-`/`+` 侧与上下文行；逐 hunk 核 `-` 侧与母本对应区间逐行一致后，按母本行序在 hunk 之外取母本原行、hunk 处替换为 `+` 侧，LF 拼接 + 末尾单个 LF，与新候选逐字节 `==`。输出：

```
== 侧B: 新候选 == 母本+9hunk 重建 ==
design diff blocks = 9
mother lines(LF split) = 7291
  hunk#1 hdr=(212, 6, 212, 21) -侧与母本一致=True
  hunk#2 hdr=(4458, 6, 4473, 10) -侧与母本一致=True
  hunk#3 hdr=(4558, 8, 4577, 131) -侧与母本一致=True
  hunk#4 hdr=(4572, 20, 4714, 105) -侧与母本一致=True
  hunk#5 hdr=(5906, 7, 6133, 8) -侧与母本一致=True
  hunk#6 hdr=(5936, 7, 6164, 8) -侧与母本一致=True
  hunk#7 hdr=(6294, 6, 6523, 9) -侧与母本一致=True
  hunk#8 hdr=(6386, 6, 6618, 15) -侧与母本一致=True
  hunk#9 hdr=(7122, 7, 7363, 8) -侧与母本一致=True
parse_ok = True  hunks = 9
equal_bytes = True   (412759 vs 412759 B)
rebuild sha256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2
```

重建件 SHA256 与新候选 SHA256 相同（`ca23c116…3c76d2`），即逐字节相等。

**门禁交叉**：同一判定的门禁版 N12「新候选 == 母本+9hunk 重建（逐字节，H1–H9 之外恒等母本）」、N14「新候选 == 旧候选 CRLF→LF（独立来源交叉验证）」、N15「旧候选字节差 == 其 CRLF 计数」均 PASS（§5 实跑输出）。

两侧合并的含义（仅此，不多不少）：新候选在字节层同时等于「旧候选做行尾规范化后的结果」与「母本+设计 9 hunk 的行文本重建」，且 H1–H9 之外逐字节恒等母本。这是字节层等价性证明，不构成对候选语义、可集成性或可用性的新判定（边界见 §6）。

---

## 5. 门禁实跑

命令（原样执行；门禁脚本自述「总控会话撰写……子代理不可修改、不可放宽」，`lead/control_20261106/gate_n1_lf_20261107.py:4`，本件未改它，铁律 3）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/control_20261106/gate_n1_lf_20261107.py post
```

完整 stdout（末行 SUMMARY 之后为退出码实测 `echo "GATE_EXIT=$?"`）：

```
PASS  U1 母本指纹零漂移  |  399508 B 517889c68f037ab6
PASS  U2 B2b 设计指纹零漂移  |  66735 B 565771d8b31c516d
PASS  U3 B2b 预审指纹零漂移  |  20615 B 3f97f3a466498196
PASS  U4 旧候选（CRLF 版）零漂移  |  420292 B CRLF=7533
PASS  N0 新候选文件存在  |  D:/Project/ra2-campaign-forge/lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py
PASS  N1 新候选零 CR 字节  |  CR=0
PASS  N2 新候选 LF 数 == 7533  |  LF=7533
PASS  N3 新候选字节数 == 412759（预测值）  |  412759 B ca23c116064b25a6
PASS  N4 无 UTF-8 BOM
PASS  N5 文件以单个 LF 收尾  |  b'))\n'
PASS  N6 设计稿解析出 9 个 diff 块  |  blocks=9
PASS  N7 母本按 LF 切行 == 7291  |  lines=7291
PASS  N9.1 hunk#1 -侧行数 == 头部声明  |  6/6
PASS  N10.1 hunk#1 +侧行数 == 头部声明  |  21/21
PASS  N11.1 hunk#1 -侧与母本逐行逐字一致  |  L212..L217
PASS  N9.2 hunk#2 -侧行数 == 头部声明  |  6/6
PASS  N10.2 hunk#2 +侧行数 == 头部声明  |  10/10
PASS  N11.2 hunk#2 -侧与母本逐行逐字一致  |  L4458..L4463
PASS  N9.3 hunk#3 -侧行数 == 头部声明  |  8/8
PASS  N10.3 hunk#3 +侧行数 == 头部声明  |  131/131
PASS  N11.3 hunk#3 -侧与母本逐行逐字一致  |  L4558..L4565
PASS  N9.4 hunk#4 -侧行数 == 头部声明  |  20/20
PASS  N10.4 hunk#4 +侧行数 == 头部声明  |  105/105
PASS  N11.4 hunk#4 -侧与母本逐行逐字一致  |  L4572..L4591
PASS  N9.5 hunk#5 -侧行数 == 头部声明  |  7/7
PASS  N10.5 hunk#5 +侧行数 == 头部声明  |  8/8
PASS  N11.5 hunk#5 -侧与母本逐行逐字一致  |  L5906..L5912
PASS  N9.6 hunk#6 -侧行数 == 头部声明  |  7/7
PASS  N10.6 hunk#6 +侧行数 == 头部声明  |  8/8
PASS  N11.6 hunk#6 -侧与母本逐行逐字一致  |  L5936..L5942
PASS  N9.7 hunk#7 -侧行数 == 头部声明  |  6/6
PASS  N10.7 hunk#7 +侧行数 == 头部声明  |  9/9
PASS  N11.7 hunk#7 -侧与母本逐行逐字一致  |  L6294..L6299
PASS  N9.8 hunk#8 -侧行数 == 头部声明  |  6/6
PASS  N10.8 hunk#8 +侧行数 == 头部声明  |  15/15
PASS  N11.8 hunk#8 -侧与母本逐行逐字一致  |  L6386..L6391
PASS  N9.9 hunk#9 -侧行数 == 头部声明  |  7/7
PASS  N10.9 hunk#9 +侧行数 == 头部声明  |  8/8
PASS  N11.9 hunk#9 -侧与母本逐行逐字一致  |  L7122..L7128
INFO  设计 diff 块中的裸空行数（无前缀、被当作上下文行） = 0
PASS  N12 新候选 == 母本+9hunk 重建（逐字节，H1–H9 之外恒等母本）  |  412759 vs 412759 B
PASS  N13 参与重建的 hunk 数 == 9  |  9
PASS  N14 新候选 == 旧候选 CRLF→LF（独立来源交叉验证）  |  412759 vs 412759 B
PASS  N15 旧候选字节差 == 其 CRLF 计数  |  7533
PASS  N16 真实净增 == 13251 B  |  actual=13251
PASS  N17 名义净增 − 真实净增 == 7533（纯行尾字节）  |  7533
PASS  N18 新候选 ast.parse 成功
PASS  N19 关键函数存在 make_pre_freshness_snapshot
PASS  N19 关键函数存在 classify_except_freshness
PASS  N19 关键函数存在 copy_post_except_evidence
PASS  N19 关键函数存在 finalize_trip
PASS  N19 关键函数存在 main
PASS  N20 锚点 H1 可定位  |  FRESHNESS_GROUP = "FRESHNESS"
PASS  N20 锚点 H2 可定位  |  backup_mtime_pre:{name}
PASS  N20 锚点 H3 可定位  |  def make_pre_freshness_snapshot(except_path:
PASS  N20 锚点 H4 可定位  |  def copy_post_except_evidence(
PASS  N20 锚点 H5 可定位  |  pre_freshness_snapshot: dict | None = None)
PASS  N20 锚点 H6 可定位  |  pre_freshness_snapshot=pre_freshness_snapsho
PASS  N20 锚点 H7 可定位  |  _pre_freshness_snapshot: dict | None = None
PASS  N20 锚点 H8 可定位  |  _pre_freshness_snapshot = make_pre_freshness
PASS  N20 锚点 H9 可定位  |  pre_freshness_snapshot=_pre_freshness_snapsh
PASS  N21 反扫描 OpenProcess 计数与母本相同  |  26 vs 26
PASS  N21 反扫描 ReadProcessMemory 计数与母本相同  |  8 vs 8
PASS  N21 反扫描 SuspendThread 计数与母本相同  |  0 vs 0
PASS  N21 反扫描 StackWalk 计数与母本相同  |  0 vs 0
PASS  N21 反扫描 MiniDump 计数与母本相同  |  19 vs 19
PASS  N21 反扫描 SetWindowsHookEx 计数与母本相同  |  1 vs 1
PASS  N21 反扫描 CreateRemoteThread 计数与母本相同  |  1 vs 1
PASS  N21 反扫描 ctypes 计数与母本相同  |  199 vs 199
PASS  N21 反扫描 WriteProcessMemory 计数与母本相同  |  3 vs 3
PASS  N21 反扫描 VirtualAllocEx 计数与母本相同  |  1 vs 1
PASS  N22 新 diff 零 CR 字节
PASS  N23 新 diff 含 9 个 @@ hunk  |  found=9
PASS  N24 新 diff 的 9 个 hunk 头与设计逐一相同
PASS  N25 新 diff 指向新候选文件名
SUMMARY_POST fails=0 bytes=412759 sha256=ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 net_gain=13251
GATE_EXIT=0
```

- 退出码 = **0**（`GATE_EXIT=0`，实测）。门禁脚本自述退出码 0 = 全 PASS、1 = 有 FAIL（`gate_n1_lf_20261107.py:10`）；SUMMARY 行 `fails=0` 对应其 `:304-306` 的 `raise SystemExit(0)`。
- 上述 PASS/FAIL 是门禁脚本的判定输出，本件如实转录；各项含义以门禁脚本源码为准（如 N12 在 `gate_n1_lf_20261107.py:230-243`，N14/N15 在 `:245-251`）。

---

## 6. 边界（不许越界）

1. 本件**不签 D-25 第 5 步通过**，也不签 R2 判定书整体复判。N-1 关闭只解除 R2 登记的阻断项 N-1 本身；R2 判定书的其余结论不变（`CANDIDATE_SEMANTIC_REVIEW_R2.md:20,26,103`）。
2. **不进入第 6 步隔离副本集成**。R2 已明示：即便语义层 PASS 成立也不等于可应用到母本、D-25 第 6 步未做（`CANDIDATE_SEMANTIC_REVIEW_R2.md:131,144`）。
3. 本件**不代表可应用到母本**。母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` 本件只读（铁律 3），任何落盘/应用动作不属本件范围。
4. **未做真机与运行时验证**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入代码（铁律 1、2）。门禁 N18 `ast.parse` 成功是静态语法层判定，不等于运行时实测（同 R2 口径，`CANDIDATE_SEMANTIC_REVIEW_R2.md:138`）。
5. N-1 关闭**不改变候选的语义审查结论**：本件证明的只是路径 2 的字节层事实（§3、§4），不新增也不推翻 R2 对候选语义的各项裁定。
6. R2:129 路径 2 后半句「四件指纹中『候选』一项随之更新并由总控重新绑定」与 R2:127「须经复核件确认」——**未在本件完成、未验、不归本件签**，属总控与复核件的后续动作。

### 未验清单

- 真机/运行时整趟、运行时退出码实测、`qc151_fields.json` 真实磁盘落盘：未验（本件与 R2 均未做，`CANDIDATE_SEMANTIC_REVIEW_R2.md:137-139`）。
- 新候选 `qc151_trip.candidate_lf.py` 的物化执行过程（何会话/何脚本产出）：本件未持、未验；本件对其正确性的依据仅 §3–§5 的只读实跑。
- `CANDIDATE_LF.diff` 的逐行内容（`+` 侧文本）复核：未验；门禁只核其零 CR（N22）、9 个 `@@` 头与设计逐一相同（N23/N24）、指向新候选文件名（N25）。
- 本件撰写者对 R2 之外任何台账/裁决登记的改动：无（铁律 3、9，未 commit、未 push，铁律 4）。
