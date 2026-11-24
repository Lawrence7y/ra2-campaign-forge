# -*- coding: utf-8 -*-
# PASS 类登记分布统计（细分类别，互斥优先序）
# 只读，Python 不写文件
import re, json

A = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
B = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

# 互斥分类（按优先序）
# G_GATE   : 明确「门禁 实跑 exit=0」的裁决门禁登记（PENDING 6+1 行）
# G_FALSE  : 已自认假绿/不可信的 PASS（GOAL:261 verify_hooks 0/13）
# G_RUNNER : 离线测试/单测/自检 PASS（W5/W11/A1 等，逐项 N/N PASS）
# G_COMPILE: 编译/链接 exit=0（CL/LINK）
# G_EXIT   : 其它 exit=0（流程门槛、趟件 rc=0 等）
# G_PASS   : 其它 PASS / 全绿 / 验证通过 字样
RE_GATE = re.compile(r"门禁.{0,20}实跑.{0,40}exit\s*=\s*0|门禁\s+exit\s*=\s*0|门禁.{0,20}复跑.{0,20}PASS")
RE_FALSE = re.compile(r"假绿|假 PASS|不可信|0/13|13 槽完全失明")
RE_RUNNER = re.compile(r"\d+/\d+\s*PASS|PASS=\d+|FAIL=0|逐项通过|用例全 PASS|测试全绿|全绿")
RE_COMPILE = re.compile(r"CL_EXIT=0|LINK_EXIT=0|CL/CL2/LINK|编译.*exit=0")
RE_EXIT = re.compile(r"(?:exit|EXIT|final_exit|门槛)\s*=\s*0|rc=0|EXIT=0|EXIT = 0")
RE_PASS = re.compile(r"\bPASS\b|SELF_TEST|验证通过|机械检查通过|通过")
RE_NOISE = re.compile(r"授权边界|不授权|零真机|零注入|零采样|未 commit|未 push|探针注入|hook/MiniDump|故障注入|反例注入|载体|carrier")

def classify(tag, p):
    with open(p, "rb") as f:
        lines = f.read().decode("utf-8", errors="replace").split("\n")
    rows = []
    for i, ln in enumerate(lines, 1):
        c = None
        if RE_GATE.search(ln): c = "GATE_EXIT0"
        elif RE_FALSE.search(ln): c = "KNOWN_FALSE_PASS"
        elif RE_RUNNER.search(ln): c = "TEST_SUITE_PASS"
        elif RE_COMPILE.search(ln): c = "COMPILE_EXIT0"
        elif RE_EXIT.search(ln): c = "OTHER_EXIT0"
        elif RE_PASS.search(ln): c = "OTHER_PASS_WORD"
        if c and not (RE_NOISE.search(ln) and c in ("OTHER_PASS_WORD", "OTHER_EXIT0")):
            rows.append({"file": tag, "line": i, "cat": c, "text": ln})
    return rows

rows = classify("PENDING", A) + classify("GOAL", B)
from collections import Counter, defaultdict
by_cat = Counter(x["cat"] for x in rows)
by_file = defaultdict(Counter)
for x in rows: by_file[x["file"]][x["cat"]] += 1
out = {
    "TOTAL": len(rows),
    "BY_CAT": dict(by_cat),
    "BY_FILE": {k: dict(v) for k, v in by_file.items()},
    "GATE_ROWS": [x for x in rows if x["cat"] == "GATE_EXIT0"],
    "KNOWN_FALSE_ROWS": [x for x in rows if x["cat"] == "KNOWN_FALSE_PASS"],
}
print(json.dumps(out, ensure_ascii=False, indent=1))
