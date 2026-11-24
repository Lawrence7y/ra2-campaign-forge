# S03-K2 · DISAGREE.md

## D1 — 派卡基线 proved 数不符（纪律 9，停机项）
- **派卡 §2**：S03 `[已证]` 仅 **11（5.67%）**。
- **盘上现值**：`COVERAGE\PANEL.md:35` S03 proved_n=**18**、proved_pct=**9.28%**；本卡 `TARGETS.tsv` 独立实算（coverage∩atlas 统一大小写）= **18/194 = 9.28%**。
- 11/194=5.67% 亦自洽，二者只差截面 ⇒ 派卡数字是**旧截面**（M3/M4 并表前）。**拒绝凑到 11**；一切统计以盘上 18 为准。未改 PANEL/coverage。

## D2 — K1「hash = 标准 CRC32」表述（继承其审计结论）
- K1 PROGRESS #5 写「CRC32：`zlib.crc32(name.upper())` 等价」。
- K1 审计 VERDICT §2 + 本卡独立 8/8 反证：应为**反射 CRC32 内核 + `len%4` 尾部填充**（`buf[r]=r`、其后填 `buf[0]=末字节`），zlib 0/8。
- 本卡 `MIX.md §2` 已按修正结论写；不改它卡文件。

## D3 — 忽略 atlas 小写坑则交集极小（§990 坑）
- 若不做大小写归一，S03 coverage(大写) ∩ atlas(小写) 会误得远小于 194；本卡 `t1_targets.py` 全量 `norm(e)=.upper()`，得 194 与 PANEL 一致。

## D4 — GetSize 惯例不适用本族（继承 §981）
- 派卡 T3 提示按 §981 槽契约；本卡实测五类 vtable **全无 `B8 imm32 C3` GetSize 槽**（CC/CD/BufferIO/RawFile v[12] 均为普通函数，MixFile 仅 1 槽）。
- 改用分配点 `push size; call 0x7C8E17` ↔ 字段 max 两处对账；闭合仅 CCFile 0x6C / MixFile 0x28 = **2/5**。不假定槽 12、不套 AbstractClass 惯例。
