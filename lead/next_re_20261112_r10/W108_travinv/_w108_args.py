import struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
d=open(EXE,"rb").read(); BASE=0x400000
def off(va): return va-BASE
def b(va,n=16): return " ".join("%02X"%x for x in d[off(va):off(va)+n])
# Ghidra decompiled  FUN_0047ea90(param_3,(char)param_3[0x23]);
# param_3[0x23] is int index 0x23 => byte offset 0x8C.  Verify bytes at the call site.
print("=== call-site argument construction (0x005688DC..0x005688F2) ===")
print("0x005688DC: "+b(0x005688DC,0x16))
print()
print("expected: 8A 97 8C 00 00 00 = mov dl,[edi+0x8C]   (edi = param_3 = the object)")
print("          8B C8             = mov  ecx,eax          (ecx = this = cell)")
print("          52                = push edx              (arg2 = whichChain = [obj+0x8C])")
print("          57                = push edi              (arg1 = node = obj)")
print("          E8 A0 61 F1 FF    = call 0x0047EA90")
print()
print("=== so the unlink call is: UNLINK(cell=ecx, node=edi, whichChain=obj->[+0x8C]) ===")
print()
# 0x47EA90 param read: mov cl,[esp+0x1C] after sub esp,0xC push esi push edi
print("=== 0x47EA90 prologue / whichChain selection (§2-1 of LEAD_VERIFY) ===")
print("0x0047EA90: "+b(0x0047EA90,0x30))
print()
print("83 EC 0C       sub  esp,0xC")
print("56             push esi")
print("8B 74 24 14    mov  esi,[esp+0x14]   ; arg1 node   (ret=+0, esi=+4, edi=+8, sub12=+0x14)")
print("57             push edi")
print("8B F9          mov  edi,ecx          ; this = cell")
print("85 F6          test esi,esi")
print("0F 84 EC 00 00 00 je 0x47EB8F")
print("8A 4C 24 1C    mov  cl,[esp+0x1C]    ; arg2 whichChain")
print("84 C9          test cl,cl")
print("74 08          je  +8  (-> 0x0047EAB3)")
print("8B 87 E8 00 00 00 mov eax,[edi+0xE8]  ; whichChain!=0 -> chain B")
print("EB 06          jmp")
print("8B 87 E4 00 00 00 mov eax,[edi+0xE4]  ; whichChain==0 -> chain A")
