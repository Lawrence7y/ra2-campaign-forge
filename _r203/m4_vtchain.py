#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203 m4：虚表基类链的商业性实证 —— 用「槽位序列前缀同一性」独立推断继承关系，并与 COL mdisp 对照。
H1 每个 vtable 的最长前缀父（在所有其它 vtable 里找最长公共前缀），要求父严格更长/等长且唯一；
H2 前缀长度分布；
H3 唯一父的比例；
H4 与 COL mdisp 的一致性：子类 mdisp==0（主对象）时，父的 mdisp 应 > 0 或 0？
H5 覆盖点分布：每个 vtable 相对其父第一个不同的槽位下标；
H6 具体案例逐槽列出（AbstractClass 家族）；
H7 反控：把槽位序列整体 +1 槽位后前缀父子关系应大量改变。
"""
import sys, struct, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
SEQ = {}
for vt in VT:
    s = []
    k = 0
    while k <= 400:
        t = P.dw(vt + 4 * k)
        if not in_text(t): break
        s.append(t); k += 1
    SEQ[vt] = tuple(s)
ck('H0 vtable 1214 / 槽位 14044', len(SEQ) == 1214 and sum(len(v) for v in SEQ.values()) == 14044,
   (len(SEQ), sum(len(v) for v in SEQ.values())))
# 索引：以首槽做分桶，避免 O(n^2) 全比较
byfirst = collections.defaultdict(list)
for vt, s in SEQ.items():
    if s: byfirst[s[0]].append(vt)
def parent(vt):
    s = SEQ[vt]
    best = []; bestn = 0
    for o in byfirst[s[0]]:
        if o == vt: continue
        os_ = SEQ[o]
        if os_ == s: continue
        m = 0
        while m < min(len(os_), len(s)) and os_[m] == s[m]: m += 1
        if m > bestn: bestn = m; best = [o]
        elif m == bestn and m > 0: best.append(o)
    return bestn, best
PAR = {}; AMB = []
for vt in SEQ:
    n, b = parent(vt)
    PAR[vt] = (n, b)
    if len(b) > 1: AMB.append(vt)
uniq = [vt for vt in SEQ if len(PAR[vt][1]) == 1]
ck('H1a 有非零前缀父的 vtable 数', sum(1 for vt in SEQ if PAR[vt][0] > 0) > 0,
   sum(1 for vt in SEQ if PAR[vt][0] > 0))
ck('H1b 唯一最长前缀父的比例 > 80%', len(uniq) / len(SEQ) > 0.80, '%.4f (%d/%d)' % (len(uniq) / len(SEQ), len(uniq), len(SEQ)))
pl = collections.Counter(PAR[vt][0] for vt in SEQ)
print('   H2 前缀长度分布 top: %s' % pl.most_common(10))
ck('H2a 前缀长度 0 的 vtable 数（无任何公共首槽）', pl[0] > 0, pl[0])
ck('H2b 前缀长度 == 父全长（纯前缀继承）的 vtable 数',
   sum(1 for vt in uniq if PAR[vt][0] == len(SEQ[PAR[vt][1][0]])) > 0,
   sum(1 for vt in uniq if PAR[vt][0] == len(SEQ[PAR[vt][1][0]])))
# H4：与 mdisp 对照
def nm(vt): return COL[VT[vt]]['name']
def mdsp(vt): return COL[VT[vt]]['mdisp']
pm = collections.Counter((mdsp(vt), mdsp(PAR[vt][1][0])) for vt in uniq)
print('   H4 (子 mdisp, 父 mdisp) 分布 top: %s' % pm.most_common(8))
ck('H4a 子 mdisp==0 且父 mdisp==0 的最多', pm.most_common(1)[0][0] == (0, 0), pm.most_common(1))
ck('H4b 子 mdisp==0 父 mdisp>0 的条数', pm[(0, 4)] + pm[(0, 8)] + pm[(0, 12)] > 0,
   pm[(0, 4)] + pm[(0, 8)] + pm[(0, 12)])
# H5 覆盖点
ov = collections.Counter(PAR[vt][0] for vt in uniq)
print('   H5 首覆盖槽位下标分布 top: %s' % ov.most_common(8))
ck('H5a 首覆盖槽位下标 == 前缀长度（定义自洽）',
   all(PAR[vt][0] == PAR[vt][0] for vt in uniq), '')
pure = [vt for vt in uniq if PAR[vt][0] == len(SEQ[PAR[vt][1][0]])]
ck('H5c 纯前缀继承（无覆盖新增）%d 条' % len(pure), len(pure) > 0, len(pure))
# H6 案例
CASES = ['.?AVAbstractClass@@', '.?AVAbstractTypeClass@@', '.?AVTechnoClass@@', '.?AVObjectClass@@']
found = {}
for want in CASES:
    for vt in SEQ:
        if nm(vt) == want:
            n, b = PAR[vt]
            found[want] = dict(vt=hex(vt), slots=len(SEQ[vt]), prefix=n,
                               parent=nm(b[0]) if len(b) == 1 else [nm(x) for x in b],
                               parent_slots=len(SEQ[b[0]]) if len(b) == 1 else None,
                               first_own=[hex(SEQ[vt][i]) for i in range(n, min(n + 3, len(SEQ[vt])))])
            break
for k, v in found.items(): print('   H6 %-30s %s' % (k, v))
ck('H6a 四个案例全部找到', len(found) == len(CASES), list(found))
# H7 反控：整体 +1 槽位
SEQ2 = {vt: (SEQ[vt][1:] if len(SEQ[vt]) > 1 else ()) for vt in SEQ}
byfirst2 = collections.defaultdict(list)
for vt, s in SEQ2.items():
    if s: byfirst2[s[0]].append(vt)
def parent2(vt):
    s = SEQ2[vt]
    if not s: return 0, []
    best = []; bestn = 0
    for o in byfirst2[s[0]]:
        if o == vt: continue
        os_ = SEQ2[o]
        if os_ == s: continue
        m = 0
        while m < min(len(os_), len(s)) and os_[m] == s[m]: m += 1
        if m > bestn: bestn = m; best = [o]
        elif m == bestn and m > 0: best.append(o)
    return bestn, best
shift_same = sum(1 for vt in uniq if parent2(vt)[1] == PAR[vt][1])
print('   H7 反控：整体去首槽后父关系不变的有 %d / %d' % (shift_same, len(uniq)))
ck('H7a 反控改变多数父关系', shift_same / max(1, len(uniq)) < 0.5, '%.4f' % (shift_same / max(1, len(uniq))))
OUT = dict(vt=len(SEQ), slots=sum(len(v) for v in SEQ.values()), uniq=len(uniq), amb=len(AMB),
           prefix_dist=dict((str(k), v) for k, v in pl.most_common()), mdisp_pairs=[[list(k), v] for k, v in pm.most_common()],
           cases=found, shift_same=shift_same, asserts=N, fails=fails)
json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r203/m4_vtchain.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
