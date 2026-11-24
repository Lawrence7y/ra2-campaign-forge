# -*- coding: utf-8 -*-
"""N-11 交付签出指纹核验（正式落位轮·撰写员）。纯 hashlib 只读；无采样、无注入、无动态解析、无网络、无写入。

用法：python -I -X utf8 _deliver_hash_check.py [附加文件路径 ...]
  无附加参数 = 核上游四件 + 前置草稿 _n11_PERF_REPAIR_HANDOFF.md（带任务书/回执预期值比对）；
  带附加参数 = 额外实算附加文件指纹（无预期值，用于本交付件 PERF_REPAIR_HANDOFF.md 落盘后登记）。"""
import hashlib
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge"

EXPECTED = [
    (BASE + r"\lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    (BASE + r"\lead\slowwindow_n8_20261108\SLOW_WINDOW_LIMITS.md",
     "e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60", 23707),
    (BASE + r"\lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",
     "5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),
    (BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    (BASE + r"\lead\perf_repair_n11_20261108\_n11_PERF_REPAIR_HANDOFF.md",
     "cf73fd80edbc538cd7fa5f2f6b69a759f8c00eeac903153146d533dd74a73269", 22745),
]


def digest(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


lines = []
all_match = True
for path, exp_sha, exp_n in EXPECTED:
    sha, n = digest(path)
    ok = (sha == exp_sha) and (n == exp_n)
    all_match = all_match and ok
    lines.append("被核对象 SHA256 = %s，字节数 = %d（%s）预期 %s…/%d B -> %s"
                 % (sha, n, os.path.relpath(path, BASE), exp_sha[:8], exp_n,
                    "MATCH" if ok else "MISMATCH"))
lines.append("ALL_MATCH = %s" % all_match)
for extra in sys.argv[1:]:
    if os.path.isfile(extra):
        sha, n = digest(extra)
        lines.append("交付件 SHA256 = %s，字节数 = %d（%s）"
                     % (sha, n, os.path.relpath(extra, BASE)))
    else:
        lines.append("交付件缺失 = %s" % extra)
sys.stdout.write("\n".join(lines) + "\n")
