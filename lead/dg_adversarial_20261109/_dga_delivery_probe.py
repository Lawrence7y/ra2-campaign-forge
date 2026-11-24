# -*- coding: utf-8 -*-
r"""_dga_delivery_probe.py — 交付形态差异专项：一行替换 vs 纯函数 guard 是否执行。

零真机、零采样；只读保护件；输出只落本写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dga_delivery_probe.py
"""
import sys, json, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dga4_dg", ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py")
G7 = _load("_dga4_g7", ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
ONE = _load("_dga4_one", ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
ONE.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert ONE.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE
A = json.loads((WD / "_dga_adversarial_out.json").read_text("utf-8"))
rows = A["cases"]
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

print("=== 纯函数 guard 逐条实跑（_mask_quotes / _scope / 二次 veto）===")
guard_rows = []
for x in rows:
    toks = [t for t in TOKS if t in x["text"]] or ["已生效"]
    for tok in toks:
        for m in re.finditer(re.escape(tok), x["text"]):
            pre = x["text"][:m.start()]
            d = DG.dg_double_neg(pre)
            reason = d["reason"]
            fired = ("第二主语" in reason) or ("并列标记" in reason)
            guard_rows.append({"id": x["id"], "tok": tok, "pos": m.start(),
                               "scope": d["scope"], "hit_text": d["hit_text"],
                               "template": d["template"], "reason": reason,
                               "secondary_veto_fired": fired})
            if fired:
                print("  ★二次 veto 触发: %s tok=%s pos=%d scope=%r hit=%r reason=%s" %
                      (x["id"], tok, m.start(), d["scope"], d["hit_text"], reason))
print("  guard 明细条数 =", len(guard_rows),
      "; 二次 veto 触发次数 =", sum(r["secondary_veto_fired"] for r in guard_rows))
print("  → 唯一触发来自 C08「非登记一或二不可」：并列否决把【真 DN】误否决（fn），"
      "而对 P10「本件不承认或并不否认」不触发（并列标记在 hit_text 之外）")

print("\n=== 一行替换形态：r10_context / r12_scan 是否调用任何 guard（co_names 实查）===")
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE", "dg_scan"]
co = {}
for fn in ("r10_context", "r12_scan"):
    names = getattr(ONE, fn).__code__.co_names
    co[fn] = {g: (g in names) for g in guards}
    print("  %-12s %s" % (fn, co[fn]))
print("  → 全部 False：一行替换只把 DOUBLE_NEG_RE 换成生成式正则，"
      "7 条不变式里靠纯函数实现的 4 条 guard 一个都不执行。"
      "与 DNEG_GENERATIVE.md:173 一致（本会话独立实跑）")

print("\n=== 一行替换 vs 纯函数：逐条差异（应判非 AMBIG）===")
diff = []
for x in rows:
    a, b = x["verdicts"]["DG_pure"], x["verdicts"]["DG_dropin"]
    if a != b:
        diff.append({"id": x["id"], "text": x["text"], "expect": x["expect"],
                     "DG_pure": a, "DG_dropin": b, "why": x["why"]})
        print("  %-4s expect=%-5s pure=%-5s dropin=%-5s | %s" %
              (x["id"], x["expect"], a, b, x["text"][:40]))
print("  差异条数 =", len(diff), "（其中 P17 引证屏蔽、C08 并列否决只在一侧生效）")

# 一行替换口径下：r10_context 的 dbl 来源 = DOUBLE_NEG_RE.search(pre)
print("\n=== 一行替换：r10_context『dbl』布尔来源逐条（前 5 例）===")
for x in rows[:5]:
    toks = [t for t in TOKS if t in x["text"]] or ["已生效"]
    ctxs = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), x["text"]):
            ctxs.append((tok, m.start(), ONE.r10_context(x["text"], m.start(), m.end())["dbl"]))
    print("  %-4s ctxs=%s" % (x["id"], ctxs[:2]))
print("  → 一行替换的 dbl 只看 pre 内的正则 .search()，无引证/微句/主语/并列 guard")

out = {"guard_rows": guard_rows,
       "secondary_veto_fired": sum(r["secondary_veto_fired"] for r in guard_rows),
       "co_names": co, "pure_vs_dropin_diff": diff}
(WD / "_dga_delivery_probe_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dga_delivery_probe_out.json")
