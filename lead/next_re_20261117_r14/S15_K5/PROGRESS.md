# S15-K5 · PROGRESS（S15 触发器 · 纯静态 · 只找名字）

## 结论表（分母 = coverage.tsv subsystem=S15 ∩ function_atlas.tsv，entry 统一大写）

| 结论 | 分级 | 证据路径 |
|---|---|---|
| 现场复算：coverage S15=159 行，表外 `006E6080` 后分母 158；基线 named(S)=137/158=86.71%，proved=95/158=60.13%，need=ceil(0.9*158)=143，基线差 6 | [已证] | `EVIDENCE/t0_baseline.txt`; `work/t0_recompute.py` |
| 叠加 K3 2 行 + K4 2 行：merged named(S)=141/158=89.24%，merged proved=98/158=62.03%；`143-141=2`，与台账 §992/§996 的 141 完全一致 | [已证] | `EVIDENCE/t0_baseline.txt`; `..\S15-K3\coverage_delta.tsv`; `..\S15_K4\coverage_delta.tsv` |
| 叠加后仍**未达** DoD 第 1 条；本卡待补缺口确为 **2 个名字**，停机核验通过，不凑数 | [已证] | `EVIDENCE/t0_baseline.txt` |
| 本卡新命名 **0 条**；17 个残余 `sub_` 均未达到“两条真正独立证据”硬门槛，故 `coverage_delta.tsv` 为空（无表头、无数据行） | [已证] | `coverage_delta.tsv`; `EVIDENCE/residual_channel_matrix.tsv`; `UNKNOWNS.md` |
| 残差口径：K4 卡面“余 19”是未并 K3 delta 的现场口径；跨卡叠加后真实残余为 17（`006E2A10`/`006E2AA0`、`00726910`/`0071FA30` 已计入 141） | [已证] | `EVIDENCE/t0_baseline.txt`; `..\S15_K4\UNKNOWNS.md` |
| YRpp 全树对 17 个残余地址的字面量命中 0；K3 已证仅 2 个地址命中且已用于 K3 delta，本卡不重签 | [已证] | `EVIDENCE/yrpp_residual_addr_matches.txt`; `..\S15-K3\EVIDENCE\yrpp_addr_matches.txt` |
| 源码/调试串：`D:\ra2mdpost\TAction.CPP` 有 4 处有效代码引用，`D:\ra2mdpost\Event.CPP` 7 处（均非本 17 个入口）；本机无原始源码树/PDB，不能由文件名推方法名 | [已证] | `EVIDENCE/strings_trigger_candidates.txt`; `EVIDENCE/source_string_neighborhood.txt`; `EVIDENCE/source_string_xref_sites.txt` |
| EVA 通道：`EVA_*` 串 80 个有有效指令引用，与 17 个残余目标函数重叠 0；不能借 EVA 串给残余目标命名 | [已证] | `EVIDENCE/eva_xrefs.txt` |
| INI 键/哨兵通道：仅 `none`/`<none>` 等通用哨兵在 4 个残余目标内出现（`006E6310`/`006F1920`/`00727AA0`/`00751590`），无唯一 INI 键可定名 | [已证] | `EVIDENCE/ini_key_xrefs.txt` |
| 全 `.text` 直调/尾跳扫描：17 目标共 74 个直接 call/jmp 站点；全部目标的原始 dword 指针命中 0、`.rdata` 虚表槽命中 0；调用者均为跨类 helper/序列化/共享动作子步 | [已证] | `EVIDENCE/call_xrefs_residual_targets.tsv`; `EVIDENCE/residual_channel_matrix.tsv`; `EVIDENCE/disasm_residual_targets.txt` |
| 动作编号/调用者语义反推只给出“主题/Voc/Vox/TagType/TriggerType 名查找”等语义，缺第二条独立命名通道；按硬约束不命名 | [未证] | `UNKNOWNS.md`; `DISAGREE.md` |

## 核心数字（给审计）

1. **(a) 盘上基线 + 叠加 K3/K4 后真实分子/分母 = `141/158 = 89.24%`**；基线 `137/158`，K3 +2，K4 +2；`need=143`。复算：`python work/t0_recompute.py` → `EVIDENCE/t0_baseline.txt`。
2. **(b) 本卡新命名条数 = 0**；没有“每条两条证据路径”可列，因 17 条均未过双通道硬门槛。复算：`coverage_delta.tsv` 为空；通道证据见 `EVIDENCE/yrpp_residual_addr_matches.txt`、`EVIDENCE/eva_xrefs.txt`、`EVIDENCE/ini_key_xrefs.txt`、`EVIDENCE/call_xrefs_residual_targets.tsv`。
3. **(c) 并入后是否 ≥143：否**。`141 < 143`，仍差 **2**；本卡未改 `COVERAGE/coverage.tsv`、未写台账、未改游戏文件、未 git commit。
