# LIVE-L2 PROBE_TABLE — 本卡实际读的地址/宽度/时机/期望值（供后续复用）

全部只读 `OpenProcess(VM_READ|QUERY_INFO)+ReadProcessMemory`；输入 `SetCursorPos/mouse_event/keybd_event` via w177_click.click_client（必须带 SetCursorPos+verify，裸 mouse_event 在本环境不落地）。ImageBase 0x400000，gamemd.exe SHA 73201CC0…F67476。

## 主判据相关（核心）
| 地址/表达式 | 字段 | 宽度 | 时机 | 本卡实测 | 期望/判据 |
|---|---|---|---|---|---|
| `obj+0x9C / +0xA0` | Building Location X/Y (lepton) | u32×2 | 放置后读新对象 | cell=(lepton>>8) | 落格 ground truth，不靠 hover 推断 |
| `dword[0x87F924]+((Y<<9)+X)*4` | CellClass* | u32 | 取目标格 | 有效指针/0xABDC50 哨兵 | §951 取格路径 |
| `cell+0xE4` | 格链头 A | u32 | 点击前/后各读 | A 成功时 0→新对象 | 新增 `.?AVBuildingClass@@` 节点且地址=新对象⇒占格 |
| `cell+0xE8` | 格链头 B | u32 | 同上 | 恒空(本卡) | headB 备份链 |
| `elem+0x30` | 格链 next | u32 | 遍历链 | — | 限 32 节点防环 |
| vptr[-4]→COL→+0xC→TD→+8 | RTTI 类名 | ASCII | 逐节点 | `.?AVInfantryClass@@`/`.?AVUnitClass@@`/`.?AVBuildingClass@@` | dsnap.rtti_name（fail-closed，不猜名） |
| `obj+0x21C` | owner HouseClass* | u32 | 筛己方 | ==PlayerHouse(0xA83D4C) | — |
| `obj+0x520`→type+0x24 | BuildingType 短 ID | ASCII≤12 | 型号 | `NAPOWR`/`NACNST` | — |
| `obj+0x81` | Limbo/o1 | u8 | 放置前后 | ghost/建造中=1；已放置=0 | **不能单独区分建造中与 ghost 在手** |
| `obj+0x74` | o2 已入格 | u8 | 放置后 | 已放置=1 | — |

## ghost 在手 / 建造仪表（仅 apparatus，非判据）
| 信号 | 宽度 | 时机 | 本卡实测 | 说明 |
|---|---|---|---|---|
| footprint 颜色 (bbox 220×220 围绕光标) | 像素计数 | 光标移到地图格后 | 绿≥3000 或 红≥3000 ⇒ ghost 在手 | 空地纯绿≈13000–16600；无 ghost 草地<1200；红=不可建 |
| credit `ph+0x30C` | u32 | 下单/等待 | 下单后逐帧递减，稳定于 pre−600 ⇒ 建造完成 | NAPOWR 600；再点图标=ghost 到手 |
| 侧栏 NAPOWR 图标 | 屏幕坐标 | 建完/拾取 | (2336,472)（2560×1440，row0 col0） | 本会话 tooltip 确认为「磁能反应爐 $600」 |

## 闭环定位 / 全局标量
| 地址 | 字段 | 宽度 | 时机 | 本卡实测 | 期望/判据 |
|---|---|---|---|---|---|
| `0x0088095C` | hover packed CellStruct | u32 | aim 每迭代、点击前 | X=lo16,Y=hi16 | hover−Location=(+1,0)；闭环目标=目标格+(1,0) |
| `0x00886FA0/A4` | camera scroll X/Y | u32×2 | aim 卫哨 | 恒(0,0) | 变化即中止闭环 |
| `0x00A8ED84` | CurrentFrame | u32 | 每 trial | 递增 | 活动性 |
| `0x00A8B238` | mode | u32 | 全程 | 5 | 局内 |
| `0x00A8E7AC/E9A0/ED6B` | 旁路三值 | u32/u8/u8 | 快照 | 0/1/0 | 逐格校验开启 |
| AbstractClass::Array Items/Count | `0xB0F724/0xB0F730` | u32×2 | 枚举对象 | ~210–250 | — |
| BUILDING_VT | 0x007E3EBC | u32 | 筛 BuildingClass | obj[0]==VT | wb_probe.enumerate_buildings |

## 输入/瞄准
| 项 | 值 | 说明 |
|---|---|---|
| JX=(55.6,25.9), JY=(−55.6,25.9) px/格 | 阻尼 0.8 迭代 | aim_cell；SAFE=(500,2020,400,1090) |
| 落格 offset | hover−Land=(+1,0) | A 组 4 成功逐一实测一致 |
| 点击必须 | click_client(SetCursorPos+verify) | 裸 mouse_event 在本环境不落地（A 闸失败根因之一） |
| 点击后等待 | ≥2.5s | 落格对象状态约数秒后稳定 |

## 未证/限制
- (105,55) 车辆格屏幕 y≈311 < SAFE 下界 400，闭环不可达（该格未纳入 C 有效 trial）。
- 单位会移动：trial 前须重读 chain_before；单位离格者标无效（B3）。
