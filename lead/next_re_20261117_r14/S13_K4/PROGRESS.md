# S13-K4 PROGRESS（≤60 行）

目标只读 `ra2youli\gamemd.exe`（SHA-256 73201CC0…F67476 已核）· capstone 5.0.7 skipdata=True · pefile · 纯静态。
开工现读盘自算（coverage.tsv ∩ function_atlas.tsv，统一大小写）：S13=240，grade [已证]=47/[静态推断]=160/[未证]=33，named_L=named_S=212。
卡面 55 = 47（coverage 内）+ 8（S13-K2 未并入 delta）；实测这 8 行在 coverage.tsv 仍 [未证] ⇒ 未并入。本卡不重取 K2 的 8 行（无双算）。

## 结论表（分级 + 证据路径）
| # | entry | 结论 | 证明类型 | 分级 | 证据路径 |
|---|---|---|---|---|---|
| 1 | 004393D0 | BombClass::GetSize 返回 0x5c；B8 5c000000 C3 @vtable slot12；factory push0x5c@0x438EAD→new0x7C8E17→mov[esi],0x7e3d10(Bomb VT) 双点闭合 | GetSize | 已证 | EVIDENCE/b8_verify.txt, getsize_ctor.txt |
| 2 | 004393E0 | BombClass::WhatAmI 返回 0x44=AbstractType::Bomb(68)；B8 44000000 C3 @slot11，RTTI .?AVBombClass@@ | WhatAmI | 已证 | EVIDENCE/b8_verify.txt |
| 3 | 0062AF50 | ParasiteClass::GetSize 返回 0x58；B8 58000000 C3 @slot12；push0x58@0x6C103C→new→ctor0x629210(mov[esi],0x7ef890) 双点闭合 | GetSize | 已证 | EVIDENCE/b8_verify.txt, getsize_ctor.txt |
| 4 | 0062AF60 | ParasiteClass::WhatAmI 返回 0x43=Parasite(67)；B8 43000000 C3 @slot11，RTTI .?AVParasiteClass@@ | WhatAmI | 已证 | EVIDENCE/b8_verify.txt |
| 5 | 0065B3A0 | RadSiteClass::GetSize 返回 0x74；B8 74000000 C3 @slot12；push0x74@0x4691B3→new→ctor0x65B1E0(mov[esi],0x7f0810) 双点闭合 | GetSize | 已证 | EVIDENCE/b8_verify.txt, getsize_ctor.txt |
| 6 | 0065B3C0 | RadSiteClass::WhatAmI 返回 0x45=RadSite(69)；B8 45000000 C3 @slot11，RTTI .?AVRadSiteClass@@ | WhatAmI | 已证 | EVIDENCE/b8_verify.txt |
| 7 | 0046BEE0 | BulletTypeClass::LoadFromINI：41 个弹道 INI 键串 (Arm@0x46BF14…AnimPalette@0x46C3E2)+call 0x528a10 | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 8 | 0046C790 | BulletTypeClass::FindOrMake：'<none>'/'none'+strcmp 0x7c8d20+push0x2f8@0x46C7E6→new0x7C8E17→ctor | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 9 | 0075CEC0 | WarheadTypeClass::Constructor：vptr 0x7f6b30@0x75D0BA + rep movsd(Verses double[11] @+0xA0) | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 10 | 0075D3A0 | WarheadTypeClass::LoadFromINI：53 键(CellSpread@0x75D3E0…Verses@0x75DDDE)+strtok 0x524EC0/0x475D70 | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 11 | 0075E3B0 | WarheadTypeClass::FindOrMake：'<none>'/'none'+strcmp+push0x1d0@0x75E406→new0x7C8E17→ctor | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 12 | 00771C70 | WeaponTypeClass::Constructor：vptr 0x7f73b8@0x771E77 + 3 子虚表 + 字段默认 | 行为级 | 已证 | EVIDENCE/behavioral7.txt |
| 13 | 00772080 | WeaponTypeClass::LoadFromINI：56 键(AmbientDamage@0x7720BB…Warhead@0x772957/Projectile@0x77298A)+resolver 0x75e3b0/0x46c790 | 行为级 | 已证 | EVIDENCE/behavioral7.txt |

分级口径：全部 `[已证]` 均为**结论本身**的字节证据（imm=枚举/尺寸双点闭合；INI 键串/vptr 写/resolver 调用）；**无** `Class::slotN` 占位名升级、**无**仅凭虚表归属升级、一个 name 对一个 entry。

## 核心数字与复算脚本
1. **本卡升级 = 13 行**（6 WhatAmI/GetSize + 7 行为级）。复算：`wc -l coverage_delta.tsv`=13；每行证据实存于 `EVIDENCE/`。
2. **穷举：全部 240 行中 B8 imm32 C3 仅 14 个**（`stub_scan.tsv`），8 归 K2，6 归本卡；无其它常量返回桩形态（`B0/B1/33C0/A1/C3` 全 0）。
3. **非已证候选穷举 = 193 行**（`exhaustive_survey.tsv`）：104 Class::slotN + 40 vslotN + 27 sub_ + 1 other = **172 占位行不可按允许证明类型升语义**；8 归 K2；6+7 本卡；纯 jmp thunk=0。
4. **proved：47(disk) → +8(K2) → +13(本卡) = 68/240 = 28.33%**；DoD 120（50%）尚差 52。按硬规矩如实报，不凑数。

复跑（只读目标）：
```bash
python work/baseline.py            # TARGETS.tsv + 现读盘 47/240
python work/dump_entry_bytes.py    # entry_bytes.tsv
python work/stub_scan.py           # stub_scan.tsv：14 B8 桩穷举
python work/b8_verify.py           # b8_verify.txt：6 新桩 RTTI/槽/枚举
python work/getsize_ctor.py        # getsize_ctor.txt：3 GetSize 工厂→ctor→vptr 双点
python work/behavioral7.py         # behavioral7.txt：7 行为级字节证据
python work/exhaustive_survey.py   # exhaustive_survey.tsv：193 非已证全分类
```

交付：PROGRESS / UNKNOWNS / DISAGREE / coverage_delta.tsv(13 行无表头) / EVIDENCE 目录 / work 目录。未改 coverage.tsv / 游戏文件；未 git commit。
