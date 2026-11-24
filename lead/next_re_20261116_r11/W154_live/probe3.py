import ctypes, struct, subprocess
from ctypes import wintypes as wt
k32=ctypes.windll.kernel32
class MBI(ctypes.Structure):
    _fields_=[("BaseAddress",ctypes.c_ulonglong),("AllocationBase",ctypes.c_ulonglong),
              ("AllocationProtect",wt.DWORD),("PartitionId",wt.WORD),("__pad",wt.WORD),
              ("RegionSize",ctypes.c_ulonglong),("State",wt.DWORD),("Protect",wt.DWORD),("Type",wt.DWORD)]
k32.OpenProcess.restype=wt.HANDLE
k32.ReadProcessMemory.argtypes=[wt.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
pid=int(subprocess.run(["powershell","-NoProfile","-Command","(Get-Process gamemd).Id"],capture_output=True,text=True).stdout.split()[0])
h=k32.OpenProcess(0x1000|0x10,False,pid)
needles=[b"LoadBench",b"RA2F_M1",b"SAVE0029",b".yrm",b".mpr",b".map",b".SAV",b".sav"]
hits={}
addr=0; scanned=0
mbi=MBI()
while addr < 0x7FFFFFFF:
    r=k32.VirtualQueryEx(h,ctypes.c_void_p(addr),ctypes.byref(mbi),ctypes.sizeof(mbi))
    if not r or mbi.RegionSize==0: break
    base=mbi.BaseAddress; size=mbi.RegionSize
    if mbi.State==0x1000 and (mbi.Protect & 0xCC) and not (mbi.Protect & 0x100):  # committed, readable, not guard
        n=min(size,8*1024*1024); buf=ctypes.create_string_buffer(n); got=ctypes.c_size_t(0)
        if k32.ReadProcessMemory(h,ctypes.c_void_p(base),buf,n,ctypes.byref(got)) and got.value>0:
            data=buf.raw[:got.value]; scanned+=got.value
            for nd in needles:
                i=data.find(nd)
                while i>=0:
                    s=max(0,i-48); e=min(len(data),i+64)
                    frag=bytes(c for c in data[s:e] if 32<=c<127 or c==0)
                    ptr=base+i
                    hits.setdefault(nd,[]).append((ptr,frag.replace(b"\x00",b"")[:110]))
                    i=data.find(nd,i+1)
                    if len(hits.setdefault(nd,[]))>12: break
    addr=base+size
print("scanned %.0f MB"%(scanned/1048576))
for nd in needles:
    print("\n== %s : %d hits =="%(nd.decode(),len(hits.get(nd,[]))))
    for ptr,frag in hits.get(nd,[])[:8]:
        print("  0x%08X  %r"%(ptr,frag))
