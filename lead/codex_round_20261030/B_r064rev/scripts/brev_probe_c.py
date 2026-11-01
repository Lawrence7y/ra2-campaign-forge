# -*- coding: utf-8 -*-
"""brev_probe_c.py — 本线（B 线）独立复核三件事，全部自写实现：

  I.  七帧全列：我自己从帧头线性走 + 路径敏感 DFS，独立算 D(stamp)/D(lea)、
      P=disp−D、W=disp−D(lea)，核「错位恒 0xC」与「17/17 W 命中 INIClass」。
 II. 「W 槽最后写者」审计（R-064 §7 局限 3 自认只扫字面 mov [esp+X]）：
      对每个 witness 行，列出从命中 stamp 到该 lea 之间**所有** esp 基址写入
      （含 dword/word/byte、含 reg 源、含 89/C6/66 形态），换算物理格，
      看是否有别的写者落在 W 上（若有，归属弱化）。
 III. 帧 D 两处虚拟 call 的 this 来源（对象身份数据流）——这是 帧 D 7 行 D 记账
      的承重假设（PURE 模式已证：不落实这两处则 7 行全剪枝）。
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
            fo = rp + (rva-(sva-ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b) == 4 else None
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
    if head in _BC: return _BC[head]
    seen = set([head]); st = [head]
    while st:
        a = st.pop()
        for x in succ(a, head):
            if x not in seen: seen.add(x); st.append(x)
    _BC[head] = seen; return seen
def retimm(head):
    imms = []
    for a in body(head):
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        if m == "ret": imms.append(0 if not o.strip() else int(o, 16))
    return (imms[0] if imms and len(set(imms)) == 1 else None), sorted(set(imms))

def effect(a, D, p, resmap):
    """返回 (nD,np,prune_reason)。"""
    _, s, b, m, o = insns[IDX[a]]
    if m == "push": return D+4, p+4, None
    if m == "pop":  return D-4, p, None
    if m == "sub" and o.startswith("esp, "):
        x = int(o.split(", ", 1)[1], 0); return D+x, p+x, None
    if m == "add" and o.startswith("esp, "):
        x = int(o.split(", ", 1)[1], 0); return D-x, 0, None
    if m == "call":
        if a in resmap:
            r = resmap[a]; return D-r, max(0, p-r), None
        t = None
        if o and not o.startswith("dword") and not o.startswith("["):
            try: t = int(o, 16)
            except Exception: t = None
        if t is not None and t in e8heads:
            r, allr = retimm(t)
            if r is None:
                return D, p, ("callee-%06X-ambig%s" % (t, allr)) if p != 0 else None
            return D-r, max(0, p-r), None
        return D, p, ("indirect-unresolved p=%d" % p) if p != 0 else None
    if m == "lea" and o.startswith("esp, "): return D, p, "esp-rewrite-lea"
    if m == "mov" and o.startswith("esp, "): return D, p, "esp-rewrite-mov"
    if m in ("leave", "pushad", "popad"): return D, p, "esp-shape"
    return D, p, None

FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0,
          "E": 0x76C290, "F": 0x778A20, "T16": 0x5D7590}
ROWS = [0x77884F, 0x77890C, 0x778956, 0x779C3D, 0x779EBD,
        0x5CEFC9, 0x5CF10E, 0x5CF162, 0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7,
        0x5D76A9, 0x76C555, 0x778BCF, 0x778DD1, 0x778E24]
RES = {0x5CEF6B: 4, 0x5CEF78: 4}
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

def dsim(head, resmap, targets):
    coll = {}; causes = {}
    stack = [(head, 0, 0)]; seenst = set(); guard = 0
    while stack:
        guard += 1
        if guard > 2_000_000: causes["GUARD"] = "budget"; break
        a, D, p = stack.pop()
        if (a, D, p) in seenst: continue
        seenst.add((a, D, p))
        if a in targets: coll.setdefault(a, set()).add(D)
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        if m == "ret": continue
        nD, np, why = effect(a, D, p, resmap)
        if why: causes.setdefault(a, set()).add(why); continue
        for x in succ(a, head): stack.append((x, nD, np))
    return coll, causes

print("### I. 七帧独立 D 记账（本线自写）：P/W 与错位 ###")
summary = []
for fr, h in FRAMES.items():
    bd = body(h)
    rows_here = [r for r in ROWS if r in bd]
    stamps = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = store_pat.match(o)
            if mm and int(mm.group(2), 16) in NAMES:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                stamps.append((a, d, int(mm.group(2), 16)))
    leas = {}
    for r in rows_here:
        la, ld = lea_of(r)
        if la: leas[r] = (la, ld)
    tg = set(x[0] for x in stamps) | set(rows_here) | set(v[0] for v in leas.values())
    coll, causes = dsim(h, RES if fr == "D" else {}, tg)
    print("\n-- 帧 %s head=%06X 行=%d stamp=%d --" % (fr, h, len(rows_here), len(stamps)))
    for r in rows_here:
        la, ld = leas.get(r, (None, None))
        Dl = coll.get(la); Dr = coll.get(r)
        W = (ld - next(iter(Dl))) if (Dl and len(Dl) == 1) else None
        hits = []
        offs = []
        for a, d, imm in stamps:
            Da = coll.get(a)
            if Da and len(Da) == 1:
                P = d - next(iter(Da))
                if P == W: hits.append((a, imm, P))
                else: offs.append((a, imm, P, None if W is None else P - W))
        uniq_stamp = len(hits) == 1
        summary.append((fr, r, W, hits, offs, Dr, Dl))
        print("  row %06X Dcall=%s leaD=%s disp=%s W=%s | 命中=%s | 其余错位=%s" % (
            r, sorted(hex(x) for x in Dr) if Dr else "-", sorted(hex(x) for x in Dl) if Dl else "-",
            hex(ld) if ld is not None else "-", hex(W) if W is not None else "-",
            [(hex(a), NAMES[i], hex(p)) for a, i, p in hits],
            [(hex(a), NAMES[i], hex(p), ("+%d" % off) if off is not None else "-") for a, i, p, off in offs]))
    if causes:
        print("   剪枝因:", {("%06X" % k if isinstance(k, int) else k): sorted(v) for k, v in causes.items()})

print("\n  == 汇总 ==")
nW = sum(1 for x in summary if x[2] is not None)
nHitIni = sum(1 for x in summary if x[2] is not None and any(i == 0x7EA5F4 for a, i, p in x[3]))
nHitGl = sum(1 for x in summary if x[2] is not None and any(i == 0x7E1B04 for a, i, p in x[3]))
nUni = sum(1 for x in summary if x[2] is not None and len(x[3]) == 1)
offs = sorted(set(o for x in summary for a, i, p, o in x[4] if i == 0x7E1B04 and o is not None))
print("  17 行中 W 可算=%d；W 命中 INIClass=%d；W 命中 GenericList=%d；命中唯一=%d" % (nW, nHitIni, nHitGl, nUni))
print("  GenericList-stamp 与 W 的错位值集合 = %s（=12 即 0xC）" % offs)
print("  帧 A/B/C/F 之外是否存在同帧 GenericList stamp：见上表（无 stamp 者不参与错位统计）")

print("\n### II. W 槽『最后写者』审计（本线新做，R-064 局限 3） ###")
wpat_all = re.compile(r"^(?:dword|word|byte) ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (.+)$")
for fr, h in FRAMES.items():
    bd = body(h)
    rows_here = [r for r in ROWS if r in bd]
    tgt = set()
    for r in rows_here:
        la, ld = lea_of(r)
        if la: tgt.add(la)
    # 把所有 esp 基址 store 也纳入 target，一次 dsim 拿到全部 D
    stores = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in bd:
            mm = wpat_all.match(o)
            if mm:
                d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                stores.append((a, d, mm.group(2)))
                tgt.add(a)
    coll, causes = dsim(h, RES if fr == "D" else {}, tgt)
    for r in rows_here:
        la, ld = lea_of(r)
        if not la: continue
        Dl = coll.get(la)
        if not (Dl and len(Dl) == 1): continue
        W = ld - next(iter(Dl))
        writers = []
        for a, d, src in stores:
            Da = coll.get(a)
            if Da and len(Da) == 1:
                P = d - next(iter(Da))
                if P == W: writers.append((a, d, src, P))
        writers.sort()
        last_before = [x for x in writers if x[0] < la]
        print("  %s row %06X W=%s | lea@%06X | 落 W 格的 esp 写者(地址序)=%s | lea 前最后写者=%s" % (
            fr, r, hex(W), la,
            [(hex(a), "disp" + hex(d), s[:22]) for a, d, s, p in writers][-6:],
            hex(last_before[-1][0]) if last_before else "无"))

print("\n### III. 帧 D 两处虚拟 call 的 this 来源（对象身份数据流） ###")
k = IDX[0x5CEF57] if 0x5CEF57 in IDX else IDX[0x5CEF41]
for j in range(IDX[0x5CEF41]-2, IDX[0x5CEF85]+3):
    a, s, b, m, o = insns[j]
    tag = ""
    if a in (0x5CEF6B, 0x5CEF78): tag = "   <== 虚拟 call（本线需落实）"
    if a == 0x5CEF41: tag = "   <== INIClass stamp"
    print("  %06X %-22s %s %s%s" % (a, b, m, o, tag))
print("  期望链：eax/edx ← 某 thiscall 返回值或 lea；需证明其对象 vptr=0x7E16B0(CCFileClass)")
print("  0x473A80 头 12 条：")
for ins in md.disasm(rb(0x473A80, 0x30), 0x473A80):
    print("    %06X %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
