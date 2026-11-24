# -*- coding: utf-8 -*-
r"""_v12_rule.py -- V1(身份陈述) / V2(完成断言) 前置分类谓词（本任务设计件，v2）。

写域：lead/gate_v1v2_20261109/。零真机、零采样代码；只用 re / 静态文本。

输入契约：classify_v12(text, start, end, token)
输出：dict{verdict: V1|V2, hard:[...], weak:[...], override:..., unit, line,
          review_flag:bool, reason:str}

分析单元 U：表格行 => 命中所在单元格；散文 => 命中所在子句（。！？；\n 边界）。
上下文 L：命中所在整行（仅供表格/疑问/引证的同行判定）。

★ 四级判定（顺序不可调换）：
  S0 HARD_V1：命中在结构上不可能是断言谓语（疑问/引述占位/表格状态列/
     完成词做定语/紧邻否定或禁止管辖/条件选言分支支配）=> 无条件 V1。
  S1 V2_OVERRIDE：U 内出现硬性完成宣称，且未被紧邻否定/禁止管辖 => V2。
     （仅当 S0 未命中才生效；压过 WEAK_V1，防止「须注意：三值已实算已交付」混入）
  S2 WEAK_V1：规定式/清单待核，且支配词在命中的【前缀】内 => V1。
     （只认前缀，避免「三值已填，完全按要求」被后置「按要求」误放过）
  S3 DEFAULT：判不了 => 默认 V2（fail-closed，宁可误拦）+ review_flag=True 要求人工复核。
     ——「判不了」如实输出，不静默放过、不假装能判。

★ 同句混合规则（对应任务第二步 c）：
  HARD_V1 > V2_OVERRIDE > WEAK_V1 > DEFAULT(V2)。理由：
  落在疑问/引述/表格/定语/否定/分支里的完成词不可能充当断言谓语，故 HARD_V1 最优先；
  硬性完成宣称可伪装进规定式句子，故压过 WEAK_V1；
  两者同时出现时 hard/override 双标记一并回报供人工审计。
"""
import re

# ---- S1 硬性完成宣称词族（出现即 V2，除非紧邻否定/禁止管辖） ----
V2_OVERRIDE = (
    "现已", "已实算", "已复算", "已实跑", "已交付", "已闭合", "补登完成",
    "登记闭合", "填好了", "填好", "填毕", "已通过门禁", "已填三值", "已填并",
    "已提交给", "已填入登记件", "已填且", "已填：", "已填:", "登记完成",
    "已填完", "已提交完", "已补登完", "已签", "已落盘", "已入账", "已交付",
)
V2_OVERRIDE_RE = re.compile(r"已(按|照|依|经|由|将|把)[^。；|]{0,12}(填|登|交|录|签|算|盘)")

# ---- 紧邻否定 / 禁止管辖 ----
ADJ_NEG_CHARS = "不未无非勿没禁别"
PROHIBIT = ("不得", "不许", "禁止", "严禁", "切勿", "不可", "不代填", "未代填", "不代")
ADJ_NEG_RE = re.compile(r"(不得|不许|禁止|严禁|切勿|不可|不|未|无|非|勿|没|禁|别)[^。；|]{0,2}$")

# ---- S0 HARD_V1 词表 ----
H1_QUESTION = ("是否", "?", "？", "哪件", "需什么", "核什么", "与否")
H1_Q_CTX = ("是否已", "|", "表", "排查", "核对", "?", "？")
H2_QUOTE = ("占位符", "示例", "样例", "先例", "反例", "负测", "合成", "构造",
            "原文", "逐字", "要求「", "引文")
H3_TABLE_HDR = ("是否已填", "是否已", "需什么字段", "核什么", "判定条件",
                "关键拒绝条件", "是否已填")
H3_STATUS = ("未填", "部分（", "部分(", "不适用", "先例", "反例", "计划号",
             "非 C07 主体", "拒绝", "通过", "存疑")
H4_NOUN_RE = re.compile(r"^(件|路径|字段|值|状态|槽|模板|记录|声明|材料|文本|清单|表|项|的)")
H4_CTX = ("<", "占位", "命令", "参数", "复制", "替换", "按", "对", "将", "把",
          "写入", "路径", "回件", "示例", "样例", "须", "应", "照", "命令")
H6_BRANCH = ("→", "若", "则", "否则", "只有", "≠", "==", "≥", "≤", "判定条件",
             "处置：", "处置:", "拒绝项", "或")
H6_OR_COOCCUR = ("≥", "≤", ">", "<", "PASS", "判", "条件", "有", "须", "记载", "缺席", "处置")

# ---- S2 WEAK_V1 规定/清单（只认命中前缀） ----
W1_RE = re.compile(r"(应|须|必须|不得|应当|按[^。；|]{0,6}填用流程|填用流程|"
                   r"自检清单|人工自检|待核|规格|校验|只允许|只由|复制|替换)")
W1_NUM_RE = re.compile(r"^\s*\d+\.")

_CLAUSE_SEPS = "。！？；\n"


def _segment(line, rel, seps):
    cuts = [0] + [m.end() for m in re.finditer("[" + re.escape(seps) + "]", line)] + [len(line)]
    cuts = sorted(set(cuts))
    for a, b in zip(cuts, cuts[1:]):
        if a <= rel < b:
            return line[a:b], a
    return line, 0


def _unit_and_line(text, start, end, token):
    ls = text.rfind("\n", 0, start) + 1
    le = text.find("\n", end)
    if le == -1:
        le = len(text)
    line = text[ls:le]
    rel = start - ls
    is_table = line.lstrip().startswith("|")
    if is_table:
        bars = [m.start() for m in re.finditer(r"\|", line)]
        a, b = 0, len(line)
        for p in bars:
            if p <= rel:
                a = p + 1
            else:
                b = p
                break
        U, off = line[a:b], a
    else:
        U, off = _segment(line, rel, _CLAUSE_SEPS)
    return line, U, off, is_table, rel - off


def _strip_quotes(s):
    """剥去 「…」 与 `…` 引证跨度，避免引文里的「不得」被当作本句禁止管辖。"""
    s = re.sub(r"「[^」\n]*」", "", s)
    s = re.sub(r"`[^`\n]*`", "", s)
    return s


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


def classify_v12(text, start, end, token):
    line, U, off, is_table, rel_u = _unit_and_line(text, start, end, token)
    pre, post = U[:max(0, rel_u)], U[max(0, rel_u) + len(token):]
    hard, weak, override = [], [], ""
    U_bare = _strip_quotes(U)

    # ---- 管辖关系：紧邻否定 / 禁止（只在分析单元内，且剥去引证；不跨行污染） ----
    gov = h5_govern(pre, post)
    adj_neg = gov["adj_neg"]
    prohibit_U = gov["prohibit_governs"]
    double_neg = gov["double_neg"]

    # ---- S0 HARD_V1 ----
    # H1 疑问式：只认 U/前缀管辖（不跨子句；问号须在命中之后）
    h1_u = any(k in U for k in H1_QUESTION[:6]) or any(q in post for q in ("?", "？"))
    h1_pre = any(k in pre[-12:] for k in ("是否", "哪件", "需什么", "核什么", "与否"))
    if (h1_u or h1_pre) and (is_table or any(k in U for k in H1_Q_CTX)
                             or any(q in post for q in ("?", "？"))):
        hard.append("H1_疑问式")
    angle = ("<" in pre[-6:] and ">" in post[:16])
    quote = ("「" in pre and "」" in post) or ("`" in pre[-2:] and "`" in post[:2])
    if (angle or quote or any(k in U for k in H2_QUOTE) or any(k in line for k in H2_QUOTE)):
        hard.append("H2_引述占位")
    if is_table and (any(k in U for k in H3_TABLE_HDR) or any(k in line for k in H3_TABLE_HDR)
                     or any(k in U for k in H3_STATUS)):
        hard.append("H3_表格状态列")
    if H4_NOUN_RE.match(post) and (any(k in pre[-8:] for k in ("<",))
                                   or any(k in U for k in H4_CTX) or any(k in line for k in H4_CTX)):
        hard.append("H4_完成词做定语")
    if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:
        hard.append("H5_否定禁止管辖")
    h6 = any(k in U for k in H6_BRANCH) or any(k in line for k in H6_BRANCH)
    if "或" in U and any(k in U for k in H6_OR_COOCCUR):
        h6 = True
    if h6 and (is_table or any(k in U for k in ("处置", "判定", "拒绝", "条件", "清单")) or "→" in U or "若" in U):
        hard.append("H6_条件选言分支")

    if double_neg:
        return {"verdict": "V2", "hard": [], "weak": [],
                "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],
                "unit": U, "line": line, "review_flag": False,
                "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}
    if hard:
        return {"verdict": "V1", "hard": hard, "weak": [], "override": "",
                "unit": U, "line": line, "review_flag": False,
                "reason": "HARD_V1 结构：" + ",".join(hard) + "（完成词不可能充当断言谓语）"}

    # ---- S1 V2_OVERRIDE（仅当无 HARD_V1） ----
    hit_override = [k for k in V2_OVERRIDE if k in U]
    if V2_OVERRIDE_RE.search(U):
        hit_override.append("已(按|照|经|将)…(填|登|交|算)")
    if hit_override and not adj_neg and not prohibit_U and not double_neg:
        override = "V2_OVERRIDE:" + "/".join(dict.fromkeys(hit_override))
        return {"verdict": "V2", "hard": [], "weak": [], "override": override,
                "unit": U, "line": line, "review_flag": False,
                "reason": "U 内含硬性完成宣称，且未被紧邻否定/禁止管辖"}

    # ---- S2 WEAK_V1（只认前缀，防后置「按要求」误放过） ----
    if W1_RE.search(pre) or W1_NUM_RE.match(U) or W1_NUM_RE.match(line):
        weak.append("W1_规定式/清单待核(前缀支配)")

    if weak:
        return {"verdict": "V1", "hard": [], "weak": weak, "override": "",
                "unit": U, "line": line, "review_flag": False,
                "reason": "WEAK_V1：" + ",".join(weak)}

    # ---- S3 DEFAULT：判不了 -> fail-closed 默认 V2 + 人工复核 ----
    return {"verdict": "V2", "hard": [], "weak": [], "override": "",
            "unit": U, "line": line, "review_flag": True,
            "reason": "无任何 V1 形状、亦无硬性完成宣称：机器判不了，fail-closed 默认 V2（宁可误拦），须人工复核或改写为显式规定式"}
