# W171 · PROGRESS

> 时间均为本机（Asia/Shanghai）。累计约 1 h 40 min。

| 时间 | 做了什么 | 结论 / 下一步 |
|---|---|---|
| 21:42 | 按序读 `R13_COMMON.md`（含"作废索引"）→ `R11_COMMON.md` → `R12_FACTS.md`（974 行，含 §25 作废 §23/§24）→ W164 `LOCOMOTION_COST.md` 方法段 + W161 `BULLET_COST_ATTRIB.md` 方法段 | 入场。记住三条作废项：§23/§24 的 mode3 叙事；`0x43F658 cmp ebp,3` 不是 mode 门；`0x55B8F0` 边界争议 |
| 21:44 | 建 `w171_lib.py`：pefile 读 + capstone `skipdata=True` + **CFG 递归下降**（`body()`）+ **边删除可达性**（`reach()`）+ 跳表解析 | 三条通道：`lin` / `cfg` / `atlas`。`skipdata=True` 实测全 `.text` 解出 **1,394,120** 条（与本轮纪律值一致） |
| 21:46 | `s1_drive_dump.py`：确认 `[0x7E7EB0+0x40]=0x4B0500`；零 rel-call、`.rdata` 唯一 dword `0x7E7EF0`；全文 dump | `0x4B0500` = 485 指令 / 1486 B / 10 直接 callee / 28 虚调用站 |
| 21:49 | `s2_pathchain.py`：链上 6 函数计数 + `0x4D3920` 的 32 个虚调用站 + A\* 回边 | 发现 **`0x42C900` 只有 327 指令**（W164 写 1563）→ 记 DISAGREE |
| 21:52 | `s3_gates.py`：边删除可达性门控分析 | 发现**门 A/B 不跳过 Process**（跳 `0x4B066C` 后仍调 `0x4B0A79`） |
| 21:54 | `s3b_pathAB.py`：把 A/B 两路指令集分开 | A 路 403 条（只到 `0x4B0A79`）、B 路 216 条（只到 `0x4B0647`）；`0x4D3987` 是唯一能绕过 FindPath 的门 |
| 21:57 | `s4_process_gates.py`：`0x4B2630` 头部与 3 个 UpdatePathfinding 站点的门控 | 站点 `0x4B28A3`/`0x4B3A0E`/`0x4B3F37`；跳过目标是 `0x4B3A4D` |
| 22:00 | `s5_searchcore.py`：`0x429A90` 的调用者穷举（字节扫 + dword 扫） | **全镜像只有 1 个调用者 `0x42CC02`**；回边 7 个，外层轮体 **544**；`0xFFF7` 字节 `c7442470f7ff0000` |
| 22:03 | `s6_budget.py`：`[esp+0x70]` 预算槽溯源 | **`0xFFF7` 是缺省**（只在 `<0` 时写入）；预算来自参数，静态不可定值 → 记 `[未证]` |
| 22:06 | `s7_args_closure.py`：A\* 全局操作数 + 深度≤3 闭包 + 成员测试 | 发现 **`0x42A3E2 cmp ecx,0x2710`**（10000 硬闸）；闭包 149 函数 / 20,514 指令；**格链原语不在深度≤3** |
| 22:10 | grep 主台账 | **`0x2710`=10000 已在台账 §566(a)**（W3 首报）⇒ 本卡只作**独立复核**，不称新发现 |
| 22:12 | `s8_callees_depth.py`：callee 身份 + 深度 8 探针 | 格链原语（`0x47E8A0`/`0x47EA90`/`0x5683C0`/`0x5687F0`/`0x47C620`）**深度 ≤8 全不可达** ⇒ ③ 必走虚槽 73 |
| 22:16 | `s9_field_writers.py`：`+0x54/+0x5E/+0x5F/+0x5A0/+0x5A4/+0x5E0` 写者普查 | `+0x54` 写 688 处（含栈污染），改用"槽 73 + 虚调用"路线取证 |
| 22:20 | `s10_slot73.py`：槽 73 解析 + 链原语成对确认 | `[Unit vt+0x124]=0x4D3780`；`0x5683C0→0x47E8A0`@`0x5684BB`、`0x5687F0→0x47EA90`@`0x5688EB` |
| 22:24 | `s11_multiplicity.py`：多实例性 | UpdatePathfinding 每 Process **最多 2 次**；wrapper 有回边 `0x4B0ABC→0x4B078C` ⇒ Process 可多次 |
| 22:28 | `s12_timebudget.py`：Q2 全部表格 | 544 指令/轮；0.284 ms ≈ 783 轮；4.54 ms ≈ 12,518 轮（3 GHz/CPI2） |
| 22:32 | `s13_globals_dual.py`：三通道对账 | **18 个函数三通道逐值相同**；同时坐实 W164 的 1563 是错的 |
| 22:36 | `s14_throttle_scope.py`：节流作用域 | **推翻前提**：`frame % N` 只跳 60 条；`call [ecx+0x40]`（loco Process）在 `0x4DA877` 不受节流 |
| 22:40 | `s15_throttle_proof.py`：逐条打 60 条 + 80x 上下文 | 60 条 = 取 cell + `fild/fmul` + `call 0x7C5F00` + `call [vptr+0x16C]` ⇒ **概率触发的应答/声音块** |
| 22:44 | `s16_frame_gates.py`：`frame % 10` 作用域 + `0x421EA0` 探针 | `frame%10` 只跳 **35 条**（`malloc(0x1C8)` + `call 0x421EA0`） |
| 22:47 | `s17_div_modulo.py`：全链 div/idiv 普查 | A\* **0 处**用 frame；`0x4B2630` 的 4 处除的是 `[0x8A07D0]`（非 frame） |
| 22:50 | `s18_loco_dispatch_gates.py`：`0x4DA877` 的支配门 | 只有 5 个门（活跃性/状态），**都不是 frame-modulo** |
| 22:52 | 核实槽 73 两站的 mode 实参 | `0x4D3E0D push 0`（mode 0＝Limbo/摘链）+ `0x4D3EA8 push 1`（mode 1＝Unlimbo/挂链）⇒ 寻路前**先摘后挂**，与台账 §914 一致 |
| 22:54 | `s19_final_audit.py`：**不用本卡 lib** 的独立复核（原始字节 + capstone） | 首跑自曝两个 bug：①把 `call` 目标也当流内分支 ⇒ 计数虚增（4701/706/2654）；②从 `0x4DA569`（非边界）线性走 ⇒ 60 读成 63。修正后三通道全对（485/2600/669/58/327/812/722，块=60） |
| 22:58 | 写 `COST_BREAKDOWN.md` / `PROGRESS.md` / `UNKNOWNS.md` / `DISAGREE.md` | 交付 |

## 中途废弃的路线（负结果，照写）

1. **想用 `[loco+0x54]` 的写者普查直接定语义** ⇒ 失败：`[reg+0x54]` 全 `.text` 有 688 处写，`[esp+0x54]` 严重污染，
   按"基址寄存器"过滤无法可靠区分 loco 与其他类。改用**虚槽 + 上下文**取证。
2. **想静态定出 A\* 轮数预算的实际值** ⇒ 失败：`[esp+0x70]` 是第 5 个栈参，
   经 `UpdatePathfinding → CallFindPath → FindPath → 0x429A90` 三层转发，
   且 `CallFindPath` 的 `push 0x7D0`（2000）**在该函数体内根本没被读取**（`S6(8)` 全文可验）。
   ⇒ 记 `[未证]`，转真机方案。
3. **想用纯调用图闭包统计"格更新"成本** ⇒ 失败：槽 73 是虚调用，静态图看不见；
   靠 `S8` 的"深度 ≤8 不可达"负结果反而**定住了**必须补虚槽这条纪律。
