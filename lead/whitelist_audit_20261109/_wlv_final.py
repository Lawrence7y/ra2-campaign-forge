# -*- coding: utf-8 -*-
# _wlv_final.py — 收尾：10 件只读指纹复算 + 报告本体 + 越界检查 + 297 溯源
import hashlib, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
BASE = {
 "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25",75673),
 "lead/gate_r9sem_20261109/_r9s_predicates.py": ("b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034",23111),
 "lead/gate_r9sem_20261109/_r9s_DESIGN.md": ("5cae35256ec123687c6cbc47753ece3d417e0e33217005bdee0b1b47e322c95c",37988),
 "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md": ("0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31",36851),
 "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md": ("cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6",27825),
 "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md": ("4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4",18966),
 "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md": ("593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740",20271),
 "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",11743),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",759518),
}
print("=== 收尾：10 件只读指纹复算 ===")
ok = True
for rel,(exp_sha,exp_n) in BASE.items():
    b = (ROOT/rel).read_bytes()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    good = (sha==exp_sha and n==exp_n)
    ok &= good
    print(("OK  " if good else "FAIL") + f" {rel}  {sha[:12]}…/{n}")
print("readonly_10_unchanged =", ok)
doc = (ROOT/"lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md").read_bytes()
print("报告本体 sha256 =", hashlib.sha256(doc).hexdigest(), " bytes =", len(doc))
print("报告本体 == payload 声明 =", hashlib.sha256(doc).hexdigest()=="f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc" and len(doc)==52705)

print("\n=== 297 溯源：上一轮 GATE_R9_SEMANTIC_ELEMENT.md 中 297 出现处 ===")
t = (ROOT/"lead/gate_r9sem_20261109/GATE_R9_SEMANTIC_ELEMENT.md").read_text(encoding="utf-8")
for i,l in enumerate(t.split("\n"),1):
    if "297" in l:
        print(f"  :{i} {l.strip()[:200]}")
print("\n=== 报告 _WL_WHITELIST_AUDIT.md 中 297 出现处 ===")
d = doc.decode("utf-8")
for i,l in enumerate(d.split("\n"),1):
    if "297" in l:
        print(f"  :{i} {l.strip()[:200]}")

print("\n=== 我独立实算的已登记/未登记项数（来自 _wlv_regress_out.json）===")
import json
my = json.loads((ROOT/"lead/whitelist_audit_20261109/_wlv_regress_out.json").read_text(encoding="utf-8"))
print(f"  n_items={my['n_items']}  registered_occurrences={my['registered_occurrences']}  "
      f"unregistered_items={my['n_items']-my['registered_occurrences']}")

print("\n=== 报告 §2②(b) 任务书引文 vs 我实读 dwfrun-c482b235 payload ===")
import json as J
p = ROOT/".zcode/workflow-runs/dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs"
txt = p.read_text(encoding="utf-8",errors="replace")
k = txt.find("export const payload = ")
low,_ = J.JSONDecoder().raw_decode(txt[k+len("export const payload = "):])
s = low["lowered"]
i = s.find("要给出")
print("  任务书原文:", repr(s[i:i+95]))
for j,l in enumerate(d.split("\n"),1):
    if "要给出" in l and "实跑" in l:
        print(f"  报告 :{j}: {l.strip()[:220]}")
