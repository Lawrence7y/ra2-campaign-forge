# -*- coding: utf-8 -*-
"""xr2_probe.py — R-064 独立复核补充探针（定点）：
  Y1 R-064 §3 所列六帧 + T16 的「INI stamp ↔ call 0x525A10 ctor」同格链逐帧定量：
     stamp disp 与 ctor 前 lea ecx disp 是否同字面、D 是否同值（⇒ 同物理格）。
  Y2 0x5256F0 复位体 lea 上下文钉：0x52575B lea eax,[esi+0x1C] / 0x525788 lea eax,[esi+0x10]，
     及 0x40E32A（0x40E320 体）置 [that]=0x7E1B0C 的钉。
  Y3 0x525A10 头 12 条（它是什么）。
只读 gamemd.exe；不启动任何进程。
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

raw = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
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

store_re = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
lea_re = re.compile(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$")

print("\n[Y1] INI stamp ↔ ctor 0x525A10 同格链（R-064 §3 所列站点定点复验）")
# (帧, 帧头, INI stamp 站点, stamp disp) —— stamp disp 从字节钉得来
CASES = [
    ("A", 0x778710, 0x7787F7, 0x30),
    ("B", 0x779B50, 0x779BEA, 0x1C),
    ("C", 0x779DD0, 0x779E6A, 0x1C),
    ("D", 0x5CEEF0, 0x5CEF41, 0x28),
    ("E", 0x76C290, 0x76C4A4, 0x30),
    ("F", 0x778A20, 0x778B20, 0x2C),
    ("T16", 0x5D7590, 0x5D761D, 0x78),
]
for fr, h, stv, sd in CASES:
    k = IDX[stv]
    # stamp 后第一条 call 0x525a10（≤4 条内），其前最近的 lea ecx,[esp+X]
    ctor = None
    for j in range(k + 1, min(k + 5, len(insns))):
        a2, s2, b2, m2, o2 = insns[j]
        if m2 == "call" and o2 == "0x525a10":
            ctor = a2; break
        if m2 == "call":
            break
    lea = None
    if ctor is not None:
        jc = IDX[ctor]
        for j in range(jc - 1, max(0, jc - 12), -1):
            a2, s2, b2, m2, o2 = insns[j]
            if m2 == "lea" and lea_re.match(o2):
                lea = (a2, int(lea_re.match(o2).group(1), 16)); break
            if m2 == "call":
                break
    # D 记账（目标：stamp、ctor 的 lea、ctor call）
    tg = {stv}
    if lea: tg.add(lea[0])
    if ctor: tg.add(ctor)
    coll, causes = dsim(h, {0x5CEF6B: 4, 0x5CEF78: 4} if fr == "D" else {}, tg)
    Ds = coll.get(stv); Dl = coll.get(lea[0]) if lea else None
    Ds1 = next(iter(Ds)) if Ds and len(Ds) == 1 else None
    Dl1 = next(iter(Dl)) if Dl and len(Dl) == 1 else None
    print("  %s stamp %06X disp=0x%-3X D=%s | ctor 0x525A10@%s | lea@%s disp=%s D=%s | 同字面disp=%s 同D=%s ⇒ 同格=%s" % (
        fr, stv, sd,
        hex(Ds1) if Ds1 is not None else "?",
        hex(ctor) if ctor else "无",
        hex(lea[0]) if lea else "-", hex(lea[1]) if lea else "-",
        hex(Dl1) if Dl1 is not None else "?",
        (lea[1] == sd) if lea else "-",
        (Ds1 == Dl1) if (Ds1 is not None and Dl1 is not None) else "-",
        (lea[1] == sd and Ds1 == Dl1) if (lea and Ds1 is not None and Dl1 is not None) else "-"))

print("\n[Y2] 复位体/节点头 lea 上下文钉")
for va, n, exp, what in [
    (0x52575B, 6, "8d861c000000", "lea eax,[esi+0x1C]（R064REV 称 @52575B）"),
    (0x525788, 6, "8d8610000000", "lea eax,[esi+0x10]（R064REV 称 @525788）"),
    (0x40E32A, 6, "c7000c1b7e00", "0x40E320 体置 [that]=0x7E1B0C（GenericNode vptr）"),
    (0x525A18, 6, "c706f4a57e00", "0x525A10 ctor 置 [this]=0x7EA5F4（若在此偏移）"),
]:
    got = rb(va, n).hex()
    print("  %06X %-16s exp=%-16s %s  %s" % (va, got, exp, "MATCH" if got == exp else "——", what))

print("\n[Y3] 0x525A10 头 12 条：")
for ins in md.disasm(rb(0x525A10, 0x30), 0x525A10):
    print("  %06X %-20s %-5s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
print("\n[Y-END] 完成")
