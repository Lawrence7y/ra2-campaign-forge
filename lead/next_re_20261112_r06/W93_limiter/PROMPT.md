# W93 · 提示词（agy / Gemini-4-hydrogen-high）· 限帧通道定谳 + ABBA 可跑脚本

你要执行 RA2 Campaign Forge 项目的**离线卡 W93**。工作目录 `D:\Project\ra2-campaign-forge`。
**只允许写 `lead\next_re_20261112_r06\W93_limiter\` 目录下的文件**；其余路径只读。**禁止启动游戏、禁止注入/调试器、禁止改任何二进制。**

## 背景（已签发，可直接引用；详见 `lead\next_re_20261112_r05\REVIEW\LEAD_VERIFY_W90.md` 与 `lead\next_re_20261112_r03\REVIEW\LEAD_VERIFY_W86.md`）
已确认 cnc-ddraw（`ra2youli\ddraw.dll`，411,648 B，SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`，ImageBase `0x10000000`，`DllCharacteristics=0x0140` ⇒ **DYNAMICBASE 开**）存在一条**非注入**可观测链：

```
maxfps 解析 → [0x100594E8]        （ddraw.ini: 全局 maxfps=-1；[gamemd] 段 maxfps=60 生效）
     ↓
sub_10006880 初始化 → interval(ms) [0x1005F128] = int(1000/fps)，参考上限 [0x1005EE48]
     ↓
每帧门闸 sub_10006AE0：用 timeGetTime 比 [0x1005F120]（上一帧放行时刻），不足则 Sleep 补差
     ↓
[0x1005F120] 每帧写入（3 处写入点，对应三条 renderer 路径）
```

Lead 已独立核过的字节（你可直接复用，但**若你的反汇编与之冲突，必须以你的实测为准并写 DISAGREE**）：
- `0x10006884  a1 e8 94 05 10  mov eax,[0x100594E8]`
- `0x1001E17D  a3 e8 94 05 10  mov [0x100594E8],eax`
- `0x1001B01A  a3 20 f1 05 10  mov [0x1005F120],eax`
- `0x10006D6C  8b 15 20 f1 05 10  mov edx,[0x1005F120]`
- `0x10015E83  c7 05 48 ee 05 10 3c 00 00 00  mov dword ptr [0x1005EE48], 0x3C`（**唯一的立即数写入 = 60**）

## 任务一（**主任务**）：把限帧通道**完整**定谳，并解释 `clamp=210`
真机实测时，W86 的脚本 `exp_rpm_framebeat.py` 校验 `maxfps=60`、`interval=16` 都通过，但打印的 **`clamp=210`**（脚本注释预期 60）。而 Lead 静态只找到"写入 60"这一条路径。请**定谳**：

1. **`exp_rpm_framebeat.py` 到底读的是哪个地址、那句 `clamp` 是怎么算出来的**（读脚本源码，逐行指出）。若它是读了别的偏移/做了别的换算 ⇒ 直接说明「210 是脚本口径问题」，并给出正确读法。**这是最可能的答案，请优先验它。**
2. 若脚本口径没问题，那么 `[0x1005EE48]` 在运行期**确实**是 210 ⇒ 找**非立即数**写入路径：`mov [abs],eax`（`a3` 形态）、`mov [reg+disp]`（reg 指向该地址）、`memcpy`/`RtlZeroMemory` 批量清零后再赋值等。给地址与字节。
3. **把限帧门闸的三条分支走完**：`vsync` 开/关、`maxfps < 参考上限`、`maxfps == -1`、`interval==0` 时分别走哪条路径，**列出每条路径下 `[0x1005F120]`（放行时刻）是否每帧更新**——因为"这个通道能不能当逐帧仪器"完全取决于此。若某些配置下它不更新，必须明说。
4. 给出**一个只读自检脚本** `verify_ddraw_globals.py`：输入 pid，枚举 `ddraw.dll` 基址，dump `RVA 0x5EE30..0x5EE70` 共 16 个 dword，并**断言** `[0x594E8]=60`、`[0x5F128]=16`、`[0x5EE48]=?`（把期望值与容差写清，失败要打印原始字节而不是崩）。这个脚本要能被下一张真机卡直接用。

## 任务二：把 `OBSERVER_ABBA_PROTOCOL.md` 变成**可跑脚本**
`lead\next_re_20261112_r06\OBSERVER_ABBA_PROTOCOL.md` 是我写的协议（尚未执行）。请写两件东西：
1. `abba_driver.py`：给定 `--pid`、`--blocks 3`、`--seg-sec 60`、`--warm-sec 10`，按 **A→B→B→A** 循环切换观测器（A=启动 `exp_rpm_framebeat.py` 子进程并记录 pid、B=不启动），每次切换写一行 `switch_log.ndjson`（`t_perf_ns`、段号、A/B、观测器 pid）。
   - **要求**：只做"启动/停止外部只读进程"，**不注入、不写目标内存**；能优雅退出（Ctrl-C 时写入 finished 标记）；对"段中崩溃"要能记录并停止。
2. `abba_analyze.py`：吃 `switch_log.ndjson` + 被测的那份逐拍 ndjson（含 `t_perf_ns`/`win_cpu_ms`/`elapsed_ingame_s`），按段切分、丢弃每段前 `warm-sec`、算每段 `CPU 消耗率 = Δwin_cpu_ms/墙钟`，做**区组内配对** `d_block = mean(A) − mean(B)`，输出均值/极差 + **三档判决**（预算：`d` 均值 ≤ 0.5 个百分点、且 3 区组方向一致 ⇒ 扰动可接受；> 0.5 ⇒ 不可接受；方向不一致 ⇒ 未分辨）。**禁止**输出 p 值/CI（点数不够，协议已说明）。

## 交付（`lead\next_re_20261112_r06\W93_limiter\`）
- `LIMITER.md`：任务一的完整定谳（含 `clamp=210` 的结论、三条分支表、`[0x1005F120]` 是否逐帧更新的判决）。
- `ABBA.md`：脚本用法、协议与实现的对应、未覆盖项（尤其"无独立画面参照"这一条**不可**掩盖）。
- `verify_ddraw_globals.py`、`abba_driver.py`、`abba_analyze.py`（**都要能在本机 python 3.12 直接跑**，只用 stdlib + 已装库 `pefile`/`capstone`；写清 `--help`）。
- `EVIDENCE\`：反汇编清单（VA/RVA/文件偏移/字节）、脚本自测输出。
- `UNKNOWNS.md` / `DISAGREE.md` / `PROGRESS.md`。

## 纪律
- 只读二进制；先复制到本卡再分析。
- 结论分级 `[本次实测]`/`[静态读码]`/`[静态推断]`/`[未证]`；**"没找到写入者"要写清搜索范围**（扫了哪些节/多少字节/哪些编码/反例校验）。
- **小步落盘**，每完成一节写一次盘（本机 agy 长任务曾多次 `print timeout` 无最终答复）。
- 时间预算 60–90 分钟；做不到就标 `[未证]` 并给下一步最小证据，**不要编**。
