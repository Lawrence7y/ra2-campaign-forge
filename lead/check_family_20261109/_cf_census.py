"""_cf_census.py -- read-only repository-wide census of check_*.py (list-driven).

Usage:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_census.py D:/Project/ra2-campaign-forge

Reads the 173 paths from _cf_filelist.txt, computes hashlib SHA256 + byte length,
classifies lines under several explicitly-defined criteria, independently
re-checks the orchestrator's literal 25-file run, and writes ONLY to
lead/check_family_20261109/_cf_census_out.json + _cf_full_census.md.
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(sys.argv[1])
WD = ROOT / "lead" / "check_family_20261109"
LIST = WD / "_cf_filelist.txt"
OUT = WD / "_cf_census_out.json"
TABLE = WD / "_cf_full_census.md"

ORCH = {
    "lead/a_residual_20261106/check_a_residual.py": (10477, "10aae9d6fd4d45c5", [], [], []),
    "lead/b2b_candidate_20261106/check_candidate.py": (12175, "4b9a278b91722f8b", [], [], [263]),
    "lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py": (16874, "7c4b9aa9cabe9912", [266], [], [358]),
    "lead/b2b_candidate_review_20261106/check_semantic_review.py": (15332, "814c2ceec0591ae3", [257], [], [330]),
    "lead/b2b_design_20261106/check_b2b.py": (9118, "fc4fd378d3d1080c", [], [], []),
    "lead/b2b_preaudit_20261106/check_b2b_preaudit.py": (13946, "293758f274f4fba1", [], [], []),
    "lead/b2_preaudit_20261106/check_b2_preaudit.py": (10300, "cb0926e1eec7c203", [], [], [231]),
    "lead/d13b_design_20261106/check_d13b.py": (9942, "316949444d9fd8f4", [], [], []),
    "lead/d13b_timing_clarify_20261106/check_timing_clarify.py": (16844, "de86d9fc4bdb0b2a", [], [], []),
    "lead/d25_ruling_20261106/check_d25.py": (2877, "ceca9d89f38a3701", [], [], []),
    "lead/d26_ruling_20261106/check_d26.py": (4245, "0018116a350de46d", [85], [], [103]),
    "lead/d27_ruling_20261106/check_d27.py": (3764, "3b769d7c64c27251", [86], [], []),
    "lead/d28_ruling_20261106/check_d28.py": (4539, "5b42a34a40046d7a", [], [94, 97, 98], [115]),
    "lead/d29_ruling_20261106/check_d29.py": (3906, "2a50b09adff555db", [84], [80, 83, 88], [105]),
    "lead/d30_ruling_20261106/check_d30.py": (3926, "6cb737963fc62a0e", [84], [80, 83, 88], [105]),
    "lead/early_trigger_feasibility_20261106/check_feasibility.py": (18295, "406c1d58ca0a2265", [366], [], []),
    "lead/nextstep_plan_20261106/check_plan.py": (3956, "0ead428e33d8707e", [], [], []),
    "lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py": (3764, "3b769d7c64c27251", [86], [], [100]),
    "lead/stale_pass_20261109/_sp_sandbox/check_d27_injected.py": (3783, "f404f58783ab4da0", [86], [], [100]),
    "lead/stale_pass_20261109/_sp_sandbox/d28/check_d28_baseline.py": (4539, "5b42a34a40046d7a", [], [94, 97, 98], [115]),
    "lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py": (3906, "2a50b09adff555db", [84], [80, 83, 88], [105]),
    "lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_injected.py": (3934, "2399e95a43eaafa4", [84], [80, 83, 88], [105]),
    "lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py": (3926, "6cb737963fc62a0e", [84], [80, 83, 88], [105]),
    "lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_injected.py": (3951, "b1670537e12a6d7c", [84], [80, 83, 88], [105]),
    "lead/stall_event_def_20261106/check_stall_def.py": (10883, "ce6e5d9f65fb764a", [118], [], [244]),
}

# Orchestrator's "any" criterion, reverse-engineered from its own 25-file run:
# single line contains "any(" AND a membership test (" in ") BEFORE " for ",
# AND another " in " after the " for " (the generator's iterable).
def orch_any_line(s):
    if "any(" not in s or " for " not in s:
        return False
    head, _, tail = s.partition(" for ")
    return " in " in head and " in " in tail


def classify(lines):
    d = dict(orch_any=[], any_gen=[], any_membership=[], any_word_or=[],
             require_all=[], pass_literal=[], pass_fstring=[], pass_print=[],
             pass_exit=[], all_gen=[], all_call=[], tuple2_lines=[],
             requirements_assign=[], section_bodies_def=[])
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if orch_any_line(s):
            d["orch_any"].append(i)
        if "any(" in s and " for " in s and " in " in s:
            d["any_gen"].append(i)
        if "any(" in s and " in " in s:
            d["any_membership"].append(i)
        # k>=2 OR word-list membership test inside any()
        if "any(" in s and re.search(r"\b(word|keyword|n|token|w|name)\s+in\s+", s):
            d["any_word_or"].append(i)
        if "require_all" in s:
            d["require_all"].append(i)
        if re.match(r"^\s*print\(\s*[\"']PASS", ln):
            d["pass_literal"].append(i)
        if re.match(r"^\s*print\(\s*f[\"']PASS", ln):
            d["pass_fstring"].append(i)
        if re.match(r"^\s*print\(.*PASS", ln):
            d["pass_print"].append(i)
        if "all(" in s:
            d["all_call"].append(i)
            if " for " in s and " in " in s:
                d["all_gen"].append(i)
        if len(re.findall(r"[\"'][^\"']+[\"']", s)) >= 2 and "(" in s:
            d["tuple2_lines"].append(i)
        if re.search(r"requirements\s*=\s*\(", s):
            d["requirements_assign"].append(i)
        if re.search(r"def section_bodies|def sections", s):
            d["section_bodies_def"].append(i)
    # single-row PASS exit: a print(...PASS...) followed within 3 lines by
    # return 0 / sys.exit / SystemExit (the aggregate verdict exit)
    for i in d["pass_print"]:
        window = "\n".join(lines[i - 1:i + 3])
        if re.search(r"return\s+0|sys\.exit|SystemExit", window):
            d["pass_exit"].append(i)
    return d


def main():
    rels = []
    for ln in LIST.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        t = ln.strip()
        rels.append(t[2:] if t.startswith("./") else t)
    rows = []
    for rel in rels:
        p = ROOT / rel
        if not p.is_file():
            rows.append(dict(rel=rel, missing=True))
            continue
        data = p.read_bytes()
        lines = data.decode("utf-8-sig", errors="replace").splitlines()
        c = classify(lines)
        rows.append(dict(rel=rel, bytes=len(data),
                         sha256=hashlib.sha256(data).hexdigest(),
                         nlines=len(lines), mtime=p.stat().st_mtime,
                         mtime_iso=datetime.fromtimestamp(p.stat().st_mtime).isoformat(
                             sep=" ", timespec="seconds"),
                         **c))
    by_rel = {r["rel"]: r for r in rows}

    orch_check = []
    for rel, (ob, osha, oany, oreql, opass) in ORCH.items():
        r = by_rel.get(rel)
        if r is None or r.get("missing"):
            orch_check.append(dict(rel=rel, present=False))
            continue
        orch_check.append(dict(
            rel=rel, present=True,
            bytes=r["bytes"], orch_bytes=ob, bytes_match=r["bytes"] == ob,
            sha256=r["sha256"], orch_sha16=osha, sha16_match=r["sha256"][:16] == osha,
            orch_any=r["orch_any"], orch_any_given=oany, any_match=r["orch_any"] == oany,
            require_all=r["require_all"], orch_req=oreql, req_match=r["require_all"] == oreql,
            pass_print=r["pass_print"], pass_literal=r["pass_literal"],
            pass_fstring=r["pass_fstring"], orch_pass_given=opass,
            pass_match=any(i in r["pass_print"] for i in opass) if opass else
                       not r["pass_print"],
        ))
    # detect internal contradiction: same sha16 but different pass list
    by_sha = {}
    for x in orch_check:
        if x.get("present"):
            by_sha.setdefault(x["sha256"], []).append((x["rel"], tuple(x["orch_pass_given"])))
    contradictions = {sha: v for sha, v in by_sha.items()
                      if len(set(p for _, p in v)) > 1}

    def cnt(k):
        return sum(1 for r in rows if r.get(k))
    combo_lit = [r["rel"] for r in rows if r.get("orch_any") and r.get("pass_literal")]
    combo_print = [r["rel"] for r in rows if r.get("orch_any") and r.get("pass_print")]
    combo_word = [r["rel"] for r in rows if r.get("any_word_or") and r.get("pass_print")]

    summary = dict(
        n_orch_any=cnt("orch_any"), n_any_gen=cnt("any_gen"),
        n_any_membership=cnt("any_membership"), n_any_word_or=cnt("any_word_or"),
        n_require_all=cnt("require_all"), n_pass_literal=cnt("pass_literal"),
        n_pass_fstring=cnt("pass_fstring"), n_pass_print=cnt("pass_print"),
        n_pass_exit=cnt("pass_exit"), n_all_call=cnt("all_call"), n_all_gen=cnt("all_gen"),
        n_requirements_assign=cnt("requirements_assign"),
        n_combo_orchany_passliteral=len(combo_lit), combo_orchany_passliteral=combo_lit,
        n_combo_orchany_passprint=len(combo_print), combo_orchany_passprint=combo_print,
        n_combo_wordor_passprint=len(combo_word), combo_wordor_passprint=combo_word,
    )
    result = dict(root=str(ROOT), total_files=len(rows),
                  missing=[r["rel"] for r in rows if r.get("missing")],
                  summary=summary, orchestrator_25_check=orch_check,
                  orch_pass_contradictions=contradictions, all_files=rows)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    # full 173-row table (path / bytes / sha16 / nlines / mtime / flags)
    buf = ["# _cf_full_census.md — 全库 check_*.py 全量清单（只读普查）", "",
           "`find . -type f -name \"check_*.py\" | sort` 得 %d 件；SHA256 由 hashlib 实算。" % len(rows),
           "全 64 位指纹见 `_cf_census_out.json` 的 `all_files[*].sha256`。", "",
           "| # | rel | bytes | sha16 | lines | mtime | orch_any | require_all | pass_print |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        if r.get("missing"):
            buf.append("| %d | %s | MISSING | | | | | | |" % (i, r["rel"]))
            continue
        f = lambda k: ",".join(map(str, r.get(k, []))) or "-"
        buf.append("| %d | %s | %d | %s | %d | %s | %s | %s | %s |" % (
            i, r["rel"], r["bytes"], r["sha256"][:16], r["nlines"],
            r["mtime_iso"], f("orch_any"), f("require_all"), f("pass_print")))
    TABLE.write_text("\n".join(buf) + "\n", encoding="utf-8")

    mism = [x for x in orch_check if not x.get("present") or not (
        x.get("bytes_match") and x.get("sha16_match") and x.get("any_match")
        and x.get("req_match"))]
    print(json.dumps(dict(total=len(rows), missing=result["missing"],
                          summary={k: v for k, v in summary.items() if not isinstance(v, list)},
                          orch_field_mismatches=mism,
                          orch_pass_contradictions=contradictions),
                     ensure_ascii=False, indent=1))
    print("WROTE", OUT.as_posix())
    print("WROTE", TABLE.as_posix())


if __name__ == "__main__":
    main()
