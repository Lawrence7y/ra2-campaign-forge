# C01 · P0 全镜像普查第 1 片 — PROGRESS（FIX round）

- 卡号 C01｜切片：function_atlas.tsv 数据行 1–1292（不含表头）｜地址 0x00401000–0x00456DFC
- 目标 ra2youli\gamemd.exe，SHA-256 73201CC0…F67476，ImageBase 0x400000，只读
- 工具：Python 3.12.10 / capstone 5.0.7（skipdata=True）/ pefile 2024.8.26；未用 Ghidra

## 分级定义（三级，R13 §6-9）
- `[已证]` = KB22 虚表槽定名 / YRpp 具名（非 `sub_XXXXXX` 占位）/ KB 具名方法（非裸类名）
- `[静态推断]` = RTTI 虚表类归属 / 字符串或导入 API 关键字 / 已知邻接传播 / YRpp 占位名
- `[未证]` = 无上述证据，仅按地址段弱先验猜测

## 子系统计数（PLAN R14 §1，S01–S22）
| Sxx | n | Sxx | n | Sxx | n | Sxx | n |
|---|---:|---|---:|---|---:|---|---:|
| S01 | 11 | S02 | 13 | S03 | 53 | S04 | 5 |
| S05 | 302 | S06 | 85 | S07 | 132 | S08 | 2 |
| S09 | 0 | S10 | 0 | S11 | 11 | S12 | 126 |
| S13 | 53 | S14 | 39 | S15 | 0 | S16 | 1 |
| S17 | 11 | S18 | 0 | S19 | 286 | S20 | 76 |
| S21 | 0 | S22 | 86 | | | | |

合计 1292。前段（0x401000–0x409000）以 S19 音频/VocClass 为主；

## 分级统计（FIX 后）
- `[已证]` = **96**；`[静态推断]` = 703；`[未证]` = 493
- high 置信占比 = 96/1292 = **7.43%**（首轮 102/7.89%，6 行 `sub_XXXXXX` 占位名降级）
- 无法归类数（仅 `[未证]`）= **493**（首轮 503，↓10）

## 核心数字（给审计员复算）
1. **本片函数数 = 1292**（与切片行数一致）。
   复算：`awk 'NR>1 && NR<=1293' function_atlas.tsv | wc -l` → 1292；总函数 12916。
2. **high 置信计数 = 96**（`[已证]` 行数）。
   复算：`grep -c $'\t\[已证\]' C01_census/coverage_delta.tsv` → 96。
   构成：KB22 槽 19 + YRpp 具名（排除 6 个占位） + KB 具名方法 1（0x410B90 WriteINI）。
3. **atlas 空洞入口数 = 下界 7 / 上界 9**（首轮 2，仅下界；审计指出漏前向通道）。
   复算下界：`awk 'NR>1 && $2=="call-jmp" || $2=="orphan"' C01_census/atlas_gaps.tsv | wc -l` → 7
   （2 个 call-jmp：0x4039C0/0x42E1C0 + 5 个 orphan：0x4093C0/0x412280/0x427850/0x42E990/0x435B50，全高置信）。
   复算上界：`awk 'NR>1' C01_census/atlas_gaps.tsv | wc -l` → 9（+0x433060 med、0x432BF0 low 候选）。

## 双通道与纪律落实
- 通道 B1（目标扫，不依赖 atlas）：全 `.text` capstone 线性扫 call/jmp 目标（`work/scan_atlas_gaps.py`），
  1,394,120 指令 / 17,997 目标 / 片内 1,481 / 非 entry 879 / 未覆盖 45 → 2 真入口（E8 rel32 调用点经字节通道复验）。
- 通道 B2（前向孤儿扫，不依赖 atlas entry+size、不依赖引用图）：全 `.text` 指令起点上筛
  「16B 对齐 + 未被 atlas 区间覆盖 + 函数序言 + 前驱 ret/jmp 无间隔」（`work/orphan_forward.py`），得 5 个零引用孤儿入口；
  另逐条复核 0x433060（ret+14nop 后 sub-esp 序言，med）与 0x432BF0（ret4+nop 后 naked helper，low）。
- 通道 A（atlas）：仅作补集定义与分类输入，不作缺口发现。
- capstone 全程 `skipdata=True`；boundary 超 max_bytes 返 unknown；站点归属用区间包含（R13 §6-3/17）。
- 未改 gamemd.exe / ddraw.dll / ra2youli\ 下任何文件；未写台账；未 git commit/push。

## 未复发 C02 缺陷（加分项复核）
- C02「vtables_v2 slots 少 1」本卡未复发。`work/scan_rtti.py` 独立扫得 1214 虚表 / 14044 槽，
  与 `EVIDENCE/rtti_vtables.json` 的 n=1214/1214 全等；主表 0x7E1F50 n=24，`+0x60`=0x7FB160 是 COL 指针非函数，
  末槽 0x410570 在位；KB22 的 19 行槽号 19/19 吻合（`_audit\VERDICT.md` §四-25/26 独立确认）。

## 主要缺口
- 493 个 `[未证]` 无直接证据，靠地址段弱先验；建议 P1 用 YRpp/KB 二次细化。
- 0x432BF0 为 naked 小函数（无序言），仅 low 候选；建议 P1 用绑定表/调用上下文确认。
- 本片 0x00400000 段（CRT/入口）函数名缺失较多（S02 仅 13 个），可专门开卡。
