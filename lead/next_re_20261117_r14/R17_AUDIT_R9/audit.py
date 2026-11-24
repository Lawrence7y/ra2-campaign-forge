#!/usr/bin/env python3
# R17-AUDIT-R9 independent audit implementation.  Read-only on gamemd.exe.
# No import/reuse of the execution side's work.py.  Writes only into R17_AUDIT_R9.
import struct, hashlib, os, json, re, sys
from collections import Counter

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R9"
data = open(EXE, 'rb').read()
SHA = hashlib.sha256(data).hexdigest().upper()

# ---- independent PE parse ----
e = struct.unpack_from('<I', data, 0x3C)[0]
assert data[e:e+4] == b'PE\0\0', 'not PE'
nsec = struct.unpack_from('<H', data, e+6)[0]
optsize = struct.unpack_from('<H', data, e+20)[0]
opt = e+24
IB = struct.unpack_from('<I', data, opt+28)[0]
secoff = opt + optsize
secs = []
for i in range(nsec):
    o = secoff + 40*i
    name = data[o:o+8].rstrip(b'\0').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o+8)
    secs.append(dict(name=name, va=IB+vaddr, vsize=vsize, raw=raddr, rsize=rsize))
def sec(n): return next(s for s in secs if s['name']==n)
def blob(s): return data[s['raw']:s['raw']+s['rsize']]
def va2off(va):
    for s in secs:
        if s['va'] <= va < s['va']+s['rsize']:
            return s['raw'] + (va-s['va'])
    return None
T = sec('.text'); R = sec('.rdata'); D = sec('.data')
TB = blob(T); RB = blob(R); DB = blob(D)
TEXT_LO, TEXT_HI_V = T['va'], T['va']+T['vsize']      # 0x401000 .. 0x7E038D
TEXT_HI_RAW = T['va']+T['rsize']
IMG_LO = min(s['va'] for s in secs)
IMG_HI = max(s['va']+s['vsize'] for s in secs)

def raw_hits(buf, val):
    pat = struct.pack('<I', val & 0xFFFFFFFF)
    out=[]; i=buf.find(pat)
    while i>=0:
        out.append(i); i=buf.find(pat,i+1)
    return out
def is_text_ptr(v): return TEXT_LO <= v < TEXT_HI_V
def is_img_ptr(v): return IMG_LO <= v < IMG_HI

RES = dict(sha=SHA, imagebase=IB, sections=secs,
           text_scan_bytes=len(TB), rdata_scan_bytes=len(RB), data_scan_bytes=len(DB),
           text_va_range=[TEXT_LO,TEXT_HI_V], text_raw_hi=TEXT_HI_RAW,
           img_range=[IMG_LO,IMG_HI])

# ================= B1 =================
# 12 candidates: the 11 explicitly enumerated by R9 + the next T2 slot 0x7E406C (documented).
CAND = [0x7E3FDC,0x7E3FE0,0x7E3FE4,0x7E3FE8,0x7E4050,0x7E4054,0x7E4058,
        0x7E405C,0x7E4060,0x7E4064,0x7E4068,0x7E406C]
b1=[]
for v in CAND:
    hs = raw_hits(TB, v)
    b1.append(dict(addr=hex(v), hits=len(hs), sites=[hex(T['va']+o) for o in hs[:20]]))
RES['B1'] = b1

# positive control 1: push imm32 / mov r32,imm32 whose immediate is a .text VA.
pushc = Counter(); pushsite={}
for i in range(len(TB)-5):
    if TB[i]==0x68:
        v=struct.unpack_from('<I',TB,i+1)[0]
        if is_text_ptr(v):
            pushc[v]+=1; pushsite.setdefault(v, T['va']+i)
movc = Counter(); movsite={}
for i in range(len(TB)-5):
    op=TB[i]
    if 0xB8 <= op <= 0xBF:
        v=struct.unpack_from('<I',TB,i+1)[0]
        if is_text_ptr(v):
            movc[v]+=1; movsite.setdefault(v, T['va']+i)
pos=[]
for v,c in pushc.most_common(3):
    n=len(raw_hits(TB,v))
    pos.append(dict(kind='push_imm32', target=hex(v), expected_min=c, measured_raw=n,
                    example_site=hex(pushsite[v]), pass_=(n>=c)))
for v,c in movc.most_common(2):
    n=len(raw_hits(TB,v))
    pos.append(dict(kind='mov_r32_imm32', target=hex(v), expected_min=c, measured_raw=n,
                    example_site=hex(movsite[v]), pass_=(n>=c)))
# positive control 2: E8 rel32 reverse-count for 0x47C620 (card suggestion)
e8_ctrl={}
for tgt in (0x47C620,):
    c=0; sites=[]
    for i in range(len(TB)-5):
        if TB[i]==0xE8:
            rel=struct.unpack_from('<i',TB,i+1)[0]
            site=T['va']+i
            if site+5+rel==tgt:
                c+=1; sites.append(hex(site))
    e8_ctrl[hex(tgt)]=dict(count=c, sites=sites[:20])
RES['B1_pos'] = dict(raw_immediate_controls=pos, e8_reverse_controls=e8_ctrl)

# anti-controls: synthetic alignment / boundary / truncation
syn=bytearray(b'\x90'*80)
for o in (0,1,2,3,76): struct.pack_into('<I',syn,o,CAND[1])
# rebuild cleanly for truncation test
syn2=bytearray(b'\x90'*80); struct.pack_into('<I',syn2,76,CAND[1])
syn3=bytearray(b'\x90'*80); syn3[77:80]=struct.pack('<I',CAND[1])[:3]  # truncated 3 bytes at 77
anti=dict(
  alignment_offsets_found={str(o):len(raw_hits(bytes(syn),CAND[1]))>0 for o in (0,1,2,3)},
  synthetic_full_at_76=len(raw_hits(bytes(syn2),CAND[1])),
  synthetic_truncated_3bytes=len(raw_hits(bytes(syn3),CAND[1])),
  real_text_in_file_bounds= (T['raw']+T['rsize'] <= len(data)),
  text_slice_len=len(TB), text_rsize=T['rsize'],
  inject_at_start_found=None, inject_at_end_found=None)
inj=bytearray(TB)
struct.pack_into('<I',inj,0,CAND[1]); anti['inject_at_start_found']=len(raw_hits(bytes(inj),CAND[1]))>0
inj=bytearray(TB)
struct.pack_into('<I',inj,len(TB)-4,CAND[1]); anti['inject_at_end_found']=len(raw_hits(bytes(inj),CAND[1]))>0
RES['B1_anti']=anti

# ================= B2 =================
def run_from(anchor_va, pred, buf, base_va):
    i=(anchor_va-base_va)//4
    if i<0 or (i+1)*4>len(buf): return None
    s=i
    while s>0 and pred(struct.unpack_from('<I',buf,(s-1)*4)[0]): s-=1
    e=i+1
    while (e+1)*4<=len(buf) and pred(struct.unpack_from('<I',buf,e*4)[0]): e+=1
    return dict(start=base_va+s*4, end_excl=base_va+e*4, start_idx=s, end_idx=e,
                slots=e-s,
                left_val=hex(struct.unpack_from('<I',buf,(s-1)*4)[0]) if s>0 else None,
                right_val=hex(struct.unpack_from('<I',buf,e*4)[0]) if (e+1)*4<=len(buf) else None)
b2_text=run_from(0x7E3FE0, is_text_ptr, RB, R['va'])
b2_img =run_from(0x7E3FE0, is_img_ptr,  RB, R['va'])
RES['B2']=dict(text_run=b2_text, image_run=b2_img,
   r8_claim=dict(start=0x7E3EBC,end=0x7E43C4,slots=(0x7E43C4-0x7E3EBC)//4),
   r9_claim=dict(start=0x7E3E8C,end_inclusive=0x7E4403,slots=(0x7E4404-0x7E3E8C)//4))
# values at R8 / R9 claimed boundaries
def dword_at(va):
    o=va2off(va)
    return struct.unpack_from('<I',data,o)[0] if o is not None else None
b2_vals={}
for va in (0x7E3E84,0x7E3E88,0x7E3E8C,0x7E3EB4,0x7E3EB8,0x7E3EBC,0x7E3EC0,
           0x7E43C0,0x7E43C4,0x7E43C8,0x7E4400,0x7E4404,0x7E4408):
    v=dword_at(va)
    b2_vals[hex(va)]=dict(value=hex(v) if v is not None else None,
                          text=is_text_ptr(v) if v is not None else None,
                          img=is_img_ptr(v) if v is not None else None)
RES['B2']['boundary_values']=b2_vals

# ================= B3 =================
from capstone import *
from capstone.x86 import *
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True

def find_anchor(buf, off, maxback=0x2000):
    # strictly anchor-aligned: start immediately after a C3 / C2 xx xx / 90|CC fill
    j=off-1; guard=0
    while j>4 and guard<maxback:
        guard+=1
        if buf[j]==0xC3:
            k=j+1
            while k<off and buf[k] in (0x90,0xCC): k+=1
            return k
        if buf[j]==0xC2:
            k=j+3
            while k<off and buf[k] in (0x90,0xCC): k+=1
            return k
        j-=1
    # fallback: run of >=2 0x90/0xCC immediately before site
    k=off-1; run=0
    while k>0 and buf[k] in (0x90,0xCC) and run<64: run+=1; k-=1
    if run>=2: return off
    return None

def disasm_window(buf, start_off, end_off, base_va):
    code=bytes(buf[start_off:end_off])
    return list(md.disasm(code, base_va+start_off))

def classify_insn(insn, V):
    imm=[]; mem=[]
    for op in insn.operands:
        if op.type==X86_OP_IMM: imm.append(op.imm & 0xFFFFFFFF)
        if op.type==X86_OP_MEM: mem.append(op.mem.disp & 0xFFFFFFFF)
    return dict(addr=hex(insn.address), mnemonic=insn.mnemonic, op_str=insn.op_str,
                imm_hit=(V in imm), memdisp_hit=(V in mem))

seg_lo = b2_text['start']; seg_hi = b2_text['end_excl']
b3_exact=[]
for V in CAND+[seg_lo, seg_lo+4, 0x7E3E90,0x7E3EBC]:
    hits=raw_hits(TB,V)
    rec=dict(target=hex(V), raw_hits=len(hits), details=[])
    for o in hits[:12]:
        anc=find_anchor(TB,o)
        d=dict(site=hex(T['va']+o), anchor=hex(T['va']+anc) if anc is not None else None, insn=None)
        if anc is not None:
            insns=disasm_window(TB,anc,min(len(TB),o+16),T['va'])
            for ins in insns:
                if ins.address==T['va']+o or ins.address<=T['va']+o<ins.address+ins.size:
                    d['insn']=classify_insn(ins,V); break
        rec['details'].append(d)
    b3_exact.append(rec)

# band scan R9 claimed [0x7E3E00,0x7E4140) and widened [0x7D0000,0x7F0000)
def band_scan(lo,hi):
    out=[]
    for o in range(len(TB)-3):
        v=struct.unpack_from('<I',TB,o)[0]
        if lo<=v<hi:
            out.append(dict(off=o,va=hex(v),site=hex(T['va']+o)))
    return out
band_r9=band_scan(0x7E3E00,0x7E4140)
band_wide=band_scan(0x7D0000,0x7F0000)
# anchored classification of band_r9 sites (cap only first 40 for time)
band_detail=[]
for h in band_r9[:40]:
    V=int(h['va'],16); o=h['off']; anc=find_anchor(TB,o)
    d=dict(site=h['site'],target=h['va'],anchor=hex(T['va']+anc) if anc is not None else None, insn=None)
    if anc is not None:
        for ins in disasm_window(TB,anc,min(len(TB),o+16),T['va']):
            if ins.address<=T['va']+o<ins.address+ins.size:
                d['insn']=classify_insn(ins,V); break
    band_detail.append(d)
# lea reg,[idx*scale+disp32] patterns reaching near segment
lea=[]
for scale,sbits in ((1,0),(2,1),(4,2),(8,3)):
    for idx in range(8):
        if idx==4: continue
        for reg in range(8):
            op1=0x8D; modrm=0x04 | (reg<<3)  # mod=00 rm=100
            sib=(sbits<<6)|(idx<<3)|5
            pat=bytes([op1,modrm,sib])
            i=TB.find(pat)
            while i>=0 and i+7<=len(TB):
                disp=struct.unpack_from('<I',TB,i+3)[0]
                if 0x7D0000<=disp<0x7F5000:
                    lea.append(dict(site=hex(T['va']+i), mnemonic='lea',
                        pattern=pat.hex(), disp=hex(disp), scale=scale, index_reg=idx,
                        can_reach=bool(disp<=seg_hi and disp+scale*0x400>=seg_lo)))
                i=TB.find(pat,i+1)
# A1 / 8B 05 disp32 (mov reg,[global]) with disp pointing at .data globals inside segment
data_globals=[]
for o in range(0,len(DB)-3,4):
    v=struct.unpack_from('<I',DB,o)[0]
    if seg_lo<=v<seg_hi:
        gva=D['va']+o
        refs=len(raw_hits(data,gva))
        data_globals.append(dict(glob=hex(gva),holds=hex(v),all_section_refs=refs))
b3_indirect=dict(band_r9_count=len(band_r9), band_r9_max=max((int(x['va'],16) for x in band_r9),default=None),
    band_wide_count=len(band_wide), band_detail=band_detail, lea_disp32=lea,
    data_globals_into_segment=data_globals)
RES['B3']=dict(exact=b3_exact, indirect=b3_indirect)

# ================= B4 =================
win_lo,win_hi=0x7E2E8C,0x7E5403
wo=va2off(win_lo); we=va2off(win_hi-1)
window=RB[wo:we+1] if wo is not None and we is not None else b''
dec_all=len(re.findall(rb'\.\?[A-Z]', RB))
dec_win=len(re.findall(rb'\.\?[A-Z]', window))
# any '.'+printable strings in window
dotstr=[m.group(0) for m in re.finditer(rb'\.[A-Za-z?_][ -~]{3,60}', window)]
# pTD shape on out-of-.text pointers in neighborhood
ptd=[]
for va in range(0x7E3E00,0x7E4100,4):
    v=dword_at(va)
    if v is not None and not is_text_ptr(v) and IMG_LO<=v<IMG_HI:
        o=va2off(v)
        if o is not None and o+12<=len(data):
            d0,d1,d2=struct.unpack_from('<III',data,o)
            nm=va2off(d0) if d0 else None
            s=None
            if nm is not None and nm<len(data): s=data[nm:nm+24]
            ptd.append(dict(slot=hex(va),val=hex(v),d0=hex(d0),d1=hex(d1),d2=hex(d2),namebytes=repr(s)))
RES['B4']=dict(decorated_all_rdata=dec_all, decorated_window=dec_win,
   window_range=[hex(win_lo),hex(win_hi)], window_bytes=len(window),
   dot_strings_sample=[repr(x) for x in dotstr[:20]], ptd_candidates=ptd)

# ---- write intermediates ----
with open(os.path.join(OUT,'raw_results.json'),'w',encoding='utf8') as f:
    json.dump(RES,f,ensure_ascii=False,indent=1)
print('DONE sha',SHA)
print('B1 counts',[(x['addr'],x['hits']) for x in b1])
print('B2 text_run',b2_text)
print('B2 image_run',b2_img)
print('B1_pos',json.dumps(RES['B1_pos'],ensure_ascii=False))
print('B1_anti',json.dumps(anti))
print('B3 band_r9_count',len(band_r9),'max',RES['B3']['indirect']['band_r9_max'])
print('B3 lea candidates',len(lea),'data_globals',data_globals)
print('B4',dec_all,dec_win,'dotstr',len(dotstr))
