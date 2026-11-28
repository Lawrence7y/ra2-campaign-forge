#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第九刀：两个订正性补充。

S1 【C1 的定量解释】证明「正则漏十进制位移」是**真 bug 但本样本零影响**：
    对全 .text 用宽松解析器扫所有 mov dword ptr [reg(+disp)], imm32，
    统计位移落在 1..9（旧正则漏掉）的条数，以及 imm 落在 .rdata/.data（=装表）的条数。
    若后者为 0，则 516 个实现体内的 538 条装表 store 里本就不存在 1..9 位移，
    旧正则的漏检风险是**潜在的**而不是已发生的。
S2 【复现 R199 的 535/538】R199 的口径是「每条 store 之后首个 call」（按 store 计 538 次），
    本刀按同一口径重算，得 in_vtable / direct_only 两数，与 R199 的 3 / 535 对照。
    同时给「按实现计」的 9 / 501（m8 口径）以说明两个口径的分母不同。
S3 538 条 store 里 imm 落 .text 虚表（=装表）的条数、imm 落非虚表内存的条数。
反控：
 R1 把 S1 的位移判据改成 1..15，看漏检风险面有多大。
 R2 S2 的「首个 call」若放宽到「store 后前 3 个 call 任一」，in_vtable 记录数变化。
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
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW; ELO = T['rawptr']
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

# ---------- S1 全段字节级扫 C7 /0（mov r/m32, imm32） ----------
# C7 /0 modrm: 基址 reg + disp8/disp32。mod=01（disp8）时位移 1..127 用 1 字节有符号。
small = collections.Counter(); small_vt = collections.Counter(); tot = 0; tot_vt = 0
pos = ELO
end = T['rawptr'] + T['rawsize']
while pos < end - 6:
    b = RAW[pos]
    if b != 0xC7: pos += 1; continue
    modrm = RAW[pos + 1]
    mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or rm == 5 and mod == 0: pos += 1; continue
    if mod == 1:
        disp = struct.unpack_from('<b', RAW, pos + 2)[0]
        if 1 <= disp <= 9:
            imm = struct.unpack_from('<I', RAW, pos + 3)[0]
            small[disp] += 1
            if P.where(imm) in ('.rdata', '.data'):
                small_vt[disp] += 1; small_vt['imm'] += 1
        pos += 7
    elif mod == 2:
        disp = struct.unpack_from('<i', RAW, pos + 2)[0]
        imm = struct.unpack_from('<I', RAW, pos + 6)[0]
        tot += 1
        if P.where(imm) in ('.rdata', '.data'): tot_vt += 1
        pos += 10
    else:
        pos += 1
small_total = sum(v for k, v in small.items() if isinstance(k, int))
print('   S1 全 .text 中 C7 /0 disp8 ∈ 1..9 的指令数 %d（旧正则会全部漏掉）' % small_total)
print('   S1 其中 imm 落 .rdata/.data（=装表）的条数 %s' % small_vt.get('imm', 0))
print('   S1 对照：disp32 形式的 C7 /0 共 %d 条，其中 imm 落 .rdata/.data %d 条' % (tot, tot_vt))
ck('S1a 全段存在 disp8 ∈ 1..9 的 C7 /0 指令（证明正则确有漏检面）', small_total > 0, small_total)
ck('S1b 但其中 imm 落 .rdata/.data 的为 0（本样本无「小位移装表」）', small_vt.get('imm', 0) == 0, small_vt.get('imm', 0))
# R1 放宽到 1..15 需 mod==1 的 disp8 上限 127
print('   R1 disp8 分布（1..20）: %s' % sorted((k, v) for k, v in small.items() if isinstance(k, int) and k <= 20))

# ---------- S2 复现 R199 的按 store 计 ----------
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
def parse_store(op):
    m = STORE_RE.match(op)
    if not m: return None
    val = m.group(3); off = 0
    if val is not None:
        off = int(val, 16) if val.startswith('0x') else int(val)
        if m.group(2) == '-': off = -off
    return m.group(1), off, int(m.group(4), 16)
def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))
per_store = collections.Counter(); per_impl = collections.Counter()
nstore = 0; rec3 = 0
for vt_d, a, vt_b in s0d:
    ins = body(a) or []
    stores = []
    for idx, (ad, sz, mn, op) in enumerate(ins):
        if mn != 'mov': continue
        ps = parse_store(op)
        if ps is None: continue
        stores.append((idx, ps[2]))
    for idx, imm in stores:
        nstore += 1
        nxt = None
        for j in range(idx + 1, len(ins)):
            if ins[j][2] == 'call' and ins[j][3].startswith('0x'):
                nxt = int(ins[j][3], 16); break
        if nxt is None: per_store['none'] += 1
        elif nxt in ALLREF: per_store['in_vtable'] += 1
        else: per_store['direct_only'] += 1
        # R2 前 3 个 call
        cs = [int(ins[j][3], 16) for j in range(idx + 1, len(ins))
              if ins[j][2] == 'call' and ins[j][3].startswith('0x')][:3]
        if any(t in ALLREF for t in cs): rec3 += 1
    cs0 = [int(op, 16) for _, _, mn, op in ins if mn == 'call' and op.startswith('0x')]
    if not cs0: per_impl['nocall'] += 1
    elif cs0[0] in ALLREF: per_impl['in_vtable'] += 1
    else: per_impl['direct_only'] += 1
print('   S2 按 store 计（分母 %d）: %s' % (nstore, dict(per_store)))
print('   S2 按实现计（分母 516）: %s' % dict(per_impl))
ck('S2a store 总数 538', nstore == 538, nstore)
ck('S2b 按 store 计 in_vtable == 3（R199 值）', per_store['in_vtable'] == 3, per_store['in_vtable'])
ck('S2c 按 store 计 direct_only == 535（R199 值）', per_store['direct_only'] == 535, per_store['direct_only'])
ck('S2d 按实现计 in_vtable == 9（m8 值）', per_impl['in_vtable'] == 9, per_impl['in_vtable'])
ck('R2a 前 3 个 call 任一在虚表内的 store 记录数', True, rec3)

# ---------- S3 ----------
s3 = collections.Counter()
for vt_d, a, vt_b in s0d:
    for idx, (ad, sz, mn, op) in enumerate(body(a) or []):
        if mn != 'mov': continue
        ps = parse_store(op)
        if ps is None: continue
        imm = ps[2]
        s3['vt' if imm in VT else ('text' if in_text(imm) else 'else')] += 1
ck('S3a 538 条 store 的 imm 段归属', True, dict(s3))

json.dump(dict(disp8_small=small_total, disp8_small_vt=small_vt.get('imm', 0), disp32=tot, disp32_vt=tot_vt,
               per_store=dict(per_store), per_impl=dict(per_impl), rec3=rec3, s3=dict(s3),
               dispdist={str(k): v for k, v in small.items() if isinstance(k, int)},
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m9_supp.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
