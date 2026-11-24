# 字段规格卡 · `0x00A8EC34`（索敌入口调用累计代理）

> **本卡只覆盖一个 VA**：`0x00A8EC34`。卡结构依 `W4_FIELD_SPEC/TASK.md:40-55`（Q1 逐字段规格卡）。
> **目标版本**：`ra2youli/gamemd.exe`，本次实跑 `Engine()` 与独立 PE 读取均得
> SHA256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
> （与 `D19_RULING/FACTBASE_D19.md:7`、`:88` 一致）。ImageBase `0x400000`。
> **纪律**：零真机、零采样实现、零母本改动；唯一写域 `W4_FIELD_SPEC/`。凡「A 调用 B ⇒ A 具有 B 性质」
> 均进 B 函数体核字节（`TASK.md:54`）；引用文件均读紧邻注释（`TASK.md:55`）。
> **已定谳前提直接采用，不推翻**：`TASK.md:20-34`（尤其 `:24`「索敌入口**调用累计**代理（无每次工作量）」、
> `:26-27`「不得换算为可见单位数、实际工作量或耗时」、`:31-33`「帧内冻结前提已被破坏」、
> `:34`「权限边界继续有效」）。

---

## 0. 一句话结论

在**未被运行时补丁改写**的 `gamemd.exe` 镜像里，`0x00A8EC34` 是一个 4 字节全局 dword，
**全镜像唯一的直接写点**是 `0x6F8E09`（`89 15 34 EC A8 00`），
由 `0x6F8DF3` 读取 + `0x6F8E04` 的 `42`（`inc edx`）喂值，
**位于且仅位于 `Greatest_Threat`（`0x6F8DF0`）的入口序言内**；
自增对从入口进入的所有路径无条件成立，连 `0x6F8E41` 的早退也发生在写回之后。
⇒ 本字段是**「进入该入口的次数」**的累计代理，**不是**扫描完成次数、扫描工作量或耗时。
可采性判「**需补证**」：静态直接写点已穷尽且可复核，但运行期有效性、间接别名写、
读档/进程生命周期、以及仓内 `ra2render.dll` 的 9 字节 Inline Hook 门控均未闭合，且授权闸未开。

---

## 1. VA / 符号名

| 项 | 值 | 依据 |
|---|---|---|
| VA | `0x00A8EC34` | `TASK.md:24`；`D19_RULING/RULING_D19.md:22` F6 |
| file_off | `0x0068EC34`（= VA − `0x400000`） | 本次实读 PE 头 ImageBase `0x400000`；D-79 记法见 `qc151_trip.harness8_v4.py:3829-3832` |
| 所在节 | `.data`，VA `0x812000`，VirtualSize `0x367BE4`，RawSize `0x6C000`，delta `0x27CC34 ≥ 0x6C000` ⇒ **零填充 BSS，无文件字节** | 本次实跑 `Engine()` 节表输出（§8 A1/A6）；静态文件侧 `u32(0xA8EC34)=0x0`（零填充回落） |
| **符号名** | **未定名** | 见下 |

**为什么不填 `GreatestThreatCallCount` / `重入计数`**：
- 本次实读 PE：`EXPORT` 目录 RVA=0 Size=0；Debug 目录 type=4（`IMAGE_DEBUG_TYPE_MISC`）；
  全文件 `RSDS`=0、`NB10`=0、`.pdb`=0。仓内 `ra2youli/` 下三个 `*.MAP` 是地图文件
  （`ECH01.MAP/ECH02.MAP/ECH03.MAP`），不是 linker map。**没有符号表可据以定名。**
- `W3_COSTBOUND/sections/Q3_SAMPLE_PLAN.md:59` 的「`GreatestThreatCallCount`」是 W3 自拟的
  描述性标签，不是从二进制恢复的符号；`W3_COSTBOUND/W3_COSTBOUND.md:283` 同。
- `docs/re/ARCHITECTURE_ATLAS.md:1259`、`:1323`、`:1331` 称「前置防重入自增 / 全局寻敌重入计数」
  —— **与字节不符**：全镜像无对该值的递减、无 `test`/`cmp` 分支、无出口减一（§3、§5），
  且写回在全部 `ret` 之前。它是累计量，不是重入深度。
- 按 `TASK.md:44`「若符号名无法确定，写「未定名」，**不得编造**」⇒ **未定名**。
  卡内若需指称，一律用 D-19 已定谳的语义措辞「索敌入口调用累计代理」
  （`RULING_D19.md:22`、`:57`、`:149`）。

---

## 2. 类型与宽度

- **宽度 = 4 字节（DWORD）**。字节依据：两条访存指令均为 32 位操作数
  `8b 15 34 ec a8 00` = `mov edx, dword ptr [0xa8ec34]` @`0x6F8DF3`；
  `89 15 34 ec a8 00` = `mov dword ptr [0xa8ec34], edx` @`0x6F8E09`。
  本次 `disp_hits(0xA8EC34)` 把前者判为 `R`、后者判为 `W`（§8 A1）。
  重叠字节区间 `[0xA8EC34, 0xA8EC38)` 的绝对地址访存普查 **恰 2 条**，均 size=4（§8 A2），
  无字节/字级部分写。
- **符号性：未验 / 无静态依据**。`inc edx`（`0x6F8E04`，`42`）对有符号/无符号中性；
  全镜像**没有任何**以该值为操作数的 `cmp`/`test`/`jcc`（§3、§8 A2），
  因此无法由指令判 `int32` 还是 `uint32`。`Q3_SAMPLE_PLAN.md:61` 写 `uint32_t` 属假设，不采信为字节结论。
  `RULING_D19.md:57` 亦把「32 位类型及符号性依据」列为待办。
- 它不是结构体字段/容器 Count：邻域 `[VA−0x20, VA+0x20]` 的 127 条绝对地址访存（§8 A5）
  显示两侧各有一个 `DynamicVectorClass` 全局——`0xA8EC18`（字段 `0xA8EC1C/20/24/28/2C`）
  与 `0xA8EC38`（`0xA8EC3C/40/44/48/4C`，`docs/re/fx_draw_chain.md:107` 标为 `WaveClass::Array`，
  `:117` 给出 `VectorClass` 布局）；本 VA 落在两者之间 8 字节间隙的后 4 字节，是**独立全局 dword**。
  `docs/re/savegame_block_manifest.md:328`、`:907` 的第 26 号存档块实参是 `0x00A8EC38`，**不是**本 VA。

---

## 3. 写点全集（★ 本卡重点）

### 3.1 直接绝对地址写点：**穷尽 = 恰 1 处**

| # | 写点 VA | 字节（原文） | 指令 | 值来源 | 所在函数体 |
|---|---|---|---|---|---|
| W1 | **`0x6F8E09`** | `89 15 34 EC A8 00` | `mov dword ptr [0xa8ec34], edx` | `edx` ← `0x6F8DF3`(`8B 15 34 EC A8 00`) 读入旧值 → `0x6F8E04`(`42`) `inc edx` | `0x6F8DF0`（`Greatest_Threat`） |

**穷尽性自证（本次实跑，命令与输出见 §8）**：

1. **全 `.text` 重同步线性解码普查**：`Engine().disp_hits(0xA8EC34)` → **`count=2`**：
   `0x6f8df3 R mov edx, dword ptr [0xa8ec34]`、`0x6f8e09 W mov dword ptr [0xa8ec34], edx`。
   覆盖率自证 **99.99837567729335% / 1,394,120 条指令 / resync=66 / .text_size=4,063,232**
   （`ra2tool.py:5-9` 规定必须重同步逐址 +1、禁止 `disasm(blob, va)` 静默停止，须打印覆盖率）。
   独立用 `P01/stream_cache.pkl`（1,394,120 条，同源 `eng.stream` 序列化，见 `P01/v1_mega.py:24-28`）复核，
   `op_str` 含 `a8ec34` 者 **恰 2 条**、指令字节含 LE dword `34 EC A8 00` 者 **恰 2 条**，与全流解码一致。
2. **全文件裸字节扫描**：LE dword `34 EC A8 00` 在整个 PE 文件 **恰 2 处**，
   均为 ModRM disp32 操作数字段：`file_off 0x2F8DF5`（VA `0x6F8DF5`，属 `0x6F8DF3` 读指令）、
   `file_off 0x2F8E0B`（VA `0x6F8E0B`，属 `0x6F8E09` 写指令）。`.data`/`.rdata`/头/覆盖区 **0 处**。
   与 `FACTBASE_D19.md:37`「扫描 .text 中该 4 字节绝对地址仅命中操作数字段 `0x6F8DF5` 与 `0x6F8E0B`」一致。
3. **别名/间接直写排除（部分）**：解码流中 `imm32 == 0xA8EC34` 的指令 **0 条**、
   `lea reg,[0xA8EC34]` **0 条**（§8 A2/A3）⇒ 无「把本 VA 装进寄存器再经 `[reg]` 写」的静态可见直写。
   外部跳入 `(0x6F8DF0, 0x6F8E09]` 的分支 **0 条**（§8 A2）⇒ 不存在绕过入口却落到写回的旁路。
4. **函数体归属（进 B 的函数体核字节）**：`0x6F8DEF/0x6F8DEF` 为两个 `90` NOP 填充，
   `0x6F8DEB c20400` 是上一函数 `ret 4`，`0x6F8DF0 83ec5c` 是本函数头（§8 A5）；
   区间 `[0x6F8DF0, 0x6F9DB0)`（体量 `0xFC0`，`Q1_C3C4_PHYS_TARGET.md:106`）内 **恰 4 个 ret**：
   `0x6F8E41`、`0x6F9B52`、`0x6F9B6B`、`0x6F9DAC`，全为 `c20c00`(`ret 0xc`)，**全在 `0x6F8E09` 之后**。
   ⇒ W1 唯一且确实在 `Greatest_Threat` 体内，入口到写回之间 **无任何 `jcc`/`cmp`/`test`/`call`（count=0）**
   （§8 A7）⇒ **自增对从入口进入的所有路径无条件成立**。

### 3.2 「真的只在 `Greatest_Threat` 里递增」——**确认（对静态镜像、直接写点）**

- 唯一 `inc` 是 `0x6F8E04` 的 `42`（`inc edx`），紧随其后 `0x6F8E05 897c2420`（`mov [esp+0x20], edi`）
  与 `0x6F8E09` 写回（§8 A7）。全镜像对 `[0xA8EC34]` 没有第二条写指令，故**没有第二个自增点**。
- **早退也计数**：`0x6F8E19 call [eax+0x84]` → `0x6F8E1F mov cl,[eax+0xd20]` →
  `0x6F8E27 je 0x6f8e44` / `0x6F8E2F call 0x50b730` → `0x6F8E36 je 0x6f8e44` →
  `0x6F8E41 c20c00 ret 0xc`（§8 A7）。该「House 已出局/清除」早退在写回**之后**。
  ⇒ 计数的是**入口**，不是完成的扫描。这是语义边界的关键一条。
- 与 `0x0087E8E0`（代际戳）不同：后者在 `0x42A67F..0x42A685` 有回绕跳 0 的**第二次自增**
  （`FACTBASE_D19.md:32`）；本字段**没有**任何第二次自增或回绕补写。

### 3.3 未穷尽的部分（**不冒充穷尽**）

- **间接别名写 / 整对象拷贝 / 加载期写**：绝对地址普查只覆盖 `[disp32 == VA]` 的直接访存。
  `FACTBASE_D19.md:37` 已明确「此检查不穷尽间接别名写、加载/进程重启」，
  `RULING_D19.md:22`(F6)、`:102` 同。本次另发现具体残余线索：`0x65AAAB` / `0x65ACC3` / `0x65AD05`
  三处 `68 30 ec a8 00`（`push 0xa8ec30`）把**紧邻本 VA 前 4 字节的地址**作为实参，
  经 `call dword ptr [edx+0x27c]` 交给一个**未求解的虚调用**（§8 A4）。
  该虚调用目标本次未做间接 CFG/虚表求解 ⇒ **不能排除**它经指针副本覆盖 `[0xA8EC30..0xA8EC37]`。
  `rep movsd` / `memset` 整块拷贝覆盖 `.data` 该区间的可能性同样未穷尽（参照
  `W1_HOLD_SURFACE/W1_HOLD_SURFACE.md:459` 对同型残余的处置：判「静态证据不支持、无已知路径，未验」）。
- **进程创建时的零填充**不是指令写点，见 §5。
- **运行时补丁**会改写 `0x6F8DF0` 起 9 字节代码（§6），属代码补丁而非本字段写点，但会**抑制 W1 发生**。

> **写点全集结论**：*直接绝对地址写点* = `{0x6F8E09 : 89 15 34 EC A8 00}`，**已穷尽**（覆盖率 99.9984% 自证）；
> *全部可能的运行期写* **未穷尽**，残余如上，标「未验」，不补造。

---

## 4. 读点与消费方

| 类别 | 位置 | 作用 | 依据 |
|---|---|---|---|
| **引擎内唯一读者** | `0x6F8DF3` `8B 15 34 EC A8 00` | **读-改-写**的读半：取旧值进 `edx`，供 `0x6F8E04 inc edx` 后写回。**不是业务判定读** | §8 A1/A2；仅此 1 条 `R` |
| 引擎内业务消费方 | **无** | 全镜像没有以该值为操作数的 `cmp`/`test`/`jcc`、没有把它搬进别的全局、没有格式化/落盘 | §3.1 普查、§8 A2；`FACTBASE_D19.md:37` |
| 函数**调用者**（≠字段读者） | 2 个直接 `E8`：`0x445F68 e8832e2b00`、`0x4D9942 e8a9f42100`；虚表槽 `+0x3C4`（=241×4）`u32(0x7F4D24)=0x6F8DF0`，另有 14 处 `call [reg+0x3c4]` 候选派发点 | 决定「是否进入 `0x6F8DF0`」，从而**间接**决定 W1 是否发生 | §8 A2/A5；`ra2render/ra2render.h:32`、`:35`；`Q1_C3C4_PHYS_TARGET.md:106`（`0x4D9920` 链，本次只核到 `0x4D9942` 一条调用） |
| 既有 Harness | **不读** | `qc151_trip.harness8_v4.py:3831-3841` 的 9 个 `MEASURE_*_VA` 无 `0xA8EC34`；对该文件 `grep -c "A8EC34\|a8ec34"` = **0** | §8 A8；`Q1_C3C4_PHYS_TARGET.md:318-319` 亦记「历史 `measure_w*.json` 的 `counters` 从未读取该 VA」 |
| 拟议消费方 | W3 观测卡的四 VA 清单（C4 微观索敌），差分 `ΔThreatCalls` | 设计用途，非既有实现 | `Q3_SAMPLE_PLAN.md:18`、`:62`、`:77-80`；`RULING_D19.md:58` 要求未来卡写定读序/时间戳，**当前未实现** |

**注意口径**：调用者是「函数入口」的入边，不是「字段」的读点。把它们混为读者会虚增读点数。
14 处 `call [reg+0x3c4]` 是否全部落到 `0x6F8DF0`（派生类可能覆写该虚槽）本次**未逐一解虚表** ⇒ 标未验。

---

## 5. 生命周期

| 阶段 | 结论 | 依据 |
|---|---|---|
| **初始化** | PE 加载器**零填充 BSS** ⇒ 进程启动时静态初值 `0`。本次节表实算：`.data` VA `0x812000` / VirtualSize `0x367BE4` / RawSize `0x6C000`，`VA−0x812000 = 0x27CC34 ≥ 0x6C000`；`Engine().u32(VA)` 文件侧得 `0x0` | §8 A1/A6 |
| CRT 静态构造写 | **未发现**。邻域 `[VA−0x20, VA+0x20]` 全部 127 条绝对地址访存中，`disp == 0xA8EC34` 的写仅 `0x6F8E09` 一条；`0x4E67E7..0x4E6947`、`0x4E7267..0x4E72D3` 是**相邻两个向量**的 CRT 构造/析构块，写的是 `0xA8EC18/1C/20/24/25/28/2C` 与 `0xA8EC38/3C/40/44/45/48/4C/4C/50/54`，**均不覆盖 `0xA8EC34`** | §8 A5 |
| **重置 / 清零** | **未发现任何** `mov [0xA8EC34], 0` 或等价清零/复位指令（全镜像直接写点仅 W1）。无「回绕跳 0」补写（对比 `0x0087E8E0` 在 `0x42A67F..85` 有） | §3.1；`FACTBASE_D19.md:32` |
| **读档 / 反序列化** | **未验**。存档块 #26 `0x680A70` 的调用点 `0x67E248 ba38eca800` 传的是 `0xA8EC38`（`docs/re/savegame_block_manifest.md:294-301`、`:328`、`:907` 及紧邻注释 `:339-343`）；本次只核到该块函数前 `0x80` 字节（首条 `mov eax,[edi+0x10]` 读的是那个向量的 Count），**未穷尽全函数体与其间接流**，不能据此断言读档不覆盖本 dword | §8 A3 |
| **析构 / 终止** | 静态全局，无对象析构、无释放路径；随进程终止消亡。**进程重启会重新零填充** ⇒ 跨进程比较会出现非回绕的向下跳变 | §8 A1/A6；`RULING_D19.md:22`(F6) |
| **运行期有效性** | **未验**。D-19 明确「候选清单不等于运行期有效性通过」、需分项授权后先验字段有效性（`RULING_D19.md:37`、`:61`、`:70`、`:104`） | `RULING_D19.md` |

---

## 6. 门控条件（**具体标志与字节**）

### 6.1 引擎内：**该字段的自增没有内部门控**

- 入口 `0x6F8DF0` 到写回 `0x6F8E09` 之间 `jcc`/`cmp`/`test`/`call` **count = 0**（§8 A7）。
- 与 `0x00A8ED50` 的「对象 `+0x98` 活跃标志门控」不同（该标志字节为
  `0x55B954 8a8198000000 mov al,[ecx+0x98]` → `0x55B95A 84c0 test al,al` → `0x55B95C 7405 je` →
  `0x55B960 ff525c`，见 `FACTBASE_D19.md:37`、`:140-143`），本 VA **不存在任何标志字节/位门控**。
- ⇒ 对本字段，「门控」的准确答复是：**门在「是否进入 `0x6F8DF0`」这一层，不在字段读写这一层**。
  入口入边见 §4（2 个直接 `call` + 虚表槽 `+0x3C4`，其 `u32(0x7F4D24)=0x6F8DF0`）。

### 6.2 仓内运行时补丁（**本次新发现的具体门控，必须披露**）

`ra2render/ra2render.dll` 若在目标进程内加载，会在 `DllMain(DLL_PROCESS_ATTACH)` 中
**无条件**调 `InstallVTableHooks()`（`ra2render/dllmain.cpp:25-31`，紧邻注释 `:29-30` 自述「模块已成功注入」），
后者在 `blitter_hooks.cpp:3781-3782`（紧邻注释「全局寻敌汇聚点与存活目标保持」）**无条件**调
`InstallGreatestThreatHook()`；`blitter_hooks.cpp:1406-1416` 把 `0x6F8DF0` 起 9 字节
（原 `83 EC 5C 8B 15 34 EC A8 00`，逐字见 `:1341-1344` 紧邻注释）改成
`E9 <rel32> 90 90 90 90`，跳板 `s_greatestThreatTrampoline` 先重放这 9 字节再 `jmp` 回 `0x6F8DF9`
（`:1393-1399`）。

- **抑制条件（具体字节/字段）**：`Hook_Techno_Greatest_Threat` 在
  `blitter_hooks.cpp:1351-1368` 检查 `pThis+0x5D4` 的旧目标指针（`:1353`）、
  目标 `+0x6C` 的 `health`（`:1355`）、`+0x81` 的 `inLimbo`（`:1356`），
  读 `ADDR_CURRENT_FRAME`（`:1358-1359`），算 `ThrottleKey(pThis)`（`:1360`），
  当 `interval > 1 && currentFrame > 0 && ((unitHash + currentFrame) % interval) != 0`（`:1362-1364`）
  → `g_telemetry.throttledTargetScans++` 并 **`return pTarget`（`:1366`）**，**不调跳板** ⇒
  `0x6F8E04/0x6F8E09` 的自增**整次被跳过**。`interval` 默认 `8`（`ra2render/ra2render.ini:22-25`
  紧邻注释；`blitter_hooks.cpp:547` 默认实参）。
- **`docs/re/re_sprint_S8_report.md:127-137`** 与 **`docs/re/net_sync_checksum.md:859-868`**
  （已读紧邻注释）独立记载同一 9B 覆盖与「节流帧短路」，与源码一致。
- **对测量趟的影响**：`qc151_trip.harness8_v4.py:21-25`（紧邻注释）把经 `ra2loader.exe` 启动
  （注入 `ra2render.dll`、`DLL_PROCESS_ATTACH` 改码）判为**本趟证据作废**；
  `s4_injection_gate()`（`:1070-1084`，紧邻注释 `:1073-1078`）要求模块表中 `ra2render`/`ra2loader`
  命中数**必须 = 0**，枚举失败亦硬停。
  **但**：`:1080-1082` 的 `--allow-loader` 双键授权模式把命中降级为 WARN 放行。
  ⇒ **本卡未检查任何具体趟件的 S4 记录**，无法断言历史/未来趟件中该 DLL 必然缺席（标未验）。
- **镜像边界**：本次反汇编的是**磁盘上未打补丁的镜像**（SHA 自证，序言 `83ec5c 8b1534eca800` 完整）。
  Hook 是运行期内存改写，不体现在本卡的任何 PE 字节证据中。两者不可混为一谈。

---

## 7. 回绕 / 溢出

- 序列：`0x6F8DF3` 读 32 位 → `0x6F8E04 42 inc edx` → `0x6F8E09` 写回 32 位（§8 A7）。
- `inc` 在 32 位下 `0xFFFFFFFF → 0x00000000`，**无饱和、无跳过 0、无异常**；
  `0x6F8E04` 与写回之间只有 `0x6F8E05 897c2420`（写栈局部），
  **没有任何基于 ZF/SF/OF 的分支或补写**（§8 A2/A7）⇒ **纯模 2³² 回绕**。
- 处理要求（规格级，非实现）：跨回绕的差分必须按模 2³² 计算；
  **进程重启**导致的向下跳变**不是**回绕，必须与回绕区分并标「不可判」
  （`RULING_D19.md:59` 要求「重置/回绕/进程生命周期变化不能判明的区间标不可判」）。
- **是否实际发生回绕：未验**（无运行期数据；需约 4.29×10⁹ 次入口）。
- 静态镜像中**不存在** `0x0087E8E0` 那种回绕后再自增跳过 0 的补写（`FACTBASE_D19.md:32`、`:126-128`）。

---

## 8. 语义边界（★ 本卡最重要一栏）

### 8.1 **能说什么**

1. **能说**：在 SHA256 `73201cc0…f67476` 的**未打补丁镜像**中，`0x00A8EC34` 是 `0x6F8DF0`
   （`Greatest_Threat`）入口序言里一个 4 字节全局 dword 的读-改-写累加量；
   直接写点全集 = `{0x6F8E09 : 89 15 34 EC A8 00}`，由 `0x6F8DF3 : 8B 15 34 EC A8 00` 与
   `0x6F8E04 : 42` 喂值，已用 99.9984% 覆盖率的全流重同步解码 + 全文件裸 dword 扫描双证（§3）。
2. **能说**：从该入口进入**一次，值 +1（模 2³²）**，且自增在入口到写回之间无条件，
   早退路径（`0x6F8E41 ret 0xc`）也已计入（§3.2）。因此按 D-19 定谳措辞，
   称其为「**索敌入口调用累计代理**」（`RULING_D19.md:22` F6、`:57`、`:149`；`TASK.md:24`）。
3. **能说**：在**同一进程、同一未改码镜像、无回绕、无未验间接写**的前提下，
   两次读数之差 `Δ` 等于该区间内**进入 `0x6F8DF0` 的次数**；可用于报告
   「入口是否被调用 / 调用累计的相对变化 / 与其他观测量的关联」，**仅此**。
4. **能说**：它不是 `0x00B0CE88` 那样的瞬时队列 Count，也不是 `0x00A8ED50` 那样的容器 Count；
   没有活跃标志门控（§6.1）；符号名「未定名」（§1）。
5. **能说**：静态镜像中无第二个自增点、无复位/清零指令、无业务读点（§3、§4、§5）。

### 8.2 **不能说什么**

1. **不能说** = 完成的扫描次数 / 成功找到目标次数 / 实际扫过的 Cell 数 / 螺旋环数 /
   单候选评估次数 / 每次工作量 / 单次耗时 / C4 总耗时。
   理由：`0x6F8E41` 早退在写回之后（§3.2），函数体 `0xFC0` 字节、4 个 `ret`
   （`0x6F8E41/0x6F9B52/0x6F9B6B/0x6F9DAC`）之后的全部工作**均未被计数**；
   `RULING_D19.md:22`、`:103`、`FACTBASE_D19.md:37`、`:47` 同判。
2. **不能说** 是「防重入计数」/「重入深度」/「当前并发扫描数」。
   理由：全镜像无递减、无 `test`/`cmp`/`jcc` 以该值为操作数、无出口减一（§3、§4）；
   `ARCHITECTURE_ATLAS.md:1259`、`:1323` 的标签与字节冲突。
3. **不能**据 `Δ` 换算为可见单位数、实际工作量或耗时，也**不能**据此判定 C4 是主犯、
   给出四大成本中心占比或优化排序（`TASK.md:25-27`；`RULING_D19.md:39`、`:99`、`:149`）。
   `Q3_SAMPLE_PLAN.md:177` 的 `y_i = alpha_i * T_i` 矩阵 **无 alpha 校准依据**
   （`TASK.md:59-65` 待办；`RULING_D19.md:20`(F4)、`:39`），本卡不提供任何 alpha 值。
4. **不能**引用 `Q3_SAMPLE_PLAN.md:203` 的「300–1500 次/秒」与 `:275` 的「闲置 ≤10 次/秒」，
   也不能用 `:79-80` 的「`Δ≤50/s` ⇒ C4 排除、`Δ≥500/s` ⇒ C4 主犯」判据
   —— `TASK.md:30` 已判其为非实测、不得引用；且本字段无工作量信息。
5. **不能说**「绝对单调累加 / 全程序无减法 ⇒ 跨生命周期无条件单调」。
   理由：进程重启重新零填充（§5）、模 2³² 回绕（§7）、读档恢复未验（§5）、
   间接别名写未穷尽（§3.3）；`FACTBASE_D19.md:37` 自陈「不背书跨生命周期无条件单调」，
   `Q3_SAMPLE_PLAN.md:75`、`:201`、`:265` 的「绝对单调累加器 / Monotonic Integrators」为超限措辞。
6. **不能说**「1 Hz 已完全充分」「相邻帧间业务计数器完全冻结」「单帧 83 次重复信息熵增益为 0」
   —— `TASK.md:28`、`:31-33` 与 `RULING_D19.md:41` 已把这些降为未证/反证；
   `0x42CC80` 可在同步重试时再次推进代际戳 ⇒ 同帧号区间内业务字段并非冻结。
7. **不能说** 一次 4 字节读是「原子 16 字节快照」的一部分：四 VA 不连续，
   `RULING_D19.md:58`、`:101` 明令披露非原子性；读失败须记 `null` 不补 0（`:59`）。
8. **不能**把磁盘镜像语义无条件外推到运行期：`ra2render.dll` 的 9B Inline Hook 在节流帧
   **整次跳过自增**（§6.2），此时 `Δ` 计的是「非节流入口数」而非「入口数」。
9. **不能说** 符号名是 `GreatestThreatCallCount`、类型是 `uint32_t`（§1、§2）——前者是 W3 自拟标签，
   后者无符号性静态依据。

> **一句话边界**：本字段只能回答「`Greatest_Threat` **被进入了多少次**」，
> 不能回答「进去之后**做了多少事、花了多少时间、谁是真凶**」。

---

## 9. 可采性判定

**需补证**。

- **支持入候选清单**（不推翻 `TASK.md:22` 的已定谳采纳）：静态依据可定位到 VA+字节，
  直接写点全集已穷尽并附覆盖率自证，语义已按 D-19 收窄为「入口调用累计代理」。
- **尚不能进实际可采清单**的缺口（逐项见 §10）：
  ① 运行期字段有效性与扰动未验、且 D-17/D-19 双闸（候选代码、真机/活进程采集）
  **均须用户明示授权**，当前未授（`TASK.md:34`；`RULING_D19.md:61`、`:104`、`:149`）；
  ② `ra2render.dll` 运行时 Hook 门控在具体趟件中是否缺席未验（§6.2）；
  ③ 间接别名写 / 整对象拷贝 / 读档反序列化未穷尽（§3.3、§5）；
  ④ 回绕与跨进程生命周期单调性无运行期数据（§5、§7）；
  ⑤ 无历史数据可用：既有 Harness 不读该 VA（§4），`Q1_C3C4_PHYS_TARGET.md:318-319` 记
  `measure_w*.json` 从未采它；`D-19` 明令「不用旧 measure 验证新增字段真值」（`RULING_D19.md:57`）。
- 不判「不可采」：`TASK.md:22` 已采纳其为有静态依据的候选，且本卡已把依据补齐到字节级。
- 不判「可采」：`RULING_D19.md:37`、`:70` 明确「候选清单 ≠ 运行期有效性通过 / 观测卡可直接执行」。

---

## 10. 未验 / 诚实账

| # | 未验项 | 边界 |
|---|---|---|
| 1 | 间接别名写 / `rep movsd`·`memset` 整块拷贝 / `push 0xA8EC30` 三处 `call [vtable+0x27c]` 目标求解 | 本次未做间接 CFG / 虚表求解；绝对地址写点穷尽，全部运行期写**未穷尽**（§3.3） |
| 2 | 任一具体测量趟件的 S4 记录、`--allow-loader` 授权趟件中 `ra2render.dll` 是否在场 | 未检查（§6.2） |
| 3 | 读档/存档反序列化是否把本 dword 恢复为其它值 | 只核 `0x680A70` 前 `0x80` 字节，未穷尽（§5） |
| 4 | 实际发生 `0xFFFFFFFF→0` 回绕与否；跨进程/跨局单调性 | 无运行期数据（§5、§7） |
| 5 | 符号名、符号性（`int32`/`uint32`） | 无符号表、无比较指令（§1、§2） |
| 6 | 14 处 `call [reg+0x3c4]` 是否全部落到 `0x6F8DF0`（派生类覆写） | 未逐表解（§4） |
| 7 | 运行期字段有效性、数值分布、读数扰动、频率充分性 | D-19 明列未验且需授权（`RULING_D19.md:70`、`:100-103`） |
| 8 | 全量 `measure_w*.json` 的 `counters` 键逐一枚举 | 本次只核 Harness v4 常量表与 grep count=0（§4）；文档记载采信 `Q1_C3C4_PHYS_TARGET.md:319` |
| 9 | `Q1_C3C4_PHYS_TARGET.md:106` 的 `UnitClass::v[151] @0x00740B10 → 0x004D4280 → 0x004D9920` 完整链 | 本次只核到 `0x4D9920` 函数头与其内 `0x4D9942` 的 `call 0x6f8df0`（§8 A5） |

**本次明确已验**：目标 SHA256、节表/BSS 几何、序言全字节、唯一写点与唯一 `inc`、
入口到写回无条件、4 个 `ret` 位置、2 个直接调用者、`u32(0x7F4D24)`、
全流解码覆盖率、全文件裸 dword 出现次数、无 `imm32`/`lea` 别名、邻域 127 条访存、
无符号表、Hook 源码与紧邻注释、Harness 常量表与 S4 门。

---

## 11. 本次实跑命令与输出（可复核）

全部命令在 `D:/Project/ra2-campaign-forge` 下以 `python -I -X utf8` 运行（`TASK.md:108`），
读 `gamemd.exe` 一律 `sys.path.insert(0, r'...\swarm_20261104')` 后 `from ra2tool import Engine`
（`TASK.md:111`）。以下为实际执行的 heredoc 脚本要点与**原始输出节录**；
完整 stdout 落在本次会话临时日志（见各 A# 标注）。

**A1 · 快速 PE/序言/原始字节扫描**（`python -I -X utf8 - <<'PY' … PY`，本次前台实跑，退出码 0）：
```python
eng = Engine(); print("SHA256", eng.sha); print("IMAGE_BASE", hex(eng.IB))
for nm,sva,vsz,rp,rsz in eng.SEC: print(" ", nm, hex(sva), hex(vsz), hex(rp), hex(rsz))
VA=0x00A8EC34; print("VA fo(off)", eng.fo(VA), "u32", hex(eng.u32(VA)))
needle=struct.pack("<I",VA); occ=[]  # 全文件 find
print("RAW_DWORD_A8EC34_COUNT", len(occ))
for a,b,m,o in eng.disasm(0x6F8DF0, 0x50): print(" ", hex(a), b, m, o)
# .text 裸 E8/E9 目标 == 0x6F8DF0 的上界扫描
```
输出节录：
```
SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
IMAGE_BASE 0x400000
  .text 0x401000 0x3df38d 0x1000 0x3e0000
  .rdata 0x7e1000 0x30074 0x3e1000 0x31000
  .data 0x812000 0x367be4 0x412000 0x6c000
VA fo(off) None u32 0x0
BSS_CHECK .data delta 0x27cc34 rawsize 0x6c000 in_raw False
RAW_DWORD_A8EC34_COUNT 2
  off 0x2f8df5 .text:VA 0x6f8df5 ctx c418c20400909083ec5c8b1534eca8005355565733ff83cd
  off 0x2f8e0b .text:VA 0x6f8e0b ctx 83cdff8bf142897c2420891534eca8008b06896c241c896c
0x6f8df0 83ec5c sub esp, 0x5c
0x6f8df3 8b1534eca800 mov edx, dword ptr [0xa8ec34]
0x6f8e04 42 inc edx
0x6f8e09 891534eca800 mov dword ptr [0xa8ec34], edx
RAW_E8_TO_6F8DF0_UPPERBOUND 2 ['0x445f68', '0x4d9942']
RAW_E9_TO_6F8DF0_UPPERBOUND 0 []
```

**A2 · 全 `.text` 重同步解码普查**（前台转后台，退出码 0；完整输出在
`chatcmpl-tool-ae1d0469ca3a66ea-stdout.log`）：
```python
cov, nins, fails = eng.coverage
print("COVERAGE pct=%.14f insns=%d resync=%d .text_size=%d" % (cov,nins,fails,eng.TSZ))
hits = eng.disp_hits(0xA8EC34); print("DISP_HITS_0xA8EC34 count=%d" % len(hits))
```
输出：
```
SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
COVERAGE pct=99.99837567729335 insns=1394120 resync=66 .text_size=4063232
DISP_HITS_0xA8EC34 count=2
   0x6f8df3 R mov edx, dword ptr [0xa8ec34] 8b1534eca8005355
   0x6f8e09 W mov dword ptr [0xa8ec34], edx 891534eca8008b06
OPSTR_MENTIONS count=2
ABS_MEM_OPERANDS_WITH_THIS_DISP count=2
```

**A3 · 别名/重叠/边界/虚表/回绕**（`chatcmpl-tool-92f558ececd6dd64-stdout.log`、`chatcmpl-tool-ab51f6b744558e6e-stdout.log`，退出码均 0）：
```
OVERLAPPING_ABSOLUTE_MEM_OPS ... COUNT 2   (仅 0x6f8df3 / 0x6f8e09, size 4)
IMM32_LOADS_OF_VA ... count=0 []
LEA_VA count 0
RETS in [0x6F8DF0,0x6F9DB0) count=4: 0x6F8E41 / 0x6F9B52 / 0x6F9B6B / 0x6F9DAC (均 c20c00)
EXTERNAL BRANCHES LANDING INSIDE (0x6F8DF0,0x6F8E09] count=0
DIRECT CALLERS: 0x445f68 e8832e2b00 ; 0x4d9942 e8a9f42100  (count 2)
u32(0x7F4D24) = 0x6f8df0 (vtable[241] per ra2render.h:32) ; 241*4 = 0x3c4
CALL [reg+0x3C4] count=14
WRAPAROUND CHECK 0x6F8E04..0x6F8E0F: 006F8E04 42 inc edx / 006F8E05 897c2420 / 006F8E09 891534eca800
ALL RAW OCCURRENCES OF THE DWORD ... count 2 (.text VA 0x6f8df4 / 0x6f8e0a)
WHOLE-FILE RAW LE DWORD 0xA8EC34 OCCURRENCES 2: file_off 0x2f8df5 / 0x2f8e0b
BLOCK #26 SAVE CALL SITE 0067E24F e81c280000 call 0x680a70 ; head 00680A76 8bfa mov edi,edx ; 00680A7C 8b4710 mov eax,[edi+0x10]
```

**A4 · 残余间接线索**（P01 缓存上下文，前台实跑）：
```
0065AAAB 6830eca800 push 0xa8ec30 ; 0065AAB1 ff907c020000 call dword ptr [eax + 0x27c]
0065ACC3 6830eca800 push 0xa8ec30 ; 0065ACC9 ff927c020000 call dword ptr [edx + 0x27c]
0065AD05 6830eca800 push 0xa8ec30 ; 0065AD0D ff927c020000 call dword ptr [edx + 0x27c]
（三处虚调用目标未求解 ⇒ §3.3 残余）
```

**A5 · 邻域/CRT/调用者/函数边界**（`chatcmpl-tool-9804c66e0370399e-stdout.log`，退出码 0）：
```
ALL DECODED INSTRUCTIONS WITH ABSOLUTE DISP IN [VA-0x20,VA+0x20] count 127
  ... 004E67E7 a33ceca800 / 004E67FD c70538eca800e49c7e00 / 004E7287 a32ceca800 ...
  006F8DF3 8b1534eca800 R ; 006F8E09 891534eca800 W   ← 区间内 disp==VA 仅此 2 条
BOUNDARY BEFORE 0x6F8DF0: 006F8DEB c20400 ret 4 / 006F8DEE 90 / 006F8DEF 90
CALLER 0x445F68 e8832e2b00 call 0x6f8df0 ; CALLER 0x4D9942 e8a9f42100 call 0x6f8df0
BSS: section .data VA 0x812000 vsize 0x367be4 rawsize 0x6c000 delta 0x27cc34 zero_fill True
```

**A6 · 无条件自增 + 早退**（`chatcmpl-tool-8c9cca4c077d2731-stdout.log`，退出码 0）：
```
=== EARLY RETURN PATH 0x6F8E19..0x6F8E44 ===
  006F8E19 ff9084000000 call [eax+0x84] ; 006F8E27 741b je 0x6f8e44
  006F8E2F e8fc28e1ff call 0x50b730 ; 006F8E36 740c je 0x6f8e44 ; 006F8E41 c20c00 ret 0xc
=== jcc/cmp/test between entry 0x6F8DF0 and writeback 0x6F8E09 ===
  count 0
=== symbol files present? ===
ra2youli/ECH01.MAP
ra2youli/ECH02.MAP
ra2youli/ECH03.MAP
(end)
```
（该日志尾部的 `find` 只列出三张地图文件，非 linker map。）

**A7 · 符号表缺失**
```
MAGIC 0x10b
EXPORT rva 0x0 size 0x0
DEBUG rva 0x3e1610 size 0x1c
DEBUG_RAW 000000004e54df3b0000000004000000100100000000000000704900
```
```
DEBUG_DIR RVA 0x3e1610 size 0x1c
try off 0x3e1610 type 4 sizeOfData 0x110 ptrRaw 0x497000
  DATA b'@\x00\x00\x00Dtr\x00\xc0%\x00\x00...'
RSDS count 0 NB10 count 0 '.pdb' count 0
```
（type=4 = `IMAGE_DEBUG_TYPE_MISC`；无 CodeView/PDB、无导出表 ⇒ 无符号表。）

**A8 · 既有 Harness 不读本 VA / S4 门**（前台实跑 `grep`）：
```
grep -n "MEASURE_.*_VA\s*=" ... → 3831..3841 共 9 个常量，无 0xA8EC34
grep -c "A8EC34\|a8ec34" qc151_trip.harness8_v4.py → 0
grep -n "DLL_PROCESS_ATTACH\|InstallVTableHooks" ra2render/dllmain.cpp → 27: / 31:
```

**未运行**：`gamemd.exe` / `ra2loader.exe` / `YURI.exe` 启动、`taskkill`、任何活进程内存读、
任何 `ReadProcessMemory`/hook/MiniDump/SuspendThread 实现、任何测试套件或构建、任何 `git commit`/`push`。
本次对 `ra2render/*`、`ra2youli/*`、`lead/*`（除本写域）均只做只读操作。

---

*本卡为静态规格，不是实现；实现与采集须用户明示授权（`TASK.md:34`、`RULING_D19.md:61`、`:149`）。*
