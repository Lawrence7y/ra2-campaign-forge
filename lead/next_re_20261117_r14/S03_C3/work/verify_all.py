
import os,sys,struct,json,hashlib,random,csv
import pefile
from capstone import *
from capstone.x86 import *

BASE=r'D:\Project\ra2-campaign-forge'
EXE=BASE+r'\ra2youli\gamemd.exe'
OUT=BASE+r'\lead\next_re_20261117_r14\S03_C3\EVIDENCE'

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            b=f.read(1<<20)
            if not b: break
            h.update(b)
    return h.hexdigest().upper()

exe_sha=sha256(EXE)
pe=pefile.PE(EXE,fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append(dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=s.VirtualAddress,vsz=s.Misc_VirtualSize,raw=s.PointerToRawData,rsz=s.SizeOfRawData))
with open(EXE,'rb') as f: BLOB=f.read()
def va2off(va):
    rva=va-IB
    for s in secs:
        if s['va']<=rva<s['va']+max(s['vsz'],s['rsz']):
            return s['raw']+(rva-s['va'])
    return None
def rd(va,n):
    o=va2off(va)
    return None if o is None else BLOB[o:o+n]
def u32(va):
    b=rd(va,4)
    return struct.unpack('<I',b)[0] if b and len(b)==4 else None
def cstr(va,n=100):
    b=rd(va,n)
    if b is None: return None
    return b.split(b'\0')[0].decode('latin1','replace')

# ---- full .text scan ----
text=[s for s in secs if s['name']=='.text'][0]
lo=IB+text['va']; hi=lo+text['vsz']  # VirtualSize
code=BLOB[text['raw']:text['raw']+text['vsz']]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
n_insn=0;n_e8=0;last=0
for ins in md.disasm(code,lo):
    n_insn+=1
    if ins.bytes and ins.bytes[0]==0xE8 and len(ins.bytes)==5: n_e8+=1
    last=ins.address
raw_e8=code.count(b'\xE8')
scan=dict(sha256=exe_sha,text_lo=lo,text_hi=hi,n_insn=n_insn,n_e8_boundary=n_e8,raw_e8=raw_e8,last_insn=last,virtual_size=text['vsz'],size_of_raw_data=text['rsz'])
json.dump(scan,open(OUT+r'\scan_scale_verified.json','w'),indent=1)
print('SCAN',json.dumps(scan))

# ---- RTTI + direct sites verification ----
targets={
 '0065CAC0':dict(va=0x65CAC0,vts=[0x7F0904],slots=[2],name_disk='RawFileClass::slot2'),
 '004324B0':dict(va=0x4324B0,vts=[0x7E1668,0x7E3A2C],slots=[10,10],name_disk='CDFileClass::vslot10'),
 '00552490':dict(va=0x552490,vts=[0x7ECF44],slots=[2],name_disk='LCWStraw::slot2'),
 '006C9890':dict(va=0x6C9890,vts=[0x7E4D90,0x7E61E0,0x7E61F0],slots=[1,1,1],name_disk='FileStraw::slot1'),
 '00631CC0':dict(va=0x631CC0,vts=[0x7E4D78,0x7E4DA0,0x7E6200],slots=[3,3,3],name_disk='FilePipe::slot3'),
 '0065D150':dict(va=0x65D150,vts=[0x7E1668,0x7E16B0,0x7E3A2C],slots=[3,3,3],name_disk='CDFileClass::slot3'),
 '00431E80':dict(va=0x431E80,vts=[0x7E3A2C],slots=[2],name_disk='BufferIOFileClass::vslot2'),
}
# direct sites from audit TSV (verified from bytes below)
site_file=BASE+r'\lead\next_re_20261117_r14\S03_CRITERION\EVIDENCE\direct_sites_bytecheck.tsv'
sites_by={k:[] for k in targets}
with open(site_file,encoding='utf-8') as f:
    r=csv.DictReader(f,delimiter='\t')
    for row in r:
        if row['entry'] in sites_by:
            sites_by[row['entry']].append(row['site'])

rtti_report={}; site_report={}
for k,t in targets.items():
    rr=[]
    for vt,slot in zip(t['vts'],t['slots']):
        col=u32(vt-4); td=u32(col+0xC) if col else None
        nm=cstr(td+8) if td else None
        slotval=u32(vt+slot*4) if vt else None
        rr.append(dict(vt='%08X'%vt,slot=slot,col=('%08X'%col if col else None),td=('%08X'%td if td else None),name=nm,vt_slot_val=('%08X'%slotval if slotval else None),match=(slotval==t['va'])))
    rtti_report[k]=rr
    sr=[]
    for s in sites_by[k]:
        sa=int(s,16); b=rd(sa,5)
        if not b or len(b)<5 or b[0]!=0xE8:
            sr.append(dict(site=s,ok=False,reason='no E8')); continue
        rel=struct.unpack('<i',b[1:5])[0]
        dst=sa+5+rel
        ok=(dst==t['va']) and not (t['va']<=sa<t['va']+{'0065CAC0':111,'004324B0':234,'00552490':346,'006C9890':67,'00631CC0':75,'0065D150':56,'00431E80':131}[k])
        sr.append(dict(site=s,bytes5=b.hex(' '),rel32=rel,dst='%08X'%dst,ok=ok))
    site_report[k]=sr
    print('RTTI',k,[(x['name'],x['match']) for x in rr])
    print('SITES',k,'n=',len(sr),'all_ok=',all(x['ok'] for x in sr))
json.dump(dict(rtti=rtti_report,direct_sites=site_report),open(OUT+r'\rtti_sites_verified.json','w'),indent=1)
