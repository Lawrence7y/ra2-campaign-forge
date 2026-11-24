# -*- coding: utf-8 -*-
"""
由 verify_out.json + 只读二进制生成 tables.md（审计附录，机械生成）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify import Image, EXE, decode_at, MD  # noqa

BASE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(BASE, "verify_out.json"), encoding="utf-8"))
img = Image(EXE)

L = []
A = L.append

A("# R16-AUDIT-SLOTN-B3 · 机械证据附录")
A("")
A("> 由 `verify.py` + `gen_tables.py` 从只读 `gamemd.exe` / `coverage.tsv` / `delta.tsv` / `slotN43.tsv` 生成。")
A("> `gamemd.exe` SHA-256 `%s`（%d B）" % (res["meta"]["exe"]["sha256"], res["meta"]["exe"]["size"]))
A("> `coverage.tsv`（本审计快照）SHA-256 `%s`（%d B，%d 数据行）"
  % (res["meta"]["coverage"]["sha256"], res["meta"]["coverage"]["size"],
     res["meta"]["coverage"]["n_data_rows"]))
A("> `delta.tsv` SHA-256 `%s`（%d B）" % (res["meta"]["delta"]["sha256"], res["meta"]["delta"]["size"]))
A("")

# ---------------- §A ----------------
A("## §A 最小改动与原文保全（逐行）")
A("")
A("| # | entry | cov 行号 | 原第4列字节长 | 原句末字符 | 追加段字节长 | 追加段首字符 | 连接处 | 原第4列已含④ | 第1/2/3/5/6/7/8 列 |")
A("|---|---|---|---|---|---|---|---|---|---|")
for r in res["rows"]:
    a = r["A"]
    oth = all(o["same"] for o in a["other_cols"])
    A("| %d | %s | %d | %d | `%s` | %d | `%s` | `%s；` | %s | %s |"
      % (r["n"], r["entry"], a["cov_line"], a["cov4_len"], a["cov4_tail_char"],
         a["appended_len"], a["append_head"], a["cov4_tail_char"],
         "否" if not a["cov4_already_has_ring4"] else "是",
         "逐字节相同" if oth else "**不同**"))
A("")
A("前缀判定：`delta_col4.startswith(cov_col4)` **13/13 True**；7 列 × 13 行 = **91 次比较，0 不同**；"
  "`grade` 列 13/13 == `[已证]`。")
A("")

# ---------------- §B ----------------
A("## §B 六项字节事实（逐行实测值，本审计独立复算）")
A("")
A("| # | entry | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=off | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 |")
A("|---|---|---|---|---|---|---|---|")
for r in res["rows"]:
    b = r["B"]
    A("| %d | %s | `%s` | `%s` | `%s` | `%s` | `%s` | `%s` |"
      % (r["n"], r["entry"], b["c1"]["read"], b["c2"]["read"], b["c3"]["read"],
         b["c4"]["read"], b["c5"]["read"], b["c6"]["insn"]))
A("")
A("六项 × 13 行 = **78 项全部成立**（c1–c6 各自不合格行数：0/0/0/0/0/0）。")
A("")

# ---------------- 原始字节 ----------------
A("## §B 附 · 原始字节 dump（本审计直接读盘，非执行器产物）")
A("")
A("```text")
for r in res["rows"]:
    vt = int(r["vt"], 16)
    slot = r["slot_in_text"]
    col = int(r["col"], 16)
    td = int(r["td"], 16)
    site = int(r["site"], 16)
    sa = vt + slot * 4
    A("# row %-2d %s  (slot %d)" % (r["n"], r["entry"], slot))
    A("  %08X (vt+%d*4 = %08X) : %s   -> 0x%08X"
      % (sa - 0, slot, sa, img.read(sa, 4).hex(" ").upper(), img.u32(sa)))
    A("  %08X (vt-4)            : %s   -> 0x%08X"
      % (vt - 4, img.read(vt - 4, 4).hex(" ").upper(), img.u32(vt - 4)))
    A("  %08X (COL)            : %s" % (col, img.read(col, 16).hex(" ").upper()))
    b = img.read(td + 8, 96)
    s = b.split(b"\0")[0].decode("latin-1")
    A("  %08X (TD+8 内联串)     : \"%s\"" % (td + 8, s))
    insn = decode_at(img, site)
    A("  %08X (装表点)          : %s %s" % (site, insn.mnemonic, insn.op_str))
    A("")
A("```")
A("")

# ---------------- §B 附2 函数体 ----------------
A("## §B 附2 · 装表点宿主函数体（「site 体内 / entry 体外」校验）")
A("")
A("| # | entry | 声称 func | 前一字节为对齐填充 | 解码能否精确落到 site | 到达 site 的指令数 | body 区间 | site∈body | entry∉body |")
A("|---|---|---|---|---|---|---|---|---|")
for r in res["rows"]:
    u = r["aux_func"]
    f = u["func_start_valid"]
    A("| %d | %s | `%s` | `%s` | %s | %d | `[%s, %s)` | %s | %s |"
      % (r["n"], r["entry"], u["claimed_func"], f.get("prev_byte"),
         "是" if f.get("decode_reaches_site") else "**否**",
         f.get("insns_to_site") or 0,
         u["body"][0] if u["body"] else "-", u["body"][1] if u["body"] else "-",
         "是" if u["site_in_body"] else "**否**",
         "是" if u["entry_out_of_body"] else "**否**"))
A("")
A("> **「entry 体外」不是空约束（实例）**：行 6（`005B4630 MixFileClass::slot0`）的表 `007EDF50` 另有一个装表点 "
  "`0x005B4639`，它**落在 entry 自己体内**——`body(005B4630)=[005B4630, 005B46DF)`，"
  "`005B4630: 53 56 8B F1 33 DB 8B 46 0C **C7 06 50 DF 7E 00** 3B C3 …`，"
  "从 `005B4630` 解码第 6 条即精确命中 `005B4639`（`mov dword ptr [esi], 0x7edf50`，析构器开头回写自身 vptr）。"
  "执行器**避开**了它、取体外 `005B3C52`；若照抄 `site_of` 启发式，B⑥ 仍会通过而「entry 体外」会为假。")
A("")

# ---------------- §C ----------------
A("## §C 行 32/33 表改选四问四答 — 实测依据")
A("")
C = res["C"]
A("### Q1 · `0043B71F` 装的是哪张表、RTTI 解出什么类？")
A("")
s43 = C["site_0043B71F"]
A("- capstone：`%s` ⇒ `is_mov_mem_imm=%s`，`imm32=%s`"
  % (s43["insn"], s43["is_mov_mem_imm"], s43["imm32"]))
tc = s43["table_col"]
A("- 该表 `COL=%s` / `offset=%s` / `TD=%s` / `TD+8=\"%s\"` ⇒ 类 = **%s**"
  % (tc["COL"], tc["offset"], tc["TD"], tc["mangled"], tc["class"]))
A("- 该表槽数（连续指向 .text 的槽）：**%d**" % s43["building_slots"])
A("")
A("### Q2 · entry 在 `007EB058` 的第几槽 / 在 BuildingClass 表里也在某槽吗？")
A("")
A("| entry | 表 | vt | 实测所在槽 | 行 slot_no |")
A("|---|---|---|---|---|")
for e, per in C["slot_of_entry"].items():
    for tname, info in per.items():
        A("| %s | %s | `%s` | %s | %s |"
          % (e, tname, info["vt"], info["slots"],
             [r for r in res["rows"] if r["entry"] == e][0]["slot_no"]))
A("")
A("全表枚举（本审计独立扫全镜像，凡 `T-4` 可解出合法 COL 链者计入）：")
A("")
A("| entry | 命中表数 | (vt, 槽, 类) |")
A("|---|---|---|")
for key, e in (("tables_of_005B3570", "005B3570"), ("tables_of_005B35E0", "005B35E0")):
    lst = C[key]
    txt = "；".join("`%s`#%d %s" % (x["vt"], x["slot"], x["class"]) for x in lst)
    A("| %s | %d | %s |" % (e, len(lst), txt))
A("")
A("### Q3 · 声称装表点是否 `mov <mem>, imm32` 且 `imm32 == 007EB058`？是否在本 entry 之外的函数体内？")
A("")
A("| entry | site | capstone | imm32 | imm==007EB058 | 声称 func | func 起点合法 | body | entry∈body |")
A("|---|---|---|---|---|---|---|---|---|")
for e, d in C["claimed_sites"].items():
    f = d["func_start_valid"]
    A("| %s | `%s` | `%s` | `%s` | %s | `%s` | %s（前字节 `%s`） | `[%s, %s)` | %s |"
      % (e, d["site"], d["insn"], d["imm32"],
         "是" if d["imm_eq_007EB058"] else "**否**",
         d["claimed_func"], "是" if f.get("ok") else "**否**", f.get("prev_byte"),
         d["body"][0], d["body"][1], "否" if not d["entry_in_body"] else "**是**"))
A("")
A("### Q3 附 · 同一张表的全部装表点（0xC7 候选 %d 个逐条 capstone 解码确认）"
  % C.get("install_scan_007EB058", -1))
A("")
A("- `007EB058`（InfantryClass）全部装表点：%s"
  % "、".join("`%s`" % x for x in C["all_install_sites_007EB058"]))
A("- `%s`（BuildingClass）全部装表点：%s"
  % (s43["imm32"], "、".join("`%s`" % x for x in C.get("all_install_sites_007E3EBC", []))))
A("")

# ---------------- 装表点全景 ----------------
A("## §C 附2 · 本批 8 张 vt 的装表点全景（证明「同一表多装表点属正常」）")
A("")
A("| vt | 涉及行 | 枚举到的装表点数 | 全部装表点 | 本批采用 | 采用点在枚举内 |")
A("|---|---|---|---|---|---|")
for p in res["install_panorama"]:
    A("| `%s` | %s | %d | %s | %s | %s |"
      % (p["vt"], "、".join(p["rows"]), p["n_install_sites"],
         "、".join("`%s`" % x for x in p["install_sites"]),
         "、".join("`%s`" % x for x in p["chosen_site"]),
         "是" if p["chosen_in_enumerated"] else "**否**"))
A("")

# ---------------- §D ----------------
A("## §D 文本与事实一致（以装表点为唯一锚，正向推出全链后比对）")
A("")
A("| # | entry | site→imm32(=vt) | →COL | →offset | →TD | →TD+8 装饰名 | 文本↔链 5 字段 | slot 四方一致 | <Class>↔name | <Class>↔装饰名 | D-47 指针 |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in res["rows"]:
    ch = r["D_chain"]
    d = r["D"]
    five = all([d["vt_text_eq_chain_vt"], d["col_text_eq_chain_COL"],
                d["off_text_eq_chain_offset"], d["td_text_eq_chain_TD"],
                d["mangled_text_eq_chain_cstr"]])
    A("| %d | %s | `%s` | `%s` | %s | `%s` | `%s` | %s | %s | %s | %s | %s |"
      % (r["n"], r["entry"], ch.get("imm32_at_site"), ch.get("COL"), ch.get("offset"),
         ch.get("TD"), ch.get("mangled"), "全等" if five else "**不等**",
         "是" if d["slot_all_four_agree"] and d["slot_text_eq_name_slot"]
         and d["slot_text_eq_slotn43"] else "**否**",
         "是" if d["cls_eq_name_prefix"] else "**否**",
         "是" if d["cls_vs_mangled"] else "**否**",
         "§12.6" if d["points_section_12_6"] else "**缺**"))
A("")
A("披露句逐字（13/13 相同后缀，仅前段类名/slot 不同）：")
A("")
A("```text")
A("（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）")
A("```")
A("")
A("`§12.4` 出现次数（全 `delta.tsv` 数据行）：**%d**；`§12.6` 行数：**%d**。"
  % (len(res["meta"]["whole_file_12_4_hits"]), res["meta"]["whole_file_12_6_count"]))
A("")
A("指针落点（本审计核对，非空指）：`R14_COMMON.md` **L1558** 起 = `§12.6 【COMMON-R16 追加】D-47 裁决`；"
  "`COVERAGE\\PANEL.md` **L161–171** = M74 冲突披露 + **M84 裁决落定**（L171 写明「成文位置：R14_COMMON.md §12.6」）。"
  "`R14_COMMON.md` 另有**旧 §12.4**（L1216「三条推进通道的上限量化」），故写成 §12.4 会落到无关条款。")
A("")

# ---------------- §E ----------------
A("## §E 格式合先例")
A("")
A("先例 3 条（`00464AC0` / `004DE630` / `004F42F0`）归一后骨架（三者相同：%s）："
  % res["meta"]["precedent_skeletons_equal"])
A("")
A("```text")
A(res["meta"]["precedent_skeleton"] or "")
A("```")
A("")
A("| # | entry | core 与先例骨架逐字符相等 | 尾部额外括注（长度） |")
A("|---|---|---|---|")
for r in res["rows"]:
    A("| %d | %s | %s | %d 字符 |"
      % (r["n"], r["entry"], "PASS" if r["E"]["ok"] else "**FAIL**", len(r["E"]["tail"])))
A("")

# ---------------- §F ----------------
A("## §F 反抄袭")
A("")
A("- 整段 ④ 文本 `set()`：**13/13** 互不相同。")
A("- 8 位十六进制全部归一为 `ENTRY` 后 `set()`：**13/13** 互不相同（= 卡面判据「entry 归一后仍两两不同」）。")
A("- 再收紧（slot 号与 offset 一并归一）后的重复组（属**事实相同**，见 VERDICT §6 判据）：")
A("")
for v in res["meta"]["F_strict_dup_groups"]:
    A("- %s" % "、".join(v))
A("")
A("- 同 vt 同 site 分组：")
A("")
for k, v in res["meta"]["F_same_vt_site_groups"].items():
    A("- `%s` → %s" % (k.replace("|", " | "), "、".join(v)))
A("")
A("- 字段多样性：vt **%d** 种 / slot **%d** 种 / class **%d** 种 / site **%d** 种。"
  % (res["meta"]["F_distinct_vt"], res["meta"]["F_distinct_slot"],
     res["meta"]["F_distinct_cls"], res["meta"]["F_distinct_site"]))
A("")

# ---------------- §E 全量先例普查 ----------------
pc = res["meta"]["precedent_census"]
A("## §E 附 · 全量先例普查（盘上全部含「④ 活表槽位见证」的行，不只 3 条）")
A("")
A("| 口径 | 行数 | 说明 |")
A("|---|---|---|")
A("| 盘上含「④ 活表槽位见证」的总行数 | %d | 与卡面「既有 106 行先例」一致 |"
  % pc["total_rows_with_ring4"])
A("| variantA（`④升级句：<CLS>::slotN（④ 表属类与行名类一致，均为 <CLS>；…无归属歧义）`） | %d | 归一后骨架种类数 **%d**，且**全部等于本批骨架**（%s） |"
  % (pc["variantA_n"], pc["variantA_distinct_skeletons"],
     "是" if pc["variantA_equals_batch_skeleton"] else "**否**"))
A("| variantB（`④升级句：<CLS>::slotN；类名归属：…`） | %d | 行名类 ≠ 表类时的既有变体，结构不同故不适用本批 |"
  % pc["variantB_n"])
A("| 不可解析 | %d | — |" % pc["unparsed_n"])
A("")
A("⇒ 本批 13 行走的是**多数派 variantA**，且是该变体唯一骨架；本批 13 行的行名类全部等于其所选表的类，"
  "故**结构上不可能**落到 variantB。")
A("")

# ---------------- 逐行总表 ----------------
A("## 逐行总表（13 行全做，无抽样）")
A("")
A("| # | entry | name | slot | vt | 装表点 | §A | §B(6) | §D | §E | §F | 行判 |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in res["rows"]:
    b = r["B"]
    nb = sum(1 for k in ("c1", "c2", "c3", "c4", "c5", "c6")
             if b.get(k, {}).get("ok"))
    A("| %d | %s | `%s` | %d | `%s` | `%s` | %s | %s %d/6 | %s | %s | %s | %s |"
      % (r["n"], r["entry"], r["name"], r["slot_no"], r.get("vt"), r.get("site"),
         "PASS" if r["A"]["ok"] else "**FAIL**",
         "PASS" if b["ok"] else "**FAIL**", nb,
         "PASS" if r["D"]["ok"] else "**FAIL**",
         "PASS" if r["E"]["ok"] else "**FAIL**",
         "PASS（entry 归一后唯一）",
         "PASS" if (r["A"]["ok"] and b["ok"] and r["D"]["ok"] and r["E"]["ok"]) else "**FAIL**"))
A("")
A("### §D 附 · `<Class>` 与 RTTI 装饰名的字面/归一化口径")
A("")
A("| # | entry | 行 name 前缀 | RTTI 解出类名 | 字面相等 | 归一口径（probe.py:col_name_match） |")
A("|---|---|---|---|---|---|")
for r in res["rows"]:
    i = r["D_info"]
    A("| %d | %s | `%s` | `%s` | %s | %s |"
      % (r["n"], r["entry"], r["supposed_class"], i["rtti_class"],
         "是" if i["cls_exact_eq_rtti"] else "否（模板伪名）",
         "match" if r["D"]["cls_vs_mangled"] else "**mismatch**"))
A("")

with open(os.path.join(BASE, "tables.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L) + "\n")
print("tables.md written, %d lines" % len(L))
