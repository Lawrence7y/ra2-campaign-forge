# -*- coding: utf-8 -*-
"""
R16-SIEVE-D1-WIDE · D1 的「② 有独立审计链」完整集合筛选器（只读；只写本目录）

判定口径 = 用户 D-52 宽读口径
--------------------------------------------------------------------------
D-52 原文（卡面 §3 照录）：
  宽读：`*_audit/VERDICT.md` 与 `NAMED_PUSH_AUDIT*/verdict.tsv` 等值，任何独立于
  ② 与 ④ 产出方的审计产物都算独立审计链。

本脚本把该口径落成下面 5 条可执行判据（S1..S5），每条都在代码里实现，
报告里出现的每个数字都由这些函数算出，不靠散文。

S1【审计产物枚举】独立审计产物 = 满足全部三点的文件：
   (a) 路径中至少有一个**目录段**名字含 audit/AUDIT（大小写不敏感）——
       覆盖 `_audit/`、`NAMED_PUSH_AUDIT*/`、`AUDIT_*/`、`R16_AUDIT_*/`、`R4_FILL_AUDIT/`；
   (b) 文件名是 `VERDICT.md` 或 `verdict.tsv`；
   (c) 不在本卡写域内（自己的产物不算）。
   ⇒ 卡面 §3.3「排除产出方自己的 EVIDENCE/ 与 REPORT.md」由 (b) 自动保证：
     产出方自述文件名是 EVIDENCE/*、REPORT.md 而非 VERDICT.md/verdict.tsv；
     且 `<card>/EVIDENCE/...` 没有 audit 目录段，双重排除。

S2【条目级判定记录】对 entry e，在审计产物 A 里找「以 e 为主体」的判定单元 U。
   判定单元 = 表格行 / 标题行 / 列表项 / 段落。主体判定（防止「提及」被当「判定」）：
   - 表格行：e 必须出现在**第一个单元格**（表格的 entry 列）；
   - 其余单元：e 作为 8 位十六进制 token 出现，且**紧跟其前的 16 字符不是引用/调用前缀**
     （call / jmp / → / -> / @ / 见 / 来源 / 参见 / 依据 / 引自 / site / 指向 / 调用）；
   - 另：单元内必须出现**判决词**（S3）。

S3【判决词】单元内出现明确的结论词（PASS/FAIL/成立/不成立/已证/白名单/黑名单/并入/
   应并入/应升/保留/退回/退级/作废/通过/不符/排除/维持/确认/命中 …）。
   ⇒ 只有判决词、没有身份证据的单元不算（那是「提及」）。

S4【② 类身份前提】单元内（或该单元所属表格表头）出现**类身份证据**：
   RTTI / .?AV… / COL / TD / vt=或 vt[ / 虚表 / 活 vptr / vtable / slot 或槽 /
   类属 / 类名 / 归属 / 类身份 / 类前缀 / vt 号 + slot 号（如 `7E1E84 / 4`）。
   对 verdict.tsv（结构化审计表）另走一条等价通道：`ring2_at` 列非空且内容实质
   （含 vt=/COL/TD/.?AV/槽/slot 之一）即视为 ② 已被独立判定 —— 这就是
   `NAMED_PUSH_AUDIT*/verdict.tsv` 与 `*_audit/VERDICT.md` 等值的落点（D-52）。

S5【② 不被否定】若同一 entry 的主体单元里出现**身份否定式**（类归属错误 / 类前缀与事实
   不符 / 错的是类前缀 / ② 不成立 / 无 RTTI / 归属错误 / 不是该类 / 与行名类不符 /
   该类无此槽），则该审计记录判 REFUTED，**不计入**集合（审计否掉了 ②，不是建立了链）。
   同一 (产物, entry) 内 REFUTED 优先于 SUPPORTED。

集合定义：
   e ∈ SIEVE_ALL  ⟺  ∃ 独立审计产物 A，A 里存在以 e 为主体、带判决词、带类身份证据、
                       且未被身份否定式推翻的记录。
   输出还会同时给出正向子集（判决含 PASS/并入/成立/白名单…）与否定判决旗标，
   便于 Lead 判断哪些行可以直接进 ④ 批次、哪些要先修身份。

复跑：python sieve.py     （只读 R14 下的审计产物与 coverage/final.tsv；只写本目录）
"""
import io
import os
import re
import sys
import collections
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
COV_LIVE = os.path.join(R14, "COVERAGE", "coverage.tsv")
D1_FIELDS = os.path.join(R14, "R16_D1_FINAL", "fields.tsv")
D1_DELTA = os.path.join(R14, "R16_D1_FINAL", "delta.tsv")
EXE_SHA_EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

# ------------------------------------------------------------------ S1 审计产物枚举
NAME_OK = ("VERDICT.md", "verdict.tsv")
AUDIT_SEG = re.compile(r"(?i)audit")


def list_audit_artifacts():
    """S1：返回 [(rel_path, abspath)]，按 rel 升序。"""
    out = []
    for dp, dn, fn in os.walk(R14):
        for f in sorted(fn):
            if f not in NAME_OK:
                continue
            ap = os.path.join(dp, f)
            rel = os.path.relpath(ap, R14)
            segs = rel.split(os.sep)[:-1]
            if not segs:
                continue
            if not any(AUDIT_SEG.search(s) for s in segs):
                continue
            top = segs[0]
            if top == "R16_SIEVE_D1_WIDE":       # 自己的写域，不算审计
                continue
            out.append((rel, ap))
    out.sort()
    return out


# ------------------------------------------------------------------ 词表（S3/S4/S5）
ADDR = re.compile(r"(?<![0-9A-Za-z])(?:0x)?([0-9A-Fa-f]{8})(?![0-9A-Za-z])")

# S2 引用/调用前缀：命中则说明该地址是「被引用的对象/站点」而不是「被判决的主体」
CITE_PRE = re.compile(
    r"(?:call|jmp|push|→|->|@|见|来源|参见|依据|引自|cited|ref|caller|callee|"
    r"site|指向|调用|被调|体内|宿主|锚|目标|位于)\s*[\s`*'\"（(：:]*$", re.I)

# 引用语境：整行属于「拿这些地址当例子/先例/对照」而不是在判它们。
# 分两档：强标记（出现在任何位置都算引用）与弱标记（只在行首 25 字内才算，
# 否则「槽位有基线」这种正文里出现「基线」会被误伤，见 S13_K4:17）。
MENTION_STRONG = re.compile(r"(先例|例如|如\s|遗留|引述|不能作为)")
MENTION_WEAK = re.compile(r"(对照|基线|反向检查|抽检|样本)")


def is_mention_context(body):
    if MENTION_STRONG.search(body):
        return True
    return bool(MENTION_WEAK.search(body[:25]))


# S3 判决词
V_POS = ["PASS", "成立", "已证", "白名单", "并入", "应升", "保留", "通过", "可升",
         "确认", "命中", "一致", "无误", "可接受", "可凭", "成立"]
V_NEG = ["FAIL", "不成立", "退回", "退级", "降级", "黑名单", "不入", "不得并入",
         "不可并入", "不予并入", "作废", "不符", "排除", "误", "矛盾", "过度纠正"]
VERDICT_TOK = re.compile(
    r"(不可并入|不得并入|不入白名单|不予并入|应剔|不成立|FAIL|PASS|白名单|黑名单|"
    r"应并入|可并入|并入|应升|可升|成立|已证|保留|退回|退级|降级|作废|通过|"
    r"不符|排除|维持|确认|命中|一致|可接受|可凭)", re.I)

# 表格的「裁决列」简写：白 / 黑 / 白·条件 / 白（…）/ **白** 之类。
# 只在表格行的**最后一个单元格**上认，避免把正文里的「空白」当成裁决。
CELL_VERDICT = re.compile(r"^[\s*`]*(白|黑)(?:[·（(].*)?$")

# S4 ② 类身份证据
ID_POS = re.compile(
    r"(RTTI|\.\?A|(?<![A-Za-z])COL(?![A-Za-z])|(?<![A-Za-z])TD(?![A-Za-z+])|"
    r"vt\s*[-=]|vt\[|虚表|活\s*vptr|vptr|vtable|slot|槽|类属|类名|归属|类身份|类前缀|"
    r"0x[0-9A-Fa-f]{6,8}\s*\[|[0-9A-Fa-f]{6,8}\s*/\s*\d+)", re.I)

# 「全表枚举」形态：`004AB9B0 在 **DisplayClass 0x7E6114[48]**` —— 审计在逐表枚举持有表，
# 这种写法里地址同样是主体（不是被引用的站点）。
ENUM_FORM = re.compile(r"\s*(?:在|位于)\s*\**\s*[A-Za-z_][\w:<>,* ]{0,40}?\s*0x[0-9A-Fa-f]{6,8}"
                       r"\s*\[")

# S5 身份否定式
ID_NEG = re.compile(
    r"(类归属错误|归属错误|类前缀与事实不符|类前缀应|错的是类前缀|②\s*不成立|"
    r"无\s*RTTI|RTTI\s*不可|不是该类|与行名类不符|该类无此槽|"
    r"类名不符|归属不符|非该类|类前缀不对|②\s*该.{0,6}行?不合格)")

# 子句边界：句号/分号/冒号之后另起一句时，句首地址也是主体（一行里可判多个条目）
CLAUSE_START = re.compile(r"(?:^|[。；;：:！!？?])\s*[\s`*'\"（(]*$")

CITE_WINDOW = 16

# ---------------------------------------------------------------------------------
# 人工复核否决表（DEFERRED：判据的一部分，不是散文）
# 键 = (entry, 产物相对路径, 行号)，值为该行为什么**不算** ② 判定（提及/判的是别的环）。
# 这张表是本卡 §4.4 反向核的落地：逐行打开审计原文后确认「该行只是在提这个地址」的，
# 在这里显式剔除；剔除后仍无其它审计记录支撑的条目会自然出集合。
# ---------------------------------------------------------------------------------
DROP_RECORD = {
    ("0043F180", "M3_merge/_audit/VERDICT.md", 27):
        "合并审计在讲 grade 冲突（0043F180 只是被举例为「表中 grade 高于本轮断言」），判的不是②",
    ("00473B10", "S03_C5/_audit/VERDICT.md", 35):
        "该节判 ③b① 档位与偏移纠错，未判类身份；类身份判定在同文件 :23 的逐行表"
        "（② 列「仅 0x7E16B0 slot9 CCFileClass」），引用改指 :23",
    ("00473B10", "S03_C5/_audit/VERDICT.md", 32):
        "该行是「表长约束把后表字段当自表槽」的取槽方法检验，判的不是该行类身份",
    ("004AB9B0", "M4_merge/_audit/VERDICT.md", 23):
        "该行判的是语义栏措辞（「已降[未证]」是否属实），不是②类身份",
    ("004D27C0", "S10_K4/_audit/VERDICT.md", 31):
        "该行是对已证行做字节+grade 抽核（b878000000c3 已证 ✓），未独立定类属",
    ("004D8FB0", "S10_K10/_audit/VERDICT.md", 6):
        "该节判环①（选择子表长度）与「②被调 grade」，此②指被调方档位、非类身份",
}

# 「批量清单判决」词：只认**清单式结论**（白名单/可留/应并入/维持/成立/不成立/PASS/FAIL…），
# 不认泛泛出现的「已证」——「已证」常出现在「先例已 [已证]」这类纯引述里。
LIST_VERDICT = re.compile(
    r"(不入白名单|不可并入|不得并入|不予并入|黑名单|应剔|不成立|FAIL|白名单|可留|"
    r"可并入|应并入|并入|维持|排除|退回|退级|降级|保留|应升|可升|成立|PASS)")

LIST_NEG_TOKS = ("不入白名单", "不可并入", "不得并入", "不予并入", "黑名单",
                 "应剔", "不成立", "FAIL", "排除", "退回", "退级", "降级")

# 强判决词：用于「同一 (entry, 产物) 有多行可引时，引结论最硬的那行」
STRONG_VERDICT = re.compile(
    r"(白名单|黑名单|可并入|应并入|并入|应升|保留|退回|退级|PASS|FAIL|成立|不成立|排除|维持)")

# 身份硬词：最贴着「类身份」的写法（用于在同类候选行里优先引真正判 ② 的那行）
IDENT_HARD = re.compile(r"(类归属|类属|类名|RTTI|vt\[|vt\s*[-=]|虚表|COL|持有表|slot|槽)")

# 批量清单里地址之间的分隔：只允许空白 / 斜杠 / 顿号 / 逗号 / 顿点（不得有其他词）
LIST_SEP = re.compile(r"^[\s/、,，`*]*$")


def addr_hits(text):
    """返回 [(pos, ENTRY)]，仅 8 位大写十六进制。"""
    return [(m.start(), m.group(1).upper()) for m in ADDR.finditer(text)]


def is_batch_list(text, hits):
    """S2/L2：该单元是不是「结论词 + 一串地址」的批量清单。
    条件：≥3 个地址 + 至少两对地址之间除分隔符外无其他字符 + 单元含清单式结论词。"""
    if len(hits) < 3:
        return False
    adjacent = 0
    for (p1, _e1), (p2, _e2) in zip(hits, hits[1:]):
        if LIST_SEP.match(text[p1 + 8:p2]):
            adjacent += 1
    return adjacent >= 2 and bool(LIST_VERDICT.search(text))


# ------------------------------------------------------------------ 单元切分
SEP_ROW = re.compile(r"^\|[\s:|-]+\|?$")


def md_units(text):
    """把 VERDICT.md 切成判定单元。kind ∈ {table_row, heading, line}。
    table_row 带 header（该表第一行非分隔行）；line 另附 paragraph 归并后的整段文本。"""
    lines = text.splitlines()
    units = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            j = i
            block = []
            while j < n and lines[j].strip().startswith("|"):
                block.append((j + 1, lines[j]))
                j += 1
            hdr = ""
            for _no, b in block:
                if not SEP_ROW.match(b.strip()):
                    hdr = b
                    break
            for no, b in block:
                if SEP_ROW.match(b.strip()):
                    continue
                units.append(dict(line=no, text=b, kind="table_row", header=hdr))
            i = j
            continue
        if s.startswith("#"):
            units.append(dict(line=i + 1, text=raw, kind="heading", header=""))
            i += 1
            continue
        # 段落归并：连续的普通行合成一个 paragraph 单元，同时保留单行单元
        j = i
        seg = []
        while j < n:
            t = lines[j].strip()
            if not t or t.startswith("|") or t.startswith("#"):
                break
            seg.append((j + 1, lines[j]))
            j += 1
        para_txt = "\n".join(x[1] for x in seg)
        for no, b in seg:
            units.append(dict(line=no, text=b, kind="line", header="", para=para_txt,
                              para_line=no))
        i = max(j, i + 1)
    return units


def is_subject(unit, pos, entry):
    """S2 主体判定。"""
    text = unit["text"]
    if unit["kind"] == "table_row":
        cells = [c.strip() for c in text.strip().strip("|").split("|")]
        if not cells:
            return False
        first = cells[0].replace("*", "").replace("`", "").strip()
        return bool(re.match(r"^(?:0x)?%s$" % entry, first, re.I))
    pre = text[max(0, pos - CITE_WINDOW):pos]
    if CITE_PRE.search(pre):
        return False
    hits = unit.get("hits") or addr_hits(text)
    if hits and hits[0][1] == entry:
        # L1：该条目是单元里的**第一个**地址 ⇒ 它是这句话的主体
        return True
    if CLAUSE_START.search(text[:pos]):
        # L1b：条目位于一个子句的句首（分号/冒号/句号之后）⇒ 它也是主体
        return True
    if ENUM_FORM.match(text[pos + 8:pos + 70]):
        # L1c：全表枚举形态「<addr> 在 <Class> 0x…[slot]」⇒ 该地址是枚举主体
        return True
    # L2：批量清单（结论词 + 一串地址），清单内每个地址都是主体
    if unit.get("batch"):
        return True
    return False


def unit_identity(unit):
    """S4：该单元是否带类身份证据（表格行可借表头）。"""
    if ID_POS.search(unit["text"]):
        return True
    if unit["kind"] == "table_row" and unit.get("header"):
        return bool(ID_POS.search(unit["header"]))
    return False


def near_polarity(text, pos):
    """返回离 pos 最近的判决词的极性：'POS' / 'NEG' / None。"""
    best = None
    for m in VERDICT_TOK.finditer(text):
        tok = m.group(1)
        d = abs(m.start() - pos)
        pol = "NEG" if any(t.lower() in tok.lower() for t in V_NEG) else "POS"
        if best is None or d < best[0]:
            best = (d, pol)
    return best[1] if best else None


# ------------------------------------------------------------------ 记录抽取
def records_from_md(rel, text):
    """S2..S5 的 md 侧实现。返回 record 列表。"""
    units = md_units(text)
    for u in units:
        u["hits"] = addr_hits(u["text"])
        u["batch"] = (u["kind"] == "line" and is_batch_list(u["text"], u["hits"]))
    # 文档级：以该 entry 为标题主体、且标题带身份证据 ⇒ 该条的 ② 在本产物里有独立定界
    head_ident = set()
    head_neg = set()
    for u in units:
        if u["kind"] != "heading":
            continue
        for pos, ent in u["hits"]:
            if CITE_PRE.search(u["text"][max(0, pos - CITE_WINDOW):pos]):
                continue
            if ID_POS.search(u["text"]):
                head_ident.add(ent)
            if ID_NEG.search(u["text"]):
                head_neg.add(ent)
    doc_ident = bool(ID_POS.search(text))

    out = []
    for u in units:
        body = u["text"]
        if not u["hits"]:
            continue
        if u["kind"] == "heading":
            continue          # 标题只提供身份定界，本身不作判决单元
        # 主体集合（供 ID_NEG 归属用）
        subs = [(p, e) for p, e in u["hits"] if is_subject(u, p, e)]
        if not subs:
            continue
        # S5：每个身份否定式只归给**离它最近的主体地址**（一行里常有多个地址，
        # 否定句说的是其中一个，不能整行连坐）
        neg_owner = set()
        for m in ID_NEG.finditer(body):
            best = min(subs, key=lambda pe: abs(pe[0] - m.start()))
            neg_owner.add(best[1])
        mention_only = is_mention_context(body)
        if mention_only:
            continue          # 引用语境（举例/先例/对照/基线）不算判定
        for pos, ent in subs:
            # S3 判决词
            cell_v = None
            if u["kind"] == "table_row":
                cells = [c.strip() for c in body.strip().strip("|").split("|")]
                if cells:
                    m = CELL_VERDICT.match(cells[-1])
                    if m:
                        cell_v = m.group(1)
            if not VERDICT_TOK.search(body) and cell_v is None:
                continue
            # S4 身份前提
            ident = unit_identity(u)
            if not ident and ent in head_ident:
                ident = True
            if not ident and u["batch"] and doc_ident:
                # 批量清单 + 该产物整体带身份复算 ⇒ 清单成员共享该身份判定
                ident = True
            if not ident:
                continue
            # 极性
            if u["batch"]:
                m = LIST_VERDICT.search(body)
                if m:
                    pol = "NEG" if m.group(0) in LIST_NEG_TOKS else "POS"
                else:
                    pol = near_polarity(body, pos)
            else:
                pol = near_polarity(body, pos)
            if cell_v is not None and pol is None:
                pol = "POS" if cell_v == "白" else "NEG"
            neg_id = (ent in neg_owner) or (ent in head_neg)
            out.append(dict(entry=ent, line=u["line"], quote=body.strip(),
                            kind=("batch" if u["batch"] else u["kind"]),
                            polarity=pol, id_neg=neg_id,
                            strength=(2 if STRONG_VERDICT.search(body) else 1),
                            width=len(u["hits"])))
    return out


def records_from_tsv(rel, text):
    """verdict.tsv：结构化审计表。entry 列 = 主体；ring2_at 列 = ② 判定（S4 等价通道）。"""
    L = text.splitlines()
    if not L:
        return []
    hdr = [h.strip() for h in L[0].split("\t")]
    if "entry" not in hdr:
        return []
    ie = hdr.index("entry")
    ir2 = hdr.index("ring2_at") if "ring2_at" in hdr else None
    iv = hdr.index("verdict") if "verdict" in hdr else None
    out = []
    for k, ln in enumerate(L[1:], start=2):
        c = ln.split("\t")
        if len(c) < len(hdr):
            continue
        ent = c[ie].strip().upper()
        if not re.match(r"^[0-9A-F]{8}$", ent):
            continue
        r2 = c[ir2].strip() if ir2 is not None else ""
        ident = bool(r2) and r2 not in ("-", "无", "N/A", "n/a") and bool(ID_POS.search(r2))
        if not ident:
            continue
        pol = None
        if iv is not None:
            v = c[iv].strip().upper()
            if v.startswith("PASS") or v in ("OK", "YES"):
                pol = "POS"
            elif v.startswith("FAIL") or v in ("NG", "NO"):
                pol = "NEG"
        neg_id = bool(ID_NEG.search(r2))
        out.append(dict(entry=ent, line=k, quote=(r2[:150] if r2 else c[iv] if iv is not None else ""),
                        kind="tsv_row", polarity=pol, id_neg=neg_id,
                        strength=2, width=1))
    return out


# ------------------------------------------------------------------ inputs
def read_tsv(p):
    L = io.open(p, encoding="utf-8-sig", newline="").read().splitlines()
    hdr = L[0].split("\t")
    rows = []
    for ln in L[1:]:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= len(hdr):
            rows.append(dict(zip(hdr, c)))
    return hdr, rows


def load_coverage_sem():
    """coverage.tsv：表头用逗号、数据行用 tab（盘上既有不一致，见 S13_K9 审计 §6）。
    返回 entry -> dict(subsystem, name, sem, grade)。"""
    L = io.open(COV_LIVE, encoding="utf-8-sig").read().splitlines()
    d = {}
    for ln in L[1:]:
        c = ln.split("\t")
        if len(c) != 8:
            continue
        d[c[0].strip().upper()] = dict(subsystem=c[1], name=c[2], sem=c[3],
                                      grade=c[4], ev=c[5], ns=c[6], conflict=c[7])
    return d


def main():
    # ---- §4.1 复现 D1
    _h, rows = read_tsv(FINAL)
    d1 = [r for r in rows if r["has_ring4"] == "D1"]
    d1_entries = []
    seen = set()
    for r in d1:
        e = r["entry"].strip().upper()
        if e not in seen:
            seen.add(e)
            d1_entries.append(e)
    d1_entries.sort()
    d1_set = set(d1_entries)

    cov = load_coverage_sem()

    # ---- 已做集合（17）与其 delta 子集（5）
    _h2, f17 = read_tsv(D1_FIELDS)
    set17 = {r["entry"].strip().upper() for r in f17}
    _h3, d5 = read_tsv(D1_DELTA)
    delta5 = {r["entry"].strip().upper() for r in d5}

    # ---- S1 枚举 + S2/S3/S4/S5 抽记录
    arts = list_audit_artifacts()
    all_recs = []          # list of dict(rel, entry, line, quote, kind, polarity, id_neg)
    dropped = []
    art_kind = collections.Counter()
    for rel, ap in arts:
        try:
            text = io.open(ap, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        recs = (records_from_tsv(rel, text) if rel.lower().endswith(".tsv")
                else records_from_md(rel, text))
        art_kind[rel.lower().rsplit(".", 1)[-1]] += 1
        for r in recs:
            if r["entry"] in d1_set:
                r["rel"] = rel
                key = (r["entry"], rel.replace(os.sep, "/"), r["line"])
                if key in DROP_RECORD:
                    dropped.append((key, DROP_RECORD[key]))
                    continue
                all_recs.append(r)

    # ---- 按 (entry, rel) 聚合：S5 身份否定**全局优先**
    # 一个独立审计已把该条的类身份否掉 ⇒ 不存在「建立 ② 的审计链」，该条整条出局，
    # 即使另一份审计给过正面判定（两份冲突时按 S5 从严，并在报告里单列冲突明细）。
    per = collections.defaultdict(list)
    for r in all_recs:
        per[(r["entry"], r["rel"])].append(r)

    supported = collections.defaultdict(list)   # entry -> [(rel, rec)]
    refuted = collections.defaultdict(list)
    for (ent, rel), rs in per.items():
        if any(x["id_neg"] for x in rs):
            refuted[ent].append((rel, [x for x in rs if x["id_neg"]][0]))
            continue
        # 同一 (entry, 产物) 的全部记录都保留，引用时再按硬/窄/正面挑最贴的那条
        for x in rs:
            supported[ent].append((rel, x))

    # S5 全局优先：被任一独立审计否掉身份的条目，从集合中剔除（冲突另表登记）
    sieve_all = sorted(e for e in supported if e not in refuted)
    refuted_entries = sorted(refuted)
    refuted_conflict = sorted(e for e in refuted if e in supported)

    # 引用证据排序：
    #   ① 一手审计优先于 R16_AUDIT_* 元审计（后者只是在转述前面的审计）；
    #   ② 结论最硬的行优先（白名单/并入/成立/保留/PASS…）；
    #   ③ 正面判决优先于否定判决；
    #   ④ 清单越窄越优先（11 行的白名单优于 149 行的白名单 —— 越窄越贴着这一条）；
    #   ⑤ 逐条形态（表格行/单行）优先于批量清单。
    KIND_PRIO = {"tsv_row": 0, "table_row": 0, "line": 1, "batch": 2}
    POL_RANK = {"POS": 0, None: 1, "NEG": 2}

    def cite_key(item):
        rel, rec = item
        rel_u = rel.replace(os.sep, "/")
        is_meta = 1 if rel_u.startswith("R16_AUDIT_") else 0
        ident_hard = 0 if IDENT_HARD.search(rec.get("quote", "")) else 1
        return (is_meta, ident_hard, -rec.get("strength", 1), POL_RANK.get(rec["polarity"], 3),
                rec.get("width", 1), KIND_PRIO.get(rec["kind"], 3), rel_u, rec["line"])

    for e in supported:
        supported[e].sort(key=cite_key)

    # ---- 正向子集（判决 POS 或未给判决）
    pos_entries = set()
    for ent in sieve_all:
        for _rel, rec in supported[ent]:
            if rec["polarity"] in (None, "POS"):
                pos_entries.add(ent)
                break

    def has4_disk(e):
        return "④" in cov.get(e, {}).get("sem", "")

    # ---- 主表 sieve_all.tsv
    hdr_out = ["entry", "subsystem", "name", "audit_file", "audit_line", "audit_quote",
               "has_ring4_on_disk(是/否)", "overlap_with_17(是/否)", "overlap_with_5(是/否)",
               "verdict_polarity", "n_supporting_artifacts"]
    lines = ["\t".join(hdr_out)]
    detail = {}
    for e in sieve_all:
        cr = cov.get(e, {})
        rel, rec = supported[e][0]
        detail[e] = (rel, rec)
        lines.append("\t".join([
            e, cr.get("subsystem", ""), cr.get("name", ""),
            rel.replace(os.sep, "/"), str(rec["line"]),
            rec["quote"].replace("\t", " ")[:300],
            "是" if has4_disk(e) else "否",
            "是" if e in set17 else "否",
            "是" if e in delta5 else "否",
            rec["polarity"] or "未给",
            str(len(supported[e])),
        ]))
    io.open(os.path.join(HERE, "sieve_all.tsv"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")

    # ---- 漏掉集合（sieve − 17）
    missed = [e for e in sieve_all if e not in set17]
    mlines = ["\t".join(hdr_out)]
    for e in missed:
        cr = cov.get(e, {})
        rel, rec = supported[e][0]
        mlines.append("\t".join([
            e, cr.get("subsystem", ""), cr.get("name", ""),
            rel.replace(os.sep, "/"), str(rec["line"]),
            rec["quote"].replace("\t", " ")[:300],
            "是" if has4_disk(e) else "否",
            "否",
            "是" if e in delta5 else "否",
            rec["polarity"] or "未给",
            str(len(supported[e])),
        ]))
    io.open(os.path.join(HERE, "missed67.tsv"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(mlines) + "\n")

    # ---- 诊断
    diag = []
    diag.append("artifacts enumerated: %d  (md=%d tsv=%d)" % (
        len(arts), art_kind.get("md", 0), art_kind.get("tsv", 0)))
    diag.append("D1 rows: %d / distinct %d" % (len(d1), len(d1_entries)))
    diag.append("records on D1 entries: %d (raw unit hits)" % len(all_recs))
    diag.append("entries SUPPORTED: %d" % len(sieve_all))
    diag.append("entries REFUTED (excluded, S5 global): %d  (of which also supported elsewhere: %d)"
                % (len(refuted_entries), len(refuted_conflict)))
    diag.append("entries with positive verdict: %d" % len(pos_entries))
    diag.append("17 ∩ sieve: %d" % len(set17 & set(sieve_all)))
    diag.append("17 − sieve: %d" % len(set17 - set(sieve_all)))
    diag.append("sieve − 17: %d" % len(missed))
    io.open(os.path.join(HERE, "debug_summary.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(diag) + "\n")

    # ---- 诊断：17 里不在集合内的
    d17 = ["17 − sieve（前批有、本口径无）："]
    for e in sorted(set17 - set(sieve_all)):
        d17.append("  %s  cov_name=%s  refuted=%s" % (
            e, cov.get(e, {}).get("name", ""), "Y" if e in refuted else "N"))
    d17.append("")
    d17.append("REFUTED entries (%d)，其中 %d 条另有正面判定（冲突，按 S5 从严剔除）："
               % (len(refuted_entries), len(refuted_conflict)))
    for e in refuted_entries:
        rel, rec = refuted[e][0]
        d17.append("  %s  %s:%d  %s" % (e, rel.replace(os.sep, "/"), rec["line"], rec["quote"][:150]))
    io.open(os.path.join(HERE, "debug_17.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(d17) + "\n")

    # ---- 诊断：每条目的全部记录，供人工反向核
    rows_dbg = ["entry\taudit_file\taudit_line\tkind\tpolarity\tid_neg\tquote"]
    for (ent, rel), rs in sorted(per.items()):
        for r in rs:
            rows_dbg.append("\t".join([ent, rel.replace(os.sep, "/"), str(r["line"]),
                                       r["kind"], r["polarity"] or "-",
                                       "Y" if r["id_neg"] else "N",
                                       r["quote"].replace("\t", " ")[:400]]))
    io.open(os.path.join(HERE, "debug_records.tsv"), "w", encoding="utf-8",
            newline="\n").write("\n".join(rows_dbg) + "\n")

    # ---- §4.4 反向核样本：18 行（确定性规则见下），逐行给人工判定
    #     规则：① 把「人工复核否决表 DROP_RECORD 导致整条出集合」的条目全部纳入（它们风险最高）；
    #           ② 其余按 n_supporting_artifacts 升序、entry 升序补齐到 18 行。
    dropped_entries = sorted({k[0] for k in DROP_RECORD} - set(sieve_all))
    pool = [e for e in sieve_all if e not in dropped_entries]
    pool.sort(key=lambda e: (len(supported[e]), e))
    sample = dropped_entries + pool[:max(0, 18 - len(dropped_entries))]

    SV = {
        "0040B880": ("AGREE", "同产物 §2 逐行表（:21）在 ② 列写明 ✓DynVec<BombClass*>，:58 是该表 11 行的白名单结论；entry 为表格行首"),
        "0040B930": ("AGREE", "同上 :22 行 ② 列 ✓DynVec<BombClass*>，:58 白名单含本 entry"),
        "0040F7C0": ("AGREE", "同上 :23 行 ② 列 ✓DynVec<WarheadTypeClass*>，:58 白名单含本 entry"),
        "0040FD90": ("AGREE", "同上 :24 行 ② 列 ✓DynVec<WeaponTypeClass*>，:58 白名单含本 entry"),
        "0040FE40": ("AGREE", "同上 :25 行 ② 列 ✓DynVec<WeaponTypeClass*>，:58 白名单含本 entry"),
        "00413F80": ("AGREE", "表格行 ② 列直接写 007E22A4[9] AircraftClass（vt+slot→类名），裁决列 PASS"),
        "0041C180": ("AGREE", "弱：审计实测 call [v+0x2C]=slot11=WhatAmI 且本 entry 字节 B8 02 000000 C3；身份复算止于 WhatAmI 立即数层面，无 RTTI 名串复算"),
        "00459EC0": ("AGREE", "弱：同 0041C180，本条字节 B8 06 对应 BuildingClass 的 WhatAmI=6"),
        "00431E80": ("AGREE", "同产物 §② ④ 核验（:35）称 14 条链 vt-4=COL→COL+0xC=TD→TD+8 名串全成立、vt[slot]==entry 全成立；:53 白名单 7 行逐条列名"),
        "004324B0": ("AGREE", "同 00431E80（:53 白名单第 2 个 entry）"),
        "004393D0": ("AGREE", "「6 行 WhatAmI/GetSize…成立」+ 字节自核 b8 5c…；身份证据为 slot11/slot12 的 B8 桩形态与 AbstractType 枚举逐值相等"),
        "0046B7E0": ("AGREE", "同 0040B880（:27 行 ② 列 ✓DynVec<BulletClass*> + :58 白名单）"),
        "0046B890": ("AGREE", "同 0040B880（:28 行 ② 列 ✓DynVec<BulletClass*> + :58 白名单）"),
        "0046C890": ("AGREE", "表格行 ② 列 VT 0x7e4948 slot8、RTTI BulletTypeClass，且 VT 由 ctor 0x46BBC0 装入 ⇒ ctor/slot 闭环；裁决 成立"),
        "00473B10": ("AGREE", "表格行 ② 列「仅 0x7E16B0 slot9 CCFileClass」+ 裁决「白·条件」；原引用 :35 判的是 ③b，已订正到 :23"),
        "004A2990": ("AGREE", "表格行 ② 列 vt 7E5DAC slot0 / COL 7FF9B8→TD 81FC30 .?AVCStreamClass@@，裁决「并入」"),
        "004A8960": ("AGREE", "表格行 ② 列 DisplayClass::slot42，7 表；裁决列「白」"),
        "004A9840": ("AGREE", "「应并入行数=4」逐条列名；该文件 :19 逐行给「②7 表同槽41」"),
        "0043F180": ("DISAGREE", "M3_merge:27 在讲 grade 冲突（本 entry 只是「表中 grade 高于本轮断言」三例之一），判的不是②；已剔除"),
        "004D27C0": ("DISAGREE", "S10_K4:31 是对已证行做字节+grade 抽核（b878000000c3 已证 ✓），未独立定类属；已剔除"),
        "004D8FB0": ("DISAGREE", "S10_K10:6 判环①（选择子表长度）与「②被调 grade」，此 ② 指被调方档位而非类身份；已剔除"),
        "004AB9B0": ("AGREE", "原引用 M4_merge:23 只是语义栏措辞，已剔除该记录；改由 S09_KPROVED:27 全表枚举（DisplayClass 0x7E6114[48]，4 行类与槽号字节可证）支撑"),
    }
    slines = ["entry\tsubsystem\tname\taudit_file\taudit_line\tverdict\treason\taction"]
    for e in sample:
        cr = cov.get(e, {})
        if e in supported:
            rel, rec = supported[e][0]
            af, al, q = rel.replace(os.sep, "/"), str(rec["line"]), rec["quote"][:120]
        else:
            rel, rec = refuted.get(e, [(DROP_RECORD.get((e, "", 0), None), None)])[0] if False else (None, None)
            # 被否决条目：引用它当时被误判的那一行
            key = [k for k in DROP_RECORD if k[0] == e][0]
            af, al, q = key[1], str(key[2]), DROP_RECORD[key]
        v, why = SV.get(e, ("未核", ""))
        slines.append("\t".join([e, cr.get("subsystem", ""), cr.get("name", ""),
                                 af or "", al or "", v, why,
                                 "剔除" if v == "DISAGREE" else "保留"]))
    io.open(os.path.join(HERE, "sample18.tsv"), "w", encoding="utf-8",
            newline="\n").write("\n".join(slines) + "\n")

    # ---- §4.5 出卡建议（数字全部由本脚本算）
    n = len(sieve_all)
    per_card = 18
    n_cards = (n + per_card - 1) // per_card
    plan = []
    plan.append("完整集合 %d 行；按 ≤18 行/卡 ⇒ 需 %d 张卡" % (n, n_cards))
    for i in range(n_cards):
        chunk = sieve_all[i * per_card:(i + 1) * per_card]
        plan.append("  卡 %d：entry %s … %s（%d 行）" % (
            i + 1, chunk[0], chunk[-1], len(chunk)))
    has4 = [e for e in sieve_all if has4_disk(e)]
    ov5 = [e for e in sieve_all if e in delta5]
    new_rows = [e for e in sieve_all if not has4_disk(e) and e not in delta5]
    plan.append("盘上已有 ④（coverage 第 4 列含 ④）应先剔：%d 行" % len(has4))
    plan.append("未并表但与待并表批次重叠（R16_D1_FINAL delta 5 行）：%d 行 %s"
                " —— 实测这 5 行盘上已含该批 ④ 升级句，是上面 %d 行的子集，不额外扣"
                % (len(ov5), " ".join(ov5), len(has4)))
    plan.append("可开卡的新行 = %d − %d（已有 ④）= %d 行 ⇒ %d 张卡（≤18/卡）"
                % (len(sieve_all), len(has4), len(new_rows),
                   (len(new_rows) + per_card - 1) // per_card))
    for i in range((len(new_rows) + per_card - 1) // per_card):
        chunk = new_rows[i * per_card:(i + 1) * per_card]
        plan.append("  新卡 %d：entry %s … %s（%d 行）" % (
            i + 1, chunk[0], chunk[-1], len(chunk)))
    plan.append("17 中不在本集合：%d 行 %s" % (len(set17 - set(sieve_all)),
                                              " ".join(sorted(set17 - set(sieve_all)))))
    io.open(os.path.join(HERE, "card_plan.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(plan) + "\n")

    # ---- 与 R16_AUDIT_D1_FINAL 的 67 行清单逐条比对（该清单在盘上，可核）
    audit67 = set()
    vs = os.path.join(R14, "R16_AUDIT_D1_FINAL", "verify_summary.json")
    if os.path.isfile(vs):
        import json
        j = json.load(io.open(vs, encoding="utf-8"))
        audit67 = {x.upper() for x in j.get("d51_broad_outside_17", [])}
    missed_set = {e for e in sieve_all if e not in set17}
    diff = []
    diff.append("审计 67 行清单: %d" % len(audit67))
    diff.append("本卡 漏掉集合: %d" % len(missed_set))
    diff.append("两者交集: %d" % len(audit67 & missed_set))
    diff.append("仅在审计清单（我未收）: %d  %s" % (len(audit67 - missed_set),
                                                 " ".join(sorted(audit67 - missed_set))))
    diff.append("仅在我集合（审计未列）: %d  %s" % (len(missed_set - audit67),
                                                 " ".join(sorted(missed_set - audit67))))
    io.open(os.path.join(HERE, "diff_vs_audit67.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(diff) + "\n")

    print("\n".join(diag))
    print()
    print("\n".join(plan))


if __name__ == "__main__":
    main()
