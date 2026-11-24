# -*- coding: utf-8 -*-
r"""_vi_shadow.py -- V12 影响面评估：影子模式全量独立重跑（只读，绝不插门禁）。

跑法：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/v12_impact_20261109/_vi_shadow.py

口径（与编排方实跑一致，便于逐处对账）：
  · 域清单 / main / banned 词表取自 lead/gate_rejudge32_20261109/_rj_delivery_baseline.json
    的 rows[*]（32 域；其中 2 域 banned=[]，逐域如实保留）。
  · 对每域只读 main 文件（utf-8），用 _g7_predicates.r10_scan(text, banned) 得逐处
    R10 kind；对同一处 (pos, token) 调 _v12_rule.classify_v12 得 V12 verdict。
  · 两个判据并排输出，不合并、不改任何既有件、不写任何真门禁。
  · 另用独立 re.finditer 复算 raw 命中集，按 (pos, token) 与 R10 对账。
  · 另独立复算 V2_OVERRIDE / WEAK_V1 标记在【同一分析单元 U】内的共现，
    用于回答「hard 与 override 是否同触」（classify_v12 命中 hard 会提前 return，
    override 字段恒为空，故必须外部独立复算）。

零真机、零采样代码；sys.dont_write_bytecode=True 防在只读域生成 __pycache__。
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"
BASELINE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G7 = load(PRED, "_vi_g7")
R = load(RULE, "_vi_v12_rule")


def sha_bytes(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def orig_line(text, pos):
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    if b < 0:
        b = len(text)
    return text[a:b]


def co_trigger(text, pos, end, tok, v):
    """独立复算：同一 U 内 hard / override / weak 三类标记是否同触。
    classify_v12 命中 hard 会提前 return，override/weak 恒为空 —— 审计可追溯性
    只能靠此处外部复算。"""
    line, U, off, is_table, rel_u = R._unit_and_line(text, pos, end, tok)
    pre, post = U[:max(0, rel_u)], U[max(0, rel_u) + len(tok):]
    U_bare = R._strip_quotes(U)
    adj_neg = bool(pre) and (pre[-1] in R.ADJ_NEG_CHARS or bool(R.ADJ_NEG_RE.search(pre)))
    prohibit_U = any(k in U_bare for k in R.PROHIBIT)
    ov_kw = [k for k in R.V2_OVERRIDE if k in U]
    ov_re = bool(R.V2_OVERRIDE_RE.search(U))
    weak_pre = bool(R.W1_RE.search(pre))
    weak_num = bool(R.W1_NUM_RE.match(U) or R.W1_NUM_RE.match(line))
    return {
        "U": U, "pre": pre, "post": post, "is_table": is_table,
        "hard_reported": list(v["hard"]),
        "override_in_U_kw": ov_kw,
        "override_in_U_re": ov_re,
        "override_would_fire": bool(ov_kw or ov_re) and not adj_neg and not prohibit_U,
        "adj_neg": adj_neg, "prohibit_U": prohibit_U,
        "weak_in_prefix": weak_pre, "weak_num": weak_num,
        "weak_would_fire": bool(weak_pre or weak_num),
        "hard_AND_override": bool(v["hard"]) and bool(ov_kw or ov_re),
        "hard_AND_weak": bool(v["hard"]) and bool(weak_pre or weak_num),
    }


def main():
    bl = json.loads(BASELINE.read_text(encoding="utf-8"))
    rows_out, lines_out = [], []
    lines_out.append("=== _vi_shadow.py 影子模式独立重跑 ===")
    lines_out.append("baseline = %s  domains=%d rows=%d" %
                     (BASELINE.as_posix(), bl["domains"], len(bl["rows"])))
    for n in ("PRED", "RULE", "BASELINE"):
        p = {"PRED": PRED, "RULE": RULE, "BASELINE": BASELINE}[n]
        s, b = sha_bytes(p)
        lines_out.append("[FP] %-9s %s sha256=%s bytes=%d" % (n, p.name, s, b))

    total_hits = 0
    grand = {"assertion_V2": [], "assertion_V1": [], "negquote_V2": [],
             "negquote_V1": [], "s3_default": [], "co_hard_override": [],
             "co_hard_weak": []}

    for r in bl["rows"]:
        dom, main, bans = r["domain"], r["main"], r["params"].get("banned", [])
        path = ROOT / dom / main
        raw_b = path.read_bytes()
        text = raw_b.decode("utf-8")
        s, b = sha_bytes(path)
        fp_match = (s == r["mainSha256"] and b == r["mainBytes"])

        # 独立 raw 命中集（不借 R10）
        raw_hits = []
        for tok in bans:
            for m in re.finditer(re.escape(tok), text):
                raw_hits.append((m.start(), tok))
        raw_hits.sort()

        problems, warnings, hits = G7.r10_scan(text, bans)
        r10_set = sorted((h["pos"], h["token"]) for h in hits)
        identical = (r10_set == raw_hits)

        dom_rec = {
            "domain": dom, "main": main, "banned": bans,
            "sha256": s, "bytes": b, "baseline_fp_match": fp_match,
            "r10_problems": len(problems), "r10_warnings": len(warnings),
            "r10_problem_texts": problems,
            "raw_hits": len(raw_hits),
            "raw_unique_pos": len(set(p for p, _ in raw_hits)),
            "raw_overlap_extra": len(raw_hits) - len(set(p for p, _ in raw_hits)),
            "raw_vs_r10_identical": identical,
            "hits": [],
        }

        lines_out.append("")
        lines_out.append("[DOM] %s | %s | sha=%s bytes=%d FP_MATCH_BASELINE=%s" %
                         (dom, main, s[:12], b, fp_match))
        lines_out.append("      banned=%r R10_problems=%d warnings=%d RAW=%d (uniq_pos=%d overlap_extra=%d) RAW==R10:%s" %
                         (bans, len(problems), len(warnings), len(raw_hits),
                          dom_rec["raw_unique_pos"], dom_rec["raw_overlap_extra"], identical))

        for h in sorted(hits, key=lambda x: (x["pos"], x["token"])):
            tok, pos, end = h["token"], h["pos"], h["pos"] + len(h["token"])
            L = text.count("\n", 0, pos) + 1
            ctx = G7.r10_context(text, pos, end)
            v = R.classify_v12(text, pos, end, tok)
            ct = co_trigger(text, pos, end, tok, v)
            orig = orig_line(text, pos)

            rec = {
                "domain": dom, "main": main, "line": L, "pos": pos,
                "token": tok, "r10_kind": h["kind"],
                "r10_neg_count": ctx["neg_count"], "r10_in_span": ctx["in_span"],
                "r10_dbl": ctx["dbl"], "r10_marked": ctx["marked"],
                "v12_verdict": v["verdict"], "hard": v["hard"], "weak": v["weak"],
                "override": v["override"], "review_flag": v["review_flag"],
                "reason": v["reason"], "unit": v["unit"], "orig": orig,
                "co": ct,
            }
            dom_rec["hits"].append(rec)
            total_hits += 1

            # 四象限 + S3 + 共触
            neq = h["kind"] in ("negation", "quote_mention", "double_neg")
            key = ("assertion" if h["kind"] == "assertion" else "negquote") + "_" + v["verdict"]
            if key in grand:
                grand[key].append((dom, L, pos, tok, h["kind"]))
            if v["review_flag"]:
                grand["s3_default"].append((dom, L, pos, tok, h["kind"]))
            if ct["hard_AND_override"]:
                grand["co_hard_override"].append((dom, L, pos, tok, ct["override_in_U_kw"], ct["override_in_U_re"]))
            if ct["hard_AND_weak"]:
                grand["co_hard_weak"].append((dom, L, pos, tok))

            lines_out.append("   L%-4d pos=%-6d tok=%-10s R10=%-13s V12=%s hard=%r weak=%r ov=%r review=%s" %
                             (L, pos, tok, h["kind"], v["verdict"], v["hard"], v["weak"],
                              v["override"], v["review_flag"]))
            lines_out.append("        reason = %s" % v["reason"])
            lines_out.append("        U     = %r" % v["unit"])
            lines_out.append("        ORIG  = %s" % orig[:400])
            lines_out.append("        CO    = hard_AND_override=%s (ov_kw=%r ov_re=%s would_fire=%s) hard_AND_weak=%s (weak_pre=%s num=%s)" %
                             (ct["hard_AND_override"], ct["override_in_U_kw"], ct["override_in_U_re"],
                              ct["override_would_fire"], ct["hard_AND_weak"], ct["weak_in_prefix"], ct["weak_num"]))

        rows_out.append(dom_rec)

    # ---- 汇总 ----
    summary = {
        "domains_total": len(rows_out),
        "domains_with_nonempty_banned": sum(1 for x in rows_out if x["banned"]),
        "domains_with_empty_banned": [x["domain"] for x in rows_out if not x["banned"]],
        "domains_with_hits": [x["domain"] for x in rows_out if x["hits"]],
        "domains_with_hits_n": sum(1 for x in rows_out if x["hits"]),
        "total_hits": total_hits,
        "r10_problems_total": sum(x["r10_problems"] for x in rows_out),
        "raw_vs_r10_all_identical": all(x["raw_vs_r10_identical"] for x in rows_out),
        "baseline_fp_all_match": all(x["baseline_fp_match"] for x in rows_out),
        "quadrants": {k: len(v) for k, v in grand.items()},
        "quadrant_items": {k: v for k, v in grand.items()},
        "r10_kind_counts": {},
        "v12_verdict_counts": {},
        "hard_marker_counts": {},
    }
    for x in rows_out:
        for h in x["hits"]:
            summary["r10_kind_counts"][h["r10_kind"]] = summary["r10_kind_counts"].get(h["r10_kind"], 0) + 1
            summary["v12_verdict_counts"][h["v12_verdict"]] = summary["v12_verdict_counts"].get(h["v12_verdict"], 0) + 1
            for m in h["hard"]:
                summary["hard_marker_counts"][m] = summary["hard_marker_counts"].get(m, 0) + 1

    lines_out.append("")
    lines_out.append("=== SUMMARY ===")
    lines_out.append(json.dumps(summary, ensure_ascii=False, indent=1))

    (WD / "_vi_shadow_out.json").write_text(
        json.dumps({"summary": summary, "rows": rows_out}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (WD / "_vi_shadow_out.txt").write_text("\n".join(lines_out) + "\n", encoding="utf-8")

    print("== _vi_shadow.py 独立重跑完成 ==")
    print("domains_total=%d nonempty_banned=%d empty_banned=%d" %
          (summary["domains_total"], summary["domains_with_nonempty_banned"],
           len(summary["domains_with_empty_banned"])))
    print("domains_with_hits=%d  total_hits=%d  r10_problems_total=%d" %
          (summary["domains_with_hits_n"], total_hits, summary["r10_problems_total"]))
    print("RAW==R10 all identical = %s ; baseline FP all match = %s" %
          (summary["raw_vs_r10_all_identical"], summary["baseline_fp_all_match"]))
    print("R10 kinds  = %s" % json.dumps(summary["r10_kind_counts"], ensure_ascii=False))
    print("V12 verdict= %s" % json.dumps(summary["v12_verdict_counts"], ensure_ascii=False))
    print("quadrants  = %s" % json.dumps(summary["quadrants"], ensure_ascii=False))
    print("hard marks = %s" % json.dumps(summary["hard_marker_counts"], ensure_ascii=False))
    print("written: %s ; %s" % (WD / "_vi_shadow_out.json", WD / "_vi_shadow_out.txt"))


if __name__ == "__main__":
    main()
