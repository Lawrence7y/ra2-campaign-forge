import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read(); BASE=0x400000
def off(va): return va-BASE
def show(va,n): return " ".join("%02X"%x for x in d[off(va):off(va)+n])
sites_4d0=[0x0047BDC4,0x0047C06B,0x0047C74A,0x0047C813,0x004812A7,0x004812C6]
sites_550=[0x005085D4,0x005085E0,0x00586816,0x005FC4A0,0x005FD2BA,0x0062AB97,
           0x006D57C5,0x006E1896,0x006E1940,0x006E1A0D]
print("### TRAV_4D0 = 0x0047C4D0 : ret 8, so two stack args pushed just before the call")
print("###   arg1 (wanted id) pushed last, arg2 (whichChain) pushed first")
print()
for a in sites_4d0:
    print("call@0x%08X   bytes[-16:call] = %s"%(a,show(a-16,16)))
print()
print("### TRAV_550 = 0x0047C550 : ONE stack arg = whichChain")
print()
for a in sites_550:
    print("call@0x%08X   bytes[-12:call] = %s"%(a,show(a-12,12)))
