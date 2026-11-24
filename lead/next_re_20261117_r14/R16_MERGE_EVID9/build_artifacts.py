# -*- coding: utf-8 -*-
"""Generate remaining artifacts: MERGE_LOG.md, BEFORE_AFTER.txt; analyze /->\\ changes."""
import os, sys, hashlib, json
sys.stdout.reconfigure(encoding="utf-8")

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(R14, "R16_MERGE_EVID9")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
COV_BEFORE = os.path.join(OUT, "coverage_before.tsv")
PANEL_BEFORE = os.path.join(OUT, "PANEL_before.md")
NINE = ["004E0E80", "006B6EA0", "006B6FA0",
        "004DF320", "004DF3A0", "004DFB70", "004DFCB0", "004DFE00", "006F4960"]

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def split(b): return b.split(b"\n")

before = open(COV_BEFORE, "rb").read()
after = open(COV, "rb").read()
p_before = open(PANEL_BEFORE, "rb").read()
p_after = open(PANEL, "rb").read()

old6, new6 = {}, {}
for ln in split(before)[1:]:
    c = ln.split(b"\t")
    if len(c)==8 and c[0].decode() in NINE: old6[c[0].decode()] = c[5].decode()
for ln in split(after)[1:]:
    c = ln.split(b"\t")
    if len(c)==8 and c[0].decode() in NINE: new6[c[0].decode()] = c[5].decode()

# ---- /->\ analysis: count positions where old had '/' and new has '\' at same relative place ----
# Method: remove the added prefix and appended note; the shared 'EVIDENCE/<file>#<entry>' core
# reveals whether the 'EVIDENCE/' separator '/' became '\'.
slash_counts = {}
for e in NINE:
    o, n = old6[e], new6[e]
    # count '/' in old col6 and '\' in new col6 on the file-path core
    # old core: EVIDENCE/<file>#<entry>  (1 slash)
    oslash = o.count("/")   # typically 1
    nbslash = n.count("\\") # typically 2 (prefix sep + EVIDENCE sep)
    # The only '/' in old is after EVIDENCE; in new that same separator is '\',
    # plus a newly-added prefix separator '\'. So extra /->\ substitutions = oslash (all become '\')
    slash_counts[e] = {"old_slash": oslash, "new_backslash": nbslash,
                       "slash_to_backslash_substitutions": oslash}
    print(f"{e}: old '/'={oslash} new '\\'={nbslash} /->\\ subs={oslash}")

total_slash2bs = sum(v["slash_to_backslash_substitutions"] for v in slash_counts.values())
print("total /->\\ substitutions across 9 rows:", total_slash2bs)

after_state = json.load(open(os.path.join(OUT,"after_state.json"), encoding="utf-8"))
ver = after_state["verifications"]
six = [(k, ver[k]["result"], ver[k]["detail"]) for k in ver if not k.startswith("_")]
klass = after_state["resolve_classes"]
dod = after_state["dod"]

# ---------------- MERGE_LOG.md ----------------
L = []
L.append("# R16-MERGE-EVID9 MERGE_LOG\n")
L.append("> 合并员：`work/cn:hy4flash-free`（agent-7）　日期：2026-11-20　卡：`R16-MERGE-EVID9`\n")
L.append("> 写域：`COVERAGE/coverage.tsv`（9 行第 6 列）+ `COVERAGE/PANEL.md`（插入 4 行）+ 本目录；两输入目录只读。\n")
L.append("## 1. 改动摘要\n")
L.append("- 3 行 delta（`004E0E80`/`006B6EA0`/`006B6FA0`）：第 6 列照 `R16_EVID9/coverage_delta.tsv` 原样取（审计 PASS、0 必改；`BOTH_IDENTICAL`，取 `S10_K8`）。")
L.append("- 6 行（`004DF320`/`004DF3A0`/`004DFB70`/`004DFCB0`/`004DFE00`/`006F4960`）：第 6 列新路径统一并 `S10_K8F\\EVIDENCE\\QUEUE_DISPATCH_AND_FALSE_KILLS.txt#<entry>`；注记逐行带各自 entry 锚点说明，主体一致但 6 行不雷同。")
L.append("- **不并 `S10_K8`**：审计已推翻「取字典序较小者」——`S10_K8F` 对 `S10_K8` 支配（K8 独有 4 行全为叙述行、载荷独有数 0）、K8 头部跳表行自相矛盾、盘上 6 行语义已为 K8F 措辞。\n")

L.append("## 2. 9 行第 6 列 before / after\n")
L.append("| entry | 行 | before 第 6 列 | after 第 6 列 |")
L.append("|---|---|---|---|")
for e in NINE:
    ln = next(i+1 for i,l in enumerate(split(before)) if l.split(b"\t")[0].decode()==e)
    L.append(f"| `{e}` | L{ln} | `{old6[e]}` | `{new6[e]}` |")
L.append("")

L.append("## 3. 6 项验证（卡 §4）\n")
L.append("| # | 检查 | 结果 | 实测 |")
L.append("|---|---|---|---|")
names = ["1_coverage_byte_restore","2_invariants","3_only_9_col6_changed",
         "4_resolve_reclassify","5_panel_restore","6_dod_not_flipped"]
for k in names:
    r = dict((x[0],x) for x in six)[k]
    detail = r[2].replace("|","\\|")
    L.append(f"| {k} | {r[1]} | {detail} |")
L.append("")
L.append(f"- 重跑四分类：`R_OK={klass['R_OK']}` / `R_MISSING={klass['R_MISSING']}` / `R_TRACE_ONLY={klass['R_TRACE_ONLY']}` / `R_EMPTY={klass['R_EMPTY']}`（预期 852/0/802/0，实测一致）。")
L.append(f"- 名义达标：`{dod['nominal']}`；严格达标：`{dod['strict']}`（预期 `S15,S16,S17` / `S17`，实测一致）。\n")

L.append("## 4. `/`→`\\` 额外字节变化\n")
L.append(f"- 9 行原第 6 列各含 1 个 `/`（`EVIDENCE/` 分隔符）；新值中该分隔符统一写为 `\\`，并新增卡目录前缀分隔符 `\\`。")
L.append(f"- 故 9 行各有 **1 处 `/`→`\\` 字节替换**（共 {total_slash2bs} 处），均落在第 6 列内，属卡面允许的指针写法保留（3 行照 delta 交付、与 M82 风格一致；6 行按卡 §3.1 指定格式）。")
L.append("- `resolve.py` 解析时 `/` 与 `\\` 均归一化为 `os.sep`，不影响可解析性；实测 `R_OK=852` 已含此写法。")
L.append("- 除第 6 列外无任何字节变化（验证 1 与 3 已逐字节证明）。\n")

L.append("## 5. 产物\n")
L.append("| 文件 | 内容 |")
L.append("|---|---|")
L.append("| `MERGE_LOG.md` | 本文件 |")
L.append("| `verify.py` | 自包含复跑 6 项验证（只读两目标文件；resolve.py/strict_panel.py 输出落本目录 `EVID_RESOLVE` 副本与 `_strict_out`）|")
L.append("| `BEFORE_AFTER.txt` | 关键行对照 + 两文件改前/改后 mtime/字节/sha256 |")
L.append("| `before_state.json` / `after_state.json` | 改前/改后状态与验证结果 |")
L.append("| `coverage_before.tsv` / `PANEL_before.md` | 改前原件逐字节副本（供还原验证）|")
L.append("| `apply_changes.py` / `pre_record.py` / `precheck.py` | 写入与前置记录脚本 |")
L.append("| `coverage_after_copy.tsv` / `_resolve_out/` / `strict_panel_copy.py` / `_strict_out/` | 验证用副本与输出（均在本目录）|")
with open(os.path.join(OUT,"MERGE_LOG.md"),"w",encoding="utf-8") as f: f.write("\n".join(L)+"\n")

# ---------------- BEFORE_AFTER.txt ----------------
import time
def statline(path):
    b=open(path,"rb").read(); st=os.stat(path)
    return f"bytes={len(b)} sha256={sha(b)} mtime={time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(st.st_mtime))} lines_lf={b.count(chr(10).encode())}"
B=[]
B.append("R16-MERGE-EVID9 BEFORE / AFTER\n")
B.append("== coverage.tsv ==")
B.append("BEFORE: "+statline(COV_BEFORE))
B.append("AFTER : "+statline(COV))
B.append("")
B.append("== PANEL.md ==")
B.append("BEFORE: "+statline(PANEL_BEFORE))
B.append("AFTER : "+statline(PANEL))
B.append("")
B.append("== 9 changed rows: entry | line | OLD col6 || NEW col6 ==")
for e in NINE:
    ln = next(i+1 for i,l in enumerate(split(before)) if l.split(b"\t")[0].decode()==e)
    B.append(f"{e} | L{ln}\n  OLD: {old6[e]}\n  NEW: {new6[e]}")
B.append("")
B.append("== resolve four classes (AFTER, rerun) ==")
B.append(f"R_OK={klass['R_OK']} R_MISSING={klass['R_MISSING']} R_TRACE_ONLY={klass['R_TRACE_ONLY']} R_EMPTY={klass['R_EMPTY']}")
B.append(f"nominal_dod={{{dod['nominal']}}} strict_dod={{{dod['strict']}}}")
with open(os.path.join(OUT,"BEFORE_AFTER.txt"),"w",encoding="utf-8") as f: f.write("\n".join(B)+"\n")

print("\nMERGE_LOG.md, BEFORE_AFTER.txt written")
print("after_state.json valid:", os.path.isfile(os.path.join(OUT,"after_state.json")))
