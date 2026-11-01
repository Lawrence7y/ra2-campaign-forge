#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§428 追加 —— G2 过滤器 bug 假墙拆穿 + d09b 双臂真数据 + exitstate 普查 v2 自我否证。CRLF=86。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """# §428　★★ 假墙拆穿：`enum_windows_for` 拿线程 id 比 pid —— 「无调试器 9 连败」整案作废；
#        双臂真数据到手（D-09-B 完成）；exitstate 普查 v2 的「=2 写点」被对齐解码自否

**性质**：真机（10-25 新开机会话 08:36:58）。承接 §427。本条推翻 §427 第一/三节主判读，
并交付 D-09-B 的正式答案。

## 一、G2：墙不存在——我的窗口过滤器自杀

arm G（`_disc_armG.py`）双口径观察：裸启 gamemd **3.1 s** 出现类=`Yuri's Revenge`
窗口，pid=4168 **就是 spawn 的那个 pid**，且与我的过滤枚举同 pid。⇒ 差异只有一个：
`_probe_d09b_hang.enum_windows_for` 写的是
    `if u32.GetWindowThreadProcessId(hwnd, byref(w)) != pid`
**返回值是线程 id，出参 w 才是 pid**（他线 `find_main_window` 用出参，从未中招）。
⇒ 该过滤**恒不等** ⇒「任何窗口都不存在」。§427 的「9 连败/机器态漂移/判别趟」
全部作废；钉死点是 `_disc_armG.py` 的**第二口径**（不按 pid 过滤的全局窗口枚举）：
同一次裸启里 per-pid 口径=0 窗（旧 bug）、global 口径=3.1 s 命中且 pid 相同。
（`_disc_boot25.py` 首跑另撞新坑：Windows 上 `os.spawnv(P_NOWAIT)` 返回**句柄不是 pid**，
把 768 当 pid ⇒ OpenProcess err=87；经 `GetProcessId(句柄)` 修正后 per-pid 口径仍 None ⇒
才逼出 arm G 的双口径对照）。**教训（入 [[gate-assert-values-not-existence]] 家族新变种）**：
「观测不到」的否定式结论，先用**第二口径交叉**（此处=不按 pid 过滤的全局枚举）；
两口径不一致时，先怀疑口径而不是世界。

## 二、D-09-B 正式答案（双臂各 1 趟，10-25 会话，修过滤器后首跑）

| 量 | MAIN（守卫**开**，无调试器） | CTRL1（守卫**关**，无调试器） |
|---|---|---|
| 窗口出现 | 0.67 s（枚举已修）| 0.65 s |
| 关窗后 60 s | **不退出**；无新窗口；except.txt **未变** | **不退出**；**弹出 `#32770` 对话框**「Yuri's Revenge」(382×163)；**except.txt 变了**（6694b75e→9871e801）|
| frame 轨迹 | 恒 0 | 恒 0 |
| **exitstate[0xA8EDD8]** | **0→1**（509 样本里翻转，之后**恒 1 到观察结束**）| **恒 0** |
| singleton | 16634640→0 | 同左 |
| ws 轨迹 | 65,964→192,516 KB（**持续爬升**）| 65,964→110,808 KB |
| 守卫日志 | enabled=1 **install 8/8** | enabled=0 关臂 |
| 收尾 | 定向击杀 | 同左 |

⇒ ①昨晚「开臂挂死」在无调试器下**复现且更强**：无对话框、无 except、exitstate 闩 1、
   ws 持续爬（192 MB）——**比关臂更像「资源泄漏中的僵尸」**；
⇒ ②**关臂无调试器**的真实形态=**弹错误对话框等人点 OK**（正是 C 趟/历史现场的形态！）
   + 写 except.txt ⇒ 「无人值守=永久挂起」，这解释为什么真实玩家「窗口关不掉」；
⇒ ③ ab24 里 192040 趟「~92 s 自行 EXIT_PROCESS」发生在**调试器泵事件**上下文，
   今晚无调试器 60 s 内 MAIN 未退 ⇒ 自退或不存在/或>60 s；**判别已列下一轮首趟**
   （MAIN `--watch 120`，一次发射钉死「到底会不会自退」）。
⇒ ④ a8=V_FAIL 是我 `_cleanup` 的**击杀后未等待**竞态（rem 在 TerminateProcess 后
   立即枚举，进程表尚未摘除）；趟末/臂间 `leftover=0` 与定向击杀清单证明实际闭环。
   修法=击杀后轮询 ≤2 s（记在探针文件头注，未改行为以免本轮内扩面）。

## 三、exitstate 静态解剖 v2：「=2 写点」被对齐解码**自我否证**

`_exitstate_census2.py`（字节先决+阳性对照 singleton=74 命中）：`.text` 字面命中 6 处，
classify 归因出「0x6BE0B6/0x6BEC72 mov [0xA8EDD8],edi/esi」「0x777818 mov [0xA8EDD8],2」等。
但 `_exitstate_hotspot.py` 从函数体**对齐**解码 0x7777FC..0x777835：
    `test edi,edi / jz / push esi / mov ecx,edi / call 0x728CF0 / … strcpy 序列 …
     mov edi,[0xB73080] / shr ecx,2 / rep movsd …`
⇒ **该区域根本不引用 [0xA8EDD8]**，触碰的是 [0xB73080]/[0xB730A0]。
「=2 写点」与「add byte ptr [ecx+0xa8edd8], ah」同类 = **线性解码错位幻影**
（本项目十坑 #1 的复发实例）。⇒ v2 的 6 处归因**未经逐点对齐复核，一律标 UNVERIFIED**；
exitstate「谁置 1/为何恒 1」的静态答案**未获得**，D-09-A 的设计输入改由
第二节实测数据承担（闩锁值 1、无对话框、ws 爬升）。下一步=以函数头锚定
（前邻 0xCC 填充）逐点重解 6 处命中，或直接用调试器读写入断点（硬件观察
WriteWatch）——后者一趟即可钉死「谁写 1」，列为候选。

## 四、卫生与账面

今日发射：判别 Q4c（假 abort=err87，spawnv 返回句柄非 pid 的新坑，已修）
+ arm F（stdio 假设判死）+ arm G（G2 命中）+ MAIN + CTRL1 = 5 趟（含 2 趟作废诊断趟）；
母本四哈希未动；他线探针件未动；`D:\\ra2dumps` 今日零新增（双臂设计上不产 dump）；
残留进程 0；载体全删（MAIN 的 ct 目录删除竞态由趟末复验兜住，`leftover=0`）。

"""

D09_UPDATE3 = """- **更新 3（2026-10-25，来源会话，本条选项不变，判据升级）**：§427「无调试器臂不可发射」
  **作废**——是来源会话探针自身的窗口过滤器 bug（`GetWindowThreadProcessId` 返回值=线程
  id 被拿去比 pid，恒不等）。修后双臂真数据（台账 §428 二）：
  **开臂无调试器**=关窗后 60 s 不退出、无对话框、except 不变、**exitstate[0xA8EDD8] 闩 1**、
  ws 爬至 192 MB（僵尸+泄漏形态）；**关臂无调试器**=不退出、**弹 #32770 错误对话框**、
  except.txt 变化（真实玩家现场形态）。⇒ ①部署不合格的结论**加强**（无调试器下更糟：
  崩溃变成静默闩锁+内存爬升）；②新增待钉量=「开臂是否根本不会自退」：ab24 的 ~92 s
  EXIT_PROCESS 发生在调试器上下文，无调试器 60 s 未退 ⇒ 下一轮首趟 MAIN `--watch 120`。
  ③静态侧：`mov [0xA8EDD8],2`「写点」被函数头对齐解码否证（错位幻影），exitstate 写者
  未定；候选手段=硬件写入断点一趟定谳。选项 A/B/C 与裁决请求**不变**。
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

    pb = PEND.read_bytes()
    assert pb.count(b"\r\n") == 0
    anchor = "- **提出**：2026-10-24（§426 同轮）".encode("utf-8")
    assert pb.count(anchor) == 1
    upd = D09_UPDATE3.encode("utf-8")
    idx = pb.index(anchor)
    pe = pb[:idx] + upd.lstrip("\n".encode()).rstrip(b"\n") + b"\n" + pb[idx:]
    assert pe.startswith(pb[:idx]) and pe.count(b"\r\n") == 0
    assert pe.count("更新 3（2026-10-25".encode()) == 1
    assert pe.count("更新 2（2026-10-24 21:3x".encode()) == 1
    PEND.write_bytes(pe)
    print("D-09 update3 inserted; %d -> %d" % (len(pb), len(pe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
