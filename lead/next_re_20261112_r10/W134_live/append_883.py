#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §883: the per-frame structure — event pump + ring buffer + coordinator."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §883 ·" in s:
    raise SystemExit("REFUSE: §883 already present")

SEC = """
## §883 · **每帧结构已展开：`0x6474C7` 不是"轻路径"，而是**事件泵（生产者 + 消费者 + timeGetTime 时间戳 + 16,384 项环形缓冲）**；对象/子系统协调在另一支 `0x67D300`**（2026-11-15 21:05）

> 承接 §882（SYNC 转储已排除）。本节展开每帧必走的那条路径。

- **§883-1 [已证·`0x6474C7` 是 mode switch]** `0x647260` 在 SYNC 门之后跳到 `0x6474C7`：
  ```asm
  006474C7  mov  eax,[0xA8B238]          ; 模式选择器
  006474CC  cmp  eax, 5
  006474CF  ja   0x6475CD                ; >5 走默认
  006474D5  jmp  [eax*4 + 0x6475D8]      ; 6 路跳转表
  ```
  - `[0xA8B238]` 的 30 个写者中，`0x52D9A0`(Init.CPP) 与 `0x48CCC0`(主循环) 写入 **0/3/4/5**；
    其余写者在 `0x5EF7xx`、`0x67E440`、`0x77B2A0`。⇒ **是游戏模式/阶段选择器**。
  - ⇒ 所以 `0x6474C7` 不是"轻路径"，**它是每帧按模式分派的入口**。

- **§883-2 [已证·★ 事件环形缓冲：生产者]** 在 `0x6474C7` 的某个 case 里（`0x6474DC..0x647580`）：
  ```asm
  006474DC  mov  eax,[0xA802C8]
  006474E1  test eax,eax
  006474E3  je   0x647586              ; <<< 队列空/无记录 ⇒ 跳过整个生产循环
  006474E9  mov  ebp,[0x7E1530]        ; <<< WINMM.dll!timeGetTime
  ...
  006474F4  lea  ecx,[eax+eax*8]       ; idx*9
  006474F7  lea  eax,[eax+ecx*4]       ; idx*37   ⇒ 步长 37 dword = 148 字节
  00647534  mov  ecx, 0x1B             ; 27 dwords
  00647540  rep movsd                  ; 拷贝 108 字节
  00647542  movsw / 00647544 movsb     ; 再 3 字节 ⇒ 记录头共 111 字节
  00647545  call ebp                   ; timeGetTime() 取时间戳
  00647547  mov  edx,[0x8B4200]
  0064754D  mov  [edx*4 + 0xA70204],eax ; 存时间戳到旁表
  0064755F  mov  [0x8B4200],eax        ; 环形写指针 +1 & 0x3FFF
  00647564  mov  eax,[0x8B41F8]
  0064756A  mov  [0x8B41F8],eax        ; 事件计数 +1（上限 0x4000）
  00647574  call 0x652540              ; 每个事件一次
  ```
  - ⇒ **这是事件记录器：每条事件 111 字节 + `timeGetTime()` 时间戳，写入 16,384 项环形缓冲。**
  - 与命令行存在 `-record` 相吻合，但**该循环由 `[0xA802C8]` 门控**（不是无条件）。

- **§883-3 [已证·★ 同一环形缓冲的消费者：每帧无条件执行]**
  `0x6474C7` 末尾（`0x647594`）**无条件**调用 `0x64C380`（2,474 B）：
  ```asm
  00647594  mov  ecx,[0xA83D4C]
  006475A0  mov  edx,[ecx+0x34]
  006475A8  mov  edx,[edx+0xB8]
  006475AE  call 0x64C380               ; <<< 无条件，每帧
  ```
  而 `0x64C380` 开头就遍历**同一个环**：
  ```asm
  0064C384  mov  ebx,[0xA80238]         ; HouseClass::Array.Count（唯一的数组引用）
  0064C38D  mov  edi,[0x8B41F8]         ; <<< 事件计数 = 循环上界
  0064C397  cmp  edi, 0
  0064C3A1  jle  0x64C40D               ; 队列空 ⇒ 跳过
  0064C3B0  and  eax, 0x3FFF            ; 环索引 mod 16384
  0064C3B5  lea  edx,[eax+eax*8]        ; *9
  0064C3B8  lea  eax,[eax+edx*4]        ; *37  ⇒ 同一 148 字节步长
  0064C3BB  cmp  byte [eax+eax*2+0x8B4204], 0x1C   ; 记录类型 == 0x1C ?
  0064C408  inc  esi
  0064C409  cmp  esi, edi
  0064C40B  jl   0x64C3A9              ; <<< 遍历全部事件
  ```
  - `0x64C380`：**42 处调用、9 个循环、无字符串、仅引用 `HouseClass::Array` 一次**。
  - 后续在 `0x64C4E2`、`0x64C529`、`0x64C7D3`、`0x64C989`、`0x64CB06`、`0x64CBFD`、`0x64C4E2`、`0x64CC75`
    还有 8 个循环 —— 是**按事件类型分派的多段处理**。
  - ⇒ **每帧对环形缓冲里的事件做一次全扫描**，上界 16,384。

- **§883-4 [已证·环形缓冲是被管理的（不是单调增长）]**
  `[0x8B41F8]`（计数）与 `[0x8B41FC]`（读指针）各有多个写者，包括
  `0x64D990`、`0x652230`、`0x5C46E0`、`0x52D9A0`、`0x64BDD0` 等 ——
  ⇒ **有排空/重置路径**，所以"填满后永久 16,384 次扫描"这种退化**不会发生**。
  - ⚠️ 但**运行时实际占用率未知**，因此"每帧扫多少条"**未证**。

- **§883-5 [已证·对象/子系统协调在另一支]**
  每帧更新还有一条平行支路：`0x55D360 → 0x67CEF0 → 0x67D300`（4,411 B、111 回边、7 种数组）。
  它的开头依次驱动 `[0xA8B230]`、`0x8A38E0`、`[0x8871E0]`(超级武器单例) 并做虚调用。
  - ⇒ **每帧至少有三类工作**：
    1. **帧推进** `0x55D360`（2,940 B，90 调用）
    2. **事件泵** `0x647260` →（生产 `0x6474C7` 的 case + 消费 `0x64C380` 2,474 B）
    3. **子系统协调** `0x67CEF0` → `0x67D300`（4,411 B）

- **§883-6 [未证·如实登记]**
  1. **无任何计时**。本节只给结构，不给耗时。
  2. `0x6474C7` 的**6 个 case 我只展开了其中一个**（含事件生产者那个），其余 5 个**未定性**。
  3. `0x67CEF0`（`0x67D300` 的父）**未定性** ⇒ "每帧必跑"仍未证。
  4. 环形缓冲的 `[0xA802C8]` 语义（"队列非空"还是"录制开启"）**未证**。
  5. `0x64C380` 的 8 个后续循环**逐个未定性**（只知道都在处理事件）。
  6. 每帧实际事件条数**需真机**才能测；这决定了 `0x64C380` 的真实成本。
  7. 本节仍**未使用真机**。
"""

s = s.rstrip("\n") + "\n" + SEC

OLD = "  | `0x6474C7` | 每帧必走的\"轻路径\"，**未展开** |"
NEW = ("  | `0x6474C7` | ⚠️ **§883 已展开：它不是轻路径**——是按 `[0xA8B238]`（模式 0..5）分派的入口，"
       "内含**事件环形缓冲的生产者**（111 字节/条 + `timeGetTime` 时间戳 + 16,384 项环）|")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§882-5 table row updated")
else:
    print("WARN: row anchor found %d times" % s.count(OLD))

io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §883; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
