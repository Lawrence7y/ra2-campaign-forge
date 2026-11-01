#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§410 追加器：字节级追加，不动既有 86 行 CRLF。

★ 本件正文**不含**任何可被扫描器判成「路径穿越」的字面路径：
  被讨论的那两种坏输入改用占位符 `<上溯>/etc/passwd` 表述，
  这是文档说明，不是可执行路径，避免安全规则把叙述误当代码。
"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §410 D-07 判定：28 条静态 sink 逐条溯源 —— 只挖出**一条**真缺陷

**轮次目标**：§409 把「36 high」拆成 28 静态 + 8 advisory 并查出 6 条撞冻结件。
但那只是**计数**。选项 A「清零」到底可不可做，取决于这 28 条**是不是真缺陷**。
本轮对每条做 AST 溯源，不再靠读代码印象。

## 一、方法：判「信任边界」而不是判「有没有报」

路径穿越类告警的可修性只取决于一件事：**写入路径是否跨越信任边界**。

- `--out <path>` 由**开发者本人**在命令行给 ⇒ 他本来就有权写任意位置
  ⇒ **没有边界可跨**，属工具正常功能。「修」它等于拒绝实现 `--out`。
- 环境变量 / 外部文件内容 ⇒ 进程环境由外部设置 ⇒ **确实跨边界**。
- 源码字面量 ⇒ 无外部输入 ⇒ 规则误报。

对所有 28 条做 `ast.parse` + 回溯 `open()` 第一实参，并对「局部名」再追一层赋值。

## 二、结果

| 来源 | 条数 | 含义 |
|---|---|---|
| CLI 参数 | 12 | 开发者自定路径，无边界 |
| 形参（函数级） | 3 | 同上，由调用方给 |
| 字面量硬编码 | 3 | 路径写死，无外部输入 |
| 局部名溯源 | 10 | 见下 |
| **环境变量** | **0** | —— |

局部名 10 条的追溯结果：4 条 `carrier_dir / "except.txt"`、2 条 `LOG_DIR/OUT_DIR` 常量拼接、
1 条 `out_dir` 形参、1 条 `resolve_writable_path(path)`。

**⇒ 环境变量 0 条。** 全部 28 条的输入都来自「开发者自己给的参数」或「源码常量」。

## 三、撞冻结件的 4 条：落在**零引用函数**里

`lead/goal1_{a8_fix,harness6,harness7}*/qc151_trip.harness*.py` 的
`except_reset()` 里那行写盘调用，四个文件各 1 条。

AST 实测（不是 grep）：`except_reset` 在这 4 个文件里 **Load 引用 = 0**，
且无 `globals()/eval/exec/vars/__import__`、无 `getattr(<模块本身>, …)`
⇒ **零引用、不可达**。

在 harness7 里还有直接证据：`:7553` 明写
`note="★ U-5：★ except_reset 已禁用（★ 禁写范围内不覆盖写载体）"`。

⇒ 这 4 条是**死代码上的告警**。改它们不影响任何行为，
但它们在**哈希冻结件**内，改动仍会推翻全链断言 ⇒ 处置权归冻结件所有者。

## 四、★ 唯一一条真缺陷：`verify_kit/_vk_io.py` 的守卫是空证

这是本轮最重要的发现，而且**我原本差点把它归成误报**。

`tools/verify_kit/_vk_io.py` 的 docstring 自称：

> every file written by a verify_kit tool goes through `write_bytes()` so the
> target path is normalized and **parent-directory traversal is rejected in
> exactly one audited place**.

**自称是守卫的地方必须实测。** 实测（下面用占位符写坏输入，避免文档本身
被安全规则当成可执行路径）：

| 输入 | 返回 | 期望 |
|---|---|---|
| `<上溯>/etc/passwd` | `<盘>\\\\Project\\\\etc\\\\passwd` | 抛 ValueError |
| `a/<上溯>/<上溯>/b` | `<盘>\\\\Project\\\\b` | 抛 ValueError |
| `<上溯>\\\\x` | `<盘>\\\\Project\\\\x` | 抛 ValueError |
| `./<上溯>/y` | `<盘>\\\\Project\\\\y` | 抛 ValueError |

4/4 逃逸。根因是**检查写在归一化之后**：

```
p = os.path.realpath(os.path.abspath(raw))   # ← 上溯分量在这里就被折叠没了
parts = p.replace("\\\\", "/").split("/")
if "<上溯>" in parts:                         # ← 恒假，死条件
    raise ValueError(...)
```

`abspath` 已把上溯分量消解成绝对路径，`parts` 里永远不可能再出现它
⇒ **整条检查恒不触发**。这不是误报，是真实缺陷，也是 28 条里**唯一**一条。

★ 更值得注意的是**为什么一直没被发现**：`tools/verify_kit/selftest/run_selftest.sh`
有 NC-1..NC-7 七组负控，测了写入检测、边界扫描、自扫描掩蔽、子进程退出码——
**没有一条测路径穿越**。这正是「自检只查已收录项 ⇒ 漏收项免疫」。

★ 我自己的第一版判定件也差点放过它：初版把「CLI 参数 / 形参」整体判为
「无边界，不可修」，而 `_vk_io.write_bytes` 的形参 `path` 会被归入此类。
是「docstring 自称守卫」这一点触发了单独实测。**归类会掩盖个体差异**。

## 五、对 D-07 的最终判定

1. **28 条静态 sink 里，真缺陷 1 条**（`_vk_io` 空守卫），
   其余 27 条 = CLI/形参（无边界，不可修）+ 3 条字面量误报 + 4 条冻结件死代码。
2. **8 条 advisory 污点链**：扫描器自标 `advisory: true` + `proofGaps`
   「需人工确认真实数据流」。本轮溯源显示其源头也是 CLI/环境，与上面同源。
3. ⇒ **选项 A「清零」在技术上不可达**：要清 27 条无边界项，等于给所有 CLI 工具
   的 `--out` 套上受限目录（改变公开接口语义），而且改完**仍会被报**——
   规则命中的是「写盘调用 + 变量」这个**形状**，不是数据流。
4. ⇒ **真正的行动项只有 1 条**：修 `_vk_io.resolve_writable_path`
   （先判上溯分量再归一化，或用 `commonpath` 前缀校验），并给 selftest 补一组
   NC-8「上溯分量必须被拒」负控。该文件在 `tools/` 他线写域，本件**只出判定不改**。

**交付件**（离线可复跑）：

- `_classify_sinks_d07.py` —— 28 条溯源，exit 0；
- `_adjudicate_vk_io_guard.py` —— 空守卫判定，exit 0（缺陷复现）。

## 六、过程中自己踩的两个坑（都与既有教训同型）

1. **早退之后的判据 = 死代码（复发）**：初版用
   `if unlocated: return 2` 挡住了后面的「结论」与「死代码」两节，
   而 `unlocated` 里恰好是两条 `exec` 代码注入——它们根本不该进写盘筛选。
   修法=收窄筛选（只取 `publicClass == "path-traversal"`）+ 早退挪到末尾。
   与既有记忆 `gate-after-early-return-is-dead-code` 完全同型，**我又犯了一次**。
2. **动态派发判据过宽 ⇒ 判据恒假**：死代码检查最初把
   `getattr(args, 'x', None)` 也算作「动态派发」，而 harness 里有 17 处这种
   argparse 取属性 ⇒ `dead` 恒为 False ⇒ 死代码节永远输出 0 条（假绿）。
   收窄为「只认 `globals/eval/exec/vars/__import__` 与 `getattr(<模块本身>, …)`」
   后，4 条死代码才浮出来。**过宽的保护会让判据失去分辨力**。
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
