# -*- coding: utf-8 -*-
"""Q05 勘误清单核验脚本 v1：MLF 头尾 + 写点普查 + 门控结构。只读 gamemd.exe。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== S1 self-cert ==")
print("sha256:", eng.sha)
print("coverage: %.6f%% / %d insns / %d resync" % eng.coverage)

def dis(va, n, tag):
    print("-- %s @0x%X --" % (tag, va))
    for a, b, m, o in eng.disasm(va, n):
        print("  0x%08X: %-22s %s %s" % (a, b, m, o))

def rdhex(va, n):
    print("  raw 0x%08X: %s" % (va, eng.rd(va, n).hex(" ")))

print("\n== S2 MLF head 0x55D360..0x55D480 ==")
dis(0x55D360, 0x120, "MLF_head")

print("\n== S3 Sleep-loop backedges in [0x55D360,0x55D880) ==")
for va, tgt, mn in eng.loop_backedges(0x55D360, 0x55D880):
    print("  backedge: 0x%08X %s -> 0x%08X" % (va, mn, tgt))

print("\n== S5b GameMode==0 branch 0x55D767..0x55D8C0 ==")
dis(0x55D767, 0x159, "gm0_branch")

print("\n== S5 suspension gate 0x55D860..0x55D8C0 ==")
dis(0x55D860, 0x60, "susp_gate")

print("\n== S6 MLF tail 0x55DE30..0x55DEE0 ==")
dis(0x55DE30, 0xB0, "MLF_tail")

print("\n== S8 write/read census [0xA8ED84] (stream) ==")
hits = eng.disp_hits(0xA8ED84)
print("total stream hits:", len(hits))
for va, k, m, o in hits:
    if k == "W":
        print("  W 0x%08X: %s %s" % (va, m, o))
ws = [h for h in hits if h[1] == "W"]
print("W count:", len(ws))
print("R count:", len(hits) - len(ws))

print("\n== S9 census [0xA8ED80] (stream) ==")
h2 = eng.disp_hits(0xA8ED80)
print("total:", len(h2))
for va, k, m, o in h2:
    if k == "W":
        print("  W 0x%08X: %s %s" % (va, m, o))

print("\n== S10 raw moffs census '84 ED A8 00' image-wide ==")
# file-offset -> VA inverse
SEC = eng.SEC
pat = bytes.fromhex("84EDA800")
cnt = 0
ctx = {}
pos = 0
raw = eng.raw
while True:
    i = raw.find(pat, pos)
    if i < 0:
        break
    va = None
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= i < rp + rsz:
            va = sva + (i - rp)
            break
    pos = i + 1
    if va is None:
        continue
    cnt += 1
print("raw occurrences:", cnt)

print("\n== S11 census [0xA8E9A0] near MLF head (first 6) ==")
h3 = eng.disp_hits(0xA8E9A0)
print("total:", len(h3))
for va, k, m, o in h3[:6]:
    print("  %s 0x%08X: %s %s" % (k, va, m, o))

print("\n== S12 0xA8E2E4 / 0x69A300 / cmp zone ==")
print("u32(0xA8E2E4) initial =", hex(eng.u32(0xA8E2E4)))
h4 = eng.disp_hits(0xA8E2E4)
print("disp_hits(0xA8E2E4):", [(hex(a), k, m, o) for a, k, m, o in h4])
print("rd(0x69A300,4):", eng.rd(0x69A300, 4).hex(" "))
call69 = [i.address for i in eng.stream if i.mnemonic == "call"
          and i.operands and i.operands[0].type == 2 and i.operands[0].imm == 0x69A300]
print("callers of 0x69A300:", [hex(a) for a in call69])

print("\n== S13 four-flag writer 0x55CFD0 head + write blocks ==")
dis(0x55CFD0, 0x40, "0x55CFD0_head")
for wva in (0x55D123, 0x55D1B1, 0x55D219, 0x55D25C):
    dis(wva - 8, 16, "writeblk@0x%X" % wva)

print("\n== S15 call census (image .text stream) ==")
targets = {0x48D080: "Game::UnknownCall", 0x55D360: "MainLogicFrame",
           0x55CFD0: "0x55CFD0", 0x69A300: "0x69A300", 0x55AFB0: "0x55AFB0",
           0x647260: "NetFrameSync", 0x7970D0: "W10host", 0x684290: "0x684290",
           0x5D4D50: "Pump"}
calls = {t: [] for t in targets}
jmps = {t: [] for t in targets}
for ins in eng.stream:
    if not ins.operands or ins.operands[0].type != 2:
        continue
    t = ins.operands[0].imm
    if ins.mnemonic == "call" and t in calls:
        calls[t].append(ins.address)
    if ins.mnemonic == "jmp" and t in jmps:
        jmps[t].append(ins.address)
for t in sorted(targets):
    cl, jl = calls[t], jmps[t]
    print("  0x%08X %-18s call=%d jmp=%d  %s%s" % (
        t, targets[t], len(cl), len(jl),
        [hex(a) for a in cl[:12]], (" jmps:" + str([hex(a) for a in jl[:6]])) if jl else ""))

print("\n== S18 raw bytes spot checks ==")
for va, n, tag in [(0x55DE73, 6, "inc_rd"), (0x55DE79, 5, "b07784_ld"),
                   (0x55DE7E, 1, "inc"), (0x55DE7F, 2, "cmp"), (0x55DE81, 6, "wr"),
                   (0x48CE8A, 0x21, "main_loop"), (0x52DA04, 8, "52da08"),
                   (0x7778C8, 0x10, "wndproc_wr"), (0x6DA7E9, 5, "6da7e9"),
                   (0x55D877, 6, "susp_bytes"), (0x55D377, 4, "377"),
                   (0x55D385, 2, "385jne"), (0x55D371, 2, "371je"),
                   (0x55D39B, 3, "sleep500"), (0x55D3B2, 3, "sleep10"),
                   (0x55DE40, 5, "de40"), (0x55DC9E, 5, "dc9e"),
                   (0x67F819, 5, "push_a8ed84"), (0x67FA19, 5, "push2")]:
    print("  %s:" % tag, "0x%08X:" % va, eng.rd(va, n).hex(" "))

print("\n== S20 LogicUpdate head 0x55E160..0x55E230 ==")
dis(0x55E160, 0xD0, "LogicUpdate_head")

print("\n== S21 pump 0x5D4D50 tail + IAT ==")
dis(0x5D4E40, 0x18, "pump_tail")
print("resolve_iat(0x7E14C0):", eng.resolve_iat(0x7E14C0))
print("resolve_iat(0x7E11F0):", eng.resolve_iat(0x7E11F0))

print("\n== S23 P01 suspension counter ==")
dis(0x684168, 0x40, "inc@0x684174")
dis(0x6836C4, 0x20, "reset@0x6836D2")

print("\n== S28 push 0xA8ED84 raw census ==")
pat2 = bytes.fromhex("6884EDA800")
pos = 0
outp = []
while True:
    i = raw.find(pat2, pos)
    if i < 0:
        break
    va = None
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= i < rp + rsz:
            va = sva + (i - rp)
            break
    pos = i + 1
    if va is not None:
        outp.append(va)
print("push 0xA8ED84 sites:", [hex(a) for a in outp])

print("\n== S29 calls to 0x637550 / 0x647260 inside MLF ==")
inMLF = [a for a in calls.get(0, [])]
for t, nm in [(0x637550, "0x637550"), (0x5D4430, "0x5D4430"), (0x647260, "0x647260"),
              (0x4A9840, "0x4A9840"), (0x54F5C0, "0x54F5C0"), (0x647260, "netsync"),
              (0x55E160, "LogicUpdate"), (0x725C70, "0x725C70"), (0x637270, "0x637270"),
              (0x684290, "0x684290"), (0x48D080, "UnknownCall")]:
    sel = [a for a in calls.get(t, []) if 0x55D360 <= a < 0x55DEE0]
    print("  %s in MLF: %s" % (nm, [hex(a) for a in sel]))

print("\n== S30 B07784 census (stream, W only + first 6 R) ==")
h5 = eng.disp_hits(0xB07784)
ws5 = [h for h in h5 if h[1] == "W"]
print("total:", len(h5), "W:", [(hex(a), m, o) for a, k, m, o in ws5])
print("R sample:", [(hex(a), m, o) for a, k, m, o in h5 if k == "R"][:6])
dis(0x69BAF8, 0x24, "0x69BB06_writer")

print("\n== S32 WndProc 0x7778CE context ==")
dis(0x7778B0, 0x30, "wndproc")

print("\n== S26 W10 host 0x7970D0 body ==")
dis(0x7970D0, 0x20, "W10host_body")

print("\n== S19 GameMainLoop 0x52DA08 zone ==")
dis(0x52D9F8, 0x20, "GML_52da08")
