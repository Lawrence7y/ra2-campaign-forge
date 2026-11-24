# 独立复核员脚本 ②：从零独立重扫 .zcode/workflow-runs 全部 mjs
# 口径：自己 json 解析 payload → lowered → 定位 GATE_CODE 块 → 块内数 DOC=max(...st_size)
# 同时给全文件字面口径、写域集合、显式命名安全实例、每处选择段原样（供 ③ 用）
import json, re, pathlib, hashlib, collections

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WFDIR = ROOT / ".zcode/workflow-runs"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_rescan_out.json"

DEFECT = "DOC=max(cands,key=lambda p:p.stat().st_size)"
DEFECT_RE = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")
JS_STR = re.compile(r'"(?:[^"\\]|\\.)*"')

def decode_js(tok):
    s = tok[1:-1]
    out = []; i = 0
    mp = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v",
          "\\": "\\", '"': '"', "'": "'", "0": "\0"}
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i + 1]
            if c == "u" and i + 5 < len(s):
                try:
                    out.append(chr(int(s[i+2:i+6], 16))); i += 6; continue
                except ValueError:
                    pass
            out.append(mp.get(c, c)); i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)

def gate_blocks(lowered):
    """返回 [(block_text, [逐行 python 源码])]，按出现顺序"""
    res = []
    for m in GATE_HEAD.finditer(lowered):
        st = m.end()
        j = re.search(r"\]\s*\.join\s*\(", lowered[st:])
        if not j:
            res.append((lowered[st:st+20000], None)); continue
        block = lowered[st:st + j.start()]
        lines = [decode_js(t) for t in JS_STR.findall(block)]
        res.append((block, lines))
    return res

all_files = sorted(p for p in WFDIR.iterdir() if p.is_file())
mjs = [p for p in all_files if p.suffix == ".mjs"]
recs = []
parse_errors = []
for p in mjs:
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"export\s+const\s+payload\s*=\s*", text)
    if not m:
        parse_errors.append({"file": p.name, "err": "no payload decl"}); continue
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, m.end())
    except Exception as e:
        parse_errors.append({"file": p.name, "err": "json: " + str(e)}); continue
    lowered = obj.get("lowered", "") if isinstance(obj, dict) else ""
    blocks = gate_blocks(lowered)
    n_whole = len(re.findall(re.escape(DEFECT), lowered))
    n_gate = sum(1 for blk, lines in blocks if lines is not None and DEFECT_RE.search("\n".join(lines)))
    # 全文件字面（含任务书引用）用宽松正则再数一次
    n_whole_loose = len(DEFECT_RE.findall(lowered))
    doc_const = re.findall(r'const\s+DOC\s*=\s*"([^"]+)"', lowered)
    dirm = re.search(r'const\s+DIR\s*=\s*"([^"]+)"', lowered)
    # 显式 expected=wd/'X.md'
    expected = []
    for blk, lines in blocks:
        if lines:
            for ln in lines:
                mm = re.search(r"expected\s*=\s*wd\s*/\s*'([^']+)'", ln)
                if mm: expected.append(mm.group(1))
    # wd=root/'lead/xxx'
    wds = []
    for blk, lines in blocks:
        if lines:
            for ln in lines:
                mm = re.search(r"wd\s*=\s*root\s*/\s*'([^']+)'", ln)
                if mm: wds.append(mm.group(1))
    # 选择段（cands 行到 NB= 行）
    segs = []
    for blk, lines in blocks:
        if not lines: continue
        for i, ln in enumerate(lines):
            if "cands=sorted(" in ln or ("cands=" in ln and "glob" in ln) or "DOC=max(" in ln or "cands=[p for p" in ln:
                # 取以 DOC=max 或 cands= 定义开头、到 NB= 的连续 5 行窗口
                j = i
                while j < len(lines) and "NB=" not in lines[j]:
                    j += 1
                seg = lines[max(0, i-2):j+1]
                segs.append({"start": max(0, i-2), "end": j, "lines": seg})
                break
    recs.append({
        "file": p.name, "bytes": p.stat().st_size,
        "payload_keys": sorted(obj.keys()) if isinstance(obj, dict) else [],
        "gate_blocks": len(blocks),
        "gate_defect_hits": n_gate,
        "wholefile_defect_literal_exact": n_whole,
        "wholefile_defect_literal_loose": n_whole_loose,
        "const_DOC": doc_const,
        "const_DIR": dirm.group(1) if dirm else None,
        "expected": expected,
        "wds": wds,
        "gate_first_line": (blocks[0][1][0] if blocks and blocks[0][1] else None),
        "gate_print_lines": [ln for blk, lines in blocks if lines for ln in lines if "print(json.dumps(" in ln],
        "gate_init_lines": [ln for blk, lines in blocks if lines for ln in lines if re.match(r"^P=\[\]", ln)],
        "segments": segs,
        "has_expected_in_gate": bool(expected),
        "has_max_in_gate": any(lines and DEFECT_RE.search("\n".join(lines)) for blk, lines in blocks),
    })

defect = [r for r in recs if r["gate_defect_hits"] > 0]
whole_literal = [r for r in recs if r["wholefile_defect_literal_exact"] > 0 or r["wholefile_defect_literal_loose"] > 0]
noise = [r for r in whole_literal if not r["has_max_in_gate"]]
explicit_safe = [r for r in recs if r["has_expected_in_gate"] and not r["has_max_in_gate"]]
docmax_any = [r for r in recs if r["wholefile_defect_literal_exact"] > 0]

# 写域：优先 wd=root/'lead/xxx'，其次 const DIR
dom = collections.Counter()
for r in defect:
    d = (r["wds"][0].split("/")[-1] if r["wds"] else
         (r["const_DIR"].strip("/").split("/")[-1] if r["const_DIR"] else "?"))
    dom[d] += 1

# 校验 36 处是否都带 hashlib 导入、print 是否含 'problems':P,
def plain(c):
    return [{"key": list(k) if isinstance(k, tuple) else k, "value": v} for k, v in c.items()]

checks = {
    "gate_defect_files": len(defect),
    "gate_defect_total_hits": sum(r["gate_defect_hits"] for r in defect),
    "files_with_more_than_one_block": sum(1 for r in defect if r["gate_blocks"] > 1),
    "domains": len(dom),
    "domain_multiplicity": {k: v for k, v in sorted(dom.items()) if v > 1},
    "wholefile_literal_files": len(whole_literal),
    "noise_files": [r["file"] for r in noise],
    "noise_expected": {r["file"]: r["expected"] for r in noise},
    "explicit_safe_files": len(explicit_safe),
    "explicit_safe_in_defect": [r["file"] for r in explicit_safe if r in defect],
    "defect_first_line_has_hashlib": sum(1 for r in defect if r["gate_first_line"] and "hashlib" in r["gate_first_line"]),
    "defect_first_lines": plain(collections.Counter(r["gate_first_line"] for r in defect)),
    "defect_print_has_problemsP": sum(1 for r in defect if any("'problems':P," in ln for ln in r["gate_print_lines"])),
    "defect_print_line_shapes": len(set(tuple(r["gate_print_lines"]) for r in defect)),
    "defect_init_shapes": plain(collections.Counter(tuple(r["gate_init_lines"]) for r in defect)),
    "defect_segment_line_counts": plain(collections.Counter(len(r["segments"][0]["lines"]) if r["segments"] else -1 for r in defect)),
    "defect_segments_per_file": plain(collections.Counter(len(r["segments"]) for r in defect)),
    "parse_errors": parse_errors,
    "mjs_total": len(mjs), "all_files_total": len(all_files),
}
out = {"checks": checks, "domains": dict(sorted(dom.items())),
       "defect_files": [{"file": r["file"], "domain": (r["wds"][0].split("/")[-1] if r["wds"] else None),
                         "const_DOC": r["const_DOC"], "expected": r["expected"],
                         "first_line": r["gate_first_line"], "init": r["gate_init_lines"],
                         "print": r["gate_print_lines"], "segment": r["segments"][0]["lines"] if r["segments"] else None}
                        for r in defect],
       "noise_detail": [{"file": r["file"], "expected": r["expected"], "whole_literal_exact": r["wholefile_defect_literal_exact"]} for r in noise],
       "recs_brief": [{"file": r["file"], "gate_defect_hits": r["gate_defect_hits"],
                       "whole_literal_exact": r["wholefile_defect_literal_exact"],
                       "expected": r["expected"], "wds": r["wds"]} for r in recs]}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
print("DOMAIN_MULTI", json.dumps(checks["domain_multiplicity"], ensure_ascii=False))
print("NOISE", json.dumps(checks["noise_files"], ensure_ascii=False))
