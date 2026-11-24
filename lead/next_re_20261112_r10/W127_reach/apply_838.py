#!/usr/bin/env python3
"""Append §838: third-defect implementation (3 null-safe helpers), verified."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §838 · **第三条缺陷已实现（3 处空安全替换，字节级验证）+ 与 ②-a 合并为同一 DLL**（2026-11-15 15:40）

- **§838-1 [已证·三处的精确位置（不是 3 处 `mov edx,[ecx+0xAC]`，第 3 处换了寄存器）]**
  | # | 站点 | 原始 12 字节 | 形态 | obj 寄存器 |
  |---|---|---|---|---|
  | 1 | `0x006F409C` | `8B 91 AC 00 00 00` `8A 82 55 01 00 00` | `mov edx,[ecx+0xAC]` / `mov al,[edx+0x155]` | ECX |
  | 2 | `0x006F4124` | `8B 91 AC 00 00 00` `8A 82 59 01 00 00` | 同上，`+0x159` | ECX |
  | 3 | **`0x006F4173`** | `8B 88 AC 00 00 00` `8A 81 5A 01 00 00` | `mov ecx,[eax+0xAC]` / `mov al,[ecx+0x15A]` | **EAX** |
  - 第 3 处**不是** `mov edx,[ecx+0xAC]`（我最初按反编译推测写成 3 处同形，**是错的**）：
    实测全函数只有 **2 处** `8B 91 AC 00 00 00`，第 3 处是 `8B 88 AC 00 00 00`（目标是 ECX、基址是 EAX）。
  - 三处**各恰好 12 字节**，且**各自紧跟 `84 C0 74 ...`（`test al,al; je`）** ⇒ 边界干净。
  - 校验：`W128_fix\verify_sites.py` → **SITE PRE-FLIGHT: PASS 3/3**（磁盘字节逐字节相同）。

- **§838-2 [已证·替换方案]** 12 字节塞得下一个 `call rel32`（5B）+ 7×`0x90`：
  ```
  E8 <rel32 -> helper>   90 90 90 90 90 90 90
  ```
  helper 做与原文**完全相同的 load**，然后判空：
  ```asm
  ; site1 的 helper（obj=ECX, dst=EDX, off=0x155）
  8B 91 AC 00 00 00   mov  edx,[ecx+0xAC]     ; 与原码相同
  85 D2               test edx,edx            ; ★ 新增的空检查
  74 07               je   .null
  8A 82 55 01 00 00   mov  al,[edx+0x155]     ; 与原码相同
  C3                  ret
  .null:
  30 C0               xor  al,al              ; 当作"该特性未启用"
  C3                  ret
  ```
  - 语义：`al=0` ⇒ 调用方的 `test al,al; je` **跳过整块**（fail-safe，功能不生效但不崩）。
  - 三个 helper 均 20 字节，`W128_fix\site_gen.py` 已用 capstone 逐一反汇编核对
    （load/判空/读字节/两条 ret 全部符合预期，`je` 精确落在 null 路径）。
  - **寄存器安全性**：三处之后 `EDX`/`ECX` 均不再被使用（站点后紧跟 `test al,al`，
    随后路径自行重载）；`call` 在 12 字节窗口内不改变任何 ESP 相对偏移。

- **§838-3 [已证·合并为单一 DLL]** `ra2nullguard.c` 现在同时装两组 hook：
  | 组 | 对象 | 数量 | 方式 |
  |---|---|---:|---|
  | ②-a 容器守卫 | `0x7241A0/520/530/540/580/730` | 6 | 入口 `E9 rel32` → stub（搬迁原序言字节） |
  | 第三条判空 | `0x6F409C/0x6F4124/0x6F4173` | 3 | 站点 `E8 rel32` → helper（12B 窗口内） |
  - 两组都是 **fail-closed**：装前逐字节比对原始字节，不符即整体拒绝（不半装）。
  - 卸载：两组各自 `Uninstall` 完整还原；`DllMain` 在 `DLL_PROCESS_DETACH` 调用。
  - 导出：`RA2NG_InstallAll` / `RA2NG_UninstallAll` / `RA2NG_ReadEntryPub` / `RA2NG_ReadSitePub` / `RA2NG_Counts`。

- **§838-4 [已证·仍未做的两件事]**
  1. **未编译**（本机无 32 位工具链，§834-6）⇒ 语法正确性**未由编译器确认**，仅经人工复查。
  2. **未真机运行** ⇒ hook 是否真的在 gamemd 里装对、以及装后游戏行为是否正常，**均未验证**。
     `verify_hook.py post --pid` 已备好（只读 RPM），一旦有可运行环境即可核验。

- **§838-5 [未证·风险登记]**
  1. `0x724580` 的 null 路径返回 `al=0`（"插入失败"），调用方是否会走异常分支——静态看不会（§825-9）。
  2. `DllMain` 内装 hook 的时机：目标例程属 UI/tooltip 路径，理论上不在 `LoadLibrary` 期间被调用，但未真机验证；
     已提供导出函数以便宿主在安全点显式调用。
  3. 若 `ra2render.dll` 或其它第三方 hook 先行修补了同一批字节，本 DLL 会因 fail-closed 而**整体拒绝安装**
     （这是有意的：宁可不动，也不要在未知状态下半装）。此时应改用导出函数按组安装并查看返回码。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §838" in src:
    sys.exit("ABORT: §838 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §838", "0x006F4173", "fail-closed"):
    print("  %-14s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
