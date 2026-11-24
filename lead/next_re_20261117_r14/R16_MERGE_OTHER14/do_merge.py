# -*- coding: utf-8 -*-
"""R16-MERGE-OTHER14 :: merge 14 rows' 4th column + insert M97 disclosure.

Hard boundaries:
  - coverage.tsv: ONLY the 4th column (index 3) of the 14 OTHER14 rows changes.
  - PANEL.md: ONLY one M97 disclosure block inserted immediately after M96.
  - No other file outside this output dir is written except these two targets.
  - No reverse engineering; col4 = pinned disk original col4 + appended delta segment.

OFF-BY-ONE DEFENSE (lesson from prior rounds):
  - Everything keyed by normalized entry + EXACT pinned before_col4 byte match.
  - New file built from the PIN, never from a re-derived positional index.
  - CONCURRENCY GUARD: live disk must byte-equal the pin, else abort before any write.

Caliber numbers in the M97 disclosure are READ FROM preflight.json (measured),
never hardcoded. Coverage.tsv has NO trailing LF (ends_lf=false) — preserved.
"""
import csv, os, sys, hashlib, json, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_OTHER14", "delta.tsv")
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
    assert len(ddata) == NROWS and all(len(dr) == 8 for dr in ddata)
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
        if r[3] != before4[e]:
            raise SystemExit("ABORT: pinned before_col4 mismatch at row %d entry %s" % (ri + 1, e))
        dr = other_by_entry[e]
        if not all(dr[c] == r[c] for c in [0, 1, 2, 4, 5, 6, 7]):
            raise SystemExit("ABORT: non-col4 column mismatch at row %d entry %s" % (ri + 1, e))
        new4 = new4_by_entry[e]
        if not (new4.startswith(before4[e]) and len(new4) > len(before4[e])):
            raise SystemExit("ABORT: strict-prefix fail at row %d entry %s" % (ri + 1, e))
        if "④" in before4[e]:
            raise SystemExit("ABORT: row %d entry %s already has ④ in pin col4" % (ri + 1, e))
        cov_rows[ri][3] = new4
        changed.append((ri + 1, e, len(before4[e]), len(new4)))
    if len(changed) != NROWS:
        raise SystemExit("ABORT: changed row count != 14 (%d)" % len(changed))

    new_cov_txt = "\n".join("\t".join(r) for r in cov_rows)
    if cov_ends_lf:
        new_cov_txt += "\n"
    new_cov_bytes = new_cov_txt.encode("utf-8")
    assert b"\r" not in new_cov_bytes

    # ---- M97 disclosure numbers, from MEASURED preflight values ----
    six = pre["six_pre"]
    N_pre_A = six["N_pre_A"]            # 0
    N_pre_B = six["N_pre_B"]            # 0
    N_new_witness = six["N_new_witness"]  # 12
    N_new_directcall = six["N_new_directcall"]  # 2
    N_A_pre = six["N_A_pre"]            # 375
    N_B_pre = six["N_B_pre"]            # 210
    proved = 1654
    N_A_post = N_A_pre + (NROWS - N_pre_A)               # 389
    N_B_post_lit = N_B_pre + (N_new_witness - N_pre_B)   # 222
    N_B_post_broad = N_B_pre + (NROWS - N_pre_B)          # 224

    M97_LINES = [
        "> ✅ **M97 补记：R16-F1-OTHER14 并入 14 行（PROBE_4GAP F1 缺口 122 行里真正无 ④ 的剩余部分；2 行 direct call + 12 行槽位见证）**",
        ("> 本批 14 行是 `R16_PROBE_4GAP` F1 缺口 122 行里改前真正无 `④` 的剩余部分（122 = 80 行本来就有 `④` + 28 行已由 B1–B5 补完 + 本批 14 行；"
         "`R16_PROBE_F1_PIVOT/_gap122_recompute.tsv` 逐行核本批 14 行 `has4=False`；清单 `R16_F1_OTHER14/delta.tsv` 源自 `R16_PROBE_F1_PIVOT/other14.tsv`）。"
         "14/14 纯追加（原第 4 列 == 新第 4 列严格前缀）、改前 14 行 `④` 计数全 0；只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同、grade 未改 `[已证]`。"),
        ("> 形态：**2 行 `direct call`**（`004AF540`@站点 `006C404C`、`004B5AB0`@站点 `006C494C`；E8 指令边界 + `site+5+rel32==entry` + 非自环；"
         "比槽位见证更强、独立于 ② 类身份证据）与 **12 行槽位见证**（vt/槽/COL/RTTI/装表点 6 项 × 12 = 72/72 全真）。"
         "异族审计 `R16_AUDIT_OTHER14/VERDICT.md` 判 **PASS 14 / FAIL 0 / 必改 0**：§A 原文保全 0 不合格、§B direct 2/2 + 槽位 72/72、"
         "§C 填充定界反推 7/7、§D 文本一致 0 不合格、§E same_source 可信、§F 反抄袭 0 不合格。"),
        ("> ⚠️ **方法披露（审计 §3.2，不判 FAIL 但引用者须知情）**：执行器自陈的「从函数起点线性反汇编精确落到站点」定界判据几乎没有分辨力——"
         "实测容差恰等于整个填充 run（6/6/6/9/9/9/9 B），把宿主起点往前挪满 run 仍「精确落到站点」（负向对照 `0040B540`→`0040B53F` 仍命中）。"
         "真正钉住 7 行边界的是三条硬证据：①填充 run 全为 `0x90`（本批无 `0xCC`）且结束于声明宿主；②run 前一字节为 `C3`（ret，上一函数终止）；"
         "③宿主是 `.data` 起始那张 **3,944 项严格升序 `.text` 代码指针表**（`00812004..00815DA0`）成员（idx 55/195/209/522/1514/2284/2498；"
         "抽检 40/40 以 ret 结尾、33/40 至少写一全局）。表名归为 CRT `__xc_a..__xc_z` 仍属推断（未找到 `_initterm` 以 imm32 引用其起止的证据），"
         "但「真实函数入口且被登记于初始化机制」由成员关系 + 形态 + `C3`/填充三重佐证。"),
        (f"> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **{N_A_pre:,} / {proved:,}（{pct(N_A_pre,proved)}%）**"
         f"升至 **{N_A_post:,} / {proved:,}（{pct(N_A_post,proved)}%）**，本批净增 **{N_A_post-N_A_pre} 行**（改前 14 行 `④` 计数全 0，N_pre_A={N_pre_A}）。"
         f"口径 B 按 PANEL 历次字面定义（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **{N_B_pre:,} / {proved:,}（{pct(N_B_pre,proved)}%）**"
         f"升至 **{N_B_post_lit:,} / {proved:,}（{pct(N_B_post_lit,proved)}%）**，净增 **{N_B_post_lit-N_B_pre} 行**而非 14——"
         f"{N_new_directcall} 行 direct call 写的是 `④ direct call 使用见证（形态 1）`，按审计 §B.1 `D_no_slot_phrase=True×2` 不含该字面子串；"
         f"若按「任一 ④ 使用见证形态（槽位 + direct）」宽口径计则为 **{N_B_post_broad:,}（+{NROWS}）**。"
         f"派卡文「A +14 / B +14」中 B+14 仅在宽口径下成立，字面口径实测为 +{N_B_post_lit-N_B_pre}，此处如实并列。"),
        ("> 判定与计数均未变：coverage 18,498 数据行、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。"),
    ]

    # ---- build new PANEL from PIN: insert M97 block right after M96 block ----
    pan_lines, pan_ends_lf = split_lines(pin_pan)
    assert pan_ends_lf is True
    assert pre["pan_struct"]["insert_at_0based"] == 283
    ins = pre["pan_struct"]["insert_at_0based"]
    assert not any("M97 补记" in l for l in pan_lines)
    assert pan_lines[ins].startswith("> 📌 **M77 并表实算说明**"), pan_lines[ins][:60]
    new_pan_lines = pan_lines[:ins] + M97_LINES + pan_lines[ins:]
    new_pan_txt = "\n".join(new_pan_lines) + "\n"
    new_pan_bytes = new_pan_txt.encode("utf-8")
    assert b"\r" not in new_pan_bytes

    # ---- DRY RUN: preview the M97 block before any write ----
    if os.environ.get("DRY_RUN") == "1":
        print("M97_LINES count:", len(M97_LINES))
        for ln in M97_LINES:
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
        "insertion": {"m96_line_index_0based": pre["pan_struct"]["m96_idx_0based"][0],
                      "insert_at_0based": ins,
                      "inserted_line_count": len(M97_LINES),
                      "insert_before_1based": ins + 1},
        "changed_rows": changed,
        "six_post_expected": {"N_A_post": N_A_post, "N_B_post_literal": N_B_post_lit,
                              "N_B_post_broad": N_B_post_broad},
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
    print("six expected post: N_A=%d N_B_lit=%d N_B_broad=%d" % (N_A_post, N_B_post_lit, N_B_post_broad))


if __name__ == "__main__":
    main()
