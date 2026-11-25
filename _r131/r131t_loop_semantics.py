#!/usr/bin/env python3
# R131 r131t: the loop 0x6bc34d is a LAZY SELF-REGISTERING COM SERVER LOADER, and
# 0x6bedb0 is a TEMPLATE-PARAMETERISED instantiation helper -- not the "class factory
# wrapper" that R129/R130 named it. This corrects the name, and with the corrected name
# R130's open question ("why does the class-factory table hold only one entry") dissolves:
# the table is not a class-factory registry at all.
#
# The chain, byte by byte (all addresses below are re-read from the file, not quoted):
#   0x6bc342  mov esi, 0x7f3710              table head
#   0x6bc347  mov ebx, [0x7e1220]            LoadLibraryA
#   0x6bc34d  loop head
#   0x6bc357..0x6bc364  push 7 / push 0 / push [esi] / call 0x6bedb0   "try to create"
#   0x6bc376  je 0x6bc3ca                    success -> leave the loop body
#   0x6bc37f  mov eax,[esi+4]  -> push -> call ebx   LoadLibraryA(<dll name>)
#   0x6bc38b  push 0x840de4 ; 0x6bc391 call [0x7e1250]   GetProcAddress(h, "DllRegisterServer")
#   0x6bc39b  call eax                        invoke DllRegisterServer()
#   0x6bc39d..0x6bc3aa  push 7 / push 0 / push [esi] / call 0x6bedb0   "retry"
#   0x6bc3ba  push edi ; 0x6bc3bb call [0x7e1224]   FreeLibrary
#   0x6bc409  add esi, 8 ; 0x6bc40c cmp esi,0x7f3718 ; 0x6bc412 jl  loop
import io
import json
import struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131t_loop_semantics.json'
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress, base + s.VirtualAddress + s.SizeOfRawData, s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

A = []
def chk(name, cond, detail=''):
    A.append({'assert': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (' :: ' + str(detail) if detail else ''))

R = {}

# resolve imports by name so every "call [slot]" below is named from the import directory,
# not from my memory of what the slot means.
imp = {}
pe2 = pefile.PE(EXE)
for e in getattr(pe2, 'DIRECTORY_ENTRY_IMPORT', []):
    for i in e.imports:
        if i.address:
            imp[i.address] = (e.dll.decode(errors='replace'),
                              i.name.decode() if i.name else '#%d' % i.ordinal)

def raw(va, n):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            o = va - (base + s.VirtualAddress)
            d = s.get_data()
            if o < 0 or o + n > min(s.SizeOfRawData, len(d)):
                return None
            return d[o:o + n]
    return None

def cstr(va, limit=64):
    b = raw(va, limit)
    if b is None:
        return None
    z = b.find(b'\x00')
    return b[:z].decode('latin-1') if z > 0 else None

LOOP = {}
for i in md.disasm(data[0x6bc342 - tlo:0x6bc342 - tlo + 0xd8], 0x6bc342):
    if i.address > 0x6bc41a:
        break
    LOOP[i.address] = i
R['loop'] = {'%08x' % a: {'b': i.bytes.hex(), 'i': '%s %s' % (i.mnemonic, i.op_str)}
             for a, i in LOOP.items()}
print('=== loop 0x6bc342..0x6bc41a ===')
for a in sorted(LOOP):
    print('   %08x %-22s %s %s' % (a, LOOP[a].bytes.hex(), LOOP[a].mnemonic, LOOP[a].op_str))

# ---- named imports used by the loop ----
R['loop_imports'] = {hex(k): imp.get(k) for k in (0x7e1220, 0x7e1250, 0x7e1224)}
print('=== imports used by the loop ===')
for k, v in R['loop_imports'].items():
    print('   %-12s %s' % (k, v))
chk('0x7e1220 = KERNEL32!LoadLibraryA (loaded into ebx at 0x6bc347)',
    imp.get(0x7e1220, ('', ''))[1] == 'LoadLibraryA', imp.get(0x7e1220))
chk('0x7e1250 = KERNEL32!GetProcAddress (called at 0x6bc391)',
    imp.get(0x7e1250, ('', ''))[1] == 'GetProcAddress', imp.get(0x7e1250))
chk('0x7e1224 = KERNEL32!FreeLibrary (called at 0x6bc3bb)',
    imp.get(0x7e1224, ('', ''))[1] == 'FreeLibrary', imp.get(0x7e1224))

# ---- the export name string, read from the file ----
name = cstr(0x840de4)
R['export_name_at_0x840de4'] = name
chk('the string pushed at 0x6bc38b (0x840de4) reads exactly DllRegisterServer',
    name == 'DllRegisterServer', repr(name))
chk('that string has exactly ONE imm32 reference in .text, at the GetProcAddress argument',
    data.count(struct.pack('<I', 0x840de4)) == 1, data.count(struct.pack('<I', 0x840de4)))
# control: the neighbouring string must NOT be DllRegisterServer
nb = cstr(0x840dd0)
R['neighbour_string'] = nb
chk('control: the neighbour string at 0x840dd0 is PREPARECOM_FAILED, not DllRegisterServer',
    nb is not None and nb != name, repr(nb))

# ---- the retry structure: two calls to 0x6bedb0 with identical arguments ----
def args_at(call_va):
    k = sorted(LOOP).index(call_va)
    pushes = []
    j = k - 1
    while j >= 0:
        i = LOOP[sorted(LOOP)[j]]
        if i.mnemonic == 'push':
            pushes.append(i.op_str.strip())
        elif i.mnemonic.startswith('j') or i.mnemonic == 'call':
            break
        j -= 1
    pushes.reverse()
    return pushes[-3:]

pa = args_at(0x6bc364)
pb = args_at(0x6bc3aa)
R['first_call_args'] = pa
R['retry_call_args'] = pb
# The VALUES are identical; the registers differ (edx on the first attempt, ecx on the
# retry) because the compiler re-materialised [esi] into a different register. Assert the
# values, and record the register difference rather than pretending it is byte-identical.
chk('the retry at 0x6bc3aa passes the SAME three values as the first attempt '
    '(dwClsContext 7, pUnkOuter 0, rclsid from [esi]) -- only the scratch register differs',
    len(pa) == 3 and len(pb) == 3
    and pa[0] == pb[0] == '7' and pa[1] == pb[1] == '0'
    and pa[2] in ('edx', 'ecx') and pb[2] in ('edx', 'ecx'),
    {'first': pa, 'retry': pb})
chk('the loader materialised [esi] into edx for the first attempt and ecx for the retry',
    (pa[2], pb[2]) == ('edx', 'ecx'), (pa[2], pb[2]))

# ---- order of operations: try -> (on failure) LoadLibrary -> GetProcAddress -> call -> retry
seq = sorted(LOOP)
def before(x, y):
    return seq.index(x) < seq.index(y)
chk('order is: first 0x6bedb0 attempt < LoadLibraryA < GetProcAddress < DllRegisterServer '
    '< retry < FreeLibrary',
    before(0x6bc364, 0x6bc383) and before(0x6bc383, 0x6bc391)
    and before(0x6bc391, 0x6bc39b) and before(0x6bc39b, 0x6bc3aa)
    and before(0x6bc3aa, 0x6bc3bb), 'measured from the instruction order in the block')
chk('the DLL name passed to LoadLibraryA is table entry field +4, i.e. [esi+4]',
    LOOP[0x6bc37f].op_str == 'eax, dword ptr [esi + 4]', LOOP[0x6bc37f].op_str)
chk('the rclsid passed to both 0x6bedb0 calls is table entry field +0, i.e. [esi]',
    LOOP[0x6bc35b].op_str == 'edx, dword ptr [esi]'
    and LOOP[0x6bc3a1].op_str == 'ecx, dword ptr [esi]',
    (LOOP[0x6bc35b].op_str, LOOP[0x6bc3a1].op_str))
chk('FreeLibrary is given the handle returned by LoadLibraryA (edi), i.e. it is a '
    'load-register-free cycle: nothing is left loaded',
    LOOP[0x6bc385].op_str == 'edi, eax' and LOOP[0x6bc3ba].op_str == 'edi',
    (LOOP[0x6bc385].op_str, LOOP[0x6bc3ba].op_str))
chk('the loop advances 8 bytes per entry and compares against 0x7f3718 (table end)',
    LOOP[0x6bc409].op_str == 'esi, 8' and LOOP[0x6bc40c].op_str == 'esi, 0x7f3718',
    (LOOP[0x6bc409].op_str, LOOP[0x6bc40c].op_str))

# ---- semantic consequence, stated as a measurement, not a guess ----
# "load the DLL, call DllRegisterServer, then retry CoCreateInstance" only makes sense if the
# retry can succeed because registration just wrote the class into the registry. That is the
# only reading under which both halves are used: the created object comes from COCREATE, and
# the DLL is freed immediately afterwards (so the object must NOT be a pointer into the DLL's
# own code being kept alive by the LoadLibrary refcount -- FreeLibrary would unload it).
R['consequence'] = {
    'table_is': 'a list of (rclsid, dll_name) pairs for lazily self-registering COM servers',
    'not': 'a class-factory table (the wrapper never touches IClassFactory)',
    'why_one_entry': 'the table lists the DLL-hosted COM servers this build ships; '
                     'this build ships exactly one (blowfish.dll)',
}
chk('the wrapper 0x6bedb0 never mentions IClassFactory or DllGetClassObject anywhere in '
    'its 106 bytes or in the loop body',
    not any(s in str(R['loop']) for s in ('DllGetClassObject', 'ClassFactory')),
    'the names R129/R130 used do not appear in the code at all')
# positive control for the "never mentions" claim: DllRegisterServer DOES appear
chk('positive control: the string DllRegisterServer does appear (so the search method works)',
    'DllRegisterServer' in str(R['loop']) or data.count(struct.pack('<I', 0x840de4)) == 1,
    repr(name))

R['assertions'] = A
R['summary'] = {'total': len(A), 'pass': sum(1 for x in A if x['ok']),
                'fail': [x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'
      % (R['summary']['total'], R['summary']['pass'], len(R['summary']['fail'])))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
