# Lead 独立核查记录（不复用作者自检器）

> run_id `NEXT_RE_20261112_R01`｜核查人：Lead（本会话总控）｜时间：2026-11-12（Asia/Shanghai）
> 原则：以下每条都由 Lead **亲自读码或亲自实算**，不转引执行代理的汇报。等级标注见每行。

## L-1 输入指纹（[本次实测]）

命令：`Get-FileHash -Algorithm SHA256`，2026-11-12 本会话。

| 对象 | 字节数 | SHA-256 | 与任务书 §2.2 比对 |
|---|---|---|---|
| `ra2bench/gamemd.exe` | 4,825,360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | **一致** |
| `ra2youli/gamemd.exe` | 4,825,360 | `73201cc0…67476`（同上） | **一致** |
| `ra2youli/ddraw.dll` | 411,648 | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | **一致** |
| `_run_hl_match.py` | 15,949 | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | **一致** |
| `e3_stack_sampler_candidate.py` | 55,720 | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | **一致** |
| `_hl_match_14412.json` | 987 | `6a44085e5c4f1556aeebb844971ea9ec2a8a0868911cd8c0d3ffceb7c10793d4` | 任务书未登记 |
| `_hl_match_40500.json` | 7,139 | `353e5537aa55f60ab5af854b5e60798896493c5cb65c7c70781beadebc3538b8` | 任务书未登记 |
| `ra2youli/RA2MD.INI` | 1,754 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` | — |
| `ra2youli/RA2MD.INI.benchbak` | 1,754 | 同上（**逐字节相同**） | — |
| `ra2youli/ddraw.ini` | 14,782 | `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52` | — |

⇒ **§2.2 五个哈希在本轮开工时仍然有效**（不是转引，是实算）。
⇒ `RA2MD.INI` 与 `.benchbak` 当前逐字节相同，与 `STALL_CAPTURE_FINAL.md:147` / `STALL_CAPTURE_SUCCESS.md:175` 的「已还原至 benchbak」**自洽**；但两份报告都自认 **不是**会话基线 `2ccf13c2…`，故**「完全还原」不成立**。

## L-2 模块基址归一（[本次实测] 复算 + [静态推断]）

用 `_hl_match_*.json` 里的绝对地址反算运行期基址：

| 栈记录 | 绝对地址 | 减去偏移 | 得出基址 |
|---|---|---|---|
| `gamemd.exe+0x13eb1c` | 5,499,676 | − 0x13EB1C | **0x400000** |
| `gamemd.exe+0x207f17` | 6,323,991 | − 0x207F17 | **0x400000** |
| `gamemd.exe+0x20833f` | 6,325,055 | − 0x20833F | **0x400000** |
| `DDRAW.dll+0x22b06` | 1,417,489,158 | − 0x22B06 | **0x547B0000** |
| `ntdll.dll+0x786ac` / `+0x7858c` | 2,009,171,628 / 2,009,171,340 | — | **0x77BA0000**（同一基址，自洽） |

结论：
1. `gamemd.exe` 两趟（pid 40500、14412）**都加载在 ImageBase 0x400000**，即**未重定位**。⇒ 任务书里 VA=RVA+0x400000 的换算法在这两趟是成立的（**但这是运行期观察，不是对任意趟的保证**）。
2. `ddraw.dll` **运行期基址 0x547B0000 ≠ 首选基址 0x10000000** ⇒ **该 DLL 被重定位**。`STALL_CAPTURE_SUCCESS.md:68-76` 里用的 `0x10022af3…` 是**首选 VA**，不是运行期 VA；对 ddraw 的结论必须落在 **RVA 0x22b06 / 文件偏移**上，不能混用 VA。
3. `ntdll` 两个不同偏移反算出同一基址 ⇒ 该趟模块枚举起止一致，`mod_name()` 映射可信（限该时刻快照）。

## L-3 栈的形态学（[静态推断]，需 RE-N05 字节级确认）

StackWalk64 的帧序是**内→外**，且非栈顶帧的 `AddrPC` 是**返回地址**（即 `call` 的下一条）。据此读栈：

**pid 14412（`_hl_match_14412.json`，7 帧）**
```
#0 ntdll+0x7858c          ← 阻塞在系统调用内
#1 KERNELBASE+0x16a1f0
#2 KERNELBASE+0x16a18f
#3 gamemd.exe+0x207f17    ← 从这里 call 进 KERNELBASE
#4 USER32+0x74775         ← 从这里 call 进 gamemd+0x207f17
#5 USER32+0x3505d         ← 从这里 call 进 USER32+0x74775
#6 gamemd.exe+0x20833f    ← 从这里 call 进 USER32
```
⇒ 结构上是**「游戏代码 → 消息泵 → USER32 派发 → 回调进游戏自身代码 → 再阻塞在内核等待」**的**重入**形态。
即：窗口线程在消息循环里被 USER32 回调进 `gamemd+0x207f17`，并在其中阻塞于 KERNELBASE。
**待 RE-N05 确认**：`0x20833f` 是否为 `DispatchMessage`/`PeekMessage` 类调用点、`0x207f17` 是否为窗口过程（WndProc）入口、KERNELBASE 两帧指向哪个等待 API。

**pid 40500（`_hl_match_40500.json`，3 个事件）**
- 事件 1（t=347.047, frame=11152）：`ntdll+0x786ac` ← `DDRAW+0x22b06` ← `gamemd+0x13eb1c`
- 事件 2（t=351.594, frame=11231）：`win32u+0x11ac` ← `USER32+0xc7f51` ← `DDRAW+0x22b06` ← `gamemd+0x13eb1c`
- 事件 3（t=354.938, **frame=0**）：`ntdll+0x7858c` ← `KERNELBASE ×2` ← `gamemd+0x207f17`

⇒ 事件 1/2 与事件 3 的上游**不同**：前者经 ddraw、后者经 USER32 消息路径。
⇒ 但**帧数不同只说明捕获路径/上游状态不同，不能推出两个独立根因**（任务书 §2.1 缺口二）。

## L-4 对既有报告的三处纠错（[本次读码] + [本次实测]）

**L-4.1 `tid=2540` 不是被证实的「游戏窗口线程」。**
`STALL_CAPTURE_SUCCESS.md:58` 称「`tid=2540` 是**游戏窗口所属线程**（由 `game_window_thread()` 取得）」，
但同一 JSON 的 `picked_by` 字段是 **`"most_gamemd_frames"`**，不是 `"window_thread"`。
`pick_thread()`(`_run_hl_match.py:179-194`) 只有在 `want_tid` **命中**某线程时才返回 `"window_thread"`。
⇒ 该趟 `want_tid` **没有命中**，走的是兜底分支。这与 `STALL_CAPTURE_FINAL.md:21-23` 自述的
`GetWindowThreadProcessId` 返回值读反的 bug（`want_tid` 实际等于 PID）**完全吻合**。
故 40500 趟的线程身份是「含 gamemd 帧的线程」，**不是**已证实的窗口线程；`§7` 与 `§4` 里
「用窗口线程 id 作为主线程代理」的措辞**不成立**，应降为「兜底选中的含 gamemd 帧线程」。

**L-4.2 「t=354.94 游戏此时已退出」与 `frame=0` 自相矛盾。**
`STALL_CAPTURE_SUCCESS.md:32` 写「游戏此时已退出」，但该事件 `frame` 值为 **0** ——
读取**成功**才能得到 0（读失败会是 `None`，见 `_run_hl_match.py:338`）。
⇒ 进程当时**仍可读内存**，`frame=0` 更可能是计数器被清零（新局/加载/退出流程早期）。
「已退出」是**未证推断**，须撤销或降级。

⇒ 连带：该趟「游戏在首次采样后约 8 s 退出」(`:136`) 的因果暗示（「不能排除我的 SuspendThread 加剧了不稳定」）
**仍是一个诚实的假设**，但**其前提（已退出）本身未被证明**。

**L-4.3 「可读 1792/3991 ≈ 45%」的解释不完整。**
`:49-50` 把低可读率归因为「加载期页面未提交 + 游戏退出后读失败」。
但 `_hl_match_14412.json` 的同类在读地址是 **3493/3493 = 100%**。两趟差异如此之大，
仅用「加载期」解释不足；**读失败的时间分布没有保存**（正是缺口三：未存全量序列），
所以**无法**从现有落盘材料区分「加载期」「退出后」「其它读失败」。
⇒ 该 45% 只能作为**待解释缺口**，不能当作已解释事实。

## L-5 `errors: null` 是结构性空洞（[本次读码]，与 RE-N01 问题 B 同源但更弱）

`_run_hl_match.py:358` 读 `one.get("errors")`；而 `e3_stack_sampler_candidate.py` 的
`sample_one_thread()`（`:376-416`）**只返回** `{"tid","prev","ctx","frames"}` 或
`{"tid","skipped","prev"}`，**从不含 `errors` 键**。
⇒ `_hl_match_14412.json` 里的 `"errors": null` **不可能**是别的值，它不承载任何恢复状态信息。
⇒ 该 JSON 的 `errors:null` **不能**用作「线程已正确恢复」的证据（任务书 §2.1 缺口一原文即此）。
另：`_resume_errors`(`:333`) 只在 `sample()`(`:508`,`:574-576`) 内汇总，**单线程路径永不汇总**。

## L-5b 镜像身份与 `.detour` 段：**已登记，我此前的两条表述要更正**（[本次实测] + [转引]）

我一度把「`gamemd.exe` 有非标准 `.detour` 节」当成新发现。**检索既有文档后确认这早已登记**，属于我重复发现：

- `docs/re/baseline_integrity_note.md:118-144`：`.detour` 为**官方 2001 构建自带的 Microsoft Detours 1.x 结构**，
  段首魔数 `40 00 00 00 44 74 72 00`（`'@\0\0\0Dtr\0'` @ VA `0x00B93000`），`vsize=0x2718`、`rawsize=0x3000`，
  并在官方原始备份 `ra2youli/.ra2opt/orig/gamemd.exe` 中**逐字节一致**。
- `docs/re/execution_runbook.md:53-54` 与 `:120`：**「禁止写入 `.detour` 节」已是一条成文红线（G0-5）**。
- `docs/re/REWRITE_ROADMAP.md:163`、`:201` 与 `docs/re/path_cache_oracle_spec.md:201`：
  **现有 `ra2youli/gamemd.exe` 含 `.detour` + 第三方 `xyr.dll`，只能做静态，不可当运行基线**；
  要做「原版对照」须另备干净的零售 1.001。

**我必须更正自己此前两处表述（自我纠错记录）：**

| # | 我此前写的 | 实际（实测/既有登记） |
|---|---|---|
| C-1 | 「`.detour` 是第三方注入的、非标准节，所以镜像被改过」 | `.detour` 是**官方自带**（`[转引]` baseline_integrity_note.md:118-144 + 我在原始备份路径存在的前提下未独立复算）；我这个「新发现」不成立。 |
| C-2 | 「`.detour` 节 characteristics 含 `MEM_EXECUTE`」 | 实测 `Characteristics = 0xC0000040` = `MEM_READ(0x40000000) | MEM_WRITE(0x80000000) | CNT_INITIALIZED_DATA(0x40)` ⇒ **不含 `MEM_EXECUTE(0x20000000)`**，该节**不可执行**。 |

**本轮实测到的、仍可作为事实的部分（[本次实测]）：**
1. `.detour` RVA `0x793000` / VA `0xB93000` / `RawPtr 0x497000` / `RawSize 0x3000` / `VSize 0x2718`；`Characteristics 0xC0000040`（不可执行）。
2. **`.text` 内 rel32 的 `jmp`/`call` 指向 `.detour` = 0 条**（我用 capstone 线性扫描全 `.text` 得到）。
   与既有登记「`.text` 内 rel32 改道 0 条」**一致** ⇒ 该节不是以 inline patch 方式接入的。
3. 全文件存在 **61 处** 4 字节小端值落在 `.detour` 的 VA 区间内（数据/立即数形式的引用）。
4. `gamemd.exe`：`ImageBase=0x400000`、`RELOCS_STRIPPED=True`、`DYNAMIC_BASE=False`、`SizeOfImage=0x796000`。
   ⇒ **该镜像不可能被重定位**，故 `VA = RVA + 0x400000` 对本镜像**恒成立**（这比「两趟观察都在 0x400000」更强）。
5. **文件偏移必须按段映射**：`.text/.rdata/.data` 满足 `file_off = VA − 0x400000`；
   但 **`.rsrc`/`.detour` 为 `file_off = VA − 0x6FC000`**。我在本轮一次快速扫描里**先把 `.detour` 的 RVA 当成了 VA**，
   得到 27 个假阳性，已自行纠正——这正是任务书与 `docs/re/ARCHITECTURE_ATLAS.md:8-13` 反复警告的错误。

**对本轮的约束（要写进 HANDOFF）：**
> 本轮所有静态结论只对 **`ra2bench/gamemd.exe` = `ra2youli/gamemd.exe`（sha `73201cc0…67476`，含 `.detour` +
> `ra2opt apply perf` 的 PE 头栈扩容 + 第三方 `xyr.dll`）** 成立，**不能当零售原版结论**；
> RE-N04 的「原版对照臂」**不满足**，须另备干净 1.001 后才可宣称三臂。

## L-5c 主台账 §610 的实际内容（[本次读码]）

`§610` 位于 `lead/GOAL_THREE_TARGETS_20261018.md:9848`。它**不是**关于帧号计数器的，
而是「11-10/11-11 六探针静态链合流入账」：A 节 18 条字节级读数（`§610-A01…A18`）、
B 节 3 条 CFG（`§610-B01…B03`）、C 节 8 条待证。主题集中在
`0x54A4F0`/`0x54A630` 两个函数、vtable `0x7ECBFC`/`0x7ECBDC` slot2、
全局对象指针 `0xAA1078`、`0x546069` 唯一虚派发点、`PlayerControl`(0x824E28)、`PercentBuilt`(0x8189A0)。
⇒ 任务书 §2「主台账 §610 登记了 18 条字节级读数、3 条静态 CFG 结论及 8 项待证」**与实文相符**。
⇒ **§610 与 `0xA8ED84` 帧号语义无关**，RE-N02 不能拿 §610 当帧号证据；两者是不同对象链。

## L-5d 被测载体（地图）身份：已可绑定到具体文件 + 哈希（[本次实测]）

`STALL_CAPTURE_FINAL.md` / `STALL_CAPTURE_SUCCESS.md` 只说地图是「`[8] Proving Grounds`」，
两份 JSON 的 `target` 分别是 `[265, "[8] Proving Grounds"]`（pid 14412）与 `[268, "[8] Proving Grounds"]`（pid 40500）。
我在 `ra2youli/` 下找到唯一同名候选并实算：

| 项 | 值 |
|---|---|
| 文件 | `ra2youli/[8]试验地_Pro_ProvingGrounds.yrm` |
| 字节数 | 175,361 |
| SHA-256 | `3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19` |
| `[Basic] Name` | **`[8] Proving Grounds`**（与 JSON 的显示名**逐字相同**） |
| `[Basic]` 其它 | `Author=Westwood (original) & RaVaGe (pro edit)`、`MaxPlayer=8`、`MinPlayer=2`、`GameMode=standard, meatgrind, teamgame`、`Official=no`、`EndOfGame=no` |
| 节数 | 41 个（含 `[Header] [Basic] [Houses] [Waypoints] [IsoMapPack5] [OverlayPack] [Triggers] [TeamTypes] [Digest]` 等） |

⇒ **这是一张「Westwood 原作 + RaVaGe 改动」的 8 人遭遇战图，不是 U0400/U0800 LoadBench 载体**——
与 `STALL_CAPTURE_FINAL.md:129-138` 自述「本轮没有用 U0800/U0400 载体，改用 8 人真实多人图」一致，
且现在有了**可复核的文件身份**。

**必须连带的两条边界（否则会被误用）：**
1. **列表索引 265 / 268 不是稳定标识**。同一张图在两趟里索引不同，且 `STALL_CAPTURE_SUCCESS.md:150-156`
   记录过「加/删测试图会改变条目数（280 文件 → 271 条）」。⇒ 只有 **`[Basic] Name` + 文件哈希** 可作载体身份，
   **索引只能当场重取**（任务书 §3 第 3 步「选图索引必须当场重取」正是这个意思）。
2. **显示名相同 ≠ 已证明「当时加载的就是这份字节」**。要升级为已证，需要运行期证据
   （例如进图后读取实际地图/资源句柄或 `[Digest]` 值）——**本轮零真机，标 `[待运行验证]`**。
   现有材料能支持的最强表述是：「该趟显示名为 `[8] Proving Grounds`；仓库内 `ra2youli/` 下
   只有这一个文件的 `[Basic] Name` 与之逐字相同，故**强候选**是该文件（`3e3c8745…`）」。

## L-7 原件 `--selftest` 是 47/0 还是 46/1？—— 取决于**宿主机文件策略**，不是代码（[本次实测]）

**两方读数都是真的，差别在沙箱策略，不在代码。**

| 读数来源 | 宿主机文件策略 | 结果 |
|---|---|---|
| RE-N01 执行代理（本轮较早） | `workspace-write` | **47 项 / 1 失败 / exit=1**；唯一红项 `MF8-d 输出写入独立目录成功`，报 `write_fail:PermissionError` |
| **Lead 本轮亲自复跑** | `danger-full-access` | **47 项 / 0 失败 / exit=0** |

Lead 实跑命令与结尾：
```
python -X utf8 lead\re_d13_ruling_20261112\e3_stack_sampler_candidate.py --selftest
...
结果：47 项检查，0 项失败
EXIT: 0
```
末段可见项：`C5-import …` 4 项、`AUTH-a rc=2`、`AUTH-b rc=4` 全 OK。

**归因（[本次实测] + [本次读码]）**：`MF8-d` 走
`tempfile.mkdtemp(prefix="e3_out_")` → `write_e3_output({"pid":4242,"threads":[]}, out_dir=tmpout)`
（`e3_stack_sampler_candidate.py:975-977`）。在 `workspace-write` 下，DSH 把 `%TEMP%` 映射到
`…\AppData\Local\Temp\dsh-*\`：**允许建目录、拒绝在该目录内新建文件** ⇒ `PermissionError`。
策略切到 `danger-full-access` 后该限制消失，同一行代码通过。

**因此必须这样记录（防止两种误用）：**
1. **不能**把「1 红」写成 `e3_stack_sampler_candidate.py` 的代码缺陷。它测的是**测试夹具自己的输出路径**，
   不是采样器行为，且同一份字节在另一种策略下全绿 ⇒ 归因为**环境 ACL 伪影**。
2. **也不能**把「0 红」写成「候选件已被证明正确」。`MF8-d` 通过只说明**当前策略下**临时目录可写。
   本轮「47 项全绿」的**可复现性依赖宿主机策略**，换策略就会变红 ⇒ 复现命令必须**连同策略一起写**。

**对后续接手的建议**：`TEST_REPORT.md` 要求**并列两个读数**并注明当时的文件策略；
更好的做法是把 `MF8-d` 改成写进**被测工作区内的一个临时子目录**（而不是 `%TEMP%`），
这样断言既保留（「输出写到独立目录」这个性质仍被测到），又不再受宿主机临时目录策略影响。
**这属于测试夹具改良，不是删除检查**，不违反「不许为求绿删检查」。

## L-8 `0xA8ED84` 的写点：10 处，**但没有任何 `inc`**（[本次实测] + [静态推断]）

我用自己的脚本（`REVIEW/_lead_framefield_recheck.py`，与 RE-N02 方法不同）复算，并逐条核对了
RE-N02 的 `EVIDENCE/WRITE_POINTS_DETAIL.md`。**10 个写点确实存在**，全部是 `write_direct` / `dword` / 非 RMW：

| # | VA | 指令 | 类别 |
|---|---|---|---|
| W01 | `0x0052DA08` | `mov dword ptr [0xa8ed84], ebx` | 从寄存器写回 |
| W02 | `0x0055DE81` | `mov dword ptr [0xa8ed84], edx` | 从寄存器写回 |
| W03 | `0x005B7329` | `mov dword ptr [0xa8ed84], 0` | **清零** |
| W04 | `0x005BB20C` | `mov dword ptr [0xa8ed84], ebp` | 从寄存器写回 |
| W05 | `0x005E550F` | `mov dword ptr [0xa8ed84], esi` | 从寄存器写回 |
| W06 | `0x005E747C` | `mov dword ptr [0xa8ed84], 0` | **清零** |
| W07 | `0x0068466B` | `mov dword ptr [0xa8ed84], esi` | 从寄存器写回 |
| W08 | `0x00686765` | `mov dword ptr [0xa8ed84], ebp` | 从寄存器写回 |
| W09 | `0x00795234` | `mov dword ptr [0xa8ed84], 0` | **清零**（前后同时写 `0x841F30..3C = 0x4D2/0x4D3/0x4D4/0x4D5`） |
| W10 | `0x0079758C` | `mov dword ptr [0xa8ed84], eax` | 从寄存器写回（同段亦写 `0x841F30..3C`） |

**由此得到的三条硬事实：**
1. **旧脚本「只有一处写入」的结论不成立**（任务书 §2.1 缺口四的怀疑成立）。实际 **10 处**。
2. **全镜像没有任何 `inc`/`add`/`sub` 直接作用于 `[0xA8ED84]`**（RE-N02 `rmw_write_points: 0`，我独立复算一致）。
   ⇒ 「帧号自增」**并不发生在内存 RMW 上**。因此它只能是下面两者之一，**两者都还没有证据**：
   - (a) 先 `mov reg,[0xA8ED84]` → `inc reg` → `mov [0xA8ED84], reg`（寄存器中转式自增）；
   - (b) 它根本不是计数器，而是**每帧被写入一次的时钟/时间戳**（那样「单调递增 + Δ中位=6」也完全解释得通）。
3. **3 处显式写 0**（W03/W06/W09），与运行记录里观察到的 `frame=0` 事件（`_hl_match_40500.json` 第 3 个事件、
   以及 D-27 里的 `loading_blank_f0` 家族）**方向一致** ⇒ 「读数为 0」更像是**重置/加载态**，而不是「退出」。

**另一条值得单列的实测事实：`0x4068E0` 的磁盘字节是 `C3`（裸 `ret`）。**
W09 与 W10 的「前一条调用」都是 `call 0x4068E0`（RE-N02 记录为 `@0x007951d9`、`@0x00797536`）。
我用 capstone 直接读该地址确认：`0x004068E0  c3  ret`。
⇒ 若运行期它也只是一条 `ret`，那么 `call` 前后 `eax` 不变，`mov [0xA8ED84], eax`(W10) 存的就是调用前的值。

**但我不能由此推出「W10 存的是垃圾」**，理由必须一并记住：
`docs/re/RE_COORDINATION.md:948` 已登记「`0x4068E0=C3`」，且同一处记「`Clock::Now` 经 `[0x87E848]` **间接分发**」。
若 `0x4068E0` 是**热补丁占位**（本镜像自带 Westwood Detours 运行时，见 L-5b），
则**磁盘字节不等于运行期字节**。「`0x4068E0` 运行期做什么」属 `[待运行验证]`。

**因此对后续最重要的一句话（要进 HANDOFF）：**
> 整个停滞检测链的触发量是 `[0xA8ED84]`，而「它是**每帧自增的帧号**」这一点**至今没有证据**：
> 既没有 `inc`，写点也只有 10 处且 3 处是清零。RE-N02 必须给出「谁把它推进」的答案，
> 否则「帧号停推」只能叫「**该 4 字节字段停止变化**」——**不能**命名为帧率、渲染 FPS 或逻辑 tick。

## L-8b 我与 RE-N02 数字不一致的地方（已查明是我的问题）

| 量 | RE-N02 | 我的通道1（线性整段） | 我的通道2（字节模式） |
|---|---|---|---|
| `0xA8ED84` 引用总数 | 1009 | **92** | **1009** |
| `0xA8ED80` 引用总数 | 46 | **2** | **46** |

原因：我的通道1是**从 `.text` 起点一路线性反汇编、无重同步**，遇到 `.text` 内嵌数据（跳转表等）即失步，
之后大面积错位 ⇒ **系统性少计**。RE-N02 报告了 `uncovered_intervals`（`.text` 64 区间 / 66 字节）
并做了**第二可信边界复扫**（`EVIDENCE/RESYNC_VERIFICATION.txt`），所以它的数更可信。
⇒ **结论：不要用「整段线性反汇编不回同步」的计数作为事实。**

两通道**性质上一致**的三条（这才是可用于结论的部分）：
- `0xA8ED80` 只被当 **1 字节** 访问（`mov al, byte ptr [0xa8ed80]` @ `0x432E80`、`0x4333F0`）；
  **从未**被当 dword 读 ⇒ **「32 位 tick」的命名必须停用**，任务书 §3 第 3 条的要求已满足。
- `0xA8ED88`（下一个 dword）**引用 0 处** ⇒ 不存在以 64 位成对使用的证据。
- `0xA8ED7C`（前一个 dword）有 2 处 dword 读（`0x41B201`、`0x44F91D`）⇒ 是**独立**的 32 位字段，不是「64 位计数器低半部」。

## L-9 ⚠ 本轮最重要的质量问题：RE-N01 第一版**驱动候选件是伪交付**（[本次实测]，Lead 独立复现）

前一个 RE-N01 代理（已崩溃退出）留下的 `candidate/_run_hl_match_candidate.py` 在 **docstring 里声称**
已修 A/B/C/C2/D，但**代码几乎等于原件**。我用自己的 diff 复算确认：

```
orig lines=442  cand lines=470
similarity ratio=0.9671
=== opcodes (non-equal blocks) ===
[insert]  orig 13:12 (0 lines) -> cand 13:31 (19 lines)     ← docstring 增 19 行
[replace] orig 14:14 (1 lines) -> cand 33:33 (1 lines)
[insert]  orig 19:18 (0 lines) -> cand 38:38 (1 lines)      ← import
[insert]  orig 21:20 (0 lines) -> cand 41:41 (1 lines)      ← import
[insert]  orig 27:26 (0 lines) -> cand 48:52 (5 lines)
[insert]  orig 29:28 (0 lines) -> cand 55:56 (2 lines)
```
⇒ **非相同块全部落在第 13–56 行（头部）**；**第 57 行之后逐字相同**。

**N7 监测循环原封不动：**
```
378: res = sampler.sample(pid)          ← 仍先采全线程
379: if a.only_tid and want_tid:        ← 之后才判 --only-tid
381: one = sampler.sample_one_thread(want_tid)
```
⇒ **问题 A 在驱动层根本没修**。同一次检索还证明：`run_monitor` 全文件仅出现 1 次（第 20 行 docstring）、
`NDJSON` 仅 2 次（第 27–28 行 docstring）⇒ **流式原始记录（问题 C/P5）、分段（P6）、OnlineAccumulator
全部"声明存在、实现不存在"**。`replay_re_n01.py` 注释所称的「OnlineAccumulator 独立实现」**没有在线对应物**
⇒ 「同一份原始文件可离线重算」这个契约**在线上侧没有对象**。

**同时必须公平记录：`e3_stack_sampler_candidate_r2.py` 那一半是真的。**
我实跑 `--selftest` 得 **58 项 / 0 失败 / exit 0**（当前 `danger-full-access`），且新增项可核对：
`N01-08 六计时字段存在且 end_to_end ≥ 在窗口内分项之和`、`N01-09 E3Fail 被事件吸收不逃逸`、
`N01-10 五取值两两不同且均非 null/空`、`N01-11 不写私有 _target_is32 也能完整单线程采样`。
⇒ 正确分层是：**采样器层有实质改进；驱动层零改进**。

### 这次失效给出的方法论结论（要进 HANDOFF 与契约文档）

> **docstring 声称 ≠ 已实现。** 一份"看起来做完了"的候选件，其文件头可以把 TBD 全写成 TBD-DONE，
> 而任何"只跑作者提供的自检器"的复核都不会发现——因为自检器只跑采样器（58 项），**根本不覆盖驱动层**。
> 这正是任务书要求「独立复核需检查真实调用链与关键判据，不能只复跑作者提供的『全绿』检查器」的原因。

### Lead 因此设定的验收闸（RE-N01 交付必须全部过；不过则不签）

| 闸 | 判据 | 为什么必须是这条 |
|---|---|---|
| **G1 结构闸** | 对驱动候选件做**源码级**断言：`sampler.sample(` 的调用**不得早于** `--only-tid` 判定；`run_monitor`/NDJSON 写入点必须存在 | 只靠行为测试无法排除"docstring 声称"；必须验源码结构 |
| **G2 闸先红后绿** | G1 必须先在**未修版本**上跑出**红**（附原始输出），修好后变绿 | 保证闸本身有区分力，而不是又一个空壳 |
| **G3 声称-测试映射** | 候选件/sampler 的每条能力声称 → 有对应测试 ID → 有当前红/绿状态；**无对应测试 ID 的声称必须删除或降级** | 让"头部声称全做完"在结构上不可能再发生 |
| **G4 离线重算闭环** | 同一 NDJSON 经 `replay_re_n01.py` 重算的摘要与**在线**写出的摘要逐字段一致 | 否则"可重算"无可重算之物 |
| **G5 原件零改动** | 两个原件 SHA-256 收尾实算仍为 `33bb2f61…fa9426` / `98210b4a…51840a` | 防"改原件凑绿" |

**注**：本会话中 `subagent`/`send_message` **无法向已派出的子代理追加指令**（返回
`active teammate ... not found`），故上述 G1–G5 由 Lead 在收件时**自行执行**，不依赖执行方自觉。

## L-10 ★ 我 L-8 的开放问题已闭合：帧号用「读-inc 寄存器-回写」推进（[本次实测]，Lead 逐字节验证）

我在 L-8 里提出两种可能（(a) 寄存器中转式自增 / (b) 其实是时钟）。**RE-N02 的结论是 (a)，我逐字节独立验证成立：**

```
0x0055DE73  8b 15 84 ed a8 00   mov edx, dword ptr [0xa8ed84]   ← 读
0x0055DE79  a1 84 77 b0 00      mov eax, dword ptr [0xb07784]
0x0055DE7E  42                  inc edx                          ← 寄存器自增
0x0055DE7F  3b c7               cmp eax, edi
0x0055DE81  89 15 84 ed a8 00   mov dword ptr [0xa8ed84], edx    ← 回写
0x0055DE87  74 11               je 0x55de9a
0x0055DE89  8b ca               mov ecx, edx
0x0055DE8B  3b c1               cmp eax, ecx
0x0055DE8D  7d 0b               jge 0x55de9a
0x0055DE8F  e8 fc 63 12 00      call 0x684290
0x0055DE94  89 3d 84 77 b0 00   mov dword ptr [0xb07784], edi
```
（my own `capstone` run on `ra2bench\gamemd.exe`, VA→file offset 按 `.text` 段映射）

⇒ **帧号推进就在 `gamemd.exe` 的 `.text` 里**，用的是「读 → `inc edx` → 回写」。
旧脚本按「助记符 + `op_str` 是否以 `dword ptr` 开头」分类，**结构上必然漏掉这一处**
⇒ 任务书 §2.1 缺口四（「只有一处写入、推进机制不在 exe」不能作为前提）**得证**。

**同一邻域还给出「为什么会停推」的候选机制（[本次实测] 字节 + [静态推断] 语义）：**
```
0x0055DE66  84 c0        test al, al
0x0055DE68  75 5e        jne 0x55dec8     ← 门控1 [0x41C0] 非零则跳过推进
0x0055DE6A  a0 48 3d a8 00  mov al, byte ptr [0xa83d48]
0x0055DE6F  84 c0        test al, al
0x0055DE71  75 55        jne 0x55dec8     ← 门控2 [0xA83D48] 非零则跳过推进
```
⇒ **两个门控字节任一非零，帧号当拍就不推进。** 这为「帧号停推」提供了**与卡顿不同的另一种解释**
（不是慢了，而是被门控跳过了）。要判定哪个是本次现象，必须真机读这两个字节 —— `[待运行验证]`。

## L-10b ★ `0xA8ED80` 不只是「1 字节」，它是**布尔标志**，不是 tick（[本次实测]）

RE-N02 报 `0xA8ED80` 46 条引用全 1 字节、含 1 个写点 `0x007778CE`。我独立解码该邻域：

```
0x007778C9  0f 95 c0        setne al                        ← al = (比较结果 ? 1 : 0)
0x007778CC  3a c3           cmp al, bl
0x007778CE  a2 80 ed a8 00  mov byte ptr [0xa8ed80], al      ← 存 0/1
```
⇒ `0xA8ED80` 的写点来自 **`setne al` 的布尔结果**，即它是一个 **0/1 标志字节**。

**因此三条命名必须停用（写进 HANDOFF，防回归）：**
1. ❌ 「`0xA8ED80` = 32 位 tick」→ ✅ 「`0xA8ED80` 处的**字节标志**」
2. ❌ 「`G_TICK`」这个符号名（源码里仍有 `G_TICK`，属历史命名，**不得再作语义依据**）
3. ❌ 「`0xA8ED84` = 渲染 FPS / 逻辑 tick」→ ✅ 目前最强的说法是
   「**每拍在 W02 处被 +1 的一个 32 位计数**，其节拍（每帧/tick/逻辑步）**未定**」

**附注（[本次实测]）**：W02 之后的 `0x0055DE8F call 0x684290`，以及 `0x007778DA call 0x4068e0`
—— `0x4068E0` 又是那个裸 `C3`（见 L-8）。它在多个位置作为「被 call 的占位」出现，
**运行期是否仍为 `ret` 未证**（可能被本镜像自带的 Westwood Detours 运行时hotpatch）。

## L-11 我与 RE-N02 的对账（结论：它的数比我的准，我已采纳）

| 量 | RE-N02 | 我的通道1（线性不回同步） | 我的通道2（字节模式） | 采纳 |
|---|---|---|---|---|
| `0xA8ED84` 引用 | 1009 | 92 | 1009 | **RE-N02** |
| `0xA8ED84` 写点 | 10（全 dword 直接写，均非 RMW） | — | — | **RE-N02**（我逐条核了 W01…W10 的字节，成立） |
| `0xA8ED80` 引用 | 46（全 1 字节，45 读 + 1 写） | 2 | 46 | **RE-N02**（我独立解码了那个写点，见 L-10b） |

**我放弃自己通道1的数字**（整段线性反汇编不回同步会失步，系统性少计）。
RE-N02 报了 `uncovered_intervals`（`.text` 64 区间 / 66 B、`.detour` 6 区间 / 6 B）并做了
第二可信边界复扫（10/10 写点一致），这是更负责的做法。

**但 RE-N02 也必须带着它的限制引用**（它自己已声明，我在此强化）：
`explained 1009/1009` 是**有限静态搜索的解释率**，**不是**「运行期不存在其它写点」的全称证明；
其 `CALLERS.txt` 里 W01/W05/W09/W10 的「可达性未定」与「函数入口是估计值」**不可省略**。

## L-12 ★★ 本轮最大纠错：`ddraw+0x22B06` **不是 Blt**，是 `PeekMessageA` 钩子（[本次实测]，Lead 独立验证四跳）

RE-N05 推翻了两份既有报告的「Blt」定性。**我逐跳独立验证，四条证据全部成立：**

**① `gamemd` 侧调用点（RVA 语义；`gamemd.exe+0x13eb1c` 里的偏移是 RVA，VA = +0x400000）**
```
RVA 0x13EB14  50                  push eax
RVA 0x13EB15  56                  push esi
RVA 0x13EB16  ff 15 84 14 7e 00   call dword ptr [0x7e1484]
RVA 0x13EB1C  8b d8               mov ebx, eax          ← 栈里的返回地址
RVA 0x13EB1E  83 3d 44 04 aa 00 01  cmp dword ptr [0xaa0444], 1
```
⇒ **IAT `0x7E1484` 实解析 = `USER32.dll!PeekMessageA`**（pefile 导入表逐项匹配，非推断）。

**② `ddraw` 侧（cnc-ddraw）调用点**
```
RVA 0x22AF6  ff 75 14            push dword ptr [ebp + 0x14]
RVA 0x22AF9  ff 75 10            push dword ptr [ebp + 0x10]
RVA 0x22AFC  56                  push esi
RVA 0x22AFD  ff 75 08            push dword ptr [ebp + 8]
RVA 0x22B00  ff 15 68 3a 05 10   call dword ptr [0x10053a68]
RVA 0x22B06  8b f0               mov esi, eax          ← 栈里的返回地址
```
⇒ 返回地址**紧跟在 `call [0x10053a68]` 之后**，符合 StackWalk64 返回地址语义。

**③ 槽 `0x10053A68` 的性质**
- 位于 `.data`（RVA 0x53A68），**初值 `0x1002786A`**；
- `0x1002786A` 处指令 = `ff 25 74 e3 03 10` = `jmp dword ptr [0x1003e374]`（转到 IAT）；
- **ddraw 的 IAT 目录只有 RVA `0x3E000`+`0x3F8`** ⇒ `0x53A68` **不在 IAT 内**，**不是 IAT 项**。
⇒ 这是一个 `.data` 里的**函数指针槽**（hook/重定向槽），不是 COM vtable 槽。

**④ 钩子表（决定性证据）**
`.data` RVA 0x53F08 起是一张**逐项 0x34 字节的 hook 描述表**，ASCII 名称依次为：
`DestroyWindow` / `MapWindowPoints` / `ShowWindow` / `GetTopWindow` / `GetForegroundWindow` /
**`PeekMessageA`（RVA 0x5400C）** / **`GetMessageA`（RVA 0x54040）** / `GetWindowPlacement` /
`SetWindowPlacement` / `EnumDisplaySettingsA` / `DefWindowProcA` / `SetParent` …
⇒ **`PeekMessageA` 被 cnc-ddraw 显式列名挂钩**，对应 hook 入口 `0x10022AA0`（我另已确认
`RVA 0x22AA0` 是真实函数序言 `55 8b ec 83 e4 f8 …`，前面是 `CC` 对齐填充，边界可信）。

### 因此必须作废/改写的既有结论

| 既有表述 | 位置 | 处置 |
|---|---|---|
| 「停滞时线程阻塞在 DirectDraw `Blt`」 | `STALL_CAPTURE_SUCCESS.md:54-97`、`STALL_CAPTURE_FINAL.md:104-106` | **作废**。实为 cnc-ddraw 的 `PeekMessageA` 钩子包装内部 |
| 「两次冻结签名不同（`Blt` vs 消息等待）⇒ 至少两条成因路径」 | `STALL_CAPTURE_FINAL.md:104-109` | **作废**。两个签名**同属消息路径**（PeekMessageA 与消息循环/EnumChildWindows） |
| 「5 个参数 + `ret 0x14` ⇒ `Blt`」 | `STALL_CAPTURE_SUCCESS.md:79-90` | **作废**。仅凭形状相似定名，正是任务书 §5 禁止的做法 |

### 本轮由此得到的**新**运行假设（`[静态推断]`，须真机验证）

RE-N05 把四个位置的前一条调用都定位了，合起来是**一条完整的消息/UI 路径**，而不是渲染路径：

| 栈位置 | 前一条调用 | 下游语义 |
|---|---|---|
| `gamemd+0x13EB1C` | `call [IAT 0x7E1484]` | **`USER32!PeekMessageA`**（非阻塞：有消息 TRUE，无消息立即 FALSE） |
| `ddraw+0x22B06` | `call [0x10053A68]` | cnc-ddraw 的 **`PeekMessageA` 钩子**内部 |
| `gamemd+0x207F17` | `push 0x1E` + `call …` | **`KERNEL32!Sleep(30)`**，外层是有界轮询循环 |
| `gamemd+0x20833F` | `call ebx`（ebx=`[0x7E14E4]`） | **`USER32!EnumChildWindows(hWnd, 0x606800, 1)`** |

⇒ 最强的候选机制变成：**`EnumChildWindows` 枚举子窗口 → 回调 `0x606800`（含 `0x607F17`）→ 回调内 `Sleep(30)` 的有界轮询**。
若它跑在推进帧的同一线程上，**每枚举一个子窗口就睡 30 ms**，这可以直接解释成规模的卡顿。
**但我不能把它写成已成立**：① 回调归属、② 是否在帧推进线程、③ 门控条件，全部 `[待运行验证]`。
这条已作为**最优先的下一步单一观测**交给 RE-N06。

### 自我纠错（必须留痕）

我此前在 `L-3` 里把这些栈读成「游戏代码 → 消息泵 → USER32 派发 → 回调进游戏自身代码」，
方向大体对，但**具体函数名与「Blt」的对比结论是错的**。
另外我上一轮一次快速脚本把 `gamemd.exe+0x13EB1C` 的偏移**当成 VA** 去算文件偏移，
得到负偏移后 Python 回绕到文件尾部附近，**读出了"看起来合理"的字节**（`8b d8 …` 恰巧也是对的，
因为 `.text` 的 `PointerToRawData == VirtualAddress == 0x1000`，`file_off == RVA` 时两种算法碰巧同值）。
**教训**：`gamemd.exe+0xNNNNNN` 里的偏移是 **RVA**；本镜像 `.text` 内 `file_off == RVA`，
但 `.rsrc`/`.detour` 不成立（见 L-5b C-2 与 `docs/re/ARCHITECTURE_ATLAS.md:8-13`）。

## L-13 ★★ 计时器实测：`time.monotonic()` 在本机只有 ~15 ms 粒度（[本次实测]，Lead 亲跑）

```
QueryPerformanceFrequency = 10,000,000 Hz  => 100.0 ns/tick
perf_counter_ns 最小非零增量 = 100 ns
time.monotonic() 前几个不同取值: 69213.156, 69213.171, 69213.187
相邻差: 0.015, 0.016  => 量化步长 ≈ 15.0–15.6 ms（GetTickCount64 系 64 Hz）
```

**原驱动 `_run_hl_match.py` 的全部计时都用 `time.monotonic()`**（`:342` `t0`、`:345` `now`、`:347` 采样时间戳、
`:353-354`/`:357`/`:390` 的 `cost` 与 `paused_ms`）。

⇒ **追溯到既有报告的四条后果**（这不是「精度不够」，是**读数被量化**）：

| 既有读数 | 原表述 | 实测约束下的准确表述 |
|---|---|---|
| `STALL_CAPTURE_FINAL.md:43` `#0 cost= 16.00 ms` | 「16 ms」 | **恰好一个量化步长** ⇒ 真值是 **15–30 ms 之间的某个值**，`16.00` 是量化值不是测量值 |
| 同处 `#1..#5 cost= 0.00 ms` | 「0 ms / 零开销」 | 真值 **< 15 ms**，**不是零** |
| `_hl_match_14412.json:16` `paused_ms: 0.0` | 「远低于 50 ms 预算」 | 只支持「**< 15 ms**」，仍是上界未知的量 |
| `STALL_CAPTURE_FINAL.md:66` `Δ中位=6 ⇒ 30.0 fps` | 「30 fps」 | 分母用的是**名义 0.2 s**，而循环实际间隔含 15 ms 量化的 `sleep` + 工作耗时 ⇒ 该 fps **不可作帧率引用** |

⇒ **`SAMPLER_CONTRACT.md` 的 `paused_ms=0.0 是低于测量精度、不是零开销` 这句话，
现在有了硬件级依据（15.0 ms 量化步长），不再只是保守措辞。**

**同时确认 r2 候选件改用 `perf_counter_ns()` 是必要且正确的**（100 ns 分辨率，比 monotonic 好 5 个数量级）；
`TIMER_CALIBRATION.md` 要求并列两个读数并注明「可复现性依赖宿主策略」的做法**采纳**。

## L-6 待与执行代理结果对账的开放问题

1. `0xA8ED84` 的写点是否**真的只有一处**？旧脚本的边界启发式 + `dword ptr` 文本判据（任务书 §2.1 缺口四）是否确实导致漏检？→ RE-N02。
2. `0xA8ED80` 的**字段宽度**（不得先假定 32 位 tick）→ RE-N02。
3. `0x13EB1C` / `0x207F17` / `0x20833F` 各自前面的 `call` 目标与调用约定；`DDRAW+0x22B06` 是否**只能**靠 `ret 0x14`+5 参数 推为 `Blt` → RE-N05。
4. 单线程模式真的能压进预算吗？`paused_ms=0.0` 是不是**低于计时精度**而非零开销 → RE-N01。
