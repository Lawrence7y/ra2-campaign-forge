# C10 · P0 全镜像普查第 10 片（最后一片）— PROGRESS

> 卡号 C10｜执行 2026-11-17｜目标 `ra2youli\gamemd.exe`（ImageBase 0x400000，SHA-256 73201CC0…F67476，只读）
> 片：`function_atlas.tsv` 逻辑行 **11629–12916**（data[11628:12916]，**1288** 函数），入口 **0x773500 – 0x7E038D**（镜像尾部）
> 通道：capstone 5.0.7(skipdata=True，全 .text 1,394,120 条) + 自写 struct PE(RTTI/字节扫) + pefile 2024.8.26；**本卡未用 Ghidra**
> 写域：仅 `lead\next_re_20261117_r14\C10_census\`

## 分级定义（R14_COMMON §6-9，同 C01–C09）
- `[已证]`=YRpp JMP_THIS/re_atlas-kb 具名地址（剔除 `noinit_t`/`Unsorted::sub_`/`CRT::int`）；`[静态推断]`=RTTI 虚表类唯一映射 Sxx(core)/模块；`[未证]`=字符串/API/邻居投票/零证据
- **high 判据**：self_known 具名 49 + vtable 类 core 映射 205 = **254**；med/low 不计入

## 结论表
| 项 | 值 | 分级 | 证据路径 |
|---|---|---|---|
| 本片函数数 | **1288** | [已证] | EVIDENCE/slice_raw.tsv；work/verify_core.py CORE1 |
| 分类完成度 | 1288/1288 全给 Sxx+置信度+一行语义 | [已证] | coverage_delta.tsv；EVIDENCE/classification_trace.tsv |
| high 置信 | **254 / 1288 = 19.72%** | [已证] | work/verify_core.py CORE2 |
| 证据分级 | [已证] 49 / [静态推断] 259 / [未证] 980 | [已证] | classification_trace.tsv grade 列 |
| 自动证据覆盖 | vtable 槽 239 函数 / 具名 49 / 模块 54 / 字符串 2 | [已证] | EVIDENCE/vtmap_hits.tsv、known_hits.tsv |
| 虚表槽自校 | **14044**（v2.json 13351，+693）| [已证] | work/rtti_independent.json；delta {1:794,0:327,-1:85,-2:8} |
| atlas 空洞三通道 | call32 **36** / jmp32 **71** / jmp8 **169** | [已证] | atlas_gaps.tsv；work/verify_core.py CORE3 |
| 行数 / 独立地址 | **276 行 / 264 独立地址**（12 地址被 2 通道命中）| [已证] | work/gap_stats.json |
| 疑似真入口合计 | **12**（卡判据 e 严格；宽松 r14_strict=14）| [已证] | EVIDENCE/entry_criteria.tsv；work/verify_core.py CORE4 |
| 虚表直指未收录入口 | **6** | [已证] | EVIDENCE/vt_direct_entries.tsv；work/vt_direct.json |

## 核心数字（给审计员复算）
1. **本片函数数=1288**：`wc -l coverage_delta.tsv`=1288；atlas `data[11628:12916]`=1288；CORE1 三路一致。
2. **high=254**：`awk -F'\t' '$3=="high"' EVIDENCE/classification_trace.tsv|wc -l`=254；分解 self_known 49 + vtable-core 205；交叉 `[已证]` 49。
3. **三通道=36/71/169；276 行/264 独立地址**。CORE3（pefile+op_str 独立重扫）三数全 match；12 地址双通道命中(276−264)。jmp32 71 中 69 非分支标签、2 分支标签。
4. **疑似真入口=12**（判据 e 全满足：16B 对齐 + prev∈{nop,ret,jmp,int3} + 非 jcc 目的 + push ebp/sub esp 序言）：`0x776490/0x776EB0/0x779A40/0x77DFD0/0x780A90/0x780E30/0x781090/0x796DE0/0x796ED0/0x796FC0/0x79C3A0/0x7A2330`，全为 call32（**jmp32 真入口 0/71**，印证坑 e）。两条独立实现（struct 通道 entry_criteria.py + pefile 通道 verify_core.py CORE4）均得 12。宽松 r14 口径=14，多出的 `0x7AEEC0`(push ecx)/`0x7DD2E0`(mov 开头) 无 push ebp/sub esp 序言，已剔除不放宽。
5. **虚表直指未收录入口=6**：`0x7AC9C0/0x7B4310/0x7B9D90/0x7BC7D0/0x7BC870/0x7BC920`。双通道（自写 struct PE RTTI vs pefile 重做）slots 均 6692、6 入口完全一致；两口径（not-in-entries / owner()==None）均得 6（无落在已有函数体内者）。

## 各子系统计数（high 分母=254）
| Sxx | n | high | Sxx | n | high | Sxx | n | high |
|---|---:|---:|---|---:|---:|---|---:|---:|
| S01 | 0 | 0 | S08 | 0 | 0 | S15 | 0 | 0 |
| S02 | 307 | 37 | S09 | 50 | 20 | S16 | 0 | 0 |
| S03 | 7 | 5 | S10 | 0 | 0 | S17 | 0 | 0 |
| S04 | 13 | 0 | S11 | 0 | 0 | S18 | 223 | 149 |
| S05 | 1 | 0 | S12 | 0 | 0 | S19 | 3 | 0 |
| S06 | 2 | 0 | S13 | 0 | 0 | S20 | 1 | 0 |
| S07 | 49 | 43 | S14 | 2 | 0 | S21 | 0 | 0 |
| S22 | 630 | 0 | | | | | | |
合计 1288。本片为**镜像尾段**：Westwood Online / wonline.cpp / WOL 聊天 / Winsock / Modem / Web(S18) 为主，CRT 运行时 str*/wcs*/mem*/alloc + 异常 RTTI(S02) 次之，WWMouseClass(S09)、BSurface/XSurface/DSurface/T_Blit*(S07)、FilePipe/FileStraw(S03)；S22 兜底 630（577 零证据 + 泛型/内联）。S01/S10/S11/S12/S13/S15/S16/S17/S21 本段无落点（非全局不存在）。

## 双通道与纪律落实
- 通道 A(atlas)：entry+size 作切片与 owner() 区间包含判定（非 entry_at_or_before，抽检 owner(0x482854)=None）。
- 通道 B1(不依赖 atlas)：自写 struct PE 从 .rdata COL→TD 恢复 RTTI 真实槽(14044)；B2(不依赖 atlas)：自写 struct PE + capstone skipdata 按操作码字节 E8/E9/EB 分通道；C 通道 pefile+op_str + CORE4 第三实现复核。三通道互不 import 判定产物。
- capstone 全程 skipdata=True；boundary_check "未判定"保留 unknown 不当 False（本片 0 例 bail；2 例 False 系真实指令内部命中 `add byte[ebp+0x53]`，落在已有函数体内不入 gap 集）。
- 反坑(a)：槽数自校 14044 非 13351；反坑(c)：B1/B2/C 独立实现；反坑(d)：self_known vs RTTI 类 16 一致/0 冲突（无误挂）；反坑(e)：真入口严格判据 12 不放宽。
- 写卡前已 grep 主台账；一行语义均标 `[未证]` 猜测，未写新 `[已证]` 发现；未改 gamemd.exe/ddraw.dll/ra2youli\；未写台账；未 git commit/push；未改 COVERAGE\coverage.tsv（只交 delta）。

## 主要缺口
- 577 零证据函数归 S22；建议 P1 用 YRpp/kb 二次细化（多为 WOL 适配器与 CRT 内联/泛型）。
- 169 个 jmp8 洞目标全为洞内短跳（首指令 mov/cmp/test/call/push），不计真入口（见 UNKNOWNS）。
- S04(13)/S19(3)/S20(1)/S14(2) high=0：仅字符串/API 弱命中，无 core 类具名（非全局不存在）。
