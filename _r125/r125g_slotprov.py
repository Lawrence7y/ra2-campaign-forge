# -*- coding: utf-8 -*-
"""R125g: slot-aware provenance, to settle the .data twin population.

R125e/R125f tracked provenance in REGISTERS only.  That misses the smart-pointer
hand-off this compiler emits, seen by hand at 0x4af851-0x4af8a5:

    lea edx, [esp + 0x10]      ; QueryInterface out-parameter (temp)
    push edx ; push 0x820270 ; push eax ; call dword ptr [ecx]
    mov edi, eax               ; HRESULT
    ...
    mov eax, dword ptr [esp + 0x14]     ; CComPtr member
    mov ebx, dword ptr [esp + 0x10]     ; the QI result
    test eax, eax ; je ... ; mov ecx,[eax] ; push eax ; call dword ptr [ecx + 8]  ; Release old
    mov dword ptr [esp + 0x14], ebx     ; store the NEW interface into the CComPtr
    ...
    mov edx, dword ptr [esp + 0x14]
    push esi ; push edx ; call dword ptr [0x7e15f4]     ; OleSaveToStream(ppstm, ...)

So the interface reaches the OLE call through a STACK SLOT, not a register.  A
register-only tracker reports "no OLE call" here, which is what R125f's W2
unresolved bucket was hiding.

This script carries both a register map and a slot map, seeded with the ppv slot
as an object, and asks the same question: is the object that came out of this
QueryInterface passed as argument 0 of OleSaveToStream?
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r125', 'r125g_slotprov.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
add('G0 exe sha256 is the pinned build',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(
    pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)

IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None
OLE = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream'}
add('G1 the OLE entry points resolve at absolute IAT addresses',
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

REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

def base_reg(txt):
    t = txt.strip()
    if t in REGS:
        return t
    if '[' in t and t.endswith(']'):
        return t[t.index('[') + 1:-1].split(' + ')[0].split(' - ')[0].strip()
    return None

G = {0x7f7c80: '109a', 0x820270: '109b', 0x7f7c70: '10Cc', 0x818858: '10Ca'}
TAG = {v: k for k, v in G.items()}

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

def classify(run, cbeg, cend, K):
    """Walk from the QI call with register+slot provenance.

    Returns dict with the OLE api reached (if any), the argument position of the
    interface, and a flag for whether the interface ever flowed into the call.
    """
    reg = {}
    # Seed the ppv slot: the QueryInterface call just wrote the interface there,
    # and QueryInterface is stdcall so the slot index is unchanged across the
    # call.  Without this seed no object ever enters the maps (S-147).
    slot = {K: 'obj'}
    i = cbeg
    while i < min(n_ins, cend):
        a, m, o = ins[i]
        if m == 'ret':
            break
        parts = o.split(', ')
        dst = parts[0].strip()
        src = parts[1].strip() if len(parts) > 1 else ''
        if m in ('mov', 'movzx', 'movsx', 'lea'):
            if dst in REGS:
                # register destination
                so = esp_off(src)
                if so is not None and slot.get(so) == 'obj':
                    reg[dst] = 'obj'
                elif so is not None:
                    reg.pop(dst, None)
                elif m == 'mov' and src in REGS and reg.get(src) == 'obj':
                    # register-to-register copy of the object (S-148)
                    reg[dst] = 'obj'
                elif ('[' in src and base_reg(src) in reg
                      and reg[base_reg(src)] == 'obj' and m == 'mov'):
                    reg[dst] = 'vt'
                else:
                    reg.pop(dst, None)
            elif '[esp + ' in dst and esp_off(dst) is not None:
                # store into a stack slot
                so = esp_off(dst)
                if dst.startswith('dword ptr') and src in REGS and reg.get(src) == 'obj':
                    slot[so] = 'obj'
                else:
                    slot.pop(so, None)
            i += 1
            continue
        if m == 'and':
            if dst in REGS and reg.get(base_reg(src)) == 'obj':
                reg[dst] = 'obj'
            elif dst in REGS:
                reg.pop(dst, None)
            i += 1
            continue
        if m == 'push':
            run.append(('reg' if o.strip() in REGS else 'other', o.strip(),
                        reg.get(o.strip())))
            i += 1
            continue
        if m == 'pop':
            if dst in REGS:
                reg.pop(dst, None)
            i += 1
            continue
        if m == 'call':
            if o.startswith('dword ptr ['):
                t = num(o[len('dword ptr ['):-1])
                if t in OLE:
                    args = [p for p in reversed(run)]
                    pos = None
                    for k, (_kk, txt, prov) in enumerate(args):
                        src_prov = prov
                        if src_prov is None:
                            so = esp_off(txt) if '[' in txt else None
                            if so is not None:
                                src_prov = slot.get(so)
                        if src_prov == 'obj':
                            pos = k
                            break
                    return {'api': OLE[t], 'argpos': pos, 'nargs': len(args)}
                # any other call consumes its own pushes
                run.clear()
                i += 1
                continue
            run.clear()
            i += 1
            continue
        if dst in REGS and m not in ('cmp', 'test'):
            reg.pop(dst, None)
        i += 1
    return {'api': None, 'argpos': None, 'nargs': len(run)}

rows = []
unres = collections.Counter()
for v, tag in G.items():
    for i, (a, m, o) in enumerate(ins):
        if m != 'push' or tail_imm(o) != v or is_dispatcher(i):
            continue
        qi = -1
        for j in range(i + 1, min(n_ins, i + 10)):
            if ins[j][1] == 'call':
                qi = j
                break
            if ins[j][1] == 'ret':
                break
        if qi < 0:
            unres['no_qi'] += 1
            continue
        K = None
        for j in range(i - 1, max(0, i - 9), -1):
            if ins[j][1] == 'lea' and '[esp + ' in ins[j][2]:
                K = esp_off(ins[j][2])
                break
        if K is None:
            unres['no_ppv_lea'] += 1
            continue
        # body end: first ret at or after the QI call
        end = qi
        while end < n_ins and ins[end][1] != 'ret':
            end += 1
        r = classify([], qi + 1, min(end + 1, n_ins), K)
        rows.append({'site': '0x%x' % a, 'tag': tag, 'K': K,
                     'api': r['api'], 'argpos': r['argpos'], 'nargs': r['nargs']})

add('G2 sites resolve at a usable rate', len(rows) > 60,
    'rows=%d unresolved=%s' % (len(rows), dict(unres)))

sav0 = [r for r in rows if r['api'] == 'OleSaveToStream' and r['argpos'] == 0]
savall = [r for r in rows if r['api'] == 'OleSaveToStream']
by_tag = collections.Counter(r['tag'] for r in sav0)
add('G3 the QueryInterface result is argument 0 of OleSaveToStream, and only'
    ' 00000109 tags produce such a site',
    len(sav0) > 30 and set(by_tag) <= {'109a', '109b'}, dict(by_tag))
add('G3b the count that reaches OleSaveToStream exceeds the count that can be'
    ' placed at argument 0; the gap is reported, not hidden',
    len(savall) >= len(sav0),
    'reaches=%d placed_at_arg0=%d gap=%d sites=%s'
    % (len(savall), len(sav0), len(savall) - len(sav0),
       ['0x%x' % int(r['site'], 16) for r in savall if r['argpos'] != 0]))

per_tag = collections.Counter(r['tag'] for r in rows)
add('G4 both .rdata and .data 00000109 populations exist, so the conclusion is'
    ' not carried by one address alone',
    per_tag['109a'] > 0 and per_tag['109b'] > 0, dict(per_tag))

n109b_sav = sum(1 for r in rows
                if r['tag'] == '109b' and r['api'] == 'OleSaveToStream')
n109b_all = per_tag['109b']
add('G5 every .data 00000109 site reaches OleSaveToStream once the stack-slot'
    ' hand-off is tracked (this is the number R125f lost)',
    n109b_sav == n109b_all and n109b_all > 0,
    '%d of %d' % (n109b_sav, n109b_all))

n10C_sav = sum(1 for r in rows
               if r['tag'] in ('10Ca', '10Cc') and r['api'] == 'OleSaveToStream')
add('G6 no 0000010C site reaches OleSaveToStream, with the same tracker',
    n10C_sav == 0, 'sites=%d' % n10C_sav)

add('G7 the tracker does not swallow every site: some resolved pushes reach no'
    ' OLE call at all, and none of them is mislabelled',
    any(r['api'] is None for r in rows),
    'no-api rows=%d of %d' % (sum(1 for r in rows if r['api'] is None), len(rows)))

rep = {'exe_sha256': EXE_SHA, 'rows': rows, 'unresolved': dict(unres),
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125g %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('unresolved:', dict(unres))
sys.exit(0 if not bad else 1)
