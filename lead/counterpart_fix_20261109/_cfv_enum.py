# -*- coding: utf-8 -*-
"""_cfv_enum.py — 对照补齐复核员·GLM 独立实现：81 格基线 + 六情景 claimant 裁决。

独立性声明：claimant 谓词由复核员从 STATE_MATRIX.json 各行 condition 原文自行推导；
裁决规则（无 claimant=ORPHAN / 全部 claimant 三元一致=OK / 否则 MISLABEL）与
STRICT（preState 字段∧condition 前件，耦合件:67）/LOOSE（condition 文本路由，
裁决:42(ii)+耦合件:112 宽键）口径沿在案定义。情景建模（T4/U/U2only/U3only/U4only/
P3/P4/PT）按主交付件 §2-§5 的定义独立编码，用于核对撰写人 _cf_enum_out.txt 的数字。
零真机/零采样/只读被核件；python -I -X utf8。
"""
import hashlib
import importlib.util
import json
import sys

BASE = r"D:\Project\ra2-campaign-forge"
CAND = BASE + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"
MATRIX = BASE + r"\lead\b2b_design_20261106\STATE_MATRIX.json"

print("== F0 fingerprints (hashlib, read-only) ==")
ok_all = True
for name, p, exp in (("candidate", CAND, ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759)),
                     ("matrix", MATRIX, ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558))):
    b = open(p, "rb").read()
    h, n = hashlib.sha256(b).hexdigest(), len(b)
    ok = (h, n) == exp
    ok_all = ok_all and ok
    print("  %s  %s  %d  %s" % (name, h, n, "MATCH" if ok else "MISMATCH"))
print("F0", "ALL_MATCH" if ok_all else "MISMATCH")

rows = json.loads(open(MATRIX, encoding="utf-8").read())
assert len(rows) == 14, len(rows)

def rowvals(line):
    r = rows[line - 2]
    return (r["verdict"], r["confidence"], r["usableAsCrashEvidence"])

spec = importlib.util.spec_from_file_location("qc151_cand_cfv", CAND)
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

grid = {}
print("== F3' 81-cell actual grid (direct call of real classify) ==")
for pk in PRE_KINDS:
    for qk in POST_KINDS:
        r = classify(mk_pre(pk), mk_post(qk))
        grid[(pk, qk)] = (r["verdict"], r["confidence"], r["usable_as_crash_evidence"])

# ---- 复核员自编 claimant 谓词（依据 = :2-:15 condition 原文）----
UNC = ["none", "empty", "missing", "dirty"]          # :2 逐字枚举的四种未采集形态
REK = ["re_none", "re_true"]                          # post.read_error 非空两型
ET = ["no_post_sha", "sha_diff", "mt_same", "mt_up", "mt_down", "mt_missing", "re_true"]  # exists=True 型

NORM = {"none": "unknown", "empty": "unknown", "missing": "unknown", "dirty": "unknown",
        "expl_unknown": "unknown", "absent": "absent_confirmed",
        "present_sha": "present", "present_nosh": "present", "error": "error"}

def cov_base(line, pk, qk, strict):
    u = NORM[pk]
    if line == 2:   # pre=None/{}/缺state/脏值 + 跑后任意；宽键读法 = 归一 unknown（耦合件:112）
        return (pk in UNC) if strict else (u == "unknown")
    if line == 3:   # pre.state 显式 unknown + 跑后无件
        return (pk == "expl_unknown") and (qk == "nofile")
    if line == 4:   # snap.error 非空 ⇒ 独立 error 出口（condition 无跑后限定）
        return (pk == "error")
    if line == 5:   # post.read_error 非空 ⇒ 独立 error 出口；strict 另须 preState=present
        return ((u == "present") and (qk in REK)) if strict else (qk in REK)
    if line == 6:   # 跑前确认无件 + 跑后在场（exists=True 字面）
        return (pk == "absent") and (qk in ET)
    if line == 7:   # 跑前确认无件 + 跑后无件
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
    if line == 13:  # 跑前在+跑后在+缺 pre.sha256（present_nosh）
        return (pk == "present_nosh") and (qk in ET)
    if line == 14:  # 跑前在+跑后在+缺 post.sha256（码序残差：present_sha×no_post_sha）
        return (pk == "present_sha") and (qk == "no_post_sha")
    if line == 15:  # 跑前在 + 跑后无件（preState=present 两种在场态）
        return (u == "present") and (qk == "nofile")
    raise AssertionError(line)

# ---- 收紧（前件加「post.read_error 为空」）----
def t2(pk, qk, strict):
    return ((pk in UNC) if strict else (NORM[pk] == "unknown")) and (qk not in REK)

def t4(pk, qk, strict):
    return (pk == "error") and (qk not in REK)

def t6(pk, qk, strict):
    return (pk == "absent") and (qk in ET) and (qk not in REK)

def t13(pk, qk, strict):
    return (pk == "present_nosh") and (qk in ET) and (qk not in REK)

# ---- 补对照行（拟 :16/:17/:18/:19，值=拟文三元）----
V_PRE = ("post_read_error", "none", False)
V_UNK = ("unknown", "none", False)

def p16(pk, qk, strict):   # 补A：preState=unknown + 跑后 read_error
    return (NORM[pk] == "unknown") and (qk in REK)

def p17(pk, qk, strict):   # 补B：preState=absent_confirmed + 跑后 read_error
    return (NORM[pk] == "absent_confirmed") and (qk in REK)

def p18(pk, qk, strict):   # 补C：preState=error + 跑后 read_error
    return (NORM[pk] == "error") and (qk in REK)

def p19(pk, qk, strict):   # 补D：pre.state 显式 unknown + 跑后非 read_error
    return (pk == "expl_unknown") and (qk not in REK)

EXTRA_VALS = {16: V_PRE, 17: V_PRE, 18: V_PRE, 19: V_UNK}

SCN = {
    "S0": dict(ovr={}, extra=[], prio=False, v4loose=False),
    "T4": dict(ovr={2: t2, 4: t4, 6: t6, 13: t13}, extra=[], prio=False, v4loose=False),
    "U": dict(ovr={2: t2}, extra=[], prio=True, v4loose=True),
    "U2only": dict(ovr={2: t2}, extra=[], prio=False, v4loose=False),
    "U3only": dict(ovr={}, extra=[], prio=True, v4loose=False),
    "U4only": dict(ovr={}, extra=[], prio=False, v4loose=True),
    "P3": dict(ovr={}, extra=[(16, p16), (17, p17), (18, p18)], prio=False, v4loose=False),
    "P4": dict(ovr={}, extra=[(16, p16), (17, p17), (18, p18), (19, p19)], prio=False, v4loose=False),
    "PT": dict(ovr={2: t2, 4: t4, 6: t6, 13: t13}, extra=[(16, p16), (17, p17), (18, p18)],
               prio=False, v4loose=False),
}
ROWS_N = {"S0": 14, "T4": 14, "U": 14, "U2only": 14, "U3only": 14, "U4only": 14,
          "P3": 17, "P4": 18, "PT": 17}

def row_vals(line, scn, strict, pk, qk):
    if line == 4 and (not strict) and SCN[scn]["v4loose"] and qk in REK:
        return V_PRE                     # U4 分流句在 loose 文本路由下承载 post_read_error
    if line in EXTRA_VALS:
        return EXTRA_VALS[line]
    return rowvals(line)

def line_covers(line, pk, qk, strict, scn):
    ovr = SCN[scn]["ovr"]
    if line in ovr:
        return ovr[line](pk, qk, strict)
    for ln, f in SCN[scn]["extra"]:
        if ln == line:
            return f(pk, qk, strict)
    return cov_base(line, pk, qk, strict)

def claimants(pk, qk, strict, scn):
    out = []
    for ln in list(range(2, 16)) + [ln for ln, _ in SCN[scn]["extra"]]:
        if not line_covers(ln, pk, qk, strict, scn):
            continue
        if SCN[scn]["prio"] and ln in (6, 13) and qk in REK \
                and line_covers(5, pk, qk, strict, scn):
            continue                     # U3：:5 优先句仅在同格并存时压制
        out.append(ln)
    return out

def survey(scn, strict):
    ok_n, mis, orph, supp = 0, [], [], 0
    for pk in PRE_KINDS:
        for qk in POST_KINDS:
            a = grid[(pk, qk)]
            cands = claimants(pk, qk, strict, scn)
            if SCN[scn]["prio"]:
                full = [ln for ln in list(range(2, 16))
                        if line_covers(ln, pk, qk, strict, scn)]
                if len(full) > len(cands):
                    supp += 1
            if not cands:
                orph.append((pk, qk))
            elif all(row_vals(i, scn, strict, pk, qk) == a for i in cands):
                ok_n += 1
            else:
                badr = [i for i in cands if row_vals(i, scn, strict, pk, qk) != a]
                mis.append((pk, qk, cands, badr, [row_vals(i, scn, strict, pk, qk) for i in badr]))
    return ok_n, mis, orph, supp

print("== M1' baseline survey ==")
exp_base = {("S0", True): (60, 12, 9), ("S0", False): (67, 14, 0)}
for strict, tag in ((True, "STRICT"), (False, "LOOSE")):
    ok_n, mis, orph, supp = survey("S0", strict)
    e = exp_base[("S0", strict)]
    verdict = "MATCH_PRECEDENT" if (ok_n, len(mis), len(orph)) == e else "DIVERGES %s" % (e,)
    print("  [S0-%s] OK=%d MISLABEL=%d ORPHAN=%d  vs _se_enum_out.txt 预期 %s -> %s"
          % (tag, ok_n, len(mis), len(orph), e, verdict))
    for pk, qk, cands, badr, badv in mis:
        print("    MIS %s x %s actual=%s claimants=%s bad=%s vals=%s"
              % (pk, qk, list(grid[(pk, qk)]), cands, badr, badv))
    for pk, qk in orph:
        print("    ORP %s x %s actual=%s" % (pk, qk, list(grid[(pk, qk)])))

print("== M2' scenario tallies (writer claims in parentheses) ==")
EXPECT = {
    ("T4", True): (61, 0, 20, 0), ("T4", False): (81, 0, 0, 0),
    ("U", True): (61, 3, 17, 1), ("U", False): (81, 0, 0, 2),
    ("U2only", True): (60, 4, 17, 0), ("U2only", False): (77, 4, 0, 0),
    ("U3only", True): (61, 11, 9, 1), ("U3only", False): (69, 12, 0, 2),
    ("U4only", True): (60, 12, 9, 0), ("U4only", False): (69, 12, 0, 0),
    ("P3", True): (63, 12, 6, 0), ("P3", False): (67, 14, 0, 0),
    ("P4", True): (69, 12, 0, 0), ("P4", False): (67, 14, 0, 0),
    ("PT", True): (75, 0, 6, 0), ("PT", False): (81, 0, 0, 0),
}
allmatch = True
for scn in ("T4", "U", "U2only", "U3only", "U4only", "P3", "P4", "PT"):
    for strict, tag in ((True, "strict"), (False, "loose")):
        ok_n, mis, orph, supp = survey(scn, strict)
        got = (ok_n, len(mis), len(orph), supp)
        e = EXPECT[(scn, strict)]
        m = got == e
        allmatch = allmatch and m
        print("  [%s-%s] rows=%d OK/M/O/supp=%d/%d/%d/%d  expect=%s  %s"
              % (scn, tag, ROWS_N[scn], got[0], got[1], got[2], got[3], e,
                 "MATCH" if m else "MISMATCH"))
        if not m:
            for pk, qk, cands, badr, badv in mis:
                print("    MIS %s x %s claimants=%s bad=%s" % (pk, qk, cands, badr))
            for pk, qk in orph:
                print("    ORP %s x %s" % (pk, qk))
print("SCENARIO_SUMMARY", "ALL_MATCH" if allmatch else "HAS_MISMATCH")

print("== M3' reachable-6 states per scenario (strict) ==")
REACH6 = [("none", "re_none"), ("none", "re_true"), ("error", "re_none"),
          ("error", "re_true"), ("absent", "re_true"), ("absent", "re_none")]
for scn in ("S0", "T4", "U", "P3", "P4", "PT"):
    sts = []
    for pk, qk in REACH6:
        cands = claimants(pk, qk, True, scn)
        a = grid[(pk, qk)]
        if not cands:
            st = "ORP"
        elif all(row_vals(i, scn, True, pk, qk) == a for i in cands):
            st = "OK"
        else:
            st = "MIS"
        sts.append(st)
    print("  %-6s strict: %s" % (scn, " ".join("%s=%s" % (("%s x %s" % c), s)
                                               for c, s in zip(REACH6, sts))))
print("CFV_ENUM_DONE")
