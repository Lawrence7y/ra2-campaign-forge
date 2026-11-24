# -*- coding: utf-8 -*-
"""_nc2_regression.py —— 对复核 verdict=partial 八条破口的定点回归（本轮实跑）。

只读加载 _nc2_placeholder.py / _nc2_lint.py；输入为内存构造或只读在盘件。
用法：python -I -X utf8 <绝对路径>/_nc2_regression.py > <绝对路径>/_nc2_regression_out.json
"""
from __future__ import annotations

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


ph = load("nc2ph_reg", "_nc2_placeholder.py")
ln = load("nc2ln_reg", "_nc2_lint.py")
claims = ph.build_demo(ROOT)
v = ph.validate_claim_numbers(claims, strict=True, root=ROOT)


def src_of(cs):
    s = {"version": 1, "prev_sha256": "", "prev_hashes": [], "history": [],
         "claims": [dict(c) for c in cs], "block_sha256": "", "binding_line": ""}
    s["block_sha256"] = hashlib.sha256(ph.chain_block_bytes(s)).hexdigest()
    s["binding_line"] = ph.binding_line(ph.chain_block_bytes(s))
    for c in s["claims"]:
        c["source_block_sha256"] = s["block_sha256"]
    return s


src = src_of(claims)
hdr = "【数字源】version=1\n" + src["binding_line"]
out = {"validate_demo": {"ok": v["ok"], "problems": v["problems"],
                         "n_claims": len(claims)}}

# ---- 破口 (1)：source_kind 自报 / value 与 sha256 不绑定 ----
vp = {}
c = dict(claims[0]); c["value"] = 999
vp["V1_change_value_keep_sha256"] = {
    "ok": ph.validate_claim_numbers([c] + claims[1:], strict=True, root=ROOT)["ok"],
    "problems": [p for p in ph.validate_claim_numbers(
        [c] + claims[1:], strict=True, root=ROOT)["problems"]
        if "claim[0]" in p]}
c = dict(claims[0]); c["stdout_sha256"] = "x"
vp["V2_stdout_sha256_bogus"] = ph.validate_claim_numbers(
    [c] + claims[1:], strict=True, root=ROOT)["problems"][:3]
c = dict(claims[0]); c["command"] = "echo fake"
c = ph.seal_claim(c)
vp["V3_command_not_rerun"] = {
    "ok": ph.validate_claim_numbers([c] + claims[1:], strict=True, root=ROOT)["ok"],
    "note": "command 本身不重跑（见未验项），但改 command 会改变 claim_digest"}
fl = [x for x in claims if x["source_kind"] == "文件行"][0]
for i, mut in enumerate([
    lambda d: d.pop("line_sha256"),
    lambda d: d.update(path="no/such/file.md"),
    lambda d: d.update(value=999),
    lambda d: d.update(line=99999),
]):
    d = dict(fl); mut(d)
    if i == 2:
        d = ph.seal_claim(d)
    r = ph.validate_claim_numbers([d], strict=True, root=ROOT)
    vp["F%d_fileline_probe" % (i + 1)] = {"ok": r["ok"], "problems": r["problems"]}
dv = dict([x for x in claims if x["source_kind"] == "推导"][1])
dv["value"] = 0.86; dv = ph.seal_claim(dv)
vp["D1_derivation_wrong_value"] = ph.validate_claim_numbers(
    [dv], strict=True, root=ROOT)["problems"]
# ★ 决定性：错值 10 标「实跑」+ 假 command / 假 stdout_sha256
bogus = dict(claims[0])
bogus.update(id="bogus_10", value=10, command="echo fake",
             stdout_path="no/such/stdout.txt", stdout_sha256="a" * 64,
             command_exit=0)
bogus = ph.seal_claim(bogus)
r = ph.validate_claim_numbers(claims + [bogus], strict=True, root=ROOT)
vp["DECISIVE_wrong10_labeled_实跑"] = {"ok": r["ok"],
    "problems": [p for p in r["problems"] if "bogus" in p or "claim[6]" in p]}
out["validator_probes"] = vp

# ---- 破口 (2)(3)(4)(6)：段落判定 / 验收段 / 发布段 / UNRENDERED ----
def lint_of(text, *, source=None, rendered=False, cs=None):
    r = ln.lint(text, cs or claims, source=source, rendered=rendered)
    return {"ok": r["ok"], "rules": sorted({f["rule"] for f in r["findings"]})}


def arr(body):
    return hdr + "\nconst ASK_ANALYST = [\n" + body + "\n].join(\"\\n\");\n"


bp = {
    "P1_title_launder": arr('  "【编排方实跑指纹】实测 7 个域、3 处问题。",'),
    "P2_review_segment": arr('  "【复核】{{N.est_effort}} 必须达成。",'),
    "P3_publishArtifact": hdr + '\n  await __host.publishArtifact("a", "file", ["x", {description: "{{N.est_effort}} 个域"}]);\n',
    "P4_delivery_string": arr('  "【交付】{{N.est_effort}} 必须达成。",'),
    "A3_acceptance_estimate": arr('  "【验收】{{N.est_effort}} 必须达成。",'),
    "A7_conclusion_estimate": hdr + '\n  conclusion: "完成 {{N.est_effort}} 个域",\n',
    "P1b_unregistered_under_title": arr('  "【编排方实跑指纹】实测 13 个域。",'),
}
out["bypass_probes"] = {}
for name, text in bp.items():
    out["bypass_probes"][name] = lint_of(text, source=src)
    out["bypass_probes"][name]["expected_reject"] = True
    out["bypass_probes"][name]["rejected"] = out["bypass_probes"][name]["ok"] is False

# UNRENDERED：带必贴绑定行也须 FAIL
out["unrendered_with_binding_line"] = lint_of(
    arr('  "【复核数据】" + vfText,\n  "【背景】{{N.ratio_32768}}。",'),
    source=src, rendered=True)

# ---- 破口 (5)：89df 的【背景—— 不应再打开引述区 ----
p89 = os.path.join(ROOT, ".zcode", "workflow-runs",
                   "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs")
L = None
for l in io.open(p89, "r", encoding="utf-8").read().split("\n"):
    if l.startswith("export const payload"):
        L = json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")
        break
s = next(i for i, x in enumerate(L) if "const ASK_ANALYST = [" in x)
e = next(i for i in range(s + 1, len(L)) if "].join" in L[i])
block = "\n".join(L[s + 1:e])
cls = ln.classify_lines(block)
inv = {}
for k in ("prose", "machine", "quoted", "code"):
    for lineno, _ in cls[k]:
        inv[lineno] = k
out["classify_89df"] = {
    "counts": {k: len(v) for k, v in cls.items()},
    "key_abs_lines": {str(a): inv.get(a - (s + 1), "NOT_CLASSIFIED")
                      for a in (107, 108, 110, 113, 122, 124)},
    "note": "lowered:122 应判 prose（旧版误判 quoted）；:110【背景—— 不再开引述区"}

# ---- 破口 (4)：8682 的 :170/:217/:226 必须进入扫描范围 ----
p86 = os.path.join(ROOT, ".zcode", "workflow-runs",
                   "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs")
for l in io.open(p86, "r", encoding="utf-8").read().split("\n"):
    if l.startswith("export const payload"):
        L86 = json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")
        break
lines_of_interest = {k: L86[k - 1] for k in (98, 110, 170, 217, 226)}
out["real_8682_lines"] = {}
for k, line in lines_of_interest.items():
    tb = hdr + "\nconst ASK_ANALYST = [\n" + line + "\n].join(\"\\n\");\n"
    r = ln.lint(tb, claims, source=src)
    out["real_8682_lines"]["lowered:%d" % k] = {
        "ok": r["ok"],
        "rules": sorted({f["rule"] for f in r["findings"]}),
        "caught": r["ok"] is False}

# ---- 破口 (7)：全链自洽 ----
tmp = os.path.join(D, "_nc2_reg_chain_tmp.json")
try:
    # ★ 用 version>=2 的「已纠正」源做篡改：version=1 的 history 本就为空，
    #   抹 history 不构成篡改（旧探针 _ncv_final.py 用 version=1 属口径问题）。
    store = {"version": 0, "prev_sha256": "", "prev_hashes": [], "history": [],
             "claims": [dict(c) for c in claims]}
    st = ph.save_source(tmp, store)
    ph.correct_value(tmp, "bindings_zero", 5, evidence="regression probe")
    st = ph.load_source(tmp)
    out["chain_selfconsistency"] = {
        "version": st["version"],
        "n_history": len(st["history"]),
        "per_claim_equals_block": all(
            c.get("source_block_sha256") == st["block_sha256"] for c in st["claims"]),
        "block_sha256": st["block_sha256"][:16]}
    st2 = json.load(io.open(tmp, "r", encoding="utf-8"))
    st2["history"] = []
    st2["prev_sha256"] = "0" * 64
    tb = ph.taskbook_header(st2) + '\n"【背景】{{N.domains_nonempty}}。"\n'
    out["chain_selfconsistency"]["after_tamper"] = ph.check_chain(tb, st2)
finally:
    if os.path.exists(tmp):
        os.remove(tmp)

# ---- 破口 (8)：自检覆盖 ----
sf = json.load(io.open(os.path.join(D, "_nc2_lint_selftest_out.json"), "r",
                       encoding="utf-8"))
hit = set()
for row in sf["rows"]:
    hit.update(row.get("rules_hit", []))
out["selftest_coverage"] = {"n": sf["n"], "n_pass": sf["n_pass"],
                            "n_real_caught": sf["n_real_caught"],
                            "rules_exercised": sorted(hit),
                            "n_rules_exercised": len(hit)}

# ---- 覆盖判定 ----
out["summary"] = {
    "bypass_probes_all_rejected": all(
        x["rejected"] for x in out["bypass_probes"].values()),
    "unrendered_with_binding_line_rejected":
        out["unrendered_with_binding_line"]["ok"] is False,
    "line122_classified_prose":
        out["classify_89df"]["key_abs_lines"].get("122") == "prose",
    "all_5_real_damage_lines_caught": all(
        x["caught"] for x in out["real_8682_lines"].values()),
    "chain_tamper_rejected":
        out["chain_selfconsistency"]["after_tamper"]["ok"] is False,
    "validator_bogus_实跑_rejected":
        vp["DECISIVE_wrong10_labeled_实跑"]["ok"] is False,
}

print(json.dumps(out, ensure_ascii=False, indent=2))
