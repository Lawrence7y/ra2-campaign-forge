# 下一步逆向方向与源码现代化适配路线

> **2026-10-02 后续派工依据**：以 [PROJECT_DIRECTION.md](PROJECT_DIRECTION.md) 的三条交付线和 P0/P1/P2 队列为准。先收尾当前审计，再围绕真实热点、闪退根因、关键系统行为契约和 DLC 资源/战役/兼容链定向逆向。下文地址结论与优化建议保留为历史输入，热点排序须经有效负载重测，不能直接当作当前优先级。

> 本文承接 `REVERSE_ENGINEERING_AND_PATCHES.md`（L1–L4 已落地部分），
> 基于 2026-09-26 对 `gamemd.exe` 未归因热点的地址级归因，以及 `YRpp/`（181 头文件）
> 社区 ABI 库交叉对照，给出下一阶段「先逆向什么、再改什么、如何现代化」的决策依据。
>
> 与 `docs/REWRITE_ROADMAP.md` 的关系：那篇是重写阶梯（L0–L5），本篇是 **在现有
> `ra2render` 注入通道上继续做增量优化** 的作战图，不重复写重写路线。

---

## 0. 本轮逆向新增结论（可直接写入总档案）

### 0.1 方法

1. 用 `ra2re perf` / loadbench 的 **未归因地址桶**（256 字节对齐）作输入；
2. 对照 `out/reverse/symbols.json` 的 **988 类 / 954 vtable 虚函数地址**；
3. 用 `YRpp/` 头文件里的 `JMP_THIS/JMP_STD(0xXXXXXX)` **具名地址** 反查；
4. 对 `gamemd.exe` 按 PE 节表（`.text` VA=`0x1000`，文件偏移=RVA，ImageBase=`0x400000`）
   回读函数序言与全局访问模式，确认语义。

### 0.2 未归因热点 → 语义归因表

| 地址桶 | 峰值占比 | 归因 | 证据 | 优化含义 |
|---|---|---|---|---|
| `0x7C9300` / `0x7C9200` | 2.4% | **引擎内嵌 CRT**：`malloc/free/new/delete`、`sprintf/vsprintf`、字符串 | `YRpp/CRT.h`：`malloc=0x7C9430`、`free=0x7C93E8`、`_new=0x7C8E17`、`sprintf=0x7C8EF4`；序言扫描命中 `0x7C8EF4` | 分配器/格式化是真热点；LFH 已上，下一步是 **池化 + 减少 sprintf** |
| `0x53E700` / `0x53EB00` | 2.6%+1.0% | **窗口消息 / 输入泵**（`sub_53E3C0/420/6B0`） | `YRpp/Unsorted.h` 声明同名 `sub_53E*`；反汇编访问 `0xAA0448/0xAA044C/0xAA0374` 全局 UI 状态 | 消息循环与 UI 轮询；优先级低于模拟/渲染，勿盲目 hook |
| `0x54F000` | 0.9% | **InputManager / Kamikaze / LaserDraw** 簇 | `YRpp/InputManagerClass.h`、`Kamikaze.h`、`LaserDrawClass.h` 均在 `0x54E–0x54F`；指令含 `+0x318` 位运算 | 特殊武器与输入轮询；高密度超武时值得做 **更新节流** |
| `0x5D4D00` | 1.9% | **MPGameMode / HWND 向量 / 窗口枚举** | `YRpp/MPGameModeClass.h`（`0x5D5B60` 等）；样本落在 `DynamicVectorClass<HWND*>` | 联机模式与窗口遍历；单机局收益有限 |
| `0x48D000` | 0.3% | **地图格子 / Theater 资源查询**（`CellClass` 标志 `+0x3598`） | 指令 `mov cl,[eax+0x3598]`；邻近 `YRpp/Unsorted.h::GetResource`、`Theater.h` | 与 L3/L4 迷雾全量刷 **正相关**；L4 折中方案的主战场 |
| `0x406F00` | 1.0% | **Audio 播放调度** | `YRpp/Audio.h`：`PlayWAV=0x407B60`、`ShutUp=0x406060`，区间 `0x4060–0x407B` | 音效/语音洪泛；可做 **每帧语音上限** |
| `0x531D00` | 0.7% | 大栈函数（`[esp+0x298]`），偏 **AI/任务编排** | 序言 `0x531A0A`，邻接 `0x53E*` UI 区但更深 | 需继续反汇编命名，列入二期 |
| `0x409300` | 1.4% | 小函数簇（`thiscall` 小方法），偏 **对象工厂/初始化** | 序言 `0x408F14` | 二期命名 |
| `0x623100` | 0.1% | **数据表 / 跳转表**（非代码热） | 字节为连续小常量 + NOP | 采样噪声，可忽略 |

### 0.2.1 冲刺结论（S9）：未归因热点函数定谳

> 本节由 S9 专项冲刺（2026-09-26）基于 `ra2youli/gamemd.exe` 全指令级与 RTTI 逆向直接追加，对 §0.2 既有未归因热点实施逐一闭环定谳。完整取证报告与反汇编实证详见 [re_sprint_S9_report.md](file:///d:/Project/ra2-campaign-forge/docs/re/re_sprint_S9_report.md)。

#### 1. 勘误 + 新旧对照总表

| 地址桶 | §0.2 旧归因与推测 | S9 新定谳结论 | 证据等级 | 修正原因与取证事实 | 现代适配决策调整 |
|---|---|---|---|---|---|
| `0x531D00` | 大栈函数（`[esp+0x298]`），偏 **AI/任务编排** | **`Init.CPP` 启动版本与背景对话框**（`Init_Version_Dialog`） | `[实证]` | 硬编码字符串 `D:\ra2mdpost\Init.CPP`（VA `0x825FB8`），对话框 ID 212/226，800×600 居中计算，格式化 MMX/版本信息 | 移出 AI 优化路线；单次启动生效，无需 Hook |
| `0x409300` | 小函数簇（`thiscall`），偏 **对象工厂/初始化** | **`StreamBuffer` 原语 + `Clock::Now` QPC 定时器** | `[实证]` | `0x4092B0–0x409354` 为流重置/冲刷/未读字节统计；`0x409360–0x4093EE` 为 `QueryPerformanceCounter` + CRT `_alldiv` 定时器派发 | 热点源于全局每帧高频查时（`Clock::Now`），绝非工厂构造频繁；可评估定时器帧级缓存 |
| `0x48D000` | **地图格子 / Theater 资源查询**（`CellClass` 标志 `+0x3598`），L4 迷雾主战场 | **`Game::CallBack` 全局多任务泵**（音频推进 + 网络加载进度同步） | `[实证]` | `[eax+0x3598]` 是 `ScenarioClass::Instance`（`0xA8B230`）的 `IsLoadingScreen`，解包 0x6C 进度更新 `ProgressScreenClass`（`0xAC4F58`） | **严禁在此挂迷雾钩子**；迷雾优化应 100% 收口于 `TacticalClass::Render` 与视野更新环 |
| `0x623100` | **数据表 / 跳转表**（非代码热），采样噪声可忽略 | **`CommonDialogProc` 跳转表 + `UI::Updated()` 轮询入口** | `[实证]` | 表为 `0x622B50` 的 switch 索引；`0x623120` 即 `UI::Updated()` 真实代码，高频轮询 `MainLogicFrame` | 不可作为噪声忽略；模态循环与视频跳帧时此为关键消息泵 |
| `0x437300` | 图形 / SHP / 绘制管线相关函数（未具名） | **`Surface::Put_Rect`**（局部表面还原包装器） | `[实证]` | 栈上构建 `BSurface`（`0x7E2070`），将内存 `XSurface` 还原至 `DSurface::Hidden_2`，由 `StaticButtonClass::Draw`（`0x6C6740`）调用 | 属于 UI 脏区还原链路，与大地图 SHP 渲染解耦 |
| `0x432E00` | 图形 / SHP / 绘制管线相关函数（未具名） | **`BinkMovieClass::Play`**（视频播放泵与跳过判定） | `[实证]` | 依赖 `binkw32.dll`，循环检测 `InputManagerClass`（`0x87F770`）按键 `0x081B`（ESC）退出 | 属于过场动画播放器，单机/联机对局内非持续热点 |

#### 2. 五大热点定谳核心实证

1. **`0x00531D00`（启动对话框与版本格式化）**：
   - 包含两大函数：`Version_Dialog_Proc`（VA `0x00531A00`，FileOffset `0x131A00`）开辟 `sub esp, 0x288`（648 字节）大栈帧，加 4 个保护寄存器总深 `0x298`，用作 `sprintf` 版本信息（`"Version %s"`, `"Internal Version %s"`, `"Release Build: %s by %s - %s"`, `"MMX %s, Vendor: %s"`, `"TXT_SHORT_TITLE"`）的格式化缓冲区；
   - 对话框构建器 `Init_Version_Dialog`（VA `0x00531CC0`）在 `0x00531D37` 读取 `0x8A00A4`（ScreenWidth）与 `0x8A00A8`（ScreenHeight），按 `(Width - 800)/2` 居中对话框，并根据分辨率载入 `"Ra2ts_s"` / `"Ra2ts_l"` 背景 SHP。全链路硬编码源码路径 `D:\ra2mdpost\Init.CPP`（VA `0x00825FB8`），**完全排除 AI/编排属性**。
2. **`0x00409300`（流 I/O 原语 + 高精度时钟）**：
   - `0x004092B0–0x00409354` 包含 `Stream::Reset` (`0x4092B0`)、`Stream::Flush` (`0x4092F0`)、`Stream::Get_Available_Count` (`0x409310`)、`Stream::Get_Unread_Bytes` (`0x409320`) 等底层 I/O 方法，服务于 Win32 消息流（`0xAA0460`/`0xAA0464`）；
   - `0x00409360–0x004093EE` 为引擎核心定时器：`Clock::Init` (`0x409360`) 通过 `QueryPerformanceFrequency` + CRT `_alldiv` 计算每毫秒计数值；`Clock::Now` (`0x4093B0`) 动态派发跳转至 `Clock::ReadQPC` (`0x4093C0`) 调用 `QueryPerformanceCounter`。全镜像有 50+ 处核心循环高频调用 `Clock::Now`，1.4% 峰值实为系统计时开销。
3. **`0x0048D000`（Game::CallBack 全局后台泵）**：
   - 指令 `mov cl, [eax + 0x3598]` 中 `eax` 实为 `ScenarioClass::Instance`（全局基址 `0x00A8B230`），`+0x3598` 为 `IsLoadingScreen` 布尔标志；
   - 处于加载期时，从网络流接收协议号 `0x6C`（`'l'` = LOAD_PROGRESS）数据包，提取远端玩家进度浮点百分比，并调用 `ProgressScreenClass::Instance`（全局基址 `0x00AC4F58`）的方法 `0x00643C50` 刷新进度条；
   - 随后的 `0x0048D080` 即为全镜像 100+ 处调用的 `Game::CallBack`，内部推进音频更新（`0x00406F70`）与网络探测保活（`0x0048D1E0`）。**与 MapClass / CellClass / 迷雾全量刷 0% 关联**。
4. **`0x00623100`（跳转表与 UI::Updated 轮询入口）**：
   - `0x006230DC–0x006230EF` 为 `CommonDialogProc`（`0x00622B50`）的 5 项 32 位跳转地址表；
   - `0x006230F0–0x00623119` 为 42 字节的 `uMsg` 稀疏 case 映射表；
   - `0x0062311A–0x0062311F` 为 6 字节 NOP（`0x90`）对齐填充；
   - `0x00623120–0x0062315F` 紧接其后，即为 `UI::Updated()`（`YRpp/UI.h:24`），高频轮询 `MainLogicFrame (0x55D360)` 与 `Game::CallBack (0x48D080)`，0.1% 采样实为该轮询代码执行消耗。
5. **`0x00437300` 与 `0x00432E00`（图形管线辅助方法）**：
   - `0x00437300`：位于 `Surface::Put_Rect`（VA `0x00437290–0x00437340`），在栈上构造 `BSurface`（vftable `0x007E2070`，RTTI `.?AVBSurface@@`），通过虚表调用 `Surface::Blit` 将内存 `XSurface` 还原至 `DSurface::Hidden_2`（`0x00887314`），由 `StaticButtonClass::Draw`（`0x006C6740`）调用；
   - `0x00432E00`：位于 `BinkMovieClass::Play`（VA `0x00432C70–0x00432E39`），循环调用 `binkw32.dll` 解压帧并 Blit 上屏至 `DSurface::Primary`（`0x00887308`）；尾部调用 `InputManagerClass::Instance`（`0x0087F770`）检测跳过键（`0x081B` / ESC），实现视频中途跳过。

#### 3. 现代化适配路线修正

1. **废弃针对 `0x48D000` 的迷雾优化假设**：P0-2（L4 视野脏区折中）应纯粹在 `TacticalClass::Render`（`0x6D3D99`）与视野更新环实施，切勿修改 `Game::CallBack`（`0x48D080`），防止破坏音频混音心跳与联机保活；
2. **时钟查询平滑（新增 P1 建议）**：`0x409300` 实证为 `QueryPerformanceCounter`，针对同一逻辑 Tick 内成百上千次的密集时间戳查询，可评估单 Tick 毫秒级时间戳缓存，减轻内核态切换开销；
3. **安全免 Hook 判定**：`0x531D00`（启动对话框）、`0x437300`（按钮背景恢复）、`0x432E00`（视频播放）均不在局内对战核心热循环中，予以封存，免于 Hook。

---

### 0.3 对「现代 CPU 单核不满却掉帧」的再确认

U200/U800 剖析里 `gamemd` 真正忙时的构成大致是：

```text
软件 Blit 族  ████████░░░░░░░░  已 Hook 6/108，仍有 RLE/Lucent/ZRead 缺口
CRT 分配/格式化 ████░░░░░░░░░░░░  几乎未动
格子/迷雾绘制   ███░░░░░░░░░░░░░  L4 全量刷会放大这一块
寻敌 O(N²)     ██░░░░░░░░░░░░░░  已节流 8 帧，未根治
音频/UI/输入    ██░░░░░░░░░░░░░░  次要
```

**结论**：下一波收益最大的不是继续堆 SIMD 微内核，而是  
**（A）补全 Blit 覆盖面 →（B）L4 脏区折中 →（C）分配器/字符串 →（D）寻敌空间索引**。

---

## 1. 现代化适配总原则（针对二进制注入通道）

| 原则 | 做法 | 反例 |
|---|---|---|
| **ABI 单一来源** | 地址/偏移统一收进 `ra2render/abi_*.h`，由脚本从 `YRpp` + `symbols.json` 生成 | 散落魔法数 `0x5D4`、`0x6C` |
| **类型安全钩子** | 新代码允许 `#include` YRpp 头（仅头文件、`JMP_*` 转发），用 `TechnoClass*` 而不是 `void*` | 继续 `IsBadReadPtr` + 裸偏移 |
| **行为契约锁** | 每项 Hook 必须有：原行为描述、回放对拍、回滚开关 | 「改完手感对了就行」 |
| **可观测** | `ra2render.ini` 遥测扩展：按 hook 统计调用/耗时/节流率 | 只有总量 `totalBlits` |
| **不碰契约层** | 不改触发器语义、随机数、寻敌胜负判定顺序 | 并行化模拟（L4 路线图里的最后项） |

### 1.1 建议落地的 `abi` 生成脚本（很小，收益大）

```text
tools/gen_abi.py
  读 YRpp/*.h 的 JMP_THIS(0x...) + 类名
  读 out/reverse/symbols.json 的 vtable/vfunc
  读 ra2re 的 m1_blit_targets.txt
  写出 ra2render/abi_generated.h  （全部 constexpr + 静态断言）
```

这样 hook 代码里可以写：

```cpp
static_assert(ABI::Techno::Target == 0x5D4);
// 而不是 magic 0x5D4
```

---

## 2. 优化路线（按 ROI 排序，每项独立可测）

> 验收一律沿用你定下的门槛：**U200/U800 回放三局，7200–14400（或实测高密度段）平均帧  
> +≥2，或 CPU0 −≥5%**；不达标回滚。一次只动一项。

> **【勘误 2026-09-29 · MIMO-H1VOID】上段验收门槛与下表 P0-1「+5～12%」、P0-3「+3～8%」的收益预估，其负载前提不成立，重测前不得引用。**（原文保留，不删字）
> **依据**：旧基准图 `[2]0LoadBench_U0200/U0800.yrm` 的 200/800 预置单位全挂在 `Russians`/`Americans`；遭遇战（`MultiplayerOnly=1`）只实例化玩家槽 house 的对象 ⇒ 真机仅 **21/22 单位**（= `HouseClass::RespawnStartingForces` 0x50D440 国家默认开局部队），**不是地图负载**。
> **指向**：替代图已产出 —— `out/loadbench/[2]0LoadBench_U{0050,0200,0800}_H1.yrm`（14-house fanout，任意 2 槽 × target/2 = 目标负载），见 `docs/re/bench_map_rework.md` 与 `out/loadbench/H1_REMEASURE_RUNBOOK.md`。
> **处置**：P0-1 / P0-3 的百分比预估**标记为作废**；待 H1 图重测后按实测数据回填。P0-2 不含百分比预估，其技术路线不受影响。

### P0（本周可做，收益确定）

| # | 项 | 逆向对象 | 改法 | 预估 | 风险 |
|---|---|---|---|---|---|
| P0-1 | **补全 RLE 步兵 Blit** | `m1_blit_targets.txt` 中 `RLEBlit*` 51 个，现只 Hook 了 2 个 | 优先 `RLEBlitTransDarkenZRead`、`RLEBlitTransLucent*`（loadbench 已见 `RLEBlitTransXlat@E` 进 Top） | 高密度局 +5～12% | 中（RLE 解码要与原版像素一致） |
| P0-2 | **L4 全量刷 → 视野脏区折中** | `TacticalClass::Render` 已在 `0x6D3D99` 强制全量；`0x48D000` 显示格子标志在拖后腿 | 仅当 `s_visionToken` / 本帧 `UpdateVisionGrid` 变动格打 dirty，或按「视野环外扩 1 格」重绘 | 抵消 L4 回归，保住迷雾即时性 | 中（需重扫 Render 内 dirty 标记写入点） |
| P0-3 | **L2 空间哈希代替纯节流** | `SelectAutoTarget` / `Greatest_Threat` 已知虚表；目标列表仍是 O(N²)/8 | 建 `CellSpread` 网格（YRpp 已有 `CellSpread.h` 语义），查询只扫邻域 | 高密度逻辑帧 +3～8%，且不再「开火发呆」 | 中高（必须回放对拍攻击顺序） |

### P1（一～两周，结构升级）

| # | 项 | 逆向对象 | 改法 | 预估 | 风险 |
|---|---|---|---|---|---|
| P1-1 | **CRT 分配池** | `0x7C8E17/_delete`、`malloc/free` | 对粒子/弹丸/临时 `sprintf` 缓冲做 freelist；统计高频 size | 抖动减少，帧稳定 | 低（已有 LFH） |
| P1-2 | **字符串/格式化削减** | `sprintf=0x7C8EF4` 落在热点桶 | UI/调试/日志路径改预格式化；禁用每帧 `sprintf` | 0.5～2% | 低 |
| P1-3 | **音频语音限流** | `0x4060–0x407B` Audio 簇 | 每帧/每 100ms 最多 N 条 Play；同 ID 去重 | 卡顿毛刺减少 | 低 |
| P1-4 | **Blit 家族按调用频次排序补全** | 108 个里还剩 ~100 | 遥测统计「每函数调用数 × 像素」，只加速 Top 10 | 剩余渲染缺口 | 中 |
| P1-5 | **YRpp 化改造 `blitter_hooks.cpp`** | 全文件 1100+ 行裸地址 | 拆 `abi_generated.h` + `hooks_render.cpp` / `hooks_ai.cpp` / `hooks_fog.cpp` | 可维护性 | 低 |

### P2（有余力再做）

| # | 项 | 说明 |
|---|---|---|
| P2-1 | 渲染/逻辑解耦（L1 Tier3） | 双缓冲 + 插值，体感提升最大，但工作量数周 |
| P2-2 | GPU 批渲染（L1 Tier2） | 在 RLE/Blit 覆盖稳定后再上 |
| P2-3 | 寻路缓存 / 流场 | 必须 oracle 对拍，影响手感 |
| P2-4 | `0x531A` / `0x408F` 命名逆向 | 二期热点归因 |
| P2-5 | 裂缝产生器 / 间谍卫星机制完善 | 挂在 `UpdateVisionGrid`，与 P0-2 同一文件可顺带 |

---

## 3. 「现代化适配」具体清单（工程侧）

### 3.1 代码结构目标

```text
ra2render/
  abi_generated.h          ← 工具生成，禁手改
  hooks/
    render_blit.cpp        ← L1，按 blit 族拆
    ai_targeting.cpp       ← L2
    fog_vision.cpp         ← L3 + L4 dirty 折中
    audio_limit.cpp        ← P1-3
    heap_pool.cpp          ← P1-1
  runtime/
    telemetry.cpp
    config.cpp
  dllmain.cpp
```

### 3.2 与 YRpp 的三种协作级别（由浅入深）

1. **只读符号源**（当前推荐）：生成 `abi_generated.h`，不把 YRpp 编进 DLL。  
2. **头文件 include**：hook 内用 `TechnoClass`/`CellClass` 布局，`static_assert` 偏移。  
3. **Phobos 风格扩展**：若未来要改玩法（裂缝反制、超武），再考虑完整 YRpp 链接。

### 3.3 测试与回滚（必须齐套）

- [ ] `ra2render.ini` 每个 hook 独立开关  
- [ ] U200/U800 回放脚本：三局平均帧 + CPU0 + Tick Miss 次数  
- [ ] 像素对拍：对同一帧截图与原版 diff（迷雾/半透明允许容差）  
- [ ] `ra2opt restore` 与 `ra2render` 卸载路径互不破坏  
- [ ] 所有新逆向按总档案第九节模板登记  

---

## 4. 建议的立即执行顺序（下一次工作会话）

```text
1) 生成 abi_generated.h（把 0x5D4 / 0x6C / blit 虚表收口）
2) P0-1 补 RLE 步兵 Top3 Blit → 回放测帧
3) P0-2 L4 视野脏区折中 → 回放测帧 + 迷雾即时性手测
4) P1-2 去掉每帧 sprintf → 回放测帧
5) 再决定是否上 P0-3 空间哈希寻敌
```

每步完成后在 `REVERSE_ENGINEERING_AND_PATCHES.md` 追加版本号条目。

---

## 5. 一句话总结

| 问题 | 答案 |
|---|---|
| 下一步该逆向什么？ | **RLE Blit 族、Render 的 dirty 写入点、CRT 分配调用图、`SelectAutoTarget` 邻域结构** |
| 下一步该优化什么？ | **Blit 覆盖面 → L4 脏区折中 → 分配/格式化 → 寻敌空间索引** |
| 如何现代化？ | **YRpp 生成 ABI 头 + hooks 按域拆分 + 每 hook 可关可测 + 禁手改魔法数** |
| 不要做什么？ | 并行化模拟核心、无对拍改寻路、无门槛地堆 SIMD |

---

## 6. S9 冲刺收尾与定谳索引

> 本文 §0.2 中的 5 大未归因热点已在 S9 专项冲刺（2026-09-26）中实现 100% 实证闭环，定谳详情见原地追加小节 [§0.2.1 冲刺结论（S9）：未归因热点函数定谳](#021-冲刺结论s9未归因热点函数定谳)；完整反汇编证据与分析全貌见专项报告 [re_sprint_S9_report.md](file:///d:/Project/ra2-campaign-forge/docs/re/re_sprint_S9_report.md)。
