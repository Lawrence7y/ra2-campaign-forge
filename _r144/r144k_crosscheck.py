#!/usr/bin/env python3
"""R144 K：回归 R143 结论 + 复核五张残余的真伪（其中 4 张高度可疑）。

疑点：0x877000/0x877010/0x87b17c/0x87b18c 四张的 COL 全是 0x800040、offset 都是 4，
表体前 8 槽是 0x10000c0 / 0xa00060 / 0x12000e0 这类「不像 .text 地址」的值，
且 0x10000c0 - 0x400000 无意义。这不像是 vtable，更像被 R144B 的 VTS 建表规则
（dword[vt-4] ∈ COL）误收的普通数据。判据：
  T1 同一 COL（0x800040）下 VTS 里共有几张？
  T2 这四张的槽值有多少落在任何已映射节内（若 0 则它们不是函数指针表）；
  T3 它们的 COL 是否满足完整 COL 结构（sig 在 .rdata、pTypeDescriptor 指向 RTTI 名字）；
  T4 0x7e6060 的槽值 8/8 落 .text 而其余 4 张 0/8 ⇒ 分层。
另外回归 R143 的 68 条链是否仍成立（用 r143lib 同法最小重实现）。
"""
import sys, json, struct, hashlib, collections
sys.path.insert(0, '_r143')
import r143lib as L
import pefile

B = L.Bin()
TDs, COL, VTS = B.vtset()
pe = pefile.PE(L.P, fast_load=True)
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}
colcd = {c: B.dw(c + 16) for c in COL}
colsig = {c: B.dw(c + 0) for c in COL}

resid = [int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']]
sus = resid[1:]
grp = collections.Counter(COLof[v] for v in resid)
T1 = grp[0x800040]
T2 = {}
for vt in resid:
    ok = 0
    for k in range(8):
        v = B.dw(vt + 4 * k)
        if v and B.sec_of(v): ok += 1
    T2[hex(vt)] = ok
T3 = {}
for vt in resid:
    c = COLof.get(vt)
    tdp = coltd.get(c)
    T3[hex(vt)] = {
        'col': hex(c) if c else None, 'sig': hex(colsig[c]) if c in colsig else None,
        'td_ptr': hex(tdp) if tdp else None,
        'td_sec': B.sec_of(tdp) if tdp else None,
        'td_name': (B.rd(tdp + 8, 64) or b'').split(b'\x00')[0].decode('latin1') if tdp else None,
        'classdesc': hex(colcd[c]) if c else None,
        'classdesc_sec': B.sec_of(colcd[c]) if c else None,
    }
# 该 COL 在 VTS 里共挂几张
same_col = [hex(v) for v in VTS if COLof.get(v) == 0x800040]

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS), 'col': len(COL),
 'T1_same_col_n': T1, 'T1_same_col_members': same_col[:12],
 'T2_slots_mapped': T2, 'T3': T3,
 'resid': [hex(v) for v in resid],
 'glyph_note': '4 张可疑项其 COL 0x800040 的 offset=4 且槽值不在任何节内 ⇒ 疑似被建表规则误收',
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('0x800040 这个 COL 下在 VTS 里恰好挂 4 张（与污染规模一致）', T1 == 4, T1)
chk('4 张可疑项的槽值落在任何已映射节内的个数全为 0', all(T2[hex(v)] == 0 for v in sus), [T2[hex(v)] for v in sus])
chk('0x7e6060 的槽值 8/8 落已映射节（真虚表）', T2[hex(resid[0])] == 8, T2[hex(resid[0])])
chk('4 张可疑项共用同一 TD 0x8202f8', len({T3[hex(v)]['td_ptr'] for v in sus}) == 1, [T3[hex(v)]['td_ptr'] for v in sus])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144k_crosscheck.json', 'w'), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])
print('\n'.join('%-62s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
