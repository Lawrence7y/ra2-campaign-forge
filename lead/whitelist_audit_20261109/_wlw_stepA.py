import json, pathlib, re, hashlib, sys
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
MJS = ROOT / ".zcode" / "workflow-runs"

# 1) ten orchestrator fingerprints, independently re-computed with hashlib
T = [
    'lead/gate_r9sem_20261109/_r9s_regress_out.json',
    'lead/gate_r9sem_20261109/_r9s_predicates.py',
    'lead/gate_r9sem_20261109/_r9s_DESIGN.md',
    'lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md',
    'lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md',
    'lead/n11_wording_fix_20261108/N11_WORDING_FIX.md',
    'lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md',
    'lead/gate_fp7_20261108/_g7_predicates.py',
    'lead/PENDING_DECISIONS.md',
    'lead/GOAL_THREE_TARGETS_20261018.md',
]
EXPECT = {
 'lead/gate_r9sem_20261109/_r9s_regress_out.json': ('5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25', 75673),
 'lead/gate_r9sem_20261109/_r9s_predicates.py': ('b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034', 23111),
 'lead/gate_r9sem_20261109/_r9s_DESIGN.md': ('5cae35256ec123687c6cbc47753ece3d417e0e33217005bdee0b1b47e322c95c', 37988),
 'lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md': ('0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31', 36851),
 'lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md': ('cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6', 27825),
 'lead/n11_wording_fix_20261108/N11_WORDING_FIX.md': ('4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4', 18966),
 'lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md': ('593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740', 20271),
 'lead/gate_fp7_20261108/_g7_predicates.py': ('02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120', 11743),
 'lead/PENDING_DECISIONS.md': ('3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
 'lead/GOAL_THREE_TARGETS_20261018.md': ('2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
}
print("=== _wlw_stepA: 10 fingerprints (hashlib, live read) ===")
ok = True
for rel in T:
    p = ROOT / rel
    if not p.is_file():
        print("MISSING", rel); ok = False; continue
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest(); n = len(b)
    eh, en = EXPECT[rel]
    good = (h == eh and n == en)
    ok = ok and good
    print(("OK  " if good else "FAIL") + "  %-62s %s / %d" % (rel, h, n))
print("readonly_10_unchanged =", ok)

# 2) verbatim task-book requirement strings, from payload files
print("\n=== _wlw_stepA: task-book verbatim requirement lines ===")
FILES = {
 'A_ruling': 'dwfrun-db5bad08-1aa0-4dea-940f-5f66a8b27a06.mjs',
 'B_reach': 'dwfrun-c482b235-41c5-431b-b9d9-2617c362b1cc.mjs',
 'C_n11': 'dwfrun-903e6b21-eb50-4c2f-a8dd-da3851198786.mjs',
 'D_s604': 'dwfrun-bc9d8b8e-9faa-4226-8022-ccd881335683.mjs',
 'E_r9sem': 'dwfrun-8156bb52-3202-457d-bbde-6774ee112fb8.mjs',
 'F_this': 'dwfrun-5e636329-c206-4e6d-b615-3e9a0255218d.mjs',
}
KEYS = ['需谁批准', '实跑输出', '改前改后', '脚本存在', '可重建', '语义在场', 'WHITELIST_AUDIT', '第五步', '第二步', '六节', '必现要素']
for tag, fn in FILES.items():
    p = MJS / fn
    if not p.is_file():
        print(tag, "MISSING", fn); continue
    t = p.read_text(encoding='utf-8', errors='replace')
    print("\n--- %s : %s (bytes=%d sha256=%s) ---" % (tag, fn, len(t.encode('utf-8')), hashlib.sha256(t.encode('utf-8')).hexdigest()))
    lines = t.splitlines()
    hits = []
    for i, L in enumerate(lines, 1):
        if any(k in L for k in KEYS):
            hits.append(i)
    # print line numbers and full line text, but truncate each at 1200 chars
    for i in hits:
        L = lines[i-1]
        print("  :%-4d %s" % (i, L[:1200]))
print("\nDONE")
