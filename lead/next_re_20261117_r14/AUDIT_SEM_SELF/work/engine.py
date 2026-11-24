
import pefile, capstone, json, os, sys
from collections import deque

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True); IMAGE = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress+IMAGE, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
text = [s for s in secs if s[0]=='.text'][0]
TB, TS, TP, TR = text[1], text[2], text[3], text[4]
RAW = open(EXE,'rb').read()
tdata = RAW[TP:TP+TR]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True

def bytes_at(va, n):
    off = va - TB
    if off < 0 or off >= TS: return None
    return tdata[off:off+n]

def insn_at(va):
    b = bytes_at(va, 16)
    if not b: return None
    for i in md.disasm(b, va): return i
    return None

def direct_target(insn):
    # call / jmp / jcc 均为直接目标（单 imm 操作数）
    ops = insn.operands
    if not ops: return None
    m = insn.mnemonic
    if (m == 'call' or m == 'jmp' or m.startswith('j') or m in ('loop','loope','loopne')):
        if ops[0].type == capstone.x86.X86_OP_IMM:
            return ops[0].imm
    return None

# ---- 独立入口集（E8 直调目标；不用 atlas）----
import json as _json
_ENT = set()
try:
    _d = _json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\entries.json'))
    _ENT = set(_d['e8'])
except Exception:
    pass

# ---- CFG extent (independent of atlas) ----
def extent(entry, maxbytes=6000):
    seen = {}       # va -> insn
    work = deque([entry])
    visited = set()
    while work:
        va = work.popleft()
        while True:
            if va in visited: break
            if va < TB or va >= TB+TS: break
            if va - entry > maxbytes: break
            # 收束：走到另一个已知函数入口（E8 直调目标）即停，避免越界吞并下一函数
            if va != entry and va in _ENT and seen: break
            insn = insn_at(va)
            if insn is None: break
            visited.add(va); seen[va] = insn
            m = insn.mnemonic
            if m == 'ret' or m.startswith('ret'):
                break
            if m == 'jmp':
                t = direct_target(insn)
                if t is not None and entry <= t < entry+maxbytes:
                    va = t; continue
                break
            if m.startswith('j') or m in ('loop','loope','loopne'):
                t = direct_target(insn)
                if t is not None and entry <= t < entry+maxbytes:
                    work.append(t)
                va = insn.address + insn.size; continue
            if m in ('int3','hlt'): break
            va = insn.address + insn.size
    if not seen: return []
    return [seen[a] for a in sorted(seen)]

# ---- helpers ----
def is_call_direct(insn): return insn.mnemonic=='call' and insn.operands and insn.operands[0].type==capstone.x86.X86_OP_IMM
def mem_disp(insn):
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM:
            return op.mem.disp
    return None

def analyze(entry, name=''):
    body = extent(entry)
    if not body: return {'entry':hex(entry),'error':'no body'}
    feats = {'entry':hex(entry),'name':name,'n_instr':len(body),
             'span': (body[-1].address+body[-1].size) - entry,
             'jcc':0,'back_edges':[],'calls':[],'jmp_tables':[],'ret_forms':{},
             'imm_writes':[], 'push_sizes':[], 'xors':0, 'or_minus1':0, 'mov_minus1':[], 'indirect_jmp':[], 'cmp_targets':set()}
    mnems = [i.mnemonic for i in body]
    for i in body:
        m = i.mnemonic
        if m.startswith('j') and m!='jmp':
            feats['jcc'] += 1
            t = direct_target(i)
            if t is not None:
                if t <= i.address: feats['back_edges'].append((hex(i.address),hex(t)))
                feats['cmp_targets'].add(t)
        if m == 'jmp':
            for op in i.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.mem.index != 0:
                    feats['jmp_tables'].append((hex(i.address), hex(op.mem.disp), i.reg_name(op.mem.index), op.mem.scale))
                elif op.type == capstone.x86.X86_OP_MEM:
                    feats['indirect_jmp'].append((hex(i.address), hex(op.mem.disp)))
        if m == 'call':
            t = direct_target(i)
            if t is not None: feats['calls'].append((hex(i.address), hex(t)))
        if m.startswith('ret'):
            k = i.mnemonic + ' ' + i.op_str; feats['ret_forms'][k] = feats['ret_forms'].get(k,0)+1
        if m == 'push' and i.operands and i.operands[0].type == capstone.x86.X86_OP_IMM:
            v = i.operands[0].imm
            if 0x10 <= v <= 0x2000: feats['push_sizes'].append((hex(i.address), hex(v)))
        if m == 'or' and 'eax' in i.op_str and '-1' in i.op_str: feats['or_minus1'] += 1
        if m == 'mov' and i.op_str.endswith(', -1'): feats['mov_minus1'].append((hex(i.address), i.op_str))
        # vt write: mov dword ptr [reg], imm  or  mov dword ptr [reg+disp], imm
        if m == 'mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[1].type==capstone.x86.X86_OP_IMM:
            feats['imm_writes'].append((hex(i.address), i.op_str))
    feats['cmp_targets'] = len(feats['cmp_targets'])
    feats['loop_count'] = len(feats['back_edges'])
    feats['n_call'] = len(feats['calls'])
    feats['n_jmp_table'] = len(feats['jmp_tables'])
    feats['distinct_callees'] = len(set(t for _,t in feats['calls']))
    return feats, body

def dump(entry, outdir):
    feats, body = analyze(entry)
    with open(os.path.join(outdir, '%08X.asm' % entry), 'w', encoding='utf-8') as f:
        for i in body:
            f.write('%08X  %-24s %s %s\n' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return feats

# capstone ⑲ self-check
chs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); chs.detail=True
t = list(chs.disasm(bytes.fromhex('ff540424'), 0x401000))[0]  # call dword ptr [esp+4]
op = [o for o in t.operands if o.type==capstone.x86.X86_OP_MEM][0]
print('SELFCHECK op.mem.index=%r  is None? %s  (expect 0, False)' % (op.mem.index, op.mem.index is None))
