# -*- coding: utf-8 -*-
"""盘点 37 处位点对应的写域交付状态：声明主件是否存在、是否为域内最大 md。
只读；结果仅打印 stdout。"""
import json, os, re

ROOT = r"D:\Project\ra2-campaign-forge"
WFR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
SCAN_OUT = r"D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_rescan_out.json"

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

# 从第一步结果重建 37 行清单（重跑同样扫描，保证口径一致）
DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
CONST_DOC_RE = re.compile(r"const DOC\s*=\s*[\"']([^\"']+)[\"']")

sites = []
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    if not DEFECT_RE.search(text):
        continue
    payload = extract_payload(text)
    low = payload.get("lowered") if isinstance(payload, dict) else None
    wm = re.search(r"唯一写域\s*=\s*([^\n\\\"，。]+)", low)
    domain = wm.group(1).strip() if wm else None
    cd = CONST_DOC_RE.search(low)
    doc = cd.group(1).strip() if cd else None
    sites.append({"file": name, "domain": domain, "const_doc": doc})

# 逐域盘点
seen = {}
for s in sites:
    d = s["domain"]
    if d not in seen:
        seen[d] = {"domains": d, "main_declared": None, "runs": []}
    seen[d]["runs"].append(s["file"])
    if s["const_doc"]:
        if seen[d]["main_declared"] and seen[d]["main_declared"] != s["const_doc"]:
            seen[d]["main_declared"] += " || " + s["const_doc"]
        else:
            seen[d]["main_declared"] = s["const_doc"]

report = []
for d, v in sorted(seen.items()):
    dp = os.path.join(ROOT, d.replace("/", os.sep).rstrip(os.sep))
    mds = []
    if os.path.isdir(dp):
        for n in os.listdir(dp):
            fp = os.path.join(dp, n)
            if os.path.isfile(fp) and n.lower().endswith(".md"):
                mds.append((n, os.path.getsize(fp)))
    mds.sort(key=lambda x: -x[1])
    decl = v["main_declared"]
    decl_name = os.path.basename(decl) if decl else None
    main_exists = any(n == decl_name for n, _ in mds) if decl_name else False
    largest = mds[0][0] if mds else None
    main_is_largest = (decl_name == largest) if decl_name else None
    main_size = next((sz for n, sz in mds if n == decl_name), None) if decl_name else None
    report.append({
        "domain": d, "runs": len(v["runs"]), "declared_main": decl_name,
        "main_exists": main_exists, "md_count": len(mds),
        "main_bytes": main_size, "largest_md": largest,
        "largest_bytes": mds[0][1] if mds else None,
        "main_is_largest": main_is_largest,
        "top3_md": [(n, sz) for n, sz in mds[:3]],
    })

print(json.dumps({"domains": len(report), "report": report}, ensure_ascii=False, indent=1))
