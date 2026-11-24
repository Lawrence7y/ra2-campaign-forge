# -*- coding: utf-8 -*-
# _fdv_e1e5v.py — 复核员独立重跑 E1（2×2 全矩阵 100 条）+ E5（7 条表内构式+正确切断负对照）
#   + 41 条语料引号字符普查（核第一步(d)「4 类引号」歧义）+ 最小实现唯一分歧定位。
# 只读保护件；输出 _fdv_e1e5_out.json；dont_write_bytecode。
import sys, os, json, re, ast, importlib.util
sys.dont_write_bytecode = True

ROOT = r"D:/Project/ra2-campaign-forge"
WD = ROOT + r"/lead/fp_discriminate_20261109"
SB = WD + r"/_fdv_sandbox"
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
out = {}

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

DG = load_mod("_fdv_dg_e1", SB + "/_fdv_dg_core_base.py")

src = open(ROOT + "/lead/dg_adversarial_20261109/_dga_adversarial.py", encoding="utf-8").read()
tree = ast.parse(src)
CASES = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if getattr(t, "id", None) == "CASES":
                CASES = [dict(id=c[0], text=c[2], expect=c[3]) for c in ast.literal_eval(node.value)]

def toks_of(text):
    return [t for t in TOKS if t in text] or ["已生效"]

def v(text):
    p, _ = DG.dg_scan(text, toks_of(text))
    return "CATCH" if p else "PASS"

# ================= E1: 2×2 全矩阵 =================
IN_CON = ["不敢不承认", "并不否认", "并非不承认", "不得不否认", "未尝不承认"]
OUT_CON = ["不容不承认", "未许不宣告", "别想不登记", "甭想不承认", "没准不承认"]
BW_REG = ["另外", "但是", "然而", "不过", "只是"]
BW_UNREG = ["其实", "说到底", "尽管", "哪怕", "反倒"]
standalone = {c: bool(DG.DG_DROPIN_RE.search(c)) for c in IN_CON + OUT_CON}
in_break = {w: bool(DG.DG_BREAK_RE.search(w)) for w in BW_REG + BW_UNREG}
print("[E1] standalone 命中 DG_DROPIN_RE：表内 %s" % {c: standalone[c] for c in IN_CON})
print("     表外 %s" % {c: standalone[c] for c in OUT_CON})
print("[E1] 边界词在 DG_BREAK_RE：已登记 %s" % {w: in_break[w] for w in BW_REG})
print("     未登记 %s" % {w: in_break[w] for w in BW_UNREG})
assert all(standalone[c] for c in IN_CON) and not any(standalone[c] for c in OUT_CON)
assert all(in_break[w] for w in BW_REG) and not any(in_break[w] for w in BW_UNREG)

rows, cells = [], {}
for con_cls, cons in (("表内", IN_CON), ("表外", OUT_CON)):
    for bw_cls, bws in (("已登记", BW_REG), ("未登记", BW_UNREG)):
        cell_catch = 0
        for con in cons:
            for bw in bws:
                t = con + bw + "本件不宣告已生效"
                g = v(t)
                cell_catch += (g == "CATCH")
                rows.append({"con_class": con_cls, "con": con, "bw_class": bw_cls, "bw": bw,
                             "text": t, "verdict": g})
        cells["%s×%s" % (con_cls, bw_cls)] = "%d/25 CATCH" % cell_catch
print("[E1] 四格 CATCH 率：G1 表内×已登记=%s ; G2 表内×未登记=%s ; G3 表外×已登记=%s ; G4 表外×未登记=%s"
      % (cells["表内×已登记"], cells["表内×未登记"], cells["表外×已登记"], cells["表外×未登记"]))
per_bw = {}
for r in rows:
    if r["con_class"] == "表内" and r["bw_class"] == "未登记":
        per_bw.setdefault(r["bw"], []).append(r["verdict"])
print("[E1] G2 格逐边界词明细：", {k: sum(1 for x in vv if x == "CATCH") for k, vv in per_bw.items()})
per_con = {}
for r in rows:
    if r["con_class"] == "表内" and r["bw_class"] == "未登记":
        per_con.setdefault(r["con"], []).append(r["verdict"])
print("[E1] G2 格逐构式明细：", {k: sum(1 for x in vv if x == "CATCH") for k, vv in per_con.items()})
out["e1"] = {"standalone": standalone, "in_break": in_break, "cells": cells,
             "rows": rows, "n": len(rows)}

# ================= E5: 表内构式 + 已登记切断（我自建 7 条） =================
E5 = [
    ("N1", "前稿不敢不承认，本件不宣告已生效", "，"),
    ("N2", "前稿不敢不承认但是本件不宣告已生效", "但是"),
    ("N3", "旧稿并不否认然而本件不宣告已生效", "然而"),
    ("N4", "「不敢不承认已生效」只是转述，本件不采信该说法", "「」"),
    ("N5", "“并不否认已生效”只是引文，本件不采信该说法", "“”"),
    ("N6", "`并非不宣告已生效`只是引文，本件不采信该说法", "反引号"),
    ("N7", "旧稿并不否认不过本件不宣告已生效", "不过"),
]
e5_rows = []
for nid, t, cut in E5:
    g = v(t)
    e5_rows.append({"id": nid, "text": t, "cut": cut, "verdict": g})
n_pass = sum(1 for r in e5_rows if r["verdict"] == "PASS")
print("[E5] 表内构式+正确切断 7 条：PASS %d/7 ；%s" % (n_pass, [(r["id"], r["verdict"]) for r in e5_rows]))
out["e5"] = e5_rows

# ================= 41 条引号字符普查（第一步(d)） =================
QUOTE_CHARS = ['"', "'", "《", "》", "「", "」", "『", "』", "“", "”", "`",
               "（", "）", "【", "】", "〈", "〉", "｢", "｣"]
qhit = {}
for c in CASES:
    for ch in QUOTE_CHARS:
        if ch in c["text"]:
            qhit.setdefault(ch, []).append(c["id"])
print("[引号普查] 41 条中出现的引号类字符 =", {k: v for k, v in qhit.items()})
print("[引号普查] 零出现的候选新增类 = %s" % [ch for ch in QUOTE_CHARS if ch not in qhit])
out["quote_chars_in_41"] = qhit

# ================= 最小实现 vs 原实现唯一分歧定位 =================
def my_mask_scope(pre):
    def blank(mm):
        g = mm.group(0)
        return g[0] + " " * (len(g) - 2) + g[-1]
    p = DG.DG_QUOTE_RE.sub(blank, pre)
    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`")):
        i = p.find(op)
        if i >= 0 and p.find(cl, i + 1) < 0:
            return p[:i + 1]
    return p

dis = []
for c in CASES:
    toks = toks_of(c["text"])
    mm0 = re.search(re.escape(toks[0]), c["text"])
    pre = c["text"][:mm0.start()]
    scope = my_mask_scope(pre)
    mine = bool(DG.DG_DROPIN_RE.search(scope))
    theirs = DG.dg_double_neg(pre)["hit"]
    if mine != theirs:
        m2 = DG.DG_DROPIN_RE.search(scope)
        dis.append({"id": c["id"], "text": c["text"], "my_raw_hit": m2.group(0) if m2 else "",
                    "their_hit": theirs,
                    "their_reason": DG.dg_double_neg(pre)["reason"]})
print("[分歧定位] raw 正则命中 vs dg_double_neg 二次 veto 分歧 %d 条：%s"
      % (len(dis), [(d["id"], d["my_raw_hit"], d["their_reason"][:30]) for d in dis]))
out["raw_vs_veto_disagreement"] = dis

json.dump(out, open(WD + "/_fdv_e1e5_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written: _fdv_e1e5_out.json")
