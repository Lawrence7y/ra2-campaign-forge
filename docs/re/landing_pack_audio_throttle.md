# ZCode 落地卡 · Audio Throttle（Play* 入口前置限频）

> **卡号**：`ZC-AUDIO-THROT` · **优先级**：P1（洪泛削峰 / 爆音治理；非 lockstep 致命面）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-AUDIO-LIMIT 静态定谳）  
> **上游**：`docs/re/audio_throttle_landing.md`（R-AUDIO-LIMIT）· 复算脚本 `out/re_work/re_sprint/R_audio_limit/` · 本卡工作区 `out/re_work/re_sprint/R_audio_card/`  
> **格式对齐**：`docs/re/landing_pack_gap_p21.md`（ZC-GAP-P21）  
> **本卡范围**：**仅入口限频**（PlayGlobal / PlayAt / PlayIndexAtPos 前置丢弃 + INI + 遥测）。原生 `Limit` 事后强斩 `0x404D80`、33ms 节流 `0x406F70`、样本生命周期 **本卡不做**。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e…` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

在 `VocClass::PlayGlobal@0x00750920`、`PlayAt@0x007509E0`、`PlayIndexAtPos@0x00750E20` **入口前置**装 trampoline，超预算/去重命中时**模仿原版失败出口**返回 NULL（`xor eax,eax; ret 8/4`）；**不碰** EVA `0x752700`、**不碰** `0x64DE3F`；默认 `[AudioThrottle] Enable=0` 零行为差。

---

## 1. 执行表（字节级 + 插入方式）

### 1.1 三钩一览

| 项 | **A 主钩** | **B 主钩** | **C 辅钩** |
|---|---|---|---|
| **步骤 ID** | `AT-A` | `AT-B` | `AT-C` |
| **函数** | `VocClass::PlayGlobal` | `VocClass::PlayAt` | `VocClass::PlayIndexAtPos` |
| **VA** | `0x00750920` | `0x007509E0` | `0x00750E20` |
| **文件偏移** | `0x00350920` | `0x003509E0` | `0x00350E20` |
| **节** | `.text` | `.text` | `.text` |
| **覆盖长度** | **6** | **5** | **5** |
| **原字节** | `51 A0 AC 64 84 00` | `A0 AC 64 84 00` | `55 8B E9 56 57` |
| **原指令** | `push ecx; mov al,[0x8464AC]` | `mov al,[0x8464AC]` | `push ebp; mov ebp,ecx; push esi; push edi` |
| **失败出口（模仿）** | `0x75092E: 33 C0 59 C2 08 00` | `0x7509EC: 33 C0 5B C2 04 00` | `0x750E2B: 33 C0 … C2 04 00` |
| **ABI** | `__fastcall`：`ECX=SoundID, EDX=Panning`；栈 `[ESP+4]=float Volume, [ESP+8]=AudioController*`；**`ret 8`** | `__fastcall`：`ECX=SoundID, EDX=CoordStruct*`；栈 `[ESP+4]=AudioController*`；**`ret 4`** | `__fastcall`：`ECX=n, EDX=CoordStruct*`；栈 `a3`；**`ret 4`** |
| **丢弃出口** | `xor eax,eax; ret 8` | `xor eax,eax; ret 4` | `xor eax,eax; ret 4` |
| **装否** | `Enable=1` 必装 | `Enable=1` 必装 | `ThrottlePlayIndexAtPos=1` 才装（默认 1） |

> **直呼面（Capstone rel32 全文）**[实证]：`PlayGlobal` 116 · `PlayAt` 97 · `PlayIndexAtPos` 18 · `EVA::QueueVoice` 77（**禁钩**）· `VoiceAlloc 0x405190` 4。  
> **二池**[实证]：`PlayIndexAtPos` 先 Pop 200 槽请求节点（`[0xB1D3A4]`）再 `call PlayAt@0x750E82`——**只钩 B 仍耗节点**，故默认双钩 B+C。

### 1.2 插入方式（二选一，本卡推荐）

| 方案 | 描述 | 评价 |
|---|---|---|
| **T. trampoline（推荐）** | 覆盖 6/5/5 字节为 `E9 rel32`（+`90` 补 6B 槽），跳入 DLL 内 `Hook_*`；`Hook_*` 内判定后放行则执行原字节片段再 `jmp` 回原入口+覆盖长 | **主推**。可承载 ShouldAllow 状态机、INI、遥测；L0 软关热更 |
| **D. DLL 内 hook（虚表/IAT 类）** | 本卡**不适用**：三入口非虚表槽、无 IAT 间接；仅能靠 inline | 否决 |
| **E. 外部补丁器等长替换** | 无判定逻辑，只能常丢/常放 | **不推荐**（无削峰收益）；若强行做，仅限「常放」无意义 |

**T 方案细节**：

| 钩 | 覆盖 | 指令槽 | trampoline 内 | 回跳 |
|---|---|---|---|---|
| A | 6B | `E9 rel32 90` | 执行原 `51 A0 AC 64 84 00`（push ecx; mov al,…） | `jmp 0x750926` |
| B | 5B | `E9 rel32` | 执行原 `A0 AC 64 84 00` | `jmp 0x7509E5` |
| C | 5B | `E9 rel32` | 执行原 `55 8B E9 56 57` | `jmp 0x750E25` |

- **保寄存器**：`EBX/ESI/EDI/EBP`；FPU 栈净空；`ECX/EDX` 在判定前压栈、放行前弹回。  
- **禁止**裸 `ret`、**禁止** `or eax,-1`（S18 已形式化否决；调用方把返回值当 `VocClass*` 解引用）。  
- **必须** `xor eax,eax` + 对应 `ret 8`/`ret 4`，与原失败出口字节级等价。  
- trampoline 代码页 `PAGE_EXECUTE_READWRITE`，卸载时还原原字节 + 释放跳板。

### 1.3 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | `0x750920` 首 6B | `51 A0 AC 64 84 00` | 若已是 `E9`/跳板：报告「已打」并停手上报；其它：**拒绝** |
| G0.3 | `0x7509E0` 首 5B | `A0 AC 64 84 00` | 同上（`E9` 已打） |
| G0.4 | `0x750E20` 首 5B | `55 8B E9 56 57` | 同上 |
| G0.5 | 失败出口窗 | `0x75092E=33 C0 59 C2 08 00`；`0x7509EC=33 C0 5B C2 04 00` | 拒绝 |
| G0.6 | 开关键 `[AudioThrottle] Enable` | 显式 `1` 才装钩；默认 **0=不装** | 零行为变化 |
| G0.7 | `EVA::QueueVoice@0x752700` 首 6B | `53 57 8B F9 8B DA` **原样** | 有任何改写 → **拒绝并回滚全部** |
| G0.8 | `0x64DE3F` 窗（帧 CRC RNG） | **零接触**；装前后字节一致 | 有任何写 → **拒绝并回滚** |

**Q1 真机首字节（安装前）**：读 `0x750920` / `0x7509E0` / `0x750E20` 首字节 → 原版字节=未打；`E9`=已有外部补丁（**停手上报，禁止覆盖未知安装者**）。

---

## 2. 参数（INI，宿主 `ra2render.ini` 或 `audio_throttle.ini`）

### 2.1 节名 `[AudioThrottle]`

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

> **键名口径**：本卡**唯一**采用 R-AUDIO-LIMIT 规格键名 `[AudioThrottle] Enable`。旧文 `landing_pack_crt_audio_particle.md` 的 `[Audio] EnableAudioThrottling` / `net_sync_desync_map.md` 的 `EnableAudioThrottling` **视为别名废弃**，执行方以本表为准。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-AUDIO】[W3-Lead临时裁决] 改前：[Audio] EnableAudioThrottling；改后：[AudioThrottle] ; DC-02 裁决口径: 8 键体系，宿主 ra2render.ini Enable=0 MaxVoicePerFrame=6 VoiceDedupMs=80；依据：docs/re/dispatch/W3_20261001_Lead_DECISION_AND_BOARD.md:41; docs/re/audio_throttle_landing.md:19, 139-147；分级：P0

### 2.2 判定顺序（ShouldAllow）——**必须严格此序**

1. `Enable==0` → **放行**（L0 软关直通）  
2. `VoicesEnabled [0x8464AC]==0` → **丢**（与原版一致）  
3. SoundID 越界（`Array->Items [0xB1D37C]` / `Count [0xB1D388]`）→ **丢**  
4. **白名单透传**（任一命中即放行，不扣预算）：  
   - `Priority [+0x40] >= WhitelistPriorityMin`  
   - **或** `(Type & WhitelistTypeMask)!=0`  
   - **或** 带非空 `AudioController` 且正在播同音  
5. 逻辑帧预算：`CurrentFrame [0xA8ED84]` 变化则重置 `budget=MaxVoicePerFrame`；`budget<=0` → **丢**  
6. `MaxAudibleDistSq>0` 且 `pCoords` 出视口且 `Priority<=1` → **丢**  
7. 同 SoundID 窗口去重（**帧钟**优先于 `GetTickCount`，利于回放稳定）：`MaxSamePerWindow` / `VoiceDedupMs`  
8. **放行**：`budget--`，更新时间戳/计数  

### 2.3 禁限频 / 禁靠近（红线，执行方必读）

| 目标 | VA | 红线 | 理由 |
|---|---|---|---|
| **EVA::QueueVoice** | `0x00752700`（enqueue `0x752480`） | **禁限频 / 禁钩 / 禁改** | 独立 `AudioStream`，不走 300 槽池；战术语音 100% 出声 |
| **帧 CRC RNG** | `0x0064DE3F` | **禁靠近 / 禁读改写** | `lea ecx,[Scenario+0x218]` 同步流；改一字节即分叉 CRC |
| AudioFrameUpdate | `0x00406F70` | 禁在此截流 | 33ms 门 + 生命周期；截流 = 爆音/错乱 |
| 样本衰减 / Limit 斩 | `0x004041D0` / `0x00404D80` | 保留兜底，不作主策略 | 事后强斩 → DAC 阶跃爆音 |
| 触发器动作整段 | `0x6DE80F→0x6DE831`、`0x6E17DE→0x6E181B` | **禁跳过整段** | 含同步 `Scenario::Random`；见 §3 |

---

## 3. 确定性门（lockstep 安全验收）

### 3.1 为什么入口丢弃安全 [实证 + 推演]

| # | 事实 | 级别 |
|---|---|---|
| 1 | `PlayGlobal` / `PlayAt` / `PlayIndexAtPos` / `VoiceAlloc` **函数体内 0 次** `Random/RandomRanged` | [实证] |
| 2 | 音频生命周期 RNG（样本/FShift/VShift/MinDelay）**全部** `Randomizer::Global@0x886B88`（**非同步**） | [实证] |
| 3 | 帧 CRC `0x64DE3F` 用 `ScenarioClass::Random`（`Scenario+0x218`，**同步**），**不在**音频路径 | [实证] |
| 4 | 触发器 `0x62` / `PlaySoundEffect` 的同步 RNG **在 Play 调用之前**消费；入口返回 NULL **不跳过**该次 `Scenario::Random` | [实证] |
| 5 | 抽样 12 处 PlayAt 调用者：**无人**以 `eax` 门控后续同步 RNG；NULL 是原版池耗尽既有契约 | [实证] |

### 3.2 短路位置裁决表

| 短路位置 | lockstep 安全？ | 执行方动作 |
|---|---|---|
| **Play* 入口前置拦截，`return NULL`** | **安全** | **本卡唯一允许** |
| 整段跳过触发器动作（含 `0x62` 的 `RandomRanged`） | **不安全** | **禁止**（掉同步 RNG） |
| 在 `0x4041D0` / `0x406F70` 内截流改生命周期 | **不安全/有害** | **禁止** |
| 改 `0x64DE3F` 帧 CRC RNG | **严禁** | **禁止**（直接分叉 CRC） |

### 3.3 确定性验收门（D-gate，A5 前置）

| ID | 检查 | 通过条件 |
|---|---|---|
| **D1** | 静态：限频路径 0 次写 `Scenario::Random` / `0x64DE3F` 窗 | 装前后该窗字节一致 |
| **D2** | 静态：未改任何触发器动作体；`0x6DE80F`/`0x6E17DE` 的 `RandomRanged` 调用仍在 | 反汇编对照 |
| **D3** | 动态：U200/U800 回放帧 CRC，`Enable=1` vs `Enable=0` vs 未打补丁 | **三者一致**（任一不一致 → FAIL，禁报成功） |
| **D4** | 动态：触发器 `PlaySoundEffectRandom (0x62)` 局，同步 RNG 消费次数与基线一致 | 计数相等（入口丢弃不改次数） |

> **残余风险**[待实测]：若未来发现某调用方 `if (Play()!=NULL) Scenario::Random...` 模式（本轮 12 处抽样未见），需白名单绕过。上线前必须过 D3。

---

## 4. 验收 A1–A5（真机；ZCode 填回执）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **A1** | 默认配置启动（`Enable=0`） | 三处字节仍为原版；无崩溃；`AudioThrottle=off` | 首字节截图/日志 |
| **A2** | `Enable=1` 启动 | 三入口为 `E9` 跳板；失败出口窗未变；`EVA 0x752700`/`0x64DE3F` 未变；日志 `AudioThrottle=on` | 字节前后对照 |
| **A3** | 50+ 步兵齐射 / 大量死亡爆炸 | **同帧新发音 ≤ `MaxVoicePerFrame`**；峰值活跃 Voice 不爆 300 池；无 `0x404D80` 强斩风暴；无阶跃爆音 | **同帧语音数曲线/计数器**（见下「没崩≠成功」） |
| **A4** | 核弹警报 / EVA 战术语音 / UI 关键音 | **100% 出声**（白名单生效）；`QueueVoice` 未被拦截 | 听感 + `evaPassthrough` 计数 |
| **A5** | U200/U800 回放 CRC 对拍 + 开关往返 | `Enable=1/0` 与未打补丁 **帧 CRC 一致**；`Enable=0` 听感回到基线 | `SYNC*.TXT` 空 + CRC 序列文件 |

### 「没崩≠成功」——A3 强制证据

**禁止把「没崩」当成功。** A3 必须同时给出：

1. **同帧语音数证据**：遥测 `soundsTriggered` / `soundsThrottled` 按帧采样（或断点 `0x750920` 计数），证明峰值帧新发音 **≤ `MaxVoicePerFrame`**；  
2. **池压力证据**：`[0x87E28C]`（当前活跃）峰值 < 300，无 NULL 风暴；  
3. **听感证据**：无爆音/无整段静音（关键音仍在）；  
4. **对照**：同场景 `Enable=0` 峰值明显更高（证明限频真在生效，而非场景本身不爆）。

---

## 5. 回滚 / MP（对照 R-MP-GATE）

### 5.1 回滚三级

| 级别 | 操作 | 影响 |
|---|---|---|
| **L0 软关** | `[AudioThrottle] Enable=0` | 钩仍在，逻辑直通；可热更；**首选** |
| **L1 卸钩** | 恢复 A/B/C 原字节（§1.1），释放 trampoline | 与原版字节级等价 |
| **L2 禁区** | **禁止**回滚/修改 `0x406F70`、`0x4041D0`、`0x404D80`、`0x64DE3F`、EVA `0x752700/0x752480` | 破坏生命周期 / CRC / 战术语音 |

- 原字节备份**装钩前落盘**：`out/re_work/re_sprint/R_audio_card/orig_bytes.bin`（6+5+5=16B）。  
- 若走补丁器：提供 `--uninstall-audio-throttle` 仅还原三处。

### 5.2 MP / 联机（R-MP-GATE 口径）

| 项 | 结论 | 依据 |
|---|---|---|
| **混端 DESYNC** | **SAFE**：Play* 入口丢弃 **0 同步 RNG**；纯声道池调度 | `net_sync_desync_map.md` **D-AUDIO**；`mp_gate_residual_deep_dive.md` §4 |
| **可否联机保留** | **可**（L-8：纯表现层，可不降级） | R-MP-GATE L-8 |
| **是否强制 MpActive 关** | **不强制**。若要求**观感一致**（两端听到相同削峰），可选照 VXL G0.5「MpActive 不装」模式 | 可选，非必须 |
| **握手字段** | **不新增**（政策既定） | R-MP-GATE：不加握手键 |
| **启动日志** | 照 L-7：打 `AudioThrottle=on\|off\|forced-off-mp` 一行（若做观感门） | L-7 |
| **默认** | `Enable=0` —— 发行/正式联机零副作用 | 与 landing_pack 对拍基线一致 |

> **混端可共存**：一端限频一端原版 = 本地少放音，**无帧 CRC 分叉**；观感可不一致，不构成 VIOLATION。

---

## 6. 遥测（只读计数，禁热路径膨胀）

| 计数器 | 含义 |
|---|---|
| `audioThrottleInstalled` | 0/1 |
| `soundsTriggered` | 实际放行数 |
| `soundsThrottled` | 丢弃数（预算/去重/距离） |
| `evaPassthrough` | 白名单透传次数（EVA/UI/高优先） |
| `peakVoicesThisSession` | 活跃 Voice 峰值（读 `[0x87E290]` 或自算） |

---

## 7. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | 误拦 EVA/UI/核弹警报 | 高 | 白名单 `Priority>=3` + `Type&0x90` + AudioController 短路；EVA 本就不走池 |
| R-2 | 同声去重过狠，齐射/连环爆「缺声」 | 中 | `VoiceDedupMs` 60~120 可调；`MaxSamePerWindow>=2`；默认关 |
| R-3 | 与 lockstep 分叉 | 高 | 只在 Play* 入口丢；不碰 `Scenario::Random` / `0x64DE3F`；过 D3 |
| R-4 | ABI 清栈错误 | 高 | 严格 `ret 8`/`ret 4`；禁裸 `ret`；trampoline 覆盖长与 §1.1 一致 |
| R-5 | 只钩 PlayAt 漏 200 槽请求节点 | 中 | `ThrottlePlayIndexAtPos=1` |
| R-6 | 视口距离剔除误杀 | 低 | 仅 `Priority<=1`；`MaxAudibleDistSq=0` 可关 |
| R-7 | 覆盖未知外部补丁 | 高 | G0.2–G0.4 / Q1 首字节门禁；已打则停手上报 |
| R-8 | 把「没崩」当成功 | 高 | A3 强制同帧语音数证据（§4） |
| R-9 | 键名混乱（`EnableAudioThrottling` 旧键） | 低 | 唯一 `[AudioThrottle] Enable`；旧键废弃 |

---

## 8. 交付回执（填完交回）

```
ZC-AUDIO-THROT RESULT
- build/md5(gamemd):
- install path: (ra2render trampoline | external patcher | ...)
- AudioThrottle.Enable:
- MaxVoicePerFrame / VoiceDedupMs / ThrottlePlayIndexAtPos:
- G0.1–G0.8: PASS/FAIL
- Q1 first byte before @0x750920 / 0x7509E0 / 0x750E20:
- bytes after (A/B/C):
- EVA 0x752700 unchanged: y/n
- 0x64DE3F window unchanged: y/n
- D1–D4: PASS/FAIL
- A1..A5: (each PASS/FAIL + evidence path)
- A3 same-frame voice peak (Enable=1 vs 0):
- except.txt: empty|path
- rollback tested (L0/L1): y/n
- MP: (single | mp-preserved | mp-forced-off) + CRC note
```

---

## 9. 不在本卡

- 原生 `Limit` 字段启用 / `MinDelay` 修复 / `0x4042EA` 强斩策略改造  
- `AudioFrameUpdate 0x406F70` 33ms 门重写  
- CRT 池化（`crt_pool_landing.md` / `landing_pack_crt_audio_particle.md` 模块一）——独立卡  
- Particle / VXL 绘制剔除——独立卡  
- 台账/看板登记 —— 由 Lead 收口  

---

*依据：R-AUDIO-LIMIT 深潜 §1–§5 + `out/re_work/re_sprint/R_audio_limit/claims.txt`（E01–E18 / D01–D05 / V01–V04）；三入口原字节 3/3 MATCH；入口丢弃 = 唯一 lockstep 安全短路位；EVA / 帧 CRC 双红线。*
