#!/usr/bin/env python3
"""Append §829-§830: the three crash signatures + ②-b's instruction-level proof."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = """
## §829 · **项目内其实有 3 种崩溃签名（不是 1 种）；占多数的 `EIP=0` 已定位到格链遍历 ⇒ ②-b 首次获得指令级实证**（2026-11-15 11:00）

- **§829-1 [已证·普查范围与方法]** `W127_reach\crash_log_census2.py` + `dedupe_and_s1.py` + `eip0_analysis.py`：
  扫 `ra2youli\`、`lead\next_re_20261112_r10\`、`lead\next_re_20261112_r02\` 下全部 `except*.txt`（102 个），
  按 **sha1 去重**（同一份文件被 harness 复制进各 trip 的 `baseline_except\`，故文件数 ≠ 事件数）。

- **§829-2 [已证·三种签名]**
  | 签名 | Access address | 指令 | 去重后日志数 | 归属 |
  |---|---|---|---:|---|
  | **`EIP=0x00000000`** | `0x00000000` | `Bytes at CS:EIP = ?? ?? …`（跳到地址 0 执行） | **20 份内容各异 + 40 份同源副本** | **②-b 格链污染（新定位，见 §829-3）** |
  | `EIP=0x00724737` | `0x00000250` | `8B 85 50 02 00 00` `mov eax,[ebp+0x250]` | 2 份内容（24 文件） | ②-a tooltip 空指针（台账 §799–§825） |
  | `EIP=0x006F40A2` | `0x00000155` | `8A 82 55 01 00 00` `mov al,[edx+0x155]`，**EDX=0** | 4 份内容（12 文件） | **第三条独立缺陷（未解）** |
  - ⇒ **②-a（tooltip）不是"项目内唯一真实崩溃记录"**，甚至不是最多的那一类。

- **§829-3 [已证·`EIP=0` 的根因：格链遍历命中已释放节点]**
  崩溃指令（`EIP=0` 的返回地址 `0x47C500` 反推，函数体自 `0x0047C4D0` 起）：
  ```asm
  0047C4D0  8B 05 A0 E9 A8 00     mov  eax,[0xA8E9A0]     ; 全局开关
  0047C4DB  8A 44 24 10           mov  al,[esp+0x10]      ; 参数：用哪条链
  0047C4E1  74 08                 je   0x47C4EB
  0047C4E3  8B B1 E8 00 00 00     mov  esi,[ecx+0xE8]     ; ★ 链 B 头（§2.1：+0xE8）
  0047C4EB  8B B1 E4 00 00 00     mov  esi,[ecx+0xE4]     ; ★ 链 A 头（§2.1：+0xE4）
  0047C4F1  85 F6                 test esi,esi
  0047C4F3  74 16                 je   0x47C50B
  0047C4F5  8B 7C 24 0C           mov  edi,[esp+0xC]      ; 要找的 WhatAmI
  0047C4F9  8B 06                 mov  eax,[esi]          ; 节点首 dword 当 vtable
  0047C4FB  8B CE                 mov  ecx,esi            ; this = 节点
  0047C4FD  FF 50 2C              call [eax+0x2C]         ; ★ WhatAmI（§2.1：vtable+0x2C）
  0047C500  3B C7                 cmp  eax,edi
  0047C502  74 0E                 je   0x47C512           ; 命中
  0047C504  8B 76 30              mov  esi,[esi+0x30]     ; ★ 后继（§2.1：+0x30）
  0047C507  85 F6 / 75 EE          test/jne               ; 遍历
  ```
  - **三个偏移全部对上 §2.1 的格链表**（链 A `+0xE4`、链 B `+0xE8`、后继 `+0x30`、WhatAmI `vtable+0x2C`）⇒ 该函数是 **"在格的链上按 WhatAmI 线性查找对象"**。

- **§829-4 [已证·20 份不同日志的寄存器完全同型]**（`eip0_analysis.py`）
  | 量 | 20 份中的取值 | 判读 |
  |---|---|---|
  | `ESI`（节点） | `0x15B4DEE0`–`0x15CADEE0`，**低 16 位恒为 `DEE0`** | 同一类定长对象的分配板带 |
  | `EAX`（被当虚表用的节点首 dword） | 18/20 = `0x10FDCA08`，另 2 份 `0x1604CCC0` / `0x16136E08` | **全部落在映像所有段之外**（`.text/.rdata/.data/.rsrc/.detour` 均不含）⇒ **不是虚表指针** |
  | `EDI`（要找的 WhatAmI） | **恒为 `0x00000024` = 36** | 见 §829-5 |
  - ⇒ 节点指针 `ESI` 本身有效但**其内存已被释放并复用**（首 dword 变成指向别处堆内存的指针），
    `[eax+0x2C]` 读到 0 ⇒ `call 0` ⇒ `EIP=0`、`Access address=0`。
  - ⇒ **这是 ②-b（格链污染 ⇒ 悬垂节点）的直接、可复现的指令级签名**，不再是仅靠对照实验"推断"。

- **§829-5 [已证·要找的对象类型 = `TerrainClass`]**（`whatami36.py`）
  - 方法：WhatAmI 是虚表槽 `+0x2C`，其实现形如 `B8 <imm32> C3`（`mov eax,N; ret`）。
    对 `_lead_rtti_map.json` 的 1,305 个虚表逐一套用此法，得 110 个不同 WhatAmI 值。
  - **自检通过**：`WhatAmI 6 → .?AVBuildingClass@@`、`WhatAmI 15 → .?AVInfantryClass@@`（与台账既有结论一致）。
  - **`WhatAmI 0x24(36) → .?AVTerrainClass@@`**（虚表 `0x007F522C`，WhatAmI 实现 `0x0071D300`）。
  - ⇒ 崩溃发生在"**在格链上查找 TerrainClass 对象**"的遍历里，链上出现了**已释放的 Terrain 节点**。
  - ⇒ 与 §2.3 呼应：`TerrainClass` 的占用状态切换虚函数是 `0x0071BFB0`（槽 73），即地形对象确实参与格链。

- **§829-6 [未证]**
  1. 谁把已释放的 Terrain 节点留在了格链上（是 §1 的多格建筑 `next` 单值复写，还是 Terrain 自身的摘链遗漏）。
     §1 的机制**能**产生这种后果（链交叉后遍历到别的格的对象，对象释放后即悬垂），但**本条日志不能单独区分**这两种成因。
  2. 第三条缺陷（`0x6F40A2`，`[edx+0x155]` 且 `EDX=0`）的完整成因未查。其上下文为
     `call [edx+0x3f8]` → `mov ecx,[eax]` → `mov edx,[ecx+0xAC]` → `mov al,[edx+0x155]`，即某对象字段 `+0xAC` 为 0。
  3. `[0xA8E9A0]` 这个全局开关的语义。

## §830 · **用户"主崩溃"自检对照表（回答阻塞项用的操作清单）**（2026-11-15 11:05）

打开 `ra2youli\\except.txt`（或任何一份崩溃日志），看这两行即可归类：

| 看到 | 结论 | 修法 |
|---|---|---|
| `Eip:00000000` + `Access address:00000000` | **②-b 格链污染**（占日志多数） | 禁止多格建筑重叠（方案 A）；链结构修复 |
| `Eip:00724737` + `Access address:00000250` | **②-a tooltip 空指针** | G2/G6 入口守卫（§825-7） |
| `Eip:006F40A2` + `Access address:00000155` | **第三条缺陷（未解）** | 需新分析 |

⚠️ 判别要点：②-a 与 ②-b **都可能**出现在"卡顿/大规模战斗"的场景里，
所以**不能靠场景描述区分**，只能靠 **EIP + Access address**。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §829" in src:
    sys.exit("ABORT: §829 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §829", "## §830", "TerrainClass", "Eip:00000000"):
    print("  %-14s %d" % (k, back.count(k)))
