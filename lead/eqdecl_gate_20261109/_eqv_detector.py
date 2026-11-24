# -*- coding: utf-8 -*-
"""
_eqv_detector.py — 复核员独立检测器（不复用实现员 _eq_detector.py 的代码与串表）。

判据直接取自本会话实读的上游原文：
- lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md:258-271（§3.1 五问 + 一句话判据）
- :315 / :536-538（两段式强制格式 A=B ⟺ [重言半] ∧ [实质半]）
- :446-461（§4.3 S1–S16 期望分类）
- :474（F3 要害：把 set equal? True 直接接「决定性」标签，中间无范围声明）
- :690-704（§6.4 十条准则）

三关（编排方【任务】第三步）：
关一 = 真重言式判「重言式」且不报 F1/F2/F3；关二 = 真实质条件不误报 F1/F2/F3；
关三 = 观测等式写成定理报 F3。

只读；零真机；纯 re/pathlib/hashlib。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WIN_R = 8    # 段落窗口半径（复核员 _eqv_measure.py 独立量测后确认）
LOC_R = 2    # 锚点局部半径（强度/范围邻接）

# ================= 标记表（复核员自拟，逐字串来自被检语料实读） =================
M_SET_EQ = [r"set equal\? True", r"sets equal\? True", r"集合恒等\? True", r"A==B\s*True",
            r"恰好等于", r"逐 id 相等", r"同一个 18 个 id 的集合",
            r"only_A\s*(?:=\s*)?\[\]\s*only_B\s*(?:=\s*)?\[\]"]
M_IFF = [r"⟺", r"⇔", r"等价于", r"同一命题", r"同一个命题", r"当且仅当"]
M_SUBSET = [r"⊆"]
M_APPROX = [r"近似省一层", r"不是近似"]
M_INTENS = [r"决定性", r"定理", r"已证", r"恒等式", r"必相等", r"恒成立", r"结构性定理"]
M_UNIV = [r"=\s*0 bit", r"0 bit", r"=\s*1\.000", r"38/38\s*=\s*1", r"增量判别力",
          r"恒 PASS", r"不提供任何新信息"]
M_OBS = [r"38/38", r"0 bit", r"0\.0 bit", r"1\.000", r"set equal", r"集合恒等",
         r"18 个 id", r"only_A", r"only_B", r"实跑", r"实测", r"38/74", r"22→0",
         r"一致率", r"n=\s*38"]
M_INEQ = [r"≤\s*min q_i", r"恰取等", r"取等"]
M_SCOPE = [r"本 74 行", r"本批语料", r"本批 74 行", r"74 行上", r"观测值", r"观测等式",
           r"样本巧合", r"巧合", r"不是定理", r"不是恒等式", r"不是精确", r"未验",
           r"反事实", r"条件行", r"train=test", r"95%", r"契约", r"谓词 SHA",
           r"换行口径", r"描述性", r"上界", r"受限", r"不是逻辑必然", r"别论域"]
M_TAUT = [r"重言式", r"重言半", r"恒真兜底", r"零信息量", r"恒真", r"逻辑重言式"]
M_TAUT_STRUCT = [r"合取项", r"去掉一个", r"8 格", r"八格", r"穷举", r"⊆", r"定义式",
                 r"代回", r"合取消去", r"恒 CATCH", r"信息量\s*=\s*0"]
M_SUBST = [r"B\s*⊆\s*A", r"非平凡", r"forbidden", r"禁止格", r"不存在格", r"反例",
           r"额外排除", r"什么输入会破", r"分叉格"]
M_BASIS_CODE = [r"依赖图", r"代码级", r"\.py", r"file:line", r"Fréchet", r"数学定理",
                r"源码蕴含"]
M_BASIS_OBS = [r"本 74 行", r"本批语料", r"74 行", r"观测", r"样本巧合", r"实跑", r"实测",
               r"train=test", r"95%", r"N\s*74", r"SHA"]
M_BASIS_LOGIC = [r"纯逻辑", r"定义式", r"合取消去", r"重言式", r"恒真兜底", r"零信息量",
                 r"逻辑连接词", r"合取项"]
M_NEG = [r"不是定理", r"不是恒等式", r"不是精确", r"未验", r"须撤回", r"须降级",
         r"判错置", r"应改为", r"→\s*改", r"须修正", r"不成立", r"不是同一命题",
         r"不是同一命题", r"禁止", r"不得"]
M_QUEST = [r"是否", r"？\s*$", r"\?\s*$", r"究竟"]
M_HENGID = [r"恒等"]
RE_NEG_ASSERT = re.compile(r"不是[「『].{2,40}[」』]\s*，?\s*而是")
RE_ECHO = re.compile(r"^\s*(?:[-*]\s*)?输出[:：]|^\s*`?输出[:：]")

HARD = re.compile(r"^\s*$|^#{1,6}\s|^-{3,}\s*$|^\s*```")


def H(text: str, pats: list[str]) -> list[str]:
    out = []
    for p in pats:
        m = re.search(p, text)
        if m and m.group(0) not in out:
            out.append(m.group(0))
    return out


def read_lines(path: pathlib.Path):
    b = path.read_bytes()
    return b.decode("utf-8", errors="replace").split("\n"), len(b), hashlib.sha256(b).hexdigest()


def segments(lines: list[str]) -> list[tuple[int, int]]:
    segs, start = [], None
    for i, l in enumerate(lines, 1):
        if HARD.match(l):
            if start is not None:
                segs.append((start, i - 1))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        segs.append((start, len(lines)))
    return [s for s in segs if s[0] <= s[1]]


def anchor_of(lines: list[str], n: int) -> list[str]:
    """该行命中的锚点族名（供证据附注）。"""
    a = lines[n - 1]
    fam = []
    for name, pats in (("SET_EQ", M_SET_EQ), ("IFF", M_IFF), ("SUBSET", M_SUBSET),
                       ("APPROX", M_APPROX), ("INTENS", M_INTENS), ("UNIV", M_UNIV),
                       ("OBS", M_OBS), ("INEQ", M_INEQ), ("TAUT", M_TAUT),
                       ("SUBST", M_SUBST), ("HENGID", M_HENGID)):
        if H(a, pats):
            fam.append(name)
    return fam


def classify(n: int, lines: list[str], seg: tuple[int, int]) -> dict:
    atext = lines[n - 1]
    lo, hi = max(seg[0], n - WIN_R), min(seg[1], n + WIN_R)
    wtext = "\n".join(lines[lo - 1:hi])
    ltext = "\n".join(lines[max(lo, n - LOC_R) - 1:min(hi, n + LOC_R)])

    f = {
        "seteq_line": bool(H(atext, M_SET_EQ)),
        "iff_line": bool(H(atext, M_IFF)),
        "sub_line": bool(H(atext, M_SUBSET)),
        "approx_line": bool(H(atext, M_APPROX)),
        "intens_line": bool(H(atext, M_INTENS)),
        "univ_line": bool(H(atext, M_UNIV)),
        "obs_line": bool(H(atext, M_OBS)),
        "scope_line": bool(H(atext, M_SCOPE)),
        "neg_line": bool(H(atext, M_NEG)),
        "taut_line": bool(H(atext, M_TAUT)),
        "struct_line": bool(H(atext, M_TAUT_STRUCT)),
        "subst_line": bool(H(atext, M_SUBST)),
        "ineq_line": bool(H(atext, M_INEQ)),
        "hengid_line": bool(H(atext, M_HENGID)),
        "quest_line": bool(H(atext, M_QUEST)),
        "echo_line": bool(RE_ECHO.match(atext)),
        "negassert_line": bool(RE_NEG_ASSERT.search(atext)),
        "w_taut": bool(H(wtext, M_TAUT)),
        "w_struct": bool(H(wtext, M_TAUT_STRUCT)),
        "w_subst": bool(H(wtext, M_SUBST)),
        "w_intens": bool(H(wtext, M_INTENS)),
        "w_univ": bool(H(wtext, M_UNIV)),
        "w_obs": bool(H(wtext, M_OBS)),
        "w_scope": bool(H(wtext, M_SCOPE)),
        "w_bcode": bool(H(wtext, M_BASIS_CODE)),
        "w_bobs": bool(H(wtext, M_BASIS_OBS)),
        "w_blogic": bool(H(wtext, M_BASIS_LOGIC)),
        "loc_intens": bool(H(ltext, M_INTENS)),
        "loc_univ": bool(H(ltext, M_UNIV)),
        "loc_scope": bool(H(ltext, M_SCOPE)),
        "loc_obs": bool(H(ltext, M_OBS)),
    }

    rec = {"line": n, "text": atext, "window": [lo, hi], "anchors": anchor_of(lines, n),
           "flags": f, "category": None, "failure_type": None, "missing": None}

    strong = any(f[k] for k in ("seteq_line", "iff_line", "sub_line", "approx_line",
                                "intens_line", "univ_line", "obs_line", "taut_line",
                                "struct_line", "subst_line", "ineq_line"))
    if not strong:
        rec.update(verdict="SKIP", reason="K2_恒等弱标记无任何等式/强度/观测（别论域）")
        return rec

    # 关一：锚点行显式重言标签 + 结构展开 ⇒ 判「重言式」，不报 F（优先级最高）
    if f["taut_line"] and (f["struct_line"] or f["w_struct"]):
        rec.update(verdict="TAUT_OK", category="TAUTOLOGY",
                   reason="锚点行显式重言标签+结构展开（TAUTOLOGY_AUDIT.md:259-260/:270-271）")
        return rec

    i_side = f["intens_line"] or f["univ_line"] or f["loc_intens"] or f["loc_univ"]
    o_side = f["obs_line"] or f["w_obs"]

    # 负控：强度/全称与观测共现，但锚点行自身带范围声明（含否定限定）⇒ 不报 F3
    if i_side and f["scope_line"] and o_side:
        rec.update(verdict="CORRECTLY_SCOPED", category="SUBSTANTIVE",
                   reason="锚点行自身有范围声明/否定限定（如 KEFF_CALC.md:314 逐字「本 74 行上的观测值，不是定理」）")
        return rec

    # 关三：强度/全称 + 观测证据，锚点行无范围声明 ⇒ F3（TAUTOLOGY_AUDIT.md:474 要害）
    if i_side and o_side and not f["scope_line"]:
        rec.update(verdict="FAIL", failure_type="F3", category="SUBSTANTIVE",
                   missing="强度/全称口吻与观测证据直接相接，锚点行无范围声明（须补「本 74 行观测等式」或撤回强度标签）",
                   reason="TAUTOLOGY_AUDIT.md:474 逐字要害同型")
        return rec

    # 提问句（无强度无观测已排除到此处）⇒ 不猜
    if f["quest_line"] and not (f["seteq_line"] and f["w_taut"] and f["w_struct"]):
        rec.update(verdict="SKIP", reason="K3_提问句（究竟/是否）非断言")
        return rec

    # 输出回显行（无强度/全称时）⇒ 证据 echo 不是声明
    if f["echo_line"] or (H(atext, [r"实跑命令"]) and not (f["intens_line"] or f["univ_line"])):
        rec.update(verdict="SKIP", reason="K5_实跑输出回显/命令行")
        return rec

    # 等式/等价声明 ⇒ 两段式义务（TAUTOLOGY_AUDIT.md:315/:536-538）
    if f["seteq_line"] or f["iff_line"]:
        if f["w_taut"] and f["w_struct"] and f["w_subst"]:
            if not (f["w_bcode"] or f["w_bobs"] or f["w_blogic"]):
                rec.update(verdict="FAIL", failure_type="F2", category="SUBSTANTIVE",
                           missing="两半已写但 Q3 依据缺失（:263-266 四类任一均未显式写出）",
                           reason="F2b：T∧S∧¬B")
                return rec
            if f["w_bobs"] and not f["w_scope"]:
                rec.update(verdict="FAIL", failure_type="F2", category="SUBSTANTIVE",
                           missing="依据为「本批 N 行观测」但窗口无 Q4 范围声明",
                           reason="F2c：T∧S∧B_obs∧¬R")
                return rec
            rec.update(verdict="PASS_QUALIFIED", category="SUBSTANTIVE",
                       reason="两半+依据+范围齐（:315 范式合格）")
            return rec
        if f["w_taut"] and f["w_struct"]:
            rec.update(verdict="FAIL", failure_type="F2", category="SUBSTANTIVE",
                       missing="缺实质半（Q2：B⊆A/禁止格/反例）",
                       reason="F2a：T∧¬S")
            return rec
        if f["w_subst"]:
            rec.update(verdict="UNDEC", reason="K6_只写实质半，重言半未见（不猜）")
            return rec
        rec.update(verdict="FAIL", failure_type="F1", category="SUBSTANTIVE",
                   missing="Q1 重言半 + Q2 实质半两半全缺；无 A⊆B/B⊆A 拆分",
                   reason="F1：等式声明∧¬T∧¬S")
        return rec

    # 数学不等式/取等（Fréchet 形态）⇒ 实质条件，无两段式义务（:452 S7）
    if f["ineq_line"]:
        rec.update(verdict="SUBST_OK", category="SUBSTANTIVE",
                   reason="不等式/取等形态（数学上界），非 A=B 型集合恒等声明")
        return rec

    # 正确否定句「不是「X」，而是 Y」⇒ 实质条件（:447 S2 判「本身正确」）
    if f["negassert_line"]:
        rec.update(verdict="SUBST_OK", category="SUBSTANTIVE",
                   reason="正确否定句（不是X而是Y），非等式声明")
        return rec

    if f["approx_line"] or f["obs_line"] or f["sub_line"]:
        rec.update(verdict="UNDEC", reason="K6_近似/观测/实质半标记但无强度无等式（不猜）")
        return rec

    rec.update(verdict="SKIP", reason="K1_无等式无强度无观测")
    return rec


def scan(path: pathlib.Path) -> dict:
    lines, nb, sha = read_lines(path)
    segs = segments(lines)
    recs = []
    for n in range(1, len(lines) + 1):
        fam = anchor_of(lines, n)
        if not fam:
            continue
        seg = next((s for s in segs if s[0] <= n <= s[1]), (n, n))
        r = classify(n, lines, seg)
        r["file:line"] = f"{path.relative_to(ROOT).as_posix()}:{n}"
        r["evidence_lines"] = [{"file:line": f"{path.relative_to(ROOT).as_posix()}:{k}",
                                "text": lines[k - 1]} for k in range(r["window"][0], r["window"][1] + 1)]
        recs.append(r)
    buckets = {"FAIL": [], "TAUT_OK": [], "PASS_QUALIFIED": [], "CORRECTLY_SCOPED": [],
               "SUBST_OK": [], "SKIP": [], "UNDEC": []}
    for r in recs:
        buckets[r["verdict"]].append(r)
    return {"file": path.relative_to(ROOT).as_posix(), "sha256": sha, "bytes": nb,
            "n_lines": len(lines), "n_anchors": len(recs),
            "by_verdict": {k: len(v) for k, v in buckets.items()},
            "recs": recs}


CASE9 = [
    ("关一", "G1a", "lead/layer_identity_20261109/LAYER_IDENTITY.md", 104, "TAUT_OK", None),
    ("关一", "G1b", "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md", 125, "TAUT_OK", None),
    ("关一", "G1c", "lead/score_decomp_20261109/SCORE_DECOMP.md", 235, "TAUT_OK", None),
    ("关二", "G2a", "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 104, "SUBST_OK", None),
    ("关二", "G2b", "lead/layer_identity_20261109/LAYER_IDENTITY.md", 128, "PASS_QUALIFIED", None),
    ("关二", "G2c", "lead/keff_calc_20261109/KEFF_CALC.md", 262, "SUBST_OK", None),
    ("关三", "G3a", "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 108, "FAIL", "F3"),
    ("关三", "G3b", "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 149, "FAIL", "F3"),
    ("关三", "G3c", "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107, "FAIL", "F3"),
]


def case9() -> dict:
    cache = {}
    rows = []
    for gate, cid, relp, ln, exp_v, exp_f in CASE9:
        if relp not in cache:
            cache[relp] = scan(ROOT / relp)
        hit = next((r for r in cache[relp]["recs"] if r["line"] == ln), None)
        act_v = hit["verdict"] if hit else "NO_ANCHOR"
        act_f = hit["failure_type"] if hit else None
        if gate == "关一":
            ok = act_v == "TAUT_OK" and act_f is None
        elif gate == "关二":
            ok = act_f is None and act_v in ("SUBST_OK", "PASS_QUALIFIED", "CORRECTLY_SCOPED")
        else:
            ok = act_v == "FAIL" and act_f == "F3"
        rows.append({"gate": gate, "case": cid, "file:line": f"{relp}:{ln}",
                     "expect": f"{exp_v}/{exp_f or '-'}", "actual": f"{act_v}/{act_f or '-'}",
                     "passed": ok, "reason": (hit or {}).get("reason"),
                     "missing": (hit or {}).get("missing"),
                     "flags": (hit or {}).get("flags"),
                     "text": (hit or {}).get("text")})
    out = {"n_cases": len(rows), "n_passed": sum(1 for r in rows if r["passed"]),
           "rows": rows}
    return out


LISTED45 = {
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": [
        1, 13, 22, 26, 87, 104, 110, 112, 116, 122, 126, 127, 128, 182, 189,
        197, 200, 208, 213, 216, 223, 225, 226, 228, 233, 234, 242, 273, 279,
        304, 326, 337, 338, 339, 365, 372, 376, 393, 400, 409, 414],
    "lead/keff_calc_20261109/KEFF_CALC.md": [340],
    "lead/score_decomp_20261109/SCORE_DECOMP.md": [135, 239],
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [158],
}


def listed45() -> dict:
    cache = {}
    rows = []
    for relp, lns in LISTED45.items():
        if relp not in cache:
            cache[relp] = scan(ROOT / relp)
        idx = {r["line"]: r for r in cache[relp]["recs"]}
        for n in lns:
            h = idx.get(n)
            rows.append({"file:line": f"{relp}:{n}", "anchored": h is not None,
                         "verdict": h["verdict"] if h else "NOT_ANCHOR",
                         "failure_type": h["failure_type"] if h else None,
                         "reason": (h or {}).get("reason")})
    out = {"n_rows": len(rows), "n_anchored": sum(1 for r in rows if r["anchored"]),
           "n_fail": sum(1 for r in rows if r["verdict"] == "FAIL"), "rows": rows}
    return out


READ_DIRS = ["lead/tautology_audit_20261109", "lead/layer_identity_20261109",
             "lead/metric_audit_20261109", "lead/keff_calc_20261109",
             "lead/evidence_indep_20261109", "lead/gate_pipeline_20261109",
             "lead/score_decomp_20261109", "lead/comparability_20261109"]


def full() -> dict:
    files = sorted({p for d in READ_DIRS for p in (ROOT / d).glob("*.md")})
    res = [scan(p) for p in files]
    tot = {}
    for r in res:
        for k, v in r["by_verdict"].items():
            tot[k] = tot.get(k, 0) + v
    return {"n_files": len(res), "n_anchors": sum(r["n_anchors"] for r in res),
            "by_verdict": tot,
            "by_file": {r["file"]: {"n_anchors": r["n_anchors"], **r["by_verdict"]} for r in res}}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "case9"
    if mode == "case9":
        print(json.dumps(case9(), ensure_ascii=False, indent=1))
    elif mode == "listed45":
        print(json.dumps(listed45(), ensure_ascii=False, indent=1))
    elif mode == "full":
        print(json.dumps(full(), ensure_ascii=False, indent=1))
    elif mode == "scan":
        rec = scan(pathlib.Path(sys.argv[2]))
        slim = {k: v for k, v in rec.items() if k != "recs"}
        slim["recs_brief"] = [{"line": r["line"], "verdict": r["verdict"],
                               "failure_type": r["failure_type"],
                               "reason": r.get("reason")} for r in rec["recs"]]
        print(json.dumps(slim, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
