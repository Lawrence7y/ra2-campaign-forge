# -*- coding: utf-8 -*-
# R216 audit: A7 law W via objdump single streaming linear sweep, two delta calibers
import sys, json, re, subprocess, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {st: COLA[c][0] for c, st in UNIQ.items()}
VSET = set(VIEWS); SLOTS = set(x for v in VIEWS.values() for x in v)
texte = P.B['.text']; lo, hi = texte['lo'], texte['hi_file']
print("views=%d slots=%d VSET&SLOTS=%d text=%08x..%08x" % (len(VIEWS), len(SLOTS), len(VSET & SLOTS), lo, hi))

RX_SITE = re.compile(r'^\s*([0-9a-f]+):\s+mov\s+(?:DWORD PTR|dword ptr)\s+\[([a-z0-9]{2,3})((?:[+-](?:0x[0-9a-f]+|\d+))?)\],\s*(0x[0-9a-f]+)\s*$', re.I)
RX_INSN = re.compile(r'^\s*([0-9a-f]+):\s+([a-z][a-z0-9]*)\s*(.*?)\s*$', re.I)
RX_MOVR  = re.compile(r'^([a-z][a-z0-9]{1,2}),\s*(0x[0-9a-f]+)$', re.I)
RX_LEA   = re.compile(r'^([a-z][a-z0-9]{1,2}),\s*\[([a-z][a-z0-9]{1,2})((?:[+-](?:0x[0-9a-f]+|\d+))?)\]\s*$', re.I)
RX_ADD   = re.compile(r'^([a-z][a-z0-9]{1,2}),\s*(0x[0-9a-f]+|\d+)$', re.I)

def parse_disp(s):
    if not s: return 0
    return int(s, 0) if s[0] not in '+-' else int(s[0] + s[1:], 0)

cmd = ['i686-w64-mingw32-objdump', '-d', '-M', 'intel', '--no-show-raw-insn',
       '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1 << 22)

cal = {'strict': {}, 'loose': {}}
tot_insn = 0; tot_c7 = 0
sites = 0; hit = 0; idxskip = 0
res = {k: {'solved': 0, 'unsolved': 0, 'eq': 0, 'ne': 0, 'diffs': [], 'ex': []} for k in cal}

for line in p.stdout:
    m = RX_INSN.match(line)
    if not m: continue
    a = int(m.group(1), 16)
    if not (lo <= a < hi): continue
    mn = m.group(2).lower(); ops = m.group(3)
    tot_insn += 1

    # ---- site test happens BEFORE the site mutates state (a store doesn't rename regs) ----
    sm = RX_SITE.match(line)
    if sm:
        tot_c7 += 1
        disp = parse_disp(sm.group(3)); imm = int(sm.group(4), 16)
        if imm in VSET:
            hit += 1
            r = sm.group(2).lower()
            for k, st in cal.items():
                if r in st:
                    res[k]['solved'] += 1
                    d = disp + st[r] - VM[imm]
                    if d == 0: res[k]['eq'] += 1
                    else:
                        res[k]['ne'] += 1; res[k]['diffs'].append(d)
                        if d <= 0 and len(res[k]['ex']) < 15:
                            res[k]['ex'].append((a, ops, r, st[r], disp, VM[imm], d))
                else:
                    res[k]['unsolved'] += 1
    elif '[' in ops and ',' in ops and re.match(r'^dword ptr \[', ops, re.I):
        if re.search(r'mov\s+dword ptr \[', line, re.I): idxskip += 1

    # ---- state updates ----
    if mn == 'call':
        for k in cal:
            for r in ('eax', 'ecx', 'edx'): cal[k].pop(r, None)
    elif mn in ('ret', 'retf', 'jmp', 'iretd'):
        for k in cal: cal[k].clear()
    if mn == 'mov':
        mm = RX_MOVR.match(ops)
        if mm:
            for k, st in cal.items(): st[mm.group(1).lower()] = int(mm.group(2), 16)
        else:
            mm = re.match(r'^([a-z][a-z0-9]{1,2}),', ops, re.I)
            if mm:
                r = mm.group(1).lower()
                cal['strict'].pop(r, None); cal['loose'][r] = 0
    elif mn == 'lea':
        mm = RX_LEA.match(ops)
        if mm:
            d, s2 = mm.group(1).lower(), mm.group(2).lower(); k2 = parse_disp(mm.group(3))
            for k, st in cal.items():
                if s2 in st: st[d] = st[s2] + k2
                else: st.pop(d, None)
        else:
            mm = re.match(r'^([a-z][a-z0-9]{1,2}),', ops, re.I)
            if mm: cal['strict'].pop(mm.group(1).lower(), None); cal['loose'][mm.group(1).lower()] = 0
    elif mn in ('add', 'sub'):
        mm = RX_ADD.match(ops)
        if mm:
            r = mm.group(1).lower(); v = int(mm.group(2), 0)
            if mn == 'sub': v = -v
            for k, st in cal.items():
                if r in st: st[r] = st[r] + v
                else: st.pop(r, None)
        else:
            mm = re.match(r'^([a-z][a-z0-9]{1,2}),', ops, re.I)
            if mm: cal['strict'].pop(mm.group(1).lower(), None); cal['loose'].pop(mm.group(1).lower(), None)
    elif mn == 'xor':
        mm = re.match(r'^([a-z][a-z0-9]{1,2}),\s*([a-z][a-z0-9]{1,2})$', ops, re.I)
        if mm and mm.group(1).lower() == mm.group(2).lower():
            for k, st in cal.items(): st[mm.group(1).lower()] = 0
    elif mn == 'pop':
        r = ops.strip().lower()
        if re.match(r'^[a-z][a-z0-9]{1,2}$', r):
            cal['strict'].pop(r, None); cal['loose'][r] = 0
    elif mn in ('push', 'cmp', 'test', 'inc', 'dec', 'and', 'or', 'shl', 'shr', 'movzx', 'movsx'):
        pass
p.stdout.close(); p.wait()

print("\n[objdump linear sweep, resyncing] insns=%d  C7 'mov dword ptr [mem], imm32' sites=%d" % (tot_insn, tot_c7))
print("  sites with imm in view-start set = %d   (other mem-imm mov forms skipped: %d)" % (hit, idxskip))
for k, r in res.items():
    print("\n caliber=%s : solved=%d unsolved=%d  eq=%d  ne=%d" % (k, r['solved'], r['unsolved'], r['eq'], r['ne']))
    if r['diffs']:
        ds = r['diffs']
        print("   diff min=%d max=%d  count<=0=%d  count>0=%d" % (min(ds), max(ds), sum(1 for x in ds if x <= 0), sum(1 for x in ds if x > 0)))
        from collections import Counter
        print("   diff top:", Counter(ds).most_common(8))
    for e in r['ex']:
        print("   nonpos: %08x %-42s reg=%s delta=%d disp=%d mdisp=%d diff=%d" % e)
