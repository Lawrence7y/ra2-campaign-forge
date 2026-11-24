# -*- coding: utf-8 -*-
# N4 gate reviewer: independent textual probe over CANDIDATE_RESIGN_YES_V2.md.
# Enumerates every occurrence of the gate's "required elements" and "bad words",
# with line numbers, full line text, and polarity classification (my own judgment).
# Also does char-level analysis of the §5 binding line and computes the exact
# gate regex / loose regex / IRON-tight regex results.
import json, re, hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
DOC = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
OUT = ROOT / "lead/n4_gate_verdict_20261109/_n4gv_text_out.json"

b = DOC.read_bytes()
t = b.decode("utf-8")
lines = t.split("\n")

def occurrences(needle):
    out = []
    for i, L in enumerate(lines, start=1):
        pos = 0
        while True:
            k = L.find(needle, pos)
            if k < 0: break
            out.append({"line": i, "col": k + 1, "text": L,
                        "before": L[max(0, k-25):k], "after": L[k+len(needle):k+len(needle)+25]})
            pos = k + len(needle)
    return out

elements = ['逐行','十四行','九 hunk','语义层 YES','甲不再绑定','不签 APPROVE_SCOPE','未验']
bads = ['可应用母本','放行 N-5','已应用','已签 APPROVE_SCOPE']

res = {
    "doc_bytes": len(b), "doc_sha256": hashlib.sha256(b).hexdigest(),
    "lines_split_newline": len(lines),
    "required_elements": {k: {"count": len(occurrences(k)), "hits": occurrences(k)} for k in elements},
    "bad_words": {k: {"count": len(occurrences(k)), "hits": occurrences(k)} for k in bads},
    "raw_counts": {
        "不签 `APPROVE_SCOPE`": t.count("不签 `APPROVE_SCOPE`"),
        "不签 APPROVE_SCOPE": t.count("不签 APPROVE_SCOPE"),
        "不签APPROVE_SCOPE": t.count("不签APPROVE_SCOPE"),
        "不签 \\`APPROVE_SCOPE\\`": t.count("不签 \\`APPROVE_SCOPE\\`"),
        "不应用母本": t.count("不应用母本"),
        "可应用母本": t.count("可应用母本"),
        "可应用母本 in 不应用母本": "可应用母本" in "不应用母本",
        "不放行 N-5": t.count("不放行 N-5"),
        "放行 N-5": t.count("放行 N-5"),
        "已应用": t.count("已应用"),
        "已签 APPROVE_SCOPE": t.count("已签 APPROVE_SCOPE"),
    },
    "sections": {s: (s in t) for s in ['## 1','## 2','## 3','## 4','## 5','## 6']},
}

# --- gate regex (verbatim from GATE_CODE line 20) ---
gate_re = re.compile(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?')
gate_bindings = gate_re.findall(t)
# loose variant used by author
loose_re = re.compile(r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?')
loose_bindings = loose_re.findall(t)
# IRON-tight (this round's iron rule): "被核对象 SHA256 = " immediately followed by 64 hex
tight_re = re.compile(r'被核对象 SHA256 = ([0-9a-fA-F]{64})，字节数 = (\d+)')
tight_bindings = tight_re.findall(t)

res["binding_regex"] = {
    "gate_strict": {"pattern": gate_re.pattern, "count": len(gate_bindings), "values": gate_bindings},
    "loose": {"pattern": loose_re.pattern, "count": len(loose_bindings), "values": loose_bindings},
    "iron_tight": {"pattern": tight_re.pattern, "count": len(tight_bindings), "values": tight_bindings},
}

# --- line 122 char-level analysis ---
L122 = lines[121]  # 1-based 122
idx_obj = L122.find("被核对象")
idx_sha = L122.find("SHA256 =")
infix = L122[idx_obj + len("被核对象"): idx_sha] if idx_obj >= 0 and idx_sha >= 0 else None
res["line122"] = {
    "text": L122,
    "len_chars": len(L122),
    "idx_被核对象": idx_obj, "idx_SHA256": idx_sha,
    "infix": infix, "infix_len": len(infix) if infix is not None else None,
    "char_between_obj_and_sha_is_space_only": infix == " ",
    "hex_backtick_wrapped": bool(re.search(r'`([0-9a-f]{64})`', L122)),
    "hex_positions": [m.span() for m in re.finditer(r'[0-9a-f]{64}', L122)],
}

# --- all lines containing SHA256 hex anywhere ---
hex_lines = []
for i, L in enumerate(lines, 1):
    for m in re.finditer(r'[0-9a-f]{64}', L):
        hex_lines.append({"line": i, "col": m.start()+1, "hex": m.group(0), "text": L[:200]})
res["all_64hex_lines"] = hex_lines

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "doc_bytes": res["doc_bytes"], "doc_sha256": res["doc_sha256"],
    "required_elements_counts": {k: v["count"] for k, v in res["required_elements"].items()},
    "bad_words_counts": {k: v["count"] for k, v in res["bad_words"].items()},
    "raw_counts": res["raw_counts"],
    "sections": res["sections"],
    "binding_regex": {k: {"count": v["count"], "values": v["values"]} for k, v in res["binding_regex"].items()},
    "line122": res["line122"],
    "all_64hex_lines": res["all_64hex_lines"],
}, ensure_ascii=False, indent=2))
