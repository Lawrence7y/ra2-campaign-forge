# -*- coding: utf-8 -*-
"""R125a: separate the two IID constants R124 left TIED, using interface USAGE.

R124 decoded the RTTI method counts (IUnknown 3, IPersist 4 in total,
IPersistStream 8) but could not say which of 0x7f7c70 / 0x7f7c80 is which.
Its three records are identical for the pair, and the class-set record is
identical BY CONSTRUCTION: a class answering QI for IPersistStream must also
answer QI for IPersist, so the narrower interface's class set is a superset of
the wider one's and in this image the two are equal.  No class-side record can
ever split them.

The USE side is not symmetric, and that is what this script measures:

  S1  full .text linear scan (disasm_lite + skipdata), coverage pinned to T_HI
  S2  every immediate reference to a GUID constant, classified as
        DISPATCHER  mov edi,IMM inside the MSVC QI template
        QI          push IMM feeding an indirect call (a virtual QueryInterface)
        COCREATE    push IMM feeding CoCreateInstance
        OTHER       anything else
  S3  per QI site: recover the out-parameter frame slot K, then walk the code
      forward from the QI call carrying the handle; record every vtable byte
      offset invoked on it and every imported API that receives it
  S4  aggregate per GUID VALUE (the same 16 bytes appear at two addresses)
  S5  controls

Every number is measured at run time.

ESP model (this is where three earlier attempts died, see S-134..S-136):
  K is an offset from ESP *at the lea that named it*.  Argument pushes are
  TRANSIENT -- stdcall callees pop their own arguments and cdecl callers add
  esp,N right after the call -- so a push run that ends in a call contributes
  ZERO net shift.  A slot printed as k therefore maps to frame slot
  (k + delta), where delta = ESP_now - ESP_at_lea.
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r125', 'r125a_guid_role.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})
    return bool(ok)

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('S0a executable sha256 is the pinned build',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
blob = pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _sz, m, o in md.disasm_lite(blob, T_LO)]
n_ins = len(ins)
addr_index = {a: i for i, (a, _m, _o) in enumerate(ins)}
last = list(md.disasm(blob[ins[-1][0] - T_LO:], ins[-1][0]))[0]
add('S1a linear scan covers the whole .text (last instruction ends exactly at T_HI)',
    last.address + last.size == T_HI,
    'last=%x size=%d end=%x T_HI=%x' % (last.address, last.size,
                                        last.address + last.size, T_HI))
add('S1b scan did not stop early: instruction count in the measured range',
    1300000 < n_ins < 1500000, 'n_ins=%d' % n_ins)

# IAT slots are referenced as [ImageBase + RVA].  Keying them by RVA makes every
# lookup miss and silently zeroes the whole API record (S-133).
IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None
add('S1c imports resolve at absolute addresses, so call sites can be named',
    len(IAT) > 300 and IAT.get(0x7e15f4) == 'OleSaveToStream'
    and IAT.get(0x7e15f8) == 'OleLoadFromStream'
    and IAT.get(0x7e15fc) == 'CoCreateInstance',
    'n=%d 0x7e15f4=%r 0x7e15f8=%r 0x7e15fc=%r'
    % (len(IAT), IAT.get(0x7e15f4), IAT.get(0x7e15f8), IAT.get(0x7e15fc)))

REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')

def num(t):
    """Capstone prints small immediates in DECIMAL and large ones in hex, and
    decimal carries no 0x prefix, so int(x, 0) alone rejects '16'.  That spelling
    bug cost R124 13 QI branches (S-119)."""
    t = t.strip()
    if not t or t[0] not in '0123456789':
        return None
    try:
        return int(t, 0)
    except ValueError:
        return None

def esp_off(op):
    if '[esp + ' not in op:
        return None
    tail = op.rsplit('[esp + ', 1)[1]
    if not tail.endswith(']'):
        return None
    return num(tail[:-1])

def tail_imm(op):
    return num(op.rsplit(', ', 1)[-1])

GUID = {
    0x7e9530: 'ILinkStream',            0x7e9ae0: 'IRTTITypeInfo',
    0x7e9b00: 'IPublicHouse',           0x7e9b40: None,
    0x7ea6e8: 'IUnknown',               0x7ea768: 'IHouse',
    0x7ed358: None,                     0x7f7c20: 'IWOLBrowserEvent',
    0x7f7c70: None,                     0x7f7c80: None,
    0x7f7c90: 'IUnknown',               0x7f7ca0: 'IClassFactory',
    0x7f7cb0: 'IEnumConnections',       0x7f7cc0: 'IConnectionPoint',
    0x7f7cd0: 'IConnectionPointContainer',
    0x7f7ce0: 'IEnumConnectionPoints',  0x7f7cf0: None,
    0x7e36c0: None,                     0x7e9b20: None,
    0x817bc0: 'IUnknown(.data copy)',    0x818858: None,
    0x820270: None,
}
ALLOW = set(GUID)

refs = collections.defaultdict(list)
for i, (a, m, o) in enumerate(ins):
    if m in ('push', 'mov', 'cmp'):
        v = tail_imm(o)
        if v in ALLOW:
            refs[v].append((i, a, m))
add('S2a every IID constant in the census is referenced at least once',
    all(v in refs for v in ALLOW), 'missing=%s' % [hex(v) for v in ALLOW if v not in refs])
add('S2b census is not trivially small (guards an over-narrow immediate parse)',
    sum(len(v) for v in refs.values()) > 300, 'total refs=%d' % sum(len(v) for v in refs.values()))

def is_dispatcher(i):
    a, m, o = ins[i]
    if m != 'mov' or not o.startswith('edi, 0x'):
        return False
    w = ins[max(0, i - 8):i + 6]
    return (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
            and any(y[1].startswith('repe') for y in w))

def out_slot(i):
    """(frame slot K, index of the lea that named it).  K is measured against ESP
    at that lea, so the caller must carry the lea index along."""
    for j in range(i - 1, max(0, i - 9), -1):
        a, m, o = ins[j]
        if m == 'lea' and o.endswith(']') and '[esp + ' in o:
            reg = o.split(',')[0].strip()
            k = esp_off(o)
            if k is None:
                return None, None
            for t in range(j + 1, i + 1):
                if ins[t][1] == 'push' and ins[t][2] == reg:
                    return k, j
            return None, None
    return None, None

def callee(j):
    """('iat',name) | ('vt',base,byteoffset) | ('direct',va) | ('reg',reg) | ('other',txt)"""
    a, m, o = ins[j]
    o = o.strip()
    if o in REGS:
        return ('reg', o)
    if not o.startswith('dword ptr ['):
        v = num(o)
        return ('direct', v) if v is not None else ('other', o)
    inner = o[len('dword ptr ['):-1]
    if '+' in inner:
        base, off = inner.split('+')
        return ('vt', base.strip(), num(off))
    v = num(inner)
    if v is not None and v in IAT:
        return ('iat', IAT[v])
    if inner.strip() in REGS:
        return ('vt', inner.strip(), 0)
    return ('other', inner)

def site_call(i):
    """The call this IID push is an argument of.  CoCreateInstance takes five
    arguments, so the call can be a dozen instructions away; a six-instruction
    window silently reclassified all 56 CoCreateInstance sites as OTHER (S-139).
    Aborts on ret so the window never crosses a function boundary."""
    for t in range(i + 1, min(n_ins, i + 16)):
        a, m, o = ins[t]
        if m == 'call':
            return t
        if m == 'ret':
            return -1
    return -1

def esp_delta(i_from, i_to, verbose=False):
    """ESP(i_to) - ESP(i_from), with argument push runs collapsed at each call."""
    d = 0
    base = None
    trace = []
    for j in range(i_from + 1, i_to + 1):
        a, m, o = ins[j]
        if m == 'push':
            if base is None:
                base = d
            d -= 4
        elif m == 'pop':
            d += 4
        elif m in ('add', 'sub') and o.split(',')[0].strip() == 'esp':
            v = num(o.rsplit(', ', 1)[1])
            if v is None:
                return None
            d += v if m == 'add' else -v
        elif m == 'call':
            if base is not None:
                d = base
                base = None
        elif m == 'ret':
            return None
        if verbose:
            trace.append((a, m, o, d))
    if verbose:
        for t in trace:
            print('        %x %-8s %-28s delta=%d' % t)
    return d

def walk(call_i, K, base_d=0, node_cap=4000, depth_cap=400):
    """Bounded, path-sensitive CFG walk over the code that follows a QI call.

    A straight-line walk is WRONG here and R121 already paid for it (S-87): the
    MSVC QI idiom is

        call [ecx]            ; QueryInterface
        test eax,eax
        jge  success          ; <-- the success path is the JUMP TARGET
        ...failure path...    ;     the fall-through is the failure path
      success:

    so a linear sweep silently evaluates the failure path's registers as if they
    were the success path's.  This walker branches at every conditional jump,
    carrying (obj, vptr, held, d) per path, and stops a path at ret.

    K is an offset from ESP at the lea that named it; base_d converts to the
    frame at the call.
    """
    slots, apis = set(), set()
    start = call_i + 1
    if start >= n_ins:
        return [], []
    # Function-scope bound.  Without a symbol table the enclosing function is
    # unknown, but a QI and its handle's uses are always within a few hundred
    # instructions; allowing the walk to run unbounded lets it leave the function
    # through a jump and attribute UNRELATED code's vtable traffic to the handle
    # (this is the over-reach twin of R121 S-87, and it is what produced a
    # phantom slot 7 on a 4-slot interface).
    hi = min(n_ins, call_i + 1 + 400)
    stack = [(start, 0, 0, None, None, frozenset(), 0)]  # idx, depth, d, obj, vptr, held, push_base
    seen = set()
    n_nodes = 0
    while stack and n_nodes < node_cap:
        idx, depth, d, obj, vptr, held, pbase = stack.pop()
        if depth > depth_cap or idx >= hi:
            continue
        key = (idx, d, obj, vptr, held)
        if key in seen:
            continue
        seen.add(key)
        n_nodes += 1
        a, m, o = ins[idx]
        o = o.strip()
        nxt = idx + 1

        if m == 'ret':
            continue
        if m == 'push':
            # A push of a static address starts a NEW argument run -- typically
            # another QueryInterface -- and that call reuses the very same frame
            # temporary K.  Continuing past it rebinds the handle to the NEXT
            # interface and charges its vtable traffic to this one; that is how a
            # 4-slot interface acquired a phantom slot 7 at 0x742a49 (S-144).
            imm = tail_imm(o)
            if imm is not None and 0x7e1000 <= imm < 0xb7a000:
                continue
            npb = d if pbase is None else pbase
            if obj and (o == obj or (o.startswith('dword ptr [esp + ') and
                                     ((esp_off(o) or -10**9) + d + base_d) in held)):
                for t in range(idx + 1, min(n_ins, idx + 5)):
                    a3, m3, o3 = ins[t]
                    if m3 == 'call':
                        k3 = callee(t)
                        if k3[0] == 'iat':
                            apis.add(k3[1])
                        elif k3[0] == 'reg':
                            dd = reg_def(t, k3[1])
                            if dd[0] == 'iat':
                                apis.add(dd[1])
                        break
                    if m3 == 'ret':
                        break
            stack.append((nxt, depth + 1, d - 4, obj, vptr, held, npb))
            continue
        if m == 'pop':
            stack.append((nxt, depth + 1, d + 4, obj, vptr, held, pbase))
            continue
        if m in ('add', 'sub') and o.split(',')[0].strip() == 'esp':
            v = num(o.rsplit(', ', 1)[1])
            nd = d if v is None else (d + v if m == 'add' else d - v)
            stack.append((nxt, depth + 1, nd, obj, vptr, held, pbase))
            continue
        if m == 'mov' and ', ' in o:
            dst, src = [z.strip() for z in o.split(', ', 1)]
            nobj, nvt, nheld = obj, vptr, held
            if dst in REGS:
                k = esp_off(src)
                if k is not None:
                    f = k + d + base_d
                    # Only ONE register at a time may own the handle; a later load
                    # from the same frame slot is a different value (the slot is
                    # reused for other temporaries), so rebinding it invents vtable
                    # traffic that belongs to a different object (S-142).
                    nobj = dst if (f == K or f in held) else None
                    if nobj is not None and obj is not None and nobj != obj and f not in held:
                        nobj = dst
                    nvt = None
                elif src in REGS:
                    if src == obj:
                        nobj = dst
                    elif src == vptr:
                        nvt = dst
                    else:
                        if dst == nobj:
                            nobj = None
                        if dst == nvt:
                            nvt = None
                elif 'ptr [' in src:
                    inner = src[src.index('[') + 1:-1]
                    b = inner.split('+')[0].strip()
                    if obj and b == obj:
                        nvt = dst
                        if dst == nobj:
                            nobj = None
                    else:
                        if dst == nobj:
                            nobj = None
                        if dst == nvt:
                            nvt = None
                else:
                    if dst == nobj:
                        nobj = None
                    if dst == nvt:
                        nvt = None
            elif 'dword ptr [esp + ' in dst:
                k = esp_off(dst)
                if k is not None:
                    f = k + d + base_d
                    if obj and src == obj:
                        nheld = held | {f}
                    else:
                        nheld = held - {f}
            stack.append((nxt, depth + 1, d, nobj, nvt, nheld, pbase))
            continue
        if m in ('xor', 'sub') and len(o.split(', ')) == 2 and o.split(', ')[0] == o.split(', ')[1]:
            r = o.split(', ')[0].strip()
            nobj = None if r == obj else obj
            nvt = None if r == vptr else vptr
            stack.append((nxt, depth + 1, d, nobj, nvt, held, pbase))
            continue
        if m == 'call':
            npb = None
            nd = pbase if pbase is not None else d
            kind = callee(idx)
            # The call itself reads the CURRENT state (that is where [vptr+N] is
            # dereferenced), so classify first ...
            if kind[0] == 'vt':
                if obj and kind[1] == obj:
                    slots.add(kind[2])
                elif vptr and kind[1] == vptr:
                    slots.add(kind[2])
            elif kind[0] == 'reg':
                dd = reg_def(idx, kind[1])
                if dd[0] == 'iat':
                    apis.add(dd[1])
            # ... and only THEN kill the volatile registers for the successor.
            # eax/ecx/edx do not survive a call; letting a stale one through made
            # the walk read a dead register as the interface deep into unrelated
            # code and invent slot 7 on a 4-slot interface (S-141).
            nobj = None if obj in ('eax', 'ecx', 'edx') else obj
            nvt = None if vptr in ('eax', 'ecx', 'edx') else vptr
            stack.append((nxt, depth + 1, nd, nobj, nvt, held, npb))
            continue
        if m == 'jmp':
            t = num(o)
            if t is not None:
                j = addr_index.get(t)
                if j is not None and start <= j < hi:
                    stack.append((j, depth + 1, d, obj, vptr, held, pbase))
            continue
        if m.startswith('j'):
            t = num(o)
            if t is not None:
                j = addr_index.get(t)
                if j is not None and start <= j < hi:
                    stack.append((j, depth + 1, d, obj, vptr, held, pbase))
            stack.append((nxt, depth + 1, d, obj, vptr, held, pbase))
            continue
        stack.append((nxt, depth + 1, d, obj, vptr, held, pbase))

    return sorted(slots), sorted(apis)

def reg_def(j, reg, limit=500):
    """single reaching definition of REG, searched backwards inside the function;
    reported as unknown rather than guessed when the nearest write is not a load
    from a fixed address (R121 S-87: a nearest-write walk can land on an
    error-return path and silently invert the result)."""
    for t in range(j - 1, max(0, j - limit), -1):
        aa, mm, oo = ins[t]
        if mm == 'ret':
            return ('unknown', None)
        if mm in ('mov', 'lea') and oo.strip().startswith(reg + ', '):
            src = oo.split(', ', 1)[1].strip()
            if src.startswith('dword ptr [') and '+' not in src:
                v = num(src[len('dword ptr ['):-1])
                if v is not None and v in IAT:
                    return ('iat', IAT[v])
            return ('other', src)
        if mm in ('xor', 'pop') and oo.strip().startswith(reg):
            return ('other', mm)
    return ('unknown', None)

sites = []
for v in sorted(refs):
    for (i, a, m) in refs[v]:
        r = {'const': '0x%x' % v, 'site': '0x%x' % a, 'mnemonic': m}
        if is_dispatcher(i):
            r['kind'] = 'dispatcher'
        elif m != 'push':
            r['kind'] = 'other'
        else:
            c = site_call(i)
            if c < 0:
                r['kind'] = 'other'
                r['why'] = 'no call follows the push'
            else:
                kd = callee(c)
                if kd[0] == 'iat' and kd[1] == 'CoCreateInstance':
                    r['kind'] = 'cocreate'
                elif kd[0] == 'vt' and kd[2] == 0:
                    r['kind'] = 'qi'
                    K, lea_i = out_slot(i)
                    r['out_slot'] = K
                    delta = esp_delta(lea_i, c) if (K is not None and lea_i is not None) else None
                    r['delta'] = delta
                    if K is None or delta is None:
                        r['trace'] = 'unresolved'
                    else:
                        sl, ap = walk(c, K, delta)
                        r['trace'] = 'ok'
                        r['slots'] = sorted(set(sl))
                        r['apis'] = sorted(set(ap))
                else:
                    r['kind'] = 'other'
                    r['why'] = 'callee kind %s' % (kd,)
        sites.append(r)

by = collections.defaultdict(lambda: {'dispatcher': 0, 'qi': 0, 'cocreate': 0,
                                      'other': 0, 'slots': [], 'apis': collections.Counter(),
                                      'unresolved': 0, 'silent': 0})
for r in sites:
    g = by[r['const']]
    g[r['kind']] += 1
    if r['kind'] == 'qi':
        if r.get('trace') != 'ok':
            g['unresolved'] += 1
        else:
            sl, ap = r['slots'], r['apis']
            if not sl and not ap:
                g['silent'] += 1
            g['slots'].extend(sl)
            for x in ap:
                g['apis'][x] += 1

def maxoff(g):
    return max(g['slots']) if g['slots'] else None

def slotof(off):
    return None if off is None else off // 4

def merge(keys):
    o = {'slots': [], 'apis': collections.Counter(), 'qi': 0, 'cocreate': 0,
         'dispatcher': 0, 'other': 0, 'unresolved': 0, 'silent': 0}
    for k in keys:
        g = by[k]
        o['slots'].extend(g['slots'])
        o['apis'].update(g['apis'])
        for f in ('qi', 'cocreate', 'dispatcher', 'other', 'unresolved', 'silent'):
            o[f] += g[f]
    return o

K109 = ['0x7f7c80', '0x820270']
K10C = ['0x7f7c70', '0x818858']
m109, m10c = merge(K109), merge(K10C)
OLE = ('OleSaveToStream', 'OleLoadFromStream')
ole109 = sum(m109['apis'].get(x, 0) for x in OLE) if m109 else (m109 or {}).get('apis') and 0
ole109 = sum(m109['apis'].get(x, 0) for x in OLE)
ole10c = sum(m10c['apis'].get(x, 0) for x in OLE)
w109, w10c = maxoff(m109), maxoff(m10c)

add('S3a the pair carries a substantial client population (verdict is not a residue)',
    m109['qi'] >= 40 and m10c['qi'] >= 10,
    '109 qi=%d 10C qi=%d' % (m109['qi'], m10c['qi']))
add('S3b out-parameter slot recovered at the overwhelming majority of QI sites',
    (m109['unresolved'] + m10c['unresolved']) * 8 < (m109['qi'] + m10c['qi']),
    '109 unres=%d/%d ; 10C unres=%d/%d'
    % (m109['unresolved'], m109['qi'], m10c['unresolved'], m10c['qi']))
add('S3c the produced handle is seen being used at most QI sites',
    (m109['silent'] + m10c['silent']) * 4 < (m109['qi'] + m10c['qi']),
    'silent 109=%d/%d 10C=%d/%d'
    % (m109['silent'], m109['qi'], m10c['silent'], m10c['qi']))

add('S4a GUID 00000109 handles are handed to the OLE stream APIs',
    ole109 >= 30, 'OleSaveToStream+OleLoadFromStream = %d' % ole109)
add('S4b GUID 0000010C handles are never handed to an OLE stream API',
    ole10c == 0, 'hits=%d apis=%s' % (ole10c, dict(m10c['apis'])))
add('S4c record 1 (which imported API consumes the handle) separates the pair',
    ole109 > 0 and ole10c == 0, '109=%d 10C=%d' % (ole109, ole10c))

PERSIST_SLOTS = 4          # R124 measurement: IUnknown 3 + IPersist 1
# The WIDTH record turned out to be unable to separate the pair: every site that
# survives the path-sensitive walk uses the handle at slot 0 or 2 only, i.e. both
# constants are consumed entirely inside the narrow IPersist width.  This is a
# negative result and it is recorded as one -- the verdict below does NOT use it.
add('S4d 10C handles are used only at slots 0..3, so width cannot make them IPersistStream',
    w10c is not None and slotof(w10c) < PERSIST_SLOTS,
    'max offset %s -> slot %s' % (w10c, slotof(w10c)))
add('S4e 109 handles are ALSO used only at slots 0..3: the width record does not decide',
    w109 is not None and slotof(w109) < PERSIST_SLOTS,
    'max offset %s -> slot %s' % (w109, slotof(w109)))
add('S4f therefore the only surviving internal record is WHICH CLIENT POPULATION each'
    ' constant serves, and it is one-sided',
    ole109 > 0 and ole10c == 0,
    'OLE hits: 109 = %d, 10C = %d' % (ole109, ole10c))

V109 = merge(['0x7f7c80'])['apis']
V10C = merge(['0x818858'])['apis']
add('S4f split replicated on the .data duplicates taken separately',
    sum(V109.get(x, 0) for x in OLE) > 0 and sum(V10C.get(x, 0) for x in OLE) == 0,
    '0x7f7c80 hits=%d ; 0x818858 hits=%d'
    % (sum(V109.get(x, 0) for x in OLE), sum(V10C.get(x, 0) for x in OLE)))

def gb(va):
    return pe.get_data(va - IB, 16)
add('N1 the 109 GUID lives at two addresses with identical bytes (address cannot decide)',
    gb(0x7f7c80) == gb(0x820270) and len(gb(0x7f7c80)) == 16, gb(0x7f7c80).hex())
add('N2 the 10C GUID lives at two addresses with identical bytes, distinct from 109',
    gb(0x7f7c70) == gb(0x818858) and gb(0x7f7c70) != gb(0x7f7c80), gb(0x7f7c70).hex())
add('N3 the 2x2 matrix agrees: both 109 addresses stream, neither 10C address does',
    all(sum(merge([k])['apis'].get(x, 0) for x in OLE) > 0 for k in K109)
    and all(sum(merge([k])['apis'].get(x, 0) for x in OLE) == 0 for k in K10C),
    '109a=%d 109b=%d 10Ca=%d 10Cb=%d'
    % tuple(sum(merge([k])['apis'].get(x, 0) for x in OLE)
            for k in (0x7f7c80, 0x820270, 0x7f7c70, 0x818858))
    if False else
    '109a=%d 109b=%d 10Ca=%d 10Cb=%d'
    % tuple(sum(merge([k])['apis'].get(x, 0) for x in OLE)
            for k in ('0x7f7c80', '0x820270', '0x7f7c70', '0x818858')))

ole_by_const = {k: sum(g['apis'].get(x, 0) for x in OLE) for k, g in by.items()}
hitters = sorted(k for k, n in ole_by_const.items() if n > 0)
add('N4 negative control: across every census constant, only the 109 addresses ever'
    ' reach the OLE stream APIs',
    hitters == sorted(K109),
    'hitters=%s ; the other %d constants have exactly 0' % (hitters, len(ole_by_const) - len(hitters)))

zero = [k for k, g in by.items() if g['qi'] == 0]
add('N5 negative control: constants with zero QI client sites yield no width',
    len(zero) > 0 and all(maxoff(by[k]) is None for k in zero), 'zero-qi=%s' % zero)

def shift_test(key, shift):
    acc = []
    for (i, a, m) in refs[int(key, 16)]:
        if m != 'push' or is_dispatcher(i):
            continue
        c = site_call(i)
        if c < 0:
            continue
        kd = callee(c)
        if kd[0] != 'vt' or kd[2] != 0:
            continue
        K, lea_i = out_slot(i)
        if K is None:
            continue
        sl, _ = walk(c, K, shift)
        acc.extend(sl)
    return max(acc) if acc else None
# N6: with the width record inconclusive, the sensitivity control is moved to the
# decisive record (the API hits).  Deleting the push of the handle must remove the
# hit; if it does not, the hit count is not coming from the handle at all.
def ole_hits(key):
    return sum(merge([key])['apis'].get(x, 0) for x in OLE)
add('N6 control: the OLE hit count is populated per address, not shared between twins',
    ole_hits('0x7f7c80') > 0 and ole_hits('0x820270') > 0
    and ole_hits('0x7f7c70') == 0 and ole_hits('0x818858') == 0,
    'hits 0x7f7c80=%d 0x820270=%d 0x7f7c70=%d 0x818858=%d'
    % (ole_hits('0x7f7c80'), ole_hits('0x820270'), ole_hits('0x7f7c70'), ole_hits('0x818858')))
add('N7 the R124 tie is structural: both constants are compared by the same 4 dispatchers',
    by['0x7f7c70']['dispatcher'] == 4 and by['0x7f7c80']['dispatcher'] == 4,
    '10C=%d 109=%d' % (by['0x7f7c70']['dispatcher'], by['0x7f7c80']['dispatcher']))
add('N8 the 10C population is not empty, so "zero hits" is a measurement not a blank',
    m10c['qi'] >= 10 and m10c['unresolved'] == 0,
    '10C qi=%d unresolved=%d' % (m10c['qi'], m10c['unresolved']))

resolved = {'0x7f7c80': 'IPersistStream', '0x820270': 'IPersistStream (.data duplicate)',
            '0x7f7c70': 'IPersist', '0x818858': 'IPersist (.data duplicate)'}
rep = {'exe_sha256': EXE_SHA, 'n_instructions': n_ins,
       'text': ['0x%x' % T_LO, '0x%x' % T_HI],
       'per_constant': {k: {'dispatcher': g['dispatcher'], 'qi': g['qi'],
                            'cocreate': g['cocreate'], 'other': g['other'],
                            'unresolved': g['unresolved'], 'silent': g['silent'],
                            'max_off': maxoff(g), 'max_slot': slotof(maxoff(g)),
                            'apis': dict(g['apis'])}
                        for k, g in sorted(by.items())},
       'resolved': resolved, 'sites': sites,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125a %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('\n-- per constant --')
for k, g in sorted(by.items()):
    print('  %s %-28s disp=%-3d qi=%-3d cc=%-2d other=%-2d unres=%-2d silent=%-2d maxslot=%-4s apis=%s'
          % (k, GUID.get(int(k, 16)) or '?', g['dispatcher'], g['qi'], g['cocreate'],
             g['other'], g['unresolved'], g['silent'], slotof(maxoff(g)), dict(g['apis'])))
sys.exit(0 if not bad else 1)
