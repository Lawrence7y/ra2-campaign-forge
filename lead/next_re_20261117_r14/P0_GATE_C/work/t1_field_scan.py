# -*- coding: utf-8 -*-
"""P0-GATE-C Task1: Four-flag field write/read point scanner.
Covers three access forms: (1) absolute [disp], (2) [reg+disp], (3) [base+idx*scale+disp].
Correct read/write detection via capstone op.access (CS_AC_READ=1, CS_AC_WRITE=2).
No dependence on function_atlas.tsv for the sweep (single linear .text sweep with skipdata=True).
"""
import hashlib, struct, pefile, bisect, sys
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WANT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

data = open(EXE, "rb").read()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha == WANT_SHA, "SHA mismatch: "+sha
pe = pefile.PE(EXE, fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm, va=BASE+s.VirtualAddress, vsize=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
            return s
    return None
def off(va):
    s = sec_of(va); return s["raw"] + (va - s["va"])
def rd(va,n):
    s = sec_of(va)
    if s is None: return b""
    o = s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va): return struct.unpack("<I", rd(va,4))[0]
def u16(va): return struct.unpack("<H", rd(va,2))[0]

TEXT = [s for s in secs if s["name"]==".text"][0]
T0, T1 = TEXT["va"], TEXT["va"]+TEXT["rawsize"]

# independent function-boundary detector (pad-start U E8 targets), NOT from atlas
pad_starts = set([T0])
for va in range(T0, T1-4):
    b = data[off(va)]
    n = 1 if b==0xC3 else (3 if b==0xC2 else 0)
    if not n: continue
    p, pad = va+n, 0
    while p < T1 and data[off(p)]==0x90 and pad < 16:
        pad += 1; p += 1
    if pad >= 2: pad_starts.add(p)
e8 = set()
for va in range(T0, T1-5):
    if data[off(va)]==0xE8:
        rel = int.from_bytes(data[off(va+1):off(va+5)],"little",signed=True)
        t = (va+5+rel)&0xFFFFFFFF
        if T0 <= t < T1: e8.add(t)
entries = sorted(pad_starts|e8)
def fn(a):
    i = bisect.bisect_right(entries,a)-1
    return entries[i] if i>=0 else T0

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True

TARGETS = {0x16BF:"byte", 0x16BE:"byte", 0x16B7:"byte", 0xE58:"dword"}
GLOBAL = 0xA8E9A0

# Single linear sweep, record every instruction with a memory operand that matches.
hits = {k:[] for k in TARGETS}
glob_hits = []
insn_list = []  # (addr, size, mnemonic, op_str, operands-snapshot)
va = T0
while va < T1:
    got = list(md.disasm(data[off(va):off(va)+16], va, count=1))
    if not got:
        va += 1; continue
    i = got[0]
    ops = []
    try:
        raw_ops = i.operands
    except Exception:
        raw_ops = []
    for o in raw_ops:
        if o.type == X86_OP_MEM:
            ops.append(dict(kind="mem", access=o.access, size=o.size,
                            base=o.mem.base, index=o.mem.index, scale=o.mem.scale,
                            disp=o.mem.disp & 0xFFFFFFFF))
        elif o.type == X86_OP_REG:
            ops.append(dict(kind="reg", access=o.access, size=o.size, reg=o.reg))
        elif o.type == X86_OP_IMM:
            ops.append(dict(kind="imm", access=o.access, size=o.size, imm=o.imm & 0xFFFFFFFF))
        else:
            ops.append(dict(kind="other", access=o.access, size=o.size))
    insn_list.append((i.address, i.size, i.mnemonic, i.op_str, ops))
    for k,o in enumerate(ops):
        if o["kind"]=="mem" and o["disp"] in TARGETS:
            is_wr = bool(o["access"] & CS_AC_WRITE)
            form = ("absolute" if o["base"]==0 and o["index"]==0
                    else "reg+off" if o["index"]==0
                    else "base+idx*scale+off")
            hits[o["disp"]].append(dict(addr=i.address, mnemonic=i.mnemonic, opstr=i.op_str,
                     rw="WRITE" if is_wr else "read", access=o["access"], opsize=o["size"],
                     opidx=k, form=form, base=o["base"], index=o["index"], scale=o["scale"], fn=fn(i.address)))
        if o["kind"]=="mem" and o["base"]==0 and o["index"]==0 and (o["disp"]&0xFFFFFFFF)==GLOBAL:
            is_wr = bool(o["access"] & CS_AC_WRITE)
            glob_hits.append(dict(addr=i.address, mnemonic=i.mnemonic, opstr=i.op_str,
                     rw="WRITE" if is_wr else "read", access=o["access"], opsize=o["size"],
                     opidx=k, fn=fn(i.address)))
    va += i.size

# reg name helper
def rname(r):
    if r==0: return "-"
    return_md = md
    try: return i.reg_name(r) if False else cs_reg_name(md.csh, r) or ("r%d"%r)
    except Exception: return "r%d"%r

print("SHA256", sha)
print("TEXT range 0x%08X..0x%08X  (%d bytes decoded, %d instructions, %d independent fn-starts)" % (T0,T1,T1-T0,len(insn_list),len(entries)))
print()
for disp in [0x16BF,0x16BE,0x16B7,0xE58]:
    rows = hits[disp]
    wr = [r for r in rows if r["rw"]=="WRITE"]
    rd_ = [r for r in rows if r["rw"]=="read"]
    forms = {}
    for r in rows: forms[r["form"]] = forms.get(r["form"],0)+1
    wforms = {}
    for r in wr: wforms[r["form"]] = wforms.get(r["form"],0)+1
    print("=== disp 0x%X (%s) : total=%d reads=%d writes=%d ===" % (disp,TARGETS[disp],len(rows),len(rd_),len(wr)))
    print("  ALL forms: %s" % forms)
    print("  WRITE forms: %s" % wforms)
    print("  absolute-only write count: %d  => missed by absolute-only scan: %d" % (wforms.get("absolute",0), len(wr)-wforms.get("absolute",0)))
    print("  -- WRITE points --")
    for r in wr:
        print("    %08X  %-7s %-34s sz=%d form=%-8s base=%s idx=%s fn=%08X" %
              (r["addr"],r["mnemonic"],r["opstr"],r["opsize"],r["form"],rname(r["base"]),rname(r["index"]),r["fn"]))
    print("  -- READ points --")
    for r in rd_:
        print("    %08X  %-7s %-34s sz=%d form=%-8s base=%s idx=%s fn=%08X" %
              (r["addr"],r["mnemonic"],r["opstr"],r["opsize"],r["form"],rname(r["base"]),rname(r["index"]),r["fn"]))
    print()

# global
gw = [r for r in glob_hits if r["rw"]=="WRITE"]
gr = [r for r in glob_hits if r["rw"]=="read"]
print("=== absolute global [0x%08X] : total=%d writes=%d reads=%d ===" % (GLOBAL,len(glob_hits),len(gw),len(gr)))
print("  -- WRITE points --")
for r in gw:
    print("    %08X  %-7s %-34s sz=%d opidx=%d fn=%08X" % (r["addr"],r["mnemonic"],r["opstr"],r["opsize"],r["opidx"],r["fn"]))
print("  -- READ count=%d (first 12) --" % len(gr))
for r in gr[:12]:
    print("    %08X  %-7s %-34s sz=%d fn=%08X" % (r["addr"],r["mnemonic"],r["opstr"],r["opsize"],r["fn"]))
