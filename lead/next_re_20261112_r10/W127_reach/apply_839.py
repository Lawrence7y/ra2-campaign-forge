#!/usr/bin/env python3
"""Append §839: compiler-free runtime patcher (unblocks §834-6)."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §839 · **绕开"没有编译器"：改用 Python 运行时补丁器，同一批机器码直接写入进程（离线自检 PASS）**（2026-11-15 16:20）

- **§839-1 [已证·动机]** §834-6 记录本机无 32 位 C 工具链 ⇒ `ra2nullguard.c` 无法编译，
  修复实际处于"代码写完但不可执行"的悬空状态。
  **但这个障碍是可以绕过的**：机器码早已生成并逐字节验证（`stubs_generated.h` / `sites_generated.h`），
  缺的只是"把字节写进进程"。写进程只需要 `VirtualAllocEx / WriteProcessMemory / VirtualProtectEx` ——
  **纯 Python + ctypes 即可，完全不需要编译器。**

- **§839-2 [已证·工件]** `W128_fix\apply_hooks.py`
  | 参数 | 作用 |
  |---|---|
  | `--pid N` | 目标进程（必填） |
  | （默认） | **dry-run**：只核对原始字节并打印计划，不写任何内存 |
  | `--apply` | 安装两组 hook |
  | `--unhook` | 从**磁盘镜像**还原原始字节（文件本身未被改动，故可精确还原） |
  | `--group a\|s\|all` | a = ②-a 六入口；s = 第三条三站点 |
  - 安装方式与 C 版完全一致：入口 `E9 rel32` → stub / 站点 `E8 rel32` → helper，余下字节填 `0x90`。
  - **复用同一批已验证字节**（从 `entries.json` / `stubs.json` / `sites.json` 读），不是另写一套。
  - 安全：**fail-closed**（当前字节与镜像不符就跳过该组并返回非 0）；改完恢复页保护；默认 dry-run，必须显式 `--apply`。

- **§839-3 [已证·离线自检 `selftest_patch.py` → PASS]**
  在没有运行中进程的情况下，把"能离线验证的部分"全部验掉：
  | 检查 | 结果 |
  |---|---|
  | 6 个入口的磁盘原始字节与计划一致 | **6/6 OK** |
  | 3 个站点的磁盘原始字节与计划一致 | **3/3 OK** |
  | 6 个 stub 可正常反汇编 | OK |
  | 3 个 helper 反汇编为 7 条指令且以 `ret` 收尾 | **3/3 OK** |
  | **rel32 算术**：对 6 个对抗性分配地址（含迫使位移为负的地址）逐一验证入口 `E9`、stub 内 `jmp`、站点 `E8` 是否正确落点 | **9 个对象 × 6 个地址 = 54 项全 OK** |
  - ⇒ 补丁**算术与字节层面已闭合**；唯一未做的仍是"在真实进程里跑一遍"。

- **§839-4 [未证·仍需真机]**
  1. 真实 `WriteProcessMemory` 到 gamemd 的 `.text` 是否被任何保护层拦截（该 exe 有非标 `.detour` 段，§827）。
  2. 装后游戏行为是否正常（未启动游戏验证）。
  3. 若 `ra2render.dll` 等第三方 hook 先改了同一批字节 ⇒ fail-closed 会整体跳过（有意设计）。
  - 验证顺序已备好：`verify_hook.py pre`（磁盘）→ `apply_hooks.py --pid N`（dry-run）→ `--apply` → `verify_hook.py post --pid N`（只读核对）。

- **§839-5 [已证·两种载体并存的关系]**
  | 载体 | 适用场景 | 状态 |
  |---|---|---|
  | `ra2nullguard.c` → DLL | 长期使用、每次启动自动生效 | 代码完整，**未编译** |
  | `apply_hooks.py` | 无编译器的当下、一次性验证、A/B 对照实验 | **已可运行**，离线自检通过 |
  - ⇒ **"没有编译器"不再阻塞验证路径**；只阻塞"随游戏自动加载"这一种形态。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §839" in src:
    sys.exit("ABORT: §839 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §839", "apply_hooks", "54 项"):
    print("  %-14s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
