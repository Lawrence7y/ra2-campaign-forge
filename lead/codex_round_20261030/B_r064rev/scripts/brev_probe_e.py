# -*- coding: utf-8 -*-
"""brev_probe_e.py — 本线两项独立检验：

 E1. 「错位 0xC」的第三种读法：GL/List stamp 落格是否 = witness this + 0xC（内嵌子对象），
     并与 0x5256F0（INIClass 复位体）的 [esi]/[esi+0xC]/[esi+0x10]/[esi+0x1C] 偏移逐项对照。
 E2. HYPV 依赖性「结论翻转风险」网格：帧 D 承重假设 = 两处间接 call 的 ret-imm（R-064 说 4）。
     对本线自算的 D 记账，扫描 (call1,call2) ∈ {0,4,8,0xC} × 三处未落实 call ∈ {0,4,8}，
     看 7 行的 W 命中是否仍唯一命中 INIClass（=归一化是否真不依赖假设）。
 E3. 帧 D 间接 call 的 this 数据流（0x5CEF57..0x5CEF85）——对象身份假设的可证性。
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
                    if r is None and p != 0: why = "callee-ambig"
                    elif r is not None: nD, np = D-r, max(0, p-r)
                elif p != 0: why = "unresolved"
        elif m == "lea" and o.startswith("esp, "): why = "esp-lea"
        elif m == "mov" and o.startswith("esp, "): why = "esp-mov"
        elif m in ("leave", "pushad", "popad"): why = "esp-shape"
        if why: causes.setdefault(a, set()).add(why); continue
        for x in succ(a, head): stack.append((x, nD, np))
    return coll, causes

ROWS = [0x77884F, 0x77890C, 0x778956, 0x779C3D, 0x779EBD, 0x5CEFC9, 0x5CF10E, 0x5CF162,
        0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7, 0x5D76A9, 0x76C555, 0x778BCF, 0x778DD1, 0x778E24]
FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0, "E": 0x76C290,
          "F": 0x778A20, "T16": 0x5D7590}
NAMES = {0x7EA5F4: "INIClass", 0x7E1B04: "GenericList", 0x7E1AFC: "List<INISection*>",
         0x7E1B0C: "GenericNode", 0x7E1668: "CDFileClass", 0x7E16B0: "CCFileClass"}
store_pat = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
def lea_of(row):
    k = IDX.get(row)
    if not k: return None, None
    a, s, b, m, o = insns[k-1]
    if m != "lea": return None, None
    mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", o)
    if not mm: return None, None
    d = mm.group(1); return a, int(d, 16) if d.startswith("0x") else int(d)

print("### E1. 错位 0xC 的第三种读法：GL/List 落格 vs witness this+偏移 ###")
print("  参照：0x5256F0（INIClass 复位体）本线亲读：[esi]=0x7EA5F4@5256F8 ; [esi+0xC]=0x7E1B04@52571E ;")
print("        lea eax,[esi+0x1C]→[eax]=0x7E1B0C@525760 ; lea eax,[esi+0x10]→[eax]=0x7E1B0C@52578D")
print("        且 0x40E320 体（@40E32A）置 [that]=0x7E1B0C(GenericNode)，本线亲读。")
for fr, h in FRAMES.items():
    bd = body(h)
    rows_here = [r for r in ROWS if r in bd]
    if not rows_here: continue
    stamps = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = store_pat.match(o)
            if mm and int(mm.group(2), 16) in NAMES:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                stamps.append((a, d, int(mm.group(2), 16)))
    leas = {r: lea_of(r) for r in rows_here}
    tg = set(x[0] for x in stamps) | set(rows_here) | set(v[0] for v in leas.values() if v[0])
    RES = {0x5CEF6B: 4, 0x5CEF78: 4} if fr == "D" else {}
    coll, causes = dsim(h, RES, tg)
    for r in rows_here:
        la, ld = leas[r]; Dl = coll.get(la)
        if not (Dl and len(Dl) == 1): continue
        W = ld - next(iter(Dl))
        rel = []
        for a, d, imm in stamps:
            Da = coll.get(a)
            if Da and len(Da) == 1:
                P = d - next(iter(Da))
                rel.append((NAMES[imm], hex(P), P - W))
        ini = [x for x in rel if x[0] == "INIClass" and x[2] == 0]
        print("  %s row %06X W=%s | 各 stamp 相对 witness this 的偏移=%s | INIClass@+0=%s" % (
            fr, r, hex(W), [(n, p, "+0x%X" % off if off >= 0 else "-0x%X" % -off) for n, p, off in rel], bool(ini)))
        break  # 每帧取首行即可（同帧同 W）

print("\n### E2. 帧 D 承重假设网格：两处间接 call 的 ret-imm 取 0/4/8/0xC 会翻转结论吗 ###")
h = 0x5CEEF0; bd = body(h)
rowsD = [r for r in ROWS if r in bd]
stampsD = []
for a, s, b, m, o in insns:
    if m == "mov" and a in bd:
        mm = store_pat.match(o)
        if mm and int(mm.group(2), 16) in NAMES:
            d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
            stampsD.append((a, d, int(mm.group(2), 16)))
leasD = {r: lea_of(r) for r in rowsD}
tgD = set(x[0] for x in stampsD) | set(rowsD) | set(v[0] for v in leasD.values() if v[0])
UNRES = [0x5CF038, 0x5CF350, 0x5CF556]
print("  (c1,c2)=两处可落实间接call的假设ret ; u=三处未落实call的假设ret(剪枝=None)")
for c1 in (0, 4, 8, 0xC):
    for u in (None, 0, 4, 8):
        res = {0x5CEF6B: c1, 0x5CEF78: c1}
        if u is not None:
            for x in UNRES: res[x] = u
        coll, causes = dsim(h, res, tgD)
        closed = 0; hitini = 0; hitgl = 0; amb = 0
        for r in rowsD:
            la, ld = leasD[r]; Dl = coll.get(la)
            if not (Dl and len(Dl) == 1): continue
            W = ld - next(iter(Dl)); closed += 1
            hits = [imm for a, d, imm in stampsD
                    if coll.get(a) and len(coll[a]) == 1 and d - next(iter(coll[a])) == W]
            if 0x7EA5F4 in hits: hitini += 1
            if 0x7E1B04 in hits: hitgl += 1
            if len(hits) > 1: amb += 1
        print("    c1=%-4s u=%-5s 闭合=%d/7 W命中INIClass=%d W命中GenericList=%d 多命中=%d 剪枝点数=%d" % (
            hex(c1), str(u), closed, hitini, hitgl, amb, len(causes)))

print("\n### E2b. 其余六帧（无间接假设）在 STRICT 下是否闭合（应恒等） ###")
for fr, h in FRAMES.items():
    if fr == "D": continue
    bd = body(h); rows_here = [r for r in ROWS if r in bd]
    stamps = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = store_pat.match(o)
            if mm and int(mm.group(2), 16) in NAMES:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                stamps.append((a, d, int(mm.group(2), 16)))
    leas = {r: lea_of(r) for r in rows_here}
    tg = set(x[0] for x in stamps) | set(rows_here) | set(v[0] for v in leas.values() if v[0])
    coll, causes = dsim(h, {}, tg)
    ok = 0; ini = 0; gl = 0
    for r in rows_here:
        la, ld = leas[r]; Dl = coll.get(la)
        if not (Dl and len(Dl) == 1): continue
        W = ld - next(iter(Dl)); ok += 1
        hits = [imm for a, d, imm in stamps if coll.get(a) and len(coll[a]) == 1 and d - next(iter(coll[a])) == W]
        ini += 0x7EA5F4 in hits; gl += 0x7E1B04 in hits
    print("  %s 行=%d 闭合=%d INIClass命中=%d GenericList命中=%d 剪枝点=%s" % (
        fr, len(rows_here), ok, ini, gl, sorted("%06X" % k for k in causes if isinstance(k, int))))

print("\n### E3. 帧 D 两处间接 call 的 this 数据流（对象身份假设） ###")
_lo = IDX[0x5CEEF0]
_hi = _lo
while _hi + 1 < len(insns) and insns[_hi+1][0] <= 0x5CEF85:
    _hi += 1
for j in range(_lo, _hi+1):
    a, s, b, m, o = insns[j]
    tag = "   <== 间接 call" if a in (0x5CEF6B, 0x5CEF78) else ""
    print("  %06X %-20s %s %s%s" % (a, b, m, o, tag))
print("  → 判定：eax/edx 在 call 前是否可静态钉为 0x7E16B0(CCFileClass) 对象的实例？")
print("    R-064 主张：对象=0x473A80 构造的 CCFileClass，rb(0x473A9B,6)=%s" % rb(0x473A9B, 6).hex())
print("    0x473A80 起：")
for ins in md.disasm(rb(0x473A80, 0x28), 0x473A80):
    print("      %06X %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
_end78 = _lo
while _end78 + 1 < len(insns) and insns[_end78+1][0] <= 0x5CEF78:
    _end78 += 1
found = [insns[j][0] for j in range(_lo, _end78+1)
         if insns[j][3] == "call" and insns[j][4] == "0x473a80"]
print("    帧 D 头..0x5CEF78 范围内 call 0x473A80 的站点：%s" % [hex(x) for x in found])
print("    0x5CEEF0 起 10 条（入口区）：")
for j in range(_lo, _lo+10):
    a, s, b, m, o = insns[j]; print("      %06X %-20s %s %s" % (a, b, m, o))
