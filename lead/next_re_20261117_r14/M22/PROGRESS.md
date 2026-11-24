# M22 · PROGRESS（合并员幂等复核，COVERAGE 唯一写者，串行）
目标白名单前 8 张：S17-K3 → S13-K2 → S13_K5 → S15-K3 → S18-K2 → S12-Q2 → S01-K2 → S02-K2。
实测结论：8 张卡的 delta 全部已由历史轮次(M7/M10/M18/M20/M21)并入 coverage.tsv，本卡逐行幂等复核，**upgrade 0 行**。
grade 只读第 5 列；entry 比较一律 tolower+去 0x；同 grade 不同名一律保留旧值标 conflict=1，不自行裁决。

## 卡 S17-K3（a-S17-K3 VERDICT 裁决 PASS; ★C: prior=sub_00431B80 占位名非真名撞车, 应合入并解除 CONFLICTS.tsv:300; ★A 五条字节证据全立, 可判[已证]）
- delta 实测数据行：1
  - `00431b80` act=**already** grade [已证]→[已证] name `BufferIOFileClass::~BufferIOFileClass`→`BufferIOFileClass::~BufferIOFileClass`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - ★D: 006CF240 应降[静态推断] (census classification_trace.tsv 非字节件、语义栏自带[未证]、conflict=1 另有3条名争) — 该行不在本卡 delta(仅 00431B80), 抄日志, 不擅自改盘
  - ★E: 0049F740/0049F8B0 的'不可定'理由不足(有 COPYPROTECTION/WChat 串未被用作理由) — 抄日志, 另卡判归属
  - ★B': 合并+降级 proved=53/102=51.96%, 绝对保守底 52/102=50.98%; named 侧零余量(91/102=89.22% 即 FAIL) — 抄日志
- 本卡计数：already=1 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S13-K2（a-S13-K2 VERDICT 裁决 PARTIAL; ★C: 8 行提级合法(硬规矩①+②), 字节级独立复算非绕过降级; 4 处交付文档错误不影响 delta 数字）
- delta 实测数据行：8
  - `0046b540` act=**already** grade [已证]→[已证] name `BulletClass::GetSize`→`BulletClass::GetSize`
  - `0046b550` act=**already** grade [已证]→[已证] name `BulletClass::WhatAmI`→`BulletClass::WhatAmI`
  - `0046c850` act=**already** grade [已证]→[已证] name `BulletTypeClass::WhatAmI`→`BulletTypeClass::WhatAmI`
  - `0046c860` act=**already** grade [已证]→[已证] name `BulletTypeClass::GetSize`→`BulletTypeClass::GetSize`
  - `0075e4f0` act=**already** grade [已证]→[已证] name `WarheadTypeClass::GetSize`→`WarheadTypeClass::GetSize`
  - `0075e500` act=**already** grade [已证]→[已证] name `WarheadTypeClass::WhatAmI`→`WarheadTypeClass::WhatAmI`
  - `007730d0` act=**already** grade [已证]→[已证] name `WeaponTypeClass::GetSize`→`WeaponTypeClass::GetSize`
  - `007730e0` act=**already** grade [已证]→[已证] name `WeaponTypeClass::WhatAmI`→`WeaponTypeClass::WhatAmI`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - PARTIAL 必改 4 处文档事实错误(分隔符0x25='%'非','; 9消费者实为9站点/6函数 7S05+1S06+1S14; DamageArea 实为 S20 非 S06; U3 loader 0x75D3A0 在 atlas/coverage) — 均不影响 delta 数字, 抄日志
  - ★C 保留: 4 条 WhatAmI 名字依赖 §981 槽契约惯例(字节事实确定、名字惯例级), 建议台账备注 — 抄日志
- 本卡计数：already=8 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S13_K5（a-S13_K5 VERDICT 裁决 PARTIAL; 主线A 6 行全部成立; PARTIAL 三点(前缀分摊/164误杀/148分母)不影响 6 行并入）
- delta 实测数据行：6
  - `0040f510` act=**already** grade [已证]→[已证] name `WarheadTypeClass::FindOrMakeIndex`→`WarheadTypeClass::FindOrMakeIndex`
  - `0046c440` act=**already** grade [已证]→[已证] name `BulletTypeClass::FindOrMakeIndex`→`BulletTypeClass::FindOrMakeIndex`
  - `004393f0` act=**already** grade [已证]→[已证] name `BombClass::slot8_deleting_dtor`→`BombClass::slot8_deleting_dtor`
  - `0046c890` act=**already** grade [已证]→[已证] name `BulletTypeClass::slot8_deleting_dtor`→`BulletTypeClass::slot8_deleting_dtor`
  - `0062af70` act=**already** grade [已证]→[已证] name `ParasiteClass::slot8_deleting_dtor`→`ParasiteClass::slot8_deleting_dtor`
  - `007730f0` act=**already** grade [已证]→[已证] name `WeaponTypeClass::slot8_deleting_dtor`→`WeaponTypeClass::slot8_deleting_dtor`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - PARTIAL(a) 前缀分摊应为 20/15/29/28 非 29/28/18/17(总数92不变); (b) 164不可证含≥18条误杀(0065BED0/0075E510); (c) 148分母未裁不得宣布达标 — 抄日志
  - 更正: 0x75E3B0 与 0040F510/0046C440 仅算法族同型, 返回约定不同(索引 vs 指针) — 抄日志
- 本卡计数：already=6 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S15-K3（a-S15-K3 VERDICT 裁决 PARTIAL; ★A/★B 两真名[已证]成立、proved 真到 97; T3 证据缺陷不影响 named/proved 计数; 卡面报3行/实际delta 2行）
- 行数差异：卡面 PARTIAL delta 行=3, coverage_delta.tsv 实测 2 数据行(006E2A10/006E2AA0); 以实测为准
- delta 实测数据行：2
  - `006e2a10` act=**already** grade [已证]→[已证] name `TActionClass::DeleteTrigger`→`TActionClass::DeleteTrigger`
  - `006e2aa0` act=**already** grade [已证]→[已证] name `TActionClass::ForceTrigger`→`TActionClass::ForceTrigger`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - 审计发现①T3-C 证据未重跑覆盖(用错 ID80 臂0x6DEBD0); ②GetSize/WhatAmI 裸字节不特异(666)需槽位锚定; ③0x465d80 误标字符串; ④TActionClass ctor 双点闭合不可复现 — 抄日志, 不影响 named/proved
  - ★D: 5 条 T2 保持 sub_ (无 YRpp 权威名), 执行员未编名属诚实正面证据 — 抄日志
- 本卡计数：already=2 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S18-K2（a-S18-K2 VERDICT 裁决 PARTIAL; 3 条硬[已证](64DAB0/64C380/4A1C10); 004C93D0 排他断言被否证, M7 已登记 PENDING 未降级; atlas_n=659）
- delta 实测数据行：4
  - `0064dab0` act=**already** grade [已证]→[已证] name `sub_0064DAB0`→`sub_0064DAB0`
  - `0064c380` act=**already** grade [已证]→[已证] name `sub_0064C380`→`sub_0064C380`
  - `004a1c10` act=**already** grade [已证]→[已证] name `Checksummer::Add_bulk`→`Checksummer::Add_bulk`
  - `004c93d0` act=**already** grade [已证]→[已证] name `FrameCRC_quant_helper`→`FrameCRC_quant_helper`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - 扣分①: 004C93D0 语义含被否证排他断言(187 vs '仅被0x64DAB0'), 应改写语义或降[静态推断], 不改则 proved 应 56 — 盘上保持[已证], PENDING_CORRECTIONS.tsv:175 已登记, 本卡不重复改
  - 扣分②: 46/46 EventType 为定义级真(cmp eax,0x2D 零自由度)不得写'46次独立裁定'; ③ §3.1 过grade、虚调用剔除数实为6、表在.data — 抄日志
- 本卡计数：already=4 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S12-Q2（a-S12-Q2 VERDICT 裁决 PARTIAL; 核心成立可入账; D-37 归属待裁, 同 grade 不同名/subsystem 保留旧值; 卡面报11行/实际delta 10行）
- 行数差异：卡面 PARTIAL delta 行=11, coverage_delta.tsv 实测 10 数据行; 以实测为准(VERDICT 亦记 8 vs 11 口径差)
- delta 实测数据行：10
  - `0041bea0` act=**already** grade [已证]→[已证] name `ObjectClass::GetMapCoords`→`ObjectClass::GetMapCoords`
  - `005657a0` act=**conflict** grade [已证]→[已证] name `MapClass::TryGetCellAt`→`MapClass::TryGetCellAt`
  - `005f6940` act=**already** grade [已证]→[已证] name `ObjectClass::SetLocation`→`ObjectClass::SetLocation`
  - `0047e8a0` act=**conflict** grade [已证]→[已证] name `CellClass::AddContent`→`CellClass::AddContent`
  - `0047ea90` act=**conflict** grade [已证]→[已证] name `CellClass::RemoveContent`→`CellClass::RemoveContent`
  - `00459ee0` act=**already** grade [已证]→[已证] name `BuildingClass::GetType_slot88`→`BuildingClass::GetType_slot88`
  - `00459ed0` act=**already** grade [已证]→[已证] name `BuildingClass_slot90_getTypeField`→`BuildingClass_slot90_getTypeField`
  - `0043b740` act=**conflict** grade [已证]→[已证] name `BuildingClass::BuildingClass`→`BuildingClass::BuildingClass`
  - `005683c0` act=**conflict** grade [已证]→[已证] name `MapClass::AddContentAt`→`MapClass::AddContentAt`
  - `004544a0` act=**conflict** grade [静态推断]→[静态推断] name `BuildingClass::vslot26`→`BuildingClass::vslot26`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - 必改5项(§951 标签 0x87F924=字段地址非基址; 0x47E8A0 末端 0x47EA89; 1439 中1409紧邻立即数/30经寄存器; +0x9C/+0xA0 是 lepton 非像素; §951 标注未审) — 抄日志
  - 应加注: 0043B740 保留[已证]注明 vptr 写点分属两函数; 0x5657E0 保持[静态推断]加注无越界检查 — 抄日志, 不在 delta 不改盘
- 本卡计数：already=4 upgrade=0 conflict=6 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S01-K2（a-S01-K2 VERDICT 裁决 PARTIAL; delta 0 数据行(卡自报无可并入项); 须降级项(结论1/结论6)抄日志不擅自改盘）
- 行数差异：卡面 PARTIAL delta 行=9, coverage_delta.tsv 实测 0 数据行(仅表头+注释); 以实测为准
- delta 实测数据行：0
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - 须降级(抄日志不擅自改盘): 结论1 0x48CEA1 '必调'错→[静态推断]; 结论6 30槽/vt0x7E1900 错(实11槽/0x7E18FC)→[静态推断]; 结论2 撤回 D3'40条'(实60)、删/降'每帧都跑'
- 本卡计数：already=0 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## 卡 S02-K2（a-S02-K2 VERDICT 裁决 PARTIAL; 4 条 CRT 名字字节体复现; 3 条归位 S02 成立; 卡面报5行/实际delta 4行）
- 行数差异：卡面 PARTIAL delta 行=5, coverage_delta.tsv 实测 4 数据行; 以实测为准
- delta 实测数据行：4
  - `007c9442` act=**already** grade [静态推断]→[静态推断] name `CRT::_nh_malloc`→`CRT::_nh_malloc`
  - `007c8b48` act=**already** grade [已证]→[已证] name `CRT::qsort`→`CRT::qsort`
  - `007c8e25` act=**already** grade [已证]→[已证] name `CRT::bsearch`→`CRT::bsearch`
  - `007c5f00` act=**already** grade [已证]→[已证] name `CRT::_ftol`→`CRT::_ftol`
- 审计要求逐条抄录(delta 外, 不擅自改盘)：
  - 必改3项(LAVOUT §1.2 VirtualFree≠VirtualAlloc/commit=0x8000; [0xB782C4] 按 CRT_NAMES 统一 nhflag; 0x4C85E0 在atlas/0x4C8FE0 在coverage 的'未录入'更正) — 抄日志, 不在 delta 不改盘
  - ★B: _ftol 地址/行为[已证], 符号名属 MSVC 推断; #15 0x7D5DC6 漏命名(≤288 非289) — 抄日志
- 本卡计数：already=4 upgrade=0 conflict=0 not_in_coverage=0 skipped_by_audit=0
- coverage.tsv 本卡落盘后 SHA-256=2db7be9bbe245a3d…（行数 18431）

## CONFLICTS 同步
- 00431B80 status OPEN→RESOLVED_M22（0 行），依据 VERDICT ★C，不删记录。

## 合计
- 处理 8 张卡；{'already': 29, 'upgrade': 0, 'conflict': 6, 'not_in_coverage': 0, 'skipped_by_audit': 0}
- 全表 [已证] 变更前后：1376 → 1376（无 upgrade/降级，盘面不变）。
- PANEL 与 coverage.tsv 自洽：22 子系统 n/named_L/named_S(R14)/named_S(strict)/proved 逐项复算吻合，见 COVERAGE/PANEL.md 的 M22 段。
