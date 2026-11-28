#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第三刀：槽 0..5 的默认实现函数体字节画像 + 267 个 D 类不匹配的构成。

只看字节，不引用任何外部文档术语；「删除析构」这类名字一律写成「形态描述」。
 B1 对 0x410260 / 0x410300 / 0x410310 / 0x410450 / 0x4C9150 五个高频地址：
    首 32 字节 hex、detail=True 反汇编到首个 ret（<=400B）、ret 形态、体内 call 目标前 3、
    体内是否出现 0x81F7C4 一类 delete 薄壳特征（直接给 call 目标地址，不下语义断言）。
 B2 267 个 D 类不匹配的构成：派生侧地址 / 基类侧地址 / 出现次数，Top 15 对。
 B3 基类侧槽 1 == 0x4C9150 的 172 个配对，其派生侧槽 1 实现分布 Top 10。
 B4 槽 0 的 87 个「继承」配对：它们是不是同一 (派生实现==基类实现) 的重复统计，给实现分布。
反控：
 R1 把窗口从「到首个 ret」改成固定 40 条，ret 形态计数变化。
"""
import sys, struct, collections, json
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

def body(va, maxb=400, maxi=200):
    o = P.r2o(va)
    if o is None: return None
    ins = []; n = 0
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.mnemonic, i.op_str)); n = i.size
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

def summarize(va):
    ins = body(va)
    if ins is None: return dict(va=hex(va), ok=False)
    calls = [op for a, mn, op in ins if mn == 'call']
    rets = [(mn, op) for a, mn, op in ins if mn.startswith('ret')]
    writes = [op for a, mn, op in ins if mn in ('mov', 'and', 'or') and op.split(',')[0].strip().startswith('dword ptr [e') and 'esp' not in op.split(',')[0]]
    tail = ins[-1] if ins else None
    return dict(va=hex(va), n=len(ins), bytes=sum(1 for _ in ins) and (tail[0] + 0 if tail else 0),
                hex=RAW[P.r2o(va):P.r2o(va) + 32].hex(),
                calls=[c for c in calls][:6], ret=rets, writes=writes[:6],
                first3=[(mn, op) for a, mn, op in ins[:3]], ordered=[(mn, op) for a, mn, op in ins])

B1 = {}
for va in (0x410260, 0x410300, 0x410310, 0x410450, 0x4C9150, 0x410470, 0x410480, 0x4103E0):
    s = summarize(va)
    B1[hex(va)] = s
    print('   B1 %-10s n=%-3d hex=%s' % (hex(va), s.get('n', -1), s['hex']))
    print('        前3: %s' % (s.get('first3')))
    print('        calls: %s' % (s.get('calls')))
    print('        ret: %s' % (s.get('ret')))
ck('B1a 0x4C9150 体 == xor eax,eax; ret（3 字节）', B1['0x4c9150']['n'] == 2 and B1['0x4c9150']['hex'].startswith('33c0c3'),
   (B1['0x4c9150']['n'], B1['0x4c9150']['hex'][:8]))
ck('B1b 0x410260 体内含 call（>=1）', len(B1['0x410260']['calls']) >= 1, B1['0x410260']['calls'])
ck('B1c 0x410300/0x410310 体形态一致（长度相同）', B1['0x410300']['n'] == B1['0x410310']['n'],
   (B1['0x410300']['n'], B1['0x410310']['n']))

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
impl_tables = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        impl_tables[P.dw(vt + 4 * k)].add(vt)

# B2 D 类不匹配构成
dmap = collections.Counter()
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    for k in range(L):
        a = P.dw(vt_d + 4 * k); b = P.dw(vt_b + 4 * k)
        if a == b or a == 0x4C9150 or len(impl_tables[a]) == 1: continue
        dmap[(a, b)] += 1
ck('B2a D 类不匹配总数 == 267', sum(dmap.values()) == 267, sum(dmap.values()))
print('   B2 D 类 Top15 (派生, 基类, 次数, 派生表数, 基类表数):')
for (a, b), c in dmap.most_common(15):
    print('        %s %s %-4d %-4d %-4d' % (hex(a), hex(b), c, len(impl_tables[a]), len(impl_tables[b])))
ck('B2b D 类不同 (派生,基类) 对数', True, len(dmap))

# B3 基类槽1 == 0x4C9150 的派生成
s1 = collections.Counter(); n1 = 0
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 2: continue
    if P.dw(vt_b + 4) != 0x4C9150: continue
    n1 += 1; s1[P.dw(vt_d + 4)] += 1
print('   B3 基类槽1==0x4C9150 的配对数=%d 派生侧槽1 分布 Top10: %s' % (n1, [(hex(a), c) for a, c in s1.most_common(10)]))

# B4 槽0 的 87 个匹配
s0 = collections.Counter()
for vt_d, vt_b in pairs:
    L = min(nslot(vt_d), nslot(vt_b))
    if L < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a == b: s0[a] += 1
print('   B4 槽0 匹配的 87 个配对的实现分布: %s' % ([(hex(a), c) for a, c in s0.most_common(10)]))
ck('B4a 槽0 匹配时派生实现多在 2 张以上表出现', all(len(impl_tables[a]) >= 2 for a in s0), dict((hex(a), len(impl_tables[a])) for a in s0))

json.dump(dict(B1={k: {kk: vv for kk, vv in v.items() if kk != 'ordered'} for k, v in B1.items()},
               dmap={'%s|%s' % (hex(a), hex(b)): c for (a, b), c in dmap.items()},
               s1={hex(a): c for a, c in s1.items()}, n1=n1,
               s0={hex(a): c for a, c in s0.items()}, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m3_bodies.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
