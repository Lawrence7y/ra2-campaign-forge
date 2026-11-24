# -*- coding: utf-8 -*-
"""xr5_probe.py — 帧 D 区间全部 call 0x525A10 站点的 this 物理槽枚举 + 0x525A60 体内 stamp 检查。
只读 gamemd.exe；不启动任何进程。
"""
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

raw = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]; optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24; ib = struct.unpack_from("<I", raw, opt + 28)[0]; tab = opt + optsz
secs = []
for i in range(nsec):
    nm = raw[tab + i*40:tab + i*40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    secs.append((nm, ib + va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            return raw[fo:fo+n] if fo + n <= rp + rsz else raw[fo:rp+rsz]
    return b""

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
print("[W1] 0x525A60 线性窗 0x100 字节内含 0x7ea5f4 的指令：")
buf = rb(0x525A60, 0x100)
hit = False
for ins in md.disasm(buf, 0x525A60):
    if "0x7ea5f4" in ins.op_str:
        hit = True
        print("  %06X %-22s %-5s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
if not hit:
    print("  （0x525A60 窗内也无 INIClass vptr stamp）")

# 全解码（与 xr1 同域）以支撑 D 记账
tn, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp + trsz]
insns = []; cur = TLO; end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur - TLO:min(cur - TLO + 15, end - TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str); break
    if got is None:
        cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
heads = set()
for a, s, b, m, o in insns:
    if m == "call" and b[:2] == "e8" and len(b) == 10:
        try:
            t = int(o, 16)
        except ValueError:
            continue
        if TLO <= t < THI:
            heads.add(t)
print("insns=%d heads=%d" % (len(insns), len(heads)))

def nxt(a):
    k = IDX.get(a)
    return None if k is None else a + insns[k][1]
def body(head):
    seen = {head}; work = [head]
    while work:
        a = work.pop(); k = IDX.get(a)
        if k is None: continue
        _, sz, by, m, o = insns[k]
        if m == "ret": continue
        dests = []
        if m == "jmp" or m[0] == "j":
            try: t = int(o, 16)
            except ValueError: t = None
            if t is not None and TLO <= t < THI and (t not in heads or t == head): dests.append(t)
            if m != "jmp":
                f = nxt(a)
                if f is not None and f < THI and (f not in heads or f == head): dests.append(f)
        else:
            f = nxt(a)
            if f is not None and f < THI and (f not in heads or f == head): dests.append(f)
        for x in dests:
            if x not in seen: seen.add(x); work.append(x)
    return seen
def retimm(head):
    imms = set()
    for a in body(head):
        k = IDX.get(a)
        if k is None: continue
        _, sz, by, m, o = insns[k]
        if m == "ret":
            imms.add(0 if not o.strip() else int(o, 16))
    return (next(iter(imms)) if len(imms) == 1 else None), sorted(imms)
def call_target(o):
    if not o or o.startswith(("dword", "word", "byte", "[")): return None
    try: t = int(o, 16)
    except ValueError: return None
    return t if TLO <= t < THI else None

def dsim(head, resmap, targets, budget=3_000_000):
    coll, causes = {}, {}
    seen = set(); work = [(head, 0, 0)]; g = 0
    while work:
        g += 1
        if g > budget:
            causes["BUDGET"] = {"budget"}; break
        a, D, p = work.pop()
        if (a, D, p) in seen: continue
        seen.add((a, D, p))
        if a in targets: coll.setdefault(a, set()).add(D)
        k = IDX.get(a)
        if k is None: continue
        _, sz, by, m, o = insns[k]
        if m == "ret": continue
        nD, np_, why = D, p, None
        if m == "push": nD, np_ = D + 4, p + 4
        elif m == "pop": nD = D - 4
        elif m in ("sub", "add") and o.startswith("esp, "):
            try: x = int(o.split(", ", 1)[1], 0)
            except ValueError: return coll, {"esp-imm-bad"}
            nD, np_ = (D + x, p + x) if m == "sub" else (D - x, 0)
        elif m == "call":
            if a in resmap:
                r = resmap[a]; nD, np_ = D - r, max(0, p - r)
            else:
                t = call_target(o)
                if t is not None and t in heads:
                    r, allr = retimm(t)
                    if r is None:
                        if p != 0: why = "callee-ambig"
                    else:
                        nD, np_ = D - r, max(0, p - r)
                elif p != 0:
                    why = "indir-unres"
        elif m in ("mov", "lea") and o.split(",")[0].strip() == "esp": why = "esp-rewrite"
        elif m in ("leave", "pushad", "popad", "enter", "xchg", "popfd"): why = "esp-shape"
        if why:
            causes.setdefault(a, set()).add(why); continue
        k2 = IDX.get(a)
        _, sz2, by2, m2, o2 = insns[k2]
        dests = []
        if m2 == "jmp" or m2[0] == "j":
            try: t = int(o2, 16)
            except ValueError: t = None
            if t is not None and TLO <= t < THI and (t not in heads or t == head): dests.append(t)
            if m2 != "jmp":
                f = nxt(a)
                if f is not None and f < THI and (f not in heads or f == head): dests.append(f)
        else:
            f = nxt(a)
            if f is not None and f < THI and (f not in heads or f == head): dests.append(f)
        for x in dests: work.append((x, nD, np_))
    return coll, causes

print("\n[W2] 帧 D 区间（0x5CEEF0 起）全部 call 0x525a10 站点及其 this 物理槽")
h = 0x5CEEF0
bd = body(h)
sites = []
for a, sz, by, m, o in insns:
    if m == "call" and o == "0x525a10" and a in bd:
        jc = IDX[a]
        lea = None
        for j in range(jc - 1, max(0, jc - 12), -1):
            a2, s2, b2, m2, o2 = insns[j]
            if m2 == "lea" and re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", o2):
                dd = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", o2).group(1)
                lea = (a2, int(dd, 16) if dd.startswith("0x") else int(dd)); break
            if m2 == "call":
                break
        sites.append((a, lea))
print("  站点数=%d" % len(sites))
tg = {0x5CEF41}
for a, l in sites:
    tg.add(a)
    if l: tg.add(l[0])
coll, causes = dsim(h, {0x5CEF6B: 4, 0x5CEF78: 4}, tg)
Dst = coll.get(0x5CEF41)
Pst = 0x28 - next(iter(Dst)) if Dst and len(Dst) == 1 else None
print("  stamp 0x5CEF41 D=%s P=%s (witness 槽)" % (
    hex(next(iter(Dst))) if Dst and len(Dst) == 1 else "?", hex(Pst) if Pst is not None else "?"))
for a, l in sites:
    Dc = coll.get(a); Dl = coll.get(l[0]) if l else None
    Dc1 = next(iter(Dc)) if Dc and len(Dc) == 1 else None
    Dl1 = next(iter(Dl)) if Dl and len(Dl) == 1 else None
    P = (l[1] - Dl1) if (l and Dl1 is not None) else None
    print("  call 0x525A10@%06X D=%s | lea@%s disp=%s D=%s → this 槽 P=%s %s" % (
        a, hex(Dc1) if Dc1 is not None else "?",
        hex(l[0]) if l else "-", hex(l[1]) if l else "-",
        hex(Dl1) if Dl1 is not None else "?",
        hex(P) if P is not None else "-",
        "（=witness 槽）" if (P is not None and Pst is not None and P == Pst) else ""))
print("  剪枝点: %s" % sorted("%06X" % k for k in causes if isinstance(k, int)))
print("\n[W-END] 完成")
