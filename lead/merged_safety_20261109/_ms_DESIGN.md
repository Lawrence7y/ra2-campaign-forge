# _ms_DESIGN.md — 最小安全集补丁设计（只出设计，不落地）

日期 2026-11-09。写域：`lead/merged_safety_20261109/`。
**本件不改任何既有件**：`_f2v_verify9.py` / `_g9_gate.py` / 全部只读域件的指纹在本会话首尾两
次实算均全等（见 §0）。改后整件只作为「候选副本」写在本写域，由模板所有者决定是否落地。

被核对象 SHA256 = c22f28ad4228d028c16d8558a8dd9a0980947631ab5bcf5c9cd84e529cf439e3，字节数 = 1618
被核对象 SHA256 = a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6，字节数 = 11623

---

## §0 实跑命令与输出索引

| 命令（`python -I -X utf8 -B` + 绝对路径） | 输出件 | 用途 |
|---|---|---|
| `.../_ms_probe.py` | `_ms_probe_stdout.txt` / `_ms_probe_out.txt` | A–F 全部实证（造真 merged rec、:21-29 逐行、:155-166 链、三形态、反例、静默误读、8 件指纹） |
| `.../_ms_regress.py` | `_ms_regress_stdout.txt` / `_ms_regress_out.txt` | 门禁补丁 30 件回归对照（结构/verdict/self_test） |
| `.../_ms_tight.py` | `_ms_tight_stdout.txt` / `_ms_tight_out.txt` | 紧版 v2 对照 + 错误传导链 + 安全集边界 |
| `.../_ms_counterexample.py` | `_ms_counterexample_stdout.txt` / `_ms_counterexample_out.txt` | 可独立实跑的反例 |
| 原样运行 `.../_f2v_verify9.py` | 终端（本会话） | 基线 `checked 9` / `EXIT=0` |

全部 `EXIT=0`。候选副本：`_ms_v9_candidate.py`（v1）、`_ms_v9_candidate_v2.py`（v2）、
`_ms_g9_candidate.py`（门禁）。本会话共发起 **21 条 Bash 命令**；其中含
`python -I -X utf8` 的 Python 进程约 22 次（8 件指纹首/末两轮、`_f2v_verify9.py` 基线、
4 支探针的多次复跑、30 件回归对照、反例、以及若干次读取/打印输出的小 `-c` 片段）；
1 次因 shell 引号转义在 `-c` 里写成非法字符串而 SyntaxError，已用正向斜杠重跑成功。
下列命令均为 `python -I -X utf8 -B` + 绝对路径；`-c` 片段亦带 `-I -X utf8`。

**8 件指纹首/末两次实算全部 MATCH=True**（`_ms_probe` F 段 + 最终复核命令）：
`ALL_EIGHT_MATCH = True`、`ALL_EIGHT_UNCHANGED = True`。只读域无新增 `.pyc`。

---

## 第一步 独立核对两处缺陷

### (a) merged rec 的确切键集与缺键

`_ms_probe.py` A 段用 `_re_linked.py:303-331` 的 `link_triple` **真造** rec（不是手搓 dict）：
先在写域造 2 个同 hash 文件 + 一份含「复制自」声明、无显式路径的绑定行文档，再调
`link_triple(text, doc_dir, hex, bytes, root=REPO)`。输出（`_ms_probe_out.txt` A1–A6）：

```
link() verdict = merged ; link_triple problems = [] ; warnings_n = 1
A1 merged rec KEYS = ['decl_lines', 'declared', 'match', 'members', 'path', 'samedoc_link', 'tier']
A3 MISSING KEY verified_path    : True
A3 MISSING KEY recomputed       : True
A3 MISSING KEY bytes            : True
A4 path = None ; match = True ; tier = 'SAMEDOC_LINK_EQ' ; members_n = 2
A5 members = [{"path": .../_ms_mem_a.py, "sha": 3a6f5a…, "bytes": 27},
              {"path": .../_ms_mem_b.py, "sha": 3a6f5a…, "bytes": 27}]
A6 samedoc_link.reverify = None
```

**键集 = 7 键**：`declared / path / match / tier / samedoc_link / members / decl_lines`。
**缺 3 键**：`verified_path / recomputed / bytes`。`path=None`、`match=True`、
`tier=SAMEDOC_LINK_EQ`、`members` 全列 2 成员（各含 `path/sha/bytes`）。

源码依据：`_re_linked.py:310-313`（rec 骨架恒 `path=None`）、`:320-329`（merged 分支只写
`tier/match/members/decl_lines`，注释明写「不写 verified_path/recomputed/bytes 等单对象字段」）、
`:27-29 / :34-36`（merged 三纪律：path=None / 禁授权推论 / members 全列）、`:234-235`（unique
才有 `reverify`）、`:47 / :177-179 / :330`（problems 恒空，一律 warning 级）。

### (b) `_f2v_verify9.py:21-29` 逐行语义与错误前提

原文（`_f2v_verify9.py:20-35`，本会话 Read 全文）：

| 行 | 语义 |
|---|---|
| :20-22 | 遍历 `pb`；`match` 非 `True` 则 `continue` |
| :23 | `src = b.get("alt") or b` —— 假定存在「单对象记录」 |
| **:24** | **`vp = Path(src.get("verified_path") or src.get("path"))` ← 基于错误前提** |
| :25-27 | 读该单对象字节、重算 sha256/size |
| :28 | `ok_sha = sha == b["declared"].lower()` |
| **:29** | **`ok_bytes = size == src["bytes"]` ← 同样基于「必有单对象 bytes」** |
| :30-34 | 打印（`b["declared"]`、`src["bytes"]` 再下标一次） |

`_ms_probe` B 段在该真 rec 上逐行复跑：

```
B0 :21 match=True ⇒ 不 continue
B1 :23 alt=None，src is b = True
B2 :24 Path(src.get('verified_path') or src.get('path')) → TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'
B2 :29 size == src['bytes'] (src['bytes'] 求值) → KeyError: 'bytes'
B2 :34 src['bytes'] (print 参数求值) → KeyError: 'bytes'
B4 绕过 :24 后 :29 → KeyError: 'bytes'
```

**错误前提 = 「`match is True` ⇒ 一定有单一 `verified_path`/`path`（及 `bytes`）」**。用 (a) 的
rec 形态证伪：`match=True` 且 `path=None` 且三键全缺；单对象信息只存在于 `members`（副本群，
2 成员）。`_re_linked.py:306-308` 明写 `match=True` **仅指声明 hex 与全体成员现盘重算逐位一致**，
不指向任何单一对象；`:30-33` 禁止由 merged 推导授权/锚定结论。所以 :24 的 `Path(None)` 与
:29/:34 的 `src["bytes"]` 都是把「副本群匹配」误当「单对象回验」。

**两处都确实崩**（与编排方一致，无反例）。补充：`:34` 是第三个 `KeyError` 点（在 print 参数
求值），任务只点 :24/:29，但补丁须一并覆盖，否则 :24/:29 修好后 :34 仍崩。

### (c) `_g9_gate.py:155-166` 判定链

原文判定链（`:155-160`，本会话 Read 全文）：`g7.r11_scan` → `bindings=[dict(b)...]` →
`n_reverified = sum(1 for b if b.get("path"))`、`n_match = sum(1 for b if b.get("match") is True)`
→ `r11_verdict = "FAIL" if r11_problems else "PASS"`。`:163` 把 `reverified`/`match_true` 记入
`predicates["R11"]`，`:164-166` 存 `binding_details` 与 verdict；`:178-179` overall 取四谓词全 PASS。

`_ms_probe` D2/D4 与 `_ms_counterexample.py` 实跑：

```
D4 注入真 merged rec 时 旧 = n_bindings=1 items=2 reverified=0 match_true=1 problems=[] verdict=PASS
D6.6 OLD+ R11=PASS verdict=PASS reverified=0 match_true=1 problems=[]
```

**输入条件**：`bindings` 中至少一条 `match is True and not path`（merged rec 正是此形），且
`r11_problems == []`。`link_triple` 的 `problems` 恒 `[]`（`_re_linked.py:47,177-179,330`），
故旧式 `:160` 只看 `r11_problems` 必得 `PASS`。`reverified`/`n_match` 只是**记账字段，不参与判定**——
这正是缺口：`match_true=1` 但 `reverified=0` 仍 PASS。

**PASS 的语义**：「匹配但无单一回验路径」被当成通过。门禁的职责是**回验**（`:2` docstring、
`:17`「每条绑定行回验一项」、`_g7_predicates.py:158-168` R11「路径隔断容忍 + 引用锚回验」）；
`reverified=0` 意味着本次运行对这条绑定行**一件对象都没回验过**，把「未回验」计成「通过」
等于门禁空跑。模块自己在 `:18-19` 已立「第 3 类空跑防线：任一谓词 items==0 ⇒ FAIL_EMPTY」，
但 R11 的 `items = 1 + len(bindings)` 含「存在性强制项」，`reverified=0` 不触发 FAIL_EMPTY，
于是空跑从 items 防线下面漏过去。

### ★ 两处都是「未来接入面」，不是「现在就崩/就放行」

本会话两条 grep 实跑（`GREP_EXIT=1` = NO_MATCH）：

- `grep -n "r11_scan_plus\|link_triple\|_re_linked\|_sl_link" lead/gate_r9r12_20261109/_g9_gate.py` → 无命中；`:155` 实读 `g7.r11_scan(text, d_dir, root=root)`（`_g7_predicates.py:157-222`），**不调 link 家族、不产 merged rec**。`_ms_probe` D1 = `False`。
- `grep -n "link_triple\|_re_linked\|_sl_link\|\blink(" lead/r11_f2_fix_20261109/_f2_r11plus.py` → 无命中；接入点 `:303-305` 的 else 现仍是 `rec["tier"] = None` + `warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")`（本会话 Read）。

`_ms_probe` D0/D2 实证：对同一份反例交付件，今日 `g7.r11_scan` 产出
`bindings=[{'declared': ..., 'path': None, 'match': None}]`、`problems=[]`、一条 R3-3b warning，
旧门禁 `verdict=PASS` **来自 R3-3b warning 不算 problem，与 link 家族/merged 无关**。
`_f2v_verify9.py` 原样运行本会话基线 = `checked 9` / `EXIT=0`（9 条 match=True 全为 T1/T2/T2N/T3
单对象形态）。

与 `MERGED_CONSUMER_AUDIT.md:78,133,165` 一致：审计【复核】已把「门禁静默放过」从**已存在
消费方**撤下，改列「未来的消费方·不可达，但应知道」。本设计把两处都按「未来接入前置补丁」
处理，**不宣称当下生产在崩或在放行**。

---

## 第二步 `_f2v_verify9.py` 最小补丁

### (a) 改前片段（`:19-35` 逐字原文）

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
```

`C0` 实跑：该片段**逐字**包含在原件中，`count=1`。（`:36` 的 `print("   *** MISMATCH ***")`
与 `:37` `print("checked", n)` 均**不动**。）

### (b) 改后片段（v1，本设计推荐）

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
```

要点：

1. **merged 分支单独处理**：先判 `tier=="SAMEDOC_LINK_EQ" or b.get("members")`，走
   `rec["members"]` 逐成员 `path/sha/bytes` 重算（`_re_linked.py:280-281` 已保证全列），
   `continue` 不落回单对象逻辑。
2. **不主张单一 path**：merged 分支从不读 `rec["path"]` / `verified_path` / `recomputed`；
   `mp` 为 `None` 时读空字节串（`bytes_ok=False`），不 `Path(None)`。
3. **缺键不崩**：所有下标改 `.get()`（`declared` / `bytes` / `member.path` / `member.bytes`），
   `:34` 的 `src["bytes"]` 一并改 `src.get("bytes")`。
4. **multi 有确定行为**：无 `path` 且无 `members` → 打印 `SKIP#…` 并 `continue`，绝不触碰单对象键。
5. **unique 路径逐字保留**：`src = b.get("alt") or b` → `Path(src.get("verified_path") or src.get("path"))`
   与输出格式串未改；`alt` 分支（`_f2_r11plus.py:124-136` 的 `_verify_candidate` 返回含
   `path/bytes`，不含 `verified_path`）继续靠 `or` 回退到 `path`。

实测（`_ms_probe_out.txt` C1/C2/C3）：`compile()=OK`；改后整件**跑真实 30 件**末行
`checked 9`、`MATCH=9`、`MISMATCH=0`（与原件基线一致）；`unique` 输出与原版逐字同形。

### (c) 「最小」体现在哪（行数实算）

`_ms_probe` C 段用 `difflib.SequenceMatcher` 对 `:19-35` 的 17 行逐行比对：

```
[V9:19-35] difflib: before=17 lines, after=39 lines, unchanged=13, removed=4, added=26, modified=4
```

- **不动 13 行**：`:19-22`（循环头+match 守卫）、`:25-27`（读字节+hashlib+size）、`:30-33`
  （n+=1 与三行 print）、`:35`（`if not (ok_sha and ok_bytes):`）全部原样保留在 unique 分支。
- **改动 4 行**：`:24` `Path(...)`→ 保留但加守卫；`:28` `b["declared"]`→`b.get(...)`；`:29`
  `src["bytes"]`→`src.get("bytes")`；`:34` 同上。
- **新增 26 行** = merged 分支 14 行 + multi 守卫 3 行 + 注释/空行 9 行。
- **改前片段之外零改动**：`:1-18`、`:36-38` 一字不动；整件只做这一处字符串替换。
- 另验过「更紧」的 v2（`_ms_tight.py`，把 `:23` 换成三形态 dispatch、原循环体整体缩进）：
  `compile=OK`、真实 30 件 `checked 9`，但 difflib `unchanged=4 / removed=14 / added=25`
  （净改 39 行），**因为缩进整块使 13 行被判为删除**，反而更不「最小」。故推荐 v1。
- 门禁补丁的「最小」另见 §三(c)：`unchanged=13 / removed=0 / added=4`，且 30 件 verdict
  改变 **0/30**（`_ms_regress_out.txt` R4）。

### (d) 三种形态的预期行为（全部实跑，见 `_ms_probe_out.txt` C3）

| 形态 | 输入 | 原版 | 改后行为 | 是否掉 KeyError |
|---|---|---|---|---|
| **unique**（有 path） | 真 `link_triple` unique rec（`tier=SAMEDOC_LINK`, `path=…/_ms_uniq.py`, 带 `verified_path/recomputed/bytes`） | OK `sha_ok=True bytes_ok=True` | 走保留的 unique 分支，`MATCH#1 sha_ok=True bytes_ok=True` | 否 |
| **merged**（无 path 有 members） | 真 `link_triple` merged rec（2 成员） | `TypeError Path(None)` | 逐成员 2 行 `MATCH#1/#2 … sha_ok=True bytes_ok=True` | 否 |
| **multi**（无 path 无 members） | 真 multi rec（`match=None`）+ 合成 `match=True, path=None, members` 缺 | 真 rec 跳过；合成版 `TypeError Path(None)` | 真 rec 跳过；合成版 1 行 `SKIP#1 … 无单一回验路径且无 members` | 否 |

额外缺键注射（C3 后 4 行）：`merged 缺 member.bytes` → `bytes_ok=False` 不崩；
`merged members=None` → `SKIP` 不崩；`unique 缺 bytes` → `bytes_ok=False` 不崩。
三种形态 + 4 种缺键共 7 例**改后列全部 `OK`**，零 `TypeError` / 零 `KeyError`。
`_ms_tight.py` T4 另用「把 bindings 注入改后整件」的方式复验 8 例（含 mixed
unique+merged+multi），全部 `OK`。

---

## 第三步 `_g9_gate.py` 最小补丁

### (a) 改前片段（`:155-167` 逐字原文）

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

`D6.0` 实跑：该片段**逐字**包含在原件中，`count=1`。

### (b) 改后片段

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

- **merged 不得 PASS**：条件精确锁在缺陷签名 `match=True and not path`；`link_triple` 的 merged
  rec 正是 `match=True / path=None`，命中即追加一条 problem ⇒ `r11_verdict="FAIL"` ⇒
  `:178-179` overall FAIL。实跑 `D6.7` / `_ms_counterexample.py` `NEW+ verdict=FAIL`。
- **保持 `check_deliverable` 返回值结构不变**：`predicates["R11"]` 的键一个不加、一个不减；
  只改 `r11_problems` 列表的**内容**与 `verdict` 的**值**。`:169-176` 合并视图靠
  `r11_problems` 自动带上 `{"rule_id":"R11","msg":...}`，无需改下游。实跑
  `D6.3 top keys 相同 = True`、`D6.4 R11 keys 相同 = True`、`D6.5 两结果均 JSON 可序列化 = True`。
- **不误伤既有 30 件**：`_ms_regress.py` 逐件跑 OLD/NEW，`R4 verdict 改变件数 = 0 / 30`、
  `R2/R3 keys 全同`、`R6 self_test old/new all_pass=True`、`D6.8` 三项自检全 True。

**为何不用更宽的 `len(bindings) - n_reverified > 0`**：本会话先试过该写法
（`_ms_probe.py` 初版 AFTER_G9），`_ms_regress.py` 首次实跑给出
`R4 verdict 改变件数 = 6 / 30`（`A_REDUCED_FORM.md`、`A_RESIDUAL_REFERENCES.md`、
`INTEGRATION_REPORT.md`、`_integ_INTEGRATION_REPORT.md`、`B_EXECUTION_SPEC.md`、
`_n4_SPEC_N4_B2B_MATRIX.md` 全部 `rev=0 R11 PASS→FAIL`），因为这些件**本来就有 R3-3b
无路径绑定行**且旧门禁按现状判 PASS。把它们一并翻成 FAIL 是「改变既有门禁策略」，不是
补这个缺陷；收窄到 `match=True and not path` 后为 0/30。此对比已实跑留档，是「最小」的实证依据。

### (c) 为什么「reverified=0 就算过」是错的

1. **门禁职责是回验，不是记账**。`:2` docstring「四谓词可复用门禁模块」、`:17`「R11 items =
   1 + len(绑定行) —— 「≥1 条绑定行」强制项 + 每条绑定行回验一项」、
   `_g7_predicates.py:158-168`「R11 绑定行路径隔断容忍 + 引用锚回验」：R11 的每一项 items 都
   对应一次**现盘重算**（`_g7_predicates.py:206-215`）。`reverified=0` 表示这些 items 一个都没
   真正执行回验。
2. **模块自己已立「空跑不得 PASS」原则**：`:13-19` 第 3 类防线明写「任一谓词 items == 0 ⇒
   FAIL_EMPTY（计 FAIL）」「0 项不得 PASS」，`:121-122 / :138-139 / :151-152` 对 R9/R10/R12 逐条
   落地。但 R11 的 `items = 1 + len(bindings)` 里那 1 是「存在性」，于是
   `items>=1` 恒成立，`reverified=0` 从防线下面漏过去 —— 这是**防线覆盖缺口**，不是设计意图。
3. **`match_true` 与 `reverified` 语义不同**：`match=True` 在 merged 形态下仅表示「声明 hex 与
   全体成员逐位一致」（`_re_linked.py:306-308`），`_re_linked.py:30-33` 明确「merged 不构成对
   任一成员的锚定、放行或授权」。把 `match_true=1` 当回验成功，等于用副本群的**存在性**替代了
   对**单一被核对象**的锚定，违反 merged 纪律二。
4. **fail-open 方向错**：门禁只允许在「已回验且一致」时 PASS；「未回验」的正确输出是
   FAIL（或至少显式人工锚定告警升级），而不是静默 PASS。旧式 `:160` 只看 `r11_problems`，
   而 `link_triple` 恒 `problems=[]`（`_re_linked.py:47,177-179,330`），所以 merged 一旦流入，
   门禁必然 fail-open。

### (d) 可实跑反例：旧门禁 PASS / 新门禁 FAIL

独立脚本：`lead/merged_safety_20261109/_ms_counterexample.py`
（命令：`python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_ms_counterexample.py"`，
本会话 `EXIT=0`，输出件 `_ms_counterexample_stdout.txt`）。

交付件 = `_ms_counterexample_deliverable.md`（283 B，写在写域）：一条**无显式路径**的绑定行
`被核对象 SHA256 = 3a6f5a…eafc5e5，字节数 = 27`，正文同文档列 2 个成员
`_ms_fixtures/_ms_mem_a.py` / `_ms_mem_b.py`（同 27 B、同 hash），并以
「`_ms_mem_b.py` 复制自 `_ms_mem_a.py`」命中 `DECL_RE`（`_re_linked.py:81`）。

```
STEP1 link_triple: tier=SAMEDOC_LINK_EQ match=True path=None members_n=2 problems=[]
       → 单一 path 不存在；唯一可回验路径是 members（副本群）。
STEP2 OLD  check_deliverable: verdict=PASS R11=PASS reverified=0 match_true=0 problems=[]
STEP2 NEW  check_deliverable: verdict=PASS R11=PASS reverified=0 match_true=0 problems=[]
STEP3 说明：:155 用 g7.r11_scan（不产 merged rec）…要复现「merged 匹配被放行」须注入 rec。
STEP2 OLD+ check_deliverable: verdict=PASS R11=PASS reverified=0 match_true=1 problems=[]
STEP2 NEW+ check_deliverable: verdict=FAIL R11=FAIL reverified=0 match_true=1 problems=['R11 回验缺口：1 条绑定行 match=True 但无单一回验路径（merged 副本群不得默认放行），须人工锚定']
结论：返回结构 top keys 相同 = True / R11 keys 相同 = True / COUNTEREXAMPLE_OK
```

**必须如实说明**：`OLD`（不注入）与 `NEW`（不注入）都 PASS，因为今日 `:155` 走
`g7.r11_scan` 根本不产 merged rec（见 §一★）。`OLD+ / NEW+` 是按
`MERGED_CONSUMER_AUDIT.md:133,165` 的口径，「将来门禁改接 plus」时把 `link_triple` 的真
merged rec 注入 `g7.r11_scan` 返回位。**因此该反例证明的是未来接入面的缺陷与补丁效果，
不是当下生产事故**。任务要求的「旧门禁 PASS、新门禁 FAIL」在 `OLD+ / NEW+` 下成立且可实跑。

---

## 第四步 最小安全集的边界

### (a) 审计还点了 6 件「静默误读」，算不算安全集？

**算「安全判定可信性」的一部分，但不算「本任务两处补丁」的第三、第四处代码改动。**

`_ms_probe` E 段把 6 件在真 merged rec 上逐个实跑（均**不崩**、均产出错结论）：

| 件:行 | 实跑输出 | 错在哪 |
|---|---|---|
| `_f2w_checks.py:29` | `sha_ok = False` | 合法 `match=True` 被记成「sha 逐字不一致」，`n_ok` 少计 1 |
| `_f2_selftest.py:110` | `endswith('_f2_r11plus.py') = False` | S4 断言失败 |
| `_f2_compare.py:67,69` | `(plus_path, plus_match) = (0, 1)` | 计数口径混杂 |
| `_f2v_final.py:54,57-58` | `collected=0 tiers={'SAMEDOC_LINK_EQ': 1}` | 开放 dict 不崩、结论错 |
| `_f2v_run.py:48-52` | `plus_paths=[None] plus_match=[True]` | 列表化后静默空白 |
| `_f2w_dogfood.py:25-30` | `collected=0 match=1 tiers={'SAMEDOC_LINK_EQ': 1}` | 同 `_f2v_final` |
| `_f2w_extract.py:26-33` | `verified='' recomputed='-' bytes='-'` | 19 条逐条表该行静默空白 |
| `_f2w_pass.py:15,17` | `plus match 计数 = 1` | merged 混入单一回验 PASS 统计 |

这些件都是「交付报告用」输出（本会话 Read 各件 docstring：`_f2w_checks.py:2-6`、
`_f2w_extract.py:2-4`、`_f2w_pass.py:2`、`_f2v_final.py` / `_f2w_dogfood.py` 自扫报告）。

**判据（崩 vs 静默错，哪个更该进安全集）**：

- 崩 = **fail-closed**。接入后审计 §5.2 第 3 步「下游消费者全量回放」立刻
  `TypeError`/`KeyError`，联调根本完不成，人必须来修 → **不会把错误结论发布出去**。
- 静默错 = **fail-open**。程序全绿、报告照出、门禁 PASS，但「无单一回验路径的副本群」被
  记成已回验/被判通过 → **错误结论会进台账/裁决**。

故按「不修则安全判定不可信」定义安全集时，**静默错比崩更该进安全集**；按「不修则程序退出」
定义时只有崩进。本任务采用前者（与「门禁的职责是回验」一致）。

### (b) 只修两处、其余静默误读不修 → 具体错误传导链

`_ms_tight.py` U 段逐段实跑（U1–U6）：

```
接入点 _f2_r11plus.py:303-305 合入 merged rec
  → _f2_compare.py:100 写出 _f2_compare_out.json：totals={"plus_path":0,"plus_match":1}   [U1]
  → _f2w_checks.py:29   读该 JSON：sha_ok=False（合法 match=True 被记成逐字不一致）      [U2]
  → _f2w_extract.py:26-33 同一 JSON：verified='' recomputed='-' bytes='-'（报告空白）      [U3]
  → _f2w_pass.py:17 / _f2v_final.py:54-58：plus match=1 collected=0，
     tiers={'SAMEDOC_LINK_EQ':1}（副本群被计入「已回验」统计）                            [U4]
  → 门禁只读 r11_problems；link_triple 恒 problems=[] ⇒ PASS                              [U5, D6.6 实证]
  ⇒ 交付件在零单一对象锚定下被放行                                                        [U6]
```

即使 `_f2v_verify9.py` 已修好（不再崩），**链条从 `_f2_compare_out.json` 那一步已经把
`(0,1)` 写进机读件**，后续 4 件报告全部继承这个口径。修两处只堵住了「崩」与「门禁注入
merged 时放行」，堵不住「报告与统计把 merged 当单对象回验」。

### (c) 安全集该有几项？

**结论：代码补丁 = 2 项（本任务两处）；但「最小安全集」作为接入前置条件 = 4 项，
另加 1 项治理/裁决。两处不足以称「够」。**

| # | 项 | 性质 | 依据 |
|---|---|---|---|
| 1 | `_f2v_verify9.py:19-35` 三形态分支 | 代码（本设计 §二） | 唯一实证崩点；不修则接入联调第 3 步直接失败 |
| 2 | `_g9_gate.py:155-167` `match=True and not path` 缺口 | 代码（本设计 §三） | 静默放行；补后 0/30 回归漂移 |
| 3 | **接入点 `_f2_r11plus.py:303-305` 的合并契约** | 代码（属接入方，**不在本任务两处补丁内**） | `MERGED_CONSUMER_AUDIT.md:181-185` §5.2 第 1/2/3 条：须显式 `tier="SAMEDOC_LINK_EQ"`、不写 `verified_path/recomputed/bytes`、problems 恒 `[]`、只并 warnings、`members/decl_lines/samedoc_link` 全列 |
| 4 | **`_f2_compare_out.json` 计数口径裁决** | 契约/口径（一处汇聚点覆盖 6 件） | 6 件静默误读全读 `_f2_compare.py:100` 写出的同一 JSON（`MERGED_CONSUMER_AUDIT.md:79,121-130` + 本会话 Read）；须显式区分「merged 匹配 ≠ 单一回验」，例如 `plus_match` 不把 `tier=SAMEDOC_LINK_EQ` 计入单对象回验列 |
| 5 | 判定书/台账登记 + run 快照 | 治理 | `MERGED_CONSUMER_AUDIT.md:187-188` §5.2 第 5/6 条、`_re_NOTES.md:72-73`（TOCTOU 快照） |

理由：本任务铁律限定「只出两处补丁设计、不改任何既有件」，故**交付 2 项补丁**；但第四步问
「安全集边界」，必须指出审计 §5.2 自己写的是「1–3（代码必做）+ 5–6（治理/审计必做）」共
5 条、第 4 条可选（`MERGED_CONSUMER_AUDIT.md:181-188`），**并非「只有这两处」**。
`_mc_AUDIT.md:184-185` 也明列「1 处崩 + 7 处静默误读」。因此「审计说这两处就是最小集」
这一表述与审计原文不符：两处是**「两处实证缺陷的最小代码补丁」**，不是**「接入的最小安全集」**。

**会漏什么**：只修 1+2 不修 3+4，见 (b) 传导链；只修 1+2 不修 3，`_f2_r11plus.py:303-305`
依旧 `tier=None`，merged 根本没接进来（现状合规但功能未上线）；只修 1+2+3 不修 4，
merged 接进来了但 6 件报告静默错、门禁之外的统计口径仍 fail-open。

---

## 第五步 接入前置条件清单（落地顺序）

接入点唯一：`lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的 `else`（本会话 Read 实读现为
`rec["tier"]=None` + R3-3b warning）。`_re_linked.py` 保持只读（`7ca339c6…/19481`）。

| 序 | 哪一件必须先改 | 为什么 | 怎么验证改完（本会话实跑 / 须接入方复跑） |
|---|---|---|---|
| **0** | **先裁决，不动代码**：台账写明是否接入、谁负责、`SAMEDOC_LINK.md:20` ★4 的显式修订 | `MERGED_CONSUMER_AUDIT.md:190-194` 指出离线人工提示模式「无 owner / 触发条件 / sink」，`R33E_MERGE.md:17`「本报告不自行上线」；不接也合规 | 判定书条目存在；本项非代码，**本会话未做、标「未验」** |
| **1** | `_f2v_verify9.py:19-35`（补丁 §二） | 唯一实证崩点；不先修则第 4 步「下游消费者全量回放」必 `TypeError`/`KeyError` | 本会话已实跑：改后整件真实 30 件 `checked 9` / `MISMATCH=0`；C3 七例（三形态+4 缺键）改后全 `OK`；`C0 BEFORE 逐字 count=1`、`C1 compile=OK` |
| **2** | `_g9_gate.py:155-167`（补丁 §三） | 静默放行；且必须与 1 同批交付，否则门禁对 merged 无防线 | 本会话已实跑：`D6.7 NEW+ FAIL` / `D6.6 OLD+ PASS`；`_ms_regress.py R4 = 0/30`、`R2/R3 keys 全同`、`R6 self_test all_pass=True`、`D6.8` 三项 True；`_ms_counterexample.py COUNTEREXAMPLE_OK` |
| **3** | `_f2_compare.py` / `_f2w_*` / `_f2v_final` / `_f2v_run` 的**计数口径裁决**（第 4 项） | 6 件静默误读汇聚于 `_f2_compare_out.json`；不裁决则 (b) 传导链成立 | 本会话 `E1-E8`、`U1-U6` 实证错值；接入方须复跑并断言 `plus_path` 与「单一回验」列分离、merged 单列 `tier=SAMEDOC_LINK_EQ`；**本会话未改这些件、标「未验」** |
| **4** | `_f2_r11plus.py:303-305` 接入 `link_triple`（第 3 项，**最后才动代码**） | 前 3 项都是为它准备消费面；先接会让 1/2/3 未修的下游直接暴露 | 接入方端到端联调：`tier=="SAMEDOC_LINK_EQ"`、`path is None`、`match is True`、`members` 全列、`problems==[]`、warnings 含「禁止由 merged 推导任何授权结论」、unique/zero/invalid_hex/multi 输出与接入前逐字节全等（`MERGED_CONSUMER_AUDIT.md:198`）。**本会话未做、标「未验」** |
| **5** | 形状断言 7 件回归 | 保证 `_re_linked.py` 三分支未被接入改动破坏 | `_re_j4_cases.py`(19/19) / `_re_run10_diff.py`(20/20) / `_re_parity_extra.py`(21/21) / `_rev_core.py`(92/92) / `_rev_cases.py`(69/69) / `_rev_edge25.py`(7/7) / `_re_struct_diff.py`(STRUCT_OK) —— 记载见 `R33E_MERGE.md:190-204`；**本会话未重跑这 7 件，标「未验」** |
| **6** | 下游消费者全量回放（11 件可达件） | `MERGED_CONSUMER_AUDIT.md:199` 要求零 `TypeError` / 零 `KeyError` / 无误读计数 | 把真 merged rec 喂给 §3.4 B 表每一件；本会话只实跑了其中 8 个表达式（E 段 + C3/T4），**全量 11 件回放未做、标「未验」** |
| **7** | 指纹护栏 + 台账登记 | 接入会改 `_f2_r11plus.py`（审计基线 `83f8217f…/15723`），只读件与两件台账不得动 | 接入前后用 `hashlib.sha256` 登记 `_re_linked.py` / `_f2_r11plus.py` / 两件台账；本会话首尾实算 8/8 全等（`F9 ALL_EIGHT_MATCH=True`、最终 `ALL_EIGHT_UNCHANGED=True`），只读域无新增 `.pyc` |
| **8** | 门禁契约回归 + run 快照落盘 | 若将来把 `_g9_gate.py` 改接 plus，须重裁 `:157-158` 口径；merged 是联查时刻快照 | `MERGED_CONSUMER_AUDIT.md:200-202`；本会话 `D6.6/D6.7` 已给注入前后的对照基线，**接入方自己改接 plus 后的回归未做、标「未验」** |

---

## 未验项 / 纪律声明

- **未验**：`link_triple` 接入 `r11_scan_plus` 的端到端联调（接入点 `:303-305` 仍空置）；
  7 件形状断言回归；11 件下游全量回放；门禁真正改接 plus 后的回归；离线提示模式的 owner/SOP
  是否已补。以上均按「未验」标注，不以本会话的局部实跑冒充。
- 本会话**未改任何既有件**：`_f2v_verify9.py`、`_g9_gate.py`、只读域全部件、两件台账。
  改后整件仅为写域候选副本（`_ms_v9_candidate.py` / `_ms_v9_candidate_v2.py` /
  `_ms_g9_candidate.py`），供模板所有者决定是否落地。
- 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
  零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；
  Python 一律 `python -I -X utf8 -B` + 绝对路径；指纹用 `hashlib`；不 commit、不 push。
- 任务要求的「复核回件绑定行」格式（写「被核对象 SHA256 = 」紧跟完整 64 位 hex、
  中间不得插入任何字符，随后「，字节数 = 」+ 数字）：见本件开头两行，分别对应
  `_f2v_verify9.py` 与 `_g9_gate.py`（值取自本会话实算，与编排方派发值全等）。
