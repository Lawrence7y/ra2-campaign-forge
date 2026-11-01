#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§427 追加 —— d09b：无调试器路全天 9 连败（窗口从未出现）+ 我污染源被他们门禁抓住 + D-09 补正。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """# §427　d09b 发射日终账：无调试器路 9 连败零窗口；两笔必须记的账（D-09 补正 + 我的污染被门禁抓）

**性质**：真机时段（授权内）。承接 D-09 选项 B（`_probe_d09b_hang.py` 双臂 +
`_diag_d09b_launch/split.py` 三问）。结论先行：**D-09-B 的主臂今天发射不出来**，
原因与守卫无关；另更正 §426/D-09 一处过强表述；并如实登记我自己的写域事故。

## 一、无调试器路 9 次发射，窗口出现次数 = 0（全配置、全修复组合）

| # | 配置 | 结果 |
|--:|---|---|
| 1 | MAIN：rc4_loader+守卫(=1)，无调试器 | gamemd 活着，40 s 零窗口 ⇒ abort |
| 2 | CTRL1：同上(=0) | 同形 |
| 3 | Q1：裸启 gamemd.exe（ab24 A 路去调试器）| 45 s 零窗口 |
| 4 | Q2：Q1 复跑 | 45 s 零窗口 |
| 5 | Q3：20 s 时中途挂调试器泵 3 s | 无窗口（且我中途 detach ⇒ 设计缺陷，作废）|
| 6 | Q4：裸启 + **修复 ddraw.ini 注释行**（`\\x01false`→`windowed=false`）| 60 s 零窗口 |
| 7 | Q4b：裸启不修 | 60 s 零窗口 |
| 8 | **Q5：ra2loader.exe（注 ra2render）**，无调试器 | 60 s 零窗口 |
| 9 | Q4c：**逐字复刻 harness `launch_direct`**（继承 stdio+env，普通 Popen）| 60 s 零窗口 |
| diag | 裸启 120 s 逐 2 s：ws 爬到 97.5 MB 平台 / frame=0 / **该 pid 顶层窗口恒空** | 同上 |

**与今天早间事实的矛盾要钉牢**：11:0x 的 h7 三趟用**同一 `_src_L1_sf8` 源**
（ddraw.ini 当时已是同一份 `\\x01false` 损坏，载体快照实测 3×0x01 一致）**无调试器**
拿到了窗口（~24 s）。⇒ **不是 ddraw 损坏本身、不是探针写法**：是**开机会话内机器状态
漂移**。现显示拓扑=双"监视器"（主 1707×960 逻辑 + 幻影副屏 [2048,103..3584,967]），
而 h7 时代实测全屏 2560×1440；`ddraw.ini savesettings=1` 会在退出时存窗口位置——
候选机制=**cnc-ddraw 在漂移后的拓扑/存档态上 D3D9 初始化卡死**，调试器事件泵的
线程时序恰好把启动带过去（ab24 挂调试器 7/7 有窗）。**[推测]，未定谳**。
⇒ 明天最便宜的判别：**新开机时段发 1 趟 h7 发射器裸趟**；窗口回来 ⇒ 会话态累积，
仍无 ⇒ 升级为新真机阻塞项。今天不再烧趟。

## 二、★ 更正 D-09/§426：「不崩也不退」说过强——真开臂三趟实为「退出慢且不确定」

D-09 表格行「无 AV 也无退出」按三趟分别回读（本条用 `pid_killed/winerr` 语义：
`False+err=5` = TerminateProcess 对**已退进程**的确定性签名，本机今日实验复现）：

| 真开臂趟 | 命中 | 结局 |
|---|---|---|
| 190505（120 s 窗）| no | 窗内未退，清扫杀（pid_killed=True）|
| 192040 | no | **关窗后 ~92 s 自行 EXIT_PROCESS**（泵满 624 事件后 break）|
| 192528（30 s 窗）| no | 窗内未退（24.1 s 时活），清扫杀 |

⇒ 正确表述：**「≤20 s 正常退出」三趟全不过**（判据不达标不变，**部署仍不合格**），
但**不是「永不退出」**。改件设计（D-09 选项 A）的目标值因此有了：退出链被守卫的
跳过改变后**延迟 ~92 s 或不定**——机制探针要问的是"退出链在等什么"，而不是"卡死了没"。

## 三、我的写域事故（如实登记 + 已被机制抓住）

21:10 我发的一条诊断命令含 `ra2opt_play.bat`（cwd=**源目录**），被后台化超时后
TaskStop，但 bat 已把 `ra2render.log`（8,690 B，PID 45812 完整注入序列）写进
`_src_L1_sf8_20261020/` ⇒ 源目录 88→**89 件**。
随后我发他们件 `_rc4_ab_probe.py --arm A --trips 1 --live` 复跑基线，
**其预检「源件数 got=89 want=88」直接拒发** ⇒ fail-closed 门禁按设计抓住污染，
我没碰成任何真发射。处置：删除我泄漏的 `ra2render.log`（21:2x），复验
88 件 + gamemd `73201cc0` / ra2render.dll `39cbd665` / except.txt `6694b75e`
三哈希未变。**教训入规：bat/任何以游戏目录为 cwd 的脚本，一律只在载体副本里跑；
TaskStop 救不回已经发生的写入。**

## 四、卫生终账（d09b 时段）

所有趟 gamemd/loader 定向击杀闭环（末次 leftover 打印竞态已复核为 0）；
`ab24/`+`d09b/` 载体目录已清；母本四哈希 + 他线探针件 `b063052c…` 终检未变；
dump 零新增（无调试器臂设计上不产 dump）。D-09 正文追加本更正（见该条「更新 2」）。

"""

D09_UPDATE = """
- **更新 2（2026-10-24 21:3x，来源会话自补，不改选项）**：本条「无 AV 也无退出」按三趟
  回读更正为「**≤20 s 判据三趟全不过，但非永不退出**」——192040 趟关窗后 ~92 s 自行
  EXIT_PROCESS（台账 §427 二）。另：选项 B 的主臂「无调试器」**当晚不可发射**——
  同会话 9 次无调试器启动（含逐字复刻 harness launch_direct、ra2loader 路）
  窗口出现次数=0，而 11:0x 的 h7 趟同源无调试器曾 24 s 出窗 ⇒ 机器态会话内漂移
  （候选=cnc-ddraw 拓扑/存档态，[推测]未定谳）。判别趟已排期：新开机时段 h7 发射器裸趟 1 次。
"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    assert crlf0 == 86, "CRLF 基线漂移：%d" % crlf0
    assert before.endswith(b"\n")
    payload = BODY.lstrip("\n").encode("utf-8")
    after = before + payload
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf0
    TARGET.write_bytes(after)
    print("ledger appended; %d -> %d" % (len(before), len(after)))

    # D-09 追加「更新 2」（纯 LF 件，锚点=文件尾，追加后仍 LF）
    pb = PEND.read_bytes()
    assert pb.count(b"\r\n") == 0
    anchor = "- **提出**：2026-10-24（§426 同轮）".encode("utf-8")
    assert pb.count(anchor) == 1, "D-09 尾锚不唯一/缺失"
    upd = D09_UPDATE.encode("utf-8")
    # 放在 D-09 的「提出」行之前更合条目格式：定位该行的字节偏移，插在其前
    idx = pb.index(anchor)
    pe = pb[:idx] + upd.lstrip(b"\n") + pb[idx:]
    assert pe.startswith(pb[:idx]) and pe.count(b"\r\n") == 0
    assert pe.count("更新 2（2026-10-24".encode("utf-8")) == 1
    PEND.write_bytes(pe)
    print("D-09 update2 inserted; %d -> %d" % (len(pb), len(pe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
