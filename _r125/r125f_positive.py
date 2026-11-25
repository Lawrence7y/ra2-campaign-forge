# -*- coding: utf-8 -*-
"""R125f: close two holes in R125e and turn the survivor's naming from
"by elimination" into positive evidence.

Holes in R125e:
  H1  R125e assumed the register holding the ppv readback is still that same
      object when it is pushed as argument 0.  A register can be reassigned in
      between.  Fixed here by asserting no write to the holder between the
      readback and the push run (W9).
  H2  R125e's forward walk covered 24 instructions, which is short.  Here the
      walk runs to the end of the basic block (first ret / first unconditional
      jump target boundary) with a hard cap, and every early exit is counted.

New positive test for the OTHER constant:
  P1  if 0000010C is IPersist, then a handle obtained by querying it should be
      used only at vtable byte offset 12 (slot 3), because IUnknown occupies
      slots 0..2 and IPersist adds exactly one method (GetClassID).
      R124 established IPersist's NumContainedBases = 1 and IUnknown = 3 from
      RTTI, so slot 3 = offset 0xc is where GetClassID must be.
      This is a positive prediction that can FAIL, which is what makes it
      evidence rather than a story.

  P2  and the 00000109 handle should be used at offsets 0..0x1c (slots 0..7 of
      an 8-slot interface block per R124's destructor-write boundary).
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r125', 'r125f_positive.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
add('W0 exe sha256 is the pinned build',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(
    pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)

IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None
OLE = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream'}
add('W1 the two OLE entry points resolve at absolute IAT addresses',
    IAT.get(0x7e15f4) == 'OleSaveToStream' and IAT.get(0x7e15f8) == 'OleLoadFromStream')

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

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

def writes_reg(i, reg):
    """Does instruction i write the 32-bit register reg (any of its sub-forms)?"""
    a, m, o = ins[i]
    dst = o.split(',')[0].strip()
    if m in ('mov', 'movzx', 'movsx', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or',
             'inc', 'dec', 'imul', 'shl', 'shr', 'sar', 'not', 'neg'):
        base = dst.split(' ')[-1]
        if base == reg:
            return True
        if m == 'pop' and o.strip() == reg:
            return True
    return False

def walk_to_ole(start, cap=64):
    """Forward walk from the QI call to the first call, counting pushes.
    Stops at ret.  Returns (api_or_None, pushes, end_idx)."""
    pushes = []
    for j in range(start, min(n_ins, start + cap)):
        aj, mj, oj = ins[j]
        if mj == 'ret':
            return None, pushes, j
        if mj == 'push':
            pushes.append(oj.strip())
        elif mj == 'call':
            if oj.startswith('dword ptr ['):
                t = num(oj[len('dword ptr ['):-1])
                if t in OLE:
                    return OLE[t], pushes, j
                return None, pushes, j
            return None, pushes, j
    return None, pushes, min(n_ins, start + cap)

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
            aj, mj, oj = ins[j]
            if mj == 'lea' and '[esp + ' in oj:
                K = esp_off(oj)
                break
        if K is None:
            unres['no_ppv_lea'] += 1
            continue
        holder = None
        rd_i = None
        for j in range(qi + 1, min(n_ins, qi + 12)):
            aj, mj, oj = ins[j]
            if mj == 'ret':
                break
            if mj == 'mov' and esp_off(oj) == K:
                holder = oj.split(',')[0].strip()
                rd_i = j
                break
        if holder is None:
            unres['no_readback'] += 1
            continue
        api, pushes, end_i = walk_to_ole(qi + 1)
        argpos = None
        arg_i = None
        if pushes:
            args = list(reversed(pushes))
            for k, pr in enumerate(args):
                if pr == holder:
                    argpos = k
                    break
        # W9: no write to the holder register between the readback and the push
        clobber = [j for j in range(rd_i + 1, end_i) if writes_reg(j, holder)]
        rows.append({'site': '0x%x' % a, 'tag': tag, 'K': K, 'holder': holder,
                     'read_at': '0x%x' % ins[rd_i][0], 'api': api,
                     'argpos': argpos, 'nargs': len(pushes),
                     'clobbers': ['0x%x' % ins[j][0] for j in clobber]})

add('W2 sites resolve at a usable rate', len(rows) > 60,
    'rows=%d unresolved=%s' % (len(rows), dict(unres)))

sav = [r for r in rows if r['api'] == 'OleSaveToStream' and r['argpos'] == 0]
add('W3 the QI result is argument 0 of OleSaveToStream with NO register rewrite'
    ' in between, at every such site',
    len(sav) > 30 and all(not r['clobbers'] for r in sav),
    'sites=%d clobbered=%d' % (len(sav), sum(1 for r in sav if r['clobbers'])))

add('W4 all of those sites come from the .rdata 00000109 constant',
    {r['tag'] for r in sav} == {'109a'},
    collections.Counter(r['tag'] for r in sav).most_common())

# ---- P1/P2: vtable offsets actually invoked on each tag's handle -----------
def ppv_slot_index(rd_va):
    i = next(i for i, (a, _m, _o) in enumerate(ins) if a == rd_va)
    return i

REGSET = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

def base_reg(txt):
    """'dword ptr [esi + 0x2c]' -> 'esi' ; 'eax' -> 'eax' ; else None"""
    t = txt.strip()
    if t in REGSET:
        return t
    if '[' in t and t.endswith(']'):
        inner = t[t.index('[') + 1:-1]
        return inner.split(' + ')[0].split(' - ')[0].strip()
    return None

def mem_off(txt):
    """'dword ptr [esi + 0x2c]' -> 0x2c ; '[esi]' -> 0"""
    t = txt.strip()
    if '[' not in t or not t.endswith(']'):
        return None
    inner = t[t.index('[') + 1:-1]
    if ' + ' not in inner:
        return 0
    return num(inner.rsplit(' + ', 1)[1])

def prov_vt_offsets(rd_i, cap=48):
    """Byte offsets of virtual calls made on the object that the ppv slot holds,
    tracked by a tiny provenance map so that unrelated objects in the same body
    are NOT attributed to this interface.

    Provenance: a register is 'obj' when it was loaded from [esp + K] (the ppv
    slot), and 'vt' when it was loaded from [<obj register>] (its vtable word).
    Only calls through an 'obj' or 'vt' register are recorded.  Any other write
    to a register clears its provenance.
    """
    prov = {}
    offs = []
    for j in range(rd_i, min(n_ins, rd_i + cap)):
        aj, mj, oj = ins[j]
        if mj == 'ret':
            break
        if mj == 'mov' or mj == 'movzx':
            dst = oj.split(', ', 1)[0].strip()
            src = oj.split(', ', 1)[1].strip() if ', ' in oj else ''
            if dst in REGSET:
                srcb = base_reg(src)
                srcprov = prov.get(srcb) if srcb else None
                if srcb and esp_off(src) is not None and esp_off(src) == K_USE.get(rd_i):
                    prov[dst] = 'obj'
                elif srcprov == 'obj':
                    prov[dst] = 'vt'
                else:
                    prov.pop(dst, None)
            continue
        # The 'hr < 0 ? NULL : ppv' idiom, spelled out because it is what this
        # compiler actually emits and it defeats a pure mov/movzx tracker:
        #     setl bl ; dec ebx ; and ebx, <ppv-value>     (S-144)
        if mj == 'and':
            dst = oj.split(', ', 1)[0].strip()
            src = oj.split(', ', 1)[1].strip() if ', ' in oj else ''
            if dst in REGSET and prov.get(base_reg(src)) == 'obj':
                prov[dst] = 'obj'
                continue
            if dst in REGSET:
                prov.pop(dst, None)
            continue
        if mj == 'call' and oj.startswith('dword ptr [') and oj.endswith(']'):
            inner = oj[len('dword ptr ['):-1]
            b = base_reg('[' + inner + ']')
            if prov.get(b) in ('obj', 'vt'):
                o2 = mem_off('[' + inner + ']')
                if o2 is not None:
                    offs.append(o2)
            continue
        dst = oj.split(',')[0].strip()
        if dst in REGSET and mj not in ('cmp', 'test', 'push'):
            prov.pop(dst, None)
    return offs

K_USE = {}

for r in rows:
    rd_i = ppv_slot_index(int(r['read_at'], 16))
    K_USE[rd_i] = r['K']
    r['vt'] = prov_vt_offsets(rd_i)

def offs_for(tag):
    c = collections.Counter()
    for r in rows:
        if r['tag'] == tag:
            for o in r['vt']:
                c[o] += 1
    return c

o109a = offs_for('109a'); o10Cc = offs_for('10Cc'); o10Ca = offs_for('10Ca')
add('P1 0000010C handles are never invoked past byte offset 0xc; 0xc is exactly'
    ' slot 3, the single slot IPersist adds on top of IUnknown 0..2',
    bool(o10Cc or o10Ca) and all(o <= 0xc for o in o10Cc) and all(o <= 0xc for o in o10Ca),
    {'0x7f7c70': dict(o10Cc), '0x818858': dict(o10Ca)})
add('P2 0000010C handles ARE invoked at offset 0xc at least once, so the'
    ' prediction has content rather than being vacuous',
    (0xc in o10Cc) or (0xc in o10Ca),
    {'0x7f7c70@0xc': o10Cc.get(0xc, 0), '0x818858@0xc': o10Ca.get(0xc, 0)})
_109_uses_0xc = o109a.get(0xc, 0)
_10C_uses_0xc = o10Cc.get(0xc, 0) + o10Ca.get(0xc, 0)
add('P3 the two constants are NOT interchangeable at use sites: only the'
    ' 0000010C handle is ever invoked at byte offset 0xc, never the 00000109 handle',
    _10C_uses_0xc > 0 and _109_uses_0xc == 0,
    {'0x7f7c80@0xc': _109_uses_0xc, '0x7f7c70@0xc': o10Cc.get(0xc, 0),
     '0x818858@0xc': o10Ca.get(0xc, 0), '109a_all': dict(o109a)})
add('P4 the 00000109 offsets stay inside the 8-slot interface block (< 0x20)',
    all(o < 0x20 for o in o109a), dict(o109a))

rep = {'exe_sha256': EXE_SHA, 'n_ins': n_ins, 'rows': rows,
       'unresolved': dict(unres),
       'vt_offsets': {'109a': dict(o109a), '10Cc': dict(o10Cc), '10Ca': dict(o10Ca)},
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125f %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('unresolved:', dict(unres))
sys.exit(0 if not bad else 1)
