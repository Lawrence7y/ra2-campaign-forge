#!/usr/bin/env python3
# Verify 11 direct candidates byte-by-byte; caller provenance; 18 conflict lookup.
import os,sys,io,json,struct,hashlib,glob,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
import pefile,capstone
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
def norm(a):return a.upper().replace("0X","")

# load exe and .text
data=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if s.Name.rstrip(b'\x00').decode()=='.text'][0]
va=ib+sec.VirtualAddress; code=data[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
def readbytes(addr,n):
    o=addr-va
    if o<0 or o+n>len(code):return None
    return code[o:o+n]

# load coverage grade map + names
grade={}; name={}; cov_rows={}
for l in open(COV,encoding='utf-8').read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split('\t'); a=norm(f[0]); grade[a]=f[4];name[a]=f[2];cov_rows[a]=f
# load atlas intervals
atlas={}
for l in open(ATLAS,encoding='utf-8').read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split('\t'); atlas[norm(f[0])]=int(f[1])
# load candidate hits
hits=[]
for l in open(os.path.join(WK,'s20_direct_hits.tsv'),encoding='utf-8').read().splitlines()[1:]:
    f=l.split('\t');
    if int(f[3])>0 and f[1]!='[已证]':
        hits.append(dict(entry=f[0],grade=f[1],name=f[2],sites=f[5].split(';')))
# also include proved hits for donor-grade stat
allhits=[]
for l in open(os.path.join(WK,'s20_direct_hits.tsv'),encoding='utf-8').read().splitlines()[1:]:
    f=l.split('\t');
    if int(f[3])>0:
        allhits.append(dict(entry=f[0],grade=f[1],name=f[2],sites=f[5].split(';')))

def owner(addr):
    # find atlas fn whose interval contains addr
    for a,sz in atlas.items():
        ai=int(a,16)
        if ai<=int(addr,16)<ai+sz:return a
    return None

md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
verified=[]
for h in hits:
    entry=h['entry']; en=int(entry,16)
    rec=dict(entry=entry,grade_old=h['grade'],name=h['name'],sites=[])
    for site in h['sites']:
        si=int(site,16); b=readbytes(si,5)
        if b is None or b[0]!=0xE8:
            rec['sites'].append(dict(site=site,ok=False,why='read/bytes'));continue
        rel=struct.unpack('<i',b[1:5])[0]; calc=(si+5+rel)&0xFFFFFFFF
        ins=next(md.disasm(b,si),None)
        callok = ins is not None and ins.id==capstone.x86.X86_INS_CALL and len(ins.operands)==1 and ins.operands[0].type==capstone.x86.X86_OP_IMM
        own=owner(site)
        selfloop = (own is not None and int(own,16)<=en<int(own,16)+atlas[own])
        if not (own is not None and int(own,16)<=en<int(own,16)+atlas[own]) and own is not None and int(own,16)<=en<int(own,16)+atlas[own]:
            selfloop=True
        # robust self-loop: caller owner interval contains entry
        if own:
            selfloop = int(own,16)<=en<int(own,16)+atlas[own]
        donor = grade.get(own,'[missing]') if own else '[no-atlas]'
        rec['sites'].append(dict(site=site,bytes=b.hex(),rel=rel,target=f'{calc:08X}',callok=callok,owner=own,owner_grade=donor,selfloop=selfloop,
                                 ok=(calc==en and callok and not selfloop)))
    verified.append(rec)

# conflict 18: search repo for entry address as a token
roots=[os.path.join(ROOT,'docs','re'),os.path.join(ROOT,'re_atlas','kb'),os.path.join(ROOT,'lead')]
pat_files=[]
for r in roots:
    for dp,dn,fn in os.walk(r):
        # skip huge/binary; limit to text
        for n in fn:
            if n.lower().endswith(('.md','.tsv','.txt','.json','.py')):
                pat_files.append(os.path.join(dp,n))
conflicts={}
for rec in verified:
    a=rec['entry']; hits_conf=[]
    # patterns: exact 8-hex address case-insensitive, with or without 0x
    rgx=re.compile(r'(?i)(?<![0-9A-F])'+re.escape(a)+r'(?![0-9A-F])')
    for p in pat_files:
        try:
            txt=open(p,encoding='utf-8',errors='ignore').read()
        except: continue
        for i,l in enumerate(txt.splitlines(),1):
            if rgx.search(l):
                hits_conf.append(p.replace(ROOT+os.sep,'')+':'+str(i)+':'+l[:160])
                if len(hits_conf)>=8:break
        if len(hits_conf)>=8:break
    conflicts[a]=hits_conf

json.dump(dict(verified=verified,conflicts=conflicts),open(os.path.join(EV,'verify_direct.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
# print concise
for rec in verified:
    good=[s for s in rec['sites'] if s['ok']]
    print(rec['entry'],rec['grade_old'],rec['name'],'good_sites=',len(good),'/',len(rec['sites']))
    for s in rec['sites']:
        print('   ',s['site'],s['bytes'],'->',s['target'],'callok',s['callok'],'owner',s.get('owner'),'owner_grade',s.get('owner_grade'),'self',s['selfloop'],'ok',s['ok'])
    print('   CONFLICTS18:',len(conflicts[rec['entry']]))
    for c in conflicts[rec['entry']][:3]:print('      ',c)
print('wrote',os.path.join(EV,'verify_direct.json'))
