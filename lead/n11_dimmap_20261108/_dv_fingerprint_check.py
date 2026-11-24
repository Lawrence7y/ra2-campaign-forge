# -*- coding: utf-8 -*-
"""独立复核：六件指纹实算（hashlib），与编排方指纹逐件比对。只读。"""
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge\lead"
FILES = [
    (r"n11_protocol_spec_20261108\OBSERVATION_PROTOCOL_SPEC.md",
     "c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351, 441),
    (r"n11_protocol_spec_20261108\_ps_N11_MIN_OBS_PROTOCOL_SPEC.md",
     "3d463483ad0d53d048a9cad9990b6c0e8b72485ef20eeaa8c519074ebdf94bda", 44300, 370),
    (r"perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",
     "7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619, 192),
    (r"direction_ruling_20261108\RULING_DIRECTION.md",
     "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514, 97),
    (r"nextstep_plan_20261106\NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225, 136),
    (r"PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, 382),
    (r"GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, 9758),
]

for rel, exp_sha, exp_bytes, exp_lines in FILES:
    p = os.path.join(BASE, rel)
    data = open(p, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    lines = data.decode("utf-8").count("\n") + (0 if data.endswith(b"\n") else 1)
    ok_sha = "MATCH" if sha == exp_sha else "MISMATCH"
    ok_b = "MATCH" if len(data) == exp_bytes else "MISMATCH"
    ok_l = "MATCH" if lines == exp_lines else "MISMATCH"
    print(f"{rel}")
    print(f"  sha256={sha}  [{ok_sha}]")
    print(f"  bytes={len(data)} (expect {exp_bytes}) [{ok_b}]  lines={lines} (expect {exp_lines}) [{ok_l}]")
