#!/usr/bin/env python3
"""R145 D：把 R144 的六形态普查换成「宽容解析器」，量化负位移漏洞对每个形态的影响。

R144（r144a）六形态：
  F1 imm∈VTS + 通用寄存器基址 + disp=0
  F3 imm∈VTS + 通用寄存器基址 + disp≠0
  F4 imm∈VTS + 绝对地址基址
  F5 寄存器搬运（mov/lea r, vt 后 <=6 条内 mov [base(+disp)], r）
  F6 .data/.rdata 初值 == vt
  F7 写栈帧 [esp/ebp(+disp)], imm∈VTS
全部依赖 r143lib.norm + RE_STORE，而 norm 不压 '-' 两侧空白 ⇒ 所有负位移站点整类丢弃。
本脚本用同一遍 disasm_lite 流式 + 宽容解析器重算六形态，输出：
  每形态 站点数 / distinct vt / 被 R144 口径丢弃的站点数
  并集、残余，以及与 R144 收口值（1213 / 5 张）的差异归因。
"""
import sys, re, json, struct, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN, STK = L.GEN, L.STK
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

# 宽容内存解析：base [+index*scale] [±disp]，符号两侧允许空格
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def memparse(s):
    s = s.replace(' ', '')
    if not s: return None
    if s.startswith('0x') and re.fullmatch(r'0x[0-9a-f]+', s):
        return ('abs', None, 0, int(s, 16))
    toks = re.findall(r'[+-]?[^+-]+', s)
    base = index = None; scale = 0; disp = 0
    for t in toks:
        sign = -1 if t.startswith('-') else 1
        core = t.lstrip('+-')
        if '*' in core:
            r, k = core.split('*'); index = r; scale = int(k)
        elif re.fullmatch(r'0x[0-9a-f]+|\d+', core):
            disp += sign * (int(core, 16) if core.startswith('0x') else int(core))
        elif base is None:
            base = core
        elif index is None:
            index = core; scale = 1
        else:
            return None
    return ('reg', base, scale, disp, index) if index is None else ('idx', base, scale, disp, index)

def parse(op):
    m = TOL.match(op)
    if not m: return None
    return memparse(m.group(1)), (m.group(2) or '').strip()

IMMR = L.RE_IMM
f1, f3, f4, f7, idxs = [], [], [], [], []          # (va, base, disp, vt)
regmove = []
dropped = collections.Counter()                     # 被 RE_STORE 丢弃但宽容解析接住
pend = {}; n = 0
for a, sz, mn, op in B.sweep(md):
    n += 1
    for r in [r for r, v in pend.items() if n - v[2] > 6]:
        del pend[r]
    if not op: continue
    pr = parse(op) if op.startswith('dword ptr [') else None
    if pr:
        mem, tgt = pr
        strict_ok = L.RE_STORE.match(op) is not None
        if mem is None:
            pass
        else:
            kind = mem[0]
            base, scale, disp, index = mem[1], mem[2], mem[3], (mem[4] if len(mem) > 4 else None)
            if tgt and IMMR.match(tgt):
                iv = immv(tgt)
                if iv in VTS:
                    if kind == 'abs': f4.append((a, base, disp, iv))
                    elif base in GEN and index is None:
                        (f1 if disp == 0 else f3).append((a, base, disp, iv))
                    elif base in STK and index is None: f7.append((a, base, disp, iv))
                    elif index is not None: idxs.append((a, op, hex(iv)))
                    if not strict_ok: dropped['imm_' + kind] += 1
            elif tgt and tgt in GEN:
                p = pend.get(tgt)
                if p:
                    regmove.append((a, base, disp, p[0], p[1]))
                    if not strict_ok: dropped['reg_store'] += 1
        # 寄存器搬运的「装 vt」前驱
        if mn == 'mov':
            mm = re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op)
            if mm and mm.group(1) in GEN:
                v = immv(mm.group(2))
                if v in VTS: pend[mm.group(1)] = (v, a, n)
        elif mn == 'lea':
            mm = re.match(r'^([a-z0-9]+),\[(0x[0-9a-f]+)\]$', op)
            if mm and mm.group(1) in GEN:
                v = immv(mm.group(2))
                if v in VTS: pend[mm.group(1)] = (v, a, n)
        continue
    if mn == 'mov' and op:
        mm = re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op)
        if mm and mm.group(1) in GEN:
            v = immv(mm.group(2))
            if v in VTS: pend[mm.group(1)] = (v, a, n)
            else: pend.pop(mm.group(1), None)
        elif mm: pend.pop(mm.group(1), None)
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'): pend.pop(r, None)

data_init = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in VTS: data_init.append((B.IB + ava + i * 4, v))

cov = {'F1': {s[3] for s in f1}, 'F3': {s[3] for s in f3}, 'F4': {s[3] for s in f4},
       'F5': {s[3] for s in regmove}, 'F6': {s[1] for s in data_init}, 'F7': {s[3] for s in f7}}
union = set().union(*cov.values())
resid = sorted(VTS - union)
prev5 = [int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']]
# R144 口径下的负位移站点数（同一遍统计，strict_ok=False 且 disp<0）
neg_by_form = collections.Counter()
for nm, arr, di in (('F1', f1, 0), ('F3', f3, 2), ('F4', f4, 2), ('F7', f7, 2)):
    pass
neg_imm = collections.Counter()
for nm2, arr in (('F3', f3), ('F4', f4), ('F7', f7)):
    for s in arr:
        if s[2] < 0: neg_imm[nm2] += 1
neg_f5 = sum(1 for s in regmove if s[2] < 0)

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS), 'insns': n,
 'F1_sites': len(f1), 'F1_distinct': len(cov['F1']),
 'F3_sites': len(f3), 'F3_distinct': len(cov['F3']),
 'F3_neg_sites': neg_imm['F3'],
 'F4_sites': len(f4), 'F4_distinct': len(cov['F4']), 'F4_neg_sites': neg_imm['F4'],
 'F5_sites': len(regmove), 'F5_distinct': len(cov['F5']), 'F5_neg_sites': neg_f5,
 'F6_sites': len(data_init), 'F6_distinct': len(cov['F6']),
 'F7_sites': len(f7), 'F7_distinct': len(cov['F7']), 'F7_neg_sites': neg_imm['F7'],
 'idx_sites': len(idxs),
 'dropped_by_R144_parser': dict(dropped),
 'union': len(union), 'union_rate_of_1218': round(len(union) / len(VTS), 4),
 'resid_n': len(resid), 'resid': [hex(v) for v in resid],
 'resid_same_as_prev5_minus': [hex(v) for v in resid] == [hex(v) for v in sorted(set(prev5) - {0x7e6060})],
 'prev5_minus_7e6060': [hex(v) for v in sorted(set(prev5) - {0x7e6060})],
 'new_covered_vs_R144': [hex(v) for v in sorted(union - (set(VTS) - set(prev5)))],
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n2, c, v): POS.append([n2, bool(c), v])
chk('正控：F1 站点 2741 / distinct 838 与 R144 逐项相同', len(f1) == 2741 and len(cov['F1']) == 838, [len(f1), len(cov['F1'])])
chk('正控：F7 站点 1337 / distinct 223 与 R144 逐项相同', len(f7) == 1337 and len(cov['F7']) == 223, [len(f7), len(cov['F7'])])
chk('正控：F4 站点 341、F6 站点 990 与 R144 一致', len(f4) == 341 and len(data_init) == 990, [len(f4), len(data_init)])
chk('F3 在宽容口径下 >= R144 的 1305（负位移被补回）', len(f3) >= 1305, len(f3))
chk('F5 在宽容口径下 >= R144 的 142', len(regmove) >= 142, len(regmove))
chk('并集 > R144 的 1213', len(union) > 1213, len(union))
chk('残余 = R144 的 5 张 − {0x7E6060}', [hex(v) for v in resid] == [hex(v) for v in sorted(set(prev5) - {0x7e6060})], [hex(v) for v in resid])
chk('新增覆盖恰为 {0x7E6060}', union - (set(VTS) - set(prev5)) == {0x7E6060}, [hex(v) for v in union - (set(VTS) - set(prev5))])
chk('宽容口径下仍有 >=1 个站点被 R144 解析器丢弃（漏洞真实存在）', sum(dropped.values()) > 0, dict(dropped))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145d_tolerant_union.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False))
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-56s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
