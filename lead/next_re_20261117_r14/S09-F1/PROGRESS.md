# S09-F1 PROGRESS（卡号 S09-F1）

## 结论表

| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| 注册窗口过程 | `0x7775C0`（`RegisterClassA @0x777CA5` 的 WNDCLASS.lpfnWndProc=`0x7775C0`） | 已证 | E01,E02,E03 |
| 输入泵 | `PeekMessageA` IAT `0x7E1484`@`0x53EB16/0x53EB99`；`DispatchMessageA`@`0x53E8A1` | 已证 | E01,E02,E04 |
| InputManager 入口 | `WndProc 0x54F790`（ecx=`[0x87F770]`），调用点 `0x7779CB`；事件环 `[0x87F770+0x114]`，head+0x314/tail+0x318 | 已证 | E02,E03,E04 |
| 事件出环 | `GetEvent 0x54F050`，主循环 `0x55E04E`（≤10 条/帧） | 已证 | E01,E04 |
| 左/右键分发点 | WndProc 消息开关 `0x54F7F9`，跳表 `0x54FB4C`(WM 100..105)/`0x54FB64`(WM 202..209)：LDOWN `0x54F8B9`/LUP `0x54F91D`/RDOWN `0x54FAEA`/RUP `0x54FAF0` | 已证 | E03 |
| 快捷键 | WM_KEY/CHAR→`0x54F824/0x54F85C`；CommandClass::Array `0x87F658`，v[8]=Execute（基类桩 `0x4C9150`，46 子类覆写） | 已证(基类)/推断(46 子类) | E01,E09 |
| 屏幕→格映射 | `0x6D6590`（`TacticalClass::PixelCoordToCell`，1265B/12 调用点）；scroll origin `0x886FA0/0x886FA4`；[this+0xB0/B4] 视口偏移；矩阵 [this+0xDE4] | 已证 | E05,E06,E07 |
| 调用者（点击） | `ProcessClickCoords 0x692300`@`0x69238E` 调映射；另 `0x6D2280`(像素→世界坐标) | 已证 | E06 |
| 点选/框选收口 | `DisplayClass::LMBUp 0x4AB9B0`（v[48]），调用点 `0x69328B`（ecx=0x87F7E8） | 已证 | E04,E08 |
| 框选枚举 | `0x6D9FF0→0x6DA5C0`：`0xB0CEC8` 12B 扁平数组 O(N)，Count=`Tactical+0xDB0`；过滤 v[0x2C]/v[0x138]/v[0x14C] + House 闸 `0x50B6F0` | 已证 | E10 |
| 选中集容器 | `0xA8EC78` = `DynamicVectorClass<ObjectClass*>`：Items `0xA8EC7C`(+4)/Count `0xA8EC88`(+0x10)/growth 0xA；另有 `0xA8ECB8` 并行容器 | 已证 | E08,E12 |
| 侧栏 Tab 映射表 | `SidebarClass+0x1544`（实例 `0x87F7E8`→`0x880D2C`），4 Tab×`0xF94`；Cameos[75]@tab+0x58，stride `0x34`；CameoCount@tab+0x54 | 已证 | E10,E11 |
| 图标→生产项 | `0x6AAD00`(SelectClass v[31])：`ItemType/Index`→`GetTechnoType 0x48DCD0`（jt `0x48DD10`,40 类）；ItemType=`0x1F` 走超武分支 | 已证 | E08,E09 |
| Cameo 点击→生产事件 | `0x6AAD00`→`FillEvent_Produce 0x4C6970`（9 直调点：7@0x6AAD00 + 2@0x6AA600） | 已证 | E08 |
| 移动/攻击→Event | `0x4AB9B0`→`FillEvent_Generic 0x4C65E0`@`0x4AC187`（另 6 调用点） | 已证 | E10 |
| Event 环 (S18 接口) | Count `0xA802C8`(<0x80)/Wr `0xA802D0`(&0x7F)/Body `0xA802D4`；回放 `Dispatcher 0x4C6CB0`→jt `0x4C8114`(46 类)→handler `0x4C70E1/0x4C711B/…`→ClickedMission/StartProduction | 已证 | E09 |
| UI 绘制入口 | `SidebarClass::Draw 0x6A6C30`(v[16])；Cameo 绘制 `0x6A9540`（门 `tab+0x1C/0x3C`，DSurface 0x887300，present 0xB0B518） | 已证 | E09 |

## 核心数字（给审计，含复算方法）

1. **链上跳数 = 12**：FLOW 主链 WM→WndProc(0x7775C0)→InputMgr(0x54F790)→PushWord(0x54F1C0)→GetEvent(0x54F050)→Mouse主处理(0x6930A0)→ProcessClickCoords(0x692300)→PixelCoordToCell(0x6D6590)→DecideAction(0x692610)→LMBUp(0x4AB9B0)→FillEvent(0x4C65E0)→Dispatcher(0x4C6CB0)。复算：数 FLOW.md 主链节点（含源/宿）=13，边=12；每条边有上表调用点 VA。
2. **侧栏映射表项数 = 75/条 Tab（4 Tab 共 300）**：复算 `python`：读 `0x6A63D6 cmp edx,0x4B`(75)；`(0xF94−0x58)/0x34=75`；`0x6A61B3` stride 计算 = 3988=0xF94。通道 A=反汇编常量；通道 B=结构算术（不依赖 atlas）。
3. **坐标映射函数 `0x6D6590`**（已证）：12 直调点全 .text skipdata 扫；内含 `sub [0x886FA0/0x886FA4]` + `_ftol 0x7C5F00` + `sar 8`。
4. **选中集容器 `0xA8EC78`**（已证，类型 `DynamicVectorClass<ObjectClass*>`）：`0x732600/0x7327D0` 用 `mov eax,[0xA8EC7C]`/`mov ebx,[0xA8EC88]`；base+4=Items, base+0x10=Count。vft 写点 `0x4E79FD mov [0xA8EC78],0x7E17AC`（构造）/`0x4E7A28 …0x7E180C`（析构），与 0x732600 临时 vector 同 vft（E12）。

## 双通道声明（纪律 1）

- 通道 A：`sweep_calls`/`sweep_disps`（全 `.text` capstone skipdata=True 线性反汇编，E01–E10 的调用点/引用表）。**不依赖 function_atlas 的 entry+size**。
- 通道 B：`.rdata` 虚表直读 + 结构算术 + 字节级 `lea`/`imul` 常量（如 tab stride 0xF94、cameo stride 0x34、75 上限、vft 槽号，E09/E11）。与通道 A 不同源（数据表 vs 代码调用图）。
- 交叉：两通道对 0x6AAD00/0x4C6970/0x4AB9B0/0x6D6590 的结论一致。

## 边界与纪律

- capstone 全程 `skipdata=True`（0x53EBCD 等处跳过的 `.byte` 已显式记录，未当代码存在性判据）；站点归属用函数区间包含（Atlas.contains），非 `entry_at_or_before`。
- `+0xE4` 是 `SidebarImage` 字符串 NUL 终结符（S16-K1 结论），本卡未把它当字段。
- 未用「最近 E8/E9」「最大函数」「无调用者=死代码」等启发式。EVIDENCE 全量未截断（10 文件 ~160KB），复跑脚本在 `work/s01..s11*.py`。
