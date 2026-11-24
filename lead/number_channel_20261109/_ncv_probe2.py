# -*- coding: utf-8 -*-
"""_ncv_probe2.py -- 对 §3.3 段落判定 / §2.3 估算禁入 / §2.4 未知 token 的定点复核。

只读输入，输出 stdout。
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


ncph = load("ncph2", "_nc_placeholder.py")
ncl = load("ncl2", "_nc_lint.py")

claims = ncph._demo_claims()
src = {"block_sha256": hashlib.sha256(ncph.canonical_bytes(claims)).hexdigest(),
       "version": 1, "claims": claims}
hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(claims))
out = {}

# ---- A. 标题洗白：未登记数字 + 机器段标题 ----
cases = {
    "A1_unregistered_number_under_machine_title":
        hdr + '\n  "【编排方实跑指纹】实测 7 个域、3 处问题。",\n',
    "A2_registered_number_under_machine_title":
        hdr + '\n  "【编排方实跑指纹】实测 13 个域。",\n',
    "A3_review_segment_estimate":
        hdr + '\n  "【复核】{{N.est_effort}} 必须达成。",\n',
    "A4_task_segment_estimate":
        hdr + '\n  "【任务】{{N.est_effort}} 必须达成。",\n',
    "A5_acceptance_segment_estimate":
        hdr + '\n  "【验收】{{N.est_effort}} 必须达成。",\n',
    "A6_publishArtifact_estimate":
        hdr + '\n  await __host.publishArtifact("a", "file", ["x", { description: "{{N.est_effort}} 个域" }]);\n',
    "A7_conclusion_estimate":
        hdr + '\n  conclusion: "完成 {{N.est_effort}} 个域",\n',
}
for name, block in cases.items():
    cls = ncl.classify_lines(block)
    r = ncl.lint(block, claims, source=src)
    out[name] = {"classes": {k: [x[0] for x in v] for k, v in cls.items()},
                 "ok": r["ok"],
                 "rules_hit": sorted({f["rule"] for f in r["findings"]})}

# ---- B. 真实归档 ASK_ANALYST 块喂给 lint（无 CLAIM_NUMBERS，模拟迁移前） ----
def lowered(path):
    for l in io.open(path, "r", encoding="utf-8").read().split("\n"):
        if l.startswith("export const payload"):
            return json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")


def ask_block(path):
    L = lowered(path)
    s = next(i for i, x in enumerate(L) if "const ASK_ANALYST = [" in x)
    e = next(i for i in range(s + 1, len(L)) if "].join" in L[i])
    return L[s + 1:e]


for tag, fname, key_lines in (
    ("89df", "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs", [122]),
    ("8682", "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs", [98, 110, 131, 132]),
):
    block = "\n".join(ask_block(os.path.join(ROOT, ".zcode", "workflow-runs", fname)))
    cls = ncl.classify_lines(block)
    inv = {}
    for k in ("prose", "machine", "quoted", "code"):
        for ln, _ in cls[k]:
            inv[ln] = k
    r = ncl.lint(block, [], dir_hint="")
    out["real_" + tag] = {
        "n_lines": len(block.split("\n")),
        "class_counts": {k: len(v) for k, v in cls.items()},
        "line122_or_key_classes": {"line%d" % ln: inv.get(ln, "NOT_CLASSIFIED") for ln in key_lines},
        "ok": r["ok"],
        "n_findings": r["summary"]["n_findings"],
        "by_rule": r["summary"]["by_rule"],
    }

# ---- C. 三例 cross_section_diff（按设计员给的形态） ----
v = ncph.validate_claim_numbers(claims, strict=False)
out["three_diff_examples"] = {
    "WRONG": ncph.cross_section_diff("【复核数据】32768", "【背景】未引用任何值", v)["problems"],
    "RIGHT": ncph.cross_section_diff("【复核数据】32768", "【背景】{{N.ratio_32768}}", v)["problems"],
    "STATIC": ncph.cross_section_diff('"【复核数据】" + vfText', "【背景】{{N.ratio_32768}}", v)["problems"],
}
# UNRENDERED 守卫被含数字的机器段击败？
out["unrendered_guard_defeat"] = ncph.cross_section_diff(
    '"【复核数据】" + vfText\n字节数 = 2017', "【背景】{{N.ratio_32768}}", v)["problems"]
r_guard = ncl.lint(hdr + '\n  "【复核数据】" + vfText,\n  "【背景】{{N.ratio_32768}}。",\n',
                   claims, source=src)
out["unrendered_guard_in_lint_rules"] = sorted({f["rule"] for f in r_guard["findings"]})

# ---- D. 未知 mustache 是否留在 render()['text'] ----
inj = "【背景】{{UNKNOWN_TOKEN_X}} 与 {{N.no_such_id}}"
rr = ncph.render(inj, v["by_id"])
out["unknown_token"] = {
    "problems": rr["problems"],
    "problem_strings_echo_token": "UNKNOWN_TOKEN_X" in json.dumps(rr["problems"], ensure_ascii=False),
    "rendered_text_echo_token": "UNKNOWN_TOKEN_X" in rr["text"],
    "rendered_text": rr["text"],
    "ok": rr["ok"],
}

# ---- E. 估算禁入验收段：按字面 tag 与按解析 id ----
out["estimate_tag_rules"] = {
    "ACCEPTANCE_SEGMENTS": list(ncph.ACCEPTANCE_SEGMENTS),
    "QUOTED_OPEN_has_复核": "【复核】" in ncl.QUOTED_OPEN.pattern,
    "QUOTED_OPEN_has_核查": "【核查】" in ncl.QUOTED_OPEN.pattern,
}

print(json.dumps(out, ensure_ascii=False, indent=2))
