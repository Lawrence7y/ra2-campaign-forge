#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§407 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
---

# §407 H-2e：判档器**读不到** harness7 的冒烟判据（真机三趟跑完也无从验收）

**轮次目标**：H 系列离线项已清完（§406 §八）。本轮转去查 D-05 的前置缺口——
**harness7 真机冒烟跑完后，证据能不能被读出来。**

## 一、缺陷：冒烟验收的 5 条判据，判档器一条都不读

`lead/goal1_harness7_20261023/S399_SECTION.md` §九 列了真机冒烟的三趟五种预期：

| 趟 | 预期 |
|:--|:--|
| 窗口模式 | `h7_fs_rect_wait_skipped` 不出现、polls 与 harness6 同量级 |
| 全屏短路 | `skipped=true`、`pre_capture_wait_polls=0`、`stage_seconds:frame` <2 s |
| 对照臂 | polls 回到 244–253、frame 回到 ~125 s、`late_start` **不**出现 |

实测 `grep`：这些字段**全在** `qc151_fields.json` 里，而
`_judge_l1_20261023.py` **一处都没读**。

⇒ 真机三趟跑完，判档器输出里**看不到**任何一个冒烟判据。
这是 §401 H-5 的同型教训：**数据在盘上，没人去读**。

## 二、第二个缺陷：字段名对不上

判档器原文（`late_start` 分支）：

```
h7.get("max_nav_to_w0_s")
```

而 harness7 实际写入的是（`:4978`）：

```
"limit_s": H7_MEASURE_MAX_NAV_TO_W0_S
```

**全仓 grep `max_nav_to_w0_s` 只有判档器这一处**——harness7 里根本不存在这个键。
⇒ 真机 `late_start` 趟跑出来，阈值恒显示 `None`。

## 三、第三个缺陷（本轮最重）：判据区**永远执行不到**

第一版把冒烟判据写成脚本中段的顺序代码（`[4b]` 段）。离线核验时发现：

**全屏短路臂的正常结局就是 `return EXIT_SHORT_CIRCUIT`（3）** ——
冒烟判据在 `return` 之后 ⇒ **真机冒烟的第 2 趟（最关键那趟）一条都执行不到**。

而这个缺陷**离线看不出来**：如果核验只测「三窗齐全」的趟，永远发现不了。
所以核验器 S1/S6/S7 全部构造**短路趟**。

修法：抽成 `h7_smoke_section(lr, check, out_dir)` 函数，
在短路分支 `return` **之前**调用，三窗齐全路径也调用。

## 四、第四个缺陷（回归逼出来的）：只判哈希会误判

修完后跑 `_verify_judge_h2.py` 回归，**B2 变红**（原 36/36）。

根因：我判定「是否 harness7 冒烟趟」只看 `harness_sha16 == H7_SHA16`。
而 **harness7 的趟若在 window 阶段就失败**，`h7_fs_rect_wait_skipped` 根本不会被写
⇒ 那种趟**不是冒烟样本**，用「skipped 应等于 False」去判它是**拿设计预期判一个没跑到那里的趟**。

改法：区分两层。
1. `is_h7_run` —— 趟是否由 harness7 跑出（哈希或 h7 记录）；
2. **冒烟字段在不在场**（`skipped` 与 `polls` 都非 None）。

缺字段 ⇒ 明确打印「**不是冒烟样本**（多半在 window 阶段就失败了）」，**不产生断言**
（既不算通过也不算失败）。这条另加了 S8 专测。

## 五、形态识别：由**产物**判定，不看命令行记忆

真机三趟靠人记「这趟传了什么参数」不可靠，且会记错。改成从产物反推：

| 产物特征 | 形态 |
|:--|:--|
| `h7_fs_rect_wait_skipped.skipped == True` | `fullscreen_short` |
| `skipped == False` **且** `pre_capture_wait_polls ≥ 200` | `fullscreen_keep`（对照臂） |
| `skipped == False` 且 polls 很小 | `windowed` |

判据常量 `H7_SMOKE` 取自 S399 §九 的**设计预期**，不是从产物反推的：

| 形态 | skipped | polls | frame_s |
|:--|:--|:--|:--|
| `windowed` | False | ≤5 | — |
| `fullscreen_short` | True | ≤0 | **< 2.0** |
| `fullscreen_keep` | False | **≥200** | **≥100.0** |

另：对照臂额外断言 `late_start` **不得**出现（S399 §九 第 3 条）；
全屏短路臂额外断言 `nav_to_measure_s` **确实被记下来**（§六 边界 2 的唯一实测数）。

## 六、门禁核验：21/21 + 5 变异全杀（`_verify_h2e_smoke.py`）

核验器**不 import 判档器内部函数**，只喂合成趟目录、看**退出码 + 输出文本**——
否则会重演「对账器复用被测物 ⇒ 两边同绿」。

八趟合成产物：

| 趟 | 构造 | 期望 |
|:--|:--|:--|
| S1 | h7 / skipped=True / polls=0 / frame=1.4 / late_start | rc=3，[4b] 全绿 |
| S2 | h7 / skipped=False / polls=0 | 识别 windowed，rc=0 |
| S3 | h7 / skipped=False / polls=253 / frame=126.6 | 识别 keep，rc=0 |
| S4 | **harness6** / 无 h7 键 | 「不适用」而非通过 |
| S5 | keep + late_start=True | **必须变红** |
| S6 | short 但 frame=90 s | **必须变红** |
| S7 | short 但 polls=5 | **必须变红** |
| S8 | h7 但无冒烟字段 | 「不是冒烟样本」，无断言 |

变异 5 条（判据不是「rc != 0」，而是**基线 vs 变异的极性翻转**）：

| 变异 | 判据 | 结果 |
|:--|:--|:--|
| M1 短路分支不调冒烟函数 | `[4b]` 整段消失 | **杀死** |
| M2 windowed 也要求 skipped=True | 基线绿 → 变异红 | **杀死** |
| M3 short 的 polls_max 放宽到 999 | 基线红（S7）→ 变异绿 | **杀死** |
| M4 frame_s_max 放宽到 999 | S6 不再变红 | **杀死** |
| M5 删掉对照臂 late_start 判据 | S5 不再变红 | **杀死** |

★ **M3 第一次跑成「FAIL」是因为我的变异判据写反了**（要求变异后仍红）。
阈值放宽的正确效果是**从红转绿**（判据失去杀伤力），不是「仍然红」。
基线红 → 变异绿才是「判据承重」的证据。已改正。

## 七、回归

| 核验器 | 结果 |
|:--|:--|
| `_verify_judge_h2.py` | **36/36**（修复 B2 后回到全绿） |
| `_verify_launcher_h2.py` | 14/14 |
| `_verify_h2e_smoke.py` | **21/21**（本轮新增） |
| `_adjudicate_h5.py` | OK |
| `_adjudicate_h6.py` | OK |
| `_adjudicate_h3.py` | OK |

真实趟回归：`l1_20261023`（harness6）仍判 EXIT=3，
[4b] 段追加输出「**不是 harness7 ⇒ 冒烟判据不适用，不是通过**」——
不改变任何既有判定。

## 八、诚实边界

1. **没有真实 harness7 趟**。全部是合成产物。真机跑出来的字段形态可能与合成不同
   （例如 `h7_fs_rect_wait_skipped` 的 value 结构若变，`isinstance(sk, dict)` 分支会走另一条）。
2. `H7_SMOKE` 的阈值（polls ≤0 / ≥200、frame <2.0 / ≥100.0）取自 S399 §九 的
   **设计预期**。真机若实测落在边界附近（例如 polls=1），那是**需要重标**的信号，
   不是判据错了 —— 届时改常量并记账，不要放宽判据蒙过去。
3. **判档器退出码没有新增**。冒烟判据失败只是让 rc=1（与其它 FAIL 同码），
   无法从退出码区分「冒烟不过」与「档位不过」。这是有意的：
   S399 §九 要求「不新增退出码」。判读要看输出文本。
4. 本轮**没有**动 harness7 一个字节（母本 hash 未变，见 §九）。
5. H-1 真机三趟**仍未做**，仍卡「用户在场」。
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
