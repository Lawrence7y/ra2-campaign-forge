# -*- coding: utf-8 -*-
"""_owv_filter.py — 差集聚焦过滤（只读，仅 stdout）。"""
import json, os

BASE = r"D:/Project/ra2-campaign-forge/lead/oldwording_sweep_20261109/"
LEAD = r"D:/Project/ra2-campaign-forge/lead"

their = json.loads(open(BASE + "_ow_raw_hits.json", "rb").read().decode("utf-8"))
mine = json.loads(open(BASE + "_owv_raw_hits.json", "rb").read().decode("utf-8"))

their_pos = {(h["file"], h["line"]) for h in their["hits"] if not h["file"].startswith("oldwording_sweep_20261109/")}
mine_all = [h for h in mine["hits"] if not h["file"].startswith("oldwording_sweep_20261109/_owv_")]
mine_pos = {(h["file"], h["line"]) for h in mine_all}
extra = [h for h in mine_all if (h["file"], h["line"]) not in their_pos]

SPECIFIC = {"持续性根因", "同一持久根因", "一因双时点", "句柄占用", "ACL损坏", "ACL 损坏",
            "根因横跨", "横跨时点", "跨两时点", "源读面", "部分同源", "造成两半", "两半",
            "同一持续根因", "同根因双时点"}
W2_DIRS = ("matrix_reach_20261109/", "w2_samecause_20261109/", "handoff_pack_20261109/",
           "text_fix_unified_20261109/", "strict_exposure_20261109/", "o1prime_reach_20261109/",
           "matrix_row5_20261109/", "matrix_ab_ruling_20261109/")

print("== D1. 差集中含特异性模式的命中（含 W2 族任意差集）==")
for h in extra:
    if (set(h["pats"]) & SPECIFIC) or h["file"].startswith(W2_DIRS):
        print(f"  {h['file']}:{h['line']} [{','.join(h['pats'])}]")
        print("    > " + h["text"][:220])

print()
print("== D2. 深度>=6 的文件清单（父目录深度>=6）及其命中 ==")
deep_files = {}
for dirpath, dirnames, filenames in os.walk(LEAD):
    rel = os.path.relpath(dirpath, LEAD)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    dirnames[:] = [d for d in dirnames if d not in {".git"}]
    if depth >= 12:
        dirnames[:] = []
    if depth >= 6:
        for fn in filenames:
            relf = (dirpath + os.sep + fn)[len(LEAD) + 1:].replace("\\", "/")
            deep_files[relf] = depth
byext = {}
for f in deep_files:
    e = os.path.splitext(f)[1].lower()
    byext[e] = byext.get(e, 0) + 1
print("  深度>=6 文件数 =", len(deep_files), " 按扩展名 =", dict(sorted(byext.items(), key=lambda x: -x[1])))
deep_hits = [h for h in mine_all if h["file"] in deep_files]
print("  深度>=6 命中数 =", len(deep_hits))
for h in deep_hits:
    print(f"    DEEP {h['file']}:{h['line']} [{','.join(h['pats'])}] {h['text'][:150]}")

print()
print("== D3. 非文本扩展名命中（.dwf.ts/.mimosa 快照族，撰写人报 12 处）==")
nt = [h for h in mine_all if h["file"].endswith(".dwf.ts") or "/.mimosa/" in h["file"] or h["file"].startswith(".mimosa/")]
same_root = [h for h in nt if "同一根因" in h["pats"] or "同根因" in h["pats"]]
other_nt = [h for h in nt if h not in same_root]
print("  .dwf.ts/.mimosa 族命中总数 =", len(nt), "；其中 同一根因/同根因 =", len(same_root), "；其他模式 =", len(other_nt))
for h in other_nt[:30]:
    print(f"    NT-OTHER {h['file']}:{h['line']} [{','.join(h['pats'])}] {h['text'][:120]}")

print()
print("== D4. 提问方点名三词在我方全扫中的分布（排除撰写人写域与 _owv_ 自产）==")
for w in ("显然可达", "必然同源", "会虚报", "必然可达"):
    ws = [h for h in mine_all if w in h["pats"]]
    print(f"  {w}: {len(ws)} 处")
    for h in ws:
        print(f"    {h['file']}:{h['line']} [{','.join(h['pats'])}] {h['text'][:120]}")
