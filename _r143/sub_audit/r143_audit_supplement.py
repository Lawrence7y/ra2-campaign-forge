#!/usr/bin/env python3
"""R143 复核补充：三件事一次跑完。
(a) 负位移装载在 .text 中有多少（主口径 norm 正则是否结构性丢弃）
(b) 把指令统计限制在 VirtualSize 内的真实条数
(c) 构造/派发同寄存器链接证据：同一函数内先 mov [reg], <vt> 再 mov rX,[reg] 再 call/jmp [rX+disp]
"""
import re, json, struct, collections, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = 'ra2bench/gamemd.exe'
DATA = open(P, 'rb').read()
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(name=s.Name.decode().rstrip('\x00'), va=s.VirtualAddress, vs=s.Misc_VirtualSize,
             raw=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
T = [s for s in SECS if s['name'] == '.text'][0]
def va2off(va):
    for s in SECS:
        lo = IB + s['va']
        if lo <= va < lo + max(s['vs'], s['rs']):
            d = va - lo
            return s['raw'] + d if d < s['rs'] else None
def rd(va, l):
    o = va2off(va); return None if o is None else DATA[o:o+l]
def dw(va):
    b = rd(va, 4); return None if b is None else struct.unpack('<I', b)[0]
def sec_of(va):
    for s in SECS:
        lo = IB + s['va']
        if lo <= va < lo + max(s['vs'], s['rs']): return s['name']

# 复建虚表集合（与主脚本同法）
def build_vtset():
    pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@'); TDs = {}
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw']+s['rs']]
            for m in pat.finditer(blob):
                S = IB + s['va'] + m.start(); v = dw(S-8)
                if v is not None and dw(S-4) == 0 and sec_of(v) in ('.data', '.rdata'):
                    TDs.setdefault(S-8, 1)
    tdset = set(TDs); COL = set()
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v = struct.unpack_from('<I', blob, i*4)[0]
                if v in tdset:
                    c = IB + s['va'] + i*4 - 12
                    if dw(c) == 0 and dw(c+12) == v and dw(c+16) != 0: COL.add(c)
    VTS = set()
    for s in SECS:
        if s['name'] in ('.data', '.rdata'):
            blob = DATA[s['raw']:s['raw']+s['rs']]
            for i in range(len(blob)//4):
                v = struct.unpack_from('<I', blob, i*4)[0]
                if v in COL:
                    vt = IB + s['va'] + i*4 + 4
                    if dw(vt-4) == v: VTS.add(vt)
    return VTS
VTS = build_vtset()

GEN = ('eax','ebx','ecx','edx','esi','edi'); STK = ('esp','ebp')
SZ = ('byte','word','dword','qword')
MEM_RE = re.compile(r'^(?:(%s) ptr )?\[(.+)\]$' % '|'.join(SZ))
def parse_mem(s):
    m = MEM_RE.match(s or '')
    if not m: return None
    size = m.group(1); inner = m.group(2)
    toks = [t for t in inner.replace('-', '+-').split('+') if t]
    base = idx_ = None; scale = 1; disp = 0
    for t in toks:
        if '*' in t:
            r, sc = t.split('*'); idx_, scale = r.strip(), int(sc, 0)
        elif re.fullmatch(r'[a-z]{2,3}', t):
            if base is None: base = t
            else: idx_, scale = t, 1
        else:
            try: disp += int(t, 0)
            except ValueError: return None
    return size, base, idx_, scale, disp
IMM = re.compile(r'^-?(?:0x[0-9a-f]+|\d+)$')
def immval(t): return (int(t,16) if t.lstrip('-').startswith('0x') else int(t)) & 0xFFFFFFFF

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
def sweep(chunk=32768):
    off = T['raw']; end = T['raw'] + T['rs']
    while off < end:
        blob = DATA[off:min(off+chunk, end)]
        base = IB + (T['va'] + (off - T['raw'])); consumed = 0
        for a, sz, mn, op in md.disasm_lite(blob, base):
            d = a - base
            if d + sz > len(blob): break
            consumed = d + sz
            yield a, sz, mn, op
        off += consumed if consumed else 1

vend = IB + T['va'] + T['vs']
n_all = 0; n_in_vs = 0
neg_mem = collections.Counter(); neg_mem_samples = defaultdict = collections.defaultdict(list)
neg_load_dword = 0; neg_load_samples = []
# (c) 同寄存器链接
links = 0; link_samples = []
chain = collections.defaultdict(list)   # reg -> [(idx, kind, detail)]
idx = 0
prev_ctx = []
for a, sz, mn, op in sweep():
    n_all += 1
    if a < vend: n_in_vs += 1
    if not op: idx += 1; continue
    ops = [x.strip() for x in re.split(r',(?![^\[]*\])', op)]
    # (a) 负位移内存操作数计数
    for o in ops:
        if '[' in o and re.search(r'-\s*(?:0x[0-9a-f]+|\d+)\s*\]', o):
            mn2 = parse_mem(o)
            neg_mem[mn] += 1
            if len(neg_mem_samples[mn]) < 3: neg_mem_samples[mn].append([hex(a), op])
            if mn == 'mov' and mn2 and mn2[0] == 'dword' and mn2[1] in GEN and o == ops[1]:
                neg_load_dword += 1
                if len(neg_load_samples) < 5: neg_load_samples.append([hex(a), op])
    # (c) 装表 -> 同基址装载 -> 派发
    if mn == 'mov' and len(ops) == 2:
        m1 = parse_mem(ops[0])
        if m1 and m1[0] == 'dword' and m1[1] in GEN and m1[2] is None and m1[4] == 0 and IMM.match(ops[1]):
            v = immval(ops[1])
            if v in VTS:
                chain[m1[1]] = [('store', idx, v)]
        m2 = parse_mem(ops[1])
        if m2 and m2[0] == 'dword' and ops[0] in GEN:
            for st in chain.get(m2[1], []):
                if st[0] == 'store' and idx - st[1] <= 40:
                    chain[ops[0]] = [('load', idx, (m2[1], st[2]))]
    if mn in ('call', 'jmp') and len(ops) == 1:
        mm = parse_mem(ops[0])
        if mm and mm[1] in GEN and mm[1] in chain:
            for st in chain[mm[1]]:
                if st[0] == 'load' and idx - st[1] <= 40:
                    links += 1
                    if len(link_samples) < 10:
                        link_samples.append([hex(a), op, st[2][0], hex(st[2][1]), mm[4]])
    if mn in ('mov','movzx','movsx','lea','pop','bswap') and ops and ops[0] in GEN:
        for r in GEN:
            if r != ops[0]: pass
        chain.pop(ops[0], None)
    if mn in ('call','jmp'):
        for r in list(chain):
            if r not in ('esi','edi','ebx'): chain.pop(r, None)
    idx += 1

tail = DATA[T['raw'] + T['vs']:T['raw'] + T['rs']]
res = {
 'text_vs': T['vs'], 'text_rs': T['rs'], 'tail_bytes': len(tail),
 'tail_all_zero': len(set(tail)) == 1 and tail[:1] == b'\x00',
 'insn_all_raw': n_all, 'insn_within_virtualsize': n_in_vs,
 'insn_in_padding': n_all - n_in_vs,
 'neg_disp_mem_ops_by_mnemonic': neg_mem.most_common(12),
 'neg_disp_samples': {k: v for k, v in list(neg_mem_samples.items())[:6]},
 'neg_disp_mov_dword_loads': neg_load_dword,
 'neg_disp_mov_samples': neg_load_samples,
 'ctor_link_dispatch_sites': links,
 'ctor_link_samples': link_samples,
 'neg_disp_total': sum(neg_mem.values()),
}
json.dump(res, open('_r143/sub_audit/audit_supplement.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
