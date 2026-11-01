# -*- coding: utf-8 -*-
"""_append_492.py - append S492 (B2 model switch per 482) to shared ledgers. Additive only."""


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


S492 = """

# §492　B2 换模型序执行（§482「十次之后还不行就换模型」）：dfmodel 四次 auth_failed（epoch 4/10）定性为
#        **确定性登录死亡**（每次 resume 数分钟内失效，非瞬态）⇒ 提前触发换模型（偏离字面 4<10 的理由入账）；
#        新 run `dwfrun-45924235` = **GLM start-plan 同族标注版**

- **偏离字面理由**：auth_failed 系确定性失败（无用户重登录则成功概率=0），重连 5-10 为零进展空耗；
  §482 十次上限的意图=防瞬态过早放弃，非要求对确定性失败空转。如用户判需补满十次，dfmodel resume
  路径保持一条命令可达。
- **同族合规**：新判定书=**同族标注版（GLM，非异族）**——persona/ask 强制族属声明行+familyLabel 字段；
  **不以同族冒充异族**（用户规则）；正式异族判定书留待 dfmodel 通道恢复后可补（resume 路径不变）。
- **续办纪律**（写入 ask）：前任 dfmodel 八探针 p01-p08+_raw 逐支配对读毕、能续办不重做、标注前任产物
  vs 亲验、错误点名；至少亲验 2 支承重探针（建议 p01/p03）。
- **B2 对账实质不变**：②趟全主张/①两趟 §487 主张/q r 张力/Δ n=14/§485-487 审计——证据面（八探针
  stdout）客观在盘，族属变化影响的是「独立判断层」的可信度标注，不是证据本身。
- 句态不变；趟数 34。待 typed ⇒ §493 回收。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S492)
b = append_lines(GOAL, S492)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
