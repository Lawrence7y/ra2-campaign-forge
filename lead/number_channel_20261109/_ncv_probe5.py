# -*- coding: utf-8 -*-
"""_ncv_probe5.py -- 核 §4.3「若只做一件事」方案 A 是否真拦得住 8682 的实际损害行。"""
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


ncph = load("ncph5", "_nc_placeholder.py")
ncl = load("ncl5", "_nc_lint.py")
claims = ncph._demo_claims()
src = {"block_sha256": hashlib.sha256(ncph.canonical_bytes(claims)).hexdigest(),
       "version": 1, "claims": claims}
hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(claims))

TB86 = os.path.join(ROOT, ".zcode", "workflow-runs",
                    "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs")
for l in io.open(TB86, "r", encoding="utf-8").read().split("\n"):
    if l.startswith("export const payload"):
        L = json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")
        break

out = {}
# 用真实损害行构造单份任务书（散文行按 lint 要求的字符串字面量形态）
real_lines = {
    "lowered_98_background": L[97].strip(),
    "lowered_110_task": L[109].strip(),
    "lowered_170_delivery": L[169].strip(),
    "lowered_217_publishArtifact": L[216].strip(),
    "lowered_226_conclusion": L[225].strip(),
}
out["real_lines_used"] = {k: v[:170] for k, v in real_lines.items()}

for k, line in real_lines.items():
    block = hdr + "\n" + line + "\n"
    cls = ncl.classify_lines(block)
    r = ncl.lint(block, claims, source=src)
    out["lint_" + k] = {
        "classes": {kk: [x[0] for x in vv] for kk, vv in cls.items()},
        "ok": r["ok"],
        "rules_hit": sorted({f["rule"] for f in r["findings"]}),
        "A_catches": "ESTIMATE_IN_ACCEPTANCE" in {f["rule"] for f in r["findings"]},
    }

# 关键反证：把错值标成「实跑」而非「估算」，方案 A 就完全失效
mislabeled = {
    "id": "domains_nonempty_wrong", "value": 10, "unit": "域",
    "scope": {"label": "全量载体", "numerator": "n", "denominator": "d", "condition": "c"},
    "source_kind": "实跑", "source_ref": "orchestrator memory",
    "sha256": "a" * 64, "command": "echo 10", "stdout_sha256": "b" * 64,
    "domain": "gate_rejudge32", "artifact": "GATE_REJUDGE_32.md",
}
m_claims = list(claims) + [mislabeled]
m_src = {"block_sha256": hashlib.sha256(ncph.canonical_bytes(m_claims)).hexdigest(),
         "version": 1, "claims": m_claims}
m_hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(m_claims))
block = m_hdr + '\n  "【交付】对 {{N.domains_nonempty_wrong}} 个域逐个判真伪。"\n'
r = ncl.lint(block, m_claims, source=m_src)
out["A_defeat_by_mislabeling_as_实跑"] = {
    "ok": r["ok"], "rules_hit": sorted({f["rule"] for f in r["findings"]}),
    "note": "错值 10 只要标 source_kind=实跑（编排方自己填），ESTIMATE_IN_ACCEPTANCE 不触发；"
            "source_kind 由撰写人自报，无外部证据校验 -> 靠自觉",
}

print(json.dumps(out, ensure_ascii=False, indent=2))
