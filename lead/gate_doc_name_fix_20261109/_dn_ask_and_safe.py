# -*- coding: utf-8 -*-
"""三件事：1) ledger_appendix 三个 run 的任务书交付指示（找主件名）；
2) 全 217 个 payload 找「已用显式命名」的安全门禁实例；
3) 受害域全部 run 历史。只读；仅打印。"""
import json, os, re

WFR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"

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

DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([^\n\\\"，。]+)")

VICTIMS = ["counterpart_fix_20261109", "d13d14_cards_20261108",
           "direction_ruling_20261108", "handoff_pack_20261109",
           "s604_script_hunt_20261109", "n4_yi_final_20261108",
           "ledger_appendix_20261108"]

print("### PART 1: ledger_appendix 交付指示 ###")
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    if "ledger_appendix_20261108" not in text or "唯一写域" not in text:
        continue
    payload = extract_payload(text)
    if not isinstance(payload, dict):
        continue
    low = payload.get("lowered") or ""
    if "唯一写域 = lead/ledger_appendix_20261108" not in low:
        continue
    k = low.find("【交付】")
    frag = low[k:k+260].replace("\n", " | ") if k >= 0 else "(no 交付 tag)"
    md_names = sorted(set(re.findall(r"([A-Z0-9_]{6,}\.md)", low)))
    print("--", name, "defect=", bool(DEFECT_RE.search(text)))
    print("   交付:", frag[:240])
    print("   md-like names:", md_names[:8])

print()
print("### PART 2: 安全实例（门禁显式命名） ###")
safe, gate_runs = [], 0
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    if "GATE_CODE" not in text and "gate" not in text.lower():
        continue
    payload = extract_payload(text)
    if not isinstance(payload, dict):
        continue
    low = payload.get("lowered") or ""
    if "GATE_CODE" not in low:
        continue
    gate_runs += 1
    has_defect = bool(DEFECT_RE.search(low))
    # 显式命名特征：门禁 python 里 DOC= 指向具体路径
    explicit = re.findall(r"DOC=(?:root|wd)/'[A-Za-z0-9_/.-]+'", low)
    doc_is_file = re.findall(r"DOC=wd/'([^']+)'", low)
    if explicit and not has_defect:
        wm = WRITE_DOMAIN_RE.search(low)
        safe.append({"file": name, "domain": wm.group(1).strip() if wm else None,
                     "explicit_forms": explicit[:3]})
print("gate-bearing payloads =", gate_runs, " safe explicit instances =", len(safe))
for s in safe:
    print("  SAFE:", s["file"], s["domain"], s["explicit_forms"])

print()
print("### PART 3: 受害域 run 历史 ###")
for v in VICTIMS:
    runs = []
    for name in sorted(os.listdir(WFR)):
        p = os.path.join(WFR, name)
        if not os.path.isfile(p):
            continue
        text = open(p, "r", encoding="utf-8", errors="replace").read()
        if v not in text:
            continue
        payload = extract_payload(text)
        low = payload.get("lowered") if isinstance(payload, dict) else ""
        low = low or ""
        if ("唯一写域 = lead/" + v) not in low:
            continue
        runs.append((name, "DOC=max缺陷" if DEFECT_RE.search(text) else "无DOC=max",
                     "有const DOC" if re.search(r"const DOC\s*=\s*[\"']", low) else "无const DOC"))
    print(v, "->", runs)
