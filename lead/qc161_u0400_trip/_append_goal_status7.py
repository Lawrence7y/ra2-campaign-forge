# -*- coding: utf-8 -*-
# GOAL anchor 收口更新⑦ — batch+repeat+early-close results, claims graded.
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BLOCK = (
    "\n"
    "### 收口更新⑦（D-10 批准批+重复批+早窗定因批执行完毕：趟数 7→19，台账 §450–§453）\n"
    "\n"
    "- **② 观察成立**：六臂+重复共 9 趟探针判器 **11/11×9 全绿**；早窗 3 趟按其单趟\n"
    "  协议**手工核验**（投递 True/0×3、a8=PASS、载体删、except 恒、timeline 全量、证据/\n"
    "  清扫零错——判器 C6/C9 不适用早窗 schema，未冒充 11/11）；0 弹框/0 交互/0 泄漏。\n"
    "  异族判读 XVERIFY_BATCH6 在途（后到证据已投），到盘前以下均为**单线读数·候选方向**：\n"
    "  ①P0/P0N 隐形僵尸（原版清窗不清逻辑、frame 全程推进，2/2）；\n"
    "  ②守卫臂 frame 终停不可逆（停点漂移 47–113 s，2/2）；\n"
    "  ③exitstate 闩 1 只在早窗（关窗时机=菜单矛盾活变量，驱动代际被排除——v2 组件\n"
    "    复现旧 MAIN 自然退形态）；c″ 机制解释在早窗路径运行期成立 2/3；\n"
    "  ④**新硬问题：latched-hang 1/3**（闩住后 bail 未兑现挂死 101.7 s）⇒「正常退」\n"
    "    在最有利路径亦非 100%，收口前需早窗加样 n≥5 判真率+竞态区分实验（侵入性另裁）。\n"
    "- **①**：本会话 7 战斗趟（P0/P0N/P1/P2/P3+P0r/P1r）帧钟 30.97–31.47、窗内\n"
    "  无卡顿事件记录；5 菜单/早窗趟 frame=0 不适用 fps；未延长、未开优化实验（仍无靶）。\n"
    "- **③**：v2 全程零改动（终钉 6afe2711 批前后双复验；闸翻两次均逐字节还原复验）；\n"
    "  新件 `_drive_c2_x_earlyclose.py`（import 复用纪律+自带上报闸）；无扩 Hook/无部署/\n"
    "  无历史改写。外层提交钩子未碰（裁决§六）。\n"
    "- **下一动作**=等 BATCH6 判定书对账（含 latched-hang 定性）→ 红项处理 →\n"
    "  早窗加样/竞态区分实验设计提交裁决；RC-4 未收口不宣布。\n"
)
d = open(GOAL, "rb").read()
assert d.endswith(b"\n") and d.count(b"\r\n") == 0, "anchor LF"
open(GOAL, "ab").write(BLOCK.encode("utf-8"))
import hashlib
print("APPENDED sha=", hashlib.sha256(open(GOAL, "rb").read()).hexdigest()[:16])
