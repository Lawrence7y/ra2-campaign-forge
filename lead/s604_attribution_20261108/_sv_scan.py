# -*- coding: utf-8 -*-
# _sv_scan.py — 复核员扫描：探针禁用构造 + 回件越界短语（纯只读）
import re, os
BASE = r"D:\Project\ra2-campaign-forge"
def rd(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8")

probe = rd(os.path.join(BASE, "lead/s604_attribution_20261108/_sa_probe.py"))
BANNED = ["ctypes", "OpenProcess", "ReadProcessMemory", "SuspendThread", "MiniDump",
          "StackWalk", "inject", "hook", "gamemd", "ra2loader", "YURI", "taskkill",
          "subprocess", "win32api", "psutil", "pymem"]
print("[A] _sa_probe.py 禁用构造扫描（回件声称零采样代码/零真机）：")
hit = False
for w in BANNED:
    for i, ln in enumerate(probe.splitlines(), 1):
        if w.lower() in ln.lower():
            hit = True
            print("   命中 {!r} @line {}: {}".format(w, i, ln.strip()[:100]))
if not hit:
    print("   无命中（0/{} 个禁用词）".format(len(BANNED)))

rep = rd(os.path.join(BASE, "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md"))
PAT = ["应改", "该改", "应修正", "应修改", "建议修正", "须改", "需要修改", "应重算", "应更新台账", "台账应"]
print("[B] _sa_ATTRIBUTION_S604.md 越界短语扫描（命中行全文列出，供语境判断）：")
hit = False
for i, ln in enumerate(rep.splitlines(), 1):
    for w in PAT:
        if w in ln:
            hit = True
            print("   line {} [{}]: {}".format(i, w, ln.strip()[:120]))
            break
if not hit:
    print("   无命中")
