# Q3 · `[Scenario+0x62C]` 变非 0 的**全部可能来源**（完备清单）

> 作者：来源完备性普查员（W1 子代理）· 2026-11-05 · **只做任务书 Q3**（Q1/Q2/Q3b 不在本文件范围）。
> 纯离线静态分析：零真机、不写采样代码、不改母本、不 commit。
> 引擎：`lead/goal3t_nightwatch_20261102/swarm_20261104/ra2tool.py` 的 `Engine`（只读 `ra2youli/gamemd.exe`，
> 构造内 SHA256 断言）。**所有全镜像普查走 `Engine.stream`（重同步线性解码）**，未用裸 `disasm(blob,va)` 做普查。
> 任务书 `TASK.md:59-70`、五个前置文件（`LEADER_PRECHECK_20261105.md`、`P01/REPORT.md`、
> `P01/VERIFY.md`、`docs/re/trigger_system_manifest.md`、`Q02/REPORT.md`）均已读。

---

## 0. 一句话结论

**闭合，但清单与领队基线的「2 条脚本可达 + 1 条引擎内部」有两处出入**：
(a) **多出 1 条脚本可达来源**——动作 117 PlayIngameMovieAndPause 间接进 `0x684060`；
(b) 基线的「引擎内部、脚本不可达」那条（`0x6579E0`）被**重分类**：入队端脚本可达、
沿翻转/释放端引擎内部；而「完全无脚本动作时自发非零」在本次静态证据下**没有已证实的来源**，
只剩一个 0 静态 xref 的未验残余。在单机局 `GameMode∈{0,5}` 里，
`[Scenario+0x62C]` 变非 0 的**唯一写指令**是 `0x684174 inc [eax+0x62C]`（唯一入口 `0x684060`），
而 `0x684060` 全镜像**恰 4 个直接 call 点**；把这 4 个点按「谁驱动」展开，得到 **4 类来源**：

| 类 | 驱动 | 脚本可达? | 引擎内部不可控? |
|---|---|---|---|
| ① 动作 **110 PauseGame** | `0x6DF703` 直调 + 从属 `0x6E4080/0x6E4086` | ✔ | ✘ |
| ② 动作 **127 StartChronoScreenEffect** | `0x6DFAC5`/`0x6E2F96` → 渐变机 `0x53B460` → `0x53B612` | ✔ | 执行时机（渐变 state2→3 逐帧）由引擎管 |
| ③ 动作 **117 PlayIngameMovieAndPause**（★ **基线漏项**） | `0x6DF916` → `0x5BF390(pause=1)` → `0xB45B68` 影片队列 → `0x6579E0` → `0x657CA0` | ✔（间接） | 挂/放的帧沿由雷达绘制链管 |
| ④ 引擎内部影片队列的非脚本入队 | 仅剩 `0x5BF2B0`（`inc ecx` @`0x5BF340` → 写回 @`0x5BF341`），**全镜像 0 个静态 xref** | ✘（未证） | ✔（若可达） |

**因此结论要精确写成**：③ 的执行时机「引擎内部不可控」，但**入队入口是脚本可达的**——
领队 `LEADER_PRECHECK_20261105.md:53` 与 `TASK.md:29` 把 `0x6579E0` 判为「不经 TActionClass 派发、
对『地图里能触发什么』不构成额外入口」，这对 `0x6579E0` **本身**成立（它唯一 call 点 `0x653446`
在雷达绘制函数里），但**对整条链不成立**：动作 117 经 `0x5BF390` 写同一个全局队列，间接进 `0x684060`。
**动作 10 PlayMovie 不进 `0x684060`**（§3.3 给逐字节反证）。
**`0x684240`（7 call 点）/ `0x684290`（4 call 点）对 `0x55D877` 冻结出口没有间接影响**（§4/§5）。

---

## 1. 取证口径（本次实跑，全部可复算）

全部命令形如（Git Bash，`python -I -X utf8`，绝对路径）：

```bash
cd /d/Project/ra2-campaign-forge
python -I -X utf8 - <<'PY'
import sys; sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine
e = Engine()
print(e.sha, e.coverage)          # 全镜像重同步解码
...                                # 逐段 dump / disp_hits / call-site 普查
PY
```

本轮共实跑 **5 个独立的 `Engine()` 全量解码进程**（每个 ~4–10 分钟），命令与关键输出摘要见 §8。

**镜像自证（每次都打印，逐位一致）**：

```
SHA 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
coverage (99.99837567729335, 1394120, 66)
```

与 `ra2tool.py:28-29,91-113`、`LEADER_PRECHECK_20261105.md:108-109`、
`P01/VERIFY.md:14` 的口径一致（P01 写 100.00% 是四舍五入）。

---

## 2. 完备清单（主表）

> 「脚本可达」= 地图 `[Actions]` 段里写一条 ActionKind 就能启动这条链；
> 「引擎内部不可控」= 链的推进/沿翻转/释放发生在引擎自身的每帧状态机里，脚本无法直接指定时刻。
> 二者**不互斥**，同时成立时两栏都标 ✔ 并注明哪一段归谁。

| # | 来源 / 触发条件 | 进 `0x684060` 的路径 | 脚本可达 | 引擎内部不可控 | 证据 |
|---|---|---|---|---|---|
| **S1** | 地图含动作 **110 PauseGame**，`Value=[action+0x90]` 为时长秒 | `0x6DF6FD mov ecx,[esi+0x90]` → `0x6DF703 call 0x684060` | ✔ | ✘（时长由脚本给；但 `[+0x630]` 已武装则被吞，见 §3.1） | `action_blocks_full.txt:2629-2632`；本次 dump；`trigger_system_manifest.md:247` |
| **S2** | 110 的 YRpp 从属体 `PauseScenarioFor 0x6E4080` | `0x6E4086 call 0x684060`；`.data:0x872E78 → 0x6E4080` | ✔（按 manifest 从属体口径） | 运行时调用者**未验**（§7） | `YRpp/TActionClass.h:238`；`u32(0x872E78)=0x6E4080` 本次实读；`P01/VERIFY.md:58` |
| **S3** | 地图含动作 **127 StartChronoScreenEffect**，`Value` = 渐变刻数 >0 | `0x6DFAC5 call 0x53B460` → `0x53B560` state2 倒数到 1 → `0x53B610 xor ecx,ecx` → `0x53B612 call 0x684060(0)` | ✔ | ✔（state2→3 由 `0x55D83A` 冻结体每帧推进） | `action_blocks_full.txt:2987-2990`；本次 `0x53B460`/`0x53B600` dump；`P01/REPORT.md:120-125` |
| **S4** | 127 的从属体 `SetChronoScreenEffectState 0x6E2F90` | `0x6E2F96 call 0x53B460` → 同 S3；调用者 `0x6DFDC4`（`Execute` 区） | ✔（从属体口径） | 运行时调用者未验 | `YRpp/TActionClass.h:198`；本次 call-site 普查 `0x53B460 = 2 点` |
| **S5 ★** | 地图含动作 **117 PlayIngameMovieAndPause**，影片 id 合法、`GameMode==0`（战役） | `0x6DF916 call 0x5BF390(dl=1)` → `0x5BF43A inc ecx` → `0x5BF43B mov [0xB45B68],ecx` → 队列项 `pause=1` → `0x653446 call 0x6579E0` → 沿翻正 `0x657CA0 call 0x684060(0)` | ✔ **间接** | ✔（沿在雷达每帧绘制里判定） | `action_blocks_full.txt:2811-2817`；本次 `0x5BF390`/`0x6579E0`/`0xB45B68` dump；`Q2_6579E0.md:142-147` |
| **S6** | 117 的从属体 `PlayMovieInSidebarPauseGame 0x6E1740` | `0x6E1748 call 0x5BF390(dl=1)` → 同 S5 | ✔（从属体口径） | 运行时调用者未验 | `YRpp/TActionClass.h:126`；本次 dump `0x6E1740` |
| **S7** | 引擎内部（无脚本动作）令影片队列 `0xB45B68>0` 且当前项 `pause=1` | 同 S5 的下半段 `0x657CA0` | ✘（**未证**） | ✔（若可达） | 唯一非动作 `inc` 写点 `0x5BF341` 属 `0x5BF2B0`，**全镜像 0 个静态 xref**；详见 §3.5 |
| **S8** | `0x684060` 的**内部早退门**反例：时长≠0 且 `[Scenario+0x630]` 已为 1 | `0x6840A9 jne 0x68417A` → **不 inc** | — | ✔ | 本次 dump `0x6840A1..0x6840AF`；`P01/VERIFY.md:55` |
| **S9** | 场景构造/重置 `0x683610` 一带 | `0x6836D2 mov [ebp+0x62C],ebx(0)` → **只清 0**，不是来源 | ✘ | ✔ | `P01/VERIFY.md:52,49`；`disp_hits_field(0x62C)` 本次 18 处 |
| **S10** | 释放侧（**非来源**，列出以闭合写点全集） | `0x684180` 的 3 个 call 点：`0x55D81C`（MLF PauseTimer 到期）、`0x53B6E6`（渐变 state3）、`0x657CC8`（影片沿翻回）→ `0x684195 dec` 写回 | — | ✔ | 本次 call-site 普查；`P01/VERIFY.md:58` |
| **S11** | 动作 **100 PlayIngameMovie**（对照，非来源） | `0x6DF54E call 0x5BF390(dl=0)` → `0x657C9C je 0x657CC8` → `0x684180`（**减**，且 counter==0 时 `0x68418E` 直退） | ✔ | ✔ | `action_blocks_full.txt:2370-2376`；本次 `0x657C7D..0x657CCD` dump |
| **S12** | `0x684240`（7 call 点）/ `0x684290`（4 call 点） | **完全不读不写 `+0x62C`**；只改 `[+0x35A2]` / `[0xA8ED9C]` / `[0xB07784]` | 部分 ✔ | ✔ | §4/§5 逐条 |

**写点完备性**：本次 `disp_hits_field(0x62C)` 全镜像 = **18 处**（与 `P01/VERIFY.md:49` 逐 VA 一致），
其中 W = 7 处；链到 `[0xA8B230]` 的 Scenario 写点**恰 3 处**：`0x6836D2`(复位 0)、
`0x684174`(inc)、`0x684195`(dec 后写回)。⇒ **除 `0x684174` 外，静态可见的指令没有任何一条能把
`+0x62C` 从 0 变非 0**。故上表的「完备」= 「把 `0x684174` 的唯一入口 `0x684060` 的 4 个 call 点全部展开」。

---

## 3. 候选逐条裁定

### 3.1 动作 110 / 127（任务书点名，已定谳，本次复核一致）

本次全镜像直接 `E8 call` 普查（重同步流）：

```
call 0x684060  = 4 : 0x53b612, 0x657ca0, 0x6df703, 0x6e4086
call 0x684180  = 3 : 0x53b6e6, 0x55d81c, 0x657cc8
call 0x53b460  = 2 : 0x6dfac5, 0x6e2f96
call 0x53b560  = 2 : 0x53a747, 0x55d83a
```

与 `P01/VERIFY.md:58`、`LEADER_PRECHECK_20261105.md:14-17` 逐位一致。

动作号绑定采信领队 §2.1（本轮未重证，属「采信」）：
`out/re_work/triggers/action_dispatch_table.tsv` 的区间命中给
`0x6DF703 ∈ kind 0x6E (110) span 006DF6FD..006DF717`、
`0x6DFAC5 ∈ kind 0x7F (127) span 006DFABF..006DFAD9`；
`trigger_system_manifest.md:247,264` 同。本次另做了一次独立区间复算（命令见 §8-C），
输出与上表一致，并额外得到 `0x6DEDD7 ∈ 0x2E`、`0x6DEDEB ∈ 0x2F`（见 §4）。

**★ 一处必须写清的加一门**（本次字节新证据，影响「触发条件」一栏）：
`0x684060` 不是「调用即 +1」。逐字节：

```
00684066 85f6           test esi, esi              ; esi = ecx = 时长秒
00684068 744c           je 0x6840b6                ; 时长==0 → 跳过计时器块【也跳过 +0x630 门】
0068406A ...            (设 [+0x620]/[+0x624]/[+0x628] = now/参2/时长×60)
0068409C a130b2a800     mov eax,[0xa8b230]
006840A1 8a8830060000   mov cl,[eax+0x630]         ; 武装旗标
006840A7 84c9           test cl,cl
006840A9 0f85cb000000   jne 0x68417a               ; ★已武装 → 直接 ret，不 inc
006840AF c6803006000001 mov byte [eax+0x630],1
006840B6 8b1530b2a800   mov edx,[0xa8b230]
006840BC 8b822c060000   mov eax,[edx+0x62c]
006840C2 85c0           test eax,eax
006840C4 0f85a5000000   jne 0x68416f               ; counter≠0 → 跳过「首挂」设置，但仍落到 inc
0068416F a130b2a800     mov eax,[0xa8b230]
00684174 ff802c060000   inc dword ptr [eax+0x62c]   ; ★唯一变非 0 的指令
0068417A 5e / 83c40c / c3  pop esi / add esp,0xc / ret
```

⇒ **时长=0 的调用者（`0x53B612` 渐变、`0x657CA0` 影片沿）必 inc**；
**时长≠0 的调用者（动作 110 且 Value>0、`0x6E4086`）在 `+0x630` 已武装时被吞掉**。
另：`0x6840CF..0x6840DB` 的 SP 判别（`Mode==0` 或 `Mode==5`）**只包住 ElapsedTimer 冻结块**
（`0x6840DD..0x68410C`）；`0x68410D` 之后的「保存 `[+0x35A2]→[0xB054CC]` / 原为 0 时置
`[+0x35A2]=1,[0xA8ED9C]=1` / `0x54F720` / `[0xB07784]=0`」与末尾 `inc` 都在判别之外，
对所有 GameMode 执行（只是 `0x55D877` 的门只在 0/5 才评估）。

### 3.2 渐变机把 127 变成「延迟一帧」的来源

`0x53B460(ecx=刻数)`：`≤0` 直接返回；`new 0x24` → `[0xA9FA9C]`；
`[0xA9FA98]=[0xA9FAA8]=ecx`；`[0xA9FAB0]=1`；
`0x53B543 mov dl,[Scenario+0x35A2]` → `[0xA9FAD1]`（渐变前是否已挂起）；
`0x53B54F call 0x684240`（**无计数器版置位**）；`0x53B554 call 0x753570`。
真正的 inc 在 `0x53B560` 的 state2：`0x53B605 cmp eax,1` → `0x53B610 xor ecx,ecx` →
`0x53B612 call 0x684060`。`0x53B560` 的两个调用点是 `0x53A747` 与 **`0x55D83A`（冻结体）**——
即渐变机在冻结期间也每帧走，故 state3 的 `0x53B6E6 call 0x684180` 能自己把计数器放回去。
（`P01/REPORT.md:118-125`；本轮逐字节复核一致。）

### 3.3 ★ 动作 10 PlayMovie：**不**间接进 `0x684060`（逐字节反证）

动作 10 内联块 `0x6DE72F..0x6DE77D`（`action_blocks_full.txt:171-193`，本次 dump 复核）的**全部** callee：

```
006DE72F  call 0x72ddb0             ; 全屏影片前处理
006DE73C  call [eax+0x14]           ; [0x887640] vtable+0x14（虚调）
006DE741  call 0x6842f0  (cl=0)     ; 屏幕尺寸比对/记录
006DE755  call 0x5bf260             ; ★PlayMovieByName → 0x5bed40 → 0x432690 (Bink 全屏播放)
006DE75C  call 0x6842f0  (cl=1)
006DE769  call [edx+0x18]           ; vtable+0x18（虚调）
006DE76C  call 0x72def0             ; 全屏影片后处理
```

本次对这条链上的每个直接 callee 都做了全镜像 `call` 目标普查与函数体 dump：

- `0x6842F0` 全函数 `0x6842F0..0x68436D`（本次 dump 到 `0x6843C0`）：只读 `[0xA8EB84/88/8C/90]`、
  `[0x886FB8/BC]`，调 `0x4068E0` / `0x560BF0`，**无 `+0x62C`、无 `0x684060`、无 `0x53B460`**。
  （其业务名本轮未定名，只按调用形态描述，不采用「屏幕尺寸比对」等推测名。）
- `0x5BF260` 全函数 `0x5BF260..0x5BF2A2`：边界检查 → `[0xABF394]` 取影片项 →
  `0x5BF296 call 0x5BED40` → `ret 0xC`。**不写 `[0xB45B68]`**。
  （Q1/Q2 兄弟节把它定名为 `PlayMovieByName`；本节只按字节描述，采信其命名但不依赖它。）
- `0x5BED40..0x5BF178`（本次完整 dump，约 130 条指令）：`call 0x5C0640 / 0x54F720 /
  0x7C8DF0 / 0x7C8D20 / 0x4068E0 / 0x432690 / 0x432C70 / 0x7535B0 / 0x753620 / 0x5BFAA0 /
  0x5BFF00 / 0x5C01F0 / 0x5BFF60 / 0x4F42F0 / 0x432700 / …` 及若干 vtable 虚调，
  **无 `0x684060`、无 `0x684180`、无 `0x53B460`、无 `0x5BF390`、无 `0xB45B68` 写、无 `+0x62C` 访存**。
  `0x5BED61 cmp [0xA8B238],0 / jne` ⇒ 该链也只在 `GameMode==0` 生效。
- `0x72DDB0` / `0x72DEF0`（本次头部 dump）：前者读 `[0xB0FBE0]` → `0x534E50`/`0x4A38D0`，
  后者读 `[0xB0FBE0]` → `0x72EF60`/`0x72F140`；均属全屏影片前后处理，无挂起入口。
- 全镜像 `call 0x5BF260` = **12** 点，其中与动作 10 相关的只有 `0x6DE755`（内联）
  与 `0x6E16F9`（从属 `PlayMovie 0x6E16D0`）；其余 10 点在 Scenario.CPP / 影片子系统
  （详见 §3.5）。`call 0x5BF390` = **4** 点，`0x5BF260` 与 `0x5BF390` **互不调用**。

⇒ **动作 10（及其从属、及其全部非脚本调用者）在本轮静态证据下都不进 `0x684060`**。
它与「挂起」唯一的共同点是都置/用 `[+0x35A2]`、`[0xA8ED9C]` 这一族——但那不是计数器（§5）。
**诚实边界**：`0x5BED40` 内含 vtable 虚调与 `0x5BFAA0` 等未逐层展开的调用，
「全函数间接闭包」本轮**未穷尽**；结论限定为「直接调用图 + 已 dump 的函数体内无此边」。

### 3.4 ★ 动作 117 PlayIngameMovieAndPause：**间接进 `0x684060`**（基线漏项）

```
006DF90E  mov ecx,[esi+0x90]      ; 影片 id
006DF914  mov dl,1                ; ★ pause = 1
006DF916  call 0x5bf390           ; 侧栏影片入队器
```

`0x5BF390`（本次完整 dump）：`0x5BF3B0..0x5BF3B7` **要求 `[0xA8B238]==0`（战役）**；
`0x5BF3F4 mov byte [esi+4],bl` 把 `dl` 写进播放项 `+4`（pause 旗标）；
`0x5BF43A inc ecx` → `0x5BF43B mov [0xB45B68],ecx` → `0x5BF447 mov [ecx+eax*4],esi` 存队列。

`0xB45B68` = 全局 `DynamicVectorClass<影片播放器*>` 的 `Count`（本轮 `disp_hits` 得
**23 处引用 / 5 个 W / 18 个 R**；Q1 兄弟节 `Q1_B45B68.md:1-39,155-201` 定名，本节采信其定名、
独立复核了写点计数）。队列由 `0x48D080`（`0x48D091 mov eax,[0xB45B68]` → vtable+8 推进）
与 `0x5BF500`（读 Count → `call [edx+0xC]`）每帧泵；`0x6579E0` 在
`0x653446`（`RadarClass::v[16]` 绘制链）被唯一调用，消费队列状态：

```
006579E3  mov edx,[0xb45b68]   ; Count
006579FD  setg bl              ; 折成「队列非空」布尔沿
00657B31  mov dl,[ecx+4]       ; ★当前播放项 pause 旗标
00657B34  mov [esp+0x13],dl
...
00657C81  mov al,[esp+0x13]    ; pause 本次值
00657C85  mov cl,[esi+0x14bc]  ; 上次 latch
00657C90  cmp cl,al
00657C98  je 0x657cd4          ; 沿未变 → 不动计数器
00657C9A  test al,al
00657C9C  je 0x657cc8          ; pause==0 → 释放
00657C9E  xor ecx,ecx          ; 时长 0
00657CA0  call 0x684060        ; ★ pause==1 沿翻正 → inc +0x62C
00657CA5  mov byte [esi+0x14bc],1
00657CC8  call 0x684180        ; 沿翻回 → dec
```

⇒ **动作 117（且仅 117，`pause=1`）可让 `+0x62C` 变非 0；动作 100 的 `dl=0` 走
`0x657C9C je 0x657CC8`，是释放侧，不能从 0 变正**（`0x68418E je 0x684239` 在 counter==0 时直退，
不会出现负值）。从属体 `0x6E1740`/`0x6E1720` 同式（`YRpp/TActionClass.h:125-126`）。

**适用域精修**：`0x5BF390` 的门是 `test [0xA8B238]; jne 退出`，即**只认 `GameMode==0`（战役）**；
而 `0x55D877` 的冻结门接受 `{0,5}`。⇒ **在 Skirmish(5) 局里，S5/S6 这条来源不成立**，
只剩 S1/S2/S3/S4。这是「单机局∈{0,5}」提问下必须分栏的一处。

### 3.5 引擎内部非脚本来源：只剩一个**未证**的入口

`0xB45B68` 的 5 个写点（本次 `disp_hits` 十进制→十六进制换算后逐 VA 打印）：

| VA | 指令 | 作用 | 所在函数 | 该函数静态 xref |
|---|---|---|---|---|
| `0x5BF341` | `mov [0xB45B68],ecx`（`inc` 后） | **+1** | `0x5BF2B0`（全屏影片注册器） | **0** |
| `0x5BF43B` | `mov [0xB45B68],ecx`（`inc` 后） | **+1** | `0x5BF390`（侧栏影片注册器） | 4（全是动作 100/117 内联+从属） |
| `0x5BF487` | `mov [0xB45B68],ebx(0)` | 清 0 | `0x5BF450` ClearAll | 6（场景加载/退出/清场） |
| `0x657B67` | `mov [0xB45B68],ecx`（`dec` 后） | −1 | `0x6579E0`（影片播完移除） | 1（`0x653446`） |
| `0x7591B1` | `mov [0xB45B68],eax(=0)` | CRT 静态初始化写 0 | `0x759180` | — |

**唯一能令 Count 从 0 变正的两处「`inc ecx` 后写回」是
`0x5BF340/0x5BF341`（`0x5BF2B0`）与 `0x5BF43A/0x5BF43B`（`0x5BF390`）。**
本次全镜像分支/调用目标普查（含 `jmp` 尾调）与原始字节 dword 扫描：

```
0x5bf2b0 branch-targets 0 []
0x5bf390 branch-targets 4 [0x6df54e, 0x6df916, 0x6e1728, 0x6e1748]
0x5bf2b0 raw LE dword occurrences: []
```

⇒ **静态可见的「非脚本入队」只有 `0x5BF2B0`，而它没有任何静态 xref**（既无 `E8/E9` 目标，
也无函数指针 dword）；其可达性**未验**。因此：

- **S7 不能写成「已证实的引擎内部来源」**，只能写成「**未排除的残余入口**」；
- 若 `0x5BF2B0` 实际上不可达，则 `0x6579E0` 这条链的 `+1` **全部**来自动作 100/117，
  领队「引擎内部、脚本不可达」的标签应反过来改成「**入队脚本可达、沿与释放引擎内部**」。

**与 Q1 兄弟节的一处不一致（登记，不越权改写）**：`Q1_B45B68.md:21-22,223-236,252-255`
称 `0x5BF260` 的 10 个非脚本调用者（含 `0x53933E "INTRO"`、`0x683CBD` Intro/Brief、
`0x6859xx` 胜败影片）会「把播放器压进 `0xB45B58`、Count 由 0→1」。
本次实跑的反证：`0x5BF260` 函数体只调 `0x5BED40`（`0x5BF296`），
`0x5BED40` 体内**无** `0x5BF2B0` / `0x5BF390` / `0xB45B68` 写 / `+0x62C`；
`0x5BF260` 与 `0x5BF2B0` 是**两个不同函数**（`0x5BF260 ret 0xC` / `0x5BF2B0 ret`），
二者之间没有静态边。Q1 自己在 `Q1_B45B68.md:116,132-136` 也把 `0x5BF2B0` 标为
「0 个静态 xref、可达性未验」，与 §5.1 J3 的强结论自相矛盾。
本次复核了 `0x53933E` 的字节（`0053932F mov ecx,0x8263A8` → `call 0x48DF30` →
`0053933E call 0x5BF260`）及串 `"INTRO"/"Intro"/"Basic"/"Brief"/"LOADING"/"%s.VQA"` 均为真，
**但这些调用只走全屏 `0x5BED40 → 0x432690` 链，不写 Count**。
⇒ 对 Q3 的净影响：**「无脚本动作时 `+0x62C` 自发非零」在本次静态证据下没有已证实的来源**，
只有 `0x5BF2B0` 这一个未验残余。这一条必须进诚实账（§7）。

### 3.6 从属体（ACTION_FUNC slave）的可达性边界

`0x6E4080`（110）、`0x6E2F90`（127）、`0x6E16D0`/`0x6E1720`/`0x6E1740`（10/100/117）
全镜像 `E8` 直接调用者均为 **0**。`.data:0x872E78 = 0x6E4080` 是唯一的 dword 指针；
本次对 `0x872A7C..0x872E7C`（**256 个等距 `0x22B` 的 `.text` 指针**，
`distinct=256`、`zero=0`、first `0x6C1A07`、last `0x6E4080`）做了消费方搜索：

```
== insns with ANY operand whose mem.disp/imm in [0x872A70,0x872F00) ==   count 0
== raw occurrences of 7C 2A 87 00 / 78 2E 87 00 / ... ==                  [] (全部)
```

即**镜像内找不到引用该表基址的指令**（可能由外部/运行时基址+索引算得，或该表仅供 YRpp 符号锚）。
`trigger_system_manifest.md:125` 早已注「hook slave 不必然生效」。
⇒ S2/S4/S6 的「脚本可达」是**按 manifest/YRpp 的从属体口径采信**，
**运行时调用者未验**；若这些 slave 实际不被调用，则 S1/S3/S5 的内联块已足以覆盖脚本面，
清单不减项（只是少几个重复入口）。

---

## 4. `0x684240`（7 call 点）与 `0x684290`（4 call 点）逐条判定

两个函数的**完整函数体**（本次 dump）：

```
00684240  mov ecx,0x87f7e8 ; call 0x6938c0 ; [0x887640] vtable+0x28 / +0xc
00684264  mov ecx,[0xa8b230]
0068426C  mov byte [ecx+0x35a2],1      ; ★挂起态 byte
00684278  mov byte [0xa8ed9c],al(1)    ; ★全局镜像
0068427D  call 0x54f720                 ; 鼠标/输入 drain
00684282  mov dword [0xb07784],0       ; ★追帧目标清零
0068428C  ret
00684290  mov eax,[0xa8b230] ; cmp byte [eax+0x35a2],1 ; (==1 才 drain vtable+0x28/+0x10 循环)
006842CC  mov byte [eax+0x35a2],0
006842D9  mov byte [0xa8ed9c],0
006842E0  call 0x54f720
006842E5  mov dword [0xb07784],0
006842EF  ret
```

**字节判据**：对 `0x684240..0x6842EF` 区间做 `disp==0x62C` 扫描 → **0 命中**；
全镜像 `call 0x684060` 的 4 个点也**没有一个是这两个函数**。
⇒ **它们不加计数、不减计数、不读计数**（与 `TASK.md:68`、`P01/REPORT.md:116` 一致）。

| # | call 点 | 所在函数/动作块 | 脚本可达 | 作用 | 对 `0x55D877` 有间接影响? |
|---|---|---|---|---|---|
| A1 | `0x4FCB39` | `0x4FC9E0`（HouseClass Win 路径）；被动作 **1 Win** `0x6DEA53`、**2 Lose** `0x6DEA83`、
     **67 AnnounceWin** `0x6DDD7F`、从属 `PlayerWin 0x6E0448` 等调用 | ✔ | 胜负结算置挂起态 | **无**（只写 `+0x35A2`/`[0xA8ED9C]`/`[0xB07784]`） |
| A2 | `0x4FCD22` | `0x4FCBD0`（Lose 路径）；被 **68 AnnounceLose** `0x6DDD9B`、从属 `PlayerLose 0x6E0468` 调用 | ✔ | 同上 | **无** |
| A3 | `0x53B54F` | 渐变启动器 `0x53B460` 尾部（由 127 驱动） | ✔（经 127） | 渐变开始前先置挂起态 | **无**；但会改变后续 `0x684060` 的「首挂」分支，见下方注 |
| A4 | `0x55D086` | `0x55CFD0`（会话/旗标消费 dispatcher，主循环 `0x48CE93/0x48CEA1` 调用） | ✘ | 会话转换时置挂起态 | **无** |
| A5 | `0x69BB01` | `0x69BAB0`（主循环 `0x48CE85` 每帧调用；另 `0x48CC70`、`0x55D154/1E2/240/28D`）；条件 `[Scenario+0x35A2]==0`；随后 `[0xB07784]=CurrentFrame+3` | ✘ | 每帧条件置挂起态 + 设追帧目标 | **无**（追帧目标属正常体，见注） |
| A6 | `0x6DEDD7` | 动作 **46 LockInput** 内联块 `0x6DED8B..0x6DEDEB` | ✔ | 锁输入时置挂起态 | **无** |
| A7 | `0x6E26AC` | `0x6E2520`（`PlayVoxelAnimAtWP` 系从属体；调用者 `0x6DED0A` = 动作 **43 CreateVoxelAnim** 派发块 `0x6DECEF..0x6DED1C`） | ✔ | 体素动画时置挂起态 | **无** |
| B1 | `0x53B722` | 渐变机 `0x53B560` state3 收尾（若 `[0xA9FAD1]==0` 才调） | ✔（经 127） | 清挂起态 | **无** |
| B2 | `0x55DE8F` | MLF **正常体**尾部：`0x55DE79 mov eax,[0xB07784]` → 与帧号比较 → 落后才调 | ✘ | 追帧收尾清挂起态 | **无**（见下方注） |
| B3 | `0x6DEDEB` | 动作 **47 UnlockInput** 内联块 | ✔ | 解锁输入时清挂起态 | **无** |
| B4 | `0x6E26C0` | `0x6E2520` 从属体（同上 A7） | ✔ | 清挂起态 | **无** |

> 注（**唯一的「间接」关系，且不影响 `0x55D877` 的门**）：
> 1. `0x684240` 把 `[+0x35A2]` 置 1；`0x684060` 在 `0x684113 mov al,[ecx+0x35A2]` /
>    `0x68411B mov [0xB054CC],al` / `0x684120 jne 0x68416F` 读到它时，会**跳过首挂设置**——
>    但 `0x68416F` 仍落到 `0x684174 inc`。所以 `0x684240` 改变的是「释放时恢复块是否执行」，
>    **不是「是否 inc」**。渐变路径（A3 → `0x53B612`）正是这个组合。
> 2. `0x684240` 把 `[0xB07784]` 清 0，`0x55DE79` 在正常体尾部读它并在落后时调 `0x684290`（B2）——
>    这条链整体位于**正常体 `0x55D878` 之后**，而冻结出口 `0x55D877` 在 `0x55D82E` 就分叉走了，
>    **正常体被整体跳过**（`P01/REPORT.md:32,80`）。故 B2 不可能反过来影响冻结门。
> 3. `0x684290` 只在 `[+0x35A2]==1` 时 drain，`0x684180` 的恢复块只在
>    `[0xB054CC]==0 && [+0x35A2]==1` 时 drain；两者共用同一族表现变量，但**共用表现变量 ≠ 共用计数器**。

**总判定：`0x684240` 的 7 个点与 `0x684290` 的 4 个点对 `0x55D877` 冻结出口「有没有间接影响」= 没有。**
它们能让 `[+0x35A2]` / `[0xA8ED9C]` 变 1，但 `0x55D877` 的门**只看 `+0x62C`**。

---

## 5. ★ 三条链**分开写清**（任务书特别要求，不许混为一谈）

### 链 A · 冻结出口 `0x55D877` 的门 —— **只读 `[Scenario+0x62C]`**

```
0055D7C2  a138b2a800        mov eax,[0xa8b238]          ; GameMode
0055D7C9  7409              je 0x55d7d4                 ; ==0 Campaign
0055D7CB  83f805            cmp eax,5
0055D7CE  0f85a4000000      jne 0x55d878                ; ≠5 → 正常体
0055D7D4  8b3d30b2a800      mov edi,[0xa8b230]          ; Scenario
0055D7DA  8a8730060000      mov al,[edi+0x630]          ; 前置门：PauseTimer 武装旗标
0055D7E2  743d              je 0x55d821                 ; 未武装 → 跳过计时器块
   ... (0x55D7E4..0x55D81C 到期时 0x55D81C call 0x684180 减一次)
0055D821  a130b2a800        mov eax,[0xa8b230]
0055D826  8b882c060000      mov ecx,[eax+0x62c]         ; ★唯一判据
0055D82C  85c9              test ecx,ecx
0055D82E  7448              je 0x55d878                 ; ==0 → 正常体
0055D830  ... (冻结体 6 项：泵/0x48D080/渐变/present/0x4F4480/节流)
0055D877  c3                ret                          ; 冻结出口
```

门 = `GameMode∈{0,5}` ∧ `[Scenario+0x62C]≠0`。
**该区间内对 `[0xA8ED9C]`、`[0xA8ED80]`、`[+0x35A2]` 的读点：0 处**
（本次 `disp_hits(0xA8ED9C)` 在 `[0x55D360,0x55DEE0)` 与 `[0x48CE40,0x48CEB0)` 内
只有 `0x48CE73` 一条 **W**，无 R；`+0x35A2` 在冻结段内无访存）。

### 链 B · 主循环每帧的**镜像抄写** —— `+0x35A2` → `[0xA8ED9C]`，与链 A 无关

```
0048CE62  a130b2a800        mov eax,[0xa8b230]
0048CE67  8a88a2350000      mov cl,[eax+0x35a2]         ; ★读挂起态 byte
0048CE6D  891da0eda800      mov [0xa8eda0],ebx          ; (另一个全局，≠0xA8ED9C)
0048CE73  880d9ceda800      mov [0xa8ed9c],cl           ; ★写镜像（byte）
0048CE79  b938b2a800        mov ecx,0xa8b238
0048CE85  e826ec2000        call 0x69bab0               ; 条件内可 call 0x684240 (A5)
0048CE8A  e8d1040d00        call 0x55d360               ; MLF（链 A 在这里面）
```

- 这条链是**单向刷新**：主循环每帧把 `+0x35A2` 抄进 `[0xA8ED9C]`，然后才调 MLF。
- `+0x35A2` 的写者有两族：`0x684060`（链 A 的**首挂**设置，`0x68414C`）、`0x684180`（恢复，`0x6841EF`）、
  `0x684240`（A1–A7，**不加计数**）、`0x684290`（B1–B4，**不加计数**）、`0x68361E` 场景重置。
  ⇒ **`[0xA8ED9C]==1` 既可能来自计数器路径，也可能来自无计数器路径，二者不等价**；
  **不能用 `[0xA8ED9C]` 作 `+0x62C≠0` 的判据**（`Q02/REPORT.md:55,192` 把二者并列为不同判别通道，与此一致）。
- `[0xA8ED9C]` 全镜像 **42 处引用 / 23 W / 19 R**；19 个 R 分布在 `0x54F212..0x54FAA5`
  （11 处）、`0x55DFDC`、`0x692F30..0x693880`（5 处）、`0x6A9734`、`0x6ABA27`
  （本次 `disp_hits` 打印，十进制 VA 经换算），
  **无一落在 `0x55D7C2..0x55D877` 的冻结门、也无一落在 `0x48CE40..0x48CEB0` 主循环判定段**。
  ⇒ 链 B 不回喂链 A。本轮未对这 19 个 R 逐一追到函数级，登记为「未穷尽」（§7）。

### 链 C · `0x55D377` 的**失焦等待环** —— 读 `[0xA8ED80]`，与链 A/B 都不同

```
0055D360  a0a0e9a800        mov al,[0xa8e9a0]           ; InGame
0055D371  0f84580b0000      je 0x55decf                 ; ==0 → 早退 al=1
0055D377  a080eda800        mov al,[0xa8ed80]           ; ★焦点旗标（不是 +0x62C！）
0055D37C  c60558cdab0001    mov byte [0xabcd58],1        ; MLF 执行中闩锁
0055D383  84c0              test al,al
0055D385  7534              jne 0x55d3bb                 ; 有焦点 → 继续
0055D38D  a138b2a800        mov eax,[0xa8b238]
0055D39B  68f4010000        push 0x1f4                  ; Mode 0/5: Sleep(500)
0055D3A0  ffd6              call esi                     ; esi=[0x7E11F0]=Sleep
0055D3A2  e8a9790700        call 0x5d4d50                ; 消息泵
0055D3A7  a080eda800        mov al,[0xa8ed80]
0055D3AE  74dd              je 0x55d38d                  ; 循环直到焦点回归
0055D3B2  6a0a / ffd6       push 0xa; call esi           ; 其他模式：单次 Sleep(10)
0055D3BB  a184eda800        mov eax,[0xa8ed84]           ; CurrentFrame
```

- `[0xA8ED80]` 全镜像 **46 处引用 / 唯一 W = `0x7778CE`**（本次 `disp_hits` 打印全部 46 条；
  `ra2tool.py:34` 注为「焦点/快进旗标，WndProc WM_ACTIVATEAPP」）；本次 dump 确认
  `0x7778C9 setne al` → `0x7778CE mov byte [0xa8ed80],al`。
- 它在 MLF 内被读 3 处：`0x55D377`（头门）、`0x55D3A7`（等待环复检）、
  `0x55D88E`（**正常体**开头，`0x55D878` 之后）；另 `0x55E204` 在节流器网络分支读。
- 这条链是 `Q02/REPORT.md:32,88-90` 的**第三条免-inc 路径**：失焦期间持续 Sleep(500)+泵，
  投影到 `[t,f]` 上也是「帧号不推进」，**但它写在链 A 的分叉之前、且不碰 `+0x62C`**。
  它是**引擎内部、脚本完全不可控**的另一类停摆原因，**不是 `0x55D877` 的来源**。

### 三链对照（禁止混用的判据表）

| | 链 A 冻结门 | 链 B 主循环镜像 | 链 C 失焦等待环 |
|---|---|---|---|
| 位置 | `0x55D7C2..0x55D877` | `0x48CE62..0x48CE8A` | `0x55D360..0x55D3BB` |
| 读的核心变量 | `[Scenario+0x62C]`（dword） | `[Scenario+0x35A2]`（byte） | `[0xA8ED80]`（byte） |
| 写的变量 | 无（只跳过 INC 块） | `[0xA8ED9C]`（byte）、`[0xA8EDA0]` | `[0xABCD58]` 闩锁 |
| 唯一写者 | `0x6836D2`/`0x684174`/`0x684195` | `0x48CE73` + `0x684060/0x684180/0x684240/0x684290` 等 23 处 | `0x7778CE` |
| 出口 | `0x55D877 ret`（不 inc 帧号） | 继续 `call 0x55D360` | 循环回 `0x55D38D`（不 inc 帧号） |
| 脚本可达 | ✔（110/127/117） | 部分 ✔（46/47/1/2/67/68/43/127 等可置 `+0x35A2`） | ✘ |
| 会不会改变 `+0x62C` | **是（唯一入口）** | **否** | **否** |
| 会不会被 `0x684240/0x684290` 影响 | **否** | **是**（它们就是写者之一） | **否** |

---

## 6. 「看似来源但不是」的排除项（完备性的另一半）

1. **动作 10 PlayMovie / 100 PlayIngameMovie**：见 §3.3 / §3.4；前者不进 `0x684060`，
   后者走 `0x684180` 减侧且 counter==0 时直退。
2. **动作 46 LockInput / 47 UnlockInput / 1 Win / 2 Lose / 67 AnnounceWin / 68 AnnounceLose /
   43 CreateVoxelAnim**：只调 `0x684240`/`0x684290`（无计数器版），**不能**让 `+0x62C` 变非 0。
3. **`0x55D81C`（MLF PauseTimer 到期）/`0x53B6E6`（渐变 state3）/`0x657CC8`（影片沿翻回）**：
   是 `dec` 侧，只会让计数器变小。
4. **`0x6836D2`**：场景构造/重置写 0。
5. **`[0xA8ED9C]` 或 `[+0x35A2]` 为 1**：见 §5 链 B，是**表现态镜像**，不是计数器。
6. **`[0xA8ED80]` 失焦 / `[0xA8EDA0]` / `[0xB07784]` 追帧 / `[0xABCD58]` 闩锁**：
   都属别的免-inc 或收尾通道，不写 `+0x62C`。
7. **`0x6842F0`（动作 10 调用的另一函数）**：全函数无 `+0x62C` 访存。
8. **4 个非 Scenario 的 `[reg+0x62C]` W 写点**（`0x665EDE`/`0x671836`/`0x71106E`/`0x71463F`）：
   `P01/VERIFY.md:49` 已排除（各函数窗口内无 `[0xA8B230]` 装载）；本次 `disp_hits_field(0x62C)`
   的 18 处与之逐 VA 一致。

---

## 7. 诚实账

**本轮亲验（均有实跑命令 + 输出，见 §8）**
1. `Engine()` 的 SHA / `coverage = (99.99837567729335, 1394120, 66)`（5 次独立解码）。
2. 全镜像 `E8 call` 与 `jmp/jcc` 目标普查：`0x684060`=4、`0x684180`=3、`0x53B460`=2、
   `0x53B560`=2、`0x684240`=7、`0x684290`=4、`0x5BF390`=4、`0x5BF260`=12、`0x6579E0`=1、
   `0x5BF2B0`=0；原始 dword 指针扫描与 256 项 `0x872A7C` 表的消费方搜索（count 0）。
3. 逐段 dump：`0x684060` / `0x684180` / `0x684240` / `0x684290` / `0x6842F0` /
   `0x53B460` / `0x53B600..0x53B740` / `0x5BF260` / `0x5BF2B0` / `0x5BF360` / `0x5BF390` /
   `0x5BF450` / `0x5BF500` / `0x5BED40` / `0x6579E0` / `0x6E16D0..0x6E1760` /
   `0x6E4080` / `0x6E2F90` / 动作 10/100/110/117/127 内联块 / `0x48CE50..0x48CEA5` /
   `0x48D080` / `0x55D360..0x55D3C0` / `0x55D7C2..0x55D878` / `0x55DE73..0x55DEA5` /
   `0x7778C0..0x7778E0` / 7+4 个 call 点上下文。
4. `disp_hits_field(0x62C)`=18、`disp_hits(0xA8ED9C)`=42(23W/19R)、
   `disp_hits(0xA8ED80)`=46(1W@`0x7778CE`)、`disp_hits(0xA8EDA0)`=32、
   `disp_hits(0xB45B68)`=23(5W/18R)、`disp_hits_field(0x35A2)`=21(5W)、
   `disp_hits(0xB07784)`=8(7W)、`disp_hits(0xB054CC)`=2、`disp_hits(0xA8B230)` 的 3 个 W。
5. 动作块区间映射（`action_dispatch_table.tsv` 146 行）：110/127/10/100/117/46/47/43 的 span 命中。
6. 非脚本影片串实读：`"INTRO"` `0x8263A8`、`"Intro"` `0x8241C0`、`"Basic"` `0x82BF9C`、
   `"Brief"` `0x83D8A8`、`"LOADING"` `0x82C1BC`、`"%s.VQA"` `0x83D888`，及 `0x53933E` 的调用字节。
7. `0x5BF390`/`0x5BF2B0`/`0x5BED40` 的 `GameMode==0` 门（战役专属）。

**采信（未重证）**
- 领队 `LEADER_PRECHECK_20261105.md:28-33` 的 110/127 动作号绑定、
  `TASK.md:18-24` 的 7 条前提、`P01/REPORT.md` + `P01/VERIFY.md` 的 `+0x62C` 定谳、
  `trigger_system_manifest.md:147,237,247,254,264` 的动作名/从属体、
  `Q02/REPORT.md:32,55,88-90,134` 的免-inc 路径画像。
- 兄弟节 `Q1_B45B68.md:1-39,155-201` 对 `0xB45B68` 的类级定名、
  `Q2_6579E0.md:23-40,91-114,142-147` 对 `RadarClass` 绘制链与 100/117 入队的定名
  （本节独立复核了其中的写点计数、4 个 call 点、动作块字节与 GameMode 门）。

**未验 / 无法判定（不得当成已闭合）**
1. **`0x5BF2B0` 的运行时可达性**：0 个静态 xref、无函数指针 dword；若它可由虚表/函数指针
   间接到达，则「无任何脚本动作时 `+0x62C` 自发非零」会多一条已证实的引擎内部来源。
   本轮**未做穷尽式间接调用闭包**。§3.5 标注了与 Q1 兄弟节的一处矛盾结论。
2. **动作 10 链上 `0x5BED40` 的虚调与 `0x5BFAA0` 等下游未逐层展开**：
   结论「动作 10 不进 `0x684060`」限于直接调用图 + 已 dump 的函数体，不是全闭包证明。
3. **`.data:0x872A7C` 256 项 ACTION_FUNC 表的运行时消费方**：镜像内找不到引用其基址的指令，
   故 S2/S4/S6 的从属体「脚本可达」是按 manifest/YRpp 口径采信，**运行时调用者未验**。
4. **`[0xA8ED9C]` 的 19 个 R 点未逐一追到函数级**：只证明它们不在 MLF 冻结门与主循环判定段内。
   若其中某个 R 反过来写 `+0x62C`（本轮 `disp_hits_field(0x62C)` 的 18 处已排除直接写），
   仍可能经间接指针写——同 `P01/REPORT.md:152` 声明的边界：
   **`rep movsd` / `memset` 整对象拷贝、经 `[0xA8B234]` 等指针副本的间接访问形态未排查**。
5. **读档/存档反序列化是否会把 `+0x62C` 恢复成非 0**：本轮未查（P01 诚实账 #4 同边界）。
6. **`0x6579E0` 在冻结帧内是否真的被调到**（冻结体 6 项执行集里 `0x4F4480` 是 present 链，
   侧栏绘制链是否在其中未逐层解）：因此「动作 117 的挂起何时被释放」本轮只给静态判据，未证实时序。
7. **Q1/Q2/Q3b**（`0x48D091` 前后 20 条、六库函数分层、地图全量普查、map_sha 对应文件）：
   **本文件一律未做**，按任务书要求只交付 Q3。
8. **零真机**：以上全是静态判据；「某次运行里 `+0x62C` 究竟非 0 过没有」不在本轮证据内。

---

## 8. 实跑命令与关键输出（复算入口）

### 8-A 全镜像 call-site / 指针普查（第 1 个解码进程）

```bash
python -I -X utf8 - <<'PY'
import sys, struct
from collections import defaultdict
sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine
e = Engine(); print('SHA256', e.sha); print('coverage', e.coverage)
calls = defaultdict(list)
for i in e.stream:
    if i.mnemonic == 'call' and i.operands and i.operands[0].type == 2:
        calls[i.operands[0].imm].append(i.address)
for t in [0x684060,0x684180,0x53B460,0x53B560,0x684240,0x684290,0x6579E0,
          0x6E16D0,0x6E1720,0x6E1740,0x6E4080,0x6E2F90,0x6842F0,0x653446,
          0x72DDB0,0x72DEF0,0x5BF260]:
    print(hex(t), len(calls.get(t,[])), [hex(x) for x in calls.get(t,[])])
PY
```

输出（节选，逐字）：

```
SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
coverage (99.99837567729335, 1394120, 66)
0x684060   callers(4) = ['0x53b612', '0x657ca0', '0x6df703', '0x6e4086']
0x684180   callers(3) = ['0x53b6e6', '0x55d81c', '0x657cc8']
0x53b460   callers(2) = ['0x6dfac5', '0x6e2f96']
0x53b560   callers(2) = ['0x53a747', '0x55d83a']
0x684240   callers(7) = ['0x4fcb39','0x4fcd22','0x53b54f','0x55d086','0x69bb01','0x6dedd7','0x6e26ac']
0x684290   callers(4) = ['0x53b722','0x55de8f','0x6dedeb','0x6e26c0']
0x6579e0   callers(1) = ['0x653446']
0x6842f0   callers(7) = ['0x6482ad','0x65238c','0x67e6d0','0x6de741','0x6de75c','0x6e16e5','0x6e1700']
0x5bf260   callers(12)= ['0x53933e','0x683cbd','0x683db6','0x685928','0x68597d','0x685999',
                          '0x6859e9','0x686073','0x6de755','0x6e16f9','0x6e992a','0x6eded3']
0x6e4080   callers(0) = [];  0x6e2f90 callers(0) = []
```

### 8-B 综合逐段 dump + 全局访存普查（第 2 个解码进程）

同 8-A 的 `Engine()` 头，后接 `dump(lo,hi,tag)`（`bisect` 到 `e.by()` 的重同步流）
与 `e.disp_hits*` 全量打印。关键输出：

```
== ENGINE == 73201cc0…f67476 (99.99837567729335, 1394120, 66)
00684174 ff802c060000   inc dword ptr [eax + 0x62c]      ← 唯一变非 0 的写
00684195 89812c060000   mov dword ptr [ecx + 0x62c], eax  ← dec 后写回
0068426C 8881a2350000   mov byte ptr [ecx + 0x35a2], al   ← 0x684240，无计数器
006842CC c680a235000000 mov byte ptr [eax + 0x35a2], 0    ← 0x684290，无计数器
0048CE67 8a88a2350000   mov cl, byte ptr [eax + 0x35a2]   ← 链 B 读
0048CE73 880d9ceda800   mov byte ptr [0xa8ed9c], cl       ← 链 B 写
0048CE8A e8d1040d00     call 0x55d360
0055D377 a080eda800     mov al, byte ptr [0xa8ed80]       ← 链 C 读
0055D826 8b882c060000   mov ecx, dword ptr [eax + 0x62c]  ← 链 A 读
0055D82E 7448           je 0x55d878
0055D877 c3             ret
== disp_hits_field(0x62C) ==   18 处（W 7 处，与 P01/VERIFY.md:49 逐 VA 一致）
== disp_hits(0xA8ED9C) ==     count 42
== disp_hits(0xA8ED80) ==     count 46 / IN-MLF 3 处 0x55D377,0x55D3A7,0x55D88E
== disp_hits(0xB45B68) ==     count 23 / W 5 处
== disp_hits_field(0x35A2) == 21 / W 5 处
== 0xA8B230 writes ==         3
== head_of / callers ==
0x657ca0 head=0x6579e0 callers=['0x653446']
0x6df703 head=0x6dd8b0 callers=['0x726605']
0x6dfac5 head=0x6dd8b0 callers=['0x726605']
0x6e4086 head=0x6e3ee0 callers=['0x72720f']
0x6e2f96 head=0x6e2f00 callers=['0x6dfdc4']
0x55d086 head=0x55cfd0 callers=['0x48ce93','0x48cea1']
0x69bb01 head=0x69bab0 callers=['0x48cc70','0x48ce85','0x55d154',…]
```

### 8-C 动作区间映射 / 表基 / 从属体指针（读文件，不解码）

```bash
python -I -X utf8 - <<'PY'
# action_dispatch_table.tsv 的 span 命中 + gamemd.exe 原始 dword 扫描
PY
```

```
0x6de72f ('0A', '006DE72F..006DE780', '…;sub_006842F0;sub_005BF260;…')
0x6df546 ('64', '006DF546..006DF562', 'sub_005BF390')
0x6df90e ('75', '006DF90E..006DF92A', 'sub_005BF390')
0x6df6fd ('6E', '006DF6FD..006DF717', 'sub_00684060')
0x6dfabf ('7F', '006DFABF..006DFAD9', 'sub_0053B460')
0x6dedd7 ('2E', '006DED8B..006DEDEB', '…sub_00684240')
0x6dedeb ('2F', '006DEDEB..006DEDFF', 'sub_00684290')
0x6E4080 ptrs 1 ['0x872e78'] ; 0x6E2F90 / 0x6E16D0 / 0x6E1720 / 0x6E1740 ptrs 0
table 0x872A7C..0x872E7C: 256 entries, distinct 256, spacing 0x22B, zero=0
```

### 8-D 影片链 / GameMode 门 / 表消费方（第 3–4 个解码进程）

```
0x5bf390 E8 callers 4 ['0x6df54e','0x6df916','0x6e1728','0x6e1748']
0x5bf2b0 E8 callers 0 [] ; raw LE dword 0x5BF2B0 occurrences: []
0x5bf450 E8 callers 6 ['0x6856d3','0x685e23','0x686475','0x6865ba','0x69bb73','0x6a7fc3']
0x5bf500 E8 callers 5 ['0x683f4f','0x684048','0x7773cf','0x777594','0x7778e4']
== insns referencing [0x872A70,0x872E90) via disp/imm ==   count 0
005BF3B0 a138b2a800 / 005BF3B5 85c0 / 005BF3B7 0f858d000000  jne 退出   ← GameMode==0 门
005BF2B0 a138b2a800 / 005BF2B8 85c0 / 005BF2BB 0f858f000000  jne 退出
005BED61 a138b2a800 / 005BED68 3bc3 / 005BED6A 0f85fe030000 jne 退出
0x8263a8 b'INTRO'  0x8241c0 b'Intro'  0x82bf9c b'Basic'
0x83d8a8 b'Brief'  0x82c1bc b'LOADING'  0x83d888 b'%s.VQA'
0053932F b9a8638200 mov ecx,0x8263a8 ; 0053933E e81d5f0800 call 0x5bf260
00657B31 8a5104 mov dl,[ecx+4] ; 00657CA0 e8bbc30200 call 0x684060
00657CC8 e8b3c40200 call 0x684180
```

### 8-E 终检：分支目标全集 / 链隔离（第 5 个解码进程）

```bash
python -I -X utf8 - <<'PY'
# 全部 jcc/jmp/call 的 rel 目标计数 + 原始字节 + MLF/主循环区间内 0xA8ED9C 读点
PY
```

```
SHA …f67476  coverage (99.99837567729335, 1394120, 66)
0x684060 branch-targets 4 [0x53b612,0x657ca0,0x6df703,0x6e4086]
0x684180 branch-targets 3 [0x53b6e6,0x55d81c,0x657cc8]
0x53b460 branch-targets 2 [0x6dfac5,0x6e2f96]
0x684240 branch-targets 7 ; 0x684290 branch-targets 4 ; 0x5bf2b0 branch-targets 0
0x6579e0 branch-targets 1 [0x653446] ; 0x6e4080 / 0x6e2f90 branch-targets 0
raw LE dword of 0x684060 / 0x684180 / 0x53b460 / 0x684240 / 0x684290 / 0x5bf2b0 : [] (全部)
0x6840A1.. : 8a883006000084c90f85cb000000c680…     ← 时长≠0 的早退门
0x55D821.. : a130b2a8008b882c06000085c974            ← 冻结门只读 +0x62C
0x48CE62.. : a130b2a8008a88a2350000891da0eda800880d9ceda8   ← 镜像链
0x55D377.. : a080eda800c60558cdab0001                 ← 失焦等待环
== disp_hits(0xA8ED9C) R inside MLF/main-loop ==  仅 0x48ce73 一条 W，无 R
== any +0x62C access inside 0x684240..0x6842EF ==  (none)
```

---

*（本文件只写 `sections/Q3_SOURCES.md`；未修改任何只读母本、台账、`ra2youli\` 或 `swarm_20261104\` 下文件，未 commit。）*
