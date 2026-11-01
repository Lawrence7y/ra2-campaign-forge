#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§426 追加 —— RC-4 守卫首验 ab24：开臂 3/3 零 AV（真机）。CRLF=86 不变。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

BODY = """# §426　★ 真机：RC-4 守卫首验（ab24）——开臂 3/3 零 AV，注入中性对照成立；两个判据级发现

**性质**：真机时段（用户 10-24 授权「只要我不说拒绝都可以真机」）。
v12 §6 序列的 ②-A 项：**v5 守卫 A/B** 首验批。产物 `lead/qc161_u0400_trip/ab24/`，
发射器 `_drive_rc4_ab24.py`（本线写域；**他线 `_rc4_ab_probe.py` 一字未改**，
import+monkeypatch 复用：CARD 重绑本线写域、create_carrier 包装写开关、
src 布局在本线物化并逐件复哈希）。

## 一、批次与结果（同开机会话 10:36 起；hold=6 s 对齐 10-22 基线；WM_CLOSE 驱动）

**发射共 6 批 12 次实跑趟**（批次 2 的 2 次 B 臂趟在启动前就 abort，无数据）。
判读只取「开关状态被守卫日志自证」的趟：

| 臂 | 实跑 | 结果 |
|---|--:|---|
| A 直启 gamemd | 4（批 1/2/3/4）| **hit=YES 四趟**：(0x724737, 0x250)，singleton_at_hit=0，关窗后 9.3–9.7 s |
| B 注入，Guard=0 | 2（批 3/4）| **hit=YES 两趟**：三元组逐位相同 |
| B 注入，Guard=1（**假开臂**，批 3）| 1 | **hit=YES**——守卫日志自证 `EnableRC4Guard=0`（见二）|
| B 注入，Guard=1（**真开臂**，批 4/5/6）| 3 | **hit=no 三趟**；日志三趟均「原字节比对 8/8 ⇒ 守卫已装 8/8」|

★★ **归因控制到位**：B-off 与 A 崩得逐位相同 ⇒ **注入本身中性**，
真开臂的 0 AV **只可归因守卫安装**；而假开臂那趟（开关实际=0）照样崩 ⇒
开关与行为**方向一致**（=0 崩 / =1 不崩），排除「真开臂的 0 AV 是运气」。
这正面回答 §407 裁决 6 的「功效仅 4.5%」担忧的前提：WM_CLOSE 臂**确定性命中**
（本会话崩溃形态 7/7：A×4 + Boff×2 + 假开×1），单趟即可判，A/B 不再需要大样本配对。
dump 旁证：崩溃趟落 `D:\\ra2dumps\\rc4ab_*.dmp`（仓外，共 **7 份**，含批 1 的
t1A——它崩了也落了 dump，只是驱动崩溃发生在落盘之后），真开臂趟**零 dump**——双通道一致。

## 二、判据级发现 1：`EnableRC4Guard=1` 首跑是**假开臂**（注释陷阱）

批次 3 三趟全 hit=YES——排查发现我替探针补的 ini 开关写入函数用了
`txt.replace("[Logic]", …)`，而载体 `ra2render.ini` 的**头注释里有字面 `[Logic]`**
⇒ 键插进注释区、不属于任何节 ⇒ `GetPrivateProfileIntA` 读回缺省 0。
批次 3 的「开臂」实际全程关臂（守卫日志自证 `EnableRC4Guard=0`）。
修正=只认**独占一行的节头**+写后**回读验证**，不符即抛（fail-closed）。
⇒ **教训**：往「别人的配置文本」里补键，注释/散文本里的同名 token 是活跃歧义源；
  开关类写入必须**回读+运行时日志双向验态**，批次 3 若只看我的写入函数会全绿自欺。
（他线探针没有开关 CLI——这个洞是他们件的真实缺口，报告移交，不改件。）

## 三、判据级发现 2：「守卫命中计数≥1」这条判据**结构上不可达**（v12 §4.3 登记降级）

守卫把 `g_hits` 的「计数合计」只在 **DLL_PROCESS_DETACH** 写日志；
而趟终是 `TerminateProcess`——**进程强杀不跑 DllMain detach** ⇒ 开臂趟的
hits_total 永远 None（本批四趟全 None）。⇒ 该判据不是「没抓到」而是
「通道不存在」；**改判为日志「守卫已装 8/8（memcmp 原字节一致）」+ 抑制差分**
承担「守卫在场且起作用」的举证。若 Lead 坚持计数，需守卫件改造
（命中即时 flush 或共享内存计数），那是改件=他线写域。

## 四、★ 未闭合缺口：守卫开臂后**不崩也不退**（关窗后 ≥24 s 存活）

短窗趟（debug_timeout=30 s）实测：关窗后 **24.1 s 无 EXIT_PROCESS**，超时后由趟
清扫击杀（a8 PASS）。长窗趟同样 114 s 未见退出。对照 t2Boff ~11 s 内走到崩溃路径。
⇒ 守卫语义=「ecx=0 时跳过空对象调用」，跳过之后**退出链卡在等不到那几次调用效果**
——把崩溃换成了挂死。**作为部署修复不合格**：还需要「跳过后主动走正常退出」。
v12 §2-A 开臂四判据现状：**0 AV ✓（真开臂三趟全过，dump 通道同步零份）**；
守卫计数 ✗（判据通道不存在，见三）；**≤20 s 正常退出 ✗（挂死，见四）**；
L1 无副作用 —— 本批未测（探针不进局）。
⇒ **不满足部署门槛**；分叉交 Lead：见 **D-09**。

## 五、卫生

6 批 10 次实跑趟串行；每趟 a8=PASS、趟间残留=0、批末进程=0（三名字实测）；
母本 gamemd `73201cc0…` / harness6 `ff8245d2…` / harness7 `d019e8be…` /
他线 `_rc4_ab_probe.py` `b063052c…` 全程未变；载体除批次 2 两孤儿目录
（我的驱动崩溃所致，1.8 GB×2，已手删，ab24 回 273 KB）外全部趟内自删；
dump 只落 `D:\\ra2dumps`。批次 1 的 t1A hit=YES 属同会话基线复现（有效证据）；
批次 2/3 的「B 臂」结果全部作废（批次 2 建载体未启动、批次 3 假开臂），
**只有批次 4/5/6/7 计入判读**。

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
    print("appended %d bytes; %d -> %d; CRLF stays %d"
          % (len(payload), len(before), len(after), crlf0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
