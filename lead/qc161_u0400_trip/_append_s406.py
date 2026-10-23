#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§406 追加器：字节级追加，不动既有 86 行 CRLF。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """
---

# §406 H-5 死因：WER 与事件日志**两条通道都零命中**（把「本轮未做」变成「做了，没有」）

**轮次目标**：H-5 死因。§401 与 §402 两处都写「要区分需 WER `AppCrash` 记录或退出时刻
dump——**本轮未做**」。本轮把它做完。

## 一、先解决「查询能不能看见东西」这个问题

「零命中」有两种解释：进程真没崩，或者普查器是瞎的。**不先排除后者，结论一文不值。**

第一版对照判据写成「窗口内必须命中别的进程的 WER 记录」→ **FAIL**。
根因不是查询失败，而是判据选错：WER 只在崩溃时落记录，
10:00–10:50 四趟都跑得好好的，**本来就不该有**任何进程的 AppCrash。
⇒ 把「WER 窗口非空」当可见性对照是**错误需求**。

改成**两条**正确的可见性对照：

1. WER 侧：归档**全量**非空（31 条历史记录可读）——证明解析器活着；
2. 事件日志侧：同窗口**不限 Id** 查到的 Application 事件数 > 0。

第 2 条实测 **15 条**（Id 分布 `{0:7, 16384:2, 16394:2, 256:1, 15:1, 8224:1, 8231:1}`）
⇒ **查询通道活着，且这 15 条里一条 1000/1001/1002 都没有**。
这才是「零命中」该有的形态：**有别的信号，就是没有崩溃信号**。

## 二、★ 变异自检：证明这套普查**抓得到**崩溃

光说「我查了，没有」还是自证。所以做一次**窗口变异**（不改代码，改被查询的时间段）：

```
窗口挪到 2026-10-23 13:50–14:00（该时段确有崩溃）
  → WER 命中 1 条：AppCrash_bt-battery-bar.e_afcd8c8...  app=bt-battery-bar.exe  @13:56:33
  → 事件日志命中 2 条：id=1000 bt-battery-bar.exe @13:56:30 / id=1001 @13:56:33
  [PASS] 变异窗口内 WER 有 AppCrash
  [PASS] 变异窗口内事件日志有 1000/1001/1002
  RESULT: 变异可被抓住
```

同一个脚本、同一套解析、同一条判据，换个时间段就能抓到崩溃
⇒ 四趟窗口的零命中**可以采信**。

## 三、四趟窗口的实测结果

四趟 `measure_w0.json` 的 `t_abs0`（绝对时刻）给出了精确时间轴，
这是此前 §401 夹逼时没用上的字段：

| 趟 | `t_abs0`（本地时） | verdict | RPM |
|:--|:--|:--|:--|
| `l1_20261023` | 2026-10-23 **10:04:19** | `no_advance` | 正常 |
| `l1_20261023b` | 2026-10-23 **10:16:28** | `no_advance` | 正常 |
| `l3_20261023` | 2026-10-23 **10:26:44** | `no_advance` | 失败 2001 次 |
| `l1_20261023c` | 2026-10-23 **10:43:17** | `no_advance` | 失败 2000 次 |

查询窗取 `10:00:00–10:50:00`（覆盖四趟全程 + 余量）：

| 通道 | 结果 |
|:--|:--|
| WER `ReportArchive` + `ReportQueue` 全时段 | 31 条，游戏进程相关 **1** 条 |
| 其中 AppCrash | **0** |
| 其中 AppHang | 1（`gamemd.exe` @**2026-10-24 01:49**，**空目录**，只有元数据无 `Report.wer`） |
| 窗口 10:00–10:50 内 gamemd 记录 | **0** |
| 窗口 10:00–10:50 内事件 1000/1001/1002 | **0**（同窗口总事件 15 条，对照成立） |

★ 那条 `AppHang_gamemd.exe` 目录的 mtime 是 **10-24 01:49**，比四趟晚 15 小时，
且 `files=[]`（空目录）。**与 H-5 无关**，顺带排除。

## 四、这确实收窄了 H-5，但不是定谳

**新增的两条否证**（方向一致）：

| 被排除的解释 | 依据 |
|:--|:--|
| 被 `TerminateProcess` 时序打死 | §402：`wait_returncode=0` 是进程自己的退出码，不是 `terminate()` 的常量 1 |
| **未处理异常 ⇒ WER 上报 AppCrash** | **本节：窗口内 WER 0 条、事件 1000/1001/1002 全 0** |

**剩余可能**（无法用现有产物进一步区分）：

1. 正常退出（`exit(0)` / 主循环返回）；
2. SEH 兜底主动 `ExitProcess(0)` —— 装了兜底的话，异常被吞掉也可给 0；
3. 崩溃上报被系统策略禁用（本机未配 `LocalDumps`，且 WER 可被整体关闭）。

★ **按铁律，「没有上报」≠「没有崩溃」**。本条**不改变** H-5「死因未定谳」的定性，
只是把「本轮未做」变成「做了，两条通道都没有」——**这是一个否证，不是新证据**。

## 五、与 §401 的夹逼关系

§401 给的死亡区间是 **(88.7, 161.0] s**，宽 72.3 s，并说「不能再收」。
本节**不试图收窄它**，理由如下（这也是复核 §401 的结论，不是推翻）：

- 旁路 `Monitor.run` 只存**相对时间**（`t0 = perf_counter()` 取「首次找到进程」那一刻），
  产物里没有绝对锚 ⇒ 与 harness 的 `stage_begin` 无法桥接。
- 本节新用的 `t_abs0` 是 **harness 侧**的绝对时刻，只能给 harness 的时间轴定位，
  **不能**把旁路的 `t=77.16 s` 换算成绝对时刻。
- ⇒ 夹逼宽度**仍然是 72.3 s**，本节没有改变它。

★ 但复核中发现 §401 引用停机机制时的一处**不精确**（不影响区间值）：
`Monitor.run` 的停机条件是 `misses > 400` 且每次失败 `sleep(0.05)`
⇒ 最短 20 s，但它还有 `h` **只打开一次、永不重开**这一层：
一旦句柄随进程死掉失效，后续 `ReadProcessMemory` 全失败 ⇒ 同样是「400 次后 break」。
⇒ 「旁路在 77.16 s 停止采样」**不能**直接读作「进程在 77.16 s 死了」；
它读作「该时刻之后连续 400 次读不到」。§401 的措辞「旁路最后有效样本 = 仍活着」是对的，
但**反向**（「停止采样 = 已死」）不成立。**这是本轮补充的边界，不是更正。**

## 六、验证

`_probe_h5_wer_census.py`：主检 **5/5 PASS** + `--self-mutation` **2/2 PASS**
（窗口变异证明普查抓得到崩溃）。
脚本三次修正如实登记：

| 次数 | 问题 | 修法 |
|:--|:--|:--|
| 1 | 可见性对照写成「窗口内必须有非游戏 WER 记录」⇒ FAIL | 那是**错误需求**：没崩就不该有记录 |
| 2 | 事件日志找不到对照 | 加「不限 Id 查同窗口」= 15 条 |
| 3 | 门禁全绿但没证明能变红 | 加 `--self-mutation` 窗口变异 |

★ 第 3 次是本轮最重要的：**一个从来不会红的门禁，绿得再漂亮也没有信息量。**

## 七、诚实边界

1. 本节只查**本机** WER 与 Application 日志；若崩溃上报被禁用，两者都会静默。
2. `AppHang_gamemd.exe`（10-24 01:49，空目录）**未追查来源**——它与四趟无关，
   但「为什么有个空目录」没解释（可能是 WER 在上报途中被取消）。
3. **没有**用 `DebugActiveProcess` 抓首次异常——那需要真机重跑（H-5 之外）。
4. H-5 的死因**仍然未定谳**。本节把三种可能缩到三种（换了内容：排除了
   「未处理异常 + WER 上报」这条最常见路径），但**没有**把数量减少到一。
5. H-1（harness7 真机三趟）**仍未做**，仍卡在「用户在场」。
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
    assert old_crlf == new_crlf, "CRLF must not change (%d -> %d)" % (old_crlf, new_crlf)
    print("before %d B / lines %d / CRLF %d" % (len(before), before.count(b"\n"), old_crlf))
    print("append %d B" % len(payload))
    print("after  %d B / lines %d / CRLF %d" % (len(after), after.count(b"\n"), new_crlf))
    LEDGER.write_bytes(after)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
