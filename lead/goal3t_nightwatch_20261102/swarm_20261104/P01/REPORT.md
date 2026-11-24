# P01 · 帧冻结出口 0x55D877 定谳：+0x62C 是 ScenarioClass 挂起深度计数器，冻结出口是「单机局脚本化渐变/动作挂起」原语

一句话：MainLogicFrame(0x55D360) 的免-inc 出口 0x55D877 由 **GameMode∈{Campaign=0, Skirmish=5} ∧ dword[Scenario+0x62C]≠0** 双门开启；+0x62C 既非暂停布尔也非同步等待或跳帧，而是 **ScenarioClass 的挂起（hold/pause）深度计数器**，由「场景渐变黑屏状态机 + 触发器动作处理器 + 一个布尔沿触发对象」三处加一，由「MLF 的 PauseTimer 到期 + 渐变机收尾 + 同一布尔对象沿翻回」三处减一；冻结期间世界模拟链被整体跳过（任务标题"世界更新照跑"需修正为"渲染/泵/节流照跑"）。

---

## 0. 现场自证

| 项 | 命令/来源 | 结果 |
|---|---|---|
| 镜像 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` 只读打开（Engine 构造内强制 SHA 断言） | SHA256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` 与 `ra2tool.py:29` 期望一致 |
| 解码覆盖 | `python -I -X utf8 v0_selfcheck.py` → `eng.coverage` | **100.00% / 1,394,120 insns / resync=66**（重同步线性解码，非 G-23 假零口径） |
| 零真机 | `tasklist /FI "IMAGENAME eq gamemd.exe"`（shell 直跑 + v0 内 GBK 解码重跑各一次） | `信息: 没有运行的任务匹配指定标准。` —— 无 gamemd 进程 |
| IAT 锚 | `eng.resolve_iat(0x7E11F0)` / `(0x7E1530)` | `('KERNEL32.dll','Sleep')` / `('WINMM.dll','timeGetTime')`，与台账一致 |
| 基线复核 | v1 `disp_hits` 全镜像普查 | Frame 0xA8ED84: **1007 引用/10 写** ✓；Focus 0xA8ED80: **46/1（0x7778CE）** ✓；0xA8B230: **1293/3（0x52BA94/0x52BAB6/0x6BEB7D）** ✓；MLF rets = **{0x55D877, 0x55DEC7, 0x55DEDB}** ✓ |
| 免-inc 可达 | `eng.func_rets(0x55D360,0x55DEE0)` + `eng.reach_without(0x55D360,0x55DEE0,0x55DE73,0x55DE84)` | 不穿 INC 块可达 ret = **{0x55D877, 0x55DEDB}**，0x55DEC7 不可达 ✓ 与台账"冻结出口"口径一致 |

产物件（全部在本写域 `P01/`）：`v0_selfcheck.py`、`v1_mega.py`、`v2_deeper.py`、`v3_xrefs.py`、`v4_final.py`、`v5_render.py` 及落盘件 `A_mlf_body.txt / B_field62c.txt / C_write_A8B230.txt / C_write_A8B238.txt / E_callees.txt / S_strings.txt / F_hold_funcs.txt / H_xref_ctx.txt / I_final_dumps.txt / G_887324.txt / S2_strings.txt / stream_cache.pkl / v*_stdout.log`。

---

## 1. 结论（每条带证据级别）

1. **[字节]** 0x55D7C2..0x55D877 全段逐字节复核通过，探针路径全部命中；每个分支的 VA/条件/目标与字节双证（§2.1 全表）。
2. **[字节]** 探针省略号（0x55D7D4..0x55D821）里藏着一道**前置门**：`0x55D7DA mov al,[edi+0x630]`。+0x630 字节旗标=1 时才检查 PauseTimer 到期（到期才减计数）；旗标=0 时**直接跳过计时器块**去查计数器——这正是"无计时器挂起不被自动释放"的结构原因。
3. **[字节]** `[[0xA8B230]+0x62C]` 的语义定谳：**挂起（hold）深度计数器**。写点全集只有三处：复位 `mov [ebp+0x62C],ebx(0)` @0x6836D2；加一 `inc [eax+0x62C]` @0x684174；减一写回 `mov [ecx+0x62C],eax` @0x684195。任何"写常量 1/写帧号"的语义都被字节排除。
4. **[字节]** [0xA8B230] 不是"GameLogic"：三个写点证明它是 **ScenarioClass::Instance**（指针槽）——0x52BA60 单例构造函数里 `new 0x3740` → `call 0x6832C0` 构造 → 存入（YRpp `ScenarioClass.h:86` 记 ctor=0x6832C0，吻合）；0x52BAB6 分配失败置空；0x6BEB7D 全局析构置空。0x683610（被 ctor 调用）写 `[ebp+0x214]=0xF4240`（=1,000,000，YRpp 注释的 UniqueID 默认值）并引用源文件串 `"D:\ra2mdpost\Scenario.CPP"`（0x6835E1→0x83D838）。
5. **[字节]** 与 +0x62C 配套的字段族已全部定位并解出语义：**+0x614 ElapsedTimer**（挂起首挂时冻结：start 置 -1、已流逝累加进 [0x61C]；恢复时 re-arm @0x68422C）、**+0x620 PauseTimer**（start/[0x624]参2/[0x628]=时长秒×60，16ms 刻）、**+0x630 武装旗标 byte**、**+0x35A2 挂起态 byte**、**[0xA8ED9C] 全局镜像**、**[0xB054CC] 前态保存**、**[0xB07784] 追帧目标清零**。
6. **[字节+推导]** 计数器的加/减调用点全集（`call_sites` 全镜像）：
   - **加一（0x684060，"挂起请求"，ecx=时长秒）4 处**：0x53B612（渐变状态机 state-2 倒数到 1 时，`33 C9` → **时长=0，无自动释放**）；0x657CA0（对象布尔沿触发，`xor ecx,ecx` 同样时长=0）；0x6DF6FD 与 0x6E4080（`ret 0x10` 动作处理器小方法，**时长=字段 [obj+0x90]**，0x6E4080 由 `.data:0x872E78` 函数指针表项引用）。
   - **减一（0x684180，"释放"）3 处**：0x55D81C（MLF PauseTimer 到期）；0x53B6E6（渐变机 state-3 倒数到 0 收尾）；0x657CC8（同一布尔对象沿翻回）。
7. **[字节]** 冻结体（0x55D830..0x55D877）实际执行集 = {0x5D4D50 消息泵（HWND 0xB73550 + G_PUMPCNT 0xAA0430++ + PeekMessage/IsDialogMessage/TranslateAccelerator/TranslateMessage 族，IAT 已解）, 0x48D080, 0x53B560 渐变机, `[0x887324]` 渲染单例 vtable+0x5C 虚调, 0x4F4480, 0x55E160 节流}；**正常体 28 个唯一调用目标（含全部世界更新链）被整体跳过**。返回值与正常体同式 `al = ([0xA8E9A0]==0)`（0x55D86D sete al），调用方主循环（0x48CE8A）无法靠返回值区分冻结帧。
8. **[推导]** 0x55E160（台账名"LogicUpdate"）是 **MainLoop 帧节流/FPS 累加器**（SP 分支用 [0x887348]/[0x887350] 定时 + Sleep（经 `mov edi,[0x7E11F0]`+`call edi`）；写 [0xA8E314] 时间债累加、[0xABCD40..] FPS 计数），两条路径共用，不是世界模拟。任务标题"帧号不推进，但世界更新照跑"应修正为：**帧号不推进、世界模拟跳过，但渲染/渐变/消息泵/节流照跑**。
9. **[推测→强]** 渐变机加计数点的调用者 0x6DFAC5/0x6E2F96 与动作处理器 0x6DF6FD/0x6E4080 同处 0x6DExxx–0x6E4xxx 的 `ret 0x10` 同构函数族区（.data 0x872A7C 起连续 .text 指针表、相邻方法间距 0x226 字节），判为**触发器/脚本动作处理器区**；「表槽序=动作号」未做真机或外部锚验证，仅给槽位 `.data:0x872E78 → 0x6E4080`。

---

## 2. 证据（逐条 VA + 字节 + 推导链）

### 2.1 冻结段逐字节复核（0x55D7C2..0x55D877，全部出自 resync 流 A_mlf_body.txt）

| VA | 字节 | 指令 | 语义 | 分支目标复核 |
|---|---|---|---|---|
| 0x55D7C2 | `A1 38 B2 A8 00` | `mov eax,[0xA8B238]` | Session::GameMode（YRpp SessionClass.h:54；Unsorted.h 亦别名 GameMode） | — |
| 0x55D7C7 | `85 C0` | `test eax,eax` | | — |
| 0x55D7C9 | `74 09` | `je 0x55D7D4` | Mode==**0=Campaign** | 0x55D7C9+2+9=0x55D7D4 ✓ |
| 0x55D7CB | `83 F8 05` | `cmp eax,5` | | — |
| 0x55D7CE | `0F 85 A4 00 00 00` | `jne 0x55D878` | Mode≠**5=Skirmish** → 正常体 | 0x55D7CE+6+0xA4=0x55D878 ✓ |
| 0x55D7D4 | `8B 3D 30 B2 A8 00` | `mov edi,[0xA8B230]` | ScenarioClass::Instance | — |
| 0x55D7DA | `8A 87 30 06 00 00` | `mov al,[edi+0x630]` | **前置门：武装旗标**（探针省略号内的门） | — |
| 0x55D7E0 | `84 C0` | `test al,al` | | — |
| 0x55D7E2 | `74 3D` | `je 0x55D821` | 旗标=0 → 跳过计时器块 | 0x55D7E2+2+0x3D=0x55D821 ✓ |
| 0x55D7E4 | `8B 87 20 06 00 00` | `mov eax,[edi+0x620]` | PauseTimer.start | — |
| 0x55D7EA | `8B B7 28 06 00 00` | `mov esi,[edi+0x628]` | PauseTimer 目标（时长） | — |
| 0x55D7F6 | `83 F8 FF` | `cmp eax,-1` | start==-1 哨兵 | — |
| 0x55D7F9 | `74 10` | `je 0x55D80B` | 未武装→视作到期 | 0x55D7F9+2+0x10=0x55D80B ✓ |
| 0x55D7FB | `8D 4F 04` | `lea ecx,[edi+4]` | 计时器 this | — |
| 0x55D7FE | `E8 3D B4 16 00` | `call 0x6C8C40` | 时钟：`FF 15 30 15 7E 00; C1 E8 04; C3` = **timeGetTime()>>4，16ms/刻** | — |
| 0x55D803 | `2B 07` | `sub eax,[edi]` | elapsed（16ms 刻） | — |
| 0x55D805 | `3B C6` | `cmp eax,esi` | | — |
| 0x55D807 | `7D 06` | `jge 0x55D80F` | elapsed≥目标 → 到期 | +6=0x55D80F ✓ |
| 0x55D809 | `2B F0` | `sub esi,eax` | 剩余 | — |
| 0x55D80B | `85 F6` | `test esi,esi` | | — |
| 0x55D80D | `7F 12` | `jg 0x55D821` | 剩余>0 → 计时未到，不减 | +0x12=0x55D821 ✓ |
| 0x55D80F | `8B 15 30 B2 A8 00` | `mov edx,[0xA8B230]` | | — |
| 0x55D815 | `C6 82 30 06 00 00 00` | `mov byte [edx+0x630],0` | **清武装旗标** | — |
| 0x55D81C | `E8 5F 69 12 00` | `call 0x684180` | **释放：counter--（减到 0 触发恢复块）** | — |
| 0x55D821 | `A1 30 B2 A8 00` | `mov eax,[0xA8B230]` | | — |
| 0x55D826 | `8B 88 2C 06 00 00` | `mov ecx,[eax+0x62C]` | **读挂起计数器** | — |
| 0x55D82C | `85 C9` | `test ecx,ecx` | | — |
| 0x55D82E | `74 48` | `je 0x55D878` | counter==0 → 正常体 | 0x55D82E+2+0x48=0x55D878 ✓ |
| 0x55D830 | `E8 1B 75 07 00` | `call 0x5D4D50` | 消息泵 | — |
| 0x55D835 | `E8 46 F8 F2 FF` | `call 0x48D080` | 输入/会话处理（正常体 0x55DE4A 同款） | — |
| 0x55D83A | `E8 21 DD FD FF` | `call 0x53B560` | 渐变状态机（冻结期间继续走） | — |
| 0x55D83F | `8B 0D 24 73 88 00` | `mov ecx,[0x887324]` | 渲染单例（new 0xE18→ctor 0x6D1C20，场景开始重建 @0x6853BF） | — |
| 0x55D845 | `8B 11` | `mov edx,[ecx]` | vtable | — |
| 0x55D847 | `FF 52 5C` | `call [edx+0x5C]` | present 类虚方法（LogicUpdate 焦点循环 0x55E269 同款） | — |
| 0x55D84A | `B9 E8 F7 87 00` | `mov ecx,0x87F7E8` | | — |
| 0x55D84F | `E8 2C 6C F9 FF` | `call 0x4F4480` | present 链（26 处调用点，LogicUpdate 0x55E271 同款） | — |
| 0x55D854 | `E8 07 09 00 00` | `call 0x55E160` | 帧节流（两条路径共用；唯一 2 调用点 0x55D854/0x55DE9A） | — |
| 0x55D859 | `8A 0D A0 E9 A8 00` | `mov cl,[0xA8E9A0]` | InGame | — |
| 0x55D85F | `33 C0` | `xor eax,eax` | | — |
| 0x55D861..71 | `5F 5E 84 C9 5D C6 05 58 CD AB 00 00 0F 94 C0 5B 81 C4 B4 01 00 00` | pop/`mov byte [0xABCD58],0`/`sete al`/pop/`add esp,0x1B4` | 返回值 al=(InGame==0)；[0xABCD58] 每帧尾清零 | — |
| 0x55D877 | `C3` | `ret` | **冻结出口** | — |

MLF 早退口（对照）：0x55D360 读 [0xA8E9A0]，==0 → 0x55DECF..0x55DEDB `mov al,1; ret`（台账第三出口）。正常尾 INC 块 0x55DE73/7E/81 字节见 A_mlf_body.txt；`eng.reach_without` 复算免-inc 可达 ret={0x55D877,0x55DEDB}。

### 2.2 +0x62C 家族 18 处命中分档（B_field62c.txt 全量；判据=capstone mem.disp==0x62C）

**A 档：基址链到 [0xA8B230]（ScenarioClass+0x62C，6 处，全部 [字节+链]）**

| VA | R/W | 指令 | 基址链 |
|---|---|---|启发式 prov=GLOBAL230 + 窗口字节直读 |
| 0x55D826 | R | `mov ecx,[eax+0x62C]` | ←0x55D821 `mov eax,[0xA8B230]` |
| 0x6840BC | R | `mov eax,[edx+0x62C]` | ←0x6840B6 `mov edx,[0xA8B230]` |
| 0x684174 | **W** | `inc [eax+0x62C]` | ←0x68416F `mov eax,[0xA8B230]` |
| 0x684186 | R | `mov eax,[ecx+0x62C]` | ←0x684180 `mov ecx,[0xA8B230]` |
| 0x685..→0x684195 | **W** | `mov [ecx+0x62C],eax` | ←0x684180 链（dec 后写回） |
| 0x6841A0 | R | `mov ecx,[eax+0x62C]` | ←0x68419B `mov eax,[0xA8B230]`（减到 0 复查触发恢复块） |

**B 档：Scenario 同族字段（disp=0x630/同函数簇，[字节]）**：0x55D815 W byte[+0x630]=0；0x6840AF W byte[+0x630]=1；0x6836D2 W [ebp+0x62C]=ebx(0)、0x6836D8 W byte[ebp+0x630]=bl(0)（Scenario.CPP 重置点：函数 0x683610，`[ebp+0x214]=0xF4240`=1,000,000 UniqueID 默认值 + `"D:\ra2mdpost\Scenario.CPP"` @0x6835E1→0x83D838 + 被 ctor 0x6832C0 调用 @0x6833DB；ebp=Scenario 三重锁定）。

**C 档：非本字段（12 处，逐个排除，禁止合并）**：0x41D435（基址=虚调 [edx+0x84] 返回值，0x61C/0x620/0x62C 连读的其他类）；0x4F11BF（[esp+0x62C] 栈参数）；0x665EDE W,5 与 0x71106E W,ebx（两个其他类构造器清块，含 0x3FE99999 浮点 imm；0x665650 即 0x8871E0 单例的 ctor）；0x67181C/0x671836（INI 解析对象 esi，0x5276D0 解析器）；0x6E10D1/0x6E1147/0x6E1B50（基址←**[0x8871E0]**，0x18C0 大小单例的 +0x62C，绘制用途）；0x714622/0x71463F（ebp 对象 INI 解析，0x843Bxx 串）。

### 2.3 写点与三个 [0xA8B230] 写点上下文（C_write_A8B230.txt）

- **0x52BA94** `A3 30 B2 A8 00` `mov [0xA8B230],eax`：0x52BA60 单例构造函数（`mov eax,0x2F30; call 0x7CA650` __chkstk 0x2F30 帧）：`push 0x3740; call 0x7C8E17`（operator new，**对象大小 0x3740**）→ `mov ecx,eax; call 0x6832C0`（**ctor，=YRpp ScenarioClass ctor**）→ 存实例。同函数随后 `push 0x18C0; call 0x7C8E17` → ctor 0x665650 → 存 [0x8871E0]（伴生单例）。
- **0x52BAB6** `89 1D 30 B2 A8 00` `mov [0xA8B230],ebx(0)`：分配失败路径置空。
- **0x6BEB7D** `89 1D 30 B2 A8 00` `mov [0xA8B230],ebx(0)`：全局析构 `push esi; call 0x7C8B3D`(delete) 后置空。
- **0x684060 全函数**（挂起请求，`sub esp,0xC; push esi; esi=ecx`=时长）：
  - 时长≠0：`call 0x6C8C40`（now，16ms 刻）→ `[0x620]=now, [0x624]=[esp+8]=参2, [0x628]=时长×60`（esi*15*4），置 [0x630]=1（已在 1 则直接退出**不加计数**，0x6840A9 jne 0x68417A）；
  - 计数==0 首挂：`call 0x406F00`；SP 判别（Mode 0/5）；**冻结 ElapsedTimer**：若 [0x614]≠-1 → 已流逝累加进 [0x61C]、[0x614]=-1；保存 [0x35A2]→[0xB054CC]；若原为 0：call 0x6938C0(0x87F7E8)、[0x887640] vtbl+0x28（=0 则 vtbl+0xC）、[0x35A2]=1、[0xA8ED9C]=1、call 0x54F720（泵）、[0xB07784]=0；
  - 尾：`inc [eax+0x62C]`。
- **0x684180 全函数**（释放）：counter==0 直接返回；counter-- 写回（0x684194/95）；再读==0 → 恢复块：若 [0xB054CC]==0 且 [0x35A2]==1 → `[0x887640] vtbl+0x28` 循环 drain（非 0 才 vtbl+0x10）、[0x35A2]=0、[0xA8ED9C]=0、0x54F720、[0xB07784]=0；若 [0x614]==-1 → `[0x614]=now`（ElapsedTimer re-arm）；`call 0x406F40`。
- **0x683610**（Scenario.CPP 场景启动/重置，被 ctor 0x6832C0 @0x6833DB 调用）：[0x20C]/[0x210]=0x2BB、**[0x214]=0xF4240**、[0x60C]/[0x610]=1、重置 ElapsedTimer(+0x614)与 PauseTimer(+0x620)、**[0x62C]=0、[0x630]=0**、再以 CurrentFrame 为基准武装 [0x11E8] 帧计时器。
- **0x684240 / 0x684290**（无计数器版挂起态置/清，配 [0xB07784] 追帧）：渐变启动器 0x53B460 尾调 0x684240（[0x35A2]=1、[0xA8ED9C]=1、[0xB07784]=0、鼠标 drain）；渐变收尾/MLF 追帧点（0x53B722、0x55DE8F）调 0x684290（清 [0x35A2]/[0xA8ED9C]/[0xB07784]）。

### 2.4 渐变状态机（0x53B560，两调用点 0x53A747/0x55D83A）

状态槽 [0xA9FAB0]（0..3，ja 退出）+ 倒计数 [0xA9FA98]：
- **state1**（0x53B575）：`32 C9` xor cl,cl → 0x53BBA0(0)，计数--; ==0 → state=2、计数=0x2D(45)（0x53B58D/0x53B597）；
- **state2**（0x53B5A2..）：逐刻计算调色板色（[0x88731C] 对象 vtbl+0x10，调色板对象 0x886FA0），计数--; **==1 → 0x53B610 `33 C9` XOR ECX,ECX → call 0x684060**（时长=0 挂起；原始字节 eng.rd(0x53B610)=`33 c9 e8 49`，capstone 在 E_callees.txt 里把 33 C9 的 op_str 印成 "cl, cl" 是工具渲染噪音，32 位语义以原始字节为准）；
- **state2→3**（0x53B617..）：计数==0 → 恢复 [0xA9FA98]=[0xA9FAA8]、state=3；
- **state3**（0x53B6CE..）：倒数到 0 → **call 0x684180 释放** + 调色板恢复 + 若 [0xA9FAD1]（渐变前是否已挂起）==0 → call 0x684290 清挂起态。
- 启动器 **0x53B460(ecx=渐变刻数)**：≤0 直接返回；new 0x24 状态对象→[0xA9FA9C]；存 [0xA9FA98]=[0xA9FAA8]=ecx；state=1；存 [0xA9FAD1]=[Scenario+0x35A2]；调 0x684240。**调用者 2 处：0x6DFAC5、0x6E2F96（动作处理器区）**。

### 2.5 主循环与节流（对照用）

- 主循环 @0x48CE40 区：每帧前置 `[0xA8ED9C] ← [Scenario+0x35A2]`（0x48CE67/0x48CE73），然后 `call 0x55D360`（0x48CE8A），al 为真才 0x55CFD0，否则 0x48C8B0 后继续 loop 0x48CE8A。
- 0x55E160：SP(Mode 0/5) 分支 0x55E2B4 用 [0x887348]/[0x887350] 定时+Sleep（edi=[0x7E11F0]=Sleep，`call edi`）；网络分支 0x55E1BC..0x55E2AC 有 [0xA8EDA0]/[0xA8ED80] 条件等待循环；尾 0x55E33B.. FPS 累加（0xABCD40..，每 0x3C=60 次结算）；引用文件串 MainLoop.CPP 的 assert 在紧邻函数 0x55E420（0x55E4F5→0x82A170）——0x55E160 本体无串，文件归属为邻接推断。

---

## 3. 与本仓既有记载的对账

| 项 | 既有记载 | 本次复核 | 裁决 |
|---|---|---|---|
| 0xA8ED84 1007 引用/10 写 | 台账基线 | 1007/10，写点 10 处含 0x55DE81 | **一致** |
| 0xA8ED80 46 引用/唯一写 0x7778CE | 台账基线 | 46/1 | **一致** |
| 0xA8B230 "GameLogic 指针" 1293/3 | 任务基线口径 | 1293/3 数目一致；但身份=**ScenarioClass::Instance**（ctor 0x6832C0+大小 0x3740+UniqueID 0xF4240+Scenario.CPP 串三重字节证据；YRpp ScenarioClass.h:58/86） | **命名冲突，纠正**：本仓 `docs/re/ARCHITECTURE_ATLAS.md:2138/2157` 亦记 ScenarioClass::Instance，与本次一致；任务基线的 "GameLogic" 为误名 |
| MLF 3 rets / 免-inc 可达 | 台账基线 | 完全一致 | **一致** |
| G_TICKTGT=0x887330 "LogicUpdate 目标间隔" | ra2tool.py:40 | 0x55E1C7/0x55E216 读 [0x887330]，与台账吻合 | **一致**（"LogicUpdate"=0x55E160 节流器） |
| 任务标题"帧号不推进，但世界更新照跑" | 任务书 | 帧号不推进 ✓；但世界模拟链（正常体 28 调用目标）**被跳过**；照跑的是泵/输入/渐变/present/节流 | **措辞纠正**（见 §1.8） |
| G_HWND 0xB73550 / G_PUMPCNT 0xAA0430 | ra2tool.py:38-39 | 0x5D4D50 头部 `mov eax,[0xB73550]`、`inc [0xAA0430]` 字节可见 | **一致** |

## 4. 诚实账

**没做的：**
1. 渲染单例 [0x887324] 的 vtable+0x5C 具体方法未解到函数名级（ctor 0x6D1C20 前 0x40 字节未见 vtable imm，vtable 存储在更深处；仅确认对象身份、重建点与调用形态）。0x48D080、0x4F4480、0x6938C0、0x406F00/0x406F40、0x54F720 等只有头部/局部字节画像，未做全函数定名。
2. 动作处理器区 0x6DF6FD/0x6E4080 的**动作号**未定谳（表基 0x872A7C 槽 255 仅是序数；未做外部锚或真机验证 0x6DFAC5/0x6E2F96 两调用者的具体动作语义）。
3. 0x657CA0 所在对象（字段 +0x14BC/+0x14BD/+0x14D9）未定名，其布尔沿触发挂起的业务入口（caller 0x653446）只追了一跳。
4. 未做 [reg+0x62C] 以外的间接访问形态排查（如 rep movsd/memset 整对象拷贝、或经 [0xA8B234] 等指针副本的访问）——若存在将不计入 18 处命中。
5. 零真机铁律下，所有"挂起实际发生"的 UX 场景（哪张地图/哪个触发器）无法验证，只给了静态判据。

**样本薄的：** 渐变机 state0/state1 的上游语义（0x53BBA0、0x53A6C0 效果函数的完整调用网）只做了一跳；0x8871E0 伴生单例（0x18C0，ctor 0x665650）只有定位级证据。

**可能出错的：**
1. `0x53B610 = 33 C9` 按 x86 规范判为 `XOR ECX,ECX`（时长=0）——capstone 的 op_str 曾渲染成 "cl, cl"，我以原始字节为准；若我的 x86 解码判断有误，渐变挂起将带一个垃圾时长计时器，但"counter+1 → 冻结"主链不受影响。
2. §1.9 的"动作处理器区"归类是强推测（结构证据：同构 ret 0x10、等距 0x226、指针表），未到函数名级。
3. 函数头集合用 ret 扫描+E8 目标（G-83 口径），个别 fstart（如 0x683610 自身非头、0x53B560 为头）已人工复核；0x683610 所在函数的**尾**未圈（0x683800 内无 ret）。
4. provenance 启发式（向后 48 指令线性追踪）在 call 边界即放弃——A 档 6 处全部有窗口字节直读兜底，但 C 档个别归档依赖"该对象另有 ctor/INI 上下文"的旁证。
5. v0 脚本曾把 tasklist 的 GBK 输出按 UTF-8 解码而抛 UnicodeDecodeError（失败在打印层，非检查层）；已改 GBK 重跑成功。pickle 缓存（stream_cache.pkl）被 Mimosa 标记"不安全反序列化"（建议级）——缓存件为本会话自产自用，未跨信任边界。

**与既有记载冲突的：** 任务基线把 [0xA8B230] 称作 GameLogic——本任务以字节证据（ctor VA、对象大小、UniqueID 常量、源文件串、repo 图集）纠正为 ScenarioClass::Instance，其余数目口径全部一致。

## 5. 复算入口

```bash
# 环境：仓库根 D:/Project/ra2-campaign-forge，只读 gamemd.exe
cd lead/goal3t_nightwatch_20261102/swarm_20261104/P01
python -I -X utf8 v0_selfcheck.py        # coverage/SHA/tasklist/IAT（~2min，引擎全量解码）
python -I -X utf8 v1_mega.py             # 全量取证落盘 A/B/C/E/S + 基线对账（~4min）
python -I -X utf8 v2_deeper.py           # 0x684060/0x684180/0x683610 全函数 + 时钟 + IAT（读 v1 缓存，快）
python -I -X utf8 v3_xrefs.py            # inc/dec 调用点上下文 + 渐变启动器（读缓存）
python -I -X utf8 v4_final.py            # 动作处理器/表槽/追帧对（读缓存）
python -I -X utf8 v5_render.py           # 渲染单例 + 正常/冻结体调用普查（读缓存）
# 单点验证（示例）：
python -I -X utf8 -c "
import sys; sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine
eng = Engine()
print(eng.coverage)                        # 必须 100.00% / 1394120
print(eng.disasm(0x55D7C2, 0x100))         # 冻结段
print(eng.disp_hits_field(0x62C))          # 18 处家族
print(eng.rd(0x53B610, 4).hex())           # 33c9e849 -> XOR ECX,ECX
"
```

**真机判据（零真机约束下仅给判据，本次未执行）**——授权真机趟件时按序读：
1. `dword [0xA8B230]` → `dword [+0x62C]`：≠0 即冻结出口生效（主判据）。
2. `byte [+0x630]`：=1 表示带 PauseTimer 的挂起（读 [+0x620]/[+0x628] 可得剩余：`(timeGetTime()>>4)−[+0x620]` vs `[+0x628]`，16ms/刻）；=0 而 +0x62C>0 为无计时器挂起（渐变/沿触发/动作路径），只能等显式释放。
3. `byte [+0x35A2]` 与 `byte [0xA8ED9C]`：=1 =挂起态镜像（主循环 0x48CE73 每帧从 +0x35A2 刷新）。
4. `[0xA9FAB0]`/`[0xA9FA98]`：渐变状态机 state/counter——若 state∈{1,2,3} 且计数递减，冻结伴随渐变黑屏；若 state=0 而 +0x62C>0，冻结来自动作处理器直接挂起（0x6DF6FD/0x6E4080/0x657CA0 路径）。
5. `dword [0xA8B238]`：走冻结路径时必为 0（战役）或 5（遭遇战）；若为其他值则 +0x62C 门根本不会被评估（证伪同步等待假说）。
6. `dword [0x887348]`/`[0x887350]`：0x55E160 节流锚点（台账 G_TICKLAST/G_TICKTGT 邻域），确认冻结帧仍被节流而非空转。
7. 证伪"ESC 菜单暂停"：无渐变（[0xA9FAB0]=0）且无动作事件时 +0x62C 自发 >0，则查 [0xB054CC] 前态与调用栈。
