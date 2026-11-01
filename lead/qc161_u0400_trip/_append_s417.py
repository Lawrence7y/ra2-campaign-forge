#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§417 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §417 三趟命令一粘贴就废 —— 反斜杠路径裸奔，规划器与 bash 的边界从没验过

**轮次目标**：§413 的规划器自检 19 项、§416 的判档器预演 8/8，两件都绿。
但**两件都只验了「值对不对」，没验「命令到了 shell 还对不对」**。
本轮把生成的命令**真的交给 bash 分词**，当场炸出一个会让三趟全线报废的缺陷。

## 一、缺陷：`quote()` 只在含空白时加引号

原实现：

```python
def quote(a: str) -> str:
    return '"%s"' % a if (" " in a or "\\t" in a) else a
```

而本项目的 argv 里全是 **Windows 反斜杠路径**（`D:\\Project\\...`），
**一个空格都没有** ⇒ `quote()` 判定「不需要引号」⇒ **全部裸奔**。

在 Git Bash 里反斜杠是转义符，实测（`_probe_bs.sh`）：

```
$ echo D:\\Project\\ra2-campaign-forge\\lead\\x.py
D:Projectra2-campaign-forgeleadx.py          ← 反斜杠全被吃掉

$ echo "D:\\Project\\ra2-campaign-forge\\lead\\x.py"
D:\\Project\\ra2-campaign-forge\\lead\\x.py    ← 加引号后完好
```

→ 规划器打印的三条命令，**照抄粘贴进 Bash 后每一条都会因路径不存在而立刻失败**。

## 二、为什么两套自检都没抓住

| 自检 | 它验的是 | 为什么漏 |
|---|---|---|
| C7 | 重建 argv 与发射器纯函数**逐字一致** | 验的是 **list 层**，`quote()` 在 list 之后才介入 |
| C8 | `--carrier-create-files` 恰 83 件 | 同上，数的是 list 里的元素 |
| C9/C10 | 不启动被测对象 / `--json` 纯净 | 与命令文本无关 |
| §416 预演 | 判档器能否正确**判型** | 完全在 `_judge_*.py` 侧，不碰命令文本 |

★ **规划器的 C7 是「list 到 list」的比对，`cmd` 字符串从未被任何判据检查过。**
这正是「验零件 ≠ 验装配」：零件（argv 列表）全对，装配（拼成 shell 命令）全错，
而**没有任何一条自检跨过这条边界**。

## 三、修法与门禁

修复（`quote()` 一律加引号，并转义内部双引号）：

```python
def quote(a: str) -> str:
    return '"%s"' % a.replace('"', '\\\\"')
```

新增两条自检：

| 项 | 判据 | 结果 |
|---|---|---|
| **C11** | `shlex.split(cmd, posix=True)[1:]` 必须**逐字等于** `argv` | ✓ 3 趟全成立 |
| **C11b** | **阳性对照**：把 `quote()` 换回旧实现，同一条分词**必须失真** | ✓ 旧式得 `D:Projectra2-campaign-forgeleadgoal1_harness7_20261023qc151_trip.harness7.py` |

★ C11 的判据**不能**写成「命令里有没有引号」—— 那对「只有一部分参数被引」不敏感，
方向不对。必须写成「分词后与原 argv 逐字相等」才有区分力。
★ C11b 是 C11 的负控：没有它，C11 只证明「恰好都对」，不证明「抓得住旧缺陷」。

负控验证器同步加 **M6**（把 `quote()` 退回旧实现）⇒ C11 变红。
`_verify_trip_plan_h1.py` 从 8/8 升到 **9/9**。

## 四、最终验收：交给真 bash

不只依赖 shlex 这个「尺子」，另用**真 bash** 跑一遍（把 `python` 换成 `echo`，
看 bash 实际收到什么），逐趟比对首尾参数：

| 趟 | bash rc | 首参数完好 | 末参数完好 |
|---|---:|---|---|
| h7a | 0 | ✓ | ✓ |
| h7b | 0 | ✓ | ✓ |
| h7c | 0 | ✓ | ✓ |

★ 这是**双向闭合**：`shlex`（判据用的尺子）与真 bash（被测环境的实现）给出同一结论。
若只用 shlex，我会担心「尺子自己错了」；若只用 bash，我无法把判据写成断言。
两者都用，才同时具备**可判**与**可信**。

## 五、顺带核到的两件事（都没问题，记录以免重复怀疑）

1. **规划器用的每个 flag 都在 harness7 的 argparse 里**：AST 抽 `add_argument`
   得 20 个选项，三趟用到的 10/11/12 个 flag **全部命中，零未知**。
2. **发射器与规划器的引号规则本来就不同，但都正确**：
   发射器走 `os.spawnv(os.P_WAIT, sys.executable, spawn_argv)`，**不过 shell**，
   它那套 `'"%s"' % a if (" " in a and not a.startswith('"'))` 只影响打印美观；
   规划器产出的是**给人复制粘贴的命令文本**，必须过 shell ⇒ 必须真加引号。
   ★ 两者不是「同一件事写了两份」，而是**两个不同用途**，不能强行统一。

## 六、交付件

| 件 | 改动 | 结果 |
|---|---|---|
| `_trip_plan_h1.py` | `quote()` 一律加引号 + C11/C11b | **21/21**（原 19） |
| `_verify_trip_plan_h1.py` | 新增 M6 变异 | **9/9**（原 8） |
| `_probe_bs.sh` / `_probe_shlex.py` / `_probe_bash_roundtrip.py` | 取证与验收 | 见上 |

★ 本轮**不改** harness、**不改**判档器、**不碰**任何既有趟产物。
修的是「交付给用户的命令文本」，这正是真机时段唯一会被执行的东西。
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
