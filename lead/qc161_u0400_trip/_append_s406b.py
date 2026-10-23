#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§406b 追加：H 系列表的**最新状态**（§399 那张表已陈旧）。字节级追加。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
## 八、H 系列最新状态（★ 覆盖 §399 §七 那张表的两处陈旧行）

§399 §七 的表里 `:15339` 仍写「H-4 **未修**」、`:15340` 仍写「H-5 **死因未定**」。
那两行在本节写作时已过时。**以下为准**：

| 项 | 状态 | 落点 |
|:--|:--|:--|
| H-1 125 s 全屏空等 | 工具已备，**未真机** | D-05 → harness7；需用户在场三趟 |
| H-2 判档器缺窗不可区分 | **已修** | §400 + §401 |
| H-3 采样率口径 | **已量化并关闭** | §399 |
| H-4 `ret` 尺寸依赖窗口边界 | **已修**（§405） | 断言 16→25；7 变异全杀 |
| H-5 C/L3 死因 | **死法已定；死因收窄到 3 项，仍未定谳** | §401 + §402 + **§406** |
| H-6 `wait_returncode` | **已定谳** | §402 |

⇒ 离线可做的 H 系列项**已全部清完**。剩下只有两类：
① H-1 真机三趟（需用户在场/授权）；
② H-5 死因的最后一格（需 `DebugActiveProcess` 抓首次异常，属真机工作）。

**H 系列不再有本线可离线推进的项。** 后续轮次不应再从 H 系列取活。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    payload = SECTION.encode("utf-8")
    if not payload.endswith(b"\n"):
        payload += b"\n"
    after = before + payload
    assert after.startswith(before)
    assert len(after) == len(before) + len(payload)
    assert before.count(b"\r\n") == after.count(b"\r\n")
    print("before %d B / CRLF %d" % (len(before), before.count(b"\r\n")))
    print("append %d B -> after %d B / CRLF %d"
          % (len(payload), len(after), after.count(b"\r\n")))
    LEDGER.write_bytes(after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
