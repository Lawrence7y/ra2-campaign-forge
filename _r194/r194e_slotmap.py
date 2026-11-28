#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第七刀：L（78 类 AbstractClass 血统）的槽位 → 默认实现全图，并订正 R193 的
「0x410410 是槽 13 的实现」这一口径（实测只在 3/78 张表里成立）。

  T1 基线复算：COL=1214 / 主表 954 / 子表 260 / 槽总 14044 / L=78。
  T2 槽 0..17 的 Top3 实现 + 覆盖张数（L 的 78 张）。
  T3 三个已闭合槽位复算：槽 4 Top1 = 0x410450(77)、槽 0 Top1 = 0x410260(75)。
  T4 槽 13 口径订正：Top1 = 0x5f6250(8/78)，0x410410 只在 3 张表里是该槽目标；
     0x5f6250 体内 call 0x410410（委派关系），因此「0x410410 = AbstractClass 槽 13 实现」
     只在 3 张覆写表的语境里成立。
  T5 0x410410 在全部 1214 张表里的槽号分布（若只出现在槽 13 ⇒ 槽位唯一，但宿主不唯一性说明见 T4）。
  T6 体形态表：每槽 Top1 的 ret 立即数 / setne / 首个字段偏移 / 是否调用其它 Top1。
  反控：N1 补集 876 张主表槽 13 Top1；N2 抽样逐槽打印。
"""
import sys, re, struct, collections, json, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
SUB = [vt for vt in VT if COL[VT[vt]]['mdisp'] != 0]
def chain(colva):
    c = COL[colva]; n = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12); out = []
    for j in range(n):
        b = P.dw(arr + 4 * j)
        if b is None or P.where(b) in ('None', 'other'): continue
        ptd = P.dw(b)
        if ptd is None: continue
        nm = P.cstr(ptd + 8, 160)
        out.append((nm.decode('latin1') if nm else None, P.dw(b + 8)))
    return out
AB = '.?AVAbstractClass@@'
LIN = sorted(vt for vt in MAIN if any(x[0] == AB for x in chain(VT[vt])))
ck('T1 基线复算 COL=1214 主表=954 子表=260 槽总=14044 L=78',
   (len(COL), len(MAIN), len(SUB), sum(NS.values()), len(LIN)) == (1214, 954, 260, 14044, 78),
   (len(COL), len(MAIN), len(SUB), sum(NS.values()), len(LIN)))
print('   L 槽数 min/max = %d/%d' % (min(NS[v] for v in LIN), max(NS[v] for v in LIN)))

table = []
for s in range(0, 18):
    cnt = collections.Counter(P.dw(vt + 4 * s) for vt in LIN if s < NS[vt])
    table.append(dict(slot=s, ncov=sum(cnt.values()), distinct=len(cnt),
                      top=[(hex(a), c) for a, c in cnt.most_common(3)]))
for r in table:
    print('   槽 %2d 覆盖 %2d 张 / 不同实现 %2d  Top3 %s' % (r['slot'], r['ncov'], r['distinct'], r['top']))
ck('T3a 槽 4 Top1 = 0x410450 / 77 张', table[4]['top'][0] == ('0x410450', 77), table[4]['top'][:2])
ck('T3b 槽 0 Top1 = 0x410260 / 75 张', table[0]['top'][0] == ('0x410260', 75), table[0]['top'][:2])
ck('T3c 槽 1 与槽 2 Top1 覆盖同为 74 张（同族默认实现）',
   table[1]['top'][0][1] == 74 and table[2]['top'][0][1] == 74,
   (table[1]['top'][:2], table[2]['top'][:2]))

# T4 槽 13 订正
c13 = collections.Counter(P.dw(vt + 52) for vt in LIN)
s13_410410 = [vt for vt in LIN if P.dw(vt + 52) == 0x410410]
print('   槽 13：不同实现 %d 个；0x410410 宿主 %d 张；Top1=%s'
      % (len(c13), len(s13_410410), c13.most_common(3)))
ck('T4a 槽 13 在 L 上没有单一默认实现：Top1 只覆盖 8/78 张（0x5f6250），不同实现 >= 40 个',
   c13.most_common(1)[0][1] == 8 and len(c13) >= 40, (c13.most_common(2), len(c13)))
ck('T4b 0x410410 只在 3/78 张 L 表的槽 13 上（== 0x7E1F50/0x7E4EEC/0x7F4348，与 R193 PV7 同三张）',
   sorted(s13_410410) == [0x7E1F50, 0x7E4EEC, 0x7F4348], [hex(x) for x in s13_410410])

def walk(va, maxb=1600, maxn=300):
    o = P.r2o(va); ins = []
    for i in md.disasm(P.RAW[o:o + maxb], va):
        ins.append(i)
        if i.mnemonic.startswith('ret') or len(ins) >= maxn: break
    return ins
def form(va):
    ins = walk(va)
    retok = bool(ins) and ins[-1].mnemonic.startswith('ret')
    off = None
    for i in ins:
        m = re.search(r'(byte|word|dword) ptr \[(?:e[a-z]{2}) \+ (0x[0-9a-f]+)\]', i.op_str)
        if m: off = m.group(2); break
    return dict(n=len(ins), ret=(ins[-1].op_str if retok else '-'), retok=retok, first_off=off,
                setne=any(i.mnemonic == 'setne' for i in ins),
                calls=[i.op_str for i in ins if i.mnemonic == 'call'],
                body=' ; '.join('%s %s' % (i.mnemonic, i.op_str) for i in ins),
                hex=P.RAW[P.r2o(va):P.r2o(va) + 16].hex(' ').upper())
TOP = {int(r['top'][0][0], 16) for r in table}
TOP |= {0x410410}
FORMS = {a: form(a) for a in sorted(TOP)}
for r in table:
    a = int(r['top'][0][0], 16); f = FORMS[a]
    print('   槽 %2d %-9s cov=%2d 体=%3d ret=%-4s setne=%-5s off=%-4s 16B=%s calls=%s'
          % (r['slot'], hex(a), r['top'][0][1], f['n'], f['ret'], f['setne'], f['first_off'], f['hex'], f['calls'][:2]))
ck('T6a 所有槽 Top1 都能反汇编到 ret（窗口 1600B / 300 条内）', all(FORMS[int(r["top"][0][0],16)]['retok'] for r in table),
   {hex(k): v['ret'] for k, v in FORMS.items() if not v['retok']})
ck('T6b 0x5f6250（槽 13 Top1）体内直接 call 0x410410 ⇒ 是委派/包装，不是另一套序列化实现',
   any(c == '0x410410' for c in FORMS[0x5f6250]['calls']), FORMS[0x5f6250]['calls'])
ck('T6c 槽 14 Top1 = 0x410490 体为 or eax,-1 ; ret（返回 -1 的默认实现）',
   FORMS[0x410490]['hex'].startswith('83 C8 FF C3'), FORMS[0x410490]['hex'])

# T5 0x410410 全表槽号分布
occ = collections.Counter(); hosts = set()
for vt in VT:
    for s in range(NS[vt]):
        if P.dw(vt + 4 * s) == 0x410410: occ[s] += 1; hosts.add(vt)
print('   0x410410 在 1214 张表中的槽号分布 %s；宿主 %d 张' % (dict(occ), len(hosts)))
ck('T5a 0x410410 只出现在槽 13（槽位唯一）', set(occ) == {13}, dict(occ))
ck('T5b 0x410410 宿主 3 张且都是 L 成员（不是 78 张全用）',
   len(hosts) == 3 and set(hosts) <= set(LIN), (len(hosts), len(hosts & set(LIN))))

# N1 补集
LI = set(LIN)
CMPL = [vt for vt in MAIN if vt not in LI]
c2 = collections.Counter(P.dw(vt + 52) for vt in CMPL if NS[vt] > 13)
print('   补集 876 张里槽 13 存在 %d 张，Top3 %s' % (sum(1 for vt in CMPL if NS[vt] > 13), c2.most_common(3)))
ck('N1 反控：补集槽 13 Top1 不是 0x410410 且与 L 的 Top1(0x5f6250) 也不同族',
   c2.most_common(1)[0][0] not in (0x410410, 0x5F6250), c2.most_common(2))
# N2 抽样
print('   N2 抽样 4 张 L 表逐槽：')
for vt in LIN[:2] + LIN[-2:]:
    print('     %08X %-40s 槽%d %s' % (vt, COL[VT[vt]]['name'], NS[vt],
          ' '.join('%d=%08X' % (s, P.dw(vt + 4 * s)) for s in range(min(NS[vt], 14)))))
json.dump(dict(table=table, forms={hex(k): {kk: vv for kk, vv in v.items()} for k, v in FORMS.items()},
               s13_counter=[(hex(a), c) for a, c in c13.most_common(60)],
               s13_410410=[hex(x) for x in s13_410410],
               occ410410={str(k): v for k, v in occ.items()},
               compl=c2.most_common(10), l_slots=[(hex(v), COL[VT[v]]['name'], NS[v]) for v in LIN]),
          open('/home/t628/projects/ra2-campaign-forge/_r194/r194e_slotmap.json', 'w'), indent=1)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails)); sys.exit(1)
