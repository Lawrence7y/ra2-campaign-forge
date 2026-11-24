# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B4 :: perform the merge of 18 rows' 4th column + insert M92 disclosure.

Hard boundaries:
  - coverage.tsv: ONLY the 4th column (index 3) of the 18 B4 rows changes.
  - PANEL.md: ONLY one M92 disclosure block is inserted, immediately after M91.
  - No other file outside this output dir is written except these two targets.
  - No reverse engineering; col4 = disk original col4 + appended delta segment.

OFF-BY-ONE DEFENSE (LESSON FROM B3):
  - Everything is keyed by normalized entry + EXACT pinned before_col4 match.
  - The new file is built from the PINNED bytes, never from a re-derived positional
    index. A row is changed only when entry matches AND row[3] == before_col4[entry]
    byte-for-byte. Any mismatch aborts before any write.
"""
import csv, os, sys, hashlib, json, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B4", "delta.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B4")


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
    assert len(ddata) == 18 and all(len(dr) == 8 for dr in ddata)
    new4_by_entry = {norm_e(dr[0]): dr[3] for dr in ddata}
    other_by_entry = {norm_e(dr[0]): dr for dr in ddata}
    assert set(new4_by_entry) == set(before4)

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
    if len(changed) != 18:
        raise SystemExit("ABORT: changed row count != 18 (%d)" % len(changed))

    new_cov_txt = "\n".join("\t".join(r) for r in cov_rows)
    if cov_ends_lf:
        new_cov_txt += "\n"
    new_cov_bytes = new_cov_txt.encode("utf-8")
    assert b"\r" not in new_cov_bytes

    # ---- build M92 disclosure (numbers are the ones measured in preflight) ----
    N_pre_A = pre["six_pre"]["N_pre_A"]
    N_A_pre = pre["six_pre"]["N_A_pre"]
    N_B_pre = pre["six_pre"]["N_B_pre"]
    N_A_post = N_A_pre + (18 - N_pre_A)
    N_B_post = N_B_pre + 18
    proved = 1654
    M92_LINES = [
        "> ✅ **M92 补记：F1（槽位-安装型）缺口行 ④ 成文 —— 批次 B4 并入 18 行**",
        r"> 本批 18 行取自 `R16_PROBE_4GAP\scan_F1_audit.tsv` 派生集合（`same_source=no` + `ring4_at` 解出装表指令 + 装表点体外 + 现盘 `[已证]` 且第 4 列无 `④ 活表槽位见证` + ③ 干净），派生命中 76 行，本批取第 55–72 行。",
        r"> 异族审计（`R16_AUDIT_F1_B4\VERDICT.md`）判 **PASS 18 / FAIL 0 / 必改 0**，§B 8 项 × 18 = **144/144** 字节事实独立复算为真。",
        r"> **定表**：执行器所选活表经审计独立核「精确类一致者恰好 1 张」（B4 类型：本批 18/18 每行该地址在镜像 `.rdata/.data` 内只出现 1 次、只落进 1 张表的 1 个槽位，**无同槽多表**；B1 类型 MouseClass::slot17 同槽 9 张、AnimClass::slot84 同槽 21 张的情况本批一次未出现，该类形态亦各只 1 张类一致），松/严双口径类一致均 18/18。",
        (f"> 数字（口径 A/B 实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{N_A_pre:,} / {proved:,}（{pct(N_A_pre,proved)}%）升至 {N_A_post:,} / {proved:,}（{pct(N_A_post,proved)}%）**，本批**净增 = {N_A_post} − {N_A_pre} = {N_A_post-N_A_pre} 行**，**不是 +18**：18 行里有 **{N_pre_A} 行**（`00749F30` / `0074BA30`）改前第 4 列已含 `④`（分别 2 个 / 1 个），故这 {N_pre_A} 行口径 A 不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{N_B_pre:,} / {proved:,}（{pct(N_B_pre,proved)}%）升至 {N_B_post:,} / {proved:,}（{pct(N_B_post,proved)}%）**（净增 {N_B_post-N_B_pre} 行）。"),
        "> ⚠️ **已接受限制与 NIT（来自审计，不判 FAIL 但引用者须知情）**：① **同一格并存两条 `④`** —— 因 append-only 约束，2 行（`00749F30` / `0074BA30`）追加后同一第 4 列里同时存在旧 `④` 表述与新 `④ 活表槽位见证`；审计已核新旧两条锚同一装表点（`00749434` / `0074AE6B`）、无矛盾，⇒ **下游若按「④ 条数」或子串分桶统计会被双计，必须按行去重**。② **本期 10 行本 entry 体内也装同一张表** —— ④ 采纳体外装表点（活性不靠自身见证），但 §12.3 意义上独立链只有体外那一条；审计点名本批 10 行（`0071CDA0` / `0071E1D0` / `0071F8C0` / `0071FA80` / `00726860` / `00726950` / `00727BF0` / `007281A0` / `0074BA30` / `0075E0C0`），而 `scan_F1_audit.tsv` 的 `n_install_inside_body` 系统性低估只报 4 行（审计 NIT-4），选择行为本身正确（10 行全避开体内写点）。③ **见证头 `::ctor` 一处（审计 NIT-1）** —— `0071F8C0` 的 ④ 见证头与升级句写作 `TEventClass::ctor` 而非 79 行先例一律的 `Class::slotN`；正文已给「槽 5 值=0071F8C0」且实测 `u32(vt+20)==0071F8C0` 为真，事实无误，但**下游按 `::slot(\\d+)` 解析会漏这 1 行**，引用者须知。",
        "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**。",
    ]

    # ---- build new PANEL from PIN: insert 7-line M92 block right after M91 block ----
    pan_lines, pan_ends_lf = split_lines(pin_pan)
    assert pan_ends_lf is True
    m91_idx = [i for i, l in enumerate(pan_lines) if "M91 补记" in l]
    assert len(m91_idx) == 1, m91_idx
    ins = None
    for i in range(m91_idx[0] + 1, len(pan_lines)):
        if pan_lines[i].startswith("> 📌 **M77 并表实算说明**"):
            ins = i
            break
    assert ins == m91_idx[0] + 7, ("unexpected M91 block length", m91_idx, ins)
    assert not any("M92 补记" in l for l in pan_lines)
    new_pan_lines = pan_lines[:ins] + M92_LINES + pan_lines[ins:]
    new_pan_txt = "\n".join(new_pan_lines) + "\n"
    new_pan_bytes = new_pan_txt.encode("utf-8")
    assert b"\r" not in new_pan_bytes

    # ---- WRITE (only the two targets) ----
    with open(COV, "wb") as f:
        f.write(new_cov_bytes)
    with open(PAN, "wb") as f:
        f.write(new_pan_bytes)

    after = {
        "coverage.tsv": file_info(COV),
        "PANEL.md": file_info(PAN),
        "insertion": {"m91_line_index_0based": m91_idx[0], "insert_at_0based": ins,
                      "inserted_line_count": len(M92_LINES),
                      "insert_before_1based": ins + 1},
        "changed_rows": changed,
        "six_post_expected": {"N_A_post": N_A_post, "N_B_post": N_B_post},
    }
    with open(os.path.join(OUT, "after_state.json"), "w", encoding="utf-8") as f:
        json.dump(after, f, ensure_ascii=False, indent=2)

    print("MERGE DONE")
    print("before:", json.dumps(before, ensure_ascii=False))
    print("after :", json.dumps(after, ensure_ascii=False))
    print("changed rows (1-based line, entry, oldlen, newlen):")
    for c in changed:
        print("  ", c)


if __name__ == "__main__":
    main()
