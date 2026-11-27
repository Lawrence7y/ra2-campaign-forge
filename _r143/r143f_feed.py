#!/usr/bin/env python3
"""R143 F：决定性相对判据 —— 每个装载位移的「被用作虚派发基址」的比率。

若对象偏移 0 处的 dword 不是 vptr（而只是普通字段），那么「mov reg,[obj+d]; call [reg+4k]」
在 d==0 与 d==4/8/... 上应当同率出现。实测逐位移的 feed 率即可判定：
  feed_rate(d) = (该位移上被用作派发基址的装载条数) / (该位移上的装载总条数)
C1 已证「构造器把虚表立即数写到偏移 0」；本步证「读取侧只在偏移 0 上富集」。
反控：把喂给派发的实参换成「不参与派发的装载」，比较同一批位移上的比率。
"""
import struct, json, subprocess, re, collections, random, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = 'ra2bench/gamemd.exe'
data = open(P, 'rb').read(); N = len(data)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
T = [s for s in secs if s[0] == '.text'][0]
TEXT_RAW = T[3]; TEXT_RSZ = T[4]

def va2off(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs):
            d = va - lo
            return raw + d if d < rs else None
    return None

def rd(va, l):
    o = va2off(va)
    if o is None or o + l > N: return None
    return data[o:o + l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs): return nm
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')
STK = ('esp', 'ebp')
W_MN = {'mov', 'movzx', 'movsx', 'lea', 'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor',
        'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul',
        'pop', 'xchg', 'bswap', 'mul', 'div', 'idiv'}

def sweep():
    off = TEXT_RAW; end = TEXT_RAW + TEXT_RSZ
    while off < end:
        chunk = data[off:min(off + 65536, end)]
        base = IB + (T[1] + (off - TEXT_RAW))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(chunk, base):
            if a - base + sz > len(chunk): break
            consumed = a - base + sz
            yield a, sz, mn, re.sub(r'\s*([+,*])\s*', r'\1', op or '')
        off += consumed if consumed else 1

RE_LOAD = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')
RE_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')

def disp_of(s):
    if s is None: return 0
    return int(s[3:], 16) if s.startswith('+0x') else -int(s[1:])

# 单遍：装载全量直方图 + 由装载喂给派发的装载 VA 集合
loads = []              # (va, dst, base, disp)
fed = set()             # 被用作派发基址的那一次装载的 VA
last = {}
for a, sz, mn, op in sweep():
    if not op: continue
    if mn in ('call', 'jmp'):
        mc = RE_CALL.match(op)
        if mc and mc.group(1) in GEN:
            l = last.get(mc.group(1))
            if l and l[0] == 'load':
                fed.add(l[3])
        for r in ('eax', 'ecx', 'edx'):
            last[r] = ('clobber', None, None, a)
        continue
    ml = RE_LOAD.match(op)
    if ml and mn == 'mov':
        dst, base, d = ml.group(1), ml.group(2), disp_of(ml.group(3))
        loads.append((a, dst, base, d))
        if dst in GEN:
            last[dst] = ('load', base, d, a)
        continue
    if mn == 'lea' and ',' in op:
        dst = op.partition(',')[0]
        if dst in GEN: last[dst] = ('other', None, None, a)
    elif mn in W_MN:
        dst = op.partition(',')[0]
        if dst in GEN: last[dst] = ('other', None, None, a)

tot_obj = collections.Counter()
tot_stk = collections.Counter()
feed_obj = collections.Counter()
feed_stk = collections.Counter()
for a, dst, base, d in loads:
    if base in GEN:
        tot_obj[d] += 1
        if a in fed: feed_obj[d] += 1
    elif base in STK:
        tot_stk[d] += 1
        if a in fed: feed_stk[d] += 1

def table(c_tot, c_feed, keys):
    out = []
    for d in keys:
        t = c_tot.get(d, 0); f = c_feed.get(d, 0)
        out.append({'disp': d, 'loads': t, 'fed': f,
                    'rate': round(f / t, 4) if t else None})
    return out

KEY = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 0x84, 0x1b8]
res = {
 'exe_sha256': hashlib.sha256(data).hexdigest(),
 'exe_bytes': N,
 'loads_total': len(loads),
 'fed_unique_loads': len(fed),
 'obj_loads_total': sum(tot_obj.values()),
 'obj_fed_total': sum(feed_obj.values()),
 'obj_overall_rate': round(sum(feed_obj.values()) / max(1, sum(tot_obj.values())), 4),
 'stk_loads_total': sum(tot_stk.values()),
 'stk_fed_total': sum(feed_stk.values()),
 'stk_overall_rate': round(sum(feed_stk.values()) / max(1, sum(tot_stk.values())), 4),
 'obj_table': table(tot_obj, feed_obj, KEY),
 'stk_table': table(tot_stk, feed_stk, KEY),
 'obj_top_disp_by_loads': tot_obj.most_common(15),
 'obj_top_disp_by_feed': feed_obj.most_common(15),
 'disp0_rank_by_loads': [d for d, c in tot_obj.most_common()].index(0) + 1,
 'disp0_rank_by_feed': [d for d, c in feed_obj.most_common()].index(0) + 1,
 'obj_feed_at_4_8': {str(k): feed_obj.get(k, 0) for k in (4, 8)},
 'obj_loads_at_4_8': {str(k): tot_obj.get(k, 0) for k in (4, 8)},
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143f_feed.json', 'w'), ensure_ascii=False, indent=1)
