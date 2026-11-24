# _hp_fp_nine.py —— 九件上游指纹独立实算（hashlib，只读）
# 用法: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c07_hardening_20261109/_hp_fp_nine.py
import hashlib, os

BASE = "D:/Project/ra2-campaign-forge/"
EXPECTED = {
    "lead/c07_protocol_attacks_20261109/PROTOCOL_ATTACK_TEST.md": "4488c8ed82c4ef7848eb85b367c6b2b2b0bab81e9f384afa581e0f44482cb743",
    "lead/c07_protocol_attacks_20261109/_pa_gate_runs.txt": "8c48e3db2000e4228d8b8f002ba451b2a88ec2778d5275591bc2f0f0f33f6300",
    "lead/c07_protocol_attacks_20261109/_pa_recon_out.txt": "a3bcee6537bb1aef522e24406c77e5984e6303a830a321f15b1a8b249bb0bcae",
    "lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md": "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547",
    "lead/c07_truth_protocol_20261109/_tp_TP_VERIFIER_CHECKLIST.md": "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7",
    "lead/c07_gate_fix_20261109/_f3_c7check.py": "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json": "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b",
    "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}

ok = 0
for rel, want in EXPECTED.items():
    p = os.path.join(BASE, rel.replace("/", os.sep))
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk); n += len(chunk)
    got = h.hexdigest()
    mark = "MATCH" if got == want and n == os.path.getsize(p) else "MISMATCH"
    if mark == "MATCH": ok += 1
    print(f"{mark} {rel} sha256={got} bytes={n}")
print(f"SUMMARY {ok}/{len(EXPECTED)} MATCH")
