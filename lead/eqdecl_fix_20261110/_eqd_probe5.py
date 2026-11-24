# -*- coding: utf-8 -*-
"""_eqd_probe5.py — 撰写员独立复跑：五行 FAIL 锚点 修复前 vs 修复后 现场判定。
只读两份检测器与被检文档；输出仅到终端。python -I -X utf8 _eqd_probe5.py
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
HERE = ROOT / "lead/eqdecl_fix_20261110"


def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


eqb = load(ROOT / "lead/eqdecl_gate_20261109/_eq_detector.py", "eq_before")
eqa = load(HERE / "_ef_detector.py", "eq_after")

PROBE = [
    ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", 158),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 13),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 223),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 242),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 338),
]
K8_CTRL = ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 339)
K9_CTRL = ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 294)


def find(eq, rel, line):
    rec = eq.scan_file(ROOT / rel)
    for b in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
        for r in rec[b]:
            if r["line"] == line:
                return r
    return None


for rel, line in PROBE + [K8_CTRL, K9_CTRL]:
    rb = find(eqb, rel, line)
    ra = find(eqa, rel, line)
    name = rel.split("/")[-1] + ":" + str(line)
    fb = rb["flags"]
    fa = ra["flags"]
    print(name)
    print("  BEFORE:", rb["verdict"], "/", rb["failure_type"], "/", rb["category"],
          "skip=", rb.get("skip_reason"),
          "E_eq=%s R_same=%s I=%s O=%s" % (fb.get("E_eq"), fb.get("R_same_line"),
                                           fb.get("I"), fb.get("O")))
    print("  AFTER :", ra["verdict"], "/", ra["failure_type"], "/", ra["category"],
          "skip=", ra.get("skip_reason"),
          "E_eq=%s E_eq_window=%s R_same=%s I=%s" % (fa.get("E_eq"), fa.get("E_eq_window"),
                                                     fa.get("R_same_line"), fa.get("I")))
