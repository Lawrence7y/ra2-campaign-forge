#!/usr/bin/env python3
# R17-R29-UPSTREAM: bounded static, read-only PE/RTTI/disassembly work for 0x5A5020.
# Only reads gamemd.exe; writes artifacts into R17_R29_UPSTREAM.
import hashlib, struct, json
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

IMG = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R29_UPSTREAM")
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
TARGET = 0x5A5020
FSTART, FEND = 0x5A5020, 0x5A5323

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

code_lo, code_hi = text['va'], text['va']+text['vsize']
fo, fe = off_va(FSTART), off_va(FEND)
assert fo is not None and fe is not None and fe-fo == FEND-FSTART
ins = list(md.disasm(b[fo:fe], FSTART))

# ---- disasm.txt (anchor aligned) ----
lines=[]
lines.append(f'IMAGE {IMG}')
lines.append(f'SHA256 {sha}')
lines.append(f'ANCHOR_PRE_5A5010_5A501F {b[off_va(0x5A5010):off_va(0x5A5020)].hex(" ")}')
lines.append(f'ANCHOR_FUNCTION_FIRST_16 {b[fo:fo+16].hex(" ")}')
lines.append(f'ANCHOR_END_LAST_16 {b[fe-16:fe].hex(" ")}')
for x in ins:
    lines.append(f'{x.address:08X}  {x.bytes.hex():<20}  {x.mnemonic:<7} {x.op_str}')
(OUT/'disasm.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

# ---- string refs inside bounded function ----
strrefs=[]
for x in ins:
    for op in x.operands:
        cand=[]
        if op.type == CS_OP_IMM: cand.append(op.imm)
        elif op.type == CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp: cand.append(op.mem.disp)
        for v in cand:
            s = cstr(v)
            if s and len(s) >= 3:
                strrefs.append(dict(site=hex(x.address), va=hex(v), s=s, ins=x.mnemonic+' '+x.op_str))

# ---- direct E8 rel32 calls to TARGET anywhere in raw .text ----
tcode = b[text['raw']:text['raw']+text['size']]
call_sites=[]
for i in range(len(tcode)-4):
    if tcode[i] != 0xE8: continue
    site = text['va']+i
    rel = struct.unpack_from('<i', tcode, i+1)[0]
    dst = site+5+rel
    if dst == TARGET:
        call_sites.append(dict(site=site, bytes=tcode[i:i+5].hex(), dst=dst))

# ---- trusted entry set: .text start + all in-range E8 call targets + post-padding ----
# (NO C3/C2 byte scanning; padding runs only 90x4+ / CCx2+)
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

caller_lines=[]; caller_bytes=0; caller_asserts=[]; host_rows=[]
for cs in call_sites:
    prior=[s for s in starts if s <= cs['site']]
    host=max(prior) if prior else text['va']
    end=cs['site']+5
    o=off_va(host); q=off_va(end)
    sub=list(md.disasm(b[o:q], host, count=100000))
    hit=[x for x in sub if x.address==cs['site']]
    boundary=bool(hit)
    caller_asserts.append((hex(host),hex(cs['site']),boundary))
    host_rows.append(dict(site=hex(cs['site']), bytes=cs['bytes'], target=hex(cs['dst']), host=hex(host), boundary=boundary, host_disasm_bytes=q-o))
    caller_lines.append(f'CALLER {host:08X} -> SITE {cs["site"]:08X}  boundary={"PASS" if boundary else "FAIL"}')
    for x in sub:
        caller_lines.append(f'{x.address:08X}  {x.bytes.hex():<20}  {x.mnemonic:<7} {x.op_str}')
    caller_lines.append('')
    caller_bytes += q-o
(OUT/'caller_entries.txt').write_text('\n'.join(caller_lines)+'\n',encoding='utf-8')

# ---- vtable enumeration vtable[-4]->COL->pTD->TD+8 name ----
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
col={}
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
            hits.append(dict(vtable=hex(vbase), slot=n, slot_va=hex(IB+rdata['rva']+(p-raw_rd)), class_name=col[c], col=hex(c)))
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
    f.write('site\tbytes\ttarget\thost\tinstruction_boundary\thost_disasm_bytes\n')
    for h in host_rows:
        f.write(f"{h['site']}\t{h['bytes']}\t{h['target']}\t{h['host']}\t{'PASS' if h['boundary'] else 'FAIL'}\t{h['host_disasm_bytes']}\n")

result=dict(
 image=str(IMG), sha256=sha, image_base=hex(IB),
 text=dict(va=hex(text['va']), scan_bytes=text['size']),
 rdata=dict(va=hex(rdata['va']), scan_bytes=end_rd-raw_rd),
 data=dict(va=hex(data['va']), scan_bytes=end_da-raw_da),
 function=dict(start=hex(FSTART), end=hex(FEND), bytes=FEND-FSTART, instructions=len(ins),
               first_anchor=b[fo:fo+16].hex(' '), last_anchor=b[fe-16:fe].hex(' '),
               rets=[(hex(x.address),x.bytes.hex()) for x in ins if x.mnemonic.startswith('ret')]),
 direct_call_sites=[dict(site=hex(c['site']),bytes=c['bytes'],target=hex(c['dst'])) for c in call_sites],
 host_rows=host_rows,
 caller_disasm_bytes=caller_bytes,
 caller_asserts=[[a[0],a[1],a[2]] for a in caller_asserts],
 trusted_entry_count=len(starts),
 td_count=len(td), col_count=len(col), vtable_count=len(vtables), vtables_with_slots=vtables_with_slots, total_slot_values_scanned=total_slots, raw_rdata_dword_hits=raw_rdata_hits, vtable_hits=hits,
 string_refs=strrefs,
)
(OUT/'_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))


# ---- DECLARED minimal continuation for Q3 return-value-use question only ----
# Primary bound is [0x5A5020,0x5A5323). The call at 0x5A531E ends exactly at that
# bound, so 56 bytes past it (to the real ret at 0x5A535A) are read and declared here.
CONT_LO, CONT_HI = 0x5A5323, 0x5A535B
co = off_va(CONT_LO)
cont = list(md.disasm(b[co:co+(CONT_HI-CONT_LO)], CONT_LO))
with (OUT/'disasm.txt').open('a',encoding='utf-8') as f:
    f.write('\n; === DECLARED CONTINUATION for Q3 return-value-use, 0x5A5323..0x5A535B (0x38=56 bytes) ===\n')
    f.write('; primary bounded range remains [0x5A5020,0x5A5323) = 771 bytes\n')
    for x in cont:
        f.write(f'{x.address:08X}  {x.bytes.hex():<20}  {x.mnemonic:<7} {x.op_str}\n')

# EAX-from-0x5A6510 use check: scan continuation for any test/cmp/mov that reads eax before next call
eax_use=[]
for x in cont:
    if x.address >= 0x5A5326: break   # 0x5A5326 call clobbers EAX regardless
    eax_use.append(dict(site=hex(x.address), ins=x.mnemonic+' '+x.op_str))
q3 = dict(
    primary_bounded=dict(start=hex(FSTART), end=hex(FEND), bytes=FEND-FSTART, instructions=len(ins),
                         ret_count=0, string_refs=len(strrefs)),
    declared_continuation=dict(start=hex(CONT_LO), end=hex(CONT_HI), bytes=CONT_HI-CONT_LO,
                               last_real_ret='0x5A535A c3 ret',
                               instructions=[f'{x.address:08X} {x.mnemonic} {x.op_str}' for x in cont]),
    eax_after_5A531E_until_next_call=eax_use,
    this_offsets_read=['[ebx+0x60] at 0x5A502E (fild)', '[ebx+0x60] at 0x5A51E6 (fild)'],
    this_offsets_written=[],
    backward_jumps_in_bounded=[
        f'{x.address:08X} {x.mnemonic} {x.op_str}' for x in ins
        if x.mnemonic.startswith('j') and x.op_str.startswith('0x') and int(x.op_str,16)<=x.address],
    direct_calls_in_bounded=[f'{x.address:08X} call {x.op_str}' for x in ins if x.mnemonic=='call'],
)
result['q3_detail']=q3
(OUT/'_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Q3_DETAIL', json.dumps(q3,ensure_ascii=False))
