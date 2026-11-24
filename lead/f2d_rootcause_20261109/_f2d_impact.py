# -*- coding: utf-8 -*-
"""F2-d 调查：L130 对象在盘状态核实 + 影响面（引用计数，只读）"""
import hashlib, json, os, re, subprocess

ROOT = r"D:\Project\ra2-campaign-forge"

def fp(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        return {"path": rel, "status": "NOT_ON_DISK"}
    b = open(p, "rb").read()
    return {"path": rel, "status": "ON_DISK", "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

out = {"anchors": [], "refs": {}}

# 1) L130 对象状态核实
out["anchors"].append(fp("lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md"))      # r2 现盘（被扫件本体）
out["anchors"].append(fp("lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md"))         # F2 报告 §5.3 实测的对照件
out["anchors"].append(fp("lead/b2b_isolated_20261107/qc151_trip.isolated.py"))         # F2/F3 绑定对象
out["anchors"].append(fp("out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"))  # 母本
out["anchors"].append(fp("lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py")) # 正式候选
out["anchors"].append(fp("lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md"))          # 规格草案

# 2) 影响面：5 个被扫文件在 lead/ 下的他件引用计数（文本 grep，只读）
targets = {
    "A_RESIDUAL_REFERENCES.md": "A_RESIDUAL_REFERENCES",
    "INTEGRATION_REPORT.md": "INTEGRATION_REPORT",
    "_integ_INTEGRATION_REPORT.md": "_integ_INTEGRATION_REPORT",
    "B_EXECUTION_SPEC.md": "B_EXECUTION_SPEC",
    "_n4_SPEC_N4_B2B_MATRIX.md": "_n4_SPEC_N4_B2B_MATRIX",
}
lead_dir = os.path.join(ROOT, "lead")
for name, pat in targets.items():
    hits = []
    for dirpath, dirnames, filenames in os.walk(lead_dir):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in filenames:
            if not fn.lower().endswith((".md", ".json", ".txt")):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            try:
                t = open(full, "r", encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            n = t.count(pat)
            if n and rel.split("/")[-1] != name:  # 排除文件自身同名行
                hits.append({"ref_file": rel, "count": n})
    hits.sort(key=lambda x: -x["count"])
    out["refs"][name] = {"self_name": name, "referring_files": len(hits), "top": hits[:12]}

print(json.dumps(out, ensure_ascii=False, indent=1))
