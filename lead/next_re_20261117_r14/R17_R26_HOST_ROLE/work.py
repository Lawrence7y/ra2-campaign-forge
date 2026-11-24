#!/usr/bin/env python3
# R17-R26-HOST-ROLE: bounded static, read-only PE/RTTI/disassembly work.
import hashlib, struct, json, os, string
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

IMG = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R26_HOST_ROLE")
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
FSTART, FEND = 0x5A6510, 0x5A691C
TARGET = 0x5A6510

b = IMG.read_bytes()
sha = hashlib.sha256(b).hexdigest().upper()
if sha != EXPECT:
    raise SystemExit("SHA MISMATCH " + sha)
pe = pefile.PE(data=b)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    n = s.Name.decode('latin1').rstrip('\0')
    secs[n] = dict(va=IB+s.VirtualAddress, rva=s.VirtualAddress, raw=s.PointerToRawData, size=s.SizeOfRawData, vsize=s.Misc_VirtualSize)
text, rdata, data = secs['.text'], secs['.rdata'], secs['.data']

def off_va(va):
    r = va - IB
    for n,s in secs.items():
        if s['rva'] <= r < s['rva']+s['size']:
            return s['raw']+(r-s['rva'])
    return None

def sec_va(va):
    r = va - IB
    for n,s in secs.items():
        if s['rva'] <= r < s['rva']+s['size']:
            return n
    return None

def u32_off(o):
    return struct.unpack_from('<I', b, o)[0] if o is not None and 0 <= o and o+4 <= len(b) else None

def u32_va(va):
    return u32_off(off_va(va))

def cstr(va, maxlen=256):
    o = off_va(va)
    if o is None: return None
    j = o
    while j < min(len(b), o+maxlen) and b[j] != 0: j += 1
    if j == o or j >= min(len(b), o+maxlen): return None
    s = b[o:j]
    if all(0x20 <= c < 0x7f for c in s):
        return s.decode('ascii')
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# Bounded function disassembly, anchored at nominal entry.
code_lo, code_hi = text['va'], text['va']+text['vsize']
fo, fe = off_va(FSTART), off_va(FEND)
assert fo is not None and fe is not None and fe-fo == FEND-FSTART
ins = list(md.disasm(b[fo:fe], FSTART))
lines=[]
lines.append(f'IMAGE {IMG}')
lines.append(f'SHA256 {sha}')
lines.append(f'ANCHOR_PRE_5A6500_5A650F {b[off_va(0x5A6500):off_va(0x5A6510)].hex(" ")}')
lines.append(f'ANCHOR_FUNCTION_FIRST_16 {b[fo:fo+16].hex(" ")}')
lines.append(f'ANCHOR_END_LAST_16 {b[fe-16:fe].hex(" ")}')
for x in ins:
    ops = x.op_str
    lines.append(f'{x.address:08X}  {x.bytes.hex():<20}  {x.mnemonic:<7} {ops}')
(OUT/'disasm.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

# Immediate/absolute string references inside bounded function.
strrefs=[]
for x in ins:
    for op in x.operands:
        cand=[]
        if op.type == CS_OP_IMM: cand.append(op.imm)
        elif op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp: cand.append(op.mem.disp)
        for v in cand:
            s = cstr(v)
            if s and len(s) >= 3:
                strrefs.append((hex(x.address), hex(v), s, x.mnemonic+' '+x.op_str))

# Direct E8 rel32 calls anywhere in raw .text.
tcode = b[text['raw']:text['raw']+text['size']]
call_sites=[]
for i in range(len(tcode)-4):
    if tcode[i] != 0xE8: continue
    site = text['va']+i
    rel = struct.unpack_from('<i', tcode, i+1)[0]
    dst = site+5+rel
    if dst == TARGET:
        call_sites.append(dict(site=site, bytes=tcode[i:i+5].hex(), dst=dst))

# Candidate function starts for caller-entry bounded disassembly.
starts={text['va']}
call_targets=set()
for i in range(len(tcode)-4):
    if tcode[i] != 0xE8: continue
    site=text['va']+i; rel=struct.unpack_from('<i',tcode,i+1)[0]; dst=site+5+rel
    if code_lo <= dst < code_hi: call_targets.add(dst)
starts.update(call_targets)
i=0
while i < len(tcode)-3:
    if tcode[i] in (0x90,0xCC):
        c=tcode[i]; j=i
        while j < len(tcode) and tcode[j]==c: j+=1
        if (c==0x90 and j-i>=4) or (c==0xCC and j-i>=2):
            if text['va']+j < code_hi: starts.add(text['va']+j)
        i=j
    else: i+=1
starts=sorted(s for s in starts if code_lo <= s < code_hi)
caller_lines=[]; caller_bytes=0; caller_asserts=[]
for cs in call_sites:
    prior=[s for s in starts if s <= cs['site']]
    host=max(prior) if prior else text['va']
    end=cs['site']+5
    o=off_va(host); q=off_va(end)
    sub=list(md.disasm(b[o:q], host, count=100000))
    hit=[x for x in sub if x.address==cs['site']]
    caller_asserts.append((hex(host),hex(cs['site']),bool(hit)))
    caller_lines.append(f'CALLER {host:08X} -> SITE {cs["site"]:08X}')
    for x in sub:
        caller_lines.append(f'{x.address:08X}  {x.bytes.hex():<20}  {x.mnemonic:<7} {x.op_str}')
    caller_bytes += q-o
(OUT/'caller_entries.txt').write_text('\n'.join(caller_lines)+'\n',encoding='utf-8')

# Vtable enumeration through vtable[-4] -> COL -> pTD -> TD+8 name.
printable=bytes(range(0x20,0x7f))
td={}
raw_da, end_da = data['raw'], data['raw']+data['size']
for o in range(raw_da, end_da-8):
    if not b[o:o+3] == b'.?A': continue
    j=o+3
    while j < end_da and b[j] in printable and j-o < 300: j+=1
    if j >= end_da or b[j] != 0 or j-o < 8: continue
    name_va = IB+data['rva']+(o-raw_da)
    tdva = name_va-8
    vf = u32_va(tdva); spare = u32_va(tdva+4)
    if vf == 0x7F9594 and spare == 0:
        td.setdefault(tdva, b[o:j].decode('ascii'))
col={}; td_name_by_va=td.copy()
raw_rd, end_rd = rdata['raw'], rdata['raw']+rdata['size']
for o in range(raw_rd, end_rd-24, 4):
    ptd = u32_off(o+12)
    if ptd not in td: continue
    cd = u32_off(o+16)
    co = off_va(cd) if cd is not None else None
    if co is None or co+16 > len(b): continue
    sig, attr, nbases, basearr = struct.unpack_from('<IIII', b, co)
    if sig == 0 and attr < 0x100 and 0 < nbases < 0x1000 and off_va(basearr) is not None:
        col.setdefault(IB+rdata['rva']+(o-raw_rd), td[ptd])
vtables=[]; hits=[]; total_slots=0; vtables_with_slots=0
for o in range(raw_rd, end_rd-4, 4):
    c = u32_off(o)
    if c not in col: continue
    vbase = IB+rdata['rva']+(o-raw_rd+4)
    vo = off_va(vbase)
    if vo is None or vo < raw_rd or vo >= end_rd: continue
    n=0; p=vo
    while p+4 <= end_rd:
        v=u32_off(p)
        if v is None or not (code_lo <= v < code_hi): break
        if v == TARGET:
            hits.append(dict(vtable=hex(vbase), slot=n, slot_va=hex(IB+rdata['rva']+(p-raw_rd)), class_name=col[c], col=hex(c), ptd=hex(ptd)))
        n+=1; p+=4
    total_slots += n
    if n: vtables_with_slots += 1
    vtables.append(dict(vtable=hex(vbase), slots=n, class_name=col[c], col=hex(c), vtable_minus4=hex(c)))
raw_target = struct.pack('<I', TARGET)
raw_rdata_hits=[]
for o in range(raw_rd, end_rd-3, 4):
    if b[o:o+4] == raw_target: raw_rdata_hits.append(hex(IB+rdata['rva']+(o-raw_rd)))

with (OUT/'vtable_hits.tsv').open('w',encoding='utf-8',newline='') as f:
    f.write('vtable_va\tslot\tslot_va\tclass_name\tcol\tchain\n')
    for h in hits:
        f.write(f"{h['vtable']}\t{h['slot']}\t{h['slot_va']}\t{h['class_name']}\t{h['col']}\tvtable[-4]->COL->pTD->TD+8\n")
with (OUT/'callers.tsv').open('w',encoding='utf-8',newline='') as f:
    f.write('site\tbytes\ttarget\tcaller_entry\tinstruction_boundary\n')
    for c,a in zip(call_sites,caller_asserts):
        f.write(f"{c['site']:08X}\t{c['bytes']}\t{c['dst']:08X}\t{a[0]}\t{'PASS' if a[2] else 'FAIL'}\n")

result=dict(
 image=str(IMG), sha256=sha, image_base=hex(IB),
 text=dict(va=hex(text['va']), scan_bytes=text['size']),
 rdata=dict(va=hex(rdata['va']), scan_bytes=end_rd-raw_rd),
 data=dict(va=hex(data['va']), scan_bytes=end_da-raw_da),
 function=dict(start=hex(FSTART), end=hex(FEND), bytes=FEND-FSTART, instructions=len(ins),
               first_anchor=b[fo:fo+16].hex(), last_anchor=b[fe-16:fe].hex(),
               rets=[(hex(x.address),x.bytes.hex()) for x in ins if x.mnemonic.startswith('ret')]),
 direct_call_sites=[dict(site=hex(c['site']),bytes=c['bytes'],target=hex(c['dst'])) for c in call_sites],
 caller_disasm_bytes=caller_bytes,
 caller_asserts=[[a[0],a[1],a[2]] for a in caller_asserts],
 td_count=len(td), col_count=len(col), vtable_count=len(vtables), vtables_with_slots=vtables_with_slots, total_slot_values_scanned=total_slots, raw_rdata_dword_hits=raw_rdata_hits, vtable_hits=hits,
 string_refs=strrefs,
)
(OUT/'_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
