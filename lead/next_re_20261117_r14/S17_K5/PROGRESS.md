# S17-K5 · PROGRESS（≤50 行）

> 卡号 S17-K5｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）｜Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26｜未用 Ghidra。
> 时点：基线 `2026-11-18T07:33:00+08:00`，合 delta 复算 `2026-11-18T07:35:32+08:00`。写域仅 `lead\next_re_20261117_r14\S17_K5\`。

## 基线（纪律 9：先核对，卡面不符即停）
- `EVIDENCE/t0_baseline.txt`：coverage header 用逗号、数据行用 tab；统一小写 entry 后 S17∩atlas = **102**；named(S)=**92/102=90.20%**，grade 第 5 列 `[已证]`=**54/102=52.94%**，与卡面逐位一致 ⇒ 不停机。
- 卡面警告的 `slotN` 严格口径问题：现台账已含 `CStreamClass::slotN` 等旧名；本卡不重判旧台账，只保证**新交名不是占位名**（`DebugLogSink_behavior`，name_kind=behavioral）。

## 一句话结论
- 交 **1 行** S17 delta：`004068E0 → DebugLogSink_behavior`（[已证]，behavioral）。合入后 **named 93/102=91.18%，proved 55/102=53.92%**，为 S17 攒出 **1 个名字缓冲**。
- `0049F740`/`0049F8B0` 的字符串路已复算成立，但语义属 **COPYPROTECTION / launcher IPC / 注册表清理**，不是 S17；按卡要求如实报告并建议 D-37 改归属，不写入 S17 delta。

## 10 条残行逐条取证（过程 → 判定）
| entry | 取证过程（读盘） | 判定 |
|---|---|---|
| `004068E0` | 全入口到 ret 只有 `C3`；扫 1,672 个 E8 调用点：1,497(89.53%) 紧邻 `push imm32`，1,492 个 imm 解出可打印 C 串；全镜像 81,715 个 E8 的 push-imm32 基线仅 5.14%。 | **可定** `DebugLogSink_behavior`；body=无操作、调用者=日志 sink 两条独立证据；非占位名；无 name conflict。 |
| `0040E340` | 75B 全反汇编为双向链表摘链/挂链；无 vptr/RTTI/串；33 个调用者跨 S04/S07/S09/S21/S22。 | 不可定：只有通用行为，没有类/域锚，拒绝 `List::sub_`。 |
| `00427940` | 体内 `TEM`(0x7E1BC6 计算串)、`.SHP`(0x81834C)，调 `FileSystem::LoadFile`；3 个调用者 S09/S21。 | 不可定：可说“装载 SHP 类资源”，但对象类与存档域均未被两条独立证据钉住。 |
| `0042E410` | 32B 全反汇编：`[eax+0..0xC]` 连续写 4 个栈参数，`ret 0x10`；25 调用者跨 S06/S07/S09/S20/S22。 | 不可定：通用 setter，无 RTTI/槽/唯一调用者。 |
| `00433CF0` | UTF-16 逐字循环 + `jmp [ecx*4+0x433EA8]` 分派；调用者集中 UI/surface/drawing。 | 不可定：文本排版/宽度行走迹象，非 S17；无类名。 |
| `004355B0` | 25B 全反汇编：写 `[eax]`,`[eax+1]`,`[eax+2]`，`ret 0xC`；19 调用者跨 S04/S07/S09/S22。 | 不可定：3 字节 setter，无域/类证据。 |
| `0043AE50` | 40B：`[esi+8]` 为真时 delete `[esi]`，清 `[0]/[4]/[8]`；279 调用者；无 RTTI/vptr。 | 不可定： owning-buffer clear 形状，但类名不确定；不套 `Class::sub_`。 |
| `0049F740` | 体内直接 push `0x81F51C`=`COPYPROTECTION - Received message from launcher.\n`；`[esi+4]==0xBEEF` 时调 `MapViewOfFileEx`，失败/成功分别 push `***** MapViewOfFileEx() Failed!` / `The message says: %s`；唯一 E8 调用者 `0x5D4DB7`∈`sub_005D4D50`(S09/[未证])。 | 语义可定但**非 S17**：launcher 共享内存映射；建议 D-37 改归属，不进 S17 delta。 |
| `0049F8B0` | 体内 push `0x81F5B8`=`COPYPROTECTION - Shutdown\n`；`UnmapViewOfFile(global 0x89F75C)`，`RegOpenKeyExA(HKEY_CLASSES_ROOT,"WChat\SysID")`，`RegDeleteValueA("ID")`，`RegCloseKey`；唯一 E8 调用者 `0x6BEC3D`∈`sub_006BE1C0`(S04/[未证])。 | 语义可定但**非 S17**：COPYPROTECTION 关停/注册表清理；建议 D-37 改归属。 |
| `00773450` | `new(0x414)`，写 vptr `0x7F743C`；RTTI `COL+0xC→TD+8` 实读 `.?AVWebBrowser@@`；`CoCreateInstance`；无直接调用者。 | 类名可证但**非 S17**：嵌入式 WebBrowser 构造器；不改 S17 名。 |

## 双通道与纪律
- 通道 A：PE 节 + capstone(skipdata=True) 逐体反汇编、rel32 调用点、push-imm 基线，不依赖 atlas entry+size；通道 B：镜像 `.data` 串地址/`#` 注释回读、RTTI `COL+0xC→TD+8`、IAT 解析、CONFLICTS/主台账 grep。
- 站点归属用 atlas 区间包含；「不存在」查了 E8/dword/RTTI/串四路；写值逐字符核对；未写台账、未改游戏文件、未 git commit。

## 证据入口
- 基线/复算：`EVIDENCE/t0_baseline.txt`、`EVIDENCE/final_recompute.txt`。
- 命名：`EVIDENCE/4068e0_callsite_pattern.txt`、`EVIDENCE/targets_detail.txt#004068E0`、`EVIDENCE/conflict_check.txt`。
- 非 S17 字符串路：`EVIDENCE/string_scan_raw.txt`、`EVIDENCE/xref_copyprotect.txt`、`EVIDENCE/copyprotect_detail.txt`。
- 明细：`EVIDENCE/decision_matrix.tsv`、`EVIDENCE/targets_detail.txt`；脚本在 `work/`。
