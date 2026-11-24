# -*- coding: utf-8 -*-
"""Q02 字节探针：慢爬 vs 冻结调和 —— 两条免-inc 出口的单次代价与结构约束。
只读 gamemd.exe；零真机；stdout-only（落盘靠 shell 重定向）。
"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

OUT = []
def p(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s, flush=True)

eng = Engine()
p("== coverage ==", eng.coverage)
cov, nins, resync = eng.coverage
assert cov > 99.99 and nins == 1394120 and resync == 66, "engine self-cert FAIL"

def dump(lo, n, title):
    p("")
    p("== %s (0x%X..0x%X) ==" % (title, lo, lo + n))
    for va, b, m, o in eng.disasm(lo, n):
        p("  %08X  %-24s %s %s" % (va, b, m, o))

# ---------- 1. MLF 头：InGame 早退 + 焦点等待环 ----------
dump(0x55D360, 0x70, "MLF head: InGame early-out + focus-wait loop")

# ---------- 2. 冻结体：确认每迭代含 throttle ----------
dump(0x55D830, 0x50, "MLF frozen body 0x55D877 path")

# ---------- 3. 正常体尾：四旗标门 + inc + throttle 的相对位置 ----------
dump(0x55DE40, 0xA0, "MLF normal tail: four-flag gate -> inc -> throttle -> rets")

# ---------- 4. throttle 0x55E160：SP 分支与节流地板 ----------
dump(0x55E160, 0x40, "throttle 0x55E160 head")
dump(0x55E2A0, 0xB0, "throttle 0x55E160 SP branch + tail")
p("")
p("initial .data: [0x887328]=%08X [0x887330]=%08X [0x887348]=%08X [0x887350]=%08X" % (
    eng.u32(0x887328), eng.u32(0x887330), eng.u32(0x887348), eng.u32(0x887350)))

# ---------- 5. 消息泵 0x5D4D50 的全镜像调用点普查（第二通道判据） ----------
p("")
p("== census: call 0x5D4D50 (MessagePump) sites ==")
by = eng.by()
sites = []
for ins in eng.stream:
    if ins.mnemonic == "call":
        try:
            ops = ins.operands
            if ops and ops[0].type == 2 and ops[0].imm == 0x5D4D50:
                sites.append(ins.address)
        except Exception:
            pass
for va in sites:
    p("  call site %08X  in-normal-body[%s]  prev2=%s" % (
        va, "YES" if 0x55D878 <= va < 0x55DEE0 else "no",
        " | ".join("%08X %s" % (by[a].address, by[a].mnemonic)
                   for a in (va - 7, va - 5, va - 2) if a in by)))
p("pump call sites total: %d, inside MLF normal body [0x55D878,0x55DEE0): %d" % (
    len(sites), sum(1 for v in sites if 0x55D878 <= v < 0x55DEE0)))

p("")
p("== G_PUMPCNT 0xAA0430 accesses ==")
for va, rw, m, o in eng.disp_hits(0xAA0430):
    p("  %08X %s %s %s" % (va, rw, m, o))

# ---------- 6. throttle 0x55E160 的调用点普查 ----------
p("")
p("== census: call 0x55E160 (throttle) sites ==")
tsites = []
for ins in eng.stream:
    if ins.mnemonic == "call":
        try:
            ops = ins.operands
            if ops and ops[0].type == 2 and ops[0].imm == 0x55E160:
                tsites.append(ins.address)
        except Exception:
            pass
for va in tsites:
    p("  call site %08X (%s)" % (va, "frozen body" if va == 0x55D854 else
                                 "normal body" if va == 0x55DE9A else "other"))

# ---------- 7. 0x55CFD0 四旗标消费机：头部 + 四旗标读写点 ----------
dump(0x55CFD0, 0x60, "0x55CFD0 flag-state-machine head")
for g in (0xA8ECD0, 0xA83D49, 0x8B41C0, 0xA83D48):
    p("")
    p("== flag 0x%X: all accesses ==" % g)
    for va, rw, m, o in eng.disp_hits(g):
        loc = ("MLF-gate" if 0x55DE40 <= va < 0x55DE90 else
               "0x55CFD0" if 0x55CFD0 <= va < 0x55D360 else "elsewhere")
        p("  %08X %s %-6s %-28s [%s]" % (va, rw, m, o, loc))

# ---------- 8. reach_without 复核 + 0x55DEC8 尾字节 ----------
p("")
rets, _ = eng.func_rets(0x55D360, 0x55DEE0)
p("MLF rets:", [hex(r.address) for r in rets])
rw = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
p("rets reachable without inc-block:", [hex(r.address) for r in rets if r.address in rw])
p("bytes @0x55DEC8:", eng.rd(0x55DEC8, 0x14).hex())
p("bytes @0x55DECF..0x55DEE0:", eng.rd(0x55DECF, 0x11).hex())

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q02/Q02_bytes_probe_out.txt",
          "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
p("")
p("WROTE Q02_bytes_probe_out.txt")
