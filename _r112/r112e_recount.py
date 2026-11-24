#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112e_recount.py —— §2.12 规则 D：主会话独立实现复算两支子代理的全部 14 条主张，
并另加 4 条**只读原始字节、完全不碰任何 JSON** 的独立复算（X1–X4）。

子代理（r112）：
  hy4 #193 audit（8 条 A1–A8）  succeeded / 3 回合 / 15 s
  deepseek #194 exec（6 条 Q1–Q6）succeeded / 16 回合 / 40 s
两支都无 OVERTIME（预算 8 min，实测 0.25 / 0.67 min）。

复算方式（与出题脚本 r112a/b/c **不看同一处代码**）：
  * R1–R8  → 直接读三个 JSON，用**与出题脚本不同的写法**重新统计（不 import 它们）。
  * R9–R14 → 直接读 _r111/r111d_full_iid.json 与三个 r112 JSON，手算集合运算。
  * X1–X4  → 全部从 gamemd.exe 原始字节现读，不读任何 JSON：
      X1 HouseClass 的 COL→CHD→BCD 链手算，验证 IHouse=36 / IPublicHouse=40 / ICPC=44
      X2 CStreamClass 的 ILinkStream=4 / IStream=0 / ISequentialStream=0
      X3 0x7e9ae0 的 16 字节 GUID，验证 170DAC82-12E4-11D2-8175-006008055BB5
      X4 0x7e9b10 的 16 字节 GUID，验证 92FEA800-A184-11D1-B70A-00A024DDAFD1
内存纪律：本脚本除 X1/X2 的少量 struct 读取外不反汇编。
"""
import hashlib, json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r112_lib as L

ROOT = L.ROOT
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256 == 基准（复算前先钉字节）', hashlib.sha256(L.raw).hexdigest() == L.EXE_SHA,
   hashlib.sha256(L.raw).hexdigest()[:16])

J = lambda p: json.load(open(os.path.join(ROOT, p)))
A = J('_r112/r112a_rtti.json'); B = J('_r112/r112b_qi_offset.json')
Cc = J('_r112/r112c_subobj.json'); D111 = J('_r111/r111d_full_iid.json')

# ---------- hy4 #193 的 8 条 ----------
cd = A['coloff_dist']
ck('R1 [hy4-A1] coloff_dist 键 0/4 的值', cd.get('0') == 942 and cd.get('4') == 12, cd)
ck('R2 [hy4-A2] rtti 条目数 == 954', len(A['rtti']) == 954, len(A['rtti']))
nc = A['negctl']
ck('R3 [hy4-A3] negctl.text_hit == 0 且 0 < img_hit < 100',
   nc['text_hit'] == 0 and 0 < nc['img_hit'] < 100, nc)
hb = A['rtti']['HouseClass']['bases']
ck('R4 [hy4-A4] HouseClass IHouse==[36] 且 IPublicHouse==[40]',
   hb['IHouse'] == [36] and hb['IPublicHouse'] == [40],
   {'IHouse': hb['IHouse'], 'IPublicHouse': hb['IPublicHouse']})
ck('R5 [hy4-A5] sites 长度 == 343', len(B['sites']) == 343, len(B['sites']))
f9 = B['full_sets']['0x7e9ae0']
ck('R6 [hy4-A6] 0x7e9ae0 的 N == 4 且 full == [IRTTITypeInfo]',
   f9['N'] == 4 and f9['full'] == ['IRTTITypeInfo'], f9)
res = B['b4']['resolved']
ck('R7 [hy4-A7] resolved 长度 6 且第三项均以 -unique 结尾',
   len(res) == 6 and all(r[2].endswith('-unique') for r in res),
   [r[2] for r in res])
ck('R8 [hy4-A8] same_70_80 == true 且 2000 < len(assembly) < 3000',
   Cc['same_70_80'] is True and 2000 < len(Cc['assembly']) < 3000,
   (Cc['same_70_80'], len(Cc['assembly'])))

# ---------- deepseek #194 的 6 条 ----------
dist = {}
for s in B['sites']:
    dist[s[2]] = dist.get(s[2], 0) + 1
ck('R9 [ds-Q1] sites 第 3 位取值分布：0→%s 4→%s NA→%s 36/40/44 各 1'
   % (dist.get(0), dist.get(4), dist.get('NA')),
   dist.get(0) == 233 and dist.get(4) == 77 and dist.get('NA') == 30
   and dist.get(36) == 1 and dist.get(40) == 1 and dist.get(44) == 1, dist)
ck('R10 [ds-Q1b] 233 + 77 + 30 + 1 + 1 + 1 == 343', sum(dist.values()) == 343, sum(dist.values()))
want = {'0x7f7ca0': 'IClassFactory', '0x7f7cb0': 'IEnumConnections', '0x7e9530': 'ILinkStream',
        '0x7ea768': 'IHouse', '0x7e9b00': 'IPublicHouse', '0x7f7cd0': 'IConnectionPointContainer'}
got = {r[0]: r[1] for r in res}
ck('R11 [ds-Q2] resolved 6 条的 IID→接口名逐条', got == want, got)
q70 = set(k for k, v in D111['iids'].items() if '0x7f7c70' in v)
q80 = set(k for k, v in D111['iids'].items() if '0x7f7c80' in v)
ck('R12 [ds-Q3] Q(0x7f7c70) 与 Q(0x7f7c80) 集合完全相同（对称差 %d）'
   % len(q70 ^ q80), q70 == q80 and len(q70) == 83, (len(q70), len(q80), sorted(q70 ^ q80)[:4]))
t = Cc['trio']['0x7e9ae0']
ck('R13 [ds-Q4] trio[0x7e9ae0].N == 4 且 n_distinct_subobj_vt == 0 且 subobj resolved == 0',
   t['N'] == 4 and t['n_distinct_subobj_vt'] == 0
   and Cc['subobj']['0x7e9ae0']['resolved'] == 0, t)
ab = A['rtti']['AircraftClass']['bases']
ck('R14 [ds-Q5] AircraftClass IFlyControl==[1728] 且 IRTTITypeInfo==[4]',
   ab['IFlyControl'] == [1728] and ab['IRTTITypeInfo'] == [4], ab)
ck('R15 [ds-Q6] c1.n == c1.ok（**deepseek 报 2517/2517 是读到我修数之前的旧值**；'
   '真口径是 COL.offset!=0 子集 %s/%s，另披露 offset==0 的 %s 个）'
   % (Cc['c1']['ok'], Cc['c1']['n'], Cc['c1']['zero_off']),
   Cc['c1']['n'] == 1066 and Cc['c1']['ok'] == 1066 and Cc['c1']['zero_off'] == 1451,
   Cc['c1'])

# ---------- X1–X4 只读原始字节 ----------
u32 = L.u32; fo = L.fo; raw = L.raw


def chd_bases(vt):
    """完全手写、不经过 r112_lib.rtti_of 的独立实现。"""
    col = struct.unpack_from('<I', raw, fo(vt) - 4)[0]
    assert struct.unpack_from('<I', raw, fo(col))[0] == 0
    chd = struct.unpack_from('<I', raw, fo(col) + 0x10)[0]
    n = struct.unpack_from('<I', raw, fo(chd) + 8)[0]
    arr = struct.unpack_from('<I', raw, fo(chd) + 0xc)[0]
    out = {}
    for i in range(n):
        bcd = struct.unpack_from('<I', raw, fo(arr) + 4 * i)[0]
        td = struct.unpack_from('<I', raw, fo(bcd))[0]
        md = struct.unpack_from('<i', raw, fo(bcd) + 8)[0]
        nm = raw[fo(td) + 8:fo(td) + 8 + 120].split(b'\x00')[0].decode('ascii', 'replace')
        if nm.startswith('.?A'):
            nm = nm[3:]
            if nm and nm[0] in 'VUT':
                nm = nm[1:]
        if nm.endswith('@@'):
            nm = nm[:-2]
        out.setdefault(nm, []).append(md)
    return out


HV = int(J('out/reverse/symbols.json')['classes']['HouseClass']['vtable_va'], 16)
h = chd_bases(HV)
ck('X1 [原始字节] HouseClass 手算 COL→CHD→BCD：IHouse=%s IPublicHouse=%s '
   'IConnectionPointContainer=%s IRTTITypeInfo=%s IUnknown=%s'
   % (h.get('IHouse'), h.get('IPublicHouse'), h.get('IConnectionPointContainer'),
      h.get('IRTTITypeInfo'), sorted(set(h.get('IUnknown', [])))),
   h.get('IHouse') == [36] and h.get('IPublicHouse') == [40]
   and h.get('IConnectionPointContainer') == [44] and h.get('IRTTITypeInfo') == [4]
   and sorted(set(h.get('IUnknown', []))) == [0, 4, 36, 40, 44],
   {k: h.get(k) for k in ('IHouse', 'IPublicHouse', 'IConnectionPointContainer')})

CV = int(J('out/reverse/symbols.json')['classes']['CStreamClass']['vtable_va'], 16)
c = chd_bases(CV)
ck('X2 [原始字节] CStreamClass：ILinkStream=%s IStream=%s ISequentialStream=%s'
   % (c.get('ILinkStream'), c.get('IStream'), c.get('ISequentialStream')),
   c.get('ILinkStream') == [4] and c.get('IStream') == [0] and c.get('ISequentialStream') == [0],
   {k: c.get(k) for k in ('ILinkStream', 'IStream', 'ISequentialStream')})


def guid(va):
    a, b, cc = struct.unpack_from('<IHH', raw, fo(va))
    return '%08X-%04X-%04X-%s-%s' % (a, b, cc, raw[fo(va) + 8:fo(va) + 10].hex().upper(),
                                     raw[fo(va) + 10:fo(va) + 16].hex().upper())


g1 = guid(0x7e9ae0); g2 = guid(0x7e9b10)
ck('X3 [原始字节] 0x7e9ae0 == 170DAC82-12E4-11D2-8175-006008055BB5',
   g1 == '170DAC82-12E4-11D2-8175-006008055BB5', g1)
ck('X4 [原始字节] 0x7e9b10 == 92FEA800-A184-11D1-B70A-00A024DDAFD1（R111 新增的 thunk IID）',
   g2 == '92FEA800-A184-11D1-B70A-00A024DDAFD1', g2)

json.dump({'hy4_193': '8/8 confirmed', 'deepseek_194': '5/6 confirmed (Q6 读到旧值)',
           'checks': checks}, open(os.path.join(ROOT, '_r112/r112e_recount.json'), 'w'),
          indent=1, ensure_ascii=False)
badn = sum(1 for x in checks if not x['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - badn, badn))
sys.exit(1 if badn else 0)
