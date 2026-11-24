# -*- coding: utf-8 -*-
"""第六轮：核对将要写进 EVIDENCE 的关键字节（避免抄写错误）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C

def b(va, n):
    return C.va_read(va, n).hex(" ")

def d(va, n, label):
    print("%s @%08X bytes= %s" % (label, va, b(va,n)))

print("### ① 入口字节")
d(0x432050,12,"row1 entry"); d(0x65d240,10,"row2 entry"); d(0x65d3a0,12,"row3 entry")
d(0x7ba530,8,"row4 entry"); d(0x7cd80f,14,"row5 entry")

print("\n### ② 虚表槽字节 (4B VA == entry)")
d(0x7e1698,4,"row1 slot CDFile#12"); d(0x7e3a5c,4,"row1 slot BufferIO#12")
d(0x7e16a4,4,"row2 slot CDFile#15"); d(0x7e3a68,4,"row2 slot BufferIO#15"); d(0x7f0940,4,"row2 slot Raw#15")
d(0x7f0904,4,"row3 slot Raw#0"); d(0x7e4d98,4,"row4 slot FileStraw#2")
print("  row5 refs to entry 007CD80F =", C.find_dword_refs(0x7cd80f))

print("\n### ② COL/TD/name  (COL at vt-4, sig; TD=COL+0xC VA; name=TD+8 inline cstr)")
for col,td,nmva in [(0x7fa4d8,0x815e38,0x815e40),(0x7fbef8,0x815e18,0x815e20),
                     (0x808790,0x815df8,0x815e00),(0x7fcd30,0x81bfc8,0x81bfd0)]:
    print("  COL %08X sig=%s  [COL+0xC]=%s (expect %08X)  name@%08X=%r" %
          (col, b(col,4), ("%08X"%C.u32(col+0xC)), td, nmva, C.read_cstr(nmva,40)))

print("\n### ③ row1 ③b④ 循环锚点字节")
d(0x4320b9,3,"loop head mov eax,[esi+0x34]")
d(0x4320c1,7,"boundary edi=[esi+0x34]-[esi+0x38]; cmp ebx,edi")
d(0x4320c3,2,"  cmp ebx,edi")
d(0x4320c5,2,"  jge 4320c9")
d(0x43214c,7,"in-loop nonstack write mov [esi+0x38],0")
d(0x4321ae,3,"in-loop nonstack write mov [esi+0x38],eax")
d(0x4321c0,3,"in-loop nonstack write mov [esi+0x4c],ecx")
d(0x432175,5,"in-loop IO call memcpy 0x7ca090")
d(0x43210b,3,"in-loop virtual call [edx+0x28]")
d(0x43211a,3,"in-loop virtual call [edx+0x24]")
d(0x43224a,7,"back-edge test ebx,ebx; jne 4320b9")

print("\n### ④ row1 ctor 安装锚点字节 (vt 0x7e1668)")
d(0x47a9d3,5,"  call base ctor 0x431b20")
d(0x47a9e3,6,"  ctor install mov [esi],0x7e1668")
d(0x473b07,5,"  direct caller call 432050")
print("  is_atexit(47A9D0)=", C.is_atexit_registered(0x47a9d0))
print("  is_atexit(401950 D0dtor)=", C.is_atexit_registered(0x401950))
