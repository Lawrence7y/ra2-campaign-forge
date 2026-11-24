# -*- coding: utf-8 -*-
r"""_r9s_predicates.py — R9S「语义要素匹配」层（新增层，绝不改写 R9 本体）。

设计要点（详见 _r9s_DESIGN.md）：
  * L0/L1 短路：先原样调用只读的 g7.r9_element_present(text, token)。
    raw / normalized 命中即原样返回同一 layer 标签 —— 凡 R9 已判在场的，R9S 一律不收紧。
  * 只有 L0/L1 双缺、且 token 在闭合注册表 SPECS 中登记过，才进入 L2。
  * L2 不是同义词表：一个 spec = 若干**必选语义角色**的合取 ∧ 结构约束 ∧ 承诺算子 ∧ 反否定。
    单个词面永远不足以命中；删掉任一角色的最小消融样本必须 FAIL。
  * 未登记 token 的 R9S 与 R9 逐位等价（返回 ""），故放松面被钉死在 5 个已登记要素上。

零真机、零采样代码；仅 import re / hashlib / importlib.util / pathlib。
写域：lead/gate_r9sem_20261109/（本文件及同前缀产物）。
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
R9_PATH = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
R9_SHA256 = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
R9_BYTES = 11743


def _load_r9_readonly():
    """只读加载 R9 本体；加载前 hashlib 验指纹，失配拒绝运行（_g9_gate.py:40-52 范式）。"""
    raw = R9_PATH.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != R9_SHA256 or len(raw) != R9_BYTES:
        raise RuntimeError("R9 谓词指纹失配：%s/%d ≠ %s/%d —— 拒绝运行"
                           % (sha, len(raw), R9_SHA256, R9_BYTES))
    spec = importlib.util.spec_from_file_location("_r9s_g7_readonly", R9_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R9 = _load_r9_readonly()

# ---------------------------------------------------------------------------
# 通用结构工具：子句 / 二级小节 / 围栏块 / 行号
# ---------------------------------------------------------------------------

_CLAUSE_BREAK = "。！？；\n"
HEADING_RE = re.compile(r"^##\s+[^\n]*$", re.M)
FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)


def clause_of(text: str, pos: int) -> str:
    """pos 所在子句（不跨句末标点/换行）。"""
    s = max((text.rfind(c, 0, pos) for c in _CLAUSE_BREAK), default=-1) + 1
    ends = [x for x in (text.find(c, pos) for c in _CLAUSE_BREAK) if x >= 0]
    e = min(ends) if ends else len(text)
    return text[s:e]


def section_of(text: str, pos: int) -> tuple[int, int, str]:
    """pos 所在的 `## ` 二级小节，返回 (起, 止, 标题行)。无标题则整篇。"""
    heads = list(HEADING_RE.finditer(text))
    lo, hi, title = 0, len(text), ""
    for i, h in enumerate(heads):
        if h.start() <= pos:
            lo = h.start()
            title = h.group(0)
            hi = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        else:
            break
    return lo, hi, title


def line_no(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def line_at(text: str, pos: int) -> str:
    s = text.rfind("\n", 0, pos) + 1
    e = text.find("\n", pos)
    return text[s:(len(text) if e < 0 else e)]


# 待定/否定/未来时守卫：这些是「提及但未交付」的语用标记。
PENDING_RE = re.compile(
    r"待补|待定|待验|待查|待确认|待指定|待落实|未验|未采集|未记录|未获得|尚未|尚无|"
    r"无法判定|不可判定|需进一步|如何[?？]|\?$|？$|拟做|计划|随后给出|随后补|略[。；]"
)
PLACEHOLDER_RE = re.compile(
    r"^(?:TBD|N/?A|待定|待指定|未定|未指定|不明确|未知|待确认|无|待补|略|\.{2,}|…+)$", re.I
)


def _pending(clause: str) -> bool:
    return bool(PENDING_RE.search(clause))


# 已登记要素的「承诺守卫」：字面出现 ≠ 要素已交付。
# 只对本层 5 个已登记 token 生效；未登记 token 的 L0/L1 命中一律原样放行（R9S ≡ R9）。
# 依据：交付性要素是一类**言语行为**（断言/判定/赋值），不是词面。
#   否定构式会取消该言语行为（「不可重建」不是「可重建」的在场，而是其否定）；
#   待定标记表示言语行为尚未完成（「可重建，证据待补」不是已交付的结论）。
# S5 的 NEG_CANCEL 在 S5 常量段之后重建（避免前向引用）；这里放通配兜底。
_NEG_MODAL_ANY = re.compile(r"不可重建|无法重建|不能重建|难以重建|重建不可|重建无法|未能重建")
NEG_CANCEL = {
    "S1_WHO_APPROVER": re.compile(r"未指定批准人|批准人待|无需批准|未经批准|批准人不明"),
    "S2_EXEC_OUTPUT": re.compile(r"输出未采集|无输出|输出待|未实跑|未跑"),
    "S3_BEFORE_AFTER_PAIR": re.compile(r"改前改后待|未做对照|尚未对照"),
    "S4_SCRIPT_EXISTENCE_DETERMINATION": re.compile(r"存在性未判|判定待|无法判定存在"),
    "S5_RECONSTRUCTIBILITY": _NEG_MODAL_ANY,
}


def _commitment_ok(text: str, token: str, spec_id: str) -> bool:
    """遍历 token 的全部字面出现：至少一处既不被否定构式吞掉、也不落在待定子句中。"""
    neg = NEG_CANCEL.get(spec_id)
    for m in re.finditer(re.escape(token), text):
        cl = clause_of(text, m.start())
        if neg and neg.search(cl):
            continue
        if _pending(cl):
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# S1 需谁批准 —— WHO_APPROVER
#   token 是 wh-问句「需 + 谁 + 批准」；其真值条件 = ∃x 批准人(x) 且 x 已被指认。
#   等价形式：把 wh-变量约束成一个具体施事的赋值句（Hamblin/Karttunen 问答语义：
#   问句指称其真答案集合，赋值句是其中一员且更强，另断言唯一性）。
#   角色：R1 批准人角色头 ∧ R2 赋值算子 ∧ R3 具体施事值；同一子句、R1<R2<R3。
# ---------------------------------------------------------------------------

_APPROVER_HEAD = re.compile(r"批准人|批准方|审批人|批准者|签批人")
_APPROVER_ASSIGN = re.compile(
    r"(?:批准人|批准方|审批人|批准者|签批人)"
    r"[^。；\n]{0,12}?(?:=|＝|为|是|由|：|:)\s*\*{0,2}"
    r"([^\s，,。；;*【】「」]{2,24})"
)
_APPROVER_BY = re.compile(r"由([^\s，,。；;]{2,24})批准")
_NEG_APPROVER = re.compile(r"未指定批准人|批准人(?=待|未)|无需批准|待批准|未经批准|谁批准未")


def _s1_who_approver(text: str):
    evidence = []
    for m in list(_APPROVER_ASSIGN.finditer(text)) + list(_APPROVER_BY.finditer(text)):
        agent = m.group(1).strip()
        cl = clause_of(text, m.start())
        if not _APPROVER_HEAD.search(cl) and not m.re is _APPROVER_BY:
            continue
        if _NEG_APPROVER.search(cl) or _pending(cl) or PLACEHOLDER_RE.match(agent):
            continue
        if not re.search(r"[\u4e00-\u9fff A-Za-z0-9]", agent):
            continue
        evidence.append({"role": "R1∧R2∧R3", "match": m.group(0)[:60],
                         "agent": agent, "line": line_no(text, m.start())})
    return (bool(evidence), {"spec": "S1_WHO_APPROVER",
                             "logic": "∃x[批准人(x) ∧ Bind(x, agent)] ∧ ¬Pending ∧ agent∉Placeholder",
                             "evidence": evidence})


# ---------------------------------------------------------------------------
# S2 实跑输出 —— EXEC_OUTPUT
#   token = 实跑(事件 e) + 输出(对象 o) 的合取：∃e Run(e) ∧ ∃o Output(e,o) ∧ Present(o)。
#   ★ 关键：「实跑返回」只命名事件；必须另有**输出载荷**本身才算。
#     Present(o) 的判据是文件内出现带具体值的 key='value' / key=value 数据行（围栏块内，
#     或紧随 EXEC 行的 2 行内）；`out:159-174` 只是索引/指针，不是输出，不计入载荷。
#   结构：EXEC 标记与载荷同处一个 `##` 小节，且载荷块起点距 EXEC 行 ≤ 8 行。
# ---------------------------------------------------------------------------

_EXEC_RE = re.compile(r"实跑返回|实跑输出|实跑|构造输入\s*(?:→|->)|PROBE_DONE|exit\s*=\s*0|本轮实跑")
_DATUM_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]{1,24}\s*=\s*"
    r"(?:'[^'\n]{1,80}'|\"[^\"\n]{1,80}\"|[^\s'\"，,；;]{1,40})"
)
# 元信息键：描述「跑过」这件事，不是被测函数的输出对象 o。
# exit / PROBE_DONE / n / 行数 / 耗时 属于 Run(e) 的附记，不构成 Output(e,o)。
_META_KEY_RE = re.compile(r"^(?:exit|code|n|count|lines|rows|steps|time|elapsed|ms|s|"
                          r"PROBE_DONE|OK|status|日期|行数|耗时|命令)$", re.I)
_NO_OUTPUT_RE = re.compile(r"输出待|输出未|无输出|未采集输出|详见|见附件|见\s*_?\w+\.txt|索引|见上|略")


def _datum_ok(block: str) -> list[str]:
    hits = []
    for m in _DATUM_RE.finditer(block):
        key = m.group(0).split("=", 1)[0].strip()
        val = m.group(0).split("=", 1)[1].strip().strip("'\"")
        if _META_KEY_RE.match(key) or PLACEHOLDER_RE.match(val) or val in ("待补", "略"):
            continue
        hits.append(m.group(0)[:70])
    return hits


def _s2_exec_output(text: str):
    evidence = []
    exec_hits = [m for m in _EXEC_RE.finditer(text)]
    # 载荷形态 (a)：围栏块
    for fm in FENCE_RE.finditer(text):
        hits = _datum_ok(fm.group(1))
        if not hits:
            continue
        sec_lo, sec_hi, _ = section_of(text, fm.start())
        for em in exec_hits:
            if not (sec_lo <= em.start() < sec_hi):
                continue
            gap = line_no(text, fm.start()) - line_no(text, em.start())
            if gap < 0 or gap > 8:
                continue
            cl = line_at(text, em.start())
            if _pending(cl) or _NO_OUTPUT_RE.search(cl):
                continue
            evidence.append({"role": "R1(EXEC)∧R2(OUTPUT载荷)", "layer": "fenced",
                             "exec": cl.strip()[:70], "datum": hits[:3],
                             "exec_line": line_no(text, em.start()),
                             "fence_line": line_no(text, fm.start()), "gap_lines": gap})
            break
    # 载荷形态 (b)：EXEC 行自身 / 其后 2 行内的内联数据行
    for em in exec_hits:
        ln = line_no(text, em.start())
        lines = text.split("\n")
        span = "\n".join(lines[ln - 1:ln + 2])
        hits = _datum_ok(span)
        if not hits:
            continue
        cl = line_at(text, em.start())
        if _pending(cl) or _NO_OUTPUT_RE.search(cl):
            continue
        evidence.append({"role": "R1(EXEC)∧R2(OUTPUT载荷)", "layer": "inline",
                         "exec": cl.strip()[:70], "datum": hits[:3], "exec_line": ln})
    # 去重
    seen, uniq = set(), []
    for e in evidence:
        k = (e["exec_line"], e["layer"], tuple(e["datum"]))
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return (bool(uniq), {"spec": "S2_EXEC_OUTPUT",
                         "logic": "∃e[Run(e)] ∧ ∃o[Output(e,o) ∧ Present(o)] ∧ SameSection ∧ Gap≤8 ∧ ¬Pending",
                         "evidence": uniq})


# ---------------------------------------------------------------------------
# S3 改前改后 —— BEFORE_AFTER_PAIR
#   token 是两个索引词「改前」「改后」的无分隔并列；语义 = 对同一对象给出 Before(t) 与 After(t)。
#   斜杠 / 、 与 → 都只是并列分隔符；【改前】…【改后】是同一合取的两个带标签槽位。
#   角色：R1 BEFORE 标签+实值 ∧ R2 AFTER 标签+实值 ∧ R3 对照算子；三者同一 `##` 小节。
# ---------------------------------------------------------------------------

_BEFORE_LABEL = re.compile(r"【改前】|【原文】|改前\s*[:：]|订正前\s*[:：]|原文\s*[:：]")
_AFTER_LABEL = re.compile(r"【改后】|【改为】|改后\s*[:：]|改为\s*[:：]|订正后\s*[:：]")
_COMPARE_RE = re.compile(r"对照|逐处|改前.{0,6}改后|改后.{0,6}改前|→|->")


def _labeled_values(text: str, label_re) -> list[dict]:
    out = []
    for m in label_re.finditer(text):
        tail = text[m.end():m.end() + 400]
        tail = re.split(r"\n(?=\s*(?:【|- |\||#))|\n\s*\n", tail)[0]
        val = tail.strip().strip("：: ").strip()
        if len(val) < 10 or PLACEHOLDER_RE.match(val) or _pending(val[:40]):
            continue
        out.append({"label": m.group(0), "value": val[:60], "line": line_no(text, m.start())})
    return out


def _s3_before_after(text: str):
    evidence = []
    for hm in HEADING_RE.finditer(text):
        lo = hm.start()
        hi = next((x.start() for x in HEADING_RE.finditer(text, lo + 1)), len(text))
        sec = text[lo:hi]
        head = hm.group(0)
        bef = _labeled_values(sec, _BEFORE_LABEL)
        aft = _labeled_values(sec, _AFTER_LABEL)
        cmp_ok = bool(_COMPARE_RE.search(head)) or bool(_COMPARE_RE.search(sec))
        if bef and aft and cmp_ok:
            evidence.append({"role": "R1(BEFORE)∧R2(AFTER)∧R3(对照)",
                             "section": head[:60], "before": bef[0], "after": aft[0],
                             "n_before": len(bef), "n_after": len(aft)})
    return (bool(evidence), {"spec": "S3_BEFORE_AFTER_PAIR",
                             "logic": "∃t[Before(t) ∧ After(t) ∧ Compare(t)] ∧ SameSection ∧ Value(t)∉Placeholder",
                             "evidence": evidence})


# ---------------------------------------------------------------------------
# S4 脚本存在性 —— SCRIPT_EXISTENCE_DETERMINATION
#   token 自身即「脚本」+「存在性」两个词素；另隐含「判定」这一言语行为。
#   真值条件：∃d Determination(d) ∧ Subject(d,script) ∧ Question(d,Exists(script)) ∧ Resolved(d)。
#   ★ 极性可正可负：判「不存在/未落盘」同样是**已交付的判定**（问的是判定，不是存在）。
#   角色：R1 脚本对象 ∧ R2 存在性谓词 ∧ R3 判定算子 ∧ R4 已决断的极性值；同一 `##` 小节。
# ---------------------------------------------------------------------------

_SCRIPT_RE = re.compile(r"脚本|生成脚本|生成器|\.py")
_EXIST_RE = re.compile(r"存在性|是否在盘|存在与否|未落盘|不存在|是否存在|在盘")
_DETERM_RE = re.compile(r"判定|结论|逐路结论|断定|认定为|证实|坐实|搜索全结果")
_POLARITY_RE = re.compile(
    r"【不存在[^】]*】|【存在[^】]*】|不存在且从未落盘|未落盘|无生成器|均无|"
    r"脚本不存在|脚本在盘|均在盘|存在且|不存在且"
)


def _s4_script_existence(text: str):
    evidence = []
    for hm in HEADING_RE.finditer(text):
        lo = hm.start()
        hi = next((x.start() for x in HEADING_RE.finditer(text, lo + 1)), len(text))
        sec = text[lo:hi]
        if not (_SCRIPT_RE.search(sec) and _EXIST_RE.search(sec) and _DETERM_RE.search(sec)):
            continue
        for pm in _POLARITY_RE.finditer(sec):
            ln = line_at(text, lo + pm.start())
            if _pending(ln) or PENDING_RE.search(ln):
                continue
            evidence.append({"role": "R1(脚本)∧R2(存在性)∧R3(判定)∧R4(已决断极性)",
                             "section": hm.group(0)[:60], "polarity": pm.group(0),
                             "line": line_no(text, lo + pm.start()),
                             "conclusion": ln.strip()[:90]})
            break
    return (bool(evidence), {"spec": "S4_SCRIPT_EXISTENCE_DETERMINATION",
                             "logic": "∃d[Determination(d) ∧ Subject(d,script) ∧ Q(d,Exists(script)) ∧ Resolved(d)] ∧ SameSection",
                             "evidence": evidence})


# ---------------------------------------------------------------------------
# S5 可重建 —— RECONSTRUCTIBILITY
#   token = 可(情态 ◇) + 重建(动作)。「可唯一重建」中「唯一」只强化算法确定性，不改情态头/动作头。
#   真值条件：◇Reconstruct(algorithm) ∧ ∃e Evidence(e, determinacy) ∧ ¬¬◇ ∧ ¬Pending。
#   角色：R1 重建动作 ∧ R2 肯定情态 ∧ R3 确定性证据；同一 `##` 小节，R2 不得被否定。
# ---------------------------------------------------------------------------

_RECON_RE = re.compile(r"重建|复现|复算|还原")
_MODAL_RE = re.compile(r"可唯一重建|可重建|可唯一复现|可复现|能重建|能够重建|可重建性|【可[^】]{0,8}重建】")
_EVID_RE = re.compile(
    r"唯一性|逐位一致|独立实现|口径唯一|max\|[^=\n]{1,12}\|\s*=\s*[\d.]+|"
    r"五项口径|\d+/\d+\s*(?:逐位|一致|命中)|完全一致|逐位复现|逐位相符"
)
_NEG_MODAL_RE = re.compile(r"不可重建|无法重建|不能重建|难以重建|重建不可|重建无法|未能重建")


def _s5_reconstructible(text: str):
    evidence = []
    for hm in HEADING_RE.finditer(text):
        lo = hm.start()
        hi = next((x.start() for x in HEADING_RE.finditer(text, lo + 1)), len(text))
        sec = text[lo:hi]
        ev = list(_EVID_RE.finditer(sec))
        if not ev:
            continue
        for mm in _MODAL_RE.finditer(sec):
            cl = clause_of(sec, mm.start())
            if _NEG_MODAL_RE.search(cl) or _pending(cl):
                continue
            if not _RECON_RE.search(mm.group(0)):
                continue
            evidence.append({"role": "R1(重建)∧R2(肯定情态)∧R3(确定性证据)",
                             "section": hm.group(0)[:60], "modal": mm.group(0),
                             "evidence": ev[0].group(0), "line": line_no(text, lo + mm.start()),
                             "clause": cl.strip()[:90]})
            break
    return (bool(evidence), {"spec": "S5_RECONSTRUCTIBILITY",
                             "logic": "◇Reconstruct(algo) ∧ ∃e Evidence(e,determinacy) ∧ ¬NegModal ∧ ¬Pending ∧ SameSection",
                             "evidence": evidence})


# ---------------------------------------------------------------------------
# 闭合注册表：key = 门禁必现要素的**精确字面串**（不做模糊/通配/embedding 匹配）
# ---------------------------------------------------------------------------

SPECS = {
    "需谁批准": {
        "id": "S1_WHO_APPROVER",
        "roles": ["批准人角色头", "赋值算子", "具体施事值"],
        "judge": _s1_who_approver,
        "basis": "wh-问句「需谁批准」指称其真答案集合；赋值句「批准人一律 = 乙设计责任人」把 wh-变量约束成具体施事，是该集合的一员且更强（另断言一律/唯一），故问答语义下等价。",
    },
    "实跑输出": {
        "id": "S2_EXEC_OUTPUT",
        "roles": ["实跑事件", "输出载荷(带具体值的 key=value 数据行)"],
        "judge": _s2_exec_output,
        "basis": "合取名词「实跑」+「输出」= ∃e Run(e) ∧ ∃o[Output(e,o) ∧ Present(o)]；「实跑返回」命名事件，围栏块内 verdict='…' conf='…' 是输出对象本身，两半齐备才成立。",
    },
    "改前改后": {
        "id": "S3_BEFORE_AFTER_PAIR",
        "roles": ["改前标签+实值", "改后标签+实值", "对照算子"],
        "judge": _s3_before_after,
        "basis": "无分隔并列「改前」∧「改后」；斜杠/【】只是并列分隔符与槽位标记，逻辑合取不变（交换律）。",
    },
    "脚本存在性": {
        "id": "S4_SCRIPT_EXISTENCE_DETERMINATION",
        "roles": ["脚本对象", "存在性谓词", "判定算子", "已决断极性"],
        "judge": _s4_script_existence,
        "basis": "定摹状词「脚本存在性」= 关于 Exists(script) 的一项已决断判定；极性正负都算已交付（问的是判定，不是存在）。",
    },
    "可重建": {
        "id": "S5_RECONSTRUCTIBILITY",
        "roles": ["重建动作", "肯定情态", "确定性证据"],
        "judge": _s5_reconstructible,
        "basis": "「可」= ◇ 情态头，「重建」= 动作头；「可唯一重建」中「唯一」只强化算法确定性，不换头不改情态，故 ◇Reconstruct 成立，且有独立实现逐位一致作证据。",
    },
}


def r9s_element_present(text: str, token: str):
    """返回 (present, layer, detail)。

    layer ∈ {"raw", "normalized", "semantic", ""}。
    raw/normalized 与 R9 完全相同（短路）；semantic = L2 语义要素层命中；
    "" = 三层全缺。detail 含命中的角色证据，可审计。
    """
    ok, layer = R9.r9_element_present(text, token)
    if ok:
        spec_pre = SPECS.get(token)
        # 承诺守卫：已登记要素的字面出现若全被否定/待定语境吞掉，判「未交付」。
        # 这是**收紧**（只会把 True 改成 False），不会造成任何放松；
        # 未登记 token 一律原样放行，保持 R9S ≡ R9。
        if spec_pre is not None and not _commitment_ok(text, token, spec_pre["id"]):
            return False, "", {
                "layer": "", "spec": spec_pre["id"], "evidence": [],
                "logic": "L0/L1 字面命中，但全部出现被 ¬NegCancel ∨ Pending 取消 → 言语行为未交付（收紧）",
            }
        return True, layer, {"layer": layer, "spec": None, "evidence": [],
                             "logic": "L0/L1 原样 R9 命中，未进入语义层"}
    spec = SPECS.get(token)
    if spec is None:
        return False, "", {"layer": "", "spec": None, "evidence": [],
                           "logic": "token 未登记语义要素规格 → R9S ≡ R9（不放宽）"}
    good, detail = spec["judge"](text)
    if good:
        detail["layer"] = "semantic"
        return True, "semantic", detail
    detail["layer"] = ""
    return False, "", detail


def r9s_check(text: str, tokens):
    """与 g7.r9_check 同签名同契约：(problems, warnings)。

    仅把「缺要素」判定换成 r9s_element_present；semantic 命中登记 warning（可审计），
    但仍计为在场、不产生 problem。
    """
    problems, warnings = [], []
    for k in tokens:
        ok, layer, _ = r9s_element_present(text, k)
        if not ok:
            problems.append("缺要素 " + k + "（R9：raw 与归一化文本双缺；R9S 语义层亦缺）")
        elif layer == "normalized":
            warnings.append("要素 %s 仅在包裹归一化后命中（raw 层缺字面）" % k)
        elif layer == "semantic":
            warnings.append("要素 %s 由语义要素层命中（raw 与归一化双缺，结构证据齐备）" % k)
    return problems, warnings


def spec_inventory():
    """闭合注册表清单（用于证明词表不膨胀：条目数 = 已登记语义要素数，非措辞数）。"""
    return {k: {"id": v["id"], "roles": list(v["roles"]), "basis": v["basis"]}
            for k, v in SPECS.items()}
