# R-063a · 旗标写点闭合 —— [0xA8ED80] 唯一写式 0x7778CE 写者身份静态闭合

**日期**：2026-10-29 · 来源线 RE-ATLAS R-063a（服务主线②退出线 D-11/E2/E3 判读）
**性质**：只读静态反汇编闭合。零真机、零游戏启动、零代码改动。既有文件全部只读未触碰。
**新写文件**：本稿 + `re_atlas/tools/_r063a_probe1..4.py`（临时脚本，只写 stdout）+ 各 `_out.txt`。
**方法论**：对齐 _crev_engine 口径——自写 PE 解析（节表 VA→file）+ 139.4 万条对齐线性解码
（与 C 线/E4 的 1,394,120 完全一致）+ E8 头集 6719 + pred 图 + 后向闭包 + 前向闭包 +
raw abs32 全镜像扫描 + IAT 自解析；未 import、未修改 `_crev_engine.py`。

---

## 0. 证据版本（自验）

- sha256(`ra2youli/gamemd.exe`) = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  **亲跑 PASS**（`ra2bench/gamemd.exe` 同值）。
- PE（自解析）：ImageBase=0x400000；`.text=[0x401000,0x7E038D)`（raw 0x3E0000）；
  `.data` 虚尺寸 0x367BE4 > raw 0x6C000 ⇒ **0xA8ED80/0xA8ED81/0xAA0430 均在 BSS，载入初值=0**。
- 正控复验：exitstate `0xA8EDD8` raw abs32 命中恰 **6** 处（0x6BE0B6/0x6BE0E1/0x6BEC72/
  0x6BEC8C/0x777809/0x777818），与 X5 独立普查逐点一致 ✓。
- 旗标 `0xA8ED80` raw abs32 命中恰 **46** 处，全在 `.text`（`.detour`/`.rsrc`/`.data` 0 处）：
  **45 读 + 1 写**。唯一写式 = **0x7778CE：`a2 80 ed a8 00` = `mov byte ptr [0xA8ED80], al`**
  （亲读字节 `a280eda800` PASS）——E4 R3 的起点坐实并加严（46 > E4 的「40+」口径）。

---

## T1. 0x7778CE 所属函数边界 —— 主窗口过程，头=0x7775C0（OS 调用，镜像内零调用点）

**方法适配**：写点后向 pred 闭包（65 节点）∩ E8 头集 = **∅**——这不是边界失效，而是
**该函数是窗口过程，不被镜像内任何代码调用**（0 条 E8/jmp/jcc 入边）。改用冷头条款
（同 _crev_engine 对 0x529394 的处理）三重定头：

1. **闭包根唯一**：后向闭包的「无 pred 根」只有一个线性地址 `0x7775BC`——逐字节裁定为
   **伪根**：`0x7775B4: 50 / 0x7775B5: ff 15 cc 13 7e 00 (call [USER32!SetFocus]) /
   0x7775BB: c3 (ret)`，随后 `0x7775BC..BF = 90 90 90 90`（4 字节对齐填充）。
   线性解码把填充 nop 当作「落入 0x7775C0 的指令」，pred 图故无根。**真头 = 0x7775C0**。
2. **寄存器平衡自洽**：头 `0x7775C0..0x7775CF` 压 `ecx,ebx,esi,edi`（且 `xor ebx,ebx`
   置 0 常量），全部 9 个出口 `pop edi/esi(/xor eax)/pop ebx/pop ecx` + `ret 0x10`
   ——4 压对 4 弹、`ret 0x10` = stdcall 四参（hwnd,uMsg,wParam,lParam）✓。若头在
   0x7775BC 则压弹失衡，不可能。
3. **邻居头泄漏排除**：下方最近 E8 头 0x777420、上方最近 E8 头 0x777AC0 的前向闭包
   均不含写点（False/False）。

**头部字节钉**（0x7775C0 起 16 字节）：
`51 8b0d28768800 53 33db 56 3bcb 57 7457`
= `push ecx; mov ecx,[0x887628]; push ebx; xor ebx,ebx; push esi; cmp ecx,ebx; push edi; je 0x777627`
——frameless（无 ebp 帧），esp 寻址，头即查 `[0x887628]` 单例。

**函数体范围** = **[0x7775C0, 0x777A7D)**：前向闭包 273 条指令，最高指令 0x777A7A
（`c21000 ret 0x10`，止于 0x777A7D）；下一 E8 头 0x777AC0 之前为填充/独立函数。

**尾形态**：9 个出口全部 `ret 0x10`（0x777624/0x777684/0x777871/0x77789D/0x77794F/
0x777982/0x7779DA/0x777A61/0x777A7A）；闭包内**恰 1 条间接 jmp** =
`0x7776AE: ff 24 95 80 7a 77 00  jmp dword ptr [edx*4 + 0x777A80]`（uMsg≤0x18 的
6 槽跳转表，槽表 0x777A80、case 字节表 0x777A98，idx=uMsg−1）；表驱动块
（0x7776B5/0x777781/0x77778D/0x7777CE/0x7777F3 等）因此不在前向闭包内，但其字节
均落在函数体范围内。**uMsg>0x18 的处理链（0x77782B..0x777A7A）为纯静态可达**。

**定名判定**（字符串锚，不强行）：全镜像对头值 0x7775C0 的 raw 引用**恰 1 处**——
`0x777C79: c7 44 24 28 c0 75 77 00  mov dword ptr [esp+0x28], 0x7775C0`，即
WNDCLASS.lpfnWndProc 槽（WNDCLASS 栈对象：`[esp+0x24]=style 3`、`[esp+0x2C..0x30]=0`、
`[esp+0x48]=0x849F48`），紧接 `0x777CA5 call [USER32!RegisterClassA]`，随后
`0x777CD0/0x777D78 call [USER32!CreateWindowExA]`（类名与窗口名**同一字符串
0x849F48 = `"Yuri's Revenge"`**），返回值两处均 `mov [0xB73550], eax`
（0x777CD6 / 0x777D7E）。
∴ **0x7775C0 = "Yuri's Revenge" 主游戏窗口的窗口过程（WndProc）**；由 USER32
消息分派调用，镜像内无调用点。注册函数头 = **0x777C30**
（`sub esp,0x38`；reach(0x777C79)∩HEADS={0x777C30} 唯一；其后向闭包根 0x777C24
同为 ret+90 填充伪根）。

---

## T2. 写点上下文 —— 写 1 的语义条件 = 「主窗口收到 WM_ACTIVATEAPP(wParam≠0) 且旗标旧值≠新值」

### T2.1 上游逐指令钉（0x77782B → 0x7778D3，全部亲读字节）

```
00777687: 8b442418        mov eax,[esp+0x18]      ; eax=uMsg（栈位见 T2.3 自洽证明）
0077768B: 83f818          cmp eax,0x18
0077768E: 0f8797010000    ja 0x77782B             ; uMsg>0x18 → 长消息链
00777694: 0f84c1030000    je 0x777A5B             ; uMsg==0x18 → 直接收尾 ret 0
…（uMsg≤0x18 走跳转表 0x7776AE，不在本链）…
0077782B: 3d05020000      cmp eax,0x205
00777830: 0f8724010000    ja 0x77795A
00777836: 0f8416010000    je 0x777952             ; uMsg==0x205(WM_RBUTTONUP) → mov byte[0x884D34],bl
0077783C: 83f81c          cmp eax,0x1c            ; ★ uMsg==0x1C = WM_ACTIVATEAPP
0077783F: 745f            je 0x7778A0             ; ★ 唯一入写路径
00777841: 3d12010000      cmp eax,0x112           ; WM_SYSCOMMAND 分支（0xF020→[0xA8ED81]=1、
00777846: 0f856d010000    jne 0x7779B9            ;   0xF120→[0xA8ED81]=bl(0)），不触 0xA8ED80
007778A0: 3b3d5035b700    cmp edi,[0xB73550]      ; 门①：参数 hwnd == 全局主窗 hwnd
007778A6: 0f859d000000    jne 0x777949            ;   非主窗 → 直接收尾 ret 0
007778AC: 8b44241c        mov eax,[esp+0x1C]      ; eax=wParam（激活参数）
007778B0: 33c9            xor ecx,ecx
007778B2: 3bc3            cmp eax,ebx             ; ebx=0（头部置定，闭包内无重写）
007778B4: 0f95c1          setne cl                ; cl = (wParam != 0) = 新值
007778B7: 33d2            xor edx,edx
007778B9: 8a1580eda800    mov dl,[0xA8ED80]       ; dl = 旗标旧值
007778BF: 3bd1            cmp edx,ecx             ; 门②：旧值 == 新值？
007778C1: 0f8482000000    je 0x777949             ;   相同 → 跳过写，直接收尾 ret 0
007778C7: 3bc3            cmp eax,ebx
007778C9: 0f95c0          setne al                ; al = (wParam != 0)   ← al 的唯一定义点
007778CC: 3ac3            cmp al,bl               ; 置 ZF=(al==0)，供写后分支用
007778CE: a280eda800      mov [0xA8ED80],al       ; ★★ 全镜像唯一写式
007778D3: 755b            jne 0x777930            ; al!=0(激活沿) → 0x777930；al==0(失焦沿) → 直落
```

**al 来源链闭合**：al 只由 `0x7778C9 setne al` 定义，其输入 eax 由 `0x7778AC mov
eax,[esp+0x1C]` 装载，门① `0x7778A6 jne` 之后 eax 无重定义——
**al ≡ (wParam != 0)**。

### T2.2 写 1 / 写 0 的语义条件（字节级）

- **写 1** 当且仅当：uMsg==0x1C（WM_ACTIVATEAPP）∧ hwnd 参数==[0xB73550]（主窗）
  ∧ wParam≠0（**被激活**）∧ 旗标旧值==0（状态沿去重，0x7778BF..C1）。
- **写 0** 同门但 wParam==0（**被停用**）。
- **写到 0 或 1 皆只发生在这条链上**；其余 44 处引用全部为读（`a0/8a 15/80 3d/38 1d`
  四种读形 + 0x7778B9 本链读），无 inc/and/or/xor 等隐写形（对齐解码逐条核过）。
- **激活沿后继（al=1 → 0x777930）**：`call 0x777420`（**Focus_Restore 处理器**：串
  `'Focus_Restore()\n'`@0x777420 头、`'Focus_Restore(): _MouseCaptured = %s\n'`、
  读 [0xB73560] 鼠标捕获、[0x887640] 虚槽 +0x18、[0x89F978] 全屏门）→
  `push 'Focus gained\n'` → 0x4068E0（printf 族日志）→ `mov byte [0x8A00A0],1` → ret 0。
- **失焦沿后继（al=0 → 直落）**：`push 'Focus_Loss()\n'` → 日志 → `mov cl,1; call
  0x5BF500` → `call 0x407020` → [0x887640] 虚槽 +0x1C → `mov [0xB73560],al` →
  按 al 选 0x81C5F0=`"true"`/0x81C5E8=`"false"` → `push 'Focus_Loss(): _MouseCaptured = %s\n'`
  → 日志 → [0x887640] 虚槽 +0x14 → `push 'Focus lost\n'` → 日志 → [0x8A00A0]=1 → ret 0。
- ∴ **旗标语义 = 应用/主窗焦点状态**（引擎内名 Focus_Loss/Focus_Restore；
  社区惯例名 GameInFocus 类）。WM_CREATE 分支（表槽 0x77778D）另建 CCToolTip
  单例 [0x887368]（RTTI `.?AVCCToolTip@@`，vptr 0x7F74C4，0x268 字节，0x7777B2 钉）；
  WM_PAINT 分支（表槽 0x7776B5）以 `0x7776C1 cmp byte [0xA8ED80],1` 门控绘制。

### T2.3 栈位自洽证明（wParam 认定非巧合）

入口栈 `+4=hwnd,+8=uMsg,+C=wParam,+10=lParam`；到 0x7776xx 链上恰存续头部 4 压。
同深度旁证：末尾缺省链 `0x777A64..0x777A70` 以 `[esp+0x14/18/1C/20]` 依序压入后
`call [USER32!DefWindowProcA]`——hwnd,uMsg,wParam,lParam 四参吻合
⇒ `[esp+0x1C]=wParam` 铁定。

### T2.4 对 E4-T5 两处标签修正（红项 RA1）

E4 §T5 称写点「门控 `wParam==hwnd`@0x7778A0 且 lParam 变化@0x7778BF」。实读：

| E4 表述 | 实读字节 | 实义 |
|---|---|---|
| 「wParam==hwnd@0x7778A0」 | `3b3d5035b700 cmp edi,[0xB73550]` | **参数 hwnd == 全局主窗 hwnd**（edi=0x777627 装的 [esp+0x14]=hwnd），与 wParam 无关 |
| 「lParam 变化@0x7778BF」 | `3bd1 cmp edx,ecx` | **旗标旧值 vs 新值(wParam≠0) 的状态去重**；lParam 全程不参与本块 |

E4 的两处**地址锚本身正确**，仅语义标签错位；「写者唯一」「hwnd==0 后旗标不可置位」
两条结论不受影响，反被加强：**旗标置 1 的唯一通道 = 激活沿的 WM_ACTIVATEAPP**。

---

## T3. 调用点普查 —— 三类全零调用面 + 唯一注册引用（OS 调用）

| 类别 | 计数 | 明细 |
|---|---|---|
| E8 直呼 0x7775C0 | **0** | `callers[0x7775C0]=[]` |
| jmp/jcc 尾调/转入头 | **0** | `jmp→head=[]`、`jcc→head=[]` |
| 虚表/数据指针中转 | **0** | `.rdata`/`.data`/`.detour` raw 命中 0 |
| **立即数引用（唯一）** | **1** | `mov [esp+0x28],0x7775C0`@**0x777C79**（WNDCLASS.lpfnWndProc） |

（头值 raw abs32 全镜像命中=1，见 T1；函数内部 6 槽跳转表 0x777A80 是**出边**不是入边。）

∴ **活调用面 = 0；该函数不由镜像内任何代码同步调用**，唯一执行通道是 USER32
分派（队列泵 DispatchMessageA / 同步 SendMessage 族）。注册链场景门控：

- 注册函数 0x777C30 的 E8 直呼**恰 2 处**：**0x6BD9CF、0x6BDB0C——双双落在宿主 A
  （0x6BB9A0）前向闭包内**（fwd(A)∈判定 True/True）。即 **A 的 boot 段建窗**，
  全屏门 [0x89F978]（唯一写 1 点 0x52FAB8）分支决定 CreateWindowExA 两形态。
- 建窗后：SetRect/AdjustWindowRectEx/MoveWindow（窗口化）→ ShowWindow(1)@0x777DA9 →
  UpdateWindow → SetFocus@0x777DC9 → RegisterHotKey(hwnd,1,7,0x4D)@0x777DDB。

---

## T4. 与 bail 等待方/消费方连线 —— 无控制流交联，纯消息队列数据流；多泵族

### T4.1 与宿主 A 的关系

- **控制流**：双向皆无。0x7775C0 无入边（T3）；其前向闭包 273 条指令与 fwd(0x6BB9A0)
  无调用交联（写点函数不被 A 调、也不调 A；A 唯一调用点 0x7CD8EA 维持 E4 结论）。
- **数据流**（唯一连线）：A 的自旋环
  `0x6BDD03 / 0x6BDD2E: call 0x5D4D50(泵); a0 80eda800 mov al,[0xA8ED80]; 84c0 test al,al; je 自身`
  ——**A 轮询本旗标等「焦点恢复」**；旗标唯一写者在 WndProc 激活沿（T2.2）。
  结合 X1（泵头 hwnd==0 ⇒ 直接 ret 不取消息）：**hwnd==0 后 WM_ACTIVATEAPP 永不被
  取用 ⇒ 旗标永不可置 1 ⇒ 两自旋环静态完备不可出**——E4-P1 的机制在本端闭合为
  「焦点语义」：**等一个永不到来的焦点恢复沿**。
- **A boot 期还有一条失焦同步通道（红项 RA3）**：A 内 `0x6BBE77..0x6BBE94`：
  `push 0; push 0x840F14; call [FindWindowA]`（0x840F14 =
  `"29e3bb2a-2f36-11d3-a72c-0090272fa661"`，GUID 隐藏窗，单实例握手）→ 找到则
  `call [SetForegroundWindow]`@0x6BBE8B → `ShowWindow(9=SW_RESTORE)`@0x6BBE94。
  若此刻本方主窗已建，该切换可**同步**投递 WM_ACTIVATEAPP(wParam=0) 给本进程窗口
  ⇒ **A 的 boot 期可经 0x6BBE91 返回地址同步走过写 0 路径**（Focus_Loss boot 通道）。

### T4.2 消费通道普查（「消息队列」的具体化）

泵/分派面（DispatchMessageA 全镜像 **5 处**，即 5 个消息循环）：

| 泵（host） | Dispatch 调用点 | 镜像内返回地址（call+6） |
|---|---|---|
| 0x5D4D50（主泵，A/B 环体） | 0x5D4E47 | **0x5D4E4D** |
| 0x53E770（Peek 封装+内嵌分派） | 0x53E8A1 | 0x53E8A7 |
| 0x432C70（成员泵，[esi+4] 门） | 0x432D1B | 0x432D21 |
| 0x759200（DDraw 侧泵） | 0x759248 | 0x75924E |
| 0x759940（DDraw 焦点等待环） | 0x759A76 | 0x759A7C |

- 泵计数器 **[0xAA0430]**：7 组写者（0x432CDD / 0x5D4D77 / 0x5DC44E-59 / 0x759210 /
  0x759A3F / 0x775A7F / 0x77F925）。**分型注意**：主泵 0x5D4D50 的 `inc` 在
  hwnd==0 短路 `je` **之后**（0x5D4D64/77）⇒ 主泵短路时计数不增；而 0x759200 泵在
  调 Peek 封装**之前**就 +1 ⇒ 「计数冻结」与「计数递增但旗标不置」的判读须按泵分型。
- **读方全景**（45 读按宿主聚簇，pump-near=±12 条指令内有泵调用）：
  自旋等待族：0x6BB9A0 内 2 处（0x6BDD08/0x6BDD33，E4 已钉）、0x55D360 内 3 处
  （0x55D377/0x55D3A7/0x55D88E——即 E4-T4② 上游函数族）、0x5D2410/0x5D2530 计 4 处、
  0x68FBB0 计 3 处、0x690160 计 4 处、冷函数 0x6904C0/0x6904E9/0x690504 等；
  门控族：WM_PAINT 块 0x7776C1、DDraw 焦点函数 0x759940/0x759C30 各 2 处、
  0x4BAD80/0x4BAF40/0x4BB000/0x4BB620/0x4C3D00/0x4C3E30/0x432E40/0x52BA60/0x55E160/
  0x6211D0/0x77DC90/0x7B84D0/冷 0x4333F0/0x4BB208/0x610950/0x774C70/0x7B93F0 各 1–3 处。
  ∴ 旗标是**全引擎焦点闸**：等待环（等 1）与绘制/输入门（判 1）两类消费。

---

## T5. D-11/E2/E3 判读增补（交付重点）

### T5.1 E2 慢采样加读清单（按判读力排序）

al 的直接来源是**栈参 wParam**（无 VA），故加读对象为旗标本体、邻位与关键因果全局：

| 优先 | VA | 内容 | 判读力 |
|---|---|---|---|
| 1 | **0xA8ED80** | 焦点旗标本体 | =1 而两宿主环未出 ⇒ 卡点不在旗标环（bail 环/尾段）；=0 且样本长期为 0 ⇒ 卡在等焦点沿（0x6BDD03/0x6BDD2E 族或 0x759940 等 DDraw 等待环） |
| 1 | **0xAA0430** | 泵调用计数（BSS 初值 0） | 增长 ⇒ 某泵在取消息（配合旗标=0 ⇒ 「泵活、激活沿不来」：窗在但前台不变）；冻结 ⇒ 主泵型短路（hwnd==0 或未进泵）——**注意按泵分型**（0x759200 型无条件 +1） |
| 1 | **0xB73550** | 主窗 hwnd | =0 ⇒ 消息通道死（写者 0x7778CE 结构性不可达，P1 无穷自旋面坐实）；≠0 且计数增 ⇒ 通道活，等系统激活沿 |
| 2 | **0x8A00A0** | 焦点沿处理完成标志（写者 0x5D1E55/0x777942） | =1 ⇒ 至少走过一次焦点沿后继（Focus_Loss/Restore 二选一已执行） |
| 2 | **0xB73560** | 鼠标捕获字节（写者 0x7773E8/0x7778FD 均在 WndProc 焦点块） | 区分失焦沿是否走完鼠标释放段 |
| 2 | **0xA8ED81** | WM_SYSCOMMAND 位（SC_MINIMIZE→1 / 0xF120→0，写者 0x777874/0x777880） | 采到 1 ⇒ 用户/系统发过最小化 |
| 3 | 0x89F978 | 全屏模式（写 1 点 0x52FAB8） | 影响 WM_PAINT 门与失焦行为形态 |
| 3 | 0x884D34 / 0x887368 | RBUTTONUP 清零位 / CCToolTip 单例 | 次要旁证 |

（0xA8ED80 与 0xA8ED81/0xA8ED6B 同 BSS 页相邻；0xA8ED6B 写者 0x5A922F/0x52F63E/0x5A95A1，
Focus_Restore 以 `cmp [0xA8ED6B],0` 门控虚调用，可一并加读。）

### T5.2 E3 五区栈读法补充 —— 「栈在 0x7778CE 所在函数」时的签名

WndProc frameless（无 EBP 链）⇒ **E3 栈判读必须按扫描而非帧游走**。签名分三型：

- **型①（队列分派，最常见）**：WndProc 帧的返回地址在 USER32 内（镜像外）；
  **镜像内最近返回地址 = Dispatch 调用点+6**：0x5D4E4D（主泵）/0x53E8A7/0x432D21/
  0x75924E/0x759A7C。落此签名 ⇒ 写者=W 经队列激活沿，bail 环未达属正常位序。
- **型②（同步激活/销毁通道，SendMessage 族）**：镜像内最近返回地址 = 下列调用点+6：
  - `0x7775BB`（0x7775B5 call SetFocus 助手尾）、`0x7775AF`（0x7775A9 call SetActiveWindow）；
  - **0x6BBE91**（A 内 0x6BBE8B call SetForegroundWindow——单实例握手失焦沿；若同时
    旗标写 0，此为 boot 期 RA3 通道的直接证据）、`0x6BBE9A`（其 ShowWindow 后）；
  - `0x777DAF`（建窗序列 ShowWindow）、`0x777DCF`（建窗序列 SetFocus）；
  - `0x775B81`/`0x775CC1`（DestroyWindow 站点，WM_DESTROY 同步）。
- **型③（WndProc 内部下潜）**：激活沿后继 `0x777930 call 0x777420(Focus_Restore)`
  ——采样落在 0x777420 体内时栈 ret=**0x777935**（=「正在处理刚写 1 的焦点恢复」，
  与写点同帧的强签名）。

**与 E4 精化表的合并读法**：栈在 0x6BDD08/0x6BDD33（A 旗标自旋环泵返回点）时，
**先读 [0xA8ED80] 与 [0xAA0430]/[0xB73550]**：旗标=0∧hwnd=0 ⇒ P1 静态完备自旋
（写者身份已无关）；旗标=0∧计数增 ⇒ 等焦点沿（有窗、泵活、无激活沿）；
旗标=1 ⇒ 不可能滞留环内（je 条件），指示采样恰在环首或非本环。

---

## T6. 红项/意外发现清单（本轮 5 项）

1. **RA1（E4 标签修正×2）**：0x7778A0 实为 `cmp edi,[0xB73550]`（参数 hwnd==全局主窗），
   非「wParam==hwnd」；0x7778BF 实为**旗标新旧值去重**（edx=旧 vs ecx=wParam≠0），
   非「lParam 变化」。锚地址正确，结论面（写者唯一、hwnd==0 后不可置 1）不变且加强。
2. **RA2（幻影根×3）**：0x7775BC / 0x777415 / 0x777C24 三个「无 pred 根」均为上一函数
   `ret` 后 `90` 填充的线性解码伪根（0x7775BC..BF=90×4、0x777415..1F=90×11、
   0x777C24..2F=90×12，逐字节钉）；同 r038/E4-R2 幻影家族。真头不受影响。
3. **RA3（A 内同步失焦通道）**：A boot 内 0x6BBE77..0x6BBE94
   FindWindowA(NULL,"29e3bb2a-…-661")+SetForegroundWindow+SW_RESTORE——本方主窗已建时
   可在 boot 期同步递送 WM_ACTIVATEAPP(0)（写 0）；写 1 通道不变（仍须激活沿）。
4. **RA4（泵族非单一）**：DispatchMessageA 全镜像 5 处=5 个消息循环；泵计数 [0xAA0430]
   7 组写者且增量语义分型（主泵 hwnd==0 不增、0x759200 泵无条件先增）——E2/E3 判读
   不能把「计数冻结」单一归因于主泵。
5. **RA5（命名锚落定）**：类名=窗口名=`"Yuri's Revenge"`（0x849F48， RegisterClassA/
   CreateWindowExA 双用）；焦点调试串族
   `'Focus_Restore()\n'/'Focus_Loss()\n'/'Focus gained\n'/'Focus lost\n'`
   （0x849ECC/0x849E94/0x849EF8/0x849F08）⇒ 旗标=焦点态（引擎命名 Focus_Loss/
   Focus_Restore）；WM_CREATE 单例=CCToolTip（`.?AVCCToolTip@@`）。

---

## T7. 诚实账（静态不可判/未逐项展开，如实列）

1. **运行期哪条通道 fired**（队列激活沿 vs 同步通道；写 1 vs 写 0）：静态只证通道与
   门控，观测趟归因须 E2 加读 + E3 栈采样。
2. **[0x887628] 单例类名 UNKNOWN**：三处 c7 05 戳均写 0（清空），真 vptr 经工厂返回值
   寄存器存入（0x560D67/0x56107F 邻域 `mov ecx,eax; call 工厂; mov [0x887628],…`），
   本轮未追工厂 RTTI；其 slot+0x38/0x40 =「消息预过滤/占用」为形态推断。
3. **0x5BF500 / 0x407020 / 0x4068E0 / 0x49F620 / 0x724200 / 0x54F790 / 0x7C8A22 /
   0x7C8A1C** 等消费侧/日志/转发函数未逐一命名（0x4068E0 为 printf 族日志，由
   `'%s\n'`/`'%s-%s'` 格式串用法佐证，未做函数级闭合）。
4. **0x475 自定义消息（0x7775DF 预过滤旁路、0x7B3AF8 第二使用点）的投递方身份**未普查。
5. **建窗两分支（[0x89F978] 全屏门）样式细节**：立即数已钉（0x2CA0000 / 0x82000000 /
   dwExStyle=8），「全屏/窗口化」标签为形态推断。
6. **E2 观测窗内泵分型**：哪个泵在跑、计数增速如何对应，属运行期。
7. **WM_ACTIVATEAPP 的 OS 侧时序**（何时递送、是否丢失）不可静态判。
8. X5 的 exitstate 6 点普查本轮以 raw 扫描**复核通过**（6/6），未重做其相对寻址论证
   （PE32 无该寻址形态，沿用上游口径）。

---

## 工件与方法

- 脚本：`re_atlas/tools/_r063a_probe1.py`（锚/边界/写点转储/读写普查/raw 扫描）、
  `_r063a_probe2.py`（冷头根证明/注册函数/IAT/串/RTTI/泵转储/读者聚簇）、
  `_r063a_probe3.py`（伪根裁定/注册链/同步 API 普查/泵调用者/WM_PAINT 块）、
  `_r063a_probe4.py`（RTTI 残项/同步返回地址精钉/副泵身份/A 内 SetForegroundWindow
  上下文/WM_CREATE 块）；probe5 为内联残钉。全部只读、只写 stdout 与各自 `_out.txt`。
- 未触碰：`_crev_engine.py`、LEDGER/STATUS/INDEX/HANDOFF、gamemd.exe、任何既有文件。
