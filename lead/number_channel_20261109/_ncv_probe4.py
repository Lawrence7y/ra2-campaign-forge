# -*- coding: utf-8 -*-
"""_ncv_probe4.py -- 定点确认：UNRENDERED 守卫、规则覆盖、census 在盘依据。"""
import hashlib
import importlib.util
import io
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
D = os.path.join(ROOT, "lead", "number_channel_20261109")


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(D, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ncph = load("ncph4", "_nc_placeholder.py")
ncl = load("ncl4", "_nc_lint.py")
claims = ncph._demo_claims()
src = {"block_sha256": hashlib.sha256(ncph.canonical_bytes(claims)).hexdigest(),
       "version": 1, "claims": claims}
hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(claims))
out = {}

# ---- 1. UNRENDERED 守卫：无 header / 有 header ----
m_only = '"【复核数据】" + vfText,'
p_only = '"【背景】{{N.ratio_32768}}。"'
v = ncph.validate_claim_numbers(claims, strict=False)
out["guard"] = {
    "bare_diff_problems": ncph.cross_section_diff(m_only, p_only, v)["problems"],
    "diff_with_binding_line_in_machine": ncph.cross_section_diff(
        m_only + "\n" + hdr.split("\n")[1], p_only, v)["problems"],
}
r_no = ncl.lint(m_only + "\n" + p_only + "\n", claims, source=None)
r_yes = ncl.lint(hdr + "\n" + m_only + "\n" + p_only + "\n", claims, source=src)
out["guard"]["lint_without_header"] = r_no["findings"]
out["guard"]["lint_with_mandatory_header"] = {
    "ok": r_yes["ok"],
    "findings": r_yes["findings"],
    "machine_lines_classified": [x[1][:110] for x in ncl.classify_lines(
        hdr + "\n" + m_only + "\n" + p_only + "\n")["machine"]],
}
out["guard"]["UNRENDERED_in_RULES"] = "UNRENDERED_MACHINE_SEGMENT" in ncl.RULES
out["guard"]["lint_maps_all_diff_problems_to"] = "CROSS_SECTION_VALUE_NOT_USED (见 _nc_lint.py:250-252)"

# ---- 2. selftest 实际覆盖的规则 ----
sf = json.load(io.open(os.path.join(D, "_nc_lint_selftest_out.json"), "r", encoding="utf-8"))
hit = set()
for row in sf["rows"]:
    for f in row.get("findings", []):
        hit.add(f["rule"])
    for r in row.get("rules_hit", []):
        if ":" not in r:
            hit.add(r)
declared = set(ncl.RULES) | {"UNRENDERED_MACHINE_SEGMENT", "ESTIMATE_IN_ACCEPTANCE"}
out["selftest_coverage"] = {
    "n_pass": sf["n_pass"], "n": sf["n"],
    "rules_exercised_by_selftest": sorted(hit),
    "declared_rules_declared_in_md": ["BARE_ARABIC", "BARE_CJK_NUMERAL", "AMBIGUOUS_SCOPE",
                                     "CROSS_DOMAIN_LEAK", "DESIGN_EXPERIMENT_UNMARKED",
                                     "DESIGN_EXPERIMENT_IN_ACCEPTANCE", "ESTIMATE_NOT_DEGRADED",
                                     "ESTIMATE_IN_ACCEPTANCE", "UNRESOLVED_PLACEHOLDER",
                                     "NONCONFORMING_MUSTACHE", "BAD_SOURCE_KIND",
                                     "MISSING_FIELDS", "BAD_SHA256", "DANGLING_DEP",
                                     "STALE_NUMBER_SOURCE", "STALE_VERSION",
                                     "CROSS_SECTION_VALUE_NOT_USED", "UNRENDERED_MACHINE_SEGMENT"],
    "not_exercised": sorted(declared - hit),
}

# ---- 3. §3.4 census 数字在盘依据 ----
needles = ["213", "3200", "2354", "2014", "1694", "17.29", "534", "14.44"]
found = {}
for n in needles:
    files = []
    for p in sorted(os.listdir(D)):
        fp = os.path.join(D, p)
        if not os.path.isfile(fp) or p.endswith(".pyc"):
            continue
        try:
            t = io.open(fp, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if n in t:
            files.append(p)
    found[n] = files
out["census_artifacts"] = {
    "files_in_write_domain": sorted(p for p in os.listdir(D) if os.path.isfile(os.path.join(D, p))),
    "needle_to_files": found,
    "census_script_on_disk": any("census" in p for p in os.listdir(D)),
}

# ---- 4. 归档/草稿计数（此时点） ----
runs = os.path.join(ROOT, ".zcode", "workflow-runs")
drafts = os.path.join(ROOT, ".zcode", "workflow-drafts")
mjs = [p for p in os.listdir(runs) if p.startswith("dwfrun-") and p.endswith(".mjs")]
dwf = [p for p in os.listdir(drafts) if p.endswith(".dwf.ts")]
with_cn = [p for p in mjs if "CLAIM_NUMBERS" in io.open(os.path.join(runs, p), "r", encoding="utf-8", errors="replace").read()]
out["counts_now"] = {"n_mjs": len(mjs), "n_dwf_ts": len(dwf),
                     "mjs_with_CLAIM_NUMBERS": with_cn,
                     "note": "设计件报 256 / 213；此时点为上述值（目录可能被并行会话追加）"}

print(json.dumps(out, ensure_ascii=False, indent=2))
