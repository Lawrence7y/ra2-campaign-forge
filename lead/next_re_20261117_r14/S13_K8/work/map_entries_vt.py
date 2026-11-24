# -*- coding: utf-8 -*-
import sys, pefile, struct
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
DATA=open(P,'rb').read()
pe=pefile.PE(P,fast_load=True)
IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'), IMG+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def sec_of(va):
    for n,b,vs,ptr,rs in SECS:
        if b<=va<b+vs: return n,b,vs,ptr,rs
    return None
def rd(va,n):
    s=sec_of(va)
    if not s: return b''
    n0,b,vs,ptr,rs=s
    off=ptr+(va-b)
    return DATA[off:off+n]
def u32(va):
    d=rd(va,4)
    return struct.unpack('<I',d)[0] if len(d)==4 else None
def cstr(va,lim=200):
    out=b''
    for i in range(lim):
        c=rd(va+i,1)
        if not c or c==b'\x00': break
        out+=c
    return out.decode('latin1')

# Build set of TD addresses for validation
tds={} 
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for va in range(b, b+vs-8, 4):
        pat=rd(va,4)
        if pat in (b'.?AV', b'.?AU'):
            name=cstr(va,120)
            if len(name)>4 and name.endswith('@@'):
                tds[va-8]=name
tdset=set(tds)
print('TDs',len(tds))
def rtti_at_vt(vt):
    colptr=u32(vt-4)   # [vt-4] holds POINTER to COL (MSVC RTTI)
    if colptr is None or colptr==0: return None,None
    td=u32(colptr+0xC)
    if td in tdset:
        return colptr, tds[td]
    return None,None

# 150 entries from byte_census minus K9 exclusions
import csv
BC=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K5\EVIDENCE\byte_census.tsv'
exK9=set('0040B880 0040B930 0040F7C0 0040FD90 0040FE40 0046B7E0 0046B890 0062B250 0062B300 0065C0D0 0065C180 0048AD60 0054E8E0 0048AD70'.split())
entries=[]
with open(BC,encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['判定'].startswith('不可证') and r['entry'].upper() not in exK9:
            entries.append((int(r['entry'],16), r['entry'], r['name']))
print('working set',len(entries))
eset=set(e[0] for e in entries)

# Scan all aligned dwords in rdata/data: if value in eset, record as possible vt slot
hits=[] # (slot_addr, value, section)
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for va in range(b, b+vs-4, 4):
        d=rd(va,4)
        if len(d)<4: continue
        v=struct.unpack('<I',d)[0]
        if v in eset:
            hits.append((va,v,nm))
print('slot hits',len(hits))
# For each hit, find vt base by walking back up to 300 slots and checking rtti_at_vt
rows=[]
for sa,v,nm in hits:
    found=None
    for slot in range(0,300):
        vt=sa-4*slot
        col,cname=rtti_at_vt(vt)
        if col is not None:
            # validate that vt+4*slot == sa and that slot index plausible
            found=(vt,slot,col,cname)
            # prefer smallest slot (closest COL) -> break at first found walking backward
            break
    rows.append((sa,v,nm,found))
# print summary
import collections
print('hits with RTTI vt found:',sum(1 for r in rows if r[3]))
out=['# vtable-slot -> entry map. Fields: slot_addr entry section vt_base slot col classname']
for sa,v,nm,found in sorted(rows):
    if found:
        vt,slot,col,cname=found
        out.append('%08X %08X %s VT=%08X SLOT=%d COL=%08X NAME=%s'%(sa,v,nm,vt,slot,col,cname))
    else:
        out.append('%08X %08X %s VT=NA SLOT=NA COL=NA NAME=NA'%(sa,v,nm))
fn=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\EVIDENCE\entry_vt_slots.tsv'
open(fn,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('wrote',fn)
# quick show class names for audit-named 18
audit18=set(int(x,16) for x in '0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split())
for sa,v,nm,found in rows:
    if v in audit18:
        print('AUDIT18 %08X'%v, found)
