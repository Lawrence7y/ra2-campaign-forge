# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B4 :: PREFLIGHT (read targets, pin into own dir, validate, DO NOT WRITE targets).

Produces in own dir:
  _pin_coverage.tsv, _pin_PANEL.md   (byte-exact snapshots taken at open)
  before_state.json                   (mtime/bytes/sha256/lines + line-ending facts)
  before_col4.json                    (entry -> pinned original col4, byte-exact)
  preflight.json                      (delta validation + invariants + N_*_pre numbers)
"""
import csv, os, sys, hashlib, json, datetime, shutil, collections

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B4", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B4")
os.makedirs(OUT, exist_ok=True)


def file_info(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    return {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest().upper(),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(),
        "lines": lf + (0 if (len(b) > 0 and b[-1:] == b"\n") else 1),
        "lf": lf,
        "crlf": crlf,
        "bare_lf": lf - crlf,
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


def split_lines(b):
    """Return list of lines WITHOUT trailing empty element, plus ends_lf."""
    txt = b.decode("utf-8")
    lines = txt.split("\n")
    ends_lf = lines[-1] == ""
    if ends_lf:
        lines = lines[:-1]
    return lines, ends_lf


def load_atlas():
    s = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                s.add(norm_e(p[0]))
    return s


def main():
    # ---- BEFORE state from live disk ----
    before = {"coverage.tsv": file_info(COV), "PANEL.md": file_info(PAN)}
    print("BEFORE:", json.dumps(before, ensure_ascii=False))

    # ---- PIN byte-exact ----
    shutil.copyfile(COV, os.path.join(OUT, "_pin_coverage.tsv"))
    shutil.copyfile(PAN, os.path.join(OUT, "_pin_PANEL.md"))
    pin_cov_b = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
    pin_pan_b = open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
    assert pin_cov_b == open(COV, "rb").read(), "pin cov mismatch"
    assert pin_pan_b == open(PAN, "rb").read(), "pin pan mismatch"
    assert hashlib.sha256(pin_cov_b).hexdigest().upper() == before["coverage.tsv"]["sha256"]
    assert hashlib.sha256(pin_pan_b).hexdigest().upper() == before["PANEL.md"]["sha256"]

    # ---- parse pinned coverage ----
    cov_lines, cov_ends_lf = split_lines(pin_cov_b)
    cov_rows = [ln.split("\t") for ln in cov_lines]
    cov_header, cov_data = cov_rows[0], cov_rows[1:]
    assert cov_ends_lf is False, "coverage.tsv unexpectedly ends with LF"
    assert b"\r" not in pin_cov_b, "coverage.tsv has CR"

    # ---- parse delta ----
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    assert len(ddata) == 18, "delta must have 18 rows"
    assert all(len(dr) == 8 for dr in ddata)
    entries = [norm_e(dr[0]) for dr in ddata]
    assert len(set(entries)) == 18, "duplicate delta entry"

    # ---- index pinned disk rows by entry ----
    by_entry = {}
    for ri, r in enumerate(cov_rows):  # include header at ri=0
        by_entry.setdefault(norm_e(r[0]), []).append(ri)

    before4 = {}
    validation = []
    for dr, e in zip(ddata, entries):
        cands = by_entry.get(e, [])
        assert len(cands) == 1, ("entry not unique in pinned disk", e, len(cands))
        ri = cands[0]
        r = cov_rows[ri]
        old4 = r[3]
        new4 = dr[3]
        prefix_ok = new4.startswith(old4) and len(new4) > len(old4)
        others_ok = all(dr[c] == r[c] for c in [0, 1, 2, 4, 5, 6, 7])
        grade_ok = r[4].strip() == "[已证]"
        if not (prefix_ok and others_ok and grade_ok):
            raise SystemExit("PREFLIGHT FAIL for %s: prefix=%s others=%s grade=%s" %
                             (e, prefix_ok, others_ok, grade_ok))
        before4[e] = old4
        validation.append({"entry": e, "row_index_1based": ri + 1,
                           "old4_len": len(old4), "new4_len": len(new4),
                           "append_len": len(new4) - len(old4),
                           "old4_head": old4[:60], "new4_tail": new4[-80:]})

    # ---- invariants on pinned BEFORE state ----
    n = len(cov_data)
    col_dist = dict(collections.Counter(len(r) for r in cov_data))
    grades = collections.Counter(r[4].strip() for r in cov_data if len(r) >= 5)
    atlas = load_atlas()
    proved_total = sum(1 for r in cov_data if len(r) >= 5 and r[4].strip() == "[已证]")
    proved_in = sum(1 for r in cov_data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in
    entries18 = set(entries)
    grade18 = all(
        any(len(r) >= 5 and norm_e(r[0]) == e and r[4].strip() == "[已证]" for r in cov_data)
        for e in entries18)

    # ---- six measured numbers: PRE parts ----
    N_pre_A = sum(1 for r in cov_data if norm_e(r[0]) in entries18 and "④" in r[3])
    N_pre_B = sum(1 for r in cov_data if norm_e(r[0]) in entries18 and "④ 活表槽位见证" in r[3])
    N_A_pre = sum(1 for r in cov_data if len(r) >= 5 and r[4].strip() == "[已证]" and "④" in r[3])
    N_B_pre = sum(1 for r in cov_data if len(r) >= 5 and r[4].strip() == "[已证]" and "④ 活表槽位见证" in r[3])

    inv = {"data_rows": n, "col_dist": col_dist, "grades": dict(grades),
           "proved_total": proved_total, "proved_in_atlas": proved_in, "proved_out_atlas": proved_out,
           "grade18_ok": grade18,
           "invariants_hold": (n == 18498 and col_dist == {8: 18498} and proved_total == 1654 and
                               proved_in == 1648 and proved_out == 6 and grade18)}

    pre = {"N_pre_A": N_pre_A, "N_pre_B": N_pre_B,
           "N_A_pre": N_A_pre, "N_B_pre": N_B_pre}

    # ---- PANEL preflight: anchors ----
    pan_lines, pan_ends_lf = split_lines(pin_pan_b)
    m91_idx = [i for i, l in enumerate(pan_lines) if "M91 补记" in l]
    m92_existing = [i for i, l in enumerate(pan_lines) if "M92 补记" in l]
    m77_after_m91 = None
    if len(m91_idx) == 1:
        for i in range(m91_idx[0] + 1, len(pan_lines)):
            if pan_lines[i].startswith("> 📌 **M77 并表实算说明**"):
                m77_after_m91 = i
                break
    panel_anchor = {"m91_indices": m91_idx, "m92_existing": m92_existing,
                    "m77_after_m91": m77_after_m91,
                    "m91_block_len": (m77_after_m91 - m91_idx[0]) if (m91_idx and m77_after_m91) else None,
                    "ends_lf": pan_ends_lf,
                    "crlf": pin_pan_b.count(b"\r\n")}

    result = {"before": before, "pin_sha": {
                  "coverage.tsv": hashlib.sha256(pin_cov_b).hexdigest().upper(),
                  "PANEL.md": hashlib.sha256(pin_pan_b).hexdigest().upper()},
              "invariants": inv, "six_pre": pre, "delta_validation": validation,
              "panel_anchor": panel_anchor}

    for path, obj in [("before_state.json", before), ("before_col4.json", before4),
                      ("preflight.json", result)]:
        with open(os.path.join(OUT, path), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    print("INVARIANTS:", json.dumps(inv, ensure_ascii=False))
    print("SIX_PRE:", json.dumps(pre, ensure_ascii=False))
    print("PANEL_ANCHOR:", json.dumps(panel_anchor, ensure_ascii=False))
    print("DELTA validation rows:", len(validation),
          "append_len range:", min(v["append_len"] for v in validation), "-",
          max(v["append_len"] for v in validation))
    if not inv["invariants_hold"]:
        raise SystemExit("PREFLIGHT: invariants do not hold")
    if m92_existing:
        raise SystemExit("PREFLIGHT: M92 already present in PANEL.md")
    if len(m91_idx) != 1 or m77_after_m91 is None:
        raise SystemExit("PREFLIGHT: M91 insertion anchor not found uniquely")
    print("PREFLIGHT OK")


if __name__ == "__main__":
    main()
