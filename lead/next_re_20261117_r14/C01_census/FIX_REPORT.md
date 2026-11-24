# C01 · FIX_REPORT（审计 PARTIAL 整改）

依据：`_audit\VERDICT.md` §二/§四/§六；R13_COMMON §1/§6/§9/§16；PLAN R14 §1。
写域仅 `C01_census\`；未改 `_audit\`、游戏文件、台账，未 git commit。

## 必改 1 — gap 改下界/上界 + 补前向通道
- 改前：atlas_gaps.tsv 2 行、仅一条 capstone 目标扫（双通道名不副实，漏孤儿入口）。
- 改后：9 行，**下界 7 / 上界 9**；新增 `chan` 列标明通道来源。
  - `call-jmp`（通道 B1，原目标扫，保留不删）：0x004039C0(E8×2)、0x0042E1C0(E8×1)。
  - `orphan`（通道 B2，新建前向扫 `work/orphan_forward.py`）：0x004093C0 / 0x00412280 / 0x00427850 /
    0x0042E990 / 0x00435B50 —— 全 16B 对齐、未被 atlas 区间覆盖、有函数序言、前驱 ret 无间隔、零直接引用。
  - `orphan-cand`（逐条复核，仅上界）：0x00433060（med，ret+14nop 后 `sub esp,0x18`）、
    0x00432BF0（low，ret4+nop 后 naked 小函数 `mov ecx,[ecx+4]…ret`，无序言）。
- 独立复核：全 `.text` capstone skipdata=True 指令起点（1,394,120 条）→ 16B 对齐 → 区间包含排除 atlas
  → 序言 → 前驱终结符。与审计 5 个孤儿逐一相符；两额外地址逐字符核对反汇编。
- 证据：`EVIDENCE/orphan_forward_stdout.txt`、`EVIDENCE/orphan_forward_verification.json`、
  `EVIDENCE/gap_bound_counts.txt`、`EVIDENCE/gap_verification.txt`（原 E8 调用点仍在）。

## 必改 2 — 修 24 处 name 泄漏 + 6 行降级
- 根因：`work/extract_yrpp_names.py` 的 `CLASS_RE` 原只匹配 `class X;` / `class X :`，
  前向声明（`class VocClass;` 等）残留 cur_class；`class X {` 或 `class X`+\n`{` 未匹配。
- 修复：CLASS_RE 加 `\{|$`；跳过 `enum class Status`；find_decl 跳过 `:` 初始化列表行；
  0x40E320 显式 override 为 GenericNode::GenericNode（模板 Node 别名不取）。
- 改后 name（24）：AudioIDXData×5、AudioController×4、AudioStream::PlayWAV、Audio::ReadWAVFile、
  BombListClass×5、BounceClass×4、BaseClass×2、BombClass::BombClass、GenericNode::GenericNode。
- 6 行降级：0x4060F0/0x406130/0x406170/0x4061D0/0x406270/0x406310（YRpp 原文 `void sub_XXXXXX(...)` 无既立名）
  由 `[已证]` → `[静态推断]`；`[已证]` **102 → 96（7.43%）**；`[静态推断]` 687 → 703；`[未证]` 503 → 493。
- 证据：`EVIDENCE/verify_name_fixes.txt`（30/30）、`EVIDENCE/verify_coverage_fix.txt`（24/24）、
  `EVIDENCE/yrpp_reparse_stdout.txt`、`EVIDENCE/classify_fix_stdout.txt`。

## 必改 3 — 更正 UNKNOWNS U3
- 改前：称「余 3 个 KB-only 保留 `[已证]`」。改后：仅 **1 个**成立（0x00410B90 WriteINI，KB11:799）；
  0x0040E4A0 CCINIClass、0x00410380 AbstractClass（裸类名）与 0x00410A60 降 `[静态推断]`。

## 加分项 — 未复发 C02 缺陷（如实记入 PROGRESS）
- `work/scan_rtti.py` 独立扫 1214 虚表 / 14044 槽，与 `EVIDENCE/rtti_vtables.json` n=1214/1214 全等；
  主表 0x7E1F50 n=24、`+0x60`=0x7FB160 为 COL 指针非函数、末槽 0x410570 在位；KB22 19/19 槽号吻合。

## 交付自检
- 改前核心数字 1292/102/2 → 改后 **1292/96/7~9**；PROGRESS 58 行、本文 ≤40 行；coverage_delta.tsv 仍 1292 行且 entry 集合不变、atlas_gaps.tsv 9 行；复算命令见 PROGRESS。
