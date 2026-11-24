# -*- coding: utf-8 -*-
"""独立重扫 .zcode/workflow-runs：找 DOC=max 挑大文件位点 + 每个受影响 payload 的
主件名线索（const DOC=）与写域。只读扫描；结果仅打印 stdout，不写任何文件。"""
import json, os, re, hashlib, sys

SCAN_DIR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"

DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
DOC_MAX_ANY_RE = re.compile(r"DOC\s*=\s*max\s*\(")
ST_SIZE_KEY_RE = re.compile(r"key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size")
CONST_DOC_RE = re.compile(r"const DOC\s*=\s*(.{0,90})")
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([^\n\\\"，。]+)")

def extract_payload(text):
    i = text.find("export const payload = ")
    if i < 0:
        return None
    j = i + len("export const payload = ")
    try:
        val, _ = json.JSONDecoder().raw_decode(text[j:])
        return val
    except Exception:
        return None

def in_allowed_dir(path):
    rp = os.path.realpath(path)
    return rp == SCAN_DIR or rp.startswith(SCAN_DIR + os.sep)

rows = []
n_files = 0
for name in sorted(os.listdir(SCAN_DIR)):
    p = os.path.join(SCAN_DIR, name)
    if not os.path.isfile(p) or not in_allowed_dir(p):
        continue
    n_files += 1
    raw = open(p, "rb").read()
    text = raw.decode("utf-8", errors="replace")
    hits = [text.count("\n", 0, m.start()) + 1 for m in DEFECT_RE.finditer(text)]
    if not hits:
        continue
    payload = extract_payload(text)
    lowered = payload.get("lowered") if isinstance(payload, dict) else None
    info = {"file": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "defect_lines": hits, "payload_parsed": payload is not None,
            "write_domain": None, "const_doc_occurrences": [],
            "defect_hits_in_lowered": 0}
    if lowered:
        wm = WRITE_DOMAIN_RE.search(lowered)
        info["write_domain"] = wm.group(1).strip() if wm else None
        info["const_doc_occurrences"] = [
            m.group(1).replace("\n", "|") for m in CONST_DOC_RE.finditer(lowered)]
        info["defect_hits_in_lowered"] = len(DEFECT_RE.findall(lowered))
    rows.append(info)

out = {"scanned_files": n_files, "files_with_defect": len(rows),
       "total_defect_hits": sum(len(r["defect_lines"]) for r in rows),
       "rows": rows}
print(json.dumps(out, ensure_ascii=False, indent=1))
