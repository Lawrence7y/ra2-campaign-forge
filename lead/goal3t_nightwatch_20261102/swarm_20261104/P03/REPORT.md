# P03 · CurrentFrame 10 写点全归因：「唯一 inc」三重复核成立（0x55DE7E→0x55DE81），但存读档存在 disp 普查之外的间接写路径；ATLAS §8.4 两处需修正

分析域：`lead/goal3t_nightwatch_20261102/swarm_20261104/P03/`
母本：`ra2youli/gamemd.exe`（只读，SHA-256 前缀 `73201cc021497c95` 校验通过，零改动）
证据分级：**[字节]** = 反汇编字节/数据行直接读取；**[推导]** = 字节 + CFG/调用链推导；**[推测]** = 明写猜测。

---

## 0. 现场自证

1. **零真机**：`tasklist | grep -i -E "gamemd|ra2loader|YURI"` → 无输出（grep exit=1）。未启动、未注入、未读任何进程内存。
2. **引擎自证**（`_p1_baseline.py`，共享引擎 `ra2tool.Engine`）：
   ```
   sha256 = 73201cc021497c95 ... (期望 73201cc021497c95)   ← 冻结母本一致
   .text  = [0x401000, 0x7e1000)  size=0x3e0000
   coverage = 100.00% / 1394120 insns / resync=66          ← 逐址+1 重同步线性解码，非裸 capstone 流
   ```
3. **基线复算**（同脚本）：`disp_hits(0xA8ED84)` → **total=1007，W=10，R=997**，与已定谳基线一致。
4. **10 写点逐字节比对**（同一脚本输出）：
   ```
   0x52da08  891d84eda800           mov [0xA8ED84], ebx
   0x55de81  891584eda800           mov [0xA8ED84], edx
   0x5b7329  c70584eda80000000000   mov dword [0xA8ED84], 0
   0x5bb20c  892d84eda800           mov [0xA8ED84], ebp
   0x5e550f  893584eda800           mov [0xA8ED84], esi
   0x5e747c  c70584eda80000000000   mov dword [0xA8ED84], 0
   0x68466b  893584eda800           mov [0xA8ED84], esi
   0x686765  892d84eda800           mov [0xA8ED84], ebp
   0x795234  c70584eda80000000000   mov dword [0xA8ED84], 0
   0x79758c  a384eda800             mov [0xA8ED84], eax
   ```
   三处锚点字节：0x55DE73=`8b1584eda800`（读）、0x55DE7E=`42 3bc7`（inc edx）、0x55DE81=`891584eda800`（写回）。
5. **全量账目闭合**：`84 ed a8 00` 在 .text 出现 **1009 次** = 1007 个 disp 操作数 + **2 个 push 立即数**（0x67F819、0x67FA19，见 §2.4）。无其它隐藏形态。

---

## 1. 结论（每条带证据级别）

| # | 结论 | 级别 |
|---|------|------|
| C1 | 10 个写点全部归因完毕（宿主函数、值来源、守卫、调用链，见 §2.1）。定界用 E8 头集（6719 目标）+ CFG 可达 + 全镜像前驱向后爬（非 call 边）三法互证，9 个写点的最小入口=头−0x1 对齐填充；未用 ±0x200 线性窗。 | [字节+推导] |
| C2 | **「唯一 inc」主张成立**：全镜像 10 个写点 mnemonic 全部为 `mov`（无 `inc [mem]`/`add [mem],imm` 直接形式）；唯一读-加-写链 = 0x55DE73 `mov edx,[g]` → 0x55DE7E `inc edx` → 0x55DE81 `mov [g],edx`（14 字节内闭合）。MLF 另两处读（0x55D3BB/0x55D8C9）均不流向任何写回。 | [字节] |
| C3 | **9/10 写点写的是 0**：W1/W5/W7 寄存器来自紧邻 `xor reg,reg`；W3/W6/W9 是字面常数 `c7 05 ... 00000000`；W8 的 ebp 来自 `xor ebp,ebp`(0x68675F)；**W4 的 ebp 经 341 条指令反向切片证明唯一写点=0x5BACBE `xor ebp,ebp`**（两处 pop ebp 均在以 ret 结尾的终路上）。即除读档序列化外，本镜像不存在"把任意非零值写进 CurrentFrame"的代码。 | [字节+推导] |
| C4 | **存在 disp 普查之外的第 11 条（间接）写路径**：2 处 `push 0xA8ED84`（0x67F819 槽+0x10 / 0x67FA19 槽+0xC）把 CurrentFrame 当 4 字节缓冲交给流对象虚方法，属存/读档字段序列化；读档侧会把存档中的帧值写进 CurrentFrame（帧号跳变为存档值）。两宿主 0x67F7E0/0x67F9C0 序列化同一组全局（[0xA8ED78]/[0xA83D4C]/[0xA8ED84]/[0x89EA40]/[0x89EC28]/[0x89ECC0]/[0xA8E3A8]/[0xB07784]）。 | [字节+推导，槽方向映射为推测] |
| C5 | **W10 宿主 0x7970D0 是死代码**：函数 [0x7970D0,0x7975AC) 在全镜像零静态引用（立即数/跳转表项/rel32/重定位均无 0x7970D0；无 call/jmp 静态入边）。其写点 0x79758C 在本镜像运行时不可达。 | [字节+推导] |
| C6 | **measure 窗（局内战斗）判定**：dispatcher 0x48CCC0（ebx=0@0x48CCD4）帧循环 `0x48CE8A call MLF ↔ 0x48CE8A`（回边 0x48CEA8 je）每轮 +1（W2，受四旗标门控）；循环出口打 `Game loop finished. Average FPS = %d`（0x81D514，除以 [0xABCD4C]）——该循环即每逻辑帧一轮。其余写点全部位于四旗标触发的转换支线（见 C7），触发时帧号**清零**：造成"跳变到 0"，不是跳到任意 N。 | [推导] |
| C7 | **冻结/跳变的控制机制闭环**：0x55CFD0 = 旗标状态机（4 个写块 0x55D123/0x55D1B1/0x55D219/0x55D25C，把 [0xA8ECD0]/[0xA83D49]/[0x8B41C0]/[0xA83D48] 四旗标与 bl(=0) 比对，不一致者触发对应路径 0x685670/0x685DC0/0x6863E0/0x686570 并清零四旗标、置 [0xABCD58]）；MLF 里四旗标任一非零 → `jne 0x55DEC8` → 跳过 inc → `mov byte [0xABCD58],0` → ret 0x55DEDB(al=1)。`reach_without(0x55D360,0x55DEE0,0x55DE73,0x55DE84)` 复核：绕开 inc 块可达 ret = {0x55D877, 0x55DEDB}，**与基线一致**。 | [字节+推导] |
| C8 | **ATLAS §8.4 地址勘误（必须修正）**：散文句"全镜像唯一定常递增写入点位于 0x0055DE73"错误——0x55DE73 是 `mov edx,[0xA8ED84]`（读，字节 8B 15 84 ED A8 00）。正确：**自增执行点 0x55DE7E（字节 42），写回点 0x55DE81（字节 89 15 84 ED A8 00）**。§8.4 自己贴的代码块标注的正是 0x55DE7E——散文与代码块自相矛盾。 | [字节] |
| C9 | **ATLAS §8.4"9 处均为载入地图、读取存档或开局清零"需修正**：10 个 disp 写点中**没有一处是"读取存档"**——真正的读档写路径是 C4 的 vtable 序列化（不在 10 写点内）。逐点判定见 §2.3：载入地图 ✓（W7/W8）、开局清零 ✓（W1）、其余 5 处（W3/W4/W5/W6/W9）更准确归为"任务/会话转换复位"，W10 是死代码。 | [推导] |
| C10 | 0x4068E0 与 0x6B8B10 均为 1 字节 `ret` 空桩（周边 nop 雪橇），W1/W4/W6/W7 宿主内所有 `push fmt; call 0x4068E0` 无副作用——与 ATLAS §8.6 已定谳结论一致，但格式串仍可用作流程意图证据（`ModemHost.StartGame(enter)`、`Pregame setup for %d players.`、`.SED`、`LOADING` 等）。 | [字节] |

---

## 2. 证据（逐条 VA + 字节 + 推导链）

### 2.1 十写点归因总表

定界方法：E8 头集（`call rel32` 目标，6719 个唯一目标）候选 → `func_rets` 出口枚举 → 全镜像非 call 边前驱向后爬找"无入边入口"；两法互证。**边界均经分支图验证**（W2 的 [0x55D360,0x55DEE0) 3 ret 与基线一致；W6 宿主 [0x5E7460,0x5E74E0) 内 0 ret、以 `jmp 0x6B8B10` 收尾@0x5E74D9，0x5E74E0 是下一函数头 `sub esp,0x1F8`）。

| 写点 | 宿主函数 [head, next) | rets | E8 调用者 | 值来源 | 守卫/时机 |
|---|---|---|---|---|---|
| 0x52DA08 | [0x52D9A0, 0x52F3F0) init | 15 | 2（0x48CDD3/0x48CFAA，均在 dispatcher 0x48CCC0） | ebx=0（xor@0x52D9C4） | 无守卫，init 直线清零块；同块置 INGAME=1@0x52D9D7、清四旗标@0x52DA78-8D、[0xA8B24C]=2@0x52E3D2 |
| 0x55DE81 | [0x55D360, 0x55DEE0) MainLogicFrame | 3（0x55D877/0x55DEC7/0x55DEDB）✓基线 | 6（0x48CE8A@0x48CCC0 帧循环 + 0x608206/0x60D407/0x62314E/0x623D72/0x624271） | edx=读-改-写（inc） | 四旗标 [0xA83D49]/[0xA8ECD0]/[0x8B41C0]/[0xA83D48] 任一非零 → jne 0x55DEC8 → [0xABCD58]=0 → ret 0x55DEDB(al=1) |
| 0x5B7329 | [0x5B7090, 0x5B7360) | 3 | 1（0x5B65BF@0x5B6020） | 字面 0 | 前置等待环 0x5B724D↔0x5B72C2（时间源 0x6C8C40，cmp 0x708/0x3C，泵 0x48D080/0x5D4D50/0x5F1C60）；环退出后 [eax+0x1254]=[0xA8B254]、[0xA8B24C]=2、call 0x6B8B10(空桩) |
| 0x5BB20C | [0x5BAC60, 0x5BB290) ModemHost.StartGame | 5 | 1（0x5B7903@0x5B77E0 ← init 0x52D9A0 + 0x5EF240×2） | ebp=0（反向切片证明，见 §2.2） | bl==1 早退 ret 0x5BACB0（'LoadGame = %s' 分支）；否则直线到写点；同块 [0xA8B24C]=2 |
| 0x5E550F | [0x5E3D10, 0x5E5F10) | 4 | 3（0x5E0D12@0x5E00B0；0x7A6DEE/0x7A7F07@0x7A41A0 ← 0x785410@0x786390） | esi=0（xor@0x5E54E5） | 宿主为 GetDlgItem/SendMessageA(edi=[0x7E14A4]@0x5E54B0, msg 0x4B2) UI 流；写块 [eax+0x1254]=0xFFFFFFFF、[0xA8B24C]=2；调用侧门控 [0xAC0268]==0 / eax∈{1,2,3} |
| 0x5E747C | [0x5E7460, 0x5E74E0) PregameSetup 助手 | 0（尾 jmp 0x6B8B10@0x5E74D9） | 5（0x5C4BB3@0x5C3EC0；0x5DD2C8/0x5DD488@0x5DC350 ← init；0x7955F4@0x794BA0；0x79759B@0x7970D0） | 字面 0 | 打 'Pregame setup for %d players.'(0x831A60)；[eax+0x1254]=[0xA8B254]、[0xA8B24C]=2 |
| 0x68466B | [0x684620, 0x684C30) .SED 场景加载器 | 2 | 1（0x683D21@0x683AB0 ← init 0x52D9A0×2 + 0x685670/0x685DC0/0x6863E0） | esi=0（xor@0x684669，写点前 2 字节） | **函数入口直线无守卫，每调用必清零**；strlen+复制文件名、'.SED'(0x83DA88)、[ecx+0x3598]=1、[0xA8E7AC]++ |
| 0x686765 | [0x686730, 0x686890) | 3 | 1（0x6849C9，在 W7 宿主内） | ebp=0（xor@0x68675F） | `call [0x7E4C30]`(=0x4790E0) 返回 al；al!=0 → 写点。0x4790E0：arg==−2 或 [0x89E3A0]==1 → al=1（[0x89E3A0] 唯一写者 0x52F7AF@0x52F3F0） |
| 0x795234 | [0x794BA0, 0x795650) 会话复位 | 4 | 1（0x7800EC@0x77F900；0x77F900 有 39 个调用者横跨 0x76xxxx-0x7Axxxx UI 族） | 字面 0 | 写点前 rep stosd 清扫 + [0x841F30..0x841F3C]=1234..1237；写点后 GameMode([0xA8B238]) 读取、call 0x5E7460@0x7955F4；调用侧守卫 [0xB77E28]==2 && [0xB77E27]!=0 && [0xB77E26]==0 |
| 0x79758C | [0x7970D0, 0x7975AC)（死代码） | 1 | **0（全镜像零静态引用）** | eax=0（xor@0x797541） | 静态不可达；内含跳转表 `jmp [eax*4+0x7975AC]`/`+0x7975C4`；'FrameSendRate is %d'/'LatencyFudge is %d' |

职责判定依据（格式串均在宿主函数内被 push）：W4 宿主打 `ModemHost.StartGame(enter)`(0x82CC04)、`LoadGame = %s`(0x82CBF4)、`D:\ra2mdpost\ModemHst.cpp`(0x82C9A4)；W7 宿主邻接 `.SED`(0x83DA88)；W7 的调用者 0x683AB0 push `LOADING`(0x82C1BC)；W6 宿主打 `Pregame setup for %d players.`(0x831A60)；W10 宿主打 `FrameSendRate is %d`(0x84C540)、`LatencyFudge is %d`(0x820C54)；dispatcher 循环尾打 `Game loop finished. Average FPS = %d`(0x81D514) 与 `ExceptionReturnStack/Address = %08X`(0x81D55C/0x81D53C——init 有 SEH 包装)。以上字面串 [字节]；流程命名 [推导]。

### 2.2 ★「唯一 inc」复核（核心攻击）——成立

三重独立检查：

1. **写点形态**：10 个写点 mnemonic 全为 `mov` [字节]。直接内存 RMW（`inc [g]`=FF /1、`add [g],1`=83 /0）若有，会以 W+`inc`/`add` mnemonic 出现在 disp_hits——不存在。
2. **逐宿主读点审计**（1007 引用落盘 `_hits_gframe.txt` 逐点核对）：
   - 其余 9 个宿主函数在写点之前**0 处** [0xA8ED84] 读；
   - MLF（唯一有写点前读的宿主）3 处读：
     - 0x55D3BB `mov eax,[g]` → `cmp eax,[0xA8E2E4]`(静态 0，全镜像无写者) → `jl 0x55D3D4` 不跳 → GameMode 分支 + `call [0x7E1530]`(timeGetTime) 存 [0xA8B55C]——**不流向写回**；
     - 0x55D8C9 `mov eax,[g]` → `and eax,7` / `cmp al,7`（每 8 帧）+ `GameMode==4` → call 0x542520——**不流向写回**；
     - 0x55DE73 `mov edx,[g]` → 0x55DE79 `mov eax,[0xB07784]` → **0x55DE7E `inc edx`** → 0x55DE7F `cmp eax,edi` → 0x55DE81 `mov [g],edx`——**唯一读-加-写**。
3. **W4 的 ebp 追源（反向切片）**：在 [0x5BAC60,0x5BB290) 内建非 call 边前驱图，从 W=0x5BB20C 反向爬取得 341 条能到达 W 的指令；切片内 ebp 写点唯一 = 0x5BACBE `xor ebp,ebp`（切片内另 4 条含 ebp 的指令均为**从** ebp 取值的 store：[0xA8B54C]/[0xA8DB9C]/[0xA8B56C]/[0xA8B570] ← ebp）。→ **W4 写 0**，airtight。

补充：MLF 尾部 `jne 0x55DEC8` 落点 `mov byte [0xABCD58],0; pop…; mov al,1; ret 0x55DEDB`——四旗标非零时不 inc 且返回 al=1。`eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)` 输出：绕开 inc 块可达 ret = `['0x55d877', '0x55dedb']`，与已定谳基线逐位一致。

### 2.3 ★ push 0xA8ED84（间接写路径，ATLAS 未计）

- 0x67F819（宿主 0x67F7E0，槽 **+0x10**）与 0x67FA19（宿主 0x67F9C0，槽 **+0xC**）：同款形态 `push 0; push 4; push 0xA8ED84; push esi; call [vtable+slot]`，后随 `test eax,eax; jl 错误路径`（0x67F9B8 / 0x67FD11）。
- 两宿主序列化**同一组全局**（§2.1 表外清单 [字节]）：[0xA8ED78]、[0xA83D4C]、[0xA8ED84]、[0x89EA40]、[0x89EC28]、[0x89ECC0]、[0xA8E3A8]、[0xB07784]——典型的整局状态存取块。
- 方向推断 [推导，槽映射为推测]：0x67F9C0（+0xC）在流读取 [0xA8ED78] **之后**调 0x6CF240(0xB0C110, 缓冲) 做校验/变换两次（0x67F9E8/0x67FA0E）——"读后验"次序指向 **Load 侧**；0x67F7E0（+0x10）无校验调用，指向 **Save 侧**。若 +0xC 槽为 Read，则读档瞬间 CurrentFrame 被写为存档帧值（4 字节缓冲直写）。调用者：0x67F7E0←0x67D300←0x67CEF0；0x67F9C0←0x67E730←0x67E440（各 1 条链，无字符串可指认，编排器身份 [推测]）。
- **影响**：「全镜像仅 10 处写入」的字面表述在**间接写**意义上不完整；但「唯一**定常自增**点」不受影响（序列化是覆盖写，不是 +1）。

### 2.4 measure 窗内可达性（任务 3）

- 帧=measure 窗本体：dispatcher 0x48CCC0（`xor ebx,ebx`@0x48CCD4 → bl 恒 0）循环：
  ```
  0x48CE8A call 0x55D360     ; MainLogicFrame（W2 在此 +1，四旗标门控）
  0x48CE8F test al,al
  0x48CE91 je 0x48CE9C
  0x48CE93 call 0x55CFD0     ; 旗标状态机(bl=0)
  0x48CE98 test al,al
  0x48CE9A jne 0x48CEAA      ; 出口 → 'Game loop finished. Average FPS = %d'
  0x48CE9C call 0x48C8B0
  0x48CEA1 call 0x55CFD0
  0x48CEA6 test al,al
  0x48CEA8 je 0x48CE8A       ; 回边：每逻辑帧一轮
  ```
  0x55CFD0 头部即读 [0xA8ED84]（`test eax,0x3FF`@0x55CFD8——每 1024 帧周期逻辑，纯读）。
- 旗标→转换→清零链：四旗标任一非零（由 0x4F7870/0x4C6CB0/0x48C8B0 等菜单/网络侧写者置位）→ MLF 跳过 inc（**冻结**）→ dispatcher 的 0x55CFD0 四变体之一触发 0x685670/0x685DC0/0x6863E0（三者各 1-2 处 call 0x683AB0 加载器）或 0x686570（'Disconnect_Gracefully'，不加载）→ 加载链内 W7/W8（或 W3/W5/W6 转换族）**清零** CurrentFrame 且置 [0xA8B24C]=2（加载相位）→ 旗标清零 → 恢复 +1。
- **判定**：局内稳态唯一周期写点 = W2（+1 步进）。W3/W5/W6/W7/W8 可由玩家在局内发起的转换（重玩/下一关/读档/断线）触发——它们产生"**跳变到 0**"而非"冻结"，且 [0xA8B24C]=2 与 f==0 同时出现 = 「f[0]==0 加载段型」的来源指纹；**不存在跳到任意非零 N 的代码路径**（唯一非零来源 = 读档序列化的存档帧值）。W1 是循环前开局；W9 是退出/复位；W10 不可达。

### 2.5 三处写 0 的时机（任务 4）

- **0x5B7329**（W3 宿主 0x5B7090）：任务/关卡转换。前置等待环（0x5B724D↔0x5B72C2：0x6C8C40 时间源，`cmp esi,0x708`(1800) 继续 / `cmp esi,0x3C`(60) 退出），环内泵 0x48D080/0x5D4D50/0x5F1C60；退出后清零。上层：0x5B6020 ← 0x5B49B0 ← **init 0x52D9A0** + 0x5EF240×2。
- **0x5E747C**（W6 宿主 0x5E7460）：Pregame setup 助手（'Pregame setup for %d players.'），5 条会话启动/重开路径的共同收尾（0x5C3EC0、0x5DC350×2、0x794BA0、0x7970D0），尾 jmp 0x6B8B10（空桩）。
- **0x795234**（W9 宿主 0x794BA0）：会话复位/退出级。调用侧守卫 `[0xB77E28]==2 && [0xB77E27]!=0 && [0xB77E26]==0`@0x7800D1-0x7800EA；宿主内 rep stosd 清扫 + 1234..1237 四连常量 + 写点后调 W6 助手@0x7955F4。0x77F900 有 39 个调用者（0x76xxxx-0x7Axxxx UI 族）。

---

## 3. 与本仓既有记载的对账

| 记载 | 对账结果 |
|---|---|
| 基线：1007 引用 / 10 写 / 唯一定常 inc 0x55DE7E + 写回 0x55DE81 | **✓ 全部复算一致**（coverage 100.00%/1394120/resync=66；W=10、R=997；字节逐位吻合） |
| 基线：MLF 3 ret（0x55D877/0x55DEC7/0x55DEDB），0x55D877 与 0x55DEDB 不经 inc 可达 | **✓** `reach_without` 复核输出 {0x55D877, 0x55DEDB} |
| 基线：0x7E11F0=Sleep / 0x7E1530=timeGetTime | **✓** resolve_iat 复核一致；0x55D3D4 `call [0x7E1530]` 即 MLF 内 timeGetTime |
| 基线：焦点旗标 0xA8ED80 唯一写者 0x7778CE | 未复核（本轮范围外，未动） |
| 基线：[0xA8B230] GameLogic 1293 引用 / 3 写 | 未复核（范围外）；本轮仅在宿主内大量读到其使用，无冲突 |
| ATLAS §8.4「全镜像唯一定常递增写入点位于 0x0055DE73」 | **✗ 地址错误**：0x55DE73=`mov edx,[g]`（读）。inc=0x55DE7E，写回=0x55DE81。§8.4 自带代码块的标注（0x55DE7E ★）是对的，散文句错——**勘误：正确地址 0x0055DE7E（自增）/0x0055DE81（写回）** |
| ATLAS §8.4「9 处均为载入地图、读取存档或开局清零」 | **△ 需修正**：载入地图 ✓（0x68466B/0x686765）、开局清零 ✓（0x52DA08）；**"读取存档"在 10 个 disp 写点内无对应**——读档写路径是 push 0xA8ED84 的 vtable 序列化（0x67F9C0 侧）；W3/W4/W5/W6/W9 应归「任务/会话转换复位」（任务重开 / ModemHost.StartGame / UI 开局 / PregameSetup / 会话复位）；W10=死代码 |
| ATLAS §8.6（0x4068E0 空桩、1672 直呼、无副作用） | **✓ 一致**；0x6B8B10 亦为同类空桩（本轮新证） |

---

## 4. 诚实账（没做的 / 样本薄的 / 可能出错的 / 冲突）

**没做**：
- 全部真机动态验证（铁律禁止）。所有"时机/触发"结论为静态 CFG + 调用链推导。
- 未复核基线中 0xA8ED80 写者、[0xA8B230] 计数（范围外，声明未动）。
- MLF 中 `cmp eax,edi`@0x55DE7F 的 **edi 值未定谳**：[0x55DC5C,0x55DE7F) 内 edi 无任何显式写（仅 rep movs 推进），最后可见赋值 0x55DC4F `mov edi,edx`（'.sav' 串复制的栈缓冲指针）；但 `mov [0xB07784],edi`@0x55DE94 与地图族写者全存 0（0x684165/0x68420D/0x684282/0x6842E5）的组合提示这是"载后一次性触发"型机制。**路径敏感追踪未闭合，此项 [推测]**，不影响 C2（唯一 inc）结论。
- 0x6CF240（校验/变换）与 0x4790E0（W8 守卫）语义未定谳（仅字节级行为：0x4790E0 arg==−2 或 [0x89E3A0]==1 → al=1）。
- W3 根链 0x5B49B0、W5 对话根 0x786390 只追到 2-3 层，未到进程入口。

**样本薄/可能出错**：
- 序列化槽方向（+0xC=Read / +0x10=Write）为 [推测]——依据"读后校验"调用次序推断，未拿到该流对象虚表静态定谳；若方向颠倒，则 C4 中"存侧/读侧"标签互换（push 0xA8ED84 的存在与"间接写路径存在"不受影响——两者必有一个方向写穿缓冲）。
- W4 宿主、W5 宿主的"职责命名"基于格式串 + 调用形态 [推导]，未到函数名符号级。
- resync=66：66 字节未被指令消费（数据/对齐），disp_hits 基于该流；若这 66 字节内藏有未被流覆盖的写点形态（如数据化代码），理论漏检——已用字节序列计数（1009=1007+2）交叉排除 [0xA8ED84] 相关漏检，但其它全局不在本任务范围。
- 0x55CFD0 的 bl 参数 = dispatcher `xor ebx,ebx`@0x48CCD4 的静态推断；已核对 [0x48CCC0,0x48CEA8) 内无 ebx 写点，但循环体外的间接依赖未穷举。

**与既有记载的冲突**：仅 ATLAS §8.4 两处（C8 地址勘误、C9 归类修正）；无其它冲突。本轮所有写入仅发生在 `P03/` 目录；未改台账、未动 re_atlas/、未 commit。

---

## 5. 复算入口

全部脚本位于 `lead/goal3t_nightwatch_20261102/swarm_20261104/P03/`，运行方式 `python -I -X utf8 <脚本>`（零真机、只读母本）：

| 脚本 | 复算内容 |
|---|---|
| `_p1_baseline.py` | coverage 自证 + 1007/10 复算 + 10 写点字节 + 三锚点字节 |
| `_p2_funcs.py` | E8 头集（6719）+ 写点宿主定界 + ret 枚举；产出 `_hits_gframe.txt`（1007 引用全量） |
| `_p3_79758c.py` | 0x79758C 上下文 + 6 候选头不可达证据 |
| `_p4_chain.py` | 落空链回走（块级定界第二视角） |
| `_p5_predclimb.py` | 全镜像非 call 边前驱爬取（找无入边入口；0x7970D0 入口集=跳转表目标） |
| `_p6_7970.py` | 0x7970D0 头（`sub esp,0x42C`）+ 跳转表 + 0x7970D0 全文件指针搜索（零命中） |
| `_p7_perview.py` | 10 写点逐点上下文/读点距离/守卫/回边 |
| `_p8_deep.py` | MLF 尾部 + reach_without 冻结出口 + 0x55D3BB/0x55D8C9 读点去向 + W4 ebp 全 listing + 0x5E7460 真尾 |
| `_p9_callers.py` | 13 调用点归属 + dispatcher 头/回边 + W6 尾 + W4 反向切片 + W3 等待环 |
| `_p10_globals.py` | 0x6B8B10/0x4068E0 空桩 + 四旗标写点 + 全局槽普查 + IAT + 0x7970D0 指针搜索 |
| `_p11_strings.py` | 格式串 + [0xA8E2E4]=0 + [0x7E4C30]=0x4790E0 + 0xA8B24C 写值 + 上层调用链 |
| `_p12_final.py` | 帧循环字节 + 0x55CFD0 四变体 + 立即数隐写检查（2 处 push）+ 字节计数 1009 |
| `_p13_pushptr.py` | push 0xA8ED84 现场 + MLF edi 写点清查 + dispatcher 循环头 + 0x684290/0x686570 |
| `_p14_saveload.py` | 序列化两宿主（0x67F7E0/0x67F9C0）+ 序列化清单 + ebx=0 + [0xB07784] 写者 |

最小复算（三行核心）：
```python
import sys; sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine
eng = Engine(); print(eng.coverage)          # 100.00% / 1394120 / 66
print(len(eng.disp_hits(0xA8ED84)))          # 1007
print(eng.rd(0x55DE7E, 1).hex())             # '42'  ← inc edx
```
