# -*- coding: utf-8 -*-
# _wlv_fingerprints.py — 独立复算：10 件基线指纹 + 被核对象报告指纹
# 仅用 hashlib，绝对路径，只读，不写任何只读域文件
import hashlib, os, json, sys

ROOT = "D:/Project/ra2-campaign-forge"

# 编排方基线（来自本任务 payload 的【编排方指纹】）
BASELINE = {
    "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
    "lead/gate_r9sem_20261109/_r9s_predicates.py": ("b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034", 23111),
    "lead/gate_r9sem_20261109/_r9s_DESIGN.md": ("5cae35256ec123687c6cbc47753ece3d417e0e33217005bdee0b1b47e322c95c", 37988),
    "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md": ("0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md": ("cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6", 27825),
    "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md": ("4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4", 18966),
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md": ("593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def sha_bytes(rel):
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

print("=== ① 10 件基线指纹独立复算（hashlib） ===")
all_ok = True
for rel, (exp_sha, exp_len) in BASELINE.items():
    sha, n = sha_bytes(rel)
    ok = (sha == exp_sha and n == exp_len)
    all_ok = all_ok and ok
    print(("OK  " if ok else "FAIL") + f" {rel}")
    print(f"     sha256={sha}  bytes={n}")
    if not ok:
        print(f"     EXPECT sha256={exp_sha}  bytes={exp_len}")
print("readonly_10_match_baseline =", all_ok)

print()
print("=== 被核对象：审查回件报告本体 ===")
for rel in [
    "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",
    "lead/whitelist_audit_20261109/_wl_step1_repro.py",
    "lead/whitelist_audit_20261109/_wl_step3_struct.py",
    "lead/whitelist_audit_20261109/_wl_step34.py",
    "lead/whitelist_audit_20261109/_wl_selfproof.py",
    "lead/whitelist_audit_20261109/_wl_selfproof_stdout.txt",
    "lead/whitelist_audit_20261109/_wl_step1_stdout.txt",
    "lead/whitelist_audit_20261109/_wl_step34_stdout.txt",
    "lead/whitelist_audit_20261109/_wl_step3_struct_stdout.txt",
]:
    sha, n = sha_bytes(rel)
    print(f"  {rel}\n     sha256={sha}  bytes={n}")

# 报告自称：52705 B / sha256=f9d00b7c...
sha, n = sha_bytes("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md")
print()
print("report_matches_payload_sha =", sha == "f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc")
print("report_matches_payload_bytes =", n == 52705)
