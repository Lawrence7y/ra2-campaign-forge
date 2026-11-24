# CERT_REAL_CHECK.md — L2 自证复核、真读盘校验设计与验证、L1 修法、整体建议

> 本件是**设计件 + 验证件**，不是对 `_fnr_check.py` 的修补。唯一写域 = `lead/cert_realcheck_20261109/`；本件及所有 `_crdoc_*` 新件均落此域。零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。零采样代码：无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256(read_bytes())`。未 commit、未 push。

---

## 1 目的与边界

**目的**：①独立复核 `lead/falsifiable_no_relax_20261109/_fnr_check.py` 的 L2 `certificate_ok` 是不是自证；②设计并**实跑**一个真读盘、真重算 hash 的证书校验器；③用伪造锚点、真实白名单 5 条、5 种篡改、fp/fn 验证它；④给出 L1 `SELF_CERTIFIED` 的修法与「来源独立」判据；⑤如实登记复核 verdict、整体建议与**未验**项。

**边界（硬约束）**：

- **只做设计与验证，不改 `_fnr_check.py`、不改任何既有件**。本会话新增文件一律 `_crdoc_` 前缀（`lead/cert_realcheck_20261109/_crdoc_run.py`、`_crdoc_pasted.py`、`_crdoc_colocated.py`、对应 `_crdoc_*_out.json` 与沙箱目录）；既有 `_cr_*` / `_crv_*` 件只读不改。收尾用 `_crv_baseline.json`（复核员登记的 15 件写域既有件基线）逐件重算，实跑输出 `PREEXISTING_ALL_UNCHANGED= True`（命令见 §6 纪律段）。
- 只读域 `lead/falsifiable_no_relax_20261109/`、`lead/check_fp_audit_20261109/`、`lead/whitelist_audit_20261109/`、`lead/gate_r9sem_20261109/`、`lead/gate_fp7_20261108/`、两件台账 `lead/PENDING_DECISIONS.md` / `lead/GOAL_THREE_TARGETS_20261018.md` 一律零改动、零追加。
- 真校验实现**必须真的读盘**：任何「相信调用方声明的布尔」都不算。下文的实现用 `Path.read_bytes()` 读封印与锚点文件、`hashlib.sha256()` 重算，不采信 `cert` 里的 `oracle_truth` / `oracle_author` / `oracle_sealed` / `predicate_author` / `whitelist_sealed`。
- 所有篡改实验只作用在写域沙箱副本（`_crdoc_sandbox/`、`_crdoc_colocated_sandbox/`）与内存字典；只读域零改动。
- **未跑** `_fnr_check.py` 的 `main()`（`:553-554` 会调用 `:548` 写回只读域）与 `_cr_real_verify.py` 的 `main()`（`:458-460` 会回写写域既有件）；本会话一律 `importlib` 模块加载 + 函数级调用（替代执行），如实登记。

---

## 2 上游指纹 + L2 自证性质复核

### 2.1 八件只读件指纹（本会话独立实算）

命令（本会话实跑）：

```
python -I -X utf8 -c "import hashlib, pathlib, json; R=pathlib.Path(r'D:\Project\ra2-campaign-forge'); ... 8 件 read_bytes() + hashlib.sha256 ..."
```

输出 `ALL_EIGHT_MATCH_BASELINE = True`，8/8 `match=True`，与【编排方指纹】逐项一致：

| 文件 | sha256 | bytes |
|---|---|---|
| `lead/falsifiable_no_relax_20261109/_fnr_check.py` | `94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2` | 28811 |
| `lead/check_fp_audit_20261109/CHECK_FALSE_ALARM_AUDIT.md` | `464355c08f961a40de2a719c556816a70448a17564f63bdc05d65981f5d09ed4` | 40950 |
| `lead/check_fp_audit_20261109/_cfa_out.json` | `a47ec95a2d3baed54cc903a765eadf31ee65f9e4a9e87c5f780148c0963dc64a` | 17830 |
| `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | `f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc` | 52705 |
| `lead/gate_r9sem_20261109/_r9s_regress.py` | `16612625a7a5b11aba8b19c895a612f319bd4421c9c095b2ff8285be9214c4b4` | 11258 |
| `lead/gate_r9sem_20261109/_r9s_predicates.py` | `b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034` | 23111 |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

会话末由 `_crdoc_run.py` 复跑同一函数，输出 `ALL_EIGHT_UNCHANGED_END = True`（`lead/cert_realcheck_20261109/_crdoc_run_out.json:step7_all_unchanged`）；`git log -1 --oneline` = `2657458`（未 commit/未 push）。

### 2.2 `certificate_ok` 逐行验了什么（源码实读）

`lead/falsifiable_no_relax_20261109/_fnr_check.py:95-124`：

- `:95-97` 签名 `certificate_ok(cert, required_roles)` / docstring `L2: validate one flip's independent truth certificate` / `problems=[]`。
- `:98-101` `anchor = cert.get("anchor","")`；`if not re.search(r"^.+:\d+$", anchor)` —— **只验正则形状**，不解析 `file:line`、不查文件存在、不查行号范围。
- `:102-104` `quote = cert.get("quote","")`；`if len(quote) < 10` —— **只验长度**，不比对任何文件原文。
- `:105-114` 遍历 `required_roles`：`v = str(roles.get(r,""))`；空或 `len(v)<2` 报 `L2b`；`NON_VALUE_RE.search(v)` 挡指针词（词表定义在 `:62-67`）。**所有值来自 `cert` 字典**。
- `:115-123` **三个自声明布尔**：`"oracle_truth" not in cert` / `cert["oracle_truth"] is not True`（`:116-119`）；`cert.get("oracle_author","") == cert.get("predicate_author","")`（`:120-121`）；`not cert.get("oracle_sealed")`（`:122-123`）。全部是 `cert` 里的键，**无外部权威、无封印、无预注册**。
- `:124` `return (len(problems)==0, problems)`。
- `:161-176` `check_l2` 只把 `certificates.get(key)` 传给 `certificate_ok`；`:238` `ok = l1_ok and l2_ok and l3_ok` 把三层相关失效叠加（`CHECK_FALSE_ALARM_AUDIT.md:196` 记「真正独立层数 = 0」），不得读作「三层独立互证」。

⇒ **结论：现行 L2 只验「字典形状 + 正则 + 长度 + 词表 + 调用方自声明布尔」，是自证**。 `CHECK_FALSE_ALARM_AUDIT.md:208` 同结论；`:211` 引作者自注。

### 2.3 读盘 / 重算 hash 的调用次数与位置（本会话 AST 实跑）

命令（本会话实跑）：

```
python -I -X utf8 -c "import ast, pathlib, json; ... 对 certificate_ok / load_seal / verify_one / verify_all 做 AST Call 统计 + 全文字符串计数 ..."
```

输出（`_fnr_check.py::certificate_ok lines=95-124`）：

```
{'open': 0, 'read_bytes': 0, 'read_text': 0, 'hashlib.sha256': 0, 'is_file': 0,
 'os.path.exists': 0, 'Path': 0, 'write_text': 0, 'write_bytes': 0}
all_call_names= ['NON_VALUE_RE.search','cert.get','len','problems.append',
                 're.search','roles.get','str']
```

全文件 554 行：`open(`=0、`read_bytes(`=0、`read_text(`=2、`hashlib.sha256(`=0、`is_file(`=0、`write_text(`=1；`hashlib` / `sha256` 的 AST `Name` 计数均为 **0**。逐行定位（本会话另一条 `-c` 实跑输出）：`hashlib` 只在 `:44 import hashlib` 出现且从未被使用；`:355` 与 `:514` 的 `read_text` 都在 `main()` 里读回归/回放 JSON；`:548` 的 `write_text` 也在 `main()`。与【编排方指纹】给的 `calls` 表（`open(`0 / `read_bytes`0 / `read_text`2 / `hashlib.sha256`0 / `Path(`1）及 `CHECK_FALSE_ALARM_AUDIT.md:209` / `_crv_ast_out.json:2-38` 一致。

对照新实现（`_cr_real_verify.py`）：`load_seal` `:77-97` 有 `seal_path.read_bytes()`×1 + `hashlib.sha256(blob)`×1 + `is_file()`×1；`verify_one` `:100-237` 有 `p.read_bytes()`×1 + `hashlib.sha256(b)`×1 + `hashlib.sha256(span)`×1 + `p.is_file()`×1；`verify_all` `:240-277` 自身无 I/O，只调 `load_seal` / `verify_one`。**真读盘、真重算 hash 在这里发生**。

### 2.4 三个布尔是谁传进来的（追查到「调用方自声明」）

- 作者自注 `_fnr_check.py:309-313`：5 份 `CERTS` 是「HYPOTHETICAL inputs … deliberately constructed here by THIS session … explicitly flagged as such」；`CHECK_FALSE_ALARM_AUDIT.md:211` 亦引此句与 `_fnr_REPORT.md:427`。
- 声明行（Read 原文 + `_cr_p1_old_check_out.json:48-88` 的 provenance 扫描）：`:320-321, :327-328, :335-336, :342-343, :349-350` 硬写 `"oracle_truth": True, "oracle_author": "independent_blind_adjudicator", "predicate_author": "author_of_V1", "oracle_sealed": True`。
- 调用方改写行（同文件）：`:392` `c["oracle_truth"]=False`、`:402`、`:410`、`:425` `c["oracle_author"]="author_of_V1"`、`:495`。`certificate_ok` 只在 `:116/:118/:120/:122` 从 `cert` 读这 4 个键。
- 本会话 `_crdoc_run.py` 的 `step2` 也在内存里亲手写这 4 个字段（`_crdoc_run.py` 第 2 段「the three self-attested booleans are literally WRITTEN BY THE CALLER here」）。三目录无 `*oracle*` / `*seal*` 文件（`_cfaa_stdout.txt:74`，`CHECK_FALSE_ALARM_AUDIT.md:210`）。
- 反向实证：本会话 `_crdoc_run.py` 把 5 份证书的 5 个布尔全部伪造成「不独立」值（`oracle_truth=False, oracle_sealed=False, oracle_author=predicate_author="author_of_V1", whitelist_sealed=False`），真校验仍 `PASS 5/5`，每行 `ignored_caller_booleans` 列出这 5 键（`_crdoc_run_out.json:step3_ignored_caller_booleans`）；`_cr_edge_cases_out.json:21-62` 的 E3 同值。旧 `certificate_ok` 在这种输入上会 FAIL（它只读布尔）。

⇒ **无封印文件、无预注册、无独立权威，纯自证**。

### 2.5 伪造锚点 + 编造引文能不能过：能（本会话实跑）

命令（本会话实跑，`_crdoc_run.py` 的 `step2`；旧检验以模块方式加载，`main()` 从不调用）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_run.py"
```

输出（`_crdoc_run_out.json:step2_P1_original_checker`）：

```
{"VERDICT": "PASS", "L1_ok": true, "L2_ok": true, "L3_ok": true,
 "L1_problems": [], "L3_caught": 13,
 "anchor_files_exist": [false, false, false, false, false],
 "certificate_ok_direct": [true, []]}
```

构造：5 份证书 `anchor = "cfaa/NO_SUCH_i.md:999999"`、`quote = "本复核凭空编造的引文，未见于任何交付件。"`（抄自 `lead/check_fp_audit_20261109/_cfaa_verify.py:443-452`）。**5 个锚点文件全不存在，仍 PASS**；与 `_cr_p1_old_check_out.json:2-23`、`CHECK_FALSE_ALARM_AUDIT.md:212` 的既有实跑同值。

**额外发现（本会话独立重算）**：原 `CERTS` 的 5 条 quote **5/5 都不是其锚点行的逐字原文**。命令（本会话实跑）：

```
python -I -X utf8 -c "... 对 m.CERTS 逐条在盘上找 verbatim ..."
```

输出 `n_on_anchor_line= 0 n_anywhere= 2`：①「需谁批准」锚 `:108` 的原文含 `**` 加粗，quote 无 → 全文件 0 命中；②「实跑输出」锚 `:65`，引文实在第 69 行；③「改前改后」锚 `:76`，quote 含省略号 `…` → 0 命中；④「脚本存在性」锚 `:44`，引文实在第 71 行；⑤「可重建」锚 `:77`，quote 含 `…` → 0 命中。⇒ 旧证书连「引文在场」这一最低要求都不满足；一旦真校验会立刻 5/5 FAIL。故 §4(b) 依据 `WHITELIST_AUDIT.md:490-498` 的 5 条白名单项，重新从盘上真实行构造可逐字复核的证书（`_cr_seal.json:1-135`）。

---

## 3 真校验设计

写域既有实现：`lead/cert_realcheck_20261109/_cr_build_seal.py`（阶段①封印生成，`:88-99` 真 `read_bytes()` + `hashlib.sha256`）、`_cr_seal.json`（4395 B，sha256 `63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23`）、`_cr_real_verify.py:77-97`（`load_seal`）、`:100-237`（`verify_one`）、`:240-277`（`verify_all`）。硬编码承诺见 `_cr_real_verify.py:44-47`。本会话另把【设计】`realVerifier` 字段的可粘贴实现逐字另存为 `_crdoc_pasted.py`（只加一个测试 driver）并实跑，见 §4(b)。

### 3(a) 最少要做的清单（10 条，缺一不可）

1. **预注册封印**：每项含 `anchor` / `quote` / `roles` / `file_sha256` / `bytes` / `evidence_lines` / `evidence_span_sha256` / `oracle`；封印自身 SHA256 硬编码进校验器（`:44-47`）。
2. **真读盘**：`seal_path.is_file()` + `seal_path.read_bytes()`；每个锚点文件 `p.is_file()` + `p.read_bytes()`。`open()` / `read_text()` 不是必需，但 `read_bytes()` 必须真发生（复核员 `_crv_l1_runtime_out.json:2-18` 的 monkeypatch 计数 `n_calls=6`，把 `read_bytes` 改成 raiser 后 `raised=true, error='REVIEWER: read_bytes blocked'`）。
3. **真重算 hash**：`hashlib.sha256(blob).hexdigest()` 比对预注册 `file_sha256`，同时比 `len(blob)` 与 `bytes`；调用方声明的 `declared_file_sha256` 只拿来与重算值对照，不采信。
4. **先验封印自身**：`load_seal` 先比 `EXPECTED_SEAL_BYTES` 与 `PRE_REGISTERED_SEAL_SHA256`，否则攻击者可连封印一起重写。⚠️ **此条单独不充分**：见 §6 复核缺口 (1)，常量与封印同处写域时必须带外签名。
5. **解析 `file:line`**：`ANCHOR_RE = r"^(.+):(\d+)$"`，且 `1 <= ln <= len(lines)`（`:180-185`）。
6. **引文逐字**：`quote in lines[ln-1]`（`:188-195`）**且** `quote == seal_rec["quote"]`（`:125-127`），防同义改写 / 伪造锚点。
7. **角色值**：`NON_VALUE_RE` 非指针，且逐字在**预注册证据窗口** `lines[lo-1:hi]` 内（`:211-223`）。
8. **证据区间精确 hash**：`sha256("\n".join(lines[lo-1:hi]) + "\n")` 比对 `evidence_span_sha256`（`:200-210`），抓「字节数不变的字符替换」（本会话 R4 实证，见 §4(c)）。
9. **ORACLE 只从封印读**：`oracle.truth` / `oracle.author` / `oracle.predicate_author` 来自 `seal_rec`，调用方 5 个布尔显式忽略并列入 `ignored_caller_booleans`（`:104-106`、`:224`）。
10. **封印缺失 / 记录缺失必须 FAIL 全部**（`:252-260`），不得空列表 vacuous PASS；输出三态 `PASS | STALE | FAIL`，且 **STALE 计入 NON_PASS**（`:271-273`）。

### 3(b) 可粘贴实现（逐字另存 `_crdoc_pasted.py`，本会话实跑通过）

```python
# 可粘贴的真校验实现（完整运行版：lead/cert_realcheck_20261109/_cr_real_verify.py）
# 依赖：_cr_seal.json 由 _cr_build_seal.py 预先从只读交付件生成，其 sha256 硬编码如下。
# 关键：所有真值来自「实读的封印」，调用方布尔一律忽略；FAIL > STALE > PASS。

import hashlib, json, re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
SEAL_PATH = ROOT / "lead" / "cert_realcheck_20261109" / "_cr_seal.json"
PRE_REGISTERED_SEAL_SHA256 = "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23"
EXPECTED_SEAL_BYTES = 4395
ANCHOR_RE = re.compile(r"^(.+):(\d+)$")
CALLER_BOOLEAN_KEYS = ("oracle_truth", "oracle_author", "oracle_sealed",
                       "predicate_author", "whitelist_sealed")
# 与 _fnr_check.py:62-67 逐字一致（未改该文件）
NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$")


def load_seal(seal_path=SEAL_PATH):
    """真读封印 + 真算 hash；防止攻击者连封印一起重写。"""
    problems = []
    if not seal_path.is_file():
        return None, ["SEAL_MISSING: no seal file on disk"]
    blob = seal_path.read_bytes()                      # REAL disk read
    if len(blob) != EXPECTED_SEAL_BYTES:
        problems.append("SEAL_BYTES_MISMATCH")
    if hashlib.sha256(blob).hexdigest() != PRE_REGISTERED_SEAL_SHA256:
        problems.append("SEAL_INTEGRITY: seal sha256 != pre-registered value")
    try:
        return json.loads(blob.decode("utf-8")), problems
    except Exception as e:
        return None, problems + ["SEAL_DECODE_ERROR: %s" % e]


def verify_one(cert, rec, root=ROOT, seal_ok=True):
    """验 1 份证书：真读盘、真算 hash、比对预注册值、查行号、查引文逐字在场。"""
    problems, checks = [], {}
    checks["ignored_caller_booleans"] = [k for k in CALLER_BOOLEAN_KEYS if k in cert]

    # (1) ORACLE 只来自封印，绝不读 cert 的 oracle_* 布尔
    oracle = rec.get("oracle", {})
    if oracle.get("truth") is not True:
        problems.append("ORACLE: pre-registered truth is not True")
    if not oracle.get("author") or oracle.get("author") == oracle.get("predicate_author"):
        problems.append("ORACLE: author not independent / absent")

    # (2) 证书声明必须与预注册记录逐字相等（防伪造锚点/同义引文/角色替换）
    anchor, quote = str(cert.get("anchor", "")), str(cert.get("quote", ""))
    if anchor != rec.get("anchor"): problems.append("ANCHOR_NOT_PRE_REGISTERED")
    if quote != rec.get("quote"):   problems.append("QUOTE_NOT_PRE_REGISTERED")
    if cert.get("roles") != rec.get("roles"): problems.append("ROLES_NOT_PRE_REGISTERED")
    if len(quote) < 10: problems.append("QUOTE_TOO_SHORT")

    # (3) 用封印的锚点解析路径，真读文件、真算 hash、比对预注册值
    m = ANCHOR_RE.match(str(rec.get("anchor", "")))
    rel, ln = (m.group(1), int(m.group(2))) if m else (None, None)
    lines = []
    if rel is None:
        problems.append("ANCHOR_FORMAT")
    else:
        p = root / rel
        if not p.is_file():
            problems.append("ANCHOR_FILE_MISSING: %s" % rel)
        else:
            b = p.read_bytes()                          # REAL disk read
            disk_hash = hashlib.sha256(b).hexdigest()   # REAL hash recomputation
            checks["disk_sha256"], checks["sealed_sha256"] = disk_hash, rec.get("file_sha256")
            checks["hash_matches_seal"] = (disk_hash == rec.get("file_sha256"))
            checks["byte_count_matches_seal"] = (len(b) == rec.get("bytes"))
            # 调用方声明的 hash 不被采信，只拿来与重算值对照
            if "declared_file_sha256" in cert and cert["declared_file_sha256"] != disk_hash:
                problems.append("HASH_MISMATCH_DECLARED: caller hash != recomputed disk hash")
            lines = b.decode("utf-8").splitlines()

    # (4) 行号必须存在
    if lines and (ln is None or ln < 1 or ln > len(lines)):
        problems.append("LINE_OUT_OF_RANGE: %s / %d lines" % (ln, len(lines)))

    # (5) 引文逐字在锚点行上（且已在 (2) 与预注册引文比对）
    if lines and ln and 1 <= ln <= len(lines):
        checks["quote_verbatim_on_anchor_line"] = quote in lines[ln - 1]
        if not checks["quote_verbatim_on_anchor_line"]:
            problems.append("QUOTE_NOT_ON_ANCHOR_LINE")

    # (6) 角色值：非指针 + 逐字在预注册证据窗口 + 窗口精确 hash（抓等长替换）
    lo, hi = rec.get("evidence_lines", [1, 1])
    if lines:
        window = "\n".join(lines[max(0, lo - 1):hi])
        span_hash = hashlib.sha256((window + "\n").encode("utf-8")).hexdigest()
        if span_hash != rec.get("evidence_span_sha256"):
            problems.append("EVIDENCE_SPAN_CHANGED")
        for r, v in rec.get("roles", {}).items():
            s = str(v)
            if NON_VALUE_RE.search(s): problems.append("ROLE_POINTER: %s" % r)
            if s not in window:        problems.append("ROLE_NOT_IN_EVIDENCE: %s" % r)

    # (7) 三态：文件缺失/内容矛盾 = FAIL；仅在证据区间外的字节变动 = STALE（NON_PASS）
    if not seal_ok: problems.append("SEAL_NOT_VERIFIED")
    if problems:                                      outcome = "FAIL"
    elif checks.get("hash_matches_seal") is False or \
         checks.get("byte_count_matches_seal") is False: outcome = "STALE"
    else:                                             outcome = "PASS"
    return {"item": list(rec["item"]), "outcome": outcome,
            "problems": problems, "checks": checks}


def verify_all(certs, root=ROOT, seal_path=SEAL_PATH):
    seal, seal_problems = load_seal(seal_path)
    seal_ok = not seal_problems
    if seal is None:   # 封印缺失 -> 全部 UNVERIFIED，绝不 vacuous PASS
        rows = [{"item": list(k), "outcome": "FAIL",
                 "problems": ["SEAL_MISSING: no pre-registered record"], "checks": {}}
                for k in sorted(certs)]
    else:
        rows = [verify_one(certs.get(tuple(r["item"]), {}), r, root, seal_ok)
                for r in seal["items"]]
    np_ = sum(r["outcome"] == "PASS"  for r in rows)
    ns  = sum(r["outcome"] == "STALE" for r in rows)
    nf  = sum(r["outcome"] == "FAIL"  for r in rows)
    return {"VERDICT": "PASS" if (rows and np_ == len(rows) and ns == 0
                                   and nf == 0 and seal_ok) else "NON_PASS",
            "seal_ok": seal_ok, "seal_problems": seal_problems,
            "n_pass": np_, "n_stale": ns, "n_fail": nf, "rows": rows}
```

本会话对该片段的实跑（两条命令）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_pasted.py"
  good = {"VERDICT": "PASS", "seal_ok": true, "n_pass": 5, "n_stale": 0, "n_fail": 0}
  P1_forged = {"VERDICT": "NON_PASS", "n_pass": 0, "n_stale": 0, "n_fail": 5}

python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_run.py"
  step6_pasted_snippet = {"runs": true, "good": PASS 5/5, "P1_forged": NON_PASS n_fail=5,
                          "elapsed_ms": 8.638}
```

完整可运行版（带统计 `Stats`、沙箱试验 driver）在 `_cr_real_verify.py:61-74`、`:77-97`、`:100-237`、`:240-277`、`:299-465`；其真实 5 条结果与本片段一致（`_cr_verify_out.json:2-58`）。

### 3(c) 「文件已变」判 STALE 还是 FAIL：按改动位置分流，STALE 必须 NON_PASS

- **STALE**：文件 hash / 字节数变了，但**认证区间**（`evidence_lines`）、引文、角色值逐字不变 —— 即**认证区间内容仍逐字幸存、无确定性矛盾**（例如改动落在认证区间之外）。理由：盲标注 ORACLE 是针对旧字节作出的，标签不可搬运到新字节；但认证内容本身没有可判定矛盾。必须重新盲标 + 重封印，**不得当作证据**。实证 `_cr_edge_cases_out.json:2-11` 的 E1、`_cr_verify_out.json:191-198` 的 T6：`outcome=STALE, problems=[], hash_matches_seal=false, byte_count_matches_seal=false, quote_on_anchor_line=true, global_VERDICT=NON_PASS, n_stale=1, n_fail=0`。
- **FAIL**：任何落在认证区间内的改动（含**字节数不变**的替换）。理由：这是对预注册引文 / 角色 / 区间 hash 的确定性矛盾，不是「过期」。实证 `_cr_edge_cases_out.json:12-20` 的 E2：把 `pf2:200` 改成 `pf2:201`，`EVIDENCE_SPAN_CHANGED` → `FAIL`，且 `byte_count_matches_seal=true`。文件缺失、封印缺失、封印 hash 不符也一律 FAIL（E4 `:63-70` / E5 `:71-78` / E6 `:79-84`）。
- 分流逻辑 `_cr_real_verify.py:226-235`：`problems` 非空 → FAIL；否则 hash 或字节数不符 → STALE；否则 PASS。⚠️ 措辞校正（复核员 H1，`_crv_holes_out.json:2-10`）：把认证行**移植进一个完全不同的文件**（同行号、区间 hash 仍匹配）也得到 `STALE / NON_PASS`，故「改动落在证据之外」应理解为「**认证区间内容仍逐字幸存**」，而不是「只是文件尾部追加」；二进制上仍拦下，但文字不能说死。
- 首版实现曾把字节数不符写成硬 `problems`，导致 T6 误判 FAIL；已修正为 `:161-166` 只写 `checks`、由 `:229-235` 统一分流（`_crv_holes_out.json:95-104` 的 H10 记录了这一结构）。这是实跑发现的缺陷，如实登记。

### 3(d) 性能代价（本会话实跑实测，不是估计）

`_cr_verify_out.json:9-15` 与 `_crdoc_run_out.json:step3b_real_5.stats`：

```
n_read_bytes_calls=6, bytes_read=128579, n_sha256_calls=11,
n_lines_decoded=955, elapsed_ms=2.479（设计件）/ 3.41（本会话复跑）
```

拆解（本会话 `-c` 实跑重算）：1 次封印读（4395 B）+ 5 次锚点文件读（4 个唯一文件：`RULING_MATRIX_AB.md` 36851 B、`MATRIX_DEFECT_REACHABILITY.md` 27825 B、`N11_WORDING_FIX.md` 18966 B、`S604_SCRIPT_GAP.md` 20271 B，后者被 2 项共用所以读 2 次）= 6 次读；11 次 sha256 = 1 封印 + 5 文件 + 5 证据区间。无缓存 128,579 B；按文件缓存则 108,308 B。

302 项外推（**估计，未实跑**）：本会话 `-c` 输出 `mean= 25978.25`、`projected_302_MB= 7.482`（25,978.25 × 302 / 1048576）；若按 302 次独立读约 7.85 MB 量级、近似线性。本会话**只实跑了 5 项 / 4 文件**。零真机、纯离线磁盘读。

---

## 4 真校验有效性验证（全部本会话实跑）

主命令（一次跑完 §4(a)–§4(d) + §5 的 demo，输出 `lead/cert_realcheck_20261109/_crdoc_run_out.json`）：

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_run.py"
```

该脚本以 `importlib` 加载 `_fnr_check.py` / `_cr_real_verify.py` / `_crdoc_pasted.py`，**不调用任何既有件的 `main()`**；所有篡改只在 `_crdoc_sandbox/` 副本上做。另有 `python -I -X utf8 ".../_crdoc_colocated.py"` 复核同域双改。

### 4(a) 伪造锚点场景：真校验能否抓住 → 5/5 全抓

`_crdoc_run_out.json:step3a_P1_real_verifier`：`VERDICT=NON_PASS, n_pass=0, n_fail=5, n_stale=0`。逐项 3 条理由（与 `_cr_verify_out.json:59-126` 同值）：

```
ANCHOR_NOT_PRE_REGISTERED   （伪造 cfaa/NO_SUCH_i.md:999999 ≠ 封印锚点）
QUOTE_NOT_PRE_REGISTERED    （编造引文 ≠ 预注册引文）
QUOTE_NOT_ON_ANCHOR_LINE    （编造引文不在真实锚点行）
```

与 §2.5 旧检验 `PASS / 5 个锚点文件全不存在` 成严格对照。可粘贴片段独立实跑同值：`_crdoc_pasted.py` 输出 `P1_forged = NON_PASS, n_fail=5`；复核员 `_crv_pasted_out.json:10-16` 亦同值。

### 4(b) 真实交付件 5 条白名单项：能否通过 → 5/5 PASS

`_crdoc_run_out.json:step3b_real_5`：`VERDICT=PASS, n_items=5, n_pass=5, n_stale=0, n_fail=0, seal_ok=true`，`stats` 见 §3(d)。5 项对应 `WHITELIST_AUDIT.md:490-498` 表①–⑤（「应保留 5 / 应移除 0 / 需补证据 0」），`_cr_seal.json` 的锚点为本会话实读的真实行：

| # | 白名单项 | 封印锚点 | 逐字引文（节选） |
|---|---|---|---|
| ① | 需谁批准 | `RULING_MATRIX_AB.md:108` | `批准人一律 = **乙设计责任人**` |
| ② | 实跑输出 | `MATRIX_DEFECT_REACHABILITY.md:69` | `verdict='post_read_error' conf='none' ...` |
| ③ | 改前改后 | `N11_WORDING_FIX.md:81` | `【改前】本件按 **13 项分写**，与裁决列名一一对应` |
| ④ | 脚本存在性 | `S604_SCRIPT_GAP.md:71` | `§604 生成脚本【不存在且从未落盘】` |
| ⑤ | 可重建 | `S604_SCRIPT_GAP.md:87` | `**判定：正确算法【可唯一重建】。**` |

本会话独立重算（命令 `python -I -X utf8 -c "... 从盘上重算 4 文件 sha256 / 区间 hash / 引文 / 角色 ..."`）输出：4/4 文件 `sha_ok=True`，5/5 `quote_on_line=True, span_ok=True, roles_in_window=True`；`seal_oracle_authors=['independent_blind_adjudicator']`，`top_keys=['items','seal_version']`。

**如实限定**：`WHITELIST_AUDIT.md:516` 记人工独立 5/5 判语义在场，但**本会话未独立重判语义**。这里的 `PASS 5/5` 只证明「预注册文本在预注册字节的预注册行上逐字在场且未被篡改」，不是语义裁决；`oracle.author` 是本会话在 `_cr_build_seal.py` 里写入的字符串，不是真第三方（详见 §6）。

### 4(c) 5 种篡改逐个结果（不许用「已加强校验」概括）

全部在写域沙箱副本上做，只读域零改动。下表为 `_crdoc_run_out.json:step4_tamper` 与 `_cr_verify_out.json:127-199` 的逐条输出：

| 篡改 | 构造（源码位置） | 结果 | 触发的 problems |
|---|---|---|---|
| **T1 改一字符** | `乙设计责任人`→`乙设计责任X`（`_cr_real_verify.py:368-374`，本会话 `_crdoc_run.py` 的 `d_one_char`） | **FAIL** | `QUOTE_NOT_ON_ANCHOR_LINE`；`EVIDENCE_SPAN_CHANGED: certified lines 108-108 differ`；`ROLE_NOT_IN_EVIDENCE: 具体施事值` |
| **T2 改行号** | anchor `:108`→`:109`（`:390-393` 的 `c_lineno`） | **FAIL** | `ANCHOR_NOT_PRE_REGISTERED: '...RULING_MATRIX_AB.md:109' != '...:108'` |
| **T3 引文换同义词** | `一律 =`→`全部 =`（`:395-398` 的 `c_syn`） | **FAIL** | `QUOTE_NOT_PRE_REGISTERED: '批准人全部 = ...' != '批准人一律 = ...'`；`QUOTE_NOT_ON_ANCHOR_LINE` |
| **T4 文件替换** | 沙箱内把 RULING 换成 N11 的字节（`:376-377` 的 `d_replace`） | **FAIL** | `QUOTE_NOT_ON_ANCHOR_LINE` + `EVIDENCE_SPAN_CHANGED` + 3 个 `ROLE_NOT_IN_EVIDENCE`（具体施事值 / 批准人角色头 / 赋值算子） |
| **T5 hash 声明不符** | 调用方 `declared_file_sha256="0"*64`，盘上文件干净（`:403-406` 的 `c_hash`） | **FAIL** | `HASH_MISMATCH_DECLARED: caller's hash != recomputed disk hash`（证明不采信声明 hash，只用重算值） |

附加场景（本会话与复核员均实跑）：

- **T6 区间外追加** → **STALE / global NON_PASS**，`problems=[]`（`_cr_verify_out.json:191-198`；`_cr_edge_cases_out.json:2-11` 的 E1 同值）。
- **R4 等长字符替换** `pf2:200`→`pf2:201` → **FAIL**，`EVIDENCE_SPAN_CHANGED`，`byte_count_matches_seal=true`（`_cr_edge_cases_out.json:12-20`；本会话 `_crdoc_run_out.json:step4_tamper` 的 `R4_same_byte_count_swap` 同值）。
- **E4 改封印本身** → `NON_PASS / seal_ok=false / SEAL_INTEGRITY / n_fail=5`；**E5 删封印** → `NON_PASS / SEAL_MISSING / n_fail=5`（非 vacuous PASS）；**E6 真文件错行号** → FAIL（`_cr_edge_cases_out.json:63-84`）。
- 复核员附加：H2 调用方伪造 `anchor` → 仍解析封印里的真实路径（`resolved_path` 为真实主件）并报 `ANCHOR_NOT_PRE_REGISTERED`；H5 空 `certs` + 有效封印 → `NON_PASS / n_items=5 / n_pass=0`；H8 认证行加尾随空格 → FAIL（`_crv_holes_out.json:11-18`、`:39-45`、`:82-88`）。

⇒ **5/5 篡改全部拦下，1 个过期场景正确标 STALE 且 NON_PASS**。

### 4(d) fp / fn

设计件语料：`_cr_verify_out.json:200-292` → `n_good=5, n_bad=11, false_positives=0, false_negatives=0, fp_ids=[], fn_ids=[]`（11 个 BAD = 5 个 P1 伪造 + 6 个篡改/过期，STALE 计入「非 PASS」）。

本会话独立语料（多 1 个 R4）：`_crdoc_run_out.json:step4_fp_fn` → `n_good=5, n_bad=12, false_positives=0, false_negatives=0, fp_ids=[], fn_ids=[]`；`sensitivity_lower_95_if_zero_fn=0.779078`、`fp_upper_95_if_zero_fp=0.450720`。复核员 `_crv_real_out.json` 亦为 5/12、0/0，`_crv_holes_out.json:46-67` 的 H6 重算功效界：11/5 → `0.761596 / 0.450720`；9/2 → `0.716871 / 0.776393`（`CHECK_FALSE_ALARM_AUDIT.md:242-244` 同值）；5/8 → `0.549280 / 0.312344`；30/30 → `0.904966 / 0.095034`。

**如实限定**：这是**定向构造、非随机抽样的小语料**，不是总体 FP/FN 率。0/12 漏检只支持「敏感度 ≥ 77.9%」（设计件 0/11 → ≥76.2%），0/5 误报无力排除 45.1% 的 FP 率。未做 bootstrap / 功效曲线。

---

## 5 L1 修法

### 5(a) `SELF_CERTIFIED` 从硬 FAIL 降为 detail witness：方向对，但「只降级」不对

- **硬 FAIL 是确定性开关**：本会话 `_crdoc_run.py` 的 `step5a_L1_ideal` 实跑 `fnr.check_l1` 在**最理想条件**（302 项全登记 `coverage_ratio=1.0, n_structurally_untested=0`、`outside_whitelist=0`、数量匹配、`whitelist_sealed=True, whitelist_author="independent"`）仍 `ok=false`，唯一 problem 是 `_fnr_check.py:149-150` 的 `SELF_CERTIFIED`；`self_certified=true`。源码 `:137-138` 只算 `wl_tokens == set(predicate_spec_keys)`，`:144-147` 另查的 sealed / author 与它无关。加一个 `:486` 的「额外预留要素」padding 后 `ok=true, problems=[]`（`_crdoc_run_out.json:step5a_L1_padding`）。
- **但「过严误报」的定性已被上游复核推翻**：`CHECK_FALSE_ALARM_AUDIT.md:184-187` 与 `:291` 明记项目明文禁止同源（`WHITELIST_AUDIT.md:506`、`_WL_WHITELIST_AUDIT.md:476`），8/8 规格一致良性世界全 PASS，64 世界全因子 `same_source_5=32/32 ALARM` 而 `plus_dummy_6=0/32 ALARM`；同源世界的 ALARM 是 (E) 条规格的**正确报警**，不是误报；「50% 随机假阳性率」标 **unconfirmed**。
- **真缺陷是操作化落差**：集合相等量不到「来源独立」，且被一个无关预留键绕过（P9 `_cfav_stdout.txt:61`；`CHECK_FALSE_ALARM_AUDIT.md:187`、`:260`）。⇒ 正确做法是「降级为 witness **同时**换上真封印 / 作者 / 预注册键集校验 + padding 检测」；只降级会删掉唯一的同源信号且保留 P9 漏洞。

### 5(b) 降级后 L1 还剩什么能力

仅剩 `_fnr_check.py:140-143` 的 `outside_whitelist` 集合包含 + `flip count == whitelist size`、`:144-147` 的 `whitelist_sealed` / `whitelist_author` 两个**调用方布尔**、以及 `:151-157` 报告用的 `coverage_ratio` / `n_structurally_untested` / `self_certified`。代码自己承认（`:156-157`）：`L1 alone can only ALARM on set changes; it can never validate semantic truth`。且 coverage 是装饰：P11（`_cfaa_stdout.txt:71`）`registered_tokens=set()` 得 `ok=true, coverage=0.0, problems=[]`；P10（`_cfaa_stdout.txt:70`）逐层召回 `L1=3/9=0.3333`（`CHECK_FALSE_ALARM_AUDIT.md:202-203`）。⇒ 只剩「集合变化」报警，既不能判语义真值，也不能判来源独立（除非按 5(c) 重做）。

### 5(c) 「来源独立」的正确判据（不是集合相等）

四条并行，出处链 + 预注册封印实读为准：

1. **作者**：`whitelist_author_id != predicate_author_id`，两者取自**预注册身份登记**（硬编码常量 / 签名清单），不取调用方字符串。
2. **预注册**：白名单 / ORACLE 封印文件带**硬编码**期望 SHA256 与字节数，校验端 `read_bytes()` + `hashlib.sha256` 重算比对；封印时间早于 V1 运行，封印文件不在判据作者的写域。⚠️ 单靠「硬编码」仍会被同域双改绕过（§6 缺口 (1)），必须带外签名 / PKI。
3. **不可派生**：`SPECS` 键集与预注册精确键集一致 —— `sha256(canonical_json(sorted(keys)))` == 预注册值，且 `set(keys) == set(json.loads(pre_registered_keys_bytes))`，使 padding / 截断直接 FAIL。这只能检出键集不符，**不能证明独立**，必须与 ①②并用。
4. **盲标注**：ORACLE 每项标签由未见 V1 输出、未写 V1 的裁决者作出，全覆盖（|labels| = |I|），coverage 作为**真 FAIL** 条件而非 detail；`UNVERIFIABLE` 单列「未验」不参与 PASS（`WHITELIST_AUDIT.md:508`）。

另需给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 输入槽（现无：本会话实跑 `python -I -X utf8 -c "... m.no_relaxation_check(artifact_text='x') ..."` 输出 `P5_TypeError= no_relaxation_check() got an unexpected keyword argument 'artifact_text'`；参数表 13 个，无交付件/封印槽），并把 `baseline_VERDICT=="PASS"` 纳入 `:280` 的 `CHECKER_VALID`（`CHECK_FALSE_ALARM_AUDIT.md:250-256` 的 P3 实证空清单在 ALARM 基线上 `CHECKER_VALID=true`）。

### 5(d) 可粘贴修法片段 + 实跑结果（两段对照，如实登记复核缺口）

**① 设计件原 demo（未改 `_fnr_check.py`，内存函数）**：`lead/cert_realcheck_20261109/_cr_p1_old_check.py:153-204` 的 `check_l1_repaired(...)`。它把 `self_certified` 写进 `detail["self_certified_witness"]` 不进 `problems`；`cov < coverage_threshold` 成为真 FAIL；`p.read_bytes()` + `hashlib.sha256` 验封印、比对 `author != predicate_author`；`sha256(keys_bytes)` 与精确键集双检拦 padding。设计件实跑 `_cr_p1_old_check_out.json:124-137`：`ideal → ok=true, problems=[], coverage_ratio=1.0, self_certified_witness=true`；`padding_attack_still_passes=false`（单边 padding）。

```python
import hashlib, json
from pathlib import Path
def check_l1_repaired(items, flips, whitelist, registered_tokens,
                      predicate_spec_keys, provenance, coverage_threshold=1.0):
    problems, detail = [], {}
    wl = {tuple(x) for x in whitelist}; fk = [(f["domain"], f["token"]) for f in flips]
    untested = [i for i in items if i["token"] not in registered_tokens]
    cov = round((len(items)-len(untested))/max(len(items),1), 4)
    detail.update(coverage_ratio=cov, n_structurally_untested=len(untested),
                  self_certified_witness=({k for _,k in wl} == set(predicate_spec_keys)))
    if [k for k in fk if k not in wl]: problems.append("L1: flips outside whitelist")
    if len(fk) != len(wl): problems.append("L1: flip count != whitelist size")
    if cov < coverage_threshold: problems.append("L1: coverage below threshold")
    p = Path(provenance["seal_path"])
    if not p.is_file(): problems.append("L1: provenance seal missing")
    else:
        b = p.read_bytes()                                  # REAL disk read
        if hashlib.sha256(b).hexdigest() != provenance["seal_sha256"]:
            problems.append("L1: whitelist seal sha256 mismatch")
        if provenance["author"] == provenance["predicate_author"]:
            problems.append("L1: whitelist author == predicate author")
    kb = provenance["keys_bytes"].encode("utf-8")
    if hashlib.sha256(kb).hexdigest() != provenance["keys_sha256"]:
        problems.append("L1: spec keys not pre-registered")
    if set(predicate_spec_keys) != set(json.loads(provenance["keys_bytes"])):
        problems.append("L1: spec keys differ (padding/truncation detected)")
    return (len(problems) == 0, problems, detail)
```

**⚠️ 复核员发现、本会话独立复跑确认：这段 demo 没有实现它自己 5(c) 的 ①②③**。`_cr_p1_old_check.py:210-216` 的 `seal_hash` 是从被校验的那个文件**当场算出来**的（`:191` 与自身比较，属自证）；`author` / `keys_bytes` / `keys_sha256` 全部是调用方 `provenance` 传入的字符串。本会话 `_crdoc_run_out.json:step5b_original_demo_attacks` 实跑：

```
B2_both_sides_padding            -> ok=true,  problems=[]     （同时 pad spec_keys 与 keys_bytes+keys_sha256 即放行）
B4_tampered_seal_recomputed_hash -> ok=true,  problems=[]     （篡改封印后重算期望 hash 即放行）
```

复核员 `_crv_b2_clean_out.json:5-19` / `_crv_l1_runtime_out.json:19-34` 同值。⇒ 设计件的 `padding_attack_still_passes=false` **只在单边 padding 的窄测试下成立**；以「可粘贴修法片段」呈现会造成过高确信。**标 unconfirmed（复核 verdict=partial 的组成部分）**。

**② 本会话补的硬编码预注册版**（`_crdoc_run.py` 的 `check_l1_repaired_hard`，仍是写域内独立 demo，**未接入 `_fnr_check.py`**）：把 `HARD_SEAL_SHA256` / `HARD_SEAL_BYTES` / `HARD_KEYS_JSON` / `HARD_KEYS_SHA256` / `HARD_WHITELIST_AUTHOR` / `HARD_PREDICATE_AUTHOR` 作为模块级常量，不取调用方 `provenance`；`cov < threshold` 真 FAIL；`self_certified` 只进 `detail`。可粘贴要点：

```python
import hashlib, json
from pathlib import Path
HARD_SEAL_SHA256  = "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23"
HARD_SEAL_BYTES   = 4395
HARD_KEYS_JSON    = PRE_REGISTERED_CANONICAL_KEYS_JSON   # 由第三方身份登记带外提供
HARD_KEYS_SHA256  = PRE_REGISTERED_KEYS_SHA256
HARD_WHITELIST_AUTHOR = "independent_blind_adjudicator"  # 身份登记，不取调用方字符串
HARD_PREDICATE_AUTHOR = "author_of_V1"

def check_l1_repaired_hard(items, flips, whitelist, registered_tokens,
                           predicate_spec_keys, seal_path, coverage_threshold=1.0):
    problems, detail = [], {}
    wl = {tuple(x) for x in whitelist}
    flip_keys = [(f["domain"], f["token"]) for f in flips]
    untested = [i for i in items if i["token"] not in registered_tokens]
    cov = round((len(items)-len(untested))/max(len(items),1), 4)
    detail["coverage_ratio"] = cov
    detail["n_structurally_untested"] = len(untested)
    detail["self_certified_witness"] = ({k for _,k in wl} == set(predicate_spec_keys))  # witness only
    if [k for k in flip_keys if k not in wl]: problems.append("L1: flips outside whitelist")
    if len(flip_keys) != len(wl): problems.append("L1: flip count != whitelist size")
    if cov < coverage_threshold: problems.append("L1: coverage below threshold")       # REAL FAIL
    p = Path(seal_path)
    if not p.is_file():
        problems.append("L1: provenance seal file missing")
    else:
        b = p.read_bytes()                                     # REAL disk read
        if len(b) != HARD_SEAL_BYTES or hashlib.sha256(b).hexdigest() != HARD_SEAL_SHA256:
            problems.append("L1: whitelist seal sha256/bytes mismatch")
    if HARD_WHITELIST_AUTHOR == HARD_PREDICATE_AUTHOR:
        problems.append("L1: whitelist author == predicate author")
    if hashlib.sha256(HARD_KEYS_JSON.encode("utf-8")).hexdigest() != HARD_KEYS_SHA256:
        problems.append("L1: spec-key register broken")
    if set(predicate_spec_keys) != set(json.loads(HARD_KEYS_JSON)):
        problems.append("L1: spec keys differ (padding / truncation detected)")
    return (len(problems) == 0, problems, detail)
```

本会话实跑（`_crdoc_run_out.json:step5c_hardcoded_demo`）：

```
ideal                            -> ok=true,  problems=[], coverage_ratio=1.0,
                                    self_certified_witness=true
B2_both_sides_padding            -> ok=false, ["L1: spec keys differ (padding / truncation detected)"]
B4_tampered_seal_recomputed_hash -> ok=false, ["L1: whitelist seal sha256/bytes mismatch"]
```

⇒ 判据 ①②③ **可实现**，但硬编码常量仍与封印同处写域，需带外签名才能抗同域双改（§6 缺口 (1)）。**未改 `_fnr_check.py`**、未接入现盘检验；这是可行性验证，不是生产修法。

---

## 6 复核回件（绑定行）+ 整体建议 + 未验项

### 6.1 绑定行（固定格式，本行不插路径、括号、星号、反引号或空格）

被核对象 SHA256 = 94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2，字节数 = 28811

出处：本会话命令 `python -I -X utf8 -c "import hashlib,pathlib,json; ... 8 件 read_bytes()+hashlib.sha256 ..."` 输出 `ALL_EIGHT_MATCH_BASELINE = True`（§2.1），与【编排方指纹】`_fnr_check.py` 完全一致；会话末 `_crdoc_run.py` 输出 `ALL_EIGHT_UNCHANGED_END = True`。`CHECK_FALSE_ALARM_AUDIT.md:276` 亦载同串。

### 6.2 复核 verdict 如实登记

**【复核】verdict = `partial`；按铁律标 `unconfirmed`**（`ranCommands=23`，`sha256Line` 为 §6.1 同串）。两大怀疑点「真校验其实也没读盘」与「5 类篡改抓不住」**均被排除（refuted 亦按铁律标 unconfirmed）**：

- 复核员 `_crv_l1_runtime_out.json:2-18`：monkeypatch `pathlib.Path.read_bytes` 计数 `n_calls=6`（封印 + 4 真实主件，S604 读 2 次），`VERDICT=PASS`；把 `read_bytes` 改成 raiser → `raised=true, error='REVIEWER: read_bytes blocked'`。本会话 §2.3 AST 与 §3(b) 片段实跑同值。
- 复核员 `_crv_real_tests.py` / `_crv_holes.py` 独立复现 5/5 篡改 FAIL/STALE、fp=0 fn=0（语料 5/12），并把可粘贴 `realVerifier` 逐字另存 `_crv_pasted.py` 实跑 `good → PASS 5/5`、`P1_forged → NON_PASS n_fail=5`（`_crv_pasted_out.json:1-18`）。
- 判 `partial` 的两处**材料性但未推翻主结论**的缺口：
  1. **封印与硬编码承诺同处写域**：`_cr_seal.json` 与 `PRE_REGISTERED_SEAL_SHA256`（`_cr_real_verify.py:44-47`）都在 `lead/cert_realcheck_20261109/`。复核员 `_crv_l1_runtime_out.json:36-44` / `_crv_holes_out.json:89-94` 的 Part C / H9：同步重写封印、记录 hash 与模块内常量后，凭空编造的内容 `VERDICT=PASS, seal_ok=true, n_pass=5, n_fail=0`。本会话第一次复现时漏同步调用方证书，得到 `NON_PASS`（`_crdoc_run_out.json:step4C_co_located_rewrite`，如实登记）；补全后 `python -I -X utf8 ".../_crdoc_colocated.py"` 输出 `VERDICT=PASS, n_pass=5, n_fail=0`，`fake_seal_sha256=482b14b3de057829065d308e50a3cfea48774ceebd928d1204abee119ec7fecb`（`_crdoc_colocated_out.json`）。⇒ §3(a)①「封印自身 SHA256 硬编码进校验器」**单独不充分**，除非常量在攻击者写域之外 / 带外部签名。
  2. **§5(d)① 的 demo 未实现其自身 §5(c) 判据**：期望 hash 运行时自算、`author`/`keys_*` 由调用方给出；双边 padding 与篡改封印后重算 hash 仍 `ok=true`（本会话 §5(d) 实跑、复核员 `_crv_b2_clean_out.json` 同值）。设计件已诚实声明「L1 修法仅为写域内独立 demo，未接入 `_fnr_check.py`」，但「可粘贴修法片段」的呈现会造成过高确信。

两处缺口恰好共同支撑、而非反驳最终结论：**仍需真第三方盲标注 ORACLE（+ 带外封印 / 签名 + 全 302 项覆盖 + 双基线），否则只是「自证换了套可复核的管道」**。

### 6.3 整体建议：(a) 最小改法清单核对

三条取自 `lead/check_fp_audit_20261109/_CFA_REPORT.md:243-245`（`:249` 记「最小闭环 = 前 3 条」；`CHECK_FALSE_ALARM_AUDIT.md:293` 另列 6 条并自标「未实装未实跑，标未验」；`:330` 记「仓库其余位置未穷举」，`:332` 记「改动方案未实装、未实跑」）：

| 条 | 内容 | 核对结论 |
|---|---|---|
| ① | `SELF_CERTIFIED` 降为 witness | **不充分，且单独看不对**。见 §5(a)：原审计 `CHECK_FALSE_ALARM_AUDIT.md:186-187/:291` 已把「过严误报」定性推翻，硬 FAIL 在同源世界是 (E) 条正确报警；只降级会删信号、留 P9 padding 洞。应改为「降级 + 真封印 / 作者 / 精确键集 + coverage 真 FAIL」（§5(c)(d)②）。 |
| ② | 独立性改为对真实 sha256 封印文件 `open` + 重算 + 作者校验 | **方向对且是核心**，本会话已实装并实跑验证（§3(b)、§4）。仍缺 5 件：`no_relaxation_check` 无交付件 / 封印输入槽（P5 TypeError，§5(c) 实跑）；须先验**封印自身** hash 且常量带外（§6.2 缺口 1）；须查行号存在 + 引文 / 角色逐字在场；须定义 STALE 且 NON_PASS；**ORACLE 必须是真第三方盲标**（`_cr_seal.json` 的 `oracle.author` 是本会话写的字符串，不是真第三方）。 |
| ③ | `CHECKER_VALID` 加 `baseline=="PASS"` + `n_wrong≥5`、`n_good≥8` | **必要但规模不足**。本会话与复核员实算 5/8 → `0.549280 / 0.312344`（`_crv_holes_out.json:55-58`），仍无力排除 31.2% FP；`CHECK_FALSE_ALARM_AUDIT.md:242-244` 的 9/2 → `0.716871 / 0.776393`。且 good 世界必须含「交付件原文级」错误类并由第三方一次性封 SHA 盲留出（`_CFA_REPORT.md:263-270`、`CHECK_FALSE_ALARM_AUDIT.md:265-267`）。 |

**三条之外仍缺**（`CHECK_FALSE_ALARM_AUDIT.md:218-220`、`:231`、`:293`；`WHITELIST_AUDIT.md:507-509`）：L3 的 13/13 逐字拟合作者 guard 词表、novel empties 只抓 14/16 漏 `N-EMPTY-1/2`；`coverage` 装饰化 P11；`:149` multiset→set 措辞；`:238` 把三个相关失效 `and` 起来被误读成「三层独立互证」（`:196` 实测独立层数=0）；按 `WHITELIST_AUDIT.md:507` 拆成 `whitelist_integrity / flip_semantics / adversarial_robustness` 三个独立布尔；302 项 ORACLE 真值表。

### 6.4 (b) 修好之后能不能真的判「没放松」→ 不能无条件判，只能有条件判一个更窄的命题

按 `_fnr_check.py:73-91` 的操作化定义，`NO_RELAXATION` 依赖 `ORACLE: I→{0,1}` 这个**在 V1 之前由独立裁决者产出、未见 V1 输出、未写 V1、带 published SHA256 seal、覆盖全部 I**（`:81` `|{ORACLE defined}|=|I|`）的语义真值。本会话实读 `_cr_seal.json:17-21` 等 5 处：`oracle` 只有 `truth/author/predicate_author`，`author` 是同一会话写入的纯字符串 `independent_blind_adjudicator`（`_cr_build_seal.py:30-31` 等 5 处硬编码 `truth:True`），顶层只有 `items` / `seal_version`，**无签名字段、无 302 项标签、无外部权威**（本会话 `-c` 输出 `seal_oracle_authors=['independent_blind_adjudicator']`, `top_keys=['items','seal_version']`；复核员 `_crv_l1_runtime_out.json:45-60`、H7 `_crv_holes_out.json:68-81` 同值）。

真校验能判的是：「预注册封印所指的字节、行、引文、角色值逐字在场且未被篡改」——这是**必要条件**，**不是** `ORACLE(i)=1` 的语义判断。三层又是相关失效叠加，不得当独立互证。⇒ 只有在「真第三方盲标 ORACLE + 带外预注册封印/签名 + 检验端实读重算 + 全 302 项覆盖 + 双基线」齐备时，才能在**该有限项目域**上判定操作化意义下的「没放松」；否则即使哈希管线全对，仍是「自证换了套更好的管道」。§6.2 的同域双改实证正是这一判断的经验支撑。

### 6.5 (c) 缺的那一环 = 真第三方盲标注 ORACLE，方案（六步）

1. V1 编写 / 运行**之前**，由未写 V1、看不到 V1 输出的裁决者，仅凭原始交付件，对 302 项逐项逐角色产出 `{0,1,UNVERIFIABLE}` + `file:line` + 逐字引文；`UNVERIFIABLE` 单列「未验」不参与 PASS（`WHITELIST_AUDIT.md:508`）。判据作者不得写白名单（`WHITELIST_AUDIT.md:506`、`_WL_WHITELIST_AUDIT.md:476`）。
2. 规范化 JSON（`sort_keys`）→ SHA256 → 64-hex **带外**硬编码 / 第三方签名进校验器；封印同时含每个交付件的 `sha256/bytes/evidence_span_sha256`（即 `_cr_seal.json` 的形状）与作者 / 时间；封印文件放在判据作者写域之外，堵 §6.2 缺口 1。
3. 校验端先验封印自身 hash / 签名，再逐件读盘重算，查行号 / 引文 / 角色；ORACLE 只读封印、忽略调用方布尔；STALE 触发重盲标 + 重封印，绝不自动 PASS。
4. 把 `WHITELIST_AUDIT.md:467/:498/:516` 的人工独立 5/5 接入 ORACLE 槽（现因 P5 无槽接不进），并扩到 302 项。
5. ≥30 条一次性封 SHA 的第三方盲留出（对抗 + 良性）作 L3 / 元检验，`n_wrong≥30, n_good≥30` → `0.904966/0.095034`；阈值跑前注册，报告 Wilson / Clopper-Pearson 区间（`CHECK_FALSE_ALARM_AUDIT.md:265-269`、`_CFA_REPORT.md:263-270`）。
6. `CHECKER_VALID` 纳入 `baseline_VERDICT=="PASS"` 与双基线，强制公开「本检验在以下情形不报警」清单（`CHECK_FALSE_ALARM_AUDIT.md:268`、`:250-256` 的 P3）。

### 6.6 (d) 这条工作判不了什么（**未验**项，如实列）

1. **语义真值**：302 项 ORACLE 真值、5 主件语义裁决未独立重判；本会话 `PASS 5/5` 只证明文本逐字在场，不证明「语义内容确已交付」（沿用 `WHITELIST_AUDIT.md:498/:516`，未重读 4 主件全文逐项重判）。
2. **真第三方 ORACLE 是否存在**：三目录无 `*oracle*` / `*seal*`（`_cfaa_stdout.txt:74`），全库未穷举（`CHECK_FALSE_ALARM_AUDIT.md:330` / `_CFA_REPORT.md:255`）。**本会话 `_cr_seal.json` 的 ORACLE 是本会话自造，不构成真第三方盲标注**；无 PKI / 签名 / 不可否认性，且「同源」本身无形式化判据，只能靠流程约束。
3. **总体 FP/FN 率**：定向构造 5/12 语料，0 FN 仅支持敏感度 ≥77.9%（设计件 0/11 → ≥76.2%），0 FP 无力排除 45.1%；非随机抽样、无 bootstrap / 功效曲线。
4. **零真机下的一切运行时行为**：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存，未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
5. **改动后检验本体的结果**：未跑 `_fnr_check.py` 的 `main()`（`:548-549` 会回写只读域）、`_cr_real_verify.py` 的 `main()`（`:458-460` 会回写写域既有件）与 `_r9s_regress.py` 本体；一律 `importlib` 模块加载 + 函数级调用（替代执行）。§5(d) 的 L1 修法仅为写域内独立 demo，**未接入 `_fnr_check.py`**（部分片段还被复核标 unconfirmed）。
6. **302 项 / R9 升级整体安全性**：302 项外推（≈7.48–7.85 MB、~302 次读）是估计未实跑；未验证现盘 R9 升级、未复跑 24/24 负样本、未验证跨项目推广。
7. **STALE 语义边界**：复核员 H1 证明「把认证行移植进一个完全不同的文件（同行号、区间 hash 仍匹配）」也判 STALE（NON_PASS）；「改动落在证据之外」的措辞已在 §3(c) 校正为「认证区间内容仍逐字幸存」，但**未穷举**所有可能的字节变动形态。
8. **改法通用性**：`CHECK_FALSE_ALARM_AUDIT.md:293` 自标「未实装未实跑，标未验」，`:332` 列「改动方案未实装、未实跑」为未验项；本会话只实装并实跑了「L2 真校验」在 5 项 / 4 文件上的可行性。

### 6.7 纪律复核（命令 + 输出）

```
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_run.py"
  ALL_EIGHT_MATCH_BASELINE_START = True
  ALL_EIGHT_UNCHANGED_END = True

python -I -X utf8 -c "... 对 _crv_baseline.json 的 15 件写域既有件重算 sha256/bytes ..."
  PREEXISTING_ALL_UNCHANGED= True

git log -1 --oneline
  2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账
```

- 只读域 5 个目录 + 两件台账零改动 / 零追加；`_fnr_check.py` 指纹收尾仍 `94d898...00c2 / 28811`。
- 本会话新件仅 7 项，全部 `_crdoc_` 前缀、全部在 `lead/cert_realcheck_20261109/`：`_crdoc_run.py`、`_crdoc_run_out.json`、`_crdoc_pasted.py`、`_crdoc_colocated.py`、`_crdoc_colocated_out.json`、`_crdoc_sandbox/`、`_crdoc_colocated_sandbox/`。既有 `_cr_*` / `_crv_*` 件一律未改（15 件基线逐件 `status: OK`）。
- 所有篡改只作用在沙箱副本与内存字典；未 commit / 未 push；零真机、零采样代码。复核 verdict=`partial` 与两处缺口按铁律标 **unconfirmed**，未以「已加强校验」概括，逐种篡改结果见 §4(c)。
