# W8·F6 定位回件 · 真实视口坐标 / 当前可见世界矩形

```
被核对象 = gamemd.exe（+ TASK.md §1 所引前置件：D17_STATIC_FIELDS.md / D20_B_VISIBILITY_GAP.md /
           W3_COSTBOUND/sections/Q1_C2_RENDER.md / W3_COSTBOUND/sections/Q1_C3C4_PHYS_TARGET.md /
           W4_FIELD_SPEC/sections/card_00A8EC34.md / 主台账 GOAL_RE_CONTINUOUS.md §563/§566）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
Engine 自证 = COVERAGE 99.99837567729335（1394120 insns / resync 66 / .text 4063232）/ IMAGEBASE 0x400000
回件时刻 = 2026-11-06 01:34:31
```

> 探针：`_w8_f6.py`（`python -I -X utf8` 独立跑完，exit=0，160.5 s）→ `_w8_f6_out.txt`（460 行）。
> 本文每个地址都可在 `_w8_f6_out.txt` 里按 VA 检索到原始字节行；无一处转抄他人文字。
> 纯静态：零真机、零活进程、零注入；唯一写域 = 本目录。

## 0. 一句话总判

**LOCATED。** TASK 给的 `0x432A35` 线索是**死胡同**（它是 Bink 电影播放器的打开函数，与战术视口无关）；
真实视口坐标在 **TacticalClass 堆实例（单例槽 `0x887324`）内**：
**`+0xB0/+0xB4`（dword×2）= 视口左上角屏幕像素原点**，由 `0x6D8B30` 按
`当前滚动位置(+0xD64/+0xD68) − 屏宽高/2(0xB0CE30/0xB0CE34)` 每帧重算；
**当前可见世界矩形（格空间）= `+0xD80/+0xD84`（左上格）与 `+0xD88/+0xD8C`（跨度）**，同函数写出、
`0x6D8AE0` 作格包含判定、`0x6D2140 IsVisible` 作世界→屏幕裁剪消费。
`DSurface+0x1C` 定谳为 **LPDIRECTDRAWSURFACE（DirectDraw COM 表面接口指针）**，非坐标非矩形。

---

## 1. F6-1 · `0x432A35` 所在函数：完整边界与绘制链位置

### 1.1 边界（字节自证）

- **完整边界 = `[0x432750, 0x432A50]`**：
  - 头 `0x432750: 83 ec 68  sub esp, 0x68`（thiscall，`ret 4` 一个栈参）；
  - 尾 `0x432A50: c2 04 00  ret 4`；
  - 其后 `0x432A53..0x432A5F` 为 13 条 `90` NOP 填充，下一函数区从 `0x432A60` 起
    （`_w8_f6_out.txt` §B）。
- 内部两个出口：`0x432874 ret 4`（失败路径：`BinkOpen` 为 0 → `call [0x7E1598] BinkGetError` →
  打印 `0x818B2C "Bink Error: %s\n"` → `xor al,al; ret 4`）与 `0x432A50 ret 4`（成功，`mov al,1`）。

### 1.2 语义判名：Bink 电影播放器的「打开/播放」函数

全部外部调用均为 IAT 可判名（`_w8_f6_out.txt` §B，`Engine.resolve_iat` 实测）：

| 调用点 | IAT | 解析 |
|---|---|---|
| `0x4327D7/0x43277D` | `0x7E11BC/0x7E15A4` | `KERNEL32!CreateFileA` / `binkw32!_BinkClose@4` |
| `0x43283A` | `0x7E11C0` | `KERNEL32!SetFilePointer` |
| `0x43278F` | `0x7E11E0` | `KERNEL32!CloseHandle` |
| `0x4327B4` | `0x7E1590/0x7E1594` | `binkw32!_BinkSetSoundSystem@8` / `_BinkOpenDirectSound@4` |
| `0x432849` | `0x7E159C` | `binkw32!_BinkOpen@8`（HBINK 存 `[esi+4]`） |
| `0x432897` | `0x7E15A0` | `binkw32!_BinkSetVolume@8` |
| `0x432917` | `0x7E14C4` | `USER32!GetClientRect`（居中用） |
| `0x432A3E` | `0x7E15A8` | `binkw32!_BinkDDSurfaceType@4` |

函数体流程：打开 .bink 文件 → `BinkOpen` → 帧率/音量 → `GetClientRect`（或取 `DSurface::Hidden`
vtable[31]/[32] 尺寸）居中 → 与电影分辨率（HBINK+0x14/+0x18 宽高，`0x4328A2..0x4328A5`）做
**裁剪矩形求交** → 结果 4 dword 写入电影对象 `[esi+0x10..0x1C]` →
`BinkDDSurfaceType(DSurface::Primary→+0x1C)` 存 `[esi+8]`。

### 1.3 绘制链位置：**不在战术绘制链**

- 直接调用者仅 2 处：`0x4326B3`、`0x4326E9`，都在 **3 指令级 wrapper/构造 `0x4326C0..0x4326F1`**
  （`[esi+0xC]=参数`、字段清零、`[esi+0x28]=-1`，然后 `call 0x432750`）；
- `0x4326C0` 的调用者 = `0x5C0878 / 0x5CC7F6`；姊妹函数 `0x432700` 的调用者 =
  `0x5BEEF3 / 0x5C0613 / 0x5C0A43 / 0x5CC833 / 0x5CEC83` —— 全部落在 **0x5BExxx–0x5CExxx
  电影/过场系统**（与 `_w8_f6_out.txt` §B 一致）。
- 该函数**不引用** `0x887324`（Tactical 单例）、**不调用** `0x6D2140`（IsVisible）、
  **不在** 渲染主簇 `0x6D8DB0..0x6DA1FB`（D-20 已证该簇零 `DrawIfVisible`）——
  它是过场电影播放层（Bink→`DSurface::Primary/Hidden` blit），与 C2 战术渲染管线零交集。

### 1.4 对 TASK 线索本身的勘误

- **「0x432A29..0x432A32 写 8 个 dword」不成立**：实写 **4 个 dword**——
  `0x432A26 lea ebx,[esi+0x10]`；`0x432A29 mov [esi+0x10],eax`；`0x432A2C mov [ebx+4],ecx`；
  `0x432A2F mov [ebx+8],edx`；`0x432A32 mov [ebx+0xC],edi`。
  即电影对象 `+0x10` 处一个 **RECT**（电影在屏幕上的目的地裁剪矩形），不是 8 dword 结构。

---

## 2. F6-2 · `DSurface+0x1C` 到底是什么

**定谳：`+0x1C` = LPDIRECTDRAWSURFACE —— DirectDraw 表面的 COM 接口指针（一个 4 字节指针）。
不是坐标、不是矩形、不是尺寸。** 三条独立证据链：

1. **RTTI**（§563 一致性复核）：`vtable 0x7E85D4` → `COL=0x800260` → 类型描述符名
   `".?AVDSurface@@"`（`_w8_f6_out.txt` §C）。
2. **DSurface 构造器 `0x4BA5A0`（`ret 0x10`）把 `+0x1C` 当 CreateSurface 出参**：
   - `0x4BA5B0 lea ebp,[esi+0x1C]`、`0x4BA5CA mov [ebp],ebx`（初值 NULL）；
   - `0x4BA5F7 mov [edx],0x6C`（`[esi+0x20]` 处的 DDSURFACEDESC，dwSize=0x6C=108）；
   - `0x4BA645..0x4BA656`：取 `[0x8A0094]`（DirectDraw 包装对象），`mov ecx,[eax]`，
     `call dword ptr [ecx+0x18]` —— **IDirectDraw 虚表槽 6 = CreateSurface（0x18=6×4）**，
     实参 `(ddsd, ebp=&this->0x1C, 0)`，随后 `0x4BA656 cmp [ebp],ebx / je 失败`；
   - 紧随 `0x4BA678 call [ecx+0x58]`（槽 22 = **GetSurfaceDesc**，0x58=22×4，实参
     `(lpdds=[ebp], &ddsd)`）取回 pitch/位深（`0x4BA680..0x4BA689`：`([ddsd+0x54]+7)>>3`
     存 `+0x10` = 每像素字节数——尺寸类字段在 `+0x10`，不在 `+0x1C`）。
   - 同构写 vtable 点全镜像 6 处：`0x4BA5D0/0x4BA6B9/0x4BA740/0x4BA814/0x4BAC86/0x4C1AC6`。
3. **消费方**：`0x432A35 mov eax,[0x887308]`（DSurface::Primary）→ `0x432A3A mov eax,[eax+0x1C]`
   → `0x432A3D push eax` → `0x432A3E call [0x7E15A8]` = **`binkw32!_BinkDDSurfaceType@4`**，
   该 Bink SDK 函数的形参就是 LPDIRECTDRAWSURFACE（返回表面类型 VRAM/系统内存）。

⇒ `0x00432A3A mov eax,[eax+0x1C]` 读到的是**指针**，后续只做 `push`+`call`，无任何坐标语义。

---

## 3. F6-3 · 当前可见世界矩形：谁计算、写到哪里

### 3.1 承载对象：TacticalClass 堆实例，单例槽 `0x887324`

- 构造器 `0x6D1C20`（头 `push ebx/esi/edi; mov esi,ecx; call 0x410170` 基类；尾 `0x6D1E1E
  mov [0x887324],esi; ret`）；vtable 写入 `0x6D1D54 mov [esi],0x7F4348`
  （次级 vtable `+4/+8/+0xC = 0x7F432C/0x7F4324/0x7F431C`）；**sizeof = 0xE18**
  （创建点 `0x687604 push 0xE18; call 0x7C8E17`（new）→ `0x687617 call 0x6D1C20`）。
- 构造器 5 个调用点（= 实例创建/重建点）：`0x52C694 / 0x599D80 / 0x6853B4 / 0x687617 / 0x6BF84F`，
  与 `0x887324` 的全部 11 处 W 写点对应（`_w8_f6_out.txt` §D）；
  置空点：`0x6D1E9B`（vtable 槽清 dtor）与 `0x6DC48E`（**vtable[8]=0x6DC470 deleting dtor 体内**）。
- `0x887324` 全镜像 461 处引用（1 处 `cmp`，其余读入 ecx/edx/eax 后 thiscall）。

### 3.2 ★ 视口像素原点：`[T+0xB0]/[T+0xB4]`（dword×2，屏幕像素）

**唯一业务写者 = `0x6D8B30`（TacticalClass 方法，`this`=esi）**，字节现场：

```
006D8B3F  mov ecx, [esi+0xD64]        ; 当前滚动位置 X
006D8B45  mov edi, [esi+0xD68]        ; 当前滚动位置 Y
006D8B4B  mov [esi+0xB0], ecx         ; ★ [T+0xB0] ← curX
006D8B51  mov [esi+0xB4], edi         ; ★ [T+0xB4] ← curY
006D8B57  mov eax, [0xB0CE30]         ; 屏幕宽
006D8B5D  sar eax,1（含 cdq/sub 符号修正）
006D8B61  sub ecx, eax                ; curX − 宽/2
006D8B63  mov [esi+0xB0], ecx         ; ★ [T+0xB0] = curX − 屏宽/2
006D8B69  mov eax, [0xB0CE34]         ; 屏幕高
006D8B7C  sar ecx,1
006D8B7E  mov eax, edi
006D8B88  sub eax, ecx                ; curY − 高/2
006D8B90  mov [esi+0xB4], eax         ; ★ [T+0xB4] = curY − 屏高/2
```

- ctor 零初始化：`0x6D1C48 mov [esi+0xB0],ebx`、`0x6D1C4E mov [esi+0xB4],ebx`（ebx=0）。
- 排除噪声：全镜像 `[reg+0xB0]` W 点 196 处、`[reg+0xB4]` 165 处（`disp_hits_field` 实测）；
  落在 Tactical 族地址域 `0x6D1C00..0x6DC500` 的仅上表 4 条对象字段写 +
  ctor 2 条。其余同域 6 条（`0x6D744B/0x6DB7D9/0x6D42E2/0x6D434B/0x6D7460/0x6DB7E9`）
  逐条核对均为 **`mov dword ptr [esp+0xB0/0xB4]`（栈槽）**，非本对象字段。

### 3.3 滚动位置链（`+0xB0/0xB4` 的上游）

| 字段 | 语义 | 写点（Tactical 族） |
|---|---|---|
| `[T+0xD64]/[+0xD68]` | **当前**滚动位置（像素） | ctor `0x6D1CAA/0x6D1CB0`；AI 内同步 `0x6D2663/0x6D266F`、`0x6D275E/0x6D276A`；`0x6D5FD0/0x6D5FDC`；`0x6D6040/0x6D604C`；跳转 `0x6D613F/0x6D614D`；vtable[5] 体 `0x6DBDC7/0x6DBDD3` |
| `[T+0xD74]/[+0xD78]` | **目标**滚动位置（像素） | 同上成对写点 + 目标推进 `0x6D861A/0x6D8622`（`0x6D85E8/0x6D85EF` 读方向表 `[ecx*8+0xB0CE38]`×倍率加到目标） |

同步模式统一为：经 `0x6D8640`（8 个调用点全在 Tactical 族）做边界校验、且
`[0xA8ED6B]`（全局抑制位，与 D-20 所引 `0x5F4B13` 同一字节）为零时采用校正值，
否则沿用旧值，随后 `call 0x6D8B30` 重算并 `mov byte [T+0xD7D],1`（置脏）。

### 3.4 ★ 当前可见世界矩形（格空间）：`[T+0xD80]/[+0xD84]` + `[T+0xD88]/[+0xD8C]`

同一写者 `0x6D8B30` 在算完 `+0xB0/+0xB4` 后继续：

```
006D8B71  mov edx, [esi+0xB0]
006D8B79  sub edx, 0x3C               ; viewX − 60
006D8B96  add eax, -0x1E              ; viewY − 30
（两值经 fstp 存栈，0x6D8BB2 call 0x5AFB80 —— 以 [T+0xDE4..0xE0C] 处的 3×4 float 矩阵
   （ctor 0x6D1DCA..0x6D1E0E 写入，含 0x408888CE/0x410888CE 等比例项）做矩阵乘反投影）
006D8BED  sar eax, 8                  ; lepton >> 8 = 格
006D8BF0  mov [esi+0xD80], eax        ; ★ 可见区左上格 X
006D8C04  mov [esi+0xD84], eax        ; ★ 可见区左上格 Y
006D8C0A  mov ecx, [0xB0CE30]         ; 屏宽
006D8C10  mov eax, 0x88888889; imul; add edx,ecx; sar edx,5   ; ÷60
006D8C2A  mov [esi+0xD88], edx        ; ★ 跨度 X = 屏宽/60 + 2
006D8C30  mov ecx, [0xB0CE34]         ; 屏高
006D8C36  imul; add; sar edx,3        ; ÷15
006D8C46  mov [esi+0xD8C], ecx        ; ★ 跨度 Y = 屏高/15 + 4
```

- **消费方 A（矩形判定的运行时形态）`0x6D8AE0`（`ret 4`，取 CellStruct\*）**：
  ```
  006D8AEC  mov edx, [ecx+0xD80]
  006D8AF2  cmp eax, edx        ; x ≥ 左上格X
  006D8AF7  mov edi, [ecx+0xD88]; add edi, edx
  006D8AFF  cmp eax, edi        ; x < 左上格X+跨度X
  006D8B04  mov eax, [ecx+0xD84]
  006D8B0A  cmp esi, eax        ; y ≥ 左上格Y
  006D8B0E  mov ecx, [ecx+0xD8C]; add ecx, eax
  006D8B16  cmp esi, ecx        ; y < 左上格Y+跨度Y
  006D8B1A  mov al, 1           ; 四条全过 → 在视口内
  ```
- **消费方 B（世界→屏幕裁剪）`TacticalClass::IsVisible 0x6D2140`**：
  `0x6D2153 mov ebp,ecx`（this）；投影后
  `0x6D2202 mov ecx,[ebp+0xB0]`、`0x6D2208 mov ebp,[ebp+0xB4]`，作差得屏内相对坐标；
  边界 = `X≥−360(0xFFFFFE98)`、`X≤[0xB0CE30]+0x168`、`Y≥−180(0xFFFFFF4C)`、
  `Y≤[0xB0CE34]+0xB4`（`0x6D2223..0x6D226F`）。其直接调用者 **139 处**
  （本次 `Engine.stream` 重扫 E8 实测 = 139，与 D-20 §1.4 独立复核一致），
  链头即 `ObjectClass::DrawIfVisible 0x5F4B63`。
- 偏移扫描另见消费点 `0x54AD9B..0x54ADEF`（经 `call [edx+0x84]` 间接取对象后读
  `+0xD80/+0xD84/+0xD88/+0xD90/+0xD8C` 装入栈结构）——**类身份未深挖，仅登记不采信**。

### 3.5 屏幕宽高与源矩形（`0xB0CE30/0xB0CE34` 的上游）

- `[0xB0CE28..0xB0CE34]` = 16 字节 Rect 全局：装载者 `0x6D5F60`
  （`0x6D5F6C..0x6D5F87` 把实参 Rect 的 `+8/+0xC` 存 `0xB0CE30/0xB0CE34`，随后走 3.3 同步链）；
  零初始化 `0x6D1A40..0x6D1A51`（`xor eax,eax` 后 4 连写）。
- 实参来源 = **Rect 全局 `0x886FA0`**：全镜像 142 处引用、仅 2 处 W（`0x40DA2C`、`0x4A8987`），
  喂给 `0x6D5F60` 的调用点 2 处：`0x4A89BD`、`0x68762C`（后者即新建 Tactical 后的装载现场）。
- 生命周期口径：`0xB0CE30/34` 只在**视频模式/局面装载**时写（2 个装载点），
  运行中不变；`[T+0xB0]/[+0xB4]` 每逻辑帧重算；`[T+0xD80/84/88/8C]` 随 `0x6D8B30` 同步刷新。

### 3.6 生命周期总表（F6 四问之 3）

| 阶段 | 事件 | 证据 VA |
|---|---|---|
| 创建 | `new 0xE18` → `ctor 0x6D1C20`（全部字段清 0，vtable `0x7F4348`）→ 存 `0x887324` → 装载 Rect `0x886FA0`→`0xB0CE28..34` → `0x6D8B30` 首算 | `0x687604/0x687617/0x687627/0x68762C`（另 4 个创建点 `0x52C694/0x599D80/0x6853B4/0x6BF84F`） |
| **每逻辑帧** | `MainLogicFrame 0x55D83F mov ecx,[0x887324]; 0x55D845 mov edx,[ecx]; 0x55D847 call [edx+0x5C]`（**vtable[23] = 0x6D2540**，TacticalClass::AI）→ AI 内帧戳守卫（`[T+0xA8]` vs `CurrentFrame 0xA8ED84`，同帧已处理则跳过：`0x6D2556..0x6D2565`）→ 滚屏应用/目标同步 → `call 0x6D8B30`（`0x6D267D/0x6D2778`）重算 `+0xB0/+0xB4/+0xD80/84/88/8C` | `0x55D83F..0x55D84A`、`0x6D2540..0x6D2789` |
| 显式跳转/装载 | `0x6D5F60`（Rect 装载+同步）、`0x6D6070`（格→像素跳转，14 个调用点）、`0x6DBD20`（vtable[5]）——均在设置点就地 `call 0x6D8B30` | `0x6D5FEA/0x6D605A/0x6D6159/0x6DBDE1` |
| 销毁 | vtable[8] deleting dtor `0x6DC470` → `0x6DC48E mov [0x887324],0`；另一槽清 dtor `0x6D1E9B` | `0x6DC470..0x6DC49D` |
| 读端 | `IsVisible 0x6D2140`（139 调用点）、`0x6D8AE0` 格包含、渲染簇 `0x6D8DB0..0x6DA1FB` 多处读实例 | `0x6D2202/0x6D2208` 等 |

---

## 4. 已排除的路径清单（F6 四问之 4 的排除面）

1. **`0x887308 / 0x88730C`**：DSurface::Primary / Hidden 指针槽（RTTI `.?AVDSurface@@` 实证、
   写者为视频模式/表面生命周期例程）——与 §563 一致，**不是视口坐标**（本轮复核维持）。
2. **`0x432A35` 线索**：所在函数 `0x432750..0x432A50` 为 Bink 电影打开函数（IAT 全判名、
   字符串 `"Bink Error: %s\n"`），调用者全在 0x5BExxx–0x5CExxx 电影系统 ——
   **不是视口来源，不在战术绘制链**。
3. **`DSurface+0x1C`**：LPDIRECTDRAWSURFACE（构造器 CreateSurface 出参 + BinkDDSurfaceType
   消费双证）——**不是坐标/矩形/尺寸**。
4. **`[reg+0xB0]/[reg+0xB4]` 全镜像 196/165 个 W 点**：逐域过滤后，非 Tactical 族的
   （0x40xxxx/0x43xxxx/0x5Bxxxx/0x74xxxx 等）均属其他类；Tactical 族地址域内的 6 条
   `+0xB0/+0xB4` 嫌疑点逐条核对为 `[esp+…]` 栈槽 —— 均排除。
5. **`0x66xxxx/0x67xxxx` 存在同偏移（+0xD64..+0xD8C）访问的另一对象家族**
   （如 `0x66680A/0x66FC0B/0x67530D` 等）：非 `0x887324` 单例，未纳入本结论（见 §6 未验）。

## 5. 对既有文档的增量

- **D-20 §2**（「视口参数仍未定位」）→ **本轮已定位**：`[0x887324]+0xB0/0xB4`（像素）与
  `+0xD80/84/88/8C`（格矩形）；「遍历推导需要复现投影」的门槛由此降低：
  外部可直接读视口原点与格矩形，不必重跑 `0x6D2140` 的投影。
- **W3 `Q1_C2_RENDER.md` §4.3** 的「`[TacticalClass+0xB0/0xB4]`」断言 → **字节级证实**，
  并补全其缺失的写者 VA（`0x6D8B30`、AI 派发 `0x55D847`、装载点 `0x6D5F60`）；
  该节所列 `[TacticalClass+0x3584]/[+0xE0]` 本轮**未复核**，维持存疑（见 §6）。
- **D-17 §4 的「下一步」**（F6 从绘制入口反向找）→ 已执行完毕，F6 可从「未定位」改为
  **LOCATED**（含 VA+类型+生命周期+访问证据）。
- **TASK F6 线索勘误**：`0x432A29..0x432A32` 为 **4 dword**（非 8 dword）。

## 6. 未验 / 诚实账

1. `0x5AFB80`（矩阵乘辅助）只核了调用形状、`[T+0xDE4]` 矩阵存在性与 `>>8` 出口；
   逐参数调用约定与完整逆投影数学**未逐指令重建**（`_w8_f6_out.txt` 未含其全函数体）。
2. `[T+0xD88]=屏宽/60+2`、`[T+0xD8C]=屏高/15+4` 的**几何含义**（为何 ÷60/÷15）未解释；
   两字段的全部渲染侧消费未穷举。
3. `0x66xxxx/0x67xxxx` 同偏移对象家族与 `0x54AD70` 间接消费者的**类身份**未深挖。
4. ctor 5 个调用点分别对应的游戏阶段（首启/读档/重开局…）未逐一标注。
5. W3 §4.3 的 `[T+0x3584]/[+0xE0]` 未复核，不采信也不否证。
6. 运行期数值分布、帧间时序、`+0xB0` 的实际取值范围——**纯静态禁令下不可验**，
   本文不做任何运行期断言。
7. 本文未运行任何 .exe/.dll、未读活进程、未改本目录外任何文件、未 commit。

## 7. 判定

**F6 = LOCATED**：
- 视口像素原点 = `[0x887324 实例 +0xB0]` / `[+0xB4]`（dword×2，屏幕像素，X/Y）；
- 可见世界矩形（格空间） = `[+0xD80]/[+0xD84]`（左上格 X/Y）+ `[+0xD88]/[+0xD8C]`（跨度 X/Y）；
- 上游滚动链 = `[+0xD64]/[+0xD68]`（当前）与 `[+0xD74]/[+0xD78]`（目标）；
- 计算者 = `0x6D8B30`；每帧驱动 = `MainLogicFrame 0x55D847 → vtable[23] → 0x6D2540`；
  消费者 = `0x6D2140`（IsVisible，139 调用点）与 `0x6D8AE0`（格包含判定）。
