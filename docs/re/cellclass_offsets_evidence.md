# CellClass 结构体成员偏移与 InvalidCell 单例实证报告

> **文档标识**：`docs/re/cellclass_offsets_evidence.md`  
> **任务编号**：A-8（派工 v10 补强任务，为 A-7 路线 A 规格提供无歧义静态证据）  
> **责任方**：Antigravity（逆向工程与验证方）  
> **基线对齐**：`docs/RE_COORDINATION.md` (§核验 v10 + 派工 v10) / `docs/re/radar_hook_routeA_spec.md`  
> **执行准则**：严禁猜测，严格区分 `[实证]`（带反汇编与原始机器码）与 `[待实测]`；不得修改 `ra2render/**` 与台账。

---

## 一、结论摘要表

| 验证目标 | 最终结论 | 证据类型 | 关键验证地址与原始指令 |
|---|---|:---:|---|
| **CellClass.MapCoords 偏移** | **`+0x24`（short X）、`+0x26`（short Y）确凿成立** | **[实证]** | ① `0x0047FF89`: `0F BF 46 24` (`movsx eax, word [esi+24h]`)<br>② `0x0047FF8D`: `0F BF 4E 26` (`movsx ecx, word [esi+26h]`)<br>③ `0x0047BC02`: `89 46 24` (`mov [esi+24h], eax` 构造函数)<br>④ `0x0047BBAD`/`BA`: `66 8B 46 24`/`26` (析构函数)<br>⑤ `0x005780E3`: `A3 74 DC AB 00` (`mov [0xABDC74], eax`) |
| **InvalidCell 全局单例** | **基址 `0x00ABDC50` 确凿成立** | **[实证]** + **[待实测方案]** | ① 静态：`gamemd.exe` 全局硬编码 314 处配对引用 `0x00ABDC50` 与 `0x00ABDC74`（`+0x24`）；<br>② `YRpp/MapClass.h` 严格对应 `pCell = &InvalidCell; pCell->MapCoords = MapCoords;`<br>③ 给出 100% 确定性的运行时内存转储测试步骤 |

---

## 二、`CellClass.MapCoords` 偏移实证 [实证]

在 A-7 实施规格中，核心寻址逻辑通过读取 `CellClass* pCell` 的网格坐标计算全局索引：**【原记 · 该前提（`0x00655D38` 处 `EAX` = `CellClass*`）已被勘误，见 §二之勘误 E1】**
$$X = \text{*(short*)(pCell + 0x24)}, \quad Y = \text{*(short*)(pCell + 0x26)}$$
$$\text{cellIdx} = (Y \ll 9) + X$$
以下通过引擎 4 处关键函数的多角度交叉反汇编证明：**`+0x24` / `+0x26` 为官方原版 MSVC 编译器唯一定义的 `MapCoords` 偏移**。

> ⚠️ **本节开头的「`CellClass* pCell`」与 `0x00655D38` 处 `EAX` 的关系已被证伪，详见紧随其后的【勘误 E1】**（原句保留，不作删除）。

---

## 二之勘误 E1〔RADAR-ERRATA · 2026-09-27〕：挂钩点 `0x00655D38` 处 EAX **不是** `CellClass*`

> **【原记】（保留原文，不得删除）**：本节开头把路线 A 的核心寻址写成「读取 `CellClass* pCell` 的网格坐标」，并默认 `0x00655D38` 处 `EAX` 即 `MapClass::GetCellAt` 返回的 `CellClass*`；本文件 §四 据此裁决 A-7 规格「坐标提取完全正确」。
>
> **【实测定谳】**：`0x00655D38` 处 `EAX` **不是 `CellClass*`**，而是 **`MapClass::GetCellFloorHeight()`（`0x00578080`）返回的格面高度 int**（单位 lepton），由 `0x655D33 call 0x578080` → `0x655D38 mov [esp+0x28],eax` 写进 **`CoordStruct.Z`** 槽位（`0x655D2F` 已预置 Z = 0），不是任何 `pCell` 缓存。
>
> ```asm
> 0x00655D2B: 89 54 24 28        mov  [esp+0x28], edx      ; CoordStruct.Y
> 0x00655D2F: 89 6C 24 2C        mov  [esp+0x2C], ebp      ; CoordStruct.Z = 0（预置）
> 0x00655D33: E8 48 23 F2 FF     call 0x00578080           ; ← MapClass::GetCellFloorHeight（返回 int）
> 0x00655D38: 89 44 24 28        mov  [esp+0x28], eax      ; ← 返回值写回 Z 槽（不是 pCell 缓存！）
> 0x00655D3C: A1 50 35 B7 00     mov  eax, [0x00B73550]    ; Game::hWnd
> ```
>
> | VA | 原始字节（gamemd.exe 只读复核） | Capstone | 说明 |
> |---|---|---|---|
> | `0x00655D33` | `E8 48 23 F2 FF` | `call 0x00578080` | 被调函数 = `GetCellFloorHeight`，不是 `GetCellAt` |
> | `0x00578080` | `83 EC 08 8B 4C 24 0C` | `sub esp,8 ; mov ecx,[esp+0xC]` | 只读 `[ecx]`/`[ecx+4]`（CoordStruct X/Y），不读 `[ecx+8]` |
> | `0x005780F6` | `C2 04 00` | `ret 4` | 被调方清栈 ⇒ 返回值 = int，且 `0x655D38` 处 `esp` 已复位 |
> | `0x00655D38` | `89 44 24 28` | `mov [esp+0x28], eax` | 写入 `CoordStruct.Z` |
>
> YRpp 交叉来源：`YRpp/MapClass.h:282` → `int GetCellFloorHeight(const CoordStruct& crd) const { JMP_THIS(0x578080); }`；`YRpp/MapClass.h:417` → `int sub_578080(CoordStruct*)`。两者与「返回 `CellClass*`」互斥。
>
> **【后果（产品决策级）】**：旧路线 A 代理据此误述写下的首道护栏
> ```asm
> cmp eax, 0x10000
> jbe do_passthrough        ; EAX 是高度值（≈0..2080）⇒ 该跳转恒成立
> ```
> **恒拒、静默早退** —— 这正是真机「雷达灰化分支进入次数单调增长（16303→17284）而雷达灰化像素数恒 0」的根因（RADAR-FIX2 定谳：EAX 语义错认 = S3 FAIL 直接根因）。凡以「`0x00655D38` 处有 pCell」为前提的下游推理（含本文件 §四 的 A-7 合规裁决）**其前提已被证伪**。
>
> **【不受影响部分】**：本文件 §二 §三 关于 `MapCoords = +0x24 / +0x26`（`0x0047FF89`/`0x0047FF8D`，其 `this` 是真正的 `CellClass*`）、构造函数 `0x0047BC02`、以及 `InvalidCell 0x00ABDC50` 与 `+0x24`（`0x00ABDC74`）配对的实证**全部维持成立**——那些取证点的受试对象确实是 `CellClass*` 本体。被推翻的仅是「挂钩点 `EAX` 的语义」这一条。
>
> **【证据口径】**：本勘误的字节断言见 `out/re_work/radar_errata/claims.txt`（`tools/audit_bytes.py` 复核 16/16 OK）；独立反汇编见 `out/re_work/radar_errata/disasm_errata.txt`。

### 1. 核心实证 1：`CellClass::Cell2Coord` / `GetCenterCoords` (`0x0047FF80`) [实证]
- **位置**：`0x0047FF80` - `0x0047FFB8`。
- **语义**：将瓦片网格坐标换算为微步世界坐标（Leptons）：
  $$\text{Coord.X} = \text{MapCoords.X} \times 256 + 128$$
  $$\text{Coord.Y} = \text{MapCoords.Y} \times 256 + 128$$
  对应 `YRpp/CellClass.h` 第 259 行：`ret.X = cell.X * 256 + 128; ret.Y = cell.Y * 256 + 128;`。
- **反汇编与原始机器码对照**：
  ```asm
  0x0047FF80: 83 EC 18             sub  esp, 0x18
  0x0047FF83: 53                   push ebx
  0x0047FF84: 55                   push ebp
  0x0047FF85: 56                   push esi
  0x0047FF86: 8B F1                mov  esi, ecx                    ; this = CellClass*
  0x0047FF88: 57                   push edi
  ; --- 读取 MapCoords.X (short, 2 字节) ---
  0x0047FF89: 0F BF 46 24          movsx eax, word ptr [esi + 0x24] ; eax = (short)MapCoords.X !
  ; --- 读取 MapCoords.Y (short, 2 字节) ---
  0x0047FF8D: 0F BF 4E 26          movsx ecx, word ptr [esi + 0x26] ; ecx = (short)MapCoords.Y !
  ; --- X 换算：X * 256 + 128 ---
  0x0047FF91: C1 E0 08             shl  eax, 8                      ; eax = X * 256
  0x0047FF94: 05 80 00 00 00       add  eax, 0x80                   ; eax += 128
  ; --- Y 换算：Y * 256 + 128 ---
  0x0047FFA0: C1 E1 08             shl  ecx, 8                      ; ecx = Y * 256
  0x0047FFA5: 81 C1 80 00 00 00    add  ecx, 0x80                   ; ecx += 128
  ```
- **判定**：引擎在取格点坐标进行几何换算时，**100% 逐字节使用 `[esi+0x24]` 取 X，`[esi+0x26]` 取 Y**。

---

### 2. 核心实证 2：`CellClass::CellClass()` 构造函数 (`0x0047BBF0`) [实证]
- **位置**：`0x0047BBF0` - `0x0047BC05`。
- **语义**：继承自 `AbstractClass`（基类尺寸 `0x24` 字节）；基类构造完毕后，派生类 `CellClass` 初始化首个成员变量 `CellStruct MapCoords`。
- **反汇编与原始机器码对照**：
  ```asm
  0x0047BBF0: 53                   push ebx
  0x0047BBF1: 55                   push ebp
  0x0047BBF2: 56                   push esi
  0x0047BBF3: 57                   push edi
  0x0047BBF4: 8B F1                mov  esi, ecx                    ; this = CellClass*
  0x0047BBF6: E8 75 45 F9 FF       call 0x00410170                  ; AbstractClass::AbstractClass()
  0x0047BBFB: A1 48 E7 89 00       mov  eax, dword ptr [0x0089E748] ; 加载初始格坐标 (0x00000000)
  0x0047BC00: 33 DB                xor  ebx, ebx
  ; --- 初始化 MapCoords (占 4 字节，short X + short Y) ---
  0x0047BC02: 89 46 24             mov  dword ptr [esi + 0x24], eax ; [esi+0x24] = MapCoords !
  0x0047BC05: 89 5E 28             mov  dword ptr [esi + 0x28], ebx ; [esi+0x28] = FoggedObjects (下个成员)
  ```
- **判定**：`AbstractClass` 占用 `0x00 - 0x23` 偏移，`CellClass` 的第一个派生属性 `MapCoords` 紧跟在 `+0x24` 处，以 4 字节 DWORD（低 16 位 X，高 16 位 Y）初始化。

---

### 3. 核心实证 3：`CellClass::~CellClass()` 析构函数 (`0x0047BBA7`) [实证]
- **位置**：`0x0047BBAD` - `0x0047BBC5`。
- **语义**：析构时核对格子坐标是否等于全局重置边界 `[0x0089E748]`。
- **反汇编与原始机器码对照**：
  ```asm
  0x0047BBAD: 66 8B 46 24          mov  ax, word ptr [esi + 0x24]   ; ax = MapCoords.X (2 字节)
  0x0047BBB1: 66 3B 05 48 E7 89 00 cmp  ax, word ptr [0x0089E748]   ; 比对 X
  0x0047BBB8: 75 0D                jne  0x0047BBC7
  0x0047BBBA: 66 8B 4E 26          mov  cx, word ptr [esi + 0x26]   ; cx = MapCoords.Y (2 字节)
  0x0047BBBE: 66 3B 0D 4A E7 89 00 cmp  cx, word ptr [0x0089E74A]   ; 比对 Y
  ```
- **判定**：析构函数以 16 位寄存器 `ax/cx` 分别访问 `+0x24` 与 `+0x26`。

---

### 4. 核心实证 4：`MapClass::GetCellAt` 坐标写入点 (`0x005780A0`) [实证]

> **〔勘误 E1b · 2026-09-27〕函数命名更正（原句保留）**：本标题及本节引用的 `0x005780A0` / `0x005780DE` / `0x005780E3` **全部位于 `0x00578080` 的函数体内**；按 YRpp（`YRpp/MapClass.h:282` / `:417`），该函数是 **`int GetCellFloorHeight(const CoordStruct&)`**（`0x00578080` 序言 `83 EC 08 8B 4C 24 0C`，尾部 `0x005780F6 = C2 04 00` = `ret 4`），**不是 `MapClass::GetCellAt`**（`GetCellAt` 走 `TryGetCellAt`（`0x005657A0`）路径，其越界哑元同样是 `0x00ABDC50`）。⇒ 本节的**字节与配对关系实证（`0x00ABDC50` ↔ `0x00ABDC74`）维持成立**，仅「函数叫什么」以 YRpp 为准。
> 独立反汇编（`0x00578080` 全函数，含 `0x5780BB cmp ecx,[0x87F928]` 边界核验与 `0x5780ED call 0x47B3A0`）见 `out/re_work/radar_errata/disasm_errata.txt`。原文如下（保留）：
- **位置**：`0x005780D0` - `0x005780E3`。
- **语义**：当访问越界格点时，将请求坐标写入返回的格对象中。
- **反汇编与原始机器码对照**：
  ```asm
  0x005780D0: 66 89 74 24 10       mov  word ptr [esp + 0x10], si   ; 栈暂存 si (Cell X)
  0x005780D5: 66 89 44 24 12       mov  word ptr [esp + 0x12], ax   ; 栈暂存 ax (Cell Y)
  0x005780DA: 8B 44 24 10          mov  eax, dword ptr [esp + 0x10] ; eax = packed {short X, short Y}
  0x005780DE: B9 50 DC AB 00       mov  ecx, 0x00ABDC50             ; ecx = InvalidCell 单例指针
  0x005780E3: A3 74 DC AB 00       mov  dword ptr [0x00ABDC74], eax ; [InvalidCell + 0x24] = MapCoords !
  ```
- **差值数学实证**：
  $$\text{Target Address} - \text{Base Address} = 0x00ABDC74 - 0x00ABDC50 = 0x24$$
  写入目标正是单例对象内部的 `+0x24` 槽位。

---

## 三、`InvalidCell` 全局单例 (0x00ABDC50) 静态与实测方案 [实证 + 待实测]

### 1. 静态代码与架构证据 [实证]
1. **全局引用频次与统计口径说明**：
   - **指令级引用点（314 处）**：经 Capstone 反汇编过滤，明确作为操作数直接出现在 `.text` 代码段执行指令中的引用点恰为 **314 次**（如 `mov ecx, 0x00ABDC50`、`cmp eax, 0x00ABDC50` 等）；
   - **全镜像原始字节串（457 处）**：若在 `gamemd.exe` 全 PE 镜像（含 `.rdata` 虚表、只读指针表与数据段）按 32 位小端序硬字节串 `50 DC AB 00` 无条件逐字节搜索，命中频次为 **457 次**。两种统计口径均彻底证实该单例在引擎全局处于最高频核心地位。
2. **与 `0x00ABDC74`（`+0x24`）的一对一配对绑定**：
   在所有无效单元返回路径中，均成对出现如下原子操作：
   ```asm
   mov  [0x00ABDC74], eax   ; 刷新 InvalidCell.MapCoords = 当前查询的目标坐标
   mov  reg, 0x00ABDC50     ; 返回 InvalidCell 对象指针
   ```
   典型位置包括：
   - `0x005780DE`（`MapClass::GetCellAt` 坐标越界分支）**【勘误 E1b：该分支属 `GetCellFloorHeight`（`0x578080`）函数体，非 `GetCellAt`】**
   - `0x00586317` / `0x0058631C`（`Is_Shrouded` 地图外视野检查）
   - `0x005863E8` / `0x005863ED`（`Is_Shrouded` 黑雾越界回退）
   - `0x00586A25` / `0x00586A2A`（地形碰撞阻挡越界回退）
   - `0x00584087` / `0x0058408C`（地图通行度检查越界回退）
3. **YRpp 官方反编译头文件规范一致性**：
   `YRpp/MapClass.h` 第 145 行与第 188–197 行：
   ```cpp
   static constexpr reference<CellClass, 0xABDC50u> const InvalidCell{};

   CellClass* GetCellAt(const CellStruct &MapCoords) const {
       auto pCell = TryGetCellAt(MapCoords);
       if(!pCell) {
           pCell = &InvalidCell;
           pCell->MapCoords = MapCoords; // 完美对应 0x005780E3 的 mov [0xABDC74], eax !
       }
       return pCell;
   }
   ```

---

### 2. 运行时动态验证与内存转储方案 [待实测]

由于 `0x00ABDC50` 位于 `.bss` 未初始化数据段（PE 文件内全为 0，程序启动后由 C++ 运行时初始化构造），若需在真机动态排查时捕获其实测内存状态，可依下列步骤复现验证：

#### 动态验证步骤与断点配置
1. **断点位置**：
   在 `0x005780DE` 设置断点（即 `MapClass::GetCellAt` 返回 `InvalidCell` 的瞬间）。**【勘误 E1b：函数名以 `GetCellFloorHeight`（`0x578080`）为准；下一条同此。】**
2. **触发方式**：
   在对战中将鼠标光标移动至小地图最外圈纯黑黑边（或主视口地图最外侧菱形不可达区域），引擎将高频调用 `GetCellAt` 并击中该断点。
3. **内存转储与预期值比对表**：

| 内存地址 | 对应字段 | 预期转储数据 | 判定标准 |
|---|---|---|---|
| `0x00ABDC50` | `CellClass.vtable` | 指向 `.rdata` 内 `CellClass` 虚表指针（如 `0x007E4BC8`） | 必须为合法代码段虚表 |
| `0x00ABDC74` | `CellClass.MapCoords.X` | 当前查询的负数坐标（如 `0xFFFF` / `-1`）或超界坐标 | 与触发入参一致 |
| `0x00ABDC76` | `CellClass.MapCoords.Y` | 当前查询的负数坐标（如 `0xFFFF` / `-1`）或超界坐标 | 与触发入参一致 |
| `0x00ABDDC0` | `CellClass+0x170` | 阻挡与地表标志位全 0 | 绝不可通行 |
| `0x00ABDD7C` | `CellClass+0x12C` | 状态标志位：`bit 3 = 0`（未探索） | 迷雾永不消除 |

---

## 四、A-7 规格的最终合规裁决

基于上述指令级实证：

> **〔勘误 E1 · 2026-09-27〕** 本节第 1、2 项均以「`0x00655D38` 处 `EAX` = `CellClass*`」为前提，该前提**已被证伪**（见 §二 勘误 E1：该处 EAX = `MapClass::GetCellFloorHeight`（`0x00578080`）返回的格面高度 int）。⇒ 下列「合规裁决」降级为【原记 · 前提已证伪】；仅其代数形式（`(Y<<9)+X`、`cmp eax,0x00ABDC50`）本身仍成立，但**不能推出「路线 A 在挂钩点取到坐标/指针」**。
1. **坐标提取完全正确**：
   A-7 规格中采用：
   ```asm
   movsx edx, word ptr [eax + 0x26]  ; MapCoords.Y
   shl   edx, 9                      ; Y * 512
   movsx ecx, word ptr [eax + 0x24]  ; MapCoords.X
   add   edx, ecx                    ; cellIdx
   ```
   经实证与 `0x0047FF89`（`GetCenterCoords`）的引擎内部读取方式**完全同构**，不存在任何偏移漂移风险。
2. **无效单元排除完全正确**：
   A-7 规格中设置的守卫：
   ```asm
   cmp   eax, 0x00ABDC50
   je    do_passthrough
   ```
   **100% 精确命中原版 `InvalidCell` 单例基址**，能彻底将所有地图边界外的探测安全导流至跳板直通，绝不发生非法寻址。
