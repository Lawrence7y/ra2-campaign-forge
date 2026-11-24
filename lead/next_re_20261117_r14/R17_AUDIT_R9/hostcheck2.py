import struct,json
from capstone import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe";OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R9"
data=open(EXE,'rb').read();e=struct.unpack_from('<I',data,0x3C)[0];n=struct.unpack_from('<H',data,e+6)[0]
os=struct.unpack_from('<H',data,e+20)[0];opt=e+24;ib=struct.unpack_from('<I',data,opt+28)[0];so=opt+os
secs=[]
for i in range(n):
 o=so+40*i;nm=data[o:o+8].rstrip(b'\0').decode();vs,va,rs,ra=struct.unpack_from('<IIII',data,o+8);secs.append((nm,ib+va,ra,rs,vs))
T=next(x for x in secs if x[0]=='.text');tva,traw,trs=T[1],T[2],T[3]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=False
buf=data[traw:traw+trs]
def resolve(start_va,site_va):
 a=start_va-tva;off=site_va-tva;end=min(trs,off+0x1000)
 insns=list(md.disasm(bytes(buf[a:end]),start_va))
 site=[x for x in insns if x.address<=site_va<x.address+x.size]
 rets=[x for x in insns if x.address>site_va and x.mnemonic in ('ret','retf')]
 info=None
 if rets:
  ins=rets[0];na=ins.address+ins.size;no=na-tva
  after=buf[no:no+8]
  info=dict(ret=hex(ins.address),fn_end=hex(na),after=after.hex())
 return dict(host=hex(start_va),site=hex(site_va),site_insn=(site[0].mnemonic+' '+site[0].op_str) if site else None,retinfo=info,assertion=(f'0x{start_va:x} <= 0x{site_va:x} < {info["fn_end"]}' if info else 'fn_end未取得'))
sites=[(0x43B680,0x43B721),(0x43B740,0x43B9FC),(0x43BCF0,0x43BCFF),(0x43B680,0x43B736),(0x43B740,0x43BA11),(0x43BCF0,0x43BD16)]
out=[resolve(h,s) for h,s in sites]
json.dump(out,open(OUT+r'\hostcheck2.json','w'),indent=1)
print(json.dumps(out,indent=1))
