# -*- coding: utf-8 -*-
# _cv_diff_20261108.py — 独立解析 CANDIDATE_LF.diff：hunk 计数、头对照 B2B§7/V2§3.1、自实现 hunk 回放判定候选=母本+九hunk、difflib 全量重算、E 块检查（只读）
import re, difflib

BASE = "D:/Project/ra2-campaign-forge/"
MASTER = BASE + "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND   = BASE + "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DIFF   = BASE + "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
B2B    = BASE + "lead/b2b_design_20261106/B2B_DESIGN.md"
V2     = BASE + "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"

mlines = open(MASTER, "rb").read().decode("utf-8").split("\n")
clines = open(CAND, "rb").read().decode("utf-8").split("\n")
dtext  = open(DIFF, "rb").read().decode("utf-8")
dlines = dtext.split("\n")

print("master lines:", len(mlines), "cand lines:", len(clines))

hdr = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
hunks = []
cur = None
for i, L in enumerate(dlines, 1):
    m = hdr.match(L)
    if m:
        cur = {"h": L, "idx": i,
               "a": int(m.group(1)), "b": int(m.group(2)) if m.group(2) is not None else 1,
               "c": int(m.group(3)), "d": int(m.group(4)) if m.group(4) is not None else 1,
               "lines": []}
        hunks.append(cur)
    elif cur is not None and (L.startswith(" ") or L.startswith("+") or L.startswith("-") or L == ""):
        cur["lines"].append(L)
    elif L.startswith("---") or L.startswith("+++"):
        continue
    else:
        cur = None

print("== hunk count:", len(hunks), "==")
plus = minus = 0
for h in hunks:
    p = sum(1 for L in h["lines"] if L.startswith("+"))
    q = sum(1 for L in h["lines"] if L.startswith("-"))
    plus += p; minus += q
    print("  diff:%3d  %s   old %d-%d  (+%d/-%d)" % (h["idx"], h["h"], h["a"], h["a"] + h["b"] - 1, p, q))
print("total + %d / - %d / net %+d" % (plus, minus, plus - minus))

print("== E 判据块 5984-5990 交叠检查 ==")
E = set(range(5984, 5991))
ov = [h["h"] for h in hunks if set(range(h["a"], h["a"] + h["b"])) & E]
print("  hunks overlapping E block:", ov if ov else "无")

print("== hunk 回放（自实现 unified-diff apply，判定 patched==candidate） ==")
errs = []
out = []
pos = 0
for h in hunks:
    a, b = h["a"], h["b"]
    if a - 1 < pos:
        errs.append(("overlap", h["h"])); continue
    out.extend(mlines[pos:a - 1])
    seg = mlines[a - 1:a - 1 + b]
    si = 0
    for L in h["lines"]:
        tag, body = L[:1], L[1:]
        if tag == " " or L == "":
            if si < len(seg) and seg[si] == body:
                out.append(body); si += 1
            else:
                errs.append(("ctx", h["h"], si, body[:60], seg[si][:60] if si < len(seg) else "<EOF>"))
        elif tag == "-":
            if si < len(seg) and seg[si] == body:
                si += 1
            else:
                errs.append(("del", h["h"], si, body[:60], seg[si][:60] if si < len(seg) else "<EOF>"))
        elif tag == "+":
            out.append(body)
    if si != len(seg):
        errs.append(("unconsumed", h["h"], si, len(seg)))
    pos = a - 1 + b
out.extend(mlines[pos:])
print("  patched==candidate:", out == clines, " patched lines:", len(out))
for e in errs[:20]:
    print("  ERR:", e)

print("== difflib 全量重算（autojunk=False） ==")
sm = difflib.SequenceMatcher(None, mlines, clines, autojunk=False)
ops = sm.get_opcodes()
blocks = []
de = ad = 0
for tag, i1, i2, j1, j2 in ops:
    if tag != "equal":
        blocks.append((tag, i1, i2, j1, j2))
        if tag in ("delete", "replace"): de += i2 - i1
        if tag in ("insert", "replace"): ad += j2 - j1
print("  change blocks:", len(blocks), "deleted:", de, "added:", ad, "net:", ad - de)
allowed = [(h["a"], h["a"] + h["b"] - 1) for h in hunks]
outside = []
for tag, i1, i2, j1, j2 in blocks:
    if tag == "insert":
        p = i1  # 插在 0 基 i1 之前 = 1 基行 i1 与 i1+1 之间
        hit = any(A - 1 <= p <= B for (A, B) in allowed)
        print("  insert @master0b%d -> in-range=%s (+%d)" % (p, hit, j2 - j1))
        if not hit: outside.append((tag, i1, i2))
    else:
        S, Ee = i1 + 1, i2  # 1 基含端
        hit = any(A <= S and Ee <= B for (A, B) in allowed)
        print("  %-7s master %d-%d cand %d-%d -> in-range=%s (-%d/+%d)" % (tag, S, Ee, j1 + 1, j2, hit, i2 - i1, j2 - j1))
        if not hit: outside.append((tag, i1, i2))
print("  blocks NOT in any hunk old-range:", outside if outside else "无（未归入块数=0）")
# E 块 5984-5990 是否全等
ebad = [ (tag,i1,i2) for tag,i1,i2,j1,j2 in ops if tag!="equal" and i1 < 5990 and i2 > 5983 ]
print("  change ops touching master 5984-5990:", ebad if ebad else "无")

print("== hunk 头与 B2B§7 / V2§3.1 表逐字对照 ==")
hpat = re.compile(r"`(-\d+,\d+ \+\d+,\d+)`")
def table_headers(path, lo, hi):
    t = open(path, "rb").read().decode("utf-8").split("\n")
    hs = []
    for i, L in enumerate(t, 1):
        if lo <= i <= hi:
            for m2 in hpat.finditer(L):
                hs.append((i, m2.group(1)))
    return hs
b2b_h = table_headers(B2B, 655, 675)
v2_h  = table_headers(V2, 75, 95)
diff_h = [h["h"].split("@@")[1].strip() for h in hunks]
print("  B2B§7 headers:", b2b_h)
print("  V2§3.1 headers:", v2_h)
print("  diff headers: ", diff_h)
print("  diff==B2B order:", diff_h == [x[1] for x in b2b_h], " diff==V2 order:", diff_h == [x[1] for x in v2_h])

print("== `+` 行禁词扫描（甲残留/禁符号/退出码符号/n-a） ==")
pl = [L[1:] for L in dlines if L.startswith("+") and not L.startswith("+++")]
print("  + lines:", len(pl))
for tok in ("n/a", "N/A", "B2_FIX_DESIGN", "absent_both, n/a", "note_cleanup_failure", "EXIT_",
            "except_set_diff", "no_new_exception", "CLEANUP_FAILURES",
            "MiniDumpWriteDump", "ReadProcessMemory", "OpenProcess", "SuspendThread",
            "WriteProcessMemory", "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHookEx",
            "TerminateProcess", "StackWalk", "os.system", "ctypes", "gamemd", "ra2loader", "taskkill", "YURI"):
    hits = [L.strip()[:110] for L in pl if tok in L]
    if hits:
        print("  TOKEN %r in + lines x%d:" % (tok, len(hits)))
        for x in hits: print("      ", x)
    else:
        print("  TOKEN %r in + lines: 0" % tok)
