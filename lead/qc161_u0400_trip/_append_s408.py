#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§408 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
---

# §408 H-2f：D-05 冒烟第 1 趟**根本发不出来** —— `--fullscreen` 被焊死

**轮次目标**：§407 修好了「harness7 冒烟证据能不能被**读出来**」。
本轮顺着同一条链往下查**发射端**：三趟到底发不发得出来。

## 一、缺口：窗口模式趟没有开关

S399 §九 第 1 趟要求：**「不传 `--fullscreen`」**跑窗口模式。
实测 `_launch_l1_20261023.py` 原 `:244`：

```
        "--measure", "1",
        "--fullscreen",        ← 焊死在 argv 列表里
        "--evid-diff",
```

⇒ 本发射器**只能发全屏趟**。真机三趟里的第 1 趟（窗口模式）
**在这个工具下根本发不出来** —— 不是「没做」，是「做不了」。

★ 与 §407 是同一个病根的两个方向：
- §407：证据写出来了，判档器**不读**；
- §408：趟需要这么发，发射器**不发**。
两者都属于「设计写了、工具链没接上」，且都**不会报错**，只会安静地缺一块。

## 二、修法：开关化，缺省行为一字不改

`--fullscreen` 改为由 `--no-fullscreen` 控制：

| 调用 | argv |
|:--|:--|
| 不传（缺省） | 含 `--fullscreen`，**与 10-23 四趟逐字一致** |
| `--no-fullscreen` | 不含 `--fullscreen` ⇒ 窗口模式 |

同时把 argv 拼装从 `main()` 内联**抽成纯函数** `build_harness_argv(...)`。
理由不是整洁：**内联在 main 里就无法离线断言**，只能靠读代码，
而「读代码觉得对」正是本轮前两次缺陷的成因。

位置也刻意保持：`--fullscreen` 仍在 `--evid-diff` **之前**。

## 三、★ 顺带挖出 §407 的一个盲区：窗口模式趟被判成「不是冒烟样本」

修发射器时核对 harness7 写入条件，发现两行 rec 的**写入前提不同**：

| 行 | 位置 | 条件 |
|:--|:--|:--|
| `h7_fs_rect_wait_skipped` | `:7364` 起 | 整块包在 `if args.fullscreen:` 里 ⇒ **只在全屏写** |
| `pre_capture_wait_polls` | `:8109` | **无条件写** |

而 §407 的判据是「`skipped` 与 `polls` 都非 None 才算冒烟样本」
⇒ **窗口模式趟（第 1 趟）永远被判「不是冒烟样本」**，而那正是 D-05 要验的三种形态之一。

⇒ 判据改为「`polls` 在场即可」+「窗口模式下断言 `skipped` **不在场**」。
窗口模式的正确值不是 `skipped=False`，而是**那一行根本不存在**。

★ 这个改动又逼出一个死数据：`H7_SMOKE["windowed"]["skipped"]` 这个键
**从未被读取**（窗口模式走另一条分支）。变异自检 M2 改它，结果**没有任何断言变化**
⇒ 当场删掉该键。**留着它等于给后人一个「改这里有用」的错觉。**

## 四、门禁核验：21/21（原 14 + 新 7）+ 2 变异全杀 + h2e 22/22

`_verify_launcher_h2.py` 新增 G 组：

| 断言 | 内容 |
|:--|:--|
| **G1** | 缺省 argv 与**改前硬编码的 13 项**逐元素相同（逐字重建后比对，不靠「看起来差不多」） |
| **G2** | `fullscreen=False` ⇒ argv 不含 `--fullscreen` |
| **G3** | 两种模式**只差**这一项，别的一字不动 |
| **G4** | `--fullscreen` 仍在 `--evid-diff` 之前 |
| **G5** | `extra_argv` 追加在末尾（对照臂 `--h7-keep-rect-wait` 的唯一通道） |
| **MG1** | 变异「忽略 fullscreen 开关」⇒ G2 变红 |
| **MG2** | 变异「`--fullscreen` 挪位」⇒ G1 逐元素比对变红 |

```
G1 缺省 argv 与改前硬编码版本逐元素相同    PASS  无
G2 fullscreen=False ⇒ argv 不含 --fullscreen   PASS
G3 两种模式仅差 --fullscreen 一项          PASS
G4 --fullscreen 仍位于 --evid-diff 之前    PASS
G5 extra_argv 追加在末尾（对照臂通道）      PASS
MG1 变异「忽略 fullscreen 开关」⇒ G2 变红   PASS
MG2 变异「--fullscreen 挪位」⇒ G1 变红      PASS
TOTAL 21/21 PASS
```

★ **G1 是本轮最重要的那条**：它把「我没改既有行为」从一个说法变成可执行比较。
如果只写 G2（窗口模式不带 `--fullscreen`），把 `--fullscreen` 挪个位置或
顺手改个别的参数都会全绿 —— 那种门禁抓不到「改坏了缺省路径」。

## 四、三趟现在都发得出来

| 趟 | 命令 | 依赖 |
|:--|:--|:--|
| 1 窗口模式 | `--harness-sha16 d019… --no-fullscreen --suffix w` | **本轮新增** |
| 2 全屏短路 | `--harness-sha16 d019… --suffix a`（缺省即全屏） | §407 已修 |
| 3 对照臂 | `--harness-sha16 d019… --suffix k --extra-argv --h7-keep-rect-wait` | 既有 |

卫生检查（A8 残留进程数=0）本就在 `main()` 预检里，无需新增。

## 五、回归

| 件 | 结果 |
|:--|:--|
| `_verify_launcher_h2.py` | **21/21**（原 14 → +7） |
| `_verify_h2e_smoke.py` | **22/22**（原 21 → +S9 窗口模式被判） |
| `_verify_judge_h2.py` | 36/36 |
| `_adjudicate_h5 / h6 / h3` | 全 OK |
| 真实趟 `l1_20261023` 判读 | 仍 EXIT=3（未受影响） |

## 五b、★ 本轮自己造成的污染（第二次 CRLF 事故，已修）

提交前查 `git diff --numstat` 发现判档器 `+580/−551` —— 而本轮真实改动只有几十行。
根因：该文件**行尾基线是纯 LF**（HEAD CRLF=0），而 `Edit` 工具在 Windows 上
**整文件重写**并写成 CRLF ⇒ 变异后 CRLF 0 → **580**，逐行都算一次重写。

修法：`bytes.replace(b"
", b"
")` 复原，`+580/−551` 立刻回到 **+43/−14**。
修后三个验证器重跑：21/21、36/36、22/22 全绿。

★ 与 §403 的台账事故**同族但方向相反**：
- §403：台账基线 **混合**（86 CRLF + 15k bare-LF），Edit 把 CRLF **抹成 LF**；
- §408：判档器基线**纯 LF**，Edit 把它**全转成 CRLF**。

⇒ 教训不是「别用 Edit」，而是 **Edit 之后必须查 `--numstat`**：
纯追加的删除数应为 0，局部修改的行数应与改动规模相称。
**删除数远超真实改动 = 行尾被动了**，与内容无关。

## 六、诚实边界

1. **没有真机**。三趟只是「发得出来」，**发得好不好不知道**。
2. `--no-fullscreen` 这条路径**从未被真机走过**。窗口模式不写
   `h7_fs_rect_wait_skipped` —— 依据是 harness7 `:7364` 的条件块，**读代码得出**，未实测。
   §408 已让判档器把这种形态识别为 `windowed` 并真判（S9 证明 polls=40 会变红），
   但**真实趟长什么样仍未见过**。
3. `H7_SMOKE` 的阈值全是 S399 §九 的设计预期。真机若落在边界附近，要重标常量并记账。
4. 本轮**只改发射器与判档器**，harness7 零字节改动（母本 hash 未变）。
5. H-1 真机三趟**仍未做**，仍卡「用户在场」。§407+§408 之后，
   **读取端与发射端都已就位**；剩下的纯粹是真机执行。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    payload = SECTION.encode("utf-8")
    if not payload.endswith(b"\n"):
        payload += b"\n"
    after = before + payload
    assert after.startswith(before)
    assert len(after) == len(before) + len(payload)
    assert before.count(b"\r\n") == after.count(b"\r\n"), "CRLF must not change"
    print("before %d B / lines %d / CRLF %d"
          % (len(before), before.count(b"\n"), before.count(b"\r\n")))
    print("append %d B -> after %d B / lines %d / CRLF %d"
          % (len(payload), len(after), after.count(b"\n"), after.count(b"\r\n")))
    LEDGER.write_bytes(after)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
