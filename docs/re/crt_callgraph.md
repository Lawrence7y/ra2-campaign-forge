# gamemd.exe 内嵌 CRT 调用图与池化逆向报告

> 目标：`gamemd.exe`（YR 1.001）ImageBase `0x400000`
> 范围：`.text` 内对 `_new / _delete / malloc / free / sprintf / vsprintf` 的直接 `CALL`（E8 rel32）
> 目的：为 perf 热点桶 `0x7C9300 / 0x7C9200`（约占忙时 2.4%）提供「谁在热路径上调分配与格式化」的逆向依据，指导池化 / 去 sprintf
> 方法：静态扫描（Capstone 线性反汇编 + 调用者聚合 + format 字符串回溯），**未改任何源码 / 补丁**

---

## 1. 扫描方法（可复现）

### 1.1 PE 与地址换算

```
ImageBase = 0x400000
.text  VA 0x00401000 .. 0x007E038D   (raw size 0x3E0000)
.rdata VA 0x007E1000 .. 0x00811074
.data  VA 0x00812000 .. 0x00B79BE4
文件偏移 = VA - 0x400000   （仅当 RVA 落在对应节内，需按节表换算）
```

### 1.2 CRT 入口（YRpp/CRT.h 已标注，本轮反汇编核实）

| 符号 | 地址 | 序言 / 语义 | 说明 |
| :--- | :--- | :--- | :--- |
| `CRT::_new` | `0x7C8E17` | `6A 01 FF 74 24 08 E8 ...` → `push 1; push size; call 0x7C9442` | operator new，size 从栈，flag=1 |
| `CRT::_delete` | `0x7C8B3D` | `FF 74 24 04 E8 ...; 59 C3` → `push p; call free` | **薄封装，本质就是 free** |
| `CRT::malloc` | `0x7C9430` | `FF 35 [0xB782C4]; FF 74 24 08; E8 ...` | 带堆句柄的 malloc |
| `CRT::free` | `0x7C93E8` | `push 9; call lock; push p; call heap_free` | 带锁的堆释放 |
| `CRT::sprintf` | `0x7C8EF4` | `55 8B EC 83 EC 20 ...` | 标准 sprintf |
| `CRT::vsprintf` | `0x7CB7BA` | — | 仅 1 处调用 |
| `CRT::strncpy` | `0x7C91D0` | 字长对齐 4 字节拷贝环在 `0x7C920B..0x7C9261` | **落在热点桶 0x7C9200** |
| `__alldvrm` 等 | `0x7C9380` 起 | 64 位除法辅助 | **落在热点桶 0x7C9300** |

> 热点桶归因修正：`0x7C9200` 不是 malloc/free，而是 **`strncpy` 的字拷贝内环**；`0x7C9300` 除 `free` 入口外还含 **64 位除法辅助例程**。分配器本体在 `0x7C9442`（malloc/new 公共例程）。

### 1.3 扫描流程（Python 伪码）

```python
# 1) 解析 PE 节表，取 .text 字节
# 2) Capstone 线性反汇编 .text，收集:
#      calls:  [(site_va, target_va), ...]     # 仅 E8 rel32 且 target 为 IMM
#      push_imm: [(site_va, imm32), ...]       # 用于 format / size 回溯
# 3) 对每个 call site，若 target ∈ CRT 表，则:
#      caller = 含该 site 的函数起点
#        - 优先: 从 site 向前回溯最近的函数序言
#          (55 8B EC / 8B FF 55 8B EC / 53 8B DC / 56 8B F1 / 6A FF / 83 EC ...)
#        - 兜底: 全 .text 所有 CALL 目标中 ≤ site 的最大者 (bisect)
# 4) 按 caller 聚合计数
# 5) sprintf: 从 call site 向前最多 32 字节扫 `68 imm32` (push imm),
#      若 imm 落在 .rdata/.data 且可读为 C 字符串 → 记为 format
# 6) _new 尺寸: call site 前 6 字节若是 `68 imm32` / `6A imm8`，记为分配尺寸
# 7) 热路径判定: 反向调用图 BFS，与帧根集合的跳数
#      帧根 = FrameTimer 0x53E770 / TacticalClass::Render / Draw 系列 /
#             SelectAutoTarget / Greatest_Threat / Sidebar 最小地图等
# 8) 归属命名: out/reverse/symbols.json 虚表槽位 + YRpp JMP 地址 + RE 档案
```

完整脚本逻辑见本轮临时产物（`crt_callgraph_scan.py` / `crt_scan2.py` / `classify.py`），核心可迁移到 `tools/xref_scan.py` 的 `xrefs` 子命令扩展。

---

## 2. 全局调用量级

| CRT 函数 | 静态 CALL 点数 | 不同调用者函数数 | 量级评价 |
| :--- | ---: | ---: | :--- |
| `_delete` | **4498** | ~1260 | 最高，且 `_delete`≡`free` |

> 【勘误 2026-09-30 · R-E06 · errata_sync】计数口径注记（不改上表原值）：上表 `_delete` **4498** 为 **线性反汇编口径**；模式扫描+指令边界确认真值 **≥ 4499**（多出的第 4499 处 = `0x0074836A`，`E8 CE 07 08 00`，全局指针单例释放；线性口径在 `0x0074835A` 相位脱节漏记）。引用静态量级时须标口径；相对差 0.02%，不影响池化决策。权威：ARCHITECTURE_ATLAS.md:4472-4478（Δ=1 定谳）/ atlas_rev/R8_ui_crt.md:330。原文保留不删字。
| `_new` | **2832** | ~1206 | 次高 |
| `sprintf` | **317** | 165 | 中等，但分散 |
| `free` | 172 | 67 | 低（多数走 `_delete`） |
| `malloc` | 54 | 39 | 低（引擎内部主要用 `_new`） |
| `vsprintf` | **1** | 1 | 可忽略 |

> 说明：以上是**静态指令条数**，不是运行期动态次数。运行期次数需挂桩统计；但静态 Top 调用者与 perf 桶 `0x7C9300`（free/除法）高度相关——`_delete`→`free` 链路是最大静态入口。

---

## 3. Top 调用者（合并 `_new/_delete/malloc/free/sprintf`）

排序按「该函数内 CRT 调用点总数」。「热路径」= 反向调用图 ≤3 跳可达帧根。

| # | 调用者地址 | 次数量级 | 内容拆分 | 推测功能 | 热路径 | 建议 |
| ---: | :--- | ---: | :--- | :--- | :--- | :--- |
| 1 | `0x004E97B0` | **362** | new 78 / del 284 | `VectorClass<T>::v[3]` 清空/析构（`push esi; mov esi,ecx; xor ebx,ebx; mov eax,[esi+4]; cmp byte [esi+0xd],bl; push eax; call _delete`）——释放自有缓冲 | 间接 | **缓冲池化 #1** |
| 2 | `0x006BB9A0` | 269 | new 163 / del 105 | 大型 SEH 函数（`sub esp,0xE1C`），疑 UI/INI 解析或载入流程；new 尺寸 8/48/64/96/116… | 载入 | 尺寸池 + 载入后冻结 |
| 3 | `0x00600630` | 204 | new 95 / del 97 / sprintf 12 | 小对象构造（双 `Wstring` 成员）+ `sprintf("%sTUR"/"%sBARL"/"b%c%c_li%d.pcx")` 拼路径 | 载入/UI | 路径串缓存 |
| 4 | `0x0072B820` | 185 | del 161 | 全局单例清理（读 `[0xB0FBA0]` vcall + 释放 `[0xB0FB9C]`） | 关局 | 不必优化 |
| 5 | `0x0052FF90` | 158 | new 142 / del 4 / sprintf 12 | `MixFileClass::ctor` 链（ctor `0x5B3C20`），MIX 资源索引 | **启动** | 预分配 / 延迟 |
| 6 | `0x0048EBF0` | 116 | new 114 / del 2 | 反复 `push 8; call _new` 造 8 字节节点，写 vtable `0x7E5B70` | 载入/列表 | **8B 节点 freelist** |
| 7 | `0x00490E50` | 119 | del 117 | `RLEBlitTransLucent25AlphaZReadWrite` 系（ConvertClass 缓冲释放） | 渲染 | 帧缓冲复用 |
| 8 | `0x004E6AE0` | 89 | del 86 | `TechnoArrayInit` / `DynamicVectorClass@Techno` 清空 | 关局/重载 | 不必优化 |
| 9 | `0x0064DEA0` | 87 | new 43 / del 43 / sprintf 1 | 读 `HouseClass::Player`（`0xA83D4C`）+ sprintf —— 分数/外交 UI | UI | 禁帧内 sprintf |
| 10 | `0x006C6400` | 84 | new 69 | `VectorClass` 容量扩展（`cmp [esi+0x10],[esi+0x8]; call [edx+8]`） | 间接 | **预留容量** |
| 11 | `0x007D6146` | 77 | malloc 7 / free 70 | CRT 自身字符串/缓冲管理 | 内部 | 桶内自耗 |
| 12 | `0x005A9A20` | 63 | new 58 | 8 字节节点构造（`word/word/dword` 字段） | 载入 | 8B freelist |
| 13 | `0x004B6C30` | 60 | new 30 / del 30 | 读 `ScenarioClass::Instance`（`0xA8B230`）+ `HouseClass::Player` —— 存档/侧栏 | UI | 禁帧内 sprintf |
| 14 | `0x00711840` | ~50 | sprintf 15 | `WeaponTypeClass` INI 读取（`sprintf("Weapon%d"/"EliteWeapon%d")`） | **rules 载入** | 允许 |
| 15 | `0x0049B720` | 37 | del 9 / sprintf 10 | 字符串指针数组释放 + `sprintf("Map%d"/"%s%d"/"%02d:%02d:%02d")` | 地图/UI | 路径缓存 |

### 3.1 模式归类（对 Top 统计的语义压缩）

| 模式 | 静态占比（`_new`） | 静态占比（`_delete`） | 特征 |
| :--- | ---: | ---: | :--- |
| **Vector / DynamicVector 缓冲增长与清空** | ~22%（625/2832） | **~38%**（1708/4498） | `v[3]` 槽；`[esi+4]=buf, [esi+0xC]=count, [esi+0xD]=owned` |

> 【勘误 2026-09-30 · R-E06 · errata_sync】口径注记：分母 `4498` 为线性反汇编口径，真值 ≥4499（见上方 R-E06 注）。占比为近似值，口径差 0.02% 不影响结论。原文保留不删字。
| 链表/小节点 new | ~15% | ~5% | `push 8 / push 12 / push 16; call _new` |
| 游戏对象构造 | ~20% | ~10% | new 后紧跟 ctor（如 `MixFileClass::ctor 0x5B3C20`） |
| 载入/INI/UI 字符串 | <5% | <5% | 伴随 sprintf |
| 未归属（普通自由函数） | ~40% | ~40% | 需下一轮逐个命名 |

---

## 4. `_new` 尺寸分布（池化优先级）

从 `push imm; call _new` 模式提取的静态尺寸频次：

| 尺寸 | 静态点数 | 推测对象 | 池化优先级 |
| ---: | ---: | :--- | :--- |
| **16 (0x10)** | 192 | 双指针节点 / 小结构 | **P0** |
| **8 (0x8)** | 166 | 单指针+标志节点（`0x48EBF0` 簇） | **P0** |
| **456 (0x1C8)** | 145 | 中型游戏对象（Type/Control 片段，ctor 写多 vtable） | **P0** |
| **12 (0xC)** | 130 | 三字段节点 | **P1** |
| 4 (0x4) | 73 | 标量/单指针 | P1 |
| 24 (0x18) | 65 | 小记录 | P1 |
| 40 (0x28) | 57 | 对话/控件 | P2 |
| 32 (0x20) | 43 | 小对象 | P2 |
| 20 (0x14) | 32 | — | P2 |
| 133 (0x85) | 29 | 路径/短缓冲 | P2 |
| 256 (0x100) | 25 | 页/缓冲 | P2 |
| 176 (0xB0) | 22 | — | P2 |
| 392 (0x188) | 21 | — | P2 |
| 1824 (0x720) | 13 | 大块（Vector 扩容目标） | P3 |

> `0x1C8`（456 字节）出现 145 次且无单一 `push 0x1C8` 立即数模式（多为 `mov reg,0x1C8; push reg` 或计算得来），说明是**结构体固定尺寸**，适合对象池。

---

## 5. sprintf / vsprintf format 字符串

### 5.1 Top format（按静态出现次数）

| 次数 | format | 主要调用者 | 场景 | 热路径 | 建议 |
| ---: | :--- | :--- | :--- | :--- | :--- |
| **34** | `"%d"` | 24 个函数（`0x41AF80` `0x44FEC8` `0x474430` `0x4F1CA0` `0x5253B0` `0x55F6E0` …） | 整数格式化，分散在 UI/调试/存档 | **部分** | **禁止帧内；改 itoa/预格式化** |
| 13 | `"DDRAW.DLL Error code = %08X"` | `0x4A3890` 簇（DDRAW 错误） | 错误路径 | 否 | 保留 |
| 12 | `"%d,%d,%d"` | `0x42ED60` `0x45FA90` `0x474B50` `0x529A30` | 坐标/RGB 三元组 | 载入/INI | 允许 |
| 6 | `"%sTUR"` / `"%sBARL"` | `0x5F6810` `0x5F8080` | Voxel 炮塔/炮管部件名 | 载入 | **首次构建后缓存** |
| 6 | `"%c:\\"` / `"\\\\.\\%c:"` | `0x478441` `0x52B620` | 盘符/设备路径 | 启动 | 允许 |
| 4 | `"Map%d"` | `0x49C0D0` `0x49C5A0` `0x49D390` `0x49DB00` | 地图名 | UI | 缓存 |
| 4 | `"%s.MAP"` | `0x5C01F0` `0x5C3EC0` | 地图文件 | 载入 | 允许 |
| 4 | `"%d,"` / `"%d,%d"` | 多处 | 序列化 | 存档 | 允许 |
| 3 | `"%02d:%02d:%02d"` | `0x49B930` `0x52AAF1` | 时间显示 | UI（可能帧内） | **限频/缓存** |
| 3 | `"mphmd.exe %d.%d.%d.%d"` | `0x663910` | 版本号 | 启动 | 允许 |
| 3 | `"Waypoint%d"` | `0x689310` `0x689E90` | 路点名 | 编辑/载入 | 允许 |
| 2 | `"MAPS%02d.MIX"` `"MOVIES%02d.MIX"` `"MAPSMD%02d.MIX"` `"MOVMD%02d.MIX"` | `0x478441` `0x530466` | MIX 卷名 | **启动** | 允许 |
| 2 | `"Weapon%d"` `"EliteWeapon%d"` | `0x711840` | rules.ini 武器段 | **rules 载入** | 允许 |
| 2 | `"%S"` | `0x5BD245`（唯一 `vsprintf` 调用者） | 宽字符桥接 | UI | 限制 |
| 2 | `"%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%d,%d,%d,%s,%s:"` | `0x5D93D0` `0x77E430` | 多人/网络序列化 | 网络 | 允许 |
| 2 | `"SAVE%04lX.%3s"` | `0x558DD0` | 存档文件名 | 存档 | 允许 |
| 2 | `"Button%02d.SHP"` | `0x6CFE20` `0x6D0680(TabClass)` | UI 按钮 | UI 载入 | 允许 |
| 2 | `"b%c%c_li%d.pcx"` 等 | `0x600630` | 载入图 PCX | 载入 | 允许 |

### 5.2 vsprintf

仅 1 处：`0x005BD1F0` → `0x005BD245`，format `"%S"`，属宽字符输出桥接，**不在战斗帧路径**。

### 5.3 禁止 / 限制清单

| 级别 | 场景 | 理由 |
| :--- | :--- | :--- |
| **禁止（帧内）** | 任何 `"%d"` / `"%d,%d"` 在 Draw / Update / SelectAutoTarget / 网络帧处理中 | 数值格式化可用 `itoa` 或预写缓冲，省掉整条 sprintf → vsprintf → 输出环 |
| **禁止（帧内）** | `"%sTUR"` / `"%sBARL"` 若在每帧 Voxel 装配路径重复执行 | 首次构建后缓存字符串 |
| **限频** | `"%02d:%02d:%02d"` 时钟、分数面板 | 1 Hz 刷新即可 |
| 允许 | MIX/MAP/PCX/Weapon/SAVE 路径与版本号 | 启动或一次性 |
| 允许 | `DDRAW.DLL Error code` | 仅错误分支 |

---

## 6. 启动/加载 vs 战斗帧内

| 类别 | 代表地址 | 依据 | 优化优先级 |
| :--- | :--- | :--- | :--- |
| **启动 / 资源载入** | `0x52FF90`（MixFileClass ctor 链）、`0x711840`（WeaponType INI）、`0x4790B0`（`MOVIES%02d.MIX`/`%c:\\`）、`0x530460`（MAPS/MOVIES MIX） | 格式串与 ctor 表明一次性载入 | 低（可预分配，不值得复杂池） |
| **rules / 地图载入** | `0x711840`、`0x5C01F0`、`0x689310` | `Weapon%d`、`%s.MAP`、`Waypoint%d` | 低 |
| **UI 构建 / 一次性** | `0x600630`（PCX 路径）、`0x64DEA0`（分数 UI）、`0x4B6C30`（侧栏/存档）、`0x49B720`（Map%d 数组） | 读 Player/Scenario 单例 + 字符串拼接 | 中（限频 sprintf） |
| **关局 / 清理** | `0x72B820`、`0x4E6AE0`（TechnoArrayInit 清空）、`0x667A30`（ScenarioClass::dtor） | 大量 `_delete` 无对应 `_new` | 不必优化 |
| **帧内风险（优化目标）** | `VectorClass::v[3]` 清空与 `DynamicVectorClass` 扩容（`0x4E97B0`、`0x6C6400`、`0x40BA50` 等）；`0x48EBF0` 8B 节点；`0x490E50` Convert 缓冲 | 实体生成/死亡、目标列表重建、渲染换算表时触发 | **P0** |
| **纯 CRT 内部** | `0x7D6146`（malloc/free 串管理）、`0x7D6494` | 自耗 | 桶内 |

> 直接 CRT 调用在 `TechnoClass::SelectAutoTarget`（`0x6FB010`）、`TechnoClass::Greatest_Threat`（`0x6F8DF0`）、`UnitClass::Draw` 等**本体内为 0**——它们的热点不在格式化/分配，而在算法本身（与 L2 节流结论一致）。但它们**间接**通过 Vector 清空、目标列表重建触发 `_delete`。

---

## 7. 池化建议

### 7.1 对象池（按优先级）

| 优先级 | 尺寸 | 措施 | 预期收益 |
| :--- | ---: | :--- | :--- |
| **P0** | 8 / 12 / 16 字节 | 三级 freelist（TLS 或单线程全局），拦截 `_new/_delete` 中对应尺寸；节点类对象 ctor/dtor 改为 pop/push | 削减最高频小块抖动 |
| **P0** | 456 (0x1C8) | 对象池（构造时从池取，析构归还）；对应 145 个静态构造点中的热对象 | 消除中型块碎片 |
| **P1** | 24 / 32 / 40 字节 | 并入 freelist 分档 | 覆盖小记录 |
| **P1** | Vector 缓冲（8/16/32/64…倍增） | `DynamicVectorClass` 扩容改为几何增长 + **最小预留**；高频 Vector 在创建时 `Reserve` 到典型峰值 | 直接砍 `_new/_delete` 中 Vector 份额（`_delete` 的 38%） |
| **P2** | 133 (0x85) / 256 (0x100) | 字符串缓冲复用（thread-local scratch） | 配合去 sprintf |

### 7.2 建议拦截的分配入口

| 入口 | 地址 | 做法 |
| :--- | :--- | :--- |
| `CRT::_new` | `0x7C8E17` | 按 size 分档查 freelist；miss 再调原 `0x7C9442` |
| `CRT::_delete` | `0x7C8B3D` | 与 `_new` 对称归还（注意当前实现是 `call free`，池化后需旁路） |
| `CRT::malloc/free` | `0x7C9430` / `0x7C93E8` | 仅 CRT 内部字符串用，量小，可暂缓 |
| `VectorClass::v[3]` 族 | 多地址 | 优先改「预留容量」而非拦截 |

### 7.3 sprintf 治理

1. **帧内禁止 `"%d"` 族**：在 Draw/Update/UI 刷新路径上，用 `CRT::_itoa` 或手写十进制转换 + `memcpy`。
2. **路径类 format 保持**（MIX/MAP/PCX/Weapon/SAVE）：启动一次性，收益低。
3. **Voxel 部件名（`%sTUR`/`%sBARL`）**：首次拼好存入 Type 对象，之后指针复用。
4. **时钟/分数**：限频到 1 Hz 或状态变更时才重算。
5. `vsprintf`（`0x7CB7BA`）仅 1 处，无需治理。

---

## 8. 与 perf 桶的对应关系

| 热点桶 | 实际内容 | 本报告对应 |
| :--- | :--- | :--- |
| `0x7C9200` | `strncpy`（`0x7C91D0`）的 4 字节拷贝内环 `0x7C920B..0x7C9261` | 字符串拷贝，与 path/format 拼接同源 |
| `0x7C9300` | `free`（`0x7C93E8`）+ `__alldvrm` 64 位除法辅助（`0x7C9380` 起） | `_delete`→`free` 链是主因；除法辅助来自 printf/格式化 |
| （相邻）`0x7C9400` | `malloc`（`0x7C9430`）→ 公共分配器 `0x7C9442` | `_new`/`malloc` 入口 |

> 结论：2.4% 忙时主要由 **`_delete`/`free` 高频调用**（Vector 清空 + 小节点）与 **strncpy/格式化辅助**构成，而非「分配器算法慢」。LFH 已上，下一步是**减少调用次数**（池化 + 预留），而非换分配器。

---

## 9. 后续扩展方向

1. **动态计数**：在 `_new/_delete/sprintf` 入口挂桩（`ra2render` 已有 LFH 时机，可加计数器），回放 `loadbench` 得到真实频次与尺寸直方图，校正静态排名。
2. **函数命名补全**：对 Top 中 `unattrib` 的地址（`0x6BB9A0` `0x600630` `0x72B820` 等）继续对照 YRpp 与 `symbols.json` 命名。
3. **Vector 预留策略**：统计各 `DynamicVectorClass` 实例的峰值容量（构造点尺寸），写死 `Reserve`。
4. **`strncpy` 调用图**：本报告聚焦分配与格式化；`strncpy`（桶 0x7C9200）可单独做一轮调用图，与去 sprintf 合并收益。

---

## 10. 可复现代码片段（精简）

```python
# crt_callgraph 核心片段
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, x86

CRT = {"_new":0x7C8E17, "_delete":0x7C8B3D,
       "malloc":0x7C9430, "free":0x7C93E8,
       "sprintf":0x7C8EF4, "vsprintf":0x7CB7BA}

def load_text(path, image_base=0x400000):
    data = open(path, "rb").read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec_off = e_lfanew + 24 + opt_size
    for i in range(nsec):
        off = sec_off + i * 40
        name = data[off:off+8].rstrip(b"\0")
        if name == b".text":
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, off + 8)
            return data, image_base + vaddr, data[rawptr:rawptr+rawsize]
    raise ValueError("no .text")

data, tva, code = load_text(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

calls, pushes = [], []
pos = 0
while pos < len(code):
    advanced = False
    for ins in md.disasm(code[pos:], tva + pos):
        advanced = True
        if ins.mnemonic == "call" and ins.operands[0].type == x86.X86_OP_IMM:
            calls.append((ins.address, ins.operands[0].imm & 0xFFFFFFFF))
        elif ins.mnemonic == "push" and ins.operands[0].type == x86.X86_OP_IMM:
            pushes.append((ins.address, ins.operands[0].imm & 0xFFFFFFFF))
        pos = ins.address - tva + ins.size
    if not advanced:
        pos += 1

from collections import Counter, defaultdict
inv = {v: k for k, v in CRT.items()}
stats = defaultdict(Counter)
for site, tgt in calls:
    if tgt in inv:
        stats[inv[tgt]][site] += 1   # 后续按函数序言归并 site → caller
```

---

## 11. 结论摘要

1. **静态量级**：`_delete` 4498 ≫ `_new` 2832 ≫ `sprintf` 317 ≫ `free` 172 ≫ `malloc` 54 ≫ `vsprintf` 1。

> 【勘误 2026-09-30 · R-E06 · errata_sync】口径注记：`_delete` 4498 为线性反汇编口径，模式扫描真值 ≥4499（第 4499 处 = `0x0074836A`）。引用时须标口径；排序与量级结论不变。原文保留不删字。
2. **最大调用者簇**是 `VectorClass/DynamicVectorClass` 的缓冲清空与扩容（`v[3]` 槽），约占 `_delete` 静态点的 38%。
3. **尺寸池化首选**：8 / 12 / 16 字节节点 + 456 (0x1C8) 中型对象。
4. **sprintf 禁令**：帧内 `"%d"` 族；`%sTUR/%sBARL` 缓存；时钟限频。载入类 format 保留。
5. **热点桶 `0x7C9200` = strncpy 内环，`0x7C9300` = free + 64 位除法辅助**——优化点是「少调用」，不是「换算法」。
6. AI 帧函数（`SelectAutoTarget` / `Greatest_Threat`）本体不直接碰 CRT；其分配压力来自列表/Vector 间接路径。

---

*扫描工具：Capstone 5.0.7；命名来源 `YRpp/CRT.h`、`out/reverse/symbols.json`（988 类 vfunc）、`REVERSE_ENGINEERING_AND_PATCHES.md`。*
