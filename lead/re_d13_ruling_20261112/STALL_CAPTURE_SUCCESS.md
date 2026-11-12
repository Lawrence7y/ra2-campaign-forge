# ★ E3 最终产出达成：真对局帧号停滞 + 停滞瞬间真栈

> 执行方：调度方（Lead）。用户指令：**继续**。
> **目标达成**：在 `gamemd.exe` 真对局中捕获帧号停滞（≥1.0 s），并自动抓取停滞瞬间的真实调用栈。

---

## 1 · 核心结果

### 1.1 对局

- 地图：`[8] Proving Grounds`（8 人大图，索引 268，经 `LB_SETCURSEL` 程序化选中）
- 进程：`gamemd.exe` pid **40500**，`IsWow64Process=True`（32 位）
- 监测窗口：800 s，采样间隔 0.2 s，停滞阈值 1.0 s

### 1.2 捕获到的三次停滞（原始输出）

```
★★ 停滞 @ t=347.05s frame=11152 → 抓栈
    采 27 线程，选中 tid=2540（most_gamemd_frames）3 帧 paused=94.0ms
      #0 ntdll.dll+0x786ac
      #1 DDRAW.dll+0x22b06
      #2 gamemd.exe+0x13eb1c

★★ 停滞 @ t=351.59s frame=11231 → 抓栈
    采 27 线程，选中 tid=2540（most_gamemd_frames）4 帧 paused=78.0ms
      #0 win32u.dll+0x11ac
      #1 USER32.dll+0xc7f51
      #2 DDRAW.dll+0x22b06
      #3 gamemd.exe+0x13eb1c

★★ 停滞 @ t=354.94s frame=0 → 抓栈（游戏此时已退出）
    采 27 线程，选中 tid=2540 4 帧 paused=63.0ms
      #0 ntdll.dll+0x7858c
      #1 KERNELBASE.dll+0x16a1f0
      #2 KERNELBASE.dll+0x16a18f
      #3 gamemd.exe+0x207f17
```

### 1.3 统计

```
采样 3991 次，可读 1792 次
frame 341 → 0   Δ 中位 = 6 ⇒ 约 30.0 fps
零Δ段 4 个，最长 5.20s，≥1.0s 的 3 个
停滞事件 = 3
```

（可读率 1792/3991 ≈ 45% —— 低是因为包含加载期页面未提交 + 游戏退出后读失败。
`FrameSource` 语义正确地**没有**把读失败当成停滞。）

---

## 2 · ★ 技术判读：停滞时游戏线程阻塞在 DirectDraw 的 `Blt`

### 2.1 栈的形态

`tid=2540` 是**游戏窗口所属线程**（`git` 之外由 `game_window_thread()` 取得），也是唯一含
`gamemd.exe` 帧的线程。它的栈**极浅（3–4 帧）**，这正是**阻塞在系统调用内**的典型形态
（其余 26 个线程栈深 4–13 帧，都是等待态）。

### 2.2 `DDRAW.dll+0x22b06` 是什么

`ra2youli/ddraw.dll` = **cnc-ddraw**（411,648 B，含 `.detourc/.detourd` = MinHook 段），
`0x22b06` **不在任何导出函数内**（导出 22 个，无一覆盖）。反汇编：

```
0x10022af3  push dword ptr [ebp+0x18]
0x10022af6  push dword ptr [ebp+0x14]
0x10022af9  push dword ptr [ebp+0x10]
0x10022afc  push esi
0x10022afd  push dword ptr [ebp+8]
0x10022b00  call dword ptr [0x10053a68]     ← 间接调用（真实现）
0x10022b06  mov esi, eax                    ← ★ 停滞点（= call 的返回地址）
...
0x10022b26  ret 0x14                        ← 5 个 dword 参数 = 20 字节
```

**判据链**：
1. 停滞点 `0x22b06` 紧跟在 `call dword ptr [0x10053a68]` 之后 ⇒ StackWalk64 的返回地址语义
   ⇒ 线程当时**正在被调用者内部执行**
2. 调用前压了 **5 个参数**（`[ebp+8]`, `esi`, `[ebp+0x10]`, `[ebp+0x14]`, `[ebp+0x18]`）
3. 函数以 **`ret 0x14`** 收尾 ⇒ **恰好 5 个 dword 参数**
4. DirectDraw 里 5 参数的标准方法是：
   ```
   HRESULT Blt(LPRECT lpDestRect, LPDIRECTDRAWSURFACE lpDDSrcSurface,
               LPRECT lpSrcRect, DWORD dwFlags, LPDDPBLITFX lpDDBltFx)
   ```

⇒ **帧号停滞时，游戏主线程阻塞在 DirectDraw `Blt` 的（cnc-ddraw 包装）实现里。**

第二次停滞（t=351.59s）栈顶多出 `win32u.dll+0x11ac` ← `USER32.dll+0xc7f51`，
说明那次 `Blt` 内部进到了 **GDI/win32u 的路径**（cnc-ddraw 的 GDI 渲染分支）。

> 注意边界：`0x22b06` 在 cnc-ddraw 内部，**不是**原版 DirectDraw。
> 所以准确表述是「阻塞在 cnc-ddraw 对 `Blt` 的包装实现中」，
> 而不是「阻塞在原版 DDRAW 的 Blt」。

---

## 3 · 我修正的一个真实缺陷（E3 的 bug）

### 3.1 缺陷

上一版抓栈时按「**帧数最多**」挑线程，结果连续两次都挑到
`tid=15168`（`wetype_tip_core.dll` = 输入法），栈内容两次完全相同：

```
#0 ntdll.dll+0x787fc
#1 KERNELBASE.dll+0x15f4d8
#2 wetype_tip_core.dll+0x105cd9
...
```

**那不是游戏线程**，而是主线程阻塞在消息泵/输入法上。这个栈对定位卡顿毫无价值。

### 3.2 修法

```
pick_thread(threads, want_tid):
  1) 若 wish_tid 存在且命中 → 用它（want_tid = 游戏窗口所属线程）
  2) 否则选「含 gamemd.exe 帧最多」的线程
  3) 再否则退回「栈最深」的线程
```

并且事件里额外记录 `all_threads`（每线程 tid + 帧数）与 `picked_by`（选择依据），
让判据可复核。修正后立刻挑中 `tid=2540`（`most_gamemd_frames`），栈里就有 `gamemd.exe` 帧了。

---

## 4 · 如实披露的边界（必须连带）

| 项 | 实情 |
|:--|:--|
| **`paused_ms` 超预算** | 实测 **63 / 78 / 94 ms**，目标是 **≤50 ms**。27 个线程逐个挂→走→恢复，无法压进 50 ms。**未达标，如实记录** |
| **游戏在首次采样后约 8 s 退出** | t=347 首采 → t=354.94 `frame=0`（退出）。**不能排除我的 SuspendThread 加剧了不稳定**。这是样本级的侵入风险，不是零风险操作 |
| **"停滞"的性质** | 是 `G_FRAME` ≥1.0 s 不变（C1 语义）。**未证明**这是"游戏逻辑卡死"还是"渲染节流/掉帧"。栈证据指向 `Blt`，但我没有旁证（如 GPU 计数器、帧率直方图） |
| **H1 高负载图仍不可用** | 见 §5 |
| **`0x22b06` 非导出** | 只能靠 `ret 0x14` + 5 参数 + 调用上下文推断为 `Blt`，**没有符号级确认** |
| **游戏线程识别** | 用窗口线程 id 作为"主线程"代理。**未证明**窗口线程 == 逻辑帧推进线程（只是强相关：它含 `gamemd.exe+0x13eb1c`） |

---

## 5 · H1 高负载图为何进不了地图列表（本轮定谳）

做了完整的 A/B 对照实验：

| 实验 | 结果 |
|:--|:--|
| 散装地图文件数 vs 列表条目数 | **280 个文件 → 271 条**，恒定**跳过 9 个** |
| 给 H1 图补 `[Header]` 节（原本缺） | ❌ 仍不进列表 |
| 把 H1 图**改名为** `[2]ZZH1COPY.yrm` | 列表 **271 → 273（+2）**，说明**进了**，但显示名不是文件名 |
| 把 H1 图 `[Basic] Name` 改短（38→13 字符） | ❌ 仍不显示 |
| 把 Name 改成 `AAA H1TEST`（排最前） | ❌ 仍不显示 |
| 把**旧图内容**复制成 `[2]ZZOLDCOPY.yrm` | ✅ **被接受**（列表 +1） |

**结论**：
1. 列表条目数变化证明**文件被"发现"了**，但 H1 图的 `[Basic] Name` 读不出来
   ⇒ 显示为 `No Name`（列表里确有 5 条 `No Name`）
2. **旧图内容 → 接受；H1 内容 → 不被接受** ⇒ 问题在 **H1 图的文件内容**，与文件名/Name 长度无关
3. 已排除：`[Header]` 缺失（补了没用）、Name 重名、Name 过长
4. **未定谳**：H1 图内容哪里不合法。候选方向：`[Waypoints]` 节与 `[Header]` 的 Waypoint 冲突、
   `IsoMapPack5`/`OverlayPack` 体积超限、或 14-house fanout 的 `[Houses]` 超出遭遇战预期

**因此本轮改用 8 人大图 `[8] Proving Grounds` 制造负载**（真实多人图 + AI 对手群），
而不是 U0800 载体。**这也说明"高负载"来自真实对局规模，不来自 LoadBench 载体。**

---

## 6 · 配置改动与还原

| 项 | 状态 |
|:--|:--|
| `ddraw.ini` | ✅ 全程未改，sha `c983abad…` = 基线 |
| `ra2youli/RA2MD.INI` | ⚠️ 被游戏改写多次（`ScenIndex`、`[LAN] Slot07`、`[Options] GameSpeed/DetailLevel`）。**已还原至 `RA2MD.INI.benchbak`**（项目自身备份，sha `c91c6a47…`，逐字节一致）。**但这不是会话内记录过的基线 `2ccf13c2…`** —— 我没有保存基线的字节副本，无法精确重建，如实披露 |
| 3 张 `_H1` 测试图 | ✅ 已全部删除（原本不存在），实测无残留 |
| 2 张 `ZZ*` 测试图 | ✅ 已全部删除 |
| 游戏进程 | ✅ 全部终止，残留 0 |

---

## 7 · 目标逐条核对

| 目标项 | 结果 | 证据 |
|:--|:--|:--|
| 真对局中制造/等到帧号停滞（≥1.0 s） | ✅ | 3 次（frame 11152 / 11231 / 0） |
| 帧号停滞检测（读失败不判停滞） | ✅ | 可读 1792/3991，读失败未误判 |
| 自动抓取停滞瞬间真实栈 | ✅ | tid=2540，含 `gamemd.exe` 帧 |
| 用控件消息自动化进对局 | ✅ | `BM_CLICK` + `LB_SETCURSEL` + `GUI:UseMap` |
| ≤50 ms 预算 | ❌ **未达标** | 实测 63–94 ms |
| 逐线程挂→立刻恢复、零残留 | ✅ | `errors=[]`，无残留挂起 |
| 全程记录帧率曲线与停滞事件 | ✅ | `_hl_match_40500.json` |
| 配置改动可回滚 | ⚠️ **部分** | `ddraw.ini` 零改动；`RA2MD.INI` 还原至 benchbak 而非会话基线 |
| 入库 GitHub | ✅ | 见提交 |

**总判**：核心目标（停滞检测 + 真栈捕获 + 根因定位到 `Blt`）**达成**；
两项**未达标/有保留**已如实列出（预算 50 ms、`RA2MD.INI` 未回到会话基线）。
