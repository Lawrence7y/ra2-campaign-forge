# -*- coding: utf-8 -*-
"""下一步计划的确定性门禁（只读检查，不修改任何文件）。

用法：python -I -X utf8 lead/nextstep_plan_20261106/check_plan.py
退出码：0 = PASS；1 = 内容不合格；2 = 文件缺失/不可解析。
"""
import json
import os
import re
import sys

ROOT = os.getcwd()
PLAN_REL = "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md"
MAN_REL = "lead/nextstep_plan_20261106/manifest.json"

HEADINGS = ["## 0 结论", "## 1 盘面现状", "## 2 下一步工作项",
            "## 3 阻断与授权", "## 4 未覆盖与风险"]
FIELD_RE = re.compile(r"^[-*]\s*(目标|动作|依据|验收|授权|风险)\s*[:：]")
ITEM_RE = re.compile(r"^###\s+(N-\d+)\s+\S")

problems = []
hard = []

plan_path = os.path.join(ROOT, PLAN_REL)
man_path = os.path.join(ROOT, MAN_REL)

if not os.path.isfile(plan_path):
    hard.append("计划文件不存在: " + PLAN_REL)
if not os.path.isfile(man_path):
    hard.append("manifest 不存在: " + MAN_REL)
if hard:
    print("GATE FAIL (hard)")
    for p in hard:
        print("  - " + p)
    sys.exit(2)

text = open(plan_path, encoding="utf-8").read()
lines = text.splitlines()

try:
    man = json.load(open(man_path, encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    print("GATE FAIL (hard): manifest 不是合法 JSON: %r" % (exc,))
    sys.exit(2)

# 1. 五个必需小节
for h in HEADINGS:
    if not any(l.strip() == h for l in lines):
        problems.append("缺小节: " + h)

# 2. 工作项数量与字段完备
items = []          # [(id, start_index)]
for i, l in enumerate(lines):
    m = ITEM_RE.match(l.strip())
    if m:
        items.append((m.group(1), i))

if len(items) < 6:
    problems.append("工作项仅 %d 条，少于下限 6 条" % len(items))

if len(items) != len({i for i, _ in items}):
    problems.append("工作项编号有重复")

bounds = [start for _, start in items] + [len(lines)]
for k, (iid, start) in enumerate(items):
    block = lines[start:bounds[k + 1]]
    got = set()
    for bl in block:
        m = FIELD_RE.match(bl.strip())
        if m:
            got.add(m.group(1))
    missing = [f for f in ["目标", "动作", "依据", "验收", "授权", "风险"] if f not in got]
    if missing:
        problems.append("工作项 %s 缺字段: %s" % (iid, "、".join(missing)))

# 3. manifest 自身与被引用路径
declared_md = os.path.normpath(str(man.get("markdownPath") or "").replace("\\", "/"))
if declared_md != os.path.normpath(PLAN_REL):
    problems.append("manifest.markdownPath 不是 %s: %r" % (PLAN_REL, man.get("markdownPath")))

cited = man.get("citedPaths") or []
if not isinstance(cited, list) or len(cited) < 10:
    problems.append("manifest.citedPaths 少于 10 条")
else:
    missing_files = []
    for p in cited:
        q = str(p).replace("\\", "/").lstrip("/")
        if not os.path.isfile(os.path.join(ROOT, q)):
            missing_files.append(str(p))
    if missing_files:
        problems.append("citedPaths 有 %d 条不存在: %s" % (
            len(missing_files), "; ".join(missing_files[:15])))

ids_declared = [str(x) for x in (man.get("workItemIds") or [])]
ids_found = [i for i, _ in items]
if ids_declared != ids_found:
    problems.append("manifest.workItemIds 与正文不一致: 声明=%r 正文=%r"
                    % (ids_declared, ids_found))

# 4. 授权口径不得含糊
if "待用户" not in text and "需用户" not in text:
    problems.append("正文未出现「需用户 / 待用户」，授权口径缺失")
if len(text) < 4000:
    problems.append("正文仅 %d 字符，少于 4000" % len(text))

if problems:
    print("GATE FAIL")
    for p in problems:
        print("  - " + p)
    sys.exit(1)

print("GATE PASS")
print("  计划: %s (%d 字符)" % (PLAN_REL, len(text)))
print("  工作项: %d 条 (%s)" % (len(items), ", ".join(ids_found)))
print("  引用路径: %d 条，全部存在" % len(cited))
print("  小节: 5/5")
sys.exit(0)
