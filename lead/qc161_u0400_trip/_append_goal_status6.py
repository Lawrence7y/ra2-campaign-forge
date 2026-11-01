# -*- coding: utf-8 -*-
# GOAL anchor 收口⑥ — reboot → P3m restored; final pins refresh.
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BLOCK = (
    "\n"
    "### 收口更新⑥（10-28 重启侦测→批次建议修正，台账 §449）\n"
    "\n"
    "- **⑤ 的五臂建议【superseded·10-28】**：机器真重启（6006 停机 10-28 00:37:12、\n"
    "  BOOT=10-28 07:52:14，6005=07:52:30）⇒ 「与 L1REG 同会话」不再成立，§1c 对照需求\n"
    "  复活 ⇒ **P3m 恢复必选**，建议回**六臂 P0→P0N→P1→P2→P3→P3m ≈27–30 min**。\n"
    "  批次内互比同新会话⇒内部效度无损；旧会话读数按 V11-c 以各臂帧钟自校准。\n"
    "- 终钉刷新：设计件=543eb983…（§3b 加 superseded-10-28 批注）、D-10=96abcae9…；\n"
    "  其余七件未动（驱动 6afe2711/自检 01c3c308/探针 597e9359/三判定书 77bb6d6c·b7e5aa4a·90ca69d9）。\n"
    "- 裁决↔发射间若再重启，本线发射前重测重报（已写入 D-10 裁③）。真机新增=0；\n"
    "  下一动作权=Codex/用户 D-10 三裁。三目标句态不变。\n"
)
d = open(GOAL, "rb").read()
assert d.endswith(b"\n") and d.count(b"\r\n") == 0, "anchor LF check"
open(GOAL, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("APPENDED sha=", hashlib.sha256(open(GOAL, "rb").read()).hexdigest()[:16])
