# -*- coding: utf-8 -*-
# 独立复核员 hy4：逐字照抄核验（第五步 b）
# 不复用编排方 _lb_build.py 的抽取结果；自己从【源件】用标记行切片取正文，
# 自己从【合订本主件】用其"↓↓↓逐字照抄" / "↑↑↑…结束" 标记切片取正文，
# 逐字节比对（含所有字符，改一个字即 MISMATCH）。
import os, hashlib

BASE = r"D:\Project\ra2-campaign-forge"
BOUND = os.path.join(BASE, r"lead\ledger_bound_20261109\_lb_BOUND_VOLUME.md")

# 源件：标记行（与源件实际一致）
SRC = [
    (1, "§605", r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md"),
    (2, "§606", r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md"),
    (3, "§607", r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md"),
    (4, "§608", r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md"),
    (5, "§609", r"lead\s604_verdict_entry_20261109\_ve_DRAFT_S609.md"),
]
SRC_START = "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓"
SRC_END = "## ↑↑↑ 草案正文结束 ↑↑↑"

# 编排方在合订本里用的包装标记（各章）
BOUND_START = "#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓"
BOUND_END = "#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑"

def read_b(rel):
    with open(os.path.join(BASE, rel), "rb") as f:
        return f.read()

def extract_between(text, start, end, occurrence):
    """严格取 start 标记行之后 ~ end 标记行之前 的内容，不含标记行。"""
    lines = text.split("\n")
    si = []
    ei = []
    for i, ln in enumerate(lines):
        if ln.strip() == start.strip():
            si.append(i)
        if ln.strip() == end.strip():
            ei.append(i)
    if occurrence >= len(si) or occurrence >= len(ei):
        raise RuntimeError("marker missing occ=%d si=%s ei=%s" % (occurrence, si, ei))
    s = si[occurrence]
    e = ei[occurrence]
    if e <= s:
        raise RuntimeError("bad order")
    return "\n".join(lines[s + 1:e])

def src_body(rel):
    raw = read_b(rel).decode("utf-8")
    return extract_between(raw, SRC_START, SRC_END, 0)

print("=== 源件正文抽取（自己按标记行切片） + 合订本逐字比对 ===")
bound_text = read_b(BOUND).decode("utf-8")
all_ok = True
for idx, (no, sec, rel) in enumerate(SRC):
    s_body = src_body(rel)
    b_body = extract_between(bound_text, BOUND_START, BOUND_END, idx)
    sb = s_body.encode("utf-8")
    bb = b_body.encode("utf-8")
    eq = (sb == bb)
    all_ok &= eq
    ss = hashlib.sha256(sb).hexdigest()
    bs = hashlib.sha256(bb).hexdigest()
    print("\n笔%d %s  %s" % (no, sec, rel.split("\\")[-1]))
    print("  src body bytes=%d sha=%s" % (len(sb), ss))
    print("  bound      bytes=%d sha=%s" % (len(bb), bs))
    print("  VERBATIM_EQ = %s" % eq)
    if not eq:
        # 定位第一处差异
        n = min(len(sb), len(bb))
        k = 0
        while k < n and sb[k] == bb[k]:
            k += 1
        print("  FIRST DIFF at byte %d: src=%r bound=%r" % (k, sb[k:k+40], bb[k:k+40]))

print("\nALL_VERBATIM =", all_ok)

# 额外：核对每章"本章正文逐字核验"声明的 sha/bytes 是否与源件正文一致
print("\n=== 复核主件各章声明的抽取 sha/bytes 是否与源件正文一致 ===")
DECL = {
    1: ("5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c", 4735),
    2: ("030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6", 4097),
    3: ("e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698", 4894),
    4: ("24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b", 6318),
    5: ("f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682", 8388),
}
for no, sec, rel in SRC:
    sb = src_body(rel).encode("utf-8")
    h = hashlib.sha256(sb).hexdigest()
    dh, db = DECL[no]
    print("笔%d %s: sha_match=%s bytes_match=%s (actual %d / declared %d)" % (
        no, sec, h == dh, len(sb) == db, len(sb), db))
