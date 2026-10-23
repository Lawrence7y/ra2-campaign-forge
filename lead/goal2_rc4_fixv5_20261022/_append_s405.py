#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§405 追加器：字节级追加，不动既有 86 行 CRLF。

★ 为什么不用 Edit：台账是混合行尾（15,378 bare-LF + 86 CRLF），
  Edit/Write 会整文件重写并抹掉那 86 行 CRLF（§403 踩过，+171/−86）。
"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
---

# §405 H-4 结题：`ret` 尺寸的窗口边界改成**推导**，并钉住分派表基址

**轮次目标**：清掉 H-4（台账 `:15339` 标「未修」的最后一条离线可做项）。
**依据**：§404 已撤回「H-4 属外部写域」那条自造理由 —— 台账 `:9215` 的写域声明
指的是 §369 真机趟、目录是 `rc4_trigger`，与 `rc4_fixv5` 无关。H-4 可动。

## 一、先纠正 H-4 的**归属**：§398 引的证据不在这个脚本里

§398 §五 把 H-4 写成「`_todo7_creation_trigger.py` 的 ret 尺寸结论依赖窗口边界」，
但举的证据是 `0x6930A0`（0x694000 → 三种尺寸）与 `0x778030`。
实测：**这两个函数都不在 `_todo7_creation_trigger.py` 里算 ret 尺寸** ——
该脚本只扫 `0x7775C0` 找 `ret 0x10`，从不解 `0x6930A0`。

用交付件同款 CFG 方法复算（`_probe_h4_owner.py`）：

| 函数 | 可达 ret 收敛集合 | 不跳窗且稳定的最小窗口 |
|:--|:--|--:|
| `0x6930A0` | `[16]` | **0x400** |
| `0x778030` | `[8]` | **0x100** |

⇒ §398 说的「放到 0x694000 就有三种尺寸」**只在「线性扫全窗口、不跟 CFG」时成立**。
按 CFG 求可达集，0x400 窗口就已是 `[16]` 且不再变。
**这不是说 §398 错了** —— 它描述的正是「线性扫描 + 窗口放宽」这个组合的风险，
只是这个风险落在 `_esp_fullpath.py` / `_esp_bfs.py` 等 5 个脚本上（§396b 已修），
**不是** `_todo7_creation_trigger.py`。

## 二、`_todo7_creation_trigger.py` 的真实缺口：窗口**截断**函数体

`_probe_h4_bound.py` 实测 `0x7775C0` 的真函数体：

```
线性解码 [0x7775C0, 0x777A80)：375 条指令，ret 11 个
  0x777624 / 0x777684 / 0x77778A / 0x777828 / 0x777871 / 0x77789D
  0x77794F / 0x777982 / 0x7779DA / 0x777A61 / 0x777A7A   ← 全部 ret 0x10
末 ret @0x777A7A 止于 0x777A7D，其后 3 字节 8d4900（lea ecx,[ecx] 填充），
紧接分派表 0x777A80
```

原实现 `dis(WNDPROC_HINT, 0x400)` 只到 `0x7779C0`：

| 窗口 | 可见 ret | ret 尺寸集合 |
|:--|--:|:--|
| 0x400（原实现） | **8/11** | `{0x10}` |
| 0x4C0（到表起点） | 11/11 | `{0x10}` |
| 0x500（越过 0x80） | 12 | **`{0, 0x10}`** ← 捡到下一个函数的 `ret 0` |

⇒ 原断言「函数内有 ret 0x10」在 8/11 的情况下也通过，
**既没证明唯一，也没证明窗口选对**。窗口一改结论就变 —— 这就是 H-4。

## 三、修法：上界**从常量推**，不手选

关键观察：分派表 `JT_DWORDS = 0x777A80` **本来就是本脚本的常量**，
而数据表不可能落在函数体内 ⇒ `BODY_END = JT_DWORDS` 是有依据的边界，不是挑出来的。

STEP 2 改为：

| 断言 | 判据 |
|:--|:--|
| ★ 函数体内全部 ret 尺寸唯一 = 0x10 | `body_sizes == {0x10}`，n=11 |
| ★ 函数体内 ret 数 = 11 | 多出口但同尺寸 |
| ★ 末 ret = `ret 0x10 @ 0x777A7A` | 末出口地址 |
| ★ 末 ret 前 4 条 = `pop edi/esi/ebx/ecx` | 与序言 `push` 配平（帧对称） |
| ★ 末 ret 到表起点之间是填充且无分支落入 | `8d4900`，32 个分支目标无一落入 |
| ★★ 负控 窗口越过 0x80 ⇒ 尺寸集合变多值 | `{0, 0x10}` |

**「上界是数据表」这句话此前从未被断言过** —— 常量写错就整段错。
所以 STEP 3 补两条锚：

| 断言 | 实测 |
|:--|:--|
| ★★ 间接跳转基址 = `JT_DWORDS` | `jmp dword ptr [edx*4 + 0x777a80]` @0x7776AE |
| ★★ 字节索引表基址 = `JT_BYTES` | `mov dl, byte ptr [ecx + 0x777a98]` @0x7776A8 |

## 四、★ 顺带修掉 STEP 1b 的**自指**判据（这是本轮真正的意外收获）

跑变异时 M6（入口 `0x7775C0 → 0x7775C1`）**存活**，即整套自检抓不到入口错移。

根因：原实现 `probe_start = WNDPROC_HINT - 16`，**起点跟着入口一起移动**。
入口错移 1 字节后，新起点解出来的边界集合里**照样**含有新入口
（`0x7775C1` 本身就是 `mov ecx,[0x887628]` 的起点）⇒ 判据恒真。

这正是台账反复登记过的「恒真式」形态，只是这次的被测物是**自检本身**。

改法（`_todo7_creation_trigger.py:94` 起）：

1. 解码起点改成**固定常量** `PROBE_ANCHOR = 0x7775B0`，不随入口移动；
2. 追加**独立**判据「入口前 3 字节全是填充」——与解码起点无关：

   ```
   0x7775BD..0x7775C0 = 90 90 90     ← 正确入口
   0x7775BE..0x7775C1 = 90 90 51     ← 错移 1 字节，末字节是 push ecx
   ```
3. 追加负控「入口错移 1 字节 ⇒ 填充判据必须失败」。

## 五、门禁核验：7 个变异全杀（`_verify_h4_gate.py`）

判据不是「rc != 0」（任何一条 FAIL 都让 rc=1，区分不出谁被抓到），而是三元组：
**rc != 0 + 指定断言出现在 FAIL 行 + 未指定的对照断言仍 PASS**。

| 变异 | 目标断言变红 | 对照仍绿 | 判定 |
|:--|:--|:--|:--|
| M1 窗口改回 0x400 | 函数体内 ret 数 = 11 | 创建入口唯一 | **KILLED** |
| M2 窗口越过 0x80 | ret 尺寸唯一 | 创建入口唯一 | **KILLED** |
| M3 `JT_DWORDS` +0xC | 间接跳转基址 | ret 尺寸唯一 | **KILLED** |
| M4 `JT_BYTES` +0x10 | 索引表基址 | 跳转基址 | **KILLED** |
| M5 负控窗口缩回体内 | 负控变多值 | ret 尺寸唯一 | **KILLED** |
| M6 入口错移 1 字节 | **入口前 3 字节全是填充** | 旧值负控 | **KILLED** |
| M7 帧对称改 3 条 pop | 末 ret 前 4 条 | ret 数 = 11 | **KILLED** |

```
变异总 7：KILLED 7 / SURVIVED 0 / SKIP 0
RESULT: ALL MUTATIONS KILLED
```

★ M6 的第一次运行是 **SURVIVED** —— 那一轮如果只报「6/7 KILLED」就收工，
STEP 1b 的自指缺陷会原样留在盘上。**变异存活不是要修补的地方，是要改判据的地方**。

## 六、重钉与产物

- `_todo7_creation_trigger.py`：**16 → 25 条断言，25/25 ALL PASS**，EXIT=0。
- `TODO7_CREATION_TRIGGER.txt`：7,807 B → **9,258 B**，CRLF **141 → 162**（全 CRLF，未混行尾）。
- 逐行 diff：162 行里**新增 21 行、改 2 行、其余逐字节相同**（见下）。
  - 改 2 行：`WNDPROC_HINT 是已知指令边界`（补「从固定锚点起解码」）、`checks passed: 16/16 → 25/25`。
  - 新增 21 行：11 条 ret 清单 + 7 条新断言 + 2 条基址锚 + 「末 ret/填充」说明行。
- 交付件**无 CRLF 污染**、无回滚、无删除行。

## 七、诚实边界

1. **`ret 0x10` 这个结论本身没变** —— 改前改后都是 `0x10`。
   本轮改的是「**为什么对**」：原来靠「窗口里有」，现在靠「函数体内 11/11 全同尺寸
   + 边界由数据表常量推出 + 帧对称 + 填充无分支落入」。
   ⇒ **本轮不改变任何下游结论**，只让结论不再依赖一个手选的窗口。
2. **`WM_SHOWWINDOW` 语义仍未从引擎侧证实**（§404 §五 第 2 条的边界未变）。
3. **`BODY_END = JT_DWORDS` 的前提是「表紧贴函数体」**。实测 `0x777A7D..0x777A80`
   只有 3 字节 `8d4900` 填充，但如果哪天换二进制、表前插了大段对齐填充，
   这条推导仍成立（填充也算体内？——不，填充在末 ret 之后，不影响 ret 计数），
   但「末 ret 到表起点之间是填充」这条断言会把它暴露。**没有留下静默空间。**
4. **H-4 之外仍未修**：H-1（harness7 差真机三趟）、H-5（C/L3 死因缺 WER/dump）。
5. **Mimosa 在 commit/push 时仍报 `scanner_enobufs`** ⇒ 本轮同样没拿到完整安全扫描结论。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    payload = SECTION.encode("utf-8")
    if not payload.endswith(b"\n"):
        payload += b"\n"
    after = before + payload
    assert after.startswith(before), "append must preserve prefix"
    assert len(after) == len(before) + len(payload), "size arithmetic"
    old_crlf = before.count(b"\r\n")
    new_crlf = after.count(b"\r\n")
    assert old_crlf == new_crlf, "CRLF count must not change (%d -> %d)" % (old_crlf, new_crlf)
    print("before %d B / lines %d / CRLF %d" % (len(before), before.count(b"\n"), old_crlf))
    print("append %d B" % len(payload))
    print("after  %d B / lines %d / CRLF %d" % (len(after), after.count(b"\n"), new_crlf))
    LEDGER.write_bytes(after)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
