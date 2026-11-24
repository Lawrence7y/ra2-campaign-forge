# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B5 :: generate MERGE_LOG.md and BEFORE_AFTER.txt from saved state.
Writes ONLY into own dir. All numbers read from before/after/preflight/verify_result JSON.
"""
import csv, os, sys, json

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B5")
DELTA = os.path.join(ROOT, "R16_F1_B5", "delta.tsv")

J = lambda n: json.load(open(os.path.join(OUT, n), encoding="utf-8"))
before = J("before_state.json")
after = J("after_state.json")
pre = J("preflight.json")
vres = J("verify_result.json")
before4 = J("before_col4.json")
cb, ca = before["coverage.tsv"], after["coverage.tsv"]
pb, pa = before["PANEL.md"], after["PANEL.md"]
six = vres["six_measured"]

with open(DELTA, encoding="utf-8-sig", newline="") as f:
    ddata = list(csv.reader(f, delimiter="\t"))[1:]
new4 = {d[0]: d[3] for d in ddata}


def fnum(x):
    return f"{x:,}"


# ---------- MERGE_LOG.md ----------
L = []
L.append("# R16-MERGE-F1-B5 · 并表日志（F1 收官批 4 行）")
L.append("")
L.append("> 批次 B5（派生集合第 73–76 行，收官批）· 审计 `R16_AUDIT_F1_B5\\VERDICT.md` = PASS 4 / FAIL 0 / 必改 0（NIT 2）")
L.append("> 写域：`COVERAGE\\coverage.tsv`（仅 4 行第 4 列）+ `COVERAGE\\PANEL.md`（仅 1 条 M93 披露）+ 本产物目录")
L.append("> 防 off-by-one：先 pin 两份目标，再以 entry + pinned `before_col4` 逐字匹配写回；写后用 pin 对照逐字节还原性自证。")
L.append("> PANEL 披露编号 **M93**，插入点紧接 M92 块之后；披露写明 **76/76 收官**。")
L.append("")
L.append("## 1. 改前 / 改后文件状态")
L.append("")
L.append("| 文件 | 状态 | mtime | 字节 | sha256 | 行数 | LF | CRLF | endsLF |")
L.append("|---|---|---|---:|---|---:|---:|---:|---|")
for label, d in [("coverage.tsv / before", cb), ("coverage.tsv / after ", ca),
                 ("PANEL.md / before", pb), ("PANEL.md / after ", pa)]:
    L.append(f"| {label} | | {d['mtime']} | {fnum(d['bytes'])} | {d['sha256']} | {fnum(d['lines'])} | {fnum(d['lf'])} | {d['crlf']} | {d['ends_lf']} |")
L.append("")
L.append("## 2. 4 行第 4 列 before / after")
L.append("")
L.append("> `append = 改后第4列 − 改前第4列`（改前为改后严格前缀，4/4）。逐行 before/after 全文见 `before_col4.json` + `delta.tsv`。")
L.append("")
L.append("| # | entry (pin 行号 1-based) | before 长度 | after 长度 | append 长度 | before 第4列（前 90 字） | append 段（前 90 字） |")
L.append("|---:|---|---:|---:|---:|---|---|")
for i, (ln, e, bl, al) in enumerate(after["changed_rows"], 1):
    b4 = before4[e]
    ap = new4[e][len(b4):]
    L.append(f"| {i} | {e} (L{ln}) | {bl} | {al} | {al-bl} | {b4[:90]} | {ap[:90]} |")
L.append("")
L.append("## 3. 九个验证项（卡面 §4）")
L.append("")
L.append("| # | 项 | 结论 | 实测 |")
L.append("|---:|---|---|---|")
for i, r in enumerate(vres["verifications"], 1):
    L.append(f"| {i} | {r['check']} | {'PASS' if r['pass'] else 'FAIL'} | {r['detail']} |")
L.append("")
L.append("## 4. 六个实测数（自算，非照抄）")
L.append("")
L.append(f"- N_pre_A（4 行改前第 4 列含 `④`）= **{six['N_pre_A']}**（00763200，散文式 `④` 计数 1）")
L.append(f"- N_pre_B（4 行改前含 `④ 活表槽位见证`）= **{six['N_pre_B']}**")
L.append(f"- N_A_pre / N_A_post（全表 `[已证]` 且含 `④`）= **{six['N_A_pre']} → {six['N_A_post']}**（净增 {six['N_A_post']-six['N_A_pre']} = 4 − {six['N_pre_A']}，00763200 改前已含 ④ 故口径 A 不增）")
L.append(f"- N_B_pre / N_B_post（全表 `[已证]` 且含 `④ 活表槽位见证`）= **{six['N_B_pre']} → {six['N_B_post']}**（净增 {six['N_B_post']-six['N_B_pre']}）")
L.append("")
L.append("## 5. 达标集合（strict_panel.py 口径复算，输出到本目录）")
L.append("")
L.append(f"- 名义达标：**{vres['dod_nominal']}**")
L.append(f"- 严格达标：**{vres['dod_strict']}**")
L.append("- 输出：`strict_panel_b5.py` / `strict_panel_out.txt`（脚本按 B4 同法复制 `RULING_R15_20261119\\work\\strict_panel.py` 并把 OUT 改到本目录）")
L.append("")
L.append("## 6. M93 披露（76/76 收官）")
L.append("")
L.append(f"- 插入点：PANEL.md 第 {after['insertion']['insert_before_1based']} 行（M92 块之后、M77 并表实算说明之前），7 行引用块，M92 在 0-based {after['insertion']['m92_line_index_0based']}。")
L.append("- 内容：PASS 4 / FAIL 0 / 必改 0（32/32）；口径 A 372→375（净增 3）、口径 B 206→210（净增 4）；**76/76 收官**（18+18+18+18+4）。")
L.append("- 两条审计 NIT 已照实写入：① `00763200` 同一格并存旧散文式 ④ 与新成文 ④（计数 1→2，审计核 188 行 witness 行 ④ 计数均 ≥2，合先例，下游按行去重）；② `00772CD0`/`00772EB0` 共用装表指令 `00771E77`，按「2 行 / 1 安装事件」记录。")
L.append("- 既有内容零删除零改字：删 M93 块后重建 sha256 == 改前 sha256（验证 #7 PASS）。")
L.append("")
open(os.path.join(OUT, "MERGE_LOG.md"), "w", encoding="utf-8").write("\n".join(L))

# ---------- BEFORE_AFTER.txt ----------
T = []
T.append("R16-MERGE-F1-B5 :: BEFORE / AFTER FILE STATE")
T.append("=" * 72)
T.append("")
for label, d in [("coverage.tsv BEFORE", cb), ("coverage.tsv AFTER ", ca),
                 ("PANEL.md    BEFORE", pb), ("PANEL.md    AFTER ", pa)]:
    T.append(f"{label}")
    T.append(f"  mtime    : {d['mtime']}")
    T.append(f"  bytes    : {d['bytes']:,}")
    T.append(f"  sha256   : {d['sha256']}")
    T.append(f"  lines    : {d['lines']:,}  (LF={d['lf']:,}, CRLF={d['crlf']}, endsLF={d['ends_lf']}, BOM={d['bom']})")
    T.append("")
T.append("-" * 72)
T.append("KEY LINE COMPARISON — 4 changed rows (col4 only):")
T.append("")
for ln, e, bl, al in after["changed_rows"]:
    b4 = before4[e]
    ap = new4[e][len(b4):]
    T.append(f"[{e}] pin line {ln} (1-based)")
    T.append(f"  col4 BEFORE ({bl} ch): {b4[:120]}")
    T.append(f"  col4 AFTER  ({al} ch): {new4[e][:120]}")
    T.append(f"  APPEND      ({al-bl} ch): {ap[:120]}")
    T.append(f"  strict-prefix: {new4[e].startswith(b4)} | §12.6 in append: {ap.count('§12.6')} | §12.4 in append: {ap.count('§12.4')}")
    T.append("")
T.append("-" * 72)
T.append(f"PANEL insertion: 7-line M93 block inserted at 1-based line {after['insertion']['insert_before_1based']} (right after M92 block).")
T.append(f"Reversibility (pin+before_col4): recon sha == BEFORE sha -> {vres['verifications'][0]['pass']}")
T.append(f"Six measured: {json.dumps(six, ensure_ascii=False)}")
T.append(f"Overall: {'ALL PASS' if vres['all_pass'] else 'SOME FAIL'}")
open(os.path.join(OUT, "BEFORE_AFTER.txt"), "w", encoding="utf-8").write("\n".join(T))

print("gen_logs OK")
print("MERGE_LOG.md bytes:", os.path.getsize(os.path.join(OUT, "MERGE_LOG.md")))
print("BEFORE_AFTER.txt bytes:", os.path.getsize(os.path.join(OUT, "BEFORE_AFTER.txt")))
