# -*- coding: utf-8 -*-
"""M64 merge verification + BEFORE state snapshot (READ ONLY).
Writes: MERGE_M64/work/before.json. Does NOT touch coverage.tsv / PANEL.md.
"""
import csv, hashlib, json, os, sys, datetime
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
AUDIT = os.path.join(ROOT, "NAMED_PUSH_AUDIT2", "verdict.tsv")
WORK = os.path.join(ROOT, "MERGE_M64", "work")

PASS = ["00691EE0", "00691FA0", "006A4930", "006E87F0", "006E9140",
        "00410C30", "00414290", "0041CFE0", "00524D70", "005F9950"]
PROTECTED = {"006A48A0": "FAIL", "00748190": "UNAUDITED"}
DELTAS = {
    "00691EE0": "NAMED_PUSH_S14_B2", "00691FA0": "NAMED_PUSH_S14_B2",
    "006A4930": "NAMED_PUSH_S14_B2", "006E87F0": "NAMED_PUSH_S14_B2",
    "006E9140": "NAMED_PUSH_S14_B2",
    "00410C30": "NAMED_PUSH_S05_B1", "00414290": "NAMED_PUSH_S05_B1",
    "0041CFE0": "NAMED_PUSH_S05_B1",
    "00524D70": "NAMED_PUSH_S05_B2", "005F9950": "NAMED_PUSH_S05_B2",
}


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def stat(p):
    st = os.stat(p)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return {
        "path": p,
        "mtime_iso": datetime.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
        "mtime_epoch_ns": st.st_mtime_ns,
        "bytes": st.st_size,
        "sha256": h.hexdigest(),
    }


def main():
    checks = {}
    before = {"coverage.tsv": stat(COV), "PANEL.md": stat(PANEL)}

    # audit table
    with open(AUDIT, encoding="utf-8-sig", newline="") as f:
        aud = list(csv.reader(f, delimiter="\t"))
    hdr = aud[0]
    rows = [r for r in aud[1:] if r and any(c.strip() for c in r)]
    checks["audit_header_8col"] = (len(hdr) == 8, len(hdr))
    checks["audit_data_rows_11"] = (len(rows) == 11, len(rows))
    vcol = hdr.index("verdict")
    ecol = hdr.index("entry")
    scol = hdr.index("subsystem")
    pass_set = [r[ecol].strip().upper() for r in rows if r[vcol].strip() == "PASS"]
    fail_set = [r[ecol].strip().upper() for r in rows if r[vcol].strip() == "FAIL"]
    checks["audit_PASS_count_10"] = (len(pass_set) == 10, len(pass_set))
    checks["audit_PASS_set"] = (sorted(pass_set) == sorted(PASS), sorted(pass_set))
    checks["audit_FAIL_set"] = (fail_set == ["006A48A0"], fail_set)
    checks["00748190_not_in_audit"] = ("00748190" not in [r[ecol].strip().upper() for r in rows],
                                       "00748190" in [r[ecol].strip().upper() for r in rows])
    # subsystem mapping from audit for PASS rows
    aud_sub = {r[ecol].strip().upper(): r[scol].strip() for r in rows}
    checks["PASS_subsystem_map"] = ({e: aud_sub.get(e) for e in PASS},
                                    {e: aud_sub.get(e) for e in PASS})

    # atlas
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))
    checks["atlas_rows"] = (True, len(atlas))

    # coverage
    with open(COV, encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.reader(f, delimiter="\t"))
    cov_hdr = all_rows[0]
    cov = [r for r in all_rows[1:] if len(r) >= 8]
    checks["cov_header_comma_8field"] = (len(cov_hdr[0].split(",")) == 8, cov_hdr[0])
    checks["cov_data_rows_18498"] = (len(cov) == 18498, len(cov))
    checks["cov_all_8col"] = (all(len(r) == 8 for r in cov), sorted({len(r) for r in cov}))

    full_proved = sum(1 for r in cov if r[4].strip() == "[已证]")
    atlas_proved = sum(1 for r in cov if ne(r[0]) in atlas and r[4].strip() == "[已证]")
    nonatlas_proved = full_proved - atlas_proved
    checks["full_proved_1502"] = (full_proved == 1502, full_proved)
    checks["atlas_proved_1496"] = (atlas_proved == 1496, atlas_proved)
    checks["nonatlas_proved_6"] = (nonatlas_proved == 6, nonatlas_proved)

    prov_by_s = Counter()
    atlas_n_by_s = Counter()
    for r in cov:
        if ne(r[0]) in atlas:
            s = r[1].strip()
            atlas_n_by_s[s] += 1
            if r[4].strip() == "[已证]":
                prov_by_s[s] += 1
    checks["S18_proved_56"] = (prov_by_s["S18"] == 56, prov_by_s["S18"])
    checks["S14_proved_111"] = (prov_by_s["S14"] == 111, prov_by_s["S14"])
    checks["S05_proved_165"] = (prov_by_s["S05"] == 165, prov_by_s["S05"])

    # unique + grade of PASS rows
    cov_by_e = {}
    for r in cov:
        cov_by_e.setdefault(ne(r[0]), []).append(r)
    cur_grade = {e: [r[4].strip() for r in cov_by_e.get(ne(e), [])] for e in PASS}
    checks["PASS_unique_in_cov"] = (
        all(len(cov_by_e.get(ne(e), [])) == 1 for e in PASS),
        {e: len(cov_by_e.get(ne(e), [])) for e in PASS})
    checks["PASS_grade_all_static"] = (
        all(cur_grade[e] == ["[静态推断]"] for e in PASS), cur_grade)
    in_atlas = {e: (ne(e) in atlas) for e in PASS}
    checks["PASS_all_in_atlas"] = (all(in_atlas.values()), in_atlas)

    # protected rows
    prot_grade = {e: [r[4].strip() for r in cov_by_e.get(ne(e), [])] for e in PROTECTED}
    checks["protected_exist_unique"] = (
        all(len(cov_by_e.get(ne(e), [])) == 1 for e in PROTECTED),
        {e: len(cov_by_e.get(ne(e), [])) for e in PROTECTED})
    checks["protected_grade_static"] = (
        all(prot_grade[e] == ["[静态推断]"] for e in PROTECTED), prot_grade)

    # delta semantics col-4
    delta_sem = {}
    for e, ddir in DELTAS.items():
        path = os.path.join(ROOT, ddir, "delta.tsv")
        with open(path, encoding="utf-8-sig", newline="") as f:
            d = list(csv.reader(f, delimiter="\t"))
        dh = d[0]
        c4 = dh.index("one_line_semantics")
        matches = [r for r in d[1:] if r and ne(r[0]) == ne(e)]
        if len(matches) == 1:
            delta_sem[e] = matches[0][c4]
        else:
            delta_sem[e] = None
    checks["delta_semantics_unique"] = (
        all(v is not None for v in delta_sem.values()),
        {e: (v is not None) for e, v in delta_sem.items()})
    checks["delta_sem_no_未证_token"] = (
        all("未证" not in (delta_sem.get(e) or "") for e in PASS),
        {e: ("未证" in (delta_sem.get(e) or "")) for e in PASS})
    checks["delta_sem_no_bracket_未证"] = (
        all("[未证]" not in (delta_sem.get(e) or "") for e in PASS),
        {e: ("[未证]" in (delta_sem.get(e) or "")) for e in PASS})

    # strict recompute
    strict_by_s = Counter()
    for r in cov:
        if ne(r[0]) in atlas and r[4].strip() == "[已证]" and "[未证]" not in r[3]:
            strict_by_s[r[1].strip()] += 1
    checks["recompute_strict_S18_46"] = (strict_by_s["S18"] == 46, strict_by_s["S18"])
    checks["recompute_strict_S14_98"] = (strict_by_s["S14"] == 98, strict_by_s["S14"])
    checks["strict_total_recomputed"] = (True, sum(strict_by_s.values()))

    payload = {
        "before": before,
        "checks": {k: {"ok": v[0], "value": v[1]} for k, v in checks.items()},
        "delta_semantics": delta_sem,
        "cur_grade": cur_grade,
        "prot_grade": prot_grade,
        "atlas_member": in_atlas,
        "prov_by_s": dict(prov_by_s),
        "strict_by_s": dict(strict_by_s),
    }
    with open(os.path.join(WORK, "before.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    all_ok = True
    for k, v in checks.items():
        ok, val = v
        flag = "OK " if ok else "FAIL"
        if not ok:
            all_ok = False
        print("%-30s %s  %s" % (k, flag, json.dumps(val, ensure_ascii=False)))
    print("\nBEFORE:")
    for name, s in before.items():
        print("  %s: bytes=%d sha256=%s mtime=%s" % (name, s["bytes"], s["sha256"], s["mtime_iso"]))
    print("\nALL_PREREQUISITES_OK=%s" % all_ok)
    if not all_ok:
        sys.exit(2)


main()
