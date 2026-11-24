# S09-KPROVED · PROGRESS（卡号 S09-KPROVED）

开工 2026-11-19T13:09:05+08:00。目标 `ra2youli\gamemd.exe` SHA-256 前缀 73201CC0/后缀 F67476（现场全值复核 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），ImageBase 0x400000，全程只读。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未建 venv/未 pip install/未用 Ghidra。写域仅 S09_KPROVED\。判据：§8.6 六条 + D-40/41/42 + §8.5 异源规则；③ 只认 ③b。

## 0. 结论：8 行全部四环齐全（四环齐全数 = **8 / 8**）

每行均 ① 16B 对齐且为真 E8 目标；② RTTI 链现场读通且 vt[slot]==entry；③b 见档位/偏移；④ direct call 站点经全 .text 独立重扫（1,392,592 指令 / 68,253 个 E8@边界，与 SURVEY-RING24 基准逐字相同）确认 E8 边界 + site+5+rel32==entry + 体外 + 非自环。grade 升 `[已证]`。

| entry | 类@所读vt(②) | ② vt:slot→类 | ③b 档位 + 现场偏移 | ④ direct site / grade | 证据路径 |
|---|---|---|---|---|---|
| 004AAE90 | MouseClass::slot46 | 0x7E1964:46→.?AVMouseClass@@ | ① 4 张边界跳表 @4AAFBB/4AB0A6/4AB37B/4AB453（cmp 界 0xa/9，目标全在体内可核） | 653CFF,69302F,6931C9 / `[已证]` | EVIDENCE/rtti_004AAE90.txt, dis_, analy3b_, EVIDENCE/ring_8.tsv |
| 005BDF70 | MouseClass::slot30 | 0x7E1964:30→.?AVMouseClass@@ | ④ 完整循环 @5BE04D（读指针→test→free→写 0→edi+4/dec ebx→jne） | 67E870 / `[已证]` | EVIDENCE/rtti_005BDF70.txt, loops_005BDF70.txt |
| 006A5310 | SidebarClass::slot8 | 0x7F3058:8→.?AVSidebarClass@@ | ④ 完整循环 @6A55A3（读[edx]→判 4 标志→写计数→edx+4/ecx++→cmp ecx,esi/jl） | 6D03A7 / `[已证]` | EVIDENCE/rtti_006A5310.txt, loops_006A5310.txt |
| 004AB9B0 | MouseClass::slot48 | 0x7E1964:48→.?AVMouseClass@@ | ① 多路守卫链（D-42 细则#1）@4ABA11/4ABA6F/4ABA7F/4ABE1F + 可证伪满闸 @4ABB5A cmp[0xA802C8],0x80/jge | 653D58,69328B / `[已证]`（最弱一环，见 DISAGREE D2） | EVIDENCE/rtti_004AB9B0.txt, dis_, analy3b_ |
| 0063FEA0 | PowerClass::slot10 | 0x7EFF54:10→.?AVPowerClass@@ | ② 可证伪哨兵 @63FED7 & 640040 cmp eax,-1→跳过取项调用、按空处理 | 6A7B0A / `[已证]` | EVIDENCE/rtti_0063FEA0.txt, dis_, analy3b_ |
| 006A7780 | SidebarClass::slot10 | 0x7F3058:10→.?AVSidebarClass@@ | ④ 完整循环 @6A795F（读[ebx+0x38]→imul→写→edi++→cmp edi,0x3c/jl） | 6D09AA / `[已证]` | EVIDENCE/rtti_006A7780.txt, loops_006A7780.txt |
| 004ACE70 | MouseClass::slot32 | 0x7E1964:32→.?AVMouseClass@@ | ④ 完整循环 @4ACF93（读→随机→写[esi+0x38]→调 578290→cmp esi,ebx/jne） | 6879FF / `[已证]` | EVIDENCE/rtti_004ACE70.txt, loops_004ACE70.txt |
| 006ABD30 | MouseClass::slot34 | 0x7E1964:34→.?AVMouseClass@@ | ④ 嵌套完整循环 @6ABF66（test ebx/jle；内层 cmp edi,2/jl，多调用写字段） | 4A8B13,56111D,67E6A9 / `[已证]` | EVIDENCE/rtti_006ABD30.txt, loops_006ABD30.txt |

② 链样例（004AAE90）：[vt-4]=[7E1960]=COL 7FAB38 → [COL+0xC]=[7FAB44]=TD 816C90 → [TD+8]=[816C98] 逐字符 `.?AVMouseClass@@` → vt[46]=[7E1A1C]=004AAE90==entry。其余 7 行同链，见各 EVIDENCE/rtti_*.txt。全部 vt[slot]==entry 读通，无 fail-closed。多条目出现在多张表（classification.rtti_classes 含 2 个类）⇒ delta 保留 coverage 既有 name、不据单一 vt 改名（错源 ⑯/§8.5），差异入 DISAGREE D1。

## 1. 核心数字（供审计复算）

- **8 行四环齐全数 = 8**（①+②+③b+④ 全绿；最弱 004AB9B0 见 DISAGREE D2）。
- **A 集合里 S09 的 has4_strict 行数 = 103**（自数，非引用 103）：classification.tsv 中 subsystem=S09 的行 629 条；`has4_strict=1` 共 **129** 条，其中 **26** 条 `has2_rtti=0`（无 ②，不属 A）；A=②∧④ ⇒ `has4_strict=1 ∧ has2_rtti=1` = **129−26 = 103**。复算：`work/count_A.py`。
- **随机基线**（S09 静态推断池 N=629，池内随机取 8 行，seed 20261119，2,000 次，命中判据 ④∧③b；行采样口径，非随机 VA 命中 target）：严格 ③b 探测 K=41 ⇒ 8×41/629=**0.5215**，实测均值 **0.549**；含多路守卫档（与本文 8 行人工口径一致）K=44 ⇒ 8×44/629=**0.5596**，实测均值 **0.587**，分布 {0:1079,1:697,2:199,3:21,4:4}。复算：`work/baseline.py`+`work/baseline_p3.py`+`work/baseline_full_dist.py`。本次选 8 行全中（8/8）远超基线 ≈0.59，源于定向挑跳表/循环/哨兵，非随机。

## 2. 复算方法与纪律自检

- 脚本全在 `work\`（triage/collect_evidence/rtti_dump/analy3b/loops_dump/baseline/baseline_p3/baseline_variants/count_A/slice），只读目标、可复跑。
- ④ 站点按「全 .text 线性扫描的指令边界」定位并验 rel32，不依赖 function_atlas.tsv 的 entry+size；站点归属用函数区间包含（inbody=False）。
- ② 类属取 RTTI TD+8 内联串逐字符读（非解引用、非 docs）；命名只到 slot 占位级，未采纳 docs/re 语义名（§8.5）。
- 未改 coverage.tsv/台账/R14_COMMON/STATUS/SURVEY_RING24/gamemd.exe；未 git commit；未抄其它卡 work\ 代码；仅交 coverage_delta.tsv。
