import json,struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
targets={'AITriggerTypeClass':0x410260,'HouseClass':0x4f6830,'HouseTypeClass':0x5125a0}
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
for k,v in sym.items():
    vf=[int(x,16) for x in v['vfuncs']]
    for t,f in targets.items():
        if f in vf:
            print('%-24s slot %d = 0x%x  (vtable 0x%s, n=%d)'%(k,vf.index(f),f,v['vtable_va'],len(vf)))
            print('    bases:',v['bases'])
