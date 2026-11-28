#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R214-EX2 · 多继承 adjustor 布局全表 + HouseClass 两处例外成因。

口径与 R213 完全一致：
  COL  : .rdata/.data 内 word 序列 w[k..k+4]，w[k]∈(0,1,2), w[k+2]==0,
         where(w[k+3])=='.data', where(w[k+4])=='.rdata',
         cstr(w[k+3]+8) 以 .?A 开头、@@ 结尾；COL 地址=段基址+4*k,
         mdisp=s32(w[k+1]), 名字=TD+8 内联名去掉首个点。
  前驱  : word==COL 地址且下一 word∈.text；vftable 起点=位点+4；slot i=起点+4*i。
  ADJUSTOR: 槽值 A 处 <=16B 小窗口解码，形如
         (sub dword ptr [esp+4], imm) ; (jmp rel32 / jmp imm)。
禁整段 .text detail=True；capstone 每次 <=16 字节、<=8 条。
"""
import sys, os, struct, json, re, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

MD = Cs(CS_ARCH_X86, CS_MODE_32)          # detail=False, 小窗口专用
OUTTXT = ROOT + '/_r214/ex2_out.txt'
OUTJSON = ROOT + '/_r214/ex2.json'
NA = 0
FAILS = []


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]


def hx(v):
    return '0x%08x' % v


def ck(name, cond, detail=''):
    global NA
    NA += 1
    if not cond:
        FAILS.append(name)
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''))


def ins(a, n=4, maxb=16):
    """<=16 字节、<=8 条、detail=False 的小窗口解码。
    返回 [(addr, mnemonic, op_str, bytes_hex)]"""
    o = P.r2o(a)
    if o is None:
        return []
    out = []
    for i in MD.disasm(P.RAW[o:o + maxb], a):
        out.append((i.address, i.mnemonic, i.op_str, i.bytes.hex()))
        if len(out) >= n:
            break
    return out


def fmtq(q):
    return ' ; '.join('%s %s' % (m, o) for _, m, o, _ in q)


def adjustor(a):
    """判据：sub dword ptr [esp+4], imm ; jmp <立即数绝对地址>。"""
    q = ins(a, 4, 16)
    if len(q) < 2:
        return {'ok': False}
    m1, o1, b1 = q[0][1], q[0][2], q[0][3]
    m2, o2, b2 = q[1][1], q[1][2], q[1][3]
    if not (m1 == 'sub' and 'esp + 4' in o1 and m2 == 'jmp'):
        return {'ok': False}
    if '[' in o2 or not o2.strip().startswith('0x'):
        return {'ok': False}                      # jmp dword ptr [...] 不算
    try:
        imm = int(o1.split(',')[-1].strip(), 16)
        jt = int(o2.strip().split()[0], 16)
    except Exception:
        return {'ok': False}
    return {'ok': True, 'imm': imm, 'jmp': jt, 'q': q[:2],
            'b1': b1, 'b2': b2, 'l1': len(b1) // 2, 'l2': len(b2) // 2}


NORM = re.compile(r'0x[0-9a-fA-F]+|\b\d+\b')


def normop(op):
    return NORM.sub('IMM', op)


def atmpl(ad):
    (_, m1, o1, b1), (_, m2, o2, b2) = ad['q']
    return '%s %s [%dB] ; %s %s [%dB]' % (
        m1, normop(o1), len(b1) // 2, m2, normop(o2), len(b2) // 2)


# =====================================================================
# 表重建（R213 口径）
# =====================================================================
COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
    for k in range(n - 4):
        if w[k] not in (0, 1, 2) or w[k + 2] != 0:
            continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata':
            continue
        nm = P.cstr(w[k + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        raw = nm.decode('latin1')
        COL[base + 4 * k] = dict(addr=base + 4 * k, sig=w[k], mdisp=s32(w[k + 1]),
                                pTD=w[k + 3], pCHD=w[k + 4],
                                name=raw, cls=raw[1:] if raw.startswith('.') else raw)

pred = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
    for k in range(n - 1):
        if w[k] in COL and P.where(w[k + 1]) == '.text':
            pred[w[k]].append(base + 4 * k)

VT = {c: v[0] + 4 for c, v in pred.items() if len(v) == 1}
SL = {}
for c in COL:
    k = 0
    while c in VT and k < 4096 and P.where(P.dw(VT[c] + 4 * k)) == '.text':
        k += 1
    SL[c] = [P.dw(VT[c] + 4 * i) for i in range(k)] if c in VT else []

MAIN = [c for c in COL if COL[c]['mdisp'] == 0]
SEC = [c for c in COL if COL[c]['mdisp'] != 0]
NCHD = len({v['pCHD'] for v in COL.values()})
main_slots = sum(len(SL[c]) for c in MAIN)
sec_slots = sum(len(SL[c]) for c in SEC)

print('=== SCALE (R213 口径) ===')
print('COL=%d  CHD=%d  前驱位点=%d  vftable=%d  主视图=%d  次视图=%d' % (
    len(COL), NCHD, sum(len(v) for v in pred.values()), len(VT), len(MAIN), len(SEC)))
print('主视图槽=%d  次视图槽=%d  合计=%d' % (main_slots, sec_slots, main_slots + sec_slots))

print('\n=== F1 规模自检（1214 / 954 / 954 / 260 / 12726 / 1318）===')
f1 = [len(COL) == 1214, NCHD == 954, len(MAIN) == 954, len(SEC) == 260,
      main_slots == 12726, sec_slots == 1318,
      len(VT) == 1214 and sum(len(v) for v in pred.values()) == 1214,
      main_slots + sec_slots == 14044]
for nm, ok, det in [
        ('F1-1 COL==1214', f1[0], len(COL)),
        ('F1-2 CHD==954', f1[1], NCHD),
        ('F1-3 主视图==954', f1[2], len(MAIN)),
        ('F1-4 次视图==260', f1[3], len(SEC)),
        ('F1-5 主视图槽==12726', f1[4], main_slots),
        ('F1-6 次视图槽==1318', f1[5], sec_slots),
        ('F1-7 前驱/vftable 一一对应==1214', f1[6],
         '%d/%d' % (len(VT), sum(len(v) for v in pred.values()))),
        ('F1-8 总槽==14044', f1[7], main_slots + sec_slots)]:
    ck(nm, ok, det)

if not all(f1):
    print('\nF1 FAIL：口径不一致，停止后续依赖项。')
    json.dump({'f1': dict(zip([1, 2, 3, 4, 5, 6, 7, 8], f1)),
               'counts': dict(COL=len(COL), CHD=NCHD, MAIN=len(MAIN), SEC=len(SEC),
                              main_slots=main_slots, sec_slots=sec_slots),
               'nassert': NA, 'fails': FAILS},
              open(OUTJSON, 'w'), indent=1, ensure_ascii=False)
    sys.exit(2)

# =====================================================================
# F2 adjustor 全表
# =====================================================================
alladj = []
for c in SEC:
    for i, sv in enumerate(SL[c]):
        ad = adjustor(sv)
        if ad['ok']:
            alladj.append(dict(col=c, cls=COL[c]['cls'], mdisp=COL[c]['mdisp'],
                               idx=i, slotval=sv, slotaddr=VT[c] + 4 * i,
                               imm=ad['imm'], jmp=ad['jmp'],
                               rawbytes=(ad['b1'] + ad['b2']),
                               l1=ad['l1'], l2=ad['l2'],
                               tmpl=atmpl(ad)))

print('\n=== F2 adjustor 全表 ===')
print('  全体 adjustor 槽数 = %d' % len(alladj))
paircnt = collections.Counter((a['idx'], a['imm']) for a in alladj)
print('  按 (idx, imm) 聚合 = %s' % sorted(paircnt.items()))
eq = [a for a in alladj if a['imm'] == a['mdisp']]
bad = [a for a in alladj if a['imm'] != a['mdisp']]
print('  imm==mdisp 通过 = %d ; 例外 = %d' % (len(eq), len(bad)))
for a in bad:
    print('    例外: addr=%s slotval=%s cls=%s mdisp=%d idx=%d imm=%d jmp=%s' % (
        hx(a['slotaddr']), hx(a['slotval']), a['cls'], a['mdisp'],
        a['idx'], a['imm'], hx(a['jmp'])))
ck('F2-1 adjustor 槽总数==305', len(alladj) == 305, len(alladj))
ck('F2-2 imm==mdisp 通过数==303', len(eq) == 303, len(eq))
ck('F2-3 例外数==2', len(bad) == 2, len(bad))
ck('F2-4 例外全为 HouseClass mdisp=40 idx3/idx4 imm=4',
   all(a['cls'] == '?AVHouseClass@@' and a['mdisp'] == 40 and
       a['idx'] in (3, 4) and a['imm'] == 4 for a in bad),
   [(a['cls'], a['idx'], a['imm']) for a in bad])

# =====================================================================
# F3 每类 mdisp 多重集
# =====================================================================
cls2md = collections.defaultdict(list)
for c in COL:
    if COL[c]['mdisp'] != 0:
        cls2md[COL[c]['cls']].append(COL[c]['mdisp'])
cls2adj = collections.Counter(a['cls'] for a in alladj)
rows = [(cl, sorted(v), cls2adj[cl]) for cl, v in cls2md.items()]
rows.sort(key=lambda r: (-len(r[1]), r[0]))
tuples = collections.Counter(tuple(r[1]) for r in rows)

print('\n=== F3 每类 mdisp 多重集（非零记录按类聚合）===')
print('  有非零 mdisp 记录的类数 = %d ; 不同 mdisp 元组数 = %d' % (len(rows), len(tuples)))
for cl, md, na in rows[:20]:
    print('    %-56s mdisp=%-28s adjustor=%d' % (cl, str(md), na))
print('  --- 完整 mdisp 元组分布（去重后计数，全部 %d 组）---' % len(tuples))
for t, n in sorted(tuples.items(), key=lambda x: (-x[1], x[0])):
    print('    %-30s x%d' % (str(t), n))
hcrow = [r for r in rows if r[0] == '?AVHouseClass@@']
print('  HouseClass 行 = %s' % hcrow)
ck('F3-1 HouseClass 存在非零 mdisp 记录', len(hcrow) >= 1, hcrow)
ck('F3-2 HouseClass 的 mdisp 元组含 40',
   any(40 in r[1] for r in hcrow), hcrow)

# =====================================================================
# F4 HouseClass 例外成因
# =====================================================================
HC = sorted([c for c in COL if COL[c]['cls'] == '?AVHouseClass@@'])
print('\n=== F4 HouseClass 例外成因 ===')
print('  HouseClass COL 记录数 = %d' % len(HC))
for c in HC:
    print('    col=%s mdisp=%-4d VT=%s slots=%d pCHD=%s' % (
        hx(c), COL[c]['mdisp'], hx(VT.get(c, 0)), len(SL[c]), hx(COL[c]['pCHD'])))

hc_slots = set()
hc_main_slots = set()
for c in HC:
    tag = 'MAIN' if COL[c]['mdisp'] == 0 else 'SEC mdisp=%d' % COL[c]['mdisp']
    print('  --- %s : %s 全槽表 (%d 槽) ---' % (tag, hx(VT.get(c, 0)), len(SL[c])))
    for i, sv in enumerate(SL[c]):
        ad = adjustor(sv)
        mark = ''
        if ad['ok']:
            mark = '  [ADJ imm=%d jmp=%s]' % (ad['imm'], hx(ad['jmp']))
        q = ins(sv, 3, 16)
        print('    idx=%-2d slotaddr=%s val=%s %-10s %s%s' % (
            i, hx(VT[c] + 4 * i), hx(sv), P.where(sv), fmtq(q), mark))
        hc_slots.add(sv)
        if COL[c]['mdisp'] == 0:
            hc_main_slots.add(sv)

exc = sorted(bad, key=lambda a: a['idx'])
print('  --- 两个例外的原始字节与反汇编 ---')
for a in exc:
    raw = P.RAW[P.r2o(a['slotval']):P.r2o(a['slotval']) + 16]
    print('    idx=%d slotval=%s 16B hex=%s' % (a['idx'], hx(a['slotval']), raw.hex(' ')))
    q = ins(a['slotval'], 4, 16)
    for adr, mn, op, bh in q:
        print('       %s  %-6s %-28s bytes=%s' % (hx(adr), mn, op, bh))
    print('       adjustor 共 %dB（sub %dB + jmp %dB）' %
          (len(a['rawbytes']) // 2, a['l1'], a['l2']))

# 目标三态核验
slot0_imm4 = collections.defaultdict(list)
for c in SEC:
    if SL[c] and adjustor(SL[c][0])['ok'] and adjustor(SL[c][0])['imm'] == 4:
        slot0_imm4[SL[c][0]].append((COL[c]['cls'], COL[c]['mdisp'], hx(c)))
print('  --- jmp_target 三态核验 ---')
for a in exc:
    jt = a['jmp']
    ja = adjustor(jt)
    in_hc = jt in hc_slots
    in_main = jt in hc_main_slots
    eq_slot0 = hx(jt) if jt in slot0_imm4 else None
    views_with_jt = sum(1 for c in SEC if jt in SL[c]) + sum(1 for c in MAIN if jt in SL[c])
    print('    idx=%d jmp=%s : (a)在本类任一视图槽=%s / 在本类主视图槽=%s ; '
          '(b)自身是adjustor=%s (imm=%s jmp=%s) ; (c)与imm=4记录slot0同址=%s (%s) ; '
          '出现在 %d 张视图内' % (
              a['idx'], hx(jt), in_hc, in_main, ja['ok'],
              hx(ja['imm']) if ja['ok'] else '-', hx(ja['jmp']) if ja['ok'] else '-',
              bool(eq_slot0), slot0_imm4.get(jt, [])[:6], views_with_jt))
ck('F4-1 HouseClass 有主视图与 mdisp=40 次视图',
   any(COL[c]['mdisp'] == 0 for c in HC) and any(COL[c]['mdisp'] == 40 for c in HC),
   [(hx(c), COL[c]['mdisp'], len(SL[c])) for c in HC])
sec40 = [c for c in HC if COL[c]['mdisp'] == 40]
ck('F4-2 HouseClass mdisp=40 次视图恰 1 张且 9 槽',
   len(sec40) == 1 and len(SL[sec40[0]]) == 9,
   [(hx(c), len(SL[c])) for c in sec40])
if sec40:
    ad40 = [adjustor(sv) for sv in SL[sec40[0]]]
    ck('F4-3 该次视图 idx0/1/2 的 imm==40（遵式部分）',
       all(ad40[i]['ok'] and ad40[i]['imm'] == 40 for i in (0, 1, 2)),
       [ad40[i].get('imm') for i in (0, 1, 2)])
    ck('F4-4 idx3/idx4 imm==4 且目标为 0x4f6e60/0x4f6950',
       sorted(ad40[i].get('jmp') for i in (3, 4)) == [0x4f6950, 0x4f6e60] and
       all(ad40[i].get('imm') == 4 for i in (3, 4)),
       [(i, ad40[i].get('imm'), hx(ad40[i].get('jmp', 0))) for i in (3, 4)])
# 目标在 HouseClass 七张视图中的精确落点（订正 R213 board「落本类主视图槽」的表述）
target_locs = {}
for a in exc:
    loc = []
    for c in HC:
        for i, sv in enumerate(SL[c]):
            if sv == a['jmp']:
                loc.append(dict(col=hx(c), mdisp=COL[c]['mdisp'], idx=i,
                                slotaddr=hx(VT[c] + 4 * i)))
    target_locs[a['jmp']] = loc
    print('    精确落点: jmp=%s -> HouseClass %s' % (hx(a['jmp']), loc))
ck('F4-5 两目标均落在本类视图槽内 (a)',
   all(a['jmp'] in hc_slots for a in exc), [hx(a['jmp']) for a in exc])
ck('F4-6 订正：两目标不在主视图，而落 mdisp=36 次视图 idx3/idx4',
   all(len(target_locs[a['jmp']]) == 1 and
       target_locs[a['jmp']][0]['mdisp'] == 36 and
       target_locs[a['jmp']][0]['idx'] in (3, 4) for a in exc),
   [target_locs[a['jmp']] for a in exc])
ck('F4-7 imm==4 恰等于 40-36（本视图 mdisp 减目标所属基类偏移）',
   all(a['imm'] == a['mdisp'] - target_locs[a['jmp']][0]['mdisp'] for a in exc),
   [(a['mdisp'], a['imm'], target_locs[a['jmp']][0]['mdisp']) for a in exc])
ck('F4-8 两目标自身非 adjustor，且与任何 imm=4 记录的 slot0 不同址 (b)(c)',
   all(not adjustor(a['jmp'])['ok'] and hx(a['jmp']) not in slot0_imm4
       for a in exc),
   [hx(a['jmp']) for a in exc])
print('  成因说明（订正 R213 board）：mdisp=40 次视图 idx3/idx4 的两条 thunk 只 sub 4，'
      '不是「减自身 mdisp=40」，因为目标 0x4f6e60 / 0x4f6950 并非主视图(mdisp=0)槽，'
      '而是同一 HouseClass 的 mdisp=36 次视图 idx3/idx4 上的**真函数体**。'
      'sub 4 = 40-36，把指向偏移 40 子对象的 this 调整为指向偏移 36 子对象，'
      '再直接 jmp 到已在偏移 36 语境下编译的函数体。'
      '故 R213 board 中「两目标均落在本类主视图槽内」为表述错误；'
      '本轮字节实证为「落 mdisp=36 次视图 idx3/idx4」，且 imm=40-36 严格成立。')

# =====================================================================
# F5 反控三点
# =====================================================================
print('\n=== F5 反控三点 ===')
madj = [(c, i, SL[c][i]) for c in MAIN for i in range(len(SL[c]))
        if adjustor(SL[c][i])['ok']]
print('  ① 954 张主视图内 adjustor 槽 = %d (检查槽数 %d)' % (len(madj), main_slots))
ck('F5-1 主视图内 adjustor 槽==0', len(madj) == 0, len(madj))

tgt_all = collections.Counter(a['jmp'] for a in alladj)
out_text = [hx(t) for t in tgt_all if P.where(t) != '.text']
print('  ② 不同 jmp 目标=%d ; 段分布=%s ; 不在 .text 的=%s' % (
    len(tgt_all), dict(collections.Counter(P.where(t) for t in tgt_all)), out_text))
ck('F5-2 全部 jmp 目标在 .text', len(out_text) == 0, out_text)

bad2 = [(a['cls'], hx(a['slotaddr']), a['mdisp'], a['idx'], a['imm'], hx(a['jmp']))
        for a in bad]
ck('F5-3 imm!=mdisp 反例仅 HouseClass mdisp=40 的 idx3/idx4 两条',
   len(bad2) == 2 and all(x[0] == '?AVHouseClass@@' and x[2] == 40 and x[3] in (3, 4)
                          for x in bad2), bad2)
ck('F5-4 无 adjustor 跳回自身',
   all(a['jmp'] != a['slotval'] for a in alladj), 0)
ck('F5-5 每张次视图 adjustor 数 ∈ {0,3,5}',
   dict(collections.Counter(sum(1 for sv in SL[c] if adjustor(sv)['ok']) for c in SEC)) ==
   {0: 159, 3: 100, 5: 1},
   dict(collections.Counter(sum(1 for sv in SL[c] if adjustor(sv)['ok']) for c in SEC)))

# =====================================================================
# F6 槽型模板 distinct
# =====================================================================
print('\n=== F6 adjustor 槽型模板（去掉立即数后的助记符序列）===')
tmpl_all = collections.Counter(a['tmpl'] for a in alladj)
mnem_only = collections.Counter(';'.join(a['tmpl'].split(' ; ')[i].split()[0]
                                        for i in range(2)) for a in alladj)
afpat = collections.Counter(''.join('A' if adjustor(sv)['ok'] else 'F' for sv in SL[c])
                            for c in SEC if adjustor(SL[c][0])['ok'])
print('  指令模板（去立即数、保留指令字节长度）distinct = %d :' % len(tmpl_all))
for t, n in tmpl_all.most_common():
    print('    %-58s x%d' % (t, n))
print('  纯助记符序列 distinct = %d : %s' % (len(mnem_only), mnem_only.most_common()))
print('  R213 的 7 种口径（次视图 A/F 槽位模板）distinct = %d :' % len(afpat))
for t, n in sorted(afpat.items(), key=lambda x: (-len(x[0]), x[0])):
    print('    %-58s x%d' % (t, n))
ck('F6-1 R213 口径 A/F 槽位模板 7 种', len(afpat) == 7, len(afpat))
ck('F6-2 A/F 模板全部以 AAA 打头', all(t.startswith('AAA') for t in afpat), sorted(afpat))
ck('F6-3 指令模板 distinct 如实上报', len(tmpl_all) >= 1, len(tmpl_all))

# =====================================================================
# JSON
# =====================================================================
hc_detail = []
for c in HC:
    hc_detail.append(dict(col=hx(c), mdisp=COL[c]['mdisp'], vt=hx(VT.get(c, 0)),
                          slots=len(SL[c]), pchd=hx(COL[c]['pCHD']),
                          table=[dict(idx=i, slotaddr=hx(VT[c] + 4 * i), val=hx(sv),
                                      sec=P.where(sv), dis=fmtq(ins(sv, 3, 16)),
                                      adj=(lambda ad: {'imm': ad['imm'], 'jmp': hx(ad['jmp'])}
                                           if ad['ok'] else None)(adjustor(sv)))
                                 for i, sv in enumerate(SL[c])]))
exc_detail = []
for a in exc:
    ja = adjustor(a['jmp'])
    exc_detail.append(dict(idx=a['idx'], slotaddr=hx(a['slotaddr']),
                           slotval=hx(a['slotval']), cls=a['cls'], mdisp=a['mdisp'],
                           imm=a['imm'], jmp=hx(a['jmp']), rawbytes=a['rawbytes'],
                           in_hc_slots=a['jmp'] in hc_slots,
                           in_hc_main_slots=a['jmp'] in hc_main_slots,
                           target_is_adjustor=ja['ok'],
                           target_adj=(lambda: {'imm': ja['imm'], 'jmp': hx(ja['jmp'])}
                                       if ja['ok'] else None)(),
                           eq_imm4_slot0=slot0_imm4.get(a['jmp'], []),
                           target_locations=target_locs.get(a['jmp'], []),
                           views_containing_target=(
                               sum(1 for c in SEC if a['jmp'] in SL[c]) +
                               sum(1 for c in MAIN if a['jmp'] in SL[c]))))

payload = {
    'meta': {'caliber': 'R213 identical', 'window_bytes': 16, 'max_insns': 8,
             'binary': 'ra2bench/gamemd.exe'},
    'F1': dict(COL=len(COL), CHD=NCHD, pred=sum(len(v) for v in pred.values()),
               vt=len(VT), MAIN=len(MAIN), SEC=len(SEC),
               main_slots=main_slots, sec_slots=sec_slots, total_slots=main_slots + sec_slots),
    'F2': dict(total=len(alladj), eq=len(eq), exceptions=len(bad),
               pair_counts=[{'idx': i, 'imm': m, 'n': n} for (i, m), n in sorted(paircnt.items())],
               exception_list=[dict(slotaddr=hx(a['slotaddr']), slotval=hx(a['slotval']),
                                    cls=a['cls'], mdisp=a['mdisp'], idx=a['idx'],
                                    imm=a['imm'], jmp=hx(a['jmp'])) for a in bad],
               adjustors=[dict(cls=a['cls'], mdisp=a['mdisp'], idx=a['idx'],
                               slotaddr=hx(a['slotaddr']), slotval=hx(a['slotval']),
                               imm=a['imm'], jmp=hx(a['jmp']), bytes=a['rawbytes'])
                          for a in alladj]),
    'F3': dict(classes=len(rows),
               top20=[{'cls': cl, 'mdisp': md, 'adjustors': na} for cl, md, na in rows[:20]],
               rows_count=len(rows),
               tuple_distribution=[{'mdisp_tuple': list(t), 'n': n}
                                   for t, n in sorted(tuples.items(), key=lambda x: (-x[1], x[0]))],
               housaclass=[{'cls': cl, 'mdisp': md, 'adjustors': na} for cl, md, na in hcrow]),
    'F4': dict(hc_records=[dict(col=hx(c), mdisp=COL[c]['mdisp'], vt=hx(VT.get(c, 0)),
                                slots=len(SL[c])) for c in HC],
               hc_views=hc_detail, exceptions=exc_detail),
    'F5': dict(main_view_adjustors=len(madj), distinct_jmp_targets=len(tgt_all),
               jmp_targets=[hx(t) for t in sorted(tgt_all)],
               out_of_text=out_text, exception_count=len(bad2)),
    'F6': dict(instruction_templates=[{'tmpl': t, 'n': n} for t, n in tmpl_all.most_common()],
               mnemonic_only=[{'seq': t, 'n': n} for t, n in mnem_only.most_common()],
               af_pattern=[{'pat': t, 'n': n} for t, n in afpat.most_common()]),
    'nassert': NA, 'fails': FAILS,
}
with open(OUTJSON, 'w') as f:
    json.dump(payload, f, indent=1, ensure_ascii=False)

print('\n=== SUMMARY ===')
print('断言 %d 条 ; FAIL %d %s' % (NA, len(FAILS), FAILS))
print('JSON bytes = %d' % os.path.getsize(OUTJSON))
print('OUTPUT %s / %s' % (OUTTXT, OUTJSON))
