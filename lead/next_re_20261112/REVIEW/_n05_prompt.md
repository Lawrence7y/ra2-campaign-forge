你是 RA2 Campaign Forge 逆向项目的执行代理。任务卡：**RE-N05「沿已有栈做等待链静态逆向」**（依据 `docs/re/NEXT_RE_TASKS_20261112.md` 第 5 步）。

## 环境
- Windows，仓库根 `D:\Project\ra2-campaign-forge`（git 分支 main，HEAD `3872ef6`）。
- 本轮 run_id = `NEXT_RE_20261112_R01`。
- Python 3.12.10、capstone 5.0.7、pefile 均已安装可用。
- 你的**写域只有** `D:\Project\ra2-campaign-forge\lead\next_re_20261112\RE-N05\`。其它目录一律**只读**（尤其 `lead/re_d13_ruling_20261112/`）。

## 授权边界（铁律，违反即任务失败）
1. **纯静态**：只读磁盘上的 PE 字节。**严禁**启动游戏（gamemd.exe / ra2loader / YURI.exe）、attach 活进程、ReadProcessMemory 活游戏进程、SuspendThread / ResumeThread / StackWalk64 / MiniDump / 断点 / 注入 / 部署 / taskkill。
2. **不执行任何 git 写操作**（不 commit / checkout / reset / clean / add / stash）。仓库里有他人未提交的工作，禁止清理或覆盖。
3. 只写自己的输出目录 `lead\next_re_20261112\RE-N05\`。

## 输入（全部只读）
- 主镜像：`ra2bench\gamemd.exe`（开工前**实算** SHA-256 与字节数并写在报告首段；若与 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` 不一致，立即停止并报告）。
- 加载 DLL：`ra2youli\ddraw.dll`（cnc-ddraw，开工前实算 SHA-256；任务书登记期望值 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`）。
- 栈证据 JSON：`lead\re_d13_ruling_20261112\_hl_match_40412.json` 请忽略，实际读这两个：
  - `lead\re_d13_ruling_20261112\_hl_match_14412.json`（pid 14412，1 个事件，单线程采样，tid=30668，7 帧）
  - `lead\re_d13_ruling_20261112\_hl_match_40500.json`（pid 40500，3 个事件，全线程采样 27 线程，选中 tid=2540；含 `DDRAW.dll+0x22b06` 与 `gamemd.exe+0x13eb1c`）
- 相关报告（只读参考，不得直接采信）：`STALL_CAPTURE_FINAL.md`、`STALL_CAPTURE_SUCCESS.md`、`STALLWALK_RECEIPT.md`（实际文件名 `STACKWALK_RECEIPT.md`）、`WOW64_RECEIPT.md`、`STATIC_FRAME_SEMANTICS.md`。

## 四个待回溯位置
| 栈记录 | 按 ImageBase 0x400000 换算的 VA | 需要回答的核心问题 |
|---|---|---|
| `gamemd.exe+0x13EB1C` | `0x53EB1C` | 前一条调用是什么？谁进入呈现/消息路径？ |
| `gamemd.exe+0x207F17` | `0x607F17` | 调用的是哪类 wait/dialog/message API？正常返回条件？ |
| `gamemd.exe+0x20833F` | `0x60833F` | 其调用上下文对应战斗、对话框还是退出？ |
| `ddraw.dll+0x22B06` | RVA `0x22B06`（**注意：dll 基址 ≠ 0x400000，必须用该趟实际基址换算**） | 返回地址前的间接调用实际目标、接口槽、隐藏 this、包装/真实现的边界 |

## 第一步必须先做：地址归一（这是本卡区分力的基础）
1. 从栈证据里的**绝对地址**反算该趟运行的实际模块基址。已知线索（**你要自己复算验证，不得照抄**）：
   - `_hl_match_14412.json` 中 `gamemd.exe+0x207f17` 的 addr=`6323991`，`gamemd.exe+0x20833f` 的 addr=`6325055`；
   - `_hl_match_40500.json` 中 `gamemd.exe+0x13eb1c` 的 addr=`5499676`，`DDRAW.dll+0x22b06` 的 addr=`1417489158`。
   验证 `addr − 记录里的偏移` 是否对该模块恒定，从而得出该趟 `gamemd.exe` 与 `ddraw.dll` 的**实际加载基址**。
2. 判据要显式：若 `gamemd.exe` 实际基址 == ImageBase `0x400000`，说明该趟**未重定位**；若不等，说明被 ASLR 重定位（并检查该 PE 是否有 `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` 与 `.reloc` 节）。
3. 输出一张 `MODULE_BINDING.md`：模块名 / 文件路径 / SHA-256 / ImageBase / 该趟实际基址 / 校验算式 / RVA→VA→**文件偏移**的换算表（用节表 rawptr 做 RVA→file offset，注意 vsize > rawsize 的尾部）。

## 第二步：每个位置的真实语义（核心交付）
对四个位置逐个完成，**每个都要给证据字节**：
1. **它到底是返回地址还是执行中的指令？** StackWalk64 的非栈顶帧给的是**返回地址**（`call` 之后的地址）。因此要先确认：该地址处是不是一条指令的**起始边界**？如果是，则阻塞点通常是**它前面那条 `call`**。用线性反汇编从可信函数边界推进确认边界，不要"往回退到看起来像指令开头"。
2. 恢复**所属函数**：从该地址向前找函数序言（如 `push ebp / mov ebp,esp`，或 `sub esp,N` 之前），给出函数起始 VA、是否被其它路径共享、多大。
3. 恢复**前一条调用**：`call` 的直接目标（若是 `call [mem]` 间接调用，追到具体槽位与运行期目标推断）、调用约定、实参在栈上的布局（给 `esp+4`… 逐项、以及是否 `ret N`）、返回值使用。
4. 恢复**下游 API 与正常返回条件**：若是导入调用，解析 IAT 槽到 `user32.dll` / `kernel32.dll` / `ntdll.dll` 的哪个导出；说明该 API 在什么条件下返回（例如 `WaitMessage` 在有消息时返回、`GetMessage` 阻塞、`MsgWaitForMultipleObjects` 超时/信号）。
5. 判断**上游入口**：这个函数被谁调用（静态可达性），对应哪一类上下文（主循环 / 对话框 / 退出清理）。

### 特别要求（写进报告，不要漏）
- **不许仅凭实参个数把函数定名为 `Blt`**。`ddraw.dll+0x22B06` 若看起来像 5 个显式参数 + `ret 0x14`，那**只是形状相似**；必须再核：vtable 槽号、`this` 指针来源、DirectDraw 接口（`IDirectDrawSurface` / `IDirectDraw` / `IDirectDrawSurface7`）的哪个方法序位、与 cnc-ddraw 本地源码/符号是否**版本匹配**。找不到匹配材料时，写"静态证据只支持 X，符号级确认需 Y"。
- **不同栈签名不能直接推导为不同根因**。`_hl_match_14412` 走 USER32 消息等待、`_hl_match_40500` 有事件走 `DDRAW+0x22b06`，你要明确：这两条是**捕获路径不同**还是**上游状态不同**；在拿到上游状态证据之前只写"候选"，不写"两条独立根因"。
- 优先复用**版本匹配的本地 cnc-ddraw 源码/符号**（先在仓库里搜 `ddraw`、`cnc-ddraw`、`IDirectDrawSurface`、`.pdb`、`*.c`/`*.cpp` 等）；没有就明说。

## 第三步：等待对象与唤醒方
- 识别等待对象的**创建 / 置位 / 复位 / 销毁 / 失败路径**（事件、互斥量、临界区、消息队列）。
- 追踪**应当唤醒它的线程/消息/呈现事件**。
- 给出 `WAIT_HYPOTHESES.csv`，列：`hypothesis_id, 位置, 假设(正常菜单等待/失焦节流/呈现同步等待/消息重入/锁等待/…), 支持证据, 反对证据, 最有区分力的下一条观测, 是否会正常发生, 等级`。

## 交付物（全部落在 `lead\next_re_20261112\RE-N05\`）
- `MODULE_BINDING.md`（含 SHA-256 实算、基址归一算式、RVA/VA/file-offset 换算表）
- `WAIT_CHAIN.md`（四个位置逐个：函数边界、前一条调用、实参布局、下游 API、正常返回条件、上游入口、证据字节）
- `WAIT_HYPOTHESES.csv`
- `EVIDENCE/`：你的脚本、原始 stdout、反汇编片段（每段标注 VA/RVA/文件偏移/原始字节）
- `UNKNOWNS.md`：未证项 + 最小缺失证据 + 建议替代方法
- `DISAGREE.md`（若发现任务书或既有报告的表述有问题）

## 质量红线
- 每条结论必须标等级：`[本次实测]`（你跑的命令+原始输出+退出码）/ `[本次读码]`（文件:行）/ `[静态推断]`（VA/RVA/文件偏移/字节）/ `[转引]`（来源路径:行）/ `[待运行验证]`。
- **扫描无命中要说明搜索范围、支持哪些编码、做过什么反例校验**。
- 不许把"有限静态搜索"写成"运行期全称证明"；不许把"这趟录到过一次"写成"机制已确认"。
- 本轮**零真机**：任何需要运行才能回答的，标 `[待运行验证]` 并给出最小观测方案，不要假装做了。

## 结束后
在你的最终回复里给 ≤40 行摘要：两个模块的 SHA-256 实算值、两趟的实际基址与算式、四个位置各自"是返回地址还是执行点"的判定 + 前一条调用 + 下游 API 一句话结论、`DDRAW+0x22B06` 的符号级确认到底做到什么程度（含未做到的部分）、两条栈签名的关系结论、以及最大的未证项。不要粘贴整个文件。
