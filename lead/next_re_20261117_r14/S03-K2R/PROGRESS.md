# S03-K2R · PROGRESS（S03-K2 重做，审计裁决 FAIL 修复）

## 上轮 FAIL 修复清单

1. **#6 假否定已修**：上轮写「3 个内嵌基类无独立堆分配」，审计指出 RawFile ctor `0x65CA80` 在 `0x407BB1`/`0x6BC099` 各有 `push 0x24; call 0x7C8E17; call 0x65CA80`。本卡全镜像三形式扫（push imm8/imm32、mov reg,imm、经 thunk/operator new），按「独立分配点 / 无分配点 / 未找到」三态报：RawFile=独立分配点(2)，CCFile=独立分配点(2)，MixFile=独立分配点；BufferIO/CDFile=**未找到**独立分配点（不写「不存在」）。证据 `EVIDENCE/E_S03K2R_alloc_tri_state.txt`、`EVIDENCE/E_S03K2R_alloc_chain.txt`。
2. **#7 窗口截断/访问形式漏扫已修**：上轮 `+0x29` 报 7W/3R；本卡以 RTTI/vtable 自有方法集为界、full-image capstone(skipdata=True) 逐指令边界扫描，三形式（A=绝对、B=寄存器基址、C=全局→指针数组→对象）全扫，重算 `+0x29`=**15W/9R**，`+0x30`=3W/7R，`+0x34`=3W/7R，Raw `+0x14`=4W/10R、`+0x18`=4W/16R、`+0x20`=4W/3R、BufferIO `+0x24`=3W/2R；与上轮审计逐项一致。证据 `EVIDENCE/E_S03K2R_fields_v4.txt`。
3. **绝对寻址漏报分解已补**：7 个字段 A 绝对形式全部 **0W/0R**；B/this 形式承载全部真访问，`+0x29` 漏 15W/9R；7 字段合计漏 36W/54R（不含 RawFile +0x24 的 0W/0R）。证据同上「ABSOLUTE-ONLY MISSES」节。
4. **已复现项保持不动**：hash 8/8（zlib 0/8）、S03∩atlas 194、named 125、proved 18、delta +4 —— **与上轮一致**。证据 `EVIDENCE/E_T2_hash_mix.txt`、`coverage_delta.tsv`。

## 结论表

| # | 结论 | 级 | 证据路径 |
|---|---|---|---|
| 1 | MIX 头：旧式 6B、新式 10B；索引 12B/item；flag bit0=SHA1、bit1=加密 | [已证]（与上轮一致） | `EVIDENCE/E_T2_findorder_header.txt` |
| 2 | hash 算法 = 反射 CRC32 + len%4 尾填充；langmd 8/8、zlib 0/8 | [已证]（与上轮一致） | `EVIDENCE/E_T2_hash_mix.txt` |
| 3 | 查找链：磁盘优先于 MIX；MIX 链表 FIFO 先注册先查 | [已证]（与上轮一致） | `EVIDENCE/E_T2_lookup_chain.txt` |
| 4 | RTTI/vtable 定界：BufIO `0x7E3A2C`、Raw `0x7F0904`、CD `0x7E1668`、CC `0x7E16B0`、Mix `0x7EDF50` | [已证]（与上轮一致） | `EVIDENCE/E_T3_rtti_discovery.txt`/`E_T3_vtables.txt` |
| 5 | BufferIO/RawFile 7字段重算：`+0x29` 15W/9R 等全部复现审计值 | [已证] | `EVIDENCE/E_S03K2R_fields_v4.txt` |
| 6 | 三形式对照：A=0/0，B/C 承载全部；绝对-only 漏 36W/54R；虚槽 `call [reg+disp]` 剔除 15 处 | [已证] | `EVIDENCE/E_S03K2R_fields_v4.txt` |
| 7 | 分配三态：RawFile=独立分配点(2×0x24)，CCFile=2×0x6C，MixFile=独立分配点；BufferIO/CDFile=**未找到**独立分配点；无「无分配点」正证项 | [已证](site) / [静态推断](未找到三态) | `EVIDENCE/E_S03K2R_alloc_tri_state.txt`/`E_S03K2R_alloc_chain.txt` |
| 8 | Raw ctor max 字段偏移 0x20+1 ⇒ align4=0x24，与两个独立 `push 0x24` 闭合 | [已证]（与上轮一致） | `EVIDENCE/E_S03K2R_alloc_tri_state.txt` |
| 9 | 压缩/加密存在性：LZO/PKStraw/RSA e=0x10001/blowfish.dll | [静态推断]（与上轮一致） | `EVIDENCE/E_T4_crypto.txt` |
| 10 | S03 基线：194 / named 125 / proved 18 / delta +4 | [已证]（与上轮一致） | `work/t1_targets.py`、`coverage_delta.tsv` |

## 核心数字（复算脚本）

- `15W/9R` = BufferIO +0x29 全三形式 W/R；绝对-only `0W/0R`，漏 `15W/9R`。复算 `python work/recheck_fields_v4.py`（证据 `EVIDENCE/E_S03K2R_fields_v4.txt`）。
- `3/5` 对齐口径闭合：RawFile 0x24（2点）+ CCFile 0x6C + MixFile 0x28；BufferIO/CDFile **未找到**独立分配点（三态中无「已证无分配点」项）。复算 `python work/recheck_alloc.py` + `python work/recheck_alloc_chain.py`。
- `8/8` hash、`194/125/18/+4` 基线：与上轮一致；复算 `python work/t2_hash_verify.py`、`python work/t1_targets.py`。
