# -*- coding: utf-8 -*-
"""1) 全库安全实例重扫（宽正则：doc/DOC=root|wd/'...'，且无 DOC=max）；
2) 37 个 DOC=max run 的 mjs 启动时刻（mtime）；
3) ledger_appendix 主件时间线。只读；仅打印。"""
import json, os, re, datetime

WFR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
ROOT = r"D:\Project\ra2-campaign-forge"

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
# 宽口径安全实例：python 门禁内 显式 doc 赋值（大小写都收）
SAFE_RE = re.compile(r"\b(doc|DOC)\s*=\s*(root|wd)\s*/\s*'([^']+\.(?:md|MD))'")
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([^\n\\\"，。]+)")

def ts(mt):
    return datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M:%S")

print("### PART A: 安全实例重扫 ###")
gate_total = defect_total = 0
safe_rows = []
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    payload = extract_payload(text)
    low = payload.get("lowered") if isinstance(payload, dict) else None
    if not low or "GATE_CODE" not in low:
        continue
    gate_total += 1
    has_defect = bool(DEFECT_RE.search(low))
    safes = SAFE_RE.findall(low)
    if has_defect:
        defect_total += 1
        continue
    if safes:
        wm = WRITE_DOMAIN_RE.search(low)
        names = sorted(set(m[2] for m in safes))
        safe_rows.append((name, wm.group(1).strip() if wm else "?", names))
print("gate-bearing =", gate_total, " with-DOC=max =", defect_total,
      " safe-explicit =", len(safe_rows))
for r in safe_rows:
    print("  SAFE", r[0], r[1], r[2])

print()
print("### PART B: 37 个 DOC=max run 启动时刻 ###")
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    if not DEFECT_RE.search(text):
        continue
    payload = extract_payload(text)
    low = payload.get("lowered") if isinstance(payload, dict) else ""
    wm = WRITE_DOMAIN_RE.search(low or "")
    dom = wm.group(1).strip() if wm else "?"
    print(" ", ts(os.path.getmtime(p)), name[:24], dom)

print()
print("### PART C: ledger_appendix / direction_ruling / d13d14 主件时间线 ###")
CHECKS = [
    r"lead\ledger_appendix_20261108\LEDGER_APPENDIX_DRAFT.md",
    r"lead\ledger_appendix_20261108\_lad_tpl.md",
    r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
    r"lead\direction_ruling_20261108\_dr_RULING.md",
    r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",
    r"lead\d13d14_cards_20261108\_n10_D13D14_CARDS_20261108.md",
]
for rel in CHECKS:
    fp = os.path.join(ROOT, rel)
    if os.path.isfile(fp):
        print(" ", ts(os.path.getmtime(fp)), os.path.getsize(fp), rel)
    else:
        print("  MISSING", rel)
