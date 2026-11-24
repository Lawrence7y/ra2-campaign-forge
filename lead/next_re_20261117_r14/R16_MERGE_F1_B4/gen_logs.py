# -*- coding: utf-8 -*-
"""R16-MERGE-F1-B4 :: generate MERGE_LOG.md and BEFORE_AFTER.txt from pinned state."""
import csv, os, sys, json, hashlib

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(r"D:\Project\ra2-campaign-forge", "lead", "next_re_20261117_r14")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B4")
DELTA = os.path.join(ROOT, "R16_F1_B4", "delta.tsv")


def main():
    before = json.load(open(os.path.join(OUT, "before_state.json"), encoding="utf-8"))
    after = json.load(open(os.path.join(OUT, "after_state.json"), encoding="utf-8"))
    before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
    with open(DELTA, encoding="utf-8-sig", newline="") as f:
        ddata = list(csv.reader(f, delimiter="\t"))[1:]
    vr = json.load(open(os.path.join(OUT, "verify_result.json"), encoding="utf-8"))

    # ---- MERGE_LOG.md ----
    lines = []
    lines.append("# R16-MERGE-F1-B4 · 并表日志")
    lines.append("")
    lines.append("> 批次 B4（派生集合第 55–72 行）· 审计 `R16_AUDIT_F1_B4\\VERDICT.md` = PASS 18 / FAIL 0 / 必改 0")
    lines.append("> 写域：`COVERAGE\\coverage.tsv`（仅 18 行第 4 列）+ `COVERAGE\\PANEL.md`（仅 1 条 M92 披露）+ 本产物目录")
    lines.append("> 防 off-by-one：先 pin 两份目标，再以 entry + pinned `before_col4` 逐字匹配写回；写后用 pin 对照逐字节还原性自证。")
    lines.append("")
    lines.append("## 1. 改前 / 改后文件状态")
    lines.append("")
    lines.append("| 文件 | 状态 | mtime | 字节 | sha256 | 行数 | LF | CRLF | endsLF |")
    lines.append("|---|---|---|---:|---|---:|---:|---:|---|")
    for fn in ["coverage.tsv", "PANEL.md"]:
        b, a = before[fn], after[fn]
        lines.append(f"| {fn} | before | {b['mtime']} | {b['bytes']:,} | {b['sha256']} | {b['lines']:,} | {b['lf']:,} | {b['crlf']} | {b['ends_lf']} |")
        lines.append(f"| {fn} | after  | {a['mtime']} | {a['bytes']:,} | {a['sha256']} | {a['lines']:,} | {a['lf']:,} | {a['crlf']} | {a['ends_lf']} |")
    lines.append("")
    lines.append("## 2. 18 行第 4 列 before / after")
    lines.append("")
    lines.append("> `append = 改后第4列 − 改前第4列`（改前为改后严格前缀，18/18）。逐行 before/after 全文见 `before_col4.json` + delta.tsv。")
    lines.append("")
    lines.append("| # | entry (pin 行号 1-based) | before 长度 | after 长度 | append 长度 | before 第4列（前 90 字） | append 段（前 90 字） |")
    lines.append("|---:|---|---:|---:|---:|---|---|")
    for i, dr in enumerate(ddata, 1):
        e = dr[0].upper()
        old4 = before4[e]
        new4 = dr[3]
        ap = new4[len(old4):]
        rec = next(c for c in after["changed_rows"] if c[1] == e)
        lines.append(f"| {i} | {e} (L{rec[0]}) | {len(old4)} | {len(new4)} | {len(ap)} | {old4[:90]} | {ap[:90]} |")
    lines.append("")
    lines.append("## 3. 九个验证项（卡面 §4）")
    lines.append("")
    lines.append("| # | 项 | 结论 | 实测 |")
    lines.append("|---:|---|---|---|")
    for i, v in enumerate(vr["verifications"], 1):
        lines.append(f"| {i} | {v['check']} | {'PASS' if v['pass'] else 'FAIL'} | {v['detail']} |")
    lines.append("")
    lines.append("## 4. 六个实测数（自算，非照抄）")
    lines.append("")
    s = vr["six_measured"]
    lines.append(f"- N_pre_A（18 行改前第 4 列含 `④`）= **{s['N_pre_A']}**（`00749F30` 2 个 / `0074BA30` 1 个）")
    lines.append(f"- N_pre_B（18 行改前含 `④ 活表槽位见证`）= **{s['N_pre_B']}**")
    lines.append(f"- N_A_pre / N_A_post（全表 `[已证]` 且含 `④`）= **{s['N_A_pre']} → {s['N_A_post']}**（净增 {s['N_A_post']-s['N_A_pre']} = 18 − {s['N_pre_A']}，口径 A 不增的 {s['N_pre_A']} 行即同格并存旧 ④）")
    lines.append(f"- N_B_pre / N_B_post（全表 `[已证]` 且含 `④ 活表槽位见证`）= **{s['N_B_pre']} → {s['N_B_post']}**（净增 {s['N_B_post']-s['N_B_pre']}）")
    lines.append("")
    lines.append("## 5. 达标集合（strict_panel.py 口径复算，输出到本目录）")
    lines.append("")
    lines.append(f"- 名义达标：**{vr['dod_nominal']}**")
    lines.append(f"- 严格达标：**{vr['dod_strict']}**")
    lines.append("- 输出：`strict_panel_out.txt` / `strict_panel.json` / `strict_panel.tsv`（若脚本产出）/ `strict_panel_b4.py`")
    lines.append("")
    lines.append("## 6. M92 披露")
    lines.append("")
    lines.append("- 插入点：PANEL.md 第 260 行（M91 块 253–259 之后，M77 并表实算说明之前），7 行引用块。")
    lines.append("- 三条 NIT 已照实写入：① `0071F8C0` 见证头 `::ctor`（非 `::slotN`，下游按 `::slot` 解析会漏 1 行）；② 本期 10 行本 entry 体内也装同表（`scan_F1_audit.tsv` 的 `n_install_inside_body` 系统性低估为 4）；③ 同格并存旧 ④ 2 行（`00749F30` / `0074BA30`）。")
    lines.append("- 既有内容零删除零改字：删 M92 块后重建 sha256 == 改前 sha256（验证 #7 PASS）。")
    lines.append("")
    with open(os.path.join(OUT, "MERGE_LOG.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # ---- BEFORE_AFTER.txt ----
    ba = []
    ba.append("R16-MERGE-F1-B4 :: BEFORE / AFTER FILE STATE")
    ba.append("")
    ba.append("== coverage.tsv ==")
    for tag, st in [("BEFORE", before["coverage.tsv"]), ("AFTER", after["coverage.tsv"])]:
        ba.append(f"{tag}: mtime={st['mtime']} bytes={st['bytes']} sha256={st['sha256']} lines={st['lines']} LF={st['lf']} CRLF={st['crlf']} endsLF={st['ends_lf']} bom={st['bom']}")
    ba.append("")
    ba.append("== PANEL.md ==")
    for tag, st in [("BEFORE", before["PANEL.md"]), ("AFTER", after["PANEL.md"])]:
        ba.append(f"{tag}: mtime={st['mtime']} bytes={st['bytes']} sha256={st['sha256']} lines={st['lines']} LF={st['lf']} CRLF={st['crlf']} endsLF={st['ends_lf']} bom={st['bom']}")
    ba.append("")
    ba.append("== key line comparison: M91 (before L253-259) -> M92 inserted at L260-266 ==")
    ba.append("M92 7-line block inserted immediately after M91 block; PANEL.md existing content byte-identical otherwise (verification #7 PASS).")
    ba.append("")
    ba.append("== key line comparison: 18 coverage rows (entry -> L) ==")
    for rec in after["changed_rows"]:
        ba.append(f"  {rec[1]} @ L{rec[0]} : col4 {rec[2]} -> {rec[3]} bytes")
    ba.append("")
    ba.append("== six measured numbers ==")
    ba.append(json.dumps(vr["six_measured"], ensure_ascii=False))
    ba.append("")
    ba.append("== DoD ==")
    ba.append(f"nominal={vr['dod_nominal']}  strict={vr['dod_strict']}")
    with open(os.path.join(OUT, "BEFORE_AFTER.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ba) + "\n")

    print("logs generated")
    print("MERGE_LOG.md bytes:", os.path.getsize(os.path.join(OUT, "MERGE_LOG.md")))
    print("BEFORE_AFTER.txt bytes:", os.path.getsize(os.path.join(OUT, "BEFORE_AFTER.txt")))


if __name__ == "__main__":
    main()
