# -*- coding: utf-8 -*-
"""brev_probe_b.py — 定位本线 brev_probe_a 与 _r064rev_probe3 的 D 记账差异（帧 A 为主）。

打印：
  1) 帧 A 序言逐条 + 从 head 到 0x77884F 的线性轨迹，每个 call 的本线 ret-imm 结算；
  2) 帧 A 路径敏感 DFS 中，到达 lea@0x77884B 的所有 (D,p) 及其前驱链（截断显示）；
  3) 同法对帧 B/C 的 lea；
  4) 对照：probe3 声称 A:D(lea)=0xD0 / GL-stamp D=0xC4 / INI-stamp D=0xC8。
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
    nm = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((nm, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva-ib <= rva < sva-ib+vsz:
            fo = rp + (rva-(sva-ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
tn, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
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
e8heads = set()
for a, s, b, m, o in insns:
    if m == "call" and b[:2] == "e8" and len(b) == 10:
        try: t = int(o, 16)
        except Exception: continue
        if TLO <= t < THI: e8heads.add(t)
print("insns=%d heads=%d" % (len(insns), len(e8heads)))

def body_of(head):
    seen = set([head]); stack = [head]
    while stack:
        a = stack.pop()
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        su = []
        if m == "ret": pass
        elif m == "jmp":
            try: t = int(o, 16)
            except Exception: t = None
            if t is not None and TLO <= t < THI and (t not in e8heads or t == head): su.append(t)
        elif m[0] == "j":
            try: t = int(o, 16)
            except Exception: t = None
            if t is not None and TLO <= t < THI and t not in e8heads: su.append(t)
            nxt = a + s
            if nxt < THI and (nxt not in e8heads or nxt == head): su.append(nxt)
        else:
            nxt = a + s
            if nxt < THI and (nxt not in e8heads or nxt == head): su.append(nxt)
        for x in su:
            if x not in seen: seen.add(x); stack.append(x)
    return seen

_RC = {}
def ret_imm(head):
    if head in _RC: return _RC[head]
    imms = []
    for a in body_of(head):
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        if m == "ret":
            imms.append(0 if not o.strip() else int(o, 16))
    _RC[head] = ((imms[0] if imms and len(set(imms)) == 1 else None), sorted(set(imms)), len(body_of(head)))
    return _RC[head]

print("\n== 帧 A 序言 + 线性轨迹（head 0x778710 → 0x77884F），每个 call 的本线 ret-imm ==")
D = 0; p = 0; k0 = IDX[0x778710]
MARK = {0x7787C0: "GL-stamp", 0x7787D1: "List-stamp", 0x7787DB: "this-lea", 0x7787F7: "INI-stamp",
        0x77884B: "W-lea", 0x77884F: "witness call"}
while True:
    a, s, b, m, o = insns[k0]
    tag = MARK.get(a, "")
    line = "  %06X %-22s %-6s %-28s D=0x%-4X p=%-4d %s" % (a, b, m, o, D, p, tag)
    if m == "push": D += 4; p += 4
    elif m == "pop": D -= 4
    elif m == "sub" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D += x; p += x
    elif m == "add" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D -= x; p = 0
    elif m == "call":
        try: t = int(o, 16)
        except Exception: t = None
        if t is not None and t in e8heads:
            r, allr, sz = ret_imm(t)
            if r is None:
                line += "   [callee %06X ret-ambig %s]" % (t, allr)
            else:
                D -= r; p = max(0, p - r); line += "   [callee %06X ret=%d]" % (t, r)
        else:
            line += "   [external/indirect]"
    print(line)
    if a >= 0x77884F: break
    if m.startswith("j"): print("      ^ BRANCH %s %s  (linear sim ignores it)" % (m, o))
    k0 += 1
print("  ⇒ 线性法得 D(W-lea)=0x%X ; probe3 声称 0xD0，GL-stamp 0xC4，INI-stamp 0xC8" % D)

print("\n== 差异定位：路径敏感 DFS，收集到 0x77884B 的 (D,p) 与其前驱 ==")
head = 0x778710
bd = body_of(head)
def succ(a):
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

RES = {}
states = {}   # (a,D,p) -> parent
stack = [(head, 0, 0)]; seen = set(); parents = {}
while stack:
    a, Dv, pv = stack.pop()
    if (a, Dv, pv) in seen: continue
    seen.add((a, Dv, pv))
    k = IDX.get(a)
    if k is None: continue
    _, s, b, m, o = insns[k]
    if m == "ret": continue
    nD, np = Dv, pv; prune = False
    if m == "push": nD, np = Dv+4, pv+4
    elif m == "pop": nD = Dv-4
    elif m == "sub" and o.startswith("esp, "):
        x = int(o.split(", ", 1)[1], 0); nD, np = Dv+x, pv+x
    elif m == "add" and o.startswith("esp, "):
        x = int(o.split(", ", 1)[1], 0); nD, np = Dv-x, 0
    elif m == "call":
        if a in RES: r = RES[a]; nD, np = Dv-r, max(0, pv-r)
        else:
            t = None
            if o and not o.startswith("dword"):
                try: t = int(o, 16)
                except Exception: t = None
            if t is not None and t in e8heads:
                r, allr, sz = ret_imm(t)
                if r is None:
                    if pv != 0: prune = True
                else: nD, np = Dv-r, max(0, pv-r)
            else:
                if pv != 0: prune = True
    elif m == "lea" and o.startswith("esp, "): prune = True
    elif m == "mov" and o.startswith("esp, "): prune = True
    elif m in ("leave", "pushad", "popad"): prune = True
    if prune: continue
    for x in succ(a):
        if x in bd or True:
            parents.setdefault((x, nD, np), []).append((a, Dv, pv))
            stack.append((x, nD, np))
target = [key for key in seen if key[0] == 0x77884B]
print("  到达 0x77884B 的状态：%s" % sorted([(hex(a), hex(d), pp) for a, d, pp in target]))
def chain_of(key, depth=0, seen_c=None):
    seen_c = seen_c or set()
    if key in seen_c or depth > 40: return
    seen_c.add(key)
    par = parents.get(key, [])
    print("    %*s← %06X D=0x%X p=%d  (from %s)" % (depth*2, "", key[0], key[1], key[2],
          sorted(["%06X/0x%X/%d" % pa for pa in par])[:4]))
    for pa in par[:3]:
        chain_of(pa, depth+1, seen_c)
for key in sorted(target, key=lambda x: x[1]):
    print("  == 路径 to %06X D=0x%X ==" % (key[0], key[1]))
    chain_of(key)
