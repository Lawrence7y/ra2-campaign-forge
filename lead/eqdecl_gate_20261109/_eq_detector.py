# -*- coding: utf-8 -*-
"""
_eq_detector.py — 「两段式等式声明」门禁检测器（只读、零真机、零采样代码）

输入：一份 .md（绝对路径）；输出：findings 列表（JSON 可序列化）。
每条 finding 含：file:line / 原文行 / 失败型 F1|F2|F3 / 缺什么（missing + all_missing）。
另给 category（TAUTOLOGY / SUBSTANTIVE / UNDECIDABLE）与 skip 计数。
任何一条命中都附 file:line 与命中的原文行（evidence_lines / evidence_matches）。

判据形式定义见同目录 _eq_DESIGN.md。
运行： python -I -X utf8 <本文件> --selftest
       python -I -X utf8 <本文件> --scan <绝对 .md 路径> [--out <绝对 json 路径>]
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# 常量：全部为逐字串，来源于本会话实读的真实 file:line（见 _eq_DESIGN.md §1）
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WINDOW_RADIUS = 8   # 见 _eq_DESIGN.md §4：本语料实测最大跨行距离 = 8
LOCAL_RADIUS = 2    # 锚点局部半径，见 classify_window 注释（强度/范围邻接判据）

# M1 显式等式 / 等价符号
M1 = {
    "M1a_A=B": [r"A\s*=\s*B", r"A==B"],
    "M1b_⟺": [r"⟺"],
    "M1c_⇔": [r"⇔"],
    "M1d_⊆": [r"A\s*⊆\s*B", r"B\s*⊆\s*A", r"⊆"],
}
# M2 中文等价式
M2 = {
    "M2a_等价于": [r"等价于"],
    "M2b_同一个命题": [r"同一个命题"],
    "M2c_同一命题": [r"同一命题"],
    "M2d_不是近似": [r"不是近似", r"近似省一层"],
    "M2e_恰好等于": [r"恰好等于", r"完全相同", r"逐一相同", r"逐 id"],
}
# M3 强度标签
M3 = {
    "M3a_决定性": [r"决定性"],
    "M3b_定理": [r"定理"],
    "M3c_已证": [r"已证"],
    "M3d_恒等": [r"恒等"],
}
# M4 集合断言（按逐字形态，含单复数变体；见 _eq_DESIGN.md §1 注）
M4 = {
    "M4a_18个id": [r"18 个 id", r"18个id"],
    "M4b_only_A_B": [r"only_A", r"only_B"],
    "M4c_set_equal": [r"set equal\? True", r"sets equal\? True", r"A==B True"],
    "M4d_集合恒等": [r"集合恒等\? True", r"集合恒等"],
    "M4e_完全相同": [r"完全相同", r"逐 id 比对通过"],
    # S12 真实形态：SCORE_DECOMP.md:233,235 逐字「恒真兜底」
    "M4f_恒真兜底": [r"恒真兜底", r"恒真", r"恒 CATCH 兜底", r"必然命中"],
    # S7 真实形态：KEFF_CALC.md:262 逐字「≤ min q_i」/「取等」
    "M4g_取等": [r"≤\s*min q_i", r"取等", r"恰取", r"Fréchet", r"Frechet"],
}
# M5 观测数值 / 统计形态
M5 = {
    "M5a_38/38": [r"38/38"],
    "M5b_0bit": [r"0 bit", r"0\.0 bit"],
    "M5c_本N行": [r"本 74 行", r"本批 74 行", r"本批语料", r"仅 N 行", r"仅 74 行",
                r"N 74", r"74 行", r"观测", r"样本巧合", r"train=test", r"95%"],
    "M5d_实跑输出": [r"实跑命令", r"输出", r"sets equal\? True", r"set equal\? True",
                 r"集合恒等\? True", r"n13=PASS n= 38", r"38/74", r"22→0",
                 r"chain_changed=18", r"unresolved_changed=18", r"一致性?率"],
}

ALL_M: dict[str, list[str]] = {}
for _d in (M1, M2, M3, M4, M5):
    ALL_M.update(_d)

# Q1 重言半：标签（须在锚点行或窗内）+ 结构展开
Q1_LABEL = [r"重言式", r"重言半", r"定义重言式", r"逻辑重言式", r"零信息量",
            r"恒真兜底", r"恒真", r"重言"]
# ★ 锚点行自身的重言标签：类别判定的唯一依据（只读作者显式标签，不猜语义）
TAUT_LABEL_ON_LINE = [r"重言式", r"重言半", r"恒真兜底", r"零信息量", r"恒真"]
Q1_STRUCT = [r"A\s*=\s*B∩", r"A=B∩", r"去掉一个合取项", r"合取项", r"A\s*⊆\s*B",
             r"定义式", r"X=X", r"代回", r"8 格", r"8 种真值格局", r"穷举",
             r"合取消去", r"恒 CATCH 兜底", r"必然命中"]

# Q2 实质半
Q2 = [r"B\s*⊆\s*A", r"实质半", r"非平凡", r"forbidden", r"禁止格", r"不存在格",
      r"额外排除", r"破口", r"反例", r"构造", r"什么输入会破", r"分叉格",
      r"破坏它的输入", r"X1/X2/X3", r"X1", r"forbidden sets"]

# Q3 依据四类（TAUTOLOGY_AUDIT.md:263-266）
BASIS_LOGIC = [r"纯逻辑", r"定义式", r"代回 X=X", r"合取消去", r"逻辑连接词",
               r"重言式", r"逻辑重言式", r"定义重言式", r"零信息量",
               r"恒真兜底", r"合取项"]           # 纯逻辑重言式自身即依据
BASIS_CODE = [r"依赖图", r"代码级", r"_g7_predicates\.py", r"_gp_pipeline\.py",
              r"_ei_n13_predicates_src\.py", r"file:line", r"数学定理", r"Fréchet",
              r"Frechet", r"源码蕴含", r"因果图", r"_v12_rule\.py", r"定理"]
BASIS_OBS = [r"本 74 行", r"本批语料", r"本批 74 行", r"仅 N 行", r"仅 74 行",
             r"N 74", r"74 行", r"train=test", r"SHA256", r"95%", r"观测",
             r"样本巧合", r"实跑", r"实测", r"样本内", r"本会话实跑"]
BASIS_ANY = BASIS_LOGIC + BASIS_CODE + BASIS_OBS

# Q4 范围声明（含本会话实读补入的逐字形态：LAYER_IDENTITY.md:128「在 74 行上同真」「额外巧合」）
SCOPE = [r"本 74 行", r"本批 74 行", r"本批语料", r"仅 N 行", r"仅 74 行", r"样本内",
         r"train=test", r"观测值", r"观测等式", r"反事实", r"条件行", r"未验",
         r"本谓词 SHA", r"本 tokens", r"换行口径", r"契约", r"样本巧合",
         r"不是定理", r"不是恒等式", r"不是逻辑恒等式", r"描述性", r"95%",
         r"上界", r"CI", r"受限", r"在 74 行上", r"74 行上", r"巧合", r"同真",
         r"样本巧合 \+ 契约巧合"]

# 观测证据标记 O（F3 用）：M5 观测数值 + 显式集合相等输出
OBS_EVIDENCE = [r"38/38", r"0 bit", r"0\.0 bit", r"1\.000", r"set equal\? True",
                r"sets equal\? True", r"集合恒等\? True", r"18 个 id", r"only_A",
                r"only_B", r"实跑命令", r"n13=PASS n= 38", r"38/74", r"22→0",
                r"chain_changed=18", r"unresolved_changed=18", r"一致性?率",
                r"取等", r"实测"]

# 强度标签 I（F3 用）。★ 不含泛化「必然 / 全称」：
# SCORE_DECOMP.md:235 逐字「恒真兜底在正类样本上的必然命中」里的「必然」是
# 对兜底行为的描述，不是把观测等式升级为定理；把它当 I 会误报 S12（关一）。
INTENSITY = [r"决定性", r"定理", r"已证", r"恒成立", r"恒等式",
             r"逻辑恒等", r"结构性定理", r"必相等"]
# 全称口吻（S5「R12 增量判别力 = 0 bit」全称、S8「38/38」全称）：
# 数值/零增量断言本身若无「本 N 行」限定即隐含全称，视作强度侧信号。
UNIVERSAL_CLAIM = [r"=\s*0 bit", r"0 bit", r"=\s*1\.000", r"38/38=1",
                   r"增量判别力", r"不提供任何新信息", r"恒 PASS"]

# 显式等式 / 等价 / 集合断言 E（F1 / skip 用）
E_MARKERS = [r"A\s*=\s*B", r"A==B", r"⟺", r"⇔", r"⊆", r"等价于", r"同一个命题",
             r"同一命题", r"不是近似", r"近似省一层", r"恰好等于", r"完全相同",
             r"逐一相同", r"逐 id", r"only_A", r"only_B", r"set equal\? True",
             r"sets equal\? True", r"集合恒等\? True", r"A==B True", r"18 个 id",
             r"恒真兜底", r"取等", r"≤\s*min q_i"]

# ★ F1 专用的「严格等式声明」：只有这些形态才触发「两段式声明」义务。
#   排除两类真实质条件（关二要求不误报）：
#   (1) S2「不是近似省一层」是**正确否定句**（TAUTOLOGY_AUDIT.md:447 逐字
#       「本身正确，不列入撤回对象」），它没有断言等式，不需拆两半；
#   (2) S7「P(allPASS|E) ≤ min q_i」是 Fréchet 不等式 + 数值取等
#       （KEFF_CALC.md:262），是数学定理，不是 A=B 型集合恒等。
#   检测器只读形态，不替作者推断「这算不算等式」⇒ 宁可少报也不猜。
E_EQ_STRICT = [r"A\s*=\s*B", r"A==B", r"⟺", r"⇔", r"⊆", r"等价于",
               r"同一个命题", r"同一命题", r"恰好等于", r"完全相同",
               r"逐一相同", r"逐 id", r"only_A", r"only_B",
               r"set equal\? True", r"sets equal\? True", r"集合恒等\? True",
               r"A==B True", r"18 个 id", r"恒真兜底"]

# 整改意见 / 纯转述（skip K5）
QUOTE_OR_REVIEW = [r"→\s*改", r"须撤回", r"判错置", r"须修正措辞", r"应改为",
                   r"改「", r"撤回", r"须降级", r"须删除", r"删除「"]

# 「纠偏语境」：强度标签被明确否定（不是定理 / 不是恒等式 / 未验 / 须撤回 等）。
# ★ 不含泛化「不是 / 不成立」：S2 的「不是近似省一层」是**正确否定句**
#   （TAUTOLOGY_AUDIT.md:447 逐字判「本身正确，不列入撤回对象」）。
CORRECTION = [r"不是定理", r"不是恒等式", r"不是逻辑恒等式", r"不是精确 1\.000",
              r"是否定理", r"⇒\s*未验", r"未验", r"须撤回", r"须降级",
              r"须修正措辞", r"强度夸大", r"判错置", r"不得读作",
              r"仍是提案", r"现状：未实装", r"不是结构性定理"]
# 提问句（「是否定理：未验」）不是断言，按 K3 跳过，不作「正确限定」
QUESTION = [r"是否", r"是否定理", r"\?\s*$", r"？\s*$"]

HARD_BOUNDARY = re.compile(r"^\s*$|^#{1,6}\s|^-{3,}\s*$|^\s*```")


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _hits(text: str, pats: list[str]) -> list[str]:
    out: list[str] = []
    for p in pats:
        m = re.search(p, text)
        if m and m.group(0) not in out:
            out.append(m.group(0))
    return out


def _has(text: str, pats: list[str]) -> bool:
    return any(re.search(p, text) for p in pats)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_lines(path: pathlib.Path) -> tuple[list[str], str | None, int, str]:
    try:
        b = path.read_bytes()
        return b.decode("utf-8", errors="replace").split("\n"), None, len(b), sha256_bytes(b)
    except OSError as e:
        return [], f"read_error:{type(e).__name__}:{e}", 0, ""


def rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# 段落窗口（状态机 SCAN → IN_WINDOW → EMIT/SKIP，见 _eq_DESIGN.md §4）
# ---------------------------------------------------------------------------
def build_segments(lines: list[str]) -> list[tuple[int, int]]:
    """硬边界：空行 / ^#{1,6}\\s / ^---+$ / 代码围栏。返回 1-based 闭区间。"""
    segs: list[tuple[int, int]] = []
    start = None
    for i, l in enumerate(lines, 1):
        if HARD_BOUNDARY.match(l):
            if start is not None:
                segs.append((start, i - 1))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        segs.append((start, len(lines)))
    return [s for s in segs if s[0] <= s[1]]


def anchor_lines(lines: list[str]) -> dict[int, list[str]]:
    """{行号: 命中的 M 子形态名}；仅命中 M1–M5 的行成为候选断言锚点。"""
    out: dict[int, list[str]] = {}
    for i, l in enumerate(lines, 1):
        ms = [k for k, pats in ALL_M.items() if _has(l, pats)]
        if ms:
            out[i] = ms
    return out


def window_for(anchor: int, seg: tuple[int, int], lines: list[str]) -> tuple[int, int, list[str]]:
    """W = [anchor-R, anchor+R] ∩ 当前硬边界段落。"""
    lo = max(seg[0], anchor - WINDOW_RADIUS)
    hi = min(seg[1], anchor + WINDOW_RADIUS)
    return lo, hi, [lines[n - 1] for n in range(lo, hi + 1)]


# ---------------------------------------------------------------------------
# 核心判定
# ---------------------------------------------------------------------------
def classify_window(anchor: int, anchor_morphs: list[str], lo: int, hi: int,
                    wlines: list[str], lines: list[str]) -> dict[str, Any]:
    """对单个窗口产一条判定记录（finding / pass / tautology_ok / skip / undecidable）。"""
    wtext = "\n".join(wlines)
    atext = lines[anchor - 1]

    # 锚点局部窗口 ±LOCAL_RADIUS 行。本会话实跑量测「强度标签行 → 最近范围词」
    # 距离分布 0:288 / 1:90 / 2:86 / 3:61 / 4:22 ⇒ 85% 的真实已限定断言把范围
    # 写在 ±2 行内。强度 I 用局部窗口；F3 的范围 R 用**锚点行自身**（见下）。
    l_lo = max(lo, anchor - LOCAL_RADIUS)
    l_hi = min(hi, anchor + LOCAL_RADIUS)
    local_text = "\n".join(lines[n - 1] for n in range(l_lo, l_hi + 1))

    E = _has(wtext, E_MARKERS)
    E_eq = _has(wtext, E_EQ_STRICT)   # F1 义务只施加于严格等式声明
    O = _has(wtext, OBS_EVIDENCE)
    R = _has(wtext, SCOPE)
    # ★ F3 的「范围声明」必须在锚点行自身：任务 F3 定义是「把仅 N 行观测
    #   **直接接**强度标签，中间无范围声明」。「中间」= 同一行两者之间。
    #   用整窗/±2 取 R 会把 8 行之外或邻行的无关「反事实 / 未验」误当范围
    #   （本会话实跑：METRIC_CONVENTION_AUDIT.md:110 的「反事实基线期望」
    #   会让 :108 的 F3 被错误洗掉）。同行判据是可复核的字面判据，不是猜测。
    R_same_line = _has(atext, SCOPE)
    R_local = _has(local_text, SCOPE)

    I_raw = _has(local_text, INTENSITY)
    U_local = _has(local_text, UNIVERSAL_CLAIM)
    denial = _has(atext, CORRECTION)          # 纠偏语境只在锚点行自身判定
    I = (I_raw or U_local) and not denial
    I_hits = (_hits(atext, INTENSITY) or _hits(local_text, INTENSITY) or
              _hits(atext, UNIVERSAL_CLAIM))

    B = _has(wtext, BASIS_ANY)
    B_logic = _has(wtext, BASIS_LOGIC)
    B_code = _has(wtext, BASIS_CODE)
    B_obs = _has(wtext, BASIS_OBS)
    T = _has(wtext, Q1_LABEL) and _has(wtext, Q1_STRUCT)
    S = _has(wtext, Q2)

    non_obs_morphs = [k for k in anchor_morphs if not k.startswith("M5")]
    assertion_object = E or O or I_raw or U_local or bool(non_obs_morphs)
    # 纠偏语境（强度标签被明确否定/撤回）也是一条「断言对象」：
    # 它是关于该等式强度的正确限定，不是无关文本，不能按 K1/K3 跳过。
    if denial and R_same_line:
        assertion_object = True

    # ---- 类别判定：只读作者在该行写下的显式重言标签，不猜语义 ----
    # 上游一句话判据（TAUTOLOGY_AUDIT.md:270-271）：「能在不读任何数据、
    # 不读任何代码的情况下只靠逻辑连接词就证明，那一半是重言式」。
    # 检测器无法自行证明，故以作者显式标签为准；标签 + 结构展开同现才判 TAUTOLOGY。
    taut_line = _has(atext, TAUT_LABEL_ON_LINE) and _has(wtext, Q1_STRUCT)
    if taut_line:
        category = "TAUTOLOGY"
    elif assertion_object or I or O:
        category = "SUBSTANTIVE"
    else:
        category = "UNDECIDABLE"

    # ---- skip 判据 K1–K5（宁可报无法判定也不许猜）----
    skip_reason = None
    if _has(atext, QUESTION):
        skip_reason = "K3_question_not_assertion"
    elif denial and R_same_line:
        # 「不是定理 / 未验 / 须撤回」+ 同行范围 = 正确限定，不跳过、不报 F3
        skip_reason = None
    elif _has(atext, [r"恒等"]) and not E and not O and not I:
        skip_reason = "K2_ident_word_other_domain"
    elif I_raw and not E and not O:
        skip_reason = "K3_intensity_without_assertion_object"
    elif T and S and B_obs and _has(wtext, [r"全称定理", r"逻辑必然 = 是"]) and not R:
        skip_reason = "K4_conflict_scope_basis"
    elif _has(atext, QUOTE_OR_REVIEW) and not E and not O:
        skip_reason = "K5_pure_quotation"
    elif (not I) and (not E):
        # 任务 (c)：既无明显强度标签、又无显式等式 ⇒ 跳过而不是猜
        skip_reason = "K1_no_equality_no_intensity"

    base: dict[str, Any] = {
        "file": "",
        "file:line": f"FILE:{anchor}",
        "line": anchor,
        "text": atext,
        "window": [lo, hi],
        "window_lines": [f"FILE:{n}" for n in range(lo, hi + 1)],
        "morphs": anchor_morphs,
        "matched_strings": _hits(atext, [p for k in anchor_morphs for p in ALL_M[k]]),
        "flags": {
            "E": E, "E_eq": E_eq, "I_raw": I_raw, "I": I, "U_local": U_local, "O": O,
            "R": R, "R_local": R_local, "R_same_line": R_same_line,
            "B": B, "B_logic": B_logic, "B_code": B_code, "B_obs": B_obs,
            "T": T, "S": S, "taut_line": taut_line,
            "correction_context": denial, "assertion_object": assertion_object,
        },
        "category": category,
    }
    if skip_reason:
        base.update({"verdict": "SKIP", "skip_reason": skip_reason,
                     "failure_type": None, "missing": None, "all_missing": []})
        return base

    # ---- 失败型，优先级 F3 > F2 > F1 ----
    # ★ F2 只追究「本件确实写了两段式声明」的情形：真重言式 / 正确等价式 /
    #   Fréchet 定理等**单一命题**不是两段式声明，其依据自足，不因窗口里
    #   没写「依据=」而报 F2（否则关一 S1/S3、关二 S4 会被误报，已实跑证实）。
    declares_two_stage = T and S
    logic_self_based = T and B_logic and not B_obs

    all_missing: list[str] = []
    if not T and not S:
        all_missing.append("Q1 重言半缺失")
    if T and not S:
        all_missing.append("Q2 实质半缺失")
    if declares_two_stage and not B:
        all_missing.append("Q3 依据缺失")
    if declares_two_stage and B_obs and not R:
        all_missing.append("Q4 仅 N 行观测缺范围声明")

    f3 = I and O and not R_same_line
    f2 = (declares_two_stage and not logic_self_based and
          ((not B) or (B_obs and not R)))
    f1 = E_eq and (not T) and (not S)
    corrected_scope = denial and R_same_line and not f3

    if f3:
        ftype, verdict = "F3", "FAIL"
        missing = ("强度标签 " + "/".join(I_hits[:3]) +
                   " 与观测证据在同一断言上共现，中间无范围声明；缺 Q4 范围声明")
    elif corrected_scope:
        # 强度标签被明确否定且带范围：正确限定/撤回，不报 F1/F2/F3
        ftype, verdict, missing = None, "CORRECTLY_SCOPED", None
    elif f2:
        ftype, verdict = "F2", "FAIL"
        missing = "；".join(x for x in all_missing if "Q1 重言半" not in x) or "Q3 依据缺失"
    elif f1:
        ftype, verdict = "F1", "FAIL"
        missing = "Q1 重言半 + Q2 实质半两半全缺；无 A⊆B / B⊆A 拆分"
    elif category == "TAUTOLOGY":
        # 真重言式：显式报出（关一「必须报」），不猜为实质条件
        ftype, verdict, missing = None, "TAUTOLOGY_OK", None
    elif T and S and B and (not B_obs or R):
        ftype, verdict, missing = None, "PASS_QUALIFIED", None
    elif not E_eq and category == "SUBSTANTIVE" and not I:
        # 真实质条件（非 A=B 型等式声明）：不施加两段式义务，
        # 也不报 F1/F2/F3。关二 S2/S7 即此类（只读形态，不猜语义）。
        ftype, verdict, missing = None, "SUBSTANTIVE_OK", None
    else:
        base.update({"verdict": "UNDECIDABLE", "failure_type": None,
                     "missing": "窗口结构齐全但无法归类（不猜）",
                     "all_missing": all_missing,
                     "skip_reason": "K6_structure_unclassifiable"})
        return base

    base.update({"verdict": verdict, "failure_type": ftype, "missing": missing,
                 "all_missing": all_missing, "skip_reason": None})
    return base


def scan_file(path: pathlib.Path) -> dict[str, Any]:
    """输入一份 .md，输出 findings / passes / tautology_ok / skips / undecidables。"""
    lines, err, nbytes, sha = read_lines(path)
    rec: dict[str, Any] = {
        "file": rel(path), "abs": str(path), "sha256": sha, "bytes": nbytes,
        "n_lines": len(lines), "window_radius": WINDOW_RADIUS,
        "local_radius": LOCAL_RADIUS,
    }
    if err:
        rec.update({"read_error": err, "findings": [], "passes": [], "tautology_ok": [],
                    "skips": [], "undecidables": [], "error": err})
        return rec

    segs = build_segments(lines)
    anchors = anchor_lines(lines)
    findings, passes, taut_ok, skips, undec = [], [], [], [], []

    for a in sorted(anchors):
        seg = next((s for s in segs if s[0] <= a <= s[1]), (a, a))
        lo, hi, wlines = window_for(a, seg, lines)
        r = classify_window(a, anchors[a], lo, hi, wlines, lines)
        f = rec["file"]
        r["file"] = f
        r["file:line"] = f"{f}:{a}"
        r["window_lines"] = [f"{f}:{n}" for n in range(lo, hi + 1)]
        # 任何一条命中都必须附 file:line 与命中的原文行
        r["evidence_lines"] = [
            {"file:line": f"{f}:{n}", "text": lines[n - 1]}
            for n in range(lo, hi + 1)
        ]
        r["evidence_matches"] = [
            {"kind": k, "file:line": f"{f}:{n}", "text": lines[n - 1],
             "matched": _hits(lines[n - 1], pats)}
            for n in range(lo, hi + 1)
            for k, pats in (("E", E_MARKERS), ("I", INTENSITY + UNIVERSAL_CLAIM),
                            ("O", OBS_EVIDENCE), ("R", SCOPE))
            if _hits(lines[n - 1], pats)
        ]
        v = r["verdict"]
        if v == "FAIL":
            findings.append(r)
        elif v in ("PASS_QUALIFIED", "CORRECTLY_SCOPED", "SUBSTANTIVE_OK"):
            passes.append(r)
        elif v == "TAUTOLOGY_OK":
            taut_ok.append(r)
        elif v == "SKIP":
            skips.append(r)
        else:
            undec.append(r)

    skip_by_reason: dict[str, int] = {}
    for s in skips + undec:
        k = s.get("skip_reason") or "UNSET"
        skip_by_reason[k] = skip_by_reason.get(k, 0) + 1
    by_ftype: dict[str, int] = {}
    for x in findings:
        by_ftype[x["failure_type"]] = by_ftype.get(x["failure_type"], 0) + 1

    rec.update({
        "n_segments": len(segs), "n_anchors": len(anchors),
        "n_findings": len(findings), "n_passes": len(passes),
        "n_tautology_ok": len(taut_ok), "n_skips": len(skips),
        "n_undecidables": len(undec),
        "skipped_total": len(skips) + len(undec),
        "skip_by_reason": skip_by_reason, "findings_by_type": by_ftype,
        "findings": findings, "passes": passes, "tautology_ok": taut_ok,
        "skips": skips, "undecidables": undec,
    })
    return rec


# ---------------------------------------------------------------------------
# 正控 / 负控（检测器自造文本，不触碰被检文档；落盘 _eq_selftest_out.json）
# ---------------------------------------------------------------------------
def controls() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(cid: str, name: str, text: str, expect_verdict: str,
            expect_ftype: str | None, expect_category: str | None, note: str) -> None:
        lines = text.split("\n")
        segs = build_segments(lines)
        anchors = anchor_lines(lines)
        a = min(anchors) if anchors else 1
        seg = next((s for s in segs if s[0] <= a <= s[1]), (a, a))
        lo, hi, wlines = window_for(a, seg, lines)
        r = classify_window(a, anchors.get(a, []), lo, hi, wlines, lines)
        r["file"] = f"<control:{cid}>"
        r["file:line"] = f"<control:{cid}>:{a}"
        cases.append({
            "id": cid, "name": name, "input_text": text,
            "expect_verdict": expect_verdict, "expect_failure_type": expect_ftype,
            "expect_category": expect_category,
            "actual_verdict": r["verdict"], "actual_failure_type": r["failure_type"],
            "actual_category": r["category"], "flags": r["flags"],
            "missing": r["missing"], "skip_reason": r.get("skip_reason"),
            "passed": (r["verdict"] == expect_verdict and
                       r["failure_type"] == expect_ftype and
                       (expect_category is None or r["category"] == expect_category)),
            "note": note,
        })

    add("P1", "正控：裸集合等式、两半全缺 → F1",
        "chain_changed=18 | unresolved_changed=18 | 集合恒等? True",
        "FAIL", "F1", None, "复刻 COMPARABILITY_AUDIT.md:158 逐字形态（检测器自造）")
    add("P2", "正控：决定性 + 观测证据、无同行范围 → F3",
        "3. **决定性集合等式**：实跑命令 2 输出 2layerPASS= 18 set equal? True，即 18 个 id 恰好等于。",
        "FAIL", "F3", "SUBSTANTIVE", "复刻 METRIC_CONVENTION_AUDIT.md:108 逐字形态（检测器自造）")
    add("P3", "正控：两半齐全、依据为 N 行观测却无范围 → F2",
        "`A ⊆ B` 是去掉一个合取项的重言式；`B ⊆ A` 非平凡方向禁止格为空，实跑 74 行统计 cells=0 set equal? True。",
        "FAIL", "F2", None, "T=True S=True B_obs=True R=False ⇒ Q4 缺失（检测器自造）")
    add("P4", "正控：跨行两段式（重言半在第 1 行、实质半在第 3 行）→ F2",
        "`A ⊆ B` 是去掉一个合取项的重言式。\n- 数据：实跑 `cells_r10C_n13P_r12C = 0`、`set equal? True`。\n- `B ⊆ A` 非平凡方向禁止格为空。",
        "FAIL", "F2", None, "跨行窗口半径 8 覆盖；T@1 / S@3 距离 2（检测器自造）")
    add("N1", "负控：强度标签被否定 + 同行有范围 → 不报 F3",
        "⇒ `P(r12=PASS|n13=PASS)=38/38=1.000` 是**本 74 行上的观测值，不是精确 1.000、不是定理**。",
        "CORRECTLY_SCOPED", None, "SUBSTANTIVE", "复刻 KEFF_CALC.md:314 逐字形态（检测器自造）")
    add("N2", "负控：代码级依据 + 范围 → 合格",
        "根因不是近似省一层，而是 **R12 不是独立证据根**：依赖图为单一根 R10 → {R12, N13.C}；本 74 行观测。\n"
        "`A ⊆ B` 是去掉一个合取项的重言式，`B ⊆ A` 只排除 `(r10=P,n13=P,r12=C)` 格；依据=代码级依赖图 file:line。",
        "PASS_QUALIFIED", None, None, "复刻 METRIC_CONVENTION_AUDIT.md:104/106 与 LAYER_IDENTITY.md:104 组合（检测器自造）")
    add("N3", "负控：别论域「恒等」、无等式无观测 → skip",
        "本节讨论帧率恒等，与集合断言无关。",
        "SKIP", None, None, "K2（检测器自造）")
    add("N4", "负控：既无等式也无强度标签 → skip",
        "本行只是普通叙述，没有断言。",
        "SKIP", None, None, "K1（检测器自造）")
    add("N5", "负控：提问式「是否定理」 → skip",
        "`P(r12=PASS|n13=PASS)=1.000` 是否定理：未验。",
        "SKIP", None, None, "K1/K3（检测器自造）")
    add("N6", "负控：真重言式类别判定 TAUTOLOGY 且不报 F1/F2/F3",
        "`A ⊆ B` 是去掉一个合取项的逻辑重言式，`A = B∩{r12=PASS}`；8 格穷举 F(A⊆B)=[]，零信息量。\n"
        "`B ⊆ A` 非平凡方向禁止格 `(r10=P,n13=P,r12=C)`，依据=本批语料的观测等式，本 74 行。",
        "TAUTOLOGY_OK", None, "TAUTOLOGY", "关一形态（检测器自造）")
    return cases


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        cs = controls()
        out = {
            "n_controls": len(cs),
            "n_passed": sum(1 for c in cs if c["passed"]),
            "n_failed": sum(1 for c in cs if not c["passed"]),
            "controls": cs,
        }
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["n_failed"] == 0 else 1

    if "--scan" in argv:
        i = argv.index("--scan")
        rec = scan_file(pathlib.Path(argv[i + 1]))
        if "--out" in argv:
            j = argv.index("--out")
            op = pathlib.Path(argv[j + 1])
            op.parent.mkdir(parents=True, exist_ok=True)
            op.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            print(json.dumps({"written": str(op), "file": rec["file"],
                              "n_findings": rec.get("n_findings"),
                              "n_tautology_ok": rec.get("n_tautology_ok"),
                              "n_skips": rec.get("n_skips"),
                              "n_undecidables": rec.get("n_undecidables"),
                              "findings_by_type": rec.get("findings_by_type"),
                              "skip_by_reason": rec.get("skip_by_reason")},
                             ensure_ascii=False))
        else:
            print(json.dumps({k: v for k, v in rec.items()
                              if k not in ("findings", "passes", "tautology_ok",
                                           "skips", "undecidables")},
                             ensure_ascii=False, indent=1))
        return 0

    print(json.dumps({"usage": "--selftest | --scan <abs.md> [--out <abs.json>]",
                     "module": "_eq_detector", "window_radius": WINDOW_RADIUS,
                     "local_radius": LOCAL_RADIUS}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
