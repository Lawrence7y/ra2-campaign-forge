# -*- coding: utf-8 -*-
"""列出 26 处现盘命中的 U / pre / post，供管辖补丁设计对账。只读既有件。"""
import json, sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SHADOW = ROOT / "lead" / "v12_impact_20261109" / "_vi_shadow_out.json"
OUT = HERE / "_h5_ctx26_out.json"

d = json.loads(SHADOW.read_text(encoding="utf-8"))
rows = []
for dom in d["rows"]:
    for h in dom["hits"]:
        co = h["co"]
        rows.append({
            "domain": dom["domain"], "line": h["line"], "pos": h["pos"],
            "token": h["token"], "r10_kind": h["r10_kind"],
            "v12": h["v12_verdict"], "hard": h["hard"],
            "U": co["U"], "pre": co["pre"], "post": co["post"],
            "adj_neg": co["adj_neg"], "prohibit_U": co["prohibit_U"],
            "override_would_fire": co["override_would_fire"],
            "weak_would_fire": co["weak_would_fire"],
        })
OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
for r in rows:
    if "H5_否定禁止管辖" in r["hard"] or r["adj_neg"] or r["prohibit_U"]:
        print("--- %s L%d pos=%d tok=%s old=%s hard=%r" %
              (r["domain"], r["line"], r["pos"], r["token"], r["v12"], r["hard"]))
        print("  U   =", repr(r["U"][:160]))
        print("  pre =", repr(r["pre"][:160]))
        print("  post=", repr(r["post"][:100]))
        print("  adj_neg=%s prohibit_U=%s override_would_fire=%s weak_would_fire=%s" %
              (r["adj_neg"], r["prohibit_U"], r["override_would_fire"], r["weak_would_fire"]))
print("total hits =", len(rows))
