# S06-K2 DISAGREE（与已入账节号/前序卡的冲突）

## D1 · GetSize 基线计数：666（本卡）vs ~837（§969）—— 口径差异，非结论冲突
- **§969 / R14_COMMON §8.2**：全镜像 `B8 imm32 C3` 候选 ~837，其中 543 落在非槽 12。
- **本卡实测**（`work/t2_getsize.py`，`EVIDENCE/t2_getsize.txt`）：`.text` VA 解码 666 个 `B8 imm C3`；全文件 raw 字节 668 个；非任何 RTTI vtable slot12 的有 597 个；若把 `C2(ret imm16)` 也算入则 `B8 imm (C3|C2)`=873（接近 837）。
- **裁定**：§969 的 837/543 与其具体扫描口径绑定（可能含 C2 或不同节范围）；本卡无法在相同口径下复现其精确值，但两者都证明「B8/C3 判据不特异、必须叠加 vtable slot12」。**结论无分歧**，仅记数口径差，供审计核对。GetSize=0x148 双向闭合在两口径下均成立。

## D2 · 与 S12-K2（审计中，未采信）：无 DISAGREE，独立验证一致
- S12-K2 声称①：`0x47C620` 只扫 head A(`+0xE4`)。本卡独立扫 `0x47C620`：`0x47C657/683/712/79E/7D9` 均为 `[edi+0xE4]`，函数内无 `[edi+0xE8]` ⇒ **一致**。
- S12-K2 声称②：`0x47E8A0` 按对象 `[+0x8C]` byte 选头。本卡独立复核：`linkadd` arg2 选头（[esp+8]=0→+E4，≠0→+E8），wrapper `0x5684B1 mov dl,[edi+0x8C]` 传入 ⇒ **一致**。
- 本卡**未引用 S12-K2 结论当前提**，上述均为独立字节复核。无冲突。

## D3 · 与 §958 / §961 / S06-K1 audit：无 DISAGREE（全部确认）
- CellClass 字段 **63**（§958）：本卡扫得 63 ✅。
- MapClass vtable **30 槽**（§958 推翻 C06 的 179）：本卡确认 30 槽 + 终止符 0x7ED47C ✅；未重开 179 之争。
- `0x87F924` 是**指针字段地址**（=MapClass+0x13C），数组基址=`dword[0x87F924]`（§961）：本卡确认 399 绝对读、0 绝对写、stride=4 ✅。
- `0x4C9150` 是抽象基类共用桩（S05-K1）：本卡确认其字节 `33 C0 C3`，MapClass v[18..21] 指向它、非 GetSize ✅。

## D4 · 与 S06-K1 执行员（已被 audit PARTIAL 更正）：本卡采信 audit 更正值
- K1 报 61 字段 → audit 更正 63：本卡采 63（T1）。
- K1 报 MapClass 179 槽 → audit 更正 30：本卡采 30（T3）。
- K1 报 `+0x30`=next（当 CellClass 字段）：本卡澄清 next 是 **ObjectClass+0x30**，CellClass+0x30 无本类读点（U1），与 audit 一致。

> 本卡未写台账、未改 `COVERAGE\coverage.tsv`、未改游戏文件、未 git commit、未跑真机。
