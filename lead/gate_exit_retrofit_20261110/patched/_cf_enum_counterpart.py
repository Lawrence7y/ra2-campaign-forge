# -*- coding: utf-8 -*-
"""_cf_enum_counterpart.py — 「收紧 condition」vs「补对照行」81 格全情景仿真（对比设计员·GLM）。

纪律：零真机 / 零采样（纯函数级静态 import + 直调，无 hook/dump/注入/内存解析）/ 被核件只读 /
唯一写域 = 本目录 / 不 commit 不 push。Python -I -X utf8 + 绝对路径。

方法（全部为本轮独立实现；claimant 谓词框架沿 _se_enum.py:191-260 本轮实读逐条对齐，便于可比）：
  F0 指纹复核（hashlib）；
  F2 importlib 静态装载候选真模块，直调 classify_except_freshness 跑 81 格；
  F3 与耦合件 §4.1a 全格表交叉核对；
  M1 基线两口径 survey（须复现 _se_enum_out.txt:14 的 60/12/9 与 :36 的 67/14/0）；
  M2 六情景 × 多读法 survey：
     S0 基线
     T4 纯收紧（:2/:4/:6/:13 前件加「post.read_error 为空」类限定，无分流句，行数不变）
     U  统一清单 B 形态（U2=:2 收紧+分流句；U3=:5 注记+优先句；U4=:4 分流句；:6/:13 不动）
     P3 补对照行（追加 :16/:17/:18 三行，verdict=post_read_error/none/false）
     P4 补对照行（P3 + :19 第四行接 expl_unknown × 跑后非 read_error 六格）
     PT 组合（T4 + P3）
  读法：strict（耦合件:67 合取键）；strict_pri（strict + :5 优先句压制同格冲突，仅 U 情景生效，
        即裁决件 _rv2_probe_20261109_out.txt:51 的 suppressed-by-priority 建模）；loose（裁决:42(ii)
        condition 文本承载路由 + :2 宽键 = 耦合件:112）。
  M3 可达 6 格逐格前后状态（REACH 标注沿 _se_enum.py:291-306 实读值）；
  M4 12 误配格 + 9 孤儿格逐格跨情景状态表（strict 读法）。
"""
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

rows_json = json.loads(open(MATRIX, encoding="utf-8").read())
assert len(rows_json) == 14, len(rows_json)

def rowvals_static(line):
    r = rows_json[line - 2]
    return (r["verdict"], r["confidence"], r["usableAsCrashEvidence"])

print("== F2 import real candidate module ==")
spec = importlib.util.spec_from_file_location("qc151_cand_cf", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
classify = mod.classify_except_freshness
print("  import ok; classify qualname =", classify.__qualname__)

PRE_KINDS = ["none", "empty", "missing", "dirty", "expl_unknown",
             "absent", "present_sha", "present_nosh", "error"]

def mk_pre(k):
    if k == "none":
        return None
    if k == "empty":
        return {}
    if k == "missing":
        return {"size": 123}
    if k == "dirty":
        return {"state": "garbage", "size": 123}
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
        b["read_error"] = "OSError: probe read fail"
    elif k == "re_true":
        b.update({"exists": True, "size": 5, "sha256": "E" * 64, "mtime_post": 222.0,
                  "read_error": "OSError: probe write fail"})
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
    return (r["verdict"], r["confidence"], r["usable_as_crash_evidence"])

# ---- F3 xcheck vs 耦合件 §4.1a ----
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

print("== F3 crosscheck vs 耦合件 §4.1a ==")
bad = 0
grid = {}
for pk in PRE_KINDS:
    for qk in POST_KINDS:
        a = actual(pk, qk)
        grid[(pk, qk)] = a
        e = EXPECT[(pk, qk)]
        if (a[0], a[1]) != (e[0], e[1]):
            bad += 1
            print("  XCHECK-FAIL %s x %s actual=%s expect=%s" % (pk, qk, a[:2], e[:2]))
print("  XCHECK %s (%d mismatch / 81)" % ("ALL_PASS" if bad == 0 else "FAIL", bad))

# ---- claimant 覆盖谓词（基线，沿 _se_enum.py:191-226 同构） ----
REK = ["re_none", "re_true"]
ET = ["no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing", "re_true"]
NORM = {"none": "unknown", "empty": "unknown", "missing": "unknown", "dirty": "unknown",
        "expl_unknown": "unknown", "absent": "absent_confirmed",
        "present_sha": "present", "present_nosh": "present", "error": "error"}

def norm(pk):
    return NORM[pk]

def cov_base(line, pk, qk, strict):
    u = norm(pk)
    if line == 2:
        return (pk in UNC) if strict else (u == "unknown")
    if line == 3:
        return (pk == "expl_unknown") and (qk == "nofile")
    if line == 4:
        return (pk == "error")
    if line == 5:
        return ((u == "present") and (qk in REK)) if strict else (qk in REK)
    if line == 6:
        return (pk == "absent") and (qk in ET)
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
        return (pk == "present_nosh") and (qk in ET)
    if line == 14:
        return (pk == "present_sha") and (qk == "no_post_sha")
    if line == 15:
        return (u == "present") and (qk == "nofile")
    raise AssertionError(line)

# ---- 情景定义 ----
def cov_tight2(pk, qk, strict):
    return ((pk in UNC) if strict else (norm(pk) == "unknown")) and (qk not in REK)

def cov_tight4(pk, qk, strict):
    return (pk == "error") and (qk not in REK)

def cov_tight6(pk, qk, strict):
    return (pk == "absent") and (qk in ET) and (qk not in REK)

def cov_tight13(pk, qk, strict):
    return (pk == "present_nosh") and (qk in ET) and (qk not in REK)

PRE_T = (PRE, "none", False)
UNK_T = (UNK, "none", False)

def cov_p16(pk, qk, strict):   # 补A unknown 归一态 + read_error
    return (norm(pk) == "unknown") and (qk in REK)

def cov_p17(pk, qk, strict):   # 补B absent_confirmed + read_error
    return (norm(pk) == "absent_confirmed") and (qk in REK)

def cov_p18(pk, qk, strict):   # 补C error + read_error
    return (norm(pk) == "error") and (qk in REK)

def cov_p19(pk, qk, strict):   # 补D unknown 归一态 + 跑后非 read_error
    return (norm(pk) == "unknown") and (qk not in REK)

EXTRA_P3 = [(16, PRE_T, cov_p16), (17, PRE_T, cov_p17), (18, PRE_T, cov_p18)]
EXTRA_D = (19, UNK_T, cov_p19)

SCN = {
    "S0": dict(cov_ovr={}, extra=[], val_ovr={}, suppress=None),
    "T4": dict(cov_ovr={2: cov_tight2, 4: cov_tight4, 6: cov_tight6, 13: cov_tight13},
               extra=[], val_ovr={}, suppress=None),
    "U":  dict(cov_ovr={2: cov_tight2}, extra=[], val_ovr={}, suppress="U3"),
    "U2only": dict(cov_ovr={2: cov_tight2}, extra=[], val_ovr={}, suppress=None),
    "U3only": dict(cov_ovr={}, extra=[], val_ovr={}, suppress="U3"),
    "U4only": dict(cov_ovr={}, extra=[], val_ovr={}, suppress=None),
    "U_NP": dict(cov_ovr={2: cov_tight2}, extra=[], val_ovr={}, suppress=None),
    "P3": dict(cov_ovr={}, extra=EXTRA_P3, val_ovr={}, suppress=None),
    "P4": dict(cov_ovr={}, extra=EXTRA_P3 + [EXTRA_D], val_ovr={}, suppress=None),
    "PT": dict(cov_ovr={2: cov_tight2, 4: cov_tight4, 6: cov_tight6, 13: cov_tight13},
               extra=EXTRA_P3, val_ovr={}, suppress=None),
}

EXTRA_VALS = {ln: t for ln, t, _f in EXTRA_P3}
EXTRA_VALS[EXTRA_D[0]] = EXTRA_D[1]

def row_vals(line, scn, reading, pk, qk):
    ov = SCN[scn]["val_ovr"]
    if (line, reading) in ov:
        return ov[(line, reading)](pk, qk)
    if line in EXTRA_VALS:
        return EXTRA_VALS[line]
    return rowvals_static(line)

def cov(line, pk, qk, strict, scn):
    ovr = SCN[scn]["cov_ovr"]
    if line in ovr:
        return ovr[line](pk, qk, strict)
    for ln, _t, f in SCN[scn]["extra"]:
        if ln == line:
            return f(pk, qk, strict)
    return cov_base(line, pk, qk, strict)

def suppress(line, pk, qk, strict, scn):
    s = SCN[scn]["suppress"]
    if s != "U3":
        return False
    if line in (6, 13) and qk in REK:
        return (norm(pk) == "present") if strict else True
    return False

def claimants(pk, qk, strict, scn, first_match=False, use_suppress=True):
    lines = list(range(2, 16)) + [ln for ln, _t, _f in SCN[scn]["extra"]]
    out = []
    for ln in lines:
        ok = cov(ln, pk, qk, strict, scn)
        if ok and use_suppress and suppress(ln, pk, qk, strict, scn):
            ok = False
        if ok:
            out.append(ln)
            if first_match:
                break
    return out

def survey(scn, strict, first_match=False):
    ok_n, mis, orph, supp = 0, [], [], 0
    for pk in PRE_KINDS:
        for qk in POST_KINDS:
            a = grid[(pk, qk)]
            cands = claimants(pk, qk, strict, scn, first_match, use_suppress=True)
            full = claimants(pk, qk, strict, scn, False, use_suppress=False)
            if len(full) > len(cands):
                supp += 1
            if not cands:
                orph.append((pk, qk, a))
            elif all(row_vals(i, scn, "loose" if not strict else "strict", pk, qk) == a
                     for i in cands):
                ok_n += 1
            else:
                badr = [i for i in cands
                        if row_vals(i, scn, "loose" if not strict else "strict", pk, qk) != a]
                mis.append((pk, qk, a, cands, badr, [row_vals(i, scn, "loose" if not strict else "strict", pk, qk) for i in badr]))
    return ok_n, mis, orph, supp

# U4 :4 分流句在 loose 读法下的取值修正（strict 读法不修正——裁决 M3b 口径）
def _val4_loose(pk, qk):
    return (PRE, "none", False) if qk in REK else rowvals_static(4)

SCN["U"]["val_ovr"][(4, "loose")] = _val4_loose
SCN["U4only"]["val_ovr"][(4, "loose")] = _val4_loose

print("== M1 baseline survey (must equal _se_enum_out.txt:14/:36) ==")
for strict, tag in ((True, "STRICT"), (False, "LOOSE")):
    ok_n, mis, orph, supp = survey("S0", strict)
    print("  [S0-%s] OK=%d MISLABEL=%d ORPHAN=%d suppressed=%d" % (tag, ok_n, len(mis), len(orph), supp))
    for pk, qk, a, cands, badr, badv in mis:
        print("    MISLABEL %s x %s -> actual=%s ; claimants=%s bad=%s values=%s" %
              (pk, qk, list(a), cands, badr, badv))
    for pk, qk, a in orph:
        print("    ORPHAN   %s x %s -> actual=%s" % (pk, qk, list(a)))

print("== M2 scenario survey (all readings) ==")
BASE_ROW_N = {"S0": 14, "T4": 14, "U": 14, "U2only": 14, "U3only": 14, "U4only": 14,
              "U_NP": 14, "P3": 17, "P4": 18, "PT": 17}
results = {}
for scn in ("S0", "T4", "U", "U2only", "U3only", "U4only", "U_NP", "P3", "P4", "PT"):
    for strict, tag in ((True, "strict"), (False, "loose")):
        ok_n, mis, orph, supp = survey(scn, strict)
        ok_f, mis_f, orph_f, _ = survey(scn, strict, first_match=True)
        results[(scn, tag)] = (ok_n, len(mis), len(orph), supp)
        print("  [%s-%s] rows=%d OK=%d MISLABEL=%d ORPHAN=%d suppressed=%d | firstmatch OK=%d M=%d O=%d"
              % (scn, tag, BASE_ROW_N[scn], ok_n, len(mis), len(orph), supp,
                 ok_f, len(mis_f), len(orph_f)))
        for pk, qk, a, cands, badr, badv in mis:
            print("    MISLABEL %s x %s -> actual=%s ; claimants=%s bad=%s" % (pk, qk, list(a), cands, badr))
        for pk, qk, a in orph:
            print("    ORPHAN   %s x %s -> actual=%s" % (pk, qk, list(a)))

# U strict + 优先句读法（裁决 _rv2_probe AFTER-B-STRICT 的 suppressed-by-priority 建模）
ok_n, mis, orph, supp = survey("U", True)
print("  [U-strict+pri(:5 优先句压制)] 见上方 [U-strict] 行 suppressed 计数；其 MISLABEL 明细即裁决 :52-:54 的 3 格")

print("== M3 reachable-6 per-scenario status (strict & loose) ==")
REACH6 = [("none", "re_none", "R-实跑"), ("none", "re_true", "R-结构未单跑"),
          ("error", "re_none", "R-实跑"), ("error", "re_true", "R-结构未单跑"),
          ("absent", "re_true", "R-实跑"), ("absent", "re_none", "R-实跑")]
for scn, strict, tag in (("S0", True, "strict"), ("T4", True, "strict"), ("U", True, "strict"),
                         ("P3", True, "strict"), ("P4", True, "strict"), ("PT", True, "strict"),
                         ("U", False, "loose"), ("T4", False, "loose"), ("PT", False, "loose")):
    print("  -- %s (%s) --" % (scn, tag))
    for pk, qk, rtag in REACH6:
        a = grid[(pk, qk)]
        cands = claimants(pk, qk, strict, scn, False)
        if not cands:
            st = "ORPHAN"
        elif all(row_vals(i, scn, "loose" if not strict else "strict", pk, qk) == a for i in cands):
            st = "OK"
        else:
            st = "MISLABEL"
        print("    %s x %-8s (%s) -> %s ; claimants=%s ; actual=%s"
              % (pk, qk, rtag, st, cands, list(a)))

print("== M4 12 mislabel + 9 orphan cells across scenarios (strict reading, all-claimant) ==")
BASE_M = [("none", "re_none"), ("none", "re_true"), ("empty", "re_none"), ("empty", "re_true"),
          ("missing", "re_none"), ("missing", "re_true"), ("dirty", "re_none"), ("dirty", "re_true"),
          ("absent", "re_true"), ("present_nosh", "re_true"), ("error", "re_none"), ("error", "re_true")]
BASE_O = [("expl_unknown", "re_none"), ("expl_unknown", "re_true"), ("expl_unknown", "no_post_sha"),
          ("expl_unknown", "sha_diff"), ("expl_unknown", "mt_same"), ("expl_unknown", "mt_up"),
          ("expl_unknown", "mt_down"), ("expl_unknown", "mt_missing"), ("absent", "re_none")]
scns = ["S0", "T4", "U", "P3", "P4", "PT"]
hdr = "  cell".ljust(30) + "".join(s.rjust(10) for s in scns)
print(hdr + "   (OK/MIS/ORP)")
for (pk, qk) in BASE_M + BASE_O:
    row = ("  %s x %s" % (pk, qk)).ljust(30)
    for scn in scns:
        cands = claimants(pk, qk, True, scn, False)
        a = grid[(pk, qk)]
        if not cands:
            row += "ORP".rjust(10)
        elif all(row_vals(i, scn, "strict", pk, qk) == a for i in cands):
            row += "OK".rjust(10)
        else:
            row += "MIS".rjust(10)
    print(row)

print("CF_ENUM_DONE")


# ---------- 出口追加（仅追加；原件一字未改）----------
# 原件三处「对自身的检查」在此合取聚合，判定式逐字复用原件表达式，不改任何判定逻辑：
#   :38-45  F0 指纹 ok_all（两件 hash+size 全 MATCH 才真）；
#   :48     assert len(rows_json) == 14（原件为 assert，失败即抛异常；此处只重算同一
#           布尔式，不替换、不删除原 assert，故原运行行为与打印完全不变）；
#   :158-168 F3 交叉核对 bad（81 格逐格对比，bad==0 才 ALL_PASS）。
# M1-M4 (:326-398) 是情景仿真的领域数据打印（OK/MISLABEL/ORPHAN 是描述被仿真的
# 清单设计，不是本脚本对自身的核验结论），原件从未据此给出 PASS/FAIL 裁决，故不纳入聚合。
ok = ok_all and (len(rows_json) == 14) and (bad == 0)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
