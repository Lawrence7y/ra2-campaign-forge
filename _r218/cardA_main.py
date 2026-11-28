#!/usr/bin/env python3
"""R218-A slot>=256 forensics, streamed. Single script emits all evidence."""
import sys, os, re, random, struct, hashlib
from collections import Counter, defaultdict

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM, CS_OP_IMM, CS_OP_REG
from capstone.x86 import X86_REG_EAX, X86_REG_ECX, X86_REG_EDX, X86_REG_EBX, X86_REG_ESP, X86_REG_EBP, X86_REG_ESI, X86_REG_EDI

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUTDIR = os.path.join(ROOT, '_r218')
os.makedirs(OUTDIR, exist_ok=True)

TEXT_LO = P.B['.text']['lo']
TEXT_HI = P.B['.text']['hi_virt']
RDATA_LO = P.B['.rdata']['lo']
RDATA_HI = P.B['.rdata']['hi_virt']
RAW = P.RAW

def dw(va):
    return P.dw(va)

def in_text(va):
    return TEXT_LO <= va < TEXT_HI

def in_rdata(va):
    return RDATA_LO <= va < RDATA_HI

def cstr(va, n=200):
    s = P.cstr(va, n)
    return s if s is not None else b''

def tdname(pTD):
    if va is None:
        return '-'
    off = P.r2o(va)
    if off is None or off + 8 > len(RAW):
        return '?'
    return RAW[off:off+8].hex()

def tdname(pTD):
    try:
        s = cstr(pTD + 8, 200)
        if s.startswith('.?AV'):
            return s[4:].split('@@')[0]
        return s
    except Exception:
        return '?'

# ---------- vtable discovery ----------
def collect_vtables(allow_rdata=False):
    # A vtable root V-4 holds a COL.  Observed COLs have signature 0 and a
    # CHD (pCHD, +0x10) whose own signature is also 0.  These two conditions
    # reproduce the main session's 1218 tables / 14044 slots exactly.
    roots = []
    for va in range(RDATA_LO, RDATA_HI, 4):
        col = dw(va)
        if col == 0 or not (RDATA_LO <= col < RDATA_HI):
            continue
        off = P.r2o(col)
        if off is None or off + 24 > len(RAW):
            continue
        sig, mdisp, pcd, ptd, pchd, selfva = struct.unpack_from('<IIIIII', RAW, off)
        if sig != 0:
            continue
        cho = P.r2o(pchd)
        if cho is None or cho + 16 > len(RAW):
            continue
        if struct.unpack_from('<I', RAW, cho)[0] != 0:
            continue
        roots.append((va, col, ptd, pchd))
    vtables = {}
    for root, col, ptd, pchd in roots:
        V = root + 4
        slots = []
        a = V
        while True:
            tgt = dw(a)
            if in_text(tgt) or (allow_rdata and in_rdata(tgt)):
                slots.append(tgt)
                a += 4
            else:
                break
        if slots:
            vtables[V] = {'root': root, 'col': col, 'ptd': ptd, 'pchd': pchd,
                          'name': tdname(ptd), 'slots': slots}
    return vtables

# ---------- CHD / BCD ----------
def chd_bases(pchd):
    off = P.r2o(pchd)
    if off is None or off + 16 > len(RAW):
        return None
    sig, attr, numbase, pbasearray = struct.unpack_from('<IIII', RAW, off)
    # pBaseArray is an array of 4-byte pointers to BCDs (each BCD is 0x1c bytes)
    out = []
    if not (RDATA_LO <= pbasearray < RDATA_HI) or numbase > 1000:
        return (sig, attr, numbase, pbasearray, out)
    for i in range(numbase):
        bo = P.r2o(dw(pbasearray + i * 4))
        if bo is None or bo + 0x1c > len(RAW):
            break
        bpTD, ncont, mdisp, pdisp, vdisp, attrs, bpCHD = struct.unpack_from('<IIIIIIi', RAW, bo)
        # PMD.mdisp is signed int32 in this build; re-interpret for negative test
        mdisp_s = mdisp if mdisp < 0x80000000 else mdisp - 0x100000000
        out.append({'pTD': bpTD, 'name': tdname(bpTD), 'mdisp': mdisp, 'mdisp_s': mdisp_s,
                    'pdisp': pdisp, 'vdisp': vdisp, 'attrs': attrs, 'pCHD': bpCHD,
                    'ncont': ncont})
    return (sig, attr, numbase, pbasearray, out)

SIX = [0x7f5c70, 0x7eb058, 0x7e22a4, 0x7e8c94, 0x7e3ebc, 0x7f4960]
CONTROL = {0x7e1f50: 24, 0x7e1f34: 6}

# ---------- streaming .text disassembly ----------
GP_REGS = {X86_REG_EAX, X86_REG_ECX, X86_REG_EDX, X86_REG_EBX, X86_REG_ESP,
           X86_REG_EBP, X86_REG_ESI, X86_REG_EDI}
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def scan_indirect():
    """Return list of (site, disp, mnemonic, opstr, bytes16) for call/jmp [reg+disp]."""
    sites = []
    bufsz = 0x8000
    va = TEXT_LO
    while va < TEXT_HI:
        off = P.r2o(va)
        remaining = TEXT_HI - va
        n = min(bufsz, remaining)
        if off is None:
            va += n
            continue
        n = min(n, len(RAW) - off)
        if n <= 0:
            break
        buf = RAW[off:off+n]
        for ins in md.disasm(buf, va):
            if ins.mnemonic not in ('call', 'jmp'):
                continue
            for op in ins.operands:
                if op.type != CS_OP_MEM or op.mem.base not in GP_REGS:
                    continue
                if op.mem.scale != 1 or op.mem.index != 0:
                    continue
                disp = op.mem.disp
                if disp < 0:
                    continue
                byteoff = P.r2o(ins.address)
                raw16 = RAW[byteoff:byteoff+min(16, ins.size)].hex() if byteoff is not None else ''
                sites.append({'addr': ins.address, 'disp': disp, 'mnem': ins.mnemonic,
                              'opstr': ins.op_str, 'raw': raw16, 'size': ins.size})
        del buf
        va += n
    return sites

# ============ MAIN ============
lines = []
def p(s=''):
    lines.append(str(s))

p('=== R218-A slot>=256 forensics ===')
p('sha256 script: ' + hashlib.sha256(open(__file__,'rb').read()).hexdigest())
p('PE sections: ' + repr(P.B))

# positive control: vtable discovery + slot counts
p('\n## POSITIVE CONTROL: vtable root discovery')
vt = collect_vtables(allow_rdata=False)
p('vtable count (.text-only targets): %d' % len(vt))
total_slots = sum(len(v['slots']) for v in vt.values())
p('total slots (.text-only): %d' % total_slots)
cnt = Counter(len(v['slots']) for v in vt.values())
over = sorted([(V, len(v['slots']), v['name']) for V, v in vt.items() if len(v['slots']) > 256])
p('tables with >256 slots: %d' % len(over))
for V, n, nm in sorted(over):
    p('  0x%x  %s  slots=%d' % (V, nm, n))
p('sum(slots-256) for >256 tables: %d' % sum(n-256 for _,n,_ in over))
for V, expect in sorted(CONTROL.items()):
    got = len(vt[V]['slots']) if V in vt else -1
    p('control 0x%x: expect=%d got=%d name=%s' % (V, expect, got, vt[V]['name'] if V in vt else '-'))
for V in SIX:
    p('six 0x%x: got=%d name=%s' % (V, len(vt[V]['slots']), vt[V]['name']))

# A4b .text|.rdata
vt2 = collect_vtables(allow_rdata=True)
p('\n## A4b total slots with .text|.rdata criteria: %d (tables=%d)' %
  (sum(len(v['slots']) for v in vt2.values()), len(vt2)))

# ---------- A1 ----------
p('\n## A1: super-256 slots vs parent class')
a1_report = []
for V in SIX:
    v = vt[V]
    p('\n--- 0x%x %s slots=%d col=0x%x pTD=0x%x pCHD=0x%x ---' %
      (V, v['name'], len(v['slots']), v['col'], v['ptd'], v['pchd']))
    info = chd_bases(v['pchd'])
    if info is None:
        p('  CHD unreadable')
        continue
    sig, attr, numbase, pbase, bases = info
    p('  CHD sig=0x%x attr=0x%x numBase=%d pBaseArray=0x%x' % (sig, attr, numbase, pbase))
    for i, b in enumerate(bases):
        flag = ' SELF' if b['pCHD'] == v['pchd'] else ''
        p('  BCD[%d] pTD=0x%x name=%s PMD=(mdisp=0x%x,pdisp=0x%x,vdisp=0x%x) attrs=0x%x pCHD=0x%x%s' %
          (i, b['pTD'], b['name'], b['mdisp'], b['pdisp'], b['vdisp'], b['attrs'], b['pCHD'], flag))
    # direct parent: negative mdisp, smallest abs; need unique
    neg = [b for b in bases if b['mdisp_s'] < 0]
    neg_sorted = sorted(neg, key=lambda b: abs(b['mdisp_s']))
    parentV = None
    reason = ''
    if neg_sorted:
        best = [b for b in neg_sorted if abs(b['mdisp_s']) == abs(neg_sorted[0]['mdisp_s'])]
        if len(best) == 1:
            parentV = best[0]
            reason = 'unique minimal negative mdisp'
        else:
            p('  parent ambiguous by rule1: %s' % ','.join(b['name'] for b in best))
    if parentV is None and neg:
        # rule2: whose pCHD base array contains this class's pTD
        cands = []
        for b in neg:
            inf2 = chd_bases(b['pCHD'])
            if not inf2:
                continue
            if any(x['pTD'] == v['ptd'] for x in inf2[4]):
                cands.append(b)
        if len(cands) == 1:
            parentV = cands[0]
            reason = 'rule2 pCHD contains self'
        elif len(cands) > 1:
            p('  parent ambiguous by rule2: %s' % ','.join(b['name'] for b in cands))
    if parentV is None:
        p('  父类不唯一 or undetermined; degrade to self-low-256 check')
        same = diff = out_of_range = 0
        for idx in range(256, len(v['slots'])):
            t = v['slots'][idx]
            if t in set(v['slots'][:256]):
                same += 1
            else:
                diff += 1
        p('  self-low256 seen=%d novel=%d' % (same, diff))
        a1_report.append((V, v['name'], 'DEGRADED', same, diff, 0))
        continue
    p('  parent=%s pTD=0x%x (%s)' % (parentV['name'], parentV['pTD'], reason))
    # find parent vtable V by pTD among all vtables
    pvs = [pV for pV, pv in vt.items() if pv['ptd'] == parentV['pTD']]
    if not pvs:
        p('  parent vtable not found; degrade')
        a1_report.append((V, v['name'], 'DEGRADED', 0, 0, 0))
        continue
    pV = pvs[0]
    ps = vt[pV]['slots']
    p('  parent vtable=0x%x slots=%d' % (pV, len(ps)))
    same = diff = oob = 0
    diffs = []
    for idx in range(256, len(v['slots'])):
        t = v['slots'][idx]
        if idx >= len(ps):
            oob += 1
            diffs.append((idx, t, None))
        elif ps[idx] == t:
            same += 1
        else:
            diff += 1
            diffs.append((idx, t, ps[idx]))
    p('  compare: same=%d diff=%d parent_oob=%d' % (same, diff, oob))
    for idx, t, pt in diffs:
        p('    slot=%d self=0x%x[%s] parent=%s[%s]' %
          (idx, t, hex8(t), ('0x%x'%pt) if pt else '-', hex8(pt)))
    a1_report.append((V, v['name'], parentV['name'], same, diff, oob))

p('\n## A1 summary')
p('V | name | parent | same | diff | oob')
for row in a1_report:
    p('%s | %s | %s | %d | %d | %d' % ('0x%x'%row[0], row[1], row[2], row[3], row[4], row[5]))

# ---------- A2 ----------
p('\n## A2: indirect call/jmp displacement scan')
sites = scan_indirect()
p('scanned .text 0x%x..0x%x' % (TEXT_LO, TEXT_HI))
p('total call/jmp [reg+disp] sites (disp>=0): %d' % len(sites))
ge400 = [s for s in sites if s['disp'] >= 0x400]
p('sites with disp>=0x400: %d' % len(ge400))
d400 = Counter(s['disp'] for s in ge400)
p('distinct disp>=0x400: %d -> %s' % (len(d400), ','.join('0x%x'%d for d in sorted(d400))))
not4 = sorted(set(d for d in d400 if d % 4 != 0))
p('disp not multiple of 4: %d -> %s' % (len(not4), ','.join('0x%x'%d for d in not4)))
sl = Counter(s['disp']//4 for s in ge400 if s['disp'] % 4 == 0 and s['disp']//4 >= 256)
p('site count with slot>=256: %d' % sum(sl.values()))
p('top20 slot counts: ' + ', '.join('slot%d=%d'%(k,c) for k,c in sl.most_common(20)))
# random 5 byte check
random.seed(218)
sample = random.sample(ge400, min(5, len(ge400)))
p('random 5 raw-byte checks:')
for s in sample:
    p('  0x%x %s %s raw16=%s' % (s['addr'], s['mnem'], s['opstr'], s['raw']))
ge2c = [s for s in sites if s['disp'] >= 0x2c]
p('positive control threshold disp>=0x2c: total=%d' % len(ge2c))
found = any(s['addr'] == 0x410210 for s in sites)
p('R217 forwarder 0x410210 call [edx+0x2c] found: %s' % found)
for s in sites:
    if s['addr'] == 0x410210:
        p('  0x%x %s %s raw=%s' % (s['addr'], s['mnem'], s['opstr'], s['raw']))
# reverse control: sites with 0<=disp<0x400 and disp//4>=256 (must be 0)
lt400_256 = [s for s in sites if s['disp'] < 0x400 and s['disp']//4 >= 256]
p('reverse control disp<0x400 with slot>=256: %d (must be 0)' % len(lt400_256))

# ---------- A3 ----------
p('\n## A3: target function profile of 464 slots')
all_targets = []
for V in SIX:
    for idx, t in enumerate(vt[V]['slots'][256:], start=256):
        all_targets.append((V, idx, t))
p('total target entries: %d' % len(all_targets))
uniq = Counter(t for _,_,t in all_targets)
p('unique targets: %d' % len(uniq))
p('top15 (target | freq | tables | slotcount | slots[:10] | hex8):')
by_t = defaultdict(list)
for V, idx, t in all_targets:
    by_t[t].append((V, idx))
for t, c in uniq.most_common(15):
    entries = by_t[t]
    tbl = len(set(V for V,_ in entries))
    slots = sorted(set(i for _,i in entries))
    p('  0x%x | %d | %d | %d | %s | %s' % (t, c, tbl, len(slots), ','.join(str(x) for x in slots[:10]), hex8(t)))
# classification
cat = Counter()
for _,_,t in all_targets:
    h = hex8(t)
    b = bytes.fromhex(h) if h not in ('?','-') else b''
    if b.startswith(bytes.fromhex('33c0c3')):
        cat['xor_eax_ret'] += 1
    elif b.startswith(b'\xc3'):
        cat['ret'] += 1
    elif len(b) >= 6 and b[0] == 0xb8 and b[5] == 0xc2:
        cat['const_ret'] += 1
    else:
        cat['other'] += 1
p('classification: %s' % dict(cat))
outside = sorted(set(t for _,_,t in all_targets if not in_text(t)))
p('targets outside .text: %d -> %s' % (len(outside), ','.join('0x%x'%x for x in outside)))

# ---------- A4a ----------
p('\n## A4a: negative control')
for V, exp in sorted(CONTROL.items()):
    s = vt.get(V, {}).get('slots', [])
    p('0x%x expect_slots=%d got=%d slots>=256 count=%d' % (V, exp, len(s), len(s[256:])))

p('\n## ANOMALIES & UNCERTAINTY')
p('- Parent determination relies on mdisp sign encoding; if no unique minimal-negative mdisp BCD, rule2 (pCHD contains self pTD) used. Degraded cases are marked above.')
p('- Byte-signature classification uses first 8 bytes only; return-constant pattern b8 ?? ?? ?? ?? c2 requires 6 bytes and may overlap other code.')
p('- disasm_lite token parse for [reg+disp] uses textual regex; only call/jmp with dword ptr and plain reg+/-disp accepted; scaled-index forms excluded (counted as absent).')

outpath = os.path.join(OUTDIR, 'cardA_evidence.txt')
with open(outpath, 'w') as f:
    f.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('\nWROTE', outpath)
