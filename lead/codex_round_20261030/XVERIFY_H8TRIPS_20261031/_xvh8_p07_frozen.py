#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p07：三份冻结件哈希清单逐行复验（§485 批后 / §486 C-0 v2 / §487 批后六件）。
只读；对每个清单的每行 现算 sha256 vs 清单值。
"""
import hashlib, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
LISTS = ["lead/codex_round_20261030/C_BATCH2C_H14_20261031/frozen_recheck_batch2c_post.txt",
         "lead/codex_round_20261030/LEADER_battle/frozen_recheck_h8_v2.txt",
         "lead/codex_round_20261030/LEADER_battle/frozen_recheck_h8_post.txt",
         "lead/codex_round_20261030/LEADER_battle/frozen_recheck_h8_pre.txt"]
BS = chr(92)
for lst in LISTS:
    print("=" * 78)
    print(lst)
    for ln in open(lst, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        h, p = ln.split(" *")
        q = p.replace(BS, "/")
        if not os.path.isfile(q):
            print("  MISSING %s" % p)
            continue
        now = hashlib.sha256(open(q, "rb").read()).hexdigest()
        print("  %s %s" % ("MATCH " if now == h else "DIFF   ", p))
