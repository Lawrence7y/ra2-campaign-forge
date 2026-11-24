# -*- coding: utf-8 -*-
# _acv_quotes.py — 复核员独立逐字核对（只读，零修改）
import io, re, sys

BASE = r"D:\Project\ra2-campaign-forge"
def rd(rel):
    with io.open(BASE + "\\" + rel, "r", encoding="utf-8") as f:
        return f.read().split("\n")

DRAFT = rd(r"lead\a_class_fix_20261109\_ac_A1A4A5_FIX_DRAFT_20261109.md")
MX  = rd(r"lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md")
MR  = rd(r"lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md")
U8F = rd(r"lead\handoff_pack_20261109\_hp_U8.md")
U9F = rd(r"lead\handoff_pack_20261109\_hp_U9.md")
W2  = rd(r"lead\w2_samecause_20261109\W2_SAME_CAUSE.md")
UF  = rd(r"lead\text_fix_unified_20261109\_uf_UNIFIED_FIX_LIST_20261109.md")

def tick(s):  # 去两侧反引号与首尾空白
    s = s.strip()
    if len(s) >= 2 and s.startswith("`") and s.endswith("`"):
        s = s[1:-1]
    return s

fails = []
def chk(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), "|", name, ("| " + detail if detail else ""))
    if not cond: fails.append(name)

# —— ② 草案件摘引 vs 受核件实文 ——
chk("A1 全行摘引 draft:58 == MATRIX:90", DRAFT[57] == MX[89])
a1_orig = tick(DRAFT[101])
chk("A1 原句 draft:102 是 MATRIX:90 行尾句", MX[89].endswith(a1_orig) and a1_orig in MX[89], repr(a1_orig[:60]))
chk("A4 全行摘引 draft:73 == _mr:112", DRAFT[72] == MR[111])
a5_row = tick(DRAFT[87])
chk("A5 行摘引 draft:88 == _mr:121", a5_row == MR[120])
a4_orig = tick(DRAFT[111])
chk("A4 原文 draft:112 == _mr:112 整行", a4_orig == MR[111])
a5_cell = tick(DRAFT[125])
chk("A5 原格 draft:126 在 _mr:121 行尾格", MR[120].endswith(a5_cell + " |"))
chk("MATRIX:146 含加粗格 **罕见**（同根因双时点；评级为推理）", "**罕见**（同根因双时点；评级为推理）" in MX[145])

# —— ③ 改文 vs U8/U9 逐字节 ——
u8 = U8F[13]   # _hp_U8.md:14
u9 = U9F[13]   # _hp_U9.md:14
tail1 = "→ read_error 先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符。"
chk("U8:14 以 read_error 尾链收尾", u8.endswith(tail1))
u8body = u8[: len(u8) - len(tail1)]
a1_new = tick(DRAFT[103])
a4_new = tick(DRAFT[113])
a5_new = tick(DRAFT[127])
prefix4 = "2. **W2**：pre 侧 "
tail2 = "。源读面持续阻断横跨 pre 与 post 两个时点，可一次造成两半。**评级：罕见**。"
chk("A4 改文 draft:114 == 「2. **W2**：pre 侧 」+ U8:14 去尾链 + 结论句尾段（逐字节）",
    a4_new == prefix4 + u8body + tail2)
chk("A5 改文 draft:128 == U9:14（逐字节同文）", a5_new == u9)
chk("U8:14 == 源③ W2:122 引用块（去「> 」后逐字节）", W2[121].startswith("> ") and W2[121][2:] == u8)
ufu8 = tick(UF[118]); ufu9 = tick(UF[129])
chk("_uf:119 U8 改后 == _hp_U8.md:14", ufu8 == u8)
chk("_uf:130 U9 改后 == _hp_U9.md:14", ufu9 == u9)

# A1 改文词汇逐字取自 U8:14（括号内列举程序化抽取，避免转写误差）
frags = ["源读面持续阻断", "AV 对该路径持续拦截", "均只在收尾时点成立，不能单独桥接", "可一次造成两半"]
m = re.search(r"ACL 拒读〔[^〕]*〕", u8);  frags.append(m.group(0) if m else "«ACL抽取失败»")
m = re.search(r"游戏句柄〔[^〕]*〕", u8);  frags.append(m.group(0) if m else "«句柄抽取失败»")
m = re.search(r"磁盘满〔[^〕]*〕", u8);    frags.append(m.group(0) if m else "«磁盘抽取失败»")
for fr in frags:
    chk("A1 改文含 U8:14 片段「%s」" % fr[:24], fr in a1_new)
chk("A1 框架「横跨 pre/post 两时点」与 MATRIX:154/U8:9 同款", "横跨 pre/post 两时点" in a1_new and "横跨 pre/post 两时点" in MX[153])
chk("A1 括号形适配（U8 主句为「源读面持续阻断：」，A1 为「源读面持续阻断（」，句角色不同）",
    "源读面持续阻断：" in u8 and "源读面持续阻断（" in a1_new)

# 旧口径残留否定性检查（改文不得再含旧表述）
chk("A4 改文不含「P4 所证」", "P4 所证" not in a4_new)
chk("A4 改文不含「采集失败」", "采集失败" not in a4_new)
chk("A4 改文不含「句柄被占/ACL 损坏」", "句柄被占" not in a4_new and "ACL 损坏" not in a4_new)
chk("A4 改文保留行尾「**评级：罕见**。」", a4_new.endswith("**评级：罕见**。"))
chk("A4 改文含「AV 瞬时锁非持续根因」「路径异常…不产 error 态」（U8 修正语义在位）",
    "AV 瞬时锁非持续根因" in a4_new and "不产 error 态" in a4_new)
chk("A1 改文不含旧句「句柄/ACL 横跨两时点」", "句柄/ACL 横跨两时点" not in a1_new)
chk("_mr:112 原行本无「→ read_error」尾链（省尾链正当）", "→ read_error" not in MR[111])
chk("_mr:112 原行本无「源读面」（旧行确为旧口径）", "源读面" not in MR[111])

# —— 唯一性复证（受核件两件全行扫描）——
def lines_with(lines, s): return [i + 1 for i, x in enumerate(lines) if s in x]
chk("「同一持续根因」在 MATRIX 仅 :90/:154", lines_with(MX, "同一持续根因") == [90, 154], str(lines_with(MX, "同一持续根因")))
chk("「同一持续根因」在 _mr 仅 :112", lines_with(MR, "同一持续根因") == [112], str(lines_with(MR, "同一持续根因")))
chk("「同根因双时点」MATRIX 仅 :146、_mr 仅 :121", lines_with(MX, "同根因双时点") == [146] and lines_with(MR, "同根因双时点") == [121])
chk("无加粗格「罕见（同根因双时点」仅 _mr:121、MATRIX 0", lines_with(MR, "罕见（同根因双时点") == [121] and lines_with(MX, "罕见（同根因双时点") == [])
chk("「源读面」两件 0 命中", lines_with(MX, "源读面") == [] and lines_with(MR, "源读面") == [])

print("---- FAILS: %d %s" % (len(fails), fails))
