import struct,pefile,csv,os
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'; EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')=='.text'); tstart=sec.PointerToRawData; tend=tstart+sec.SizeOfRawData; tva=base+sec.VirtualAddress
def nv(x): return format(x&0xffffffff,'08X')
s20vt=set()
with open(os.path.join(EV,'vtable_rtti.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): s20vt.add(r['vt'])
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
def parse_c7(start):
    if start+6>tend or raw[start]!=0xC7: return None
    modrm=raw[start+1]; mod=modrm>>6; reg=(modrm>>3)&7; rm=modrm&7
    if reg!=0 or mod==3: return None
    i=start+2; base_reg=None; index_reg=None; disp=None
    if rm==4:
        if i>=tend: return None
        sib=raw[i]; i+=1; b=sib&7; ix=(sib>>3)&7
        if mod==0:
            if b==5: base_reg=None; disp=struct.unpack_from('<i',raw,i)[0]; i+=4
            else: base_reg=b
        elif mod==1:
            base_reg=b; disp=struct.unpack_from('<b',raw,i)[0]; i+=1
        else:
            base_reg=b; disp=struct.unpack_from('<i',raw,i)[0]; i+=4
        if ix!=4: index_reg=ix
    else:
        if mod==0 and rm==5: base_reg=None; disp=struct.unpack_from('<i',raw,i)[0]; i+=4
        elif mod==1: base_reg=rm; disp=struct.unpack_from('<b',raw,i)[0]; i+=1
        elif mod==2: base_reg=rm; disp=struct.unpack_from('<i',raw,i)[0]; i+=4
        else: base_reg=rm
    if i+4>tend: return None
    imm=struct.unpack_from('<I',raw,i)[0]; i+=4
    return {'start':start,'mod':mod,'rm':rm,'base_reg':base_reg,'index_reg':index_reg,'disp':disp,'imm':imm,'len':i-start,'bytes':raw[start:i].hex().upper()}
rows=[]; dec=Cs(CS_ARCH_X86,CS_MODE_32)
for off in range(tstart,tend):
    if raw[off]!=0xC7: continue
    p=parse_c7(off)
    if not p or nv(p['imm']) not in s20vt: continue
    ins=None
    for x in dec.disasm(raw[off:off+p['len']],tva+off-tstart):
        if x.address==tva+off-tstart and x.size==p['len']: ins=f'{x.mnemonic} {x.op_str}'; break
    rows.append((nv(tva+off-tstart),'ABS' if p['base_reg'] is None else ('R'+str(p['base_reg'])),nv(p['disp']&0xffffffff) if p['disp'] is not None else '',nv(p['imm']),p['bytes'],ins or 'DECODE_FAIL'))
with open(os.path.join(EV,'raw_c7_s20vt.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('site\taddr_mode\tglobal_or_disp\tvt\tbytes\tinsn\n')
    for r in rows: f.write('\t'.join(r)+'\n')
print('RAW_C7_S20VT',len(rows),'ABS',sum(1 for r in rows if r[1]=='ABS'),'REG',sum(1 for r in rows if r[1]!='ABS'))
for r in rows[:80]: print('\t'.join(r))
