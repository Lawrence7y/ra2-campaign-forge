# RADAR-FIX2 交付报告：改用引擎原生减暗路径（放弃自绘灰化）+ 清 P0 悬项

> 任务号：RADAR-FIX2（派工方：Lead / ZC-2 复验后续）
> 执行方：DSH 子代理（会话 session-852a2193 之下）
> 工作区：D:\Project\ra2-campaign-forge（Windows）
> 基线：ra2youli\gamemd.exe（MD5 4f37486e5b0dbe2ae5f45aeee0f98367，只读未变）
> 产物：ra2render.dll 134,144 B / MD5 961E4B6C883E4D18C48B293CF5D53122（已部署 ra2youli\）
> 证据口径：全部结论给 VA + FileOffset + 原始字节 + Capstone 反汇编 + xref；未跑的一律标 [待实测]

---

## [META]

- task=RADAR-FIX2 executor=DSH 子代理（deepseek-v4.1-flash harness） mode=accept-edits
- scope_declared=ra2render/**、ra2youli/ra2render.{dll,ini}、新建 docs/re/radar_fix2_report.md、out/re_work/radar_fix2/**
- 快照时点：本轮所有 exe 反汇编基于只读基线 gamemd.exe（MD5 4f37486e…，2026-09-27 复算一致）；
  所有 DLL 反汇编基于本轮重建产物 MD5 961E4B6C…（构建时间 2026-09-27 14:31）。

---

## [0] 结论摘要

1. **F1 定谳：0x00B73550 不是迷雾开关，而是 Game::hWnd（游戏主窗口句柄 HWND）** —— YRpp 常量 + 全 exe 仅 2 个写点（均为 CreateWindowExA 返回值落地）+ 77 处读点全部当 Win32 窗口句柄用（SetFocus/SetCapture/ShowWindow/GetClientRect/...）。**写它会污染 70+ 处 Win32 调用** ⇒ F2 分支 ① 否决。
2. **F2 取分支 ②：新增挂钩 0x00655D87（7 字节）按我方三态视野谓词驱动引擎减暗判定位 [esp+0x13]，直接复用引擎减暗体（像素精确 50% 减暗），不自绘像素**；自绘路径降级为 RadarFogGuardMode 0/1/2 的 A/B 对照档；新增遥测「原生减暗路径命中次数」+ 引擎自身判定数 + 覆盖差 + 早退分桶。
3. **S3 FAIL（分支计数增长、像素恒 0）根因已定谳**：0x00655D38 处 EAX **不是 CellClass\***，而是 **MapClass::GetCellFloorHeight()（0x578080）返回的格面高度 int**（YRpp/MapClass.h:282 与 :417 明确定义为 int，且 0x578080 以 ret 4 返回）；旧代理把它当 pCell ⇒ 首道 cmp eax,0x10000/jbe 护栏**恒被拒**，灰化静默早退。这与真机日志（分支 16303→17284 单调、像素 0）逐条吻合。
4. **F3 清项**：(a) ScenarioClass+0x3598 非 IsLoadingScreen（YRpp 记 unknown_3598；全 exe 12 处访问均为字节粒度门控；真机 = 0x92）⇒ 该判据已删，改为雷达双表面有效性；(b) s_visionGrid 盖章链给出 3 条候选根因 + 新增 5 个诊断计数（一轮真机即可定位）；(c) 我方 proxy 早退序列/寄存器契约/EAX 语义已逐条反汇编核对，**EAX 语义错认即 S3 根因**。
5. **门禁全绿**：verify_anchors.py 323/323 PASS；audit_bytes.py 41/41 OK；产物级反汇编确认三个挂钩点（0x655D38 / 0x65719A / 新增 0x655D87）与档位分派、新遥测符号齐备。
6. 出厂默认 **EnableMinimapFog 仍为 0**（未过真机验收不放行），ZC-3 需手动置 1；见 §10 步骤与 [9] 待裁决。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-1 | 0xB73550 是不是「迷雾总开关」？ | **不是**。= Game::hWnd（主窗口句柄 HWND） | [实证] | YRpp/Unsorted.h:17、ref/yrpp/Unsorted.h:17；exe 0x00777CD6/0x00777D7E（唯二写点）；0x00692489/0x006931DD/0x006938D5（读点样例） |
| F1-2 | 谁写它、何时为 0/非 0？ | 仅 2 处写点，均为 USER32!CreateWindowExA 返回值落地；0 = 窗口创建前（启动早期），窗口创建后恒定非 0（菜单与局内皆非 0）⇒ 它是「有窗口」弱门控，不是菜单/局内判别器 | [实证] | IAT 解析：0x7E14D4=CreateWindowExA；0x7E13CC=SetFocus、0x7E13FC=SetCapture、0x7E146C=UpdateWindow、0x7E1498=ShowWindow、0x7E14C4=GetClientRect、0x7E13F8=ReleaseCapture（pefile 导入表） |
| F1-3 | 与 FogOfWar 串（0x0082C3D4）的关系？ | **无关联**。该串属一段 "BridgeDestroy: %s / FogOfWar: %s / Crates: %s / Crap Engineers: %s" 的调试打印格式串表；0xB73550 无任何 xref 指向该串所在代码 | [实证] | 0x0082C3D4 前后 48 字节 dump；0xB73550 全库 197 个原始命中分类结果（77 读 / 2 写 / 其余为立即数误配） |
| F2-1 | 走 ① 还是 ②？ | **②**（① 被否决：写 HWND 会污染 70+ 处 Win32 调用） | [实证] | 见 §2；[7] 红线 |
| F2-2 | 最简改动 | 新增 H3 挂钩 0x00655D87（7B，mov eax,[edi+4] + mov [esp+0x14],ebp）+ 跳板；在引擎判定完成后按我方三态谓词改写 [esp+0x13]；**删掉自绘 Get/Set 像素的默认路径**（保留为档 0/1/2） | [实证]（产物反汇编） | 产物 0x10002290（H3 代理）、0x10004400（RadarHook_NativeDecide） |
| F2-3 | 引擎原生减暗 vs 自绘像素等价性 | **逐通道等价**（代数证明见 §5）：引擎 = 提取三通道各 shr 1；自绘 = (c>>1)&0x7BEF ≡ R'=floor(R/2)、G'=floor(G/2)、B'=floor(B/2)，源像素同为 [this+0x1220] | [实证]+[推演] | exe 0x655EEE/0x655F0A/0x655F20（三处 shr reg,1）；0x655E8A（源表面）、0x655EE2（目标表面） |
| F2-4 | 新增遥测「原生减暗路径命中次数」 | 已加：s_nativeDarkenHits（最终 flag=1 次数）+ s_nativeEngineDarkHits（引擎自身判定为暗）+ s_nativeForcedDarkHits（我方强制）+ s_nativeOverrideDeltas（覆盖差） | [实证]（产物反汇编计数点） | 产物 0x102E19F4 / 0x102E19F8 / 0x102E19FC / 0x102E1A00；DLL 字符串 0x10018C50（[ra2render-telemetry-radar]） |
| F3-1 | ScenarioClass+0x3598 真实语义 | **非 IsLoadingScreen**：YRpp/ScenarioClass.h:224 记为 DWORD unknown_3598；全 exe 12 处访问均为**字节**粒度门控（cmp byte [scn+0x3598],0）；真机实测字节 = 0x92（非 0/1）⇒ 原判据无据。**替代谓词**：雷达双表面 [0x87F7E8+0x121C]/[+0x1220] 有效性 + GameMode∈[0,5] | [实证]+[待实测]（0x92 为 ZCode 实测） | exe 0x0048D001、0x0048D0EF、0x005989DC、0x00598B1E、0x00598BA4、0x00598D07、0x00598D8D、0x00598E6C、0x00598FFF、0x005990A4、0x0059918F |
| F3-2 | s_visionGrid 为何从未盖章 | **静态不可闭环**。已排除：数组 Items/Count 偏移读法正确（YRpp/ArrayClasses.h：Items +0x04、Count +0x10）；UpdateVisionGrid 帧守卫、pPlayer 判据、stampTechnoArray 门槛均可达。候选根因 3 条：(a) 对象健康过滤读 pObj+0x6C（偏移未独立实证）；(b) isPlayerOrAlly 的 ownerIdx(+0x30)/allies(+0x5788)；(c) 观测为测量假象（主视图 半透明迷雾格子=8.3M 说明同一条 0x12C cf_Explored 判据与网格消费链在实际运行中活着）。⇒ **本轮已加 5 个诊断计数**（求解成功/失败、已探索、直视圈内、各早退桶），一轮真机即可定位 | [实证]（排除项）+[待实测]（根因） | blitter_hooks.cpp:879-1032（UpdateVisionGrid）、:943-979（stampTechnoArray）、:1070/:1140/:1188/:1231（消费点）；ra2youli/ra2render.log（真机日志原文） |
| F3-3 | 我方 Hook_RadarPlot_Cell_Proxy 早退序列/寄存器契约/EAX 语义 | 反汇编（旧产物 0x10002250 / 新产物 0x100022F0）与源码**逐条一致**，无 codegen 缺陷；寄存器契约经复核正确（EAX/ESI/EDI/EBP 保持、ECX/EDX 可破）。**EAX 语义错认 = S3 直接根因**：非 CellClass\* 而是格面高度 int ⇒ 首道 pCell 护栏恒拒 | [实证] | 旧产物反汇编（out/re_work/radar_fix2/artifact_verify_prev.txt）、新产物同上；exe 0x5780F6（ret 4）、YRpp/MapClass.h:282/417 |
| F4-1 | 编译与部署 | VS2022 x86 编译通过（build_log.txt，0 warning）；旧 DLL 备份；新 DLL 已部署 ra2youli\；两份 ini 同步（字节一致，单 [Logic] 节） | [实证] | §6 / §8；MD5 961E4B6C…；备份 out/re_work/radar_fix2/ra2render.dll.bak-pre-fix2 |
| F4-2 | build.bat 越界副作用 | 已改为**可选**：默认不覆盖已部署 ra2loader.exe，仅当 set RA2RENDER_DEPLOY_LOADER=1 时部署（本轮构建日志出现 skip 行，仅 1 file(s) copied） | [实证] | ra2render/build.bat:31-44；build_log.txt |
| F5-1 | 产物级验收 | 三个挂钩点立即数齐备（0x655D38×6、0x65719A×5、0x655D87×6）；H1/H3 代理与跳板装配正确；档位分派 cmp byte [0x10021022],3；新遥测符号/字符串齐备；hWnd **只读**（全 .text 仅 1 处 cmp [0xb73550],0） | [实证] | out/re_work/radar_fix2/artifact_verify.txt |

---

## [2] 关键证据块

### 2.1 F1：0xB73550 = Game::hWnd（HWND）

交叉来源 1（项目自带 YRpp 常量表，两处副本一致）：

    YRpp/Unsorted.h:17            static constexpr reference<HWND, 0xB73550u> const hWnd{};
    ref/yrpp/Unsorted.h:17        static constexpr reference<HWND, 0xB73550u> const hWnd{};
    ref/yrpp/Unsorted.h:18        static constexpr reference<HINSTANCE, 0xB732F0u> const hInstance{};

（旁证：0xB732F0 与 0xB73550 在 0x5E2D33/0x788CEA/0x793250 等处紧邻出现，与 hInstance/hWnd 同族。）

交叉来源 2（exe 全库 xref 分类；工具 out/re_work/radar_fix2/d3_xref.py + d5_classify.py）：

    原始 4 字节命中 197 处 → 去除立即数误配后：读点 77、写点 2
    写点 1  0x00777CD6  A3 50 35 B7 00   mov [0x00B73550],eax    ← 紧随 call [IAT 0x7E14D4]
    写点 2  0x00777D7E  A3 50 35 B7 00   mov [0x00B73550],eax    ← 同上
    IAT    0x007E14D4 = USER32.dll!CreateWindowExA   （pefile 导入表解析）
    读点样例:
      0x00692489  A1 50 35 B7 00        mov eax,[0xB73550]      ; ProcessClickCoords 内
      0x006931DD  8B 0D 50 35 B7 00     mov ecx,[0xB73550] ; push ecx ; call [0x7E13FC]
      0x006938D5  8B 0D 50 35 B7 00     mov ecx,[0xB73550] ; cmp eax,ecx ; jmp [0x7E13F8]
      0x00664031/0x006227F1/0x006313D1/0x00631582/0x00787DDC/0x0077DE5B ... 共 77 处
    IAT 语义: 0x7E13CC=SetFocus 0x7E13FC=SetCapture 0x7E13F8=ReleaseCapture
              0x7E146C=UpdateWindow 0x7E1498=ShowWindow 0x7E149C=InvalidateRect
              0x7E14A4=SendMessageA 0x7E14B4=SetRect 0x7E14C4=GetClientRect
              0x7E14D0=SetForegroundWindow 0x7E1400=AdjustWindowRectEx
              0x7E1404=GetMenu 0x7E141C=GetTopWindow 0x7E1420=GetForegroundWindow

⇒ 定谳：**它是窗口句柄，不是迷雾开关**。真机「战役局内 0xB73550 非 0」与「菜单里也非 0」都成立，故它区分不了菜单/局内，也表达不了迷雾状态；引擎在 Plot_Cell 里读它只为「窗口已建立 ⇒ 有渲染上下文」。

### 2.2 F1 附：0x0082C3D4（FogOfWar 串）与本全局无关联

    0x0082C3D4 前后 64 字节:
    ...  'uce: %s\n\0\0\0\0BridgeDestroy: %s\n\0\0FogOfWar: %s\n\0\0\0Crates: %s\n\0Crap Engineers: %s\n\0'
    ⇒ 一段调试打印格式串表（"Xxx: %s" 系列），非 INI 键解析点；无 xref 把 0xB73550 与它关联。

### 2.3 F3③ 核心：0x00655D38 处 EAX 的真实语义（S3 FAIL 根因）

exe 反汇编（0x655D14–0x655D41，Capstone，基线 MD5 4f37486e…）：

    0x00655D14  8D 44 24 20        lea eax,[esp+0x20]              ; &CoordStruct{X,Y,Z}
    0x00655D1B  89 4C 24 20        mov [esp+0x20],ecx             ; X = cellX*256+128 (lepton)
    0x00655D25  50                 push eax
    0x00655D2B  89 54 24 28        mov [esp+0x28],edx             ; Y
    0x00655D2F  89 6C 24 2C        mov [esp+0x2c],ebp             ; Z = 0 (预置)
    0x00655D33  E8 48 23 F2 FF     call 0x00578080                ; ← MapClass::GetCellFloorHeight
    0x00655D38  89 44 24 28        mov [esp+0x28],eax             ; ← 返回值写回 Z 槽（不是 pCell 缓存！）
    0x00655D3C  A1 50 35 B7 00     mov eax,[0x00B73550]           ; Game::hWnd
    0x00655D41  3B C5 74 18        cmp eax,ebp / je 0x00655D5D

0x578080 的返回契约 [实证]：

    YRpp/MapClass.h:282   int GetCellFloorHeight(const CoordStruct& crd) const { JMP_THIS(0x578080); }
    YRpp/MapClass.h:417   int sub_578080(CoordStruct *Coords)          { JMP_THIS(0x578080); }
    0x00578080  83 EC 08 8B 4C 24 0C     sub esp,8 ; mov ecx,[esp+0xC]   （只读 [ecx]/[ecx+4]，不读 [ecx+8]）
    0x005780F6  C2 04 00                  ret 4                            （被调方清栈 ⇒ 0x655D38 处 esp 已复位）
    ⇒ 返回值 EAX = int（地形/格面高度，单位 lepton；LevelHeight=104），**不是 CellClass\***。

旧代理据此写的第一道护栏（旧产物 0x100022BF，逐字节同源码）：

    100022BF  3D 00000100      cmp eax, 0x10000
    100022C4  0F 86 80 00 00 00   jbe 0x1000234A     ; ⇒ EAX 是高度值(≈0..2080) ⇒ 恒跳 passthrough

⇒ **「雷达灰化分支进入次数」增长（护栏 1/2 通过，与真机一致）而「雷达灰化像素数」恒 0** 的直接原因，就是这条恒真早退。真机日志（ra2youli/ra2render.log）原文抽样：
  16303 → 16340 → 16362 → … → 17284（单调增长），同段落「雷达灰化像素数: 0」。（ZCode 实测，本轮仅引用其原文）

### 2.4 F2：引擎减暗体与驱动位（[实证]）

    0x00655D62  39 2D 50 35 B7 00   cmp dword [0xB73550],ebp   ; 第 1 判据：hWnd
    0x00655D68  74 18                je  0x00655D82             ; hWnd==0 -> [esp+0x13]=0
    0x00655D74  E8 27 07 F3 FF       call 0x005864A0            ; 第 2 判据：引擎逐格减暗判定
    0x00655D7B  C6 44 24 13 01       mov byte [esp+0x13],1      ; 雾中 ⇒ 减暗
    0x00655D82  C6 44 24 13 00       mov byte [esp+0x13],0      ; 亮
    0x00655D87  8B 47 04 89 6C 24 14 mov eax,[edi+4] ; mov [esp+0x14],ebp   ← 【新增挂钩 H3（7B）】
    0x00655D8E  8D 04 80             lea eax,[eax+eax*4]         ← H3 跳板回跳点
    0x00655E7E  8A 44 24 13         mov al,[esp+0x13]           ; 判定位消费点
    0x00655E8A  8B 8E 20 12 00 00    mov ecx,[esi+0x1220]        ; 源表面（BSurface 地形缓存）
    0x00655EE2  8B 86 1C 12 00 00    mov eax,[esi+0x121C]        ; 目标表面（工作表面）
    0x00655EEE/0x655F0A/0x655F20   D1 ED / D1 EB / D1 EA      ; 三通道各 shr 1（像素精确 50% 减暗）
    0x00655F40  FF 50 24              call dword ptr [eax+0x24]   ; Set_Pixel(pt,color)

引擎逐格谓词语义（YRpp 明确定义，[实证]）：

    0x00586360 = MapClass::IsLocationShrouded(const CoordStruct&)   （YRpp/MapClass.h:211）
       0x005863F2  F6 81 2C 01 00 00 08   test byte [ecx+0x12C],8   ; cf_Explored（已探索位）
       0x005863F9 / 0x00586481  jne -> 返回 false（非黑雾）；否则返回 true
    0x005864A0 = 引擎雷达减暗判定（Plot_Cell 0x655D74 直接调用）
       0x0058652E  8B 88 3C 01 00 00      mov ecx,[eax+0x13C] ; test ecx,ecx ; >0 -> 返回 true = 减暗

⇒ 引擎减暗体存在且像素精确，且其判定位 [esp+0x13] 是**唯一**驱动入口 ⇒ 按我方三态谓词改写该位即可复用全部原生实现（不自绘）。

---

## [3] 勘误（对既有文档/结论的更正）

| 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|
| docs/re/cellclass_offsets_evidence.md:22-25（及 ra2render.h 注释「EAX 即返回的合法 CellClass*」、docs/re/radar_hook_routeA_spec.md、docs/re/routeA_implementation_audit.md:39、out/re_work/da4/claims.txt:9、out/re_work/da1/claims.txt:3） | 0x00655D38 处 EAX = MapClass::GetCellAt 返回的 CellClass* | EAX = **MapClass::GetCellFloorHeight（0x578080）返回的格面高度 int**，写回 CoordStruct.Z | YRpp/MapClass.h:282/417 明确定义 0x578080 为 int 返回值；0x578080 以 ret 4 返回，且 0x655D2F 预置 Z=0 后由 0x655D38 覆盖 | **影响产品决策**：S3 FAIL 根因即此；所有依赖「0x655D38 有 pCell」的后续分析作废 |
| docs/re/radar_fix_report.md / RE_COORDINATION.md:1420 中「0x655D62 cmp [0xB73550],0 ⇒ 该全局疑为迷雾总开关」 | 疑为迷雾总开关 | 是 **Game::hWnd**（窗口句柄）；引擎此处语义 = 「有渲染窗口」 | 唯 2 写点均来自 CreateWindowExA；77 读点全部当 Win32 句柄 | **影响产品决策**：F2 分支 ① 否决（不可写） |
| docs/re/radar_minimap_dots.md:146「0xB73550 为 0 时跳过迷雾检测（编辑器/特殊模式）」 | 编辑器/特殊模式开关 | 为 0 = 主窗口尚未创建（启动早期），与编辑器无关 | 同上级；窗口创建即非 0（菜单亦然） | 文档口径更正 |
| docs/re/shroud_click_interaction.md:15/35/261（已正确记为 HWND） | 游戏主窗口句柄 HWND | 与定谳一致，无需改 | —— | 无 |
| ra2render/ra2render.h 中 OFF_SCENARIO_ISLOADING 0x3598 注释「ScenarioClass::IsLoadingScreen」 | IsLoadingScreen | **误标**：ScenarioClass+0x3598 语义未定（YRpp 记 DWORD unknown_3598；全 exe 为字节粒度门控；真机 = 0x92）；已从护栏谓词中删除 | YRpp/ScenarioClass.h:224 + exe 12 处访问形态 + ZCode 实测 | **影响产品决策**：原护栏可静默拦死灰化（P0 悬项已清） |
| docs/RE_COORDINATION.md:1420「0x655C50–0x656100 内对 +0x12C 的访问数 = 0 ⇒ 旧代理判据是自造」 | 结论方向正确 | 补强：该区间**根本没有 pCell**（Plot_Cell 全程只用 CoordStruct 坐标 + 0x586360/0x5864A0 两个谓词），故 +0x12C 访问数为 0 是必然，不是「引擎不用」 | 本轮全函数反汇编 | 文档口径更正（结论不变） |
| docs/re/radar_fix2_report.md:288（本文件 §8 符号表 s_radarGuardRejects 行）**【RADAR-ERRATA2 就地订正】** | s_radarGuardRejects[0..5] 0x102E19E0+（隐含 0x102E19E0 + 4n） | **s_radarGuardRejects[0..7] = 0x102E1A04 + 4n**（[0..5] 在用：0x102E1A04 / 0x102E1A08 / 0x102E1A0C / 0x102E1A10 / 0x102E1A14 / 0x102E1A18；[6]/[7] = 0x102E1A1C / 0x102E1A20 未被遥测引用） | RADAR-ERRATA2 独立反汇编部署 DLL（17/17 与 ZCode 真值一致）：旧式使字段 J4/J5/J6 与计数器 L/K/A 同址，且旧基址在 DLL 内零引用（字节模式 E0 19 2E 10 出现 0 次）；mode1/mode2 同 tick 实测「未探索 12272 vs K 7201」同址两值 | **影响做内存观察/断点的人**（会跟错地址）；不影响已交付 DLL 行为（纯文档错） |

- **RADAR-ERRATA2 口径精确化**：任务卡对旧表的证伪叙述「mode0 实测 J2=20781 而 K=0 ⇒ 同址两值」在旧式下并不同址（旧 J2 = 0x102E19E4 ≠ K = 0x102E19F0）；严谨叙述见 §8 勘误块「口径附注」——同址碰撞对是 J4↔L、J5↔K、J6↔A。
- **RADAR-ERRATA2 写作用域外残留**：out/re_work/radar_fix2/rep_p4.md:45（组装本报告用的旧片段）仍带旧式 0x102E19E0+；该文件不在本任务写作用域，是否同步由 Lead 决定（交付文档 = 本文件，已订正）。

（注：本节只产出订正清单，未修改任何他人文档 —— 见 [5] 写作用域。）

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可直接执行） | 阻塞级 |
|---|---|---|---|---|
| 1 | s_visionGrid 从未盖章的真实根因 | 静态可排除项已排除（Items/Count 偏移、帧守卫、pPlayer 判据），剩余候选是运行期数据（对象数组内容、健康过滤读的 pObj+0x6C 偏移语义），静态不可判定 | 跑一轮并读新遥测行（[ra2render-telemetry-radar] 三态谓词样本: 求解成功 X / 失败 Y (已探索 E, 直视圈内 V)）。若 V 恒 0 且 E 正常 ⇒ 网格盖章链断；再在 Cheat Engine 对 s_visionGrid 基址下内存写断点（基址见 [8] 符号表） | P1 |
| 2 | 引擎自身减暗判定（0x5864A0 的 [cell+0x13C]>0）是否为「explored && !visible」 | 需定位 [cell+0x13C] 的维护者（写点未定位；该字段 YRpp 无正式命名） | 一轮真机看「引擎自身判定为暗」计数：>0 ⇒ 原生已在工作；=0 且「原生减暗路径命中次数」>0 ⇒ 由我方驱动生效 | P1 |
| 3 | 是否还有其它「静默早退」入口 | 需要运行期观测 | 已加 6 个早退分桶计数（总开关/护栏/表面/谓词/未探索/直视），一轮真机即可全清 | P2 |
| 4 | EnableMinimapFog 出厂默认是否放开为 1 | 需 ZC-3 真机验收结论 | 见 [9] 待裁决 | P0（闸门） |
| 5 | 减暗驱动是否与联机锁步相关 | 需 MP 对拍 | 联机侧 s_minimapFogGate 被 MpActive 强制 0 ⇒ 本特性在联机不生效；若后续放开需 MP 门控矩阵 + 真机对拍 | P1 |

---

## [5] 写作用域合规声明

改动文件清单（本轮实际写入）：

| 路径 | 字节数 | 起止时间 | 说明 |
|---|---|---|---|
| ra2render/blitter_hooks.cpp | 106,068 | 14:25:26 | 重写雷达段（H1 代理改薄壳 + 新增 H3 代理/两个 C++ 体/新遥测/档位 3）+ 遥测行 + 配置默认 |
| ra2render/ra2render.h | 15,617 | 14:24:50 / 14:31 | 新增 ADDR_RADAR_NATIVE_DECIDE/RESUME、ADDR_GAME_HWND、RADAR_FOG_GUARD_NATIVE |
| ra2render/ra2render.ini | 4,902 | 14:28:16 | RadarFogGuardMode=3 + 档位说明与 F3① 勘误 |
| ra2youli/ra2render.ini | 4,902 | 14:28:29 | 与上同步（字节一致） |
| ra2render/build.bat | 1,256 | 14:27:50 | ra2loader.exe 部署改为可选（默认不覆盖） |
| ra2render/ra2render.dll | 134,144 | 14:31:53 | 重建产物（同时被 build.bat 部署） |
| ra2youli/ra2render.dll | 134,144 | 14:31:53 | 部署（与 ra2render/ 副本 MD5 一致 961E4B6C…） |
| docs/re/radar_fix2_report.md | 本文件 | 新建 | 交付报告 |
| out/re_work/radar_fix2/** | 见 [8] | 新建 | 备份、日志、反汇编证据、claims、诊断脚本 |

未触碰清单（只读/未写）：
- ra2youli/gamemd.exe（MD5 4f37486e5b0dbe2ae5f45aeee0f98367，本轮两次复算一致）—— 未写 exe；
- 任何 .mix/.map/.sav；ra2forge/**；mcp/**；ra2opt/**；docs/RE_COORDINATION.md；docs/re/AGENT_DELIVERY_FORMAT.md；docs/re/anchor_claims.txt；其它 docs；
- ra2youli/ra2loader.exe（未被本轮构建覆盖，见 build_log.txt 的 skip 行）。

目标二进制哈希（证明只读）：

    gamemd.exe  MD5 4f37486e5b0dbe2ae5f45aeee0f98367  4,825,360 B
    旧部署 DLL  MD5 EA7D988752FD48F26A8A04452D64E2FE  132,608 B  （备份 out/re_work/radar_fix2/ra2render.dll.bak-pre-fix2）
    新部署 DLL  MD5 961E4B6C883E4D18C48B293CF5D53122  134,144 B

---

## [6] 门禁实跑输出（原文粘贴）

### 6.1 python tools\verify_anchors.py

    ===================================================================================================================
      RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
    ===================================================================================================================
    目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
    断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
    反汇编器 : Capstone x86-32 引擎已就绪
    -------------------------------------------------------------------------------------------------------------------
    [基线完整性审计]
      [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
      [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
      [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 (@ VA 0xb93000) -> 严禁写入/注入原则确立
    -------------------------------------------------------------------------------------------------------------------
    回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
    ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
    ===================================================================================================================

（完整输出：out/re_work/radar_fix2/verify_anchors_out.txt）

### 6.2 python tools\audit_bytes.py out\re_work\radar_fix2\radar_fix2_claims.txt

    VA         期望字节                       实际字节                   判定     标签/上下文
    0x655c50   a1 4c 3d a8 00             a1 4c 3d a8 00         OK     Plot_Cell 入口: mov eax,[0x00A83D4C]
    0x655d33   e8 48 23 f2 ff             e8 48 23 f2 ff         OK     call 0x00578080 = MapClass::GetCellFloorHeight
    0x655d38   89 44 24 28 a1 50 35 b7 00 89 44 24 28 a1 50 35 b7 00 OK   路线 A 挂钩点 9 字节区
    0x655d62   39 2d 50 35 b7 00          39 2d 50 35 b7 00      OK     cmp dword [0x00B73550],ebp
    0x655d7b   c6 44 24 13 01             c6 44 24 13 01         OK     mov byte [esp+0x13],1（雾中→减暗）
    0x655d87   8b 47 04 89 6c 24 14       8b 47 04 89 6c 24 14   OK     【新增挂钩 H3】7 字节区
    0x655eee   d1 ed                      d1 ed                  OK     shr ebp,1（R 通道减半）
    0x5863f2   f6 81 2c 01 00 00 08       f6 81 2c 01 00 00 08   OK     test byte [ecx+0x12C],8 = cf_Explored
    0x5780f6   c2 04 00                   c2 04 00               OK     GetCellFloorHeight ret 4
    0x777cd6   a3 50 35 b7 00             a3 50 35 b7 00         OK     [唯一写点 1] mov [0x00B73550],eax
    0x65719a   e8 91 93 00 00             e8 91 93 00 00         OK     [H2 挂钩点] call 0x00660530
    （此处为节选；完整 41 行见 out/re_work/radar_fix2/audit_bytes_out.txt）
    --------------------------------------------------------------------------------------------------------------
    合计 41 条：OK=41  MISMATCH/NOREAD=0

---

## [7] 风险与红线提示

| 红线 | 是否触及 | 说明与门控 |
|---|---|---|
| ① 同步语义/命令序 | **不触及** | 挂钩位于渲染侧（RadarClass/MapClass 重绘路径，非模拟 tick）；不写引擎状态量、不改命令序；H3 只写本函数栈帧内一个字节 [esp+0x13]（0x655E7E 的消费位）。且联机模式下 s_minimapFogGate 被 MpActive 强制 0（GetEffectiveMinimapFog），特性整体不生效 |
| ② 随机数消费序 | **不触及** | 不调用任何 RNG；新增调用仅 0x586360 / 0x5864A0（纯网格查询，无副作用除了无效坐标时写 InvalidCell.MapCoords，与引擎自身在同函数内已做的写法同类） |
| ③ 存档结构 | **不触及** | 不新增/修改任何存档字段；不写 Scenario/Session/CellClass 持久字段（自绘档只写雷达表面像素） |
| ④ 渲染像素等价性 | **触及（已论证）** | 引擎减暗体 = 三通道各 shr 1（0x655EEE/0x655F0A/0x655F20）；自绘公式 (c>>1)&0x7BEF 经代数化简与之**逐通道等价**（附录 A.2）。H3 档不改像素算法，只改引擎自己的判定位 ⇒ 像素由引擎原版代码产生，等价性最强 |
| ⑤ 写 0x00B73550（HWND） | **明确禁止** | 本轮代码对该全局**只读**：产物反汇编确认 .text 中仅 1 处 cmp dword [0xb73550],0（0x10004437），无任何写指令 |
| ⑥ 越界写入 | **已消除一个既往越界副作用** | build.bat 原无条件 copy ra2loader.exe → ra2youli/，本轮改为可选（默认 skip）；本轮构建日志可见 skip 行、仅 1 file(s) copied |

⇒ **需要 MP 门控矩阵/真机对拍验收**：本改动触及「渲染像素等价性」这一条，且雷达属渲染侧，故正式放行前需 ZC-3 真机三档 A/B + （若未来放开联机）MP 对拍。禁止宣称「零风险 / 零 Desync」。

---

## [8] 交付物清单

| 类型 | 路径 | 规模/条数 |
|---|---|---|
| 交付文档 | docs/re/radar_fix2_report.md | 本文件（10 节骨架 + 2 附录） |
| 附带步骤 | out/re_work/radar_fix2/zcode_retest_steps.md | ZC-3 真机复验步骤（三档 A/B + 判据表） |
| 断言 | out/re_work/radar_fix2/radar_fix2_claims.txt | 41 条（audit_bytes.py 全 OK） |
| 门禁输出 | out/re_work/radar_fix2/verify_anchors_out.txt | 323/323 PASS 原文 |
| 门禁输出 | out/re_work/radar_fix2/audit_bytes_out.txt | 41/41 OK 原文 |
| 反汇编证据 | out/re_work/radar_fix2/artifact_verify.txt | 产物级反汇编（H1/H3 代理、档位分派、hWnd 只读门、立即数/字符串清单） |
| 反汇编证据 | out/re_work/radar_fix2/e1_flagloads.txt、e2_fogpred.txt、artifact_verify_prev.txt | 0x586360/0x5864A0 全函数、0x12C/0x140 位操作扫描、旧产物代理反汇编 |
| 备份 | out/re_work/radar_fix2/ra2render.dll.bak-pre-fix2（132,608 B，MD5 EA7D9887…）、ra2render.ini.bak-pre-fix2、ra2render.dll.build-pre-fix2 | 3 件 |
| 编译日志 | out/re_work/radar_fix2/build_log.txt | 0 warning / 0 error，ALL BUILDS FINISHED SUCCESSFULLY |
| 诊断脚本 | out/re_work/radar_fix2/*.py（rd.py, d3_xref.py, d5_classify.py, d9_flags2.py, e2/e3/e5/e8, f4_verify.py, splice.py） | 12 个 |
| 源码改动 | ra2render/blitter_hooks.cpp、ra2render/ra2render.h、ra2render/build.bat、ra2render/ra2render.ini、ra2youli/ra2render.ini、ra2render/ra2render.dll、ra2youli/ra2render.dll | 7 件 |

关键新遥测符号（.data 地址，便于真机内存观察）：

    s_nativeDarkenHits        0x102E19F4   原生减暗路径命中次数（最终 flag=1）
    s_nativeEngineDarkHits    0x102E19F8   引擎自身判定为暗
    s_nativeForcedDarkHits    0x102E19FC   我方谓词强制为暗
    s_nativeOverrideDeltas    0x102E1A00   覆盖差（我方≠引擎）
    s_radarProbeOk            0x102E1A24   谓词求解成功
    s_radarProbeFail          0x102E1A28   谓词求解失败
    s_radarProbeExplored      0x102E1A2C   样本中已探索
    s_radarProbeVisible       0x102E1A30   样本中直视圈内
    s_radarHwndZero           0x102E1A34   hWnd==0 放弃覆盖
    s_minimapFogPixels        0x102E19EC   自绘灰化像素数（档 0/1/2）
    s_minimapFogBranchHits    0x102E19F0   自绘灰化分支进入次数
    s_radarGuardRejects[0..5] 0x102E19E0+   早退分桶：总开关/护栏/表面/谓词/未探索/直视   【原记 · 该地址已被 RADAR-ERRATA2 证伪，见下方勘误块；原值保留未删】
    s_radarGuardRejects[0..7] 0x102E1A04+   ★订正★ 早退分桶（声明为 8 槽数组，[0..5] 在用）= 0x102E1A04 + 4n ⇒ 0x102E1A04 / 0x102E1A08 / 0x102E1A0C / 0x102E1A10 / 0x102E1A14 / 0x102E1A18（[6]/[7] = 0x102E1A1C / 0x102E1A20 未被遥测引用）

> **【RADAR-ERRATA2 勘误块 · 2026-09-27】§8 符号表 s_radarGuardRejects 行地址订正（就地，原记一字未删）**
>
> **原记（保留）**：s_radarGuardRejects[0..5] ~~0x102E19E0+~~（隐含 0x102E19E0 + 4n；早退分桶：总开关/护栏/表面/谓词/未探索/直视）
> **正解**：s_radarGuardRejects[0..5] = 0x102E1A04 + 4n ⇒ 0x102E1A04 / 0x102E1A08 / 0x102E1A0C / 0x102E1A10 / 0x102E1A14 / 0x102E1A18（4 字节步进、互不重叠）。
> 该数组**声明为 8 槽**（ra2render/blitter_hooks.cpp:61：uint32_t s_radarGuardRejects[8]），故 [6]/[7] = 0x102E1A1C / 0x102E1A20 存在但未被任何遥测字段引用。
>
> **证伪逻辑（旧表为何不可能成立）**
> 1. **算术重叠**：按旧式 0x102E19E0+4n，n=3→0x102E19EC（= L 灰化像素数）、n=4→0x102E19F0（= K 灰化分支进入次数）、n=5→0x102E19F4（= A 原生减暗路径命中次数）⇒ 旧表把字段 J4/J5/J6 与计数器 L/K/A 放在同一地址。
> 2. **运行期同址两值（决定性）**：ZC-3 mode1 同一次 2 秒遥测里「未探索(J5) = 12272」而「灰化分支进入次数 K = 7201」——旧表称二者同址 0x102E19F0；mode2 同 tick 亦为「12474 vs 7205」。同一地址不可能同刻两值 ⇒ 旧表自相矛盾。（另两组同样矛盾：直视圈内 1252/1244 vs A = 0 @旧址 0x102E19F4；谓词失败 0 vs L = 7201/7205 @旧址 0x102E19EC。）
> 3. **代码零引用**：旧基址 0x102E19E0（小端字节模式 E0 19 2E 10）在部署 DLL 中**出现 0 次**（.text 亦 0 次）；而 17 个真计数器各有 2–4 处代码引用。mode0 实测「护栏拦截 = 20781」必须落在真址 0x102E1A08（.text 引用 2 次）；若落在旧址 0x102E19E4，则没有任何指令会去写它。
> ⚠ **口径附注（对勘误任务卡表述的精确化）**：任务卡所述「mode0 实测 J2 = 20781 而 K = 0 ⇒ 同一地址不可能同时是两个值」——在旧式下 J2 = 0x102E19E4 与 K = 0x102E19F0 **并不同址**，故该句单独不构成同址矛盾；真正的同址碰撞对是 **J4↔L、J5↔K、J6↔A**，其运行期矛盾由 mode1/mode2 数据给出（上条第 2 点）。结论（旧表地址错误）不受影响。
>
> **独立复核口径**（RADAR-ERRATA2 本会话自写 capstone 脚本，未把他方数字当输入）：对部署 DLL 的遥测格式化函数（真身 0x100014D0–0x10001668，ZCode 引的 0x10001540–0x10001668 只覆盖中后段）取出三条格式串（0x10018B20 常规行 12 字段 / 0x10018C50 雷达行 14 字段 / 0x10018DA8 hWnd 行 1 字段）各自调用点的压参区，做**槽位闭合校验**（%u = 1 槽、%llu 与 %.1f = 2 槽）：22=22、14=14、1=1 全 CLOSED；再按 __cdecl 右→左压参**反序对齐字段序**逐字段钉死地址。**与 ZCode ZC-3 真值逐条一致 17/17（地址差异 0、push 锚点差异 0）。**
>
> 证据：out/re_work/radar_errata2/disasm_counter_addr.txt（逐指令压参 dump + 槽位闭合 + 否证段 + 源码序对照）、addr_compare.md（三方对照表）、xref_sites.txt（每个计数器在 .text 的全部引用点）、claims.txt + audit_bytes_out.txt（字节断言 25/25 OK）、runtime_corroboration.txt（运行期佐证）、grep_selfcheck.txt（全文自查）、verify_anchors_out.txt（323/323 PASS）。
> ⚠ 计数器槽位本身位于 .data ZeroInit 虚拟区（文件数据止于 VA 0x10021A00）⇒ **那里没有静态字节可断言**；故 claims.txt 的断言对象是 .text 中引用该槽位的**压参指令原始字节**（FF 35 <disp32>），槽位地址即该指令的操作数 disp32。

---

## [9] 待裁决项

| # | 分叉 | 建议方案 | 理由 |
|---|---|---|---|
| 1 | EnableMinimapFog 出厂默认 0 还是 1 | **维持 0 出厂；ZC-3 PASS 后由 Lead 决定翻 1** | 该项从未过真机验收；本轮虽把风险面缩小（只写栈帧一个字节、复用引擎减暗体），但仍需 ZC-3 结论 |
| 2 | RadarFogGuardMode 默认档 | **已设 3（原生减暗驱动）** | 自绘路径已被证不可达（EAX 误认），且像素等价性由引擎自身保证；0/1/2 保留供 A/B |
| 3 | 若 ZC-3 显示「引擎自身判定为暗」计数长期为 0 | 说明原版雷达减暗在其实际数据链下从未触发；此时档 3（我方驱动）即为唯一生效路径，建议保留并考虑把 EnableMinimapFog 翻 1 | 该计数是本轮新增的关键判据（见步骤文档判据表） |
| 4 | 是否回收自绘路径（彻底删除档 0/1/2 代码） | **暂不删**，保留为 A/B 与回归对照；待 ZC-3 双档像素一致后再评估瘦身 | 任务卡 F2 明确要求「保留为 RadarFogGuardMode 的一档以便 A/B」 |
| 5 | ScenarioClass+0x3598 的最终语义是否继续追查 | 建议降级为 P2（已从关键路径移除）；若要追，下一步是对 0x48D001/0x598xxx 调用链做写点定位 | 已不构成产品风险 |

---

## 附录 A：本轮实现细节

### A.1 代码改动（ra2render/blitter_hooks.cpp 雷达段整体重写）

1. **H1（0x00655D38，9B，挂钩点未变）**：代理由「内联汇编自绘全流程」改为**薄壳**：
   保存 EAX → 填静态上下文 RadarHookCtx{radarThis, pt, floorHeight, &CoordStruct} → call RadarHook_SelfDrawn（C++）→ 还原 EAX
   → 若 C++ 侧已落像素则走函数尾声（pop edi/esi/ebp/ebx; add esp,0x30; ret 4），否则 jmp 跳板 0x00655D41。
2. **H3（0x00655D87，7B，新增）**：填上下文（含 pFlag = &[esp+0x13]）→ call RadarHook_NativeDecide（C++）→ jmp 跳板（回放 7 字节原指令后跳 0x00655D8E）。
3. **C++ 体 RadarHook_SelfDrawn**（档 0/1/2 自绘）：护栏 3 档 + 雷达双表面校验 + 三态谓词求解 + （c>>1)&0x7BEF + Get/Set_Pixel；每个早退点各 +1 分桶计数。
4. **C++ 体 RadarHook_NativeDecide**（档 3，默认）：读引擎判定位并计数 → 门控/档位判定 → **只读 hWnd 门** → 三态谓词求解 → 改写 [esp+0x13] → 计数。
5. **三态谓词 RadarResolveCellState**：explored = !MapClass::IsLocationShrouded(0x586360, &CoordStruct)；inVision = (s_visionGrid[cellY*512+cellX] == s_visionToken)（cellX/Y 由 CoordStruct.X/Y >> 8，与本插件网格盖章约定一致）。
6. 配置：RadarFogGuardMode 值域 0..3，默认 3（API 默认与 ini 默认同改）；ini 两份同步。
7. build.bat：ra2loader.exe 部署可选（RA2RENDER_DEPLOY_LOADER=1 才部署）。

### A.2 自绘公式与引擎减暗体的逐通道等价性（代数证明）

RGB565 布局：bit15-11 = R(5)，bit10-5 = G(6)，bit4-0 = B(5)。

引擎（0x655E8A–0x655F43）：按像素格式位移表（0x8A0DD0..0x8A0DE4）分别取出 R/G/B，各自 shr 1，再按位拼回：

    R' = floor(R/2) << 11 ;  G' = floor(G/2) << 5 ;  B' = floor(B/2)

自绘：c' = (c >> 1) & 0x7BEF，其中 0x7BEF = 0111 1011 1110 1111b（bit15/bit10/bit4 被清零）。

    c>>1 后：原 R4..R0 落到 bit14..bit10 → 掩码保留 bit14..bit11，清 bit10 ⇒ R' = R4R3R2R1 = floor(R/2) ✓
             原 G5..G0 落到 bit9..bit4  → 掩码保留 bit9..bit5，清 bit4  ⇒ G' = G5G4G3G2G1 = floor(G/2) ✓
             原 B4..B0 落到 bit3..bit-1 → 掩码保留 bit3..bit0（B0 自然丢失）   ⇒ B' = floor(B/2) ✓

⇒ 两者**逐通道完全一致**（同一源像素：均取自 [radarThis+0x1220] 的 Get_Pixel(pt)）。故 A/B 两档若像素计数同时 >0，应观察到**逐像素相同**的灰化结果；这也解释了为何「像素等价性」从来不是 S3 的问题，问题只是**可达性**。

### A.3 为何选 0x00655D87 而不是 0x00655D62 做驱动点

- 0x00655D62 是 6 字节 cmp [0xB73550],ebp，改写它必须**跳过**引擎自身的 hWnd 门与 0x5864A0 调用，并自行保持 ZF 供 0x00655D68 的 je 使用 —— 契约面更大。
- 0x00655D87 恰好 7 字节（mov eax,[edi+4] + mov [esp+0x14],ebp），跳板回放可**逐位复原**原指令；代理在引擎判定之后**只覆盖一个字节**，门控关闭时行为与未挂钩逐位一致（失败可回滚到 0 成本）。
- 该点之后 EAX/ECX/EDX 均被 0x655D8E 起的代码重建，寄存器契约最窄（只需保 ESI/EDI/EBP/EBX，由 __cdecl 被调方自动保证）。

---

## 附录 B：ZC-3 真机复验步骤（摘要；完整版见 out/re_work/radar_fix2/zcode_retest_steps.md）

1. 备份现场：copy ra2youli\ra2render.dll 与 ra2render.ini 到 out/re_work/radar_fix2/zc3_backup\（部署件 MD5 应为 961E4B6C883E4D18C48B293CF5D53122）。
2. 置 ra2youli\ra2render.ini：【FogOfWar】EnableMinimapFog=1（RadarFogGuardMode 保持 3）。
3. 启动战役（任意一张有迷雾的官方战役），进入局内后清空/记录 ra2youli\ra2render.log 的起点。
4. 观察新增遥测行（每 2 秒）：

    [ra2render-telemetry-radar] 原生减暗路径命中次数: A (引擎自身判定为暗: B, 我方谓词强制为暗: C, 覆盖差: D) | 三态谓词样本: 求解成功 E / 失败 F (已探索 G, 直视圈内 H) | 自绘早退桶: ...
    [ra2render-telemetry-radar] 引擎 hWnd 门放弃覆盖次数: I

5. 判据（一轮即可定走哪条路）：
   - A 单调增长 ⇒ 引擎减暗体确实在跑（雷达迷雾生效）；B > 0 ⇒ 引擎自身谓词也认为该格该暗（原生能力存在）；B = 0 且 C > 0 ⇒ 是本轮驱动让它生效的。
   - H = 0 且 G > 0 ⇒ 我方直视网格可疑（s_visionGrid 盖章链断，见 [4]#1）⇒ 会过度灰化（含自家基地），此为验收判据之一。
   - I > 0 ⇒ 引擎 hWnd 门曾被触发（正常只在极早期出现）。
6. 三档 A/B：分别置 RadarFogGuardMode=1（自绘新谓词档）、2（自绘无护栏档）、3（原生驱动档），各跑同一局面 3-5 分钟：
   - 档 1/2 看「雷达灰化分支进入次数」「雷达灰化像素数」均单调增长；
   - 档 3 看「原生减暗路径命中次数」单调增长且「雷达灰化像素数」停止增长（因不自绘）；
   - 三档的雷达观感应一致（附录 A.2 的等价性）；档 0 作为旧行为对照应仍为 0 像素。
7. 回传：日志文件 + 三档遥测行原文 + 观感结论（是否与被灰化区域一致、自家基地是否被误灰）。

---
（报告完）

## 附录 C：对「0x3598 悬项」在旧产物中的存在性复核（补 [3] 勘误）

旧部署产物（备份 MD5 EA7D9887…，即 ZC-2 所测那一版）反汇编（out/re_work/radar_fix2/artifact_verify_prev.txt）证明：源码中的 0x3598 判据**确实被编译进去**了：

    1000228B  80 BA 98 35 00 00 00    cmp byte ptr [edx + 0x3598], 0
    10002292  75 0F                   jne 0x100022A3              ; 非 0 ⇒ guard_new_fail ⇒ passthrough
    （mode 1 新谓词档路径）

但 ZC-2 的实测同时显示「雷达灰化分支进入次数」单调增长（16303→17284）——按代码，该计数只在 guard_passed 之后自增，故 0x3598 在**那些测量时刻必须为 0**。结合 ZCode 另行测到该字节 = 0x92 的事实，可判定该字段是**运行期会变化**的字节标志（非 0/1 布尔）。

结论（两条并存，不冲突）：
- **确定性死因（已定谳）**：EAX≠pCell ⇒ cmp eax,0x10000/jbe 恒拒 —— 它**必然**导致 S3 FAIL，与 0x3598 取值无关；
- **潜在死因（已移除）**：0x3598 在某些时段为 0x92 ⇒ mode 1 护栏会在那些时段静默拦死灰化 —— 这正是「P0 悬项」的实质风险，本轮已删除该判据（改为雷达双表面有效性）。

---

## 附录 D：遥测计数器地址独立复核与订正（RADAR-ERRATA2 · 2026-09-27）

> 触发：ZCode ZC-3 反查 §8 符号表 s_radarGuardRejects 行地址有误（「J 桶与 K/L/A 重叠」）。本附录是**独立复核**（不抄他人结论）的落地记录。
> 写作用域：本文件 + out/re_work/radar_errata2/**；**未改任何二进制、未启动游戏、未注入**。

### D.1 被测件与复核口径（自证式，可复跑）

被测件：ra2youli/ra2render.dll = 134,144 B / MD5 961E4B6C883E4D18C48B293CF5D53122（ImageBase 0x10000000，全程 open(rb) 只读）。

1. 定位三条遥测格式串（0x10018B20 常规行 / 0x10018C50 雷达行 / 0x10018DA8 hWnd 行）并解析其 % 转换符序列；
2. 在 .text 全文扫描 push imm32 == 格式串 VA，得到三个调用点 0x100015E0 / 0x1000163E / 0x10001654；
3. 自调用点回溯到**上一条 call** 取该调的压参区，抽出 push 槽位；
4. **槽位闭合校验**（必需槽位由格式串字段算：%u=1、%llu/%.1f=2）：常规行 22=22、雷达行 14=14、hWnd 行 1=1 —— 全部 CLOSED；
5. 按 __cdecl 右→左压参**反序对齐字段序**，取每字段的内存操作数 disp32 ⇒ 计数器地址。

反汇编证据全文：out/re_work/radar_errata2/disasm_counter_addr.txt（脚本 re_disasm_counter_addr.py）。

### D.2 订正后的地址表（17 个计数器，全部来自 D.1 的压参序列）

| # | 计数 | 语义 | 符号 | .data VA（独立推导） | 钉死用 push 指令 | 原始字节 |
|---|---|---|---|---|---|---|
| 1 | A | 原生减暗路径命中次数 | s_nativeDarkenHits | `0x102E19F4` | `0x10001638` | `FF35F4192E10` |
| 2 | B | 引擎自身判定为暗 | s_nativeEngineDarkHits | `0x102E19F8` | `0x10001632` | `FF35F8192E10` |
| 3 | C | 我方谓词强制为暗 | s_nativeForcedDarkHits | `0x102E19FC` | `0x1000162C` | `FF35FC192E10` |
| 4 | D | 覆盖差 | s_nativeOverrideDeltas | `0x102E1A00` | `0x10001626` | `FF35001A2E10` |
| 5 | E | 三态谓词求解成功 | s_radarProbeOk | `0x102E1A24` | `0x10001620` | `FF35241A2E10` |
| 6 | F | 三态谓词求解失败 | s_radarProbeFail | `0x102E1A28` | `0x1000161A` | `FF35281A2E10` |
| 7 | G | 样本中已探索 | s_radarProbeExplored | `0x102E1A2C` | `0x10001614` | `FF352C1A2E10` |
| 8 | H | 样本中直视圈内 | s_radarProbeVisible | `0x102E1A30` | `0x1000160E` | `FF35301A2E10` |
| 9 | I | 引擎 hWnd 门放弃覆盖 | s_radarHwndZero | `0x102E1A34` | `0x1000164E` | `FF35341A2E10` |
| 10 | J1 | 早退桶[0] 总开关关闭 | s_radarGuardRejects[0] | `0x102E1A04` | `0x10001608` | `FF35041A2E10` |
| 11 | J2 | 早退桶[1] 护栏拦截 | s_radarGuardRejects[1] | `0x102E1A08` | `0x10001602` | `FF35081A2E10` |
| 12 | J3 | 早退桶[2] 表面无效 | s_radarGuardRejects[2] | `0x102E1A0C` | `0x100015FC` | `FF350C1A2E10` |
| 13 | J4 | 早退桶[3] 谓词失败 | s_radarGuardRejects[3] | `0x102E1A10` | `0x100015F6` | `FF35101A2E10` |
| 14 | J5 | 早退桶[4] 未探索 | s_radarGuardRejects[4] | `0x102E1A14` | `0x100015F0` | `FF35141A2E10` |
| 15 | J6 | 早退桶[5] 直视圈内 | s_radarGuardRejects[5] | `0x102E1A18` | `0x100015EA` | `FF35181A2E10` |
| 16 | K | 自绘灰化分支进入次数 | s_minimapFogBranchHits | `0x102E19F0` | `0x10001572` | `FF35F0192E10` |
| 17 | L | 自绘灰化像素数 | s_minimapFogPixels | `0x102E19EC` | `0x1000156C` | `FF35EC192E10` |

（DLL VA 为真实虚址；「钉死用 push 指令」是该地址在 .text 中的字节级锚点，即 FF 35 <disp32>，disp32 即该计数器地址。）

### D.3 交叉校验（三条互相独立的证据）

1. **与 ZCode ZC-3 产物比对**：17/17 一致（地址差异 0、push 锚点差异 0）——机器比对见 addr_compare.md；
2. **源码声明序**：ra2render/blitter_hooks.cpp:54-66 的 extern "C" 声明序（s_minimapFogPixels, s_minimapFogBranchHits, s_nativeDarkenHits…, s_radarGuardRejects[8], s_radarProbeOk, …）与地址升序**严格一致、稠密无填充**；且「数组基址 0x102E1A04 + 8×4 = 0x102E1A24 = s_radarProbeOk」成立 ⇒ 6 槽假设被否证（若 6 槽该差应为 0x18）；
3. **引用计数**：17 个真计数器在 .text 各有 2–4 处引用（xref_sites.txt 列出指令原文）；旧基址 0x102E19E0 的字节模式在整份 DLL 出现 **0 次**。

### D.4 运行期佐证（数据来源 = ZCode ZC-3 实测产物，本会话只读引用）

| 档位 | A | K | L | J2 护栏拦截 | J5 未探索 | J6 直视圈内 |
|---|---|---|---|---|---|---|
| mode0 | 0 | 0 | 0 | **20781** | 0 | 0 |
| mode1 | 0 | 7201 | 7201 | 0 | 12272 | 1252 |
| mode2 | 0 | 7205 | 7205 | 0 | 12474 | 1244 |
| mode3 | 7804 | 0 | 0 | 0 | 0 | 0 |

（同档一行内的数值取自同一次 2 秒遥测 tick —— 三条遥测行在同一个 2 秒节流门内打印，见 0x100014F6 cmp eax,0x7D0。旧式把这些字段中的三个与 L/K/A 强行同址，mode1/mode2 遂给出同址两值。提取脚本：re_runtime_corroboration.py → runtime_corroboration.txt。）

### D.5 门禁实跑输出（原文粘贴）

    ===================================================================================================================
      RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
    ===================================================================================================================
    目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
    断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
    反汇编器 : Capstone x86-32 引擎已就绪
    -------------------------------------------------------------------------------------------------------------------
    [基线完整性审计]
      [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
      [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
      [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
    -------------------------------------------------------------------------------------------------------------------
    回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
    ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
    ===================================================================================================================

    python tools\audit_bytes.py out\re_work\radar_errata2\claims.txt --exe ra2youli\ra2render.dll
    （25 条字节断言，对象 = .text 压参指令）
    ----------------------------------------------------------
    合计 25 条：OK=25  MISMATCH/NOREAD=0

口径说明：audit_bytes.py 的段映射基准硬编码为 IMAGE_BASE=0x400000（面向 gamemd.exe），故 claims.txt 左侧数值 = DLL 真实 VA − 0x10000000 + 0x400000，真实 VA 写在注释里；计数器 .data 槽位在 ZeroInit 虚拟区（无文件字节）⇒ 断言对象取 .text 中的压参指令。

### D.6 交付物（out/re_work/radar_errata2/）

| 文件 | 内容 |
|---|---|
| re_disasm_counter_addr.py + disasm_counter_addr.txt | 独立反汇编脚本与全量证据（段表/ZeroInit 边界、三条格式串、三个调用点压参序列逐指令 dump、槽位闭合、地址表、否证段、函数边界与源码序对照） |
| re_addr_consistency.py + addr_compare.md + xref_sites.txt + counter_addr_indep.json | 与 ZCode 真值的机器比对、三方对照表、17 个计数器的 .text 引用点、机器可读地址表 |
| re_runtime_corroboration.py + runtime_corroboration.txt | 运行期佐证（引用 ZCode ZC-3 实测产物） |
| claims.txt + audit_bytes_out.txt | 25 条字节断言与 audit_bytes.py 原文输出（25/25 OK） |
| verify_anchors_out.txt | 323/323 PASS 原文 |
| grep_selfcheck.txt | F3 全文自查（旧 J 桶地址在文档中的其他引用逐处处置） |
| README.md | 目录导读与复现命令 |

（附录 D 完 · RADAR-ERRATA2）
