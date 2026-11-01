# -*- coding: utf-8 -*-
"""_append_503.py - append S503 (user-ruled erratum + A'' approval) to shared ledgers. Additive only."""


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


S503 = """

# §503　用户勘误与 A'' 批准（2026-11-01；追加式，§502 原文不静默改写）

- **勘误（§502 三句态改为）**：
  - ① **「周期性停滞与 BOOT 会话显著相关；单位数量单独不足以解释现象，因果机制未闭合」**
    （原 §502「判别单元=BOOT 确立」表述过强——相关≠因果，机制未闭合）；
  - ② 正常退出硬门槛未达成、RC-4 不收口（不变）；
  - ③ 保持态，**回归义务继续**（新增：后续候选/实验须保留对既有结论的回归核验）。
- **A'' 批准（重启干预方向）**，执行协议（用户原文要点全收）：
  - 先离线准备；**用户重启并告知后**方按既有授权边界串行真机；**不得自行重启机器**；E3 仍未授权；
  - 主会话+子代理并行：A=独立复算停滞判据（原始 (t,frame) 序列；明确加载/活动战斗/终局/无推进/
    读失败/采样缺口分类；检查首尾截断；解释低 fps 但零停滞的窗口）；B=逐趟 BOOT 证据表
    （BOOT 身份来源与可信度；**日期不能直接充当 BOOT 身份**；核对地图/二进制/配置/协议/速度/分辨率/
    有效战斗阶段）；主会话=重启前后对照卡片+环境快照+v4 冻结锚与执行路径核查；
  - 重启实验：尽量取得重启前同协议有效基线（无则明确为历史对照）；地图/配置/候选/采样参数/判据
    全不变；重启前后记录 BOOT 身份/运行时长/后台环境/实际采样节律；首跑沿用 v4；到不了目标帧或
    缺有效战斗窗 ⇒ 只报相应轨迹、**不得算「卡顿消失」**；不同时改轮询率/观察时长/负荷（确需改独立登记）；
    单趟=筛查，补趟由信息量决定，不无界加样；
  - 结果口径：新 BOOT 改善 ⇒ 支持「重启相关环境变化可能缓解」（待重复与持续性验证，**不得称修复完成**）；
    仍停滞 ⇒ 本次重启未消除（**不得直接判持久软件态**）；无有效窗/采样失效 ⇒ 无结论；重启暂时缓解
    **不改变 RC-4 状态**；
  - 冻结件不改、零新增 Hook、零主动状态写、子代理不启动游戏；真机后由不同上下文复算原始轨迹再更新
    三目标状态。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S503)
b = append_lines(GOAL, S503)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
