# -*- coding: utf-8 -*-
"""_se_enum.py — STRICT 口径暴露面评估：两口径 81 格独立重算（不采信上一轮数字）。

纪律：零真机 / 零采样 / 只读被核件 / 唯一写域 = 本目录 / 不 commit 不 push。
方法：
  1) hashlib 复核候选与乙矩阵指纹（与编排方基线比对）；
  2) 顶层 AST 副作用扫描（登记顶层 Call 与 __main__ 守卫）；
  3) importlib spec_from_file_location 静态装载候选真模块，直调真
     classify_except_freshness（非 AST 复刻、非硬编码路由）跑 9 pre × 9 post = 81 格；
  4) 交叉核对：81 格实码三元 vs 耦合件 MATRIX_ROW5_COUPLING.md §4.1a 全格表；
  5) claimant 覆盖谓词 = 本轮独立手编（依据 = STATE_MATRIX.json 各行 condition 原文逐字；
     STRICT 口径定义 = 耦合件 :67「匹配键 = preState 字段 + condition 前件」合取纪律；
     LOOSE 口径定义 = RULING_MATRIX_AB.md:42(ii)「condition 文本承载路由、preState 列为
     登记示例态」；LOOSE 的 :2 宽键读法依据 = 耦合件 :112「宽 preState 键读法下 :2/:3 兜住」）；
  6) 裁决规则（与上轮同基以便可比）：无 claimant ⇒ ORPHAN；全部 claimant 三元 == 实码三元
     （verdict/conf/usable；JSON 无 is_new 字段，实码 is_new 不入比较）⇒ OK；否则 MISLABEL；
     另报 first-match-wins 敏感性变体；
  7) 实流可达域标注：REAL_PRE × REAL_POST（依据 make_pre/copy_post 输出域实读），对每个
     暴露格标注 可达-实跑 / 可达-结构未单跑 / 不可达（附控制流依据的出处见报告）。
"""
import ast
import hashlib
import importlib.util
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge"
CAND = os.path.join(BASE, "lead", "b2b_candidate_lf_20261107", "qc151_trip.candidate_lf.py")
MATRIX = os.path.join(BASE, "lead", "b2b_design_20261106", "STATE_MATRIX.json")
EXP_CAND = ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759)
EXP_MATRIX = ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558)

print("== F0 fingerprints (hashlib, read-only) ==")
ok_all = True
for name, p, exp in (("candidate", CAND, EXP_CAND), ("matrix", MATRIX, EXP_MATRIX)):
    b = open(p, "rb").read()
    h, n = hashlib.sha256(b).hexdigest(), len(b)
    ok = (h, n) == exp
    ok_all = ok_all and ok
    print("  %s  %s  %d  %s" % (name, h, n, "MATCH" if ok else "MISMATCH"))
print("F0", "ALL_MATCH" if ok_all else "MISMATCH")

rows = json.loads(open(MATRIX, encoding="utf-8").read())
assert len(rows) == 14, len(rows)

def rowvals(line):  # 文件行 2..15
    r = rows[line - 2]
    return (r["verdict"], r["confidence"], r["usableAsCrashEvidence"])

print("== F1 AST top-level scan (import safety 登记项) ==")
src = open(CAND, encoding="utf-8").read()
tree = ast.parse(src)
calls = [n.lineno for n in tree.body if isinstance(n, ast.Call)]
guards = [n.lineno for n in tree.body
          if isinstance(n, ast.If) and "__main__" in ast.unparse(n.test)]
print("  top-level Call nodes (lineno):", calls)
print("  __main__ guard If nodes (lineno):", guards)

print("== F2 import real candidate module ==")
spec = importlib.util.spec_from_file_location("qc151_cand_se", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
classify = mod.classify_except_freshness
print("  import ok; FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES)
print("  classify qualname =", classify.__qualname__)

PRE_KINDS = ["none", "empty", "missing", "dirty", "expl_unknown",
             "absent", "present_sha", "present_nosh", "error"]

def mk_pre(k):
    if k == "none":
        return None
    if k == "empty":
        return {}
    if k == "missing":
        return {"size": 123}                                    # 缺 state
    if k == "dirty":
        return {"state": "garbage", "size": 123}                # 脏值
    if k == "expl_unknown":
        return {"state": "unknown", "exists": None}
    if k == "absent":
        return {"state": "absent_confirmed", "exists": False}
    if k == "present_sha":
        return {"state": "present", "exists": True, "sha256": "D" * 64, "mtime_pre": 111.0}
    if k == "present_nosh":
        return {"state": "present", "exists": True, "sha256": None, "mtime_pre": 111.0}
    if k == "error":
        return {"state": "error", "error": "OSError: probe"}
    raise AssertionError(k)

POST_KINDS = ["re_none", "re_true", "nofile", "no_post_sha",
              "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing"]

def mk_post(k):
    b = {"exists": None, "size": None, "sha256": None, "mtime_post": None, "read_error": None}
    if k == "re_none":
        b["read_error"] = "OSError: probe read fail"            # 读/统计失败：exists 停在 None
    elif k == "re_true":
        b.update({"exists": True, "size": 5, "sha256": "E" * 64, "mtime_post": 222.0,
                  "read_error": "OSError: probe write fail"})   # 写副本失败：:4769 先置 exists=True
    elif k == "nofile":
        b["exists"] = False
    elif k == "no_post_sha":
        b.update({"exists": True, "size": 5, "mtime_post": 222.0})
    elif k == "sha_diff":
        b.update({"exists": True, "sha256": "E" * 64, "mtime_post": 222.0})
    elif k == "mt_same":
        b.update({"exists": True, "sha256": "D" * 64, "mtime_post": 111.0})
    elif k == "mt_up":
        b.update({"exists": True, "sha256": "D" * 64, "mtime_post": 222.0})
    elif k == "mt_down":
        b.update({"exists": True, "sha256": "D" * 64, "mtime_post": 55.0})
    elif k == "mt_missing":
        b.update({"exists": True, "sha256": "D" * 64, "mtime_post": None})
    return b

def actual(pk, qk):
    r = classify(mk_pre(pk), mk_post(qk))
    return (r["verdict"], r["confidence"], r["is_new"],
            r["usable_as_crash_evidence"], r["pre_snapshot_state"])

# ---- F3 交叉核对：耦合件 §4.1a 全格表（verdict·conf·is_new；9 类 pre × 9 类 post）----
PRE, UNK, NFA, AB, VAN = ("post_read_error", "unknown", "new_first_appearance",
                          "absent_both", "vanished")
NW, LU, RW, EPS = ("new_write", "leftover_unchanged", "rewritten_same_content",
                   "error_pre_snapshot")
EXPECT = {}

def setexp(prekinds, qk, v, c, n):
    for pk in prekinds:
        EXPECT[(pk, qk)] = (v, c, n)

UNC = ["none", "empty", "missing", "dirty"]
for qk in POST_KINDS:
    if qk in ("re_none", "re_true"):
        setexp(UNC + ["expl_unknown"], qk, PRE, "none", None)
    else:
        setexp(UNC + ["expl_unknown"], qk, UNK, "none", None)
setexp(["absent"], "re_none", PRE, "none", None)
setexp(["absent"], "re_true", PRE, "none", None)
setexp(["absent"], "nofile", AB, "low", False)
for qk in ("no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing"):
    setexp(["absent"], qk, NFA, "high", True)
setexp(["present_sha"], "re_none", PRE, "none", None)
setexp(["present_sha"], "re_true", PRE, "none", None)
setexp(["present_sha"], "nofile", VAN, "none", None)
setexp(["present_sha"], "no_post_sha", PRE, "none", None)
setexp(["present_sha"], "sha_diff", NW, "high", True)
setexp(["present_sha"], "mt_same", LU, "high", False)
setexp(["present_sha"], "mt_up", RW, "medium", True)
setexp(["present_sha"], "mt_down", RW, "low", True)
setexp(["present_sha"], "mt_missing", LU, "medium", False)
setexp(["present_nosh"], "re_none", PRE, "none", None)
setexp(["present_nosh"], "re_true", PRE, "none", None)
setexp(["present_nosh"], "nofile", VAN, "none", None)
for qk in ("no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing"):
    setexp(["present_nosh"], qk, EPS, "none", None)
for qk in POST_KINDS:
    if qk in ("re_none", "re_true"):
        setexp(["error"], qk, PRE, "none", None)
    else:
        setexp(["error"], qk, EPS, "none", None)

print("== F3 crosscheck vs 耦合件 §4.1a（81 格 verdict·conf·is_new）==")
bad = 0
grid = {}
for pk in PRE_KINDS:
    for qk in POST_KINDS:
        a = actual(pk, qk)
        grid[(pk, qk)] = a
        e = EXPECT[(pk, qk)]
        if (a[0], a[1], a[2]) != e:
            bad += 1
            print("  XCHECK-FAIL %s x %s actual=%s expect=%s" % (pk, qk, a[:3], e))
print("  XCHECK %s (%d mismatch / 81)" % ("ALL_PASS" if bad == 0 else "FAIL", bad))

# ---- F4 claimant 覆盖谓词（本轮独立手编；依据 = 各行 condition 原文）----
UNCOLLECTED = ["none", "empty", "missing", "dirty"]       # :2 condition 逐字枚举的四种未采集形态
RE_KINDS = ["re_none", "re_true"]                          # read_error 两型（copy_post :4786 唯一写点）
# 「跑后在 / 在场（存在性硬证）」按字面 = exists=True 全形态；re_true 因 :4769 先置 exists=True
# 后 :4772 才可失败而属字面在场（:4773-4790 except 只增 read_error 键，不触 exists）。
ET_COVER = ["no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing", "re_true"]

def prestate(pk):
    # classify :4637-4639 归一口：∉ FRESHNESS_SNAPSHOT_STATES ⇒ unknown
    return {"none": "unknown", "empty": "unknown", "missing": "unknown", "dirty": "unknown",
            "expl_unknown": "unknown", "absent": "absent_confirmed",
            "present_sha": "present", "present_nosh": "present", "error": "error"}[pk]

def cov(line, pk, qk, strict):
    # STRICT = preState 字段 ∧ condition 前件（耦合件 :67 合取键）
    # LOOSE  = condition 文本承载路由、preState 列为登记示例态（裁决 :42(ii)；
    #          :2 的宽键读法（含显式 unknown）依据 = 耦合件 :112）
    u = prestate(pk)
    if line == 2:
        return (pk in UNCOLLECTED) if strict else (u == "unknown")   # 「跑后任意文件状态」= post 任意
    if line == 3:
        return (pk == "expl_unknown") and (qk == "nofile")           # 「显式 unknown + 跑后无件」
    if line == 4:
        return (pk == "error")                                       # 「snap.error 非空」无跑后限定
    if line == 5:
        if strict:
            return (u == "present") and (qk in RE_KINDS)             # preState=present 合取独占
        return qk in RE_KINDS                                        # condition 无 pre 限定 ⇒ 任意 pre
    if line == 6:
        return (pk == "absent") and (qk in ET_COVER)                 # 「跑后在场（存在性硬证）」字面
    if line == 7:
        return (pk == "absent") and (qk == "nofile")
    if line == 8:
        return (pk == "present_sha") and (qk == "mt_same")
    if line == 9:
        return (pk == "present_sha") and (qk == "mt_missing")
    if line == 10:
        return (pk == "present_sha") and (qk == "sha_diff")
    if line == 11:
        return (pk == "present_sha") and (qk == "mt_up")
    if line == 12:
        return (pk == "present_sha") and (qk == "mt_down")
    if line == 13:
        return (pk == "present_nosh") and (qk in ET_COVER)           # 「跑前在+跑后在+缺 pre.sha256」
    if line == 14:
        return (pk == "present_sha") and (qk == "no_post_sha")       # 码序残差：present_nosh 已被 :13 先截
    if line == 15:
        return (u == "present") and (qk == "nofile")
    raise AssertionError(line)

def claimants(pk, qk, strict):
    return [i for i in range(2, 16) if cov(i, pk, qk, strict)]

def survey(strict):
    ok_n, mis, orph = 0, [], []
    for pk in PRE_KINDS:
        for qk in POST_KINDS:
            a = grid[(pk, qk)]
            act3 = (a[0], a[1], a[3])          # verdict / conf / usable（JSON 无 is_new 字段）
            cands = claimants(pk, qk, strict)
            if not cands:
                orph.append((pk, qk, act3))
            elif all(rowvals(i) == act3 for i in cands):
                ok_n += 1
            else:
                badr = [i for i in cands if rowvals(i) != act3]
                mis.append((pk, qk, act3, cands, badr, [rowvals(i) for i in badr]))
    return ok_n, mis, orph

def survey_firstmatch(strict):
    ok_n, mis, orph = 0, [], []
    for pk in PRE_KINDS:
        for qk in POST_KINDS:
            a = grid[(pk, qk)]
            act3 = (a[0], a[1], a[3])
            cands = claimants(pk, qk, strict)
            if not cands:
                orph.append((pk, qk, act3))
            elif rowvals(cands[0]) == act3:
                ok_n += 1
            else:
                mis.append((pk, qk, act3, cands, [cands[0]], [rowvals(cands[0])]))
    return ok_n, mis, orph

print("== M1 baseline survey（裁决规则：全部 claimant 须与实码一致）==")
s_ok, s_mis, s_orph = survey(True)
l_ok, l_mis, l_orph = survey(False)
print("  [BASELINE-STRICT] OK=%d MISLABEL=%d ORPHAN=%d (81 cells)" % (s_ok, len(s_mis), len(s_orph)))
for pk, qk, act3, cands, badr, badv in s_mis:
    print("    MISLABEL %s x %s -> actual=%s ; claimants=%s values=%s ; bad=%s" %
          (pk, qk, list(act3), cands, badv, badr))
for pk, qk, act3 in s_orph:
    print("    ORPHAN   %s x %s -> actual=%s" % (pk, qk, list(act3)))
print("  [BASELINE-LOOSE ] OK=%d MISLABEL=%d ORPHAN=%d (81 cells)" % (l_ok, len(l_mis), len(l_orph)))
for pk, qk, act3, cands, badr, badv in l_mis:
    print("    MISLABEL %s x %s -> actual=%s ; claimants=%s values=%s ; bad=%s" %
          (pk, qk, list(act3), cands, badv, badr))
for pk, qk, act3 in l_orph:
    print("    ORPHAN   %s x %s -> actual=%s" % (pk, qk, list(act3)))

print("== M2 sensitivity: first-match-wins 变体 ==")
s2 = survey_firstmatch(True)
l2 = survey_firstmatch(False)
print("  [FIRSTMATCH-STRICT] OK=%d MISLABEL=%d ORPHAN=%d" % (s2[0], len(s2[1]), len(s2[2])))
print("  [FIRSTMATCH-LOOSE ] OK=%d MISLABEL=%d ORPHAN=%d" % (l2[0], len(l2[1]), len(l2[2])))

# ---- F5 实流可达域（make_pre / copy_post 输出域实读；出处见报告 §3）----
REAL_PRE = ["none", "absent", "present_sha", "error"]      # None=:6528 调用侧；三态=make_pre 输出域
REAL_POST = ["nofile", "re_none", "re_true", "sha_diff",
             "mt_same", "mt_up", "mt_down"]                # copy_post 四形态展开；no_post_sha/mt_missing 仅 fixture
real_grid = set((pk, qk) for pk in REAL_PRE for qk in REAL_POST)
print("== F5 real-flow reachable grid size = %d / 81" % len(real_grid))

REACH = {
    ("none", "re_none"): "R-实跑",
    ("none", "re_true"): "R-结构未单跑",
    ("error", "re_none"): "R-实跑",
    ("error", "re_true"): "R-结构未单跑",
    ("absent", "re_true"): "R-实跑",
    ("absent", "re_none"): "R-实跑",
    ("empty", "re_none"): "NR", ("empty", "re_true"): "NR",
    ("missing", "re_none"): "NR", ("missing", "re_true"): "NR",
    ("dirty", "re_none"): "NR", ("dirty", "re_true"): "NR",
    ("present_nosh", "re_true"): "NR",
    ("expl_unknown", "re_none"): "NR", ("expl_unknown", "re_true"): "NR",
    ("expl_unknown", "no_post_sha"): "NR", ("expl_unknown", "sha_diff"): "NR",
    ("expl_unknown", "mt_same"): "NR", ("expl_unknown", "mt_up"): "NR",
    ("expl_unknown", "mt_down"): "NR", ("expl_unknown", "mt_missing"): "NR",
}

def tag_reach(cell):
    t = REACH.get(cell)
    if t is None:
        return "IN-REAL-GRID" if cell in real_grid else "OUT-REAL-GRID"
    return t

print("== M3 exposed-cell reachability split（两栏分开，不合并）==")
for tag, mis, orph in (("STRICT", s_mis, s_orph), ("LOOSE", l_mis, l_orph)):
    exp_cells = [(pk, qk, "MISLABEL") for pk, qk, _, _, _, _ in mis] + \
                [(pk, qk, "ORPHAN") for pk, qk, _ in orph]
    r_run = [c for c in exp_cells if tag_reach((c[0], c[1])) == "R-实跑"]
    r_struct = [c for c in exp_cells if tag_reach((c[0], c[1])) == "R-结构未单跑"]
    nr = [c for c in exp_cells if tag_reach((c[0], c[1])) == "NR"]
    unassessed = [c for c in exp_cells if tag_reach((c[0], c[1])) not in ("R-实跑", "R-结构未单跑", "NR")]
    print("  [%s] exposed=%d ; 可达-实跑=%d ; 可达-结构未单跑=%d ; 不可达纯文本债=%d ; 未评估=%d"
          % (tag, len(exp_cells), len(r_run), len(r_struct), len(nr), len(unassessed)))
    if unassessed:
        print("    UNASSESSED:", unassessed)
    for c in r_run:
        print("    可达-实跑       %s x %s (%s) actual=%s" % (c[0], c[1], c[2], list(grid[(c[0], c[1])][:3])))
    for c in r_struct:
        print("    可达-结构未单跑 %s x %s (%s) actual=%s" % (c[0], c[1], c[2], list(grid[(c[0], c[1])][:3])))
    for c in nr:
        print("    不可达-文本债   %s x %s (%s) actual=%s" % (c[0], c[1], c[2], list(grid[(c[0], c[1])][:3])))

print("== M4 full 81-cell table (actual + claimants) ==")
for pk in PRE_KINDS:
    for qk in POST_KINDS:
        a = grid[(pk, qk)]
        print("  %-13s x %-11s actual=%s/%s/%s ; strict-claimants=%s ; loose-claimants=%s"
              % (pk, qk, a[0], a[1], a[2], claimants(pk, qk, True), claimants(pk, qk, False)))

print("SE_ENUM_DONE")
