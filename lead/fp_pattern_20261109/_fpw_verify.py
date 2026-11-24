# -*- coding: utf-8 -*-
r"""_fpw_verify.py — 交付撰写员：本会话独立复核（只读保护树；唯一写域 lead/fp_pattern_20261109/）。

纪律：零真机 / 零采样代码 / 零 hook；保护件 compile/exec 内存加载或 AST 字面抽取，
      sys.dont_write_bytecode=True；指纹只用 hashlib.sha256。
      不 import、不 exec 任何 _fp_ / _fpv_ 既有脚本；下面的 detect / grade 均为本会话自写。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpw_verify.py
"""
import sys, json, hashlib, re, ast, types, math, time
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
SESSION_START_NS = time.time_ns()

OUT = {}
def emit(k, v):
    OUT[k] = v
    print("[%s] %s" % (k, json.dumps(v, ensure_ascii=False)))

def sha(rel):
    b = (ROOT / rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

def lit_assigns(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    o = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    try: o[tg.id] = ast.literal_eval(n.value)
                    except Exception: pass
    return o

def load_src(name, path):
    m = types.ModuleType(name); m.__file__ = str(path)
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

# ==================== (A) 九件编排方指纹 + 16 件绑定行 ====================
print("=== (A) 指纹独立实算（hashlib.sha256） ===")
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
BIND16 = [
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
FP = {}
for rel in BIND16:
    h, n = sha(rel); FP[rel] = {"sha256": h, "bytes": n}
    print("  [%s]" % rel)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h, n))
bad9 = [rel for rel, (h, n) in ORCH9.items()
        if FP[rel]["sha256"] != h or FP[rel]["bytes"] != n]
emit("orch9_check", {"n": 9, "all_sha_and_bytes_match": not bad9, "mismatch": bad9})
# 被核交付件绑定行（复核回件 sha256Line 载入本会话重算对照）
DELIVERABLE_BIND = {
 "_fp_ANALYSIS.md": "5873fa7079b415cd5ca5fc51f4e9aaca84c702b897596aa50fdfd07df6e15277",
}
emit("deliverable_bindline_check", {k: {"declared": v, "_fp_ANALYSIS_bytes": (WD / "_fp_ANALYSIS.md").stat().st_size}
                                    for k, v in DELIVERABLE_BIND.items()})

# ==================== (B) 41 条 × 6 判定器自写 detect ====================
print("=== (B) 41 条 × 6 判定器自写重跑 ===")
DG = load_src("_fpw_dg", DG_DIR / "_dg_core.py")
H5 = load_src("_fpw_h5", H5P)
G7 = load_src("_fpw_g7", G7P)
DROP = load_src("_fpw_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert DROP.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE
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
    r["H5_lit"] = "CATCH" if ml else "PASS"; hits["H5_lit"] = ml.group(0) if ml else ""
    hg = False; hh = ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]: hg = True; hh = g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"; hits["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks); r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12"] = m12.group(0) if m12 else ""; hits["R12_lit"] = hits["R12"]
    hits["DG_dropin"] = ""
    return r, hits

rerun = []
for cid, shape, text, exp, why, attack in CASES:
    r, hits = detect(text)
    rerun.append({"id": cid, "text": text, "expect": exp, "forced": FORCED.get(cid, exp),
                  "why": why, "attack": attack, "verdicts": r, "hits": hits})
byid = {x["id"]: x for x in rerun}

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
ORCH = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
diff = {k: [strict[k]["fp"], strict[k]["fn"], ORCH["scoring_strict"][k]["fp"], ORCH["scoring_strict"][k]["fn"]]
        for k in DET if (strict[k]["fp"], strict[k]["fn"], strict[k]["fp_ids"], strict[k]["fn_ids"]) !=
        (ORCH["scoring_strict"][k]["fp"], ORCH["scoring_strict"][k]["fn"],
         ORCH["scoring_strict"][k]["fp_ids"], ORCH["scoring_strict"][k]["fn_ids"])}
emit("strict_vs_orch", {"n_cases": 41, "all_identical": not diff,
                        "by_detector": {k: {"fp": strict[k]["fp"], "fn": strict[k]["fn"]} for k in DET},
                        "diff": diff})
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
vdiff = [(x["id"], k) for x in V["rows"] for k in DET
         if x["verdicts"][k] != byid[x["id"]]["verdicts"][k]]
emit("verdicts_vs_verify_json", {"n_cases": 41, "n_detectors": 6, "n_diff": len(vdiff), "diff": vdiff})

# ==================== (C) 四级分级 + 7 fp + d1=- + min_edit ====================
print("=== (C) 分级 / 构式对应 / min_edit ===")
def grade_strict(r):
    if r["min_edit"] == 0: return "belowL0"
    if r["d1"] or r["d3_pure"] or r["d3_dropin"]: return "L0"
    if r["d2"]: return "L1"
    if r["lcs_train"].get("len", 0) >= 4 or r["min_edit"] <= 5: return "L2"
    return "L3"
sd = Counter(grade_strict(r) for r in G["rows"])
ld = Counter(r["grade"] for r in V["grade_rows"])
emit("grade_recompute", {"strict": {lv: sd.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")},
                         "strict_stored": G["grade_distribution"],
                         "loose": {lv: ld.get(lv, 0) for lv in ("L0", "L1", "L2", "L3")},
                         "loose_stored": V["grade_distribution"]})
FP7 = strict["DG_pure"]["fp_ids"]; FN11 = strict["DG_pure"]["fn_ids"]
rowsG = {r["id"]: r for r in G["rows"]}
fp7_rows = [{"id": c, "d1": rowsG[c]["d1"], "d1_nonempty": bool(rowsG[c]["d1"]),
             "d3_pure": rowsG[c]["d3_pure"], "d3_dropin": rowsG[c]["d3_dropin"],
             "hit": byid[c]["hits"]["DG_pure"], "min_edit": rowsG[c]["min_edit"],
             "grade": rowsG[c]["grade"], "attack": rowsG[c]["attack"],
             "expect": byid[c]["expect"], "verdict": byid[c]["verdicts"]["DG_pure"]} for c in FP7]
emit("fp7_rows", fp7_rows)
emit("fp7_all_d1_nonempty_and_d3_true",
     {"all_d1_nonempty": all(r["d1_nonempty"] for r in fp7_rows),
      "all_d3_pure_true": all(r["d3_pure"] for r in fp7_rows)})
# d3 恒真（分判定器口径）
n_pure_catch = sum(1 for x in rerun if x["verdicts"]["DG_pure"] == "CATCH")
n_drop_catch = sum(1 for x in rerun if x["verdicts"]["DG_dropin"] == "CATCH")
n_d3p = sum(1 for r in G["rows"] if r["d3_pure"])
n_d3d = sum(1 for r in G["rows"] if r["d3_dropin"])
n_d3any = sum(1 for r in G["rows"] if r["d3_pure"] or r["d3_dropin"])
set_pure = {x["id"] for x in rerun if x["verdicts"]["DG_pure"] == "CATCH"}
set_d3p = {r["id"] for r in G["rows"] if r["d3_pure"]}
emit("d3_tautology_scope", {"n_pure_catch": n_pure_catch, "n_d3_pure": n_d3p,
                            "pure_catch_eq_d3_pure_set": set_pure == set_d3p,
                            "n_dropin_catch": n_drop_catch, "n_d3_dropin": n_d3d,
                            "n_d3_any": n_d3any, "d3_any_eq_pure_catch": n_d3any == n_pure_catch,
                            "d3_any_eq_dropin_catch": n_d3any == n_drop_catch})
# d1=- 全 41 口径
d1empty = [r["id"] for r in G["rows"] if not r["d1"]]
d1empty_neg = [c for c in d1empty if byid[c]["expect"] == "PASS"]
d1empty_pos = [c for c in d1empty if byid[c]["expect"] == "CATCH"]
d1empty_neg_ok = [c for c in d1empty_neg if byid[c]["verdicts"]["DG_pure"] == "PASS"]
d1empty_pos_fn = [c for c in d1empty_pos if byid[c]["verdicts"]["DG_pure"] == "PASS"]
emit("d1_empty_full41", {"n": len(d1empty), "n_neg": len(d1empty_neg), "neg_all_correct": len(d1empty_neg_ok),
                         "n_pos": len(d1empty_pos), "pos_fn_ids": d1empty_pos_fn,
                         "all_correct": len(d1empty_neg_ok) == len(d1empty_neg) and not d1empty_pos_fn})
emit("d1_nonempty_correct_negatives",
     [{"id": c, "d1": rowsG[c]["d1"], "min_edit": rowsG[c]["min_edit"],
       "verdict": byid[c]["verdicts"]["DG_pure"]}
      for c in [x["id"] for x in rerun if x["expect"] == "PASS" and rowsG[x["id"]]["d1"]
                and x["verdicts"]["DG_pure"] == "PASS"]])
# 17 条负样本 2×2 + Fisher
neg = [x["id"] for x in rerun if x["expect"] == "PASS"]
a = sum(1 for c in neg if rowsG[c]["d1"] and byid[c]["verdicts"]["DG_pure"] == "CATCH")
b = sum(1 for c in neg if rowsG[c]["d1"] and byid[c]["verdicts"]["DG_pure"] == "PASS")
c0 = sum(1 for c in neg if not rowsG[c]["d1"] and byid[c]["verdicts"]["DG_pure"] == "CATCH")
d0 = sum(1 for c in neg if not rowsG[c]["d1"] and byid[c]["verdicts"]["DG_pure"] == "PASS")
fisher = math.comb(9, 7) * math.comb(8, 0) / math.comb(17, 7)
emit("contingency_17", {"n": len(neg), "d1plus_fp": a, "d1plus_ok": b, "d1minus_fp": c0,
                        "d1minus_ok": d0, "P_fp_given_d1plus": round(a / (a + b), 4),
                        "P_fp_given_d1minus": round(c0 / (c0 + d0), 4),
                        "fisher_one_sided": round(fisher, 8)})
# min_edit 与误报：两个方向都穷举阈值
me = {c: rowsG[c]["min_edit"] for c in neg}
isfp = {c: byid[c]["verdicts"]["DG_pure"] == "CATCH" for c in neg}
fp_me = sorted(me[c] for c in neg if isfp[c]); ok_me = sorted(me[c] for c in neg if not isfp[c])
inc = [(x, y) for x in fp_me for y in ok_me if x > y]   # fp 的 me 反而更大 ⇒ 违单调递增
dec = [(x, y) for x in fp_me for y in ok_me if x < y]   # 判对的 me 反而更大 ⇒ 违单调递减
def acc_ge(t): return sum(1 for c in neg if (me[c] >= t) == isfp[c])
def acc_le(t): return sum(1 for c in neg if (me[c] <= t) == isfp[c])
ge = max((acc_ge(t), t) for t in range(0, 20))
le = max((acc_le(t), t) for t in range(0, 20))
emit("min_edit_analysis", {"fp_me": fp_me, "ok_me": ok_me,
                           "overlap": sorted(set(fp_me) & set(ok_me)),
                           "violations_of_me(fp)>me(ok)_monotone": len(inc),
                           "violations_of_me(fp)<me(ok)_monotone": len(dec),
                           "best_ge_threshold": {"correct": ge[0], "n": len(neg), "t": ge[1]},
                           "best_le_threshold": {"correct": le[0], "n": len(neg), "t": le[1]},
                           "no_threshold_separates": ge[0] < len(neg) and le[0] < len(neg)})
# min_edit 独立重建（79 句）
TRAIN_FILES = {t: DG_DIR / t for t in ("_dg_step34.py", "_dgv_probe.py", "_dgv_neg2.py", "_dg_step1.py")}
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
SENTS_LIST = sorted(set(v for v in labeled.values() if len(v) >= 8 and re.search(r"[\u4e00-\u9fff]", v)))
me_re = {}
for x in rerun:
    best = (10 ** 9, None)
    for s in SENTS_LIST:
        if abs(len(s) - len(x["text"])) > 22: continue
        dd = lev(x["text"], s)
        if dd < best[0]: best = (dd, s)
    me_re[x["id"]] = best[0]
me_diff = {c: [me_re[c], V["near"][c]["dist"]] for c in V["near"] if me_re[c] != V["near"][c]["dist"]}
emit("min_edit_rebuild", {"n_train_sentences": len(SENTS_LIST), "n_compared": len(V["near"]),
                          "all_match_stored": not me_diff, "diff": me_diff})

# ==================== (D) 因果 vs 构造偏差：两侧证据 ====================
print("=== (D) 双解释证据 ===")
MY_BREAK = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究",
            "总而言之", "归根结底", "话说回来", "退一步说", "哪怕", "说白了"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
unreg = []
for w in MY_BREAK:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = detect(t)
    unreg.append({"w": w, "BREAK": bool(DG.DG_BREAK_RE.search(w)), "DG_pure": r["DG_pure"]})
reg = []
for w in BREAK10:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = detect(t)
    reg.append({"w": w, "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"]})
emit("sideA_boundary_probe", {"unreg_n": len(unreg),
                               "unreg_BREAK_false_and_pure_CATCH": sum(1 for z in unreg if not z["BREAK"] and z["DG_pure"] == "CATCH"),
                               "reg_n": len(reg), "reg_pure_PASS": sum(1 for z in reg if z["DG_pure"] == "PASS"),
                               "reg_dropin_CATCH": sum(1 for z in reg if z["DG_dropin"] == "CATCH")})
emit("sideA_regex_provenance", {"stats": DG.DG_STATS,
                                 "all_pure_hit_decomposable": all(
                                     s["pure_decomposable"] for s in V["share_rows"] if s["hit_DG_pure"])})
# fp7 护栏精确探针
guard = {}
for cid in FP7:
    text = byid[cid]["text"]
    toks = [t for t in TOKS if t in text] or ["已生效"]
    per = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[:m.start()]
            masked = DG._mask_quotes(pre)
            scope = DG._scope(masked)
            mm = DG.DG_DROPIN_RE.search(scope)
            hit = mm.group(0) if mm else ""
            coord_out = bool(re.search(r"[/／]|、|或|以及|同时|并且|一是|二是|其一|其二", pre.replace(hit, "", 1))) if hit else False
            per.append({"tok": tok, "pre": pre, "masked_changed": masked != pre,
                        "quote_re_matched": bool(DG.DG_QUOTE_RE.search(pre)),
                        "break_words_in_pre": [w for w in MY_BREAK if w in pre],
                        "match": hit, "coord_outside_hit": coord_out})
    guard[cid] = per
emit("sideA_fp7_guard_probe", guard)
# 构造偏差：d1 目录来源（源码行实读）+ 构造同源计数
src_grade = (AI / "_ai_grade.py").read_text(encoding="utf-8").splitlines()
emit("sideB_d1_catalog_lines", {"lines_48_58": [src_grade[i - 1] for i in range(48, 59)],
                                 "line_103": src_grade[102], "line_91": src_grade[90]})
cs = [x for x in rerun]
emit("sideB_construction_provenance",
     {"attack_nonempty": sum(1 for x in cs if x["attack"]),
      "why_core_line": sum(1 for x in cs if "_dg_core.py:" in x["why"]),
      "why_table_or_lineno_upstream_regex": sum(1 for x in cs if re.search(
          r"DG_BREAK_RE|_BQ|_SECOND|DG_QUOTE_RE|DG_COORD_RE|NEG2|PSEUDO|MID|_g7_predicates.py|:\d+", x["why"])),
      "why_table_or_lineno_alt_regex": sum(1 for x in cs if re.search(
          r"MID|DG_BREAK_RE|_SECOND|DG_QUOTE_RE|DG_COORD_RE|PSEUDO_DN|COMP|23 项|闭合表|词首负向前瞻|≤4|_BQ|DG_|_dg_core\.py", x["why"])),
      "fp7_attack_all_nonempty": all(byid[c]["attack"] for c in FP7), "n": len(cs)})
# 零学习机制扫描
KEYS = r"\b(fit|train|training|learn|learning|gradient|torch|sklearn|numpy|pickle|weights|model|epoch|optimizer)\b"
emit("sideB_zero_learning_source_scan",
     {f: {"n_lines": len((ROOT / f).read_text(encoding="utf-8").splitlines()),
          "learning_keyword_hits": [m.group(0) for m in re.finditer(KEYS, (ROOT / f).read_text(encoding="utf-8"), re.I)],
          "re_compile_calls": len(re.findall(r"re\.compile", (ROOT / f).read_text(encoding="utf-8")))}
      for f in ["lead/dneg_generative_20261109/_dg_core.py",
                "lead/h5_governance_20261109/_h5_pasteable.py",
                "lead/gate_fp7_20261108/_g7_predicates.py"]})
# d1 目录内生性：H5 29 纯字面支 / G7 十式 与 CAT_IN_TRAIN 的关系 + d1 空负样本六判定器
h5_raw_branches = (H5.H5_R12_TEN + "|" + H5.H5_DN_EXTRA).split("|")
# 一条带通配的选择支含 [^...] 与 (?:...|...) 内层竖线；朴素按 | 切把它裂成 9 片。
# 真正选择支 = 10（H5_R12_TEN）+ 19（H5_DN_EXTRA 纯字面）+ 1（带通配）= 30；纯字面 = 29。
_r12 = [s for s in H5.H5_R12_TEN.split("|") if s]
_extra = H5.H5_DN_EXTRA.split("|")
_i0 = next(i for i, s in enumerate(_extra) if "[^" in s)
_i1 = next(i for i, s in enumerate(_extra) if s.endswith(")"))
_wild_fragments = _extra[_i0:_i1 + 1]
h5_lit = [s for s in _r12 + _extra[:_i0] + _extra[_i1 + 1:]
          if re.fullmatch(r"[\u4e00-\u9fff]+", s) and len(s) >= 2]
h5_lit = list(dict.fromkeys(h5_lit))
h5_wild = [_extra[_i0:_i1 + 1]]
g7_ten = re.findall(r"\(([^()]*)\)", (G7P.read_text(encoding="utf-8").splitlines()[75]))
g7_forms = g7_ten[0].split("|") if g7_ten else []
cat = set(G["catalog_in_train"])
emit("sideB_d1_catalog_endogeneity",
     {"catalog_in_train_n": len(cat), "h5_pure_literal_branches": len(h5_lit),
      "h5_wildcard_branches": len(h5_wild), "h5_literals_in_CAT_IN_TRAIN": sum(1 for s in h5_lit if s in cat),
      "g7_forms_n": len(g7_forms), "g7_forms_in_CAT_IN_TRAIN": sum(1 for s in g7_forms if s in cat),
      "g7_ten_equals_DG_R12_TEN": sorted(g7_forms) == sorted(DG.R12_TEN)})
d1empty_neg_id = [c for c in neg if not rowsG[c]["d1"]]
emit("sideB_d1empty_negatives_six_detectors",
     {"n": len(d1empty_neg_id),
      "n_any_CATCH": sum(1 for c in d1empty_neg_id for k in DET if byid[c]["verdicts"][k] == "CATCH")})
emit("sideB_cross_detector_fp",
     {k: {"fp": strict[k]["fp"], "fp_all_d1_nonempty": all(rowsG[c]["d1"] for c in strict[k]["fp_ids"]),
          "fp_d1_empty_ids": [c for c in strict[k]["fp_ids"] if not rowsG[c]["d1"]]} for k in DET})

# ==================== (E) 复核 D1–D7 ====================
print("=== (E) 复核回件 D1–D7 ===")
# D1 H5 支数
h5_fp_hits = {c: byid[c]["hits"]["H5_lit"] for c in strict["H5_lit"]["fp_ids"]}
emit("D1_h5_branch_count", {"R12_TEN_n": len(H5.H5_R12_TEN.split("|")),
                             "DN_EXTRA_naive_split_n": len(H5.H5_DN_EXTRA.split("|")),
                             "DN_EXTRA_wildcard_fragments_n": len(_wild_fragments),
                             "true_pure_literal_branches": len(h5_lit),
                             "true_total_branches": len(h5_lit) + 1,
                             "claimed_in_fp_classify_stdout_36": 37,
                             "h5_9fp_hits_all_from_true_literals": all(h in h5_lit for h in h5_fp_hits.values()),
                             "h5_9fp_hits": h5_fp_hits})
# D2 阈值（已在 C 节双方向穷举）
emit("D2_threshold_directions", {"ge_best_correct": ge[0], "ge_best_t": ge[1],
                                  "le_best_correct": le[0], "le_best_t": le[1],
                                  "claim_10_of_17_is_global_best": ge[0] == 10 and le[0] <= 10})
# D3 表宽 vs fp/fn
emit("D3_table_width_vs_fp_fn",
     {"rows": [{"detector": "R12", "table": 10, "fp": strict["R12"]["fp"], "fn": strict["R12"]["fn"]},
               {"detector": "H5_lit", "table": len(h5_lit) + 1, "fp": strict["H5_lit"]["fp"], "fn": strict["H5_lit"]["fn"]},
               {"detector": "DG_pure", "table": DG.DG_STATS["cartesian_total"], "fp": strict["DG_pure"]["fp"], "fn": strict["DG_pure"]["fn"]}],
      "fp_monotone_increasing": strict["R12"]["fp"] <= strict["H5_lit"]["fp"] <= strict["DG_pure"]["fp"],
      "fn_monotone_decreasing": strict["R12"]["fn"] >= strict["H5_lit"]["fn"] >= strict["DG_pure"]["fn"]})
# D4 已在 C 节；D5 引用行号；D7 两批探针
cls = (WD / "_fp_classify_stdout.txt").read_text(encoding="utf-8").splitlines()
rec = (WD / "_fp_recompute_stdout.txt").read_text(encoding="utf-8").splitlines()
adv = (AI / "ADVSET_INDEPENDENCE.md").read_text(encoding="utf-8").splitlines()
emit("D5_citation_line_check",
     {"_fp_classify_stdout_n_lines": len(cls),
      "line2_is_P06": cls[1].startswith('{"id": "P06"'),
      "line8_is_P12": cls[7].startswith('{"id": "P12"'),
      "line9_is_blank": cls[8].strip() == "",
      "line10_is_fn_header": cls[9].startswith("=== fn=11"),
      "line11_is_C01": cls[10].startswith('{"id": "C01"'),
      "line21_is_C12": cls[20].startswith('{"id": "C12"'),
      "line24_is_summary": cls[23].startswith('{"fp_n": 7'),
      "line27_is_DG_pure": cls[26].startswith('{"DG_pure"'),
      "line32_is_R12_lit": cls[31].startswith('{"R12_lit"'),
      "line35_is_h5_hits": cls[34].startswith('{"P06"'),
      "line36_h5_branch_claim": cls[35],
      "_fp_recompute_stdout_n_lines": len(rec),
      "ADVSET_571": adv[570], "ADVSET_574": adv[573][:120]})
# D7 两批 14 词
av_line = (AI / "_ai_verify_stdout.txt").read_text(encoding="utf-8").splitlines()[244]
dg_line = (DGA / "DG_ADVERSARIAL.md").read_text(encoding="utf-8").splitlines()[176]
av_words = re.findall(r"\('([^']+)', 'CATCH', 'CATCH'\)", av_line)
dgm = re.search(r"词表：`([^`]+)`", dg_line)
dg_words = dgm.group(1).split("/") if dgm else []
emit("D7_two_14word_sets", {"ai_verify_stdout_245_n": len(av_words), "dg_adversarial_177_n": len(dg_words),
                             "identical": sorted(av_words) == sorted(dg_words),
                             "only_in_av": sorted(set(av_words) - set(dg_words)),
                             "only_in_dg": sorted(set(dg_words) - set(av_words))})

# ==================== (F) fp/fn 逐条分类探针 ====================
print("=== (F) fp7/fn11 逐条分类 ===")
fp7_cls = [{"id": c, "d1": rowsG[c]["d1"], "d3_pure": rowsG[c]["d3_pure"],
            "hit": byid[c]["hits"]["DG_pure"], "min_edit": rowsG[c]["min_edit"],
            "type": "过宽/护栏污染", "why": byid[c]["why"]} for c in FP7]
fn_probe = {}
for c in FN11:
    text = byid[c]["text"]
    toks = [t for t in TOKS if t in text] or ["已生效"]
    any_match = False; post_veto = False; pseudo_la = False; matches = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[:m.start()]; scope = DG._scope(DG._mask_quotes(pre))
            mm = DG.DG_DROPIN_RE.search(scope)
            if mm:
                any_match = True; matches.append(mm.group(0))
                h = mm.group(0)
                if DG.DG_COORD_RE.search(h) or DG.DG_SECOND_SUBJ_RE.search(h): post_veto = True
    # PSEUDO 词首负向前瞻：构式串命中被 veto 挡住（无 Match 但含 PSEUDO 词）
    if not any_match and any(p in text for p in DG.PSEUDO_DN): pseudo_la = True
    fn_probe[c] = {"any_regex_match": any_match, "post_veto": post_veto,
                   "pseudo_negative_lookahead_candidate": pseudo_la, "matches": matches}
emit("fp7_classified", fp7_cls)
emit("fn11_probe", fn_probe)
emit("fn11_counts", {"覆盖不足_无Match": sum(1 for c in FN11 if not fn_probe[c]["any_regex_match"] and not fn_probe[c]["pseudo_negative_lookahead_candidate"]),
                      "后置veto误杀": sum(1 for c in FN11 if fn_probe[c]["post_veto"]),
                      "正则内PSEUDO前瞻": sum(1 for c in FN11 if fn_probe[c]["pseudo_negative_lookahead_candidate"])})
emit("fn_d1_nonempty_ids", [c for c in FN11 if rowsG[c]["d1"]])

# ==================== (G) held-out / H5 / 对照表条款 ====================
print("=== (G) 文档条款核对 ===")
emit("G_heldout_lines", {"ADVSET_542_543": [adv[i - 1] for i in (542, 543)],
                          "ADVSET_544_546": [adv[i - 1] for i in (544, 545, 546)],
                          "ADVSET_550": adv[549], "ADVSET_559": adv[558],
                          "ADVSET_569": adv[568][:150], "ADVSET_570": adv[569],
                          "ADVSET_574_severity": adv[573][:120], "ADVSET_588": adv[587],
                          "ADVSET_604": adv[603], "DGADV_308": (DGA / "DG_ADVERSARIAL.md").read_text(encoding="utf-8").splitlines()[307][:170]})
h5_src = H5P.read_text(encoding="utf-8").splitlines()
emit("G_h5_src", {"lines_31_40": [h5_src[i - 1] for i in range(31, 41)],
                   "g7_76": (G7P.read_text(encoding="utf-8").splitlines()[75]),
                   "g7_92": (G7P.read_text(encoding="utf-8").splitlines()[91]),
                   "g7_144": (G7P.read_text(encoding="utf-8").splitlines()[143])})
emit("G_h5_p16_p17", {c: {"H5_lit": byid[c]["verdicts"]["H5_lit"], "H5_gov": byid[c]["verdicts"]["H5_gov"],
                           "lit_hit": byid[c]["hits"]["H5_lit"]} for c in ("P16", "P17")})
emit("G_comparison_table", {k: {"fp": strict[k]["fp"], "fn": strict[k]["fn"],
                                "fp_all_d1_nonempty": all(rowsG[c]["d1"] for c in strict[k]["fp_ids"])}
                            for k in ("DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit")})

# ==================== (H) 保护树零写核对 ====================
print("=== (H) 保护树零写核对 ===")
PROT = [AI, DGA, DG_DIR, ROOT / "lead" / "h5_governance_20261109",
        ROOT / "lead" / "gate_fp7_20261108",
        ROOT / "lead" / "PENDING_DECISIONS.md", ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"]
prot_files = []
for p in PROT:
    if p.is_dir(): prot_files += [q for q in sorted(p.rglob("*")) if q.is_file()]
    else: prot_files.append(p)
def norm(p): return str(p).replace("\\", "/").lower()
base = {}
for rel, (h, n) in ORCH9.items(): base[norm(ROOT / rel)] = (h, n)
for rel, val in FP.items(): base[norm(ROOT / rel)] = (val["sha256"], val["bytes"])
for rel, fpv in V["fingerprints"].items():
    p = ROOT / rel
    if p.exists() and isinstance(fpv, dict) and "sha" in fpv:
        base[norm(p)] = (fpv["sha"], fpv.get("bytes"))
snap = json.loads((DG_DIR / "_dgv_protected_snapshot.json").read_text(encoding="utf-8"))
for _group, mapping in snap.items():
    if not isinstance(mapping, dict): continue
    for rel, val in mapping.items():
        if isinstance(val, list) and len(val) >= 1 and isinstance(val[0], str) and len(val[0]) == 64:
            base[norm(ROOT / rel)] = (val[0], val[1] if len(val) > 1 and isinstance(val[1], int) else None)
        elif isinstance(val, dict) and "sha" in val:
            base[norm(ROOT / rel)] = (val["sha"], val.get("bytes"))
mismatch = []
n_baseline = 0
for p in prot_files:
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    key = norm(p)
    if key in base:
        n_baseline += 1
        exp_h, exp_n = base[key]
        if h != exp_h or (exp_n is not None and len(b) != exp_n):
            mismatch.append({"file": key, "sha": h, "bytes": len(b)})
newer = [str(p) for p in prot_files if p.stat().st_mtime_ns > SESSION_START_NS]
pyc_new = [str(p) for p in prot_files if p.suffix == ".pyc" and p.stat().st_mtime_ns > SESSION_START_NS]
emit("H_protected_zero_write", {"n_protected_files": len(prot_files), "n_with_external_baseline": n_baseline,
                                 "baseline_mismatch": mismatch,
                                 "files_mtime_after_script_start": newer,
                                 "new_pyc_after_script_start": pyc_new,
                                 "write_domain_files": sorted(q.name for q in WD.iterdir() if q.is_file())})

(WD / "_fpw_verify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=2), encoding="utf-8")
print("written: _fpw_verify_out.json")
