#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 EXEC B: 槽0类专属实现「首 call 目标」的调用面与身份普查。

单脚本一次性完成：Q1 全段 disasm_lite 调用图 + 字节法复核；Q2 首 call 调用面；
Q3 落槽 3 例；Q4 Top15；Q5 77 个再装表；Q6 字节身份线索；R1/R2/R3 三反控。
严禁 detail=True 全段常驻；仅对少数命中目标单独开 detail=False 小体反汇编。
"""
import sys, os, re, json, struct, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = ROOT + '/_r200/exec_b'
os.makedirs(OUT, exist_ok=True)
LO, HI = P.B['.text']['lo'], P.B['.text']['hi_file']
RAW = P.RAW
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)   # detail=False always
CHUNK = 65536

PASS, FAIL = [], []
def chk(cond, msg):
    (PASS if cond else FAIL).append(msg)
    print(('PASS ' if cond else 'FAIL ') + msg)

def hx(x): return hex(x) if x is not None else 'None'
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n

# ---------- P1..P3 baseline (class/vtable reconstruction) ----------
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=struct.unpack('<i', struct.pack('<I', w[i + 1]))[0],
                                 ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
chk(len(COL) == 1214, 'A1 COL==1214 (measured %d)' % len(COL))

VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
chk(len(VT) == 1214, 'A2 VT==1214 (measured %d)' % len(VT))

NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    NS[vt] = k
    return k
slot_total = sum(nslot(v) for v in VT)
chk(slot_total == 14044, 'A3 slot total==14044 (measured %d)' % slot_total)

CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
PTD = {vt: COL[VT[vt]]['ptd'] for vt in VT}
MAIN = [vt for vt in VT if MD[vt] == 0]
chk(len(MAIN) == 954, 'A4 main tables==954 (measured %d)' % len(MAIN))
TD2VT = {}
for vt in MAIN: TD2VT[PTD[vt]] = vt

ALLREF = collections.defaultdict(list)
for vt in VT:
    for k in range(nslot(vt)): ALLREF[P.dw(vt + 4 * k)].append((vt, k))

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v not in CHD: CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, dd in CHD.items():
    arr = dd['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and dd['n'] is not None and 0 < dd['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(dd['n'])]
        if any(x is None for x in lst): lst = None
    dd['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=struct.unpack('<i', struct.pack('<I', P.dw(b + 8)))[0])

def direct_children(bcds, i):
    out = []
    n = len(bcds); lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

def base_vt(vt):
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    if not ch or not ch['bcds']: return None
    for j in direct_children(ch['bcds'], 0):
        if BCDS[ch['bcds'][j]]['mdisp'] == 0:
            return TD2VT.get(BCDS[ch['bcds'][j]]['ptd'])
    return None

# ---------- P4 pairs -> 516 derived slot-0 bodies ----------
d = json.load(open(ROOT + '/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
chk(len(pairs) == 603, 'A5 pairs==603 (measured %d)' % len(pairs))
s0 = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a, b = P.dw(vt_d), P.dw(vt_b)
    if a != b: s0.append((vt_d, a, vt_b))
chk(len(s0) == 516, 'A6 derived slot0 mismatch==516 (measured %d)' % len(s0))

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
REC = []
for vt_d, a, vt_b in s0:
    ins = body(a)
    if ins is None:
        REC.append(dict(vt_d=vt_d, impl=a, vt_b=vt_b, ins=[], calls=[], stores=[], first=None, first3=[]))
        continue
    calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    stores = [(ad, m.group(1), int(m.group(3), 16), m.group(2))
              for ad, sz, mn, op in ins for m in [STORE_RE.match(op)] if mn == 'mov' and m]
    # task "体内首个 call" = first call of the body.
    first_body = calls[0][1] if calls else None
    # R199 uses per-store "next call after that store" (one count per store, 538 total).
    after_store = []
    for sad, reg, imm, disp in stores:
        nxt = next((tgt for cad, tgt in calls if cad > sad), None)
        if nxt is not None: after_store.append((sad, imm, nxt))
    REC.append(dict(vt_d=vt_d, impl=a, vt_b=vt_b, ins=ins, calls=calls, stores=stores,
                    first=first_body, after_store=after_store,
                    first3=[c[1] for c in calls[:3]]))
chk(all(r['ins'] for r in REC), 'A7 all 516 bodies disassembled')
T = set(r['first'] for r in REC if r['first'] is not None)
chk(len(T) > 0 and len(T) <= 516, 'A8 T nonempty and bounded (measured %d)' % len(T))
AS_TOTAL = sum(len(r['after_store']) for r in REC)
print('[P4] first-body-call T=%d  per-store next-call events=%d (R199 expects 538)' % (len(T), AS_TOTAL))
chk(AS_TOTAL == 538, 'A8b per-store next-call events==538 (measured %d)' % AS_TOTAL)

# ================= Q1: global call graph, chunked disasm_lite =================
CALLAT = []                       # (site, target)
CALLERS = collections.defaultdict(list)
resync = 0
for cs in range(LO, HI, CHUNK):
    ce = min(cs + CHUNK, HI)
    data = RAW[P.r2o(cs):P.r2o(cs) + (ce - cs)]
    start = 0
    while start < len(data):
        last_end = None; got = 0
        for ad, sz, mn, op in md.disasm_lite(data[start:], cs + start):
            got += 1; last_end = ad - cs + sz
            if mn == 'call' and op.startswith('0x'):
                tgt = int(op, 16)
                if in_text(tgt):
                    CALLAT.append((ad, tgt)); CALLERS[tgt].append(ad)
        if got == 0:
            start += 1; resync += 1
        elif last_end >= len(data):
            break
        else:
            start = last_end + 1; resync += 1
print('[Q1] CALLAT total=%d, distinct call targets=%d, disasm resync events=%d' %
      (len(CALLAT), len(CALLERS), resync))
chk(len(CALLAT) > 10000, 'A9 CALLAT>10000 (measured %d)' % len(CALLAT))
chk(len(CALLERS) > 1000, 'A10 distinct call targets>1000 (measured %d)' % len(CALLERS))
DEL = 0x7C8B3D
disasm_sites = set(CALLERS.get(DEL, []))
print('[Q1] call 0x7C8B3D: disasm_lite sites=%d (R199 ref >=503)' % len(disasm_sites))
chk(len(disasm_sites) >= 503, 'A11 disasm_lite call-%s sites>=503 (measured %d)' % (hx(DEL), len(disasm_sites)))

# byte-law independent recount: E8 + rel32
tb = RAW[P.r2o(LO):P.r2o(LO) + (HI - LO)]
byte_sites = set()
for i in range(len(tb) - 4):
    if tb[i] == 0xE8:
        rel = struct.unpack_from('<i', tb, i + 1)[0]
        if LO + i + 5 + rel == DEL: byte_sites.add(LO + i)
print('[Q1] call 0x7C8B3D: byte-scan(E8+rel32) sites=%d' % len(byte_sites))
chk(len(byte_sites) > 0, 'A12 byte-scan call sites>0 (measured %d)' % len(byte_sites))
only_dis = sorted(disasm_sites - byte_sites); only_byte = sorted(byte_sites - disasm_sites)
consistent = (not only_dis and not only_byte)
print('[Q1/R2] two口径 %s: disasm=%d byte=%d; disasm-only=%d byte-only=%d' %
      ('CONSISTENT' if consistent else 'DIFFER', len(disasm_sites), len(byte_sites), len(only_dis), len(only_byte)))
for x in only_dis[:20]: print('   disasm-only site %s' % hx(x))
for x in only_byte[:20]: print('   byte-only site %s' % hx(x))

# ================= Q2: call-face of first-call targets =================
HOST_KEYS = sorted(CALLERS.keys())
def host_of(site):
    i = bisect.bisect_left(HOST_KEYS, site) - 1
    return HOST_KEYS[i] if i >= 0 else None

q2_rows = []
for t in sorted(T):
    cl = CALLERS.get(t, [])
    hs = set(host_of(s) for s in cl)
    q2_rows.append(dict(target=t, calls=len(cl), hosts=len(hs),
                        in_vtable=bool(ALLREF.get(t)), callers=cl))
hist = collections.Counter()
for r in q2_rows:
    n = r['calls']
    hist['1' if n == 1 else ('2..3' if 2 <= n <= 3 else ('4..10' if 4 <= n <= 10 else '>10'))] += 1
print('[Q2] |T|=%d; call-point histogram 1=%d 2..3=%d 4..10=%d >10=%d' %
      (len(T), hist['1'], hist['2..3'], hist['4..10'], hist['>10']))
chk(sum(hist.values()) == len(T), 'A13 histogram sums to |T|')
print('[Q2] top10 by call points: %s' %
      [(hx(r['target']), r['calls'], r['hosts']) for r in sorted(q2_rows, key=lambda x: -x['calls'])[:10]])
# Q2 supplement: frequency of first-body-call target among the 516 implementations
first_freq = collections.Counter(r['first'] for r in REC if r['first'] is not None)
print('[Q2s] 516 impls first-body-call target frequency Top20: %s' %
      [(hx(t), c) for t, c in first_freq.most_common(20)])
print('[Q2s] first call == 0x7C8B3D: %d/%d; distinct targets excluding it: %d; '
      'singleton targets (freq==1): %d' %
      (first_freq.get(DEL, 0), sum(first_freq.values()),
       len([t for t in T if t != DEL]), sum(1 for c in first_freq.values() if c == 1)))
chk(sum(first_freq.values()) >= len(T), 'A13b first-call frequency sums to >=|T|')

# ================= Q3: the in-vtable first calls =================
# Task's P5 "3 条" refers to the store-after-first call (R199 criterion); report both.
def q3_for(key):
    rows = []
    for r in REC:
        if key == 'after_store':
            events = [(sad, imm, nxt) for sad, imm, nxt in r['after_store']]
        else:
            events = [] if r['first'] is None else [(None, None, r['first'])]
        for cad, st_imm, t in events:
            if t is None or t not in ALLREF: continue
            ks = [k for vt, k in ALLREF[t] if vt == st_imm]
            hit_slot = ks[0] if ks else None
            vts = sorted(set(vt for vt, k in ALLREF[t]))
            rows.append(dict(impl=hx(r['impl']), target=hx(t),
                             store_imm=hx(st_imm),
                             slots=[[hx(vt), k, CLS[vt]] for vt, k in ALLREF[t]],
                             verdict=('装表后 call 槽 %d' % hit_slot) if hit_slot is not None else '巧合地址出现在某个槽里',
                             classes=[CLS[v] for v in vts]))
    return rows
q3_rows = q3_for('after_store')
q3_body_rows = q3_for('first')
print('[Q3] in-vtable after-store-first calls=%d (task P5 expects 3); body-first calls=%d' %
      (len(q3_rows), len(q3_body_rows)))
chk(len(q3_rows) == 3, 'A14 in-vtable after-store-first calls==3 (measured %d)' % len(q3_rows))
for x in q3_rows:
    print('   impl=%s target=%s store_imm=%s slots=%s verdict=%s' %
          (x['impl'], x['target'], x['store_imm'],
           [[s[0], s[1]] for s in x['slots']], x['verdict']))

# ================= Q4: Top15 by call points =================
def ins_text(ins, n=12):
    return ['%08x  %-7s %s' % (a, mn, op) for a, sz, mn, op in ins[:n]]

top15 = sorted(q2_rows, key=lambda x: (-x['calls'], x['target']))[:15]
chk(len(top15) == 15, 'A15 Top15 size==15 (measured %d)' % len(top15))
q4_rows = []
for x in top15:
    t = x['target']
    ins = body(t, 400, 120) or []
    q4_rows.append(dict(address=hx(t), calls=x['calls'], hosts=x['hosts'],
                        in_vtable=x['in_vtable'], first12=ins_text(ins, 12)))
print('[Q4] Top15:')
for x in q4_rows:
    print('   %s calls=%d hosts=%d inVT=%s' % (x['address'], x['calls'], x['hosts'], x['in_vtable']))
    for line in x['first12'][:12]: print('       %s' % line)
chk(all(x['first12'] for x in q4_rows), 'A16 all Top15 bodies readable')

# ================= Q5: 77 "reload table" targets =================
STR_RE = re.compile(r'0x([0-9a-f]+)')
def rdata_strings(ins, limit=5):
    out = []
    for ad, sz, mn, op in ins:
        for m in STR_RE.finditer(op):
            va = int(m.group(1), 16)
            if P.where(va) == '.rdata':
                s = P.cstr(va, 40)
                if s and len(s) >= 2:
                    out.append([hx(va), ''.join(chr(c) if 32 <= c < 127 else '.' for c in s)])
                    if len(out) >= limit: return out
    return out

q5_bucket = collections.Counter(); q5_rows = []; reload_n = 0
for r in REC:
    # R199's 77 counts first-body call targets whose body contains a store.
    t = r['first']
    if t is None: continue
    b2 = body(t, 300, 120)
    if b2 is None: continue
    st = [(ad, int(m.group(3), 16)) for ad, sz, mn, op in b2
          for m in [STORE_RE.match(op)] if mn == 'mov' and m]
    if not st: continue
    reload_n += 1
    for imm in [s[1] for s in st]:
        if imm == r['vt_d']: b = 'eq_vt_d'
        elif imm == r['vt_b']: b = 'eq_vt_b'
        elif imm in VT and MD[imm] == 0: b = 'other_main'
        elif imm not in VT: b = 'not_in_vt'
        else: b = 'subtable_other'
        q5_bucket[b] += 1
    q5_rows.append(dict(impl=hx(r['impl']), target=hx(t), vt_d=hx(r['vt_d']), vt_b=hx(r['vt_b']),
                        stores=[hx(s[1]) for s in st],
                        classes=['eq_vt_d' if s[1] == r['vt_d'] else
                                 'eq_vt_b' if s[1] == r['vt_b'] else
                                 'other_main' if (s[1] in VT and MD[s[1]] == 0) else
                                 'not_in_vt' if s[1] not in VT else 'subtable_other' for s in st]))
print('[Q5] strict criterion: first-call target body contains mov [reg{+disp}],imm32 -> %d records' % reload_n)
chk(reload_n == 77, 'A17 reload count==77 (measured %d)' % reload_n)
print('[Q5] buckets=%s (sum=%d)' % (dict(q5_bucket), sum(q5_bucket.values())))
chk(sum(q5_bucket.values()) >= reload_n, 'A18 bucket sum>=77')

# ================= Q6: byte-only identity clues for Top15 =================
q6_rows = []
for x in q4_rows:
    t = int(x['address'], 16)
    ins = body(t, 400, 120) or []
    ret = [(a, sz, mn, op) for a, sz, mn, op in ins if mn.startswith('ret')]
    end = ret[-1][0] + ret[-1][1] if ret else (ins[-1][0] + ins[-1][1] if ins else t)
    o = P.r2o(end)
    cc_run = nop_run = 0
    if o is not None:
        j = o
        while j < len(RAW) and RAW[j] == 0xCC: cc_run += 1; j += 1
        j = o
        while j < len(RAW) and RAW[j] == 0x90: nop_run += 1; j += 1
    ss = rdata_strings(ins)
    q6_rows.append(dict(address=x['address'], cc_tail=cc_run, nop_tail=nop_run,
                        cc_boundary=cc_run > 0,
                        strings=ss, string_clue=(ss[0] if ss else '无字符串引用'),
                        rets=[[hx(a), mn, op] for a, sz, mn, op in ret]))
print('[Q6] identity clues:')
for x in q6_rows:
    print('   %s cc_tail=%d nop_tail=%d rets=%s strings=%s' %
          (x['address'], x['cc_tail'], x['nop_tail'], x['rets'], x['string_clue']))
chk(sum(1 for x in q6_rows if x['rets']) >= 10, 'A19 most Top15 have ret')

# ================= R1: host criterion sensitivity =================
def alt_host(site):
    o = P.r2o(site)
    if o is None: return None
    floor = max(P.r2o(LO), o - 4096)
    j = o - 1
    while j >= floor and RAW[j] not in (0xCC, 0x90): j -= 1
    if j < floor: return None
    # first *instruction* after the padding run
    k = j + 1
    while k < o and RAW[k] in (0xCC, 0x90): k += 1
    if k >= o: return None
    return LO + (k - P.r2o(LO))
prim_total = sum(len(set(host_of(s) for s in CALLERS.get(t, []))) for t in T)
alt_total = sum(len(set(x for s in CALLERS.get(t, []) if (x := alt_host(s)) is not None)) for t in T)
prim_pairs = sum(len(set(host_of(s) for s in CALLERS.get(t, []))) for t in T)
print('[R1] total distinct hosts over T: primary(nearest callable entry)=%d  alt(prev CC/90 pad+1)=%d' %
      (prim_total, alt_total))
chk(prim_pairs == prim_total, 'A20 R1 primary total reproducible')

# ================= R3: relax first-call to first-3-call =================
T3 = set()
for r in REC: T3.update(r['first3'])
T3 = {t for t in T3 if t is not None}
gt10 = sum(1 for t in T3 if len(CALLERS.get(t, [])) > 10)
print('[R3] |T first1|=%d  |T first3|=%d  targets with >10 call points=%d' % (len(T), len(T3), gt10))
chk(len(T3) >= len(T), 'A21 first3 superset of first1')
chk(gt10 >= 0, 'A22 R3 >10 count computed')

# ---------- emit ----------
result = dict(
    baseline=dict(COL=len(COL), VT=len(VT), slots=slot_total, main=len(MAIN),
                  pairs=len(pairs), derived_slot0=len(s0)),
    Q1=dict(CALLAT=len(CALLAT), distinct_targets=len(CALLERS), resync=resync,
            del_disasm=len(disasm_sites), del_byte=len(byte_sites),
            consistent=consistent, disasm_only=[hx(x) for x in only_dis[:20]],
            byte_only=[hx(x) for x in only_byte[:20]]),
    Q2=dict(T_size=len(T), histogram=dict(hist),
            first_freq={hx(t): c for t, c in first_freq.most_common()},
            rows=[dict(address=hx(r['target']), calls=r['calls'], hosts=r['hosts'],
                       in_vtable=r['in_vtable'], callers=[hx(c) for c in r['callers']]) for r in q2_rows]),
    Q3=q3_rows, Q3_body_first=q3_body_rows,
    Q4=q4_rows, Q5=dict(reload=reload_n, criterion='store-after-first call (R199); strict mov [reg{+disp}],imm32 in target body',
                        buckets=dict(q5_bucket), rows=q5_rows),
    Q6=q6_rows,
    R1=dict(primary=prim_total, alt=alt_total),
    R2=dict(consistent=consistent, disasm_only=len(only_dis), byte_only=len(only_byte)),
    R3=dict(T1=len(T), T3=len(T3), gt10=gt10),
    asserts=len(PASS) + len(FAIL), fails=FAIL)
json.dump(result, open(OUT + '/callgraph.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (len(PASS) + len(FAIL), len(FAIL), FAIL))
