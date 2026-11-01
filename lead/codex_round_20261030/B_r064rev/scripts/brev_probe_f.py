# -*- coding: utf-8 -*-
"""brev_probe_f.py — 本线收口三项（修正引擎后）：
 F1. 「同字面 disp 配对」vs「物理同槽配对」的可互换性计数（用本线 brev_b/c/e 同款已验证引擎）。
 F2. 错位 0xC 的第三种读法之字节闭合：witness this 落格 −0x98 → −0x8C = this+0xC；
     同物理槽是否被两阶段 vptr 写（0x7E1B04 后 0x7E1AFC）= List<INISection*>(基类 GenericList)
     的构造序列；并对照 0x5256F0 的 [esi+0xC]=0x7E1B04。
 F3. 帧 D [esp+0x68] 的槽连续性：lea ecx,[esp+0x68]@5CEEFC 与 mov eax,[esp+0x68]@5CEF5E
     是否指同一物理槽（决定 vtable 落实的对象身份链是否闭合）。
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

raw = open(r"D:\Project\ra2-campaign-forge\ra2youli/gamemd.exe", "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e+6)[0]; optsz = struct.unpack_from("<H", raw, e+20)[0]
opt = e+24; ib = struct.unpack_from("<I", raw, opt+28)[0]; tab = opt+optsz
secs = []
for i in range(nsec):
    nm = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((nm, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva-ib <= rva < sva-ib+vsz:
            fo = rp+(rva-(sva-ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b) == 4 else None
def cstr(va, mx=90):
    o = bytearray()
    for i in range(mx):
        c = rb(va+i, 1)
        if not c or c == b"\0": break
        o += c
    return o.decode("latin1")
tn, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva+trsz
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []; cur = TLO; end = TLO+trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str); break
    if got is None: cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
e8heads = set()
for a, s, b, m, o in insns:
    if m == "call" and b[:2] == "e8" and len(b) == 10:
        try: t = int(o, 16)
        except Exception: continue
        if TLO <= t < THI: e8heads.add(t)
def succ(a, head):
    k = IDX.get(a)
    if k is None: return []
    _, s, b, m, o = insns[k]
    if m == "ret": return []
    out = []
    if m == "jmp":
        try: t = int(o, 16)
        except Exception: t = None
        if t is not None and TLO <= t < THI and (t not in e8heads or t == head): out.append(t)
        return out
    if m[0] == "j":
        try: t = int(o, 16)
        except Exception: t = None
        if t is not None and TLO <= t < THI and t not in e8heads: out.append(t)
    nxt = a + s
    if nxt < THI and (nxt not in e8heads or nxt == head): out.append(nxt)
    return out
_BC = {}
def body(head):
    if head not in _BC:
        seen = set([head]); st = [head]
        while st:
            a = st.pop()
            for x in succ(a, head):
                if x not in seen: seen.add(x); st.append(x)
        _BC[head] = seen
    return _BC[head]
_RC = {}
def retimm(head):
    if head not in _RC:
        imms = []
        for a in body(head):
            k = IDX.get(a)
            if k is None: continue
            _, s, b, m, o = insns[k]
            if m == "ret": imms.append(0 if not o.strip() else int(o, 16))
        _RC[head] = (imms[0] if imms and len(set(imms)) == 1 else None, sorted(set(imms)))
    return _RC[head]
def dsim(head, resmap, targets):
    coll = {}; causes = {}
    stack = [(head, 0, 0)]; seenst = set(); guard = 0
    while stack:
        guard += 1
        if guard > 2_000_000: causes["GUARD"] = {"budget"}; break
        a, D, p = stack.pop()
        if (a, D, p) in seenst: continue
        seenst.add((a, D, p))
        if a in targets: coll.setdefault(a, set()).add(D)
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        if m == "ret": continue
        nD, np, why = D, p, None
        if m == "push": nD, np = D+4, p+4
        elif m == "pop": nD = D-4
        elif m == "sub" and o.startswith("esp, "):
            x = int(o.split(", ", 1)[1], 0); nD, np = D+x, p+x
        elif m == "add" and o.startswith("esp, "):
            x = int(o.split(", ", 1)[1], 0); nD, np = D-x, 0
        elif m == "call":
            if a in resmap:
                r = resmap[a]; nD, np = D-r, max(0, p-r)
            else:
                t = None
                if o and not o.startswith("dword") and not o.startswith("["):
                    try: t = int(o, 16)
                    except Exception: t = None
                if t is not None and t in e8heads:
                    r, allr = retimm(t)
                    if r is None:
                        if p != 0: why = "callee-ambig"
                    else: nD, np = D-r, max(0, p-r)
                elif p != 0: why = "unresolved-indirect"
        elif m == "lea" and o.startswith("esp, "): why = "esp-lea"
        elif m == "mov" and o.startswith("esp, "): why = "esp-mov"
        elif m in ("leave", "pushad", "popad"): why = "esp-shape"
        if why: causes.setdefault(a, set()).add(why); continue
        for x in succ(a, head): stack.append((x, nD, np))
    return coll, causes

FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0, "E": 0x76C290,
          "F": 0x778A20, "T16": 0x5D7590}
ROWS = [0x77884F, 0x77890C, 0x778956, 0x779C3D, 0x779EBD, 0x5CEFC9, 0x5CF10E, 0x5CF162,
        0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7, 0x5D76A9, 0x76C555, 0x778BCF, 0x778DD1, 0x778E24]
NAMES = {0x7EA5F4: "INIClass", 0x7E1B04: "GenericList", 0x7E1AFC: "List<INISection*>",
         0x7E1B0C: "GenericNode", 0x7E1668: "CDFileClass", 0x7E16B0: "CCFileClass"}
sp = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
def lea_of(row):
    k = IDX.get(row)
    if not k: return None, None
    a, s, b, m, o = insns[k-1]
    if m != "lea": return None, None
    mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", o)
    if not mm: return None, None
    d = mm.group(1); return a, int(d, 16) if d.startswith("0x") else int(d)
RES_D = {0x5CEF6B: 4, 0x5CEF78: 4}

print("### F1. 判据可互换性（本线修正引擎）：17 行逐行 ###")
lit = phys = sub = 0; tot = 0
for fr, h in FRAMES.items():
    bd = body(h); rh = [r for r in ROWS if r in bd]
    st = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = sp.match(o)
            if mm and int(mm.group(2), 16) in (0x7E1B04, 0x7E1AFC):
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                st.append((a, d, int(mm.group(2), 16)))
    leas = {r: lea_of(r) for r in rh}
    tg = set(x[0] for x in st) | set(rh) | set(v[0] for v in leas.values() if v[0])
    coll, causes = dsim(h, RES_D if fr == "D" else {}, tg)
    for r in rh:
        la, ld = leas[r]; Dl = coll.get(la)
        if not (Dl and len(Dl) == 1): continue
        W = ld - next(iter(Dl)); tot += 1
        ls = [x for x in st if x[1] == ld]                                      # 同字面 disp
        ps = [x for x in st if coll.get(x[0]) and len(coll[x[0]]) == 1 and x[1]-next(iter(coll[x[0]])) == W]
        ss = [x for x in st if coll.get(x[0]) and len(coll[x[0]]) == 1 and x[1]-next(iter(coll[x[0]])) == W+0xC]
        lit += bool(ls); phys += bool(ps); sub += bool(ss)
        print("  %s %06X W=%s | 同字面disp的GL/List store=%s | 同物理槽=%s | 落 this+0xC 槽=%s" % (
            fr, r, hex(W), [(hex(a), NAMES[i]) for a, d, i in ls],
            [(hex(a), NAMES[i]) for a, d, i in ps], [(hex(a), NAMES[i]) for a, d, i in ss]))
print("  ⇒ 17 行中：存在『同字面 disp 的 GL/List store』=%d；『同物理槽(=W)』=%d；『落 W+0xC(子对象槽)』=%d" % (lit, phys, sub))
print("  ⇒ 判据『同字面 disp』⇒『物理同槽』在本镜像 17 行中成立否：%s" % ("否（恒 0 同行）" if phys == 0 else "部分"))

print("\n### F2. 两阶段 vptr 写同一物理槽（帧 A/B/C/F 的 this+0xC） ###")
for fr, h in [("A", 0x778710), ("B", 0x779B50), ("C", 0x779DD0), ("F", 0x778A20)]:
    bd = body(h)
    seq = []
    tg = set()
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = sp.match(o)
            if mm and int(mm.group(2), 16) in NAMES:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                tg.add(a); seq.append((a, d, int(mm.group(2), 16)))
    la, ld = lea_of([r for r in ROWS if r in bd][0])
    tg.add(la)
    coll, _ = dsim(h, {}, tg)
    Dl = coll.get(la)
    W = ld - next(iter(Dl)) if Dl and len(Dl) == 1 else None
    print("  帧 %s W(this)=%s 各 store 落格（地址序）：" % (fr, hex(W) if W is not None else "-"), end="")
    for a, d, i in sorted(seq):
        Da = coll.get(a)
        if Da and len(Da) == 1:
            P = d - next(iter(Da))
            rel = P - W if W is not None else None
            print("\n      %06X %s disp=%s → P=%s rel(this)=%s" % (a, NAMES[i], hex(d), hex(P),
                  ("+0x%X" % rel) if rel is not None and rel >= 0 else ("-0x%X" % -rel if rel is not None else "-")), end="")
    print()
print("  对照 0x5256F0（本线亲读字节）：[esi]=0x7EA5F4@5256F8 → [esi+0xC]=0x7E1B04@52571E")
print("  RTTI（本线正确二跳解析）：List<INISection*> numBases=2，基类数组含 TD 0x817508 '.?AVGenericList@@'")
col = rd(0x7E1AFC-4); chd = rd(col+0x10); arr = rd(chd+0xC); nb = rd(chd+8)
print("  亲读：CHD=%06X numBases=%s arr=%06X raw=%s" % (chd, nb, arr, rb(arr, 4*nb).hex()))
for i in range(nb):
    b = rd(arr+i*4)
    print("      [%d] BCD=%06X → pTD=%06X 名=%r mdisp=%d" % (i, b, rd(b), cstr(rd(b)+8), struct.unpack("<i", rb(b+4, 4))[0]))

print("\n### F3. 帧 D 的 [esp+0x68] 槽连续性（对象身份链） ###")
h = 0x5CEEF0
pts = [0x5CEEFC, 0x5CEF5E, 0x5CEF67, 0x5CEF6B, 0x5CEF6E, 0x5CEF74, 0x5CEF78, 0x5CEF41]
coll, causes = dsim(h, RES_D, set(pts))
for a in pts:
    D = coll.get(a)
    if not D: print("  %06X 剪枝 %s" % (a, causes.get(a))); continue
    it = insns[IDX[a]]
    ds = "0x68" in it[4]
    P = (0x68 - next(iter(D))) if ds and len(D) == 1 else None
    print("  %06X %-20s %s %s D=%s P=%s" % (a, it[2], it[3], it[4],
          hex(next(iter(D))) if len(D) == 1 else sorted(hex(x) for x in D), hex(P) if P is not None else "-"))
print("  0x473A80 ctor 体：mov esi,ecx; … mov [esi],0x7E16B0@473A9B; mov eax,esi; ret（本线亲读，见 brev_e/brev_d 留档）")
print("  ⇒ ecx@5CEEFC 与 eax-load@5CEF5E 若同物理槽，则 [eax+8] 的 vtable 即 0x7E16B0（CCFileClass）")
