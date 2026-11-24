# S06-K1 DISAGREE（与卡面/线索/台账的分歧）

| # | 对象 | 卡面/线索说法 | 本卡实测 | 裁决依据 | 处理 |
|---|---|---|---|---|---|
| D1 | MapClass GetSize | 任务 §3：「两类各自的 GetSize（`v[12]` 的 `B8 <imm32> C3` 形态）与构造器 `push <size>` 两处独立对上」 | **MapClass 没有 GetSize 虚方法**：RTTI `.?AVMapClass@@` 主 vtable `0x7ED404` 全 179 个 .text 槽中 `B8 imm32 C3` = **0 处**；v[12]=`0x4F4410` 是普通函数（比较/分派，非 GetSize）；MapClass 基类 ctor 是 `0x4F4220` ≠ AbstractClass `0x410170`，不属"槽11=WhatAmI/槽12=GetSize"的 69 类通例。单例 `0x87F7E8` 实为 DisplayClass(:MapClass) 实例（vft `0x7E6114`），同样无 GetSize | RTTI COL offset=0 定主 vtable；全表裸扫 B8/C3；构造器写法 | 报 `[已证]` 分歧；MapClass size 改用**派生边界法 =0x1174**（基 ctor 末写 +0x1170(4B)，DisplayClass ctor `4A8730` 首写 +0x1174）；**不凑数**。请 Lead 修订卡面该句 |
| D2 | CellClass 格坐标候选 | 任务 §1：「`+0xFC..0x100` = 格坐标候选（§933 PROBE_TABLE 曾提，标 `[未证]`）」；clue `cellclass_offsets_evidence.md` 称 `+0x24/+0x26` | **MapCoords 确在 `+0x24`(X)/`+0x26`(Y)**：ctor `47BC02` 写 dword、dtor `47BBAD/BA` 与 GetCenterCoords `47FF89/8D` 与 vt18 `486845/49` 读；`+0xFC` 是析构中 delete 的附属对象指针（`47BB91/9B/A1`），`+0x100` 保留 dword（ctor `47BCE7`） | 写点+读点双支撑、纪律 16；不依赖 clue（clue 勘误 E1 已自行撤回其挂钩点结论） | `[已证]` 纠正；§933 候选只对"是字段"成立，对"是坐标"证伪 |
| D3 | 0x485020 调用者数 | R14_COMMON §4.3 / 台账 §923：列出 5 处（`70F9DD/70FA3B/70FAA1/70FAFF/6D7A48`） | 全镜像 **20** 处（另含 `423BAF`、`4DD190/1E4/245/299`、`4DD48D/4B5/553/57B/62D/655/6FC/724`、`568DE1`、`68507A`）；5 处是子集 | 双通道全 `.text` E8 rel32 扫描（capstone 20 == raw 20，集合相同）；非穷举式列点 | 扩充记录；§923 的 5 处不是全量 |
| D4 | CellClass 占用判定 | R14_COMMON §2.2：`0x47E8A0` 挂链不校验占用，校验在上层 Unlimbo | 本卡一致（链头 `+0xE4/+0xE8` 写于 ctor `47BC82/88` 与 linkadd/linkdel）；未找到 CellClass 上独立 bool 占用字段 | 现场反汇编 | 无分歧；记入 UNKNOWNS U4 |
| D5 | 单例类型 | 任务：「MapClass 单例 = 0x87F7E8」 | 该地址最终动态对象是 **PowerClass**（vft `0x7EFF54`，RTTI `.?AVPowerClass@@`）；构造链 `63F6B0→652960→4A8730(DisplayClass)→565090(MapClass)`，MapClass 基子对象在偏移 0，`+0x13C` 仍是格数组基址 | RTTI 链：ctor `63F71C` 写 vft `0x7EFF54`；`0x6AC863`/`0x4A8830` 写中间 vft `0x7E6114`(DisplayClass)；`mov ecx,0x87F7E8`+`call 0x5657A0` 取格 | 语义上仍是"Map/格表单例"（与 §955 纠正一致，非 RulesClass）；类型名精确化为 PowerClass(:DisplayClass:MapClass) | 

> 所有分歧均为实测推翻预设，**未修改任何台账/游戏文件**。D1 是本卡最重要的 negative result，供 Lead 修订卡模板与后续卡引用。
