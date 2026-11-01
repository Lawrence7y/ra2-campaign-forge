# -*- coding: utf-8 -*-
"""brev_probe_a.py — 本线（B 线 R-064rev 续办）自写判据，独立于 _r064rev_probe1..7 与 R-064 probe。

目的（对应任务复核点 2 的 (a)/(b)）：
  (a) 盘上字节：R-062 三窗与 R-063b/R-064 补 stamp 的 8 字节窗，逐字节亲读；
  (b) 物理槽配对：用「我自己的」D 记账器（路径敏感 DFS + 我自己的 ret-imm 解法）
      独立算 P = disp - D、W = disp - D(lea)，核 0xC 恒错位与 17/17 W 命中；
  (c) 判据可互换性：证明「同字面 disp」与「同物理槽」在 esp 移动下不等价，
      并统计 17 行里「同字面 disp 的 store 恰也在同物理槽」的行数（若为 0，则
      R-062 §2 的 5 行配对命题在其自身判据下也从未成立）。

只读 gamemd.exe；不启动游戏。
"""
import struct, hashlib, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
IMG_SHA = hashlib.sha256(raw).hexdigest()
print("[identity] gamemd.exe sha256 =", IMG_SHA)
assert IMG_SHA == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", raw, e_lfanew + 20)[0]
opt = e_lfanew + 24
ib = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
secs = []
for i in range(nsec):
    nm = raw[tab + i*40: tab + i*40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    secs.append((nm, ib + va, vsz, rp, rsz))

def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            return raw[fo:fo+n] if fo < rp + rsz else bytes(n)
    return b""

def rd(va):
    b = rb(va, 4)
    return int.from_bytes(b, "little") if len(b) == 4 else None

(tn, tva, tvsz, trp, trsz) = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []
cur = TLO; end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        break
    if got is None:
        cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
print("[decode] insns=%d range=%06X..%06X" % (len(insns), insns[0][0], insns[-1][0]))

# ---------- 我自己的 E8 头集合 + 我自己的闭包 ----------
e8heads = set()
for a, s, b, m, o in insns:
    if m == "call" and b[:2] == "e8" and len(b) == 10:
        try: t = int(o, 16)
        except (ValueError, TypeError): continue
        if TLO <= t < THI:
            e8heads.add(t)
print("[heads] distinct E8 targets =", len(e8heads))

def succ_of(a, head):
    k = IDX.get(a)
    if k is None: return []
    _, s, b, m, o = insns[k]
    if m == "ret": return []
    def ok(t):
        return TLO <= t < THI and (t not in e8heads or t == head)
    if m == "jmp":
        try: t = int(o, 16)
        except (ValueError, TypeError): return []
        return [t] if ok(t) else []
    out = []
    if m[0] == "j":
        try: t = int(o, 16)
        except (ValueError, TypeError): t = None
        if t is not None and TLO <= t < THI and t not in e8heads:
            out.append(t)
    nxt = a + s
    if nxt < THI:
        # fallthrough into another head is not part of this body
        if nxt not in e8heads or nxt == head:
            out.append(nxt)
    return out

_CACHE = {}
def body_of(head):
    if head in _CACHE: return _CACHE[head]
    seen = set([head]); stack = [head]
    while stack:
        a = stack.pop()
        for x in succ_of(a, head):
            if x not in seen:
                seen.add(x); stack.append(x)
    _CACHE[head] = seen
    return seen

def my_ret_imm(head):
    """我自己的 ret-imm：闭包内所有 ret 的 imm 集合；唯一才返回值，否则 None。"""
    imms = set()
    for a in body_of(head):
        k = IDX.get(a)
        if k is None: continue
        _, s, b, m, o = insns[k]
        if m == "ret":
            imms.add(0 if not o.strip() else int(o, 16))
    return (next(iter(imms)) if len(imms) == 1 else None), sorted(imms)

# ---------- (a) 盘上字节：三窗 + 补 stamp ----------
print("\n### (a) 盘上 8 字节窗（本线亲读） ###")
PIN = [
    ("R-062 窗1 0x7787C0", 0x7787C0, "c7442438041b7e00"),
    ("R-062 窗2 0x779BB3", 0x779BB3, "c7442424041b7e00"),
    ("R-062 窗3 0x779E33", 0x779E33, "c7442424041b7e00"),
    ("R-064 补 A  0x7787F7", 0x7787F7, "c7442430f4a57e00"),
    ("R-064 补 B  0x779BEA", 0x779BEA, "c744241cf4a57e00"),
    ("R-064 补 C  0x779E6A", 0x779E6A, "c744241cf4a57e00"),
    ("R-063b 0x5CEF41", 0x5CEF41, "c7442428f4a57e00"),
    ("R-063b 0x76C4A4", 0x76C4A4, "c7442430f4a57e00"),
    ("R-063b 0x778B20", 0x778B20, "c744242cf4a57e00"),
    ("T16 0x5D761D", 0x5D761D, "c7442478f4a57e00"),
]
for label, va, exp in PIN:
    got = rb(va, 8).hex()
    print("  %-22s %06X: %s  exp=%s  %s" % (label, va, got, exp, "MATCH" if got == exp else "MISMATCH"))

print("\n  0x5256F0 体内双 stamp：")
print("    rb(0x5256F8,6)=%s (mov [esi],0x7EA5F4 期望 c706f4a57e00)" % rb(0x5256F8, 6).hex())
print("    rb(0x52571E,7)=%s (mov [esi+0xC],0x7E1B04 期望 c7460c041b7e00)" % rb(0x52571E, 7).hex())
print("    rb(0x525760,7)=%s rb(0x52578D,7)=%s (GenericNode 头件候选)" % (rb(0x525760,7).hex(), rb(0x52578D,7).hex()))

# ---------- (b) 我自己的 D 记账 ----------
FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0,
          "E": 0x76C290, "F": 0x778A20, "T16": 0x5D7590}
ROWS = [0x77884F, 0x77890C, 0x778956, 0x779C3D, 0x779EBD,
        0x5CEFC9, 0x5CF10E, 0x5CF162, 0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7,
        0x5D76A9, 0x76C555, 0x778BCF, 0x778DD1, 0x778E24]

def find_lea(row):
    k = IDX.get(row)
    if k is None or k == 0: return None, None
    a, s, b, m, o = insns[k-1]
    if m != "lea": return None, None
    mm = re.match(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$", o)
    if not mm: return None, None
    d = mm.group(1)
    return a, int(d, 16) if d.startswith("0x") else int(d)

print("\n### (b) 17 行的 witness lea（本线亲读字节） ###")
LEA = {}
for r in ROWS:
    la, ld = find_lea(r)
    LEA[r] = (la, ld)
    b = insns[IDX[r]][2]
    print("  row %06X  call=%s ; lea@%s bytes=%s disp=%s" % (
        r, b, hex(la) if la else "None",
        insns[IDX[la]][2] if la else "-", hex(ld) if ld is not None else "-"))

RESOLVED_INDIRECT = {0x5CEF6B: 4, 0x5CEF78: 4}   # 帧 D 两处可落实虚拟 call（本线自验见下）
print("\n  帧 D 两处间接 call 的本线自验：")
print("    rb(0x5CEF6B,3)=%s rb(0x5CEF78,3)=%s (ff5008=call[eax+8], ff521c=call[edx+0x1C])" % (
    rb(0x5CEF6B, 3).hex(), rb(0x5CEF78, 3).hex()))
print("    rb(0x473A9B,6)=%s (CCFileClass ctor stamp [esi]=0x7E16B0 期望 c706b0167e00)" % rb(0x473A9B, 6).hex())
s1 = rd(0x7E16B0 + 8); s2 = rd(0x7E16B0 + 0x1C)
print("    vtable[0x7E16B0+8]=%06X my_ret_imm=%s ; [+0x1C]=%06X my_ret_imm=%s" % (
    s1, my_ret_imm(s1)[0], s2, my_ret_imm(s2)[0]))

def my_dsim(head, resmap):
    """我自己的路径敏感 esp-D：状态 (D,p)。与 R-064 同语义，但代码全新、ret-imm 用我自己的闭包。"""
    targets = set()
    for r in ROWS:
        if r in body_of(head): targets.add(r)
        la = LEA[r][0]
        if la in body_of(head): targets.add(la)
    stamp_re = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
    for a, s, b, m, o in insns:
        if m == "mov" and a in body_of(head):
            mm = stamp_re.match(o)
            if mm and int(mm.group(2), 16) in (0x7EA5F4, 0x7E1B04, 0x7E1AFC, 0x7E1B0C, 0x7E1668):
                targets.add(a)
    coll = {}; causes = {}
    stack = [(head, 0, 0)]; seenst = set(); guard = 0
    while stack:
        guard += 1
        if guard > 4_000_000:
            causes["guard"] = "budget"; break
        a, D, p = stack.pop()
        if (a, D, p) in seenst: continue
        seenst.add((a, D, p))
        k = IDX.get(a)
        if k is None:
            if a in targets: coll.setdefault(a, set()).add(None)
            continue
        _, s, b, m, o = insns[k]
        if a in targets: coll.setdefault(a, set()).add(D)
        if m == "ret": continue
        nD, np = D, p; prune = False
        if m == "push": nD, np = D + 4, p + 4
        elif m == "pop": nD = D - 4
        elif m == "sub" and o.startswith("esp, "):
            x = int(o.split(", ", 1)[1], 0); nD, np = D + x, p + x
        elif m == "add" and o.startswith("esp, "):
            x = int(o.split(", ", 1)[1], 0); nD, np = D - x, 0
        elif m == "call":
            if a in resmap:
                r = resmap[a]; nD, np = D - r, max(0, p - r)
            else:
                t = None
                if o and not o.startswith("dword") and not o.startswith("eax") and not o.startswith("edx"):
                    try: t = int(o, 16)
                    except (ValueError, TypeError): t = None
                if t is not None and t in e8heads:
                    r, allr = my_ret_imm(t)
                    if r is None:
                        if p != 0:
                            causes.setdefault(a, set()).add("callee-ambiguous %s" % allr); prune = True
                        # p==0 => 两种约定效应 0
                else:
                    if p != 0:
                        causes.setdefault(a, set()).add("indirect/external-unresolved p=%d" % p); prune = True
        elif m == "lea" and o.startswith("esp, "):
            causes.setdefault(a, set()).add("esp-rewrite-lea"); prune = True
        elif m == "mov" and o.startswith("esp, "):
            causes.setdefault(a, set()).add("esp-rewrite-mov"); prune = True
        elif m in ("leave", "pushad", "popad"):
            causes.setdefault(a, set()).add("esp-shape"); prune = True
        if prune: continue
        for x in succ_of(a, head):
            stack.append((x, nD, np))
    return coll, causes, targets

stamp_re = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
NAMES = {0x7EA5F4: "INIClass", 0x7E1B04: "GenericList", 0x7E1AFC: "List<INISection*>",
         0x7E1B0C: "GenericNode", 0x7E1668: "CDFileClass"}

print("\n### (b2) 逐帧：本线 D 记账 → P/W（STRICT：无 resmap；另跑 帧D 含两落实）###")
tbl = []
for fr, h in FRAMES.items():
    res = RESOLVED_INDIRECT if fr == "D" else {}
    coll, causes, targets = my_dsim(h, res)
    rows_here = [r for r in ROWS if r in targets]
    # 帧内 stamps
    st = []
    for a, s, b, m, o in insns:
        if m == "mov" and a in targets:
            mm = stamp_re.match(o)
            if mm:
                imm = int(mm.group(2), 16)
                if imm in NAMES:
                    d = mm.group(1); d = int(d, 16) if d.startswith("0x") else int(d)
                    D = coll.get(a)
                    st.append((a, d, imm, D))
    for r in rows_here:
        Dr = coll.get(r); la, ld = LEA[r]; Dl = coll.get(la)
        W = (ld - next(iter(Dl))) if (Dl and len(Dl) == 1 and None not in Dl) else None
        hits = []
        mis = []
        for a, d, imm, D in st:
            if D and len(D) == 1 and None not in D:
                P = d - next(iter(D))
                if P == W: hits.append((a, imm, P))
                elif imm == 0x7E1B04: mis.append((a, imm, P, P - W if W is not None else None))
        tbl.append((fr, r, W, hits, mis))
        print("  %s row %06X D=%s | lea D=%s disp=%s W=%s | W命中=%s | GL错位=%s" % (
            fr, r,
            sorted(hex(x) for x in Dr) if Dr else "剪枝",
            sorted(hex(x) for x in Dl) if Dl else "剪枝", hex(ld) if ld is not None else "-",
            hex(W) if W is not None else "-",
            [(hex(a), NAMES[i], hex(p)) for a, i, p in hits],
            [(hex(a), hex(pp), hex(mm) if mm is not None else "-") for a, i, pp, mm in mis]))
    if causes:
        print("     剪枝因 %s: %s" % (fr, {("%06X" % k if isinstance(k, int) else k): sorted(v) for k, v in causes.items()}))

print("\n  汇总：17 行中本线 W 命中 INIClass stamp 的行数 =",
      sum(1 for fr, r, W, h, m in tbl if W is not None and any(i == 0x7EA5F4 for a, i, p in h)))
print("  汇总：W 命中 GenericList stamp 的行数 =",
      sum(1 for fr, r, W, h, m in tbl if W is not None and any(i == 0x7E1B04 for a, i, p in h)))
print("  汇总：GL-stamp 与 W 的错位值集合 =",
      sorted(set(mm for fr, r, W, h, m in tbl for a, i, pp, mm in m if mm is not None)))

# ---------- (c) 「同字面 disp」 vs 「同物理槽」 ----------
print("\n### (c) 判据可互换性检验 ###")
lit_same = 0; phys_same = 0; rows_checked = 0
for fr, h in FRAMES.items():
    res = RESOLVED_INDIRECT if fr == "D" else {}
    coll, causes, targets = my_dsim(h, res)
    gl = []
    for a, s, b, m, o in insns:
        if m != "mov" or a not in targets:
            continue
        mm = stamp_re.match(o)
        if not mm or int(mm.group(2), 16) != 0x7E1B04:
            continue
        ds = mm.group(1)
        d = int(ds, 16) if ds.startswith("0x") else int(ds)
        gl.append((a, d, coll.get(a)))
    for r in ROWS:
        if r not in targets: continue
        la, ld = LEA[r]; Dl = coll.get(la)
        if not (Dl and len(Dl) == 1): continue
        W = ld - next(iter(Dl)); rows_checked += 1
        ls = [x for x in gl if x[1] == ld]                      # 同字面 disp 的 GL store
        ps = [x for x in gl if x[2] and len(x[2]) == 1 and (x[1] - next(iter(x[2]))) == W]
        if ls: lit_same += 1
        if ps: phys_same += 1
        print("  %s row %06X lea-disp=%s W=%s : 同字面disp的GL-store=%s 同物理槽的GL-store=%s" % (
            fr, r, hex(ld), hex(W), [hex(x[0]) for x in ls], [hex(x[0]) for x in ps]))
print("  17 行中：存在『同字面 disp 的 GenericList store』的行数 = %d / %d" % (lit_same, rows_checked))
print("  17 行中：存在『同物理槽的 GenericList store』的行数 = %d / %d" % (phys_same, rows_checked))

# ---------- ret-imm 关键 callee 本线亲查 ----------
print("\n### (d) 关键 callee 的 ret-imm（本线闭包自算） ###")
for t in (0x528C00, 0x525A10, 0x5256F0, 0x527F20, 0x526D90, 0x5295F0, 0x40E340,
          0x40E320, 0x7B6290, 0x7B4620, 0x7B66C0, 0x47A9D0, 0x431F10, 0x65D150,
          0x47AF10, 0x7B5440, 0x4325C0, 0x526810, 0x7B4630, 0x7B5B30, 0x52B4F0,
          0x473FC0, 0x473D10):
    v, allr = my_ret_imm(t)
    print("  %06X ret唯一=%s 全部ret=%s 闭包=%d" % (t, v, allr, len(body_of(t))))
