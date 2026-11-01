# -*- coding: utf-8 -*-
# GOAL anchor append: 收口更新③ (LF file, keep LF).
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BLOCK = (
    "\n"
    "### 收口更新③（D-10 立项 + 通道探针 GO-READY，台账 §441/§442）\n"
    "\n"
    "- **② 局内关窗（X）**：交付包由四件扩为六件——新增 D-10 待裁条目\n"
    "  （批次构成/顺序、P2∧P3m 存废、真机时段；`PENDING_DECISIONS.md` 4,949→6,641 B）与\n"
    "  **通道探针 `_x_channel_probe_20261027.py`**（sha256=a1cd4dbb…）：零发射前提下补上\n"
    "  v2 故障注入未证的三层空白——真 GDI 桌面截屏 3584×967 走同一判定器（S1 规范可解+\n"
    "  S2 frac=0.8927 非全黑）、PNG 读写双侧 schema 对合、负控变异 7/7 命中；\n"
    "  `--preflight` rc=0⇒GO-READY、`--live` 永久 rc=3（探针无游戏 popen 路径，非后门）。\n"
    "- 四件终值哈希复核不变：65e086e7…/8c74bba6…/b66466b6…/77bb6d6c…；本轮真机新增仍=0。\n"
    "- **三目标句态不变**：①受测窗有限未复现、②菜单态有限通过+局内失败项开放（归因义务\n"
    "  保留）、③保持态。下一动作权在 Codex/用户（D-10 三裁）；异族探针审计已派（在途）。\n"
)
d = open(GOAL, "rb").read()
assert d.endswith(b"\n"), "anchor must end with newline"
assert d.count(b"\r\n") == 0, "anchor is LF; abort"
open(GOAL, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("APPENDED sha=", hashlib.sha256(open(GOAL, "rb").read()).hexdigest()[:16])
