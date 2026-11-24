# -*- coding: utf-8 -*-
"""xr1_probe.py — R-064 独立复核探针（XVERIFY_R064RECHK_GLM_20261101，GLM start-plan 族）。

全新实现（不复用 R-064 probe1..4、_r064rev_probe1..7、brev_probe_a..f 的代码）：
  X1 镜像身份 + 段表
  X2 RTTI 双链 walk（0x7E1B04 / 0x7EA5F4 / 0x7E1AFC / 0x7E1B0C / 0x7E1668）+ 组合非继承判定
  X3 盘上字节钉（R-062 三窗、R-064 补 stamp、0x5256F0 复位体三 stamp、0x525A10 ctor）
  X4 全 .text 线性解码 + E8 头集合 + 闭包/ret-imm 引擎（我自己的）
  X5 路径敏感 esp-D 归一化（17 行 W/P、命中、GL 错位）——STRICT
  X6 帧 D vtable 落实自验 + E2 承重假设网格（c1×u）+ E2b 其余六帧恒等
  X7 判据可互换性 17 行全验（同字面 disp / 同物理槽 / W+0xC 子对象槽）
  X8 帧 F 解码边界定量：线性流 vs 锚定流（0x778B20 字节钉锚），esp 效应差 δ 与补丁重模拟
  X9 关键 callee ret-imm 表

只读 gamemd.exe；不启动任何进程；不写本写域以外任何文件。
"""
import struct, hashlib, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
SHA = hashlib.sha256(raw).hexdigest()
print("[X1] gamemd.exe sha256 =", SHA)
if SHA != "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476":
    print("FATAL: hash mismatch, stop."); sys.exit(1)

# ---- 段表（我自己的 PE 解析） ----
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
ib = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
secs = []
for i in range(nsec):
    nm = raw[tab + i*40: tab + i*40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    secs.append((nm, ib + va, vsz, rp, rsz))
    print("  sec %-8s va=%08X vsz=%06X raw=%06X/%06X" % (nm, ib+va, vsz, rp, rsz))

def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            return raw[fo:fo+n] if fo + n <= rp + rsz else raw[fo:rp+rsz]
    return b""
def rd(va):
    b = rb(va, 4)
    return int.from_bytes(b, "little") if len(b) == 4 else None
def cstr(va, mx=96):
    o = bytearray()
    for i in range(mx):
        c = rb(va + i, 1)
        if not c or c == b"\0":
            break
        o += c
    return o.decode("latin1")

# ---- X2 RTTI walk ----
print("\n[X2] RTTI 双链 walk（我自己的二跳解析）")
def rtti(V):
    col = rd(V - 4)
    if col is None:
        return None
    sig = rd(col)
    td = rd(col + 0xC)
    chd = rd(col + 0x10)
    name = cstr(td + 8) if td else "?"
    vfp = rd(td) if td else None
    nb = rd(chd + 8) if chd else None
    bases = []
    if chd and nb:
        arr = rd(chd + 0xC)
        for i in range(nb):
            bcd = rd(arr + i*4) if arr else None
            if bcd and rd(bcd):
                ptd = rd(bcd)
                bases.append((ptd, cstr(ptd + 8), rd(bcd + 4), struct.unpack("<i", rb(bcd + 8, 4))[0]))
    return dict(V=V, COL=col, sig=sig, TD=td, name=name, vfp=vfp, CHD=chd, nb=nb, bases=bases)

FAM = {}
for label, V in [("GenericList", 0x7E1B04), ("INIClass", 0x7EA5F4),
                 ("List<INISection*>", 0x7E1AFC), ("GenericNode", 0x7E1B0C),
                 ("CDFileClass", 0x7E1668), ("CCINIClass-ctrl", None), ("CCFileClass", 0x7E16B0)]:
    if V is None:
        continue
    r = rtti(V)
    FAM[label] = r
    print("  %-18s V=%06X COL=%06X sig=%s TD=%06X vfp=%06X CHD=%06X numBases=%s name=%r" % (
        label, V, r["COL"], r["sig"], r["TD"], r["vfp"], r["CHD"], r["nb"], r["name"]))
    for i, (tdp, tdn, ncb, mdisp) in enumerate(r["bases"]):
        print("      base[%d] pTD=%06X %r numContainedBases=%d mdisp=%d" % (i, tdp, tdn, ncb, mdisp))

# 控制位复现（R-062 §2 / R-064 §1）：CCINIClass TD 名与 vfp
print("  [0x8174C8]=%08X (期望 vfp 0x7F9594) ; 0x8174D0 名=%r" % (rd(0x8174C8) or 0, cstr(0x8174D0)))
gl, ini = FAM["GenericList"], FAM["INIClass"]
gl_td, ini_td = 0x817508, 0x8174B0
lst = FAM["List<INISection*>"]
print("  互不为基类：GenericList 基含 INIClassTD? %s ; INIClass 基含 GenericListTD? %s" % (
    any(tdp == ini_td for tdp, _, _, _ in gl["bases"]),
    any(tdp == gl_td for tdp, _, _, _ in ini["bases"])))
print("  List<INISection*> 基含 GenericListTD(0x817508)? %s (numBases=%s, CHD=%06X)" % (
    any(tdp == gl_td for tdp, _, _, _ in lst["bases"]), lst["nb"], lst["CHD"]))

# ---- X3 字节钉 ----
print("\n[X3] 盘上字节钉")
PINS = [
    ("R062窗1", 0x7787C0, 8, "c7442438041b7e00"),
    ("R062窗2", 0x779BB3, 8, "c7442424041b7e00"),
    ("R062窗3", 0x779E33, 8, "c7442424041b7e00"),
    ("补A", 0x7787F7, 8, "c7442430f4a57e00"),
    ("补B", 0x779BEA, 8, "c744241cf4a57e00"),
    ("补C", 0x779E6A, 8, "c744241cf4a57e00"),
    ("R063b-D", 0x5CEF41, 8, "c7442428f4a57e00"),
    ("R063b-E", 0x76C4A4, 8, "c7442430f4a57e00"),
    ("R063b-F", 0x778B20, 8, "c744242cf4a57e00"),
    ("T16", 0x5D761D, 8, "c7442478f4a57e00"),
    ("复位体[esi]", 0x5256F8, 6, "c706f4a57e00"),
    ("复位体[esi+C]", 0x52571E, 7, "c7460c041b7e00"),
    ("复位体[+1C]", 0x525760, 6, "c7000c1b7e00"),
    ("复位体[+10]", 0x52578D, 6, "c7000c1b7e00"),
]
ok = 0
for lab, va, n, exp in PINS:
    got = rb(va, n).hex()
    ok += got == exp
    print("  %-12s %06X: %-16s exp=%-16s %s" % (lab, va, got, exp, "MATCH" if got == exp else "MISMATCH"))
print("  => %d/%d MATCH" % (ok, len(PINS)))

# ---- X4 线性解码 + 引擎 ----
print("\n[X4] 全 .text 线性解码…")
tn, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp + trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []
cur = TLO
end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur - TLO:min(cur - TLO + 15, end - TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        break
    if got is None:
        cur += 1
        continue
    insns.append(got)
    cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
print("  insns=%d 范围 %06X..%06X" % (len(insns), insns[0][0], insns[-1][0]))
heads = set()
for a, s, b, m, o in insns:
    if m == "call" and b[:2] == "e8" and len(b) == 10:
        try:
            t = int(o, 16)
        except ValueError:
            continue
        if TLO <= t < THI:
            heads.add(t)
print("  E8 头集合 = %d" % len(heads))

def nxt(a):
    k = IDX.get(a)
    return None if k is None else a + insns[k][1]

def body(head):
    seen = {head}
    work = [head]
    while work:
        a = work.pop()
        k = IDX.get(a)
        if k is None:
            continue
        _, sz, by, m, o = insns[k]
        if m == "ret":
            continue
        dests = []
        if m == "jmp" or m[0] == "j":
            try:
                t = int(o, 16)
            except ValueError:
                t = None
            if t is not None and TLO <= t < THI and (t not in heads or t == head):
                dests.append(t)
            if m == "jmp":
                pass
            else:
                f = nxt(a)
                if f is not None and f < THI and (f not in heads or f == head):
                    dests.append(f)
        else:
            f = nxt(a)
            if f is not None and f < THI and (f not in heads or f == head):
                dests.append(f)
        for x in dests:
            if x not in seen:
                seen.add(x)
                work.append(x)
    return seen

def retimm(head):
    imms = set()
    for a in body(head):
        k = IDX.get(a)
        if k is None:
            continue
        _, sz, by, m, o = insns[k]
        if m == "ret":
            imms.add(0 if not o.strip() else int(o, 16))
    return (next(iter(imms)) if len(imms) == 1 else None), sorted(imms)

def call_target(o):
    if not o:
        return None
    if o.startswith("dword") or o.startswith("word") or o.startswith("byte") or o.startswith("["):
        return None
    try:
        t = int(o, 16)
    except ValueError:
        return None
    return t if TLO <= t < THI else None

def effect(a, D, p, resmap):
    """返回 (nD, np, prune_reason or None)。我自己的 esp 结算。"""
    _, sz, by, m, o = insns[IDX[a]]
    if m == "push":
        return D + 4, p + 4, None
    if m == "pop":
        return D - 4, p, None
    if m in ("sub", "add") and o.startswith("esp, "):
        try:
            x = int(o.split(", ", 1)[1], 0)
        except ValueError:
            return D, p, "esp-imm-bad"
        return (D + x, p + x, None) if m == "sub" else (D - x, 0, None)
    if m == "call":
        if a in resmap:
            r = resmap[a]
            return D - r, max(0, p - r), None
        t = call_target(o)
        if t is not None and t in heads:
            r, allr = retimm(t)
            if r is None:
                return D, p, ("callee-ambig-%06X%s" % (t, allr)) if p != 0 else None
            return D - r, max(0, p - r), None
        return D, p, ("indir-unres-p%d" % p) if p != 0 else None
    if (m in ("mov", "lea")) and o.split(",")[0].strip() == "esp":
        return D, p, "esp-rewrite"
    if m in ("leave", "pushad", "popad", "enter", "xchg", "popfd", "iret", "hlt", "int"):
        return D, p, "esp-shape"
    return D, p, None

def dsim(head, resmap, targets, budget=3_000_000):
    coll, causes = {}, {}
    seen = set()
    work = [(head, 0, 0)]
    g = 0
    while work:
        g += 1
        if g > budget:
            causes["BUDGET"] = {"budget"}
            break
        a, D, p = work.pop()
        if (a, D, p) in seen:
            continue
        seen.add((a, D, p))
        if a in targets:
            coll.setdefault(a, set()).add(D)
        k = IDX.get(a)
        if k is None:
            continue
        _, sz, by, m, o = insns[k]
        if m == "ret":
            continue
        nD, np_, why = effect(a, D, p, resmap)
        if why:
            causes.setdefault(a, set()).add(why)
            continue
        k2 = IDX.get(a)
        _, sz, by, m2, o2 = insns[k2]
        dests = []
        if m2 == "jmp" or m2[0] == "j":
            try:
                t = int(o2, 16)
            except ValueError:
                t = None
            if t is not None and TLO <= t < THI and (t not in heads or t == head):
                dests.append(t)
            if m2 != "jmp":
                f = nxt(a)
                if f is not None and f < THI and (f not in heads or f == head):
                    dests.append(f)
        else:
            f = nxt(a)
            if f is not None and f < THI and (f not in heads or f == head):
                dests.append(f)
        for x in dests:
            work.append((x, nD, np_))
    return coll, causes

# ---- X5 17 行 STRICT ----
FRAMES = {"A": 0x778710, "B": 0x779B50, "C": 0x779DD0, "D": 0x5CEEF0,
          "E": 0x76C290, "F": 0x778A20, "T16": 0x5D7590}
ROWS = [0x77884F, 0x77890C, 0x778956, 0x779C3D, 0x779EBD,
        0x5CEFC9, 0x5CF10E, 0x5CF162, 0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7,
        0x5D76A9, 0x76C555, 0x778BCF, 0x778DD1, 0x778E24]
NAMES = {0x7EA5F4: "INIClass", 0x7E1B04: "GenericList", 0x7E1AFC: "List<INISection*>",
         0x7E1B0C: "GenericNode", 0x7E1668: "CDFileClass", 0x7E16B0: "CCFileClass"}
store_re = re.compile(r"^dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
lea_re = re.compile(r"^ecx, (?:dword ptr )?\[esp \+ (0x[0-9a-f]+|\d+)\]$")

def lea_of(row):
    k = IDX.get(row)
    if not k:
        return None, None
    a, sz, by, m, o = insns[k - 1]
    if m != "lea":
        return None, None
    mm = lea_re.match(o)
    if not mm:
        return None, None
    d = mm.group(1)
    return a, int(d, 16) if d.startswith("0x") else int(d)

def frame_stamps(bd):
    st = []
    for a, sz, by, m, o in insns:
        if m == "mov" and a in bd:
            mm = store_re.match(o)
            if mm and int(mm.group(2), 16) in NAMES:
                d = mm.group(1)
                st.append((a, int(d, 16) if d.startswith("0x") else int(d), int(mm.group(2), 16)))
    return st

print("\n[X5] 17 行 STRICT D-归一化（我自己的引擎）")
RES_D = {0x5CEF6B: 4, 0x5CEF78: 4}
allrows = []
for fr, h in FRAMES.items():
    bd = body(h)
    rh = [r for r in ROWS if r in bd]
    st = frame_stamps(bd)
    leas = {r: lea_of(r) for r in rh}
    tg = set(x[0] for x in st) | set(rh) | set(v[0] for v in leas.values() if v[0])
    coll, causes = dsim(h, RES_D if fr == "D" else {}, tg)
    for r in rh:
        la, ld = leas[r]
        Dl = coll.get(la)
        W = ld - next(iter(Dl)) if (Dl and len(Dl) == 1) else None
        hits, offs = [], []
        for a, d, imm in st:
            Da = coll.get(a)
            if Da and len(Da) == 1:
                P = d - next(iter(Da))
                if P == W:
                    hits.append((a, imm, P))
                else:
                    offs.append((a, imm, P, None if W is None else P - W))
        allrows.append((fr, r, W, hits, offs))
        print("  %s row %06X D(row)=%s D(lea)=%s W=%s 命中=%s" % (
            fr, r,
            sorted(hex(x) for x in coll.get(r, [])) or "剪枝",
            sorted(hex(x) for x in Dl) if Dl else "剪枝",
            hex(W) if W is not None else "-",
            [(hex(a), NAMES[i], hex(pp)) for a, i, pp in hits]))
    if causes:
        print("    (%s 剪枝点: %s)" % (fr, sorted("%06X" % k for k in causes if isinstance(k, int))))
nW = sum(1 for x in allrows if x[2] is not None)
nI = sum(1 for x in allrows if x[2] is not None and any(i == 0x7EA5F4 for a, i, p in x[3]))
nG = sum(1 for x in allrows if x[2] is not None and any(i == 0x7E1B04 for a, i, p in x[3]))
nU = sum(1 for x in allrows if x[2] is not None and len(x[3]) == 1)
glset = sorted(set(o for x in allrows for a, i, pp, o in x[4] if i == 0x7E1B04 and o is not None))
print("  汇总: W可算=%d/17 W命中INIClass=%d W命中GenericList=%d 唯一命中=%d GL错位集=%s" % (nW, nI, nG, nU, glset))

# ctor 同格链（补强）：INI stamp 与 0x525A10 ctor this 同 disp 同 D 同格
print("\n  INI stamp 邻近 ctor 0x525A10 的 this 同格链（每帧）：")
for fr, h in FRAMES.items():
    bd = body(h)
    ini_stamps = [(a, d) for a, d, imm in frame_stamps(bd) if imm == 0x7EA5F4]
    for a, d in ini_stamps:
        k = IDX.get(a)
        found = None
        for j in range(max(0, k - 6), min(k + 8, len(insns))):
            aa, sz, by, m, o = insns[j]
            if m == "call" and o == "0x525a10":
                for jj in range(j - 1, max(0, j - 5), -1):
                    a2, s2, b2, m2, o2 = insns[jj]
                    if m2 == "lea" and lea_re.match(o2):
                        found = (a2, int(lea_re.match(o2).group(1), 16))
                        break
                break
        if found:
            la2, ld2 = found
            print("  %s stamp@%06X disp=%s → ctor 前 lea@%06X disp=%s → 同字面disp=%s" % (
                fr, a, hex(d), la2, hex(ld2), ld2 == d))
        else:
            print("  %s stamp@%06X disp=%s → 邻域±8 条内未见 lea+call 0x525A10 对" % (fr, a, hex(d)))

# ---- X6 vtable 落实 + E2 网格 + E2b ----
print("\n[X6] 帧 D vtable 落实自验")
print("  rb(0x5CEF6B,3)=%s rb(0x5CEF78,3)=%s (期望 ff5008 / ff521c)" % (rb(0x5CEF6B, 3).hex(), rb(0x5CEF78, 3).hex()))
print("  rb(0x473A9B,6)=%s (CCFileClass ctor stamp, 期望 c706b0167e00)" % rb(0x473A9B, 6).hex())
s1, s2 = rd(0x7E16B0 + 8), rd(0x7E16B0 + 0x1C)
r1, a1 = retimm(s1); r2, a2 = retimm(s2)
print("  vtable[0x7E16B0+8]=%06X ret唯一=%s 全ret=%s ; [+0x1C]=%06X ret唯一=%s 全ret=%s" % (s1, r1, a1, s2, r2, a2))
for x in (0x5CF038, 0x5CF350, 0x5CF556):
    k = IDX.get(x)
    print("  未落实 call 候选 %06X bytes=%s %s %s" % (x, insns[k][2], insns[k][3], insns[k][4]) if k else "  %06X 不在解码流" % x)

print("\n  E2 承重假设网格（帧 D，c1=两落实 call 假设 ret；u=三未落实 call 假设 ret/None=按剪枝规则）")
h = 0x5CEEF0
bd = body(h)
rhD = [r for r in ROWS if r in bd]
stD = frame_stamps(bd)
leasD = {r: lea_of(r) for r in rhD}
tgD = set(x[0] for x in stD) | set(rhD) | set(v[0] for v in leasD.values() if v[0])
UNRES = [0x5CF038, 0x5CF350, 0x5CF556]
grid = []
for c1 in (0, 4, 8, 0xC):
    for u in (None, 0, 4, 8):
        res = {0x5CEF6B: c1, 0x5CEF78: c1}
        if u is not None:
            for x in UNRES:
                res[x] = u
        coll, causes = dsim(h, res, tgD)
        closed = ini = gl = multi = 0
        for r in rhD:
            la, ld = leasD[r]
            Dl = coll.get(la)
            if not (Dl and len(Dl) == 1):
                continue
            W = ld - next(iter(Dl))
            closed += 1
            hits = [imm for a, d, imm in stD
                    if coll.get(a) and len(coll[a]) == 1 and d - next(iter(coll[a])) == W]
            ini += 0x7EA5F4 in hits
            gl += 0x7E1B04 in hits
            multi += len(hits) > 1
        grid.append((c1, u, closed, ini, gl, multi))
        print("    c1=%-4s u=%-5s 闭合=%d/7 W命中INIClass=%d W命中GenericList=%d 多命中=%d" % (
            hex(c1), str(u), closed, ini, gl, multi))
only_claim = all((ini == 7 and gl == 0) if (c1 == 4 and u in (None, 8)) else (ini == 0 and gl == 0)
                 for c1, u, closed, ini, gl, multi in grid)
print("  => 「仅 (c1=4,u∈{None,8}) 7/7 闭合∧INIClass=7；其余 14 组 INIClass=0 且 GL 恒 0」： %s" % only_claim)

print("\n  E2b 其余六帧 STRICT 恒等：")
nonD_closed = 0
for fr, hh in FRAMES.items():
    if fr == "D":
        continue
    bdx = body(hh)
    rhx = [r for r in ROWS if r in bdx]
    stx = frame_stamps(bdx)
    lx = {r: lea_of(r) for r in rhx}
    tgx = set(x[0] for x in stx) | set(rhx) | set(v[0] for v in lx.values() if v[0])
    coll, causes = dsim(hh, {}, tgx)
    okc = ini = gl = 0
    for r in rhx:
        la, ld = lx[r]
        Dl = coll.get(la)
        if not (Dl and len(Dl) == 1):
            continue
        okc += 1
        W = ld - next(iter(Dl))
        hits = [imm for a, d, imm in stx
                if coll.get(a) and len(coll[a]) == 1 and d - next(iter(coll[a])) == W]
        ini += 0x7EA5F4 in hits
        gl += 0x7E1B04 in hits
    nonD_closed += okc
    print("    %s 行=%d 闭合=%d INIClass=%d GenericList=%d" % (fr, len(rhx), okc, ini, gl))
print("  => 非 D 帧 STRICT 恒等闭合行数 = %d（R064REV 称「14 行」；10+7=17 才自洽）" % nonD_closed)

# ---- X7 判据可互换性 17 行 ----
print("\n[X7] 判据可互换性（17 行全验）")
lit = phys = sub = 0
for fr, hh in FRAMES.items():
    bdx = body(hh)
    rhx = [r for r in ROWS if r in bdx]
    stx = frame_stamps(bdx)
    glst = [(a, d, imm) for a, d, imm in stx if imm in (0x7E1B04, 0x7E1AFC)]
    lx = {r: lea_of(r) for r in rhx}
    tgx = set(x[0] for x in stx) | set(rhx) | set(v[0] for v in lx.values() if v[0])
    coll, _ = dsim(hh, RES_D if fr == "D" else {}, tgx)
    for r in rhx:
        la, ld = lx[r]
        Dl = coll.get(la)
        if not (Dl and len(Dl) == 1):
            continue
        W = ld - next(iter(Dl))
        ls = [x for x in glst if x[1] == ld]
        ps = [x for x in glst if coll.get(x[0]) and len(coll[x[0]]) == 1 and x[1] - next(iter(coll[x[0]])) == W]
        ss = [x for x in glst if coll.get(x[0]) and len(coll[x[0]]) == 1 and x[1] - next(iter(coll[x[0]])) == W + 0xC]
        lit += bool(ls); phys += bool(ps); sub += bool(ss)
        print("  %s %06X W=%s 同字面GL/List=%s 同物理槽=%s 落W+0xC=%s" % (
            fr, r, hex(W), [(hex(a), NAMES[i]) for a, d, i in ls],
            [(hex(a), NAMES[i]) for a, d, i in ps], [(hex(a), NAMES[i]) for a, d, i in ss]))
print("  => 同字面disp有GL/List store 的行=%d；同物理槽=%d；落 W+0xC 槽=%d（共 17）" % (lit, phys, sub))

# ---- X8 帧 F 解码边界 ----
print("\n[X8] 帧 F 解码边界定量（0x778B39..0x778B47）")
print("  原始字节：")
b0 = rb(0x778B10, 0x50)
for i in range(0, 0x50, 16):
    print("    %06X: %s" % (0x778B10 + i, b0[i:i+16].hex(" ")))
print("  我的线性解码流覆盖 0x778B20..0x778B60：")
for a, sz, by, m, o in insns:
    if 0x778B20 <= a < 0x778B60:
        print("    %06X %-20s %-5s %s" % (a, by, m, o))
print("  全镜像 jmp/jcc 直接跳入 [0x778B40..0x778B47) 的站点：")
ent = []
for a, sz, by, m, o in insns:
    if m in ("jmp",) or m[0] == "j":
        try:
            t = int(o, 16)
        except ValueError:
            continue
        if 0x778B40 <= t < 0x778B47:
            ent.append((a, m, t))
for a, m, t in ent:
    print("    %06X %s -> %06X" % (a, m, t))
if not ent:
    print("    （无）")
print("  锚定流（从字节钉 stamp 0x778B20 线性前向解码到 0x778BA8）：")
anchor = []
for ins in md.disasm(rb(0x778B20, 0x88), 0x778B20):
    anchor.append((ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str))
for a, sz, by, m, o in anchor:
    print("    %06X %-20s %-5s %s" % (a, by, m, o))

def espsum(seq):
    tot = 0
    for a, sz, by, m, o in seq:
        if m == "push":
            tot += 4
        elif m == "pop":
            tot -= 4
        elif m == "sub" and o.startswith("esp, "):
            tot += int(o.split(", ", 1)[1], 0)
        elif m == "add" and o.startswith("esp, "):
            tot -= int(o.split(", ", 1)[1], 0)
        elif m == "call":
            t = call_target(o)
            if t is not None and t in heads:
                r, _ = retimm(t)
                if r is not None:
                    tot -= r
    return tot

lin_win = [x for x in insns if 0x778B39 <= x[0] < 0x778B47]
anc_win = [x for x in anchor if 0x778B39 <= x[0] < 0x778B47]
print("  线性流 [0x778B39..0x778B47) 指令: %s" % [(hex(a), m) for a, s, b, m, o in lin_win])
print("  锚定流 [0x778B39..0x778B47) 指令: %s" % [(hex(a), m) for a, s, b, m, o in anc_win])
print("  线性流 esp 净效应=%+d ; 锚定流 esp 净效应=%+d ; δ=%d" % (
    espsum(lin_win), espsum(anc_win), espsum(anc_win) - espsum(lin_win)))

# 补丁重模拟：把帧 F 闭包内与锚定流冲突的指令段替换为锚定流，重跑 D-sim
def patched_sim(head, targets, resmap):
    """在 insns 覆盖层上打补丁：帧 F 区间 [0x778B39..0x778BA8) 用锚定流替换，保留其余全部指令。"""
    global insns, IDX
    save = (insns, IDX)
    try:
        anc = [(a, sz, by, m, o) for a, sz, by, m, o in anchor]
        lo = 0x778B39
        hi = anc[-1][0] + anc[-1][1]  # 锚定流最后一条的结束地址，避免留洞
        newi = [x for x in insns if not (lo <= x[0] < hi)]
        newi.extend(anc)
        newi.sort(key=lambda x: x[0])
        insns, IDX = newi, {a: i for i, (a, s, b, m, o) in enumerate(newi)}
        coll, causes = dsim(head, resmap, targets)
        return coll, causes
    finally:
        insns, IDX = save

bdF = body(0x778A20)
rhF = [r for r in ROWS if r in bdF]
stF = frame_stamps(bdF)
leasF = {r: lea_of(r) for r in rhF}
tgF = set(x[0] for x in stF) | set(rhF) | set(v[0] for v in leasF.values() if v[0])
collF, _ = dsim(0x778A20, {}, tgF)
collP, causesP = patched_sim(0x778A20, tgF, {})
def report(coll, tag):
    out = []
    for r in rhF:
        la, ld = leasF[r]
        Dl = coll.get(la)
        W = ld - next(iter(Dl)) if (Dl and len(Dl) == 1) else None
        hits = [(hex(a), NAMES[imm], hex(d - next(iter(coll[a])))) for a, d, imm in stF
                if coll.get(a) and len(coll[a]) == 1 and d - next(iter(coll[a])) == W] if W is not None else []
        out.append("  %s row %06X W=%s 命中=%s" % (tag, r, hex(W) if W is not None else "-", hits))
    for a, d, imm in stF:
        Da = coll.get(a)
        if Da and len(Da) == 1:
            out.append("  %s stamp %06X %s D=%s P=%s" % (tag, a, NAMES[imm], hex(next(iter(Da))), hex(d - next(iter(Da)))))
    return out
for line in report(collF, "线性"):
    print(line)
for line in report(collP, "锚定"):
    print(line)
print("  锚定重模拟剪枝点: %s" % sorted("%06X" % k for k in causesP if isinstance(k, int)))

# ---- X9 关键 callee ret-imm ----
print("\n[X9] 关键 callee ret-imm（我自己的闭包交集）")
for t in (0x528C00, 0x525A10, 0x5256F0, 0x527F20, 0x526D90, 0x5295F0, 0x40E340, 0x40E320,
          0x7B6290, 0x47A9D0, 0x4325C0, 0x7B5440, 0x526810, 0x7B4630, 0x7B5B30, 0x7B4690,
          0x7B46F0, 0x473FC0, 0x473D10, 0x473A80, 0x431F10, 0x431B80):
    v, allr = retimm(t)
    print("  %06X ret唯一=%s 全ret=%s 闭包=%d" % (t, v, allr, len(body(t))))
print("\n[X-END] 完成")
