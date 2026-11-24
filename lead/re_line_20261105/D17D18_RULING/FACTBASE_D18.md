# D-18 独立事实核证

2026-11-05。已按要求导入 `ra2tool.Engine`，只读原始 gamemd.exe，并亲自反汇编复算。目标 SHA256：`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。未执行游戏、未读写活进程、未修改被核证文件。

结论：三处指定字节均复现。`0xFFF7`（65527）确实是 SearchCore 外层节点展开轮数的上限，依据是同一循环计数器的零初始化、每轮递增、上限比较和退出收口。它不是剩余预算的递减变量，也不是“最多 65527 个不同格子”的直接计数。指定路径中调用方传入的 2000 没有被转发为预算，包装函数改传 -1，SearchCore 将负预算改为 65527。文档“硬编码 2000 个节点”的泛化断言与此路径矛盾。

## 五项结构化结果

```json
[
  {
    "supportsOption": "D18-1：调用方 push 2000 的字节成立",
    "detail": "亲验 ra2youli/gamemd.exe VA 0x004D3E3B，字节 68 D0 07 00 00，Engine 反汇编 push 0x7d0。紧邻 0x004D3E37 51、0x004D3E38 53、0x004D3E39 6A 00、0x004D3E47 52、0x004D3E48 50 共传六个参数，0x004D3E4B E8 50 7D FF FF 调 0x004CBBA0。因此 2000 是包装函数第三个栈参数；仅此 push 不能证明实际搜索预算为 2000。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D18-2：包装函数丢弃该 2000 预算并转发 -1 成立",
    "detail": "亲验 ra2youli/gamemd.exe VA 0x004CBC1B..0x004CBC23（含整条后继指令）字节 50 6A FF 6A FF 89 54 24 14：0x004CBC1B push eax，0x004CBC1C push -1，0x004CBC1E push -1，0x004CBC20 mov [esp+0x14],edx。注意题目截至 0x004CBC22 会截断这条 mov；截至 22 的原始字节为 50 6A FF 6A FF 89 54 24。已读完整包装函数 0x004CBBA0..0x004CBC40：序言 sub esp,0x14 / push esi / push edi，使参数 1..6 对应稳定栈偏移 +0x20..+0x34；第三参数 2000 位于 +0x28，没有被读取转发。0x004CBC13 8B 44 24 34 读取的是第六参数，不是 2000。随后七次 push 构成 0x0042C900 的参数，其中第五参数来自 0x004CBC1C 的 -1；0x004CBC31 E8 CA 0C F6 FF 实调 0x0042C900。其序言总栈调整 0x30，参数五在 +0x44；0x0042CBEA 8B 54 24 44 取该参数，0x0042CBFB 52 将其作为 SearchCore 参数五，0x0042CC02 E8 89 CE FF FF 调 0x00429A90。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D18-3：负预算缺省为 0xFFF7 的字节成立",
    "detail": "亲验 ra2youli/gamemd.exe 0x00429D59 C7 44 24 70 F7 FF 00 00 = mov dword ptr [esp+0x70],0xfff7。紧邻 0x00429D51 8B 44 24 70 取值，0x00429D55 85 C0 test eax,eax，0x00429D57 7D 08 jge 0x00429D61：只有有符号负值被替换；非负上限保留。SearchCore 序言 sub esp,0x4C 加四次保存寄存器 push，总栈差 0x5C，所以 [esp+0x70] 是第五栈参数，正对应第 2 项追到的 -1。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D18-4：0xFFF7 是外层节点展开轮数预算；不是其他无关计数器",
    "detail": "已进入并逐指令检查 ra2youli/gamemd.exe SearchCore 0x00429A90..0x0042A45D：重同步解码 2509/2509 字节，100.0%，失败 0。0x00429AB6 C7 44 24 28 00 00 00 00 将展开轮数 [esp+0x28] 置零；0x00429D6D 8B 4C 24 70 取预算，0x00429D71 8B 44 24 28 取轮数，0x00429D77 3B C1 比较，0x00429D79 0F 8D 5F 06 00 00 在轮数>=预算时跳 0x0042A3DE。其间 0x00429D7F 起读取当前开放集节点，0x00429DC2 起按方向枚举邻居，0x0042A1A1..0x0042A1AD 用独立的 [esp+0x18] 方向计数器递增到 8 并回跳；随后 0x0042A1BF..0x0042A3B5 对开放集做堆调整/移除当前节点并选下一节点。0x0042A3C9 8B 4C 24 28、0x0042A3D1 41、0x0042A3D4 89 4C 24 28 将外层轮数加一；0x0042A3D8 0F 85 8F F9 FF FF 在下一节点非空时返回预算比较。0x0042A3F2 3B 4C 24 70、0x0042A3F6 74 46 再次识别轮数等于预算并跳失败收口。因此预算是节点处理/展开轮数上限，不是路径长度、代价或邻居循环次数。到目标、开放集耗尽、其他早退可先结束；不能说每次都会用满 65527，更不能凭此断言运行耗时或慢帧根因。另 0x0042A3E2 81 F9 10 27 00 00 在退出收口比较 10000，但该处没有返回主循环的回边，不能据此称主循环硬上限 10000。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D18-5：文档确实声称 2000；该泛化表述需修订",
    "detail": "亲读 docs/re/pathfinding_deep_dive.md:46-51 与 68-74 及相邻表头。48 行原文：2. **纯 Dijkstra（无启发式）**：算法并非 A*，而是维护了开放集与累计代价值数组的均匀代价搜索（Uniform-Cost Search），最大展开深度被硬编码为 `0x7D0`（2000 个节点）。74 行原文：| `+0x3C` | `int` | `MaxNodeBudget` | 最大节点搜索预算，由外层传入（`0x7D0` = 2000） |。第 2-4 项证实指定路径的预算实为 -1→65527，不能采信硬编码 2000 的通用说法。另亲验 0x0042C927 8B 4C 24 4C / 0x0042C92F 89 4D 3C：this+0x3C 取的是 FindPath 第七参数；实际预算是第五参数。SearchCore 0x00429C10 8B 46 3C / 0x00429C13 85 C0 / 0x00429C15 74 08 仅按 this+0x3C 是否非零决定是否调用 0x0042ACF0，该字段不是本文确认的预算槽。此处不凭该条件调用进一步命名其完整语义。",
    "provenance": "我亲验"
  }
]
```

## 文档指定段落的原文摘录

`docs/re/pathfinding_deep_dive.md:46-51`：

> ### 核心逆向新发现
> 1. **工作区免清零机制（Generation Stamp）**：`PathFinder` 单例内部维护了一个 32 位生成计数器（`this+0x28`）。每次寻路仅递增计数器，节点访问标记直接与计数器比对，完全避免了每次寻路对 512×512 地图网格进行 `memset`，仅在 42 亿次计数器回绕时做一次整段清零。
> 2. **纯 Dijkstra（无启发式）**：算法并非 A*，而是维护了开放集与累计代价值数组的均匀代价搜索（Uniform-Cost Search），最大展开深度被硬编码为 `0x7D0`（2000 个节点）。
> 3. **3x3 差分方向查找表**：回溯函数 `0x0042AA90` 将前后格子的坐标差通过公式 `Index = 3 * dY + dX` 映射到全局常数表 `0x00818760`，直接解码出 0–7 经典 Westwood 8 方向。当 `|dX| > 1 || |dY| > 1` 时输出特殊方向 `8`（Tube 管道传送）。
> 4. **单例无全局起终点缓存**：`0x0087E8B8` 是无状态的单次搜索器，游戏中数十个单位同时被框选移动到同一地点时，引擎完全重复执行数十次全量 Dijkstra 搜索，这是群体移动掉帧的主要瓶颈。

`docs/re/pathfinding_deep_dive.md:68-74`：

```text
| `+0x24` | `DWORD*` | `pNodeCostArrayA` | 累计移动代价值数组（Dijkstra g-score） |
| `+0x28` | `DWORD` | **`GenerationStamp`** | **生成戳计数器**，每次 `FindPath` 递增，核心免清零标识 |
| `+0x2C` | `int` | `UnitSpeed` | 当前寻路单位的移动速度参数 |
| `+0x30` | `int` | `StartCellHeight` | 起点格子高度/桥面层级 |
| `+0x34` | `int` | `TargetCellHeight`| 终点格子高度/桥面层级 |
| `+0x38` | `BYTE` | `bIsBusy` | 寻路忙状态标志（入口置 1，退出置 0） |
| `+0x3C` | `int` | `MaxNodeBudget` | 最大节点搜索预算，由外层传入（`0x7D0` = 2000） |
```

这些引文只证明文档写了什么；本次未顺带核证引文中所有其他算法、性能或缓存结论。

## 亲跑命令与输出

先读 `lead/goal3t_nightwatch_20261102/swarm_20261104/ra2tool.py:1-17` 的解码纪律及 `51-85` 的实现：Engine 以 rb 读取 EXE、断言 SHA，按 PE section 映射 VA。以下为实际成功执行的集中核验命令；此处 SearchCore 覆盖率仅为指定函数，不冒称全 .text 普查。

```bash
python -I -c 'import sys; sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104"); from ra2tool import Engine; e=Engine(); print("SHA",e.sha);
for a,n in [(0x4d3e3b,5),(0x4cbc1b,9),(0x429d59,8),(0x429ab6,8),(0x429d6d,18),(0x42a3c9,21),(0x42a3f2,6),(0x42cbea,8),(0x42cbfa,13)]:
 print("RAW",hex(a),e.rd(a,n).hex(" "))
 for r in e.disasm(a,n): print(hex(r[0]),*r[1:])
a=0x429a90;z=0x42a45d;cur=a;decoded=0;fails=0
while cur<z:
 got=list(e.md.disasm(e.rd(cur,min(15,z-cur)),cur,count=1))
 if not got: cur+=1;fails+=1;continue
 decoded+=got[0].size;cur+=got[0].size
print("COVERAGE",decoded,z-a,100*decoded/(z-a),"FAILS",fails)'
```

输出：

```text
SHA 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
RAW 0x4d3e3b 68 d0 07 00 00
0x4d3e3b 68d0070000 push 0x7d0
RAW 0x4cbc1b 50 6a ff 6a ff 89 54 24 14
0x4cbc1b 50 push eax
0x4cbc1c 6aff push -1
0x4cbc1e 6aff push -1
0x4cbc20 89542414 mov dword ptr [esp + 0x14], edx
RAW 0x429d59 c7 44 24 70 f7 ff 00 00
0x429d59 c7442470f7ff0000 mov dword ptr [esp + 0x70], 0xfff7
RAW 0x429ab6 c7 44 24 28 00 00 00 00
0x429ab6 c744242800000000 mov dword ptr [esp + 0x28], 0
RAW 0x429d6d 8b 4c 24 70 8b 44 24 28 33 d2 3b c1 0f 8d 5f 06 00 00
0x429d6d 8b4c2470 mov ecx, dword ptr [esp + 0x70]
0x429d71 8b442428 mov eax, dword ptr [esp + 0x28]
0x429d75 33d2 xor edx, edx
0x429d77 3bc1 cmp eax, ecx
0x429d79 0f8d5f060000 jge 0x42a3de
RAW 0x42a3c9 8b 4c 24 28 8b 44 24 14 41 85 c0 89 4c 24 28 0f 85 8f f9 ff ff
0x42a3c9 8b4c2428 mov ecx, dword ptr [esp + 0x28]
0x42a3cd 8b442414 mov eax, dword ptr [esp + 0x14]
0x42a3d1 41 inc ecx
0x42a3d2 85c0 test eax, eax
0x42a3d4 894c2428 mov dword ptr [esp + 0x28], ecx
0x42a3d8 0f858ff9ffff jne 0x429d6d
RAW 0x42a3f2 3b 4c 24 70 74 46
0x42a3f2 3b4c2470 cmp ecx, dword ptr [esp + 0x70]
0x42a3f6 7446 je 0x42a43e
RAW 0x42cbea 8b 54 24 44 8b 44 24 40
0x42cbea 8b542444 mov edx, dword ptr [esp + 0x44]
0x42cbee 8b442440 mov eax, dword ptr [esp + 0x40]
RAW 0x42cbfa 51 52 50 56 53 57 8b cd e8 89 ce ff ff
0x42cbfa 51 push ecx
0x42cbfb 52 push edx
0x42cbfc 50 push eax
0x42cbfd 56 push esi
0x42cbfe 53 push ebx
0x42cbff 57 push edi
0x42cc00 8bcd mov ecx, ebp
0x42cc02 e889ceffff call 0x429a90
COVERAGE 2509 2509 100.0 FAILS 0
```

此外，本次亲跑了完整 SearchCore 及 0x0042C900 的反汇编，并读完整输出中节点处理、邻居枚举和堆调整段。最初从片段地址 0x004CBC10、0x004D3E10、0x004CBBD0 开始的局部反汇编含未对齐开头行，这些无效开头行未用作证据；随后已从完整函数入口 0x004CBBA0 重跑，解码 160/160 字节，所有包装函数指令一致。0x004CBC0C 调用的 0x00429780 已进入函数体，两个出口 0x0042981A C2 08 00 与 0x00429824 C2 08 00 均清理 8 字节，与包装函数栈偏移分析一致。未运行动态游戏性能测试，未声称此预算直接解释历史慢帧。
