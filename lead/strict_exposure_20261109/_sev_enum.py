# -*- coding: utf-8 -*-
# 复核员独立重算：STRICT/LOOSE 两口径 81 格（9 pre × 9 post）
# 方法：importlib 装载候选真模块直调真 classify_except_freshness（非 AST 复刻、非硬编码）；
#       claimant 谓词由复核员按 STATE_MATRIX.json 14 行 condition 原文独立手编；
#       实码网格与耦合件 §4.1a 逐格交叉核对。
# 只读；零真机；零采样。
import ast
import importlib.util
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge"
CAND = os.path.join(BASE, "lead", "b2b_candidate_lf_20261107", "qc151_trip.candidate_lf.py")
MATRIX = os.path.join(BASE, "lead", "b2b_design_20261106", "STATE_MATRIX.json")

SHA_A = "a" * 64
SHA_B = "b" * 64

# ---------- F0 指纹（复核员自算） ----------
import hashlib
for tag, path in (("candidate", CAND), ("matrix", MATRIX)):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    print(f"F0 {tag} {h.hexdigest()} {n}")

# ---------- F1 顶层 AST 扫描（装载安全自查） ----------
with open(CAND, "r", encoding="utf-8") as f:
    src = f.read()
tree = ast.parse(src)
top_calls = [n.lineno for n in tree.body
             if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
main_guard = [n.lineno for n in tree.body
              if isinstance(n, ast.If) and
              getattr(n.test, "left", None) is not None and
              getattr(n.test.left, "id", "") == "__name__"]
print(f"F1 top-level Expr-Call = {top_calls} ; __main__ guard = {main_guard}")

# ---------- F2 importlib 装载真模块 ----------
spec = importlib.util.spec_from_file_location("qc151_trip_candidate_lf", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
classify = mod.classify_except_freshness
print(f"F2 import ok ; FRESHNESS_SNAPSHOT_STATES = {getattr(mod, 'FRESHNESS_SNAPSHOT_STATES', 'MISSING')}")

# ---------- 网格：9 pre × 9 post ----------
# pre 九类（与耦合件 §4.1a 同基）：未采集四变体 + 显式unknown + absent + present带sha + present缺sha + error
PRE = {
    "none":         None,
    "empty":        {},
    "missing":      {"exists": True},
    "dirty":        {"state": "junk_state"},
    "expl_unknown": {"state": "unknown"},
    "absent":       {"state": "absent_confirmed", "exists": False},
    "present_sha":  {"state": "present", "exists": True, "sha256": SHA_A, "mtime_pre": 1000.0},
    "present_nosh": {"state": "present", "exists": True, "sha256": None, "mtime_pre": 1000.0},
    "error":        {"state": "error", "error": "OSError: fake", "exists": None},
}
# post 九类：re_true 镜像真实 C2 流（:4769 先置 exists/size/sha/mt → :4772 写炸 → :4786 只增 read_error）
POST = {
    "re_none":    {"read_error": "PermissionError: fake-lock", "exists": None},
    "re_true":    {"read_error": "OSError: fake-disk-full", "exists": True,
                   "sha256": SHA_A, "mtime_post": 1000.0},
    "nofile":     {"exists": False},
    "no_post_sha": {"exists": True, "sha256": None},
    "sha_diff":   {"exists": True, "sha256": SHA_B},
    "mt_same":    {"exists": True, "sha256": SHA_A, "mtime_post": 1000.0},
    "mt_up":      {"exists": True, "sha256": SHA_A, "mtime_post": 2000.0},
    "mt_down":    {"exists": True, "sha256": SHA_A, "mtime_post": 500.0},
    "mt_missing": {"exists": True, "sha256": SHA_A, "mtime_post": None},
}
PRE_ORDER = ["none", "empty", "missing", "dirty", "expl_unknown",
             "absent", "present_sha", "present_nosh", "error"]
POST_ORDER = ["re_none", "re_true", "nofile", "no_post_sha", "sha_diff",
              "mt_same", "mt_up", "mt_down", "mt_missing"]

def actual_of(pk, qk):
    r = classify(PRE[pk], POST[qk])
    return (r["verdict"], r["confidence"], r["is_new"], r["usable_as_crash_evidence"])

# ---------- F3 与耦合件 §4.1a 全格表交叉核对（复核员自编期望网格，摘自该文档实读） ----------
V, N = None, None  # is_new 未测 = None
X4 = {  # (verdict, conf, is_new) 期望；记法 PRE=post_read_error UNK=unknown EPS=error_pre_snapshot
    ("none", "re_none"): ("post_read_error", "none", N), ("none", "re_true"): ("post_read_error", "none", N),
    ("none", "nofile"): ("unknown", "none", N), ("none", "no_post_sha"): ("unknown", "none", N),
    ("none", "sha_diff"): ("unknown", "none", N), ("none", "mt_same"): ("unknown", "none", N),
    ("none", "mt_up"): ("unknown", "none", N), ("none", "mt_down"): ("unknown", "none", N),
    ("none", "mt_missing"): ("unknown", "none", N),
    ("empty", "re_none"): ("post_read_error", "none", N), ("empty", "re_true"): ("post_read_error", "none", N),
    ("empty", "nofile"): ("unknown", "none", N), ("empty", "no_post_sha"): ("unknown", "none", N),
    ("empty", "sha_diff"): ("unknown", "none", N), ("empty", "mt_same"): ("unknown", "none", N),
    ("empty", "mt_up"): ("unknown", "none", N), ("empty", "mt_down"): ("unknown", "none", N),
    ("empty", "mt_missing"): ("unknown", "none", N),
    ("missing", "re_none"): ("post_read_error", "none", N), ("missing", "re_true"): ("post_read_error", "none", N),
    ("missing", "nofile"): ("unknown", "none", N), ("missing", "no_post_sha"): ("unknown", "none", N),
    ("missing", "sha_diff"): ("unknown", "none", N), ("missing", "mt_same"): ("unknown", "none", N),
    ("missing", "mt_up"): ("unknown", "none", N), ("missing", "mt_down"): ("unknown", "none", N),
    ("missing", "mt_missing"): ("unknown", "none", N),
    ("dirty", "re_none"): ("post_read_error", "none", N), ("dirty", "re_true"): ("post_read_error", "none", N),
    ("dirty", "nofile"): ("unknown", "none", N), ("dirty", "no_post_sha"): ("unknown", "none", N),
    ("dirty", "sha_diff"): ("unknown", "none", N), ("dirty", "mt_same"): ("unknown", "none", N),
    ("dirty", "mt_up"): ("unknown", "none", N), ("dirty", "mt_down"): ("unknown", "none", N),
    ("dirty", "mt_missing"): ("unknown", "none", N),
    ("expl_unknown", "re_none"): ("post_read_error", "none", N), ("expl_unknown", "re_true"): ("post_read_error", "none", N),
    ("expl_unknown", "nofile"): ("unknown", "none", N), ("expl_unknown", "no_post_sha"): ("unknown", "none", N),
    ("expl_unknown", "sha_diff"): ("unknown", "none", N), ("expl_unknown", "mt_same"): ("unknown", "none", N),
    ("expl_unknown", "mt_up"): ("unknown", "none", N), ("expl_unknown", "mt_down"): ("unknown", "none", N),
    ("expl_unknown", "mt_missing"): ("unknown", "none", N),
    ("absent", "re_none"): ("post_read_error", "none", N), ("absent", "re_true"): ("post_read_error", "none", N),
    ("absent", "nofile"): ("absent_both", "low", False),
    ("absent", "no_post_sha"): ("new_first_appearance", "high", True),
    ("absent", "sha_diff"): ("new_first_appearance", "high", True),
    ("absent", "mt_same"): ("new_first_appearance", "high", True),
    ("absent", "mt_up"): ("new_first_appearance", "high", True),
    ("absent", "mt_down"): ("new_first_appearance", "high", True),
    ("absent", "mt_missing"): ("new_first_appearance", "high", True),
    ("present_sha", "re_none"): ("post_read_error", "none", N), ("present_sha", "re_true"): ("post_read_error", "none", N),
    ("present_sha", "nofile"): ("vanished", "none", N),
    ("present_sha", "no_post_sha"): ("post_read_error", "none", N),
    ("present_sha", "sha_diff"): ("new_write", "high", True),
    ("present_sha", "mt_same"): ("leftover_unchanged", "high", False),
    ("present_sha", "mt_up"): ("rewritten_same_content", "medium", True),
    ("present_sha", "mt_down"): ("rewritten_same_content", "low", True),
    ("present_sha", "mt_missing"): ("leftover_unchanged", "medium", False),
    ("present_nosh", "re_none"): ("post_read_error", "none", N), ("present_nosh", "re_true"): ("post_read_error", "none", N),
    ("present_nosh", "nofile"): ("vanished", "none", N),
    ("present_nosh", "no_post_sha"): ("error_pre_snapshot", "none", N),
    ("present_nosh", "sha_diff"): ("error_pre_snapshot", "none", N),
    ("present_nosh", "mt_same"): ("error_pre_snapshot", "none", N),
    ("present_nosh", "mt_up"): ("error_pre_snapshot", "none", N),
    ("present_nosh", "mt_down"): ("error_pre_snapshot", "none", N),
    ("present_nosh", "mt_missing"): ("error_pre_snapshot", "none", N),
    ("error", "re_none"): ("post_read_error", "none", N), ("error", "re_true"): ("post_read_error", "none", N),
    ("error", "nofile"): ("error_pre_snapshot", "none", N), ("error", "no_post_sha"): ("error_pre_snapshot", "none", N),
    ("error", "sha_diff"): ("error_pre_snapshot", "none", N), ("error", "mt_same"): ("error_pre_snapshot", "none", N),
    ("error", "mt_up"): ("error_pre_snapshot", "none", N), ("error", "mt_down"): ("error_pre_snapshot", "none", N),
    ("error", "mt_missing"): ("error_pre_snapshot", "none", N),
}
mm = 0
for pk in PRE_ORDER:
    for qk in POST_ORDER:
        a = actual_of(pk, qk)
        if (a[0], a[1], a[2]) != X4[(pk, qk)]:
            mm += 1
            print(f"  XFAIL {pk} x {qk} actual={a[:3]} expected={X4[(pk, qk)]}")
print(f"F3 crosscheck vs 耦合件 §4.1a: {'ALL_PASS' if mm == 0 else f'{mm} MISMATCH'} / 81")

# ---------- claimant 谓词（复核员按 14 行 condition 原文独立手编） ----------
# 行号 = STATE_MATRIX.json 文件行（:2-:15）。STRICT = (归一 pre 态 == 行 preState 字段) ∧ 前件成立。
# LOOSE = 仅前件（condition 承载路由；:2 对显式 unknown 的覆盖采宽 preState 键，依据 = 耦合件 :112，
#         为复现裁决基线 ORPHAN=0 的必要读法；另设 LOOSE-puretext 变体核该依赖）。
# 编码注记（关键裁定）：
#  * :6/:13 的后件是存在性断言（跑后在场）——read_error 格 exists=True 时仍成立（耦合件 §4.1b O1′/W3 同判）。
#  * :8-:12 的后件是内容观测断言（sha/mt 比对）——read_error 置位时该观测按 :5「独立 error 出口」被抢占，
#    故要求 post.read_error 为空（§4.1b 未把 :8-:12 列为任何 read_error 格 claimant，同判）。
#  * re_true 的 post fixture 带 sha（真实流 :4769 先 update sha 再 :4772 写炸），:14「缺 post.sha256」
#    自然不命中，无需额外守卫。
def norm_state(pk):
    st = PRE[pk].get("state") if isinstance(PRE[pk], dict) else None
    return st if st in ("unknown", "absent_confirmed", "present", "error") else "unknown"

def pre_is_present(pk):
    return PRE[pk].get("sha256") is not None

def elig(row, pk, qk, loose, wide2):
    """row = 文件行号 int；返回 bool。loose=True 时跳过 preState 字段合取；wide2=:2 宽键含显式 unknown。"""
    post = POST[qk]
    re_err = bool(post.get("read_error"))
    pex = post.get("exists")
    nst = norm_state(pk)
    field_ok = True
    if not loose:
        fld = ROWS[row]["preState"]
        field_ok = (fld == nst)
    if not field_ok:
        return False
    if row == 2:
        # condition：pre=None/{}/缺state/脏值（未采集），跑后任意文件状态
        if wide2 and loose:
            return nst == "unknown"
        return pk in ("none", "empty", "missing", "dirty")
    if row == 3:
        # pre.state 显式为 unknown（未采集）+ 跑后无件
        return pk == "expl_unknown" and pex is False
    if row == 4:
        # 跑前采集抛异常（snap.error 非空），无跑后限定
        return pk == "error"
    if row == 5:
        # 跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口
        return bool(re_err)
    if row == 6:
        # 跑前确认无件 + 跑后在场（存在性硬证）
        return pk == "absent" and pex is True
    if row == 7:
        # 跑前确认无件 + 跑后无件
        return pk == "absent" and pex is False
    if row in (8, 9, 10, 11, 12):
        # 跑前在 + 跑后在 + 内容观测断言族；read_error 置位 ⇒ 观测被 :5 独立出口抢占
        if not (nst == "present" and pex is True and not re_err and pre_is_present(pk)):
            return False
        psha, post_sha = PRE[pk].get("sha256"), post.get("sha256")
        pmt, omt = PRE[pk].get("mtime_pre"), post.get("mtime_post")
        same_sha = (psha is not None and post_sha is not None and post_sha == psha)
        if row == 8:
            return same_sha and pmt is not None and omt is not None and float(omt) == float(pmt)
        if row == 9:
            return same_sha and (pmt is None) != (omt is None)
        if row == 10:
            return psha is not None and post_sha is not None and post_sha != psha
        if row == 11:
            return same_sha and pmt is not None and omt is not None and float(omt) > float(pmt)
        if row == 12:
            return same_sha and pmt is not None and omt is not None and float(omt) < float(pmt)
    if row == 13:
        # 跑前在 + 跑后在 + 缺 pre.sha256（存在性后件，read_error 格仍命中，§4.1b W3 同判）
        return nst == "present" and pex is True and not pre_is_present(pk)
    if row == 14:
        # 跑前在 + 跑后在 + 缺 post.sha256（无法比对）
        # 「无法比对」前件以 pre.sha 在场为前提——缺 pre.sha 的格由 :13（码序 7）先截，
        # 耦合件 §4.1a 注记：「码序 7（:4673 缺 pre.sha）先于码序 8（:4678 缺 post.sha）」，
        # §4.1b 该格仅登记 :13。若去此前提（字面读法），present_nosh×no_post_sha 将经 :14 多出
        # 1 格 MISLABEL（STRICT 59/13/9、LOOSE 66/15/0）——见 M2 变体输出。
        return (nst == "present" and pex is True and not re_err
                and pre_is_present(pk) and post.get("sha256") is None)
    if row == 15:
        # 跑前在 + 跑后无件
        return nst == "present" and pex is False
    raise AssertionError(row)

with open(MATRIX, "r", encoding="utf-8") as f:
    ROWS = {i + 2: r for i, r in enumerate(json.load(f))}  # 文件行 :2-:15

ROW_ORDER = list(range(2, 16))
# 矩阵三元 = (verdict, confidence, usableAsCrashEvidence)；JSON 无 is_new 字段
def row_triple(row):
    r = ROWS[row]
    return (r["verdict"], r["confidence"], r["usableAsCrashEvidence"])

def survey(loose, wide2, first_match):
    ok = mis = orph = 0
    detail = []
    for pk in PRE_ORDER:
        for qk in POST_ORDER:
            a = actual_of(pk, qk)
            cl = [r for r in ROW_ORDER if elig(r, pk, qk, loose, wide2)]
            if not cl:
                orph += 1
                detail.append((pk, qk, "ORPHAN", []))
                continue
            a3 = (a[0], a[1], a[3])  # verdict/conf/usable
            if first_match:
                bad = [] if row_triple(cl[0]) == a3 else [cl[0]]
            else:
                bad = [r for r in cl if row_triple(r) != a3]
            if bad:
                mis += 1
                detail.append((pk, qk, "MISLABEL", cl, bad))
            else:
                ok += 1
    return ok, mis, orph, detail

print("== M1 baseline（规则：无 claimant=ORPHAN；claimant 三元(verdict/conf/usable) 全对=OK，否则 MISLABEL）==")
s_ok, s_mis, s_orph, s_det = survey(False, False, False)
print(f"[SEV-STRICT] OK={s_ok} MISLABEL={s_mis} ORPHAN={s_orph} (81 cells)")
l_ok, l_mis, l_orph, l_det = survey(True, True, False)
print(f"[SEV-LOOSE ] OK={l_ok} MISLABEL={l_mis} ORPHAN={l_orph} (81 cells)")
print("-- STRICT mislabel/orphan cells --")
for d in s_det:
    if d[2] == "ORPHAN":
        print(f"  ORPHAN   {d[0]} x {d[1]}")
    else:
        cl, bad = d[3], d[4]
        print(f"  MISLABEL {d[0]} x {d[1]} claimants={cl} bad={bad} claim_triples={[row_triple(r) for r in cl]}")
print("-- LOOSE mislabel cells --")
for d in l_det:
    if d[2] == "MISLABEL":
        print(f"  MISLABEL {d[0]} x {d[1]} claimants={d[3]} bad={d[4]}")

print("== M2 敏感性：first-match-wins + LOOSE-puretext + :14 字面变体 ==")
fm_s = survey(False, False, True)[:3]
fm_l = survey(True, True, True)[:3]
pt_l = survey(True, False, False)[:3]
print(f"[SEV-FM-STRICT] OK={fm_s[0]} MISLABEL={fm_s[1]} ORPHAN={fm_s[2]}")
print(f"[SEV-FM-LOOSE ] OK={fm_l[0]} MISLABEL={fm_l[1]} ORPHAN={fm_l[2]}")
print(f"[SEV-LOOSE-PURETEXT(:2 不采宽键)] OK={pt_l[0]} MISLABEL={pt_l[1]} ORPHAN={pt_l[2]}")

# :14 字面变体（不要求 pre.sha 在场）：临时重定义后重算
_orig_elig14 = elig
def elig_lit14(row, pk, qk, loose, wide2):
    if row == 14:
        post = POST[qk]
        return (norm_state(pk) == "present" and post.get("exists") is True
                and not post.get("read_error") and post.get("sha256") is None)
    return _orig_elig14(row, pk, qk, loose, wide2)
elig = elig_lit14
lit_s = survey(False, False, False)[:3]
lit_l = survey(True, True, False)[:3]
elig = _orig_elig14
print(f"[SEV-LIT14-STRICT(:14 不要求 pre.sha)] OK={lit_s[0]} MISLABEL={lit_s[1]} ORPHAN={lit_s[2]}")
print(f"[SEV-LIT14-LOOSE ] OK={lit_l[0]} MISLABEL={lit_l[1]} ORPHAN={lit_l[2]}")

# ---------- M3 可达性两栏（实流 pre = None/make_pre 三态；post = copy_post 四形态 + 内容变体；
#                    fixture-only = {}/缺state/脏值/显式unknown/present缺sha × 缺post.sha/mt缺） ----------
REAL_PRE = {"none", "absent", "present_sha", "error"}
REAL_POST = {"re_none", "re_true", "nofile", "sha_diff", "mt_same", "mt_up", "mt_down"}
def split(det):
    reach = [(d[0], d[1], d[2]) for d in det if d[0] in REAL_PRE and d[1] in REAL_POST]
    debt = [(d[0], d[1], d[2]) for d in det if not (d[0] in REAL_PRE and d[1] in REAL_POST)]
    return reach, debt
print("== M3 暴露格两栏（可达 / 不可达文本债，分开不合并）==")
for name, det in (("STRICT", s_det), ("LOOSE", l_det)):
    reach, debt = split(det)
    print(f"[{name}] exposed={len(det)} 可达={len(reach)} 不可达文本债={len(debt)}")
    for pk, qk, st in reach:
        print(f"  可达   {pk} x {qk} ({st})")
    for pk, qk, st in debt:
        print(f"  文本债 {pk} x {qk} ({st})")

# ---------- M4 逐格 claimant 对照表（供复核存档） ----------
print("== M4 81 格 actual + claimants ==")
for pk in PRE_ORDER:
    for qk in POST_ORDER:
        a = actual_of(pk, qk)
        cs = [r for r in ROW_ORDER if elig(r, pk, qk, False, False)]
        cl = [r for r in ROW_ORDER if elig(r, pk, qk, True, True)]
        print(f"  {pk:12s} x {qk:11s} actual={a[0]}/{a[1]}/{a[2]} ; strict={cs} ; loose={cl}")
print("SEV_ENUM_DONE")
