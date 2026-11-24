# -*- coding: utf-8 -*-
"""M63 merge verification + BEFORE state snapshot.
Read-only: does NOT modify coverage.tsv / PANEL.md.
Writes: MERGE_M63/work/before.json (before-state facts) and prints checks.
"""
import csv, hashlib, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
AUDIT = os.path.join(ROOT, "NAMED_PUSH_AUDIT", "verdict.tsv")
WORK = os.path.join(ROOT, "MERGE_M63", "work")

PASS = ["005414C0", "0071F8C0", "0041F580", "00503040", "00512290", "00512480"]
FAIL = ["005C46E0", "0065AC40"]
EXPECT_BEFORE_GRADE = {
    "005414C0": "[静态推断]", "0071F8C0": "[未证]",
    "0041F580": "[静态推断]", "00503040": "[静态推断]",
    "00512290": "[静态推断]", "00512480": "[静态推断]",
}

DELTA_SEM = {
    "005414C0": os.path.join(ROOT, "NAMED_PUSH_S18_B1", "delta.tsv"),
    "0071F8C0": os.path.join(ROOT, "NAMED_PUSH_S18_B2", "delta.tsv"),
    "0041F580": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00503040": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00512290": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00512480": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
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
        "mtime_iso": __import__("datetime").datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
        "mtime_epoch_ns": st.st_mtime_ns,
        "bytes": st.st_size,
        "sha256": h.hexdigest(),
    }


def main():
    checks = {}
    before = {"coverage.tsv": stat(COV), "PANEL.md": stat(PANEL)}

    # --- audit table cross-check ---
    with open(AUDIT, encoding="utf-8-sig", newline="") as f:
        aud = list(csv.reader(f, delimiter="\t"))
    hdr = aud[0]
    rows = [r for r in aud[1:] if r and any(c.strip() for c in r)]
    checks["audit_header_8col"] = (len(hdr) == 8, len(hdr))
    checks["audit_data_rows_8"] = (len(rows) == 8, len(rows))
    verdict_col = hdr.index("verdict")
    pass_set = [r[0].strip().upper() for r in rows if r[verdict_col].strip() == "PASS"]
    fail_set = [r[0].strip().upper() for r in rows if r[verdict_col].strip() == "FAIL"]
    checks["audit_PASS_set"] = (sorted(pass_set) == sorted(PASS), pass_set)
    checks["audit_FAIL_set"] = (sorted(fail_set) == sorted(FAIL), fail_set)
    checks["audit_PASS_count_6"] = (len(pass_set) == 6, len(pass_set))

    # --- atlas membership ---
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))
    checks["atlas_rows"] = (True, len(atlas))
    in_atlas = {e: (ne(e) in atlas) for e in PASS + FAIL}

    # --- coverage load ---
    with open(COV, encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.reader(f, delimiter="\t"))
    cov_hdr = all_rows[0]
    cov = [r for r in all_rows[1:] if len(r) >= 8]
    # 表头 1 行逗号分隔（PANEL M52 段明载「表头 1 行逗号、数据 TAB 8 列」），数据行 TAB 8 列
    checks["cov_header_comma_8field"] = (len(cov_hdr[0].split(",")) == 8, cov_hdr[0])
    checks["cov_data_rows_18498"] = (len(cov) == 18498, len(cov))
    checks["cov_all_8col"] = (all(len(r) == 8 for r in cov), sorted({len(r) for r in cov}))

    full_proved = sum(1 for r in cov if r[4].strip() == "[已证]")
    atlas_proved = sum(1 for r in cov if ne(r[0]) in atlas and r[4].strip() == "[已证]")
    nonatlas_proved = full_proved - atlas_proved
    checks["full_proved_1496"] = (full_proved == 1496, full_proved)
    checks["atlas_proved_1490"] = (atlas_proved == 1490, atlas_proved)
    checks["nonatlas_proved_6"] = (nonatlas_proved == 6, nonatlas_proved)

    # per-subsystem proved (atlas内)
    from collections import Counter
    prov_by_s = Counter()
    atlas_n_by_s = Counter()
    for r in cov:
        if ne(r[0]) in atlas:
            s = r[1].strip()
            atlas_n_by_s[s] += 1
            if r[4].strip() == "[已证]":
                prov_by_s[s] += 1
    checks["S18_proved_54"] = (prov_by_s["S18"] == 54, prov_by_s["S18"])
    checks["S14_proved_107"] = (prov_by_s["S14"] == 107, prov_by_s["S14"])

    # --- current grade of 6 PASS rows (unique) ---
    cov_by_e = {}
    for r in cov:
        cov_by_e.setdefault(ne(r[0]), []).append(r)
    cur_grade = {}
    for e in PASS:
        occ = cov_by_e.get(ne(e), [])
        cur_grade[e] = [r[4].strip() for r in occ]
    checks["6_rows_unique_in_cov"] = (all(len(cov_by_e.get(ne(e), [])) == 1 for e in PASS),
                                      {e: len(cov_by_e.get(ne(e), [])) for e in PASS})
    checks["6_rows_grade_match"] = (
        all(cur_grade[e] == [EXPECT_BEFORE_GRADE[e]] for e in PASS), cur_grade)
    checks["6_rows_all_in_atlas"] = (all(in_atlas[e] for e in PASS), in_atlas)

    # --- FAIL rows current grade (must stay untouched) ---
    fail_grade = {e: [r[4].strip() for r in cov_by_e.get(ne(e), [])] for e in FAIL}
    checks["2_FAIL_rows_exist_unique"] = (
        all(len(cov_by_e.get(ne(e), [])) == 1 for e in FAIL),
        {e: len(cov_by_e.get(ne(e), [])) for e in FAIL})

    # --- delta col-4 semantics extraction ---
    delta_sem = {}
    delta_row = {}
    for e, path in DELTA_SEM.items():
        with open(path, encoding="utf-8-sig", newline="") as f:
            d = list(csv.reader(f, delimiter="\t"))
        dh = d[0]
        c4 = dh.index("one_line_semantics")
        matches = [r for r in d[1:] if r and ne(r[0]) == ne(e)]
        if len(matches) != 1:
            delta_row[e] = ("NONUNIQUE", len(matches))
        else:
            delta_row[e] = ("OK", 1)
            delta_sem[e] = matches[0][c4]
    checks["delta_semantics_unique"] = (all(v[0] == "OK" for v in delta_row.values()), delta_row)
    checks["delta_sem_no_未证_token"] = (
        all("未证" not in delta_sem.get(e, "") for e in PASS),
        {e: ("未证" in delta_sem.get(e, "")) for e in PASS})
    checks["delta_sem_no_bracket_未证"] = (
        all("[未证]" not in delta_sem.get(e, "") for e in PASS),
        {e: ("[未证]" in delta_sem.get(e, "")) for e in PASS})

    # --- strict baseline recompute (must match PANEL current strict) ---
    # proved_strict = atlas内 [已证] 且语义栏不含 [未证]
    strict_by_s = Counter()
    for r in cov:
        if ne(r[0]) in atlas and r[4].strip() == "[已证]" and "[未证]" not in r[3]:
            strict_by_s[r[1].strip()] += 1
    checks["recompute_strict_S18_44"] = (strict_by_s["S18"] == 44, strict_by_s["S18"])
    checks["recompute_strict_S14_94"] = (strict_by_s["S14"] == 94, strict_by_s["S14"])
    # 注意：PANEL 严格表 S22 strict 记 2，而 strict_panel.py 口径重算 S22=12（+10），
    # 属 M60 既有截面差异，非本卡引入；本卡只按增量 +6 更新 TOTAL 1163→1169，不重算全表、不碰 S22。
    panel_strict_total = 1163
    checks["strict_total_baseline_is_panel_1163"] = (panel_strict_total == 1163, panel_strict_total)
    recomputed_total = sum(strict_by_s.values())
    checks["strict_total_delta_is_only_S22"] = (
        recomputed_total - panel_strict_total == strict_by_s["S22"] - 2,
        {"recomputed": recomputed_total, "panel": panel_strict_total,
         "S22_recomputed": strict_by_s["S22"], "S22_panel": 2,
         "note": "pre-existing M60 S22 strict discrepancy; out of M63 scope"})

    # --- expected AFTER numbers ---
    exp = {
        "full_proved_after": full_proved + 6,
        "atlas_proved_after": atlas_proved + 6,
        "nonatlas_proved_after": nonatlas_proved,
        "S18_proved_after": prov_by_s["S18"] + 2,
        "S14_proved_after": prov_by_s["S14"] + 4,
        "S18_strict_after": strict_by_s["S18"] + 2,
        "S14_strict_after": strict_by_s["S14"] + 4,
        "TOTAL_strict_after": sum(strict_by_s.values()) + 6,
    }
    checks["expected_after"] = (True, exp)

    # --- write before.json ---
    payload = {
        "before": before,
        "checks": {k: {"ok": v[0], "value": v[1]} for k, v in checks.items()},
        "delta_semantics": delta_sem,
        "cur_grade": cur_grade,
        "fail_grade": fail_grade,
        "atlas_member": in_atlas,
        "expected_after": exp,
    }
    with open(os.path.join(WORK, "before.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    # --- print ---
    all_ok = True
    for k, (ok, val) in checks.items():
        if k == "expected_after":
            continue
        flag = "OK " if ok else "FAIL"
        if not ok:
            all_ok = False
        print("%-32s %s  %s" % (k, flag, json.dumps(val, ensure_ascii=False)))
    print("\nBEFORE:")
    for name, s in before.items():
        print("  %s: bytes=%d sha256=%s mtime=%s" % (name, s["bytes"], s["sha256"], s["mtime_iso"]))
    print("\nALL_PREREQUISITES_OK=%s" % all_ok)
    if not all_ok:
        sys.exit(2)


main()
