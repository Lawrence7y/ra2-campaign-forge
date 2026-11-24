# -*- coding: utf-8 -*-
# 独立复核员 hy4：逐字照抄【决定性】核验
# 判据 A（决定性）：把「源件两标记行之间的正文」整段字节串作为 needle，
#   在合订本主件全文里做 bytes.find —— 命中即证明该正文逐字内嵌（改一字即 0 命中）。
# 判据 B（辅助）：取合订本每章 ↓↓↓/↑↑↑ 之间内容，剥离包装产生的额外前后空行后与源件正文逐字符比。
# 附带：绑定行正则 / ⑤ 抽查重点笔3、笔5 / 第六区顺序措辞 / 第七区越界 grep 统计。
import os, hashlib, re

BASE = r"D:\Project\ra2-campaign-forge"
BOUND = os.path.join(BASE, r"lead\ledger_bound_20261109\_lb_BOUND_VOLUME.md")

SRC = [
    (1, "§605", r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md", 7806),
    (2, "§606", r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md", 6714),
    (3, "§607", r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md", 7703),
    (4, "§608", r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md", 10080),
    (5, "§609", r"lead\s604_verdict_entry_20261109\_ve_DRAFT_S609.md", 18980),
]
SRC_START = "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓"
SRC_END = "## ↑↑↑ 草案正文结束 ↑↑↑"
BOUND_START = "#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓"
BOUND_END = "#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑"

def rb(rel):
    with open(os.path.join(BASE, rel), "rb") as f:
        return f.read()

def src_body(rel):
    lines = rb(rel).decode("utf-8").split("\n")
    si = next(i for i, l in enumerate(lines) if l.strip() == SRC_START.strip())
    ei = next(i for i, l in enumerate(lines) if i > si and l.strip() == SRC_END.strip())
    return "\n".join(lines[si + 1:ei])

bound_b = rb(BOUND)
bound_s = bound_b.decode("utf-8")

print("=== 判据 A：源件正文整段字节串是否原样内嵌于合订本（find，改一字即 0 命中） ===")
allA = True
for no, sec, rel, fbytes in SRC:
    needle = src_body(rel).encode("utf-8")
    first = bound_b.find(needle)
    cnt = bound_b.count(needle)
    hit = first >= 0
    allA &= hit
    print("笔%d %s needle=%dB sha=%s find_pos=%s count=%d  -> %s" % (
        no, sec, len(needle), hashlib.sha256(needle).hexdigest()[:16],
        first if hit else "NOT_FOUND", cnt, "VERBATIM_INLINED" if hit else "REFUTED"))
print("ALL_A_VERBATIM_INLINED =", allA)

print()
print("=== 判据 B：精确验证「块 = 1 前导空行 + 正文 + 1 尾随空行」（包装为纯空行，非改字） ===")
# W 在标记行后写 "\n\n"（多 1 空行），正文后写 "\n\n"（多 1 空行）；
# 源件 body 自身首尾各带 1 个 \n。故块相对 body 恰好多首尾各 1 个 \n。
lines = bound_s.split("\n")
si_list = [i for i, l in enumerate(lines) if l.strip() == BOUND_START.strip()]
ei_list = [i for i, l in enumerate(lines) if l.strip() == BOUND_END.strip()]
allB = True
for idx, (no, sec, rel, fbytes) in enumerate(SRC):
    block = "\n".join(lines[si_list[idx] + 1:ei_list[idx]])
    body = src_body(rel)
    eq = (block == ("\n" + body + "\n"))
    allB &= eq
    print("笔%d %s block=%dB  == '\\n'+body(%dB)+'\\n' ? %s" % (
        no, sec, len(block.encode('utf-8')), len(body.encode('utf-8')), eq))
print("ALL_B_WRAPPER_ONLY =", allB)

print()
print("=== 绑定行：严格正则 + 值 ===")
pat = r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = ([0-9]+)"
bl = re.findall(pat, bound_s)
print("BINDING_LINES count =", len(bl))
for i, (h, b) in enumerate(bl):
    print("  #%d len64=%s sha=%s bytes=%s" % (i + 1, len(h) == 64, h[:16], b))
EXP = ["e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4",
       "213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da",
       "d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6",
       "bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e",
       "058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec"]
EB = [7806, 6714, 7703, 10080, 18980]
vals_ok = (len(bl) == 5 and all(bl[i][0] == EXP[i] and int(bl[i][1]) == EB[i] for i in range(5)))
print("BINDING_VALUES_MATCH_BASELINE =", vals_ok)

print()
print("=== ⑤ 重点抽查：笔3 / 笔5 正文首行与末行（逐字） ===")
for no in (3, 5):
    rel = SRC[no - 1][2]
    b = src_body(rel)
    bl_ = b.split("\n")
    print("笔%d 首非空行: %s" % (no, next(l for l in bl_ if l.strip())))
    print("笔%d 末非空行: %s" % (no, next(l for l in reversed(bl_) if l.strip())))

print()
print("=== ⑥ 第五区是否替 Leader 决定顺序：统计「建议/宜/留/裁决/不替」 vs 强制性措辞 ===")
sec5 = bound_s[bound_s.index("## 五、入账顺序建议"):]
for w in ["不替", "建议", "宜", "留 Leader", "裁定", "裁决", "必须", "先入账", "暂缓"]:
    print("  '%s' 出现 %d 次" % (w, sec5.count(w)))
