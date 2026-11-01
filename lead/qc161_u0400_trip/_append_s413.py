#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§413 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §413 H-1 三趟编排器：把「散文」变成可复跑的命令

**轮次目标**：§407/§408 修完了「证据能不能被读出来」（判档端）与
「趟能不能发出来」（发射端）。本轮补最后一段：**三趟的命令本身**。

## 一、缺口在哪

S399 §九 把真机三趟写成了**散文**：

> 1. 窗口模式一轮：**不传 `--fullscreen`** …
> 2. 全屏短路一轮：`--fullscreen`（缺省短路）…
> 3. 对照臂一轮：`--fullscreen --h7-keep-rect-wait` …

而 `_launch_l1_20261023.py` **没有 dry-run** —— 它一路走到 `os.spawnv`。
后果在真机时段才暴露：

- 三趟参数各不相同（全屏开关 / harness 哈希 / 附加参数），靠手敲；
- 每趟跑掉 2–3 分钟（全屏臂 ~125 s 帧阶段），敲错一次废一趟；
- ★ **敲错不会报错**——参数都合法，只是跑成了别的那趟。
  第 2 趟误加 keep 开关，短路的收益就测不到，而输出看起来「一切正常」。

## 二、修法：只打印，不启动

`_trip_plan_h1.py` 输出三趟完整命令 + 自检，**不建目录、不启动进程**。

★ 关键设计：**不自己拼 argv**，而是 import 发射器的 `build_harness_argv()`
纯函数来自行生成。这样「编排器打印的命令」与「发射器实际发射的命令」
在**构造上**必然一致。若两处各写一份，漂移只会在真机时段暴露。

三趟（suffix 互不相同，防 out-dir/trip-id 覆盖）：

| 趟 | suffix | 全屏 | harness | 附加参数 |
|---|---|---|---|---|
| 1 窗口模式 | `h7a` | **否** | harness7 | — |
| 2 全屏短路 | `h7b` | 是 | harness7 | — |
| 3 对照臂 | `h7c` | 是 | harness7 | `--h7-keep-rect-wait` |

## 三、自检 17/17

C1 suffix 互异 / C2 out-dir 互异 / C3a 第 1 趟不含全屏 / C3b 第 2、3 趟含全屏 /
C4a 第 3 趟恰一次 keep / C4b 第 1、2 趟不带 keep / C5 三趟都是 harness7 /
C6 trip-id 与 suffix 一一对应 / **C7 重建 argv 与发射器纯函数逐字一致（无漂移）** /
C8 载体附加件恰 83 件 / C9 本件不含进程启动调用。

## 四、负控 8/8：五个变异全被捕获

| 变异 | 对应的真实事故 | 命中的判据 |
|---|---|---|
| M1 suffix 撞车 | out-dir 覆盖前一趟证据 | C1 + C2 |
| M2 第 1 趟忘关全屏 | 发成第 2 趟，窗口证据永远缺 | C3a |
| M3 第 2 趟误加 keep | 短路臂变对照臂，核心收益测不到 | C4b |
| M4 第 3 趟漏掉 keep | 对照臂变短路臂，A/B 对照消失 | C4a |
| M5 第 2 趟用 harness6 | 用缺补丁的件跑「补丁验证」 | C5 |

## 五、过程中两个自己踩的判据坑

1. **C9 曾恒假（自指）**：初版把禁用词写成字面量列表再 `in me`，
   而**词就写在文件里** ⇒ 必然命中 ⇒ 恒红。
   改成「运行时拼接禁用名 + 扫本件 **AST 调用节点**（不认字符串/注释）」后转绿。
   与 `gate-assert-values-not-existence` 的恒真式同型，方向相反（恒假）。
2. **负控装置本身失效**：首版把编排器原样搬进 `<tmp>/lead/qc161_u0400_trip/`，
   而它用 `Path(__file__).parents[2]` 推仓库根 ⇒ 推出来是 **Temp 目录**
   ⇒ 发射器导入不到 ⇒ **8 条全红但红项为空**。
   修法=注入一行把 ROOT 钉回真仓库根。
   ★ 症状（全红、无细节）本该立刻怀疑「装置没跑起来」，而不是「被测件有 5 个缺陷」。

## 六、交付件

| 件 | 作用 | 结果 |
|---|---|---|
| `_trip_plan_h1.py` | 三趟命令编排（只打印） | **17/17** |
| `_verify_trip_plan_h1.py` | 负控 | **8/8，5 变异全捕获** |

★ 未真机、未启动任何进程。真机时段只需复制粘贴这三条命令。
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
