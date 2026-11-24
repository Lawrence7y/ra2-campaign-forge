# S07-K2 PROGRESS — 渲染 §4 六条结论地址级双支撑（卡号 S07-K2）

目标 `gamemd.exe` SHA-256 `73201CC0…F67476`（开工/收工均只读）；写域仅本卡目录 + `_ghidra\S07-K2\`。
工具 Python 3.12.10 + capstone 5.0.7(skipdata) + pefile 2024.8.26；脚本在 `work/`，原始输出在 `EVIDENCE/`。

## 结论表（T2 六条逐地址双支撑）
| # | §4 结论 | 双支撑证据 | 判定 |
|---|---|---|---|
| 1 | `0x8A0360`=`[5]LayerClass`(0x18/Count+0x10/Growth+0x14=10) | ctor `0x4A8630`(mov edx,5 + add eax,0x18 循环 + 三层vftable链 + `[eax+0xC],0xA`); 界 `cmp esi,0x8A03D8`@`0x4A8918`; 读点 `0x6D9800`/`0x6D996C`/`0x6D9A58` | **升 [已证]** |
| 2 | `0x8A0390`/`0x8A0364` 同一数组元素2/0 | `lea edx,[edi+edi*2];lea ecx,[edx*8+0x8A0360]`(SetLayer `0x4A974A/52`, idx*0x18); 排序调用 `0x55DBC3 mov ecx,0x8A0390`; ctor stride 一致 | **升 [已证]** |
| 3 | `ObjectClass+0x94`=层索引 | 写 `0x4A9762`(idx)/`0x4A97D2`(-1)/`0x636BB3`(-1); 读 `0x4A972A`/`0x4A977E`/`0x402268`。写点全集 **49 对象字段/112 栈**, 值 **−1:3 / imm0:2 / 寄存器:44**（与台账 §939 逐字一致） | **升 [已证]** |
| 4 | `[+0x80]`=精灵级脏标记 | 置1有比较 `cmp al,cl/je 0x438E43`→`0x438E3C mov byte[eax+0x80],1`; 消费清0 `0x43CEFD`/`0x6D98EF`/`0x6D9A27`/`0x6D9B1A`; 读门控 `0x43CEC3`/`0x6D9A88`。写点本卡实测 181/81 函数（见 D2） | **机制 [已证]，站点计数待统一** |
| 5 | 三遍历器皆 `call[+0x104]`→清`[+0x80]` | `0x6D97D0`✓(`0x6D98E9`/`EF`)、`0x6D9920`✓(`0x6D9A21`/`27`)；**`0x6D9A50` 否**：读`[esi+0x80]`门控 + `call 0x6D2790`(直接) + 清0(`0x6D9B1A`) | **原表述证伪并更正（DISAGREE D1）** |
| 6 | 六道过滤判据+失败跳转 | ①`test 0x482879,j e→0x482956` ②`0x482887,je→0x482956` ③`and 0x482897,je→0x482956` ④`cmp 0x482943,jge→0x482956` ⑤`test 0x43CEC9,je→0x43D017` ⑥4比较 `0x43CF4F/5C/69/76→0x43D017` | **升 [已证]** |

**小结：六条中 4 条升 [已证]（1/2/3/6），1 条机制已证但计数口径待统一（4），1 条原表述被字节证伪并更正（5）。**
T3/T4：LayerClass/Blitter/RLEBlitter/Surface 族 RTTI(COL+0xC→TD+8)/COL/TD/槽数(从`.rdata`自数)见 `LAYOUT.md`；`B8 imm32 C3` 基线 666 复现，**Blitter/Surface 族槽内 0 命中**（GetSize 双证不适用，非证据不足）。

## 给审计员的核心数字（现场可复算）
1. **S07 ∩ atlas = 804 / named(S)=587(73.01%) / proved=68(8.46%)**，Class::sub_=0。复算：`python work/t1_stats.py`（读盘上 coverage.tsv ∩ function_atlas.tsv）。卡面 807/589/65 为 M4 前旧值，按纪律9用盘上现值（DISAGREE D5）。
2. **`+0x94` 写点 49/112、值 −1:3/imm0:2/寄存器:44**。复算：`python work/sweep_all.py` → `sweep_0x94_access.tsv` 取 `is_write=1` 且基址寄存器≠esp 得 49。两种访问形式都扫（绝对 + `mov reg,imm`后`[reg+off]`），否则会得到"0 写"假象（纪律19）。
3. **基线 `B8 imm32 C3`=666**（R14 基线 666 精确一致），`B8 imm32`裸字节=10578（≠R14 的 837，口径不同，DISAGREE D3）。复算：`work/t3t4.py` 末段。

## 缺口（本卡未做完，已立方法/证据）
- 距 50% proved：804 分母需 +334（→402），量极大，本卡只立方法不凑数。
- 区域级脏区仍 `[未证]`（UNKNOWNS U1，不下"不存在"结论）。
- `+0x80` 写点 181/81 vs R14 179/83、`B8 imm32` 837 vs 10578 两处口径待审计统一（D2/D3）。
- `0x4A8630`(层数组ctor)/`0x551A30`(层排序) 字节已证，前者属 initterm 整类桶按政策未提交，后者已入 delta；重分类须 M/Lead 裁决（D4）。

## 交付
`PROGRESS.md`(本文件) · `TARGETS.tsv`(804行) · `LAYOUT.md` · `UNKNOWNS.md` · `DISAGREE.md` · `coverage_delta.tsv`(2行) · `EVIDENCE/`(12反汇编+4 sweep+3 分析) · `work/`(7脚本)。
未改 `COVERAGE\coverage.tsv`；未碰游戏文件；未 git commit。
