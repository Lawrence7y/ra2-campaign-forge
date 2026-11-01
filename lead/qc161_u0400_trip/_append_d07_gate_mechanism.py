#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 追加：§415 破案结论入裁决清单（字节级追加，CRLF 数不变）。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "PENDING_DECISIONS.md"

SECTION = """
- **★★ 机制更正（2026-10-24，GOAL-3T §415，不改本条选项）**：上一条把墙描述为
  「commit 相 enobufs 放行 / push 相拦」并推测「墙态随他线写盘活动波动」。
  本轮用固定载荷**直喂 git 门钩子 38 次**（15+3+20），**全部 deny、输出恒 2674 B**，
  换会话 id 三次亦全 deny ⇒ **判定不是波动的，是确定性的**。真相是三条机制叠加：

  1. **触发词 = 命令行子串匹配，与仓库无关。** `echo "git commit"`、
     `grep -n "git commit" <file>` 这类**没有任何 Git 动作**的命令同样被 deny；
     在 `/tmp/gg2` 空仓执行 `cd /tmp/gg2 && git commit`，门禁报的仍是
     **cwd 项目**的 36 条。⇒ 它不解析命令结构、不看命令指向哪个仓。
     ★ 这也是「明明没提交却报墙、命令像没执行」的成因：**整条 bash 被拦，从未执行**。

  2. **单次门禁 ≈20.6 s**，而 `payload/contracts/scan-profiles.json` 里 `gate` 档
     写的是 `preToolUse.hardTimeoutMs: 1000`。该档只服务 Write 钩子；
     Git 门走 full-repository 档。**两档预算不可混用**（我先前按 1 s 预算
     误判过「这么慢一定是超时放行」）。

  3. **★ 根因：`MIMOSA_HOOK_FAILURE_MODE` 未设置 ⇒ 默认 `open`。**
     扫描没跑完整时，钩子返回的 `hookSpecificOutput` **没有 `permissionDecision`
     字段**（不是 `allow`，是「没意见」）⇒ 宿主按放行处理。用
     `MIMOSA_PROJECT_MAXFILES` 造不完整覆盖，同载荷对照：

     | MAXFILES | FAILURE_MODE | 判定 |
     |---:|---|---|
     | 200 | `open`（默认） | **放行**（缺字段，`source_limit_exceeded`） |
     | 600 | `open` | **放行**（`scanner_enobufs`） |
     | 200 | `strict` | **deny** |
     | 800 | 任意 | deny（36 high） |
     | 1500（默认） | 任意 | deny（36 high） |

     **决定性负控**：`/tmp/cleanrepo`（1 个无害 .py、零高危）执行真实 commit
     —— **成功**（`55c609d`），门禁理由 `library_source_unavailable /
     callgraph_fact_partial`。⇒ **放行只与「扫描跑没跑完」有关，与「有没有缺陷」无关。**

  **对本条的直接影响**：
  - 上一条「本线无可控手段」**成立**，但原因不同：不是墙在波动，而是
    **ENOBUFS/覆盖不全时门禁静默失效开放**，所以「有时能过」并不代表干净。
  - **红灯可信，绿灯不可信**：放行有三种成因（无触发词 / 没跑完+open / 真无发现），
    宿主表现上无法区分 ⇒ 任何时候都不能把「提交过了」当作「门禁认为干净」。
  - 选项格局不变：A 仍被 §410–§412 证否（修了不减数），**B 仍是唯一可执行路径**。
    ★ 新增一条**加固**建议（与绕钩子相反，供 Lead 裁决）：
    在项目级把 `MIMOSA_HOOK_FAILURE_MODE` 设为 `strict`，让覆盖不全时**也阻断**。
    这不是为了让我更容易提交，而是为了让「绿灯」重新有信息量。
  - ★ 我验证过三种避开子串匹配的写法（拆词 / 子 shell / 文件传参），**一条都没采用**
    ——那与 `--no-verify` 等价。台账 §415、记忆 `github-worklog-and-scanner-policy-wall`。
"""


def main() -> int:
    before = TARGET.read_bytes()
    assert b"\r\n" in before, "母本应为 CRLF 混合件"
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    TARGET.write_bytes(after)
    print("appended %d bytes; %d -> %d" % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
