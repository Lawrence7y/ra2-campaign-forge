# -*- coding: utf-8 -*-
"""_rs_verify.py — Step 1: independent verbatim comparison, block boundaries,
group-3 transcription-marker check, and needle-variant investigation.
Read-only. hashlib only.
"""
import os, hashlib

ROOT = "D:/Project/ra2-campaign-forge/lead/"

def load(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        b = f.read()
    return b, b.decode("utf-8", "replace").splitlines()

def fp(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def show_cmp(tag, a, b):
    print("--- %s ---" % tag)
    print("A len(chars) =", len(a), " sha256 =", fp(a))
    print("B len(chars) =", len(b), " sha256 =", fp(b))
    print("verbatim EQUAL =", a == b)
    if a != b:
        # first difference + all differing positions
        n = min(len(a), len(b))
        diffs = [(i, a[i] if i < len(a) else "<EOS>", b[i] if i < len(b) else "<EOS>")
                 for i in range(max(len(a), len(b))) if (i >= n or a[i] != b[i])]
        print("num differing positions =", len(diffs))
        for i, ca, cb in diffs[:40]:
            print("  pos %d: A=%r (U+%04X)  B=%r (U+%04X)" %
                  (i, ca, ord(ca) if ca != "<EOS>" else 0,
                   cb, ord(cb) if cb != "<EOS>" else 0))
    else:
        print("first 60 chars =", repr(a[:60]))
        print("last  60 chars =", repr(a[-60:]))

LA = "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
D3 = "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md"
TPL = "ledger_appendix_20261108/_lad_tpl.md"
ATT = "s604_attribution_20261108/S604_ATTRIBUTION.md"
MH  = "minhard_check_20261109/_mh_MINHARD_CHECK.md"

if __name__ == "__main__":
    la_b, la = load(LA)
    d3_b, d3 = load(D3)
    tp_b, tp = load(TPL)
    at_b, at = load(ATT)
    mh_b, mh = load(MH)

    print("### (a) GROUP 1 : LEDGER_APPENDIX_DRAFT.md:123  vs  _la_draft3:25")
    show_cmp("group1", la[122], d3[24])

    print()
    print("### GROUP 2 : LEDGER_APPENDIX_DRAFT.md:215  vs  _lad_tpl.md:151")
    show_cmp("group2", la[214], tp[150])

    print()
    print("### (b) transcription-block markers in LEDGER_APPENDIX_DRAFT.md")
    for i, L in enumerate(la, 1):
        if ("逐字转录开始" in L or "逐字转录结束" in L or
            "草案正文" in L and ("↓↓↓" in L or "↑↑↑" in L or "从这里开始" in L)):
            print("%4d | %s" % (i, L))
    print("LA total lines =", len(la))
    print("line 110 =", repr(la[109]))
    print("line 125 =", repr(la[124]))
    print("line 111..124 chars =", len("\n".join(la[110:124])),
          "sha256 =", fp("\n".join(la[110:124])))
    print("line 123 in [111,124]? ", 111 <= 123 <= 124)
    print("line 215 in [111,124]? ", 111 <= 215 <= 124)
    print("§6.3 heading line 211 =", repr(la[210]))
    print("line 215 =", repr(la[214]))

    print()
    print("### D3 block markers")
    for i, L in enumerate(d3, 1):
        if ("↓↓↓" in L or "↑↑↑" in L):
            print("%4d | %s" % (i, L))
    print("D3 lines 13..26 chars =", len("\n".join(d3[12:26])),
          "sha256 =", fp("\n".join(d3[12:26])))

    print()
    print("### (c) GROUP 3 : S604_ATTRIBUTION.md transcription-block hunt")
    keys = ["逐字转录", "整段复制", "↓↓↓", "↑↑↑", "草案正文", "从这里开始",
            "可整段复制追加", "转录开始", "转录结束"]
    found = []
    for i, L in enumerate(at, 1):
        for k in keys:
            if k in L:
                found.append((i, k, L))
    print("ATT bytes =", len(at_b), "lines =", len(at),
          "marker-like hits =", len(found))
    for i, k, L in found[:40]:
        print("%4d [%s] | %s" % (i, k, L[:150]))
    print("ATT:171 =", repr(at[170]))
    print("ATT:1   =", repr(at[0]))

    print()
    print("### (d) needle-variant check on _mh_MINHARD_CHECK.md extras 206,207,253")
    for n in [206, 207, 253]:
        print("%4d | %s" % (n, mh[n-1][:220]))
    print("needle present?")
    for n in [206, 207, 253]:
        L = mh[n-1]
        print(n, "只能判「不可复现」" in L, "不能定位当年错误步骤" in L,
              "只能判『不可复现』" in L)
