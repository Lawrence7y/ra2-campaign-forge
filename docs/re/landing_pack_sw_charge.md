# ZCode 落地卡 · SW 充能冗余二次 call 删除 + Cameo 限频（可选）

> **卡号**：`ZC-SW-CHARGE` · **优先级**：P2（零风险微优化；充能链本身**无 bug、无需修复**）  
> **执行方**：ZCode（真机/补丁安装唯一写者）· **起草**：MiMo（R-SW-CHARGE 静态定谳）  
> **上游**：`docs/re/sw_charge_state_deep_dive.md`（T16）· 复算脚本 `out/re_work/re_sprint/R_sw_charge/` · 本卡工作区 `out/re_work/re_sprint/R_sw_card/`  
> **格式对齐**：`docs/re/landing_pack_gap_p21.md`（ZC-GAP-P21）  
> **本卡范围**：**主项 L-SW-1 仅一处 7B NOP**（语义不变）；**附录 L-SW-2** Cameo 读缓存限频为可选（须真机确认 `frame=-1`）。禁区/验收/回滚/MP 见 §5–§7。  
> **证据基线**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · size 4,825,360 B · ImageBase `0x00400000` · `file_off = VA − 0x00400000`
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 一句话

把 `HasChargeProgressed` 慢路径里对纯函数 `GetCameoChargeState` 的**冗余二次 call**（`0x006CBE88` 起 **7 字节**）换成 **`90×7`**，复用第一次结果 `eax`——**零语义变化、零 CRC 影响**；其余充能链（Timer / `IsCharged` / `ChargeDrainState` / 公式）**一字不动**。附录 L-SW-2 可选把侧栏 Cameo 绘点改为读 `+0x78` 缓存（纯 UI）。

---

## 1. 主项 L-SW-1 执行表（字节级，等长替换）

| 项 | 值 |
|---|---|
| **步骤 ID** | `L-SW-1` |
| **VA** | `0x006CBE88` |
| **文件偏移** | `0x002CBE88` |
| **节** | `.text` |
| **函数** | `SuperClass::HasChargeProgressed` @ `0x006CBCA0`（慢路径 `remaining != 0`） |
| **原字节（7B）** | `8B CE E8 51 00 00 00` |
| **原指令** | `mov ecx, esi` ; `call 0x6CBEE0`（第二次 `GetCameoChargeState`，结果丢弃） |
| **新字节（7B）** | `90 90 90 90 90 90 90` |
| **新指令** | `nop ×7` |
| **改动长度** | **必须 7==7 等长**（禁 trampoline / 禁动 `.detour` / 禁改邻接指令） |

### 1.1 上下文窗（安装前后自检用）

| 偏移相对 VA | 原字节 | 说明 |
|---|---|---|
| `0x6CBE7C` | `8B CE` | `mov ecx, esi` —— **第一次** `GetCameoChargeState` 入参准备 |
| `0x6CBE7E` | `E8 5D 00 00 00` | `call 0x6CBEE0` → `eax = e1`（**保留，勿动**） |
| `0x6CBE83` | `3B 46 78` | `cmp eax, [esi+0x78]` —— 脏检测；**不改 `eax`** |
| `0x6CBE86` | `74 15` | `je 0x6CBE9D` —— 无变化 → `return false`；**不改 `eax`** |
| **`0x6CBE88`** | **`8B CE E8 51 00 00 00`** | **★ 本卡替换点**（冗余二次 call） |
| `0x6CBE8F` | `89 46 78` | `mov [esi+0x78], eax` —— 写回 `CameoChargeState`；**用的是 `eax`** |

**为什么可以删**：`GetCameoChargeState 0x6CBEE0` 是**纯读**（不写任何状态，见深潜 §3.2）；`cmp`/`je` 均不改 `eax`。第二次 call 结果必然等于第一次，写回 `+0x78` 的值不变。NOP 后 `eax` 仍是 `e1`，`0x6CBE8F` 语义完全等价。[实证]

### 1.2 语义边界（只许删这一件事）

| 对象 | 动作 | 本卡 |
|---|---|---|
| 第二次 `mov ecx,esi; call 0x6CBEE0` @ `0x6CBE88` | 冗余计算 | **删除（7×NOP）** |
| 第一次 call @ `0x6CBE7E` + `cmp/je` | 脏检测 | **保留** |
| `mov [esi+0x78], eax` @ `0x6CBE8F` | 缓存回写 | **保留**（写入值不变） |
| `GetCameoChargeState 0x6CBEE0` 本体公式 | 显示映射 | **禁止改**（§5） |
| `HasChargeProgressed` 其余副作用 | 逻辑推进 | **禁止跳/改**（§5） |
| `RechargeTimer` / `IsCharged` / `ChargeDrainState` | 状态机 | **禁止改**（§5） |

---

## 2. 安装前置（全部 PASS 才允许写）

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | 目标文件 SHA-256 | `73201CC0…F67476` | **拒绝安装** |
| G0.2 | `VA 0x6CBE88` 文件偏移 `0x2CBE88` 首 7B | `8B CE E8 51 00 00 00` | 若已是 `90×7`：报告「已打」并跳过；其它：**拒绝** |
| G0.3 | 窗前 `0x6CBE86` = `74 15` | MATCH | 拒绝 |
| G0.4 | 窗后 `0x6CBE8F` = `89 46 78` | MATCH | 拒绝 |
| G0.5 | 首次 call `0x6CBE7E` = `E8 5D 00 00 00` | MATCH | 拒绝 |
| G0.6 | `.text` 节可写性 / 映像基址 | PE32 / base `0x400000` | 拒绝 |
| G0.7 | 开关键 `EnableSWChargeOpt` | 显式 `1` 才安装 | 默认 **0=不装**（零行为变化） |
| G0.8 | 禁区字节窗（§5 表）装前后一致 | 逐点 MATCH | **拒绝并回滚** |

**Q1 真机首字节（安装前）**：断点/读 `0x6CBE88` 首字节 → `8B`=未打 / `90`=已有外部补丁（此时**停手并上报**，禁止覆盖未知安装者）。

---

## 3. 开关 · 遥测 · 回滚

### 3.1 开关（ini，与现有门控风格一致）

| 键 | 默认 | 语义 |
|---|---|---|
| `EnableSWChargeOpt` | **`0`** | `1` 时安装 L-SW-1；`0` 时不碰 `.text` |
| `EnableSWCameoCache` | **`0`** | `1` 时才考虑附录 L-SW-2；**默认不做**；键名勿与 L-SW-1 混用 |

**联机**：L-SW-1 **零语义变化**，`MpActive` 下**可安装、可保留**（无需强制关）；启动日志打印 `SWChargeOpt=on|off`。若发行策略要求「联机二进制与原版字节全同」，可选照 VXL G0.5 做 `MpActive` 不装——**非必须**。

### 3.2 遥测（只读计数，禁止热路径膨胀）

| 计数器 | 含义 |
|---|---|
| `swChargeOptInstalled` | 0/1 |
| `swChargeRedundantCallsSkipped` | 可选：命中慢路径次数（仅诊断档；也可省） |

### 3.3 回滚

1. **软**：`EnableSWChargeOpt=0` + 重启游戏/重载 DLL（安装态在 init 决定，参考 `LoadConfig` 仅 init 读一次的教训）。  
2. **硬**：备份 7B 原字节 `s_origLSW1[7] = 8B CE E8 51 00 00 00` → `memcpy` 还原。  
3. **卸载工具**：若走补丁器，提供 `--uninstall-l-sw-1` 仅还原该 7B。  
4. **原字节备份落盘**：`out/re_work/re_sprint/R_sw_card/orig_bytes.bin`（7B；若做 L-SW-2 再 +5B）。

---

## 4. 真机验收用例（A-系列，最小 5 条）

| ID | 步骤 | 期望 | 证据要求 |
|---|---|---|---|
| **A1** | 默认配置启动（`EnableSWChargeOpt=0`） | `0x6CBE88` 仍为原 7B；无崩溃；日志 `SWChargeOpt=off` | 首字节/日志 |
| **A2** | `EnableSWChargeOpt=1` 启动 | `0x6CBE88`=`90×7`；`0x6CBE86/0x6CBE8F/0x6CBE7E` 未变；禁区窗一致；日志 `SWChargeOpt=on` | 字节前后对照 |
| **A3** | 建超武建筑，起充 → 观察侧栏 Cameo 覆盖帧推进 → 到点 | **充能仍完整推进**：Cameo 帧从 `0x35` 倒扣到 `0`，到点变 `0x36`；`IsCharged` 翻转帧与未打补丁一致（同种子/同步回放对拍） | **到点帧号**（不是「没崩」）；对照未打补丁 |
| **A4** | A3 后存 `.SAV` → 读档 | 充能进度/`IsCharged`/Cameo 保持；`except.txt` 空 | 存读档截图/日志 |
| **A5** | 双端同构建对拍（或 U-回放 CRC） | `Enable=1` vs `0` vs 未打补丁 **帧 CRC / Checksum v[13] 一致** | `SYNC*.TXT` 空 + CRC 序列 |

**禁止把「没崩」当成功**：A3 必须有「充能到点帧号不变」的证据（断点 `0x6CBE6F` 写 `ReadinessFrame`，或回放帧号对拍）。

---

## 5. 禁区（红线 · 执行方必读 · 违者即 DESYNC/坏档）

> 来源：深潜 §2.2 副作用清单、§5.2 CRC 表、§6.3 纯逆向收口范围。以下对象**一律禁改、禁跳、禁重排**。

### 5.1 `HasChargeProgressed 0x6CBCA0` —— 副作用非幂等，**禁跳帧 / 禁旁路**

每逻辑帧由 `HouseClass::Update 0x4F8440` @ `0x4F8E4A` 驱动，携带 **7 项副作用**（**非幂等**，跳一帧就错）：

| # | 副作用 | 字节锚点 |
|---|---|---|
| 1 | `SpecialSoundDuration(+0x50)--` | `0x6CBCAF: 48 / 89 46 50` |
| 2 | `IsCharged(+0x6F)` 翻转 | `0x6CBDCC` / `0x6CBDBA` |
| 3 | `ChargeDrainState(+0x7C)` 转移 | `0x6CBDB7` / `0x6CBD86` |
| 4 | `RechargeTimer` 重装（drain 收束） | `0x6CBDA1/07/0A` |
| 5 | `CameoChargeState(+0x78)` 回写 | `0x6CBE8F` |
| 6 | `ReadinessFrame(+0x74)` 写入 | `0x6CBE6F` |
| 7 | `isPlayer` 时 EVA/音效 | `0x6CBDE6` 跳表 |

- **禁止**跳过 `HasChargeProgressed` 调用、禁止按视觉帧节流它、禁止把它改成纯查询。  
- **允许**仅删 §1 那次冗余二次 call（结果复用，副作用清单不减项）。  
- 死代码 `0x4F9370`（0 call / 0 imm32）**不要「顺手修」**——它不可达，动它无收益且引入风险。

### 5.2 禁改充能公式 / 推进规则

| 对象 | VA | 红线 | 理由 |
|---|---|---|---|
| **`GetCameoChargeState` 公式本体** | `0x6CBEE0`（`54.0` 常数 `0x7F4048`） | **禁改公式 / 禁改常数 / 禁改 clamp `0..0x35/0x36`** | 返回值经 `+0x78` 进 `CalculateChecksum v[13]=0x6CE020`；改公式 = 分叉 Checksum |
| **`RechargeTimer` 推进 / `IsCharged` 翻转帧** | `0x6CBD5D` 比较链 | **禁改** | 间接进帧 CRC + Checksum |
| `SetRechargeTime` / `ResetRechargeTime` | `0x6CC280` / `0x6CC290` | **禁止单端调用**（仅 TAction 触发器、须全端同帧） | 写 `CustomChargeTime+0x24` |
| `SetCharge` / `Grant` / `SetOnHold` 计时折叠 | `0x6CC1E0` / `0x6CB560` / `0x6CB4D0` | **禁改折叠语义**（`Start==-1 ⇒ Duration` 即剩余） | 全链共用同一比较 |
| `CanFire` 判定 | `0x6CC360` | **禁改** | 与 `ChargeDrainState` FSM 自洽 |
| `IronCurtainCharged` / `ChronoSphereCharged` | `0x41F0D0` / `0x41F180` | **禁改** | AITrigger 判决；同吃 Timer 折叠 |

### 5.3 允许碰 / 禁止碰（CRC 判定速查，承接深潜 §5.2）

| 改动对象 | 帧 CRC `0x64DAB0` | Checksum v[13] `0x6CE020` | 判定 |
|---|---|---|---|
| 侧栏 Cameo 绘制 / 跳帧 / 限频（**仅 UI 调用点**） | 否 | 否 | **安全** |
| `ShouldDrawProgress` / `ShouldFlashTab` / EVA | 否 | 否 | **安全** |
| **L-SW-1**（删冗余二次 call，写回值不变） | 否 | 否 | **安全** |
| L-SW-2（UI 调用点读 `+0x78` 缓存） | 否 | 否 | **安全**（须先过 `frame=-1` 真机确认） |
| `GetCameoChargeState` **本体公式** | 否 | **是**（经 `+0x78`） | **禁止** |
| `RechargeTimer` 推进 / `IsCharged` 翻转帧 | 间接是 | **是** | **禁止** |
| 跳过 `HasChargeProgressed` | 间接是 | **是** | **禁止** |

---

## 6. 附录 L-SW-2 · 侧栏 Cameo 重绘限频（可选 · 须真机确认）

> **状态**：**可选，默认不做**。深潜建议「若只做一个，优先 L-SW-1」。本附录给出字节规格与门槛；**未过 Q2 真机确认前禁止安装**。

### 6.1 规格

| 项 | 值 |
|---|---|
| **步骤 ID** | `L-SW-2`（附录） |
| **VA** | `0x006A99AC` |
| **文件偏移** | `0x002A99AC` |
| **函数** | 侧栏 Cameo 绘点（`0x6A9966-0x6A99B1` 序列内） |
| **原字节（5B）** | `E8 2F 25 02 00` |
| **原指令** | `call 0x6CBEE0`（每视觉帧重算 `GetCameoChargeState`） |
| **新字节 A（5B）** | `8B 41 78 90 90` |
| **新指令 A** | `mov eax, [ecx+0x78]` ; `nop` ; `nop`（读逻辑侧缓存） |
| **改动长度** | **必须 5==5 等长** |
| **影响面** | **仅显示**；`GetCameoChargeState` 本体不动，`+0x78` 写侧不动；UI 从不进 CRC |

上下文窗：

```
0x006A99A3  8B 91 58 02 00 00   mov  edx, [ecx+0x258]   ; Supers.Items（保留）
0x006A99A9  8B 0C BA             mov  ecx, [edx+edi*4]   ; p = Items[i]（保留）
0x006A99AC  E8 2F 25 02 00       call 0x6CBEE0           ; ★ 替换点
0x006A99B1  89 44 24 38          mov  [esp+0x38], eax    ; frame 送往绘制（保留）
```

### 6.2 门槛：`frame = -1` 真机确认（**Q2，不过则放弃 L-SW-2**）

逻辑侧 `+0x78` 初值 = `-1`（ctor `0x6CAFD1`）。Grant 后首个逻辑帧 `HasChargeProgressed` 尚未回写前，补丁 A 会把 `0xFFFFFFFF` 当作 cameo 帧号送入绘制器。

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| **Q2.1** | 真机/调试器确认绘制器 `0x4AED70` 对 `frame=-1` 的行为 | 不崩溃、不花屏、不读越界 SHP 帧（最好能 clamp 或跳绘） | **放弃 L-SW-2**，维持原状 |
| **Q2.2** | Grant 后首视觉帧截图 | 无异常帧/无垃圾像素 | 放弃 |
| **Q2.3** | 若 Q2.1 不容错 | 改用补丁 B（见下）或**整体放弃** | 禁止硬上补丁 A |

**补丁 B（稳妥，6 字节，需向后借 1 字节或插入短跳）** —— 若不可借字节则**放弃**，维持原状：

```
; 期望序列（示意，需在更大空隙重排）：
mov  eax, [ecx+0x78]        ; 8B 41 78
cmp  eax, -1                ; 83 F8 FF
jne  short use_cached
call 0x6CBEE0               ; E8 .. (仅 cache 未就绪时回退)
use_cached:
```

### 6.3 L-SW-2 独立验收（仅当 Q2 通过后）

| ID | 步骤 | 期望 |
|---|---|---|
| **B1** | `EnableSWCameoCache=1` 启动 | `0x6A99AC`=`8B 41 78 90 90`；`0x6A99A3/A9/B1` 未变 |
| **B2** | 起充全程目视 | Cameo 推进观感与原版一致（倒扣覆盖）；到点 `0x36` |
| **B3** | Grant 后首帧 | **无花屏/无越界**（Q2 证据复用） |
| **B4** | A5 同款 CRC 对拍 | UI 改动 **不进** CRC；三者一致 |

---

## 7. MP / 确定性（充能零 RNG · lockstep 安全）

### 7.1 为什么安全 [实证]

| # | 事实 | 级别 |
|---|---|---|
| 1 | 充能链 6 个关键函数（`HasChargeProgressed` / `GetCameoChargeState` / `Grant` / `CanFire` / `IronCurtainCharged` / `ChronoSphereCharged`）静态扫描 **零 RNG、零 `timeGetTime`** | [实证] 深潜 §5.1 |
| 2 | 充能 = 纯 `CurrentFrame(0xA8ED84)` 整数差 + 一次 x87 显示映射；逻辑判定全整数 | [实证] |
| 3 | `CurrentFrame` 全镜像唯一 `inc` 在 `0x55DE81`（`MainLogicFrame`），每逻辑帧 +1，与墙钟无关 | [实证] |
| 4 | 浮点映射只影响 `GetCameoChargeState` 显示值；输入确定、FPU CW 由 `0x7C5F00` 规范 | [实证] |
| 5 | L-SW-1 不改任何写入值（`eax` 复用），故不改 `+0x78`、不改 Checksum | [推演] 纯函数等价 |

### 7.2 MP 裁决表

| 项 | L-SW-1 | L-SW-2 |
|---|---|---|
| **混端 DESYNC** | **SAFE**（字节级语义等价） | **SAFE**（纯 UI，不进 CRC） |
| **可否联机保留** | **可**（R-MP-GATE L-8 同级） | **可** |
| **是否强制 MpActive 关** | **不强制**（可选观感门） | **不强制** |
| **握手字段** | **不新增** | **不新增** |
| **默认** | `EnableSWChargeOpt=0` | `EnableSWCameoCache=0` |
| **启动日志** | `SWChargeOpt=on\|off` | `SWCameoCache=on\|off\|skipped-q2` |

> **红线重申**：联机安全的前提是**只做本卡允许的删冗余/纯 UI**。一旦动 §5.2 任何公式/推进/翻转帧，立即变成 **VIOLATION**（`IsCharged` 翻转帧分叉 → 帧 CRC + Checksum 双分叉）。

---

## 8. 风险（执行方必读）

| ID | 风险 | 等级 | 要求 |
|---|---|---|---|
| R-1 | 把 L-SW-1 误做成「跳过二次 call **及其后写回**」 | 高 | 只 NOP 7B；`0x6CBE8F` 写回**必须保留** |
| R-2 | 顺手「优化」`GetCameoChargeState` 公式或 `54.0` | 高 | §5.2 禁区；公式/常数/clamp 全禁 |
| R-3 | 把 `HasChargeProgressed` 按视觉帧节流/跳帧 | 高 | 7 项副作用非幂等；禁跳 |
| R-4 | L-SW-2 未过 Q2 就上补丁 A | 高 | `frame=-1` 可能花屏/越界；**Q2 不过则不做** |
| R-5 | flags/邻接误伤 | 中 | 只许 `90`；**禁止**改写 `0x6CBE86`/`0x6CBE8F` 或用 `8B→` 一类 1B 改法 |
| R-6 | 覆盖未知外部补丁 | 高 | G0.2 / Q1 首字节门禁；已打则停手上报 |
| R-7 | 把「没崩」当成功 | 高 | A3 强制「到点帧号不变」证据（§4） |
| R-8 | 单端调用 `Set/ResetRechargeTime` | 高 | 仅 TAction、全端同帧；本卡不碰 |

---

## 9. 交付回执（填完交回）

```
ZC-SW-CHARGE RESULT
- build/md5(gamemd):
- install path: (ra2render hook | external patcher | ...)
- EnableSWChargeOpt:
- EnableSWCameoCache:
- G0.1–G0.8: PASS/FAIL
- Q1 first byte before @0x6CBE88:
- bytes after @0x6CBE88 (L-SW-1):
- context @0x6CBE86 / 0x6CBE8F / 0x6CBE7E unchanged: y/n
- L-SW-2 applied: y/n (if y: Q2.1/Q2.2 evidence + bytes after @0x6A99AC)
- forbidden windows unchanged (§5.3): y/n
- A1..A5: (each PASS/FAIL + evidence path)
- A3 charge-complete frame (patched vs baseline):
- A5 CRC / Checksum v[13] match: y/n
- except.txt: empty|path
- rollback tested: y/n
- MP: (single | mp-preserved | mp-forced-off) + CRC note
```

---

## 10. 不在本卡

- `GetCameoChargeState` 公式重写 / `54.0` 映射调整 / clamp 语义变更 —— **禁区**  
- `RechargeTimer` 折叠算法 / `IsCharged` 翻转时机 / `ChargeDrainState` FSM 重做 —— **禁区**  
- `Set/ResetRechargeTime` 行为变更 —— **禁区**  
- 跳帧/节流 `HasChargeProgressed` —— **禁区**  
- 死代码 `0x4F9370` 清理、`Type+0xF8` 相关假说验证 —— 纯逆向收口，无补丁  
- Launch 发射路径 RNG（已由 `superweapon_re.md` 10.2 闭环）  
- 台账/看板登记 —— 由 Lead 收口

---

*依据：R-SW-CHARGE 深潜 §2.2 副作用清单 · §3.2 UI/逻辑解耦 · §5 确定性 · §6.1/6.2 字节规格；原 7B/5B 规格与 `verify_sw_charge{,2,3}.py` 一致；7×NOP 为唯一「不写内存、不改 flags、不改写入值」的 7B 替换；L-SW-2 默认不做，Q2 真机 `frame=-1` 确认前禁止安装。*
