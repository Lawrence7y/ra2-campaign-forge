# -*- coding: utf-8 -*-
"""_owv_compare.py — 撰写人命中集 vs 复核员命中集 双向比对（只读，仅 stdout）。"""
import json

BASE = r"D:/Project/ra2-campaign-forge/lead/oldwording_sweep_20261109/"

their = json.loads(open(BASE + "_ow_raw_hits.json", "rb").read().decode("utf-8"))
mine = json.loads(open(BASE + "_owv_raw_hits.json", "rb").read().decode("utf-8"))

their_pos = {(h["file"], h["line"]) for h in their["hits"]}
their_self = {(h["file"], h["line"]) for h in their["hits"] if h["file"].startswith("oldwording_sweep_20261109/")}
mine_all = mine["hits"]
mine_pos = {(h["file"], h["line"]) for h in mine_all}
mine_self = {(h["file"], h["line"]) for h in mine_all if h["file"].startswith("oldwording_sweep_20261109/_owv_")}

# 我方有效集 = 全部命中 − 我自产脚本（_owv_*）；撰写人自产件（_ow_*）保留参与比对
mine_eff = mine_pos - mine_self
their_115 = their_pos - their_self

print("their raw =", len(their_pos), "| their self-domain =", len(their_self), "| their listed(=raw-self) =", len(their_115))
print("mine raw =", len(mine_pos), "| my _owv_ self =", len(mine_self), "| mine effective =", len(mine_eff))
print()
miss_theirs = sorted(their_115 - mine_pos)
print("A. 撰写人命中未落进我方扫描（应为 0）：", len(miss_theirs))
for f, l in miss_theirs[:20]:
    print("   MISS", f, l)
print()
extra = sorted(mine_eff - their_115)
print("B. 我方命中中撰写人没有的位置（候选新发现）：", len(extra))
for f, l in extra:
    h = next(x for x in mine_all if (x["file"], x["line"]) == (f, l))
    print(f"   EXTRA {f}:{l} [{','.join(h['pats'][:6])}] {h['text'][:150]}")
print()
print("C. 撰写人写域自产 8 处明细：")
for f, l in sorted(their_self):
    h = next(x for x in their["hits"] if (x["file"], x["line"]) == (f, l))
    print(f"   SELF {f}:{l} [{','.join(h['pats'][:4])}]")
