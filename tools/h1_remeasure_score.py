#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h1_remeasure_score.py — H1 指纹复测离线验收/记分（H1RM / ZC-H1RM）

输入 evidence JSON 或 CSV（schema = h1_remeasure_evidence_v1，
权威定义见 docs/re/h1_remeasure_protocol.md §3），输出 PASS/FAIL 判分表 + markdown。

用法：
  python tools/h1_remeasure_score.py evidence.json
  python tools/h1_remeasure_score.py evidence.csv --md out/re_work/h1_remeasure/SCORE.md
  python tools/h1_remeasure_score.py --selftest
  python tools/h1_remeasure_score.py --schema

退出码：0 = 总判 PASS，1 = 总判 FAIL，2 = 输入/schema 错误。

判分口径（与协议 §2/§4 一致）：
  J1 指纹作废率（计入表的 H1 局必须 100% 过 S1）
  J2 A2 delta = units_seen(H1)-units_seen(空图) ∈ [0.8T, 1.2T]
  J3 旧误选签名 178/713/2852 不得混入有效标度表（713 不得当 U0200 读数）
  J4 国家矩阵 8 格覆盖
  J5 性能 coverage
  J6 except 门禁
  J7 还原
  ROI 解冻 = R1∧R2∧R3∧R4
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MD = ROOT / "out" / "re_work" / "h1_remeasure" / "SCORE.md"
SELFTEST_DIR = ROOT / "out" / "re_work" / "h1_remeasure" / "selftest"
SCHEMA_ID = "h1_remeasure_evidence_v1"

# --- 常量（docs/re/h1_remeasure_protocol.md §1）---
EXPECTED_FP = {
    "U0050": "H1FP1|U0050|26c371932de7",
    "U0200": "H1FP1|U0200|4bf2d6692bd5",
    "U0800": "H1FP1|U0800|1189b6b550ff",
}
TARGET = {"U0050": 50, "U0200": 200, "U0800": 800}
TIERS = ("U0050", "U0200", "U0800")

# 误选签名带（中心, 半宽）；713 为硬红线，不得当 U0200/任意档标度点
MISSELECT_BANDS = ((178, 20), (713, 20), (2852, 40))

# 国家矩阵：{美蘇,美随机,蘇随机,随机随机} × {UC=0,10}
MATRIX_CELLS = tuple(
    (p, e, uc)
    for p, e in (
        ("Americans", "Russians"),
        ("Americans", "Random"),
        ("Russians", "Random"),
        ("Random", "Random"),
    )
    for uc in (0, 10)
)
MIN_ROUNDS_DEFAULT = 3
FP_VOID_RATE_WARN = 0.20

BOOL_TRUE = {"1", "true", "yes", "y", "t"}
BOOL_FALSE = {"0", "false", "no", "n", "f", ""}

RUN_FIELDS = (
    "run_id", "seg", "map_kind", "tier", "player", "enemy",
    "unit_count", "credits", "fingerprint_read", "fingerprint_expect",
    "name_read", "units_seen", "sample_frame",
    "fps_avg", "cpu0_avg", "tick_miss",
    "except_fresh", "except_eip", "except_sha256",
    "restored", "invalid", "invalid_reason", "notes",
)
INT_FIELDS = ("unit_count", "credits", "units_seen", "sample_frame")
FLOAT_FIELDS = ("fps_avg", "cpu0_avg", "tick_miss")
BOOL_FIELDS = ("except_fresh", "restored", "invalid")


# ---------------------------------------------------------------------------
# 载入 / 规范化
# ---------------------------------------------------------------------------
def _coerce(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in RUN_FIELDS:
        v = row.get(k, None)
        if v is None:
            out[k] = None
            continue
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                out[k] = None
                continue
        if k in INT_FIELDS:
            try:
                out[k] = int(float(v))
            except (TypeError, ValueError):
                out[k] = None
        elif k in FLOAT_FIELDS:
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = None
        elif k in BOOL_FIELDS:
            if isinstance(v, bool):
                out[k] = v
            else:
                s = str(v).strip().lower()
                if s in BOOL_TRUE:
                    out[k] = True
                elif s in BOOL_FALSE:
                    out[k] = False
                else:
                    out[k] = None
        else:
            out[k] = str(v)
    # 缺省
    if out.get("map_kind") is None:
        out["map_kind"] = "h1"
    out["map_kind"] = str(out["map_kind"]).lower()
    if out.get("tier") is None:
        out["tier"] = "NA"
    if out.get("credits") is None:
        out["credits"] = 0
    if out.get("sample_frame") is None:
        out["sample_frame"] = 15
    if out.get("fingerprint_expect") is None and out.get("tier") in EXPECTED_FP:
        out["fingerprint_expect"] = EXPECTED_FP[out["tier"]]
    return out


def load_evidence(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        runs = [_coerce(r) for r in rows]
        return {"schema": SCHEMA_ID, "batch_id": path.stem, "runs": runs, "source": str(path)}
    data = json.loads(text)
    if isinstance(data, list):
        data = {"schema": SCHEMA_ID, "runs": data}
    if not isinstance(data, dict) or "runs" not in data:
        raise ValueError("evidence JSON 需含 runs[] 或为行数组")
    data["runs"] = [_coerce(r) for r in data["runs"]]
    data.setdefault("schema", SCHEMA_ID)
    data["source"] = str(path)
    return data


# ---------------------------------------------------------------------------
# 判分核心
# ---------------------------------------------------------------------------
def in_misselect_band(units_seen: int | None) -> bool:
    if units_seen is None:
        return False
    return any(abs(units_seen - c) <= w for c, w in MISSELECT_BANDS)


def cell_key(run: dict) -> tuple:
    return (run.get("player"), run.get("enemy"), run.get("unit_count"))


def annotate(runs: list[dict]) -> list[dict]:
    """S1 指纹 + 误选签名标注。"""
    for r in runs:
        r["fp_ok"] = None
        r["misselect"] = in_misselect_band(r.get("units_seen"))
        r["countable"] = False
        r["void_reason"] = None

        if r.get("invalid"):
            r["void_reason"] = r.get("invalid_reason") or "pre_invalid"
            continue

        if r.get("map_kind") == "empty":
            r["fp_ok"] = True  # 空图不要求 H1FP1
        else:
            read = r.get("fingerprint_read") or ""
            expect = r.get("fingerprint_expect") or ""
            if not read:
                r["fp_ok"] = False
                r["void_reason"] = "fp_missing"
            elif read.strip() != expect.strip():
                r["fp_ok"] = False
                r["void_reason"] = "fp_mismatch"
            else:
                r["fp_ok"] = True

        if r["void_reason"]:
            continue

        # 误选签名：强制剔出有效标度表（J3 红线）
        if r["misselect"]:
            r["void_reason"] = "misselect_sig"
            continue

        if r.get("map_kind") == "h1" and r.get("units_seen") is None:
            r["void_reason"] = "no_units_seen"
            continue

        r["countable"] = True
    return runs


def score(data: dict, min_rounds: int = MIN_ROUNDS_DEFAULT) -> dict:
    runs = annotate(list(data.get("runs") or []))
    report: dict[str, Any] = {
        "schema": SCHEMA_ID,
        "batch_id": data.get("batch_id"),
        "source": data.get("source"),
        "n_runs": len(runs),
        "min_rounds": min_rounds,
        "runs": runs,
    }

    h1_runs = [r for r in runs if r.get("map_kind") == "h1"]
    empty_runs = [r for r in runs if r.get("map_kind") == "empty"]
    h1_attempts = len(h1_runs)
    h1_void = sum(1 for r in h1_runs if not r["countable"])
    h1_countable = [r for r in h1_runs if r["countable"]]
    void_rate = (h1_void / h1_attempts) if h1_attempts else 1.0

    # ---- J1 指纹 ----
    fp_mismatch = sum(1 for r in h1_runs if r.get("void_reason") == "fp_mismatch")
    fp_missing = sum(1 for r in h1_runs if r.get("void_reason") == "fp_missing")
    misselect_n = sum(1 for r in runs if r.get("misselect"))
    misselect_leaked = sum(
        1 for r in h1_countable if r.get("misselect")
    )  # 应恒为 0；annotate 已剔
    j1 = {
        "attempts": h1_attempts,
        "void": h1_void,
        "void_rate": round(void_rate, 4),
        "fp_mismatch": fp_mismatch,
        "fp_missing": fp_missing,
        "countable": len(h1_countable),
        "pass_100pct_counted": all(r.get("fp_ok") for r in h1_countable),
        "healthy": void_rate <= FP_VOID_RATE_WARN,
    }
    # 计入表必须 100% 过 S1；作废率>20% 只是测量健康警告（不单独 FAIL，除非无有效样本）
    j1["verdict"] = "PASS" if j1["pass_100pct_counted"] and h1_attempts > 0 else "FAIL"
    if j1["healthy"] is False and j1["verdict"] == "PASS":
        j1["verdict"] = "PASS_WARN"

    # ---- J3 误选签名 ----
    j3 = {
        "misselect_n": misselect_n,
        "leaked_into_counted": misselect_leaked,
        "bands": [f"{c}±{w}" for c, w in MISSELECT_BANDS],
        "hard_rule": "713 不得再当 U0200 读数",
        "verdict": "PASS" if misselect_leaked == 0 else "FAIL",
    }
    # 额外：若有 run 被标 countable 且 units≈713 却 tier=U0200 —— annotate 已挡；
    # 再显式扫描一遍原始行，防 schema 外字段绕过。
    for r in runs:
        if r.get("map_kind") == "h1" and in_misselect_band(r.get("units_seen")):
            if r.get("tier") == "U0200" and abs((r.get("units_seen") or 0) - 713) <= 20:
                r["hard_flag"] = "U0200_READ_AS_713"
                if r.get("countable"):
                    j3["verdict"] = "FAIL"

    # ---- J2 A2 delta（按 档 × 矩阵格）----
    empty_by_cell: dict[tuple, list[int]] = defaultdict(list)
    for r in empty_runs:
        if r["countable"] and r.get("units_seen") is not None:
            empty_by_cell[cell_key(r)].append(r["units_seen"])

    tier_table: dict[str, dict] = {}
    for tier in TIERS:
        t = TARGET[tier]
        rows = []
        deltas = []
        for cell in MATRIX_CELLS:
            h1_vals = [
                r["units_seen"]
                for r in h1_countable
                if r.get("tier") == tier and cell_key(r) == cell and r.get("units_seen") is not None
            ]
            em = empty_by_cell.get(cell, [])
            n_h1 = len(h1_vals)
            n_e = len(em)
            if n_h1 == 0 and n_e == 0:
                status = "MISSING"
                d = None
            elif n_e == 0:
                status = "NO_EMPTY_CTRL"
                d = None
            elif n_h1 == 0:
                status = "NO_H1"
                d = None
            else:
                d = mean(h1_vals) - mean(em)
                deltas.append(d)
                lo, hi = 0.8 * t, 1.2 * t
                status = "IN_BAND" if lo <= d <= hi else "OUT_BAND"
            rows.append({
                "cell": f"{cell[0]}/{cell[1]}/UC{cell[2]}",
                "player": cell[0], "enemy": cell[1], "unit_count": cell[2],
                "n_h1": n_h1, "n_empty": n_e,
                "h1_mean": round(mean(h1_vals), 2) if h1_vals else None,
                "empty_mean": round(mean(em), 2) if em else None,
                "delta": round(d, 2) if d is not None else None,
                "band": f"[{0.8 * t:g}, {1.2 * t:g}]",
                "status": status,
            })
        delta_mean = mean(deltas) if deltas else None
        lo, hi = 0.8 * t, 1.2 * t
        if delta_mean is None:
            verdict = "NO_DATA"
        elif lo <= delta_mean <= hi and all(r["status"] == "IN_BAND" for r in rows if r["delta"] is not None):
            verdict = "IN_BAND"
        elif lo <= delta_mean <= hi:
            verdict = "MEAN_IN_BAND_SOME_OUT"
        else:
            verdict = "OUT_BAND"
        tier_table[tier] = {
            "target": t,
            "band": [lo, hi],
            "cells": rows,
            "n_deltas": len(deltas),
            "delta_mean": round(delta_mean, 2) if delta_mean is not None else None,
            "verdict": verdict,
        }

    j2_ok = all(tier_table[t]["verdict"] == "IN_BAND" for t in TIERS)
    j2 = {"tiers": tier_table, "verdict": "PASS" if j2_ok else "FAIL"}

    # ---- J4 矩阵覆盖 ----
    cell_counts: dict[str, int] = {}
    matrix_rows = []
    covered = 0
    for cell in MATRIX_CELLS:
        n = sum(
            1
            for r in h1_countable
            if cell_key(r) == cell and r.get("map_kind") == "h1"
        )
        # 计每档；矩阵格按「任一档有样本」计覆盖，另记 per-tier
        label = f"{cell[0]}/{cell[1]}/UC{cell[2]}"
        cell_counts[label] = n
        per_tier = {
            t: sum(1 for r in h1_countable if r.get("tier") == t and cell_key(r) == cell)
            for t in TIERS
        }
        ok = n >= min_rounds
        if ok:
            covered += 1
        matrix_rows.append({
            "cell": label, "n_total": n, "per_tier": per_tier,
            "min_rounds": min_rounds, "ok": ok,
        })
    j4 = {
        "cells": matrix_rows,
        "covered": covered,
        "required": len(MATRIX_CELLS),
        "verdict": "PASS" if covered == len(MATRIX_CELLS) else ("PARTIAL" if covered else "FAIL"),
    }

    # ---- J5 性能 coverage ----
    perf_n = sum(
        1
        for r in h1_countable
        if any(r.get(k) is not None for k in ("fps_avg", "cpu0_avg", "tick_miss"))
    )
    denom = len(h1_countable)
    coverage = (perf_n / denom) if denom else 0.0
    perf_rows = [
        {
            "run_id": r.get("run_id"),
            "tier": r.get("tier"),
            "fps_avg": r.get("fps_avg"),
            "cpu0_avg": r.get("cpu0_avg"),
            "tick_miss": r.get("tick_miss"),
        }
        for r in h1_countable
        if any(r.get(k) is not None for k in ("fps_avg", "cpu0_avg", "tick_miss"))
    ]
    j5 = {
        "perf_n": perf_n,
        "countable_h1": denom,
        "coverage": round(coverage, 4),
        "rows": perf_rows,
        "verdict": "PASS" if coverage > 0 else "FAIL",
    }

    # ---- J6 except ----
    except_fresh = [
        r for r in runs if r.get("except_fresh") and not r.get("invalid")
    ]
    eip_list = [r.get("except_eip") for r in except_fresh if r.get("except_eip")]
    red_eip = [e for e in eip_list if e and (
        e.lower().startswith("0x54d3") or e.lower().startswith("0x01b00000")
        or e.lower().startswith("54d3") or e.lower().startswith("01b00000")
    )]
    j6 = {
        "except_fresh_n": len(except_fresh),
        "eips": eip_list,
        "red_line_eip": red_eip,
        "verdict": "FAIL" if red_eip else ("PASS_WARN" if except_fresh else "PASS"),
    }

    # ---- J7 还原 ----
    unrestored = [r for r in runs if r.get("restored") is False and not r.get("invalid")]
    j7 = {
        "unrestored_n": len(unrestored),
        "unrestored_ids": [r.get("run_id") for r in unrestored],
        "verdict": "PASS" if not unrestored else "FAIL",
    }

    # ---- ROI ----
    r1 = j2_ok
    r2 = bool(j1["pass_100pct_counted"]) and denom > 0
    r3 = j3["verdict"] == "PASS"
    r4 = (j7["verdict"] == "PASS") and (j6["verdict"] != "FAIL")
    roi_ok = r1 and r2 and r3 and r4
    roi = {
        "R1_delta_all_in_band": r1,
        "R2_fp_100pct_counted": r2,
        "R3_no_misselect_leak": r3,
        "R4_restore_and_except": r4,
        "verdict": "UNFREEZE_CANDIDATE" if roi_ok else "KEEP_FROZEN",
    }

    # ---- 总判 ----
    hard = [j2, j3, j6, j7]
    # J1：无有效样本也 FAIL；作废率高仅 WARN
    j1_fail = (j1["verdict"] == "FAIL") or (denom == 0)
    j4_fail = j4["verdict"] == "FAIL"
    j5_fail = j5["verdict"] == "FAIL"
    any_hard_fail = any(x["verdict"] == "FAIL" for x in hard) or j1_fail or j4_fail or j5_fail
    overall = "FAIL" if any_hard_fail else "PASS"

    report.update({
        "J1_fingerprint": j1,
        "J2_delta": j2,
        "J3_misselect": j3,
        "J4_matrix": j4,
        "J5_perf": j5,
        "J6_except": j6,
        "J7_restore": j7,
        "ROI": roi,
        "overall": overall,
    })
    return report


# ---------------------------------------------------------------------------
# markdown 输出
# ---------------------------------------------------------------------------
def to_markdown(report: dict) -> str:
    L: list[str] = []
    a = L.append
    a(f"# H1 指纹复测判分报告（{report.get('batch_id') or 'batch'}）")
    a("")
    a(f"- source: `{report.get('source')}`")
    a(f"- runs: {report.get('n_runs')} · min_rounds={report.get('min_rounds')}")
    a(f"- **总判：{report.get('overall')}** · **ROI：{report['ROI']['verdict']}**")
    a("")

    a("## 总表")
    a("")
    a("| 判据 | verdict | 要点 |")
    a("|---|---|---|")
    j1 = report["J1_fingerprint"]
    a(f"| J1 指纹 | {j1['verdict']} | 尝试 {j1['attempts']} · 作废 {j1['void']} "
      f"(率 {j1['void_rate']:.1%}) · 计入 {j1['countable']} · 计入局 100% 过 S1={j1['pass_100pct_counted']} |")
    j2 = report["J2_delta"]
    a(f"| J2 delta | {j2['verdict']} | " +
      " · ".join(f"{t}:{j2['tiers'][t]['verdict']} Δ={j2['tiers'][t]['delta_mean']}" for t in TIERS) + " |")
    j3 = report["J3_misselect"]
    a(f"| J3 误选签名 | {j3['verdict']} | 命中 {j3['misselect_n']} · 泄入有效表 {j3['leaked_into_counted']} |")
    j4 = report["J4_matrix"]
    a(f"| J4 矩阵 | {j4['verdict']} | 覆盖 {j4['covered']}/{j4['required']} |")
    j5 = report["J5_perf"]
    a(f"| J5 性能 | {j5['verdict']} | coverage={j5['coverage']:.1%} ({j5['perf_n']}/{j5['countable_h1']}) |")
    j6 = report["J6_except"]
    a(f"| J6 except | {j6['verdict']} | 新生 {j6['except_fresh_n']} · 红线 EIP {j6['red_line_eip'] or '无'} |")
    j7 = report["J7_restore"]
    a(f"| J7 还原 | {j7['verdict']} | 未还原 {j7['unrestored_n']} |")
    roi = report["ROI"]
    a(f"| ROI | {roi['verdict']} | R1={roi['R1_delta_all_in_band']} R2={roi['R2_fp_100pct_counted']} "
      f"R3={roi['R3_no_misselect_leak']} R4={roi['R4_restore_and_except']} |")
    a("")

    a("## J2 A2 delta 表")
    a("")
    for t in TIERS:
        tt = report["J2_delta"]["tiers"][t]
        a(f"### {t} · target={tt['target']} · band={tt['band']} · mean Δ={tt['delta_mean']} · **{tt['verdict']}**")
        a("")
        a("| 格 | n_h1 | n_empty | h1_mean | empty_mean | delta | 状态 |")
        a("|---|---:|---:|---:|---:|---:|---|")
        for c in tt["cells"]:
            a(f"| {c['cell']} | {c['n_h1']} | {c['n_empty']} | {c['h1_mean']} | "
              f"{c['empty_mean']} | {c['delta']} | {c['status']} |")
        a("")

    a("## J4 国家矩阵")
    a("")
    a("| 格 | n_total | U0050 | U0200 | U0800 | ok |")
    a("|---|---:|---:|---:|---:|---|")
    for m in report["J4_matrix"]["cells"]:
        pt = m["per_tier"]
        a(f"| {m['cell']} | {m['n_total']} | {pt.get('U0050', 0)} | {pt.get('U0200', 0)} | "
          f"{pt.get('U0800', 0)} | {'Y' if m['ok'] else 'N'} |")
    a("")

    if report["J5_perf"]["rows"]:
        a("## J5 性能样本")
        a("")
        a("| run_id | tier | fps | cpu0 | tick_miss |")
        a("|---|---|---:|---:|---:|")
        for p in report["J5_perf"]["rows"]:
            a(f"| {p['run_id']} | {p['tier']} | {p['fps_avg']} | {p['cpu0_avg']} | {p['tick_miss']} |")
        a("")

    a("## 作废/签名明细")
    a("")
    a("| run_id | tier | units_seen | countable | void_reason | misselect |")
    a("|---|---|---:|---|---|---|")
    for r in report["runs"]:
        if r.get("countable") and not r.get("misselect"):
            continue
        a(f"| {r.get('run_id')} | {r.get('tier')} | {r.get('units_seen')} | "
          f"{r.get('countable')} | {r.get('void_reason')} | {r.get('misselect')} |")
    a("")
    a("---")
    a("判分脚本：`tools/h1_remeasure_score.py` · 协议：`docs/re/h1_remeasure_protocol.md`")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# --schema
# ---------------------------------------------------------------------------
def print_schema() -> None:
    print(f"schema = {SCHEMA_ID}")
    print("fields:")
    for f in RUN_FIELDS:
        print(f"  - {f}")
    print("expected fingerprints:")
    for t, fp in EXPECTED_FP.items():
        print(f"  {t}: {fp}")
    print("misselect bands:", ", ".join(f"{c}±{w}" for c, w in MISSELECT_BANDS))


# ---------------------------------------------------------------------------
# --selftest（假数据跑通 schema）
# ---------------------------------------------------------------------------
def _run(run_id, seg, map_kind, tier, player, enemy, uc, units, fp="", **kw):
    row = {
        "run_id": run_id, "seg": seg, "map_kind": map_kind, "tier": tier,
        "player": player, "enemy": enemy, "unit_count": uc, "credits": kw.pop("credits", 0),
        "fingerprint_read": fp,
        "fingerprint_expect": EXPECTED_FP.get(tier, ""),
        "units_seen": units, "sample_frame": 15,
        "except_fresh": False, "restored": True, "invalid": False,
    }
    row.update(kw)
    return row


def build_fake_pass() -> dict:
    """三档 delta 恰为 50/200/800，矩阵 8 格各 3 轮 H1 + 3 轮空图。"""
    runs = []
    # 空图底座：SU=22
    for i, (p, e, uc) in enumerate(MATRIX_CELLS):
        for r in range(3):
            runs.append(_run(f"EMPTY-{i}-r{r}", "2", "empty", "NA", p, e, uc, 22))
    # H1：空图 + T
    base = 22
    for i, (p, e, uc) in enumerate(MATRIX_CELLS):
        for tier, T in TARGET.items():
            for r in range(3):
                runs.append(_run(
                    f"H1-{tier}-C{i}-r{r}", "3", "h1", tier, p, e, uc,
                    base + T,
                    fp=EXPECTED_FP[tier],
                    fps_avg=60.0, cpu0_avg=12.0, tick_miss=0.01,
                ))
    return {"schema": SCHEMA_ID, "batch_id": "selftest-pass", "runs": runs}


def build_fake_fail_713() -> dict:
    """U0200 读到 713（旧误选签名）仍企图计入。"""
    runs = []
    for r in range(3):
        runs.append(_run(f"EMPTY-r{r}", "2", "empty", "NA", "Americans", "Russians", 0, 22))
    for r in range(3):
        runs.append(_run(
            f"U0200-713-r{r}", "3", "h1", "U0200", "Random", "Random", 0,
            713, fp=EXPECTED_FP["U0200"], fps_avg=60.0, cpu0_avg=12.0, tick_miss=0.01,
        ))
    # 其它档凑一点合法数据，证明 FAIL 来自 J3 而非空表
    for tier, T in TARGET.items():
        if tier == "U0200":
            continue
        for r in range(3):
            runs.append(_run(
                f"{tier}-ok-r{r}", "3", "h1", tier, "Americans", "Russians", 0,
                22 + T, fp=EXPECTED_FP[tier],
            ))
    return {"schema": SCHEMA_ID, "batch_id": "selftest-fail-713", "runs": runs}


def build_fake_fail_fp() -> dict:
    """指纹不匹配（读回 U0200 却记 U0050）仍企图计数。"""
    runs = []
    for r in range(3):
        runs.append(_run(f"EMPTY-r{r}", "2", "empty", "NA", "Americans", "Russians", 0, 22))
    for r in range(3):
        runs.append(_run(
            f"U0050-badfp-r{r}", "3", "h1", "U0050", "Americans", "Russians", 0,
            72, fp=EXPECTED_FP["U0200"],  # 故意错
            fps_avg=60.0, cpu0_avg=12.0, tick_miss=0.01,
        ))
    for r in range(3):
        runs.append(_run(
            f"U0200-ok-r{r}", "3", "h1", "U0200", "Americans", "Russians", 0,
            222, fp=EXPECTED_FP["U0200"],
        ))
    for r in range(3):
        runs.append(_run(
            f"U0800-ok-r{r}", "3", "h1", "U0800", "Americans", "Russians", 0,
            822, fp=EXPECTED_FP["U0800"],
        ))
    return {"schema": SCHEMA_ID, "batch_id": "selftest-fail-fp", "runs": runs}


def build_fake_fail_scale() -> dict:
    """U0800 delta 出带（只给 400 而不是 800）。"""
    runs = []
    for r in range(3):
        runs.append(_run(f"EMPTY-r{r}", "2", "empty", "NA", "Americans", "Russians", 0, 22))
    for tier, T in TARGET.items():
        units = 22 + (400 if tier == "U0800" else T)
        for r in range(3):
            runs.append(_run(
                f"{tier}-r{r}", "3", "h1", tier, "Americans", "Russians", 0,
                units, fp=EXPECTED_FP[tier],
                fps_avg=60.0, cpu0_avg=12.0, tick_miss=0.01,
            ))
    return {"schema": SCHEMA_ID, "batch_id": "selftest-fail-scale", "runs": runs}


def run_selftest() -> int:
    SELFTEST_DIR.mkdir(parents=True, exist_ok=True)
    cases = [
        ("fake_pass.json", build_fake_pass, "PASS", "UNFREEZE_CANDIDATE"),
        ("fake_fail_713.json", build_fake_fail_713, "FAIL", "KEEP_FROZEN"),
        ("fake_fail_fp.json", build_fake_fail_fp, "FAIL", "KEEP_FROZEN"),
        ("fake_fail_scale.json", build_fake_fail_scale, "FAIL", "KEEP_FROZEN"),
    ]
    # 713 用例：J3 应 FAIL 且总判 FAIL
    ok = True
    lines = ["# h1_remeasure_score selftest", ""]
    for name, builder, exp_overall, exp_roi in cases:
        data = builder()
        path = SELFTEST_DIR / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        rep = score(load_evidence(path))
        md = to_markdown(rep)
        (SELFTEST_DIR / (path.stem + ".SCORE.md")).write_text(md, encoding="utf-8")
        (SELFTEST_DIR / (path.stem + ".score.json")).write_text(
            json.dumps({k: v for k, v in rep.items() if k != "runs"}, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        got_o, got_r = rep["overall"], rep["ROI"]["verdict"]
        hit = (got_o == exp_overall and got_r == exp_roi)
        # 额外断言
        extra = []
        if name == "fake_fail_713.json":
            extra.append(rep["J3_misselect"]["verdict"] == "FAIL" or rep["J3_misselect"]["misselect_n"] >= 3)
            extra.append(any(r.get("hard_flag") == "U0200_READ_AS_713" for r in rep["runs"]))
        if name == "fake_pass.json":
            extra.append(rep["J2_delta"]["verdict"] == "PASS")
            extra.append(rep["J1_fingerprint"]["void_rate"] == 0.0)
        if name == "fake_fail_fp.json":
            extra.append(rep["J1_fingerprint"]["void_rate"] > 0)
        if name == "fake_fail_scale.json":
            extra.append(rep["J2_delta"]["tiers"]["U0800"]["verdict"] == "OUT_BAND")
        ok = ok and hit and all(extra)
        status = "OK" if (hit and all(extra)) else "NG"
        lines.append(f"- [{status}] {name}: overall={got_o} (exp {exp_overall}) "
                     f"roi={got_r} (exp {exp_roi}) extra={extra}")
        print(f"[selftest] {name}: overall={got_o} roi={got_r} extra={extra} => {status}")

    lines.append("")
    lines.append(f"**selftest {'PASS' if ok else 'FAIL'}**")
    (SELFTEST_DIR / "SELFTEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 同时写一份 CSV 等价，验证 CSV 载入
    csv_path = SELFTEST_DIR / "fake_pass.csv"
    data = build_fake_pass()
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(RUN_FIELDS))
        w.writeheader()
        for row in data["runs"]:
            w.writerow({k: row.get(k, "") for k in RUN_FIELDS})
    rep_csv = score(load_evidence(csv_path))
    csv_ok = rep_csv["overall"] == "PASS"
    print(f"[selftest] fake_pass.csv: overall={rep_csv['overall']} => {'OK' if csv_ok else 'NG'}")
    ok = ok and csv_ok

    print(f"\nselftest {'PASS' if ok else 'FAIL'}  (artifacts: {SELFTEST_DIR})")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="H1 remeasure evidence scorer (H1RM)")
    ap.add_argument("evidence", nargs="?", help="evidence .json or .csv")
    ap.add_argument("--md", type=Path, default=None, help="markdown 报告输出路径")
    ap.add_argument("--json-out", type=Path, default=None, help="判分 JSON 输出路径")
    ap.add_argument("--min-rounds", type=int, default=MIN_ROUNDS_DEFAULT)
    ap.add_argument("--selftest", action="store_true", help="写假数据并跑通 schema")
    ap.add_argument("--schema", action="store_true", help="打印 schema 字段")
    args = ap.parse_args(argv)

    if args.schema:
        print_schema()
        return 0
    if args.selftest:
        return run_selftest()
    if not args.evidence:
        ap.error("需要 evidence 路径，或 --selftest / --schema")

    path = Path(args.evidence)
    if not path.is_file():
        print(f"ERROR: 文件不存在: {path}", file=sys.stderr)
        return 2
    try:
        data = load_evidence(path)
    except Exception as e:
        print(f"ERROR: 载入失败: {e}", file=sys.stderr)
        return 2

    report = score(data, min_rounds=args.min_rounds)
    md = to_markdown(report)

    md_path = args.md or DEFAULT_MD
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        slim = {k: v for k, v in report.items() if k != "runs"}
        slim["runs_annotated"] = [
            {kk: rr.get(kk) for kk in (
                "run_id", "tier", "map_kind", "units_seen", "fp_ok",
                "misselect", "countable", "void_reason", "hard_flag",
            )}
            for rr in report["runs"]
        ]
        args.json_out.write_text(
            json.dumps(slim, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )

    # 控制台摘要
    print(md.split("## 作废")[0])
    print(f"markdown -> {md_path}")
    print(f"OVERALL={report['overall']}  ROI={report['ROI']['verdict']}")
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
