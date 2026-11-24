# -*- coding: utf-8 -*-
"""
_ef_fence_state.py — 第一步 (a)(b)：独立确认围栏缺陷
(a) 自写围栏状态机，逐行标注「这行在不在 ``` 内」；对 COMPARABILITY_AUDIT.md:158
    与 LAYER_IDENTITY.md:13/223/242/338 逐行给结论；未闭合围栏兜底。
    三种口径同算：v1=内容行（不含标记行）/ v2=含标记行 / v3=检测器 HARD_BOUNDARY
    同款 ^\s*``` 切换语义。未闭合尾部按 inside 计入（兜底）。
(b) 复现原版 build_segments 在 COMPARABILITY_AUDIT.md 145..175 的切分，
    与编排方实测 (158,164) 比对；同时给 LAYER_IDENTITY.md 4 行所在段。
只读：被检文档与原检测器一律不改；输出落本任务写域。
运行： python -I -X utf8 <本文件>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
ORIG = ROOT / "lead/eqdecl_gate_20261109/_eq_detector.py"
OUT = ROOT / "lead/eqdecl_fix_20261110/_ef_fence_state_out.json"

# 与原 _eq_full_run.py READ_DIRS 完全一致的 15 件
FILES = [
    "lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md",
    "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md",
    "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md",
    "lead/keff_calc_20261109/KEFF_CALC.md",
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md",
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/score_decomp_20261109/SCORE_DECOMP.md",
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md",
]

PROBE = {
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [157, 158, 159, 164, 165],
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": [13, 223, 242, 338],
}


def read_lines(path: pathlib.Path):
    b = path.read_bytes()
    return b.decode("utf-8", errors="replace").split("\n"), len(b), hashlib.sha256(b).hexdigest()


def fence_scan(lines: list[str]) -> dict:
    """独立围栏状态机（不借用检测器常量）。
    开行：^\s*(`{3,}|~{3,})info?   闭行：^\s* 同字符{>=open_len} \s*$
    未闭合兜底：扫描结束时仍 IN ⇒ 剩余行全部记 inside（标记 unclosed=True）。"""
    n = len(lines)
    content = [False] * n   # v1: 标记行之间的内容行
    incl = [False] * n      # v2: 连同开/闭标记行一起算 inside
    state = False
    ch, olen = None, 0
    cur_start = None
    ranges = []
    unclosed = False
    for i, l in enumerate(lines):
        m = re.match(r"^\s*(`{3,}|~{3,})", l)
        if not state:
            if m:
                state = True
                ch = m.group(1)[0]
                olen = len(m.group(1))
                cur_start = i
        else:
            # 已在围栏内：只有「同字符、长度≥开行、其后仅空白」的行才算闭行
            m2 = re.match(r"^\s*(`{3,}|~{3,})\s*$", l)
            if m2 and m2.group(1)[0] == ch and len(m2.group(1)) >= olen:
                ranges.append({"open_0": cur_start, "close_0": i,
                               "open_1": cur_start + 1, "close_1": i + 1,
                               "closed": True})
                state = False
                ch, olen, cur_start = None, 0, None
    if state:
        ranges.append({"open_0": cur_start, "close_0": None,
                       "open_1": cur_start + 1, "close_1": None,
                       "closed": False})
        unclosed = True
        for i in range(cur_start + 1, n):
            content[i] = True
            incl[i] = True
    for r in ranges:
        for i in range(r["open_0"] + 1, (r["close_0"] if r["closed"] else n)):
            content[i] = True
            incl[i] = True
        incl[r["open_0"]] = True
        if r["closed"]:
            incl[r["close_0"]] = True
    # v3：与检测器 HARD_BOUNDARY 同款切换语义（^``` 即翻状态，闭行从宽）
    tog = [False] * n
    t = False
    for i, l in enumerate(lines):
        if re.match(r"^\s*```", l):
            t = not t
            tog[i] = t   # 开标记行本身记为 inside 后的状态翻转结果
    return {"v1_content": content, "v2_incl_marks": incl, "v3_toggle": tog,
            "ranges": ranges, "unclosed": unclosed}


def main() -> int:
    spec = importlib.util.spec_from_file_location("_eq_detector_orig", ORIG)
    eq = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(eq)

    out: dict = {"per_file": {}, "probe_lines": {}, "build_segments": {}}
    for relp in FILES:
        p = ROOT / relp
        lines, nb, sha = read_lines(p)
        fs = fence_scan(lines)
        v1 = sum(fs["v1_content"])
        v2 = sum(fs["v2_incl_marks"])
        v3 = sum(1 for x in fs["v3_toggle"] if x)
        out["per_file"][relp] = {
            "sha256": sha, "bytes": nb, "n_lines": len(lines),
            "n_fences": len(fs["ranges"]), "unclosed": fs["unclosed"],
            "n_inside_v1_content_only": v1,
            "n_inside_v2_incl_marks": v2,
            "n_inside_v3_toggle": v3,
            "fence_ranges_1based": [
                [r["open_1"], r["close_1"], r["closed"]] for r in fs["ranges"]],
        }

    # ---- 逐行探针 ----
    for relp, lns in PROBE.items():
        p = ROOT / relp
        lines, _, _ = read_lines(p)
        fs = fence_scan(lines)
        rows = []
        for n in lns:
            rows.append({
                "line": n,
                "in_fence_v1": fs["v1_content"][n - 1],
                "in_fence_v2": fs["v2_incl_marks"][n - 1],
                "text": lines[n - 1][:200],
            })
        out["probe_lines"][relp] = rows

    # ---- CA 150..175 逐行明细（围栏状态 + 是否硬边界）----
    ca = ROOT / "lead/comparability_20261109/COMPARABILITY_AUDIT.md"
    lines, _, _ = read_lines(ca)
    fs = fence_scan(lines)
    detail = []
    for n in range(150, min(176, len(lines) + 1)):
        detail.append({
            "line": n,
            "hard_boundary(bool(eq.HARD_BOUNDARY.match))":
                bool(eq.HARD_BOUNDARY.match(lines[n - 1])),
            "in_fence_v1": fs["v1_content"][n - 1],
            "in_fence_v2": fs["v2_incl_marks"][n - 1],
            "text": lines[n - 1][:120],
        })
    out["comparability_150_175_detail"] = detail

    # ---- (b) 复现原版 build_segments ----
    for relp, lns in PROBE.items():
        p = ROOT / relp
        lines, _, _ = read_lines(p)
        segs = eq.build_segments(lines)
        hits = {}
        for n in lns:
            seg = next((s for s in segs if s[0] <= n <= s[1]), None)
            hits[n] = list(seg) if seg else None
        near = [list(s) for s in segs if not (s[1] < 145 or s[0] > 175)] if "comparability" in relp else \
               [list(s) for s in segs if not (s[1] < 1 or s[0] > 430) and
                any(abs(s[0] - x) <= 12 or abs(s[1] - x) <= 12 for x in lns)]
        out["build_segments"][relp] = {
            "segments_near": near,
            "line_to_segment": {str(k): v for k, v in hits.items()},
            "n_segments_total": len(segs),
        }
        # CA 专项：编排方实测 seg=(158,164)，逐字比对
        if "comparability" in relp:
            seg158 = next((s for s in segs if s[0] <= 158 <= s[1]), None)
            out["build_segments"][relp]["seg_containing_158"] = list(seg158) if seg158 else None
            out["build_segments"][relp]["matches_orchestrator_158_164"] = (seg158 == (158, 164))

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 终端摘要 ----
    print("== 围栏状态机（独立实现）==")
    for relp, d in out["per_file"].items():
        print(f"  {relp}: n_lines={d['n_lines']} fences={d['n_fences']} "
              f"unclosed={d['unclosed']} inside_v1={d['n_inside_v1_content_only']} "
              f"inside_v2={d['n_inside_v2_incl_marks']} inside_v3={d['n_inside_v3_toggle']}")
    print("== 逐行探针 ==")
    for relp, rows in out["probe_lines"].items():
        for r in rows:
            print(f"  {relp}:{r['line']} v1={r['in_fence_v1']} v2={r['in_fence_v2']} | {r['text'][:80]}")
    print("== CA 150..175 ==")
    for r in detail:
        print(f"  {r['line']:3d} hb={r['hard_boundary(bool(eq.HARD_BOUNDARY.match))']!s:5} "
              f"v1={r['in_fence_v1']!s:5} | {r['text'][:70]}")
    print("== build_segments 复现 ==")
    for relp, d in out["build_segments"].items():
        print(f"  {relp}: line_to_segment={d['line_to_segment']} "
              f"n_segments={d['n_segments_total']}")
        if "seg_containing_158" in d:
            print(f"    seg(158)={d['seg_containing_158']} "
                  f"==(158,164)? {d['matches_orchestrator_158_164']}")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
