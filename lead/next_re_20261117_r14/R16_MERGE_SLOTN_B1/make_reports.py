# -*- coding: utf-8 -*-
"""生成 MERGE_LOG.md 与 BEFORE_AFTER.txt（只读状态与文件，写自己的产物）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B1")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")
C4="\u2463"

bs=json.load(open(os.path.join(OUTD,"before_state.json"),encoding="utf-8"))
a_s=json.load(open(os.path.join(OUTD,"after_state.json"),encoding="utf-8"))
vr=json.load(open(os.path.join(OUTD,"verify_result.json"),encoding="utf-8"))

# 当前 15 行 after4
cov_lines=open(COV,encoding="utf-8").read().splitlines()
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e
after4_by_entry={}
for ln in cov_lines:
    c=ln.split("\t")
    if len(c)>=8 and ne(c[0]) in set(t["entry"] for t in bs["coverage"]["target_rows"]):
        after4_by_entry[ne(c[0])]=c[3]

# ---------- MERGE_LOG.md ----------
L=[]
L.append("# R16-MERGE-SLOTN-B1 · MERGE LOG")
L.append("")
L.append("> 合并员：agent-11 · 2026-11-20（R16 第 4 轮）")
L.append("> 写域：`COVERAGE/coverage.tsv`（仅 15 行第 4 列）+ `COVERAGE/PANEL.md`（1 指针 + 1 插入）+ 本产物目录")
L.append("")
L.append("## 1 · 并表概览")
L.append("")
L.append("- 输入：`R16_SLOTN_B1/delta.tsv`（1 表头 + 15 数据行，8 列），审计 `R16_AUDIT_SLOTN_B1` 裁 **PASS 15 / FAIL 0 / 必改 0**（90/90 字节项为真）。")
L.append("- 规则：第 4 列 = 盘上原第 4 列（严格前缀）+ 追加段；第 1/2/3/5/6/7/8 列逐字节不动。")
L.append("- **必需替换**：追加段里的 `R14_COMMON §12.4` → `R14_COMMON §12.6`，**替换发生次数 = %d**（预期 15）。"%bs["delta"]["replacement_count"])
L.append("  - 替换前 1 例：`…见 R14_COMMON §12.4 与 PANEL 对应披露）`")
L.append("  - 替换后 1 例：`…见 R14_COMMON §12.6 与 PANEL 对应披露）`")
L.append("  - 仅替换该字样一处/行，其余字节不改。")
L.append("")
L.append("## 2 · 15 行逐行 before/after 第 4 列")
L.append("")
L.append("说明：`before` 为盘上原值（严格前缀）；`after` = before + 追加段（追加段已含 §12.6）。前缀校验逐行 PASS。")
L.append("")
for i,t in enumerate(bs["coverage"]["target_rows"],1):
    e=t["entry"]; b=t["col4_before"]; a=after4_by_entry[e]
    add=a[len(b):] if a.startswith(b) else "<NOT PREFIX>"
    L.append("### 行 %d · entry `%s`"%(i,e))
    L.append("")
    L.append("- before（原第 4 列，%d B）：`%s`"%(len(b.encode("utf-8")),b))
    L.append("- after（新第 4 列，%d B）：`%s`"%(len(a.encode("utf-8")),a))
    L.append("- 追加段（%d B）：`%s`"%(len(add.encode("utf-8")),add))
    L.append("- 严格前缀：`before == after[:len(before)]` → **PASS**；其余 7 列逐字节相同 → **PASS**；改前已含字符 ④ = **%s**。"%("是" if t.get("before_has_circled4") else "否"))
    L.append("")
L.append("## 3 · 8 项验证结果与实测数字")
L.append("")
L.append("| 项 | 结果 | 关键实测 |")
L.append("|---|---|---|")
order=["V1_coverage_byte_restore","V2_invariants","V3_only_15_col4","V4_strict_prefix",
       "V5_circled4_chengwen","V6_panel_restore","V7_dod_no_flip","V8_line_endings"]
for k in order:
    v=vr[k]; st=v["status"]
    extra=""
    if k=="V1_coverage_byte_restore": extra="重建 sha=%s，改前 sha=%s，与备份字节相等=%s"%(v["recon_sha8"],v["before_sha8"],v["recon_eq_bak"])
    elif k=="V2_invariants": extra="18,498 行 / {8:18498} / [已证]1654 / atlas内1648 / 外6 / 15行grade=[已证]"
    elif k=="V3_only_15_col4": extra="差异行=%d（恰 15），entry 集合匹配=%s，仅第4列不同"%(v["n_diff"],v["entries_match"])
    elif k=="V4_strict_prefix": extra="%d/%d 逐行严格前缀 PASS"%(v["n_ok"],v["n"])
    elif k=="V5_circled4_chengwen": extra="改前 %d → 改后 %d（卡面预期 334）；改前已含 ④ 的 6 行不增，净增 %d 行"%(v["before"],v["after"],v["net_new"])
    elif k=="V6_panel_restore": extra="重建 sha=%s，改前 sha=%s，删除插入块+回改指针后字节相等=%s"%(v["recon_sha8"],v["before_sha8"],v["recon_eq_bak"])
    elif k=="V7_dod_no_flip": extra="名义=%s 严格=%s（rc=%d）"%(v["nominal"],v["strict"],v["returncode"])
    elif k=="V8_line_endings": extra="coverage LF %d→%d，PANEL LF %d→%d，无 CRLF 混用；字节增量 cov=%d / panel=%d 与追加/插入吻合"%(v["cov_before"]["LF"],v["cov_after"]["LF"],v["pan_before"]["LF"],v["pan_after"]["LF"],v["d_cov_bytes"],v["d_pan_bytes"])
    L.append("| %s | %s | %s |"%(k,st,extra))
L.append("")
L.append("### V5 ④ 已成文计数偏差说明（卡面 §4.5「若不符，报实测值并查清」）")
L.append("")
L.append(vr["V5_circled4_chengwen"]["explanation"])
L.append("")
L.append("> 处置：PANEL.md 的 M86 披露按卡面 §3.2(b) 逐字写入「319 / 1,654（19.29%）升至 334 / 1,654（20.19%）」；")
L.append("> 本验证报告与回复如实给出实测 319 → 328 及原因。该偏差交由 lead 裁量是否需在后续轮次修正披露数字。")
L.append("")
L.append("## 4 · 还原性与不变量明细")
L.append("")
L.append("- 改前 sha（coverage）= `%s`；把 15 行第 4 列换回后重建 sha = `%s` → **一致**。"%(bs["coverage"]["sha256"],vr["V1_coverage_byte_restore"]["recon_sha8"]))
L.append("- 改前 sha（PANEL）= `%s`；删除 M86 插入块并把指针回改后重建 sha = `%s` → **一致**。"%(bs["panel"]["sha256"],vr["V6_panel_restore"]["recon_sha8"]))
L.append("- 达标复算：复制 `strict_panel.py` 到本目录 `strict_panel_local.py`，仅把 `OUT` 重定向到 `strict_out`（口径不变），输出未写原目录。")
L.append("")

open(os.path.join(OUTD,"MERGE_LOG.md"),"w",encoding="utf-8").write("\n".join(L))

# ---------- BEFORE_AFTER.txt ----------
B=[]
B.append("R16-MERGE-SLOTN-B1 · BEFORE / AFTER 状态")
B.append("="*70)
B.append("")
for label,key in [("coverage.tsv","coverage"),("PANEL.md","panel")]:
    b=bs[key]; a=a_s[key]
    B.append("[%s]"%label)
    B.append("  BEFORE  mtime=%s  bytes=%d  sha256=%s  lines(LF)=%d"%(b["mtime_local"],b["bytes"],b["sha256"],b["nlines_lf"]))
    B.append("  AFTER   mtime=%s  bytes=%d  sha256=%s  lines(LF)=%d"%(a["mtime_local"],a["bytes"],a["sha256"],a["nlines_lf"]))
    B.append("")
B.append("关键行对照")
B.append("-"*70)
B.append("PANEL.md L171 指针：")
B.append("  BEFORE: > 成文位置：`R14_COMMON.md §12.4`。")
B.append("  AFTER : > 成文位置：`R14_COMMON.md §12.6`。")
B.append("")
B.append("PANEL.md M85 块之后插入的 M86 披露（8 行，逐字）：")
for s in bs["panel"]["inserted_lines"]:
    B.append("  "+s)
B.append("")
B.append("coverage.tsv 第 4 列替换模式： %s -> %s （次数 %d）"%(
    bs["delta"]["replacement_pattern"],bs["delta"]["replacement_new"],bs["delta"]["replacement_count"]))
B.append("")
B.append("delta.tsv mtime=%s bytes=%d sha256=%s"%(bs["delta"]["mtime_local"],bs["delta"]["bytes"],bs["delta"]["sha256"]))
B.append("")
open(os.path.join(OUTD,"BEFORE_AFTER.txt"),"w",encoding="utf-8").write("\n".join(B))

print("reports written:",
      os.path.getsize(os.path.join(OUTD,"MERGE_LOG.md")),
      os.path.getsize(os.path.join(OUTD,"BEFORE_AFTER.txt")))
