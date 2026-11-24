# -*- coding: utf-8 -*-
"""P01 核验员独立复算脚本。只读 gamemd.exe，写域仅本目录。
逐节复算 REPORT.md 的 keyFacts；每节独立 try，不因单点失败中断。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

OUT = []
def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)

VERD = {}
def verdict(k, v):
    VERD[k] = v
    say(">>> VERDICT[%s] = %s" % (k, v))

eng = Engine()
by = eng.by()   # 触发全量重同步解码

# ============ 0. 现场 ============
say("== 0. 环境 ==")
say("SHA match:", eng.sha == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
cov = eng.coverage
say("coverage = %.4f%% / %d insns / resync=%d" % cov)
VERD["coverage"] = "%.4f%%/%d/resync%d" % cov
say("IAT 0x7E11F0 =", eng.resolve_iat(0x7E11F0))
say("IAT 0x7E1530 =", eng.resolve_iat(0x7E1530))

# ============ KF1 冻结段逐字节 ============
say("== KF1. 冻结段 0x55D7C2..0x55D880 ==")
seg = list(eng.disasm(0x55D7C2, 0xC0))
segd = {}
for a, b, m, o in seg:
    segd[a] = (b, m, o)
    say("0x%08X  %-14s %s %s" % (a, b, m, o))
# 关键字节硬断言
HARD = [
    (0x55D7C2, "a138b2a800"),          # mov eax,[0xA8B238]
    (0x55D7C7, "85c0"),                # test eax,eax
    (0x55D7C9, "7409"),                # je 0x55D7D4
    (0x55D7CB, "83f805"),              # cmp eax,5
    (0x55D7CE, "0f85a4000000"),        # jne 0x55D878
    (0x55D7D4, "8b3d30b2a800"),        # mov edi,[0xA8B230]
    (0x55D7DA, "8a8730060000"),        # mov al,[edi+0x630]
    (0x55D7E0, "84c0"),                # test al,al
    (0x55D7E2, "743d"),                # je 0x55D821
    (0x55D7E4, "8b8720060000"),        # mov eax,[edi+0x620]
    (0x55D7EA, "8bb728060000"),        # mov esi,[edi+0x628]
    (0x55D7F6, "83f8ff"),              # cmp eax,-1
    (0x55D7F9, "7410"),                # je 0x55D80B
    (0x55D7FB, "8d4f04"),              # lea ecx,[edi+4]
    (0x55D7FE, "e83db41600"),          # call 0x6C8C40
    (0x55D803, "2b07"),                # sub eax,[edi]
    (0x55D805, "3bc6"),                # cmp eax,esi
    (0x55D807, "7d06"),                # jge 0x55D80F
    (0x55D809, "2bf0"),                # sub esi,eax
    (0x55D80B, "85f6"),                # test esi,esi
    (0x55D80D, "7f12"),                # jg 0x55D821
    (0x55D80F, "8b1530b2a800"),        # mov edx,[0xA8B230]
    (0x55D815, "c6823006000000"),      # mov byte[edx+0x630],0
    (0x55D81C, "e85f691200"),          # call 0x684180
    (0x55D821, "a130b2a800"),          # mov eax,[0xA8B230]
    (0x55D826, "8b882c060000"),        # mov ecx,[eax+0x62C]
    (0x55D82C, "85c9"),                # test ecx,ecx
    (0x55D82E, "7448"),                # je 0x55D878
    (0x55D830, "e81b750700"),          # call 0x5D4D50
    (0x55D835, "e846f8f2ff"),          # call 0x48D080
    (0x55D83A, "e821ddfdff"),          # call 0x53B560
    (0x55D83F, "8b0d24738800"),        # mov ecx,[0x887324]
    (0x55D845, "8b11"),                # mov edx,[ecx]
    (0x55D847, "ff525c"),              # call [edx+0x5C]
    (0x55D84A, "b9e8f78700"),          # mov ecx,0x87F7E8
    (0x55D84F, "e82c6cf9ff"),          # call 0x4F4480
    (0x55D854, "e807090000"),          # call 0x55E160
    (0x55D859, "8a0da0e9a800"),        # mov cl,[0xA8E9A0]
    (0x55D85F, "33c0"),                # xor eax,eax
    (0x55D877, "c3"),                  # ret
]
fails = []
for va, hx in HARD:
    got = eng.rd(va, len(hx) // 2).hex()
    if got != hx:
        fails.append((va, hx, got))
if fails:
    say("HARD-FAIL:", fails)
    verdict("KF1_freeze_bytes", "REFUTED")
else:
    # 分支目标独立复算
    bt = [
        ("0x55D7C9 je +9", 0x55D7C9 + 2 + 0x09, 0x55D7D4),
        ("0x55D7CE jne +0xA4", 0x55D7CE + 6 + 0xA4, 0x55D878),
        ("0x55D7E2 je +0x3D", 0x55D7E2 + 2 + 0x3D, 0x55D821),
        ("0x55D7F9 je +0x10", 0x55D7F9 + 2 + 0x10, 0x55D80B),
        ("0x55D807 jge +6", 0x55D807 + 2 + 6, 0x55D80F),
        ("0x55D80D jg +0x12", 0x55D80D + 2 + 0x12, 0x55D821),
        ("0x55D82E je +0x48", 0x55D82E + 2 + 0x48, 0x55D878),
        ("0x55D81C call rel", 0x55D81C + 5 + 0x0012695F, 0x684180),
        ("0x55D7FE call rel", 0x55D7FE + 5 + 0x0016B43D, 0x6C8C40),
        ("0x55D830 call rel", 0x55D830 + 5 + 0x000751B, 0x5D4D50),
    ]
    say("branch-target recompute:", [(n, hex(c), hex(t), c == t) for n, c, t in bt])
    verdict("KF1_freeze_bytes", "PASS" if all(c == t for _, c, t in bt) else "PARTIAL")

# capstone 视角的段（对照 op_str 渲染）
say("capstone 0x55D7C9..0x55D7D4:", [(a, m, o) for a, b, m, o in seg if 0x55D7C9 <= a <= 0x55D7D4])

# ============ KF2 +0x62C 家族 / 写点全集 ============
say("== KF2. disp_hits_field(0x62C) 全镜像 ==")
h62 = eng.disp_hits_field(0x62C)
say("total disp==0x62C hits =", len(h62))
for va, rw, m, o in h62:
    say("  0x%08X %s %-6s %s" % (va, rw, m, o))
w62 = [h for h in h62 if h[1] == "W"]
say("write hits:", [(hex(va), m, o) for va, rw, m, o in w62])
# 各命中处向上回溯 0x30 字节找 [0xA8B230] 装载（独立于原报告启发式）
def ctx230(va):
    import capstone
    md = eng.md
    blob = eng.rd(va - 0x40, 0x40)
    out = []
    cur = va - 0x40
    while cur < va:
        got = list(md.disasm(eng.raw[eng.fo(cur):eng.fo(cur) + 15], cur))
        if not got:
            cur += 1
            continue
        i = got[0]
        out.append((i.address, i.mnemonic + " " + i.op_str))
        cur += i.size
    hit = [x for x in out if "0xa8b230" in x[1].lower()]
    return hit
for va, rw, m, o in h62:
    say("ctx 0x%08X base230=%s | %s" % (va, ctx230(va), o))

# ============ KF3 [0xA8B230] 身份 ============
say("== KF3. [0xA8B230] 三个写点 + ctor 链 ==")
h230 = eng.disp_hits(0xA8B230)
wr = [h for h in h230 if h[1] == "W"]
say("0xA8B230 refs=%d writes=%d writers=%s" % (len(h230), len(wr), [hex(x[0]) for x in wr]))
for va in (0x52BA60,):
    for a, b, m, o in eng.disasm(va, 0x80):
        say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("bytes 0x52BA94:", eng.rd(0x52BA94, 5).hex())
say("bytes 0x52BAB6:", eng.rd(0x52BAB6, 5).hex())
say("bytes 0x6BEB7D:", eng.rd(0x6BEB7D, 5).hex())
for a, b, m, o in eng.disasm(0x6BEB60, 0x30):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
# ctor 0x6832C0 内 0x6833DB call 0x683610
say("disasm 0x6833D0..0x6833E5:")
for a, b, m, o in eng.disasm(0x6833D0, 0x15):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("call target from 0x6833DB:", hex(0x6833DB + 5 + struct.unpack("<i", eng.rd(0x6833DC, 4))[0]))
# 0x6835E1 引用 Scenario.CPP 串
say("disasm 0x6835D5..0x6835F0:")
for a, b, m, o in eng.disasm(0x6835D5, 0x1B):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
s8 = eng.rd(0x83D838, 0x30)
say("string @0x83D838:", s8.split(b"\0")[0])
# 0x683610 函数：0xF4240 写 + 0x62C/0x630 清零
say("disasm 0x683610..0x6836E5:")
for a, b, m, o in eng.disasm(0x683610, 0xD5):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))

# ============ KF4 时钟 / 0x684060 / 0x684180 ============
say("== KF4. 时钟 0x6C8C40 + 挂起/释放函数 ==")
say("bytes 0x6C8C40:", eng.rd(0x6C8C40, 12).hex())
for a, b, m, o in eng.disasm(0x6C8C40, 12):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("disasm 0x684060..0x6841B0:")
for a, b, m, o in eng.disasm(0x684060, 0x150):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("disasm 0x68422C..0x684245 (ElapsedTimer re-arm):")
for a, b, m, o in eng.disasm(0x684210, 0x38):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
for g in (0xA8ED9C, 0xB054CC, 0xB07784):
    hh = eng.disp_hits(g)
    say("global 0x%X: refs=%d writers=%s" % (g, len(hh), [(hex(x[0]), x[2] + " " + x[3]) for x in hh if x[1] == "W"][:8]))

# ============ KF5 call sites ============
say("== KF5. E8 直接调用点普查 ==")
def call_sites(target):
    res = []
    for i in by.values():
        if i.mnemonic != "call":
            continue
        try:
            op = i.operands[0]
        except Exception:
            continue
        if op.type == 2 and op.imm == target:
            res.append(i.address)
    return sorted(res)
for t, name in ((0x684060, "inc/hold"), (0x684180, "dec/release"), (0x53B460, "grad-starter"),
                (0x55E160, "throttle"), (0x6C8C40, "clock"), (0x53B560, "grad-machine"),
                (0x5D4D50, "pump"), (0x48D080, "sess"), (0x4F4480, "present")):
    cs = call_sites(t)
    say("call 0x%06X (%s): %d sites %s" % (t, name, len(cs), [hex(x) for x in cs]))
say("u32(0x872E78) =", hex(eng.u32(0x872E78)))
say("bytes 0x53B610:", eng.rd(0x53B610, 8).hex())
say("capstone 0x53B610:", eng.disasm(0x53B610, 8))
say("capstone 0x53B60E:", eng.disasm(0x53B60E, 10))
for va in (0x53B612, 0x53B6E6, 0x657CA0, 0x657CC8, 0x6DF6FD, 0x6E4080):
    say("bytes@0x%06X:" % va, eng.rd(va, 5).hex())

# ============ KF6 冻结体/正常体调用普查 + 返回值 ============
say("== KF6. 冻结体与正常体 ==")
def calls_in(lo, hi):
    res = []
    for i in by.values():
        if not (lo <= i.address < hi) or i.mnemonic != "call":
            continue
        try:
            op = i.operands[0]
        except Exception:
            continue
        if op.type == 2:
            res.append((i.address, op.imm))
    return res
fz = calls_in(0x55D830, 0x55D877)
say("frozen-body direct calls:", [(hex(a), hex(t)) for a, t in fz])
say("frozen-body unique targets:", len(set(t for a, t in fz)))
for hi, tag in ((0x55DEC7, "to ret0x55DEC7"), (0x55DEE0, "to 0x55DEE0")):
    nm = calls_in(0x55D878, hi)
    ut = sorted(set(t for a, t in nm))
    say("normal-body [%s] direct calls=%d unique targets=%d" % (tag, len(nm), len(ut)))
    for a, t in nm:
        say("   0x%08X -> 0x%06X" % (a, t))
say("bytes 0x55D861..0x55D877:", eng.rd(0x55D861, 0x16).hex())
for a, b, m, o in eng.disasm(0x55D85F, 0x1A):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("normal tail 0x55DEC0..0x55DEE0:")
for a, b, m, o in eng.disasm(0x55DEC0, 0x20):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
say("mainloop 0x48CE60..0x48CEA0:")
for a, b, m, o in eng.disasm(0x48CE60, 0x40):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))

# ============ KF7 0x55E160 节流 ============
say("== KF7. 0x55E160 ==")
for a, b, m, o in eng.disasm(0x55E1B0, 0x120):
    say("  0x%08X  %-12s %s %s" % (a, b, m, o))
for g in (0x887348, 0x887350, 0x887330, 0xA8E314, 0xABCD40):
    hh = eng.disp_hits(g)
    say("global 0x%X refs=%d" % (g, len(hh)))

# ============ KF9 MLF CFG ============
say("== KF9. MLF rets / reach_without ==")
rets, succ = eng.func_rets(0x55D360, 0x55DEE0)
say("rets:", [hex(i.address) for i in rets])
rw = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
rw_rets = sorted(a for a in rw if a in {i.address for i in rets})
say("reach_without rets:", [hex(a) for a in rw_rets])
say("0x55DEC7 in reachable set:", 0x55DEC7 in rw)

# ============ KF10 基线计数 ============
say("== KF10. 基线四项 ==")
for g in (0xA8ED84, 0xA8ED80, 0xA8B230, 0xA8B238):
    hh = eng.disp_hits(g)
    wr = [(hex(x[0]), x[2], x[3]) for x in hh if x[1] == "W"]
    say("0x%X refs=%d writes=%d %s" % (g, len(hh), len(wr), wr))
hh84 = eng.disp_hits(0xA8ED84)
say("0xA8ED84 inc instructions:",
    [(hex(i.address), i.mnemonic, i.op_str) for i in by.values()
     if i.mnemonic.startswith("inc") and any(
         (op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp == 0xA8ED84)
         for op in (i.operands if hasattr(i, "operands") else []))])
say("bytes 0x55DE73..0x55DE84:", eng.rd(0x55DE73, 0x11).hex())

# ============ KF11 字段族/镜像 ============
say("== KF11. 字段族全局 ==")
for g in (0xAA0430, 0xB73550, 0xA9FAB0, 0xA9FA98, 0xA9FA9C, 0xA9FAA8, 0xA9FAD1, 0x887324):
    hh = eng.disp_hits(g)
    wr = [(hex(x[0]), x[2], x[3]) for x in hh if x[1] == "W"][:6]
    say("0x%X refs=%d writers(first6)=%s" % (g, len(hh), wr))

# ============ 汇总落盘 ============
with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P01/verify_aux.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
say("WROTE verify_aux.txt")
