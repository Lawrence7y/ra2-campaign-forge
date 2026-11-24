# -*- coding: utf-8 -*-
# _fv_fingerprint.py — 复核员独立指纹实算（只读；本脚本落复核写域，前缀 _fv_）
import hashlib
import pathlib

BASE = pathlib.Path(r"D:/Project/ra2-campaign-forge")

# 编排方清单 10 件（期望值来自编排方指纹 JSON）
expected_orch = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": ("0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": ("7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),
    "lead/n11_protocol_spec_20261108/_ps_N11_MIN_OBS_PROTOCOL_SPEC.md": ("3d463483ad0d53d048a9cad9990b6c0e8b72485ef20eeaa8c519074ebdf94bda", 44300),
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": ("c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351),
    "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md": ("5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),
    "lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md": ("e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7", 28648),
    "lead/direction_ruling_20261108/RULING_DIRECTION.md": ("0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514),
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
}

# 撰写人自述产出 7 件（期望值来自回件 evidence 自报字节数）
expected_writer = {
    "lead/pending_factpack_20261108/_fp_N10-C02_Q1.md": 9026,
    "lead/pending_factpack_20261108/_fp_N10-C03_Q2.md": 7567,
    "lead/pending_factpack_20261108/_fp_N10-C06_Q5.md": 7571,
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md": 5756,
    "lead/pending_factpack_20261108/_fp_INDEX.md": 5802,
    "lead/pending_factpack_20261108/_fp_fingerprint_out.txt": 2409,
    "lead/pending_factpack_20261108/_fp_goal_slices_out.txt": 12654,
}

order = list(expected_orch.keys()) + list(expected_writer.keys())
for rel in order:
    p = BASE / rel
    try:
        data = p.read_bytes()
    except OSError as e:
        print(f"{rel}\tERROR\t{e}")
        continue
    h = hashlib.sha256(data).hexdigest()
    mark = ""
    if rel in expected_orch:
        e = expected_orch[rel]
        mark = "ORCH-MATCH" if (h == e[0] and len(data) == e[1]) else "ORCH-MISMATCH"
    elif rel in expected_writer:
        mark = "SIZE-MATCH" if len(data) == expected_writer[rel] else "SIZE-MISMATCH"
    print(f"{rel}|sha256={h}|bytes={len(data)}|{mark}")
