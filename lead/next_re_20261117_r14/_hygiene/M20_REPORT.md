# M20_REPORT — S13_N1 PASS 2 行并表
1. 2026-11-18T08:56:33.322+0；快照 `_hygiene/M20_before/` 4 文件已记 SHA-256（`SHA256SUMS.tsv`）：coverage c91e168d…126de7e、PANEL 5bf9c4a8…3b484dc、CONFLICTS a1449969…2ea35b3、PENDING 099030f5…b2145cb。
2. `0065B1E0`：name `sub_0065B1E0`→`RadSiteClass::RadSiteClass`（U3 去 `()`，全表 0/18431 先例）；grade `[已证]` 不变；semantics/evidence 用卡 delta；n_sources 1→2，conflict=0。
3. `00773030`：name `WeaponTypeClass::FindIndex` 不变；grade `[未证]`→`[已证]`；semantics 收紧为只读 Items@0x88756C / Count@0x887578，`0x887568` 仅基址、本函数不读；n_sources 3→2（⑰ A1/A2/A3 同属一环），conflict=0。
4. 行数 18,431→18,431，entry 增删 0；sub_：S13∩atlas 26→24，全表 6,896→6,894。
5. grade before `[未证]` 11,031 / `[静态推断]` 6,028 / `[已证]` 1,372 → after `[未证]` 11,030 / `[静态推断]` 6,028 / `[已证]` **1,373**；atlas 内 `[已证]` 1,367→1,368。审计要求 +2 与快照矛盾：`0065B1E0` before 已 `[已证]`（N_FIX 已提级，仅 name 未更正），故实际只 +1，未改其他行凑数。
6. S13 实测（atlas W130 ∩ coverage 大写 entry）：n=240；named(L/S-R14) 214→216 = **216/240=90.00%**，门槛 216 ⇒ **恰好达标、零余量**；strict 74→76=31.67%；proved 74→75 = **75/240=31.25%**；148 口径 proved 75/148=50.68%。
7. **提示：S13 达到 90.00% 但零余量**；**240 口径达标，148 口径见 D-37 待裁**（D-38 strict 双列保留，不做单方达标宣告）。
8. 冲突/PENDING：CONFLICTS 468→468（+0；占位名转真名不触发同 grade 双真名冲突）；PENDING 270→272（+2：U3 name 去 `()` 1 条；U1/U2 semantics+n_sources 收紧 1 条）。
9. PANEL 保留 named_pct_S(R14/strict) 双列、S13 240/148 双分母、S22 不参与排名；三分母 A/B/C 12,916/14,487/18,431 不变。
10. after SHA-256：coverage 07498bff874f6db7f0d7af592ed7ecf4bcf5b37f19920c6a3fb9b1311cbd3a0c、PANEL d6cce095f6a616ae9548b7902aadd31af30a5dda00a92e25c8f55821f1acbd2f、CONFLICTS a14499692822f7a44b843070fa93a53621fba6d72a075aadc97b2de232ea35b3、PENDING e0d10c7408e7b35acad2955a436f806f3c37c0a802477e2733bc8359ee34bbba。
