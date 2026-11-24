# MERGED 最小安全集补丁设计（只出设计，不落地）

> 全部结论以本会话实跑命令输出或 `文件:行` 为依据。命令一律 `python -I -X utf8 -B` + 绝对路径；指纹一律 `hashlib.sha256`。本次交付新建本文件及 `_final_*_stdout.txt` 输出件于写域 `lead/merged_safety_20261109/`；复跑现成探针另按脚本自身行为刷新了写域内既有 `_ms_probe_out.txt`、`_ms_counterexample_deliverable.md` / `_ms_counterexample_out.txt`、`_ms_regress_out.txt`、`_ms_tight_out.txt` 等同名输出件（内容未改，见 §6.3）。

## 1 目的与边界

**目的**：对 `_re_linked.py` 的 `merged rec` 进入消费面后暴露的两处实证缺陷，给出「改前片段 / 改后片段」逐字对照、三形态行为表、反例、最小安全集边界与接入前置条件；由模板所有者决定是否落地。

**边界（本会话遵守）**：

- 只出补丁设计，**不落地**。未改 `_f2v_verify9.py`、未改 `_g9_gate.py`、未改任何既有件与两件台账；改后整件仅作为写域候选副本 `_ms_v9_candidate.py` / `_ms_v9_candidate_v2.py` / `_ms_g9_candidate.py` 存在。
- `_g9_gate.check_deliverable` 返回值结构不许变：函数入口 `_g9_gate.py:70`，返回 `result` 在 `_g9_gate.py:203`，结构定义 `_g9_gate.py:181-187`。补丁 2 只改 `r11_problems` 的内容与由其推出的 `verdict` 值，不动任何键。
- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。不 commit、不 push。
- 两处缺陷均属**未来接入面**，当下不崩、不放行：本会话实跑 `grep -n "r11_scan_plus\|link_triple\|_re_linked" lead/gate_r9r12_20261109/_g9_gate.py` → `GREP_EXIT=1 NO_MATCH`；接入点 `_f2_r11plus.py:303-305` 实读仍为 `rec["tier"]=None` + R3-3b warning；`_g9_gate.py:155` 实读为 `g7.r11_scan(...)`（原版谓词，不产 merged rec）；审计亦在 `MERGED_CONSUMER_AUDIT.md:133,141-144` 撤下「门禁静默放过」并记 severity=medium。severity 取 medium；若实施接入而未先补齐 §5 的前置条件，按 `MERGED_CONSUMER_AUDIT.md:144` 升 high。
- 复核回件 verdict = **partial → unconfirmed**。四项硬门槛通过（② 键集相同、④ 无键增删、⑤ 反例跑得出、⑧ 无越界），但 ⑥ 的「单点覆盖 6 件」被逐件实读证伪、⑦ 一个子例与 DESIGN 记载不符、尺寸登记不符，详见 §6。

## 2 上游指纹（八件）+ 两处缺陷的独立复现

### 2.1 八件指纹（本会话 hashlib 实算）

命令（本会话实跑）：

```
cd "D:/Project/ra2-campaign-forge" && python -I -X utf8 -B -c "
import hashlib
files = ['lead/r11_f2_fix_20261109/_f2v_verify9.py','lead/gate_r9r12_20261109/_g9_gate.py','lead/gate_fp7_20261108/_g7_predicates.py','lead/r33e_merge_20261109/_re_linked.py','lead/merged_consumer_audit_20261109/_mc_AUDIT.md','lead/merged_consumer_audit_20261109/MERGED_CONSUMER_AUDIT.md','lead/PENDING_DECISIONS.md','lead/GOAL_THREE_TARGETS_20261018.md']
base='D:/Project/ra2-campaign-forge/'
for f in files:
    b=open(base+f,'rb').read()
    print(f); print('  sha256 =',hashlib.sha256(b).hexdigest()); print('  bytes  =',len(b))
"
```

输出逐字（与编排方【编排方指纹】8 件全等）：

```
lead/r11_f2_fix_20261109/_f2v_verify9.py
  sha256 = c22f28ad4228d028c16d8558a8dd9a0980947631ab5bcf5c9cd84e529cf439e3
  bytes  = 1618
lead/gate_r9r12_20261109/_g9_gate.py
  sha256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6
  bytes  = 11623
lead/gate_fp7_20261108/_g7_predicates.py
  sha256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120
  bytes  = 11743
lead/r33e_merge_20261109/_re_linked.py
  sha256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52
  bytes  = 19481
lead/merged_consumer_audit_20261109/_mc_AUDIT.md
  sha256 = 8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367
  bytes  = 33762
lead/merged_consumer_audit_20261109/MERGED_CONSUMER_AUDIT.md
  sha256 = 85de273758a6b87915f9735a07e1b9e1d11c594de50f41d83f5e70145257c263
  bytes  = 40884
lead/PENDING_DECISIONS.md
  sha256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7
  bytes  = 52419
lead/GOAL_THREE_TARGETS_20261018.md
  sha256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede
  bytes  = 759518
```

### 2.2 merged rec / 缺三键 / 崩点 / 静默放行条件的独立复现

本会话实跑（EXIT=0，输出落 `_final_probe_stdout.txt`，100 行）：

```
python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_ms_probe.py" > "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_final_probe_stdout.txt" 2>&1
```

关键输出逐字：

```
A1 merged rec KEYS = ['decl_lines', 'declared', 'match', 'members', 'path', 'samedoc_link', 'tier']
A3 MISSING KEY verified_path    : True
A3 MISSING KEY recomputed       : True
A3 MISSING KEY bytes            : True
A4 path = None ; match = True ; tier = 'SAMEDOC_LINK_EQ' ; members_n = 2
A6 samedoc_link.reverify = None
B2 :24 Path(src.get('verified_path') or src.get('path')) → TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'
B2 :29 size == src['bytes'] (src['bytes'] 求值)           → KeyError: 'bytes'
B2 :34 src['bytes'] (print 参数求值)                      → KeyError: 'bytes'
B4 绕过 :24 后 :29 → KeyError: 'bytes'
D1 r11_scan 是否产 merged rec = False （r11_scan 不调 link 家族；:155 实读为 g7.r11_scan）
D4 :157-160 假设注入真 merged rec 时 旧 = {"n_bindings": 1, "items": 2, "reverified": 0, "match_true": 1, "n_unverified": 1, "problems": [], "verdict": "PASS"}
F9 ALL_EIGHT_MATCH = True
```

即：**merged rec** 键集恰为 7 键、`match=True`、`path=None`、`members_n=2`，且**缺三键** `verified_path/recomputed/bytes`；`samedoc_link.reverify=None`。形状的代码依据：`_re_linked.py:310-313` 造骨架 `path=None`，`:320-329` 的 merged 分支只写 `tier/match/members/decl_lines`，`:314-319` 的 unique 分支才写 `verified_path/recomputed/bytes`；`:306-308` 明示 `match=True` 仅指「声明 hex 与全体成员现盘重算逐位一致」、不指向单一对象；`:47` 明示 problems 恒空。

缺陷 1（`_f2v_verify9.py`）：`:23 src = b.get("alt") or b`、`:24 vp = Path(src.get("verified_path") or src.get("path"))`、`:29 ok_bytes = size == src["bytes"]`、`:34 src["bytes"]` 全按单对象 rec 取键。merged 注入时 :24 `Path(None)` → `TypeError`；绕过 :24 后 :29/:34 仍 `KeyError: 'bytes'`（B4 实证）。

缺陷 2（`_g9_gate.py`）：`:157 n_reverified = sum(1 for b in bindings if b.get("path"))`、`:158 n_match = sum(...)` 只统计、不判定；`:160 r11_verdict = "FAIL" if r11_problems else "PASS"`。merged 的 `problems=[]`（`_re_linked.py:47`）且 `match=True/path=None` ⇒ `reverified=0`、`match_true=1`、verdict=PASS。这就是「**reverified=0 就算过**」的静默放行条件；审计 `MERGED_CONSUMER_AUDIT.md:133` 亦把它明列为「将来改接 plus 时」的真实误读（当下不可达）。

## 3 `_f2v_verify9.py` 最小补丁（改前改后逐字对照）

### 3.1 改前片段（逐字，`_f2v_verify9.py:19-36`，共 18 行；其中 `:19-35` 的 17 行是 `_ms_probe.py` 的 `BEFORE_V9` 替换常量，`:36` 为循环体内未改动的尾行，为便于对照一并列出）

```python
    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        src = b.get("alt") or b
        vp = Path(src.get("verified_path") or src.get("path"))
        data = vp.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        ok_sha = sha == b["declared"].lower()
        ok_bytes = size == src["bytes"]
        n += 1
        print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
        print("   declared=%s" % b["declared"])
        print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
        print("   bytes declared=%s mine=%d bytes_ok=%s" % (src["bytes"], size, ok_bytes))
        if not (ok_sha and ok_bytes):
            print("   *** MISMATCH ***")
```

`_ms_probe.py` C0 实跑：`C0 BEFORE_V9 逐字包含在原件中 = True (count=1)`。

### 3.2 改后片段（逐字，候选副本 `_ms_v9_candidate.py:19-58`，共 40 行；替换上列 :19-35 的 17 行，:36 尾行逐字保留）

```python
    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        # --- merged：副本群，按 members 逐成员核对；不主张单一 path；缺键一律 .get ---
        if b.get("tier") == "SAMEDOC_LINK_EQ" or b.get("members"):
            for m in (b.get("members") or []):
                mp = m.get("path")
                data = Path(mp).read_bytes() if mp else b""
                sha = hashlib.sha256(data).hexdigest()
                size = len(data)
                ok_sha = sha == (b.get("declared") or "").lower()
                ok_bytes = size == m.get("bytes")
                n += 1
                print("MATCH#%d #%d bind#%d tier=%s member=%s" % (n, i, k + 1, b.get("tier"), mp))
                print("   declared=%s" % (b.get("declared") or ""))
                print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
                print("   bytes declared=%s mine=%d bytes_ok=%s" % (m.get("bytes"), size, ok_bytes))
                if not (ok_sha and ok_bytes):
                    print("   *** MISMATCH ***")
            continue
        if not (b.get("alt") or b).get("path"):
            # --- multi：无单一 path 且无 members → 确定行为 = 记 SKIP，不读任何单对象键 ---
            n += 1
            print("SKIP#%d #%d bind#%d tier=%s 无单一回验路径且无 members（multi：不主张 path）" % (n, i, k + 1, b.get("tier")))
            continue
        src = b.get("alt") or b
        vp = Path(src.get("verified_path") or src.get("path"))
        data = vp.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        ok_sha = sha == (b.get("declared") or "").lower()
        ok_bytes = size == src.get("bytes")
        n += 1
        print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
        print("   declared=%s" % (b.get("declared") or ""))
        print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
        print("   bytes declared=%s mine=%d bytes_ok=%s" % (src.get("bytes"), size, ok_bytes))
        if not (ok_sha and ok_bytes):
            print("   *** MISMATCH ***")
```

### 3.3 改动行数（本会话 difflib 实算）

命令：`python -I -X utf8 -B -c "import ast,difflib; ... SequenceMatcher(...)"`（绝对路径读入原件与候选副本）。输出：

```
v9 unchanged= 33 removed= 4 added= 26 opcodes= [('insert', 22, 22, 22, 44), ('replace', 27, 29, 49, 51), ('replace', 31, 32, 53, 54), ('replace', 33, 34, 55, 56)]
v9 compile=OK lines= 59
```

整件口径：**unchanged=33 / removed=4 / added=26**，只做一次字符串替换（一次 insert + 3 处把 `b["declared"]`/`src["bytes"]` 改 `.get`）。本会话另用探针同口径实算两种片段范围：① 探针 `_ms_probe.py` 的 `BEFORE_V9` 替换常量（`:19-35`，17 行）对 `AFTER_V9`（39 行，`autojunk=False`）= `unchanged=13 removed=4 added=26`，即编排方回件所记口径；② 本件 §3.1/§3.2 为便于对照多列了未改动的尾行 `:36`（18 行 → 40 行），实算 `unchanged=14 removed=4 added=26`。另：本会话早先误用「原地文件 :19-36（18 行）」对「候选副本 :19-58（40 行）」交叉比对（两段的起点/终点不对应），曾得 `unchanged=12 removed=5 added=26`，该数字口径不成立、已作废。三种口径均如实登记，不互相冒充；有效结论均为「只新增 22 行、替换 4 行」；本会话另实读验证 `_ms_probe.py` 的 `v9patched = v9src.replace(BEFORE_V9, AFTER_V9)` 与候选副本 `_ms_v9_candidate.py` 全文逐字相等（`PATCHED_EQUALS_CANDIDATE True`、`C0_count 1`），证明改后片段确由改前片段替换而来。另验过 v2 紧版 `_ms_v9_candidate_v2.py`：compile / 30 件均 OK，但整件 `unchanged=4 removed=14 added=25`（`_ms_tight_stdout.txt`），更不最小，故不选 v1 之外的方案。

### 3.4 三形态预期行为表（本会话 `_ms_probe.py` C3、`_ms_tight.py` T4 实跑）

| 形态 | 输入 | 改前 | 改后（实测） | 是否掉 TypeError/KeyError |
|---|---|---|---|---|
| **unique**（有 `path`，真 `link_triple` unique rec） | `_re_linked.py:314-319` 带 `verified_path/recomputed/bytes` | OK `MATCH#1 sha_ok=True bytes_ok=True` | 走保留的 unique 分支：`MATCH#1 … sha_ok=True bytes_ok=True`（C3 改后列 `OK n=1`） | 否 |
| **merged**（`match=True`、`path=None`、`members_n=2`） | `_re_linked.py:320-329` | `:24 TypeError: ... not 'NoneType'` | 逐成员 `MATCH#1/#2 … sha_ok=True bytes_ok=True`（C3 改后列 `OK n=2`） | 否 |
| **multi**（无 `path` 无 `members`） | 真 multi rec `match=None` + 合成 `match=True, path=None, members` 缺 | 真 rec 跳过；合成版 `:24 TypeError` | 真 rec 跳过（`OK n=0`）；合成版 `SKIP#1 … 无单一回验路径且无 members`（`OK n=1`） | 否 |

缺键注射（C3 后 4 行，改后全 `OK`）：`merged 缺 member.bytes` → `bytes_ok=False`；`merged members=None` → `OK n=0`（**注意**：输出 0 行，不是 SKIP；见 §6 复核 ⑦）；`unique 缺 bytes` → `bytes_ok=False`；`merged 缺 declared` → 确定性 `MISMATCH`。`_ms_tight.py` T4 另复验 8 例（含 mixed unique+merged+multi）全 `OK`、零 `TypeError` / 零 `KeyError`。

真实 30 件回归（C2）：`C2 改后整件跑真实 30 件 = OK，末行 = 'checked 9'，MISMATCH 行数 = 0，MATCH 行 = 9`。

## 4 `_g9_gate.py` 最小补丁（改前改后 + 返回值结构不变 + 反例）

### 4.1 改前片段（逐字，`_g9_gate.py:155-167`，共 13 行）

```python
    r11_problems, r11_warnings, bindings = g7.r11_scan(text, d_dir, root=root)
    bindings = [dict(b) for b in bindings]
    n_reverified = sum(1 for b in bindings if b.get("path"))
    n_match = sum(1 for b in bindings if b.get("match") is True)
    r11_items = 1 + len(bindings)  # 存在性强制项 1 + 每条绑定行回验
    r11_verdict = "FAIL" if r11_problems else "PASS"
    predicates["R11"] = {
        "rule_id": "R11", "name": "绑定行路径隔断容忍 + 引用锚回验（第 8 类）",
        "items": r11_items, "bindings": len(bindings), "reverified": n_reverified,
        "match_true": n_match,
        "problems": list(r11_problems), "warnings": list(r11_warnings),
        "binding_details": bindings, "verdict": r11_verdict,
    }
```

### 4.2 改后片段（逐字，候选副本 `_ms_g9_candidate.py:155-171`，共 17 行）

```python
    r11_problems, r11_warnings, bindings = g7.r11_scan(text, d_dir, root=root)
    bindings = [dict(b) for b in bindings]
    n_reverified = sum(1 for b in bindings if b.get("path"))
    n_match = sum(1 for b in bindings if b.get("match") is True)
    r11_items = 1 + len(bindings)  # 存在性强制项 1 + 每条绑定行回验
    n_match_no_path = sum(1 for b in bindings
                          if b.get("match") is True and not b.get("path"))
    if n_match_no_path:
        r11_problems = list(r11_problems) + ["R11 回验缺口：%d 条绑定行 match=True 但无单一回验路径（merged 副本群不得默认放行），须人工锚定" % n_match_no_path]
    r11_verdict = "FAIL" if r11_problems else "PASS"
    predicates["R11"] = {
        "rule_id": "R11", "name": "绑定行路径隔断容忍 + 引用锚回验（第 8 类）",
        "items": r11_items, "bindings": len(bindings), "reverified": n_reverified,
        "match_true": n_match,
        "problems": list(r11_problems), "warnings": list(r11_warnings),
        "binding_details": bindings, "verdict": r11_verdict,
    }
```

改动行数（本会话 difflib 实算）：`g9 unchanged= 238 removed= 0 added= 4 opcodes= [('insert', 159, 159, 159, 163)]`；`g9 compile=OK lines= 242`；片段口径 `unchanged=13 removed=0 added=4`。**只新增 4 行，其余 13 行逐字不动**。

### 4.3 返回值结构不变论证

- `check_deliverable` 入口 `_g9_gate.py:70`，返回 `result` 在 `:203`，结构定义 `:181-187`（10 个顶层键）。补丁只新增局部变量 `n_match_no_path` 并把 `r11_problems` 换成同类型 `list`；`predicates["R11"]` 的 10 个键（`:161-167`）一个不加不减；`:169-176` 合并视图自动带 `rule_id`，元素键仍为既有 `["msg","rule_id"]`；`:178-179` overall 逻辑不动。`problems` 列表长度 0→1 属**值变化，非键增删**。
- 本会话实跑 `_ms_probe.py`：`D6.3 返回结构 top keys 相同 = True ['bytes','checklist','file','old_gate','predicates','problems','sha256','utf8_strict','verdict','warnings']`；`D6.4 返回结构 R11 keys 相同 = True ['binding_details','bindings','items','match_true','name','problems','reverified','rule_id','verdict','warnings']`；`D6.8 改后 self_test() all_pass=True`。
- 本会话实跑 `_ms_regress.py`（输出 `_final__ms_regress_stdout.txt`，EXIT=0）：`R2 top-level keys 全部相同 = True`、`R3 R11 keys 全部相同 = True`、`R4 verdict 改变件数 = 0 / 30`、`R6 self_test old all_pass=True new all_pass=True`。复核方独立用纯键集签名比对 OLD/候选/自造三模块亦得 30/30 键集全同、30/30 verdict 零漂移（【复核】④）。
- 为何不用宽条件 `len(bindings)-n_reverified>0`：`_ms_regress.py` 首次用宽条件实跑为 `6/30 PASS→FAIL`（把既有 R3-3b 无路径件一并翻 FAIL，属策略改变），收窄为 `match=True and not path` 后 0/30；对比已留档。

### 4.4 「reverified=0 就算过」为何错

`:157` 的 `reverified` 只是**计数**，`:160` 判定只看 `r11_problems`。merged rec 的 `match=True` 含义被 `_re_linked.py:306-308` 限定为「全体成员逐位一致」，**不是单一对象回验**；`_re_linked.py:47` 又规定任何分支都不产 problem。于是 `reverified=0 / match_true=1 / problems=[]` 同时成立时，旧链给出 PASS——把「零单一对象锚定的副本群」当作已回验放行，是 fail-open（静默误读）。`:159` 注释写「存在性强制项 1 + 每条绑定行回验」，但 `:17` 所声明的「R11 每条绑定行回验一项」在这条路径上并未真正执行。补丁新增的 4 行把这一缺口显式变成 problem，交人工锚定。

### 4.5 可实跑的旧 PASS / 新 FAIL 反例

命令（本会话实跑，EXIT=0，输出 `_final__ms_counterexample_stdout.txt`）：

```
python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_ms_counterexample.py" > "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_final__ms_counterexample_stdout.txt" 2>&1
```

关键输出逐字：

```
STEP1 link_triple: tier=SAMEDOC_LINK_EQ match=True path=None members_n=2 problems=[]
STEP2 OLD+ check_deliverable: verdict=PASS R11=PASS reverified=0 match_true=1 problems=[]
STEP2 NEW+ check_deliverable: verdict=FAIL R11=FAIL reverified=0 match_true=1 problems=['R11 回验缺口：1 条绑定行 match=True 但无单一回验路径（merged 副本群不得默认放行），须人工锚定']
      返回结构 top keys 相同 = True
      返回结构 R11 keys 相同 = True
COUNTEREXAMPLE_OK
```

同一脚本不注入时 `OLD`/`NEW` 均 PASS（`STEP2 OLD … verdict=PASS R11=PASS reverified=0 match_true=0`、`STEP2 NEW … verdict=PASS`），脚本 `:9` 明写原因：当下 `:155` 用 `g7.r11_scan` 不产 merged rec，要复现「merged 匹配被放行」须按「将来门禁改接 plus」注入 rec，与 `MERGED_CONSUMER_AUDIT.md:133/165` 一致。`_ms_probe.py` D6.6/D6.7 亦给同结论：`OLD R11=PASS verdict=PASS reverified=0 match_true=1 problems=[]` / `NEW R11=FAIL verdict=FAIL reverified=0 match_true=1 problems=[…]`。旧PASS新FAIL 反例成立，但**不得冒充当下生产事故**。

## 5 最小安全集边界

### 5.1 判据：崩溃 vs 静默误读谁更该进

按「**不修则安全判定不可信**」定义安全集（本设计采用，与「门禁职责是回验」一致）：

- 崩 = fail-closed：接入后审计 §5.2 第 3 步「下游消费者全量回放」立刻 `TypeError`/`KeyError`（`_f2v_verify9.py:24/29`），联调无法完成，人必须来修，错误结论发不出去。
- 静默误读 = fail-open：程序全绿、报告照出、门禁 PASS，却把无单一回验路径的副本群记成已回验/被判通过，错误结论会进台账/裁决。

故**静默错比崩更该进安全集**；只有按「不修则程序退出」定义时才只有崩进。依据：`_ms_DESIGN.md:400-408`、`_ms_tight_stdout.txt` V1/V2/V3 实跑。

### 5.2 只修两处的错误传导链（本会话 `_ms_tight.py` U1-U6 实跑，`_final__ms_tight_stdout.txt`）

```
U1 写出 _f2_compare_out.json 形态：totals={"plus_path": 0, "plus_match": 1}
U2 _f2w_checks.py:29 读该 JSON → sha_ok=False（合法 match=True 被记成「sha 逐字不一致」，n_ok 少计 1）
U3 _f2w_extract.py:26-33 同一 JSON → verified='' recomputed='-' bytes='-'（19 条逐条表该行静默空白）
U4 _f2w_pass.py:17 / _f2v_final.py:54-58 → plus match=1 collected=0 tiers={'SAMEDOC_LINK_EQ': 1}（merged 被计入「已回验」统计，而 collected=0）
U5 门禁若只读 r11 problems（旧 :160 `FAIL if r11_problems else PASS`）且 link_triple 恒 problems=[]（_re_linked.py:47,177-179,330）→ 无单一回验路径的副本群被判 PASS（_ms_probe D6.6 实证）。
U6 结论链：merged rec → compare 写出 (plus_path=0, plus_match=1) → checks/extract 报告静默空白 → pass/final 把副本群计入已回验 → 门禁 problems=[] ⇒ PASS ⇒ 交付件在零单一对象锚定下被放行。
```

修好 `_f2v_verify9` 只堵住「崩」，堵不住从 `_f2_compare.py:100` 写进 `_f2_compare_out.json` 那一步已落盘的 `(0,1)` 口径。补丁 2 只在「门禁改接 plus 并注入 merged rec」时生效，也堵不住报告层的统计口径。

### 5.3 安全集应有几项（含复核修正）

**代码补丁 = 2 项**（本任务 §3/§4）；但作为**接入前置条件的最小安全集**，审计原文写的是 1–3（代码必做）+ 5–6（治理/审计必做）**共 5 条、第 4 条可选**（`MERGED_CONSUMER_AUDIT.md:181-188`），`_mc_AUDIT.md:184-185` 明列「1 处崩 + 7 处静默误读」，`MERGED_CONSUMER_AUDIT.md:137` 修正后为「1 崩 + 8 静默误读」。所以「审计说这两处就是最小集」与审计原文不符：两处是「两处实证缺陷的最小代码补丁」，**不是「接入的最小安全集」**。

按审计条款归并，本设计给出的接入前置 **4 项 + 1 项治理**：

| # | 项 | 性质 | 依据 |
|---|---|---|---|
| 1 | `_f2v_verify9.py:19-35` 三形态分支 | 代码（§3） | 唯一实证崩点 |
| 2 | `_g9_gate.py:155-167` `match=True and not path` 缺口 | 代码（§4） | 静默放行；0/30 回归漂移 |
| 3 | 接入点 `_f2_r11plus.py:303-305` 的合并契约 | 代码（属接入方，不在本任务两处补丁内） | `MERGED_CONSUMER_AUDIT.md:183-185` §5.2 第 1/2/3 条：显式 `tier=SAMEDOC_LINK_EQ`、不写 `verified_path/recomputed/bytes`、problems 恒 `[]`、只并 warnings、`members/decl_lines/samedoc_link` 全列；**且须修 B1/B2/B5 三件去单对象假设**（`:184`） |
| 4 | 计数口径裁决（**不是一处汇聚点**） | 契约/口径 | `MERGED_CONSUMER_AUDIT.md:184` 要求 B3/B6/B7/B8/B9/B10 显式区分「merged 匹配 ≠ 单一回验」；须分别覆盖 JSON 读者与直调者，见下方复核修正 |
| 5 | 判定书/台账登记 + run 快照 | 治理 | `MERGED_CONSUMER_AUDIT.md:187-188` §5.2 第 5/6 条；`:190-194` 指出离线提示模式无 owner / 触发条件 / sink |

**复核 ⑥ 修正（必须采纳）**：`_ms_DESIGN.md:439`/:440 与 `_ms_tight_stdout.txt` V4 称「6 件静默误读全读 `_f2_compare.py:100` 写出的同一 JSON」「一处汇聚点覆盖 6 件」，被逐件实读证伪。本会话实跑 `grep -rn "_f2_compare_out.json\|r11_scan_plus" "lead/r11_f2_fix_20261109/" --include="*.py"` 得：读 `_f2_compare_out.json` 的仅 `_f2w_checks.py:14`、`_f2_compare.py:17`（写者）、`_f2w_extract.py:13`、`_f2w_pass.py:6`、`_f2w_final.py:31`；另 `_f2_selftest.py:64,75,117`、`_f2v_final.py:50`、`_f2v_run.py:35`、`_f2w_dogfood.py:21` **直调 `plus.r11_scan_plus`**，不经该 JSON（审计 `MERGED_CONSUMER_AUDIT.md:79` 亦只说读者=那 3 件加 `_f2w_extract.py:13`）。故第 ④ 项必须按「两套消费面分别裁决」，不能按单点收敛；「4 项+1 治理」的**机制依据不成立，结论方向仍成立**（安全集不止两处）。计数口径亦不一致：`_ms_DESIGN.md` §四(a) 表格为 8 行、`MERGED_CONSUMER_AUDIT.md:137` 为 8 静默误读、`_mc_AUDIT.md:184-185` 为 7 静默误读，本件不冒充统一数字。

- 只修 1+2 不修 3：接入点仍 `tier=None`，merged 根本没接进来（现状合规但功能未上线）。
- 只修 1+2+3 不修 4：merged 接进来了，但 JSON 读者与直调者两路报告仍静默错、门禁之外的统计口径仍 fail-open。
- 只修 1+2+3+4 不修 5：无 run 快照 / 判定书 / owner，审计可追溯凭据缺失（`MERGED_CONSUMER_AUDIT.md:187-188,190-194`）。

### 5.4 接入前置条件与落地顺序（依 `_ms_DESIGN.md:459-469`，未验项如实标注）

| 序 | 哪件先改 | 为什么 | 验证 / 状态 |
|---|---|---|---|
| 0 | 先裁决不动代码：台账写明是否接入、谁负责、`SAMEDOC_LINK.md:20` ★4 显式修订 | `MERGED_CONSUMER_AUDIT.md:190-194`；不接也合规（`R33E_MERGE.md:17`） | **未验**（本会话未做） |
| 1 | `_f2v_verify9.py`（§3） | 唯一实证崩点；不先修则下游回放必崩 | 本会话已实跑：30 件 `checked 9` / `MISMATCH=0`；C3 七例全 `OK`；compile OK |
| 2 | `_g9_gate.py`（§4） | 静默放行；须与 1 同批 | 本会话已实跑：`0/30` 漂移、top/R11 keys 全同、self_test 全 True、`COUNTEREXAMPLE_OK` |
| 3 | 计数口径裁决（第 ④ 项，覆盖 JSON 读者 + 直调者两路） | 不裁决则 §5.2 传导链成立 | 本会话已实证错值（E1-E8 / U1-U6），**未改这些件、未验其修复** |
| 4 | `_f2_r11plus.py:303-305` 接入 `link_triple`（第 ③ 项，**最后才动代码**） | 前 3 项都是为它准备消费面 | 端到端联调断言 `tier/path/match/members/problems/warnings` 及 unique/zero/invalid_hex/multi 逐字节全等（`MERGED_CONSUMER_AUDIT.md:198`）；**未验** |
| 5 | 形状断言 7 件回归 | 接入不得破坏 `_re_linked.py` 三分支 | `_re_j4_cases.py`(19/19) / `_re_run10_diff.py`(20/20) / `_re_parity_extra.py`(21/21) / `_rev_core.py`(92/92) / `_rev_cases.py`(69/69) / `_rev_edge25.py`(7/7) / `_re_struct_diff.py`(STRUCT_OK)，记载见 `R33E_MERGE.md:190-204`；**本会话未重跑，未验** |
| 6 | 下游消费者全量回放（11 件可达件） | `MERGED_CONSUMER_AUDIT.md:199` 要求零 TypeError / 零 KeyError / 无误读计数 | 本会话只跑 8 个表达式（E 段 + C3/T4），**全量 11 件未做、未验** |
| 7 | 指纹护栏 + 台账登记 | 接入会改 `_f2_r11plus.py`；只读件与两件台账不得动 | 本会话 8/8 hashlib 全等（`F9 ALL_EIGHT_MATCH=True`），只读域无新增 `.pyc` |
| 8 | 门禁契约回归 + run 快照落盘 | 若将来改接 plus 须重裁 `:157-158`；merged 是联查时刻快照（TOCTOU 同限） | `MERGED_CONSUMER_AUDIT.md:200-202`；本会话只给注入前后基线，**改接 plus 后回归未做、未验** |

## 6 复核回件（绑定行）+ 未改任何件声明 + 未验项

### 6.1 绑定行（本会话 hashlib 实算，与编排方派发值全等；格式固定）

被核对象 SHA256 = c22f28ad4228d028c16d8558a8dd9a0980947631ab5bcf5c9cd84e529cf439e3，字节数 = 1618
被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

### 6.2 复核 verdict 如实登记

**复核 verdict = partial → unconfirmed**（【复核】回件）。四项硬门槛全部通过：② 自造 merged rec 键集与回件 A1 逐字一致（7 键、缺三键）、④ 顶层 10 键 / R11 10 键零增删、⑤ `OLD+ PASS / NEW+ FAIL` 反例 EXIT=0、⑧ 8 件 3 轮 hashlib 全等且无越界。两处补丁本身（compile、三形态/缺键、30 件回归、反例、接口不变）复核方亦全部独立复跑通过。

不能给 confirmed 的三点，本会话逐项核实**均成立**：

1. **「单点覆盖 6 件」被证伪**：`_ms_DESIGN.md:439`/:440 与 `_ms_tight_stdout.txt` V4 的「一处汇聚点覆盖 6 件静默误读」不成立；本会话 grep 实读见 §5.3，4 件直调 `r11_scan_plus` 不经 `_f2_compare_out.json`。审计原文 `MERGED_CONSUMER_AUDIT.md:79` 亦只列 3 件读者加 `_f2w_extract.py:13`。故第 ④ 项须改为「两路分别裁决」。计数口径亦不一致（DESIGN 8 行 / 审计 8 静默 / `_mc_AUDIT.md` 7 静默）。
2. **`merged members=None` 子例与 DESIGN 记载不符**：`_ms_DESIGN.md:259` 写「→ SKIP 不崩」，但 `_ms_v9_candidate.py:24` 因 `tier` 仍命中 merged 分支、`for m in (... or [])` 空转后 `continue`，输出 0 行；`_final_probe_stdout.txt` 的 `C3 merged members=None | … 改后 OK n=0 []` 与 `_msv_final_stdout.txt:17` `2.2 CASE 5 merged members=None 输出行数=0` 均证实「不崩但静默空跑、无确定输出」。这是候选 v1 的一处已知行为缺口，**不冒充 SKIP**；若落地，建议模板所有者把该分支补一条显式 `SKIP`。
3. **尺寸登记不符**：回件 `what` 称 `_ms_DESIGN.md = 34021 B`，本会话实算 `DESIGN bytes = 34299`、`DESIGN sha256 = bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44`（命令 `python -I -X utf8 -B -c "from pathlib import Path; … hashlib.sha256 …"`）。

复核方其余结论沿用：当下可达性复核（g7.r11_scan 不产 merged rec、`_g9_gate.py` 无 `r11_scan_plus/link_triple/_re_linked`、`_f2_r11plus.py:303-305` 仍空置、原件 `_f2v_verify9.py` 基线 EXIT=0）成立，severity=medium 成立。复核方 8 次 Bash 调用与 8 项点名检查的原文见【复核】回件；本会话**未重复其全部独立脚本**，只复跑其点名的 `_ms_probe.py` / `_ms_regress.py` / `_ms_counterexample.py` / `_ms_tight.py` 及本件 §2.1/§3.3 的实算，均如上登记。

### 6.3 未改任何件声明

本会话未改 `_f2v_verify9.py`、未改 `_g9_gate.py`、未改 `lead/r11_f2_fix_20261109/`、`lead/gate_r9r12_20261109/`、`lead/r33e_merge_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/merged_consumer_audit_20261109/` 及两件台账中的任何件；8 件指纹本会话实算与派发值全等（§2.1），原件仍含逐字 `:24` 与 `:160`（§3.1/§4.1 引用）。只在写域 `lead/merged_safety_20261109/` 新建本文件 `MERGED_MIN_SAFETY_PATCH.md` 与本次复跑输出 `_final_probe_stdout.txt` / `_final__ms_regress_stdout.txt` / `_final__ms_counterexample_stdout.txt` / `_final__ms_tight_stdout.txt`；复跑 4 支现成探针另按脚本自身行为重写了写域内同名输出件 `_ms_probe_out.txt`、`_ms_counterexample_deliverable.md`、`_ms_counterexample_out.txt`、`_ms_regress_out.txt`、`_ms_tight_out.txt`（本会话 `ls`/`stat` 核得 mtime 变为 11:49:52–11:49:58，属写域内输出件，非既有设计件；其内容与编排方留档的 `_ms_*_stdout.txt` 一致，未作人工编辑）。其余既有 `_ms_*` / `_msv_*` 候选与证据件一律未改，只读域全部件未改。零真机、零采样代码；Python 一律 `python -I -X utf8 -B` + 绝对路径；指纹用 `hashlib`；不 commit、不 push。

### 6.4 未验项（如实标注，不以局部实跑冒充）

- `link_triple` 接入 `r11_scan_plus` 的端到端联调（接入点 `_f2_r11plus.py:303-305` 仍空置）；
- 7 件形状断言回归（`MERGED_CONSUMER_AUDIT.md:197` 明写「本会话未重跑这 7 件，标未验」）；
- 11 件下游全量回放（本会话只跑 8 个表达式）；
- 门禁真正改接 plus 后的契约回归；
- 第 ④ 项两路计数口径裁决的修复与回归；
- 候选 v1 的 `merged members=None` 补 SKIP 后的回归；
- 离线提示模式的 owner / SOP / 触发条件是否补齐（`MERGED_CONSUMER_AUDIT.md:194` 指出全仓 0 个调度者）；
- 判定书 / 台账登记与 run 快照落盘。

以上均**未验**。
