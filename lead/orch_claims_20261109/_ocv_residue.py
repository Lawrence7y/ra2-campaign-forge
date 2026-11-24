# -*- coding: utf-8 -*-
"""_ocv_residue.py - find delivered artifacts still carrying the WRONG numbers,
and verify internal consistency of the report's own counts. Read-only."""
import json, os, re, glob

R = "D:/Project/ra2-campaign-forge/lead/"
W = R + "orch_claims_20261109/"

# 1) wrong numbers still present in delivered artifacts (verbatim line hits)
targets = {
 "STALE_PASS_INVENTORY.md (3 行)": (R+"stale_pass_20261109/STALE_PASS_INVENTORY.md", ["只有 3 行", "台账 3 行"]),
 "GATE_REJUDGE_32.md (10域/5域)": (R+"gate_rejudge32_20261109/GATE_REJUDGE_32.md", ["10 域", "5 个", "五个", "十个"]),
 "GATE_N13_QUOTED_ASSERTION.md (四条问题)": (R+"gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md", ["四条问题"]),
 "MINHARD_SET_CHECK.md (4 件最小)": (R+"minhard_check_20261109/MINHARD_SET_CHECK.md", ["4 件最小", "「4 件"]),
 "_dn_glm_final.md (+5768B)": (R+"gate_doc_name_fix_20261109/_dn_glm_final.md", ["5768"]),
 "PENDING_DECISIONS.md (exit=0)": (R+"PENDING_DECISIONS.md", ["exit=0"]),
 "REFSYNC_SCOPE_FIX.md (SELF_TEST=PASS)": (R+"refsync_scope_20261109/REFSYNC_SCOPE_FIX.md", ["SELF_TEST = PASS"]),
}
res = {}
for name, (p, keys) in targets.items():
    lines = open(p, encoding="utf-8").read().splitlines()
    hits = {}
    for k in keys:
        hits[k] = [(i+1, lines[i][:220]) for i in range(len(lines)) if k in lines[i]]
    res[name] = {"path": p.replace(R, "lead/"), "hits": hits}
print("=== A. wrong-number residues in delivered artifacts ===")
print(json.dumps(res, ensure_ascii=False, indent=2))

# 2) archived publishArtifact description with wrong number
D = "D:/Project/ra2-campaign-forge/.zcode/workflow-runs/"
tb = {}
for p in sorted(glob.glob(D+"*.mjs")):
    src = open(p, encoding="utf-8").read()
    i = src.find("export const payload = ")
    if i < 0: continue
    try:
        pl, _ = json.JSONDecoder().raw_decode(src[i+len("export const payload = "):])
        low = pl.get("lowered", "")
    except Exception:
        continue
    for n, L in enumerate(low.splitlines(), 1):
        if "publishArtifact" in L or "description:" in L:
            if any(k in L for k in ("10 个", "十个", "5 个", "五个", "四条")):
                tb.setdefault(os.path.basename(p), []).append((n, L.strip()[:300]))
print("=== B. published artifact metadata carrying wrong numbers ===")
print(json.dumps(tb, ensure_ascii=False, indent=2))

# 3) report's own internal consistency: section 2(d) 'three' vs 4 numbered items
rep = open(W+"_oc_ORCH_CLAIMS_AUDIT.md", encoding="utf-8").read().splitlines()
sec = []
for i, L in enumerate(rep, 1):
    if 149 <= i <= 156 or 130 <= i <= 148:
        sec.append((i, L[:200]))
print("=== C. report lines 130-156 (section 2b/2c/2d) ===")
for i, L in sec: print(f"{i}: {L}")

# 4) DOC name expected by archived gate vs actual file
src = open(D+"dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs", encoding="utf-8").read()
i = src.find("export const payload = ")
pl, _ = json.JSONDecoder().raw_decode(src[i+len("export const payload = "):])
low = pl["lowered"].splitlines()
print("=== D. archived DOC / gate / prefix rule ===")
for n, L in enumerate(low, 1):
    if "const DOC" in L or "const DIR" in L or "按约定命名" in L or "_oc_ 前缀" in L or "全部 _oc_" in L:
        print(f"lowered:{n}: {L.strip()[:300]}")
print("actual files matching ORCH_CLAIMS_AUDIT:", [os.path.basename(x) for x in glob.glob(W+"*ORCH_CLAIMS_AUDIT*")])
