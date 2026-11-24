# -*- coding: utf-8 -*-
"""Q2 探索探针 v1 —— 反汇编窗口 + 覆盖率自证 + 字节读取（只读；stdout 由 shell 重定向落盘）"""
import sys, time, hashlib
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine


def P(*a):
    print(" ".join(str(x) for x in a))


t0 = time.time()
e = Engine()
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXC = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"

raw_exe = open(EXE, "rb").read()
raw_exc = open(EXC, "rb").read()
P("EXE sha256 =", hashlib.sha256(raw_exe).hexdigest(), "bytes =", len(raw_exe))
P("EXC sha256 =", hashlib.sha256(raw_exc).hexdigest(), "bytes =", len(raw_exc))
P("Engine.sha =", e.sha, "IB =", hex(e.IB))
P("SEC table:", [(n, hex(a), hex(v), hex(rp), hex(rs)) for (n, a, v, rp, rs) in e.SEC])
P(".text TLO/THI/TSZ =", hex(e.TLO), hex(e.THI), hex(e.TSZ))

cov, cnt, resync = e.coverage
P("COVERAGE =", "%.4f" % cov, "insns =", cnt, "resync_fails =", resync)
by = e.by()
P("by() keys =", len(by), "build_seconds =", "%.2f" % (time.time() - t0))

target = 0x7CFC9F
P("target in by() =", target in by)
P("bytes @0x7CFC9F (rd 32) =", e.rd(target, 32).hex(" ").upper())

LO, HI = 0x7CFA80, 0x7CFE80
addrs = sorted(a for a in by if LO <= a < HI)
P("=== resync instruction starts in [%s,%s) : %d ===" % (hex(LO), hex(HI), len(addrs)))
for a in addrs:
    ins = by[a]
    b = e.rd(a, ins.size).hex(" ").upper()
    P("%08X  %-18s  %s %s" % (a, b, ins.mnemonic, ins.op_str))

P("=== elapsed =", "%.2f" % (time.time() - t0))
