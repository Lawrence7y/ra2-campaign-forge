# -*- coding: utf-8 -*-
"""_dtx_check.py -- this-session independent verification for DETECT_TRIAGE.md.

Read-only over all protected dirs; writes only _dtx_check_out.json in the
write domain.  No gates are executed, no dynamic injection, no real game,
no sampling code.  Bytecode writing disabled.
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


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kd = load("_dtx_kd", KD / "_kd_detect.py")

# (1) exact fixture from _kdv_probe3.py:19-30
p3 = (KD / "_kdv_probe3.py").read_text(encoding="utf-8")
i = p3.index("SRC = '''") + len("SRC = '''")
j = p3.index("'''", i)
fp = kd.analyse("legal_k1_plus_unrelated_accum", p3[i:j].encode("utf-8"))

# (2) exact V7 / V8 fixtures from _kdv_semantic_probe.py
sp = (KD / "_kdv_semantic_probe.py").read_text(encoding="utf-8")


def fixture(name):
    a = sp.index('add("%s"' % name)
    b = sp.index("'''", a) + 3
    c = sp.index("'''", b)
    return sp[b:c]


v7 = kd.analyse("V7_true_collapse_renamed", fixture("V7_true_collapse_renamed").encode("utf-8"))
v8 = kd.analyse("V8_true_collapse_no_any_keyword", fixture("V8_true_collapse_no_any_keyword").encode("utf-8"))

# (3) out-of-census candidates, --one style re-run
cands = [
    "lead/refsync_scope_20261109/_rs_carrier_scan.py",
    "out/re_work/work_chain/CONTINUE_20261003/lead/decide_all/scripts/selfgate.py",
]
probes = []
for rel in cands:
    p = ROOT / rel
    b = p.read_bytes()
    r = kd.analyse(rel, b)
    probes.append(dict(rel=rel, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b),
                       verdict=r["verdict"], has_k=r["has_k"],
                       attribution=r["attribution"],
                       collapse=[c["kind"] for c in r["collapse"]]))

# (4) 173-row frozen counts, 40-row per-piece table, binding-line format
frozen = json.loads((KD / "_kd_detect_out.json").read_text(encoding="utf-8"))
triage = json.loads((WD / "_dt_triage_out.json").read_text(encoding="utf-8"))
report = (WD / "_dt_REPORT.md").read_text(encoding="utf-8")
import re
bl = re.findall(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$", report, re.M)
strict = all(re.fullmatch(r"被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+", x)
             for x in re.findall(r"^被核对象 SHA256 = .*$", report, re.M))
table = (WD / "_dt_table.md").read_text(encoding="utf-8").splitlines()
table_rows = [x for x in table if re.match(r"^\| \d+ \|", x)]

upstream = [
    "lead/k1bit_detect_20261109/_kd_detect_out.json",
    "lead/k1bit_detect_20261109/K1BIT_DETECTOR.md",
    "lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json",
    "lead/check_family_20261109/_cf_detect_out.json",
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
hashes = []
for rel in upstream:
    b = (ROOT / rel).read_bytes()
    hashes.append(dict(rel=rel, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b)))

out = dict(
    probe3=dict(verdict=fp["verdict"], want="LEGAL_AGGREGATE", has_k=fp["has_k"],
                n_accum=fp["n_accum"], false_positive=(fp["verdict"] == "CONFIRMED_K1BIT")),
    V7=dict(verdict=v7["verdict"], want="CONFIRMED_K1BIT", has_k=v7["has_k"],
            false_negative=(v7["verdict"] != "CONFIRMED_K1BIT")),
    V8=dict(verdict=v8["verdict"], want="CONFIRMED_K1BIT", has_k=v8["has_k"],
            false_negative=(v8["verdict"] != "CONFIRMED_K1BIT")),
    probes=probes,
    frozen_counts=frozen["counts"],
    triage_counts=triage["counts"], triage_groups=triage["group_counts"],
    n_triage_rows=len(triage["rows"]), n_table_rows=len(table_rows),
    n_binding_lines=len(bl), binding_strict=strict,
    binding_first7_equal_my_hashes=([x[0] for x in bl[:7]] == [h["sha256"] for h in hashes]),
    hashes=hashes,
)
(WD / "_dtx_check_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
