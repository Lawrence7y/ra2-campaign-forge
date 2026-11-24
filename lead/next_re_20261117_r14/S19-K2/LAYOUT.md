# S19-K2 · LAYOUT.md — 类布局与 GetSize（§981 槽契约）

> 目标 SHA-256 `73201CC0…F67476` 亲测一致。方法：§8.2 技术②（双点闭合，**不假定槽 12**）、§981 槽契约、§8.1 ⑧ RTTI 链 `COL+0xC→TD+8`（读不到 fail-closed）。
> 复算脚本：`work/baseline_check.py`、`work/wave_rtti2.py`、`work/wave_vt.py`、`work/final_verify.py`、`work/voc_fields.py`、`work/t3_access_forms.py`。

## 1. 已入账前提（只引用不重做，§968）
- **`VocClass` = 0x148 B** `[已证]`：入账硬证（GetSize）。本卡停机核验复算：工厂 `0x4063B0` 内 `push 0x148`@`0x4063F5` → `call 0x7C8E17`(operator new) + `mov ecx,0x52; rep stosd`（0x52×4=0x148）；全 `.text` `B8 48 01 00 00 C3` 仅 2 处（`0x487E70`/`0x74AB10`），后者邻项 `0x74ABxx` 音频族。与入账值一致 ✓。
- 24 字段降 `[静态推断]`；FLOW §3 `+0x9C/+0x11C` 按 §968 更正为 **`+0xB4`(SampleIndices[0x20]) / `+0x134`(NumSamples)**。

## 2. GetSize / 槽契约核验（`B8 imm32 C3` 不特异 ⇒ 叠加槽位锚定）
基线实测（纪律 1/§8.2 技术④）：全 `.text` `B8 imm32`（不要求 C3）= **5,857**；裸 `ret(C3)` = **14,652**。⇒ 纯 `B8 imm32 C3` 形态无鉴别力，必须**双点闭合 + 槽位锚定**。

| 类 | RTTI（COL+0xC→TD+8） | vtable / GetSize 槽 | imm | 分配点 `push size`→new | 分级 |
|---|---|---|---|---|---|
| **VocClass** | 无自身 TD（仅 `.?AV?$VectorClass@PAVVocClass@@@@` 等模板名）⇒ 类名取已入账交叉事实，非本次 RTTI 新发现 | `B8 48 01 00 00 C3` @`0x74AB10`（表项 `0x7F6348`，邻项音频族 `0x74ABxx`），槽号未由 TD 定 | 0x148 | `push 0x148`@0x4063F5 → `0x7C8E17` | `[已证]`（已入账） |
| **WaveClass** | **TD `0x847EB0`**（`.?AVWaveClass@@` 内联于 TD+8=`0x847EB8`）；**主 COL `0x80D418`**（sig=0,off=0,TD=0x847EB0,CHD=0x80D408）；`vtable[-1]`@`0x7F6BF0` → **vtable `0x7F6BF4`** | slot12 = `0x75F880` = `B8 40 02 00 00 C3`; 另 slot35=`0x5F42A0`→`0x7FFFFFFF`、slot36=`0x4263C0`→`.data 0x8182E0` 是 §981 已记录反例 ⇒ **不能假定槽 12，靠双点闭合选中 slot12** | 0x240 (576) | `push 0x240`@`0x6BF0BC`/`0x6FF449`/`0x6FF623` → 全部 `call 0x7C8E17`(operator new) | `[已证]`（RTTI 链 + 3 处双点闭合） |

- `0x4C9150`（`33 C0 C3` 抽象基类共用桩）已按 §981/§8.2 ②排除（不在上述命中）。
- 分配点形态覆盖：`68 imm32`（`push 0x148`/`push 0x240` 均为 68 imm32 型式）已扫；未发现本片类使用 `6A imm8`/`mov [esp],imm`/`sub esp,imm` 承载 size 的情形（0x148/0x240 > 0xFF，`6A` 不可能编码）。
- **其它音频类（Mixer/Stream/Theme/EVA "manager"）**：全镜像 RTTI 仅见 `AVWaveClass@@`（有 TD）、其余音频相关只到模板容器（`AV?$DynamicVectorClass@PAVVoxClass@@@@`、`AV?$VectorClass@PAUThemeControl@@@@`、`AV?$DynamicVectorClass@PAVVocClass@@@@`），**无独立 TypeDescriptor** ⇒ 按纪律 5 fail-closed，**类名不可定，不猜**；GetSize 无可指认 vtable 槽，保持 `sub_`。

## 3. VocClass 字段表（0x148 B；写点+读点双支撑，§6 纪律 4）
> 写点=ctor `0x4063B0`/13 个 INI setter（`0x406540`..`0x406600`，键名逐字符核对，见前序 VERDICT D3）/ `0x4041D0`(reader1)/`0x405190`(VoiceAlloc)/`0x752DB0`(LoadFromINI)；读者域同上。字段语义承袭前序 24 行（已降 `[静态推断]`），本卡按 §968 更正 2 行偏移。W/R 数为 `work/voc_fields.py` 在锚定方法内的实测操作数。

| 偏移 | 宽度 | 类型 | 写者全集（锚定方法内） | 读者≥3 | 语义 | 分级 |
|---|---|---|---|---|---|---|
| +0x00 | 4 | ptr | 0x4043F4 | 24 | 通用链/next | `[静态推断]` |
| +0x0C | 4 | int | 0x406427 | 13 | 索引/计数 | `[静态推断]` |
| +0x10 | 4 | int | 0x40642E,0x406573(Control) | 13 | Control 模式 | `[已证]`(键/偏移双实锤) |
| +0x14 | 4 | int | 0x406435,0x4065C0(Type) | 4 | Type(SCREEN=0x20) | `[已证]` |
| +0x18 | 4 | int | 0x40433A,0x404422 | 11 | 状态字 | `[静态推断]` |
| +0x24 | 4 | ptr | 0x40526D | 8 | 关联对象 | `[静态推断]` |
| +0x28 | 4 | float | 0x752DCC | 3 | 音量基值(1.0f) | `[静态推断]` |
| +0x40 | 4 | int | 0x406443,0x406540(Limit) | 2 | Limit(=2) | `[已证]` |
| +0x44 | 4 | ptr | 0x40423B,0x4042F0 | 1 | 链表/索引 | `[静态推断]` |
| +0x48 | 4 | int | 0x40643C,0x4065D0(Priority) | 1 | Priority(=3) | `[已证]` |
| +0x50 | 4 | int | 0x40644A,0x4065E0(Range) | — | Range(=10) | `[已证]` |
| +0x54 | 4 | float | 0x406451,0x4065F4(MinVolume) | — | MinVolume(0.2f) | `[已证]` |
| +0x58/+0x5C | 4+4 | int | 0x406604/0x406607(Delay 双值) | — | MinDelay/MaxDelay | `[已证]` |
| +0x6C | 32 | char[0x20] | ctor `lea+0x6C`+strncpy | 2 | Name | `[静态推断]` |
| +0x98 | 4 | int | 0x40424B | 1 | 索引字段 | `[静态推断]` |
| **+0xB4** | 4×0x20 | int[] | `(索引式 [reg+eax*4+0xB4] 8 处)` | ≥3 | SampleIndices[0x20]（§968 更正，替 +0x9C） | `[静态推断]` |
| +0xA8 | 4 | ptr | 0x404404,0x405290 | 2 | 缓冲指针 | `[静态推断]` |
| +0xB0 | 4 | int | 0x4044F3,0x404512 | 3 | 计数 | `[静态推断]` |
| **+0x134** | 4 | int | LoadFromINI 区索引写 | ≥1 | NumSamples（§968 更正，替 +0x11C） | `[静态推断]` |
| +0x138 | 4 | int | 0x406589,0x406591 | 1 | Control 关联 | `[静态推断]` |
| +0x13C | 4 | int | 0x4065AA,0x4065B1 | 1 | Control 关联 | `[静态推断]` |

> ⚠️ 字段语义为前序承袭，本卡只核验写点/读者与本类归属；「24 字段」不可独立证成（前序 VERDICT §5），故整体保持 `[静态推断]`，仅 INI setter 命中的 6 行因"键名字符串 + 写偏移 + 构造器默认值"三重字节佐证升 `[已证]`。
> **三种访问形式**：锚定 10 方法内扫得绝对 `[0xADDR]` 16 处、`[reg+disp]` 85 处、立即数加载基址型计入后者；`call [reg+disp]` 在锚定方法内 **0 处（剔除数 0）**，不计入数据字段读点。

## 4. WaveClass 字段（简表，0x240 B，`[静态推断]`）
`[esi+4]`=Bink 句柄（多个 w32 wrapper 读）、`[esi+0x20]`/`[esi+0x24]`=dimensions、`[esi+0x28]`=file handle（close 处写 -1）、`[esi+0x2D]`=wait 标志（`0x433031` 写 1）、`[esi+0x30]`=goto 位置（`0x432BE4` 清 0）。均由 `0x432700`/`0x432750`/`0x432BD0`/`0x433020` 本类方法写+读，双支撑；完整字段表需另卡穷举，本卡只给骨架。
