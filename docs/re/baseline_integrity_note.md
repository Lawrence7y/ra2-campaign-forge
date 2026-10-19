# 二进制基线完整性备忘录 (Baseline Integrity Note)

> **修订版本**：v1.0 (S22 终审定案)  
> **审计对象**：`ra2youli/gamemd.exe` vs `ra2youli/.ra2opt/orig/gamemd.exe`  
> **基线准绳**：`out/reverse/symbols.json` 与 `docs/re/anchor_claims.txt`  
> **自动化套件**：[`tools/verify_anchors.py`](file:///d:/Project/ra2-campaign-forge/tools/verify_anchors.py)  
> **保真裁定**：`.text` 代码段 100% 原始纯洁，全库 323 处决定性锚点绝对有效，基线稳固！

---

## 一、 核心结论总览 (Executive Summary)

在针对尤里复仇核心二进制文件（`gamemd.exe`，ImageBase `0x00400000`）的逆向工程推进至第五波（S21–S23）期间，多项跨文档交叉审计曾暴露出关于**基线哈希漂移**、**PE 头差异**与 **.detour 段性质**的重大疑点。

经 Lead 与 S22 专项子代理联合复算、二进制逐字节比对（Byte-by-Byte Diff）以及 PE 结构深度逆向，现对全局基线做出以下**不可动摇的终审裁定**：

```
[基线裁定矩阵]
┌───────────────────┬────────────────────────────────────────────────────────┬──────────┐
│ 审计维度          │ 核心定案事实                                           │ 裁定状态 │
├───────────────────┼────────────────────────────────────────────────────────┼──────────┤
│ .text 段完整性    │ 严格以 raw(SizeOfRawData) 口径为准，SHA-256 100% 匹配  │ ✅ PASS  │
│                   │ 记录值: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a20...   │          │
├───────────────────┼────────────────────────────────────────────────────────┼──────────┤
│ 口径差误报排查    │ vsize 口径哈希为 bf9d56ae...，系未包含链接器填充导致   │ 澄清消除 │
├───────────────────┼────────────────────────────────────────────────────────┼──────────┤
│ PE 头 2 字节差异  │ 偏移 0xAE (0x00→0x20) 与 0xB2 (0x10→0x40)，为 perf 栈 │ ✅ 确认  │
│                   │ 保留扩容(1M→4M)，代码段 0 字节改动，保真度 100%        │          │
├───────────────────┼────────────────────────────────────────────────────────┼──────────┤
│ .detour 段性质    │ 官方 2001 构建自带 Microsoft Detours 1.x 结构体        │ ✅ 原生  │
│                   │ 首部魔数 "Dtr\0"，vsize=0x2718, rawsize=0x3000         │          │
├───────────────────┼────────────────────────────────────────────────────────┼──────────┤
│ 代码注入防护红线  │ 严禁向 .detour 段写入任何 Hook 跳板；必须使用独立 Cave │ 🔴 红线  │
└───────────────────┴────────────────────────────────────────────────────────┴──────────┘
```

---

## 二、 关键深度剖析一：`raw(SizeOfRawData)` vs `vsize(Misc_VirtualSize)` 口径裁定

### 1. 现象与矛盾暴露
在执行自动化完整性审计脚本（如早期的 `_audit_integrity.py`）时，部分子代理直接读取 PE 节头的 `Misc_VirtualSize`（`0x003DF38D`）切片并计算 SHA-256，得出：
$$\text{SHA-256}_{\text{vsize}} = \texttt{bf9d56aea20a9e52432bbc152e8ff08d334712955e2689455770b8333779908e}$$
而早期逆向工作总台账 `out/reverse/symbols.json` 中记录的黄金基准值为：
$$\text{SHA-256}_{\text{recorded}} = \texttt{c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738}$$
二者不一致，一度引发“二进制是否在测试中被污染篡改”的恐慌与争议。

### 2. 深入 MSVC 链接机制复算
检查 `gamemd.exe` 中 `.text` 段的 PE 结构定义：
- **虚拟地址 (VA)**：`0x00401000`（`RVA = 0x00001000`）
- **文件物理偏移 (PointerToRawData)**：`0x00001000`
- **代码有效虚拟尺寸 (Misc_VirtualSize)**：`0x003DF38D`（2,487,181 字节）
- **磁盘物理对齐尺寸 (SizeOfRawData)**：`0x003E0000`（2,490,368 字节，按 `FileAlignment = 0x1000` 对齐）
- **尾部补齐差额**：
  $$\Delta = \text{SizeOfRawData} - \text{Misc_VirtualSize} = \text{0x003E0000} - \text{0x003DF38D} = \text{0x00000C73} \quad (3,187 \text{ 字节})$$

这 $3,187$ 字节为 MSVC 6.0 链接器在生成 PE 文件时，为了按 4KB 扇区对齐而填充在磁盘上的空字节（主要是 `\0` 或 `\xCC` 调试陷阱）。

### 3. 终审定案
当对整个物理段 `data[0x1000 : 0x1000 + 0x3E0000]` 进行 SHA-256 计算时：
$$\text{SHA-256}_{\text{raw}} = \texttt{c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738} \quad (\bigstar \mathbf{100\%\ MATCH})$$

> [!IMPORTANT]
> **全库规约**：
> `symbols.json` 起点记录的是物理磁盘镜像的完整段数据哈希。**今后任何自动化校验与完整性审计工具，必须严格使用 `raw(SizeOfRawData)` 口径**。严禁仅对 `Misc_VirtualSize` 算哈希，彻底杜绝口径差误报！

---

## 三、 关键深度剖析二：PE 头偏移 0xAE/0xB2 处 2 字节差异还原

### 1. 逐字节全镜像扫描事实
对生产工作副本 `ra2youli/gamemd.exe` 与原始干净备份 `ra2youli/.ra2opt/orig/gamemd.exe` 执行全量字节级比对（总尺寸均为 4,825,360 字节），全文件仅有**恰好 2 个字节**存在差异：

```
[文件逐字节差异定位]
文件偏移 0x000000AE:  Orig = 0x00  |  Curr = 0x20
文件偏移 0x000000B2:  Orig = 0x10  |  Curr = 0x40
（全文件其余 4,825,358 字节完全一致，.text / .rdata / .data / .rsrc / .detour 零修改）
```

### 2. PE 规范结构体逆向解构
在 `gamemd.exe` 中，DOS 头偏移 `0x3C` 处读取 `e_lfanew = 0x00000050`：
- `0x0050..0x0053`: PE 签名 `PE\0\0`
- `0x0054..0x0067`: `IMAGE_FILE_HEADER`（COFF 文件头，共 20 字节）
- `0x0068..0x0147`: `IMAGE_OPTIONAL_HEADER32`（PE 可选头，共 224 字节）

将差异字节映射到 PE 结构定义：
1. **偏移 0x000000AE**（可选头偏移 $+70$ 字节）：
   对应 `IMAGE_OPTIONAL_HEADER32.DllCharacteristics`（Word，2 字节，位于 `0xAE..0xAF`）。
   - 原版值：`0x0000`
   - 现版值：`0x0020`（启用了 `IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA` / 终端服务器/兼容性标志位）
2. **偏移 0x000000B2**（可选头偏移 $+74$ 字节）：
   对应 `IMAGE_OPTIONAL_HEADER32.SizeOfStackReserve`（Dword，4 字节，位于 `0xB0..0xB3`）。
   - 原版值：`0x00100000`（小端编码：`00 00 10 00`，即 **1MB** 栈保留空间）
   - 现版值：`0x00400000`（小端编码：`00 00 40 00`，即 **4MB** 栈保留空间）
   - 导致其第 3 个字节（偏移 `0xB2`）由 `0x10` 变为 `0x40`。

### 3. 操作源头归因与保真证明
查验工程根目录日志 `ra2youli/.ra2opt/manifest.json`：
```json
{
  "run_id": "20260925-161048",
  "command": "ra2opt apply perf",
  "actions": [
    "expand_stack_reserve: 1MB -> 4MB (offset 0xB0)",
    "set_dll_characteristics: 0x0020 (offset 0xAE)"
  ]
}
```
**归因结论**：
该修改为 `ra2opt` 性能套件为了避免原版游戏在大规模 AI 复杂寻路与多单位火拼时产生深层递归栈溢出（Stack Overflow Crash），而在二进制头部施加的**良性栈扩容补丁**。
它既没有移动任何节区，也没有向代码段插入任何字节。经 `ra2opt restore` 可以 100% 原样还原为原始的 `0x00` 与 `0x10`。

因此，**当前生产环境下的 `.text` 与全部逻辑代码处于 100% 原始未动状态**！

---

## 四、 关键深度剖析三：`.detour` 段原生自带 `"Dtr\0"` 签名与禁写入红线

### 1. 结构与尺寸实测澄清
早先部分逆向报告曾猜测 `.detour` 段是第三方注入物，甚至估算“尺寸为 6,980 字节”。经 S22 联合复算，实测数据如下：
- **节名称**：`.detour`
- **虚拟地址 (VA)**：`0x00B93000`（`RVA = 0x00793000`）
- **文件物理偏移 (PointerToRawData)**：`0x00497000`
- **实际虚拟大小 (Misc_VirtualSize)**：`0x00002718`（**10,008 字节**）
- **文件物理大小 (SizeOfRawData)**：`0x00003000`（**12,288 字节**）
- **段首前 32 字节十六进制**：
  ```
  40 00 00 00 44 74 72 00 c0 25 00 00 c0 25 00 00
  e0 f0 40 00 40 01 00 00 00 00 00 00 00 00 00 00
  ```
  其中 ASCII 对应：`@\0\0\0Dtr\0`。

### 2. 原生性实证
在官方原始备份 `ra2youli/.ra2opt/orig/gamemd.exe` 中，该 `.detour` 段与上述 32 字节数据**完全存在且逐字节一致**。
这表明：**Westwood / EA 在 2001 年编译打包《尤里复仇》1.001 时，其工程管道原生集成了 Microsoft Research Detours 1.x 库**，用于处理内部函数重定向或早期的补丁分发。

### 3. 禁写禁注入红线（Safety Redline）
早期子代理曾提出“利用 `.detour` 段内未使用的空间作为内存代码洞（Code Cave），写入联机网络同步修复（Net Sync Fix）的跳板代码”。

> [!CAUTION]
> **绝对禁令（DO NOT TOUCH .detour）**：
> 1. 原生 `.detour` 段包含 Westwood 官方 Detours 运行时的数据结构与宿主跳转表，任何盲目覆盖都会损坏游戏原生的间接调用链；
> 2. 后续任何热补丁、Hook 跳板或探针拓展代码，**严禁注入 `.detour` 段**；
> 3. 必须严格遵循 `net_sync_fix_spec.md` 规范：通过调用操作系统 API `VirtualAlloc(0x01B00000, 0x1000, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE)` 申请干净的独立内存页作为 Code Cave；若申请失败则执行安全阻断并退出，确保原始 PE 镜像不受不可逆破坏。

---

## 五、 全库回归套件使用与验收

基于上述三项基线定案，S22 交付了完整的工业级回归工具 [`tools/verify_anchors.py`](file:///d:/Project/ra2-campaign-forge/tools/verify_anchors.py) 与全库锚点断言库 [`docs/re/anchor_claims.txt`](file:///d:/Project/ra2-campaign-forge/docs/re/anchor_claims.txt)。

### 1. 运行一键校验
在任意安装了 Python 3 的环境中直接执行：
```bash
python tools/verify_anchors.py
```

### 2. 校验结果范例
```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

该套件的落地为 S21 交叉审计、S23 真机执行剧本以及未来的补丁注入提供了坚不可摧的自动化基准防线。

---

## 六、 唯一事实源与门禁固化（task-11 / `[v1.5.35]` 收尾补录）

### 1. 唯一事实源 = `docs/re/anchor_claims.txt`（**323 条**）

| 项 | 内容 |
|---|---|
| 文件 | `docs/re/anchor_claims.txt` |
| 最终条数 | **323**（`43 + 79 + 77 + 124`） |
| 构成 | `43` 条 S1–S20 全局核心 + `79` 条存档块（源 82 行，去重 3 行）+ `77` 条触发器 + `124` 条 MIX 文件链 |
| 去重规则 | 以 **VA 为主键**；同 VA 且**字节断言串完全相同**者折叠为 1 条（保留首现行）；同 VA 而字节串**不同**者视为**冲突，禁止静默取舍**（当前 0 例）。规则全文已写入该文件头部注释。 |
| 合并复算 | `python out/re_work/errata/audit_claims_merge.py` → 三来源并集**逐字节**被本文件覆盖（缺失 0 / 不一致 0） |

**已撤销的副本口径**：`out/re_work/{save_blocks,triggers,fs_mix}/claims.txt` 自本备忘起降级为**来源留档**，
不再作为断言基准；一切回归、放行与验收均以 `docs/re/anchor_claims.txt` 为准。

### 2. 门禁 G0（写入 `docs/re/execution_runbook.md §2.1.2`）

> **先跑 `python tools/verify_anchors.py`，要求 `323/323 PASS` 且 `.text` 基线（`raw(SizeOfRawData)` 口径）一致，方可进入 Phase 1。**

放行三条件（缺一不可）：

1. `断言总数 = 323` 且 `PASS = 323`（`FAIL = 0`、`NOREAD = 0`）；
2. `.text` 原始段 SHA256 = `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（口径 = `raw(SizeOfRawData = 0x3E0000)`）；
3. **未**命中 `vsize` 口径哈希 `bf9d56ae...`（命中属**度量口径误报**，须修正脚本后重跑，**不得据此判 FAIL**）。

**task-11 实测复算（两条工具链交叉验证，均全绿）**：

```
python tools/verify_anchors.py              -> 断言总数 323 | PASS 323 (100.00%) | FAIL 0 | NOREAD 0
python tools/audit_bytes.py docs/re/anchor_claims.txt -> 合计 323 条：OK=323  MISMATCH/NOREAD=0
```

### 3. 本次收尾一并更正的跨文档口径（详见 `docs/re/savegame_block_manifest.md §8.4-bis / §9-bis`）

| # | 事项 | 结论 |
|---|---|---|
| 1 | 35 个模板函数 MD5 长度口径 | **127 B**（代码长度）→ `9f6770a9cd27…`；**128 B**（含对齐填充）→ `cb13908da7ed66fb…`。两者各自 35/35 唯一，均正确，**引用必须注明长度** |
| 2 | `0xA8ECA4 / 0xA8ECA8 / 0xA8ECB0` | 定谳 = `Items / Capacity / Count`（**RE-A 原表述 `Count = 0xA8ECA4` 已更正**） |
| 3 | 读档侧函数计数 16 vs 15 | **不矛盾**：16 = 不同助手函数地址数（`0x680F70..0x681840`）；15 = 调用点数（目标窗口 `0x680FF0..0x6812E0`）；不含间接/虚表调用，不含 `0x67FDD0/0x67FDE0` 包装 |
