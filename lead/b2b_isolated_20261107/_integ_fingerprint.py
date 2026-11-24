# -*- coding: utf-8 -*-
"""_integ_fingerprint.py — D-25 第 6 步隔离副本离线集成 · 指纹实算（hashlib，只读）。

同一脚本实跑两次：
  集成前 → _integ_fingerprint_pre.txt（此时隔离副本尚未创建，属正常）
  集成后 → _integ_fingerprint_post.txt（母本第 2 次实算，必须与第 1 次逐字节一致）
母本绑定记录：517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508 B
候选绑定记录：ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 / 412759 B
铁律：零真机、零采样代码；本脚本只读所有文件，自身落在唯一写域。
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
FILES = [
    ("母本", "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"),
    ("候选LF", "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"),
    ("候选diff", "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"),
    ("批准设计", "lead/b2b_design_20261106/B2B_DESIGN.md"),
    ("R3判定书", "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md"),
    ("隔离副本", "lead/b2b_isolated_20261107/qc151_trip.isolated.py"),
]
EXPECT_MOTHER = ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508)
EXPECT_CAND = ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759)

print("== _integ_fingerprint ==", "label:", sys.argv[1] if len(sys.argv) > 1 else "(no label)")
fps = {}
for name, rel in FILES:
    p = ROOT / rel
    if not p.is_file():
        print(f"{name}: MISSING {rel}")
        continue
    d = p.read_bytes()
    h = hashlib.sha256(d).hexdigest()
    fps[name] = (h, len(d))
    print(f"{name}: sha256={h} bytes={len(d)} LF={d.count(b'\n')} CR={d.count(b'\r')}")
    print(f"    path={p}")

ok = True
if fps.get("母本") != EXPECT_MOTHER:
    print(f"!! 母本漂移: {fps.get('母本')} expected {EXPECT_MOTHER}")
    ok = False
else:
    print("[PASS] 母本 == 绑定记录 517889c6.../399508")
if fps.get("候选LF") != EXPECT_CAND:
    print(f"!! 候选漂移: {fps.get('候选LF')} expected {EXPECT_CAND}")
    ok = False
else:
    print("[PASS] 候选 == 绑定记录 ca23c116.../412759")
if "隔离副本" in fps:
    if fps["隔离副本"] == fps["候选LF"]:
        print("[PASS] 隔离副本 == 候选（SHA256+字节数逐字节同一）")
    else:
        print(f"!! 隔离副本 != 候选: {fps['隔离副本']} vs {fps['候选LF']}")
        ok = False
else:
    print("（隔离副本尚未创建——pre 轮属预期）")
print("FINGERPRINT_RESULT =", "OK" if ok else "DRIFT")
sys.exit(0 if ok else 1)
