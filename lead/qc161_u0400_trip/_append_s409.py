#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§409 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
---

# §409 D-07 支撑：36 high 逐条定性 —— 阻断是真的，但「清零」与铁律冲突

**轮次目标**：§408 的提交过了，**推送被 L3 整仓门禁拦下**，报「36 个高危」。
D-07（另一会话立项）当时只有这个数字。本轮不改门禁、不绕钩子，
而是把「36」拆成可复算的清单，让 D-07 的三个选项能被真正裁决。

## 一、先钉计量口径：36 是 occurrence，不是缺陷数

用密封深扫产物 `scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0/findings.json`：

| 口径 | 值 | 说明 |
|---|---|---|
| findings 条数 | 37 | 含 1 条 low |
| **severity==high** | **36** | 与门禁口径**逐位相符** |
| 唯一 `findingId` | 29 | 粒度实测 = **(规则, 文件) 对**，**不是**缺陷数 |
| 受影响文件 | 21 | |
| 跨文件共用 findingId | **0** | 证实上一行的粒度判断 |

★ 口径陷阱（本轮自己踩到并修掉）：我第一版脚本写「唯一 findingId = 实际缺陷数」，
据此输出「29 个缺陷」——**错**。实测 `findingId` 在同一文件同规则的多行间**共用**
（`atlas_audit.py:189/193/230` 三处一个 ID），跨文件**从不**共用（组内文件数恒为 1）。
把它当缺陷数，等于把「一处规则命中多行」记成「一个缺陷」。已在件内改口径并加
「跨文件共用 = 0」作为该判断的自证断言。

**构成拆解**：

- **28 条静态 sink**（规则直接命中文件打开写盘点）；
- **8 条跨文件污点链**，且扫描器自己标了 `advisory: true` + `proofGaps`：
  「静态 advisory 需要人工确认真实数据流和可利用性」。

★ 这 8 条是**深扫才出现**的：变更前 `normal` 档 29 条（28 high + 1 low），
深扫后 37 条。差额**不是我引入的**——逐条 diff 显示新增 8 条全落在
harness4/5/6/7 上，而这三个文件我一个字节没碰（harness6/7 哈希实测仍等于冻结值）。

## 二、决定性的发现：6 条撞在**哈希冻结件**上

| 件 | 实测 | 冻结理由 | 该件上 high |
|---|---|---|---|
| `qc151_trip.harness6.py` | ✓ `ff8245d27b3db22a` / 463,219 B | 母本（四趟实测 `harness_sha16`） | 3 |
| `qc151_trip.harness7.py` | ✓ `d019e8beecfb5fd8` / 472,020 B | D-05 补丁副本（母本零改动派生） | 3 |

⇒ **6 条 high 落在「改了就会推翻全链哈希断言」的件上**。

这改写了 D-07 的选项性质。D-07 原来把 A/B/C 摆成三条并列路线，隐含
「A 只是工作量大」。实测后不是：**A 要求他人去改母本/补丁副本，
而那与「母本零改动」的铁律直接冲突**——不是愿不愿做，是做了就自毁前提。

另外 12 条落在 `tools/atlas_*.py`（atlas 审计线）、`dropped611`、`a8` 等**他线写域**，
本线按分工无权修改。

## 三、本线贡献：0

`_census_d07_gate36.py [5]` 实测：**本线写域（`lead/qc161_u0400_trip/`）命中 0 条**。
⇒ 阻断完全来自既有件，§408 的交付件本身对门禁**贡献为零**。
这也解释了为什么**提交能过、推送不能过**：commit 走 diff-only 档，
push 走整仓。

## 四、负控：证明这份普查**能红**

普查件通篇是「0 条」「6 条」这类**否定式结论**。按既有教训
（`gate-assert-values-not-existence`），否定式断言在本规则已按此实现时永远为真。
故配 `_verify_census_d07.py`：不 import 被测件内部（避免两边同绿），
而是**造篡改过的 findings.json** 让它跑，只判输出文本是否随篡改而变。

| 变异 | 篡改 | 期望 | 实测 |
|---|---|---|---|
| M1 | 一条 high 落点改到本线写域 | 本线段报出该路径 | ✓ |
| M2 | 一条 high 降成 medium | high 36→35 | ✓ |
| M3 | 移除 harness6 全部落点 | 冻结命中 6→3 | ✓ |
| M4 | 一条污点链改 static | 污点链 8→7 | ✓ |
| M5 | 两文件共用一个 findingId | 跨文件共用 0→≥1 | ✓ |
| M6 | 全部 high 降级 | high=0 且冻结=0 | ✓ |

**11/11 PASS，6/6 变异被捕获。**

★ 过程中 M1 先红了一次，但**红的是我的判据不是被测件**：我写了
`"1 条" in out.split("[5]")`，而普查件在该段打印的是**路径本身**
（`★ <path>:<line>`），不打印「1 条」这种措辞。改成找被注入的路径
（`"_evil.py" in seg`）后转绿。**变异存活时要先问「是件错了还是尺子错了」**，
这一条与 §405 M6 同型。

## 五、结论与对 D-07 的影响

1. **门禁阻断是真的**，不是误报噪声：28 条静态 sink 都是真实的文件写盘点。
2. **但「清零」不成立**：6 条撞在哈希冻结件上，清零等于改母本，与铁律冲突。
3. **本线无责**：贡献 0 条。
4. ⇒ 真正可走的是 **B（按写域路由：只扫 staged 路径）**——它不是「偷懒」，
   而是与 commit 已有的 diff-only 档**对齐**（同一件事，push 端没跟上）。
   C（镜像仓）受「主仓=唯一真源」限制。
   A 若要成立，需先裁决「冻结件是否允许为安全告警破冻结」——这是**Lead 级**
   的口径冲突，不是执行问题。

**交付件**（均离线可复跑）：

- `lead/qc161_u0400_trip/_census_d07_gate36.py` —— 普查，exit 0；
- `lead/qc161_u0400_trip/_verify_census_d07.py` —— 负控，11/11 + 6 变异。

**未做**：未改门禁配置、未设 `core.hooksPath`、未 `--no-verify`、未碰任何他线文件、
未改 harness6/7（哈希逐位复核仍等于冻结值）。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = (body.replace("\r\n", "\n")).encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d"
        % (crlf0, after.count(b"\r\n")))

    LEDGER.write_bytes(after)
    print("appended %d bytes; total %d -> %d"
          % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
