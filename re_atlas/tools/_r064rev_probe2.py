# -*- coding: utf-8 -*-
"""_r064rev_probe2.py — 复核点 2 前半：帧结构普查（全新实现）
- 自带 PE/.text 装载与全段线性解码（对齐起点推进；与门禁同 decode 域但独立代码）
- 全镜像 E8 目标集合（aligned heads）
- gate 同款 frame_lo（prev-ret 规则）对 17 行亲算
- 六帧 A/B/C/D/E/F：序言/段图/窗内全部 c7-esp-stamp（0x7EA5F4 与 0x7E1B04 与 0x7E1AFC）逐址列齐
- witness lea 逐址列齐；GenericNode 头件候选字节复核（CHD 基类数组偏移修正）
"""
import struct, hashlib, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", raw, e_lfanew + 20)[0]
opt = e_lfanew + 24
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
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b)==4 else None
def cstr(va, mx=80):
    out=bytearray()
    for i in range(mx):
        c=rb(va+i,1)
        if not c or c==b"\0": break
        out+=c
    return out.decode("latin1")

# ---- .text linear decode（对齐推进）----
tname, tva, tvsz, trp, trsz = next(s for s in secs if s[0]==".text")
TLO, THI = tva, tva + trsz  # raw-mapped end
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
# 与门禁同域：逐条解码；解码失败 ⇒ cur+=1（该字节不产生指令项）。
# 单块 disasm 会在首个失败处整体停止，故必须逐条推进。
insns = []  # (addr, size, bytes-hex, mn, op)
cur = TLO
end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        break
    if got is None:
        cur += 1
        continue
    insns.append(got)
    cur += got[1]
ADDR = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
print("decoded insns: %d  range %06X..%06X" % (len(insns), insns[0][0], insns[-1][0]))

# ---- E8 targets (aligned heads) ----
e8 = {}
for a, s, b, m, o in insns:
    if m == "call" and b.startswith("e8") and len(b) == 10:
        tgt = int(o, 16) if o.startswith("0x") else None
        if tgt is not None:
            e8.setdefault(tgt, []).append(a)
print("E8 distinct targets:", len(e8))

# ---- 17 行与 frame_lo（gate 同规则：向后找首条 ret，其后继为帧下界）----
ROWS = [0x77884F,0x77890C,0x778956,0x779C3D,0x779EBD,
        0x5CEFC9,0x5CF10E,0x5CF162,0x5CF284,0x5CF2E0,0x5CF42C,0x5CF4C7,
        0x5D76A9,0x76C555,0x778BCF,0x778DD1,0x778E24]
def frame_lo(call_va):
    j = ADDR[call_va] - 1
    while j >= 0 and insns[j][3] != "ret":
        j -= 1
    return insns[j+1][0]
print("\n== 17 行：call 现场字节 + frame_lo + E8 头判定 ==")
for r in ROWS:
    k = ADDR.get(r)
    if k is None:
        print("  %06X  未对齐解码!" % r); continue
    a,s,b,m,o = insns[k]
    fl = frame_lo(r)
    head = fl if fl in e8 else None
    print("  %06X  %s %s %s %-24s frame_lo=%06X E8头=%s" % (r, b, m, o, "(witness行)", fl, "YES" if head else "NO:"+hex(fl)))

# ---- 帧定义（R-064 声称值，逐一亲验为 E8 头）----
FRAMES = {"A":0x778710, "B":0x779B50, "C":0x779DD0, "D":0x5CEEF0, "E":0x76C290, "F":0x778A20, "T16":0x5D7590}
print("\n== 帧头 E8 自验 ==")
for k,h in FRAMES.items():
    print("  %s head=%06X E8-callers=%d 首3: %s" % (k, h, len(e8.get(h,[])), [hex(x) for x in e8.get(h,[])[:3]]))

# ---- 各帧窗内 stamp 普查：c7 44 24 disp, imm（mov [esp+disp],imm32）----
def frame_window(h):
    """帧窗：head 起，至下一条『其他 E8 头的序言前 ret』难以静态定；用退而求其次：
    窗 = head..head 之后第一个属于其他 E8 头且前方有 ret 的地址。简化：直接给 head→下一条 ret 序列收敛后的下一头。
    实操：从 h 向后解码，遇到 ret 且其后地址是 E8 头 ⇒ 帧尾在此。"""
    j = ADDR[h]
    end = None
    while j < len(insns):
        a,s,b,m,o = insns[j]
        if m == "ret":
            nxt = insns[j+1][0] if j+1 < len(insns) else None
            if nxt in e8 and nxt != h:
                end = a; break
        if m == "jmp":
            pass
        j += 1
        if a - h > 0x1200:
            break
    return end

print("\n== 各帧 stamp 全列（[esp+d],imm，imm∈{7EA5F4,7E1B04,7E1AFC,7E1B0C,7E1668}）==")
IMMS = {0x7EA5F4:"INIClass", 0x7E1B04:"GenericList", 0x7E1AFC:"List<INISection*>", 0x7E1B0C:"GenericNode", 0x7E1668:"CDFileClass"}
pat = re.compile(r"^mov dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$")
for k, h in FRAMES.items():
    end = frame_window(h)
    print("\n-- 帧 %s head=%06X 尾 ret@%s --" % (k, h, hex(end) if end else "未定"))
    j = ADDR[h]
    lim = (ADDR[end]+1) if end else len(insns)
    stamps, leas, calls528 = [], [], []
    while j < lim:
        a,s,b,m,o = insns[j]
        if m == "mov":
            mm = pat.match(o)
            if mm:
                disp = int(mm.group(1),16) if mm.group(1).startswith("0x") else int(mm.group(1))
                imm = int(mm.group(2),16)
                if imm in IMMS:
                    stamps.append((a,disp,imm,"%s %s" % (IMMS[imm], hex(imm))))
        if m == "lea" and o.startswith("ecx, dword ptr [esp"):
            mm = re.match(r"^ecx, dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\]$", o)
            if mm:
                disp = int(mm.group(1),16) if mm.group(1).startswith("0x") else int(mm.group(1))
                leas.append((a,disp))
        if m == "call" and o.strip() == "0x528c00":
            calls528.append(a)
        j += 1
    print("  stamp:")
    for a,d,imm,tag in stamps:
        print("    %06X  disp=%s  %s" % (a, hex(d), tag))
    print("  lea ecx,[esp+d] 总数=%d；紧邻 call 0x528C00 的 witness lea:" % len(leas))
    cset = set(calls528)
    for a,d in leas:
        nxt = insns[ADDR[a]+1][0]
        if nxt in cset:
            print("    lea %06X disp=%s -> call %06X" % (a, hex(d), nxt))
    print("  call 0x528C00 站点:", [hex(x) for x in calls528])

# ---- GenericNode 头件候选 + CHD 基类数组偏移修正 ----
print("\n== CHD 基类数组偏移修正复读 ==")
for label, v in [("GenericList",0x7E1B04),("INIClass",0x7EA5F4),("GenericNode",0x7E1B0C),("List<INISection*>",0x7E1AFC),("CDFileClass",0x7E1668)]:
    col = rd(v-4); chd = rd(col+0x10); numB = rd(chd+8)
    bases=[]
    for i in range(numB or 0):
        b = rd(chd+0xC+i*4)
        bases.append((hex(b), cstr(b+8) if b else "-"))
    print("  %s CHD=%06X numBases=%s bases=%s" % (label, chd, numB, bases))
print("\n== 0x5256F0 体 0x525740..0x5257A0 反汇编（GenericNode stamp 位置重定）==")
md2 = Cs(CS_ARCH_X86, CS_MODE_32)
for ins in md2.disasm(rb(0x525740,0x60), 0x525740):
    tag=""
    if "0x7e1b0c" in ins.op_str or "0x7e1afc" in ins.op_str: tag="  <== stamp"
    print("  %06X  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, tag))
