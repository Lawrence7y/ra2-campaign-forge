# ZC-11 `except.txt` 崩溃取证归因报告

> [META]
> 任务=ZC-11 except.txt 崩溃取证（P0）· 执行方=MiMo 取证子代理 · 日期 2026-09-29/30
> 证据源：`out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated`（及副本）
> 二进制只读：`ra2youli/gamemd.exe`（MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`）、`ra2bench/ra2render.dll`（MD5 `3C1077BD…`，152,576 B）
> 写作用域：`out/re_work/except_forensics/**`、`docs/re/except_zc11_forensics.md`（本文）
> **不改** `ra2render/**`、`ra2youli/**`、`ra2bench/**`、`RESULT_ZC11.md` 本体

---

## [0] 结论摘要（≤8 行）

1. **[实证] 崩溃点在原版 `gamemd.exe` `.text`，不在跳板/桩**：EIP `0x007CFC9F` 落在 `.text`（VA `0x00401000`–`0x007E038D`），函数为**内嵌 MSVC 6.0 CRT 小块堆分配器 `__sbh_alloc_block`**（入口 `0x007CFB13`）。不在 `0x01B00000` 跳板页，不在 `ra2render.dll`（ImageBase `0x10000000`，运行期钩子入口 `0x54D3xxxx`）。
2. **[实证] 直接死因 = SBH 空闲链表节点指针被毒值污染**：崩溃指令 `mov ecx, [edx]`（`8B 0A`），`EDX=FE00FFFF`；上一条 `mov edx, [ecx+edi*8+4]`（`0x7CFC9B`）从空闲位图槽位载入节点指针，该指针已是毒值。属**堆元数据损坏**（UAF / double-free / 越界写入 freelist / 未初始化槽位）。
3. **[实证] 调用链全在原版 CRT**：`CRT::_new (0x7C8E17) → _nh_malloc (0x7C9442) → heap_alloc (0x7C946E) → __sbh_alloc_block (0x7CFB13)`；栈上返回地址 `0x7C9489 / 0x7C9452 / 0x7C8E22` 逐帧吻合。
4. **[实证] 与 `ra2render.dll` 无直接执行路径关系**：崩溃指令与调用链均不在任何注入钩子（Blit/Draw/寻敌/迷雾/雷达/L4）内；毒值 `FE00FFFF` 在 `gamemd.exe` 与 `ra2render.dll` 映像中**均无立即数**。
5. **[实证] 时间戳归属 segD U0200 对局**：`except.txt` CreationTime **2026-09-29 22:38:24**，夹在 `segD_U0200_setup.png`（22:21:01）与 `segD_U0200_sample.json`（22:46:07）之间；前后证据面 = 段 D 遭遇战 U0200 档（随机敌国 units_seen 713–716，全场最高负载档之一）。
6. **[推演] 根因候选**：①原版 SBH 在高密度对象生命周期下的 freelist 损坏（AnimClass/BulletClass/ParticleClass 高频 new/delete）；②某对象缓冲越界写穿邻块头；③double-free 使 freelist 成环/污染。**ra2render 不是执行层肇因**，但 LFH 激活（`HeapSetInformation`×7/8 进程堆）改变了底层 Windows 堆布局，理论上可影响 SBH 后备大块的取用时序——列为**弱相关待实测**，不作主因。
7. **[实证] 与 RESULT_ZC11.md [7]「零崩溃」声明直接矛盾**：收尾已登记该矛盾（`docs/re/zc11_closeout_report.md` [0]③）；本文补上归因，并给出勘误建议（见 §八）。**不得**因报告写过「零崩溃」而回避。
8. **[待实测] 复现性**：需 A/B（同图同档 ①仅原版 ②注入 ra2render ③注入但 EnableLFH=0）各 ≥3 局，观察 `except.txt` 复现率，才能把「LFH 弱相关」从推演升为实证或排除。

---

## [1] 异常现场全文解析

### 1.1 头部寄存器（`except.txt` L1–L19）

| 字段 | 值 | 判读 |
|---|---|---|
| Error code | `EXCEPTION_ACCESS_VIOLATION` | 访问违例 |
| Access address | `FE00FFFF`（**read**） | 与 `EDX` 同值 ⇒ 解引用毒指针 |
| Exception at | `007CFC9F` | EIP |
| EAX | `1498EC08` | 堆块/对象指针（用户堆区） |
| EBX | `14830AA8` | 同上 |
| ECX | `1498FB68` | 同上（= 栈 `00F9D15C`） |
| **EDX** | **`FE00FFFF`** | **毒值 / 野指针** |
| ESI | `7FFFFFFF` | 掩码常量（`or esi,0xffffffff; shr esi,cl` 的结果） |
| EDI | `00000004` | 位图命中位号 / 循环下标 |
| ESP | `00F9D148` | 栈顶 |
| EBP | `00F9D168` | 帧指针 |
| EFlags | `00010286` | CF=0 ZF=1…（崩溃前 `cmp` 结果） |

Bytes at CS:EIP（与 `ra2youli/gamemd.exe` 文件偏移 `0x3CFC9F` **逐字节一致**）：

```
8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
```

### 1.2 栈回溯（`Stack dump` 全文 1024 行已解析）

栈内**真实 .text 返回地址**（排除 UTF-16 字符串半字伪码址）：

| 栈位 | 值 | 归属 |
|---|---|---|
| `00F9D16C` | `007C9489` | `heap_alloc` 内 `call 0x7CFB13` 的返回点（`__sbh_alloc_block` 调用者） |
| `00F9D180` | `007C9452` | `_nh_malloc` 内 `call 0x7C946E` 的返回点 |
| `00F9D188` | `007C8E22` | `CRT::_new` 内 `call 0x7C9442` 的返回点 |
| `00F9D194` | `0048F740` | 游戏侧对象构造（写入 vtable `0x7E56D8`，`call 0x420140`） |
| `00F9D1A8` | `004911EB` | 游戏侧循环（`cmp eax,[0x89ED08]`） |
| `00F9D1C8` | `0056104B` | 游戏侧 `push 0x98; call 0x7C8E17`（152B 对象 new） |
| `00F9D24C` | `00683DF8` | 游戏逻辑（`call 0x72DEF0` / `call 0x5FB160`） |
| `00F9D34C` | `0052E74A` | 游戏逻辑（`test al,al` 分支） |
| `00F9D62C` | `001B0022` | **非** `0x01B00000` 跳板页；低地址数据/句柄残留（见 §2.4） |

栈内 UTF-16LE 字符串（**数据残留，非调用帧**）：

| 栈位 | 字符串 | 来源推断 |
|---|---|---|
| `00F9D368` | `ce RTX 3060 Laptop GPU` | 显示适配器枚举（诊断截图栈） |
| `00F9D704` | `GameViewer Virtual Display Adapter` | 虚拟显示驱动（GameViewerIddDriver） |
| `00F9D808` | `Root\GameViewerIddDriver` | 同上 |
| `00F9DA74` | `[ApiName] Hook Entered` | 通用 Hook 框架格式串（**不在** ra2render/ddraw/ra2loader/gamemd 映像内；疑来自虚拟显示驱动或系统 Hook） |
| `00F9E054` | `\\.\DISPLAY2` | 显示器设备路径 |

### 1.3 毒值 `FE00FFFF` 来源分析

| 检查项 | 结果 | 证据 |
|---|---|---|
| `gamemd.exe` 映像内立即数 `FF FF 00 FE` | **0 处** | `recompute_poison.txt` |
| `ra2render.dll` 映像内立即数 | **0 处** | 同上 |
| 指针形态 | 非规范用户地址（> `0x80000000`，Win32 用户态不可读） | 触发 read AV |
| 位拆解 | `0xFE00` : `0xFFFF`（两个 16 位）；或 `~0x01FF0001` | — |
| 与 ESI=`7FFFFFFF` 的关系 | ESI 是分配器**掩码**（`or esi,-1; shr esi,cl`），非毒值来源 | 反汇编 `0x7CFB45–0x7CFB48` |
| 与 EDI=`4` 的关系 | EDI 是空闲位图扫描命中的**位号**，用于 `[ecx+edi*8+4]` 取节点 | `0x7CFC98–0x7CFC9B` |

**[推演] 毒值来源候选（按可能性排序）**：

1. **freelist 节点被 use-after-free 写穿**：对象释放后其内存被复用，用户态数据覆盖了 next 指针字段；`FE00FFFF` 像被写入的业务数据（例如颜色/掩码/坐标打包）而非分配器自身填充。
2. **double-free 导致 freelist 成环/自引用**：与 `crt_pool_risk_review.md` §威胁二描述的失效模式同构（原版 SBH 无 Tag 防护）。
3. **相邻堆块越界写**：高密度 `AnimClass`（456B）/`BulletClass`（352B）/`ParticleClass`（312B）并发存活时，一块溢出 4–16 字节即可污染邻块头/邻 freelist 槽。
4. **未初始化槽位**（可能性低）：SBH 建堆时应清零；除非后备大块来自非清零的 `HeapAlloc` 且建堆路径漏清。

> 注：`0x00F9D2EC` 栈位另有 `FFFF0000`，与 `FE00FFFF` 同族形态，进一步支持「业务数据覆写 freelist」而非「分配器自身投毒」。

---

## [2] 反汇编：EIP 所属函数

### 2.1 PE 节表（`ra2youli/gamemd.exe`，ImageBase `0x00400000`）

| 节 | VA | VS | 说明 |
|---|---|---|---|
| `.text` | `0x00401000` | `0x3DF38D` | **EIP 在此**（RVA `0x3CFC9F`） |
| `.rdata` | `0x007E1000` | `0x30074` | 只读数据/vtable |
| `.data` | `0x00812000` | `0x367BE4` | 全局数据（SBH 状态 `[0xB78B8C/94/98]` 在此） |
| `.rsrc` | `0x00B7A000` | `0x18128` | 资源 |
| `.detour` | `0x00B93000` | `0x2718` | Detours 存根节（签名未变，门禁 323/323 PASS） |

**EIP 判定**：`0x007CFC9F` ∈ `.text` ⇒ **原版代码**；≠ `0x01B00000` 跳板页；≠ `ra2render.dll` 任一节。

### 2.2 函数识别：`__sbh_alloc_block @ 0x007CFB13`

与 `docs/re/crt_memory_pool_deep_dive.md` / `ARCHITECTURE_ATLAS.md` 已命名的 **SBH 小内存堆分配器** 吻合：

```
007CFB13: 55                push    ebp
007CFB14: 8BEC              mov     ebp, esp
007CFB16: 83EC14            sub     esp, 0x14
007CFB19: A1 94 8B B7 00    mov     eax, [0xB78B94]    ; SBH 状态
007CFB1E: 8B 15 98 8B B7 00 mov     edx, [0xB78B98]
...
007CFB2D: 8B4508            mov     eax, [ebp+8]       ; size
007CFB33: 8D4817            lea     ecx, [eax+0x17]    ; 对齐
007CFB36: 83E1F0            and     ecx, 0xFFFFFFF0
007CFB3C: C1F904            sar     ecx, 4             ; size class
007CFB3F: 49                dec     ecx
007CFB40: 83F920            cmp     ecx, 0x20
```

崩溃点前 6 条（原文 L19 字节序列逐条对应）：

```
007CFC98: 8B4DF4            mov     ecx, [ebp-0xC]     ; 空闲槽基址
007CFC9B: 8B54F904          mov     edx, [ecx+edi*8+4] ; ← 载入 freelist 节点指针（已是 FE00FFFF）
007CFC9F: 8B0A              mov     ecx, [edx]         ; ★ 崩溃：读节点 size 字段
007CFCA1: 2B4DF0            sub     ecx, [ebp-0x10]    ; 与请求尺寸做差
007CFCA4: 8BF1              mov     esi, ecx
007CFCA6: 894DF8            mov     [ebp-8], ecx
007CFCA9: C1FE04            sar     esi, 4             ; 计算归还 size class
007CFCAC: 4E                dec     esi
007CFCAD: 83FE3F            cmp     esi, 0x3F          ; 64 桶上限
007CFCB0: 7E03              jle     ...
007CFCB2: 6A3F 5E           push 0x3F; pop esi
007CFCB5: 3BF7              cmp     esi, edi
007CFCB7: 0F84 0D010000     je      0x7CFDCA
007CFCBD: 8B4A04            mov     ecx, [edx+4]       ; next
007CFCC0: 3B4A08            cmp     ecx, [edx+8]       ; prev（双向链表完整性检查）
```

**语义**：SBH 正在从某 size-class 的空闲链表摘除/归并节点；`[edx]=size`、`[edx+4]=next`、`[edx+8]=prev` 为经典双向 freelist 布局。`EDX` 为毒值 ⇒ **在本次 new 之前，freelist 元数据已被破坏**。

### 2.3 调用链（栈返回地址 × 反汇编交叉验证）

```
游戏侧 (0x48F740 / 0x4911EB / 0x56104B / 0x683DF8 / 0x52E74A …)
  └─ CRT::_new            0x007C8E17   (push 1; push size; call _nh_malloc)
       └─ _nh_malloc       0x007C9442   (溢出检查; call heap_alloc)
            └─ heap_alloc  0x007C946E   (size ≤ __sbh_threshold ? SBH : HeapAlloc)
                 └─ __sbh_alloc_block  0x007CFB13   ★ 崩溃于 +0x18C = 0x007CFC9F
```

栈 `00F9D16C=0x7C9489` 正是 `heap_alloc` 内 `call 0x7CFB13` 的下一条；`00F9D180=0x7C9452`、`00F9D188=0x7C8E22` 逐级吻合（对照 `crt_memory_pool_deep_dive.md` §2.2 原文反汇编）。

### 2.4 跳板页与注入件对照

| 候选区域 | 是否涉及 | 依据 |
|---|---|---|
| `0x01B00000` 跳板/桩页 | **否** | EIP 与栈返回地址均不在该页；`ra2render.dll` 内 8 处 `0x01B00000` 为 VirtualProtect/trampoline 缓冲引用，非本次执行路径 |
| `0x001B0022`（栈 `00F9D62C`） | **否** | 非 `0x01B00000` 页；低地址残留，非 .text 返回点 |
| `ra2render.dll`（`0x54D3xxxx` 钩子入口） | **否** | 栈上无任何 `0x54D3xxxx` 返回地址 |
| `ra2render` L1 Blit 钩子 | **否** | 死因在分配器，不在绘制 |
| `ra2render` L2 寻敌钩子 | **否** | 同上 |
| `ra2render` L3 迷雾/`CellClass::Draw` | **否** | 同上 |
| `ra2render` L4 全量重绘桩 | **否** | 同上 |
| `ra2render` 雷达/小地图 Plot_Cell | **否** | 同上 |
| `cnc-ddraw`（`ra2bench/ddraw.dll`） | **否**（执行路径） | 栈上无 ddraw 返回点；但其作为 DirectDraw 包装层共存，属环境变量 |

---

## [3] 时间线：崩溃对到 ZC-11 哪一段

### 3.1 关键时间戳

| 时刻 | 事件 | 源 |
|---|---|---|
| 19:34:15 | ZC-11 开工（`hashes.start.txt`） | 证据树 |
| 19:34:59 | `ra2render.log` 创建 | 文件属性 |
| 19:43 | 段 0 菜单取证 | `s0/**` |
| 20:44–20:48 | 段 A 对拍 | `segA/**` |
| 20:57–21:19 | 段 B | `segB/**` |
| 21:19–21:46 | 段 C | `segC/**` |
| 21:53–22:21 | 段 D 前置（地图列表校准、U0050/U0800/U0200 setup） | `segD/**` |
| **22:38:24** | **`except.txt` 生成（CreationTime）** | `closeout/except.txt.final_isolated` |
| 22:46:07 | `segD_U0200_sample.json` / `segD_U0200_battle.png` | `segD/**` |
| 22:46:10 | `segD_U0200_record.json` | `segD/**` |
| 22:47:55 | `dd_setup.png` / `dd_open.png`（诊断） | `segD/**` |
| 22:50–22:51 | U0050/U0800 sample+record | `segD/**` |
| 22:54–22:57 | 段 E 机位复位 | `segE/**` |
| 23:03:33 | 战役存档最终隔离 | `segC/quarantine_*.final` |
| 23:05:07 | `ra2render.log` 末次写入 | 文件属性 |
| 23:35 | `RESULT_ZC11.md` 成文 | 文件属性 |
| 23:55:25 | 收尾隔离副本 `.ra2bench.zc11_window` 创建 | 文件属性（内容与原件逐字节相同） |

### 3.2 段归属判定

**[实证] 崩溃落在 segD（段 D）U0200 对局窗口**：

- 崩溃时刻 22:38:24 严格夹在 `segD_U0200_setup.png`（22:21:01，**−17.4 min**）与 `segD_U0200_sample.json`（22:46:07，**+7.7 min**）之间。
- 段 A/B/C 的最后产物均 ≤21:46，距崩溃 >52 min；段 E 首件 22:54:23，距崩溃 +16 min（崩溃后仍继续跑，说明该局异常退出但 harness 未中断整批）。
- RESULT_ZC11 [2]D 记载 U0200 随机敌国 `units_seen=713–716 @f15`、战斗 ~1:39 提前终局——**单位密度最高的档之一**，与 SBH 高频对象 churn 高度同构。

| 段 | 与 22:38:24 的距离 | 判定 |
|---|---|---|
| seg0 | 19:43（−175 min） | 排除 |
| segA | 20:48（−110 min） | 排除 |
| segB | 21:19（−79 min） | 排除 |
| segC | 21:46（−52 min） | 排除 |
| **segD** | **22:21 setup ↔ 22:46 sample（窗口内）** | **[实证] 归属** |
| segE | 22:54（+16 min） | 排除（崩溃后） |
| segG | 未产生动态 dump | 不适用 |

---

## [4] 归因表

| # | 命题 | 结论 | 等级 | 依据 |
|---|---|---|---|---|
| A1 | EIP 在原版 `.text` | 是 | **[实证]** | PE 节表 + 字节比对（L19 ≡ 文件偏移 `0x3CFC9F`） |
| A2 | EIP 在 `0x01B00000` 跳板页 | 否 | **[实证]** | EIP/栈返回点均不在该页 |
| A3 | EIP 在 `ra2render.dll` | 否 | **[实证]** | DLL ImageBase `0x10000000`，钩子入口 `0x54D3xxxx`；栈无返回点 |
| A4 | 所属函数 | `__sbh_alloc_block @ 0x007CFB13`（内嵌 CRT SBH） | **[实证]** | 反汇编 + `crt_memory_pool_deep_dive.md` / ATLAS 命名 |
| A5 | 直接死因 | freelist 节点指针 = 毒值 `FE00FFFF`，解引用 read AV | **[实证]** | `mov ecx,[edx]`；`EDX=FE00FFFF`；上一条取指针来源 |
| A6 | 毒值是模块内立即数 | 否 | **[实证]** | gamemd/ra2render 映像 0 命中 |
| A7 | 调用链含注入钩子 | 否 | **[实证]** | 栈 8 个 .text 返回点全在 CRT/游戏侧 |
| A8 | 崩溃段归属 | segD U0200 对局 | **[实证]** | 时间戳夹逼（22:21 / 22:38 / 22:46） |
| A9 | 与 Blit/寻敌/迷雾/雷达/L4 钩子有直接执行关系 | 否 | **[实证]** | A2+A3+A7 |
| A10 | 根因 = 原版 SBH 在高密度对象生命周期下 freelist 损坏（UAF/double-free/越界写） | 主候选 | **[推演]** | 毒值形态、无立即数、U0200 负载、`crt_pool_risk_review.md` 威胁矩阵 |
| A11 | ra2render EnableLFH 改变底层堆布局，可能间接影响 SBH 后备块 | 弱相关 | **[待实测]** | `blitter_hooks.cpp:774–786` 对 7/8 进程堆 `HeapSetInformation(LFH)`；SBH 自管 freelist，理论上不共享，需 A/B |
| A12 | `[ApiName] Hook Entered` 串 = ra2render 所写 | 否/未证 | **[推演]** | 该串不在 ra2render/ddraw/ra2loader/gamemd 映像；疑来自 GameViewerIddDriver 或系统 Hook |
| A13 | RESULT_ZC11 [7]「零崩溃」 | **错误，须勘误** | **[实证]** | except.txt CreationTime 落在 ZC-11 窗口内；收尾文档已登记矛盾 |
| A14 | 崩溃后 harness 未中断 | 是 | **[实证]** | 22:46–22:57 段 D/E 证据继续产出 |

### 是否与 `ra2render.dll` 注入件相关？

| 层次 | 判定 | 等级 |
|---|---|---|
| **执行层（谁的指令崩的）** | **无关**——原版 CRT `__sbh_alloc_block` | [实证] |
| **数据层（谁污染了 freelist）** | **未证与注入相关**；主候选为原版对象生命周期缺陷 | [推演] |
| **环境层（注入是否改变触发概率）** | **不能排除**——LFH/满速计时/钩子热路径提高对象 churn | [待实测] |

**一句话**：崩溃**不是** ra2render 钩子代码造成的；但「注入态下才复现」尚未被证伪，需 A/B 实测收口。

---

## [5] 根因候选（分级）

| 序 | 候选 | 等级 | 支持 | 反证/缺口 |
|---|---|---|---|---|
| R1 | 原版 SBH freelist 损坏（UAF 写穿 next） | **[推演]·主** | 毒值像业务数据；U0200 713 单位高频 new/delete；`crt_pool_risk_review.md` 威胁四同构 | 无 dump，不能指认具体对象类型 |
| R2 | double-free → freelist 成环/污染 | **[推演]** | 威胁二；粒子/动画提前结束又析构 | 同上 |
| R3 | 邻块越界写（Anim/Bullet/Particle 之一） | **[推演]** | 352/456B 对象在 713 单位局内存活峰值极高 | 同上 |
| R4 | ra2render EnableLFH 间接改变 SBH 后备块时序 | **[待实测]** | `HeapSetInformation`×7/8 | SBH 自管 freelist，与进程堆 LFH 不共享链表 |
| R5 | ra2render 某钩子越界写（数据层） | **[待实测]·弱** | 注入态共存 | 无返回点；钩子均带 `__except`；源码侧未见对 SBH 元数据的写 |
| R6 | cnc-ddraw 包装层堆干扰 | **[待实测]·弱** | 共存 | 无执行路径证据 |

---

## [6] 证据锚点

| 证据 | 路径 | 哈希/属性 |
|---|---|---|
| 崩溃转储（隔离件） | `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated` | SHA256 `B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870`；26,830 B；CreationTime 2026-09-29 22:38:24 |
| 同内容副本 | `…/closeout/except.txt.ra2bench.zc11_window` | 逐字节相同；副本创建 23:55:25（收尾隔离） |
| 反汇编全文 | `out/re_work/except_forensics/disasm_7CFC9F.txt`、`func_7CFC9F.txt` | 只读生成 |
| 调用点/毒值扫描 | `out/re_work/except_forensics/callers_and_poison.txt` | 只读生成 |
| 会话/时间线 | `out/re_work/except_forensics/sessions_timeline.txt` | 47 个 ra2render 会话 PID |
| **可复算脚本** | `out/re_work/except_forensics/recompute_except_zc11.py` | 一键复现全文解析+反汇编+毒值扫描+时间线 |
| 游戏二进制 | `ra2youli/gamemd.exe` = `ra2bench/gamemd.exe` | MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`；SHA256 `73201CC0…` |
| 注入件 | `ra2bench/ra2render.dll` | 152,576 B；MD5 `3C1077BD44F2B0DB9D30D55C5C9DA68C`；SHA256 `8430204C…` |
| 遥测日志 | `ra2bench/ra2render.log` | 4,197,243 B；47 会话；末次写 23:05:07 |
| 时间线对照 | `out/re_work/zcode_live/RESULT_ZC11.md`（只读引用） | 段 D U0200 记录 |
| 收尾矛盾登记 | `docs/re/zc11_closeout_report.md` [0]③ | 已指出与 [7] 不符 |
| SBH 架构命名 | `docs/re/crt_memory_pool_deep_dive.md`、`ARCHITECTURE_ATLAS.md` | `__sbh_alloc_block @ 0x007CFB13` |
| 池风险威胁矩阵 | `docs/re/crt_pool_risk_review.md` | UAF/double-free 失效模式同构 |

---

## [7] 是否勘误 RESULT_ZC11.md [7]

### 7.1 矛盾原文

> RESULT_ZC11.md [0]⑦ / [7]：「**[7] 零崩溃零 desync**：ra2bench 全程未生成 except.txt；……」
> 「*是否触发 desync/崩溃：否*。ra2bench 全程未生成 except.txt（该文件此前不存在、收尾仍不存在）」

**事实**：`ra2bench/except.txt` 于 **2026-09-29 22:38:24** 生成（ZC-11 窗口 19:34–23:05 内），收尾将其哈希后隔离至 `evidence/closeout/`。`docs/re/zc11_closeout_report.md` [0]③ 已登记该差异。

### 7.2 勘误建议（**必须**，不得回避）

| 目标 | 改前 | 改后 | 理由 |
|---|---|---|---|
| RESULT_ZC11.md [0]⑦ | 「零崩溃零 desync」 | 「**有 1 次崩溃**（segD U0200 对局 @22:38:24，`except.txt` 见 closeout）；desync 无联机面仍为 0；崩溃归因见 `docs/re/except_zc11_forensics.md`」 | except.txt CreationTime 落在本卡窗口 |
| RESULT_ZC11.md [7] | 「全程未生成 except.txt / 收尾仍不存在」 | 「`except.txt` 于 22:38:24 生成并已隔离（SHA256 `B42C7014…`）；崩溃点=原版 `__sbh_alloc_block`，非注入钩子；详见取证报告」 | 同上 |
| RESULT_ZC11.md [1] 表 D 行 | 可选加脚注 | 「U0200 对局中途发生 1 次原版 CRT 崩溃，harness 重启后完成采样」 | 解释 22:38→22:46 的 8 min 空窗 |
| 任务卡/台账「零崩溃」类表述 | 一律 | 改为「崩溃 1 次（原版 SBH），非注入肇因」 | 红线一致性 |

**影响面**：不影响段 A–E 的像素/性能结论本身（那些证据均在崩溃前后独立产出且自洽）；但**「全程稳定」类宣称必须撤回**，性能分档解读需注明「U0200 采样含一次进程重启」。

---

## [8] 复现与验证计划（P0）

| 步骤 | 动作 | 判定 |
|---|---|---|
| V1 | 同图 U0200 + 随机敌国，**无 ra2render** 跑 ≥3 局 | 若复现 ⇒ 原版固有（坐实 R1–R3） |
| V2 | 同图 + ra2render 默认档（含 LFH=1）≥3 局 | 与 V1 对比复现率 |
| V3 | 同图 + ra2render 但 `EnableLFH=0` ≥3 局 | 隔离 R4 |
| V4 | 崩溃时抓 minidump / 用 x64dbg 在 `0x7CFC9B` 下硬件断点 | 指认被污染槽位所属 size-class 与最后写入者 |
| V5 | 若 V1=0 且 V2>0 ⇒ 升级 R5，按钩子热路径二分（先关 L2 寻敌，再关 L4，再关 Blit） | 定位注入侧触发器 |

---

## [9] 草稿：待裁决项补丁（供 RESULT_ZC11 / 台账 §九引用）

> 下列条目为**草稿**，建议以「勘误+新增待裁决」形式并入 RESULT_ZC11.md §[9] 或顶层台账；**不就地改 RESULT 本体**（本卡写作用域外）。

1. **[P0] RESULT_ZC11 [7]「零崩溃」勘误落地**：按 §7.2 三处改写；台账与任务卡同步；引用本报告 `docs/re/except_zc11_forensics.md` 作为归因附件。
2. **[P0] except.txt 归因收口**：已收口到「原版 `__sbh_alloc_block` freelist 损坏」；剩余动作 = §8 V1–V5 A/B 实测，把 R4/R5 从 [待实测] 降为排除或坐实。
3. **[P0] segD U0200 采样有效性**：22:38 崩溃 → 22:46 重启采样，存在 8 min 空窗；请裁决 U0200 的 `fps_avg/units_seen` 是否需剔除崩溃局、或标注「含重启后重跑」。
4. **[P1] H1 分档失效专项**（沿用 RESULT [9]⑤）：不变，仍为性能 ROI 前提。
5. **[P1] enter_battle ESC 缺陷**（沿用 [9]④）：harness 已修（`harness_closeout_zc11.md`），待真机回归。
6. **[P1] 箭头键复位三件套**（沿用 [9]②）：建议固化进 harness（`bench_cam_reset.py` 已备）。
7. **[P2] vision-dirty 默认切换**（沿用 [9]①）：维持 force-full，先补帧率 A/B。
8. **[P2] 非线性混色桩**（沿用 [9]③）：先 G dump + 雾格分层。
9. **[新增 P1] 崩溃可观测性**：harness 在对局结束后应**主动检查 `except.txt` 存在性**并写入段记录（本次靠收尾才发现）；建议 `bench_replay.py` 增加 `except_watch` 步骤。
10. **[新增 P2] GameViewerIddDriver 虚拟显示层**：栈上出现其字符串与 `[ApiName] Hook Entered`；若后续崩溃复现，需把虚拟显示驱动/系统 Hook 纳入环境对照（与 cnc-ddraw 一并列为环境变量）。

---

## 附录 A —— 可复算

```powershell
python out/re_work/except_forensics/recompute_except_zc11.py          # 文本报告
python out/re_work/except_forensics/recompute_except_zc11.py --json   # JSON
```

产物：`out/re_work/except_forensics/recompute_{except,disasm,poison,timeline}.txt` + `recompute_record.json`。

前置：`pefile`、`capstone`（已装：capstone 5.0.7）。对 `ra2youli/`、`ra2bench/` **只读**。

## 附录 B —— 字节级核对（EIP）

| 源 | 十六进制 |
|---|---|
| except.txt L19 | `8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E …` |
| gamemd.exe @ RVA `0x3CFC9F` | `8b 0a 2b 4d f0 8b f1 89 4d f8 c1 fe 04 4e …` |
| 结论 | **逐字节一致** ⇒ 崩溃现场未被改写，EIP 归属可信 |
