
import pefile, json
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=False); IMAGE=pe.OPTIONAL_HEADER.ImageBase
SEC=[]
for s in pe.sections:
    SEC.append((s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress+IMAGE, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
RAW=open(EXE,'rb').read()
def sec_of(va):
    for n,b,vs,pr,rs in SEC:
        if b<=va<b+max(vs,rs): return (n,b,pr,rs)
    return None
def dword(va):
    s=sec_of(va)
    if not s: return None
    n,b,pr,rs=s; off=pr+(va-b)
    if off<0 or off+4>len(RAW): return None
    return int.from_bytes(RAW[off:off+4],'little')
def cstr(va, n=64):
    s=sec_of(va)
    if not s: return None
    nme,b,pr,rs=s; off=pr+(va-b)
    if off<0: return None
    e=RAW.find(b'\x00', off, off+n)
    if e<0: return None
    return RAW[off:e]
TEXT=[s for s in SEC if s[0]=='.text'][0]
TB,TEND=TEXT[1], TEXT[1]+TEXT[2]
RDATA=[s for s in SEC if s[0]=='.rdata'][0]
RB,REND=RDATA[1], RDATA[1]+RDATA[3]

# 枚举虚表：扫描 .rdata 4 字节对齐，若 vt[-1] 指向 .rdata 且 COL+0xC -> TD, TD+8 是 ".?AV" 名串
vts={}
va=RB
while va < REND-4:
    if dword(va) is not None and TB <= dword(va) < TEND:
        col=dword(va-4)
        if col and RB<=col<REND:
            td=dword(col+0xC)
            if td and RB<=td<REND:
                nm=cstr(td+8,96)
                if nm and (nm.startswith(b'.?AV') or nm.startswith(b'.?AU')):
                    # 收集槽
                    slots=[]
                    p=va
                    while p< REND:
                        v=dword(p)
                        if v is None or not (TB<=v<TEND): break
                        slots.append(v); p+=4
                    name=nm.replace(b'\x00',b'').decode('latin1')
                    vts[va]={'name':name,'slots':slots,'col':col}
    va+=4
print('vtables found', len(vts))
json.dump({hex(k):{'name':v['name'],'slots':[hex(x) for x in v['slots']]} for k,v in vts.items()},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\vtables.json','w'), ensure_ascii=False)
# 反查：给定 entry，它在哪些 (vt, slot)
rev={}
for vt,v in vts.items():
    for k,s in enumerate(v['slots']):
        rev.setdefault(s,[]).append((hex(vt), v['name'], k, hex(k*4)))
json.dump({hex(k):[list(t) for t in v] for k,v in rev.items()},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\vt_rev.json','w'), ensure_ascii=False)
for e in (0x487E70,0x5B2E10,0x459ED0,0x459EE0,0x4DA2B0,0x40F150,0x40F0A0,0x417FE0):
    print(hex(e), rev.get(e, 'NOT IN ANY VT')[:4])
