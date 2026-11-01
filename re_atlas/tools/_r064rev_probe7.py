# -*- coding: utf-8 -*-
"""_r064rev_probe7.py — 补充：帧 A/B/C 全 stamp（含 0x7E1AFC/0x7E1B0C）路径敏感落格 + W 命中唯一性
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
        t = int(o, 16) if o.startswith("0x") else None
        if t is not None and TLO <= t < THI: e8set.add(t)

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
    if head not in _RC:
        body, seen = closure(head)
        imms = []
        for a in body:
            k = IDX.get(a)
            if k is not None and insns[k][3] == "ret":
                o = insns[k][4]
                imms.append(int(o, 16) if o.startswith("0x") else (int(o) if o.strip().isdigit() else 0))
        _RC[head] = ((imms[0] if imms and len(set(imms)) == 1 else None), body, seen, imms)
    return _RC[head]
def callee_retimm(t): return ret_imm(t)[0]

RES = {0x5CEF6B: 4, 0x5CEF78: 4}
def dsim(head, targetset):
    v, body, seen, _ = ret_imm(head)
    collect = {}; causes = {}
    stack = [(head, 0, 0)]; seenst = set(); guard = 0
    while stack:
        guard += 1
        if guard > 3_000_000: break
        a, D, p = stack.pop()
        if (a, D, p) in seenst: continue
        seenst.add((a, D, p))
        k = IDX.get(a)
        if k is None:
            causes.setdefault("undecoded@%06X" % a, 1); continue
        _, s, b, m, o = insns[k]
        if a in targetset: collect.setdefault(a, set()).add(D)
        if m == "ret": continue
        nD, np = D, p; pruned = False
        if m == "push": nD, np = D + 4, p + 4
        elif m == "pop": nD = D - 4
        elif m == "sub" and o.startswith("esp, "):
            x = int(o.split(", ")[1], 0); nD, np = D + x, p + x
        elif m == "add" and o.startswith("esp, "):
            x = int(o.split(", ")[1], 0); nD, np = D - x, 0
        elif m == "call":
            if a in RES:
                r = RES[a]; nD, np = D - r, max(0, p - r)
            else:
                t = int(o, 16) if (o.startswith("0x")) else None
                if t is None or t not in e8set:
                    if p != 0: causes.setdefault("%06X call-unresolved" % a, 1); pruned = True
                else:
                    r = callee_retimm(t)
                    if r is None:
                        if p != 0: causes.setdefault("%06X callee-%06X-ambig" % (a, t), 1); pruned = True
                    else: nD, np = D - r, max(0, p - r)
        elif m == "lea" and o.startswith("esp, "): causes.setdefault("%06X esp-lea" % a, 1); pruned = True
        elif m == "mov" and o.startswith("esp, "): causes.setdefault("%06X esp-mov" % a, 1); pruned = True
        elif m in ("leave", "pushad", "popad"): causes.setdefault("%06X esp-shape" % a, 1); pruned = True
        if pruned: continue
        for x in body.get(a, ()): stack.append((x, nD, np))
    return collect, causes

IMMS = {0x7EA5F4: "INIClass", 0x7E1B04: "GenericList", 0x7E1AFC: "List<INISection*>", 0x7E1B0C: "GenericNode", 0x7E1668: "CDFileClass", 0x7E16B0: "CCFileClass"}
pat = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
FR = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0}
ROWS = {"A": [0x77884F, 0x77890C, 0x778956], "B": [0x779C3D], "C": [0x779EBD]}
CTOR_LEA = {"A": [0x7787DB], "B": [0x779BCE], "C": [0x779E4E]}
CTOR_CALL = {"A": [0x7787FF], "B": [0x779BF2], "C": [0x779E72]}
for fr, h in FR.items():
    v, body, seen, _ = ret_imm(h)
    allst = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in seen:
            mm = pat.match(o)
            if mm:
                imm = int(mm.group(2), 16)
                if imm in IMMS:
                    d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                    allst.append((a, d, imm))
    tgt = set(a for a, d, i in allst) | set(ROWS[fr]) | set(CTOR_LEA[fr]) | set(CTOR_CALL[fr])
    for r in ROWS[fr]:
        k = IDX[r]
        if insns[k-1][3] == "lea": tgt.add(insns[k-1][0])
    collect, causes = dsim(h, tgt)
    print("\n== 帧 %s head=%06X 路径敏感全 stamp 落格 ==" % (fr, h))
    # 构造链（R-064 §3 补强）：this-lea 同格 + call 0x525A10
    for la in CTOR_LEA[fr]:
        mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", insns[IDX[la]][4])
        d = int(mm.group(1), 16) if mm.group(1).startswith("0x") else int(mm.group(1))
        Dl = collect.get(la)
        Pc = d - next(iter(Dl)) if Dl and len(Dl) == 1 else None
        cc = insns[IDX[la]+1] if False else None
        nxtk = IDX[la]
        calls = []
        j = nxtk + 1
        while j < len(insns) and insns[j][0] - la <= 0x30:
            if insns[j][3] == "call" and insns[j][4] == "0x525a10": calls.append(insns[j][0])
            j += 1
        print("  ctor-lea %06X disp=%s D=%s P=%s → call0x525A10@%s" % (
            la, hex(d), ("0x%X" % next(iter(Dl))) if Dl and len(Dl)==1 else (sorted(hex(x) for x in Dl) if Dl else "剪枝"),
            hex(Pc) if Pc is not None else "-", [hex(x) for x in calls]))
    # W
    for r in ROWS[fr]:
        kk = IDX[r]; lea = insns[kk-1][0]
        mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", insns[kk-1][4])
        d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
        Dl = collect.get(lea)
        W = d - next(iter(Dl)) if Dl and len(Dl) == 1 else None
        print("  row %06X W=%s" % (r, hex(W) if W is not None else "-"))
    seenW = None
    for a, d, imm in sorted(allst):
        Da = collect.get(a)
        info = ""
        if Da and len(Da) == 1:
            P = d - next(iter(Da))
            info = "D=0x%X P=%s" % (next(iter(Da)), hex(P))
            if imm == 0x7EA5F4: seenW = P
        else:
            info = "D-ambig%s" % (sorted(hex(x) for x in Da) if Da else "剪枝")
        print("  stamp %06X %s disp=%s %s" % (a, IMMS[imm], hex(d), info))
    print("  witness W=%s → 命中 stamp：%s" % (
        hex(seenW) if seenW else "?",
        [(hex(a), IMMS[i], "P=" + hex(d - next(iter(collect[a])))) for a, d, i in sorted(allst)
         if collect.get(a) and len(collect[a]) == 1 and d - next(iter(collect[a])) == seenW]))
    print("  剪枝因:", sorted(causes.keys()))
