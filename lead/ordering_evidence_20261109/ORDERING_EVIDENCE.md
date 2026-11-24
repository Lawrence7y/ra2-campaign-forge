# ORDERING_EVIDENCE.md — 定序依据清点件（2026-11-09）

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

> 绑定行按铁律固定格式：`被核对象` = `lead/cert_realcheck_20261109/_cr_seal.json`（见本件 §6 复核回件）。本会话用 `hashlib.sha256(read_bytes())` 实算，等于编排方【编排方实跑指纹】该件 sha256/bytes。行内 64 位十六进制与数字之间未插入路径、括号、星号、反引号或空格。

**本件身份**：定序依据清点件撰写员的最终交付，写于唯一写域 `lead/ordering_evidence_20261109/`。**只做清点与设计**；未改任何既有件、未生成新 seal、未 commit、未 push；零真机（未启动 gamemd.exe / ra2loader / YURI.exe、未 taskkill、未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。全部为 `python -I -X utf8` 读盘、`hashlib`、`os.stat`、AST 静态解析、`git` / `fsutil` / `vssadmin` / `wevtutil` 只读查询、sqlite3 `mode=ro`。

**本件相对被核件的状态**：被核件 `lead/ordering_evidence_20261109/_oe_ORDERING_EVIDENCE.md`（45,567 B，sha256 `2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969`）已由复核回件判 **`verdict = partial`**（编排方【复核】字段），按交付要求**如实记为 `unconfirmed`**。本件不修改被核件，而是把复核指出的 3 处事实性越界 + 1 处标签松动逐项吸收并收窄措辞；**最终结论不变**：`前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED`（`lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md:174`、`:350`）维持。

**本会话实跑命令清单（引用锚，全部为本次实跑）**：

| # | 命令（原样） | 输出要点 |
|---|---|---|
| C1 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oew_verify.py"` | `FINGERPRINTS_ALL_MATCH=True`（8/8）、`REVIEWED_MATCH_BASELINE=True`、`BINDING n_strict_hits=1`、10 组秒差全复现、`CTIME`、`WIN_CTIME_EXP`、`LIB_SCAN`、`COMBINATORICS`、`TRIPLE`、`CONSTRUCTION`、内容因果链、`DB`、`GIT_HEAD`、`READONLY_ALL_UNCHANGED=True` → `_oew_verify_out.json` |
| C2 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oew_2.py"` | `AST_sets`（五源集合全等）、`coverage`、`whitelist_vs_V1`、`db_tokens`、`db_rows_detail`（两次 builder stdout + old→new 常量）、`ledger_selfwarnings`、`atime_drift` → `_oew_2_out.json` |
| C3 | `timeout 45 sh -c 'fsutil usn readjournal D: \| grep -a -i -m 12 "_cr_seal\|_cr_build_seal"'` | `PIPE_RC=124`（45 s 超时、0 字节输出）；另跑带 `2>/dev/null` 变体同为 `RC2=124` |
| C4 | `git log -1 --format="%H %cI"` / `git ls-files --error-unmatch lead/cert_realcheck_20261109/_cr_seal.json` / `git status --porcelain -- <5 RO 目录+2 台账>` / `git log --oneline -- <6 目录>` | HEAD `26574589aa8401e8f3f2934680a1ea7109bafa2d 2026-11-01T19:35:33+08:00`；`rc=1 pathspec ... did not match`；5 RO 目录全 `??`；六目录 `git log` 全 0 行 |
| C5 | `fsutil usn queryjournal D:` / `vssadmin list shadows` / `wevtutil qe Security /q:"*[System[(EventID=4663)]]" /f:text /c:1`（C1 内） | 三者 `rc=0`；USN journal 存在（256 MB、`Next Usn` 点值本会话 `0x4006c22e8`）；VSS 唯一 `C:` 卷影 `2026/11/9 13:52:54`；4663 输出空 |
| C6 | `python -I -X utf8 -c "<utime 实验>"`（C1 内，写域新建 `_oew_ctime_probe.tmp` 后 unlink） | 同路径覆写 `ctime_changed_on_overwrite=False / mtime_gt_ctime_after_overwrite=True`；`os.utime(p,(atime, mtime-1000))` 后 `mtime_changed_by_utime=True / ctime_changed_by_utime=False` |
| C7 | `python -I -X utf8 -c "<5 个 file_sha256 出处>"`（C1 内） | 5 个 hash 在 `_r9s_regress_out.json` 的确切 JSON 路径全为 `/four_domains/*/mainSha256`（`all_are_four_domains_mainSha256=True`） |
| C8 | `python -I -X utf8 -c "<收尾 8 件指纹复算>"`（C1 内，末段） | `READONLY_ALL_UNCHANGED = True`（8/8 sha256 + bytes 全等编排方基线） |

> 说明：C2 中一次 python-embedded 的 USN 管道因 Git Bash 引号传递得到 `rc=255`（系统找不到指定路径），属**命令包装问题**，非目标结论；故按点名命令原样在 shell 重跑 C3，得 `rc=124`。两值均如实登记。C1 内 sqlite 活库用 `mode=ro` + 5 次重试（复核回件 C2 曾记 `immutable=1` 触发 `database disk image is malformed`），本会话未复现该错误，标「本会话未遇」。

---

## 1 目的与边界

**目的**：在「本地文件系统三时间（mtime / ctime / atime）可分别设置」的前提下，清点**还有什么能用来定序**，逐项判「可用 / 部分可用 / 不可用」及其「能证明什么 / 不能证明什么」；给出替代方案的设计、强度、代价与对本案的可救性；对「5 项 == whitelist == flips」的**三重相等**做巧合概率估算并判其机制含义；最后给出复核回件、结论与未验项。

**边界（铁律）**：
1. **只做清点与设计**，**不改任何既有件、不生成新 seal**。唯一写域 = `lead/ordering_evidence_20261109/`；本件新增文件前缀 `_oew_`（`_oew_verify.py` / `_oew_verify_out.json` / `_oew_2.py` / `_oew_2_out.json` / `ORDERING_EVIDENCE.md`）。
2. **绝对只读**：`lead/seal_chronology_20261109/`、`lead/oracle_spec_20261109/`、`lead/cert_realcheck_20261109/`、`lead/gate_pipeline_20261109/`、`lead/gate_r9sem_20261109/`、两件台账，一律不得修改、追加、覆盖。C8 收尾 `READONLY_ALL_UNCHANGED = True`。
3. **零真机 / 零采样代码**（见篇首），**不 commit、不 push**。C4 复核 HEAD 未变、写域仍 `??`。
4. Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
5. 引用必须追到「实跑命令 + 输出」或「文件:行」；拿不到写「未验」，不补造。

**「元数据不可靠」不等于「无法定序」**：这是编排方铁律，也是本件的落点。mtime / ctime / atime、git 时间字段、sqlite `time_created`、MFT 属性、OS 日志、系统时钟都**可写**；但**内容因果链（哈希单向偏序）、闭合注册表的构造性恒等、多载体 old→new 引用链、commit-then-reveal 的制度性承诺、带外见证**都不读时间字段即可给出「依赖先后」。§3 给出七类逐项判定，§4 给出三个替代方案，§5 给出概率估算。

---

## 2 上游指纹 + 时序与元数据复核

### 2.1 八件上游指纹（编排方【编排方实跑指纹】逐件比对）

C1 `FINGERPRINTS_ALL_MATCH = True`，8/8 sha256 与 byte 数全等；C8 收尾再算一次 `READONLY_ALL_UNCHANGED = True`。逐件（sha256 略去中段用 `…` 仅为排版，原值见 `_oew_verify_out.json:fingerprints` 与编排方指纹字段）：

| # | 文件 | sha256（完整 64 hex 见输出件） | 字节数 | 结果 |
|---|---|---|---|---|
| 1 | `lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md` | `5af2b304…391c6392cc5f` | 45423 | MATCH |
| 2 | `lead/seal_chronology_20261109/_sc_probe_out.json` | `09548c9a…f8d8aa20b1ec6d7` | 9590 | MATCH |
| 3 | `lead/seal_chronology_20261109/_sc_ctime.py` | `e49151ca…0bad7839b8d769657` | 1126 | MATCH |
| 4 | `lead/oracle_spec_20261109/_os_ORACLE_SPEC.md` | `5417fb06…e1d0048bf695a2156` | 52542 | MATCH |
| 5 | `lead/cert_realcheck_20261109/_cr_seal.json` | `63ebd274…9221d5d3ca23` | 4395 | MATCH |
| 6 | `lead/cert_realcheck_20261109/_cr_build_seal.py` | `2e539d39…ea5ea279ef0b86574` | 5376 | MATCH |
| 7 | `lead/PENDING_DECISIONS.md` | `3765eddb…2692a1d15e1c8f2d7` | 52419 | MATCH |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de4…eee120384bf640cded8a933ede` | 759518 | MATCH |

> 所有 8 件完整 64 位值见 C1 `_oew_verify_out.json:fingerprints`、编排方【编排方实跑指纹】及本件 §6.2 的绑定行；本表用 `…` 缩写仅为排版可读，不作引用值。

被核件自身：C1 `REVIEWED_MATCH_BASELINE = True`（`_oe_ORDERING_EVIDENCE.md` = `2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969` / 45,567 B），与编排方【复核】`sha256Line` 第 9 行一致；其严格格式绑定行 `n_strict_hits=1`、`equals_disk_seal_sha=True`、`equals_disk_seal_bytes=True`（§6）。

### 2.2 10 件 mtime 秒差（C1，全 10/10 复现）

十件 `mtime` 逐件值见 `lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md:68-79` 与 `_sc_probe_out.json:4-26`；C1 `deltas_seal_minus`（`seal.mtime − X.mtime`，整数 = `int(epoch)` 相减，浮点 = `os.stat().st_mtime` 原始浮点相减）：

| X | mtime | 整数差 | 浮点差 |
|---|---|---|---|
| `seal` | 18:33:04.974 | 0 | 0.0 |
| `seal_builder` | 18:33:00.475 | **+4 s** | +4.498976 |
| `real_verify` | 18:34:15.406 | **−71 s** | −70.432142 |
| `V1_reg_out` | 13:53:57.028 | **+16747 s** | +16747.945093 |
| `V1_reg_py` | 12:52:54.833 | +20410 s | +20410.140839 |
| `V1_union_out` | 12:51:07.919 | +20517 s | +20517.054212 |
| `r9s_pred` | 13:00:28.599 | +19956 s | +19956.374944 |
| `r9s_reg_out` | 14:32:26.810 | **+14438 s** | +14438.163088 |
| `fnr_check` | 16:11:22.675 | +8502 s | +8502.298289 |
| `wl_audit` | 15:06:20.838 | +12404 s | +12404.135316 |

编排方【定序依据】给出的 5 个关键秒差（16747 / 20410 / 14438 / 4 / 71）**逐项吻合**；`SEAL_CHRONOLOGY.md:81-93` 双口径亦吻合。**能证明**：当前盘上这 10 个字段的值、以及「若字段未被改动则 seal 的 mtime 晚于 V1 各输出」。**不能证明**：「确系事后」、谁写的、看过什么（`SEAL_CHRONOLOGY.md:111-117`）。

### 2.3 ★ ctime 异常：324 秒组合成立，但**不是异常，更不是伪造证明**

C1 精确值：
```
seal          mtime = 1794220384.9740431  (18:33:04.974)   ctime = 1794220056.272236  (18:27:36.272)
seal_builder  mtime = 1794220380.4750667  (18:33:00.475)   ctime = 1794220380.4750667
seal.mtime − seal.ctime = 328.701807 s
builder.mtime − seal.ctime = 324.202831 s  →  整数 324 s
```
组合成立（编排方【定序依据】`seal_times` / `builder_times` 与 C1 一致）。`lead/seal_chronology_20261109/_sc_ctime.py:4-30` 是最早记录该组合的 seed 脚本；`_sc_probe_out.json:12-13` 记 `ctime_local 18:27:36` / `atime_local 20:18:12`。

**★ 复核回件指出的被核件事实错误（本会话独立复现，必须收窄）**：`lead/ordering_evidence_20261109/_oe_verify.py:86` 把 `impossible_under_normal_fs = seal.ctime < builder.mtime` 置 `True`，`_oe_ORDERING_EVIDENCE.md:60` 与被核 `evidence` 串原样复述。**这是错的**：

- C6 实跑：写域新建 `_oew_ctime_probe.tmp`，同路径覆写后 `ctime_changed_on_overwrite=False / mtime_gt_ctime_after_overwrite=True`；再 `os.utime(p,(atime, mtime-1000))` 后 `mtime_changed_by_utime=True / ctime_changed_by_utime=False`。⇒ Windows 上 `os.stat().st_ctime` 是**创建时间**，不是 POSIX 元数据变更时间；**mtime > ctime 是普通覆写后的常态**。
- C1 全库扫描 `lead/` 下 9,616 件：`mtime−ctime>0` 有 **5,261** 件、`>60s` **873** 件、`>300s` **523** 件、**超过 seal 自身 328.701807 s 的有 506 件**（例 `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` 798,834.888 s）。复核回件 C4 的 9,580 / 5,231 / 868 / 521 / 505 是同一时刻稍早的点值，本会话点值随并发写入漂移，方向一致。⇒ `seal_delta_is_unusual = False`，连「异常」都算不上，更非 `impossible`。
- 因此 `_oe_ORDERING_EVIDENCE.md:221`「证据级只此一件被实证异常」须收窄为「**只有本件的具体 324 s 组合被逐件核对**」；且该模式在 Windows 下本身正常、对全库任何文件都不带伪造含义。

**自然成因（第二载体，本会话独立复现）**：CLI 会话库 `C:\Users\Administrator\.zcode\cli\db\db.sqlite` 的 `part` 表（`mode=ro`），C1 `_oew_verify_out.json:db.rows` + C2 `_oew_2_out.json:db_rows_detail`：

| rowid | `time_created` | 事件 | seal |
|---|---|---|---|
| 635245 | 18:27:31.093 | `Write` 创建 `_cr_build_seal.py` | — |
| **635250** | **18:27:35.515** | `Bash` 首次跑 builder | `bytes=3905`、`sha256=f1a55901379e44c81a88b7f8f0ceab99a8038fc12a55cd819dfa8bd05f6d1006` |
| 635535 | 18:32:59.231 | `Edit` 改 builder（加 `evidence_span_sha256`） | — |
| **635544** | **18:33:04.197** | `Bash` 二次跑 builder（同路径覆写） | `bytes=4395`、`sha256=63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23` |
| 635552 | 18:33:11.549 | `Edit` 校验器常量 `old_string`=`f1a559…1006`/3905 → `new_string`=`63ebd274…ca23`/4395 | — |

⇒ 目录项 18:27:36 首次创建、18:33:04 同路径覆写；生成器 18:32:59 被改、其 ctime/mtime 一起到 18:33:00。**无需任何 `SetFileTime`**。「seal 的 ctime 早于其生成器 mtime 324 s」是「两次生成 + 覆写」的自然结果。

**能证明**：至少两次生成、同路径覆写、mtime 与 ctime 反映不同历史事件（最后写 vs 目录项创建）。**不能证明**：有人伪造过 mtime / ctime、不能证明「确系事后」、不能证明标注者看过答案。被核件 `:76` 已把结论收窄到「不能由该组合实证被分别设置」，**方向正确**；本件进一步指出该组合在本平台连异常都不算。另：被核件 `:106` 称 ctime「可被 `NtSetInformationFile` 类接口改」——本会话**未实跑该接口，标未验**；可写性依据是 `os.utime` / `SetFileTime` 的接口事实（`SEAL_CHRONOLOGY.md:111`、`ORACLE_SPEC.md:121`），不是本组合的推论。

### 2.4 atime 信息量 = 零，且被核查者自身读盘污染

- 编排方【定序依据】`seal_times.atime = 21:04:04`；`_sc_probe_out.json:13` = `20:18:12`；C1 十件 atime **8 个不同值**（22:19:40 ~ 22:37:15）；C2 对 `lead/seal_chronology_20261109/_sc_ctime.py` 记 `atime_before = 22:37:47.320`，仅 `read_bytes()` 一次后 `atime_after = 22:38:46.475`，`changed_by_our_own_read = True`（Δ=59.155153 s）。复核回件 C3 亦记 `22:04:08.052 → 22:09:10.762`。
- ⇒ atime 记「最近一次被读」，会被任何核查者改写；Windows 还有 last-access 延迟/关闭策略。**不承载生成/写入先后**，不能作「谁在何时看过」的证据。**不可用**（逐项判定见 §3）。

### 2.5 「元数据可分别设置」的意义 = 一类证据整体降级，不是「无法定序」

精确划分（**不许用「元数据不可靠」一句概括**）：

1. **适用范围 = 全库方法论级**：可写性是 `SetFileTime` / `os.utime` / `touch` 的通用接口属性，对 `lead/` 下任何文件同样成立；`ORACLE_SPEC.md:121` 已把 mtime / git commit 时间 / 邮件 Date 头 / 第三方 push 时间统一列为「**B 弱旁证（不抵赖）**」。今后所有仅凭本地三时间得出的「确系事前/确系事后」一律不可作。
2. **降级不是归零**：仍可证「当前盘上此刻该字段的值」及「若字段未被改动则的相对先后」。结论须写成「在当前可见 mtime 下 A 晚于 B / 不能排除事后」。
3. **不扩散到内容层**：C1 八件指纹全 MATCH、C8 `READONLY_ALL_UNCHANGED=True`；哈希 / 集合 / 引文等**内容强制**证据不受影响。
4. **★★ 还有什么能用**：① 内容因果链（§3①、§4 甲）；② CLI 会话库 `part` 表行序 + `time_created`（§3⑤）；③ 闭合注册表 / 构造性恒等（§5）；④ 多载体 `old→new` 引用链（§3⑤）；⑤ OS 日志 / USN / VSS（§3⑦，本案未取到）；⑥ commit-then-reveal + 带外见证（§4 乙/丙，制度级设计）。**「元数据不可靠 ≠ 无法定序」的落点即这些**。

---

## 3 定序依据清点（七类逐项）

统一记号：**能证明** = 该依据自身未被改动假设下可推出的最小命题；**不能证明** = 越界部分；**可用 / 部分 / 不可用** = 对本案能否实跑取到并用于定序。

| # | 依据 | 判定 | 能证明什么 | 不能证明什么 | 密码学强制 vs 可写 |
|---|---|---|---|---|---|
| ① | **mtime**（10 件秒差） | **部分可用**（弱旁证） | 当前字段值；「若未被改则 A 晚于 B」⇒「不能排除事后」 | 「确系事后/事前」、谁写的、看过什么、语义真值、抗同域双改（`CERT_REAL_CHECK.md:509`） | **可写**（`os.utime`/`SetFileTime`/`touch`）；非密码学强制。C1 十组秒差全复现 |
| ② | **ctime**（324 s 组合） | **部分可用**（更弱） | 目录项创建/文件创建时刻；本例实证「两次生成、同路径覆写」 | 内容最后写入时刻、文件「诞生」唯一时刻、任何认知状态；**不能证明伪造** | **可写**（`NtSetInformationFile` 类接口**未验**）；Windows 下 `mtime>ctime` 为常态（C6 + C1 全库 506 件反例） |
| ③ | **atime** | **不可用** | 仅「最近一次被读」 | 生成/写入先后、谁读过、读了什么 | **可写且自动被污染**（C2 `changed_by_our_own_read=True`）；零定序信息 |
| ④ | **git 跟踪 / commit 历史** | **本例不可用（零覆盖）／机制上部分可用** | 若已跟踪：commit DAG 父子 + tree/blob 哈希构成内容绑定的顺序；已发布 commit 难静默改写 | 未跟踪文件的一切；本地 commit 时间可改（`GIT_COMMITTER_DATE`）；未 push 可 rebase/amend；不可否认性 | commit 对象由 SHA-1 **内容寻址（内容强制）**；但**时间字段可写**、仓库本地可重写、无签名时不带身份。C4：六目录 `git log` 全 0 行、5 RO 目录全 `??`、`ls-files --error-unmatch` `rc=1`、HEAD `2657458` 为 11-01 |
| ⑤ | **CLI 会话库 `db.sqlite` 的 `part` 表行序 + `time_created` + 完整 stdout** | **部分可用（本案最强现有旁证，第二载体）** | 实跑给出 `635245→635250→635535→635544→635552` 记录链与两次 builder 完整 stdout、`old→new` 常量替换；可证「同一会话内事件的**记录顺序**」；与文件 mtime/ctime 三元组交叉自洽（ctime 18:27:36 ↔ 首次生成 18:27:35.515；mtime 18:33:04 ↔ 二次生成 18:33:04.197） | 绝对物理时刻（本地时钟可改）；rowid 严格 = 全局真实先后（C1 窗口 635000–636000 的 1001 行中 **182 次** `time_created` 倒退）；`count=622897 < max(rowid)=648627`（约 2.5 万 rowid 缺口）、有 `time_updated` 列 ⇒ **不是 append-only 日志**（标签松动，见下）；DB 本地 sqlite 可写；不能判认知状态 /「未见 V1」 | **本地 sqlite 可写、无签名、非密码学强制**；由 CLI 运行时自动追加，伪造需同时改文件系统与 DB |
| ⑥ | **内容交叉引用 / 哈希因果链** | **部分可用 → 内容强制方向** | 若 B 的字节里出现 A 的 sha256（或逐字引文 + 行号），则**该版本 A 必先于该版本 B**。C1：seal 自身 64-hex 在 `_cr_real_verify.py` / `CERT_REAL_CHECK.md` / `ORACLE_SPEC.md` / `_os_ORACLE_SPEC.md` / `SEAL_CHRONOLOGY.md` / `_sc_SEAL_CHRONOLOGY.md` **6/6 全命中**；`_cr_real_verify.py:44-47` 硬编码该 sha 与 `4395` | **反向**（A 晚于 B 不能由哈希单向证明）；「引用者是否相信/看过」；同域双改可同时伪造（`CERT_REAL_CHECK.md:509`）。**★ 复核指出的引用错类**：被核件 `:110/:160` 称「seal 的 5 个 `file_sha256` 出现在 `_r9s_regress_out.json` ⇒ seal 先于该引用件」——C7 定位这 5 个 hash 的确切 JSON 路径全为 `/four_domains/*/mainSha256`（4 个主件文件哈希，`脚本存在性`/`可重建` 同为 `593c7a3e…`），**并非 seal 自身字节的引用**，属共享上游文件的巧合，不构成 seal→regress_out 的内容因果；真正的内容因果是 seal 自身 sha 在 6 份引用件中命中 | **内容强制（密码学级偏序）**：sha256 单向，无法「先写 B 再让 A 的 hash 撞上」；但**载体文件可写**，需带外锚才抗同域双改 |
| ⑦ | **目录项顺序 + OS 日志 / USN / VSS / 4663** | **部分可用（有载体，本案未取到记录，标未验）** | `os.scandir` 枚举顺序（按名称排序，**非创建序**）；C5 `fsutil usn queryjournal D:` `rc=0`（journal 存在、Max 256 MB、`Next Usn` 本会话点值 `0x4006c22e8`，复核回件记 `0x4005dd898`、被核件记 `0x400452a58`，属点值漂移）；`vssadmin list shadows` `rc=0` 唯一 `C:` 卷影 `2026/11/9 13:52:54`；若取到对应记录可给独立于 mtime 的写入序列 | C3 点名命令 `timeout 45 sh -c 'fsutil usn readjournal D: \| grep -a -i -m 12 "_cr_seal\|_cr_build_seal"'` → **`rc=124`（超时、0 字节）**；`wevtutil ... 4663 /c:1` `rc=0` 输出空（未启用或未记录，未进一步验）；VSS 是 **C:** 卷、项目在 **D:**、13:52:54 早于 seal 18:33:04 ⇒ 对本案无可用快照；USN 环形缓冲可能已覆盖；仍不能判「改本地时钟」或认知状态。**未解析 MFT / `$I30`，标未验** | 日志由 OS 内核写（比用户态 mtime 难改），但**可管理员清除/停审、可改系统时钟**；**非密码学强制** |

**★ 密码学 / 内容强制者：仅 ⑥ 的哈希因果链（及 ④ 中 git blob/commit 内容寻址）。** 其余（mtime / ctime / atime、git 时间字段、sqlite、MFT 属性、日志/审计、系统时钟）**全部可写**。

**★ 无 PKI 现状下最强依据是什么（分两问，不可混）**：

- **「本案现已存在、能实跑取到的最强」= ⑤ CLI `part` 表行序 + 完整 stdout，由 ⑥ 内容因果链交叉加固**。理由：与文件 mtime **不同源的第二载体**、CLI 运行时自动追加、`old_string` 逐字引用前一次 hash（内容自洽不依赖时间）。**但只是制度级/旁证级**：DB 本地可写、时钟可改、行序有倒退实证。`ORACLE_SPEC.md:127` 定义仍成立：「无 PKI 的上限 = 可复核的管道 + 制度担保的隔离」。
- **「方法论上最强、无 PKI 也能构造」= 带外 commit-then-reveal + 内容哈希锚**（§4 乙/丙；`SEAL_CHRONOLOGY.md:138-141`、`:278-283`，`ORACLE_SPEC.md:131-133`）：`t0` 把 `H(P)` 放到被测方 A **无写权**载体，`t1` 交 `H(labels)`，`t2` 才跑 V1。密码学强制的是「内容不可回改」，时间先后靠「带外载体不可被 A 写」这一**制度事实**。
- **真正把时间做成密码级事实的是 M2**（`git commit -S` / minisign / sigstore + 公钥指纹带外公布，`ORACLE_SPEC.md:132`）或 **M3**（RFC3161 TSA + 透明日志，`:133`）。C1 `signature_sidecars_cert = []`；`SEAL_CHRONOLOGY.md:125-126/:274` 亦记 `n_repo_signature_sidecars=0`、无内嵌 `timestamp/nonce/witness`。⇒ **现状不可否认性 = 0**（`ORACLE_SPEC.md:125`）。

**★ 标签松动（复核回件 ③，如实登记）**：被核件 `:109/:124/:151` 多处称 `part` 表为「append-only 行序」，而 C1 实测有 `time_updated` 列、`count < max(rowid)`、本地 sqlite 可写；该文件自己在 `:109/:151` 已承认「非 append-only 日志、本地 sqlite 可写」，属**内部措辞不一致，非结论错误**。本件统一改称「CLI 运行时自动追加的 `part` 表行序（非 append-only 日志）」。

---

## 4 替代方案：把「时间先后」换成「依赖先后」

不再问「A 的写入时刻 < B 的写入时刻」（需可信时钟），改问：① **内容依赖**（B 含 A 的 sha256 / 逐字引文 ⇒ A 版本先于 B 版本）；② **承诺依赖**（`H(A)` 在 `t0` 被放到 A 无法回写的载体）；③ **机制依赖**（B 的生成脚本硬编码 A 的结构）。三者**只给偏序、不给绝对时刻**，且都**不判认知状态**（`ORACLE_SPEC.md:123`「读没读过，从产物上不可判定」）。

**要救的命题**（`_fnr_check.py:73-76`，经 `SEAL_CHRONOLOGY.md:165` 引）：ORACLE 必须「produced **BEFORE V1 is run**, by an adjudicator who **does not see V1's outputs** and **did not author V1**, with a **published SHA256 seal**」。方向是**「seal 早于 V1」**，另含独立性、认知状态、带外发布。

| 方案 | 做法 | 强度 | 代价 | ★ 对本案能否救 |
|---|---|---|---|---|
| **甲 内容因果链 / 哈希链** | B 逐字含 A 的 sha256 / 行号引文，验证方重算 `sha256(A_bytes)`；更好是 `H_n = sha256(H_{n-1} ‖ content_n)`（Merkle/追加链） | **密码学级偏序**（内容强制、抗碰撞假设）；不给绝对时刻；不抗同域双改（需带外锚，`CERT_REAL_CHECK.md:509`） | 极低：已有 `hashlib`；需预先约定「引用谁」且 A 字节冻结 | **不能救（方向错 + 缺失）**。要证「seal 先于 V1」须 V1 产物字节里出现 seal 的 sha；C1 自扫 5 份 V1 产物 `SEAL_SHA_IN_V1_ANY = False`、`seal_full_sha_present=false` 全件、`seal_prefix16_present=false` 全件。反向却成立：seal 自身 sha 在 6 份引用件全命中、`_cr_real_verify.py:44-47` 硬编码全 sha + `4395`（C1 `verifier_constant` 双 True）⇒ 证得「seal 先于这些引用件」，**不是「seal 先于 V1」**。且 C2 DB 链显示 seal 生成 18:27/18:33、V1 输出 12:50–14:32，方向是 **晚**。甲反而把「晚」用内容链加固 |
| **乙 commit-then-reveal** | `t0` 公布 `H(P)` 到 A 无写权载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / ≥2 见证人各留副本 + 带 Date 头回执）；`t1` 交 `H(labels)`；`t2` 才跑 V1；验收 `t0<t1<t2` 且 `sha256(P)==H(P)` | **制度级 `t0<t1<t2` + 密码级内容绑定**；`ORACLE_SPEC.md:127` 定义的无 PKI 上限；不可否认性仍 0（`:125`） | 中：≥2 见证人 / 公开只读载体 / ACL 隔离日志；302 项双盲全标注 ≈50.33 人时、端到端 60–95 人时（`SEAL_CHRONOLOGY.md:329`、`ORACLE_SPEC.md:309`） | **不能救本案（事后无法补做）**。`t0` 必须在 V1 之前；C4 seal 与六目录全 `git log` 0 行、`?? untracked`；C1 无签名 sidecar；`SEAL_CHRONOLOGY.md:125-127/:274` 记 seal 顶层仅 `items`/`seal_version`（`_cr_seal.json:1-135` 实读），无 `timestamp/nonce/witness`、无 append-only 日志。**现在补公布 `H(seal)` 只能证明「从现在起没改」**，不能追溯成 V1 之前的预注册。即便当初做了，也仍买不到「未见 V1 输出」（`ORACLE_SPEC.md:123`、`SEAL_CHRONOLOGY.md:144/:284`） |
| **丙 带外见证 / 第三方时间戳** | 第三方记「收到 `H(P)`」的时刻与内容；升级 = **M2** `git commit -S` / minisign / sigstore + 公钥指纹带外公布；再升级 = **M3** RFC3161 TSA + 透明日志（CT 式 append-only） | M2 把「谁、何时、哪份内容」绑定到人，T1/T4/T6/T8 由制度级升密码级（`SEAL_CHRONOLOGY.md:330`）；M3 时序成为可验证事实、真正不可否认（`:331`） | M2 低（一对现成密钥，无需自建 CA）；M3 高（采购/自建 PKI、TSA、透明日志运维）；人力成本三者共享不可压缩 | **对「seal 早于 V1」不能救**：无任何 `t0` 之前带外记录（同乙；`SEAL_CHRONOLOGY.md:132` 明记「本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据」）；C5 VSS 是 **C:** 卷且 13:52:54 早于 seal、项目在 D:；C3 USN `rc=124`；4663 空。**对「seal 晚于 V1」**：⑤ 的多载体记录已把它做成**强旁证**（仍非密码级）。纯「第三方记 wall-clock」只抵御改 mtime，**不抵御改本地时钟**（`SEAL_CHRONOLOGY.md:142`） |
| **丁（补充）OS 只追加日志 + 卷影** | USN / 4663 / 第三方备份 / 另一卷 VSS 快照 | 中：独立于用户态 mtime；能证「某时刻存在某版本」 | 中高：需**事前**启用审计与保留策略；USN 环形缓冲会覆盖 | **不能救**（本案未取到，C3/C5） |
| **戊（补充，本案已实证有效）多载体会话日志 + `old→new` 引用链** | CLI 运行时把每次工具调用（命令 + 完整 stdout）自动追加到与产物不同源的 DB；`Edit` 的 `old_string` 逐字引用上一版 hash | **中（旁证级）**：跨载体一致性使伪造须同时改产物与日志；内容层由哈希加固；无签名故不可否认性 0 | 低（本库天然具备，C1/C2 直接读到）；代价是必须**承认 DB 可写** | **不能救「早于」**，但能给出可用的方向性定序（旁证级，同上） |
| **己（补充）闭合注册表 / 构造性恒等分析** | 不读时间，直接查「候选集是否被上游 SPECS/白名单闭合决定」 | **高（机制级、content-enforced）**，但证明「依赖/同源」而非「时间戳」 | 极低：读源码 + 集合运算 | **不能救「早于」**，但能给出机制级结论（§5） |

**★ 总判断**：甲 / 乙 / 丙 **没有一个能把本案救成「seal 是 V1 之前的独立预注册」**。原因不是证据不够，而是**命题方向与实测记录相反 + `t0` 承诺载体缺失**：V1 产物里没有 seal 的 hash、无 `t0` 带外承诺、且第二载体记录显示 seal 生成于 V1 之后。三者**都买不到「标注者未见 V1 输出」这一认知状态**（`ORACLE_SPEC.md:123`）。`SEAL_CHRONOLOGY.md:169-174/:189-191/:350` 的 `前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED` 本会话复核后**维持不变**；本件只补充「成因可解释（两次生成）」与「第二载体的强旁证」两点。**不许把救不回来写成能救。**

---

## 5 ★★★★ 三重相等分析（5 项 == whitelist == flips）

### 5.1 事实复核

C1 `triple_equality` + C2 `AST_sets`（AST 静态解析源码，**不 import、不执行**）：

```
n_items = 302（_scv_sets_out.json:6-7 / :13-16：302 互异，coverage=5/302，missing=297，negatives=0）
n_seal_items = 5   n_flips = 5   n_whitelist_literal = 5   n_SPECS_keys = 5
n_ITEMS_literal = 5   n_CERTS_keys = 5
seal_eq_flips = True   seal_eq_whitelist_output = True   seal_eq_whitelist_literal = True
seal_eq_ITEMS_literal = True   seal_eq_CERTS_keys = True
seal_tokens_eq_SPECS_keys = True   seal_tokens_eq_spec_inventory_keys = True
SPECS_keys = ['可重建','实跑输出','改前改后','脚本存在性','需谁批准']
flips_all_whitelisted = True   n_tightens = 0   flips_outside_whitelist = []
```

来源：`lead/cert_realcheck_20261109/_cr_seal.json:1-135`（顶层仅 `items` / `seal_version`，`author`/`truth` 自写）；`_cr_build_seal.py:22-78` 的 `ITEMS` 5 对字面表；`lead/gate_r9sem_20261109/_r9s_regress.py:112-119` 的 `WHITELIST` 硬编码 Set 字面量（注释「本次任务书指名要求改判的 5 处」）、`:199-206` 输出 `flips`/`whitelist`；`_r9s_predicates.py:371-402` 闭合 `SPECS` Dict、`:405` `r9s_element_present` 未登记 token 直接 `return False`；`lead/falsifiable_no_relax_20261109/_fnr_check.py:314-351` 的 `CERTS` 同 5 键同 `independent_blind_adjudicator` 串。

### 5.2 巧合概率估算（若三者独立）

设候选池 `I` = 302 个互异 `(domain, token)` 对（N=302），取 k=5。C1 `combinatorics` 三法独立算（`math.comb` / 阶乘 / 迭代）：

```
C(302,5) = 20,248,875,010  （≈2.0249×10¹⁰，log₁₀ = 10.306400899623716）
all_equal = True
p_pair_if_independent  = 1/C(302,5)     = 4.93854596616427e-11   （约 1/202 亿）
p_3way_if_independent  = 1/C(302,5)^2   = 2.4389236259917386e-21 （约 1/4.1×10²⁰）
若候选池收窄为含已登记 token 的 10 对：C(10,5)=252
  p_pair = 1/252   = 0.003968253968253968
  p_3way = 1/252^2 = 1.5747039556563368e-05
```

复核回件 C1/C5 的 20,248,875,010 / `4.93854596616427e-11` / `2.4389236259917386e-21` / 252 与本会话**逐位吻合**。

**★ 但独立性假设在本案不成立，上述数字不能当「巧合概率」用**：源码 AST 证明 `SPECS`（闭合 5 键）== `spec_inventory` 5 键 == `ITEMS` 5 对 == `CERTS` 5 键 == seal == flips == whitelist，`r9s_element_present` 对未登记 token 直接 `return False` ⇒ `flips_outside_whitelist=[]`、`n_tightens=0` 是**设计后果**。C1 `construction_mechanism.all_four_sources_equal = True`、`conditional_probability_of_equality_given_code = 1`。⇒ 三重相等是**构造性恒等（by construction）**，条件概率 = 1；`2.4e-21` 仅是独立性假设下的**反事实数**。`SEAL_CHRONOLOGY.md:206-224`「不是巧合，是构造性恒等」判定**维持**。

**★ 复核回件 ④ 指出的 1 处过度外推（本会话独立复现，须收窄）**：被核件 `:200` 称「白名单/SPECS 在 V1 输出之前就存在…V1 输出 13:53:57 / 14:32:26」、`:191` 称 12:59:07「早于全部 V1 输出」——只挑了较晚的两件。C2 `whitelist_vs_V1`：`_gp_regression_v1_union_out.json` mtime **12:51:07.919**、`_gp_regression.py` **12:52:54.833**，均早于白名单注释首现 `rowid=620123 / 12:56:18.016`；C1 DB 另查到 `rowid=619829 / 12:50:36.847` 写 `_gp_regression.py`，其内容已含字串 `_gp_regression_out.json`。⇒ `claim_whitelist_before_ALL_V1_outputs_is_literally_false = True`，**「早于全部 V1 输出」字面上不成立**。
但 C2 `db_tokens` 给出 5 个 token 在 DB 的最早提及：`可重建` 2026-06-21 17:51:50.199、`改前改后` 2026-09-11 17:27:42.293、`实跑输出` 2026-09-27 11:09:25.031、`需谁批准` 2026-11-08 23:53:02.354、`脚本存在性` 2026-11-09 00:57:51.462，加上 `_r9s_regress.py:112` 注释「本次任务书指名要求改判的 5 处」，故「**选择无需看 V1 输出**」仍可由任务书预置支撑——措辞应改为「**依赖被测方预置白名单/SPECS，该选择机制先于本次 V1 回归运行；不早于每一份 V1 产物的 mtime**」。**结论不变**。

### 5.3 ★ 若不是巧合，相等本身是不是「见答案」的证据？

必须分开两命题（否则犯 `SEAL_CHRONOLOGY.md:224` 指出的措辞不精确）：

| 命题 | 判定 | 依据 |
|---|---|---|
| **P1「标注时看过 V1 回归输出」** | **不能由此相等证明** | 认知状态产物上不可判定（`ORACLE_SPEC.md:123`）；选择可由任务书预置白名单得出（§5.2 收窄） |
| **P2「标注集与被测方答案集/白名单同源，故 ORACLE 不由被测方独立派生」** | **★ 成立，且是内容/机制强制，比时间戳更强** | C1/C2 七源集合全等；`_cr_build_seal.py:30-31`、`:41-42`、`:52-53`、`:64-65`、`:75-76` 的 `oracle.truth=True` 与 `author="independent_blind_adjudicator"` 全是生成器内自写字符串 |

**「比时间戳更强」的确切含义**：时间戳（mtime / ctime / atime / DB `time_created`）都是**可写元数据**，只给「不能排除」级弱旁证；集合相等 + 闭合注册表是**读字节即可复算、不依赖任何时间字段**的结构事实，改时间不能改变它、改内容会改变 sha256（C1 八件指纹 + C8 `READONLY_ALL_UNCHANGED=True` 已冻结）。它直接推出 `(A) ∀i: V0=0 ∧ V1=1 ⇒ ORACLE=1` 变成**恒真重言式**（`SEAL_CHRONOLOGY.md:232`）、`ORACLE_SPEC.md:109` 的 C3「不可派生」判 FAIL、「标注独立」在**机制层面不可能成立，与认知状态无关**（`:224`）。
**但仍不能推出**：「标注者看过 V1」「有意作弊」「语义真值为伪」「`NO_RELAXATION` 为假」「mtime 曾被伪造」。准确表述 = `SEAL_CHRONOLOGY.md:224` 原文「**依赖被测方预置白名单/SPECS，该依赖早于 V1 输出；且 seal 本身在当前可见 mtime 下晚于 V1 4h39m7s、不能排除事后**」（本件把「早于 V1 输出」按 §5.2 收窄为「早于本次 V1 回归运行、不早于每一份 V1 产物 mtime」）。

### 5.4 能否替代时间证据？——**前提层能替代，时序层不能替代**

- **能替代**：判「预注册 / 独立性」原本要靠 `t0<t1<t2` 时间戳；P2 不依赖时间就能判 `_fnr_check.py:73-76` 的 ②③「未见 V1 输出 / 不可由 V1 派生」「身份独立」**机制上不满足**（`author` 只是字符串、选择由闭合注册表决定）。⇒ `SEAL_CHRONOLOGY.md:170-171` 这两条内容证据**更强且足够**，`前提层不成立` 不因时间元数据被降级而动摇。这正是「元数据不可靠 ≠ 无法定序」的落点。
- **不能替代**：① ①「产于 V1 之前」是纯时间先后命题，相等在 seal 早于或晚于 V1 时都成立；② 不给绝对时刻 / 不给 `t0`；③ 不判「确系事后 / 标注者看过答案」；④ 不能救 §4 的「seal 早于 V1」。
- ⇒ **判词**：内容证据是**前提层的充分替代**，是**时序层的不充分替代**；二者分层，不得互相降格或冒充（`SEAL_CHRONOLOGY.md:180-183`）。

---

## 6 复核回件（绑定行格式）+ 结论 + 未验项

### 6.1 复核回件

编排方【复核】给出 `verdict = partial`（`ranCommands = 27`），本件按交付要求**如实记为 `unconfirmed`**（`refuted` 或 `partial` 均标 unconfirmed）。复核 `sha256Line` 含 9 行严格格式绑定行，逐行复算 C1 全 MATCH；本件自身绑定行见篇首与 §6.2。

复核七项结论与本会话独立实跑的对照：

| 复核项 | 复核判 | 本会话复现 |
|---|---|---|
| ① 八件指纹 + 绑定行 + 文档计数 | 成立 | C1 `FINGERPRINTS_ALL_MATCH=True`、`REVIEWED_MATCH_BASELINE=True`、`n_strict_hits=1` |
| ② ★ ctime 组合 + 自然成因 + **事实错误** | 组合成立、成因成立、**但 `impossible_under_normal_fs` 标签错** | C1/C6：Windows ctime=创建时间、全库 506 件超 328.7 s ⇒ 本件 §2.3 收窄，且**更强化「无伪造证据」** |
| ③ 逐项表 + **标签松动** | 8 行均有双列；「append-only 行序」措辞与 DB 有 `time_updated` / rowid 缺口冲突 | C1 `count<max(rowid)`、窗口 182 次倒退 ⇒ 本件 §3 统一改称「自动追加的行序（非 append-only）」 |
| ④ ★★ 三重相等 + **过度外推** | 组合数逐位对、构造性恒等判定正确；「早于全部 V1 输出」字面不成立 | C1/C2 全复现 ⇒ 本件 §5.2 收窄，结论不变 |
| ⑤ 三方案能否救 + **引用错类** | 全判不能救正确；5 个 `file_sha256` 是 `four_domains.mainSha256` 非 seal 引用 | C7 全件确认 ⇒ 本件 §3⑥ / §4 甲更正 |
| ⑥ 适用范围 + 需收窄的一处 | 全库方法论级判对；`:221`「只此一件被实证异常」与 505/506 件反例冲突 | C1 全库扫描支撑 ⇒ 本件 §2.3 收窄 |
| ⑦ 越界检查 | 152 件 RO 域未被改、无新 seal、未 commit | C4 HEAD 未变、写域 `??`；C8 8/8 未变；C1 `signature_sidecars_cert=[]` |

**★ 不改变最终结论**：`前提层不成立` / `INTEGRITY_OK_BUT_UNCONFIRMED`（`SEAL_CHRONOLOGY.md:174`、`:350`）复核后维持。复核指出的两个点名陷阱均未踩：未「笼统说元数据不可靠」（§3 逐项 8 行双列）、未「救不回来也说能救」（§4 总判断）。

### 6.2 绑定行（固定格式，本件 §6 复核回件必须含）

以下九行逐件为「实跑命令 C1 + 输出」得到的指纹；每行采用铁律规定的固定格式：`被核对象` + 空格 + `SHA256` + 等号 + 空格 + 完整 64 位十六进制（中间不得插入路径、括号、星号、反引号或空格）+ 中文逗号 + `字节数` + 等号 + 空格 + 数字：

被核对象 SHA256 = 5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f，字节数 = 45423
被核对象 SHA256 = 09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7，字节数 = 9590
被核对象 SHA256 = e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657，字节数 = 1126
被核对象 SHA256 = 5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156，字节数 = 52542
被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395
被核对象 SHA256 = 2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574，字节数 = 5376
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969，字节数 = 45567

> 前 8 行 = 编排方【编排方实跑指纹】八件；第 9 行 = 被核件 `_oe_ORDERING_EVIDENCE.md`（复核 `sha256Line` 第 9 行）。篇首另有一行同格式的 63eb…ca23 / 4395 为本件的**对象绑定行**。C1 校验被核件 `n_strict_hits=1` 且 hash/bytes 等于磁盘 seal。

### 6.3 结论

1. **「元数据不可信」的适用范围** = **全库方法论级**（可写性是 API 事实，对 `lead/` 下任何文件同样成立，`ORACLE_SPEC.md:121`）；**证据级**只有「本件 324 s 组合被逐件核对」，且该模式在 Windows 下**本身正常**、对全库任何文件都不带伪造含义（C1 全库 506 件反例）。**不扩散到内容层**（C1/C8 指纹全 MATCH）。
2. **已有 mtime 论证要不要重审** = **不全部重审，按 mtime 的角色分三类**：A. mtime 为唯一主判据且结论「确系 / 因此被漏」→ 需重审改写；B. mtime 为旁证、主判据是哈希/内容 → 不需重审；C. 仅描述性陈述 → 不需重审但保留「这是文件 mtime」限定。依据（C2 `ledger_selfwarnings` 实读）：`GOAL_THREE_TARGETS_20261018.md:8859`（「mtime 不自动等于异常发生时间」）、`:9170`（`test_06_rewritten_same_content`：同内容重写 sha 同 mtime 变）、`:9171`（`test_10_run_start_anchor_is_corroboration_only`，「明确否决 naive A（纯 mtime）方案」）、`:9340`（T2 = 「B 跑前基线哈希主判据 + A 加固版 mtime 旁证」）、`:4595-4597`（吻合 ≠ 真实状态，编排方【清点】字段引）。⇒ 做一次「A 类清单化筛查」，**不做全库推倒**；本会话只做 grep + 定点读，**未穷举全库 A 类论证，标未验**。
3. **以后做时序论证的准则**：① 时间字段只作旁证，结论一律带「在当前可见 X 下 / 不能排除」，atime 直接弃用；② 优先内容强制偏序（把 `H(A)` 写进 B / `old_string` 逐字引用 A，重算 `hashlib.sha256`），更稳用哈希链 `H_n = sha256(H_{n-1}‖content_n)`；③ 承诺必须在被测方写域之外（`SEAL_CHRONOLOGY.md:269-275` T8），验收须模拟同域双改仍 FAIL（`CERT_REAL_CHECK.md:509` 现状是 PASS 故 T8 不成立）；④ **commit-then-reveal** 固定 `t0<t1<t2`，事后补公布只证「从现在起未改」；⑤ 升级 **M2**（`git commit -S`/minisign/sigstore）或 **M3**（RFC3161 + 透明日志），现状无签名 sidecar；⑥ 事前启用 USN / 4663 / 另一卷 VSS（本案 C3/C5 事后取不到）；⑦ 多载体交叉（产物 + CLI 会话库 + 校验器常量 + 台账），遇「ctime 早于生成器」先查两次生成/覆写；⑧ 分离管道层 / 前提层 / 时序层 / 认知层，不互相冒充（`:176-185`）；⑨ 先查闭合注册表，若候选集被 SPECS/白名单闭合决定，直接判「选择依赖 / 不可派生 FAIL」，不必绕时间戳；⑩ 阴性结论只记某一时刻点值，不把字节数/目录数/`Next Usn` 当可引用定值（`:130`）。
4. **总判**：本案 seal 在当前可见的**两个独立载体**（文件 mtime/ctime + CLI `part` 表）下生成记录**晚于 V1**，且 5 项恰等于被测方预置白名单 → `前提层不成立`、`INTEGRITY_OK_BUT_UNCONFIRMED` **维持**；三方案无一能救成「V1 之前的独立预注册」。

### 6.4 未验项（如实列，不补造）

1. **判不了「seal 确系事后生成」、也判不了「mtime/ctime 曾被人为伪造」** —— 本会话反而给出「两次生成 + 覆写」自然成因（§2.3）；`NtSetInformationFile` 类接口改 ctime **未实跑，未验**。
2. **判不了 seal 与 V1 的绝对真实先后** —— 无带外时间戳 / 无签名 / git 对 11-09 六目录零覆盖 / CLI DB 仍是本地可写文件 + 本地时钟。只能说「在当前可见 mtime/ctime 与 CLI DB 两个独立载体下，seal 生成记录晚于 V1 输出记录」。
3. **判不了「标注者是否看过 V1 输出」这一认知状态** —— `ORACLE_SPEC.md:123` 产物上不可判定；本会话只判集合相等与构造链。
4. **判不了语义真值 / 302 项语义裁决 / `NO_RELAXATION`** —— 未重读 32 主件全文逐项重判；5/302 覆盖、0 负例、0 `UNVERIFIABLE`（`SEAL_CHRONOLOGY.md:201-204/:359-361`）。
5. **判不了不可否认性 / 抗同域双改现状达标** —— 无 PKI / 签名 / RFC3161；C1 无伴随签名件；`ORACLE_SPEC.md:125` 技术上限为 0；**本会话未重跑** `CERT_REAL_CHECK.md:509` 同域双改攻击（只读纪律，沿用既有输出件）。
6. **判不了「三层独立互证 / 置信度量化」** —— 相关失效叠加；κ、p_o、CI、总体 fp/fn 率无第三方标签（`:361`）。
7. **判不了本库 A 类 mtime 论证的完整清单** —— C2 只做 grep + 定点读，未做全库穷举扫描，**未验**。
8. **判不了 NTFS 目录项真实创建顺序 / MFT `$I30` 索引序** —— 只登记 `os.scandir` 枚举顺序（按名称排序，非创建序），**未解析 MFT，未验**。
9. **判不了 USN 是否留有 `_cr_seal.json` 写入记录** —— C5 `fsutil usn queryjournal D:` `rc=0` journal 存在，但 C3 `readjournal` 45 s `rc=124`；`wevtutil ... 4663 /c:1` `rc=0` 输出空，未进一步判「未启用审计」还是「无记录」，**未验**。`Next Usn` 三次读数（`0x400452a58` / `0x4005dd898` / `0x4006c22e8`）为点值漂移，不作定值。
10. **判不了 VSS 对本案的适用性** —— C5 唯一卷影是 **C:** 卷 `2026/11/9 13:52:54`，项目在 **D:** 且 seal 18:33，无可用快照；未列全所有卷 / 所有 shadow，**未验**。
11. **判不了 302 项清单外部完备性 / 交付件确由某次实跑产生** —— `_os_ORACLE_SPEC.md:288/:489` 明记未验。
12. **判不了零真机下的一切运行时行为** —— 未启动任何游戏进程、未写采样/hook 代码；未跑 `_cr_real_verify.py:main()` / `_fnr_check.py:main()`（前者会回写 `_cr_verify_out.json`、后者会回写只读域，见 `SEAL_CHRONOLOGY.md:367`），管道层判断依据是读源码 + 指纹/集合复算。
13. **§4 全部甲/乙/丙/丁/戊方案均未执行**（只做清点与设计要求）—— 全部标「设计，未验」；未生成新 seal。
14. **CLI 库命中数 / 行数 / 窗口倒退数是某一时刻点值** —— C1 `count=622897 / max_rowid=648627 / size=3,419,279,360 B`，与复核回件 `621173 / 645981`、被核件 `618737 / 644467` 不同，属并发写入漂移；只把「命中/未命中」当结论。
15. **复核回件 C2 记 `immutable=1` 读活库曾触发 `database disk image is malformed`（rc=1）** —— 本会话用 `mode=ro` + 5 次重试**未遇到**该错误，如实记为「本会话未复现」。
16. **C2 python-embedded USN 管道一次 `rc=255`** —— Git Bash 引号包装问题，已按点名命令原样重跑 C3 得 `rc=124`；两值均登记，不隐瞒。

### 6.5 纪律核对

- 唯一写域 `lead/ordering_evidence_20261109/`；本件新增前缀 `_oew_`：`_oew_verify.py` / `_oew_verify_out.json` / `_oew_2.py` / `_oew_2_out.json` / `ORDERING_EVIDENCE.md`。C6 的 `_oew_ctime_probe.tmp` 已 `unlink`。
- 六只读域及两件台账：C8 `READONLY_ALL_UNCHANGED = True`（8/8 编排方指纹 sha + bytes 全等）；**未修改、未追加、未覆盖**。
- C4 `git status --porcelain -- lead/ordering_evidence_20261109/` = `?? lead/ordering_evidence_20261109/`；HEAD 仍 `26574589aa8401e8f3f2934680a1ea7109bafa2d 2026-11-01T19:35:33+08:00`；**未 commit、未 push**。
- **未改任何既有件、未生成新 seal**；C1 `signature_sidecars_cert = []`。指纹一律 `hashlib`；Python 一律 `python -I -X utf8` + 绝对路径。
- 引用均追到「实跑命令 + 输出」或「文件:行」；未验项已明确标注，未补造。
