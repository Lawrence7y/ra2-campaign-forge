# E4_WRITER_CLOSURE_20261029 — 写者身份静态闭合（乙-1：0x6BEC72 宿主 B）

**日期**：2026-10-29 · 来源线 GOAL-3T X 退出线 E4（B 线实验矩阵 E4 卡片）
**性质**：只读静态反汇编闭合。零真机、零代码改动、零游戏运行。唯一新写文件=本稿；
临时脚本=`_e4w_closure.py`（本目录，分节 A0–B15，自写 PE 解析+139.4 万指令对齐解码+pred 图
+双向闭包+导入表解析，方法论对齐 R-061/R-062；未 import、未修改 C 线 `re_atlas/tools/_crev_engine.py`）。
**被审镜像**：`ra2youli/gamemd.exe`（本稿全部字节读自该副本；`ra2bench/gamemd.exe` 同哈希）。

## 0. 证据版本（自验）

- sha256(gamemd.exe) = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  **亲跑复核 PASS**（两副本同值）。与 XVERIFY_X_STATIC_20261026.md、_crev_engine.py 钉值一致。
- PE（自写解析）：ImageBase=0x400000，ENTRY=0x7CD80F，`.text=[0x401000,0x7E1000)`；
  `.data` 虚尺寸 0x367BE4 > 原始 0x6C000（尾部为 BSS）——0xA8ED80/0xA8EDD8/0xB73550/0x887368
  均在 BSS，**载入初值=0**。
- 对齐线性解码 1,394,120 条指令（与 C 线引擎「139 万」一致）；E8 头 6719 个、对齐 call 位点 68,244。
- **字节锚 12/12 亲读回验 PASS**（A1 节）：0x6BE08C/0x6BE0B6/0x6BE0E1/0x6BE0E7、
  0x6BEC60/0x6BEC6A/0x6BEC72/0x6BEC8C/0x6BEC9B、0x5D4D50、0x777809/0x777818——
  与 XVERIFY X2/X4/X5 逐字节一致，上游钉值有效。
- 关键 IAT（自解析导入表 372 项）：`0x7E14AC=PostMessageA`、`0x7E1444=PostQuitMessage`、
  `0x7E1214=ExitProcess`、`0x7E15DC=CoDisconnectObject`、`0x7E15D0=OleUninitialize`、
  `0x7E1384=OLEAUT32!#ord34`、`0x7E11E0=CloseHandle`、`0x7E11F0=Sleep`、`0x7E11DC=WaitForSingleObject`。

## T1. 0x6BEC72 所属函数边界 —— 宿主 B 头=0x6BEC60（异于宿主 A）

**方法**：`reach(site) ∩ E8头集`（后向 pred 闭包 ∩ 对齐 call 目标，R-061/R-062 同式）。

- 宿主 A 侧（0x6BE0B6 写 / 0x6BE0E1 判 / 0x6BE0DC 环头 / 0x6BE0E9 出环）：四点
  `reach ∩ HEADS = {0x6BB9A0}` **唯一**。**宿主 A 函数头 = 0x6BB9A0**。
  序言（16 字节）：`55 8b ec 6a ff 68 18 37 7f 00 68 d4 c1 7c 00 64`
  = `push ebp; mov ebp,esp; push -1; push 0x7F3718; push 0x7CC1D4; mov eax,fs:[0]…`
  ——标准 MSVC SEH 框架函数（大函数，闭包 3772 条指令）。
  **口径修正（红项 R1）**：设计书 §1b-B 称「宿主函数头 `0x6BE074 ret`/`0x6BE075 mov esp,[ebp-0x18]`」
  ——实读 0x6BE074/75 是 A **函数体内**的 SEH 展开尾（[ebp-0x18] 即 0x6BB9C6
  `mov [ebp-0x18],esp` 存的栈 cookie 槽），非函数头。X2 的字节判定不受影响。
- 宿主 B 侧（0x6BEC72 写 / 0x6BEC8C 判 / 0x6BEC87 环头 / 0x6BEC9D 出环）：
  `reach ∩ HEADS = {0x6BEC50, 0x6BEC60}` 两头。逐字节裁定（B4/B12/B13）：
  - **0x6BEC50 = `push ecx; call 0x7CBDDC` + 10×nop = exit(ecx) 存根**。0x7CBDDC 即 CRT exit
    实现（`push 0; push 0; push [esp+0xC]; call 0x7CBE1C…`，链终点 `0x7CBEB9 call [ExitProcess]`，
    exit 不返回）⇒ 其「穿入 0x6BEC60」是**线性布局伪边（死穿入）**，非真实控制边。
  - **真头 = 0x6BEC60**：`a1 50 35 b7 00 56 6a 00 6a 00 be 01 00 00 00 6a`
    = `mov eax,[0xB73550](hwnd); push esi; push 0; push 0; mov esi,1; push …`——
    **无帧序言**（仅 push esi 保存，尾 0x6BED4D `pop esi; 0x6BED4E ret`）。
  - 函数体 = **0x6BEC60..0x6BED4E**（fwd 闭包 72 条后继，闭包内**零间接 jmp** ⇒ B 的
    函数内控制流**全静态可闭合**；闭包内间接项全部是 `call dword ptr[...]` IAT/虚表调用）。
- **两写点不同函数**（0x6BB9A0 ≠ 0x6BEC60）：E4 卡片反证读数「0x6BEC72 与 0x6BE0B6 同属一函数
  ⇒ 两宿主前提翻」**不成立**——「两宿主」前提**字节级坐实**。

## T2. 宿主 B 函数内等待环结构 —— 有自有环；环体仅泵；环内无 ExitProcess

B 函数全貌（B4 转储，关键段）：

```
006BEC60: mov eax,[0xB73550]        ; hwnd            ← 函数头
006BEC65: push esi                  ; 保存 esi
006BEC66: push 0 / 006BEC68: push 0
006BEC6A: mov esi,1
006BEC6F: push 2                    ; Msg=2=WM_DESTROY
006BEC71: push eax                  ; hWnd
006BEC72: mov [0xA8EDD8],esi        ; ★闩=1（直线可达，进块即写）
006BEC78: call [PostMessageA]       ; PostMessageA(hwnd, WM_DESTROY, 0, 0)
006BEC7E: mov eax,[0xB73550]; test eax,eax
006BEC85: je 0x6BEC9D               ; 出口①：hwnd==0 → 跳过环
006BEC87: call 0x5D4D50             ; ★环头=继续泵
006BEC8C: cmp [0xA8EDD8],esi        ; 双检1：exitstate==1?
006BEC92: jne 0x6BEC9D              ; 出口②：≠1 → 出环
006BEC94: mov eax,[0xB73550]; test eax,eax
006BEC9B: jne 0x6BEC87              ; ★唯一回边（双检2：hwnd≠0 → 回环）
006BEC9D: …（出环尾段，见下）
```

- **自有环坐实**：回边普查（B6）= B 闭包内恰 2 条回边——`0x6BEC9B jne 0x6BEC87`（等待环）
  与 `0x6BED27 jne 0x6BED1C`（0x69E500 逐元素析构计数环，非等待）。环判据与 X4 双检
  0x6BEC8C / 0x6BEC94..9B 一一对应：**hwnd≠0 且 exitstate==1 才续转**。
- **环体仅 `call 0x5D4D50`（泵）**：无 Sleep、无 ExitProcess、无返回。
- **环后尾段（0x6BEC9D..0x6BED4E）无 ExitProcess**（B8：B 闭包 IAT 调用=
  PostMessageA/OLEAUT#34/CoDisconnectObject/OleUninitialize/PostQuitMessage/CloseHandle 族，
  **无 ExitProcess/TerminateProcess**）：
  `0x840A74` 检查→OLEAUT#34→`CoDisconnectObject(0x89A29C,0)`→`OleUninitialize`→
  `[0x887640]` 虚调用（+0x14 槽、slot0(1)，判空保护）→`mov [0x887640],0`→
  [0xb0bcf4] 析构环→**`PostQuitMessage(0)`@0x6BED3B**→`call 0x5DA720`→`call 0x6BE1C0`→`ret`。
  0x6BE1C0 虽位于 A 函数地址跨度内，但是**独立 E8 头、唯一调用者=0x6BED48（B）**，
  且后向包含性证明其代码**不可达** A 的写点/环（见 T3）。
- 对照宿主 A 的环（同构异判）：A 写 1（0x6BE0B6）→PostMessageA(hwnd,2)（0x6BE0D6）→
  环 `0x6BE0DC call 泵 / 0x6BE0E1 cmp [exitstate],edi / 0x6BE0E7 je 回环`——
  **A 等的是 exitstate 变为 ≠1**（即 C 块写 2），B 等的是 hwnd 死或 exitstate≠1。
  两环消费闩的共同机制 = **消息队列**：写者投 WM_DESTROY → WndProc 的 C 块
  （0x7777F3..0x77822，旧≠0 ⇒ `mov [0xA8EDD8],2`@0x777818）→ 写者环判据满足 → 出环。

## T3. 控制流汇合判定（关键）—— 完全独立；唯一方向边 A→B；B 的调用者无法再达 A

（B5/B9，前向闭包不穿 call）：

- `fwd(0x6BB9A0)`∩`fwd(0x6BEC60)` = **∅**（3772 vs 72 条指令，零共享指令）。
  A_write/A_cmp/A_loop ∉ fwdB；B_write/B_cmp/B_loop ∉ fwdA。
- **跨函数 jmp/jcc 边：双向均为 0 条**。
- **call 边 B→A：0 条**（B 的 4 个直接 callees=泵/0x5DA720/0x69E500/0x6BE1C0/0x7C8B3D，
  后四者调用者普查证明均不触及 A 头 0x6BB9A0）。
- call 边 **A→B：恰 1 条**（0x6BDCFE，见 T4-③）。
- **B 的调用者返回后不可能到达 A**（B9）：A 全镜像唯一调用点=0x7CD8EA（启动段，见 T4），
  B 的三个活调用者（0x5B3C20/0x647260/0x6BB9A0）在 callB 之后的可达集内**均无**对 A 头的
  调用（`after callB → callA reachable=[]` 三行全空）。
- 后向包含性补强：`reach(0x6BE0B6) ∩ HEADS = {0x6BB9A0}` 唯一 ⇒ 0x6BE1C0 等 A 跨度内的
  任何中间 E8 头**均无分支路径**通往 A 写点/环。

**结论（任务3三选一）**：**完全独立**。乙-1 主张的「主线程其后从未进入宿主 A 环」在
结构上**成立**：闩若由 B 写出，A 的 bail 站点 0x6BE0E1（只存在于 A 的环）没有任何
来自 B 函数或其调用者返回路径的进入通道。c″ 覆盖盲区**结构存在**。

## T4. 调用点普查（E8 直呼全查 + jmp 尾调 + 间接/数据引用 + 逐点上游门控）

**宿主 A（0x6BB9A0）**：E8 直呼**恰 1 处**；jmp 尾调 0；含头地址操作数的其他指令 0；
全镜像 raw abs32 命中 0。⇒ **A 是单入口主函数，只在启动段被调一次**：

```
007CD8E9: push eax
007CD8EA: call 0x6BB9A0        ; ←唯一调用点（enc=None；ENTRY=0x7CD80F 同区 CRT 启动链）
007CD8EF: mov [ebp-0x60],eax   ; 收返回值
007CD8F2: push eax
007CD8F3: call 0x7CBDDC        ; exit(status) → CRT → ExitProcess
```
即：A 返回 ⇒ 进程退；A 不返回 ⇒ 无出口。**验证+补全了 X 静态审计书的宿主 A 调用面**
（原书未列调用点清单；其 §1b-B 的「函数头 0x6BE074/75」误标已修正，见红项 R1）。

**宿主 B（0x6BEC60）**：E8 直呼 4 处，其中 **1 处为幻影（红项 R2）**；jmp 尾调 0；
间接/数据引用 0。**活调用点 = 3**：

- ① **0x5B3C70**（所属函数 0x5B3C20；上游 60 个调用者，含 A×2@0x6BD7EF/0x6BD81F）：
  ```
  005B3C58: mov eax,[0x81C1D0]
  005B3C5D: mov [esp+0x30],0x7E4C30        ; 函数指针槽（.data 值=0x4790E0）
  005B3C66: call [0x7E4C30]                ; 有效性回调([0x81C1D0])
  005B3C6C: test al,al / 005B3C6E: jne 0x5B3C7F   ; 真 → 跳过退出
  005B3C70: call 0x6BEC60                  ; ★假(0) → 宿主B（闩=1）
  005B3C75: mov ecx,1 / 005B3C7A: call 0x6BEC50   ; exit(1)
  ```
  语义：0x5B3C20 是通用对象构造方法（vptr 0x7EDF50，0x28 字节对象，60 调用者遍布
  0x406B10/0x530000/0x5301A0/0x530460×22/0x5349C0/0x534E50/0x534FA0/0x552CC0/0x699980/
  0x6BB9A0×2/0x788180/0x7AFB90/None×8）；**全局有效性回调（0x4790E0，检查 [0x81C1D0]
  与字节 [0x89E3A0]）返回假 ⇒ 调 B 优雅退 + exit(1)**。A 在自身 boot 段两次构造该对象
  （0x6BD7EF→[0x884E04]、0x6BD81F→[0x884E00]）⇒ **A 的初始化失败路径也会触发 B 写闩**。
- ② **0x64736D**（所属函数 0x647260；其唯一调用者=0x55D360，后者被 6 处调用：
  0x48CE8A/0x608206/0x60D407/0x62314E/0x623D72/0x624271）：
  ```
  00647260: mov al,[0xA8D5F8]; test al,2; je 0x6474C7      ; 场景旗标 bit1 门
  …0x54F000/0x54F050 键盘读（cmp ax,0x1B=ESC）；[0xA8D5F8] bit4；
   G_FRAME=[0xA8ED84]>0 检查；[0x887640] 虚调用与缓存 [0xAC50F8]/[0xAC5200] 比对；
   frame 与 [0xA8E30C] 阈值比较…
  0064736D: call 0x6BEC60                  ; ★条件满足 → 宿主B（闩=1）
  00647372: xor ecx,ecx / 00647374: call 0x6BEC50   ; exit(0)
  ```
  语义：**逐帧「自动退出」检查**（帧阈值/ESC/旗标位），读 G_FRAME——菜单/演示/片头类
  帧循环的自动退出路径，然后 exit(0)。
- ③ **0x6BDCFE**（宿主 A 函数体内）：
  ```
  006BDCAC: call [edx+0x70]                ; [0x887308] 对象虚槽28（对象=0x4BA770 工厂所建）
  006BDCB3: cmp eax,2 / sete al / mov [0x8175B0],al
  006BDCBE: test al,al / jne 0x6BDD03      ; 结果==2 → 跳过B
  006BDCFE: call 0x6BEC60                  ; ★结果≠2 → 宿主B（闩=1）
  006BDD03: call 0x5D4D50; mov al,[0xA8ED80]; test al,al; je 0x6BDD03   ; 自旋环1
  006BDD11: call 0x49F620; test al,al; jne 0x6BDD2E
            （否则 push 1; call 0x7CBDDC = exit(1)）
  006BDD2E: call 0x5D4D50; mov al,[0xA8ED80]; test al,al; je 0x6BDD2E   ; 自旋环2
  006BDD3C: …（直线流向退出序列准备段 0x6BDD3C..0x6BE08A）
  ```
- **幻影点 0x54A8C0**（红项 R2）：前 10 字节全 nop、再前为 `0x54A8B6 ret`；
  pred 链回溯 9 层全为 nop，无任何 E8 头/分支/数据引用可达，0x54A8C0 本身也**不在 HEADS**
  （无人调用它）⇒ **死代码调用点**（与 C 线 r038_e8_phantom 同族），B 的活调用面=3。

## T5. 场景态门控 + 早窗相容性

- **宿主 A 写点（0x6BE0B6）的门**：A 内部退出序列的位置门——上游直线区含
  `[0xa8f7ac]`、`[0xa8e960]` 位旗标（0x5295F0/0x529560 两次 INI 类读取后合成）、
  自旋旗标 `[0xA8ED80]`、对象 `[0x887308]` 虚槽==2 门。菜单/战斗的显式分支**未在静态面
  直接可名**（全局无符号），但 B 线事实（战斗关窗/就绪关窗不闩）与此结构相容：
  A 写点在 A 主流程的「决定退出」段，不在战斗/菜单空闲热路径上。
- **宿主 B 的三个活调用点全部是「退出请求/初始化失败/自动退出」类边路**：
  ① 全局有效性失败→构造期退出（boot 期可达：A 自己在 boot 段调 0x5B3C20）；
  ② 帧循环自动退出（读 G_FRAME，菜单/演示/片头帧环可达）；
  ③ A 内部条件调用（场景对象虚槽≠2 时）。
- **早窗相容**：闩时刻与加载进度同序（B 线 F5）与此结构相容——B 的①②路径都在
  boot→菜单过渡期的加载/帧环上，触发时刻天然受加载快慢调制；且 **A 的自旋环①**
  （0x6BDD03）在 hwnd==0 后**不可出**（见 T6-P1），其进入点恰在 B 调用（闩）之后。
- **决定性静态事实**：`[0xA8ED80]`（A 自旋旗标）全镜像**唯一写点 = 0x7778CE**，位于
  WndProc（0x7775C0）的 uMsg>0x18 消息处理链（pred 链直通 WndProc 头；门控
  `wParam==hwnd`@0x7778A0 且 lParam 变化@0x7778BF），其余 40+ 处引用全部是读。
  而**泵 0x5D4D50 头 `hwnd==0 ⇒ 直接返回不取消息`**（X1）⇒ **hwnd==0 后该旗标永远无法置位**
  （消息不再被取）。.data 初值=0（BSS）。

## T6. 判定输出

### 乙-1 判定：**结构存在（由「可能」升级）**，同时被两项新静态事实改形

1. **升级依据（字节级）**：
   - 宿主 B=独立函数 0x6BEC60..0x6BED4E，写闩点 0x6BEC72 直线可达（进块即写）；
   - 自有等待环 0x6BEC87..0x6BEC9B，判据双检与 X4 一致；
   - B 的控制流（含其全部调用者返回路径）**无任何通道**进入 A 环（T3 三重证明：
     闭包互斥/零跨边/调用者后继无 A 调用）；A 单入口 0x7CD8EA 已在启动时消费。
   - bail 站点 0x6BE0E1 只在 A 环内 ⇒ **闩若由 B 写，c″ 永不被询问——覆盖盲区坐实**。
2. **改形一（收窄）**：B 的两个外部调用者（0x5B3C20/0x647260）在 B 返回后**立即
   `exit(1)/exit(0)`**（0x6BEC50 存根 → CRT → ExitProcess）。「B 写闩后进程整体冻结」
   的挂点被收窄到：**B 尾段五步**（OLEAUT#34 / CoDisconnectObject / OleUninitialize /
   0x5DA720 / 0x6BE1C0）**或 CRT 退出析构链**——有界但逐个静态不透明（虚调用/外部 API）。
3. **改形二（新形态 P1，红项 R3）**：经 A 内部门 0x6BDCFE 的 B-调用变体——
   若场景对象虚槽 ≠2，A 调 B（闩=1 写出）→ B 立即返回（hwnd 已 0 ⇒ 环被跳过）→
   A 直落自旋环 0x6BDD03/0x6BDD2E（`call 泵; test [0xA8ED80]; je 自旋`）——
   hwnd==0 ⇒ 泵空转、旗标唯一写者 0x7778CE 永不可达 ⇒ **静态完备的无穷自旋**：
   闩=1、bail 站点未达、进程活、CPU 自旋。**写者=B，栈却落在宿主 A 函数内（bail 环之前）**。
4. **反证读数**：「0x6BEC72 与 0x6BE0B6 同属一函数/同一环」**被否证**（T1）；
   「宿主 B 路径必然汇入宿主 A 环」**被否证**（T3）。乙-1 不被静态削弱。

### 对假说表的影响

| 假说 | 影响 |
|---|---|
| **乙-1** | **结构存在（升级）**。但纯形式挂点收窄（改形一），且新增 P1 变体（改形二）。写者身份本身仍属运行期不可静态判定。 |
| **甲**（bail 已出环，teardown 阻塞） | 结构前提不变（要求写者=A：0x6BE0B6）。A 出环后 teardown 首段（0x6BE0E9..0x6BE15B 十余个析构调用 + OLE 尾段）与 B 尾段**共享同一组不透明调用**（OLEAUT#34/CoDisconnectObject/OleUninitialize）——「同一路径 1/3 阻塞」的挂点集合对甲/乙-1 部分重叠，静态不可分。 |
| **丙**（进入 A、写 1、首次 cmp 前阻塞） | 首次 cmp 前的 A 内区间被静态枚举收窄：写后段仅 0x6BE0BC..0x6BE0D6（0x720770/0x406D40/PostMessageA(空 hwnd 快速失败)）——**该窄段没有显性等待原语**，丙-原式先验下降；但 P1 显示「闩=1 且停在 cmp 之前的 A 内」可由**写者=B**造成，丙与乙-1 在栈面上不再互斥（见下）。 |
| **丁**（hook 在位性） | 不受本轮影响（E2 读 6 字节覆盖不变）。 |

**对 E2/E3 判读规则的增补（义务移交）**：
- E3 预注册读法「栈在宿主 A ⇒ 乙-1 死」**须精化**：栈返回地址 **≈0x6BE0DF**（A bail 环内）
  ⇒ 乙-1 死（原读法保留）；栈在 **0x6BDD08 / 0x6BDD33**（A 的 [0xA8ED80] 自旋环泵返回点）
  或 **0x6BDD16**（环间 0x49F620 返回点）
  ⇒ **写者身份未定**（可能是 B 经 0x6BDCFE 写的，P1 形态）；栈在 B 尾段/CRT 析构 ⇒ 乙-1-阻塞族；
  栈在 0x5B3C20/0x647260 的 exit 调用侧 ⇒ 同前。
- E2「CPU≈1 核自旋」读法新增第三落点：**A 的 [0xA8ED80] 自旋环（P1）**——先验上「自旋族」
  不再只指向「bail 环未出」。

### 红项/意外发现清单（5 项）

1. **R1**：设计书 §1b-B「宿主函数头 0x6BE074/0x6BE075」误标——实为 A 内 SEH 展开尾；
   真头 0x6BB9A0（SEH 序言）。X2 字节判定不受影响。
2. **R2**：宿主 B 的 E8 普查 4 点中 **0x54A8C0 为死代码幻影调用点**（ret+nop 垫后，无任何
   可达路径，自身亦无人调用）；活调用面=3。B 的 naive 双头 {0x6BEC50,0x6BEC60} 中
   0x6BEC50 是 exit(ecx) 存根（死穿入伪边）。
3. **R3**：新静态完备挂点 **P1**：A 自旋环 0x6BDD03/0x6BDD2E + 旗标唯一写点 0x7778CE
   （WndProc >0x18 消息链）+ 泵 hwnd==0 短路（X1）⇒ hwnd==0 后自旋环不可出；
   配合 0x6BDCFE 门控 B 调用构成「写者=B、栈在 A、闩=1」的完整机制。
4. **R4**：闩的消费通道是**消息队列**而非直接控制流（两写者都靠 PostMessageA(hwnd,WM_DESTROY)
   → C 块写 2 → 各自环判据放行）；两宿主在字节层是「同构异判」对（A 等 ==2 变化、B 等 hwnd 死或 ≠1）。
5. **R5**：exitstate 写 1 的两宿主均无直接 ExitProcess；进程级退出收敛于：A 返回→启动段
   exit(status)（0x7CD8F3）、或 B 的外部调用者 exit(0/1)（0x6BEC50 三调用者
   0x5B3C7A/0x647374/0x715871）、或 A 内 exit(1) 路径（0x7CBDDC 在 A 内 6 处）。
   全镜像直接 ExitProcess 引用仅 4 call + 1 jmp（0x4C858C/0x7CBEB9/0x7CD959/0x7CDA7C/0x7C8458），
   均不在两宿主闭包内。

## 局限（静态不可判部分，如实列）

1. **运行期写者身份**（A 写 vs B 写）：静态只证「两条结构通道都通、B 通道绕开 bail 站点」；
   观测趟中哪条 fired 不可静态判定（需 E3 栈采样或写者探针）。
2. **P1 的运行期可达性**：A 是否会在 hwnd==0 后仍走到 0x6BDCFE（场景对象 [0x887308]
   虚槽返回值、A 此刻所处状态机位置）——依赖运行期对象态，静态不可判。
3. **B 尾段五步与 CRT 退出析构链是否阻塞**（乙-1-阻塞族的最终挂点）：CoDisconnectObject/
   OleUninitialize/0x5DA720/0x6BE1C0/CRT doexit 内部静态不透明（虚调用+外部 API+析构表）。
4. **场景态显式命名**：0xA8D5F8/0x89E3A0/0x81C1D0/0x887308/[edx+0x70] 等门控全局无符号表
   支持，「菜单/战斗/加载」语义标签为形态推断（帧环/构造期/自旋结构），非字节级命名。
5. **间接跳转盲区**：全图 6719 头内所有 jmp 均有静态目标（间接 jmp 在两宿主闭包内为零，
   B 函数内为零）；但 WndProc 类表驱动入口（0x777A80 表）按 X3 口径人工解析，未入 pred 图——
   对本稿结论无影响（两写点/两环/调用面均不经表驱动）。
6. X5 对 exitstate 的 6 引用点/0 清零写者普查系上游既有结论，本轮引用未重扫
   （本稿全部字节锚与之对齐，12/12 复验通过）。

**方法与工件**：分析脚本 `_e4w_closure.py`（本目录；分节 A0 哈希/A1 锚/A2 解码/B3 边界/
B4 转储/B5 汇合/B6 回边/B7 调用普查/B8 IAT/B9 调用者汇合/B10 上游/B11 尾块/B12–B15 补查），
只读运行、只写 stdout；未触碰 _crev_engine.py、re_atlas 台账、gamemd.exe 及任何现有文件。

---

## 勘误注（2026-10-30，Leader 依 R-063a 复核代录·台账 §469）

R-063a（re_atlas/evidence/r063a_flag_writer_closure.md）复核发现本报告 T5 两处标签错位：
0x7778A0 实为「hwnd==全局主窗 [0xB73550]」判定（非『wParam==hwnd』）；0x7778BF 实为旗标新旧值
去重门（非『lParam 变化』）。锚地址与结论均不受影响——R-063a 的 WNDPROC 定名反而**加强**本报告
P1 闭合：旗标=窗口焦点态，写 1=WM_ACTIVATEAPP 激活沿，A 自旋环=等焦点恢复；hwnd==0 后泵短路、
激活沿永不达 ⇒ 挂死=等一个永不到来的焦点沿。原文保留追加式。
