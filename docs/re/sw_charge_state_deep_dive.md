# SW 充能状态机深潜 · R-SW-CHARGE（全静态收口）

> **对象**：`gamemd.exe` YR 1.001（`ImageBase=0x400000`，偏移 = VA − 0x400000）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **基文件**：`ra2bench/gamemd.exe`（4,825,360 字节）
> **本任务范围**：充能状态机 ABI / 侧栏 Cameo 推进 / 联机确定性 / 可落地项
> **证据脚本**：`out/re_work/re_sprint/R_sw_charge/verify_sw_charge{,2,3}.py`（可重复运行，输出 `*_out.txt`）
> **上位底稿**：`docs/re/superweapon_re.md`（M-3 收口 · 10.0 冲刺）、`docs/re/ARCHITECTURE_ATLAS.md` §7、`YRpp/SuperClass.h`
> **基址约定**：文中 VA 均为加载地址；字节序列为该 VA 起的原始机器码。

---

## 0. 结论速览

| # | 结论 | 证据档 |
|---|---|---|
| 1 | **充能 = 纯帧计数比较**：`elapsed = CurrentFrame(0xA8ED84) − RechargeTimer.Start(+0x30)`，与 `Duration(+0x38)` 比较。**无倒计时器、无墙钟、无 RNG。** | [实证] |
| 2 | `HasChargeProgressed 0x6CBCA0` 是**唯一每帧逻辑推进器**，由 `HouseClass::Update 0x4F8440` 遍历 `House+0x258` 多槽位驱动；返回值 = 「Cameo 帧是否变化 / 是否到点」的 **UI 脏标记**，同时翻转 `IsCharged/ChargeDrainState`。 | [实证] |
| 3 | **UI 与逻辑解耦点**：`GetCameoChargeState 0x6CBEE0` 是**纯读**函数（不写任何状态）；侧栏绘点 `0x6A99AC` 每视觉帧重算，逻辑侧只靠 `+0x78` 缓存做脏检测。 | [实证] |
| 4 | Cameo 帧公式：`frame = trunc( (remaining/total) × 54.0 )`，**clamp 到 0..0x35**；`IsCharged && !UseChargeDrain` 直接返回 **0x36**。语义是**倒扣覆盖**：`0x35`=刚开始充、`0`=即将完成、`0x36`=就绪。 | [实证] |
| 5 | 多超武槽位：`HouseClass+0x258 = Supers.Items`，`+0x264 = Supers.Count`（YRpp `DynamicVectorClass` Count 在 +0xC）；每 House 独立一套 `SuperClass` 实例，互不共享计时。 | [实证] |
| 6 | **确定性**：充能链 6 个关键函数（HasCharge / GetCameo / Grant / CanFire / IronCurtainCharged / ChronoSphereCharged）静态扫描 **零 RNG、零 timeGetTime**。联机安全；改推进规则会改 `IsCharged` 翻转帧 → 禁止。 | [实证] |
| 7 | **可落地**：见 §6。1 处冗余 `GetCameoChargeState` 二次调用可删（逻辑路径、语义不变）；1 处侧栏 Cameo 读缓存限频点（纯 UI）。**其余为纯逆向收口。** | [实证] |

---

## 1. 充能状态机完整 ABI

### 1.1 `SuperClass` 实例布局（Size=0x80，vtable `0x7F3FE8`）

与 YRpp `SuperClass.h` 交叉一致；下表只列充能相关槽位，读/写点均带字节。

| 偏移 | 字段 | 类型 | 初值 (ctor `0x6CAF90`) | 关键读/写字节 |
|---|---|---|---|---|
| **+0x24** | `CustomChargeTime` | int | `-1`（= 用 Type 默认） | `GetRechargeTime 0x6CC260: 8B 41 24 / 83 F8 FF / 75 09 / 8B 41 28 / 8B 80 B0 00 00 00` |
| **+0x28** | `Type` | `SuperWeaponTypeClass*` | arg1 | `0x6CB658: 8B 90 B0 00 00 00`（读 `RechargeTime+0xB0`） |
| **+0x2C** | `Owner` | `HouseClass*` | arg2 | — |
| **+0x30** | **`RechargeTimer.Start`** | int（帧） | `CurrentFrame`（`0x6CAFB5: 89 4E 30`） | 判空 `0x6CB5A4: 83 7E 30 FF`；比较 `0x6CBD5D: 8B 0D 84 ED A8 00` |
| **+0x34** | `RechargeTimer.StartTime` | int | 未显式清零（Grant 写 arg） | `0x6CB66F: 89 4F 04` |
| **+0x38** | **`RechargeTimer.Duration`** | int（帧） | `0`（`0x6CAFB8: 89 5E 38`） | `0x6CB672: 89 57 08`；比较 `0x6CBD65: 3B C8` |
| +0x3C | `FlashSidebarTabFrames` | int | 自 `Type+0x60` | `0x6CB583: 8B 51 60` |
| +0x40 | `BlinkState` | bool | 0 | `0x6CB580: 88 5E 40` |
| +0x48/+0x4C | `BlinkTimer` | LARGE_INTEGER | 0 | — |
| +0x50 | `SpecialSoundDuration` | int | `-1` | 每帧自减 `0x6CBCAF: 48 / 89 46 50` |
| **+0x60** | `CanHold` | bool | 1（`0x6CAFC7: C6 46 60 01`） | `0x6CB597: 38 5E 60` |
| +0x68 | `Animation` | `AnimClass*` | 0 | — |
| **+0x6D** | `Granted` | bool | 0 | `0x6CB579: C6 46 6D 01`；早退 `0x6CBD03: 0F 84 94 01 00 00` |
| +0x6E | `OneTime` | bool | 0 | `0x6CB57D: 88 46 6E` |
| **+0x6F** | `IsCharged` | bool | 0（`0x6CAFEA: 88 5E 6F`） | 写 `0x6CB824: 88 41 6F`（SetReadiness）；读 `0x6CBD09: 8A 46 6F` |
| **+0x70** | `IsOnHold` | bool | 0 | `0x6CBD21: 8A 46 70` |
| **+0x74** | `ReadinessFrame` | int | `-100`（`0x6CAFF0: C7 46 74 FF FF FF FF`… 实际 `0xFFFFFF9C`） | 到点写 `0x6CBE6F: 89 4E 74` = `CurrentFrame` |
| **+0x78** | `CameoChargeState` | int | `-1`（`0x6CAFD1: 89 46 78`） | 脏检测 `0x6CBE83: 3B 46 78` / 回写 `0x6CBE8F: 89 46 78` |
| **+0x7C** | `ChargeDrainState` | int (−1/0/1/2) | `-1`（`0x6CAFD4: 89 46 7C`） | `0x6CBD80: 83 7E 7C 02`；`CanFire 0x6CC374: 8B 41 7C` |

> **计时三槽语义**（`TimerStruct`）：`Start` = 起充帧（`-1` = 未在跑 / 已折算到 Duration）；`Duration` = 总帧数（跑动中同时兼作「剩余」——见下）；`StartTime` = Grant 时的入参，充能判定不读它。
>
> **关键**：引擎没有独立的「剩余帧」字段。运行中剩余 = `Duration − (CurrentFrame − Start)`；暂停/挂起时把剩余写回 `Duration` 并置 `Start = -1`。这是全链一致的折叠表示。

### 1.2 计时折叠算法（全链共用的同一段比较）

四处共用同一形态（`HasChargeProgressed` / `GetCameoChargeState` / `SetOnHold` / `IronCurtainCharged`）：

```
if Start == -1:
    remaining = Duration            ; 已折叠：Duration 即剩余
else:
    elapsed  = CurrentFrame - Start ; 0x6CBD5D: mov ecx,[0xA8ED84]; sub ecx,edi
    if elapsed >= Duration:         ; 0x6CBD65: cmp ecx,eax; jge
        remaining = 0
    else:
        remaining = Duration - elapsed
```

挂起折叠（`SetOnHold 0x6CB4D0`，`0x6CB53E`）：

```
Duration = remaining ; Start = -1
```

展开还原（`Grant 0x6CB560` 尾段 / `HasCharge` drain 收束 `0x6CBDA1`）：

```
Start = CurrentFrame ; StartTime = arg ; Duration = RechargeTime
```

`RechargeTime` 解析（`GetRechargeTime 0x6CC260`）：

```
eax = CustomChargeTime(+0x24)
if eax != -1: return eax
return Type->RechargeTime(+0xB0)     ; 默认 0x1194 = 4500 帧
```

### 1.3 多超武槽位 ABI

| 槽位 | 地址 | 字节实证 |
|---|---|---|
| `HouseClass::Supers.Items` | `House+0x258` | `0x4F8E34: 8B 86 58 02 00 00`；`0x41F0E7: 8B B1 58 02 00 00` |
| `HouseClass::Supers.Count` | `House+0x264` | `0x4F8E7B: 8B 86 64 02 00 00`；`0x41F0DB: 8B 91 64 02 00 00` |

YRpp `DynamicVectorClass`（`ArrayClasses.h:183-339`）：`VectorClass` = `Items+0 / Capacity+4 / IsInitialized+8 / IsAllocated+9`，派生 `Count+0xC / CapacityIncrement+0x10`。故 `Supers` 对象起于 `House+0x258`，`Count` 正好落 `+0x264` —— 与汇编双点吻合。[实证]

全局 `SuperClass::Array` = `0xA83CB8`（ctor 末尾登记，9 处 imm32 引用）；与 per-House `Supers` 是两套索引（前者全局实例表，后者 per-House 持有列表）。

**每 House 一套独立 `SuperClass` 实例**：计时字段在实例内，槽位间无共享状态。同一 `SuperWeaponType` 若被多次 Grant（多建筑），是多个实例各自计时。

---

## 2. `HasChargeProgressed 0x6CBCA0` 每帧语义

### 2.1 调用方

| 调用点 | 所属函数 | 状态 |
|---|---|---|
| `0x4F8E4A` | **`HouseClass::Update 0x4F8440`**（vtable `0x7EA8FC`） | **唯一活路径**，每逻辑帧 × 每 House × 每 Supers[i] |
| `0x4F9397` | `0x4F9370` 独立近似拷贝 | **死代码**：`.text` 无 call、全镜像 **0 处 imm32** → 不可达 |

循环骨架（`0x4F8E34-0x4F8E84`）：

```
for (ebx = 0; ebx < House+0x264; ++ebx) {
    SuperClass* p = *(House+0x258)[ebx];
    bool isPlayer = (House == HouseClass::Player 0xA83D4C);   // 0x4F8E42: 3B F0 / 0F 94 C1
    if (p->HasChargeProgressed(isPlayer) && isPlayer) {
        // EVA/音效：Type->vtable[0x40]() 取 ID，0x6ABC60 / 0x6A60A0 触发
    }
}
```

`isPlayer` 走 `stdcall` 尾 `ret 4`（`0x6CBCA0` 末 `C2 04 00`），入参在 `[esp+0x1C]`（`0x6CBDC8: 8A 4C 24 1C`）。

### 2.2 控制流全图（逐字节）

```
HasChargeProgressed(bool isPlayer)          ; 0x6CBCA0
│
├─ SpecialSoundDuration(+0x50) > 0 ?  → dec        ; 0x6CBCAF
│   └─ == 0 时清 -1 并放音 (Type+0xC0, call 0x7509E0)
│
├─ Granted(+0x6D)==0            → return false     ; 0x6CBD03
├─ IsCharged(+0x6F)==1
│   └─ && UseChargeDrain(Type+0xE5)==0 → return false  ; 0x6CBD19
├─ IsOnHold(+0x70)==1           → return false     ; 0x6CBD26
│
├─ Start(+0x30) == -1 ?                            ; 0x6CBD32
│   ├─ CameoChargeState(+0x78)==-1 → return false  ; 0x6CBD3B
│   └─ else: +0x78 = -1; return true               ; 0x6CBD41  (UI 脏)
│
├─ remaining = fold(Start, Duration)               ; 0x6CBD53-0x6CBD6D
│   └─ remaining != 0 →                            ; 0x6CBE7C
│        e1 = GetCameoChargeState()                ; 0x6CBE7E
│        e1 == +0x78 ? return false
│        e2 = GetCameoChargeState()  ← 冗余二次调用 ; 0x6CBE88  ★可落地
│        +0x78 = e2; return true                   ; 0x6CBE8F
│
└─ remaining == 0  (到点)                          ; 0x6CBD73
    ├─ UseChargeDrain ?
    │   ├─ ChargeDrainState(+0x7C)==2 (Draining)   ; 0x6CBD80
    │   │   → +0x7C = 0 (Charging)                 ; 0x6CBD86
    │   │   → 重启 Timer: Start=CurrentFrame, Duration=RechargeTime  ; 0x6CBDA1
    │   │   → return true
    │   └─ else
    │       → +0x7C = 1 (Ready); IsCharged = 1     ; 0x6CBDB7 / 0x6CBDBA
    │       → return true
    └─ !UseChargeDrain
        → IsCharged = 1                            ; 0x6CBDCC
        → if isPlayer: 12 路 EVA 跳表 (Type+0xB4)  ; 0x6CBDE6: FF 24 85 A8 BE 6C 00
        → ReadinessFrame(+0x74) = CurrentFrame     ; 0x6CBE6F
        → return true
```

**返回值语义**：`true` = 「充能视图发生了变化」——要么 Cameo 帧变了，要么到点/状态翻转。这是 **UI 脏标记 + EVA 触发器**，不是「是否充完」。充完判定是 `IsCharged` / `ChargeDrainState` 本身。

**副作用清单**（决定它不能被跳帧）：
1. `SpecialSoundDuration--`（**有状态、非幂等**）
2. `IsCharged` 翻转
3. `ChargeDrainState` 转移
4. `RechargeTimer` 重装（drain 收束时）
5. `CameoChargeState` 缓存回写
6. `ReadinessFrame` 写入
7. `isPlayer` 时 EVA/音效

### 2.3 `ChargeDrainState` 转移图（4 态）

YRpp `GeneralDefinitions.h:912`：`None=-1 / Charging=0 / Ready=1 / Draining=2`。

```
            Grant(UseChargeDrain)
   None(-1) ─────────────────────► Charging(0)
                                      │
                    充能到点           │ 充能到点
                  (remaining==0)       ▼
                              Ready(1) ◄──┬── 玩家再点 / SetReadiness
                                      │   │
                              点击发射    │  (drain 中途)
                                      ▼   │
                              Draining(2)─┘  remaining==0 时收束回
                                      │      Charging(0) 并重装 Timer
                                      ▼
                              (发射/OneTime 回收)
```

字节锚点：
- `→ Ready`：`0x6CBDB7: 89 5E 7C`（`ebx=1`）+ `0x6CBDBA: 88 5E 6F`
- `Draining → Charging`：`0x6CBD86: C7 46 7C 00 00 00 00` + Timer 三槽重装 `0x6CBDA1/07/0A`
- `CanFire` 判定：`UseChargeDrain ? (ChargeDrainState != 0) : IsCharged`（`0x6CC360: 8A 41 70 / 8A 90 E5 00 00 00 / 8B 41 7C / 0F 95 C0` / `8A 41 6F`）

---

## 3. 侧栏 Cameo 推进（`GetCameoChargeState 0x6CBEE0`）

### 3.1 帧号语义（**倒扣覆盖**，不是正向进度）

```
if !Granted                    → 0
if UseChargeDrain:
    if ChargeDrainState == 2:  → f = 1.0 - (total*scale - remaining)/(total*scale)
                                 = remaining/(total*scale)        ; 泄放中 = 余量视角
    else:                      → f = remaining / total            ; 蓄能中 = 余量视角
else:  // 常规充能
    if IsCharged               → return 0x36                      ; 54 = 就绪专用帧
    else:                      → f = remaining / total
frame = trunc(f × 54.0)        ; 0x6CC048: fmul qword [0x7F4048] ; 54.0
return (frame >= 0x35) ? 0x35 : frame                             ; 0x6CC053: 83 F8 35
```

浮点常数（`verify_sw_charge2.py` 实证）：

| 地址 | 值 | 用途 |
|---|---|---|
| `0x7E1718` | `1.0` (double) | drain 路径 `fsubr` 取补 |
| `0x7F4048` | **`54.0`** (double) | ×54 映射到 SHP 覆盖帧 |
| `0x7E2AC8` | `1.0` (float) | AI Charged 阈值（§4） |
| `0x7EAAE0` | `0.01` (float) | `SetCharge` 百分比缩放 |

`0x7C5F00` = `fistp` 型 double→int 截断辅助（保存/校验 FPU CW，`0x7C5F03: D9 3C 24` / `0x7C5F1B: DF 38`），非 `ftol`，行为确定。

**帧域**：`0 .. 0x35`（0–53）为充能覆盖动画；`0x36`（54）= 就绪；`0` 在 `!Granted` 与「即将充满」两种情况下都会出现，区分靠 `Granted/IsCharged`。

> ATLAS 旧表述「帧 0..0x35 推进」是**帧域**正确，但方向是**倒扣**：`0x35` 覆盖最满（刚起充）→ `0` 覆盖将尽（即将到点）。Cameo SHP 是遮罩擦除动画。

### 3.2 UI / 逻辑解耦点

| 层 | 入口 | 是否写状态 | 驱动节拍 |
|---|---|---|---|
| **逻辑** | `HasChargeProgressed` @ `HouseClass::Update 0x4F8E4A` | **是**（6 项副作用，§2.2） | 每逻辑帧 |
| **UI** | `GetCameoChargeState` @ 侧栏绘点 `0x6A99AC` | **否**（纯读） | 每视觉帧 |

侧栏绘点完整序列（`0x6A9966-0x6A99B1`，`verify_sw_charge2.py`）：

```
p = HouseClass::Player(0xA83D4C)->Supers.Items[i]     ; 0x6A9970/76
b1 = p->ShouldDrawProgress()      ; 0x6A9979 → 0x6CDE90
p->NameReadiness()                ; 0x6A9994 → 0x6CC2B0
frame = p->GetCameoChargeState()  ; 0x6A99AC → 0x6CBEE0   ★UI 重算点
```

**解耦结论**：
- `GetCameoChargeState` **不写** `+0x78`，也不改 Timer。UI 可任意调用/跳过，不影响逻辑。
- `+0x78` 只是逻辑侧的「上次报告给 UI 的帧号」，专供 `HasChargeProgressed` 判断 `return true/false`。
- 逻辑不依赖 UI 是否绘制；UI 不推进逻辑。**跳掉 UI 重绘 = 联机安全**。
- 反过来**不可**跳掉 `HasChargeProgressed` —— 它携带 `IsCharged/ChargeDrainState/Timer` 副作用。

`ShouldDrawProgress 0x6CDE90`：`UseChargeDrain ? 1 : !IsCharged`（有覆盖才画）。
`ShouldFlashTab 0x6CE1A0`：就绪且 `ReadinessFrame + Type->FlashSidebarTabFrames(+0xE8) > CurrentFrame` 时闪烁；`+0xE8==-1` 恒闪。

---

## 4. AITrigger 蓄能判决（`0x41F0D0` / `0x41F180`）

两者结构完全同构，仅 `Type+0xB4` 判别不同：

| 函数 | 判别 | 含义 |
|---|---|---|
| `IronCurtainCharged 0x41F0D0` | `cmp dword [Type+0xB4], 1` | `SuperWeaponType::IronCurtain` |
| `ChronoSphereCharged 0x41F180` | `cmp dword [Type+0xB4], 3` | `SuperWeaponType::ChronoSphere` |

共同逻辑：

```
for each SuperClass* p in House->Supers:          ; +0x258 / +0x264
    if p->Type->Type == <IronCurtain|ChronoSphere>:
        if !p->Granted: continue
        remaining = fold(p->RechargeTimer)        ; 同 §1.2
        progress  = remaining / p->GetRechargeTime()
        if progress >= (1.0 - Rules->AIChargeThreshold)   ; [0x7E2AC8]=1.0 − [Rules+0xD70]
            return true
return false
```

字节：`0x41F126: 8B 15 84 ED A8 00`（CurrentFrame）/ `0x41F13A: E8 21 D1 2A 00`（`GetRechargeTime`）/ `0x41F152: D9 05 C8 2A 7E 00`（阈值 1.0）/ `0x41F158: D8 A0 70 0D 00 00`（`Rules+0xD70`）。

**与 ATLAS 的差异**：`SuperWeaponTypeClass+0xF8` Range 假说破产得到再次确认——这两个函数只读 `Type+0xB0`(RechargeTime)、`Type+0xB4`(Type enum)、`+0xE5`(UseChargeDrain)、`Rules+0xD70`，**从不读 `+0xF8`**。[实证]

---

## 5. 确定性与联机安全性

### 5.1 RNG / 墙钟探针（`verify_sw_charge.py` §9）

| 函数 | call→`0x65C780/0x65C7E0` | call→`timeGetTime` 族 |
|---|---|---|
| `HasChargeProgressed 0x6CBCA0` | 无 | 无 |
| `GetCameoChargeState 0x6CBEE0` | 无 | 无 |
| `Grant 0x6CB560` | 无 | 无 |
| `CanFire 0x6CC360` | 无 | 无 |
| `IronCurtainCharged 0x41F0D0` | 无 | 无 |
| `ChronoSphereCharged 0x41F180` | 无 | 无 |

**充能推进 = 纯 `CurrentFrame` 整数差 + 一次 x87 浮点映射（仅显示公式）**。逻辑判定全部是整数比较。`CurrentFrame 0xA8ED84` 全镜像唯一 `inc` 在 `0x55DE81`（`MainLogicFrame`），每逻辑帧 +1 —— 与墙钟无关（`clock_frame_loop.md`）。

浮点映射（`fild/fmul/fdiv/fistp`）只影响 `GetCameoChargeState` 的**返回显示值**；该值写入 `+0x78` 后**进 `CalculateChecksum v[13]=0x6CE020`**（`superweapon_re.md` §6.2）。因输入（整数 Timer + Rules 常数）确定、FPU CW 由 `0x7C5F00` 规范，结果确定。

### 5.2 进 CRC / Checksum 情况（承接 `superweapon_re.md` §6）

| 改动对象 | 帧 CRC `0x64DAB0` | Checksum v[13] `0x6CE020` | 判定 |
|---|---|---|---|
| 侧栏 Cameo 绘制 / 跳帧 / 限频 | 否 | 否 | **安全** |
| `ShouldDrawProgress` / `ShouldFlashTab` / EVA | 否 | 否 | **安全** |
| `GetCameoChargeState` 读缓存化（仅 UI 调用点） | 否 | 否 | **安全** |
| `GetCameoChargeState` 本体公式 | 否 | **是**（经 `+0x78`） | **禁止** |
| `RechargeTimer` 推进规则 / `IsCharged` 翻转帧 | 间接是 | **是** | **禁止** |
| `SetRechargeTime 0x6CC280` / `ResetRechargeTime 0x6CC290` | 间接是 | 是 | **禁止**（仅 TAction 触发器、须全端同帧） |

### 5.3 结论

- **不吃 RNG**、**不吃墙钟** → 充能是纯确定性帧函数。
- 联机 lockstep 下各端 `CurrentFrame` 同步，充能进度必然一致。
- 唯一要守的红线：**不改推进规则、不单端调用 `Set/ResetRechargeTime`、不改 `GetCameoChargeState` 公式**。
- `Launch` 子函数吃 RNG 属于**发射路径**（已由 `superweapon_re.md` 10.2 闭环），不在本任务充能链内；且 RNG 消耗本身在 lockstep 下也是同步的。

---

## 6. 可落地项（字节规格）

> 总判：充能状态机**本身无 bug、无需修复** —— 语义完整、确定性成立。以下是 **2 处零语义风险的微优化/限频点**，非修复。其余为**纯逆向收口**。

### 6.1 ★ 删除冗余二次 `GetCameoChargeState` 调用（逻辑路径 · 语义不变）

**位置**：`HasChargeProgressed` 内，`0x6CBE7C` 慢路径。

```
0x006CBE7C  8B CE          mov  ecx, esi
0x006CBE7E  E8 5D 00 00 00 call 0x6CBEE0      ; e1 = GetCameoChargeState()
0x006CBE83  3B 46 78       cmp  eax, [esi+0x78]
0x006CBE86  74 15          je   0x6CBE9D      ; 无变化 → false
0x006CBE88  8B CE          mov  ecx, esi
0x006CBE8A  E8 51 00 00 00 call 0x6CBEE0      ; e2 = 同一纯函数  ← 冗余
0x006CBE8F  89 46 78       mov  [esi+0x78], eax
0x006CBE92  ... ret 1
```

`GetCameoChargeState` 是纯读（§3.2），`cmp/je` 不改 `eax`，第二次 call 结果必然等于第一次。

**补丁**（`0x6CBE88` 起 7 字节 → NOP，`eax` 复用）：

```
VA 0x006CBE88  原: 8B CE E8 51 00 00 00
             改: 90 90 90 90 90 90 90
```

| 项 | 值 |
|---|---|
| 文件偏移 | `0x2CBE88` |
| 原字节 | `8B CE E8 51 00 00 00` |
| 新字节 | `90 90 90 90 90 90 90` |
| 语义影响 | 无（纯函数结果复用） |
| CRC 影响 | 无（不改任何写入值） |
| 风险 | 零 |

### 6.2 ★ 侧栏 Cameo 重绘限频：读缓存 `+0x78`（纯 UI）

**位置**：侧栏绘点 `0x6A99AC`。

```
0x006A99A3  8B 91 58 02 00 00   mov  edx, [ecx+0x258]   ; Supers.Items
0x006A99A9  8B 0C BA             mov  ecx, [edx+edi*4]   ; p = Items[i]
0x006A99AC  E8 2F 25 02 00       call 0x6CBEE0           ; frame = GetCameoChargeState()
0x006A99B1  89 44 24 38          mov  [esp+0x38], eax
```

`GetCameoChargeState` 每视觉帧做 2 次 `fild/fmul/fdiv` + `fistp`。逻辑侧已在 `+0x78` 缓存「当前应显示的帧号」，且仅在变化时更新 —— 正是限频后的值。

**补丁 A（5 字节内，需接受 `+0x78==-1` 的 1 逻辑帧窗口）**：

```
VA 0x006A99AC  原: E8 2F 25 02 00
             改: 8B 41 78 90 90          ; mov eax,[ecx+0x78]; nop; nop
```

**补丁 B（稳妥，6 字节，需向后借 1 字节或插入短跳）** —— 若不可借字节则放弃，维持原状：

```
; 期望序列（示意，需在更大空隙重排）：
mov  eax, [ecx+0x78]        ; 8B 41 78
cmp  eax, -1                ; 83 F8 FF
jne  short use_cached
call 0x6CBEE0               ; E8 .. (仅在 cache 未就绪时回退)
use_cached:
```

| 项 | 值 |
|---|---|
| 文件偏移 | `0x2A99AC` |
| 影响面 | **仅显示**；`GetCameoChargeState` 本体不动，`+0x78` 写侧不动 |
| CRC 影响 | 无（UI 调用点从不进 CRC） |
| 收益 | 省每视觉帧每 SW 一次 x87 闭包；侧栏 SW 槽位多时可观 |
| 风险 | 补丁 A：Grant 后首个逻辑帧前显示 `0xFFFFFFFF` 帧号 → 绘制器需能容忍（建议先确认 `0x4AED70` 对 frame=−1 的行为，或直接用补丁 B） |

> **建议**：若只做一个，优先 6.1（零风险）。6.2 属可选限频，做前须在真机确认 cameo 绘制器对 `frame=-1` 的容错；否则**保持原样**，本任务即为纯逆向收口。

### 6.3 明确「纯逆向收口」的范围

以下均为**逆向成果、无补丁需求**：

- 充能折叠表示（`Start==-1` ⇒ `Duration` 即剩余）——设计自洽，无溢出/无回绕风险（帧号为 32 位有符号，单局远够）。
- 多槽位 per-House 独立计时——无共享可破坏。
- `ChargeDrainState` 4 态 FSM——转移闭合，`CanFire` 判定与之自洽。
- `isPlayer` 门控 EVA——AI 端不放音，无联机副作用。
- 死代码 `0x4F9370`（0 call / 0 imm32）——`SpecialSoundDuration` 不存在双倍递减风险。
- `Type+0xF8 Range` 假说破产——充能/AI 判决链均不读该偏移。

---

## 7. 关键地址速查

| VA | 符号 | 角色 |
|---|---|---|
| `0x6CAF90` | `SuperClass::ctor` | 字段初始化 + 4 重 vtable |
| `0x6CB4D0` | `SetOnHold` | 挂起/恢复，Timer 折叠/展开 |
| `0x6CB560` | `Grant` | 授予/起充，写 `RechargeTimer` |
| `0x6CB820` | `SetReadiness` | 3 字节写 `IsCharged+0x6F` |
| **`0x6CBCA0`** | **`HasChargeProgressed`** | **每帧充能推进 + UI 脏标记** |
| **`0x6CBEE0`** | **`GetCameoChargeState`** | **Cameo 帧 0..0x35 / 0x36，纯读** |
| `0x6CC1E0` | `SetCharge` | 百分比→Timer（`×0.01`） |
| `0x6CC260` | `GetRechargeTime` | `CustomChargeTime` 或 `Type+0xB0` |
| `0x6CC280/0x6CC290` | `Set/ResetRechargeTime` | 写 `CustomChargeTime+0x24` |
| `0x6CC360` | `CanFire` | `IsOnHold` / `IsCharged` / `ChargeDrainState` |
| `0x6CDE90` | `ShouldDrawProgress` | UI |
| `0x6CE1A0` | `ShouldFlashTab` | UI |
| `0x4F8440` | `HouseClass::Update` | 充能主驱动（vtable `0x7EA8FC`） |
| `0x4F8E4A` | — | 唯一活调用点 |
| `0x41F0D0` | `IronCurtainCharged` | AITrigger，`Type+0xB4==1` |
| `0x41F180` | `ChronoSphereCharged` | AITrigger，`Type+0xB4==3` |
| `0xA8ED84` | `Unsorted::CurrentFrame` | 唯一时间基（10 处写，1 处 inc） |
| `0xA83D4C` | `HouseClass::Player` | `isPlayer` 判别 |
| `0xA83CB8` | `SuperClass::Array` | 全局实例表 |
| `0x7F4048` | — | `54.0` 帧映射常数 |
| `0x7C5F00` | — | `fistp` 双精度→int 截断 |

---

## 8. 复现步骤

```powershell
python out/re_work/re_sprint/R_sw_charge/verify_sw_charge.py
python out/re_work/re_sprint/R_sw_charge/verify_sw_charge2.py
python out/re_work/re_sprint/R_sw_charge/verify_sw_charge3.py
```

依赖：`capstone`（已用 5.0.7）。脚本只读 `ra2bench/gamemd.exe`，输出到 stdout（同时落盘 `*_out.txt`）。

---

## 9. 证据档声明

| 断言 | 档 |
|---|---|
| 充能三槽布局 + 比较指令 | [实证] `verify_sw_charge.py` §7-10 原始字节 |
| `HasChargeProgressed` 全文控制流 | [实证] 同上 §1 全量反汇编 |
| `GetCameoChargeState` 公式 + 常数 54.0/1.0 | [实证] `verify_sw_charge2.py` §1-2 |
| UI/逻辑解耦（`0x6A9940` 绘点三连调） | [实证] `verify_sw_charge2.py` §3 |
| 多槽位 `+0x258/+0x264` + YRpp Count@+0xC | [实证] `verify_sw_charge.py` §7 + `ArrayClasses.h` |
| 零 RNG / 零墙钟 | [实证] `verify_sw_charge.py` §9 闭包扫描 |
| 死代码 `0x4F9370`（0 call / 0 imm32） | [实证] `verify_sw_charge.py` §8 + 全镜像 imm32 扫描 |
| `Type+0xF8` 不被充能链读取 | [实证] 本轮反汇编无 `+0xF8` 访问 |
| AI 阈值 `Rules+0xD70` / 判别 `Type+0xB4==1/3` | [实证] `verify_sw_charge.py` §3 |
| `ChargeDrainState` 转移字节锚点 | [实证] `verify_sw_charge.py` §1 |
| 历史：Timer 进 Save 流 / Launch 吃 RNG / Grant 触发路径 | [文档] `superweapon_re.md` 10.1-10.3（本任务未重做） |
