# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B3 :: re-runnable verification of all 9 checks from the card §4.

Reads only: coverage.tsv, PANEL.md, delta.tsv, before_col4.json, before_state.json,
            after_state.json (all in this output dir where relevant).
Writes only into this output dir.
"""
import csv, os, sys, hashlib, json, collections, re, math, subprocess

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B3", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B3")

RESULTS = []


def check(cond, name, detail=""):
    RESULTS.append({"check": name, "pass": bool(cond), "detail": detail})
    print(("PASS" if cond else "FAIL"), "-", name, ("| " + detail) if detail else "")
    return cond


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def read_rows(path):
    b = open(path, "rb").read()
    txt = b.decode("utf-8")
    lines = txt.split("\n")
    ends_lf = lines[-1] == ""
    if ends_lf:
        lines = lines[:-1]
    rows = [ln.split("\t") for ln in lines]
    return b, lines, rows, ends_lf


def norm_e(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def load_atlas():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(norm_e(p[0]))
    return atlas


def kou4(rows, substring):
    return sum(1 for r in rows if len(r) >= 5 and r[4].strip() == "[已证]" and substring in r[3])


def main():
    before = json.load(open(os.path.join(OUT, "before_state.json"), encoding="utf-8"))
    after = json.load(open(os.path.join(OUT, "after_state.json"), encoding="utf-8"))
    before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
    ddata = list(csv.reader(open(DELTA, encoding="utf-8-sig", newline=""), delimiter="\t"))[1:]

    cov_b, cov_lines, cov_rows, cov_ends_lf = read_rows(COV)
    pan_b, pan_lines, pan_rows_dummy, pan_ends_lf = read_rows(PAN)

    # ---------- CHECK 9: line endings ----------
    cov_crlf = cov_b.count(b"\r\n")
    pan_crlf = pan_b.count(b"\r\n")
    le_ok = (cov_crlf == 0 and pan_crlf == 0 and
             cov_ends_lf == before["coverage.tsv"]["ends_lf"] and
             pan_ends_lf == before["PANEL.md"]["ends_lf"] and
             cov_b.count(b"\n") == before["coverage.tsv"]["lf"] and
             pan_b.count(b"\n") == after["PANEL.md"]["lf"])
    check(le_ok, "9. 行尾不混用、LF 一致",
          f"cov CRLF={cov_crlf} LF={cov_b.count(chr(10).encode())} endsLF={cov_ends_lf}; "
          f"pan CRLF={pan_crlf} LF={pan_b.count(chr(10).encode())} endsLF={pan_ends_lf}")

    # ---------- CHECK 1: byte-level reversibility (coverage.tsv) ----------
    recon_rows = [list(r) for r in cov_rows]
    reverted = 0
    for r in recon_rows:
        e = norm_e(r[0])
        if e in before4 and r[3] != before4[e]:
            r[3] = before4[e]
            reverted += 1
    recon_b = "\n".join("\t".join(r) for r in recon_rows).encode("utf-8")
    rev_ok = (sha(recon_b) == before["coverage.tsv"]["sha256"] and len(recon_b) == before["coverage.tsv"]["bytes"])
    check(rev_ok, "1. coverage.tsv 逐字节还原性",
          f"reverted_rows={reverted}; recon sha={sha(recon_b)[:8]} bytes={len(recon_b)}; "
          f"expected {before['coverage.tsv']['sha256'][:8]} {before['coverage.tsv']['bytes']}")

    # ---------- CHECK 2: invariants ----------
    header = cov_rows[0]
    data = cov_rows[1:]
    n = len(data)
    col_dist = collections.Counter(len(r) for r in data)
    grades = collections.Counter(r[4].strip() for r in data if len(r) >= 5)
    atlas = load_atlas()
    proved_total = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]")
    proved_in = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in
    # 18 rows grade still [已证]
    entries18 = {norm_e(r[0]) for r in ddata}
    grade18 = all(any(len(r) >= 5 and norm_e(r[0]) == e and r[4].strip() == "[已证]" for r in data) for e in entries18)
    inv_ok = (n == 18498 and col_dist == {8: 18498} and proved_total == 1654 and
              proved_in == 1648 and proved_out == 6 and grade18)
    check(inv_ok, "2. 不变量 18498/{8:18498}/1654/1648/6/18行grade",
          f"n={n} coldist={dict(col_dist)} proved={proved_total} in={proved_in} out={proved_out} grade18={grade18}")

    # ---------- CHECK 3: only 18 rows' col4 changed ----------
    # Compare current data rows against reconstructed-before rows
    before_rows = [ln.split("\t") for ln in "\n".join("\t".join(r) for r in recon_rows).split("\n")]
    diff_entries = []
    bad_rows = []
    for cur, prev in zip(cov_rows, before_rows):
        if cur != prev:
            diff_e = norm_e(cur[0])
            diff_entries.append(diff_e)
            other_same = all(cur[c] == prev[c] for c in [0, 1, 2, 4, 5, 6, 7])
            if not other_same:
                bad_rows.append(diff_e)
    only_ok = (set(diff_entries) == entries18 and len(diff_entries) == 18 and not bad_rows)
    check(only_ok, "3. 仅 18 行第 4 列变化",
          f"diff_count={len(diff_entries)} diff_entries_match={set(diff_entries)==entries18} bad_other_cols={bad_rows}")

    # ---------- CHECK 4: strict prefix 18/18 ----------
    prefix_ok_count = 0
    others_ok_count = 0
    for dr in ddata:
        e = norm_e(dr[0])
        cands = [r for r in cov_rows[1:] if norm_e(r[0]) == e]
        assert len(cands) == 1
        cur = cands[0]
        old4 = before4[e]
        new4 = cur[3]
        if new4.startswith(old4) and len(new4) > len(old4):
            prefix_ok_count += 1
        if all(dr[c] == cur[c] for c in [0, 1, 2, 4, 5, 6, 7]):
            others_ok_count += 1
    check(prefix_ok_count == 18 and others_ok_count == 18, "4. 严格前缀 18/18 且其它列同 delta",
          f"prefix={prefix_ok_count}/18 others={others_ok_count}/18")

    # ---------- CHECK 5: six measured numbers ----------
    # Recompute from current disk (post) and from reconstructed before rows
    before_data = before_rows[1:]
    N_pre_A = sum(1 for r in before_data if norm_e(r[0]) in entries18 and "④" in r[3])
    N_pre_B = sum(1 for r in before_data if norm_e(r[0]) in entries18 and "④ 活表槽位见证" in r[3])
    N_A_pre = kou4(before_data, "④")
    N_A_post = kou4(data, "④")
    N_B_pre = kou4(before_data, "④ 活表槽位见证")
    N_B_post = kou4(data, "④ 活表槽位见证")
    six = {"N_pre_A": N_pre_A, "N_pre_B": N_pre_B, "N_A_pre": N_A_pre, "N_A_post": N_A_post,
           "N_B_pre": N_B_pre, "N_B_post": N_B_post}
    expected_six = {"N_pre_A": 16, "N_pre_B": 0, "N_A_pre": 354, "N_A_post": 356, "N_B_pre": 170, "N_B_post": 188}
    check(six == expected_six, "5. 六个实测数", json.dumps(six, ensure_ascii=False))

    # ---------- CHECK 6: §12.6 / §12.4 counts ----------
    s126_app = sum(r[3][len(before4[norm_e(r[0])]):].count("§12.6") for r in cov_rows[1:] if norm_e(r[0]) in entries18)
    s124_app = sum(r[3][len(before4[norm_e(r[0])]):].count("§12.4") for r in cov_rows[1:] if norm_e(r[0]) in entries18)
    s126_all = sum(1 for r in data if len(r) >= 4 and "§12.6" in r[3])
    s124_all = sum(1 for r in data if len(r) >= 4 and "§12.4" in r[3])
    s126_before = sum(1 for r in before_data if len(r) >= 4 and "§12.6" in r[3])
    s124_before = sum(1 for r in before_data if len(r) >= 4 and "§12.4" in r[3])
    check(s126_app == 18 and s124_app == 0 and s124_all == 0,
          "6. §12.6/§12.4 命中计数",
          f"append §12.6={s126_app} §12.4={s124_app}; whole-table post §12.6={s126_all} §12.4={s124_all}; "
          f"pre §12.6={s126_before} §12.4={s124_before}")

    # ---------- CHECK 7: PANEL.md reversibility ----------
    # PANEL.md ends with LF: split keeps a trailing '' element that MUST be preserved
    # on rejoin, otherwise the final LF is lost.
    pan_txt_now = pan_b.decode("utf-8")
    pan_lines_full = pan_txt_now.split("\n")  # trailing '' preserved
    m91_idx = [i for i, l in enumerate(pan_lines_full) if "M91 补记" in l]
    rev_pan_ok = False
    if len(m91_idx) == 1:
        i = m91_idx[0]
        cand = pan_lines_full[:i] + pan_lines_full[i+7:]
        rb = "\n".join(cand).encode("utf-8")
        rev_pan_ok = (sha(rb) == before["PANEL.md"]["sha256"] and len(rb) == before["PANEL.md"]["bytes"])
        pan_detail = f"m91_at_line={i} rebuilt sha={sha(rb)[:8]} bytes={len(rb)}"
    else:
        pan_detail = f"M91 marker count={len(m91_idx)}"
    check(rev_pan_ok, "7. PANEL.md 还原性（删 M91 块）", pan_detail)

    # ---------- CHECK 8: 达标未翻转 (strict_panel.py 口径, output to own dir) ----------
    sp_src = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
    sp_dst = os.path.join(OUT, "strict_panel_b3.py")
    src = open(sp_src, encoding="utf-8").read()
    src = src.replace('OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")',
                      'OUT  = r"' + OUT + '"')
    with open(sp_dst, "w", encoding="utf-8") as f:
        f.write(src)
    # run it, capture output
    res = subprocess.run([sys.executable, sp_dst], capture_output=True, text=True, encoding="utf-8")
    sp_out = res.stdout
    nom = re.search(r"名义达标:([^\n]*)", sp_out)
    strict = re.search(r"严格达标:([^\n]*)", sp_out)
    nom_s = nom.group(1).strip() if nom else ""
    strict_s = strict.group(1).strip() if strict else ""
    dod_ok = (nom_s == "S15,S16,S17" and strict_s == "S17")
    check(dod_ok, "8. 达标未翻转 (strict_panel.py)",
          f"名义=[{nom_s}] 严格=[{strict_s}] (期望 S15,S16,S17 / S17)")
    # save strict_panel output
    with open(os.path.join(OUT, "strict_panel_out.txt"), "w", encoding="utf-8") as f:
        f.write(sp_out)

    # ---------- write machine-readable result ----------
    summary = {
        "six_numbers": six,
        "verifications": RESULTS,
        "all_pass": all(r["pass"] for r in RESULTS),
        "coverage_before": before["coverage.tsv"],
        "coverage_after": after["coverage.tsv"],
        "panel_before": before["PANEL.md"],
        "panel_after": after["PANEL.md"],
        "dod_nominal": nom_s, "dod_strict": strict_s,
    }
    with open(os.path.join(OUT, "verify_result.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== OVERALL:", "ALL PASS" if summary["all_pass"] else "SOME FAIL", "===")


if __name__ == "__main__":
    main()
