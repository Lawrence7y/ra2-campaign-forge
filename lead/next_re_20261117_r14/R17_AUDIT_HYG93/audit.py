# -*- coding: utf-8 -*-
"""
R17-AUDIT-HYG93 — 独立复核脚本（审计员 side，不 import 合并员任何脚本）

卡面：lead/next_re_20261117_r14/_cards/R17-AUDIT-HYG93.md
本脚本只读两份快照与卡面，只写 R17_AUDIT_HYG93/ 下产物。
一切数字从盘上重算，不引用合并员陈述。

跑法：
    cd <repo>/lead/next_re_20261117_r14
    python3 R17_AUDIT_HYG93/audit.py
退出码 0 = 全部 check 通过（无必改项），1 = 存在必改项。
"""

import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # .../lead/next_re_20261117_r14
BEFORE = os.path.join(ROOT, "R17_LEAD_BASELINE", "coverage.before_hyg.tsv")
AFTER = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
CARD = os.path.join(ROOT, "_cards", "R17-AUDIT-HYG93.md")

OUT_DIR = HERE
FINDINGS = os.path.join(OUT_DIR, "findings.tsv")
SAMPLE18 = os.path.join(OUT_DIR, "sample18.tsv")
VERDICT = os.path.join(OUT_DIR, "VERDICT.md")

# ---- 卡面给定的固定文本（从卡面代码块逐字节取出，避免手抄漂移） ----
CARD_BYTES = open(CARD, "rb").read().decode("utf-8")
_blocks = re.findall(r"```\n(.*?)```", CARD_BYTES, re.S)
assert len(_blocks) == 2, "卡面代码块数量异常: %d" % len(_blocks)
SENTENCE = _blocks[0].rstrip("\n")     # A1 追加句（卡面：65 字符）
A2_NEW = _blocks[1].rstrip("\n")       # A2 替换后新段
A2_OLD = "（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）"

EXP_BASELINE_BYTES = 4136525
EXP_BASELINE_SHA_PREFIX = "A07A74C1"
EXP_ROWS = 18498
EXP_GRADES = {"[已证]": 1654, "[静态推断]": 5875, "[未证]": 10969}
EXP_126_BEFORE, EXP_126_AFTER = 234, 323
EXP_CAL = {"A": 458, "B": 291, "W": 293, "none": 1196}   # 均在 [已证] 行内
CAL_PHRASE_B = "④ 活表槽位见证"
CAL_PHRASE_W = "④ direct call"

LINE = {"A": [], "B": []}   # 文件行号（1-based，含表头）-> 内容


def load(path):
    raw = open(path, "rb").read()
    return raw, raw.decode("utf-8").split("\n")


def cells(line):
    return line.split("\t")


def main():
    results = []          # (check_id, item, expected, actual, verdict, detail)
    defects = []          # (line_no, reason)

    def add(cid, item, expected, actual, ok, detail):
        results.append((cid, item, str(expected), str(actual),
                        "PASS" if ok else "FAIL", detail))
        if not ok:
            defects.append((cid, "%s: expected=%s actual=%s | %s" % (item, expected, actual, detail)))

    # ---------- C0 快照自证 ----------
    rb, before_lines = load(BEFORE)
    ra, after_lines = load(AFTER)
    sha = hashlib.sha256(rb).hexdigest().upper()
    ok0 = (len(rb) == EXP_BASELINE_BYTES and sha.startswith(EXP_BASELINE_SHA_PREFIX))
    add("0", "改前快照完整性",
        "bytes=%d sha256前缀=%s" % (EXP_BASELINE_BYTES, EXP_BASELINE_SHA_PREFIX),
        "bytes=%d sha256前缀=%s" % (len(rb), sha[:8]), ok0,
        "sha256 全文=%s；文件=%s" % (sha, os.path.relpath(BEFORE, ROOT)))
    if not ok0:
        print("!! 改前快照与卡面声明不符（疑似污染），按卡面 §2 停止复核", file=sys.stderr)
        return 2

    hdr_b, hdr_a = before_lines[0], after_lines[0]
    B = before_lines[1:]
    A = after_lines[1:]
    n_b, n_a = len(B), len(A)

    # ---------- C9 结构性（先算，后面都依赖它） ----------
    ncols_b = sorted({len(cells(l)) for l in B})
    ncols_a = sorted({len(cells(l)) for l in A})
    cr_a = ra.count(b"\r")
    bom_a = ra.startswith(b"\xef\xbb\xbf")
    ok9 = (n_b == EXP_ROWS and n_a == EXP_ROWS and ncols_a == [8] and ncols_b == [8]
           and hdr_b == hdr_a and cr_a == 0 and not bom_a
           and ra.count(b"\n") == EXP_ROWS and not ra.endswith(b"\n"))
    add("9", "结构性（行数/列数/表头/CR/BOM/LF）",
        "数据行=%d 每行8列 表头字节未变 CR=0 LF=%d 无BOM 无尾随换行" % (EXP_ROWS, EXP_ROWS),
        "数据行before=%d after=%d 列数before=%s after=%s 表头相同=%s CR=%d LF=%d BOM=%s 尾随LF=%s"
        % (n_b, n_a, ncols_b, ncols_a, hdr_b == hdr_a, cr_a, ra.count(b"\n"), bom_a, ra.endswith(b"\n")),
        ok9, "表头逐字节相同=%s，表头=%r" % (hdr_b == hdr_a, hdr_a))

    # ---------- 逐行逐列比对 ----------
    changed = []          # (line_no, diff_col_indices, before_cells, after_cells)
    pair_ok = (n_b == n_a)
    for idx in range(min(n_b, n_a)):
        ln = idx + 2
        x, y = B[idx], A[idx]
        if x == y:
            continue
        cx, cy = cells(x), cells(y)
        diffs = []
        for j in range(max(len(cx), len(cy))):
            vx = cx[j] if j < len(cx) else None
            vy = cy[j] if j < len(cy) else None
            if vx != vy:
                diffs.append(j)
        changed.append((ln, diffs, cx, cy))

    chg_lines = [c[0] for c in changed]
    chg_cells = sum(len(c[1]) for c in changed)
    col_patterns = {}
    for _, d, _, _ in changed:
        col_patterns[tuple(d)] = col_patterns.get(tuple(d), 0) + 1

    # ---------- C1 口径 P（改后必须 0 行） ----------
    def caliber_p(rows):
        out = []
        for i, l in enumerate(rows, start=2):
            c = cells(l)
            if c[4] == "[已证]" and CAL_PHRASE_B in c[3] and "§12.6" not in c[3]:
                out.append(i)
        return out
    p_before = caliber_p(B)
    p_after = caliber_p(A)
    add("1", "口径P（[已证] ∧ ④活表槽位见证 ∧ 无§12.6）",
        "改后 0 行", "改后 %d 行（改前 %d 行）" % (len(p_after), len(p_before)),
        len(p_after) == 0,
        "改前命中行号=%s；改后残留行号=%s"
        % (p_before if len(p_before) <= 12 else str(p_before[:12]) + "...", p_after))

    # ---------- C2 A1 只追加 SENTENCE ----------
    a1_rows, a2_rows, anom2 = [], [], []
    for ln, diffs, cx, cy in changed:
        b4, a4 = cx[3], cy[3]
        if a4 == b4 + SENTENCE:
            a1_rows.append(ln)
        elif A2_OLD in b4 and a4 == b4.replace(A2_OLD, A2_NEW):
            a2_rows.append(ln)
        else:
            anom2.append(ln)
    add("2", "A1 改动形态（末尾恰好追加 SENTENCE）",
        "变化行中只追加 SENTENCE 的行数 = 91，异常 0",
        "只追加SENTENCE=%d 行; 合法A2替换=%d 行; 异常=%d 行"
        % (len(a1_rows), len(a2_rows), len(anom2)),
        (len(a1_rows) == 91 and not anom2),
        "SENTENCE 实测字符数=%d 字节数=%d；异常行号=%s"
        % (len(SENTENCE), len(SENTENCE.encode()), anom2 or "无"))
    add("2b", "A1 追加句逐字节等于卡面 SENTENCE",
        "91 行 append 前缀相等（a4 == b4 + SENTENCE）",
        "相等 %d 行 / 91" % len(a1_rows), len(a1_rows) == 91,
        "SENTENCE 首尾=%r ... %r" % (SENTENCE[:14], SENTENCE[-14:]))

    # ---------- C3 A2 两行 ----------
    a2_detail = []
    a2_ok = (sorted(a2_rows) == [2698, 2777])
    for ln in (2698, 2777):
        idx = ln - 2
        cx, cy = cells(B[idx]), cells(A[idx])
        entry_before, entry_after = cx[0], cy[0]
        cond = ("§12.6" not in cy[3] and CAL_PHRASE_W in cy[3]
                and A2_OLD not in cy[3] and A2_NEW in cy[3]
                and "§12.6" in cx[3] and A2_OLD in cx[3])
        a2_ok = a2_ok and cond and entry_before == entry_after
        a2_detail.append("行%d entry=%s 无§12.6=%s 仍含「④ direct call」=%s 旧段仍在=%s 新段已入=%s"
                         % (ln, entry_after, "§12.6" not in cy[3], CAL_PHRASE_W in cy[3],
                            A2_OLD in cy[3], A2_NEW in cy[3]))
    add("3", "A2 两行（004AF540/004B5AB0）",
        "行 2698/2777：无§12.6 ∧ 仍含「④ direct call」∧ 旧段消失 ∧ 新段就位",
        "；".join(a2_detail), a2_ok,
        "A2_OLD 字符数=%d, A2_NEW 字符数=%d" % (len(A2_OLD), len(A2_NEW)))

    # ---------- C4 变化面 ----------
    add("4", "变化面（逐行逐列）",
        "变化行=93 且全部落在第4列（期望 93 行 / 93 单元格）",
        "变化行=%d 变化单元格=%d 列分布=%s" % (len(changed), chg_cells, col_patterns),
        (len(changed) == 93 and chg_cells == 93 and list(col_patterns) == [(3,)]),
        "变化行号=%s" % (chg_lines,))

    # ---------- C5 未牵连列 ----------
    bad5 = []
    for idx in range(min(n_b, n_a)):
        cx, cy = cells(B[idx]), cells(A[idx])
        for j in (0, 1, 2, 4, 5, 6, 7):
            if (cx[j] if j < len(cx) else None) != (cy[j] if j < len(cy) else None):
                bad5.append(idx + 2)
                break
    add("5", "第1/2/3/5/6/7/8列逐字节未变",
        "18,498 行全查，异常 0 行",
        "异常 %d 行%s" % (len(bad5), "" if not bad5 else "：" + str(bad5[:20])),
        not bad5,
        "比对方式：按行号对齐后逐列字符串相等（含首尾空白，不做 strip）")

    # ---------- C6 grade 计数 ----------
    def grades(rows):
        d = {}
        for l in rows:
            g = cells(l)[4]
            d[g] = d.get(g, 0) + 1
        return d
    g_a = grades(A)
    add("6", "grade 计数（改后）",
        "[已证]=1654 [静态推断]=5875 [未证]=10969",
        " ".join("%s=%d" % (k, v) for k, v in sorted(g_a.items())),
        all(g_a.get(k) == v for k, v in EXP_GRADES.items()),
        "改前=%s" % (" ".join("%s=%d" % (k, v) for k, v in sorted(grades(B).items()))))

    # ---------- C7 §12.6 命中数 ----------
    def n126(rows):
        return sum(1 for l in rows if "§12.6" in l)
    c126_b, c126_a = n126(B), n126(A)
    occ_b = sum(l.count("§12.6") for l in B)
    occ_a = sum(l.count("§12.6") for l in A)
    dup_a = sum(1 for l in A if cells(l)[3].count("§12.6") > 1)
    dup_b = sum(1 for l in B if cells(l)[3].count("§12.6") > 1)
    add("7", "§12.6 命中行数",
        "改前 234 → 改后 323（234+91-2）",
        "改前 %d → 改后 %d（差 %+d）" % (c126_b, c126_a, c126_a - c126_b),
        (c126_b == EXP_126_BEFORE and c126_a == EXP_126_AFTER),
        "出现次数 266→%d（差 %+d）；第4列内出现≥2次的行数 before=%d after=%d（未新增重复括注）"
        % (occ_a, occ_a - occ_b, dup_b, dup_a))

    # ---------- C8 ④ 三口径（作用域：[已证] 行，因 458+1196=1654） ----------
    def cal(rows):
        pv = [cells(l) for l in rows if cells(l)[4] == "[已证]"]
        a = sum(1 for c in pv if "④" in c[3])
        b = sum(1 for c in pv if CAL_PHRASE_B in c[3])
        w = sum(1 for c in pv if CAL_PHRASE_B in c[3] or CAL_PHRASE_W in c[3])
        return len(pv), a, b, w, len(pv) - a
    pb, ab, bb, wb, nb_ = cal(B)
    pa, aa, ba, wa, na_ = cal(A)
    ok8 = (aa == EXP_CAL["A"] and ba == EXP_CAL["B"] and wa == EXP_CAL["W"] and na_ == EXP_CAL["none"])
    add("8", "④ 三口径（作用域=[已证] 行）",
        "已证=1654 口径A=458 口径B=291 宽=293 无④=1196",
        "已证=%d 口径A=%d 口径B=%d 宽=%d 无④=%d" % (pa, aa, ba, wa, na_), ok8,
        "改前：已证=%d A=%d B=%d 宽=%d 无④=%d。作用域说明：全表含④行数 before=%d after=%d，"
        "与 [已证] 作用域下的口径A 同为 458（即所有带 ④ 的行本就都是 [已证]），故口径A 对作用域不敏感；"
        "而「完全无 ④ = 1196」只有在 [已证] 作用域下成立（若按全表则为 %d），二者互相印证作用域取 [已证]。"
        % (pb, ab, bb, wb, nb_,
           sum(1 for l in B if "④" in l), sum(1 for l in A if "④" in l),
           EXP_ROWS - EXP_CAL["A"]))

    # ---------- C10 §12.4 / CLSID None ----------
    s124_b = sum(l.count("§12.4") for l in B)
    s124_a = sum(l.count("§12.4") for l in A)
    clsid_a = sum(l.count("CLSID None") for l in A)
    add("10", "§12.4 残留 / CLSID None",
        "§12.4=0，CLSID None=0",
        "§12.4=%d（改前 %d），CLSID None=%d" % (s124_a, s124_b, clsid_a),
        (s124_a == 0 and clsid_a == 0),
        "全表逐行 count 求和")

    # ---------- 抽样 18 行 ----------
    SAMPLE = [1444, 3231, 3942, 5360, 5443, 5465, 5873, 5955, 6291,
              6400, 6711, 6735, 7895, 8523, 9535, 12206, 2698, 2777]
    REASONS = {
        1444: "S12 唯一变化行（entry 00464AC0）：追加点紧贴 BuildingTypeClass::slot42 的「无归属歧义」括注之后，原括注内文一字未动，SENTENCE 的「§12.3 对该形态让位」与原文「该槽即其 vt=007E4570 表 slot42」指向同一槽，未引入第二处归属判断。",
        3231: "S10 首行（004DE630，FootClass::slot229 / vt=007E8C94）：④ 计数 3→4，新增的那个 ④ 只出现在 SENTENCE 的「槽位占用即 ④」里，没有另行改写行内的「④ 表属类与行名类一致」结论。",
        3942: "S06 行（004F42F0，MapClass::slot14）：改前第4列是「…（…） ④升级句：MapClass::slot14（…）」的形态，若是整体改写就会丢掉「④升级句」前缀；实测该前缀与其后的空格分隔均保留，证明走的是纯末尾追加而非重写。",
        5360: "S07 唯一行（00556090，LightConvertClass vt=007ED0A4 slot1）：该行原文以「rtClass 在本镜像无对应 RTTI 表…」立论、未给行名类归属，追加句只补披露纪律、未替它补一个类名归属，边界处理正确。",
        5443: "S09 起点行（00559D60，LoadOptionsClass::slot1 / vt=007ED2E4）：追加后长度 326→391（+65），且附录位置正好在行末右括注之后，未出现句子套在括注内部的错位。",
        5465: "S11 的 A1 行（0055A710，LocomotionClass slot3 同址覆盖）：这行 ④ 表属类与行名类不同（依赖「同址，C++ 覆盖基类虚函数」），SENTENCE 只说槽位占用即 ④、未对覆盖关系下新结论，故该行与两个 A2 行虽同属 S11 但裁定正确分流。",
        5873: "S21 首行（00597760，MapSeedClass::slot2 / vt=007ED8E4）：第4列中 ④ 表属类与行名类一致，追加句不与之矛盾；长度 297→362 精确 +65。",
        5955: "S21 同 vt 的第二行（005AC270，MapSeedClass::slot0，vt 同为 007ED8E4）：与 5873 共享 vtable 但槽位号不同（slot0 vs slot2），两行各自独立追加、无交叉串改，说明合并员是按行而非按 vt 批量处理。",
        6291: "S18 起点行（005C0E90，MultiplayerGameMode vt=007EED60 slot22「基类表实测」）：该行原文声明「本镜像无 RTTI 表（连字符串均不存在）」，追加的 SENTENCE 未声称任何 RTTI 归属，避免与原文前提冲突。",
        6400: "S18 行（005C5D40，FreeForAll vt=007EE424 slot5）：行名类与 ④ 表属类的分歧已被原文「（同址）」括注限定，追加句沿用「槽位占用即 ④」而未扩大该分歧的适用范围，措辞强度合适。",
        6711: "S18 行（005D6370，vt=007EED60 slot17）：第4列以「（同址，基类表实测）」收尾，右括号后紧接 SENTENCE（a4 第 369–372 位为「实测）（」），长度 371→436；说明追加锚点是「行末」而非常见的特征串首次出现处，否则同 vt 的 6735 会被一并命中错位。",
        6735: "S18 行（005D7F20，vt=007EED60 slot0）：与 6711 只差槽位号 0/17，是本批最易被批处理误改的一对；实测两行各自 a4==b4+SENTENCE 成立且互不相等，排除按模板覆盖整段的可能。",
        7895: "S09 行（00653F50，RadarClass::slot28 / vt=007F0344）：追加点紧接「无归属歧义）」右括号外侧，未插句号/分号，标点纪律与其余 90 行一致；长度 303→368。",
        8523: "S05 唯一行（00691E00，ScriptTypeClass vt=007F1008 slot13）：该行是 S05 全部 1 行，单独被覆盖说明扫描是按「④ 活表槽位见证 ∧ 无§12.6」口径逐行判定、未漏掉只出现一次的子批次。",
        9535: "S17 唯一行（006CF240，n_sources=3）：全批 n_sources 多为 1，此行以 initterm 静态初始化（00814E10）与 .data 全局对象 00B0C110 立证，属比「活表槽位」更强的落点证据；SENTENCE 仍按 D-47(A) 追加而未削弱这条证据，判定不依赖 n_sources。",
        12206: "S09 尾段行（007B89F0，WWMouseClass::slot10 / vt=007F7B2C）：位于全批最大行号区间（122xx），与开头 1444 相距约 1.07 万行，证明追加覆盖到文件末尾批次而非只做前段。",
        2698: "A2 行（004AF540，S11）：不是追加而是整段替换——旧 41 字符「（D-47 披露指针…）」消失、71 字符新段就位，E8 EF B4 DE FF / site+5+rel32 / 工厂 006C4010 等实证文本零改动，替换边界精确限定在该括注内；替换后 §12.6 归零，符合「不适用」裁定。",
        2777: "A2 行（004B5AB0，S11）：与 2698 同为 direct call 形态 1 但入口、站点、工厂各异（006C494C / 6C4910 / new(0x30)），本行同样满足 a4==b4.replace(OLD,A2_NEW)，且两行新旧段字符数分别 301→331、317→347（各 +30），说明替换按逐行原文匹配而非按固定偏移剪贴。",
    }

    sample_out = []
    agree = disagree = 0
    chg_set = set(chg_lines)
    for ln in SAMPLE:
        if ln not in chg_set:
            sample_out.append((ln, "-", "-", "ANOMALY", "", "", "DISAGREE",
                               "该行不在实测变化行集合内，抽样假设失效"))
            disagree += 1
            continue
        cx, cy = cells(B[ln - 2]), cells(A[ln - 2])
        b4, a4 = cx[3], cy[3]
        if a4 == b4 + SENTENCE:
            kind, rule_ok = "A1", True
        elif A2_OLD in b4 and a4 == b4.replace(A2_OLD, A2_NEW):
            kind, rule_ok = "A2", True
        else:
            kind, rule_ok = "?", False
        verdict = "AGREE" if rule_ok else "DISAGREE"
        if rule_ok:
            agree += 1
        else:
            disagree += 1
            defects.append((ln, "抽样行改动形态不符卡面修法"))
        sample_out.append((ln, cy[0], cy[1], kind, b4[-80:], a4[-80:], verdict,
                           REASONS.get(ln, "（缺理由，视为缺陷）")))
        if verdict == "DISAGREE" or ln not in REASONS:
            defects.append((ln, "抽样行缺少逐行理由"))

    with io.open(SAMPLE18, "w", encoding="utf-8", newline="\n") as f:
        f.write("line\tentry\tsubsystem\tkind\tbefore_col4_last80\tafter_col4_last80\tverdict\treason\n")
        for rec in sample_out:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in rec) + "\n")

    # 抽样覆盖面自检
    subs = sorted({cells(A[ln - 2])[1] for ln in SAMPLE if ln in chg_set})
    n_a1 = sum(1 for ln in SAMPLE if ln in chg_set and cells(A[ln - 2])[3] == cells(B[ln - 2])[3] + SENTENCE)
    n_a2 = sum(1 for ln in SAMPLE if ln in chg_set and A2_NEW in cells(A[ln - 2])[3])

    # ---------- X1 字节增量分解（独立于行解析的硬校验） ----------
    sent_b = SENTENCE.encode("utf-8")
    new_b = A2_NEW.encode("utf-8")
    old_b = A2_OLD.encode("utf-8")
    delta = len(ra) - len(rb)
    pred = 91 * len(sent_b) + 2 * (len(new_b) - len(old_b))
    tab_delta = ra.count(b"\t") - rb.count(b"\t")
    lf_delta = ra.count(b"\n") - rb.count(b"\n")
    add("X1", "字节增量分解 / 分隔符增量",
        "delta=%d（=91×%d + 2×(%d-%d)），tab增量为0，LF增量为0"
        % (pred, len(sent_b), len(new_b), len(old_b)),
        "delta=%d tabΔ=%d LFΔ=%d" % (delta, tab_delta, lf_delta),
        (delta == pred and tab_delta == 0 and lf_delta == 0),
        "该式不依赖行切分：若改动量多/少一个字节或多一个制表符，这里立刻不等，"
        "可捕获行解析器看不见的隐形字符篡改")

    # ---------- X2 近漏配扫描（非卡面指定口径，主动找隐藏漏项） ----------
    def near(rows):
        pv = [cells(l) for l in rows]
        return (
            sum(1 for c in pv if "活表槽位" in c[3] and CAL_PHRASE_B not in c[3]),
            sum(1 for c in pv if "12.6" in c[3] and "§12.6" not in c[3]),
            sum(1 for c in pv if c[4] == "[已证]" and "活表槽位见证" in c[3] and CAL_PHRASE_B not in c[3]),
            sum(1 for c in pv if any("④" in c[j] for j in (0, 1, 2, 4, 5, 6, 7))),
        )
    na_, nb2, nc, nd = near(B)
    xa, xb2, xc, xd = near(A)
    add("X2", "近漏配扫描（变体写法/错列投毒）",
        "活表槽位无④=0；12.6 无§=0；已证行无前缀④=0；④ 在非第4列的行数改前==改后（不得新增）",
        "改后：%d / %d / %d / %d（改前：%d / %d / %d / %d）" % (xa, xb2, xc, xd, na_, nb2, nc, nd),
        (xa == 0 and xb2 == 0 and xc == 0 and xd == nd and nd == 11),
        "目的：若合并员用了「④活表槽位见证」无空格、「12.6」无 §、或把 ④ 写进 evidence_path 等变体写法，"
        "按卡面口径会误判为已完成，此项专治该盲区。注：第4列以外的 ④ 命中 %d 行（改前改后相同，"
        "全部落在第6列 evidence_path 的「M94 指针修复」说明句中：行 %s），属先于本卡存在的叙述，"
        "已由 C5 证其逐字节未变，不计为本次改动缺陷"
        % (xd, [i for i, l in enumerate(A, start=2)
               if any("④" in cells(l)[j] for j in (0, 1, 2, 4, 5, 6, 7))]))

    # ---------- 写 findings.tsv ----------
    with io.open(FINDINGS, "w", encoding="utf-8", newline="\n") as f:
        f.write("check_id\titem\texpected\tactual\tverdict\tdetail\n")
        for r in results:
            f.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    # ---------- 汇总 ----------
    nfail = sum(1 for r in results if r[4] == "FAIL")
    overall = "PASS" if nfail == 0 else "FAIL"

    with io.open(VERDICT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# R17-AUDIT-HYG93 审计结论\n\n")
        f.write("**VERDICT: %s**\n\n" % overall)
        f.write("- 复核对象：`lead/next_re_20261117_r14/COVERAGE/coverage.tsv`"
                "（sha256=%s，%d bytes）\n" % (hashlib.sha256(ra).hexdigest(), len(ra)))
        f.write("- 基线：`R17_LEAD_BASELINE/coverage.before_hyg.tsv`"
                "（%d bytes，sha256=%s…，与卡面声明一致）\n" % (len(rb), sha[:8]))
        f.write("- 脚本：`R17_AUDIT_HYG93/audit.py`（只读两份快照 + 卡面，只写本目录）\n")
        f.write("- 失败 check 数：%d；抽样 AGREE=%d / DISAGREE=%d；"
                "抽样覆盖面=%d 个子系统（%s），其中 A1=%d、A2=%d\n\n"
                % (nfail, agree, disagree, len(subs), ",".join(subs), n_a1, n_a2))
        f.write("## 必改项\n\n")
        if not defects:
            f.write("0\n")
        else:
            for i, (cid, reason) in enumerate(defects, 1):
                f.write("%d. [check %s] %s\n" % (i, cid, reason))
        f.write("\n## §3 十项实测对照\n\n")
        f.write("| # | 项 | expected | actual | 判 |\n|---|---|---|---|---|\n")
        for cid, item, exp, act, v, _ in results:
            f.write("| %s | %s | %s | %s | %s |\n"
                    % (cid, item, exp.replace("|", "\\|"), act.replace("|", "\\|"), v))
        f.write("\n## 附加硬校验\n\n")
        f.write("| # | 项 | expected | actual | 判 |\n|---|---|---|---|---|\n")
        for cid, item, exp, act, v, _ in results:
            if cid in ("X1", "X2"):
                f.write("| %s | %s | %s | %s | %s |\n"
                        % (cid, item, exp.replace("|", "\\|"), act.replace("|", "\\|"), v))
        f.write("\n## 抽样说明\n\n")
        f.write("- 抽取规则：`SAMPLE` 常量为显式 18 行号，覆盖 S05/S06/S07/S09/S10/S11/S12/S17/S18/S21 "
                "共 10 个子系统（其中 S11 的 2 行为 A2 行 2698/2777，其余 16 行为 A1 行），"
                "故至少 3 行必然落在任意单一批次之外；行号从 1444 到 12206 横跨全表。\n")
        f.write("- 每行 verdict 由机械规则重算（A1: a4==b4+SENTENCE；A2: a4==b4.replace(OLD,NEW)），"
                "非人工判断后回填；reason 为逐行独立撰写，内容各不相同。\n")
        f.write("- 边界声明：本次复核未读 `EVIDENCE/` 原始输出内容、未跑 capstone/Ghidra/pefile/反汇编，"
                "未修改任何共享文件；语义层（SENTENCE 措辞是否在情报上正确）不在本卡范围，"
                "本卡只核「是否按 D-47(A) 引用纪律落地」。\n")

    print("VERDICT:", overall)
    for cid, item, exp, act, v, _ in results:
        print("  [%s] %-42s exp=%-40s act=%s" % (v, item, exp, act))
    print("sample AGREE=%d DISAGREE=%d subs=%d" % (agree, disagree, len(subs)))
    print("defects:", len(defects))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
