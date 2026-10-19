# ASM-FIX 收官报告：P1/P2 字节勘误 + N-2 改锚 + P3 定性标注 + 区段配准

> **任务卡**：ASM-FIX ｜ **执行方**：DSH 子代理（任务号 ASM-FIX，父代理 session-852a2193） ｜ **日期**：2026-09-27
> **基线二进制**：`ra2youli/gamemd.exe`（YR 1.001，4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，ImageBase `0x400000`）—— **全程只读**；MD5 前后一致、mtime 未变（2026-09-25 16:10:48）
> **地址口径**：FileOffset 一律走 PE 段表映射（`off = rawptr + (VA - 段基址)`），不用 `VA-0x400000` 简写口径（与 `tools/audit_bytes.py`/`out/re_work/asm_scan/classify.py` 同口径）
> **上游输入**：`docs/re/inline_assertion_scan.md`（ASM-SCAN：150 文件 / 28,703 个 `0xVA` 出现点 / 321 条②③不符）、`out/re_work/asm_scan/errata_table.md`、`out/re_work/asm_scan/classified.json`

---

## [0] 结论摘要

1. **P1/P2 真勘误在授权范围内清零**：errata 表 36 条 P1 + 8 条 P2 中，**40 条（32 P1 + 8 P2）已在授权目标文档内就地勘误并复扫为 0**；余 **4 条**（`REVERSE_ENGINEERING_AND_PATCHES.md:1992`、`docs/RE_COORDINATION.md:1240`，与 P2 `REVERSE_ENGINEERING_AND_PATCHES.md:247`）**全部落在任务卡明令禁止触碰的两份 Lead 所有文件中**，已逐条列出交 Lead 处理（§4）。
2. **前后对比（验收②）**：同口径（ASM-SCAN 快照那 150 个文件）②③ **321 → 278（−43）**，其中 **P1 36→2、P2 8→1、P4 43→25、B-ERRATA-QUOTE 3→18**；P3 保持 27（本批只加标注、不改字节，符合 F4）。全库口径（154 文件 = 快照 150 + 窗口后新增 3 份 + 本报告）②③ = 332（**本报告自身仅贡献 6 条，且全部带「原记」标记 ⇒ 归 R-ERRATA 非勘误桶**）。
3. **N-2 已改锚并恢复等级（F3）**：真锚点 **`0x007BC8A3: 66 8B 01`**（`mov ax,[ecx]`，`BlitTrans@G@0x007BC890` 内 16 位源像素流循环体）经本批**独立 Capstone 反汇编复核**，`closure` §5.2/§6 行 29 与 `nonrle` §6 Item 2 的锚点全部落地，`A 类 · [实证]` 等级恢复。
4. **最大风险（新发现，超出原勘误表）**：`ARCHITECTURE_ATLAS.md` §9.2「每逻辑帧固定消费 1 次 RNG」的证据链**原记锚点** `0x0064DAD9: E8 52 1A F6 FF`（`call 0x005AF530`）**全镜像 0 命中**；且**全 .text 无任何 call/jmp 以 `0x005AF530` 为目标**（自跑全量站点普查 = 0 处），该 VA 本身也不是函数入口 ⇒ 该条**结论方向不变但字节级证据链待重新锚定**，已在文档就地加「影响面警示」。
5. **门禁全绿**：`tools/verify_anchors.py` **323/323 PASS**、`tools/audit_bytes.py docs/re/anchor_claims.txt` **323 OK**（金标准未动）；附加自证：重扫生成的 `out/re_work/asm_scan/claims.txt` **1273/1273 OK**（含本批新写的全部订正字节串）。

---

## [META]

```text
task=ASM-FIX   executor=DSH 子代理 (session-852a2193 派工)   mode=accept-edits
scope_declared = errata_table.md 列出的 P1/P2 目标文档（均在 docs/re/ 下）+ 新建 out/re_work/asm_fix/**
                + 新建 docs/re/asm_fix_report.md
elapsed ≈ 单轮（工具链见 §8），工作区 D:\Project\ra2-campaign-forge
```

---

## [1] 逐条必答项结论表

| # | 任务项 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1 | P1 真字节错 36 条就地勘误 | **32/32 授权条目完成**（4 条在禁区，见 §4）；每条「保留原记 + 勘误块」 | [实证] | `docs/re/asm_fix_report.md` §3.1、`out/re_work/asm_fix/change_list.md` |
| F1-a | `ARCHITECTURE_ATLAS.md:471/472` 伪编码 | `0x006DA945: 8B 4C 24 1C`（原记 `89 7C 83 E4`，全镜像 0 命中）+ `0x006DA957: 89 83 E0 00 00 00` | [实证] | VA 0x006DA945 / FileOff 0x2DA945；Capstone：`mov ecx,[esp+0x1C]` → `0x006DA949: 89 8C 83 E4 00 00 00 mov [ebx+eax*4+0xE4],ecx` |
| F1-b | `ARCHITECTURE_ATLAS.md:1371/1374` | `85 C0` → `84 C0`（`test al,al`；该 2 字节模式全镜像 400+ 命中 ⇒ 非走锚，是抄错） | [实证] | 0x0048CE8F: 84 C0 74 09、0x0048CE98: 84 C0 75 0E（Capstone 逐条） |
| F1-c | `doc_consistency_fix_list.md:214/215` | `89 91 34 01 00 00` → `89 B8 …`（`mov [eax+0x134],edi`）/ `89 98 …`（`mov [eax+0x134],ebx`） | [实证] | 0x00577EC5、0x00577B60（Capstone 逐条） |
> 【W3 勘误 · W3-A6/ISSUE-TABLE-GAP-BYTES】改前：89 91 34 01 00 00；改后：89 B8 34 01 00 00 (0x00577EC5) / 89 98 34 01 00 00 (0x00577B60)；依据：ra2youli/gamemd.exe:0x177EC5, 0x177B60; docs/re/doc_consistency_fix_list.md:49 (N-2)；分级：P0
| F1-d | `cross_doc_consistency_audit.md:182` | 立即数 `00` → `01`（`mov byte [esi+0x84], 1`） | [实证] | 0x006E9CE8 |
| F1-e | `trigger_runtime_deep_dive.md:461` | rel32 `E8 CC 7D 02 00` → `E8 CC 7D 1C 00`（`call 0x00725C70`，与同行「帧尾 0x725C70 抽干」自洽）；同格另一断言 `0x6E5230: C6 46 34 01` 亦订正为真锚点 **0x006E5233** | [实证] | 0x0055DE9F、0x006E5233；解析目标 0x00585C70 的原记串全镜像 0 命中 |
| F1-f | sprint 报告 S2/S3/S5/S14/S17 的 P1 条目 | 全部就地处理：11 条**真值订正**（S2:345/352-355、S3:115/126/232、S5:398/404、S14:488、S17:51）+ 其余按「原记/实测」定性标注（VA 落指令中间或清单为手写拼接） | [实证] | §3.1 逐条表 |
| F2 | P2 真 VA 走锚 8 条改锚（字节不变） | **8/8 完成**：closure `0x006F876F`；S14 `0x00409511`/`0x0053E510`/`0x0053E574`；S7 `0x004D37F5`/`0x004D37DD`；savegame `0x0067E0A8` | [实证] | §3.2 逐条表 |
| F3 | N-2 改锚 `0x007BC8A3: 66 8B 01` + 恢复 `A 类 · [实证]` | **完成**：`closure` §5.2（:456/:462）、§6 行 29（:573）、DA4-10 汇总表（:586）+ `nonrle` §6 Item 2（:273）全部落地；循环体逐条复核成立 | [实证] | VA 0x007BC890（`ret 0x20`）内 0x007BC8A3: 66 8B 01（全镜像 65 处、窗口 0x7BC800–0x7BC900 内唯一） |
| F4 | P3 27 条统一加标注（不逐条改字节） | **完成**：7 份 sprint 报告统一加「手写示意清单」定性标注（ASM-FIX-35），P3 计数复扫**保持 27**（证明未改字节） | [实证] | S2:10 / S3:8 / S5:6 / S7:4 / S11:8 / S14:6 / S17:7 |
| F5-1 | 区段配准 `ARCHITECTURE_ATLAS.md:1511-1514`（U-1） | 逐字节订正为实测真指令序列（`A1 EC 3D A8 00` 等 4 条）；**原记块判「来源构建不明 · 待重新锚定」**（±0x200 滑窗 0 命中 + 全镜像 0 命中） | [实证]+[推演] | 0x0064DACE/DAD3/DAD6/DADC；`E8 52 1A F6 FF` 全镜像 0 命中；目标 0x5AF530 全 .text 0 处调用站点 |
| F5-2 | `offline_verification_alternatives.md:132/133`（U-2） | **判「来源构建不明 · 待重新锚定」**：0x006BAC10 落指令中间（真指令起 0x006BAC0A）；±0x200 滑窗 0 命中；全 .text 候选 3 处 / 7 处均 Δ>1MB | [实证] | §3.5，候选址已列供下一批反查（不猜、不定谳） |
| F5-3 | `particle_fog_owner_evidence.md:226-228` | **给出真锚点 `0x0062DE6D`**（与本文同节原记写点 0x62DE2F / 0x62DE37 / 0x62DE54 同函数、字段 +0xE0 一致，Δ=−0x1F00）；实测断言 0x0062DE6D: 8B 8E E0 00 00 00、0x0062DE73: 3B CB、0x0062DE75: 74 3A；**函数归属须重新定谳**（不属 0x0062FD60） | [实证] | — |
| F5-4 | `landing_equivalence_static_proof.md:276-279` | **判「来源构建不明 · 待重新锚定」**：0x007C8E24: C3（`ret`，函数已结束）；原记 `85 C0 75 14` 在 ±0x200 内无指令边界对齐命中（全镜像 44 处） | [实证] | §3.5；同页 `operator delete` 块（0x007C8B3D）复核无误 |
| F5-5 | `blitter_microkernel_deep_dive.md:198-200` | **给出真锚点**：本 5 行整体 −1 偏移 + `push ecx` 误置；真序列 = `0x00496820: 51` / `0x00496821: 8B 44 24 14` / `0x00496825: 8B 54 24 1C` / `0x00496829: 53` / `0x0049682a: 55`（行 201 起原本正确） | [实证] | VA 0x00496820–0x0049682B（Capstone 全窗口） |
| 验收① | P1/P2 真勘误计数降为 0 | **授权目标文档 = 0**；残留 3 条全在禁区文件（§4 逐条理由） | [实证] | `out/re_work/asm_fix/before_after_table.md` 表 C/D |
| 验收② | 前后对比表 | 321 → 278（同口径）／332（全库 154 文件），按分类分布见 §3.6 | [实证] | 同上 |
| 验收③ | 对比表写入报告 + 附脚本命令原文 | 完成（§3.6 表 + §6 命令） | [实证] | §6 |
| 门禁 | `verify_anchors.py` 323/323 + `audit_bytes.py` 323 OK | **全绿**（原文见 §6）；附加 1273 OK | [实证] | §6 |

---

## [2] 关键证据块（VA / FileOffset / 原始字节 / Capstone 反汇编 / 来源）

统一工具：`out/re_work/asm_fix/probe.py`（只读；VA→字节+Capstone 线性扫描+指令边界判定+全镜像模式普查+call/jmp 站点普查+滑窗序列配准）。**全部地址走 PE 段表**，FileOffset 由脚本给出。

```text
[E1] 0x006DA945  .text  FileOffset 0x2DA945   （ATLAS:471/472 · l4_vision:72/73）
  actual : 8B 4C 24 1C | 89 8C 83 E4 00 00 00 | 8B 83 E0 00 00 00 | 40 | 89 83 E0 00 00 00
  capstone: 006DA945 mov ecx,[esp+0x1c]
            006DA949 mov [ebx+eax*4+0xe4], ecx      <- VisibleCells[Count] = pCell
            006DA950 mov eax,[ebx+0xe0] / 006DA956 inc eax / 006DA957 mov [ebx+0xe0],eax
  census : declared "89 7C 83 E4" whole-image hits = 0 ；declared "FF 43 E0" whole-image hits = 0

[E2] 0x0048CE8F / 0x0048CE98  .text          （ATLAS:1371/1374）
  actual : 84 C0 74 09 E8 38 01 0D 00 | 84 C0 75 0E
  capstone: 0048CE8F test al,al / 0048CE91 je 0x48ce9c / 0048CE98 test al,al / 0048CE9A jne 0x48ceaa
  census : declared "85 C0" hits = 400(cap) nearest 0x004144CC Δ=-494019 ⇒ 非走锚

[E3] 0x0064DACE  .text  FileOffset 0x24DACE   （ATLAS §9.2 帧 CRC · U-1 · 【最高影响面】）
  actual : A1 EC 3D A8 00 | 8B 04 B0 | 8D 88 9C 00 00 00 | 8B B8 9C 00 00 00
  capstone: 0064DACE mov eax,[0xa83dec] / 0064DAD3 mov eax,[eax+esi*4] / 0064DAD6 lea ecx,[eax+0x9c]
            0064DADC mov edi,[eax+0x9c] / 0064DAE2 mov ebx,[ecx+4] / 0064DAE5 mov edx,[ecx+8]
  census : 原记 "E8 52 1A F6 FF" 全镜像 0 命中；±0x200 滑窗配准 pattern[0]="A1 30 B2 A8 00" 0 命中
  xref   : 全 .text call/jmp → 0x005AF530 站点数 = 0（自跑全量普查）；0x005AF530 本身非函数入口
           （该 VA 落在 005AF52F 的 "24 08 and al,8" 指令中间）

[E4] 0x007BC8A3  .text  FileOffset 0x3BC8A3   （N-2 真锚点 · F3）
  actual : 66 8B 01 | 83 C1 02 | 66 85 C0 | 74 03 | 66 89 02 | 83 C2 02 | 4E | 75 EC
  capstone: 007BC8A3 mov ax,[ecx] / 007BC8A6 add ecx,2 / 007BC8A9 test ax,ax / 007BC8AC je 0x7bc8b1
            007BC8AE mov [edx],ax / 007BC8B1 add edx,2 / 007BC8B4 dec esi / 007BC8B5 jne 0x7bc8a3
            函数头 007BC890（ret 0x20 收尾）
  census : "66 8B 01" 全镜像 65 处；0x7BC800..0x7BC900 内仅此 1 处
  注     : 上游 closure 记「66 处」，实测 65（微勘误，见 §9）

[E5] 0x0062DE6D  .text  FileOffset 0x22DE6D   （F5-3 真锚点）
  actual : 8B 8E E0 00 00 00 | 3B CB | 74 3A
  capstone: 0062DE6D mov ecx,[esi+0xe0] / 0062DE73 cmp ecx,ebx / 0062DE75 je 0x62deb1
  census : 原记锚 0x0062FD6D 实测 "00 00 83 F8 04 77"（落在 0062FD69 的 mov eax,[eax+0x2b4] 指令中间）
           序列 "8B 8E E0 00 00 00 85 C9 74" 全镜像 0 命中
           与原记 VA 同节写点 0x62DE2F / 0x62DE37 / 0x62DE54 同函数、字段位移 +0xE0 一致

[E6] 0x00496820  .text                   （F5-5 真序列，Δ=+1 归位）
  actual : 51 | 8B 44 24 14 | 8B 54 24 1C | 53 | 55 | 8B 6C 24 14 | 56 | 8B 74 24 14 | 89 4C 24 0C
  capstone: 00496820 push ecx / 00496821 mov eax,[esp+0x14] / 00496825 mov edx,[esp+0x1c]
            00496829 push ebx / 0049682a push ebp / 0049682b mov ebp,[esp+0x14]（文档 :201 原本正确）
  census : 原记序 "53 55 51" 在 ±0x40 内无一致在序命中（53 于 +1、55 于 +2 后即断）

[E7] 0x006E5233 / 0x007C8E3D              （本批机器复扫自查出的两处自身订正）
  0x006E5230: 56 8B F1 (push esi; mov esi,ecx)  →  0x006E5233: C6 46 34 01 (mov byte [esi+0x34],1)
  0x007C8E3C: 0C (mov [ebp+0xC],ecx 末字节)      →  0x007C8E3D: 3B CF (cmp ecx,edi)
```

**机器可读断言**：复扫生成的 `out/re_work/asm_scan/claims.txt` 共 **1273 条**（`tools/audit_bytes.py` → 1273/1273 OK），其中含本批新写的全部订正字节串（`0x006DA945 = 8B 4C 24 1C`、`0x007BC8A3 = 66 8B 01`、`0x0062DE6D = 8B 8E E0 00 00 00` 等）。

---

## [3] 勘误（F1–F5 逐项对应；共 **76 条就地编辑 / 20 个文件**）

> 全部为**单行就地编辑**（`out/re_work/asm_fix/apply_edits.py`，先全量校验后一次性写盘；**无任何插入/删除行** ⇒ 所有下游行号稳定，errata 表行号可直接复用）。
> 「原记」= 保留原文值，「勘误 ASM-FIX-n」= 勘误块编号；每行都以 `勘误 ASM-FIX-n：原记 … 实测 …` 形式内联。
> 机器可读全量清单：`out/re_work/asm_fix/change_list.md`（逐条 改前/改后）+ `edits_all.json`。

### 3.1 F1 —— P1 真字节错（授权 32 条；括号内为 ASM-FIX 号）

| 勘误号 | 文件:行 | VA | 实测（订正后写入） | 原记（保留） | 处置 |
|---|---|---|---|---|---|
| ASM-FIX-5 | docs/re/ARCHITECTURE_ATLAS.md:471 | 0x006DA945 | 8B 4C 24 1C | 89 7C 83 E4 | 就地订正（原记全镜像 0 命中） |
| ASM-FIX-5 | docs/re/ARCHITECTURE_ATLAS.md:472 | 0x006DA957 | 89 83 E0 00 00 00 | FF 43 E0 | 就地订正 |
| ASM-FIX-5 | docs/re/l4_vision_dirty_final_spec.md:72 | 0x006DA945 | 8B 4C 24 1C | 89 7C 83 E4 | 同源复述，同步订正 |
| ASM-FIX-5 | docs/re/l4_vision_dirty_final_spec.md:73 | 0x006DA957 | 89 83 E0 00 00 00 | FF 43 E0 | 同源复述，同步订正 |
| ASM-FIX-6 | docs/re/ARCHITECTURE_ATLAS.md:1371 | 0x0048CE8F | 84 C0 | 85 C0 | 就地订正（`test al,al`） |
| ASM-FIX-6 | docs/re/ARCHITECTURE_ATLAS.md:1374 | 0x0048CE98 | 84 C0 | 85 C0 | 就地订正 |
| ASM-FIX-7 | docs/re/cross_doc_consistency_audit.md:182 | 0x006E9CE8 | C6 86 84 00 00 00 01（`mov byte [esi+0x84],1`） | 原记立即数 00 | 就地订正（0/1 写反） |
| ASM-FIX-8 | docs/re/ARCHITECTURE_ATLAS.md:1511-1514 | 0x0064DACE/DAD3/DAD6/DADC | A1 EC 3D A8 00 / 8B 04 B0 / 8D 88 9C 00 00 00 / 8B B8 9C 00 00 00 | A1 30 B2 A8 00 / 8D 88 18 02 00 00 / E8 52 1A F6 FF / 03 F8 | 逐字节订正 + 加「影响面警示」 |
| ASM-FIX-9 | docs/re/doc_consistency_fix_list.md:214 | 0x00577EC5 | 89 B8 34 01 00 00 | 89 91 34 01 00 00 | 就地订正 |
| ASM-FIX-9 | docs/re/doc_consistency_fix_list.md:215 | 0x00577B60 | 89 98 34 01 00 00 | 89 91 34 01 00 00 | 就地订正 |
| ASM-FIX-4 | docs/re/trigger_runtime_deep_dive.md:461 | 0x0055DE9F | E8 CC 7D 1C 00 | E8 CC 7D 02 00 | 就地订正（rel32 单字节） |
| ASM-FIX-4b | docs/re/trigger_runtime_deep_dive.md:461 | 0x006E5233 | C6 46 34 01 | 0x6E5230 处 C6 46 34 01 | 改锚 Δ+3（原 VA 为 push esi/mov esi,ecx） |
| ASM-FIX-11 | docs/re/re_sprint_S2_report.md:167 | 0x004AA52A | 8B 8E FC 00 00 00（真边界） | 原记 E8 B0 22 1B 00（原锚点 0x004AA52B 实测 8E FC 00 00 00，VA 落指令中间） | 定性标注：415 处同目标调用，±0x400 唯一站点 0x004AA6A2 不足定谳 ⇒ 待重新锚定 |
| ASM-FIX-11 | docs/re/superweapon_re.md:807 | 0x004AA52A | 8B 8E FC 00 00 00（真边界） | 原记 E8 B0 22 1B 00 | 同源复述，同步标注 |
| ASM-FIX-12 | docs/re/re_sprint_S2_report.md:345 | 0x006CDEFB | E8 80 24 D4 FF | E8 7D 24 D4 FF | 改锚 Δ−3 + 字节订正（本窗唯一 `call 0x410380` 站点） |
| ASM-FIX-13 | docs/re/re_sprint_S2_report.md:352-355 | 0x006CDF13/19/20/27 | C7 06 … / C7 46 04 … / C7 46 08 … / C7 46 0C … | C7 00 … / C7 40 04/08/0C … | 就地订正（ModRM r/m 寄存器名规范化误写） |
| ASM-FIX-14 | docs/re/re_sprint_S2_report.md:357 | 0x006CDF2E | 8B 46 68 57 | 83 7E 68 00 | 定性标注（手写规范化；语义「比较」→「取值」） |
| ASM-FIX-15 | docs/re/re_sprint_S2_report.md:371 | 0x006CDFB2 | 8A 12 00 00 C7（原 VA 实测） | E8 89 12 00 00 | 定性标注：同目标 3 候选（CDF98h/CDFA6h/CDFB1h）不唯一 ⇒ 待重新锚定 |
| ASM-FIX-16 | docs/re/re_sprint_S2_report.md:421 | 0x006CC36E | 00 00 84 D2（原 VA 实测） | 80 78 52 00 | 定性标注：VA 落指令中间 ⇒ 待重新锚定 |
| ASM-FIX-16 | docs/re/re_sprint_S2_report.md:423 | 0x006CC374 | 8B 41 7C 85（原 VA 实测） | 83 79 7C 00 | 定性标注（手写规范化） |
| ASM-FIX-17 | docs/re/re_sprint_S3_report.md:115 | 0x00451970 | E8 2B 05 FD FF | 0x0045196E 处 E8 2D 05 FD FF | 改锚 Δ+2 + 字节订正（本窗唯一 `call 0x421EA0`） |
| ASM-FIX-18 | docs/re/re_sprint_S3_report.md:126 | 0x00423B3C | FF 50 48 | FF 90 48 00 00 00 | 就地订正（disp8 形式，语义等价） |
| ASM-FIX-19 | docs/re/re_sprint_S3_report.md:232 | 0x00556D53 | 8B 0D 7C CB AB 00 | 8B 15 7C CB AB 00 | 就地订正（`mov ecx,` 非 edx） |
| ASM-FIX-20 | docs/re/re_sprint_S5_report.md:398 | 0x0040937A | 6A 00 68 E8 03 00 00 51 52 E8 48 FF 3B 00 | 6A 00 68 E8 03 00 00 E8 4E FF 3B 00 | 就地订正（原记省略 `51 52` 两压栈 + rel32 错） |
| ASM-FIX-21 | docs/re/re_sprint_S5_report.md:401 | 0x0055D377 | A0 80 ED A8 00 C6 05 58 CD AB | 8A 05 80 ED A8 00 84 C0 75 33 | 就地订正（首指令短编码等价，后续序列不符） |
| ASM-FIX-21 | docs/re/re_sprint_S14_report.md:487 | 0x0055D377 | 同上 | 同上 | 同源复述，同步订正 |
| ASM-FIX-22 | docs/re/re_sprint_S5_report.md:404 | 0x006842D3 | 8B 0D 70 F7 87 00 C6 05 9C ED A8 00 | 8B 0D 70 F7 87 00 E8 3B B4 EC FF | 就地订正（后 5 字节实为 `call 0x54F720` 位于 0x006842E0，Δ+0x0D，原文跨指令拼接） |
| ASM-FIX-25 | docs/re/re_sprint_S14_report.md:475 | 0x00406F8C | 00 01 00 00 00（原 VA 实测） | 83 F8 21 7E 41 | 定性标注：VA 落 `C7 05 5C E7 87 00 01 00 00 00` 指令中间 ⇒ 待重新锚定 |
| ASM-FIX-26 | docs/re/re_sprint_S14_report.md:488 | 0x0055D830 | E8 1B 75 07 00 E8 46 F8 F2 FF | … E8 4B F8 F2 FF | 就地订正（rel32 → `call 0x0048D080`，与本行注释一致） |
| ASM-FIX-27 | docs/re/re_sprint_S14_report.md:489 | 0x0055D650 | 8D 46 0A 89 0D 28 73 88 00 8D 4C 24 14 89 | … A3 30 73 88 00 | 就地订正 + 补真锚（第 3 条指令 = 0x0055D667: A3 30 73 88 00，Δ+0x17；双写结论成立） |
| ASM-FIX-27 | docs/re/re_sprint_S14_report.md:490 | 0x0055D744 | 同上（本条第 3 条 = 0x0055D75B，Δ+0x17） | 同上 | 就地订正 + 补真锚 |
| ASM-FIX-28 | docs/re/re_sprint_S17_report.md:51 | 0x006CD75F | 8B 82 EC 0F 00 00 | 0x006CD754 处 8B 8A EC 0F 00 00 | 改锚 Δ+0x0B + 寄存器订正（eax，与 S2 §7.4 互证） |
| （禁区） | REVERSE_ENGINEERING_AND_PATCHES.md:237/238 | — | 已在 Lead 侧订正 | — | 本批复核：现文本已含 `FF 74 24 04 E8 A2`（EXACT），无需再动 |
| （禁区） | REVERSE_ENGINEERING_AND_PATCHES.md:1992 / docs/RE_COORDINATION.md:1240 | 0x006F8737 | D1 F8（`sar eax,1`） | C1 F8 01（全镜像 0 命中） | **未动（禁区）**，交 Lead（§4） |

### 3.2 F2 —— P2 真 VA 走锚（8/8 完成，字节不变；括号内 Δ）

| 勘误号 | 文件:行 | 原锚点 | 真值 VA（写入） | Δ |
|---|---|---|---|---|
| ASM-FIX-1 | docs/re/deep_dive_sweeps_closure.md:269（§2.2 正文） | 0x006F876B | **0x006F876F** | +4 |
| ASM-FIX-1 | docs/re/deep_dive_sweeps_closure.md:265（附带发现块，改为「已落地」） | 0x006F876B | 0x006F876F | +4 |
| ASM-FIX-23 | docs/re/re_sprint_S14_report.md:472 | 0x00409510 | 0x00409511 | +1 |
| ASM-FIX-24 | docs/re/re_sprint_S14_report.md:479 | 0x0053E516 | 0x0053E510 | −6 |
| ASM-FIX-24 | docs/re/re_sprint_S14_report.md:480 | 0x0053E57A | 0x0053E574 | −6 |
| ASM-FIX-29 | docs/re/re_sprint_S7_report.md:47 | 0x004D37EA | 0x004D37F5 | +11 |
| ASM-FIX-29 | docs/re/re_sprint_S7_report.md:48 | 0x004D37D2 | 0x004D37DD | +11 |
| ASM-FIX-30 | docs/re/savegame_block_manifest.md:126 | 0x0067E0A9 | 0x0067E0A8 | −1 |

### 3.3 F3 —— N-2 改锚（已裁定，执行完毕）

| 勘误号 | 文件:行 | 改后 | 说明 |
|---|---|---|---|
| ASM-FIX-3 | docs/re/deep_dive_sweeps_closure.md:456（§5.2 实证定位） | 锚点 `0x007BC8A3: 66 8B 01`；`A 类 · [实证]` 成立 | 原「须重新锚定后方可维持」表述改为「已在本批恢复锚点」 |
| ASM-FIX-3 | docs/re/deep_dive_sweeps_closure.md:462（DA4-9 勘误块） | 追加「裁定执行」段：真锚点 + 循环体逐条复核 | 原文（含 0x004926C0 失效判定）**逐字保留**，仅尾部追加 |
| ASM-FIX-3 | docs/re/deep_dive_sweeps_closure.md:573（§6 行 29） | 锚点格 → `0x007BC8A3: 66 8B 01`；等级格 `[实证]（待重新锚定）` → `[实证]` | **撤销「待重新锚定」** |
| ASM-FIX-3 | docs/re/deep_dive_sweeps_closure.md:586（DA4-10 汇总表行 29） | 原记列为引、真锚列落地；结论「锚点已恢复」 | 与 §5.2/§6 自洽 |
| ASM-FIX-3 | docs/re/nonrle_blit_and_named_hotspots.md:273（§6 Item 2） | 补入锚点 `0x007BC8A3: 66 8B 01` + `【A 类 · [实证]】` | 该行原无地址，属**补锚** |

### 3.4 F4 —— P3 定性标注（27 条，字节未改）

7 份 sprint 报告统一加注（`ASM-FIX-35`，位置：各报告头部「证据分级/纪律」行尾部）：
`docs/re/re_sprint_S2_report.md:10`、`S3:8`、`S5:6`、`S7:4`、`S11:8`、`S14:6`、`S17:7`。
标注原文（统一）：

> 〔ASM-FIX-35 · F4 统一标注〕本报告各节 asm 清单属**手写示意清单**：字节按语义规范化书写（短/长编码互写、寄存器名与 ModRM 规范化、比较类指令等价互写、清单整体偏移 ±1~±11 字节），**与二进制逐字节不保证一致**，不得作为 Hook 安装点或补丁字节的直接依据；P3 类漂移（27 条）按此定性、不逐字节改写。可复算的逐字节断言以 `out/re_work/asm_scan/claims.txt`（`tools/audit_bytes.py` 全绿）与各条已加勘误块为准。

**验证 F4 未改字节**：复扫 P3-LIST-DRIFT 计数 **27 → 27**（BEFORE/AFTER 均为 27）——若本批动过这些清单字节，该计数必然变化。

### 3.5 F5 —— U-1/U-2 区段配准（±0x200 滑窗逐偏移比对 + Capstone）

| # | 区段 | 搜索范围与方法 | 结论 | 处置 |
|---|---|---|---|---|
| U-1 | `ARCHITECTURE_ATLAS.md:1511-1514`（0x0064DACE） | 0x0064DACE ±0x200 内对原记 4 条指令逐条滑窗；另做全镜像模式普查 | pattern[0] `A1 30 B2 A8 00` 窗内 0 命中（全镜像 458 处 ⇒ 高频公共指令）；`E8 52 1A F6 FF` 全镜像 0 命中；目标 0x5AF530 全 .text **0 处调用站点** | **真指令序列已逐字节订正**；原记块标「**来源构建不明 · 待重新锚定**」+ 影响面警示 |
| U-2 | `offline_verification_alternatives.md:132/133` | 0x006BAC10 / 0x006BAE40 ±0x200 滑窗；全 .text 模式普查 | 0x006BAC10 **落指令中间**（真指令起 0x006BAC0A）；0x006BAE40 边界但为 `3B F0 cmp esi,eax`；声明序言窗内 0 命中，全 .text 仅 3 处 / 7 处（Δ>1MB） | 标「**来源构建不明 · 待重新锚定**」；**候选址全列**（Lock 3 处 / Unlock 7 处）供下一批以 DirectDraw vtable 调用图反查（**不猜、不定谳**） |
| U-3a | `particle_fog_owner_evidence.md:226-228` | 0x0062FD6D ±0x200 滑窗 + 序列组合普查 + 同函数一致性 | **真锚点 = 0x0062DE6D**（Δ=−0x1F00）；与原记 VA 同节写点同函数、字段 +0xE0 一致、指令间距 +6/+2 一致 | 就地改锚（3 行）+ 标「函数归属须重新定谳（不属 0x0062FD60）」 |
| U-3b | `landing_equivalence_static_proof.md:276-279` | ±0x200 滑窗（含指令边界对齐校验） | 0x007C8E24: C3（`ret`，本函数已结束）；0x007C8E25: 55 8B EC（下一函数起点）；原记 `85 C0 75 14` 全镜像 44 处，窗内**无边界对齐命中** | 标「**来源构建不明 · 待重新锚定**」；同页 `operator delete`（0x007C8B3D）复核无误 |
| U-3c | `blitter_microkernel_deep_dive.md:198-200` | 0x00496828 ±0x40 滑窗 + 0x00496820 起全窗口反汇编 | **真序列在 0x00496820 起、整体归位**（原记 5 行 −1 且 `push ecx` 误置） | 就地订正 5 行（196–200），行 201 起原本正确 |

### 3.6 验收②③ —— 扫描前后对比表（`out/re_work/asm_fix/before_after_table.md` 机器生成）

**表 B（同口径：ASM-SCAN 快照的 150 个文件）**

| 分类 | BEFORE | AFTER（同口径） | Δ |
|---|---|---|---|
| P1-BYTE-ERROR | 36 | **2** | −34 |
| P2-VA-DRIFT | 8 | **1** | −7 |
| P3-LIST-DRIFT | 27 | 27 | 0 |
| P4-REVIEW | 43 | 25 | −18 |
| A-ARTIFACT | 178 | 179 | +1 |
| B-PATCH | 26 | 26 | 0 |
| B-ERRATA-QUOTE | 3 | 18 | +15 |
| **②③ 合计** | **321** | **278** | **−43** |

**表 A（全库口径：154 文件 = 快照 150 + 窗口后新增 3 份 + 本报告）**：②③ 合计 **332**，分类分布 **P1 38 / P2 9 / P3 27 / P4 29 / A-ARTIFACT 179 / B-ERRATA-QUOTE 24 / B-PATCH 26**。构成拆解：同口径 278 + `docs/re/inline_assertion_scan.md`（ASM-SCAN 报告本体，其 §3.1/§3.2 表格本身即在引用全部原记字节）48 条（P1 36 + P2 8 + 其他 4）**+ 本报告自身 6 条**（全部带「原记」标记 ⇒ R-ERRATA）。全库 P1/P2 的构成 = 禁区 2 + inline_assertion_scan 36 = **38**（P1）／禁区 1 + inline 8 = **9**（P2）。新增文档非本批勘误对象（后两文件更非授权写作范围）。

**行级迁移（同口径）**：44 行的不符断言**消失**（已复扫为 EXACT）；16 行由 P1/P2/P4 **转入 B-ERRATA-QUOTE**（即「勘误块引用原值」——预期不符，正是本批「保留原记」的机器表现）；2 行为窗口后其他执行方写入产生（`REVERSE_ENGINEERING_AND_PATCHES.md:247` P2、`docs/RE_COORDINATION.md:1318` A-ARTIFACT，见 §5 双快照声明）。

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|---|---|---|---|---|
| L1 | `REVERSE_ENGINEERING_AND_PATCHES.md:1992` 与 `docs/RE_COORDINATION.md:1240` 记 `0x006F8737: C1 F8 01`（实测 `D1 F8`，原串全镜像 0 命中） | **禁区**（任务卡明令不得触碰这两份 Lead 所有文件）；同为 T-2 勘误的 closure §2.2 已订正（B-ERRATA-QUOTE），此两处为台账侧复述 | Lead 按 closure:262 的措辞就地订正（1 行 1 处）；或授权本批追加 | P1 |
| L2 | `REVERSE_ENGINEERING_AND_PATCHES.md:247` 原记锚点 `0x00655C50: 89 44 24 28 A1 50 35 B7 00`（实测该串真锚 = **0x00655D38**, Δ+0xE8） | 同上（**禁区**）；该行系 Lead 于扫描窗口后（10:01）写入 | 交给 Lead：改锚 `0x00655D38`（`89 44 24 28 A1 50 35 B7 00`） | P1 |
| L3 | `docs/re/inline_assertion_scan.md` 自身 §3.1/§3.2 表格 48 条对 ②③ 的引用（P1 36 / P2 8） | 该文件**不在** errata_table.md 的 P1/P2 目标文档清单内，且非本批授权写作范围 | 二选一：① 给该报告两处表格加「原记」标记（机器即归 R-ERRATA）；② 在下次扫描的排除规则中显式豁免「扫描器自身报告」 | P2 |
| L4 | U-1/`ATLAS:1511-1514` 的「唯一共享 RNG 每帧消费 1 次」**字节级证据链缺失** | 原锚点全镜像 0 命中、其目标 0x5AF530 全 .text 0 处调用站点、且该 VA 非函数入口 ⇒ 静态只能证伪，无法证真 | 以 `RandomObject::Random` 的**真实入口**（由 `0x64DAB0` 帧 CRC 函数体内的调用点反查）重建锚点；建议专项（含 `Rules+0xFEC` 邻域） | **P0** |
| L5 | U-2 `Surface::Lock/Unlock` 入口 | `55 8B EC …` 是高频公共序言，模式普查无法唯一定位；声明锚点落指令中间 | 用 `DirectDrawSurface` vtable 槽（`FF 50/52 60` 等）+ 调用图反查真实入口后重锚；候选址已列（3 处 / 7 处） | P2 |
| L6 | `S2:167`/`superweapon:807` 的 `call 0x0065C7E0` 站点 | 全镜像 415 处同目标调用，±0x400 内唯一位于 0x004AA6A2（Δ+0x177），**多候选不唯一** | 以函数边界（`0x004AA440` 航线计算入口）约束后再定 | P2 |
| L7 | `S2:371` 三处 `call 0x006CF240`（CDF98h/CDFA6h/CDFB1h） | 同目标多候选，Δ 分别 −0x1A/−0x0B/−0x01 | 以实参语义（`&Animation` vs `0xB0C110`）判定 | P2 |
| L8 | `S2:421/423`、`S14:475`、`S14:489-490` 后续语义 | 原记字节为手写规范化/跨指令拼接，VA 落指令中间 | 按函数边界重扫邻域后重锚 | P2 |
| L9 | closure 记「`66 8B 01` 全镜像 66 处」，实测 **65 处** | 属计数微勘误，不在本批授权的 F1–F5 条目内 | Lead 一句订正（`closure:461`） | P3 |
| L10 | `trigger_runtime:341/440/443`、`superweapon:348-395`、`weapons_damage_production:785-815` 等 P4 条目（25 条） | F1/F2 未覆盖（任务卡未列入），语义判读量大 | 下一批按函数边界批量复扫 | P2 |

> **〔ASM-FIX2 追加 · 2026-09-27〕本表状态更新（本批只读/授权范围内）**：
> - **L4（P0）→ 已闭环**：帧 CRC 路径的局内 RNG 消费点已用实测锚点重建（`0x0064DE3F` + `0x0064DE70 → 0x00650A90` 内 `0x650AB7`/`0x650AF2` 之一 ⇒ 每逻辑帧 **2** 次），见 `ARCHITECTURE_ATLAS.md §9.2`〔ASM-FIX2-1〕。
> - **L5（P2）→ 已闭环**：`Surface::Lock/Unlock` 真锚定为 `DSurface::Lock = 0x004BAD80` / `DSurface::Unlock = 0x004BAF40`（RTTI vtable `0x007E85D4` 槽 `+0x5C`/`+0x60`；体内 `call [reg+0x64]` = `IDirectDrawSurface7::Lock`），见 `offline_verification_alternatives.md:132/133`〔ASM-FIX2-2〕。
> - **L3（P2）→ 已闭环（采纳建议的「排除规则」方案）**：`extract_claims.py` 增加扫描器/勘误报告文件级豁免（`--include-self` 可关），`classify.py` 增加行级 `selfref` 标记（含勘误区措辞识别）；复扫不再把历史引用计为 P1/P2。
> - **L1/L2（P1）→ 仍在禁区**：本批**未触碰** `REVERSE_ENGINEERING_AND_PATCHES.md` 与 `docs/RE_COORDINATION.md`。复扫现存 2 条 P1 均为这两份文件**引用已证伪锚点**的行（含「证伪/待重新锚定」措辞，现按 F3 规则归 `S-SELFREF`）：`REVERSE_ENGINEERING_AND_PATCHES.md:2215` 与 `docs/RE_COORDINATION.md:1352`（均记 `0x0064DAD9: E8 52 1A F6 FF`）⇒ 建议 Lead 就地改为真锚点或保留勘误措辞。

---

## [5] 写作用域合规声明

**改动文件清单（20 个，全部在 `docs/re/`，均为 errata_table.md 列出的 P1/P2 目标文档）**：逐文件改动数与字节数/mtime 见 `out/re_work/asm_fix/change_list.md` §「逐文件改动与磁盘状态」；摘要：`ARCHITECTURE_ATLAS.md`(9)、`re_sprint_S14_report.md`(11)、`re_sprint_S2_report.md`(11)、`deep_dive_sweeps_closure.md`(6)、`blitter_microkernel_deep_dive.md`(5)、`landing_equivalence_static_proof.md`(4)、`re_sprint_S3_report.md`(4)、`re_sprint_S5_report.md`(4)、`particle_fog_owner_evidence.md`(3)、`re_sprint_S7_report.md`(3)、其余 10 文件各 1–2 条，**共 76 条就地编辑**。

**未触碰清单（逐类声明）**：
1. **REVERSE_ENGINEERING_AND_PATCHES.md、docs/RE_COORDINATION.md** —— Lead 所有，**零写入**（本批只读；`REVERSE:1992/247`、`RE_COORD:1240` 的残余 P1/P2 已列入 §4 交 Lead）。
2. **docs/DESIGN.md、ra2forge/**、mcp/**、ra2opt/**、docs/re/ra2forge_fix_forge2.md** —— FORGE-2 正在写，**零写入**（`ra2forge_fix_forge1/2.md` 仅出现在扫描的 files_scanned 列表中，本批未打开写入）。
3. **ra2render/**、ra2youli/**、out/钢铁残响/** 、其他未列入 errata 的 docs —— **零写入**。
4. **二进制** —— `ra2youli/gamemd.exe` **全程只读**：MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（前后一致）、4,825,360 B、mtime 2026-09-25 16:10:48 未变；`.text` 段哈希 `c0368a17…4eb738`、`.detour` 原生签名完好；未启动游戏、未注入、未改任何 exe/dll。

**双快照声明**：ASM-SCAN 原快照窗口为 2026-09-27 09:54–09:59（150 文件）。本批勘误期间工作区被其他会话改写：新增 `docs/re/inline_assertion_scan.md`、`docs/re/ra2forge_fix_forge1.md`、`docs/re/ra2forge_fix_forge2.md`（扫描数 150→153），且 `REVERSE_ENGINEERING_AND_PATCHES.md` / `docs/RE_COORDINATION.md` 出现扫描窗口后写入的行（`:247`、`:1318`，**非本执行方所写**，本批未触碰二者）。故对比表同时给出「全库口径」与「同口径（150 文件）」两栏；**勘误前快照已完整保存**于 `out/re_work/asm_fix/before/`。
**被动再生成**：按任务卡要求重跑 ASM-SCAN，`out/re_work/asm_scan/` 下的 `claims_raw.json / classified.json / mismatch_ranked.tsv / errata_table.md / triage_tables.md / claims.txt` 被同名覆盖为新结果（**勘误前版本已先复制到 `out/re_work/asm_fix/before/`**）。除此之外未写任何他人目录。

---

## [6] 门禁实跑输出（原文粘贴）

命令与输出（`cd /d D:\Project\ra2-campaign-forge`）：

```text
> python tools\verify_anchors.py
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

> python tools\audit_bytes.py docs/re/anchor_claims.txt
合计 323 条：OK=323  MISMATCH/NOREAD=0          （金标准 323 条未动）

> python tools\audit_bytes.py out/re_work/asm_scan/claims.txt      （附加自证，非任务卡要求）
合计 1273 条：OK=1273  MISMATCH/NOREAD=0        （本批新写订正字节串全部通过）
```

**验收复核（勘误后重跑 ASM-SCAN 原文命令）**：

```bat
cd /d D:\Project\ra2-campaign-forge
python out\re_work\asm_scan\extract_claims.py --min-bytes 0
python out\re_work\asm_scan\classify.py
python out\re_work\asm_scan\triage.py
python out\re_work\asm_scan\build_errata.py
python out\re_work\asm_fix\compare_scan.py          :: 生成前后对比表
```

```text
scanned files : 154
claims        : 29115
classify      : {'NOBYTES': 26293, 'EXACT': 2396, 'MISMATCH': 320, 'OOB': 241, 'PREFIX_LEN': 12, 'ALIAS': 1}
triage buckets: {'OK-EXACT': 2396, 'R-ERRATA': 25, 'R-PATCH': 26, 'R-ERR-VA': 10, 'R-NONBYTE-1B': 159,
                 'R-CONCAT': 12, 'R-CANDIDATE': 100, 'OK-OOB': 241, 'OK-ALIAS': 1}
claims.txt    : 1264 条 EXACT 断言 (dedup)
build_errata  : {'P1-BYTE-ERROR': 38, 'P2-VA-DRIFT': 9, 'P3-LIST-DRIFT': 27, 'P4-REVIEW': 29,
                 'A-ARTIFACT': 179, 'B-ERRATA-QUOTE': 24, 'B-PATCH': 26}
compare_scan  : BEFORE ②③ = 321 / AFTER(all) = 332 / AFTER(same-file) = 278
                residual P1(same-file) = 2   residual P2(same-file) = 1   （均在禁区文件，见 §4 L1/L2）
```

---

## [7] 风险与红线提示

**逐条回答四问**（触及者必须走 MP 门控矩阵/真机对拍验收）：

| 触及项 | 是否触及 | 说明 |
|---|---|---|
| ① 同步语义 / 命令序 | **触及（证据链层）** | `S14:489/490`（联机滞后补偿 +10ms 写点 0x887328/0x887330）、`S5/S14`「帧前台跳过 Sleep」行的原记字节被证为**手写拼接**；结论（双写成立）在本窗内复核成立，但**精确写点次序须重新复核**后方可作为补丁依据。**需 MP 门控矩阵 + 真机对拍验收**，本批不宣称任何同步结论变更。 |
| ② 随机数消费序 | **触及（且为最大风险）** | `ATLAS §9.2`「唯一共享 RNG 每逻辑帧固定消费 1 次」的锚点 **0x0064DAD9: call 0x005AF530 全镜像 0 命中**，且全 .text **无任何调用站点**以 0x405AF530 为目标。**结论方向不变（该章其余论证与 S2 §7.2/S7 的 RNG 闭环独立成立），但本批已就地加警示：不得再引用该锚点**；重建锚点前**禁止**以该条作为「谁可调用 RNG」的字节级依据。**需 MP 门控矩阵/真机对拍验收**。 |
| ③ 存档结构 | **触及（证据链层）** | `S2:345`（v5 Load `0x6CDEF0` 内 `call 0x410380` → 真锚 0x006CDEFB）、`S2:352-355`（4 重虚表恢复写点 → `mov [esi+…]`）；**字段/结构结论无变更**，仅安装点地址与寄存器语义订正。**建议在真机对拍（存档往返）中复验**。 |
| ④ 渲染像素等价性 | **触及（结论反而增强）** | N-2 改锚 `0x007BC8A3: 66 8B 01` 使「16 位源像素流 / 跳色键 / 非 8 位索引流」恢复 `A 类 · [实证]`；blitter 微核清单 5 行订正。像素等价性仍以**真机渲染对拍**为准（静态只证语义，不证像素）。 |

**红线遵守**：未启动游戏、未注入、未改 exe/dll、未伪造实测（所有「实测」均来自只读脚本对基线镜像的现算，脚本与原始输出均在本交付物内可复跑）、未越界写入。**本批不宣称「零风险 / 零 Desync」**。

---

## [8] 交付物清单

| 类别 | 路径 | 规模 |
|---|---|---|
| **勘误后目标文档** | `docs/re/` 下 **20 个**（见 §5 清单） | 76 条就地编辑 |
| **本报告** | `docs/re/asm_fix_report.md` | 本文件 |
| 只读探针 | `out/re_work/asm_fix/probe.py` | VA→字节/Capstone/边界/普查/call 站点/滑窗配准 |
| 事务编辑器 | `out/re_work/asm_fix/apply_edits.py` | 先全量校验后写盘；空 `old` = 行尾追加 |
| 勘误规格（机器记录） | `out/re_work/asm_fix/edits_{a,b,c,d,e}.json` + `edits_all.json` | 76 条（含改前/改后全文） |
| 报告自查修正记录 | `out/re_work/asm_fix/edits_f.json` / `edits_g.json`（RPT-1…RPT-11，27 条） | 本报告自身的「机器可读化」修正：使复扫时本报告只产生带「原记」标记的 R-ERRATA 行（6 条）、**不产生任何 P1/P2/P4 噪声** |
| 改动清单 | `out/re_work/asm_fix/change_list.md` | 逐条 改前/改后 + 逐文件字节数/mtime |
| 前后对比 | `out/re_work/asm_fix/before_after_table.md`（`compare_scan.py`） | 全库/同口径双表 + 残余逐条理由 |
| 行级迁移 | `out/re_work/asm_fix/diff_rows.py` 输出 | 44 行消失 / 16 行转 B-ERRATA-QUOTE / 2 行为他人写入 |
| 勘误前快照 | `out/re_work/asm_fix/before/`（6 个原始产物） | 321 条基线，可随时复算 |
| 探针作业单 | `out/re_work/asm_fix/job_*.json` | 8 组、约 45 个取证任务（可复跑） |
| 复扫产物（任务卡要求） | `out/re_work/asm_scan/{claims_raw.json, classified.json, mismatch_ranked.tsv, errata_table.md, triage_tables.md, claims.txt}` | 29,115 claims；claims.txt 1273 条 |
| 断言 | `out/re_work/asm_scan/claims.txt` | **1273 条**（`audit_bytes.py` 1273/1273 OK） |

---

## [9] 待裁决项

1. **是否给 ASM-SCAN 报告自身的 ②③ 表加「原记」标记**（L3）：加标记后复扫 P1/P2 可再降 44 条（该报告 §3.1/§3.2 本质是历史引用）。建议采纳「扫描排除规则豁免扫描器自身报告」而非改其正文——理由：保持历史报告不可变。
2. **禁区三行**（`REVERSE:1992/247`、`RE_COORD:1240`，L1/L2）：建议 Lead 就地订正（改动量 3 行），否则任何复扫都会残留 P1×2/P2×1。**是否授权本批执行？**
3. **L4（帧 CRC RNG 锚点重建）**：建议立专项（P0）——以 `0x0064DAB0` 函数体内真实调用点为起点反查 `RandomObject::Random` 入口，再重建「唯一共享 RNG」断言。本批不越权改判结论。
4. **L9（65 vs 66 微勘误）**：closure:461 记「66 处」，实测 65；是否顺手订正？（本批未动，因不在 F1–F5 授权条目内）
5. **F4 标注的覆盖范围**：本批按「sprint 报告」7 份统一加注；若 Lead 希望同样标注扩展到非 sprint 文档（`fx_draw_chain.md`、`clock_frame_loop.md`、`audio_input_hotspots.md` 等手写清单密集文档），请下达追加批次。
6. **`S2:167/superweapon:807` 与 `S2:371` 的多候选重锚**（L6/L7）：是否开放「按函数边界 + 实参语义」的定向重锚批次？本批按「禁止猜」只列候选、不定谳。
