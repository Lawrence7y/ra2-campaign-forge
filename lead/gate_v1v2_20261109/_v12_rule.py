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


def classify_v12(text, start, end, token):
    line, U, off, is_table, rel_u = _unit_and_line(text, start, end, token)
    pre, post = U[:max(0, rel_u)], U[max(0, rel_u) + len(token):]
    hard, weak, override = [], [], ""
    U_bare = _strip_quotes(U)

    # ---- 管辖关系：紧邻否定 / 禁止（只在分析单元内，且剥去引证；不跨行污染） ----
    adj_neg = bool(pre) and (pre[-1] in ADJ_NEG_CHARS or bool(ADJ_NEG_RE.search(pre)))
    prohibit_U = any(k in U_bare for k in PROHIBIT)

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
    if adj_neg or prohibit_U or "无已填" in U:
        hard.append("H5_否定禁止管辖")
    h6 = any(k in U for k in H6_BRANCH) or any(k in line for k in H6_BRANCH)
    if "或" in U and any(k in U for k in H6_OR_COOCCUR):
        h6 = True
    if h6 and (is_table or any(k in U for k in ("处置", "判定", "拒绝", "条件", "清单")) or "→" in U or "若" in U):
        hard.append("H6_条件选言分支")

    if hard:
        return {"verdict": "V1", "hard": hard, "weak": [], "override": "",
                "unit": U, "line": line, "review_flag": False,
                "reason": "HARD_V1 结构：" + ",".join(hard) + "（完成词不可能充当断言谓语）"}

    # ---- S1 V2_OVERRIDE（仅当无 HARD_V1） ----
    hit_override = [k for k in V2_OVERRIDE if k in U]
    if V2_OVERRIDE_RE.search(U):
        hit_override.append("已(按|照|经|将)…(填|登|交|算)")
    if hit_override and not adj_neg and not prohibit_U:
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
