# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B3 :: perform the merge of 18 rows' 4th column + insert M91 disclosure.

Hard boundaries respected:
  - coverage.tsv: ONLY the 4th column (index 3) of the 18 B3 rows changes.
  - PANEL.md: ONLY one M91 disclosure block is inserted, immediately after M90.
  - No other file outside this output dir is written except these two targets.
  - No reverse engineering; col4 = disk original col4 + appended delta segment.
"""
import csv, os, sys, hashlib, json, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B3", "delta.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B3")
os.makedirs(OUT, exist_ok=True)

M91_LINES = [
    "> ✅ **M91 补记：F1（槽位-安装型）缺口行 ④ 成文 —— 批次 B3 并入 18 行**",
    "> 本批 18 行取自 `R16_PROBE_4GAP\\scan_F1_audit.tsv` 派生集合（`same_source=no` + `ring4_at` 解出装表指令 + 装表点体外 + 现盘 `[已证]` 且第 4 列无 `④ 活表槽位见证` + ③ 干净），派生命中 76 行，本批取第 37–54 行。",
    "> 异族审计（`R16_AUDIT_F1_B3\\VERDICT.md`）判 **PASS 18 / FAIL 0 / 必改 0**，§B 8 项 × 18 = **144/144** 字节事实独立复算为真。",
    "> **定表**：执行器所选活表经审计独立核「精确类一致者恰好 1 张」（B3 类型：本批 18/18 每行该地址在镜像 `.rdata/.data` 内只出现 1 次、只落进 1 张表的 1 个槽位，**无同槽多表**；B1 类型 MouseClass::slot17 同槽 9 张、AnimClass::slot84 同槽 21 张的情况亦各只 1 张类一致，本批未出现），松/严双口径类一致均 18/18。",
    "> 数字（口径 A/B 实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **354 / 1,654（21.40%）升至 356 / 1,654（21.52%）**，本批**净增 = 356 − 354 = 2 行**，**不是 +18**：18 行里有 **16 行**（14 行 `④ 活 COM 类对象` + 2 行 `④ 行外 ctor`）改前第 4 列已含 `④`，故这 16 行口径 A 不增（另 2 行 `006E3E30`/`006E57A0` 改前无 ④，净增 2 行）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **170 / 1,654（10.28%）升至 188 / 1,654（11.37%）**（净增 18 行）。",
    "> ⚠️ **已接受限制（来自审计 NIT，不判 FAIL 但引用者须知情）**：① **同一格并存两条 `④`** —— 因 append-only 约束，16 行追加后同一第 4 列里同时存在旧 `④` 表述（`④ 活 COM 类对象` / `④ 行外 ctor`）与新 `④ 活表槽位见证`；审计已核新旧两条指向同一 vt/site/宿主、无矛盾，⇒ **下游若按「④ 条数」或子串分桶统计会被双计，必须按行去重**。② **个位行本 entry 体内也装同一张表** —— ④ 采纳的是体外装表点（活性不靠自身见证），但 §12.3 意义上独立链只有体外那一条；审计点名 B2 批有 6 行如此（`005FEAF0`/`0062D7A0`/`0062D9A0`/`00644960`/`00645950`/`006B5850`），本披露写入该条以覆盖后续批次；**本批（B3）实测 0 行**（18/18 `self_install_sites=[]`，见 `R16_AUDIT_F1_B3\\VERDICT.md` §C），B1 批对应行数未逐行核，见各批 `fields.tsv`。③ **同一格内「宿主」一词指两个不同函数（本批 14 个工厂行）** —— 旧 ④ 的「宿主 `006BB9A0`」= **调用该 ctor 的注册函数（调用方函数）**，新 ④ 的「装表点 `006C37C9` 位于 `006C37C0` 体内」中「宿主 `006C37C0`」= **装表点所在函数**；审计（NIT-2）独立复算两者**均实测为真**（14 个调用点 `006BD015`…`006BD684` 逐行 `which_body` 全落 `006BB9A0`，装表点 `006C37C9` 等确在各自 ctor 体内），**非矛盾、属同词两义**，引用者须知此区别。",
    "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**。",
]


def file_info(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    return {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest().upper(),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat(),
        "lf": b.count(b"\n"),
        "crlf": crlf,
        "bare_lf": b.count(b"\n") - crlf,
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


def main():
    # ---- BEFORE state ----
    before = {"coverage.tsv": file_info(COV), "PANEL.md": file_info(PAN)}

    cov_raw = open(COV, "rb").read()
    cov_txt = cov_raw.decode("utf-8")
    cov_lines = cov_txt.split("\n")
    assert cov_lines[-1] != "", "coverage.tsv should NOT end with LF"
    cov_rows = [ln.split("\t") for ln in cov_lines]
    cov_header, cov_data = cov_rows[0], cov_rows[1:]

    pan_raw = open(PAN, "rb").read()
    pan_txt = pan_raw.decode("utf-8")
    pan_lines = pan_txt.split("\n")
    assert pan_lines[-1] == "", "PANEL.md should end with LF"
    # keep the trailing empty element so join reproduces exactly

    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    assert len(ddata) == 18

    # index disk rows by entry
    by_entry = {}
    for idx, r in enumerate(cov_data):
        by_entry.setdefault(norm_e(r[0]), []).append(idx)

    # ---- validate + prepare replacements ----
    replacements = []  # (line_index, new_col4, old_col4, entry)
    for dr in ddata:
        assert len(dr) == 8
        e = norm_e(dr[0])
        cands = [i for i, r in enumerate(cov_data) if norm_e(r[0]) == e]
        assert len(cands) == 1, (e, len(cands))
        di = cands[0]
        ri = di + 1  # cov_data = cov_rows[1:], so cov_rows index = cov_data index + 1
        r = cov_rows[ri]
        old4 = r[3]
        new4 = dr[3]
        assert new4.startswith(old4) and len(new4) > len(old4), ("prefix fail", e)
        for c in [0, 1, 2, 4, 5, 6, 7]:
            assert dr[c] == r[c], ("col mismatch", e, c)
        assert r[4].strip() == "[已证]", ("grade", e)
        replacements.append((ri, new4, old4, e))

    # ---- apply coverage.tsv changes (only col4 of 18 rows) ----
    new_cov_rows = [list(r) for r in cov_rows]
    for idx, new4, old4, e in replacements:
        new_cov_rows[idx][3] = new4
    new_cov_txt = "\n".join("\t".join(r) for r in new_cov_rows)
    new_cov_bytes = new_cov_txt.encode("utf-8")
    # sanity: no BOM, no CR introduced
    assert b"\r" not in new_cov_bytes

    # ---- insert M91 into PANEL.md immediately after M90 block ----
    assert not any("M91 补记" in ln for ln in pan_lines), "M91 already present"
    m90_idx = None
    for i, ln in enumerate(pan_lines):
        if "M90 补记" in ln:
            m90_idx = i
            break
    assert m90_idx is not None, "M90 marker not found"
    # find insertion point = first line after M90 starting with the M77 note
    ins = None
    for i in range(m90_idx + 1, len(pan_lines)):
        if pan_lines[i].startswith("> 📌 **M77 并表实算说明**"):
            ins = i
            break
    assert ins is not None, "insertion anchor (M77 note after M90) not found"
    assert ins == m90_idx + 7, ("unexpected M90 block length", m90_idx, ins)
    new_pan_lines = pan_lines[:ins] + M91_LINES + pan_lines[ins:]
    new_pan_txt = "\n".join(new_pan_lines)
    new_pan_bytes = new_pan_txt.encode("utf-8")
    assert b"\r" not in new_pan_bytes

    # ---- write ----
    with open(COV, "wb") as f:
        f.write(new_cov_bytes)
    with open(PAN, "wb") as f:
        f.write(new_pan_bytes)

    after = {"coverage.tsv": file_info(COV), "PANEL.md": file_info(PAN)}
    after["insertion"] = {"m90_line_index": m90_idx, "insert_at_line_index": ins,
                          "inserted_line_count": len(M91_LINES)}

    with open(os.path.join(OUT, "before_state.json"), "w", encoding="utf-8") as f:
        json.dump(before, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "after_state.json"), "w", encoding="utf-8") as f:
        json.dump(after, f, ensure_ascii=False, indent=2)

    # stash original col4 values for reversibility check (within own dir only)
    with open(os.path.join(OUT, "before_col4.json"), "w", encoding="utf-8") as f:
        json.dump({e: old4 for idx, new4, old4, e in replacements}, f, ensure_ascii=False, indent=1)

    print("MERGE DONE")
    print("before:", json.dumps(before, ensure_ascii=False))
    print("after :", json.dumps(after, ensure_ascii=False))


if __name__ == "__main__":
    main()
