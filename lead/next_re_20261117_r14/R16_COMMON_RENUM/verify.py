# -*- coding: utf-8 -*-
"""R16-COMMON-RENUM 可复跑验证脚本。
用法: python verify.py
校验 R14_COMMON.md 的两处改动、重号统计与还原性。
"""
import sys, hashlib, re

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
DOC = ROOT + r"\R14_COMMON.md"
CARD = ROOT + r"\_cards\R16-COMMON-RENUM.md"

H0 = "b23cd2e8bedfff08910e967a19d4cc258cc46f51304908da37329c525e6e3551"  # 改前
H3 = "2aa32cc23a2b3c236e2ccdd72c50878734b808250c8fabf1828bed7ae88ca36a"  # 改后

old_title = "### §12.4 【COMMON-R16 追加，2026-11-20】D-47 裁决 —— D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位"
new_title = "### §12.6 【COMMON-R16 追加，2026-11-20】D-47 裁决 —— D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位"

data = open(DOC, "rb").read()
card_lines = open(CARD, "rb").read().splitlines()
expect_ins = card_lines[44]  # 卡面第 45 行 = 待插入行（权威原文）

# 行号按 \n 计数（与 grep / 任务卡一致）；混合行尾下不用 splitlines()
dl = data.split(b"\n")
def dstr(b): return b.decode("utf-8", "replace")

ok = True
def check(name, cond, extra=""):
    global ok
    print(("PASS" if cond else "FAIL") + " | " + name + (" | " + extra if extra else ""))
    if not cond:
        ok = False

cur = hashlib.sha256(data).hexdigest()
check("改后 sha256 == H3", cur == H3, cur)
check("改后字节数 == 230242", len(data) == 230242, str(len(data)))

nb = new_title.encode("utf-8"); ob = old_title.encode("utf-8")
check("标题 §12.6 恰 1 处", data.count(nb) == 1, "count=%d" % data.count(nb))
check("旧标题 §12.4【COMMON-R16】0 处", data.count(ob) == 0, "count=%d" % data.count(ob))

a14 = [(i, s) for i, l in enumerate(dl, 1) for s in [dstr(l)]
       if re.match(r"^#+ .*12\.4", s)]
a16 = [(i, s) for i, l in enumerate(dl, 1) for s in [dstr(l)]
       if re.match(r"^#+ .*12\.6", s)]
check("标题型 12.4 恰 1 处（L1216）", len(a14) == 1 and a14[0][0] == 1216,
      repr(a14))
check("标题型 12.6 恰 1 处（L1558）", len(a16) == 1 and a16[0][0] == 1558,
      repr(a16))

ins_b = expect_ins + b"\n"
check("插入行恰 1 处且与卡面第45行字节一致",
      data.count(expect_ins) == 1, "count=%d bytes=%d" % (data.count(expect_ins), len(expect_ins)))
check("插入行位于 L1377", dl[1376] == expect_ins,
      repr(dstr(dl[1376])[:60]))

# 还原性：撤销两处改动
anchor = "### 13.4 待裁项 **D-47**：D-43(A) 与 §12.3 正面冲突（未解）\n\n".encode("utf-8")
rev = data.replace(nb, ob, 1).replace(anchor + ins_b, anchor, 1)
hr = hashlib.sha256(rev).hexdigest()
check("还原性：撤销两处 == H0", hr == H0, hr)

print("----")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
