# M15_REPORT — S10_K13 单行并表
时点：2026-11-18T06:46:17+08:00；快照 2026-11-18T06:44:23+08:00 已存 `_hygiene/M15_before/` 并记 SHA-256；写域仅 `COVERAGE/` 与 `_hygiene/`。
快照 SHA-256：coverage=CA5CE49316E5CC189393909AED88CED6986F543C3A7C801C13F67BA83E887979；PANEL=A2032B5D9E9ED9DA1B8908E78FF4ED0669AFB12315C313D5FB6AA5D4FE98A2DE；CONFLICTS=31A8915886E8A1089552C95F3A3AB85949A882D6EB140DF93F6F5DBDF9497E05；PENDING=0EB57B50B1683834BCC69009EA4C084637D34583359F162D12B93044E89547D8。
改后 SHA-256：coverage=E5F7BF9726D7BF935EC83D10BB64775C7CC069DC0E8797864B9A3FE1CB5B8B81；PANEL=A8C9D2E438E19CB95C6896AED231C02DFEB8951666F8AF7910D12FB7F718AE6D；CONFLICTS=31A8915886E8A1089552C95F3A3AB85949A882D6EB140DF93F6F5DBDF9497E05；PENDING=9C3BB325B02F4B57B1383557210C08C4FF6B19C08DE77EADA0979A47BECFD911。
并入：仅 1 行 `004D7330`，`[静态推断] FootClass::slot91` → `[已证] FootClass::ApplyDamageAndCacheSubobjectNotification_behavior`；name/semantics/evidence_path/n_sources 按 delta 同步，并按审计修正 args[2]、[esp+0x14] 未初始化局部槽、vtable[0x3C8] 三处文字。
排除：`004D85D0` 不并入、不改 grade/conflict，盘上保持 `[静态推断] AircraftClass::slot99`；`004D85D0` 待 `S10-K14` 返工。
排除证据：0x816CAC 体内 0 引用（仅 `005B3740 GetMissionName` 的 8 字节步长指针表用）；环④ `0065C7E0` 为幽灵被调（0 次调用）；FootClass/AircraftClass 共享 slot 0x18C、Infantry/Unit 覆盖版 `ecx=this` 直调，类归属应为 `FootClass::`。
coverage.tsv：before/after 18,431/18,431 行；entry 新增 0、删除 0；仅 1 数据行变化。
grade 第 5 列 before：`[未证]` 11,031 / `[静态推断]` 6,032 / `[已证]` 1,368。
grade 第 5 列 after ：`[未证]` 11,031 / `[静态推断]` 6,031 / `[已证]` 1,369（`[已证]` +1）。
S10 口径：表内 528、表外 2（0041B860/005B3740）、atlas_n 526；门槛 263，before 差 150、after 差 149。
S10 proved before：113/526=21.4829%；after：**114/526=21.6730%**（113+1）。
S10 named_L：513/526=97.5285%（不变）；named_S(R14)：513/526=97.5285%（不变）。
S10 named_S(strict)：before 77/526=14.6380%；after 78/526=14.8289%（slot91→behavioral 真名）。
atlas 内合计：proved 1,363→1,364；strict named 1,318→1,319；L 7,193 与 S(R14) 7,186 不变。
CONFLICTS 数据行 465→465（新增 0）：本次为 grade 提级，未触发同 grade name/subsystem 冲突。
PENDING_CORRECTIONS 数据行 261→262（新增 1：M15 并入登记；排除行不另登记）。
PANEL 已刷新 S10/TOTAL/当前计数；保留 named_pct_S 双列、S13 240/148 双分母、S22 不参与排名及三分母 12,916/14,487/18,431。
