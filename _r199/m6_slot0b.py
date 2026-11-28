#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第六刀（修订 m5 的判据错误）：槽 0 的 516 个类专属实现的真实形态。

m5 自错：只匹配 [ecx]=imm 形式，漏掉 [esi]/[eax]=imm（this 指针先被搬进 esi）。
本刀改为「任意基址寄存器 」的 mov dword ptr [reg], imm32，并逐条判 imm32 是不是虚表地址。
判据：
 G1 对 516 个派生侧槽 0 实现，提取所有 mov dword ptr [reg{+disp}], imm32 与 mem,reg 之外形态。
 G2 imm32 落在 VT 集合里 => 该 imm 是虚表地址，取其类名与 mdisp。
 G3 三分类：装的是本类（同名）的表 / 别类的表 / 非虚表立即数。
 G4 「本类表」里装的是主表（mdisp==0）还是子表（mdisp!=0）。
 G5 是否存在 operator delete 薄壳 call（0x7C8B3D）：给命中数与失败数。
 G6 反控：基类侧 264 个实现跑同一套判据，比较「装本类表」比例。
 G7 m5 的错误判据（只看 [ecx]）会漏多少：给 5 vs 真值的数。
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], name=nm.decode('latin1'))
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
CLS_OF_VT = {vt: COL[VT[vt]]['name'] for vt in VT}
MDISP_OF_VT = {vt: COL[VT[vt]]['mdisp'] for vt in VT}

def body(va, maxb=400, maxi=200):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
def feat(va):
    ins = body(va)
    if ins is None: return None
    stores = []; calls = []; retform = None
    for a, sz, mn, op in ins:
        if mn.startswith('ret'):
            retform = op if op else 'plain'
        if mn == 'mov':
            m = STORE_RE.match(op)
            if m: stores.append((m.group(1), int(m.group(3), 16), m.group(2)))
        if mn == 'call' and op.startswith('0x'):
            calls.append(int(op, 16))
    return dict(n=len(ins), nbytes=sum(s for _, s, _, _ in ins),
                stores=stores, calls=calls, ret=retform, ins=ins)

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []; s0b = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a))
    s0b.append((vt_b, b))
ck('G0a 516 / 603', (len(s0d), len(s0b)) == (516, 603), (len(s0d), len(s0b)))

FD = {a: feat(a) for a in set(a for _, a in s0d)}
ck('G1a 516 个全部可反汇编且有 ret', all(v and v['ret'] for v in FD.values()),
   sum(1 for v in FD.values() if not v or not v['ret']))

def classify(vt_d, a):
    f = FD[a]
    own = CLS_OF_VT[vt_d]
    k_own = k_other = k_nonvt = 0
    own_mdisp = []
    for reg, imm, disp in f['stores']:
        if imm in CLS_OF_VT:
            if CLS_OF_VT[imm] == own:
                k_own += 1; own_mdisp.append(MDISP_OF_VT[imm])
            else:
                k_other += 1
        else:
            k_nonvt += 1
    return k_own, k_other, k_nonvt, own_mdisp

tot_own = tot_other = tot_nonvt = 0; has_own = 0; owndisp = collections.Counter()
nstore_hist = collections.Counter(); delcall = 0; deleless = []
for vt_d, a in s0d:
    f = FD[a]
    nstore_hist[len(f['stores'])] += 1
    ko, kt, kn, md_ = classify(vt_d, a)
    tot_own += ko; tot_other += kt; tot_nonvt += kn
    if ko: has_own += 1
    for m in md_: owndisp[m] += 1
    if 0x7C8B3D in f['calls']: delcall += 1
    else: deleless.append((CLS_OF_VT[vt_d], hex(a)))
print('   G2 516 个派生槽0: store 条数直方图=%s' % dict(nstore_hist))
print('   G3 装本类表的实现=%d/%d (%.2f%%)；装别类表=%d 条；非虚表立即数=%d 条'
      % (has_own, 516, 100.0 * has_own / 516, tot_other, tot_nonvt))
print('   G4 装的本类表 mdisp 分布=%s' % dict(owndisp))
ck('G3a 装本类表占比 == 100%%', has_own == 516, (has_own, 516))
ck('G4a 装的本类表全是 mdisp!=0 的子表', 0 not in owndisp, dict(owndisp))
print('   G5 体内 call 0x7C8B3D 的实现=%d/516，缺该 call 的=%d 例: %s'
      % (delcall, len(deleless), deleless[:8]))
ck('G5a 含 delete 薄壳 call 占比 > 90%%', delcall / 516.0 > 0.90, round(100 * delcall / 516.0, 2))

# G6 基类侧反控
uniq_b = set(a for _, a in s0b)
FB = {a: feat(a) for a in uniq_b}
b_own = 0; b_hist = collections.Counter(); b_owndisp = collections.Counter()
base_of = {}
for vt_b, b in s0b: base_of.setdefault(b, []).append(vt_b)
for b in uniq_b:
    f = FB[b]; b_hist[len(f['stores'])] += 1
    ok = 0
    for vt_b in base_of[b]:
        own = CLS_OF_VT[vt_b]
        for reg, imm, disp in f['stores']:
            if imm in CLS_OF_VT and CLS_OF_VT[imm] == own:
                ok += 1; b_owndisp[MDISP_OF_VT[imm]] += 1
    if ok: b_own += 1
print('   G6 基类侧槽0 去重=%d: store 直方图=%s，装本类表=%d (%.2f%%)，mdisp 分布=%s'
      % (len(uniq_b), dict(b_hist), b_own, 100.0 * b_own / len(uniq_b), dict(b_owndisp)))
ck('G6a 基类侧装本类表占比同样高（>=90%%）', b_own / float(len(uniq_b)) >= 0.90,
   round(100.0 * b_own / len(uniq_b), 2))

# G7 m5 错误判据漏数
m5_like = sum(1 for vt_d, a in s0d if any(r == 'ecx' for r, i, dp in FD[a]['stores']))
print('   G7 只按 [ecx] 判会得 %d 条（真值 516），漏 %d 条' % (m5_like, 516 - m5_like))
ck('G7a 漏数>0 证明 m5 判据过窄', m5_like < 516, (m5_like, 516))

# G8 基址寄存器分布
regs = collections.Counter()
for vt_d, a in s0d:
    for r, i, dp in FD[a]['stores']: regs[r] += 1
print('   G8 store 基址寄存器分布=%s' % dict(regs))
ck('G8a 基址以 esi 为主', regs.get('esi', 0) >= 0.8 * sum(regs.values()), (regs.get('esi', 0), sum(regs.values())))

# G9 mdisp 值分布（哪一层子表被装）
print('   G9 装的本类表 mdisp Top10=%s' % owndisp.most_common(10))

json.dump(dict(hist=dict(nstore_hist), has_own=has_own, tot_own=tot_own, tot_other=tot_other,
               tot_nonvt=tot_nonvt, owndisp={str(k): v for k, v in owndisp.items()},
               delcall=delcall, deleless=deleless[:30],
               base=dict(uniq=len(uniq_b), hist=dict(b_hist), own=b_own,
                         owndisp={str(k): v for k, v in b_owndisp.items()}),
               m5_like=m5_like, regs=dict(regs), asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m6_slot0b.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
