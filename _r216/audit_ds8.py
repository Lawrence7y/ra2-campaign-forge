# -*- coding: utf-8 -*-
# R216 audit: A7 breakdown - base register / delta calibers, to reconcile 4195/2911/2551/360
import sys, json, re, subprocess
from collections import Counter, defaultdict
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

D = json.load(open('/home/t628/projects/ra2-campaign-forge/_r216/audit_ds_views.json'))
VIEWS = {int(k, 16): v for k, v in D['views'].items()}
COLA = {int(k, 16): v for k, v in D['cola'].items()}
UNIQ = {int(k, 16): v for k, v in D['preamble2view'].items()}
VM = {st: COLA[c][0] for c, st in UNIQ.items()}
VSET = set(VIEWS)
lo, hi = P.B['.text']['lo'], P.B['.text']['hi_file']

RX_SITE = re.compile(r'^\s*([0-9a-f]+):\s+mov\s+dword ptr \[([a-z0-9]{2,3})((?:[+-](?:0x[0-9a-f]+|\d+))?)\],\s*(0x[0-9a-f]+)\s*$', re.I)
RX_INSN = re.compile(r'^\s*([0-9a-f]+):\s+([a-z][a-z0-9]*)\s*(.*?)\s*$', re.I)

def pd(s):
    return 0 if not s else int(s, 0) if s[0] not in '+-' else int(s[0] + s[1:], 0)

# calibers:
#  A) 'off': registers hold only offsets from an unknown pointer base.
#     mov reg,[esp+N] / mov reg,[ebp+N] / mov reg,[reg2+disp] -> offset (if reg2 known)
#     mov reg, imm  -> UNKNOWN (absolute value, not a this-pointer offset)
#  B) 'abs': registers hold absolute values; mov reg,[esp+N] -> 0 (loose-ish but param base)
cmd = ['i686-w64-mingw32-objdump', '-d', '-M', 'intel', '--no-show-raw-insn',
       '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1 << 22)

st_off = {}     # caliber A
st_abs = {}     # caliber B
stats = defaultdict(int)
statsC = defaultdict(Counter)
sitesA = defaultdict(int); sitesB = defaultdict(int)
ex = []

def upd(regs, mode, mn, ops, line):
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'): regs.pop(r, None); return
    if mn in ('ret', 'retf', 'jmp', 'iretd', 'leave'):
        regs.clear(); return
    if mn == 'mov':
        m = re.match(r'^([a-z][a-z0-9]{1,2}),\s*(.+)$', ops, re.I)
        if not m: return
        d = m.group(1).lower(); src = m.group(2)
        mm = re.match(r'^(0x[0-9a-f]+)$', src, re.I)
        if mm:
            if mode == 'abs': regs[d] = int(mm.group(1), 16)
            else: regs.pop(d, None)
            return
        mm = re.match(r'^\[([a-z][a-z0-9]{1,2})((?:[+-](?:0x[0-9a-f]+|\d+))?)\]$', src, re.I)
        if mm:
            b = mm.group(1).lower(); disp = pd(mm.group(2))
            if b == 'esp' or b == 'ebp' or b in ('esi', 'edi', 'ebx', 'eax', 'ecx', 'edx'):
                # pointer load: base becomes 0 offset (unknown absolute)
                regs[d] = 0 if (b in ('esp', 'ebp') or True) else None
            else: regs.pop(d, None)
            return
        regs.pop(d, None); return
    if mn == 'lea':
        m = re.match(r'^([a-z][a-z0-9]{1,2}),\s*\[([a-z][a-z0-9]{1,2})((?:[+-](?:0x[0-9a-f]+|\d+))?)\]$', ops, re.I)
        if m:
            d, b = m.group(1).lower(), m.group(2).lower(); disp = pd(m.group(3))
            if b in regs: regs[d] = regs[b] + disp
            elif b in ('esp', 'ebp'): regs[d] = disp
            else: regs.pop(d, None)
            return
        d = ops.split(',')[0].strip().lower(); regs.pop(d, None); return
    if mn in ('add', 'sub'):
        m = re.match(r'^([a-z][a-z0-9]{1,2}),\s*(0x[0-9a-f]+|\d+)$', ops, re.I)
        if m:
            r = m.group(1).lower(); v = int(m.group(2), 0) * (1 if mn == 'add' else -1)
            if r in regs: regs[r] += v
            else: regs.pop(r, None)
            return
        r = ops.split(',')[0].strip().lower(); regs.pop(r, None); return
    if mn == 'xor':
        m = re.match(r'^([a-z][a-z0-9]{1,2}),\s*([a-z][a-z0-9]{1,2})$', ops, re.I)
        if m and m.group(1).lower() == m.group(2).lower(): regs[m.group(1).lower()] = 0
        return
    if mn in ('pop',):
        r = ops.strip().lower()
        if re.match(r'^[a-z][a-z0-9]{1,2}$', r): regs.pop(r, None)
        return
    if mn in ('inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar', 'sal', 'imul', 'mul', 'div', 'idiv',
              'xchg', 'adc', 'sbb', 'neg', 'not', 'movzx', 'movsx', 'cmovne', 'setne', 'push'):
        r = ops.split(',')[0].strip()
        if re.match(r'^[a-z][a-z0-9]{1,2}$', r, re.I): regs.pop(r.lower(), None)
        return

for line in p.stdout:
    m = RX_INSN.match(line)
    if not m: continue
    a = int(m.group(1), 16)
    if not (lo <= a < hi): continue
    mn = m.group(2).lower(); ops = m.group(3)
    sm = RX_SITE.match(line)
    if sm:
        r = sm.group(2).lower(); disp = pd(sm.group(3)); imm = int(sm.group(4), 16)
        mdisp = VM.get(imm)
        if mdisp is not None:
            statsC['imminvset'][r] += 1
            statsC['disp'][('0' if disp == 0 else '+')] += 1
            sitesA[(r, disp == 0)] += 1
            for tag, st in (('A', st_off), ('B', st_abs)):
                if r in st:
                    d = disp + st[r] - mdisp
                    stats[tag + '_solved'] += 1
                    if d == 0: stats[tag + '_eq'] += 1
                    else:
                        stats[tag + '_ne'] += 1
                        statsC[tag + '_diff'][('<=0' if d <= 0 else '>0')] += 1
                        if d <= 0 and len(ex) < 8 and tag == 'B':
                            ex.append((a, ops, r, st[r], disp, mdisp, d))
                    if tag == 'B': stats['B_dmin'] if False else None
                else:
                    stats[tag + '_unsolved'] += 1
    upd(st_off, 'off', mn, ops, line)
    upd(st_abs, 'abs', mn, ops, line)
p.stdout.close(); p.wait()

print("total sites with imm in VSET:", sum(statsC['imminvset'].values()))
print(" by base reg:", dict(sorted(statsC['imminvset'].items())))
print(" by disp shape:", dict(statsC['disp']))
print(" (reg,disp==0) counts:", dict(sorted(sitesA.items())))
for tag in ('A', 'B'):
    print("\n caliber=%s solved=%d unsolved=%d eq=%d ne=%d" % (tag, stats[tag+'_solved'], stats[tag+'_unsolved'], stats[tag+'_eq'], stats[tag+'_ne']))
    print("   nonpositive diffs:", dict(statsC[tag+'_diff']))
print("\n examples B <=0:")
for e in ex: print("  %08x %-40s reg=%s delta=%d disp=%d mdisp=%d diff=%d" % e)
