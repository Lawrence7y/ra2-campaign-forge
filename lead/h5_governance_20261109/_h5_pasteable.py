# -*- coding: utf-8 -*-
r"""_h5_pasteable.py — H5 管辖关系修复【可粘贴片段】（只出设计，不改任何既有件）。

粘贴位置：lead/gate_v1v2_20261109/_v12_rule.py
  (P1) 整段插在 `def classify_v12(...)` 之前（即 :107 之后）；
  (P2) 用本件末尾 PATCH_NOTES 的四处替换改写 :114-116 / :135 / :143-146 之后 / :152。

本片段只用 re / 静态文本；零真机、零采样代码、无外部依赖、无文件 IO。
语义口径：V1 = 身份/否定陈述（门禁放过 PASS）；V2 = 完成断言（门禁抓 CATCH）。

被取代的旧实现（_v12_rule.py:112-116, :135, :152）：
    U_bare = _strip_quotes(U)
    adj_neg = bool(pre) and (pre[-1] in ADJ_NEG_CHARS or bool(ADJ_NEG_RE.search(pre)))
    prohibit_U = any(k in U_bare for k in PROHIBIT)          # ← 只问「U 内有无禁止词」
    ...
    if adj_neg or prohibit_U or "无已填" in U: hard.append("H5_否定禁止管辖")
    ...
    if hit_override and not adj_neg and not prohibit_U: ...
"""

import re

# ================= 常量（沿用 _v12_rule.py:41-43 的原始口径，片段自带以便独立粘贴） =========
H5_ADJ_NEG_CHARS = "不未无非勿没禁别"
H5_ADJ_NEG_RE = re.compile(
    r"(不得|不许|禁止|严禁|切勿|不可|不|未|无|非|勿|没|禁|别)[^。；|]{0,2}$")

# ---------- 双重否定表（R12 十式 + 实测漏式 + 分离型） ----------
# R12 十式逐字取自 lead/gate_fp7_20261108/_g7_predicates.py:76 DOUBLE_NEG_RE。
# 复用语义、不复用实现：本地超集 + 管辖微句作用域（理由见 _h5_DESIGN.md 第三步 c）。
H5_R12_TEN = (
    r"不得不|并不是不|并非不|不是不|不能不|不可不|未曾不|没有不|不无|无不"
)
H5_DN_EXTRA = (
    r"亦非不|未尝不|未始不|未有不|并非没有|并非毫无|不是没有|并不否认|"
    r"不可能不|不可谓不|不敢不|不会不|未必不|未免不|岂能不|焉能不|哪能不|不为不|莫不|"
    r"非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)"
)
# 长式在前，避免「并不是不」被「不是不」先吃掉
H5_DOUBLE_NEG_RE = re.compile("(" + H5_R12_TEN + "|" + H5_DN_EXTRA + ")")

# ---------- 前向辖域桥接：否定/禁止算子 + 辖域动词 + ≤24 字补语 ----------
# group(1)=算子, group(2)=辖域动词, group(3)=补语（token 落在补语末端）
H5_BRIDGE_RE = re.compile(
    r"((?:不代填|未代填|不得|不许|不可能|不可|禁止|严禁|切勿|未见|"
    r"不|未|无|非|勿|没|禁|别|莫))"
    r"(?:(?:[把将被让令以按照])[^，,；;。！？\n]{0,4}?)?"
    r"((?:宣告|宣布|宣称|声称|断言|认定|认为|承认|写成|记作|记为|标为|视作|"
    r"视为|当作|判为|登记|注明|录入|表明|代填|覆盖|应用|"
    r"填|写|记|说|做|见|算|盘|交|录|签))"
    r"([^，,；;。！？\n]{0,24})$"
)

# 微句边界（U 已按 。！？；\n 切过，这里补逗号级与转折级边界）
H5_MICRO_BREAK_RE = re.compile(r"[，,；;]|但|然而|不过|却|只是|反之|相反|另")
# 补语里出现「第二个独立主语」=> 已另起一句断言，桥接作废
H5_SELF_SUBJ_RE = re.compile(
    r"(?:本笔|本件|本节|本回件|本候选|该笔|该件|此笔|台账|母本|本域|本轮|第\s*\d+\s*笔)")
H5_CONTRAST_RE = re.compile(r"(?:但|然而|不过|却|只是|反之|相反)")

# 全句否定辖域框：句首否定标签 + token 后 40 字内谓语否定
H5_FRAME_HEAD_RE = re.compile(
    r"^\s*[^\u4e00-\u9fff]{0,4}"
    r"(?:不可能|未覆盖|未见|未做|未验|未发现|未含|无越权|非断言)")
H5_FRAME_POST_RE = re.compile(r"(?:未做|未覆盖|未见|没有|无须|无需|不用|未|无|非|不可能)")

# 引证屏蔽用（完整跨度置等长空格；未闭合开界符之后截断）
_H5_QUOTE_FULL = re.compile(r"「[^」\n]*」|『[^』\n]*』|`[^`\n]*`|“[^”\n]*”")
_H5_QUOTE_OPEN = "「『`“"
_H5_QUOTE_CLOSE = "」』`”"


def _h5_mask_quotes(pre):
    """G4 引证屏蔽：把引证跨度【内部】置为等长空格，但保留开/闭界符本身，
    使「禁止填「已生效」字样」里的 `填「` 仍能接上桥接动词；
    未闭合开界符之后的整段截断（token 落在引文内时由 H2_引述占位负责）。"""
    def blank(m):
        s = m.group(0)
        return s[0] + " " * (len(s) - 2) + s[-1]
    s = _H5_QUOTE_FULL.sub(blank, pre)
    for op in _H5_QUOTE_OPEN:
        i = s.find(op)
        if i < 0:
            continue
        j = s.find("」" if op == "「" else "』" if op == "『" else op, i + 1)
        if j < 0:
            return s[:i + 1]
    return s


def _h5_last_micro(s):
    """G2 跨子句不管辖：取最后一个微句边界之后的管辖前缀。"""
    cuts = [m.end() for m in H5_MICRO_BREAK_RE.finditer(s)]
    return s[cuts[-1]:] if cuts else s


def _h5_no_second_subject(tail):
    """补语内只允许「紧贴现语动词的直接宾语」（≤2 字），再远的主语视为另起断言。"""
    return not any(m.start() > 2 for m in H5_SELF_SUBJ_RE.finditer(tail))


def h5_govern(pre, post):
    """H5 管辖判定主入口。pre/post = 分析单元 U 内 token 的前/后缀（不含 token）。

    返回 dict：
      adj_neg           紧邻否定（形状 a，沿用原语义）
      prohibit_governs  前向禁止/否定【真的管辖该 token】（形状 b/c；取代旧 prohibit_U）
      double_neg        管辖微句内双重否定=肯定（取消豁免并强制 CATCH）
      dn_hit            命中的双重否定构式
      shapes            命中的形状清单（审计可追溯）
      scope             实际参与判定的管辖前缀

    三条硬约束：G1 前向（算子只在 pre，post 里的不得/禁止一律不管辖）；
    G2 同微句（逗号/分号/转折之后重取前缀）；G3 有辖域路径（紧邻 / 桥接 / 辖域框），
    不是「只看距离」。
    """
    p = _h5_mask_quotes(pre)
    scope = _h5_last_micro(p)

    # ---- G5 双重否定：只在管辖微句内识别，不做否定词奇偶计数 ----
    dm = H5_DOUBLE_NEG_RE.search(scope)
    double_neg = bool(dm)
    dn_hit = dm.group(0) if dm else ""

    # ---- 形状 a：紧邻管辖（≤2 字） ----
    adj_neg = bool(p) and (p[-1] in H5_ADJ_NEG_CHARS
                           or bool(H5_ADJ_NEG_RE.search(p)))

    # ---- 形状 b：辖域动词桥接（长距前向管辖，≤24 字补语，无微句边界） ----
    shapes = []
    if adj_neg:
        shapes.append("a_紧邻")
    bm = H5_BRIDGE_RE.search(scope)
    bridge = False
    if bm:
        tail = bm.group(3)
        bridge = (len(tail) <= 24 and _h5_no_second_subject(tail)
                  and not H5_CONTRAST_RE.search(tail))
        if bridge:
            shapes.append("b_桥接:" + bm.group(1) + bm.group(2))

    # ---- 形状 c：全句否定辖域框（句首否定标签 + 谓语否定） ----
    frame = (bool(H5_FRAME_HEAD_RE.search(p))
             and bool(H5_FRAME_POST_RE.search(post[:40])))
    if frame:
        shapes.append("c_辖域框")

    return {"adj_neg": adj_neg,
            "prohibit_governs": bool(bridge or frame),
            "double_neg": double_neg, "dn_hit": dn_hit,
            "shapes": shapes, "scope": scope}


# ================= PATCH_NOTES：四处精确替换（供 _h5_patch.py 机械施加） ================
# ① :114-116 →
#     # ---- H5 补丁：管辖 = 前向 + 同微句 + 有辖域路径 + 非双重否定 ----
#     gov = h5_govern(pre, post)
#     adj_neg = gov["adj_neg"]
#     prohibit_U = gov["prohibit_governs"]
#     double_neg = gov["double_neg"]
# ② :135 →
#     if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:
#         hard.append("H5_否定禁止管辖")
#    （原文 :135-136 两行；改条件即可，append 行不动）
# ③ 在 :143 `if hard:` 之前插入（必须【之前】：若放在 return 之后即成死代码；
#    且双重否定=肯定应压过其余 HARD_V1 结构理由）：
#     if double_neg:
#         return {"verdict": "V2", "hard": [], "weak": [],
#                 "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],
#                 "unit": U, "line": line, "review_flag": False,
#                 "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}
# ④ :152 →  if hit_override and not adj_neg and not prohibit_U and not double_neg:
# 另：把本文件全文（除模块 docstring 外）插到 `def classify_v12` 之前。
