"""_cf_lineage.py -- pairwise similarity / mtime lineage / family predicate.

Usage:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_lineage.py D:/Project/ra2-campaign-forge

Reads only. Writes ONLY to lead/check_family_20261109/_cf_lineage_out.json.
"""
import difflib
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(sys.argv[1])
WD = ROOT / "lead" / "check_family_20261109"
CENSUS = WD / "_cf_census_out.json"
OUT = WD / "_cf_lineage_out.json"

FOUR = {
    "d27": "lead/d27_ruling_20261106/check_d27.py",
    "d28": "lead/d28_ruling_20261106/check_d28.py",
    "d29": "lead/d29_ruling_20261106/check_d29.py",
    "d30": "lead/d30_ruling_20261106/check_d30.py",
}
ANCESTORS = {
    "d25": "lead/d25_ruling_20261106/check_d25.py",
    "d26": "lead/d26_ruling_20261106/check_d26.py",
}
ALL = {**FOUR, **ANCESTORS}


def norm(lines):
    """Normalize: strip, drop blank lines and pure-comment lines."""
    return [l.strip() for l in lines
            if l.strip() and not l.strip().startswith("#")]


def pairwise(a_lines, b_lines):
    a, b = norm(a_lines), norm(b_lines)
    # exact common lines (multiset)
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    common = sum((ca & cb).values())
    only_a = sum((ca - cb).values())
    only_b = sum((cb - ca).values())
    jacc = common / (common + only_a + only_b) if (common + only_a + only_b) else 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ratio = sm.ratio()
    blocks = [dict(a_start=x.a + 1, b_start=x.b + 1, size=x.size)
              for x in sm.get_matching_blocks() if x.size >= 3]
    return dict(a_norm=len(a), b_norm=len(b), common_lines=common,
                only_a=only_a, only_b=only_b,
                line_jaccard=round(jacc, 4), difflib_ratio=round(ratio, 4),
                matching_blocks_ge3=blocks)


def family_predicate(rel):
    """Code-level k->1bit family predicate, evaluated on source text only.

    F1: a literal requirements/tuple table with >=1 row whose word-list has
        k>=2 quoted tokens AND an OR (require_all=False / absent) branch
    F2: an any() (or any(present)) collapse of that OR word-list into 1 bool
    F3: a single aggregate PASS print + return/exit 0, no per-word hit output
    F4: section-body extractor (sections / section_bodies) feeding word tests
    """
    p = ROOT / rel
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    # F1: literal requirements table (4-tuple with require_all flag) OR
    #     d27-style 3-tuple OR word list
    has_req_table = bool(re.search(r"requirements\s*=\s*\(", text))
    or_rows = []
    for i, l in enumerate(lines, 1):
        qs = re.findall(r"[\"']([^\"']+)[\"']", l)
        if len(qs) >= 2 and ("False" in l or (l.strip().startswith("(") and
                                              "True" not in l and len(qs) >= 3)):
            or_rows.append(dict(line=i, tokens=qs))
    # F2: any() collapse
    any_lines = [i for i, l in enumerate(lines, 1) if "any(" in l]
    any_word = [i for i, l in enumerate(lines, 1)
                if "any(" in l and re.search(r"\b(word|keyword|n|w|present)\b", l)]
    # F3: single PASS exit
    pass_lines = [i for i, l in enumerate(lines, 1)
                  if re.match(r"^\s*print\(.*PASS", l)]
    exit_lines = [i for i, l in enumerate(lines, 1)
                  if re.search(r"return\s+0|return\s+0\s+if|sys\.exit|SystemExit", l)]
    hit_output = [i for i, l in enumerate(lines, 1)
                  if re.search(r"hits\b|PER_NEEDLE|hit_set|matched_words|逐输入|逐词", l, re.I)]
    # F4
    extractor = [i for i, l in enumerate(lines, 1)
                 if re.search(r"def section_bodies|def sections|def section_body", l)]
    # classify
    f1 = has_req_table or bool(or_rows)
    f2 = bool(any_word)
    f3 = len(pass_lines) >= 1 and bool(exit_lines) and not hit_output
    f4 = bool(extractor)
    verdict = "CONFIRMED" if (f1 and f2 and f3 and f4) else (
        "SUSPECT" if (f2 and f3) else "NOT_FAMILY")
    return dict(rel=rel, F1_or_word_table=dict(has_req_table=has_req_table,
                                               or_rows=or_rows),
                F2_any_collapse=dict(any_lines=any_lines, any_word_lines=any_word),
                F3_single_pass=dict(pass_lines=pass_lines, exit_lines=exit_lines,
                                    per_word_hit_output=hit_output),
                F4_section_extractor=extractor,
                flags=dict(F1=f1, F2=f2, F3=f3, F4=f4), verdict=verdict)


def main():
    src = {k: (ROOT / v).read_text(encoding="utf-8-sig").splitlines()
           for k, v in ALL.items()}
    # pairwise across 6
    pairs = {}
    keys = list(ALL)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            pairs["%s|%s" % (a, b)] = pairwise(src[a], src[b])

    # exact shared function bodies: sections() in d26/d27; section_bodies() in d29/d30
    def func(lines, name):
        out, on = [], False
        for l in lines:
            if re.match(r"^def %s\(" % re.escape(name), l):
                on = True
            elif on and re.match(r"^def ", l):
                break
            if on:
                out.append(l.rstrip())
        return [x.strip() for x in out if x.strip() and not x.strip().startswith("#")]

    func_cmp = {}
    for name in ("sections", "section_bodies", "section_body"):
        owners = [k for k in keys if func(src[k], name)]
        func_cmp[name] = dict(owners=owners, bodies={
            k: func(src[k], name) for k in owners})
        if len(owners) >= 2:
            for i in range(len(owners)):
                for j in range(i + 1, len(owners)):
                    a, b = owners[i], owners[j]
                    A, B = func(src[a], name), func(src[b], name)
                    func_cmp[name]["%s|%s" % (a, b)] = dict(
                        identical=A == B, a_len=len(A), b_len=len(B),
                        common=sum(1 for x in A if x in B),
                        ratio=round(difflib.SequenceMatcher(None, A, B,
                                    autojunk=False).ratio(), 4))

    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = census["all_files"]
    # mtime lineage of the whole 173 + combo members
    combo = set(census["summary"]["combo_orchany_passprint"])
    mtime_all = sorted([dict(rel=r["rel"], mtime=r["mtime_iso"],
                             sha16=r["sha256"][:16],
                             in_combo=r["rel"] in combo,
                             orch_any=r["orch_any"], pass_print=r["pass_print"])
                        for r in rows], key=lambda x: x["mtime"])
    # family predicate over 25 orchestrator + all combo + 4 + d25/d26
    target = set(census["summary"]["combo_orchany_passprint"]) | set(FOUR.values()) | set(ANCESTORS.values())
    fam = {rel: family_predicate(rel) for rel in sorted(target)}

    result = dict(
        pairwise_6=pairs, function_identity=func_cmp,
        mtime_first20=mtime_all[:20],
        combo_members_by_mtime=[x for x in mtime_all if x["in_combo"]],
        family_predicate=fam,
        family_counts={v: sum(1 for f in fam.values() if f["verdict"] == v)
                       for v in ("CONFIRMED", "SUSPECT", "NOT_FAMILY")},
    )
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(
        pairwise={k: dict(common_lines=v["common_lines"], only_a=v["only_a"],
                          only_b=v["only_b"], line_jaccard=v["line_jaccard"],
                          difflib_ratio=v["difflib_ratio"])
                  for k, v in pairs.items()},
        func_identity={k: {kk: vv for kk, vv in v.items() if isinstance(vv, dict)
                           and "identical" in vv} for k, v in func_cmp.items()},
        mtime_first8=mtime_all[:8],
        family_counts=result["family_counts"],
        confirmed=[r for r, f in fam.items() if f["verdict"] == "CONFIRMED"],
        suspect=[r for r, f in fam.items() if f["verdict"] == "SUSPECT"],
    ), ensure_ascii=False, indent=1))
    print("WROTE", OUT.as_posix())


if __name__ == "__main__":
    main()
