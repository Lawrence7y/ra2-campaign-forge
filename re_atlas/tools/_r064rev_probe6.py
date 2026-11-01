# -*- coding: utf-8 -*-
"""_r064rev_probe6.py — 修正版：MSVC BaseClassArray 正确版式（BCD 首元=自描述）重读基类名；
   帧 A 直线 D 轨迹补全 callee ret-imm（闭合第三法差 8 之谜）；T16/D PURE 分级。
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e+6)[0]; optsz = struct.unpack_from("<H", raw, e+20)[0]
opt = e+24; ib = struct.unpack_from("<I", raw, opt+28)[0]; tab = opt+optsz
secs = []
for i in range(nsec):
    name = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((name, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for name, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b) == 4 else None
def cstr(va, mx=90):
    out = bytearray()
    for i in range(mx):
        c = rb(va+i, 1)
        if not c or c == b"\0": break
        out += c
    return out.decode("latin1")

print("== 修正版式：BCD 首元(CHD+0xC)=自描述 TD*；真基类自 CHD+0x10 起 ==")
def bases(V, label):
    col = rd(V-4); chd = rd(col+0x10); self_td = rd(col+0xC)
    e0 = rd(chd+0xC)
    print("  %-16s numBases=%s 自描述BCD=%06X[+0]=%06X==自身TD?%s" % (
        label, rd(chd+8), e0, rd(e0), rd(e0) == self_td))
    arr = []
    nb = rd(chd+8) or 0
    for i in range(1, nb):
        p = rd(chd+0xC+i*4)
        arr.append((hex(p), cstr(rd(p)+8) if p and rd(p) else "?"))
    print("      真基类(%d/%d)：%s" % (nb-1, nb, arr))
    print("      全部数组元 TD 名：", [cstr(rd(rd(chd+0xC+i*4))+8) for i in range(nb)])
    return arr
gb = bases(0x7E1B04, "GenericList")
ib_ = bases(0x7EA5F4, "INIClass")
lb = bases(0x7E1AFC, "List<INISection*>")
print("  == 互斥判定（全部数组元含对方 TD）==")
gltd = rd(rd(0x7E1B04-4)+0xC); initd = rd(rd(0x7EA5F4-4)+0xC)
def allt(V):
    col = rd(V-4); chd = rd(col+0x10); nb = rd(chd+8) or 0
    return [rd(rd(chd+0xC+i*4)) for i in range(nb) if rd(chd+0xC+i*4)]
print("  GenericList 数组含 INIClass TD(%06X)? %s" % (initd, initd in allt(0x7E1B04)))
print("  INIClass   数组含 GenericList TD(%06X)? %s" % (gltd, gltd in allt(0x7EA5F4)))
print("  List<INISection*> 数组含 GenericList TD? %s" % (gltd in allt(0x7E1AFC)))

# ---- .text 解码 ----
tname, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []; cur = TLO; end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str); break
    if got is None: cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
e8set = set()
for a, s, b, m, o in insns:
    if m == "call" and b.startswith("e8") and len(b) == 10:
        try: t = int(o, 16)
        except ValueError: continue
        if TLO <= t < THI: e8set.add(t)

def closure(head):
    body = {}; stack = [head]; seen = {head}
    while stack:
        a = stack.pop()
        k = IDX.get(a)
        if k is None: body[a] = []; continue
        _, s, b, m, o = insns[k]
        succ = []
        if m == "ret": pass
        elif m == "jmp":
            t = int(o, 16) if o.startswith("0x") else None
            if t is not None and TLO <= t < THI and (t not in e8set or t == head): succ.append(t)
        elif m[0] == "j":
            t = int(o, 16) if o.startswith("0x") else None
            if t is not None and TLO <= t < THI and t not in e8set: succ.append(t)
            nxt = a + s
            if nxt < THI and (nxt not in e8set or nxt == head): succ.append(nxt)
        else:
            nxt = a + s
            if nxt < THI and (nxt not in e8set or nxt == head): succ.append(nxt)
        body[a] = succ
        for x in succ:
            if x not in seen: seen.add(x); stack.append(x)
    return body, seen

_RC = {}
def ret_imm(head):
    if head in _RC: return _RC[head]
    body, seen = closure(head)
    imms = []
    for a in body:
        k = IDX.get(a)
        if k is not None and insns[k][3] == "ret":
            o = insns[k][4]
            imms.append(int(o, 16) if o.startswith("0x") else (int(o) if o.strip().isdigit() else 0))
    v = imms[0] if (imms and len(set(imms)) == 1) else None
    _RC[head] = (v, body, seen, imms)
    return _RC[head]

print("\n== 帧 A 直线轨迹·callee ret 全亲查 ==")
for t in (0x7B4620, 0x7B66C0, 0x47A9D0, 0x431F10, 0x65D150, 0x47AF10, 0x40E320, 0x7B5440, 0x40E340, 0x525A10, 0x4325C0, 0x526810):
    v, body, seen, imms = ret_imm(t)
    print("  %06X ret交集=%s 全部=%s E8头=%s" % (t, v, sorted(set(imms)), t in e8set))

print("\n== 帧 A 直线 D 轨迹（ret 全由上表）==")
RIM = {}
for t in (0x7B4620, 0x7B66C0, 0x47A9D0, 0x431F10, 0x65D150, 0x47AF10, 0x40E320, 0x7B5440, 0x40E340, 0x525A10, 0x4325C0, 0x526810, 0x528C00):
    RIM[t] = ret_imm(t)[0]
D = 0; p = 0; marks = {}
k0 = IDX[0x778710]
for i in range(k0, IDX[0x77884F]+1):
    a, s, b, m, o = insns[i]
    if a in (0x7787C0, 0x7787D1, 0x7787DB, 0x7787F7, 0x77884B, 0x778844, 0x778840, 0x77883F):
        marks[a] = (D, p)
    if m == "push": D += 4; p += 4
    elif m == "pop": D -= 4
    elif m == "sub" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D += x; p += x
    elif m == "add" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D -= x; p = 0
    elif m == "call":
        t = int(o, 16) if o.startswith("0x") else None
        if t in RIM and RIM[t] is not None:
            r = RIM[t]; D -= r; p = max(0, p - r)
        elif t is not None:
            print("    未知 ret-imm callee %06X @%06X (p=%d)" % (t, a, p))
for a in sorted(marks):
    it = insns[IDX[a]]
    print("  %06X D=0x%-4X p=%-4d %s %s" % (a, marks[a][0], marks[a][1], it[2], it[4]))
print("  G-stamp P=0x38-D=0x%X ; INI-stamp P=0x30-D=%s ; W=0x38-D=%s" % (
    0x38 - marks[0x7787C0][0], hex(0x30 - marks[0x7787F7][0]), hex(0x38 - marks[0x77884B][0])))
print("  ⇒ 直线法（含未取分支污染）P 仍满足：W==INI-P？%s；G-P==W+0xC？%s" % (
    (0x30 - marks[0x7787F7][0]) == (0x38 - marks[0x77884B][0]),
    (0x38 - marks[0x7787C0][0]) == (0x38 - marks[0x77884B][0]) + 0xC))
