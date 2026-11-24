# -*- coding: utf-8 -*-
# _fgR2_selfcheck.py —— R2_FINAL_GRADE.md 门禁等价自检 + 本件指纹实算（只读；stdout 输出）
# 检查项与工作流 GATE_CODE 对齐：六节「## 1..6」、八要素、禁用词、SHA256 绑定行正则。
import hashlib, re

DOC = r"D:\Project\ra2-campaign-forge\lead\r2_final_grade_20261108\R2_FINAL_GRADE.md"
with open(DOC, "rb") as f:
    b = f.read()
t = b.decode("utf-8")

problems = []
for s in ["## 1", "## 2", "## 3", "## 4", "## 5", "## 6"]:
    if s not in t:
        problems.append("缺小节 " + s)
for k in ["维度 A", "维度 B", "维度 C", "维度 D", "升格", "阻塞项", "未验", "不选判据"]:
    if k not in t:
        problems.append("缺要素 " + k)
for bad in ["gamemd.exe", "ra2loader", "taskkill"]:
    if bad in t:
        problems.append("含禁用词 " + bad)
bindings = re.findall(r"被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?", t)
if not bindings:
    problems.append("缺 SHA256 绑定行")

print("GATE_OK =", (not problems))
print("problems =", problems)
print("bindings =", len(bindings))
for h in bindings:
    print("  binding:", h)
print("R2_FINAL_GRADE.md SHA256 =", hashlib.sha256(b).hexdigest())
print("R2_FINAL_GRADE.md bytes  =", len(b))
