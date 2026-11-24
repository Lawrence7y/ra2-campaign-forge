# -*- coding: utf-8 -*-
"""_dt_triage.py -- per-piece 4-level classification of the 40 CONFIRMED pieces.

Read-only over protected dirs; writes only into lead/detect_triage_20261109/.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
repro = json.loads((WD / "_dt_repro_out.json").read_text(encoding="utf-8"))
scope = json.loads((WD / "_dt_scope_out.json").read_text(encoding="utf-8"))
kd = json.loads((ROOT / "lead/k1bit_detect_20261109/_kd_detect_out.json")
                .read_text(encoding="utf-8"))

PROD = {
    "lead/d27_ruling_20261106/check_d27.py": ("D-27", "PENDING_DECISIONS.md:129"),
    "lead/d28_ruling_20261106/check_d28.py": ("D-28", "PENDING_DECISIONS.md:117"),
    "lead/d29_ruling_20261106/check_d29.py": ("D-29", "PENDING_DECISIONS.md:105"),
    "lead/d30_ruling_20261106/check_d30.py": ("D-30", "PENDING_DECISIONS.md:92"),
}
# hashes registered in the stale-pass inventory / census (independent upstream)
REGISTERED = {
    "lead/d27_ruling_20261106/check_d27.py": "3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c",
    "lead/d28_ruling_20261106/check_d28.py": "5b42a34a40046d7a",  # 16-hex prefix in _cf_census.py:37
    "lead/d29_ruling_20261106/check_d29.py": "2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14",
    "lead/d30_ruling_20261106/check_d30.py": "6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd",
}

rows = []
for x in repro["confirmed_rows"]:
    rel = x["rel"]
    if rel in PROD:
        grp = "生产件"
        level = "A"
        ruling, ledger_line = PROD[rel]
        note = "生产门禁；台账已裁决记录行；PASS 已被引用"
    else:
        grp = ("沙箱 _cm_tmp" if "/_cm_tmp/" in rel else
               "沙箱 _cmv_tmp" if "/_cmv_tmp/" in rel else
               "沙箱 _sp_sandbox" if "/_sp_sandbox/" in rel else "OTHER")
        level = "D"
        ruling, ledger_line = "", ""
        note = "沙箱/审计副本；两台账 0 行引用（_dt_scope_out.json:sandbox_in_ledgers）"
    rows.append(dict(rel=rel, sha256=x["sha256"], bytes=x["bytes"],
                     group=grp, level=level, ruling=ruling,
                     ledger_line=ledger_line, note=note,
                     has_k=x["has_k"], attribution=x["attribution"],
                     collapse=x["collapse"]))

counts = {}
for lv in "ABCD":
    counts[lv] = sum(1 for r in rows if r["level"] == lv)
group_counts = {}
for r in rows:
    group_counts[r["group"]] = group_counts.get(r["group"], 0) + 1

prod_check = []
for rel, (ruling, line) in PROD.items():
    r = next(x for x in rows if x["rel"] == rel)
    reg = REGISTERED[rel]
    ok = (r["sha256"] == reg) if len(reg) == 64 else r["sha256"].startswith(reg)
    prod_check.append(dict(rel=rel, sha256=r["sha256"], bytes=r["bytes"],
                           registered=reg, match=ok, ruling=ruling,
                           ledger_line=line))

# binding lines for the re-verified artifacts
artifacts = [
    "lead/k1bit_detect_20261109/_kd_detect_out.json",
    "lead/k1bit_detect_20261109/K1BIT_DETECTOR.md",
    "lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json",
    "lead/check_family_20261109/_cf_detect_out.json",
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
binding = []
for p in artifacts:
    b = (ROOT / p).read_bytes()
    binding.append(dict(rel=p, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b)))
for r in rows:
    if r["level"] == "A":
        binding.append(dict(rel=r["rel"], sha256=r["sha256"], bytes=r["bytes"]))

out = dict(n=len(rows), counts=counts, group_counts=group_counts,
           rows=rows, prod_check=prod_check, binding=binding,
           suspect6=repro["suspect_rows"],
           cf_suspect=scope["suspect_compare"]["cf_suspect"],
           carrier_one=scope["carrier_one"])
(WD / "_dt_triage_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("counts", counts)
print("group_counts", group_counts)
print("=== A-level production gates ===")
for r in prod_check:
    print(" ", r["rel"], r["sha256"], r["bytes"], "match_registered=", r["match"],
          r["ruling"], r["ledger_line"])
print("=== D-level by group ===")
for g, n in sorted(group_counts.items()):
    if g != "生产件":
        print(" ", g, n)
print("=== binding lines ===")
for b in binding:
    print("被核对象 SHA256 = %s，字节数 = %d" % (b["sha256"], b["bytes"]))
print("WROTE", (WD / "_dt_triage_out.json").as_posix())
