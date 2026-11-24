# R10 事实底座（每张 R10 卡开工前必读）

> 编制：Lead｜2026-11-14 20:5x｜轮次 R10
> 本轮用户令：① 授权使用新装工具（Ghidra / PresentMon / DIE / x32dbg）对 RA2 逆向；② 子代理与 harness 全部授权；③ **立即取消 Hy4 使用权，直到今晚 24:00**。
> 前置事实底座仍有效：`lead\next_re_20261112_r09\R09_COMMON.md`（路径/哈希/硬禁令/崩溃签名/表达纪律）。**必读**。
> 本轮新增事实：`lead\next_re_20261112_r09\LEAD_FINDINGS_R09.md` 的 **L1 / L2 / L4 / L6 / L7 / L8**。

---

## 0 · 路由禁令（本轮硬约束）

- **禁止使用 `work/cn:hy4free`**（用户 2026-11-14 20:45 令，直到当日 24:00）。
- 可用：`magpie-anthropic/zcode/GLM-5.3-Flash`、`magpie-anthropic/work/cn:deepseek-v4.1-flash`。
- 该禁令由 Lead 执行；你（子卡）若需要外部模型，只能用上面两个。

## 1 · 授权变更（本轮生效，与 R09 底座的红线有差别）

**已授权**：
1. 使用 Ghidra / DIE / PresentMon / x32dbg **对本项目二进制做逆向**；
2. 只读附加调试器、抓崩溃现场、生成与分析 **minidump**；
3. 安装的工具在 `D:\Tools`、`C:\Program Files (x86)\Resource Hacker`、WinGet Packages 下。

**仍然禁止（未授权，违反即整卡作废）**：
1. **写** `ra2youli\gamemd.exe` / `ddraw.dll` / `ra2youli\` 下任何文件；
2. **写目标进程内存**（`PROCESS_VM_WRITE` / `WriteProcessMemory`）；
3. **改 `.detour` 段**（VA `0xB93000`，Westwood 原生 Detours，非可执行）；
4. **改主台账** `lead\GOAL_THREE_TARGETS_20261018.md`（append-only）；
5. **taskkill 非本卡进程**；
6. **软件断点（`int3` 补丁 = 写内存）** —— 用户授权的是"放开调试器附加"，**未明说允许软件断点**；首次使用前须回报 Lead 再确认。
7. **启动游戏**（除 Lead 亲执的真机卡外，任何子卡不得启动 `gamemd.exe`）。

---

## 2 · Ghidra 使用要点（本轮所有卡共用）

- 安装：`D:\ghidra\ghidra_12.1.4_PUBLIC`；`support\launch.properties` 已指向 `D:\jdk21\jdk-21.0.12.1+1`（**不要改 PATH**）。
- Lead 已建好一份全量分析库：`D:\Project\ra2-campaign-forge\_ghidra_proj`（`.gpr` = `gamemd_auto.gpr`，`.rep` 137.6 MB，**8,948 个函数**，分析耗时 3.4 min）。

### ⚠ 工程锁：**不要**共用 Lead 的库

Ghidra 工程打开时会**加锁**，多个 headless 进程同时用同一个 `.gpr` 会失败。

⇒ **你的做法**：在你自己的卡目录下建**你自己的**工程并重新导入分析（只要 3.4 分钟）：

```powershell
$g  = 'D:\ghidra\ghidra_12.1.4_PUBLIC'
$my = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\<你的卡号>\_ghidra'
$sp = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\<你的卡号>\ghidra_scripts'
New-Item -ItemType Directory -Force -Path $my,$sp | Out-Null
# 1) 导入 + 全量分析（约 3.4 分钟）
& "$g\support\analyzeHeadless.bat" $my ghidra_$env:COMPUTERNAME -import 'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
# 2) 之后反复用 -process 跑你的脚本（秒级）
& "$g\support\analyzeHeadless.bat" $my ghidra_$env:COMPUTERNAME -process gamemd.exe -noanalysis -scriptPath $sp -postScript YourScript.java
```

- 脚本用 **Java**（`extends GhidraScript`，类名 = 文件名，放在 `-scriptPath` 目录）。Ghidra 12 默认不带 Jython，**别写 .py 脚本**。
- Java 编译错误会让整个 postScript 失败，日志关键字：`REPORT SCRIPT ERROR` / `error: no suitable method`。**改完必须重跑并确认无此报错。**
- 已验证可用的 API：`DecompInterface.decompileFunction(f, timeoutSec, monitor)`、`getFunctionContaining(addr)`、`getFunctionBefore(addr)`（**没有** `(addr, boolean)` 这个重载）、`currentProgram.getFunctionManager().getFunctionCount()`。

### 已知可用结果（省你时间，但请自己复核）
- `0x0047C520` → `FUN_0047c520`，47 B，语义 = 在 `cell+0xE4` 链里找 `WhatAmI()==6` 的第一个对象
- `0x0047C4D0` → `FUN_0047c4d0`，73 B，语义 = 在 `cell+0xE4`/`+0xE8`（按参数选）链里找 `WhatAmI()==wanted`
- `0x0047EA90` → `FUN_0047ea90`，263 B，语义 = 从链里摘除指定对象（链头/链中都处理），摘后 `next` 置 0
- 链 next 偏移 = `+0x30`（伪码里显示为 `param_2[0xc]`）
- `DAT_00a8e9a0` = 崩溃族三处函数入口的共同 bool 守卫

---

## 3 · 已证的关键结构（**引用前请复核**）

| 事实 | 值 | 来源 |
|---|---|---|
| `CellClass` 访问 | 两级：`table = *(DWORD**)0x0087F924`；`obj = table[Y*512 + X]`；表项**可为 NULL** | L8 |
| 静态 cell 槽 | `0x0089C2E0`（无效格 fallback）；另一锚点 `0x00ABDC50` | L8 |
| `CellClass` stride | `0x148`（`0x005663C3: push 0x148`；`0x00566AA6: add ebp,0x148`） | L8-4 |
| 链头 | `+0xE4`（链 A）/ `+0xE8`（链 B） | L1 |
| 节点 next | `+0x30` | L1 |
| `WhatAmI()` 槽 | `+0x2C` | L1 |
| 格坐标字段 | `+0x24`（行）/ `+0x26`（列），世界坐标 = `v*256+128` | L1（Ghidra 反编译得出） |
| 已知类 ID 锚 | vtable `0x007EB058` 的 `WhatAmI()` = **15**；vtable `0x007E3EBC` 的 = **6** | L2 |
| `A8ED50` | Bullet 向量 Count，**不是**开火/接触代理 | R09 底座 + §635-4 |

## 4 · 表达纪律（不变）

1. 每条结论标 `[已证]` / `[静态推断]` / `[未证]`。
2. **每个数字/地址必须附产出它的命令**（可粘贴运行）。
3. 引用别处数字必须回到原始文件核，写 `file:line`。
4. 负结果也是交付；查不到就写"查不到 + 试过哪些途径"，**不许编**。
5. 与预期不符写进 `DISAGREE.md`。
6. 禁止 p 值 / 置信区间 / "显著"。

## 5 · 交付物结构（每卡相同）

```
lead\next_re_20261112_r10\<卡号>\
  PROGRESS.md      # 每步一行
  <主报告>.md      # 先写这个，别留到最后
  UNKNOWNS.md      # ≤20 行
  DISAGREE.md
  ghidra_scripts\  # 你的 .java
  EVIDENCE\        # 全部原始 stdout
```

**硬规矩（R09 教训）：一卡一问；交付物 ≤ 1 报告 + 1 脚本；主报告在证据齐后立刻写（200 行内可交付版），再补材料；给硬时限。**
