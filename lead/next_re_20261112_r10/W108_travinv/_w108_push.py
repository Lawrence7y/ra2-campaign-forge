import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read(); BASE=0x400000
def off(va): return va-BASE
def by(va): return d[off(va)]

print("### TRAV_4D0 (ret 8) - push ORDER: last-pushed is arg1=wanted, first-pushed is arg2=whichChain")
print("###  cdecl/thiscall-with-stack: caller pushes right-to-left => arg2 first")
print("###  observed pattern '6A 00 . . 6A xx' = push 0 (arg2) ; push xx (arg1)")
print()
for a,desc in ((0x0047BDC4,""),(0x0047C06B,""),(0x0047C74A,""),(0x0047C813,""),
               (0x004812A7,""),(0x004812C6,"")):
    # find the two pushes immediately before the call
    seq=[]
    va=a-1
    for k in range(8):
        if by(va-1)==0x6A:
            seq.append(by(va))
            va-=2
        elif by(va-1)==0x6B:
            va-=3
        else:
            break
    print("call@0x%08X  pushes-before (innermost first) = %s"%(a,seq))
print()
print("### TRAV_550 (ONE arg = whichChain) - pattern '6A 00' right before, then mov ecx,cell")
print("###  6A 00 = push 0  => whichChain = 0  => CHAIN A, in every case")
print()
for a in (0x005085D4,0x005085E0,0x00586816,0x005FC4A0,0x005FD2BA,
          0x0062AB97,0x006D57C5,0x006E1896,0x006E1940,0x006E1A0D):
    print("call@0x%08X  bytes[-8] = %s"%(a," ".join("%02X"%x for x in d[off(a-8):off(a)])))
