# S03-K1 · DISAGREE（冲突与更正）

| # | 对象 | 冲突点 | 本卡处置 | 依据 |
|---|---|---|---|---|
| D1 | 派卡任务第 4 项「两类的 GetSize（`v[12]` 的 `B8 <imm32> C3`）」 | 该模板措辞针对 AbstractClass 派生类（如 S16-K1 SuperClass v[12]=0x6CE210）。但 CCFileClass/MixFileClass **非 AbstractClass 派生**：CCFileClass v[12]=`0x473AE0` 字节 `56 8b f1 8b 46 58…`（带 2 参的 Read 族方法 `ret 8`，见 E02/E08），MixFileClass vft 仅 1 槽，**均无** `B8 imm C3` GetSize。 | 不编造 GetSize 值；按 K 类等价核对改用 **new(size) 分配点 ↔ 字段 max(disp+width)** 两处独立对账：CC=0x6C、Mix=0x28，均吻合。已在 PROGRESS/LAYOUT 标注为「事实修正」。请审计按等价口径裁决。 | E02_vtables_getsize.txt / E05 / E08 |
| D2 | 台账 §27610「`0x65CA80` CCFileClass（按文件名推断，实为 RawFileClass）」 | 派卡背景提示曾有类名误挂；线索文档 `fs_mix_load_chain*.md` 把 `0x65CA80` 称 RawFileClass ctor、CCFileClass ctor 为 `0x4739F0`。 | 本卡类名只认 RTTI TypeDescriptor：CCFileClass TD=`0x815E58`/vft=`0x7E16B0`/ctor=`0x4739F0`（E01）。`0x65CA80` 未进入本卡任何结论。与台账 §27610 更正一致，无新冲突。 | E01_rtti.txt；R14_COMMON 纪律 17 |
| D3 | 线索文档 `fs_mix_load_chain.md` §1.2 称 CCFileClass vft `+0x14=Open 0x473C50`、`+0x1C=Get_File 0x473D10` | 本卡实测 vft slot 5=`0x473C50`、slot 7=`0x473D10`（即 `+0x14`/`+0x1C`），**一致**。线索文档只是线索，本卡已用 RTTI+capstone+Ghidra 重新取证，结论相同。 | 无冲突，线索被本卡独立证据升级为 [已证]。 | E01 / E02 / E03 |
| D4 | 线索文档 MIX 索引项「12B {id,offset,size}」 | 本卡独立复核确认 12B（ctor `numFiles*12` + Find 12B 步长）。 | 无冲突，双通道印证。 | E04 / E08 |
| D5 | 派卡「哈希 CRC32 变体」 | 实测是**标准反射 CRC-32/ISO-HDLC**（poly 0xEDB88320、init/final 0xFFFFFFFF），非自定义初始值的"变体"。 | 按实测记录；"变体"措辞不适用于本镜像。 | E05 / E08 |

> 未改任何台账、共享表、游戏文件；coverage_delta.tsv 单独交付，未改 `COVERAGE\coverage.tsv`。
