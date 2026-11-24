# -*- coding: utf-8 -*-
"""Generate MERGE_LOG.md and BEFORE_AFTER.txt from saved state + verify results."""
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
MY   = os.path.join(ROOT, "R16_MERGE_F1_B1")
state = json.load(open(os.path.join(MY, "merge_state.json"), encoding="utf-8"))
verify_txt = open(os.path.join(MY, "VERIFY.txt"), encoding="utf-8").read()
analysis = json.load(open(os.path.join(MY, "analysis.json"), encoding="utf-8"))
six = analysis["six_numbers"]

orig = state["original_col4"]
delta = state["delta_col4"]
entries = state["entries"]

def t(ts):
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

# ---------------- BEFORE_AFTER.txt ----------------
ba = []
ba.append("R16-MERGE-F1 / B1 — BEFORE / AFTER")
ba.append("=" * 78)
ba.append("COVERAGE\\coverage.tsv")
for tag, k in [("BEFORE", "before"), ("AFTER", "after")]:
    s = state[k]["coverage"]
    ba.append(f"  {tag:6s} mtime={s['mtime']:.6f} ({t(s['mtime'])})  bytes={s['size']:,}  sha256={s['sha256']}  lines(\\n)={s['lines']}")
ba.append(f"  delta bytes = +{state['after']['coverage']['size']-state['before']['coverage']['size']}")
ba.append("")
ba.append("COVERAGE\\PANEL.md")
for tag, k in [("BEFORE", "before"), ("AFTER", "after")]:
    s = state[k]["panel"]
    ba.append(f"  {tag:6s} mtime={s['mtime']:.6f} ({t(s['mtime'])})  bytes={s['size']:,}  sha256={s['sha256']}  lines(\\n)={s['lines']}")
ba.append(f"  delta bytes = +{state['after']['panel']['size']-state['before']['panel']['size']}")
ba.append("")
ba.append("KEY LINE COMPARISON (coverage.tsv 18 rows, col4 only):")
ba.append("-" * 78)
for e in entries:
    ba.append(f"  entry {e}")
    ba.append(f"    before[3] ({len(orig[e])} ch): {orig[e][:120]}{'...' if len(orig[e])>120 else ''}")
    ba.append(f"    after [3] ({len(delta[e])} ch): {delta[e][:120]}{'...' if len(delta[e])>120 else ''}")
ba.append("")
ba.append("KEY LINE COMPARISON (PANEL.md):")
ba.append("-" * 78)
ba.append(f"  inserted {state['insert_line_count']} lines after BEFORE line {state['insert_line_after_m88']} (immediately after M88 block)")
for ln in state["disclosure_lines"]:
    ba.append("  " + ln)
open(os.path.join(MY, "BEFORE_AFTER.txt"), "w", encoding="utf-8").write("\n".join(ba) + "\n")

# ---------------- MERGE_LOG.md ----------------
ml = []
ml.append("# R16-MERGE-F1 / B1 — MERGE LOG")
ml.append("")
ml.append("> 角色：合并员（本轮 coverage.tsv / PANEL.md 唯一写者）")
ml.append("> 批次 B1 = 派生集合按 entry 升序第 1–18 行")
ml.append("> 审计裁决：`R16_AUDIT_F1_B1/VERDICT.md` — PASS 18 / FAIL 0 / 必改 0")
ml.append("> 产物目录：`R16_MERGE_F1_B1/`  ·  PANEL 披露编号 M89（紧接 M88 块之后）")
ml.append("")
ml.append("## 0. 两份文件改前 → 改后")
ml.append("")
ml.append("| 文件 | 阶段 | mtime | 字节 | sha256 | 行数(\\n) |")
ml.append("|---|---|---|---|---|---|")
for fname in ["coverage", "panel"]:
    for tag, k in [("before", "before"), ("after", "after")]:
        s = state[k][fname]
        path = "coverage.tsv" if fname == "coverage" else "PANEL.md"
        ml.append(f"| {path} | {tag} | {s['mtime']:.3f} | {s['size']:,} | `{s['sha256']}` | {s['lines']} |")
ml.append("")
ml.append("## 1. 六个实测数（卡面 §2.1，自己实测，未照抄预测/旧值）")
ml.append("")
ml.append("| 量 | 实测值 |")
ml.append("|---|---|")
ml.append(f"| N_pre_A（18 行改前第 4 列已含 `④`） | {six['N_pre_A']} |")
ml.append(f"| N_pre_B（18 行改前第 4 列已含 `④ 活表槽位见证`，应为 0） | {six['N_pre_B']} |")
ml.append(f"| N_A_pre / N_A_post（口径 A 全表） | {six['N_A_pre']} / {six['N_A_post']}（净增 {six['netA']}） |")
ml.append(f"| N_B_pre / N_B_post（口径 B 全表） | {six['N_B_pre']} / {six['N_B_post']}（净增 {six['netB']}） |")
ml.append("")
ml.append("口径 A = `MERGE_M79/verify.py:159`：`r[4].strip()=='[已证]' and '④' in r[3]`；")
ml.append("口径 B = `[已证]` 且第 4 列含子串 `④ 活表槽位见证`。")
ml.append("")
ml.append(f"⇒ 口径 A 净增 **{six['netA']}**（不是 +18）：18 行中 {six['N_pre_A']} 行改前第 4 列已含 `④`，")
ml.append(f"   仅 4 行（`004684E0`/`004F45B0`/`00524D70`/`005F9950`）改前无 `④`；口径 B 净增 **{six['netB']}**。")
ml.append("")
ml.append("## 2. 9 项验证（卡面 §4）逐项 PASS/FAIL")
ml.append("")
ml.append("```text")
ml.append(verify_txt.rstrip())
ml.append("```")
ml.append("")
ml.append("## 3. 18 行第 4 列 before / after")
ml.append("")
ml.append("每行的 `after[3] == delta[3]`，且 `after[3].startswith(before[3])`（严格前缀 18/18）；")
ml.append("第 1/2/3/5/6/7/8 列逐字节未变（见 §2 验证 3）。")
ml.append("")
for e in entries:
    seg = delta[e][len(orig[e]):]
    ml.append(f"### {e}")
    ml.append("")
    ml.append(f"- before[3]（{len(orig[e])} ch）: `{orig[e]}`")
    ml.append(f"- after[3]（{len(delta[e])} ch）: `{delta[e]}`")
    ml.append(f"- 追加段（{len(seg)} ch）: `{seg}`")
    ml.append("")
open(os.path.join(MY, "MERGE_LOG.md"), "w", encoding="utf-8").write("\n".join(ml) + "\n")

print("WROTE BEFORE_AFTER.txt", os.path.getsize(os.path.join(MY, "BEFORE_AFTER.txt")))
print("WROTE MERGE_LOG.md", os.path.getsize(os.path.join(MY, "MERGE_LOG.md")))
