# -*- coding: utf-8 -*-
"""_dtv_fixtures.py -- independent re-run of the reply's FP/FN fixtures.

Read-only over protected dirs; writes only _dtv_fixtures_out.json in the write
domain.  Bytecode writing disabled.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD = ROOT / "lead/k1bit_detect_20261109"

spec = importlib.util.spec_from_file_location("_dtv_kd_fix", KD / "_kd_detect.py")
kd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd)

# exact fixture from _kdv_probe3.py:19-30 (verbatim, copied by reading the file)
p3 = (KD / "_kdv_probe3.py").read_text(encoding="utf-8")
start = p3.index("SRC = '''") + len("SRC = '''")
end = p3.index("'''", start)
SRC3 = p3[start:end]
fp = kd.analyse("legal_k1_plus_unrelated_accum", SRC3.encode("utf-8"))

# exact V7/V8 fixtures from _kdv_semantic_probe.py:101-123
sp = (KD / "_kdv_semantic_probe.py").read_text(encoding="utf-8")


def fixture(name):
    i = sp.index('add("%s"' % name)
    j = sp.index("'''", i) + 3
    k = sp.index("'''", j)
    return sp[j:k]


V7 = fixture("V7_true_collapse_renamed")
V8 = fixture("V8_true_collapse_no_any_keyword")
v7 = kd.analyse("V7_true_collapse_renamed", V7.encode("utf-8"))
v8 = kd.analyse("V8_true_collapse_no_any_keyword", V8.encode("utf-8"))

# independent --one re-run of the out-of-census carrier
carrier = ROOT / "lead/refsync_scope_20261109/_rs_carrier_scan.py"
cr = kd.analyse(carrier.relative_to(ROOT).as_posix(), carrier.read_bytes())

out = dict(
    probe3=dict(source="_kdv_probe3.py:19-30",
                verdict=fp["verdict"], want="LEGAL_AGGREGATE",
                false_positive=(fp["verdict"] == "CONFIRMED_K1BIT"),
                has_k=fp["has_k"], n_accum=fp["n_accum"],
                n_real_collapse=fp["n_real_collapse"],
                onebit_exit=fp["onebit_exit"]),
    V7=dict(source="_kdv_semantic_probe.py:101-111",
            verdict=v7["verdict"], want="CONFIRMED_K1BIT",
            false_negative=(v7["verdict"] != "CONFIRMED_K1BIT"),
            has_k=v7["has_k"], n_real_collapse=v7["n_real_collapse"]),
    V8=dict(source="_kdv_semantic_probe.py:113-123",
            verdict=v8["verdict"], want="CONFIRMED_K1BIT",
            false_negative=(v8["verdict"] != "CONFIRMED_K1BIT"),
            has_k=v8["has_k"], n_real_collapse=v8["n_real_collapse"]),
    carrier=dict(rel=cr["rel"], sha256=cr["sha256"], bytes=cr["bytes"],
                 verdict=cr["verdict"], has_k=cr["has_k"],
                 attribution=cr["attribution"],
                 collapse=[c["kind"] for c in cr["collapse"]]),
)
(WD / "_dtv_fixtures_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
print("WROTE", (WD / "_dtv_fixtures_out.json").as_posix())
