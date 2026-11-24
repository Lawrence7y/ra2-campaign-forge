# -*- coding: utf-8 -*-
r"""_dg_step4c.py — 第四步(c) 全量 74 条回归：改前 vs 改后（内存替身，零落盘）。
不改任何既有件：导入 _gp_regression.py 的 CORPUS 定义（它 import 时会构造语料，
但主流程在 __main__ 保护之外——本脚本只读其 CORPUS 全局变量，不写它的输出文件）。

实跑：python -I -X utf8 D:/.../lead/dneg_generative_20261109/_dg_step4c.py
"""
import sys, json, hashlib, importlib.util, pathlib
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# 只读导入：_gp_regression.py 顶层无 __main__ 保护会执行 main，但只写它自己的写域。
# 为避免任何写盘，改为【逐字复制其语料构造】不现实；这里用 runpy 拦截 Path.write_text。
import io, contextlib
_real_write_text = Path.write_text
def _blocked(self, *a, **k):
    if "gate_pipeline_20261109" in str(self):
        return 0          # 拦截既有件输出文件写入，保证绝对只读
    return _real_write_text(self, *a, **k)
Path.write_text = _blocked
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    REG = _load("_dg4c_reg", ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression.py")
Path.write_text = _real_write_text
CORPUS = REG.CORPUS
print("CORPUS n =", len(CORPUS), "（_gp_regression.py 逐字构造，主流程输出已拦截，未写盘）")

g7, n13, T = REG.g7, REG.n13, REG.T
DG = _load("_dg4c_dg", WD / "_dg_core.py")
P = REG.P
r10name = "r10_" + "scan"


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


def judge(item, mode, shim):
    text, toks = item["text"], item["tokens"]
    G = shim if mode.endswith("_dg") else g7
    if mode.startswith("naive"):
        return "CATCH" if any(t in text for t in toks) else "PASS"
    if mode.startswith("r10"):
        r10fn = getattr(G, r10name)
        return "CATCH" if r10fn(text, toks)[0] else "PASS"
    if mode.startswith("r12"):
        return "CATCH" if G.r12_scan(text, toks)[0] else "PASS"
    if mode.startswith("n13"):
        p, _ = n13.r13_assertions(text, T, **{r10name: getattr(G, r10name),
                                               "r12_scan": G.r12_scan})
        return "CATCH" if p else "PASS"
    if mode.startswith("chain"):
        r = P.gate_check(text, toks, WD, G, n13, T)
        adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
        return ("CATCH" if adj else "PASS"), r["summary"]["conflicts"], r["summary"]["unresolved"]
    raise ValueError(mode)


shim = make_shim()
MODES = ["naive", "r10", "r12", "n13", "chain", "r10_dg", "r12_dg", "n13_dg", "chain_dg"]
stat = {m: {"ok": 0, "fp": 0, "fn": 0} for m in MODES}
changed = []
conf_old = conf_new = 0
for it in CORPUS:
    got = {}
    for m in MODES:
        v = judge(it, m, shim)
        if isinstance(v, tuple):
            got[m], nc, nu = v
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
        changed.append({"id": it["id"], "expect": it["expect"],
                        "old": got["chain"], "new": got["chain_dg"],
                        "r12_old": got["r12"], "r12_new": got["r12_dg"],
                        "n13_old": got["n13"], "n13_new": got["n13_dg"],
                        "text": it["text"][:70]})

print("\n=== 改前/改后 74 条全量（实跑）===")
for m in MODES:
    s = stat[m]
    print("  %-9s ok=%-3d FP=%-2d FN=%-2d" % (m, s["ok"], s["fp"], s["fn"]))
print("  chain 层间冲突 old =", conf_old, " new =", conf_new)
print("\n=== 结论变更的条目（chain old -> chain new）===")
for c in changed:
    print("  %-14s expect=%-5s %-5s -> %-5s (r12 %d->%d, n13 %s->%s) | %s" %
          (c["id"], c["expect"], c["old"], c["new"],
           1 if c["r12_old"] == "CATCH" else 0, 1 if c["r12_new"] == "CATCH" else 0,
           c["n13_old"], c["n13_new"], c["text"]))
print("  变更条数 =", len(changed))

# 家族级
fam = {}
for it in CORPUS:
    f = it["family"]
    d = fam.setdefault(f, {"n": 0, "old_ok": 0, "new_ok": 0, "old_fn": 0, "new_fn": 0})
    d["n"] += 1
    o = judge(it, "chain", shim)[0]
    nw = judge(it, "chain_dg", shim)[0]
    d["old_ok"] += (o == it["expect"])
    d["new_ok"] += (nw == it["expect"])
    d["old_fn"] += (o == "PASS" and it["expect"] == "CATCH")
    d["new_fn"] += (nw == "PASS" and it["expect"] == "CATCH")
print("\n=== 按族 ===")
for k, v in fam.items():
    print("  %-26s n=%-3d old_ok=%-3d new_ok=%-3d old_FN=%-2d new_FN=%-2d" %
          (k, v["n"], v["old_ok"], v["new_ok"], v["old_fn"], v["new_fn"]))

out = {"corpus_n": len(CORPUS), "stats": stat, "changed": changed,
       "chain_conflicts_old": conf_old, "chain_conflicts_new": conf_new,
       "by_family": fam, "dg_stats": DG.DG_STATS}
(WD / "_dg_step4c_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dg_step4c_out.json")
