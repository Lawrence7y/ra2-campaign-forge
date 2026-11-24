# S08-K1 DISAGREE

| # | 对象 | 分歧 | 本卡裁决 | 依据 |
|---|---|---|---|---|
| D1 | 任务卡提法「迷雾按格存储？位图(1bit/格)还是字节数组？」 | 二选一预设 | **两者都不是**：每格 CellClass 对象字段（1 个 stride-4 指针数组 + 每格独立字节/位） | E01 `test byte [cell+0x12C],8` + `[0x87F924+idx*4]`，无 `shr idx,3` 位运算 |
| D2 | 线索 `unit_visibility_mechanism.md`：`0x5865E0` 全 exe 25 处调用 | 本卡通道 B=25，atlas `n_callers=24` | 采 **25**（通道 B 可复跑逐址）；atlas 少 1 记 UNKNOWNS U5 | E01/E13 V3 |
| D3 | 线索 `radar_minimap_dots.md` 早期记 `0x655D38 call 0x578080 = MapClass::GetCell` | 该文档自身勘误 E4b 改为 `GetCellFloorHeight` | 采 **勘误口径**（`GetCellFloorHeight`），标 `[待复核]` | 线索 §9.1 E4b；本卡未复核该支 |
| D4 | 线索 `fog_split_report.md` E3 原记「`+0x12C bit3` 不是已探索位，在 `+0x140`" | 同文档 E3·就地订正反向证伪 | 采 **`+0x12C bit3(0x08)=cf_Explored`** | E01 读 `0x5863F2 test [ecx+0x12C],8` + 写 `0x4A98EC or al,8` 双向 |
| D5 | 线索称 RadarClass 单例 `0x87F7E8` | 与已入账事实（MapClass 单例=`0x87F7E8`）冲突 | 判线索该处**笔误**：`0x87F7E8` 是 **MapClass**；RadarClass 是 SidebarClass 基类子对象 | 任务卡已证事实 + E01 `mov ecx,0x87F7E8` 调 Map 谓词 + E10/E11 Sidebar ctor 链 |
| D6 | 「每帧更新入口」是否 = `CellClass::Draw 0x4801F0`（2 调用者） | 该入口是逐可见格渲染态重算，不是逻辑帧驱动 | 采 **`UpdateSpySat 0x508F60`（1 调用者）**为每帧迷雾状态更新入口；`0x4801F0` 单列为渲染侧重算 | E08/E09/E13 V4 主帧链 |
