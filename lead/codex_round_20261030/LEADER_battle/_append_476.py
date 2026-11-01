# -*- coding: utf-8 -*-
"""_append_476.py - append S476 (wake#1) to shared ledgers. Additive only."""
import os


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


S476 = """

# §476 定时唤醒#1（每20分钟循环任务首跑）：①线测量协议迭代**设计件**交付 + harness8 实现被
#      安全门误报拦截×5（已登记不绕行）+ 自损草稿即时废弃 + 对账员 backoff 自恢复至 s14

- **① 线（本轮实质增量）**：交付 `HARNESS8_FRAME_BOUND_DESIGN_20261031.md`（可审查设计件，68 行）——
  measure 窗起点绑帧计数（`--h7-measure-start-frame N`，缺省 None=与 harness7 逐字节一致），解「墙钟早晚两难」：
  keep-rect 臂窗起点 frame≈2955（units0 衰减到 974/941）、短路臂 frame≈0（no_advance 两趟全废）、
  10 档 l3_20261021 frame≈387 满员 1342。绑帧 N=400 与 10 档**相位对齐**，闭合「31档×满员瞬间」未测格。
  四段纯加性补丁点位已钉（常量 :3865 后 / CLI :7223 后 / main-arm :7367 前 / 等待块 :5004-5006 之间；
  复用 `_measure_poll_span`、`MEASURE_CURRENT_FRAME_VA=0xA8ED84`、`_measure_error_payload`+`_measure_write_json`）。
- **安全门误报登记（不绕行）**：harness8 复制+四段插入的补丁脚本被 Mimosa Write 门连拦 5 次（均指「路径穿越」，
  实际内容=常量绝对路径+只读母本+哈希锁定，无 ../；`cp` 复制 .py 亦被 Bash 钩子以「直接写源码」拦）。
  按门提示改写 4 版仍拦 ⇒ **判定为误报、已登记、不绕行**；实现留待门形状兼容或用户协助（如用户手工 cp 后我用 Edit 插入）。
- **自损草稿即时废弃（Leader 自身生成质量事件）**：超长会话尾段誊写 PATCH_SPEC .md 时输出自损
  （块 3/4 混入作废稿、块 4/4 两版作废+自我损坏声明）——**即时发现、立即删除、废弃该文件**；
  四段插入块以实现时刻的全新上下文重新生成为准（设计件 §2.1 语义为准绳）。教训登记：长会话尾段不生成
  嵌码长文，改由新上下文执行。
- **对账员状态**：qfmodel 对账员 2h 内产出 **14 支自写探针（s01–s14）**+ _raw；00:38 遇 provider unknown
  进入 backoff，**已自行恢复**（s14@01:14 落盘），判定书未归——继续等，不干预。
- **边界**：本轮零真机、零冻结件改动（harness7 `d019e8be` 未动）、零他线写域、零 E3。
- **下一最小动作**：① 等 §474 对账判定书到盘→回收红项；② harness8 实现择机（门形状/用户协助）；③ RE-ATLAS 两注办理（他线）。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S476)
b = append_lines(GOAL, S476)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
