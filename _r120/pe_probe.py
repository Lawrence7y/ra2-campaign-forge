import struct, json, sys
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
d=open(P,'rb').read()
print('len',len(d))
assert d[:2]==b'MZ'
e_lfanew=struct.unpack_from('<I',d,0x3c)[0]
print('e_lfanew',hex(e_lfanew), d[e_lfanew:e_lfanew+4])
mach,nsec,tds,psym,nsym,optsz,chars=struct.unpack_from('<HHIIIHH',d,e_lfanew+4)
print('machine',hex(mach),'nsec',nsec,'optsz',optsz)
opt=e_lfanew+24
magic=struct.unpack_from('<H',d,opt)[0]
print('opt magic',hex(magic))
ImageBase=struct.unpack_from('<I',d,opt+28)[0]
print('ImageBase',hex(ImageBase))
SizeOfImage=struct.unpack_from('<I',d,opt+56)[0]
SizeOfHeaders=struct.unpack_from('<I',d,opt+60)[0]
print('SizeOfImage',hex(SizeOfImage),'SizeOfHeaders',hex(SizeOfHeaders))
# data dirs
dd=opt+96
dirs=[]
for i in range(16):
    rva,sz=struct.unpack_from('<II',d,dd+8*i)
    dirs.append((i,rva,sz))
print('dirs:',' '.join('%d:%x/%x'%(i,r,s) for i,r,s in dirs if r or s))
sec=e_lfanew+24+optsz
S=[]
for i in range(nsec):
    name=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8)
    ch=struct.unpack_from('<I',d,sec+40*i+36)[0]
    S.append(dict(name=name,va=va,vs=vs,raw=ra,rawsize=rs,ch=ch))
    print('%-8s VA=%08x VS=%08x raw=%08x rawsize=%08x ch=%08x'%(name,va,vs,ra,rs,ch))
json.dump(dict(e_lfanew=e_lfanew,ImageBase=ImageBase,SizeOfImage=SizeOfImage,sections=S,dirs={i:[r,s] for i,r,s in dirs}),open('/home/t628/projects/ra2-campaign-forge/_r120/x120exec_pe.json','w'),indent=1)
