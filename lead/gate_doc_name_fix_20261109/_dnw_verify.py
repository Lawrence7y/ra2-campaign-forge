# -*- coding: utf-8 -*-
"""撰写员独立复核 A：八件上游指纹现值 + .zcode/workflow-runs 位点独立重扫。
只读历史件；快照只写本写域。python -I -X utf8 <绝对路径>"""
import json, re, pathlib, hashlib, collections

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_verify_out.json"

# 编排方派发常量（任务【编排方指纹】，8 件）
FPS = {
    "lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md": ("302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c", 31692),
    "lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md": ("8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
    "lead/gate_subject_id_20261109/_si_fix_lib.py": ("54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee", 2850),
    "lead/gate_subject_id_20261109/_si_gatescan_out.json": ("c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94", 611043),
    "lead/gate_subject_id_20261109/_si_wfscan_out.json": ("e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52", 180256),
    "lead/gate_subject_id_20261109/_si_exploit_out.txt": ("151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587", 5717),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

fp_rows = []
for rel, (exp_sha, exp_nb) in FPS.items():
    p = ROOT / rel
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    fp_rows.append({"file": rel, "sha256": sha, "bytes": len(raw),
                    "expected_sha256": exp_sha, "expected_bytes": exp_nb,
                    "match": sha == exp_sha and len(raw) == exp_nb})
fp_summary = {"upstream_matches": sum(1 for r in fp_rows if r["match"]), "total": len(fp_rows)}

# ---- 位点独立重扫 ----
DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
DEFECT_LITERAL = "DOC=max(cands,key=lambda p:p.stat().st_size)"
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")
EXPECTED_RE = re.compile(r"expected\s*=\s*wd\s*/\s*'([^']+\.md)'")
DOCROOT_RE = re.compile(r"doc\s*=\s*root\s*/\s*'([^']+\.md)'")
WD_RE = re.compile(r"wd\s*=\s*root\s*/\s*'([^']+)'")
CONSTDOC_RE = re.compile(r'const\s+DOC\s*=\s*"([^"]+\.md)"')
DELIVER_RE = re.compile(r"【交付】[^\n]{0,400}?([A-Z0-9_]{4,}\.md)")

def gate_block_lines(lowered):
    """返回所有 GATE_CODE 块内的 JS 字符串元素（已解转义），供逐行检查。"""
    out = []
    for m in GATE_HEAD.finditer(lowered):
        st = m.end()
        j = re.search(r"\]\s*\.join\s*\(", lowered[st:])
        block = lowered[st:st + (j.start() if j else 20000)]
        for tok in re.findall(r'"(?:[^"\\]|\\.)*"', block):
            s = tok[1:-1]
            s = re.sub(r"\\n", "\n", s)
            s = re.sub(r"\\'", "'", s)
            s = re.sub(r'\\"', '"', s)
            out.append(s)
    return out

all_files = sorted(p for p in WFDIR.iterdir() if p.is_file())
mjs = [p for p in all_files if p.suffix == ".mjs"]
recs, parse_errors = [], []
for p in mjs:
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"export\s+const\s+payload\s*=\s*", text)
    if not m:
        parse_errors.append({"file": p.name, "err": "no payload"}); continue
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, m.end())
    except Exception as e:
        parse_errors.append({"file": p.name, "err": "json:" + str(e)}); continue
    low = obj.get("lowered", "") if isinstance(obj, dict) else ""
    glines = gate_block_lines(low)
    gate_hit = sum(1 for ln in glines if DEFECT_RE.search(ln))
    whole_lit = low.count(DEFECT_LITERAL)
    expected = [mm.group(1) for ln in glines for mm in [EXPECTED_RE.search(ln)] if mm]
    docroot = [mm.group(1) for ln in glines for mm in [DOCROOT_RE.search(ln)] if mm]
    wds = [mm.group(1) for ln in glines for mm in [WD_RE.search(ln)] if mm]
    constdocs = CONSTDOC_RE.findall(low)
    deliver = DELIVER_RE.findall(low)
    recs.append({"file": p.name, "gate_hit": gate_hit, "whole_lit": whole_lit,
                 "expected": expected, "docroot": docroot, "wds": wds,
                 "constdocs": constdocs, "deliver": deliver})

defect = [r for r in recs if r["gate_hit"] > 0]
whole = [r for r in recs if r["whole_lit"] > 0]
noise = [r["file"] for r in whole if r["gate_hit"] == 0]
# 安全实例：门禁块内显式命名（expected=wd 或 doc=root）且块内无 DOC=max
safe_expected = [r for r in recs if r["expected"] and r["gate_hit"] == 0]
safe_docroot = [r for r in recs if r["docroot"] and not r["expected"] and r["gate_hit"] == 0]
safe_all = [r for r in recs if (r["expected"] or r["docroot"]) and r["gate_hit"] == 0]
safe_in_defect = [r["file"] for r in defect if r["expected"] or r["docroot"]]

dom = collections.Counter()
for r in defect:
    d = (r["wds"][0].split("/")[-1] if r["wds"] else "?")
    dom[d] += 1

checks = {
    "all_files_total": len(all_files),
    "mjs_total": len(mjs),
    "payload_parse_errors": parse_errors,
    "gate_defect_files": len(defect),
    "gate_defect_total_hits": sum(r["gate_hit"] for r in defect),
    "domains": len(dom),
    "domain_multiplicity": {k: v for k, v in sorted(dom.items()) if v > 1},
    "wholefile_literal_files": len(whole),
    "noise_files_in_wholefile_only": noise,
    "safe_expected_files": len(safe_expected),
    "safe_docroot_files": len(safe_docroot),
    "safe_total_files": len(safe_all),
    "safe_in_defect_set": safe_in_defect,
}
out = {"fp_summary": fp_summary, "fp_rows": fp_rows, "checks": checks,
       "domains": dict(sorted(dom.items())),
       "defect_files": [{"file": r["file"], "constdocs": r["constdocs"],
                         "deliver": r["deliver"][:2], "wds": r["wds"]} for r in defect]}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("FP", json.dumps(fp_summary, ensure_ascii=False))
for r in fp_rows:
    print("  %-64s match=%s bytes=%d" % (r["file"].split("/")[-1], r["match"], r["bytes"]))
print("CHECKS", json.dumps(checks, ensure_ascii=False, indent=1))
print("DOMAINS", json.dumps(dict(sorted(dom.items())), ensure_ascii=False))
