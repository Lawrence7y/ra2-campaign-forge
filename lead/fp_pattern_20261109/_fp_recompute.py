# -*- coding: utf-8 -*-
r"""_fp_recompute.py — 误报模式分析员：只读独立复算（不改任何对抗集/谓词/语料）。

纪律：零真机 / 零采样代码 / 零 hook；只 re + ast + 静态文本 + hashlib。
      ★ 保护件一律 compile/exec 内存加载或 AST 字面抽取，sys.dont_write_bytecode=True，
        绝不写 __pycache__，绝不写保护树。唯一写域 lead/fp_pattern_20261109/。
      ★ 不执行第二步(d) 的判别实验（消融/交叉）；本件只复算既有 41 条既有数据。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fp_recompute.py
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

def lev(a, b):
    if a == b: return 0
    if len(a) < len(b): a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

# ==================== (0) 绑定指纹（本会话 hashlib 独立重算） ====================
print("=== (0) 被核对象绑定行 ===")
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
fingerprints = {}
for rel in BIND:
    h, n = sha(rel)
    fingerprints[rel] = {"sha256": h, "bytes": n}
    print("  [%s]" % rel)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h, n))
OUT["fingerprints"] = fingerprints

ORCH = {
 "lead/advset_indep_20261109/_AI_ADVSET_INDEPENDENCE.md": "668f4606f1a54c51433074f6271b3ee336acee7348aab89e91b75a46e6557b6f",
 "lead/advset_indep_20261109/_ai_grade_out.json": "f3e52f828c3c75875ed82fb41c5d38d04419e3c1e87a5ce01b6b1f3f1ea27298",
 "lead/advset_indep_20261109/_ai_verify_stdout.txt": "a7bbb835b9cca4dafb2bfd27d1959aa4b139a8a0f532b14d726411a66f800cea",
 "lead/dg_adversarial_20261109/_dga_adversarial_out.json": "395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c",
 "lead/dneg_generative_20261109/_dg_core.py": "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1",
 "lead/h5_governance_20261109/_h5_pasteable.py": "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c",
 "lead/gate_fp7_20261108/_g7_predicates.py": "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",
 "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
 "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}
mism = [k for k, v in ORCH.items() if fingerprints[k]["sha256"] != v]
emit("orch_fingerprint_match", {"n": len(ORCH), "all_match": not mism, "mismatch": mism})

# ==================== (1) 内存加载谓词 + AST 抽 CASES，独立重跑 41 条判定 ====================
print("\n=== (1) 41 条判定独立重跑 ===")
DG = load_src("_fp_dg", DG_DIR / "_dg_core.py")
H5 = load_src("_fp_h5", H5P)
G7 = load_src("_fp_g7", G7P)
DROP = load_src("_fp_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
A = lit_assigns(DGA / "_dga_adversarial.py")
CASES, FORCED = A["CASES"], A["FORCED"]
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
DET = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]

def detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {k: "PASS" for k in DET}; hits = {}
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"; hits["DG_pure"] = h[0]["hit"] if h else ""
    pd, _ = DROP.r12_scan(text, toks); r["DG_dropin"] = "CATCH" if pd else "PASS"
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hg = False
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            if H5.h5_govern(text[:m.start()], text[m.end():])["double_neg"]: hg = True
    r["H5_gov"] = "CATCH" if hg else "PASS"
    p12, _ = G7.r12_scan(text, toks); r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    return r, hits

rerun = []
for cid, shape, text, exp, why, attack in CASES:
    r, hits = detect(text)
    rerun.append({"id": cid, "shape": shape, "text": text, "expect": exp,
                  "forced": FORCED.get(cid, exp), "why": why, "attack": attack,
                  "verdicts": r, "hits_pure": hits["DG_pure"]})

def score(key, forced=False):
    fp, fn, amb, fpi, fni = 0, 0, 0, [], []
    for x in rerun:
        e = x["forced"] if forced else x["expect"]
        if e == "AMBIG" and not forced: amb += 1; continue
        g = x["verdicts"][key]
        if e == "PASS" and g == "CATCH": fp += 1; fpi.append(x["id"])
        elif e == "CATCH" and g == "PASS": fn += 1; fni.append(x["id"])
    return {"n": len(rerun) - amb, "amb_excluded": amb, "fp": fp, "fn": fn,
            "fp_ids": fpi, "fn_ids": fni}

strict = {k: score(k) for k in DET}
orchestrator = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
cmp = {}
for k in DET:
    a, b = strict[k], orchestrator["scoring_strict"][k]
    cmp[k] = {"rerun": [a["fp"], a["fn"], a["fp_ids"], a["fn_ids"]],
              "orch": [b["fp"], b["fn"], b["fp_ids"], b["fn_ids"]],
              "identical": (a["fp"], a["fn"], a["fp_ids"], a["fn_ids"]) ==
                           (b["fp"], b["fn"], b["fp_ids"], b["fn_ids"])}
emit("strict_rerun_vs_orch", {"n_cases": len(rerun), "all_identical": all(v["identical"] for v in cmp.values()),
                              "by_detector": {k: {"fp": v["rerun"][0], "fn": v["rerun"][1],
                                                  "identical": v["identical"]} for k, v in cmp.items()}})
FP = strict["DG_pure"]["fp_ids"]; FN = strict["DG_pure"]["fn_ids"]
emit("DG_pure_strict", strict["DG_pure"])

# ==================== (2) 独立重建 min_edit（AST 抽训练句 + Levenshtein） ====================
print("\n=== (2) min_edit 独立重建 ===")
TRAIN_FILES = {t: DG_DIR / t for t in
               ("_dg_step34.py", "_dgv_probe.py", "_dgv_neg2.py", "_dg_step1.py")}
labeled = {}
for tag, p in TRAIN_FILES.items():
    for name, val in lit_assigns(p).items():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, (tuple, list)) and len(item) >= 2 and isinstance(item[0], str) \
                        and re.fullmatch(r"[A-Z]{1,3}\d{1,2}", item[0]) and isinstance(item[1], str):
                    labeled.setdefault(item[0] + "@" + tag, item[1])
for name, idx in (("GAPS", 1), ("NEG20", 1), ("A", 1), ("PARITY", 0)):
    for item in lit_assigns(TRAIN_FILES["_dg_step34.py"]).get(name, []):
        if isinstance(item, (tuple, list)) and len(item) > idx and isinstance(item[idx], str):
            labeled.setdefault("S:" + str(item[idx])[:12], item[idx])
for name in ("H5_EXTRA", "H5_SPLIT"):
    for s in lit_assigns(TRAIN_FILES["_dg_step34.py"]).get(name, []):
        labeled.setdefault("H:" + s[:12], s)
for name in ("GAPS", "NEG"):
    for item in lit_assigns(TRAIN_FILES["_dgv_probe.py"]).get(name, []):
        s = item[1] if isinstance(item, (tuple, list)) else item
        if isinstance(s, str): labeled.setdefault("V:" + s[:12], s)
for item in lit_assigns(TRAIN_FILES["_dgv_neg2.py"]).get("CASES", []):
    if isinstance(item, (tuple, list)) and len(item) > 1:
        labeled.setdefault("W:" + item[1][:12], item[1])
for s in lit_assigns(TRAIN_FILES["_dgv_neg2.py"]).get("SKELETON", []):
    labeled.setdefault("K:" + s[:12], s)
for item in lit_assigns(TRAIN_FILES["_dg_step1.py"]).get("GAPS", []):
    if isinstance(item, (tuple, list)) and len(item) > 1:
        labeled.setdefault("G:" + item[1][:12], item[1])
for s in lit_assigns(TRAIN_FILES["_dg_step1.py"]).get("CTRL_CATCH", []):
    labeled.setdefault("C:" + s[:12], s)
SENTS = {k: v for k, v in labeled.items() if len(v) >= 8 and re.search(r"[\u4e00-\u9fff]", v)}
SENTS_LIST = sorted(set(SENTS.values()))
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
me_re = {}
for x in rerun:
    best = (10 ** 9, None)
    for s in SENTS_LIST:
        if abs(len(s) - len(x["text"])) > 22: continue
        d = lev(x["text"], s)
        if d < best[0]: best = (d, s)
    me_re[x["id"]] = best[0]
me_diff = {x["id"]: [me_re[x["id"]], V["near"][x["id"]]["dist"]]
           for x in rerun if me_re[x["id"]] != V["near"][x["id"]]["dist"]}
emit("min_edit_rebuild", {"n_train_sentences": len(SENTS_LIST),
                          "all_match_stored": not me_diff, "diff": me_diff})

# ==================== (3) 四级分级独立复算（严格 + 宽松） ====================
print("\n=== (3) 分级复算 ===")
def grade_strict(r):
    if r["min_edit"] == 0: return "belowL0"
    if r["d1"] or r["d3_pure"] or r["d3_dropin"]: return "L0"
    if r["d2"]: return "L1"
    if r["lcs_train"].get("len", 0) >= 4 or r["min_edit"] <= 5: return "L2"
    return "L3"

sd = Counter(grade_strict(r) for r in G["rows"])
sd_full = {lv: sd.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")}
ld = Counter(r["grade"] for r in V["grade_rows"])
ld_full = {lv: ld.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")}
emit("grade_recompute", {
  "strict_recomputed_from_rows": sd_full,
  "strict_stored": G["grade_distribution"],
  "strict_match": sd_full["L0"] == 24 and sd_full["L1"] == 17 and sd_full["L2"] == 0 and sd_full["L3"] == 0,
  "loose_recomputed_from_rows": ld_full,
  "loose_stored": V["grade_distribution"],
  "loose_match": ld_full["L0"] == 33 and ld_full["L1"] == 8 and ld_full["L2"] == 0 and ld_full["L3"] == 0,
  "strict_L0_ids": [r["id"] for r in G["rows"] if grade_strict(r) == "L0"],
  "strict_L1_ids": [r["id"] for r in G["rows"] if grade_strict(r) == "L1"],
})
# 文档口径统计复算
emit("doc_stats_recompute", {
  "d1_nonempty": sum(1 for r in G["rows"] if r["d1"]),
  "d2_nonempty": sum(1 for r in G["rows"] if r["d2"]),
  "d3_any": sum(1 for r in G["rows"] if r["d3_pure"] or r["d3_dropin"]),
  "d1_or_d3": sum(1 for r in G["rows"] if r["d1"] or r["d3_pure"] or r["d3_dropin"]),
  "lcs_ge6": sum(1 for r in G["rows"] if r["lcs_train"].get("len", 0) >= 6),
  "exact_overlap": orchestrator["novelty"]["exact_overlap"],
  "all_pure_hit_decomposable": all(s["pure_decomposable"] for s in V["share_rows"] if s["hit_DG_pure"]),
})

# ==================== (4) (b)(c)(d) 逐条 + 列联表 ====================
print("\n=== (4) 误报 / 判对 / min_edit 逐条 ===")
byid = {r["id"]: r for r in G["rows"]}
verd = {x["id"]: x["verdicts"]["DG_pure"] for x in rerun}
fp_rows = []
for cid in FP:
    r = byid[cid]
    fp_rows.append({"id": cid, "expect": r["expect"], "verdict": verd[cid],
                    "d1": r["d1"], "d1_nonempty": bool(r["d1"]),
                    "d3_pure": r["d3_pure"], "d3_dropin": r["d3_dropin"],
                    "hit": r["hit_pure"], "min_edit": r["min_edit"],
                    "grade": r["grade"], "attack": next(x["attack"] for x in rerun if x["id"] == cid)})
emit("fp7_rows", fp_rows)
emit("fp7_all_d1_nonempty", all(z["d1_nonempty"] for z in fp_rows))
emit("fp7_all_d3_true", all(z["d3_pure"] and z["d3_dropin"] for z in fp_rows))

# 所有 d1 = "-" 的样本（全 41 条口径，以及 PASS-expect 负样本口径）
d1empty_all = [r["id"] for r in G["rows"] if not r["d1"]]
d1empty_neg = [r["id"] for r in G["rows"] if not r["d1"] and r["expect"] == "PASS"]
d1empty_rows = [{"id": cid, "expect": byid[cid]["expect"], "verdict": verd[cid],
                 "d3_pure": byid[cid]["d3_pure"], "min_edit": byid[cid]["min_edit"],
                 "grade": byid[cid]["grade"]} for cid in d1empty_all]
emit("d1_empty_rows", d1empty_rows)
emit("d1_empty_all_correct", {"n": len(d1empty_all),
     "all_verdict_PASS": all(z["verdict"] == "PASS" for z in d1empty_rows),
     "n_strict_negative": len(d1empty_neg),
     "negative_all_judged_correct": all(byid[c]["expect"] == verd[c] for c in d1empty_neg),
     "note": "全 41 条口径下 d1 空的 CATCH 样本存在（d3 非空），但那是 expect=CATCH/AMBIG 的真阳/歧义样本"})
# d1 非空但判对的负样本（反例：训练构式 ≠ 必然误报）
d1ne_pos = [{"id": r["id"], "verdict": verd[r["id"]], "d1": r["d1"],
             "min_edit": r["min_edit"], "why": next(x["why"] for x in rerun if x["id"] == r["id"])}
            for r in G["rows"] if r["d1"] and r["expect"] == "PASS" and verd[r["id"]] == "PASS"]
emit("d1_nonempty_but_correct_negatives", d1ne_pos)

# 2x2 列联表（17 条 PASS-expect 负样本）
neg = [r for r in G["rows"] if r["expect"] == "PASS"]
a = sum(1 for r in neg if r["d1"] and verd[r["id"]] == "CATCH")       # d1+ & fp
b = sum(1 for r in neg if r["d1"] and verd[r["id"]] == "PASS")         # d1+ & correct
c = sum(1 for r in neg if not r["d1"] and verd[r["id"]] == "CATCH")    # d1- & fp
d = sum(1 for r in neg if not r["d1"] and verd[r["id"]] == "PASS")      # d1- & correct
def C(n, k): return math.comb(n, k)
fisher_one = C(a+b, a) * C(c+d, c) / C(a+b+c+d, a+c)
emit("contingency_17_negatives", {"d1plus_fp": a, "d1plus_correct": b,
     "d1minus_fp": c, "d1minus_correct": d,
     "P_fp_given_d1plus": round(a/(a+b), 4), "P_fp_given_d1minus": round(c/(c+d), 4),
     "fisher_one_sided_p": round(fisher_one, 8),
     "fisher_formula": "C(%d,%d)*C(%d,%d)/C(%d,%d)" % (a+b, a, c+d, c, a+b+c+d, a+c)})

# min_edit 单调性：按 me 排序后 fp 指示序列是否单调；逆序对数
seq = sorted(((r["min_edit"], 1 if verd[r["id"]] == "CATCH" else 0, r["id"]) for r in neg))
fp_me = sorted(r["min_edit"] for r in neg if verd[r["id"]] == "CATCH")
ok_me = sorted(r["min_edit"] for r in neg if verd[r["id"]] == "PASS")
inv = sum(1 for x in fp_me for y in ok_me if x > y)   # fp 的 me 反而更大 = 违单调递增
inv2 = sum(1 for x in fp_me for y in ok_me if x < y)  # 判对的 me 反而更大 = 违单调递减
best = max(((max(0, sum(1 for r in neg if (r["min_edit"] >= t) == (verd[r["id"]] == "CATCH"))), t)
            for t in range(0, 20)), key=lambda z: (z[0], -z[1]))
emit("min_edit_analysis", {"sorted_(me,is_fp,id)": seq, "fp_me": fp_me, "correct_me": ok_me,
     "fp_range": [min(fp_me), max(fp_me)], "correct_range": [min(ok_me), max(ok_me)],
     "overlap": sorted(set(fp_me) & set(ok_me)),
     "violations_of_monotone_increasing": inv, "violations_of_monotone_decreasing": inv2,
     "best_threshold_accuracy": {"correct": best[0], "n": len(neg), "threshold": best[1]},
     "verdict": "无单调关系" if set(fp_me) & set(ok_me) else "可分"})

# ==================== (5) 定义性/构造性分析 ====================
print("\n=== (5) 定义性与构造性 ===")
# d3 与 CATCH 是否定义性等价
taut = []
for x, s in zip(V["rows"], V["share_rows"]):
    hit = bool(x["hits"]["DG_pure"]); catch = x["verdicts"]["DG_pure"] == "CATCH"
    if hit != catch or (hit and not s["pure_decomposable"]): taut.append(x["id"])
emit("d3_tautology", {"n_mismatch": len(taut), "ids": taut,
     "n_DG_pure_CATCH": sum(1 for x in V["rows"] if x["verdicts"]["DG_pure"] == "CATCH"),
     "n_d3_pure_true": sum(1 for s in V["share_rows"] if s["pure_decomposable"]),
     "conclusion": "d3 := decomposable(hit_DG_pure)；hit 非空 <=> CATCH；故 d3=True 与 CATCH 定义性等价"})
# d1 目录的内生性：CATALOG 是否来自 DG 自身闭合表
emit("d1_catalog_provenance", {
     "d1_def": "_ai_grade.py:103  d1 = [k for k in CAT_IN_TRAIN if k in text]",
     "catalog_def": "_ai_grade.py:48-58  catalog 由 DG.R12_TEN / DG.PSEUDO_DN / GAPS / H5_EXTRA / H5_SPLIT / H5 字面支拼成",
     "train_def": "_ai_grade.py:64-78  CAT_IN_TRAIN = 目录条目在 DG 训练句子里作子串",
     "conclusion": "特征 d1 的分母（构式目录）取自被测 DG 自身的闭合表；CATCH 也由同一批表生成的 DG_DROPIN_RE 匹配 ⇒ 特征与结果共用同一表，非独立观测"})
# 7 fp 的 attack / why 是否点名被测源码（生成机制同源证据）
fp_srcline = [{"id": z["id"], "attack": z["attack"],
               "why_has_core_line": "_dg_core.py:" in next(x["why"] for x in rerun if x["id"] == z["id"]),
               "why_has_table": bool(re.search(r"DG_BREAK_RE|_BQ|_SECOND|DG_QUOTE_RE|DG_COORD_RE|NEG2|PSEUDO|MID|:[0-9]", next(x["why"] for x in rerun if x["id"] == z["id"])))}
              for z in fp_rows]
emit("fp7_construction_provenance", {"rows": fp_srcline,
     "all_attack_nonempty": all(z["attack"] for z in fp_srcline),
     "all_why_references_dg_internals": all(z["why_has_core_line"] or z["why_has_table"] for z in fp_srcline)})
# 全体 41 条 attack / why 同源计数
emit("all41_construction_provenance", {
  "attack_nonempty": sum(1 for x in rerun if x["attack"]),
  "why_has_core_line": sum(1 for x in rerun if "_dg_core.py:" in x["why"]),
  "why_has_table_or_lineno": sum(1 for x in rerun if re.search(r"DG_BREAK_RE|_BQ|_SECOND|DG_QUOTE_RE|DG_COORD_RE|NEG2|PSEUDO|MID|_g7_predicates.py|:\d+", x["why"])),
  "n": len(rerun)})
# H5 / R12 对照：其 fp 是否也全在训练构式上
h5fp = strict["H5_lit"]["fp_ids"]; h5fn = strict["H5_lit"]["fn_ids"]
r12fp = strict["R12"]["fp_ids"]; r12fn = strict["R12"]["fn_ids"]
emit("detector_comparison", {
  "DG_pure": {"fp": len(FP), "fn": len(FN), "fp_ids": FP, "fn_ids": FN,
              "fp_all_d1_nonempty": all(byid[c]["d1"] for c in FP),
              "fn_all_d1_empty_or_not": [byid[c]["d1"] for c in FN]},
  "H5_lit": {"fp": len(h5fp), "fn": len(h5fn), "fp_ids": h5fp,
             "fp_all_d1_nonempty": all(byid[c]["d1"] for c in h5fp),
             "fp_d1": [byid[c]["d1"] for c in h5fp]},
  "R12": {"fp": len(r12fp), "fn": len(r12fn), "fp_ids": r12fp,
          "fp_all_d1_nonempty": all(byid[c]["d1"] for c in r12fp)},
  "H5_lit_zero_memory": "H5_DOUBLE_NEG_RE 是 H5_R12_TEN(10 支)+H5_DN_EXTRA(19 式字面+1 通配) 的手写正则，无任何学习/记忆过程（_h5_pasteable.py:31-40）",
})
# fn 逐条：d1/grade/attack/why，供分类
fn_rows = [{"id": c, "d1": byid[c]["d1"], "d3_pure": byid[c]["d3_pure"],
            "grade": byid[c]["grade"], "min_edit": byid[c]["min_edit"],
            "attack": next(x["attack"] for x in rerun if x["id"] == c),
            "why": next(x["why"] for x in rerun if x["id"] == c)} for c in FN]
emit("fn11_rows", fn_rows)

# 写盘（唯一写域）
(WD / "_fp_recompute_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fp_recompute_out.json")
