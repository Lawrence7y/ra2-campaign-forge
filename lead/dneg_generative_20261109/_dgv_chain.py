# -*- coding: utf-8 -*-
r"""_dgv_chain.py — 独立复核⑤：GP-A1 三层链能不能被兜住。
两种替换口径分别实跑：
  (A) 作者 Shim 口径：r12_scan 换成 DG.dg_scan + r10_context 用 DG 重算 dbl
  (B) 真实「一行替换」口径：加载【第二个真实模块实例】，只把它的模块级
     DOUBLE_NEG_RE 换成 DG.DG_DROPIN_RE——这样 r10_context/r12_scan 的
     __globals__ 确实指向新正则，等价于在文件 :76 改一行。零改动其它函数。
另跑 74 条全量回归（A/B 两口径），核对作者声称的改前/改后数字。
零真机、零采样；纯内存，Path.write_text 拦截保证不写既有件。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_chain.py
"""
import sys, json, hashlib, importlib.util, io, contextlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"
GP = ROOT / "lead" / "gate_pipeline_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
assert hashlib.sha256(G7P.read_bytes()).hexdigest() == \
    "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# 只读导入 74 条语料（拦截既有件写盘）
_real_wt = Path.write_text
def _blocked(self, *a, **k):
    if "gate_pipeline_20261109" in str(self):
        return 0
    return _real_wt(self, *a, **k)
Path.write_text = _blocked
try:
    with contextlib.redirect_stdout(io.StringIO()):
        REG = _load("_dgv_reg", GP / "_gp_regression.py")
finally:
    Path.write_text = _real_wt
print("CORPUS n =", len(REG.CORPUS))

# ★ 两个真实模块实例；oneline 的 __globals__ 与文件改一行等价
G7 = _load("_dgv_g7_base", G7P)
ONELINE = _load("_dgv_g7_oneline", G7P)
DG = _load("_dgv_core2", WD / "_dg_core.py")
ONELINE.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
print("one-line 模拟自检：r10_context.__globals__['DOUBLE_NEG_RE'] is DG =",
      ONELINE.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE,
      " ; base 仍是原十式 =", G7.r10_context.__globals__["DOUBLE_NEG_RE"] is G7.DOUBLE_NEG_RE)

P = _load("_dgv_P", GP / "_gp_pipeline.py")
N13 = _load("_dgv_n13", P.N13_PATH)
T = list(N13.DEFAULT_TOKENS)


def mk_shim():
    """作者 _dg_step4c.py 的 Shim 口径（额外改 r10_context + r12_scan）。"""
    class S: pass
    s = S()
    for a in dir(G7):
        if not a.startswith("__"):
            setattr(s, a, getattr(G7, a))
    s.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
    s.r12_scan = lambda text, tokens: DG.dg_scan(text, tokens)
    _o = G7.r10_context
    def ctx(text, start, end):
        d = dict(_o(text, start, end))
        w = max(0, start - G7.NEG_WINDOW)
        b = max(text.rfind(c, 0, start) for c in G7.CLAUSE_BREAK)
        if b > w: w = b
        d["dbl"] = bool(DG.DG_DROPIN_RE.search(text[w:start]))
        if d["dbl"]: d["kind"] = "double_neg"
        return d
    s.r10_context = ctx
    return s


def chain(mod, item):
    r = P.gate_check(item["text"], item["tokens"], WD, mod, N13, T)
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    return ("CATCH" if adj else "PASS"), r


A = ["GP-A1", "GP-A2", "GP-A3"]
BYID = {it["id"]: it for it in REG.CORPUS}
print("\n=== ⑤ GP-A1/A2/A3 三层链：base / Shim(A) / 一行替换(B) ===")
rows = []
for cid in A:
    it = BYID[cid]
    line = {"id": cid, "expect": it["expect"], "text": it["text"]}
    for tag, mod in (("base", G7), ("shim", mk_shim()), ("oneline", ONELINE)):
        v, r = chain(mod, it)
        line[tag] = v
        line[tag + "_layers"] = {k: val["problems_n"] for k, val in r["layers"].items()}
        line[tag + "_conflicts"] = r["summary"]["conflicts"]
        line[tag + "_spans"] = [
            {"tok": x["token"], "pos": x["pos"], "r10": x["r10"], "r12": x["r12"],
             "n13": x["n13"], "verdict": x["verdict"], "rules": x["rules"]}
            for x in r["_rows"]]
    rows.append(line)
    print("  %-6s expect=%-5s base=%-5s shim=%-5s oneline=%-5s | layers(base/shim/oneline)=%s / %s / %s" %
          (cid, it["expect"], line["base"], line["shim"], line["oneline"],
           line["base_layers"], line["shim_layers"], line["oneline_layers"]))
    for x in line["oneline_spans"]:
        print("      [oneline span] tok=%s pos=%d r10=%s r12=%s n13=%s => %s rules=%s" %
              (x["tok"], x["pos"], x["r10"], x["r12"], x["n13"], x["verdict"], ",".join(x["rules"])))

# 74 条全量（base / Shim / 一行替换 三口径），只统计 chain
print("\n=== ⑤-b 74 条 chain 全量（三口径）===")
stat = {}
MODS = {"base": G7, "shim": mk_shim(), "oneline": ONELINE}
for tag, mod in MODS.items():
    ok = fp = fn = conf = 0
    per = {}
    for it in REG.CORPUS:
        v, r = chain(mod, it)
        conf += r["summary"]["conflicts"]
        per[it["id"]] = v
        if v == it["expect"]: ok += 1
        elif it["expect"] == "PASS": fp += 1
        else: fn += 1
    stat[tag] = {"ok": ok, "fp": fp, "fn": fn, "conflicts": conf, "per": per}
    print("  %-8s ok=%-3d FP=%-2d FN=%-2d conflicts=%d" % (tag, ok, fp, fn, conf))
for tag in ("shim", "oneline"):
    ch = [(i, stat["base"]["per"][i], stat[tag]["per"][i], BYID[i]["expect"])
          for i in stat["base"]["per"] if stat["base"]["per"][i] != stat[tag]["per"][i]]
    print("  %-8s 变更条数=%d : %s" % (tag, len(ch), ch[:20]))

print("\n=== ⑤-c 与作者申报数字比对 ===")
claim = json.loads((WD / "_dg_step4c_out.json").read_text("utf-8"))
print("  作者 _dg_step4c_out.json stats(chain/chain_dg) =",
      {k: {q: claim["stats"][k][q] for q in ("ok", "fp", "fn")} for k in ("chain", "chain_dg")})
print("  作者 chain_conflicts_old/new =", claim["chain_conflicts_old"], claim["chain_conflicts_new"])
print("  本复核 base/shim/oneline chain =", [(t, stat[t]["ok"], stat[t]["fp"], stat[t]["fn"], stat[t]["conflicts"])
                                            for t in stat])

# 一行替换在自造负样本上的 delta（③④，用真实模块实例）
NEG = [
    ("V01", "「并非不宣告已生效」只是引文，本件不采信该说法。"),
    ("V02", "别处不得不承认但本件不宣告已生效"),
    ("V03", "旧稿并不否认然而本件不宣告已生效"),
    ("V04", "并不否认甲方不宣告已生效"),
    ("V05", "并没有不承认但本件只登记已入账"),
    ("V06", "无越权断言：本件不出现「可应用母本…」。"),
    ("V07", "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；"),
    ("V12", "不得不承认旧稿却本件不宣告已生效"),
    ("V13", "并不否认本笔不宣告已生效"),
    ("V15", "本件不承认、并不否认均不成立已生效"),
]
print("\n=== ⑤-d 一行替换在 10 条自造负样本上的 base→oneline 变化 ===")
neg_rows = []
for cid, text in NEG:
    toks = [t for t in ("已生效", "已入账", "可应用母本", "放行 N-5") if t in text] or ["已生效"]
    vb, _ = chain(G7, {"text": text, "tokens": toks})
    vo, ro = chain(ONELINE, {"text": text, "tokens": toks})
    dbl = [ONELINE.r10_context(text, m.start(), m.end())["dbl"]
           for tok in toks for m in __import__("re").finditer(__import__("re").escape(tok), text)]
    neg_rows.append({"id": cid, "base": vb, "oneline": vo, "dbl_any": any(dbl),
                     "r12_problems": len(ONELINE.r12_scan(text, toks)[0])})
    print("  %-4s base=%-5s oneline=%-5s dbl=%-5s r12=%d | %s" %
          (cid, vb, vo, any(dbl), len(ONELINE.r12_scan(text, toks)[0]), text[:42]))
print("  → base CATCH 数 =", sum(r["base"] == "CATCH" for r in neg_rows),
      "; oneline CATCH 数 =", sum(r["oneline"] == "CATCH" for r in neg_rows),
      "; 新增 CATCH =", [r["id"] for r in neg_rows if r["base"] != "CATCH" and r["oneline"] == "CATCH"])

out = {"corpus_n": len(REG.CORPUS), "gp_rows": rows,
       "chain_stat": {k: {q: v[q] for q in ("ok", "fp", "fn", "conflicts")} for k, v in stat.items()},
       "changed_vs_base": {t: [(i, stat["base"]["per"][i], stat[t]["per"][i])
                               for i in stat["base"]["per"] if stat["base"]["per"][i] != stat[t]["per"][i]]
                           for t in ("shim", "oneline")},
       "author_claim": {"stats": claim["stats"],
                        "chain_conflicts_old": claim["chain_conflicts_old"],
                        "chain_conflicts_new": claim["chain_conflicts_new"]},
       "oneline_negatives": neg_rows}
(WD / "_dgv_chain_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_chain_out.json")
