"""_rsv_blocks.py — independent transcription block boundary + §607 body hashing.
Do NOT reuse the author's regex. Anchor on the marker lines by their literal text found
in the files themselves, then compute body hashes under several candidate conventions.
Run: python -I -X utf8 ".../_rsv_blocks.py"
"""
import hashlib, os, re
ROOT = r"D:/Project/ra2-campaign-forge"

def readlines(rel):
    txt = open(os.path.join(ROOT, rel), "r", encoding="utf-8", newline="").read()
    return txt.split("\n")

F1 = "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
F2 = "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md"
F3 = "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md"
F4 = "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md"

# independent anchor definition: any line containing 逐字转录开始 / 逐字转录结束 /
# 从这里开始整段复制 / 草案正文结束 / 逐字照抄 combined with 开始/结束 semantics
START_PAT = re.compile(r"(逐字转录开始|从这里开始整段复制|逐字照抄.{0,20}开始|草案正文.{0,10}开始)")
END_PAT   = re.compile(r"(逐字转录结束|草案正文结束|逐字照抄.{0,20}结束)")

def blocks(rel):
    L = readlines(rel)
    starts = [(i+1, L[i]) for i in range(len(L)) if START_PAT.search(L[i])]
    ends   = [(i+1, L[i]) for i in range(len(L)) if END_PAT.search(L[i])]
    pairs = []
    used = set()
    for s, st in starts:
        cand = [e for e, et in ends if e > s and e not in used]
        if cand:
            e = min(cand); used.add(e); pairs.append((s, e))
        else:
            pairs.append((s, None))
    return L, starts, ends, pairs

for rel in [F1, F2, F3, F4]:
    L, starts, ends, pairs = blocks(rel)
    print(f"=== {rel} (len split={len(L)}) ===")
    print("  START markers:", [(n, t[:70]) for n, t in starts])
    print("  END   markers:", [(n, t[:70]) for n, t in ends])
    print("  PAIRS (start,end):", pairs)
    for s, e in pairs:
        if e is None: continue
        body = L[s:e-1]  # exclusive of marker lines
        print(f"  block {s}-{e} inner lines {s+1}..{e-1} count={len(body)}")
        # print first and last inner line for eyeball
        if body:
            print("    first:", repr(body[0][:90]))
            print("    last :", repr(body[-1][:90]))
    print()

# §607 body: author says :111-124 in F1 and :13-26 in F2, both 2707 chars,
# sha256 a758a87b31da39e740977dff05e315333e8fb336ac0d8cdd86866244cfdaab82
def h(txt, label):
    b = txt.encode("utf-8")
    print(f"  {label}: chars={len(txt)} bytes={len(b)} sha256={hashlib.sha256(b).hexdigest()}")

print("=== §607 BODY HASH under multiple conventions ===")
L1, L2 = readlines(F1), readlines(F2)
for lo, hi, label in [(111,124,"F1 lines 111..124"),(13,26,"F2 lines 13..26")]:
    L = L1 if "F1" in label else L2
    seg = L[lo-1:hi]
    print(f"-- {label} : {lo}..{hi} ({hi-lo+1} lines) --")
    h("\n".join(seg), "join_with_LF_no_tail")
    h("\n".join(seg) + "\n", "join_with_LF_plus_tail")
    h("".join(seg), "concat_no_sep")
