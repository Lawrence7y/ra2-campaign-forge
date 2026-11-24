# ORACLE_SPEC.md — 第三方盲标注 ORACLE 最小规范（六节规范件）

> 本件 = 编排方交付任务「写 ORACLE_SPEC.md 到本任务写域」的规范正文。唯一写域 `lead/oracle_spec_20261109/`。
> 纪律：**只做规范设计**，不改任何既有件、不生成新的 seal、不 commit、不 push；零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码（不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
> 本会话产物（均为**新建**，不覆盖既有件）：`ORACLE_SPEC.md`（本件）、`_os6_audit.py`（14,866 B，只读核查脚本）、`_os6_audit_out.json`（9,299 B，实跑输出，**核查输出而非 seal**）。写域内既有 5 件 `_os_ORACLE_SPEC.md` / `_os_audit.py` / `_os_audit_out.json` / `_osv_verify.py` / `_osv_verify_out.json` 保持原字节未动。

---

## 1 目的与边界

**目的**：为「`NO_RELAXATION` 是否成立」所依赖的 `ORACLE: I → {0,1}` 给出一个**最小、可执行、可复核**的第三方盲标注规范，把 `_fnr_check.py:70-92` 里那句「by an adjudicator who does not see V1's outputs and did not author V1, with a published SHA256 seal」从自然语言声明拆成逐条可检验物；并给出 302 项工程规范、κ 门槛、UNVERIFIABLE 规则与工作量数字。

**边界（硬）**：

1. **只做规范设计**。本件不产生任何标注、不产生任何标签、不产生任何 ORACLE_SEAL、不生成新的 seal；所有 JSON 代码块均为**格式模板**，未落盘为 seal 文件。实跑核查：`find lead/oracle_spec_20261109 -maxdepth 1 -type f \( -iname "*seal*" -o -name "*.sig" -o -name "*.asc" -o -name "*.pem" \) -print` → 空（`_os6_audit_out.json:C7_boundary.seal_like_files = []`）。
2. **不改任何既有件**。只读域 = `lead/cert_realcheck_20261109/` 全部件（含 `_cr_seal.json` / `_cr_real_verify.py`）、`lead/falsifiable_no_relax_20261109/`、`lead/check_fp_audit_20261109/`、`lead/whitelist_audit_20261109/`、`lead/gate_r9sem_20261109/`、`lead/keff_calc_20261109/`、`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`，一律不得修改/追加/覆盖。全程重算 10 件指纹，跑完后再算仍 10/10 全匹配（`_os6_audit_out.json:C8_readonly_unchanged.all_match_after_audit = True`），反证只读内容零漂移。
3. **不跑会回写的 main()**：`_cr_real_verify.py:458-460` 会写 `_cr_verify_out.json`，`_fnr_check.py:548-549` 会写 `_fnr_check_out.json`；本会话只 `importlib` 模块加载 + 函数级调用（模块名非 `__main__`，main() 不触发），见 `_os6_audit.py` C4/C5 段。
4. **本会话本身不是第三方、不盲**：本子代理是单会话、读了所有只读件（含 V1 回归输出与复核结论），**不满足 T1–T8 与 B1–B3**。故本件只是规范，不是标注、不是证据、不证明任何语义真值。
5. **引用纪律**：每条结论追到「本会话实跑命令+输出」或「文件:行」；拿不到写「未验」，不补造。编排方给的背景结论（如 `_crdoc_colocated.py` 同域双改 `PASS 5/5`、旧检验伪造锚点 `n_fail=5`、fp/fn 0/0）本会话**未独立复跑**，一律标「沿用记录，未独立复跑」。
6. **未验**是本件的一等公民：凡无法从盘上产物判定的，显式列为靠信任 / 未验，不得写成已证明。

**必现概念索引**：`oracle.author`(§2) / 签名·PKI(§2,§3) / 第三方判据(§3) / 盲·未见(§4) / 302 项·κ·UNVERIFIABLE·工作量(§5) / 最强验证·边界·未验(§6)。

---

## 2 上游指纹（十件）+ 现有 seal 三方性核查

### 2(a) 编排方十件指纹：独立重算 10/10 全匹配

实跑命令（本会话，主命令）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_os6_audit.py
```

输出首段：`WROTE _os6_audit_out.json bytes 9299` / `C1 fingerprints all_match = True n = 10` / `C8 all_match_after_audit = True`。逐行见 `_os6_audit_out.json:checks.C1_fingerprints.rows`（10 行，每行含 declared/computed sha256+bytes 与 `match`）。10 件声明值逐字抄自编排方【编排方指纹】JSON 块，`hashlib.sha256(read_bytes())` 重算，sha256 与字节数**双匹配**：

| # | 文件（相对仓库根） | sha256（声明=重算） | bytes |
|---|---|---|---|
| 1 | `lead/cert_realcheck_20261109/_cr_seal.json` | `63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23` | 4395 |
| 2 | `lead/cert_realcheck_20261109/_cr_real_verify.py` | `3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa` | 21178 |
| 3 | `lead/cert_realcheck_20261109/CERT_REAL_CHECK.md` | `fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014` | 53782 |
| 4 | `lead/cert_realcheck_20261109/_cr_p1_old_check_out.json` | `7c433113755ad64cf779e232efeddc4f39bc325ffef53c9057f2dda8d3f7a007` | 3033 |
| 5 | `lead/cert_realcheck_20261109/_cr_verify_out.json` | `4d224936b7ebdb4a5c5be25b31d226ec965cce72c100d8db5f0ec4d829a73464` | 7921 |
| 6 | `lead/falsifiable_no_relax_20261109/_fnr_check.py` | `94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2` | 28811 |
| 7 | `lead/check_fp_audit_20261109/CHECK_FALSE_ALARM_AUDIT.md` | `464355c08f961a40de2a719c556816a70448a17564f63bdc05d65981f5d09ed4` | 40950 |
| 8 | `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | `f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc` | 52705 |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

`git status --porcelain` 中两件台账为 `MM`、六个只读目录为 `??`，均为**会话开始即有的状态**（见环境 gitStatus 快照）；指纹全匹配证明内容未被本会话改动。`git log -1 --oneline` → `2657458`（未新增 commit）。

### 2(b) 现有 `_cr_seal.json`：结构 / 键集 / `oracle.author`

文件：`lead/cert_realcheck_20261109/_cr_seal.json:1-135`（4,395 B）。本会话 C2 段实读并输出（`_os6_audit_out.json:checks.C2_seal`）：

- **顶层键**：`['items', 'seal_version']`（`:2` / `:134`；`seal_version = "cr-1"`）。**无**第三键。
- **仅 5 项**：`n_items = 5`；每项键集完全相同（10 键）：`anchor, bytes, evidence_lines, evidence_span_sha256, file_sha256, item, n_lines, oracle, quote, roles`（`:3-28` 为一完整样板）。
- **`oracle` 仅 3 子键**：`author, predicate_author, truth`（`:17-21`）。
- **`oracle.author` 5/5 同一字符串**：`independent_blind_adjudicator`（`:18, :44, :69, :95, :121`）；`predicate_author` 5/5 `author_of_V1`；`truth` 5/5 `true`（`all_oracle_truth = [True,True,True,True,True]`），**无负例、无 UNVERIFIABLE**。
- **该字符串是同会话自写**：`_cr_build_seal.py:30-31, :41-42, :52-53, :64-65, :75-76` 五处硬编码 `{"truth": True, "author": "independent_blind_adjudicator", "predicate_author": "author_of_V1"}`，`:83` `seal = {"seal_version":"cr-1","items":[]}`，`:105-107` 规范化写入 `WDIR / "_cr_seal.json"`。`CERT_REAL_CHECK.md:341` 自认「`oracle.author` 是本会话在 `_cr_build_seal.py` 里写入的字符串，不是真第三方」；`:544`「本会话自造，不构成真第三方盲标注」；`:528` 同值。
- **唯一「独立性」检查是字符串不等**：`_cr_real_verify.py:112-114` — `if oracle.get("author","") == oracle.get("predicate_author","") or not oracle.get("author"): problems.append("ORACLE: author not independent / absent")`。配合 `:57-58` `CALLER_BOOLEAN_KEYS` / `:104-106` 忽略调用方布尔，能挡「调用方伪造」，**挡不住「作者字段本身由作者写入」**。

### 2(c) 签名 / PKI 四处阴性（实跑）

同一主命令 C2 段输出：

| 查法 | 输出 | 结论 |
|---|---|---|
| 全 JSON 键树扫 `sign/sig_/signature/pki/pgp/gpg/x509/…/签名/证书/时间戳/公证/不可否认` | `sig_key_hits = []` | 键树无签名字段 |
| 原始 4,395 B 全文扫同词表 | `sig_raw_hits = []` | 字节层无签名串 |
| PGP/CERTIFICATE 起始标记 | `pgp_markers = []` | 无装甲签名 |
| 同目录 `.sig/.asc/.pem/.p7s/.crt/.pub` 及文件名含 sig/sign/pubkey | `sidecars = []`（`cert_dir_file_count = 30`） | 无伴随签名件 |

另：全仓修剪遍历（`os.walk`，跳过 `.git/node_modules/__pycache__/.tmp/vendor/dist`）`n_repo_files_scanned = 300704`，`repo_signature_sidecars = []`（`n_repo_signature_sidecars = 0`）；等价的 shell 查法 `find . -type f \( -name "*.sig" -o -name "*.asc" -o -name "*.p7s" -o -name "*.pem" -o -name "*_pubkey*" -o -name "*.crt" \) -print | head -n 40` → 空（编排方 C1b 同值，本会话用 Python 修剪遍历复现）。`_cr_real_verify.py:31-37` import 仅 `copy/hashlib/json/re/shutil/time/pathlib`，`cr_verify_has_sig_or_crypto_import = False` — **无签名库、无 PKI、无 TSA/RFC3161、无 nonce、无 witness、无时间戳字段**。

`CERT_REAL_CHECK.md:391` 自认「单靠硬编码仍会被同域双改绕过，必须带外签名 / PKI」；`:509` 记同域双改实证 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`（**本会话未重跑该攻击，标沿用记录**）；`:544`「无 PKI / 签名 / 不可否认性」。

### 2(d) 与「真第三方 ORACLE」差在哪 —— 逐条（每条有出处）

时序实跑（C3 段，`_os6_audit_out.json:checks.C3_mtime`）：`_r9s_regress_out.json 14:32:26`、seal `18:33:04`、`_cr_real_verify.py 18:34:15`；`seal_later_than_v1_regress_output = True`。mtime 只是**弱旁证**，但方向违反 `_fnr_check.py:73` 的「produced BEFORE V1 is run」。

| # | 缺口 | 应是什么 | 现状（实跑/实读） | 判定 |
|---|---|---|---|---|
| 1 | **作者身份** | 具名预注册 `ID_REG` + 带外认证材料，与 V1 作者集合交为空 | `oracle.author` 为 5 处硬编码字符串（`_cr_build_seal.py:30-76`）；唯一判据是字符串不等（`_cr_real_verify.py:112-114`） | 无第三方 |
| 2 | **签名 / PKI** | 逐分片签名或带外承诺哈希，封印/常量至少一者在 A 写域外 | 四处全阴性（§2c）；无签名库；`PRE_REGISTERED_SEAL_SHA256` 常量与封印同处 `lead/cert_realcheck_20261109/`（`:44-47`, `CERT_REAL_CHECK.md:509`） | 无 PKI，抗同域双改为零 |
| 3 | **时间 / 盲** | `t0 < t1(标注) < t2(V1 首跑)` 带外可见 | seal mtime 18:33:04 **晚于** V1 回归输出 14:32:26；且 `seal_items_equal_flips = True` / `seal_items_equal_whitelist = True` / `n_seal_flip_intersection = 5`（C2 实跑）⇒ 5 项恰是被测输出选出的 5 对，**标注时已见 V1 输出**，违反 `_fnr_check.py:74` | 盲不成立 |
| 4 | **覆盖** | `|{i:ORACLE(i) defined}| = |I| = 302`（`:81` (C)） | seal 只有 5 项，缺 297 项；C4 实跑 `n_items=302`，5/302 = 0.0166 | 不覆盖 |
| 5 | **标签质量** | 三值 `{0,1,UNVERIFIABLE}`、有负例、双裁决者 + κ | 5/5 全 `true`，单一作者，无 κ、无混淆矩阵、无 CI | 不可复核 |
| 6 | **语义层** | `ORACLE(i)=1` = 「所需语义内容确已交付」的人的逐角色判断（`_fnr_check.py:75-76`） | `CERT_REAL_CHECK.md:530` 明写真校验只判「预注册文本在预注册字节的预注册行上逐字在场且未被篡改」，**不是 ORACLE(i)=1** | 必要非充分 |
| 7 | **工程接入** | `no_relaxation_check` 有 `artifact_text` / `seal_path` 槽 | C5 实跑两个 TypeError（§5e）；`CERT_REAL_CHECK.md:395, :521`、`_WL_WHITELIST_AUDIT.md` 的人工独立 5/5 接不进（`:537`） | 断链 |

⇒ **能力上限**：`未篡改 ∧ 逐字在场` 是 `语义真值` 的**必要非充分**条件；`sha256` 无密钥，不认证「谁算的 / 何时算的」。这一句即本规范全部设计的出发点。

---

## 3 「第三方」可检验判据（四条判据 + 无 PKI 分类 + 最小可信方案）

**核心命题**：**「第三方」不能靠自己声明**。`oracle.author = "independent_blind_adjudicator"`、`author != predicate_author`、`whitelist_sealed=True` / `whitelist_author="independent"`（`_fnr_check.py:229-230`）、「本会话独立复核」自述 —— 四者都是同一会话可任意写入的字符串/布尔，**明确不算判据**。

### 3(a) 四条判据（承 `CERT_REAL_CHECK.md:386-393` 5(c) 四条，逐条给可检验物而非声明）

设 `V1`=被测谓词/回归；`A`=V1 作者集合；`B`=ORACLE 标注者集合；`P`=预注册包（`ID_REG` + `A_REG` + `LABEL_SPEC` + 302 项清单 + κ/覆盖阈值 + 隔离方案）；`H(·)`=`hashlib.sha256(canonical_json(·))`。**T := C1∧C2∧C3∧C4 全部成立；任一不可核即 `UNVERIFIED`，不得记 PASS。**

| 编号 | 判据 | **可检验物（不是声明）** | 可执行检验 | 现状 |
|---|---|---|---|---|
| **C1 作者身份可验证 + 与 V1 作者不同** | 对应 `CERT_REAL_CHECK.md:390` 第 1 条 | `ID_REG`：逐条 `adjudicator_id` + 认证材料（带外签名公钥指纹 / 机构账号 / 双渠道回执）+ 注册时间；`A_REG` 同法；`H(ID_REG)`、`H(A_REG)` 在 V1 运行前带外公布且**不在 A 写域** | 校验端 `hashlib.sha256(ID_REG_bytes) == 带外承诺`；`set(B_ids) ∩ set(A_ids) == ∅` 打印交并两侧；查无共同组织线；逐分片认证材料（禁止单一共享串） | FAIL：`oracle.author` 为硬编码串，无 `ID_REG` |
| **C2 预注册 + 抗同域双改** | 对应 `:391` 第 2 条 | 封印带硬编码期望 `sha256/bytes`，`read_bytes()` 重算；封印时间早于 V1；**封印 / 承诺 / 校验器常量至少一者在 A 写域外**（带外签名 / 第三方存证 / append-only 日志） | `_cr_real_verify.py:77-97` 的读盘重算能力 + **攻击演练**：模拟 A 同步重写封印+常量+内容，要求仍 FAIL（对照 `:509` 现在 PASS） | FAIL：常量与封印同域（`:44-47`），无签名 |
| **C3 不可派生** | 对应 `:392` 第 3 条 | 标注包每条含 `file:line` 逐字引文 + 逐角色正面证据；引文所在交付件 `sha256` 早于 V1；标注包**不含** V1 谓词/守卫词表/`SPECS` 键/`VERDICT`/flip/白名单 | 引文逐字在盘校验（扩 `_cr_real_verify.py:119-131` 到 302 项）；对标注包做 V1 词表扫描，命中即 FAIL；`INPUT_MANIFEST ∩ V1_OUTPUTS == ∅` | FAIL：5 项恰为 flips/白名单（§2d-3） |
| **C4 全覆盖盲标注** | 对应 `:393` 第 4 条 | 每项标签由**未见 V1 输出、未写 V1** 的裁决者作出，`|labels|=|I|=302`；`coverage` 作为**真 FAIL** 条件而非 detail；`UNVERIFIABLE` 单列不参与 PASS | §4 流程 + §5 门禁：`len(items)==302`、每人 `|labels_i|==302`、`coverage_ratio` 进 `problems.append`、κ 与 T1–T8 逐条状态 | FAIL：5/302，coverage 只在 detail（`_fnr_check.py:151-157`; `FALSIFIABLE_NO_RELAX.md:170`） |

**细化判据 T1–T8（逐条，与上表同义展开，供 §5 门禁逐条报状态）**：`T1` 作者身份可验证（`H(ID_REG)` 带外重算）；`T2` 与 V1 作者不同（集合交为空 + 无共同汇报线）；`T3` 未见 V1 输出（`INPUT_MANIFEST ∩ V1_OUTPUTS = ∅` + ACL 日志）；`T4` 标注早于 V1（`t0 H(P) < t1 H(labels_i) < t2 V1 首跑`，哈希带外可见）；`T5` 标注不可由 V1 派生（逐字引文 + 无 V1 词表）；`T6` 作者与分片绑定（逐分片认证材料，禁单一共享字符串）；`T7` ≥2 名互不通气裁决者 + κ；`T8` 抗同域双改（承诺/封印/常量至少一者在 A 写域外，演练必须 FAIL）。出处：`_os_ORACLE_SPEC.md:173-182`（本会话实读）。

### 3(b) 无 PKI 下：哪些能查 / 哪些只能靠制度（分类，如实）

| 类别 | 判据 | **能查（技术可复核）** | **只能靠信任（零技术可查）** |
|---|---|---|---|
| **A 纯哈希/集合可查** | 内容完整性 | `hashlib.sha256` 逐字节重算：文件/区间/规范 JSON 与承诺一致（C1 已 10/10 + seal 本身） | **谁**算的、**何时**算的、承诺是否被同域双改 |
| | 逐字在场 | 行号存在、引文/角色值逐字在认证区间、非指针值（`_cr_real_verify.py:119-131`, `:62-67` `NON_VALUE_RE`） | 引文的语义是否等于「内容已交付」 |
| | 集合/结构 | `B∩A=∅`、`|labels|=302`、键集精确、`UNVERIFIABLE` 计数、κ/覆盖率确定性复算 | `A_REG`/`B` 名单本身是否真实完整、标注者是否真独立作答 |
| **B 弱旁证（不抵赖）** | 时间先后 | 文件 mtime、git commit 时间、邮件 Date 头、第三方仓 push 时间（C3 实跑 mtime） | 本地时钟可改；无 RFC3161 时**不能**作不可否认证据 |
| | 身份 | 机构账号、工号、双渠道回执、公开署名 | 账号盗用 / 代签 / 挂名；无签名则无法把某条标注绑定到某人 |
| **C 只能靠制度** | 未见 V1 输出/源码/彼此标注 | **读没读过，从产物上不可判定**（§4b）。只可给集合排除、ACL 日志、commit-then-reveal 一致性、见证记录 | ★ 全部。任何「未见」自述都是**信任声明**，不是可检验事实 |
| | 承诺确在 V1 前、W 与 A 无串通、302 清单外部完备性、交付件确由某次实跑产生 | 无 | 全部 |
| | 不可否认性 | **无 PKI 时技术上为零** | 全部 |

⇒ 无 PKI 的**上限** = 「可复核的管道 + 制度担保的隔离」，**绝不能声称「已证明独立异源」**（`_os_ORACLE_SPEC.md:210`，本会话 `grep -n "已证明" _os_ORACLE_SPEC.md` 仅 `:210/:259/:465` 三处，全为否定/禁止式，无肯定断言）。

### 3(c) 最小可信方案（按可信度递增；M1 为下限，缺任一环降 `UNVERIFIED`）

- **M1（零 PKI，需带外载体 + 多方见证）**：① `t0` 前把 `P`（`ID_REG`/`A_REG`/`LABEL_SPEC`/302 清单/κ 门槛/覆盖阈值/隔离方案）规范化算 `H(P)` 64-hex；② `H(P)` 发到 **A 无写权限**的载体（公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / 两名见证人各自留存副本 + 带 Date 头回执）；③ 物理/ACL 隔离：标注账号对 `lead/gate_r9sem_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/cert_realcheck_20261109/` 无 read，只拿 32 个原始交付件只读快照（每个含 `sha256/bytes`）；④ 双盲分片 + commit-then-reveal（先交 `H(labels_i)` 后交明文）；⑤ **W 持封印，且封印与校验器硬编码常量分域**；⑥ 检验端先验封印自身哈希 / 带外承诺，忽略调用方布尔。**M1 只到制度级**，不提供不可否认性。
- **M2（推荐）**：在 M1 上用现成身份体系做签名 —— `git commit -S` / minisign / sigstore / 机构 SSO 短时效 token；把「谁、何时、哪份内容」绑定到人。依据 `CERT_REAL_CHECK.md:391, :535` 与 `_os_ORACLE_SPEC.md:473`（推荐 M2）。**注**：既有 `_os_ORACLE_SPEC.md:216` 把 M1 标「——推荐」，与 `:473` 及编排方 `oraclSpec`「M2（推荐）」矛盾；本规范取 **M2 推荐**（复核件 `whatBreaksIt` ③ 已登记该措辞残留）。
- **M3（最强）**：PKI + RFC3161 可信时间戳 + 透明日志（append-only / Merkle），把时序做成可验证事实而非弱旁证。
- **现状明确不可接受**：`_cr_seal.json` 的形状 + `oracle.author` 字符串 + 同域硬编码常量，四条判据全 FAIL。

---

## 4 「盲」可检验判据（三种盲 + 怎么证未见 + 可执行流程 + 靠信任）

### 4(a) 三种盲（互不蕴含，必须分开）

| 层 | 定义 | 本项目具体屏蔽什么 | 出处 |
|---|---|---|---|
| **B1 未见 V1 输出**（最低必须） | 标注时不知 V1 对每项的判定/翻案/VERDICT/白名单 | `_r9s_regress_out.json`、`_fnr_*_out.json`、5 条 flips、白名单、`no_relaxation`、`VERDICT=PASS`、各轮复核结论 | `_fnr_check.py:73-76` 明文要求「does not see V1's outputs」 |
| **B2 未见 V1 源码 / 谓词**（更强） | 不知 `SPECS` 5 键、守卫词表、非值正则、判档逻辑 | `_r9s_predicates.py:371-402` `SPECS`、`_fnr_check.py:62-67` `NON_VALUE_RE`、白名单与 SPECS 同源关系 | 本规范追加（抗同源设计） |
| **B3 未见彼此标注**（双盲） | 各裁决者之间不通气，不看到对方标签/证据/分歧 | 另一人的 `labels_i`、κ 中间结果、仲裁意见 | 本规范追加（抗挂名） |

**B1 ⇏ B2**（看过源码仍可能不知输出）；**B3 ⇏ B1**（多人都看过 V1 输出）。**「盲」不是**不知道项目背景、不是不读交付件原文、不是不知 `LABEL_SPEC` —— 恰恰相反，裁决者**必须**能读到 32 个原始交付件全文，否则无法判语义（`_os_ORACLE_SPEC.md:244`）。

### 4(b) 怎么证明「未见」——如实说：从产物上不可证明

**`X 未读 Y` 是关于一个未发生事件的否定命题，有限产物无法证成**（`_os_ORACLE_SPEC.md:246-259`，本会话实读）。可证的只是「若读了，会留下痕迹」的**必要条件**，每一条都能被更彻底的串通绕过：

| 手段 | 能给出什么 | 不能给出什么 |
|---|---|---|
| 集合排除（可查） | `INPUT_MANIFEST ∩ V1_OUTPUTS = ∅`；标注包不含 V1 词表/VERDICT 字面；302 项 `id` 不含 `flip/whitelisted` 字段 | 看了但没抄 |
| 时序（弱） | 交付件 `sha256` 早于 V1；`t0<t1<t2` 带外承诺 | 本地时钟可改；承诺者与 A 串通（C3 mtime 反例：seal 18:33 > 回归 14:32） |
| commit-then-reveal | `sha256(labels)` 先于 V1 公布、事后重算一致 ⇒ 标签**未在 V1 之后被改写** | 标签在承诺**之前**是否已看过 V1；哈希可在看完后提前算 |
| ACL / 隔离日志 | 标注账号无 read 权限、快照只读、无网络出口 | 线下口头泄露、屏幕共享、同一人换账号；日志本身也在某方控制下 |
| 第三方见证 / 监督 | 在场记录、双渠道回执、访谈纪要 | 见证人串通 |
| 签名 / PKI / TSA | 把「谁、何时、哪份内容」绑定到人 | 签名前的所见所闻（**内容绑定 ≠ 认知状态绑定**） |

⇒ **唯一诚实写法**：「T3/T4/T5 的必要条件全部通过 + 隔离制度已执行并由 [具名第三方] 担保」，并显式标注「**未见本身为制度性假设，非技术可证事实**」。任何「已证明盲」的肯定断言超出可核范围。

### 4(c) 可执行流程 S0–S8（谁 / 何时 / 做什么 / 留什么可核证据）

角色：`A`=V1 作者方（**只提供原始交付件与项清单，不参与标注、不写 ORACLE**）；`W`=见证/监督方（持带外载体，与 A 无共同写域）；`B1,B2`=两名裁决者；`G`=门禁运行方；第三名预注册仲裁者裁分歧。`t0<t1<t2<t3<t4`。

| 步 | 时点 | 谁 | 动作 | 可核证据 |
|---|---|---|---|---|
| S0 | `t0` 前 | A | 冻结 32 交付件 + 302 项清单（**只含 `domain/token/main`**，不含 flip/白名单/VERDICT），逐件 `sha256/bytes/n_lines` | `ARTIFACT_MANIFEST`；C6 实算 32 文件 / 969,049 B / 7,494 行 / 578,353 字符 |
| S1 | `t0` | A+W | 冻结 `P`，算 `H(P)`，W 带外公布并留存副本 | 64-hex + 载体 URL/邮件 Date 头 + 两份见证回执 |
| S2 | `t0–t1` | W+管理员 | 隔离环境：`B1/B2` 对三目录无 read ACL，只给 S0 的 32 文件只读快照 | ACL 导出、快照 sha 清单、管理员签字 |
| S3 | `t1` | B1,B2 | **各自**对全 302 项按 §5b 产出三值标签 + `file:line` + 逐字引文 + 逐角色证据 + 置信度；`UNVERIFIABLE` 单列；彼此不通信；先交 `H(labels_i)` 后交明文 | `labels_1`,`labels_2`, 各自承诺哈希、提交时间凭证、`INPUT_MANIFEST` |
| S4 | `t1–t2` | W | 重算 `sha256(canonical_json(labels_i))` == 承诺；算 κ（§5d）；κ 不过 → 全 302 项重标/换人；分歧交第三名仲裁者 | κ 报告、3×3 混淆矩阵、分歧表、仲裁记录 |
| S5 | `t2` 前 | W | 封 `ORACLE_SEAL` + `P` + 全分片 + 各步哈希；`H(ORACLE_SEAL)` 带外公布；封印件与校验器常量**分域** | `H(ORACLE_SEAL)` 承诺、封印件、T1–T8 逐条核验表 |
| S6 | `t2` | G | **V1 首次运行**（此前不得运行） | 运行日志含起止时间、`predicate_sha`、`seal_sha` |
| S7 | `t3` | G | 先验封印/带外承诺 → 逐件读盘重算 → 查行号/引文/角色 → 忽略调用方布尔 → 按 `_fnr_check.py:78-91` (A)(B)(C)(D)(E) 判定；STALE/UNVERIFIABLE 一律 NON_PASS | `VERIFY_OUT` 含 `n_read_bytes/n_sha256` 计数 |
| S8 | `t4` | W | 揭盲：公开全分片、κ、分歧、同域双改攻击演练（必须 FAIL） | 揭盲包；复核者可重算全部哈希与 κ |

**时序硬条件**：`t0(H(P)) < t1(H(labels_i)) < t2(V1 首跑)`，且 `H(ORACLE_SEAL)` 在 `t2` 前带外可见。**现状违反**（§2d-3）。

### 4(d) 哪些只能靠信任（九条，如实列）

1. 「没看过」本身（B1/B2/B3）；2. `ID_REG` 身份真实性、无共同汇报线；3. 标注者本人作答、无代笔/挂名；4. 带外载体不可篡改与时钟可信；5. 承诺确在 V1 之前；6. **语义判断本身**（`ORACLE(i)=1` 是人的理解，逐字引文可查、语义等价不可机械化）；7. W 与 A 无串通；8. 302 项清单的外部完备性（`I` 来自 `_r9s_regress_out.json` 的 32 域 `per_element`，不是外部真值域）；9. 原始交付件确由某次实跑产生（`_WL_WHITELIST_AUDIT.md:497-498` 已记 75/75、−114.8、`pf2:200`、「乙设计责任人」实存等**未验**；零真机纪律）。

---

## 5 302 项工程规范（是什么 + 输出格式 + UNVERIFIABLE + κ + ★ 工作量）

### 5(a) 302 项是什么（实跑复现）

**不是 302 个文件、不是 302 个域，是 32 个域下 `per_element` 的 302 个 `(domain, token)` 项**（C4 段，`_os6_audit_out.json:checks.C4_universe302`）。

- 载体 `lead/gate_r9sem_20261109/_r9s_regress_out.json`，实算 `sha256=5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25` / `bytes=75673`（`_WL_WHITELIST_AUDIT.md:502` 同值）。
- 构造（精确复现 `_fnr_check.py:354-363`）：遍历 `ref["domains32"]["rows"]`，跳过 `main_missing`，对每行 `per_element` 产 `{"domain":r["domain"],"token":e["token"]}`。实跑输出：`n_items = 302`、`n_distinct_pairs = 302`、`n_domains_rows = 32`、`sum_per_element = 302`、`main_missing_count = 0`、`n_flips = 5`、`n_whitelist = 5`、`n_distinct_tokens = 237`。
- `registered_tokens = ['可重建','实跑输出','改前改后','脚本存在性','需谁批准']`（`_r9s_predicates.py:371` 的 `SPECS` 5 键，本会话 AST 实读）；这 5 个 token 在 302 项中出现 `n_registered_token_occurrences = 10` 次，其余 `n_structurally_untested = 292` 项 token 未登记 ⇒ **`coverage_ratio = 0.0331`**（`FALSIFIABLE_NO_RELAX.md:112`, `:363` 同值）。**292 项结构性不翻案，但仍须盲标，不能跳过**。
- 唯一 0 项域 `zero_element_domains = ['lead/o1prime_reach_20261109/']`（§5c `ANCHOR_UNRESOLVABLE` 实例）。
- ★ 含义：`_fnr_check.py:81` (C) 要求 `|{i:ORACLE(i) defined}|=|I|=302`；现有 seal 5 项且恰为 whitelist 5 对（C2 实跑），是**用被测输出挑出的子集**，不能充当覆盖全集的 ORACLE（`FALSIFIABLE_NO_RELAX.md:157`「ORACLE applies to 5 flips out of 302 items」、`:170`「(C) 覆盖只报告不门禁」）。

### 5(b) 盲标输出格式（逐项模板，未落盘）

**（1）项清单 `ITEMS`（W 冻结，早于 V1）** — `item_id = sha256(canonical_json({domain,token}))[:16]`；**不得**含 `flip/whitelisted/r9_present/r9s_present` 等 V1 字段；`n_items==302` 为硬门禁。

```json
{"item_id":"I0001","domain":"lead/c07_gate_audit_20261109/","main":"C07_SELFCHECK_AUDIT.md",
 "token":"15 项校验","main_sha256":"<64hex>","main_bytes":0,"main_n_lines":0,
 "spec_version":"r9s-20261109"}
```

**（2）单个裁决者一条标注 `LABEL`（必填 8 字段）**

```json
{"item_id":"I0001","adjudicator_id":"B1","label":"DELIVERED",
 "evidence":{"anchor":"lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md:12",
             "evidence_lines":[10,14],"quote":"<逐字引文，>=10 字符>",
             "roles":{"<角色名>":"<具体实值，非指针/未决>"},"span_sha256":"<64hex>"},
 "confidence":"HIGH","rationale":"<为何该角色值构成语义交付，<=200 字>",
 "labeled_at":"<ISO8601>","artifact_manifest_sha256":"<64hex，锁定所读交付件版本>"}
```

- `label ∈ {"DELIVERED"(1), "NOT_DELIVERED"(0), "UNVERIFIABLE"}`（三值，与 `_fnr_REPORT.md:108` 对齐）；`confidence ∈ {HIGH,MEDIUM,LOW}`，`LOW` 须第二人复核。
- `evidence.roles` 必须对 `LABEL_SPEC` 预注册的**每个必需角色**给具体实值；命中 `_fnr_check.py:62-67` `NON_VALUE_RE`（见台账/待判/尚需/是否/并非/不可重建/未验…）即 `INVALID`，不是标签。
- 序列化：`json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",",":")) + "\n"`，`hashlib.sha256(blob.encode("utf-8"))`（沿用 `_cr_build_seal.py:105-111`）。**指纹一律 hashlib**。

**（3）汇总 `ORACLE`（W 封印，模板）**：`oracle_version, n_items=302, pre_registration{H_P, H_artifact_manifest, published_at, out_of_band_ref}, adjudicators[{id,id_reg_ref,label_sha256}], agreement{kappa,n_disagreements,adjudicated}, items[302 × {item_id,final_label,resolved_by,evidence_sha256,confidence}], counts{DELIVERED,NOT_DELIVERED,UNVERIFIABLE}, seal_sha256`（形状见 `_os_ORACLE_SPEC.md:346-359`，本会话实读）。

**硬门禁**：`len(items)==302`；`item_id` 集合 == `ITEMS` 集合；无 V1 字段；每项 `file_sha256/span_sha256` 与盘上重算一致；`counts` 之和 == 302；接入时**必须**给 `no_relaxation_check` 增 `artifact_text`/`seal_path` 两槽（C5 两个 TypeError），并把 `coverage` 做成真 FAIL（`_fnr_check.py:151-157` 现只报告）。

### 5(c) UNVERIFIABLE 规定

**允许且只有 5 种 `reason_code`**：`ARTIFACT_MISSING`（main 不在盘或 sha 与 manifest 不符；C6 `missing=[]`）、`ANCHOR_UNRESOLVABLE`（找不到可判语义的 `file:line`；如 `per_element=0` 的 `lead/o1prime_reach_20261109/`）、`EVIDENCE_TOO_AMBIGUOUS`（原文只有指针/未决/否定；`_WL_WHITELIST_AUDIT.md:497-498` 未验项）、`SPEC_UNDEFINED`（`LABEL_SPEC` 未给该 token 必需角色，237 个不同 token 的长尾）、`OUT_OF_SCOPE`（需真机/活进程/采样才能判定 —— 铁律禁止，一律此码，不得猜）。

**规定（硬）**：
1. `UNVERIFIABLE` **不是 0、不是 1、不参与 PASS**，单列「未验」（`CERT_REAL_CHECK.md:393`, `FALSIFIABLE_NO_RELAX.md:457`, `lead/whitelist_audit_20261109/WHITELIST_AUDIT.md:508` 同口径；本会话实读 `:508` = 「对全部 302 项用第三方逐项真值表比对；`T==UNVERIFIABLE` 单列「未验」，不参与 PASS」）。注意 `_WL_WHITELIST_AUDIT.md:508` 是表格头，不是该判据，勿混用。
2. 覆盖记账：`n_DELIVERED + n_NOT_DELIVERED + n_UNVERIFIABLE == 302` **且** `n_UNVERIFIABLE > 0 ⇒ 整体 UNCONFIRMED / NON_PASS`，不得报 PASS。**注意口径**：项目既有 `FALSIFIABLE_NO_RELAX.md:188` 写的是 `|{i:ORACLE(i)≠UNVERIFIABLE}|=|I|`（UNVERIFIABLE **不计入**覆盖）—— 故上式是本规范的**设计选择**（三值计数和 == 302），不是对 `:188` 的「精确改写」；复核件 `whatBreaksIt` ⑤ 已登记 `_os_ORACLE_SPEC.md:377` 该措辞不严谨。净效果**不放松**（仍 NON_PASS），但不得冒认与既有定义一致。
3. 必须给 `reason_code` + `rationale` + 第二人复核回执；不得由 A 代填；**禁止为凑 κ 把分歧统一改 `UNVERIFIABLE`**。
4. 报告必须给 `n_UNVERIFIABLE/302` 与逐项清单。
5. STALE（交付件字节变了但认证区间幸存，`CERT_REAL_CHECK.md:285`）→ 转 `UNVERIFIABLE` 并重盲标，绝不自动沿用旧标签。

### 5(d) κ 要求（确定性、可复算）

1. 对象：`B1,B2` 对**同一 302 项**的 `302×2` 三值标签矩阵；统计量 **Cohen's κ = (p_o − p_e)/(1 − p_e)**，`p_o = 一致项数/302`，`p_e = Σ_k (n_{B1,k}/302)(n_{B2,k}/302)`。>2 名改用 **Fleiss κ** 并在 `P` 预注册，禁止事后挑统计量。
2. **必须同时报告**：`p_o`、3×3 混淆矩阵、`n_disagreements`、按 label 分层的 κ、95% CI（bootstrap ≥10000 次固定种子 **或** 解析 SE，二选一在 `P` 预注册）。
3. 先冻结标签（`H(labels_i)` 已带外公布）再算 κ；κ 脚本与输入哈希随揭盲包公开；**禁止先看 κ 再改标签**（改标签即新承诺，重走 S1）。
4. 门槛（`P` 中跑前定死）：κ 点估计 **≥ 0.80**；κ 95% CI 下界 **≥ 0.70**；`p_o` **≥ 0.90**；`|labels_i|==302` 每人；`n_UNVERIFIABLE==0` 才可报 PASS；分歧全部由第三名预注册仲裁者裁定留痕。不过则**重训 `LABEL_SPEC` / 换人 / 全 302 项重标**（不许只重标分歧项，否则泄漏）。同时报 T1–T8 逐条状态。
5. **如实校正（本会话新发现，非沿用）**：`_os_ORACLE_SPEC.md:402` 写「项目内既无 κ 实测值、也无既定门槛」—— 本会话 `python -I -X utf8 -c "<扫 lead/**/*.md 中含 κ/kappa/Cohen 且含 0.x 的行>"` 实跑命中 **16 行**，其中 **κ ≥ 0.8** 确在相邻工作流出现：`lead/comparability_20261109/COMPARABILITY_AUDIT.md:357`、`lead/pvalue_recalc_20261109/PVALUE_RECALC.md:236`、`lead/score_decomp_20261109/SCORE_DECOMP.md:181`（后者自标「本会话未跑，未验」）、`_pv_PVALUE_RECALC.md:247`、`_cmp_AUDIT_20261109.md:312`。**但**这些是 train/dev/test 盲留出集的**另一抽样框**、且均自标未跑/未验；**0.70 CI 下界 / 0.90 p_o / 三值 302 项矩阵在本会话扫描中零命中**；`_fnr_REPORT.md:280` 只写「独立真值双盲 + κ」无阈值，`FALSIFIABLE_NO_RELAX.md:477` 明写「未做 bootstrap / GroupKFold / Cohen's κ」。⇒ 准确表述：**κ≥0.8 在相邻工作流有先例（未验），本规范的 0.80/0.70/0.90 三门槛组合及三值 302 项口径仍为规范建议值**，须 W 在 `t0` 前裁决接受。**本会话未计算任何 κ**（无第三方标签），此条计入 §6 未验项。

### 5(e) P5 两槽（实跑）

`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_os6_audit.py` 的 C5 段（`importlib` 加载 `_fnr_check.py` 为模块，非 `__main__`）输出：

```
C5 {'artifact_text': "no_relaxation_check() got an unexpected keyword argument 'artifact_text'",
    'seal_path': "no_relaxation_check() got an unexpected keyword argument 'seal_path'"}
```

`n_params = 13`，参数表 `items, flips, whitelist, registered_tokens, spec_keys, certificates, spec_roles, predicate, adversarial_corpus, predicate_author, whitelist_author, whitelist_sealed, mutation_payload`，`has_artifact_text = False` / `has_seal_path = False`（`_fnr_check.py:227-231`）。⇒ `CERT_REAL_CHECK.md:537` 的人工独立 5/5 **接不进**，须补两槽后再扩到 302 项。

### 5(f) ★ 工作量估算（数字全部来自 C6 实算）

**基数实跑**（`_os6_audit_out.json:checks.C6_workload`）：读 32 个 `main` 文件，`distinct_main_files = 32`、`missing = []`、`total_bytes = 969049`、`total_lines = 7494`、`total_chars = 578353`、`n_distinct_tokens = 237`；均摊 `chars_per_item = 1915.1`、`mean_bytes_per_item = 3208.8`。

**单名裁决者仅通读全文的下限**：按 400–600 中文技术字符/分钟精读，`read_only_h_at_400cpm = 24.1 h` / `read_only_h_at_600cpm = 16.07 h`。**这还不含查行号、抄逐字引文、逐角色举证、写 rationale ⇒ 「3 分钟/项」在本语料上不现实**（`chars_per_min = 638.4`，高于精读带）。

| 场景 | 每项 | 单人名额 | 2 名独立裁决者 | 仲裁（15% 分歧 ×8min） | 端到端（含 W ≈+8h） | 折算字符/分钟 |
|---|---|---|---|---|---|---|
| 乐观（仅定位+标签） | 3 min | **15.10 h** | **30.20 h** | 6.04 h | **≈ 44.24 h** | 638.4 |
| 基准（读片段+逐角色引文+rationale） | 5 min | **25.17 h** | **50.33 h** | 6.04 h | **≈ 64.37 h** | 383.0 |
| 保守（长尾 token/多角色/回查） | 8 min | **40.27 h** | **80.53 h** | 6.04 h | **≈ 94.57 h** | 239.4 |

- **口径校正（复核件 `whatBreaksIt` ⑤ 已登记）**：`adjudication_h_exact_45p3 = 6.04`（15% × 302 = 45.3 项 × 8min/60）；`adjudication_h_rounded_45 = 6.00`（45 项）。`_os_ORACLE_SPEC.md:96` 写「disagree 15% items = 45」却并列 6.04，两处口径不一；本规范取 **6.04 = 未取整 45.3 项**，并显式标注。端到端 44.24 / 64.37 / 94.57 h 用未取整值，与 `_os_ORACLE_SPEC.md:412-414` 的 ≈44.2/64.4/94.6 一致。
- **结论**：基准 **50.33 人时纯标注**，端到端 **≈ 60–95 人时**；2 人并行按每日有效 6 h ⇒ **约 5–8 个工作日**（不含预注册、隔离搭建、揭盲复核、302 项读盘验证）。**建议按 8 min/项排期**（239.4 字符/分钟，给逐角色抄引文与 rationale 留时间）—— 注意 `_os_ORACLE_SPEC.md:413` 标「基准（推荐 5 min）」而 `:418` 写「建议按 8 min/项」，属基准场景 vs 排期建议的措辞不一，本规范取 **8 min/项排期**。
- **现状对照**：`_cr_seal.json` 只有 5 项、5/5 全 `true`、生成器硬编码（`_cr_build_seal.py:30-76`）⇒ **实际人工盲标投入 = 0**。`_WL_WHITELIST_AUDIT.md:485` 的「独立 5/5」是另一轮复核会话复读原文，`:466` 自警「内容恰好是对的，但机制不能证明它对」，`:497-498` 多项未验 ⇒ **不得按比例外推到 302 项，也不计入本规范产出**。
- 不含 302 项检验端读盘验证：`CERT_REAL_CHECK.md:301` 的 7.482 MB / 7.85 MB 外推自标「估计，未实跑」，**本会话亦未跑**。

---

## 6 复核回件 + 结论 + 未验项

### 6(a) 复核回件（绑定行，格式固定）

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

（本会话实跑复核：`python -I -X utf8 -c "<hashlib.sha256(read_bytes(_cr_seal.json))>"` → `sha256 = 63ebd274…ca23` / `bytes = 4395` / `is_64hex = True`；与编排方【编排方指纹】及 `_os6_audit_out.json:C1_fingerprints.rows[0]` 一致。）

**复核 verdict 如实记**：编排方【复核】件给 `"verdict": "confirmed"`，`sha256Line` 与上绑定行同值，`ranCommands = 17`。本会话据 `_osv_verify_out.json:checks`（`fingerprints.all_match = true`, `n = 10`）、`_os_ORACLE_SPEC.md:427` / `:481` / `:483` 复核其证据链，**未发现复核件 `whatBreaksIt` 所列任一推翻条件触发**（十件指纹未变、全库无签名件、无肯定式「已证明盲」、写域无新 seal、T1–T8 未退化为 author 字符串/调用方布尔、§4c 净效果不放松）。故本件**如实记 `confirmed`**。按交付要求「refuted 或 partial 标 unconfirmed」—— 本次 verdict 非 refuted/partial，**该规则未触发**，不标 unconfirmed。

**复核件登记的残留缺陷（如实沿用，均不改变最终答案）**：① `_os_ORACLE_SPEC.md:192` 把「访问控制日志（或制度声明）」并列为最小可核证据，是「声明即判据」措辞残留（但 `:177` 主 T3 要求 ACL 日志、`:205` C 类、「任一不可核即 UNVERIFIED」兜底，不会产出假 PASS）；② `:216` M1「——推荐」与 `:473` / 编排方 `oraclSpec`「M2（推荐）」矛盾（本规范 §3c 取 M2 推荐）；③ `:377` 称 (C) 为「精确改写」不严谨（本规范 §5c-2 已校正为设计选择）；④ `:96` 6.04 与 45 项口径不一（本规范 §5f 已校正）；⑤ `:413` 5 min 基准与 `:418` 8 min 排期措辞不一（本规范 §5f 已取 8 min 排期）。**本会话新增一条**：`:402`「项目内无既定 κ 门槛」过宽（§5d-5，相邻工作流有 κ≥0.8 先例，均自标未跑/未验）。以上均为措辞/口径，不改变「最强验证 = `INTEGRITY_OK_BUT_UNCONFIRMED`、不能判 `NO_RELAXATION`」。

### 6(b) ★ 当前条件下的最强验证（结论）

**最强 = 「可复核的完整性管道 + 全量结构/集合门禁 + 诚实的未验记账」，其 VERDICT 只能是 `INTEGRITY_OK_BUT_UNCONFIRMED`，不是 `NO_RELAXATION=PASS`。**

依据：`_fnr_check.py:70-92` 的操作化定义要求 ORACLE ① 在 V1 之前产出 ② 由未见 V1 输出、未写 V1 的裁决者作出 ③ 带 published SHA256 seal ④ 覆盖全部 `I`（`:81` (C)）。现状四条全不满足（§2d）。`CERT_REAL_CHECK.md:530`「真校验能判的是…逐字在场且未被篡改…不是 ORACLE(i)=1 的语义判断」、`:512`「自证换了套更好的管道」、`:543-544`「语义真值未独立重判 / 本会话自造不构成真第三方盲标注」；`_WL_WHITELIST_AUDIT.md:466`「内容恰好是对的，但机制不能证明它对」、`:486`「『没放松』不可信」同向。`INTEGRITY_OK_BUT_UNCONFIRMED` 是本规范自创判词（本会话实跑 `grep -rn "INTEGRITY_OK_BUT_UNCONFIRMED\|UNCONFIRMED" lead/ --include=*.md 2>/dev/null | head -20` → 命中 `lead/oracle_spec_20261109/ORACLE_SPEC.md`（本件）、`_os_ORACLE_SPEC.md:377/:398/:427`（同写域规范件）与 `lead/two_products_20261109/TWO_PRODUCTS_ALIGN.md:405/:420`（无关产品件的 `TP-7 UNCONFIRMED` 打印）；零命中项目既有 gate 判词），**未冒认为项目既有判词**。

**它支撑什么（可复核事实）**：
1. `_cr_seal.json` 4,395 B 与承诺 SHA256 一致（C1 10/10 + C2 重算）；`_cr_real_verify.py:77-97` 真读盘重算、`:44-47` 硬编码常量、`:87-92` 失配报错。
2. 封印所指 5 个锚点文件的字节/行/引文/角色值逐字在场且未被篡改（`:119-131`；`CERT_REAL_CHECK.md:530`）。
3. 忽略调用方布尔（`:57-58`, `:104-106`）。
4. 结构门禁可实跑：`n_items==302`、键集精确、集合交并、`UNVERIFIABLE` 单列、κ 可确定性复算、`coverage_ratio=0.0331`（C4）。
5. 同域双改缺口可被显式声明（`:509` 现状会 PASS；本会话**未重跑该攻击**，标沿用）。
6. 诚实记账：T1–T8 全标 `UNVERIFIED`，`n_items_sealed = 5/302`，语义真值层 `302/302` 未验。

**它不支撑什么（越界即错）**：「ORACLE 由真第三方作出」；「语义内容确已交付」= `ORACLE(i)=1`；「302 项全量证明没放松」；「封印不可否认 / 抗同域双改」；「人工独立 5/5 已接入 ORACLE」；「fp/fn=0/0 可外推为总体率」（编排方背景自标 constructed, non-random, NOT a population rate）。**一句话边界**：`未篡改 ∧ 逐字在场` 是 `语义真值` 的**必要非充分**条件；`可复核的管道` ≠ `独立异源真值`（`CERT_REAL_CHECK.md:512`, `:530`）。

### 6(c) 还差什么（逐项可勾清单，按 `_fnr_check.py:78-91` (A)–(E) 与 `CERT_REAL_CHECK.md:532-539`）

**人力** — [ ] ≥2 名未写 V1 / 未参与 V1 设计派发 / 未见 V1 输出的具名裁决者（预注册 `ID_REG`，T1/T2/T7）+ 1 名仲裁者；[ ] 与 A 无共同写域的见证方 W；[ ] 1 名管理员出 ACL/隔离日志；[ ] 1 名独立复核者复算 κ 与全部哈希；[ ] 工作量 §5f 基准 50.33 人时 / 端到端 60–95 人时 / 5–8 工作日，**不得由 A 代标**。

**制度** — [ ] `t0<t1<t2` 先承诺后运行（现状倒置）；[ ] B1/B2/B3 隔离声明，「未见」标为制度性假设（不得写已证明）；[ ] `LABEL_SPEC`、κ 门槛（§5d）、`UNVERIFIABLE` 规则（§5c）、覆盖 `=1.0`、元检验 `n_wrong≥30 / n_good≥30`（`CERT_REAL_CHECK.md:538` 的 `0.904966/0.095034`）全部跑前预注册；[ ] `WHITELIST` 与 `SPECS` 解同源（`_WL_WHITELIST_AUDIT.md:476`, `FALSIFIABLE_NO_RELAX.md:304`②），`VERDICT` 拆三独立布尔（`:477`）；[ ] 揭盲公开全分片、κ、分歧、攻击演练、未验清单。

**技术** — [ ] 给 `no_relaxation_check` 增 `artifact_text`/`seal_path` 两槽（C5 两个 TypeError）并扩到 302 项；[ ] 302 项 `ORACLE_SEAL`：形状沿用 `_cr_seal.json:3-28` 的 `file_sha256/bytes/evidence_lines/evidence_span_sha256/quote/roles` + 新加 `adjudicator_id/labeled_at/confidence/reason_code/带外承诺哈希`；[ ] 带外承诺/签名（最低 M1、推荐 M2、最强 M3），**封印与硬编码常量分域**堵 `CERT_REAL_CHECK.md:509`；[ ] 检验端先验封印/签名 → 逐件读盘重算 → 查行号/引文/角色 → 忽略调用方布尔 → STALE 触发重盲标；[ ] `coverage` 做真 FAIL（`_fnr_check.py:151-157` 现只在 detail）；[ ] 302 项 L3/元检验 + ≥30 条一次性封 SHA 的第三方盲留出，报告 Wilson / Clopper-Pearson 区间；[ ] (A) SOUNDNESS、(B) BOUNDED TIGHTENING **代码实装**（`FALSIFIABLE_NO_RELAX.md:170` 记 (B) 未实现）、(D) SENSITIVITY 在 302 项全集跑；[ ] κ 脚本 + bootstrap CI + 混淆矩阵随揭盲包公开。

### 6(d) 判不了什么（本工作 / 本会话，如实列）

1. **判不了 `_fnr_check.py:78-91` 的 `NO_RELAXATION`**：(C) 覆盖需 302 项盲标（本会话 0 项），(A)/(B) 需 ORACLE 语义真值（本会话无）。
2. **判不了任何语义真值**（`CERT_REAL_CHECK.md:543`）：未重读 32 主件全文逐项重判；`_WL_WHITELIST_AUDIT.md:497-498` 的 `pf2:200` /「乙设计责任人」/ 75/75 / −114.8 沿用为**未验**。
3. **判不了「第三方存在 / 盲成立 / 未见」**：本会话是单会话读所有只读件，本身不满足 T1–T8 与 B1–B3；本件只是规范。
4. **判不了不可否认性与抗同域双改**：无 PKI/签名；`CERT_REAL_CHECK.md:509` 的同域双改攻击本会话**未重跑**（只读纪律 + 不生成新 seal）。
5. **判不了 κ、p_o、CI、fp/fn 总体率**：无第三方标签，本会话**未计算任何 κ**；编排方背景 fp/fn 0/0 自标 constructed 非随机语料（`CERT_REAL_CHECK.md:368`, `:545`）。
6. **判不了 5 条白名单机制有效性**（`_WL_WHITELIST_AUDIT.md:466`, `:486`）。
7. **判不了 302 项验证器实跑成本与结果**：`CERT_REAL_CHECK.md:301` 外推自标「估计，未实跑」；本会话只跑 5 项封印的指纹/结构核查与 302 项**清单复算**，未跑 302 项读盘验证，未跑 `_cr_real_verify.py:main()` / `_fnr_check.py:main()`（会回写只读域/既有件）。
8. **判不了 302 项清单的外部完备性**：`I` 来自 `_r9s_regress_out.json` 32 域 `per_element`（C4），非外部真值域。
9. **判不了交付件「确由某次实跑产生」**：零真机纪律（`_WL_WHITELIST_AUDIT.md:497`）。
10. **本规范自身不构成证据**：未标注、未封印、未隔离、未揭盲；M1/M2/M3、κ 门槛、工作量中的「建议/估算」值均为设计值，须 W 在 `t0` 前裁决接受。

### 6(e) 未验项（汇总，逐条标来源）

| # | 未验内容 | 来源 / 状态 |
|---|---|---|
| 1 | 302 项语义真值、5 主件语义裁决 | `CERT_REAL_CHECK.md:543`；本会话 0 项盲标 |
| 2 | 真第三方 ORACLE 是否存在、盲是否成立、未见 | `:544`；本会话不满足 T1–T8/B1–B3 |
| 3 | κ 实测值、p_o、CI、3×3 混淆矩阵 | `FALSIFIABLE_NO_RELAX.md:477`；本会话未算任何 κ |
| 4 | κ≥0.8 相邻工作流先例是否适用于本 302 项口径 | 本会话新发现（§5d-5）；`COMPARABILITY_AUDIT.md:357` 等自标未跑/未验 |
| 5 | fp/fn 总体率 | `CERT_REAL_CHECK.md:368`, `:545`；constructed 非随机语料 |
| 6 | 同域双改攻击、旧检验伪造锚点 `n_fail=5`、L1 修法 demo | `:509`, `:325`, `:490`, `:547`；**本会话未重跑**，仅沿用记录 |
| 7 | 302 项读盘验证成本/结果（7.482 MB 外推） | `:301` 自标估计未实跑；本会话未跑 |
| 8 | 5 条白名单机制有效性、人工独立 5/5 可外推性 | `_WL_WHITELIST_AUDIT.md:466`, `:485-486` |
| 9 | 交付件 `pf2:200` / 「乙设计责任人」/ 75/75 / −114.8 实存与权限 | `_WL_WHITELIST_AUDIT.md:497-498` |
| 10 | (A)(B)(C)(D)(E) 中 (B) 实装、(C) 真门禁、302 项 L3/元检验 | `FALSIFIABLE_NO_RELAX.md:170`；C5 两槽缺位（本会话实跑 TypeError） |
| 11 | 交付件确由某次实跑产生 | 零真机纪律，`:497` |
| 12 | M1/M2/M3 方案、κ 三门槛、工作量估算的接受裁决 | 本规范设计值，须 W 在 `t0` 前裁决；本件未执行 |

### 6(f) 纪律自查（实跑）

- `git log -1 --oneline` → `2657458`（未新增 commit）；`git status --porcelain -- lead/oracle_spec_20261109/` → `?? lead/oracle_spec_20261109/`（未 push、未 commit）。
- 写域文件清单（收尾 `ls -la lead/oracle_spec_20261109/`）：既有 5 件 + 本会话新建 3 件（`_os6_audit.py` 14,866 B、`_os6_audit_out.json` 9,299 B、`ORACLE_SPEC.md` 本件）；`find … -iname "*seal*" -o -name "*.sig" -o -name "*.asc" -o -name "*.pem"` → 空 ⇒ **未生成新 seal、未改任何既有件**。
- 10 件只读指纹在全部读操作结束后重算仍 10/10 全匹配（C8）；两件台账 mtime 2026-11-08 22:26 / 2026-11-06 06:53，未被本会话写。
- 零真机、零采样代码：本会话脚本只做 `read_bytes` / `hashlib.sha256` / `json` / `ast` / `os.walk` / `importlib` 函数级调用；未启动任何游戏进程、未 taskkill、未读活进程内存；`sys.dont_write_bytecode=True` 防 `__pycache__` 新增。
