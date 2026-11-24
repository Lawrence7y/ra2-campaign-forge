# -*- coding: utf-8 -*-
# 扫描两台账：四件门禁相关行 + 所有 PASS / exit=0 / 验证通过 类登记
# 只读，绝不改台账。Python 内不写任何文件，结果走 stdout。
import re, json

A = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
B = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

FOUR = ["check_d27", "check_d29", "check_d30", "_rs_carrier_scan",
        "carrier_scan", "SELF_TEST", "REFSYNC_SCOPE_FIX"]

PAT = [
    r"exit\s*=\s*0", r"EXIT\s*=\s*0", r"exit0",
    r"\bPASS\b", r"通过", r"验证通过", r"机械检查通过",
    r"门禁.*?(?:PASS|通过|exit)", r"(?:PASS|通过|exit).*?门禁",
    r"SELF_TEST", r"实跑", r"复跑", r"逐项通过", r"全.*?PASS",
]

def scan(tag, p):
    with open(p, "rb") as f:
        data = f.read()
    lines = data.decode("utf-8", errors="replace").split("\n")
    four = []
    passes = []
    for i, ln in enumerate(lines, 1):
        if any(k in ln for k in FOUR):
            four.append({"file": tag, "line": i, "text": ln})
        if any(re.search(x, ln) for x in PAT):
            passes.append({"file": tag, "line": i, "text": ln})
    return {"tag": tag, "nlines": len(lines), "four": four, "passes": passes}

ra = scan("PENDING", A)
rb = scan("GOAL", B)
out = {
    "FOUR_HITS": ra["four"] + rb["four"],
    "FOUR_HITS_COUNT": len(ra["four"]) + len(rb["four"]),
    "FOUR_BY_FILE": {"PENDING": len(ra["four"]), "GOAL": len(rb["four"])},
    "PASS_HITS": ra["passes"] + rb["passes"],
    "PASS_HITS_COUNT": len(ra["passes"]) + len(rb["passes"]),
    "PASS_BY_FILE": {"PENDING": len(ra["passes"]), "GOAL": len(rb["passes"])},
    "LINE_COUNTS": {"PENDING": ra["nlines"], "GOAL": rb["nlines"]},
}
print(json.dumps(out, ensure_ascii=False, indent=1))
