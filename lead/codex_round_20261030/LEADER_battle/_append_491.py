# -*- coding: utf-8 -*-
"""_append_491.py - append S491 (B2 stop #2, durable login ask) to shared ledgers. Additive only."""


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


S491 = """

# §491　B2 第二次 provider 截停（同因 auth_failed；resume 后 ~40min 内 p08 落盘后 token 再失效）
#        ⇒ **登录态不稳定（flapping）**；§482 计 epoch 2/10；本轮不再自动恢复，待用户持久重登录后一次续跑

- **状态**：run `dwfrun-453c97dc` stop #2（同 §490 因）；探针 **8 支**（+p08_a8_live 02:11）+ _raw 全在盘；
  判定书仍未落盘；journal 完整，恢复成本不变（只重跑撰写段）。
- **处置**： Leader 停止自动 resume（避免撰写段反复被截）；**待用户确认已持久登录 new-provider-3**
  ⇒ ResumeWorkflowRun 一次 ⇒ 判定书 ⇒ §492 回收。若 dfmodel 登录无法持久：异族白名单事实耗尽
  （qfmodel 已撤、GLM=执行同族不冒充）⇒ 按政策停下报用户裁决（B2 剩余=纯撰写段，探针证据已足）。
- 句态不变；趟数 34。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S491)
b = append_lines(GOAL, S491)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
