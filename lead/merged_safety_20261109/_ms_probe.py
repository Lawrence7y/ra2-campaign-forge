# -*- coding: utf-8 -*-
"""_ms_probe.py — 最小安全集补丁设计：独立复跑/实证。

只读取既有件；所有新写文件均在 lead/merged_safety_20261109/ 内。
零真机、零采样代码；指纹用 hashlib；-I -X utf8 -B；sys.dont_write_bytecode。
本件不修改 _f2v_verify9.py / _g9_gate.py / 任何既有件：改后整件只作为
「候选副本」写入本写域（_ms_v9_candidate.py / _ms_g9_candidate.py），
用标准 importlib 模块加载器验证可跑；既有件指纹全程未变。
"""
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
FIX = W / "_ms_fixtures"
FIX.mkdir(parents=True, exist_ok=True)

V9 = REPO / "lead" / "r11_f2_fix_20261109" / "_f2v_verify9.py"
G9 = REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
RE = REPO / "lead" / "r33e_merge_20261109" / "_re_linked.py"
G7P = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

OUT = []


def say(s=""):
    OUT.append(str(s))
    print(s)


def load(name, path):
    """标准模块加载器；不用 exec 内置函数。"""
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RE_MOD = load("_ms_re_linked", RE)
G7 = load("_ms_g7_predicates", G7P)

# ---------------------------------------------------------------- 补丁文本
# _f2v_verify9.py :19-35 原文（逐字，来自本会话 Read 全文 :19-35）
BEFORE_V9 = '''    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
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
'''

AFTER_V9 = '''    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
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
'''

# _g9_gate.py :155-167 原文（逐字，来自本会话 Read 全文 :155-167）
BEFORE_G9 = '''    r11_problems, r11_warnings, bindings = g7.r11_scan(text, d_dir, root=root)
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
'''

AFTER_G9 = '''    r11_problems, r11_warnings, bindings = g7.r11_scan(text, d_dir, root=root)
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
'''


def diffcount(before, after, tag):
    b, a = before.splitlines(), after.splitlines()
    sm = difflib.SequenceMatcher(None, b, a, autojunk=False)
    added = removed = unchanged = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            unchanged += i2 - i1
        else:
            removed += i2 - i1
            added += j2 - j1
    say("[%s] difflib: before=%d lines, after=%d lines, unchanged=%d, removed=%d, added=%d, modified=%d"
        % (tag, len(b), len(a), unchanged, removed, added, min(removed, added)))
    return dict(before=len(b), after=len(a), unchanged=unchanged,
                removed=removed, added=added)


# ================================================================ A. 造真实 merged rec
say("=" * 78)
say("A. 用 link_triple 真造 rec（unique / merged / multi）")
say("=" * 78)

MEM = b"# merged member\nprint('x')\n"
MA, MB = FIX / "_ms_mem_a.py", FIX / "_ms_mem_b.py"
MA.write_bytes(MEM)
MB.write_bytes(MEM)
MHEX = hashlib.sha256(MEM).hexdigest()
MBYTES = len(MEM)

merged_text = (
    "# 交付件（反例）\n\n"
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "两个产物：`_ms_mem_a.py` 与 `_ms_mem_b.py`。\n"
    "`_ms_mem_b.py` 复制自 `_ms_mem_a.py`。\n"
) % (MHEX, MBYTES)
DELIVERABLE = FIX / "_ms_deliverable.md"
DELIVERABLE.write_text(merged_text, encoding="utf-8")

mp, mw, merged_rec = RE_MOD.link_triple(merged_text, FIX, MHEX, MBYTES, root=REPO)
say("merged_text:\n" + merged_text.rstrip())
say("link() verdict = %s ; link_triple problems = %r ; warnings_n = %d"
    % (merged_rec["samedoc_link"]["verdict"], mp, len(mw)))
say("A1 merged rec KEYS = %s" % sorted(merged_rec.keys()))
say("A2 merged rec = %s" % json.dumps({k: v for k, v in merged_rec.items()
                                      if k != "samedoc_link"}, ensure_ascii=False, sort_keys=True))
for k in ("verified_path", "recomputed", "bytes"):
    say("A3 MISSING KEY %-16s : %s" % (k, k not in merged_rec))
say("A4 path = %r ; match = %r ; tier = %r ; members_n = %d"
    % (merged_rec.get("path"), merged_rec.get("match"),
       merged_rec.get("tier"), len(merged_rec.get("members") or [])))
say("A5 members = %s" % json.dumps(merged_rec.get("members"), ensure_ascii=False))
say("A6 samedoc_link.reverify = %r" % merged_rec["samedoc_link"].get("reverify"))

# unique
UNIQ = FIX / "_ms_uniq.py"
UNIQ.write_bytes(b"# unique\n")
UHEX = hashlib.sha256(UNIQ.read_bytes()).hexdigest()
uniq_text = "被核对象 SHA256 = %s，字节数 = %d\n\n产物：`_ms_uniq.py`。\n" % (UHEX, len(UNIQ.read_bytes()))
up, uw, uniq_rec = RE_MOD.link_triple(uniq_text, FIX, UHEX, len(UNIQ.read_bytes()), root=REPO)
say("A7 unique rec KEYS = %s ; path=%r match=%r tier=%r"
    % (sorted(uniq_rec.keys()), uniq_rec.get("path"), uniq_rec.get("match"), uniq_rec.get("tier")))

# multi（不加溯源声明词）
MULA, MULB = FIX / "_ms_mul_a.py", FIX / "_ms_mul_b.py"
MULA.write_bytes(b"# multi member\n")
MULB.write_bytes(b"# multi member\n")
XHEX = hashlib.sha256(MULA.read_bytes()).hexdigest()
multi_text = "被核对象 SHA256 = %s，字节数 = %d\n\n两个产物：`_ms_mul_a.py` 与 `_ms_mul_b.py`。\n" % (
    XHEX, len(MULA.read_bytes()))
xp, xw, multi_rec = RE_MOD.link_triple(multi_text, FIX, XHEX, len(MULA.read_bytes()), root=REPO)
say("A8 multi  rec KEYS = %s ; path=%r match=%r tier=%r members=%r"
    % (sorted(multi_rec.keys()), multi_rec.get("path"), multi_rec.get("match"),
       multi_rec.get("tier"), multi_rec.get("members")))

# synthetic multi：match=True / path=None / 无 members（题目要求第三形态确定行为）
multi_forced = {"declared": XHEX, "path": None, "match": True,
                "tier": "SAMEDOC_LINK", "samedoc_link": {"verdict": "multi"}}
say("A9 synthetic multi(match=True,path=None,no members) KEYS = %s"
    % sorted(multi_forced.keys()))

# ================================================================ B. 复跑 _f2v_verify9 :21-29
say()
say("=" * 78)
say("B. _f2v_verify9.py:21-29 在 merged rec 上逐行复跑")
say("=" * 78)
b = merged_rec
say("B0 :21 `if b.get('match') is not True: continue` → match=%r ⇒ 不 continue（进入 :23）"
    % b.get("match"))
src = b.get("alt") or b
say("B1 :23 `src = b.get('alt') or b` → alt=%r，src is b = %s" % (b.get("alt"), src is b))
for label, fn in (
    (":24 Path(src.get('verified_path') or src.get('path'))",
     lambda: Path(src.get("verified_path") or src.get("path"))),
    (":28 b['declared'].lower()                              ", lambda: b["declared"].lower()),
    (":29 size == src['bytes'] (src['bytes'] 求值)          ", lambda: src["bytes"]),
    (":34 src['bytes'] (print 参数求值)                     ", lambda: src["bytes"]),
):
    try:
        r = fn()
        say("B2 %s → OK %r" % (label, r))
    except Exception as e:
        say("B2 %s → %s: %s" % (label, type(e).__name__, e))
say("B3 src.get('verified_path')=%r ; src.get('path')=%r ; src.get('bytes')=%r ; 'bytes' in src=%s"
    % (src.get("verified_path"), src.get("path"), src.get("bytes"), "bytes" in src))

# 独立证明 :29 也崩（绕过 :24，给一个真实在盘文件当 vp）
fake_size = len(MA.read_bytes())
try:
    ok_bytes = fake_size == src["bytes"]
    say("B4 绕过 :24 后 :29 → OK %r" % ok_bytes)
except Exception as e:
    say("B4 绕过 :24 后 :29 → %s: %s" % (type(e).__name__, e))
say("B5 前提错在哪：:24 假定 `match is True ⇒ 必有单一 verified_path/path`；"
    "A1/A4 实测 merged rec match=True、path=None、缺 verified_path/recomputed/bytes，"
    "单对象信息只在 members（2 成员）⇒ 该前提为假。")

# ================================================================ C. 补丁文本校验 + 三形态
say()
say("=" * 78)
say("C. _f2v_verify9 补丁：原文逐字校验 / 语法 / 三种形态 / 缺键 / 真实 30 件回归")
say("=" * 78)
v9src = V9.read_text(encoding="utf-8")
say("C0 BEFORE_V9 逐字包含在原件中 = %s (count=%d)"
    % (BEFORE_V9 in v9src, v9src.count(BEFORE_V9)))
v9patched = v9src.replace(BEFORE_V9, AFTER_V9)
V9CAND = W / "_ms_v9_candidate.py"
V9CAND.write_text(v9patched, encoding="utf-8")
try:
    compile(v9patched, "<_ms_v9_candidate>", "exec")
    say("C1 改后整件 compile() = OK；候选副本已写入 %s" % V9CAND.name)
except Exception as e:
    say("C1 compile FAILED = %s: %s" % (type(e).__name__, e))
DV = diffcount(BEFORE_V9, AFTER_V9, "V9:19-35")

# 用标准模块加载器跑候选副本（真实 30 件），捕获 stdout
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        load("_ms_v9_candidate_run", V9CAND)
    out = buf.getvalue()
    say("C2 改后整件跑真实 30 件 = OK，末行 = %r，MISMATCH 行数 = %d，MATCH 行 = %d"
        % (out.strip().splitlines()[-1], out.count("*** MISMATCH ***"), out.count("MATCH#")))
except Exception as e:
    say("C2 改后整件实跑 FAILED = %s: %s" % (type(e).__name__, e))


def patched_loop(pb, i=0):
    """AFTER_V9 中 :20-35 循环的忠实转录（print → 收集）；用于三形态/缺键注入。"""
    lines = []
    n = 0
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        if b.get("tier") == "SAMEDOC_LINK_EQ" or b.get("members"):
            for m in (b.get("members") or []):
                mp = m.get("path")
                data = Path(mp).read_bytes() if mp else b""
                sha = hashlib.sha256(data).hexdigest()
                size = len(data)
                ok_sha = sha == (b.get("declared") or "").lower()
                ok_bytes = size == m.get("bytes")
                n += 1
                lines.append("MATCH#%d tier=%s member=%s sha_ok=%s bytes_ok=%s"
                             % (n, b.get("tier"), mp, ok_sha, ok_bytes))
            continue
        if not (b.get("alt") or b).get("path"):
            n += 1
            lines.append("SKIP#%d tier=%s 无单一回验路径且无 members" % (n, b.get("tier")))
            continue
        src = b.get("alt") or b
        vp = Path(src.get("verified_path") or src.get("path"))
        data = vp.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        ok_sha = sha == (b.get("declared") or "").lower()
        ok_bytes = size == src.get("bytes")
        n += 1
        lines.append("MATCH#%d tier=%s alt=%s vp=%s sha_ok=%s bytes_ok=%s"
                     % (n, b.get("tier"), bool(b.get("alt")), vp, ok_sha, ok_bytes))
    return lines, n


def orig_loop(pb, i=0):
    """BEFORE_V9 :20-35 忠实转录（用于对照）。"""
    lines = []
    n = 0
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
        lines.append("MATCH#%d %s sha_ok=%s bytes_ok=%s" % (n, vp, ok_sha, ok_bytes))
    return lines, n


cases = [
    ("unique (有 path)", [uniq_rec]),
    ("merged (无 path 有 members)", [merged_rec]),
    ("multi 真 rec (match=None)", [multi_rec]),
    ("multi 合成 (match=True, 无 path 无 members)", [multi_forced]),
    ("merged 缺 members[0].bytes", [{**merged_rec, "members": [{"path": str(MA), "sha": MHEX}]}]),
    ("merged members=None", [{**merged_rec, "members": None}]),
    ("unique 缺 bytes", [{k: v for k, v in uniq_rec.items() if k != "bytes"}]),
]
for name, pb in cases:
    try:
        o_l, o_n = orig_loop(pb)
        o = "原版 OK n=%d %s" % (o_n, o_l[:1])
    except Exception as e:
        o = "原版 %s: %s" % (type(e).__name__, e)
    try:
        p_l, p_n = patched_loop(pb)
        p = "改后 OK n=%d %s" % (p_n, p_l[:2])
    except Exception as e:
        p = "改后 %s: %s" % (type(e).__name__, e)
    say("C3 %-42s | %s || %s" % (name, o, p))

# ================================================================ D. _g9_gate :155-166 判定链
say()
say("=" * 78)
say("D. _g9_gate.py:155-166 判定链 + 反例（旧门禁 PASS / 新门禁 FAIL）")
say("=" * 78)

text = DELIVERABLE.read_text(encoding="utf-8")
rp, rw, rb = G7.r11_scan(text, FIX, root=REPO)
say("D0 真实 g7.r11_scan(反例交付件): problems=%r warnings=%r bindings=%s"
    % (rp, rw, [{k: b.get(k) for k in ("declared", "path", "match")} for b in rb]))
say("D1 r11_scan 是否产 merged rec = %s （r11_scan 不调 link 家族；:155 实读为 g7.r11_scan）"
    % any(b.get("tier") == "SAMEDOC_LINK_EQ" for b in rb))


def chain(bindings, problems, patched=False):
    n_reverified = sum(1 for b in bindings if b.get("path"))
    n_match = sum(1 for b in bindings if b.get("match") is True)
    r11_items = 1 + len(bindings)
    probs = list(problems)
    n_unverified = len(bindings) - n_reverified
    n_match_no_path = sum(1 for b in bindings
                          if b.get("match") is True and not b.get("path"))
    if patched and n_match_no_path:
        probs.append("R11 回验缺口：%d 条 match=True 无单一回验路径" % n_match_no_path)
    verdict = "FAIL" if probs else "PASS"
    return dict(n_bindings=len(bindings), items=r11_items, reverified=n_reverified,
                match_true=n_match, n_unverified=n_unverified,
                problems=probs, verdict=verdict)

say("D2 :157-160 今日实际链（r11_scan 输出） 旧 = %s" % json.dumps(chain(rb, rp), ensure_ascii=False))
say("D3 :157-160 今日实际链（r11_scan 输出） 新 = %s"
    % json.dumps(chain(rb, rp, patched=True), ensure_ascii=False))
say("D4 :157-160 假设注入真 merged rec 时 旧 = %s"
    % json.dumps(chain([merged_rec], [], patched=False), ensure_ascii=False))
say("D5 :157-160 假设注入真 merged rec 时 新 = %s"
    % json.dumps(chain([merged_rec], [], patched=True), ensure_ascii=False))

# 真门禁：原件 vs 候选副本
say()
say("D6 真 check_deliverable 实跑（原件不改；候选副本写入写域后用模块加载器载入）")
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

g9src = G9.read_text(encoding="utf-8")
say("D6.0 BEFORE_G9 逐字包含在原件中 = %s (count=%d)"
    % (BEFORE_G9 in g9src, g9src.count(BEFORE_G9)))
g9patched_src = g9src.replace(BEFORE_G9, AFTER_G9)
G9CAND = W / "_ms_g9_candidate.py"
G9CAND.write_text(g9patched_src, encoding="utf-8")
try:
    compile(g9patched_src, "<_ms_g9_candidate>", "exec")
    say("D6.1 改后整件 compile() = OK；候选副本已写入 %s" % G9CAND.name)
except Exception as e:
    say("D6.1 compile FAILED = %s: %s" % (type(e).__name__, e))
DG = diffcount(BEFORE_G9, AFTER_G9, "G9:155-167")

OLD = load("_ms_g9_old", G9)
NEWMOD = load("_ms_g9_candidate_run", G9CAND)
NEW = NEWMOD.check_deliverable

r_old = OLD.check_deliverable(DELIVERABLE, REQ, FORB, root=REPO, doc_dir=FIX)
r_new = NEW(DELIVERABLE, REQ, FORB, root=REPO, doc_dir=FIX)
for tag, r in (("OLD", r_old), ("NEW", r_new)):
    R11 = r["predicates"]["R11"]
    say("D6.2 %s verdict=%s | R9=%s R10=%s R12=%s R11=%s | R11 reverified=%d match_true=%d problems=%s"
        % (tag, r["verdict"],
           r["predicates"]["R9"]["verdict"], r["predicates"]["R10"]["verdict"],
           r["predicates"]["R12"]["verdict"], R11["verdict"],
           R11["reverified"], R11["match_true"], R11["problems"]))

keys_old = sorted(r_old.keys())
keys_new = sorted(r_new.keys())
r11_old = sorted(r_old["predicates"]["R11"].keys())
r11_new = sorted(r_new["predicates"]["R11"].keys())
say("D6.3 返回结构 top keys 相同 = %s %s" % (keys_old == keys_new, keys_new))
say("D6.4 返回结构 R11 keys 相同 = %s %s" % (r11_old == r11_new, r11_new))
say("D6.5 两结果均 JSON 可序列化 = %s" % (
    isinstance(json.dumps(r_old, ensure_ascii=False), str)
    and isinstance(json.dumps(r_new, ensure_ascii=False), str)))

# 注入 merged rec（模拟将来门禁改接 plus）：证明 match=True/path=None 不得 PASS
def fake_r11(text_, doc_dir, root=None, recompute=None):
    return [], ["绑定行缺显式路径（merged 副本群）"], [dict(merged_rec)]


OLD.g7.r11_scan = fake_r11
NEWMOD.g7.r11_scan = fake_r11
i_old = OLD.check_deliverable(DELIVERABLE, REQ, FORB, root=REPO, doc_dir=FIX)
i_new = NEW(DELIVERABLE, REQ, FORB, root=REPO, doc_dir=FIX)
say("D6.6 注入真 merged rec：OLD R11=%s verdict=%s reverified=%d match_true=%d problems=%s"
    % (i_old["predicates"]["R11"]["verdict"], i_old["verdict"],
       i_old["predicates"]["R11"]["reverified"], i_old["predicates"]["R11"]["match_true"],
       i_old["predicates"]["R11"]["problems"]))
say("D6.7 注入真 merged rec：NEW R11=%s verdict=%s reverified=%d match_true=%d problems=%s"
    % (i_new["predicates"]["R11"]["verdict"], i_new["verdict"],
       i_new["predicates"]["R11"]["reverified"], i_new["predicates"]["R11"]["match_true"],
       i_new["predicates"]["R11"]["problems"]))

# self_test 回归（候选副本模块）
try:
    checks, allpass = NEWMOD.self_test()
    say("D6.8 改后 self_test() all_pass=%s checks=%s"
        % (allpass, [(c["id"], c["ok"]) for c in checks]))
except Exception as e:
    say("D6.8 改后 self_test FAILED = %s: %s" % (type(e).__name__, e))

# ================================================================ E. 静默误读簇复跑
say()
say("=" * 78)
say("E. 六件「静默误读」消费方在 merged rec 上的实跑（不崩但结论错）")
say("=" * 78)
r = merged_rec
sha_ok = (r.get("recomputed") or "").lower() == r["declared"].lower()
say("E1 _f2w_checks.py:29  sha_ok = %r  ← 合法 match=True 被记成「sha 逐字不一致」" % sha_ok)
say("E2 _f2_selftest.py:110 endswith('_f2_r11plus.py') = %r  ← S4 断言失败" % (
    r.get("verified_path", "").endswith("_f2_r11plus.py")))
plus_path = sum(1 for b in [r] if b.get("path"))
plus_match = sum(1 for b in [r] if b.get("match") is True)
say("E3 _f2_compare.py:67,69  (plus_path, plus_match) = (%d, %d)  ← 计数口径混杂" % (plus_path, plus_match))
collected = sum(1 for b in [r] if b.get("path"))
tiers = {}
for b in [r]:
    if b.get("match") is True:
        tiers[b.get("tier")] = tiers.get(b.get("tier"), 0) + 1
say("E4 _f2v_final.py:54,57-58  collected=%d tiers=%s  ← 开放 dict 不崩、结论错" % (collected, tiers))
say("E5 _f2v_run.py:48-52  plus_paths=%r plus_match=%r plus_tiers=%r" % (
    [b.get("path") for b in [r]], [b.get("match") for b in [r]], [b.get("tier") for b in [r]]))
say("E6 _f2w_dogfood.py:25-30  collected=%d match=%d tiers=%s" % (collected, plus_match, tiers))
say("E7 _f2w_pass.py:15,17  plus match 计数 = %d  ← merged 混入单一回验 PASS 统计" % plus_match)
vp = r.get("verified_path", "") or ""
rc = r.get("recomputed", "") or ""
say("E8 _f2w_extract.py:26-33  verified=%r recomputed=%r bytes=%r  ← 报告静默空白"
    % (vp, (rc[:16] + "...") if rc else "-", r.get("bytes", "-")))

# ================================================================ F. 指纹复核
say()
say("=" * 78)
say("F. 本会话实算指纹（hashlib，与编排方派发值比对）")
say("=" * 78)
EXPECT = {
    "lead/r11_f2_fix_20261109/_f2v_verify9.py":
        ("c22f28ad4228d028c16d8558a8dd9a0980947631ab5bcf5c9cd84e529cf439e3", 1618),
    "lead/gate_r9r12_20261109/_g9_gate.py":
        ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/gate_fp7_20261108/_g7_predicates.py":
        ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/r33e_merge_20261109/_re_linked.py":
        ("7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    "lead/merged_consumer_audit_20261109/_mc_AUDIT.md":
        ("8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367", 33762),
    "lead/merged_consumer_audit_20261109/MERGED_CONSUMER_AUDIT.md":
        ("85de273758a6b87915f9735a07e1b9e1d11c594de50f41d83f5e70145257c263", 40884),
    "lead/PENDING_DECISIONS.md":
        ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md":
        ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
allok = True
for rel, (eh, eb) in EXPECT.items():
    raw = (REPO / rel.replace("/", "\\")).read_bytes()
    h, n = hashlib.sha256(raw).hexdigest(), len(raw)
    ok = (h == eh and n == eb)
    allok &= ok
    say("F %s sha256=%s bytes=%d MATCH=%s" % (rel, h, n, ok))
say("F9 ALL_EIGHT_MATCH = %s" % allok)

(W / "_ms_probe_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_ms_probe_out.txt"))
