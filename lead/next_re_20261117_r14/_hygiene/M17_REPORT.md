# M17_REPORT — S10_K15 两行按审计应升裁定并入
1. 快照：先存 `_hygiene/M17_before/`；before SHA-256：coverage 4B2435804E5CDC55E787486B1F7E4E4FC528224145867210DB0615FF45CC2C4F；PANEL A8C9D2E438E19CB95C6896AED231C02DFEB8951666F8AF7910D12FB7F718AE6D；CONFLICTS 31A8915886E8A1089552C95F3A3AB85949A882D6EB140DF93F6F5DBDF9497E05；PENDING EF02D7CAA1071FC051F485946E20152ED38EA0BC9B713E7982BDAD8990D5514A。
2. 并入：仅 S10_K15 两行（物理行 10040/10041）：006FB170、006FB470；均 [静态推断]→[已证]，name 改 TechnoClass::Enable/DisableAreaVisibilityCounterRefresh_behavior；evidence_path/n_sources/conflict 取 delta（PROOF 路径、4、0）。
3. 006FB170 语义前：AircraftClass 虚表槽 261(+0x414)：Mission/单位行为AI 方法（槽语义未证）。后：TechnoClass 基类共享槽 261 的 GapGenerator 帷幕半径逐格计数开启，写明 INI 0x712170→type+0xCD1/CD2/CD3、0044D880 双门控与 +0x26C 播种、[v+0x414]、环④ callee。
4. 006FB470 语义前：AircraftClass 虚表槽 262(+0x418)：Mission/单位行为AI 方法（槽语义未证）。后：TechnoClass 基类共享槽 262 的 GapGenerator 帷幕半径逐格计数关闭，写明同一 INI/门控/播种链、[v+0x418] 与配对 [v+0x414]、环④ callee。
5. 两行语义均采纳审计补出的环①：0x712170 按 0x843E98 GapGenerator / 0x843E84 GapRadiusInCells / 0x843E6C SuperGapRadiusInCells 写 type+0xCD1/CD2/CD3；不再保留卡面「caller+字段」占位表述。
6. 两行语义均补记审计漏报环④：006D20E0 TacticalClass::AdjustForZ [已证]×2；其余已证 callee 保留，未改动 4/5 callee 的冲突标记。
7. 覆盖表：before/after 数据行 18,431/18,431；逐行仅上述 2 行变化；无新增/删除 entry。
8. 第 5 列 grade before：[未证] 11,031 / [静态推断] 6,031 / [已证] 1,369。
9. 第 5 列 grade after ：[未证] 11,031 / [静态推断] 6,029 / [已证] 1,371（[已证] +2）。
10. S10 实测：atlas_n 526（表内 528、表外 2）；proved before 114/526=21.6730%，after 116/526=22.0532%；门槛 263 差 147。
11. S10 named 实测：named_L 513/526=97.5285%，named_S(R14) 513/526=97.53%（现行口径 513→513，不沿用卡面 515）；strict 现场 before 79→after 81（审计基线 78，K15 两行 +2），81/526=15.40%。
12. PANEL：S10 行刷新为 513/513/81/116；TOTAL atlas 内 proved 1,364→1,366、strict 1,319→1,322（含 M16 落盘改名 +1）；保留 named_pct_S 双列、S13 240/148 双分母、S22 不参与排名、三分母 12,916/14,487/18,431。
13. CONFLICTS 新增 0：本次为跨 grade 提级，不触发「同 grade 但 name/subsystem 不一致」规则；数据行仍 465。
14. PENDING 新增 2：M17/006FB170 与 M17/006FB470，分别登记 grade+name+one_line_semantics 更正；数据行 263→265。
15. 为何采纳升级：VERDICT 裁决 PARTIAL，但必审1明确环②/③成立、环①仅因执行员漏证而「应升 [已证]」；审计用 INI 键写点与 0044D880 type 门控/播种链完成字节级闭环，不是虚高。
16. 类归属：审计自写 RTTI 复算六表 slot261/262 均指向两地址、全镜像各恰好 6 处且无 E8 直调，采纳 TechnoClass 基类级命名；不并 S10_K16 三行与 S17_K5 一行（均无审计）。
17. after SHA-256：coverage F5F985051EE76D7732162A788E69D0FAE80E1105492E552A6710328CEF08BB61；PANEL 07A83823566829B1FBAB1EA9C108B56CE5D4BC3E9C2336A096A47503ADB82B38；CONFLICTS 31A8915886E8A1089552C95F3A3AB85949A882D6EB140DF93F6F5DBDF9497E05；PENDING 32CB7369E8DE4D587E8D1EE581DD2B7ACBABC14512544C036FC56074C56F6C10。
