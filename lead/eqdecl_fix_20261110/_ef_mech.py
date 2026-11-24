# -*- coding: utf-8 -*-
"""
_ef_mech.py — 第一步 (c)：LI:13/223/242/338 + CA:158 五行假阳/可疑机制逐行查清。
用【原版】检测器（只读 import，不修改）跑 scan_file，对每行给：
  · 锚点全行原文 + 窗口逐行原文（E/I/O/R 逐行命中标注）
  · flags 全量 + verdict/failure_type/missing
  · K1–K6 每个 skip 通道在「锚点行自身」上的逐条求值结果（为何没接住）
  · F1/F2/F3 三个判据的逐条求值结果
只读；输出落写域 _ef_mech_out.json。
运行： python -I -X utf8 <本文件>
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
ORIG = ROOT / "lead/eqdecl_gate_20261109/_eq_detector.py"
OUT = ROOT / "lead/eqdecl_fix_20261110/_ef_mech_out.json"

spec = importlib.util.spec_from_file_location("_eq_detector_orig", ORIG)
eq = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(eq)

PROBES = [
    ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", 158),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 13),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 223),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 242),
    ("lead/layer_identity_20261109/LAYER_IDENTITY.md", 338),
]


def main() -> int:
    out = []
    cache: dict[str, dict] = {}
    for relp, n in PROBES:
        if relp not in cache:
            cache[relp] = eq.scan_file(ROOT / relp)
        rec = cache[relp]
        allhits = (rec["findings"] + rec["passes"] + rec["tautology_ok"] +
                   rec["skips"] + rec["undecidables"])
        h = next((x for x in allhits if x["line"] == n), None)
        if h is None:
            out.append({"file:line": f"{relp}:{n}", "error": "NOT_AN_ANCHOR"})
            continue
        lines = eq.read_lines(ROOT / relp)[0]
        atext = lines[n - 1]
        lo, hi = h["window"]
        wl = [(k, lines[k - 1]) for k in range(lo, hi + 1)]

        wtext = "\n".join(t for _, t in wl)
        # K 通道逐条求值（复刻 classify_window :300-317 的顺序与判据）
        E = eq._has(wtext, eq.E_MARKERS)
        O = eq._has(wtext, eq.OBS_EVIDENCE)
        I_raw = eq._has(h["flags"] and "\n".join(
            lines[k - 1] for k in range(max(lo, n - eq.LOCAL_RADIUS),
                                        min(hi, n + eq.LOCAL_RADIUS) + 1)), eq.INTENSITY)
        k_eval = {
            "K3_question(_has(atext,QUESTION))": {
                "value": eq._has(atext, eq.QUESTION),
                "hits": eq._hits(atext, eq.QUESTION)},
            "K2(恒等 on atext and not E and not O and not I)": {
                "value": eq._has(atext, [r"恒等"]) and not E and not O and not h["flags"]["I"],
                "atext_恒等": eq._hits(atext, [r"恒等"])},
            "K3_intensity(I_raw and not E and not O)": {
                "value": I_raw and not E and not O},
            "K5_quote(_has(atext,QUOTE_OR_REVIEW) and not E and not O)": {
                "value": eq._has(atext, eq.QUOTE_OR_REVIEW) and not E and not O,
                "hits": eq._hits(atext, eq.QUOTE_OR_REVIEW)},
            "K1(not I and not E)": {"value": (not h["flags"]["I"]) and (not E)},
            "denial(CORRECTION on atext)": {
                "value": eq._has(atext, eq.CORRECTION),
                "hits": eq._hits(atext, eq.CORRECTION)},
            "R_same_line(SCOPE on atext)": {
                "value": eq._has(atext, eq.SCOPE),
                "hits": eq._hits(atext, eq.SCOPE)},
        }
        T, S = h["flags"]["T"], h["flags"]["S"]
        E_eq = h["flags"]["E_eq"]
        B = h["flags"]["B"]
        B_obs = h["flags"]["B_obs"]
        R = h["flags"]["R"]
        declares = T and S
        logic_self = T and h["flags"]["B_logic"] and not B_obs
        f_eval = {
            "E_eq": E_eq, "T": T, "S": S,
            "f3 = I and O and not R_same_line": h["flags"]["I"] and h["flags"]["O"] and not h["flags"]["R_same_line"],
            "f2 = T and S and not logic_self and ((not B) or (B_obs and not R))":
                declares and not logic_self and ((not B) or (B_obs and not R)),
            "f1 = E_eq and (not T) and (not S)": E_eq and (not T) and (not S),
            "R(window)": R, "R_local": h["flags"]["R_local"],
            "R_same_line": h["flags"]["R_same_line"],
        }
        per_line_marks = []
        for k, t in wl:
            per_line_marks.append({
                "line": k,
                "E": eq._hits(t, eq.E_MARKERS),
                "I": eq._hits(t, eq.INTENSITY + eq.UNIVERSAL_CLAIM),
                "O": eq._hits(t, eq.OBS_EVIDENCE),
                "R": eq._hits(t, eq.SCOPE),
                "text": t,
            })
        out.append({
            "file:line": f"{relp}:{n}",
            "verdict": h["verdict"], "failure_type": h["failure_type"],
            "category": h["category"], "missing": h.get("missing"),
            "morphs": h["morphs"], "matched_strings": h["matched_strings"],
            "flags": h["flags"], "window": [lo, hi],
            "anchor_full_text": atext,
            "k_eval": k_eval, "f_eval": f_eval,
            "window_lines_marked": per_line_marks,
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in out:
        print("=" * 100)
        print(r["file:line"], "->", r.get("verdict"), "/", r.get("failure_type"),
              "/", r.get("category"))
        print("  锚点全行:", r.get("anchor_full_text"))
        print("  morphs:", r.get("morphs"), " matched:", r.get("matched_strings"))
        print("  flags:", json.dumps(r.get("flags"), ensure_ascii=False))
        print("  K 通道:")
        for k, v in (r.get("k_eval") or {}).items():
            print(f"    {k} = {v}")
        print("  F 判据:")
        for k, v in (r.get("f_eval") or {}).items():
            print(f"    {k} = {v}")
        print("  窗口逐行（E/I/O/R 命中）:")
        for m in (r.get("window_lines_marked") or []):
            mark = f"E={m['E']} I={m['I']} O={m['O']} R={m['R']}"
            print(f"    {m['line']:3d} {mark}")
            print(f"        | {m['text'][:160]}")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
