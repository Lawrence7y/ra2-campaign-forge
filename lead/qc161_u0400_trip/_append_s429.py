#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§429 追加 —— 150 s 双臂终账：开臂不自退（~92s 是调试器假象）+ exitstate 闩 1 定 D-09-A 靶。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """# §429　D-09-B 终账（双臂 150 s / 1480 样本，a8 竞态已修）：开臂**不自退**——
#        ab24 的 ~92 s EXIT_PROCESS 是调试器假象；exitstate 闩 1 = D-09-A 的设计靶

**性质**：真机（10-25 会话，续 §428 双臂首跑后的加窗复跑）。本条**更正 §428-四/update 3**
留下的「自退或>60 s」开放问——答案=**无调试器下开臂根本不自退**。

## 一、双臂 150 s 终态（`_probe_d09b_hang.py --live --watch 150`，击杀轮询修后 a8=PASS）

| 量（1480 样本，wait_failed=0） | MAIN 守卫开·无调试器 | CTRL1 守卫关·无调试器 |
|---|---|---|
| 150 s 内退出？ | **否**（exitcode 恒 None）| **否** |
| exitstate[0xA8EDD8] | 0→**1 后恒 1**（distinct_n=2）| **恒 0**（distinct_n=1）|
| frame | 恒 0 | 恒 0 |
| singleton | →0（同左）| →0 |
| ws | 66,020→**181,488** KB（distinct_n=98，单调爬）| 66,024→**171,368** KB（distinct_n=79，爬）|
| 关窗后新窗口 | **无** | **#32770「Yuri's Revenge」382×163**（错误框等人点 OK）|
| except.txt | **未变** | **变**（→9871e801，写入现场）|

## 二、★ 定论：守卫开臂=「进入退出流程但卡在第 1 步」，且**永不自退**

1. **「~92 s 自行 EXIT_PROCESS」被否**：那是 ab24 **调试器泵事件**上下文特有；
   同配置无调试器 150 s 内 0 退出、0 对话框 ⇒ §428/update 3 的「或不存在/或>60 s」
   收敛为「**无调试器下不存在**」。⇒ 部署不合格从「退出慢」升级为「**静默僵尸，须外部杀**」。
2. **exitstate 0→1 是关键正证**：守卫并非「什么都不做」——它让单例清零后
   退出状态机**确实从 0 进到 1**（开始退出），但**卡在 1**（没走到完成）。
   ⇒ D-09-A 的设计靶精确了：不是「造一个退出」，而是「**让 exitstate 从 1 走到完成**」
   ——守卫跳过的空对象调用里，有**一步是退出推进所必需的**，跳过它使状态机停摆。
3. **关臂对照给出真实世界形态**：守卫关=弹 #32770 错误框+写 except.txt（正是
   历史 except.txt 现场与玩家「关不掉窗口」的成因）；守卫开=连错误框都不弹、
   except 不写 ⇒ **守卫把「可诊断的崩溃」换成了「不可诊断的静默僵尸」**，
   对无人值守 harness 更糟（ab24 早先「except 零新增不代表没崩」这条铁律在此显形）。

## 三、ws 爬升是「挂起态」共性，非守卫特有（别误记）

两臂 ws 都从 66 MB 单调爬到 ~180 MB ⇒ 爬升是**frame=0 但主循环仍在分配**的挂起态特征，
不能算「守卫导致泄漏」。守卫的**独有**差异只有三项：exitstate 1 vs 0、无框 vs 有框、
except 不变 vs 变。**如实分列，不打包成「守卫=泄漏」**。

## 四、卫生

本轮（10-25 全天）发射：Q4c(假abort) / arm F / arm G / MAIN60 / CTRL1-60 / MAIN150 /
CTRL1-150 = 7 次，其中 2 次为 G2 假墙期作废（arm F、Q4c 有效但结论被 G2 推翻）。
母本四哈希全程未变、他线探针件未动、`D:\\ra2dumps` 今日零新增、残留 0、载体全删
（150 s 趟 carrier_deleted 复验通过）。D-09 追加更新 4（自退问题定谳+设计靶精确化）。

"""

D09_UPDATE4 = """- **更新 4（2026-10-25，来源会话，选项不变，自退问定谳）**：双臂 `--watch 150`
  复跑（1480 样本/臂，击杀轮询修后 a8=PASS）⇒ **无调试器开臂 150 s 内不自退**
  （exitcode 恒 None）⇒ §428/update3 的「~92 s 自退」**是调试器泵事件的假象**，
  部署不合格从「退出迟」**升级为「静默僵尸须外部杀」**。
  **正向进展**：exitstate[0xA8EDD8] 观测到 **0→1**（守卫确让退出状态机「开始退出」），
  但卡在 1 ⇒ D-09-A 设计靶精确为「让 exitstate 走完 1→完成」，不是「凭空造退出」。
  关臂对照=弹 #32770 错误框 + 写 except.txt（真实玩家「关不掉窗」成因）；开臂连框都不弹
  ⇒ 守卫把可诊断崩溃换成不可诊断僵尸。ws 两臂同爬（挂起态共性，非守卫特有，不误记）。
"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    assert crlf0 == 86, "CRLF 漂移：%d" % crlf0
    assert before.endswith(b"\n")
    payload = BODY.lstrip("\n").encode("utf-8")
    after = before + payload
    assert after.startswith(before) and after.count(b"\r\n") == crlf0
    TARGET.write_bytes(after)
    print("ledger appended; %d -> %d" % (len(before), len(after)))

    pb = PEND.read_bytes()
    assert pb.count(b"\r\n") == 0
    anchor = "- **提出**：2026-10-24（§426 同轮）".encode("utf-8")
    assert pb.count(anchor) == 1
    upd = D09_UPDATE4.strip().encode("utf-8") + b"\n"
    idx = pb.index(anchor)
    pe = pb[:idx] + upd + pb[idx:]
    assert pe.startswith(pb[:idx]) and pe.count(b"\r\n") == 0
    for tag in ("更新 2（2026-10-24 21:3x", "更新 3（2026-10-25", "更新 4（2026-10-25"):
        assert pe.count(tag.encode()) == 1, tag
    PEND.write_bytes(pe)
    print("D-09 update4 inserted; %d -> %d" % (len(pb), len(pe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
