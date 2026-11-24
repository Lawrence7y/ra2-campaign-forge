"""Final self-check: re-verify GetSize bytes, whatami, and key evidence counts."""
import os, json, struct, pefile
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
DATA=open(P,'rb').read()
def rd(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return struct.unpack_from('<I',DATA,pr+d)[0]
    return None
def rdbytes(va,n):
    for nm,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return DATA[pr+d:pr+d+n]
    return None
# vtable + 12*4
VT={'BuildingClass':0x7E3EBC,'UnitClass':0x7F5C70,'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4}
print('=== GetSize (v[12]) raw bytes ===')
for nm,vt in VT.items():
    f12=rd(vt+12*4); f11=rd(vt+11*4)
    b12=rdbytes(f12,6); b11=rdbytes(f11,6)
    print('%-14s v12=%08X %s -> imm=%d(0x%X) | v11=%08X %s -> id=%d'%(
        nm,f12,b12.hex(),struct.unpack_from('<I',b12,1)[0] if b12[0]==0xB8 else -1,
        struct.unpack_from('<I',b12,1)[0] if b12[0]==0xB8 else -1,
        f11,b11.hex(),struct.unpack_from('<I',b11,1)[0] if b11[0]==0xB8 else -1))
# baseline numbers from json
sj=json.load(open(os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','EVIDENCE','vtable_write_sites.json')))
b=sj['baseline']
print('=== baseline ===')
print('C705 in .rdata=%d distinct=%d named=%d | random=%d named=%d (%.2f%%)'%(
    b['c705_total_in_rdata'],b['distinct_vals'],b['named_vals'],b['random_rdata_n'],b['random_rdata_named'],b['random_rdata_fp_pct']))
# delta rows
dl=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','coverage_delta.tsv')
rows=list(csv.DictReader(open(dl,encoding='utf-8'),delimiter='\t')) if False else open(dl,encoding='utf-8').read().splitlines()
print('=== delta rows (incl header) ===',len(rows))
