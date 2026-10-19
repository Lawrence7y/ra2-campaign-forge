# RADAR-FIX 交付报告（Q3① 小地图灰化护栏 P0 + 重复 [Logic] 节 P1）

> 任务卡：RADAR-FIX　|　执行方：Antigravity(agy) 通道 / 本次由 DSH 子代理执行
> 工作区：D:\Project\ra2-campaign-forge（Windows）　|　基线：ra2youli/gamemd.exe（MD5 4F37486E5B0DBE2AE5F45AEEE0F98367）【只读，未改】
> 本报告为**交付文档**（细节承载）；执行方回执正文另附（≤4 页）。

---

## 【勘误块 · RADAR-ERRATA · 2026-09-27】（保留原文，本块为就地订正）

> 本报告成文于 RADAR-FIX 批次；下列 3 类误述已由 **RADAR-FIX2 定谳 + Lead 独立反汇编复核**推翻。**原正文一字未删**，仅在本块与相应行加注【原记 · 已勘误】。
>
> **E5① `0x00B73550` 不是「迷雾总开关」，而是 `Game::hWnd`（主窗口句柄 HWND）。**
> - 【原记 · 已勘误】本批之后的裁决记录（`docs/RE_COORDINATION.md:1420-1421`，**不在本次写作用域**）曾把 `0x655D62 cmp dword [0xB73550],0` 记为「该全局疑为迷雾总开关」，并据此评估「写它让引擎原生减暗生效」的分支 ①。
> - **正解**：`0xB73550` = `Game::hWnd`（`YRpp/Unsorted.h:17` / `ref/yrpp/Unsorted.h:17`：`reference<HWND, 0xB73550u> const hWnd{}`）。全 exe 仅 **2 个写点** `0x777CD6`/`0x777D7E`（均 `A3 50 35 B7 00 mov [0x00B73550],eax`，紧随 `CreateWindowExA` 返回值），**77 处读点全部当 Win32 句柄**（`SetFocus`/`SetCapture`/`ReleaseCapture`/`ShowWindow`/`GetClientRect`/…）。引擎 `Plot_Cell` 中 `0x00655D62 = 39 2D 50 35 B7 00` 的语义 = 「主窗口是否已创建」（游戏内恒真，菜单亦非 0）。
> - ⇒ **分支 ① 已被否决**：写它会污染 70+ 处 Win32 调用，**禁止写入**；本轮及后续对该全局**只读**。
> - 字节证据：`0x00777CD6 = A3 50 35 B7 00`、`0x00777D7E = A3 50 35 B7 00`、`0x00655D62 = 39 2D 50 35 B7 00`（见 `out/re_work/radar_errata/claims.txt`）。
>
> **E5② `ScenarioClass+0x3598` 不是 `IsLoadingScreen`。**
> - 【原记 · 已勘误】本报告 §2.2 标题与结论（第 110/131 行）把 `+0x3598` 命名为 `IsLoadingScreen`（自标「[实证] 读点 + [推演] 命名」），§2.8 反汇编注释（第 225 行 `; IsLoadingScreen`）沿用该名。
> - **正解**：YRpp 仅记 `DWORD unknown_3598`（`YRpp/ScenarioClass.h:224`），**语义未定**；全 exe 12 处访问**均为字节粒度门控**（`cmp byte [scn+0x3598],0`，如 `0x0048D0EF = 8A 88 98 35 00 00 mov cl,[eax+0x3598]`、`0x005989DC = 38 99 98 35 00 00 cmp byte [ecx+0x3598],bl`）；真机实测该**字节 = `0x92`**（非 0/1 布尔）⇒ 它不是「是否加载屏」的布尔判据，用作门控可**静默拦死**灰化。
> - ⇒ 该判据已从护栏谓词中删除（RADAR-FIX2 F3①），改以雷达双表面有效性 + `GameMode∈[0,5]` 替代。
>
> **E5③ 附录 A.3 的 `N` 门限按「小地图增量重绘」校准**（就地勘误见附录 A.3 同节）。

---

## [META]

| 项 | 值 |
|---|---|
| task | RADAR-FIX（Q3① 小地图灰化 P0 + P1 配置死键） |
| executor | DSH 子代理（parent agent id: session-852a2193-df41-4859-b6f3-cd17f595410f） |
| mode | accept-edits（写作用域见 [5]） |
| 快照时点 | gamemd.exe MD5 = 4F37486E5B0DBE2AE5F45AEEE0F98367；旧 DLL SHA256 = E7FA669C…DCC7CA（129,536 B） |
| 基线只读 | gamemd.exe 全程只读（见 [5] 哈希）；未启动游戏、未注入进程（见 [7]） |

---

## [0] 结论摘要

1. **Q3① 的根因是「地址语义判错」，不是「阈值/时机不对」**：`0x00A8B238` 不是「游戏状态（0=菜单,3/4=局内,5=加载）」，而是 **`SessionClass::Instance` 对象的首成员 `GameMode`**（YRpp `SessionClass.h:54/56` 用 `reference<SessionClass,0xA8B238u>`，即**原地静态实例**，非指针）。其枚举只有 `{0=Campaign, 3=LAN, 4=Internet, 5=Skirmish}`（`ref/yrpp/GeneralDefinitions.h:670-675`）。
2. 因此 ZCode 的实测 **campaign=0 / skirmish=5 完全符合枚举**，而旧护栏「0=菜单 ⇒ 跳过」把**战役对局**判成菜单 —— 灰化分支对战役**永远不可达**，且「1=局内」这类折中也救不了它（0 与局内同值）。
3. 更关键：`0x00A8B238==0` **既出现在战役局内、也出现在退局/回菜单重置路径**（`0x52E175` / `0x52E1FE` / `0x52E213` / `0x52E553` / `0x52E5D4` 全部 `mov [0xA8B238],ebx(=0)`）。⇒ **该地址在任何组合下都无法单独充当「是否局内」谓词**，必须换判据。
4. **选定的新谓词（证据最强）= 引擎自己的判据**：`HouseClass::Player / PlayerPtr (0x00A83D4C) != 0`，并以 `ScenarioClass::Instance (0xA8B230) != 0`、`ScenarioClass+0x3598 == 0`（非加载屏）、`GameMode (0xA8B238) <= 5` 三项收窄。首项正是 `RadarClass::Plot_Cell` 函数头 **0x00655C5D `cmp eax,ebp` / 0x00655C62 `je 0x00656138`** 所用的同一判据（`PlayerPtr==0` 直接 return）——语义 = 存在本地玩家 = 有活对局。
5. **已落地并部署**：新 DLL `ra2render/ra2render.dll` + `ra2youli/ra2render.dll`（132,608 B，SHA256 `26FE7A71…9A5D`）；新增 ini 开关 `[FogOfWar] RadarFogGuardMode=0|1|2`（默认 **1=新谓词**）；新增遥测 `雷达灰化分支进入次数`（`s_minimapFogBranchHits`）并与既有 `雷达灰化像素数` 一并进 2 秒遥测行；两份 ini 的重复 `[Logic]` 已合并为单节，启动日志新增 `配置来源` 行区分 **ini 命中 / API 默认值兜底**。
6. **风险最大项**：新谓词的真机有效性属 **[待实测]**（本批为静态定谳 + 编译产物级验收，真机由 ZCode 执行）。若 `RadarFogGuardMode=1` 下计数仍恒 0，按 [附录 A] 的 A/B 阶梯用 `=2`（无护栏）隔离，并回读 4 个全局原值。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|---|---|---|---|
| F1-c1 | `0xA8B238` 到底是什么？ | **`SessionClass::Instance.GameMode`**（枚举 0=Campaign,3=LAN,4=Internet,5=Skirmish；非「菜单/加载状态」） | [实证] | `ref/yrpp/SessionClass.h:54,56`；`ref/yrpp/GeneralDefinitions.h:670-675`；gamemd `0x0052DB09 A1 38B2A800` / `0x0052DD61 C7 05 38B2A800 04000000` / `0x0052DD7F …03…` / `0x0052E10F …05…`；`docs/re/anchor_claims.txt:126` |
| F1-c2 | 为何 campaign=0 / skirmish=5？ | 正是枚举值本身：战役=Campaign(0)、遭遇战=Skirmish(5)。GameMainLoop **直接以该值做 switch** | [实证] | `0x0052E14D A1 38B2A800` + `0x0052E158 83F805` + `0x0052E161 FF 24 85 A4EB5200`（表 0x52EBA4，idx=GameMode 0..5） |
| F1-c3 | 候选① `ScenarioClass::Instance(0xA8B230)!=0 && +0x3598==0` 可用吗？ | **可作辅助项，不可单独作主判据**：Scenario 指针在菜单/退局被清零（可用），但 `+0x3598` 语义 YRpp 仅记 `unknown_3598`（DWORD），命名属推演 | [实证]（写点/读点）+[推演]（命名） | 写点 `0x0052BA94 A3 30B2A800`、`0x0052BAB6`/`0x006BEB7D` 清零；读点 `0x0048D001`、`0x0048D0EF 8A 88 98350000`；耦合 `0xAC4F58`(ProgressScreenClass) |
| F1-c4 | 候选② `0xB0B518`（"雷达激活标志"）可用吗？ | **否决**：它是「侧边栏/雷达本帧需要 present/重绘」的**事件脏标志**（多处 `=1`，状态机 `=bl(0)` 清），不是稳定的「是否局内」位 | [实证] | 置位 `0x00653621 C6 05 18B5B000 01`、`0x006A723A`、`0x006D0BB7`；清零 `0x006A7166 88 1D 18B5B000`、`0x006AB9C9`；另见 `docs/re/sidebar_selection_ui.md:63,164` |
| F1-c5 | 最强谓词是什么？ | **`PlayerPtr (0x00A83D4C) != 0`（+3 项收窄）**：`HouseClass::Player` 指针，**引擎自身对这条路径的判据** | [实证] | `ref/yrpp/HouseClass.h:145 reference<HouseClass*,0xA83D4Cu>`；`0x00655C50 A1 4C3DA800` / `0x00655C5D 3BC5` / `0x00655C62 0F 84 D0040000`（→`0x00656138` 尾声）；语义定谳 `0x0050B71E 3BCA` + `0x0050B720 0F94C0`（`sete al`：owner==Player）；赋值 `0x0068ACE9 A3 4C3DA800`；清零 `0x0052D9DE 89 1D 4C3DA800` |
| F1-c6 | 会误判吗？ | 见 §2.7 误判矩阵：**不会把菜单判成局内**（菜单 `PlayerPtr==0`）；理论上可能把极短暂过渡帧判成非局内（退局/重载瞬间），后果仅「该帧不灰化」，有 `=2` 兜底 | [推演] | — |
| F2 | 护栏替换 + ini 开关 + 两遥测 | **已落地**：`RadarFogGuardMode` 置于 ini 开关**之后**、默认 1；新增 `雷达灰化分支进入次数`，与既有 `雷达灰化像素数` 并入 2 秒遥测行；既有护栏（cell 有效性 / `Cells.Capacity` 上界 262144 / 指针下界 0x10000 / `s_minimapFogGate`）**一字未动** | [实证]（源码 + 产物反汇编） | `ra2render/blitter_hooks.cpp:1562-1617`（护栏）、`:306-325`（2 秒遥测行）、`ra2render/ra2render.h:85-99,211`；产物 `0x10002250–0x100022B9` |
| F3 | 重复 `[Logic]` 合并 + 来源日志 | **已落地**：两份 ini 现各**恰 1 个** `[Logic]`（含 `TargetScanInterval` 与 `TargetScanKey`）+ 1 个 `[FogOfWar]`；新增 `配置来源` 日志行，逐键标 `(来源: ini)` / `(来源: 默认值)` | [实证] | `ra2render/ra2render.ini`（41 行）、`ra2youli/ra2render.ini`（41 行，两份 SHA256 同 `03BE7142…`）；`blitter_hooks.cpp` 的 `GetIniStringEx/GetIniIntEx/IniSrc` |
| F4 | 构建与部署 | **已完成**：旧 DLL 已备份 → `ra2render/build.bat`（VS2022 BuildTools x86 v17.14.33）→ 部署 `ra2youli/ra2render.dll`；两份 ini 同步 | [实证] | `out/re_work/radar_fix/build_log.txt`；备份 `out/re_work/radar_fix/backup/*.pre-radarfix`；新 DLL 132,608 B SHA256 `26FE7A71…9A5D` |
| F5 | 编译产物级验收 | **三项全过**（见 §2.8）：① 新护栏常量/调用与源码逐条一致；② 两个遥测符号存在（COFF 符号表 + 地址差交叉校验）；③ 旧护栏路径可由 `RadarFogGuardMode=0` 抵达 | [实证] | `out/re_work/radar_fix/disasm/f5_dll_verify.txt`、`f5_symbols.txt` |
| 门禁 | 锚点 + 字节断言 | `verify_anchors.py` **323/323 PASS**；`audit_bytes.py claims.txt` **59/59 OK** | [实证] | `out/re_work/radar_fix/verify_anchors_out.txt`、`audit_out.txt` |

---

## [2] 关键证据块

### 2.1 定谳：`0x00A8B238` = `SessionClass::Instance.GameMode`

**(a) 符号来源（third-party 定义，非本项目推测）**

- `ref/yrpp/SessionClass.h:54` → `static constexpr reference<SessionClass, 0xA8B238u> const Instance{};`
  `reference<T, A>` 表示 **A 处即对象本体**（不是 `T*` 指针变量）。
- `ref/yrpp/SessionClass.h:56` → `GameMode GameMode;`（**第 0 个成员，偏移 0**）。
- `ref/yrpp/GeneralDefinitions.h:670-675` →
  `enum class GameMode : unsigned int { Campaign = 0x0, LAN = 0x3, Internet = 0x4, Skirmish = 0x5 };`

**(b) 字节级佐证：值域与写点**（全部经 `audit_bytes.py` OK）

| VA | 原始字节 | Capstone | 语义 |
|---|---|---|---|
| `0x0052DD61` | `C7 05 38 B2 A8 00 04 00 00 00` | `mov dword [0xA8B238], 4` | Internet 局启动 |
| `0x0052DD7F` | `C7 05 38 B2 A8 00 03 00 00 00` | `mov dword [0xA8B238], 3` | LAN 局启动 |
| `0x0052E10F` | `C7 05 38 B2 A8 00 05 00 00 00` | `mov dword [0xA8B238], 5` | **Skirmish 局启动**（实测 =5 命中） |
| `0x0052E175` / `0x0052E553` / `0x0052E5D4` | `89 1D 38 B2 A8 00` | `mov dword [0xA8B238], ebx(=0)` | **退局/回菜单重置为 0**（⇒ 0 二义） |
| `0x0067E3BD` | `83 3D 38 B2 A8 00 05` | `cmp dword [0xA8B238], 5` | 既有台账锚点（`docs/re/anchor_claims.txt:126`） |

> 值 1/2 亦被使用（`0x52E185` 同时承担 idx1/idx2），与「战役内过场/特殊会话」相关；本批不细究，只影响谓词的「`<=5` 上界」写法。

**(c) 状态机 jump table 反推 —— 该值就是分派键**

`GameMainLoop 0x0052D9A0` 帧首（`0x0052D9C9` 起读 `ScenarioClass::Instance`，`0x0052D9DE` 清 `PlayerPtr`，随后 `0x0052DB09` 读 GameMode）：

    0052DB09  A1 38B2A800        mov  eax,[0xA8B238]
    0052DB0E  3B C3              cmp  eax,ebx(0)
    0052DB12  BE 12000000        mov  esi,0x12          ; ==0 -> esi=0x12（局内帧态）
    0052DB1B  83 F8 04           cmp  eax,4
    0052DB1E  0F 94 C1           sete cl
    0052DB21  83 C1 10           add  ecx,0x10          ; ==4 -> esi=0x11 ; 其它 -> esi=0x10
    ...
    0052DCD5  8D 46 01           lea  eax,[esi+1]
    0052DCD8  83 F8 12           cmp  eax,0x12
    0052DCDB  0F 87 65070000     ja   0x52E446
    0052DCE1  FF 24 85 58EB5200  jmp  dword [eax*4+0x52EB58]   ; 屏幕状态机

进入局内帧后（`0x0052E119` 把 `0xA8B238` 交给 `0x6980C0`，遍历后）：

    0052E14D  A1 38B2A800                mov eax,[0xA8B238]
    0052E158  83 F8 05                   cmp eax,5
    0052E15B  0F 87 E3010000             ja  0x52E344
    0052E161  FF 24 85 A4EB5200          jmp dword [eax*4+0x52EBA4]   ; ★ 按 GameMode 直接分派

**表 `0x52EBA4` 六项（idx = GameMode 0..5）**：

| idx | 表内字节（VA=0x52EBA4+4i） | 目标 | 语义 |
|---|---|---|---|
| 0 | `2F DD 52 00` | `0x0052DD2F` | Campaign：`mov esi,0x12; jmp 0x52E446`（**局内跑帧**） |
| 1 | `85 E1 52 00` | `0x0052E185` | 特殊会话分支 |
| 2 | `85 E1 52 00` | `0x0052E185` | 同上 |
| 3 | `44 E3 52 00` | `0x0052E344` | LAN（继续跑帧） |
| 4 | `1E E2 52 00` | `0x0052E21E` | Internet |
| 5 | `68 E1 52 00` | `0x0052E168` | **Skirmish**：`call 0x6AE2C0`，返回 0 时 `mov [0xA8B238],0` |

⇒ **「0=菜单」的前提被结构性推翻**：GameMode==0 走的是 idx0 = 战役局内跑帧路径，而不是任何「菜单等待」路径。菜单/前端的切换体现在 `esi` 屏幕状态（`0x52EB58` 表），不在 `0xA8B238` 上。

### 2.2 候选①：`ScenarioClass::Instance (0xA8B230)` + `IsLoadingScreen(+0x3598)`【原记 · 该命名已被勘误：见文首 E5② —— `+0x3598` 语义未定，实测字节 = 0x92，非加载屏布尔】

- `ref/yrpp/ScenarioClass.h:58` → `reference<ScenarioClass*, 0xA8B230u>`（**指针变量**）。
- 写点：[实证] `0x0052BA94 A3 30 B2 A8 00`（建 Scenario 时挂堆实例）、`0x0052BAB6`、`0x006BEB7D`（两处清零）。
- `+0x3598`：全镜像仅 **31** 条 `disp=0x3598` 访存指令，且只在 `0x48D0xx` 与 `0x598xxx–0x59Axxx` 两簇。

    0048D0EA  A1 30B2A800            mov  eax,[0xA8B230]
    0048D0EF  8A 88 98350000          mov  cl,[eax+0x3598]
    0048D0F5  84 C9                    test cl,cl
    0048D0F7  74 68                    je   0x48D161        ; ==0 跳过"加载进度泵"
    0048D0F9..0048D13A               ... call 0x5F1C30（取 0xA8EA70 列表项）
    0048D111  83 7C 24 04 6C           cmp dword [esp+4],0x6C
    0048D137  B9 584FAC00              mov ecx,0xAC4F58        ; ProgressScreenClass

    005989CF  8B 0D 30B2A800           mov ecx,[0xA8B230]
    005989DC  38 99 98350000           cmp  byte [ecx+0x3598],bl(0)
    005989E2  0F 94 C0                 sete al                  ; 「非加载」= 1
    005989F0  68 00005940              push 0x40590000          ; float 100.0
    005989F6  B9 584FAC00              mov  ecx,0xAC4F58
    005989FB  E8 60 A00A00              call 0x642A60            ; ProgressScreen->SetProgress(100%)

⇒ 【原记 · 已勘误（E5②）】~~`+0x3598 != 0` 与「把进度打到 100%」互斥，命名 **IsLoadingScreen** 方向正确~~（[实证] 读点 + [推演] 命名；YRpp `ScenarioClass.h:224` 仅记 `DWORD unknown_3598`）。
**〔勘误〕** 后续取证推翻该命名：12 处访问**全为字节粒度门控**、真机实测字节 = **`0x92`**（非 0/1）⇒「非 0 即加载屏」不成立，**该判据不得再用于门控**（RADAR-FIX2 F3 已从护栏删项）。紧随其后的「判断：可作辅助项（局内恒为 0）」同属已证伪前提。
**判断**：可作辅助项（局内恒为 0）；单独作主判据不足（YRpp 未定名，且本项目此前对 0xA8B238 已犯过「按文档想当然」的错，不重犯）。

### 2.3 候选②（否决）：`0xB0B518`

- 置位：`0x00653621 C6 05 18B5B000 01`、`0x006A723A`、`0x006D0BB7`、`0x0063FB55`、`0x006A7AAD` …（共 19 处写 1）
- 清零：`0x006A7166 88 1D 18B5B000`（`mov [0xB0B518],bl`）、`0x006AB9C9`（同款）、`0x006A748A`
- 读点仅 5 处（`0x006A7019`、`0x006A7090`、`0x006A7143`、`0x006A73A5` …）

⇒ 形态是「本帧侧边栏/雷达有变化 → 置 1 → present 后清 0」的**脏标志**（`docs/re/sidebar_selection_ui.md:63/164` 与 `REVERSE_ENGINEERING_AND_PATCHES.md:249` 两种记载中，前者与指令形态一致）。**它不是状态位**，不能充当局内谓词；把它当状态读会在「无变化的静止帧」误判。

### 2.4 选定谓词（F1 最强证据）：`PlayerPtr (0x00A83D4C) != 0`

**(a) 符号**：`ref/yrpp/HouseClass.h:145` → `static constexpr reference<HouseClass*, 0xA83D4Cu> const Player{};`（**指针变量**）。

**(b) 引擎自身的判据（本谓词的杀手级证据）**：挂钩点所在函数 `RadarClass::Plot_Cell`（`0x00655C50`）**函数头**即用该地址做门：

    00655C50  A1 4C3DA800        mov  eax,[0xA83D4C]     ; PlayerPtr
    00655C55  83 EC 30           sub  esp,0x30
    00655C58  53 / 55 33ED / 56   push ebx / push ebp ; xor ebp,ebp ; push esi
    00655C5D  3B C5              cmp  eax,ebp(0)
    00655C5F  57                 push edi
    00655C60  8B F1              mov  esi,ecx            ; ecx = 雷达单例 0x87F7E8
    00655C62  0F 84 D0 04 00 00  je   0x656138          ; ★ PlayerPtr==0 -> 直接 return
    ...
    00656138  5F 5E 5D 5B 83 C4 30 C2 04 00     ; 函数尾声 pop edi/esi/ebp/ebx; add esp,0x30; ret 4

即：**本钩子（`0x00655D38`）能被执行，本身就意味着引擎已判定 `PlayerPtr != 0`**。把同一条判据写进护栏，语义上不会与引擎打架。

**(c) 语义定谳（它是 HouseClass*，且是「本地玩家」）**：`0x50B6F0`（Plot_Cell 内部"未探索格只画己方"门所调函数）：

    0050B6F0  A1 38B2A800        mov  eax,[0xA8B238]     ; GameMode
    0050B6F5  85 C0              test eax,eax
    0050B6F7  75 1D              jne  0x50B716          ; 非 Campaign -> 走 PlayerPtr 比较
    0050B6F9  8A 81 EC010000     mov  al,[ecx+0x1EC]     ; Campaign 特例：读 House 属性位
    ...
    0050B716  8B 15 4C3DA800     mov  edx,[0xA83D4C]
    0050B71E  3B CA              cmp  ecx,edx
    0050B720  0F 94 C0           sete al                 ; al = (house == PlayerPtr)

**(d) 生命周期写点**：赋值 `0x0068ACE9 A3 4C3DA800`（建局时挂本地玩家 House*，随后 `mov eax,[eax+0x34]` 立即解引用 ⇒ 确认是指针）；清零 `0x0052D9DE 89 1D 4C3DA800`（GameMainLoop 帧首重置段）、`0x00685231`（退局收尾）。

### 2.5 候选（补充）：调用链可达性 —— 整条雷达绘制链只在局内

`docs/re/radar_hook_routeA_spec.md` / `out/reverse/minimap_re_report.md` 已实证调用链：
`MouseClass::v[16]=0x6D0A20 → SidebarClass::v[16]=0x6A6C30 → PowerClass::v[16]=0x63FB20 → RadarClass::v[16]=0x653100 → RadarClass::Refresh=0x656EC0 → call 0x655C50`（`0x6574C3`/`0x657520`）。
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x6574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
而 `0x655C50` 入口第一件事就是 `PlayerPtr==0 → return`（§2.4b）。⇒ 该链在菜单下即使被调度，也**不会**进入灰化代码。这解释了为什么「护栏」在本路径上**本质冗余**，也说明新护栏取「引擎自己的判据」是自洽而非叠加。

### 2.6 旧护栏为何是 P0（复现链）

    [ZCode ZC-1 实测] 战役局内 [0xA8B238]=0x00（帧 9189 / 135 单位 / 31fps）
            ↓ 旧护栏语义（代码注释）"0=菜单"
            cmp byte ptr [0xA8B238], 0  →  je do_passthrough   ← 恒成立
            ↓
       灰化分支永不可达 ⇒ 遥测"小地图灰化像素" 全程 0（157 条遥测为证）

新证据链补全：`0` 不是「菜单」而是「Campaign」，且 `0` 还被退局路径写入 ⇒ **该地址在任何编码下都无法实现旧注释的意图**。

### 2.7 误判矩阵（新谓词）

| 场景 | PlayerPtr!=0 | Scenario!=0 | +0x3598==0 | GameMode<=5 | 判定 | 是否正确 |
|---|---|---|---|---|---|---|
| 主菜单（开局前） | 0 | 0 | — | 0 | 跳过灰化 | ✅（且 Plot_Cell 本就不会被调） |
| 战役局内 | 1 | 1 | 1 | 0 | **放行灰化** | ✅（修复目标） |
| 遭遇战局内 | 1 | 1 | 1 | 5 | **放行灰化** | ✅ |
| LAN/Internet 局内 | 1 | 1 | 1 | 3/4 | 放行（但 `EnableMinimapFog` 在 MpActive 下强制 0，总闸先关） | ✅ 保守 |
| 加载进度屏 | 1 | 1 | **1** | 任意 | 跳过灰化 | ✅ 预期 |
| 退局/回菜单过渡帧 | 可能 0 | 可能 1/0 | — | 0 | 跳过 | ✅ 无害（仅少灰化 1 帧） |
| 存档读盘中（`0x5EF7xx` 路径） | 可能 0 | 1 | — | 0/1 | 跳过 | ✅ 无害 |

**已知理论缺口**：若将来某战役补丁把 `GameMode` 写成 `>5`，新谓词会拒绝灰化。缓解：`RadarFogGuardMode=2` 无护栏兜底；且该值与引擎自身 switch 上界同源。

### 2.8 F5 编译产物级验收（对最终部署 DLL，SHA256 `26FE7A71…9A5D`）

来源：`out/re_work/radar_fix/disasm/f5_dll_verify.txt`（反汇编）、`f5_symbols.txt`（符号）。

**① 新护栏分支与源码逐条一致**（DLL ImageBase 0x10000000，桩入口 `0x10002250`）

    10002250  80 3D A3090210 00        cmp  byte [0x100209A3],0        ; s_minimapFogGate
    10002257  0F 84 ED000000           je   0x1000234A                  ; do_passthrough
    1000225D  8A 0D 22000210           mov  cl,[0x10020022]            ; s_radarFogGuardMode
    10002263  84 C9                    test cl,cl
    10002265  74 42                    je   0x100022A9                  ; mode0 -> guard_legacy
    10002267  80 F9 02                 cmp  cl,2
    1000226A  74 4D                    je   0x100022B9                  ; mode2 -> guard_passed
    1000226C  50                       push eax
    1000226D  B9 4C3DA800             mov  ecx,0x00A83D4C             ; HouseClass::Player
    10002272  8B 09                    mov  ecx,[ecx]
    10002274  81 F9 00000100           cmp  ecx,0x10000
    1000227A  72 27                    jb   0x100022A3
    1000227C  BA 30B2A800             mov  edx,0x00A8B230             ; ScenarioClass::Instance
    10002281  8B 12                    mov  edx,[edx]
    10002283  81 FA 00000100           cmp  edx,0x10000
    10002289  72 18                    jb   0x100022A3
    1000228B  80 BA 98350000 00        cmp  byte [edx+0x3598],0        ; 【原记 · 已勘误（E5②）】IsLoadingScreen
                                                                      ;   ⇒ 该字节语义未定（YRpp: unknown_3598），真机实测 = 0x92；本护栏已删
    10002292  75 0F                    jne  0x100022A3
    10002294  BA 38B2A800             mov  edx,0x00A8B238             ; GameMode
    10002299  8B 12                    mov  edx,[edx]
    1000229B  83 FA 05                 cmp  edx,5
    1000229E  77 03                    ja   0x100022A3
    100022A0  58  EB16                 pop eax ; jmp 0x100022B9
    100022A3  58  E9 A1000000          pop eax ; jmp 0x1000234A        ; guard_new_fail
    100022A9  50 / B8 38B2A800        push eax; mov eax,0x00A8B238     ; ★旧护栏路径保留
    100022AF  80 38 00                 cmp  byte [eax],0
    100022B2  58 / 0F 84 91000000     pop eax; je 0x1000234A
    100022B9  FF 05 E8092E10           inc  dword [0x102E09E8]         ; 雷达灰化分支进入次数
    100022BF  3D 00000100              cmp  eax,0x10000                ; ↓ 既有护栏原样保留
    100022CA  3D 50DCAB00              cmp  eax,0x00ABDC50
    100022D1  F6 80 2C010000 08        test byte [eax+0x12C],8
    100022EB  81 FA 00000400            cmp  edx,0x40000
    10002302  8B 8E 20120000           mov  ecx,[esi+0x1220]
    10002310  8B 96 1C120000           mov  edx,[esi+0x121C]
    10002321  FF 50 28                 call dword [eax+0x28]           ; Get_Pixel
    10002324  D1 E8 / 25 EF7B0000      shr eax,1 ; and eax,0x7BEF
    10002337  FF 52 24                 call dword [edx+0x24]           ; Set_Pixel
    1000233A  FF 05 E4090210           inc  dword [0x100209E4]         ; 雷达灰化像素数
    10002344  83 C4 30 / C2 0400        add esp,0x30 ; ret 4
    1000234A  FF 25 EC092E10           jmp  dword [0x102E09EC]         ; s_pPlotCellTrampoline

**② 两个遥测计数符号存在**（`blitter_hooks.obj` COFF 符号表 + 地址差交叉校验）

| 符号 | obj 段 | obj 偏移 | DLL 引用地址 | 校验 |
|---|---|---|---|---|
| `_s_minimapFogBranchHits` | `.bss` | 0x2C0098 | `0x102E09E8`（`100022B9 inc dword [..]`） | 与 `_s_visionGrid`(0x98 / 0x100209E8) 的差 **两处都是 0x2C0000** ✔ |
| `_s_minimapFogPixels` | `.bss` | 0x94 | `0x100209E4`（`1000233A inc dword [..]`） | 与 `_s_visionGrid` 的差 **两处都是 −4** ✔ |
| `_s_radarFogGuardMode` | `.data` | 0x22 | `0x10020022`（段基+0x22，初值字节 **01**） | 段基+偏移一致 ✔ |
| `_s_pPlotCellTrampoline` | `.bss` | 0x2C009C | `0x102E09EC` | 差 **0x2C0004** 一致 ✔ |

**③ 旧护栏路径仍可抵达**：`0x100022A9–0x100022B3` 的 `mov eax,0xA8B238; cmp byte [eax],0; je` 完整存在，且由 `s_radarFogGuardMode==0` 分支进入（与源码 `guard_legacy:` 标签一一对应）。
**④ 挂钩点未变**：DLL `.text` 内 `mov eax,0x655d38` / `push 9` / `push 0x655d38` / `mov byte [0x655d38],0xe9`（安装 9 字节补丁）与 `0x0065719A` 常量均存在。

---

## [3] 勘误（对既有文档/结论的更正；**本批不改他人文档，交 Lead 处置**）

| # | 目标文件:行号 | 改前原文 | 改后文本 | 理由 | 影响面 |
|---|---|---|---|---|---|
| E-1 | `docs/re/clock_frame_loop.md:85`（表格行） | `0xA8B238 = SessionClass 游戏状态（0=菜单, 3/4=局内, 5=加载…），571 处` | `0xA8B238 = SessionClass::Instance 首成员 GameMode（0=Campaign, 3=LAN, 4=Internet, 5=Skirmish）；不是菜单/加载状态` | YRpp `SessionClass.h:54/56` + `GeneralDefinitions.h:670-675`；写点 0x52DD61/DD7F/E10F；GameMainLoop 按该值 switch（0x52E161→表 0x52EBA4） | **影响产品决策**：旧记载直接导致 Q3① 的 P0 误判；同文档 `:192/257/432` 同址引用需一并订正 |
| E-2 | `docs/re/mp_autodowngrade_spec.md:154` | `[0xA8B238]∈{1,2,3,4} 且主判=1 ⇒ 联机对局进行中` | 改为「`[0xA8B238]` = GameMode（0/3/4/5 为战役/LAN/Internet/遭遇战）；**它不能区分局内与菜单**（0 双关），联机判定请只用 0xA8D5F8 与 0xAA0444」 | 实测 campaign=0 / skirmish=5；0 亦由退局路径写入 | 影响联机门控文档的辅助判据；若真有代码按 `∈{1,2,3,4}` 判「局内」，会在战役(=0)与遭遇战(=5)双双失效 |
| E-3 | `docs/re/mp_autodowngrade_spec.md:22` | `② [0xA8B238]∈{3,4}（局内）` | 同上订正 | 同上 | 同上 |
| E-4 | `docs/re/ARCHITECTURE_ATLAS.md:1307` | `M2["GameMainLoop (0x0052D9A0) 全局状态机 [0x00A8B238]"]` | 补注「`[0xA8B238]` 为 SessionClass::Instance.GameMode（非屏幕状态；屏幕状态在 `esi`/表 0x52EB58）」 | 本批反汇编证据 | 文档准确性；不影响既有结论方向 |
| E-5 | `out/reverse/minimap_re_report.md:63` | `0x00A8B238 = 游戏状态（0=菜单；≠0=局内）` | `0x00A8B238 = SessionClass::Instance.GameMode（0=Campaign,3=LAN,4=Internet,5=Skirmish；与菜单无关）` | 同上；该行是旧护栏注释的来源 | 直接影响小地图补丁设计（本批已按新语义重写护栏） |
| E-6 | `ra2render/blitter_hooks.cpp:1484`（**改前**；**就地已改**） | `mov eax, 0x00A8B238  // 游戏状态（0=菜单）` | 删除；替换为三模式护栏 + 完整注释块（`blitter_hooks.cpp:1562-1617`，等价反汇编见 §2.8） | ZC-1 真机 + 本批静态双重定谳 | 本次修复本体 |
| E-7 | `ra2render/ra2render.ini` / `ra2youli/ra2render.ini`（**就地已改**） | 文件末尾存在**第二个** `[Logic]` 节（`TargetScanKey`） | 合并进首个 `[Logic]` 节并加勘误注释 | Windows `GetPrivateProfileStringA/IntA` 对同名重复节**只读第一个** ⇒ 该键从未生效，「配置(position)」实为 API 默认值 | 解释了一个长期隐性缺陷（配置静默失效） |
| E-8 | `REVERSE_ENGINEERING_AND_PATCHES.md:249` 与 `docs/re/sidebar_selection_ui.md:63` 对 `0xB0B518` 的两种记载 | 前者「byte 雷达激活标志 1=雷达开启」；后者「全局"侧边栏内容已变/需 present"标志」 | 以指令形态为准：**near-事件脏标志**（19 处置 1 / 多处清 0），非稳定状态位 | `0x00653621 C6 05…01`、`0x006A7166 88 1D…`、`0x006AB9C9` | 文档准确性；**不要拿它当「局内/雷达可用」判据** |

---

## [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证方法（可执行） | 阻塞级别 |
|---|---|---|---|---|
| U-1 | 新谓词在真机的**有效性**（灰化分支进入次数>0、灰化像素>0） | 需运行游戏；本批禁启动进程 | 按 [附录 A] 执行；`Select-String -Path ra2youli\ra2render.log -Pattern '雷达灰化'` | **P0** |
| U-2 | `0xA8B238` 值 1/2 的精确语义（`0x52E185` 分支） | 不在本修范围内，且需会话/过场真机对照 | 反汇编 `0x0052E185` 全函数；真机在战役过场/读盘时采样该值 | P2 |
| U-3 | `ScenarioClass+0x3598` 的**官方命名** | YRpp 仅记 `DWORD unknown_3598`；本批只能由读点行为（加载进度泵 / 进度置 100%）推定 | 追 YR 1.001 PDB 或 Ares/Phobos 命名表 | P2 |
| U-4 | 菜单下遥测是否会周期打印（负向对照基线） | 需真机日志 | [附录 A] A.5：菜单静置 ≥30 s，确认两计数**不增长** | P1 |
| U-5 | LAN/Internet 局内 `RadarFogGuardMode` 是否需二次约束 | 需求侧未定（G-01 已强制 `EnableMinimapFog=0`），总闸优先级高于护栏 | 人裁决（见 [9]-Q1） | P2 |
| U-6 | 战役「有雷达」的初始条件 | 战役局是否给雷达取决于地图/建筑；静态无法确定 | [附录 A] A.2 提供两种造法（自带雷达关 / 自建作战实验室） | P1 |

---

## [5] 写作用域合规声明

**改动文件清单（字节数 / 时间）**

| 路径 | 改动前 | 改动后 | 时间 |
|---|---|---|---|
| `ra2render/ra2render.h` | 13,141 B | **15,092 B / 295 行**（+局内判据常量块 / +`g_radarFogGuardMode`） | 13:27:56 |
| `ra2render/blitter_hooks.cpp` | 86,961 B / 1,892 行 | **95,586 B / 2,023 行**（+ini 来源判定、+护栏三模式、+遥测） | 13:27:56 |
| `ra2render/ra2render.ini` | 2,996 B / 51 行 / 2×`[Logic]` | **4,205 B / 41 行 / 1×`[Logic]`**（SHA256 `03BE7142…5417`） | 13:28:25 |
| `ra2youli/ra2render.ini` | 2,996 B / 51 行 / 2×`[Logic]` | **4,205 B / 41 行 / 1×`[Logic]`**（同哈希） | 13:28:25 |
| `ra2render/ra2render.dll` | 129,536 B `E7FA669C…` | **132,608 B** SHA256 `26FE7A71D7B3618A49FCDDDA639B3B3EC94BE747360432E8ED82A919003B9A5D` | 13:27:59 |
| `ra2youli/ra2render.dll` | 129,536 B `E7FA669C…` | **132,608 B** 同哈希（由 build.bat 部署） | 13:27:59 |
| `ra2render/ra2loader.exe`、`ra2render/*.obj` | 构建产物 | 随构建更新（在 `ra2render/**` 允许范围内） | 13:27 |
| `docs/re/radar_fix_report.md` | — | **新建**（本文件） | 13:3x |
| `out/re_work/radar_fix/**` | — | **新建**（备份 / 编译日志 / 反汇编证据 / claims） | 13:1x–13:3x |

**未触碰清单**：`gamemd.exe`（MD5 **4F37486E5B0DBE2AE5F45AEEE0F98367**，前后一致）、任何 `.mix` / `.map` / `.sav`、`ra2forge/**`、`mcp/**`、`ra2opt/**`、`docs/RE_COORDINATION.md`、其他 `docs/**`、台账、其他项目文件。

**一处需声明的越界副作用（已回滚并核验）**：`ra2render/build.bat` 固定执行 `copy /y ra2loader.exe ..\ra2youli\ra2loader.exe`，而 `ra2youli/ra2loader.exe` 不在允许写范围内（且与 `ra2render/ra2loader.exe` **哈希本就不同**）。处置：构建前备份 → 构建后**逐字节还原** → 复核 SHA256 仍为原值 `E10F60C59C73EC6AA536A6B4A80F99C0037D56E5E91BE3076481662D89985594`。⇒ **对外部文件的内容零净变更**（仅 mtime 因 copy 而变）。若 Lead 认为连 mtime 也不能动，请裁决（见 [9]-Q3）。

---

## [6] 门禁实跑输出（原文粘贴）

**(1) `python tools\verify_anchors.py` —— 323/323 PASS**

    [基线完整性审计]
      [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
      [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
      [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
    回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
    ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

（完整输出：`out/re_work/radar_fix/verify_anchors_out.txt`）

**(2) `python tools\audit_bytes.py out\re_work\radar_fix\claims.txt` —— 59/59 OK，0 MISMATCH/NOREAD**

    合计 59 条：OK=59  MISMATCH/NOREAD=0

（节选：`0x52db09 a1 38 b2 a8 00 → OK mov eax,[0xA8B238]`；`0x52e161 ff 24 85 a4 eb 52 00 → OK jmp dword [eax*4+0x52EBA4]`；`0x655c62 0f 84 d0 04 00 00 → OK je 0x656138`；`0x50b720 0f 94 c0 → OK sete al`；`0x68ace9 a3 4c 3d a8 00 → OK mov [0xA83D4C],eax`。完整输出：`out/re_work/radar_fix/audit_out.txt`）

> 说明：首次运行曾出现 2 条 MISMATCH，均为**我方地址笔误**（`0x00655C5F` 实为 `push edi`，`je` 在 `0x00655C62`；另一条应为 `0x00653621` 而非 `0x00653623`）。已修正 claims，并同步修正 `ra2render.h` / `blitter_hooks.cpp` 中对应注释后**重新构建**（故最终 DLL 哈希为 `26FE7A71…`）。

---

## [7] 风险与红线提示

- **未启动游戏、未注入进程**：本批全程仅静态反汇编 + 编译 + 文件部署；`ra2youli/gamemd.exe` 只读（MD5 未变）；无调试器附加、无 `ra2loader` 运行。真机部分**留给 ZCode**。
- **① 同步语义/命令序**：**未触及**。新护栏只读 4 个引擎全局（`0xA83D4C` / `0xA8B230` / `0xA8B238` / `+0x3598`），无写、无新调用、无 RNG、无事件环操作；且位于 `RadarClass::Plot_Cell`（渲染路径）内，不在逻辑帧内。
- **② 随机数消费序**：**未触及**（无 Random 调用；像素灰化只用 `[vt+0x28]`/`[vt+0x24]` 表面读写）。
- **③ 存档结构**：**未触及**（不写任何引擎结构；`s_*` 均为本 DLL 私有 BSS）。
- **④ 渲染像素等价性**：**触及**（本任务即渲染补丁）。灰化公式 `shr eax,1; and eax,0x7BEF` 与主视图灰雾同源、未改；**新增的是「让分支可达」**，因此首次会让**小地图出现 50% 灰化像素**——这是期望行为，但**与前版本像素不同**。⇒ **需要真机对拍验收**（ZCode），且 `RadarFogGuardMode=0` 可一键回到旧像素行为做 A/B。
- **联机**：`EnableMinimapFog` 在 `MpActive` 下仍被 G-01 强制 0（`s_minimapFogGate=0` 在护栏之前短路），本批**未放宽**该保守策略。**不得**据此宣称「联机安全/零 Desync」；联机若启用小地图灰化，仍须走 MP 门控矩阵 + 真机对拍。
- **回滚**：`out/re_work/radar_fix/backup/` 内含旧 DLL 与旧 ini 原件（`*.pre-radarfix`）；`RadarFogGuardMode=0` 为逻辑回滚位。

---

## [8] 交付物清单

| 类别 | 路径 | 规模 |
|---|---|---|
| 源码 | `ra2render/blitter_hooks.cpp` | 95,586 B / 2,023 行（改前 86,961 B / 1,892 行） |
| 源码 | `ra2render/ra2render.h` | 15,092 B / 295 行 |
| 配置 | `ra2render/ra2render.ini`、`ra2youli/ra2render.ini` | 各 4,205 B / 41 行，各 1×`[Logic]`、1×`[FogOfWar]` |
| 产物 | `ra2render/ra2render.dll`、`ra2youli/ra2render.dll` | 132,608 B，SHA256 `26FE7A71…9A5D` |
| 备份 | `out/re_work/radar_fix/backup/` | 5 个（旧 DLL ×2、旧 ini ×2、`ra2loader.exe`（还原用）） |
| 编译日志 | `out/re_work/radar_fix/build_log.txt` | 511 B |
| 反汇编证据 | `out/re_work/radar_fix/disasm/` | 8 个：recon_refs 132 KB、recon2 47 KB、recon3 21 KB、recon4 152 KB、gamemainloop 49 KB、recon6_3598、f5_dll_verify 24 KB、f5_symbols 8 KB |
| 断言 | `out/re_work/radar_fix/claims.txt` | **59 条**（全 OK） |
| 门禁输出 | `verify_anchors_out.txt`、`audit_out.txt` | 323/323 PASS、59/59 OK |
| 脚本 | `out/re_work/radar_fix/*.py` | 8 个（recon_refs / recon2–recon6 / f5_verify / f5_symbols） |
| 报告 | `docs/re/radar_fix_report.md` | 本文件 |

---

## [9] 待裁决项（需人/Lead 决定）

| # | 分叉 | 建议方案 | 理由 |
|---|---|---|---|
| Q1 | `RadarFogGuardMode` 与 G-01 `MpActive` 强制的优先级 | 保持现状：`s_minimapFogGate`（G-01）先短路，护栏只对单机生效 | 不动已验收的联机保守策略；本批不扩大联机面 |
| Q2 | 新谓词是否再加一项 `[0xA8ED5D]/[0xA8ED6B]`（疑似暂停/焦点标志）提高严格度 | **不建议**；先用 4 项版真机跑通，再按数据决定 | 每多一个 AND 项就多一个「分支再次不可达」的风险，本批教训即此 |
| Q3 | `build.bat` 对 `ra2youli/ra2loader.exe` 的固定 copy 越界（本批已还原内容） | 授权：要么把这行改为可选，要么把 `ra2youli/ra2loader.exe` 加入允许写清单 | 否则今后每次执行 build.bat 都会触碰该文件 |
| Q4 | 勘误 E-1..E-5、E-8 由谁落地 | 建议 Lead 指派；本批只出清单不改他人文档 | 遵守「不改他人文档」纪律 |
| Q5 | 真机验收若 `mode 1` 仍为 0（U-1） | 按附录 A 阶梯：先 `=2` 确认灰化本体工作，再回读 4 个全局原值定位是哪一项为假 | 可把「谓词错」与「灰化本体错」彻底分离 |

---

## 附录 A｜真机验收步骤（交给 ZCode）

**前置**：`ra2youli/` 已部署新 `ra2render.dll`（SHA256 `26FE7A71…9A5D`）与新 `ra2render.ini`；单机（非联机）启动，避免 `MpActive` 把总闸关掉。

### A.0 配置（把总闸打开）
在 `ra2youli/ra2render.ini` 的 `[FogOfWar]` 中确认/改为：

    EnableStarCraftFog=1
    EnableMinimapFog=1
    RadarFogGuardMode=1

### A.1 启动日志判据（进游戏前先看这段）
`ra2youli/ra2render.log` 应出现（原文）：

    [ra2render] 配置来源: TargetScanKey=position (来源: ini) | TargetScanInterval=8 (来源: ini) | EnableMinimapFog=1 (来源: ini) | RadarFogGuardMode=1 (来源: ini)
    [ra2render] 门控: MpActive=false, TargetScanKey=配置(position)->生效(position), TargetScanInterval=配置(8)->生效(8), EnableMinimapFog=配置(1)->生效(1), RadarFogGuardMode=生效(1)

- ✅ 判据 1：`TargetScanKey=position (来源: ini)`（不是「默认值」）⇒ 证明 `[Logic]` 合并生效、配置死键已修。
- ❌ 若显示 `(来源: 默认值)` ⇒ ini 未被读取（检查游戏工作目录下是否存在 `ra2render.ini`；本 DLL 用 `GetCurrentDirectoryA + "\ra2render.ini"`）。

抽取命令：

    Select-String -Path ra2youli\ra2render.log -Pattern '配置来源|门控|门控状态迁移' | Select-Object -Last 6

### A.2 构造「战役 + 有雷达 + 侦察后撤离」
1. 单机 → 战役 → 任选一关，进入局内（等到 HUD/侧边栏出现）。
2. **保证有雷达**（二选一）：
   - a) 该关自带雷达建筑/已给雷达（侧边栏右下角出现 140×108 小地图框）；
   - b) 无雷达则**尽快建造 作战实验室/雷达**使小地图出现；建筑未完工前小地图为黑框，不算通过。
3. **侦察后撤离**：
   - 选 1 辆快速单位（履带车/坦克）向地图**未探索区域**移动一段（视野圈扫过去）；
   - 停在那里 ≥2 秒（让该区域进入「已探索」）；
   - 再把它**撤回**原处（或移开），使刚才那片区域**离开直视圈**。
4. 停留 10 秒以上（遥测 2 秒一行，至少 5 行）。

### A.3 日志判据（核心 PASS 条件）

    Select-String -Path ra2youli\ra2render.log -Pattern '雷达灰化' | Select-Object -Last 8

应看到（每 2 秒一行）：

    [ra2render-telemetry] ... 雷达灰化分支进入次数: <N>, 雷达灰化像素数: <M>

- ✅ **PASS**：局内数秒后 `N` **单调增长且显著 > 0**，且 `M > 0`（≥ 已撤离区域的格子数）。
  - **【原记 · 已勘误（E5③）】** 原文门限：~~预期每 2 秒数千～数万（视口内「已探索且直视圈外」的格数每次全量重绘都会进分支）~~ —— 该量级**高估**。
  - **校准后门限（按「小地图增量重绘」机制）**：小地图常态走**脏矩形/脏点增量重绘**（`0x006574C3` 与 `0x00657520` 两处 `call 0x00655C50`），只有**全图重建**（`0x00657CE0`，视角跳转/雷达重置）才逐像素全量。⇒ 真机实测 **`N ≈ 500–1500 / 2s`**（每 2 秒数百至约 1500 次分支进入即属正常态），**仅在全量重绘那一秒**出现 **+3043/s** 量级尖峰。**判据：`N > 0` 且随操作单调增长即 PASS，不再要求「数千～数万/2s」。**
  - 证据：`out/re_work/zcode_live/zc2/RESULT_ZC2.md:28-45`（mode2 实测 16153→17172→17945→19039 ≈1000/2s；mode1 实测 7901→8807→9577→10765；视角跳转×5 中 `jump3` 单秒 `+3043` ≈ 全量重绘，菜单静置 17284→17284 冻结）；Lead 采信记录 `REVERSE_ENGINEERING_AND_PATCHES.md:2372`、`docs/RE_COORDINATION.md:1422`。
- ❌ **FAIL**：`N` 恒 0 且 `M` 恒 0（= ZC-1 旧现象复现）⇒ 见 A.6 阶梯。
- ⚠️ `N > 0` 但 `M == 0`：护栏已放行、但下游护栏（cell 有效性 / `s_visionGrid` token / 表面指针）全拦——回读 `s_visionToken` 与 `s_visionGrid` 在局内是否被填充（可能迷雾更新环未跑）。

### A.4 截图判据（像素级）
对**同一片已撤离区域**拍两张：
1. 「单位在视野内」时：该区域在小地图上**全彩**；
2. 「单位撤离后」：该区域在小地图上**约 50% 亮度灰化**（`shr 1 / & 0x7BEF`），而直视圈内仍全彩。

建议裁剪侧边栏左下小地图框（约 140×108）放大比对；文件命名如 `radarfix_a1_inview.png` / `radarfix_a2_withdrawn.png`。
- ✅ PASS：两张在该区域存在**可见亮度差**，且灰色区域边界与「视野圈残留」形状一致。
- 附加：ZC-1 的旧 FAIL 截图（如 `q3_10_minimapfog_state.png`）可作「改前」基准。

### A.5 负向对照（菜单不得增长）
回到主菜单静置 ≥30 s，再查：

    Select-String -Path ra2youli\ra2render.log -Pattern '雷达灰化' | Select-Object -Last 4

- ✅ PASS：`N`/`M` **不增长**（或菜单期根本没有该行）。这证明新护栏没有把菜单误判成局内。

### A.6 A/B 阶梯（若 A.3 FAIL，用于定位）
按顺序各跑一次 A.2（每次改 ini 后**重启游戏**）：

| 步骤 | `RadarFogGuardMode` | 期望 | 结论指向 |
|---|---|---|---|
| S1 | `0` | `N=0`、`M=0`（复现旧 FAIL） | 证明旧护栏确实拦死 |
| S2 | `2` | `N>0`、`M>0` | 灰化本体（像素通路/表面/vision grid）**正常** ⇒ 问题在谓词 |
| S3 | `1` | `N>0`、`M>0` | ✅ 全链路通过 |
| S3 失败而 S2 成功 | `1` | `N=0` | 谓词过严：请回读 4 个全局原值 ↓ |

**S3 失败时的取证**（用你已有的内存读取通道，任意时刻在局内采一次）：

| 全局 | 期望（局内） | 若不符 |
|---|---|---|
| `*(u32*)0x00A83D4C`（PlayerPtr） | 非 0 且 ≥0x10000 | =0 ⇒ 该战役竟无本地玩家 House（异常，回读 `0x0068ACE9` 是否执行过） |
| `*(u32*)0x00A8B230`（ScenarioClass::Instance） | 非 0 且 ≥0x10000 | =0 ⇒ Scenario 未建（异常） |
| `*(u8*)(0x00A8B230 + 0x3598)` | 0 | ≠0 ⇒ 该关全程处于「加载屏」标志（需去掉此项，明确回报） |
| `*(u32*)0x00A8B238`（GameMode） | 0（战役）/3/4/5 | >5 ⇒ 上界写法需放宽 |

把这张表的实测值回报给 Lead，即可在不改代码的情况下判定是哪一项为假。

### A.7 回报给 Lead 的最小证据集
1. `ra2render.log` 中：`配置来源` 行、`门控` 行、局内最后 8 行 `雷达灰化` 遥测、菜单静置 4 行；
2. A.4 的两张裁剪截图；
3. A.6 四全局实测值（若做过）；
4. 结论：PASS / FAIL + 复现的 mode。

---

*报告结束。*
