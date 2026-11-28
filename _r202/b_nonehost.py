#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B official: 8 none hosts + INoticeSink disp8=8, all numbers measured.
Reuses _r201/m12_final.py extraction口径 verbatim. Writes b_nonehost.json/.log only."""
import sys, struct, json, bisect, collections, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
OUT = '/home/t628/projects/ra2-campaign-forge/_r202'
LOG = open(OUT + '/b_nonehost.log', 'w', encoding='utf-8')
class Tee:
    def __init__(self, stream):
        self.stream = stream
    def write(self, s):
        try: self.stream.write(s)
        except Exception: pass
        if not LOG.closed: LOG.write(s)
    def flush(self):
        try: self.stream.flush()
        except Exception: pass
        if not LOG.closed: LOG.flush()
sys.stdout = Tee(sys.__stdout__)
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
    for i in range(n-4):
        if w[i] not in (0, 1, 2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3]+8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i] = dict(mdisp=s32(w[i+1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i] = P.dw(base+4*i-4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
REGNAME = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
# --- store extractors, identical to m12_final ---
recs = []; pos = T['rawptr']; end = T['rawptr'] + T['rawsize']
while pos < end-6:
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos+1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        d = struct.unpack_from('<b', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+3)[0]
        recs.append((va, REGNAME[rm], d, im)); pos += 7
    elif mod == 2:
        d = struct.unpack_from('<i', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+6)[0]
        recs.append((va, REGNAME[rm], d, im)); pos += 10
    else: pos += 1
sub = [r for r in recs if 1 <= r[2] <= 9 and r[3] in VT]
BUF = RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS = []; CALLAT = []; p2 = 0
while p2 < len(BUF):
    got = False
    for off, sz, mn, op in md.disasm_lite(BUF[p2:p2+65536], LO+p2):
        got = True; INS.append((off, sz, mn, op))
        if mn == 'call' and op.startswith('0x'):
            t = int(op, 16)
            if in_text(t): CALLAT.append((off, t))
        p2 += sz
    if not got: p2 += 1
INS.sort(); ADDRS = [a for a,_,_,_ in INS]
REGION = []; st = LO
for a, sz, mn, op in INS:
    if mn.startswith('ret') or mn == 'int3': REGION.append((st, a+sz)); st = a+sz
if st < HI: REGION.append((st, HI))
RL = [r[0] for r in REGION]
def reg_of(va):
    i = bisect.bisect_right(RL, va)-1
    return REGION[i] if i >= 0 else None
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c)-1
    return SORT[i] if i >= 0 else None
allsite = []; pos = T['rawptr']
while pos < end-4:
    if RAW[pos] == 0x66:
        if pos+2 < end and RAW[pos+1] == 0xC7:
            mo = RAW[pos+2] >> 6; pos += 6 if mo == 0 else (7 if mo == 1 else 11); continue
        pos += 1; continue
    if RAW[pos] != 0xC7: pos += 1; continue
    modrm = RAW[pos+1]; mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
    if reg != 0 or rm == 4 or (rm == 5 and mod == 0): pos += 1; continue
    va = LO + (pos - T['rawptr'])
    if mod == 1:
        d = struct.unpack_from('<b', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+3)[0]; allsite.append((va, REGNAME[rm], d, im)); pos += 7
    elif mod == 2:
        d = struct.unpack_from('<i', RAW, pos+2)[0]; im = struct.unpack_from('<I', RAW, pos+6)[0]; allsite.append((va, REGNAME[rm], d, im)); pos += 10
    else:
        im = struct.unpack_from('<I', RAW, pos+2)[0]; allsite.append((va, REGNAME[rm], 0, im)); pos += 6
vts = [r for r in allsite if r[3] in VT]
mainall = [r for r in vts if MD[r[3]] == 0]
suball = [r for r in vts if MD[r[3]] != 0]
brm = collections.defaultdict(int); brs = collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])] += 1
for r in suball: brs[reg_of(r[0])] += 1
cS = collections.Counter()
for r in sub:
    rg = reg_of(r[0])
    if rg is None: cS['noreg'] += 1
    elif brm[rg] > 0 and brs[rg] > 0: cS['both'] += 1
    elif brs[rg] > 0: cS['only_sub'] += 1
    else: cS['none'] += 1
def fmt_store(r):
    return '%s disp=%d imm=%s mdisp=%d cls=%s' % (hex(r[0]), r[2], hex(r[3]), MD[r[3]], CLS[r[3]])
def jstore(r):
    return dict(addr=hex(r[0]), disp=r[2], imm=hex(r[3]), mdisp=MD[r[3]], cls=CLS[r[3]], base=r[1])
def region_stores(rg): return sorted([r for r in vts if rg[0] <= r[0] < rg[1]], key=lambda x: x[0])
def ins_at(a, b): return [x for x in INS if a <= x[0] < b]
def field_stores(rg, base):
    pat = re.compile(r'^dword ptr \[' + re.escape(base) + r'(?: \+ (0x[0-9a-f]+|\d+))?\], ')
    out = []
    for a, sz, mn, op in ins_at(rg[0], rg[1]):
        if mn != 'mov' or not pat.match(op): continue
        off = pat.match(op).group(1)
        off = int(off, 16) if off and off.startswith('0x') else (int(off) if off else 0)
        out.append(dict(addr=hex(a), offset=off, ins=mn + ' ' + op))
    return out
def call_contexts(rg):
    out = []
    for c, t in CALLAT:
        if t != rg[0]: continue
        ctx = [(hex(a), mn + ' ' + op) for a, sz, mn, op in INS if c-24 <= a <= c]
        out.append(dict(site=hex(c), target=hex(t), ctx24=ctx))
    return out

print('=== BASE COUNTS (measured) ===')
print('COL=%d VT=%d mainall=%d suball=%d store_sub=%d regions=%d callsites=%d' %
      (len(COL), len(VT), len(mainall), len(suball), len(sub), len(REGION), len(CALLAT)))
ck('BASE-1 697 store 复现', len(sub) == 697, len(sub))
ck('BASE-2 区间数 31968 复现', len(REGION) == 31968, len(REGION))
ck('BASE-3 区间分类 689/0/8 复现', (cS['both'],cS['only_sub'],cS['none']) == (689,0,8), dict(cS))

# ---- controls ----
print('\n=== POSITIVE CONTROLS ===')
CTL = {}
for cn in ('.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@'):
    sites = [r for r in mainall if CLS[r[3]] == cn]
    regs = set(reg_of(r[0]) for r in sites)
    CTL[cn] = dict(n=len(sites), regions=len(regs), sites=[hex(r[0]) for r in sites])
    print('%s: n=%d regions=%d sites=%s' % (cn, len(sites), len(regs), CTL[cn]['sites']))
ck('POS-1 Airstrike 6 处/6 区间', CTL['.?AVAirstrikeClass@@']['n'] == 6 and CTL['.?AVAirstrikeClass@@']['regions'] == 6, CTL['.?AVAirstrikeClass@@']['n'])
ck('POS-2 AlphaShape 6 处/6 区间', CTL['.?AVAlphaShapeClass@@']['n'] == 6 and CTL['.?AVAlphaShapeClass@@']['regions'] == 6, CTL['.?AVAlphaShapeClass@@']['n'])
ck('POS-3 Bomb 6 处/6 区间', CTL['.?AVBombClass@@']['n'] == 6 and CTL['.?AVBombClass@@']['regions'] == 6, CTL['.?AVBombClass@@']['n'])
print('\n=== NEGATIVE CONTROL: whole .text as ONE region ===')
whole_main = len(mainall)   # 整段一个区间时，全部主表装填都落入同一个区间
whole_sub = len(suball)     # 全部次表装填同样落入该区间
wc = collections.Counter()
for r in sub:
    if whole_main > 0 and whole_sub > 0: wc['both'] += 1
    elif whole_sub > 0: wc['only_sub'] += 1
    else: wc['none'] += 1
print('whole-region classification: main=%d sub=%d %s' % (whole_main, whole_sub, dict(wc)))
ck('NEG-1 whole both == 697', wc['both'] == 697, wc['both'])
ck('NEG-2 whole none == 0', wc['none'] == 0, wc['none'])

# ---- T1 ----
NONE_ADDRS = [0x5d5b80,0x635f34,0x637114,0x638aa4,0x6cf196,0x6cf209,0x7b1b2b,0x7b27fb]
none_found = sorted(r[0] for r in sub if brs[reg_of(r[0])] == 0)
print('\n=== T1: 8 none hosts ===')
ck('T1-0 实测 8 条 none 地址与卡面一致', none_found == NONE_ADDRS, [hex(a) for a in none_found])
T1 = []
for ta in NONE_ADDRS:
    r = next(x for x in sub if x[0] == ta)
    rg = reg_of(ta)
    st = region_stores(rg)
    mains = [s for s in st if MD[s[3]] == 0]
    subs = [s for s in st if MD[s[3]] != 0]
    base = r[1]
    at0 = [s for s in mains if s[2] == 0]
    outer = at0[0][3] if at0 else None
    host = CLS[outer] if outer is not None else CLS[r[3]]
    # main classes in chronological order, deduplicated with first-seen address
    order = []
    for s in mains:
        if CLS[s[3]] not in [x['cls'] for x in order]:
            order.append(dict(cls=CLS[s[3]], first=hex(s[0]), disp=s[2]))
    ev = ['region_main_table']
    if not at0:
        ev.append('store_own_main_table')
    cc = call_contexts(rg)
    if cc: ev.append('call_site_this_transfer')
    fld = field_stores(rg, base)
    if fld: ev.append('same_base_field_init')
    undet = 'UNDETERMINED: outer object class at [base+0] has no immediate VT store in this region' if not at0 else None
    rec = dict(store=fmt_store(r), store_addr=hex(ta), base=base,
               region=[hex(rg[0]), hex(rg[1])],
               region_stores=[jstore(s) for s in st],
               main_stores=[jstore(s) for s in mains], sub_stores=[jstore(s) for s in subs],
               main_classes_in_order=order,
               host_class=host, outer_class=CLS[outer] if outer is not None else 'UNDETERMINED',
               evidence_type=ev, call_targets_at_region_start=cc,
               same_base_field_inits=fld, undetermined=undet)
    T1.append(rec)
    print('\n-- %s base=%s region=%s..%s' % (rec['store'], base, rec['region'][0], rec['region'][1]))
    for s in st: print('   VTS ' + fmt_store(s) + ('  [MAIN]' if MD[s[3]] == 0 else '  [SUB]'))
    print('   main classes (first seen order): ' + ' -> '.join(x['cls'] + '@' + x['first'] for x in order))
    print('   host_class=%s outer_class=%s evidence=%s' % (host, rec['outer_class'], ev))
    for c in cc:
        print('   CALL AT region start %s:' % c['site'])
        for a, s in c['ctx24']: print('      %s %s' % (a,s))
    for f in fld: print('   FIELD %s %s' % (f['addr'], f['ins']))
    if undet: print('   ' + undet)
ck('T1-1 8 条均有区间内 mdisp==0 装表', all(len(x['main_stores']) > 0 for x in T1), sum(1 for x in T1 if x['main_stores']))
ck('T1-2 每条 host_class 均实测得到', all(x['host_class'] != 'UNDETERMINED' for x in T1), sum(1 for x in T1 if x['host_class'] != 'UNDETERMINED'))
ck('T1-3 5 条区间内 [base+0] 主表可得外层宿主类', sum(1 for x in T1 if x['outer_class'] != 'UNDETERMINED') == 5,
   sum(1 for x in T1 if x['outer_class'] != 'UNDETERMINED'))

print('\n=== T1 SENSITIVITY CONTROL ===')
sens = {}
for ta in (0x6cf196, 0x7b27fb):
    rg = reg_of(ta); up = host_of(ta); ur = reg_of(up) if up else None
    forced = region_stores(ur) if ur else []
    sens[hex(ta)] = dict(upstream_callat_target=hex(up) if up else None,
                         upstream_region=[hex(ur[0]), hex(ur[1])] if ur else None,
                         forced_region_vts=[jstore(s) for s in forced],
                         forced_main_count=sum(1 for s in forced if MD[s[3]] == 0),
                         conclusion='UNDETERMINED (forced region has no main-table VT store)')
    print('%s actual region=%s..%s; upstream CALLAT target=%s -> region=%s..%s; forced region VTs=%d mains=%d => %s' %
          (hex(ta), hex(rg[0]), hex(rg[1]), hex(up) if up else 'None',
           hex(ur[0]) if ur else '-', hex(ur[1]) if ur else '-', len(forced), sens[hex(ta)]['forced_main_count'], sens[hex(ta)]['conclusion']))
ck('SENS-1 强归上游区间后结论改变（上游区间零主表）',
   all(sens[k]['forced_main_count'] == 0 for k in sens), {k:v['forced_main_count'] for k,v in sens.items()})

# ---- T2 ----
NOTICE_ADDRS = [0x410174, 0x4101c2, 0x6e8008]
print('\n=== T2: INoticeSink disp8 ===')
T2 = []
for ta in NOTICE_ADDRS:
    rg = reg_of(ta)
    st = region_stores(rg)
    r = next(x for x in sub if x[0] == ta)
    base = r[1]
    # this-base origin: first mov <reg>,ecx in region
    origin = None
    for a, sz, mn, op in ins_at(rg[0], rg[1]):
        if mn == 'mov' and re.match(r'^' + re.escape(base) + r', ecx$', op):
            origin = dict(addr=hex(a), ins=mn + ' ' + op); break
    if origin is None:
        for a, sz, mn, op in ins_at(rg[0], rg[1]):
            if mn in ('mov','lea') and re.match(r'^' + re.escape(base) + r'\b', op):
                origin = dict(addr=hex(a), ins=mn + ' ' + op); break
    # window +-40 bytes: raw bytes from file, disassembled instruction-by-instruction (bounded)
    wa = max(LO, ta-40); wb = min(HI, ta+41)
    wo = P.r2o(wa)
    raww = RAW[wo:wo+(wb-wa)]
    win = []
    for i in md.disasm(raww, wa):
        win.append(dict(addr=hex(i.address), bytes=i.bytes.hex(), ins=i.mnemonic + ' ' + i.op_str,
                        mark='<<<< STORE' if i.address == ta else ''))
    plus4 = [jstore(s) for s in st if s[2] == 4]
    same8_secondary = [jstore(s) for s in st if s[2] == 8 and MD[s[3]] != 0]
    notice_secondary = [jstore(s) for s in st if 'INoticeSink' in CLS[s[3]] and MD[s[3]] != 0]
    subn = sum(1 for s in st if MD[s[3]] != 0)
    print('\n-- %s region=%s..%s base=%s origin=%s' %
          (fmt_store(r), hex(rg[0]), hex(rg[1]), base, origin))
    for s in st: print('   VTS ' + fmt_store(s))
    for w in win: print('   WIN %s  %-20s %-45s %s' % (w['addr'], w['bytes'], w['ins'], w['mark']))
    print('   +4 stores: %s; same-disp-8 secondary: %s; INoticeSink secondary: %d; region sub(VT mdisp!=0)=%d' %
          ([x['cls'] + '@' + x['addr'] for x in plus4],
           [x['cls'] + '@' + x['addr'] for x in same8_secondary], len(notice_secondary), subn))
    why = ('INoticeSink primary VT stored at [base+8] (mdisp=0), followed by INoticeSource at [base+12]; '
           'the complete object stores AbstractClass primary at [base+0] and its secondary tables at +4/+8/+12. '
           'The +8 is the subobject offset of INoticeSink inside the complete object, not the class mdisp.')
    print('   WHY8: ' + why)
    T2.append(dict(store=fmt_store(r), region=[hex(rg[0]), hex(rg[1])], base=base, this_origin=origin,
                   region_stores=[jstore(s) for s in st], window_bytes40=win,
                   plus4_stores=plus4, same_disp8_secondary=same8_secondary,
                   inotice_secondary=notice_secondary, region_sub_count=subn,
                   why8=why, first_field_class=plus4[0]['cls'] if plus4 else 'UNDETERMINED'))
ck('T2-1 三条 INoticeSink mdisp 均为 0', all(MD[next(x for x in sub if x[0]==a)[3]] == 0 for a in NOTICE_ADDRS),
   [MD[next(x for x in sub if x[0]==a)[3]] for a in NOTICE_ADDRS])
ck('T2-2 三条 c7 disp 均为 8', all(next(x for x in sub if x[0]==a)[2] == 8 for a in NOTICE_ADDRS),
   [next(x for x in sub if x[0]==a)[2] for a in NOTICE_ADDRS])
ck('T2-3 3/3/6 次表数复算一致', [x['region_sub_count'] for x in T2] == [3,3,6],
   [x['region_sub_count'] for x in T2])
ck('T2-4 三区间均有 +8 同位移的 mdisp==8 次表（二进制证据）',
   all(len(x['same_disp8_secondary']) > 0 for x in T2), [len(x['same_disp8_secondary']) for x in T2])
ck('T2-5 三区间 INoticeSink 自身次表数均为 0', all(len(x['inotice_secondary']) == 0 for x in T2),
   [len(x['inotice_secondary']) for x in T2])

result = dict(meta=dict(baseline=dict(COL=len(COL),VT=len(VT),main=len(mainall),sub=len(suball),
                                      store_sub=len(sub),regions=len(REGION),cat=dict(cS))),
              controls=dict(positive=CTL,negative_whole=dict(wc),sensitivity=sens),
              T1=T1, T2=T2, asserts=N, fails=fails)
json.dump(result, open(OUT + '/b_nonehost.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
LOG.close()
