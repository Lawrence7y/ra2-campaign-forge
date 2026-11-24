# -*- coding: utf-8 -*-
# P04: 落空链回走 + 入边搜索 —— 独立于 E8 头集的第二套定界法（双验证）
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()
stream = eng.stream
starts = sorted(by)

WRITES = [0x52DA08, 0x55DE81, 0x5B7329, 0x5BB20C, 0x5E550F,
          0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C]

import bisect

def fall_chain_start(W):
    """从 W 沿『前驱指令落空到达』回走，直到断点(ret/jmp/未解码间隙)。返回链起点。"""
    a = W
    while True:
        if a not in by:
            return None
        # 找到落空到达 a 的最近指令起点
        i = bisect.bisect_left(starts, a) - 1
        if i < 0:
            return a
        b = starts[i]
        ins = by[b]
        if b + ins.size != a:
            return a                      # 无落空前驱（间隙/数据）→ a 即链头
        if ins.mnemonic in ("ret", "jmp", "leave") or ins.mnemonic.startswith("iret"):
            return a                      # 块边界 → a 是新块起点
        a = b

def branch_ins(t):
    """全镜像中跳入 t 的分支（jcc/jmp/call 立即数目标）。"""
    out = []
    for ins in stream:
        if ins.mnemonic[0] in "j" or ins.mnemonic == "call":
            try:
                if ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm == t:
                    out.append((ins.address, ins.mnemonic))
            except Exception:
                pass
    return out

for W in WRITES:
    S = fall_chain_start(W)
    if S is None:
        print("W=%#x 链断于未解码字节" % W)
        continue
    bi = branch_ins(S)
    # S 之前的落空前驱（若无 → S 无线性入口）
    i = bisect.bisect_left(starts, S) - 1
    lin_pred = None
    if i >= 0:
        b = starts[i]
        if by[b].address + by[b].size == S:
            lin_pred = b
    print("W=%#x  链头 S=%#x  落空前驱=%s  入边=%s" % (
        W, S,
        "%#x" % lin_pred if lin_pred else "无(S 即入口)",
        bi if bi else "无"))
