# seal 时序核查与两层分离评估（`_sc_`，2026-11-09）

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

（本行按铁律格式固定，`被核对象` = `lead/cert_realcheck_20261109/_cr_seal.json`；本会话实跑 `_sc_probe.py` 用 `hashlib.sha256` 对其 `read_bytes()` 重算，与编排方【编排方实跑指纹】一致；`ORACLE_SPEC.md:283` 用同一串，故沿用同一被核对象。格式中数字间未插入路径/括号/星号/反引号/空格。）

---

## 0 本会话实跑清单（全部零真机、零采样、纯离线只读盘 + 新写域）

| # | 命令（原样） | 用途 / 输出 |
|---|---|---|
| 1 | `mkdir -p "D:/Project/ra2-campaign-forge/lead/seal_chronology_20261109"` | 创建唯一写域 |
| 2 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/seal_chronology_20261109/_sc_probe.py"` | 10 件 mtime/bytes/sha256 + 10 个编排方指纹比对 + 9 组时差；输出见 `_sc_probe_out.json` 与本文件 §1 |
| 3 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/seal_chronology_20261109/_sc_ctime.py"` | NTFS CreationTime 与 mtime 分离、seal.CreationTime 与各 V1 件的差 |
| 4 | `powershell -NoProfile -Command "... Get-Item ... CreationTime/LastWriteTime/LastAccessTime"` | 独立读 10 件 NTFS 三个时间，与 Python `os.stat` 交叉核对 |
| 5 | `python -I -X utf8 -c "<读 _fnr_check.py:60-90 / :135-160 / :350-368；_cr_build_seal.py 全文；_cr_real_verify.py:40-50 / :75-100 / :104-135 / :450-470；CERT_REAL_CHECK.md:385-400 / :500-515 / :525-550；_os_ORACLE_SPEC.md:170-184 / :212-228 / :425-450 / :478-492；ORACLE_SPEC.md:115-138 / :281-310 / :290-295；WHITELIST_AUDIT.md:465-470 / :496-518；_WL_WHITELIST_AUDIT.md:464-468 / :484-486>"` | 逐行读关键判据 |
| 6 | `python -I -X utf8 -c "<读 _r9s_regress_out.json 实算 302 项 / flips / whitelist / seal 5 项集合相等>"` | 实算 `n_items=302`、`distinct=302`、`seal items == whitelist pairs ? True`、`== flips ? True`、`5/302=0.016556`、`missing=297` |
| 7 | `python -I -X utf8 -c "<读 _cr_seal.json 结构、_crdoc_colocated_out.json 全文>"` | `top_keys=['items','seal_version']`、`n_items=5`、5/5 `truth=True`、`oracle keys=['author','predicate_author','truth']`；共址改写输出 `VERDICT=PASS, n_pass=5, n_fail=0` |
| 8 | `git log --format='%h %cI' -- <8 件>` / `git ls-files <6 目录>` / `git status --porcelain -- <6 目录>` / `git reflog -5` | 8 件全部 `git log` 空、6 目录 `ls-files=0`、6 目录 `??` untracked、HEAD 3 提交均在 2026-11-01 |
| 9 | `python -I -X utf8 -c "<扫 CLI 日志 zcode-2026-11-09.jsonl / rollout jsonl / .claude/projects / .codex/sessions / %TEMP% zcode-bash-*>"` | 见 §1(c)，**未找到**任何 seal 生成时刻的独立带外记录 |
| 10 | `python -I -X utf8 -c "<收尾重算 10 件编排方指纹>"` | `ALL_TEN_UNCHANGED_END = True`（逐件 `UNCHANGED`） |

`ranCommands` 计 10 组前台命令（含若干 `-c` 内联读盘/算指纹）；全部只写 `lead/seal_chronology_20261109/` 下 3 个新件：**未改任何既有件、未生成任何新 seal、未 commit、未 push**。收尾 `git status --porcelain -- lead/seal_chronology_20261109/` 仅 `?? lead/seal_chronology_20261109/`。

---

## 1 第一步：复核时序

### 1(a) 10 件 mtime 逐项 + seal 与 V1 的精确差

实跑 #2 输出（本机时区 `中国标准时间` = UTC+8，`time.timezone=-28800`；`local` 与编排方表逐项一致）：

| tag | 文件 | mtime (local) | mtime (UTC) | epoch | bytes | sha256（前 12） |
|---|---|---|---|---|---|---|
| seal | `lead/cert_realcheck_20261109/_cr_seal.json` | 2026-11-09 18:33:04 | 10:33:04 | 1794220384 | 4395 | `63ebd27428c1…` |
| seal_builder | `…/_cr_build_seal.py` | 18:33:00 | 10:33:00 | 1794220380 | 5376 | `2e539d392b0a…` |
| real_verify | `…/_cr_real_verify.py` | 18:34:15 | 10:34:15 | 1794220455 | 21178 | `3d8ab1092ebf…` |
| **V1_reg_out** | `lead/gate_pipeline_20261109/_gp_regression_out.json` | **13:53:57** | 05:53:57 | 1794203637 | 38575 | `d3543657aa4f…` |
| V1_reg_py | `…/_gp_regression.py` | 12:52:54 | 04:52:54 | 1794199974 | 13017 | `1804e5bfb4c3…` |
| V1_union_out | `…/_gp_regression_v1_union_out.json` | 12:51:07 | 04:51:07 | 1794199867 | 37461 | `68c7ecd3aafc…` |
| r9s_pred | `lead/gate_r9sem_20261109/_r9s_predicates.py` | 13:00:28 | 05:00:28 | 1794200428 | 23111 | `b0265fc57ef4…` |
| r9s_reg_out | `…/_r9s_regress_out.json` | 14:32:26 | 06:32:26 | 1794205946 | 75673 | `5bfb169acc58…` |
| fnr_check | `lead/falsifiable_no_relax_20261109/_fnr_check.py` | 16:11:22 | 08:11:22 | 1794211882 | 28811 | `94d89881f6a2…` |
| wl_audit | `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | 15:06:20 | 07:06:20 | 1794207980 | 52705 | `f9d00b7c9a12…` |

**seal − V1（实跑 #2 逐项算）**：

- `seal − V1_reg_out = +16747 s = 4h 39m 7s` ← 与编排方 `delta_seal_minus_V1_seconds=16747` / `delta_human=4h 39m 7s` **完全一致**
- `seal − V1_reg_py = +20410 s = 5h 40m 10s`（背景写「5h40m」，精确 5h40m10s）
- `seal − V1_union_out = +20517 s = 5h 41m 57s`
- `seal − r9s_pred = +19956 s = 5h 32m 36s`
- `seal − r9s_reg_out = +14438 s = 4h 0m 38s`
- `seal − fnr_check = +8502 s = 2h 21m 42s`；`seal − wl_audit = +12404 s = 3h 26m 44s`
- `seal − seal_builder = +4 s`；**`seal − real_verify = −71 s = −0h 1m 11s`**（背景表未点破：校验器比封印晚 1m11s 才落盘）
- 10 件编排方指纹逐项 `sha=MATCH bytes=MATCH` → 10/10；两件台账 mtime 亦复现 2026-11-08 22:26:42 / 2026-11-06 06:53:04（与 `ORACLE_SPEC.md:349` 同）

⇒ **10/10 mtime 逐项与编排方表一致，seal 晚于所有 V1 件，`seal_after_V1=true` 复现成立。**

另一个独立的「另一轮实跑」：`_os6_audit_out.json:checks.C3_mtime` 记 `seal_later_than_v1_regress_output = true`、`note: "mtime is a weak circumstantial signal only; no trusted timestamp exists"`（实跑 #5 读取）。这是**同一机器同一文件系统**上的第二次读，不是独立的时钟源。

### 1(b) ★ mtime 能被伪造：「seal 晚于 V1」能证明什么、不能证明什么

**能证明**：
1. 在**当前盘上、以当前文件系统元数据为准**，`_cr_seal.json` 的 mtime 比 `_gp_regression_out.json` 晚 16747 秒；若两者 mtime 均未被改动，则按 `_fnr_check.py:73`「produced BEFORE V1 is run」的**字面时序条件不成立**。
2. 由此**不能排除「事后」**：即不能排除 seal 是在看到 V1 输出之后才写成的。这是本证据唯一稳健的方向性内容（且是「不能排除」而非「确系」）。
3. 与内容证据合看，还能证明「seal 的 5 项恰是被测输出集合」这一**与事后构造相容**的事实（§3(b)）；但这是内容层，不是 mtime 层。

**不能证明**（逐条，严格区分）：
- **不能证明「确系事后」**：mtime 是用户态可写元数据（`SetFileTime` / `touch` / `os.utime` / 复制时保留或重置），本地时钟亦可改。`ORACLE_SPEC.md:121` 把 mtime 列在「**B 弱旁证（不抵赖）**」，注明「本地时钟可改；无 RFC3161 时不能作不可否认证据」。
- **不能证明 seal 的作者/标注者「看到了 V1 输出」**：这是认知状态，`ORACLE_SPEC.md:123` 明写「**读没读过，从产物上不可判定**……任何『未见』自述都是信任声明，不是可检验事实」。
- **不能证明 seal 曾被伪造 / 也不能证明未被伪造**：mtime 与内容 hash 是两回事；`_cr_seal.json` 的 sha256 只绑定字节，不绑定写入时刻（`_cr_real_verify.py:82-92` 只比对 hash 与字节数，无时间字段）。
- **不能证明 `NO_RELAXATION` 为假**：`NO_RELAXATION` 是 `_fnr_check.py:78-91` 的 (A)–(E) 合取，时序只是其中的**前提**之一；前提不成立只使判定**不可作**，不等于判定为假。
- **不能证明管道失效**：`_cr_real_verify.py` 的技术行为与 seal 何时生成无关（§2(a)）。

★ 一句话：**「mtime 晚」⇒ 只能得到「不能排除事后 / 预注册的时序条件在当前可见证据下不成立」；它不能得到「确系事后」「标注时看过答案」「语义真值为伪」「管道坏了」中的任何一个。**

### 1(c) 其它独立时间证据？给搜索方向

**本会话实跑搜索结果（#8/#9）— 均为阴性或弱旁证**：

| 候选 | 实跑 | 结果 |
|---|---|---|
| git 历史 | `git log --format='%h %cI' -- <8 件>`、`git ls-files <6 目录>`、`git status --porcelain -- <6 目录>`、`git reflog -5` | 8 件 `git log` 全空；6 目录 `ls-files=0`；6 目录全部 `?? untracked`；HEAD 三次提交都是 2026-11-01 19:30–19:35，**晚于 11-09 的这批文件** ⇒ git 对 11-09 时序**零覆盖** |
| NTFS CreationTime / 三时间分离 | PowerShell `Get-Item` + Python `os.stat`（#3/#4） | 见 §1(d)：方向一致，但同属本地可写元数据 |
| 文件内嵌时间戳 | `grep -rn "generated_at\|timestamp\|labeled_at\|created_at\|ran_at\|2026-11-09 1[3-9]:" <4 个 json>` | 0 命中；`_cr_seal.json` 顶层仅 `items`/`seal_version`，无 `timestamp`/`nonce`/`witness`（`ORACLE_SPEC.md:75` 亦记「无时间戳字段」） |
| CLI 会话库 | `~/.zcode/cli/log/zcode-2026-11-09.jsonl`（121,745,546 B）、`~/.zcode/cli/rollout/*.jsonl`、`~/.claude/projects`（135 文件）、`~/.codex/sessions`（244 文件）、`~/.claude/history.jsonl`（668 行）、`~/.zcode/cli/agents/session_*`（27 个，均 ≤11-08） | 11-09 CLI 主日志中 `_cr_seal.json` / `SEAL WRITTEN` / `_cr_build_seal` / `PRE-REGISTERED` / `63ebd27428c1` **命中数全 0**；`.claude/projects` / `.codex/sessions` 中 11-09 文件数 = **0**；`%TEMP%` 下 61 个 `zcode-bash-*` 会话目录的日志中含 seal sha 前缀者 **0**；仅**本次**工作流的 rollout 日志有 1 条命中（是本会话自己的读操作，非生成时刻） |
| 既有另一轮 mtime 记录 | `_os6_audit_out.json:C3_mtime`、`ORACLE_SPEC.md:81` | 同一文件系统第二次读，非独立时钟 |

⇒ **本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据。** 注意：`~/.claude/history.jsonl` 末行有 `timestamp=1793187297784`（毫秒 epoch）与 `project`/`sessionId` 形态，说明 CLI 会话库**具备**带时间戳的记录能力；但 11-09 的这批文件没有对应的会话记录可查到（其他 CLI 的日志目录未在本次授权范围内穷举，标**未验**）。

**搜索方向（给下一轮，未执行）**：
1. `~/.zcode/cli/rollout/`、`~/.zcode/cli/log/` 按 11-09 12:00–19:00 时间窗过滤 `tool_use` / `Bash` 记录，找 `_cr_build_seal.py` 的 stdout（`SEAL WRITTEN`、`sha256 = 63ebd274…`）的出现时刻；注意 CLI 日志本身也由同一账号可写，**只是弱旁证**。
2. 其它 CLI 的会话库（`~/.claude/projects/**/*.jsonl`、`~/.codex/sessions/2026/11/09/`、`~/.cursor`、`~/.gemini`）按文件名 `_cr_seal.json` 反查首次写入时刻。
3. 仓库外带外载体：邮件 Date 头、公开 gist / 第三方仓 push 时间、CI 工件时间戳、Windows 事件日志 / USN 变更日志（`fsutil usn`）、VSS 卷影副本、EDR/杀软文件审计日志。这类才可能构成**独立**证据。
4. 若存在 `git commit -S` + RFC3161 / sigstore / 透明日志，则可直接把 `t0<t1<t2` 升为密码级；现状 `ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`、`repo_signature_sidecars=[]`，**无**。

### 1(d) 若 mtime 被伪造过，还有什么办法独立定序？（给方案，不执行）

按证据强度递增；每条注明它能否抵御「伪造者同时改本地时钟/元数据」：

1. **内容级单向锚定（不依赖任何时钟）**：把 seal 的 `sha256` 写进**在 V1 之前已存在且不可改**的介质——V1 回归脚本/输出的注释、早期台账的既有行、既有 commit 的 message/tree。若 V1 产物字节里出现 seal 的 64-hex，则 seal 必早于该 V1 产物（前提：V1 产物自身字节未被改写，其 sha256 已在编排方指纹里冻结）。**反向定序**（seal 晚于 V1）无法用哈希做单向证明，只能靠「V1 产物里没有 seal 的承诺」+「带外时间戳」。实跑：本会话未在 V1 输出中搜到该 64-hex（标**未验**，未系统穷举键树）。
2. **commit-then-reveal + 带外载体（M1，`_os_ORACLE_SPEC.md:216-222`、`ORACLE_SPEC.md:131`）**：`t0` 把 `H(P)` 发到 A 无写权的载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / 两名见证人各留副本 + 含 Date 头回执）；`t1` 交 `H(labels)`；`t2` 才跑 V1；要求 `t0<t1<t2`。抵御本地时钟伪造，但**只到制度级**（`ORACLE_SPEC.md:127`：「无 PKI 的上限 = 可复核的管道 + 制度担保的隔离」）。
3. **M2 现成身份体系（`ORACLE_SPEC.md:132` 推荐）**：`git commit -S` / minisign / sigstore / 机构 SSO 短时效 token；把「谁、何时、哪份内容」绑定到人。仍是「签名时刻」而非「认知状态」，但比 mtime 强得多。
4. **M3 RFC3161 可信时间戳 + 透明日志（append-only / Merkle）**：`ORACLE_SPEC.md:133`「把时序做成可验证事实而非弱旁证」。这是唯一能把「确系事后 / 确系事前」判成密码级事实的路径。
5. **文件系统级旁证**：NTFS USN journal、卷影副本、Windows 安全审计（4663 文件写入）、第三方备份。可抵御「改 mtime」但抵御不了「改本地时钟」；且**仍不能判「未见 V1 输出」**（`ORACLE_SPEC.md:123`）。

★ **无论哪条都不能判「标注者没看过答案」**——那是认知状态，产物上不可判定，只能靠 ACL 日志 + 双盲分片 + commit-then-reveal 做制度担保（`ORACLE_SPEC.md:123, :161`「内容绑定 ≠ 认知状态绑定」）。

### 1(d)-补 一个本会话实测的 mtime 可塑性旁证（方向性，非伪造证明）

实跑 #3/#4：

- `_cr_seal.json`：`CreationTime=18:27:36`、`mtime=18:33:04` → **相差 328 s**，即该路径/文件对象在 18:27:36 已存在、18:33:04 被最后写入；
- `_cr_build_seal.py`（自称生成 seal 的脚本）`CreationTime=mtime=18:33:00`，比 seal 的 CreationTime **晚 324 s**；
- `_gp_regression_out.json`：`CreationTime=12:50:43`、`mtime=13:53:57`（相差 3797 s，回归重跑覆盖）；
- 按 CreationTime 定序：`seal.CreationTime − V1_reg_out.CreationTime = +20213 s = 5h36m53s`，`− r9s_reg_out.CreationTime = +19871 s = 5h31m11s`，方向仍一致。

含义：**mtime 与 CreationTime 可以不一致、且能分别被设置**——这正是「mtime 只是弱旁证」的具体表现。但请注意：这**不是**「有人伪造过 mtime」的证据（更可能是生成器在同一路径上先写后覆写 / 首次试跑残留），也未改变方向。它只能说明「时间元数据不是单一、天然可信的写入时刻」。**未验**：USN/文件系统日志未读，不能判定该 328 s 的真实成因。

---

## 2 第二步：把两层结论彻底拆开（本任务核心）

### 2(a) 管道层：`_cr_real_verify.py` 的技术正确性独立于 seal 的时序吗？

**判断：独立（技术上完全独立）；但「管道好」这个结论的适用范围也随之被限定。**

实读 `_cr_real_verify.py`：

- `:44-47` 硬编码 `PRE_REGISTERED_SEAL_SHA256 = "63ebd274…ca23"` / `EXPECTED_SEAL_BYTES = 4395`；
- `:77-97 load_seal()`：`seal_path.read_bytes()`（`:82` 注释 `REAL disk read`）、`hashlib.sha256(blob)` 重算（`:85`）、字节数与 hash 双比对，失配 → `SEAL_BYTES_MISMATCH` / `SEAL_INTEGRITY`；
- `:119-131`：调用方 `anchor` / `quote` / `roles` 必须与封印记录逐字相等，否则 `ANCHOR_NOT_PRE_REGISTERED` / `QUOTE_NOT_PRE_REGISTERED` / `ROLES_NOT_PRE_REGISTERED`；
- `:108-117`：ORACLE 取自封印、忽略调用方布尔（`:104-106 CALLER_BOOLEAN_KEYS`）；`:112-114` 的独立性唯一判据只是**字符串不等** `author != predicate_author`。

这些是**确定性的读盘 + 哈希 + 逐字比较**，其正确性与「封印何时生成」「谁生成」「是否看过 V1」在逻辑上无依赖关系：给定相同的封印字节，今天跑和 V1 之前跑，`load_seal()` 的输出完全一样。本会话实跑 #2 复算 `_cr_seal.json` = `63ebd274…ca23` / 4395 B，与 `:44-47` 常量**精确相等**（这是管道自洽的直接实证）；另实跑 #10 收尾复算，10 件只读指纹 `ALL_TEN_UNCHANGED_END = True`。

但**必须限定**：管道只验证「封印字节 == 常量」「被封字节 == 封印所指」「引文/角色逐字在场」。它验证不了「封印所指的字节是 V1 之前冻结的」，也验证不了「`truth=True` 是独立语义裁决」（`CERT_REAL_CHECK.md:530` 明写这是**必要条件**，不是 `ORACLE(i)=1`）。⇒ 时序不影响技术正确性，**但影响这个正确性所能支撑的命题**。

### 2(b) 前提层：seal 的「预注册」性质成立吗？

**判断：不成立（按 `_fnr_check.py:73-76` 的操作化定义，四条全不满足）。**

`_fnr_check.py:73-76` 要求 ORACLE 是「produced **BEFORE V1 is run**, by an adjudicator who **does not see V1's outputs** and **did not author V1**, with a **published SHA256 seal**」。逐条对照：

| 条件 | 证据 | 结论 |
|---|---|---|
| 产于 V1 之前 | 实跑 #2：seal 18:33:04 > V1_reg_out 13:53:57（+16747 s）、> V1_reg_py（+20410 s）、> r9s_reg_out（+14438 s）；`_os6_audit_out.json:C3_mtime.seal_later_than_v1_regress_output=true`；`ORACLE_SPEC.md:81` 同值 | **不满足**（在当前可见 mtime 下；且即使 mtime 被伪造为早，也未建立带外时序） |
| 标注者未见 V1 输出 | 实跑 #6：seal 5 项 == `_r9s_regress_out.json` 的 `whitelist` 5 对 == `flips` 5 条（集合相等输出 `True`），`ORACLE_SPEC.md:87`「⇒ 5 项恰是被测输出选出的 5 对，标注时已见 V1 输出」；`_cr_build_seal.py:2` 自称 phase 1 of a PRE-REGISTERED seal，但 `:20-21` 注释「Verbatim quotes were read from these exact lines of the on-disk deliverables」 | **不满足（内容层面显示选择依赖 V1 输出）**；且认知状态本身产物上不可判定 |
| 未写 V1 / 身份独立 | 实读 `_cr_build_seal.py:30-31, :41-42, :52-53, :64-65, :75-76`：5 处 `author: "independent_blind_adjudicator"` 全是**生成器内自写字符串**；`_cr_real_verify.py:112-114` 唯一判据是字符串不等；`_os_ORACLE_SPEC.md:184` 把该字符串与「字符串比较」「调用方布尔」「本会话自述独立」并列为**明确不算判据**的四类反模式 | **不满足** |
| published SHA256 seal（带外） | 实读 `_cr_seal.json` 顶层仅 `items`/`seal_version`（实跑 #7），无 `signature`/`pubkey`/`timestamp`/`nonce`/`witness`；`ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`、无签名库 import；封印与常量同处 `lead/cert_realcheck_20261109/`（`:44-47` vs `_cr_seal.json`），`CERT_REAL_CHECK.md:509` 实证可同域双改 | **不满足** |

`ORACLE_SPEC.md:295` 亦列「现状四条全不满足（§2d）」。⇒ **所谓「预注册 ORACLE」在 V1 全部跑完之后才生成，且不构成带外预注册。前提不成立。**

### 2(c) ★ 两层各自能支撑什么结论 — 对照表

| 层 | 该层「通过/成立」意味着 | **能说** | **不能说** | 本例状态 |
|---|---|---|---|---|
| **管道层** | 校验器按封印字节正确读盘重算、逐字比较、忽略调用方布尔 | ①「`_cr_seal.json` 的 4395 B 与硬编码承诺 sha256 一致」；②「封印所指 5 个锚点文件的字节/行/引文/角色值逐字在场**且未被篡改**」；③「这些检查是可复核的、确定性的」 | ✗「文本是 V1 之前冻结的」；✗「`ORACLE(i)=1` 语义内容确已交付」；✗「标注独立/盲/未见答案」；✗「封印不可否认 / 抗同域双改」（`:509` 反例）；✗「fp/fn=0/0 可外推为总体率」；✗「`NO_RELAXATION=PASS`」 | **通过**（实跑 #2/#10 指纹一致；`_os_ORACLE_SPEC.md:441-449` 左栏同） |
| **前提层** | ORACLE 由独立第三方在 V1 之前、未见 V1、未写 V1 产出，带带外封印且覆盖全 I | 「标注独立于 V1」「`truth` 是异源语义真值」「(A)/(B)/(C) 有合法输入」「时序满足 `t0<t1<t2`」 | ✗「管道技术正确」（前提不蕴含实现）；✗「文本未篡改」（那是哈希层）；✗ 即使前提成立，仍须 (D) SENSITIVITY 元检验与 (E) 白名单来源才能判 `NO_RELAXATION`（`_fnr_check.py:78-91`） | **不成立**（§2(b) 四条全不满足；`_os_ORACLE_SPEC.md:443-449` 右栏同） |

关键分离：**「文本未篡改」是「语义真值」的必要非充分条件**（`ORACLE_SPEC.md:305`、`CERT_REAL_CHECK.md:530`）。管道层给出必要条件，前提层才可能给出异源真值；两层互不蕴含、互不替代、失效模式不相关——但也**不能反过来当「独立互证」**（`CERT_REAL_CHECK.md:530`「三层又是相关失效叠加，不得当独立互证」）。

前提层**本例成立吗？不成立**。所以「标注独立」这句话在本例**不能说**；`_cr_seal.json` 里的 `author="independent_blind_adjudicator"` 只是字符串，不是独立性的证据（`_os_ORACLE_SPEC.md:184`）。

### 2(d) ★ 「管道好 + 前提假」的准确表述（一句话）

> **校验器能正确证明「某个由被测方自己在 V1 之后写成、且可能看过 V1 输出的 5 项封印」所指的字节逐字在场且未被篡改，因此它证明的是一套可复核的完整性管道，而不是任何独立异源的语义真值或「没放松」。**

更短的口径：`可复核的完整性管道 ≠ 独立异源真值`；或按 `CERT_REAL_CHECK.md:512` 既有措辞「**自证换了套更好的管道**」。注意不要用「证明没放松，只是置信度低一点」这类降格表述——前提假时该结论**根本不可作**，不是置信度问题。

---

## 3 第三步：5 项 vs 302 项的差距

### 3(a) 缺 297 项的后果

实跑 #6：从 `_r9s_regress_out.json` 按 `_fnr_check.py:355-363` 口径复算 `n_items=302`、`distinct (domain,token)=302`、`flips=5`、`whitelist=5`；`_cr_seal.json` `n_items=5`；`5/302=0.016556`，**缺 297 项**。

- **`_fnr_check.py:81` 的 (C) ORACLE COVERAGE `|{i:ORACLE(i) defined}| = |I|` 直接不满足**（5≠302），因此 (A) SOUNDNESS / (B) BOUNDED TIGHTENING 的全称量词 `∀i∈I` 没有合法输入 ⇒ **`NO_RELAXATION` 不能判**（`ORACLE_SPEC.md:110`、`_os_ORACLE_SPEC.md:481`）。
- 覆盖率只在 `detail` 里报告、不是真 FAIL：`_fnr_check.py:151-157` 的 `detail` 有 `n_items` / `coverage_ratio`，`problems` 里没有 coverage 项（`FALSIFIABLE_NO_RELAX.md:170`「(C) 覆盖只报告不门禁」）。⇒ 现有门禁**连「5≠302」都不会报 FAIL**，这一缺口是静默的。
- 按 `_os_ORACLE_SPEC.md:302-304`：302 项里 5 个已登记 token 出现 10 次，其余 **292 项结构性不可能翻案**，`coverage_ratio=0.0331`（按已登记 token 计）；seal 的 5/302 = 0.0166。⇒ 297 项**完全没有语义标签**，既无 `true` 也无 `false` 也无 `UNVERIFIABLE`；按 `ORACLE_SPEC.md:303` 的诚实记账应为 `n_items_sealed = 5/302`、语义真值层 `302/302` 未验。
- **无负例**：5/5 全 `truth=True`（实跑 #7），既不能估假阳性也不能估敏感度；`_os_ORACLE_SPEC.md:435` 要求把 `T1–T8` 全标 `UNVERIFIED`。

### 3(b) ★ 5 项恰好等于白名单 5 对 — 说明什么？（标注时是否已知答案）

实跑 #6 输出：

```
seal items == whitelist pairs ? True
seal items == flips (domain,token) ? True
intersection size = 5
```

5 项逐一对上 `flips` 的 5 条（`需谁批准`/`实跑输出`/`改前改后`/`脚本存在性`/`可重建`）与 `whitelist` 的 5 对；`ORACLE_SPEC.md:87`：「5 项恰是被测输出选出的 5 对，**标注时已见 V1 输出**，违反 `_fnr_check.py:74`」；`_os_ORACLE_SPEC.md:305` 同「用被测输出挑出来的子集」。

**说明**：项的选择不是从 `I` 的 302 项独立清单里抽的，而是**由 V1 的翻案结果 / 白名单决定的**——即先有答案（哪 5 项翻案、哪 5 对被白名单放行），再挑这 5 项来「标注」。这是典型的选择依赖（selection on the dependent variable）。配合 §1(a) 的时序（seal 晚 4h39m）：**内容与时序两条弱证据同向**。

**「标注时是否已知答案」**：本会话能判的是「**产物层面**标注集与 V1 答案集完全相同」，且 `_WL_WHITELIST_AUDIT.md:466` 自警「这批白名单内容恰好是对的，但机制不能证明它对」、`WHITELIST_AUDIT.md:467/:516` 的「人工独立 5/5」是**另一轮复核会话复读原文**的判定。至于「标注者当初心里的认知状态」，按 `ORACLE_SPEC.md:123` **产物上不可判定，本会话判不了**（标「未验」）；但按预注册的判据口径，这种选择方式本身就使「未见 V1 输出」**不可核** ⇒ T3/T4 FAIL。

补充：5/5 全 `truth=True` 且恰好等于「应保留 5 / 应移除 0 / 需补证据 0」（`WHITELIST_AUDIT.md:498`），无一个负例 —— 这与「看着答案标」相容，但同样**不是**该认知状态的证明。

### 3(c) 若 5 项标注是「看着答案标的」，作为「独立真值」的价值是多少？

**作为「独立真值」的价值 = 0**（不是「低」，是零）。理由：

- 独立性的定义就是「不由被测方/被测输出派生」（`_fnr_check.py:73-75`、T5 `_os_ORACLE_SPEC.md:179`「标注内容不可由 V1 派生」）。若标签由答案反填，则 `ORACLE` 与 `V1` 同源，`(A) ∀i: V0=0∧V1=1 ⇒ ORACLE=1` 变成**恒真重言式**，不携带任何关于 V1 是否放松的信息。
- 它仍能保留的价值只有两项，且都**不属于**「独立真值」：①**管道自测样本**（证明读盘/哈希/逐字比较能跑通，`CERT_REAL_CHECK.md:329` 的 `PASS 5/5` 属此类）；②**内容判定可能恰好是对的**（`_WL_WHITELIST_AUDIT.md:466`「内容恰好是对的，但机制不能证明它对」、`WHITELIST_AUDIT.md:516`「5 条白名单内容：可信」）——但「恰好对」不等于「由机制证明对」，不能当 ORACLE。
- 因此 `_os_ORACLE_SPEC.md:419` 明写「实际人工盲标投入 = 0」「5/5 不能按比例外推到 302 项，也不能计入本规范的第三方盲标产出」；`_os_ORACLE_SPEC.md:471` 要求把人工独立 5/5「**作为参考而非 ORACLE**」接入。

### 3(d) 用 5 项支撑 302 项的结论，属于什么错误？与之前的口径错置同类吗？

**属于：以偏概全 / 选择性样本外推（coverage fallacy）+ 口径错置的近亲，但不是同一个口径错置。**

- 主要错误：`_fnr_check.py:81` 要求 `|{ORACLE defined}| = |I| = 302`；用 5 项（且是被测输出挑出的 5 项）去支撑「302 项全量证明没放松」，是**把「子集上可复核」偷换成「全集上成立」**，违反全称量词 `∀i∈I`。`_os_ORACLE_SPEC.md:445` 右栏把「302 项全量证明没放松」明确列为越界；`ORACLE_SPEC.md:274`「不得按比例外推到 302 项」。
- 次生错误：**选择偏差**（样本不是随机抽自 I，而是 `flips`∩`whitelist`），所以连「5/302 的统计外推 + 置信区间」都不合法；更无 `UNVERIFIABLE` / 负例。
- **与「口径错置」是否同类**：既有 `口径错置` 的定义见 `lead/keff_calc_20261109/KEFF_CALC.md:110-112`——把 `fp_rate`（「非断言被误拦率」）当 `fn_rate`（「真断言被放过率」）相乘，是**把一个口径的量代入另一个口径的公式**（量的语义错置）。本例的 5→302 是**同一口径的量被用在不匹配的量化域上**（集合/量词域错置）。二者同属「**量或证据被用于其定义域之外的口径**」这一大类（都是把 A 场景的可复核事实搬到 B 场景当结论），因此**是同类家族**；但**不是同一个具体错误**：一个是「指标定义错置」（误拦率↔放过率、似然↔后验，`KEFF_CALC.md:108-109`），一个是「覆盖域/选择偏差错置」（5 项↔302 全集、被测输出挑样）。回答应写：**同族不同型**，不可混称。
- `ORACLE_SPEC.md:305` 把它归入「越界即错」：可复核的管道 ≠ 独立异源真值；`:299` 只支撑「封印所指 **5 个锚点文件**的字节/行/引文/角色值逐字在场」。

---

## 4 第四步：核「同域双改」这个最严重的漏洞

### 4(a) `:509` 说法核对 — **成立**

实读 `CERT_REAL_CHECK.md:509`（本会话 #5）：原文记载「`_cr_seal.json` 与 `PRE_REGISTERED_SEAL_SHA256`（`_cr_real_verify.py:44-47`）都在 `lead/cert_realcheck_20261109/`」，复核员 Part C / H9「同步重写封印、记录 hash 与模块内常量后，凭空编造的内容 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`」，并记第一次复现漏同步调用方证书得 `NON_PASS`（如实登记），补全后 `python -I -X utf8 ".../_crdoc_colocated.py"` 输出 `VERDICT=PASS, n_pass=5, n_fail=0`、`fake_seal_sha256=482b14b3…ec7fecb`。

本会话交叉核对（未重跑攻击，只读）：
- `_crdoc_colocated_out.json`（实跑 #7 读全文）逐字含 `"VERDICT": "PASS"`, `"seal_ok": true`, `"n_pass": 5`, `"n_stale": 0`, `"n_fail": 0`, `"fake_seal_sha256": "482b14b3de057829065d308e50a3cfea48774ceebd928d1204abee119ec7fecb"`, `"note": "FULL co-located double rewrite: seal + artifact + caller cert + hard-coded constant, all inside the same write domain"`；
- `_crdoc_colocated.py:52`（改交付件字节）、`:55-68`（重写 seal 记录并重算 `file_sha256`/`evidence_span_sha256`）、`:70-73`（**改写 `V.PRE_REGISTERED_SEAL_SHA256` 与 `V.EXPECTED_SEAL_BYTES` 常量**）、`:76-80`（同步调用方证书并调 `verify_all`）——四者在同一写域内同步改写，机制成立；
- `_cr_real_verify.py:44-47` 常量与 `_cr_seal.json` 确在同目录（实跑 #2 路径），`:87-92` 只比对这两个可由攻击者改写的值。

⇒ **「`:509` 同域双改可造出 PASS 5/5」说法成立，且有可复核输出件与脚本支撑。** 本会话**未独立重跑**该攻击（纪律：不改既有件、不生成新 seal；`ORACLE_SPEC.md:77`/`:302`/`:484` 亦标「未重跑，沿用记录」）——如实记为「沿用既有实跑输出，未独立复现」。

### 4(b) ★ 若连承诺都可被同域重写，「预注册」这个概念还有意义吗？

**分析：概念本身仍有意义，但本例的实现使它退化为「零约束的自证」，因此在本例里没有证据价值。**

- 「预注册」的有效性来自**时间 + 写域双重不可回改**：`t0` 冻结 `H(P)`，且承诺在 A 写域之外，之后任何改写都会与带外承诺失配。若承诺与封印、常量、交付件、调用方证书**同处一个可写域**，则攻击者可以「一整套同步重算」，使校验方程 `sha256(seal_bytes) == CONST` 与 `sha256(artifact_bytes) == seal.file_sha256` 同时成立——哈希仍是真的、重算仍是对的，只是**被比较的两个端点都由同一方提供**。此时 `PASS` 只表示「这套自洽方程成立」，与「事前冻结」无关。
- 所以 `CERT_REAL_CHECK.md:509` 的准确含义是：**§3(a)①「封印自身 SHA256 硬编码进校验器」单独不充分，除非常量在攻击者写域之外 / 带外部签名**；`_os_ORACLE_SPEC.md:199` 把「承诺是否被同域双改」列为 A 类纯密码学可查**查不到**的三项之一（另两项「谁算的」「何时算的」）。
- 概念不因此作废：`ORACLE_SPEC.md:118` 把「内容完整性」列为 A 类可查；只要加上 T8 的带外锚定（`_os_ORACLE_SPEC.md:182`），同一个哈希管道立刻恢复「预注册」的约束力。⇒ **缺的是锚，不是哈希；缺的是信任根，不是算法。**
- 但要如实说清：即使补了带外锚，也只能证明「**这份字节在 t0 之前已冻结**」；**仍不能证明「标注者未见 V1 输出」**（`ORACLE_SPEC.md:123`、`:161`「签名前的所见所闻：内容绑定 ≠ 认知状态绑定」）。预注册能买到的是**不可回改**，不是**认知独立**。

### 4(c) T8「抗同域双改」判据可执行吗？

**判据（实读 `_os_ORACLE_SPEC.md:182` / `ORACLE_SPEC.md:112`）**：承诺哈希 + 标注包 + 校验器常量**至少三者之一**位于 `A` 写域之外（带外签名 / 第三方存证 / 公证 / append-only 日志）；检验方法 = 攻击演练：模拟 A 同步重写封印 + 常量 + 内容，要求仍 FAIL（对照 `CERT_REAL_CHECK.md:509` 现在会 PASS）。

**可执行性判断：作为「设计/验收判据」完全可执行；作为「现状门禁」不可执行。**

- 可执行的理由：①**结构性可查**——三者路径/归属可静态枚举，检查「至少一个的写 ACL 不含 A」是确定性判断；②**演练可复现**——`_crdoc_colocated.py:52-80` 已经给出一个可粘贴的四件套同步改写模板，把「至少一个锚在域外」加进去后，重算的端点无法与之匹配，必然在 `_cr_real_verify.py:87-92` 报 `SEAL_BYTES_MISMATCH` / `SEAL_INTEGRITY`；③`ORACLE_SPEC.md:112` 把 T8 列为逐条报状态的门禁，`:303` 要求「同域双改缺口可被显式声明」，`_os_ORACLE_SPEC.md:434` 要求「演练必须报 FAIL」。
- 现状不可执行的理由：①`ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`、`cr_verify_has_sig_or_crypto_import=False`，**没有任何带外锚**；②`ORACLE_SPEC.md:87/:108` 把 C2「预注册 + 抗同域双改」判为 **FAIL：常量与封印同域**；③本会话 #8 实跑 git 6 目录全 `?? untracked`、无签名 commit，也没有 append-only 日志；④因此「至少一者在 A 写域外」这个条件**当前为假**，演练必然给出 `PASS`（`:509` 已实证），判据只能报 FAIL 而不能报 PASS。
- **本会话未执行该演练**（纪律：不生成新 seal、不改既有件；`ORACLE_SPEC.md:484` 记「未重跑」）。标「未独立复跑」。

### 4(d) 在没有 PKI 的现状下，这条能不能做到？

**判断：T8 的「结构性/制度级」版本能做到，`不可否认` 的密码级版本做不到；因此只能做到「抗同域双改」而非「不可否认」。**

- **能做到（M1，`_os_ORACLE_SPEC.md:216-222` 标「推荐」、`ORACLE_SPEC.md:131` 列为下限）**：把 `H(P)` 发到 A 无写权限的载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / 两名见证人各留副本 + 含 Date 头回执），并让 **W 持封印、封印与校验器硬编码常量分域**（`:221`、`:535`）。此时「同步重写四件套」会被域外那份 64-hex 拦住，演练可报 FAIL。`ORACLE_SPEC.md:127` 定义「无 PKI 的上限 = 可复核的管道 + **制度担保的隔离**」。
- **做不到（密码级 / 不可否认）**：`ORACLE_SPEC.md:125`「**不可否认性：无 PKI 时技术上为零**」；`:124` 把「承诺确在 V1 前、W 与 A 无串通、302 清单外部完备性、交付件确由某次实跑产生」列为「无」检验方法、全部只能靠制度；`:121` 把 mtime/git commit 时间/邮件 Date 头/第三方 push 时间统统列为「B 弱旁证（不抵赖）」。⇒ 见证人可以串通、载体管理员可以改、本地时钟可以改，M1 只把攻击成本从「改一个目录」抬到「串通多方」，**不是密码学不可否认**。
- **可低成本升级到密码级（M2，`ORACLE_SPEC.md:132` 标推荐）**：用现成身份体系 `git commit -S` / minisign / sigstore / 机构 SSO 短时效 token，「只需一对密钥 + 公钥指纹带外公布」（`_os_ORACLE_SPEC.md:224`），即可把 T1/T4/T6/T8 从制度级升到密码级，**无需自建 CA**。M3（PKI + RFC3161 + 透明日志）才是完整的不可否认（`ORACLE_SPEC.md:133`）。
- 另注意 §4(b) 的限定：即使 M2/M3 到位，仍不能证明「未见 V1 输出」——`ORACLE_SPEC.md:123`「读没读过，从产物上不可判定」。

---

## 5 第五步：结论与建议

### 5(a) ★ `INTEGRITY_OK_BUT_UNCONFIRMED` 准确吗？

**评价：准确，且是本会话可核证据下唯一不越界的判词；但有两点必须随判词一并声明，否则会被误读。**

- 准确之处：①前半 `INTEGRITY_OK` 对应管道层**实测通过**——实跑 #2/#10 十件指纹全匹配、`_cr_seal.json` 与 `_cr_real_verify.py:44-47` 常量精确相等、`_os_ORACLE_SPEC.md:441-449` 左栏六项可复核事实；②后半 `BUT_UNCONFIRMED` 对应前提层**四条全不成立**（§2(b)）+ 覆盖 5/302（§3）+ 同域双改实证（§4(a)）；③`ORACLE_SPEC.md:293` / `_os_ORACLE_SPEC.md:427` 明确「不是 `NO_RELAXATION=PASS`」，把「未证」与「证伪」分开，符合「拿不到写未验」的纪律。
- 必须随附的两点：
  1. **它是自创判词，不是项目既有 gate 判词**：`ORACLE_SPEC.md:295` 实跑 `grep` 后自述「本规范自创判词……零命中项目既有 gate 判词，未冒认为项目既有判词」。因此不能写成「项目门禁判定为 `INTEGRITY_OK_BUT_UNCONFIRMED`」。
  2. **`INTEGRITY_OK` 只覆盖「封印字节与承诺一致 + 5 个锚点逐字在场」**：它**不覆盖**「封印未被同域双改」——`:509` 的攻击造出的正是 `seal_ok=true` 的 `PASS`。`ORACLE_SPEC.md:303` / `_os_ORACLE_SPEC.md:434` 要求「同域双改缺口必须显式声明，不得隐藏」。所以更严谨的展开是 `INTEGRITY_OK（可复核的完整性管道，含已知同域双改残留缺口）_BUT_UNCONFIRMED（语义真值/独立/全覆盖均未验）`。
- 措辞矛盾如实登记：`_os_ORACLE_SPEC.md:216` 把 M1 标「——推荐」，而 `ORACLE_SPEC.md:132`（主规范，verdict=confirmed）明确取 **M2 推荐**并登记该矛盾（`:289` 残留缺陷②）。本会话按主规范取 M2。

### 5(b) 让前提成立的最小成本路径（M1/M2/M3）— 推荐

**推荐 M2（`ORACLE_SPEC.md:132` 同），理由是「成本几乎不增、把 T1/T4/T6/T8 一次升到密码级」。**

| 方案 | 成本 | 能买到 | 不能买到 |
|---|---|---|---|
| M1（下限）`_os_ORACLE_SPEC.md:216-222` | 带外载体 + ≥2 见证人 + ACL 隔离日志 + commit-then-reveal；**但 302 项双盲标注本身按 `_os_ORACLE_SPEC.md:413` 基准 ≈50.33 人时 / 端到端 60–95 人时、5–8 工作日**（`ORACLE_SPEC.md:309`） | 制度级时序 `t0<t1<t2`、封印与常量分域、T8 演练可报 FAIL | 不可否认性（`ORACLE_SPEC.md:125` 技术上为零）；W 与 A 无串通；「未见」 |
| **M2（推荐）** `ORACLE_SPEC.md:132`、`_os_ORACLE_SPEC.md:224` | 在 M1 上加**一对现成密钥**：`git commit -S` / minisign / sigstore / 机构 SSO token + 公钥指纹带外公布；**无需自建 CA** | 把「谁、何时、哪份内容」绑定到人，T1/T4/T6/T8 升密码级 | 签名前的所见所闻（内容绑定 ≠ 认知状态绑定，`ORACLE_SPEC.md:161`） |
| M3（最强）`ORACLE_SPEC.md:133` | 自建/采购 PKI + RFC3161 TSA + 透明日志 | 时序成为可验证事实、真正不可否认 | 仍需 ≥2 名真第三方 + 双盲 + 302 项全覆盖（人力不减） |

**关键提醒（最小成本不等于最小工作量）**：三者共享同一个不可压缩的成本——`ORACLE_SPEC.md:295` 的四条件（V1 之前 / 未见 V1 / 未写 V1 / published seal）与 `:110` C4 全覆盖，必须「≥2 名具名裁决者各自标全 302 项 + 仲裁 + κ≥0.80 + `UNVERIFIABLE` 单列」（`_os_ORACLE_SPEC.md:220`, `:385-399`, `ORACLE_SPEC.md:309`）。**M2 只是在这条必经流程上补了签名，没有新增人力；M1 省下的只是密钥，省不下 50+ 人时。** 另需工程接入：`CERT_REAL_CHECK.md:395` / `_os_ORACLE_SPEC.md:361` 要求给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 两槽（现状 C3 两个 TypeError），并把 coverage 做成真 FAIL（现状 `_fnr_check.py:151-157` 只在 detail）。

**本会话不执行任何 M 方案**（纪律：只做时序核查与分离评估，不生成新 seal）。

### 5(c) ★ 当前所有「三层/独立/置信度」结论最终应如何表述（一句话）

> **本项目当前只能声称「一套技术正确、可复核的完整性管道 + 全量结构/集合门禁 + 诚实未验记账（VERDICT = `INTEGRITY_OK_BUT_UNCONFIRMED`）」；任何「三层独立互证」「标注独立」「置信度已量化」「没放松」的说法都不成立：三层是相关失效叠加、ORACLE 前提四条全不满足、5/302 覆盖且样本由被测输出挑出，因此语义真值层 302/302 未验。**

依据：`CERT_REAL_CHECK.md:530`（「三层又是相关失效叠加，不得当独立互证」）、`:512`（「自证换了套更好的管道」）、`ORACLE_SPEC.md:305`（必要非充分 / 越界即错清单）、`_os_ORACLE_SPEC.md:435`（T1–T8 全标 UNVERIFIED、`302/302` 未验、`n_items_sealed=5/302`）、`WHITELIST_AUDIT.md:517` / `_WL_WHITELIST_AUDIT.md:486`（「『没放松』的证明：不可信」）。**特别禁止**用「置信度低」「三层独立所以更可靠」「fp/fn=0/0」把 `UNCONFIRMED` 降格成弱 PASS（`_os_ORACLE_SPEC.md:446` 明列 fp/fn 外推为越界）。

### 5(d) 这条工作判不了什么（如实列）

沿用 `CERT_REAL_CHECK.md:541-550`、`_os_ORACLE_SPEC.md:479-490`、`ORACLE_SPEC.md:323-339`，加本会话特有项：

1. **判不了「确系事后」**——mtime 可伪造（§1(b)）；也判不了「mtime 曾被伪造」（未读 USN/审计日志，标未验）。
2. **判不了 seal 生成时刻的真实先后**——无带外时间戳、无签名、无 git 历史（6 目录全 untracked、HEAD 止于 11-01）、CLI 会话库 11-09 无 seal 记录（§1(c)）；本次新增的 CreationTime 也只是同一本地文件系统的另一可写元数据。
3. **判不了「标注者是否看过 V1 输出」这个认知状态**——产物上不可判定（`ORACLE_SPEC.md:123`）；本会话只判了「标注集 == V1 答案集」这一产物事实。
4. **判不了 `ORACLE(i)=1` 语义真值 / 302 项语义裁决**——未重读 32 主件全文逐项重判（`CERT_REAL_CHECK.md:543`、`ORACLE_SPEC.md:322`）。
5. **判不了 `_fnr_check.py:78-91` 的 `NO_RELAXATION`**——(C) 需 302 项盲标（本会话 0 项）、(A)/(B) 需 ORACLE 语义真值（无）、(B) 未实装（`_os_ORACLE_SPEC.md:476`）、(D) 未在 302 全集上跑。
6. **判不了「三层独立 / 置信度」**——三层为相关失效叠加；κ、p_o、CI、总体 fp/fn 率均无第三方标签，5/12 构造语料非随机（`CERT_REAL_CHECK.md:545`）。
7. **判不了不可否认性与抗同域双改的现状达标**——无 PKI/签名（`ORACLE_SPEC.md:125`）；且本会话**未重跑** `:509` 的共址改写攻击（只读纪律 + 未生成新 seal），只核对了既有输出件与脚本。
8. **判不了 302 项验证器实跑成本与结果**——`CERT_REAL_CHECK.md:301` 的 7.482 MB / 7.85 MB 自标「估计，未实跑」；本会话只复算了 302 项**清单**（`n_items=302`）与 5 项封印指纹，未跑 302 项读盘验证。
9. **判不了 302 项清单本身的外部完备性**——`I` 来自 `_r9s_regress_out.json` 32 域 `per_element`，是否等于真实项目域取决于冻结时的人工判断（`_os_ORACLE_SPEC.md:288`）。
10. **判不了零真机下的一切运行时行为**——未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；未验证现盘 R9 升级、未复跑 24/24 负样本、未验证跨项目推广。
11. **判不了交付件「确由某次实跑产生」**——`_os_ORACLE_SPEC.md:489`、`WHITELIST_AUDIT.md:497` 明记未验。
12. **本会话未跑 `_cr_real_verify.py:main()` / `_fnr_check.py:main()`**——前者 `:458-460` 会回写 `_cr_verify_out.json`，后者 `:548-549` 会回写只读域；一律 `importlib`/`-c` 只读替代。⇒ 管道层「通过」的判断依据是**读源码 + 指纹/结构复算**，不是跑校验器 main() 的端到端结果（如实标注）。
13. **判不了其它 CLI 会话库**——`~/.claude/projects`、`~/.codex/sessions`、`%TEMP%` 已查阴性；`~/.cursor`、`~/.gemini`、Windows 事件日志 / USN / VSS 未在本次授权范围穷举，标未验。

---

## 6 纪律核对

- 零真机、零采样代码：全部命令为 `python -I -X utf8` 读盘/算 `hashlib.sha256`/`os.stat`、`powershell Get-Item`、`git log/status/reflog`、`grep`；无进程/内存/注入操作。
- 绝对只读域未动：收尾实跑 #10 重算 10 件编排方指纹 `ALL_TEN_UNCHANGED_END = True`（逐件 `UNCHANGED`），两件台账在内。
- 唯一写域 `lead/seal_chronology_20261109/` 新增 3 件：`_sc_probe.py`、`_sc_probe_out.json`、`_sc_ctime.py`，加本件共 4 件；`git status --porcelain -- lead/seal_chronology_20261109/` 仅 `?? lead/seal_chronology_20261109/`。
- 未改任何既有件、**未生成新 seal**、未 commit、未 push。
- 指纹一律 `hashlib`；引用均追到「实跑命令+输出」或「文件:行」；未验项已明确标注，未补造。
