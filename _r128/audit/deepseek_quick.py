# -*- coding: utf-8 -*-
import re,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE='ra2bench/gamemd.exe'
d=open(EXE,'rb').read(); T=d[0x1000:0x1000+0x3e0000]; TVA=0x401000
md=Cs(CS_ARCH_X86,CS_MODE_32)
off=lambda va: va-TVA
def dis(va,n):
    return list(md.disasm_lite(T[off(va):off(va)+n],va))
print('=== whole-file raw occurrences of LE 0x7ea6e8 (bytes e8 a6 7e 00) ===')
idx=[m.start() for m in re.finditer(re.escape(bytes.fromhex('e8a67e00')),d)]
for i in idx: print('  file_off=%s approx_va=%s ctx=%s'%(hex(i),hex(i-0x1000+0x401000),d[i-4:i+8].hex(' ')))
print('=== C: 0x7ea6e8 sites, dist to next f3a7 ===')
for va in (0x42930f,0x4293a5,0x4f4273):
    win=T[off(va):off(va)+32]
    k=win.find(b'\xf3\xa7')
    print('  %s win=%s f3a7_rel=%s abs=%s'%(hex(va),win.hex(),k,hex(va+k)))
    for a,s,m,o in dis(va,32):
        print('     %x %s %s'%(a,m,o))
        if a+ s > va+32: break
print('=== D: push imm list 0x429270..0x429360 ===')
for a,s,m,o in dis(0x429270,0xf0):
    if m=='push' and re.match(r'^0x[0-9a-f]+$',o):
        print('  %x push %s bytes=%s'%(a,o,T[off(a):off(a)+s].hex()))
print('=== D: call dword ptr [reg] + governing movs ===')
for a,s,m,o in dis(0x429270,0xf0):
    if m=='call' and o.startswith('dword ptr ['):
        print('  %x %s'%(a,o))
print('  movs into edx in window:')
for a,s,m,o in dis(0x429270,0xf0):
    if m.startswith('mov') and o.startswith('edx,'):
        print('   %x %s %s'%(a,m,o))
print('  xor edx:')
for a,s,m,o in dis(0x429270,0xf0):
    if m=='xor' and o.startswith('edx,'):
        print('   %x xor %s'%(a,o))
