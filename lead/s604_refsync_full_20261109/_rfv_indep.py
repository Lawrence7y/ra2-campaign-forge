# -*- coding: utf-8 -*-
"""_rfv_indep.py — 独立复核员自写只读指纹/清单核验脚本（前缀 _rfv_）
零真机、零采样：仅 hashlib 读盘 + 文本解析，不改任何被核件。
用法: python -I -X utf8 <绝对路径>/_rfv_indep.py
"""
import hashlib, os, re, sys

ROOT = "D:/Project/ra2-campaign-forge"
LEAD = ROOT + "/lead"

def fp(rel):
    p = LEAD + "/" + rel
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

# ---- (1) 六件编排方基线 ----
BASE6 = [
    "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
    "s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
    "s604_refsync_20261109/S604_REFSYNC_DRAFT.md",
    "s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",
    "PENDING_DECISIONS.md",
    "GOAL_THREE_TARGETS_20261018.md",
]
EXPECT6 = {
    "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    "s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    "s604_refsync_20261109/S604_REFSYNC_DRAFT.md": ("cbadcb872c696c7a39af50764ecc0b276d42e9a89afd73caead0a8d703338841", 38819),
    "s604_refsync_20261109/_rs_REFSYNC_DRAFT.md": ("7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572", 33869),
    "PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
print("=== (1) 六件基线独立实算 ===")
ok6 = 0
for r in BASE6:
    h, n = fp(r)
    eh, en = EXPECT6[r]
    m = "MATCH" if (h == eh and n == en) else "MISMATCH"
    if m == "MATCH": ok6 += 1
    print("%s %s sha=%s bytes=%d expect=%s/%d" % (m, r, h, n, eh, en))
print("BASE6 MATCH = %d/6" % ok6)

# ---- (2) 13 件 §4.2 证据件指纹 ----
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
AUTHOR13 = {
 "slowframe_r3_20261108/S604_GAP_RECHECK.md": ("5d1b0ecc", 19291),
 "s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a6067", 27182),
 "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("72410261", 17272),
 "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9", 45719),
 "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f97", 7703),
 "ledger_appendix_20261108/_lad_tpl.md": ("a2313396", 25723),
 "s604_script_gap_20261109/S604_SCRIPT_GAP.md": ("593c7a3e", 20271),
 "s604_script_gap_20261109/_sg_FINDINGS.md": ("a9f293bb", 10925),
 "s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("82347668", 30536),
 "s604_exclusive_20261109/_ex_EXCLUSIVITY.md": ("1ad890b4", 20623),
 "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md": ("e7c29e06", 23707),
 "direction_ruling_20261108/RULING_DIRECTION.md": ("0ebd68dd", 16514),
 "direction_ruling_20261108/_dr_RULING.md": ("c6fa7a0a", 20942),
}
print("=== (2) 13 件 §4.2 证据件独立实算 ===")
ok13 = 0
for r in FILES13:
    h, n = fp(r)
    eh, en = AUTHOR13[r]
    m = "MATCH" if (h.startswith(eh) and n == en) else "MISMATCH"
    if m == "MATCH": ok13 += 1
    print("%s %s sha=%s bytes=%d expect=%s.../%d" % (m, r, h, n, eh, en))
print("FILES13 MATCH = %d/13" % ok13)

# ---- (3) §4.2 表格独立解析：逐 file:line 严数 ----
print("=== (3) §4.2 表格独立解析（file:line 展开严数）===")
vp = LEAD + "/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md"
with open(vp, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()
# 表区 = 行 94..125 (1-based)
tbl = lines[93:125]
print("表行数(94..125) = %d" % len(tbl))
# 人工按 # 展开：解析每行的「行」列，拆出所有 :NN 或 :NN-NN 或 :10(b)
points = {}   # key=(file,line) -> list of row#
cur_file = None
row_count = 0
for ln in tbl:
    cols = [c.strip() for c in ln.strip().strip("|").split("|")]
    if len(cols) < 3: continue
    num = cols[0]
    if not num.isdigit(): continue
    row_count += 1
    fcell = cols[1]
    lcell = cols[2]
    if fcell != "同件" and fcell.startswith("lead/"):
        cur_file = fcell.replace("lead/", "", 1)
    # 展开 lcell 中所有 :NN
    # 匹配 :数字 或 :数字-数字 或 :数字(b) 或 :数字、:NN
    for m in re.finditer(r":(\d+)(?:-(\d+))?(\([a-z]\))?", lcell):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
        for x in range(a, b+1):
            k = (cur_file, x)
            points.setdefault(k, []).append(int(num))
print("解析到 # 行数 = %d" % row_count)
print("file:line 严数（含区间展开、含区间合并前逐行）= %d" % len(points))
# 但 §4.2 :90 声明 43 处，其「严数」口径：:115-116 计 2 行、:55-57 计 3 行 —— 与我的展开一致
# 打印每个 # 的展开点，便于核对
for k in sorted(points, key=lambda z:(z[0], z[1])):
    print("  %s:%d  <- #%s" % (k[0], k[1], ",".join(str(x) for x in points[k])))

# ---- (4) 同文对 IDENTICAL 实算 ----
print("=== (4) 同文对逐字比对（3 组）===")
def line_of(rel, n):
    with open(LEAD+"/"+rel, "r", encoding="utf-8") as f:
        return f.read().splitlines()[n-1]
PAIRS = [
 ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "ledger_appendix_20261108/_lad_tpl.md", 151),
 ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
 ("s604_attribution_20261108/S604_ATTRIBUTION.md", 136, "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md", 90),
]
for a,la,b,lb in PAIRS:
    ta, tb = line_of(a,la), line_of(b,lb)
    print("%s %s:%d vs %s:%d" % ("IDENTICAL" if ta==tb else "DIFF", a,la,b,lb))
    print("   A= %r" % ta[:200])
    print("   B= %r" % tb[:200])

# ---- (5) 交付草案自检 ----
print("=== (5) 交付件自检 ===")
dp = LEAD + "/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md"
with open(dp, "rb") as f: db = f.read()
print("_rf_FULL_REFSYNC_DRAFT.md sha=%s bytes=%d" % (hashlib.sha256(db).hexdigest(), len(db)))
with open(dp, "r", encoding="utf-8") as f: dl = f.read().splitlines()
# 绑定行
bl = [ (i+1,l) for i,l in enumerate(dl) if "被核对象 SHA256" in l ]
for i,l in bl:
    print("绑定行 :%d = %r" % (i,l))
    m = re.fullmatch(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", l)
    print("  格式严格匹配(无插入字符) = %s" % bool(m))

# 三选一计数：搜索 §3 各条判定
tally = {"改":0,"加注":0,"保留":0}
for i,l in enumerate(dl):
    m = re.match(r"^·\s*[:0-9()\-,（b）\s]+?\s*(改|加注|保留)\s*[—-]", l)
    if m: tally[m.group(1)] += 1
print("§3 逐处三选一计数（按行首·模式） = %r" % tally)
print("=== DONE ===")
