# -*- coding: utf-8 -*-
"""Read-only pre-analysis for R16-MERGE-F1-B3.
Measures baseline state and all six口径 numbers from the CURRENT disk.
Writes only into this output directory.
"""
import csv, os, sys, hashlib, json, collections, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B3", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B3")
os.makedirs(OUT, exist_ok=True)


def file_info(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    bare_lf = b.count(b"\n") - crlf
    return {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest().upper(),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(),
        "lf": b.count(b"\n"),
        "crlf": crlf,
        "bare_lf": bare_lf,
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


def read_cov():
    raw = open(COV, "rb").read()
    txt = raw.decode("utf-8-sig")
    # splitlines keep structure; file uses LF only
    lines = txt.split("\n")
    # last element may be '' if ends with LF; coverage does NOT end with LF
    if lines and lines[-1] == "":
        lines = lines[:-1]
    rows = []
    for ln in lines:
        rows.append(ln.split("\t"))
    return raw, lines, rows


def main():
    cov_info = file_info(COV)
    pan_info = file_info(PAN)

    raw, lines, rows = read_cov()
    header = rows[0]
    data = rows[1:]

    # invariants
    n_data = len(data)
    col_dist = collections.Counter(len(r) for r in data)
    grade_counts = collections.Counter(r[4].strip() for r in data if len(r) >= 5)

    # atlas
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(norm_e(p[0]))

    proved_total = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]")
    proved_in = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in

    # delta
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        drows = list(csv.reader(f, delimiter="\t"))
    dheader = drows[0]
    ddata = drows[1:]
    assert len(ddata) == 18, len(ddata)

    # index disk rows by entry
    by_entry = {}
    for idx, r in enumerate(data):
        by_entry.setdefault(norm_e(r[0]), []).append((idx, r))

    # 6 numbers
    N_pre_A = 0
    N_pre_B = 0
    prechecks = []
    per_row = []
    for dr in ddata:
        assert len(dr) == 8, len(dr)
        e = norm_e(dr[0])
        hits = by_entry.get(e, [])
        assert len(hits) == 1, (e, len(hits))
        idx, r = hits[0]
        disk_col4 = r[3]
        delta_col4 = dr[3]

        if "④" in disk_col4:
            N_pre_A += 1
        if "④ 活表槽位见证" in disk_col4:
            N_pre_B += 1

        prefix_ok = delta_col4.startswith(disk_col4) and len(delta_col4) > len(disk_col4)
        others_ok = all(dr[c] == r[c] for c in [0, 1, 2, 4, 5, 6, 7])
        grade_ok = r[4].strip() == "[已证]"
        append = delta_col4[len(disk_col4):] if prefix_ok else ""
        s126 = append.count("§12.6")
        s124 = append.count("§12.4")
        prechecks.append(prefix_ok and others_ok and grade_ok)
        per_row.append({
            "entry": e, "line_idx": idx,
            "prefix_ok": prefix_ok, "others_ok": others_ok, "grade_ok": grade_ok,
            "append_len": len(append.encode("utf-8")),
            "s126": s126, "s124": s124,
            "old_has_four": "④" in disk_col4,
            "old_has_witness": "④ 活表槽位见证" in disk_col4,
            "old_col4": disk_col4, "new_col4": delta_col4,
            "name": r[2],
        })

    # whole-table 口径 A/B before
    def kou4(rows, substring):
        return sum(1 for r in rows if len(r) >= 5 and r[4].strip() == "[已证]" and substring in r[3])

    N_A_pre = kou4(data, "④")
    N_B_pre = kou4(data, "④ 活表槽位见证")

    # simulate post
    data_post = []
    for r in data:
        data_post.append(list(r))
    for pr in per_row:
        idx = pr["line_idx"]
        # find the delta row
        e = pr["entry"]
        dr = next(d for d in ddata if norm_e(d[0]) == e)
        data_post[idx][3] = dr[3]

    N_A_post = kou4(data_post, "④")
    N_B_post = kou4(data_post, "④ 活表槽位见证")

    # §12.6 / §12.4 counts whole table before/after (col4)
    s126_pre = sum(1 for r in data if len(r) >= 4 and "§12.6" in r[3])
    s124_pre = sum(1 for r in data if len(r) >= 4 and "§12.4" in r[3])
    s126_post = sum(1 for r in data_post if len(r) >= 4 and "§12.6" in r[3])
    s124_post = sum(1 for r in data_post if len(r) >= 4 and "§12.4" in r[3])

    result = {
        "cov_info": cov_info,
        "pan_info": pan_info,
        "header": header,
        "n_data": n_data,
        "col_dist": dict(col_dist),
        "grade_counts": dict(grade_counts),
        "proved_total": proved_total,
        "proved_in": proved_in,
        "proved_out": proved_out,
        "N_pre_A": N_pre_A,
        "N_pre_B": N_pre_B,
        "N_A_pre": N_A_pre,
        "N_A_post": N_A_post,
        "N_B_pre": N_B_pre,
        "N_B_post": N_B_post,
        "net_A": N_A_post - N_A_pre,
        "net_B": N_B_post - N_B_pre,
        "s126_pre": s126_pre, "s124_pre": s124_pre,
        "s126_post": s126_post, "s124_post": s124_post,
        "all_prechecks_ok": all(prechecks),
        "per_row": per_row,
    }

    with open(os.path.join(OUT, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    # console summary
    print("=== PRE-ANALYSIS (current disk) ===")
    print("cov:", cov_info)
    print("pan:", pan_info)
    print("n_data=", n_data, "col_dist=", dict(col_dist))
    print("grade_counts=", dict(grade_counts))
    print("proved total/in/out=", proved_total, proved_in, proved_out)
    print("N_pre_A=", N_pre_A, "N_pre_B=", N_pre_B)
    print("N_A_pre=", N_A_pre, "N_A_post=", N_A_post, "net=", N_A_post - N_A_pre)
    print("N_B_pre=", N_B_pre, "N_B_post=", N_B_post, "net=", N_B_post - N_B_pre)
    print("all_prechecks_ok=", all(prechecks))
    print("§12.6 pre/post=", s126_pre, s126_post, " §12.4 pre/post=", s124_pre, s124_post)
    print("--- per-row ④ status ---")
    for pr in per_row:
        print(pr["entry"], "old_four=", pr["old_has_four"], "old_witness=", pr["old_has_witness"],
              "prefix=", pr["prefix_ok"], "others=", pr["others_ok"], "grade=", pr["grade_ok"],
              "s126=", pr["s126"], "s124=", pr["s124"], "applen=", pr["append_len"])


if __name__ == "__main__":
    main()
