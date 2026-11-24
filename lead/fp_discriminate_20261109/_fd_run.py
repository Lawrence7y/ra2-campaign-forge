# -*- coding: utf-8 -*-
r"""_fd_run.py — 判别实验总跑件（E2 消融 / E1 2x2 / E5 扩样）。只写本任务写域。
素材来源：lead/dg_adversarial_20261109/_dga_adversarial.py 的 CASES（AST 字面抽取，只读）。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_run.py
"""
import sys, json, hashlib, re, ast, types
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SB = WD / "_fd_sandbox"
DGA = ROOT / "lead" / "dg_adversarial_20261109"

OUTS = {}
def emit(fname, key, val):
    OUTS.setdefault(fname, {})[key] = val
    print("[%s] %s" % (key, json.dumps(val, ensure_ascii=False)[:400]))

def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

BIND = [
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md",
    "lead/fp_pattern_20261109/_fp_recompute_out.json",
    "lead/dg_adversarial_20261109/_dga_adversarial_out.json",
    "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md",
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/dneg_generative_20261109/_dg_core.py",
    "lead/h5_governance_20261109/_h5_pasteable.py",
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md",
]
print("=== (0) 原件绑定行（实验前） ===")
fp_before = {}
for rel in BIND:
    h, n = sha(ROOT / rel)
    fp_before[rel] = {"sha256": h, "bytes": n}
    print("被核对象 SHA256 = %s，字节数 = %d  (%s)" % (h, n, rel))

def load_src(name, path):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), m.__dict__)
    return m

def lit_assigns(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Name):
                    try: out[tgt.id] = ast.literal_eval(n.value)
                    except Exception: pass
    return out

# ---------- 41 条全集（只读抽取） ----------
A = lit_assigns(DGA / "_dga_adversarial.py")
CASES, FORCED = A["CASES"], A["FORCED"]
CASE_BY_ID = {c[0]: {"id": c[0], "shape": c[1], "text": c[2], "expect": c[3],
                     "why": c[4], "attack": c[5]} for c in CASES}
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

# ---------- 本任务自写 detect（调用方式：dg_scan / 换行 r12_scan 双口径） ----------
def make_detect(DG, G7):
    G7.DOUBLE_NEG_RE = DG.DG_DROPIN_RE          # DG_dropin = 交付形态「只换 :76 一行」
    def detect(text):
        toks = [t for t in TOKS if t in text] or ["已生效"]
        p, h = DG.dg_scan(text, toks)
        pd, _ = G7.r12_scan(text, toks)
        return {"DG_pure": "CATCH" if p else "PASS",
                "DG_pure_hit": h[0]["hit"] if h else "",
                "DG_dropin": "CATCH" if pd else "PASS", "toks": toks}
    return detect

def run_all(core_path, g7_path):
    DG = load_src("fd_dg", core_path)
    G7 = load_src("fd_g7", g7_path)
    det = make_detect(DG, G7)
    rows = []
    for cid in sorted(CASE_BY_ID):
        c = CASE_BY_ID[cid]
        v = det(c["text"])
        rows.append({"id": cid, "expect": c["expect"], "text": c["text"],
                     "DG_pure": v["DG_pure"], "DG_pure_hit": v["DG_pure_hit"],
                     "DG_dropin": v["DG_dropin"]})
    return DG, G7, det, rows

def strict_score(rows, key="DG_pure"):
    fp, fn, fpi, fni, amb = 0, 0, [], [], []
    for x in rows:
        if x["expect"] == "AMBIG":
            amb.append(x["id"]); continue
        if x["expect"] == "PASS" and x[key] == "CATCH":
            fp += 1; fpi.append(x["id"])
        elif x["expect"] == "CATCH" and x[key] == "PASS":
            fn += 1; fni.append(x["id"])
    return {"n": len(rows) - len(amb), "amb_excluded": amb, "fp": fp, "fn": fn,
            "fp_ids": fpi, "fn_ids": fni}

# ==================== (1) 第一步：素材复核 ====================
print("\n=== (1a) 编排方给的 26 条 vs CASES 原文逐条比对 ===")
ASK = {
 "fp": [("P06","前稿不敢不承认其实本件不宣告已生效"),("P07","前稿不敢不承认说到底本件不宣告已生效"),
        ("P08","旧稿并不否认尽管本件不宣告已生效"),("P09","旧稿并不否认与监理方不宣告已生效"),
        ("P10","本件不承认或并不否认已生效"),("P11","\"并非不宣告已生效\"只是引文，本件不采信该说法"),
        ("P12","《并不否认已生效》只是引文，本件不采信该说法")],
 "fn": [("C01","不容不宣告本件已生效"),("C02","未许不宣告本件已生效"),("C03","别想不登记本件已入账"),
        ("C04","甭想不承认本件已生效"),("C05","没准不承认本件已生效"),
        ("C07","非登记五份原始件不可才算本件已生效"),("C08","非登记一或二不可才算本件已生效"),
        ("C09","非登记本件不可才算本件已生效"),("C10","并非本件不宣告已生效"),
        ("C11","非不承认本件已生效"),("C12","非不认可本件已生效")],
 "neg_ok": [("P01","旧稿不承认，本件不宣告已生效"),("P02","旧稿未登记、本件亦未宣告已生效"),
            ("P03","无越权断言，也不出现放行 N-5 类措辞，本件不采信已生效"),
            ("P04","前段不采信母本后段不宣告本件已生效"),("P05","不核不录，本件不采信已生效"),
            ("P13","既不宣告旧稿已入账，也不宣告本件已生效"),("P14","不予登记亦不宣告本件已生效"),
            ("P15","旧稿不承认，但本件也不宣告已生效")],
}
mat = {}
for grp, items in ASK.items():
    rows = []
    for cid, txt in items:
        c = CASE_BY_ID.get(cid)
        rows.append({"id": cid, "ask_text": txt, "cases_text": c["text"] if c else None,
                     "expect_cases": c["expect"] if c else None,
                     "identical": bool(c) and c["text"] == txt, "expect_in_ask": "PASS" if grp != "fn" else "CATCH"})
    mat[grp] = rows
    print("  %s: n=%d identical=%d" % (grp, len(rows), sum(1 for r in rows if r["identical"])))
missing = [cid for cid in ("P16", "P17", "C06", "C13", "C14", "C15", "C16", "C17", "C18", "C19",
           "C20", "A01", "A02", "A03", "A04") if cid not in ASK.get("fp", []) + [i[0] for i in ASK["fn"]] + [i[0] for i in ASK["neg_ok"]]]
emit("_fd_material_out.json", "material_check", {
    "n_cases_total": len(CASES), "expect_dist": {e: sum(1 for c in CASES if c[3] == e) for e in ("PASS", "CATCH", "AMBIG")},
    "groups": mat,
    "ids_not_in_ask_material": missing,
    "all_26_identical": all(r["identical"] for g in mat.values() for r in g)})

print("\n=== (1c) 护栏常量逐个列出（自沙箱底版核读取） ===")
DG0, G70, DET0, ROWS0 = run_all(SB / "_dg_core_base.py", SB / "_g7_predicates_base.py")
consts = {
 "NEG1_n": len(set(DG0.NEG1)), "NEG1": list(DG0.NEG1),
 "MID_n": len(set(DG0.MID)), "MID": list(DG0.MID),
 "NEG2_n": len(set(DG0.NEG2)), "NEG2": list(DG0.NEG2),
 "PSEUDO_DN": list(DG0.PSEUDO_DN),
 "_BREAK": DG0._BREAK, "_BQ": DG0._BQ,
 "DG_BREAK_RE_pattern": DG0.DG_BREAK_RE.pattern,
 "DG_BREAK_RE_words": ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"],
 "_SECOND_raw": DG0._SECOND,
 "_SECOND_words": DG0._SECOND.split("|"),
 "DG_COORD_RE_pattern": DG0.DG_COORD_RE.pattern,
 "DG_QUOTE_RE_pattern": DG0.DG_QUOTE_RE.pattern,
 "GAP": list(DG0.GAP), "SCOPE_VERB_n": len(set(DG0.SCOPE_VERB)), "SPLIT_TAIL": list(DG0.SPLIT_TAIL),
 "R12_TEN": list(DG0.R12_TEN),
 "g7_NEG_WINDOW": G70.NEG_WINDOW, "g7_CLAUSE_BREAK": G70.CLAUSE_BREAK,
 "g7_DOUBLE_NEG_RE": G70.DOUBLE_NEG_RE.pattern if G70.DOUBLE_NEG_RE != DG0.DG_DROPIN_RE else "(swapped)",
 "g7_DOUBLE_NEG_RE_10": ["不得不", "并非不", "并不是不", "不是不", "无不", "没有不", "不无", "不能不", "不可不", "未曾不"],
 "g7_NEG_RE": G70.NEG_RE.pattern, "g7_SPAN_RE": G70.SPAN_RE.pattern, "g7_SELF_MARKERS": list(G70.SELF_MARKERS),
}
emit("_fd_material_out.json", "guard_constants", consts)

# ==================== (2) 第一步(b)：基线独立复现 ====================
print("\n=== (1b) 基线独立复现（自写 detect，41 条全集） ===")
sc0 = strict_score(ROWS0, "DG_pure")
sc0d = strict_score(ROWS0, "DG_dropin")
emit("_fd_baseline_out.json", "DG_pure_strict", sc0)
emit("_fd_baseline_out.json", "DG_dropin_strict", sc0d)
orch = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
o = orch["scoring_strict"]["DG_pure"]
same = (sc0["fp_ids"] == o["fp_ids"] and sc0["fn_ids"] == o["fn_ids"])
emit("_fd_baseline_out.json", "baseline_vs_orchestrator", {
    "my_fp_ids": sc0["fp_ids"], "my_fn_ids": sc0["fn_ids"],
    "orch_fp_ids": o["fp_ids"], "orch_fn_ids": o["fn_ids"], "identical": same})
print("\n".join("%s expect=%s DG_pure=%s dropin=%s hit=%r" % (r["id"], r["expect"], r["DG_pure"], r["DG_dropin"], r["DG_pure_hit"]) for r in ROWS0))

# fp 逐条根因独立确认（首命中 token 处 dg_double_neg 明细）
print("\n=== (1b+) 7 条 fp 根因独立确认 ===")
fp_detail = []
for cid in sc0["fp_ids"]:
    c = CASE_BY_ID[cid]
    toks = [t for t in TOKS if t in c["text"]] or ["已生效"]
    tok = toks[0]
    m = re.search(re.escape(tok), c["text"])
    pre, post = c["text"][:m.start()], c["text"][m.end():]
    r = DG0.dg_double_neg(pre, post)
    fp_detail.append({"id": cid, "token": tok, "hit": r["hit"], "hit_text": r["hit_text"],
                      "template": r["template"], "scope": r["scope"], "reason": r["reason"],
                      "second_subj_in_scope": bool(DG0.DG_SECOND_SUBJ_RE.search(r["scope"])),
                      "second_subj_in_hit": bool(DG0.DG_SECOND_SUBJ_RE.search(r["hit_text"])),
                      "coord_in_scope": bool(DG0.DG_COORD_RE.search(r["scope"])),
                      "coord_in_hit": bool(DG0.DG_COORD_RE.search(r["hit_text"])),
                      "coord_word_in_scope": (DG0.DG_COORD_RE.search(r["scope"]) or [None]) and (DG0.DG_COORD_RE.search(r["scope"]).group(0) if DG0.DG_COORD_RE.search(r["scope"]) else "")})
emit("_fd_baseline_out.json", "fp7_root_cause_detail", fp_detail)

# ==================== (3) 第二步：E2 消融五臂 ====================
print("\n=== (E2) 五臂消融 ===")
ARMS = [("base", SB / "_dg_core_base.py"),
        ("jia_护栏补数据", WD / "_fd_dg_core_jia.py"),
        ("jiac_甲加改代码veto整窗", WD / "_fd_dg_core_jiac.py"),
        ("yi_删构式NEG1侧", WD / "_fd_dg_core_yi.py"),
        ("yi2_删构式NEG2侧", WD / "_fd_dg_core_yi2.py")]
e2 = {"arms": {}}
base_rows = {r["id"]: r for r in ROWS0}
for name, path in ARMS:
    DG, G7, det, rows = run_all(path, SB / "_g7_predicates_base.py")
    sc = strict_score(rows, "DG_pure")
    scd = strict_score(rows, "DG_dropin")
    trans = []
    for r in rows:
        b = base_rows[r["id"]]
        if b["DG_pure"] != r["DG_pure"] or b["DG_dropin"] != r["DG_dropin"]:
            trans.append({"id": r["id"], "expect": r["expect"],
                          "DG_pure": "%s->%s" % (b["DG_pure"], r["DG_pure"]),
                          "DG_dropin": "%s->%s" % (b["DG_dropin"], r["DG_dropin"])})
    rten_ok = all(bool(DG.DG_DROPIN_RE.search(c)) for c in DG.R12_TEN)
    e2["arms"][name] = {"core_file": str(path), "DG_pure_strict": sc,
                        "DG_dropin_strict": scd, "changed_ids_vs_base": trans,
                        "R12_TEN_anchor_all_generated": rten_ok,
                        "verdicts": {r["id"]: [r["DG_pure"], r["DG_dropin"]] for r in rows}}
    print("%s: DG_pure fp=%d fn=%d fp_ids=%s fn_ids=%s ; dropin fp=%d fn=%d ; R12_TEN锚=%s ; changed=%s" % (
        name, sc["fp"], sc["fn"], sc["fp_ids"], sc["fn_ids"], scd["fp"], scd["fn"], rten_ok,
        [(t["id"], t["DG_pure"]) for t in trans]))
emit("_fd_e2_out.json", "e2_arms", e2["arms"])

# 隐藏代价探针（41 条集上看不见的）
print("\n=== (E2+) 隐藏代价探针 ===")
PROBES = [
 ("乙_真阳丢失A", "监管方不敢不承认本件已生效"),
 ("乙_真阳丢失B", "监理方并不否认本件已生效"),
 ("乙_真阳丢失C", "复审组并非不承认本件已生效"),
 ("甲_新断裂词撞名词", "非登记结果不可才算本件已生效"),
 ("甲_新断裂词撞名词2", "未尝不承认审核结果本件已生效"),
]
probe_rows = {}
for pname, ptext in PROBES:
    pr = {}
    for name, path in ARMS:
        DG, G7, det, _ = run_all(path, SB / "_g7_predicates_base.py")
        v = det(ptext)
        pr[name] = [v["DG_pure"], v["DG_pure_hit"]]
    probe_rows[pname] = {"text": ptext, "verdicts": pr}
    print("%s %r => %s" % (pname, ptext, pr))
emit("_fd_e2_out.json", "hidden_cost_probes", probe_rows)

# ==================== (4) 第三步：E1 2x2 析因 ====================
print("\n=== (E1) 表内/表外 x 边界已登记/未登记 ===")
NEI_IN = ["不敢不承认", "并不否认", "并非不承认", "不得不否认", "未尝不承认"]
NEI_OUT = ["不容不承认", "未许不宣告", "别想不登记", "甭想不承认", "没准不承认"]
BW_IN = ["另外", "但是", "然而", "不过", "只是"]
BW_OUT = ["其实", "说到底", "尽管", "哪怕", "反倒"]
e1 = {"construct_in_table_standalone": {}, "cells": {}}
for c in NEI_IN:
    e1["construct_in_table_standalone"][c] = bool(DG0.DG_DROPIN_RE.search(c))
for c in NEI_OUT:
    e1["construct_in_table_standalone"][c] = bool(DG0.DG_DROPIN_RE.search(c))
cells = {"G1_表内x已登记": (NEI_IN, BW_IN), "G2_表内x未登记": (NEI_IN, BW_OUT),
         "G3_表外x已登记": (NEI_OUT, BW_IN), "G4_表外x未登记": (NEI_OUT, BW_OUT)}
for gname, (cs, bs) in cells.items():
    rows = []
    for c in cs:
        for b in bs:
            t = c + b + "本件不宣告已生效"
            v = DET0(t)
            rows.append({"construct": c, "boundary": b, "text": t,
                         "DG_pure": v["DG_pure"], "hit": v["DG_pure_hit"]})
    n_catch = sum(1 for r in rows if r["DG_pure"] == "CATCH")
    e1["cells"][gname] = {"n": len(rows), "catch": n_catch,
                          "catch_rate": round(n_catch / len(rows), 4), "rows": rows}
    print("%s: %d/%d CATCH" % (gname, n_catch, len(rows)))
emit("_fd_e1_out.json", "e1", e1)

# ==================== (5) 第四步：E5 负对照扩样 ====================
print("\n=== (E5) 表内构式 + 正确切断 负样本 7 条 ===")
E5 = [
 ("N1", "旧稿不敢不承认，但是本件不宣告已生效", "已登记断裂：，+但是"),
 ("N2", "旧稿并不否认，然而本件不宣告已生效", "已登记断裂：，+然而"),
 ("N3", "“并非不宣告已生效”只是引文，本件不采信该说法", "已登记引号：“”"),
 ("N4", "「并不否认已生效」只是引文，本件不采信该说法", "已登记引号：「」"),
 ("N5", "`不敢不承认已生效`只是引文，本件不采信该说法", "已登记引号：反引号"),
 ("N6", "前稿不敢不承认，本件不宣告已生效", "已登记断裂：，"),
 ("N7", "旧稿并不否认，本件不宣告已生效", "已登记断裂：，+第二主语后置"),
]
e5 = []
for nid, txt, cut in E5:
    v = DET0(txt)
    cons = next((c for c in NEI_IN if c in txt), "")
    e5.append({"id": nid, "text": txt, "cut_device": cut, "construct": cons,
               "construct_in_table": bool(DG0.DG_DROPIN_RE.search(cons)) if cons else None,
               "DG_pure": v["DG_pure"], "hit": v["DG_pure_hit"]})
emit("_fd_e5_out.json", "e5", {"n": len(e5), "pass_n": sum(1 for r in e5 if r["DG_pure"] == "PASS"),
                               "rows": e5})
for r in e5:
    print("%s %s => %s (hit=%r)" % (r["id"], r["text"], r["DG_pure"], r["hit"]))

# ==================== (6) 原件复核（实验后） ====================
print("\n=== (6) 原件复核（实验后） ===")
drift = []
for rel in BIND:
    h, n = sha(ROOT / rel)
    ok = (h == fp_before[rel]["sha256"] and n == fp_before[rel]["bytes"])
    if not ok: drift.append(rel)
    print("被核对象 SHA256 = %s，字节数 = %d  (%s) %s" % (h, n, rel, "OK" if ok else "DRIFTED"))
emit("_fd_material_out.json", "originals_unchanged_after_all", {"drift": drift})

for fname, obj in OUTS.items():
    (WD / fname).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written: %s" % fname)
