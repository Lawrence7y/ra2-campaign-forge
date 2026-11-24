# -*- coding: utf-8 -*-
"""Generate MERGE_LOG.md and BEFORE_AFTER.txt from the measured state."""
import csv, os, sys, json, hashlib

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(ROOT, "R16_MERGE_F1_B3")
DELTA = os.path.join(ROOT, "R16_F1_B3", "delta.tsv")

before = json.load(open(os.path.join(OUT, "before_state.json"), encoding="utf-8"))
after = json.load(open(os.path.join(OUT, "after_state.json"), encoding="utf-8"))
before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
vr = json.load(open(os.path.join(OUT, "verify_result.json"), encoding="utf-8"))
ddata = list(csv.reader(open(DELTA, encoding="utf-8-sig", newline=""), delimiter="\t"))[1:]

six = vr["six_numbers"]
verifs = vr["verifications"]

# ---------------- MERGE_LOG.md ----------------
L = []
L.append("# R16-MERGE-F1-B3 · 合并日志")
L.append("")
L.append("> 批次 B3（派生集合第 37–54 行，18 行）；PANEL 披露编号 M91，插入点紧接 M90 块之后。")
L.append("> 审计 R16_AUDIT_F1_B3/VERDICT.md：PASS 18 / FAIL 0 / 必改 0（已核，方可并表）。")
L.append("")
L.append("## 一、改前 → 改后（两份文件）")
L.append("")
L.append("| 文件 | 改前 bytes | 改后 bytes | 改前 sha256(前8) | 改后 sha256(前8) |")
L.append("|---|---:|---:|---|---|")
L.append(f"| coverage.tsv | {before['coverage.tsv']['bytes']} | {after['coverage.tsv']['bytes']} | "
         f"{before['coverage.tsv']['sha256'][:8]} | {after['coverage.tsv']['sha256'][:8]} |")
L.append(f"| PANEL.md | {before['PANEL.md']['bytes']} | {after['PANEL.md']['bytes']} | "
         f"{before['PANEL.md']['sha256'][:8]} | {after['PANEL.md']['sha256'][:8]} |")
L.append("")
L.append("## 二、六个实测数（改前盘上自算，非预测/旧值）")
L.append("")
L.append(f"- N_pre_A = **{six['N_pre_A']}**（18 行中改前第 4 列已含字符 `④` 的行数）")
L.append(f"- N_pre_B = **{six['N_pre_B']}**（18 行中改前第 4 列已含 `④ 活表槽位见证` 的行数）")
L.append(f"- N_A_pre = **{six['N_A_pre']}** → N_A_post = **{six['N_A_post']}**（净增 **{six['N_A_post']-six['N_A_pre']}**，不是 +18；"
         f"18 行里 16 行改前已含 `④`，故口径 A 不增）")
L.append(f"- N_B_pre = **{six['N_B_pre']}** → N_B_post = **{six['N_B_post']}**（净增 **{six['N_B_post']-six['N_B_pre']}**）")
L.append("")
L.append("口径 A = `[已证]` 且第 4 列含字符 `④`（MERGE_M79/verify.py:159）；口径 B = `[已证]` 且第 4 列含子串 `④ 活表槽位见证`。")
L.append("")
L.append("审计记的两条已接受限制已写进 M91 披露：① 16 行同格并存两条 `④`（按行去重）；"
         "② 个位行本 entry 体内也装同一张表（本批实测 0 行，写入以覆盖后续批次）；"
         "另按派发要求照实写入 NIT-2：同格内「宿主」一词指两个不同函数（旧 ④ = 调用方注册函数 006BB9A0；新 ④ = 装表点函数 006C37C0/006C37C9 所在函数），两者均实测为真。")
L.append("")
L.append("## 三、9 项验证（verify.py 可复跑）")
L.append("")
L.append("| # | 验证 | 结果 | 实测 |")
L.append("|---|---|---|---|")
for i, v in enumerate(verifs, 1):
    L.append(f"| {i} | {v['check']} | {'PASS' if v['pass'] else 'FAIL'} | {v['detail']} |")
L.append("")
L.append("达标集合（strict_panel.py 口径，输出在本目录）：名义 **S15,S16,S17**，严格 **S17**（未翻转）。")
L.append("")
L.append("## 四、18 行第 4 列 before / after")
L.append("")
L.append("每行「改前第 4 列」为盘上原值，「改后第 4 列」为 delta 值（= 原值 + 追加段）。"
         "已核 18/18 严格前缀、其余 7 列逐字节相同。")
L.append("")
for dr in ddata:
    e = dr[0].strip().upper()
    old = before4[e]
    new = dr[3]
    append = new[len(old):] if new.startswith(old) else "<PREFIX FAIL>"
    L.append(f"### {e}  {dr[2]}")
    L.append("")
    L.append("**改前第 4 列：**")
    L.append("```")
    L.append(old)
    L.append("```")
    L.append("")
    L.append("**追加段（④ 活表槽位见证 + D-47 披露）：**")
    L.append("```")
    L.append(append)
    L.append("```")
    L.append("")
L.append("## 五、边界声明")
L.append("")
L.append("- 只改 coverage.tsv 这 18 行的第 4 列；其它行/列、grade/判定/行序均未动。")
L.append("- PANEL.md 只插入 1 条 M91 披露（7 行 `> ` 引用块），既有内容零删除零改字（删 M91 块后 sha 复原为改前值）。")
L.append("- 未改 R14_COMMON/台账/看板/_drafts/_cards/卡目录；未做逆向；strict_panel 输出在本目录。")
L.append("")

with open(os.path.join(OUT, "MERGE_LOG.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))

# ---------------- BEFORE_AFTER.txt ----------------
B = []
B.append("R16-MERGE-F1-B3 BEFORE / AFTER")
B.append("=" * 60)
for label, key in [("coverage.tsv", "coverage.tsv"), ("PANEL.md", "PANEL.md")]:
    b = before[key]; a = after[key]
    B.append("")
    B.append(f"[{label}]")
    B.append(f"  BEFORE  bytes={b['bytes']}  sha256={b['sha256']}  mtime={b['mtime']}  lines(LF)={b['lf']}  crlf={b['crlf']}  endsLF={b['ends_lf']}")
    B.append(f"  AFTER   bytes={a['bytes']}  sha256={a['sha256']}  mtime={a['mtime']}  lines(LF)={a['lf']}  crlf={a['crlf']}  endsLF={a['ends_lf']}")
B.append("")
B.append("=" * 60)
B.append("PANEL key lines (M90 -> M91 -> next):")
pan = open(os.path.join(ROOT, "COVERAGE", "PANEL.md"), encoding="utf-8").read().split("\n")
for i, l in enumerate(pan):
    if "M90 补记" in l or "M91 补记" in l or (i > 250 and "M77 并表实算说明" in l):
        B.append(f"  L{i+1}: {l[:120]}")
B.append("")
B.append("coverage key lines (first 2 B3 targets):")
cov = open(os.path.join(ROOT, "COVERAGE", "coverage.tsv"), encoding="utf-8").read().split("\n")
for target in ("006C3890", "006E57A0"):
    for l in cov:
        if l.startswith(target + "\t"):
            p = l.split("\t")
            B.append(f"  {target}: grade={p[4]} hasWitness={'④ 活表槽位见证' in p[3]} hasD47={'D-47(A)' in p[3]} col4len={len(p[3])}")
            break
B.append("")
B.append("VERIFICATIONS: " + ", ".join(f"{'P' if v['pass'] else 'F'}" for v in verifs))
B.append("SIX NUMBERS: " + json.dumps(six, ensure_ascii=False))
B.append("")

with open(os.path.join(OUT, "BEFORE_AFTER.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(B))

print("WROTE MERGE_LOG.md and BEFORE_AFTER.txt")
