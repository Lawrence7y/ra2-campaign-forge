# SEAL_CHRONOLOGY.md — seal 时序核查与两层分离评估（2026-11-09）

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

> 本行按铁律格式固定：`被核对象` = `lead/cert_realcheck_20261109/_cr_seal.json`。本会话以 `hashlib.sha256(read_bytes())` 实算，等于编排方【编排方指纹】该件 sha256 与 `ORACLE_SPEC.md:283` 同串；数字之间未插入路径、括号、星号、反引号或空格。§6.1 再给同一行并附格式复验。

**本会话实跑命令清单（全部零真机、零采样、纯离线只读盘 + 唯一写域）**

| # | 命令（原样） | 输出要点 |
|---|---|---|
| 1 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/seal_chronology_20261109/_final_verify.py"` | 自写独立实现：`ORCH_ALL_TEN_MATCH = True`、`TIMING_ALL_MATCH = True`、`delta_seal_v1_int = 16747` / `float = 16747.945093`、`delta_seal_minus_real_verify_int = -71` / `float = -70.432142`、`n_items = 302 distinct = 302 missing = 297 coverage = 0.016556`、`seal_eq_flips/whitelist/flips_eq_whitelist = True/True/True`、`seal_eq_spec_keys_tokens = True`、绑定行正则两处各命中 1 行且 `is64hex=True`；输出落 `_final_verify_out.json`。**首次运行因 `_final_verify.py` 缺 `ctime_local` 键报 `KeyError` 退出 1，已修正后重跑成功（如实登记）** |
| 2 | `python -I -X utf8 -c "<读 _r9s_regress_out.json 结构 / spec_inventory / seal items>"` | `domains32.flips=5`、`whitelist=5`、`n rows=32`；seal `top_keys=['items','seal_version']`、5/5 `truth=True` |
| 3 | `python -I -X utf8 -c "<读 _os6_audit_out.json C3_mtime>"` | `seal_later_than_v1_regress_output=true`，且**已同时列出** `_cr_seal.json 18:33:04` 与 `_cr_real_verify.py 18:34:15` |
| 4 | `python -I -X utf8 -c "<读 _crdoc_colocated.py:1-44>"` | `:30-33` 用 `importlib` 载入 `V`，确认 `:71-73` 改的是**内存模块属性** |
| 5 | `powershell -NoProfile -Command "Get-Item ... CreationTime/LastWriteTime/LastAccessTime"` | seal Creation 18:27:36 / Write 18:33:04；builder 18:33:00；V1 Creation 12:50:43 / Write 13:53:57；r9s_reg_out Creation 12:56:24 / Write 14:32:26 |
| 6 | `python -I -X utf8 -c "<扫 CLI 主日志 / .claude/projects / .codex/sessions / %TEMP% zcode-bash-*>"` | 主日志 125,845,064 B、五个 seal 关键词命中全 0；`.claude/projects` 135 文件、`.codex/sessions` 244 文件、11-09 文件名 0；`%TEMP%` 69 个 `zcode-bash-*` 目录、扫 19 文件、sha 前缀命中 0 |
| 7 | `git log --format='%h %cI' -- <8 件>` / `git status --porcelain -- <6 目录>` / `git reflog -5` / `git log -1` | 8 件 `git log` 全空；6 目录全 `??`；HEAD `2657458 2026-11-01T19:35:33+08:00`；reflog 三次提交均 2026-11-01 |
| 8 | `python -I -X utf8 -c "<逐行读 _fnr_check.py / _cr_real_verify.py / _cr_build_seal.py / CERT_REAL_CHECK.md / ORACLE_SPEC.md / _os_ORACLE_SPEC.md / WHITELIST_AUDIT.md / _WL_WHITELIST_AUDIT.md / KEFF_CALC.md 关键行>"` | 见各节 `文件:行` 引用 |
| 9 | `find lead/cert_realcheck_20261109 -maxdepth 1 -type f \( -name "*.sig" -o -name "*.asc" -o -name "*.p7s" -o -name "*.pem" -o -name "*_pubkey*" -o -name "*.crt" \) -print` | 空（无伴随签名件）；`grep -n "三层" CERT_REAL_CHECK.md` → `:56/:524/:530` |
| 10 | `python -I -X utf8 -c "<从 _final_verify_out.json 算全部 hms 时差与 ctime 差>"` | 9 组整数/浮点差、9 组 CreationTime 差，见 §2.2 |

本会话仅写 `lead/seal_chronology_20261109/` 下 3 个**新件**：`_final_verify.py`、`_final_verify_out.json`、本件 `SEAL_CHRONOLOGY.md`；**未修改任何既有件（含 `_sc_SEAL_CHRONOLOGY.md`、`_scv_*`、`_sc_*`）、未生成新 seal、未 commit、未 push**。

---

## 1 目的与边界

**目的**：只做两件事 ——（一）复核 `_cr_seal.json` 相对 V1 回归输出的**时序**，并严格区分「mtime 晚」能证明与不能证明的命题；（二）把「管道有效性」与「前提成立性」**两层彻底拆开**，逐层给判断，不用「时序有问题」这类概括代替逐层结论。顺带完成 5 vs 302 差距、同域双改、最终表述三项评估。

**边界（铁律）**：

- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。全部命令为 `python -I -X utf8` 读盘、`hashlib.sha256`、`os.stat`、`powershell Get-Item`、`git` 只读、`grep`/`find`。
- 绝对只读：`lead/oracle_spec_20261109/`、`lead/cert_realcheck_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/gate_pipeline_20261109/`、`lead/gate_r9sem_20261109/`、`lead/whitelist_audit_20261109/` 全部件与两件台账，一律不修改、不追加、不覆盖。收尾 §6.6 复算十件指纹 `ORCH_ALL_TEN_MATCH = True`。
- 唯一写域 = `lead/seal_chronology_20261109/`。**不改任何既有件、不生成新 seal**（本会话没有写 `*_seal.json`，也没有调用 `_cr_build_seal.py`；沙箱内既有的 `_crdoc_fake_seal.json` 是上游既有件，本会话只读它的指纹）。
- 不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
- 引用一律追到「实跑命令 + 输出」或「文件:行」；拿不到写「未验」，不补造。
- ★★ **mtime 可被伪造**：「mtime 晚」只能证明「**不能排除事后**」，**不能证明「确系事后」**。本件全篇严格区分这两者；凡涉及 seal 生成时刻的表述，一律带「在当前可见 mtime 下 / 不能排除事后」限定，不写成平叙事实。

**复核 verdict 如实记**：编排方【复核】件给 `"verdict": "partial"`（`ranCommands=26`）。按交付规则「refuted 或 partial 标 unconfirmed」—— 本次 `partial` 触发该规则，故本件判词标 **`unconfirmed`**，不写成 confirmed。详见 §6.1。

---

## 2 上游指纹（十件）+ 时序复核

### 2.1 十件编排方指纹逐项复现（实跑 #1）

自写独立实现（`_final_verify.py`）：对每件 `read_bytes()` 全量算 `hashlib.sha256` 并比 `st_size`，与编排方【编排方指纹】十件的 sha256/bytes 逐项对照 → `ORCH_ALL_TEN_MATCH = True`（10/10 全 `sha_match=True, bytes_match=True`）。逐件实算值：

| # | 文件 | sha256（前 16） | bytes | 判定 |
|---|---|---|---|---|
| 1 | `lead/oracle_spec_20261109/_os_ORACLE_SPEC.md` | `5417fb06fc5ad7b6…` | 52542 | MATCH |
| 2 | `lead/oracle_spec_20261109/_os_audit_out.json` | `c791716862caaa55…` | 80300 | MATCH |
| 3 | `lead/cert_realcheck_20261109/_cr_seal.json` | `63ebd27428c1a011…` | 4395 | MATCH |
| 4 | `lead/cert_realcheck_20261109/_cr_real_verify.py` | `3d8ab1092ebf85ef…` | 21178 | MATCH |
| 5 | `lead/cert_realcheck_20261109/CERT_REAL_CHECK.md` | `fa3a45b7fd96ea8c…` | 53782 | MATCH |
| 6 | `lead/falsifiable_no_relax_20261109/_fnr_check.py` | `94d89881f6a2e1af…` | 28811 | MATCH |
| 7 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f9914…` | 38575 | MATCH |
| 8 | `lead/gate_r9sem_20261109/_r9s_regress_out.json` | `5bfb169acc58221a…` | 75673 | MATCH |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb6…` | 52419 | MATCH |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d412554…` | 759518 | MATCH |

另复现既有草稿 `_sc_SEAL_CHRONOLOGY.md` = 45,423 B / sha `5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f`，与其自述一致；本会话**未修改它**。

### 2.2 十件 mtime 逐项 + seal 与 V1 的精确差（实跑 #1/#10）

本机时区 UTC+8。编排方【时序数据】十件的 mtime 字符串、epoch（整数秒）、bytes，`TIMING_ALL_MATCH = True`（10/10 全 `mtime_str_match / epoch_match / bytes_match = True`）：

| tag | 文件 | mtime (local) | epoch(int) | bytes | sha256（前 12） |
|---|---|---|---|---|---|
| seal | `lead/cert_realcheck_20261109/_cr_seal.json` | **2026-11-09 18:33:04** | 1794220384 | 4395 | `63ebd27428c1…` |
| seal_builder | `…/_cr_build_seal.py` | 18:33:00 | 1794220380 | 5376 | `2e539d392b0a…` |
| real_verify | `…/_cr_real_verify.py` | 18:34:15 | 1794220455 | 21178 | `3d8ab1092ebf…` |
| **V1_reg_out** | `lead/gate_pipeline_20261109/_gp_regression_out.json` | **13:53:57** | 1794203637 | 38575 | `d3543657aa4f…` |
| V1_reg_py | `…/_gp_regression.py` | 12:52:54 | 1794199974 | 13017 | `1804e5bfb4c3…` |
| V1_union_out | `…/_gp_regression_v1_union_out.json` | 12:51:07 | 1794199867 | 37461 | `68c7ecd3aafc…` |
| r9s_pred | `lead/gate_r9sem_20261109/_r9s_predicates.py` | 13:00:28 | 1794200428 | 23111 | `b0265fc57ef4…` |
| r9s_reg_out | `…/_r9s_regress_out.json` | 14:32:26 | 1794205946 | 75673 | `5bfb169acc58…` |
| fnr_check | `lead/falsifiable_no_relax_20261109/_fnr_check.py` | 16:11:22 | 1794211882 | 28811 | `94d89881f6a2…` |
| wl_audit | `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | 15:06:20 | 1794207980 | 52705 | `f9d00b7c9a12…` |

**seal − X 的精确差（实跑 #10）**。整数差 = 各自 `int(epoch)` 相减（= 编排方 `delta_seal_minus_V1_seconds=16747` 的口径）；浮点差 = `os.stat().st_mtime` 原始浮点相减（修正复核缺陷 6：整数差是「先截断再相减」，不是「精确差」）：

| X | 整数差 | 浮点差 | 换算（整数口径） |
|---|---|---|---|
| **V1_reg_out** | **+16747 s** | **+16747.945093 s** | **4h 39m 7s（4h39m）** |
| V1_reg_py | +20410 s | +20410.141 s | 5h 40m 10s |
| V1_union_out | +20517 s | +20517.054 s | 5h 41m 57s |
| r9s_pred | +19956 s | +19956.375 s | 5h 32m 36s |
| r9s_reg_out | +14438 s | +14438.163 s | 4h 00m 38s |
| fnr_check | +8502 s | +8502.298 s | 2h 21m 42s |
| wl_audit | +12404 s | +12404.135 s | 3h 26m 44s |
| seal_builder | +4 s | +4.499 s | 0h 00m 04s |
| **real_verify** | **−71 s** | **−70.432142 s** | 校验器比 seal 晚 0h 01m 11s（浮点 70.432 s）落盘 |

`seal − V1_reg_out = +16747 s = 4h39m7s` 与编排方 `delta_human="4h 39m 7s"` / `seal_after_V1=true` 完全一致。**在当前可见 mtime 下，seal 晚于全部 8 件 V1/前置件，且 `seal_after_V1=true` 复现成立。**

> **修正复核缺陷 5（新发现性被夸大）**：`real_verify` 比 `seal` 晚 71 s **不是本会话或上一轮的新发现**。`ORACLE_SPEC.md:81` 与 `_os6_audit_out.json:checks.C3_mtime` 已同时明列 `_cr_seal.json 18:33:04`、`_cr_real_verify.py 18:34:15`、`_r9s_regress_out.json 14:32:26`（实跑 #3 读得 `seal_later_than_v1_regress_output=true`、`note: "mtime is a weak circumstantial signal only; no trusted timestamp exists"`）。只是编排方【时序数据】的回件表格未列这一项，非源材料未载。本件如实登记出处，不冒称新发现。

**NTFS CreationTime 交叉（实跑 #1/#5/#10）**：PowerShell `Get-Item` 与 Python `os.stat` 一致 —— seal CreationTime 18:27:36、mtime 18:33:04（浮点差 328.701807 s ≈ 328 s = 5m29s）；`_cr_build_seal.py` Creation=mtime=18:33:00，比 seal 的 CreationTime **晚 324.203 s**；V1_reg_out Creation 12:50:43 / Write 13:53:57；按 CreationTime 定序 `seal.Creation − V1_reg_out.Creation = +20213.191 s = 5h36m53s`，`− r9s_reg_out.Creation = +19871.682 s = 5h31m12s`，方向一致。含义：mtime 与 CreationTime 可不一致、可分别被设置，是「mtime 只是弱旁证」的具体表现；**这不是「有人伪造过 mtime」的证据**，成因未验（未读 USN/审计日志）。

### 2.3 ★ mtime 能证明什么、不能证明什么

**能证明（唯一稳健的方向性内容）**：

1. 在**当前盘上、以当前文件系统元数据为准**，`_cr_seal.json` 的 mtime 比 `_gp_regression_out.json` 晚 16747 s（浮点 16747.945093 s = 4h39m7s）；若两者 mtime 均未被改动，则 `_fnr_check.py:73` 的「produced **BEFORE** V1 is run」**字面时序条件不成立**。
2. 由此**不能排除「事后」**：即不能排除 seal 是在看到 V1 输出之后才写成的。注意措辞是「不能排除」，**不是「确系」**。
3. 与内容证据合看，还能证明「seal 的 5 项恰等于被测输出/预置白名单集合」这一**与事后构造相容**的产物事实（§4.2）；但这是内容层，不是 mtime 层。

**不能证明（逐条严格区分）**：

- **不能证明「确系事后」**：mtime 是用户态可写元数据（`SetFileTime` / `touch` / `os.utime`），本地时钟亦可改。`ORACLE_SPEC.md:121` 把 mtime 列为「**B 弱旁证（不抵赖）**」，明记「本地时钟可改；无 RFC3161 时不能作不可否认证据」；`ORACLE_SPEC.md:81` 亦自注「mtime 只是弱旁证」。
- **不能证明 seal 的作者/标注者「看到了 V1 输出」**：认知状态，`ORACLE_SPEC.md:123` 明写「**读没读过，从产物上不可判定**……任何『未见』自述都是信任声明，不是可检验事实」。
- **不能证明 seal 曾被伪造、也不能证明未被伪造**：sha256 只绑定字节，不绑定写入时刻（`_cr_real_verify.py:82-92` 只比对 hash 与字节数，无时间字段）。
- **不能证明 `NO_RELAXATION` 为假**：`NO_RELAXATION` 是 `_fnr_check.py:78-91` 的 (A)–(E) 合取，时序只是前提之一；前提不成立只使判定**不可作**，不等于判定为假。
- **不能证明管道失效**：`_cr_real_verify.py` 的技术行为与 seal 何时生成无关（§3.1）。

★ 一句话：**「mtime 晚」⇒ 只能得到「不能排除事后 / 预注册的时序条件在当前可见证据下不成立」；它不能得到「确系事后」「标注时看过答案」「语义真值为伪」「管道坏了」中的任何一个。** 复核缺陷 2 指出的残留泄漏（把「不能排除事后」写成「确系事后」的平叙事实）在本件全篇已消除。

### 2.4 其它独立时间证据（实跑 #3/#5/#6/#7/#9）— 均为阴性或弱旁证

| 候选 | 实跑 | 结果 |
|---|---|---|
| git 历史 | `git log --format='%h %cI' -- <8 件>`、`git ls-files <6 目录>`、`git status --porcelain -- <6 目录>`、`git reflog -5`、`git log -1` | 8 件 `git log` 全空；6 目录 `ls-files=0`、状态全 `?? untracked`；HEAD `2657458 2026-11-01T19:35:33+08:00`，reflog 三次提交均 **2026-11-01**（早于 11-09）⇒ **git 对 11-09 这批文件零覆盖**。**修正复核缺陷 3（时间关系写反）**：11-01 **早于** 11-09，不是「晚于 11-09 的这批文件」；结论「零覆盖」不变 |
| NTFS 三时间 | PowerShell `Get-Item` + Python `os.stat` | 方向一致，但同属本地可写元数据，非独立时钟源（§2.2） |
| 文件内嵌时间戳 | seal 顶层键实跑 #2 = `['items','seal_version']`；`ORACLE_SPEC.md:75` 记全 JSON 键树/全文扫 `timestamp/签名/…` 全空、无 nonce / witness | 无内嵌时间字段；`n_repo_signature_sidecars=0`、`cr_verify_has_sig_or_crypto_import=False` |
| 伴随签名件 | `find lead/cert_realcheck_20261109 -maxdepth 1 -type f \( -name "*.sig" -o … \) -print`（实跑 #9） | 空 |
| CLI 会话库 | 主日志 `zcode-2026-11-09.jsonl`、`.claude/projects`、`.codex/sessions`、`%TEMP% zcode-bash-*` | 五个关键词 `_cr_seal.json` / `SEAL WRITTEN` / `_cr_build_seal` / `PRE-REGISTERED` / `63ebd27428c1` 命中 **全 0**；`.claude/projects` 135 文件、`.codex/sessions` 244 文件、11-09 文件名 0；`%TEMP%` 69 个会话目录扫 19 文件、sha 前缀命中 0 |
| 另一轮 mtime 记录 | `_os6_audit_out.json:C3_mtime`、`ORACLE_SPEC.md:81`（实跑 #3） | 同一文件系统第二次读，非独立时钟源 |

**修正复核缺陷 8（阴性证据计数随日志增长漂移）**：主日志现 **125,845,064 B**（复核件记 123,531,995 B，草稿记 121,745,546 B），`%TEMP% zcode-bash-*` 现 **69 个**（复核件记 64、草稿记 61）。这些是**某一时刻的点值**，会随并发会话写入而漂移，不是稳定事实；关键词命中数仍全 0，**阴性结论不变**。本件只把「命中数 0」当结论，不把字节数/目录数当可引用定值。

⇒ **本会话未找到任何独立的（带外的、不受本地写域控制的）时间证据。**

### 2.5 若 mtime 被伪造过，还有什么办法独立定序？（给方案，本会话不执行，标未验）

按证据强度递增，并注明能否抵御「伪造者同时改本地时钟/元数据」：

1. **内容级单向锚定（不依赖时钟）**：把 seal 的 64-hex 写进**在 V1 之前已存在且不可改**的介质（V1 回归脚本/输出注释、早期台账既有行、既有 commit message/tree）。若 V1 产物字节里出现 seal 的 sha256，则 seal 必早于该 V1 产物（前提：V1 产物自身字节未被改写，其 sha256 已在编排方指纹里冻结）。**反向定序（seal 晚于 V1）无法用哈希单向证明**，只能靠「V1 产物里没有 seal 的承诺」+ 带外时间戳。本会话未系统穷举 V1 输出键树（标未验）。
2. **commit-then-reveal + 带外载体（M1）**：`_os_ORACLE_SPEC.md:216-222`、`ORACLE_SPEC.md:131` —— `t0` 把 `H(P)` 发到 A 无写权的载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / 两名见证人各留副本 + 含 Date 头回执），`t1` 交 `H(labels)`，`t2` 才跑 V1，要求 `t0<t1<t2`。抵御本地时钟伪造，但只到**制度级**（`ORACLE_SPEC.md:127`「无 PKI 的上限 = 可复核的管道 + 制度担保的隔离」）。
3. **M2 现成身份体系**：`ORACLE_SPEC.md:132` 推荐 —— `git commit -S` / minisign / sigstore / 机构 SSO 短时效 token，把「谁、何时、哪份内容」绑定到人。仍是「签名时刻」而非「认知状态」，但比 mtime 强得多；`:125` 无 PKI 时不可否认性技术上为零。
4. **M3 RFC3161 可信时间戳 + 透明日志**：`ORACLE_SPEC.md:133` —— 唯一能把「确系事前/确系事后」判成密码级事实的路径。现状 `ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`，**无**。
5. **文件系统级旁证**：NTFS USN journal、卷影副本 VSS、Windows 安全审计 4663、第三方备份。可抵御「改 mtime」，抵御不了「改本地时钟」；且**仍不能判「未见 V1 输出」**。

★ 无论哪条都**不能判「标注者没看过答案」** —— 认知状态产物上不可判定（`ORACLE_SPEC.md:123`、`:161`「内容绑定 ≠ 认知状态绑定」），只能靠 ACL 日志 + 双盲分片 + commit-then-reveal 做制度担保。

---

## 3 两层拆分（管道层 / 前提层）

### 3.1 管道层：技术正确性独立于 seal 的时序吗？ —— **判断：独立（技术上完全独立），但适用范围被限定**

实读 `_cr_real_verify.py`：

- `:44-47` 硬编码 `PRE_REGISTERED_SEAL_SHA256 = "63ebd274…ca23"`、`EXPECTED_SEAL_BYTES = 4395`；
- `:77-97 load_seal()`：`:82` 真 `seal_path.read_bytes()`、`:85` `hashlib.sha256(blob)` 重算、`:87-92` 字节数与 hash 双比对，失配报 `SEAL_BYTES_MISMATCH` / `SEAL_INTEGRITY`；
- `:104-117`：`:57-58` `CALLER_BOOLEAN_KEYS` 五个调用方布尔被忽略；`:112-114` 独立性唯一判据只是字符串不等 `author != predicate_author`（`_os_ORACLE_SPEC.md:184` 明确列为反模式）；
- `:119-131`：`anchor` / `quote` / `roles` 必须与封印记录逐字相等，否则 `ANCHOR_NOT_PRE_REGISTERED` / `QUOTE_NOT_PRE_REGISTERED` / `ROLES_NOT_PRE_REGISTERED`。

这些是**确定性的读盘 + 哈希 + 逐字比较**，与「封印何时生成 / 谁生成 / 是否看过 V1」在逻辑上无依赖：给定相同封印字节，今天跑与 V1 之前跑 `load_seal()` 输出完全相同。实跑 #1 复算 `_cr_seal.json` = `63ebd274…ca23` / 4395 B，与 `:44-47` 常量**精确相等**（管道自洽的直接实证）；十件只读指纹 `ORCH_ALL_TEN_MATCH = True`。⇒ **管道层【通过】，独立于时序。**

**必须限定**：管道只验证「封印字节 == 常量」「被封字节 == 封印所指」「引文/角色逐字在场」。它验证不了「封印所指字节是 V1 之前冻结的」，也验证不了 `truth=True` 是独立语义裁决（`CERT_REAL_CHECK.md:530` 明写这是**必要条件**，不是 `ORACLE(i)=1`）。时序不影响技术正确性，**但影响这个正确性所能支撑的命题**。

### 3.2 前提层：「预注册」性质成立吗？ —— **判断：不成立（按 `_fnr_check.py:73-76` 四条全不满足）**

`_fnr_check.py:73-76` 要求 ORACLE 是「produced **BEFORE V1 is run**, by an adjudicator who **does not see V1's outputs** and **did not author V1**, with a **published SHA256 seal**」；`:78-91` 定义 (A)–(E) 合取。逐条对照：

| 条件 | 证据 | 逐条判断 |
|---|---|---|
| ① 产于 V1 之前 | 实跑 #1：seal 18:33:04 > V1_reg_out 13:53:57（+16747 s = 4h39m7s）、> V1_reg_py（+20410 s）、> r9s_reg_out（+14438 s）；`_os6_audit_out.json:C3_mtime.seal_later_than_v1_regress_output=true`；`ORACLE_SPEC.md:81` 同值 | **不满足**（在当前可见 mtime 下字面条件不成立）；且 mtime 可伪造、无带外时间戳，故既不能写「确系事后」，也不能建立 `t0<t1<t2` |
| ② 未见 V1 输出 / 标注不可由 V1 派生 | 实跑 #1：`seal5 == flips == whitelist`（三集合相等均为 `True`），`seal5` 的 5 个 token == `spec_inventory` 5 键 == `_r9s_predicates.py:371-402` SPECS 全键；`ORACLE_SPEC.md:87` 记「5 项恰是被测输出选出的 5 对」，`ORACLE_SPEC.md:109` 的 C3「不可派生」判 FAIL | **不满足**（选择依赖被测方预置白名单/SPECS，见 §4.2）；标注者认知状态本身产物上不可判定（`ORACLE_SPEC.md:123`），故「未见」不可核 |
| ③ 未写 V1 / 身份独立 | 实读 `_cr_build_seal.py:30-31`（及 `:41-42`、`:52-53`、`:64-65`、`:75-76` 共 5 处）：`author: "independent_blind_adjudicator"` 全是生成器内**自写字符串**，`truth:True` 硬编码；`_cr_real_verify.py:112-114` 唯一判据是字符串不等；`_os_ORACLE_SPEC.md:184` 把该字符串、字符串比较、调用方布尔、本会话自述独立并列为**明确不算判据的四类反模式** | **不满足** |
| ④ published SHA256 seal（带外） | 实跑 #2：seal 顶层仅 `items`/`seal_version`，无 `signature`/`pubkey`/`timestamp`/`nonce`/`witness`；`ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`、无签名库 import；实跑 #9 cert 目录无伴随签名件；封印与常量同处 `lead/cert_realcheck_20261109/`，`CERT_REAL_CHECK.md:509` 实证可同域双改 | **不满足** |

`ORACLE_SPEC.md:295` 亦列「现状四条全不满足」。⇒ **前提层【不成立】**：在当前可见证据下，这不是带外预注册，也不构成独立异源 ORACLE。**注意**：① 的「不满足」是「当前可见 mtime 下 + 无带外时序」，不是「确系事后」的证明（§2.3）。

### 3.3 ★ 两层各自能支撑什么结论 —— 对照表

| 层 | 该层「通过/成立」意味着 | **能说** | **不能说** | 本例状态 |
|---|---|---|---|---|
| **管道层** | 校验器按封印字节正确读盘重算、逐字比较、忽略调用方布尔 | ①「`_cr_seal.json` 的 4395 B 与硬编码承诺 sha256 一致」；②「封印所指 5 个锚点的字节/行/引文/角色值**逐字在场且未被篡改**」；③「这些检查可复核、确定性」 | ✗「文本是 V1 之前冻结的」；✗「`ORACLE(i)=1` 语义内容确已交付」；✗「标注独立/盲/未见答案」；✗「封印不可否认 / 抗同域双改」（`:509` 反例）；✗「fp/fn=0/0 可外推为总体率」；✗「`NO_RELAXATION=PASS`」 | **通过**（实跑 #1 十件指纹 + 常量精确相等；`_os_ORACLE_SPEC.md:441-449` 左栏同） |
| **前提层** | ORACLE 由独立第三方在 V1 之前、未见 V1、未写 V1 产出，带带外封印且覆盖全 I | 「标注独立于 V1」「`truth` 是异源语义真值」「(A)/(B)/(C) 有合法输入」「`t0<t1<t2`」 | ✗「管道技术正确」（前提不蕴含实现）；✗「文本未篡改」（那是哈希层）；✗ 即使成立，仍须 (D) SENSITIVITY 元检验与 (E) 白名单来源才能判 `NO_RELAXATION`（`_fnr_check.py:78-91`） | **不成立**（§3.2 四条全不满足；`_os_ORACLE_SPEC.md:443-449` 右栏同） |

关键分离：**「文本未篡改」是「语义真值」的必要非充分条件**（`ORACLE_SPEC.md:305`、`CERT_REAL_CHECK.md:530`）。管道层给出必要条件，前提层才可能给出异源真值；**两层互不蕴含、互不替代**（管道通过 ⇏ 前提成立；前提成立 ⇏ 管道正确）。前提层本例**不成立**，因此「标注独立」这句话**不能说**；`_cr_seal.json` 里的 `author="independent_blind_adjudicator"` 只是字符串（`_os_ORACLE_SPEC.md:184`）。

> **修正复核缺陷 4（自相矛盾 + 三元组混用）**：不复述「两层失效模式不相关」这种与所引 `:530`「相关」冲突的措辞。本件对两层只断言**逻辑蕴含关系**（互不蕴含），不断言失效模式相关性。另：`CERT_REAL_CHECK.md:530` / `:56` / `:524` 的「三层」指 `_fnr_check.py` 的 **L1 结构 / L2 语义 / L3 对抗**（`FALSIFIABLE_NO_RELAX.md:198-204` 明列），并判「三层是**相关失效叠加**、`CHECK_FALSE_ALARM_AUDIT.md:196` 记真正独立层数 = 0，不得当独立互证」；它与本节的「管道层 / 前提层」**不是同一个三元组**，不得混用。结论分述：L1/L2/L3 不得当独立互证；管道层与前提层也不得当独立互证（前者是后者的实现载体，相关失效）。

### 3.4 ★ 「管道好 + 前提假」的准确表述

> **校验器能正确证明「某个在当前可见 mtime 下晚于 V1、不能排除事后、且其 5 项恰等于被测方预置白名单的封印」所指的字节逐字在场且未被篡改，因此它证明的是一套可复核的完整性管道，而不是任何独立异源的语义真值或「没放松」。**

更短口径：`可复核的完整性管道 ≠ 独立异源真值`；或沿用 `CERT_REAL_CHECK.md:512`「**自证换了套可复核的管道**」。**禁止**写成「证明没放松，只是置信度低一点」这类降格表述 —— 前提假时该结论**根本不可作**，不是置信度问题。**修正复核缺陷 2**：本表述已把上一版「由被测方自己在 V1 之后写成」改为「在当前可见 mtime 下晚于 V1、不能排除事后」，不把弱旁证写成确证。

---

## 4 5 项 vs 302 项

### 4.1 缺 297 项的后果（实跑 #1/#2）

按 `_fnr_check.py:355-363` 口径从 `_r9s_regress_out.json` 复算：`n_items=302`、`distinct (domain,token)=302`、`flips=5`、`whitelist=5`；`_cr_seal.json n_items=5`；`5/302 = 0.016556291390728478`，**缺 297 项**。

- **`_fnr_check.py:81` 的 (C) ORACLE COVERAGE `|{i:ORACLE(i) defined}| = |I|` 直接不满足**（5≠302），(A) SOUNDNESS / (B) BOUNDED TIGHTENING 的全称量词 `∀i∈I` 没有合法输入 ⇒ **`NO_RELAXATION` 不能判**（`ORACLE_SPEC.md:110`、`_os_ORACLE_SPEC.md:481`）。
- **缺口是静默的**：`_fnr_check.py:151-157` 的 `detail` 里只有 `n_items` / `coverage_ratio`，`problems` 里没有 coverage 项（`FALSIFIABLE_NO_RELAX.md:170`「(C) 覆盖只报告不门禁」）⇒ 现有门禁**连 5≠302 都不会报 FAIL**。
- **297 项完全没有语义标签**，既无 `true` 也无 `false` 也无 `UNVERIFIABLE`；`_os_ORACLE_SPEC.md:435` 要求 T1–T8 全标 `UNVERIFIED`、语义真值层 `302/302` 未验、`n_items_sealed = 5/302`。
- **无负例**：5/5 全 `truth=True`（实跑 #1 `seal_truth_all_true=True`、`n_truth_false=0`、`negatives=0`），既不能估假阳性也不能估敏感度。

### 4.2 ★ 5 项恰等于白名单 5 对 —— 不是巧合，是构造性恒等（修正复核缺陷 1）

实跑 #1/#2 输出：

```
seal_eq_flips = True          seal_eq_whitelist = True          flips_eq_whitelist = True
seal_eq_spec_keys_tokens = True
spec_inventory keys = ['可重建', '实跑输出', '改前改后', '脚本存在性', '需谁批准']
n_items_with_registered_token = 10    n_items_no_registered_token = 292    n_distinct_registered_pairs = 10
```

**必须说透的构造链**（这是复核缺陷 1 指出的核心，上一版只说「选择依赖 V1 输出」不够）：

1. `_r9s_predicates.py:371-402` 的 `SPECS` 是**闭合注册表**，恰好 5 个键 = `spec_inventory` 5 键 = seal 5 个 token = `flips` 5 个 token = `whitelist` 5 个 token（实跑 `seal_eq_spec_keys_tokens=True`）。即这 5 项**就是全部已登记 token**，不是从 302 项里抽出来的样本。
2. `flips` 与 `whitelist` 集合相等（实跑 `flips_eq_whitelist=True`），且 `WHITELIST` 是 `_r9s_regress.py:112-119` 的**硬编码字面量**，注释明写「本次任务书指名要求改判的 5 处」。该文件 mtime **12:59:07**（实跑 #1 `EXTRA r9s_regress_py`），**早于**全部 V1 输出（13:53:57 / 14:32:26）与 seal（18:33:04）。
3. `_fnr_check.py:314-351` 的 `CERTS`（同一 5 键、同一 `independent_blind_adjudicator` 串）在 16:11:22 已存在，比 seal 早 8502 s = 2h21m42s。
4. 302 项里只有 **10 个 (domain,token) 对**含已登记 token，其余 **292 项结构性不可能翻案**（`_os_ORACLE_SPEC.md:304`、`_fnr_check.py:133-135` 的 `untested` 口径）；"outside_whitelist=0" 是 `self_certified` 的**设计后果**（`_fnr_check.py:136-150`）。

⇒ **选择依赖的是「早于 V1 输出的预置任务书 / SPECS / 白名单」，不是「看到 V1 输出后挑出来的」**。因此 `ORACLE_SPEC.md:87` 的「标注时已见 V1 输出」措辞**不精确**：准确表述应为「**依赖被测方预置白名单/SPECS，该依赖早于 V1 输出；且 seal 本身在当前可见 mtime 下晚于 V1 4h39m7s、不能排除事后**」。方向不变、且被加强：`WHITELIST` 与 `SPECS` 同源（判据作者自己写的白名单，`WHITELIST_AUDIT.md:517`、`_WL_WHITELIST_AUDIT.md:486`），`ORACLE_SPEC.md:109` 的 C3「不可派生」判 FAIL，「标注独立」在机制层面**不可能成立**，与标注者的认知状态无关。

**「标注时是否已知答案」**：产物层面能判的是「标注集 == V1 答案集 == 预置白名单集」（三个集合相等，实跑 True）；`_WL_WHITELIST_AUDIT.md:466` 自警「这批白名单内容恰好是对的，但机制不能证明它对」。至于「标注者当初心里的认知状态」，按 `ORACLE_SPEC.md:123` **产物上不可判定，本会话判不了（标未验）**。但按预注册判据口径，这种构造本身已使「未见 V1 输出 / 不可派生」**不可核** ⇒ T3/T4/T5 不可作（`ORACLE_SPEC.md:112`）。

### 4.3 若 5 项标注是「看着答案标的」，作为「独立真值」的价值

**作为「独立真值」的价值 = 0**（不是「低」，是零）：

- 独立性的定义就是「不由被测方/被测输出派生」（`_fnr_check.py:73-75`；T5 `_os_ORACLE_SPEC.md:179`「标注内容不可由 V1 派生」）。若标签由同源的预置白名单/SPECS 反填，则 `ORACLE` 与 `V1` 同源，`(A) ∀i: V0=0∧V1=1 ⇒ ORACLE=1` 变成**恒真重言式**，不携带任何关于 V1 是否放松的信息。
- 仍能保留的价值只有两项，且都**不属于**「独立真值」：① **管道自测样本**（证明读盘/哈希/逐字比较能跑通，`CERT_REAL_CHECK.md:329` 的 `PASS 5/5` 属此类）；② **内容判定可能恰好是对的**（`_WL_WHITELIST_AUDIT.md:466`「内容恰好是对的，但机制不能证明它对」、`WHITELIST_AUDIT.md:516`「5 条白名单内容：可信」）—— 但「恰好对」不等于「由机制证明对」。
- `_os_ORACLE_SPEC.md:419` 明写「实际人工盲标投入 = 0」「5/5 不能按比例外推到 302 项，也不能计入本规范的第三方盲标产出」；`:471` 要求把人工独立 5/5「**作为参考而非 ORACLE**」接入。

### 4.4 用 5 项支撑 302 项的结论，属于什么错误？与「口径错置」同类吗？

**主错误 = 覆盖域/量词域错置（coverage fallacy）+ 选择偏差**：`_fnr_check.py:81` 要求 `|{ORACLE defined}| = |I| = 302`；用 5 项（且是被测方预置白名单挑出的 5 项）去支撑「302 项全量证明没放松」，是把「子集上可复核」偷换成「全集上成立」，违反全称量词 `∀i∈I`（`_os_ORACLE_SPEC.md:445` 右栏把「302 项全量证明没放松」列为越界；`ORACLE_SPEC.md:274`「不得按比例外推到 302 项」）。次生错误：样本不是随机抽自 I，而是 `flips ∩ whitelist ∩ SPECS`，所以连「5/302 的统计外推 + 置信区间」都不合法；且无 `UNVERIFIABLE` / 负例。

**与既有「口径错置」同族不同型，不可混称**：`lead/keff_calc_20261109/KEFF_CALC.md:110-112` 定义的「口径错置」是把 `fp_rate`（非断言被误拦率）当 `fn_rate`（真断言被放过率）代入公式，属**指标定义错置 / 量的语义错置**；本例是**同一口径的量被用在不匹配的量化域上**（集合/量词域错置 + 选择偏差）。二者同属「量或证据被用于其定义域之外的口径」这一大类，但**不是同一个具体错误**。`ORACLE_SPEC.md:305` 归入「越界即错」；`:299` 只支撑「封印所指 **5 个锚点文件**的字节/行/引文/角色值逐字在场」。

---

## 5 同域双改

### 5.1 读 `CERT_REAL_CHECK.md:509` 核说法 —— **成立，但须精确化「四件套」的载体（修正复核缺陷 7）**

实读 `CERT_REAL_CHECK.md:509`：原文记载「`_cr_seal.json` 与 `PRE_REGISTERED_SEAL_SHA256`（`_cr_real_verify.py:44-47`）都在 `lead/cert_realcheck_20261109/`」，复核员 Part C / H9「同步重写封印、记录 hash 与模块内常量后，凭空编造的内容 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`」；并如实登记第一次复现漏同步调用方证书得 `NON_PASS`，补全后 `python -I -X utf8 ".../_crdoc_colocated.py"` 输出 `VERDICT=PASS, n_pass=5, n_fail=0`、`fake_seal_sha256=482b14b3…ec7fecb`。

本会话交叉核对（**只读，未重跑攻击**）：

- `_crdoc_colocated_out.json:1-6` 逐字含 `"VERDICT": "PASS"`、`"seal_ok": true`、`"n_pass": 5`、`"n_stale": 0`、`"n_fail": 0`；`:49-50` 含 `fake_seal_sha256 = 482b14b3de057829065d308e50a3cfea48774ceebd928d1204abee119ec7fecb` 与 `note: "FULL co-located double rewrite: seal + artifact + caller cert + hard-coded constant, all inside the same write domain"`；5 条 `per_item` 全 `PASS` / `problems=[]`。
- 实跑 #4 读 `_crdoc_colocated.py:30-33`：`V` 是 `importlib.util.spec_from_file_location(...)` **载入到内存的模块对象**。故 `:71-73` 的 `V.PRE_REGISTERED_SEAL_SHA256 = ...` / `V.EXPECTED_SEAL_BYTES = ...` 改的是**内存属性**，**不是磁盘上的 `_cr_real_verify.py`**。上一版「四件套同域同步改写」措辞偏松，准确说法是：**沙箱内磁盘假交付件（`:48-52`）+ 沙箱内磁盘假 seal（`:55-68`，实跑 #1 得 `_crdoc_colocated_sandbox/_crdoc_fake_seal.json` 19:14:23 / 3997 B / sha `482b14b3…ec7fecb`，与 `:49` 同串）+ 内存模块常量（`:71-73`）+ 调用方证书（`:75-78`），四者在同一写域/同一进程内同步改写后调 `verify_all`（`:80`）**。
- `_cr_real_verify.py:44-47` 常量与 `_cr_seal.json` 确在同目录；`:87-92` 只比对这两个可被同域控制的端点。

⇒ **`:509` 同域双改可造出 `seal_ok=true` 的 PASS 5/5 说法成立**，有可复核输出件与脚本支撑。**本会话未独立重跑**该攻击（纪律：不改既有件、不生成新 seal；`ORACLE_SPEC.md:77`、`:302`、`:484` 亦标「未重跑，沿用记录」）—— 如实记为「沿用既有实跑输出，未独立复现」。

### 5.2 ★ 若连承诺都可被同域重写，「预注册」还有无意义？

**概念本身仍有意义，但本例的实现使它退化为「零约束的自证」，因此在本例没有证据价值。**

- 「预注册」的有效性来自**时间 + 写域双重不可回改**：`t0` 冻结 `H(P)`，承诺在 A 写域之外，之后任何改写都与带外承诺失配。若承诺与封印、常量、交付件、调用方证书同处一个可写域，攻击者可「一整套同步重算」，使 `sha256(seal_bytes) == CONST` 与 `sha256(artifact_bytes) == seal.file_sha256` 同时成立 —— 哈希仍是真的、重算仍是对的，只是**被比较的两个端点都由同一方提供**。此时 PASS 只表示「这套自洽方程成立」，与「事前冻结」无关。
- 准确含义：`CERT_REAL_CHECK.md:509` 说明 §3(a)①「封印自身 SHA256 硬编码进校验器」**单独不充分**，除非常量在攻击者写域之外 / 带外部签名；`_os_ORACLE_SPEC.md:199`、`ORACLE_SPEC.md:118` 把「承诺是否被同域双改」「谁算的」「何时算的」列为 A 类纯密码学**查不到**的三项。
- 概念不因此作废：`ORACLE_SPEC.md:118` 把「内容完整性」列为 A 类可查；只要加上 T8 的带外锚（`_os_ORACLE_SPEC.md:182`），同一个哈希管道立刻恢复约束力。⇒ **缺的是锚/信任根，不是哈希/算法。**
- 但要如实说清：即使补了带外锚，也只能证明「**这份字节在 t0 之前已冻结**」；**仍不能证明「标注者未见 V1 输出」**（`ORACLE_SPEC.md:123`、`:161`）。预注册能买到「不可回改」，买不到「认知独立」。

### 5.3 T8「抗同域双改」判据可执行吗？

**判据（实读 `_os_ORACLE_SPEC.md:182`、`ORACLE_SPEC.md:108/:112`）**：承诺哈希 + 标注包 + 校验器常量**至少三者之一**位于 `A` 写域之外（带外签名 / 第三方存证 / 公证 / append-only 日志）；检验方法 = 攻击演练：模拟 A 同步重写封印 + 常量 + 内容，要求**仍 FAIL**（对照 `CERT_REAL_CHECK.md:509` 现在会 PASS）。

**判断：作为「设计/验收判据」完全可执行；作为「现状门禁」不可执行（条件当前为假）。**

- 可执行：① **结构性可查** —— 三者路径/归属可静态枚举，「至少一个的写 ACL 不含 A」是确定性判断；② **演练可复现** —— `_crdoc_colocated.py:48-80` 已给出可粘贴的同步改写模板，把「至少一个锚在域外」加进去后，重算端点无法与之匹配，必然在 `_cr_real_verify.py:87-92` 报 `SEAL_BYTES_MISMATCH` / `SEAL_INTEGRITY`；③ `ORACLE_SPEC.md:112` 把 T8 列为逐条报状态的门禁，`:303` 要求「同域双改缺口可被显式声明」，`_os_ORACLE_SPEC.md:434` 要求「演练必须报 FAIL」。
- 现状不可执行：① `ORACLE_SPEC.md:75` 实跑 `n_repo_signature_sidecars=0`、`cr_verify_has_sig_or_crypto_import=False`（实跑 #9 cert 目录无伴随签名件）；② `ORACLE_SPEC.md:87/:108` 把 C2「预注册 + 抗同域双改」判 **FAIL：常量与封印同域**；③ 实跑 #7 git 六目录全 `?? untracked`、无签名 commit、无 append-only 日志；④ 因此「至少一者在 A 写域外」当前为假，演练必然给 PASS（`:509` 已实证），判据只能报 FAIL。
- **本会话未执行该演练**（纪律：不生成新 seal、不改既有件；`ORACLE_SPEC.md:484` 记「未重跑」）。标「未独立复跑 / 未验」。

### 5.4 在没有 PKI 的现状下，这条能不能做到？

**判断：T8 的「结构性/制度级」版本能做到，「不可否认」的密码级版本做不到；因此只能做到「抗同域双改」，做不到「不可否认」。**

- **能做到（M1）**：`_os_ORACLE_SPEC.md:216-222`（标「推荐」）、`ORACLE_SPEC.md:131` 列为下限 —— 把 `H(P)` 发到 A 无写权限的载体，并让 W 持封印、**封印与校验器硬编码常量分域**（`:221`、`:535`）。此时同步重写四件套会被域外那份 64-hex 拦住，演练可报 FAIL。`ORACLE_SPEC.md:127` 定义「无 PKI 的上限 = 可复核的管道 + **制度担保的隔离**」。
- **做不到（密码级）**：`ORACLE_SPEC.md:125`「**不可否认性：无 PKI 时技术上为零**」；`:124` 把「承诺确在 V1 前、W 与 A 无串通、302 清单外部完备性、交付件确由某次实跑产生」列为无检验方法、只能靠制度；`:121` 把 mtime / git commit 时间 / 邮件 Date 头 / 第三方 push 时间统列为「B 弱旁证（不抵赖）」。M1 只把攻击成本从「改一个目录」抬到「串通多方」。
- **可低成本升级到密码级（M2，`ORACLE_SPEC.md:132` 推荐）**：用现成身份体系 `git commit -S` / minisign / sigstore / 机构 SSO 短时效 token，`ORACLE_SPEC.md:132`「只需一对密钥 + 公钥指纹带外公布」，即可把 T1/T4/T6/T8 从制度级升到密码级，**无需自建 CA**。M3（PKI + RFC3161 + 透明日志）才是完整不可否认（`ORACLE_SPEC.md:133`）。
- 另注意 §5.2 限定：即使 M2/M3 到位，仍不能证明「未见 V1 输出」（`ORACLE_SPEC.md:123`）。

---

## 6 复核回件（绑定行）+ 结论 + 未验项

### 6.1 复核回件：绑定行（格式固定）与 verdict 如实记

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

实跑 #1 格式复验：用「固定前缀 + 64 位小写十六进制捕获组 + 固定中文逗号与后缀 + 数字捕获组」的正则（模式串见 `_final_verify.py` 内 `pat` 变量，不在正文重复以免与绑定行混淆）在既有草稿 `_sc_SEAL_CHRONOLOGY.md` 命中 1 行、在 `ORACLE_SPEC.md:283` 命中 1 行，两处 `is64hex=True`，且均等于盘上 `_cr_seal.json` 的 `hashlib.sha256(read_bytes())` 实算值 `63ebd274…ca23` / 4395 B。本件文首与本节各给同一行（同一绑定值，无第二套数值），行内未插入路径、括号、星号、反引号或空格。

**复核 verdict 如实记**：编排方【复核】件 `"verdict": "partial"`、`ranCommands=26`、`sha256Line` 与本绑定行同值。按交付规则「**refuted 或 partial 标 unconfirmed**」—— 本次为 `partial`，规则**触发**，故本件结论标 **`unconfirmed`**，不写 confirmed。（上下文对照，不混用：`CERT_REAL_CHECK.md:504` 自记其复核 `verdict = partial` 并按铁律标 `unconfirmed`；`ORACLE_SPEC.md:287` 记的是**另一轮**复核 `confirmed` 且注明「该规则未触发」。本件照记本轮 `partial / unconfirmed`。）

**复核件登记的 8 项可引用缺陷（如实沿用，并给本件处置）**：

| # | 缺陷 | 本件处置 |
|---|---|---|
| 1 | 步骤④未说透：5 项不是巧合而是构造性恒等；白名单 `_r9s_regress.py:113-119` 硬编码、mtime 12:59:07 早于全部 V1 输出；`_fnr_check.py:314-351` 早 seal 2h22m | §4.2 全量补上构造链，并把 `ORACLE_SPEC.md:87`「标注时已见 V1 输出」校正为「依赖被测方预置白名单，该依赖早于 V1 输出」 |
| 2 | mtime 当铁证残留泄漏（3 句把「不能排除事后」写成「确系事后」） | §2.3 §3.4 全篇限定；§3.4 表述已改写 |
| 3 | 事实错误「11-01 晚于 11-09」 | §2.4 已改为「11-01 **早于** 11-09」，零覆盖结论不变 |
| 4 | 「失效模式不相关」与 `:530`「相关」冲突、且混用 L1/L2/L3 三元组 | §3.3 修正框：只断言互不蕴含；明确两个三元组不同 |
| 5 | 「real_verify 晚 71 s / 编排方表未点破」夸大新发现性 | §2.2 注：`ORACLE_SPEC.md:81` / `C3_mtime` 已载，不冒称新发现 |
| 6 | −71 s / 16747 s 是 epoch 截断取整后相减，被称「精确差」 | §2.2 同时给整数差与浮点差（−70.432142 / +16747.945093） |
| 7 | 「四件套同域同步改写」措辞偏松：`:71-73` 改内存属性非磁盘 | §5.1 精确化载体；磁盘假 seal 实跑指纹 `482b14b3…ec7fecb` 已核 |
| 8 | 阴性证据计数随日志增长漂移 | §2.4 只把「命中数 0」当结论，字节数/目录数标为点值 |

复核件已确认项本会话亦独立复现：十件指纹 `ORCH_ALL_TEN_MATCH=True`、mtime 与 PowerShell 交叉一致、两层确实拆开、5vs302 集合相等且缺 297、`:509` 与 `INTEGRITY_OK_BUT_UNCONFIRMED` 判定准确、越界为零（六只读域与两件台账指纹未变、HEAD 仍 `2657458`、未 commit/push）。

### 6.2 `INTEGRITY_OK_BUT_UNCONFIRMED` 准确吗？

**评价：准确，且是本会话可核证据下唯一不越界的判词；但有两点必须随判词一并声明，否则会被误读。**

- 准确之处：① `INTEGRITY_OK` 对应**管道层实测通过** —— 实跑 #1 十件指纹全匹配、`_cr_seal.json` 与 `_cr_real_verify.py:44-47` 常量精确相等、`_os_ORACLE_SPEC.md:441-449` 左栏可复核事实；② `BUT_UNCONFIRMED` 对应**前提层四条全不成立**（§3.2）+ 覆盖 5/302（§4.1）+ 同域双改实证（§5.1）；③ `ORACLE_SPEC.md:293` / `_os_ORACLE_SPEC.md:427` 明确「不是 `NO_RELAXATION=PASS`」，把「未证」与「证伪」分开，符合「拿不到写未验」纪律。
- **必须随附两点**：
  1. **它是自创判词，不是项目既有 gate 判词**：`ORACLE_SPEC.md:295` 实跑 `grep` 后自述「本规范自创判词……零命中项目既有 gate 判词，未冒认为项目既有判词」。不能写成「项目门禁判定为 `INTEGRITY_OK_BUT_UNCONFIRMED`」。
  2. **`INTEGRITY_OK` 不覆盖抗同域双改**：`:509` 的攻击造出的正是 `seal_ok=true` 的 `PASS`。`ORACLE_SPEC.md:303` / `_os_ORACLE_SPEC.md:434` 要求「同域双改缺口必须显式声明，不得隐藏」。更严谨展开：`INTEGRITY_OK（可复核的完整性管道，含已知同域双改残留缺口）_BUT_UNCONFIRMED（语义真值/独立/全覆盖均未验）`；复核件建议的 `PIPELINE_SELFCONSISTENT_BUT_ORACLE_UNCONFIRMED` 亦等价且更不易被读成「抗篡改」，本件不改动既有判词，仅登记。
- 措辞矛盾如实登记：`_os_ORACLE_SPEC.md:216` 把 M1 标「——推荐」，而主规范 `ORACLE_SPEC.md:132` 取 **M2 推荐**并在 `:289` 登记该矛盾。本件按主规范取 M2。

### 6.3 最小成本路径推荐（M1 / M2 / M3）

**推荐 M2（`ORACLE_SPEC.md:132` 同），理由是「成本几乎不增、把 T1/T4/T6/T8 一次升到密码级」。**

| 方案 | 成本 | 能买到 | 不能买到 |
|---|---|---|---|
| M1（下限）`_os_ORACLE_SPEC.md:216-222` | 带外载体 + ≥2 见证人 + ACL 隔离日志 + commit-then-reveal；**302 项双盲标注本身 ≈50.33 人时 / 端到端 60–95 人时 / 5–8 工作日**（`ORACLE_SPEC.md:309`） | 制度级 `t0<t1<t2`、封印与常量分域、T8 演练可报 FAIL | 不可否认性（`ORACLE_SPEC.md:125` 技术上为零）；W 与 A 无串通；「未见」 |
| **M2（推荐）** `ORACLE_SPEC.md:132`、`_os_ORACLE_SPEC.md:224` | 在 M1 上加**一对现成密钥**：`git commit -S` / minisign / sigstore / 机构 SSO token + 公钥指纹带外公布；无需自建 CA | 把「谁、何时、哪份内容」绑定到人，T1/T4/T6/T8 升密码级 | 签名前的所见所闻（内容绑定 ≠ 认知状态绑定，`ORACLE_SPEC.md:161`） |
| M3（最强）`ORACLE_SPEC.md:133` | 自建/采购 PKI + RFC3161 TSA + 透明日志 | 时序成为可验证事实、真正不可否认 | 仍需 ≥2 名真第三方 + 双盲 + 302 项全覆盖（人力不减） |

**★ 关键提醒（最小成本 ≠ 最小工作量）**：三者共享同一个**不可压缩**的人力成本 —— `ORACLE_SPEC.md:295` 四条件与 `:110` C4 全覆盖，必须「≥2 名具名裁决者各自标全 302 项 + 仲裁 + κ≥0.80 + `UNVERIFIABLE` 单列」（`_os_ORACLE_SPEC.md:220`, `:385-399`, `ORACLE_SPEC.md:309`）。**M2 只是在必经流程上补签名，没有新增人力；M1 省下的只是密钥，省不下 50+ 人时。** 另需工程接入：`CERT_REAL_CHECK.md:395` / `_os_ORACLE_SPEC.md:361` 要求给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 两槽（现状 C3 两个 TypeError），并把 coverage 做成真 FAIL（现状 `_fnr_check.py:151-157` 只在 detail）。**本会话不执行任何 M 方案**（只做时序核查与分离评估）。

### 6.4 ★ 所有层数结论的最终表述（逐层判断，不用「时序有问题」概括）

| 层 | 本例逐层判断 | 依据 |
|---|---|---|
| mtime / 时序层 | 当前可见 mtime 下 seal 晚于 V1 **+16747 s = 4h39m7s**（浮点 +16747.945093 s）；**只能得出「不能排除事后」**，不能得出「确系事后」；无带外时间证据 | 实跑 #1/#10；§2.2 §2.3 §2.4 |
| **管道层** | **通过**（技术正确性独立于时序；确定性读盘+哈希+逐字比较） | `_cr_real_verify.py:77-97/:119-131`；实跑 #1 指纹一致；§3.1 |
| **前提层**（预注册/独立性） | **不成立**（四条全不满足；且 mtime 弱旁证不能升级为时序确证） | `_fnr_check.py:73-76`；§3.2 |
| 覆盖层 | **不成立**（5 项 / 302 项 = 0.016556，**缺 297 项**；缺口静默不报 FAIL） | 实跑 #1；`_fnr_check.py:81/:151-157`；§4.1 |
| 选择/同源层 | **不成立**（5 项 == 白名单 5 对 == flips 5 条 == SPECS 5 键，构造性恒等；白名单由被测方预置、早于 V1 输出） | 实跑 #1；`_r9s_regress.py:112-119`；`_r9s_predicates.py:371-402`；§4.2 |
| 抗同域双改层（T8） | **不成立**（`:509` 实证 PASS 5/5；无带外锚/签名/PKIsidecar） | `_crdoc_colocated_out.json:1-6/:49-50`；实跑 #9；§5 |
| L1/L2/L3 门禁层 | **不得当独立互证**（相关失效叠加，独立层数 = 0） | `CERT_REAL_CHECK.md:56/:524/:530`；`FALSIFIABLE_NO_RELAX.md:198-204` |
| 语义真值层 | **302/302 未验**（5/5 全 `truth=True`、0 负例、0 `UNVERIFIABLE`；`ORACLE(i)=1` 未独立重判） | 实跑 #1/#2；`_os_ORACLE_SPEC.md:435`；`CERT_REAL_CHECK.md:543` |
| 不可否认层 | **技术上为零**（无 PKI / 签名 / RFC3161） | `ORACLE_SPEC.md:75/:125` |
| 总体 VERDICT | **`INTEGRITY_OK_BUT_UNCONFIRMED`**（自创判词、非项目 gate 判词；**不是** `NO_RELAXATION=PASS`） | `ORACLE_SPEC.md:293`；`_os_ORACLE_SPEC.md:427`；§6.2 |

> **★ 最终表述（一句话）**：**本项目当前只能声称「一套技术正确、可复核的完整性管道 + 全量结构/集合门禁 + 诚实未验记账（VERDICT = `INTEGRITY_OK_BUT_UNCONFIRMED`）」；任何「三层独立互证」「标注独立」「置信度已量化」「没放松」的说法都不成立：L1/L2/L3 是相关失效叠加、ORACLE 前提四条全不满足、5/302 覆盖且 5 项恰等于被测方预置的白名单 5 对、同域双改可造 PASS，因此语义真值层 302/302 未验。**

依据：`CERT_REAL_CHECK.md:530`（三层相关失效叠加，不得当独立互证）、`:512`（自证换了套更好的管道）、`ORACLE_SPEC.md:305`（必要非充分 / 越界即错）、`_os_ORACLE_SPEC.md:435`（T1–T8 全标 UNVERIFIED、`302/302` 未验、`n_items_sealed=5/302`）、`WHITELIST_AUDIT.md:517` / `_WL_WHITELIST_AUDIT.md:486`（「『没放松』的证明：不可信」）。**特别禁止**用「置信度低」「三层独立所以更可靠」「fp/fn=0/0」把 `UNCONFIRMED` 降格成弱 PASS（`_os_ORACLE_SPEC.md:446` 明列 fp/fn 外推为越界）。

### 6.5 判不了什么 / 未验项（如实列，沿用 `CERT_REAL_CHECK.md:541-550`、`_os_ORACLE_SPEC.md:479-490`、`ORACLE_SPEC.md:323-339` 加本会话特有项）

1. **判不了「确系事后」**（mtime 可伪造，§2.3）；**也判不了「mtime 曾被伪造」**（未读 USN / 审计日志，标未验）。
2. **判不了 seal 生成时刻的真实先后** —— 无带外时间戳、无签名、git 对 11-09 零覆盖、CLI 会话库 11-09 无 seal 记录（§2.4）；CreationTime 只是同一本地文件系统的另一可写元数据。三种认知/时序状态（确系事后、标注者看过答案、mtime 曾被伪造）一律判不了。
3. **判不了「标注者是否看过 V1 输出」这个认知状态** —— 产物上不可判定（`ORACLE_SPEC.md:123`）；本会话只判了「标注集 == V1 答案集 == 预置白名单集」这一产物事实。
4. **判不了 `ORACLE(i)=1` 语义真值 / 302 项语义裁决** —— 未重读 32 主件全文逐项重判（`CERT_REAL_CHECK.md:543`、`ORACLE_SPEC.md:322`）。
5. **判不了 `_fnr_check.py:78-91` 的 `NO_RELAXATION`** —— (C) 需 302 项盲标（本会话 0 项）、(A)/(B) 需 ORACLE 语义真值（无）、(B) 未实装（`_os_ORACLE_SPEC.md:476`）、(D) 未在 302 全集上跑。
6. **判不了「三层独立 / 置信度」** —— 相关失效叠加；κ、p_o、CI、总体 fp/fn 率均无第三方标签（`CERT_REAL_CHECK.md:545`）。
7. **判不了不可否认性与抗同域双改的现状达标** —— 无 PKI/签名（`ORACLE_SPEC.md:125`）；**本会话未重跑** `:509` 共址改写攻击（只读纪律 + 未生成新 seal），只核对既有输出件与脚本。
8. **判不了 302 项验证器实跑成本与结果** —— `CERT_REAL_CHECK.md:301` 的 7.482 MB / 7.85 MB 自标「估计，未实跑」；本会话只复算 302 项**清单**与 5 项封印指纹，未跑 302 项读盘验证。
9. **判不了 302 项清单本身的外部完备性** —— `I` 来自 `_r9s_regress_out.json` 32 域 `per_element`（`_os_ORACLE_SPEC.md:288`）。
10. **判不了零真机下的一切运行时行为** —— 未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；未验证现盘 R9 升级、未复跑 24/24 负样本、未验证跨项目推广。
11. **判不了交付件「确由某次实跑产生」** —— `_os_ORACLE_SPEC.md:489`、`WHITELIST_AUDIT.md:497` 明记未验。
12. **本会话未跑 `_cr_real_verify.py:main()` / `_fnr_check.py:main()`** —— 前者 `:458-460` 会回写 `_cr_verify_out.json`，后者 `:548-549` 会回写只读域；一律 `importlib` / 只读 `-c` 替代。⇒ **管道层「通过」的判断依据是读源码 + 指纹/结构复算，不是跑校验器 main() 的端到端结果**（如实标注）。
13. **判不了其它 CLI 会话库** —— `.claude/projects`、`.codex/sessions`、`%TEMP%` 已查阴性；`~/.cursor`、`~/.gemini`、Windows 事件日志 / USN / VSS 未在本次授权范围穷举，标未验。
14. **§2.1 的十件指纹是本会话收尾时点值** —— 并发工作流可能继续写 `lead/` 其它目录；本会话收尾 `ORCH_ALL_TEN_MATCH = True` 只证明「本会话期间这十件未变」，不证明之后不变。
15. **若 mtime 被伪造如何独立定序的 5 条方案（§2.5）全部未执行** —— 只给方案，标未验。

### 6.6 纪律核对

- 零真机、零采样代码：全部命令为 `python -I -X utf8` 读盘 / `hashlib.sha256` / `os.stat`、`powershell Get-Item`、`git` 只读、`grep` / `find`；无进程/内存/注入操作。
- 绝对只读域未动：收尾实跑 #1 重算十件编排方指纹 `ORCH_ALL_TEN_MATCH = True`；两件台账（`PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`）在内。六只读域与两件台账一律未修改、未追加、未覆盖。
- 唯一写域 `lead/seal_chronology_20261109/` 本会话**新增 3 件**：`_final_verify.py`、`_final_verify_out.json`、本件 `SEAL_CHRONOLOGY.md`；既有 `_sc_*` / `_scv_*` 件一律未改。`git status --porcelain -- lead/seal_chronology_20261109/` 为 `?? lead/seal_chronology_20261109/`；HEAD 仍 `2657458 (2026-11-01)`。
- **未改任何既有件、未生成新 seal、未 commit、未 push。**
- 指纹一律 `hashlib`；引用均追到「实跑命令 + 输出」或「文件:行」；未验项已明确标注，未补造。复核 `verdict = partial` 已如实记并按规则标 `unconfirmed`。
