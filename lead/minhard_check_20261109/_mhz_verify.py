# _mhz_verify.py — MINHARD_SET_CHECK independent verification (this session)
# read-only over all upstream dirs; only writes its own stdout (redirected by caller)
import hashlib
import os
import re
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
LEAD = os.path.join(ROOT, "lead")

def rp(rel):
    return os.path.join(ROOT, rel.replace("/", os.sep))

def readb(rel):
    with open(rp(rel), "rb") as f:
        return f.read()

def lines(rel):
    return readb(rel).decode("utf-8").splitlines()

def sha(rel):
    return hashlib.sha256(readb(rel)).hexdigest()

def nbytes(rel):
    return len(readb(rel))

OUT = []
def p(s=""):
    OUT.append(str(s))

# ============ A. 11 orchestrator fingerprints ============
ORCH = {
 "lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md": ("d9b9c5acd0077060fe7ab0a064c263aa609881bfdc1736407d66d5eec890e1f3", 55331, 338),
 "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md": ("8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5", 61819, 366),
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182, 196),
 "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2", 17272, 129),
 "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536, 267),
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703, 41),
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719, 237),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980, 83),
 "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097, 171),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, 9758),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, 382),
}
p("== A. 11 orchestrator fingerprints (this session hashlib) ==")
all_sha = all_bytes = True
for rel, (esh, eb, el) in ORCH.items():
    h, b, nl = sha(rel), nbytes(rel), readb(rel).count(b"\n")
    ms, mb = (h == esh), (b == eb)
    all_sha &= ms; all_bytes &= mb
    p(f"  {rel} sha={h} MATCH_SHA={ms} bytes={b} MATCH_BYTES={mb} newline_count={nl} orchestrator_lines={el} lines_diff={el-nl}")
p(f"ALL_SHA_MATCH={all_sha}  ALL_BYTES_MATCH={all_bytes}")
p(f"BINDING: 被核对象 SHA256 = {sha('lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md')}，字节数 = {nbytes('lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md')}")

# ============ B. three groups verbatim + pair equality ============
G1_EXPECT = "- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。"
G2_EXPECT = "3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。"
G3_EXPECT = "3. **无法归属（缺口，还差什么）**：**确切错误机理无法归属**——§604 空档列当年内联脚本体未落盘（台账 :9751 自述；:9752-9755 仅自认两次已改正的错误），N-8 侧 `_n8_variants2.py` 亦未落盘（`SLOW_WINDOW_LIMITS.md:92`），故「实现 bug / 誊写错 / 未测奇异口径」三选一**不可定谳**。要补齐需：当年内联脚本的落盘副本，或含空档列中间值的等价产物；在此之前本归属止于「数字错误」这一事实类。"
TARGETS = [
 ("LEDGER_123", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, G1_EXPECT),
 ("DRAFT3_25", "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25, G1_EXPECT),
 ("LEDGER_215", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, G2_EXPECT),
 ("TPL_151", "lead/ledger_appendix_20261108/_lad_tpl.md", 151, G2_EXPECT),
 ("ATTR_171", "lead/s604_attribution_20261108/S604_ATTRIBUTION.md", 171, G3_EXPECT),
 ("BOUND_VOL_196", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196, G1_EXPECT),
 ("BOUND_LB_129", "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129, G1_EXPECT),
]
p("")
p("== B. three-group verbatim lines (1-based) and pair equality ==")
vals = {}
for tag, rel, n, expect in TARGETS:
    L = lines(rel)
    got = L[n-1]
    vals[tag] = got
    p(f"  {tag} {rel}:{n} MATCH_TASK_TEXT={got==expect}")
    p(f"     TEXT= {got}")
p(f"  处8≡处9 (LEDGER_123==DRAFT3_25) = {vals['LEDGER_123']==vals['DRAFT3_25']}")
p(f"  #C1≡#C2 (LEDGER_215==TPL_151) = {vals['LEDGER_215']==vals['TPL_151']}")
p(f"  BOUND_VOL_196==LEDGER_123 = {vals['BOUND_VOL_196']==vals['LEDGER_123']}")
p(f"  BOUND_LB_129==LEDGER_123 = {vals['BOUND_LB_129']==vals['LEDGER_123']}")
p(f"  total lines: LEDGER={len(lines('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md'))} DRAFT3={len(lines('lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md'))} ATTR={len(lines('lead/s604_attribution_20261108/S604_ATTRIBUTION.md'))}")

# ============ C. block markers & IN_BLOCK ============
p("")
p("== C. verbatim-copy block markers and IN_BLOCK for the five group lines ==")
def find_blocks(rel):
    L = lines(rel)
    starts = [i+1 for i,x in enumerate(L) if ("逐字转录开始" in x or "草案正文（逐字照抄，从下一行起）" in x or "从这里开始整段复制" in x)]
    ends = [i+1 for i,x in enumerate(L) if ("逐字转录结束" in x or "草案正文（逐字照抄结束）" in x or "草案正文结束" in x)]
    return starts, ends, L

CHECK_FILES = [
 ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", [123, 215]),
 ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", [25]),
 ("lead/ledger_appendix_20261108/_lad_tpl.md", [151]),
 ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md", [171]),
 ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", [196]),
 ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", [129]),
 ("lead/ledger_bound_20261109/_lb2_TEMPLATE.md", []),
]
for rel, probes in CHECK_FILES:
    starts, ends, L = find_blocks(rel)
    p(f"  {rel} starts={starts} ends={ends}")
    for n in probes:
        inside = any(s < n < e for s, e in zip(starts, ends)) if len(starts)==len(ends) else None
        p(f"    :{n} IN_BLOCK={inside}  text={L[n-1][:60]}...")
    # print marker lines verbatim
    for n in starts+ends:
        p(f"    MARKER :{n}: {L[n-1]}")

# ============ D. repo-wide exact-match scan of G1 boundary sentence ============
p("")
p("== D. repo-wide exact-line scan of the §607 boundary sentence (G1) ==")
needle = G1_EXPECT
hits = []
scanned = 0
for base, dirs, files in os.walk(LEAD):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
    for fn in files:
        if not fn.lower().endswith((".md", ".py", ".txt", ".json")):
            continue
        fp = os.path.join(base, fn)
        try:
            with open(fp, "rb") as f:
                raw = f.read()
            txt = raw.decode("utf-8")
        except Exception:
            continue
        scanned += 1
        for i, ln in enumerate(txt.splitlines(), 1):
            if ln == needle:
                hits.append((os.path.relpath(fp, ROOT).replace(os.sep, "/"), i))
p(f"  files_scanned={scanned}  exact_line_hits={len(hits)}")
for rel, i in sorted(hits):
    p(f"    {rel}:{i}")

# ============ E. two ledgers: not-yet-entered check ============
p("")
p("== E. two ledgers: §605-§610 / 码形定谳 / dur 字典 / 512655 grep ==")
pat = re.compile(r"§60[5-9]|§610|码形定谳|dur 字典|512655")
for rel in ["lead/GOAL_THREE_TARGETS_20261018.md", "lead/PENDING_DECISIONS.md"]:
    ms = [(i, l) for i, l in enumerate(lines(rel), 1) if pat.search(l)]
    p(f"  {rel} matches={len(ms)}")
    for i, l in ms[:10]:
        p(f"    :{i}: {l[:100]}")

# ============ F. source lines for 'outdated' and 'minimal set' claims ============
p("")
p("== F. key upstream lines (verbatim) ==")
KEY = [
 ("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md", [1, 22, 46, 47, 48, 66, 67, 69, 70]),
 ("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md", [79, 88, 90, 101, 107, 108, 129, 148, 151]),
 ("lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md", [62, 68, 85, 126, 238, 247, 249, 251, 267, 275, 278, 283, 285, 291, 297, 303, 307, 308, 309, 315, 319, 322, 338, 339]),
 ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", [3, 10, 28, 34, 46, 83, 84, 85, 196, 202, 203]),
 ("lead/ledger_appendix_20261108/_lad_tpl.md", [154, 155, 156, 157, 158, 160, 161]),
 ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", [4, 11, 31, 209, 211, 222]),
 ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", [1, 4, 11, 28]),
]
for rel, ns in KEY:
    L = lines(rel)
    p(f"  ---- {rel} (total {len(L)} lines) ----")
    for n in ns:
        if n <= len(L):
            p(f"    :{n}: {L[n-1]}")
        else:
            p(f"    :{n}: <OUT_OF_RANGE total={len(L)}>")

# ============ G. reviewer artifacts: verdict evidence ============
p("")
p("== G. reviewer (_mhv_*) / writer (_mh_*) artifact key lines ==")
for rel, ns in [
 ("lead/minhard_check_20261109/_mhv_fp_out.txt", [58, 60]),
 ("lead/minhard_check_20261109/_mh_fp_verify_out.txt", [1, 13]),
 ("lead/minhard_check_20261109/_mhv_final_out.txt", [82, 83, 84, 100, 101, 102, 103]),
 ("lead/minhard_check_20261109/_mhv_blocks3_out.txt", [8, 9, 12, 17, 20, 24, 32, 36, 55, 56]),
 ("lead/minhard_check_20261109/_mh_final_out.txt", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
]:
    L = lines(rel)
    p(f"  ---- {rel} (total {len(L)} lines) ----")
    for n in ns:
        if n <= len(L):
            p(f"    :{n}: {L[n-1]}")
        else:
            p(f"    :{n}: <OUT_OF_RANGE>")

sys.stdout.write("\n".join(OUT) + "\n")
