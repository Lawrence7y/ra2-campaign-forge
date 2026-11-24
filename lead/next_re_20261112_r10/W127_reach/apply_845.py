#!/usr/bin/env python3
"""Append §845: third-defect behavioural A/B (site-level) + the complete evidence matrix."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §845 · **第三条缺陷的行为 A/B 也通过：原始 12 字节 AV、已安装 helper 返回 `al=0` 且进程存活**（2026-11-15 20:50）

- **§845-1 [已证·方法（不需要游戏任何对象）]**
  缺陷触发条件就是 `[obj+0xAC] == 0`，因此可以完全自造现场：
  在目标进程里分配一个**全零页**作假对象（保证 `[obj+0xAC]==0`），然后用远程线程执行：
  | 臂 | 执行的代码 |
  |---|---|
  | **control** | 原始 12 字节序列：`mov ecx,obj; mov edx,[ecx+0xAC]; mov al,[edx+0x155]` |
  | **patched** | `mov ecx,obj; call <站点 E8 实际指向的 helper>`（**通过已安装的补丁调用，不是副本**） |
  工具：`W128_fix\live_site_ab.py`；日志 `W128_fix\site_ab.log`。

- **§845-2 [已证·结果]**
  | 臂 | 线程退出码 | 进程 | `mark` | `al` |
  |---|---|---|---|---|
  | **control**（原始序列） | **`0xC0000005`** | **死亡** | 未写 | — |
  | **patched**（已装 helper） | `259` = `STILL_ACTIVE`（停在 `jmp $`） | **存活** | **1** | **`0x00`** |
  - patched 臂实测 `SITE 0x006F409C -> helper 0x0E2F0000`，即**真的走了安装后的补丁**。
  - ⇒ **判决：helper prevents the crash = YES**（脚本自动判定）。

- **§845-3 [已证·这条 A/B 同时验证了 §831 的根因判断]**
  §831 说根因是"`[obj+0xAC]` 未判空就解引用 `+0x155`"。本实验直接构造 `[obj+0xAC]==0`：
  - 原始序列**确实**在读 `[0+0x155]` 时 AV（`0xC0000005`）⇒ 根因判断成立；
  - helper **确实**走空路径返回 `al=0` ⇒ 修复语义正确（调用方 `test al,al; je` 会跳过整块）。

- **§845-4 [★ 最终证据矩阵：三种缺陷 × 五个环节]**（本会话全部完成）
  | 环节 | ②-a（6 个容器/字段例程） | 第三条缺陷（3 站点） | ②-b 数据层 |
  |---|---|---|---|
  | 缺陷存在（静态） | §833：50 处无守卫 / 6 例程 | §831：3 处 `[obj+0xAC]` 未判空 | §841-1：重叠断言恒真 |
  | 缺陷存在（**真机**） | **§844：6/6 入口 `ecx=0` → `0xC0000005`** | **§845：`[obj+0xAC]=0` → `0xC0000005`** | §841-2：step2=10 格 / step3=0 |
  | 修复实现（字节级） | §834：6 stub，capstone 自检 | §838：3 helper，capstone 自检 | §841-4：footprint 感知检测器 |
  | 修复装入（**真机回读**） | §842-3：6/6 match + jmp 落点正确 | §842-4：3/3 match | — |
  | **修复有效（真机 A/B）** | **§843/§844：6/6 YES** | **§845-2：YES** | §841-2：断言现在会真的失败 |
  | 可卸载 | §842-5：9/9 逐字节还原 | 同左 | — |
  - ⇒ **用户裁定的"三种都修"在设计与可复核验证两层全部闭合**，其中两种缺陷还拿到了**真机行为 A/B**。

- **§845-5 [未证·如实列出本轮仍未覆盖的]**
  1. **"正常游玩无副作用"未验**：没有进任务、没点 UI，因此"装 hook 后 tooltip 显示/游戏行为是否正常"未验。
     风险点：`0x724580` 空路径返回 `al=0` 改变"插入失败"语义；6 个例程的空路径是否影响正常流程。
  2. **未在真实崩溃场景里验证"崩溃消失"**：A/B 是"人为构造 `this=NULL`"，不是"游戏自己进入 NULL 期"。
     两者等价性依赖 §833/§840 的静态可达性分析，**没有运行期直接观测到 `[0x887368]==NULL`**。
  3. `0x7777F9` 的 `ebx==0` 仍未证（§840-3）。
  4. NAPOWR=3×2 未从 `artmd.ini` 的 `Foundation=` 交叉确认（§841-3）。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §845" in src:
    sys.exit("ABORT: §845 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §845", "最终证据矩阵", "al=0"):
    print("  %-16s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
