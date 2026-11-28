# -*- coding: utf-8 -*-
"""R210-C 独立审计（deepseek 审核员）—— 自己重解析 PE/COL/vftable，不采信 q3.json。
输出 _r210/audit_deepseek.json 与逐项 PASS/FAIL 摘要。"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
RAW = P.RAW
mdD = Cs(CS_ARCH_X86, CS_MODE_32); mdD.detail = True
mdL = Cs(CS_ARCH_X86, CS_MODE_32); mdL.detail = False
TEXT = P.B['.text']; TLO, THI = TEXT['lo'], TEXT['hi_virt']
def intext(v): return v is not None and TLO <= v < THI

# ================= 1. COL =================
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
        va = s['lo'] + (o - o0)
        cols[va] = {'sig': sig, 'mdisp': mdisp, 'pTD': ptd, 'pCHD': pchd,
                    'name': nm.decode('latin1')}

# ================= 2. vftable（仅 .rdata 数据区；.text 里的 COL 引用是代码不是表） =================
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

views = {}   # col -> {'mdisp','pCHD','name','vt','s'}
for c, vt in vt_of.items():
    k = cols[c]
    views[c] = {'mdisp': k['mdisp'], 'pCHD': k['pCHD'], 'name': k['name'],
                'vt': vt, 's': slots(vt)}
by = collections.defaultdict(dict)      # pCHD -> {mdisp: col}
for c, v in views.items(): by[v['pCHD']][v['mdisp']] = c

N_VIEW = len(views)
N_EXTRA = sum(1 for v in views.values() if v['mdisp'] != 0)
N_CLS = len(by)
CLS_EXTRA = [p for p, m in by.items() if any(o != 0 for o in m)]
N_CLS_EXTRA = len(CLS_EXTRA)
N_CLS_MAIN = sum(1 for m in by.values() if 0 in m)

# ================= 3. QI 符号解析（单遍线性扫描 + esp 位移跟踪，无 CFG 爆炸） =================
def qi_offsets(f0, maxb=900):
    """返回 QI 里写入 out 参数的 this 派生偏移集合。
    状态：this 基准（来自 mov reg,[esp+4]，esp 位移跟踪）与 this+K 派生寄存器。"""
    o = P.r2o(f0)
    if o is None: return set()
    hits = set()
    regs = {}          # regname -> None | ('this', K)
    delta = 0          # esp 相对入口的位移
    try:
        for i in mdD.disasm(RAW[o:o + maxb], f0):
            m = i.mnemonic; op = i.operands
            # 记录写入内存的 this 派生值（用当前 esp 状态解释 store 无关紧要）
            if op and op[0].type == X86_OP_MEM and len(op) == 2 and op[1].type == X86_OP_REG:
                src = i.reg_name(op[1].reg)
                if regs.get(src): hits.add(regs[src][1])
            # 更新目的寄存器
            if op and op[0].type == X86_OP_REG:
                dst = i.reg_name(op[0].reg)
                if m == 'mov' and len(op) == 2 and op[1].type == X86_OP_MEM:
                    mm = op[1].mem
                    base = i.reg_name(mm.base) if mm.base else None
                    if base == 'esp':
                        regs[dst] = ('this', 0) if (delta + mm.disp) == 4 else None
                    elif base in regs and regs[base]:
                        regs[dst] = ('this', regs[base][1] + mm.disp)
                    else:
                        regs[dst] = None
                elif m == 'lea' and len(op) == 2 and op[1].type == X86_OP_MEM:
                    mm = op[1].mem
                    base = i.reg_name(mm.base) if mm.base else None
                    regs[dst] = ('this', regs[base][1] + mm.disp) if (base in regs and regs[base]) else None
                elif m == 'mov' and len(op) == 2 and op[1].type == X86_OP_REG:
                    regs[dst] = regs.get(i.reg_name(op[1].reg))
                elif m in ('add', 'sub') and len(op) == 2 and op[1].type == X86_OP_IMM and regs.get(dst):
                    regs[dst] = ('this', regs[dst][1] + (op[1].imm if m == 'add' else -op[1].imm))
                elif m == 'xor' and len(op) == 2 and op[0].reg == op[1].reg:
                    regs[dst] = None
                else:
                    regs[dst] = None
            # esp 调整（对后续指令生效）
            if m == 'push': delta -= 4
            elif m == 'pop': delta += 4
            elif m in ('sub', 'add') and len(op) == 2 and op[0].type == X86_OP_REG \
                    and i.reg_name(op[0].reg) == 'esp' and op[1].type == X86_OP_IMM:
                delta += (-op[1].imm if m == 'sub' else op[1].imm)
            # 函数结束：ret 之后紧跟 int3/nop 填充
            if m in ('ret', 'retf'):
                tail = RAW[o + (i.address - f0) + i.size: o + (i.address - f0) + i.size + 2]
                if tail and tail[0] in (0x90, 0xcc):
                    break
    except Exception:
        pass
    return hits

# ================= 组 1 =================
G1 = {'classes': [], 'fails': []}
slot0_hist = collections.Counter()
for p, m in sorted(by.items()):
    main = m.get(0)
    if main is None: continue
    f0 = views[main]['s'][0]
    slot0_hist[f0] += 1
    extras = sorted(o for o in m if o != 0)
    R = sorted(qi_offsets(f0) or [])
    pred = sorted({4} | {r for r in R if r > 0})
    rec = {'name': views[main]['name'], 'pCHD': p, 'slot0': f0, 'R': R,
           'extra': extras, 'pred': pred, 'ok': set(pred) == set(extras)}
    G1['classes'].append(rec)
    if not rec['ok']: G1['fails'].append(rec)
# 12 个 QI 目标判定：slot0 被 >=2 类共用
QI12 = [f for f, c in slot0_hist.items() if c >= 2]
S = set(QI12)
G1['n_extra_views'] = N_EXTRA
G1['n_classes_with_extra'] = N_CLS_EXTRA
G1['n_classes_main'] = N_CLS_MAIN
G1['n_extra_ok'] = sum(1 for r in G1['classes'] if r['ok'] and r['extra'])
G1['n_extra_fail'] = len(G1['fails'])
G1['distinct_slot0_with_extra'] = len({r['slot0'] for r in G1['classes'] if r['extra']})
G1['qi_targets_multi'] = len(QI12)
G1['slot0_hist_top'] = [{'fn': hex(f), 'classes': c} for f, c in slot0_hist.most_common(16)]
G1['rev_classes_on_qi12'] = sum(1 for r in G1['classes'] if r['slot0'] in S)
G1['rev_classes_on_qi12_with_extra'] = sum(1 for r in G1['classes'] if r['slot0'] in S and r['extra'])
G1['cls_has_view4'] = sum(1 for m in by.values() if 4 in m)
G1['extra_excl_8_12_21784'] = sum(1 for v in views.values()
                                  if v['mdisp'] not in (0, 8, 12, 21784))
G1['house'] = [r for r in G1['classes'] if r['slot0'] == 0x4f6830]
G1['extra_cnt_hist'] = dict(collections.Counter(len(r['extra']) for r in G1['classes']))
G1['pred_eq_extra_fails'] = [{'name': r['name'], 'slot0': hex(r['slot0']), 'R': r['R'],
                              'extra': r['extra'], 'pred': r['pred']} for r in G1['fails'][:25]]

# ================= 组 2 thunk =================
def thunk(va):
    o = P.r2o(va)
    if o is None: return None
    b = RAW[o:o + 16]
    if len(b) < 10: return None
    # 83 / 81  6c|44 24 04  imm  ; E9 rel32
    if b[0] in (0x83, 0x81) and b[1] in (0x6c, 0x44) and b[2] == 0x24 and b[3] == 0x04:
        if b[0] == 0x83:
            imm = struct.unpack_from('<b', b, 4)[0]; p = 5
        else:
            imm = struct.unpack_from('<i', b, 4)[0]; p = 8
        sign = 1 if b[1] == 0x6c else -1          # 6c = sub [esp+4],imm ; 44 = add
        if b[p] != 0xE9: return None
        rel = struct.unpack_from('<i', b, p + 1)[0]
        return {'kind': 'sub' if sign == 1 else 'add', 'imm': sign * imm,
                'jmp': va + p + 5 + rel, 'size': p + 5}
    return None

G2 = {'n': 0, 'ok': 0, 'fails': [], 'imm4_hits': 0, 'imm4_checked': 0,
      'by_k': {}, 'kinds': {}, 'distinct_thunks': 0}
occ = []
seenT = set()
for c, v in views.items():
    for k, f in enumerate(v['s']):
        t = thunk(f)
        if not t: continue
        G2['n'] += 1; occ.append((c, k, f, t)); seenT.add(f)
        G2['by_k'][k] = G2['by_k'].get(k, 0) + 1
        G2['kinds'][t['kind']] = G2['kinds'].get(t['kind'], 0) + 1
G2['distinct_thunks'] = len(seenT)
for c, k, f, t in occ:
    m = by[views[c]['pCHD']]
    mT = views[c]['mdisp']; mV = mT - t['imm']
    okv = mV in m
    exp = views[m[mV]]['s'][k] if (okv and k < len(views[m[mV]]['s'])) else None
    if okv and exp == t['jmp']: G2['ok'] += 1
    else: G2['fails'].append({'name': views[c]['name'], 'k': k, 'mT': mT, 'imm': t['imm'],
                              'mV': mV, 'mV_in_set': okv, 'jmp': hex(t['jmp']),
                              'expect': hex(exp) if exp else None, 'kind': t['kind'],
                              'thunk': hex(f)})
    mV2 = mT - t['imm'] + 4
    G2['imm4_checked'] += 1
    if mV2 in m and k < len(views[m[mV2]]['s']) and views[m[mV2]]['s'][k] == t['jmp']:
        G2['imm4_hits'] += 1
G2['n_fails'] = len(G2['fails']); G2['fail_sample'] = G2['fails'][:12]
G2['occ'] = [[hex(c), k, hex(f)] for c, k, f, t in occ]
G2['house_occ'] = [[hex(c), k, views[c]['mdisp'], hex(f), t['imm'], hex(t['jmp'])]
                   for c, k, f, t in occ if views[c]['name'] == '.?AVHouseClass@@']

# ================= 组 3 =================
mainv = [(c, v) for c, v in views.items() if v['mdisp'] == 0]
G3 = {'n_main': len(mainv), 'total_slots': sum(v['n'] if False else len(v['s']) for _, v in mainv),
      'slots_ge3': sum(max(0, len(v['s']) - 3) for _, v in mainv),
      'short_no_slot3': sum(1 for _, v in mainv if len(v['s']) <= 3)}
s3 = [(c, v['s'][3]) for c, v in mainv if len(v['s']) > 3]
G3['n_with_slot3'] = len(s3)
tgt = collections.Counter(a for _, a in s3)
G3['slot3_unique_tables'] = sum(1 for _, a in s3 if tgt[a] == 1)
G3['slot3_shared_tables'] = sum(1 for _, a in s3 if tgt[a] >= 2)
G3['slot3_distinct_targets'] = len(tgt)

def rets_of(addr, maxb=900):
    o = P.r2o(addr)
    if o is None: return None
    out = []
    try:
        for i in mdL.disasm(RAW[o:o + maxb], addr):
            if i.mnemonic in ('ret', 'retf'):
                s2 = i.op_str.strip().replace(' ', '')
                out.append('ret' + ('_' + s2 if s2 else ''))
    except Exception:
        pass
    return out

hf, hl, hm, noret, multi = collections.Counter(), collections.Counter(), collections.Counter(), 0, 0
for c, a in s3:
    rs = rets_of(a)
    if not rs: noret += 1; continue
    if len(set(rs)) > 1: multi += 1
    hf[rs[0]] += 1; hl[rs[-1]] += 1
    for x in set(rs): hm[x] += 1
G3['hist_first'] = hf.most_common(8)
G3['hist_last'] = hl.most_common(8)
G3['hist_mix'] = hm.most_common(8)
G3['noret'] = noret; G3['multi_ret_fn'] = multi
G3['n_main_with_vt_gt3'] = sum(1 for _, v in mainv if len(v['s']) > 3)

out = {'n_col': len(cols), 'n_view': N_VIEW, 'n_extra_views': N_EXTRA,
       'n_classes': N_CLS, 'n_classes_main': N_CLS_MAIN, 'n_classes_extra': N_CLS_EXTRA,
       'mdisp_hist': dict(sorted(collections.Counter(v['mdisp'] for v in views.values()).items())),
       'G1': G1, 'G2': G2, 'G3': G3}
json.dump(out, open(ROOT + '/_r210/audit_deepseek.json', 'w'), indent=0, ensure_ascii=False)

print('=== 结构 ===')
print('COL=%d  vftable=%d  extra(mdisp!=0)=%d  pCHD类=%d  含主视图类=%d  含额外视图类=%d'
      % (N_VIEW and len(cols), N_VIEW, N_EXTRA, N_CLS, N_CLS_MAIN, N_CLS_EXTRA))
print('mdisp_hist =', out['mdisp_hist'])
print('=== 组1 ===')
print('extra视图=%d 含额外视图类=%d 律U成立类=%d 不成立类=%d 有额外视图且成立类=%d'
      % (N_EXTRA, N_CLS_EXTRA, len(G1['classes']) - len(G1['fails']), len(G1['fails']),
         G1['n_extra_ok']))
print('slot0 共用目标数(multi)=%d ; 落在这些目标上的类=%d (其中有额外视图 %d)'
      % (G1['qi_targets_multi'], G1['rev_classes_on_qi12'], G1['rev_classes_on_qi12_with_extra']))
print('slot0 频次 top:', G1['slot0_hist_top'])
print('含偏移4视图的类=%d ; extras 排除 8/12/21784 后=%d'
      % (G1['cls_has_view4'], G1['extra_excl_8_12_21784']))
print('extra_cnt_hist =', G1['extra_cnt_hist'])
for r in G1['house']:
    print('House: slot0=%x R=%s extra=%s pred=%s ok=%s' % (r['slot0'], r['R'], r['extra'], r['pred'], r['ok']))
print('不成立样本:')
for r in G1['pred_eq_extra_fails'][:8]: print('  ', r)
print('=== 组2 ===')
print('thunk 槽位=%d (distinct thunk=%d) 律V成立=%d 失败=%d kinds=%s by_k=%s'
      % (G2['n'], G2['distinct_thunks'], G2['ok'], G2['n_fails'], G2['kinds'], G2['by_k']))
print('反控 imm+4 命中=%d / %d' % (G2['imm4_hits'], G2['imm4_checked']))
for f in G2['fail_sample'][:6]: print('  F2:', f)
print('House thunk occ:', G2['house_occ'])
print('=== 组3 ===')
print('主表=%d 总槽=%d slot>=3槽=%d 短表无slot3=%d 有slot3表=%d 独占=%d 复用=%d 落点数=%d'
      % (G3['n_main'], G3['total_slots'], G3['slots_ge3'], G3['short_no_slot3'],
         G3['n_with_slot3'], G3['slot3_unique_tables'], G3['slot3_shared_tables'],
         G3['slot3_distinct_targets']))
print('ret 首:', G3['hist_first'])
print('ret 末:', G3['hist_last'])
print('ret 混合:', G3['hist_mix'], 'noret=', G3['noret'], 'multi=', G3['multi_ret_fn'])
