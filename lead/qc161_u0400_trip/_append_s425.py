#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§425 追加 —— X11 静态收口：三替代解释两否一存。CRLF=86 不变。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

BODY = """# §425　X11 静态收口：C/L3 战斗结束三替代解释——两否一存（零真机）

**性质**：离线只读（趟图字节 + 载体资源 + 旁路时钟）。承接 §424 X11 残留
（「收场触发者是谁」）。第二意见（general-purpose 兜底）留了两个可静态排查的
备选，本轮全部排查完毕：

## 一、地图触发器说 —— **否证（图里根本没有触发器）**

普查（同 grep 模式，配可见对照）：

| 文件 | `[Trigger` 命中 | 说明 |
|---|--:|---|
| `_src_L1_sf8_20261020/XMP29U2.MAP`（C 趟图）| **0** | 全节表无 [Triggers]/[Action]/[Event]/[TaskForce]/[TeamType]/[Script] |
| `_src_L3_sf10c_20261021/XMP29U2.MAP`（L3 趟图）| **0** | 同上；两图节表一致 |
| `_maps_fixed/XMP29U2.MAP.orig_93c2974b` | **1**（`:1559`）| **阳性对照**：未走 spawnfix 的母图有 [Triggers]（内容=环境音效三条：Bird/City/Wind Sounds，无任何收场动作）|
| `[2]0LoadBench_U0400.yrm` | 1 | 第二对照，同样命中=装置能看见 [Triggers] |

⇒ **零命中是"真没有"**（spawnfix 系图重存时掉了触发器节），**且即便按母图
[Triggers] 内容看也只是音效**——「地图脚本主动收场」这条替代解释被否。
附带：`TimeLimit=` 全部图中 **0 命中**（对照同目录件可见性由上表钉），
`[Basic]` 无 `EndOfGame=yes`。⇒ **定时器收场亦否**。

## 二、歼灭/胜负收场说 —— **否证（结束时仗还打着）**

C 旁路时钟跳零瞬间及前后：units/infantry/techno = **813 / 311 / 1128 恒定非零**
（跳零前=跳零时=时钟尾行三处同值）。若是「某 house 被歼灭⇒战败判定」，
实体计数应塌向零或至少剧烈变化。14 个 house 全 `PlayerControl=no`（两图一致）。
⇒ 「打赢/打输的胜负播报」与观测矛盾；第二意见的胜/负串族（victorious/defeated）
不是本次画面文案。

## 三、剩下的一条：引擎对「无控制方会话」的自动终止 —— 与全部观测自洽

三否一存 ⇒ C/L3 的收场=**无玩家控制的遭遇战被引擎按会话层自动终止**
（画面文案「Battle control terminated」的措辞也指向控制层而非胜负层，
第二意见独立给出同一读法，置信中）。
「无人点 OK 却以码 0 结束」用第二意见 #2 解释：**该框不是阻塞式模态**
（真模态不会自退），引擎在会话终止路径上自行收尾。

## 四、资源侧取证（如实登记为不确定）

`Battle control terminated` 在 gamemd.exe / YURI.exe / 载体 16 个顶层 .mix
（utf-16-le 与 latin1 双编码）全部 0 命中；`ra2md.csf` 同 0（csf 里连
"terminated/accomplished/defeated" 都没有，仅 Mission/Control/OK 等散词=键名）。
⇒ **文案来源未能静态定位**（嵌套 mix 需 TOC 展开，成本不匹配收益）。
这条不确定**不抬升也不削弱**判决：主判据是 §424 的 X1–X10 + 本节的普查。

## 五、结论与边界

- **H-5 残留子问题 X11 关闭（静态可达范围内）**：收场触发者=引擎会话层自动终止；
  脚本说/定时器说/歼灭说分别被节表普查、TimeLimit 普查、实体计数恒非零否证。
- **交付件（判据从散文升为可复跑门禁）**：`_census_x11_endtrigger.py`
  **12/12 PASS**——每条「0 命中」都带**阳性对照**（母图 .orig/yrm 确有
  [Triggers] 可被同一装置看见、插入式探针可见 TimeLimit、csf 里 Mission/OK
  散词可数），装置被证「看得见」；`_verify_x11_census.py` 负控 **5/5**——
  诱饵图含触发器⇒T1d 红、诱饵含 TimeLimit⇒T2b 红、诱饵时钟跳零 units 清零⇒T4 红
  且非目标不传染。
  ⇒ 过程中又抓到并修掉**判据 id 令牌碰撞**（负控器按行首首个令牌取 key，
  三行同以 `T1` 开球/两行同以 `T5` 开球会互相覆盖，「checks=8/11」对不上真实条数；
  id 唯一化后 12=12 才闭合）。**教训：被检件的判据 id 必须互不为前缀，
  否则负控器读不到该红。**
- 要再进一步只剩真机复测（换无触发器空图对照或画面连续采样），
  与 v12 §5 待办的真机时段合并排期，不单开趟。
- 卫生：本轮零真机、零进程；只读普查；母本哈希未动（§424 已核）。

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
