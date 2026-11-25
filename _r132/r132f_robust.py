#!/usr/bin/env python3
# R132 r132f: robustness of the "exactly two instantiations" claim + if-arm signature census.
#
# Two independent ways a third copy could hide from r132b's mask:
#   (a) it differs in an immediate OTHER than the three IID pushes (e.g. a different
#       vtable offset or a different dwClsContext constant baked in) -> so mask ALL imm32;
#   (b) only the if-arm (CoCreateInstance immediately followed by OleRun) was inlined
#       somewhere, not the whole 136-byte body.
# Both are censused here. Also fixes my r132e mislabel: the LAST push before a stdcall
# call is the FIRST argument, not the third.
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r132/r132f_robust.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress,
                base + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData), s)
tlo, thi, ts = secs['.text']
data = ts.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32)

LEN = 136
A0 = 0x6bedb0
body = data[A0 - tlo:A0 - tlo + LEN]
R = {'body_len': LEN}

# ---------- (a) mask EVERY immediate byte inside the body ----------
msk = bytearray(LEN)
imm_fields = []
for i in md.disasm(body, A0):
    if i.op_str and '0x' in i.op_str:
        # find trailing hex literal(s); mark the last 4 bytes of the instruction if imm32
        for tok in i.op_str.replace(',', ' ').replace('[', ' ').replace(']', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if v > 0xff:                       # imm32, not imm8
                    rel = (i.address - A0) + i.size - 4
                    if 0 <= rel <= LEN - 4:
                        imm_fields.append({'insn': hex(i.address), 'rel': hex(rel), 'v': hex(v)})
                        for k in range(rel, rel + 4):
                            msk[k] = 1
R['all_imm32_fields'] = imm_fields
R['masked_bytes_all_imm'] = sum(msk)
print('imm32 fields:', len(imm_fields), 'masked bytes:', sum(msk), 'of', LEN)

def find_masked(pat, m):
    out = []
    L = len(pat)
    i = 0
    while i <= len(data) - L:
        if data[i] != pat[0]:
            i += 1
            continue
        ok = True
        for j in range(L):
            if m[j]:
                continue
            if data[i + j] != pat[j]:
                ok = False
                break
        if ok:
            out.append(tlo + i)
            i += L
        else:
            i += 1
    return out

hits_all_imm = find_masked(body, msk)
R['instantiations_all_imm_masked'] = [hex(h) for h in hits_all_imm]
print('instantiations with ALL imm32 masked:', [hex(h) for h in hits_all_imm])

# ---------- (b) if-arm signature: call CoCreateInstance then call OleRun nearby ----------
ccis = bytes.fromhex('ff15fc157e00')
oler = bytes.fromhex('ff1500167e00')
sig = []
for p in range(len(data) - 6):
    if data[p:p + 6] == ccis:
        # look for OleRun within the next 60 bytes
        w = data[p + 6:p + 6 + 60]
        q = w.find(oler)
        if q >= 0:
            sig.append(tlo + p)
R['ifarm_signature_sites'] = [hex(s) for s in sig]
print('if-arm signature (CoCreateInstance..OleRun within 60B):', len(sig), [hex(s) for s in sig])

# ---------- the 7 OleRun sites and whether each sits in a template body ----------
oler_sites = []
p = 0
while True:
    p = data.find(oler, p)
    if p < 0:
        break
    oler_sites.append(tlo + p)
    p += 1
R['olerun_sites'] = [hex(s) for s in oler_sites]
bodies = {A0: 136, 0x41c250: 136}
in_body = []
for s in oler_sites:
    for b, ln in bodies.items():
        if b <= s < b + ln:
            in_body.append({'site': hex(s), 'body': hex(b)})
R['olerun_in_template_body'] = in_body
print('OleRun sites:', [hex(s) for s in oler_sites])
print('  of which inside a template body:', in_body)

ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + ((' [%s]' % d) if d else ''))
chk('all-imm mask still yields exactly 2', len(R['instantiations_all_imm_masked']) == 2,
    len(R['instantiations_all_imm_masked']))
chk('if-arm signature sites found=7', len(R['ifarm_signature_sites']) == 7,
    len(R['ifarm_signature_sites']))
chk('7 OleRun sites total', len(R['olerun_sites']) == 7, len(R['olerun_sites']))
chk('only 2 OleRun sites inside a template body', len(R['olerun_in_template_body']) == 2,
    len(R['olerun_in_template_body']))
json.dump(ASSERT, open(OUT.replace('.json','_assert.json'),'w'), ensure_ascii=False, indent=1)
print('assertions:', len(ASSERT), 'FAIL', sum(1 for a in ASSERT if not a['pass']))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('wrote', OUT)
