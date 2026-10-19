# R-AUDIO-LIMIT 音频限频落地规格（Audio Throttle Landing Spec）

> **文档标识**：`docs/re/audio_throttle_landing.md`  
> **任务编号**：R-AUDIO-LIMIT（由「已逆向未落地」收成）  
> **逆向目标**：`ra2youli/gamemd.exe` YR 1.001，ImageBase `0x00400000`，`FileOffset = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：`[实证]` = VA + FileOffset + 机器码（本轮 `out/re_work/re_sprint/R_audio_limit/*.py` 复算）；`[推演]` = 相邻实证 + x86/MSVC 习惯；`[待实测]` = 需真机  
> **上游深潜**：`docs/re/audio_engine_deep_dive.md`、`docs/re/audio_input_hotspots.md`、`docs/re/crt_memory_pool_deep_dive.md`、`docs/re/trigger_determinism_deep_dive.md`  
> **边界**：只读逆向 + 规格落地；不改 `ra2render/**`、`gamemd.exe`、`ra2youli/**`、`tools/**`、台账/看板/ATLAS  

---

## 0. 一页结论

| 维度 | 结论 | 级别 |
|---|---|---|
| **限频点 VA** | 主钩 `VocClass::PlayGlobal@0x00750920`、`VocClass::PlayAt@0x007509E0`；辅钩 `PlayIndexAtPos@0x00750E20`（省 200 槽请求节点） | [实证] |
| **通道池** | **300 槽**确认：`mov ecx, 0x12C` @ `0x403F42`，单槽 `0x280=640B`，池头 `[0x87E2A8]`；分配 `0x405190` 零抢占 | [实证] |
| **原生 Limit/MinDelay** | 播放入口**不读**；`Limit` 仅在 `0x4042EA` 事后强斩（`0x404D80` 爆音源）；`MinDelay` 仅循环音 `0x40573D` | [实证] |
| **建议参数** | `Enable=0`（默认关）、`MaxVoicePerFrame=6`、`VoiceDedupMs=80`、`WhitelistPriorityMin=3`、`WhitelistTypeMask=0x90` | [推演]+[待实测] |
| **确定性** | **入口丢弃对 lockstep 安全**：Play* 内部 0 次同步 RNG；生命周期 RNG 全是 `Randomizer::Global@0x886B88`（非同步）；触发器 `0x62` 先吃 `Scenario::Random` 再 Play | [实证] |
| **CRT 耦合** | **低**：仅初始化一次性 `operator new(194408)` 走 `CRT::_new@0x7C8E17`；运行时 Voice 分配纯 Freelist，不进 CRT | [实证] |

---

## 1. 音频播放/调度路径

### 1.1 入口与 ABI [实证]

| 函数 | VA | FileOffset | 入口机器码 | 约定 | 失败出口 |
|---|---|---|---|---|---|
| `VocClass::PlayGlobal` | `0x00750920` | `0x350920` | `51 A0 AC 64 84 00` | `__fastcall`：`ECX=SoundID, EDX=Panning`；栈 `[ESP+4]=float Volume, [ESP+8]=AudioController*`；`ret 8` | `0x75092E: 33 C0 59 C2 08 00`（eax=0） |
| `VocClass::PlayAt` | `0x007509E0` | `0x3509E0` | `A0 AC 64 84 00` | `__fastcall`：`ECX=SoundID, EDX=CoordStruct*`；栈 `[ESP+4]=AudioController*`；`ret 4` | `0x7509EC: 33 C0 5B C2 04 00`（eax=0） |
| `VocClass::PlayIndexAtPos` | `0x00750E20` | `0x350E20` | `55 8B E9 56 57` | `__fastcall`：`ECX=n, EDX=CoordStruct*`；栈 `a3`；`ret 4` | `0x750E2B: xor eax,eax; … ret 4` |
| `EVA::QueueVoice` | `0x00752700` | `0x352700` | `53 57 8B F9 8B DA` | **独立流，不走 300 槽池** | — |

三者第一道闸均为 `VoicesEnabled [0x8464AC]`；SoundID 边界：`Array->Items [0xB1D37C]`、`Count [0xB1D388]`。

**直呼点普查**（Capstone 全文 rel32 扫描）[实证]：

| 目标 | 直呼数 | 典型簇 |
|---|---|---|
| `PlayGlobal` | **116** | `0x63xxxx`(22) UI/Sidebar、`0x6Axxxx`(13)、`0x61xxxx`(9) |
| `PlayAt` | **97** | `0x44xxxx`(10) 开火/死亡、`0x51xxxx`(9)、`0x70xxxx`(9)、`0x4Dxxxx`(7) 武器多采样、`0x73xxxx`(7) 建筑 +0x56C/570 |
| `PlayIndexAtPos` | **18** | 含触发器 `0x6DE831`（动作 0x62）、`0x6E181B` |
| `EVA::QueueVoice` | **77** | 战术语音，**禁止限频** |
| `VoiceAlloc 0x405190` | **4** | `0x4066C0` / `PlayGlobal` / `PlayAt` / `PlayIndexAtPos` 间接 |

### 1.2 通道池 ABI（~300 槽复核 = 确认）[实证]

```
0x403F3D  mov  edx, 0x280          ; 单槽 640B
0x403F42  mov  ecx, 0x12C          ; 容量 300
0x403F4C  call 0x4074D0            ; FixedPool::Init
0x403F51  mov  [0x87E2A8], eax     ; 池头
```

| 全局 | 含义 |
|---|---|
| `[0x87E2A8]` | Voice 池 Freelist 头（300 槽） |
| `[0x87E180]` | 活跃 Voice 双向链表头 |
| `[0x87E28C]` / `[0x87E290]` | 当前活跃数 / 历史峰值 |
| `[0x81610C]` | 全局递增 Handle 源 |
| `slot+0x18` | 状态位：`bit0=0x01` 终止可回收；`bit7=0x80` 动态堆 |
| `slot+0x1C` | 播放态：0 空闲 / 1 准备 / 2 播放 / 4 已停 |
| `slot+0x24` | `VocClass*` |
| `slot+0x138` | Handle |

**分配 `0x405190` 策略**[实证]：
1. O(1) `FixedPool::Pop [0x407520]`；
2. 失败则扫活跃链表，仅回收 `bit0==1` 的**已终止**节点（`0x4051ED: test al,1`）；
3. 再 Pop；仍空 → **返回 NULL**。

**零抢占设计**[实证]：不读 Priority（`+0x40`）、无 LRU、无最老抢占。300 槽全在发声时新声全部静默。

**第二池：3D 请求节点**[实证]：
```
0x7510E5  mov  edx, 0x3C           ; 节点 60B
0x7510EA  mov  ecx, 0xC8           ; 容量 200
0x7510EF  call 0x4074D0
0x7510F6  mov  [0xB1D3A4], eax     ; 池头
```
`PlayIndexAtPos` 先 Pop 节点、填坐标、再 `call PlayAt@0x750E82`、链入 `[0xB1D320]`；由 `0x750EC0` 每 33ms 推进。**只钩 PlayAt 仍会耗请求节点**——故建议双钩。

### 1.3 限频点（原生）与 33ms 节流 [实证]

| 机制 | 字段/VA | 真实执行点 | 问题 |
|---|---|---|---|
| `Limit` | `Voc+0x48`（写 `0x4065D0`） | **仅** `0x4042EA` 读，超限 `0x404D80` 强停 | 事后强斩 → DAC 阶跃爆音 |
| `MinDelay/MaxDelay` | `+0x58/0x5C`（写 `0x406600`） | **仅** `0x40573D`，且 `Control & 0x88`（LOOP/PREDELAY/AMBIENT） | 跨单位同声 0 拦截 |
| `Range/MinVolume` | `+0x50/0x54` | `PlayAt` 内 `0x750AC0` 衰减 | 已有，保留 |
| `Priority` | `+0x40`（写 `0x406540`） | **分配层不读** | 低优先可挤掉高优先 |
| `AudioFrameUpdate` | `0x406F70` | `cmp eax,0x21`（33ms）门 | **禁止在此截流** |

---

## 2. 高频触发点与重复短路安全性

### 2.1 爆炸 / 建造 / 语音 触发点 [实证]

| 场景 | 入口 | 代表 VA | 说明 |
|---|---|---|---|
| 武器开火（多采样随机） | `PlayAt` | `0x44D51A`、`0x4DAAE2`、`0x519803`、`0x70218B`、`0x73A033` | 先 `Random/RandomRanged` 选样本再 Play |
| 单位死亡/受击 | `PlayAt` | `0x449B92`、`0x44A856`、`0x44A899`、`0x44B9A3` | `this+0x6A0/6A4/718` 音效槽 |
| 建筑伤害/摧毁 | `PlayAt` | `0x739A54`、`0x739CB9`、`0x739EB3` | `type+0x56C/0x570` |
| 动画爆炸 | `PlayAt` / `PlayIndexAtPos` | `0x4470FA`、`0x6CCE28`… | AnimClass 音效 |
| 触发器 `PlaySoundEffectRandom` (0x62) | `PlayIndexAtPos` | RNG `0x6DE80F` → Play `0x6DE831` | **先 RNG 后 Play** |
| 触发器 `PlaySoundEffect` | `PlayIndexAtPos` | RNG `0x6E17DE` → Play `0x6E181B` | 同上 |
| EVA 战术语音 | `QueueVoice` | 77 处 | **独立 AudioStream，不限频** |
| UI/全局 | `PlayGlobal` | `0x63xxxx` 22 处 | 白名单透传 |

### 2.2 重复短路 vs RNG/确定性 [实证 + 推演]

**关键事实**：

1. `PlayGlobal` / `PlayAt` / `PlayIndexAtPos` / `VoiceAlloc` **函数体内 0 次** `Random/RandomRanged`。[实证]
2. 音频生命周期 RNG（样本选择 `0x4047EA/0x404918/0x4049EE`、FShift `0x405684`、VShift `0x40569C`、MinDelay `0x40574A`、`0x405B19`）**全部** `mov ecx, 0x886B88` = **`Randomizer::Global`（非 lockstep）**。[实证]
3. 帧 CRC `0x64DE3F` 用 `lea ecx,[Scenario+0x218]` = **`ScenarioClass::Random`（同步流）**，**不在音频路径**。[实证]
4. 触发器 0x62 / 0x6E17DE 的同步 RNG **在 Play 调用之前**消费；入口返回 NULL 不会跳过该次 `Scenario::Random`。[实证]
5. 抽样 12 处 PlayAt 调用者：**无人**把 `eax` 返回值作为后续同步 RNG 的门控；NULL 是原版池耗尽既有契约。[实证]

**结论**：

| 短路位置 | lockstep 安全？ | 理由 |
|---|---|---|
| Play* 入口前置拦截，`return NULL` | **安全** | 调用方 RNG 已消费或用 Global；跳过的仅 Global |
| 整段跳过触发器动作（含 0x62 的 RandomRanged） | **不安全** | 掉同步 RNG |
| 在 `0x4041D0` / `0x406F70` 内截流改生命周期 | **不安全/有害** | 破坏样本生命周期 + 可能改 Global 序列（非同步但体感差）+ 强斩爆音 |
| 改 `0x64DE3F` 帧 CRC RNG | **严禁** | 直接分叉 CRC |

**残余风险**[待实测]：若未来发现某调用方 `if (Play()!=NULL) Scenario::Random...` 模式（本轮未见），需白名单绕过。上线前用 U200/U800 回放对拍帧 CRC。

---

## 3. 落地规格

### 3.1 INI 键（建议节名 `[AudioThrottle]`，宿主 `ra2render.ini` 或独立 `audio_throttle.ini`）

> 【W3 勘误 · FREEZE_CANDIDATE §7 C25-C28 / Lead DC-02,DC-03】[W3-Lead临时裁决] 改前：建议节名 `[AudioThrottle]`，宿主 `ra2render.ini` 或独立 `audio_throttle.ini`；改后：依 DC-02 裁决宿主明确为 `ra2render.ini`（不建独立文件），采用 8 键 `[AudioThrottle]` 方案；依 DC-03 默认值取 0（键缺失即原版，安全侧），单位取「帧」，键名带 `_frames`；依据：Lead 临时裁决 DC-02、DC-03；分级：[推演]

```ini
[AudioThrottle]
; 总开关：0=原版洪泛（默认，便于对拍）；1=启用前置限频
Enable=0

; 每逻辑帧全局最大新发音数（建议 4~8；>8 基本无削峰收益）
MaxVoicePerFrame=6

; 同 SoundID 跨单位去重静默窗（毫秒；建议 60~120）
VoiceDedupMs=80

; 时间窗内同 SoundID 最多放行条数
MaxSamePerWindow=2

; 白名单：Priority >= 此值直接透传（3=HIGH, 4=CRITICAL）
WhitelistPriorityMin=3

; 白名单 Type 位掩码（0x10=GLOBAL, 0x80=PLAYER；0x90=EVA/UI）
WhitelistTypeMask=0x90

; 视口外弱音效剔除距离平方（逻辑坐标；0=关闭）
MaxAudibleDistSq=120000

; 是否同时拦截 PlayIndexAtPos 的请求节点分配（1=省 200 槽二池压力）
ThrottlePlayIndexAtPos=1
```

**默认 `Enable=0`**：与 `landing_pack` / 对拍基线一致，开箱零行为差。

### 3.2 钩点与字节

| 钩 | VA | 覆盖长度 | 原字节 | Hook | Trampoline |
|---|---|---|---|---|---|
| **A 主** PlayGlobal | `0x00750920` | 6 | `51 A0 AC 64 84 00` | `E9 rel32 90` | 执行 6 字节后 `jmp 0x750926` |
| **B 主** PlayAt | `0x007509E0` | 5 | `A0 AC 64 84 00` | `E9 rel32` | 执行 5 字节后 `jmp 0x7509E5` |
| **C 辅** PlayIndexAtPos | `0x00750E20` | 5 | `55 8B E9 56 57` | `E9 rel32` | 执行 5 字节后 `jmp 0x750E25` |

- 拦截判定为真时：**直接模仿原版失败出口**  
  - PlayGlobal：`xor eax,eax; ret 8`  
  - PlayAt / PlayIndexAtPos：`xor eax,eax; ret 4`  
  禁止裸 `ret`、禁止 `or eax,-1`（S18 已形式化否决）。
- 保寄存器：`EBX/ESI/EDI/EBP`；FPU 栈净空。
- `ThrottlePlayIndexAtPos=0` 时 C 钩不装或直通。

**判定顺序（ShouldAllow）**：
1. `Enable==0` → 放行  
2. `VoicesEnabled==0` → 丢（与原版一致）  
3. SoundID 越界 → 丢  
4. `Priority >= WhitelistPriorityMin` **或** `(Type & WhitelistTypeMask)!=0` **或** 带非空 `AudioController` 且正在播同音 → **透传**  
5. 逻辑帧预算：`CurrentFrame [0xA8ED84]` 变化则重置 `budget=MaxVoicePerFrame`；`budget<=0` → 丢  
6. `MaxAudibleDistSq>0` 且 `pCoords` 出视口且 `Priority<=1` → 丢  
7. 同 SoundID 窗口去重（`GetTickCount` 或帧钟均可；帧钟更利于回放稳定）  
8. 放行：`budget--`，更新时间戳  

### 3.3 回滚

| 级别 | 操作 | 影响 |
|---|---|---|
| **L0 软关** | `AudioThrottle.Enable=0` | 钩仍在，逻辑直通；可热更 |
| **L1 卸钩** | 恢复 A/B/C 原字节（上表），卸 trampoline | 与原版字节级等价 |
| **L2 禁区** | **禁止**回滚/修改 `0x406F70`、`0x4041D0`、`0x404D80`、`0x64DE3F`、EVA `0x752700/0x752480` | 破坏样本生命周期 / CRC / 战术语音 |

原字节备份必须在装钩前落盘（建议 `out/re_work/re_sprint/R_audio_limit/orig_bytes.bin`）。

### 3.4 与 CRT 池化的耦合 [实证]

| 路径 | 分配器 | 与 CRT 池关系 |
|---|---|---|
| Voice 池初始化 | `FixedPool::Init@0x4074D0` → `call 0x7C8E17`（`CRT::_new`）一次 `new(194408)` | **仅初始化**。194408 > SBH 阈值 1016 → `HeapAlloc`；`SizeToPoolIdx` 不命中 → 穿透原版 malloc |
| 请求节点池初始化 | 同上 @ `0x7510EF`（`new(200*(0x3C+8)+8)`） | 同上，仅初始化 |
| 运行时 Voice 分配 `0x405190` | **纯 Freelist**（`0x407520/0x407530`） | **完全不进 CRT** |
| 运行时请求节点 | Freelist `[0xB1D3A4]` | 不进 CRT |
| EVA / AudioStream | CRT 小对象（32B 节点等） | 可能落入 CRT 池 8 桶，但与限频正交 |

**耦合判定：低（运行时零共享）**。风险仅当：
1. CRT 池错误接管大块 `new`（`SizeToPoolIdx` 误匹配 194408）→ 必须保证大尺寸走穿透；
2. 将来把 FixedPool 改成逐槽 `new` → 会与 CRT 池/`Particle/Bullet/Anim` 桶争用，**禁止**。

限频**减少**运行时 Voice 创建，对 CRT 池是减压而非增压。

---

## 4. 风险表

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R1 | 误拦 EVA/UI/核弹警报 | 高 | 白名单 `Priority>=3` + `Type&0x90` + AudioController 短路；EVA 本就不走池 |
| R2 | 同声去重过狠，齐射/连环爆「缺声」 | 中 | `VoiceDedupMs` 60~120 可调；`MaxSamePerWindow>=2`；默认关 |
| R3 | 与 lockstep 分叉 | 高 | 只在 Play* 入口丢；不碰 `Scenario::Random` / 帧 CRC；上线前回放 CRC 对拍 |
| R4 | ABI 清栈错误 | 高 | 严格 `ret 8` / `ret 4`；trampoline 覆盖字节数与上表一致 |
| R5 | 只钩 PlayAt 漏请求节点 | 中 | `ThrottlePlayIndexAtPos=1` |
| R6 | 视口距离剔除误杀 | 低 | 仅 `Priority<=1`；`MaxAudibleDistSq=0` 可关 |
| R7 | 与 CRT 池大块分配互相干扰 | 低 | 见 §3.4；校验 `SizeToPoolIdx` 大尺寸穿透 |
| R8 | 强斩爆音被误认为限频无效 | 低 | 限频是**前置**；`0x404D80` 路径保留作兜底，不作为主策略 |

---

## 5. 验收（[待实测]）

| 场景 | 判据 |
|---|---|
| 50+ 步兵齐射 | 峰值活跃 Voice ≤ `MaxVoicePerFrame`× 窗口；无 300 池耗尽 |
| 大量死亡/爆炸 | 无 `0x404D80` 风暴；无阶跃爆音 |
| 核弹/EVA | 警报与 EVA 100% 出声 |
| U200/U800 回放 | 帧 CRC 与未打补丁一致（`AudioThrottle.Enable=1/0` 均测） |
| 开关切换 | `Enable=0` 听感/行为回到基线 |

---

## 6. 证据索引（工作区 `out/re_work/re_sprint/R_audio_limit/`）

| 文件 | 内容 |
|---|---|
| `verify_anchors.py` | 入口字节、300 槽、33ms 门、分配/强斩、CRT 耦合、调用点普查（9/9 OK） |
| `scan_triggers_rng.py` | 触发簇、0x62 动作体、RNG 近邻、NULL 处理抽样 |
| `scan_rng_order.py` | RNG 相对 Play 先后、PlayIndexAtPos 二池、调用点全表 |
| `scan_rng_identity.py` | 音频核心 RNG 的 `this`（全部 `0x886B88` Global）vs 帧 CRC（Scenario+0x218） |
| `claims.txt` | 三档证据清单 |

---

## 7. 与既有文档关系

- 复核并**确认** `audio_engine_deep_dive.md` 的 300 槽、入口 ABI、Limit 事后强斩、MinDelay 失效结论。  
- **收紧**其 §4 方案：补充 PlayIndexAtPos 二池、RNG 身份二分（Global vs Scenario）、CRT 运行时零共享。  
- **否定**在 `0x406F70`/`0x4041D0` 做限频（`audio_input_hotspots.md` §1.4 原判维持）。  
- 与 `trigger_determinism_deep_dive.md` §2.2 对齐：动作 0x62 的 `RandomRanged` 属同步流，但发生在 Play **之前**，入口短路不改其次数。
