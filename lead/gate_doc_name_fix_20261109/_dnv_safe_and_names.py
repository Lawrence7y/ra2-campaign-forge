# 独立复核员脚本 ②b：核对「49 个安全实例」「33 const DOC + 3【交付】」「36 处主件名」
import json, re, pathlib, collections

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_safe_and_names_out.json"
DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")
JS_STR = re.compile(r'"(?:[^"\\]|\\.)*"')

def decode_js(tok):
    s = tok[1:-1]; out = []; i = 0
    mp = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "\\": "\\", '"': '"', "'": "'", "0": "\0"}
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i+1]
            if c == "u" and i + 5 < len(s):
                try: out.append(chr(int(s[i+2:i+6], 16))); i += 6; continue
                except ValueError: pass
            out.append(mp.get(c, c)); i += 2
        else: out.append(s[i]); i += 1
    return "".join(out)

def gate_lines(lowered):
    m = GATE_HEAD.search(lowered)
    if not m: return None
    st = m.end()
    j = re.search(r"\]\s*\.join\s*\(", lowered[st:])
    if not j: return None
    return [decode_js(t) for t in JS_STR.findall(lowered[st:st+j.start()])]

gen1 = []; gen3 = []; other = []; defects = []
for p in sorted(WFDIR.glob("*.mjs")):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"export\s+const\s+payload\s*=\s*", text)
    if not m: continue
    obj, _ = json.JSONDecoder().raw_decode(text, m.end())
    lowered = obj.get("lowered", "")
    lines = gate_lines(lowered)
    if lines is None: continue
    src = "\n".join(lines)
    is_def = bool(DEFECT_RE.search(src))
    if is_def: defects.append((p.name, lowered, lines)); continue
    g1 = [ln for ln in lines if re.search(r"doc\s*=\s*root\s*/\s*'", ln)]
    g1b = [ln for ln in lines if "交付件缺失" in ln]
    g3 = [ln for ln in lines if re.search(r"expected\s*=\s*wd\s*/\s*'", ln)]
    g3b = [ln for ln in lines if "主交付件未按约定命名" in ln]
    if g1 and g1b: gen1.append(p.name)
    elif g3 and g3b: gen3.append(p.name)
    elif g1 or g3: other.append({"file": p.name, "g1": g1, "g1b": g1b, "g3": g3, "g3b": g3b})
    else: other.append({"file": p.name, "note": "neither"})

# 36 处主件名：const DOC= 与 【交付】文本
DELIVER_RE = re.compile(r"【交付】[^\[\]]*?([A-Z][A-Z0-9_]*\.md)")
rows = []
for fname, lowered, lines in defects:
    dc = re.findall(r'const\s+DOC\s*=\s*"([^"]+)"', lowered)
    dirm = re.search(r'const\s+DIR\s*=\s*"([^"]+)"', lowered)
    wdm = [ln for ln in lines if re.search(r"wd\s*=\s*root\s*/\s*'", ln)]
    wd = re.search(r"wd\s*=\s*root\s*/\s*'([^']+)'", "\n".join(lines))
    dom = wd.group(1).split("/")[-1] if wd else (dirm.group(1).strip("/").split("/")[-1] if dirm else "?")
    main = dc[0].split("/")[-1] if dc else None
    src_kind = "const DOC=" if main else None
    if not main:
        hints = DELIVER_RE.findall(lowered)
        if hints: main = hints[0]; src_kind = "【交付】文本"
    rows.append({"file": fname, "domain": dom, "main": main, "src": src_kind})

# 对照编排方 36 行清单（从任务给的 sites 表抄录）
EXPECTED = {
 "962827dd": "C07_SELFCHECK_AUDIT.md", "66e74798": "C07_GATE_G1_G5_FIX.md",
 "80551feb": "PROTOCOL_ATTACK_TEST.md", "80d9632c": "C07_IDENTITY_SLOT.md",
 "bc3fed8c": "C07_IDENTITY_SLOT.md", "24bda605": "C07_TRUTH_SELF_PROOF.md",
 "636adfc5": "COUNTERPART_FIX.md", "5ad91c91": "F2D_ROOT_CAUSE.md",
 "fed3c2a2": "GATE_FALSE_POSITIVE_5_6_7.md", "65d9f3a9": "GATE_LITERAL_MATCH_POSTMORTEM.md",
 "65b875da": "GATE_R9R12_REGRESSION.md", "a4a38b66": "APPROVAL_PACK.md",
 "13448f03": "LEDGER_APPENDIX_DRAFT.md", "616f12ea": "LEDGER_APPENDIX_DRAFT.md",
 "830e57b2": "LEDGER_APPENDIX_DRAFT.md", "db5bad08": "RULING_MATRIX_AB.md",
 "c482b235": "MATRIX_DEFECT_REACHABILITY.md", "69087c8f": "MATRIX_ROW5_COUPLING.md",
 "f0c21a59": "RULING_STATIC_ORDER.md", "ffc43bb0": "DIM_COLUMN_MAPPING.md",
 "903e6b21": "N11_WORDING_FIX.md", "af6f3c87": "CANDIDATE_RESIGN_YES_V2.md",
 "a1c4b1fd": "O1PRIME_REACHABILITY.md", "ebe5b75c": "PENDING_FACTPACK_C02_C03_C06_C07.md",
 "d3ec8aec": "R11_F2_COVERAGE_FIX.md", "cec38f8b": "S604_ATTRIBUTION.md",
 "88b03f6c": "S604_EXCLUSIVITY.md", "5e5d5e49": "S604_SCRIPT_GAP.md",
 "bc9d8b8e": "S604_SCRIPT_GAP.md", "dcda8414": "S604_SCRIPT_HUNT.md",
 "cd88a9f5": "SAMEDOC_LINK.md", "15585c14": "STRICT_EXPOSURE.md",
 "53714984": "UNIFIED_TEXT_FIX.md", "802eb959": "U5U6_MIRROR_TEXTS.md",
 "f123d326": "V2_PRECISION_FIX_PROPOSAL.md", "27d477b1": "W2_SAME_CAUSE.md",
}
mismatch = []
for r in rows:
    key = r["file"].replace("dwfrun-", "")[:8]
    exp = EXPECTED.get(key)
    r["expected"] = exp
    r["match"] = (r["main"] == exp)
    if not r["match"]: mismatch.append(r)
    p = ROOT / "lead" / r["domain"] / (r["main"] or "?")
    r["delivered"] = p.is_file()
    r["bytes"] = p.stat().st_size if p.is_file() else 0

out = {
 "safe_gen1": len(gen1), "safe_gen3": len(gen3), "safe_total": len(gen1) + len(gen3),
 "safe_in_defect": [x for x in gen1 + gen3 if x in [d[0] for d in defects]],
 "other_gate_shapes": len(other), "other_sample": other[:6],
 "defect_files": len(defects),
 "const_doc_count": sum(1 for r in rows if r["src"] == "const DOC="),
 "deliver_text_count": sum(1 for r in rows if r["src"] == "【交付】文本"),
 "no_source": [r for r in rows if not r["src"]],
 "name_mismatches": mismatch, "names_match": len(rows) - len(mismatch),
 "delivered_count": sum(1 for r in rows if r["delivered"]),
 "rows": rows,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False, indent=2))
