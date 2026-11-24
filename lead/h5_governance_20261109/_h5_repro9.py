# -*- coding: utf-8 -*-
"""独立复核编排方九条管辖样本：直接 import _v12_rule.classify_v12。"""
import importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
OUT = HERE / "_h5_repro9_out.json"

spec = importlib.util.spec_from_file_location("_v12_rule", str(RULE))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("loaded =", hasattr(m, "classify_v12"))

CASES = [
 {"id":"REGRESS1","text":"本笔已入账 0 命中不得写成未入账","token":"已入账","expect":"应CATCH"},
 {"id":"REGRESS2","text":"审阅不得不承认本候选已生效。","token":"已生效","expect":"应CATCH"},
 {"id":"CTRL_OK","text":"本件已生效，可应用母本","token":"已生效","expect":"应CATCH"},
 {"id":"TRUE_NEG","text":"本节登记不宣告 N-4 正式绑定已生效","token":"已生效","expect":"应PASS"},
 {"id":"TRAIL_NEG","text":"已入账不得重复登记","token":"已入账","expect":"应CATCH"},
 {"id":"LEAD_NEG","text":"不得写成已入账","token":"已入账","expect":"应PASS"},
 {"id":"DOUBLE_1","text":"并非不宣告已生效","token":"已生效","expect":"应CATCH"},
 {"id":"DOUBLE_2","text":"不能不说本笔已入账","token":"已入账","expect":"应CATCH"},
 {"id":"DOUBLE_3","text":"无不认为本件已生效","token":"已生效","expect":"应CATCH"},
]

out = []
for c in CASES:
    s = c["text"].find(c["token"])
    r = m.classify_v12(c["text"], s, s + len(c["token"]), c["token"])
    rec = dict(c)
    rec.update({"verdict": r["verdict"], "hard": r["hard"], "override": r["override"],
                "weak": r["weak"], "review_flag": r["review_flag"], "unit": r["unit"]})
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False))

OUT.write_text(json.dumps({"loaded": True, "cases": out}, ensure_ascii=False, indent=1),
               encoding="utf-8")
print("written:", OUT.name)
