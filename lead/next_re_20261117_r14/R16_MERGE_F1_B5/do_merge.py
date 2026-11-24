# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B5 :: merge 4 rows' 4th column + insert M93 disclosure.

Hard boundaries:
  - coverage.tsv: ONLY the 4th column (index 3) of the 4 B5 rows changes.
  - PANEL.md: ONLY one M93 disclosure block inserted immediately after M92.
  - No other file outside this output dir is written except these two targets.
  - No reverse engineering; col4 = pinned disk original col4 + appended delta segment.

OFF-BY-ONE DEFENSE (lesson from prior rounds):
  - Everything keyed by normalized entry + EXACT pinned before_col4 byte match.
  - New file built from the PIN, never from a re-derived positional index.
  - CONCURRENCY GUARD: live disk must byte-equal the pin, else abort before any write.
"""
import csv, os, sys, hashlib, json, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B5", "delta.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B5")


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


def split_lines(b):
    txt = b.decode("utf-8")
    lines = txt.split("\n")
    ends_lf = lines[-1] == ""
    if ends_lf:
        lines = lines[:-1]
    return lines, ends_lf


def pct(n, d):
    return f"{100.0 * n / d:.2f}"


def main():
    pin_cov = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
    pin_pan = open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
    before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
    pre = json.load(open(os.path.join(OUT, "preflight.json"), encoding="utf-8"))
    before = pre["before"]

    # ---- CONCURRENCY GUARD: live disk must still equal the pin ----
    live_cov = open(COV, "rb").read()
    live_pan = open(PAN, "rb").read()
    if live_cov != pin_cov or live_pan != pin_pan:
        raise SystemExit("ABORT: live disk diverged from pin (concurrent writer). "
                         "cov_equal=%s pan_equal=%s" % (live_cov == pin_cov, live_pan == pin_pan))

    # ---- delta ----
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    assert len(ddata) == 4 and all(len(dr) == 8 for dr in ddata)
    new4_by_entry = {norm_e(dr[0]): dr[3] for dr in ddata}
    other_by_entry = {norm_e(dr[0]): dr for dr in ddata}
    assert set(new4_by_entry) == set(before4), (set(new4_by_entry), set(before4))

    # ---- build new coverage FROM PIN, keyed by entry + exact before_col4 ----
    cov_lines, cov_ends_lf = split_lines(pin_cov)
    cov_rows = [ln.split("\t") for ln in cov_lines]
    changed = []
    for ri, r in enumerate(cov_rows):
        e = norm_e(r[0])
        if e not in before4:
            continue
        # EXACT byte match against pinned original col4 — off-by-one / wrong-row guard
        if r[3] != before4[e]:
            raise SystemExit("ABORT: pinned before_col4 mismatch at row %d entry %s" % (ri + 1, e))
        dr = other_by_entry[e]
        if not all(dr[c] == r[c] for c in [0, 1, 2, 4, 5, 6, 7]):
            raise SystemExit("ABORT: non-col4 column mismatch at row %d entry %s" % (ri + 1, e))
        new4 = new4_by_entry[e]
        if not (new4.startswith(before4[e]) and len(new4) > len(before4[e])):
            raise SystemExit("ABORT: strict-prefix fail at row %d entry %s" % (ri + 1, e))
        cov_rows[ri][3] = new4
        changed.append((ri + 1, e, len(before4[e]), len(new4)))
    if len(changed) != 4:
        raise SystemExit("ABORT: changed row count != 4 (%d)" % len(changed))

    new_cov_txt = "\n".join("\t".join(r) for r in cov_rows)
    if cov_ends_lf:
        new_cov_txt += "\n"
    new_cov_bytes = new_cov_txt.encode("utf-8")
    assert b"\r" not in new_cov_bytes

    # ---- M93 disclosure numbers, from MEASURED preflight values ----
    N_pre_A = pre["six_pre"]["N_pre_A"]
    N_pre_B = pre["six_pre"]["N_pre_B"]
    N_A_pre = pre["six_pre"]["N_A_pre"]
    N_B_pre = pre["six_pre"]["N_B_pre"]
    # post is derived from measured pre + exact arithmetic; verify.py re-measures post from disk.
    N_A_post = N_A_pre + (4 - N_pre_A)
    N_B_post = N_B_pre + (4 - N_pre_B)
    proved = 1654
    # Plain (non-f) strings for {{...}} placeholders: avoid f-string brace escaping entirely.
    SECRET_SITE = "0075EA3F"

    M93_LINES = [
        "> ✅ **M93 补记：F1（槽位-安装型）缺口行 ④ 成文 —— 批次 B5 并入 4 行**",
        r"> 本批 4 行取自 `R16_PROBE_4GAP\scan_F1_audit.tsv` 派生集合（`same_source=no` + `ring4_at` 解出装表指令 + 装表点体外 + 现盘 `[已证]` 且第 4 列无 `④ 活表槽位见证` + ③ 干净），派生命中 76 行，本批取第 73–76 行（收官批）。" ,
        r"> 异族审计（`R16_AUDIT_F1_B5\VERDICT.md`）判 **PASS 4 / FAIL 0 / 必改 0**，§B 8 项 × 4 = **32/32** 字节事实独立复算为真。",
        r"> **定表**：执行器所选活表经审计独立核「精确类一致者恰好 1 张」（本批 4/4 每行该地址在镜像 `.rdata/.data` 内 `dd` 命中数=1、只落进 1 张表的 1 个槽位，无需改选；`00772CD0`/`00772EB0` 同表 `007F73B8` 的 slot5/slot6 亦各只 1 张类一致），松/严双口径类一致均 4/4。",
        (f"> 数字（口径 A/B 实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{N_A_pre:,} / {proved:,}（{pct(N_A_pre,proved)}%）升至 {N_A_post:,} / {proved:,}（{pct(N_A_post,proved)}%）**，本批**净增 = {N_A_post} − {N_A_pre} = {N_A_post-N_A_pre} 行**，**不是 +4**：4 行里有 **{N_pre_A} 行**（`00763200`）改前第 4 列已含散文式 `④`（`④ {SECRET_SITE}…`，计数 1），故这 {N_pre_A} 行口径 A 不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{N_B_pre:,} / {proved:,}（{pct(N_B_pre,proved)}%）升至 {N_B_post:,} / {proved:,}（{pct(N_B_post,proved)}%）**（净增 {N_B_post-N_B_pre} 行）。"),
        r"> ⚠️ **已接受限制与 NIT（来自审计，不判 FAIL 但引用者须知情）**：① **同一格并存两条 `④`** —— 因 append-only 约束，`00763200` 追加后同一第 4 列里同时存在旧散文式 `④`（`④ 0075EA3F…`）与新 `④ 活表槽位见证`；审计已核新旧两条指向同一 vt=`007F6BF4` / site=`0075EA3F` / 宿主 `0075E950`、无矛盾（改前 `④` 计数 1 → 改后 2；审计核 188 行 witness 行 `④` 计数全部 ≥2、无一行是 1，本行 2 个合先例、非重复表述，算净增按「+1 成文形态」计），⇒ **下游若按「④ 条数」或子串分桶统计会被双计，必须按行去重**。② **同一安装事件服务两行（审计 NIT-1）** —— `00772CD0`（slot5）与 `00772EB0`（slot6）共用同一条安装指令 `00771E77`（同表 `007F73B8`、同宿主 `00771C70`）；两行在各自槽号上分别成立、互不争抢，但就「活表」而言是**同一个安装事件**，宜按「**2 行 / 1 安装事件**」记录，不要当成两条独立见证累加（该事实 `R14_COMMON §13.4:1454` 已披露，D-47(A) 下不构成 FAIL）。",
        r"> **76/76 收官**：五批合计 76 行（18+18+18+18+4），F1 缺口 ④ 成文全部兑现、无剩余可补，**无遗漏、无重叠**（B1∪B2∪B3∪B4∪B5 = 76 行派生基集）；**本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**。",
    ]

    # ---- build new PANEL from PIN: insert 7-line M93 block right after M92 block ----
    pan_lines, pan_ends_lf = split_lines(pin_pan)
    assert pan_ends_lf is True
    m92_idx = [i for i, l in enumerate(pan_lines) if "M92 补记" in l]
    assert len(m92_idx) == 1, m92_idx
    ins = None
    for i in range(m92_idx[0] + 1, len(pan_lines)):
        if pan_lines[i].startswith("> 📌 **M77 并表实算说明**"):
            ins = i
            break
    assert ins == m92_idx[0] + 7, ("unexpected M92 block length", m92_idx, ins)
    assert not any("M93 补记" in l for l in pan_lines)
    new_pan_lines = pan_lines[:ins] + M93_LINES + pan_lines[ins:]
    new_pan_txt = "\n".join(new_pan_lines) + "\n"
    new_pan_bytes = new_pan_txt.encode("utf-8")
    assert b"\r" not in new_pan_bytes

    # ---- DRY RUN: verify placeholder braces rendered literally before any write ----
    if os.environ.get("DRY_RUN") == "1":
        joined = "\n".join(M93_LINES)
        print("M93_LINES count:", len(M93_LINES))
        print("line4 rj4eogw7 occurrences:", M93_LINES[4].count("0075EA3F"))
        print("line4 SECRET repr:", repr(M93_LINES[4][M93_LINES[4].find("散文式"):M93_LINES[4].find("散文式")+60]))
        print("line5 rj4eogw7 occurrences:", M93_LINES[5].count("0075EA3F"))
        print("line5 cw2xrnxc occurrences:", M93_LINES[5].count("0075E950"))
        print("any single-brace SECRET leak:", bool(__import__('re').search(r'(?<!\{)\{SECRET_|SECRET_\w+\}(?!\})', joined)))
        print("--- rendered M93 block ---")
        for ln in M93_LINES:
            print(ln)
        print("DRY RUN - NO WRITE")
        return

    # ---- WRITE (only the two targets) ----
    with open(COV, "wb") as f:
        f.write(new_cov_bytes)
    with open(PAN, "wb") as f:
        f.write(new_pan_bytes)

    after = {
        "coverage.tsv": file_info(COV),
        "PANEL.md": file_info(PAN),
        "insertion": {"m92_line_index_0based": m92_idx[0], "insert_at_0based": ins,
                      "inserted_line_count": len(M93_LINES),
                      "insert_before_1based": ins + 1},
        "changed_rows": changed,
        "six_post_expected": {"N_A_post": N_A_post, "N_B_post": N_B_post},
    }
    with open(os.path.join(OUT, "after_state.json"), "w", encoding="utf-8") as f:
        json.dump(after, f, ensure_ascii=False, indent=2)

    print("MERGE DONE")
    print("coverage before sha/bytes:", before["coverage.tsv"]["sha256"][:8], before["coverage.tsv"]["bytes"])
    print("coverage after  sha/bytes:", after["coverage.tsv"]["sha256"][:8], after["coverage.tsv"]["bytes"])
    print("PANEL   before sha/bytes:", before["PANEL.md"]["sha256"][:8], before["PANEL.md"]["bytes"])
    print("PANEL   after  sha/bytes:", after["PANEL.md"]["sha256"][:8], after["PANEL.md"]["bytes"])
    print("insertion:", json.dumps(after["insertion"], ensure_ascii=False))
    print("changed rows (1-based line, entry, oldlen, newlen):")
    for c in changed:
        print("  ", c)
    print("six expected post: N_A_post=%d N_B_post=%d" % (N_A_post, N_B_post))


if __name__ == "__main__":
    main()
