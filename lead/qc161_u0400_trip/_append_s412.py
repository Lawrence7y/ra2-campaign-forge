#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§412 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §412 全仓同类普查：从「17 处」缩到「1 处」，全程都是判据在变

**轮次目标**：§410–§411 在 `verify_kit/_vk_io.py` 确认了「先归一化、后判上溯分量
⇒ 恒假死条件」这一缺陷。按既有纪律 **修一处必须全仓搜同类**，
否则只是修了当场文件。本轮做这次普查。

## 一、结果

全仓（git 跟踪的 388 个 `.py`）**同类真缺陷 = 1 处**，就是已确认的 `_vk_io.py`。
它**是孤例**。

但这个「1」是在判据改了三轮之后才得到的。三轮的数字分别是
**0 → 17 → 2（含阳性对照）→ 剔除本线 1**。过程比结论更值得记。

## 二、判据三轮演进（每轮都是「数字变了，但我没改被测物」）

### 第 1 轮：0 条 —— 假绿

初版只查「校验语句里的变量 == 归一化赋值的目标变量」。`_vk_io` 的形态是：

```
p = realpath(abspath(raw))        ← 归一化目标是 p
parts = p.replace(...).split()    ← 实际被校验的是 parts
if "<上溯>" in parts:              ← 校验的是 parts，不是 p
```

只看「同一变量」⇒ 漏掉 `parts` ⇒ **连已知样本都抓不到**，
输出「0 条 → 孤例」的**假绿**。

★ 这正是既有教训的形状：**没有阳性对照的「零发现」没有信息量**。
若当时直接交付「全仓无同类」，就是把判据失效说成了事实。

### 第 2 轮：17 处 —— 判据落在「形状」上，全是噪声

补了**一跳污点传播**（归一化目标派生出的变量也标记），`_vk_io` 被抓到，
阳性对照成立。但同时冒出 17 处，其中：

- **8 处**是四个 harness 的 `check_carrier_boundary()`；
- `tools/extract_mix.py` 的 `startswith(PROJECT_ROOT)`；
- `re_atlas/tools/verify_r0{21,24}_claims.py` 等。

逐条看源码后确认：**这 16 处几乎全是误报**。因为我把两种性质相反的检查混为一谈：

| 检查语义 | 归一化之后做它 | 性质 |
|---|---|---|
| 「上溯**分量**是否还在」 | 分量已被折叠 ⇒ 恒假 | **缺陷** |
| 「结果是否**仍在基目录内**」 | 先归一化再比前缀 = 标准正确写法 | **安全** |

`extract_mix.py` 用 `startswith` 前缀法，我**实测**过它能拦住
`<工程根>/<上溯>/evil` → resolve 后为 `<盘>/Project/evil`，不在前缀内 ⇒ 拦住。
`check_carrier_boundary` 更是先 `_norm_path` 再判 `is_descendant`，顺序完全正确。

⇒ 判据必须落在**检查的语义**上，不能落在「含 `..` 或含 startswith」这个**文本形状**上。

### 第 3 轮：2 处 —— 语义分类后收敛

按语义分流（`DEAD` / `VALID`）后：`_vk_io.py` 1 处 + **本线自己的判定件**
`_adjudicate_vk_io_guard.py` 1 处（它故意内含坏例，属自我描述）。

剔除本线判定件 ⇒ **他线真缺陷 0 处**，`_vk_io.py` 确认孤例。

## 三、为什么这一轮的「1」可信

因为同时具备两个条件，缺一不可：

1. **阳性对照**：判据必须能抓到已知样本 `_vk_io.py`。件内已把它写成硬断言
   （抓不到就 `return 1`），杜绝上一轮那种假绿。
2. **逐个定性**：17 处不是直接当结论，而是逐条读源码 + 对 `extract_mix`
   做**实测**（构造逃逸路径看是否真被拦住）。分类表是本轮的主要产出。

## 四、交付件

| 件 | 作用 | 结果 |
|---|---|---|
| `_census_normalize_then_check.py` | 全仓同类普查（含阳性对照硬断言） | exit 0，真缺陷 1 处 |

## 五、连带教训

- **「17 处」与「1 处」之间没有改过任何被测文件**，只有判据在变。
  报数之前先问：这个数字是「被测物的属性」还是「我判据的属性」。
- **误报的代价不是噪声，是掩盖**：17 处里 16 处噪声把唯一的真缺陷挤成了
  1/17，读者无法分辨。**过宽的判据会让真信号失去分辨力**——
  这与 §410 死代码那节的「`getattr(args,..)` 误判致判据恒假」是同一族的两个方向。
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
