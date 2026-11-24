# -*- coding: utf-8 -*-
"""Generate MERGE_LOG.md from measured states + verify_result.json (own dir only)."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B3")
bs=json.load(open(os.path.join(OUTD,"before_state.json"),encoding="utf-8"))
a_s=json.load(open(os.path.join(OUTD,"after_state.json"),encoding="utf-8"))
vr=json.load(open(os.path.join(OUTD,"verify_result.json"),encoding="utf-8"))

L=[]
def w(s=""): L.append(s)

w("# R16-MERGE-SLOTN-B3 · MERGE_LOG")
w()
w("> 角色：合并员（`work/cn:hy4flash-free`）—— 本轮 `coverage.tsv` 与 `PANEL.md` 的唯一写者")
w("> 输入：`R16_SLOTN_B3/delta.tsv`（13 行）+ `R16_AUDIT_SLOTN_B3/VERDICT.md`（13 PASS / 0 FAIL / 0 必改；指针 13/13 已是 §12.6，本批无需规范化）")
w("> 硬边界：只改 coverage.tsv 这 13 行第 4 列；PANEL.md 只插入 1 条 M88 披露，既有内容零删除零改字；不改 R14_COMMON/台账/看板/_drafts/_cards；卡目录只读；不做逆向。")
w()
w("## 1. 改前 → 改后（盘上实测）")
w()
w("| 文件 | mtime(本地) | 字节 | sha256 | 行数(LF) | 行尾 |")
w("|---|---|---:|---|---:|---|")
for label in ("coverage","panel"):
    b=bs[label]; a=a_s[label]
    w("| %s 改前 | %s | %d | %s | %d | CRLF=%d LF=%d CR=%d BOM=%s ends_nl=%s |" %
      (label,b["mtime_local"],b["bytes"],b["sha256"],b["lines_nl"],b["CRLF"],b["LF"],b["CR"],b["BOM"],b["ends_nl"]))
    w("| %s 改后 | %s | %d | %s | %d | CRLF=%d LF=%d CR=%d BOM=%s ends_nl=%s |" %
      (label,a["mtime_local"],a["bytes"],a["sha256"],a["lines_nl"],a["CRLF"],a["LF"],a["CR"],a["BOM"],a["ends_nl"]))
w()
w("- 两份文件改前均为 **纯 LF、无 BOM**；改后行尾形态未变、未引入混用（V9）。")
w("- 改前基线不变量（自算）：数据行 18,498 / 列分布 {8:18498} / `[已证]` 1,654 / atlas 内 1,648 / atlas 外 6 —— 与卡面 §2 一致；改后须仍成立（V2）。")
w()

w("## 2. 口径 A/B 五个实测数（卡面 §2.1，绝不照抄预测或旧值）")
w()
m=bs["measured"]
w("| 量 | 实测值 | 说明 |")
w("|---|---:|---|")
w("| `N_pre` | %d | 13 行里改前第 4 列已含字符 `④` 的行数（%s） |" %
  (m["N_pre"], "、".join("`%s`"%e for e in m["pre_circled4_entries"])))
w("| `N_A_pre` → `N_A_post` | %d → %d | 全表口径 A（`[已证]` 且第 4 列含字符 `④`），净增 %+d |" %
  (m["N_A_pre"],m["N_A_post"],m["N_A_post"]-m["N_A_pre"]))
w("| `N_B_pre` → `N_B_post` | %d → %d | 全表口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`），净增 %+d |" %
  (m["N_B_pre"],m["N_B_post"],m["N_B_post"]-m["N_B_pre"]))
w()
w("- 口径 A 判据原文：`MERGE_M79/verify.py:159` → `sum(1 for r in rows if r[4].strip()=='[已证]' and '④' in r[3])`；口径 B：第 4 列含子串 `④ 活表槽位见证`。")
w("- 五个数改前从 `coverage.before.bak` 字节现算、改后从当前 `coverage.tsv` 字节现算；`N_pre=3` 的 3 行均为「合同闭合 ③b④」分类标签里已有 `④`，故 A 净增 = 13 − 3 = 10（非 +13），B 净增 = 13。")
w("- M88 披露里的所有数字即本节实测值。")
w()

w("## 3. 13 行第 4 列 before → after")
w()
w("> 严格前缀 13/13；其余第 1/2/3/5/6/7/8 列逐字节相同；13 行 grade 改前改后均 `[已证]`。")
w()
for i,t in enumerate(bs["coverage"]["target_rows"],1):
    w("### %d. `%s` %s" % (i,t["entry"],t["name"]))
    w("- BEFORE 第 4 列：")
    w("  ```text")
    w("  "+t["col4_before"])
    w("  ```")
    w("- AFTER 第 4 列：")
    w("  ```text")
    w("  "+t["col4_after"])
    w("  ```")
    w("- 追加段（%d B）：`%s`" % (t["added_bytes"],t["append_seg"]))
    w("- 追加段内 `§12.6` 命中 %d / `§12.4` 命中 %d；改前已含 `④`=%s、已含 `④ 活表槽位见证`=%s。" %
      (t["append_s126_hits"],t["append_s124_hits"],t["before_has_circled4"],t["before_has_witness"]))
    w()
w("## 4. PANEL.md M88 披露（插于 M87 块后、M77 锚点前，共 %d 行）" % a_s["panel"]["m87_block_lines"] if False else "## 4. PANEL.md M88 披露（插于 M87 块之后，共 %d 行）" % len(bs["panel"]["inserted_lines"]))
w()
for l in bs["panel"]["inserted_lines"]: w(l)
w()
w("> 既有内容零删除零改字：删掉上述 M88 块后重建 sha256 == 改前 sha256（V7）。")
w()

w("## 5. 10 项验证逐项 PASS/FAIL 与实际数字")
w()
w("| 项 | 结果 | 关键实测 |")
w("|---|---|---|")
labels=[
 ("V1_coverage_byte_restore","逐字节还原性（coverage.tsv）","recon_sha8=%s / before_sha8=%s / recon_eq_bak=%s / locate=%s" %
   (vr["V1_coverage_byte_restore"]["recon_sha8"],vr["V1_coverage_byte_restore"]["before_sha8"],
    vr["V1_coverage_byte_restore"]["recon_eq_bak"],vr["V1_coverage_byte_restore"]["ok_locate"])),
 ("V2_invariants","不变量","data_rows=%d coldist=%s 已证=%d atlas内=%d atlas外=%d 13行[已证]=%s" %
   (vr["V2_invariants"]["measured"]["data_rows"],vr["V2_invariants"]["measured"]["coldist"],
    vr["V2_invariants"]["measured"]["yizheng"],vr["V2_invariants"]["measured"]["atlas_in"],
    vr["V2_invariants"]["measured"]["atlas_out"],vr["V2_invariants"]["grades_yizheng_13"])),
 ("V3_only_13_col4","只有 13 行第 4 列变了","diff=%d 期望=13 entry匹配=%s 每行仅col4=%s" %
   (vr["V3_only_13_col4"]["n_diff"],vr["V3_only_13_col4"]["entries_match"],not vr["V3_only_13_col4"]["bad"])),
 ("V4_strict_prefix","严格前缀","%d/%d" % (vr["V4_strict_prefix"]["n_ok"],vr["V4_strict_prefix"]["n"])),
 ("V5_five_numbers","口径 A/B 五个数",str(vr["V5_five_numbers"]["measured"])+" net_A=%+d net_B=%+d consistent=%s" %
   (vr["V5_five_numbers"]["net_A"],vr["V5_five_numbers"]["net_B"],vr["V5_five_numbers"]["consistent"])),
 ("V6_pointer_counts","§12.6/§12.4 命中计数","13行内 %d/%d；全表 §12.6 lines %d→%d hits %d→%d；§12.4 %d→%d" %
   (vr["V6_pointer_counts"]["append_13_s126"],vr["V6_pointer_counts"]["append_13_s124"],
    vr["V6_pointer_counts"]["whole_before_s126_lines"],vr["V6_pointer_counts"]["whole_after_s126_lines"],
    vr["V6_pointer_counts"]["whole_before_s126_hits"],vr["V6_pointer_counts"]["whole_after_s126_hits"],
    vr["V6_pointer_counts"]["whole_before_s124_hits"],vr["V6_pointer_counts"]["whole_after_s124_hits"])),
 ("V7_panel_restore","PANEL.md 还原性","recon_sha8=%s / before_sha8=%s / recon_eq_bak=%s / 删除M88=%s / 块行数=%d" %
   (vr["V7_panel_restore"]["recon_sha8"],vr["V7_panel_restore"]["before_sha8"],
    vr["V7_panel_restore"]["recon_eq_bak"],vr["V7_panel_restore"]["ok_insert_removed"],
    vr["V7_panel_restore"]["m88_block_lines"])),
 ("V8_dod_no_flip","达标未翻转","名义=%s 严格=%s rc=%d" %
   (vr["V8_dod_no_flip"]["nominal"],vr["V8_dod_no_flip"]["strict"],vr["V8_dod_no_flip"]["returncode"])),
 ("V9_line_endings","行尾","cov CRLF/LF/CR=%d/%d/%d pan=%d/%d/%d；d_cov_bytes=%d d_pan_bytes=%d；未混用=%s" %
   (vr["V9_line_endings"]["cov_after"]["CRLF"],vr["V9_line_endings"]["cov_after"]["LF"],vr["V9_line_endings"]["cov_after"]["CR"],
    vr["V9_line_endings"]["pan_after"]["CRLF"],vr["V9_line_endings"]["pan_after"]["LF"],vr["V9_line_endings"]["pan_after"]["CR"],
    vr["V9_line_endings"]["d_cov_bytes"],vr["V9_line_endings"]["d_pan_bytes"],
    not vr["V9_line_endings"]["cov_mixed"] and not vr["V9_line_endings"]["pan_mixed"])),
 ("V10_slotN43_closeout","43 行收官核对","slotN43 entries=%d 命中行=%d unique=%d missing=%s" %
   (vr["V10_slotN43_closeout"]["slotn_entries_in_file"],vr["V10_slotN43_closeout"]["closeout_rows"],
    vr["V10_slotN43_closeout"]["closeout_unique"],vr["V10_slotN43_closeout"]["missing"])),
]
for k,title,detail in labels:
    st=vr[k]["status"]
    w("| %s（%s） | **%s** | %s |" % (title,k,st,detail))
npass=sum(1 for k in vr if vr[k]["status"]=="PASS")
w()
w("**合计：PASS %d / 10，FAIL %d。**" % (npass,10-npass))
w()

w("## 6. 达标集合与边界声明")
w()
w("- strict_panel 口径复算：脚本 `strict_panel_local.py`（`RULING_R15_20261119/work/strict_panel.py` 副本，仅 `OUT` 改到本目录 `strict_out/`）；名义 **S15,S16,S17**（3/22），严格 **S17**（1/22）—— 未翻转。")
w("- 43 行收官：全表第 4 列含 `④ 活表槽位见证` 且 entry ∈ `PROBE_802/slotN43.tsv` 的行 = **43/43**（三批 15+15+13 全覆盖，`slotN` 类已无剩余可补）。")
w("- 本批 2 处合法改选（005B3570 / 005B35E0）已在 M88 披露中知情引用；审计两行判成立。")
w("- 未改 R14_COMMON.md / 台账 / 看板 / `_drafts` / `_cards` / 任何卡目录；未做逆向；strict_panel 输出只在本目录。")
w("- 产物：`MERGE_LOG.md`、`verify.py`、`BEFORE_AFTER.txt`、`before_state.json`、`after_state.json`、`verify_result.json`、`coverage.before.bak`、`PANEL.before.bak`、`merge.py`、`strict_panel_local.py`、`strict_out/`、`measure_pre.py/json`。")

with open(os.path.join(OUTD,"MERGE_LOG.md"),"w",encoding="utf-8") as f:
    f.write("\n".join(L)+"\n")
print("MERGE_LOG.md written, lines=%d, PASS=%d/10"%(len(L),npass))
