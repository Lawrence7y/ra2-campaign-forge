#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§424 追加 —— 纯字节追加，CRLF=86 不变，前缀逐字节保持断言。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

BODY = """# §424　三份 RC-4 dump 独立判读 18/18 + H-5 裁决 CONFIRMED + 待裁决台账丢单事故与外科恢复

**性质**：离线（读盘上既有产物 + 仓外 `D:\\ra2dumps`；零真机、零游戏启动）。
**本轮 Lead 裁决 v12 §4 全部执行**：D-01 结案、H-5 核查、模型池收缩重钉。

## 一、三份 RC-4 minidump 独立判读 —— `_verify_dumps_rip.py` **18/18 PASS**

上一版用「x86 CONTEXT 固定偏移 0xB8=Eip」**失败**（读到垃圾 0x2B）。本轮查明：
转储声明架构 `arch=0x9`（UNKNOWN_WOW64），线程上下文是 WOW64 混合尺寸 0x67f，
针值实测落在 **ctx+0xF8** —— 两种 flavor 假设在同一点巧合，固定偏移不可依赖。
⇒ 改**三层判据**，每层独立可杀：
- **L1 结构**：`ThreadList 流尺寸 == 4+48×count`（三份 20 线程全中）；
- **L2 唯一**：崩溃 EIP 字节 `37477200` 在**整份 dump 恰好 1 次**；
- **L3 归属**：该唯一偏移 ∈ 某线程 context 窗口，且 ThreadId == PROBE_DBG
  `rc4_hit.thread`（33096 / 29792 / 37180 逐份配对，三份全中）。
旁证（不作判据）：owner 上下文读值 **Ecx=0 / Esi=0x87F7E8 / Edi=0xF9A344** 三份一致
——与 RC-4「空对象 + 单例全局 + except Esp」三元组现场吻合。
size/sha 与 PROBE_DBG 申报逐份一致（381,007,524 / 381,003,428 / 318,039,700）。
**负控**：`--mutate-M1` 针值改坏 ⇒ L2 三份全红（且 10 次命中，唯一性判据非虚设）；
`--mutate-M2` 期望 tid+1 ⇒ L3 三份全红。产物 `_verify_dumps_rip.out.txt`。
⇒ 「H-5 等真机 DebugActiveProcess」的旧记账**过时**：捕获早已完成（10-22 三趟
三连击），本轮把 dump 侧从「他人脚本单份硬编码」升为**独立三份交叉定谳**。
他人件 `VERIFY_RC4_MINIDUMP.py` 的假 `--dump` 接口（头注承诺、全文件零 argv 解析、
常量第一份专属）**只登记不改**（写域纪律），报告移交归属线。

## 二、★ H-5 v12 裁决 —— Lead 假设 **CONFIRMED（成立）**：C/L3 = 关卡太短，战斗结束正常自退（码 0）

Lead §4.2 原话：「C/L3 可能是测试关卡太短，打赢后游戏正常退出（码 0），而不是崩溃。」
`_adjudicate_h5_v12.py` **13/13** + `_verify_h5_v12.py` 负控 **11/11**
（5 变异 × 目标红+非目标不传染）：

| 判据 | 实测 |
|---|---|
| X1 | C/L3 `wait_returncode=0`（§402 已证 0=「等待时已自退」非活杀 1）|
| X2 | except 多重集差两趟均 0 新增（单独不足，组合用）|
| X3 | `ws_kb=20` 进程已死档（对照 A 趟 137,504 活着）|
| X4 ★ | **同轴时间线**：旁路跳零 clock-t=70.879 + `stage_begin:launch`=11.484 ⇒ **82.363 s**，而 CLOSE 在 frame 阶段之后 ≥ **161.750 s** ⇒ 死亡先于 harness 任何窗口动作 **79.4 s** ⇒ **RC-4 的 WM_CLOSE→DestroyWindow→链 在这两趟结构上不可能发生** |
| X4b/c | 战斗终点帧峰值 1260（≈40.6 s @31fps）；跳零落时钟在跑区间 |
| X5 | 跳零后 1158 条样本 RPM 持续成功、计数器冻结非 None ⇒ 进程活着离开战场 |
| X6 | iso V_FAIL 在 terminate **之前** ⇒ 非竞态产物 |
| X7 | 对照臂 A：rc=1 活杀 + units0=672 ⇒ 两种机制确证 |
| X8 ★ | **时长账**：战斗 45.5 s < 协议 3×25+4=79 s ⇒ 满窗前战斗已结束 ⇒ **测量窗根因收敛到测试图本身**（Lead 预判兑现）|
| X9 | C 终帧画面 41,583 B 与 S397:168 登记逐字节对账 |
| X10 | S397 登记 C 画面=「Battle control terminated — press OK」对话框（游戏内终止文案）|

★ **对 Lead 旁证的一处如实修正**：「A 趟画面是 Mission accomplished」**不成立**——
A 趟实测画面是 Unit Deployment Screen（且 A 进程活着，rc=1）。真正的画面旁证由
**C 趟的终止对话框**承担；主假设本身成立，不受此修正影响（X1–X10 独立于画面）。
**残留子问题（不阻塞裁决）**：对话框 OK 无人点击，进程却码 0 结束——游戏自退/
超时关窗未定谳（字符串不在 YURI.exe/gamemd.exe 明文字节，在资源里，静态到此前为止）。
**对①的后果**：C/L3 两趟确认对帧率零信息量（早已定性），而「31 档在」的基线趟
仍须 T55 spawnfix 那一档——H-5 关的是「死因」问题，不是档位问题。

## 三、⚠ 待裁决台账丢单事故 —— `PENDING_DECISIONS.md` 是并发移动靶

1. `e8dc58e`（RE-ATLAS R-041 轮）**整文件重写**该件（36,976→8,425 B），
   **静默吞掉**本线上一轮立的 **D-08 全文**（harness7 升格裁决）与 D-06 的后续更新；
2. 本轮读取时该件又两次变样（8,970→6,691 B，D-06 消失、末行截断在半句
   「…§409 用密封深扫」）——同一时刻另一会话在写。
⇒ 本线对策（`_fix_pending_d01_recover.py`，原子写+逐段断言）：
- **D-01 结案**（Lead v12 §4.1）：条目删除，已裁记录插入「C' 停在方案 A；B' 可重开；
  『不确认即视为同意』违规，今后禁止」；
- **事实更正**（unshallow 后实测，`git fetch --unshallow` 本轮执行）：根提交=
  `c4923c8`（唯一），截至 `66eef68` 历史 **192** 个提交（HEAD `e79f4b0`=194）。
  条目原文「b7f0508 是根提交/共 105 提交」系**浅仓库假象**（v12 §2 开工即验的原因）；
- **恢复** D-06 全文（XVERIFY 来源件，逐字节自旧版重建）+ D-07 本线追加段
  （自 `_append_d07_evidence.py` 原文）+ **D-08 全文**（自 `_append_d08.py` 原文），
  6,691→11,444 B。**他人条目主体逐字保留**。
⇒ **教训入规**：共用台账的追加纪律防不住**他人的整文件重写**；跨会话写共享件后，
   下一轮必须先验「自己上轮内容还在不在」，不能只验「我追加的内容在不在」。

## 四、模型池收缩与派发通道现状（v12 §8 更新）

用户图示允许列表 = 16 项（ListModels 实测吻合）。三件子代理 persona 重钉：
`ra2-quick-consult` `new-provider/qfmodel$enabled`→**`new-provider-3/qoder-cn:qfmodel`**；
`ra2-patch-verifier` `new-provider-3/deepseek-v4.1-flash`→同上（DeepSeek 族裸名不在列表）；
`ra2-re-analyst` `new-provider-4/step-5-preview`（**禁用线**）→`new-provider-2/glm-5.3-flash`。
★ 但 Agent 派发**注册表按会话缓存**：重钉后仍按旧值解析报 `provider-not-found`，
新建 persona 亦不入表 ⇒ **异族咨询/盲验本轮全部派发失败**（千问单轮问 H-5 三子问
的件未送出，顺延下一会话冷启动重试）。本轮无子代理产出；台账 §424 全部主会话亲执。

## 五、卫生与铁律

- 母本三哈希复核未变：harness6 `ff8245d27b3db22a` / harness7 `d019e8beecfb5fd8` /
  gamemd `73201cc021497c95`；真机进程 0（gamemd/ra2 计数均 0），零新趟。
- dump 与 ra2dumps 本体不上仓；只上判读脚本与输出 txt。
- 未碰 re_atlas/ 他线暂存件；提交用显式路径限定。
- commit 单次尝试；被 L3 拦则不重试（D-07 裁决挂起中）。

"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    assert crlf0 == 86, "CRLF 基线漂移：%d" % crlf0
    assert before.endswith(b"\n"), "母本须以 LF 结尾"
    payload = BODY.lstrip("\n").encode("utf-8")
    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, "CRLF 数必须不变"
    TARGET.write_bytes(after)
    print("appended %d bytes; %d -> %d; CRLF stays %d"
          % (len(payload), len(before), len(after), crlf0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
