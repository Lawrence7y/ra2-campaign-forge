# -*- coding: utf-8 -*-
"""1) 79 个门禁 payload 中非 DOC=max 非显式的 8 个「其他形态」；
2) 33 域竞争窗口扫描：是否存在 size>主件 且 mtime<主件 的侧件 md。
只读；仅打印。"""
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
SAFE_RE = re.compile(r"\b(doc|DOC)\s*=\s*(root|wd)\s*/\s*'([^']+\.(?:md|MD))'")
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([^\n\\\"，。]+)")

print("### PART A: 其他形态门禁（非缺陷非显式） ###")
for name in sorted(os.listdir(WFR)):
    p = os.path.join(WFR, name)
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8", errors="replace").read()
    payload = extract_payload(text)
    low = payload.get("lowered") if isinstance(payload, dict) else None
    if not low or "GATE_CODE" not in low:
        continue
    if DEFECT_RE.search(low) or SAFE_RE.search(low):
        continue
    wm = WRITE_DOMAIN_RE.search(low)
    k = low.find("GATE_CODE")
    seg = low[k:k+700].replace("\n", " ⏎ ")
    print("--", name, (wm.group(1).strip() if wm else "?"))
    print("   ", seg[:560])
    print()

print("### PART B: 33 域竞争窗口（侧件更大且早于主件） ###")
DOMAINS = {
 "lead/c07_gate_audit_20261109/": "C07_SELFCHECK_AUDIT.md",
 "lead/c07_gate_fix_20261109/": "C07_GATE_G1_G5_FIX.md",
 "lead/c07_protocol_attacks_20261109/": "PROTOCOL_ATTACK_TEST.md",
 "lead/c07_slot_20261109/": "C07_IDENTITY_SLOT.md",
 "lead/c07_truth_protocol_20261109/": "C07_TRUTH_SELF_PROOF.md",
 "lead/counterpart_fix_20261109/": "COUNTERPART_FIX.md",
 "lead/f2d_rootcause_20261109/": "F2D_ROOT_CAUSE.md",
 "lead/gate_fp7_20261108/": "GATE_FALSE_POSITIVE_5_6_7.md",
 "lead/gate_postmortem_20261109/": "GATE_LITERAL_MATCH_POSTMORTEM.md",
 "lead/gate_r9r12_20261109/": "GATE_R9R12_REGRESSION.md",
 "lead/handoff_pack_20261109/": "APPROVAL_PACK.md",
 "lead/ledger_appendix_20261108/": "LEDGER_APPENDIX_DRAFT.md",
 "lead/matrix_ab_ruling_20261109/": "RULING_MATRIX_AB.md",
 "lead/matrix_reach_20261109/": "MATRIX_DEFECT_REACHABILITY.md",
 "lead/matrix_row5_20261109/": "MATRIX_ROW5_COUPLING.md",
 "lead/n10c04_ruling_20261108/": "RULING_STATIC_ORDER.md",
 "lead/n11_dimmap_20261108/": "DIM_COLUMN_MAPPING.md",
 "lead/n11_wording_fix_20261108/": "N11_WORDING_FIX.md",
 "lead/n4_yi_final_20261108/": "CANDIDATE_RESIGN_YES_V2.md",
 "lead/o1prime_reach_20261109/": "O1PRIME_REACHABILITY.md",
 "lead/pending_factpack_20261108/": "PENDING_FACTPACK_C02_C03_C06_C07.md",
 "lead/r11_f2_fix_20261109/": "R11_F2_COVERAGE_FIX.md",
 "lead/s604_attribution_20261108/": "S604_ATTRIBUTION.md",
 "lead/s604_exclusive_20261109/": "S604_EXCLUSIVITY.md",
 "lead/s604_script_gap_20261109/": "S604_SCRIPT_GAP.md",
 "lead/s604_script_hunt_20261109/": "S604_SCRIPT_HUNT.md",
 "lead/samedoc_link_20261109/": "SAMEDOC_LINK.md",
 "lead/strict_exposure_20261109/": "STRICT_EXPOSURE.md",
 "lead/text_fix_unified_20261109/": "UNIFIED_TEXT_FIX.md",
 "lead/u5u6_mirror_20261109/": "U5U6_MIRROR_TEXTS.md",
 "lead/v2_precision_fix_20261108/": "V2_PRECISION_FIX_PROPOSAL.md",
 "lead/w2_samecause_20261109/": "W2_SAME_CAUSE.md",
}
def ts(mt):
    return datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M:%S")
for dom, main in sorted(DOMAINS.items()):
    dp = os.path.join(ROOT, dom.replace("/", os.sep).rstrip(os.sep))
    mp = os.path.join(dp, main)
    if not os.path.isfile(mp):
        print(" %s 主件缺失 %s" % (dom, main))
        continue
    mt_main, sz_main = os.path.getmtime(mp), os.path.getsize(mp)
    races = []
    for n in os.listdir(dp):
        fp = os.path.join(dp, n)
        if not os.path.isfile(fp) or not n.lower().endswith(".md") or n == main:
            continue
        sz = os.path.getsize(fp)
        mt = os.path.getmtime(fp)
        if sz > sz_main and mt < mt_main:
            races.append((n, sz, ts(mt)))
    flag = "RACE" if races else "ok  "
    print(" %s %s main=%dB(%s)%s" % (flag, dom, sz_main, ts(mt_main),
          ("  racers=" + str(races)) if races else ""))
