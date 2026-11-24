# -*- coding: utf-8 -*-
"""_slw_hashes.py — 联查报告撰写员守卫：本会话 hashlib 实算，stdout 输出，不写任何文件。
对比基线：编排方指纹 8 件 + 写域实现交付件 5 件 + F2D_ROOT_CAUSE.md:48 证据五件记录 + 锚对象现算。
"""
import hashlib
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"

def fp(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n

def cmp(tag, rel, want_sha, want_bytes=None):
    try:
        sha, n = fp(rel)
    except OSError as e:
        print(f"[{tag}] {rel} -> READ_FAIL {e}")
        return
    ok_sha = (sha == want_sha)
    ok_b = True if want_bytes is None else (n == want_bytes)
    verdict = "MATCH" if (ok_sha and ok_b) else "MISMATCH"
    print(f"[{tag}] {verdict} {rel}")
    print(f"        sha256 = {sha}")
    print(f"        bytes  = {n}  (want sha={want_sha[:12]}… bytes={want_bytes})")

UPSTREAM = [
    ("U1", "lead/gate_fp7_20261108/_g7_predicates.py",
     "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("U2", "lead/r11_f2_fix_20261109/_f2_r11plus.py",
     "83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    ("U3", "lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md",
     "d789c9f64d1c0586075bec3d62b2a544e2adf4ed3282bf391a21e3f9218fa0f1", 32939),
    ("U4", "lead/f2d_rootcause_20261109/_f2d_ROOTCAUSE.md",
     "d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05", 21424),
    ("U5", "lead/r11_f2_fix_20261109/_f2_repro_out.json",
     "3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72", 28386),
    ("U6", "lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md",
     "dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578),
    ("U7", "lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("U8", "lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

DELIVER = [
    ("D1", "lead/samedoc_link_20261109/_sl_link.py",
     "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", 12475),
    ("D2", "lead/samedoc_link_20261109/_sl_run10.py",
     "666ef44fafc70ee287a06cd70b1c0345eb4eb047ab2bd350afa75d9779ca736b", None),
    ("D3", "lead/samedoc_link_20261109/_sl_run10_out.json",
     "ed031e01e90e004dab43552085f5f6e5b5d184e7d1efa6f5699d6f76b5da454c", 36749),
    ("D4", "lead/samedoc_link_20261109/_sl_selftest.py",
     "adf95027569fadfd7c09e7aecbb998ebe59485b94b1ee5dc5ff5dc2980aedf93", 8294),
    ("D5", "lead/samedoc_link_20261109/_sl_selftest_out.json",
     "4ee4996ce89b966d625eed5eab18d8a1ef37286284102be841b6f389b0094465", 1905),
]

# F2D_ROOT_CAUSE.md:48 所记证据五件（实现报告照录值）
EVIDENCE = [
    ("E1", "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
     "1209ca4c", 33431, None),
    ("E2", "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
     "65463431", 24022, None),
    ("E3", "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md",
     "9742f2cc", 15179, None),
    ("E4", "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",
     "be733335", 32183, None),
    ("E5", "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md",
     "cb4f3011", 22136, None),
]

def evidence(tag, rel, prefix, want_bytes, _):
    sha, n = fp(rel)
    verdict = "MATCH" if (sha.startswith(prefix) and n == want_bytes) else "MISMATCH"
    print(f"[{tag}] {verdict} {rel}")
    print(f"        sha256 = {sha}")
    print(f"        bytes  = {n}  (want prefix={prefix}… bytes={want_bytes})")

# 锚对象现算（联查回验的独立重放）
ANCHORS = [
    ("A条1", "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md"),
    ("A条2", "lead/b2b_isolated_20261107/qc151_trip.isolated.py"),
    ("A条3a", "lead/b2b_isolated_20261107/qc151_trip.isolated.py"),
    ("A条3b", "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"),
    ("A条4", "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"),
    ("A条5", "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"),
    ("A条6", "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md"),
]

def anchors(tag, rel, *a):
    sha, n = fp(rel)
    print(f"[{tag}] {rel}")
    print(f"        sha256 = {sha}")
    print(f"        bytes  = {n}")

def main():
    print("== 上游八件（编排方指纹基线）==")
    for tag, rel, sha, b in UPSTREAM:
        cmp(tag, rel, sha, b)
    print("== 写域实现交付件五件 ==")
    for tag, rel, sha, b in DELIVER:
        cmp(tag, rel, sha, b)
    print("== 证据五件（F2D_ROOT_CAUSE.md:48 记录口径）==")
    for tag, rel, prefix, b, _ in EVIDENCE:
        evidence(tag, rel, prefix, b, _)
    print("== 锚对象现算（独立重放）==")
    for tag, rel in ANCHORS:
        anchors(tag, rel, None)
    # 条3 双文件逐字节比较
    p1 = os.path.join(ROOT, "lead", "b2b_isolated_20261107", "qc151_trip.isolated.py")
    p2 = os.path.join(ROOT, "lead", "b2b_candidate_lf_20261107", "qc151_trip.candidate_lf.py")
    same = open(p1, "rb").read() == open(p2, "rb").read()
    print(f"[条3逐字节] qc151_trip.isolated.py == qc151_trip.candidate_lf.py -> {same}")
    print("DONE")

if __name__ == "__main__":
    sys.exit(main())
