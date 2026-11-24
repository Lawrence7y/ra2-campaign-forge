# -*- coding: utf-8 -*-
"""_ocw_verify.py — 本会话独立复核脚本（只读）。
用途：验证复核员 6 处破口 + 抽 20 条 CLAIMS 原文 + 绑定行重建 + 9 件指纹。
运行：python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/orch_claims_20261109/_ocw_verify.py" > ".../_ocw_verify_out.json"
零真机、零采样代码；只读路径；hashlib 指纹。"""
import json, pathlib, re, hashlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
RUNS = ROOT / ".zcode/workflow-runs"
WD = ROOT / "lead/orch_claims_20261109"
out = {}


def lowered(name):
    p = RUNS / name
    t = p.read_text(encoding="utf-8")
    s = t[t.index("export const payload =") + len("export const payload ="):].lstrip()
    return json.JSONDecoder().raw_decode(s)[0]["lowered"]


def grep_lines(name, keys, ctx=0):
    ls = lowered(name).splitlines()
    hits = []
    for i, l in enumerate(ls, 1):
        if any(k in l for k in keys):
            hits.append({"line": i, "text": l[:600]})
    return hits


def file_lines(rel, nums):
    p = ROOT / rel
    ls = p.read_text(encoding="utf-8").splitlines()
    return {str(n): ls[n-1][:600] if 1 <= n <= len(ls) else "<OOR>" for n in nums}


# ---- 破口①: "有三条清晰的方向性" 却列 4 项；"系统性偏乐观或偏保守" 原文 ----
out["bp1_directionality"] = {
    "old_report_line150": (WD / "_oc_ORCH_CLAIMS_AUDIT.md").read_text(encoding="utf-8").splitlines()[149][:400],
    "archive_115_136": grep_lines("dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs",
                                  ["偏乐观", "方向性", "系统性低估"], 0),
}

# ---- 破口②: #6 GP-A1 PASS→CATCH 归档原句（dwfrun-e526a76c）----
out["bp2_gpa1_literal"] = {
    "e526a76c": grep_lines("dwfrun-e526a76c-1d47-40d5-ab0b-19aabad9af91.mjs",
                           ["PASS→CATCH", "GP-A1", "唯一变更条目"]),
    "old_report_claim6_line": (WD / "_oc_ORCH_CLAIMS_AUDIT.md").read_text(encoding="utf-8").splitlines()[58][:400],
}

# ---- 破口③: _dn_glm_final.md:256 / :293 是否同件内撤回 ----
p = ROOT / "lead/gate_doc_name_fix_20261109/_dn_glm_final.md"
ls = p.read_text(encoding="utf-8").splitlines()
out["bp3_dn_glm"] = {
    "total_lines": len(ls),
    "line_256": ls[255][:600] if len(ls) >= 256 else "<OOR>",
    "line_293": ls[292][:600] if len(ls) >= 293 else "<OOR>",
    "withdraw_words_in_whole_file": [i+1 for i, l in enumerate(ls)
                                     if any(k in l for k in ["撤回", "作废", "不成立", "更正", "已废"])][:40],
    "external_ref_GATE_DOC_NAME_FIX": file_lines("lead/gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md", [234, 302]),
}

# ---- 破口④: 两处真残留 + :182 "数字层没有残留错值" ----
out["bp4_residues"] = {
    "868215ce_217_226": grep_lines("dwfrun-868215ce-0000-0000-0000-000000000000.mjs",
                                   ["十个域", "10 个仍报问题的域"]) if False else "see dedicated scan below",
    "stale_pass_57_59_107": file_lines("lead/stale_pass_20261109/STALE_PASS_INVENTORY.md", [57, 59, 107, 174]),
    "old_report_line182": (WD / "_oc_ORCH_CLAIMS_AUDIT.md").read_text(encoding="utf-8").splitlines()[181][:500],
}

# 全量 glob 找 868215ce 与 32 域描述
cands = sorted(RUNS.glob("dwfrun-868215ce*.mjs"))
for c in cands:
    out["bp4_residues"]["868215ce_file"] = c.name
    out["bp4_residues"]["868215ce_hits"] = grep_lines(c.name, ["十个域", "10 个仍报问题的域", "10 个", "5 个"])[:30]

# ---- 破口⑤: CLAIM_NUMBERS 在归档 .mjs 中出现次数；本任务 source_kind；裸数字 token ----
claim_num_files = []
for f in sorted(RUNS.glob("*.mjs")):
    try:
        lo = lowered(f.name)
    except Exception:
        continue
    if "CLAIM_NUMBERS" in lo:
        claim_num_files.append(f.name)
out["bp5"] = {
    "archive_files_with_CLAIM_NUMBERS": claim_num_files,
    "count": len(claim_num_files),
    "this_book_source_kind_present": "source_kind" in lowered("dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs"),
    "old_report_line222": (WD / "_oc_ORCH_CLAIMS_AUDIT.md").read_text(encoding="utf-8").splitlines()[221][:400],
}
lo89 = lowered("dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs")
ask_start = lo89.find("ASK_ANALYST")
seg = lo89[ask_start:] if ask_start >= 0 else lo89
out["bp5"]["arabic_numeric_tokens_in_ASK_ANALYST_tail"] = len(re.findall(r"[0-9]+(?:\.[0-9]+)?", seg))
out["bp5"]["chinese_numeral_classifiers"] = len(re.findall(r"[一二三四五六七八九十百]+[件条行个域倍条项分针层处]", seg))

# ---- 破口⑥: #11/#15/#17 是否被下发（排除本任务书）----
ids_keys = {
    "11": ["n4_yi_final", "门禁挑错中稿", "挑错中稿"],
    "15": ["SELF_TEST=FAIL 是脚本缺陷", "SELF_TEST = FAIL", "脚本缺陷"],
    "17": ["修好就能插", "H5 修好", "可以插"],
}
book_hits = {}
for k, keys in ids_keys.items():
    hs = []
    for f in sorted(RUNS.glob("*.mjs")):
        if f.name.startswith("dwfrun-89df48db"):
            continue
        try:
            lo = lowered(f.name)
        except Exception:
            continue
        for i, l in enumerate(lo.splitlines(), 1):
            if any(x in l for x in keys):
                hs.append({"file": f.name, "line": i, "text": l[:300]})
    book_hits[k] = hs[:40]
out["bp6_literal_taskbooks"] = book_hits
out["bp6_stats_claim"] = json.loads((WD / "_oc_stats_out.json").read_text(encoding="utf-8"))

# ---- 20 条 CLAIMS 逐字抽取 ----
m = re.search(r"const CLAIMS = \[(.*?)\];", lo89, re.S)
literals = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)) if m else []
numbered = [s for s in literals if re.match(r"^\d+\.\s", s)]
out["claims"] = {
    "archive_literals": len(literals),
    "numbered": len(numbered),
    "lines": numbered,
    "bound_bytes": len("\n".join(numbered).encode("utf-8")),
    "bound_sha256": hashlib.sha256("\n".join(numbered).encode("utf-8")).hexdigest(),
}

# ---- 9 件指纹（本会话复核 hashlib）----
fp_expect = {
    "lead/pvalue_recalc_20261109/_pv_PVALUE_RECALC.md": ("277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac", 29780),
    "lead/keff_calc_20261109/KEFF_CALC.md": ("4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
    "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    "lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md": ("e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8", 82856),
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md": ("a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
fp = []
for rel, (esha, ebytes) in fp_expect.items():
    p = ROOT / rel
    b = p.read_bytes()
    fp.append({"file": rel, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
               "sha_match": hashlib.sha256(b).hexdigest() == esha, "bytes_match": len(b) == ebytes})
out["fingerprints"] = {"count": len(fp), "all_match": all(x["sha_match"] and x["bytes_match"] for x in fp), "items": fp}

# ---- 越界检查：写域文件清单 / HEAD / 受保护路径状态由外部 git 命令另跑 ----
out["write_domain_files"] = sorted(f.name for f in WD.iterdir() if f.is_file())

print(json.dumps(out, ensure_ascii=False, indent=2))
