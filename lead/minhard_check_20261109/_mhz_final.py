# _mhz_final.py — final self-check of MINHARD_SET_CHECK.md (this session)
import hashlib, os, re, subprocess, sys
ROOT = r"D:\Project\ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "minhard_check_20261109")
DOC = os.path.join(WD, "MINHARD_SET_CHECK.md")
O = []
def p(s=""): O.append(str(s))

raw = open(DOC, "rb").read()
txt = raw.decode("utf-8")
L = txt.splitlines()
p(f"== A. deliverable ==")
p(f"  bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()} lines={len(L)} newlines={raw.count(bytes([10]))}")

p("")
p("== B. binding line strict format ==")
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
hits = [(i, m.group(1), m.group(2)) for i, l in enumerate(L, 1) if (m := pat.match(l))]
p(f"  strict_matches={len(hits)}")
for i, h, b in hits:
    p(f"    :{i}: sha={h} bytes={b}")
expect_sha = hashlib.sha256(open(os.path.join(ROOT, "lead", "s604_refsync_full_20261109", "S604_REFSYNC_FULL.md"), "rb").read()).hexdigest()
expect_bytes = os.path.getsize(os.path.join(ROOT, "lead", "s604_refsync_full_20261109", "S604_REFSYNC_FULL.md"))
p(f"  recomputed sha={expect_sha} bytes={expect_bytes}")
p(f"  BINDING_OK={bool(hits) and hits[0][1]==expect_sha and hits[0][2]==str(expect_bytes)}")

p("")
p("== C. six sections present exactly ==")
for n in range(1, 7):
    ms = [i for i, l in enumerate(L, 1) if l.startswith(f"## {n} ")]
    p(f"  '## {n} ' -> {ms}")
p("")
p("== D. required elements (must appear) ==")
req = ["处8", "处9", "#C1", "#C2", "#A3", "永久台账", "4 件最小", "零边际成本",
       "执行顺序", "最坏情形", "未验", "partial", "unconfirmed", "只校核", "不入账"]
for k in req:
    p(f"  {k}: count={txt.count(k)}")
p("")
p("== E. verbatim three-group originals present ==")
G1 = "- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。"
G2 = "3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。"
G3 = "3. **无法归属（缺口，还差什么）**：**确切错误机理无法归属**——§604 空档列当年内联脚本体未落盘（台账 :9751 自述；:9752-9755 仅自认两次已改正的错误），N-8 侧 `_n8_variants2.py` 亦未落盘（`SLOW_WINDOW_LIMITS.md:92`），故「实现 bug / 誊写错 / 未测奇异口径」三选一**不可定谳**。要补齐需：当年内联脚本的落盘副本，或含空档列中间值的等价产物；在此之前本归属止于「数字错误」这一事实类。"
for tag, s in [("G1", G1), ("G2", G2), ("G3", G3)]:
    p(f"  {tag} present={s in txt} count={txt.count(s)}")

p("")
p("== F. 11 upstream fingerprints unchanged in this session (hashlib) ==")
ORCH = {
 "lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md": ("d9b9c5acd0077060fe7ab0a064c263aa609881bfdc1736407d66d5eec890e1f3", 55331),
 "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md": ("8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5", 61819),
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
 "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2", 17272),
 "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703),
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
 "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
}
ok = True
for rel, (eh, eb) in ORCH.items():
    b = open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb").read()
    m = (hashlib.sha256(b).hexdigest() == eh and len(b) == eb)
    ok &= m
    p(f"  {rel} MATCH={m}")
p(f"  ALL_11_UNCHANGED={ok}")

p("")
p("== G. git status (readonly paths) + log ==")
cmd = ["git", "status", "--short", "--",
       "lead/s604_refsync_full_20261109/", "lead/s604_attribution_20261108/",
       "lead/s604_verdict_entry_20261109/", "lead/ledger_appendix_20261108/",
       "lead/ledger_bound_20261109/", "lead/GOAL_THREE_TARGETS_20261018.md",
       "lead/PENDING_DECISIONS.md"]
r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
p("  " + r.stdout.replace("\n", "\n  ").rstrip())
p(f"  exit={r.returncode}")
r2 = subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=ROOT, capture_output=True, text=True)
p(f"  git log -1 = {r2.stdout.strip()}")
p("")
p("== H. write domain files (this session only added _mhz_* + MINHARD_SET_CHECK.md) ==")
for pref in ["_mh_", "_mhv_", "_mhz_", "MINHARD_SET_CHECK.md"]:
    fs = sorted(f for f in os.listdir(WD) if f.startswith(pref))
    p(f"  {pref} count={len(fs)}")
sys.stdout.write("\n".join(O) + "\n")
