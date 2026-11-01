# -*- coding: utf-8 -*-
"""_r064rev_probe4.py — 复核点 2/3/7 收尾：BCD 基类名 / 构造链自动普查 / 帧 A 手算 D 轨迹 / 帧界表
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
ib = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
secs = []
for i in range(nsec):
    name = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((name, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for name, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
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
def td_name(td):
    return cstr(td + 8) if td else None

print("== CHD/BaseClassDescriptor 正确解链（[CHD]=自身TD*；BCD+0=基类TD*）==")
for label, V in [("GenericList", 0x7E1B04), ("INIClass", 0x7EA5F4), ("GenericNode", 0x7E1B0C),
                 ("List<INISection*>", 0x7E1AFC), ("CDFileClass", 0x7E1668), ("CCFileClass", 0x7E16B0)]:
    col = rd(V-4); chd = rd(col+0x10); self_td = rd(chd); numB = rd(chd+8)
    bases = []
    for i in range(numB or 0):
        bcd = rd(chd + 0xC + i*4)
        bases.append((hex(bcd), td_name(rd(bcd)) if bcd else "-"))
    print("  %-16s CHD=%06X 自身TD=%06X %r numBases=%s bases=%s" % (label, chd, self_td, td_name(self_td), numB, bases))

gtd = rd(rd(0x7E1B04-4)+0xC); itd = rd(rd(0x7EA5F4-4)+0xC)
glg = rd(rd(0x7E1B04-4)+0x10); img = rd(rd(0x7EA5F4-4)+0x10)
gb = [td_name(rd(rd(glg+0xC+i*4))) for i in range(rd(glg+8) or 0)]
ib_ = [td_name(rd(rd(img+0xC+i*4))) for i in range(rd(img+8) or 0)]
print("  互不为基类：GenericList 基类含 INIClass TD(%06X)? %s ; INIClass 基类含 GenericList TD(%06X)? %s"
      % (itd, itd in [x for x in ib_ if x], gtd, gtd in gb))
lstg = rd(rd(0x7E1AFC-4)+0x10)
lb = [td_name(rd(rd(lstg+0xC+i*4))) for i in range(rd(lstg+8) or 0)]
print("  List<INISection*> 基类名=%s（R-064 声称恰含 GenericList ⇒ %s）" % (lb, '.?AVGenericList@@' in lb))

# .text 解码（对齐推进）
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

FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0, "E": 0x76C290, "F": 0x778A20, "T16": 0x5D7590}
# 帧界表：各帧 head 起、下一帧 head 或其他已知函数 head 前——简化：用「小于 a 的最大 head」
HS = sorted(FRAMES.values())
def head_of(a):
    prev = None
    for h in HS:
        if h <= a: prev = h
    return prev

print("\n== 全镜像 0x7EA5F4 stamp 后 12 条窗内构造链普查（lea 同 disp + call 0x525A10）==")
pat = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], 0x7ea5f4$")
n30 = 0
for a, s, b, m, o in insns:
    if m == "mov":
        mm = pat.match(o)
        if mm:
            n30 += 1
            disp = mm.group(1)
            k = IDX[a]; found_lea = found_call = None
            for j in range(k+1, min(k+13, len(insns))):
                a2, s2, b2, m2, o2 = insns[j]
                if m2 == "call" and o2 == "0x525a10" and found_lea: found_call = a2; break
                if m2 == "lea" and o2 in ("ecx, [esp + %s]" % disp, "ecx, dword ptr [esp + %s]" % disp):
                    found_lea = a2
            hd = head_of(a)
            fn = next((n for n, h in FRAMES.items() if h == hd), "") if hd else ""
            print("  stamp %06X disp=%-6s lea=%s call=%s %s" % (
                a, disp, hex(found_lea) if found_lea else "-",
                hex(found_call) if found_call else "-",
                ("帧"+fn) if fn else ""))
print("  共 %d 处 stamp（R-064 口径 30 处）" % n30)

print("\n== R-064 声称六帧构造链 (lea,call525A10) 逐址验 ==")
CLAIMS = [("A", 0x7787DB, 0x7787FF), ("B", 0x779BCE, 0x779BF2), ("C", 0x779E4E, 0x779E72),
          ("D", 0x5CEF81, 0x5CEF85), ("E", 0x76C480, 0x76C4AC), ("F", 0x778B03, 0x778B28)]
for fr, lea, c in CLAIMS:
    l = insns[IDX[lea]] if lea in IDX else None
    cc = insns[IDX[c]] if c in IDX else None
    print("  %s lea %06X=[%s %s] ; call %06X=[%s %s]" % (
        fr, lea, l[2] if l else "?", l[4] if l else "?", c, cc[2] if cc else "?", cc[4] if cc else "?"))

print("\n== 帧 A 手算 D 轨迹（R-064 §3 逐项：stamp@D=0xC4 → … → lea@D=0xD0）==")
k = IDX[0x778710]
D = 0; p = 0; trace = []
a = 0x7787C0
kk = IDX[a]
# 从 0x7787C0 到 0x77884B 线性走（同地址流；R-064 声称此处直线无分支）
def sim_range(h, lo, hi):
    D = 0; p = 0
    events = []
    k = IDX[h]
    while insns[k][0] < lo: k += 1
    while insns[k][0] <= hi:
        a, s, b, m, o = insns[k]
        if m == "push": D += 4; p += 4
        elif m == "pop": D -= 4
        elif m == "sub" and o.startswith("esp, "):
            x = int(o.split(", ")[1], 16) if "0x" in o else int(o.split(", ")[1]); D += x; p += x
        elif m == "add" and o.startswith("esp, "):
            x = int(o.split(", ")[1], 16) if "0x" in o else int(o.split(", ")[1]); D -= x; p = 0
        elif m == "call":
            try: t = int(o, 16)
            except Exception: t = None
            if t and t in IDX or (t and t < THI):
                # ret-imm：找该头闭包内 ret（简化：线性找头后首个 ret 且唯一化验过——用 probe3 结论表）
                RIM = {0x40E340:4, 0x525A10:8, 0x5256F0:0, 0x7B4630:0, 0x7B6290:0, 0x4325C0:0, 0x526810:0, 0x526D90:0xC, 0x528C00:0x10, 0x5295F0:0xC, 0x7B5B30:0}
                r = RIM.get(t)
                if r is None:
                    events.append(("UNK-CALL", a, t, "p=%d" % p))
                else:
                    D -= r; p = max(0, p - r)
                    events.append(("call%06X(r=%d)" % (t, r), a, None, "D=%x p=%d" % (D, p)))
        if a == 0x7787C0: events.append(("STAMP-GL", a, None, "D=%x" % D))
        if a == 0x7787F7: events.append(("STAMP-INI", a, None, "D=%x" % D))
        if a == 0x77884B: events.append(("LEA-W", a, None, "D=%x" % D))
        k += 1
    return events
ev = sim_range(0x778710, 0x7787C0, 0x77884F)
for x in ev: print("   ", x)
print("  期望：STAMP-GL D=0xc4；STAMP-INI D=0xc8；LEA-W D=0xd0")

print("\n== 帧 A 反汇编 0x7787B0..0x778860（分支在场否，亲验直线）==")
k = IDX[0x7787B0] if 0x7787B0 in IDX else None
if k:
    while insns[k][0] <= 0x778860:
        a, s, b, m, o = insns[k]
        tag = ""
        if m.startswith("j"): tag = "  <== 分支!"
        print("  %06X %-20s %s %s%s" % (a, b, m, o, tag))
        k += 1

print("\n== 声称『−0x8C 槽先 GenericList 后 List<INISection*> 复用』（帧 A stamp 0x7E1AFC）==")
pat2 = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], 0x7e1afc$")
for a, s, b, m, o in insns:
    if m == "mov" and pat2.match(o):
        hd = head_of(a)
        fn = next((n for n, h in FRAMES.items() if h == hd), "")
        if fn in ("A", "B", "C"):
            print("  stamp %06X disp=%s 帧%s" % (a, pat2.match(o).group(1), fn))
