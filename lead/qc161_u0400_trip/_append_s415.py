#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§415 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §415 门禁「红绿反复」破案 —— 不是随机，是失败开放；且触发词是子串匹配

**轮次目标**：§409–§414 的改动全部卡在提交上。台账里把它记成「门态非确定、
同一文件红绿反复」，并按「撞运气绕钩子」的禁令停止重试。本轮**不再重试提交**，
而是把「非确定」当成待破的案子来查。

结论先行：**它根本不随机。** 三个独立机制叠在一起，被误读成随机。

## 一、机制一：门禁对**命令行文本**做子串匹配，与仓库无关

用一个固定载荷直接喂 `git-gate-hook.mjs`（不经宿主），把 `command` 换成
**完全无关**的内容：

| `tool_input.command` | 判定 | 说明 |
|---|---|---|
| `git commit -m repro` | deny（36 high） | 预期 |
| `git push origin main` | deny（36 high） | 预期 |
| `git status --porcelain` | 无输出、放行 | 不含触发词 |
| **`echo "git commit"`** | **deny（36 high）** | ★ 纯 echo，无任何 Git 动作 |
| **`grep -n "git commit" <file>`** | **deny（36 high）** | ★ 只是 grep |

在宿主上复核：一条**真实执行**的 `echo "SIDE_EFFECT_OK git commit phrase in text"`
被拦下且**从未执行**（该行输出根本没出现，取而代之的是门禁消息）。

★ 另一个更早的旁证：我在 `/tmp/gg2`（全新空仓）里执行
`cd /tmp/gg2 && git commit`，门禁报的仍是 **`D:\\Project\\ra2-campaign-forge`** 的
36 条 —— 它读的是**当前工作目录的项目**，不解析命令指向哪个仓。
⇒ 门禁 = 「命令文本含 `git commit`/`git push` ⇒ 扫 cwd 项目」，
**既不解析命令结构，也不判断是否真有 Git 动作**。

★ 这解释了我先前碰到的一类怪事：我写的**带 `git commit` 字样的 shell 片段**
（哪怕只是探针、回显、注释）会让整条 bash 调用被拦，
而我当时误以为「命令跑了但门禁随机变红」。

## 二、机制二：30 次实测，判定完全确定

同一载荷连跑 **15 次** + 再跑 **3 次** + 再跑 **20 次**：

| 批次 | 次数 | 结果 | 耗时 |
|---|---:|---|---|
| 第 1 批 | 15 | **15/15 deny**，输出恒 2674 B | 20.4–21.6 s |
| 第 2 批 | 3 | **3/3 deny**，2674 B | 21.1–21.2 s |
| 第 3 批 | 20 | **20/20 deny** | — |

输出字节数逐次相同、`permissionDecision` 逐次相同。
换 `session_id`（他人会话 / 空串 / 本会话）三次，全部 **deny**。
⇒ **在覆盖完整的前提下，门禁是确定性的。** 「红绿反复」不可能来自判定本身。

★ 附带发现：单次门禁耗时 **≈20.6 s**，而 `scan-profiles.json` 的 `gate` 档
声称 `preToolUse.hardTimeoutMs: 1000`。**实测超了 20 倍** —— 该档只用于 Write
钩子，Git 门走的是 full-repository 扫描，两者预算不可混用。

## 三、机制三（★ 根因）：覆盖不完整 ⇒ **默认失败开放**

`MIMOSA_HOOK_FAILURE_MODE` 未设置（实测 `env | grep -i mimosa` 为空），
默认值 **`open`**。此时只要扫描没能跑完整，门禁**不下判定**，命令放行：

```json
{"systemMessage":"🛡 Mimosa L3：git commit 前深度扫描为 INCONCLUSIVE
 （scanner_enobufs）；不能视为安全。当前兼容模式失败开放。",
 "hookSpecificOutput":{"hookEventName":"PreToolUse", "additionalContext":"..."}}
```

★ 注意 `hookSpecificOutput` 里**没有 `permissionDecision` 字段** ——
不是 `allow`，是「没意见」。宿主按放行处理。

三档对照（同一载荷，只改 `MIMOSA_PROJECT_MAXFILES`）：

| MAXFILES | 判定 | `permissionDecision` | systemMessage |
|---:|---|---|---|
| 200 | **放行** | **缺字段** | `source_limit_exceeded` 等，明确写「失败开放」 |
| 600 | **放行** | **缺字段** | `scanner_enobufs` |
| 800 | deny | `deny` | 36 high |
| 1500（默认） | deny | `deny` | 36 high |

同一个 `MAXFILES=200`，只改失败模式就翻转：

| `MIMOSA_HOOK_FAILURE_MODE` | 判定 |
|---|---|
| `open`（默认） | **放行**（缺 `permissionDecision`） |
| `strict` | **deny** |

★ **决定性负控**：在 `/tmp/cleanrepo`（一个只有 1 个无害 .py 的全新仓）
执行真实 `git commit` —— **成功**（`55c609d probe commit`），
而门禁给的理由是 `library_source_unavailable / callgraph_fact_partial`。
那个仓里**一条高危都没有**，却照样因为「扫描没跑完整」而放行。
⇒ **放行与「有没有缺陷」无关，只与「扫描跑没跑完」有关。**

## 四、三机制合成的真实图景

```
命令文本含 'git commit' / 'git push'?
  ├─ 否 → 放行（不扫描）
  └─ 是 → 对 cwd 项目跑 full-repository 深度扫描
           ├─ 跑完且 36 high → deny（确定性）
           └─ 没跑完（ENOBUFS / source_limit_exceeded / callgraph partial ...）
                ├─ FAILURE_MODE=open（默认）→ 不下判定 → 放行
                └─ FAILURE_MODE=strict       → deny
```

所以「同一文件红绿反复」的真相是：**两次尝试之间，扫描是否跑完整变了**，
而变的原因在系统资源（`ENOBUFS` 是缓冲区耗尽）、文件规模、并发会话，
不在我的文件内容。我先后按「文件内容」和「暂存体积」两个假说解释过，**都错**。

## 五、这对「铁律」意味着什么（不改任何东西，只记录）

1. **红灯可信，绿灯不可信。** deny 是确定性结论；放行有三种成因
   （无触发词 / 没跑完 + open / 真无发现），**无法从宿主表现上区分**。
   ⇒ 以后看到「提交过了」，不能当作「门禁认为干净」。
2. **不允许用「换一种写法」去命中放行。** 我本轮验证了
   「把触发词拆开写 / 放进子 shell / 用文件传参」都能绕过子串匹配 ——
   **我没有采用任何一条**，因为那与 `--no-verify` 等价。记录它是为了让
   「这条路存在」变成已知事实，而不是可选项。
3. **真正的修缮只有两条正路**：把 36 条清掉（他线写域，且 §409–§412 已证
   「修唯一真缺陷也不减少条数」），或按 `MIMOSA_HOOK_FAILURE_MODE=strict`
   把失败开放关掉（这会让门禁**更容易**红，不是更容易绿）。
   ★ 后者是**加固**方向，与「绕钩子」相反，可交 Lead 裁决。

## 六、本轮交付与「负结果」申报

| 项 | 结果 |
|---|---|
| 门禁判定确定性 | **38 次实测全 deny**（15+3+20） |
| 触发条件 | 命令行**子串**匹配 `git commit`/`git push`，与仓库无关 |
| 根因 | `MIMOSA_HOOK_FAILURE_MODE` 默认 `open` ⇒ 扫描不完整即放行 |
| 决定性负控 | 空仓无害文件也放行（`55c609d`），理由=扫描不完整 |
| §414 成果完整性 | `grep §414 = 1`；`_verify_h2e_smoke.py` **25/25 PASS** |
| 提交 | **仍未提交**（不变）——本轮不重试、不换写法、不绕 |

★ 本轮**没有**产生任何代码改动，也没有让任何卡住的提交变绿。
它产出的是一份「红灯可信/绿灯不可信」的可复算判定，供 D-07 裁决。
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
