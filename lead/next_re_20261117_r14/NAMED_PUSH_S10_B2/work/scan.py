# -*- coding: utf-8 -*-
"""NAMED_PUSH_S10_B2 取证脚本：只读 gamemd.exe，全 .text skipdata 线性扫描 +
RTTI/vtable 解析，为第 19-36 行候选逐行收集 D-40 四环锚点。
④ 独立取证：direct E8/E9 + capstone 双通道 + 立即数/位移 + 全镜像 dword + vptr 装表上下文。"""
import os, sys, struct, hashlib, csv
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_OP_IMM, X86_OP_REG, X86_OP_MEM

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # batch dir
OUT = os.path.join(BASE, 'work')
HITS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv'

# --- 从 hits_detail.tsv 动态取 S10 named 排序第 19-36 行，避免手抄错 ---
rows = [r for r in csv.DictReader(open(HITS, encoding='utf-8'), delimiter='\t')
        if r['subsystem'] == 'S10' and r['p3b2_named'] == 'True']
rows.sort(key=lambda r: int(r['entry'], 16))
sel = rows[18:36]
assert len(sel) == 18
ENTRIES = [(r['entry'], r['name'], int(r['size'])) for r in sel]
for e in ENTRIES:
    assert e[0] == e[0].upper() and not e[0].startswith('0X'), e

h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest().upper()
assert h == EXE_SHA, h
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    secs.append(dict(nm=nm, va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
TEXT = next(s for s in secs if s['nm'] == '.text')
TEXT_VA, TEXT_END = TEXT['va'], TEXT['va'] + max(TEXT['vs'], TEXT['rs'])
DATA_SECS = [s for s in secs if s['nm'] in ('.rdata', '.data')]

def read(va, n):
    for s in secs:
        if s['va'] <= va < s['va'] + max(s['vs'], s['rs']):
            off = s['pr'] + (va - s['va'])
            return raw[off:off+n]
    return b''

def dword(va):
    b = read(va, 4)
    return int.from_bytes(b, 'little') if len(b) == 4 else None

def in_text(va):
    return TEXT_VA <= va < TEXT_END

# ---------- RTTI/vtable ----------
def rtti(vt):
    col = dword(vt-4)
    if col is None or not (0x7e0000 <= col < 0x850000): return None
    td = dword(col+0xC)
    if td is None or not (0x400000 <= td < 0x900000): return None
    s = read(td+8, 160).split(b'\x00')[0]
    try: nm = s.decode('latin1')
    except: nm = repr(s)
    return nm if nm.startswith('.?A') else None

def find_vt(entry):
    out = []; pat = struct.pack('<I', entry)
    for s in DATA_SECS:
        base = s['va']; start = s['pr']; ln = s['rs']; i = 0
        while True:
            j = raw.find(pat, start+i, start+ln-3)
            if j < 0: break
            va = base + (j - start); st = va
            while True:
                p = dword(st-4)
                if p is not None and in_text(p): st -= 4
                else: break
            en = va + 4
            while True:
                nx = dword(en)
                if nx is not None and in_text(nx): en += 4
                else: break
            nm = rtti(st)
            out.append(dict(vt=st, slot=(va-st)//4, name=nm, nslots=(en-st)//4, hitva=va))
            i = j - start + 1
    return out

# ---------- 全 .text 线性扫描：direct call/jmp rel32 目标索引 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
text_bytes = raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]
callers = {}   # target -> list of (site, mnemonic, size)
skipped = 0
for ins in md.disasm(text_bytes, TEXT_VA):
    if ins.id == 0:
        skipped += 1; continue
    if ins.id in (X86_INS_CALL, X86_INS_JMP) and ins.operands:
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            t = op.imm & 0xFFFFFFFF
            callers.setdefault(t, []).append((ins.address, ins.mnemonic+' '+ins.op_str, ins.size))

# 立即数/位移引用
imm_ref = {}
for ins in md.disasm(text_bytes, TEXT_VA):
    if ins.id == 0: continue
    for op in ins.operands:
        if op.type == X86_OP_IMM:
            k = '%08X' % (op.imm & 0xFFFFFFFF)
            imm_ref.setdefault(k, []).append((ins.address, ins.mnemonic+' '+ins.op_str))
        elif op.type == X86_OP_MEM and op.mem.disp:
            k = '%08X' % (op.mem.disp & 0xFFFFFFFF)
            imm_ref.setdefault(k, []).append((ins.address, ins.mnemonic+' '+ins.op_str+' [disp]'))

# raw E8/E9 rel32 直接调用（独立于 capstone）
text_sz = len(text_bytes)
def raw_direct(target):
    hits = []
    for off in range(0, text_sz-5):
        op = text_bytes[off]
        if op in (0xE8, 0xE9):
            rel = int.from_bytes(text_bytes[off+1:off+5], 'little', signed=True)
            site = TEXT_VA + off; t = (site + 5 + rel) & 0xFFFFFFFF
            if t == target: hits.append((site, 'E8' if op == 0xE8 else 'E9'))
    return hits

# 全镜像 dword 出现
def dword_occ(entry):
    pat = struct.pack('<I', entry); cnt = 0; txt = []; other = []
    for s in secs:
        base = s['pr']; ln = s['rs']; i = 0
        while True:
            j = raw.find(pat, base+i, base+ln-3)
            if j < 0: break
            va = s['va'] + (j - base)
            if s['nm'] == '.text':
                txt.append(va)
            else:
                other.append((s['nm'], va))
            cnt += 1
            i = j - base + 1
    return cnt, txt, other

lines = []
def P(x=''): lines.append(str(x))

P('# NAMED_PUSH_S10_B2 取证原始数据（第 19-36 行）')
P('EXE SHA-256 = %s' % h)
P('ImageBase=0x%08X .text=[0x%08X,0x%08X) size=0x%X' % (IB, TEXT_VA, TEXT_END, text_sz))
P('sections: ' + ', '.join('%s@0x%08X(vs=0x%X,rs=0x%X)' % (s['nm'], s['va'], s['vs'], s['rs']) for s in secs))
P('linear sweep: callers targets=%d skipdata_bytes=%d' % (len(callers), skipped))
# 阳性对照
ctrl = callers.get(0x410230, [])
P('阳性对照 callers[0x410230]=%d（验证扫描器有效）' % len(ctrl))
P()

for ea_s, name, size in ENTRIES:
    ea = int(ea_s, 16)
    P('=' * 92)
    P('ENTRY %s  NAME %s  size=%d' % (ea_s, name, size))
    # ①
    P('[1] 入口: in_text=%s  bytes@entry=%s' % (
        in_text(ea), raw[TEXT['pr']+(ea-TEXT_VA):TEXT['pr']+(ea-TEXT_VA)+16].hex(' ')))
    first = list(md.disasm(read(ea, 48), ea))[:10]
    for ins in first:
        P('    %08X  %-26s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic+' '+ins.op_str))
    # ②
    vts = find_vt(ea)
    if not vts:
        P('[2] 类身份: 无 vtable slot 指向本 entry（.rdata/.data 4字节 VA 命中 0）')
    else:
        P('[2] 类身份: %d 个 vtable slot 指向本 entry:' % len(vts))
        for v in vts[:14]:
            P('    vt=0x%08X slot=+%d(0x%X) nslots=%d RTTI=%r hitva=0x%08X' % (
                v['vt'], v['slot'], v['slot']*4, v['nslots'], v['name'], v['hitva']))
    # ④
    cl = callers.get(ea, [])
    rd = raw_direct(ea)
    ir = imm_ref.get(ea_s, [])
    cnt, txt, other = dword_occ(ea)
    P('[4] direct call/jmp (capstone) 指向本 entry: %d 处 %s' % (
        len(cl), [(hex(x[0]), x[1]) for x in cl[:12]]))
    P('[4] raw E8/E9 direct 指向本 entry: %d 处 %s' % (len(rd), [(hex(a), op) for a, op in rd[:12]]))
    P('[4] entry VA 立即数/位移引用 .text: %d 处 %s' % (len(ir), [('%08X'%a, d) for a, d in ir[:8]]))
    P('[4] entry VA 全镜像 dword: %d 次, .text内=%d %s, 非代码=%s' % (
        cnt, len(txt), ['%08X'%v for v in txt[:8]], other[:8]))
    P()

open(os.path.join(OUT, 'scan_all.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('wrote scan_all.txt lines=%d callers=%d ctrl=%d' % (len(lines), len(callers), len(ctrl)))
