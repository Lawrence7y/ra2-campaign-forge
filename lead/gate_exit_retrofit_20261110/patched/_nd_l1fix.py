# -*- coding: utf-8 -*-
"""_nd_l1fix.py — 修正后的 L1 原型（应当怎么改；不改任何既有件）。

修正点（基于复核 verdict=partial 的 V4/V5 误合并 + 哨兵冲突）：
1. 归一字母表严格对齐 _rs_carrier_scan.py:79 的 PAIRS：只认 「」『』``“”。
   未收录的 ‘’ / 半错配 『」 不进归一键；原文 span 无效者报 UNKNOWN。
2. 召回后强制在原始行上复验「命中片段的成对包裹符有效 + 可与 R5 PAIRS 对应」；
   不复验就并入 canon 身份 = 把不同意思的句子当成同一句。
3. 哨兵改用 PUA（\ue000/\ue001/\ue002），且逐行预检「原文不得含哨兵码位」；
   本会话实跑语料含 U+0001（ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:3465）。
4. 1:1 保长、位置可回溯；归一串只作召回键，绝不写入台账或作「同一句」证据。
"""
import os, re, importlib.util, sys

ROOT = r"D:/Project/ra2-campaign-forge/lead"
SCAN = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
CANON = "只能判「不可复现」"
PAIRS = [("「", "」"), ("『", "』"), ("`", "`"), ("“", "”")]
LQ, RQ, SQ = "\ue000", "\ue001", "\ue002"          # PUA private sentinels
SENTINELS = {LQ, RQ, SQ}

def norm(s):
    """1:1 保长；只归一 PAIRS 收录的引号类字符。其它码位（含 ‘’ 及哨兵）原样。
    反引号是 PAIRS 的对称对：按出现次序交替映射为 LQ/RQ，仍保持 1:1 保长。"""
    out, tick = [], 0
    for c in s:
        if c in "「『“": out.append(LQ)
        elif c in "」』”": out.append(RQ)
        elif c == "`":
            out.append(LQ if tick % 2 == 0 else RQ)
            tick += 1
        else: out.append(c)
    return "".join(out)

QN = norm(CANON)

def find_norm_candidates(line):
    """返回 [(orig_start, orig_end, raw_text, status)]。
    status=OK 仅当原文片段的首尾包裹符构成 PAIRS 中合法成对跨度。
    """
    if SENTINELS & set(line):
        return []                                   # 哨兵冲突：不猜，交人工
    n = norm(line)
    res, pos = [], 0
    while True:
        k = n.find(QN, pos)
        if k < 0: break
        a, b = k, k + len(QN)
        raw = line[a:b]
        # 复验：原文片段的包裹符必须是 PAIRS 认可的成对引号，
        # 且 R5 在该行的引号跨度恰为「命中片段内层」(a+3,b)（防止整句引文里的子串被当独立引文）。
        exact = (len(raw) >= 3 and (raw[3], raw[-1]) in PAIRS
                 and any((x, y) == (a + 3, b) for x, y, _ in mod.spans_of_quotes(line)))
        res.append((a, b, raw, "OK" if exact else "UNKNOWN"))
        pos = k + 1
    return res

spec = importlib.util.spec_from_file_location("_rs_mod2", SCAN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CASES = [
    ("canon angle",     "只能判「不可复现」", "OK"),
    ("curly corner",    "只能判『不可复现』", "OK"),
    ("curly double",    "只能判“不可复现”", "OK"),
    ("V4 mismatched",   "只能判『不可复现」", "UNKNOWN"),
    ("V5 single curly", "只能判‘不可复现’", "NOT-RECALLED"),
    ("V1 different word","只能判「不可复原」", "NOT-RECALLED"),
    ("V3 no quote",     "只能判不可复现", "NOT-RECALLED"),
    ("backtick pair",   "只能判`不可复现`", "OK"),
    ("inverted",        "只能判』不可复现『", "NOT-RECALLED"),
]
print("=== corrected L1 fixture ===")
print("canon key =", repr(QN))
print("PAIRS =", PAIRS)
allpass = True
for nm, s, expect in CASES:
    hits = find_norm_candidates(s)
    got = hits[0][3] if hits else "NOT-RECALLED"
    ok = (got == expect)
    allpass &= ok
    print("  %-5s %-18s %-42r -> %-14s expect=%-14s spans=%s" % (
        "PASS" if ok else "FAIL", nm, s, got, expect, mod.spans_of_quotes(s)))
print("FIXTURE_SELF_TEST =", "PASS" if allpass else "FAIL")

# corpus: corrected L1 on all (excl write domain), compare with three quote variants
V3 = ("只能判「不可复现」", "只能判『不可复现』", "只能判“不可复现”")
truth, rec, mapped, bad = set(), set(), 0, 0
sentinel_files = []
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace(os.sep, "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []
        continue
    for f in sorted(fn):
        if not f.lower().endswith(".md"):
            continue
        p = os.path.join(dp, f)
        r = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if r.startswith("needle_norm_20261109/"):
            continue
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        ls = b.decode("utf-8", "replace").splitlines()
        for i, L in enumerate(ls, 1):
            if SENTINELS & set(L):
                sentinel_files.append((r, i))
            if any(v in L for v in V3):
                truth.add((r, i))
            for (a, e, raw, status) in find_norm_candidates(L):
                mapped += 1
                if raw != L[a:e] or norm(raw) != QN:
                    bad += 1
                if status == "OK":
                    rec.add((r, i))
print("=== corpus check ===")
print("PUA sentinel collision lines =", len(sentinel_files), sentinel_files[:3])
print("three quote-variant truth: lines=%d files=%d" % (len(truth), len({r for r, i in truth})))
print("corrected L1 OK:          lines=%d files=%d" % (len(rec), len({r for r, i in rec})))
print("L1 == truth ? %s ; FP=%d FN=%d" % (rec == truth, len(rec - truth), len(truth - rec)))
print("mapped hits=%d ; orig_slice/norm bad=%d" % (mapped, bad))
# ---------- 出口追加（只追加；以上 123 行原件逐字未改）----------
# 原件对自身的检查结果全部走 print（无写盘、无 assert、无显式出口）：
#   :84  FIXTURE_SELF_TEST = PASS/FAIL —— :76-81 的 allpass 合取 9 条 fixture
#   :119 PUA sentinel collision lines = 0（哨兵冲突数须为 0）
#   :122 L1 == truth ? True ; FP=0 FN=0（召回集合须等于真值集合）
#   :123 mapped hits / orig_slice/norm bad = 0（位置回溯坏项须为 0）
# 出口只把这些既有结果合取成一个布尔，不改任何既有 print、不改任何既有判定。
# 约束 C1/C2/C3：纯追加、库本体/import 不动、不新增全局名字（ok 原件 :80 已有）。
ok = True
ok = ok and bool(allpass)
ok = ok and bool(len(sentinel_files) == 0)
ok = ok and bool(rec == truth)
ok = ok and bool(bad == 0)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
