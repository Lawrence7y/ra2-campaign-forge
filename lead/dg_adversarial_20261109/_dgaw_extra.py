# -*- coding: utf-8 -*-
r"""_dgaw_extra.py — 复核回件指出的 3 项「未验其实已验」及闭合表口径的独立重跑。"""
import sys, ast, json, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgaw_e_dg", DG_DIR / "_dg_core.py")
H5 = _load("_dgaw_e_h5", ROOT / "lead/h5_governance_20261109/_h5_pasteable.py")
G7 = _load("_dgaw_e_g7", ROOT / "lead/gate_fp7_20261108/_g7_predicates.py")
DROP = _load("_dgaw_e_drop", ROOT / "lead/gate_fp7_20261108/_g7_predicates.py")
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
OUT = {}

print("=== (1) _dg_core.py 顶层闭合表 AST 计数 ===")
tree = ast.parse((DG_DIR / "_dg_core.py").read_text(encoding="utf-8"))
tables = []
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple):
        for t in node.targets:
            if isinstance(t, ast.Name):
                tables.append((t.id, len(ast.literal_eval(node.value)), node.lineno))
for name, n, ln in tables:
    print("  %-14s n=%-3d :%d" % (name, n, ln))
core = [x for x in tables if x[0] != "R12_TEN"]
print("  → 参与生成式的闭合表 = %d 张 %s ; 加 R12_TEN 对账锚 = %d 张（DNEG_GENERATIVE.md:163 记 6 张）"
      % (len(core), [x[0] for x in core], len(tables)))
OUT["tables"] = tables

print("\n=== (2) DNEG_GENERATIVE.md:346 的 16/17 vs 0/17 独立重跑 ===")
C17 = ["何尝不", "安能不", "岂敢不", "没法不", "并非未", "并非无", "不由得不",
       "忍不住不", "不见得不", "不一定不", "不是没", "非写成已入账不可", "非登记不可",
       "非说不", "没说不", "没法不说", "非但不"]
rows17 = []
for c in C17:
    dg = bool(DG.DG_DROPIN_RE.search(c))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(c))
    r12 = bool(G7.DOUBLE_NEG_RE.search(c))
    rows17.append({"c": c, "dg": dg, "h5": h5, "r12": r12})
    print("  %-16s DG=%-5s H5=%-5s R12=%s" % (c, dg, h5, r12))
print("  → DG %d/17 ; H5 %d/17 ; R12 %d/17"
      % (sum(x["dg"] for x in rows17), sum(x["h5"] for x in rows17), sum(x["r12"] for x in rows17)))

print("\n=== (3) DNEG_GENERATIVE.md:347 分离型 post 整句 0/4 独立重跑 ===")
S4 = ["非写成已入账不可", "不宣告已生效不行", "非登记已入账不可", "不写成已入账不成"]
TOKS = ["已生效", "已入账", "已追加"]
rows4 = []
for t in S4:
    toks = [x for x in TOKS if x in t] or ["已生效"]
    pure, _ = DG.dg_scan(t, toks)
    drop, _ = DROP.r12_scan(t, toks)
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(t))
    rows4.append({"t": t, "pure": bool(pure), "drop": bool(drop), "h5": h5})
    print("  %-22s DG_pure=%-5s DG_dropin=%-5s H5_lit=%-5s" % (t, bool(pure), bool(drop), h5))
print("  → DG_pure CATCH %d/4 ; DG_dropin CATCH %d/4 ; H5_lit CATCH %d/4"
      % (sum(x["pure"] for x in rows4), sum(x["drop"] for x in rows4), sum(x["h5"] for x in rows4)))
OUT["c17"] = rows17
OUT["s4"] = rows4
(WD / "_dgaw_extra_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgaw_extra_out.json")
