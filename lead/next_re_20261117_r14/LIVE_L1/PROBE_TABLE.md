# LIVE-L1 PROBE_TABLE — 本卡实际读的地址/宽度/时机/期望值（供后续卡复用）

全部只读 `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + ReadProcessMemory`；输入用 `SetCursorPos/mouse_event/keybd_event`。ImageBase 0x400000，gamemd.exe SHA 73201CC0…F67476。

## 全局标量（dword 除非注明）
| 地址 | 字段 | 宽度 | 时机 | 本卡实测值 | 期望/判据 |
|---|---|---|---|---|---|
| 0x00A8ED84 | CurrentFrame | u32 | 每次试验前后/采样 | 8→20656（各会话） | 活动性判别；局内 >5 |
| 0x00A8B238 | mode | u32 | 全程 | 5（局内/暂停） | ≠§2 的 0x43F180 mode 参数（见 UNKNOWNS） |
| 0x0088095C | hover packed CellStruct | u32 | 放置前/光标后/点击后各 1 | X=lo16,Y=hi16 | 引擎鼠标所在格（§4.2⑤，唯一写点 0x4FB3BC，只读）；JX=(55.6,25.9)/JY=(−55.6,25.9) |
| 0x00886FA0 / 0x00886FA4 | camera scroll X/Y | u32×2 | 每轮闭环 | 恒 (0,0) | 变化即停闭环 |
| 0x00A8E7AC | can-place bypass | u32 | 只读轮询 | 0（全程） | 0⇒逐格校验开启 |
| 0x00A8E9A0 | headA scan gate | u8 | 只读轮询 | 1（全程） | 1⇒WhatAmI 扫描开启 |
| 0x00A8ED6B | backup path gate | u8 | 只读轮询 | 0（全程） | — |
| 0x00B0F724 / 0x00B0F730 | AbstractClass::Array Items/Count | u32×2 | 枚举对象 | Count≈200–250 | 对象枚举基 |
| 0x00A8022C / 0x00A80238 | HouseClass::Array Items/Count | u32×2 | 读 player house | — | — |
| 0x00A83D4C | PlayerHouse | u32 | 每次快照 | 0x10d7xxxx | owner 比对基准 |

## 对象/格偏移（相对指针）
| 表达式 | 字段 | 宽度 | 时机 | 本卡实测 | 来源 |
|---|---|---|---|---|---|
| obj+0x21C | owner HouseClass* | u32 | 筛己方 | ==PlayerHouse | §5/WB |
| obj+0x520 | BuildingTypeClass* | u32 | 型号 | NAPOWR type ptr | §951（非 MapClass） |
| type+0x24 | 短 ID 串 | ASCII≤12 | 型号名 | `NAPOWR`/`NACNST` | WB |
| obj+0x9C / +0xA0 | Location X/Y (lepton) | u32×2 | 取格 | >>8 = cell | §951；cell=(lepton>>8) |
| obj+0x81 | Limbo bool (o1) | u8 | 放置前/后 | limbo=1→placed=0 | §2.3/W176；ghost 在手与 Ready 不可单靠此区分（见 UNKNOWNS） |
| obj+0x74 | 已入格锁存 (o2) | u8 | 放置前后 | limbo 0→placed 1 | W177 |
| obj+0x80 | 精灵脏标记 (o3) | u8 | 只读 | 0/1 | §4.5 |
| obj+0x30 | 格链 next | u32 | 遍历链 | — | §2.2 |
| cell+0xE4 / +0xE8 | 格链头 A/B | u32×2 | 每 trial 前后 | headA 有链；headB 空 | §2.2；A=+0xE4 主链，B=+0xE8 |
| cell+0x24 / +0x26 | Cell self coords | u16×2 | 自检 | 与 idx 一致 | WB |
| 格数组 | `dword[0x87F924]+((Y<<9)+X)*4` | u32 | 取 CellClass* | 有效指针/0xABDC50 哨兵 | §951 |
| vtable RTTI | `vt−4→COL→+0xC→TD→+8` | u8[] | 节点类名 | `.?AVInfantryClass@@`/`.?AVUnitClass@@`/`.?AVBuildingClass@@` | §8.2⑦；COL 在 vt−4 |
| 0x47C620 arg2 | BuildingTypeClass* | — | 静态沿用 | 比较集 {6,2,0x24}，不含 15/1 | §2.4（本卡只读沿用，未动态读 arg2） |

## 屏幕/输入
| 项 | 值 | 说明 |
|---|---|---|
| SetProcessDPIAware 后客户区 | 2560×1440 物理 | 侧栏 x≈2246..2560 |
| 闭环 J 初值 | JX=(55.6,25.9), JY=(−55.6,25.9) px/格 | 阻尼 0.75 + Broyden rank-1；收敛 E=(0,0) |
| 建 NAPOWR 图标 | (2336,472)（top-left build tile，磁能反應爐=NAPOWR） | W177-I 像素定位 + 本卡 l1_full/v2 复核 |
| 足迹颜色阈 | 绿 G>180,R<90,B<90；红 R>180,G<90,B<90 | 220×220 bbox；grass 基线绿≈478–1009，真足迹≈14000–15500 ⇒ 阈值 3000 区分 |

## 未动态读/不可由本卡验证
- 0x43F180 的 mode 参数（挂链 1/3）：调用发生在引擎内部，本卡未下断点（授权禁止 Hook）；只读全局 mode=5 不能替代。
- 0x47C853 断点、arg2 动态值：需硬件断点，未授权，见 UNKNOWNS。
