# -*- coding: utf-8 -*-
"""_owv_xcheck.py — ④内部矛盾清点 + ⑤完备性抽查 + ⑥越界检查（只读，仅 stdout）。"""
import json, os, time, subprocess

BASE = r"D:/Project/ra2-campaign-forge/lead/oldwording_sweep_20261109/"
LEAD = r"D:/Project/ra2-campaign-forge/lead"

mine = json.loads(open(BASE + "_owv_raw_hits.json", "rb").read().decode("utf-8"))
hits = [h for h in mine["hits"] if not h["file"].startswith("oldwording_sweep_20261109/_owv_")]

print("== X1. 内部矛盾清点：新措辞(源读面/部分同源)按文件分布，与旧措辞文件求交 ==")
newword_files = {}
for h in hits:
    if "源读面" in h["pats"] or "部分同源" in h["pats"]:
        newword_files.setdefault(h["file"], []).append(h["line"])
oldword_files = {}
for h in hits:
    OLD = {"同一持续根因", "持续根因", "AV 瞬时锁", "句柄/ACL", "句柄被占", "横跨两时点",
           "横跨 pre", "横跨 post", "同根因", "同一根因", "路径异常"}
    if set(h["pats"]) & OLD:
        oldword_files.setdefault(h["file"], []).append(h["line"])
print("  含新措辞文件（live 树）:")
for f in sorted(newword_files):
    print("   ", f, "->", newword_files[f])
print("  旧措辞∧新措辞 同文件交集:")
for f in sorted(set(newword_files) & set(oldword_files)):
    print("   BOTH", f, "旧@", oldword_files[f][:8], "新@", newword_files[f][:8])
print("  纯旧无新（自相矛盾风险件）:", sorted(set(oldword_files) - set(newword_files)))
for f in ("matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", "matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md"):
    print(f"  {f}: 源读面命中 = {len(newword_files.get(f, []))}")

print()
print("== X2. 九件绑定件中四件「撰写人称 0 命中」件在我方 44 模式下的命中 ==")
for f in ("o1prime_reach_20261109/O1PRIME_REACHABILITY.md",
          "matrix_row5_20261109/MATRIX_ROW5_COUPLING.md",
          "matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
          "PENDING_DECISIONS.md"):
    fh = [h for h in hits if h["file"] == f]
    print(f"  {f}: {len(fh)} 处")
    for h in fh[:12]:
        print(f"    {h['line']} [{','.join(h['pats'])}] {h['text'][:120]}")

print()
print("== X3. PENDING_DECISIONS.md grep P10|U8|U9 ==")
txt = open(LEAD + "/PENDING_DECISIONS.md", "rb").read().decode("utf-8", errors="replace")
lines = txt.splitlines()
c = 0
for i, l in enumerate(lines, 1):
    if "P10" in l or "U8" in l or "U9" in l:
        c += 1
        if c <= 5:
            print(f"   hit :{i}: {l.strip()[:100]}")
print("  P10|U8|U9 命中行数 =", c)

print()
print("== X4. 12 件 GBK 可疑件在我方扫描中的命中 ==")
their = json.loads(open(BASE + "_ow_raw_hits.json", "rb").read().decode("utf-8"))
gbk12 = their["meta"]["decodeErrFiles"]
for f in gbk12:
    fh = [h for h in hits if h["file"] == f]
    print(f"  {f}: {len(fh)} 处", [(h["line"], h["pats"]) for h in fh])

print()
print("== X5. ⑥越界：9 件绑定件 mtime + 普查窗口内外新写件 ==")
FILES9 = ["matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", "w2_samecause_20261109/W2_SAME_CAUSE.md",
          "o1prime_reach_20261109/O1PRIME_REACHABILITY.md", "matrix_row5_20261109/MATRIX_ROW5_COUPLING.md",
          "strict_exposure_20261109/STRICT_EXPOSURE.md", "matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
          "handoff_pack_20261109/APPROVAL_PACK.md", "PENDING_DECISIONS.md", "GOAL_THREE_TARGETS_20261018.md",
          "matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md", "strict_exposure_20261109/_se_report.md",
          "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"]
for f in FILES9:
    p = LEAD + "/" + f
    st = os.stat(p)
    print(f"  mtime {time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime))}  {f}")
marker = LEAD + "/oldwording_sweep_20261109/_ow_sweep.py"
mt = os.stat(marker).st_mtime
newer = []
for dirpath, dirnames, filenames in os.walk(LEAD):
    dirnames[:] = [d for d in dirnames if d not in {".git"}]
    for fn in filenames:
        p = dirpath + os.sep + fn
        relf = p[len(LEAD) + 1:].replace("\\", "/")
        if relf.startswith("oldwording_sweep_20261109/"):
            continue
        try:
            if os.stat(p).st_mtime > mt:
                newer.append(relf)
        except OSError:
            pass
print("  普查脚本落盘（_ow_sweep.py mtime 基准）之后被写过的 lead/ 件（写域除外）:", len(newer))
for f in newer[:20]:
    print("   NEWER", f)
