# -*- coding: utf-8 -*-
"""_f2w_extract.py — 交付报告用：从 _f2_repro_out.json + _f2_compare_out.json
提取 19 条绑定行逐条表（行号/原 path/新 path/tier/match/现盘重算值/verified_path）。
只读；输出到 stdout。零真机、零采样。"""
import json
from pathlib import Path

D = Path(r"D:\Project\ra2-campaign-forge\lead\r11_f2_fix_20261109")
REPO = "D:\\Project\\ra2-campaign-forge\\"
LEAD = REPO + "lead\\"

repro = json.loads((D / "_f2_repro_out.json").read_text(encoding="utf-8"))
cmp_ = json.loads((D / "_f2_compare_out.json").read_text(encoding="utf-8"))

rows = repro["rows"]
plus_bindings = []
for r in cmp_["results"]:
    plus_bindings.extend(r["plus"]["bindings"])
orig_bindings = []
for r in cmp_["results"]:
    orig_bindings.extend(r["orig"]["bindings"])

print("rows=%d plus_bindings=%d orig_bindings=%d" % (len(rows), len(plus_bindings), len(orig_bindings)))
for i, (row, ob, pb) in enumerate(zip(rows, orig_bindings, plus_bindings), 1):
    short = row["file"].replace(LEAD, "lead/").replace("\\", "/")
    vp = pb.get("verified_path", "") or ""
    vp = vp.replace(REPO, "").replace("\\", "/")
    rc = pb.get("recomputed", "") or ""
    print("%2d| %s L%-4d %s | orig_path=%r orig_match=%r | plus_path=%r tier=%s match=%s cite=%s | recomputed=%s bytes=%s | verified=%s" % (
        i, short, row["line_no"], row["declared"][:12],
        ob["path"], ob["match"], pb.get("path"), pb.get("tier"),
        pb.get("match"), pb.get("citation"),
        (rc[:16] + "...") if rc else "-", pb.get("bytes", "-"), vp))
