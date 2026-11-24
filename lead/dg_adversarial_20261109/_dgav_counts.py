# -*- coding: utf-8 -*-
r"""_dgav_counts.py — precise AST/regex branch counts + co_names 8-guard check."""
import sys, ast, json, importlib.util, re
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgav3_dg", DG_DIR / "_dg_core.py")
H5 = _load("_dgav3_h5", ROOT / "lead/h5_governance_20261109/_h5_pasteable.py")
G7 = _load("_dgav3_g7", ROOT / "lead/gate_fp7_20261108/_g7_predicates.py")
ONE = _load("_dgav3_one", ROOT / "lead/gate_fp7_20261108/_g7_predicates.py")
ONE.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
OUT = {}

print("=== (1) H5_DN_EXTRA 顶层选择支：sre_parse 精确计数 ===")
import sre_parse
branches = list(sre_parse.parse(H5.H5_DN_EXTRA))
print("  sre_parse 顶层支数 =", len(branches))
for i, (op, av) in enumerate(branches, 1):
    lit = "".join(chr(x[1]) if x[0] == sre_parse.LITERAL else "?" for x in av
                  if isinstance(av, list)) if isinstance(av, list) else ""
    print("   %2d %s" % (i, str(op) + " " + lit[:60]))
print("  H5_DN_EXTRA 源码 =", H5.H5_DN_EXTRA)
print("  顶层含 sre_parse.BRANCH =", sum(1 for op, av in branches if op == sre_parse.BRANCH))
print("  H5_R12_TEN 顶层支数 =", len(list(sre_parse.parse(H5.H5_R12_TEN))))
print("  合计字面/通配支 =", len(branches) + len(list(sre_parse.parse(H5.H5_R12_TEN))),
      "; 纯字面支 =", len(branches) + len(list(sre_parse.parse(H5.H5_R12_TEN))) - 1)
OUT["h5_branches"] = {"extra": len(branches), "ten": len(list(sre_parse.parse(H5.H5_R12_TEN))),
                      "total": len(branches) + len(list(sre_parse.parse(H5.H5_R12_TEN)))}

print("\n=== (2) co_names 8 个 guard（与 _dga_delivery_probe.py:55 同表）===")
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE", "dg_scan"]
co = {}
for fn in ("r10_context", "r12_scan"):
    names = getattr(ONE, fn).__code__.co_names
    co[fn] = {g: g in names for g in guards}
    print("  %-12s 全 False = %s ; 明细 = %s" % (fn, all(not v for v in co[fn].values()), co[fn]))
OUT["co_names8"] = co

print("\n=== (3) DG 闭合表口径：AST 顶层 tuple 逐项 ===")
tree = ast.parse((DG_DIR / "_dg_core.py").read_text(encoding="utf-8"))
tables = []
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple):
        for t in node.targets:
            if isinstance(t, ast.Name):
                try:
                    n = len(ast.literal_eval(node.value))
                    tables.append((t.id, n, node.lineno))
                except Exception:
                    pass
for name, n, ln in tables:
    print("  %-14s n=%-3d :%d" % (name, n, ln))
core_tables = [x for x in tables if x[0] not in ("R12_TEN",)]
print("  → 参与生成式的闭合表 =", len(core_tables), [x[0] for x in core_tables])
print("  → 加 R12_TEN 对账锚 =", len(tables), "张（DNEG_GENERATIVE.md:163 记 6 张）")
OUT["tables"] = tables

print("\n=== (4) 19 式/十式口径：各自是否互不包含 ===")
gaps = ["亦非不", "未尝不", "未始不", "未有不", "莫不", "不敢不", "不会不", "不可能不",
        "未必不", "未免不", "岂能不", "焉能不", "哪能不", "不可谓不", "不为不",
        "并非没有", "并非毫无", "不是没有", "并不否认"]
ten = list(DG.R12_TEN)
print("  19 式 n =", len(gaps), "; 十式 n =", len(ten),
      "; 交集 =", sorted(set(gaps) & set(ten)))
print("  H5_DN_EXTRA 含 19 式字面 =", sum(1 for g in gaps if g in H5.H5_DN_EXTRA), "/19",
      "; 不含 =", [g for g in gaps if g not in H5.H5_DN_EXTRA])
OUT["gaps_ten"] = {"gaps": len(gaps), "ten": len(ten), "overlap": sorted(set(gaps) & set(ten))}

(WD / "_dgav_counts_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgav_counts_out.json")
