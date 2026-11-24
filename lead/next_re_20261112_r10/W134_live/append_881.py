#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §881: the real per-frame chain and the reachable cost structure."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §881 ·" in s:
    raise SystemExit("REFUSE: §881 already present")

SEC = """
## §881 · **【① 的真锚点找回】`0x6BB9A0`(引擎初始化) → `0x48CCC0`(Conquer.CPP 主循环) → `0x55D360`(每帧更新) —— 该链已闭合，并给出可达的成本结构**（2026-11-15 19:10）

> 承接 §880（`0x006DD8B0` 是 TAction，已排除）。本轮从**帧计数器 `0xA8ED84` 反查写入者**入手，
> 一路追到真正的主循环。纯静态，零真机。

- **§881-1 [已证·唯一 `inc` 型帧推进]** 全 `.text`（1,394,120 条指令）里对 `0xA8ED84` 的 20 处引用中，
  **只有一处是"读-加-写"**：
  ```asm
  0055DE6A  mov  al,[0xA83D48]
  0055DE6F  test al,al
  0055DE71  jne  0x55DEC8          ; 某标志置位则跳过推进
  0055DE73  mov  edx,[0xA8ED84]    ; 读当前帧
  0055DE79  mov  eax,[0xB07784]    ; 目标帧
  0055DE7E  inc  edx               ; +1
  0055DE81  mov  [0xA8ED84],edx    ; 写回
  0055DE87  je   0x55DE9A
  0055DE8B  cmp  eax,ecx / jge     ; 与目标帧比较
  ```
  - 其余 19 处都是 `mov [0xA8ED84], 0` 或 `mov [0xA8ED84], reg`（**初始化/复位**），
    位置包括 `0x52DA08`、`0x5B7329`、`0x68676B`、`0x79758C` 等。
  - ⇒ **`0x55D360` 里的这一处就是每帧心跳。**

- **§881-2 [已证·主循环链已闭合]**
  | 环节 | 地址 | 证据 |
  |---|---|---|
  | 引擎初始化 | **`0x6BB9A0`**（10,256 B） | 直接调用主循环两次：`0x6BE041`、`0x6BE061` |
  | **游戏主循环** | **`0x48CCC0`**（780 B） | 体内唯一源文件字符串 **`D:\\ra2mdpost\\Conquer.CPP`**；含 `TXT_INITGAME_FAILED`、`MessageBoxIndirectA` |
  | 每帧更新 | **`0x55D360`**（2,940 B） | 在内层循环被调用；唯一 `inc` 型帧推进（§881-1） |
  - 主循环结构（我亲自反汇编）：
    ```asm
    ; 外层：0x48CDE5 <- 0x48CFB1
    0048CDCF  call 0x52BA60            ; Init.CPP 引导（§878 那个 4,333 B 函数）
    ...
    ; 内层（每帧）：0x48CE8A <- 0x48CEA8
    0048CE5D  call 0x7241A0            ; <<< ②-a 受害例程
    0048CE85  call 0x69BAB0
    0048CE8A  call 0x55D360            ; <<< 推进一帧
    0048CE8F  test al,al
    0048CE93  call 0x55CFD0            ; 谓词
    0048CE9C  call 0x48C8B0            ; Conquer.CPP
    0048CEA1  call 0x55CFD0
    0048CEA8  je   0x48CE8A            ; while (!谓词) 继续
    ...
    0048CFAA  call 0x52D9A0            ; Init.CPP（4,536 B）
    0048CFB1  jne  0x48CDE5            ; 外层继续
    ```
  - ⇒ **②-a 的崩溃点 `0x48CE5D` 就在主循环内层**，与"常规玩法必现"的现场统计（§835 的 25/26）一致。

- **§881-3 [已证·每帧更新的规模]** `0x55D360`：**90 处调用（44 个唯一 callee）、6 个循环，
  自身不引用任何对象数组 Count**。
  - 从它出发 BFS（深度 ≤4）：**可达 913 个函数**，按深度 `{1:44, 2:133, 3:331, 4:404}`。

- **§881-4 [已证·★ 对象数组迭代器的可达子集]**
  全镜像中"同时引用某数组 Count 且含回边循环"的函数共 **181 个**（我逐条扫出，非采样）。
  其中 **30 个**从每帧更新可达：
  | 深度 | 函数 | 大小 | 遍历的数组 |
  |---:|---|---:|---|
  | **1** | `0x55AFB0` | 1,901 | House ×2 |
  | **2** | **`0x67D300`** | **4,411** | **House/Unit/Infantry/Building/Aircraft/Anim/Trigger 各 1（7 种）** |
  | 2 | `0x64DEA0` | 11,242 | 9 种各若干（**已知是 SYNC 状态转储，见 §881-5**） |
  | 2 | `0x6D3D10` | 3,643 | Techno, House |
  | 2 | `0x55E420` | 3,507 | House |
  | 2 | `0x64C380` | 2,474 | House |
  | 2 | `0x64DAB0` | 973 | Infantry, Unit, Building, House |
  | 3 | `0x650A90` | 3,161 | House/Unit/Infantry/Aircraft/Building 各 4 |
  | 3 | `0x6C6F50` | 6,259 | House, Unit, Infantry, Aircraft |
  | 3 | `0x6D8DB0` | 2,584 | Building ×2 |
  | 4 | `0x6DD8B0` | 9,530 | （TAction，见 §880） |
  | … | 其余 19 个 | <2,300 | 多为单类 House/Techno/Building |
  - **`0x67D300` 是最强候选**：4,411 B、**111 个回边**、遍历 7 种数组、无字符串。
    其开头（我亲自反汇编）：
    ```asm
    0067D308  mov ecx,[0xA8B230]     ; 全局单例
    0067D310  call 0x689310
    0067D315  mov ecx,0x8A38E0
    0067D31B  call 0x4C6340
    0067D320  mov ecx,[0x8871E0]     ; §878 的超级武器单例
    0067D327  call 0x674730
    0067D342  call dword ptr [ecx+0x10]   ; 虚调用
    ```
    ⇒ 它是**依次驱动多个子系统单例的每帧协调器**。
  - 它只有 **1 个调用者 `0x67D1AF`**。

- **§881-5 [已证·`0x64DEA0` 是 SYNC 转储，不是模拟]** 其字符串为
  `SYNC%01d.TXT`、`COORD:%d,%d Facing:%d Mission:%d Type:%d(%s) ...`、
  `%s: IsHuman:%d Color:%s ID:%d HouseType:%s ...`
  ⇒ **多人同步校验/状态转储**，把全场对象格式化成文本写文件。
  - 它有 **2 个调用者**（`0x647368`、`0x64CCBA`），**可达但很可能被开关门控**——**未验证门控条件**。
  - ⚠️ 若它**未被门控而每帧执行**，仅它一个就是巨大开销（11 KB、写文件、遍历 9 种数组）。
    **这是 ① 最值得优先排除的一项**（静态可查：看两个调用者前是否有同步校验开关判断）。

- **§881-6 [已证·151 个迭代器不可从每帧更新到达]** 包括：
  `0x6CC390`（6,835，超级武器，§878）、`0x565C10`（5,374）、`0x519630`（5,083）、
  `0x6F9E50`（4,533）、`0x686B20`（4,532，任务载入）、`0x4F54A0`（4,250）、
  `0x599650`（4,124）、`0x6F8DF0`（4,031）等。
  - ⇒ **它们不在每帧路径上**（至少深度 ≤4 内不在），是事件驱动/载入期代码。
  - ⚠️ 注意：可达性用**直接调用**算，**虚调用不可见**（§853-4 的既有教训），
    所以"不可达"对虚派发的函数**不成立**。

- **§881-7 [未证·如实登记]**
  1. **没有做任何成本测量**。本节给的是**结构可达性 + 函数规模**，不是耗时。
     `0x67D300` 的 111 个循环里有多少**实际执行**取决于数据依赖分支（§873-5 的教训）。
  2. **虚调用不可见**：30 个可达迭代器只是"经直接调用可达"的那部分。
  3. `0x64DEA0` 的**门控条件未查**（见 §881-5）。
  4. `0x67D300` 的**调用者 `0x67D1AF` 未定性**，因此"它每帧必跑"**未证**——
     只证了"从每帧更新出发、经 2 层直接调用可达"。
  5. `0x55D360` 的 44 个 callee **未逐个定性**（只统计了数组引用）。
  6. `0xA8ED84` 的**语义**我按台账既有口径当"逻辑帧计数器"使用；本轮未独立验证它是否
     与 `Sleep(1000)` 的时间节流对齐。
  7. 本轮**未使用真机**（虽已获授权），因为纯静态已能闭合链条；真机可用于验证 §881-5/§881-7-4。

- **§881-8 [已证·产物]** `lead\\next_re_20261112_r10\\W134_live\\w134b_reach_frame.py` + `reach.log`
  （可复跑：BFS 深度、迭代器清单、不可达清单、主循环调用者）。
"""

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §881; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
