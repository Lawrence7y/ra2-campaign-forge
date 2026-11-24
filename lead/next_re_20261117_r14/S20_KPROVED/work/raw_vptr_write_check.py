import struct,pefile,csv,os
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'; EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')=='.text'); tstart=sec.PointerToRawData; tend=tstart+sec.SizeOfRawData; tva=base+sec.VirtualAddress
def nv(x): return format(x&0xffffffff,'08X')
s20vt=set()
with open(os.path.join(EV,'vtable_rtti.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): s20vt.add(r['vt'])
rows=[]
for off in range(tstart,tend-9):
    if raw[off:off+2]!=b'\xC7\x05': continue
    g,imm=struct.unpack_from('<II',raw,off+2)
    if nv(imm) in s20vt:
        rows.append((nv(tva+off-tstart),nv(g),nv(imm),raw[off:off+10].hex().upper()))
with open(os.path.join(EV,'raw_c705_s20vt.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('site\tglobal\tvt\tbytes\n')
    for r in rows: f.write('\t'.join(r)+'\n')
print('RAW_C705_S20VT',len(rows))
for r in rows[:40]: print('\t'.join(r))
