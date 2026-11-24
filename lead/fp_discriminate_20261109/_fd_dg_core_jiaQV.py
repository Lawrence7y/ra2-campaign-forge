# -*- coding: utf-8 -*-
r"""_dg_core.py — 双重否定【构式生成】方案核心（只出设计，不改任何既有件）。

设计约束（来自任务书）：
  G-A 闭合：有限条部件集 + 有限条模板，不靠「无限加词」；部件集是封闭常量表。
  G-B 不误判两个独立否定短语：只在【同一微句、同一管辖链】内承认 N1…N2；
      跨子句/跨引证/跨并列/跨主语一律切断；不做否定词奇偶计数。
  G-C 与 R12 十式兼容：十式全部落在生成式语言内（真超集），十式字面枚举可保留作
      对账锚（可选，非必须）。
  G-D 零真机、零采样、只 re + 静态文本、无外部依赖、无文件 IO。

形式化（见 _dg_DESIGN.md 第二步）：
  N1 ∈ NEG1（前段否定/反问/周遍算子，闭合表）
  M  ∈ MID （情态/能愿/程度/系词/述谓桥，闭合表，含空串 ε）
  N2 ∈ NEG2（后段否定 / 否定谓语，闭合表）
  G  ∈ GAP（分离式受控间隔，闭合虚词表，含 ε）
  V  ∈ SCOPE_VERB（分离式辖域动词，闭合表）
  X  ∈ SPLIT_TAIL（分离式句末第二否定，闭合表）
  模板 T12（连写）：S ::= N1 · M · N2            —— 零通配字符
  模板 T3 （分离）：S ::= N1 · G · V · (¬B,≤4) · X  —— 唯一通配是受控补语
  作用域：S 只在【同一微句】内，且其后到 token 之间不得出现句界/逗号/转折/引号
          （由锚定到 pre 末尾的 lookahead 保证）；命中链内不得有第二主语或并列标记。
  语义约束：N1 必须【支配】N2 所在谓语（¬(¬P)），而不是两次各自独立的否定
            （¬P ∧ ¬Q）。这是与枚举法 / 奇偶法的分水岭。

本模块导出：
  NEG1/MID/NEG2/GAP/SCOPE_VERB/SPLIT_TAIL  闭合部件集
  dg_build_dropin_regex()  -> (compiled, pattern, stats)  【可粘贴】替换 :76 一行
  DG_DROPIN_RE / DG_PATTERN / DG_STATS
  dg_double_neg(pre, post="") -> dict   纯函数（带全部 G-B 约束）
  dg_scan(text, tokens) -> (problems, hits)  与 r12_scan 同签名的替身（不替换既有件）
"""
import re

# ==================== 闭合部件集（有限表；新增构式只能改表，不能增加规则条数） ====================
# NEG1：前段否定算子。含反问型 (岂/焉/哪/安能/何尝)、周遍否定型 (莫/无)。
NEG1 = (
    # 单字/基础否定
    "不", "没", "无", "非", "未", "莫", "勿", "别", "甭", "岂", "焉", "安", "谁说",
    # 判断/系词否定
    "并非", "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",
    # 时体/经验否定
    "未尝", "未曾", "未始", "未有", "何尝", "未免", "未必",
    # 能愿/情态否定
    "不能", "不可", "不得", "没有", "不敢", "不会", "不可能", "不该", "不应",
    "不准", "不宜", "不肯", "不屑", "不便", "不免", "不由得", "忍不住",
    "没法", "无法", "不见得", "不一定", "不否认", "并不",
    # 反问/周遍
    "岂能", "焉能", "哪能", "安能", "岂敢", "何能", "谁能", "莫不",
)
# MID：N1 与 N2 之间的成分。只收【虚词/情态/能愿/系词/述谓桥】，闭合表。
# ★ 刻意不收「但」：`不但不 / 非但不` 只有一个有效否定，是伪双重否定。
# ★ 刻意不收任何实词，`不闻不问 / 不卑不亢 / 不打不成交` 这类「两个独立否定」
#    在 MID 中无合法项，天然不匹配。
MID = (
    "",                                     # ε：莫不 / 无不 / 不无 / 并非不 / 未尝不
    "得", "能", "可", "谓", "为", "是",     # 不得不 / 不能不 / 不可不 / 不可谓不 / 不为不
    "会", "敢", "必", "免", "始", "尝", "曾", "有",
    "可能", "一定", "见得", "由得", "住",
    "得不", "说不", "说",                   # 不由得不 / 没说不 / 非说不
)
# NEG2：后段否定 / 否定谓语
NEG2 = (
    "不", "没", "没有", "毫无", "无", "未", "非", "莫", "别", "勿", "不是",
    "否认", "不承认", "不认为", "不宣告", "不出现",
    "不可", "不行", "不成", "不可谓", "不是说",
)
# GAP：T3 分离式 N1 与辖域动词之间的受控间隔（闭合虚词表，含 ε）
GAP = ("", "把", "将", "被", "让", "令", "以", "按", "照")
# SCOPE_VERB：T3 辖域动词（闭合表，仅完成/述谓动词）
SCOPE_VERB = (
    "宣告", "宣布", "宣称", "声称", "断言", "认定", "认为", "承认", "说", "写",
    "写成", "记作", "记为", "标为", "视作", "视为", "判为", "登记", "注明",
    "录入", "填", "登", "记", "签", "做", "算", "应用", "覆盖", "代填",
)
# T3 句末第二否定
SPLIT_TAIL = ("不可", "不行", "不成", "不可谓", "不罢休")

# 词汇化「伪双重否定」：形式上是 N1+ε+N2，但已是单词副词/连词，真值不是 ¬¬P。
# 用负向前瞻在正则内 veto（保证 .search() 的 bool 语义与 re.Pattern 完全一致）。
PSEUDO_DN = ("无非", "莫非", "莫不是", "不非", "没没", "无无", "非非",
             "没不", "不没", "非不", "没没不", "不不不")

# ==================== 边界/屏蔽（G-B 的关键） ====================
_BREAK = r"。！？；;，,、：:\n"
_BQ = r"。！？；;，,、：:\n「」『』“”`"
# 局域补语排除引号/句界/第二主语（分离式唯一的通配）
_SECOND = r"本笔|本件|本节|本回件|本候选|该笔|该件|此笔|台账|母本|本域|本轮|审阅回件|复核回件|第\s*\d+\s*笔"
DG_BREAK_RE = re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另")
DG_SECOND_SUBJ_RE = re.compile(r"(?:" + _SECOND + r")")
DG_COORD_RE = re.compile(r"[/／]|、|或|以及|同时|并且|一是|二是|其一|其二")
DG_QUOTE_RE = re.compile(r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`")


def _alt(words):
    """闭合表 → 正则选择支；长词在前，防短词先吃掉长词（'并不是不' vs '不是不'）。"""
    return "(?:" + "|".join(re.escape(w) for w in sorted(set(words), key=lambda x: (-len(x), x))) + ")"


def dg_build_dropin_regex():
    """★ 可粘贴：编译期由闭合部件表生成【一条】re.Pattern，语义与 re.compile 完全一致
    （.search(pre) 返回 Match 或 None），因此 _g7_predicates.py:92 / :144 调用点零改动。

    三条不变式（G-B 证明要点）：
      ① T12 = N1·M·N2，零通配字符；两个独立否定短语之间的实词/标点/主语
         不可能出现在闭合的 MID 中 ⇒ 拼不出跨短语匹配。
      ② T3 唯一通配是 (?:(?!第二主语)[^BQ]){0,4} —— 排除句界/引号/第二主语，
         不能跨子句、跨引证、跨主语搭桥。
      ③ 尾部锚定 (?=[^BQ]{0,24}$) —— 构式必须与 token 处于同一管辖微句，
         前一句/引号内的双重否定不污染当前 token。
      ④ 词首负向前瞻排除 PSEUDO_DN 词汇化伪构式。
      ⑤ 全程不数否定词奇偶（沿用 _g7_predicates.py:74-75 的结论）。
    """
    n1, mid, n2 = _alt(NEG1), _alt(MID), _alt(NEG2)
    gap, verb, tail = _alt(GAP), _alt(SCOPE_VERB), _alt(SPLIT_TAIL)
    veto = r"(?!(?:" + "|".join(re.escape(w) for w in PSEUDO_DN) + r"))"
    # 受控补语：≤4 字、不含句界/引号/第二主语
    comp = r"(?:(?!(?:" + _SECOND + r"))[^" + _BQ + r"]){0,4}?"
    # 同微句锚：构式之后到 pre 末尾（= token 起点）只允许 ≤24 个非句界/非引号字符。
    # 024 = 沿用 R10 NEG_WINDOW；「构式与 token 之间不得再起新句/新引文」。
    # ★ 注意：防「两个独立否定」的主证不是这一条，而是【闭合 MID】+ scope 切断 +
    #   引证屏蔽 + 第二主语/并列 veto（见 _dg_DESIGN.md 第二步(c) 的形式证明）。
    #   此处若在 N2 后强制要求辖域动词，会漏掉「并不否认 / 并非没有」这类
    #   N2 本身即否定谓语的构式（实测 _dg_step1.py 会退化），故不采用。
    govern = r"(?=[^" + _BQ + r"]{0,24}$)"
    t12 = r"(?P<t12>" + veto + n1 + mid + n2 + r")"
    t3 = r"(?P<t3>" + veto + n1 + gap + verb + comp + tail + r")"
    pattern = "(?:" + t12 + "|" + t3 + ")" + govern
    n_t12 = len(set(NEG1)) * len(set(MID)) * len(set(NEG2))
    n_t3 = len(set(NEG1)) * len(set(GAP)) * len(set(SCOPE_VERB)) * len(set(SPLIT_TAIL))
    return re.compile(pattern), pattern, {
        "n_neg1": len(set(NEG1)), "n_mid": len(set(MID)), "n_neg2": len(set(NEG2)),
        "n_gap": len(set(GAP)), "n_verb": len(set(SCOPE_VERB)), "n_tail": len(set(SPLIT_TAIL)),
        "n_pseudo_veto": len(set(PSEUDO_DN)),
        "cartesian_T12": n_t12, "cartesian_T3": n_t3, "cartesian_total": n_t12 + n_t3,
        "rule_count": 2,          # T12 / T3 —— 有限条，不随词表规模增长
        "pattern_chars": len(pattern),
        "wildcards": 1,           # 仅 T3 的受控补语；T12 零通配
    }


DG_DROPIN_RE, DG_PATTERN, DG_STATS = dg_build_dropin_regex()
# 对账锚：R12 原十式，逐字取自 _g7_predicates.py:76
R12_TEN = ("不得不", "并非不", "并不是不", "不是不", "无不",
           "没有不", "不无", "不能不", "不可不", "未曾不")


def _mask_quotes(s):
    """引证跨度内部置等长空格，保留开闭界符；未闭合开界符后截断。"""
    def blank(m):
        g = m.group(0)
        return g[0] + " " * (len(g) - 2) + g[-1]
    out = DG_QUOTE_RE.sub(blank, s)
    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`")):
        i = out.find(op)
        if i >= 0 and out.find(cl, i + 1) < 0:
            return out[:i + 1]
    return out


def _scope(s):
    """取最后一个微句边界之后的管辖前缀（跨句/跨逗号/跨转折/跨冒号一律切断）。"""
    cuts = [m.end() for m in DG_BREAK_RE.finditer(s)]
    return s[cuts[-1]:] if cuts else s


def dg_double_neg(pre, post=""):
    """纯函数：给定越权 token 的 pre/post（不含 token），判 pre 内是否存在
    【同微句、同管辖链】的双重否定构式。返回 dict（hit/hit_text/template/scope/reason）。
    """
    p = _mask_quotes(pre)
    scope = _scope(p)
    m = DG_DROPIN_RE.search(scope)
    if not m:
        return {"hit": False, "hit_text": "", "template": "", "scope": scope,
                "reason": "scope 内无 N1-M-N2 管辖链（或已被微句/引证/并列/距离切断）"}
    hit_text = m.group(0)
    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"
    if DG_SECOND_SUBJ_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含第二主语：两否定不互相支配"}
    if DG_COORD_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含并列标记：两个独立否定项"}
    return {"hit": True, "hit_text": hit_text, "template": tmpl, "scope": scope,
            "reason": "同微句内 N1 支配 N2（¬(¬P)），非两次独立否定"}


def dg_scan(text, tokens):
    """与 _g7_predicates.r12_scan 同签名的替身：(problems, hits)。
    仅用于本任务实跑对照；【不修改、不替换】既有 r12_scan。"""
    problems, hits = [], []
    for tok in tokens:
        for m in re.finditer(re.escape(tok), text):
            r = dg_double_neg(text[:m.start()], text[m.end():])
            if r["hit"]:
                problems.append("越权断言 %s（DG：%s 命中 %s）" %
                                (tok, r["template"], r["hit_text"]))
                hits.append({"token": tok, "pos": m.start(), "hit": r["hit_text"]})
    return problems, hits


if __name__ == "__main__":
    print("DG_STATS =", DG_STATS)
    print("R12_TEN all generated =", all(bool(DG_DROPIN_RE.search(c)) for c in R12_TEN))
    for s in ["不得不", "并非不", "亦非不", "未尝不", "莫不", "不敢不",
              "并非没有", "并不否认", "不是没有", "不可谓不", "岂能不",
              "无非", "莫非", "不闻不问", "非但不", "不但不",
              "无越权断言：本件不出现「可应用母本…」。"]:
        print("%-40s %s" % (s, bool(DG_DROPIN_RE.search(s))))

# --- 甲QV = 甲Q + 改代码（二次 veto 查整窗 scope） ---
# ===== _fd_ OVERRIDE (甲QV) : 由 _fd_setup.py 生成，原件正文一字未改 =====
import re as _fd_re
_FD_BREAK14 = ['其实', '说到底', '尽管', '换言之', '与此同时', '反倒', '结果', '终究', '总而言之', '归根结底', '话说回来', '退一步说', '哪怕', '说白了']
_FD_QUOTE_NEW = ['"[^"\\n]*"', '《[^》\\n]*》']
DG_BREAK_RE = _fd_re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另|" + "|".join(_fd_re.escape(w) for w in _FD_BREAK14))
DG_QUOTE_RE = _fd_re.compile(r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`" + "|" + "|".join(_FD_QUOTE_NEW))
def _mask_quotes(s):
    def blank(m):
        g = m.group(0)
        return g[0] + " " * (len(g) - 2) + g[-1]
    out = DG_QUOTE_RE.sub(blank, s)
    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`"),
                   ('"', '"'), ("《", "》")):
        i = out.find(op)
        if i >= 0 and out.find(cl, i + 1) < 0:
            return out[:i + 1]
    return out
def dg_double_neg(pre, post=""):
    p = _mask_quotes(pre)
    scope = _scope(p)
    m = DG_DROPIN_RE.search(scope)
    if not m:
        return {"hit": False, "hit_text": "", "template": "", "scope": scope,
                "reason": "scope 内无 N1-M-N2 管辖链"}
    hit_text = m.group(0)
    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"
    zone = scope
    why2 = "整窗内含第二主语"
    whyc = "整窗内含并列标记"
    if DG_SECOND_SUBJ_RE.search(zone):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": why2}
    if DG_COORD_RE.search(zone):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": whyc}
    return {"hit": True, "hit_text": hit_text, "template": tmpl, "scope": scope,
            "reason": "同微句内 N1 支配 N2"}
