from base import BUF, IB, u32, s32, cstr, in_raw, blob, TEXT
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
def is_code(v): return tlo<=v<thi
rd_lo,rd_hi=0x007E1000,0x00811074
slot=0x007EA8FC
# find vtable start = walk back over code ptrs
s=slot
while s-4>=rd_lo and is_code(u32(s-4)): s-=4
print("=== vtable start for slot 0x7EA8FC ===")
print("  vt start = %08X ; slot index = %d" % (s,(slot-s)//4))
col=u32(s-4)
print("  COL ptr (vt-4)=%08X  raw=%s" % (col, blob(col,0x18).hex() if in_raw(col,0x18) else "n/a"))
if in_raw(col,0x18):
    for i in range(0,0x18,4):
        v=u32(col+i)
        print("     COL+0x%02X = %08X %s" % (i,v,cstr(v,40) if in_raw(v,8) and 0x812000<=v<0xB79BE4 and v==0x812000+ (v-0x812000) and cstr(v,8).startswith(".") else ""))
    td=u32(col+0xC)
    print("  pTD = %08X ; TD raw=%s" % (td, blob(td,0x10).hex() if in_raw(td,0x10) else "n/a"))
    if in_raw(td,0x10):
        print("  TD+0x00=%08X  TD+0x08 inline name=%r" % (u32(td), blob(td+8,24)))
print()
print("=== slots around the found one ===")
for k in range(0,18):
    a=s+4*k
    v=u32(a)
    print("   slot %-2d %08X  %08X %s" % (k,a,v,"<<< 0x4F8440" if v==0x004F8440 else ""))
