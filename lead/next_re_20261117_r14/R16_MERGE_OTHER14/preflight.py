# -*- coding: utf-8 -*-
"""R16-MERGE-OTHER14 :: PREFLIGHT (read-only on targets, writes only own dir).

Measures the CURRENT live disk state byte-for-byte, pins both target files,
verifies baseline invariants, measures the caliber A/B numbers from the pin,
checks the 14 OTHER14 rows are still UNMERGED and delta's col4 is a strict
prefix of the pinned original col4 (off-by-one / wrong-row / concurrency guard).

M97 disclosure is inserted immediately after the M96 block in PANEL.md.
"""
import csv, os, sys, hashlib, json, datetime, collections

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_OTHER14", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_OTHER14")
NROWS = 14


def file_info(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    return {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest().upper(),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(),
        "lines": lf + (0 if (len(b) > 0 and b[-1:] == b"\n") else 1),
        "lf": lf, "crlf": crlf, "bare_lf": lf - crlf,
        "ends_lf": len(b) > 0 and b[-1:] == b"\n",
        "bom": b[:3] == b"\xef\xbb\xbf",
    }


def norm_e(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def split_rows(b):
    txt = b.decode("utf-8")
    lines = txt.split("\n")
    ends_lf = lines[-1] == ""
    if ends_lf:
        lines = lines[:-1]
    return lines, [ln.split("\t") for ln in lines], ends_lf


def kou(rows, substring):
    return sum(1 for r in rows if len(r) >= 5 and r[4].strip() == "[已证]" and substring in r[3])


def main():
    cov_b = open(COV, "rb").read()
    pan_b = open(PAN, "rb").read()
    before = {"coverage.tsv": file_info(COV), "PANEL.md": file_info(PAN)}

    # PIN byte-for-byte copies into own dir
    open(os.path.join(OUT, "_pin_coverage.tsv"), "wb").write(cov_b)
    open(os.path.join(OUT, "_pin_PANEL.md"), "wb").write(pan_b)

    cov_lines, cov_rows, cov_ends_lf = split_rows(cov_b)
    pan_lines, _, pan_ends_lf = split_rows(pan_b)

    # ---- delta ----
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    assert len(ddata) == NROWS and all(len(dr) == 8 for dr in ddata), "delta must be 14 rows x 8 cols"
    entries = [norm_e(dr[0]) for dr in ddata]
    expect_entries = ["0040BC10", "0040F8F0", "0040FEC0", "00422CA0", "0046B910",
                      "0048AFD0", "0048B020", "004AF540", "004B5AB0", "0054EBA0",
                      "0062B380", "0065BED0", "0065C200", "0075E510"]
    assert entries == expect_entries, (entries, expect_entries)
    new4_by_e = {norm_e(dr[0]): dr[3] for dr in ddata}
    dr_by_e = {norm_e(dr[0]): dr for dr in ddata}

    # ---- baseline invariants from PIN ----
    data = cov_rows[1:]
    n = len(data)
    col_dist = dict(collections.Counter(len(r) for r in data))
    proved_total = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]")

    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(norm_e(p[0]))
    proved_in = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in

    inv = {"n": n, "col_dist": col_dist, "proved_total": proved_total,
           "proved_in": proved_in, "proved_out": proved_out,
           "atlas_file": ATLAS, "atlas_size": len(atlas)}

    # ---- caliber numbers, MEASURED from pin ----
    # A = [已证] & 第4列含字面 '④'; B = [已证] & 第4列含字面 '④ 活表槽位见证'
    N_pre_A = sum(1 for r in data if norm_e(r[0]) in entries and "④" in r[3])
    N_pre_B = sum(1 for r in data if norm_e(r[0]) in entries and "④ 活表槽位见证" in r[3])
    # among the delta's NEW col4, how many carry each literal marker
    N_new_ring4 = sum(1 for dr in ddata if "④" in dr[3])
    N_new_witness = sum(1 for dr in ddata if "④ 活表槽位见证" in dr[3])
    N_new_directcall = sum(1 for dr in ddata if "④ direct call" in dr[3])
    N_A_pre = kou(data, "④")
    N_B_pre = kou(data, "④ 活表槽位见证")
    six_pre = {
        "N_pre_A": N_pre_A, "N_pre_B": N_pre_B,
        "N_new_ring4": N_new_ring4, "N_new_witness": N_new_witness, "N_new_directcall": N_new_directcall,
        "N_A_pre": N_A_pre, "N_B_pre": N_B_pre,
        "N_A_post_expected": N_A_pre + (NROWS - N_pre_A),
        "N_B_post_expected_literal": N_B_pre + (N_new_witness - N_pre_B),
        "N_B_post_expected_broad": N_B_pre + (NROWS - N_pre_B),
    }

    # ---- per-row checks against PIN (off-by-one / wrong-row / concurrency guard) ----
    before4 = {}
    row_report = []
    loc = {}
    for ri, r in enumerate(cov_rows):
        e = norm_e(r[0])
        if e in entries:
            loc.setdefault(e, []).append((ri + 1, r))
    hard_fail = []
    for e in entries:
        if e not in loc or len(loc[e]) != 1:
            hard_fail.append("entry %s located %d times (need exactly 1)" % (e, len(loc.get(e, []))))
            continue
        lineno, r = loc[e][0]
        orig4 = r[3]
        before4[e] = orig4
        dr = dr_by_e[e]
        new4 = new4_by_e[e]
        witness_pre = "④ 活表槽位见证" in orig4
        ring4_pre = "④" in orig4
        grade_ok = (len(r) >= 5 and r[4].strip() == "[已证]")
        prefix = new4.startswith(orig4) and len(new4) > len(orig4)
        other_cols_ok = all(dr[c] == r[c] for c in [0, 1, 2, 4, 5, 6, 7])
        circled_count_pre = orig4.count("④")
        row_report.append({"entry": e, "pin_line_1based": lineno,
                           "grade_ok": grade_ok, "witness_pre": witness_pre, "ring4_pre": ring4_pre,
                           "strict_prefix": prefix, "other_cols_ok": other_cols_ok,
                           "circled_count_pre": circled_count_pre,
                           "orig4_len": len(orig4), "new4_len": len(new4),
                           "orig4_preview": orig4[:110]})
        if ring4_pre:
            hard_fail.append("%s ALREADY has ④ in pin col4 (not a true no-④ row)" % e)
        if not grade_ok:
            hard_fail.append("%s grade != [已证]" % e)
        if not prefix:
            hard_fail.append("%s strict-prefix FAIL (concurrent write / wrong row)" % e)
        if not other_cols_ok:
            hard_fail.append("%s other-column byte mismatch vs delta" % e)

    # ---- PANEL structure: M96 exists once, M97 absent, locate insertion point ----
    m96_idx = [i for i, l in enumerate(pan_lines) if "M96 补记" in l]
    m97_idx = [i for i, l in enumerate(pan_lines) if "M97 补记" in l]
    pan_struct = {"m96_idx_0based": m96_idx, "m97_idx_0based": m97_idx,
                  "pan_ends_lf": pan_ends_lf}
    ins = None
    if len(m96_idx) == 1:
        for i in range(m96_idx[0] + 1, len(pan_lines)):
            if pan_lines[i].startswith("> 📌 **M77 并表实算说明**"):
                ins = i
                break
    # M96 block = header(L279) + 4 body lines (L280-283) => next marker at L284(0based283)
    pan_struct["insert_at_0based"] = ins
    pan_struct["expected_ins"] = (m96_idx[0] + 5) if len(m96_idx) == 1 else None
    pan_struct["block_after_m96"] = (pan_lines[m96_idx[0]:m96_idx[0]+5] if len(m96_idx) == 1 else None)
    if len(m96_idx) != 1:
        hard_fail.append("PANEL M96 count != 1: %s" % m96_idx)
    if m97_idx:
        hard_fail.append("PANEL already contains M97 block: %s" % m97_idx)
    if ins != pan_struct["expected_ins"]:
        hard_fail.append("PANEL insertion point %s != expected %s" % (ins, pan_struct["expected_ins"]))

    # ---- baseline invariant assertions (from task) ----
    if not (n == 18498 and col_dist == {8: 18498} and proved_total == 1654 and
            proved_in == 1648 and proved_out == 6):
        hard_fail.append("baseline invariant mismatch: %s" % inv)

    preflight = {
        "before": before, "inv": inv, "six_pre": six_pre,
        "row_report": row_report,
        "pan_struct": pan_struct,
        "hard_fail": hard_fail,
        "cov_ends_lf": cov_ends_lf, "pan_ends_lf": pan_ends_lf,
    }
    json.dump(preflight, open(os.path.join(OUT, "preflight.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(before4, open(os.path.join(OUT, "before_col4.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(before, open(os.path.join(OUT, "before_state.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("=== PREFLIGHT ===")
    print("coverage before:", json.dumps(before["coverage.tsv"], ensure_ascii=False))
    print("PANEL   before:", json.dumps(before["PANEL.md"], ensure_ascii=False))
    print("inv:", json.dumps(inv, ensure_ascii=False))
    print("six_pre:", json.dumps(six_pre, ensure_ascii=False))
    print("pan_struct:", json.dumps(pan_struct, ensure_ascii=False))
    print("row_report:")
    for rr in row_report:
        print("  ", json.dumps(rr, ensure_ascii=False))
    print("HARD_FAIL:", json.dumps(hard_fail, ensure_ascii=False))
    if hard_fail:
        print("!!! PREFLIGHT FAILED — DO NOT MERGE !!!")
        sys.exit(2)
    print("PREFLIGHT OK")


if __name__ == "__main__":
    main()
