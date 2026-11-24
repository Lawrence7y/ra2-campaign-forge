# -*- coding: utf-8 -*-
"""_ncv_probe.py -- 独立压力测试 _nc_placeholder.py / _nc_lint.py。

只读加载两个模块；所有输入为只读件或内存构造；不写任何既有件。
覆盖：
  1. 真实归档 ASK_ANALYST 块的 classify_lines 结果（散文/机器/引述）
  2. 「段落判定靠结构」的可绕过性（标题洗白 / 【复核】 / publishArtifact）
  3. per-claim sha256 / stdout_sha256 / line_sha256 是否真的绑定
  4. 受控词表与必填字段是否与规格一致
  5. cross_section_diff 三例 + 未知 mustache 不回显
  6. §4.1 估算的内部算术一致性
"""
import hashlib
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


ncph = load("ncph_probe", "_nc_placeholder.py")
ncl = load("ncl_probe", "_nc_lint.py")

TB89 = os.path.join(ROOT, ".zcode", "workflow-runs",
                    "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs")
TB86 = os.path.join(ROOT, ".zcode", "workflow-runs",
                    "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs")


def lowered(path):
    for l in io.open(path, "r", encoding="utf-8").read().split("\n"):
        if l.startswith("export const payload"):
            return json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")
    raise RuntimeError("no payload")


def ask_block(path):
    L = lowered(path)
    start = next(i for i, s in enumerate(L) if "const ASK_ANALYST = [" in s)
    end = next(i for i in range(start + 1, len(L)) if "].join" in L[i])
    return start + 1, L[start + 1:end], L


out = {}

# ---- 1. 真实归档的段落分类 ----
for tag, path, key_lines in (("89df", TB89, [107, 108, 110, 113, 122, 124]),
                             ("8682", TB86, [94, 95, 98, 110, 131, 132, 170])):
    lineno0, block, L = ask_block(path)
    cls = ncl.classify_lines("\n".join(block))
    inv = {}
    for kind in ("prose", "machine", "quoted", "code"):
        for ln, _ in cls[kind]:
            inv[ln] = kind
    rows = []
    for abs_ln in key_lines:
        rel = abs_ln - lineno0
        rows.append({"lowered_line": abs_ln,
                     "class": inv.get(rel, "NOT_CLASSIFIED"),
                     "text": L[abs_ln - 1].strip()[:150]})
    out["classify_" + tag] = {
        "ask_block_first_lowered_line": lineno0,
        "n_block_lines": len(block),
        "counts": {k: len(v) for k, v in cls.items()},
        "key_lines": rows,
    }

# ---- 2. 规则可绕过性探针 ----
claims = ncph._demo_claims()
src = {"block_sha256": hashlib.sha256(ncph.canonical_bytes(claims)).hexdigest(),
       "version": 1, "claims": claims}
hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(claims))

probes = {
    "P1_title_launder": hdr + '\n  "【编排方实跑指纹】实测 13 个域仍有门禁问题。",\n',
    "P2_review_segment": hdr + '\n  "【复核】{{N.est_effort}} 必须达成。",\n',
    "P3_publishArtifact": hdr + '\n  await __host.publishArtifact("a", "file", ["x", {description: "{{N.est_effort}} 个域"}]);\n',
    "P4_delivery_string": hdr + '\n  "【交付】{{N.est_effort}} 必须达成。",\n',
    "P5_plain_prose_bare": hdr + '\n  "【背景】实测 13 个域。",\n',
}
out["bypass_probes"] = {}
for name, block in probes.items():
    cls = ncl.classify_lines(block)
    r = ncl.lint(block, claims, source=src)
    out["bypass_probes"][name] = {
        "classes": {k: [x[0] for x in v] for k, v in cls.items()},
        "ok": r["ok"],
        "rules_hit": sorted({f["rule"] for f in r["findings"]}),
    }

# ---- 3. 校验器绑定性探针 ----
def clone(cid):
    return dict(next(c for c in claims if c["id"] == cid))

vp = {}
c = clone("domains_nonempty")
c["value"] = 999
vp["V1_change_value_keep_sha256"] = ncph.validate_claim_numbers([c], strict=False)["ok"]
c = clone("domains_nonempty")
c["stdout_sha256"] = "x"
vp["V2_stdout_sha256_not_hex"] = ncph.validate_claim_numbers([c], strict=False)["ok"]
c = clone("domains_nonempty")
c["command"] = "echo fake"
vp["V3_command_not_rerun"] = ncph.validate_claim_numbers([c], strict=False)["ok"]
# 文件行：缺 line_sha256
fc = {"id": "file_claim", "value": 13, "unit": "域",
      "scope": {"label": "全量载体", "numerator": "n", "denominator": "d", "condition": "c"},
      "source_kind": "文件行", "source_ref": "demo", "sha256": "a" * 64,
      "path": "lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md", "line": 51,
      "domain": "gate_rejudge32", "artifact": "GATE_REJUDGE_32.md"}
vp["V4_fileline_no_line_sha256_false_strict"] = ncph.validate_claim_numbers([fc], strict=False)["ok"]
fc2 = dict(fc)
fc2["path"] = "no/such/file.md"
vp["V5_fileline_bogus_path_strict"] = ncph.validate_claim_numbers([fc2], strict=True)["ok"]
# 实读该行但值不在行内（GATE_REJUDGE_32.md:51 含 13 域；改 value 为 999）
fc3 = dict(fc)
fc3["path"] = os.path.join(ROOT, "lead", "gate_rejudge32_20261109", "GATE_REJUDGE_32.md")
fc3["line"] = 51
fc3["line_sha256"] = hashlib.sha256(
    io.open(fc3["path"], encoding="utf-8").read().split("\n")[50].encode("utf-8")).hexdigest()
fc3["value"] = 999
r3 = ncph.validate_claim_numbers([fc3], strict=True)
vp["V6_fileline_value_not_in_line_strict"] = {"ok": r3["ok"], "problems": r3["problems"]}
# 估算缺 source_ref（§2.1 表称所有必填）
ec = clone("est_effort")
ec.pop("source_ref", None)
vp["V7_estimate_no_source_ref"] = ncph.validate_claim_numbers([ec], strict=False)["ok"]
# kind 词表外
xc = clone("domains_nonempty")
xc["source_kind"] = "拍脑袋"
vp["V8_bad_kind"] = ncph.validate_claim_numbers([xc], strict=False)["problems"]
out["validator_probes"] = vp
out["required_table"] = {k: list(v) for k, v in ncph.REQUIRED.items()}
out["scope_label_count"] = len(ncph.SCOPE_LABELS)
out["rules_missing_UNRENDERED"] = "UNRENDERED_MACHINE_SEGMENT" not in ncl.RULES

# ---- 4. cross_section_diff + 未知 mustache ----
v = ncph.validate_claim_numbers(claims, strict=False)
wrong = ncph.cross_section_diff("【复核数据】32768 0.14013134", "【背景】什么都没引用", v)
right = ncph.cross_section_diff("【复核数据】32768", "【背景】{{N.ratio_32768}}", v)
static = ncph.cross_section_diff('"【复核数据】" + vfText', "【背景】{{N.ratio_32768}}", v)
rr = ncph.render("【背景】" + "{{PROBE_TOKEN}}" + " 与 {{N.no_such_id}}", v["by_id"])
out["diff_and_mustache"] = {
    "WRONG": wrong["problems"], "RIGHT": right["problems"], "STATIC": static["problems"],
    "render_problems": rr["problems"],
    "echoes_probe_token": "PROBE_TOKEN" in json.dumps(rr, ensure_ascii=False),
}
# lint 对 STATIC 的规则码
r_static = ncl.lint(hdr + '\n  "【复核数据】" + vfText,\n  "【背景】{{N.ratio_32768}}。",\n',
                    claims, source=src)
out["diff_and_mustache"]["lint_static_rules"] = sorted({f["rule"] for f in r_static["findings"]})

# ---- 5. §4.1 估算内部算术 ----
mean_numbers = 17.29
fields_per = 10
out["effort_arith"] = {
    "mean_residual_numbers": mean_numbers,
    "fields_per_claim_assumed": fields_per,
    "at_10s_per_field_min": round(mean_numbers * fields_per * 10 / 60, 1),
    "at_20s_per_field_min": round(mean_numbers * fields_per * 20 / 60, 1),
    "at_10s_per_claim_min": round(mean_numbers * 10 / 60, 1),
    "at_20s_per_claim_min": round(mean_numbers * 20 / 60, 1),
    "design_claim_minutes": "4-8",
    "consistent_if_per_field": False,
    "consistent_if_per_claim": True,
}

print(json.dumps(out, ensure_ascii=False, indent=2))
