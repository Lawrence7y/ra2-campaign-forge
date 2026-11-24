#!/usr/bin/env python3
"""Append §843: A/B behavioural proof on the real game."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §843 · **真机 A/B 行为判决：同一 `ecx=0` 调用，未打补丁 = AV 杀进程（0xC0000005），打补丁 = 安全返回**（2026-11-15 19:40）

- **§843-1 [已证·这是 ②-a 首次"可控复现"]**
  此前 60+ 轮只有一份 `ra2youli\except.txt`（不可重现、场景不明）。本节第一次**按需触发**该缺陷：
  在运行中的 gamemd 里用 `CreateRemoteThread` 执行一段自建 trampoline：
  ```asm
  6A 00            push 0            ; FUN_00724730 的 1 个 dword 栈参
  31 C9            xor  ecx,ecx      ; this = NULL   ← 缺陷触发条件
  B8 30 47 72 00   mov  eax,0x00724730
  FF D0            call eax
  C7 05 <mark> 01000000   mov dword [mark],1   ; 只有"安全返回"才会写到
  EB FE            jmp  $
  ```
  工具：`W128_fix\live_guard_ab.py`；原始日志 `W128_fix\ab.log`。

- **§843-2 [已证·两臂结果]**
  | 臂 | 装 hook | 远程线程退出码 | 进程 | `mark` 是否被写 | 主窗口 |
  |---|---|---|---|---|---|
  | **control** | 否 | **`0xC0000005` = `EXCEPTION_ACCESS_VIOLATION`** | **死亡** | 未写（`None`，进程已不在） | — |
  | **patched** | 是（group A，6 个入口） | `259` = `STILL_ACTIVE`（停在 `jmp $` 自旋） | **存活** | **`1`（已写）** | `Yuri's Revenge` |
  - ⇒ **control 臂精确复现了缺陷**：`this=NULL` 进 `FUN_00724730`，首访 `[ebp+0x250]` 即 AV。
  - ⇒ **patched 臂证明守卫生效**：stub 的 `test ecx,ecx / jz` 走空路径 `ret 4`，
    控制流**回到了我们自己的 trampoline** 并写下 `mark=1`，游戏继续正常运行（主窗口标题仍在）。
  - ⇒ **判决：guard prevents the crash = YES**（脚本自动判定，两条件均满足）。

- **§843-3 [已证·为什么 control 臂没有生成 `except.txt`（解释一处反直觉现象）]**
  - 崩溃发生在**我们创建的远程线程**上，该线程没有游戏安装的 SEH 帧/线程级 handler，
    因此走的是系统默认终止路径，**游戏的 `SetUnhandledExceptionFilter` 落盘逻辑没有跑到**。
  - ⇒ 判据不能依赖 `except.txt` 是否生成，**必须用线程退出码 + 进程存活**。这也是脚本改用
    `GetExitCodeThread` 的原因（第一次跑时只看 `except.txt` 与进程存活，得到"control 未崩"的**假阴性**，
    重跑插桩后才拿到 `0xC0000005`）。
  - ⚠️ **纪律**：这是本轮第 4 次"代理指标不足导致误判"（前三次见 §833-1、§835-1）。
    共性教训：**判定"崩没崩"必须用最直接的可观测（退出码/异常码），不要用旁证（日志文件/进程表快照）**。

- **§843-4 [已验证的完整证据链（②-a）]**
  | 环节 | 证据 |
  |---|---|
  | 缺陷存在 | 真机 A/B：`ecx=0` → `0xC0000005`（§843-2） |
  | 缺陷范围 | 50 处无守卫 / 6 个例程（§833，两套独立方法互证 §840） |
  | 修复实现 | 6 个 stub 字节级生成 + capstone 自检（§834） |
  | 修复装得上 | 真机装入并回读 6/6 match + `jmp` 落点正确（§842-3） |
  | 修复可卸载 | `--unhook` 逐字节还原 + 再 dry-run rc=0（§842-5） |
  | **修复真的挡得住** | **真机 A/B：patched 臂安全返回、进程存活、`mark=1`（§843-2）** |

- **§843-5 [未证·仍未覆盖]** 本条只验证了 `0x724730` 一个入口。其余 5 个入口
  （`0x724580/0x7241A0/0x724520/0x724530/0x724540`）**只有装入+回读证据（§842），没有行为 A/B**。
  同一脚本可直接扩展（改 trampoline 的 `fn` 即可），属低成本后续。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §843" in src:
    sys.exit("ABORT: §843 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §843", "0xC0000005", "guard prevents"):
    print("  %-16s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
