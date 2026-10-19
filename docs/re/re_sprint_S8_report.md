# S8 专项冲刺报告 · 联机确定性与门控收口深潜

> 任务：**S8 专项冲刺**（派工 v19 · 2026-09-26）  
> 目标文档：[net_sync_checksum.md](file:///d:/Project/ra2-campaign-forge/docs/re/net_sync_checksum.md)（已追加 §13 冲刺结论）  
> 只读引用：[hook_gate_gap_table.md](file:///d:/Project/ra2-campaign-forge/docs/re/hook_gate_gap_table.md)、[MP_SAFETY_REVIEW.md](file:///d:/Project/ra2-campaign-forge/docs/re/MP_SAFETY_REVIEW.md)  
> 分析目标：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，`.text` VA `0x1000`，`FileOffset = VA - 0x400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 工具与复算环境：Python 3.12 + pefile + capstone 5.x，脚本存档于 `out/re_work/re_sprint/S8/`

---

## 0. 冲刺总览与闭环台账

| 流号 | 任务目标 | 闭环数 | 未闭环数 | 核心定谳与新发现 |
|---|---|---|---|---|
| **S8** | 联机确定性与门控收口深潜 | **3 大项 / 7 小项全闭环** | **0** | ① `0x8A0370/-0xC` 定谳为 `LayerClass::Objects[5]` 图层数组，`0x8A03E8` 为循环哨兵；② 超武与微粒 100% 不参与帧 CRC（微粒仅进离线 SYNC 诊断）；③ G-03/G-04/G-06/G-07/G-09 完成字节级指令实证与补强 |

---

## 1. 核心任务一：帧 CRC 尾部簇类型定谳（闭环原 §7.2）

### 1.1 证据溯源与反汇编实证

在 `Compute_Frame_CRC`（VA `0x0064DAB0`，FileOffset `0x24DAB0`）末尾，原文档标记为未确认的 `0x8A0370/-0xC` 与 `0x8A03E8` 代码段如下：

```assembly
; === gamemd.exe 0x0064DCE4 - 0x0064DD92 (FileOffset: 0x24DCE4 - 0x24DD92) ===
0x0064DCE4: bd70038a00       mov      ebp, 0x8a0370                 ; ebp 初始化为 Layer[0].Count
0x0064DCE9: 8b4500           mov      eax, dword ptr [ebp]          ; 取当前 Layer.Count
0x0064DCEC: 33ff             xor      edi, edi                      ; 对象索引 edi = 0
0x0064DCEE: 85c0             test     eax, eax
0x0064DCF0: 897c2410         mov      dword ptr [esp + 0x10], edi
0x0064DCF4: 0f8e8f000000     jle      0x64dd89                      ; 若 Count <= 0，跳下一图层
0x0064DCFA: 8b55f4           mov      edx, dword ptr [ebp - 0xc]    ; edx = Layer.Items (0x8A0370 - 0xC = 0x8A0364)
0x0064DCFD: 8b34ba           mov      esi, dword ptr [edx + edi*4]  ; 取对象 esi = Items[edi]
0x0064DD00: 8bce             mov      ecx, esi                      ; this = esi
0x0064DD02: 8b06             mov      eax, dword ptr [esi]          ; eax = vtable
0x0064DD04: ff502c           call     dword ptr [eax + 0x2c]        ; v[11] WhatAmI() RTTI 类型
0x0064DD07: 83f804           cmp      eax, 4                        ; 是否为 AnimClass (4)?
0x0064DD0A: 750f             jne      0x64dd1b                      ; 非 Anim 则量化坐标进 CRC
0x0064DD0C: 8b4e04           mov      ecx, dword ptr [esi + 4]      ; AnimType
0x0064DD0F: 8d4604           lea      eax, [esi + 4]
0x0064DD12: 50               push     eax
0x0064DD13: ff5110           call     dword ptr [ecx + 0x10]
0x0064DD16: 83f8fe           cmp      eax, -2                       ; 特殊跳过标记 -2
0x0064DD19: 745e             je       0x64dd79                      ; 跳过该动画
0x0064DD1B: 8d969c000000     lea      edx, [esi + 0x9c]             ; 空间坐标 (X, Y, Z)
...
; 坐标量化除以 10 (0x66666667乘法) 并混合进 0xAC51FC
...
0x0064DD79: 8b4500           mov      eax, dword ptr [ebp]
0x0064DD7C: 47               inc      edi
0x0064DD7D: 3bf8             cmp      edi, eax
0x0064DD7F: 897c2410         mov      dword ptr [esp + 0x10], edi
0x0064DD83: 0f8c71ffffff     jl       0x64dcfa
0x0064DD89: 83c518           add      ebp, 0x18                     ; 步进到下一个图层 Count
0x0064DD8C: 81fde8038a00     cmp      ebp, 0x8a03e8                 ; 越界哨兵检查
0x0064DD92: 0f8c51ffffff     jl       0x64dce9                      ; 循环处理 5 个图层
```

紧随图层之后的第二段循环（`0x0064DD98`–`0x0064DE33`）：
```assembly
0x0064DD98: a188f78700       mov      eax, dword ptr [0x87f788]     ; LogicClass.Count
0x0064DD9D: 33ed             xor      ebp, ebp
0x0064DD9F: 85c0             test     eax, eax
0x0064DDA1: 0f8e8c000000     jle      0x64de33
0x0064DDA7: 8b157cf78700     mov      edx, dword ptr [0x87f77c]     ; LogicClass.Items
0x0064DDAD: 8b34aa           mov      esi, dword ptr [edx + ebp*4]  ; 取注册到逻辑心跳的对象
... 逐对象同样调用 WhatAmI() 并混合坐标 ...
0x0064DE33: 8b1530b2a800     mov      edx, dword ptr [0xa8b230]     ; 局内 ScenarioClass 实例
0x0064DE39: 8d8a18020000     lea      ecx, [edx + 0x218]            ; ScenarioClass::Random
0x0064DE3F: e83ce90000       call     0x65c780                      ; 抽取 1 次局内随机数并混合入 CRC
```

### 1.2 真实类型与内存结构判定

1. **`0x8A0360` 的全局数组定谳 [实证]**：
   - 构造函数位于 VA `0x004A8630`–`0x004A866B`（FileOffset `0x0A8630`）。
   - 初始化循环：寄存器 `edx = 5`，初值 `eax = 0x8A0368`，每轮 `add eax, 0x18`。
   - 虚表写入：`mov dword ptr [eax - 8], 0x007E6060`。
   - `symbols.json` RTTI 证实：虚表 `0x007E6060` 属于 `LayerClass`，基类为 `DynamicVectorClass<ObjectClass*>`（单体大小 24 = `0x18` 字节）。
   - 内存布局（`.data` 段）：
     - `LayerClass::Objects[0]`（`Layer::Underground`）：基址 `0x8A0360`，`Items=0x8A0364`，`Count=0x8A0370`。
     - `LayerClass::Objects[1]`（`Layer::Surface`）：基址 `0x8A0378`，`Items=0x8A037C`，`Count=0x8A0388`。
     - `LayerClass::Objects[2]`（`Layer::Ground`）：基址 `0x8A0390`，`Items=0x8A0394`，`Count=0x8A03A0`。
     - `LayerClass::Objects[3]`（`Layer::Air`）：基址 `0x8A03A8`，`Items=0x8A03AC`，`Count=0x8A03B8`。
     - `LayerClass::Objects[4]`（`Layer::Top`）：基址 `0x8A03C0`，`Items=0x8A03C4`，`Count=0x8A03D0`。
   - **`0x8A03E8` 哨兵裁决**：第 4 个图层的 Count 在 `0x8A03D0`，加步长 `0x18` 得到 `0x8A03E8`。`cmp ebp, 0x8A03E8` 是标标准准的 **5 元素定长数组越界哨兵**，绝不存在“0x8A03E8 独立对象”。

2. **`0x0087F778` 的 `LogicClass::Instance` 定谳 [实证]**：
   - 构造函数位于 VA `0x0040CB80`（FileOffset `0x00CB80`）。
   - 写入虚表 `0x007E18FC`，`symbols.json` RTTI 证实为 `LogicClass`（继承自 `LayerClass`）。
   - 字段偏移：`0x87F77C`（Items 缓冲区），`0x87F788`（Count 计数）。
   - 职责：维护所有具有主动逻辑更新需求的对象（技术单位、弹药、活动触发器等）。

---

## 2. 核心任务二：超武/微粒在校验计算流中的定谳

### 2.1 逐链路定谳对照表

针对派工单要求的 `Compute_Checksum` / `0x64DE75` / `0x64C911` / `0x64CC0A` 进行逐指令验证：

| 校验/执行链路 | 地址与上下文 | 超级武器 (`SuperClass`) | 微粒 (`ParticleClass` / `System`) | 实证与分析依据 |
|---|---|---|---|---|
| **每帧锁步 CRC** (`Compute_Frame_CRC`) | `0x64DAB0`–`0x64DE75`<br>（FileOffset `0x24DAB0`） | **完全未抽样 (0%)** | **完全未抽样 (0%)** | `SuperClass` 仅继承 `AbstractClass`（非 `ObjectClass`），无空间坐标，不进图层；微粒存储在专属池 `0xA83DC0/0xA80200`，不进图层与 Logic。`0x64DAB0` 内部 483 条指令无任何涉及超武或微粒的读取 |
| **标准网络事件执行** | `0x64C911` 处 `call 0x4C6CB0` | **命令级执行，无 CRC** | **无** | 派发 Kind `0x18 Special` 或 `0x12 SpecialPlace`。在执行时刻不计算 CRC；其破坏/生成行为在次生帧影响 Unit/Building 坐标 |
| **MegaMission 事件执行** | `0x64CC0A` 处 `call 0x4C6CB0` | **不涉及** | **不涉及** | 仅执行 MegaMission 编队任务 |
| **desync 离线报告** (`SyncReport` / `SYNC*.TXT`) | `0x64DEA0` / `0x6516F0`<br>（FileOffset `0x24DEA0`） | **不单列**（进 House 域） | **包含独立 4 节** | 在 `0x650300` 循环计算微粒 CRC（`*** Particle CRCs ***` 与 `*** Particle System CRCs ***`），调 `v[13] CalculateChecksum` |

### 2.2 核心结论

1. **在线锁步安全**：超级武器与微粒**均不被抽样进每帧锁步比对的 `CurrentFrameCRC`**。对微粒系统进行任何纯表现层渲染优化（如粒子发射率、轨迹剔除、光晕），只要不破坏其所属逻辑实体状态，**绝对不会触发联机 desync**。
2. **离线诊断差异**：微粒被纳入了 desync 发生后的诊断文本（`SYNC*.TXT`）。若未来有人扩展修改了 `ParticleClass` 的内部字段并触碰了 `CalculateChecksum` (v[13])，只会在双方 desync 抓包分析时打印出不一致，而非导致 desync 的诱因。
3. **超武的分叉链路**：超武充能与射击是纯逻辑状态（`IsCharged/Granted`），其本身不直接进帧 CRC，但通过：
   - 冷却时间到了产生 `SpecialPlace` 命令；
   - 产生核弹/闪电风暴 Anim 与伤害；
   - 改变目标建筑物与单位的血量及存活状态；
   间接在后续帧迫使图层与单位数组中的坐标和状态改变，从而在 `0x64DAB0` 中被捕获。

---

## 3. 核心任务三：G-03 / G-04 / G-06 / G-07 / G-09 缺口实证补强

### 3.1 G-03 · L2 Threat Retention 无独立门控键 [实证补强]
- **精准地址与原始指令**：
  - 目标：`TechnoClass::Greatest_Threat`
  - VA：`0x006F8DF0`（FileOffset：`0x2F8DF0`）
  - 原指令（9 字节）：`83 EC 5C 8B 15 34 EC A8 00`（`sub esp, 0x5c; mov edx, dword ptr [0xa8ec34]`）
  - 原版行为：递增调用全局计数器 `0xA8EC34`，并分配 0x5C 局部栈帧展开空间桶、螺旋 Cell、单位数组的三路完整择优打分。
  - 当前 Hook 改写：`blitter_hooks.cpp:495-502` 覆盖 9 字节跳转至 `Hook_Techno_Greatest_Threat`，在 `((unitHash + currentFrame) % interval) != 0` 节流帧短路直接 `return *(void**)(pThis + 0x5D4)`。
- **补强分析 [推演]**：
  - 目标保持改变了原版“每帧对当前威胁重新严格打分择优”的机制。在敌人移动出射程或更高危目标（如自爆卡车、天启坦克）逼近时，节流帧会粘滞于旧目标。
  - 目前 Target Retention 逻辑与 `TargetScanInterval` 强耦合，没有独立的 ini 开关（如 `EnableThreatRetention`）。若联机对拍中发现目标粘滞造成分叉，只能将 `TargetScanInterval=1` 整体禁用节流，无法单独关闭 retention 保留调度节流。
- **治理建议**：新增 `[Logic] EnableThreatRetention=0/1`，联机自动降级白名单 W2 联动设为 0。

### 3.2 G-04 · B1/B2 混色桩与 L4 补丁无独立键 [实证补强]
- **精准地址与原始指令**：
  - **B1 混色桩**：VA `0x0047F40F`（FileOffset：`0x07F40F`），长度 49 字节。
    - 原指令起首：`66 8B 08 66 83 F9 7F 75 07 66 33 C9 8A CB EB 1E 8B 54 24 48 ...`
  - **B2 混色桩**：VA `0x0047F4AE`（FileOffset：`0x07F4AE`），长度 51 字节。
    - 原指令起首：`66 8B 08 66 83 F9 7F 75 09 66 0F B6 D2 66 89 10 EB 21 ...`
  - **L4 视口全量重绘补丁**：VA `0x006D3D99`（FileOffset：`0x2D3D99`），原指令 6 字节：
    - `0F 8D 98 00 00 00`（`jge 0x006D3E37`）
    - 安装改写：`E9 99 00 00 00 90`（`jmp 0x006D3E37; nop`）
- **补强分析 [实证]**：
  - `InstallCellClassDrawHook` 在安装时**无条件**对上述三处打入跳板和跳转补丁；
  - 即使在 `ra2render.ini` 中设置 `EnableStarCraftFog=0`、`FadeFogTransition=0`，上述代码段仍被改写，B1/B2 桩依然执行（仅强度固定 256），L4 依然强制跳过脏矩形判断每帧重绘全屏视口；
  - 这破坏了“全关迷雾回到原版纯净基线”的承诺，并与 Q7 脏矩形优化折中直接冲突。
- **治理建议**：在 `InstallCellClassDrawHook` 增加门控，当 `EnableStarCraftFog=0` 时完全跳过写入；补齐 `[Render] L4DirtyMode=force-full|off`。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0

### 3.3 G-06 · S2/S3 状态写无独立键 [实证补强]
- **精准地址与原始指令**：
  - **S2 (`ScenarioClass` 标志 `&= ~0x1000`)**：
    - 读取端点 1：VA `0x006D8FCB`（FileOffset `0x2D8FCB`）：`test ah, 0x10; je 0x6D8FE7`。若为 1 则调用 `MapClass::IsCellShrouded 0x5865E0` 进行绘制剔除。
    - 读取端点 2：VA `0x006D9630`（FileOffset `0x2D9630`）：`test ah, 0x10; je 0x6D966A`。
    - 写入行为：`blitter_hooks.cpp:747` 强行清零该位以绕过引擎迷雾剔除。
  - **S3 (`HouseClass + 0x577A` SpySatActive)**：
    - 写入端点：VA `0x00509054`（FileOffset `0x109054`）：`mov al, [esi+0x577a]; test al, al; jne ... mov byte ptr [esi+0x577a], 1`（间谍卫星上线时全图揭示）。
    - 消费端点：VA `0x0050BD10`（FileOffset `0x10BD10`）：`mov al, [ecx+0x577a]; test al, al; jne 0x50bd25; call 0x577ab0`（若为 1 则阻止裂缝产生器重黑视野）。
    - 写入行为：`blitter_hooks.cpp:753` 每逻辑帧强行将 `pPlayer + 0x577A` 写为 0。
- **补强分析 [实证]**：
  - `ScenarioClass` 与 `HouseClass` 均为联机锁步契约内的核心可序列化状态。
  - 在混联模式下，安装 DLL 的客户端强清两处状态，而原版客户端保持引擎逻辑，将立即造成两端迷雾覆盖与裂缝产生器生效时序的永久分叉。
  - 只要任意 fog 键开启并调用 `UpdateVisionGrid`，S2/S3 就会被无条件写入，无独立控制键。
- **治理建议**：新增 `[Multiplayer] MpStateWrites=0` 开关（或与 `EnableSpySatRadarSweep` 强绑定）；联机模式检测到非完全对称客户端时强制关闭写操作。

### 3.4 G-07 · S1 TYPE 补丁无 Remove 还原 [实证补强]
- **精准地址与原始指令**：
  - `BuildingTypeClass + 0x16A5`（SpySat 布尔标志）：在 VA `0x00508F88` 读取（`cmp byte ptr [eax + 0x16a5], 0`）；
  - `BuildingTypeClass + 0x16F0`（超武索引）：在 VA `0x004516B1` 读取（`cmp dword ptr [eax + 0x16f0], -1`）；
  - `SuperWeaponTypeClass + 0xB0`（RechargeTime 充能帧数）与 `+0xF8`（Range 范围）。
- **补强分析 [实证]**：
  - `PatchSpySatBuildingTypes`（`blitter_hooks.cpp:597-623`）直接覆写了内存中全局唯一的 Type 规则对象。
  - 现网在 `RemoveVTableHooks` 或战局结束（`OnGameEnd`）中没有对应的反向赋值逻辑。一旦打上补丁，即使在 ini 中关闭开关或退出对局回到主菜单开始原版战役，间谍卫星的类型属性仍然处于被篡改状态（全图揭示丢失，变为雷达扫视），造成进程生命周期内的永久污染。
- **治理建议**：在补丁前将原内存的 4 项数据备份至静态变量，在 `RemoveVTableHooks` 和战局结束钩子中执行严格对称还原。

### 3.5 G-09 · `EnableMinimapFog=1` 时 everSeen 记忆不进档 [实证补强]
- **精准地址与原始指令**：
  - `CellClass::Save`（VA `0x00483C10`，FileOffset `0x083C10`）与 `CellClass::Load`（VA `0x004839F0`，FileOffset `0x0839F0`）仅序列化引擎原生的 Cell 属性。
  - `s_everSeenGrid` 为 512×512 字节数组（256 KB），位于 `ra2render.dll` 私有未初始化内存中，完全独立于引擎存档流。
  - 关键代码 `blitter_hooks.cpp:714-721`：
    ```cpp
    if (currentFrame < s_lastFrame - 30) {
        memset(s_everSeenGrid, 0, sizeof(s_everSeenGrid));
        ...
    }
    ```
    当玩家读档导致 `currentFrame` 出现大幅回退时，DLL 显式执行 `memset` 将 `s_everSeenGrid` 全面清零。
- **补强分析与裁决 [实证]**：
  - `s_everSeenGrid` 纯属表现层数据，未挂入 `Compute_Frame_CRC`，因此清零行为**绝不会引起联机锁步 desync**；
  - 现象表现为：读档后，先前侦察过的战争迷雾建筑暗影全部消失，需单位重新侦察方可再次盖章。此属体验/UX 遗留，而非锁步安全违规，定谳为“已知体验限制”，免除联机安全整改阻断。

---

## 4. 产出物清单与复算索引

| 路径 | 类型 | 说明 |
|---|---|---|
| `docs/re/net_sync_checksum.md` | 文档（追加） | 原地追加 §13 冲刺结论，闭环核心定谳 |
| `docs/re/re_sprint_S8_report.md` | 文档（新建） | 本报告文档 |
| `out/re_work/re_sprint/S8/disasm_64dab0.py` | 脚本 | `Compute_Frame_CRC` 完整反汇编提取 |
| `out/re_work/re_sprint/S8/find_tail_xrefs.py` | 脚本 | 全局图层与哨兵交叉引用检索 |
| `out/re_work/re_sprint/S8/inspect_sync_strings.py` | 脚本 | 诊断性 SYNC 报告字符串定位 |
| `out/re_work/re_sprint/S8/disasm_4a8640.py` | 脚本 | `LayerClass::Objects[5]` 构造函数与析构函数反汇编提取 |
| `out/re_work/re_sprint/S8/check_v11_returns.py` | 脚本 | `AbstractClass::WhatAmI()` 各兵种返回值定谳提取 |
| `out/re_work/re_sprint/S8/find_7e18fc.py` | 脚本 | `LogicClass` 虚表与实例定谳提取 |
| `out/re_work/re_sprint/S8/find_all_call_34.py` | 脚本 | 全局 `CalculateChecksum` (v[13]) 调用点扫描 |
| `out/re_work/re_sprint/S8/disasm_greatest_threat.py` | 脚本 | G-03 `Greatest_Threat` 原字节与指令提取 |
| `out/re_work/re_sprint/S8/disasm_b1_b2_l4.py` | 脚本 | G-04 B1/B2 混色桩与 L4 原字节指令提取 |
| `out/re_work/re_sprint/S8/find_577a_refs.py` | 脚本 | G-06 `House+0x577A` 与 `Scenario` 标志位读写点提取 |
| `out/re_work/re_sprint/S8/find_sw_type_offsets.py` | 脚本 | G-07 S1 TYPE 补丁字段读写端点提取 |
| `out/re_work/re_sprint/S8/disasm_cell_save.py` | 脚本 | G-09 `CellClass::Save` 读档重置行为提取 |

---

## 5. 台账 §九 草稿（供 Lead 合并）

```markdown
### [v1.5.29] - 联机确定性与门控收口深潜（S8，纯逆向与实证，无补丁）
#### 1. 现象与需求描述
- 针对联机锁步确定性基础设施展开字节级实证，定谳帧 CRC 尾部簇类型，裁定超级武器与微粒是否进每帧 CRC，并对门控缺口表 G-03/G-04/G-06/G-07/G-09 提供指令级实证。
#### 2. 逆向调研与根因剖析
- 尾部簇定谳：0x8A0360 为全局图层数组 LayerClass::Objects[5]（步长 0x18），0x8A0370 为第 0 图层 Count，0x8A03E8 为循环越界哨兵；0x87F778 为 LogicClass::Instance。原 §7.2 未决项彻底闭环。
- 校验流定谳：超级武器（SuperClass）与微粒（Particle/ParticleSystem）100% 不进每帧锁步比对的 Compute_Frame_CRC。微粒仅在发生 desync 后的 SYNC*.TXT 离线诊断中由 CalculateChecksum 扫描。
- 缺口实证：
  - G-03：0x006F8DF0 TechnoClass::Greatest_Threat 原 9B (83 EC 5C 8B 15 34 EC A8 00)；Target Retention 缺乏独立键。
  - G-04：0x0047F40F (B1, 49B)、0x0047F4AE (B2, 51B)、0x006D3D99 (L4, 6B 原 0F 8D 98 00 00 00) 无条件安装，全关迷雾仍生效。
  - G-06：Scenario+0 位 0x1000（0x006D8FCB 读取）与 House+0x577A（0x00509054/0x0050BD10 读写）无独立开关，随 UpdateVisionGrid 强写。
  - G-07：BuildingType+0x16A5（0x00508F88 读取）与 +0x16F0（0x004516B1 读取）等 TYPE 补丁缺乏对称卸载还原逻辑。
  - G-09：CellClass::Save (0x00483C10) 不含 s_everSeenGrid；blitter_hooks.cpp:717 帧号倒退时显式 memset 清零，属已知体验限制而非 desync。
#### 3. 具体修改与补丁实现
- 无引擎代码补丁。更新 docs/re/net_sync_checksum.md 追加 §13 冲刺结论，产出 docs/re/re_sprint_S8_report.md。
#### 4. 实测验证效果
- [实证] 经 Python + pefile + capstone 静态提取 gamemd.exe 字节，指令与偏移 100% 对齐；双端真机对拍维持挂起。
```
