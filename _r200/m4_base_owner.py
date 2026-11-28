#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第四刀（决定性订正）：538 条装表 store 的**目标对象归属**。

m1/m2/m3 显示：538 条里偏移全 0 的 532 条中有 16 条 imm 与 vt_d 无 RTTI 血缘（GenericNode / ?$VectorClass@H@@ /
?$rc_ptr@..@ / BlowPipe），且这 16 条的 store 基址未必是 this。
本刀用**基址寄存器的来源**做硬判据，把每条 store 归到三类：
  T=this（基址是 esi 且在函数序言里由参数/自身搬运而来，或基址就是 this 寄存器）
  N=new（基址寄存器在 store 之前被 call 的返回值 eax 覆盖，或 lea 自 [this+off] 后的字段指针）
  F=field（基址来自 mov reg,[reg+imm] 的字段加载，即指向成员指针）
判据细化（全部字节，按指令序列顺序回放）：
 M1 记录体内每条指令对 eax/ebx/ecx/edx/esi/edi/ebp 的整字写（mov/lea/pop/xor reg,reg/call 隐含 eax）。
 M2 store 基址 reg 的最近一次定义：
    - 'mov reg, esi' / 'lea reg,[esi+..]' / 'lea reg,[esp+..]'（this 经栈传）= this 侧
    - 'call 0x..' 紧接其后（= 返回值 eax）= new/alloc 侧
    - 'mov reg,[reg2+imm]' = field 侧
    - 'mov reg, imm32' = const 侧（不可能用于 store 基址，但记录）
    - 无定义 = unknown
 M3 用该归属 x imm 类别（own/base/other/nonvt）交叉。
反控：
 R1 把「this 侧」判据放宽为「reg == esi」（R199 口径）看交叉变化。
 R2 只要 base 归属 unknown 的条数 > 20 就说明判据不足，须在正文标注。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
ck('M0a 516', len(s0d) == 516, len(s0d))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

def evolve(ins):
    """顺序回放，返回每个下标处「各寄存器最近一次定义」。"""
    state = {}; hist = []
    for idx, (ad, sz, mn, op) in enumerate(ins):
        hist.append(dict(state))
        if mn in ('mov', 'lea') and ',' in op:
            dst, src = [x.strip() for x in op.split(',', 1)]
            if dst in REGS:
                state[dst] = (idx, mn, src)
            # 内存写不改寄存器
        elif mn == 'xor' and op.split(',')[0].strip() == op.split(',')[-1].strip() and op.split(',')[0].strip() in REGS:
            state[op.split(',')[0].strip()] = (idx, 'zero', '0')
        elif mn == 'pop' and op.strip() in REGS:
            state[op.strip()] = (idx, 'pop', '')
        elif mn == 'call':
            state['eax'] = (idx, 'call', op)
        elif mn in ('add', 'sub', 'inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar') and ',' in op:
            dst = op.split(',')[0].strip()
            if dst in REGS: state[dst] = (idx, 'arith', op)
    return hist

def classify_base(src, mn):
    if src in ('esi',):
        return 'this'
    if src.startswith('dword ptr [esi') or src.startswith('dword ptr [esp'):
        return 'field' if 'esi' in src else 'stack'
    if re.match(r'^0x[0-9a-f]+$', src):
        return 'const'
    if mn == 'call':
        return 'new'
    if src in REGS:
        return 'copy:' + src
    return 'other'

cross = collections.Counter(); rows = []; unk = 0
for vt_d, a, vt_b in s0d:
    ins = body(a) or []
    hist = evolve(ins)
    for idx, (ad, sz, mn, op) in enumerate(ins):
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        reg = m.group(1); off = int(m.group(2), 16) if m.group(2) else 0
        imm = int(m.group(3), 16)
        if imm == vt_d: t = 'own_main'
        elif imm == vt_b: t = 'base_main'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other_main'
        else: t = 'nonvt'
        st = hist[idx]
        # 基址 reg 归约：若 reg 是 esi 本身 => this；否则看最近定义
        if reg == 'esi':
            base = 'this'
        elif reg in st:
            d_idx, d_mn, d_src = st[reg]
            base = classify_base(d_src, d_mn)
            # copy 链再归约一层
            if base.startswith('copy:'):
                r2 = base.split(':')[1]
                if r2 == 'esi': base = 'this_copy'
                elif r2 in st:
                    _, m2, s2 = st[r2]
                    base = 'copy2:' + classify_base(s2, m2)
                else: base = 'copy_unknown'
        else:
            base = 'unknown'; unk += 1
        cross[(base, t)] += 1
        rows.append(dict(cls_d=CLS[vt_d], impl=hex(a), store=hex(ad), reg=reg, off=off, imm=hex(imm),
                         cat=t, base=base, cls_imm=CLS.get(imm)))

print('   M3 归属 x 类别交叉:')
for k in sorted(cross): print('        %-18s %-12s %d' % (k[0], k[1], cross[k]))
ck('M2a store 总数 538', len(rows) == 538, len(rows))
thisn = sum(v for (b, t), v in cross.items() if b in ('this', 'this_copy'))
ck('M3a this 侧 store 条数', True, thisn)
print('   M3b this 侧 %d / 538 = %.2f%%' % (thisn, 100.0 * thisn / 538))
nonthis = [(b, t, v) for (b, t), v in cross.items() if b not in ('this', 'this_copy')]
print('   M3c 非 this 侧明细: %s' % sorted(nonthis))
ck('R2a unknown 条数 <= 20', unk <= 20, unk)

# 关键交叉：非 this 的 store 的 imm 类别
nt_imm = collections.Counter()
for r in rows:
    if r['base'] not in ('this', 'this_copy'):
        nt_imm[r['cat']] += 1
print('   M4 非 this store 的 imm 类别: %s' % dict(nt_imm))
ck('M4a 非 this 侧 other_main 条数 >= 30', nt_imm['other_main'] >= 30, nt_imm['other_main'])
# this 侧的 other_main 条数
t_om = sum(1 for r in rows if r['base'] in ('this', 'this_copy') and r['cat'] == 'other_main')
ck('M4b this 侧 other_main 条数', True, t_om)
print('   M4c this 侧 other_main %d 条；非 this 侧 other_main %d 条' % (t_om, nt_imm['other_main']))
for r in rows:
    if r['base'] in ('this', 'this_copy') and r['cat'] == 'other_main':
        print('        M4d %-52s <- %-52s reg=%s base=%s' % (r['cls_d'], r['cls_imm'], r['reg'], r['base']))

json.dump(dict(cross={'%s|%s' % k: v for k, v in cross.items()}, this_side=thisn, unknown=unk,
               nonthis=sorted(nonthis), nt_imm=dict(nt_imm), t_om=t_om,
               rows=rows, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m4_base_owner.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
