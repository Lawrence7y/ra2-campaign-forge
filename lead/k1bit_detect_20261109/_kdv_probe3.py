# -*- coding: utf-8 -*-
"""_kdv_probe3.py -- one decisive legal all()/k=1 false-positive fixture.

This legal script has k=1 (a single fixed literal tested across SAMPLE bodies)
and an unrelated `ok &= good` accumulator over a single constant check.  It is
semantically LEGAL (no k>=2 homogeneous input OR-collapse, no k->1bit loss),
yet the reported detector's verdict is CONFIRMED_K1BIT because `has_k` is
bypassed by the presence of any BIT_ACCUM site (_kd_detect.py:484-487).
"""
import importlib.util
import json
from pathlib import Path

WD = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("_kd_p3", WD / "_kd_detect.py")
kd = importlib.util.module_from_spec(sp)
sp.loader.exec_module(kd)

SRC = '''
def main():
    cases = ["doc1", "doc2"]
    ok = True
    good = (1 == 1)
    ok &= good
    if not any("FIXED" in case for case in cases):
        print("FAIL")
        return 1
    print("PASS")
    return 0
'''

r = kd.analyse("legal_k1_plus_unrelated_accum", SRC.encode("utf-8"))
out = dict(verdict=r["verdict"], want="LEGAL_AGGREGATE",
           ok=(r["verdict"] == "LEGAL_AGGREGATE"),
           has_k=r["has_k"], onebit_exit=r["onebit_exit"],
           n_real_collapse=r["n_real_collapse"], n_accum=r["n_accum"],
           collapse=[(c["kind"], c["quantifies"], c["k"]) for c in r["collapse"]],
           note="k=1 legal existential over samples; unrelated ok&=good must not "
                "convert has_k=False into CONFIRMED_K1BIT")
(WD / "_kdv_probe3_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
