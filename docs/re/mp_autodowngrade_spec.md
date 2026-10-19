# 联机自动降级门控规格（MP_AUTODOWNGRADE_SPEC）

> 任务：**M-6** · 派工 v10 · 2026-09-26
> 问题：S2（`ScenarioClass` 标志写）/ S3（`House+0x577A`）**无 ini 门控**，与原版客户端混联时只能整局不加载 `ra2render.dll`。
> 目标：产品级**自动降级**方案——运行时检测「当前是否联机/锁步」，联机自动旁路全部 VIOLATION/RISK 项，单机保留增强；**规格-only**，供 ZCode 落地。
> 写作用域：本文件 + `out/re_work/mp_autodowngrade/**`；**不改** `ra2render/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`gamemd.exe`。
> 证据源（只读）：`ra2youli/gamemd.exe`（ImageBase=`0x400000`，file off = VA−`0x400000`）capstone 反汇编、`docs/re/net_sync_checksum.md`、`docs/re/MP_SAFETY_REVIEW.md`、`docs/re/INSTALLED_HOOKS_AUDIT.md`、`docs/re/clock_frame_loop.md`、`ra2render/blitter_hooks.cpp`（1797 行，只读行号引用）。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 证据标签：**[实证]** = 本任务用 capstone 对 `gamemd.exe` 逐字节反汇编复算；**[待实测]** = 仅有文档/推断，运行时行为未在真机双端确认。
>
> 判定图例（沿用 MP_SAFETY_REVIEW）：
> - **SAFE** = 纯表现层，不进同步契约，联机锁步下可共存
> - **RISK** = 可能影响同步，需条件验证；混联/混 DLL 必坏
> - **VIOLATION** = 现网实现下必导致或高概率 desync

---

## 0. 结论摘要

| 项 | 结论 |
|---|---|
| **推荐主判定** | `*(uint8_t*)0x00A8D5F8 & 0x02`（联机会话位 bit1）**置位 ⇒ 联机/锁步**。`0x647260 NetFrameSync` 入口即以此为门 [实证] |
| **辅助确认** | ① `[0xAA0444]==2`（网络模态/收包会话阶段）② `[0xA8B238]∈{3,4}`（局内）③ `[0xA802C8]>0`（本地事件环非空）④ `[0x8B41F8]>0`（网络命令环非空）。四选二命中即升联机置信 |
| **降级动作** | 联机 ⇒ 强制 `TargetScanInterval=1`、禁 Threat Retention 短路、跳过 S1 TYPE 补丁、跳过 S2/S3 状态写。**不改逻辑状态、不碰 `Compute_Frame_CRC 0x64DAB0`** |
| **保守默认** | 检测失败/不确定 ⇒ **按联机降级**（宁可单机少功能，不可联机 desync） |
| **单机强制** | `[Logic] ForceSinglePlayer=1` 可覆盖检测，保留全部增强（供调试/单机验收） |
| **回滚** | `[Logic] MpAutoDowngrade=0` 一键关闭整个门控，回到现网行为 |
| **混联可行性** | 本规格落地后，**可与原版客户端混联**（本端自动降级到与原版一致的逻辑面）；SAFE 表现层差异不产生 desync |

**一句话**：`0xA8D5F8` bit1 是引擎自己的「联机会话」开关（`NetFrameSync` 入口即测它）；用它做主判定 + 会话阶段/事件环做辅助确认，把 M-4 的 VIOLATION/RISK 七项全部挂到「联机自动旁路」，混联就不必再「整局不加载 DLL」。

---

## 1. 联机检测点（地址级依据）

### 1.0 检测架构

```
                    ┌─────────────────────────────────────┐
   每逻辑帧 / 配置装入时 │  MpSessionDetector::Poll()          │
                    │  主判定 + 辅助确认 → 置信度           │
                    └──────────────┬──────────────────────┘
                                   │ g_mpSessionState
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
            SINGLE            AMBIGUOUS           MULTIPLAYER
          (单机增强)         (保守→按联机)         (自动旁路)
                 │                 │                 │
                 └────────────┬────┴─────────────────┘
                              ▼
                    各门控点读 g_mpSessionState
                    （不写引擎状态，不进 CRC）
```

**硬约束**：检测逻辑本身必须是**纯读引擎全局**，禁止写 `0xA8D5F8` / `0xA8B238` / `0xAA0444` / 事件环；禁止引入墙钟、指针哈希进任何会被同步的路径。

---

### 1.1 主判定：`0x00A8D5F8` 会话标志（bit1 = 0x02）

| 字段 | 内容 |
|---|---|
| **地址** | `0x00A8D5F8`（BSS 全局，dword，实际作 byte 位域用） |
| **位语义** | bit0=0x01、**bit1=0x02（联机会话/锁步）**、bit2=0x04、bit3=0x08。`0x647260` 测 bit1；`0x64729F/0x6472B6` 测 bit2（`bl=4`）；`0x48CF0E` 测 `bit0|bit1`（mask=3） |
| **为何是主判定** | `NetFrameSync 0x647260`（联机同步驱动，唯一被 `MainLogicFrame 0x55DE40` 调用）**入口第一件事**就是 `test al, 2`，bit1=0 则整段同步（收包/CRC/命令）全部跳过——引擎自己用它区分单机/联机 |
| **样本规模** | imm32 `F8 D5 A8 00` 全文 **52** 处 [实证] |

#### 1.1.1 `NetFrameSync` 入口 [实证]

```
00647260  A0 F8 D5 A8 00        mov  al, byte ptr [0xA8D5F8]
00647265  83 EC 74              sub  esp, 0x74
00647268  A8 02                 test al, 2              ; ★主判定★ bit1
0064726A  53                    push ebx
0064726B  55                    push ebp
0064726C  56                    push esi
0064726D  57                    push edi
0064726E  0F 84 53 02 00 00     je   0x6474C7           ; bit1=0 → 早退（单机路径）
```

原始字节（file off `0x247260`）：
`a0 f8 d5 a8 00 83 ec 74 a8 02 53 55 56 57 0f 84 53 02 00 00 8b 0d 70 f7`

#### 1.1.2 同函数内 bit2 复测 [实证]

```
00647287  BB 04 00 00 00        mov  ebx, 4
...
0064729F  84 1D F8 D5 A8 00     test byte ptr [0xA8D5F8], bl   ; bl=4 → bit2
006472A5  74 55                 je   0x6472FC
...
006472B6  84 1D F8 D5 A8 00     test byte ptr [0xA8D5F8], bl
006472BC  74 3E                 je   0x6472FC
```

原始字节：`84 1d f8 d5 a8 00`（全文出现 **2** 次）[实证]

#### 1.1.3 引擎其它读点（交叉印证 bit1 语义）

| 地址 | 原始字节 | 反汇编 | 语义 | 标签 |
|---|---|---|---|---|
| `0x0052DB33` | `f6 05 f8 d5 a8 00 02` | `test byte ptr [0xA8D5F8], 2` | GameMainLoop 联机分支 | [实证] |
| `0x0052DC34` | `a1 f8 d5 a8 00 24 fd a3 f8 d5 a8 00` | `mov eax,[0xA8D5F8]; and al,0xFD; mov [0xA8D5F8],eax` | **写点**：清 bit1（会话结束） | [实证] |
| `0x0048CE0D` | `f6 05 f8 d5 a8 00 02 74 17` | `test byte ptr [0xA8D5F8], 2; je …` | GameRunner 联机分支 | [实证] |
| `0x0048CF0E` | `f6 05 f8 d5 a8 00 03 74 0a` | `test byte ptr [0xA8D5F8], 3` | GameRunner 测 bit0\|bit1 | [实证] |
| `0x0055D463` | `f6 05 f8 d5 a8 00 02 74 25` | `test byte ptr [0xA8D5F8], 2` | MainLogicFrame 联机分支 | [实证] |
| `0x0055D878` | `8b 0d f8 d5 a8 00 f6 c1 02` | `mov ecx,[0xA8D5F8]; test cl, 2` | MainLogicFrame | [实证] |
| `0x004C7929` | `f6 05 f8 d5 a8 00 02 0f 85 …` | `test byte ptr [0xA8D5F8], 2; jne …` | NetworkEvent::Execute | [实证] |
| `0x004C80F6` | `f6 05 f8 d5 a8 00 02 75 0a` | `test byte ptr [0xA8D5F8], 2` | NetworkEvent::Execute 尾部 | [实证] |

**写点**（全 5 处 `A3 F8 D5 A8 00` = `mov [0xA8D5F8], eax`）[实证]：
`0x0048CF9A`、`0x0052DC3B`、`0x0052DD2A`、`0x0052E96A`、`0x0052F9F2`。
其中 `0x0052DC34–0x0052DC3B` 明确 `and al, 0xFD` 清 bit1——**bit1 只由引擎会话建立/拆除路径改写**，运行期读是稳定的。

#### 1.1.4 推荐读法（门控伪码）

```c
// 纯读，无副作用；每次判定缓存到 g_mpSessionState（见 §3）
static inline bool DetectMpPrimary() {
    return (*reinterpret_cast<const uint8_t*>(0x00A8D5F8) & 0x02) != 0;
}
```

---

### 1.2 辅助确认（避免误判，四选二升置信）

#### 1.2.1 `0xAA0444` 会话阶段 [实证]

| 字段 | 内容 |
|---|---|
| **地址** | `0x00AA0444`（BSS dword） |
| **语义** | 0=关闭 / 1=收包中 / 2=**模态等待（联机收包忙等）**（`audio_input_hotspots.md` 命名；本任务字节复算一致） |
| **关键读点** | `0x0053E86C`：`83 3D 44 04 AA 00 02` = `cmp dword ptr [0xAA0444], 2` → `jne 0x53EB01`。**只有 ==2 才进入 DirectPlay 收包忙等环 `0x53E8B3`** |
| **写点** | `0x0053E527`：`C7 05 44 04 AA 00 01 00 00 00`（=1）；`0x0053E59D`：`C7 05 44 04 AA 00 02 00 00 00`（=2）；`0x0053E2BD`：`89 35 44 04 AA 00`（写 esi） |
| **全文规模** | imm32 `44 04 AA 00` 共 **23** 处 |
| **辅助判据** | `[0xAA0444]==2` ⇒ 高度疑似联机模态；`==0` 且主判=0 ⇒ 单机 |
| **标签** | 读点/写点字节 [实证]；「单机局该值基本不为 2」 [待实测]（文档断言，需真机双端采样） |

```
0053E86C  83 3D 44 04 AA 00 02     cmp  dword ptr [0xAA0444], 2
0053E873  0F 85 88 02 00 00        jne  0x53EB01
0053E879  8B 1D 84 14 7E 00        mov  ebx, dword ptr [0x7E1484]   ; IAT/消息入口
...
0053E8B3  39 2D 78 04 AA 00        cmp  dword ptr [0xAA0478], ebp   ; 忙等自环点
0053E8DE  EB D3                    jmp  0x53E8B3
```

#### 1.2.2 `SessionClass` 状态字 `0x00A8B238` [实证]

| 字段 | 内容 |
|---|---|
| **地址** | `0x00A8B238`（`SessionClass` 游戏状态；`clock_frame_loop.md`：0=菜单，1/2/3/4=局内，5=加载…） |
| **全文规模** | imm32 `38 B2 A8 00` 共 **791** 处；`83 3D 38 B2 A8 00 imm8`（cmp imm）**147** 处 |
| **门控用法** | 仅作「是否局内」辅助：`[0xA8B238] ∈ {1,2,3,4}` 且主判=1 ⇒ 联机对局进行中；`=0`（菜单）时**不应**因残留位误判联机 |
| **注意** | 该 dword **不能单独区分单机/联机**——单机遭遇战同样处于 3/4。只作「在局内」门 |

> **【勘误 2026-09-27 · 已定谳】** 上表「0=菜单，1/2/3/4=局内，5=加载」**错误**。真身 = `SessionClass::Instance` 首成员 **`GameMode`**：`SessionClass.h:54` `reference<SessionClass,0xA8B238u>`（原地实例、非指针）；枚举 `GameMode { Campaign=0, LAN=3, Internet=4, Skirmish=5 }`（`GeneralDefinitions.h:670-675`）。⇒ 真机实测 **战役=0 / 遭遇战=5 就是枚举本身**；且 `0` 还被退局路径反复写入（`0x52E175/1FE/213/553/5D4` 均 `mov [0xA8B238],ebx (=0)`）⇒ **任何编码都无法用它区分菜单与局内**。本表「辅助确认 `∈{1,2,3,4}`」一项**作废**；改用引擎自身判据：`PlayerPtr(0xA83D4C)!=0 && ScenarioClass::Instance(0xA8B230)!=0 && (Scenario+0x3598)==0`（即 `RadarClass::Plot_Cell` 函数头 `0x00655C5D`/`0x00655C62` 所用判据）。详见 `[v1.8.3]` 与 `docs/re/radar_fix_report.md`。
| **标签** | [实证] |

```
0064737F  A1 38 B2 A8 00           mov  eax, dword ptr [0xA8B238]   ; NetFrameSync 内
00647474  A1 38 B2 A8 00           mov  eax, dword ptr [0xA8B238]
0048CF21  A1 38 B2 A8 00 83 F8 02  mov  eax,[0xA8B238]; cmp eax, 2  ; GameRunner 状态机
00448524  83 3D 38 B2 A8 00 04     cmp  dword ptr [0xA8B238], 4     ; 典型局内比较
```

#### 1.2.3 NetworkEvent 环计数 `0x00A802C8` [实证]

| 字段 | 内容 |
|---|---|
| **地址** | `0x00A802C8` = `QueuedEvents` 索引/计数（上限 `0x80`）；`0xA802D0` 写指针；`0xA802D4` 事件体（128×111B） |
| **全文规模** | `C8 02 A8 00` **143** 处；`D0 02 A8 00` **167** 处；`D4 02 A8 00` **50** 处 |
| **关键读点** | `0x006474DC`：`A1 C8 02 A8 00` = `mov eax, [0xA802C8]; test eax,eax; je 0x647586` |
| **辅助判据** | 短窗口内计数持续 >0 或单调变化 ⇒ 本地在产生/发送命令（联机命令流）。单机亦会产生 UI 命令，故**仅作弱辅助** |
| **标签** | [实证] |

```
006474DC  A1 C8 02 A8 00           mov  eax, dword ptr [0xA802C8]
006474E1  85 C0                    test eax, eax
006474E3  0F 84 9D 00 00 00        je   0x647586
```

#### 1.2.4 同步驱动 `0x647260` 是否入链 [实证]

| 字段 | 内容 |
|---|---|
| **调用点** | **全文唯一**：`0x0055DE40`（`MainLogicFrame` 尾部）。`E8 1B 94 0E 00` → rel32 解算目标 = **`0x00647260`** [实证] |
| **入链含义** | `0x55DE40` **每逻辑帧必调** `0x647260`（无条件 `call`）；真正区分单机/联机的是函数内部 `0xA8D5F8` bit1 早退 |
| **门控用法** | 不可把「是否 call 到 0x647260」当判据（单机也 call）；应把「**进入 0x647260 主体后是否走到 0x6472FC+**」或直接读 `0xA8D5F8` 当判据 |
| **标签** | [实证] |

```
0055DE40  E8 1B 94 0E 00           call 0x647260     ; rel32 → 0x00647260 ✓
0055DE45  E8 06 97 0D 00           call 0x637550
```

#### 1.2.5 网络命令环 `Queue`（`0x8B41F8/0x8B41FC/0x8B4204`）[实证]

| 全局 | 角色 | imm32 计数 |
|---|---|---|
| `0x008B41F8` | Queue 计数 | 39 |
| `0x008B41FC` | Queue 读游标 | 26 |
| `0x008B4204` | Queue 基址（0x4000×111B） | 25 |

辅助判据：`[0x8B41F8] > 0` ⇒ 有已排序网络命令待消费（联机强信号）。单机通常为 0。

#### 1.2.6 DirectPlay / 收包环（间接信号）

| 字段 | 内容 |
|---|---|
| **地址** | 收包忙等环 `0x0053E8B3`（`jmp 0x53E8B3` 自环）；入口门 `0x0053E86C` 测 `[0xAA0444]==2` |
| **IAT/句柄** | `0x007E1484`（`call ebx` 消息/收包入口）、`0x007E14C0`（回调）。**具体 IDirectPlay 句柄全局未定位** |
| **门控用法** | 不建议直接 hook 收包环；以 `0xAA0444==2` 间接等价 |
| **标签** | 环与门字节 [实证]；「DirectPlay 句柄地址」**[待实测]**（未在 `gamemd.exe` 静态定位唯一全局） |

#### 1.2.7 MPGameMode 指针 [待实测]

| 候选 | 证据 |
|---|---|
| `MultiplayerGameMode` vtable `0x005D7F20` | imm32 全文仅 **1** 处（`0x007EED60`，疑 RTTI/元数据）——**不是可稳定读的实例指针** [实证] |
| 真 MP 逻辑簇 | `0x5C0xxx–0x5D0xxx` 的 `*GameMode` 虚函数（`nonrle_blit_and_named_hotspots.md`）；`MPCooperative::v[43] 0x5C46E0` 等 |
| 结论 | **当前无单一「MPGameMode 指针」全局可做读点**；场景类型建议改读 `SessionClass` 邻域字段（如 `0xA8B238` 状态 + `0xA8D5F8`），或待真机在内存中扫描 GameMode 实例。**禁止猜地址** |

---

### 1.3 推荐主判定 + 辅助确认（防误判合成）

```c
enum MpConfidence { MP_OFF = 0, MP_AMBIGUOUS = 1, MP_ON = 2 };

MpConfidence DetectMpSession() {
    const uint8_t  sflags = *reinterpret_cast<const uint8_t*>(0x00A8D5F8); // 主
    const uint32_t phase  = *reinterpret_cast<const uint32_t*>(0x00AA0444);
    const uint32_t gs     = *reinterpret_cast<const uint32_t*>(0x00A8B238);
    const int32_t  qEv    = *reinterpret_cast<const int32_t*>(0x00A802C8);
    const int32_t  qNet   = *reinterpret_cast<const int32_t*>(0x008B41F8);

    const bool primary = (sflags & 0x02) != 0;          // 引擎自己的锁步开关
    const bool inGame  = (gs >= 1 && gs <= 4);
    int score = 0;
    if (primary)           score += 2;                  // 主判定权重最高
    if (phase == 2)        score += 1;                  // 联机模态
    if (inGame && primary) score += 1;                  // 局内+联机
    if (qNet > 0)          score += 1;                  // 网络命令环非空
    if (qEv > 0 && primary) score += 1;                 // 本地命令+联机

    if (score >= 2) return MP_ON;
    if (primary)    return MP_ON;                       // 主判单票也足够（引擎同源）
    if (phase == 2) return MP_AMBIGUOUS;                // 弱信号单独出现 → 保守
    return MP_OFF;
}
```

**误判防护矩阵**：

| 误判方向 | 后果 | 防护 |
|---|---|---|
| 联机误判为单机 | 保留 VIOLATION/RISK → **desync（致命）** | 主判定取引擎同源 `0xA8D5F8`；分数≥2 或 primary 即 MP_ON；失败默认 MP |
| 单机误判为联机 | 单机功能消失（体验） | 可接受；`ForceSinglePlayer=1` 覆盖；遥测 `mpFalsePositiveSuspect` |
| 菜单/加载中误判 | 无关紧要 | `gs` 不在 1..4 时不给分 |
| 读档后残留位 | 短暂误降级 | 会话拆除时引擎自清 bit1（`0x52DC34` `and al,0xFD`）；门控每 N 帧重采样 |

**采样时机**：① DLL `LoadConfig` 后一次；② 每逻辑帧（`UpdateVisionGrid` 帧守卫旁，`CurrentFrame` 变化时）；③ 主判位从 0→1 或 1→0 边沿立即刷新。边沿切换时打遥测日志。

---

## 2. 降级白名单（联机必须旁路 / SAFE 保留）

### 2.1 总表

> 「门控代码位置」给 `ra2render/blitter_hooks.cpp` 现行行号（只读快照，1797 行构建）与 Hook 名；落地时以符号搜定位，行号漂移不阻塞。
> 「默认值」指**联机降级后**的生效值；「单机默认」指未降级时。

| # | 项 | M-4 判定 | 门控代码位置 | 联机必须 | 联机默认/动作 | 单机默认 | 回滚 |
|---|---|---|---|---|---|---|---|
| W1 | **`>>4` / ThrottleKey 节流** | **VIOLATION**（现网指针键）/ 修键后 RISK | `Hook_Techno_SelectAutoTarget` `:437-440`；`Hook_Unit_SelectAutoTarget` `:458-461`；`Hook_Techno_Greatest_Threat` `:496-499`；键 `ThrottleKey()` `:168`；配置 `TargetScanInterval` `:4,:62-64` | **旁路节流** | **强制 `g_targetScanInterval=1`**（三处 `if (g_targetScanInterval > 1 && …)` 永不进入 → 原版全量扫描） | `TargetScanInterval=8`（或 ini） | ini / `MpAutoDowngrade=0` |
| W2 | **Threat Retention 短路** | **RISK**（返回值替代） | `Hook_Techno_Greatest_Threat` 节流帧 `return pTarget` 短路（`:496-509` 一带）；读 `+0x5D4/+0x6C/+0x81` | **禁短路返回** | 与 W1 同门：`interval==1` 时短路分支不进入；若独立开关则 `MpThreatRetention=0` | 允许（修键后） | 同上 |
| W3 | **S1 SpySat TYPE 补丁** | **RISK** | `PatchSpySatBuildingTypes()` `:597`（懒加载 `:741-742`）；写 `SuperWeaponTypeClass+0xB0/+0xF8`、`BuildingTypeClass+0x16A5/+0x16F0` | **跳过补丁** | `if (MpActive()) return;` 置于 `PatchSpySatBuildingTypes` 入口；`s_spySatPatched` 不置位 | `EnableSpySatRadarSweep=1` 时打补丁 | 联机不写 TYPE → 无需还原；单机回滚见审计 A8（建议补 Remove） |
| W4 | **S2 `ScenarioClass` 标志写** | **RISK** | `UpdateVisionGrid` `:748-751` `*(uint32_t*)scenarioBase &= ~0x1000u` | **跳过写** | `if (MpActive()) skip;` **不写**（保持引擎原值） | 每帧清 `0x1000` | 随门控 |
| W5 | **S3 `House+0x577A` 写** | **RISK** | `UpdateVisionGrid` `:754` `*(uint8_t*)(pPlayer+0x577A)=0` | **跳过写** | `if (MpActive()) skip;` **不写** | 每帧清 0 | 随门控 |
| W6 | **UpdateVisionGrid 无条件调用** | 载体（S1/S2/S3） | 调用点 `:883`、`:955`、`:1004`、`:1040`；asm 注释 `:1380`（`Hook_RadarPlot_Proxy` 内） | **调用保留、状态写旁路** | 不禁止函数本身（everSeen/网格是 DLL 私有 SAFE）；仅 W3/W4/W5 三段状态副作用被 MpActive() 旁路。若需更狠：联机直接不调 `UpdateVisionGrid`（表现层 everSeen 失效，可接受） | 无条件调用 | 随门控 |

### 2.2 SAFE 保留（联机不旁路）

| 类 | 项 | 说明 |
|---|---|---|
| Blit×6 | `Hook_BlitTransXlatAlphaZRead` / `Hook_BlitTransXlat_G` / `Hook_RLEBlitTransXlat_G` / `Hook_BlitTrans_G` / `Hook_BlitTransDarken_G` / `Hook_BlitPlain_G` | 纯像素，不进 CRC/存档 |
| Draw 剔除×5 | `Hook_Unit_Draw` / `Hook_Infantry_Draw` / `Hook_Aircraft_Draw` / `Hook_Building_Draw` / `Hook_Bullet_Draw`（槽 69） | 只拦 `Draw` 虚函数；`s_visionGrid`/`s_everSeenGrid` 私有 |
| Cell/混色×3 | `Hook_CellClass_Draw` `0x4801F0` / `Hook_FogBlendB1_Stub` `0x47F40F` / `Hook_FogBlendB2_Stub` `0x47F4AE` | 像素混色 |
| L4 全量刷 | `0x006D3D99` 补丁 | dirty-rect 域，SAFE（建议补独立键，非本规格必须） |
| 雷达×2 | `Hook_RadarPlot_Proxy` `0x6574C3` / `Hook_RadarPending_Proxy` `0x65719A` | 像素；**注意缺陷1 崩溃**与同步无关，但联机掉线同样致命 → 建议联机默认 `EnableMinimapFog=0` |
> 【W3 勘误 · W3-A6/ISSUE-DISAMBIG-RADAR-HOOK】改前：0x6574C3；改后：0x006574C3（RadarClass::Plot_Cell 主循环调用点，见 ra2render.h:158；实际补丁下沉点位于 0x00655D38，见 blitter_hooks.cpp:150, 3016）；依据：ra2render/ra2render.h:158; ra2render/blitter_hooks.cpp:150, 2711, 2920, 3016, 3090；分级：P2
| S4 | 战局重载清网格 | DLL 私有 |

> **【勘误 DA4-1 · 2026-09-27】（原文保留，未删字：上表「雷达×2」行照旧）**
> - **分类**：本条属「**误当现网安装点**」——原文把调用点 `0x006574C3`（`0x6574C3`）写成 `Hook_RadarPlot_Proxy` 的落点。
> - **订正后（现网口径）**：安装点 = **`RadarClass::Plot_Cell(0x00655C50)` 内部下沉点 `0x00655D38`（9 字节：`E9 rel32` + 4×`90`；跳板还原 9 字节后 `jmp 0x00655D41`）+ 强制刷新 `0x0065719A`（5 字节 `call` 等长）**。`0x006574C3` 仍是**原版调用链事实**（`E8 88 E7 FF FF` = `call 0x00655C50`），但**已非安装点**，仅余 `ra2render.h:76-77` 死宏 `ADDR_RADAR_PLOT` / `ADDR_RADAR_PLOT_CALLSITE`（cpp 零引用）。
> - **真机证据**：`ra2youli/ra2render.log:1099`（同文共 15 处）——「成功挂载路线 A 下沉挂钩 (Plot_Cell 0x00655D38 9 字节补丁 + 强制刷新 0x0065719A)」。
> - **字节依据**（`out/re_work/da4/claims.txt`，`tools/audit_bytes.py` 12/12 全 OK）：`0x00655D38 = 89 44 24 28 A1 50 35 B7 00`、`0x00655D41 = 3B C5 74 18`、`0x0065719A = E8 91 93 00 00`、`0x006574C3 = E8 88 E7 FF FF`。
> - **影响面**：本表两列的**联机判定结论不变**（`Hook_RadarPlot_Proxy`/`Hook_RadarPending_Proxy` 仍为像素层「可动」项，联机默认 `EnableMinimapFog=0` 的建议不变）；仅**安装地址口径**须以 `0x00655D38` + `0x0065719A` 为准。与 `docs/re/doc_consistency_fix_list.md` §3.3 N-3 / §4 P0 一致。

> **红线重申**（`RE_COORDINATION.md` §3 + net_sync §5/§10）：门控本身不得触碰 `IsShrouded(0x487950)` / `IsCellShrouded(0x5865E0)` / `RevealArea*`、RNG `0x65C6D0` 族、命令序、`Compute_Frame_CRC 0x64DAB0`、枚举顺序。**降级只做「旁路增强」，不做「写回引擎」**。

### 2.3 每项门控伪码（供 ZCode 落地）

```c
// ---- 公共状态（DLL 私有，不进档、不进 CRC）----
static MpConfidence g_mpSessionState = MP_AMBIGUOUS; // 保守默认：不确定→按联机
static uint32_t     g_mpDowngraded = 0, g_mpRestore = 0, g_mpDetectPoll = 0;

static inline bool MpActive() {
    return g_mpSessionState != MP_OFF;  // AMBIGUOUS 视同联机（保守）
}

// ---- W1/W2：节流/Retention（配置层强制，最小改动）----
void ApplyMpLogicGate() {
    if (MpActive()) {
        g_targetScanInterval = 1;       // 三处短路分支永不进入
        g_mpDowngraded |= 0x01;
    }
    // 单机且未 ForceSinglePlayer 时按 ini 恢复
}

// ---- W3：SpySat TYPE ----
void PatchSpySatBuildingTypes() {
    if (MpActive()) { g_mpDowngraded |= 0x04; return; }  // 不写 TYPE
    ...
}

// ---- W4/W5：Scenario / House 状态写 ----
void UpdateVisionGrid() {
    ...
    if (!s_spySatPatched) {
        if (!MpActive()) PatchSpySatBuildingTypes();     // W3
    }
    if (!MpActive()) {                                   // W4+W5
        uintptr_t scenarioBase = *reinterpret_cast<uintptr_t*>(ADDR_SCENARIO_INSTANCE);
        if (scenarioBase) *reinterpret_cast<uint32_t*>(scenarioBase) &= ~0x1000u;
        *reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(pPlayer) + 0x577A) = 0;
        g_mpDowngraded |= 0x18;
    }
    ...
}
```

**不改逻辑状态证明**：W1/W2 只影响「本端是否跑增强节流/Retention」；W3 不写 TYPE；W4/W5 不写引擎全局。凡被旁路的路径，行为回到**原版语义**或**纯本地增强**，均不进入 `0x64DAB0` 帧 CRC 对象扫描与 `v[13]` Checksum。

---

## 3. 门控语义

### 3.1 状态机

| 状态 | 进入条件 | 动作 | 退出 |
|---|---|---|---|
| **SINGLE** | `DetectMp()==MP_OFF` 且 `ForceSinglePlayer==0` | 全增强按 ini | 主判翻转或 AMBIGUOUS |
| **MULTIPLAYER** | `DetectMp()==MP_ON` 或 `MP_AMBIGUOUS` | **自动旁路 W1–W6**；SAFE 保留 | 主判位 0→ 持续 N 帧稳定 |
| **FORCE_SP** | `ForceSinglePlayer=1` | 忽略检测，全增强 | 配置关闭 |
| **DISABLED** | `MpAutoDowngrade=0` | 门控完全不作用（现网行为） | 配置开启 |

### 3.2 硬性语义约束

1. **检测到联机 → 自动旁路**：不改逻辑状态、不影响帧 CRC `0x64DAB0`。旁路 = 「不执行增强写/短路」，不是「写相反值」。
2. **检测失败 → 保守默认降级**：`g_mpSessionState` 初值 = `MP_AMBIGUOUS`；`DetectMp()` 抛异常/读失败 ⇒ 保持 AMBIGUOUS（视同联机）。
3. **单机强制开启**：`[Logic] ForceSinglePlayer=1` → 跳过检测，强制 SINGLE（调试/单机验收用）。与 `MpAutoDowngrade` 互斥时 **ForceSinglePlayer 优先**（显式意图）。
4. **不触碰同步契约**：门控读点全是引擎全局只读；门控写点全是 DLL 私有计数/状态。禁止在门控路径调用 RNG、改枚举序、写 `ScenarioClass`/`House`/Techno。
5. **帧 CRC 无影响**：被旁路的 W4/W5 原本写的是常量（`&= ~0x1000` / `=0`）；联机不写时两端必须都「不写」或都「写」——混联时原版端不写，本端也不写 ⇒ 一致。单机本端写、无对手 ⇒ 无 CRC 比对。
6. **切换沿**：SINGLE→MP 在 `0xA8D5F8` bit1 置位边沿立即生效（下一门控点起旁路）；MP→SINGLE 建议**连续 30 帧**主判=0 再恢复增强，防抖。切换打遥测。

### 3.3 与「混联只能不加载 DLL」的关系

| 场景 | 现网 | 本规格落地后 |
|---|---|---|
| 本端单机 | 全增强 | 全增强（或误降级→ForceSinglePlayer） |
| 全端同 DLL+同 ini | 可联机（须手工 ini） | 自动；W1 强制 interval=1 |
| **混联（对方原版）** | **只能不加载 DLL** | **可加载**：本端自动旁路 W1–W6，逻辑面与原版一致；SAFE 表现层差异不 desync |
| 混联但用户强开 ForceSinglePlayer | — | 危险：S2/S3/TYPE 会写 → **必须在 UI/日志红字警告**；遥测 `mpForceSpInSession` |

---

## 4. 遥测与回滚

### 4.1 计数器（DLL 私有 uint32，2 秒遥测行输出，格式对齐现有 `ra2render.log`）

| 计数器 | 含义 | 递增时机 |
|---|---|---|
| `mpDowngraded` | 联机旁路总次数（位图累计亦可） | 任一 W 项被旁路时 +1 或置位 |
| `mpDetectPoll` | 检测轮询次数 | 每次 `DetectMpSession()` |
| `mpDetectOn` | 判定为联机次数 | `MP_ON` |
| `mpDetectAmbiguous` | 保守降级次数 | `MP_AMBIGUOUS` |
| `mpDetectEdge` | 主判位翻转次数 | bit1 0↔1 边沿 |
| `mpForceSpInSession` | 会话中 ForceSinglePlayer（危险） | 检测 MP 但被强制 SP |
| `mpFalsePositiveSuspect` | 疑似误判联机（主判=0 但曾降级且无网络信号） | 启发式 |
| `mpGateErrors` | 检测读失败/异常 | catch |

遥测行示例：

```
[ra2render] mp gate: state=MULTIPLAYER downgraded=0x1D poll=12041 on=11800 amb=12 edge=2 forceSpInSession=0
```

### 4.2 ini 覆盖键（建议名，`[Logic]` 段）

| 键 | 默认 | 语义 |
|---|---|---|
| `MpAutoDowngrade` | **1** | 总闸：0=关闭整个自动降级（现网行为） |
| `MpDetectIntervalFrames` | 30 | 检测重采样间隔（帧） |
| `MpDebounceFrames` | 30 | MP→SP 恢复防抖帧数 |
| `ForceSinglePlayer` | 0 | 强制单机增强（覆盖检测） |
| `MpThrottleForceInterval` | 1 | 联机时 `TargetScanInterval` 强制值（1=完全旁路） |
| `MpBypassSpySatTypes` | 1 | W3 总开关（0=联机也打 TYPE 补丁，仅全端同 DLL 时可试） |
| `MpBypassStateWrites` | 1 | W4/W5 总开关 |
| `MpDisableThreatRetention` | 1 | W2 总开关 |
| `MpTelemetry` | 1 | 0=不打 mp gate 遥测行 |

> 键名与 `telemetry_and_switches_spec.md` 的 `OnlineSafeMode` 思路兼容：`OnlineSafeMode=1` 可视为 `MpAutoDowngrade=1` 的别名（落地时任选，文档二选一统一）。
>
> 【W3 勘误 · Lead DC-05】[W3-Lead临时裁决] 改前：§4.2 各键命名与反极性（如 `MpDisableThreatRetention`、`MpBypassStateWrites`）；改后：依 DC-05 裁决节名全部归入 `[Logic]`，极性统一为 `Enable*=1` 表示启用该行为（`MpStateWrites` 仍成键，不采丙案不设键）；依据：Lead 临时裁决 DC-05；分级：[推演]

### 4.3 误判联机导致单机功能消失的回滚开关

| 场景 | 开关 | 效果 |
|---|---|---|
| 单机被误降级 | `ForceSinglePlayer=1` | 立即恢复全部增强（用户显式声明） |
| 门控整体有害 | `MpAutoDowngrade=0` | 完全回到现网行为（一键回滚） |
| 只想关某项 | `MpBypass*=0` 对应键 | 单项不旁路（调试） |
| 紧急 | 移除/改名 `ra2render.dll` | 进程级回滚（既有 Install/Remove 对称路径不变） |

**回滚验证要求**：每次开 `MpAutoDowngrade=0` 后，单机功能集应与「无门控构建」逐键一致；联机若强行开 0，日志须红字提示 desync 风险。

---

## 5. 验证方法（对照 net_sync 帧 CRC / Checksum）

### 5.1 总原则

> **验证的是「门控生效」且「不引入新分叉」**——两边都要证。
> 参考：`net_sync_checksum.md` §3.2 帧 CRC `0x64DAB0`→`CurrentFrameCRC@0xAC51FC`、`LatestFramesCRC[256]@0xB04474`；desync 检出 `0x64C6E2–0x64C6F2`；诊断 `H-D5/H-D6` 镜像（`net_sync_fix_spec.md`）。

### 5.2 单机场景（证明「增强仍在」+「误降级可回滚」）

| 步骤 | 操作 | 期望 |
|---|---|---|
| S-1 | `MpAutoDowngrade=1`，进单机遭遇战 | 遥测 `state=SINGLE`，`mpDowngraded` 不增；SpySat/迷雾/节流增强按 ini 生效 |
| S-2 | 同局开关 `ForceSinglePlayer=1/0` | 功能集可逆；无 `except.txt` 新增 |
| S-3 | 人为制造 AMBIGUOUS（临时把主判读点 mock 为 0 且 phase=2） | `mpDetectAmbiguous` 增，功能降级；`ForceSinglePlayer=1` 恢复 |
| S-4 | `MpAutoDowngrade=0` | 与无门控构建行为一致（键位/遥测对比） |

**证据**：真实截图（《实测证据标准 v2》）、`ra2render.log` 遥测时间线、2 秒计数非零（增强项）。

### 5.3 联机场景（证明「旁路生效」+「无新分叉」）

| 步骤 | 操作 | 期望 |
|---|---|---|
| M-1 | **双端同 DLL** 进联机（局域网/回环） | 双端遥测 `state=MULTIPLAYER`；`TargetScanInterval` 实际=1；W3–W5 未执行 |
| M-2 | 双端跑 ≥3 局 U200/U800 | **逐帧 `LatestFramesCRC` 一致**；无 `TXT_OUT_OF_SYNC`/`SYNC*.TXT` |
| M-3 | 对照 `Compute_Frame_CRC 0x64DAB0` 镜像（H-D5） | 双端 CRC 流零差异 |
| M-4 | **混联**（一端原版 gamemd 无 DLL，一端本 DLL+门控） | 本端自动旁路；≥2 局无 desync（**这是本规格的杀手验收**） |
| M-5 | 会话中翻转 `ForceSinglePlayer=1`（负向） | 应出现 `mpForceSpInSession`；若 desync 则证明门控必要（记录为红线操作） |
| M-6 | 对局结束回单机 | 防抖 `MpDebounceFrames` 后恢复增强；无残留降级 |

**分叉归因**：若 M-2/M-4 出现 desync，先取 `SYNC*.TXT` 与 H-D2 快照，对照本规格 W 表——若 desync 字段落在 W1–W6 已旁路面，说明旁路不彻底（门控 bug）；若落在其他面，归其它缺陷。

### 5.4 不引入新分叉的静态证明（[静态核验]）

1. 门控代码路径**零写**引擎全局（代码审查 + 跟踪点）：只写 `g_mp*` / ini 变量。
2. W1 联机强制 `interval=1` 后，三处 `if (g_targetScanInterval > 1 …)` 短路分支不可达（与 `MP_SAFETY_REVIEW` §4.1 同构）。
3. W4/W5 联机不执行写指令 ⇒ 与原版字节级同状态（原版也无这两条写）。
4. 帧 CRC 对象扫描表不含 DLL 私有全局（net_sync §3.2 既有结论）。

### 5.5 验收清单（ZCode 落地后勾选）

- [ ] 主判定读点与本文 §1.1 字节一致（构建前用 `verify_mp_detect_bytes.py` 复跑）
- [ ] 联机自动降级：W1–W6 全部可遥测证明「未执行」
- [ ] 单机增强不减：功能键逐一开关回归
- [ ] 混联 ≥2 局无 desync（杀手用例）
- [ ] `MpAutoDowngrade=0` 一键回滚有效
- [ ] `ForceSinglePlayer` 误用有红字警告 + 遥测
- [ ] 连续 3 局无 `except.txt` 新增（沿 v1.6.0 稳定性闸门）

---

## 6. 附录

### 6.1 字节证据存档

| 文件 | 内容 |
|---|---|
| `out/re_work/mp_autodowngrade/verify_mp_detect_bytes.py` | 主检测点 capstone 复算脚本 |
| `out/re_work/mp_autodowngrade/verify_mp_detect_bytes_out.txt` | 输出（§1.1–§1.2 全部原始字节） |
| `out/re_work/mp_autodowngrade/verify_mp_detect_bytes2.py` | 补充：DirectPlay 环 / `0xAA0444` / 写点 / 调用者 |
| `out/re_work/mp_autodowngrade/verify_mp_detect_bytes2_out.txt` | 输出 |

关键字节速查：

| VA | raw | 含义 |
|---|---|---|
| `0x00647260` | `A0 F8 D5 A8 00` | `mov al,[0xA8D5F8]` 主判定 |
| `0x00647268` | `A8 02` | `test al,2` |
| `0x0064726E` | `0F 84 53 02 00 00` | `je 0x6474C7` 单机早退 |
| `0x0064729F` | `84 1D F8 D5 A8 00` | `test [0xA8D5F8], bl`（bit2） |
| `0x0055DE40` | `E8 1B 94 0E 00` | `call 0x647260`（唯一调用点） |
| `0x0053E86C` | `83 3D 44 04 AA 00 02` | `cmp [0xAA0444],2` DirectPlay 门 |
| `0x0052DC34` | `A1 F8 D5 A8 00 24 FD` | 清 bit1 写点 |

### 6.2 与既有文档交叉

| 文档 | 交叉点 |
|---|---|
| `MP_SAFETY_REVIEW.md` | §0 VIOLATION×3/RISK×4/SAFE×18 为本白名单输入；§4.3 指出 S2/S3 无键、混联只能不加载 DLL——本规格即解此 |
| `net_sync_checksum.md` | §3.2 帧 CRC、§4.2 序列化、§7.10 单机早退、§8 速查 |
| `INSTALLED_HOOKS_AUDIT.md` | §4-B1 指针哈希；A6 无键补丁；A8 SpySat 无还原；S1–S4 |
| `telemetry_and_switches_spec.md` | `OnlineSafeMode` 与本 `MpAutoDowngrade` 对齐 |
| `net_sync_fix_spec.md` | H-D5/H-D6 镜像作联机验收探针 |

### 6.3 遗留 / 待实测

1. **MPGameMode 实例指针**未定位唯一全局 [待实测]；现用 `0xA8D5F8`+`0xAA0444` 足够，不阻塞。
2. **DirectPlay 句柄**静态未收敛 [待实测]；以 `0xAA0444==2` 间接等价。
3. **`0xA8D5F8` bit2/bit3 语义**仅知 `0x64729F/0x6472B6` 测 bit2、`0x48CF0E` 测 bit0\|1 [实证读点]，**位域完整命名**待真机采样 [待实测]。
4. **bit1 被引擎置位的完整写点集合**（5 处 `A3 F8 D5 A8 00`）中各分支语义未逐支命名；不影响「只读 bit1」的门控正确性。
5. 混联杀手用例（§5.3 M-4）**尚未跑**——落地后必测。

---

> **台账 §九 草稿**（供 Lead 合并）：
> ```
> ### [v1.5.x] - 联机自动降级门控规格（M-6，规格-only，无补丁）
> #### 1. 现象与需求描述
> - S2 Scenario 标志写 / S3 House+0x577A 无 ini 门控，混联只能不加载 DLL；
>   需产品级「检测联机→自动旁路 VIOLATION/RISK，单机保留增强」方案。
> #### 2. 逆向调研与根因剖析
> - 主判定 0xA8D5F8 bit1（NetFrameSync 0x647260 入口 A0 F8 D5 A8 00 / A8 02 / je 0x6474C7）；
> - 辅助：0xAA0444==2（0x53E86C cmp）、0xA8B238 局内、0xA802C8/0x8B41F8 事件环；
> - 唯一 call 0x647260 @ 0x55DE40（E8 1B 94 0E 00）。
> - 白名单 W1–W6：ThrottleKey 节流 / Threat Retention / S1 TYPE / S2 / S3 / UpdateVisionGrid 状态写；
>   SAFE 18 项保留。检测失败保守降级；ForceSinglePlayer / MpAutoDowngrade 回滚。
> #### 3. 具体修改与补丁实现
> - 无代码补丁。产出 docs/re/mp_autodowngrade_spec.md + verify_mp_detect_bytes*.py 字节存档。
> #### 4. 实测验证效果
> - [静态核验] capstone 逐字节实证；混联/双端 CRC 对拍 [待实测]，验收清单见规格 §5。
> ```
