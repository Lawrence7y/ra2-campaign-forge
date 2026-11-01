#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§422 追加器：台账 + PENDING 双件字节级追加，CRLF 各自不变。"""
from __future__ import annotations

import sys
from pathlib import Path

LEAD = Path(__file__).resolve().parents[1]

LEDGER_TEXT = """
---

# §422 键契约审计抓到真缺陷：判档器读 FRAME.skipped，而真机对照臂只写 META

**轮次目标**：§421 立了「合成样本按『真机会写吗』造」的纪律。本轮把它从
口头纪律变成**机器审计**：判档器每个读取键 ↔ harness7 写入点，**两侧都 AST
取证**，不硬编码。当场抓出一个会让**真机 h7c 全程白跑**的缺陷。

## 一、缺陷本体（三重证据）

`h7_fs_rect_wait_skipped` 在 harness7 有**两个族**的写入点：

| 站点 | group | 值 | 写入条件 |
|---|---|---|---|
| `:7373` | **META** | `True` | fullscreen 且未 opt-out（短路臂） |
| `:7378` | **META** | `False` | fullscreen 且 `--h7-keep-rect-wait`（对照臂） |
| `:8087` | **FRAME** | dict | 外层 `if _H7_STATE["fs_rect_wait_skipped"]` |

★ FRAME 侧那个 dict 被 `if skipped` 挡着 ⇒ **只有短路臂写，对照臂根本不写**。
而判档器 `:155` **只读 FRAME**：

```
keep 臂真机产物：META=False 在场，FRAME 缺席
⇒ 判档器 sk = None ⇒ 判型掉 else「未跑到矩形等待，不是冒烟样本」⇒ return
⇒ 对照臂全部判据（polls_min / frame_s_min / late_start）永不执行
```

**真机 h7c 会整趟被判「不是冒烟样本」——冒烟验收的对照臂直接缺失。**
这是 §407 字段名错配（`max_nav_to_w0_s`）的同型事故，但更隐蔽：
**键名相同、group 不同**。

## 二、为什么三层验证都没抓住它

| 层 | 为什么漏 |
|---|---|
| mk_trip 手搓（smoke 25/25） | 样本按判档器**读取方**造（FRAME dict）——自洽样本 |
| forms 真实产物改造（10/10） | 我「改造」时也是按读取方注入 FRAME dict |
| fullpath（9/9） | 同上 |

★ **三层的共同盲区：样本的字段形态来自判档器代码，不来自 harness7 代码。**
这正是记忆里 `exclusion-rule-and-selfcheck-blindness` 的「对账器复用被测物
逻辑 ⇒ 两边同绿」。修法只有一个：**审计的写入侧独立取证**。

## 三、审计件与它自己踩的坑

`_audit_key_contract.py`：写入侧解析 harness7 全部 `rec.add(...)` 站点
（含每个站点的**祖先 If 链 + body/orelse 极性**），读取侧解析判档器全部
`rec_get(...)`，做三臂（short/keep/windowed）可达性推演。**5/5 PASS**。

审计器自身首版连踩三个取证不全，全部被**自己加的 W1 自检**抓出：

| 坑 | 症状 | 修法 |
|---|---|---|
| 只收 Constant 键 | f-string `f"stage_seconds:{name}"` 判「无写入点」⇒ W1 假阳性 | JoinedStr 还原成正则 |
| 只认 `rec.add` | Recorder 方法里 `self.rec.add` 漏收（正是 stage_seconds 出处） | `_is_rec_add` 两形态都认 |
| If 链不分极性 | `:7378` 在 `if not keep:` 的 **else** 里 ⇒ W4 假阴（keep 不可达） | `branch_chain_for` 带 body/orelse |

★ 三个都是「否定式断言（读键 ⊄ 写键）尤其怕取证不全」的实例。
W1 自检（「f-string 必须能匹配 stage_seconds:frame」）就是为这个放的——
**它一红，说明是尺子瞎了，不是被测物漏写**。

## 四、修复与回归升级

1. **判档器** `:155` 改读 **META**（三臂契约完整的来源）。
2. **mk_trip / forms / fullpath 的合成构造改成双写契约**：
   short 写 META=True + FRAME dict；**keep 只写 META=False**；windowed 不写。
   ⇒ smoke 25/25、forms 10/10、fullpath 9/9、trip_plan 9/9 全绿。
3. **审计 W3 从「抓到缺陷」升级为「回归钉死」**：缺陷现场的断言修好后必然过时，
   判据换成「判档器不得再读任何 keep 不可达键（已申报的 n2m 除外）」，
   并做**承重试验**：把判档器临时改回 FRAME 读取 ⇒ W3 精确红在
   `FRAME.h7_fs_rect_wait_skipped`。★ **修完缺陷的判据要同时改写成防回归形式**，
   否则它下次翻红会被当成误报忽略掉。
4. **fullpath 负控 M1 升级**：首版打 FRAME 侧的 `skipped: True` 锚点，
   修复后**存活**（判型已不读 FRAME）⇒ 改打 META 侧 `add(...True)` ⇒ 恢复捕获。
   ★ 又一例「变异存活先问尺子」：这次是**被测面移动了**，锚点要跟。

## 五、交付件

| 件 | 结果 |
|---|---|
| `_judge_l1_20261023.py` | `:155` 读 META（+11/−1） |
| `_audit_key_contract.py` | **5/5**，两侧 AST 取证 + W1 自检 + W3 回归 + 承重试验 |
| `_verify_h2e_smoke.py` mk_trip | 双写契约合成 | 25/25 |
| `_preview_h7_forms.py` / `_preview_h7_fullpath.py` | 构造同步 | 10/10 / 9/9 |
| `_verify_h7_fullpath.py` | M1 升级 META 锚点 | 6/6 |

★ 真机判读预期随之更正：**h7c 的 fields 里 META.h7_fs_rect_wait_skipped=False
是判型来源**；FRAME 侧缺席是正常形态。判档器现在会正确判它 fullscreen_keep。
"""

PENDING_TEXT = """
- **★★★ 真缺陷修复（2026-10-24，GOAL-3T §422）—— 不修则真机 h7c 整趟白跑**
  `_audit_key_contract.py`（两侧 AST 取证的键契约审计，**5/5**）抓到：
  判档器 `:155` 原读 **FRAME**.h7_fs_rect_wait_skipped，而 harness7 的 FRAME
  写入（`:8087`）被 `if fs_rect_wait_skipped` 挡住 ⇒ **对照臂只写 META=False
  （`:7378`），不写 FRAME** ⇒ 真机 h7c 会被判「不是冒烟样本」，
  **对照臂全部判据永不执行**（= D-05 冒烟第 3 条直接缺失）。
  - 三层预演/负控此前全部按**读取方**造样本（FRAME dict），自洽掩盖了它
    ——「对账器复用被测物逻辑 ⇒ 两边同绿」同族。
  - **修复**：判档器改读 META；mk_trip/forms/fullpath 合成改**双写契约**
    （short=META+FRAME / keep=仅META=False / windowed=不写）。
    回归：smoke 25/25、forms 10/10、fullpath 9/9、M1 升级后 6/6。
  - **真机判读预期更正（取代 §421 里「h7c 无 n2m」的同段）**：
    ① h7c 判型来源 = `META.h7_fs_rect_wait_skipped=False`；FRAME 缺席是**正常形态**。
    ② h7c 仍**不会有** `h7_nav_to_measure`（那只在短路臂写）⇒
       `late_start 不得出现` 以 `late_start=None` 通过，是**设计不变量**验证。
    ③ h7b（短路臂）META=True **且** FRAME dict 双写，`nav_to_measure_s` 仍须记录。
  - ★ 审计器自身三个取证坑（f-string 动态键 / self.rec.add / If-else 极性）
    全部被自设的 W1/W4 自检当场抓出 —— 否定式断言（「读键 ⊄ 写键」）
    必须配「取证完整性」阳性对照。台账 §422。
"""


def append(target: Path, text: str) -> None:
    before = target.read_bytes()
    assert b"\r\n" in before, "母本应为 CRLF 混合件: %s" % target
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")
    payload = text.lstrip("\n").replace("\r\n", "\n").encode("utf-8")
    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, "CRLF 数变了"
    target.write_bytes(after)
    print("%s: +%d bytes, %d->%d, CRLF=%d"
          % (target.name, len(payload), len(before), len(after), crlf0))


def main() -> int:
    append(LEAD / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md", LEDGER_TEXT)
    append(LEAD / "PENDING_DECISIONS.md", PENDING_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
