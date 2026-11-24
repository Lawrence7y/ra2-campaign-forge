# -*- coding: utf-8 -*-
r"""_fpv_verify.py — 误报模式【独立复核员】自写只读复算脚本。

纪律：零真机 / 零采样 / 零 hook；只用 re + ast + hashlib + 静态文本 + json。
      保护件一律 ast.literal_eval / compile-exec 内存加载，sys.dont_write_bytecode=True。
      唯一写域 lead/fp_pattern_20261109/，产出前缀 _fpv_。不改任何对抗集/谓词/语料。

★ 本脚本不 import 也不采信 _fp_recompute.py / _fp_classify.py 的任何计算结果，
  只对原始源码 + 原始 JSON 数据做独立重算；对照编排方 9 件指纹与 _fp_ 回件声明。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpv_verify.py
      > D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpv_verify_stdout.txt 2>&1
"""
import sys, json, hashlib, re, ast, types, math
from pathlib import Path
from collections import Counter

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_pattern_20261109"
AI = ROOT / "lead" / "advset_indep_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

OUT = {}
def emit(k, v):
    OUT[k] = v
    print("[%s] %s" % (k, json.dumps(v, ensure_ascii=False)))

def sha(rel):
    b = (ROOT / rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

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

def load_src(name, path):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), m.__dict__)
    return m

# ================= (A) 独立实算指纹（16 件 + 编排方 9 件比对） =================
print("=== (A) 指纹独立实算（hashlib.sha256） ===")
BIND = [
 "lead/advset_indep_20261109/_AI_ADVSET_INDEPENDENCE.md",
 "lead/advset_indep_20261109/_ai_grade_out.json",
 "lead/advset_indep_20261109/_ai_verify_stdout.txt",
 "lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md",
 "lead/advset_indep_20261109/_ai_verify_out.json",
 "lead/advset_indep_20261109/_ai_grade.py",
 "lead/advset_indep_20261109/_ai_verify.py",
 "lead/dg_adversarial_20261109/_dga_adversarial_out.json",
 "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md",
 "lead/dg_adversarial_20261109/_dga_adversarial.py",
 "lead/dneg_generative_20261109/_dg_core.py",
 "lead/dneg_generative_20261109/DNEG_GENERATIVE.md",
 "lead/h5_governance_20261109/_h5_pasteable.py",
 "lead/gate_fp7_20261108/_g7_predicates.py",
 "lead/PENDING_DECISIONS.md",
 "lead/GOAL_THREE_TARGETS_20261018.md",
]
F = {}
for rel in BIND:
    h, n = sha(rel)
    F[rel] = {"sha256": h, "bytes": n}
    print("  [%s]" % rel)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h, n))

# 编排方 9 件基线（从本次被核对象【编排方指纹】逐字录入，不采信 _fp_ 脚本内 ORCH）
ORCH9 = {
 "lead/advset_indep_20261109/_AI_ADVSET_INDEPENDENCE.md": ("668f4606f1a54c51433074f6271b3ee336acee7348aab89e91b75a46e6557b6f", 41557),
 "lead/advset_indep_20261109/_ai_grade_out.json": ("f3e52f828c3c75875ed82fb41c5d38d04419e3c1e87a5ce01b6b1f3f1ea27298", 28117),
 "lead/advset_indep_20261109/_ai_verify_stdout.txt": ("a7bbb835b9cca4dafb2bfd27d1959aa4b139a8a0f532b14d726411a66f800cea", 43943),
 "lead/dg_adversarial_20261109/_dga_adversarial_out.json": ("395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c", 55528),
 "lead/dneg_generative_20261109/_dg_core.py": ("7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322),
 "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
 "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
rows9 = []
for rel, (h0, n0) in ORCH9.items():
    h, n = F[rel]["sha256"], F[rel]["bytes"]
    rows9.append({"path": rel.split("/")[-1], "sha_match": h == h0, "bytes_match": n == n0,
                  "declared_bytes": n0, "actual_bytes": n})
emit("orch9_fingerprint_check", {"n": 9, "all_sha_match": all(z["sha_match"] for z in rows9),
     "all_bytes_match": all(z["bytes_match"] for z in rows9),
     "mismatch": [z["path"] for z in rows9 if not (z["sha_match"] and z["bytes_match"])],
     "rows": rows9})
# 与 _fp_recompute_stdout.txt 申报的 5 条主绑定行比对（格式/值）
bind5 = {
 "ADVSET_INDEPENDENCE.md": "2e60c913ceb2755fef4cb42020c3362ff63e0acbaa99541012ab7a361c8a232a",
 "_ai_grade_out.json": "f3e52f828c3c75875ed82fb41c5d38d04419e3c1e87a5ce01b6b1f3f1ea27298",
 "_dga_adversarial_out.json": "395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c",
 "_dg_core.py": "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1",
 "_h5_pasteable.py": "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c",
}
b5 = {}
for name, h0 in bind5.items():
    rel = next(r for r in BIND if r.endswith("/" + name))
    b5[name] = F[rel]["sha256"] == h0
emit("declared_5_bindlines_match", {"all": all(b5.values()), "by_file": b5})

# ================= (B) 独立重跑 41 条 × 6 判定器 =================
print("\n=== (B) 41 条 × 6 判定器独立重跑（自写 detect） ===")
DG = load_src("_fpv_dg", DG_DIR / "_dg_core.py")
H5 = load_src("_fpv_h5", H5P)
G7 = load_src("_fpv_g7", G7P)
DROP = load_src("_fpv_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
A = lit_assigns(DGA / "_dga_adversarial.py")
CASES, FORCED = A["CASES"], A["FORCED"]
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
DET = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]

def my_detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {k: "PASS" for k in DET}
    hits = {}
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    hits["DG_pure"] = h[0]["hit"] if h else ""
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hits["H5_lit"] = ml.group(0) if ml else ""
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"
    hits["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12_lit"] = m12.group(0) if m12 else ""
    return r, hits

rr = []
for cid, shape, text, exp, why, attack in CASES:
    r, hits = my_detect(text)
    rr.append({"id": cid, "text": text, "expect": exp, "forced": FORCED.get(cid, exp),
               "shape": shape, "why": why, "attack": attack,
               "verdicts": r, "hits": hits})

def my_score(key, forced=False):
    fp, fn, amb, fpi, fni = 0, 0, 0, [], []
    for x in rr:
        e = x["forced"] if forced else x["expect"]
        if e == "AMBIG" and not forced:
            amb += 1; continue
        g = x["verdicts"][key]
        if e == "PASS" and g == "CATCH": fp += 1; fpi.append(x["id"])
        elif e == "CATCH" and g == "PASS": fn += 1; fni.append(x["id"])
    return {"n": len(rr) - amb, "amb_excluded": amb, "fp": fp, "fn": fn,
            "fp_ids": fpi, "fn_ids": fni}

S = {k: my_score(k) for k in DET}
D = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
cmp = {}
for k in DET:
    a, b = S[k], D["scoring_strict"][k]
    cmp[k] = {"mine": [a["fp"], a["fn"], a["fp_ids"], a["fn_ids"]],
              "orch": [b["fp"], b["fn"], b["fp_ids"], b["fn_ids"]],
              "identical": (a["fp"], a["fn"], a["fp_ids"], a["fn_ids"]) ==
                           (b["fp"], b["fn"], b["fp_ids"], b["fn_ids"])}
emit("fpv_strict_vs_orch", {"n_cases": len(rr),
     "all_identical": all(z["identical"] for z in cmp.values()),
     "by_detector": {k: {"fp": S[k]["fp"], "fn": S[k]["fn"], "identical": z["identical"]}
                     for k, z in cmp.items()}})
emit("fpv_DG_pure_strict", S["DG_pure"])
# 与 _ai_verify_out.json 逐条 verdicts 比对（第二独立源）
vverd = {x["id"]: x["verdicts"] for x in V["rows"]}
vdiff = [(x["id"], k) for x in rr for k in DET if x["verdicts"][k] != vverd[x["id"]][k]]
emit("fpv_verdicts_vs_verify_json", {"n_cases": len(rr), "n_detectors": len(DET),
     "n_diff": len(vdiff), "diff": vdiff[:20]})

# ================= (C) d1 / d3 构式对应独立复算 =================
print("\n=== (C) 分级 + d1 / d3 构式对应独立复算 ===")
byid = {r["id"]: r for r in G["rows"]}
verd = {x["id"]: x["verdicts"]["DG_pure"] for x in rr}

# 严格分级函数（照 _ai_grade.py:134-139 的分支，独立抄写）
def my_grade(r):
    if r["min_edit"] == 0: return "belowL0"
    if r["d1"] or r["d3_pure"] or r["d3_dropin"]: return "L0"
    if r["d2"]: return "L1"
    if r["lcs_train"].get("len", 0) >= 4 or r["min_edit"] <= 5: return "L2"
    return "L3"
sd = Counter(my_grade(r) for r in G["rows"])
sd_full = {lv: sd.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")}
ld = Counter(r["grade"] for r in V["grade_rows"])
ld_full = {lv: ld.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")}
emit("fpv_grade_recompute", {"strict": sd_full, "strict_stored": G["grade_distribution"],
     "loose": ld_full, "loose_stored": V["grade_distribution"],
     "strict_match": sd_full == {"L0": 24, "L1": 17, "L2": 0, "L3": 0},
     "loose_match": ld_full == {"L0": 33, "L1": 8, "L2": 0, "L3": 0}})

# 7 条 fp 逐条 d1/d3/hit/min_edit/attack
FP = S["DG_pure"]["fp_ids"]
fp_rows = []
for c in FP:
    r = byid[c]
    fp_rows.append({"id": c, "expect": r["expect"], "verdict": verd[c],
                    "d1": r["d1"], "d1_nonempty": bool(r["d1"]),
                    "d3_pure": r["d3_pure"], "d3_dropin": r["d3_dropin"],
                    "hit": r["hit_pure"], "min_edit": r["min_edit"],
                    "grade": r["grade"], "attack": next(x["attack"] for x in rr if x["id"] == c)})
emit("fpv_fp7_rows", fp_rows)
emit("fpv_fp7_all_d1_nonempty", all(z["d1_nonempty"] for z in fp_rows))
emit("fpv_fp7_all_d3_true", all(z["d3_pure"] and z["d3_dropin"] for z in fp_rows))

# d3 恒真：CATCH ⇔ hit非空 ⇔ d3_pure（独立遍历 41 条）
taut = []
for x, s in zip(V["rows"], V["share_rows"]):
    hit = bool(x["hits"]["DG_pure"])
    catch = x["verdicts"]["DG_pure"] == "CATCH"
    if hit != catch or (hit and not s["pure_decomposable"]):
        taut.append(x["id"])
emit("fpv_d3_tautology", {"n_mismatch": len(taut), "ids": taut,
     "n_catch": sum(1 for x in V["rows"] if x["verdicts"]["DG_pure"] == "CATCH"),
     "n_d3_pure_true": sum(1 for s in V["share_rows"] if s["pure_decomposable"])})

# d1 空全 41 条口径：判对/判错，按 expect 分组
d1e = [r for r in G["rows"] if not r["d1"]]
d1e_neg = [r for r in d1e if r["expect"] == "PASS"]
d1e_pos = [r for r in d1e if r["expect"] == "CATCH"]
def correct(r): return byid[r["id"]]["expect"] == verd[r["id"]]
emit("fpv_d1_empty_full41", {"n": len(d1e),
     "ids": [r["id"] for r in d1e],
     "n_neg": len(d1e_neg), "neg_all_correct": sum(1 for r in d1e_neg if correct(r)),
     "n_pos": len(d1e_pos), "pos_all_correct": sum(1 for r in d1e_pos if correct(r)),
     "pos_fn_ids": [r["id"] for r in d1e_pos if not correct(r)],
     "all_correct": all(correct(r) for r in d1e)})
emit("fpv_d1_nonempty_correct_negatives",
     [{"id": r["id"], "d1": r["d1"], "min_edit": r["min_edit"], "verdict": verd[r["id"]]}
      for r in G["rows"] if r["d1"] and r["expect"] == "PASS" and verd[r["id"]] == "PASS"])

# 17 条 PASS 负样本 2x2 + Fisher 单侧
neg = [r for r in G["rows"] if r["expect"] == "PASS"]
a = sum(1 for r in neg if r["d1"] and verd[r["id"]] == "CATCH")
b = sum(1 for r in neg if r["d1"] and verd[r["id"]] == "PASS")
c = sum(1 for r in neg if not r["d1"] and verd[r["id"]] == "CATCH")
d = sum(1 for r in neg if not r["d1"] and verd[r["id"]] == "PASS")
fisher = math.comb(a+b, a) * math.comb(c+d, c) / math.comb(a+b+c+d, a+c)
emit("fpv_contingency_17", {"n": len(neg), "d1plus_fp": a, "d1plus_ok": b,
     "d1minus_fp": c, "d1minus_ok": d,
     "P_fp_given_d1plus": round(a/(a+b), 4), "P_fp_given_d1minus": round(c/(c+d), 4),
     "fisher_one_sided": round(fisher, 8)})

# min_edit 单调性
fp_me = sorted(r["min_edit"] for r in neg if verd[r["id"]] == "CATCH")
ok_me = sorted(r["min_edit"] for r in neg if verd[r["id"]] == "PASS")
emit("fpv_min_edit", {"fp_me": fp_me, "ok_me": ok_me,
     "overlap": sorted(set(fp_me) & set(ok_me)),
     "viol_inc": sum(1 for x in fp_me for y in ok_me if x > y),
     "viol_dec": sum(1 for x in fp_me for y in ok_me if x < y)})

# 文档统计复算
emit("fpv_doc_stats", {"d1_nonempty": sum(1 for r in G["rows"] if r["d1"]),
     "d2_nonempty": sum(1 for r in G["rows"] if r["d2"]),
     "d3_any": sum(1 for r in G["rows"] if r["d3_pure"] or r["d3_dropin"]),
     "d1_or_d3": sum(1 for r in G["rows"] if r["d1"] or r["d3_pure"] or r["d3_dropin"]),
     "lcs_ge6": sum(1 for r in G["rows"] if r["lcs_train"].get("len", 0) >= 6),
     "exact_overlap": D["novelty"]["exact_overlap"],
     "all_pure_hit_decomposable": all(s["pure_decomposable"] for s in V["share_rows"] if s["hit_DG_pure"])})

# ================= (D) 第二步(a)：两侧证据的独立实跑 =================
print("\n=== (D) 第二步(a) 因果 vs 构造偏差：两侧独立实跑证据 ===")
# 侧 A：14 未登记边界词 / 10 已登记词（自写受控替换，固定表内构式不变）
MY_BREAK = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究",
            "总而言之", "归根结底", "话说回来", "退一步说", "哪怕", "说白了"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
probe_unreg = []
for w in MY_BREAK:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = my_detect(t)
    probe_unreg.append({"w": w, "in_BREAK_RE": bool(DG.DG_BREAK_RE.search(w)),
                        "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"]})
probe_reg = []
for w in BREAK10:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = my_detect(t)
    probe_reg.append({"w": w, "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"]})
emit("fpv_sideA_boundary_probe", {
  "unreg_n": len(probe_unreg),
  "unreg_BREAK_false_and_pure_CATCH": sum(1 for z in probe_unreg if not z["in_BREAK_RE"] and z["DG_pure"] == "CATCH"),
  "unreg_all_pure_CATCH": all(z["DG_pure"] == "CATCH" for z in probe_unreg),
  "reg_n": len(probe_reg),
  "reg_pure_PASS": sum(1 for z in probe_reg if z["DG_pure"] == "PASS"),
  "reg_dropin_CATCH": sum(1 for z in probe_reg if z["DG_dropin"] == "CATCH"),
  "unreg_detail": [(z["w"], z["DG_pure"]) for z in probe_unreg],
  "reg_detail": [(z["w"], z["DG_pure"], z["DG_dropin"]) for z in probe_reg]})

# 侧 A2：DG_DROPIN_RE 是否只由闭合表生成（静态检视 pattern 结构）
dg_src = (DG_DIR / "_dg_core.py").read_text(encoding="utf-8")
emit("fpv_sideA_regex_provenance", {
  "pattern_chars": len(DG.DG_PATTERN), "stats": DG.DG_STATS,
  "t12_zero_wildcard_claim": "T12 = veto+NEG1+MID+NEG2 全字面；唯一通配 comp{0,4}? 在 T3（_dg_core.py:118-128）",
  "all_pure_hit_decomposable": all(s["pure_decomposable"] for s in V["share_rows"] if s["hit_DG_pure"])})

# 侧 B：d1 目录内生 —— 独立重建 CATALOG 来源（读 _ai_grade.py:48-58 的赋值）
grade_src_lines = (AI / "_ai_grade.py").read_text(encoding="utf-8").splitlines()
emit("fpv_sideB_d1_catalog_lines", {"lines_48_58": [grade_src_lines[i-1].rstrip() for i in range(48, 59)],
     "line_103": grade_src_lines[102].rstrip(),
     "line_91": grade_src_lines[90].rstrip()})

# 侧 B：构造者读源码行号 —— 独立计数
attack_nonempty = sum(1 for x in rr if x["attack"])
why_core_line = sum(1 for x in rr if "_dg_core.py:" in x["why"])
why_table = sum(1 for x in rr if re.search(r"DG_BREAK_RE|_BQ|_SECOND|DG_QUOTE_RE|DG_COORD_RE|NEG2|PSEUDO|MID|_g7_predicates.py|:\d+", x["why"]))
fp_attack_all = all(next(x["attack"] for x in rr if x["id"] == c) for c in FP)
emit("fpv_sideB_construction_provenance", {"attack_nonempty": attack_nonempty,
     "why_core_line": why_core_line, "why_table_or_lineno": why_table,
     "n": len(rr), "fp7_attack_all_nonempty": fp_attack_all})

# 侧 B：跨判定器 fp 是否全部落在 d1 非空（六判定器逐一）
cross = {}
for k in DET:
    fpi, fni = S[k]["fp_ids"], S[k]["fn_ids"]
    cross[k] = {"fp": S[k]["fp"], "fn": S[k]["fn"],
                "fp_all_d1_nonempty": all(byid[c]["d1"] for c in fpi),
                "fp_d1_empty_ids": [c for c in fpi if not byid[c]["d1"]],
                "fn_d1_nonempty_ids": [c for c in fni if byid[c]["d1"]]}
emit("fpv_sideB_cross_detector_fp", cross)

# H5 / R12 是否零学习：独立统计手写支与 fp 命中串
h5_lit = lit_assigns(H5P)
branches = [b for b in (h5_lit["H5_R12_TEN"] + "|" + h5_lit["H5_DN_EXTRA"]).split("|")
            if b and "[^" not in b]
h5_hits = {x["id"]: x["hits"]["H5_lit"] for x in rr}
h5_fp_hits = {c: h5_hits[c] for c in S["H5_lit"]["fp_ids"]}
emit("fpv_sideB_H5", {"H5_lit_fp": S["H5_lit"]["fp"], "H5_gov_fp": S["H5_gov"]["fp"],
     "R12_fp": S["R12"]["fp"], "R12_lit_fp": S["R12_lit"]["fp"],
     "h5_literal_branches_n": len(branches),
     "h5_fp_hits": h5_fp_hits,
     "h5_fp_hits_all_from_literal_table": all(any(b == h or b in h for b in branches) for h in h5_fp_hits.values()),
     "r12_fp_ids": S["R12"]["fp_ids"],
     "h5_src_lines_31_40": [(ROOT / "lead/h5_governance_20261109/_h5_pasteable.py").read_text(encoding="utf-8").splitlines()[i-1].rstrip() for i in range(31, 41)]})

# ================= (E) 第三步(c)：fp7 / fn11 逐条分类独立核 =================
print("\n=== (E) 第三步(c) fp/fn 逐条分类（独立按 why/src 与源码行核对） ===")
FN = S["DG_pure"]["fn_ids"]
why = {x["id"]: x["why"] for x in rr}
fp_class = []
for c in FP:
    r = byid[c]
    fp_class.append({"id": c, "expect": "PASS", "verdict": verd[c], "d1": r["d1"],
                     "d3_pure": r["d3_pure"], "hit": r["hit_pure"],
                     "type": "过宽/护栏污染", "why": why[c]})
fn_class = []
for c in FN:
    r = byid[c]
    fn_class.append({"id": c, "expect": "CATCH", "verdict": verd[c], "d1": r["d1"],
                     "d3_pure": r["d3_pure"], "hit": r["hit_pure"], "why": why[c]})
emit("fpv_fp7_individual", fp_class)
emit("fpv_fn11_individual", fn_class)
emit("fpv_class_counts", {"fp_n": len(FP), "fn_n": len(FN),
     "fp_all_d1_nonempty": all(z["d1"] for z in fp_class),
     "fn_d1_empty": sum(1 for z in fn_class if not z["d1"]),
     "fn_d1_nonempty_ids": [z["id"] for z in fn_class if z["d1"]]})

# ================= (F) 第四步(b)/(c) 文档条款定位核对 =================
print("\n=== (F) 第四步(b)/(c) 条款定位 ===")
def readlines(rel, rng):
    ls = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return {i: ls[i-1][:180] for i in rng if i <= len(ls)}
emit("fpv_heldout_doc_lines", {
  "ADVSET_542_550": readlines("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", range(542, 551)),
  "ADVSET_559": readlines("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", [559]),
  "ADVSET_569_571": readlines("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", range(569, 572)),
  "ADVSET_588": readlines("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", [588]),
  "ADVSET_604": readlines("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", [604]),
  "DGA_308": readlines("lead/dg_adversarial_20261109/DG_ADVERSARIAL.md", [308])})
emit("fpv_h5_doc_lines", {
  "H5PASTE_31_40": readlines("lead/h5_governance_20261109/_h5_pasteable.py", range(31, 41)),
  "G7_76": readlines("lead/gate_fp7_20261108/_g7_predicates.py", [76])})

# ================= 写盘 =================
(WD / "_fpv_verify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fpv_verify_out.json")
