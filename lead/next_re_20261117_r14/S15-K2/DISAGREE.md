# DISAGREE.md — S15-K2 异议与偏离记录

## D1 · 盘上 coverage S15 = 159 行，与卡面/PANEL 158 不一致 → 按纪律 9 停下核验，非凑数
- 卡面前提："S15 atlas 158 / named 107 / proved 53"（与 `PANEL.md` 一致）。
- 初筛 `coverage.tsv` 得 159 行：多出 `006E6080 name=TagTypeClass::slot25 grade=[静态推断]`，来源是 P0-GATE vt-direct（`evidence_path` 指向 `ENTRY_ADJUDICATION_FULL.tsv#006E6080`），**不在** `function_atlas.tsv`。
- 核验：atlas 内 S15 = 158，L-named=107、S-named=107、proved=53，**逐值复现 PANEL**。无重复 entry。
- 处置：分母采用 atlas 158（R14-R8/R14-R15 DoD 字面口径，与 PANEL 一致）；`006E6080` 不纳入本卡 delta、不擅自改 coverage。已记 `UNKNOWNS.md` U7。**不是卡面错，是口径差（atlas 分母 vs 全表行数）。**

## D2 · S15 无 `Class::sub_XXXXXXXX` 占位 ⇒ L 口径 = S 口径
- R14-R14 裁定：DoD named 判 S 口径（排除 `Class::sub_`）。实测 S15 的 51 条未具名行全是纯 `sub_XXXXXXXX`（两种口径都排除），没有任何 `Class::sub_` 行。
- 处置：S15 的 L-named% 与 S-named% 数值恒相同（107→137）。不因"D1 口径差"人为制造差异。

## D3 · `B8 imm32 C3` 候选数 837 vs 666 口径（引用 STATUS_BOARD R14 裁定，不重测）
- 本卡的 12 条 `B8 imm32 C3`（6 GetSize + 6 WhatAmI）**不依赖**全镜像 837/666 计数；靠"值确在本类 vtable 槽 11/12 位"（`.rdata` COL 定界实测）+ RTTI 类名 + YRpp 枚举三证。符合 STATUS_BOARD "必须叠加槽位锚定"要求。
- `slot12` imm 与构造器 `push <size>` 双点闭合 6/6，排除小立即数 `6A imm8` 陷阱（本类 size 均 >0x7F，为 `68 imm32`，另有 6A 通道已全 `.text` 扫，`T2_alloc_sites.txt` 52 个命中含 6A/68 两形态）。

## D4 · 构造器 5 条含重名（C++ 重载，非冲突）
- `006E4DE0`/`006E4F60` 命名 `TagClass::TagClass`、`00725FA0` 命名 `TriggerClass::TriggerClass`——与 coverage 已有同名条目并存。这是 C++ 构造器重载（同一类名多入口），非 entry 冲突（entry 唯一）。证据为入口写 vtable 链 + 基类 ctor，非推测。若合并员因"名字唯一性"拦截，请按重载保留。

## D5 · 动作实现 25 条的语义名来自 YRpp `TriggerAction` 枚举 + 跳表序
- 派卡提示"用真依据定名，不许编名"。本卡依据链：① 字节跳表 `0x6DFDEC[i]`（145 项、KiB 复核 38/91/92 别名吻合 KB）；② `Execute` 序言 `mov edx,[esi+0x2C]; dec edx; cmp edx,0x90; jmp [edx*4+...]` ⇒ 表索引 i ↔ 动作ID i+1（1-based）；③ handler 是薄壳、唯一 call = 该 `sub_`；④ YRpp `GeneralDefinitions.h` 的 `enum class TriggerAction` 给出 i+1 的名字。三处语义旁证吻合（RetintRed/Green/Blue 写 RGB 全局 0x3534/8/C；PlaySoundEffectAtWaypoint 读 waypoint 坐标；ClearAllSmudges 调 MapClass）。严格判据剔除 5 条非唯一 call 者（见 UNKNOWNS U2），未放宽。
- 若审计认为"YRpp 枚举名 ≠ 字节自证名"，可降级该 25 条为 `[静态推断]` 并保留 entry 名——但 42→17 条 `[已证]`，proved 回落 70/158=44.3%（仍>33.54% 基线），本卡不以该风险换数字。

## D6 · 未创建 KB、未写台账、未改游戏文件、未 git commit
- 严格守写域；派生品全在 `S15-K2\`。

## D7 · capstone `skipdata=True` 与双通道
- 所有字节通道脚本用 `audit_lib.md32(skipdata=True)`；`sweep_calls` 1,394,120 指令/66 skip byte。跳表/vtable/构造器字节读取不依赖 atlas entry+size（atlas 仅用于分母与交叉），满足纪律 1"至少一条不依赖 atlas"。
