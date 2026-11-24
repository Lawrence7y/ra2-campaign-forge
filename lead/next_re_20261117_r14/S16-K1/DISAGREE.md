# S16-K1 DISAGREE（与线索文档的冲突，全部以本卡实测为准）

| # | 线索说法 | 本卡实测 | 裁断 |
|---|---|---|---|
| 1 | `superweapon_re.md` §2：SWType vtable `v[12]=GetSize`、`v[13]=Checksum` | RTTI 实测主 vft `0x7F4090`：v[10]=`0x6CE8F0`→`0x20`(WhatAmI=32)，v[11]=`0x6CE900`→`0x100`(GetSize)，v[12]=`0x6CE910`=CalculateChecksum。SuperClass 才是 v[11]=WhatAmI/v[12]=GetSize | **线索错**（类层次槽位错开 1）；以 E01/E02 为准 |
| 2 | `superweapon_re.md` §3.2：SWType `SidebarImageFile[0x18]` 起点 `+0xCC`，`+0xE8=FlashSidebarTabFrames` | 本卡确认 `SidebarImage` 写 `0xCC..0xE3`（0x18 字节+`.SHP`）；但 `FlashSidebarTabFrames` 实为 **`+0xE8`** 由 loader `6CEAFD` 写、ShouldFlashTab `6CE1C4` 读 — 与线索一致 | 一致（保留） |
| 3 | `superweapon_re.md` §3.2 / `gap_generator_spysat_deep_dive.md`：`SW.AuxBuildings`、`+0xF8 Range` 由 PsychicReveal 读取 | 镜像无 `SW.AuxBuildings` 字符串，只有 `AuxBuilding`→`+0xC8`；PsychicReveal case 11（`6CD70C`）取 `Rules+0xFEC`，**不读** SWType `+0xF8` | **线索措辞不确**；以 E07/E12 为准 |
| 4 | `sw_charge_state_deep_dive.md` §2.1：`0x4F8E4A` 在 `HouseClass::Update 0x4F8440`；`0x4F9397` 在 `0x4F9370` 死代码 | 本卡确认正确，且补充：`function_atlas.tsv` 在 `0x4F830C..0x4F93E0` **整段空洞**，必须用通道 B（序言+ret 区间）归属；`0x4F9370` 0 直接调用/0 imm32 | 一致 + **补充 atlas 洞** |
| 5 | 线索称 `CurrentFrame 0xA8ED84` "唯一 inc 在 0x55DE81" | 本卡全 `.text` 扫到 **10 处写**（`52DA08/55DE81/5B7329/5BB20C/5E550F/5E747C/68466B/686765/795234/79758C`），但只有 `55DE81` 是主循环 `inc edx` 后回写；其余为读档/初始化/重置 | **精确化**：不能说"唯一写"，应说"主循环唯一自增写" |
| 6 | `superweapon_re.md` §1.3：`Grant 0x6CB658` 读 `Type+0xB0` 写 Timer | 本卡确认 `6CB658 mov edx,[eax+0xB0]`、`6CB672 mov [edi+8],edx`；并确认 INI `RechargeTime` 经 `fmul [0x7F4100]=900.0`→`_ftol` 落 `+0xB0` | 一致 + **新增 900.0 换算常数** |
| 7 | 卡正文候选假设"`SW.AuxBuildings` 等" | 该键名猜测未坐实；实际锚点为单数 `AuxBuilding` | 已否证（见 UNKNOWNS #5） |
