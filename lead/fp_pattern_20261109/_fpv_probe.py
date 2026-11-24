# -*- coding: utf-8 -*-
r"""_fpv_probe.py — 独立复核员：对被核回件的「逐条分类」与关键因果证据做更严格的探针。

只做只读复算（ast/compile-exec 内存加载 + 静态文本），唯一写域 lead/fp_pattern_20261109/。
产出前缀 _fpv_。不改任何对抗集/谓词/语料；不执行判别实验 E1-E6（不改样本、不改谓词）。
"""
import sys, json, re, ast, types, hashlib
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_pattern_20261109"
AI = ROOT / "lead" / "advset_indep_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

OUT = {}
def emit(k, v):
    OUT[k] = v
    print("[%s] %s" % (k, json.dumps(v, ensure_ascii=False)))

def load_src(name, path):
    m = types.ModuleType(name); m.__file__ = str(path)
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), m.__dict__)
    return m
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

DG = load_src("_fpv2_dg", DG_DIR / "_dg_core.py")
H5 = load_src("_fpv2_h5", H5P)
G7 = load_src("_fpv2_g7", G7P)
A = lit_assigns(DGA / "_dga_adversarial.py")
CASES, FORCED = A["CASES"], A["FORCED"]
G = json.loads((AI / "_ai_grade_out.json").read_text(encoding="utf-8"))
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
D = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
byid = {r["id"]: r for r in G["rows"]}
share = {s["id"]: s for s in V["share_rows"]}
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

# ============ (1) d3_pure 与 d3_any：CATCH⇔d3 的准确口径 ============
print("=== (1) d3 口径精确核对 ===")
both = [r["id"] for r in G["rows"] if (r["d3_pure"] or r["d3_dropin"])]
pure_true = [r["id"] for r in G["rows"] if r["d3_pure"]]
dropin_only = [r["id"] for r in G["rows"] if r["d3_dropin"] and not r["d3_pure"]]
catch_pure = [x["id"] for x in V["rows"] if x["verdicts"]["DG_pure"] == "CATCH"]
catch_dropin = [x["id"] for x in V["rows"] if x["verdicts"]["DG_dropin"] == "CATCH"]
emit("d3_scope", {"d3_any_n": len(both), "d3_pure_n": len(pure_true),
     "d3_dropin_only_ids": dropin_only,
     "pure_catch_n": len(catch_pure), "dropin_catch_n": len(catch_dropin),
     "pure_catch_eq_d3_pure_set": set(catch_pure) == set(pure_true),
     "dropin_catch_eq_d3_dropin_set": set(catch_dropin) ==
        set(r["id"] for r in G["rows"] if r["d3_dropin"]),
     "note": "回件 what/§5a 写『41 条 CATCH⇔d3=True 零反例』；精确口径应为 DG_pure CATCH⇔d3_pure（19/19）。"
             "d3_any=21 比 19 多 2 条，该 2 条是 DG_dropin CATCH 而 DG_pure PASS。"})

# ============ (2) fn11 逐条：正则是否命中 / 命中后是否被二次 veto ============
# 这是区分「覆盖不足」与「抑制污染(veto 误杀)」的可观测量，独立于构造者 why 字段。
print("\n=== (2) fn11 独立探针：regex match? veto? ===")
def probe_one(cid):
    c = next(x for x in CASES if x[0] == cid)
    text = c[2]
    toks = [t for t in TOKS if t in text] or ["已生效"]
    # 复刻 dg_scan 的前缀划分
    recs = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[:m.start()]
            masked = DG._mask_quotes(pre)
            scope = DG._scope(masked)
            mm = DG.DG_DROPIN_RE.search(scope)
            r = DG.dg_double_neg(pre, text[m.end():])
            recs.append({"tok": tok, "pre": pre, "scope": scope,
                         "regex_match": mm.group(0) if mm else "",
                         "regex_t3": bool(mm and mm.group("t3")) if mm else False,
                         "hit": r["hit"], "hit_text_field": r["hit_text"],
                         "reason": r["reason"]})
    return recs

FN = D["scoring_strict"]["DG_pure"]["fn_ids"]
fn_probe = {}
for cid in FN:
    recs = probe_one(cid)
    # 归为「regex 命中但被 veto 掉」：任一 token 前缀有 regex_match 但 dg_double_neg hit=False
    veto_killed = any(z["regex_match"] and not z["hit"] for z in recs)
    any_match = any(bool(z["regex_match"]) for z in recs)
    # PSEUDO_DN 词首负向前瞻在正则内部（:116），不产生 match
    pseudo = any(z["hit_text_field"] and DG.DG_COORD_RE.search(z["hit_text_field"]) for z in recs) or \
             any("并列" in z["reason"] or "第二主语" in z["reason"] for z in recs)
    fn_probe[cid] = {"any_regex_match": any_match, "veto_killed_after_match": veto_killed,
                     "coord_or_second_veto_reason": pseudo,
                     "regex_matches": [z["regex_match"] for z in recs if z["regex_match"]],
                     "reasons": [z["reason"] for z in recs if z["reason"]][:2]}
emit("fn11_independent_probe", fn_probe)

# ============ (3) d1 目录是否横跨 H5/R12 自身字面表（跨判定器证据的内生性） ============
print("\n=== (3) d1 目录来源与三判定器表的关系 ===")
H5lit = lit_assigns(H5P)
cat = set(G["catalog"])
h5_branches = [b for b in (H5lit["H5_R12_TEN"] + "|" + H5lit["H5_DN_EXTRA"]).split("|") if b and "[^" not in b]
r12_ten = set(DG.R12_TEN)
r12_g7_forms = set(re.findall(r"\(([^)]*)\)", (G7P.read_text(encoding="utf-8").splitlines()[75])))
g7_ten = set(r12_g7_forms.pop().split("|")) if r12_g7_forms else set()
emit("d1_catalog_endogeneity", {
  "catalog_n": len(cat),
  "h5_literal_branches_n": len(h5_branches),
  "h5_branches_in_catalog": sum(1 for b in h5_branches if b in cat),
  "DG_R12_TEN_n": len(r12_ten), "DG_R12_TEN_in_catalog": sum(1 for b in r12_ten if b in cat),
  "G7_DOUBLE_NEG_forms": sorted(g7_ten),
  "G7_forms_in_catalog": sum(1 for b in g7_ten if b in cat),
  "G7_forms_equal_DG_R12_TEN": g7_ten == r12_ten,
  "note": "d1 的 CATALOG 直接含 H5 字面支与 DG.R12_TEN(=G7 的 10 式)。"
          "故『六判定器 fp 全在 d1 非空』对 H5/R12 也接近定义性必然，"
          "不是三个独立判定器的经验巧合；但『H5/R12 零学习』的源码事实独立成立。"})

# ============ (4) 三个判定器是否真无学习/记忆机制（源码扫描） ============
print("\n=== (4) 零学习机制源码核对 ===")
KEY = re.compile(r"\b(fit|train|training|learn|weight|gradient|pickle|torch|sklearn|numpy|dataset|epoch|model\.|memor)", re.I)
srcs = {"_dg_core.py": DG_DIR / "_dg_core.py", "_h5_pasteable.py": H5P, "_g7_predicates.py": G7P}
scan = {}
for name, p in srcs.items():
    ls = p.read_text(encoding="utf-8").splitlines()
    hit = [(i+1, ls[i].rstrip()[:100]) for i in range(len(ls)) if KEY.search(ls[i])]
    scan[name] = {"n_lines": len(ls), "learning_keyword_hits": hit,
                  "re_compile_calls": sum(1 for l in ls if "re.compile" in l)}
emit("zero_learning_source_scan", scan)

# ============ (5) P16/P17：H5_lit 独有 fp、H5_gov 消失（逐条命中串） ============
print("\n=== (5) H5_lit vs H5_gov 的 P16/P17 ===")
def h5_hits(text):
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    toks = [t for t in TOKS if t in text] or ["已生效"]
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]: hg, hh = True, g["dn_hit"]
    return {"H5_lit": "CATCH" if ml else "PASS", "lit_hit": ml.group(0) if ml else "",
            "H5_gov": "CATCH" if hg else "PASS", "gov_hit": hh}
p1617 = {c[0]: h5_hits(c[2]) for c in CASES if c[0] in ("P16", "P17")}
emit("h5_p16_p17", p1617)
emit("h5_gov_fp_ids_vs_lit", {"H5_lit_fp": D["scoring_strict"]["H5_lit"]["fp_ids"],
     "H5_gov_fp": D["scoring_strict"]["H5_gov"]["fp_ids"],
     "lit_only": sorted(set(D["scoring_strict"]["H5_lit"]["fp_ids"]) -
                        set(D["scoring_strict"]["H5_gov"]["fp_ids"]))})

# ============ (6) 被核回件引用的文档行号逐条核对（挑易错行） ============
print("\n=== (6) 文档行号精确核对 ===")
def L(rel, nums):
    ls = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return {n: (ls[n-1][:160] if n <= len(ls) else "<OOB>") for n in nums}
emit("doc_line_accuracy", {
  "ADVSET_571": L("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", [571]),
  "ADVSET_567_575": L("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", range(567, 576)),
  "ADVSET_266_281": L("lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md", [266, 281]),
  "DGADV_23": L("lead/dg_adversarial_20261109/DG_ADVERSARIAL.md", [23]),
  "DGADV_178_179": L("lead/dg_adversarial_20261109/DG_ADVERSARIAL.md", [178, 179]),
  "DGADV_247": L("lead/dg_adversarial_20261109/DG_ADVERSARIAL.md", [247]),
  "DGADV_308": L("lead/dg_adversarial_20261109/DG_ADVERSARIAL.md", [308]),
  "AIVERIFY_245_246": L("lead/advset_indep_20261109/_ai_verify_stdout.txt", [245, 246]),
  "AIVERIFY_394_402": L("lead/advset_indep_20261109/_ai_verify.py", [394, 402]),
  "AIGRADE_103": L("lead/advset_indep_20261109/_ai_grade.py", [103]),
  "G7_92": L("lead/gate_fp7_20261108/_g7_predicates.py", [92]),
  "G7_144": L("lead/gate_fp7_20261108/_g7_predicates.py", [144]),
})

# ============ (7) 14 词表两处是否一致（_ai_verify vs DG_ADVERSARIAL） ============
print("\n=== (7) 两处 14 词表一致性 ===")
av = (AI / "_ai_verify_stdout.txt").read_text(encoding="utf-8").splitlines()
set_av = re.findall(r"\('([^']+)', 'CATCH'", av[244])
dgmd = (DGA / "DG_ADVERSARIAL.md").read_text(encoding="utf-8").splitlines()
m = re.search(r"词表：`([^`]*)`", dgmd[176])
set_dg = m.group(1).split("/") if m else []
emit("two_14word_sets", {"ai_verify_stdout_245": set_av, "dg_adversarial_177": set_dg,
     "identical": set_av == set_dg, "n_av": len(set_av), "n_dg": len(set_dg),
     "only_in_av": sorted(set(set_av) - set(set_dg)),
     "only_in_dg": sorted(set(set_dg) - set(set_av)),
     "note": "两处都是 14/14 CATCH，但词表不同（两批独立探针）；被核回件把它们并列引用时未区分。"})

(WD / "_fpv_probe_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fpv_probe_out.json")
