# -*- coding: utf-8 -*-
"""_rfv_quotes.py — 核 §3 各条「原文逐字」是否与真实 file:line 一致；并核写域/只读域 mtime。"""
import os, re, time
ROOT = "D:/Project/ra2-campaign-forge/lead"
DRAFT = ROOT + "/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md"
with open(DRAFT, encoding="utf-8") as f: dl = f.read().splitlines()

# 逐处「原文逐字」块：定位 **#XX｜:NNN｜判定** 后紧跟的 - 原文逐字...（`...`）或 - 说错什么
FILEMAP = {
 "A": "s604_attribution_20261108/S604_ATTRIBUTION.md",
 "B": "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
 "C": "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "D": "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "E": "s604_script_gap_20261109/_sg_FINDINGS.md",
 "F": "s604_exclusive_20261109/S604_EXCLUSIVITY.md",
 "G": "s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
 "H": "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
 "I": "direction_ruling_20261108/RULING_DIRECTION.md",
 "J": "direction_ruling_20261108/_dr_RULING.md",
}
print("=== §3 「原文逐字」引文 vs 真实文件行（片段包含检查）===")
cur = None
for i, l in enumerate(dl):
    m = re.match(r"^\*\*(#[A-J]\d)", l)
    if m: cur = m.group(1)[1]
    if "原文逐字" not in l or cur is None: continue
    # 提取该行中反引号包围的最长片段
    segs = re.findall(r"`([^`]+)`", l)
    if not segs: continue
    q = max(segs, key=len)
    # 从本行或后续 2 行找 :NNN
    nums = re.findall(r":(\d+)", l)
    if not nums:
        nums = re.findall(r":(\d+)", " ".join(dl[max(0,i-6):i]))
    if not nums: continue
    n = int(nums[-1])
    fp = ROOT + "/" + FILEMAP[cur]
    try: lines = open(fp, encoding="utf-8").read().splitlines()
    except Exception as e: print("  %s ERR %s" % (cur, e)); continue
    real = lines[n-1] if n <= len(lines) else ""
    ok = (q in real) or (q[:60] in real)
    print("  %-4s :%-4d %s  draft_quote_len=%d real_len=%d" % (cur, n, "MATCH" if ok else "MISMATCH", len(q), len(real)))
    if not ok:
        print("      QUOTE = %r" % q[:160])
        print("      REAL  = %r" % real[:160])

print("=== 13 件 mtime（都须早于交付草案 09:32）===")
FILES13 = [
 "slowframe_r3_20261108/S604_GAP_RECHECK.md",
 "s604_attribution_20261108/S604_ATTRIBUTION.md",
 "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
 "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "ledger_appendix_20261108/_lad_tpl.md",
 "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "s604_script_gap_20261109/_sg_FINDINGS.md",
 "s604_exclusive_20261109/S604_EXCLUSIVITY.md",
 "s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
 "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
 "direction_ruling_20261108/RULING_DIRECTION.md",
 "direction_ruling_20261108/_dr_RULING.md",
]
for r in FILES13:
    st = os.stat(ROOT + "/" + r)
    print("  %s  %s  %d B" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), r, st.st_size))
print("=== 写域 mtime ===")
wd = ROOT + "/s604_refsync_full_20261109"
for f in sorted(os.listdir(wd)):
    st = os.stat(os.path.join(wd, f))
    print("  %s  %-32s %d B" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), f, st.st_size))
