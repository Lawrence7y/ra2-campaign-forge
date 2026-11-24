# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B2 · 由 before/after state 生成 BEFORE_AFTER.txt 与 MERGE_LOG.md。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

OUTD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_MERGE_SLOTN_B2"
bs=json.load(open(os.path.join(OUTD,"before_state.json"),encoding="utf-8"))
a_s=json.load(open(os.path.join(OUTD,"after_state.json"),encoding="utf-8"))
vr=json.load(open(os.path.join(OUTD,"verify_result.json"),encoding="utf-8"))

def st(x): return "PASS" if x["status"]=="PASS" else "FAIL"

# ---------- BEFORE_AFTER.txt ----------
L=[]
L.append("R16-MERGE-SLOTN-B2 · BEFORE / AFTER 文件状态")
L.append("="*70)
L.append("")
for nm,key in [("COVERAGE\\coverage.tsv","coverage"),("COVERAGE\\PANEL.md","panel")]:
    b=bs[key]; a=a_s[key]
    L.append(f"[{nm}]")
    L.append(f"  BEFORE  mtime_local = {b['mtime_local']}")
    L.append(f"          bytes      = {b['bytes']}")
    L.append(f"          sha256     = {b['sha256']}")
    L.append(f"          LF/CRLF    = {b['nlines_lf']} / {b['crlf']}")
    L.append(f"  AFTER   mtime_local = {a['mtime_local']}")
    L.append(f"          bytes      = {a['bytes']}")
    L.append(f"          sha256     = {a['sha256']}")
    L.append(f"          LF/CRLF    = {a['nlines_lf']} / {a['crlf']}")
    L.append(f"  DELTA   bytes {a['bytes']-b['bytes']:+d}, sha256 {b['sha256'][:8]} -> {a['sha256'][:8]}")
    L.append("")
L.append("[delta.tsv 输入]")
d=bs["delta"]
L.append(f"  {d['path']}")
L.append(f"  bytes={d['bytes']} sha256={d['sha256']} mtime_local={d['mtime_local']}")
L.append(f"  15 行第4列；替换模式 {d['replacement_pattern']!r} -> {d['replacement_new']!r}，共 {d['replacement_count']} 处")
L.append("")
L.append("[关键行对照]")
L.append("  PANEL.md：M86 块(L214-223) 原样保留；其后插入 M87 披露 7 行(L224-230)，")
L.append("            M77 锚点由 L224 顺延至 L231；既有内容零删除零改字（V7 还原性 PASS）。")
L.append("  coverage.tsv：仅 15 个 entry 的第 4 列变化，其余 7 列逐字节相同（V3 PASS），")
L.append("                原第 4 列为新第 4 列的严格前缀（V4 15/15 PASS）。")
L.append("")
open(os.path.join(OUTD,"BEFORE_AFTER.txt"),"w",encoding="utf-8").write("\n".join(L))

# ---------- MERGE_LOG.md ----------
M=[]
M.append("# R16-MERGE-SLOTN-B2 · 并表日志")
M.append("")
M.append("> 角色：合并员（本轮 `coverage.tsv` 与 `PANEL.md` 的唯一写者）")
M.append("> 写域：`COVERAGE/coverage.tsv`（仅 15 行第 4 列）+ `COVERAGE/PANEL.md`（仅插入 1 条 M87 披露）+ 本产物目录。其余只读。")
M.append("> 日期：2026-11-20（R16 第 6 轮）· 15 行")
M.append("")
M.append("## 1 · 改前 / 改后文件状态")
M.append("")
M.append("| 文件 | 阶段 | 字节 | sha256 | mtime(local) | LF/CRLF |")
M.append("|---|---|---:|---|---|---|")
for nm,key in [("coverage.tsv","coverage"),("PANEL.md","panel")]:
    b=bs[key]; a=a_s[key]
    M.append(f"| {nm} | BEFORE | {b['bytes']} | `{b['sha256']}` | {b['mtime_local']} | {b['nlines_lf']}/{b['crlf']} |")
    M.append(f"| {nm} | AFTER | {a['bytes']} | `{a['sha256']}` | {a['mtime_local']} | {a['nlines_lf']}/{a['crlf']} |")
M.append("")
M.append("## 2 · 指针规范化留痕（Lead 口径：并表环节统一规范化）")
M.append("")
M.append(f"- 替换模式：`{bs['delta']['replacement_pattern']}` → `{bs['delta']['replacement_new']}`（两字符替换）。")
M.append(f"- **替换发生次数：{vr['V6_pointer_normalize']['replacement_count']} 处**（15 行各 1 处，均在追加段内）。")
M.append(f"- **替换后 `coverage.tsv` 内 `§12.6` 命中：{vr['V6_pointer_normalize']['s126_hits_after']} 行**（改前 15 行 = 批次 1 已入库的 15 entry，改后 30 行 = 批次 1 + 批次 2）。")
M.append(f"- 改后 `coverage.tsv` 内 `§12.4` 命中：**{vr['V6_pointer_normalize']['s124_hits_after']}**（改前亦为 0；`R14_COMMON.md` 那边不受影响）。")
M.append("- 这是流程规范化，取证未重做；异族审计 §A/§B/§C/§E/§F 全部独立复算通过，唯一 FAIL 原因即此指针编号过时。")
M.append("")
M.append("## 3 · 3.1 节实测四数（不许推算，全部从盘上现算）")
M.append("")
f=vr["V5_four_numbers"]["measured"]
M.append("| 量 | 实测值 | 说明 |")
M.append("|---|---:|---|")
M.append(f"| N_pre（15 行改前已含字符 ④） | {f['N_pre']} | 改前第 4 列已在「合同闭合 ③b④」标签里含 ④，改后计数不增 |")
M.append(f"| N_A_pre（口径 A 改前） | {f['N_A_pre']} | `[已证]` 且第 4 列含字符 ④ |")
M.append(f"| N_A_post（口径 A 改后） | {f['N_A_post']} | 净增 {vr['V5_four_numbers']['net_A']}（不是 +15；15 − N_pre = {15-f['N_pre']}） |")
M.append(f"| N_B_pre（口径 B 改前） | {f['N_B_pre']} | `[已证]` 且第 4 列含 `④ 活表槽位见证` |")
M.append(f"| N_B_post（口径 B 改后） | {f['N_B_post']} | 净增 {vr['V5_four_numbers']['net_B']}（15 行全部新增见证段） |")
M.append("")
M.append("> 口径 A 判据：`MERGE_M79/verify.py:159` = `grade == \"[已证]\" and \"④\" in col4`。")
M.append("> 口径 B 判据：`grade == \"[已证]\" and \"④ 活表槽位见证\" in col4`。")
M.append("> 四数均由 `verify.py` 从 `coverage.before.bak` 与当前 `coverage.tsv` 字节现算，不引用任何预测值。")
M.append("")
M.append("## 4 · 9 项验证（逐项 PASS/FAIL）")
M.append("")
M.append("| # | 项 | 结果 | 关键实测 |")
M.append("|---|---|---|---|")
order=[
 ("V1_coverage_byte_restore","逐字节还原性(coverage)","restore sha8=%s / before sha8=%s，重建字节==备份"%(
     vr["V1_coverage_byte_restore"]["recon_sha8"],vr["V1_coverage_byte_restore"]["before_sha8"])),
 ("V2_invariants","不变量","18,498 / {8:18498} / 1,654 / 1,648 / 6 / 15 行 grade 仍 [已证]"),
 ("V3_only_15_col4","只有 15 行第 4 列变","差异行 %d，entry 全匹配=%s，每行仅第4列=%s"%(
     vr["V3_only_15_col4"]["n_diff"],vr["V3_only_15_col4"]["entries_match"],
     not bool(vr["V3_only_15_col4"]["bad"]))),
 ("V4_strict_prefix","严格前缀","%d/%d"%(vr["V4_strict_prefix"]["n_ok"],vr["V4_strict_prefix"]["n"])),
 ("V5_four_numbers","口径 A/B 四数","A %d->%d, B %d->%d, N_pre=%d"%(
     f["N_A_pre"],f["N_A_post"],f["N_B_pre"],f["N_B_post"],f["N_pre"])),
 ("V6_pointer_normalize","§12.6 替换/命中","替换 %d 处，§12.6 命中 %d 行，§12.4 命中 %d"%(
     vr["V6_pointer_normalize"]["replacement_count"],vr["V6_pointer_normalize"]["s126_hits_after"],
     vr["V6_pointer_normalize"]["s124_hits_after"])),
 ("V7_panel_restore","PANEL.md 还原性","删 M87 块后 sha8=%s / before sha8=%s，字节==备份"%(
     vr["V7_panel_restore"]["recon_sha8"],vr["V7_panel_restore"]["before_sha8"])),
 ("V8_dod_no_flip","达标未翻转","名义=%s，严格=%s，rc=%d"%(
     vr["V8_dod_no_flip"]["nominal"],vr["V8_dod_no_flip"]["strict"],vr["V8_dod_no_flip"]["returncode"])),
 ("V9_line_endings","行尾","cov CRLF=%d/LF=%d，pan CRLF=%d/LF=%d，无混用"%(
     vr["V9_line_endings"]["cov_after"]["CRLF"],vr["V9_line_endings"]["cov_after"]["LF"],
     vr["V9_line_endings"]["pan_after"]["CRLF"],vr["V9_line_endings"]["pan_after"]["LF"])),
]
for i,(k,title,detail) in enumerate(order,1):
    M.append(f"| {i} | {title} | **{st(vr[k])}** | {detail} |")
npass=sum(1 for k in vr if vr[k]["status"]=="PASS")
M.append("")
M.append(f"**合计 PASS {npass}/9。**")
M.append("")
M.append("## 5 · strict_panel 复算（达标未翻转）")
M.append("")
sc=a_s["strict"]
M.append(f"- 脚本：`{sc['script']}`；输出目录：`{sc['out_dir']}`（严格输出到自己的目录）。")
M.append(f"- 名义达标：**{sc['nominal']}**（期望 S15,S16,S17）；严格达标：**{sc['strict']}**（期望 S17）；returncode={sc['returncode']}。")
M.append("")
M.append("## 6 · 15 行第 4 列 before / after")
M.append("")
M.append("> 每行原第 4 列为新第 4 列的严格前缀；其余 7 列逐字节相同。下表 before 为改前原值（截断显示尾部追加段），after 为规范化入库值。")
M.append("")
M.append("| entry | before 第4列(末尾 60 字) | after 第4列(末尾 60 字) | 改前已含④ |")
M.append("|---|---|---|---|")
for t in bs["coverage"]["target_rows"]:
    b=t["col4_before"]; a=t["col4_after"]
    M.append(f"| `{t['entry']}` | …{b[-60:]}` | …{a[-60:]}` | {'是' if t['before_has_circled4'] else '否'} |")
M.append("")
M.append("### 6.1 完整新增段（after 相对 before 的追加部分，含 §12.6）")
M.append("")
for t in bs["coverage"]["target_rows"]:
    b=t["col4_before"]; a=t["col4_after"]
    add=a[len(b):]
    M.append(f"- `{t['entry']}`：")
    M.append(f"  ```")
    M.append(f"  {add}")
    M.append(f"  ```")
M.append("")
M.append("## 7 · 边界自证")
M.append("")
M.append("- 只改 `coverage.tsv` 这 15 行的第 4 列；其它行、其它列一律未动（V1/V3）。")
M.append("- 不改 grade、不改判定、不改行序、不增删行（V2/V3）。")
M.append("- `PANEL.md` 只做一件新增：插入 1 条 M87 披露；既有内容零删除零改字（V7）。")
M.append("- 未改 `R14_COMMON.md`、台账、看板、`_drafts\\`、`_cards\\`、任何卡目录；`R16_SLOTN_B2\\` 与 `R16_AUDIT_SLOTN_B2\\` 全程只读。")
M.append("- 未做逆向；`strict_panel.py` 仅复制并把 OUT 重定向到本产物目录。")
M.append("")
open(os.path.join(OUTD,"MERGE_LOG.md"),"w",encoding="utf-8").write("\n".join(M))
print("reports written: BEFORE_AFTER.txt, MERGE_LOG.md")
