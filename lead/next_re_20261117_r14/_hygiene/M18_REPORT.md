# M18_REPORT — S10_K16 审计裁决并入
1. 快照：先存 `_hygiene/M18_before/`，52 个 COVERAGE 文件 SHA-256 清单见 `_hygiene/M18_before/SHA256SUMS.txt`；关键 before：coverage F5F985051EE76D7732162A788E69D0FAE80E1105492E552A6710328CEF08BB61、PANEL 07A83823566829B1FBAB1EA9C108B56CE5D4BC3E9C2336A096A47503ADB82B38、CONFLICTS 31A8915886E8A1089552C95F3A3AB85949A882D6EB140DF93F6F5DBDF9497E05、PENDING 32CB7369E8DE4D587E8D1EE581DD2B7ACBABC14512544C036FC56074C56F6C10。
2. 事1完成：仅 `0070B570` 由 `[静态推断] AircraftClass::slot263` 升 `[已证] TechnoClass::ClampAndAdvancePairedFloatState_behavior`；six-class 同槽无派生覆盖，按审计归属 TechnoClass 级。
3. 升级依据（审计 VERDICT 逐行裁定2原文）：环① `type+0xD6A ← "BalloonHover"`（0x714DA9，body 0x70B677 读）、`rules+0x18B8 ← "FallBackCoefficient"`（0x66B8D5，body 8 处 fld）；审计裁决「应升 1 行：0070B570 → [已证]」。
4. 0070B570 语义：用 K16 配对浮点钳制/推进表述，补上述两键锚和 `[this+0x3CD]` / `[this+0x425]` 两门；删除错误「双门控」说法——唯一 vcall `[v+0x41C]`@006FA236 仅由 `[v+0x298]` 门控，`[this+0x90]` 测试在 0x6FA23C、发生在 vcall 之后。
5. 事2完成：`00701410`、`006F4EB0` 均保持 `[静态推断]`，未升 grade；按审计文字更正各自 one_line_semantics。
6. 00701410 维持理由：head claim `+0x6C/+0x70 ← type+0xA0` 无类型 INI 键锚；body 实为 Building-only（`cmp eax,6`），补 `ConditionYellow`/`BuildingRepairedSound` 并收回 type-sound 断言；环③ caller `00519630` 仍是占位名 `[静态推断]` slot99 实现。
7. 006F4EB0 维持理由：`+0x220` 只有裸立即数 1/2/3、无枚举符号，`0xA83D4C` 无名锚且无 INI 键；语义修正 `call [reg+0x420]` 站点 9→10，补漏 `0x454D95`。
8. 同 grade 名异：K16 对上述两行的 TechnoClass 行为名与盘面 `AircraftClass::slot259/264` 不同，按规则保留旧名、`conflict=1`、CONFLICTS +2，不裁决；提级行跨 grade 不触发同 grade 冲突。
9. named 口径修正：审计指出 513→516 不自洽；named 规则为 `526 − 13 个 sub_`，416 个 `Class::slotN` 占位名本来已计 named，3 行改名不增加 named。现场复算 S10 named_L/S(R14) 仍 513/526=97.5285%，PANEL 未沿用 516。
10. 复算：coverage 数据行 before/after 18,431/18,431，entry 新增/删除 0；第 5 列 before `[未证]` 11,031 / `[静态推断]` 6,029 / `[已证]` 1,371；after `[未证]` 11,031 / `[静态推断]` 6,028 / `[已证]` 1,372（+1）。
11. S10：atlas_n 526，proved 116→117（117/526=22.2433%）；named_L/S(R14) 513→513，strict 81→82；门槛 263 差 146。atlas 内全表 proved 1,366→1,367。
12. PANEL：更新当前值、TOTAL、S10 行并新增 M18 段；保留 named_pct_S 双列、S13 240/148 双分母、S22 不参与排名、三分母 12,916/14,487/18,431。
13. 登记：CONFLICTS 465→467（+2）；PENDING 265→268（+3：提级 1 + 语义更正 2）。
14. after SHA-256：coverage 607FAE0FC061168A8E05B79F9B475E3CA0739BC14871CBE4AA069D1AD7BA8810；PANEL FC56B715B867EF4CF9F44E7E1124413F57E96B5F36B96F4FD73E48E699374070；CONFLICTS 04B3B00770F86AD54C3858E8C62BD8225414D3DE61C963EB8F7C95FEB3EF8298；PENDING 1DAEBB038683D69EB480138647C362D5CF7BEC826357A43375F561E41F41732B。
