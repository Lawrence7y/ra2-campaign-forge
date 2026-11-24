#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Close §857-5 item 5, record the GLM concurrency limit, refresh handover."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"

s = io.open(LED, encoding="utf-8", newline="").read()

# 1. close §857-5 item 5 with a forward pointer
OLD5 = '  5. 那 370 个"计入总数但不可枚举"的函数条目仍未解释。'
NEW5 = (
    '  5. ~~那 370 个"计入总数但不可枚举"的函数条目仍未解释。~~\n'
    '     - ⇒ **§860 已闭合**：370 = Ghidra 的 **`EXTERNAL` 地址空间**里的 PE **导入函数**'
    '（`getExternalFunctions().size == 370`，逐条枚举全为 Win32 API）。\n'
    '       `getFunctionCount()` 统计全部地址空间，`getFunctions(true)` 只走 `ram` 空间。\n'
    '       **12,916 就是引擎的完整函数数**，无未解释余量。见 §860-3 的口径定稿。'
)
n5 = s.count(OLD5)
if n5 != 1:
    raise SystemExit("REFUSE: §857-5 item 5 found %d times" % n5)
s = s.replace(OLD5, NEW5)

CONSTRAINT = """
## §861 · **运维约束（给后续会话）：GLM 子代理并发上限 = 3，超限即限流，表现为"看起来卡死"**（2026-11-15 14:25）

- **§861-1 [已证·用户告知]** GLM 模型通道**限制并发 3 个子代理**，超出会触发限流。
- **§861-2 [已证·本轮的代价]** 2026-11-15 13:23 我一次派了 **6 个** GLM 子代理（T1..T6）。
  40 余分钟后只有 **2 个**（T1、T5）落了文件，其余 4 个**连输出目录都没建**。
  这与台账里"GLM 子代理 `glm-loads69` 跑满 70 分钟零产出"是**同一现象的重复**。
  - ⇒ **归因订正**：上一轮把 `glm-loads69` 记成"卡死/无产出"，很可能也是**并发超限被限流**，不是模型故障。
  - ⇒ **判别方法**：不要看 `list_agents` 的 `running`（它不反映是否真的在跑），
    要看**输出目录里有没有文件在长大**，以及**有没有 python 进程**。两者都空 ⇒ 大概率在被限流。
- **§861-3 [已证·正确做法]** GLM 同时最多 3 路；超出部分**改派 DeepSeek**
  （`magpie-anthropic/work/cn:deepseek-v4.1-flash`，白名单已验）。
  另注：宿主还有**活动子代理总上限 8**，超过会直接拒绝派发（`subagent limit reached`）。
- **§861-4 [未证·未量化]** 限流是"排队"还是"丢弃"未知。若是排队，被限流的任务最终会跑；
  本轮 T3/T4/T6 已被我叫停，未观察其自然结局。
"""
if "## §861 ·" in s:
    raise SystemExit("REFUSE: §861 already present")
s = s.rstrip("\n") + "\n" + CONSTRAINT
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
print("ledger: item 5 closed + §861 added, size=%d" % len(s.encode("utf-8")))

# 2. handover
h = io.open(HAND, encoding="utf-8", newline="").read()
HOLD = '5. 370 个"计入总数但不可枚举"的函数条目未解释'
HNEW = (
    '5. ~~370 个"计入总数但不可枚举"的函数条目未解释~~ → **§860 已闭合**：\n'
    '   它们是 `EXTERNAL` 地址空间里的 PE **导入函数**；'
    '**12,916 是引擎完整函数数**，无未解释余量'
)
nh = h.count(HOLD)
if nh == 1:
    h = h.replace(HOLD, HNEW)
    print("handover: item 5 closed")
else:
    print("WARN: handover item 5 pattern found %d times, skipped" % nh)

GLM_NOTE = """
> ### ⚠️ 运维约束：GLM 子代理并发上限 = 3（台账 §861）
> GLM 通道**同时最多 3 路**，超出被限流；超限的表现为**输出目录迟迟不建、无 python 进程**，
> 极易被误判为"模型卡死"。**判别方式看落盘与进程，不要看 `list_agents` 的 running**。
> 超出部分改派 DeepSeek（`magpie-anthropic/work/cn:deepseek-v4.1-flash`）。
> 宿主另有**活动子代理总上限 8**，超过直接拒绝派发。
> 历史订正：早前记录的"glm-loads69 跑 70 分钟零产出"很可能也是并发超限，**不是模型故障**。

"""
ANCH = "## 0. 锚点（未变）"
if "GLM 子代理并发上限 = 3" in h:
    print("handover: concurrency note already present")
elif h.count(ANCH) == 1:
    h = h.replace(ANCH, GLM_NOTE + ANCH)
    print("handover: concurrency note added")
else:
    print("WARN: anchor not unique, note skipped")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
print("handover size=%d" % len(h.encode("utf-8")))

for name, txt in (("ledger", s), ("handover", h)):
    bad = [(i, hex(ord(c))) for i, c in enumerate(txt) if ord(c) < 32 and c not in "\n\t"]
    print("%s control chars: %d" % (name, len(bad)))
