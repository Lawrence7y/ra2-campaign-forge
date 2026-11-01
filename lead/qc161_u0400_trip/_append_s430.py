#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§430 追加 —— 硬件写断点定谳 exitstate 写入者 0x6BE0B6；WOW64 #DB=0x4000001E 两坑。CRLF=86。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """# §430　★★ 硬件写断点一趟定谳：exitstate[0xA8EDD8]=1 的写入者 = `0x6BE0B6 mov [0xA8EDD8],edi (edi=1)`；
#        装置自身拆掉两个坑（WOW64 单步=0x4000001E；Dr7=0x90001 由游戏内阳性对照自证）

**性质**：真机（10-25 会话续 §429）。交付 D-09-A 的设计输入。
件 `_wp_exitstate_writer.py`（v3 终版）；产物 `lead/qc161_u0400_trip/d09b/wp2_*/_rec.json`。

## 一、趟设计（游戏本身=自证台，两级阳性对照同一条代码路径）

- S0 附加后 Wow64GetThreadContext 读通（Eip 落 ntdll=启动早期合法，v2 误用
  「游戏镜像区间」谓词把自己杀了一回——S0 谓词=**能读到平坦 32 位地址即可**）。
- **P1=[0x00B73550]（hwnd 全局）写断点**：§429 双证它在退出链必被写 0 ⇒ P1 不中=装置死。
- **P2=[0x00A8EDD8]（exitstate）**：P1 命中后当场换装，等写者。
- Dr7 掩码不靠记忆：候选逐个实测 + 游戏内 P1 命中即 **0x90001 为正确值**
  （L0=bit0 | 写=01<<16 | 4B=10<<18）。**v1 用 64 位 python 孩子自证是苹果比橘子**
  （喂 32 位 CONTEXT 必废），整轮差点被我判「装置不可用」——第二次同型教训：
  **自证台必须与被试同配置**（同 WOW64、同上下文结构）。

## 二、结果（一趟，hits=2，卫生四项 PASS，leftover=0）

| 命中 | 时刻 | 线程 | Dr6 | EIP(下一条) | 当场读值 |
|---|--:|---|---|---|---|
| P1 hwnd | 14.17 s | 18852 | ffff0ff1(B0) | **0x777814** | eax=0，exitstate=0 |
| P2 exitstate | **19.99 s（WM_CLOSE 后 +5.8 s）** | 18852 | ffff0ff1(B0) | **0x6BE0BC** | **edi=1**，exitstate_now=1 |

字节回推（x86 写断点在**指令执行后**触发）：
- P1 现场 0x777806 起：`mov [0x887368],ebx / mov eax,[0xA8EDD8] / mov [0xB73550],ebx`
  ⇒ **正是 §398/ab24 的 0x777803 清零块**——阳性对照不但证明装置，还**顺带把那条
  链的运行时存在性钉到了指令粒度**。（P1 t=14.17 与 close_at=14.224 差 50 ms 且
  先后反了——时间戳取自不同分支的 round，不影响命中本体，如实登记不追。）
- P2 写点 **0x6BE0B6：`mov [0xA8EDD8], edi`（edi=1）**；紧邻前文
  `mov edx,[0x88730c] / mov cl,1 / call 0x4F4780`，紧邻后文
  `mov ecx,0xA83D10 / call …`；所在函数是一条**长链**（0x6BE0xx 起每 ~0x48 字节
  一个同构块：`call 0x6C7400(ecx=0xB0BC88) / push 8 / call 0x7C9E17 / push 名字串
  (0x7e96xx) / push eax,1,1,buffer / call esi`）⇒ 形如**「按序冲刷一串退出步骤/
  事件处理器，然后把 exitstate 递增 1」**的状态机主体。

## 三、对 census v2（§429 三）的裁决

- 0x6BE0B6「mov [0xA8EDD8],edi」**运行时坐实为真**（census 的字节先决没错，
  是它邻块 0x6BE0B7 的 `cmp eax,0xa8edd8` 错位读法造成假象）；
- 0x777818「mov [0xa8edd8],2」**维持幻影**——P2 断点从未捕到写 2（一趟内
  1→2 的那次写根本没发生）⇒ 与 §429 实测互证：**状态机走到 1 就停**。

## 四、D-09-A 设计输入（定稿级，供裁决）

写入 1 之后**无人再写**；150 s 轮询（§429）与断点趟（本条）双口径一致。
⇒ 守卫开臂的挂死不是「exitstate 没被推进」而是「**推进它的例程自己卡在
第 1 块的完成条件上**」——长链里 `call esi` 调的是被守卫跳过的成员函数族
（ecx=0 ⇒ 守卫 `xor eax,eax; ret`），**它们的返回值/副作用是后续块的门槛**。
候选改法（都属守卫件改造，他线写域，Lead 派或授权）：
  a) 守卫在 ecx=0 时不只返回 0，而是**置位该退出步骤的「视为完成」标志**
     （需先静态钉 `call esi` 各族的返回被谁消费）；
  b) 或守卫**别拦这些特定调用点**、改为在拦到的同时把链上等待量补写；
  c) 或放弃函数头 trampoline，改在 0x6BE0B6 之后做**exitstate 强制推进**
     （1→2→…）+ 逐块跳过——风险最高（绕过游戏自己的顺序保证）。
⇒ **一趟硬件写断点把「卡住」变成了「卡在第几块、为什么」**；剩余问题
（`call esi` 具体是谁、返回被谁消费）是纯静态活，可下轮离线做（不烧趟）。

## 五、卫生

本会话（10-25）真机累计发射：wp v2 一趟（S0 谓词误杀，未投 WM_CLOSE）+
wp v3 一趟（本条）；两趟载体全删、leftover=0、母本四哈希未变、他线件只读
（`_rc4_ab_probe.py` `b063052c…` 前后一致、`D:\\ra2dumps` 今日零新增）。
`d09b/wp2_*` 产物=JSON 判据件（无游戏资源，ct 树已删且 gitignore 已堵）。

"""

D09_UPDATE5 = """- **更新 5（2026-10-25，来源会话，选项不变，D-09-A 设计输入到手）**：一趟硬件写断点
  定谳 **exitstate=1 的写入者=`0x6BE0B6 mov [0xA8EDD8],edi(edi=1)`**（主线程，WM_CLOSE 后
  +5.8 s；阳性对照 P1=hwnd 写点 0x777814 同趟命中，顺带把 §398 清零块钉到指令粒度）；
  写入 1 后**再无人写**（断点+150 s 轮询双口径一致）⇒ 挂死=退出步骤长链
  （0x6BE0xx 每 ~0x48B 一块，`call esi`=被守卫跳过的成员函数族）卡在第 1 块完成条件。
  改法候选 a/b/c 见台账 §430 四（均属守卫件改造=他线写域，需 Lead 派工或授权本线出副本）。
  census v2 裁决：0x6BE0B6 运行时坐实为真；「=2 写点」维持幻影。
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
    upd = D09_UPDATE5.strip().encode("utf-8") + b"\n"
    idx = pb.index(anchor)
    pe = pb[:idx] + upd + pb[idx:]
    assert pe.startswith(pb[:idx]) and pe.count(b"\r\n") == 0
    for tag in ("更新 2（2026-10-24 21:3x", "更新 3（2026-10-25",
                "更新 4（2026-10-25", "更新 5（2026-10-25"):
        assert pe.count(tag.encode()) == 1, tag
    PEND.write_bytes(pe)
    print("D-09 update5 inserted; %d -> %d" % (len(pb), len(pe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
