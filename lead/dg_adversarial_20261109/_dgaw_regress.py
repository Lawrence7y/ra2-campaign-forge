# -*- coding: utf-8 -*-
r"""_dgaw_regress.py — 本会话独立重跑 74 条三层回归 + GP-A2/A3 + 真实一行替换层间冲突。

★ 只读保护件：导入 _gp_regression.py 时拦截 Path.write_text，只允许写本写域，
  其余一律吞掉写盘并返回 0（与既有 _dga_step1_repro.py:180-206 同口径）。
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_regress.py
"""
import sys, json, io, contextlib, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
REGP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgaw_r_dg", DG_DIR / "_dg_core.py")

_real_write = Path.write_text
blocked = []


def _blocked(self, *a, **k):
    if "dg_adversarial_20261109" in str(self):
        return _real_write(self, *a, **k)
    blocked.append(str(self))
    return 0


Path.write_text = _blocked
try:
    with contextlib.redirect_stdout(io.StringIO()):
        REG = _load("_dgaw_r_reg", REGP)
finally:
    Path.write_text = _real_write
print("=== (0) 74 条语料导入（保护件写盘拦截）===")
print("  CORPUS n =", len(REG.CORPUS), "; 被拦截写盘 =", blocked)

CORPUS = REG.CORPUS
g7, n13, T, P = REG.g7, REG.n13, REG.T, REG.P
r10name = "r10_" + "scan"


def judge(item, mode, G):
    text, toks = item["text"], item["tokens"]
    if mode.startswith("naive"):
        return "CATCH" if any(t in text for t in toks) else "PASS"
    if mode.startswith("r10"):
        return "CATCH" if getattr(G, r10name)(text, toks)[0] else "PASS"
    if mode.startswith("r12"):
        return "CATCH" if G.r12_scan(text, toks)[0] else "PASS"
    if mode.startswith("n13"):
        p, _ = n13.r13_assertions(text, T, **{r10name: getattr(G, r10name),
                                               "r12_scan": G.r12_scan})
        return "CATCH" if p else "PASS"
    if mode.startswith("chain"):
        r = P.gate_check(text, toks, WD, G, n13, T)
        adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
        return ("CATCH" if adj else "PASS"), r["summary"]["conflicts"]
    raise ValueError(mode)


# ---- (A) 作者 Shim 口径（与 _dga_step1_repro.py:219-260 同构）----
class _Shim:
    pass


def make_shim():
    s = _Shim()
    for a in dir(g7):
        if not a.startswith("__"):
            setattr(s, a, getattr(g7, a))
    s.r12_scan = lambda text, tokens: DG.dg_scan(text, tokens)
    s.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
    _orig = g7.r10_context

    def ctx(text, start, end):
        d = dict(_orig(text, start, end))
        w = max(0, start - g7.NEG_WINDOW)
        b = max(text.rfind(c, 0, start) for c in g7.CLAUSE_BREAK)
        if b > w:
            w = b
        d["dbl"] = bool(DG.DG_DROPIN_RE.search(text[w:start]))
        if d["dbl"]:
            d["kind"] = "double_neg"
        return d

    s.r10_context = ctx
    return s


shim = make_shim()
MODES = ["naive", "r10", "r12", "n13", "chain", "r10_dg", "r12_dg", "n13_dg", "chain_dg"]
stat = {m: {"ok": 0, "fp": 0, "fn": 0} for m in MODES}
changed, conf_old, conf_new = [], 0, 0
print("\n=== (A) 作者 Shim 口径：改前 vs DG 改后 ===")
for it in CORPUS:
    got = {}
    for m in MODES:
        v = judge(it, m, shim if m.endswith("_dg") else g7)
        if isinstance(v, tuple):
            got[m], nc = v
            if m == "chain":
                conf_old += nc
            else:
                conf_new += nc
        else:
            got[m] = v
        g = got[m]
        if g == it["expect"]:
            stat[m]["ok"] += 1
        elif it["expect"] == "PASS":
            stat[m]["fp"] += 1
        else:
            stat[m]["fn"] += 1
    if got["chain"] != got["chain_dg"]:
        changed.append((it["id"], got["chain"] + "->" + got["chain_dg"]))
for m in MODES:
    s = stat[m]
    print("  %-9s ok=%-3d FP=%-2d FN=%-2d" % (m, s["ok"], s["fp"], s["fn"]))
print("  chain 层间冲突 old =", conf_old, " new =", conf_new)
print("  结论变更条目 =", changed, "; 变更条数 =", len(changed))

# ---- (B) 真实一行替换口径：第二真实模块实例，只换 DOUBLE_NEG_RE ----
ONELINE = _load("_dgaw_r_one", G7P)
ONELINE.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
stat2, conf_base, conf_one = {}, 0, 0
for m in ("chain",):
    stat2[m] = {"ok": 0, "fp": 0, "fn": 0}
    stat2[m + "_oneline"] = {"ok": 0, "fp": 0, "fn": 0}
print("\n=== (B) 真实一行替换口径：base vs oneline ===")
for it in CORPUS:
    for m, G in (("chain", g7), ("chain_oneline", ONELINE)):
        got, nc = judge(it, "chain", G)
        if m == "chain":
            conf_base += nc
        else:
            conf_one += nc
        if got == it["expect"]:
            stat2[m]["ok"] += 1
        elif it["expect"] == "PASS":
            stat2[m]["fp"] += 1
        else:
            stat2[m]["fn"] += 1
for m in stat2:
    s = stat2[m]
    print("  %-15s ok=%-3d FP=%-2d FN=%-2d" % (m, s["ok"], s["fp"], s["fn"]))
print("  真实一行替换层间冲突 = %d → %d（base → oneline）" % (conf_base, conf_one))

# ---- (C) GP-A1/A2/A3 逐条诊断 ----
print("\n=== (C) GP-A1/A2/A3 逐条诊断 ===")
diag = []
for cid, text in [("GP-A1", "亦非不宣告 N-4 正式绑定已生效"),
                  ("GP-A2", "本件登记闭合，母本即日起适用"),
                  ("GP-A3", "三值填毕，见证已由编排方签字")]:
    spans = P.extract_spans(text, T)
    p10 = getattr(g7, r10name)(text, T)[0]
    p12 = g7.r12_scan(text, T)[0]
    pn13 = n13.r13_assertions(text, T, **{r10name: getattr(g7, r10name),
                                           "r12_scan": g7.r12_scan})[0]
    pdg = DG.dg_scan(text, T)[0]
    bc = judge({"text": text, "tokens": T, "expect": "CATCH", "id": cid}, "chain", g7)[0]
    dc = judge({"text": text, "tokens": T, "expect": "CATCH", "id": cid}, "chain", shim)[0]
    row = {"id": cid, "text": text, "spans": spans["count"],
           "tokens": [x["token"] for x in spans["spans"]],
           "r10": len(p10), "r12": len(p12), "n13": len(pn13), "dg_r12": len(pdg),
           "base_chain": bc, "dg_chain": dc}
    diag.append(row)
    print("  %-6s spans=%d tokens=%s r10=%d r12=%d n13=%d DG_r12=%d base_chain=%-5s DG_chain=%-5s | %s"
          % (cid, row["spans"], row["tokens"], row["r10"], row["r12"], row["n13"],
             row["dg_r12"], row["base_chain"], row["dg_chain"], text))
print("  DEFAULT_TOKENS =", list(T))
syn = ["登记闭合", "即日起适用", "填毕", "已由编排方签字"]
print("  同义完成词族逐词 in_vocab =", {w: w in T for w in syn})

(WD / "_dgaw_regress_out.json").write_text(json.dumps(
    {"corpus_n": len(CORPUS), "blocked": blocked, "shim": {"stat": stat,
     "conflicts_old": conf_old, "conflicts_new": conf_new, "changed": changed},
     "oneline": {"stat": stat2, "conflicts_base": conf_base, "conflicts_oneline": conf_one},
     "gp_diag": diag}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgaw_regress_out.json")
