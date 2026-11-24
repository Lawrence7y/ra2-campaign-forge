# -*- coding: utf-8 -*-
import sys,pefile,struct,json,collections
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
D=open(P,'rb').read(); pe=pefile.PE(P,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'),IMG+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def fo2va(fo):
    for n,b,vs,pt,rs in SECS:
        if pt<=fo<pt+rs:return b+(fo-pt)
    return None
TEXT=[s for s in SECS if s[0]=='.text'][0]
tp,tr=TEXT[3],TEXT[4]
found=collections.defaultdict(list)
text=D[tp:tp+tr]
for i in range(len(text)-6):
    if text[i]==0xC7 and (text[i+1]&0xC7)==0x06:
        modrm=text[i+1]; mod=(modrm>>6)&3; rm=modrm&7
        if mod==0 and rm==5: immoff=i+2+4
        elif mod==1: immoff=i+2+1
        elif mod==2: immoff=i+2+4
        else: immoff=i+2
        if immoff+4>len(text): continue
        imm=struct.unpack('<I',text[immoff:immoff+4])[0]
        if 0x7e0000<=imm<=0x820000:
            va=fo2va(tp+i); found[imm].append((va,'C7_%02X'%modrm))
for i in range(len(text)-5):
    if text[i]==0x68:
        imm=struct.unpack('<I',text[i+1:i+5])[0]
        if 0x7e0000<=imm<=0x820000:
            va=fo2va(tp+i); found[imm].append((va,'PUSH'))
e=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\EVIDENCE\analysis_full.json',encoding='utf-8'))
a18=set('0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split())
for r in e['results']:
    if r['ea'] in a18:
        vts=set(s[1] for s in r['slots'] if s[1])
        print(r['ea'],'vts',[hex(v) for v in vts])
        for vt in vts:
            sites=found.get(vt,[])
            print('   VT %08X refs: %d'%(vt,len(sites)),sites[:6])
