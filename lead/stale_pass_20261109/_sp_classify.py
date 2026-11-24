# -*- coding: utf-8 -*-
# 精确分类「门禁 exit=0 / PASS / 验证通过」类登记（紧口径）
# 只读，Python 不写文件
# 口径说明：
#   GATE_EXIT  = 行内出现 exit=0/EXIT=0（含 门禁实跑）
#   PASS_TOKEN = 行内出现独立大写 PASS 或 SELF_TEST = PASS 或 N/N PASS
#   VERIFY_OK  = 行内出现 验证通过 / 全绿 / 逐项通过 / 通过（且上下文是检验/门禁/自检，非「通过决议」）
#   GATE_LINE  = 行内出现「门禁 实跑」或「门禁 exit」
# 排除：只含「注入」「哨兵」「carrier」等与 PASS 无关的行；「授权边界」行。
import re, json

A = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
B = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

RE_EXIT = re.compile(r"(?:exit|EXIT|CL_EXIT|LINK_EXIT|final_exit)\s*=\s*0")
RE_PASS = re.compile(r"\bPASS\b|SELF_TEST\s*=\s*PASS|\d+/\d+\s*PASS")
RE_VERIFY = re.compile(r"验证通过|逐项通过|全绿|机械检查通过|全过|全.*?PASS|\d+/\d+\s*PASS")
RE_GATE = re.compile(r"门禁.{0,20}实跑|门禁.{0,20}exit|门禁.{0,20}复跑|门禁回归")
# 噪声：授权边界 / 真机趟 / 载体 / 注入（非坏输入注入的登记）/ 哨兵（非检验哨兵）
RE_NOISE = re.compile(r"授权边界|不授权|零真机|零注入|零采样|carrier|载体|探针注入|hook/MiniDump|故障注入|反例注入")

FOUR_NAMES = ["check_d27", "check_d29", "check_d30", "_rs_carrier_scan",
              "carrier_scan", "SELF_TEST", "REFSYNC_SCOPE_FIX"]

def classify(tag, p):
    with open(p, "rb") as f:
        lines = f.read().decode("utf-8", errors="replace").split("\n")
    rows = []
    for i, ln in enumerate(lines, 1):
        cats = []
        if RE_EXIT.search(ln): cats.append("EXIT0")
        if RE_PASS.search(ln): cats.append("PASS")
        if RE_VERIFY.search(ln): cats.append("VERIFY")
        if RE_GATE.search(ln): cats.append("GATE_RUN")
        if not cats: continue
        is_four = any(k in ln for k in FOUR_NAMES)
        is_noise = bool(RE_NOISE.search(ln))
        rows.append({"file": tag, "line": i, "cats": cats,
                     "is_four": is_four, "noise": is_noise, "text": ln})
    return rows

r = classify("PENDING", A) + classify("GOAL", B)

# 汇总
by_cat = {}
for c in ["EXIT0", "PASS", "VERIFY", "GATE_RUN"]:
    by_cat[c] = sum(1 for x in r if c in x["cats"])
four_rows = [x for x in r if x["is_four"]]
other_rows = [x for x in r if not x["is_four"]]
noise_rows = [x for x in r if x["noise"] and not x["is_four"]]

out = {
    "TOTAL_HITS": len(r),
    "BY_CAT": by_cat,
    "BY_FILE": {t: sum(1 for x in r if x["file"] == t) for t in ["PENDING", "GOAL"]},
    "FOUR_ROWS": four_rows,
    "FOUR_COUNT": len(four_rows),
    "OTHER_ROWS": other_rows,
    "OTHER_COUNT": len(other_rows),
    "NOISE_SUSPECT_OTHER": len(noise_rows),
}
print(json.dumps(out, ensure_ascii=False))
