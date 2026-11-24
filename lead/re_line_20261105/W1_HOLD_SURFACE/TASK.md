# W1 任务书 · 挂起计数器 `Scenario+0x62C` 的**来源完备性普查**

> 你（子代理）是 RA2/YR 引擎逆向分析员。本轮任务是**纯离线静态分析**，
> 目标是回答一个具体问题，并交出可复算的清单。**不启动游戏、不写采样代码、不改母本。**

## 0. 先读这些（不要跳）

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | `D:\Project\ra2-campaign-forge\lead\re_line_20261105\_leader\LEADER_PRECHECK_20261105.md` | **领队已钉死的事实**，别重做 |
| 2 | `D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\P01\REPORT.md` | 挂起计数器全解（含写点/调用点全集） |
| 3 | `D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\P01\VERIFY.md` | 独立复核，含 18 处 disp 命中表 |
| 4 | `D:\Project\ra2-campaign-forge\docs\re\trigger_system_manifest.md` | 动作派发跳表（145 项，§2） |
| 5 | `D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\Q02\REPORT.md` | 「冻结 vs 慢爬」调和，含对 Q04 采样方案的警告 |

## 1. 已定谳的前提（**直接采用，不要重新证明，也不要推翻**）

1. `[0xA8B230]` = `ScenarioClass::Instance`；`+0x62C` = 挂起深度计数器（dword）。
2. 写点**恰 3 处**：`0x6836D2`（复位 0）、`0x684174`（`inc`）、`0x684195`（`dec` 后写回）。
3. 「挂起请求」入口函数 `0x684060`（参数 `ecx` = 时长秒，0 = 无自动释放），**call 点恰 4 处**：
   `0x53B612`（渐变机 state2→3）、`0x657CA0`、`0x6DF703`、`0x6E4086`。
4. 「释放」入口函数 `0x684180`，**call 点恰 3 处**：`0x55D81C`（MLF PauseTimer 到期）、
   `0x53B6E6`（渐变机 state3 收尾）、`0x657CC8`。
5. 渐变启动器 `0x53B460`，**call 点恰 2 处**：`0x6DFAC5`、`0x6E2F96`。
6. **领队本轮新查（采信即可）**：
   - `0x6DF703` 落在动作 **110 PauseGame** 派发块（`0x6DF6FD..0x6DF717`）；
   - `0x6DFAC5` 落在动作 **127 StartChronoScreenEffect** 派发块（`0x6DFABF..0x6DFAD9`）；
   - `0x657CA0` 所在函数头 = `0x6579E0`，全镜像**唯一调用者 `0x653446`**，
     由一个全局计数 `0xB45B68` 的沿翻转驱动（23 处引用）。
7. 引擎读取器：`D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\ra2tool.py`
   的 `Engine` 类（只读 `ra2youli\gamemd.exe`，内部断言 SHA256 = `73201cc0…f67476`）。
   `import sys; sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104'); from ra2tool import Engine`
   **必须用重同步线性解码**（`Engine.stream` 已实现），不得用裸 `disasm(blob, va)` 做普查。

## 2. 你要回答的三个问题（**这是本轮的交付**）

### Q1 · `0xB45B68` 是什么？（**最高优先**）

P01 只说「一个布尔沿触发对象」。你要定到**类与字段级**：

- `0xB45B68` 是全局变量（静态初值 0）。23 处引用里，写点 3 个
  （`0x5BF341` / `0x5BF43B` / `0x5BF487`），都在 `0x5BF3xx` 一带——**找出这一带的函数边界与身份**。
- 它被 `0x48D091` 读（`MainLogicFrame` 块内！`0x48D080` 是被冻结体也调用的那个函数）——
  **这条特别重要**：说明它与主循环直接相关。给出该处前后 20 条指令的完整反汇编与语义判断。
- 结论要写成：`0xB45B68` 的语义（是什么计数器/旗标）、谁在什么条件下改它、
  **在没有任何地图脚本动作的情况下它会不会非 0**。

### Q2 · `0x6579E0` 这个函数在做什么？

- 它读 `0xB45B68`（`setg bl`）与 `[esi+0x14bd]`，在沿翻正时 `call 0x684060`（挂起，时长 0），
  沿翻回时 `call 0x684180`（释放）。字段族 `+0x14b8 / +0x14bc / +0x14bd / +0x14d4 / +0x14d9` 都在它附近。
- 唯一调用者是 `0x653446`——**追上去**：它在哪个函数、由谁调用、属于哪个子系统
  （提示：`0x752370 / 0x752480 / 0x753570 / 0x7529E0 / 0x70F120 / 0x6F1F70` 是它调用的库函数，
  判断它们属于渲染/音频/输入/网络哪一层）。
- 结论要写成：**这个对象是不是"玩家可见的过场/影片/简报接管"**？还是别的东西？给证据。
  （如果它确实是「播放影片/过场时挂起世界」，那它就和动作 10 PlayMovie / 117 PlayIngameMovieAndPause 同族，
   请明确指出。）

### Q3 · 还有没有第五个来源？（完备性）

在 Q1/Q2 基础上回答：**在单机局（GameMode∈{0,5}）里，让 `[Scenario+0x62C]` 变非 0 的全部可能来源**，
逐条列出并标注「脚本可达 / 引擎内部不可控」。

必须覆盖的候选：
- 动作 110 PauseGame、127 StartChronoScreenEffect（已定）；
- 动作 10 PlayMovie / 117 PlayIngameMovieAndPause 是否**间接**进 `0x684060`（追它们的从属体）；
- 引擎的 `0x684240`（无计数器版挂起态置位，7 个 call 点）与 `0x684290`（清除，4 个 call 点）
  ——它们**不加计数**但会置 `[Scenario+0x35A2]`/`[0xA8ED9C]`，请判断它们对 `0x55D877` 冻结出口**有没有间接影响**
  （提示：`0x55D877` 的门只看 `+0x62C`，但 `0x48CE67/0x48CE73` 会把 `+0x35A2` 抄进 `[0xA8ED9C]`，
   而 `0x55D377` 的等待环读 `[0xA8ED80]`——请在报告里把这几条链**分开写清**，不要混为一谈）。

### Q3b · 地图面普查（可机械完成，**必须做全**）

对 `D:\Project\ra2-campaign-forge\ra2youli\` 下全部 `.yrm/.map/.MAP`（含 `*.mmx` 若有），
解析每张图的 `[Actions]` 段，统计出现的动作 kind 直方图，
并明确指出：**哪些图含 110 或 127**。

领队已抽查 8 张（`U0050/U0100/U0200/U0400/U0800` + `ECH01/02/03`），结果是
`U0400={2,4,9}`、`U0100/U0800` 无 `[Actions]`、ECH 只有 1/2/9。
**你要做全量，并把结果与领队的抽查对齐**（不一致要指出来）。

另外：测量趟用到的图不止 `ra2youli\` 下这些——`l1*` 趟的 map_sha 前缀是 `0add791d`、
`l3*` 是 `f3bb0a4e`、archive 各不相同。请顺带说明**这些 sha 对应哪个物理文件**
（可查 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/MANIFEST.json` 或 `_src_*` 目录）。
**如果找不到对应文件，就明确写「找不到」，不要猜。**

## 3. 交付物

写到：`D:\Project\ra2-campaign-forge\lead\re_line_20261105\W1_HOLD_SURFACE\`
文件名：`W1_HOLD_SURFACE.md`（正文）+ 你写的探针脚本 `_w1_probe.py`（可复算）
+ 原始输出 `_w1_probe_out.txt`。

正文结构：
1. **一句话结论**（挂起计数器的来源是否已闭合）
2. Q1 `0xB45B68` 定谳（含反汇编片段与 VA）
3. Q2 `0x6579E0` 子系统归属（含调用链）
4. Q3 来源完备清单（表：来源 / 触发条件 / 脚本可达? / 证据）
5. Q3b 地图全量普查表（每图一行：文件名 / n_actions / kind 直方图 / 含110? / 含127?）
6. **诚实账**（你亲验了什么、采信了什么、没查什么）

## 4. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存，
  不写任何采样代码（不写 hook、不写 MiniDump、不写 SuspendThread/StackWalk）。
- **只读**：`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/PENDING_DECISIONS.md`、
  `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`、`ra2youli\` 全部文件、
  `lead/goal3t_nightwatch_20261102\swarm_20261104\` 下任何文件 —— **一律不得修改**。
  你的**唯一写域**是本任务 §3 指定的三个文件。
- Python 一律 `python -I -X utf8`，路径一律绝对路径。
- **不 commit、不 push**。
- 引用的每个数字都要能追到「我实跑的命令 + 输出」或「某文件某行」。
  **拿不到证据就写「未验」，不要补造。**
- 如果你发现领队 §1 的前提有错，**明确写出来并给出反证**，不要默默绕过。
