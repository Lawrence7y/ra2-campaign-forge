# -*- coding: utf-8 -*-
"""R210-C 组1 定稿复核：通用栈参数跟踪 + 委托 call 组合，独立于主会话脚本。
只读 gamemd.exe，写 _r210/audit_g1.json。"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
RAW = P.RAW
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
mdL = Cs(CS_ARCH_X86, CS_MODE_32); mdL.detail = False
T = P.B['.text']; TLO, THI = T['lo'], T['hi_virt']
def intext(v): return v is not None and TLO <= v < THI

# ---------- COL / vftable ----------
cols = {}
for s in P.SECS:
    if s['rawsize'] < 24: continue
    o0, n = s['rawptr'], s['rawsize']
    for o in range(o0, o0 + n - 23, 4):
        sig, mdisp, cdo, ptd, pchd = struct.unpack_from('<5I', RAW, o)
        if sig not in (0, 1, 2) or cdo != 0 or mdisp > 0x10000: continue
        if P.where(ptd) != '.data' or P.where(pchd) != '.rdata': continue
        nm = P.cstr(ptd + 8, 200)
        if not nm or len(nm) < 2: continue
        cols[s['lo'] + (o - o0)] = {'mdisp': mdisp, 'pCHD': pchd, 'name': nm.decode('latin1')}
vt_of = {}
s = P.B['.rdata']; o0, n = s['rawptr'], s['rawsize']
for o in range(o0, o0 + n - 3, 4):
    v = struct.unpack_from('<I', RAW, o)[0]
    if v in cols: vt_of[v] = s['lo'] + (o - o0) + 4
def slots(vt, cap=400):
    r = []
    for i in range(cap):
        v = P.dw(vt + 4 * i)
        if not intext(v): break
        r.append(v)
    return r
views = {c: {'mdisp': cols[c]['mdisp'], 'pCHD': cols[c]['pCHD'], 'name': cols[c]['name'],
             'vt': vt, 's': slots(vt)} for c, vt in vt_of.items()}
by = collections.defaultdict(dict)
for c, v in views.items(): by[v['pCHD']][v['mdisp']] = c

# ---------- thunk ----------
def thunk(va):
    o = P.r2o(va)
    if o is None: return None
    b = RAW[o:o + 16]
    if len(b) < 10: return None
    if b[0] in (0x83, 0x81) and b[1] in (0x6c, 0x44) and b[2] == 0x24 and b[3] == 0x04:
        if b[0] == 0x83: imm = struct.unpack_from('<b', b, 4)[0]; p = 5
        else: imm = struct.unpack_from('<i', b, 4)[0]; p = 8
        sg = 1 if b[1] == 0x6c else -1
        if b[p] != 0xE9: return None
        return {'imm': sg * imm, 'jmp': va + p + 5 + struct.unpack_from('<i', b, p + 1)[0], 'size': p + 5}
    return None

# ---------- QI 解析：this 槽 = 入口 [esp+4]；委托 call 需组合 ----------
THIS_SLOT = 4
_memo = {}
def qi_R(f0, depth=0, stack=()):
    if f0 in _memo: return _memo[f0]
    if depth > 6: return set()
    o = P.r2o(f0)
    if o is None: return set()
    regs, delta, stores, calls = {}, 0, [], []
    for i in md.disasm(RAW[o:o + 900], f0):
        m = i.mnemonic; op = i.operands
        # 寄存器 -> (槽, 位移)
        if m == 'mov' and len(op) == 2 and op[0].type == X86_OP_REG and op[1].type == X86_OP_MEM:
            mm = op[1].mem; base = i.reg_name(mm.base) if mm.base else None
            d = i.reg_name(op[0].reg)
            if base == 'esp': regs[d] = (delta + mm.disp, 0)
            elif base in regs and regs[base]: regs[d] = (regs[base][0], regs[base][1] + mm.disp)
            else: regs[d] = None
        elif m == 'lea' and len(op) == 2 and op[1].type == X86_OP_MEM:
            mm = op[1].mem; base = i.reg_name(mm.base) if mm.base else None
            d = i.reg_name(op[0].reg)
            regs[d] = (regs[base][0], regs[base][1] + mm.disp) if (base in regs and regs[base]) else None
        elif m == 'mov' and len(op) == 2 and op[0].type == X86_OP_REG and op[1].type == X86_OP_REG:
            regs[i.reg_name(op[0].reg)] = regs.get(i.reg_name(op[1].reg))
        elif m in ('add', 'sub') and len(op) == 2 and op[0].type == X86_OP_REG \
                and op[1].type == X86_OP_IMM and regs.get(i.reg_name(op[0].reg)):
            d = i.reg_name(op[0].reg); b = regs[d]
            regs[d] = (b[0], b[1] + (op[1].imm if m == 'add' else -op[1].imm))
        elif m == 'xor' and len(op) == 2 and op[0].type == X86_OP_REG and op[0].reg == op[1].reg:
            regs[i.reg_name(op[0].reg)] = None
        elif op and op[0].type == X86_OP_REG and m not in ('test', 'cmp', 'push', 'call', 'jmp',
                                                           'jcc', 'nop', 'repe', 'repne'):
            regs[i.reg_name(op[0].reg)] = None
        # 记录 this 派生值写出
        if op and op[0].type == X86_OP_MEM and len(op) == 2 and op[1].type == X86_OP_REG:
            src = i.reg_name(op[1].reg)
            tg = regs.get(src)
            if tg and tg[0] == THIS_SLOT: stores.append(tg[1])
        if m == 'call' and op and op[0].type == X86_OP_IMM:
            t = op[0].imm
            if intext(t): calls.append(t)
        if m == 'push': delta -= 4
        elif m == 'pop': delta += 4
        elif m in ('sub', 'add') and len(op) == 2 and op[0].type == X86_OP_REG \
                and i.reg_name(op[0].reg) == 'esp' and op[1].type == X86_OP_IMM:
            delta += (-op[1].imm if m == 'sub' else op[1].imm)
        if m in ('ret', 'retf'):
            tail = RAW[o + (i.address - f0) + i.size: o + (i.address - f0) + i.size + 2]
            if tail and tail[0] in (0x90, 0xcc): break
    R = set(stores)
    for t in calls:                       # QI 委托：先调基类 QI，再追加本类偏移
        if t in stack: continue
        if looks_like_qi(t):
            R |= qi_R(t, depth + 1, stack + (f0,))
    _memo[f0] = R
    return R

def looks_like_qi(f0):
    o = P.r2o(f0)
    if o is None: return False
    b = RAW[o:o + 24]
    # 典型头部：读 [esp+0xc]/[esp+0x10] 或 push ebx; mov ebx,[esp+8]
    return (b[0] == 0x8B and b[1] == 0x44 and b[2] == 0x24) or \
           (b[0] == 0x8B and b[1] == 0x54 and b[2] == 0x24) or \
           (b[0] == 0x53 and b[1] == 0x8B and b[2] == 0x5C and b[3] == 0x24)

# ---------- 101 / 91 口径 ----------
extra_all = [(c, v) for c, v in views.items() if v['mdisp'] != 0]
cand = [(c, v) for c, v in extra_all if thunk(v['s'][0]) is not None]
TGT = {thunk(v['s'][0])['jmp'] for _, v in cand}
print('视图总数=%d  mdisp!=0 视图=%d  其中 slot0 挂 thunk=%d（主张 101）'
      % (len(views), len(extra_all), len(cand)))
print('涉及类=%d（主张 91）  slot0 thunk 落点=%d' % (len({v['pCHD'] for _, v in cand}), len(TGT)))

# ---------- 律 U 逐类 ----------
okl, badl = [], []
for p in sorted(by):
    m = by[p]
    if 0 not in m: continue
    if p not in {v['pCHD'] for _, v in cand}: continue
    f0 = views[m[0]]['s'][0]
    R = qi_R(f0)
    ex = sorted(o for o in m if o != 0 and thunk(views[m[o]]['s'][0]) is not None)
    pred = sorted({4} | {r for r in R if r > 0})
    rec = {'name': views[m[0]]['name'], 'slot0': hex(f0), 'R': sorted(R),
           'extra_thunked': ex, 'pred': pred}
    (okl if set(pred) == set(ex) else badl).append(rec)
print('\n律 U：成立 %d / 共 %d   不成立 %d' % (len(okl), len(okl) + len(badl), len(badl)))
for b in badl: print('  F:', b)
print('House:', [r for r in okl + badl if r['slot0'] == '0x4f6830'])

# ---------- 双向等价 ----------
S = TGT
rev_all = [p for p, m in by.items() if 0 in m]
on_tgt = [p for p in rev_all if views[by[p][0]]['s'][0] in S]
tgt_thunked = {v['pCHD'] for _, v in cand}
print('\n反向：主视图类 %d；slot0 落在 12 个 QI 落点的类 %d；其中有 thunk 额外视图的类 %d'
      % (len(rev_all), len(on_tgt), len(set(on_tgt) & tgt_thunked)))
print('  仅落在落点却无 thunk 额外视图的类 =', [views[by[p][0]]['name'] for p in on_tgt
                                            if p not in tgt_thunked])
print('  有 thunk 额外视图却 slot0 不在落点的类 =',
      [views[by[p][0]]['name'] for p in tgt_thunked if p not in set(on_tgt)])
json.dump({'views': len(views), 'extra_all': len(extra_all), 'extra_thunked': len(cand),
           'classes_thunked': len({v['pCHD'] for _, v in cand}), 'n_targets': len(TGT),
           'targets': sorted(hex(x) for x in TGT), 'ok': len(okl), 'bad': badl,
           'house': [r for r in okl + badl if r['slot0'] == '0x4f6830'],
           'rev_total': len(rev_all), 'rev_on_target': len(on_tgt),
           'rev_on_target_thunked': len(set(on_tgt) & tgt_thunked)},
          open(ROOT + '/_r210/audit_g1.json', 'w'), indent=1)
