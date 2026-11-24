# -*- coding: utf-8 -*-
"""M60 independent recomputation. READ ONLY. Run before and after merge."""
import sys, re, hashlib, os, json
from collections import Counter

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(BASE, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(BASE, "COVERAGE", "PANEL.md")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
B1 = os.path.join(BASE, "SEMFIX_ENGFAM_B1", "coverage_delta.tsv")
B2 = os.path.join(BASE, "SEMFIX_ENGFAM_B2", "coverage_delta.tsv")
B1V = os.path.join(BASE, "SEMFIX_ENGFAM_B1", "_audit", "verdict.tsv")
B2V = os.path.join(BASE, "SEMFIX_ENGFAM_B2", "_audit", "verdict.tsv")

SYS = ["S%02d" % i for i in range(1, 23)]
UNPROVEN_RE = re.compile(r"unproven|unverified|not proven", re.I)


def read_tsv(path, skip_header=True):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        lines = f.read().splitlines()
    if skip_header:
        lines = lines[1:]
    return [ln.split("\t") for ln in lines if ln != ""]


def load_atlas():
    rows = read_tsv(ATLAS)
    s = set()
    for r in rows:
        if r:
            s.add(r[0].strip().upper())
    return s, len(rows)


def load_cov():
    rows = read_tsv(COV)
    bad = [i for i, r in enumerate(rows, 2) if len(r) != 8]
    return rows, bad


def main():
    atlas_set, atlas_rows = load_atlas()
    cov, bad = load_cov()
    print("ATLAS rows=%d unique_entries_upper=%d" % (atlas_rows, len(atlas_set)))
    print("COV data rows=%d  bad_width_rows=%s" % (len(cov), bad[:10]))
    assert not bad, "coverage has rows != 8 cols"

    # whole-table counts
    grade_ct = Counter(r[4] for r in cov)
    proved_all = sum(1 for r in cov if r[4] == "[已证]")
    proved_in = sum(1 for r in cov if r[4] == "[已证]" and r[0].strip().upper() in atlas_set)
    proved_out = proved_all - proved_in
    unproven_rows = [r for r in cov if UNPROVEN_RE.search(r[3])]
    print("GRADE histogram:", dict(grade_ct))
    print("PROVED all=%d atlas_in=%d atlas_out=%d" % (proved_all, proved_in, proved_out))
    print("UNPROVEN-family rows=%d" % len(unproven_rows))
    for r in unproven_rows:
        m = UNPROVEN_RE.search(r[3])
        print("  UNPROVEN %s %s grade=%s hit=%s :: %s" % (r[0], r[1], r[4], m.group(0), r[3][:90]))

    # 22 subsystem recompute (atlas-internal)
    stats = {}
    sum_p = sum_s = sum_n = 0
    for s in SYS:
        rows = [r for r in cov if r[1] == s and r[0].strip().upper() in atlas_set]
        n = len(rows)
        p = sum(1 for r in rows if r[4] == "[已证]")
        st = sum(1 for r in rows if r[4] == "[已证]" and "未证" not in r[3])
        stats[s] = (n, p, st)
        sum_n += n; sum_p += p; sum_s += st
    print("\n=== 22 subsystem recompute (atlas-internal) ===")
    for s in SYS:
        n, p, st = stats[s]
        print("%s n=%d proved=%d strict=%d  pct=%.2f strictpct=%.2f  ceil50=%d  nom=%s strict=%s" % (
            s, n, p, st, 100.0*p/n if n else 0, 100.0*st/n if n else 0,
            -(-n//2), "达标" if p >= -(-n//2) else "—", "达标" if st >= -(-n//2) else "—"))
    print("SUM22 n=%d proved=%d strict=%d" % (sum_n, sum_p, sum_s))
    print("TOTAL pct=%.2f strictpct=%.2f" % (100.0*sum_p/sum_n, 100.0*sum_s/sum_n))

    # check delta entries
    print("\n=== delta entries check ===")
    drows = []
    for tag, path, verdict, ev in [("B1", B1, B1V, "SEMFIX_ENGFAM_B1/_audit/VERDICT.md"),
                                    ("B2", B2, B2V, "SEMFIX_ENGFAM_B2/_audit/VERDICT.md")]:
        dr = read_tsv(path)
        vr = read_tsv(verdict)
        print("%s delta rows=%d verdict rows=%d verdicts=%s" % (tag, len(dr), len(vr), dict(Counter(v[1] for v in vr))))
        vmap = {v[0]: v[1] for v in vr}
        for r in dr:
            e = r[0].strip().upper()
            assert re.fullmatch(r"[0-9A-F]{8}", e), "bad entry %s" % e
            assert vmap.get(e) == "PASS", "%s entry %s not PASS" % (tag, e)
            match = [c for c in cov if c[0].strip().upper() == e]
            assert len(match) == 1, "entry %s not unique in coverage (%d)" % (e, len(match))
            c = match[0]
            assert c[4] == "[已证]", "entry %s grade=%s" % (e, c[4])
            assert c[1] == "S17", "entry %s subsystem=%s" % (e, c[1])
            assert e in atlas_set, "entry %s not in atlas" % e
            drows.append((e, tag, r[3], ev))
    ents = [x[0] for x in drows]
    print("delta total=%d unique=%d" % (len(ents), len(set(ents))))
    assert len(ents) == 34 and len(set(ents)) == 34
    # unproven family of the 34
    up34 = [e for e in ents if UNPROVEN_RE.search([c for c in cov if c[0].strip().upper() == e][0][3])]
    print("34-row unproven-family hits=%d" % len(up34))
    print("all unproven rows are the 34? %s" % (set(x[0].strip().upper() for x in unproven_rows) == set(ents)))

    # dump json for later compare
    out = {
        "atlas_rows": atlas_rows, "cov_rows": len(cov),
        "proved_all": proved_all, "proved_in": proved_in, "proved_out": proved_out,
        "unproven_count": len(unproven_rows),
        "stats": {s: stats[s] for s in SYS},
        "sum22": {"n": sum_n, "proved": sum_p, "strict": sum_s},
        "delta_rows": [{"entry": e, "batch": t, "semantics": sem, "ev": ev} for e, t, sem, ev in drows],
    }
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "recompute.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nWROTE recompute.json")


if __name__ == "__main__":
    main()
