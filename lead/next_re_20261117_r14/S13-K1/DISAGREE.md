# S13-K1 DISAGREE

本卡结论与既有资料的分歧，逐条引用节号并给出本卡取证依据。

| # | 既有说法 | 来源节号 | 本卡结论 | 本卡依据 | 裁定 |
|---|---|---|---|---|---|
| D1 | `re_atlas/kb/30` §19.10 A-40 列 WeaponTypeClass/WarheadTypeClass/BulletTypeClass 为「尚未接入本工具」、613(更正 644) 键不含这三类 | `re_atlas/kb/30` §19.2/§19.10 A-40 | 三类各有完整 loader 字段表：Weapon 56 INI 键、Warhead 53、BulletType 41（本卡新解出，合计 150 键） | `EVIDENCE/ini_fields.tsv`（逐键 store_site），loader 入口 slot25 实测 | 非矛盾：kb/30 的 613/644 是「已接入工具」的口径；本卡把 A-40 的三类补解 |
| D2 | R14_COMMON §1 作废索引警示 `vtables_v2.json` 槽数错（14,044 vs 13,351） | `R14_COMMON.md` §1 (a)、纪律 (a) | 本卡**不读** `vtables_v2.json`，从 .rdata 连续指针定界得 27/27/40/125 | `EVIDENCE/rtti_extract.txt`（VT 地址 + measured_slots） | 遵循纪律，无冲突 |
| D3 | 早期线索（kb/30 §19）把 loader 里 `verses` 键的写点落在 `+0x149`(byte) | `re_atlas/kb/30` §19（TypeClass 键→偏移工具口径；A-40 未覆盖，但工具形状会如此标） | `+0x149` 是派生标志（0x75DE80 比较 +0xC0/+0xD0 得）；真正 `Verses` 落点是 `double[11]@+0xA0`（`fstp qword [ebx]` 循环） | `EVIDENCE/inspect_special.txt` 逐条 0x75DDCC–0x75DEA6 | 本卡更正：以循环写点为准（纪律 #13 逐字符核对写值） |
| D4 | `class_contract.json`（线索）给 BulletTypeClass size 760、Warhead 464、Weapon 352、Bullet 352 | `re_atlas/evidence/class_contract.json`（线索源） | 完全一致（0x2F8/0x1D0/0x160/0x160） | slot12 立即数 + 解析器 `push 0x1d0`/`0x2f8` 分配 | 双通道印证，无冲突 |

未发现与 `docs/re/*.md`、`weapons_damage_*.md` 的**已证**结论冲突；这些旧文档一律只当线索，本卡所有结论均从二进制重新取证。
