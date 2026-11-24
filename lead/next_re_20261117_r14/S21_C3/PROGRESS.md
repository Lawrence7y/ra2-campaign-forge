补齐 5 行 ③
# S21-C3 PROGRESS

- 卡号：S21-C3；目标：ra2youli\gamemd.exe 只读；写域仅限 S21_C3 与 _ghidra\S21-C3。
- 开工骨架已落地；必读：R14_COMMON §8 ⑲⑳㉑㉒/§8.4/§8.5、lead\PENDING_DECISIONS.md D-40、本卡 CARD.md。
- 补齐③行数：5/5；交付 coverage_delta.tsv（8 列，name 逐字不动，只改 semantics + grade）。
- grade：00599650 [静态推断]→[已证]；其余 4 行 [未证]→[已证]。

## 逐行③（指令偏移）
- 00539760：+0x00 读/写灯位全局，+0x70/+0xA2/+0xD4 delete 旧缓冲，+0xE7 同步 Scenario 字段，+0x127 E8 0053AD00 RecalcLighting；void/无显式入参。
- 0053AB50：+0x00 E8 0053C280 UpdateLighting，+0x05 读 [0xA83D4C]，+0x0A 写 PlayerHouse+0x5779=1；void。
- 0053AF40：+0x10 跳表分派 [0xA9FAC0]，+0x3B/+0x95/+0xC6 虚调用取格值，+0x7A Fire，+0xF7 UpdateLighting，+0xFF 归零判定；void。
- 00595740：+0x05 调基类 0x595680，+0x2E~+0x114 构造成员并装 0x7E4DD8/0x7ED90C，+0x11F~+0x188 写默认值，+0x18E 返回 this；thiscall。
- 00599650：+0x15~+0xD2 算尺寸，+0x156~+0x20E 写 Map INI，+0x45A/+0x491 waypoint 与 cell 标志，+0x825~+0x8B7 全图迭代/寻路，+0xEC0 雷达，+0x1019 ret 4。

## 自证与边界
- ⑨ 盘上复算：5/5 entry 的 S21、grade、name 与 CARD 表一致；name 保持 sub_/PsyDom::Update 原值。
- ⑲ capstone 5.0.7：无 op.index；mem.index 无 index 返回 0（int），自检 14054 个 mem 操作数中 None=0。
- 扫描覆盖 .text VirtualSize 100%：1,392,592 指令 / 68,253 E8@边界 / 81,715 原始 E8；SHA-256 73201cc0...f67476。
- ④ 全部为 E8 指令边界直调，site+5+rel32==entry，非自环；见 EVIDENCE/direct_sites_verified.json。
- ② 沿用审计白名单与具名锚点；0053AF40 另有 YRpp SuperClass.h:190-191 CALL(0x53AF40)；未用 docs/台账作名字异源通道。
- ⑱ 全库按 8 位地址扫描只报不改名：924 处命中（详见 EVIDENCE/conflict18.txt），name 未改。
- 随机基线：S21 同子系统随机取同样多行口径 46/129=35.66%（raw 132 口径 34.85%）；direct call 未用于升格。
- 未使用 atexit 析构器表、槽号匹配、slot-baseline、「P=R=100%」或随机 VA 地址算术自证。

## 交付
- coverage_delta.tsv / UNKNOWNS.md / DISAGREE.md / EVIDENCE/ / work/ 均已落在本卡写域。
