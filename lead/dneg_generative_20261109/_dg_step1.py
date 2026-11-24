# -*- coding: utf-8 -*-
r"""_dg_step1.py — 第一步(a)(b)：独立复核 19 式漏判面 + 结构分类。
零真机、零采样；只读既有谓词（hashlib 先验指纹），输出只落本写域。
实跑：python -I -X utf8 D:/.../lead/dneg_generative_20261109/_dg_step1.py
"""
import sys, json, hashlib, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
FP_PRED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
FP_GAP = "ffd552207039b220e2a3e649af32aea25bbcd923fe6f9742a8bdb634cb837dc6"

def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

b = PRED.read_bytes()
assert hashlib.sha256(b).hexdigest() == FP_PRED and len(b) == 11743, "谓词指纹失配"
g7 = _load("_dg_g7", PRED)
DG = _load("_dg_core_mod", WD / "_dg_core.py")
gap_out = ROOT / "lead" / "h5_governance_20261109" / "_h5_r12_gap_out.json"
assert hashlib.sha256(gap_out.read_bytes()).hexdigest() == FP_GAP

# 19 式（逐字取自 _h5_r12_gap.py:27-47，与编排方背景清单一致），本地重列不采信 JSON 结论
GAPS = [
    ("亦非不", "亦非不宣告 N-4 正式绑定已生效", "亦", "非", "", "不", "COP_NEG"),
    ("未尝不", "未尝不认为本件已生效", "", "未", "尝", "不", "ASP_NEG"),
    ("未始不", "未始不认为本件已生效", "", "未", "始", "不", "ASP_NEG"),
    ("未有不", "未有不认为本件已生效", "", "未", "有", "不", "EXIST_NEG"),
    ("莫不", "莫不认为本件已生效", "", "莫", "", "不", "UNIV_NEG"),
    ("不敢不", "不敢不承认本件已生效", "", "不", "敢", "不", "MOD_NEG"),
    ("不会不", "不会不承认本件已生效", "", "不", "会", "不", "MOD_NEG"),
    ("不可能不", "不可能不宣告本件已生效", "", "不", "可能", "不", "MOD_NEG"),
    ("未必不", "未必不认为本件已生效", "", "未", "必", "不", "EPIST_NEG"),
    ("未免不", "未免不认为本件已生效", "", "未", "免", "不", "EPIST_NEG"),
    ("岂能不", "岂能不说本件已生效", "岂", "", "能", "不", "RHET_NEG"),
    ("焉能不", "焉能不说本件已生效", "焉", "", "能", "不", "RHET_NEG"),
    ("哪能不", "哪能不说本件已生效", "哪", "", "能", "不", "RHET_NEG"),
    ("不可谓不", "不可谓不宣告本件已生效", "", "不", "可谓", "不", "MOD_NEG"),
    ("不为不", "不为不认为本件已生效", "", "不", "为", "不", "COP_NEG"),
    ("并非没有", "并非没有宣告本件已生效", "", "并非", "", "没有", "NEG_PRED"),
    ("并非毫无", "并非毫无宣告本件已生效", "", "并非", "", "毫无", "NEG_PRED"),
    ("不是没有", "不是没有宣告本件已生效", "", "不是", "", "没有", "NEG_PRED"),
    ("并不否认", "并不否认本件已生效", "", "并不", "", "否认", "NEG_PRED"),
]
CTRL_CATCH = ["不得不承认本候选已生效", "并非不宣告已生效", "并不是不认为本件已生效",
              "不是不承认本件已生效", "无不认为本件已生效", "不能不说本件已生效",
              "不可不说本件已生效", "未曾不认为本件已生效", "没有不承认本件已生效",
              "不无认为本件已生效"]
TOK = "已生效"

print("=== (0) 指纹 ===")
print("  _g7_predicates.py sha256 =", FP_PRED, "bytes =", len(b))
print("  _h5_r12_gap_out.json sha256 =", FP_GAP, "bytes =", gap_out.stat().st_size)
print("  DOUBLE_NEG_RE.pattern =", g7.DOUBLE_NEG_RE.pattern)

print("\n=== (1a) 19 式逐条独立复核（regex_hit / r10_kind / r10_dbl / r12_problems）===")
rows = []
for name, text, adv, n1, mid, n2, cat in GAPS:
    pos = text.find(TOK)
    ctx = g7.r10_context(text, pos, pos + len(TOK))
    p12, h12 = g7.r12_scan(text, [TOK])
    rhit = bool(g7.DOUBLE_NEG_RE.search(name))
    pdg, hdg = DG.dg_scan(text, [TOK])
    r = {"construct": name, "text": text, "regex_hit": rhit,
         "r10_kind": ctx["kind"], "r10_dbl": ctx["dbl"],
         "r10_neg_count": ctx["neg_count"], "r12_problems": len(p12),
         "dg_problems": len(pdg), "dg_hit": hdg[0]["hit"] if hdg else "",
         "struct": {"adv": adv, "N1": n1, "MID": mid, "N2": n2}, "category": cat,
         "verdict": "漏判确认" if (not rhit and len(p12) == 0) else "矛盾"}
    rows.append(r)
    print("  %-9s regex_hit=%-5s r10_kind=%-9s r10_dbl=%-5s neg_count=%d r12_problems=%d  => %-8s | DG=%d hit=%s" %
          (name, str(rhit).lower(), ctx["kind"], str(ctx["dbl"]).lower(),
           ctx["neg_count"], len(p12), r["verdict"], len(pdg), r["dg_hit"]))
n_ok = sum(1 for r in rows if r["regex_hit"] is False and r["r12_problems"] == 0)
print("  → 19 式中 regex_hit=false 且 r12_problems=0 : %d/%d" % (n_ok, len(rows)))

print("\n=== (1a-ctrl) 编排方给的 6 条对照（4 漏 + 2 CATCH）===")
for text in ["亦非不宣告 N-4 正式绑定已生效", "未尝不认为本件已生效",
             "莫不认为本件已生效", "不敢不承认本件已生效",
             "并非不宣告已生效", "不得不承认本件已生效"]:
    pos = text.find(TOK)
    ctx = g7.r10_context(text, pos, pos + len(TOK))
    p12, _ = g7.r12_scan(text, [TOK])
    print("  %-32s r10kind=%-11s r12=%d  => %s" %
          (text, ctx["kind"], len(p12), "PASS(漏)" if len(p12) == 0 else "CATCH"))

print("\n=== (1a-R12ten) 既有十式逐字复核（防退化基线）===")
ten_rows = []
for c in DG.R12_TEN:
    ten_rows.append({"construct": c,
                     "r12_regex": bool(g7.DOUBLE_NEG_RE.search(c)),
                     "dg_regex": bool(DG.DG_DROPIN_RE.search(c))})
    print("  %-9s R12_regex=%-5s DG_regex=%s" %
          (c, ten_rows[-1]["r12_regex"], ten_rows[-1]["dg_regex"]))
print("  → 十式 R12 全 True=%s ; DG 全 True=%s" %
      (all(x["r12_regex"] for x in ten_rows), all(x["dg_regex"] for x in ten_rows)))
for text in CTRL_CATCH:
    p12, _ = g7.r12_scan(text, [TOK])
    pdg, _ = DG.dg_scan(text, [TOK])
    print("  %-30s r12=%d dg=%d" % (text, len(p12), len(pdg)))

print("\n=== (1b) 共同结构分类 ===")
cats = {}
for r in rows:
    cats.setdefault(r["category"], []).append(r["construct"])
for k, v in cats.items():
    print("  %-10s n=%-2d : %s" % (k, len(v), " / ".join(v)))

out = {"predicate_sha256": FP_PRED, "predicate_bytes": len(b),
       "gap_json_sha256": FP_GAP, "re_pattern": g7.DOUBLE_NEG_RE.pattern,
       "gap_rows": rows, "gap_confirmed": n_ok, "gap_total": len(rows),
       "r12_ten": ten_rows, "categories": cats, "dg_stats": DG.DG_STATS}
(WD / "_dg_step1_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dg_step1_out.json")
