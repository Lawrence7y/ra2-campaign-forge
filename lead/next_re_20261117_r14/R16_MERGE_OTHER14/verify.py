# -*- coding: utf-8 -*-
"""R16-MERGE-OTHER14 :: re-runnable verification of all 8 checks from the task.

Reads: live coverage.tsv / PANEL.md, pinned snapshots in own dir, delta.tsv,
       before_col4.json, before_state.json, after_state.json, preflight.json.
Writes ONLY into own dir (incl. strict_panel.py copy + its outputs).
All numbers are MEASURED from disk (pre = pin, post = live), never hardcoded.

Checks:
  ① strict prefix 14/14
  ② coverage byte-level reversibility (pin + before_col4 -> sha == before)
  ③ invariants 18498 / {8:18498} / 1654 / atlas-in 1648 / out 6
  ④ only 14 rows' col4 changed; cols 1/2/3/5/6/7/8 byte-identical; grade unchanged
  ⑤ caliber A/B measured before/after
  ⑥ PANEL reversibility (delete inserted 6-line M97 block -> sha == before)
  ⑦ 达标未翻转 (strict_panel.py -> nominal S15,S16,S17 / strict S17)
  ⑧ line endings not mixed
"""
import csv, os, sys, hashlib, json, collections, re, subprocess

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_OTHER14", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_OTHER14")
NROWS = 14

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
    pre = json.load(open(os.path.join(OUT, "preflight.json"), encoding="utf-8"))
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    entries = {norm_e(dr[0]) for dr in ddata}
    new4_by_e = {norm_e(dr[0]): dr[3] for dr in ddata}

    cov_b = open(COV, "rb").read()
    pan_b = open(PAN, "rb").read()
    pin_cov_b = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
    pin_pan_b = open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
    cov_lines, cov_rows, cov_ends_lf = split_rows(cov_b)
    pin_lines, pin_rows, pin_ends_lf = split_rows(pin_cov_b)
    pan_lines, _, pan_ends_lf = split_rows(pan_b)

    # ---------- ① strict prefix 14/14 ----------
    prefix_ok = 0
    prefix_detail = []
    for dr in ddata:
        e = norm_e(dr[0])
        cands = [r for r in cov_rows[1:] if norm_e(r[0]) == e]
        if len(cands) != 1:
            continue
        cur = cands[0]
        old4 = before4[e]
        if cur[3].startswith(old4) and len(cur[3]) > len(old4) and cur[3][len(old4):] == new4_by_e[e][len(old4):]:
            prefix_ok += 1
    check(prefix_ok == NROWS, "① 严格前缀 14/14",
          f"prefix_ok={prefix_ok}/{NROWS}")

    # ---------- ② byte-level reversibility (pin + before_col4) ----------
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
    rev_ok = (reverted == NROWS and append_exact == NROWS and
              sha(recon_b) == before["coverage.tsv"]["sha256"] and
              len(recon_b) == before["coverage.tsv"]["bytes"] and
              recon_b == pin_cov_b)
    check(rev_ok, "② coverage.tsv 逐字节还原性（pin+before_col4 自证）",
          f"reverted={reverted} append_exact={append_exact} recon sha={sha(recon_b)[:8]} "
          f"bytes={len(recon_b)} vs before {before['coverage.tsv']['sha256'][:8]} {before['coverage.tsv']['bytes']} "
          f"exact_pin={recon_b==pin_cov_b}")

    # ---------- ③ invariants ----------
    data = cov_rows[1:]
    n = len(data)
    col_dist = dict(collections.Counter(len(r) for r in data))
    atlas = load_atlas()
    proved_total = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]")
    proved_in = sum(1 for r in data if len(r) >= 5 and r[4].strip() == "[已证]" and norm_e(r[0]) in atlas)
    proved_out = proved_total - proved_in
    inv_ok = (n == 18498 and col_dist == {8: 18498} and proved_total == 1654 and
              proved_in == 1648 and proved_out == 6)
    check(inv_ok, "③ 不变量 18,498 / {8:18498} / [已证] 1,654 / atlas 内 1,648 / 外 6",
          f"n={n} coldist={col_dist} proved={proved_total} in={proved_in} out={proved_out}")

    # ---------- ④ only 14 rows' col4 changed; other cols byte-identical; grade unchanged ----------
    diff_e = []
    bad_other = []
    if len(cov_rows) == len(pin_rows):
        for cur, prev in zip(cov_rows, pin_rows):
            if cur != prev:
                diff_e.append(norm_e(cur[0]))
                if not all(cur[c] == prev[c] for c in [0, 1, 2, 4, 5, 6, 7]):
                    bad_other.append(norm_e(cur[0]))
                # grade is col index 4; assert unchanged vs pin explicitly
                if not (len(cur) >= 5 and len(prev) >= 5 and cur[4] == prev[4]):
                    bad_other.append(norm_e(cur[0]) + ":grade")
    only_ok = (len(cov_rows) == len(pin_rows) and set(diff_e) == entries and
               len(diff_e) == NROWS and not bad_other)
    check(only_ok, "④ 仅 14 行第 4 列变；第 1/2/3/5/6/7/8 列逐字节相同；grade 未变",
          f"diff_count={len(diff_e)} match14={set(diff_e)==entries} bad_other={bad_other} diff_e={sorted(diff_e)}")

    # ---------- ⑤ caliber A/B measured before/after ----------
    pin_data = pin_rows[1:]
    N_pre_A = sum(1 for r in pin_data if norm_e(r[0]) in entries and "④" in r[3])
    N_pre_B = sum(1 for r in pin_data if norm_e(r[0]) in entries and "④ 活表槽位见证" in r[3])
    N_A_pre = kou(pin_data, "④")
    N_B_pre = kou(pin_data, "④ 活表槽位见证")
    N_A_post = kou(data, "④")
    N_B_post = kou(data, "④ 活表槽位见证")
    N_new_witness = sum(1 for dr in ddata if "④ 活表槽位见证" in dr[3])
    five = {"N_pre_A": N_pre_A, "N_pre_B": N_pre_B,
            "N_A_pre": N_A_pre, "N_A_post": N_A_post, "net_A": N_A_post - N_A_pre,
            "N_B_pre": N_B_pre, "N_B_post_literal": N_B_post, "net_B_literal": N_B_post - N_B_pre,
            "N_new_witness": N_new_witness,
            "net_B_broad_if_all14": NROWS}
    five_ok = (N_pre_A == 0 and N_pre_B == 0 and
               N_A_post - N_A_pre == NROWS and
               N_B_post - N_B_pre == N_new_witness and
               N_A_post == after["six_post_expected"]["N_A_post"] and
               N_B_post == after["six_post_expected"]["N_B_post_literal"])
    check(five_ok, "⑤ 口径 A/B 自实测改前改后（A 预期 +14；B 字面 +12/宽口径 +14）",
          json.dumps(five, ensure_ascii=False) + " | lead_expected B+14 only under broad 'any ④ witness' interpretation")

    # ---------- ⑥ PANEL reversibility (delete inserted 6-line M97 block) ----------
    n_ins = after["insertion"]["inserted_line_count"]
    m97_idx = [i for i, l in enumerate(pan_lines) if "M97 补记" in l]
    rev_pan_ok = False
    detail = f"M97 count={len(m97_idx)}"
    if len(m97_idx) == 1:
        i = m97_idx[0]
        cand = pan_lines[:i] + pan_lines[i + n_ins:]
        rb = ("\n".join(cand) + "\n").encode("utf-8")
        rev_pan_ok = (sha(rb) == before["PANEL.md"]["sha256"] and
                      len(rb) == before["PANEL.md"]["bytes"] and
                      rb == pin_pan_b)
        m96_idx = [j for j, l in enumerate(pan_lines) if "M96 补记" in l]
        block_txt = "".join(pan_lines[i:i + n_ins])
        detail = (f"M97_at_0based={i} M96_at={m96_idx} after_M96={bool(m96_idx) and i==m96_idx[0]+5} "
                  f"n_ins={n_ins} insert_before_1based={i+1} rebuilt sha={sha(rb)[:8]} bytes={len(rb)} "
                  f"exact_pin={rb==pin_pan_b} block_has_4points={all(s in block_txt for s in ['122','B1','direct call','0x90','C3','3,944','375','389','210','222'])}")
    check(rev_pan_ok, "⑥ PANEL.md 还原性（删 6 行 M97 块）", detail)

    # ---------- ⑦ 达标未翻转 (strict_panel.py, output to own dir) ----------
    sp_src = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
    sp_dst = os.path.join(OUT, "strict_panel_other14.py")
    src = open(sp_src, encoding="utf-8").read()
    old_line = 'OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")'
    if old_line in src:
        src = src.replace(old_line, 'OUT  = r"' + OUT + '"')
    else:
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
    check(dod_ok, "⑦ 达标未翻转 (strict_panel.py)",
          f"名义=[{nom_s}] 严格=[{st_s}] (期望 S15,S16,S17 / S17); rc={res.returncode}")

    # ---------- ⑧ line endings not mixed ----------
    le_ok = (cov_b.count(b"\r\n") == 0 and pan_b.count(b"\r\n") == 0 and
             cov_ends_lf == before["coverage.tsv"]["ends_lf"] and
             pan_ends_lf == before["PANEL.md"]["ends_lf"] and
             cov_b.count(b"\n") == before["coverage.tsv"]["lf"] and
             pan_b.count(b"\n") == before["PANEL.md"]["lf"] + n_ins)
    check(le_ok, "⑧ 行尾不混用、LF/endsLF 一致",
          f"cov CRLF={cov_b.count(bytes([13,10]))} LF={cov_b.count(bytes([10]))} endsLF={cov_ends_lf} "
          f"(before LF={before['coverage.tsv']['lf']} endsLF={before['coverage.tsv']['ends_lf']}); "
          f"pan CRLF={pan_b.count(bytes([13,10]))} LF={pan_b.count(bytes([10]))} endsLF={pan_ends_lf} "
          f"(before LF={before['PANEL.md']['lf']}+{n_ins} endsLF={before['PANEL.md']['ends_lf']})")

    # ---------- write machine-readable result ----------
    summary = {
        "checks_results": RESULTS,
        "all_pass": all(r["pass"] for r in RESULTS),
        "five_measured": five,
        "coverage_before": before["coverage.tsv"], "coverage_after": after["coverage.tsv"],
        "panel_before": before["PANEL.md"], "panel_after": after["PANEL.md"],
        "dod_nominal": nom_s, "dod_strict": st_s,
    }
    with open(os.path.join(OUT, "verify_result.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== OVERALL:", "ALL PASS" if summary["all_pass"] else "SOME FAIL", "===")
    print("FIVE MEASURED:", json.dumps(five, ensure_ascii=False))
    if not summary["all_pass"]:
        sys.exit(3)


if __name__ == "__main__":
    main()
