# _oe_ORDERING_EVIDENCE.md — 定序依据清点、概率估算与无时间证据替代方案（2026-11-09）

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

> 绑定行按铁律固定格式：`被核对象` = `lead/cert_realcheck_20261109/_cr_seal.json`；本会话用 `hashlib.sha256(read_bytes())` 实算，等于编排方【编排方实跑指纹】该件 sha256/bytes，也等于 `_oe_verify.py` 的 `ORCH_ALL_MATCH = True` 中该行。行内 64 位十六进制与数字之间未插入路径、括号、星号、反引号或空格。

**纪律**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。全部为 `python -I -X utf8` 读盘、`hashlib`、`os.stat`、`git` 只读、`grep` / `find` / `fsutil` / `vssadmin` / `wevtutil` 只读查询、sqlite3 `mode=ro`。**只做清点与设计，未改任何既有件、未生成新 seal、未 commit、未 push**。绝对只读域与两件台账收尾 `READONLY_ALL_UNCHANGED = True`（8/8）。唯一写域 = `lead/ordering_evidence_20261109/`，产出前缀 `_oe_`。

## 0 本会话实跑命令清单（引用锚）

| # | 命令（原样） | 输出要点 |
|---|---|---|
| 1 | `mkdir -p lead/ordering_evidence_20261109`（写域建档） | `CREATED` |
| 2 | `git ls-files --error-unmatch lead/cert_realcheck_20261109/_cr_seal.json` | `error: pathspec ... did not match any file(s) known to git`、`rc=1` |
| 3 | `git log --oneline -- <6 目录> \| wc -l` / `git status --porcelain -- <5 目录>` / `git log -1 --format='%h %cI %aI'` | 6 目录 `git log` 全 0 行；5 目录全 `??`；HEAD `2657458 2026-11-01T19:35:33+08:00` |
| 4 | `find ... -name "db.sqlite"`（多 base） | 命中 `C:\Users\Administrator\.zcode\cli\db\db.sqlite`（3,391,758,336 B） |
| 5 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oe_verify.py"` | `ORCH_ALL_MATCH=True`、`TIMING_ALL_MATCH=True`、10 组秒差全复现、`CTIME_ANOMALY`、`ATIME distinct=6`、`COMBINATORICS`、内容因果链、绑定行复验 |
| 6 | `python -I -X utf8 ".../_oe_db_probe.py"`（首次 `IndexError`，修 3 处聚合取值后重跑成功，如实登记） | `PART_MINMAX=[1,644467,1782034359034,1794229822668,618737]`；`part` 618,699+ 行；8 个 seal 关键词**全命中**（`63ebd27428c1` n=146 等）；`PART_ROWID_VS_TIME` 抽样 19,970 对有 467 次时间倒退 |
| 7 | `python -I -X utf8 ".../_oe_db_focus.py"` | 首个 seal-sha part `rowid=635544 / 18:33:04.197`；写 builder `635245 / 18:27:31.093`；首次生成 `635250 / 18:27:35.515`；`WINDOW n_time_backwards=2439` |
| 8 | `python -I -X utf8 ".../_oe_deep.py"` | 两次 builder 输出全文首/末 sha；`rowid=635552 / 18:33:11.549` 常量从 `f1a559…1006`/3905 改为 `63ebd274…ca23`/4395；seal 自身 sha **不在** V1 四输出；5 个 `file_sha256` 在 `_r9s_regress_out.json`；USN/VSS/4663 查询（详见 §2） |
| 9 | `python -I -X utf8 -c "<fsutil/vssadmin/wevtutil 字节解码查询>"` | USN journal D: 存在（`First Usn 0x3f0000000`、`Next Usn 0x400452a58`、256 MB）；VSS 有 1 份 `C:` 卷影（`2026/11/9 13:52:54`）；4663 事件查询 rc=0、输出空 |
| 10 | `timeout 45 sh -c 'fsutil usn readjournal D: \| grep -a -i -m 12 "_cr_seal\|_cr_build_seal"'` | `usn_rc=124`（超时，未取到记录；标未验） |
| 11 | `python -I -X utf8 ".../_oe_explain.py"` | 精确 epoch 三时间；`ATIME_DRIFT changed_by_our_own_read=True`；两次生成时序；WHITELIST 关键词最早出现；`ROWID_MONO` 三段倒退 3220/2444/1600 |
| 12 | `grep -n "更晚建\|纯 mtime\|mtime 旁证\|..." <两件台账>` + 定点读 `GOAL_THREE_TARGETS_20261018.md:4412-4419/4592-4600/8844-8862/9165-9175/9336-9344` | 台账已自警「mtime 不自动等于异常发生时间」、T2 主判据=跑前基线哈希 + mtime 旁证、否决 naive 纯 mtime；另有 1 处「因为更晚所以漏」在 `lead/\refsync_scope_20261109/` |
| 13 | `find lead/cert_realcheck_20261109 -maxdepth 1 -type f \( -name "*.sig" -o ... \) -print` | 空（无伴随签名件） |
| 14 | `python -I -X utf8 -c "<8 件指纹收尾复算>"` + `git status --porcelain -- lead/ordering_evidence_20261109/` + `git log -1` | `READONLY_ALL_UNCHANGED = True`（8/8）；写域 `??`；HEAD 仍 `2657458` |

---

## 1 第一步：复核时序与元数据异常

### 1.1 (a) 10 件 mtime 与秒差能否复现？——**能，10/10 全复现**

实跑 #5（`_oe_verify.py`）：`TIMING_ALL_MATCH = True`，10/10 的 `mtime_str_match / epoch_match / bytes_match` 全 True。逐件值见 `_oe_verify_out.json:timing`（`lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md:68-79` 同表）。`seal − X` 整数差（=`int(epoch)` 相减）与浮点差（`os.stat().st_mtime` 原始浮点相减）全复现：

| X | 整数差 | 浮点差 | 换算 |
|---|---|---|---|
| V1_reg_out | **+16747 s** | +16747.945093 s | 4h39m7s |
| V1_reg_py | +20410 s | +20410.140839 s | 5h40m10s |
| V1_union_out | +20517 s | +20517.054212 s | 5h41m57s |
| r9s_pred | +19956 s | +19956.374944 s | 5h32m36s |
| r9s_reg_out | +14438 s | +14438.163088 s | 4h00m38s |
| fnr_check | +8502 s | +8502.298289 s | 2h21m42s |
| wl_audit | +12404 s | +12404.135316 s | 3h26m44s |
| seal_builder | +4 s | +4.498976 s | 4 s |
| real_verify | **−71 s** | −70.432142 s | 校验器晚 1m11s |

编排方给出的 5 个关键秒差（16747 / 20410 / 14438 / 4 / 71）**逐项吻合**。`SEAL_CHRONOLOGY.md:81-93` 的浮点/整数双口径亦吻合。

### 1.2 (b) ★ ctime 早于生成器 324 s —— **组合成立，但它有自然成因，不是伪造证明**

实跑 #5/#11 精确值：
```
seal          mtime = 1794220384.9740431  (18:33:04.974 +08)
              ctime = 1794220056.272236   (18:27:36.272 +08)
              atime = 1794230334.4536228  (21:18:54.453 +08，是本次会话读盘时刻)
seal_builder  mtime = 1794220380.4750667  (18:33:00.475 +08)
              ctime = 1794220380.4750667  (18:33:00.475 +08)
```
`seal.mtime − seal.ctime = 328.701807 s`；`builder.mtime − seal.ctime = 324.202831 s`（整数 324）；`impossible_under_normal_fs = True`。**组合成立**。

**但本会话在 CLI 会话库里找到了自然解释，这是编排方材料里没有的**（实跑 #7/#8/#11，`_oe_explain_out.json:two_builder_runs`）：

| DB rowid | `part.time_created`（UTC+8） | 事件 | 该次写出的 seal |
|---|---|---|---|
| 635245 | 18:27:31.093 | `Write` 创建 `_cr_build_seal.py`（首次落盘） | — |
| **635250** | **18:27:35.515** | `Bash` 首次跑 builder | `bytes=3905`、`sha256=f1a55901379e44c81a88b7f8f0ceab99a8038fc12a55cd819dfa8bd05f6d1006` |
| 635535 | 18:32:59.231 | `Edit` 改 builder（加 `evidence_span_sha256`） | — |
| **635544** | **18:33:04.197** | `Bash` 第二次跑 builder（覆写同名 seal） | `bytes=4395`、`sha256=63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23` |
| 635552 | 18:33:11.549 | `Edit` 把 `_cr_real_verify.py` 常量由 `f1a559…1006`/3905 改为 `63ebd274…ca23`/4395 | — |

即：`_cr_seal.json` 的**目录项在 18:27:36 首次创建**（ctime 保留该时刻），随后 18:33:04 被**同路径覆写**（mtime 更新到 18:33:04）；而 `_cr_build_seal.py` 在 18:32:59 被 Edit 过，其 ctime/mtime 一起更新到 18:33:00（NTFS 上编辑重建了该文件的时间戳）。于是「seal 的 ctime 早于 builder 的 mtime 324 s」是**「seal 首次生成用旧版 builder → 之后 builder 被改 → seal 被改后重建」**的自然结果，**无需任何 `SetFileTime` 操作**。

⇒ **结论要收窄**：这个组合
- **能证明**：至少两次生成、同路径覆写、且「mtime / ctime 分别反映不同的历史事件（最后写 vs 目录项创建/元数据变更）」，故用任一单个时间字段代表「文件诞生时刻」都会错；
- **不能证明**：有人调用 `SetFileTime` / `os.utime` 伪造过时间、不能证明「确系事后」、不能证明标注者看过答案。编排方背景称「它用这个实证了 mtime/ctime 均可被分别设置」——**本会话不能由这个组合实证「被分别设置」**；该组合在普通覆写下即可出现。可写性是 `SetFileTime`/`os.utime` 的**接口事实**（`SEAL_CHRONOLOGY.md:111`、`ORACLE_SPEC.md:121` 引文），不是本组合的推论。
- 附带：**DB 记录本身仍是本地可写文件**（§2），它解释成因但不构成带外时间源。

### 1.3 (c) atime 是什么值？有没有信息量？——**零定序信息量，且已被本会话自身读数污染**

- 编排方实跑表给 `seal_times.atime = 21:04:04`；`_sc_probe_out.json:13` 给 `atime_local = 2026-11-09 20:18:12`；本会话实跑 #5 读到 10 件 atime 的 **6 个不同值** `21:03:03 / 21:03:17 / 21:04:27 / 21:07:51 / 21:07:57 / 21:08:59`；实跑 #11 再读 seal 得到 `21:18:54.453`。**同一文件在不同时刻读，atime 值不同**。
- 实跑 #11 直接实证因果：对 `lead/seal_chronology_20261109/_sc_ctime.py` 先记 `atime_before = 1794230339.4825184`（21:18:59.482），仅执行一次 `read_bytes()` 后 `atime_after = 1794230383.4628143`（21:19:43.462），`changed_by_our_own_read = True`。
- ⇒ atime 记录的是「**最近一次被读**」，会被任何核查者（包括本次清点）改写；Windows 还默认启用 last-access 更新延迟/关闭策略。它**不承载文件生成/写入先后**，也不能作为「谁在何时看过」的证据（读的主体、是否成功读、是否缓存命中均不可判）。**不可用**。

### 1.4 (d) ★ 「元数据可被分别设置」对本库其它时序论证意味着什么？

**含义 = 一类证据被整体降级，但「无法定序」不成立。** 精确划分：

1. **适用范围是「全库所有以本地文件系统三时间为唯一依据的论证」，不是只此一件。** 可写性是 `SetFileTime` / `os.utime` / `touch` 的通用接口属性，对 `lead/` 下任何文件同样成立；`ORACLE_SPEC.md:121`（经 `SEAL_CHRONOLOGY.md:111` 引）已把 mtime / git commit 时间 / 邮件 Date 头 / 第三方 push 时间统一列为「**B 弱旁证（不抵赖）**」。
2. **降级不是归零**：仍可证明「**当前盘上此刻该字段的值**」及「若字段未被改动则的相对先后」。凡结论应写成「在当前可见 mtime 下 A 晚于 B / 不能排除事后」，不得写成「确系事后 / 确系事前」。`SEAL_CHRONOLOGY.md:37/:105-117` 已按此措辞。
3. **本库已有自警，不必推倒重来**（实跑 #12）：`GOAL_THREE_TARGETS_20261018.md:8859` 明记「**mtime 不自动等于异常发生时间**」并接受裁决员拒绝背书；`:9340` 把 T2 判据定为「**跑前基线哈希主判据 + A 加固版 mtime 旁证**」；`:9170` 记 `test_06_rewritten_same_content`（同内容重写、sha 相同 mtime 变）；`:9171` 记 `test_10_run_start_anchor_is_corroboration_only`「明确否决 naive A（纯 mtime）方案」；`:4595-4597` 明写「声明与 mtime 吻合不等于画面就是那一趟的真实状态」。这些结论的**主判据是哈希/内容**，mtime 只是旁证 ⇒ **不受本次降级影响，不需全部重审**。
4. **但有一类要重审**：以「更晚 ⇒ 因此被漏 / 因此不在圈定范围」为**因果解释**的论证。实跑 #12 命中 `lead/\refsync_scope_20261109\_rs_CARRIER_MAP.md:181` 与 `REFSYNC_SCOPE_FIX.md:220`：后者自己已收窄为「『因为更晚所以漏』只对这 1 件成立」，且举证改由**源件** `_lb_BOUND_VOLUME.md`（内容 + 已被 65 命中扫到）承担。这类应逐条查「是否另有内容/哈希主判据」，只有把 mtime 当唯一因果的才需改写。
5. **★★ 关键界定（编排方铁律）**：「元数据不可靠」**不等于「无法定序」**。本会话实跑确认还有多条可用：① 内容因果链（§2.4、§3 甲）；② CLI 会话库 `part` 表 append-only 行序 + `time_created`（§2.3）；③ USN journal 存在、VSS 卷影存在（§2.7）；④ 组合数学上的构造性恒等（§4）；⑤ commit-then-reveal / 带外见证等**制度级**设计（§3）。详见下节。

---

## 2 第二步：逐项清点所有可能的定序依据

统一记号：**能证明**=在该依据自身未被改动的假设下可推出的最小命题；**不能证明**=越界部分。

### 2.1 表：8 类依据逐项判定

| # | 依据 | 可用性 | 能证明什么 | 不能证明什么 | 可写性 / 强制性 |
|---|---|---|---|---|---|
| 1 | **mtime** | **部分可用**（弱旁证） | 当前盘上该字段的值；「若未被改则 A 晚于 B」；⇒「不能排除事后」 | 「确系事后/事前」、谁写的、看过什么、语义真值、抗同域双改 | **可写**（`os.utime`/`SetFileTime`/`touch`）；非密码学强制 |
| 2 | **ctime** | **部分可用**（更弱） | 目录项创建/最近一次元数据变更的时刻；本例实证「两次生成、同路径覆写」 | 内容最后写入时刻、文件「诞生」的唯一时刻（覆写时不更新）；任何认知状态 | **可写**（可被 NtSetInformationFile 类接口改；本例却是自然覆写，见 §1.2）；与 mtime 可不同源 |
| 3 | **atime** | **不可用** | 仅「最近一次被读」 | 生成/写入先后、谁读过、读了什么 | **可写且自动被污染**（实跑 #11 `changed_by_our_own_read=True`）；零定序信息 |
| 4 | **git 跟踪与 commit 历史** | **本例不可用（零覆盖）／机制上部分可用** | 若已跟踪：commit DAG 的父子关系 + `committer date` + tree/blob 哈希，构成内容绑定的顺序；已发布 commit 难静默改写 | 未跟踪文件的一切；本地 commit 时间可改（`GIT_COMMITTER_DATE`）；未 push 的 commit 可 rebase/amend；不可否认性 | commit 对象由 SHA-1 内容寻址（**内容强制**，改内容则 hash 变）；但**提交时间字段可写**、仓库本地可重写；无签名时不带身份 |
| 5 | **CLI 会话库 `db.sqlite` 的 `part` 表 rowid 顺序** | **部分可用（本会话新发现，且是本案最强现有旁证）** | rowid 是 `INTEGER PRIMARY KEY` 自增（实跑 #6 `CREATE TABLE part (id text primary key, ... , sequence integer)`，rowid 1→644,467），`time_created` 为 epoch ms；实跑 #7 精确给出 seal 两次生成的 wall-clock 与命令输出全文；可证「同一会话内事件的**记录顺序**」 | 绝对物理时刻（本地时钟可改）；rowid 严格等于全局真实先后（实跑 #6/#11 抽样 19,970 对有 **467 次** `time_created` 倒退，三段窗口 3220/2444/1600 次倒退，跨会话并发写入可见）；DB 文件本身可被 sqlite3 直接改写；不能判认知状态、不能判「未见 V1」 | **本地 sqlite 文件可写**（非密码学强制、非 append-only 日志、无签名）；但它是**第二个独立载体**，与文件 mtime 不同源，且由 CLI 运行时自动追加——伪造需同时改文件系统与 DB |
| 6 | **文件内容交叉引用（A 引用 B 的行号/引文/指纹）** | **部分可用 → 内容强制方向** | 若 B 的字节里出现 A 的 sha256（或 A 的逐字引文+行号），则**该版本的 A 必先于该版本的 B**（前提：sha256 抗碰撞、B 的字节可验证且未被改）。实跑 #5：`_sc_SEAL_CHRONOLOGY.md` 的 sha 出现在 `SEAL_CHRONOLOGY.md`；seal 的 sha/prefix 出现在 `_cr_real_verify.py`、`CERT_REAL_CHECK.md`、`ORACLE_SPEC.md`、`_os_ORACLE_SPEC.md`、两份 chronology 稿（详见 `_oe_verify_out.json:content_causal`） | **反向**（A 晚于 B 不能由哈希单向证明）；不能判「引用者当时是否相信/看过」；若 A、B 同处一个可写域则可**同域双改**同时伪造（`CERT_REAL_CHECK.md:509`，经 `SEAL_CHRONOLOGY.md:248-256` 引）；行号/引文本身可抄写，不含时间 | **内容强制（密码学级）**：sha256 单向，无法「先写 B 再让 A 的 hash 撞上」；但**载体文件可写**、且需带外锚才能抗同域双改 |
| 7 | **目录项创建顺序（NTFS 目录索引）** | **不可用／部分可用（弱）** | `os.scandir` 原生枚举顺序（实跑 #5 记 `DIR_ORDER_CERT`：cert 目录 38 项按名称排序，非创建序）。NTFS `$MFT` 的 `FILE_NAME` 创建时间、`$I30` 索引项可给「目录项加入顺序」 | 文件内容最后写入时刻；跨目录顺序；「文件生成」与「目录项建立」不等价；索引会被重建/整理、删除后复用 | **可写**（低层工具可改 MFT 属性；本会话**未解析 MFT / $I30**，只登记 scandir 枚举顺序，标未验） |
| 8 | **日志 / USN / VSS** | **部分可用（有载体，未取到本案记录，标未验）** | 实跑 #9：`fsutil usn queryjournal D:` rc=0、journal 存在（`Usn Journal ID 0x01dd047e36773586`、`First Usn 0x3f0000000`、`Next Usn 0x400452a58`、Max 256 MB、`写入范围分配: 已禁用` 见输出原文）；`vssadmin list shadows` rc=0、**有 1 份 `C:` 卷影，创建时间 `2026/11/9 13:52:54`**；USN/VSS/4663 若取到对应记录，可给独立于 mtime 的写入事件序列 | 实跑 #10 `timeout 45 sh -c 'fsutil usn readjournal D: \| grep -a -i -m 12 "_cr_seal\|_cr_build_seal"'` → `usn_rc=124`（**超时，未取到记录**）；`wevtutil qe Security ... EventID=4663 /c:1` rc=0 **输出空**（未启用或未记录，未进一步验）；VSS 是 **C:** 卷、文件在 **D:**，`13:52:54` 早于 seal 18:33:04 ⇒ **对本案无可用快照**；USN 环形缓冲可能已覆盖 11-09 早段；仍不能判「改本地时钟」或认知状态 | 日志由 OS 内核写（比用户态 mtime 难改），但**可管理员清除/停审、可改系统时钟**；**非密码学强制** |

### 2.2 (b)(c) 小结：哪些是密码学/内容强制，哪些可写

- **内容强制（不可伪造，抗碰撞假设下）**：仅 **#6 的哈希因果链**（以及 #4 中 git blob/commit 的内容寻址，但「提交时间」不在此列）。它给的是**偏序**（A 的 hash 在 B 里 ⇒ A 的版本先于 B 的版本），不是绝对时刻，也**不抗同域双改**。
- **其余全部可写**：#1/#2/#3 用户态可写；#4 时间字段可写、本地历史可重写；#5 本地 sqlite 可写；#7 MFT 属性可写；#8 日志/审计可清除、系统时钟可改。
- **强度分层**：内容强制（偏序） > OS 内核追加日志/卷影（若取到） > CLI 会话库第二载体 > git commit DAG（若已跟踪） > mtime/ctime > atime ≈ 目录枚举顺序。

### 2.3 (d) ★ 无 PKI 现状下最强的定序依据是什么？

**分两种问法，答案不同，不可混：**

- **「本案现已存在的、能实跑取到的最强依据」= CLI 会话库 `part` 表的 append-only 行序 + 命令输出全文（#5），并由内容因果链（#6）交叉加固。** 理由：它是**与文件 mtime 不同源的第二个载体**，由 CLI 运行时自动追加，实跑 #7/#8 给出 `rowid` 单调链 `635245 → 635250 → 635535 → 635544 → 635552` 与对应 `time_created`、以及两次 builder 的**完整 stdout**（含 `sha256 = f1a559…1006 / 3905` → `sha256 = 63ebd274…ca23 / 4395`）、常量 Edit 的 `old_string → new_string`。这构成一条**内容自洽的因果链**：`旧 seal 输出 → 改 builder → 新 seal 输出 → 把新 hash 写进校验器常量`，其中后一步的 `old_string` 逐字引用前一步的 hash，方向由内容强制，不依赖时间字段。
  - **但它只是制度级/旁证级**：DB 本地可写、时钟可改、rowid 不保证全局真实先后（实跑 #6/#11 倒退实证）。`ORACLE_SPEC.md:127`（经 `SEAL_CHRONOLOGY.md:281` 引）的定义仍然成立：「无 PKI 的上限 = 可复核的管道 + **制度担保的隔离**」。
- **「方法论上最强的、无 PKI 也能构造的依据」= 带外 commit-then-reveal（§3 乙/丙）+ 内容哈希锚**（`SEAL_CHRONOLOGY.md:138-141`、`:278-283`，`ORACLE_SPEC.md:131-133`）：`t0` 把 `H(P)` 放到被测方 A **无写权**的载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / ≥2 名见证人各留副本），`t1` 交 `H(labels)`，`t2` 才跑 V1；若之后 V1 产物里出现该 hash，则 A 的字节由 hash 单向绑定。密码学强制的是「**内容不可回改**」，时间先后靠「带外载体不可被 A 写」这一**制度事实**。
- **真正把时间做成密码级事实的是 M3（RFC3161 TSA + 透明日志）或 M2（`git commit -S`/minisign/sigstore + 公钥指纹带外公布）**；实跑 #13 确认 cert 目录**无任何 `.sig/.asc/.p7s/.pem/.crt/_pubkey*` 伴随签名件**，`SEAL_CHRONOLOGY.md:125-126/:274` 亦记 `n_repo_signature_sidecars=0`。⇒ **现状不可否认性 = 0**（`ORACLE_SPEC.md:125`，经 `SEAL_CHRONOLOGY.md:282` 引）。

---

## 3 第三步：无时间证据时的替代方案

### 3.1 (a) 「A 先于 B」还能怎么证？——**把「时间先后」换成「依赖先后」**

不再问「A 的写入时刻 < B 的写入时刻」（这需要可信时钟），改问下列三个可检验命题之一：

1. **内容依赖**：B 的字节里出现 A 的 sha256 / A 的逐字引文+行号 ⇒ 该版本 A 必已存在才能被引用（**单向、内容强制**）。
2. **承诺依赖**：`H(A)` 在 t0 被放到 A 无法回写的载体，B 在 t1 出现 ⇒ B 不能早于承诺公布。
3. **机制依赖**：B 的生成脚本/算法硬编码了 A 的结构（如本例 `SPECS`/`WHITELIST` 的 5 键）⇒ 不依赖时间即可判「B 由 A 派生」。

三者都**只给偏序、不给绝对时刻**，且都**不判认知状态**（「标注者是否看过答案」产物上不可判定，`ORACLE_SPEC.md:123`，经 `SEAL_CHRONOLOGY.md:144/:226` 引）。

### 3.2 (b)(c) 方案清单（≥3，含更好的）、强度与代价

| 方案 | 做法 | 强度 | 代价 | 能否抵御「同时改本地时钟+元数据」 |
|---|---|---|---|---|
| **甲 内容因果链** | B 逐字含 A 的 sha256 / 行号/引文；验证方重算 `sha256(A_bytes)` 并比对；更好的是**哈希链**：`H_n = sha256(H_{n-1} ‖ content_n)`（Merkle/追加链），任一环插入都破坏后续全部 | **密码学级偏序**（内容强制，抗碰撞假设）；**不给绝对时刻**；不抗同域双改（需带外锚，`CERT_REAL_CHECK.md:509`） | 极低：已有 `hashlib`；需预先约定「引用谁」，且 A 的字节要冻结 | **能**（完全不读时间字段） |
| **乙 commit-then-reveal** | `t0` 公布 `H(P)` 到 A 无写权载体；`t1` 公布 `H(labels)`；`t2` 才跑 V1；验收 `t0<t1<t2` 且 `sha256(P)==H(P)` | **制度级 t0<t1<t2 + 密码级内容绑定**；`ORACLE_SPEC.md:127` 定义的无 PKI 上限；不可否认性仍为 0（`ORACLE_SPEC.md:125`） | 中：≥2 见证人 / 公开只读载体 / ACL 隔离日志；302 项双盲全标注 ≈50.33 人时、端到端 60–95 人时（`SEAL_CHRONOLOGY.md:329`） | **能**（时序靠带外不可写，不靠本地时钟）；抵御不了多方串通 |
| **丙 带外见证 / 第三方时间戳** | 第三方记录「收到 H(P)」的时刻与内容；升级 = **M2** `git commit -S` / minisign / sigstore / 机构 SSO 短时效 token + 公钥指纹带外公布；再升级 = **M3** RFC3161 TSA + 透明日志（Certificate Transparency 式 append-only） | M2：把「谁、何时、哪份内容」绑定到人，T1/T4/T6/T8 由制度级升密码级（`SEAL_CHRONOLOGY.md:330`）；M3：时序成为可验证事实、真正不可否认（`:331`） | M2 低（一对现成密钥，无需自建 CA）；M3 高（采购/自建 PKI、TSA、透明日志运维）；人力成本三者共享不可压缩 | M2/M3 **能**；纯「第三方记录 wall-clock」只抵御改 mtime，**不抵御改本地时钟**（`SEAL_CHRONOLOGY.md:142`） |
| **丁（补充）OS 级只追加日志 + 卷影** | USN journal / Windows 4663 审计 / 第三方备份 / VSS 快照，把「写入事件」外置到内核或另一卷 | 中：独立于用户态 mtime；能证「某时刻存在某版本」 | 中高：需**事前**启用审计与保留策略；USN 环形缓冲会覆盖；实跑 #9/#10 见 §2.1#8 | **部分**：抵御改 mtime，抵御不了改本地时钟 |
| **戊（补充，本案已实证有效）多载体会话日志 + `old→new` 引用链** | 让 CLI/工作流运行时把每次工具调用（命令 + 完整 stdout）自动追加到与产物不同源的 DB；利用 `Edit` 的 `old_string` 逐字引用上一版 hash，形成自洽链 | **中（旁证级）**：跨载体一致性使伪造须同时改产物与日志；内容层由哈希加固；无签名故不可否认性 0 | 低（本库已天然具备，实跑 #7/#8 直接读到）；代价是必须**承认 DB 可写**并显式声明 | **部分**：不读时间也能靠 rowid 顺序 + 引用链定序，但 rowid 不保证全局真实先后（倒退实证） |
| **己（补充）闭合注册表 / 构造性恒等分析** | 不靠时间，直接查「候选集是否被上游 SPECS/白名单闭合决定」；若是，则「独立性」在机制层不可能成立（§4、`SEAL_CHRONOLOGY.md:219-224`） | **高（机制级，content-enforced）**，但证明的是「**依赖/同源**」而非「时间戳」 | 极低：读源码 + 集合运算 | **能**（完全不读时间字段） |

### 3.3 (d) ★ 对本案（seal vs V1）：三个方案各自能不能救？

**先固定要救的命题**：`_fnr_check.py:73-76`（经 `SEAL_CHRONOLOGY.md:165` 引）要求 ORACLE「**produced BEFORE V1 is run**, by an adjudicator who does not see V1's outputs and did not author V1, with a published SHA256 seal」。注意这是**「seal 早于 V1」**的方向，且还要求独立性、认知状态、带外发布。

| 方案 | 能否救 | 判断与实跑依据 |
|---|---|---|
| **甲 内容因果链** | **不能救（方向错 + 缺失）**，但能给出反向的、同样致命的结论 | 要证「seal 先于 V1」，须在 **V1 产物字节里出现 seal 的 sha256**。实跑 #5/#8：`seal_self_sha_in_V1 = []`；`_scv_sets.py:45-53`（读文件）亦判 3 份 V1 输出 `False`；编排方 `SEAL_CHRONOLOGY.md:138` 亦标「反向定序无法用哈希单向证明」。反向却**成立**：seal 的 5 个 `file_sha256` 出现在 `_r9s_regress_out.json`（实跑 #8），且 `_cr_real_verify.py` 逐字含 seal 的 sha（`SEAL_CHRONOLOGY.md:154-159`）⇒ 证得「**被封锚点文件 / seal 先于这些引用件**」，**不是「seal 先于 V1」**。且 DB 因果链（§1.2）显示 seal 生成在 18:27/18:33，V1 输出在 12:50–14:32（实跑 #11 `V1_parts` 12:50:36 起）——**方向是 seal 晚**。⇒ 甲不仅救不了，还把「晚」这件事用内容链加固了。 |
| **乙 commit-then-reveal** | **不能救本案（事后无法补做）**；但对「以后」是正确设计 | `t0` 承诺必须**在 V1 之前**公布到带外载体。实跑 #2/#3：seal 与 6 目录全 `git log` 0 行、`?? untracked`；实跑 #13 无签名 sidecar；`SEAL_CHRONOLOGY.md:125-127/:274` 记无内嵌 `timestamp/nonce/witness`、无 append-only 日志、`n_repo_signature_sidecars=0`。**现在补一个 `H(seal)` 的公布只能证明「从现在起没改」，不能追溯成 V1 之前的预注册**（这正是 commit-then-reveal 的全部意义）。⇒ 本案不可救；且即便当初做了，也仍买不到「未见 V1 输出」（`SEAL_CHRONOLOGY.md:144/:265/:284`）。 |
| **丙 带外见证 / 第三方时间戳** | **对「seal 早于 V1」：不能救；对「seal 晚于 V1」：本会话找到的本地多载体记录已把它做成强旁证，但仍不是密码级** | 无任何 t0 之前的带外记录（同乙，实跑 #2/#3/#13；`SEAL_CHRONOLOGY.md:132` 明记「本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据」）。**但本会话新发现**：CLI 会话库 `part` 表（实跑 #6–#8、#11）自动记录了 seal 两次生成、builder 改写、常量 Edit 的 `rowid`/`time_created`/完整 stdout，与文件 mtime/ctime 三元组**交叉自洽**（§1.2：ctime 18:27:36 ↔ 首次生成 18:27:35.515；mtime 18:33:04 ↔ 二次生成 18:33:04.197；builder 18:33:00 ↔ Edit 18:32:59.231）。这是**第二个独立载体**的 append-only 记录，强度远高于单看 mtime，但仍是**本地可写 DB + 本地时钟**，按 `ORACLE_SPEC.md:121` 属「B 弱旁证（不抵赖）」。⇒ 不能把「seal 早于 V1」救回来；能把「**在当前可见的多个独立载体下，seal 的生成记录晚于 V1 输出记录**」这一**方向性事实**显著加固。M2/M3 是未来方案，现状无。 |
| **丁/戊/己** | **丁不能救**（USN 未取到、VSS 是 C: 卷且 13:52:54 早于 seal、4663 空，实跑 #9/#10）；**戊能给出可用的方向性定序**（但只到旁证级，同上）；**己能给出机制级结论**（见 §4）但不救「早于」 | 见 §2.1#8、§3.2 |

**总判断**：三方案**没有一个能把本案救成「seal 是 V1 之前的独立预注册」**。原因不是证据不够，而是**命题本身与实测记录方向相反 + 承诺载体缺失**：`t0` 不存在、V1 产物里没有 seal 的 hash、且已有另一独立载体记录显示 seal 生成于 V1 之后。`SEAL_CHRONOLOGY.md:169-174/:189-191/:350` 的 `前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED` / 最终表述，本会话**复核后维持不变**；本会话只是补充了「成因可解释（两次生成）」与「存在第二载体的强旁证」两点。

---

## 4 第四步：三重相等的概率估算

### 4.1 (a) 事实复核（实跑 #5，与 `_scv_sets_out.json:1-17` 一致）

```
n_items=302  distinct=302  n_seal=5  n_flips=5  n_whitelist=5
seal_eq_flips=True   seal_eq_whitelist=True   flips_eq_whitelist=True
seal_tokens_eq_spec_keys=True   spec_keys=['可重建','实跑输出','改前改后','脚本存在性','需谁批准']
n_items_with_registered_token=10   n_distinct_registered_pairs=10   n_items_no_registered_token=292
coverage=5/302=0.016556291390728478   missing=297   n_negatives=0   truth_all_true=True
```

### 4.2 (b) 若三者独立，巧合概率（组合数）

设 `I` = 302 个互异 `(domain, token)` 对，`|I| = N = 302`，从中取 `k = 5` 个，共
`C(302,5) = 302·301·300·299·298 / 120 = 20,248,875,010`（≈ 2.025×10¹⁰，log₁₀ ≈ 10.3064）。实跑 #5 `COMBINATORICS` 给出该值。

- **两两相等**（例如 seal == flips，随机独立取）：`p₁ = 1 / C(302,5) ≈ 4.9385×10⁻¹¹`（约 1 / 202 亿）。
- **三重相等**（seal、flips、whitelist 三个独立 5-子集都等于同一集合）：`p₃ = 1 / C(302,5)² ≈ 2.4389×10⁻²¹`（约 1 / 4.1×10²⁰）。
- 若把候选池收窄为「含已登记 token 的 10 个 `(domain,token)` 对」（实跑 #5 `n_distinct_registered_pairs=10`）：`C(10,5) = 252`，则 `p₁ = 1/252 ≈ 3.968×10⁻³`、`p₃ = 1/252² ≈ 1.5747×10⁻⁵`。

**★ 但这个独立性假设在本案不成立，所以上述数字不能当「巧合概率」用。** 实跑 #5 与 `SEAL_CHRONOLOGY.md:219-224` 已给出构造链：
`_r9s_predicates.py:371-402` 的 `SPECS` 是**闭合注册表，恰好 5 键** == `spec_inventory` 5 键 == seal 5 token == flips 5 token == whitelist 5 token（`seal_tokens_eq_spec_keys=True`）；`WHITELIST` 是 `_r9s_regress.py:112-119` 的**硬编码字面量**，注释明写「本次任务书指名要求改判的 5 处」（我实读该文件 `:112-119` 确认）；`_fnr_check.py:314-351` 的 `CERTS` 同 5 键、同 `independent_blind_adjudicator` 串（`SEAL_CHRONOLOGY.md:221` 引）；302 项里只有 10 对含已登记 token，其余 292 项**结构性不可能翻案**。
⇒ 三者相等是**构造性恒等（by construction）**，条件概率 = 1，不是 2.4×10⁻²¹ 的巧合。`SEAL_CHRONOLOGY.md:206-224` 的「不是巧合，是构造性恒等」判定，本会话独立复算后**维持**。

### 4.3 (c) ★ 若不是巧合，相等本身是不是「标注时已见答案」的证据？——**不是「见过 V1 输出」的证据，但它是「依赖被测方预置答案」的机制级证据，且不依赖任何时间字段**

必须把两个命题分开，否则会犯 `SEAL_CHRONOLOGY.md:224` 指出的措辞不精确：

| 命题 | 判定 | 依据 |
|---|---|---|
| P1「**标注时看过 V1 回归输出**」 | **不能由此相等证明**（产物上不可判定认知状态，`ORACLE_SPEC.md:123`） | 白名单/SPECS 在 V1 输出**之前**就存在：实跑 #11 `WHITELIST_EARLIEST`「本次任务书指名要求改判的 5 处」最早 `rowid=620123 / 12:56:18.016`，`_r9s_regress.py` 文件 mtime 12:59:07（`SEAL_CHRONOLOGY.md:220`）；V1 输出 13:53:57 / 14:32:26。⇒ 选择**无需**看 V1 输出，从任务书预置白名单即可得出 |
| P2「**标注集与被测方的答案集/白名单同源，故 ORACLE 不由被测方独立派生**」 | **★ 成立，且是内容/机制强制的，比时间戳更强** | 实跑 #5 三重相等 + `seal_tokens_eq_spec_keys=True`；`_r9s_regress.py:112-119` 硬编码；`_cr_build_seal.py:24-77`（我实读）的 `ITEMS` 5 项逐字就是这 5 对、`oracle.truth=True` 与 `author="independent_blind_adjudicator"` 全为**生成器内自写字符串**（`:30-31`、`:41-42`、`:52-53`、`:64-65`、`:75-76`） |

**「比时间戳更强」的确切含义**：
- 时间戳（mtime/ctime/atime/DB `time_created`）都是**可写元数据**，只给「不能排除」级别的弱旁证（§2）。
- 集合相等 + 闭合注册表是**读字节即可复算、且不依赖任何时间字段**的结构事实：改时间不能改变它，改内容会改变 sha256（编排方 8 件指纹 + 实跑 #14 `READONLY_ALL_UNCHANGED=True` 已冻结）。它是**密码学/内容层可复核**的。
- 它直接推出：`(A) ∀i: V0=0 ∧ V1=1 ⇒ ORACLE=1` 变成**恒真重言式**，不携带关于 V1 是否放松的信息（`SEAL_CHRONOLOGY.md:232`）；`ORACLE_SPEC.md:109` 的 C3「不可派生」判 FAIL；「标注独立」在**机制层面不可能成立，与标注者认知状态无关**（`:224`）。
- **但它仍不能推出**：「标注者看过 V1」「标注者有意作弊」「语义真值为伪」「`NO_RELAXATION` 为假」「mtime 曾被伪造」。`SEAL_CHRONOLOGY.md:113-117/:226/:357-358` 已逐条划界。准确表述应为「**依赖被测方预置白名单/SPECS，该依赖早于 V1 输出；且 seal 在当前可见多个载体的记录下晚于 V1、不能排除事后**」（`:224` 原文）。

### 4.4 (d) 这个证据能不能替代时间证据？——**能替代「独立性/预注册前提是否成立」的时间证据；不能替代「A 先于 B」的时间证据**

- **能替代的部分**：判「预注册/独立性」时，原本要靠 `t0<t1<t2` 时间戳。而 P2（构造性恒等）**不依赖时间**就能判 `_fnr_check.py:73-76` 的 ②③（「未见 V1 输出 / 不可由 V1 派生」「身份独立」）**机制上不满足**：`author` 只是字符串、选择由闭合注册表决定。⇒ 对 `SEAL_CHRONOLOGY.md:170-171` 这两条，内容证据**更强且足够**，`前提层不成立` 的结论不因时间元数据被降级而动摇。这正是编排方铁律「元数据不可靠 ≠ 无法定序」的落点。
- **不能替代的部分**：① ①「产于 V1 之前」是**纯粹的时间先后命题**，集合相等完全不蕴含它（相等在 seal 早于或晚于 V1 时都成立）；② 不能给绝对时刻、不能给 `t0`；③ 不能判「确系事后 / 标注者看过答案」这两个认知/时序状态；④ 不能救 §3.3 的「seal 早于 V1」。
- ⇒ **判词**：内容证据是**前提层**的充分替代，是**时序层**的不充分替代。二者分层，不得互相降格或冒充。`SEAL_CHRONOLOGY.md:180-183/:187-191` 的「管道层 / 前提层互不蕴含」框架仍然适用。

---

## 5 第五步：结论与建议

### 5.1 (a) 「元数据不可信」的适用范围 —— **全库方法论级，但证据级只此一件被实证异常**

- **方法论层（全库）**：mtime/ctime/atime 的可写性是 API 事实，对 `lead/` 下**任何**文件同样成立；`ORACLE_SPEC.md:121` 已把 mtime 列为「B 弱旁证（不抵赖）」。⇒ 今后**所有**仅凭本地三时间得出的「确系事前/确系事后」结论一律不可作，须改写成「在当前可见 mtime 下 / 不能排除」。
- **证据层（本件）**：本会话实证的「ctime 早于 mtime 328 s、早于 builder 324 s」是 **`_cr_seal.json` 这一件**的具体状态，且已由 DB 记录解释为**两次生成 + 同路径覆写**（§1.2），**不是**「全库文件都被改过时间」的证据，更不是「有人伪造过 mtime」的证据。`SEAL_CHRONOLOGY.md:99` 亦明确「这不是『有人伪造过 mtime』的证据，成因未验」——本会话**补上了成因**，但结论方向不变。
- **不扩散到内容层**：哈希/集合/引文等**内容强制**证据不受影响（实跑 #5/#14，编排方 8 件指纹全 MATCH、只读域 8/8 未变）。

### 5.2 (b) 已有基于 mtime 的时序论证要不要全部重审？——**不全部重审；按「mtime 的角色」分三类**

| 类 | 判据 | 处置 | 实跑依据 |
|---|---|---|---|
| A. mtime 为**唯一主判据**且结论是「确系 X 时发生 / 确系事后 / 因此被漏」 | 需要重审，改写为「不能排除」或补内容/日志主判据 | 实跑 #12：`lead/\refsync_scope_20261109\REFSYNC_SCOPE_FIX.md:220` 已自行收窄「『因为更晚所以漏』只对这 1 件成立」并把举证移到源件内容；`_rs_CARRIER_MAP.md:181` 同类。建议逐条查是否另有内容主判据 |  |
| B. mtime 为**旁证**，主判据是哈希/内容 | **不需重审** | `GOAL_THREE_TARGETS_20261018.md:9340`（T2 = 跑前基线哈希主判据 + A 加固版 mtime 旁证）、`:9171`（明确否决 naive 纯 mtime）、`:9170`（同内容重写 sha 同 mtime 变）、`:4595-4597`（吻合 ≠ 真实状态）、`:8859`（mtime 不自动等于异常发生时间）、`:4416`（残留件判定由**同 sha/同字节/同微秒 mtime** 共同支撑） |  |
| C. 仅用 mtime 做**描述性**陈述（如「107 份 mtime 跨 442.20 小时」） | 不需重审，但须保留「这是文件 mtime」的限定 | `GOAL_THREE_TARGETS_20261018.md:8847-8851/:8877/:8899` 已自行订正并三度自警 |  |

⇒ **结论：做一次「A 类清单化筛查」，不做全库推倒。** 本会话实跑 #12 只做了 grep + 定点读若干行，**未穷举全库所有 mtime 论证**，标未验；A 类是否还有其它实例需在授权范围内另跑全量扫描。

### 5.3 (c) 「以后做时序论证」的准则（可写入门禁）

1. **时间字段只作旁证**：任何结论不得单凭 mtime/ctime/atime 得出「确系」；一律带「在当前可见 X 下 / 不能排除」限定。atime 直接弃用。
2. **优先内容强制的偏序**：把 `H(A)` 写进 B 的字节（或 B 的 `old_string`/引文逐字引用 A），用 `hashlib.sha256(read_bytes())` 复算；给「A 的版本先于 B 的版本」而非绝对时刻。更稳的是哈希链 `H_n = sha256(H_{n-1}‖content_n)`。
3. **承诺必须在被测方写域之外**：`H(P)`、标注包、校验器常量**至少一者**带外（`SEAL_CHRONOLOGY.md:269-275` T8 判据）；验收方式是模拟同域双改**必须仍 FAIL**（`CERT_REAL_CHECK.md:509` 的现状是 PASS，故 T8 现状不成立）。
4. **commit-then-reveal 固定 `t0<t1<t2`**：`t0` 公布 `H(P)` 到 A 无写权载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / ≥2 见证人 + 带 Date 头回执），`t1` 交 `H(labels)`，`t2` 才跑被测程序。事后补公布只能证明「从现在起未改」。
5. **签名/时间戳升级**：`git commit -S` / minisign / sigstore / 机构 SSO 短时效 token + 公钥指纹带外公布（M2，`ORACLE_SPEC.md:132`）；需真正不可否认才上 RFC3161 TSA + 透明日志（M3，`:133`）。本会话实跑 #13 确认现状无签名 sidecar。
6. **事前启用外置日志**：USN / 4663 审计 / 另一卷 VSS / 第三方备份，且保留策略覆盖目标时段。实跑 #9 显示 D: USN journal 存在但 #10 读取超时未取到、VSS 只有 C: 卷且早于 seal、4663 空 ⇒ **必须事前配置，事后取不到**。
7. **多载体交叉**：产物 + CLI 会话库 + 校验器常量 + 台账，至少两处不同源；凡「某文件的 ctime 早于其生成器」这类异常，先查「是否两次生成/覆写」再谈伪造（本会话 §1.2 即为一例）。
8. **分离四层，不互相冒充**：管道层 / 前提层 / 时序层 / 认知层（`SEAL_CHRONOLOGY.md:176-185`）。`INTEGRITY_OK` 不覆盖抗同域双改、不是 `NO_RELAXATION=PASS`；「内容绑定 ≠ 认知状态绑定」（`ORACLE_SPEC.md:161`）。
9. **闭合注册表要先查**：若候选集被上游 SPECS/白名单闭合决定，直接判「选择依赖 / 不可派生 FAIL」，不必绕时间戳（§4.3）。
10. **凡阴性结论**（日志无命中）记为「某一时刻点值」，不把字节数/目录数当可引用定值（`SEAL_CHRONOLOGY.md:130`）。

### 5.4 (d) 本条工作判不了什么（如实列）

1. **判不了「seal 确系事后生成」、也判不了「mtime/ctime 曾被人为伪造」** —— 本会话反而给出「两次生成 + 覆写」的自然成因（§1.2）；未读 USN 具体记录（#10 超时）、未验 ctime 是否被 `NtSetInformationFile` 类接口改过。
2. **判不了 seal 与 V1 的绝对真实先后** —— 无带外时间戳、无签名、git 对 11-09 六目录零覆盖、CLI DB 仍是本地可写文件 + 本地时钟。只能说「在当前可见的 mtime/ctime 与 CLI DB 两个独立载体下，seal 生成记录晚于 V1 输出记录」。
3. **判不了「标注者是否看过 V1 输出」这一认知状态** —— 产物上不可判定（`ORACLE_SPEC.md:123`）；本会话只判了集合相等与构造链。
4. **判不了语义真值 / 302 项语义裁决 / `NO_RELAXATION`** —— 未重读 32 主件全文逐项重判；5/302 覆盖、0 负例、0 `UNVERIFIABLE`（`SEAL_CHRONOLOGY.md:201-204/:359-361`）。
5. **判不了「三层独立互证 / 置信度量化」** —— 相关失效叠加；κ、p_o、CI、总体 fp/fn 率无第三方标签（`:361`）。
6. **判不了不可否认性** —— 无 PKI / 签名 / RFC3161；实跑 #13 无伴随签名件；`ORACLE_SPEC.md:125` 技术上限为 0。
7. **判不了本库 A 类 mtime 论证的完整清单** —— 实跑 #12 只做 grep + 定点读，未做全库穷举扫描，标未验。
8. **判不了 NTFS 目录项真实创建顺序 / MFT `$I30` 索引序** —— 实跑 #5 只登记 `os.scandir` 枚举顺序（按名称排序，非创建序），**未解析 MFT**，标未验。
9. **判不了 USN 是否留有 `_cr_seal.json` 的写入记录** —— `fsutil usn queryjournal D:` 确认 journal 存在，但 `fsutil usn readjournal D: | grep ...` 45 s 超时（#10 `usn_rc=124`）；`wevtutil ... 4663 /c:1` rc=0 输出空（#9），未进一步判定是「未启用审计」还是「无记录」，标未验。
10. **判不了 VSS 对本案的适用性** —— #9 显示唯一卷影是 **C:** 卷、`2026/11/9 13:52:54`，而项目在 **D:** 且 seal 在 18:33，故无可用快照；未列全所有卷/所有 shadow（只一次 `vssadmin list shadows` 输出）。
11. **判不了 zero-RT 下的一切运行时行为** —— 零真机、零采样代码；未复跑真机/负样本/跨项目推广。
12. **本会话未跑 `_cr_real_verify.py:main()` / `_fnr_check.py:main()` / 未重跑 `:509` 同域双改攻击** —— 只读纪律；未生成新 seal。管道层判断依据仍是读源码 + 指纹/集合复算（`SEAL_CHRONOLOGY.md:367` 同）。
13. **未执行任何 §3 的甲/乙/丙/丁方案**（只做清点与设计要求）—— 全部标「设计，未验」。
14. **§2.1#5 的 CLI 库命中数是某一时刻点值**（实跑 #6 `part` 行 618,737 与后续 #7 的 644,467 上限不同，会话并发写入会漂移）；只把「命中/未命中」当结论，不把行数当可引用定值。
15. **`part` 表 rowid 的全局单调性未验** —— 实跑 #6/#11 抽样实证存在 `time_created` 倒退（19,970 对中 467 次；三段窗口 3220/2444/1600），故只用于「同一会话内的记录顺序」，不外推为全局真实先后。

---

## 6 产出与纪律核对

- 唯一写域 `lead/ordering_evidence_20261109/` 新增 10 件（前缀 `_oe_`）：`_oe_verify.py` / `_oe_verify_out.json`、`_oe_db_probe.py` / `_oe_db_probe_out.json`、`_oe_db_focus.py` / `_oe_db_focus_out.json`、`_oe_deep.py` / `_oe_deep_out.json`、`_oe_explain.py` / `_oe_explain_out.json`、本件 `_oe_ORDERING_EVIDENCE.md`。
- 六只读域及两件台账：收尾实跑 #14 `READONLY_ALL_UNCHANGED = True`（8/8 编排方指纹 sha + bytes 全 MATCH）；未修改、未追加、未覆盖。
- `git status --porcelain -- lead/ordering_evidence_20261109/` = `?? lead/ordering_evidence_20261109/`；HEAD 仍 `2657458 2026-11-01T19:35:33+08:00`；**未 commit、未 push**。
- **未改任何既有件、未生成新 seal**。指纹一律 `hashlib`；Python 一律 `python -I -X utf8` + 绝对路径（`_oe_db_probe.py` 首次 `IndexError` 已修并如实登记）。
- 引用均追到「实跑命令 + 输出」或「文件:行」；未验项已明确标注，未补造。
