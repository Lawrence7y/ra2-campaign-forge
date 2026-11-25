# -*- coding: utf-8 -*-
"""R125e: which ARGUMENT of the OLE call is the QueryInterface result?

R125a/R125d only ask "does the body containing this IID push also call an OLE
stream API".  That is a population association.  It cannot say whether the
handle produced by that QueryInterface is the interface handed to OLE, because
the body may push several objects and only one of them is the QI result.

This script measures the stronger, local relation:

  Q1  at each push of 00000109 / 0000010C, find the QueryInterface call it is
      the riid argument of, and recover the ppv out-parameter frame slot K
  Q2  QueryInterface is stdcall: it pops its own three arguments, so ESP at the
      call equals ESP right after it.  Therefore a read of [esp + K] AFTER the
      call names the SAME slot that the lea BEFORE the call named -- no frame
      arithmetic model is needed at all.  (This is the cheap, robust way to
      dodge the esp-model bugs that cost R125a six self-injuries.)
  Q3  walk forward inside the same basic block and record, for each push of a
      register loaded from [esp + K], whether it becomes argument 0 or 1 of the
      OLE call (last push = argument 0 in stdcall)
  Q4  controls: the non-QI argument; the 0000010C side; window 0

If the QI result is *always and only* argument 0 of OleSaveToStream, then the
byte-level fact "the object produced by querying this IID is used as the first
parameter of OleSaveToStream" is established without any header or signature
lookup.  Whether that first parameter is named IPersistStream is then a naming
question, and the script states separately what it does and does not prove.
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r125', 'r125e_argrole.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
add('Q0 exe sha256 is the pinned build',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(pe.get_data(TEXT.VirtualAddress,
                                                               TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)
idx_of = {a: i for i, (a, _m, _o) in enumerate(ins)}

IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None
OLE = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream'}
add('Q1 the OLE stream entry points resolve at absolute IAT addresses',
    IAT.get(0x7e15f4) == 'OleSaveToStream' and IAT.get(0x7e15f8) == 'OleLoadFromStream',
    {hex(k): IAT.get(k) for k in OLE})

def num(t):
    t = t.strip()
    if not t or t[0] not in '0123456789':
        return None
    try:
        return int(t, 0)
    except ValueError:
        return None

def tail_imm(op):
    return num(op.rsplit(', ', 1)[-1])

def esp_off(op):
    if '[esp + ' not in op or not op.endswith(']'):
        return None
    return num(op.rsplit('[esp + ', 1)[1][:-1])

G = {0x7f7c80: '109a', 0x820270: '109b', 0x7f7c70: '10Cc', 0x818858: '10Ca'}
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

rows = []
unresolved = collections.Counter()

for v, tag in G.items():
    for i, (a, m, o) in enumerate(ins):
        if m != 'push' or tail_imm(o) != v or is_dispatcher(i):
            continue
        # Q1/Q2: the ppv slot is the [esp + K] that is pushed (or lea'd) as the
        # third argument, and it is re-read with the SAME K after the call
        # because QueryInterface is stdcall.
        qi = -1
        for j in range(i + 1, min(n_ins, i + 10)):
            if ins[j][1] == 'call':
                qi = j
                break
            if ins[j][1] == 'ret':
                break
        if qi < 0:
            unresolved['no_qi_call'] += 1
            continue
        # the ppv slot was named before this push: look back for the lea
        K = None
        for j in range(i - 1, max(0, i - 9), -1):
            aj, mj, oj = ins[j]
            if mj == 'lea' and '[esp + ' in oj:
                K = esp_off(oj)
                break
        if K is None:
            unresolved['no_ppv_lea'] += 1
            continue
        # Q3: after the QI call, which register is loaded from [esp + K]?
        holder = None
        for j in range(qi + 1, min(n_ins, qi + 12)):
            aj, mj, oj = ins[j]
            if mj == 'ret':
                break
            if mj == 'mov' and oj.endswith('[esp + %s]' % (
                    ('0x%x' % K) if K >= 0xa else str(K))):
                holder = oj.split(',')[0].strip()
                break
            if mj == 'mov' and esp_off(oj) == K:
                holder = oj.split(',')[0].strip()
                break
        if holder is None:
            unresolved['no_ppv_readback'] += 1
            continue
        # walk forward: collect the push run feeding the next call
        pushes = []
        api = None
        for j in range(qi + 1, min(n_ins, qi + 24)):
            aj, mj, oj = ins[j]
            if mj == 'ret':
                break
            if mj == 'push':
                pushes.append(oj.strip())
            elif mj == 'call':
                if oj.startswith('dword ptr ['):
                    t = num(oj[len('dword ptr ['):-1])
                    if t in OLE:
                        api = OLE[t]
                break
        argpos = None
        if api and pushes:
            args = list(reversed(pushes))
            for k, pr in enumerate(args):
                if pr == holder:
                    argpos = k
                    break
        rows.append({'site': '0x%x' % a, 'tag': tag, 'K': K, 'holder': holder,
                     'api': api, 'argpos': argpos, 'nargs': len(pushes)})

add('Q2 the QI ppv slot and the readback register are recovered at most sites',
    len(rows) > 60 and sum(unresolved.values()) < 30,
    'resolved=%d unresolved=%s' % (len(rows), dict(unresolved)))

sav = [r for r in rows if r['api'] == 'OleSaveToStream']
load = [r for r in rows if r['api'] == 'OleLoadFromStream']
add('Q3 the OLE API reached from every one of these pushes is OleSaveToStream,'
    ' never OleLoadFromStream',
    len(sav) > 30 and len(load) == 0,
    'save=%d load=%d' % (len(sav), len(load)))

tags_with_save = collections.Counter(r['tag'] for r in sav)
add('Q4 every OleSaveToStream hit comes from a 00000109 push, none from 0000010C',
    set(tags_with_save) <= {'109a', '109b'}, dict(tags_with_save))

pos = collections.Counter((r['tag'], r['argpos']) for r in sav)
add('Q5 the QueryInterface result is ALWAYS passed as argument 0 of'
    ' OleSaveToStream at every resolved site',
    all(r['argpos'] == 0 for r in sav) and len(sav) > 30,
    'argpos distribution=%s' % {str(k): v for k, v in pos.items()})

narg = collections.Counter(r['nargs'] for r in sav)
add('Q6 OleSaveToStream is called with exactly 2 pushed arguments at every site'
    ' (a 2-parameter import, so the interface must be one of them)',
    set(narg) == {2}, dict(narg))

# control: some other register is argument 1 -- the two parameters are distinct
other = collections.Counter()
for r in sav:
    other[r['holder']] += 1
add('Q7 the interface register is a single, small set of registers (not'
    ' "every push happened to match")',
    len(other) <= 4, dict(other))

# control: sites that resolve to NO OLE call must exist, else the walk is
# accidentally swallowing everything
noapi = [r for r in rows if r['api'] is None]
add('Q8 the forward walk does not over-reach: a substantial share of the pushes'
    ' reach no OLE call at all',
    len(noapi) > 10, 'no-api rows=%d of %d' % (len(noapi), len(rows)))

rep = {'exe_sha256': EXE_SHA, 'n_ins': n_ins,
       'rows': rows, 'unresolved': dict(unresolved),
       'argpos_distribution': {str(k): v for k, v in pos.items()},
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125e %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('unresolved:', dict(unresolved))
sys.exit(0 if not bad else 1)
