# -*- coding: utf-8 -*-
"""精确字节锚点收集：为 6 行生成 EVIDENCE 需要的地址+字节。"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def line(label, va, n=16):
    b=C.va_read(va,n)
    return "%-30s @%s : %s"%(label,C.hx(va),b.hex(" ").upper())

def col_detail(col_va):
    sig=C.u32(col_va); off=C.u32(col_va+4); cd=C.u32(col_va+8)
    td=C.u32(col_va+0xC); chd=C.u32(col_va+0x10)
    return "COL=%s sig=%d offset=%d cdOffset=%d pTD=%s pCHD=%s TD+8name=%s"%(
        C.hx(col_va),sig,off,cd,C.hx(td) if td else "?",C.hx(chd) if chd else "?",
        C.read_cstr(td+8,80) if td else "?")

ROWS=[
 ("004A2B60","CStreamClass::slot3",0x007E5DB8,0x007E5DAC,0x007FF9B8,
  [(0x004A2C3E,"FF 51 0C","call [ecx+0xc]"),(0x004A2C41,"85 C0","test eax,eax"),(0x004A2C43,"7C 7C","jl 0x4A2CC1"),
   (0x004A2C73,"FF 51 0C","call [ecx+0xc]"),(0x004A2C76,"85 C0","test eax,eax"),(0x004A2C78,"7C 47","jl 0x4A2CC1"),
   (0x004A2CC1,"5F","failure epilogue pop edi"),(0x004A2CBF,"33 C0","success xor eax,eax")]),
 ("004A2CD0","CStreamClass::slot4",0x007E5DBC,0x007E5DAC,0x007FF9B8,
  [(0x004A2D8D,"E8 8E 02 00 00","call 0x4A3020"),(0x004A2D92,"85 C0","test eax,eax"),(0x004A2D94,"7C 61","jl 0x4A2DF7"),
   (0x004A2DB1,"E8 6A 02 00 00","call 0x4A3020"),(0x004A2DB6,"85 C0","test eax,eax"),(0x004A2DB8,"7C 3D","jl 0x4A2DF7"),
   (0x004A2DF5,"33 C0","success xor eax,eax"),(0x004A2DF7,"5F","failure epilogue pop edi")]),
 ("006BEF10","T_TClassFactory_VCStreamClass__::slot3",0x007F3774,0x007F3768,0x00809C68,
  [(0x006BEF6A,"FF 10","call [eax]=QueryInterface"),(0x006BEF6C,"8B F8","mov edi,eax"),
   (0x006BEF6E,"85 FF","test edi,edi"),(0x006BEF70,"7D 09","jge 0x6BEF7B"),
   (0x006BEF72,"FF 52 38","call [edx+0x38]=Release on fail"),
   (0x006BEE49,"C7 00 68 37 7F 00","ctor vptr install"),(0x006BEF4C,"E8 CF 38 DE FF","call ctor 0x4A2820")]),
 ("006BF690","T_TClassFactory_VSuperClass__::slot3",0x007F37EC,0x007F37E0,0x00809DF8,
  [(0x006BF6ED,"FF 10","call [eax]=QueryInterface"),(0x006BF6EF,"8B F8","mov edi,eax"),
   (0x006BF6F1,"85 FF","test edi,edi"),(0x006BF6F3,"7D 09","jge 0x6BF6FE"),
   (0x006BF6F5,"FF 52 20","call [edx+0x20]=Release on fail"),
   (0x006BF5C9,"C7 00 E0 37 7F 00","ctor vptr install"),(0x006BF6CF,"E8 EC B7 00 00","call ctor 0x6CAEC0")]),
]

def main():
    for entry,name,slot,vt,col,sites in ROWS:
        print("="*len(name))
        print("%s %s"%(entry,name))
        print("  slot @%s value = %s"%(C.hx(slot), C.hx(C.u32(slot))))
        print("  " + col_detail(col))
        print("  vtable slot0 [vt+0] @%s = %s"%(C.hx(vt), C.hx(C.u32(vt))))
        print("  vtable slot1 [vt+4] @%s = %s"%(C.hx(vt+4), C.hx(C.u32(vt+4))))
        for va,expect,desc in sites:
            b=C.va_read(va,8).hex(" ").upper()
            print("  %-28s @%s bytes=%-22s expect=%-18s"%(desc,C.hx(va),b,expect))
        print()

if __name__=="__main__":
    main()
