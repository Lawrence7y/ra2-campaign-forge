# -*- coding: utf-8 -*-
r"""_rj_double_track.py — 判据重判员：32 域双轨重判（朴素字面 vs R10/R12 真实谓词）。

零真机、零采样、绝对只读：只读 32 域主件 + 谓词库 + 本任务自己的基线重跑件；
所有产出落唯一写域 lead/gate_rejudge32_20261109/，前缀 _rj_。

双轨定义（与编排方口径一致）：
  朴素轨 = 门禁家族现状 `for bad in [...]: if bad in t: P.append('含越权断言 '+bad)`
           —— 每个 token 至多报 1 处（不看语境、不看出现次数）。
  R10 轨 = _g7_predicates.r10_scan(text, banned) —— 逐处出现做语境分类，
           assertion 报 problem；negation / quote_mention 报 warning；double_neg 交 R12。
  R12 轨 = _g7_predicates.r12_scan(text, banned) —— 双重否定构式重新判违规。
谓词加载前用 hashlib 实算指纹，与编排方派发值比对，失配拒绝运行。
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
BASE = WDIR / "_rj_baseline_rerun.json"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
PRED_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
PRED_BYTES = 11743


def load_pred():
    raw = PRED.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != PRED_SHA or len(raw) != PRED_BYTES:
        raise RuntimeError("谓词库指纹失配 %s/%d != %s/%d"
                           % (sha, len(raw), PRED_SHA, PRED_BYTES))
    spec = importlib.util.spec_from_file_location("_rj_g7_predicates", PRED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def line_text(text, pos):
    s = text.rfind("\n", 0, pos) + 1
    e = text.find("\n", pos)
    if e < 0:
        e = len(text)
    return text[s:e]


def clause_text(text, pos, back=90, fwd=60):
    """取命中所在的子句（含左右邻字，逐字保留），用于语境判读。"""
    s = max(0, pos - back)
    e = min(len(text), pos + fwd)
    return text[s:e]


def main():
    g7 = load_pred()
    base = json.loads(BASE.read_text(encoding="utf-8"))
    rows = base["rows"]
    out = {"pred_sha256": PRED_SHA, "pred_bytes": PRED_BYTES,
           "baseline_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
           "domains": len(rows), "rows": []}
    for r in rows:
        dom = r["domain"]
        main_name = r["main"]
        mp = ROOT / dom.rstrip("/") / main_name
        banned = r["params"]["banned"]
        raw = mp.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        # --- 朴素轨：每 token 至多 1 处 ---
        naive_problems = []
        naive_occ = {}
        for tok in banned:
            hits = list(re.finditer(re.escape(tok), text))
            naive_occ[tok] = len(hits)
            if hits:
                naive_problems.append("含越权断言 " + tok)
        # --- R10 / R12 轨 ---
        r10_problems, r10_warnings, r10_hits = g7.r10_scan(text, banned)
        r12_problems, r12_hits = g7.r12_scan(text, banned)
        # 逐处命中明细（含行号、原句、子句、语境类别）
        occ = []
        for h in r10_hits:
            pos = h["pos"]
            occ.append({"token": h["token"], "pos": pos,
                        "line": line_of(text, pos),
                        "kind": h["kind"], "neg_count": h["neg_count"],
                        "in_span": h["in_span"],
                        "line_text": line_text(text, pos),
                        "clause": clause_text(text, pos)})
        # R12 命中的行号
        r12_detail = [{"token": h["token"], "pos": h["pos"],
                       "line": line_of(text, h["pos"]),
                       "line_text": line_text(text, h["pos"])} for h in r12_hits]
        out["rows"].append({
            "domain": dom, "main": main_name,
            "main_bytes": len(raw), "main_sha256": hashlib.sha256(raw).hexdigest(),
            "banned": banned,
            "bindings_baseline": r["bindings"],
            "bindingRegex": r["params"]["bindingRegex"],
            "gateProblems_baseline": r["gateProblems"],
            "naive": {"problems": naive_problems, "count": len(naive_problems),
                      "occurrences_per_token": naive_occ},
            "r10": {"problems": r10_problems, "count": len(r10_problems),
                    "warnings": r10_warnings, "warnings_count": len(r10_warnings),
                    "occurrences": len(r10_hits)},
            "r12": {"problems": r12_problems, "count": len(r12_problems),
                    "hits": r12_detail},
            "hits": occ,
        })
    W = WDIR / "_rj_double_track_out.json"
    W.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # 控制台摘要（可复核）
    print("pred_sha256=%s/%dB baseline_sha256=%s domains=%d"
          % (PRED_SHA, PRED_BYTES, out["baseline_sha256"], out["domains"]))
    with_ban = [x for x in out["rows"] if x["banned"]]
    hit_any = [x for x in out["rows"]
               if x["naive"]["count"] or x["r10"]["count"] or x["r12"]["count"]]
    print("with_banned_list=%d  hit_on_any_track=%d" % (len(with_ban), len(hit_any)))
    for x in out["rows"]:
        if x["naive"]["count"] or x["r10"]["count"] or x["r12"]["count"]:
            print("  %-48s %-38s naiveP=%d r10P=%d r12P=%d r10W=%d occ=%d"
                  % (x["domain"], x["main"], x["naive"]["count"],
                     x["r10"]["count"], x["r12"]["count"],
                     x["r10"]["warnings_count"], x["r10"]["occurrences"]))
    print("wrote " + str(W))


main()
