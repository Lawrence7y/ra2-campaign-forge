# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B4 :: re-runnable verification of all 9 checks from card §4.

Reads: live coverage.tsv / PANEL.md, pinned snapshots in own dir, delta.tsv,
       before_col4.json, before_state.json, after_state.json.
Writes ONLY into own dir.
Six numbers are MEASURED from disk (before = pin, after = live), never hardcoded.
"""
import csv, os, sys, hashlib, json, collections, re, subprocess

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B4", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B4")

RESULTS = []


def check(cond, name, detail=""):
    RESULTS.append({"check": name, "pass": bool(cond), "detail": detail})
    print(("PASS" if cond else "FAIL"), "-", name, ("| " + detail) if detail else "")
    return cond


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def split_rows(b):
    txt = b.decode("utf-8")
    lines = txt.split("\n")
    ends_lf = lines[-1] == ""
    if ends_lf:
        lines = lines[:-1]
    return lines, [ln.split("\t") for ln in lines], ends_lf


def norm_e(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


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


def kou(rows, substring):
    return sum(1 for r in rows if len(r) >= 5 and r[4].strip() == "[已证]" and substring in r[3])


def main():
    before = json.load(open(os.path.join(OUT, "before_state.json"), encoding="utf-8"))
    after = json.load(open(os.path.join(OUT, "after_state.json"), encoding="utf-8"))
    before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    entries18 = {norm_e(dr[0]) for dr in ddata}
    new4_by_e = {norm_e(dr[0]): dr[3] for dr in ddata}

    cov_b = open(COV, "rb").read()
    pan_b = open(PAN, "rb").read()
    pin_cov_b = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
    pin_pan_b = open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
    cov_lines, cov_rows, cov_ends_lf = split_rows(cov_b)
    pin_lines, pin_rows, pin_ends_lf = split_rows(pin_cov_b)
    pan_lines, _, pan_ends_lf = split_rows(pan_b)

    # ---------- CHECK 1: byte-level reversibility (coverage.tsv) vs PIN ----------
    # Revert col4 for exactly the 18 entries; require current col4 == before4+delta-append.
    recon = [list(r) for r in cov_rows]
    reverted = 0
    append_exact = 0
    for r in recon:
        e = norm_e(r[0])
        if e not in before4:
            continue
        old4 = before4[e]
        if r[3].startswith(old4):
            append_exact += 1
        r[3] = old4
        reverted += 1
    recon_b = ("\n".join("\t".join(r) for r in recon) + ("\n" if cov_ends_lf else "")).encode("utf-8")
    rev_ok = (reverted == 18 and append_exact == 18 and
              sha(recon_b) == before["coverage.tsv"]["sha256"] and
              len(recon_b) == before["coverage.tsv"]["bytes"])
    check(rev_ok, "1. coverage.tsv 逐字节还原性（对照 pin）",
          f"reverted={reverted} append_exact={append_exact} recon sha={sha(recon_b)[:8]} "
          f"bytes={len(recon_b)} expected {before['coverage.tsv']['sha256'][:8]} {before['coverage.tsv']['bytes']}")

    # ---------- CHECK 2: invariants ----------
    data = cov_rows[1:]
    n = len(data)
    col_dist = dict(collections.Counter(len(r) for r in data))
    atlas = load_atlas()
    proved_total = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]")
    proved_in = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in
    grade18 = all(any(len(r) >= 5 and norm_e(r[0]) == e and r[4].strip() == "[已证]" for r in data)
                  for e in entries18)
    inv_ok = (n == 18498 and col_dist == {8: 18498} and proved_total == 1654 and
              proved_in == 1648 and proved_out == 6 and grade18)
    check(inv_ok, "2. 不变量 18498/{8:18498}/1654/1648/6/18行grade",
          f"n={n} coldist={col_dist} proved={proved_total} in={proved_in} out={proved_out} grade18={grade18}")

    # ---------- CHECK 3: only 18 rows' col4 changed (vs PIN) ----------
    diff_e = []
    bad_other = []
    if len(cov_rows) == len(pin_rows):
        for cur, prev in zip(cov_rows, pin_rows):
            if cur != prev:
                diff_e.append(norm_e(cur[0]))
                if not all(cur[c] == prev[c] for c in [0, 1, 2, 4, 5, 6, 7]):
                    bad_other.append(norm_e(cur[0]))
    only_ok = (len(cov_rows) == len(pin_rows) and set(diff_e) == entries18 and
               len(diff_e) == 18 and not bad_other)
    check(only_ok, "3. 仅 18 行第 4 列变化（对照 pin）",
          f"diff_count={len(diff_e)} match18={set(diff_e)==entries18} bad_other={bad_other}")

    # ---------- CHECK 4: strict prefix 18/18 + other cols match delta ----------
    prefix_ok = 0
    others_ok = 0
    append_exact2 = 0
    for dr in ddata:
        e = norm_e(dr[0])
        cands = [r for r in cov_rows[1:] if norm_e(r[0]) == e]
        if len(cands) != 1:
            continue
        cur = cands[0]
        old4 = before4[e]
        if cur[3].startswith(old4) and len(cur[3]) > len(old4):
            prefix_ok += 1
        if all(dr[c] == cur[c] for c in [0, 1, 2, 4, 5, 6, 7]):
            others_ok += 1
        if cur[3][len(old4):] == dr[3][len(old4):]:
            append_exact2 += 1
    check(prefix_ok == 18 and others_ok == 18 and append_exact2 == 18,
          "4. 严格前缀 18/18 且其它列同 delta 且追加段逐字",
          f"prefix={prefix_ok}/18 others={others_ok}/18 append_exact={append_exact2}/18")

    # ---------- CHECK 5: six MEASURED numbers ----------
    pin_data = pin_rows[1:]
    N_pre_A = sum(1 for r in pin_data if norm_e(r[0]) in entries18 and "④" in r[3])
    N_pre_B = sum(1 for r in pin_data if norm_e(r[0]) in entries18 and "④ 活表槽位见证" in r[3])
    N_A_pre = kou(pin_data, "④")
    N_B_pre = kou(pin_data, "④ 活表槽位见证")
    N_A_post = kou(data, "④")
    N_B_post = kou(data, "④ 活表槽位见证")
    six = {"N_pre_A": N_pre_A, "N_pre_B": N_pre_B,
           "N_A_pre": N_A_pre, "N_A_post": N_A_post,
           "N_B_pre": N_B_pre, "N_B_post": N_B_post}
    consistent = (N_pre_B == 0 and
                  N_A_post - N_A_pre == 18 - N_pre_A and
                  N_B_post - N_B_pre == 18 - N_pre_B and
                  N_A_post == after["six_post_expected"]["N_A_post"] and
                  N_B_post == after["six_post_expected"]["N_B_post"])
    check(consistent, "5. 六个实测数（自算，非照抄）", json.dumps(six, ensure_ascii=False))

    # ---------- CHECK 6: §12.6 / §12.4 hit counts ----------
    s126_app = sum(r[3][len(before4[norm_e(r[0])]):].count("§12.6")
                   for r in cov_rows[1:] if norm_e(r[0]) in entries18)
    s124_app = sum(r[3][len(before4[norm_e(r[0])]):].count("§12.4")
                   for r in cov_rows[1:] if norm_e(r[0]) in entries18)
    s126_all = sum(1 for r in data if len(r) >= 4 and "§12.6" in r[3])
    s124_all = sum(1 for r in data if len(r) >= 4 and "§12.4" in r[3])
    s126_pre = sum(1 for r in pin_data if len(r) >= 4 and "§12.6" in r[3])
    s124_pre = sum(1 for r in pin_data if len(r) >= 4 and "§12.4" in r[3])
    check(s126_app == 18 and s124_app == 0 and s124_all == 0,
          "6. §12.6/§12.4 命中计数",
          f"append §12.6={s126_app} §12.4={s124_app}; post §12.6={s126_all} §12.4={s124_all}; "
          f"pre §12.6={s126_pre} §12.4={s124_pre}")

    # ---------- CHECK 7: PANEL.md reversibility (delete inserted 7 lines) ----------
    # PANEL.md ends with LF: split_rows strips the trailing '' — rebuild with +'\n'
    m92_idx = [i for i, l in enumerate(pan_lines) if "M92 补记" in l]
    rev_pan_ok = False
    detail = f"M92 count={len(m92_idx)}"
    if len(m92_idx) == 1:
        i = m92_idx[0]
        cand = pan_lines[:i] + pan_lines[i + 7:]
        rb = ("\n".join(cand) + "\n").encode("utf-8")
        rev_pan_ok = (sha(rb) == before["PANEL.md"]["sha256"] and
                      len(rb) == before["PANEL.md"]["bytes"])
        # also verify insertion point = right after M91 block (M91+7 == M92 index)
        m91_idx = [j for j, l in enumerate(pan_lines) if "M91 补记" in l]
        detail = (f"M92_at_0based={i} M91_at={m91_idx} after_M91={m91_idx and i==m91_idx[0]+7} "
                  f"rebuilt sha={sha(rb)[:8]} bytes={len(rb)}")
    check(rev_pan_ok, "7. PANEL.md 还原性（删 M92 块）", detail)

    # ---------- CHECK 8: 达标未翻转 (strict_panel.py, output to own dir) ----------
    sp_src = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
    sp_dst = os.path.join(OUT, "strict_panel_b4.py")
    src = open(sp_src, encoding="utf-8").read()
    old_line = 'OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")'
    if old_line in src:
        src = src.replace(old_line, 'OUT  = r"' + OUT + '"')
    else:
        # fallback: replace any OUT assignment line ending in work
        src = re.sub(r'(?m)^OUT\s*=.*$', 'OUT  = r"' + OUT + '"', src, count=1)
    with open(sp_dst, "w", encoding="utf-8") as f:
        f.write(src)
    res = subprocess.run([sys.executable, sp_dst], capture_output=True, text=True, encoding="utf-8")
    sp_out = res.stdout
    with open(os.path.join(OUT, "strict_panel_out.txt"), "w", encoding="utf-8") as f:
        f.write(sp_out)
    nom = re.search(r"名义达标:([^\n]*)", sp_out)
    st = re.search(r"严格达标:([^\n]*)", sp_out)
    nom_s = nom.group(1).strip() if nom else ""
    st_s = st.group(1).strip() if st else ""
    dod_ok = (nom_s == "S15,S16,S17" and st_s == "S17")
    check(dod_ok, "8. 达标未翻转 (strict_panel.py)",
          f"名义=[{nom_s}] 严格=[{st_s}] (期望 S15,S16,S17 / S17); rc={res.returncode}")

    # ---------- CHECK 9: line endings unchanged ----------
    le_ok = (cov_b.count(b"\r\n") == 0 and pan_b.count(b"\r\n") == 0 and
             cov_ends_lf == before["coverage.tsv"]["ends_lf"] and
             pan_ends_lf == before["PANEL.md"]["ends_lf"] and
             cov_b.count(b"\n") == before["coverage.tsv"]["lf"] and
             pan_b.count(b"\n") == after["PANEL.md"]["lf"])
    check(le_ok, "9. 行尾不混用、LF/endsLF 一致",
          f"cov CRLF={cov_b.count(bytes([13,10]))} LF={cov_b.count(bytes([10]))} endsLF={cov_ends_lf}; "
          f"pan CRLF={pan_b.count(bytes([13,10]))} LF={pan_b.count(bytes([10]))} endsLF={pan_ends_lf}")

    # ---------- write machine-readable result ----------
    summary = {
        "six_measured": six,
        "six_arithmetic": {
            "net_A": N_A_post - N_A_pre, "expected_net_A": 18 - N_pre_A,
            "net_B": N_B_post - N_B_pre, "expected_net_B": 18 - N_pre_B,
        },
        "verifications": RESULTS,
        "all_pass": all(r["pass"] for r in RESULTS),
        "coverage_before": before["coverage.tsv"], "coverage_after": after["coverage.tsv"],
        "panel_before": before["PANEL.md"], "panel_after": after["PANEL.md"],
        "dod_nominal": nom_s, "dod_strict": st_s,
    }
    with open(os.path.join(OUT, "verify_result.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== OVERALL:", "ALL PASS" if summary["all_pass"] else "SOME FAIL", "===")
    print("SIX MEASURED:", json.dumps(six, ensure_ascii=False))


if __name__ == "__main__":
    main()
