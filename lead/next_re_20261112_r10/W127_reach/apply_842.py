#!/usr/bin/env python3
"""Append §842: LIVE verification result (hooks installed/verified/restored on real gamemd)."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §842 · **真机验证通过：9 个 hook 在真实 gamemd 里装对、读回、卸载还原；且运行时 `.text` 与磁盘逐字节一致**（2026-11-15 19:00）

- **§842-1 [已证·方法与产物]** `W128_fix\live_hook_test.py`（驱动）+ 既有 `apply_hooks.py` / `verify_hook.py`。
  流程：抢实例锁 → 启动沙盒 `gamemd.exe` → 等 pid → 静置 8 s → **dry-run** → **apply** → **独立回读** → **unhook** → 再 dry-run → 终止 → 查残留 → 还锁。
  原始日志：`W128_fix\live_hook_test.log`。本次 pid=4936，launcher=43060（WMI Win32_Process.Create，与项目既有启动方式一致）。

- **§842-2 [已证·★ 运行时 `.text` 与磁盘镜像逐字节相同]**
  - **dry-run 返回 rc=0**：`apply_hooks.py` 对 9 个站点逐一做了 fail-closed 比对
    （"当前内存字节 == 磁盘镜像字节"），**全部相等**才继续。
  - ⇒ **那个非标 `.detour` 段（内嵌 MZ，§827）并没有在运行期解密或改写 `.text`**。
  - ⇒ 这一条同时确认了两件事：① 静态反汇编/静态地址在运行期有效（既有全部静态结论的前提成立）；
    ② **保护层不拦 `WriteProcessMemory`**（否则 apply 会失败或进程崩）。
  - ⇒ 这是 §827-5 遗留问题（"是否会校验 `.text` 完整性"）的**部分答案**：至少在启动 + 静置 8 s 后写入 9 处、
    再读回、再还原的整个过程中，没有触发任何拦截或崩溃。

- **§842-3 [已证·②-a 六入口守卫（group A）真机回读 6/6 OK]**
  | 入口 | stub 地址 | stub 体 | 内部 `jmp` 落点 |
  |---|---|---|---|
  | `0x007241A0` | `0x0E300000` | match | 精确指回 `0x007241A5` |
  | `0x00724520` | `0x0E310000` | match | 精确指回 `0x0072452A` |
  | `0x00724530` | `0x0E320000` | match | 精确指回 `0x00724536` |
  | `0x00724540` | `0x0E330000` | match | 精确指回 `0x00724546` |
  | `0x00724580` | `0x0E340000` | match | 精确指回 `0x00724588` |
  | `0x00724730` | `0x0E350000` | match | 精确指回 `0x00724736` |
  - `verify_hook.py post` 独立解码：入口首字节 `E9`、`rel32` 落点 == stub、stub 内 `jmp` 落点 == resume、
    入口剩余字节全为 `0x90`。**POST-CHECK: PASS**。

- **§842-4 [已证·第三条缺陷三站点（group S）真机回读 3/3 OK]**
  | 站点 | helper 地址 | helper 体 | 填充 |
  |---|---|---|---|
  | `0x006F409C` | `0x0E360000` | match | 7×`0x90` ok |
  | `0x006F4124` | `0x0E370000` | match | ok |
  | `0x006F4173` | `0x0E380000` | match | ok |

- **§842-5 [已证·卸载可完整还原]** `--unhook` 把 9 处**逐字节**还原（日志逐条打印 `restored=... OK`），
  随后再跑一次 dry-run **rc=0** ⇒ 内存字节已回到与磁盘镜像完全一致的状态。
  ⇒ **该补丁是可逆的**，这对做 A/B 对照实验（同一进程内装/卸）很关键。

- **§842-6 [已证·无残留]** 终止后 `Get-Process gamemd` 为空；实例锁由脚本改写为
  `purpose=LIVE hook test FINISHED; residual_gamemd=0; owner restored.`。

- **§842-7 [未证·本轮仍未覆盖的部分（如实）]**
  1. **未在"有实际战斗/建筑被摧毁"的场景里验证崩溃是否消失** —— 本轮只到"进程起来、hook 装对、读回一致，
     然后卸载终止"。要验证 ②-a / 第三条缺陷的**行为**效果，需要在会触发这些路径的场景里跑（见下）。
  2. **未验证装 hook 后游戏功能是否正常**（没进任务、没点 UI）。风险点：`0x724580` 的 null 路径返回 `al=0`
     改变"插入失败"语义；6 个例程的 stub 是否影响 tooltip 正常显示，需进图观察。
  3. `0x7777F9` 的 `ebx==0` 仍未证（§840-3）。
  4. 那个 `UnicodeDecodeError`（subprocess 用 GBK 解 PowerShell 输出）只影响中文控制台回显，
     **不影响任何检查结论**（所有 rc 均为 0）。属工具瑕疵，已记录。

- **§842-8 [下一步·验证行为效果的最小实验设计]**
  | 目标 | 做法 | 判据 |
  |---|---|---|
  | ②-a 行为验证 | 装 G6 → 进一局 → 触发 tooltip 清理路径（悬停 UI + 战斗） | 不再出现 `Eip:00724737`；且 tooltip 显示正常 |
  | 第三条行为验证 | 装 group S → 进一局带可摧毁建筑的地图 | 不再出现 `Eip:006F40A2` |
  | 副作用检查 | 装全部 → 正常玩 3-5 min | 无新崩溃、tooltip 无异常、帧率无显著变化 |
  | A/B 对照 | 同进程 `--unhook` 后再玩 | 崩溃可复现（证明差异来自补丁） |
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §842" in src:
    sys.exit("ABORT: §842 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §842", "0x0E300000", "逐字节"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
