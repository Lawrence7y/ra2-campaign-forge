#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186-EXEC (hy4) 独立复算：vtable 装点位移 == COL.mdisp 六个数字。

不复用 pe185：直接用 pefile 从 PE 头推导段边界。
全部数字由字节算出，不做任何预估。
"""
import os, json, struct, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUTDIR = os.path.join(ROOT, '_r186')
os.makedirs(OUTDIR, exist_ok=True)
RAW = open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    va = IB + s.VirtualAddress
    SECS[nm] = dict(va=va, lo=va, hi_file=va + s.SizeOfRawData,
                    hi_virt=va + s.Misc_VirtualSize,
                    rawptr=s.PointerToRawData, rawsize=s.SizeOfRawData)
TEXT = SECS['.text']
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
assert TEXT['lo'] == TEXT_LO and TEXT['hi_file'] == TEXT_HI, (TEXT, TEXT_LO, TEXT_HI)

def in_file_sec(va, name):
    s = SECS[name]
    return s['lo'] <= va < s['hi_file']

def r2o(va):
    for s in SECS.values():
        if s['lo'] <= va < s['hi_file']:
            return s['rawptr'] + (va - s['lo'])
    return None

def dw(va):
    o = r2o(va)
    return None if o is None or o + 4 > len(RAW) else struct.unpack_from('<I', RAW, o)[0]

def cstr(va, m=256):
    o = r2o(va)
    if o is None:
        return None
    e = RAW.find(b'\0', o, o + m)
    return None if e < 0 else RAW[o:e]

def class_name(ptd):
    """pTD+8 处 RTTI 名，去 .?A 前缀与 @@ 后缀。"""
    nm = cstr(ptd + 8, 256)
    if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
        return nm[3:-2].decode('latin1')
    return None

# ---------- 1. COL 全镜像枚举（严格口径：.?AV / .?AU）----------
COLS, COLS_loose = {}, {}
for secname in ('.rdata', '.data'):
    s = SECS[secname]
    nd = s['rawsize'] // 4
    vals = struct.unpack_from('<%dI' % nd, RAW, s['rawptr'])
    for i in range(nd - 4):
        d0, d1, d2, d3, d4 = vals[i:i + 5]
        if d0 not in (0, 1) or d2 != 0:
            continue
        if not in_file_sec(d3, '.data') or not in_file_sec(d4, '.rdata'):
            continue
        nm = cstr(d3 + 8, 256)
        if not nm or not (nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        rec = dict(mdisp=d1, ptd=d3, pchd=d4, name=nm.decode('latin1'))
        COLS_loose[s['lo'] + 4 * i] = rec
        if nm.startswith(b'.?AV') or nm.startswith(b'.?AU'):
            COLS[s['lo'] + 4 * i] = rec

# ---------- 2. vtable 全镜像枚举 ----------
VTS, VTS_loose = {}, {}
for secname in ('.rdata', '.data'):
    s = SECS[secname]
    nd = s['rawsize'] // 4
    vals = struct.unpack_from('<%dI' % nd, RAW, s['rawptr'])
    for i, v in enumerate(vals):
        if not (TEXT_LO <= v < TEXT_HI):
            continue
        base = s['lo'] + 4 * i
        c = dw(base - 4)
        if c in COLS:
            VTS[base] = COLS[c]
        if c in COLS_loose:
            VTS_loose[base] = COLS_loose[c]

N1, N2 = len(VTS), len(COLS)

# ---------- 3. 指令候选（disasm_lite 64KB 分块，逐字节滑动取 dword）----------
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
cand, cand_aligned = {}, {}
for st in range(0, TEXT['rawsize'], 65536):
    seg = RAW[TEXT['rawptr'] + st: TEXT['rawptr'] + min(st + 65536, TEXT['rawsize'])]
    for a, sz, mn, op in mdl.disasm_lite(seg, TEXT['va'] + st):
        if sz < 5:
            continue
        base_off = TEXT['rawptr'] + (a - TEXT['va'])
        hit = hit_al = None
        for j in range(sz - 3):
            w = struct.unpack_from('<I', RAW, base_off + j)[0]
            if w in VTS:
                if hit is None:
                    hit = w
                if (a + j) % 4 == 0 and hit_al is None:
                    hit_al = w
        if hit is not None:
            cand[a] = hit
        if hit_al is not None:
            cand_aligned[a] = hit_al

N3, N3_aligned = len(cand), len(cand_aligned)

# ---------- 4. 逐条 ModRM 分类 ----------
stores, others = [], []
for a, w in cand.items():
    o = TEXT['rawptr'] + (a - TEXT['va'])
    ins = list(md.disasm(RAW[o:o + 15], a))
    if not ins:
        others.append((a, None, 'undecodable', w)); continue
    i = ins[0]
    imm = None
    for opd in i.operands:
        if opd.type == X86_OP_IMM and opd.imm in VTS:
            imm = opd.imm; break
    if imm is None:
        others.append((a, None, i.mnemonic + ' ' + i.op_str, w)); continue
    o0 = i.operands[0]
    if (i.mnemonic == 'mov' and len(i.operands) == 2
            and o0.type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM):
        m = o0.mem
        stores.append((a, imm,
                       i.reg_name(m.base) if m.base else None,
                       i.reg_name(m.index) if m.index else None,
                       m.disp))
    else:
        others.append((a, imm, i.mnemonic + ' ' + i.op_str, w))

N4 = len(stores)
STACK = {'esp', 'ebp'}
N5_list = [s for s in stores if s[2] not in STACK and s[2] is not None and s[3] is None]
N5 = len(N5_list)

def mdisp_of(vt):
    rec = VTS.get(vt)
    return None if rec is None else rec['mdisp']

eq = [s for s in N5_list if s[4] == mdisp_of(s[1])]
ne = [s for s in N5_list if s[4] != mdisp_of(s[1])]
N6 = len(eq)

# ---------- 反控 ----------
N6_ctrl = len([s for s in N5_list if s[4] + 1 == mdisp_of(s[1])])
N6_const0 = len([s for s in N5_list if 0 == mdisp_of(s[1])])

# ---------- top10 ----------
disp_top10 = collections.Counter(s[4] for s in ne).most_common(10)
cls_top10 = collections.Counter(class_name(VTS[s[1]]['ptd']) or '<unknown>' for s in ne).most_common(10)
stack_n = sum(1 for s in stores if s[2] in STACK)
idx_n = sum(1 for s in stores if s[3] is not None)
abs_n = sum(1 for s in stores if s[2] is None)

# ---------- 输出 ----------
print('N1 = %d' % N1)
print('N2 = %d' % N2)
print('N3 = %d' % N3)
print('N4 = %d' % N4)
print('N5 = %d' % N5)
print('N6 = %d' % N6)
print('N6/N5 = %.4f%% (%d/%d)' % (100.0 * N6 / N5 if N5 else 0.0, N6, N5))
print('CTRL disp+1: N6 -> %d (must be 0) %s' % (N6_ctrl, 'OK' if N6_ctrl == 0 else 'FAIL'))
print('CTRL mdisp=0: N6 -> %d' % N6_const0)
print('DIFF_DISP_TOP10 = %s' % json.dumps([[str(k), v] for k, v in disp_top10], ensure_ascii=False))
print('DIFF_CLASS_TOP10 = %s' % json.dumps([[k, v] for k, v in cls_top10], ensure_ascii=False))
print('REF strict/loose: COL=%d/%d vtable=%d/%d N3_aligned=%d' %
      (N2, len(COLS_loose), N1, len(VTS_loose), N3_aligned))
print('REF stores=%d others=%d stack=%d indexed=%d absbase=%d ne=%d' %
      (N4, len(others), stack_n, idx_n, abs_n, len(ne)))

res = dict(N1=N1, N2=N2, N3=N3, N4=N4, N5=N5, N6=N6,
           pct=(100.0 * N6 / N5 if N5 else None),
           ctrl_disp_plus1=N6_ctrl, ctrl_mdisp_const0=N6_const0,
           disp_top10=[[str(k), v] for k, v in disp_top10],
           class_top10=cls_top10,
           ref=dict(strict_cols=N2, loose_cols=len(COLS_loose),
                    strict_vts=N1, loose_vts=len(VTS_loose), n3_aligned=N3_aligned,
                    stores=N4, others=len(others), stack=stack_n, indexed=idx_n,
                    absbase=abs_n, ne=len(ne)))
outp = os.path.join(OUTDIR, 'exec_hy4_census.json')
json.dump(res, open(outp, 'w'), indent=1, sort_keys=True)
print('JSON -> %s' % outp)
