
import sys
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
atl=K.atl_map()
def ret_info(va,label):
    a=atl.get('%08X'%va)
    sz=int(a['size']) if a else 4096
    ins=K.dis(va, max(sz,64))
    rets=[i for i in ins if i.mnemonic.startswith('ret')]
    print(f"CALLEE {label} @0x{va:08X} atlas_size={sz if a else 'NA'} firstret:", [(hex(i.address), i.mnemonic, i.op_str, i.bytes.hex()) for i in rets[:6]])
    # show first 3 and around first ret
    if ins:
        print("  prologue:", " | ".join(K.fmt(i) for i in ins[:6]))
    if rets:
        r=rets[0]; idx=ins.index(r)
        print("  around ret:", " | ".join(K.fmt(i) for i in ins[max(0,idx-3):idx+2]))
for va,label in [(0x65c7e0,'65C7E0 map-getter'),(0x5657a0,'5657A0 cell-getter'),(0x4838e0,'4838E0 can-spread'),(0x410380,'410380'),(0x4101c0,'4101c0')]:
    ret_info(va,label)
print()
print("=== 5FDD20 full ===")
for i in K.dis(0x5FDD20,190): print(K.fmt(i))
