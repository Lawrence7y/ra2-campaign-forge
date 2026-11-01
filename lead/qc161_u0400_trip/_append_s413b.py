#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§413b 勘误追加：修正 §413 里「17/17」为最终 19/19，并补记三个新坑。

★ 不回头改 §413 正文（追加纪律），只在其后追加勘误 —— 让「先写了什么、
  后来发现什么」都留在台账里。
"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §413b §413 勘误：自检条数 17 → **19**，以及收尾时新踩的三个坑

**为什么要勘误**：§413 落盘时自检是 17 条，收尾自查又发现该件有**两个真实缺陷**，
修完变成 19 条。数字变了就得追记，否则台账与件对不上。

## 一、`--json` 模式曾被自检文本污染

`--json` 承诺输出机器可读内容，但自检的 `✓/✗` 也打在 stdout 上
⇒ `json.load(stdout)` 报 `Extra data`。**这是工具的真实缺陷**，不是使用方式问题。

修法：`--json` 时自检文本改走 **stderr**（`_QUIET` 开关 + `rec()` 分流），
stdout 只剩 JSON。并把它定成常驻判据 **C10**（子进程实跑一遍、`json.load` 成功才算过）。

## 二、C10 初版是**无界自递归**

C10 要「启动自己」来验证 `--json` 隔离，而子进程会**再跑一次 C10**
⇒ 无限生孩子（实测一条命令挂住，只得手动 kill）。

修法：环境变量哨兵 `TRIP_PLAN_JSON_PROBE`，子进程侧跳过本项。

★ 教训：**自检里「启动自己」必须自带终止条件**。这与「门禁要能拒绝什么」同族——
一个自身会失控的判据，比没有判据更危险。

## 三、C9 与 C10 语义冲突 ⇒ C9 必须收窄

C9 原判「本件不含任何子进程启动调用」，C10 引入后**必然**含 `subprocess.run`
⇒ C9 恒红。但 C9 的原意不是「不许有子进程」，而是**「不许把被测对象启动起来」**。

修法：C9 改为判「有无 spawn/Popen/system 调用，或有无 harness 专用参数字面量
（`--target-map` / `--carrier-create-from` / `--measure`）」。
★ 并补 **C9b 阳性对照**：同一套判据扫**真发射器**必须判为「启动被测对象」——
否则收窄语义后可能变成「谁都判不出来」的空断言（假绿）。

## 四、负控里的「17/17」是另一个自己埋的雷

负控原本硬编码 `"TOTAL 17/17 PASS" in out`，判据变 19 条后**假红**。
改为判 `TOTAL (\\d+)/(\\d+)` 的**分子==分母**且无 ✗ 行 ⇒ 条数增长不再破坏负控。

★ 与「写死数量」同族：**判据条数会变，断言不该锚在条数上**。

## 五、最终状态

| 件 | 结果 |
|---|---|
| `_trip_plan_h1.py` | **19/19 PASS**（C1–C10，含 C9b 阳性对照） |
| `_verify_trip_plan_h1.py` | **8/8 PASS**，5 变异全捕获 |

三趟命令口径不变（§413 第二节表格仍成立）；仍未真机、未启动任何被测对象。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    LEDGER.write_bytes(after)
    print("appended %d bytes; total %d -> %d"
          % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
