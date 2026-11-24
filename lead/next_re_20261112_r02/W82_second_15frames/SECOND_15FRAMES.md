# W82 · 静态定谳：gamemd.exe「引擎把 15 帧当 1 秒」（event 13 ElapsedTime）

- 卡号 **W82** ｜ 执行者 agent-3（GLM-5.3-Flash，子代理，非 Lead）｜ 起始 `2026-11-14T09:57:18+08:00`
- 目标二进制：`D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe`
- **实测 SHA-256 `[本次实测]`**：`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  （4,825,360 B；与卡片给定值 **MATCH=YES**）
- 纪律：`I launched 0 / attached 0` —— 未启动 `gamemd.exe`、未 attach、未读活进程内存、未取 `.game_instance.lock`。
  只写 `W82_second_15frames\`；未写 `ra2forge`/`ra2opt`/`ra2bench`；未动 `W21`–`W81`；`git` 未调用。
- 工具：python + capstone（5.0.7）+ 复用 `W50_endofgame_chain\EVIDENCE\text_insns.pkl`
  （全 `.text` 线性反汇编缓存，1,394,120 行，VA 0x401000..0x7E0FFD，`[本次读码]` 复核其结构后直接消费）。

---

## 0. 结论速览（四问一句话）

| # | 问题 | 答案 | 强度 |
|---|---|---|---|
| ① | event 13 求值处？ | **找到了**：求值函数 `0x0071E940`，按 `[事件+0x2C]` 分发，**分发索引 = type − 13**（`0x71E950 lea eax,[ecx-0xD]`，范围 13..61），压缩跳转表 `0x71F218`/`0x71F248`；**type 13 → case 0 → `0x0071EC33`** | `[本次实测]` |
| ② | 拿什么当"当前时间"？ | **不是秒时钟，是帧差**：`fired ⟺ ([0xA8ED84] − timer.started) ≥ timer.duration`，两个量都是**帧**。`[0xA8ED84]` 为逻辑帧计数器（主循环 `0x55DE81` 每帧 +1；场景重置点 `0x68466B`/`0x686765`） | `[本次实测]` |
| ③ | 有没有参与换算的 15？ | **有，已证**：装弹函数 `0x00726400` 中，事件参数 N（秒，`[事件+0x34]`）经 `lea eax,[eax+eax*2]`（×3）→ `lea eax,[eax+eax*4]`（×5）＝ **×15** 写入 `timer.duration`，且整段被 `cmp dword ptr [edi+0x2C], 0x0D`（**type==13**）闸住 —— 这个 15 **确实参与了 elapsed-time 换算**，不是孤立常量 | `[本次实测]` |
| ④ | 三选一判定 | **`H-E 有直接证据`**（含一处措辞精确化，见 §4/DISAGREE） | `[本次实测]` |

---

## 1. 证据基线与记号

- 反汇编引用格式：`VA 0x00XXXXXX` + 指令原文；`.text` 内文件偏移 = VA − 0x400000（W59 `[转引]`）。
- 记号：`[本次实测]`＝本卡自跑脚本所得字节/反汇编（`EVIDENCE\w82_step*.py`，7 个脚本全部 exit 0）；
  `[本次读码]`＝直接阅读既有文件；`[静态推断]`＝由字节链推得但未运行时证明；`[转引]`＝已签发事实。
- 消费的既有资产：W50 `text_insns.pkl`（1,394,120 行线性反汇编，`[本次读码]`）；W63 `w63_lib.py` 的
  frame 地址口径 `0x00A8ED84`（`[转引]`）；W79 `SURVIVE_AND_ANNHIL_RESULT.md` 的 `frame = 15N + 90` 律与
  编译侧无换算结论（`[转引]`）。
- ⚠️ 数据质量声明：pkl 是"遇坏字节逐字节续扫"的韧性线性扫描，**计数型 xref 可能有数据区假阳性**；
  本卡所有结论锚定在具体 VA 的逐指令核验上。其中 step1b 的"全镜像唯一 `imul …,0xf`"（`0x006B024E`）
  **已被本卡证伪**：T4 原始字节显示那是函数指针表 `0x006AFD7A…0x006B020F` 的表项字节
  （`…3c 00 6b 00 | 0f 02 6b 00…`，`imul eax,[eax],0xf`＝表项 `0x006B020F` 中段的误读码）——
  **代码中不存在 imul 形式的 ×15**；真 ×15 是 lea 对（见 §3）。

---

## 2. 线索 A：event 13（ElapsedTime）求值代码

### 2.1 求值函数与分发结构 `[本次实测]`

```
VA 0x0071E940  sub esp, 0x1c            ; 求值函数入口（前有 nop 填充）
VA 0x0071E945  mov ebp, ecx             ; ebp = this = 触发器事件节点
VA 0x0071E94D  mov ecx, dword ptr [ebp + 0x2c]   ; ★事件 TYPE
VA 0x0071E950  lea eax, [ecx - 0xd]              ; ★分发索引 = type − 13
VA 0x0071E953  cmp eax, 0x30                     ; 范围 0..0x30 ⇒ type ∈ [13, 61]
VA 0x0071E956  ja 0x71ec63                       ; 越界走默认体
VA 0x0071E95C  xor edx, edx
VA 0x0071E95E  mov dl, byte ptr [eax + 0x71f248] ; 压缩字节映射表（49 项）
VA 0x0071E964  jmp dword ptr [edx*4 + 0x71f218]  ; case 跳转表（12 项）
```

**type → case 体全映射**（解码 `0x71F218`（12 个合法目标）与 `0x71F248`（49 字节）：

| type | case | 体 VA | 语义（读码判定） |
|---|---|---|---|
| **13** | **0** | **0x0071EC33** | **帧定时器：`frame − started ≥ duration`**（见 2.2） |
| 14 | 1 | 0x0071EBE9 | 同款结构但内联读 **`[Scen+0x11E8]/[Scen+0x11F0]`**（全局任务计时器） |
| 27 / 28 | 2 / 3 | 0x0071EB53 / 0x71EB75 | `[事件+0x34]` 为参 → `call 0x689760(Scen, …)`（局部变量读/写对） |
| 36 / 37 | 4 / 5 | 0x0071EB9E / 0x71EBC0 | 同上 → `call 0x689a00` |
| 45 | 6 | 0x0071EAE7 | 返回 `[Scen+0x352C] <= [事件+0x34]`（`setle`） |
| 46 | 7 | 0x0071EB06 | 返回 `[Scen+0x352C] >= [事件+0x34]`（`setge`） |
| **47** | 8 | **0x0071EB28** | 返回 `[事件+0x34] <= frame/15`（0x88888889 魔数 ÷15，见 §3.3） |
| 51 | 0 | 0x0071EC33 | **与 13 共享 case 0**（同用帧定时器结构，装弹处有独立 ×15 分支，`0x726453..0x726494`） |
| 60 / 61 | 9 / 10 | 0x0071E96B / 0x71EA30 | 按名字串匹配（`[事件+0x38]` vs 名字表 `0xA8EB04/0xA8EB10`） |
| 其余 | 11 | 0x0071EC63 | 默认：再按 `0x71F27C/0x71F284` 二级分派 |

⇒ **type 13 是这张表的第一项**，`1,13,0,N` 的 type 字段直落 case 0。

### 2.2 case 0 体：event 13 的"当前时间" `[本次实测]`

```
VA 0x0071EC33  mov ecx, dword ptr [esp + 0x3c]  ; arg3 = 触发器内嵌定时器指针
VA 0x0071EC37  mov edx, dword ptr [ecx]         ; started（+0）
VA 0x0071EC39  mov eax, dword ptr [ecx + 8]     ; duration（+8）
VA 0x0071EC3C  cmp edx, -1                      ; started==-1 ⇒ 定时器未启用
VA 0x0071EC3F  je 0x71ec4f
VA 0x0071EC41  mov ecx, dword ptr [0xa8ed84]    ; ★当前帧计数器
VA 0x0071EC47  sub ecx, edx                     ; elapsed = frame − started
VA 0x0071EC49  cmp ecx, eax                     ; vs duration
VA 0x0071EC4B  jge 0x71ec57                     ; elapsed ≥ duration ⇒ 命中
VA 0x0071EC4D  sub eax, ecx                     ; remaining = duration − elapsed
VA 0x0071EC4F  test eax, eax
VA 0x0071EC51  jne 0x71f163                     ; remaining≠0 ⇒ 未命中
VA 0x0071EC57  pop edi / … / mov al, 1 / ret 0x18  ; ★命中
```

**关键问题的答案**：event 13 拿的是**每逻辑帧 +1 的计数器 `[0xA8ED84]` 与装弹时刻之差**，
和**以帧为单位的 duration** 比较 —— 两者都无秒量纲；N→帧的换算不在求值处，而在装弹处（§3）。

arg3 的来源（调用方 `TriggerClass::Spring`，`0x007264C0`）`[本次实测]`：

```
VA 0x007264C4  mov al, [esi+0x44]        ; trigger.enabled
VA 0x007264CF  mov al, [esi+0x30]        ; trigger.completed
VA 0x007264ED  mov eax, [esi+0x24]       ; TriggerTypeClass*
VA 0x007264F2  mov edi, [eax+0xac]       ; 事件链表头
VA 0x00726522  lea eax, [esi + 0x34]     ; ★&TriggerClass.timer（{+0x34 started, +0x38 ?, +0x3C duration}）
VA 0x00726540  call 0x71e940             ; ecx=事件节点；唯一调用点 0x006E5414（每帧触发器扫描）
VA 0x00726585  mov edi, [edi + 0x28]     ; 事件链 next
```
TriggerClass 布局由三处互证：构造器 `0x00725FA0`（`[esi+0x34]=[0xA8ED84]`、`[esi+0x3C]=0`），
Spring（+0x24/+0x30/+0x34/+0x40 fired 位图/+0x44 enabled），序列化器 `0x00726790`
（`[esi+0x34] started`、`[esi+0x3C] duration` 同款复算）。大小 0x48（`0x726930 mov eax,0x48`）。

帧计数器写点（10 处，`[本次实测]`）：每帧自增 `VA 0x0055DE81`（主循环，
`mov edx,[0xa8ed84]; inc edx; mov [0xa8ed84],edx`）；场景复位 `0x0068466B`（Start_Scenario 区，置 0）、
`0x00686765`（`xor ebp,ebp; mov [0xa8ed84],ebp`）；其余为游戏模式切换写点。

---

## 3. 重点：15 的参与证明 + 完整换算链

### 3.1 装弹处：参数秒 ×15 → 帧定时器 `[本次实测]` ★核心证据

```
VA 0x00726400  （TriggerClass 构造/重装弹函数）
VA 0x0072640A  mov eax, dword ptr [esi + 0x24]   ; TriggerTypeClass*
VA 0x0072640D  mov edi, dword ptr [eax + 0xac]   ; 事件链
VA 0x0072641C  cmp dword ptr [edi + 0x2c], 0xd   ; ★★事件 TYPE == 13（0x0D）
VA 0x00726420  jne 0x726453
VA 0x00726422  mov ecx, dword ptr [0xa8ed84]     ; 当前帧
VA 0x00726428  mov eax, dword ptr [edi + 0x34]   ; ★事件参数 = N（秒）
VA 0x0072642B  lea edx, [esi + 0x34]             ; trigger 定时器
VA 0x0072642E  lea eax, [eax + eax*2]            ; N×3
VA 0x00726431  mov dword ptr [edx], ecx          ; timer.started = frame
VA 0x00726437  lea eax, [eax + eax*4]            ; N×3×5 = ★N×15（帧）
VA 0x0072643A  mov dword ptr [edx + 4], ecx      ; timer.+4 = 调用方栈参
VA 0x0072643F  mov dword ptr [edx + 8], eax      ; ★timer.duration = N×15
VA 0x00726442..0x726450                          ; 清本事件 fired 位
```

- 编译器用 **`lea×3` + `lea×5`** 实现常量乘 15（无 imul）——这就是 step1b 全镜像
  "imul 15 = 0 命中"的原因；×15 的存在由指令对直接证明。
- 该 ×15 **只对 type 13**（`cmp …,0x0D` 闸）与 type 51（`0x726453..0x726494`，同样
  `lea×3; lea×5` 但参数先 `/2` 加权）生效 —— 15 不是散落的无关常量，就是 ElapsedTime 的秒→帧系数。
- 装弹时机：构造器 `0x00725FA0` 末尾 `VA 0x007260E7 call 0x726400`（触发器实例化时即装弹），
  另三个调用点：Spring 全事件命中后重装（`0x7265A4`）、两个"局部变量/计数器事件存在才重装"的
  扫描（`0x7263BB`/`0x7263EB`，闸函数 `0x727010`=查 type 27/28、`0x727050`=查 type 36/37 ——
  与本卡触发器无关，不触发）。

### 3.2 完整换算链（判定 H-E 成立）

```
MAP:  [Events] 0B00001C = 1,13,0,N                     （ra2forge 原样写 N，W79 [转引]）
  → 触发器事件节点 { +0x2C: 13, +0x30: 0, +0x34: N }    （求值器/装弹器两侧读取一致）
装弹（场景装载 → 触发器实例化 0x725FA0 → 0x726400）：
     timer.started  = [0xA8ED84]        @装弹时刻        (0x726431)
     timer.duration = N × 15  [帧]                       (0x72642E lea×3, 0x726437 lea×5)
每逻辑帧（0x6E5414 → Spring 0x7264C0 → 求值器 0x71E940 → case 0x71EC33）：
     fired ⟺ frame − started ≥ duration
命中 → 动作链 → WinnerIs(8) → 胜利 → 结算屏冻结 frame
实测（W79，18 点）[转引]：  冻结 frame = 15×N + 90（8→210、20→390、55→915，零误差）
⇒ started = 90：装弹发生在场景帧复位后的第 90 帧（+90 的归属精确化见 §4 与 UNKNOWNS U1）
真实时间 = frame / 31.25 = 0.48×N + 2.88 [秒]
```

### 3.3 线索 B：「1 秒 = 15 帧」是引擎多处一致的时间基准（旁证）

1. **type 47 求值体 `0x0071EB28`** `[本次实测]`：`frame(0xA8ED84)` × `0x88888889` + `sar edx,3`
   ＝ **signed ÷15**，商与事件参数比较（`setle`）⇒ 该事件的参数语义就是 **frame/15 = 秒**。
2. **任务倒计时 HUD** `[本次实测]`：`0x006D4963` 读 `[Scen+0x11E8]`(started)/`[Scen+0x11F0]`(duration)
   后 `mov eax,0x88888889; imul ecx`（÷15）把**剩余帧换算成剩余秒**显示；`0x0071EBFC`（type 14 体）
   直接用同结构判到期。
3. **(0x7FFFFFFF − frame)/15** 形态三处（`0x006DA9D0`/`0x006DAD5E`/`0x00704DB0`）：
   倒计时类显示/逻辑把帧基准换算为 15 帧/秒的"秒"。
4. **未发现**"logic tick 率 ≠ 渲染帧率"的固定步长结构（无 `while(accumulator ≥ interval)` 形态、
   无独立 `logic_fps` 全局）：`[0xA8ED84]` 每主循环帧 +1（`0x55DE81`），逻辑帧即渲染帧。
   实测 31.25/s 来自 32ms 帧步进（W79 `[转引]`）。引擎内**没有**全局 `15` 常量参与帧率，
   15 只以"触发器/计时器的秒↔帧换算系数"出现（装弹 ×15、求值/显示 ÷15）。

---

## 4. 三选一判定与措辞精确化

**判定：`H-E 有直接证据`。**

- 「引擎把 15 帧当 1 秒」在**触发器时间语义**上成立且已证到指令级：event 13 的参数（秒）
  在装弹处被 ×15 换算为帧定时器（`0x72642E/0x726437`，type==13 闸 `0x72641C`），求值处按
  帧差比较（`0x71EC33`）；同引擎 type 47 求值、任务倒计时显示均以 `frame/15` 为"秒"。
- 与卡片 H-E 表述的**两点精确化**（不改变判定方向）：
  1. **+90 不是"公式外加的加载偏移"，而是 `timer.started`** —— 装弹时刻的 `[0xA8ED84]` 值
     （`0x726431`）。实测律 `frame = 15N + 90` ⟺ 装弹发生在帧 90（或等价地"命中在 15N、
     另有 90 帧固定胜利转场"，二者的静态/运行时判别见 `UNKNOWNS.md` U1，给出真机观察点）。
  2. "实际渲染帧率 31.25/s ⇒ 时间流速 2.08 倍"这句的机制本体是：**参数按 15 帧/秒装弹，
     而帧实际以 31.25/s 推进**；引擎没有第二个"名义时钟"，只有这一个帧计数器
     （`0x55DE81` 每帧 +1）。

---

## 5. 关键 VA 表

| 项 | VA | 指令/事实 | 强度 |
|---|---|---|---|
| 求值函数入口 | `0x0071E940` | `sub esp,0x1c; mov ebp,ecx` | `[本次实测]` |
| 事件类型字段 | `0x0071E94D` | `mov ecx,[ebp+0x2c]` | `[本次实测]` |
| 分发索引 type−13 | `0x0071E950` | `lea eax,[ecx-0xd]; cmp eax,0x30; ja` | `[本次实测]` |
| 压缩映射/跳转表 | `0x71F248` / `0x71F218` | byte map[0]=0 → case 0 | `[本次实测]` |
| **event 13 case 体** | `0x0071EC33..0x71EC60` | `frame − [ecx] ≥ [ecx+8]` ⇒ `al=1` | `[本次实测]` |
| 定时器结构 arg 来源 | `0x00726522` | `lea eax,[esi+0x34]`（TriggerClass+0x34） | `[本次实测]` |
| Spring 唯一调用点 | `0x006E5414` | 宿主 ~`0x6E53A0` 每帧触发器扫描 | `[本次实测]` |
| **×15 装弹（核心）** | `0x0072641C / 0x72642E / 0x726437 / 0x726431 / 0x72643F` | `cmp [edi+0x2C],0x0D`；`lea eax,[eax+eax*2]`；`lea eax,[eax+eax*4]`；`started=frame`；`duration=N×15` | `[本次实测]` |
| TriggerClass 构造器 | `0x00725FA0` | `+0x34=[0xA8ED84]`、`+0x3C=0`；`0x7260E7 call 0x726400` | `[本次实测]` |
| 帧计数器自增 | `0x0055DE81` | `inc edx; mov [0xa8ed84],edx` | `[本次实测]` |
| 帧计数器复位 | `0x0068466B` / `0x00686765` | `mov [0xa8ed84],0` | `[本次实测]` |
| type 47（÷15 直接比较） | `0x0071EB28..0x71EB50` | `imul 0x88888889; sar 3` ＝ frame/15 vs 参数 | `[本次实测]` |
| 任务倒计时 ÷15 显示 | `0x006D4963..0x6D4984` | `[Scen+0x11E8/0x11F0]` + `imul 0x88888889` | `[本次实测]` |
| imul-15 假阳性排除 | `0x006B0238..0x6B0253` | 函数指针表 `0x006AFD7A…0x006B020F`，非代码 | `[本次实测]` |

---

## 6. 交付物索引

- `SECOND_15FRAMES.md`（本报告）
- `UNKNOWNS.md` / `DISAGREE.md` / `PROGRESS.md` / `HEARTBEAT.txt` / `STARTED.txt`
- `EVIDENCE\`：`w82_step1.py`、`w82_step1b.py`、`w82_step2.py`、`w82_step3.py`、`w82_step4.py`、
  `w82_step5.py`、`w82_step6.py`、`w82_step7.py` + 各 `step*.stdout.txt`（全部 `EXIT_CODE=0`，
  见 `exit_codes.txt`）；`step1b_frame_xrefs.txt`（0xA8ED84 全量 xref 1009 处）、
  `step1b_muldiv15.txt`、`step1b_switch_candidates.txt`
