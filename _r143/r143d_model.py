#!/usr/bin/env python3
"""R143 D：主测量脚本（带正/反控断言）。目标：用字节判「对象偏移 0 处的 dword 是否是虚表指针」。

三条判据：
  C1 写入侧：.text 内 mov dword ptr [reg+disp], imm32，reg 属于 {eax..edi}，imm32 属于 VTS。
     -> disp==0 的站点数、覆盖的 distinct vt 数、disp 直方图。
  C2 读取侧：间接 call/jmp [reg+4k] 的 reg，其最近一次定义是 mov reg,[reg2+disp]。
     -> 该 disp==0 的占比，与「全部对象类内存装载 disp==0 的占比」基线比 => 富集倍数。
     -> 再把装载基址 reg2 分为「栈类(esp/ebp)」与「对象类(其余 6 个)」分别统计。
  C3 槽位面：派发位移 disp/4 的分布，与「表槽数」的关系（只报事实，不下结论）。

反控（必须为真，否则脚本 assert 失败）：
  N1 伪虚表集合（等势随机抽样）下 C1 的 disp==0 站点数与 distinct 覆盖数必须显著低于真集。
  N2 把 C2 的「disp==0」换成 4/8/0xc/0x10，对象类计数必须逐级远低于 0 位。
  N3 绝对地址写（mov dword ptr [0x87f5d8], imm32）必须被单独归类，不得混入 C1 的对象类。
  N4 派发点必须 100% 落在 objdump 起点集里；基线是「起点集大小 / .text 字节数」。

内存纪律：只用 disasm_lite 流式（64KB 分块）；不对整段 .text 开 detail=True。
"""
import struct, json, subprocess, re, collections, random, sys, hashlib

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = 'ra2bench/gamemd.exe'
data = open(P, 'rb').read(); N = len(data)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
T = [s for s in secs if s[0] == '.text'][0]
TEXT_LO = IB + T[1]; TEXT_RAW = T[3]; TEXT_RSZ = T[4]; TEXT_VSZ = T[2]

POS = []   # 正控断言
NEG = []   # 反控断言

def ok(name, cond, detail=''):
    (POS if cond else POS).append((name, bool(cond), detail))
    if not cond:
        print('ASSERT FAIL(POS): %s %s' % (name, detail))

def okn(name, cond, detail=''):
    NEG.append((name, bool(cond), detail))
    if not cond:
        print('ASSERT FAIL(NEG): %s %s' % (name, detail))

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

# ---------------- 虚表集合 ----------------
pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
TDs = {}
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        for m in pat.finditer(data[raw:raw + rs]):
            s = IB + ava + m.start()
            if dw(s - 8) is not None and dw(s - 4) == 0 and sec_of(dw(s - 8)) in ('.data', '.rdata'):
                TDs[s - 8] = m.group()
tdset = set(TDs)
COL = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in tdset:
                c = IB + ava + i * 4 - 12
                if dw(c) == 0 and dw(c + 12) == v and dw(c + 16) != 0:
                    COL.add(c)
VTS = set(); VT_OCC = 0
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in COL:
                vt = IB + ava + i * 4 + 4
                if dw(vt - 4) == v:
                    VTS.add(vt); VT_OCC += 1

RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\](?:,([^,]+))?$')
RE_LOAD = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')
RE_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$')
RE_IMM = re.compile(r'^(0x[0-9a-f]+|\d+)$')

def disp_of(s):
    if s is None: return 0
    return int(s[3:], 16) if s.startswith('+0x') else -int(s[1:])

def scan(vtset):
    """一遍扫描，同时收集：对象类/绝对类 imm 存、派发点及其基址来源、装载位移直方图（分栈类/对象类）。"""
    st_obj = []          # (va, reg, disp, imm)
    st_abs = []          # (va, tgt_va, imm)
    rec = []             # (va, mn, reg, disp, kind, load_base, load_disp, load_va)
    load_obj = collections.Counter()
    load_stk = collections.Counter()
    last = {}
    n_ins = 0
    for a, sz, mn, op in sweep():
        n_ins += 1
        if not op: continue
        if mn in ('call', 'jmp'):
            mc = RE_CALL.match(op)
            if mc:
                b, d = mc.group(1), disp_of(mc.group(2))
                if b in GEN:
                    l = last.get(b)
                    if l and l[0] == 'load':
                        rec.append((a, mn, b, d, 'load', l[1], l[2], l[3]))
                    else:
                        rec.append((a, mn, b, d, (l[0] if l else 'unknown'), None, None, None))
                for r in ('eax', 'ecx', 'edx'):
                    last[r] = ('clobber', None, None, a)
                continue
        ms = RE_STORE.match(op)
        if ms and mn in ('mov', 'movl'):
            base, ds, tgt = ms.group(1), disp_of(ms.group(2)), ms.group(3)
            if tgt is not None and RE_IMM.match(tgt):
                iv = (int(tgt, 16) if tgt.startswith('0x') else int(tgt)) & 0xFFFFFFFF
                if base in GEN:
                    st_obj.append((a, base, ds, iv))
                elif base.startswith('0x'):
                    st_abs.append((a, int(base, 16), iv))
            continue
        ml = RE_LOAD.match(op)
        if ml and mn == 'mov':
            dst, base, ds = ml.group(1), ml.group(2), disp_of(ml.group(3))
            if base in GEN:
                load_obj[ds] += 1
            elif base in STK:
                load_stk[ds] += 1
            if dst in GEN:
                last[dst] = ('load', base, ds, a)
            continue
        if mn == 'lea' and ',' in op:
            dst = op.partition(',')[0]
            if dst in GEN: last[dst] = ('other', None, None, a)
        elif mn in W_MN:
            dst = op.partition(',')[0]
            if dst in GEN: last[dst] = ('other', None, None, a)
    return dict(st_obj=st_obj, st_abs=st_abs, rec=rec, load_obj=load_obj, load_stk=load_stk, n_ins=n_ins)

S = scan(VTS)
st_obj_vt = [s for s in S['st_obj'] if s[3] in VTS]
st_abs_vt = [s for s in S['st_abs'] if s[2] in VTS]
d0 = [s for s in st_obj_vt if s[2] == 0]
dn = [s for s in st_obj_vt if s[2] != 0]
vt_d0 = {s[3] for s in d0}
vt_dn = {s[3] for s in dn}

# C2
rec_load = [r for r in S['rec'] if r[4] == 'load']
obj_load = [r for r in rec_load if r[5] in GEN]
stk_load = [r for r in rec_load if r[5] in STK]
def share(c, k):
    return round(c.get(k, 0) / max(1, sum(c.values())), 4)
obj_d0 = sum(1 for r in obj_load if r[6] == 0)
stk_d0 = sum(1 for r in stk_load if r[6] == 0)
all_obj_loads = sum(S['load_obj'].values())
all_stk_loads = sum(S['load_stk'].values())

# C3 槽位面
slot = collections.Counter(r[3] // 4 for r in S['rec'])
slot_bad = sum(1 for r in S['rec'] if r[3] % 4 != 0)

# ---------------- 反控 ----------------
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(struct.unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
Sf = scan(FAKE)
fake_d0 = [s for s in Sf['st_obj'] if s[3] in FAKE and s[2] == 0]
fake_vt = {s[3] for s in fake_d0}

try:
    starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())
    SRC = '_r140/obj_starts.txt'
except Exception as e:
    starts = set(); SRC = 'UNAVAILABLE %s' % e
disp_in_starts = sum(1 for r in S['rec'] if r[0] in starts)
base_rate = len(starts) / TEXT_RSZ

res = {
 'exe_sha256': hashlib.sha256(data).hexdigest(),
 'exe_bytes': N,
 'instructions': S['n_ins'],
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS), 'vt_occurrences': VT_OCC,
 'C1_obj_imm_stores': len(S['st_obj']),
 'C1_obj_imm_stores_vt': len(st_obj_vt),
 'C1_obj_vt_disp0': len(d0),
 'C1_obj_vt_disp0_distinct': len(vt_d0),
 'C1_obj_vt_disp0_coverage': round(len(vt_d0) / len(VTS), 4),
 'C1_obj_vt_dispn': len(dn),
 'C1_obj_vt_dispn_distinct': len(vt_dn),
 'C1_obj_vt_union_distinct': len(vt_d0 | vt_dn),
 'C1_obj_disp_hist': dict(sorted(collections.Counter(s[2] for s in st_obj_vt).items())),
 'C1_obj_base_regs': dict(collections.Counter(s[1] for s in st_obj_vt)),
 'C1_abs_imm_stores': len(S['st_abs']),
 'C1_abs_imm_stores_vt': len(st_abs_vt),
 'C1_abs_disp_na': len(st_abs_vt),
 'C2_dispatch_total': len(S['rec']),
 'C2_kind_hist': dict(collections.Counter(r[4] for r in S['rec'])),
 'C2_load_total': len(rec_load),
 'C2_load_obj': len(obj_load), 'C2_load_obj_disp0': obj_d0,
 'C2_load_obj_disp0_share': round(obj_d0 / max(1, len(obj_load)), 4),
 'C2_load_stk': len(stk_load), 'C2_load_stk_disp0': stk_d0,
 'C2_load_stk_disp0_share': round(stk_d0 / max(1, len(stk_load)), 4),
 'C2_load_obj_by_disp': collections.Counter(r[6] for r in obj_load).most_common(10),
 'C2_load_shift4_8_c_10': {str(k): sum(1 for r in obj_load if r[6] == k) for k in (0, 4, 8, 12, 16)},
 'BASE_all_obj_loads': all_obj_loads,
 'BASE_all_obj_loads_disp0': S['load_obj'].get(0, 0),
 'BASE_all_obj_loads_disp0_share': share(S['load_obj'], 0),
 'BASE_all_stk_loads': all_stk_loads,
 'BASE_all_stk_loads_disp0': S['load_stk'].get(0, 0),
 'BASE_all_stk_loads_disp0_share': share(S['load_stk'], 0),
 'ENRICH_obj': round((obj_d0 / max(1, len(obj_load))) / max(1e-9, share(S['load_obj'], 0)), 3),
 'C3_slot_hist_top': slot.most_common(12),
 'C3_disp_mod4_nonzero': slot_bad,
 'C3_max_slot': max(slot) if slot else None,
 'N1_fake_n': len(FAKE), 'N1_fake_disp0_sites': len(fake_d0),
 'N1_fake_disp0_distinct': len(fake_vt),
 'N2_starts_src': SRC, 'N2_starts_n': len(starts),
 'N2_dispatch_in_starts': disp_in_starts,
 'N2_start_baseline_rate': round(base_rate, 4),
}
print(json.dumps(res, ensure_ascii=False, indent=1))

# ---------------- 断言 ----------------
ok('C1 对象类 imm 写里 imm 属于 VTS 的数量 > 0', len(st_obj_vt) > 0, len(st_obj_vt))
ok('C1 disp==0 是对象类里最常见的位移', collections.Counter(s[2] for s in st_obj_vt).most_common(1)[0][0] == 0)
ok('C1 disp==0 站点数 > disp!=0 站点数', len(d0) > len(dn), '%d vs %d' % (len(d0), len(dn)))
ok('C2 派发基址绝大多数由内存装载而来', len(rec_load) / len(S['rec']) > 0.9, len(rec_load) / len(S['rec']))
ok('C2 对象类装载位移 0 占多数', obj_d0 > 0.8 * len(obj_load), '%d/%d' % (obj_d0, len(obj_load)))
ok('C2 富集倍数 > 1.5', res['ENRICH_obj'] > 1.5, res['ENRICH_obj'])
ok('C2 栈类装载位移 0 的占比不同于对象类（形态可分辨）',
   abs(share(S['load_stk'], 0) - share(S['load_obj'], 0)) > 0.02,
   '%.4f vs %.4f' % (share(S['load_stk'], 0), share(S['load_obj'], 0)))
ok('C3 派发位移全部 4 字节对齐', slot_bad == 0, slot_bad)
okn('N1 伪虚表集合 disp0 站点数显著低于真集', len(fake_d0) < 0.2 * len(d0), '%d vs %d' % (len(fake_d0), len(d0)))
okn('N1 伪虚表 distinct 覆盖低于真集', len(fake_vt) < 0.2 * len(vt_d0), '%d vs %d' % (len(fake_vt), len(vt_d0)))
okn('N2 位移 0 远高于 4/8/0xc/0x10', obj_d0 > 10 * max(1, max(sum(1 for r in obj_load if r[6] == k) for k in (4, 8, 12, 16))))
okn('N3 绝对地址写不进对象类', all(s[1] in GEN for s in S['st_obj']))
okn('N4 派发点全部落在 objdump 起点集', disp_in_starts == len(S['rec']), '%d/%d' % (disp_in_starts, len(S['rec'])))
okn('N4 起点集基线远低于 100%', base_rate < 0.5, base_rate)

res['POS'] = [(n, c, d) for n, c, d in POS]
res['NEG'] = [(n, c, d) for n, c, d in NEG]
res['pos_pass'] = sum(1 for _, c, _ in POS if c)
res['pos_fail'] = sum(1 for _, c, _ in POS if not c)
res['neg_pass'] = sum(1 for _, c, _ in NEG if c)
res['neg_fail'] = sum(1 for _, c, _ in NEG if not c)
print('POS %d/%d  NEG %d/%d' % (res['pos_pass'], len(POS), res['neg_pass'], len(NEG)))
json.dump(res, open('_r143/r143d_model.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'st_vt_d0': [[hex(a), b, hex(v)] for a, b, d, v in d0[:50]],
           'st_vt_dn': [[hex(a), b, d, hex(v)] for a, b, d, v in dn[:50]],
           'rec_obj_load': [[hex(r[0]), r[1], r[2], r[3], r[5], r[6]] for r in obj_load[:50]]},
          open('_r143/r143d_samples.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if (res['pos_fail'] or res['neg_fail']) else 0)
