# -*- coding: utf-8 -*-
"""N-8 残项收口 · 第 7 项：GOAL 是否存在比 :9757 更新的节（NEXT_STEPS_20261106.md:80
「当前最新节号未验不作依据」）。

核对：总行数、:9757 是否为末行、最后一个/最大的「## §N」节头、末尾有无更多内容。
只读；唯一写域 = 本脚本同目录 _n8r_item7_goaltail_out.txt。零真机、零采样代码。
"""
import hashlib
import io
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
GOAL = os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


b = open(GOAL, "rb").read()
P("[H] 被核对象 = lead/GOAL_THREE_TARGETS_20261018.md")
P("    SHA256 = %s" % hashlib.sha256(b).hexdigest())
P("    字节数 = %d" % len(b))
P("    （编排方指纹 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede / 759518 → %s）"
  % ("SAME" if hashlib.sha256(b).hexdigest() ==
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede" and
     len(b) == 759518 else "DIFF"))

text = b.decode("utf-8")
lines = text.split("\n")
# 常规行计数（与 wc -l 一致：按 \n 计）
n_nl = b.count(b"\n")
P("")
P("[L] \\n 计数 = %d（wc -l 口径）；split 后片段 = %d（末片段 %s）"
  % (n_nl, len(lines), "为空=文件以换行结尾" if lines[-1] == "" else "非空=" + repr(lines[-1][:40])))
last_line_no = n_nl if lines[-1] == "" else len(lines)
P("    末行行号 = :%d，内容 = %r" % (last_line_no, lines[last_line_no - 1]))

P("")
P("[S] 「## §N」节头全表（末 5 个）")
sec = []
for i, ln in enumerate(lines[:last_line_no], 1):
    m = re.match(r"^## §(\d+)", ln)
    if m:
        sec.append((i, int(m.group(1)), ln[:80]))
for i, n, ln in sec[-5:]:
    P("    :%d  §%d  %s" % (i, n, ln))
mx = max(sec, key=lambda x: x[1])
P("    最大的「## §N」节号 = §%d @ :%d；共 %d 个「## §」节头" % (mx[1], mx[0], len(sec)))

P("")
P("[T] 末尾区段（:9687 起的 §604 节内最后 6 行）")
for i in range(last_line_no - 5, last_line_no + 1):
    P("    :%d  %s" % (i, lines[i - 1]))

P("")
P("[Q] 是否存在 :9757 之后的内容：")
P("    总行数 = %d，末行 = :%d → :9757 之后 %s" %
  (last_line_no, last_line_no,
   "无任何行（:9757 即 EOF 前最后一行）" if last_line_no == 9757 else "存在，见上"))

P("")
P("[X] 行内 §9[0-9][0-9] 引用（非节头，附注）")
for i, ln in enumerate(lines[:last_line_no], 1):
    if re.search(r"§9\d\d", ln):
        P("    :%d  %s" % (i, ln.strip()[:90]))

P("")
P("N8R_ITEM7 DONE")

io.open(os.path.join(HERE, "_n8r_item7_goaltail_out.txt"), "w", encoding="utf-8").write(
    "\n".join(OUT) + "\n")
print("\n".join(OUT))
