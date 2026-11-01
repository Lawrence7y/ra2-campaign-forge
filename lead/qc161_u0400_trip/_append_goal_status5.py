# -*- coding: utf-8 -*-
# GOAL anchor 收口更新⑤ — V2FIX receipt + final pins, package complete.
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BLOCK = (
    "\n"
    "### 收口更新⑤（复核到盘零红项+§445 补闸闭合；交付包终钉齐备，台账 §446）\n"
    "\n"
    "- XVERIFY_V2FIX（`90ca69d9…`，GLM）V1–V6 **全 CONFIRMED 零红项**；V3 双向证明修复\n"
    "  （回注旧缺陷⇒0.9042 红、原版噪声带内）；V5 全仓普查无第二现场。总判=可交 D-10 审定。\n"
    "- §445 载体路径闸已补（130 断言+FT13+M10）⇒ 套件 17/17、变异 10/10、live rc=3 不变。\n"
    "- 终钉：驱动=6afe2711…、自检=01c3c308…、设计件=70894c58…（§3b 收口）、探针=597e9359…。\n"
    "- 批次建议定稿=**五臂 P0→P0N→P1→P2→P3（P3m 可选末臂）**；真机新增仍=0；\n"
    "  下一动作权=Codex/用户 D-10 三裁。三目标句态不变。\n"
)
d = open(GOAL, "rb").read()
assert d.endswith(b"\n") and d.count(b"\r\n") == 0, "anchor LF check"
open(GOAL, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("APPENDED sha=", hashlib.sha256(open(GOAL, "rb").read()).hexdigest()[:16])
