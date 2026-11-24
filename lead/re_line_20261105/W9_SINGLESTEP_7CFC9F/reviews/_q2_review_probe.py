# -*- coding: utf-8 -*-
"""独立复核员 Q2 自跑探针（只读二进制 / 仓内文件；零真机）。
写入唯一写域 reviews/。独立于 _w9_q2.py 重新计算。
"""
import sys, os, hashlib, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXC = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003",
                   "lead", "boot_hang_triage_20261018",
                   "EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")

def P(*a):
    print(" ".join(str(x) for x in a), flush=True)

def hx(b):
    return b.hex(" ").upper()

# ---- 1. 两个 SHA256 + 字节数（自算）----
exe_raw = open(EXE, "rb").read()
exc_raw = open(EXC, "rb").read()
P("[SHA] gamemd.exe sha256=", hashlib.sha256(exe_raw).hexdigest(), "bytes=", len(exe_raw))
P("[SHA] EXCEPT    sha256=", hashlib.sha256(exc_raw).hexdigest(), "bytes=", len(exc_raw))

# ---- 2. Engine 自证 ----
e = Engine()
P("[ENGINE] sha=", e.sha, "IB=", hex(e.IB), "TLO/THI/TSZ=",
  hex(e.TLO), hex(e.THI), hex(e.TSZ))
cov, nins, nf = e.coverage
P("[ENGINE] COVERAGE=%.12f%% insns=%d resync_fails=%d" % (cov, nins, nf))
by = e.by()

# ---- 3. 目标 EIP 字节 + 指令归属 ----
T = 0x7CFC9F
P("[TARGET] in by()=", T in by, "rd(32)=", hx(e.rd(T, 32)))
P("[TARGET] disasm(32)=", [(hex(a), b, m, o) for a, b, m, o in e.disasm(T, 32)][:8])

# ---- 4. 序言 / 前一函数尾 ----
H = 0x7CFB13
P("[PROLOG] rd(0x7CFB12,10) =", hx(e.rd(0x7CFB12, 10)))
P("[PROLOG] rd(0x7CFB13,5)  =", hx(e.rd(H, 5)))
P("[PROLOG] disasm(0x7CFB13,0x10)=",
  [(hex(a), b, m, o) for a, b, m, o in e.disasm(H, 0x10)])
P("[PROLOG] prev-epilogue in by()=",
  [(hex(a), by[a].mnemonic, by[a].op_str) for a in range(H - 6, H) if a in by])

# 上一个 ret 是否在 (0x7CFB13, 0x7CFC9F) 之间：找反例
between_rets = [a for a in sorted(by) if H < a < T and by[a].mnemonic.startswith("ret")]
P("[PROLOG] ret insn starts in (0x7CFB13,0x7CFC9F) =", [hex(a) for a in between_rets])

# 全流中直接 call/jmp 立即数目标 == 0x7CFB13（交叉验证入口）
xrefs = []
for a, ins in by.items():
    try:
        if ins.operands and ins.operands[0].type == 2:
            if ins.operands[0].imm == H and (ins.mnemonic.startswith("j") or ins.mnemonic == "call"):
                xrefs.append((a, ins.mnemonic, hx(bytes(ins.bytes))))
    except Exception:
        pass
P("[PROLOG] direct call/jmp xrefs to 0x7CFB13 =", len(xrefs),
  [(hex(a), m, b) for a, m, b in sorted(xrefs)])

# ---- 5. 函数界 [0x7CFB13, 0x7CFE1C) ----
LO, HI = 0x7CFB13, 0x7CFE1C
addrs = sorted(a for a in by if LO <= a < HI)
P("[BOUND] instruction count in [0x7CFB13,0x7CFE1C) =", len(addrs))
gaps = [(a, by[a].size, addrs[i+1]) for i, a in enumerate(addrs[:-1])
        if a + by[a].size != addrs[i+1]]
P("[BOUND] gaps (end != next start) =", gaps[:10], "count=", len(gaps))
P("[BOUND] first/last =", hex(addrs[0]), hex(addrs[-1]),
  "last_end=", hex(addrs[-1] + by[addrs[-1]].size))
P("[BOUND] length = 0x%X = %d B" % (HI - LO, HI - LO))
P("[BOUND] TARGET offset = +0x%X = +%d B" % (T - LO, T - LO))
rets = [a for a in addrs if by[a].mnemonic.startswith("ret")]
P("[BOUND] ret insns in window =", [(hex(a), hx(e.rd(a, by[a].size))) for a in rets])
fr, _ = e.func_rets(LO, HI)
P("[BOUND] e.func_rets(0x7CFB13,0x7CFE1C) =", len(fr),
  [(hex(r.address), r.mnemonic, hx(e.rd(r.address, r.size))) for r in fr])
fr2, _ = e.func_rets(LO, 0x7D0113)
P("[BOUND] e.func_rets(0x7CFB13,0x7D0113) =", len(fr2), [hex(r.address) for r in fr2])

# 全部 C3 字节偏移 vs 指令起始
c3_all = [a for a in range(LO, HI) if e.rd(a, 1) == b"\xC3"]
P("[BOUND] offsets whose byte == C3 =", [hex(a) for a in c3_all])
P("[BOUND] of those, in by() =", [hex(a) for a in c3_all if a in by])
for a in c3_all:
    if a not in by:
        owner = max((x for x in addrs if x <= a), default=None)
        if owner is not None:
            P("[BOUND]   C3@%s inside insn @%s %s %s bytes=%s"
              % (hex(a), hex(owner), by[owner].mnemonic, by[owner].op_str,
                 hx(e.rd(owner, by[owner].size))))

# 下一函数起点 + 尾声
P("[BOUND] rd(0x7CFE1C,8) =", hx(e.rd(HI, 8)), "in by()=", HI in by,
  "insn=", (by[HI].mnemonic, by[HI].op_str) if HI in by else None)
P("[BOUND] epilogue =", [(hex(a), hx(e.rd(a, by[a].size)), by[a].mnemonic, by[a].op_str)
                         for a in addrs if a >= 0x7CFE11])

# 内部 call/jmp 立即数目标越界（找反例：函数是否还有别的出口）
outgoing = []
for a in addrs:
    ins = by[a]
    if ins.mnemonic.startswith("j") or ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2:
                t = ins.operands[0].imm
                if not (LO <= t < HI):
                    outgoing.append((a, ins.mnemonic, hex(t)))
        except Exception:
            pass
P("[BOUND] jmp/call imm targets outside window =", len(outgoing),
  [(hex(a), m, t) for a, m, t in outgoing])

# ---- 6. EXCEPT 件头部 Bytes at CS:EIP 与磁盘字节比对 ----
txt = exc_raw.decode("utf-8", "replace").splitlines()
P("[EXCEPT] lines 1-17:")
for i, ln in enumerate(txt[:17], 1):
    P("   L%d: %s" % (i, ln))
eip_line = next((ln for ln in txt if "Bytes at CS:EIP" in ln), None)
P("[EXCEPT] EIP line =", eip_line)
