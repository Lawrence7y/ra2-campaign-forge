import sys,pefile,capstone
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
D=open(P,'rb').read();pe=pefile.PE(P,fast_load=True);IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip(chr(0)),IMG+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def rd(va,n):
    for nm,b,vs,pt,rs in SECS:
        if b<=va<b+vs:return D[pt+(va-b):pt+(va-b)+n]
    return b''
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);MD.skipdata=True
print('=== 0075E510 (up to 1 ret) ===')
cnt=0;rets=0
for ins in MD.disasm(rd(0x75e510,700),0x75e510):
    print('%08X %-8s %s'%(ins.address,ins.mnemonic,ins.op_str))
    if ins.mnemonic=='ret':rets+=1
    cnt+=1
    if rets>=1 or cnt>95:break
print()
print('=== search imm 0x007e5170 in .text ===')
t=[s for s in SECS if s[0]=='.text'][0]
tb=D[t[3]:t[3]+t[4]]
pat=bytes([0x70,0x51,0x7e,0x00])
pos=0
while True:
    i=tb.find(pat,pos)
    if i<0:break
    va=t[1]+i
    print(' at %08X prev8=%s next2=%s'%(va,tb[max(0,i-8):i].hex(),tb[i+4:i+6].hex()))
    pos=i+1
