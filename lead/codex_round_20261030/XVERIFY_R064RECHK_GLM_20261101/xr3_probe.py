# -*- coding: utf-8 -*-
"""xr3_probe.py — R-064 独立复核补充探针（第三批定点）：
  Z1 帧 D ctor 对 0x5CEF81(lea)/0x5CEF85(call 0x525A10)：字节 + D 值 + 与 stamp 0x5CEF41 同格判定。
  Z2 修正编码的 lea 上下文钉：0x52575B=8d461c（lea eax,[esi+0x1C]）、0x525788=8d4610（lea eax,[esi+0x10]）。
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

print("[Z1] 帧 D ctor 对 0x5CEF81/0x5CEF85")
for va, n in [(0x5CEF81, 4), (0x5CEF85, 5)]:
    k = IDX.get(va)
    print("  %06X bytes=%s  %s %s" % (va, rb(va, n).hex(),
          insns[k][3] if k else "?", insns[k][4] if k else "?"))
tg = {0x5CEF41, 0x5CEF81, 0x5CEF85, 0x5CEF6B, 0x5CEF78}
coll, causes = dsim(0x5CEEF0, {0x5CEF6B: 4, 0x5CEF78: 4}, tg)
for a in sorted(tg):
    D = coll.get(a)
    print("  %06X D=%s" % (a, sorted(hex(x) for x in D) if D else "剪枝"))
Dst = coll.get(0x5CEF41); Dl = coll.get(0x5CEF81)
if Dst and Dl and len(Dst) == 1 and len(Dl) == 1:
    Pst = 0x28 - next(iter(Dst)); Pl = 0x28 - next(iter(Dl))
    print("  stamp P=disp0x28-D(%s)=%s ; ctor-lea P=disp0x28-D(%s)=%s ⇒ 同格=%s" % (
        hex(next(iter(Dst))), hex(Pst), hex(next(iter(Dl))), hex(Pl), Pst == Pl))

print("\n[Z2] 修正编码的 lea 上下文钉")
for va, n, exp, what in [
    (0x52575B, 3, "8d461c", "lea eax,[esi+0x1C]（后随 3bc3 cmp eax,ebx、c7 00 stamp）"),
    (0x525788, 3, "8d4610", "lea eax,[esi+0x10]"),
    (0x52575E, 2, "3bc3", "cmp eax,ebx"),
    (0x52578B, 2, "3bc3", "cmp eax,ebx"),
]:
    got = rb(va, n).hex()
    print("  %06X %-10s exp=%-10s %s  %s" % (va, got, exp, "MATCH" if got == exp else "——", what))
print("\n[Z-END] 完成")
