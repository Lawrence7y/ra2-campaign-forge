# -*- coding: utf-8 -*-
"""_ncv_probe3.py -- 校正探针：真实归档块用 lowered 绝对行号定位 + 误报基线 + 完整性核查。"""
import importlib.util
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
D = os.path.join(ROOT, "lead", "number_channel_20261109")


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(D, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ncl = load("ncl3", "_nc_lint.py")
out = {}


def lowered(path):
    for l in io.open(path, "r", encoding="utf-8").read().split("\n"):
        if l.startswith("export const payload"):
            return json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")


def block_of(path):
    L = lowered(path)
    s = next(i for i, x in enumerate(L) if "const ASK_ANALYST = [" in x)
    e = next(i for i in range(s + 1, len(L)) if "].join" in L[i])
    return s + 1, "\n".join(L[s + 1:e])


for tag, fname, key_lines in (
    ("89df", "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs",
     [107, 108, 110, 113, 122, 124]),
    ("8682", "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs",
     [94, 95, 98, 110, 131, 132, 170]),
):
    first, block = block_of(os.path.join(ROOT, ".zcode", "workflow-runs", fname))
    cls = ncl.classify_lines(block)
    inv = {}
    for k in ("prose", "machine", "quoted", "code"):
        for ln, _ in cls[k]:
            inv[ln] = k
    out[tag] = {
        "first_lowered_line": first,
        "counts": {k: len(v) for k, v in cls.items()},
        "key_lines": {str(a): inv.get(a - first + 1, "NOT_CLASSIFIED") for a in key_lines},
    }

# ---- 误报基线：按设计员 §3.4 口径（唯一可复现的部分）重算 ----
drafts_dir = os.path.join(ROOT, ".zcode", "workflow-drafts")
paths = sorted(p for p in os.listdir(drafts_dir) if p.endswith(".dwf.ts"))
n_drafts = len(paths)
with_ask, prose_line_total, raw_ar, after_code = 0, 0, 0, 0
residuals = []
for p in paths:
    txt = io.open(os.path.join(drafts_dir, p), "r", encoding="utf-8", errors="replace").read()
    m = re.search(r"const\s+ASK_ANALYST\s*=\s*\[(.*?)\n\s*\]\.join", txt, re.S)
    if not m:
        continue
    with_ask += 1
    cls = ncl.classify_lines(m.group(1))
    for _, body in cls["prose"]:
        prose_line_total += 1
        raw_ar += len(ncl.ARABIC.findall(body))
        t = ncl.mask_exempt(body)
        after_code += len(ncl.ARABIC.findall(t))
    r = ncl.lint(m.group(1), [], dir_hint="")
    residuals.append(r["summary"]["n_findings"])
out["census_my_own_classifier"] = {
    "n_drafts": n_drafts, "with_ASK_ANALYST": with_ask,
    "prose_lines": prose_line_total,
    "arabic_raw": raw_ar, "arabic_after_mask_exempt": after_code,
    "n_findings_sum": sum(residuals),
    "note": "口径与 §3.4 不同（我用 classify_lines+mask_exempt，非设计员的独立统计脚本）；仅作方向对照",
}

# ---- .mjs 归档含 CLAIM_NUMBERS 数量 ----
runs = os.path.join(ROOT, ".zcode", "workflow-runs")
mjs = [p for p in os.listdir(runs) if p.startswith("dwfrun-") and p.endswith(".mjs")]
n_claim = sum(1 for p in mjs if "CLAIM_NUMBERS" in io.open(os.path.join(runs, p), "r", encoding="utf-8", errors="replace").read())
out["archive_claim_numbers"] = {"n_mjs": len(mjs), "with_CLAIM_NUMBERS": n_claim}

# ---- §4.1 算术：按「每个字段 10-20 秒」与 17.29 个/份 ----
mean = 17.29
out["effort_check"] = {
    "mean_residual": mean,
    "min_at_10s_per_field": round(mean * 10 * 10 / 60, 2),
    "min_at_20s_per_field": round(mean * 10 * 20 / 60, 2),
    "claimed_minutes_for_migration": "4-8",
    "ratio_low": round((mean * 10 * 10 / 60) / 4, 2),
    "verdict": "若按 §4.1 字面『每字段 10–20 秒 × 约 10 字段』，估算应为 28.8–57.6 分钟；"
               "4–8 分钟只与『每个数字 10–20 秒』相容。§4.1 的估算单位自相矛盾。",
}

print(json.dumps(out, ensure_ascii=False, indent=2))
