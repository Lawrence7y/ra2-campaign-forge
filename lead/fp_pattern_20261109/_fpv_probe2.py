# -*- coding: utf-8 -*-
r"""_fpv_probe2.py — 独立复核员：修正 _fpv_probe.py 两个字段的探针缺陷，并补 fp7 护栏归因核对。

缺陷说明（如实登记）：_fpv_probe.py 的 coord_or_second_veto_reason 用 "并列" 子串匹配 reason，
而 dg_double_neg 的通用 no-match reason 本身含「微句/引证/并列/距离切断」，导致 11/11 全 True（假阳性）；
G7_DOUBLE_NEG_forms 用 re.findall(r"\(([^)]*)\)") 扫 :76 把 r"(不得不" 的前缀一起吞了。
本件用精确口径重做这两项，不删改 _fpv_probe.py / _fpv_probe_stdout.txt。
只读复算；唯一写域 lead/fp_pattern_20261109/，前缀 _fpv_。
"""
import sys, json, re, ast, types
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
DG = load_src("_fpv3_dg", DG_DIR / "_dg_core.py")
G7 = load_src("_fpv3_g7", G7P)
A = ast.parse((DGA / "_dga_adversarial.py").read_text(encoding="utf-8"))
ASG = {}
for n in A.body:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name):
                try: ASG[t.id] = ast.literal_eval(n.value)
                except Exception: pass
CASES = ASG["CASES"]
V = json.loads((AI / "_ai_verify_out.json").read_text(encoding="utf-8"))
D = json.loads((DGA / "_dga_adversarial_out.json").read_text(encoding="utf-8"))
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

print("=== (1) fn11 veto 机制【精确】分类（修正 _fpv_probe.py 的假阳性字段） ===")
# 精确判据：
#   (a) 后置 veto 误杀 = DG_DROPIN_RE 在 scope 上有 Match，但 dg_double_neg 因
#       DG_SECOND_SUBJ_RE / DG_COORD_RE 在 hit_text 内命中而返回 hit=False（:179-184）。
#   (b) 正则内 veto = PSEUDO_DN 词首负向前瞻(:116) 使 search 直接不产生 Match。
#   (c) 覆盖不足 = 无 Match 且不属于 (b)。
FN = D["scoring_strict"]["DG_pure"]["fn_ids"]
detail = {}
for cid in FN:
    c = next(x for x in CASES if x[0] == cid)
    text = c[2]
    toks = [t for t in TOKS if t in text] or ["已生效"]
    recs = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[:m.start()]
            masked = DG._mask_quotes(pre)
            scope = DG._scope(masked)
            mm = DG.DG_DROPIN_RE.search(scope)
            r = DG.dg_double_neg(pre, text[m.end():])
            recs.append({"match": mm.group(0) if mm else "",
                         "hit": r["hit"],
                         "coord_in_hit_text": bool(r["hit_text"] and DG.DG_COORD_RE.search(r["hit_text"])),
                         "second_in_hit_text": bool(r["hit_text"] and DG.DG_SECOND_SUBJ_RE.search(r["hit_text"])),
                         "pseudo_in_pre": any(w in pre for w in DG.PSEUDO_DN)})
    post_veto = any(z["match"] and not z["hit"] and (z["coord_in_hit_text"] or z["second_in_hit_text"]) for z in recs)
    pseudo_pre = any(z["pseudo_in_pre"] for z in recs) and not any(z["match"] for z in recs)
    coverage = not any(z["match"] for z in recs) and not pseudo_pre
    cls = "后置veto误杀(:179-184)" if post_veto else ("正则内PSEUDO否定前瞻(:116)" if pseudo_pre else "覆盖不足(无Match)")
    detail[cid] = {"class": cls, "regex_match": [z["match"] for z in recs if z["match"]],
                   "post_veto": post_veto, "pseudo_negative_lookahead": pseudo_pre}
emit("fn11_veto_mechanism_exact", detail)
from collections import Counter
emit("fn11_veto_mechanism_counts", dict(Counter(z["class"] for z in detail.values())))

print("\n=== (2) G7 DOUBLE_NEG_RE 十式【精确】与 DG.R12_TEN 比对（修正解析缺陷） ===")
line76 = (G7P.read_text(encoding="utf-8").splitlines()[75])
m = re.search(r"re\.compile\(r\"\(([^)]*)\)\"\)", line76)
g7_ten = set(m.group(1).split("|")) if m else set()
emit("g7_ten_exact", {"line76": line76.strip(), "n": len(g7_ten), "forms": sorted(g7_ten),
     "equals_DG_R12_TEN": g7_ten == set(DG.R12_TEN),
     "DG_R12_TEN": sorted(set(DG.R12_TEN)),
     "note": "G7 DOUBLE_NEG_RE 十式与 DG.R12_TEN 逐字相同（:76 注释亦自述『对账锚』）。"})

print("\n=== (3) fp7 逐条护栏归因独立探针 ===")
# 对每条 fp：找使 CATCH 的 token 前缀，报告 scope / match / 是否被引号屏蔽 / 是否在 BREAK_RE 内
FP = D["scoring_strict"]["DG_pure"]["fp_ids"]
fp_guard = {}
for cid in FP:
    c = next(x for x in CASES if x[0] == cid)
    text = c[2]
    toks = [t for t in TOKS if t in text] or ["已生效"]
    recs = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[:m.start()]
            masked = DG._mask_quotes(pre)
            scope = DG._scope(masked)
            mm = DG.DG_DROPIN_RE.search(scope)
            if mm:
                recs.append({"tok": tok, "pre": pre, "masked_changed": masked != pre,
                             "scope": scope, "match": mm.group(0),
                             "t3": bool(mm.group("t3")),
                             "break_words_in_pre": [w for w in
                                ["其实","说到底","尽管","但","然而","不过","却","只是","反之","相反","另外","另"]
                                if w in pre],
                             "quote_re_matched": bool(DG.DG_QUOTE_RE.search(pre)),
                             "coord_outside_hit": any(w in pre and w not in mm.group(0)
                                for w in ["或","以及","同时","并且"])})
    fp_guard[cid] = recs
emit("fp7_guard_probe", fp_guard)
emit("fp7_guard_summary", {c: {"n_match": len(r),
     "masked_changed": any(z["masked_changed"] for z in r),
     "quote_re_matched": any(z["quote_re_matched"] for z in r),
     "break_words": [z["break_words_in_pre"] for z in r],
     "coord_outside_hit": any(z["coord_outside_hit"] for z in r),
     "match": [z["match"] for z in r]} for c, r in fp_guard.items()})

print("\n=== (4) fn 三类分组与回件『8 覆盖不足 + 3 veto 误杀』的对应 ===")
emit("fn_class_vs_claim", {
  "claimed": {"覆盖不足": 8, "抑制污染(veto 误杀)": 3},
  "claimed_ids": {"覆盖不足": ["C01","C02","C03","C04","C05","C07","C09","C10"],
                  "veto误杀": ["C08","C11","C12"]},
  "my_exact": {"覆盖不足(无Match)": sorted([c for c,z in detail.items() if z["class"].startswith("覆盖不足")]),
               "后置veto": sorted([c for c,z in detail.items() if z["class"].startswith("后置veto")]),
               "正则内PSEUDO": sorted([c for c,z in detail.items() if z["class"].startswith("正则内")])},
  "note": "回件把 C08/C11/C12 合并为『抑制污染(veto 误杀)』3 条；我的精确探针显示 C08 是后置 veto"
          "（有 Match 再被 DG_COORD_RE 否），C11/C12 是正则内负向前瞻（根本不产生 Match）。"
          "3 条计数成立，但两种 veto 机制不同，修复方向也应分开（回件 §3(d) 已分开列）。"})

(WD / "_fpv_probe2_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fpv_probe2_out.json")
