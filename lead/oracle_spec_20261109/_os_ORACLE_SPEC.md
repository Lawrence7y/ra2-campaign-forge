# 第三方盲标注 ORACLE 最小规范（只做规范设计，不生成 seal）

- 本件路径：`lead/oracle_spec_20261109/_os_ORACLE_SPEC.md`（唯一写域，前缀 `_os_`）
- 日期：2026-11-09。零真机、零采样代码、不 commit / 不 push、不改任何既有只读件、不生成新 seal。
- 本件为**规范设计**，不是一次标注、不是一次检验、不是一份第三方证明。
- 引用约定：`文件:行` = 实读行；`命令` = 本会话实跑命令 + 输出；「未验」= 本会话没做/做不到。

---

## 0 本会话实跑命令与输出（供复核）

**C0 编排方 10 件指纹独立重算**

```
命令：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_os_audit.py
输出：ALL_MATCH = True（10/10）
      lead/cert_realcheck_20261109/_cr_seal.json
        computed_sha256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23
        computed_bytes  = 4395
      （其余 9 件逐行 sha/bytes 见 lead/oracle_spec_20261109/_os_audit_out.json:fingerprints）
```

**C1 seal 结构 / 作者 / 签名（同一脚本的 SEAL 段）**

```
输出：top_keys = ["items", "seal_version"]
      n_items = 5
      item_keys_sorted = ["anchor","bytes","evidence_lines","evidence_span_sha256",
        "file_sha256","item","n_lines","oracle","quote","roles"]
      all_item_keysets_identical = true
      oracle_subkeys_sorted = ["author","predicate_author","truth"]
      all_oracle_authors = ["independent_blind_adjudicator"]
      all_predicate_authors = ["author_of_V1"]
      all_oracle_truth = [true,true,true,true,true]
      all_oracle_truth_types = ["bool"]
      sig_word_key_hits = []       # 全 JSON 树键名无 signature/pki/pubkey/nonce/timestamp… 字样
      sig_word_raw_hits = []       # 原始 4395 B 字节内亦无
      pgp_markers = []
      sidecar_candidates = []      # 同目录 30 个文件，无 .sig/.asc/.pem/.p7s/.crt/.pub，无 sign/sig 文件名
      dir_file_count = 30
```

原盘复核命令（同一结论）：

```
命令：find . -type f \( -name "*.sig" -o -name "*.asc" -o -name "*.p7s" \
        -o -name "*.pem" -o -name "*_pubkey*" -o -name "*.crt" \) -print | head -n 40
输出：（空）—— 全库无 detached signature / 公钥 / 证书文件
命令：python -I -X utf8 -c "<列 _cr_real_verify.py 的 import 行>"
输出：29 from __future__ ... 31 import copy 32 import hashlib 33 import json
      34 import re 35 import shutil 36 import time 37 from pathlib import Path
      → 无 cryptography / ssl / hmac / nacl / gpg / OpenSSL / 签名验证库
```

**C2 302 项来源（独立复算，不采信文字结论）**

```
命令：python -I -X utf8 -c "<读 _r9s_regress_out.json，按 _fnr_check.py:355-363 的构造逐行复现>"
输出：REPRO of _fnr_check.py:355-363: n_items = 302
      distinct (domain,token) = 302
      n_domains_rows = 32
      main_missing count = 0
      n_flips = 5   n_whitelist = 5
      SPECS keys from spec_inventory = ['可重建','实跑输出','改前改后','脚本存在性','需谁批准']
      registered-token occurrences = 10
      structurally_untested = 292   coverage_ratio = 0.0331
      sum_per_element = 302
```

**C3 P5 输入槽（实跑 TypeError）**

```
命令：python -I -X utf8 -c "<importlib 加载 _fnr_check.py，调用 no_relaxation_check(artifact_text='x') ...>"
输出：no_relaxation_check params = ['items','flips','whitelist','registered_tokens',
        'spec_keys','certificates','spec_roles','predicate','adversarial_corpus',
        'predicate_author','whitelist_author','whitelist_sealed','mutation_payload']
      P5_artifact_text_TypeError = no_relaxation_check() got an unexpected keyword argument 'artifact_text'
      P5_seal_path_TypeError     = no_relaxation_check() got an unexpected keyword argument 'seal_path'
```

**C4 标注工作量基数（本会话实算，非假设）**

```
命令：python -I -X utf8 -c "<读 32 个 domain/main 文件，统计字节/行/字符>"
输出：domains 32；per_element_len min/max/sum = 0 / 13 / 302
      zero-element domains = ['lead/o1prime_reach_20261109/']
      main files total bytes = 969049   lines = 7494   missing = []
      mean bytes/item = 3208.8   mean lines/item = 24.8
      n distinct tokens = 237
      distinct main files = 32   total_chars = 578353
      chars per item (302) = 1915.1
      read hours @400 chars/min = 24.1   @600 = 16.07
      scenario 3 min/item -> per_rater_h 15.1  two_raters_h 30.2
      scenario 5 min/item -> per_rater_h 25.17 two_raters_h 50.33
      scenario 8 min/item -> per_rater_h 40.27 two_raters_h 80.53
      disagree 15% items = 45   adjudication_h@8min = 6.04
```

被核对象绑定行（格式按铁律，无路径/括号/反引号/空格插入）：

被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395

---

## 1 第一步：现有 seal 的「第三方性」核查

### 1(a) `_cr_seal.json` 的结构，逐项键集

`lead/cert_realcheck_20261109/_cr_seal.json:1-135`（实读）+ C1：

| 层 | 键集（sorted） | 值/类型 | 出处 |
|---|---|---|---|
| 顶层 | `["items","seal_version"]` | `items`: list[5]；`seal_version` = `"cr-1"` | `_cr_seal.json:2`, `:134` |
| item（**5 项键集完全相同**，C1 `all_item_keysets_identical=true`） | `["anchor","bytes","evidence_lines","evidence_span_sha256","file_sha256","item","n_lines","oracle","quote","roles"]` | 10 键 | `_cr_seal.json:3-28`（另 4 项 `:29-53`、`:54-79`、`:80-105`、`:106-132`） |
| `item` 字段 | 二元 list `[domain, token]` | str,str | `_cr_seal.json:12-15` |
| `anchor` | `文件:行` | str | `_cr_seal.json:4` |
| `bytes` / `n_lines` | 文件字节数 / 行数 | int | `_cr_seal.json:5`, `:16` |
| `evidence_lines` | `[lo,hi]` | list[int,int] | `_cr_seal.json:6-9` |
| `file_sha256` / `evidence_span_sha256` | 全文件 / 认证区间 sha256 | 64-hex str | `_cr_seal.json:10-11` |
| `quote` | 逐字引文 | str | `_cr_seal.json:22` |
| `roles` | 逐角色正面证据字典 | dict[str,str] | `_cr_seal.json:23-27` |
| `oracle` | **`["author","predicate_author","truth"]`** | 3 键，无第 4 键 | `_cr_seal.json:17-21` |

生成路径：`lead/cert_realcheck_20261109/_cr_build_seal.py:83` `seal={"seal_version":"cr-1","items":[]}`；`:85-101` 逐项 `read_bytes()` + `hashlib.sha256` + 认证区间 hash；`:105-107` 规范化 JSON 落盘。

校验路径：`lead/cert_realcheck_20261109/_cr_real_verify.py:44-47` 硬编码 `PRE_REGISTERED_SEAL_SHA256 = "63ebd274…ca23"` / `EXPECTED_SEAL_BYTES = 4395`；`:77-97` `load_seal` 真读盘重算；`:108-117` ORACLE 只从封印取、忽略调用方布尔（`:57-58` `CALLER_BOOLEAN_KEYS`）。

### 1(b) `oracle.author` 的值；所有 item 是否同一作者

- 值：`"independent_blind_adjudicator"`（`_cr_seal.json:18`, `:44`, `:69`, `:95`, `:121`），C1 `all_oracle_authors = ["independent_blind_adjudicator"]` → **5/5 同一个字符串**。
- `predicate_author` 恒为 `"author_of_V1"`（`:19` 等 5 处），C1 `all_predicate_authors = ["author_of_V1"]`。
- `truth` 5/5 都是 `true`（C1 `all_oracle_truth_types=["bool"]`），即**没有一条负例 / UNVERIFIABLE**。
- ★ 这个字符串是**生成器自己写进去的**：`_cr_build_seal.py:30-31`、`:41-42`、`:52-53`、`:64-65`、`:75-76` 五处硬编码 `{"truth": True, "author": "independent_blind_adjudicator", "predicate_author": "author_of_V1"}`。它不是身份凭证、不是签名、不是外部登记。设计件自己承认：`lead/cert_realcheck_20261109/CERT_REAL_CHECK.md:341`「`oracle.author` 是本会话在 `_cr_build_seal.py` 里写入的字符串，不是真第三方」；`:528` 同；`:544`「本会话 `_cr_seal.json` 的 ORACLE 是本会话自造，不构成真第三方盲标注」。
- 唯一被实际执行的「独立性」检查是 `_cr_real_verify.py:112-114`：**字符串不等**（`oracle.author != oracle.predicate_author` 且非空）。字符串相等性可被任意伪造，不构成身份判据（见 §2）。

### 1(c) ★ 有没有任何签名 / PKI / 不可否认性机制？给验证

**结论：没有。四类验证全部为阴性，且有一处实证攻击。**

1. **结构阴性**：C1 `sig_word_key_hits=[]`、`sig_word_raw_hits=[]`、`pgp_markers=[]`、`sidecar_candidates=[]`。顶层只有 `items` / `seal_version`（`_cr_seal.json:1`, `:134`）；`oracle` 只有 3 键（`_cr_seal.json:17-21`）。**无 `signature` / `signer` / `pubkey` / `timestamp` / `nonce` / `cert_chain` / `tsa` / `witness` 任何字段**。
2. **依赖阴性**：`_cr_real_verify.py:31-37` 的 import 只有 `copy/hashlib/json/re/shutil/time/pathlib`（C1），**无任何非对称密码 / 签名验证 / 时间戳库**。`hashlib.sha256` 是**无密钥**摘要：任何能写文件的人都能重算，不提供来源认证或不可否认性。
3. **同域阴性**：`_cr_seal.json` 与硬编码承诺常量 `_cr_real_verify.py:44-47` 同在 `lead/cert_realcheck_20261109/`。设计件 `:509` 记复核员 `_crv_l1_runtime_out.json:36-44` / `_crv_holes_out.json:89-94` 的 H9 实证：同步重写封印 + 记录 hash + 模块内常量后，凭空编造内容得 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`；本会话 `_crdoc_colocated.py` 复现 `fake_seal_sha256=482b14b3…ec7fecb`（`:509`）。`CERT_REAL_CHECK.md:391` 明写「单靠硬编码仍会被同域双改绕过，必须带外签名 / PKI」。**本会话未重跑该攻击**（属只读域既有输出，标「沿用，未独立复现」）。
4. **时间阴性**：`seal` 无时间字段；`_cr_seal.json` mtime `2026-11-09 18:33:04` **晚于** V1 回归输出 `_r9s_regress_out.json` mtime `2026-11-09 14:32:26` 与 `_r9s_predicates.py` `13:00:28`（本会话 `python -I -X utf8 -c "<stat 6 文件>"` 实跑）。即便把 mtime 当证据，它也**不能**满足「标注早于 V1 运行」；且 mtime 可改、无 RFC3161 时间戳，只能作为弱旁证。

⇒ 无 PKI、无签名、无可信时间戳、无外部公证、无不可否认性。**只有完整性（未篡改），没有来源认证（谁标的）与时序认证（何时标的）。**

### 1(d) 就「独立异源」，现有 seal 差在哪（逐条）

| # | 缺口 | 可核证据 | 差在哪个判据 |
|---|---|---|---|
| 1 | **自封作者**：`author` 是被测方自己写的字符串，无身份绑定 | `_cr_build_seal.py:30-31` 等 5 处硬编码；`CERT_REAL_CHECK.md:341`, `:528`, `:544` | 作者身份可验证（§2a-1） |
| 2 | **同会话生成**：封印与生成器、校验器、V1 检验件同处一写域 | `_cr_build_seal.py:18` `WDIR`；`_cr_real_verify.py:40-45`；同目录 30 文件（C1） | 与 V1 作者不同（§2a-2） |
| 3 | **无盲隔离证据**：生成器 `:20-21` 明写「Verbatim quotes were read from these exact lines of the on-disk deliverables」；`_cr_seal.json` 的 `item`/`whitelist` 与 `_r9s_regress_out.json:domains32.whitelist` 5 对完全相同（C2 + `_cr_seal.json:12-15` 等） → 标注时显然已见 V1 的翻案集合 | `_cr_build_seal.py:20-21`；C2 `n_flips=5 n_whitelist=5` | 未见 V1 输出（§2a-3） |
| 4 | **时序倒置**：seal mtime 18:33 > 回归输出 14:32、谓词 13:00；无时间字段 | 本会话 stat 命令；`_cr_seal.json:1-135` 无 timestamp | 标注早于 V1 运行（§2a-4） |
| 5 | **覆盖只有 5/302**：`n_items=5`，且 5 条恰是白名单翻案项 | C1 `n_items=5`；C2 `n_items=302`, `n_flips=5`；`CERT_REAL_CHECK.md:528`「无 302 项标签」 | ORACLE COVERAGE（C）(`_fnr_check.py:81`) |
| 6 | **标签退化**：5/5 全 `truth=true`，无负例、无 `UNVERIFIABLE` | C1 `all_oracle_truth=[true×5]` | 无法估 fp/fn 与 κ；与 `_fnr_check.py:89` 的 ORACLE 定义域 `{0,1}`、`_fnr_REPORT.md:108` 的 `{0,1,UNVERIFIABLE}` 不符 |
| 7 | **无签名字段 / 无外部权威 / 无常量的带外锚定** | C1 四类阴性；`CERT_REAL_CHECK.md:509`, `:391` | 不可否认性、抗同域双改 |
| 8 | **作者判据只是字符串不等** | `_cr_real_verify.py:112-114` | 可被任意改名绕过 |
| 9 | **独立性未经带外承诺**：SHA256 常量与封印同域，无「先公开承诺、后揭盲」证据 | `_cr_real_verify.py:44-47`；`CERT_REAL_CHECK.md:509` | 预注册真实性 |
| 10 | **输入槽缺位**：`no_relaxation_check` 无 `artifact_text` / `seal_path`，真第三方件接不进 | C3 两个 TypeError；`CERT_REAL_CHECK.md:395`, `:521` | 工程可接入性 |

⇒ `_cr_seal.json` 证明的是「**预注册封印所指的字节、行、引文、角色值逐字在场且未被篡改**」（`CERT_REAL_CHECK.md:530` 原话，本会话 C0/C1 独立确认封印本身哈希一致）。它是**必要条件**，不是语义真值、不是独立异源。

---

## 2 第二步：「第三方」的可检验判据（核心）

### 2(a) ★ 「第三方」不能靠自己声明 —— 可检验判据清单

定义：设 `V1` = 被测谓词 / 回归；`A` = V1 作者集合；`B` = ORACLE 标注者集合；`P` = 预注册包（身份登记 + 标注规范 + 项清单 + 承诺哈希）。
**T（第三方）:= 下列 T1–T8 全部同时成立**，任何一条不可核即标 `UNVERIFIED`，不得记 PASS。

| 编号 | 判据 | **可检验物（不是声明）** | 检验方法（可执行） |
|---|---|---|---|
| **T1** | 作者身份可验证 | 预注册身份登记 `ID_REG`：每条含 `adjudicator_id` + 认证材料（带外签名公钥指纹 / 机构账号 / 双渠道回执）+ 注册时间；`ID_REG` 自身 SHA256 在 V1 运行前**带外公布**（邮件列表 / 公开只读仓 / 第三方存证），且该承诺不在 `A` 的写域 | 校验端 `hashlib.sha256(ID_REG_bytes)` == 带外承诺；逐条查认证材料；`ID_REG` 中不含 `A` 的任何成员 |
| **T2** | 与 V1 作者不同 | V1 作者清单 `A_REG`（同法带外预注册）+ 版本控制作者字段 / 账号归属 | 集合判据 `set(B_ids) ∩ set(A_ids) == ∅`，且 `∀b∈B: org(b) != org(a)` 无共同汇报线；输出 `intersection` 与两侧 id 列表供复核 |
| **T3** | 未见 V1 输出 | ① `P` 中**只有原始交付件**的 `sha256/bytes`，**不含** `_r9s_regress_out.json` / `_fnr_*_out.json` / VERDICT / flip 表 / 白名单；② 标注输入清单 `INPUT_MANIFEST`（逐文件 sha256）中不含任何 V1 产物；③ 物理/权限隔离的**访问控制日志**（标注方账号对 V1 目录无 read ACL，或 V1 产物在标注窗口后才生成） | ① 对 302 项 `id` 与 V1 输出键集比对，要求交集为空或仅有「项清单」这一最小必要交集且该清单本身早于 V1；② `set(INPUT_MANIFEST) ∩ set(V1_OUTPUTS) == ∅`；③ 日志按时间窗核对（无日志 → 只能靠制度，见 2c） |
| **T4** | 标注时间早于 V1 运行 | **先承诺后揭盲链**：`t0` 公布 `H(P)`（64-hex）；`t1` 标注方提交 `H(labels)` 与标注包；`t2` V1 首次运行；要求 `t0 < t1 < t2`，且 `H(labels)` 在 `t2` 之前已出现在**不受 A 控制**的载体 | 校验端重算 `sha256(canonical_json(labels))` == `H(labels)`；比对三个时间凭证。**注意**：无 PKI 时本地 mtime 只是弱旁证 |
| **T5** | 标注内容不可由 V1 派生 | 标注包中每条含 `file:line` 逐字引文 + 逐角色正面证据；引文所在的交付件 `sha256` 早于 V1；标注包**不含**任何 V1 谓词/守卫词表/SPECS 键 | 引文逐字在盘校验（沿用 `_cr_real_verify.py:119-131` 的能力，但扩展到 302 项）；对标注包做 V1 词表扫描，命中即 FAIL |
| **T6** | 作者与标注内容绑定（防「挂名」） | 每个 `adjudicator_id` 对**自己的**标注分片产出可核验的认证材料（签名 / 双渠道回执 / 一次性口令本）；不是单个作者的统一字符串 | 逐分片校验；若仅有一个共享字符串 → 等同 1(b) 的失败模式，判 FAIL |
| **T7** | 多源 | ≥2 名互不通气的裁决者（`B` 至少 2），各自独立分片；任一分片与 V1 作者重合则整体 FAIL | 输出 `n_adjudicators`、分片映射、κ（§4d） |
| **T8** | 不可否认 / 抗同域双改 | 承诺哈希 + 标注包 + 校验器常量**至少三者之一**位于 `A` 写域之外（带外签名 / 第三方存证 / 公证 / append-only 日志） | 攻击演练：模拟 `A` 同步重写封印 + 常量 + 内容，要求仍 FAIL（对照 `CERT_REAL_CHECK.md:509` 现在会 PASS） |

**反模式（明确不算判据）**：`oracle.author = "independent_blind_adjudicator"`（`_cr_seal.json:18`）；`author != predicate_author` 的字符串比较（`_cr_real_verify.py:112-114`）；`whitelist_sealed=True` / `whitelist_author="independent"` 这类调用方布尔（`_fnr_check.py:230`）；「本会话独立复核」的自述。这四类都是**同一会话可任意写入的字符串/布尔**，无可检验的出处链。

### 2(b) 四项必覆盖判据的落地对照

| 要求 | 对应编号 | 最小可核证据 |
|---|---|---|
| 作者身份可验证 | T1 + T6 | `ID_REG` 带外承诺哈希 + 逐分片认证材料 |
| 与 V1 作者不同 | T2 + T7 | `A_REG` vs `B` 集合交为空 + 无共同组织线 |
| 未见 V1 输出 | T3 + T5 | `INPUT_MANIFEST` 与 V1 产物集合交为空 + 访问控制日志（或制度声明） |
| 标注时间早于 V1 运行 | T4 + T8 | `t0<t1<t2` 的带外时间戳 + 承诺哈希重算一致 |

### 2(c) ★ 无 PKI 时：哪些还能查 / 哪些只能靠制度（分类，如实）

| 类别 | 判据 | 无 PKI 下能查到什么 | 剩余只能靠信任 |
|---|---|---|---|
| **A 类：纯密码学可查（有密钥无关）** | 内容完整性 | `hashlib.sha256` 逐字节重算：文件/区间/规范 JSON 是否与承诺一致（C0/C1 已实跑 10/10 + seal 本身） | **谁**算的、**何时**算的、承诺是否被同域双改（CERT_REAL_CHECK.md:509 实证可绕） |
| | 逐字在场 | 行号存在、引文/角色值逐字在认证区间内（`_cr_real_verify.py:119-131`） | 引文的语义是否等于「内容已交付」 |
| | 集合/结构判据 | `B∩A=∅`、`|labels|=302`、键集精确匹配、`UNVERIFIABLE` 计数 | `A_REG`/`B` 名单本身是否真实、完整 |
| | κ / 覆盖率 / 阈值 | 可完全确定性复算（§4d） | 标注者是否真的独立作答 |
| **B 类：弱旁证（可查但不抵赖）** | 时间先后 | 文件 mtime、git commit 时间、日志时间、邮件 Date 头、第三方仓 push 时间 | 本地时钟/系统时间可改；无 RFC3161 时**不能**作不可否认证据 |
| | 身份 | 机构账号、工号、双渠道回执、公开网页署名 | 账号被盗用 / 代签 / 挂名；无签名则无法把某条标注绑定到某个人 |
| **C 类：只能靠制度（零技术可查）** | 未见 V1 输出 / 未见 V1 源码 / 未见彼此标注 | **读没读过，从产物上不可判定**（见 §3b）。只能靠：物理隔离、权限 ACL、签署保密/隔离声明、监督员在场、标注顺序登记、事后访谈 | ★ 全部。任何「未见」的自述都是**信任声明**，不是可检验事实 |
| | 标注者确实本人作答 | 无生物/签名绑定时不可查 | 全部（署名真实性、无代笔） |
| | 承诺在 V1 前已公开 | 带外载体若也由 A 控制则不可查 | 第三方存证机构/见证人的诚实 |
| | 不可否认性 | **无 PKI 时技术上为零** | 全部 |

⇒ 无 PKI 能达到的**上限**是「**可复核的管道 + 制度担保的隔离**」，绝不能声称「已证明独立异源」。

### 2(d) 「最小可信方案」：PKI 成本太高时可接受的替代

按可信度递增，给出**最低可接受组合**（M1 为下限，缺任一环即降为 `UNVERIFIED`）：

**M1（最低，零 PKI 但需带外载体 + 多方见证）——推荐**
1. **预注册**（V1 运行前）：把 `ID_REG`（作者名单/机构/分片）、`LABEL_SPEC`（§4b 模板）、302 项清单、κ 门槛、覆盖阈值写成 `P`，`sha256(canonical_json(P))` → 64-hex。
2. **带外公布**：该 64-hex 发到 **A 无写权限**的载体：公开只读 gist / 邮件列表存档 / 第三方 append-only 日志 / 两名见证人各自留存副本 + 回执（含 Date 头）。**这一步替代 PKI 的时序与不可否认性，但只是制度级**。
3. **物理隔离**：标注方账号对 `lead/gate_r9sem_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/cert_realcheck_20261109/` 无读权限；只拿 32 个原始交付件的只读快照（每个含 `sha256/bytes`）。留 ACL 截图 / 日志。
4. **双盲分片**：≥2 名裁决者各自独立标全 302 项（或交叉分配后互换复核），彼此不通信；各自产出 `labels_i` 与 `sha256(canonical_json(labels_i))`，**先交哈希、后交明文**（commit-then-reveal）。
5. **封印与揭盲**：监督员汇总、算 κ、仲裁分歧；最终 `ORACLE` + 全部原始分片 + `P` + 各步哈希一并封 `sha256`，与校验器常量**分域存放**（常量硬编码在 A 写域外的构建产物里，或至少让封印由见证方持有）。
6. **检验端**：先验封印自身哈希/带外承诺，再逐件读盘重算、查行号/引文/角色、忽略调用方布尔（`_cr_real_verify.py:57-58`, `:108-117` 的能力），STALE → 重盲标（`CERT_REAL_CHECK.md:285`）。**补上 `artifact_text` / `seal_path` 槽**（C3）。

**M2（更强，仍无需自建 CA）**：用现成身份体系做**签名**：`git commit -S`（已有 GPG/SSH 密钥）、`minisign` / `age` 单密钥、`sigstore` / GitHub OIDC 签名、机构 SSO 签发的短时效 token。只需一对密钥 + 公钥指纹带外公布，即可把 T1/T4/T6/T8 从制度级升到密码级。

**M3（最强）**：PKI + RFC3161 时间戳 + 公开透明日志（证书透明 / append-only），实现真正的不可否认。

**明确不可接受**：仅 `_cr_seal.json` 形状 + 作者字符串 + 同域硬编码常量（现状，§1）；仅在报告里写「由独立方标注」；仅 mtime；仅「本会话/本复核轮自述独立」。

---

## 3 第三步：「盲」的可检验判据

### 3(a) 「盲」指什么 —— 三层必须分开

| 层 | 定义 | 对本项目具体屏蔽什么 | 可核程度 |
|---|---|---|---|
| **B1 未见 V1 输出**（**最低必须**） | 标注时不知道 V1 对每项的判定/翻案/VERDICT/白名单 | `_r9s_regress_out.json`、`_fnr_*_out.json`、5 条 flips、白名单、`no_relaxation=True`、`VERDICT=PASS`、各轮复核报告结论 | 部分（集合比对 + 隔离日志；读没读过不可从产物判定） |
| **B2 未见 V1 源码 / 谓词**（更强） | 不知道 `SPECS` 5 键、守卫词表、非值正则、判档逻辑 | `_r9s_predicates.py:371-402` 的 `SPECS`、`_fnr_check.py:62-67` `NON_VALUE_RE`、白名单与 SPECS 同源关系 | 部分（标注包做词表扫描；但「知道」不可查） |
| **B3 未见彼此标注**（双盲） | 各裁决者之间不通气、不看到对方标签/证据/分歧 | 另一人的 `labels_i`、κ 中间结果、仲裁意见 | 部分（提交顺序 + 隔离；不可从产物判定） |

**B1 是 `_fnr_check.py:73-76` 明文要求的最低层**：ORACLE「produced BEFORE V1 is run, by an adjudicator who does not see V1's outputs and did not author V1, with a published SHA256 seal」。B2/B3 是本项目为抗「同源设计」与「挂名」追加的规范。**三者互不蕴含**：做到 B1 不等于 B2（看过源码仍可能不知输出），做到 B3 不等于 B1（多人都看过 V1 输出）。

**「盲」不是**：不知道项目背景、不知道交付件原文、不知道标注规范。恰恰相反，裁决者**必须**能读到 32 个原始交付件全文与 `LABEL_SPEC`，否则无法判语义。混淆这两者会把规范写成不可执行。

### 3(b) ★ 怎么证明「未见」——如实说：从产物上不可证明

**结论：`X 未读 Y` 是关于一个未发生事件的否定命题，有限产物无法证成。** 可证的只是「若读了，会在产物/日志上留下痕迹」的那些**必要条件**，且每个都能被更彻底的串通绕过。分级如下：

| 手段 | 能给出什么 | 不能给出什么 | 落到本项目 |
|---|---|---|---|
| **集合排除（可查）** | 标注包 `INPUT_MANIFEST` 与 V1 产物集合交为空；标注包不含 V1 谓词/词表/VERDICT 字面；302 项 `id` 中不含 `flip`/`whitelisted` 字段 | 看了但没抄 | 用 C2 的 302 项 `(domain,token)` 清单作唯一允许的项清单；比对 `domains32.flips` 5 条与 `whitelist` 5 对不得出现在标注包 |
| **时序（弱）** | 原始交付件 `sha256` 早于 V1；`t0<t1<t2` 的带外承诺 | 本地时钟可改；承诺者与 A 串通 | C1 的 mtime 反例（seal 18:33 > 回归 14:32）正是失败例 |
| **commit-then-reveal（可查一致性）** | `sha256(labels)` 先于 V1 公布，事后重算一致 → 标签**未在 V1 之后被改写** | 标签**在承诺之前**是否已看过 V1；哈希可在看完后提前算 | 只锁「事后不改」，不锁「事前未见」 |
| **ACL / 隔离日志（可查记录）** | 标注账号对 V1 目录无读权限、快照只读、无网络出口的标注环境 | 线下口头泄露、屏幕共享、同一人换账号 | 需第三方管理员出具日志；日志本身也在某方控制下 |
| **第三方见证 / 监督（制度）** | 在场记录、双渠道回执、访谈纪要 | 见证人串通 | 完全靠信任 |
| **密码学（PKI/TSA）** | 签名 + 时间戳把「谁、何时、哪份内容」绑定到人 | 签名前的所见所闻 | 仍是「内容绑定」，不是「认知状态绑定」 |

⇒ **唯一诚实的写法**：把「未见」表述为「**T3/T4/T5 的必要条件全部通过 + 隔离制度已执行并由 [具名第三方] 担保**」，并显式标注「**未见本身为制度性假设，非技术可证事实**」。任何声称「已证明盲」的说法都超出可核范围。

### 3(c) 可执行的流程（谁 / 何时 / 做什么 / 留什么可核证据）

角色：`A` = V1 作者方（**只提供原始交付件与项清单，不参与标注、不写 ORACLE**）；`W` = 见证/监督方（持带外载体，与 A 无共同写域）；`B1,B2` = 两名裁决者；`G` = 门禁运行方。`t0<t1<t2<t3<t4`。

| 步 | 时点 | 谁 | 动作 | 留下的可核证据 |
|---|---|---|---|---|
| S0 | `t0` 之前 | A | 冻结 32 个交付件 + 302 项清单（**只含 `domain/token/main`**，不含 flip/白名单/VERDICT），逐件 `sha256/bytes/n_lines` | `ARTIFACT_MANIFEST`；C2/C4 已实算 32 文件 / 969,049 B / 7,494 行 / 578,353 字符 |
| S1 | `t0` | A+W | 冻结 `P` = `LABEL_SPEC`(§4b) + `ID_REG` + `A_REG` + 302 清单 + κ/覆盖阈值 + 隔离方案；算 `H(P)`；W 把 `H(P)` 发到 A 无写权的载体并留存副本 | `H(P)` 64-hex + 载体 URL / 邮件存档 Date 头 + 两份见证回执 |
| S2 | `t0`–`t1` | W+管理员 | 建隔离标注环境：`B1/B2` 账号对 `lead/gate_r9sem_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/cert_realcheck_20261109/` 无 read ACL；只读快照仅含 S0 的 32 文件 | ACL 导出、快照 `sha256` 清单、管理员签字 |
| S3 | `t1` | B1, B2 | **各自**对 302 项逐项按 §4b 产出标签 + `file:line` + 逐字引文 + 逐角色证据 + 置信度；`UNVERIFIABLE` 单列；彼此不通信；先交 `H(labels_i)` 给 W，后交明文 | `labels_1`, `labels_2`，各自的 `H(labels_i)`，提交时间凭证，`INPUT_MANIFEST` |
| S4 | `t1`–`t2` | W | 重算 `sha256(canonical_json(labels_i))` == 各自承诺；算 κ（§4d）；κ<门槛 → 返工/换人；分歧交第三名仲裁者（其身份同样预注册） | κ 报告、分歧表、仲裁记录、最终 `ORACLE` |
| S5 | `t2` 之前 | W | 把最终 `ORACLE` + `P` + 全部分片 + 各步哈希封成 `ORACLE_SEAL`，`sha256` → 64-hex；**W 带外公布**该哈希；封印件与校验器常量分域 | `H(ORACLE_SEAL)` 带外承诺、封印件、`T1–T8` 逐条核验表 |
| S6 | `t2` | G | **V1 首次运行**（此前不得运行），产出回归输出 | 运行日志含起止时间、`predicate_sha`、`seal_sha` |
| S7 | `t3` | G | 检验端先验封印/带外承诺 → 逐件读盘重算 → 查行号/引文/角色 → 忽略调用方布尔 → 按 `_fnr_check.py:78-91` 的 (A)(B)(C)(D)(E) 判定；STALE/UNVERIFIABLE 一律 NON_PASS | `VERIFY_OUT`，含 `n_read_bytes/n_sha256` 计数（对照 `CERT_REAL_CHECK.md:301` 的 302 项外推 7.482 MB 估计；本会话**未实跑 302 项验证**） |
| S8 | `t4` | W | 揭盲：公开全部分片、κ、分歧、攻击演练（模拟同域双改必须 FAIL） | 揭盲包；复核者可重算全部哈希与 κ |

**时序硬条件**：`t0(H(P)) < t1(H(labels_i)) < t2(V1 首跑)`，且 `H(ORACLE_SEAL)` 在 `t2` 前已带外可见。现状违反此条件（§1d-4）。

### 3(d) 哪些环节只能「靠信任」——如实列

1. **「没看过」本身**（B1/B2/B3）：读没读过不可从产物判定；只能信隔离制度、见证人、裁决者自述。
2. **作者身份的真实性**：无 PKI 时，`ID_REG` 里的身份、机构、无共同汇报线，靠人事/机构记录与见证人。
3. **标注者本人作答、无代笔/挂名**：无签名时不可查。
4. **带外载体的不可篡改与时钟可信**：邮件存档 / 公开仓 / 见证人副本可能被 A 影响；本地 mtime/git 时间可改。
5. **承诺确实发生在 V1 之前**：除带外时间戳外不可查；`commit-then-reveal` 只锁「事后未改」。
6. **语义判断本身**：`ORACLE(i)=1` 意为「语义内容确已交付」（`_fnr_check.py:75-76`），这是人的理解；逐字引文可查，**语义等价不可机械化**。
7. **监督方 W 与 A 无串通**：只能靠组织独立性。
8. **302 项清单的完备性**：`I` 是否穷尽真实项目域，取决于清单冻结时的人工判断（C2 的 302 是 `_r9s_regress_out.json` 里 32 域的 `per_element`，不是外部真值域）。
9. **原始交付件本身真实**：`WHITELIST_AUDIT.md:497-498` 已记 `:69-71` 载荷、75/75、−114.8、「乙设计责任人」实存等**未验**；沿用而不补造。

---

## 4 第四步：302 项盲标的工程规范

### 4(a) ★ 302 项是什么（去读 `_r9s_regress_out.json` 确认）

**不是 302 个文件，也不是 302 个域；是 32 个域下 `per_element` 的 302 个 `(domain, token)` 项**（C2）。

- 载体：`lead/gate_r9sem_20261109/_r9s_regress_out.json`，本会话实算 `sha256=5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25`，`bytes=75673`（`_os_audit_out.json:universe302`；`_WL_WHITELIST_AUDIT.md:502` 亦记同值）。
- 顶层键：`baseline_sha256 / domains32 / four_domains / four_domains_total_remaining / no_relaxation / r9_pred_bytes / r9_pred_recomputed / r9_pred_sha256 / samples / spec_inventory / verdict`（C0 脚本输出）。
- `domains32`：`n_domains=32`、`rows=32`、`flips=5`、`n_flips=5`、`tightens=0`、`whitelist=5`（C2）。
- 构造（精确）：`lead/falsifiable_no_relax_20261109/_fnr_check.py:355-363` 遍历 `ref["domains32"]["rows"]`，跳过 `r.get("main_missing")` 的域，对每行 `per_element` 各产一项 `{"domain":r["domain"],"token":e["token"]}`。本会话复现：`n_items=302`、`distinct (domain,token)=302`、`main_missing count=0`、`sum_per_element=302`。
- 分布（C4）：`per_element` 长度 min 0 / max 13 / sum 302；唯一 0 项域 `lead/o1prime_reach_20261109/`；32 个 `main` 文件全在盘，共 969,049 B / 7,494 行 / 578,353 字符；237 个不同 token，最高频 `未验`(31)、`未改任何文件`(15)、`需谁批准`(6)。
- `spec_inventory` 只有 5 键（C2）；302 项里这 5 个已登记 token 出现 **10 次**，其余 **292 项结构性不可能翻案**，`coverage_ratio=0.0331`（`FALSIFIABLE_NO_RELAX.md:112` 同值）。
- ★ 关键含义：`_fnr_check.py:81` 的 (C) 要求 `|{i:ORACLE(i) defined}|=|I|=302`。**现有 seal 只有 5 项**（C1），且这 5 项恰是 `whitelist` 的 5 对（`_cr_seal.json:12-15` 等 vs C2 `whitelist`），即**用被测输出挑出来的子集**，不能充当覆盖全集的 ORACLE。`FALSIFIABLE_NO_RELAX.md:157`「ORACLE applies to 5 flips out of 302 items」、`:170`「(C) 覆盖只报告不门禁」同此。
- 现状 `verdict="PASS"`, `no_relaxation=true`（C0）只是同一集合的相等性结论，`_WL_WHITELIST_AUDIT.md:486` 判「不可信」。

### 4(b) 盲标产出格式（逐项模板）

**（1）项清单 `ITEMS`（W 冻结，早于 V1）**

```json
{"item_id":"I0001",
 "domain":"lead/c07_gate_audit_20261109/",
 "main":"C07_SELFCHECK_AUDIT.md",
 "token":"15 项校验",
 "main_sha256":"<64hex>","main_bytes":0,"main_n_lines":0,
 "spec_version":"r9s-20261109"}
```

`item_id` = `sha256(canonical_json({domain,token}))[:16]`（确定性、可重算）；**不得**含 `flip` / `whitelisted` / `r9_present` / `r9s_present` 等 V1 字段（T3/T5）。共 302 行，`n_items=302` 为硬门禁。

**（2）单个裁决者的一条标注 `LABEL`（必填 8 字段）**

```json
{"item_id":"I0001",
 "adjudicator_id":"B1",
 "label":"DELIVERED",
 "evidence":{"anchor":"lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md:12",
             "evidence_lines":[10,14],
             "quote":"<逐字引文，>=10 字符>",
             "roles":{"<角色名>":"<具体实值，非指针/未决>"},
             "span_sha256":"<64hex>"},
 "confidence":"HIGH",
 "rationale":"<为何该角色值构成语义交付，<=200 字>",
 "labeled_at":"<ISO8601>",
 "artifact_manifest_sha256":"<64hex，锁定所读交付件版本>"}
```

- `label ∈ {"DELIVERED"(1), "NOT_DELIVERED"(0), "UNVERIFIABLE"}`；**三值**，与 `_fnr_REPORT.md:108` 的 `{0,1,UNVERIFIABLE}` 对齐（比 `_fnr_check.py:73` 的 `{0,1}` 多一档，用于诚实记未验）。
- `id / domain / token / 真值 / 证据 / 置信度` 六项全部覆盖；另加 `adjudicator_id`（T6 分片绑定）、`rationale`（可复核性）、`labeled_at`（T4 弱旁证）、`artifact_manifest_sha256`（防 STALE）。
- `evidence.roles` 必须对 `LABEL_SPEC` 为该 token 预注册的**每个必需角色**给具体实值；命中 `_fnr_check.py:62-67` `NON_VALUE_RE`（见台账/待判/尚需/是否/并非/不可重建/未验…）即判 `INVALID`，不是标签。
- `confidence ∈ {"HIGH","MEDIUM","LOW"}`；`LOW` 不得单独支撑 PASS，须第二人复核。
- 规范序列化：`json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",",":"))` + `\n`，`hashlib.sha256(blob.encode("utf-8"))`（沿用 `_cr_build_seal.py:105-111` 的规范化做法）。**指纹一律 hashlib**。

**（3）汇总 `ORACLE`（W 封印）**

```json
{"oracle_version":"os-1","n_items":302,
 "pre_registration":{"H_P":"<64hex>","H_artifact_manifest":"<64hex>",
                     "published_at":"<ISO8601>","out_of_band_ref":"<URL/邮件存档>"},
 "adjudicators":[{"id":"B1","id_reg_ref":"...","label_sha256":"<64hex>"},
                 {"id":"B2","id_reg_ref":"...","label_sha256":"<64hex>"}],
 "agreement":{"kappa":0.0,"n_disagreements":0,"adjudicated":[]},
 "items":[{"item_id":"I0001","final_label":"DELIVERED","resolved_by":"BOTH_AGREE",
           "evidence_sha256":"<64hex>","confidence":"HIGH"}],
 "counts":{"DELIVERED":0,"NOT_DELIVERED":0,"UNVERIFIABLE":0},
 "seal_sha256":"<64hex，规范化后自指留空/由 W 带外公布>"}
```

**硬门禁**：`len(items)==302`；`item_id` 集合 == `ITEMS` 集合；无 V1 字段；每项 `evidence` 的 `file_sha256/span_sha256` 与盘上重算一致；`counts` 之和 == 302。接入时**必须**给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 两槽（C3 两个 TypeError；`CERT_REAL_CHECK.md:395`, `:521`），并把 `coverage` 做成真 FAIL 条件（`_fnr_check.py:151-157` 现只报告；`FALSIFIABLE_NO_RELAX.md:170`）。

### 4(c) 「标不了」的项：UNVERIFIABLE 规定

允许且只有以下情形可标 `UNVERIFIABLE`（须给 `reason_code`）：

| code | 触发 | 例（本项目实况） |
|---|---|---|
| `ARTIFACT_MISSING` | `main` 文件不在盘或 `sha256` 与 manifest 不符 | C4 `missing=[]`；若不符即此码 |
| `ANCHOR_UNRESOLVABLE` | 找不到可判语义的 `file:line` | `per_element=0` 的 `lead/o1prime_reach_20261109/`（C4） |
| `EVIDENCE_TOO_AMBIGUOUS` | 原文只有指针/未决/否定，无法给具体实值 | `_WL_WHITELIST_AUDIT.md:497-498` 的 `pf2:200`、「乙设计责任人」实存、75/75、−114.8 等**未验** |
| `SPEC_UNDEFINED` | `LABEL_SPEC` 未给该 token 的必需角色定义 | 237 个不同 token 中的长尾（C4） |
| `OUT_OF_SCOPE` | 需真机/活进程/采样才能判定 | 铁律禁止，一律此码，不得猜 |

**规定（硬）**：
1. `UNVERIFIABLE` **不是 0、不是 1、不参与 PASS**；单列「未验」（`CERT_REAL_CHECK.md:393`, `FALSIFIABLE_NO_RELAX.md:457`, `WHITELIST_AUDIT.md:508` 同一口径）。
2. `_fnr_check.py:81` 的 (C) 要求全覆盖：把 (C) 精确改写为 `n_DELIVERED + n_NOT_DELIVERED + n_UNVERIFIABLE == 302`，但**判定式**里 `UNVERIFIABLE` 记为「未验」，因此只要 `n_UNVERIFIABLE > 0`，**整体 VERDICT = UNCONFIRMED / NON_PASS**，不得报 PASS。这避免用「已定义」偷换「已判定」。
3. 必须给 `reason_code` + `rationale` + 第二人复核签名/回执；不得由 A 代填；不得为凑 κ 把分歧统一改 `UNVERIFIABLE`（防止用未验掩盖低一致性）。
4. 报告必须给 `n_UNVERIFIABLE/302` 与逐项清单；`CERT_REAL_CHECK.md:543` 的「语义真值未独立重判」在非盲标条件下即属此类。
5. STALE（交付件字节变了但认证区间幸存，`CERT_REAL_CHECK.md:285`）→ 该项转 `UNVERIFIABLE` 并重盲标，绝不自动沿用旧标签。

### 4(d) κ（一致性）的计算要求与门槛

**计算要求（确定性、可复算）**
1. 对象：`B1`、`B2` 对**同一 302 项**的独立标签矩阵 `302×2`，标签域为 3 类 `{DELIVERED, NOT_DELIVERED, UNVERIFIABLE}`。
2. 统计量：**Cohen's κ**（2 名裁决者、名义尺度），`κ = (p_o − p_e)/(1 − p_e)`，其中 `p_o = (一致项数)/302`，`p_e = Σ_k (n_{B1,k}/302)(n_{B2,k}/302)`（按边际乘积）。若采用 >2 名，改用 **Fleiss' κ** 并在 `P` 中预注册，不得事后挑统计量。
3. **必须**同时报告：`p_o`、混淆矩阵 3×3、`n_disagreements`、按 `label` 分层的 κ、以及 95% CI（bootstrap ≥10000 次重抽样，固定种子，或解析 SE；二选一在 `P` 预注册）。
4. 计算前**先冻结标签**（commit-then-reveal 的 `H(labels_i)` 已带外公布）；κ 计算脚本与输入哈希随揭盲包公开；禁止先看 κ 再改标签（改标签即新承诺，须重走 S1）。
5. κ 单独不够：须同时报**覆盖门禁** `n_UNVERIFIABLE/302`、`n_items==302`、`T1–T8` 逐条状态。

**门槛（在 `P` 中预注册，跑前定死）**

| 项 | 阈值 | 不过怎么办 |
|---|---|---|
| `κ` 点估计 | **≥ 0.80** | 返工：重训 `LABEL_SPEC`、换裁决者、重标全 302 项（不许只重标分歧项，否则泄漏） |
| `κ` 95% CI 下界 | **≥ 0.70** | 同上；且不得用点估计过线掩盖宽区间 |
| `p_o` | **≥ 0.90** | 同上 |
| `n_UNVERIFIABLE` | **= 0** 才可报 PASS；>0 一律 UNCONFIRMED | 见 §4c |
| 覆盖 | `|labels_i| == 302` 对每名裁决者 | 缺项即 FAIL（对应 `_fnr_check.py:81` 的 (C)） |
| 分歧 | 全部由第三名预注册仲裁者裁定并留痕 | 无仲裁记录 → FAIL |

**说明（如实）**：0.80/0.70/0.90 是**本规范提出的建议阈值**，不是从项目既有文件读到的既有约定——本会话 `grep -rn "kappa|κ|Cohen|Fleiss|一致性"` 命中 `_fnr_REPORT.md:280`（只写「独立真值双盲 + κ」无阈值）与 `FALSIFIABLE_NO_RELAX.md:477`（明写「未做 bootstrap / GroupKFold / Cohen's κ」）。**项目内既无 κ 实测值、也无既定门槛**，此处阈值须由 W 在 `t0` 前裁决接受；本会话**未计算任何 κ**（无第三方标签）。

### 4(e) ★ 盲标工作量估算（302 项 × 每项几分钟 = 多少小时）

**基数来自 C4 实算**：32 个 `main` 文件、969,049 B / 7,494 行 / 578,353 字符；均摊每项 ≈ 1,915 字符 / 24.8 行；237 个不同 token；292 项 token 未登记（结构性不翻案，但仍需盲标，不能跳过）。

**单名裁决者读全文的下限**（C4）：按 400–600 字符/分钟的中文技术文本精读速度，仅**通读** 578,353 字符就需 **16.07–24.10 小时**。这还不含查行号、抄逐字引文、逐角色举证、写 rationale。**故「3 分钟/项」在本语料上不现实。**

| 场景 | 每项耗时 | 单人名额 | 2 名独立裁决者 | 加 κ 计算/仲裁 (15% 分歧×8min) | 总人时（含 W 监督 ≈ +8h） |
|---|---|---|---|---|---|
| 乐观（仅定位+标签，不抄引文） | 3 min | 302×3/60 = **15.10 h** | **30.20 h** | +6.04 h | ≈ 44.2 h |
| **基准（推荐：读片段+逐角色引文+rationale）** | **5 min** | 302×5/60 = **25.17 h** | **50.33 h** | +6.04 h | ≈ 64.4 h |
| 保守（长尾 token / 多角色 / 反复回查） | 8 min | 302×8/60 = **40.27 h** | **80.53 h** | +6.04 h | ≈ 94.6 h |

- **结论：基准 ≈ 50.3 人时纯标注，端到端 ≈ 60–95 人时**；按 2 人并行、每日有效 6 小时计，**约 5–8 个工作日**（不含预注册、隔离环境搭建、揭盲复核）。
- 口径说明：这是**纯人工盲标**的估算，不含 32 文件指纹冻结、`ORACLE_SEAL` 生成、302 项检验端读盘验证（后者按 `CERT_REAL_CHECK.md:301` 的估计约 7.482 MB / 7.85 MB 量级 IO，机器时间毫秒–秒级，可忽略；该 302 项外推在该件自标「估计，未实跑」，本会话亦**未实跑 302 项验证**）。
- 折算校验：均摊每项 1,915 字符（C4）。基准 5 min/项 ≈ 383 字符/分钟，落在 C4 的 400–600 精读速度带下沿且略偏乐观；保守 8 min/项 ≈ 239 字符/分钟，给逐角色抄引文与写 rationale 留出时间，更贴近实际。**建议按 8 min/项排期**。
- 与现状对比：现有 `_cr_seal.json` 只有 5 项、5/5 全 `true`、由生成器硬编码（`_cr_build_seal.py:30-76`），**实际人工盲标投入 = 0**；`_WL_WHITELIST_AUDIT.md:485` 的「独立 5/5」是**另一轮复核会话**复读原文的判定，且 `:466` 自警「这批白名单内容恰好是对的，但机制不能证明它对」，`:497-498` 列多项未验 → **5/5 不能按比例外推到 302 项，也不能计入本规范的第三方盲标产出**。

---

## 5 第五步：结论与建议

### 5(a) ★ 当前条件（无第三方、无 PKI）能做到的最强验证

**结论：最强 = 「可复核的完整性管道 + 全量结构/集合门禁 + 诚实的未验记账」，其 VERDICT 只能是 `INTEGRITY_OK_BUT_UNCONFIRMED`，不是 `NO_RELAXATION=PASS`。**

具体可做到的（均有本会话实跑或实读支撑）：
1. **封印与盘上字节的一致性**：C0 10/10 指纹全匹配；`_cr_real_verify.py:77-97` 真读盘重算、`EXPECTED_SEAL_BYTES=4395` 与 `PRE_REGISTERED_SEAL_SHA256` 比对。
2. **逐字在场校验**：行号存在、引文逐字、角色值逐字在认证区间、非指针值（`_cr_real_verify.py:119-131`, `:51-56`）；伪造锚点 `:999999` 会被 `ANCHOR_NOT_PRE_REGISTERED` 抓（`CERT_REAL_CHECK.md:325`, 编排方给的背景实跑 `n_fail=5`；本会话**未重跑该验证器 main()**，因 `:458-460` 会回写写域既有件，只读纪律禁止——标「沿用编排方/设计件记录，本会话未独立复跑」）。
3. **忽略调用方布尔**：`:57-58` `CALLER_BOOLEAN_KEYS`、`:104-106` `ignored`；`CERT_REAL_CHECK.md:87` 记 5 布尔全伪造仍 PASS 5/5 的反向实证（同一未复跑限定）。
4. **结构门禁**：`n_items==302`、键集精确、集合交并、`UNVERIFIABLE` 单列、`coverage_ratio` 作为真 FAIL（现状只在 detail，`_fnr_check.py:151-157`；`FALSIFIABLE_NO_RELAX.md:170`）。
5. **同域双改的演练必须报 FAIL**：现状会 PASS（`CERT_REAL_CHECK.md:509`），因此**当前最强验证必须显式声明这一残留缺口**，不得隐藏。
6. **诚实记账**：把 `T1–T8` 全标 `UNVERIFIED`，`n_UNVERIFIABLE/302 = 302/302`（语义真值层），`n_items_sealed = 5/302`。

**做不到**：把 `ORACLE(i)=1` 从「字符串」升级为「独立异源语义真值」——这需要 §2 的第三方 + §3 的盲 + §4 的 302 项，三者缺一不可，且其中「未见」「身份」「不可否认」在无 PKI 时只能靠制度（§2c/§3d）。

### 5(b) 最强验证能支撑 / 不能支撑什么（边界）

| 能支撑（可复核事实） | 不能支撑（越界即错） |
|---|---|
| 「`_cr_seal.json` 的 4,395 B 与承诺 SHA256 一致」（C0/C1） | 「ORACLE 由真第三方作出」（§1b/§1d-1） |
| 「封印所指 5 个锚点文件的字节、行、引文、角色值逐字在场且未被篡改」（`CERT_REAL_CHECK.md:530`） | 「语义内容确已交付」= `ORACLE(i)=1`（`:530`, `:341`, `:543`） |
| 「302 项 = 32 域 `per_element`，292 项结构性不翻案，`coverage_ratio=0.0331`」（C2） | 「302 项全量证明没放松」（`FALSIFIABLE_NO_RELAX.md:112`, `:363`） |
| 「旧检验在 `:999999` 伪造锚点上三层全过、新检验会 FAIL」（背景编排方实跑；设计件 `:325`） | 「新校验器在当前语料上 fp=fn=0 可外推为总体率」（编排方背景自标 `constructed, non-random corpus, NOT a population rate`） |
| 「P5 无 `artifact_text`/`seal_path` 槽」（C3 两个 TypeError） | 「人工独立 5/5 已接入 ORACLE」（`CERT_REAL_CHECK.md:537` 明写接不进） |
| 「无签名/PKI/时间戳/不可否认机制」（C1 四类阴性） | 「封印不可否认 / 抗同域双改」（`:509` 实证反例） |
| 「L1 修法 demo 既消误报又抓 padding」（背景编排方实跑；`:440-490`） | 「该 demo 已接入生产检验器」（`:490`, `:547` 明写未接入、部分 unconfirmed） |

**一句话边界**：`未篡改 ∧ 逐字在场` 是 `语义真值` 的**必要非充分**条件；`可复核的管道` ≠ `独立异源真值`（`CERT_REAL_CHECK.md:512`, `:530`）。

### 5(c) 真正判定 NO_RELAXATION 还差什么（人力 / 制度 / 技术，逐项可勾）

按 `_fnr_check.py:78-91` 的 (A)(B)(C)(D)(E) 与 `CERT_REAL_CHECK.md:530`, `:532-539` 的六步方案：

**人力**
- [ ] ≥2 名**未写 V1、未参与 V1 设计/派发、未见 V1 输出**的裁决者，具名并预注册到 `ID_REG`（T1/T2/T7）；建议再加 1 名仲裁者。
- [ ] 1 名与 A 无共同写域的见证/监督方 W，负责 `t0<t1<t2` 与带外承诺。
- [ ] 1 名管理员出具 ACL/隔离日志；1 名独立于 A 的复核者复算 κ 与全部哈希。
- [ ] 工作量：§4e 基准 50.3 人时（2 人）/ 端到端 60–95 人时 / 5–8 工作日；**不得由 A 代标**。

**制度**
- [ ] `t0<t1<t2` 的**先承诺后运行**纪律：V1 首次运行在 ORACLE 封印带外公布之后（现状倒置，§1d-4）。
- [ ] B1/B2/B3 三层盲的隔离声明与保密约定；「未见」如实标为制度性假设（§3b/§3d），不得写成已证明。
- [ ] `LABEL_SPEC`、κ 阈值（§4d）、`UNVERIFIABLE` 规则（§4c）、覆盖阈值 `=1.0`、元检验 n_wrong/n_good 阈值（`CERT_REAL_CHECK.md:538` 建议 ≥30/≥30 → `0.904966/0.095034`）全部**跑前预注册**，不得事后调。
- [ ] `WHITELIST` 与 `SPECS` 解同源（`_WL_WHITELIST_AUDIT.md:476`, `FALSIFIABLE_NO_RELAX.md:304`②）；`VERDICT` 拆成 `whitelist_integrity / flip_semantics / adversarial_robustness` 三个独立布尔（`:477`, `CERT_REAL_CHECK.md:524`）。
- [ ] 揭盲与公开：全部分片、κ、分歧、攻击演练、未验清单一次性公开；`CHECKER_VALID` 纳入 `baseline_VERDICT=="PASS"` 与双基线（`:395`, `:539`）。

**技术**
- [ ] 给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 两槽（C3 两个 TypeError；`:395`, `:521`），把 `WHITELIST_AUDIT.md:467/:498/:516` 的人工独立 5/5 **作为参考而非 ORACLE** 接入（`:537`），再扩到 302 项。
- [ ] 302 项 `ORACLE_SEAL`：形状沿用 `_cr_seal.json:3-28`（`file_sha256/bytes/evidence_lines/evidence_span_sha256/quote/roles`）+ 新加 `adjudicator_id / labeled_at / confidence / reason_code / 带外承诺哈希`；规范化 JSON + `hashlib.sha256`。
- [ ] 带外承诺 / 签名：最低 M1（§2d），推荐 M2（`git commit -S` / minisign / sigstore）或 M3（PKI + RFC3161）。**封印与硬编码常量分域**，堵 `CERT_REAL_CHECK.md:509` 的同域双改。
- [ ] 检验端：先验封印自身哈希/签名 → 逐件读盘重算 → 行号/引文/角色 → 忽略调用方布尔 → STALE 触发重盲标（`:285`, `:536`）；`coverage` 做真 FAIL（`:393`）。
- [ ] 302 项 L3 / 元检验 + ≥30 条一次性封 SHA 的第三方盲留出（对抗 + 良性），报告 Wilson / Clopper-Pearson 区间（`:538`, `CHECK_FALSE_ALARM_AUDIT.md:265-269`）。
- [ ] (A) SOUNDNESS、(B) BOUNDED TIGHTENING 的**代码实装**：`FALSIFIABLE_NO_RELAX.md:170` 记 (B) 未实现（非注释代码 `tighten` 出现 0 次）；(D) SENSITIVITY 的元检验须在 302 项全集上跑，不得只在 5 项上。
- [ ] κ 计算脚本 + bootstrap CI + 混淆矩阵（§4d），随揭盲包公开可复算。

### 5(d) 这条工作判不了什么（如实列）

1. **判不了 `_fnr_check.py:78-91` 的 `NO_RELAXATION`**：(C) 覆盖需 302 项盲标，本会话 0 项；(A)/(B) 需 ORACLE 语义真值，本会话无。
2. **判不了任何一处的语义真值**（`CERT_REAL_CHECK.md:543`）：本会话未重读 32 主件全文逐项重判；`WHITELIST_AUDIT.md:497-498` 的 `pf2:200` /「乙设计责任人」/ 75/75 / −114.8 等沿用为未验。
3. **判不了「第三方存在 / 盲成立 / 未见」**：本会话是一个人（本子代理）在同一会话读所有只读件，**本身就不满足 T1–T8 与 B1–B3**，本件只是规范，不是标注。
4. **判不了不可否认性与抗同域双改**：无 PKI/签名；且未重跑 `CERT_REAL_CHECK.md:509` 的共址改写攻击（只读纪律 + 未生成新 seal）。
5. **判不了 κ、p_o、CI、fp/fn 总体率**：无第三方标签；编排方背景中的 `fp/fn→0/0` 自标 constructed、非随机语料、NOT a population rate（`CERT_REAL_CHECK.md:368` 亦记 5/12、0/0 为本会话独立语料）。
6. **判不了 5 条白名单机制有效性**：`_WL_WHITELIST_AUDIT.md:466`「内容恰好是对的，但机制不能证明它对」；`:486` 记「没放松」不可信。
7. **判不了 302 项验证器的实跑成本与结果**：`CERT_REAL_CHECK.md:301` 的 302 项外推自标「估计，未实跑」；本会话只实跑 5 项封印的指纹/结构核查与 302 项的**清单复算**，未跑 302 项读盘验证、未跑 `_cr_real_verify.py:main()`（`:458-460` 会回写写域既有件）、未跑 `_fnr_check.py:main()`（`:548-549` 会回写只读域）。
8. **判不了 302 项清单本身的外部完备性**：`I` 来自 `_r9s_regress_out.json` 的 32 域 `per_element`（C2），是否等于真实项目域，取决于冻结时的人工判断。
9. **判不了交付件「确由某次实跑产生」**：零真机纪律，`WHITELIST_AUDIT.md:497` 明记未验。
10. **本规范自身不构成证据**：未做标注、未封印、未做隔离、未做揭盲；所有 M1/M2/M3、κ 阈值、工作量数字中标注为「建议/估算」者均为设计值，须由 W 在 `t0` 前裁决接受。

---

## 6 纪律自查

- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；本会话脚本只做 `read_bytes` + `hashlib.sha256` + JSON 结构分析。
- 绝对只读：`lead/cert_realcheck_20261109/`、`lead/falsifiable_no_relax_20261109/`、`lead/check_fp_audit_20261109/`、`lead/whitelist_audit_20261109/`、`lead/gate_r9sem_20261109/`、`lead/keff_calc_20261109/`、`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` 全部只读；C0 对 10 件只读指纹重算并全匹配，可反证未改。
- 唯一写域 = `lead/oracle_spec_20261109/`，产物仅 `_os_ORACLE_SPEC.md` / `_os_audit.py` / `_os_audit_out.json`；**不生成新 seal**（本件所有 JSON 均为格式模板，未落盘为 seal 文件）。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
- 不 commit、不 push；未改任何既有件。
