# S13-K9 DISAGREE

## 与 a-S13-K6 审计
- **一致**：11 行 exact 判定全部成立（0040B880/0040B930/0040F7C0/0040FD90/0040FE40/0046B7E0/0046B890/0062B250/0062B300/0065C0D0/0065C180），逐行 11/11 一致。它对 vptr 写入示例 `mov [0x89C668],0x7E17CC @0x43856D` 字节级复算无误。
- **补充/更正**：审计 §3 说 "RTTI 45/45 通过" 用的 vt-4 链——本卡用正确 vtable 基址（0x7E17CC 而非槽地址 0x7E17D4）复算，类名全读出（DynamicVectorClass<T*>），结论方向一致，但注意「槽地址当 vt 基」会得假阴性（本卡早期踩过，已纠正并记录在 work/rtti_vtbase.py 注）。审计 §1 说 "F2 行 0x40F7C0 在 0x7E1E90 仅一处引用" 与本卡 vtmap 一致（0x7E1E84+8=0x7E1E8C 是唯一 .rdata 槽），不冲突。
- **3 漏扫行**：审计 §2 指出 0048AD60(slot6)/0054E8E0(slot6)/0048AD70(slot1) 漏扫，本卡确认这 3 行 ③ exact 为 0（不给 [已证]），与审计「应补进候选池但未交 exact 证据」的立场一致。

## 与 S13_K7
- ** disagree（核心）**：S13_K7 `core_numbers.json` 的 `exact11_entries_with_hit=0` / `exact_call_sites_total=0` **错误**。本卡双通道实测 18 call 站点 / 11 入口命中。根因是其脚本只认 `mov ecx,[global]`(8B0D) 而实际 exact 形态是 `mov ecx,<global addr>`(B9 imm)；且 vptr 载入 `mov edx,[G]` 常在 mov ecx 之前（例 0x43863B 早于 0x438645）。其空表 `exact_callsites.tsv` 只有表头属脚本假阴性，不是事实。
- **一致**：K7 的 `slots56=56`/`slots56_S13=52`/`slots56_S22=4` 与本卡 vtable 族计数方向一致（本卡未重数分母）。

## 与其他卡
- 未改 S13_K8 的 164 行、未碰 S13_K2/K5 已并 14 行、未改分母（D-37 未裁）、未写 COVERAGE/台账、未 git commit。