# 时钟 / 帧循环 / 空桩调用簇 逆向档案

> 逆向对象：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，文件偏移 = VA − `0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 目标：① Clock 体系（`0x4093B0` 真热 / perf `0x409300` 桶）② `0x4068E0` 空桩 1672 直呼聚类 ③ 帧主循环顶层链 ④ `timeBeginPeriod(1)` 与 Sleep ⑤ 优化建议
> 方法：Capstone 5.x 全文 `.text` 单遍扫描（68253 `call` / 15006 `jmp` / 4601 间接）+ IAT 反查 + `out/reverse/symbols.json` vfunc 命名 + YRpp 交叉对照
> 工作产物：`out/re_work/clock_frame/`（脚本 `analyze_clock_frame.py` / `analyze_pass2.py` / `analyze_pass3.py` 及各 `disasm_*/skel_*/callers` 文本）
> 约束：只读逆向，不改 `REVERSE_ENGINEERING_AND_PATCHES.md` 与任何源码/dll。
> 前置文档：`docs/re/nonrle_blit_and_named_hotspots.md`（§3.2 Clock 簇首提）、`docs/re/audio_input_hotspots.md`（§1.1 空桩、§1.2 AudioFrameUpdate）、`docs/re/dirty_rect_l4.md`（§5.2 `+0x3598` 门控）

---

## 0. 结论速览

| # | 命题 | 结论 | 热度 |
|---|---|---|---|
| 1 | **perf `0x409300` 桶 = Clock 真热** | **确认**。`0x4093B0/Clock::Now` 是 35 处直呼的高精度时间源（QPC/timeGetTime 双路径），音频、渲染、主循环、主题音乐都取它 | **真热** |
| 2 | **`0x4068E0` 空桩 = 发行版掏空的 printf 日志宏** | **确认**。1 字节 `ret`，1672 处 `push fmt; call; add esp,N` 直呼，fmt 全是 `.rdata` 诊断串（`Missing sample %s\n` 等），**0 处数据指针**（不进 vtable） | **伪热点**（每次 1–2 周期） |
| 3 | **帧主循环链** | `0x6BE000`（启动）→ `0x48CCC0 GameRunner` → `0x52BA60 GameStart` + `0x52D9A0 GameMainLoop`（状态机）→ **`0x55D360 MainLogicFrame`（每逻辑帧，`CurrentFrame++` 在此）** → `0x55E160 LogicUpdate` | — |
| 4 | **逻辑帧号推进点** | **全镜像仅 10 处写 `0xA8ED84`**，唯一 `inc` 在 `0x55DE73–0x55DE81`（`0x55D360` 尾部）。其余 9 处是清零/存读档回填 | — |
| 5 | **Clock 与 GameSpeed/FrameDelay** | **两条独立时间线**：`Clock::Now`（墙钟 64 位，音频/测时）≠ `CurrentFrame`（逻辑帧号）。**帧节拍用的是 `timeGetTime` 直呼**（经 `0x5D5890` 薄桩），不是 `Clock::Now` | — |
| 6 | **`timeBeginPeriod(1)`** | 引擎自带 3 对封装（`0x5D5870/0x5D5880/0x5D5890`），在 `0x55D360/0x55E160` 里**成对包裹计时测量**；ra2render 的常驻 1ms 是加强版，使 `Sleep(10)` 从 ~15.6ms 抖动降到 ~10ms | — |
| 7 | **空桩能否 nop** | **可安全忽略/短路**（语义零变化），收益 <0.2%。改成遥测计数点**不建议全量做**（见 §2.4 风险） | — |
| 8 | **帧循环冗余** | `0x48D080` 每逻辑帧被 `0x55D360` + `0x55E160` **各调一次**；`0x55D360` 的 `Sleep(10)` 是固定值，不随帧耗时自适应 | 有肉 |

---

## 1. Clock 档案（`0x409360–0x40946A`）

### 1.1 函数表（已全量反汇编：`out/re_work/clock_frame/disasm_clock.txt`）

| 地址 | 建议名 | 职责 | 证据 |
|---|---|---|---|
| `0x00409360` | **`Clock::Init`** | `QueryPerformanceFrequency`→`0x7C92D0` 定点缩放，结果存 `0x87E828/0x87E82C`；安装函数指针 `0x87E848 = 0x4093C0`（QPC 成功）或 `0x4093F0`（QPF 失败回退） | IAT `0x7E11D8=QueryPerformanceFrequency` |
| `0x004093B0` | **`Clock::Now`** | `mov eax,[0x87E848]; test; jmp eax`，指针为空则返回 `edx:eax = 0`。返回 **64 位时间** | **perf `0x409300` 桶热点本体** |
| `0x004093C0` | `Clock::NowQpc` | `QueryPerformanceCounter` → `0x7C92D0` 缩放（用 `0x87E828/2C` 系数）→ `edx:eax` | IAT `0x7E11D4=QueryPerformanceCounter` |
| `0x004093F0` | `Clock::NowTick` | `timeGetTime` 回退：`0x87E84C` 自增作序列号，双读 `timeGetTime` 与 `0x7E1760/0x7E1764` 间接槽对齐，处理 32 位回绕（`jae` 则 `inc edi`）；`0x40941E` 为自旋等待（两读 `0x87E84C` 不等则空转） | IAT `0x7E1530=timeGetTime` |
| `0x7C92D0` | `ScaleToMs`（暂名） | 64 位定点缩放原语，被 `Clock::Init/NowQpc` 及 `0x406670` 调用 | 3 处直呼 |

**函数指针安装**：全镜像对 `0x87E848` 只有 3 处引用 —— `0x409393`（写 QPC 路径）、`0x4093A1`（写 Tick 路径）、`0x4093B0`（读+间接跳）。**唯一安装者是 `Clock::Init`**，而 `Clock::Init` 的唯一调用者是 **`0x406B10`（音频子系统 bootstrap）**。

### 1.2 `Clock::Now` 调用者全景（35 处直呼，按域聚类）

完整清单：`out/re_work/clock_frame/clock_now_callers.txt`。

| 域 | 宿主函数 | 直呼数 | 频率 | 说明 |
|---|---|---|---|---|
| **音频** | `0x406F70 AudioFrameUpdate` | 1 | **每 UI 帧**（内建 33ms 门） | 节流比较用 |
| 音频 | `0x4055C0`（经 `0x4041D0` 样本链表） | 3 | 每音频 tick | 样本衰减计时 |
| 音频 | `0x4070B0/0x407100/0x407170/0x4071C0` | 2+1+1+1 | 事件/每帧 | AudioController 时戳 |
| 音频 | `0x407550/0x407860/0x407B60/0x4080F0` | 1+2+1+2 | 流播放 | WAV/主题流 |
| **游戏主循环** | **`0x52D9A0 GameMainLoop`** | **4** | 每状态分支 | 帧间隔测量 |
| 游戏主循环 | `0x52BA60 GameStart` | 2 | 启动一次 | 初始化时戳 |
| **渲染** | `0x6D4B50`（在 `TacticalClass::Render@0x6D3D10` 内） | 2 | 每渲染帧 | 帧耗时/滚动插值 |
| 音乐 | `0x752760 ThemeTick` | 1 | 每音频 tick | 主题曲推进 |
| 其它 | `0x53DE00`（`0x6BB9A0` 调用）、`0x5312A0`、`0x409880/0x409C40`（内部递归） | 1+1+1+1 | 低频 | — |

**关键发现（与既有文档的细化）**：
1. `0x4093B0` 的间接跳 `jmp eax` **没有静态 xref**，全靠 35 处直呼；`call [0x87E848]` 形式 **0 处**——所有调用都写死 `call 0x4093B0`，由后者再间接。这简化了 hook（只需 patch `0x87E848` 或 `0x4093B0` 本体）。
2. **逻辑帧节拍不用 `Clock::Now`**：`0x55D360/0x55E160` 的帧间隔测量走 `timeGetTime` 薄桩 `0x5D5890`（`jmp [0x7E1530]`）。`Clock::Now` 是音频/测时/渲染的高精度墙钟，与 `CurrentFrame` 解耦。
3. `0x4093F0/NowTick` 的 32 位回绕处理表明 timeGetTime 回退路径是**为长局（>49.7 天）准备的**，实际 Windows 上 QPC 几乎总成功，该路径冷。

### 1.3 与 GameSpeed / FrameDelay / CurrentFrame 的关系

```
Clock::Now (0x4093B0)          CurrentFrame (0xA8ED84)
  = 墙钟，64 位，单位≈ms/µs       = 逻辑帧号，int，每 MainLogicFrame 自增 1
  用途：音频 33ms 门、样本衰减、   用途：TimerStruct、动画、触发器、
        渲染帧耗时、主题曲               寻路延迟、Kamikaze 30 帧更新…
        ↓ 不驱动                    ↓ 由 0x55DE73 inc
  GameSpeed / FrameDelay 走第三条线：timeGetTime (0x5D5890) + 0x887328/0x887330 间隔
```

| 全局 | 含义 | 引用热度 |
|---|---|---|
| `0xA8ED84` | `Unsorted::CurrentFrame` | **1007 处引用**，10 处写 |
| `0xA8E7AC` | 会话代数/重入计数（`0x52E0BE` inc / `0x52E0D0` dec 包住 `0x52CB90`） | 292 处 |
| `0x829FF4` / `0x829FF8` | `MinFrameRate` 对（YRpp `FPSCounter.h`） | 3 处，全在 `0x55AF60` |
| `0xABCD44` | `FPSCounter::CurrentFrameRate` | 12 处 |
| `0xABCD50` | FPS 迟滞标志（`0x55AF60` 内翻转） | 3 处 |
| `0x887328/0x887330` | 逻辑帧节拍：上次 timeGetTime / 目标间隔 | `0x55E160` 专用 |
| `0xA8E2E4` | 帧号阈值（`CurrentFrame >= 此值` 则 `call 0x69A300`） | `0x55D3CA` |
| `0xA8B55C/0xA8B560/0xA8B564` | 帧耗时记账：`timeGetTime` 快照 / 累计 ms（上限 0x3E8）/ 帧计数 | `0x55D3D4–0x55DE3A` |
| `0xA8ED80` | 「快进/跳过 Sleep」标志（=1 时 `0x55D360` 跳过 Sleep 块） | — |
| `0xA8E9A0` | 局内标志（=0 时 `0x55D360` 直接早退） | — |
| `0xA8B238` | `SessionClass::Instance` 首成员 **`GameMode`**（`SessionClass.h:54` = `reference<SessionClass,0xA8B238u>`）〔勘误 2026-09-27：原记「0=菜单, 3/4=局内, 5=加载」**错误**〕——枚举 `GameMode { Campaign=0, LAN=3, Internet=4, Skirmish=5 }`（`GeneralDefinitions.h:670-675`，与真机实测 campaign=0 / skirmish=5 完全吻合；`0` 亦由退局路径反复写入 ⇒ **不可作「菜单/局内」判据**）| **571 处** |

**FPS/细节档位**（`0x55AF60`，由每帧 `0x55AFB0` 间接驱动）：
```
if (ABCD50) {  // 上帧已降档
    if (CurrentFrameRate(ABCD44) >= MinFrameRate(829FF4) + 829FF8)  ABCD50 = 0;  // 回升
} else {
    if (CurrentFrameRate < MinFrameRate)  ABCD50 = 1;  // 降档
}
```
这是 **Detail 级别迟滞**，不是 GameSpeed 本体。GameSpeed 数值在 `GameOptionsClass::GameSpeed` / `SessionClass::GameSpeed`（YRpp），经 `0x887330` 目标间隔影响 `0x55E160` 的节拍（映射公式见 §6 未决 2）。

---

## 2. 空桩聚类（`0x4068E0`，1672 直呼）

### 2.1 定性：发行版掏空的 printf 式日志/断言宏

**桩体**（`out/re_work/clock_frame/disasm_clock.txt` 旁证）：
```
004068E0  c3                   ret          ; ← 全部内容
004068E1  90 ... 90            nop×15      ; 对齐到 0x4068F0
004068F0  ...                  ; 下一个真函数（小循环分发器 call ebx N 次）
```

**调用形态**（抽样 40 个宿主函数，`stub_caller_samples.txt`）——**高度一致**：
```asm
push esi                  ; 可选参数
push 0x816218             ; .rdata 格式串
call 0x4068E0             ; ← 空 ret
add esp, 8                ; cdecl 清栈
```

**fmt 串实锤**（`0x8161E8` 一带）：

| 地址 | 字符串 |
|---|---|
| `0x8161E8` | `event mempool size = %d\n` |
| `0x816218` | `Missing sample %s\n` |
| `0x81628C` | `Unable to change the priority of the Streamer Thread - %s\n` |
| `0x8162D8` | `%s access to stream failed. Access already acquired.\n` |
| `0x816310/0x816318` | `Read` / `Write` |

**三条硬证据**：
1. **0 处数据指针**：全镜像扫描 `0x4068E0` 的绝对 dword 出现 **0 次** —— 它**不进 vtable、不作回调安装**，排除「空虚函数默认实现」与「COMDAT 折叠空方法」（那些会在 vtable 里留下地址）。
2. **调用约定是 cdecl varargs**：`push fmt; call; add esp, N`，与 `printf(fmt, ...)` / `WWDebugPrint` / `DEBUG_LOG(...)` 完全同构。
3. **参数全是诊断语义**：缺样本、流访问失败、线程优先级、内存池大小——**错误路径/调试输出**，不是业务参数。

**结论**：这是 Westwood 典型的 `DEBUG_LOG` / `WWASSERT` 宏在 **Release 编译时被定义为空函数** 的残留。调用点是宏展开留下的 `call`，不是程序员手写的空回调。命名建议 **`DebugLogStub` / `noop_printf`**。

### 2.2 调用者聚类（1672 处 / 424 个宿主函数）

完整清单：`out/re_work/clock_frame/stub_4068E0_callers.txt`。

| 域（按宿主 VA） | 代表宿主 | 呼数 | 主要 fmt 语义 |
|---|---|---|---|
| **音频/流** `0x40xxxx–0x41xxxx` | `0x403ED0`、`0x4064A0`、`0x407550`、`0x408C30`、`0x411650/0x411B20` | ~80 | `Missing sample`、`Streamer Thread`、`stream failed` |
| **CD/文件/MIX** `0x479xxx–0x481xxx` | `CD::v[2]@0x4791F0`（**x47**）、`0x47A080`（x22）、`0x481A00`（x16） | ~120 | CD 扇区/MIX 目录诊断 |
| **网络** `0x54xxxx`、`0x7Bxxxx` | `IPXInterfaceClass::v[15]`（x19）、`UDPInterfaceClass`、`WinModemClass`、`NullModemClass` | ~80 | 连接/包诊断 |
| **UI / 地图 / 建筑** `0x5Bxxxx–0x5Fxxxx` | `0x5B4EE0/0x5B82F0/0x5B8CE0`（各 x20）、`0x5F0690/0x5F1FA0/0x5FA620` | ~200 | 触发器/地形/侧栏 |
| **游戏主循环/启动** | **`0x52BA60` x33**、`0x48D1E0` x10、`0x52D9A0` x8、`0x53DE00` x1 | **52** | 启动步骤/状态迁移日志 |
| **地图/渲染** `0x64xxxx–0x6BBxxx` | `0x6BB9A0`（**x69**，最大单宿主）、`0x64C380`（x14） | ~150 | 脏矩形/绘制诊断 |
| 其余（COM/ATL、MPCooperative、WWMouse、多播） | `?$CComObject@VCChatEventSink@@`、`WWMouseClass`、`MPCooperative` | ~200 | — |

**页直方图 Top**：`0x6BB000` x63、`0x479000` x45、`0x5F2000` x44、`0x47A000` x36、`0x795000` x36 —— **无单一热点页**，是全域诊断残留。

### 2.3 是否落在每帧环里

| 问题 | 答案 |
|---|---|
| 空桩是否每帧被调？ | **部分**。已知热/循环函数内共 **52/1672（3.1%）**：`0x52BA60` x33（启动一次）、`0x48D1E0` x10（状态分发）、`0x52D9A0` x8（主循环状态机）、`0x53DE00` x1。**每逻辑帧稳定执行的只有 `0x52D9A0`/`0x48D1E0` 内约 10–18 处**，其余多在错误分支 |
| 是宏/断言残留？ | **是**（§2.1） |
| 能否安全 nop / 忽略？ | **能**。空 `ret` 不改任何寄存器/标志（x86 `ret` 只动 `esp/eip`），调用方 `add esp,N` 自行清栈。**语义零变化**。但 5 字节 `call` 改 `nop`×5 或改 `add esp,N` 后跳过，二选一即可，不必两者都做 |
| 性能收益 | **<0.2%**。每次 1–2 周期；即便每帧 20 次也只是 ~40 周期/帧，淹没在 `0x5D4D50` 消息泵里 |

### 2.4 若改为遥测计数点的风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| **eax/edx 未定义** | `ret` 不写返回值；少数调用点若读 `eax` 会拿到垃圾。**未逐点验证 1672 处是否都不读返回值** | hook 时保持 `ret` 语义（不写 eax），或先全量扫描「call 后 3 条指令是否读 eax」 |
| **冷路径稀疏** | `Missing sample` / `stream failed` 只在错误时触发，计数长期为 0，遥测无信息量 | 只对**已知热路径的 18 处**做计数，不全量 |
| **启动洪泛** | `0x52BA60` 一次启动就 33 处，若计数器有原子/锁开销，启动期会被放大 | 用 `static uint32_t` 非原子递增（单线程诊断） |
| **格式串解析** | 若「改遥测」=「真 printf」，会引入 I/O、锁、性能悬崖；`0x52BA60` 启动路径日志可能上千行 | **绝不要**把桩变成真 printf；只做聚合计数 |
| **联机同步** | 空桩无副作用，改有副作用后**不得**进确定性路径的副作用（如改 RNG/分配器） | 计数器放独立遥测区，不进存档/回放 |

**建议**：保持空桩不动；若要遥测，在 **ra2render hook 层**对 `0x52D9A0` 内那 8 个 call 点（或对 `0x4068E0` 本体做采样桩）做**每帧聚合计数**，并用 ini 开关。

---

## 3. 帧循环图

### 3.1 顶层地址链

```
PE entry 0x7CD80F (CRT startup)
  └─ … 应用初始化 … 0x406B10 AudioBootstrap
        └─ 0x409360 Clock::Init     ★安装 0x87E848
  └─ 0x6BE000 区  应用主入口（0x6BE02F 检查 0xA8F7AC 分流）
        ├─ 0x6BE041 / 0x6BE061  call 0x48CCC0   GameRunner
        └─ 0x6BE07F  atexit/SetUnhandledExceptionFilter(0x6BB990)

GameRunner 0x48CCC0   —— 一局游戏的外层（0x48CCC3 开 0x1C28 字节栈）
  ├─ 0x48CCCF  call 0x52BA60        GameStart / SessionSetup
  │      ├─ … 构造 ScenarioClass(0x6832C0)、装载规则、输入清空 …
  │      ├─ 0x52CA37 / 0x52CA4E     Clock::Now ×2（启动时戳）
  │      └─ 0x52CB77  jmp 0x48D080  尾调用 Game::UnknownCall
  ├─ 0x48CDD3  call 0x52D9A0        GameMainLoop ①（首次）
  │      └─ 状态机 [0xA8B238]，jump tables @0x52EB58/0x52EBA4/0x52EBD0
  └─ ★ 0x48CE8A–0x48CEA8  真正的每帧环
        0048CE8A  call 0x55D360        MainLogicFrame   ← 每逻辑帧
        0048CE91  je   0x48CE9C
        0048CE93  call 0x55CFD0        FrameSample（每 0x400 帧采样）
        0048CE9A  jne  0x48CEAA        （返回非 0 则退环）
        0048CE9C  call 0x48C8B0        （会话/存档维护）
        0048CEA1  call 0x55CFD0
        0048CEA8  je   0x48CE8A        ★回边
        └─ 0x48CFAA  call 0x52D9A0     GameMainLoop ②（收尾/下一局）
```

### 3.2 `0x55D360` = `MainLogicFrame`（**CurrentFrame++ 所在**）

调用者：`0x48CE8A`（主环）+ `0x608206/0x60D407/0x62314E/0x623D72/0x624271`（模态/UI 内嵌泵）。

```
0x55D360 MainLogicFrame:
  if (![0xA8E9A0]) return;                 // 非局内，早退
  [0xABCD58] = 1;                          // 「帧处理中」标志
  if (![0xA8ED80]) {                       // 非快进
      if (state==0 || state==5)  { Sleep(0x1F4=500ms); MessagePump(0x5D4D50); }
      else                       { Sleep(0x0A=10ms);   MessagePump(0x5D4D50); }
  }
  if (CurrentFrame >= [0xA8E2E4])  0x69A300(state);   // 帧号阈值触发
  [0xA8B55C] = timeGetTime();              // 帧起点
  … 输入检查 0x54F5C0 / 视口缩放 0x4A9840 …
  0x637550();  0x5D4430();                 // 环境/消息列表
  … 联机状态 3/4 分支 …
  elapsed = timeGetTime() - [0xA8B55C];
  if (elapsed > 1000) elapsed = 1000;
  [0xA8B560] += elapsed;  [0xA8B564]++;    // 帧耗时记账
  0x647260();  0x637550();
  0x48D080();                              // ★Game::UnknownCall（每帧钩 ①）
  …
  edx = CurrentFrame;  inc edx;            // 0x55DE73–0x55DE7E
  CurrentFrame = edx;                      // 0x55DE81  ★唯一 inc
  if ([0xB07784] < edx) { 0x684290(); [0xB07784] = edi; }
  0x55E160();                              // ★LogicUpdate（世界更新）
  0x725C70();  0x637270();
  [0xABCD58] = 0;
```

### 3.3 `0x55E160` = `LogicUpdate`（带自己的 timeGetTime 节拍）

```
0x55E160:
  if (state==0 || state==5) goto idle;
  now = timeGetTime(0x5D5890);             // ← 帧节拍用 timeGetTime，非 Clock::Now
  if (now - [0x887328] < [0x887330]) return;  // 未到目标间隔
  0x48D080();                              // ★Game::UnknownCall（每帧钩 ②）
  if ([0xA8EDA0]==0 && [0xA8ED80]==1) {
      // 真正的对象/世界更新（含 0x55AFB0 FPS 档位、0x55E3B5 CurrentFrame 读…）
  }
```
`0x887328/0x887330` 的装入由 `0x5D5870`（`timeBeginPeriod(1)`）/ `0x5D5880`（`timeEndPeriod(1)`）包裹的测量段完成（`0x55D4C1–0x55D760` 一带共 5 组 begin/end 对）。

### 3.4 `0x48D080` = `Game::UnknownCall`（每帧钩，169 直呼）

YRpp `Unsorted.h:45` 已命名为 `Game::UnknownCall`。骨架（`skel_48D080.txt`）：

```
0x48D080:
  0x406F70();                    // AudioFrameUpdate（Clock::Now + 33ms 门）
  if (someList) v[8]();          // 虚回调
  switch ([0xA8B238]) {          // 游戏状态
    case …: 0x48D1E0();          // 网络/输入分发（消息泵 + IPX）
    case …: 遍历 0xA8EA70 队列 → 0x643C50();   // 环境效果（见 dirty_rect §5.2）
    …
  }
  0x7CA67F();                    // CRT 辅助
```
**每逻辑帧被调 2 次**：`0x55D360` 尾部 1 次 + `0x55E160` 节拍开门时 1 次。

### 3.5 每帧固定做的全局更新（汇总）

| # | 更新 | 地址 | 频率 |
|---|---|---|---|
| 1 | 消息泵 `MainMessagePump` | `0x5D4D50`（经 `0x55D360` 的 Sleep 块 / `0x48D1E0`） | 每 UI 帧 |
| 2 | 音频帧 `AudioFrameUpdate` | `0x406F70`（33ms 自节流） | 每 `0x48D080` |
| 3 | 输入队列 peek | `0x54F000/0x54F050` | 每帧 |
| 4 | **`CurrentFrame++`** | `0x55DE73–0x55DE81` | 每 `0x55D360` |
| 5 | 世界/对象更新 | `0x55E160`（timeGetTime 节拍） | 按 GameSpeed 间隔 |
| 6 | 帧耗时记账 | `0xA8B560/0xA8B564` | 每 `0x55D360` |
| 7 | FPS/细节档位 | `0x55AF60`（经 `0x55AFB0`） | 每逻辑更新 |
| 8 | 环境效果队列 | `0x643C50`（`0x48D080` 内） | 每帧 |
| 9 | 网络收包 `FrameBeat_NetRecv` | `0x53E770`（经 `0x5D4D50`/`0x48D1E0`） | 每帧 |
| 10 | 帧采样（每 0x400 帧） | `0x55CFD0` | 1/1024 |

---

## 4. `timeBeginPeriod(1)` 与引擎 Sleep/等待

### 4.1 引擎自带封装（`out/re_work/clock_frame/timebegin_wrappers.txt`）

| 地址 | 语义 | 反汇编要点 |
|---|---|---|
| **`0x5D5870`** | `this->T = timeBeginPeriod(1)` | `push 1; call [0x7E1538]; mov eax,esi; ret`（thiscall，返回 this） |
| **`0x5D5880`** | `timeEndPeriod(1)` | `push 1; call [0x7E152C]; ret` |
| **`0x5D5890` / `0x5D58A0`** | `timeGetTime` 薄桩 | `jmp [0x7E1530]`（两份等价拷贝） |

**调用点分布**：
- `0x55D360`（MainLogicFrame）：`0x55D4CE/0x55D541/0x55D643/0x55D6BB/0x55D737` 起共 **5 组 begin/end 对**，包裹 `0x55D4C1–0x55D760` 的计时测量段。
- `0x55E160`（LogicUpdate）：`0x55E1D6/0x55E229/0x55E28F` 多次 `timeGetTime`。
- `0x411B20`（音频）、`0x5B1D90`、`0x411650`（BSurface dtor）：各有 1 对 begin/end。

**含义**：引擎**在测量帧间隔的瞬间**把系统调度精度拉到 1ms，测完立刻还原。这是局部窗口，不是全局。

### 4.2 与 ra2render `timeBeginPeriod(1)` 的关系

`ra2render/dllmain.cpp:34` 在 DLL_PROCESS_ATTACH 时全局 `timeBeginPeriod(1)`，DETACH 时 `timeEndPeriod(1)`。效果：

| 场景 | 无 ra2render | 有 ra2render |
|---|---|---|
| `0x55D360` 的 `Sleep(10)` | 默认 15.6ms 量化，实际 ~15–31ms | **~10ms**，抖动显著下降 |
| 引擎内部 begin/end 包裹 | 有效（测量窗口 1ms） | **多余但无害**（已是 1ms） |
| `0x4F4780` 的 `Sleep(0x32=50ms)` | ~50–62ms | ~50ms |
| 空闲等待 `Sleep(500)`（菜单） | 无感 | 无感 |

**结论**：ra2render 的常驻 1ms **是引擎帧节拍的实质性增强**，不要去掉。引擎内部的 begin/end 对可以保留（无害、且无 ra2render 时仍是保护）。

### 4.3 Sleep 点全表（22 处，`analyze_pass3.py` §8）

| VA | 参数 | 宿主 | 性质 |
|---|---|---|---|
| `0x55D39B` | **0x1F4 (500ms)** | `0x55D360` | 菜单空闲节拍 |
| `0x55D3B2` | **0x0A (10ms)** | `0x55D360` | **局内帧节拍** |
| `0x4F4B90` | 0x32 (50ms) | `0x4F4780` | 显示/滚动等待 |
| `0x432D2C` | 0x21 (33ms) | `0x432C70` | 与音频 33ms 门同周期 |
| `0x607F11` | 0x1E (30ms) | `0x6071E0` | `0x406F70` 的另一入口 |
| `0x479839` | 0x1F4 | `CD::v[2]` | CD 换盘等待 |
| `0x47A81F` | 0x3E8 | `0x47A6F0` | CD/文件 |
| `0x4C85C2` | 0xFA0 | `0x4C84E0` | 长等待 |
| `0x68FBFA` | 0x1F4 | `0x68FBB0` | 等待 |
| `0x6BBF8B` | 0x9C4 | `0x6BB9A0` | 等待（同宿主也是空桩最大调用者） |
| `0x6DEF20` / `0x6E28C9` | 0x3E8 | `0x6DD8B0` / `0x6E2520` | 等待 |
| `0x775194` | 0x64 | `WinModemClass::v[7]` | 串口 |
| `0x7A1F2E` | 0x64 | `0x7A1BB0` | 等待 |
| `0x7949FD` | 5 | `0x7947B0` | 短等待 |
| 其余 | 0 / 寄存器 | `0x49F620`、`0x53DE00`、`0x5DC350`、`0x60D450`、`0x7759E0` | 忙等/让步 |

`WaitForSingleObject` 约 20 处（`0x407780` 音频线程、`0x7B84xx` 鼠标/COM），`MsgWaitForMultipleObjects` **未导入**。

---

## 5. 优化建议

### 5.1 Clock 是否可缓存 —— **可，但限单帧**

| 项 | 建议 | 风险 |
|---|---|---|
| 同一逻辑帧内多次 `Clock::Now` | **帧首取一次缓存**（`static int64_t s_frameNow`），`0x406F70`/渲染/`0x752760` 读缓存 | 低。音频 33ms 门只要求单调，单帧缓存（<67ms）不破坏 |
| 跨逻辑帧缓存 | **不要**。`0x55D360` 的 `Sleep(10)` 会让帧长变化，跨帧缓存会漂 | 高 |
| 替换 `jmp [0x87E848]` 为直呼 `0x4093C0` | **可选**。省 2 条指令（`mov/test/jmp`）+ 一次间接预测失败；QPC 路径几乎恒真 | 低。但保留 `0x87E848` 作 hook 点更有价值 |
| 把 `0x4093B0` 的 35 处直呼改成读 TLS 缓存 | 收益最大在 `0x4055C0`（x3）与 `0x52D9A0`（x4） | 中，需逐点确认语义 |

**收益预估**：perf `0x409300` 桶 104 样本（1.4%）里，QPC 系统调用本身占大头；缓存后可省 **0.5–1.0%**，是本簇最划算的一刀。

### 5.2 空桩是否可去掉调用 —— **可，收益极小**

- **安全**：`call 0x4068E0`（5 字节）→ `nop`×5，或改为 `add esp,N` + `nop`。语义零变化（§2.3）。
- **收益**：<0.2%。**不建议单独做**；若做，只 nop **`0x52D9A0`/`0x48D1E0` 内的 18 处**热路径 call。
- **不要**改成真 printf（§2.4）。

### 5.3 帧循环冗余扫描

| # | 冗余点 | 证据 | 建议 | 预估收益 |
|---|---|---|---|---|
| 1 | **`0x48D080` 每逻辑帧被调 2 次** | `0x55D360` 尾部 + `0x55E160` 节拍开门 | 合并为 1 次（在 `0x55DE9A` 前后统一）。注意 `0x406F70` 自带 33ms 门，二次调用本身便宜，但 `0x643C50` 队列遍历会做两遍 | 0.3–0.8% |
| 2 | **`0x55D360` 的 `Sleep(10)` 固定值** | `push 0xA; call Sleep` | 改为「目标帧时 − 已耗时」自适应，不足 1ms 则 `Sleep(0)`+`SwitchToThread`。**须配 timeBeginPeriod(1)** | 帧率上限从 ~100Hz 提到真实能力；对 15fps 逻辑帧无影响，但对渲染帧率有益 |
| 3 | **`0x54F000` 空环仍 `call 0x5D4D50`** | `audio_input_hotspots.md` §4.1 第 3 条 | 「本帧已泵过」标志，一次/帧 | 0.5–1.5%（消息泵是空环主成本） |
| 4 | `0x48D080` 的 `0x7CA67f` CRT 辅助 ×2 | `skel_48D080.txt` | 未逆，若为纯诊断可 nop | 未知 |
| 5 | `0x55D360` 内 `0x637550` 被调 **2 次**（`0x55DD9B` + `0x55DE45`） | `LogicFrame_body_tail` | 确认是否幂等，若是则去重 | 微 |

### 5.4 明确不建议动

- `0x406F70` 的 33ms 音频门（已节流）。
- `0x53E8B3` 收包忙等（是等待不是工作）。
- `0x54F000` 输入环本体（契约层，联机同步敏感）。
- `0x87E848` 函数指针本身（是 hook 的最佳切入点，保留）。
- ra2render 的 `timeBeginPeriod(1)`（帧节拍的实质增强）。

---

## 6. 未决问题

1. **`0x7C92D0` 缩放原语的定点格式**（QPC→ms 的系数布局）未逆；影响「Clock 缓存后单位是否仍是 ms」。
2. **GameSpeed 数值 → `0x887330` 目标间隔**的映射公式未逐指令确认（在 `0x55E160`/`0x55D360` 的测量段装入路径，`0x55D4C1–0x55D760`）。
3. **`0xA8E2E4`**（`CurrentFrame >= 此值` 触发 `0x69A300`）语义未查——疑似「本局帧预算/超时」。
4. **`0x52D9A0` 状态机的 jump table 全集**（`0x52EB58/0x52EBA4/0x52EBD0/0x52EBBC` 等 4 张表）未展开；状态码 0–5 的完整迁移未画全。
5. **`0x4068E0` 是否有「真身」**（某调试 DLL 导出的 `WWDebugPrint`）可对照签名；目前只靠调用形态反推。
6. **1672 处 call 后是否有人读 `eax`** 未全量验证——改遥测前必须补（§2.4）。
7. **单机 vs 联机**下 `0x55D360` 的 `Sleep(10)` 是否恒定（联机可能被 `0x53E8B3` 忙等取代）；需 loadbench 双场景对比。
8. **`0xB07784`**（`CurrentFrame` 越过它则 `0x684290`）——疑似「录像/回放关键帧边界」，未确认。
9. **`0x48D1E0`（Dispatcher）的完整状态分支**未逐条命名；它内含 10 处空桩 call 与 5 处 `0x5D4D50`，是消息泵的第二大调用者。
10. **`0x6BB9A0`（空桩最大宿主 x69）** 本身未逆；同宿主还有 `Sleep(0x9C4)` 与 `WaitForSingleObject`，疑似 CD/安装检查大函数。

---

## 附录 A：地址速查

| VA | 名 | 角色 | 热度 |
|---|---|---|---|
| `0x406B10` | `AudioBootstrap` | 唯一调 `Clock::Init` | 冷（一次） |
| `0x409360` | `Clock::Init` | 装 `0x87E848` | 冷（一次） |
| **`0x4093B0`** | **`Clock::Now`** | 64 位墙钟，`jmp [0x87E848]` | **真热（perf 0x409300）** |
| `0x4093C0` | `Clock::NowQpc` | QPC+缩放 | 热（被间接） |
| `0x4093F0` | `Clock::NowTick` | timeGetTime 回退+自旋 | 冷 |
| `0x7C92D0` | `ScaleToMs` | 64 位定点缩放 | 中 |
| **`0x4068E0`** | **`DebugLogStub`** | **空 `ret`，1672 直呼 printf 残留** | **伪热点** |
| `0x4068F0` | `CallN` | `call ebx` N 次分发器 | 冷 |
| `0x406F70` | `AudioFrameUpdate` | 33ms 门，调 `Clock::Now` | 半热 |
| `0x48CCC0` | `GameRunner` | 一局外层 | 热（壳） |
| `0x48CE8A` | 主环回边 | `call 0x55D360` 循环 | 热 |
| **`0x55D360`** | **`MainLogicFrame`** | **每逻辑帧，`CurrentFrame++` @ `0x55DE81`** | **真热** |
| `0x55CFD0` | `FrameSample` | 每 0x400 帧状态快照 | 冷 |
| **`0x55E160`** | **`LogicUpdate`** | timeGetTime 节拍 + 世界更新 | **真热** |
| `0x48D080` | `Game::UnknownCall` | 每帧钩（169 直呼，每逻辑帧 ×2） | 真热（壳） |
| `0x48D1E0` | `GameDispatcher` | 状态分发 + 消息泵 + 空桩 ×10 | 热 |
| `0x52BA60` | `GameStart` | 启动，空桩 ×33，尾 `jmp 0x48D080` | 冷（一次） |
| `0x52D9A0` | `GameMainLoop` | 状态机，`CurrentFrame` 清零 @ `0x52DA08` | 热 |
| `0x5D5870` | `TlsTimeBeginPeriod` | `timeBeginPeriod(1)` thiscall 包装 | 中 |
| `0x5D5880` | `TlsTimeEndPeriod` | `timeEndPeriod(1)` | 中 |
| `0x5D5890` | `TimeGetTimeThunk` | `jmp [timeGetTime]` | **真热（帧节拍）** |
| `0x5D4D50` | `MainMessagePump` | 消息泵 | 真热 |
| `0x53E770` | `FrameBeat_NetRecv` | 帧节拍/收包 | 真热 |
| `0x6D3D10` | `TacticalClass::Render` | 渲染（内调 `0x6D4B50`→`Clock::Now`） | 真热 |
| `0x6BE000` | `AppMain` | 启动/会话建立，调 `GameRunner` | 冷（一次） |

**关键全局**

| VA | 含义 |
|---|---|
| `0x87E848` | Clock 函数指针（QPC=0x4093C0 / Tick=0x4093F0） |
| `0x87E828/0x87E82C` | QPC→ms 缩放系数（64 位） |
| `0x87E84C` | `NowTick` 自旋序列号 |
| `0xA8ED84` | `Unsorted::CurrentFrame` |
| `0xA8E7AC` | 会话代数/重入计数 |
| `0xA8ED80` | 快进（跳过 Sleep）标志 |
| `0xA8E9A0` | 局内标志 |
| `0xA8B238` | 游戏状态（SessionClass） |
| `0xA8E2E4` | 帧号阈值 |
| `0xA8B55C/60/64` | 帧耗时记账 |
| `0x887328/0x887330` | 逻辑帧节拍（timeGetTime） |
| `0x829FF4/0x829FF8` | MinFrameRate 对 |
| `0xABCD44` | CurrentFrameRate |
| `0xB07784` | 关键帧边界（暂名） |
| `0x7E11D4/0x7E11D8` | IAT：QueryPerformanceCounter / Frequency |
| `0x7E1530` | IAT：timeGetTime |
| `0x7E1538/0x7E152C` | IAT：timeBeginPeriod / timeEndPeriod |
| `0x7E11F0` | IAT：Sleep |
| `0x7E11DC` | IAT：WaitForSingleObject |

---

## 附录 B：与既有结论对照

| 来源 | 原结论 | 本次确认/修正 |
|---|---|---|
| `nonrle_blit_and_named_hotspots.md` §3.2 | `0x409360` 装 `0x87E848`，`0x4093B0` 为热点本体 | **确认**；补出唯一安装者 `0x406B10`、35 处直呼全景、`NowTick` 回绕细节 |
| 同上 §6 未决 4 | 「`Clock::Now` 调用者未反向追完」 | **已补完**：35 处直呼，无 `call [0x87E848]`；并更正「与 GameSpeed/FrameDelay 关系」——帧节拍走 `timeGetTime`，不用 Clock |
| `audio_input_hotspots.md` §1.1 | `0x4068E0` 空桩 1672 直呼，疑空默认实现 | **更正定性**：是 **printf 日志宏残留**（fmt 串实锤），不是空虚函数；0 处数据指针 |
| 同上 §6 未决 1 | 「需按调用方聚类」 | **已完成**：424 宿主 / 6 大域 / 热路径仅 52 处（3%） |
| 同上 §1.2 | `0x406F70` 33ms 门 + `0x48D080` 170 直呼 | **确认**；补出 `0x48D080` 每逻辑帧被调 **2 次**（`0x55D360`+`0x55E160`） |
| `dirty_rect_l4.md` §5.2 | `0x48D080` 按状态遍历 `0xA8EA70` | **确认**；补出其为 `MainLogicFrame` 尾部的每帧钩 |
| 同上 §5.1 | `0x684675` 开局 `CurrentFrame:=0`、`[0xA8E7AC]++` | **确认**；另找到 `0x52DA08` 也清零（`GameMainLoop` 入口） |
| REVERSE_ENGINEERING_AND_PATCHES.md | ra2render 调 `timeBeginPeriod(1)` | **补充**：引擎自带 3 对封装，`0x55D360/0x55E160` 成对包裹测量；ra2render 常驻 1ms 是 `Sleep(10)` 精度的实质增强 |

---

## 7. 冲刺结论（S5）

### 7.1 §6 十大未决问题逐条闭环台账

| # | 未决条目 | S5 冲刺定性 | 证据级别 | 核心反汇编证据 (VA / FileOffset / 机器码 / 指令) | 结论详述 |
|---|---|---|---|---|---|
| 1 | `0x7C92D0` 缩放原语定点格式 | **MSVC CRT 标准 `_alldiv`（带符号 64 位整除）** | **[实证]** | `VA 0x7C92D0 (0x3C92D0): 57 56 53 (push edi, esi, ebx)` ... `VA 0x7C9377 (0x3C9377): c2 10 00 (ret 0x10)` | 并非私制定点缩放，而是 CRT `_alldiv(int64 dividend, int64 divisor)`。在 `Clock::Init (0x409360)` 中先执行 `_alldiv(QPF, 1000)` 得每毫秒计数值；在 `Clock::NowQpc (0x4093C0)` 中执行 `_alldiv(QPC, counts_per_ms)`。因此 `Clock::Now` 返回值**直接为毫秒 (ms)**，单帧缓存单位与 `timeGetTime` 100% 对齐。 |
| 2 | GameSpeed → `0x887330` 映射公式 | **$1000 / \text{TargetFPS}$ 毫秒整除** | **[实证]** | `VA 0x55D51C (0x15D51C): b8 e8 03 00 00 (mov eax, 0x3E8)`<br>`VA 0x55D522 (0x15D522): f7 3d 58 b5 a8 00 (idiv [0xA8B558])`<br>`VA 0x55D55E (0x15D55E): 89 35 30 73 88 00 (mov [0x887330], esi)` | 目标帧间隔公式严格为 `1000 / [0xA8B558]` ms。30 FPS 对应 33 ms (`0x21`)，60 FPS 对应 16 ms，默认 15 FPS 对应 66 ms。在 `0x55E160` (LogicUpdate) 中通过 `now - [0x887328] >= [0x887330]` 门控世界更新。 |
| 3 | `0xA8E2E4` 与 `0x69A300` 语义 | **Debug 帧预算断言桩（空 `ret`）** | **[实证]** | `VA 0x69A300 (0x29A300): c3 (ret)`<br>`VA 0x55D3C6 (0x15D3C6): 3b c1 (cmp eax, ecx)`<br>`VA 0x55D3CF (0x15D3CF): e8 2c cf 13 00 (call 0x69A300)` | 全镜像中 `0x69A300` 是单字节空桩 `ret`，`0xA8E2E4` 在 `.data` 初值为 0 且无动态写入。此为 Westwood 遗留的帧数预算/自动化测试触发桩，Release 构建下为纯 no-op。 |
| 4 | `0x52D9A0` 状态机 Jump Table 全集 | **GameMode 分发 (6 态) + 阶段迁移表 (19 态)** | **[实证]** | `VA 0x52E158 (0x12E158): cmp eax, 5; ja 0x52E344; jmp [eax*4 + 0x52EBA4]`<br>`VA 0x52DCD8 (0x12DCD8): cmp eax, 0x12; ja 0x52E446; jmp [eax*4 + 0x52EB58]` | `0x52EBA4` 严格对应 `SessionClass::GameMode` 6 态（0=Campaign, 1=Modem, 2=Serial, 3=LAN, 4=Internet, 5=Skirmish）；`0x52EB58` 展开 19 项生命周期子状态（0=装载, 1/18=局内运行, 8=战败, 9=胜利, 10=重开, 11=退出）。 |
| 5 | `0x4068E0` 空桩真身命名 | **`WWDebug_Printf` / `Debug_Print` (Release NDEBUG 消除残留)** | **[实证] + [推演]** | 全镜像 1672 处调用点，传参全为 `.rdata` 格式串（如 `0x840F5C "%d-%d\n"`, `0x849E94 "Focus_Loss()\n"`），cdecl 调用约定 | 无外部调试 DLL 导入。MSVC 6.0 编译期因未对可变参数空函数内联而保留了调用点与单字节 `ret` 桩体。建议符号名锁定为 `WWDebug_Printf`。 |
| 6 | 1672 处 Call 空桩后 `eax` 读写验证 | **全量扫描：0 处读 `eax`，100% 安全** | **[实证]** | 遍历全量 1672 处 `call 0x4068E0` 后续基本块，严格指令语义扫描 | **0 / 1672** 处在被重写前读取 `eax`。所有调用方均将该函数视作 `void`。短路/NOP/改遥测绝对不会引入未定义寄存器副作用。 |
| 7 | `0x55D360` Sleep(10) 单机 vs 联机恒定性 | **关键修正：前台窗口 `[0xA8ED80]==1` 时完全零 Sleep！** | **[实证]** | `VA 0x55D377 (0x15D377): a1 80 ed a8 00 (mov al, [0xA8ED80])`<br>`VA 0x55D385 (0x15D385): 75 34 (jne 0x55D3BB)`<br>`VA 0x7778CE (0x3778CE): mov [0xA8ED80], al (Focus_Loss 写入)` | `0xA8ED80` 为 `AppHasFocus` 标志。正常游戏（有焦点）时直接跳过 Sleep 块（零 Sleep）；`Sleep(500)`（单机暂停）与 `Sleep(10)`（联机后台保活）**仅在失去焦点后台运行时生效**！ |
| 8 | `0xB07784` 与 `0x684290` 语义 | **过场动画/对话框 3 帧防抖与输入锁解冻机制** | **[实证]** | `VA 0x69BB06 (0x29BB06): mov edx, [0xA8ED84]; add edx, 3; mov [0xB07784], edx`<br>`VA 0x55DE8B (0x15DE8B): cmp eax, ecx; jge 0x55DE9A; call 0x684290`<br>`VA 0x6842D3 (0x2842D3): mov ecx, [0x87F770]; call 0x54F720` | 进入过场/电影时置标志 `ScenarioClass+0x35A2=1` 并设定 `[0xB07784] = CurrentFrame + 3` 锁输入；3 帧后由 `0x684290` 恢复鼠标显示、清空输入队列 (`0x54F720`) 并解冻交互。 |
| 9 | `0x48D1E0` Dispatcher 完整语义 | **`Game::CallBack`（UDP 端口探测与连接保活分发器）** | **[实证]** | `VA 0x48D2F0 (0x08D2F0): push 0x81D710 ("Sending NET_PORT_PROBE packets in Call_Back\n")`<br>`VA 0x48D3F4 (0x08D3F4): cmp edi, 0x960 (40秒超时判定)`<br>`VA 0x48D36B (0x08D36B): call 0x5D4D50` | 局域网/互联网联机对局中负责发送 `NET_PORT_PROBE` 包、40 秒无包超时判定及等待过程中的 Win32 消息泵。 |
| 10 | `0x6BB9A0`（空桩最大宿主 x69）身份 | **引擎主入口 `WinMain`（启动检查与 AutoPlay 互斥）** | **[实证]** | `VA 0x7CD8EA (0x3CD8EA): e8 b1 e0 ee ff (call 0x6BB9A0)`<br>`VA 0x6BBF86 (0x2BBF86): push 0x9C4 (2500ms); call Sleep`<br>`VA 0x6BBFAD (0x2BBFAD): push 0x840E38 ("Got AutoPlayMutex okay.\n")` | CRT 启动函数 `0x7CD80F` 调用 `WinMain` 的目标地址就是 `0x6BB9A0`。69 处空桩是 `DEBUG_LOG("%d-%d\n", __LINE__, step)` 启动追踪打点；2500ms 等待是等待光盘 AutoPlay 互斥体释放。 |

---

### 7.2 输入环与 `AudioFrameUpdate (0x406F70)` 33ms 节流深度交互模型

```
[Win32 消息流]                                       [游戏逻辑/渲染帧主环]
  WndProc (0x54F790)                                  MainLogicFrame (0x55D360)
         │                                                    │
  InputMgr::PushWord (0x54F1C0)                               ├─ [0xA8ED80 Focus 门控]
         │ (环形队列 ring[256])                               │    ├─ 有焦点: 直接跳过 (0 Sleep)
         ▼                                                    │    └─ 失焦: Sleep(500) 或 Sleep(10)
  InputMgr::PeekEvent (0x54F000)                              │
         │ (若环未满)                                         ├─ 中期钩: call 0x48D080 ①
         ▼                                                    │
  MessagePump (0x5D4D50)                                      ├─ 帧尾钩: call 0x48D080 ②
         ├─ USER32!GetCursorPos (0x53E770)                    │
         ├─ WWMouseClass::SetCoords (0x887640)               ├─ CurrentFrame++ (0x55DE81)
         └─ USER32!PeekMessageA                               │
                                                              ▼
                                                        LogicUpdate (0x55E160)
                                                              │ (timeGetTime 节拍)
                                                              └─ 节拍钩: call 0x48D080 ③
                                                                      │
                                                                      ▼
                                                        Game::UnknownCall (0x48D080)
                                                                      │ (170 处统一直呼)
                                                                      ▼
                                                        AudioFrameUpdate (0x406F70)
                                                                      │
                                                                      ├─ 重入锁 [0x87E75C]
                                                                      ├─ 读 Clock::Now (0x4093B0)
                                                                      └─ if (now - last < 33ms) return;
                                                                           └─ 执行 0x4041D0/0x750EC0/0x752760
```

1. **调用拓扑与解耦机制**：
   - 全镜像中 `AudioFrameUpdate (0x406F70)` **仅有 2 处直呼**：
     - `0x0048D08C`（位于通用心跳 `Game::UnknownCall@0x48D080` 内）
     - `0x00607F0A`（位于 Bink/Smacker 视频播放自旋等待环内）
   - 输入泵 `InputMgr::PeekEvent (0x54F000)` / `MessagePump (0x5D4D50)` **绝不调用音频更新**；音频系统也从不向输入队列投递事件。两者仅在 `MainLogicFrame` 顶层按序调度，实现强时序解耦。
2. **多重触发与 33ms 硬件保护闸**：
   - 单逻辑帧内，`0x48D080` 被触发 2~3 次（`0x55D835` 中期、`0x55DE4A` 帧尾、`0x55E1F3` 逻辑开门时）。
   - `0x406F70` 序言通过全局重入锁 `[0x87E75C]` 与 `Clock::Now` 33ms（`0x21`）差值门控：无论外部每帧心跳被高频调用多少次，真正的音频样本衰减 (`0x4041D0`)、语音列表推进 (`0x750EC0`) 与主题曲流推进 (`0x752760`) **严格被硬件时钟锁定在最大 30Hz**。
3. **失焦与休眠下的退化表现**：
   - 当游戏失焦（`[0xA8ED80]==0`）进入 `Sleep(500)` 时，单机模式下 `MainLogicFrame` 挂起，不再到达 `0x48D080`，音频推进自然暂停；重获焦点后立即单调推进，绝无时间倒流。

---

### 7.3 `0x53E7*` 族真实职责边界与体系定位

既有文档曾将 `0x53E770` 假设为网络收包或通用帧节拍。S5 冲刺通过 IAT 对照、vtable 反查与反汇编，**彻底证实该簇为 Westwood 底层 Win32 消息循环与硬件输入驱动层**：

| VA | 真实命名 | 真实职责 | 核心证据 |
|---|---|---|---|
| `0x0053E6B0` | `ModalDialogEventPump` | 模态对话框与剪贴板处理 | 持有临界区 `0xAA0418` 锁，弹出系统文件选择或存盘对话框 |
| `0x0053E720` | `GetInputCaptureMode` | 获取当前窗口输入捕获模式 | 返回 `[0xAA0444]`（0=标准Win32，1=游戏独占输入，2=模态等待） |
| `0x0053E730` | `WaitAndPumpMessages` | 阻塞式消息等待环 | 循环调用 `0x53E770` 直至产生消息，遇 `WM_QUIT (0x12)` 返回 0 |
| **`0x0053E770`** | **`PumpWin32MouseAndMessages`** | **硬件鼠标采样 + 坐标转换 + Win32 消息 peek** | `USER32!GetCursorPos@0x7E13C0` 采样硬件鼠标；通过 `WWMouseClass::Instance (0x887640)->v[0x44]` 转换为客户区坐标；变动时调用 `v[0x38] (SetCoords)` 并压入 0x14 字节移动包；随后执行 `PeekMessageA` |
| `0x0053E86C` | `ModalMessagePump` | 模态消息分发 | 仅当 `[0xAA0444]==2` 时接管，处理 `WM_KEYDOWN` (ESC `0x1B`) 与 `WM_PAINT` (`0x0F`) |
| `0x0053E8B3` | `DirectPlayIdleSpin` | 网络空闲自旋 | 忙等 `[0xAA0478]` 标志与 `0x409320` 缓冲，属于空转等待而非计算热点 |
| `0x0053EC40` | `VirtualKeyboard_SetKey` | 虚拟键盘按键注入 | 向模拟键盘数组 `0xAA0168[ecx]` 写入按键状态字 |
| `0x0053EC70` | `VirtualKeyboard_GetKeyState` | 虚拟化 `GetKeyState` | 若 `[0xAA0444]==0` 直通 `USER32!GetKeyState@0x7E13A8`，否则读虚拟表 |
| `0x0053EC90` | `VirtualKeyboard_GetAsyncKeyState` | 虚拟化 `GetAsyncKeyState` | 若 `[0xAA0444]==0` 直通 `USER32!GetAsyncKeyState@0x7E13E0`，否则读虚拟表 |

**架构定位结论**：
`0x53E7*` 族**不是网络传输层**，而是引擎与 Win32 OS 之间的**输入适配与消息泵中枢**。`[0x887640]` 确为 `WWMouseClass::Instance`。其 CPU 占用的实质是高频轮询 `GetCursorPos` 与 `PeekMessageA` 产生的系统调用开销，而非逻辑瓶颈。

