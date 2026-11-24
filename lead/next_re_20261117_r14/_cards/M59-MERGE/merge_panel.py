# -*- coding: utf-8 -*-
"""M59: edit PANEL.md. Cell-level, line-number targeted, with strict guards."""
import os, sys

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
LOG = os.path.join(ROOT, "_cards", "M59-MERGE", "PANEL_EDIT_LOG.txt")

NOTE = ("M59 并表 S15S16_3B2 审计 PASS 7 行（S15 006E3DB0/006E4660/006E5730/006E6080/006E6410/00727240 "
        "+ S16 006CE800，[静态推断]→[已证]，语义取 delta 原文、evidence_path 改指 S15S16_3B2/_audit/VERDICT.md；"
        "同卡 4 行 006E3E30/006E56E0/006E57A0/007276A0 审计 FAIL 整行拒绝；006E6080 不在 atlas 故 A 口径仅 +6）")

with open(PANEL, "r", encoding="utf-8", newline="") as f:
    raw = f.read()
assert "\r" not in raw
parts = raw.split("\n")
assert parts[-1] == ""  # ends with one LF
lines = parts[:-1]
assert len(lines) == 503, len(lines)

orig = list(lines)
log = []

def set_cell(lineno, old_cells, new_cells, tag):
    idx = lineno - 1
    cur = lines[idx].split(" | ")
    assert cur == old_cells, (tag, lineno, len(cur), len(old_cells))
    lines[idx] = " | ".join(new_cells)
    log.append("EDITED line %d (%s)" % (lineno, tag))

# ---- Table 1: 覆盖面板 ----
# L69 S15: proved_n 101->106, proved_pct 63.92->67.09, append NOTE to DoD gap cell
c = lines[68].split(" | ")
assert c[0] == "| S15" and c[8] == "101" and c[9] == "63.92", c[:11]
c[8], c[9] = "106", "67.09"
assert c[-1].endswith(" |")
c[-1] = c[-1][:-2] + " " + NOTE + " |"
lines[68] = " | ".join(c)
log.append("EDITED L69 S15: proved 101->106, pct 63.92->67.09, note appended")

# L70 S16: proved 46->47, pct 51.11->52.22, append NOTE
c = lines[69].split(" | ")
assert c[0] == "| S16" and c[8] == "46" and c[9] == "51.11", c[:11]
c[8], c[9] = "47", "52.22"
assert c[-1].endswith(" |")
c[-1] = c[-1][:-2] + " " + NOTE + " |"
lines[69] = " | ".join(c)
log.append("EDITED L70 S16: proved 46->47, pct 51.11->52.22, note appended")

# L77 TOTAL: atlas-in proved 1484->1490, pct 11.49->11.54; prepend M59 clause + append NOTE
c = lines[76].split(" | ")
assert c[0] == "| **TOTAL**" and c[8] == "**1484**" and c[9] == "**11.49**", c[:11]
c[8], c[9] = "**1490**", "**11.54**"
M59_TOTAL = ("M59 +7（S15S16_3B2 审计 PASS 7 行：S15 +6/S16 +1，其中 006E6080 atlas 外）："
             "全表 [已证] 1,489→1,496、atlas 内 1,484→1,490、atlas 外 5→6；"
             "TOTAL proved_pct 11.49→11.54（实算 1,490/12,916=11.5361%→11.54）；named/L/strict 各列不变。")
assert c[-1].endswith(" |")
c[-1] = M59_TOTAL + " " + c[-1][:-2] + " " + NOTE + " |"
lines[76] = " | ".join(c)
log.append("EDITED L77 TOTAL: proved 1484->1490, pct 11.49->11.54, M59 clause prepended + note appended")

# ---- Table 2: 严格口径双列表 ----
# L119 S15 strict: proved 101->106, pct 63.92->67.09, strict 48->53, strict_pct 30.38->33.54
c = lines[118].split(" | ")
assert c[0] == "| S15" and c[2] == "101" and c[3] == "63.92" and c[4] == "**48**" and c[5] == "**30.38**", c
c[2], c[3], c[4], c[5] = "106", "67.09", "**53**", "**33.54**"
lines[118] = " | ".join(c)
log.append("EDITED L119 strict S15: 101->106, 63.92->67.09, 48->53, 30.38->33.54")

# L120 S16 strict: proved 46->47, pct 51.11->52.22, strict 20->21, strict_pct 22.22->23.33
c = lines[119].split(" | ")
assert c[0] == "| S16" and c[2] == "46" and c[3] == "51.11" and c[4] == "**20**" and c[5] == "**22.22**", c
c[2], c[3], c[4], c[5] = "47", "52.22", "**21**", "**23.33**"
lines[119] = " | ".join(c)
log.append("EDITED L120 strict S16: 46->47, 51.11->52.22, 20->21, 22.22->23.33")

# ---- Table 3: M47 复算 table ----
# L183 S15: proved 101->106
c = lines[182].split(" | ")
assert c[0] == "| S15" and c[5] == "101", c
c[5] = "106"
lines[182] = " | ".join(c)
log.append("EDITED L183 M47-table S15: proved 101->106")

# L184 S16: proved 46->47
c = lines[183].split(" | ")
assert c[0] == "| S16" and c[5] == "46", c
c[5] = "47"
lines[183] = " | ".join(c)
log.append("EDITED L184 M47-table S16: proved 46->47")

# ---- Append M59 section at end ----
FAIL_REASONS = [
    ("006E3E30", "entry=006E3E30：call 0x00410320@0x006E3E3F/test/jl 地址全真且被调可伪证(E_POINTER@0x0041032B vs 成功 ret 0xC@0x00410374)，但 006E3E30 全体 29 字节纯转发壳：两路径汇于同一条 ret 0xC@0x006E3E4A 仅差 eax 值，主张的\"成功路径继续对象初始化\"在本行字节中不存在(fall-through 仅 xor eax,eax@0x006E3E48 两条)，系同族模板假句，查3不成立"),
    ("006E56E0", "entry=006E56E0：主张的检查点不成立——call 0x004A1D50@0x006E56FD 之后 0x006E5702 有 mov eax,[esi+0x28](8B 46 28) 先覆写 eax，0x006E5705 的 test 测的是成员字段而非被调返回；被调 0x004A1D50 实为 CRC-4 累加壳(0x004A1DE0 CRC32 表 0x81F7B4，返回 CRC 值@0x004A1F97)，其返回仅作 CRC 输入从不分支；且 je 目标 0x006E571B 为共享尾部(fall-through 走完同样汇入)，主张的可伪证哨兵契约在 006E56E0 字节层不存在"),
    ("006E57A0", "entry=006E57A0：call 0x00410320@0x006E57AF/test/jl 地址全真，但 006E57A0 全体 29 字节纯转发壳：两路径汇于同一条 ret 0xC@0x006E57BA 仅差 eax 值，fall-through 仅 xor eax,eax@0x006E57B8，主张的\"成功路径继续对象初始化\"在本行字节中不存在(模板假句)，查3不成立；②④环本身成立"),
    ("007276A0", "entry=007276A0：三重不成立——被调 0x00528660 返回 bool(al=0@0x005289CE/al=1@0x005289C2)，D-46(A) bool 主输出不算 ③b②；call@0x0072774B 后 0x00727750 有 mov eax,[ebx+0xAC](8B 83 AC 00 00 00) 覆写 eax，0x00727758 的 test 测成员字段、被调返回被整体丢弃(同型第二处 0x007277DF)；je 目标 0x00727764 为两路径公共续点(fall-through 链走完同样汇入)，唯一差异是 ecx 计数进 sprintf(\"%d\")，主张\"走与成功不同的收尾\"在 007276A0 为假"),
]

sec = []
sec.append("")
sec.append("## M59 并表说明（S15S16_3B2 审计 PASS 7 行原地升格；FAIL 4 行整行拒绝）")
sec.append("")
sec.append("- 来源：`S15S16_3B2\\S15_delta.tsv`（10 行）+ `S15S16_3B2\\S16_delta.tsv`（1 行）共 11 行；审计表 `S15S16_3B2\\_audit\\verdict.tsv`（11 行数据/7 列，第 2 列 `verdict`）裁 PASS 7 / FAIL 4；只并判 PASS 的 7 行。7 行均原地 `[静态推断]`→`[已证]`，第 4 列语义取 delta 原文、evidence_path 改指 `S15S16_3B2/_audit/VERDICT.md`；第 1/2/3/7/8 列与 name/subsystem 一字未动，coverage 仍 18,498 数据行、8 列 TAB 分隔。")
sec.append("- **006E6080 在 atlas 外**：6 个 S15 PASS 行（006E3DB0/006E4660/006E5730/006E6080/006E6410/00727240）中 `006E6080` 不在 `function_atlas.tsv`，只进全表 `[已证]`、不进 atlas 内计数；其余 5 个 S15 PASS 行与 S16 的 `006CE800` 均在 atlas 内。故 A 分母口径只 +6（S15 +5、S16 +1），全表 `[已证]` 1,489→1,496（+7）、atlas 内 1,484→1,490（+6）、atlas 外已证 5→6（+1，即 `006E6080`）。")
sec.append("- **4 行 FAIL 整行拒绝**（grade 仍 `[静态推断]`、第 4/5/6/7/8 列与 name/subsystem 均未动），entry 与一句话原因（照抄审计表 `verdict.tsv` 第 7 列 `reason`）：")
for entry, reason in FAIL_REASONS:
    sec.append("  - `%s`（S15）：%s" % (entry, reason))
sec.append("- **③b② 通道基础率与虚报率**：该通道基础率实测 **28.05%**（`S15S16_3B2\\base_rate.tsv`：S15 **45.45%**、S16 **7.89%**）；审计随后把 11 行主张的虚报率打到 **4/11 = 36.4%**（PASS 7 / FAIL 4）。故该通道剩下的池很小。")
sec.append("- 面板同步：S15 proved 101→106/158=67.09%、proved_strict 48→53/158=33.54%（门槛 79，差 26）；S16 proved 46→47/90=52.22%、proved_strict 20→21/90=23.33%（门槛 45，差 24）；TOTAL atlas 内 proved 1,484→1,490、proved_pct 11.49→11.54。名义达标仍 S15/S16/S17，严格达标仍仅 S17。")
sec.append("- 未改其它文件、未 git commit。")
sec.append("")

# append section: lines currently end at original L503 (''), keep exactly one trailing LF
lines = lines + sec
out = "\n".join(lines) + "\n"
with open(PANEL, "w", encoding="utf-8", newline="") as f:
    f.write(out)

log.append("APPENDED section '## M59 并表说明' (%d new lines)" % (len(sec)))
log.append("TOTAL lines now %d" % len(lines))
log.append("NOTE used: " + NOTE)
with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print("WROTE PANEL.md and log")
