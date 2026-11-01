#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§424b 追加 —— 异族咨询实况 + 第二意见对 H-5 表述的收紧。CRLF=86 不变。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

BODY = """# §424b　派发通道实况（本会话注册表缓存）+ H-5 第二意见与表述收紧

## 一、派发现况（如实登记）

- 三件 persona 的 model 行已按用户允许列表（= ListModels 16 项）改盘
  （consult→`new-provider-3/qoder-cn:qfmodel`、verifier→同、re-analyst→`new-provider-2/glm-5.3-flash`）；
- **但 Agent 注册表按会话缓存**：重钉后派发仍按旧值解析（`provider-not-found; selection=new-provider/qfmodel`），
  新建 persona 类型本会话不可见（`Agent type not found`）；
- CreateWorkflow 的 subagent_model 能解析允许模型，但技能契约 §1 明确：**用户未点名
  workflow 就不得起 workflow** ⇒ 不用它绕派发；
- ⇒ 本轮第二意见经 **general-purpose（会话模型 DeepSeek 族）**兜底送达。
  **覆盖登记窄于计划**：同族 fresh-context 意见 ≠ 异族盲验；异族（千问/GLM）派发
  **顺延下一会话冷启动**（缓存失效后 persona 重钉才生效）。

## 二、第二意见三答（置信度随原文）

1. **触发源**（中）：「Battle control terminated」属**会话/控制层自动终止**一族，
   不是胜/负播报族（后者是 victorious/defeated/Mission Accomplished）。
   保留两个备选：**开局 0 单位 house 立即出局**（社区已知坑）/ **地图自带触发器收场**。
   全 AI 房时长**无公认常数**（低置信，明示不编）。
2. **无人点 OK 的走向**（中低）：**不存在可靠的「模态框超时自退」**；「没人点却码 0
   结束」反推该对话框**大概率不是阻塞式模态**（或退出由另一路径完成）。
   ⇒ 这正面回应了 §424 X11 的残留子问题（谁按的 OK：**它可能根本不需要按**）。
3. **退出码区分力**（高）：**码 0 单独不能证明没崩溃**——SEH 兜底 `ExitProcess(0)`
   与正常结束在退出码维度不可区分；裸 AV 才是 0xC0000005 可分。

## 三、对 H-5 裁决的影响：**结论不动，表述收紧一处**

§424 的判定本就**不以退出码单证**：X4 同轴时线（死先于任何 harness 窗口动作 79.4 s）+
X5（跳零后 RPM 持续成功、计数器冻结非 None ⇒ 进程活着离开战场）+ X2 except 零新增 +
§406 WER 双通道零命中，是**组合否证**；X1 只是其一。
按第二意见把最终表述从「CONFIRMED=正常退出」**收紧为**：
「C/L3 的死亡**与会话终止路径完全一致**（正常结束形态），崩溃形态被组合证据否证；
『码 0』单证不作『未崩溃』证明（此口径与铁律『except 零新增≠未崩溃』同理）。」
备选解释处置：0 单位出局说——旁路 `best_25s_window` 实测 units 964→822 递减，
战斗真实打起来了，该说弱化但不排除（收场触发者是谁仍是 X11 残留）；
地图触发器说——静态无解，若 Lead 要钉死，唯一干净手段是换无触发器空图复测（真机，待排期）。

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
